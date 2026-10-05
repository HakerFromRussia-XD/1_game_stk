from pathlib import Path
import sys,struct,json,math,shutil,xml.etree.ElementTree as E
from PIL import Image
r=Path(__file__).resolve().parent;f=r/'candidate';sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse,rewrite_texture_names
asphalt=Path('/Users/motoricallc/.codex/generated_images/01a0ed9b-a75e-74c3-a40c-1713421a0a70/exec-dc9c0bce-0fbe-4bc8-b7ed-34c9b333bee0.png');shutil.copy2(asphalt,r/'references/asphalt-generated.png')
for name in ['AC_auto1.jpg','Aoitori_road3.jpg','msl2-road1_r.jpg','Tunnel_AC_auto1.jpg']:Image.open(asphalt).convert('RGB').resize((512,512),Image.Resampling.LANCZOS).save(f/name,quality=88,optimize=True)
# Diagnostic repeat is compositing for seam verification only, not a painted texture edit.
im=Image.open(f/'AC_auto1.jpg');repeat=Image.new('RGB',(1536,1536))
for x in range(3):
 for y in range(3):repeat.paste(im,(x*512,y*512))
repeat.save(r/'asphalt-repeat.jpg')
shutil.copy2(f/'curbs_Albedo_B.jpg',f/'dp_barrier.jpg')
d=parse(r/'before/dp-motorsports-land-ii_track.spm');names=[p[:] for p in d['materials']];removed=[3,7,8,9,10,22,38,39,40,43,51,55,56,57,58,59,68]
keep=[1,2,12,14,19,23,24,25,26,27,28,29,30,31,32,36,37,45,46,48,64]
palette=[i for i in range(72) if i not in keep+removed+[41,42]]
def cell(c):return ((c%4+.5)/4,(c//4+.5)/4)
# Texture remaps preserve every original vertex, normal and triangle for all retained meshes.
for i in palette:
 names[i]=['dp_palette.png',''];b=d['buffers'][i];path=r/'before'/d['materials'][i][0];im=Image.open(path).convert('RGB') if path.exists() else None
 for v in b['vertices']:
  x,y,z=v['position'];u,w=v.get('uv',(0,0));rgb=im.getpixel((int((u%1)*im.width)%im.width,int((w%1)*im.height)%im.height)) if im else (180,180,180);br=sum(rgb)/3
  c=0
  if i in [0,5,6,13,15,16,17,35,54,60,70]:c=0 if br>95 else 3
  elif i in [11,49]:c=12 if br<160 else 10
  elif i==18:c=2 if br<135 else 0
  elif i==21:c=3 if br<95 else 2 if br<155 else 0
  elif i==33:c=[2,9,1,0][int(x*1.1+z*1.2)%4]
  elif i in [34,50,65,66,67,69,71]:c=(12 if br<55 else 3 if br<110 else 2 if br<165 else 0)
  elif i in [20,44]:c=10 if br<120 else 11
  elif i==47:c=2 if int(x/1.8)%2 else 13
  elif i==53:c=3
  elif i==61:c=7 if br<155 else 8
  elif i in [62,63]:c=3 if br<85 else 2 if br<125 else 0
  struct.pack_into('<2e',d['raw'],v['uv_offset'],*cell(c))
# Existing overhead gantry uses a compact vector banner, retaining its exact mesh and placement.
names[34]=['dp_gantry.png','']
for v in d['buffers'][34]['vertices']:
 u,w=struct.unpack_from('<2e',d['raw'],v['uv_offset']);x,y,z=v['position']
 if y>21.4 and 0<x<4.1 and 40<z<58:
  u=.5+(z-40.78644)/(57.188965-40.78644)*.5;w=1-(y-21.448805)/(23.065409-21.448805)
 else:u=u*.5
 struct.pack_into('<2e',d['raw'],v['uv_offset'],u,w)
for i in [46,47]:
 names[i]=['dp_awning.png','']
 for v in d['buffers'][i]['vertices']:
  x,y,z=v['position'];struct.pack_into('<2e',d['raw'],v['uv_offset'],(x*.993+z*.119)/3,y/3)
for i in [41,42]:
 names[i]=['dp_barrier.jpg','']
 for v in d['buffers'][i]['vertices']:
  x,y,z=v['position'];struct.pack_into('<2e',d['raw'],v['uv_offset'],(x+z)/5,y/2)
for i in [1,2,12,36]:
 for v in d['buffers'][i]['vertices']:
  x,y,z=v['position'];struct.pack_into('<2e',d['raw'],v['uv_offset'],x/6,z/6)
for i in [19,23,24,25,26,27,28,29,30,31,32]:
 for v in d['buffers'][i]['vertices']:
  x,y,z=v['position'];struct.pack_into('<2e',d['raw'],v['uv_offset'],x/9,z/9)
# Remove decorative buffers and their material slots cleanly; retained buffer geometry bytes are exact.
retained=[i for i in range(72) if i not in removed]
raw=d['raw'][:28]+struct.pack('<H',len(retained))
for i in retained:
 for name in names[i]:
  enc=name.encode();raw+=struct.pack('B',len(enc))+enc
raw+=struct.pack('<HH',1,len(retained))
for mi,i in enumerate(retained):
 buf=d['buffers'][i];start=buf['vertices'][0]['offset']-10;end=d['buffers'][i+1]['vertices'][0]['offset']-10 if i+1<len(d['buffers']) else d['geometry_end']
 data=bytearray(d['raw'][start:end]);struct.pack_into('<H',data,8,mi)
 if i in palette and i not in [34,47]:
  # Constant palette coordinate per face prevents interpolation through unrelated atlas cells.
  verts=[];ids=[];lookup={}
  for j in range(0,len(buf['indices']),3):
   corners=[buf['vertices'][k] for k in buf['indices'][j:j+3]]
   uvs=[struct.unpack_from('<2e',d['raw'],v['uv_offset']) for v in corners];uv=max(uvs,key=uvs.count)
   for v in corners:
    key=(*v['position'],v['normal'],*uv)
    if key not in lookup:lookup[key]=len(verts);verts.append(key)
    ids.append(lookup[key])
  assert len(verts)<=65535,(i,len(verts))
  data=bytearray(struct.pack('<IIH',len(verts),len(ids),mi))
  for v in verts:data+=struct.pack('<3fI2e',*v)
  data+=struct.pack('<'+str(len(ids))+('H' if len(verts)>255 else 'B'),*ids)
 raw+=data
(f/'dp-motorsports-land-ii_track.spm').write_bytes(raw)
mat=E.parse(r/'before/materials.xml');E.SubElement(mat.getroot(),'material',{'name':'dp_palette.png'});E.SubElement(mat.getroot(),'material',{'name':'dp_barrier.jpg'});E.SubElement(mat.getroot(),'material',{'name':'dp_flower.png','shader':'alphatest','ignore':'Y'});mat.write(f/'materials.xml',encoding='unicode')
(r/'material-remap.json').write_text(json.dumps({'removedDecorativeBuffers':removed,'paletteBuffers':palette,'materials':names},indent=2));print('MATERIALS_DONE')
