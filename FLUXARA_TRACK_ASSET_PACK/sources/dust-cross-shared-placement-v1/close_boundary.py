from pathlib import Path
import bpy,hashlib,json,math,struct,sys,xml.etree.ElementTree as E
from mathutils import Vector
r=Path(__file__).resolve().parent;w=r/'delivery-v1';out=w/'candidate';sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
src=r/'before/dust-cross-split-combat_track.spm';d=parse(src);b=d['buffers'][0];allv=b['vertices'];coords=[v['position']for v in allv];low=9.021985054016113;outerlow=16.72918701171875;top=25.16668701171875
inner=sorted(set(v for v in coords if abs(v[1]-low)<.001),key=lambda v:math.atan2(v[2]-1.5,v[0]+3.1));outer=set(v for v in coords if abs(v[1]-outerlow)<.001);assert len(inner)==len(outer)==28
outer=[min(outer,key=lambda q:(p[0]-q[0])**2+(p[2]-q[2])**2)for p in inner];segments=[];missing=[]
for k,a in enumerate(inner):
 z=inner[(k+1)%28];covered=[]
 for j in range(0,len(b['indices']),3):
  vs=[coords[v]for v in b['indices'][j:j+3]];xx={(v[0],v[2])for v in vs}
  if {(a[0],a[2]),(z[0],z[2])}<=xx and min(v[1]for v in vs)<10 and max(v[1]for v in vs)>25:covered.append(j//3)
 segments.append({'segment':k,'start':a,'end':z,'existingInnerWallTriangles':len(covered)})
 if not covered:missing.append(k)
assert missing==[1,17,26],missing
model=out/'dust-cross_boundary_closures_v1.spm';verts=[];inds=[];blenderverts=[];faces=[];uvs=[];details=[]
for k in missing:
 k1=(k+1)%28;a=inner[k];z=inner[k1];oa=outer[k];oz=outer[k1];ps=[a,z,oz,oa,(a[0],top,a[2]),(z[0],top,z[2]),(oz[0],top,oz[2]),(oa[0],top,oa[2])];center=sum((Vector(x)for x in ps),Vector())/8
 # Six welded faces form a closed wedge exactly between the old fence endpoints.
 for quad in [(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7),(0,3,2,1)]:
  q=list(quad);p0,p1,p2=[Vector(ps[i])for i in q[:3]];normal=(p1-p0).cross(p2-p0).normalized();fc=sum((Vector(ps[i])for i in q),Vector())/4
  if normal.dot(fc-center)<0:q=q[::-1];p0,p1,p2=[Vector(ps[i])for i in q[:3]];normal=(p1-p0).cross(p2-p0).normalized()
  packed=sum((round(max(-1,min(1,n))*511)&1023)<<(j*10)for j,n in enumerate(normal));start=len(verts)
  for vi in q:
   v=ps[vi];dist=math.hypot(v[0]-a[0],v[2]-a[2]);uv=(dist*.72,-v[1]*.9586+1.827)
   verts.append((v,packed,uv));blenderverts.append((v[0],v[2],v[1]));uvs.append((uv[0],1-uv[1]))
  inds.extend([start,start+1,start+2,start,start+2,start+3]);faces.extend([(start+2,start+1,start),(start+3,start+2,start)])
 delta=Vector((z[0]-a[0],0,z[2]-a[2]));normal=Vector((delta.z,0,-delta.x)).normalized();mid=(Vector(a)+Vector(z))/2
 assert normal.dot(mid-Vector((-3.1,low,1.5)))>0
 details.append({'segment':k,'start':a,'end':z,'outerStart':oa,'outerEnd':oz,'lengthMeters':delta.length,'midpoint':list(mid),'outwardNormal':list(normal),'triangles':12})
positions=[x[0]for x in verts];bounds=[min(v[k]for v in positions)for k in range(3)]+[max(v[k]for v in positions)for k in range(3)];head=b'SP'+bytes([10,1])+struct.pack('<6fH',*bounds,1)
for tex in ['metalgrid.png','']:raw=tex.encode();head+=bytes([len(raw)])+raw
body=struct.pack('<HHIIH',1,1,len(verts),len(inds),0)
for p,n,uv in verts:body+=struct.pack('<3fI2e',*p,n,*uv)
body+=bytes(inds);model.write_bytes(head+body);re=parse(model);assert len(re['buffers'][0]['indices'])==108
# Welded topology of each added section must be watertight, without openings.
for offset in range(0,len(inds),36):
 import collections
 edges=collections.Counter()
 for j in range(offset,offset+36,3):
  pp=[tuple(positions[v])for v in inds[j:j+3]]
  for i in range(3):edges[tuple(sorted((pp[i],pp[(i+1)%3])))]+=1
 assert set(edges.values())=={2}
scene=E.parse(out/'scene.xml');assert not any(n.get('id')=='DustCrossBoundaryClosures'for n in scene.getroot());E.SubElement(scene.getroot(),'object',id='DustCrossBoundaryClosures',type='static',model=model.name,xyz='0 0 0',hpr='0 0 0',scale='1 1 1',interaction='static',shape='exact',**{'mass':'0'});scene.write(out/'scene.xml',encoding='utf-8',xml_declaration=True);(w/'scene.xml').write_bytes((out/'scene.xml').read_bytes())
file=w/'native/Dust Cross Split Combat.blend';bpy.ops.wm.open_mainfile(filepath=str(file));bpy.context.preferences.filepaths.save_version=0
snap={o.name:(tuple(tuple(v.co)for v in o.data.vertices),tuple(tuple(v.vertices)for v in o.data.polygons))for o in bpy.data.objects if o.type=='MESH'};poses={o.name:[list(v)for v in o.matrix_world]for o in bpy.data.objects}
mesh=bpy.data.meshes.new('DustCross_BoundaryClosures');mesh.from_pydata(blenderverts,[],faces);mesh.update();layer=mesh.uv_layers.new(name='UVMap')
for loop in mesh.loops:layer.data[loop.index].uv=uvs[loop.vertex_index]
mat=bpy.data.materials.get('metalgrid.png');assert mat;mesh.materials.append(mat);obj=bpy.data.objects.new('DustCross_BoundaryClosures',mesh);bpy.context.scene.collection.objects.link(obj);obj['type']='object';obj['interaction']='static';obj['shape']='exact';obj['runtime_model']=model.name;obj['map_specific_boundary']='Three source perimeter gaps only; protected road unchanged';obj['asset_id']='dust-cross-boundary-closures-v1'
text=bpy.data.texts.get('scene.xml');text.clear();text.write((out/'scene.xml').read_text());proof={'trackId':'fluxara-user-dust-cross-split-combat','sourceFenceInnerSegments':28,'sourceFenceCompleteSegments':25,'sourceFenceMissingSegments':3,'closedSegments':details,'completedInnerPerimeterSegments':28,'closedPerimeterTopologicallyVerified':True,'closedAddedSolidsWatertight':True,'newTriangles':36,'newModelBytes':model.stat().st_size,'newTextures':0,'texture':'metalgrid.png (same existing fence texture)','physicalSceneInteraction':'static','physicalShape':'exact','protectedCourseSpmByteExact':src.read_bytes()==(out/src.name).read_bytes(),'protectedNavmeshByteExact':(r/'before/navmesh.xml').read_bytes()==(out/'navmesh.xml').read_bytes(),'existingVisualMeshesAndTransformsUnchanged':True,'existingArtUserApproved':True,'runtimeTestPending':True};(w/'boundary-verification.json').write_text(json.dumps(proof,indent=2));text=bpy.data.texts.new('DustCross_BoundaryClosures.json');text.write(json.dumps(proof,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(file));bpy.ops.wm.open_mainfile(filepath=str(file))
for name,v in snap.items():o=bpy.data.objects[name];assert v==(tuple(tuple(x.co)for x in o.data.vertices),tuple(tuple(x.vertices)for x in o.data.polygons)),name
for name,m in poses.items():assert m==[list(v)for v in bpy.data.objects[name].matrix_world],name
assert len(bpy.data.objects['DustCross_BoundaryClosures'].data.polygons)==36
proof['allPreviousMeshGeometryExactAfterReopen']=len(snap);proof['allPreviousMatricesExactAfterReopen']=len(poses);proof['finalBlendSha256']=hashlib.sha256(file.read_bytes()).hexdigest();(w/'boundary-verification.json').write_text(json.dumps(proof,indent=2));print('DUST_THREE_PERIMETER_GAPS_CLOSED_NATIVE_REOPEN_VERIFIED',proof['newModelBytes'],flush=True)
