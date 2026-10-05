from pathlib import Path
import sys,shutil,struct,json,hashlib,copy,xml.etree.ElementTree as E
from PIL import Image
r=Path(__file__).resolve().parent;src=r/'before';f=r/'candidate';f.mkdir(exist_ok=True)
repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK'
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
authored={n:(f/n).read_bytes() for n in ['OBJ.png','CR1.png','CR2.png']}
for p in src.iterdir():
 if p.is_file():shutil.copy2(p,f/p.name)
for n,raw in authored.items():(f/n).write_bytes(raw)
reuse=[]
grass=pack/'textures/dp-motorsports-reference-v2/msl2-grass001.jpg'
assert grass.is_file();shutil.copy2(grass,f/'ml_grass.jpg');reuse.append({'role':'ground','source':str(grass),'target':'ml_grass.jpg','sha256':hashlib.sha256(grass.read_bytes()).hexdigest()})
# A technical resolution variant retains the original road atlas, markings and UV layout.
variants=[]
for n in ['ROAD.png','ROADgloss.png','SAND.png','KERB.png']:
 im=Image.open(src/n);size=(max(1,im.width//2),max(1,im.height//2));im.resize(size,Image.Resampling.LANCZOS).save(f/n,optimize=True);variants.append({'file':n,'source':str(src/n),'sourceSha256':hashlib.sha256((src/n).read_bytes()).hexdigest(),'dimensions':size,'change':'Technical downsample only; no painted edits'})
d=parse(src/'motorsport-land_track.spm');removed=[3,9,13];keep=[i for i in range(len(d['buffers'])) if i not in removed];names=[a[:] for a in d['materials']];names[d['buffers'][2]['material']]=['ml_grass.jpg',''];names[d['buffers'][5]['material']]=['OBJ.png',''];names[d['buffers'][12]['material']]=['OBJ.png','']
for bi in [6,7,8]:
 for v in d['buffers'][bi]['vertices']:
  u,w=v['uv']
  if 0<=u<.5 and 0<=w%1<.125:
   x,y,z=v['position'];struct.pack_into('<2e',d['raw'],v['uv_offset'],((x+z)/12)%0.5,w)
for v in d['buffers'][2]['vertices']:
 x,y,z=v['position'];struct.pack_into('<2e',d['raw'],v['uv_offset'],x/9,z/9)
used_names=[];slot={}
for i in keep:
 old=d['buffers'][i]['material'];pair=names[old]
 if pair not in used_names:used_names.append(pair)
 slot[old]=used_names.index(pair)
raw=d['raw'][:28]+struct.pack('<H',len(used_names))
for pair in used_names:
 for n in pair:
  enc=n.encode();raw+=struct.pack('B',len(enc))+enc
raw+=struct.pack('<HH',1,len(keep))
for i in keep:
 b=d['buffers'][i];start=b['vertices'][0]['offset']-10;end=d['buffers'][i+1]['vertices'][0]['offset']-10 if i+1<len(d['buffers']) else d['geometry_end']-24
 buf=bytearray(d['raw'][start:end]);struct.pack_into('<H',buf,8,slot[b['material']]);raw+=buf
raw+=d['raw'][d['geometry_end']-24:];(f/'motorsport-land_track.spm').write_bytes(raw)
mat=E.parse(src/'materials.xml')
for e in list(mat.getroot()):
 if e.get('name') in ['HOR.png','OBJALPHA.png','fluxara_drifttex_directionSign_a.png']:mat.getroot().remove(e)
for q in mat.getroot():
 if q.get('name')=='OBJ.png':q.attrib.pop('gloss-map',None)
m=copy.deepcopy(next(x for x in mat.getroot() if x.get('name')=='GRASS.png'));m.set('name','ml_grass.jpg');mat.getroot().append(m);mat.write(f/'materials.xml',encoding='unicode')
scene=E.parse(src/'scene.xml');sun=scene.getroot().find('sun');sun.set('sun-diffuse','190 181 157');sun.set('ambient','130 140 139');sun.set('fog-color','174 214 239');sun.set('fog-start','220');sun.set('fog-end','1300');sun.set('fog-max','0.12')
sky=scene.getroot().find('sky-box');sky.set('texture',' '.join('dp_sky_'+x+'.jpg' for x in ['top','bottom','left','right','front','back']));sky.set('texture-size','512');sky.attrib.pop('sh-texture',None)
for p in (pack/'textures/dp-motorsports-reference-v2').glob('dp_sky_*.jpg'):shutil.copy2(p,f/p.name);reuse.append({'role':'sky','source':str(p),'target':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
scene.write(f/'scene.xml',encoding='unicode');(r/'reuse.json').write_text(json.dumps(reuse,indent=2));(r/'texture-resolution-variants.json').write_text(json.dumps(variants,indent=2));(r/'material-remap.json').write_text(json.dumps({'retainedOriginalBuffers':keep,'removedDecorativeBuffers':removed,'names':names},indent=2));print('STAGED',len(keep),'protected road buffer 10 retained exactly')
