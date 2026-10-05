from pathlib import Path
import shutil,json,hashlib,sys,struct,xml.etree.ElementTree as E
from PIL import Image
r=Path(__file__).resolve().parent;repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK';f=r/'candidate';f.mkdir(exist_ok=True)
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
reuse=[];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for p in (r/'before').iterdir():
    if p.is_file():shutil.copy2(p,f/p.name)
def variant(src,name,limit=512,role='direct',note='Technical resolution variant only'):
    src=Path(src);im=Image.open(src);old=im.size
    if max(im.size)>limit:im.thumbnail((limit,limit),Image.Resampling.LANCZOS)
    if Path(name).suffix.lower() in ['.jpg','.jpeg']:im.convert('RGB').save(f/name,quality=92,optimize=True)
    else:im.save(f/name,optimize=True)
    reuse.append({'source':str(src),'sourceSha256':sha(src),'sourceDimensions':old,'target':name,'dimensions':im.size,'sha256':sha(f/name),'reuseTier':role,'adaptation':note})
# Keep every original material definition and its physical properties.
# Limit supporting maps as well; those bytes count towards the actual track budget.
for p in (r/'before').iterdir():
    if p.suffix.lower() in ['.jpg','.png'] and p.name!='screenshot.jpg':variant(p,p.name,256 if any(s in p.stem.lower() for s in ['gloss','_nm','-nm','norm','_nrm']) else 512)
variant(pack/'textures/lap-catch-reference-v1/lc_stone.png','castelwall.jpg',512,'adapt','Approved pooled cartoon stone blocks under the original castle material name')
variant(pack/'textures/shared/fluxara_lava_meteors_v1/fluxara_meteor_lava.png','blackrock_lava.jpg',512,'adapt','Pooled glowing lava-rock cracks, original material/UV and gravity property retained')
for name in ['Lava_004_COLOR.jpg','lava_2k_diffuse.jpg','lava.png']:
    variant(r/'generated/volcano_lava_flow_v1.png',name,512,'authored','New built-in imagegen lava flow; 3x3 repeat visually inspected')
variant(r/'generated/volcano_road_v1.png','track01.png',512,'authored','Built-in imagegen road material; edge strips preserved, no road geometry changes; 3x3 inspected')
variant(r/'generated/volcano_roof_v2.png','roof_3.jpg',512,'authored','Built-in imagegen roof sheet, used over original whole-face UV; not claimed seamless')
variant(pack/'textures/lap-catch-reference-v1/fluxara_reedboat_wood.png','fluxara_drifttex_generic_WoodA.png',512,'adapt','Pooled stylized warm wood; original bridge mesh and physical material retained')
scene=E.parse(r/'before/scene.xml');sun=scene.getroot().find('sun');sun.set('sun-diffuse','168 150 143');sun.set('ambient','110 109 120');sun.set('fog-color','173 147 169');sun.set('fog-start','350');sun.set('fog-end','1500');sun.set('fog-max','.20')
sky=scene.getroot().find('sky-box');sky.set('texture',' '.join('dp_sky_'+n+'.jpg' for n in ['top','bottom','left','right','front','back']));sky.attrib.pop('sh-texture',None)
for p in (pack/'textures/dp-motorsports-reference-v2').glob('dp_sky_*.jpg'):
    shutil.copy2(p,f/p.name);reuse.append({'source':str(p),'target':p.name,'sourceSha256':sha(p),'sha256':sha(p),'reuseTier':'direct','adaptation':'Approved pooled daytime sky'})
scene.write(f/'scene.xml',encoding='unicode')
# Native editable material palette. UV changes affect scenery only; original mesh
# positions, packed normals, topology, bounds, and model origins stay identical.
assert (r/'Rock13_col.jpg.svg').is_file() and (r/'blackrock.jpg.svg').is_file()
for name in ['Rock13_col.jpg','blackrock.jpg']:shutil.copy2(r/name,f/name)
changes=[]
for name in ['volcano_track.spm','vulcan_01.spm','vulcan_02.spm','vulcan_03.spm']:
    d=parse(r/'before'/name);raw=d['raw'];changed=0
    for b in d['buffers']:
        if d['materials'][b['material']][0]!='Rock13_col.jpg':continue
        for v in b['vertices']:
            packed=v['normal'];ny=(packed>>10)&1023;ny=ny-1024 if ny>511 else ny
            moss=ny/511>.72 and v['position'][1]>-10
            struct.pack_into('<2e',raw,v['uv_offset'],.75 if moss else .25,.5)
            if 'color_offset' in v and raw[v['color_offset']]!=128:struct.pack_into('3B',raw,v['color_offset']+1,255,255,255)
            changed+=1
    (f/name).write_bytes(raw);changes.append({'model':name,'sceneryPaletteVertices':changed,'positionsNormalsIndicesBoundsPreserved':True})
(r/'scenery-palette-proof.json').write_text(json.dumps(changes,indent=2));(r/'reuse.json').write_text(json.dumps(reuse,indent=2));(r/'placements.json').write_text('[]');(r/'new-shared-runtime.json').write_text('{"libraries":[]}')
print('STAGED',sum(p.stat().st_size for p in f.iterdir() if p.is_file()))
