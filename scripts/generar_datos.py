"""Llena con datos sintéticos (deterministas) las tablas de una base ya creada.

Lee tipos, ENUM y FKs de information_schema. Las tablas que ya tienen filas
(catálogos insertados a mano en el .sql) no se tocan.
"""
import datetime
import os
import random
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mysql_utils as mu  # noqa: E402

NOMBRES = ["Ana", "Luis", "María", "José", "Carmen", "Pedro", "Lucía", "Jorge", "Sofía", "Diego",
           "Valeria", "Carlos", "Daniela", "Miguel", "Andrea", "Fernando", "Gabriela", "Ricardo",
           "Paola", "Javier", "Isabel", "Andrés", "Mónica", "Raúl", "Elena", "Sergio", "Natalia",
           "Óscar", "Patricia", "Hugo"]
APELLIDOS = ["García", "López", "Martínez", "Pérez", "González", "Rodríguez", "Hernández", "Ramírez",
             "Morales", "Castillo", "Juárez", "Méndez", "Ortiz", "Reyes", "Flores", "Cruz", "Rivera",
             "Gómez", "Díaz", "Vásquez"]
CIUDADES = ["Guatemala", "Quetzaltenango", "Antigua", "Escuintla", "Cobán", "Huehuetenango",
            "Mazatenango", "Chimaltenango", "Puerto Barrios", "Zacapa"]
PAISES = ["Guatemala", "México", "El Salvador", "Honduras", "Costa Rica", "Colombia", "España",
          "Estados Unidos"]
PALABRAS = ["Alfa", "Beta", "Delta", "Sol", "Luna", "Norte", "Sur", "Central", "Prime", "Nova",
            "Maya", "Quetzal", "Volcán", "Lago", "Ceiba", "Jade", "Cumbre", "Río", "Plaza", "Faro"]
FECHA_MIN = datetime.date(2022, 1, 1)
FECHA_MAX = datetime.date(2025, 12, 31)


def _meta(db):
    con = mu.conectar("information_schema")
    with con.cursor() as c:
        c.execute("""SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, COLUMN_TYPE, EXTRA, IS_NULLABLE,
                            CHARACTER_MAXIMUM_LENGTH, NUMERIC_PRECISION, NUMERIC_SCALE, COLUMN_KEY
                     FROM COLUMNS WHERE TABLE_SCHEMA=%s ORDER BY TABLE_NAME, ORDINAL_POSITION""", (db,))
        cols = c.fetchall()
        c.execute("""SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
                     FROM KEY_COLUMN_USAGE WHERE TABLE_SCHEMA=%s AND REFERENCED_TABLE_NAME IS NOT NULL""", (db,))
        fks = c.fetchall()
        c.execute("""SELECT TABLE_NAME, COLUMN_NAME FROM STATISTICS
                     WHERE TABLE_SCHEMA=%s AND NON_UNIQUE=0 AND INDEX_NAME<>'PRIMARY'""", (db,))
        unicos = {(t, col) for t, col in c.fetchall()}
    con.close()
    tablas = {}
    for t, col, dt, ct, extra, nul, largo, prec, esc, key in cols:
        tablas.setdefault(t, []).append(dict(col=col, dt=dt, ct=ct, auto="auto_increment" in extra,
                                             nul=nul == "YES", largo=largo, prec=prec, esc=esc,
                                             pk=key == "PRI", unico=(t, col) in unicos))
    fk = {(t, col): (rt, rc) for t, col, rt, rc in fks}
    return tablas, fk


def _orden(tablas, fk):
    deps = {t: {rt for (tt, _), (rt, _) in fk.items() if tt == t and rt != t} for t in tablas}
    orden, hechos = [], set()
    while len(orden) < len(tablas):
        listos = [t for t in tablas if t not in hechos and deps[t] <= hechos]
        if not listos:  # ciclo: se rompe por orden alfabético
            listos = [sorted(t for t in tablas if t not in hechos)[0]]
        for t in sorted(listos):
            orden.append(t)
            hechos.add(t)
    return orden


def _fecha(rnd):
    return FECHA_MIN + datetime.timedelta(days=rnd.randint(0, (FECHA_MAX - FECHA_MIN).days))


def _numero(rnd, nombre, c):
    n = nombre.lower()
    if c["dt"] in ("decimal", "double", "float"):
        if re.search(r"(precio|price|costo|cost|monto|amount|total|salario|salary|sueldo|saldo|balance|"
                     r"importe|pago|tarifa|fee|valor)", n):
            v = rnd.choice([rnd.uniform(5, 150), rnd.uniform(50, 2500), rnd.uniform(500, 15000)])
        elif re.search(r"(nota|score|calif|rating|punt)", n):
            v = rnd.uniform(40, 100) if "rating" not in n else rnd.uniform(1, 5)
        elif re.search(r"(desc|porc|pct|tasa|rate)", n):
            v = rnd.uniform(0, 0.35)
        elif re.search(r"(peso|weight)", n):
            v = rnd.uniform(1, 60)
        else:
            v = rnd.uniform(1, 1000)
        esc = c["esc"] if c["esc"] is not None else 2
        tope = 10 ** ((c["prec"] or 10) - esc) - 1
        return round(min(v, tope), esc)
    if c["ct"].startswith("tinyint(1)") or re.match(r"^(es_|is_|activo|active|tiene_)", n):
        return rnd.choice([0, 1, 1])
    if re.search(r"(edad|age)", n):
        return rnd.randint(18, 80)
    if re.search(r"(anio|año|year|^yr)", n):
        return rnd.randint(2010, 2025)
    if re.search(r"(cant|qty|quantity|unidades|stock|existencia)", n):
        return rnd.randint(1, 50)
    if re.search(r"(credit|creditos)", n):
        return rnd.randint(2, 6)
    if re.search(r"^(dias|days)$", n):
        return rnd.randint(1, 30)
    if re.search(r"(dosis|dose)", n):
        return rnd.choice([50, 100, 250, 500])
    if re.search(r"(reorder|minimo|min_)", n):
        return rnd.randint(5, 30)
    if re.search(r"(minut|duracion|duration|dur_)", n):
        return rnd.randint(20, 240)
    if re.search(r"(capacidad|capacity|cupo|asientos|seats)", n):
        return rnd.randint(10, 300)
    if c["dt"] == "tinyint":
        return rnd.randint(0, 100)
    return rnd.randint(1, 500)


def _texto(rnd, t, c, i):
    n = c["col"].lower()
    largo = c["largo"] or 100
    if re.search(r"(email|correo|mail)", n):
        v = f"{rnd.choice(NOMBRES).lower()}.{rnd.choice(APELLIDOS).lower()}{i}@mail.com"
        v = v.translate(str.maketrans("áéíóúñ", "aeioun"))
    elif re.search(r"(apellido|last_?name|lname)", n):
        v = rnd.choice(APELLIDOS)
    elif re.search(r"(^nombre$|^nom$|first_?name|fname|^name$|nombres|nombre_completo|full_?name)", n) and \
            re.search(r"(clien|cust|emple|emp|pacien|pac|estud|stud|alum|usuar|user|autor|author|"
                      r"socio|miem|member|doctor|medic|vet|prof|teacher|instr|conduc|driver|vend|"
                      r"agent|piloto|pasaj|huesp|guest|lector|reader|entren|jugad|player|tecn|dueno|"
                      r"owner|propiet|cajer|mesero|repart|chofer|staff|personal|contact)", t.lower()):
        v = f"{rnd.choice(NOMBRES)} {rnd.choice(APELLIDOS)}" if "first" not in n and "fname" not in n \
            else rnd.choice(NOMBRES)
    elif re.search(r"(ciudad|city|municipio)", n):
        v = rnd.choice(CIUDADES)
    elif re.search(r"(pais|country|ctry|nacionalidad|nationality)", n):
        v = rnd.choice(PAISES)
    elif re.search(r"(tel|phone|cel)", n):
        v = f"{rnd.randint(2, 5)}{rnd.randint(1000000, 9999999)}"
    elif re.search(r"(direcc|address|addr|dir$)", n):
        v = f"{rnd.randint(1, 30)} calle {rnd.randint(1, 40)}-{rnd.randint(10, 99)}, zona {rnd.randint(1, 18)}"
    elif re.search(r"(codigo|code|sku|placa|plate|serie|serial|isbn|matricula|carnet)", n):
        v = f"{c['col'][:3].upper()}-{i:04d}"
    elif re.search(r"(descripcion|description|desc|notas|notes|observ|coment|comment|motivo|reason|detalle)", n):
        v = rnd.choice(["Sin observaciones", "Revisión general", "Pendiente de seguimiento",
                        "Cliente frecuente", "Urgente", "Atención estándar", "Requiere aprobación"])
    else:
        base = re.sub(r"s$", "", t.split("_")[-1]).capitalize()
        v = f"{base} {rnd.choice(PALABRAS)} {i}"
    return v[:largo]


def poblar(db: str, filas_base=25, filas_transacc=160, semilla=2026):
    rnd = random.Random(f"{semilla}-{db}")
    tablas, fk = _meta(db)
    con = mu.conectar(db)
    ids = {}
    with con.cursor() as cur:
        for t in _orden(tablas, fk):
            cols = tablas[t]
            cur.execute(f"SELECT COUNT(*) FROM `{t}`")
            existentes = cur.fetchone()[0]
            if existentes == 0:
                n_fk = sum(1 for c in cols if (t, c["col"]) in fk)
                n = filas_transacc if n_fk >= 2 or (n_fk >= 1 and any(c["dt"] in ("date", "datetime")
                                                                       for c in cols)) else filas_base
                if n_fk == 1 and n == filas_base:
                    n = 60
                insertables = [c for c in cols if not c["auto"]]
                n_pk = sum(1 for c in cols if c["pk"])
                # En PK compuestas la unicidad es de la tupla (la resuelve INSERT IGNORE)
                usados = {c["col"]: set() for c in insertables if c["unico"] or (c["pk"] and n_pk == 1)}
                filas = []
                for i in range(1, n + 1):
                    fila = []
                    for c in insertables:
                        clave = (t, c["col"])
                        if clave in fk:
                            rt, rc = fk[clave]
                            pool = ids.get((rt, rc)) or [None]
                            v = rnd.choice(pool) if not (c["nul"] and rnd.random() < 0.05) else None
                        elif c["pk"] and c["dt"] in ("int", "bigint", "smallint"):
                            v = i
                        elif c["dt"] == "enum":
                            opciones = re.findall(r"'((?:[^']|'')*)'", c["ct"])
                            v = rnd.choice(opciones)
                        elif c["dt"] in ("date", "datetime", "timestamp"):
                            d = _fecha(rnd)
                            v = d if c["dt"] == "date" else datetime.datetime.combine(
                                d, datetime.time(rnd.randint(7, 21), rnd.choice([0, 15, 30, 45])))
                        elif c["dt"] == "time":
                            v = f"{rnd.randint(7, 21):02d}:{rnd.choice([0, 30]):02d}:00"
                        elif c["dt"] in ("int", "bigint", "smallint", "tinyint", "mediumint",
                                         "decimal", "double", "float"):
                            v = _numero(rnd, c["col"], c)
                        elif c["dt"] == "year":
                            v = rnd.randint(2010, 2025)
                        else:
                            v = _texto(rnd, t, c, i)
                        if c["col"] in usados:
                            if v in usados[c["col"]]:
                                v = f"{v}-{i}" if isinstance(v, str) else i
                            usados[c["col"]].add(v)
                        fila.append(v)
                    filas.append(fila)
                nombres = ", ".join(f"`{c['col']}`" for c in insertables)
                marcas = ", ".join(["%s"] * len(insertables))
                cur.executemany(f"INSERT IGNORE INTO `{t}` ({nombres}) VALUES ({marcas})", filas)
            # ids disponibles para las FKs de las siguientes tablas
            for (tt, cc), (rt, rc) in fk.items():
                if rt == t and (rt, rc) not in ids:
                    cur.execute(f"SELECT `{rc}` FROM `{rt}`")
                    ids[(rt, rc)] = [r[0] for r in cur.fetchall()]
    con.close()


def crear_y_poblar(nombre: str, ruta_sql: str):
    with open(ruta_sql, encoding="utf-8") as f:
        mu.crear_base(nombre, f.read())
    poblar(nombre)


if __name__ == "__main__":
    for ruta in sys.argv[1:]:
        nombre = os.path.splitext(os.path.basename(ruta))[0]
        crear_y_poblar(nombre, ruta)
        print("ok", nombre)
