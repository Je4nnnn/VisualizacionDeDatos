# E1 ? Diagn?stico Chilexpress

Integrantes: Jean Dupraz, Matias Sandoval y Benjamin V?squez.

## Documentos principales

- `resultados/E1/Diagnostico.pdf`: informe de cinco p?ginas.
- `E1_diagnostico.ipynb`: notebook ejecutado, con identificaci?n del equipo.
- `resultados/E1/diccionario_revisado.csv`, `perfil_calidad.csv`, `matriz_reglas.csv` y `fichas_indicadores.csv`: productos solicitados.
- El resto de `resultados/E1/`: gr?ficos y evidencia del an?lisis.
- `INFORME_DESARROLLO.md` y `AUDITORIA_FINAL_E1.md`: metodolog?a, revisi?n y limitaciones.

## Reproducci?n

Conservar esta estructura. Desde esta carpeta, en PowerShell, crear un entorno con Python compatible (entorno probado: Python 3.14.3):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r desarrollo/requirements-lock.txt
.\.venv\Scripts\python.exe desarrollo/ejecutar_notebook.py
.\.venv\Scripts\python.exe desarrollo/validar_resultados.py
```

Tambi?n puede abrirse el notebook con el int?rprete del entorno y ejecutar todas sus celdas. La ejecuci?n regenera los resultados y el informe. El generador ejecutar_notebook.py reconstruye el notebook; para conservar su portada, preferir ejecutar el notebook existente.

Las fuentes docentes y sus plantillas se conservan porque el validador comprueba sus hashes. No son productos completados adicionales. El PDF de instrucciones se incluye por la misma raz?n. No se necesita la carpeta de auditor?a temporal para reproducir el an?lisis.

## Preparaci?n de esta carpeta

Se copiaron ?nicamente entregables, fuentes y dependencias necesarias, excluyendo entornos, cach?s, wheels, archivos del editor y copias temporales. Los originales de trabajo no se eliminaron ni alteraron. Se agreg? la identificaci?n del equipo al notebook y se actualiz? la copia de la auditor?a con esa confirmaci?n; no se cambiaron c?lculos ni salidas. La ejecuci?n acad?mica por un compa?ero a?n debe completarse.
