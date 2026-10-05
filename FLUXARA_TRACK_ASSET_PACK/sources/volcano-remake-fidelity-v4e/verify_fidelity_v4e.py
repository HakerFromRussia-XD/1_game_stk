from pathlib import Path
import hashlib,json,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v4e';c=w/'candidate';base=r/'fidelity-v3/candidate'
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
changes=json.loads((w/'changes.json').read_text());names={q['model']for q in changes['models']}
for q in changes['models']:
 a=parse(r/'before'/q['model']);b=parse(c/q['model']);assert a['bounds']==b['bounds']
 assert sum(len(x['indices'])//3 for x in a['buffers'])==sum(len(x['indices'])//3 for x in b['buffers'])
 pts=[v['position']for x in b['buffers']for v in x['vertices']]
 bounds=tuple([min(p[k]for p in pts)for k in range(3)]+[max(p[k]for p in pts)for k in range(3)])
 assert bounds==a['bounds']
 assert all(v['uv'] in [(0,0),(1,0),(0,1),(1,1)]for x in b['buffers']for v in x['vertices'])
orig=E.parse(base/'scene.xml');new=E.parse(c/'scene.xml');removed=[]
for o in orig.getroot().findall('object'):
 if o.get('model') in names:
  assert o.get('interaction')=='ghost'
  for e in list(o.findall('animated-texture')):
   if e.get('name')=='gfx_snowStormAnimated_a.png':removed.append(o.get('id'));o.remove(e)
assert E.tostring(orig.getroot())==E.tostring(new.getroot())
a=E.parse(base/'materials.xml');mt=next(e for e in a.getroot()if e.get('name')=='gfx_snowStormAnimated_a.png');mt.set('name','vr_volcanic_smoke.png');mt.set('shader','alphatest')
assert E.tostring(a.getroot())==E.tostring(E.parse(c/'materials.xml').getroot())
for p in base.iterdir():
 if p.name not in names|{'scene.xml','materials.xml'}:assert sha(p)==sha(c/p.name)
prod=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources/tracks/fluxara-user-volcano-remake')
assert all(sha(p)==sha(prod/p.name)for p in (r/'fidelity-v2/baseline').iterdir()if p.is_file())
proof={'models':changes['models'],'cardUvCornersVerified':True,'mainRoadMeshAndEveryOtherSpmByteExactV3':True,'allGameplayNodesTransformsCurvesAndLibrariesExactV3':True,'removedTextureAnimationOnGhostIds':removed,'onlyMaterialChange':'New unique smoke filename and lit alpha-cutout shading. No physical parameters changed.','sourceProductionUnchanged':True,'productionIntegrated':False}
(w/'preservation.json').write_text(json.dumps(proof,indent=2));print('V4E_PRESERVATION_VERIFIED',len(names),len(removed))
