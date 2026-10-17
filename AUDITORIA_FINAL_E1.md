# Auditoría final E1 — Chilexpress

Fecha: 15 de octubre de 2026. Datos sintéticos docentes.

## Dictamen

La actividad está técnicamente preparada para entrega: el notebook se ejecutó desde cero en un kernel nuevo, se reprodujeron las 28 tablas CSV y las seis visualizaciones, y se confirmaron independientemente los seis KPI. El PDF cumple las cinco páginas máximas y contiene audiencia, decisión, resultados, recomendación, límites y limpieza. No se detectó una inconsistencia numérica que requiera cambiar los resultados.

La entrega académica definitiva queda **condicionada a completar la revisión por un compañero y confirmar la identificación de los tres integrantes**. No se acredita una revisión humana inexistente. Hay una observación de presentación: la trazabilidad de cada hallazgo está distribuida entre el PDF, el informe y los CSV; conviene incorporar la tabla de hallazgos de esta auditoría al material de lectura. No se estima una nota ni se sustituye la evaluación del profesor.

## Alcance y método

Se releyeron íntegramente las tres páginas de `Chilexpress_E1_Diagnostico.docx.pdf`. También se contrastaron el enunciado general DOCX, README, metadatos, diccionario, notebook, código de análisis, informe, PDF y tablas resultantes. El PDF específico E1 delimita esta auditoría; no se inventan obligaciones de E2–E4.

La prueba usó una copia en `auditoria_e1/reproduccion/`, manteniendo las rutas relativas. Se ejecutó el **notebook existente**, borrando sus salidas solamente en la copia, mediante nbclient y un kernel nuevo con el intérprete local. No se usó el generador `ejecutar_notebook.py`, que reconstruiría el notebook. El script de auditoría recalculó por separado las poblaciones y los seis KPI con lectura CSV y datetime; empleó NumPy para media y cuantiles, y rangos de pandas para Spearman. Esta última parte comparte bibliotecas estadísticas con el desarrollo, pero no llama a su lógica de cálculo.

Evidencia ejecutable: `auditoria_e1/verificar.py`. Resultado: `auditoria_e1/evidencia.json`. Se comprobó por SHA-256 la conservación de los 105 archivos preexistentes incluidos en `auditoria_e1/hashes_previos.json` (excluidos entorno, cachés, wheels y metadatos del editor). La reproducción también verifica los nueve CSV contra el manifiesto docente.

## Matriz de cumplimiento

PASS = requisito respaldado por evidencia; FAIL = incumplimiento demostrado; PENDIENTE = comprobación o acción externa todavía no acreditada. Las observaciones de mejora no convierten automáticamente un PASS en FAIL.

| ID / origen | Requisito | Estado | Evidencia y fundamento |
|---|---|---|---|
| T1, p.1 | Audiencias ejecutiva y operacional | PASS | PDF p.1; informe, Objetivos y audiencia. Coordinación de capacidad y supervisores de zona. |
| T1, p.1 | Tres preguntas medibles y acciones asociadas | PASS | PDF p.1: concentración de incumplimientos, cola del atraso y prioridad multicriterio; vincula cada respuesta con una acción. |
| T2, p.1 | Archivos, filas, claves, granularidad, procedencia y hash | PASS | `inventario.csv`: nueve fuentes, dimensiones y SHA-256; código valida claves y cardinalidad. |
| T2, p.1 | Períodos y cortes de los tres lotes | PASS | `lotes.csv`, `periodos_observados.csv`, PDF p.2. Cortes UTC preservados. |
| T2, p.1 | Separar filas físicas, entidades y exposición | PASS | 240.700, 240.000 y 233.657 respectivamente; `poblaciones.csv` y recálculo independiente. |
| T3, p.1 | Tipo, escala, unidad, nulabilidad y contratos | PASS | `diccionario_revisado.csv`, `matriz_reglas.csv`. Condición especial de entrega; unidades revisadas y escalas. Algunas categorías conservan el tipo técnico object: la escala nominal aclara su interpretación. |
| T3, p.1 | Revisar ID, fecha de negocio y fecha de carga | PASS | ID único tras deduplicación; fecha definida como despacho UTC; latencia calculada contra primera carga, nunca contra hoy. |
| T4, p.1 | Distribución | PASS | `01_distribucion.png`, `distribuciones.csv`: atraso, ceros, P90, P99 y extremos. |
| T4, p.1 | Categorías | PASS | `02_categorias.png`, `categorias.csv`: estados por entidades. |
| T4, p.1 | Evolución temporal | PASS | `03_temporal.png`, `evolucion_mes.csv`: tasa mensual con denominadores. |
| T4, p.1 | Comparación de segmentos | PASS | `04_segmentos.png`, `ranking_turnos.csv`, `segmentos_mes.csv`. Gráfico de cantidad complementado por tasas en tablas. |
| T4, p.1 | Relación bivariada interpretable | PASS | `05_bivariado.png`, `correlacion.csv`: peso/costo, 229.308 pares válidos, Spearman; asociación sin causalidad. |
| T4, p.1 | Faltantes por segmento | PASS | `06_faltantes.png`, `faltantes_segmento.csv`, lote/ruralidad/servicio. |
| T5, p.1 | Perfil de calidad por lote y segmento | PASS | `perfil_calidad.csv`: seis reglas por lote/ruralidad/servicio, fallas y denominadores. |
| T5, p.1 | Defectos, extremos plausibles y ausencias estructurales | PASS | Informe, Calidad y resultados; `nulos_campos_segmento.csv`, `dominios.csv`. Peso negativo es defecto; un positivo extremo requiere investigación; entrega ausente depende del estado. |
| T5, p.1 | Estimar indicadores afectados por sesgo | PASS | Informe y `matriz_reglas.csv`, justificación/impacto_KPI: fechas afectan cumplimiento y atraso; faltantes rurales afectan peso/costo y composición. |
| T6, p.1 | Seis KPI con denominadores | PASS | `fichas_indicadores.csv`, K1–K6; recálculo independiente de todos los resultados, detallado abajo. |
| T6, p.1 | Seis métricas de calidad | PASS | Fichas Q1–Q6, matriz y perfil: peso, entrega obligatoria, consistencia temporal, FK, latencia y SLA histórico. Son tasas de falla, no porcentajes de éxito. |
| T6, p.1 | Dos o más límites de interpretación | PASS | PDF p.5 e informe: censura del tránsito, madurez desigual, desconocidos, cambio SLA y ausencia de causalidad. |
| R1, p.2 | Tasa y cantidad por zona/semana/servicio; numeradores, denominadores y mínimo | PASS | `zona_semana_servicio.csv`: incumplimientos, cumplimientos, denominador, exposición, desconocidos, tasas y minimo_100. El mínimo 100 es una política propuesta y explícita. |
| R2, p.2 | Contrastar media/P90 e interpretar cola | PASS | `distribuciones.csv`, tablas segmentadas e informe. Se amplía la interpretación cuantitativa en esta auditoría; la media no siempre es menor que P90. |
| R3, p.2 | Mismo servicio/ruralidad; mezcla y SLA octubre | PASS | `comparacion_mismo_servicio_ruralidad.csv`, `ranking_estandarizado.csv`, `cambio_sla.csv`; pesos comunes dentro de ruralidad y advertencia de no causalidad. |
| R4, p.2 | Diez turnos, dos zonas y regla explícita | PASS | `ranking_turnos.csv`: zonas 8 y 4, cinco turnos cada una; score y restos mayores documentados. |
| R4, p.2 | Dos rankings y medición del piloto | PASS | Ranking de tasa frente a score; informe y PDF p.4: cuatro semanas base/intervención, controles, madurez equivalente y seis KPI. |
| S1, p.2 | Entrega anterior al despacho y entregado sin fecha | PASS | Q2=350 ausentes; Q3=350 incoherentes; ambos conservados como resultados desconocidos cuando están expuestos. |
| S1, p.2 | Ausencia estructural en tránsito/cancelado | PASS | `nulos_campos_segmento.csv`; no se considera defecto Q2 en esos estados. |
| S2, p.2 | Faltantes rurales y diferencias de servicio | PASS | Perfil, mapa de faltantes e informe: peso ausente rural 4,35% frente a urbano 0,70%, ponderado por envíos. |
| S3, p.2 | Tránsito vencido incumplido; separar cancelados/no vencidos | PASS | Máscaras en `analisis_e1.py` y recálculo independiente; 6.011 cancelados separados. No hay promesas futuras válidas observadas; los 332 restantes son no determinables. |
| S4, p.2 | No recuperar campos sin evidencia ni atribuir causalidad | PASS | `evidencia_eventos.csv` informa candidatos sin reparar fechas; PDF p.4–5 e informe limitan inferencias. |
| P1, p.3 | Notebook desde cero con tres lotes y complementarios | PASS | Prueba nueva en copia aislada, salidas ejecutadas sin error; `auditoria_e1/evidencia.json`. Requiere distribuir el módulo local y las fuentes. |
| P2, p.3 | Diagnostico.pdf de hasta cinco páginas y contenidos pedidos | PASS | Cinco páginas: audiencia/decisión, metodología, resultados, recomendación/piloto, calidad/límites/limpieza. Texto reproducido idéntico. |
| P3, p.3 | Diccionario, perfil y matriz con reglas justificadas | PASS | Los tres CSV existen y se reproducen. La matriz contiene campo, condición, severidad, denominador, tratamiento, justificación e impacto; el perfil enlaza por regla_id. |
| P4, p.3 | Fichas de seis KPI/seis métricas y trazabilidad | PASS | Doce fichas: fórmula, columnas, población, período, denominador, responsable y acción; matriz aporta denominadores numéricos de calidad. |
| Revisión, p.3 | Ejecución posible desde una sesión nueva | PASS | Kernel nuevo y notebook original en copia; 28 CSV iguales y seis PNG idénticos por SHA-256. No equivale a instalar desde cero en otro equipo. |
| Revisión, p.3 | Cada hallazgo con evidencia, período, unidad, población y límite | PASS | Evidencia distribuida entre informe, PDF y CSV; tabla consolidada de esta auditoría debajo. Recomendable adjuntarla para evitar que el lector reconstruya referencias. |
| Revisión, p.3 | Separar observación, hipótesis y decisión | PASS | Observaciones estadísticas; score propuesto y piloto como hipótesis; asignación explícita como decisión preliminar. No se afirma efecto demostrado. |
| Revisión humana | Compañero reproduce y revisa entrega | PENDIENTE | El PDF pide que un compañero pueda ejecutar; la posibilidad técnica está probada. No hay registro de ejecución o revisión por un compañero. |
| Enunciado general | Equipo de tres integrantes identificado | PENDIENTE | El DOCX general exige equipo de tres; no se encontraron nombres en los entregables revisados. Confirmar integrantes e identificación antes de presentar. |

No se detectaron FAIL demostrados en los requisitos técnicos revisados. PASS no implica automáticamente puntaje completo: profundidad, claridad y valoración de las propuestas corresponden al profesor.

## Conciliación de poblaciones y denominadores

| Concepto | Cantidad | Relación |
|---|---:|---|
| Filas físicas principales | 240.700 | Antes de deduplicar |
| Copias exactas adicionales | 700 | Se quitan solo en la copia analítica |
| Envíos únicos | 240.000 | 240.700 − 700 |
| Cancelados | 6.011 | Fuera del cumplimiento |
| No cancelados con promesa no determinable | 332 | No se puede establecer exposición válida |
| No cancelados con promesa válida futura al corte | 0 | No confundir con los 332 anteriores |
| Expuestos a promesa vencida | 233.657 | 240.000 − 6.011 − 332 |
| Desconocidos entre expuestos | 700 | 350 entregas ausentes + 350 incoherentes |
| Evaluados | 232.957 | 233.657 − 700 |
| Incumplimientos conocidos | 40.100 | Incluye tránsito vencido |
| Cumplimientos conocidos | 192.857 | 232.957 − 40.100 |

**Cumplimiento observado = 192.857 / 232.957 × 100 = 82,7865228347% = 82,79%.** Incumplimiento observado = 17,2134771653%.

No corresponde usar 240.000 como denominador de este KPI: incluiría cancelados, promesas no determinables y resultados desconocidos. Tampoco corresponde restar solo 40.100 y 700 de 240.000 para deducir cumplimientos. Los 700 duplicados y los 700 desconocidos son conceptos diferentes y su igualdad numérica es una coincidencia.

Si se toma toda la exposición vencida y se asignan los desconocidos a los dos extremos, cumplimiento mínimo = 192.857/233.657 = **82,54%**; máximo = (192.857+700)/233.657 = **82,84%**. Es un intervalo de sensibilidad, no un intervalo de confianza. El 82,79% describe únicamente casos evaluables y su exclusión puede introducir sesgo.

Corrección de interpretación registrada: `no_cancelados_no_expuestos` no significa necesariamente «promesas todavía no vencidas». En estos datos los 332 casos son no determinables; el informe ya advierte esta distinción en Hallazgos segmentados. No hay un error de cálculo que corregir.

## Verificación estadística y KPI

| Indicador | Resultado recalculado | Población/denominador |
|---|---:|---|
| K1 Cumplimiento | 82,7865228347% | 192.857 / 232.957 evaluados |
| K2 Volumen incumplido | 40.100 envíos | Conteo conocido, no porcentaje |
| K3 Atraso medio | 46,5144993902 h | 232.957 evaluados, incluye ceros |
| K4 P90 de atraso | 47,2956111111 h | Mismos evaluados; cuantil lineal 0,90 |
| K5 Costo medio | 4.670,6623730175 CLP/envío | 233.989 no cancelados con costo válido |
| K6 Reclamos | 7,6358290347% | 17.867 / 233.989 no cancelados con reclamo 0/1 |
| Asociación auxiliar | Spearman 0,4614161929 | 229.308 pares peso>0 y costo>=0, no cancelados |

Se incluyeron ceros válidos y se excluyeron campos inválidos según el KPI. El atraso es max(0, entrega−compromiso); en tránsito vencido se usa corte−compromiso. No es duración total del envío y el tránsito está censurado. No se detectan costos negativos ni reclamos fuera de 0/1; por ello las medias de costo zonal sin filtro explícito de negativos coinciden con la política de costo válido para este paquete. Esa equivalencia debe reevaluarse con otros datos.

El costo medio de `distribuciones.csv` es 4.553,68 CLP porque describe los **240.000 envíos**, incluidos cancelados; K5 usa no cancelados. La diferencia es válida, no un error. El P90 y el promedio tampoco tienen un orden obligatorio: el 1% extremo puede elevar la media por encima del P90. Aquí P99=1.815,73 h y máximo=4.479,43 h evidencian una cola muy larga; no se deben borrar extremos solo por su magnitud.

Las reglas Q1–Q6 se calcularon sobre sus poblaciones específicas: 3.850/240.000; 350/229.418 entregados; 350/229.068 entregados con fecha; 580/240.000 sin referencia de destino; 37.776/240.000 con latencia inválida/fuera de 0–48 h; 920/240.000 sin SLA histórico coincidente. Las tasas son de defecto. Las tablas regeneradas coinciden; este control no aporta una segunda implementación independiente de cada celda del perfil.

El score usa percentiles de volumen, tasa y costo inverso con pesos 45/30/15%, más 10% ruralidad. La selección es zonas 8 y 4, coincidente con los dos primeros puestos por tasa. Sus 3.300 y 3.220 incumplimientos generan cuotas 5,0613 y 4,9387: restos mayores asigna **5 y 5**. Es una política propuesta, no una optimización causal o económica demostrada.

## Hallazgos consolidados para lectura académica

Todos corresponden a despachos de 2025 y al corte particular de cada lote; no son datos reales de la empresa.

| Observación | Evidencia | Unidad y población | Límite e implicación |
|---|---|---|---|
| 82,79% de cumplimiento y 40.100 incumplimientos | `resumen.json`, `poblaciones.csv`, PDF p.3 | % y envíos; 232.957 evaluados | 700 desconocidos y 332 no determinables; publicar denominadores antes de priorizar. |
| Media 46,51 h, P90 47,30 h, P99 1.815,73 h | `distribuciones.csv`, figura 01 | Horas; evaluados con ceros | Tránsito censurado; combinar frecuencia y cola, no inferir tiempo final. |
| Zona 8: media 63,78 h/P90 102,22 h; zona 4: 59,02/103,11 h | `ranking_turnos.csv`, figura 04 | Horas; 9.765 y 9.687 evaluados zonales | Mezcla y SLA distintos; comprobar estratos antes de interpretar deterioro. La cola justifica seguimiento además de la media. |
| Peso ausente rural 4,35%, urbano 0,70% | `faltantes_segmento.csv`, figura 06 | % sobre entidades con ruralidad conocida, ponderación por n | No identifica mecanismo causal de ausencia; limita comparación de peso/costo. |
| Peso/costo asociados, rho=0,461 | `correlacion.csv`, figura 05 | Sin unidad; 229.308 pares válidos | No demuestra que cambiar peso cause variación equivalente de costo. |
| SLA rural cambia en octubre: estándar 96→108 h; express 48→60 h | `cambio_sla.csv`, comparación estratificada | Horas; registros con SLA vigente | Un cambio de cumplimiento puede reflejar una promesa distinta, sin cambio operacional. |
| Costo 4.670,66 CLP y reclamos 7,64% | `resumen.json`, fichas K5/K6 | CLP/envío y %; 233.989 no cancelados | Población distinta de cumplimiento; costo promedio no es costo marginal por turno. |

Hipótesis: el refuerzo podría mejorar el desempeño de zonas seleccionadas. Decisión propuesta: cinco turnos para cada zona. Verificación futura: piloto con línea base, controles y ventanas de maduración equivalentes. El historial no demuestra el resultado del piloto.

## Reproducibilidad y límites de la prueba

El archivo `auditoria_e1/evidencia.json` enumera los 28 CSV comparados mediante igualdad de DataFrames y los seis PNG idénticos por SHA-256. El PDF mantiene cinco páginas y el mismo texto; no se exige identidad binaria del PDF porque sus metadatos pueden variar. Los KPI independientes coinciden con tolerancia relativa 1e-12. Las imágenes y tablas existentes no se sobrescribieron.

La prueba acredita ejecución nueva en el entorno instalado, no una instalación limpia en otro computador ni revisión humana. El notebook importa `desarrollo/analisis_e1.py`: **el ipynb solo no es autónomo**. Conservar rutas, datos y dependencias. Para repetir esta auditoría desde la raíz, con el entorno instalado y la copia aislada presente:

```powershell
.\.venv\Scripts\python.exe auditoria_e1/verificar.py
```

Ese comando escribe solamente en `auditoria_e1/`. La reproducción académica habitual está descrita en `INFORME_DESARROLLO.md`; sus comandos regeneran los entregables, por lo que deben ejecutarse sobre una copia si se desea conservarlos.

## Obligaciones, recomendaciones y pendientes

- **Obligatorio E1:** los seis trabajos, preguntas/riesgos, diagnóstico de situaciones, cuatro productos y condiciones de reproducibilidad del PDF. Se verificaron en la matriz.
- **Pendiente académico:** confirmar tres integrantes e identificación del equipo; obtener revisión de un compañero y registrar fecha/entorno/resultado. El criterio literal es que pueda ejecutar: ya se acreditó técnicamente, pero no hay evidencia de participación del compañero.
- **Recomendaciones de presentación:** hacer explícitos en el PDF los 192.857 cumplimientos y la conciliación completa; trasladar referencias y límites junto a cada hallazgo; incluir P99 para explicar mejor la cola. No son correcciones de resultados ni exigencias adicionales de gráficos dentro del PDF.
- **Políticas propuestas, no impuestas por el docente:** mínimo 100, pesos 45/30/15/10, cuatro semanas base y cuatro de intervención y umbrales cero de defectos. Deben seguir declaradas como propuestas.
- **Trabajo futuro fuera de E1:** ejecutar realmente el piloto, desarrollar dashboard terminado, pruebas con usuarios y tareas E2–E4. E1 exige proponer cómo medir el piloto, no ejecutarlo. La ausencia de documentos de futuras entregas no bloquea el diagnóstico E1 disponible.
- **No requerido:** predicción, nota autocalculada, inventar campos verdaderos dañados o afirmar causalidad.

## Registro de modificaciones

No se modificaron archivos preexistentes, ni originales docentes ni entregables. Se añadieron esta auditoría y `auditoria_e1/`: hashes previos, script de verificación, evidencia JSON, copia de reproducción y cachés/kernel locales. Las únicas regeneraciones ocurrieron dentro de esa copia. No fue necesario corregir código, datos, KPI o PDF: no se demostró un error numérico. Las precisiones de denominadores, costo y no exposición quedan registradas aquí y no alteran resultados.

## Archivos para presentar al profesor

Entregar un ZIP conservando la estructura desde la raíz:

1. `E1_diagnostico.ipynb` ejecutado.
2. `resultados/E1/Diagnostico.pdf` (cinco páginas).
3. `resultados/E1/diccionario_revisado.csv`, `perfil_calidad.csv`, `matriz_reglas.csv` y `fichas_indicadores.csv`.
4. Resto de `resultados/E1/`: seis PNG, tablas de respaldo y JSON de resultados/validación/versiones.
5. `desarrollo/analisis_e1.py`, `ejecutar_notebook.py`, `validar_resultados.py`, `requirements-lock.txt` y `fuentes_sha256.json`, para reproducir y verificar.
6. `02_Chilexpress_Alumnos/` con los datos docentes originales y sus metadatos, diccionario y documentos de contexto; si el profesor ya distribuyó las fuentes, acordar su reutilización manteniendo las rutas.
7. `INFORME_DESARROLLO.md` y `AUDITORIA_FINAL_E1.md`. Como evidencia adicional, `auditoria_e1/verificar.py`, `evidencia.json` y `hashes_previos.json`; la copia completa de auditoría no es necesaria para evaluar E1.

No incluir `.venv`, `.jupyter_e1`, `.idea`, `__MACOSX`, cachés, wheels ni la copia duplicada de reproducción. Incorporar la identificación del equipo antes de enviar. El notebook necesita los datos y el módulo: entregar solamente el PDF y el ipynb impediría reproducir la actividad.
