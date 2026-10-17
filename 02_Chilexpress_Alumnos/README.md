# Chilexpress cumplimiento y capacidad de reparto

Versión ampliada del 1 de octubre de 2026. Datos, metas y encargos simulados; no representan resultados reales de la empresa.

## Comenzar
Leer 00_Enunciado_general.docx y los cuatro Word de entregas/. Abrir 00_inicio.ipynb desde esta carpeta. Crear un entorno Python 3.11 o superior y ejecutar `pip install -r requirements.txt`. Registrar las versiones probadas al entregar.

## Inventario
Se conservan los CSV originales de datos/base/ y datos/actualizacion/. datos/ampliacion/ agrega exactamente 100.000 filas principales con claves nuevas. Total principal: 240,700; claves distintas: 240,000. Los complementarios son adicionales, no cuentan dentro de las 100.000 nuevas.

Los tres lotes se usan desde E1. En E4 se prueba reingesta idempotente y un cambio de filtro, fórmula, política o vigencia. La incorporación de julio no debe actualizar retroactivamente otros snapshots.

## Contrato
CSV UTF-8, separador coma, decimal punto y nulos vacíos. La ampliación contiene excepciones de formato que deben normalizarse: algunos números con coma decimal sin miles y fechas dd/mm/YYYY HH:MM:SS en UTC, además de ISO 8601. Cargado_en significa primera carga, no última actualización de estado. No comparar antigüedad con la fecha actual.

Los cortes UTC son 2025-07-08, 2025-08-08 y 2026-01-08. Los catálogos históricos usan desde inclusivo y hasta exclusivo. Debe haber exactamente una coincidencia por hecho. Complementarios operacionales y tarifas cubren agosto-diciembre; ausencia anterior es fuera de alcance.

Cada fila principal representa un envío al corte de su lote. Se añaden 100.000 envíos de agosto a diciembre. El detalle de eventos nuevo contiene recepción y un evento posterior por envío; no es otra tabla de envíos para sumar.

Las metas del año están en datos/complementarios/metas_2025_ancho.csv y sustituyen analíticamente metas_ancho.csv; no concatenar ambas versiones. Los historiales sustituyen el catálogo estático para atributos con vigencia; conservar los catálogos originales como fuente.

## Evaluación
E1 10%, E2 15%, E3 25%, E4 individual 10%. Proyecto total 60%; controles 20% y certamen 20%. Seis KPI de negocio, seis métricas de calidad y 4-6 gráficos. No se requiere predicción. La IA debe declararse y verificarse. Las pruebas con usuarios deben ser reales.

## Fuentes
Contexto: https://www.chilexpress.cl/
- pandas uniones: https://pandas.pydata.org/docs/user_guide/merging.html
- pandas datos ausentes: https://pandas.pydata.org/docs/user_guide/missing_data.html
- Wickham Tidy Data: https://www.jstatsoft.org/article/view/v059i10
- Munzner: https://www.cs.ubc.ca/~tmm/vadbook/
