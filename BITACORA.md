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

### 2026-10-25 · Mario Rocha
Revisé las 40 preguntas de validación y reescribí la redacción de 19 de `clinica_vet` (v01–v20 salvo v05), apoyándome
en un asistente de IA para la redacción. Solo cambió el texto de `pregunta`: se verificó que cada una siguiera pidiendo
lo mismo que su SQL (mismas columnas y filtros).

### 2026-10-25 · Mario Rocha
Entrené la configuración B (atención + MLP) en Colab con GPU T4: 18,464,768 parámetros entrenables (1.182 %). La
primera corrida falló porque Colab trae `torchao` 0.10 y `peft` 0.21.2 exige 0.16 o más; como no usamos `torchao`, lo
ocultamos antes de importar `peft` en `entrenar.py` y `solucion.py` (esto también evita que falle la inferencia en el
Colab del evaluador). La segunda corrida se quedó sin memoria (CUDA OOM) en el paso 6, así que usamos `--batch 2
--accum 8`, que mantiene el batch efectivo en 16. Resultado: 147 pasos en 32.2 min y eval loss final 0.2091, apenas
peor que A (0.2065), contra la hipótesis de que B ganaría. El EX en validación decide cuál se entrega.

### 2026-10-26 · Mario Rocha
Corrí `03_evaluacion.ipynb` en Colab T4 con los adapters A y B. El oráculo dio EX = 1.0. EX ponderado en la validación
propia: baseline 0.538, LoRA A 0.692, LoRA B 0.692 y LoRA B + autocorrección 0.718 (baseline + autocorrección: 0.615).
A y B empatan, pero fallan en preguntas distintas (A acierta v18 y w18; B, w16 y w20); el notebook desempata a favor de
B, que quedó en `adapter/`. El adapter mejora sobre todo las fáciles (0.71 → 1.0) y las medias (0.50 → 0.79); las
difíciles se quedan en 0.5. La autocorrección solo rescata w12 en B. Con B + autocorrección todavía fallan v09, v13,
v15, v17, v18, v20, w15 y w18: 3 por join, 2 por columna o tabla inexistente, 2 de sintaxis y 1 de filtro.
Verificación del contrato: carga en 25.4 s, máximo 10.9 s por pregunta y salida determinista.

### 2026-10-25 · _[Luis Pedro Lira]_
_Pendiente (Luis): su entrada del entrenamiento de A en Colab T4 (4,358,144 parámetros, 30.0 min, eval loss 0.2065)._
