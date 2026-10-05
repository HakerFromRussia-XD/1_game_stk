import bpy,json,sys,hashlib,struct,collections,math,shutil
from pathlib import Path
from mathutils import Vector,Matrix,kdtree
from mathutils.bvhtree import BVHTree
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
track='fluxara-user-spell-lab';before=r/'before';out=r/'candidate';out.mkdir(parents=True,exist_ok=True)
for p in before.iterdir():
 if p.is_file():shutil.copy2(p,out/p.name)
base=json.load(open(r/'native-inspection.json'))[0];bpy.ops.wm.open_mainfile(filepath=base['path']);bpy.context.view_layer.update();d=parse(before/'spell_gardens.spm');matches={q['name']:q for q in json.load(open(r/'spell-match.json')) if q['complete']};groups=collections.defaultdict(list)
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
     if hit is None or dist>.0005:return None
     worldSurfaceDistance=(gm(row).to_3x3()@(hit-p)).length
     if worldSurfaceDistance>.001:return None
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

# Pure scenery; route meshes and every original gameplay node remain outside this edit.
libs=r/'new-library';globaltex=r/'new-textures';libs.mkdir(exist_ok=True);globaltex.mkdir(exist_ok=True);aliases={};texture_rows=[]
for pair in d['materials']:
 for n in pair:
  if not n or n in aliases:continue
  src=before/n;assert src.is_file(),n;h=hashlib.sha256(src.read_bytes()).hexdigest();packaged=Path('/Users/motoricallc/Downloads/fluxara-drift/build-ios-shared-props-simulator/Debug-iphonesimulator/Fluxara Drift.app/data/textures')/n;already=packaged.is_file() and hashlib.sha256(packaged.read_bytes()).hexdigest()==h;alias=n if already else 'fluxara_pool_'+h[:12]+src.suffix;aliases[n]=alias;dst=globaltex/alias;shutil.copy2(src,dst);texture_rows.append({'original':n,'alias':alias,'source':str(src),'path':str(dst),'bytes':dst.stat().st_size,'sha256':h,'previouslyPackaged':already,'previouslyPackagedPath':str(packaged) if already else None})
placements=[];prototypes=[];removed=set();rejected=[]
import xml.etree.ElementTree as E
for key,rows in groups.items():
 rows=[q for q in rows if gm(q).to_3x3().determinant()>0]
 if len(rows)<2:continue
 first=rows[0];vertices=get_vertices(first);valid=[(first,{'localPositionError':0,'worldPositionError':0,'localNormalError':0,'triangleTopologyAndUVColorExact':True})]
 for row in rows[1:]:
  proof=check(vertices,row)
  if proof:valid.append((row,proof))
  else:rejected.append(row['name'])
 if len(valid)<2:continue
 name='fluxara_driftlib_spell_reuse_'+key[:12];folder=libs/name;folder.mkdir(exist_ok=True);chunks=collections.defaultdict(list)
 for bi,ti in first['matched']:chunks[bi].append(ti)
 model=name+'_main.spm';new=write_model(folder/model,chunks,gm(first),aliases)
 scene=E.Element('scene');E.SubElement(scene,'object',id=name+'_mesh',type='animation',model=model,xyz='0 0 0',hpr='0 0 0',scale='1 1 1',interaction='ghost',**{'skeletal-animation':'false'});E.ElementTree(scene).write(folder/'node.xml',encoding='unicode')
 for row,proof in valid:
  mat=Matrix(row['matrix']);loc,rot,scale=mat.decompose();eu=rot.to_euler('XZY');gamexyz=[loc.x,loc.z,loc.y];hpr=[-math.degrees(eu.x),-math.degrees(eu.z),-math.degrees(eu.y)];sc=[scale.x,scale.z,scale.y]
  rebuilt=Matrix.Translation(loc)@eu.to_matrix().to_4x4()@Matrix.Diagonal((*scale,1));assert max(abs(mat[i][j]-rebuilt[i][j]) for i in range(4) for j in range(4))<.0001
  ident='PoolReuse_'+row['name'];placements.append({'id':ident,'sourceObject':row['name'],'library':name,'xyz':gamexyz,'hpr':hpr,'scale':sc,'sourceMatrix':row['matrix'],'worldGeometryMatchesOriginalScenery':proof});removed.update(tuple(q) for q in row['matched'])
 prototypes.append({'library':name,'sourceObject':first['name'],'instances':len(valid),'triangles':sum(len(b['indices'])//3 for b in new['buffers']),'localBounds':new['bounds'],'model':str(folder/model),'nativeMesh':bpy.data.objects[first['name']].data.name})
remaining=collections.defaultdict(list)
for bi,b in enumerate(d['buffers']):
 for ti in range(0,len(b['indices']),3):
  if (bi,ti) not in removed:remaining[bi].append(ti)
used_proto_tex={n for q in prototypes for pair in parse(q['model'])['materials'] for n in pair if n}
retained_aliases={n:a for n,a in aliases.items() if a in used_proto_tex}
new=write_model(out/'spell_gardens.spm',remaining,aliases=retained_aliases,bounds=d['bounds'])
# Check the retained triangle stream uses the exact original vertex records.
for oldbi,newb in zip(sorted(remaining),new['buffers']):
 old=d['buffers'][oldbi];kept=[i for ti in remaining[oldbi] for i in old['indices'][ti:ti+3]];source_records=[bytes(d['raw'][old['vertices'][i]['offset']:end_vertex(old['vertices'][i],old)]) for i in kept]
 actual=[]
 for i in newb['indices']:
  v=newb['vertices'][i];end=v['offset']+12+(4 if new['flags']&1 else 0)
  if new['flags']&2:end+=1+(3 if new['raw'][end]!=128 else 0)
  if new['materials'][newb['material']][0]:end+=4+(4 if new['materials'][newb['material']][1] else 0)+(4 if new['flags']&4 else 0)
  actual.append(bytes(new['raw'][v['offset']:end]))
 assert source_records==actual
x=E.parse(out/'scene.xml')
for row in placements:E.SubElement(x.getroot(),'library',name=row['library'],id=row['id'],xyz=' '.join(f'{v:.9g}' for v in row['xyz']),hpr=' '.join(f'{v:.9g}' for v in row['hpr']),scale=' '.join(f'{v:.9g}' for v in row['scale']))
x.write(out/'scene.xml',encoding='utf-8',xml_declaration=True)
used_tex={n for q in prototypes for pair in parse(q['model'])['materials'] for n in pair if n}
texture_rows=[q for q in texture_rows if q['alias'] in used_tex]
archive=r/'unused-candidate-textures';archive.mkdir(exist_ok=True)
for p in globaltex.iterdir():
 if p.name not in used_tex:shutil.move(str(p),str(archive/p.name))
remaining_original_refs={n for f in out.glob('*.spm') for pair in parse(f)['materials'] for n in pair if n}
mats=E.parse(out/'materials.xml');original={q.get('name'):q for q in mats.getroot()}
for q in texture_rows:
 if q['original']==q['alias']:continue
 e=E.fromstring(E.tostring(original[q['original']])) if q['original'] in original else E.Element('material',name=q['original']);e.set('name',q['alias']);mats.getroot().append(e)
 if q['original'] in original and q['original'] not in remaining_original_refs:mats.getroot().remove(original[q['original']])
mats.write(out/'materials.xml',encoding='utf-8',xml_declaration=True)
# Shared files keep their original names and exact bytes. Remaining local models
# use the engine global texture search fallback; their material definitions stay.
for q in texture_rows:
 local=out/q['original']
 assert local.read_bytes()==Path(q['path']).read_bytes()
 if q['original'] in remaining_original_refs:continue
 shutil.move(str(local),str(archive/local.name))
oldbytes=sum(p.stat().st_size for p in before.iterdir() if p.is_file());newbytes=sum(p.stat().st_size for p in out.iterdir() if p.is_file());shared=sum(p.stat().st_size for p in libs.rglob('*') if p.is_file())+sum(q['bytes'] for q in texture_rows if not q['previouslyPackaged']);proof={'trackId':track,'stage':'Candidate; not integrated or runtime validated','sourceBytes':oldbytes,'candidateTrackBytes':newbytes,'allNewSharedBytes':shared,'totalCandidateBytes':newbytes+shared,'weightNotIncreased':newbytes+shared<=oldbytes,'coordinateInstances':len(placements),'uniqueModels':len(prototypes),'extractedTriangles':len(removed),'remainderVertexRecordsAndTriangleOrderExact':True,'routeMeshesUnchanged':True,'originalSceneNodesUnchanged':True,'rejectedNativeSourceObjects':rejected,'prototypes':prototypes,'textures':texture_rows,'placements':placements}
(r/'spell-extraction.json').write_text(json.dumps(proof,indent=2));assert proof['weightNotIncreased'];assert len(placements)>0
print('SPELL_EXTRACTION_CANDIDATE',len(placements),len(prototypes),oldbytes,newbytes+shared,flush=True)
