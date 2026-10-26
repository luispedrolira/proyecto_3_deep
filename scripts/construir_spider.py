"""Convierte los pares de Spider a MySQL 8.4.10, los valida, traduce las preguntas
al español (MarianMT local) y escribe datos/spider_es.jsonl y los descartes.

Uso:  python scripts/construir_spider.py <ruta/spider_data> --muestra 2300
Requiere haber corrido antes scripts/migrar_spider.py.
"""
import argparse
import csv
import json
import os
import random
import re
import sys

import sqlglot
from sqlglot import exp

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import mysql_utils as mu  # noqa: E402

SEMILLA = 2026

MOTIVOS = {
    1055: "only_full_group_by",
    1064: "sintaxis",
    1054: "columna_inexistente",
    1146: "tabla_inexistente",
    1305: "funcion_inexistente",
    1582: "funcion_inexistente",
    3024: "timeout",
    1052: "columna_ambigua",
    1248: "subconsulta_sin_alias",
    1222: "set_op_columnas",
    1235: "no_soportado",
    1140: "only_full_group_by",      # agregado sin GROUP BY mezclado con columnas
    3065: "order_by_fuera_de_distinct",
    1525: "valor_fecha_invalido",
}


def motivo_error(err: str) -> str:
    m = re.search(r"\((\d{4}),", err or "")
    return MOTIVOS.get(int(m.group(1)), f"error_{m.group(1)}") if m else "otro"


def nivel_sql(sql: str) -> str:
    s = sql.upper()
    n_select = len(re.findall(r"\bSELECT\b", s))
    if n_select > 1 or re.search(r"\b(WITH|OVER|INTERSECT|EXCEPT|UNION)\b", s):
        return "dificil"
    if re.search(r"\b(JOIN|GROUP BY|HAVING)\b", s):
        return "media"
    return "facil"


def convertir(sql: str, tablas_reales: dict) -> str:
    """SQL de Spider -> MySQL: ajusta mayúsculas de tablas (Linux es sensible) y
    normaliza con sqlglot. Las comillas dobles de Spider son strings en MySQL."""
    sql = sql.strip().rstrip(";")
    try:
        arbol = sqlglot.parse_one(sql, read="mysql")
        for t in arbol.find_all(exp.Table):
            real = tablas_reales.get(t.name.lower())
            if real:
                t.set("this", exp.to_identifier(real))
        return arbol.sql(dialect="mysql")
    except Exception:
        return sql


def literales(sql: str):
    return [m.group(2) for m in re.finditer(r"(['\"])((?:(?!\1).){1,60})\1", sql)]


def proteger(pregunta: str, sql: str):
    """Sustituye en la pregunta los valores literales del SQL por [i] para que
    el traductor no los cambie."""
    valores = []
    for lit in sorted(set(literales(sql)), key=len, reverse=True):
        patron = re.compile(re.escape(lit), re.IGNORECASE)
        if patron.search(pregunta):
            pregunta = patron.sub(f"[{len(valores)}]", pregunta)
            valores.append(lit)
    return pregunta, valores


def restaurar(texto: str, valores):
    for i, v in enumerate(valores):
        texto = texto.replace(f"[{i}]", v)
    return texto


def traducir(frases, lote=48):
    from transformers import MarianMTModel, MarianTokenizer
    nombre = "Helsinki-NLP/opus-mt-en-es"
    tok = MarianTokenizer.from_pretrained(nombre)
    modelo = MarianMTModel.from_pretrained(nombre).eval()
    salida = []
    for i in range(0, len(frases), lote):
        b = tok(frases[i:i + lote], return_tensors="pt", padding=True, truncation=True)
        o = modelo.generate(**b, num_beams=2, max_new_tokens=128)
        salida += tok.batch_decode(o, skip_special_tokens=True)
        print(f"  traducidas {len(salida)}/{len(frases)}", flush=True)
    return salida


def limpiar_pregunta(p: str) -> str:
    p = re.sub(r"\s+([?.,!])", r"\1", p.strip())
    return re.sub(r"\s+", " ", p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spider_dir")
    ap.add_argument("--muestra", type=int, default=2300)
    args = ap.parse_args()

    pares = []
    for f in ("train_spider.json", "train_others.json"):
        with open(os.path.join(args.spider_dir, f), encoding="utf-8") as fh:
            pares += json.load(fh)

    esquemas, tablas = {}, {}
    validos, descartes, vistos = [], [], set()
    for i, p in enumerate(pares):
        db = "sp_" + p["db_id"]
        if db not in esquemas:
            esquemas[db] = mu.esquema_show_create(db)
            tablas[db] = {t.lower(): t for t in re.findall(r"CREATE TABLE `([^`]+)`", esquemas[db])}
        sql = convertir(p["query"], tablas[db])
        clave = (db, p["question"].strip().lower())
        if clave in vistos:
            descartes.append({"fuente": "spider", "db_id": p["db_id"], "pregunta": p["question"],
                              "sql": sql, "motivo": "duplicado", "error": ""})
            continue
        vistos.add(clave)
        r = mu.consultar(db, sql, max_filas=1)
        if not r["ok"]:
            descartes.append({"fuente": "spider", "db_id": p["db_id"], "pregunta": p["question"],
                              "sql": sql, "motivo": motivo_error(r["error"]), "error": r["error"][:300]})
            continue
        validos.append({"db_id": p["db_id"], "db": db, "pregunta_en": p["question"], "sql": sql,
                        "nivel": nivel_sql(sql)})
        if i % 1000 == 0:
            print(f"validados {i}/{len(pares)}", flush=True)

    print(f"Válidos {len(validos)}, descartados {len(descartes)}")

    # Muestra estratificada: más peso a media y difícil (lo que más pesa en la nota)
    rnd = random.Random(SEMILLA)
    por_nivel = {n: [v for v in validos if v["nivel"] == n] for n in ("facil", "media", "dificil")}
    cuota = {"facil": 0.25, "media": 0.40, "dificil": 0.35}
    muestra = []
    for n, lst in por_nivel.items():
        rnd.shuffle(lst)
        muestra += lst[: int(args.muestra * cuota[n])]
    faltan = args.muestra - len(muestra)
    resto = [v for n in por_nivel for v in por_nivel[n][int(args.muestra * cuota[n]):]]
    rnd.shuffle(resto)
    muestra += resto[:max(faltan, 0)]
    no_usados = len(validos) - len(muestra)

    protegidas = [proteger(limpiar_pregunta(v["pregunta_en"]), v["sql"]) for v in muestra]
    traducidas = traducir([p for p, _ in protegidas])

    os.makedirs(os.path.join(RAIZ, "datos"), exist_ok=True)
    with open(os.path.join(RAIZ, "datos", "spider_es.jsonl"), "w", encoding="utf-8") as fh:
        for k, (v, (_, vals), es) in enumerate(zip(muestra, protegidas, traducidas)):
            fila = {
                "id": f"spider_{k:05d}", "db_id": v["db_id"], "esquema": esquemas[v["db"]],
                "pregunta": restaurar(es, vals), "pregunta_en": v["pregunta_en"], "sql": v["sql"],
                "nivel": v["nivel"], "fuente": "spider",
            }
            fh.write(json.dumps(fila, ensure_ascii=False) + "\n")

    with open(os.path.join(RAIZ, "datos", "descartes_spider.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["fuente", "db_id", "pregunta", "sql", "motivo", "error"])
        w.writeheader()
        w.writerows(descartes)

    resumen = {"pares_spider": len(pares), "validos": len(validos), "descartados": len(descartes),
               "muestra_usada": len(muestra), "validos_no_usados_por_muestreo": no_usados}
    motivos = {}
    for d in descartes:
        motivos[d["motivo"]] = motivos.get(d["motivo"], 0) + 1
    resumen["descartes_por_motivo"] = dict(sorted(motivos.items(), key=lambda x: -x[1]))
    with open(os.path.join(RAIZ, "datos", "resumen_spider.json"), "w", encoding="utf-8") as fh:
        json.dump(resumen, fh, ensure_ascii=False, indent=2)
    print(json.dumps(resumen, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
