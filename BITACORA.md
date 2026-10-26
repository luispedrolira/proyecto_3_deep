# Bitácora

> Cada entrada: fecha, autor y lo que se hizo. **Pendiente: el compañero debe escribir sus propias entradas.**

### 2026-10-25 · Luis Pedro Lira
Análisis del enunciado y división del trabajo. Parte 1 (Luis): datos y entrenamiento. Parte 2 (compañero):
validación, inferencia, evaluación y errores. Acordamos tres contratos: un `prompt.py` compartido, el formato JSONL
y los nombres de los esquemas de validación (`clinica_vet`, `inv_mgmt`).

### 2026-10-25 · Luis Pedro Lira
Instalamos MySQL 8.4.10 con Docker (`mysql:8.4.10`) y verificamos que `sql_mode` incluye `ONLY_FULL_GROUP_BY`.
Escribimos `scripts/setup_mysql.sh` para Colab y `scripts/mysql_utils.py`, con un usuario de solo lectura `lector`.

### 2026-10-25 · Luis Pedro Lira
Migramos Spider: las 146 bases SQLite de train + others pasaron a MySQL. Los tipos se infieren de los valores reales,
porque SQLite es laxo, y las FK solo se agregan cuando apuntan a una PK simple. En Linux los nombres de tabla distinguen
mayúsculas, así que se corrigen en el SQL con sqlglot.

### 2026-10-25 · Luis Pedro Lira
Validamos los 8,659 pares de Spider en MySQL 8.4.10: 8,432 son válidos y 227 se descartaron. La causa principal es
`ONLY_FULL_GROUP_BY` (83 + 7), seguida de columnas inexistentes (70). Tomamos una muestra estratificada de 2,300 y la
traducimos con MarianMT, protegiendo los literales del SQL con marcadores `[i]`.

### 2026-10-25 · Luis Pedro Lira
Creamos 11 esquemas propios con COMMENT y nombres mixtos (español, inglés y abreviados), y un generador de datos
sintéticos determinista basado en `information_schema`. Escribimos 180 pares, con unos 40 % difíciles; todos ejecutan
sin error.

### 2026-10-25 · Luis Pedro Lira
Armamos el dataset final: 2,347 pares de entrenamiento y 94 de eval loss, separados por esquema. Verificamos 0 fugas de
validación. Hipótesis antes de entrenar: la config B (atención + MLP) supera a la A (solo atención) en eval loss y
EX, sobre todo en las preguntas difíciles.

### 2026-10-25 · _[compañero]_
_Pendiente: revisión y ajuste de las 40 preguntas de validación y del evaluador (oráculo EX = 1.0)._

### 2026-10-25 · _[compañero]_
_Pendiente: baseline, evaluación de A/B, experimento de autocorrección y análisis de errores._

### 2026-10-25 · _[quien entrene]_
_Pendiente: entrenamiento A y B en Colab T4 (tiempos, parámetros entrenables, curvas)._
