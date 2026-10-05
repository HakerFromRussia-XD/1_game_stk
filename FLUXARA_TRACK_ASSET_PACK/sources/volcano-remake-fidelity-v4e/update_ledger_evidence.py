from pathlib import Path
import json,shutil
r=Path(__file__).resolve().parent;pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK');p=r.parent.parent/'fluxara-user-volcano-remake.asset-ledger.json'
a=json.load(open(p));a['preservation']=json.load(open(r/'preservation-audit.json'));a['runtimeValidation']=json.load(open(r/'runtime-validation.json'));a['previewUpdate']=json.load(open(r/'preview-update.json'));a['report']=str(r.parent/'fluxara-user-volcano-remake-final/report/index.html');a['canonicalMaterialVerification']=json.load(open(r/'canonical-bindings-verification.json'));p.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
sources=pack/'sources/volcano-remake-reference-v1'
for q in r.iterdir():
 if q.suffix in ['.py','.js','.svg','.json']:shutil.copy2(q,sources/q.name)
shutil.copy2(p,sources/p.name);shutil.copytree(r/'screenshots',sources/'screenshots',dirs_exist_ok=True)
shutil.copytree(r.parent/'fluxara-user-volcano-remake-final/report',sources/'report',dirs_exist_ok=True)
print('LEDGER_EVIDENCE_UPDATED')
