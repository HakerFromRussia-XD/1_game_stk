from pathlib import Path
import json
import os
import shutil
import subprocess
import time
import xml.etree.ElementTree as E

r=Path(__file__).resolve().parent
work=r/'fidelity-v19'
assert (work/'preservation-verification.json').is_file(), 'Require current V19 preservation proof before launch'
shots=work/'screenshots'
shots.mkdir(exist_ok=True)
device='3B2F19DC-4F76-4F61-9F8D-D5E914A6D123'
bundle='io.fluxara.drift'
app=Path(subprocess.check_output(['xcrun','simctl','get_app_container',device,bundle,'app'],text=True).strip())
probe=app/'data/tracks/fluxara-volcano-fidelity-v19-drive-probe'
source=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources')
required=[('library','fluxara_driftlib_volcano_fountain_v13'),('library','fluxara_driftlib_volcano_castle_body_v15'),('library','fluxara_driftlib_volcano_castle_roof_v15'),('library','fluxara_driftlib_volcano_castle_battlement_v15'),('library','fluxara_driftlib_volcano_gate_roof_v15'),('textures','fluxara_volcano_lava_shared_v13.jpg'),('textures','fluxara_castle_brick_v15.jpg'),('library','fluxara_driftlib_volcano_grass_stone_cliff_v16'),('textures','fluxara_volcano_stone_shared_v16.jpg'),('library','fluxara_driftlib_volcano_green_mound_v18')]
hill=source/'library/fluxara_driftlib_grassy_hill_v2';installed_hill=app/'data/library'/hill.name
assert all((installed_hill/p.name).read_bytes()==p.read_bytes()for p in hill.iterdir()if p.is_file()),'Existing installed hill library must match source before direct reuse'
assert not probe.exists()
copied=[]
for folder,name in required:
    dst=app/'data'/folder/name
    assert not dst.exists(),dst
    copied.append(dst)
    src=source/folder/name
    if src.is_dir():shutil.copytree(src,dst)
    else:shutil.copy2(src,dst)
shutil.copytree(work/'candidate',probe)
track=E.parse(probe/'track.xml')
track.getroot().set('name','Volcano Remake draft V19')
track.getroot().set('internal','Y')
track.write(probe/'track.xml',encoding='unicode')
for name in ['drive-stdout.log','drive-stderr.log']:
    (work/name).unlink(missing_ok=True)
cmd=['xcrun','simctl','launch','--terminate-running-process',
     '--stdout='+str(work/'drive-stdout.log'),'--stderr='+str(work/'drive-stderr.log'),
     device,bundle,'--no-sound','--no-high-scores','--race-now','--test-ai=-1',
     '--track='+probe.name,'--mode=1','--laps=1','--numkarts=1','--kart=fluxara-ace','--seed=4']
rows=[]
try:
    result=subprocess.check_output(cmd,text=True)
    pid=int(result.strip().split(':')[-1])
    start=time.monotonic()
    print(result,flush=True)
    for second in [40,80,140,190]:
        time.sleep(max(0,second-(time.monotonic()-start)))
        os.kill(pid,0)
        shot=shots/f'drive-{second}s.png'
        subprocess.run(['xcrun','simctl','io',device,'screenshot',str(shot)],capture_output=True,check=True)
        rows.append({'seconds':second,'screenshot':str(shot)})
        print('DRAFT_CAPTURED',second,shot,flush=True)
except KeyboardInterrupt:
    print('RECORDING_STOPPED_BY_OPERATOR_AFTER_SAVED_EVIDENCE',flush=True)
finally:
    subprocess.run(['xcrun','simctl','terminate',device,bundle],capture_output=True)
    shutil.rmtree(probe)
    for p in copied:
        if p.is_dir():shutil.rmtree(p)
        else:p.unlink()
    (work/'drive-capture.json').write_text(json.dumps({'command':cmd,'screenshots':rows,
        'kind':'Candidate gameplay in a temporary simulator-only track. Production source and final Blender project not yet replaced.',
        'forceWinsUsed':False},indent=2))
