# Contribuciones

| Área | Tarea | Responsable | Evidencia |
|---|---|---|---|
| Datos | MySQL 8.4.10 local y en Colab | Luis Pedro Lira | `scripts/setup_mysql.sh`, `scripts/mysql_utils.py` |
| Datos | Migración de Spider a MySQL, validación y traducción | Luis Pedro Lira | `scripts/migrar_spider.py`, `scripts/construir_spider.py`, `datos/descartes.csv` |
| Datos | 11 esquemas propios, generador de datos y 180 pares | Luis Pedro Lira | `datos/esquemas_propios/`, `scripts/generar_datos.py`, `datos/pares_propios.jsonl` |
| Datos | Dataset final y verificación de fugas | Luis Pedro Lira | `scripts/construir_dataset.py`, `datos/resumen_datos.json` |
| Entrenamiento | Script LoRA y configuraciones A/B | Luis Pedro Lira | `scripts/entrenar.py`, `notebooks/02_entrenamiento.ipynb` |
| Entrenamiento | Corridas en Colab T4 | Luis Pedro Lira (A), Mario Rocha (B) | `resultados/entrenamiento_{A,B}.json`, `resultados/curvas_loss_*.png` |
| Validación y errores | 2 esquemas y 40 preguntas de validación | _[compañero]_ | `datos/validacion/` |
| Validación y errores | Evaluador por ejecución | Luis Pedro Lira | `scripts/evaluador.py` |
| Validación y errores | `solucion.py` y autocorrección | Luis Pedro Lira; Mario Rocha (arreglo de compatibilidad con torchao en Colab) | `solucion.py`, `prompt.py` |
| Validación y errores | Baseline, A/B, experimento de inferencia, análisis de errores | Mario Rocha | `notebooks/03_evaluacion.ipynb`, `resultados/` |
| Presentación | Diapositivas y predicción de EX | Luis Pedro Lira, Mario Rocha | `presentacion.pdf` |
