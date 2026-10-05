import bpy,json,sys,hashlib,struct,collections,math,shutil
from pathlib import Path
from mathutils import Vector,Matrix,kdtree
from mathutils.bvhtree import BVHTree
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
  for _,i,dist in sorted(kd.find_range(v['pos'],.0005),key=lambda item:item[2]):
   a=first[i]
   if a['uv']==v['uv'] and a['color']==v['color'] and a['material']==v['material'] and (a['localNormal']-v['localNormal']).length<.006:
    mapped.append(a);worldError=max(worldError,(gm(row)@a['pos']-gm(row)@v['pos']).length);err=max(err,dist);ne=max(ne,(a['localNormal']-v['localNormal']).length);found=True;break
  if not found:return None
 other_tri=collections.Counter(tuple(sorted([labels(v) for v in mapped[j:j+3]],key=str)) for j in range(0,len(mapped),3))
 surface_error=0;topology_exact=other_tri==first_tri
 if not topology_exact:
  # Exporters can choose a different diagonal after a world transform. Accept
  # only triangles that represent the same surfaces, checked both ways.
  for source,target in [(first,other),(other,first)]:
   mesh=BVHTree.FromPolygons([v['pos'] for v in target],[(i,i+1,i+2) for i in range(0,len(target),3)],all_triangles=True)
   for i in range(0,len(source),3):
    vs=[v['pos'] for v in source[i:i+3]]
    for weights in [(1/3,1/3,1/3),(.5,.5,0),(.5,0,.5),(0,.5,.5),(.6,.2,.2),(.2,.6,.2),(.2,.2,.6)]:
     p=sum((v*w for v,w in zip(vs,weights)),Vector());hit,n,fi,dist=mesh.find_nearest(p)
     if hit is None or dist>.0001:return {'reject':'surface', 'distance':dist,'sourceTriangle':i,'sample':list(p)}
     surface_error=max(surface_error,dist)
 if worldError>.001:return None
 return {'localPositionError':err,'worldPositionError':worldError,'localNormalError':ne,'triangleTopologyAndUVColorExact':topology_exact,'uvAndColorPerVertexExact':True,'bidirectionalSurfaceDistance':surface_error,'sameSurfaceWithAlternativeTriangulation':not topology_exact}

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


for key,rows in groups.items():
 if len(rows)>1 and 'Bunting' in rows[0]['name']:
  print('BUNTING_DIAG',[(q['name'],check(get_vertices(rows[0]),q)) for q in rows[1:]],flush=True)
