"""Migra las bases SQLite de Spider a MySQL 8.4.10.

Uso:  python scripts/migrar_spider.py <ruta/spider_data> [--max-filas 5000]
Crea una base `sp_<db_id>` por cada base usada en train_spider/train_others.
Los tipos se infieren de los valores (las columnas de SQLite son laxas).
"""
import argparse
import json
import os
import re
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mysql_utils as mu  # noqa: E402

RE_INT = re.compile(r"^-?\d{1,18}$")
RE_FLOAT = re.compile(r"^-?\d+(\.\d+)?([eE][-+]?\d+)?$")
RE_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RE_DATETIME = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")


def q(nombre: str) -> str:
    return "`" + nombre.replace("`", "``") + "`"


def inferir_tipo(valores, declarado: str) -> str:
    vals = [v for v in valores if v is not None and v != ""]
    if not vals:
        return "VARCHAR(255)"
    textos = [v if isinstance(v, str) else str(v) for v in vals]
    if all(isinstance(v, int) or (isinstance(v, str) and RE_INT.match(v.strip())) for v in vals):
        return "BIGINT" if any(abs(int(str(v).strip())) > 2_000_000_000 for v in vals) else "INT"
    if all(isinstance(v, (int, float)) or (isinstance(v, str) and RE_FLOAT.match(v.strip())) for v in vals):
        return "DOUBLE"
    if all(RE_DATE.match(t) for t in textos) and all(t[:4] != "0000" for t in textos):
        return "DATE"
    if all(RE_DATETIME.match(t) for t in textos) and all(t[:4] != "0000" for t in textos):
        return "DATETIME"
    largo = max(len(t.encode("utf-8")) for t in textos)
    return "VARCHAR(255)" if largo <= 255 else "TEXT"


def convertir_valor(v, tipo):
    if v is None or (v == "" and tipo not in ("VARCHAR(255)", "TEXT")):
        return None
    if tipo in ("INT", "BIGINT"):
        return int(str(v).strip())
    if tipo == "DOUBLE":
        return float(str(v).strip())
    if isinstance(v, bytes):
        return v.decode("utf-8", "replace")
    return str(v) if tipo in ("VARCHAR(255)", "TEXT") else v


def migrar_base(ruta_sqlite: str, db_mysql: str, max_filas: int):
    src = sqlite3.connect(ruta_sqlite)
    src.text_factory = lambda b: b.decode("utf-8", "replace")
    cur = src.cursor()
    tablas = [r[0] for r in cur.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
    ddl, datos, fks = [], {}, []
    for t in tablas:
        info = cur.execute(f"PRAGMA table_info({q(t).replace('`', chr(34))})").fetchall()
        cols = [r[1] for r in info]
        filas = cur.execute(f"SELECT * FROM {q(t).replace('`', chr(34))} LIMIT {max_filas}").fetchall()
        tipos = [inferir_tipo([f[i] for f in filas], info[i][2]) for i in range(len(cols))]
        pk = [r[1] for r in sorted(info, key=lambda r: r[5]) if r[5] > 0]
        # Solo se declara PK si es válida con los datos reales
        if pk:
            idx = [cols.index(c) for c in pk]
            claves = [tuple(f[i] for i in idx) for f in filas]
            if (any(k is None for c in claves for k in c) or len(set(claves)) != len(claves)
                    or any(tipos[i] == "TEXT" for i in idx)):
                pk = []
        lineas = [f"  {q(c)} {tp}{' NOT NULL' if c in pk else ''}" for c, tp in zip(cols, tipos)]
        if pk:
            lineas.append(f"  PRIMARY KEY ({', '.join(q(c) for c in pk)})")
        ddl.append(f"CREATE TABLE {q(t)} (\n" + ",\n".join(lineas) + "\n)")
        datos[t] = (cols, tipos, filas, pk)
        for r in cur.execute(f"PRAGMA foreign_key_list({q(t).replace('`', chr(34))})").fetchall():
            fks.append((t, r[3], r[2], r[4]))  # (tabla, col, tabla_ref, col_ref)
    src.close()

    mu.crear_base(db_mysql, ";\n".join(ddl) + ";")
    con = mu.conectar(db_mysql)
    with con.cursor() as c:
        c.execute("SET FOREIGN_KEY_CHECKS=0")
        for t, (cols, tipos, filas, _) in datos.items():
            if not filas:
                continue
            marcas = ", ".join(["%s"] * len(cols))
            sql = f"INSERT IGNORE INTO {q(t)} VALUES ({marcas})"
            conv = [[convertir_valor(v, tp) for v, tp in zip(f, tipos)] for f in filas]
            for i in range(0, len(conv), 1000):
                c.executemany(sql, conv[i:i + 1000])
        # FKs: solo si la columna referida es la PK simple de la tabla destino
        nombres = {t.lower(): t for t in datos}
        n_fk = 0
        for t, col, tref, cref in fks:
            tref_real = nombres.get(str(tref).lower())
            if not tref_real or not cref:
                continue
            pk_ref = datos[tref_real][3]
            if len(pk_ref) != 1 or pk_ref[0].lower() != str(cref).lower():
                continue
            try:
                c.execute(f"ALTER TABLE {q(t)} ADD FOREIGN KEY ({q(col)}) "
                          f"REFERENCES {q(tref_real)} ({q(pk_ref[0])})")
                n_fk += 1
            except Exception:
                pass
    con.close()
    return len(tablas), n_fk


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spider_dir")
    ap.add_argument("--max-filas", type=int, default=5000)
    args = ap.parse_args()

    dbs = set()
    for f in ("train_spider.json", "train_others.json"):
        with open(os.path.join(args.spider_dir, f), encoding="utf-8") as fh:
            dbs |= {x["db_id"] for x in json.load(fh)}
    ok, fallidas = 0, []
    for db in sorted(dbs):
        ruta = os.path.join(args.spider_dir, "database", db, f"{db}.sqlite")
        try:
            n_t, n_fk = migrar_base(ruta, f"sp_{db}", args.max_filas)
            ok += 1
            print(f"OK  {db}: {n_t} tablas, {n_fk} FK", flush=True)
        except Exception as e:
            fallidas.append((db, str(e)[:200]))
            print(f"ERR {db}: {e}", flush=True)
    print(f"\nMigradas {ok}/{len(dbs)}")
    with open(os.path.join(args.spider_dir, "migracion_fallidas.json"), "w", encoding="utf-8") as fh:
        json.dump(fallidas, fh, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
