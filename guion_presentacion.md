# Guion de la presentación (máx. 12 diapositivas)

> Borrador para armar `presentacion.pdf`. Los números marcados como **[X]** salen de `resultados/`.

1. **Problema y contrato.** Esquema `SHOW CREATE TABLE` + pregunta en español → una consulta MySQL 8.4.10.
   Qwen2.5-Coder-1.5B-Instruct + LoRA. Reglas: T4, < 30 s por pregunta, generación determinista y solo SELECT.
2. **Pipeline de datos.** Diagrama: Spider (SQLite) → migración a MySQL → transpilar con sqlglot → ejecutar en 8.4.10 →
   traducir con MarianMT (literales protegidos) + 11 esquemas propios → dataset de 2,347 pares.
3. **Descartes.** De 8,659 pares de Spider, 8,432 son válidos y 266 se descartaron en total. Barras por motivo:
   `ONLY_FULL_GROUP_BY` 90, columna inexistente 70, esquema largo 39…
   Lección: `ONLY_FULL_GROUP_BY` es la principal diferencia entre SQLite y MySQL.
4. **Esquemas propios y validación.** 11 esquemas con COMMENT y nombres mixtos (español, inglés y abreviados).
   Validación: `clinica_vet` + `inv_mgmt`, 40 preguntas (14/14/12), partición por esquema y 0 fugas.
5. **Prompt y post-proceso.** El system prompt menciona `ONLY_FULL_GROUP_BY`. El esquema se normaliza (sin ENGINE, sin
   KEY, unos 27 % menos caracteres). Se extrae el bloque ```sql``` y hay un filtro anti-DML.
6. **Configuraciones LoRA.** A = atención y B = atención + MLP (único factor). Hipótesis escrita antes de entrenar.
   Tabla: parámetros entrenables **[X]**, minutos en T4 **[X]**, eval loss **[X]**.
7. **Curvas de loss.** `resultados/curvas_loss_A.png` y `resultados/curvas_loss_B.png`.
8. **Resultados en validación.** Tabla de EX: baseline, A, B y la mejor con autocorrección, con desglose por nivel **[X]**.
9. **Experimento de inferencia: autocorrección con `ejecutar`.** Cuántas consultas con error se rescataron **[X]**,
   cuánto cambió el EX **[X]** y su costo en tiempo **[X]** s por pregunta.
10. **Análisis de errores.** Barras por categoría (sintaxis, columna o tabla inexistente, JOIN, agregación, filtro,
    resultado distinto) y 2 ejemplos comentados.
11. **Predicción del EX oculto.** EX_val × un factor de ajuste por dominio nuevo (nombres abreviados, más preguntas
    difíciles) → intervalo **[X ± Y]**, justificado con el desglose por nivel y los pesos 1/2/3.
12. **Conclusiones y trabajo futuro.** Qué funcionó, qué no, y cómo seguir en el Proyecto Final: más datos difíciles,
    few-shot y corrección semántica.
