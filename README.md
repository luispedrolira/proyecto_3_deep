# Proyecto 3 · Text-to-SQL con LoRA

Fine-tuning con LoRA de **Qwen/Qwen2.5-Coder-1.5B-Instruct** para generar consultas **MySQL 8.4.10** a partir del
esquema (`SHOW CREATE TABLE`, con `COMMENT`) y una pregunta en español.

Deep Learning 2026 · Universidad del Valle de Guatemala

## Contrato

```python
from solucion import generar_sql
sql = generar_sql(esquema: str, pregunta: str, ejecutar=None)  # -> una sola consulta SELECT / WITH ... SELECT
```

- `config.json` elige el modelo base y si se usa el adapter (`usar_adapter`). Con `false` se usa el **mismo prompt**.
- El modelo se carga al importar `solucion.py` (fp16 en GPU) y el adapter se fusiona (`merge_and_unload`) para que la inferencia sea más rápida.
- La generación es greedy (`do_sample=False`) y se fija la semilla 2026, así que es determinista.
- **Post-proceso**: se extrae el bloque ```sql```, se toma solo la primera sentencia y se rechaza cualquier consulta que no empiece con `SELECT`/`WITH` o que contenga DML/DDL (`INSERT`, `UPDATE`, `DROP`…). En ese caso se devuelve `SELECT 1`.
- **Autocorrección** (experimento de inferencia): si el evaluador pasa `ejecutar`, la consulta se ejecuta. Si MySQL devuelve
  error, se le muestra el error al modelo y se pide una corrección, con un máximo de 3 llamadas a `ejecutar` y un presupuesto de unos 24 s por pregunta.

## Ejecución

### Evaluador (Colab T4)
```bash
pip install -r requirements.txt
python -c "import solucion; print(solucion.generar_sql(open('esquema.sql').read(), '¿Cuántos clientes hay?'))"
```

### Reproducir todo
| Paso | Dónde | Comando |
|---|---|---|
| MySQL 8.4.10 | local | `docker run -d --name mysql8410 -e MYSQL_ROOT_PASSWORD=root -p 3307:3306 mysql:8.4.10` |
| MySQL 8.4.10 | Colab | `bash scripts/setup_mysql.sh` y luego `MYSQL_PORT=3306` |
| Migrar Spider | local/Colab | `python scripts/migrar_spider.py <spider_data>` |
| Pares Spider (validar + traducir) | local/Colab | `python scripts/construir_spider.py <spider_data> --muestra 2300` |
| Esquemas propios con datos | local/Colab | `python scripts/generar_datos.py datos/esquemas_propios/*.sql` |
| Bases de validación | local/Colab | `python scripts/evaluador.py --preparar` |
| Dataset final | local/Colab | `python scripts/construir_dataset.py` |
| Entrenar | Colab T4 | `python scripts/entrenar.py --config A` (y `--config B`) |
| Evaluar | Colab T4 | `notebooks/03_evaluacion.ipynb` (o `python scripts/evaluador.py ...`) |

## Estructura

```
solucion.py  config.json  requirements.txt  prompt.py   ← prompt compartido entre entrenamiento e inferencia
adapter/                    ← mejor adapter LoRA (entregable)
scripts/                    ← MySQL, migración de Spider, generador de datos, dataset, entrenamiento, evaluador
datos/
  entrenamiento.jsonl       ← 2,347 pares (Spider traducido + propios)
  eval_loss.jsonl           ← 94 pares de 7 esquemas Spider separados (solo para la curva de eval loss)
  descartes.csv             ← todos los pares descartados y su motivo
  esquemas_propios/         ← 11 esquemas propios (.sql)
  pares_propios.jsonl       ← 180 pares sobre los esquemas propios
  validacion/               ← 2 esquemas + 40 preguntas (no aparecen en el entrenamiento)
notebooks/                  ← 01_datos, 02_entrenamiento, 03_evaluacion
resultados/                 ← validacion_propia.csv, curvas de loss, resúmenes
```

## Datos

| Fuente | Pares | Notas |
|---|---|---|
| Spider (train + others) | 8,659 en total, **8,432 válidos** en MySQL 8.4.10 | Se migraron 146 bases SQLite a MySQL. Se tomó una muestra estratificada de 2,300 (25 % fácil, 40 % media, 35 % difícil) y se tradujo con MarianMT |
| Propios (11 esquemas) | 180, todos válidos | Mezclan nombres en español, inglés y abreviados, con `COMMENT`. Unos 40 % son difíciles (CTE, ventanas, fechas) |
| **Entrenamiento final** | **2,347** | 591 fáciles, 944 medias y 812 difíciles |

**Descartes (266)** — detalle en `datos/descartes.csv` y `datos/resumen_datos.json`:

| Motivo | n |
|---|---|
| `only_full_group_by` (errores 1055/1140) | 90 |
| columna inexistente (1054, casi siempre columnas con mayúsculas o espacios en Spider) | 70 |
| esquema demasiado largo (> 7,000 caracteres, ~2k tokens) | 39 |
| pregunta duplicada en la misma base | 25 |
| `ORDER BY` fuera de `DISTINCT` (3065) | 22 |
| subconsulta sin alias (1248) | 9 |
| no soportado (1235) | 6 |
| valor de fecha inválido (1525) | 4 |
| tabla inexistente (1146) | 1 |

Además, 6,132 pares de Spider válidos **no se usaron** por el muestreo, para mantener el entrenamiento dentro del tiempo de Colab.

**Validación propia**: `clinica_vet` (7 tablas, nombres en español) e `inv_mgmt` (7 tablas, inglés abreviado), con
40 preguntas: 14 fáciles, 14 medias y 12 difíciles. La partición es **por esquema**: `construir_dataset.py` verifica
que ni las bases ni los nombres de tabla de la validación aparezcan en el entrenamiento (0 coincidencias).

## Experimentos

| | Config A | Config B |
|---|---|---|
| target_modules | q, k, v, o | q, k, v, o + gate, up, down |
| r / alpha / dropout | 16 / 32 / 0.05 | 16 / 32 / 0.05 |
| Parámetros entrenables | _ver resultados/entrenamiento_A.json_ | _ver resultados/entrenamiento_B.json_ |
| Tiempo de entrenamiento (T4) | _pendiente_ | _pendiente_ |
| Eval loss final | _pendiente_ | _pendiente_ |

Resultados en la validación propia (`resultados/resumen_experimentos.csv`):

| Corrida | EX | Fácil | Media | Difícil |
|---|---|---|---|---|
| Baseline (sin adapter) | _pendiente_ | | | |
| LoRA A | _pendiente_ | | | |
| LoRA B | _pendiente_ | | | |
| Mejor LoRA + autocorrección | _pendiente_ | | | |

## Licencias

- **Qwen2.5-Coder-1.5B-Instruct**: Apache 2.0.
- **Spider** (Yu et al., 2018): CC BY-SA 4.0. Los pares derivados (convertidos a MySQL y traducidos) se distribuyen bajo la misma licencia.
- **Helsinki-NLP/opus-mt-en-es** (usado solo para traducir el dataset): CC BY 4.0.
- MySQL 8.4.10 Community: GPL v2.
- Código de este repositorio: MIT.

## Uso de IA

- **Claude Code (Anthropic)** se usó como asistente de programación para escribir los scripts, `solucion.py`, los
  notebooks y esta documentación. También redactó los esquemas propios y los pares pregunta–SQL de entrenamiento:
  el enunciado permite "pares generados con un LLM". Todos los pares se validaron ejecutándolos en MySQL 8.4.10.
- El set de validación lo redactó el asistente y el equipo lo revisó y ajustó. **(Equipo: revisen y reescriban las preguntas
  que consideren, porque el enunciado pide preguntas escritas por ustedes. Luego actualicen esta línea.)**
- Las preguntas de Spider se tradujeron con un modelo local de traducción automática (MarianMT), sin APIs externas.
- En la inferencia **no** se usa ninguna API externa: solo el modelo base más el adapter LoRA.
