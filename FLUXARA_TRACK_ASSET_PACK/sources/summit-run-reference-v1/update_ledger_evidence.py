from pathlib import Path
import json,shutil
r=Path(__file__).resolve().parent;pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK');p=r.parent.parent/'fluxara-summit-run.asset-ledger.json'
a=json.load(open(p));validation={
    'campaignThreeLaps':{'naturalFinishObserved':True,'screenshot':str(r/'screenshots/final-campaign-440s.png'),'evidence':str(r/'final-campaign-capture.json'),'versionBoundary':'Before final snow-cliff palette and decorative cascade changes; protected route and physical materials remain identical'},
    'finalNormalOneLap':{'naturalFinishObserved':True,'screenshot':str(r/'screenshots/final-normal-lap-150s.png'),'evidence':str(r/'final-normal-lap-capture.json')},
    'forceWinsUsed':False,'reverseDirectionVerified':False,'performanceMeasured':False}
(r/'runtime-validation.json').write_text(json.dumps(validation,indent=2))
a['runtimeValidation']=validation;a['previewUpdate']=json.load(open(r/'preview-update.json'));a['report']=str(r.parent/'fluxara-summit-run-final/report/index.html');a['canonicalMaterialVerification']=json.load(open(r/'canonical-bindings-verification.json'))
p.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
sources=pack/'sources/summit-run-reference-v1'
for q in r.iterdir():
    if q.suffix in ['.py','.js','.svg','.json']:shutil.copy2(q,sources/q.name)
shutil.copy2(p,sources/p.name);shutil.copytree(r/'screenshots',sources/'screenshots',dirs_exist_ok=True)
print('LEDGER_EVIDENCE_UPDATED')
