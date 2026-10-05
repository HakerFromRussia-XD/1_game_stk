from pathlib import Path
import sys,json,xml.etree.ElementTree as E,hashlib
from math import sqrt
r=Path(__file__).resolve().parent;w=r/'fidelity-v5-alpha';c=w/'candidate';base=r/'fidelity-v4e/candidate';sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
rows=json.loads((w/'tint-changes.json').read_text());models={q['model']for q in rows};core={'AshCloud.spm','AshColumn.spm','PyroclasticFlow.spm'}
for row in rows:
 old=parse((r/'before'if row['model']in core else base)/row['model']);new=parse(c/row['model']);assert old['bounds']==new['bounds']
 for a,b in zip(old['buffers'],new['buffers']):
  assert a['indices']==b['indices'];assert len(a['vertices'])==len(b['vertices'])
  for v,u in zip(a['vertices'],b['vertices']):assert all(v.get(k)==u.get(k)for k in['position','normal','uv'])and u['color']==(145,119,159)
old=E.parse(base/'scene.xml');new=E.parse(c/'scene.xml');layout=json.loads((w/'layout-changes.json').read_text())
for row in layout:
 a=next(o for o in old.getroot().findall('object')if o.get('id')==row['id']);b=next(o for o in new.getroot().findall('object')if o.get('id')==row['id']);assert a.get('interaction')==b.get('interaction')=='ghost';assert a.get('hpr')==b.get('hpr')
 av=list(map(float,a.get('xyz').split()));bv=list(map(float,b.get('xyz').split()));assert av[0]==bv[0]and av[2]==bv[2]and abs(bv[1]-av[1]-row['heightOffset'])<1e-7
 assert b.attrib==row['newAttributes'];b.attrib.clear();b.attrib.update(a.attrib)
 for ac,bc in zip(a.findall('curve'),b.findall('curve')):
  assert ac.attrib==bc.attrib
  for ap,bp in zip(ac.findall('p'),bc.findall('p')):
   assert ap.attrib.keys()==bp.attrib.keys()
   for key in ap.attrib:
    af,ay=map(float,ap.get(key).split());bf,by=map(float,bp.get(key).split());assert af==bf
    expected=ay+row['heightOffset']if ac.get('channel')=='LocY'else ay*row['animatedScaleFactor']if ac.get('channel')in['ScaleX','ScaleY','ScaleZ']and row['animatedScaleFactor']is not None else ay
    assert abs(by-expected)<1e-6
   bp.attrib.clear();bp.attrib.update(ap.attrib)
assert E.tostring(old.getroot())==E.tostring(new.getroot())
mt=E.parse(base/'materials.xml');next(m for m in mt.getroot()if m.get('name')=='vr_volcanic_smoke.png').set('shader','alphablend');assert E.tostring(mt.getroot())==E.tostring(E.parse(c/'materials.xml').getroot())
for p in base.iterdir():
 if p.name not in models|{'scene.xml','materials.xml'}:assert p.read_bytes()==(c/p.name).read_bytes(),p.name
before=parse(r/'before/volcano_track.spm');current=parse(c/'volcano_track.spm');road=lambda d:next(b for b in d['buffers']if d['materials'][b['material']][0]=='track01.png');a=road(before);b=road(current);assert a['indices']==b['indices'];assert all(all(v.get(k)==u.get(k)for k in['position','normal','uv','color'])for v,u in zip(a['vertices'],b['vertices']))
for name in ['track.xml','quads.xml','graph.xml','scripting.as','easter_eggs.xml']:assert (r/'before'/name).read_bytes()==(c/name).read_bytes(),name
prod=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources/tracks/fluxara-user-volcano-remake');assert all(p.read_bytes()==(prod/p.name).read_bytes()for p in(r/'fidelity-v2/baseline').iterdir()if p.is_file())
(w/'preservation.json').write_text(json.dumps({'threeCoreEffectsOriginalPositionsNormalsUvsIndicesAndBoundsRestored':True,'fiveOtherEffectsGeometryExactV4E':True,'originalRoadGeometryUvsNormalsColoursAndIndicesExact':True,'originalGameplayFilesExact':['track.xml','quads.xml','graph.xml','scripting.as','easter_eggs.xml'],'allOtherSceneNodesExactV4E':True,'onlySceneChanges':layout,'uniformVertexColourRgb':[145,119,159],'onlyMaterialChange':'Alpha blending, all physical parameters unchanged','allOtherModelsAndTexturesExactV4E':True,'productionSourceUnchanged':True,'productionIntegrated':False,'models':rows},indent=2));print('V5_ALPHA_PRESERVATION_VERIFIED')
