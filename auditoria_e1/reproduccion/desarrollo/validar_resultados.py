"""Recalcula poblaciones con csv/datetime, independientemente de pandas."""
from pathlib import Path
import csv, json, hashlib
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[1]
def date(value):
    if not value: return None
    try:
        return datetime.strptime(value,'%d/%m/%Y %H:%M:%S').replace(tzinfo=timezone.utc) if '/' in value else datetime.fromisoformat(value.replace('Z','+00:00'))
    except ValueError: return None
totals=dict(entidades=0,expuestos=0,evaluados=0,incumplimientos=0,desconocidos=0)
for lot,cut in [('base','2025-07-08'),('actualizacion','2025-08-08'),('ampliacion','2026-01-08')]:
    cut=date(cut+'T00:00:00Z'); seen=set()
    with (ROOT/'02_Chilexpress_Alumnos'/'datos'/lot/'envios.csv').open(encoding='utf-8',newline='') as f:
        for row in csv.DictReader(f):
            values=tuple(row.values())
            if values in seen: continue
            seen.add(values); totals['entidades']+=1
            start,promise,delivery=map(date,[row['fecha'],row['compromiso'],row['entrega']])
            exposed=row['estado']!='cancelado' and start is not None and promise is not None and start<=promise<=cut
            if not exposed: continue
            totals['expuestos']+=1
            valid_delivery=row['estado']=='entregado' and delivery is not None and start<=delivery<=cut
            evaluated=valid_delivery or row['estado']=='en_transito'
            if evaluated:
                totals['evaluados']+=1
                totals['incumplimientos']+=int(row['estado']=='en_transito' or delivery>promise)
            else: totals['desconocidos']+=1
actual=json.loads((ROOT/'resultados'/'E1'/'resumen.json').read_text(encoding='utf-8'))
for key,value in totals.items(): assert actual[key]==value,(key,value,actual[key])
manifest=json.loads((ROOT/'desarrollo'/'fuentes_sha256.json').read_text(encoding='utf-8'))
assert all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest for path,digest in manifest.items())
from pypdf import PdfReader
pdf=PdfReader(ROOT/'resultados'/'E1'/'Diagnostico.pdf')
assert len(pdf.pages)<=5 and all(len(p.extract_text())>100 for p in pdf.pages)
import nbformat
nb=nbformat.read(ROOT/'E1_diagnostico.ipynb',as_version=4)
assert all(c.execution_count is not None and not any(o.output_type=='error' for o in c.outputs) for c in nb.cells if c.cell_type=='code')
evidence=dict(recalculo_independiente=totals,coincidencia=True,fuentes_preservadas=len(manifest),paginas_pdf=len(pdf.pages),notebook_ejecutado_sin_errores=True)
(ROOT/'resultados'/'E1'/'verificacion_independiente.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
print(json.dumps(evidence,indent=2))
