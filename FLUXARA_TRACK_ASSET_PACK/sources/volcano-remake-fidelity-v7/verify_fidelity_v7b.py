from pathlib import Path
import sys,json,xml.etree.ElementTree as E,copy
r=Path(__file__).resolve().parent;w=r/'fidelity-v7b';c=w/'candidate';base=r/'fidelity-v5-alpha/candidate';layout=json.loads((w/'layout-changes.json').read_text());rows=json.loads((w/'smoke-changes.json').read_text());models={q['model']for q in rows}
old=E.parse(base/'scene.xml').getroot();new=E.parse(c/'scene.xml').getroot()
removed={E.fromstring(s).get('id'):s for s in layout['consolidatedSpriteInstances']}
for obj in list(old.findall('object')):
    if obj.get('id')in removed:
        assert E.tostring(obj,encoding='unicode')==removed[obj.get('id')];assert obj.get('interaction')=='ghost';old.remove(obj)
for row in layout['modified']:
    a=next(o for o in old.findall('object')if o.get('id')==row['id']);b=next(o for o in new.findall('object')if o.get('id')==row['id']);assert E.tostring(a,encoding='unicode')==row['originalXml'];assert E.tostring(b,encoding='unicode')==row['candidateXml'];assert a.get('interaction')==b.get('interaction')=='ghost';replacement=copy.deepcopy(a);new.remove(b);new.insert(list(old).index(a),replacement)
assert E.tostring(old)==E.tostring(new)
for p in base.iterdir():
    if p.is_file()and p.name not in models|{'scene.xml'}:assert p.read_bytes()==(c/p.name).read_bytes(),p.name
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
for row in rows:
    orig=parse(r/'before'/row['model']);current=parse(c/row['model']);assert max(abs(x-y)for x,y in zip(orig['bounds'],current['bounds']))<.0001;assert .8*row['originalTriangles']<=row['triangles']<=1.2*row['originalTriangles'];assert .8*row['originalBytes']<=row['candidateBytes']<=1.2*row['originalBytes']
    obj=next(o for o in E.parse(c/'scene.xml').getroot().findall('object')if o.get('model')==row['model']);xyz=list(map(float,obj.get('xyz').split()));scale=list(map(float,obj.get('scale').split()));assert obj.get('hpr')=='0.000000000 0.000000000 0.000000000';assert not list(obj)
    bounds=[tuple(current['bounds'][k+side*3]*scale[k]+xyz[k]for k in range(3))for side in range(2)];assert max(abs(x-y)for v,u in zip(bounds,row['worldBoundsTarget'])for x,y in zip(v,u))<.0001
road=lambda d:next(b for b in d['buffers']if d['materials'][b['material']][0]=='track01.png');a=road(parse(r/'before/volcano_track.spm'));b=road(parse(c/'volcano_track.spm'));assert a['indices']==b['indices'];assert len(a['vertices'])==len(b['vertices']);assert all(all(v.get(k)==u.get(k)for k in ['position','normal','uv','color'])for v,u in zip(a['vertices'],b['vertices']))
ceiling=max(v['position'][1]for v in b['vertices'])+3.5;assert all(q['worldBoundsTarget'][0][1]>ceiling for q in rows)
names=['track.xml','quads.xml','graph.xml','scripting.as','easter_eggs.xml']
for name in names:assert(r/'before'/name).read_bytes()==(c/name).read_bytes()
prod=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources/tracks/fluxara-user-volcano-remake');assert all(p.read_bytes()==(prod/p.name).read_bytes()for p in(r/'fidelity-v2/baseline').iterdir()if p.is_file())
(w/'preservation.json').write_text(json.dumps({'originalRoadPositionsNormalsUvsColoursAndIndicesExact':True,'originalGameplayFilesExact':names,'allOtherModelsTexturesAndMaterialsExactV5Alpha':True,'allOtherSceneNodesExactV5Alpha':True,'coreEffectsOriginalLocalBoundsOriginsAxesRetained':True,'coreMeshBytesAndTrianglesWithinTwentyPercent':True,'scope':'Mesh bytes only; existing 64x32 palette textures reused, not original large smoke textures. Decorative transforms and animation explicitly changed.','threeCloudMinimumHeightAboveRoadCeiling':ceiling,'modifiedGhostInstances':len(layout['modified']),'consolidatedSpriteInstances':layout['removedCount'],'productionIntegrated':False,'productionSourceUnchanged':True,'models':rows},indent=2));print('V7B_PRESERVATION_VERIFIED')
