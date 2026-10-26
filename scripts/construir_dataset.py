"""Une Spider (traducido) + pares propios en el dataset final de entrenamiento.

  - valida cada par propio en MySQL 8.4.10 (los que fallan van a descartes);
  - verifica que ningún esquema/tabla de validación aparezca en entrenamiento;
  - separa un 5 % de los esquemas (no de las preguntas) para la eval loss.

Salidas: datos/entrenamiento.jsonl, datos/eval_loss.jsonl, datos/descartes.csv,
         datos/resumen_datos.json
"""
import csv
import glob
import json
import os
import random
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "scripts"))
import mysql_utils as mu  # noqa: E402
from construir_spider import motivo_error, nivel_sql  # noqa: E402

SEMILLA = 2026
MAX_CHARS_ESQUEMA = 7000  # ~2000 tokens; evita truncar el SQL objetivo
D = os.path.join(RAIZ, "datos")


def leer_jsonl(ruta):
    with open(ruta, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def tablas_de(esquema):
    return {t.lower() for t in re.findall(r"CREATE TABLE `([^`]+)`", esquema)}


def main():
    descartes = []
    with open(os.path.join(D, "descartes_spider.csv"), encoding="utf-8") as f:
        descartes += list(csv.DictReader(f))
    for d in descartes:  # normaliza motivos con la tabla actual de códigos MySQL
        if d["error"]:
            d["motivo"] = motivo_error(d["error"])

    # --- pares propios
    propios, esquemas = [], {}
    for k, p in enumerate(leer_jsonl(os.path.join(D, "pares_propios.jsonl"))):
        db = p["db"]
        if db not in esquemas:
            esquemas[db] = mu.esquema_show_create(db)
        r = mu.consultar(db, p["sql"], max_filas=1)
        if not r["ok"]:
            descartes.append({"fuente": "propio", "db_id": db, "pregunta": p["pregunta"], "sql": p["sql"],
                              "motivo": motivo_error(r["error"]), "error": r["error"][:300]})
            continue
        propios.append({"id": f"propio_{k:04d}", "db_id": db, "esquema": esquemas[db],
                        "pregunta": p["pregunta"], "sql": p["sql"], "nivel": nivel_sql(p["sql"]),
                        "fuente": "propio"})

    spider = leer_jsonl(os.path.join(D, "spider_es.jsonl"))
    todos = []
    for x in spider + propios:
        if len(x["esquema"]) > MAX_CHARS_ESQUEMA:
            descartes.append({"fuente": x["fuente"], "db_id": x["db_id"], "pregunta": x["pregunta"],
                              "sql": x["sql"], "motivo": "esquema_demasiado_largo", "error": ""})
            continue
        todos.append(x)

    # --- fuga: esquemas de validación
    val_dbs = {os.path.splitext(os.path.basename(r))[0]
               for r in glob.glob(os.path.join(D, "validacion", "esquemas", "*.sql"))}
    val_tablas = set()
    for db in val_dbs:
        val_tablas |= tablas_de(mu.esquema_show_create(db))
    fuga_db = [x["id"] for x in todos if x["db_id"] in val_dbs]
    fuga_tab = [x["id"] for x in todos if tablas_de(x["esquema"]) & val_tablas]
    assert not fuga_db, f"Esquemas de validación en entrenamiento: {fuga_db[:5]}"

    # --- partición por esquema para la eval loss
    rnd = random.Random(SEMILLA)
    dbs = sorted({x["db_id"] for x in todos if x["fuente"] == "spider"})
    rnd.shuffle(dbs)
    dbs_eval = set(dbs[: max(1, int(0.05 * len(dbs)))])
    train = [x for x in todos if x["db_id"] not in dbs_eval]
    evalset = [x for x in todos if x["db_id"] in dbs_eval]
    rnd.shuffle(train)

    for nombre, datos in (("entrenamiento.jsonl", train), ("eval_loss.jsonl", evalset)):
        with open(os.path.join(D, nombre), "w", encoding="utf-8") as f:
            for x in datos:
                f.write(json.dumps(x, ensure_ascii=False) + "\n")

    with open(os.path.join(D, "descartes.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["fuente", "db_id", "pregunta", "sql", "motivo", "error"])
        w.writeheader()
        w.writerows(descartes)

    def conteo(lst, campo):
        c = {}
        for x in lst:
            c[x[campo]] = c.get(x[campo], 0) + 1
        return dict(sorted(c.items(), key=lambda t: -t[1]))

    with open(os.path.join(D, "resumen_spider.json"), encoding="utf-8") as f:
        res_spider = json.load(f)
    resumen = {
        "entrenamiento": len(train), "eval_loss": len(evalset),
        "por_fuente": conteo(train, "fuente"), "por_nivel": conteo(train, "nivel"),
        "esquemas_entrenamiento": len({x["db_id"] for x in train}),
        "esquemas_propios": sorted({x["db_id"] for x in propios}),
        "esquemas_eval_loss": sorted(dbs_eval),
        "pares_propios_escritos": len(leer_jsonl(os.path.join(D, "pares_propios.jsonl"))),
        "pares_propios_validos": len(propios),
        "descartes_total": len(descartes), "descartes_por_motivo": conteo(descartes, "motivo"),
        "descartes_por_fuente": conteo(descartes, "fuente"),
        "spider": res_spider,
        "fuga_esquemas_validacion": len(fuga_db),
        "ejemplos_con_tablas_homonimas_a_validacion": len(fuga_tab),
    }
    with open(os.path.join(D, "resumen_datos.json"), "w", encoding="utf-8") as f:
        json.dump(resumen, f, ensure_ascii=False, indent=2)
    print(json.dumps(resumen, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
