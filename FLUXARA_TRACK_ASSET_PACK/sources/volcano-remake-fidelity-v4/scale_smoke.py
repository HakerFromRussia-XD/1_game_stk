from pathlib import Path
import json,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;f=r/'candidate';before=E.parse(r/'before/scene.xml').getroot();scene=E.parse(f/'scene.xml');models={'AshCloud.spm','AshColumn.spm','PyroclasticFlow.spm','PyroclasticFlowAsh.spm','AshColumnEffect.spm'};rows=[]
for e in scene.getroot().findall('object'):
 if e.get('model') not in models:continue
 old=next(q for q in before.findall('object') if q.get('id')==e.get('id'));assert e.get('interaction')=='ghost';scale=[v*.35 for v in map(float,old.get('scale').split())];e.set('scale',' '.join(f'{v:.8f}' for v in scale));rows.append({'id':e.get('id'),'model':e.get('model'),'oldScale':old.get('scale'),'newScale':e.get('scale'),'ghostDecorationOnly':True,'xyzHprAndAnimationCurvesExact':True,'reason':'Reduce original enormous smoke sheets that filled the road and camera; keep a smaller volcanic plume in the same world position'})
scene.write(f/'scene.xml',encoding='unicode');(r/'smoke-scale-proof.json').write_text(json.dumps(rows,indent=2));print('SMOKE_SCALE_READY',len(rows))
