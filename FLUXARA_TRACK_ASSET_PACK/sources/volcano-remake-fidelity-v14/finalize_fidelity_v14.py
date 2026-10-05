from pathlib import Path
import bpy,json,sys,math
from mathutils import Vector
r=Path(__file__).resolve().parent;w=r/'fidelity-v14';pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK');mod=pack/'models/volcano-remake-fidelity-v14';mod.mkdir(exist_ok=True);native=w/'native';native.mkdir(exist_ok=True);a=json.loads((r/'fidelity-v13/asset-registration.json').read_text());proof=json.loads((w/'central-rock-changes.json').read_text());bpy.ops.wm.open_mainfile(filepath=a['finalBlend']);bpy.context.preferences.filepaths.save_version=0;sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
source=parse(r/'fidelity-v13/candidate/volcano_track.spm')['buffers'][1];changed=set();meshes={o.data for o in bpy.data.objects if o.type=='MESH'and Path(o.get('source_model','')).name=='volcano_track.spm'and len(o.data.polygons)==604 and any(m and 'vr_arch_stone.png'in m.name for m in o.data.materials)};assert len(meshes)==1,[m.name for m in meshes];mat=bpy.data.materials['VRV4E_Rock13_col.jpg']
for mesh in meshes:
 for poly in mesh.polygons:
  assert [tuple(mesh.vertices[j].co)for j in poly.vertices]==[(source['vertices'][i]['position'][0],source['vertices'][i]['position'][2],source['vertices'][i]['position'][1])for i in reversed(source['indices'][3*poly.index:3*poly.index+3])],poly.index
 mesh.materials.append(mat)
 for t in proof['originalComponentTriangleIds']:mesh.polygons[t].material_index=len(mesh.materials)-1
 changed.update(o.name for o in bpy.data.objects if o.type=='MESH'and o.data==mesh)
helper=(r/'finalize_fidelity_v9.py').read_text();exec(helper[helper.index('def mesh_from_buffer'):helper.index('updates=a')]);b=parse(w/'candidate/volcano_track.spm')['buffers'][2];mesh=mesh_from_buffer('VRV14_CentralRockMesh',b,[mat]);norm=[]
for loop in mesh.loops:
 p=b['vertices'][loop.vertex_index]['normal'];v=[]
 for shift in [0,10,20]:
  q=(p>>shift)&1023;v.append((q-1024 if q>511 else q)/511)
 n=Vector((v[0],v[2],v[1]));n.normalize();norm.append(n)
mesh.normals_split_custom_set(norm);mesh.update();assert all(n.vector.length>.9 for n in mesh.corner_normals)
proto=bpy.data.objects.new('VRV14_Prototype_CentralRock',mesh);bpy.data.collections['Volcano Remake Asset Prototypes'].objects.link(proto);proto.hide_set(True);proto.hide_render=True;proto['asset_id']='volcano-fidelity-v14-central-rock';proto['source_model']=str(w/'candidate/volcano_track.spm');proto['source_buffer']=2;row={'id':proto['asset_id'],'name':proto.name,'sourceModel':proto['source_model'],'sourceBuffer':2,'triangles':72,'materials':[mat.name],'role':'Original central decorative mountain geometry with existing textured rock material. Physics, UVs and bounds retained.'};a['objects'].append(row);a['newPrototypes']=[row];a['newMaterialVariants']=[];a['visualLibrary']=str(mod/'Volcano Remake Central Rock Library.blend');bpy.data.libraries.write(a['visualLibrary'],{proto},fake_user=True,compress=True);(mod/'volcano_track.spm').write_bytes((w/'candidate/volcano_track.spm').read_bytes())
for o in bpy.data.objects:
 if o.get('source_model')and 'fidelity-v13/candidate'in o['source_model']:o['source_model']=o['source_model'].replace('fidelity-v13/candidate','fidelity-v14/candidate')
a.update({'finalBlend':str(native/'Volcano Remake.blend'),'centralRockMaterialChangedMeshObjects':sorted(changed),'status':'V14 central mountain uses existing rock texture; original indexed geometry UVs normals and collision unchanged. No new materials or image files. Isolated candidate.'});bpy.ops.wm.save_as_mainfile(filepath=a['finalBlend']);(w/'asset-registration.json').write_text(json.dumps(a,indent=2));print('V14_NATIVE_ROCK_MATERIAL_SAVED',len(a['objects']),len(a['materials']),flush=True)
