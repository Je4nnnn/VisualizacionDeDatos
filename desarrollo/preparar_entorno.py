"""Descarga wheels compatibles desde API JSON de PyPI evitando el índice HTML lento.
Se ejecuta con Python del sistema (requests disponible) y solo instala en .venv.
"""
from pathlib import Path
import requests, subprocess, sys
from pip._vendor.packaging.requirements import Requirement
from pip._vendor.packaging.version import Version, InvalidVersion
from pip._vendor.packaging.tags import sys_tags
from pip._vendor.packaging.utils import parse_wheel_filename, canonicalize_name
ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'desarrollo'/'wheels'; CACHE.mkdir(exist_ok=True)
tags=set(sys_tags()); selected={}; constraints={}; pending=[]
initial=(ROOT/'02_Chilexpress_Alumnos'/'requirements.txt').read_text().splitlines()+['pypdf','nbclient','ipykernel']
pending.extend(Requirement(x) for x in initial if x.strip())
while pending:
    req=pending.pop(0)
    if req.marker and not any(req.marker.evaluate({'extra':x}) for x in (['']+list(req.extras))): continue
    name=canonicalize_name(req.name)
    constraints.setdefault(name,[]).append(req.specifier)
    if name in selected:
        if not all(s.contains(selected[name][0],prereleases=False) for s in constraints[name]): raise RuntimeError(f'Conflicto {name}: {constraints[name]}')
        continue
    j=requests.get(f'https://pypi.org/pypi/{name}/json',timeout=30); j.raise_for_status(); j=j.json()
    versions=[]
    for v in j['releases']:
        try: parsed=Version(v)
        except InvalidVersion: continue
        if not parsed.is_prerelease and all(s.contains(parsed,prereleases=False) for s in constraints[name]): versions.append(parsed)
    chosen=None
    for version in sorted(versions,reverse=True):
        info=requests.get(f'https://pypi.org/pypi/{name}/{version}/json',timeout=30).json()
        for file in info.get('urls',[]):
            if not file['filename'].endswith('.whl') or file.get('yanked'): continue
            try: compatible=bool(parse_wheel_filename(file['filename'])[3]&tags)
            except Exception: continue
            if compatible: chosen=(str(version),file,info); break
        if chosen: break
    if not chosen: raise RuntimeError('No wheel compatible: '+name)
    version,file,info=chosen
    print(name,version,flush=True)
    path=CACHE/file['filename']
    data=requests.get(file['url'],timeout=90); data.raise_for_status(); path.write_bytes(data.content)
    import hashlib
    assert hashlib.sha256(data.content).hexdigest()==file['digests']['sha256']
    selected[name]=(version,path)
    for dep in info['info'].get('requires_dist') or []:
        child=Requirement(dep)
        if child.marker and not any(child.marker.evaluate({'extra':e}) for e in (['']+list(req.extras))): continue
        # Ya evaluada en el contexto del paquete padre.
        child.marker=None; pending.append(child)
subprocess.run([str(ROOT/'.venv'/'Scripts'/'python.exe'),'-m','pip','--disable-pip-version-check','install','--no-index','--no-deps',*[str(v[1]) for v in selected.values()]],check=True)
(ROOT/'desarrollo'/'requirements-lock.txt').write_text('\n'.join(f'{n}=={v[0]}' for n,v in sorted(selected.items()))+'\n',encoding='utf-8')
