"""Fine-tuning LoRA de Qwen2.5-Coder para Text-to-SQL (pensado para Colab T4).

Uso:  python scripts/entrenar.py --config A        # solo atención
      python scripts/entrenar.py --config B        # atención + MLP
Salidas: adapter_<cfg>/ , resultados/entrenamiento_<cfg>.json , resultados/curvas_loss_<cfg>.png

Las dos configuraciones difieren en un solo factor: target_modules.
"""
import argparse
import json
import math
import os
import random
import sys
import time

# Colab trae torchao 0.10 y peft 0.21 lanza ImportError si la versión es < 0.16.
# No usamos torchao: lo ocultamos antes de importar peft.
sys.modules.setdefault("torchao", None)

import numpy as np
import torch
from peft import LoraConfig, get_peft_model
from transformers import (AutoModelForCausalLM, AutoTokenizer, Trainer, TrainerCallback,
                          TrainingArguments)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
from prompt import construir_mensajes, respuesta_asistente  # noqa: E402

ATENCION = ["q_proj", "k_proj", "v_proj", "o_proj"]
MLP = ["gate_proj", "up_proj", "down_proj"]
CONFIGS = {
    "A": {"target_modules": ATENCION},
    "B": {"target_modules": ATENCION + MLP},
}
LORA_COMUN = {"r": 16, "lora_alpha": 32, "lora_dropout": 0.05}


def leer_jsonl(ruta):
    with open(ruta, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def tokenizar(tok, ej, max_len):
    prompt = tok.apply_chat_template(construir_mensajes(ej["esquema"], ej["pregunta"]),
                                     tokenize=False, add_generation_prompt=True)
    objetivo = respuesta_asistente(ej["sql"]) + tok.eos_token  # <|im_end|> en Qwen2.5
    ids_p = tok(prompt, add_special_tokens=False)["input_ids"]
    ids_o = tok(objetivo, add_special_tokens=False)["input_ids"]
    if len(ids_p) + len(ids_o) > max_len:
        return None
    # La loss solo se calcula sobre la respuesta del asistente
    return {"input_ids": ids_p + ids_o, "labels": [-100] * len(ids_p) + ids_o}


class Collator:
    def __init__(self, pad_id):
        self.pad_id = pad_id

    def __call__(self, lote):
        n = max(len(x["input_ids"]) for x in lote)
        ids = torch.full((len(lote), n), self.pad_id, dtype=torch.long)
        lab = torch.full((len(lote), n), -100, dtype=torch.long)
        att = torch.zeros((len(lote), n), dtype=torch.long)
        for i, x in enumerate(lote):
            m = len(x["input_ids"])
            ids[i, :m] = torch.tensor(x["input_ids"])
            lab[i, :m] = torch.tensor(x["labels"])
            att[i, :m] = 1
        return {"input_ids": ids, "labels": lab, "attention_mask": att}


class Registro(TrainerCallback):
    def __init__(self):
        self.train, self.eval = [], []

    def on_log(self, args, state, control, logs=None, **kw):
        logs = logs or {}
        if "loss" in logs:
            self.train.append((state.global_step, logs["loss"]))
        if "eval_loss" in logs:
            self.eval.append((state.global_step, logs["eval_loss"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", choices=list(CONFIGS), required=True)
    ap.add_argument("--modelo", default="Qwen/Qwen2.5-Coder-1.5B-Instruct")
    ap.add_argument("--epocas", type=float, default=1.0)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--batch", type=int, default=4)
    ap.add_argument("--accum", type=int, default=4)
    ap.add_argument("--max-len", type=int, default=2048)
    ap.add_argument("--max-steps", type=int, default=-1)
    ap.add_argument("--eval-n", type=int, default=120, help="ejemplos de eval_loss a usar")
    ap.add_argument("--limite-train", type=int, default=0, help="0 = todos")
    ap.add_argument("--semilla", type=int, default=2026)
    args = ap.parse_args()

    random.seed(args.semilla)
    np.random.seed(args.semilla)
    torch.manual_seed(args.semilla)

    cuda = torch.cuda.is_available()
    tok = AutoTokenizer.from_pretrained(args.modelo)
    dtype = torch.float16 if cuda else torch.float32
    modelo = AutoModelForCausalLM.from_pretrained(args.modelo, dtype=dtype)
    if cuda:
        modelo.to("cuda")
    modelo.config.use_cache = False
    modelo.gradient_checkpointing_enable()
    modelo.enable_input_require_grads()

    cfg_lora = LoraConfig(task_type="CAUSAL_LM", target_modules=CONFIGS[args.config]["target_modules"],
                          **LORA_COMUN)
    modelo = get_peft_model(modelo, cfg_lora)
    # Los pesos LoRA en fp32: con fp16 puro el GradScaler falla ("unscale FP16 gradients")
    for p in modelo.parameters():
        if p.requires_grad:
            p.data = p.data.float()
    entrenables = sum(p.numel() for p in modelo.parameters() if p.requires_grad)
    totales = sum(p.numel() for p in modelo.parameters())
    print(f"Parámetros entrenables: {entrenables:,} de {totales:,} ({100 * entrenables / totales:.3f} %)")

    datos_train = leer_jsonl(os.path.join(RAIZ, "datos", "entrenamiento.jsonl"))
    if args.limite_train:
        datos_train = datos_train[: args.limite_train]
    datos_eval = leer_jsonl(os.path.join(RAIZ, "datos", "eval_loss.jsonl"))
    random.Random(args.semilla).shuffle(datos_eval)
    datos_eval = datos_eval[: args.eval_n]
    train = [t for t in (tokenizar(tok, e, args.max_len) for e in datos_train) if t]
    evalset = [t for t in (tokenizar(tok, e, args.max_len) for e in datos_eval) if t]
    print(f"Train: {len(train)} (descartados por longitud: {len(datos_train) - len(train)}) | Eval: {len(evalset)}")

    pasos_epoca = math.ceil(len(train) / (args.batch * args.accum))
    targs = TrainingArguments(
        output_dir=os.path.join(RAIZ, f"checkpoints_{args.config}"),
        num_train_epochs=args.epocas, max_steps=args.max_steps,
        per_device_train_batch_size=args.batch, per_device_eval_batch_size=args.batch,
        gradient_accumulation_steps=args.accum, learning_rate=args.lr,
        lr_scheduler_type="cosine", warmup_steps=max(1, int(0.03 * pasos_epoca * args.epocas)),
        weight_decay=0.0, fp16=cuda, logging_steps=5,
        eval_strategy="steps", eval_steps=max(5, pasos_epoca // 8),
        save_strategy="no", report_to="none", seed=args.semilla,
        dataloader_num_workers=0, remove_unused_columns=False,
    )
    reg = Registro()
    trainer = Trainer(model=modelo, args=targs, train_dataset=train, eval_dataset=evalset,
                      data_collator=Collator(tok.pad_token_id or tok.eos_token_id), callbacks=[reg])
    t0 = time.time()
    trainer.train()
    minutos = (time.time() - t0) / 60
    eval_final = trainer.evaluate()["eval_loss"]
    reg.eval.append((trainer.state.global_step, eval_final))

    salida = os.path.join(RAIZ, f"adapter_{args.config}")
    modelo.save_pretrained(salida)
    tok.save_pretrained(salida)

    os.makedirs(os.path.join(RAIZ, "resultados"), exist_ok=True)
    info = {
        "config": args.config, "modelo": args.modelo, "target_modules": CONFIGS[args.config]["target_modules"],
        **LORA_COMUN, "parametros_entrenables": entrenables, "parametros_totales": totales,
        "porcentaje_entrenable": round(100 * entrenables / totales, 4),
        "ejemplos_train": len(train), "ejemplos_eval": len(evalset), "epocas": args.epocas,
        "lr": args.lr, "batch_efectivo": args.batch * args.accum, "pasos": trainer.state.global_step,
        "minutos_entrenamiento": round(minutos, 2), "eval_loss_final": round(eval_final, 4),
        "gpu": torch.cuda.get_device_name(0) if cuda else "cpu",
        "curva_train": reg.train, "curva_eval": reg.eval,
    }
    with open(os.path.join(RAIZ, "resultados", f"entrenamiento_{args.config}.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 4))
    if reg.train:
        ax.plot(*zip(*reg.train), label="train loss")
    if reg.eval:
        ax.plot(*zip(*reg.eval), marker="o", label="eval loss")
    ax.set_xlabel("paso")
    ax.set_ylabel("loss")
    ax.set_title(f"Config {args.config}: {'+'.join(CONFIGS[args.config]['target_modules'])}", fontsize=9)
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(RAIZ, "resultados", f"curvas_loss_{args.config}.png"), dpi=130)
    print(json.dumps({k: v for k, v in info.items() if not k.startswith("curva")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
