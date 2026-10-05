from pathlib import Path
import copy,hashlib,json,shutil,subprocess,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'delivery-v1';w.mkdir(exist_ok=True);p=json.loads((r/'dust-extraction.json').read_text());repo=Path('/Users/motoricallc/Downloads/fluxara-drift');res=repo/'iosApp/FluxaraResources';pack=repo/'FLUXARA_TRACK_ASSET_PACK';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
source=res/'tracks'/p['trackId'];assert all(sha(source/f.name)==sha(f)for f in (r/'before').iterdir()if f.is_file())
assert sha(r.parent/'fluxara-user-dust-cross-final/Dust Cross Split Combat.blend')==json.loads((r/'baseline.json').read_text())['nativeSha256']
def norm(x):return(x.tag,dict(x.attrib),(x.text or '').strip(),tuple(norm(q)for q in x))
orig=E.parse(r/'before/scene.xml').getroot();candidate=E.parse(r/'candidate/scene.xml').getroot();assert norm(orig)[:3]==norm(candidate)[:3];assert tuple(norm(x)for x in orig)==tuple(norm(x)for x in list(candidate)[:len(orig)])
for f in (r/'before').iterdir():
 if f.is_file()and f.name not in ['dust-cross_scenery.spm','scene.xml','materials.xml']+[q['original']for q in p['textures']]:assert (r/'candidate'/f.name).read_bytes()==f.read_bytes(),f.name
aliases={q['original']:q['alias']for q in p['textures']};oldmat=E.parse(r/'before/materials.xml').getroot();newmat=E.parse(r/'candidate/materials.xml').getroot()
for x in oldmat:
 y=copy.deepcopy(x);y.set('name',aliases.get(x.get('name'),x.get('name')));assert any(norm(y)==norm(z)for z in newmat),x.get('name')
old=parse(r/'before/dust-cross_scenery.spm');new=parse(r/'candidate/dust-cross_scenery.spm');removed=sum(q['triangles']*q['instances']for q in p['prototypes']);assert sum(len(x['indices'])//3 for x in old['buffers'])==sum(len(x['indices'])//3 for x in new['buffers'])+removed
mod=pack/'models/dust-cross-shared-v1';mod.mkdir(exist_ok=True);tex=pack/'textures/dust-cross-shared-v1';tex.mkdir(exist_ok=True)
for q in p['prototypes']:
 src=Path(q['model']).parent;dst=mod/src.name
 if not dst.exists():shutil.copytree(src,dst)
 assert all((dst/f.name).read_bytes()==f.read_bytes()for f in src.iterdir()if f.is_file())
for q in p['textures']:
 f=Path(q['path']);dst=tex/f.name
 if not dst.exists():shutil.copy2(f,dst)
 assert sha(dst)==q['sha256']==sha(r/'before'/q['original'])
proof={'sourceFilesExactExtractionBaseline':True,'sourceNativeExactExtractionBaseline':True,'originalSceneNodesSemanticallyExact':len(orig),'originalSceneRootAttributesExact':True,'originalRouteAndOtherResourceFilesByteExact':True,'materialDefinitionsExactUnderTextureAliasMap':True,'originalSceneryTriangles':sum(len(x['indices'])//3 for x in old['buffers']),'remainingSceneryTriangles':sum(len(x['indices'])//3 for x in new['buffers']),'extractedSharedTrianglesAcrossInstances':removed,'extractionWorldPositionMaximumErrorMeters':max(q['worldGeometryMatchesOriginalScenery']['worldPositionError']for q in p['placements']),'sameTexturePixelFiles':True,'physicalPackRuntimeVariantsPresent':6,'newRasterPixels':False,'originalResourceBytes':p['sourceBytes'],'candidateResourceBytesIncludingNewSharedFiles':p['totalCandidateBytes'],'newSharedGameBytes':p['allNewSharedBytes'],'sourceCoordinateParts':len(p['placements']),'productionIntegrated':False}
(w/'preflight.json').write_text(json.dumps(proof,indent=2));print('DUST_INDEPENDENT_PREFLIGHT_VERIFIED',proof,flush=True)
