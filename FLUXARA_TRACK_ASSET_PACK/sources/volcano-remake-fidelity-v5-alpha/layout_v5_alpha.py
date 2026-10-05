from pathlib import Path
import shutil,json,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v5-alpha';c=w/'candidate';history=w/'iterations/alpha-before-layout';history.mkdir(parents=True,exist_ok=True)
if not (history/'scene.xml').exists():
 shutil.copy2(c/'scene.xml',history/'scene.xml')
 for name in ['drive-capture.json','preservation.json','budget.json','tint-changes.json','asset-registration.json']:
  if (w/name).exists():shutil.copy2(w/name,history/name)
 shutil.copytree(w/'screenshots',history/'screenshots',dirs_exist_ok=True)
scene=E.parse(history/'scene.xml');rows=[]
settings={'AshCloud.spm':(43.61,[.18,.18,.18],None),'AshColumn.spm':(83.60,[.315,.3465,.3185],None),'PyroclasticFlow.spm':(130,[.12,.12,.12],.12)}
for obj in scene.getroot().findall('object'):
 model=obj.get('model')
 if model not in settings:continue
 assert obj.get('interaction')=='ghost';dy,scales,scale_curve_factor=settings[model];old=dict(obj.attrib);xyz=list(map(float,obj.get('xyz').split()));xyz[1]+=dy;obj.set('xyz',' '.join(f'{v:.8f}'for v in xyz));obj.set('scale',' '.join(f'{v:.8f}'for v in scales))
 for curve in obj.findall('curve'):
  channel=curve.get('channel');is_y=channel=='LocY';is_scale=channel in ['ScaleX','ScaleY','ScaleZ']and scale_curve_factor is not None
  if not is_y and not is_scale:continue
  for point in curve.findall('p'):
   for key in ['c','h1','h2']:
    if key not in point.attrib:continue
    frame,value=map(float,point.get(key).split());value=value+dy if is_y else value*scale_curve_factor;point.set(key,f'{frame:.8f} {value:.8f}')
 rows.append({'id':obj.get('id'),'model':model,'oldAttributes':old,'newAttributes':dict(obj.attrib),'heightOffset':dy,'animatedScaleFactor':scale_curve_factor,'scope':'Decorative ghost effects only; model geometry/origins/axes retained, per-map placements adjusted.'})
assert len(rows)==3;scene.write(c/'scene.xml',encoding='unicode');(w/'layout-changes.json').write_text(json.dumps(rows,indent=2));print('V5_ALPHA_OVERHEAD_LAYOUT_READY',rows)
