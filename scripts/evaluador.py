"""Evaluador por ejecución (EX ponderado) sobre la validación propia.

Reglas del enunciado:
  - se compara el resultado, no el texto;
  - el orden de filas solo cuenta si la pregunta lo pide;
  - números redondeados a 2 decimales;
  - una columna adicional no penaliza.

Uso:
  python scripts/evaluador.py --preparar                       # crea las bases de validación
  python scripts/evaluador.py --oraculo                        # sanity check: EX debe ser 1.0
  python scripts/evaluador.py --nombre baseline --usar-adapter 0
  python scripts/evaluador.py --nombre lora_B --adapter adapter_B/ --autocorreccion 1
"""
import argparse
import csv
import glob
import itertools
import json
import os
import re
import sys
import tempfile
import time
from collections import Counter

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import mysql_utils as mu  # noqa: E402

PESOS = {"facil": 1, "media": 2, "dificil": 3}
RUTA_PREGUNTAS = os.path.join(RAIZ, "datos", "validacion", "preguntas.jsonl")
RUTA_ESQUEMAS = os.path.join(RAIZ, "datos", "validacion", "esquemas")


# ---------------------------------------------------------------- comparación

def _norm(v):
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, (int, float)):
        return round(float(v), 2) + 0.0  # +0.0 evita -0.0
    if isinstance(v, str):
        s = v.strip()
        if re.fullmatch(r"-?\d+(\.\d+)?", s):
            return round(float(s), 2) + 0.0
        return s
    return v


def _clave(v):
    # Para ordenar valores heterogéneos (None, números, texto)
    return (v is None, str(type(v)), v if v is not None else 0)


def _columnas(filas, n):
    return [[f[j] for f in filas] for j in range(n)]


def coinciden(ref: dict, pred: dict, importa_orden: bool) -> bool:
    """True si `pred` contiene (en alguna selección de columnas) el resultado de `ref`."""
    if not pred.get("ok"):
        return False
    fr = [[_norm(v) for v in f] for f in ref["filas"]]
    fp = [[_norm(v) for v in f] for f in pred["filas"]]
    if len(fr) != len(fp):
        return False
    if not fr:
        return True
    nr, np_ = len(fr[0]), len(fp[0])
    if np_ < nr:
        return False
    cr, cp = _columnas(fr, nr), _columnas(fp, np_)
    # Candidatas: columnas de pred con el mismo multiconjunto de valores
    candidatas = []
    for j in range(nr):
        firma = Counter(cr[j])
        cand = [k for k in range(np_) if Counter(cp[k]) == firma]
        if not cand:
            return False
        candidatas.append(cand)
    filas_ref = [tuple(f) for f in fr]
    for combo in itertools.islice(itertools.product(*candidatas), 2000):
        if len(set(combo)) != len(combo):
            continue
        proy = [tuple(f[k] for k in combo) for f in fp]
        if importa_orden:
            if proy == filas_ref:
                return True
        elif sorted(proy, key=lambda t: [_clave(x) for x in t]) == \
                sorted(filas_ref, key=lambda t: [_clave(x) for x in t]):
            return True
    return False


# ---------------------------------------------------------------- categorías

def _estructura(sql):
    import sqlglot
    from sqlglot import exp
    try:
        a = sqlglot.parse_one(sql, read="mysql")
    except Exception:
        return None
    tablas = {t.name.lower() for t in a.find_all(exp.Table)}
    aggs = sorted(type(x).__name__ for x in a.find_all(exp.AggFunc))
    group = bool(list(a.find_all(exp.Group))) or bool(list(a.find_all(exp.Having)))
    wheres = sorted(w.sql().lower() for w in a.find_all(exp.Where))
    return tablas, aggs, group, wheres


def categorizar(sql_pred: str, pred: dict, sql_ref: str) -> str:
    if not pred.get("ok"):
        err = pred.get("error") or ""
        m = re.search(r"\((\d{4}),", err)
        cod = int(m.group(1)) if m else 0
        if cod in (1054, 1146):
            return "columna_tabla_inexistente"
        if cod == 1055:
            return "agregacion"
        return "sintaxis"
    ep, er = _estructura(sql_pred), _estructura(sql_ref)
    if ep is None or er is None:
        return "resultado_distinto"
    if ep[0] != er[0]:
        return "join"
    if ep[1] != er[1] or ep[2] != er[2]:
        return "agregacion"
    if ep[3] != er[3]:
        return "filtro"
    return "resultado_distinto"


# ---------------------------------------------------------------- ejecución

def cargar_preguntas():
    with open(RUTA_PREGUNTAS, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def preparar():
    from generar_datos import crear_y_poblar
    for ruta in sorted(glob.glob(os.path.join(RUTA_ESQUEMAS, "*.sql"))):
        nombre = os.path.splitext(os.path.basename(ruta))[0]
        crear_y_poblar(nombre, ruta)
        print("base lista:", nombre)
    mu.crear_lector()


def evaluar(nombre, generar=None, con_ejecutar=True, salida=None):
    preguntas = cargar_preguntas()
    esquemas = {}
    filas, puntos, total = [], 0, 0
    for q in preguntas:
        db = q["db_id"]
        if db not in esquemas:
            esquemas[db] = mu.esquema_show_create(db)
        ref = mu.consultar(db, q["sql"])
        t0 = time.time()
        if generar is None:  # oráculo
            sql = q["sql"]
        else:
            ejecutar = mu.hacer_ejecutar(db) if con_ejecutar else None
            try:
                sql = generar(esquemas[db], q["pregunta"], ejecutar)
            except Exception as e:
                sql = f"-- error: {e}"
        dt = time.time() - t0
        pred = mu.consultar(db, sql)
        ok = coinciden(ref, pred, q.get("importa_orden", False))
        peso = PESOS[q["nivel"]]
        total += peso
        puntos += peso if ok else 0
        filas.append({
            "id": q["id"], "config": nombre, "db_id": db, "nivel": q["nivel"], "peso": peso,
            "pregunta": q["pregunta"], "sql_ref": q["sql"], "sql_pred": sql,
            "ejecuta": int(bool(pred.get("ok"))), "acierto": int(ok),
            "categoria": "" if ok else categorizar(sql, pred, q["sql"]),
            "error": (pred.get("error") or "")[:200], "tiempo_s": round(dt, 2),
        })
        print(f"{q['id']} {q['nivel']:7s} {'✔' if ok else '✘'} {dt:5.1f}s  {sql[:90]}", flush=True)

    ex = puntos / total
    por_nivel = {}
    for n in PESOS:
        sub = [f for f in filas if f["nivel"] == n]
        por_nivel[n] = round(sum(f["acierto"] for f in sub) / len(sub), 3) if sub else None
    resumen = {"config": nombre, "EX": round(ex, 4), "por_nivel": por_nivel,
               "ejecutan": sum(f["ejecuta"] for f in filas), "n": len(filas),
               "tiempo_medio_s": round(sum(f["tiempo_s"] for f in filas) / len(filas), 2),
               "tiempo_max_s": max(f["tiempo_s"] for f in filas)}
    print(json.dumps(resumen, ensure_ascii=False))

    if salida:
        os.makedirs(os.path.dirname(salida), exist_ok=True)
        nuevo = not os.path.exists(salida)
        with open(salida, "a", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(filas[0].keys()))
            if nuevo:
                w.writeheader()
            w.writerows(filas)
        ruta_res = os.path.join(os.path.dirname(salida), "resumen_experimentos.jsonl")
        with open(ruta_res, "a", encoding="utf-8") as f:
            f.write(json.dumps(resumen, ensure_ascii=False) + "\n")
    return resumen, filas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preparar", action="store_true")
    ap.add_argument("--oraculo", action="store_true")
    ap.add_argument("--nombre", default="exp")
    ap.add_argument("--usar-adapter", type=int, default=1)
    ap.add_argument("--adapter", default="adapter/")
    ap.add_argument("--autocorreccion", type=int, default=1)
    ap.add_argument("--modelo", default=None, help="sobrescribe modelo_base (solo pruebas)")
    ap.add_argument("--salida", default=os.path.join(RAIZ, "resultados", "validacion_propia.csv"))
    args = ap.parse_args()

    if args.preparar:
        preparar()
        return
    if args.oraculo:
        r, _ = evaluar("oraculo")
        assert r["EX"] == 1.0, "El evaluador no reconoce la referencia como correcta"
        return

    with open(os.path.join(RAIZ, "config.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    cfg["usar_adapter"] = bool(args.usar_adapter)
    if args.modelo:
        cfg["modelo_base"] = args.modelo
    cfg["adapter"] = os.path.abspath(os.path.join(RAIZ, args.adapter))
    tmp = os.path.join(tempfile.gettempdir(), f"t2s_config_{args.nombre}.json")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f)
    os.environ["T2S_CONFIG"] = tmp
    os.environ["AUTOCORRECCION"] = str(args.autocorreccion)
    sys.path.insert(0, RAIZ)
    t0 = time.time()
    import solucion
    print(f"Modelo cargado en {time.time() - t0:.1f}s")
    evaluar(args.nombre, solucion.generar_sql, con_ejecutar=bool(args.autocorreccion), salida=args.salida)


if __name__ == "__main__":
    main()
