"""Utilidades para MySQL 8.4.10 (local con Docker o en Colab con setup_mysql.sh).

Variables de entorno: MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD.
Por defecto apunta al contenedor local:  docker run -p 3307:3306 mysql:8.4.10
"""
import datetime
import decimal
import os

import pymysql
from pymysql.constants import CLIENT

HOST = os.environ.get("MYSQL_HOST", "127.0.0.1")
PORT = int(os.environ.get("MYSQL_PORT", "3307"))
USER = os.environ.get("MYSQL_USER", "root")
PASSWORD = os.environ.get("MYSQL_PASSWORD", "root")
LECTOR = ("lector", "lector")
TIMEOUT_MS = 10000


def conectar(db=None, usuario=None, multi=False):
    user, pwd = usuario or (USER, PASSWORD)
    return pymysql.connect(
        host=HOST, port=PORT, user=user, password=pwd, database=db,
        charset="utf8mb4", autocommit=True,
        client_flag=CLIENT.MULTI_STATEMENTS if multi else 0,
    )


def crear_base(nombre: str, script_sql: str):
    """(Re)crea la base `nombre` y ejecuta el script DDL + INSERT."""
    con = conectar(multi=True)
    try:
        with con.cursor() as cur:
            cur.execute(f"DROP DATABASE IF EXISTS `{nombre}`")
            cur.execute(f"CREATE DATABASE `{nombre}` CHARACTER SET utf8mb4")
            cur.execute(f"USE `{nombre}`")
            cur.execute(script_sql)
            while cur.nextset():
                pass
    finally:
        con.close()


def crear_lector():
    """Usuario de solo lectura, como el del evaluador."""
    con = conectar()
    with con.cursor() as cur:
        cur.execute("CREATE USER IF NOT EXISTS 'lector'@'%' IDENTIFIED BY 'lector'")
        cur.execute("GRANT SELECT, SHOW VIEW ON *.* TO 'lector'@'%'")
    con.close()


def listar_bases():
    con = conectar()
    with con.cursor() as cur:
        cur.execute("SHOW DATABASES")
        bases = [r[0] for r in cur.fetchall()]
    con.close()
    return [b for b in bases if b not in ("mysql", "information_schema", "performance_schema", "sys")]


def esquema_show_create(db: str) -> str:
    """Esquema tal como lo entrega el evaluador: SHOW CREATE TABLE de cada tabla."""
    con = conectar(db)
    with con.cursor() as cur:
        cur.execute("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE'")
        tablas = [r[0] for r in cur.fetchall()]
        partes = []
        for t in tablas:
            cur.execute(f"SHOW CREATE TABLE `{t}`")
            partes.append(cur.fetchone()[1] + ";")
    con.close()
    return "\n\n".join(partes)


def _valor(v):
    if isinstance(v, decimal.Decimal):
        return float(v)
    if isinstance(v, (datetime.date, datetime.datetime, datetime.time, datetime.timedelta)):
        return str(v)
    if isinstance(v, bytes):
        return v.decode("utf-8", "replace")
    return v


def consultar(db: str, sql: str, max_filas=None, lector=True):
    """Ejecuta `sql` y devuelve {ok, columnas, filas, error}."""
    con = None
    try:
        con = conectar(db, usuario=LECTOR if lector else None)
        with con.cursor() as cur:
            cur.execute(f"SET SESSION MAX_EXECUTION_TIME={TIMEOUT_MS}")
            cur.execute(sql)
            columnas = [d[0] for d in cur.description] if cur.description else []
            filas = cur.fetchall() if max_filas is None else cur.fetchmany(max_filas)
            filas = [[_valor(v) for v in f] for f in filas]
        return {"ok": True, "columnas": columnas, "filas": filas, "error": None}
    except Exception as e:
        return {"ok": False, "columnas": [], "filas": [], "error": f"{type(e).__name__}: {e}"}
    finally:
        if con is not None:
            con.close()


def hacer_ejecutar(db: str, max_llamadas=3):
    """Simula la función `ejecutar` que entrega el evaluador (máx. 10 filas, 3 llamadas)."""
    estado = {"llamadas": 0}

    def ejecutar(sql: str) -> dict:
        estado["llamadas"] += 1
        if estado["llamadas"] > max_llamadas:
            return {"ok": False, "columnas": [], "filas": [], "error": "Límite de llamadas alcanzado"}
        return consultar(db, sql, max_filas=10)

    ejecutar.estado = estado
    return ejecutar
