from pathlib import Path
import sys,shutil,json,hashlib,copy,xml.etree.ElementTree as E
from PIL import Image
r=Path(__file__).resolve().parent;repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK';f=r/'candidate';f.mkdir(exist_ok=True)
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse,rewrite_texture_names
for p in (r/'before').iterdir():
 if p.is_file():shutil.copy2(p,f/p.name)
pool=json.load(open(repo/'FLUXARA_TRACK_ASSET_POOL.json'));index={x['id']:x for k in ['objects','materials','textures'] for x in pool[k]};reuse=[]
def image_variant(asset,target,size=512):
 a=index[asset];src=Path(a.get('packFile',a.get('file'))['path']);assert src.is_file(),src
 im=Image.open(src);dimensions=im.size
 if max(im.size)>size:im.thumbnail((size,size),Image.Resampling.LANCZOS)
 im.save(f/target,optimize=True)
 reuse.append({'role':target,'assetId':asset,'source':str(src),'sourceSha256':hashlib.sha256(src.read_bytes()).hexdigest(),'sourceDimensions':dimensions,'target':target,'dimensions':im.size,'adaptation':'Technical resolution/format variant; image pixels not painted','sha256':hashlib.sha256((f/target).read_bytes()).hexdigest()})
for name in ['Ice_001_COLOR.png','ice.png','fluxara_drift_generic_ice_alpha_custom.png']:image_variant('ski-dash-ice-surface-v27',name)
for name in ['grassded.png','fluxara_drift_generic_snow_a.png']:image_variant('ski-dash-snow-surface-v10',name)
for name in ['rock.jpg','rock_brown.jpg','rock_grey.jpg']:image_variant('ski-dash-cliff-rock-v2',name)
image_variant('ski-dash-snowrock-v3','snowrock.jpg')
for name in ['snowoodbridge.jpg','wooden.png']:image_variant('ski-dash-alpine-timber-winter-v1',name)
water=pack/'textures/lap-catch-reference-v1/fluxara_water_flow.png';assert water.is_file();shutil.copy2(water,f/'Water_001_COLOR.png');reuse.append({'role':'water','source':str(water),'target':'Water_001_COLOR.png','sha256':hashlib.sha256(water.read_bytes()).hexdigest(),'adaptation':'Direct pooled waterfall image; original waterfall/lake mesh and UV retained'})
scene=E.parse(r/'before/scene.xml');sun=scene.getroot().find('sun');sun.set('sun-diffuse','125 127 133');sun.set('ambient','95 107 119');sun.set('fog-color','173 213 243');sun.set('fog-start','280');sun.set('fog-end','1400');sun.set('fog-max','0.18')
sky=scene.getroot().find('sky-box');sky.set('texture',' '.join('dp_sky_'+x+'.jpg' for x in ['top','bottom','left','right','front','back']));sky.set('texture-size','512');sky.attrib.pop('sh-texture',None)
for p in (pack/'textures/dp-motorsports-reference-v2').glob('dp_sky_*.jpg'):shutil.copy2(p,f/p.name);reuse.append({'role':'sky','source':str(p),'target':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'adaptation':'Direct reuse'})
# Render the old branch-card trees invisibly, retaining their exact meshes and LOD placement as colliders.
# The visible winter fir is a separate shared visual model; no original collider or transform is removed.
assert (r/'sr_tree_collision.png').is_file();shutil.copy2(r/'sr_tree_collision.png',f/'sr_tree_collision.png')
for n in ['treeMod1_LOD80.spm','treeMod1_LOD170.spm']:
 d=parse(r/'before'/n);(f/n).write_bytes(rewrite_texture_names(d,[['sr_tree_collision.png',''] for _ in d['materials']]))
mat=E.parse(r/'before/materials.xml');E.SubElement(mat.getroot(),'material',name='sr_tree_collision.png',shader='alphatest')
mat.write(f/'materials.xml',encoding='unicode');scene.write(f/'scene.xml',encoding='unicode')
(r/'reuse.json').write_text(json.dumps(reuse,indent=2));print('STAGED: original course and moving models remain byte-identical')
