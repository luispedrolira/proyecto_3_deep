"""Prompt compartido entre el entrenamiento y la inferencia (solucion.py).

Cualquier cambio aquí cambia lo que el modelo vio al entrenar: si se modifica,
hay que reentrenar el adapter.
"""
import re

SYSTEM = (
    "Eres un experto en MySQL 8.4. Recibes el esquema de una base de datos "
    "(sentencias CREATE TABLE, con sus COMMENT) y una pregunta en español. "
    "Responde únicamente con una consulta MySQL válida (SELECT o WITH ... SELECT) "
    "dentro de un bloque ```sql```. Usa solo tablas y columnas del esquema. "
    "La base usa ONLY_FULL_GROUP_BY: toda columna no agregada del SELECT debe ir en el GROUP BY."
)

SYSTEM_CORRECCION = (
    "Eres un experto en MySQL 8.4. Una consulta generada para la pregunta produjo un error en MySQL. "
    "Lee el error, identifica la causa (columna o tabla inexistente, alias no definido, GROUP BY "
    "incompleto, sintaxis) y escribe una consulta corregida DIFERENTE a la anterior, usando solo "
    "tablas y columnas del esquema. Responde únicamente con la consulta dentro de un bloque ```sql```."
)

_RUIDO_TABLA = re.compile(
    r"\)[ \t]*ENGINE=[^;\n]*?(?=COMMENT=|;|$)", re.IGNORECASE | re.MULTILINE
)


def normalizar_esquema(esquema: str) -> str:
    """Quita opciones de tabla que no aportan (ENGINE, CHARSET, COLLATE,
    AUTO_INCREMENT=n) para ahorrar tokens, conservando los COMMENT."""
    s = esquema.replace("\r\n", "\n")
    s = _RUIDO_TABLA.sub(") ", s)
    s = re.sub(r"\s+COLLATE\s+\w+", "", s)
    s = re.sub(r"\s+CHARACTER SET\s+\w+", "", s)
    s = re.sub(r"\) +COMMENT=", ") COMMENT=", s)
    s = re.sub(r"\) +(;|$)", r")\1", s, flags=re.MULTILINE)
    # Índices secundarios no aportan semántica; las FK sí (se conservan sin su nombre)
    s = re.sub(r"(?m)^\s*KEY `[^`]*` \([^\n]*\),?\n", "", s)
    s = re.sub(r"CONSTRAINT `[^`]*` FOREIGN KEY", "FOREIGN KEY", s)
    s = re.sub(r",(\s*\n\))", r"\1", s)
    s = re.sub(r"[ \t]+\n", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def construir_mensajes(esquema: str, pregunta: str) -> list:
    """Mensajes de chat para generar SQL. Mismo formato en train e inferencia."""
    usuario = (
        f"### Esquema\n{normalizar_esquema(esquema)}\n\n"
        f"### Pregunta\n{pregunta.strip()}"
    )
    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": usuario},
    ]


def construir_mensajes_correccion(esquema: str, pregunta: str, sql: str, resultado: str) -> list:
    """Mensajes para el reintento con la retroalimentación de ejecutar()."""
    usuario = (
        f"### Esquema\n{normalizar_esquema(esquema)}\n\n"
        f"### Pregunta\n{pregunta.strip()}\n\n"
        f"### Error de MySQL\n{resultado}\n\n"
        f"### Consulta incorrecta (no la repitas)\n{sql}\n\n"
        "### Consulta corregida"
    )
    return [
        {"role": "system", "content": SYSTEM_CORRECCION},
        {"role": "user", "content": usuario},
    ]


def respuesta_asistente(sql: str) -> str:
    """Formato de la respuesta objetivo en el entrenamiento."""
    return f"```sql\n{sql.strip().rstrip(';')}\n```"
