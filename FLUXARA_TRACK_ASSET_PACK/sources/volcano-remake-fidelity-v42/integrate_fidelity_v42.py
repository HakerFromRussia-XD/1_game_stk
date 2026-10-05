from pathlib import Path
import ast,hashlib,json,os,shutil,subprocess
r=Path(__file__).resolve().parent;w=r/'fidelity-v42';repo=Path('/Users/motoricallc/Downloads/fluxara-drift');res=repo/'iosApp/FluxaraResources';dest=res/'tracks/fluxara-user-volcano-remake';c=w/'candidate';p=json.loads((w/'preservation-verification.json').read_text());run=json.loads((w/'runtime-validation.json').read_text());a=json.loads((w/'asset-registration.json').read_text());audit=json.loads((w/'pool-audit.json').read_text())
assert run['naturalFinishObserved']and run['temporaryCopiedResourcesCleanupVerified']and p['independentBothMeshesOnlyStoneUVByteChangesVerified']and p['allCandidateAndAcceptedHistoryBytes']<p['v1Bytes']
assert json.loads((w/'final-blend-verification.json').read_text())['canonicalPending']==False
def files(folder):return {str(f.relative_to(folder)):hashlib.sha256(f.read_bytes()).hexdigest()for f in folder.rglob('*')if f.is_file()}
assert files(dest)==files(r/'candidate'),'Production map must still match preserved V1 before replacing it'
device='3B2F19DC-4F76-4F61-9F8D-D5E914A6D123';app=Path(subprocess.check_output(['xcrun','simctl','get_app_container',device,'io.fluxara.drift','app'],text=True).strip());installed=app/'data/tracks'/dest.name
installed_before=files(installed);source_before=files(dest);missing_before=set(source_before)-set(installed_before)
assert all(source_before.get(name)==sha for name,sha in installed_before.items()),'Do not overwrite unrelated installed map changes'
assert missing_before=={'dp_sky_'+side+'.jpg'for side in ['back','bottom','front','left','right','top']},missing_before
required=[];env={'required':required,'work':w,'source':res}
tree=ast.parse((r/'capture_fidelity_v42_drive.py').read_text())
for node in tree.body:
 if isinstance(node,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='required'for t in node.targets):env['required']=ast.literal_eval(node.value)
 if isinstance(node,ast.Expr)and isinstance(node.value,ast.Call)and isinstance(node.value.func,ast.Attribute)and isinstance(node.value.func.value,ast.Name)and node.value.func.value.id=='required':exec(compile(ast.Module(body=[node],type_ignores=[]),'<dependencies>','exec'),env)
copied=[]
for folder,name in dict.fromkeys(env['required']):
 src=res/folder/name;dst=app/'data'/folder/name;assert src.exists(),src
 if dst.exists():
  assert files(dst)==files(src)if src.is_dir()else dst.read_bytes()==src.read_bytes(),dst
 else:
  if src.is_dir():shutil.copytree(src,dst)
  else:shutil.copy2(src,dst)
  copied.append(str(dst))
stage=w/'production-stage';istage=w/'installed-stage';assert not stage.exists()and not istage.exists();shutil.copytree(c,stage);shutil.copytree(c,istage)
for filename in ['track.xml','quads.xml','graph.xml','scripting.as','easter_eggs.xml']:assert(stage/filename).read_bytes()==(r/'candidate'/filename).read_bytes()
backup=w/'production-before-integration';ibackup=w/'installed-before-integration';assert not backup.exists()and not ibackup.exists()
os.rename(dest,backup);os.rename(stage,dest);os.rename(installed,ibackup);os.rename(istage,installed)
assert files(dest)==files(c)==files(installed)
final=r.parent/'fluxara-user-volcano-remake-final/Volcano Remake.blend';old=w/'user-final-before-integration.blend';assert not old.exists();subprocess.run(['/bin/cp','-c',str(final),str(old)],check=True);tmp=final.with_name('Volcano Remake.transfer.blend');subprocess.run(['/bin/cp','-c',a['finalBlend'],str(tmp)],check=True);os.replace(tmp,final)
assert hashlib.sha256(final.read_bytes()).hexdigest()==hashlib.sha256(Path(a['finalBlend']).read_bytes()).hexdigest()
assert len(list(final.parent.glob('*.blend')))==1
proof={'workingSourceIntegrated':True,'installedSimulatorResourceFilesMatchSource':True,'newBuildPerformed':False,'referenceAcceptance':False,'productionMap':str(dest),'installedMap':str(installed),'finalBlend':str(final),'finalBlendSha256':hashlib.sha256(final.read_bytes()).hexdigest(),'previousSourceMapPreserved':str(backup),'previousInstalledMapPreserved':str(ibackup),'previousFinalBlendPreserved':str(old),'newInstalledSharedResourcePaths':copied,'allTrackFilesExactCandidate':len(files(c)),'controlsExactV1':True,'preview':str(dest/'screenshot.jpg'),'previewBytes':(dest/'screenshot.jpg').stat().st_size,'previewSha256':hashlib.sha256((dest/'screenshot.jpg').read_bytes()).hexdigest(),'allCandidateAndAcceptedHistoryBytes':p['allCandidateAndAcceptedHistoryBytes'],'v1Bytes':p['v1Bytes'],'savingVsV1Bytes':p['savingVsV1Bytes'],'goalComplete':False}
(w/'integration-verification.json').write_text(json.dumps(proof,indent=2));print('V42_WORKING_MAP_SOURCE_SIMULATOR_FINAL_BLEND_AND_PREVIEW_INTEGRATED',proof,flush=True)
