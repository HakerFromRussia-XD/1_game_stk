from pathlib import Path
import json,shutil,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v15';res=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources');p=json.loads((w/'castle-atmosphere-changes.json').read_text())
bodylib=res/'library/fluxara_driftlib_volcano_castle_body_v15';bodylib.mkdir(exist_ok=True)
files={'newTowerBody':bodylib,'newTowerRoof':Path(p['roofedLibrary']),'newTowerFlag':Path(p['battlementLibrary']),'newGateRoofModel':Path(p['newGateRoofLibrary'])}
for key,lib in files.items():
 old=Path(p[key]);dst=lib/old.name
 if old!=dst:
  assert not dst.exists() or dst.read_bytes()==old.read_bytes()
  shutil.move(old,dst)
 p[key]=str(dst)
(bodylib/'node.xml').write_text('<scene><object id="CastleBody" type="animation" model="fluxara_castle_v15_body.spm" xyz="0 0 0" hpr="0 0 0" scale="1 1 1" interaction="ghost" skeletal-animation="false" /></scene>')
(bodylib/'materials.xml').write_text('<materials><material name="fluxara_castle_brick_v15.jpg" /></materials>')
for role,key in [('roof','roofedLibrary'),('battlement','battlementLibrary')]:
 lib=Path(p[key]);root=E.parse(lib/'node.xml');obj=root.getroot().find('object[@id="CastleBody"]');assert obj is not None
 attributes={'id':'CastleBodyLibrary','name':bodylib.name,'xyz':'0 0 0','hpr':'0 0 0','scale':obj.get('scale')};root.getroot().remove(obj);root.getroot().insert(0,E.Element('library',attributes));root.write(lib/'node.xml',encoding='unicode')
p['sharedBodyLibrary']=str(bodylib);p['runtimeResourceLayout']='One physical body model in a nested shared library; one cap in each variant library. No duplicate model files.';(w/'castle-atmosphere-changes.json').write_text(json.dumps(p,indent=2))
for n in ['capture_fidelity_v15_inspection.py','capture_fidelity_v15_drive.py']:
 f=r/n;s=f.read_text();s=s.replace("('library','fluxara_driftlib_volcano_castle_roof_v15')","('library','fluxara_driftlib_volcano_castle_body_v15'),('library','fluxara_driftlib_volcano_castle_roof_v15')")
 for model in ['fluxara_castle_v15_body.spm','fluxara_castle_v15_roof.spm','fluxara_castle_v15_flag.spm','fluxara_volcano_gate_roof_v15.spm']:s=s.replace(",('models','"+model+"')",'')
 f.write_text(s)
archive=w/'iterations/initial-global-model-layout';archive.mkdir(parents=True,exist_ok=True)
for n in ['probe-stdout.log','probe-stderr.log']:
 f=w/n
 if f.exists() and not (archive/n).exists():shutil.copy2(f,archive/n)
print('V15_SHARED_LIBRARY_LAYOUT_FIXED',p['sharedBodyLibrary'])
