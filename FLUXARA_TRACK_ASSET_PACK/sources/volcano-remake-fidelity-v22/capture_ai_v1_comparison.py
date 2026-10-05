from pathlib import Path
import json,shutil,subprocess,time,os,hashlib,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'ai-v1-comparison';w.mkdir(exist_ok=True);shots=w/'screenshots';shots.mkdir(exist_ok=True)
device='3B2F19DC-4F76-4F61-9F8D-D5E914A6D123';bundle='io.fluxara.drift'
app=Path(subprocess.check_output(['xcrun','simctl','get_app_container',device,bundle,'app'],text=True).strip());source=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources');baseline=r/'fidelity-v2/baseline';probe=app/'data/tracks/fluxara-volcano-ai-v1-comparison-probe';assert not probe.exists()
for p in baseline.iterdir():
    if p.is_file():assert p.read_bytes()==(source/'tracks/fluxara-user-volcano-remake'/p.name).read_bytes()
libs=sorted({e.get('name')for e in E.parse(baseline/'scene.xml').getroot().findall('library')})
for name in libs:
    folder=source/'library'/name;installed=app/'data/library'/name
    assert all((installed/p.name).read_bytes()==p.read_bytes()for p in folder.iterdir()if p.is_file()),name
shutil.copytree(baseline,probe);track=E.parse(probe/'track.xml');track.getroot().set('name','Volcano V1 AI comparison');track.getroot().set('internal','Y');track.write(probe/'track.xml',encoding='unicode')
cmd=['xcrun','simctl','launch','--terminate-running-process','--stdout='+str(w/'drive-stdout.log'),'--stderr='+str(w/'drive-stderr.log'),device,bundle,'--no-sound','--no-high-scores','--race-now','--test-ai=-1','--track='+probe.name,'--mode=1','--laps=1','--numkarts=1','--kart=fluxara-ace','--seed=4'];rows=[]
try:
    result=subprocess.check_output(cmd,text=True);pid=int(result.strip().split(':')[-1]);start=time.monotonic();print(result,flush=True)
    for second in [40,80,140,190]:
        time.sleep(max(0,second-(time.monotonic()-start)));os.kill(pid,0);shot=shots/f'v1-{second}s.png';subprocess.run(['xcrun','simctl','io',device,'screenshot',str(shot)],capture_output=True,check=True);rows.append({'seconds':second,'screenshot':str(shot)});print('V1_CAPTURED',second,flush=True)
finally:
    subprocess.run(['xcrun','simctl','terminate',device,bundle],capture_output=True);shutil.rmtree(probe)
    assert not probe.exists()
    for name in libs:
        assert all((app/'data/library'/name/p.name).read_bytes()==p.read_bytes()for p in (source/'library'/name).iterdir()if p.is_file())
    data={'command':cmd,'screenshots':rows,'kind':'Unmodified integrated V1 baseline, same installed simulator app/mode/seed/kart as V21. Only temporary track display/internal attributes changed. No forced win.','forceWinsUsed':False,'baselineSourceMainSPMSha256':hashlib.sha256((baseline/'volcano_track.spm').read_bytes()).hexdigest(),'allBaselineSourceFilesExactProductionBeforeProbe':True,'existingInstalledLibrariesUnchanged':True,'finalProbeCleanupVerified':True}
    (w/'capture.json').write_text(json.dumps(data,indent=2));print('V1_AI_COMPARISON_CAPTURE_CLEANED',flush=True)
