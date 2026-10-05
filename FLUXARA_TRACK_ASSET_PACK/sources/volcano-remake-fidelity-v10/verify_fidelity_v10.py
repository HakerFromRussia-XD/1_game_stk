from pathlib import Path
from collections import Counter
import sys,json,hashlib,math,xml.etree.ElementTree as E
from PIL import Image
r=Path(__file__).resolve().parent;w=r/'fidelity-v10';c=w/'candidate';base=r/'fidelity-v9/candidate';sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
changes=json.loads((w/'cliff-changes.json').read_text());weights=[]
def texture_path(folder,name):
 local=folder/name
 if local.is_file():return local
 reg=json.loads((r/'fidelity-v9/asset-registration.json').read_text());entry=reg['textures'].get(name)
 if entry:
  alias=folder/Path(entry['source']).name
  if alias.is_file():
   assert hashlib.sha256(alias.read_bytes()).hexdigest()==entry['sha256'];return alias
 roots=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources')
 found=list(roots.rglob(name))
 if not found:
  built=Path('/Users/motoricallc/Downloads/fluxara-drift/build-ios-shared-props-simulator/Debug-iphonesimulator/Fluxara Drift.app/data');found=list(built.rglob(name))
 assert found,name
 hashes={hashlib.sha256(p.read_bytes()).hexdigest()for p in found};assert len(hashes)==1,(name,len(hashes));return found[0]
def model_weight(folder,name):
 d=parse(folder/name);textures={t for pair in d['materials']for t in pair if t};return (folder/name).stat().st_size+sum(texture_path(folder,t).stat().st_size for t in textures),sorted(textures)
for row in changes:
 name=row['model'];a=parse(base/name);b=parse(c/name);assert a['bounds']==b['bounds'];assert a['flags']==b['flags'];assert b['geometry_end']==len(b['raw']);expected=[['vr_moss_palette.jpg'if n=='Rock13_col.jpg'else n for n in pair]for pair in a['materials']];assert b['materials']==expected;assert len(a['buffers'])==len(b['buffers']);affected={q['buffer']for q in row['buffers']}
 for i,(old,new)in enumerate(zip(a['buffers'],b['buffers'])):
  assert old['indices']==new['indices'] and len(old['vertices'])==len(new['vertices'])
  for v,u in zip(old['vertices'],new['vertices']):
   assert all(v.get(k)==u.get(k)for k in ['position','color','uv2'])
   if i in affected:assert u['uv']==(.25,.5)
   else:assert v.get('normal')==u.get('normal') and v.get('uv')==u.get('uv')
 before,oldtex=model_weight(base,name);after,newtex=model_weight(c,name);assert after<=1.2*before;weights.append({'model':name,'previousCandidateModelWithUsedTexturesBytes':before,'candidateModelWithUsedTexturesBytes':after,'changePercent':100*(after/before-1),'weightWithin20Percent':True,'oldTextures':oldtex,'newTextures':newtex,'retainedVertexPositionsColoursAndIndicesExact':True})
road=lambda d:next(q for q in d['buffers']if d['materials'][q['material']][0]=='track01.png');oldroad=road(parse(r/'before/volcano_track.spm'));newroad=road(parse(c/'volcano_track.spm'));assert oldroad['indices']==newroad['indices'];assert all(all(v.get(k)==u.get(k)for k in ['position','normal','uv','color'])for v,u in zip(oldroad['vertices'],newroad['vertices']))
changed={q['model']for q in changes}
for p in base.iterdir():
 if p.is_file()and p.name not in changed|{'Rock13_col.jpg','materials.xml'}:assert p.read_bytes()==(c/p.name).read_bytes(),p.name
names=['track.xml','quads.xml','graph.xml','scripting.as','easter_eggs.xml']
for name in names:assert(c/name).read_bytes()==(r/'before'/name).read_bytes()
oldm=E.parse(base/'materials.xml').getroot();oldm.remove(next(q for q in oldm if q.get('name')=='Rock13_col.jpg'));assert E.tostring(oldm)==E.tostring(E.parse(c/'materials.xml').getroot());assert not any('Rock13_col.jpg'in pair for p in c.glob('*.spm')for pair in parse(p)['materials']);assert(c/'scene.xml').read_bytes()==(base/'scene.xml').read_bytes();im=Image.open(c/'vr_moss_palette.jpg');stone=im.getpixel((16,16));assert stone==(151,133,145)
prod=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources/tracks/fluxara-user-volcano-remake');assert all(p.read_bytes()==(prod/p.name).read_bytes()for p in(r/'fidelity-v2/baseline').iterdir()if p.is_file())
proof={'originalRoadPositionsNormalsUvsColoursAndIndicesExact':True,'originalGameplayFilesExact':names,'allScenePlacementsExactV9':True,'allModelVertexPositionsAndIndicesExactV9':True,'allNonCliffUvsAndNormalsExactV9':True,'collisionGeometryExactV9':True,'palettePixelsUnchanged':True,'sampledStoneRgb':stone,'perModelWithTexturesWeights':weights,'weightMeasurementScope':'SPM plus each uniquely referenced texture file. Compared to preceding candidate V9; individual shared texture may be charged to each model for this per-model check. Map budget separately counts actual files once.','productionIntegrated':False,'productionSourceUnchanged':True};(w/'preservation.json').write_text(json.dumps(proof,indent=2));print('V10_CLIFF_AND_COURSE_PRESERVATION_VERIFIED',[(q['model'],round(q['changePercent'],2))for q in weights])
