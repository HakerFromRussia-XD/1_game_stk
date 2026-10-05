from pathlib import Path
import json,sys,hashlib,collections,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v13';c=w/'candidate';old=r/'fidelity-v12/candidate';proof=json.loads((w/'fountain-changes.json').read_text());sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
alias=proof['textureAlias'];changed=set(proof['textureAliasOnlyModels']);checked=[]
def triangles(b,attrs=False):
 return collections.Counter(tuple(tuple(sorted(b['vertices'][j].items()))if attrs else tuple(b['vertices'][j]['position'])for j in b['indices'][i:i+3])for i in range(0,len(b['indices']),3))
# Preserve triangle orientation and every indexed attribute for retained surfaces.
def attrs(v):return {k:x for k,x in v.items()if not k.endswith('offset')}
def full(b,omit=set()):
 return collections.Counter(tuple(json.dumps(attrs(b['vertices'][j]),sort_keys=True)for j in b['indices'][i:i+3])for i in range(0,len(b['indices']),3)if i//3 not in omit)
for name in changed:
 a=parse(old/name);b=parse(c/name);assert b['materials']==[[alias if n=='lava_2k_diffuse.jpg'else n for n in row]for row in a['materials']],name
 assert a['bounds']==b['bounds'],name
 assert len(a['buffers'])==len(b['buffers']),name
 for i,(x,y)in enumerate(zip(a['buffers'],b['buffers'])):
  assert x['material']==y['material']
  if name=='volcano_track.spm'and i==12:assert full(x,set(proof['originalTriangleIds']))==full(y)
  else:assert [attrs(v)for v in x['vertices']]==[attrs(v)for v in y['vertices']]and x['indices']==y['indices'],(name,i)
 checked.append(name)
a=parse(old/'volcano_track.spm');coll=parse(c/proof['hiddenOriginalCollisionModel']);subset=collections.Counter(tuple(tuple(a['buffers'][12]['vertices'][j]['position'])for j in a['buffers'][12]['indices'][3*t:3*t+3])for t in proof['originalTriangleIds']);assert triangles(coll['buffers'][0])==subset
# Exact original driving surface and control bytes.
original=r/'before';source=parse(original/'volcano_track.spm');road=lambda d:next(b for b in d['buffers']if d['materials'][b['material']][0]=='track01.png');assert full(road(source))==full(road(parse(c/'volcano_track.spm')))
protected=['track.xml','quads.xml','graph.xml','scripting.as','easter_eggs.xml']
for name in protected:assert (c/name).read_bytes()==(original/name).read_bytes(),name
s=E.parse(c/'scene.xml').getroot();new=[e for e in s if e.get('id','').startswith('VRV13_')];assert len(new)==2
for e in new:s.remove(e)
cloud=next(e for e in s.findall('object')if e.get('model')=='AshColumn.spm');cloud.set('xyz',E.fromstring(proof['oldCloudXml']).get('xyz'))
for e in s.iter():
 if e.get('name')==alias:e.set('name','lava_2k_diffuse.jpg')
assert E.tostring(s)==E.tostring(E.parse(old/'scene.xml').getroot())
m=E.parse(c/'materials.xml').getroot()
for e in m.iter():
 if e.get('name')==alias:e.set('name','lava_2k_diffuse.jpg')
assert E.tostring(m)==E.tostring(E.parse(old/'materials.xml').getroot())
for p in old.iterdir():
 if p.name not in changed|{'scene.xml','materials.xml','lava_2k_diffuse.jpg'}and p.is_file():assert (c/p.name).read_bytes()==p.read_bytes(),p.name
assert not (c/'lava_2k_diffuse.jpg').exists();texture=Path(proof['newGlobalTexture']);assert texture.read_bytes()==(old/'lava_2k_diffuse.jpg').read_bytes()
f=parse(proof['newSharedModel']);assert all(abs(v-q)<1e-4 for v,q in zip(f['bounds'],sum(proof['sourceComponentBounds'],[])))
assert proof['newModelWithTextureBytes']<=proof['sourceModelWithTextureBytes']*1.2
lib=Path(proof['newSharedLibrary']);node=E.parse(lib/'node.xml').getroot().find('object');assert node.get('interaction')=='ghost';assert node.get('xyz')==node.get('hpr')=='0 0 0'and node.get('scale')=='1 1 1'
repo=Path('/Users/motoricallc/Downloads/fluxara-drift');prod=repo/'iosApp/FluxaraResources/tracks/fluxara-user-volcano-remake';baseline=r/'fidelity-v2/baseline'
for p in baseline.iterdir():
 if p.is_file():assert (prod/p.name).read_bytes()==p.read_bytes(),p.name
size=lambda p:sum(f.stat().st_size for f in p.rglob('*')if f.is_file());map_bytes=size(c);libs=sum(size(repo/'iosApp/FluxaraResources/library'/n)for n in ['fluxara_driftlib_volcano_castle_tower_v8b','fluxara_driftlib_volcano_castle_tower_v9','fluxara_driftlib_volcano_fountain_v13']);total=map_bytes+libs+texture.stat().st_size;v1=size(baseline);assert total<v1,(total,v1)
result={'indexedSurfaceAttributesExactExceptRemovedColumn':checked,'originalColumnCollisionTrianglesExact':72,'originalRoadIndexedAttributesExact':True,'protectedControlBytesExact':protected,'sceneChangesOnlyNewFountainColliderTextureAliasAndCloudPosition':True,'otherModelsAndImagesExactV12':True,'lavaTextureBytesExactOriginal':True,'fountainOriginAxesBoundsRetained':True,'modelWithTextureUpper20PercentPassed':True,'modelWithTextureChangePercent':proof['modelWithTextureWeightChangePercent'],'candidateMapBytes':map_bytes,'newSharedLibraryBytesIncludingRetainedCastleVariants':libs,'newGlobalTextureBytes':texture.stat().st_size,'candidateIncludingNewSharedBytes':total,'v1Bytes':v1,'savingBytesVsV1':v1-total,'productionStillExactV1':True,'visualReferenceAcceptance':False}
(w/'preservation-verification.json').write_text(json.dumps(result,indent=2));print('V13_PRESERVATION_AND_WEIGHT_VERIFIED',total,v1-total)
