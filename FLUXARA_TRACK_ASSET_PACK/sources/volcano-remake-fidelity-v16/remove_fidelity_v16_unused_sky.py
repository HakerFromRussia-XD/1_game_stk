from pathlib import Path
import json,sys,hashlib,shutil,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v16';c=w/'candidate';res=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources');sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
# Resolve the actual transitive XML/model/script closure for this candidate's active libraries.
texts=[];models=[];libs=set();pending=[e.get('name')for e in E.parse(c/'scene.xml').getroot().iter('library')];refs=set()
def folder_refs(folder):
 for p in folder.iterdir():
  if p.is_file()and p.suffix.lower()in ['.xml','.as','.glsl','.vert','.frag']:texts.append(p.read_text(errors='replace'))
  if p.is_file()and p.suffix=='.spm':
   models.append(str(p));refs.update(n for pair in parse(p)['materials']for n in pair if n)
folder_refs(c)
while pending:
 name=pending.pop()
 if name in libs:continue
 libs.add(name);lib=res/'library'/name;assert lib.is_dir(),name;folder_refs(lib);root=E.parse(lib/'node.xml').getroot();pending +=[e.get('name')for e in root.iter('library')]
combined='\n'.join(texts);sky=E.parse(c/'scene.xml').getroot().find('sky-box');active=sky.get('texture').split();assert len(active)==6 and all(n.startswith('dp_sky_')for n in active);assert all(c.joinpath(n).is_file()for n in active)
names=['magma_sky_n.png','magma_sky_s.png','magma_sky_e.png','magma_sky_w.png','magma_sky_t.png','magma_sky_bottom.png'];backup=w/'removed-unused-images';backup.mkdir(exist_ok=True);removed=[]
for name in names:
 assert name not in refs and name not in combined,name
 p=c/name;target=backup/name
 if p.exists():
  if target.exists():assert p.read_bytes()==target.read_bytes()
  else:shutil.copy2(p,target)
  original=r/'fidelity-v15/candidate'/name;assert original.read_bytes()==target.read_bytes();p.unlink()
 assert target.is_file();removed.append({'name':name,'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'preservedOutsideCandidate':str(target),'previousCandidateSource':str(r/'fidelity-v15/candidate'/name)})
proof={'scope':'Only unreferenced legacy magma sky image copies in the staged V16 candidate. Original production/source/library images and all active sky, IBL and effects retained.','activeSkyImages':active,'resolvedActiveLibraries':sorted(libs),'spmModelsRead':models,'xmlAndScriptSourcesRead':len(texts),'allRemovedFilesAbsentFromCompleteActiveModelTextureAndXmlScriptClosure':True,'removed':removed,'savedBytes':sum(q['bytes']for q in removed),'productionFilesNotModified':True,'runtimeValidationAfterRemovalPending':True};(w/'unused-sky-removal.json').write_text(json.dumps(proof,indent=2));p=w/'terrain-changes.json';d=json.loads(p.read_text());d['removedUnusedSkyImages']=proof['removed'];d['unusedSkyBytesSaved']=proof['savedBytes'];d['candidateMapBytes']=sum(p.stat().st_size for p in c.iterdir()if p.is_file());d['candidateIncludingNewSharedBytes']=d['candidateMapBytes']+d['newSharedLibraryBytesIncludingRetainedHistoricalVariants']+d['newGlobalTextureBytes'];d['savingBytesVsV1']=d['v1Bytes']-d['candidateIncludingNewSharedBytes'];p.write_text(json.dumps(d,indent=2));print('V16_UNUSED_LEGACY_SKY_COPIES_REMOVED',proof['savedBytes'],d['candidateIncludingNewSharedBytes'],flush=True)
