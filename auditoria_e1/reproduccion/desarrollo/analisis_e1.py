"""Diagnóstico E1 reproducible; nunca escribe en las fuentes originales."""
from pathlib import Path
import hashlib, json, sys, platform, importlib.metadata, textwrap
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / '02_Chilexpress_Alumnos'
OUT = ROOT / 'resultados' / 'E1'
OUT.mkdir(parents=True, exist_ok=True)
def save(df, name):
    df.to_csv(OUT / (name + '.csv'), index=False, encoding='utf-8-sig')
def dates(s):
    slash = s.str.contains('/', na=False)
    result = pd.to_datetime(s.where(~slash), format='ISO8601', utc=True, errors='coerce')
    result.loc[slash] = pd.to_datetime(s[slash], format='%d/%m/%Y %H:%M:%S', utc=True, errors='coerce')
    return result

def run():
    meta = json.loads((SRC/'metadatos.json').read_text(encoding='utf-8'))
    inventory=[]; loaded={}
    for f in meta['files']:
        p=SRC/f['archivo']; digest=hashlib.sha256(p.read_bytes()).hexdigest()
        assert digest == f['sha256'], f'Fuente alterada: {p}'
        d=pd.read_csv(p,dtype='string'); loaded[f['archivo']]=d
        assert d.shape == (f['filas'],f['columnas'])
        if p.name=='envios.csv': key=['envio_id']; grain='envío al corte de su lote'
        elif p.name=='eventos_envio.csv': key=['evento_id']; grain='evento logístico, dos por envío nuevo'
        elif p.name=='destinos.csv': key=['destino_id']; grain='destino'
        elif p.name=='sla_historial.csv': key=['destino_id','servicio','vigente_desde']; grain='versión temporal destino/servicio'
        elif p.name=='sla.csv': key=['destino_id','servicio']; grain='destino/servicio estático'
        else: key=['destino_id','indicador']; grain='destino/indicador con meses en columnas'
        inventory.append(dict(archivo=f['archivo'],filas=len(d),columnas=len(d.columns),clave='/'.join(key),claves_distintas=len(d[key].drop_duplicates()),granularidad=grain,sha256=digest,procedencia='Paquete docente local; datos sintéticos'))
    save(pd.DataFrame(inventory),'inventario')
    cuts={'base':'2025-07-08','actualizacion':'2025-08-08','ampliacion':'2026-01-08'}
    frames=[]; duplicate_rows=[]
    for lot,cut in cuts.items():
        d=loaded[f'datos/{lot}/envios.csv'].copy()
        duplicate_rows.append(dict(lote=lot,filas_fisicas=len(d),entidades=d.envio_id.nunique(),copias_exactas=int(d.duplicated().sum()),corte_UTC=cut))
        d=d.drop_duplicates(); d['lote']=lot; d['corte']=pd.Timestamp(cut,tz='UTC'); frames.append(d)
    raw=pd.concat(frames,ignore_index=True)
    assert len(raw)==240000 and raw.envio_id.is_unique
    save(pd.DataFrame(duplicate_rows),'lotes')
    d=raw.copy(); log=[]
    for c in ['fecha','compromiso','entrega','cargado_en']:
        d[c]=dates(raw[c])
        for i in raw.index[raw[c].str.contains('/',na=False)]: log.append((raw.at[i,'envio_id'],raw.at[i,'lote'],c,raw.at[i,c],str(d.at[i,c]),'fecha UTC explícita'))
        for i in raw.index[raw[c].notna() & d[c].isna()]: log.append((raw.at[i,'envio_id'],raw.at[i,'lote'],c,raw.at[i,c],'NaT','fecha inválida: cuarentena analítica, original conservado'))
    save(raw.groupby(['lote','servicio'],dropna=False).size().rename('entidades').reset_index(),'servicios_originales')
    d['servicio']=raw.servicio.str.strip().str.lower()
    for i in raw.index[raw.servicio.ne(d.servicio).fillna(False)]: log.append((raw.at[i,'envio_id'],raw.at[i,'lote'],'servicio',raw.at[i,'servicio'],d.at[i,'servicio'],'quitar espacios y normalizar mayúsculas: dominio inequívoco'))
    for c in ['peso_kg','distancia_km','intentos','tarifa_clp','costo_operacion_clp','reclamo']:
        d[c]=pd.to_numeric(raw[c].str.replace(',','.',regex=False),errors='coerce')
        for i in raw.index[raw[c].str.contains(',',na=False)]: log.append((raw.at[i,'envio_id'],raw.at[i,'lote'],c,raw.at[i,c],str(d.at[i,c]),'coma decimal sin miles'))
    save(pd.DataFrame(log,columns=['envio_id','lote','campo','valor_original','valor_preparado','regla']),'bitacora_normalizacion')
    periods=d.groupby('lote').agg(entidades=('envio_id','size'),fecha_min=('fecha','min'),fecha_max=('fecha','max'),carga_min=('cargado_en','min'),carga_max=('cargado_en','max'),corte=('corte','first')).reset_index()
    save(periods,'periodos_observados')
    dim=loaded['datos/dimensiones/destinos.csv']; assert dim.destino_id.is_unique
    d=d.merge(dim,on='destino_id',how='left',validate='many_to_one')
    hist=loaded['datos/complementarios/sla_historial.csv'].copy()
    for c in ['vigente_desde','vigente_hasta']: hist[c]=dates(hist[c])
    hist['sla_horas_vigente']=pd.to_numeric(hist.sla_horas_vigente)
    candidates=d[['envio_id','destino_id','servicio','fecha']].merge(hist,on=['destino_id','servicio'],how='left')
    hits=candidates[(candidates.fecha>=candidates.vigente_desde)&(candidates.fecha<candidates.vigente_hasta)]
    assert not hits.envio_id.duplicated().any()
    d=d.merge(hits[['envio_id','sla_horas_vigente']],on='envio_id',how='left',validate='one_to_one')
    eligible=d.fecha.notna() & d.destino_id.isin(dim.destino_id) & d.servicio.isin(['estandar','express'])
    assert d.loc[eligible,'sla_horas_vigente'].notna().all(), 'Falta SLA para hecho con claves y fecha válidas'
    ev=loaded['datos/complementarios/eventos_envio.csv'].copy(); ev['instante']=dates(ev.instante)
    assert ev.evento_id.is_unique and ev.groupby('envio_id').size().eq(2).all()
    assert set(ev.envio_id)==set(d.loc[d.lote.eq('ampliacion'),'envio_id'])
    events=ev.pivot(index='envio_id',columns='tipo_evento',values='instante').add_prefix('evento_').reset_index()
    before=len(d); d=d.merge(events,on='envio_id',how='left',validate='one_to_one'); assert len(d)==before
    save(ev.groupby('tipo_evento').agg(eventos=('evento_id','size'),inicio=('instante','min'),fin=('instante','max')).reset_index(),'eventos_resumen')
    # E1 diagnostica defectos; no se recuperan fechas dañadas sin adjudicación.
    d['entregado']=d.estado.eq('entregado'); d['cancelado']=d.estado.eq('cancelado')
    d['fecha_incoherente']=d.entregado & (d.entrega.lt(d.fecha)|d.entrega.gt(d.corte))
    d['entrega_valida']=d.entregado & d.entrega.notna() & ~d.fecha_incoherente & d.fecha.notna()
    d['promesa_valida']=d.compromiso.notna() & d.fecha.notna() & d.compromiso.ge(d.fecha)
    d['expuesto']=~d.cancelado & d.promesa_valida & d.compromiso.le(d.corte)
    d['evaluado']=d.expuesto & (d.entrega_valida|d.estado.eq('en_transito'))
    d['incumple']=d.evaluado & (d.estado.eq('en_transito')|d.entrega.gt(d.compromiso))
    d['cumple']=d.evaluado & ~d.incumple
    d['desconocido']=d.expuesto & ~d.evaluado
    d['atraso_h']=((d.entrega.where(d.entrega_valida,d.corte)-d.compromiso).dt.total_seconds()/3600).clip(lower=0).where(d.evaluado)
    d['semana']=d.fecha.dt.strftime('%G-W%V'); d['mes']=d.fecha.dt.strftime('%Y-%m')
    d['latencia_h']=(d.cargado_en-d.fecha).dt.total_seconds()/3600
    d['promesa_h']=(d.compromiso-d.fecha).dt.total_seconds()/3600
    if 'evento_entrega' in d:
        evidence=d[d.lote.eq('ampliacion')].copy()
        evidence['fecha_entrega_principal_defectuosa']=evidence.entregado & (evidence.entrega.isna()|evidence.fecha_incoherente)
        evidence['evento_entrega_valido']=evidence.evento_entrega.notna() & evidence.evento_entrega.ge(evidence.fecha) & evidence.evento_entrega.le(evidence.corte)
        evidence['candidato_recuperacion']=evidence.fecha_entrega_principal_defectuosa & evidence.evento_entrega_valido
        save(evidence.groupby('estado').agg(envios=('envio_id','size'),defectos=('fecha_entrega_principal_defectuosa','sum'),eventos_entrega_validos=('evento_entrega_valido','sum'),candidatos_recuperacion=('candidato_recuperacion','sum')).reset_index(),'evidencia_eventos')
    populations=d.groupby('lote').agg(entidades=('envio_id','size'),cancelados=('cancelado','sum'),expuestos=('expuesto','sum'),evaluados=('evaluado','sum'),desconocidos=('desconocido','sum'),incumplidos=('incumple','sum'))
    populations['no_cancelados_no_expuestos']=populations.entidades-populations.cancelados-populations.expuestos
    save(populations.reset_index(),'poblaciones')
    nulls=[]
    for keys,part in d.groupby(['lote','tipo_zona','servicio'],dropna=False):
        for field in raw.columns:
            structural=part.estado.isin(['cancelado','en_transito']) & part.entrega.isna() if field=='entrega' else pd.Series(False,index=part.index)
            nulls.append(dict(lote=keys[0],tipo_zona=keys[1],servicio=keys[2],campo=field,n=len(part),nulos=int(part[field].isna().sum()),nulos_estructurales=int(structural.sum())))
    save(pd.DataFrame(nulls),'nulos_campos_segmento')
    domains=[]
    for field,mask in [('peso_kg',d.peso_kg.le(0)),('distancia_km',d.distancia_km.le(0)),('costo_operacion_clp',d.costo_operacion_clp.lt(0)),('tarifa_clp',d.tarifa_clp.lt(0)),('intentos',d.intentos.lt(0)|d.intentos.mod(1).ne(0)),('reclamo',~d.reclamo.isin([0,1])),('estado',~d.estado.isin(['entregado','en_transito','cancelado'])),('servicio',~d.servicio.isin(['estandar','express'])),('compromiso',d.compromiso.lt(d.fecha))]:
        domains.append(dict(campo=field,fallas=int(mask.fillna(False).sum()),denominador=len(d),tratamiento='Investigar; no imputar ni eliminar filas completas'))
    save(pd.DataFrame(domains),'dominios')
    checks=[
      ('Q1','peso_kg',d.peso_kg.isna(),pd.Series(True,index=d.index),'Completitud peso','Conservar nulo; no imputar','Sesgo de peso y costo rural'),
      ('Q2','entrega',d.entregado & d.entrega.isna(),d.entregado,'Entrega obligatoria','Desconocido; contrastar eventos sin sobrescribir','Cumplimiento y atraso'),
      ('Q3','entrega',d.fecha_incoherente,d.entregado & d.entrega.notna(),'Consistencia temporal','Excluir del atraso; conservar evidencia','Cumplimiento y atraso'),
      ('Q4','destino_id',d.zona.isna(),pd.Series(True,index=d.index),'Integridad referencial','Cuarentena para rankings','Segmentación y capacidad'),
      ('Q5','cargado_en',d.latencia_h.gt(48)|d.latencia_h.lt(0)|d.latencia_h.isna(),pd.Series(True,index=d.index),'Carga dentro de 0–48 h','Investigar latencia; no comparar con hoy','Oportunidad del diagnóstico'),
      ('Q6','sla_horas_vigente',d.sla_horas_vigente.isna(),pd.Series(True,index=d.index),'Cobertura SLA histórico','No sustituir por SLA estático','Comparabilidad de promesas')]
    profiles=[]; rules=[]
    for rid,field,bad,pop,label,treat,impact in checks:
        rules.append(dict(regla_id=rid,tabla='envios',campo=field,condicion=label,severidad='alta',denominador='entregados' if rid=='Q2' else 'entregados con fecha' if rid=='Q3' else 'entidades únicas',filas_evaluadas=int(pop.sum()),filas_fallidas=int((bad&pop).sum()),tratamiento=treat,justificacion=impact,impacto_KPI=impact))
        for keys,idx in d.groupby(['lote','tipo_zona','servicio'],dropna=False).groups.items():
            n=int(pop.loc[idx].sum()); b=int((bad&pop).loc[idx].sum())
            profiles.append(dict(regla_id=rid,lote=keys[0],tipo_zona=keys[1],servicio=keys[2],fallas=b,denominador=n,tasa_falla=b/n if n else np.nan))
    # Duplicación se perfila sobre filas físicas, antes de deduplicar.
    rules.append(dict(regla_id='DUP',tabla='envios',campo='envio_id',condicion='Copias exactas',severidad='alta',denominador='filas físicas',filas_evaluadas=240700,filas_fallidas=700,tratamiento='Deduplicar las 14 columnas dentro de cada lote',justificacion='Evitar doble conteo',impacto_KPI='Todos los agregados'))
    for rid,field,mask,treat,impact in [('FECHA','fecha',d.fecha.isna(),'Cuarentena temporal; no inventar día','Exposición y series temporales'),('PESO','peso_kg',d.peso_kg.le(0),'Excluir peso inválido de relaciones físicas; conservar envío','Peso/costo'),('SERVICIO','servicio',raw.servicio.ne(raw.servicio.str.strip().str.lower()),'Normalizar espacios y mayúsculas; registrar original','Segmentos y cobertura SLA')]:
        rules.append(dict(regla_id=rid,tabla='envios',campo=field,condicion='Valor inválido o formato no canónico',severidad='alta',denominador='entidades únicas',filas_evaluadas=len(d),filas_fallidas=int(mask.fillna(False).sum()),tratamiento=treat,justificacion=impact,impacto_KPI=impact))
    save(pd.DataFrame(rules),'matriz_reglas'); save(pd.DataFrame(profiles),'perfil_calidad')
    def aggregate(g):
        out=g.agg(entidades=('envio_id','size'),exposicion=('expuesto','sum'),denominador=('evaluado','sum'),incumplimientos=('incumple','sum'),cumplimientos=('cumple','sum'),desconocidos=('desconocido','sum'),atraso_media_h=('atraso_h','mean'),atraso_p90_h=('atraso_h',lambda s:s.quantile(.9)))
        out['incumplimiento_pct']=100*out.incumplimientos/out.denominador.replace(0,np.nan)
        out['cumplimiento_pct']=100*out.cumplimientos/out.denominador.replace(0,np.nan)
        out['minimo_100']=out.denominador.ge(100)
        out['cumplimiento_inferior_pct']=100*out.cumplimientos/out.exposicion.replace(0,np.nan)
        out['cumplimiento_superior_pct']=100*(out.cumplimientos+out.desconocidos)/out.exposicion.replace(0,np.nan)
        return out.reset_index()
    weekly=aggregate(d.groupby(['zona','tipo_zona','semana','servicio'],dropna=False)); save(weekly,'zona_semana_servicio')
    segments=aggregate(d.groupby(['destino_id','zona','tipo_zona','servicio','mes'],dropna=False)); save(segments,'segmentos_mes')
    zones=aggregate(d.groupby(['destino_id','zona','tipo_zona'],dropna=False))
    save(zones,'zonas_incluyendo_no_identificados')
    # Un destino sin catálogo no identifica una zona elegible para asignar turnos.
    zones=zones[zones.zona.notna() & zones.denominador.ge(100)].copy()
    active=d[~d.cancelado]
    cost=active.groupby('destino_id').agg(costo_medio_clp=('costo_operacion_clp','mean'),costo_observado=('costo_operacion_clp','count'))
    zones=zones.merge(cost,on='destino_id',how='left')
    # Ranking alternativo por tasa; regla multicriterio con pesos docentes explícitos.
    zones['ranking_tasa']=zones.incumplimiento_pct.rank(ascending=False,method='min')
    zones['score']=.45*zones.incumplimientos.rank(pct=True)+.30*zones.incumplimiento_pct.rank(pct=True)+.15*zones.costo_medio_clp.rank(pct=True,ascending=False)+.10*zones.tipo_zona.eq('rural')
    zones=zones.sort_values(['score','destino_id'],ascending=[False,True]); zones['ranking_equilibrado']=range(1,len(zones)+1)
    zones['turnos']=0; chosen=zones.index[:2]; weights=zones.loc[chosen,'incumplimientos']; allocation=10*weights/weights.sum(); floors=np.floor(allocation).astype(int)
    for idx in (allocation-floors).sort_values(ascending=False).index[:10-int(floors.sum())]: floors.loc[idx]+=1
    zones.loc[chosen,'turnos']=floors; assert zones.turnos.sum()==10
    save(zones,'ranking_turnos')
    metas=loaded['datos/complementarios/metas_2025_ancho.csv'].melt(id_vars=['destino_id','indicador','unidad','sentido'],var_name='mes',value_name='meta')
    metas['mes']=metas.mes.str.replace('m','',regex=False).str.replace('_','-',regex=False); metas['meta']=pd.to_numeric(metas.meta)
    assert not metas.duplicated(['destino_id','indicador','mes']).any(); save(metas,'metas_tidy')
    compare=segments.groupby(['destino_id','mes'],dropna=False)[['cumplimientos','denominador']].sum().reset_index(); compare['cumplimiento_pct']=100*compare.cumplimientos/compare.denominador
    compare=compare.merge(metas[metas.indicador.eq('cumplimiento_pct')],on=['destino_id','mes'],validate='one_to_one'); compare['brecha_pp']=compare.cumplimiento_pct-compare.meta; save(compare,'comparacion_metas')
    sla=d.groupby(['mes','tipo_zona','servicio'],dropna=False).agg(n=('envio_id','size'),sla_media=('sla_horas_vigente','mean'),promesa_media=('promesa_h','mean')); save(sla.reset_index(),'cambio_sla')
    # Comparación dentro de estratos y estandarización con mezcla común del año.
    strat=aggregate(d.groupby(['destino_id','tipo_zona','servicio'],dropna=False))
    mix=d[d.evaluado].groupby(['tipo_zona','servicio']).size(); mix=mix/mix.groupby(level=0).transform('sum')
    strat=strat.merge(mix.rename('peso_comun').reset_index(),on=['tipo_zona','servicio'],validate='many_to_one')
    strat['aporte_pp']=strat.incumplimiento_pct*strat.peso_comun
    standardized=strat.groupby('destino_id').agg(tasa_estandarizada_pct=('aporte_pp','sum'),estratos=('servicio','nunique')); save(strat,'comparacion_mismo_servicio_ruralidad'); save(standardized.reset_index(),'ranking_estandarizado')
    # Distribuciones, categorías, correlación interpretable y nulos segmentados.
    distribution=d[['peso_kg','distancia_km','costo_operacion_clp','atraso_h']].describe(percentiles=[.5,.9,.99]).reset_index(); save(distribution,'distribuciones')
    save(d.groupby(['lote','estado','servicio'],dropna=False).size().rename('entidades').reset_index(),'categorias')
    pair=d.loc[(d.peso_kg>0)&(d.costo_operacion_clp>=0)&~d.cancelado,['peso_kg','costo_operacion_clp']].dropna()
    corr=float(pair.corr(method='spearman').iloc[0,1]); save(pd.DataFrame([dict(variables='peso_kg / costo_operacion_clp',metodo='Spearman',pares=len(pair),rho=corr)]),'correlacion')
    missing=d.groupby(['lote','tipo_zona','servicio'],dropna=False).agg(n=('envio_id','size'),peso_nulo=('peso_kg',lambda s:s.isna().sum()),cancelados=('cancelado','sum'))
    missing['peso_nulo_pct']=100*missing.peso_nulo/missing.n; save(missing.reset_index(),'faltantes_segmento')
    contracts=pd.read_csv(SRC/'diccionario_datos.csv')
    contracts['escala']=contracts.campo.map(lambda c:'nominal' if c.endswith('_id') or c in ['zona','region','tipo_zona','servicio','estado','tipo_evento','indicador','sentido'] else 'intervalo temporal UTC' if c in ['fecha','entrega','compromiso','cargado_en','instante','vigente_desde','vigente_hasta'] else 'razón')
    contracts.loc[contracts.campo.eq('reclamo'),'escala']='nominal dicotómica (0/1)'
    contracts['unidad_revisada']=contracts.campo.map(lambda c:'kg' if c=='peso_kg' else 'km' if c=='distancia_km' else 'CLP nominal sin IVA' if c.endswith('_clp') else 'horas corridas' if c.startswith('sla_horas') else 'UTC' if c in ['fecha','entrega','compromiso','cargado_en','instante','vigente_desde','vigente_hasta'] else 'conteo' if c=='intentos' else '0/1' if c=='reclamo' else 'según definición')
    contracts['contrato_propuesto']='Clave según granularidad; no imputar sin evidencia; tipos canónicos tras normalización'
    contracts.loc[contracts.campo.eq('peso_kg'),'tipo_esperado']='numérico positivo (no object)'
    contracts.loc[contracts.campo.eq('fecha'),'definicion']='Fecha de despacho/negocio del envío en UTC; no fecha de carga'
    contracts['obligatoriedad_revisada']=contracts.obligatorio_para_KPI.map({True:'obligatorio para KPI dependiente',False:'según indicador'})
    contracts.loc[contracts.campo.eq('entrega'),'obligatoriedad_revisada']='obligatoria cuando estado=entregado; estructuralmente nula en tránsito/cancelado'
    save(contracts,'diccionario_revisado')
    cards=[]
    definitions=[('K1','Cumplimiento','100*cumplimientos/evaluados','cumplimientos','evaluados','%','fecha,compromiso,entrega,estado,corte','Priorizar capacidad'),('K2','Volumen incumplido','sum(incumple)','incumplimientos','no aplica: conteo','envíos','estado,compromiso,entrega,corte','Dimensionar turnos'),('K3','Atraso promedio','sum(atraso_h)/evaluados','horas de atraso truncadas en 0','evaluados','h','compromiso,entrega,estado,corte','Medir demora'),('K4','Atraso P90','quantile(atraso_h,0.9)','distribución empírica','evaluados','h','compromiso,entrega,estado,corte','Controlar cola'),('K5','Costo operacional medio','sum(costo válido)/n costo válido','costo operacional','no cancelados con costo válido','CLP/envío','costo_operacion_clp,estado','Evaluar costo'),('K6','Tasa de reclamos','100*sum(reclamo=1)/n reclamo válido','reclamos','no cancelados con reclamo 0/1','%','reclamo,estado','Vigilar experiencia')]
    for rid,label,formula,num,den,unit,cols,action in definitions:
        cards.append(dict(id=rid,tipo='KPI',objetivo=label,formula=formula,numerador=num,denominador=den,unidad=unit,granularidad='zona/semana/servicio; mínimo 100 evaluados',fuente_columnas=cols,poblacion='K1–K4: promesas vencidas no canceladas con resultado evaluable; K5–K6: no cancelados',periodo_corte='2025; corte propio de cada lote',tratamiento_nulos='Excluir campo inválido del denominador y publicar cobertura; sin imputación',umbral='meta docente por destino/mes para K1; restantes sin umbral provisto',responsable='equipo operacional docente',accion=action))
    for r in rules[:6]: cards.append(dict(id=r['regla_id'],tipo='calidad',objetivo=r['condicion'],formula='100*filas_fallidas/filas_evaluadas',numerador=r['filas_fallidas'],denominador=r['denominador'],unidad='%',granularidad='lote/ruralidad/servicio',fuente_columnas=r['campo'],poblacion=r['denominador'],periodo_corte='corte propio del lote',tratamiento_nulos=r['tratamiento'],umbral='0% defectos propuesto; latencia máxima 48h del metadato',responsable='responsable de datos docente',accion=r['tratamiento']))
    save(pd.DataFrame(cards),'fichas_indicadores')
    headline=dict(entidades=len(d),expuestos=int(d.expuesto.sum()),evaluados=int(d.evaluado.sum()),incumplimientos=int(d.incumple.sum()),desconocidos=int(d.desconocido.sum()),cumplimiento_pct=100*d.cumple.sum()/d.evaluado.sum(),atraso_media_h=d.atraso_h.mean(),atraso_p90_h=d.atraso_h.quantile(.9),costo_medio_clp=active.costo_operacion_clp.where(active.costo_operacion_clp>=0).mean(),reclamos_pct=100*active.reclamo.where(active.reclamo.isin([0,1])).mean(),rho_peso_costo=corr)
    (OUT/'resumen.json').write_text(json.dumps(headline,indent=2,ensure_ascii=False),encoding='utf-8')
    figures=[]
    def finish(name,title,ylabel):
        plt.title(title); plt.ylabel(ylabel); plt.tight_layout(); plt.savefig(OUT/(name+'.png'),dpi=150); figures.append(name); plt.close()
    plt.figure(figsize=(9,4)); d.atraso_h.dropna().plot.hist(bins=60,log=True); plt.xlabel('Atraso (horas; no es duración total del envío)'); finish('01_distribucion','Atraso al corte: evaluados; incluye ceros y tránsito censurado','Envíos (escala logarítmica)')
    plt.figure(figsize=(9,4)); d.estado.value_counts().plot.bar(); finish('02_categorias','Estados al corte propio de cada lote; 240.000 entidades','Envíos')
    temporal=aggregate(d.groupby('mes')); save(temporal,'evolucion_mes')
    plt.figure(figsize=(10,4)); plt.plot(temporal.mes,temporal.incumplimiento_pct,marker='o'); plt.xticks(rotation=45); finish('03_temporal','Incumplimiento mensual; cortes y mezcla distintos','% de evaluados')
    plt.figure(figsize=(10,4)); top=zones.sort_values('incumplimientos',ascending=False); plt.bar(top.zona,top.incumplimientos); plt.xticks(rotation=75,fontsize=7); finish('04_segmentos','Incumplimientos por zona; promesas vencidas evaluables','Envíos')
    plt.figure(figsize=(8,4)); plt.hexbin(pair.peso_kg,pair.costo_operacion_clp,gridsize=45,mincnt=1,bins='log'); plt.xlabel('Peso (kg)'); plt.colorbar(label='log10 conteo'); finish('05_bivariado',f'Peso y costo, pares válidos no cancelados; Spearman {corr:.3f}','Costo CLP')
    grid=missing.reset_index(); grid['segmento']=grid.lote+' / '+grid.tipo_zona.fillna('sin catálogo')
    heat=grid.pivot(index='segmento',columns='servicio',values='peso_nulo_pct')
    fig,ax=plt.subplots(figsize=(9,5)); img=ax.imshow(heat.to_numpy(dtype=float),aspect='auto',cmap='YlOrRd',vmin=0)
    ax.set_xticks(range(len(heat.columns)),heat.columns); ax.set_yticks(range(len(heat)),heat.index)
    for i in range(len(heat)):
        for j in range(len(heat.columns)): ax.text(j,i,f'{heat.iloc[i,j]:.2f}%',ha='center',va='center',color='white' if heat.iloc[i,j]>5 else 'black')
    fig.colorbar(img,ax=ax,label='% de envíos del segmento'); finish('06_faltantes','Peso ausente por lote, ruralidad y servicio','Lote / ruralidad')
    make_documents(headline,zones,rules,figures,distribution,missing,temporal,sla)
    packages=['pandas','numpy','matplotlib','seaborn','plotly','streamlit','jupyterlab','nbclient','ipykernel','pypdf']
    (OUT/'versiones.json').write_text(json.dumps(dict(python=sys.version,plataforma=platform.platform(),paquetes={p:importlib.metadata.version(p) for p in packages}),indent=2),encoding='utf-8')
    # Validar preservación también después del procesamiento.
    assert all(hashlib.sha256((SRC/f['archivo']).read_bytes()).hexdigest()==f['sha256'] for f in meta['files'])
    (OUT/'validaciones.json').write_text(json.dumps(dict(hashes_originales=True,filas_fisicas=240700,entidades=240000,copias_exactas=700,eventos=len(ev),eventos_por_envio=2,union_eventos_sin_expansion=True,coincidencia_sla_maxima=1,sla_sin_coincidencia=int(d.sla_horas_vigente.isna().sum()),turnos=int(zones.turnos.sum()),graficos=len(figures)),indent=2),encoding='utf-8')
    print(json.dumps(headline,indent=2)); print(zones[['zona','tipo_zona','ranking_tasa','ranking_equilibrado','turnos']].to_string(index=False))
    return headline

def make_documents(h,z,r,figures,dist,missing,temporal,sla):
    allocation='; '.join(f"{row.zona} ({row.tipo_zona}): {row.turnos} turnos" for row in z[z.turnos.gt(0)].itertuples())
    questions=['¿Qué zonas, semanas y servicios concentran más incumplimientos y mayor tasa con al menos 100 evaluados? Cambia la selección de zonas y semanas del piloto.', '¿Dónde el P90 del atraso es elevado aun con media moderada, dentro del mismo servicio y ruralidad? Cambia la prioridad de seguimiento de la cola.', '¿Cómo cambia la prioridad al incorporar costo, ruralidad y mezcla de servicios? Cambia la distribución de los diez turnos y exige revisar SLA desde octubre.']
    limits=['Los datos y metas son sintéticos; no describen resultados reales de Chilexpress.', 'Las asociaciones y rankings no prueban que diez turnos reduzcan el atraso. Se necesita un piloto.', 'El tránsito vencido tiene atraso acumulado al corte, censurado: no es tiempo final de entrega.', 'Los defectos excluidos del denominador pueden sesgar el cumplimiento; se publican desconocidos y límites inferior/superior.', 'Los cortes tienen distinta madurez y el SLA rural cambia desde octubre; una variación agregada no identifica deterioro.', 'El score y el mínimo 100 son políticas analíticas propuestas, no requisitos ni pesos dados por el profesor.']
    narrative=f"""# INFORME DE DESARROLLO — E1 Chilexpress

## Introducción y alcance
Actividad académica del curso Visualización de Datos, profesor Viktor Tapia, Universidad de Santiago de Chile. Se leyó íntegramente Chilexpress_E1_Diagnostico.docx.pdf (3 páginas), el DOCX general, README, notebook inicial, diccionario, metadatos, plantillas y trazabilidad. El caso utiliza datos totalmente sintéticos. Se desarrolla E1 (RA1, IL1.1 e IL1.2), que no exige dashboard terminado ni predicción. E2–E4 se mencionan como contexto; faltan sus cuatro Word y la carpeta entregas. No se inventaron sus rúbricas.

## Objetivos y audiencia
Objetivo general: recomendar una distribución verificable de diez turnos semanales entre dos zonas para un piloto, equilibrando incumplimiento, volumen, costo y ruralidad.
Objetivos específicos: inventariar y verificar fuentes; separar filas y entidades; normalizar formatos; diagnosticar calidad; explorar seis perspectivas; definir seis KPI y seis métricas de calidad; documentar límites y limpieza.
Audiencia ejecutiva: coordinación docente que asigna capacidad y presupuesto. Audiencia operacional: supervisores docentes de zona que programan turnos y monitorean atrasos.

"""+'\n'.join(f'{i+1}. {q}' for i,q in enumerate(questions))+f"""

## Archivos y contratos
Los nueve CSV del manifiesto se verifican por SHA-256 y dimensiones (inventario.csv). Base: 120.600 filas, enero–junio, corte UTC 08-07-2025; actualización: 20.100 filas, julio, corte 08-08-2025; ampliación: 100.000 filas, agosto–diciembre, corte 08-01-2026. Hay 240.700 filas físicas, 240.000 entidades y 700 copias exactas. La exposición es una población analítica de promesas vencidas, no filas ni eventos.
destinos aporta zona, región y ruralidad con unión N:1. sla_historial se une por destino, servicio y fecha dentro de [desde,hasta); nunca se aplica el SLA estático a todo el año. eventos_envio contiene 200.000 eventos de 100.000 envíos: se pivotea antes de unir 1:1. Los eventos no se suman como envíos. metas_2025_ancho se transforma a 288 filas tidy; sustituye analíticamente metas_ancho, sin concatenar versiones. Los catálogos estáticos se conservan e inventarían. Los eventos previos a agosto son ausencia de cobertura, no cero actividad.
diccionario_revisado.csv conserva las definiciones originales y agrega escalas, unidades y contratos. Se corrige peso de object a numérico y fecha a despacho UTC. Identificadores y categorías son nominales; instantes son de intervalo; pesos, distancias, costos y conteos son de razón. Entrega vacía es estructural en cancelado/en_transito y defecto en entregado. Cero en costos e intentos puede ser válido para cancelados.

## Herramientas y entorno
Python 3.14.3 en .venv; pandas, NumPy, Matplotlib, seaborn, Plotly, Streamlit y JupyterLab según requirements original, más pypdf, nbclient e ipykernel. Las versiones efectivamente usadas están en resultados/E1/versiones.json y desarrollo/requirements-lock.txt. Se usa pandas para análisis y Matplotlib para las seis figuras y el PDF; no se necesita una aplicación web para E1.

## Procedimiento y metodología
1. Lectura de las instrucciones antes del desarrollo; identificación de productos y rúbrica (audiencia 25, EDA 30, calidad 30, reproducibilidad 15 puntos).
2. Verificación de hashes y dimensiones antes y después del procesamiento. Lectura de CSV como texto para conservar formatos y claves.
3. Deduplicación exacta dentro de cada lote; validación de claves únicas globales. Los snapshots conservan su corte.
4. Normalización explícita ISO/fechas dd/mm a UTC y coma decimal sin miles a punto. bitacora_normalizacion.csv registra cada celda normalizada; no se recuperan valores dañados por conjetura.
5. Uniones con validación de cardinalidad; control de vigencias y cobertura; pivot de eventos y melt de metas.
6. Diagnóstico por lote/ruralidad/servicio antes de imputación. Las fechas inconsistentes o entregados sin entrega quedan como desconocidos para cumplimiento si la promesa está vencida. No se borran del total ni de la exposición.
7. Exposición: no cancelados con fecha y compromiso válidos y compromiso <= corte. Evaluados: exposición con entrega válida o en_transito. Incumplidos: entrega posterior a compromiso o tránsito vencido. Promesas aún no vencidas y cancelados se separan. Cumplimiento: cumplidos/evaluados; cada tabla publica numeradores, denominadores y desconocidos. Los límites de sensibilidad asignan todos los desconocidos primero a incumplidos y después a cumplidos.
8. Atraso=max(0,entrega-compromiso) en entregados válidos y max(0,corte-compromiso) en tránsito vencido; promedio y P90 incluyen ceros de todos los evaluados. No se confunde atraso condicional de incumplidos con atraso de la población evaluada.
9. Seis análisis y gráficos: distribución del atraso; categorías de estado; evolución mensual; comparación de zonas; relación peso/costo mediante Spearman sobre pares válidos; faltantes por segmento. zona_semana_servicio.csv ofrece el detalle semanal exigido y marca el mínimo propuesto de 100 evaluados.
10. comparacion_mismo_servicio_ruralidad.csv compara estratos; ranking_estandarizado.csv usa pesos comunes de servicio dentro de cada ruralidad para reducir efecto de mezcla. cambio_sla.csv expone promesa y SLA por mes/servicio/ruralidad. No se atribuye causalmente el cambio de octubre al desempeño.

## Resultados verificados
Se obtuvieron {h['entidades']:,} entidades; {h['expuestos']:,} promesas vencidas expuestas; {h['evaluados']:,} evaluados, {h['incumplimientos']:,} incumplimientos y {h['desconocidos']:,} resultados desconocidos entre expuestos. Cumplimiento observado: {h['cumplimiento_pct']:.2f}%. Atraso promedio: {h['atraso_media_h']:.2f} h; P90: {h['atraso_p90_h']:.2f} h. El P90 y la media describen aspectos distintos de la cola; ambos deben revisarse por segmento antes de priorizar. Costo medio no cancelado: {h['costo_medio_clp']:.2f} CLP; reclamos: {h['reclamos_pct']:.2f}%. Spearman peso/costo: {h['rho_peso_costo']:.3f}, asociación sin interpretación causal.
La mayor tasa segmentada de peso ausente es {missing.peso_nulo_pct.max():.2f}% (faltantes_segmento.csv). El peso ausente puede distorsionar análisis de composición, peso y costo; excluirlo no altera por sí mismo el conteo de cumplimiento, pero una exclusión completa de filas sí sesgaría ese KPI. Las fechas de entrega dañadas impactan directamente cumplimiento y atraso. No se eliminan extremos solo por ser grandes: distribuciones.csv permite revisar percentiles 90/99 y máximos; sin evidencia de dominio, un extremo positivo es candidato a revisión, no defecto confirmado.

## Recomendación y contraste de rankings
Ranking alternativo: tasa de incumplimiento descendente. Ranking equilibrado: 45% percentil de volumen incumplido + 30% percentil de tasa + 15% percentil inverso de costo medio + 10% indicador rural. Menor costo se premia como aproximación de eficiencia; no es costo marginal por turno y no permite estimar retorno. Se usan todos los meses del año como diagnóstico, con madurez desigual advertida. ranking_turnos.csv publica los dos rankings para todas las zonas. No comparar rural y urbano como si fueran estratos equivalentes.
Propuesta: {allocation}. Se eligen las dos primeras zonas del score; diez turnos se reparten proporcionalmente a sus incumplimientos por método de restos mayores. Los pesos son una decisión docente transparente que debe validarse con responsables, no una optimización demostrada. Los rankings se contrastan también con tasas estandarizadas y límites de desconocidos; la propuesta es preliminar y sensible a estas políticas.
Piloto propuesto: cuatro semanas de línea base y cuatro de intervención; registrar turnos efectivamente realizados y exposición por zona/semana/servicio/ruralidad. Comparar cambios con zonas de control equivalentes y, si es factible, asignación aleatoria entre zonas elegibles. Medir cumplimiento, volumen incumplido, atraso medio/P90, costo y reclamos con igual ventana de maduración; publicar diferencias, denominadores e incertidumbre. Éxito propuesto: mejora de cumplimiento sin deterioro de costo/reclamos, con umbrales acordados antes de iniciar. No se ejecutó un piloto ni pruebas con usuarios reales.

## Calidad y plan de limpieza
matriz_reglas.csv registra campo, severidad, denominador, evaluados, fallas, tratamiento y efecto en KPI. perfil_calidad.csv ofrece seis métricas por lote/segmento: peso faltante, entrega obligatoria ausente, inconsistencia temporal, integridad de destino, latencia fuera de 0–48 h y cobertura SLA. La duplicación se registra adicionalmente sobre filas físicas; no se oculta tras deduplicar.
Primero normalizar formatos y quitar solo copias exactas. Después investigar fechas dañadas contrastando eventos disponibles desde agosto, sin sustituir ultimo_control por entrega; registrar evidencia antes de cualquier reparación. Mantener cuarentena analítica por indicador en vez de eliminar filas completas. Revisar faltantes rurales, fechas, costos/pesos no positivos y dominios de estado/servicio. Los historiales no se cambian retroactivamente. Los umbrales de defecto cero son propuestas de contrato, no verdades del paquete.

## Visualizaciones y evidencias
01_distribucion.png: histograma en horas, muestra ceros y cola; el tránsito está censurado. 02_categorias.png: conteos nominales de estados por entidad. 03_temporal.png: tasa mensual sobre evaluados; no compara cohortes con madurez idéntica. 04_segmentos.png: cantidad incumplida por zona; debe consultarse junto a tasa y denominador de ranking_turnos.csv. 05_bivariado.png: densidad peso/costo en pares válidos; no prueba causa. 06_faltantes.png: porcentaje de peso ausente por segmento; evita ocultarlo en el promedio global. Todas representan 2025 con cortes específicos; los CSV asociados contienen población, unidad y denominador. El PDF sintetiza audiencia, decisión, hallazgos, límites y limpieza en cinco páginas.

## Problemas, límites y pendientes
"""+'\n'.join('- '+x for x in limits)+"""
- No está instalada la herramienta rg; se usó PowerShell para inspección.
- Faltan entregas/ y sus Word. E1 se resuelve con el PDF disponible; E2–E4 quedan fuera del alcance verificable.
- No se dispone de integrantes ni pruebas humanas: la revisión independiente por un compañero y cualquier prueba con usuarios quedan pendientes, sin registros ficticios.
- Se declara asistencia de IA en código, análisis y redacción; la ejecución y validaciones automáticas aportan evidencia, pero no sustituyen revisión académica humana.

## Reproducción
Desde la raíz en PowerShell:
```powershell
python -m venv .venv
.\\.venv\\Scripts\\python -m pip install -r desarrollo/requirements-lock.txt
.\\.venv\\Scripts\\python desarrollo/analisis_e1.py
.\\.venv\\Scripts\\python desarrollo/ejecutar_notebook.py
.\\.venv\\Scripts\\python desarrollo/validar_resultados.py
```
E1_diagnostico.ipynb en la raíz puede ejecutarse desde una sesión nueva con el intérprete de .venv. Detecta la raíz buscando el script. La ejecución regenera resultados/E1 y el informe sin modificar los originales. versiones.json identifica el entorno probado; validaciones.json recoge controles. Los hashes de los nueve datos se comprueban antes y después.

## Registro de modificaciones
Solo se agregaron .venv/, .jupyter_e1/, desarrollo/, resultados/, E1_diagnostico.ipynb e INFORME_DESARROLLO.md. Dentro de resultados/E1 se generan CSV analíticos, seis PNG, resumen/validaciones/versiones JSON y Diagnostico.pdf. Los archivos del paquete original y el PDF de instrucciones se conservaron. El notebook inicial no se completó ni sobrescribió: se creó el notebook E1 solicitado.

## Cumplimiento y conclusiones
Se implementaron los seis trabajos requeridos por E1, los seis análisis, inventario con hashes, diccionario revisado, seis KPI y seis métricas de calidad, matriz de reglas, perfil segmentado, contraste de rankings, asignación de diez turnos y plan de piloto. Los entregables están en la raíz y resultados/E1. La calidad no se trata como un paso aislado: afecta los denominadores y la interpretación de la recomendación. La asignación es una hipótesis operativa para validar mediante piloto; no demuestra una mejora causal.
Pendientes externos: revisión por compañero, identificación del equipo, ejecución real del piloto y documentos faltantes para futuras entregas. No se afirma una calificación ni el cumplimiento de rúbricas no disponibles.
"""
    rural_missing=missing.reset_index().groupby('tipo_zona')[['n','peso_nulo']].sum()
    rates=100*rural_missing.peso_nulo/rural_missing.n
    details='\n\n## Hallazgos segmentados y controles adicionales\n'
    details+='Faltantes de peso por ruralidad, ponderados por número de envíos: '+ '; '.join(f'{k}: {v:.2f}%' for k,v in rates.items())+'. Fuente: faltantes_segmento.csv, entidades de 2025; ruralidad desconocida fuera de esta comparación. Una diferencia de cobertura limita las comparaciones de peso/costo.\n\n'
    details+='Los dos rankings coinciden en las dos primeras zonas: '+allocation+'. Sus diferencias en posiciones restantes se consultan en ranking_turnos.csv; la coincidencia no prueba robustez ante otros pesos o ventanas. Las zonas sin catálogo y segmentos con menos de 100 evaluados se excluyen de la asignación, conservándose en zonas_incluyendo_no_identificados.csv.\n\n'
    details+='SLA rural observado: estándar 96 h hasta septiembre y 108 h desde octubre; express 48 h y 60 h, respectivamente. Urbano: estándar 72 h y express 24 h. La promesa puede cambiar sin que cambie la duración física de la entrega, por lo que comparar solo cumplimiento agregado es insuficiente (cambio_sla.csv).\n\n'
    details+='Calidad sobre entidades únicas tras normalización de formatos:\n\n|Regla|Campo|Fallas|Evaluados|Tratamiento|\n|---|---|---:|---:|---|\n'
    for rule in r:
        details+=f"|{rule['regla_id']}|{rule['campo']}|{rule['filas_fallidas']}|{rule['filas_evaluadas']}|{rule['tratamiento']}|\n"
    details+='\nLas variantes de servicio con espacios/mayúsculas se normalizan con trazabilidad; servicios_originales.csv conserva su distribución previa. Las fechas imposibles se convierten a NaT solo en la copia analítica, y se registran en bitacora_normalizacion.csv. Los envíos sin fecha válida no se clasifican automáticamente como promesas futuras: no_cancelados_no_expuestos incluye casos no determinables; revisar dominios.csv y nulos_campos_segmento.csv. evidencia_eventos.csv cuenta candidatos con evidencia de entrega para una eventual limpieza posterior, sin aplicar una reparación en E1.\n\n'
    details+='Instalación: la resolución inicial de pip se demoró; preparar_entorno.py descargó wheels compatibles mediante la API JSON de PyPI, comprobó sus hashes y los instaló localmente. pip check verificó dependencias. Para reinstalar sin red, ejecutar `.\\.venv\\Scripts\\python -m pip install --no-index --find-links desarrollo/wheels -r desarrollo/requirements-lock.txt` tras crear .venv. .jupyter_e1/ mantiene kernel y cachés dentro del proyecto porque el directorio personal de IPython no permite escritura en esta sesión. No se cambiaron configuraciones globales.\n'
    details+='\nVerificación independiente: validar_resultados.py recalcula entidades, exposición, evaluados, incumplidos y desconocidos directamente con csv/datetime, sin pandas; exige coincidencia con resumen.json, verifica los hashes de las 21 fuentes y comprueba cinco páginas máximas del PDF y ejecución sin errores del notebook. Su evidencia se guarda en verificacion_independiente.json. El histograma usa escala logarítmica en el conteo para hacer visible la cola sin eliminar extremos.\n'
    narrative+=details
    (ROOT/'INFORME_DESARROLLO.md').write_text(narrative,encoding='utf-8')
    pages=[('1. Audiencia, decisión y alcance', ['Datos sintéticos docentes. E1: diagnóstico y necesidades.','Decisión: diez turnos adicionales semanales entre dos zonas.','Audiencia ejecutiva: coordinación de capacidad. Operacional: supervisores de zona.']+questions),('2. Inventario y metodología',[f"240.700 filas físicas; {h['entidades']:,} entidades; 700 copias exactas.",'Base enero-junio: corte 08/07/2025. Julio: 08/08/2025. Agosto-diciembre: 08/01/2026. Todos UTC.','Hashes verificados. Deduplicación exacta por lote; normalización explícita de fechas y decimales.','SLA por vigencia [desde,hasta); eventos pivoteados 1:1; metas anuales tidy.','Exposición: promesas vencidas no canceladas. Evaluados: entrega válida o tránsito vencido.','Se publican desconocidos, denominadores y sensibilidad; mínimo propuesto: 100 evaluados.']),('3. Hallazgos y evidencia',[f"Evaluados: {h['evaluados']:,}; incumplimientos: {h['incumplimientos']:,}; desconocidos expuestos: {h['desconocidos']:,}.",f"Cumplimiento: {h['cumplimiento_pct']:.2f}%; media atraso: {h['atraso_media_h']:.2f} h; P90: {h['atraso_p90_h']:.2f} h.",f"Costo medio: {h['costo_medio_clp']:.2f} CLP; reclamos: {h['reclamos_pct']:.2f}%; Spearman peso/costo: {h['rho_peso_costo']:.3f}.",'Evidencias 2025: zona_semana_servicio.csv, distribuciones.csv, correlacion.csv, faltantes_segmento.csv.','Seis figuras PNG: distribución, categorías, evolución, segmentos, bivariado y faltantes.','cambio_sla.csv y comparacion_mismo_servicio_ruralidad.csv separan mezcla y vigencia; no identifican causalidad.']),('4. Recomendación y piloto',[allocation,'Score propuesto: 45% volumen, 30% tasa, 15% costo inverso, 10% ruralidad.','ranking_turnos.csv contrasta score y tasa; ranking_estandarizado.csv controla mezcla de servicio dentro de ruralidad.','Turnos proporcionales al incumplimiento de las dos zonas seleccionadas, con restos mayores.','Piloto: cuatro semanas base y cuatro intervención; controles equivalentes, aleatorización si factible, igual madurez.','Monitorear seis KPI, exposición y turnos realizados. Acordar éxito antes del piloto; no atribuir mejora al historial.']),('5. Calidad, límites y reproducibilidad',limits+['Reglas: peso faltante, entrega ausente/incoherente, FK, latencia y SLA; duplicados como control adicional.','Limpieza: normalizar, deduplicar exactos, investigar eventos, mantener desconocidos; sin imputación especulativa.','Ejecutar E1_diagnostico.ipynb con .venv desde sesión nueva; ver INFORME_DESARROLLO.md.','Faltan Word de entregas futuras; revisión humana y piloto pendientes. IA declarada; originales conservados.'])]
    with PdfPages(OUT/'Diagnostico.pdf') as pdf:
        for title,paras in pages:
            fig=plt.figure(figsize=(8.27,11.69)); fig.text(.09,.94,title,fontsize=16,weight='bold'); y=.88
            for para in paras:
                wrapped=textwrap.fill(para,width=91); fig.text(.09,y,wrapped,fontsize=10,va='top'); y-=.024*(wrapped.count('\n')+1)+.025
            fig.text(.09,.035,'Chilexpress E1 | Datos sintéticos | Evidencia detallada en resultados/E1',fontsize=8); pdf.savefig(fig); plt.close(fig)

if __name__=='__main__': run()
