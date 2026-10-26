"""Text-to-SQL: Qwen2.5-Coder + adapter LoRA.

Contrato:  generar_sql(esquema: str, pregunta: str, ejecutar=None) -> str
El modelo se carga al importar el módulo, según config.json.
"""
import json
import os
import random
import re
import sys
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

DIR = os.path.dirname(os.path.abspath(__file__))
if DIR not in sys.path:
    sys.path.insert(0, DIR)

from prompt import construir_mensajes, construir_mensajes_correccion  # noqa: E402

# Experimento de inferencia: reintentar con el error de ejecutar(). Poner en
# False para medir el modelo sin autocorrección.
AUTOCORRECCION = os.environ.get("AUTOCORRECCION", "1") != "0"
MAX_NEW_TOKENS = 320
MAX_LLAMADAS_EJECUTAR = 3
PRESUPUESTO_S = 24.0  # margen bajo el límite de 30 s por pregunta

# T2S_CONFIG solo se usa en nuestros experimentos; el evaluador usa config.json
with open(os.environ.get("T2S_CONFIG", os.path.join(DIR, "config.json")), encoding="utf-8") as f:
    CONFIG = json.load(f)

SEMILLA = int(CONFIG.get("semilla", 2026))
random.seed(SEMILLA)
torch.manual_seed(SEMILLA)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEMILLA)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DTYPE = torch.float16 if DEVICE == "cuda" else torch.float32


def _cargar_modelo():
    nombre = CONFIG["modelo_base"]
    tok = AutoTokenizer.from_pretrained(nombre)
    try:
        modelo = AutoModelForCausalLM.from_pretrained(nombre, dtype=DTYPE)
    except TypeError:  # transformers < 4.56
        modelo = AutoModelForCausalLM.from_pretrained(nombre, torch_dtype=DTYPE)
    if CONFIG.get("usar_adapter", False):
        from peft import PeftModel

        ruta = os.path.join(DIR, CONFIG.get("adapter", "adapter/"))
        modelo = PeftModel.from_pretrained(modelo, ruta)
        modelo = modelo.merge_and_unload()  # inferencia más rápida
    modelo.to(DEVICE).eval()
    return tok, modelo


TOKENIZER, MODELO = _cargar_modelo()


def _generar(mensajes: list) -> str:
    texto = TOKENIZER.apply_chat_template(mensajes, tokenize=False, add_generation_prompt=True)
    entradas = TOKENIZER(texto, return_tensors="pt").to(DEVICE)
    with torch.no_grad():
        salida = MODELO.generate(
            **entradas,
            max_new_tokens=MAX_NEW_TOKENS,
            do_sample=False,
            temperature=None,
            top_p=None,
            top_k=None,
            pad_token_id=TOKENIZER.eos_token_id,
        )
    nuevos = salida[0, entradas["input_ids"].shape[1]:]
    return TOKENIZER.decode(nuevos, skip_special_tokens=True)


# ---------------------------------------------------------------- post-proceso

_PROHIBIDAS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|REPLACE\s+INTO|GRANT|REVOKE|"
    r"RENAME|CALL|LOAD|HANDLER|LOCK|UNLOCK|SET|INTO\s+OUTFILE|INTO\s+DUMPFILE)\b",
    re.IGNORECASE,
)
_FALLBACK = "SELECT 1"


def _sin_literales(sql: str) -> str:
    """Reemplaza literales entre comillas para buscar palabras clave sin falsos positivos."""
    return re.sub(r"'(?:[^'\\]|\\.|'')*'|\"(?:[^\"\\]|\\.)*\"|`[^`]*`", "''", sql)


def _primera_sentencia(sql: str) -> str:
    """Corta en el primer ';' que no esté dentro de comillas."""
    comilla = None
    i = 0
    while i < len(sql):
        c = sql[i]
        if comilla:
            if c == "\\":
                i += 2
                continue
            if c == comilla:
                comilla = None
        elif c in ("'", '"', "`"):
            comilla = c
        elif c == ";":
            return sql[:i]
        i += 1
    return sql


def extraer_sql(texto: str) -> str:
    m = re.search(r"```(?:sql|mysql)?\s*\n?(.*?)(?:```|$)", texto, re.DOTALL | re.IGNORECASE)
    sql = m.group(1) if m else texto
    m = re.search(r"\b(WITH|SELECT)\b", sql, re.IGNORECASE)
    if m:
        sql = sql[m.start():]
    sql = _primera_sentencia(sql)
    # Quita comentarios de línea que el modelo a veces agrega
    sql = re.sub(r"--[^\n]*", "", sql)
    return re.sub(r"\s+", " ", sql).strip()


def es_segura(sql: str) -> bool:
    if not re.match(r"^\s*(WITH|SELECT|\()", sql, re.IGNORECASE):
        return False
    return not _PROHIBIDAS.search(_sin_literales(sql))


def _describir(res: dict) -> str:
    if not res.get("ok"):
        return f"ERROR: {res.get('error')}"
    filas = res.get("filas") or []
    return f"Columnas: {res.get('columnas')}\nFilas (máx. 10): {filas[:5]}"


# ---------------------------------------------------------------- contrato

def generar_sql(esquema: str, pregunta: str, ejecutar=None) -> str:
    inicio = time.time()
    sql = extraer_sql(_generar(construir_mensajes(esquema, pregunta)))
    if not es_segura(sql):
        sql = _FALLBACK

    if ejecutar is None or not AUTOCORRECCION:
        return sql

    ultima_ok = None
    for llamada in range(MAX_LLAMADAS_EJECUTAR):
        try:
            res = ejecutar(sql)
        except Exception as e:  # el evaluador nunca debe tumbar la función
            res = {"ok": False, "error": str(e)}
        if res.get("ok"):
            ultima_ok = sql
            break
        # Sin tiempo o sin más llamadas para verificar la corrección: no reintentar
        transcurrido = time.time() - inicio
        if llamada == MAX_LLAMADAS_EJECUTAR - 1 or transcurrido > PRESUPUESTO_S / 2:
            break
        nuevo = extraer_sql(_generar(construir_mensajes_correccion(esquema, pregunta, sql, _describir(res))))
        if not es_segura(nuevo) or nuevo == sql:
            break
        sql = nuevo
    return ultima_ok or sql
