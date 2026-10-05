from pathlib import Path
import json,sys,hashlib
r=Path(__file__).resolve().parent;w=r/'fidelity-v10b';c=w/'candidate';base=r/'fidelity-v9/candidate';norms=r/'fidelity-v10/candidate';sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
changes=json.loads((r/'fidelity-v10/cliff-changes.json').read_text());weights=[]
for row in changes:
 name=row['model'];a=parse(base/name);b=parse(c/name);n=parse(norms/name);assert a['bounds']==b['bounds'] and a['materials']==b['materials'] and a['flags']==b['flags'];assert b['geometry_end']==len(b['raw']);assert len(a['buffers'])==len(b['buffers']);affected={q['buffer']for q in row['buffers']}
 for i,(old,new)in enumerate(zip(a['buffers'],b['buffers'])):
  assert old['indices']==new['indices'];assert len(old['vertices'])==len(new['vertices'])
  for index,(v,u)in enumerate(zip(old['vertices'],new['vertices'])):
   assert all(v.get(k)==u.get(k)for k in ['position','color','uv','uv2'])
   assert u['normal']==(n['buffers'][i]['vertices'][index]['normal']if i in affected else v['normal'])
 assert(c/name).stat().st_size==(base/name).stat().st_size;weights.append({'model':name,'spmBytes':(c/name).stat().st_size,'modelBytesExactPreviousV9':True,'textureTableAndUvsExactV9':True,'modelPlusTexturesWeightChangePercentAgainstV9':0,'weightWithin20Percent':True})
changed={q['model']for q in changes}
for p in base.iterdir():
 if p.is_file()and p.name not in changed:assert p.read_bytes()==(c/p.name).read_bytes(),p.name
names=['track.xml','quads.xml','graph.xml','scripting.as','easter_eggs.xml']
for name in names:assert(c/name).read_bytes()==(r/'before'/name).read_bytes()
road=lambda d:next(q for q in d['buffers']if d['materials'][q['material']][0]=='track01.png');a=road(parse(r/'before/volcano_track.spm'));b=road(parse(c/'volcano_track.spm'));assert a['indices']==b['indices'];assert all(all(v.get(k)==u.get(k)for k in ['position','normal','uv','color'])for v,u in zip(a['vertices'],b['vertices']))
prod=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources/tracks/fluxara-user-volcano-remake');assert all(p.read_bytes()==(prod/p.name).read_bytes()for p in(r/'fidelity-v2/baseline').iterdir()if p.is_file())
(w/'preservation.json').write_text(json.dumps({'originalRoadPositionsNormalsUvsColoursAndIndicesExact':True,'originalGameplayFilesExact':names,'allScenePlacementsExactV9':True,'allModelVertexPositionsIndicesColoursUvsAndMaterialBindingsExactV9':True,'onlyDecorativeCliffNormalsChanged':True,'collisionGeometryExactV9':True,'stoneTexturePixelsExactV9':True,'perModelWeights':weights,'weightMeasurementScope':'Same SPM byte size, same texture references, all texture file bytes exact V9: model plus texture weight therefore unchanged from V9. This does not assume missing global textures have zero size.','productionIntegrated':False,'productionSourceUnchanged':True},indent=2));print('V10B_STONE_RESTORATION_AND_COURSE_VERIFIED',flush=True)
