"""Register the physical candidate separately; preserve the production ledger."""
from pathlib import Path
import json
import shutil
import hashlib

r=Path(__file__).resolve().parent
work=r/'fidelity-v3'
pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK')
sources=pack/'sources/volcano-remake-fidelity-v3'
sources.mkdir(parents=True,exist_ok=True)
(sources/'generated').mkdir(exist_ok=True)
shutil.copy2(work/'volcano-cliff-stone-v2-source.png',sources/'generated/volcano-cliff-stone-v2-source.png')
shutil.copy2(work/'stone-repeat-3x3.png',sources/'stone-repeat-3x3.png')
shutil.copy2(work/'imagegen-prompt.txt',sources/'imagegen-prompt.txt')
reuse=json.loads((r/'reuse.json').read_text())
reuse=[v for v in reuse if v['target'] not in ['Rock13_col.jpg','vr_moss_palette.jpg']]
new=sources/'generated/volcano-cliff-stone-v2-source.png'
reuse.extend([
    {'source':str(pack/'textures/volcano-remake-fidelity-v2/Rock13_col.jpg'),'target':'Rock13_col.jpg','reuseTier':'direct','adaptation':'V2 lavender cliff image and projection retained unchanged in V3.'},
    {'source':str(pack/'textures/volcano-remake-reference-v1/Rock13_col.jpg'),
     'target':'vr_moss_palette.jpg','reuseTier':'direct',
     'adaptation':'Existing native two-cell palette reused for moss; only the green cell is sampled.'}])
sky=sources/'generated/warm-sky-panorama-source.png'
shutil.copy2(work/'warm-sky-panorama-source.png',sky)
reuse=[x for x in reuse if not x['target'].startswith('dp_sky_')]
for name in ['top','bottom','left','right','front','back']:
    reuse.append({'source':str(sky),'target':'dp_sky_'+name+'.jpg','reuseTier':'authored','assetMethod':'built-in imagegen; technical bilinear cube projection','adaptation':'Warm blue/gold/peach cloud sky. One panorama projected into six matched faces; donor sky retained unchanged.'})
(work/'reuse.json').write_text(json.dumps(reuse,indent=2))
code=(r/'register_inventory.py').read_text()
code=code.replace("reg=json.load(open(r/'asset-registration.json'))", "reg=json.load(open(r/'fidelity-v3/asset-registration.json'))")
code=code.replace('volcano-remake-reference-v1','volcano-remake-fidelity-v3')
code=code.replace("'volcano-v1-", "'volcano-fidelity-v3-")
code=code.replace("r/'reuse.json'", "r/'fidelity-v3/reuse.json'")
code=code.replace("(r/'candidate')", "(r/'fidelity-v3/candidate')")
code=code.replace("r/'candidate/materials.xml'", "r/'fidelity-v3/candidate/materials.xml'")
code=code.replace("r/'pool-audit.json'", "r/'fidelity-v3/pool-audit.json'")
code=code.replace("(r.parent.parent/(track+'.asset-ledger.json'))", "(r/'fidelity-v3/candidate-asset-ledger.json')")
code=code.replace("r/'preservation-audit.json'", "r/'fidelity-v3/preservation.json'")
code=code.replace("'Integrated; final visual acceptance pending'", "'Candidate; production integration pending'")
code=code.replace("'Integrated; visual acceptance pending'", "'Candidate; production integration pending'")
code=code.replace("'Integrated'", "'Candidate; production integration pending'")
code=code.replace("'Integrated; final visual acceptance pending'", "'Candidate; production integration pending'")
code=code.replace("r/'pool-before-volcano-remake.json'", "r/'fidelity-v3/pool-before-fidelity-v3.json'")
code=code.replace("svg=sources/(alias+'.svg');variant=", "svg=(sources/(alias+'.svg')) if alias!='Rock13_col.jpg' else sources/'not-used-as-palette';variant=")
code=code.replace("(r/'preview-update.json').exists()", "False")
code=code.replace("'finalRuntimeChecksInProgress'", "'Candidate validation only'")
exec(compile(code,str(r/'register_inventory.py'),'exec'))
# Correct the candidate-specific provenance rather than implying original geometry was kept.
pool_path=pack.parent/'FLUXARA_TRACK_ASSET_POOL.json'
pool=json.loads(pool_path.read_text())
ledger_path=work/'candidate-asset-ledger.json'
ledger=json.loads(ledger_path.read_text())
for collection in [pool['objects'],ledger['objects']]:
    for obj in collection:
        if obj.get('id')=='volcano-fidelity-v3-stone-portal':
            obj['reuseTier']='authored'
            obj['reason']='New stone portal prototype, 300 triangles, original decorative component bounds and inherited origin retained. Candidate only.'
            obj['runtimeGeometry']='Currently embedded in the candidate volcano_track.spm; no additional runtime library or duplicate mesh per placement.'
        elif obj.get('id','').startswith('volcano-fidelity-v3-model-') and obj.get('displayName') in ['volcano_track.spm','vulcan_01.spm','vulcan_02.spm','vulcan_03.spm']:
            obj['physicalSourcePath']=str(sources/'fidelity-v3.py')
            obj['reason']='V3 candidate: all geometry retained from V2. Main model changes only vertex colors of two ignored additive glow effects; volcano models are reused unchanged from V2.'
for collection in [pool['textures'],ledger['textures']]:
    for texture in collection:
        if texture.get('id','').startswith('volcano-fidelity-v3-') and texture.get('displayName')=='screenshot.jpg':
            texture['physicalSourcePath']=str(pack/'textures/volcano-remake-reference-v1/screenshot.jpg')
            texture['reuseTier']='direct'
            texture['reason']='The preceding production preview is retained as a placeholder in the candidate; production campaign preview has not been replaced.'
for p in ['fidelity_v3.py','finalize_fidelity_v3.py','add_fidelity_v3_portal.py','capture_fidelity_v3_probe.py','capture_fidelity_v3_drive.py']:
    shutil.copy2(r/p,sources/p)
shutil.copy2(r/'fidelity_v3.py',sources/'fidelity-v3.py')
for p in work.glob('*.json'):
    if p.name not in ['pool-before-fidelity-v3.json']:
        shutil.copy2(p,sources/p.name)
shutil.copytree(work/'screenshots',sources/'screenshots',dirs_exist_ok=True)
ledger['runtimeValidation']=json.loads((work/'runtime-validation.json').read_text())
ledger['report']='Candidate evidence is appended separately to map 10 report; previous production version retained.'
ledger['approval']='No user visual approval recorded for candidate V3.'
ledger['status']='Candidate; production source, campaign preview and final delivery are unchanged.'
ledger['assets']=ledger['objects']+ledger['materials']+ledger['textures']
ledger_path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
pool_path.write_text(json.dumps(pool,ensure_ascii=False,indent=2)+'\n')
print('FIDELITY_CANDIDATE_POOL_REGISTERED')

shutil.copy2(work/'prepare_sky.js',sources/'prepare_sky.js')
