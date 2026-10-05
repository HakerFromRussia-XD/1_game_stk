from pathlib import Path
import json,shutil,sys,struct,xml.etree.ElementTree as E,hashlib
r=Path(__file__).resolve().parent;f=r/'candidate';f.mkdir(exist_ok=True);repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK';src=r/'before';reuse=[]
for p in src.iterdir():
 if p.is_file():shutil.copy2(p,f/p.name)
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse,rewrite_texture_names
d=parse(src/'lap-catch_track.spm');materials=[a[:] for a in d['materials']]
# Only visual texture/UV assignments change. Protected mesh positions, normals and indices stay exact.
files={
 'stone':pack/'textures/spell-lab-reference-v1/spell_stone.png',
 'ivory':pack/'textures/spell-lab-reference-v1/spell_ivory.png',
 'wood':pack/'textures/shared/fluxara_cocoa_wood_bridge_v1/fluxara_cocoa_bridge_wood.png',
 'grass':pack/'textures/shared/fluxara_grassy_island_v1/fluxara_island_grass.png',
 'rock':pack/'textures/167beb1a6a205cbd/alpine_stone_warm_v1.png',
 'road':pack/'textures/dp-motorsports-reference-v2/AC_auto1.jpg',
 'water':next(pack.glob('textures/**/fluxara_water_flow.png')),
 'palette':pack/'textures/dp-motorsports-reference-v2/dp_palette.png',
 'curb':pack/'textures/dp-motorsports-reference-v2/dp_barrier.jpg'
}
for k,p in files.items():
 assert p.exists(),p
 n={'stone':'lc_stone.png','ivory':'lc_ivory.png','wood':'lc_wood.png','grass':'lc_grass.png','rock':'lc_rock.png','road':'lc_road.jpg','water':'lc_water.png','palette':'dp_palette.png','curb':'lc_curb.jpg'}[k]
 shutil.copy2(p,f/n);reuse.append({'role':k,'source':str(p),'target':n,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
roles={38:'ivory',39:'ivory',40:'ivory',0:'stone',1:'stone',2:'road',3:'road',4:'ivory',6:'rock',7:'ivory',8:'stone',9:'grass',10:'stone',12:'wood',14:'road',15:'stone',17:'road',18:'grass',19:'grass',20:'grass',22:'road',25:'wood',26:'stone',27:'palette',28:'water',29:'ivory',32:'road',34:'rock',35:'rock',37:'rock',41:'grass',43:'rock',44:'rock',45:'grass',46:'grass',47:'grass',48:'stone',51:'curb',52:'road',53:'road',54:'road',56:'road',50:'ivory',66:'water',74:'water',57:'palette',58:'palette',59:'palette',60:'stone',61:'rock',62:'road',63:'wood',64:'wood',65:'rock',67:'road',68:'road',69:'stone',70:'road',71:'road',73:'water'}
lookup={q['role']:q['target'] for q in reuse};remap=[]
for i,b in enumerate(d['buffers']):
 old=d['materials'][b['material']][0]
 if i not in roles:continue
 role=roles[i];new=lookup[role];materials[b['material']]=[new,''];remap.append({'buffer':i,'old':old,'new':new})
 for v in b['vertices']:
  x,y,z=v['position']
  if role=='palette':uv=((3+.5)/4,(0+.5)/4) if i==57 else ((0+.5)/4,(0+.5)/4)
  elif role=='curb':uv=((x+z)/5,y/3) # Preserve original pattern mapping along every curved edge.
  elif role=='road':uv=(x/6,z/6)
  elif role=='grass':uv=(x/12,z/12)
  elif role=='water':uv=(x/40,z/40)
  else:uv=v['uv'] # Original wall unwrap is preserved; geometric outline and direction unchanged.
  struct.pack_into('<2e',d['raw'],v['uv_offset'],*uv)
(f/'lap-catch_track.spm').write_bytes(rewrite_texture_names(d,materials))
# Copy physics exactly onto remapped visual names. Multiple originals can have distinct gravity/speed behavior, so use per-original material filenames below.
physics=E.parse(src/'materials.xml').getroot();newphys=E.Element('materials');physics_by={e.get('name'):e for e in E.parse(repo/'build-ios-shared-props-simulator/Debug-iphonesimulator/Fluxara Drift.app/data/textures/materials.xml').getroot()};physics_by.update({e.get('name'):e for e in physics})
import copy
# Each original needs a unique name when physics differ; shared underlying pixels are kept byte-identical.
unique={}; texture_groups={}
for row in remap:
 original=row['old'].replace('stk','fluxara_drift');e=physics_by.get(original,physics_by.get(row['old']))
 if e is not None:
  e=copy.deepcopy(e)
  for attr in ['normal-map','gloss-map']:e.attrib.pop(attr,None)
  key=(hashlib.sha256((f/row['new']).read_bytes()).hexdigest(),json.dumps({k:v for k,v in e.attrib.items() if k!='name'},sort_keys=True),str([E.tostring(q) for q in e]))
  if key not in texture_groups:
   safe='lc_surface_'+str(row['buffer'])+Path(row['new']).suffix;texture_groups[key]=safe;shutil.copy2(f/row['new'],f/safe);e.set('name',safe);newphys.append(e)
  row['new']=texture_groups[key];unique[row['buffer']]=row['new']
# Rewrite names again without changing vertices.
c=parse(f/'lap-catch_track.spm');n=[a[:] for a in c['materials']]
for i,name in unique.items():n[c['buffers'][i]['material']]=[name,'']
(f/'lap-catch_track.spm').write_bytes(rewrite_texture_names(c,n))
for e in physics:
 if e.get('name') not in [q['old'].replace('stk','fluxara_drift') for q in remap]:newphys.append(copy.deepcopy(e))
# New decorative shared library materials handle their own dependencies.
E.ElementTree(newphys).write(f/'materials.xml',encoding='unicode')
scene=E.parse(src/'scene.xml');sun=scene.getroot().find('sun');sun.set('fog-color','173 211 234');sun.set('fog-start','150');sun.set('fog-end','1200');sun.set('fog-max','0.18');sun.set('sun-diffuse','155 154 145');sun.set('ambient','110 118 114')
sky=scene.getroot().find('sky-box');sky.set('texture',' '.join('dp_sky_'+x+'.jpg' for x in ['top','bottom','left','right','front','back']));sky.set('texture-size','512');sky.attrib.pop('sh-texture',None)
for p in (r.parent/'dp-motorsports-rework/candidate').glob('dp_sky_*.jpg'):shutil.copy2(p,f/p.name)
scene.write(f/'scene.xml',encoding='unicode');(r/'reuse.json').write_text(json.dumps(reuse,indent=2));(r/'material-remap.json').write_text(json.dumps(remap,indent=2));print('STAGED',len(remap),len(reuse))
