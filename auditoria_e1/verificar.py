from pathlib import Path
import os, sys, json, hashlib, csv, math
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager

ROOT=Path(__file__).resolve().parents[1]
COPY=ROOT/'auditoria_e1/reproduccion'
for key in ['IPYTHONDIR','JUPYTER_CONFIG_DIR','JUPYTER_DATA_DIR','JUPYTER_RUNTIME_DIR','MPLCONFIGDIR']:
    p=ROOT/'auditoria_e1/cache'/key; p.mkdir(parents=True,exist_ok=True); os.environ[key]=str(p)
kd=ROOT/'auditoria_e1/kernel'; kd.mkdir(exist_ok=True)
(kd/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],'display_name':'Auditoria E1','language':'python'}))
manager=KernelSpecManager(kernel_dirs=[str(kd.parent)])
nb=nbformat.read(COPY/'E1_diagnostico.ipynb',as_version=4)
for cell in nb.cells:
    if cell.cell_type=='code': cell.outputs=[]; cell.execution_count=None
client=NotebookClient(nb,timeout=600,kernel_name='kernel',resources={'metadata':{'path':str(COPY)}})
client.km=KernelManager(kernel_name='kernel',kernel_spec_manager=manager)
client.execute()
nbformat.write(nb,COPY/'E1_diagnostico.ipynb')
print('Notebook original ejecutado desde cero en copia.',flush=True)

def dt(v):
    if not v: return None
    try: return datetime.strptime(v,'%d/%m/%Y %H:%M:%S').replace(tzinfo=timezone.utc) if '/' in v else datetime.fromisoformat(v.replace('Z','+00:00'))
    except ValueError: return None
def num(v):
    try: return float(v.replace(',','.'))
    except ValueError: return None
counts=dict(entidades=0,expuestos=0,evaluados=0,incumplimientos=0,desconocidos=0,cancelados=0,no_expuestos=0,futuros=0,promesa_no_determinable=0)
delays=[]; costs=[]; claims=[]; pairs=[]; unknown_types={}
for lot,cut in [('base','2025-07-08'),('actualizacion','2025-08-08'),('ampliacion','2026-01-08')]:
    cut=dt(cut+'T00:00:00Z'); seen=set()
    with (ROOT/'02_Chilexpress_Alumnos/datos'/lot/'envios.csv').open(encoding='utf-8',newline='') as f:
        for r in csv.DictReader(f):
            key=tuple(r.values())
            if key in seen: continue
            seen.add(key); counts['entidades']+=1
            start,promise,end=map(dt,[r['fecha'],r['compromiso'],r['entrega']])
            active=r['estado']!='cancelado'
            if not active: counts['cancelados']+=1
            cost,claim,weight=map(num,[r['costo_operacion_clp'],r['reclamo'],r['peso_kg']])
            if active:
                if cost is not None and cost>=0: costs.append(cost)
                if claim in [0,1]: claims.append(claim)
                if cost is not None and cost>=0 and weight is not None and weight>0: pairs.append((weight,cost))
            valid_promise=start is not None and promise is not None and start<=promise
            exposed=active and valid_promise and promise<=cut
            if not exposed:
                if active:
                    counts['no_expuestos']+=1
                    counts['futuros' if valid_promise and promise>cut else 'promesa_no_determinable']+=1
                continue
            counts['expuestos']+=1
            valid_end=r['estado']=='entregado' and end is not None and start<=end<=cut
            if not (valid_end or r['estado']=='en_transito'):
                counts['desconocidos']+=1
                label='entrega_ausente' if end is None else 'entrega_incoherente'
                unknown_types[label]=unknown_types.get(label,0)+1
                continue
            counts['evaluados']+=1
            late=r['estado']=='en_transito' or end>promise
            counts['incumplimientos']+=int(late)
            delays.append(max(0,((end if valid_end else cut)-promise).total_seconds()/3600))
fulfilled=counts['evaluados']-counts['incumplimientos']
stats=dict(cumplimiento_pct=100*fulfilled/counts['evaluados'],atraso_media_h=float(np.mean(delays)),atraso_p90_h=float(np.quantile(delays,.9)),costo_medio_clp=float(np.mean(costs)),reclamos_pct=100*float(np.mean(claims)),rho_peso_costo=float(pd.DataFrame(pairs).rank().corr().iloc[0,1]))
actual=json.loads((ROOT/'resultados/E1/resumen.json').read_text())
assert all(counts[k]==actual[k] for k in ['entidades','expuestos','evaluados','incumplimientos','desconocidos'])
assert all(math.isclose(v,actual[k],rel_tol=1e-12) for k,v in stats.items())
comparisons={}
for p in (ROOT/'resultados/E1').glob('*.csv'):
    q=COPY/'resultados/E1'/p.name
    pd.testing.assert_frame_equal(pd.read_csv(p),pd.read_csv(q))
    comparisons[p.name]='PASS'
images={p.name:hashlib.sha256(p.read_bytes()).hexdigest()==hashlib.sha256((COPY/'resultados/E1'/p.name).read_bytes()).hexdigest() for p in (ROOT/'resultados/E1').glob('*.png')}
assert len(images)==6 and all(images.values())
from pypdf import PdfReader
pdf=PdfReader(ROOT/'resultados/E1/Diagnostico.pdf'); pdf2=PdfReader(COPY/'resultados/E1/Diagnostico.pdf')
assert [p.extract_text() for p in pdf.pages]==[p.extract_text() for p in pdf2.pages]
prior=json.loads((ROOT/'auditoria_e1/hashes_previos.json').read_text())
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==v for p,v in prior.items())
result=dict(conteos=counts,cumplidos=fulfilled,desconocidos_tipo=unknown_types,estadisticos=stats,costo_n=len(costs),reclamos_n=len(claims),reclamos=int(sum(claims)),pares_n=len(pairs),sensibilidad_pct=[100*fulfilled/counts['expuestos'],100*(fulfilled+counts['desconocidos'])/counts['expuestos']],tablas=comparisons,figuras_identicas=images,pdf_paginas=len(pdf.pages),pdf_texto_reproducido=True,notebook_nuevo_kernel=True,archivos_previos_preservados=len(prior))
(ROOT/'auditoria_e1/evidencia.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(result,indent=2,ensure_ascii=False))
