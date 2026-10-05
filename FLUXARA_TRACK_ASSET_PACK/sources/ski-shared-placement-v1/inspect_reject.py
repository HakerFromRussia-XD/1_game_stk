import bpy,json,sys,hashlib,struct,collections,math,shutil
from pathlib import Path
from mathutils import Vector,Matrix,kdtree
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
track='fluxara-user-ski-dash';before=r/'before';out=r/'candidate';out.mkdir(parents=True,exist_ok=True)
for p in before.iterdir():
 if p.is_file():shutil.copy2(p,out/p.name)
base=json.load(open(r/'native-inspection.json'))[0];bpy.ops.wm.open_mainfile(filepath=base['path']);bpy.context.view_layer.update();d=parse(before/'ski-dash_winter_scenery.spm');matches={q['name']:q for q in json.load(open(r/'ski-match.json')) if q['complete']};groups=collections.defaultdict(list)
for name,row in matches.items():
 o=bpy.data.objects[name];signature=hashlib.sha256(str(([list(v.co) for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons],[[tuple(q.uv) for q in l.data] for l in o.data.uv_layers],[sorted(hashlib.sha256(bytes(n.image.packed_file.data) if n.image.packed_file else Path(bpy.path.abspath(n.image.filepath)).read_bytes()).hexdigest() for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image) if m and m.use_nodes else None for m in o.data.materials])).encode()).hexdigest();groups[signature].append(row)
C=Matrix(((1,0,0,0),(0,0,1,0),(0,1,0,0),(0,0,0,1)))
def gm(row):return C@Matrix(row['matrix'])@C

def end_vertex(v,b):
 off=v['offset']+12+(4 if d['flags']&1 else 0)
 if d['flags']&2:off+=1+(3 if d['raw'][off]!=128 else 0)
 if d['materials'][b['material']][0]:off+=4+(4 if d['materials'][b['material']][1] else 0)+(4 if d['flags']&4 else 0)
 return off

def unpack(n):
 vals=[]
 for k in range(3):
  v=(n>>(k*10))&1023;vals.append((v-1024 if v>511 else v)/511)
 return Vector(vals)
def packed(v,old):
 v=v.normalized();n=old&0xc0000000
 for k in range(3):n|=(max(-511,min(511,round(v[k]*511)))&1023)<<(k*10)
 return n

def get_vertices(row):
 mat=gm(row);inv=mat.inverted();normal=mat.to_3x3().transposed();rows=[]
 for bi,ti in row['matched']:
  b=d['buffers'][bi]
  for vi in b['indices'][ti:ti+3]:
   v=b['vertices'][vi];rows.append({'bi':bi,'vi':vi,'pos':inv@Vector(v['position']),'localNormal':(normal@unpack(v.get('normal',0))).normalized(),'uv':v.get('uv'),'color':v.get('color'),'material':tuple(d['materials'][b['material']])})
 return rows

def check(first,row):
 other=get_vertices(row);labels=lambda a:(tuple(round(x,4) for x in a['pos']),a['uv'],a['color'],a['material']);first_tri=collections.Counter(tuple(sorted([labels(v) for v in first[j:j+3]],key=str)) for j in range(0,len(first),3));mapped=[];worldError=0;kd=kdtree.KDTree(len(first))
 for i,v in enumerate(first):kd.insert(v['pos'],i)
 kd.balance();err=0;ne=0
 for v in other:
  found=False
  for _,i,dist in kd.find_range(v['pos'],.0005):
   a=first[i]
   if a['uv']==v['uv'] and a['color']==v['color'] and a['material']==v['material'] and (a['localNormal']-v['localNormal']).length<.006:
    mapped.append(a);worldError=max(worldError,(gm(row)@a['pos']-gm(row)@v['pos']).length);err=max(err,dist);ne=max(ne,(a['localNormal']-v['localNormal']).length);found=True;break
  if not found:return {'rejected':'No matching vertex', 'position':list(v['pos'])}
 other_tri=collections.Counter(tuple(sorted([labels(v) for v in mapped[j:j+3]],key=str)) for j in range(0,len(mapped),3))
 if other_tri!=first_tri:return {'rejected':'Triangle topology differs','worldError':worldError}
 if worldError>.001:return {'rejected':'World coordinate error','worldError':worldError}
 return {'localPositionError':err,'worldPositionError':worldError,'localNormalError':ne,'triangleTopologyAndUVColorExact':True}

def write_model(path,buffer_chunks,mat=None,aliases=None,bounds=None):
 material_ids=sorted(set(d['buffers'][i]['material'] for i in buffer_chunks));materials=[[(aliases or {}).get(n,n) for n in d['materials'][i]] for i in material_ids];mm={m:i for i,m in enumerate(material_ids)};body=bytearray();usedpositions=[];count=0
 for bi,tis in sorted(buffer_chunks.items()):
  if not tis:continue
  b=d['buffers'][bi];indices=[v for ti in tis for v in b['indices'][ti:ti+3]];used=sorted(set(indices));vm={v:i for i,v in enumerate(used)};body+=struct.pack('<IIH',len(used),len(indices),mm[b['material']]);inv=mat.inverted() if mat else None
  for i in used:
   v=b['vertices'][i];rec=bytearray(d['raw'][v['offset']:end_vertex(v,b)]);pos=inv@Vector(v['position']) if inv else Vector(v['position']);usedpositions.append(pos)
   if mat:
    struct.pack_into('<3f',rec,0,*pos)
    if d['flags']&1:struct.pack_into('<I',rec,v['normal_offset']-v['offset'],packed(mat.to_3x3().transposed()@unpack(v['normal']),v['normal']))
    if d['flags']&4 and d['materials'][b['material']][0]:
     off=v['tangent_offset'];old=struct.unpack_from('<I',d['raw'],off)[0];struct.pack_into('<I',rec,off-v['offset'],packed(inv.to_3x3()@unpack(old),old))
   body+=rec
  fmt='I' if len(used)>65535 else 'H' if len(used)>255 else 'B';body+=struct.pack('<'+str(len(indices))+fmt,*(vm[v] for v in indices));count+=1
 if bounds is None:bounds=[min(v[k] for v in usedpositions) for k in range(3)]+[max(v[k] for v in usedpositions) for k in range(3)]
 head=b'SP'+bytes([d['version'],d['flags']])+struct.pack('<6fH',*bounds,len(materials))
 for pair in materials:
  for n in pair:
   t=n.encode();head+=struct.pack('B',len(t))+t
 raw=head+struct.pack('<HH',1,count)+body;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw);new=parse(path);assert new['geometry_end']==len(raw);return new


results=[]
for key,rows in groups.items():
 if len(rows)<2:continue
 a,b=rows[:2];first=get_vertices(a);other=get_vertices(b);kd=kdtree.KDTree(len(first))
 for i,v in enumerate(first):kd.insert(v['pos'],i)
 kd.balance();normerror=0;poserror=0;uvdiff=0;cdiff=0;mdiff=0
 for v in other:
  _,idx,dist=kd.find(v['pos']);u=first[idx];poserror=max(poserror,dist);normerror=max(normerror,(u['localNormal']-v['localNormal']).length);uvdiff+=u['uv']!=v['uv'];cdiff+=u['color']!=v['color'];mdiff+=u['material']!=v['material']
 results.append({'first':a['name'],'other':b['name'],'n':len(rows),'positionError':poserror,'normalError':normerror,'uvDifferent':uvdiff,'colorDifferent':cdiff,'materialsDifferent':mdiff,'check':check(first,b)})
(r/'debug-reject.json').write_text(json.dumps(results,indent=2));print('GROUP_DEBUG',results,flush=True)
