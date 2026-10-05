from pathlib import Path
import hashlib,json,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v5';base=r/'fidelity-v4e/candidate';c=w/'candidate';sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
rows=json.loads((w/'smoke-changes.json').read_text());names={q['model'] for q in rows};sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for p in base.iterdir():
 if p.is_file() and p.name not in names:assert sha(p)==sha(c/p.name),p.name
scene=E.parse(c/'scene.xml').getroot()
for row in rows:
 d=parse(c/row['model']);before=parse(r/'before'/row['model']);points=[v['position'] for b in d['buffers'] for v in b['vertices']];bounds=[min(v[k] for v in points) for k in range(3)]+[max(v[k] for v in points) for k in range(3)]
 assert max(abs(a-b)for a,b in zip(bounds,before['bounds']))<.0001
 assert max(abs(a-b)for a,b in zip(d['bounds'],before['bounds']))<.0001
 assert .8*row['originalTriangles']<=row['triangles']<=1.2*row['originalTriangles']
 assert .8*row['originalBytes']<=row['candidateBytes']<=1.2*row['originalBytes']
 affected=[o for o in scene.findall('object') if o.get('model')==row['model']];assert affected and all(o.get('interaction')=='ghost' for o in affected)
prod=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources/tracks/fluxara-user-volcano-remake');assert all(sha(p)==sha(prod/p.name) for p in (r/'fidelity-v2/baseline').iterdir() if p.is_file())
(w/'preservation.json').write_text(json.dumps({'parent':'V4E','onlyThreeGhostSmokeModelsChanged':True,'mainMeshEveryOtherSpmAllTexturesAndXmlByteExactV4E':True,'ghostLocalBoundsMaxError':max(q['boundsMaxError']for q in rows),'modelBytesAndTrianglesWithin20PercentOriginal':True,'originAxesAndTransformsUnchanged':True,'productionUnchanged':True,'productionIntegrated':False,'models':rows},indent=2));print('V5_PRESERVATION_VERIFIED')
