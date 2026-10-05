from pathlib import Path
import datetime,hashlib,json,shutil,subprocess
r=Path(__file__).resolve().parent;root=r.parents[2];repo=Path('/Users/motoricallc/Downloads/fluxara-drift');source=repo/'iosApp/FluxaraResources/tracks/fluxara-summit-run';final=root/'output/fluxara-summit-run-final';pack=repo/'FLUXARA_TRACK_ASSET_PACK';app=Path(subprocess.check_output(['xcrun','simctl','get_app_container','3B2F19DC-4F76-4F61-9F8D-D5E914A6D123','io.fluxara.drift','app'],text=True).strip());texture=pack/'textures/summit-run-reference-v1/wooden.png';before=r/'before';before.mkdir(exist_ok=True)
for name,p in [('wooden-runtime-512.png',source/'wooden.png'),('wooden-pack-512.png',texture),('Summit Run.blend',final/'Summit Run.blend'),('ledger.json',root/'fluxara-summit-run.asset-ledger.json'),('report.html',final/'report/index.html')]:
 if not(before/name).exists():shutil.copy2(p,before/name)
oldBytes=(source/'wooden.png').stat().st_size
for target in [source/'wooden.png',final/'wooden.png',texture,app/'data/tracks/fluxara-summit-run/wooden.png']:
 target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(r/'wooden.png',target)
oldId='summit-v1-texture-70a6d3949123';info=lambda p:{'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()};new=info(texture);pp=repo/'FLUXARA_TRACK_ASSET_POOL.json';pool=json.loads(pp.read_text());lp=root/'fluxara-summit-run.asset-ledger.json';ledger=json.loads(lp.read_text())
for items in [pool['textures'],pool['assets'],ledger['assets']]:
 for q in items:
  if q['id']!=oldId:continue
  if 'file'in q:q['previousFile512']=q['file'];q['file']=new
  q['bytes']=new['bytes'];q['sha256']=new['sha256'];q['runtimeExportResolution']=[256,256];q['sourceArtResolutionPreserved']=[512,512];q['previousRuntimeExport512']=str(before/'wooden-pack-512.png');q['adaptation']='Technical sips resize of the same winter timber art from 512x512 to 256x256 to retain the model-plus-used-texture byte budget. Original source art and canonical high-resolution authoring image retained.'
ledger['textureWeightFix']={'textureId':oldId,'oldBytes':oldBytes,'newBytes':new['bytes'],'savingBytes':oldBytes-new['bytes'],'runtimeTexture':new,'sourceArtUnchanged':True,'nativeGeometryChanged':False,'newRuntimeTestPerformed':False,'newBuildPerformed':False,'timestamp':datetime.datetime.now(datetime.timezone.utc).isoformat()};pool['updated']=ledger['textureWeightFix']['timestamp'];pp.write_text(json.dumps(pool,ensure_ascii=False,indent=2)+'\n');lp.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n');(r/'integration.json').write_text(json.dumps(ledger['textureWeightFix'],indent=2)+'\n');print('SUMMIT_RUNTIME_WOOD_TEXTURE_256_SAVED',oldBytes,new['bytes'],flush=True)
