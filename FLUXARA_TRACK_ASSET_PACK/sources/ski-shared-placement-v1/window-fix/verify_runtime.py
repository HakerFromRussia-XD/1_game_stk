from pathlib import Path
import json,hashlib,subprocess,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;repo=Path('/Users/motoricallc/Downloads/fluxara-drift');a=json.load(open(r/'runtime-materials.json'));app=repo/'build-ios-shared-props-simulator/Debug-iphonesimulator/Fluxara Drift.app';installed=Path(subprocess.check_output(['xcrun','simctl','get_app_container','3B2F19DC-4F76-4F61-9F8D-D5E914A6D123','io.fluxara.drift','app'],text=True).strip());src=repo/'iosApp/FluxaraResources';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rows=[]
for q in a['rows']:
 for root in [src,app/'data',installed/'data']:
  folder=root/'library'/q['library'];assert sha(folder/'materials.xml')==q['afterMaterialsSha256'];assert next(e for e in E.parse(folder/'materials.xml').getroot() if e.get('name')==q['texture']).get('shader')=='unlit'
  for name,h in q['unchangedFiles'].items():assert sha(folder/name)==h,(root,name)
 rows.append({'library':q['library'],'windowShaderUnlitSourceBuiltInstalled':True,'meshTextureColliderEmitterAndNodeByteExact':True})
a['runtimeVerification']=rows;(r/'runtime-materials.json').write_text(json.dumps(a,indent=2));print('SHARED_WINDOWS_RUNTIME_VERIFIED',len(rows))
