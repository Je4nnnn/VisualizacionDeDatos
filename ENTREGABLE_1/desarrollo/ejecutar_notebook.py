"""Crea y ejecuta E1 desde kernel nuevo; falla si cualquier celda falla."""
from pathlib import Path
import sys, os
ROOT=Path(__file__).resolve().parents[1]
for key,folder in [('IPYTHONDIR','ipython'),('JUPYTER_CONFIG_DIR','config'),('JUPYTER_DATA_DIR','data'),('JUPYTER_RUNTIME_DIR','runtime'),('MPLCONFIGDIR','matplotlib')]:
    target=ROOT/'.jupyter_e1'/folder; target.mkdir(parents=True,exist_ok=True); os.environ[key]=str(target)
import nbformat
from nbclient import NotebookClient
from jupyter_client.kernelspec import KernelSpecManager
import json
ROOT=Path(__file__).resolve().parents[1]
kernel_dir=ROOT/'desarrollo'/'kernel_e1'
kernel_dir.mkdir(exist_ok=True)
(kernel_dir/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],'display_name':'Python E1 local','language':'python'}),encoding='utf-8')
nb=nbformat.v4.new_notebook()
nb.cells=[nbformat.v4.new_markdown_cell('''# E1 — Diagnóstico y necesidades Chilexpress
Datos sintéticos. Instrucciones: PDF E1 de tres páginas y enunciado general.
Se preservan los tres lotes y sus cortes. Ver INFORME_DESARROLLO.md para audiencias, preguntas, metodología, límites y decisiones. El módulo local contiene el procedimiento íntegro, comentado y reproducible; esta sesión lo ejecuta desde cero.
La recomendación es preliminar; no demuestra causalidad. Asistencia de IA declarada. No se simulan pruebas humanas.'''),nbformat.v4.new_code_cell('''from pathlib import Path
import sys
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p/'desarrollo'/'analisis_e1.py').exists())
sys.path.insert(0,str(ROOT/'desarrollo'))
from analisis_e1 import run
resumen = run()
'''),nbformat.v4.new_code_cell('''import pandas as pd
from IPython.display import display, Image, Markdown
OUT = ROOT/'resultados'/'E1'
for nombre in ['inventario','lotes','matriz_reglas','perfil_calidad','ranking_turnos','cambio_sla','ranking_estandarizado','comparacion_metas','fichas_indicadores']:
    display(Markdown('### '+nombre))
    display(pd.read_csv(OUT/(nombre+'.csv')))
'''),nbformat.v4.new_code_cell('''for nombre in ['01_distribucion','02_categorias','03_temporal','04_segmentos','05_bivariado','06_faltantes']:
    display(Image(filename=str(OUT/(nombre+'.png'))))
display(Markdown((ROOT/'INFORME_DESARROLLO.md').read_text(encoding='utf-8')))
''')]
nb.metadata['kernelspec']={'name':'e1_local','display_name':'Python E1 local','language':'python'}
nbformat.write(nb,ROOT/'E1_diagnostico.ipynb')
manager=KernelSpecManager(kernel_dirs=[str(ROOT/'.jupyter_e1'/'share'/'jupyter'/'kernels')])
manager.install_kernel_spec(str(kernel_dir),kernel_name='e1_local',user=False,prefix=str(ROOT/'.jupyter_e1'))
manager.kernel_dirs.insert(0,str(ROOT/'.jupyter_e1'/'share'/'jupyter'/'kernels'))
client=NotebookClient(nb,timeout=600,kernel_name='e1_local',resources={'metadata':{'path':str(ROOT)}})
# KernelManager explícito evita depender de un kernel global o del PATH.
from jupyter_client import KernelManager
client.km=KernelManager(kernel_name='e1_local',kernel_spec_manager=manager)
client.execute()
nbformat.write(nb,ROOT/'E1_diagnostico.ipynb')
assert all(o.output_type!='error' for c in nb.cells if c.cell_type=='code' for o in c.get('outputs',[]))
print('Notebook ejecutado sin errores:',ROOT/'E1_diagnostico.ipynb')
