from pathlib import Path
import shutil,json,hashlib,xml.etree.ElementTree as E
from PIL import Image
r=Path(__file__).resolve().parent;f=r/'candidate';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
src=Path('/Users/motoricallc/.codex/generated_images/01a0ed9b-a75e-74c3-a40c-1713421a0a70/exec-f0da3cf4-f1de-48da-b43b-dd529c88b1d4.png');dst=r/'generated/volcano_smoke_v1.png';shutil.copy2(src,dst)
im=Image.open(dst).convert('RGBA');assert im.getchannel('A').getextrema()[0]==0;im.thumbnail((512,512),Image.Resampling.LANCZOS)
reuse=json.load(open(r/'reuse.json'));reuse=[v for v in reuse if v['target'] not in ['smoke_huricane.png','smoke_huricane_transp.png','fluxara_drifttex_generic_lavaA.png']]
for name in ['smoke_huricane.png','smoke_huricane_transp.png']:
 im.save(f/name,optimize=True);reuse.append({'source':str(dst),'sourceSha256':sha(dst),'target':name,'sha256':sha(f/name),'dimensions':im.size,'reuseTier':'authored','adaptation':'Imagegen transparent plume sprite; original smoke meshes/animations preserved'})
im=Image.open(r/'generated/volcano_lava_flow_v1.png');im.thumbnail((512,512),Image.Resampling.LANCZOS);im.save(f/'fluxara_drifttex_generic_lavaA.png',optimize=True);reuse.append({'source':str(r/'generated/volcano_lava_flow_v1.png'),'sourceSha256':sha(r/'generated/volcano_lava_flow_v1.png'),'target':'fluxara_drifttex_generic_lavaA.png','sha256':sha(f/'fluxara_drifttex_generic_lavaA.png'),'reuseTier':'authored','adaptation':'Track-local variant of global lava texture; no global donor mutation'})
mat=E.parse(r/'before/materials.xml');changes=[]
for e in mat.getroot():
 if e.get('name') in ['smoke_huricane.png','smoke_huricane_transp.png']:
  old=dict(e.attrib);e.set('shader','alphablend');e.attrib.pop('normal-map',None);changes.append({'name':e.get('name'),'before':old,'after':dict(e.attrib),'physicalAttributesUnchanged':True})
mat.write(f/'materials.xml',encoding='unicode');(r/'smoke-material-proof.json').write_text(json.dumps(changes,indent=2));(r/'reuse.json').write_text(json.dumps(reuse,indent=2));print('MATERIALS_POLISHED',len(reuse),sum(p.stat().st_size for p in f.iterdir() if p.is_file()))
