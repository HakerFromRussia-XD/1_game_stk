from pathlib import Path
import json, shutil, xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v6';w.mkdir(exist_ok=True)
shutil.copytree(r/'fidelity-v5-alpha/candidate',w/'candidate',dirs_exist_ok=True)
tree=E.parse(w/'candidate/scene.xml');changes=[]
for obj in tree.getroot().findall('object'):
    model=obj.get('model');ident=obj.get('id');dy=0;factors=None
    if model=='AshCloud.spm':factors=(1,3.3333333333,1)
    elif model=='AshCloud2.spm':dy=110;factors=(2.5,.85,.7)
    elif model=='AshColumnEffect.spm':dy=75;factors=(1,1.7,.6)
    elif model=='PyroclasticFlowAsh.spm':dy=140;factors=(.25,.25,.08)
    elif model=='EruptionAsh.spm':dy=200;factors=(.65,1.4,.3)
    if factors is None:continue
    assert obj.get('interaction')=='ghost'
    original=E.tostring(obj,encoding='unicode');xyz=list(map(float,obj.get('xyz').split()));scale=list(map(float,obj.get('scale').split()))
    xyz[1]+=dy;obj.set('xyz',' '.join(f'{v:.8f}'for v in xyz));obj.set('scale',' '.join(f'{v*f:.8f}'for v,f in zip(scale,factors)))
    for curve in obj.findall('curve'):
        channel=curve.get('channel')
        if channel!='LocY' and channel not in ['ScaleX','ScaleY','ScaleZ']:continue
        for point in curve.findall('p'):
            for key in ['c','h1','h2']:
                if not point.get(key):continue
                frame,value=map(float,point.get(key).split())
                value=value+dy if channel=='LocY' else value*factors[['ScaleX','ScaleY','ScaleZ'].index(channel)]
                point.set(key,f'{frame:.3f} {value:.8f}')
    changes.append({'id':ident,'model':model,'heightOffset':dy,'scaleFactors':factors,'originalXml':original,'candidateXml':E.tostring(obj,encoding='unicode'),'scope':'Decorative ghost placement and height/scale curves only; model geometry, axes, local origins unchanged.'})
tree.write(w/'candidate/scene.xml',encoding='unicode')
(w/'layout-changes.json').write_text(json.dumps(changes,indent=2))
assert len(changes)==9
print('V6_DECORATIVE_LAYOUT_READY',len(changes))
