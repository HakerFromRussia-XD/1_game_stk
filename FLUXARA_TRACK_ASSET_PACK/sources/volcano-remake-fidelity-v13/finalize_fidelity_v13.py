from pathlib import Path
import bpy,json,sys,hashlib,math,xml.etree.ElementTree as E
from mathutils import Matrix,Vector
r=Path(__file__).resolve().parent;w=r/'fidelity-v13';pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK');mod=pack/'models/volcano-remake-fidelity-v13';mod.mkdir(exist_ok=True);native=w/'native';native.mkdir(exist_ok=True)
a=json.loads((r/'fidelity-v12/asset-registration.json').read_text());proof=json.loads((w/'fountain-changes.json').read_text());bpy.ops.wm.open_mainfile(filepath=a['finalBlend']);bpy.context.preferences.filepaths.save_version=0
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
helper=(r/'finalize_fidelity_v9.py').read_text();exec(helper[helper.index('def mesh_from_buffer'):helper.index('updates=a')])
def native_mesh(name,b,mats):
 mesh=mesh_from_buffer(name,b,mats);norm=[]
 for loop in mesh.loops:
  p=b['vertices'][loop.vertex_index]['normal'];v=[]
  for shift in [0,10,20]:
   q=(p>>shift)&1023;v.append((q-1024 if q>511 else q)/511)
  n=Vector((v[0],v[2],v[1]));n.normalize();norm.append(n)
 mesh.normals_split_custom_set(norm);mesh.update();assert all(n.vector.length>.9 for n in mesh.corner_normals),name;return mesh
# Replace only the visible column submesh; every other mesh stays linked to its old data.
changed_meshes=[];old_meshes={o.data for o in bpy.data.objects if o.type=='MESH'and Path(o.get('source_model','')).name=='volcano_track.spm'and any(m and m.name.startswith('VRV4E_lava_2k_diffuse.jpg')for m in o.data.materials)}
assert len(old_meshes)==1,[m.name for m in old_meshes]
b=parse(w/'candidate/volcano_track.spm')['buffers'][12]
for mesh in old_meshes:
 replacement=native_mesh('VRV13_MainLavaPatches',b,list(mesh.materials));users=[o for o in bpy.data.objects if o.type=='MESH'and o.data==mesh]
 for o in users:o.data=replacement;changed_meshes.append(o.name)
# Shared image alias carries the original pixels; material variants avoid mutating donors.
texture=Path(proof['newGlobalTexture']);target=pack/'textures/volcano-remake-fidelity-v13'/texture.name;target.parent.mkdir(exist_ok=True);target.write_bytes(texture.read_bytes());image=bpy.data.images.load(str(target),check_existing=False);image.name=texture.name;image.pack();oldrows=[q for q in a['materials']if 'lava_2k_diffuse.jpg'in q.get('textures',[])];assert len(oldrows)==6
mapping={};newrows=[]
for i,row in enumerate(oldrows):
 mat=bpy.data.materials[row['name']].copy();mat.name=f'VRV13_LavaShared_{i}';mat['asset_id']=f'volcano-fidelity-v13-lava-material-{i}'
 for node in mat.node_tree.nodes:
  if node.type=='TEX_IMAGE'and node.image and 'lava_2k_diffuse.jpg'in node.image.name:node.image=image
 mapping[row['name']]=mat;newrows.append({'id':mat['asset_id'],'name':mat.name,'textures':[texture.name],'sourceMaterialId':row['id'],'adaptation':'Original material settings and pixels retained; shared runtime texture filename alias only.'})
for mesh in bpy.data.meshes:
 for i,mat in enumerate(mesh.materials):
  if mat and mat.name in mapping:mesh.materials[i]=mapping[mat.name]
a['materials']=[q for q in a['materials']if q not in oldrows]+newrows
oldtex=a['textures'].pop('lava_2k_diffuse.jpg');a['textures'][texture.name]={'source':str(texture),'packPath':str(target),'bytes':texture.stat().st_size,'sha256':hashlib.sha256(texture.read_bytes()).hexdigest(),'poolId':'volcano-fidelity-v13-lava-texture-alias','reusedPixelsSource':oldtex['packPath'],'reusedPixelsSha256':oldtex['sha256']}
lib=Path(proof['newSharedLibrary']);d=parse(proof['newSharedModel']);mesh=native_mesh('VRV13_LavaFountainMesh',d['buffers'][0],[mapping[oldrows[0]['name']]]);proto=bpy.data.objects.new('VRV13_Prototype_LavaFountain',mesh);bpy.data.collections['Volcano Remake Asset Prototypes'].objects.link(proto);proto.hide_set(True);proto.hide_render=True;proto['asset_id']='volcano-fidelity-v13-lava-fountain';proto['source_model']=proof['newSharedModel'];row={'id':proto['asset_id'],'name':proto.name,'sourceModel':proof['newSharedModel'],'triangles':proof['triangles'],'materials':[mesh.materials[0].name],'role':'Three curved lava jets with flying embers, shared ghost scenery, preserves original column effect bounds and source collision separately.'};a['objects'].append(row);a['newPrototypes']=[row]
scene=E.parse(w/'candidate/scene.xml').getroot();xml=next(e for e in scene.findall('library')if e.get('id')=='VRV13_PooledLavaFountain');instance=bpy.data.objects.new(xml.get('id'),mesh);bpy.data.collections['Volcano Remake Shared Instances'].objects.link(instance);instance['shared_runtime_library']=lib.name;instance['source_prototype']=proto.name;instance['asset_id']=proto['asset_id'];instance['source_xml']=E.tostring(xml,encoding='unicode');a['nativeSharedInstances'].append({'name':instance.name,'prototype':proto.name,'library':lib.name,'matrix':[list(v)for v in instance.matrix_world],'sourcePlacementId':xml.get('id')})
xml=next(e for e in scene.findall('object')if e.get('id')=='VRV13_OriginalLavaColumnCollision');collmesh=native_mesh(xml.get('id'),parse(w/'candidate'/xml.get('model'))['buffers'][0],[]);o=bpy.data.objects.new(xml.get('id'),collmesh);col=next(c for c in bpy.data.collections if 'Protected' in c.name);col.objects.link(o);o.hide_set(True);o.hide_render=True;o['source_model']=str(w/'candidate'/xml.get('model'));o['source_xml']=E.tostring(xml,encoding='unicode');a['nativeOriginalObjects'].append({'name':o.name,'model':xml.get('model'),'matrix':[list(v)for v in o.matrix_world],'sourceXml':o['source_xml']})
cloudxml=next(e for e in scene.findall('object')if e.get('model')=='AshColumn.spm');cloudrow=next(q for q in a['nativeOriginalObjects']if q['model']=='AshColumn.spm');o=bpy.data.objects[cloudrow['name']];xyz=list(map(float,cloudxml.get('xyz').split()));o.matrix_world.translation=(xyz[0],xyz[2],xyz[1]);cloudrow['matrix']=[list(v)for v in o.matrix_world];cloudrow['sourceXml']=E.tostring(cloudxml,encoding='unicode');o['source_xml']=cloudrow['sourceXml']
for o in bpy.data.objects:
 if o.get('source_model')and 'fidelity-v12/candidate'in o['source_model']:o['source_model']=o['source_model'].replace('fidelity-v12/candidate','fidelity-v13/candidate')
 if o.get('source_xml'):o['source_xml']=o['source_xml'].replace('lava_2k_diffuse.jpg',texture.name)
for row in a['nativeOriginalObjects']:
 if 'sourceXml'in row:row['sourceXml']=row['sourceXml'].replace('lava_2k_diffuse.jpg',texture.name)
for filename in ['scene.xml','materials.xml']:
 bpy.data.texts[filename].clear();bpy.data.texts[filename].write((w/'candidate'/filename).read_text())
for filename in ['node.xml','materials.xml']:bpy.data.texts.new(lib.name+'/'+filename).write((lib/filename).read_text())
a['runtimeLibrarySources'][lib.name]=str(lib);a['visualLibrary']=str(mod/'Volcano Remake Fountain Library.blend');bpy.data.libraries.write(a['visualLibrary'],{proto,*mapping.values()},fake_user=True,compress=True);(mod/Path(proof['newSharedModel']).name).write_bytes(Path(proof['newSharedModel']).read_bytes())
a.update({'finalBlend':str(native/'Volcano Remake.blend'),'fountainChangedMainMeshObjects':changed_meshes,'fountainCloudObject':cloudrow['name'],'newMaterialVariants':newrows,'sourceLavaMaterialRows':oldrows,'status':'V13 lava fountain and linked smoke; stone UVs and image preserved. Isolated candidate; original physics retained in map-only hidden proxy; source production unchanged.'});bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=a['finalBlend']);(w/'asset-registration.json').write_text(json.dumps(a,indent=2));print('V13_NATIVE_FOUNTAIN_SAVED',len(a['objects']),len(a['materials']),len(a['nativeSharedInstances']),flush=True)
