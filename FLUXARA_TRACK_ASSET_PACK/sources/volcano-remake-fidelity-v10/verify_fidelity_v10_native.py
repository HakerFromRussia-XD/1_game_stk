from pathlib import Path
import bpy,json,sys,math,hashlib
r=Path(__file__).resolve().parent;w=r/'fidelity-v10';code=(r/'verify_blend.py').read_text().replace("r/'asset-registration.json'","r/'fidelity-v10/asset-registration.json'").replace("r/'candidate'","r/'fidelity-v10/candidate'").replace("r/'final-blend-verification.json'","r/'fidelity-v10/final-blend-verification.json'");exec(compile(code,str(r/'verify_blend.py'),'exec'));sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
a=json.loads((w/'asset-registration.json').read_text());checks=[]
for row in a['newPrototypes']:
 obj=bpy.data.objects[row['name']];b=parse(row['sourceModel'])['buffers'][row['sourceBuffer']];assert len(obj.data.vertices)==len(b['vertices']);assert max(abs(x-y)for v,s in zip(obj.data.vertices,b['vertices'])for x,y in zip(v.co,(s['position'][0],s['position'][2],s['position'][1])))<.00002;assert [tuple(p.vertices)for p in obj.data.polygons]==[tuple(reversed(b['indices'][t:t+3]))for t in range(0,len(b['indices']),3)]
 error=0;angle=0;degenerate=0;areas={l:p.area for p in obj.data.polygons for l in p.loop_indices}
 for l in obj.data.loops:
  v=b['vertices'][l.vertex_index];assert max(abs(x-y)for x,y in zip(obj.data.uv_layers['UVMap'].data[l.index].uv,(v['uv'][0],1-v['uv'][1])))<1e-7;bits=[(v['normal']>>(10*k))&1023 for k in range(3)];n=[(x-1024 if x>511 else x)/511 for x in bits];n=[n[0],n[2],n[1]];length=math.sqrt(sum(x*x for x in n))
  if length>1e-5:
   if areas[l.index]<1e-10:
    degenerate+=1;continue
   actual=obj.data.corner_normals[l.index].vector;error=max(error,max(abs(x-y/length)for x,y in zip(actual,n)));dot=sum(x*y/length for x,y in zip(actual,n));angle=max(angle,math.degrees(math.acos(max(-1,min(1,dot)))))
 print('MEASURED_NATIVE_NORMALS',row['name'],error,angle,flush=True);assert angle<1,(row['name'],angle)
 for node in obj.data.materials[0].node_tree.nodes:
  if node.type=='TEX_IMAGE':assert node.image.packed_file and hashlib.sha256(node.image.packed_file.data).hexdigest()==a['textures']['vr_moss_palette.jpg']['sha256']
 update=next(q for q in a['cliffBufferUpdates']if q['model']==Path(row['sourceModel']).name);assert all(bpy.data.objects[name].data==obj.data for name in update['objects']);checks.append({'prototype':obj.name,'triangles':row['triangles'],'positionsIndicesUvsMatchSpm':True,'maximumCustomNormalComponentError':error,'maximumCustomNormalAngularErrorDegrees':angle,'nativeNormalAngularToleranceDegrees':1,'nativeNormalsAreNotBitIdenticalToPackedSpm':True,'zeroAreaCornerNormalsExcluded':degenerate,'zeroAreaGeometryStillRetained':True,'originalNativeCliffInstancePartsLinkedToPrototype':len(update['objects'])})
p=w/'final-blend-verification.json';data=json.loads(p.read_text());data.update({'newCliffPrototypes':checks,'cliffPalettePixelsMatchExistingSource':True});p.write_text(json.dumps(data,indent=2));print('V10_NATIVE_CLIFFS_AND_NORMALS_VERIFIED',flush=True)
