from pathlib import Path
import bpy,json,sys,hashlib,xml.etree.ElementTree as E,faulthandler
faulthandler.enable()
from mathutils import Matrix
r=Path(__file__).resolve().parent;w=r/'fidelity-v9';native=w/'native';native.mkdir(exist_ok=True);pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK');mod=pack/'models/volcano-remake-fidelity-v9';mod.mkdir(exist_ok=True)
a=json.loads((r/'fidelity-v8b/asset-registration.json').read_text());bpy.ops.wm.open_mainfile(filepath=a['finalBlend']);bpy.context.preferences.filepaths.save_version=0
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
def mesh_from_buffer(name,b,materials):
    print('MESH_CREATE',name,len(b['vertices']),len(b['indices']),flush=True)
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata([(v['position'][0],v['position'][2],v['position'][1])for v in b['vertices']],[],[tuple(reversed(b['indices'][t:t+3]))for t in range(0,len(b['indices']),3)])
    mesh.update(calc_edges=True)
    assert not mesh.validate(verbose=True)
    print('MESH_TOPOLOGY_READY',name,len(mesh.loops),flush=True)
    for mat in materials:mesh.materials.append(mat)
    if b['vertices'][0].get('uv'):
        uv=mesh.uv_layers.new(name='UVMap');values=[]
        for loop in mesh.loops:
            source=b['vertices'][loop.vertex_index]['uv'];values.extend([source[0],1-source[1]])
        uv.data.foreach_set('uv',values)
    col=mesh.color_attributes.new(name='Color',type='FLOAT_COLOR',domain='CORNER');colors=[]
    for loop in mesh.loops:colors.extend([x/255 for x in b['vertices'][loop.vertex_index].get('color',(255,255,255))]+[1])
    col.data.foreach_set('color',colors)
    mesh.polygons.foreach_set('use_smooth',[True]*len(mesh.polygons));mesh.update();print('MESH_DONE',name,flush=True);return mesh
updates=a['mainBufferUpdates']
for obj in bpy.data.objects:
    if Path(obj.get('source_model','')).name=='volcano_track.spm':obj['source_model']=str(w/'candidate/volcano_track.spm')
skin=json.loads((w/'skin-changes.json').read_text());oldproto=bpy.data.objects['VRV8B_Prototype_CastleTower'];oldmat=oldproto.data.materials[0];mat=oldmat.copy();mat.name='VRV9_CastlePalette';mat['asset_id']='volcano-fidelity-v9-castle-material'
image=bpy.data.images.load(str(Path(skin['library'])/skin['runtimeTextureAlias']),check_existing=False);image.name=skin['runtimeTextureAlias'];image.pack()
for node in mat.node_tree.nodes:
    if node.type=='TEX_IMAGE':node.image=image
print('BUILD_TOWER',flush=True);source=parse(skin['adaptedModel']);mesh=mesh_from_buffer('VRV9_CastleTowerMesh',source['buffers'][0],[mat]);proto=bpy.data.objects.new('VRV9_Prototype_CastleTower',mesh);bpy.data.collections['Volcano Remake Asset Prototypes'].objects.link(proto);proto.hide_set(True);proto.hide_render=True;proto['asset_id']='volcano-fidelity-v9-castle-tower';proto['source_model']=skin['adaptedModel']
row={'id':proto['asset_id'],'name':proto.name,'sourceModel':skin['adaptedModel'],'triangles':skin['triangles'],'materials':[mat.name]};a['objects']=[q for q in a['objects']if q['id']!='volcano-fidelity-v8b-castle-tower']+[row];a['materials']=[q for q in a['materials']if q['id']!='volcano-fidelity-v8b-castle-material']+[{'id':mat['asset_id'],'name':mat.name,'textures':[skin['runtimeTextureAlias']]}]
scene=E.parse(w/'candidate/scene.xml').getroot()
print('BUILD_INSTANCES_AND_COLLIDERS',flush=True)
for change in json.loads((w/'castle-changes.json').read_text()):
    obj=bpy.data.objects[change['id']];obj.data=mesh;xyz=change['xyz'];scale=change['scale'];matrix=Matrix.Translation((xyz[0],xyz[2],xyz[1]))@Matrix.Diagonal((scale[0],scale[2],scale[1],1));obj.matrix_world=matrix;obj['source_prototype']=proto.name;obj['shared_runtime_library']=Path(skin['library']).name
    entry=next(q for q in a['nativeSharedInstances']if q['name']==obj.name);entry.update({'prototype':proto.name,'library':Path(skin['library']).name,'matrix':[list(v)for v in matrix]})
    xml=next(q for q in scene.findall('object')if q.get('model')==change['collider']);obj=bpy.data.objects[xml.get('id')];d=parse(w/'candidate'/change['collider']);obj.data=mesh_from_buffer(xml.get('id'),d['buffers'][0],[]);obj['source_model']=str(w/'candidate'/change['collider']);obj['source_xml']=E.tostring(xml,encoding='unicode');entry=next(q for q in a['nativeOriginalObjects']if q['name']==obj.name);entry['sourceXml']=obj['source_xml']
bpy.data.objects.remove(oldproto,do_unlink=True);a['runtimeLibrarySources'].pop('fluxara_driftlib_volcano_castle_tower_v8b');a['runtimeLibrarySources'][Path(skin['library']).name]=skin['library']
for name in ['node.xml','materials.xml']:bpy.data.texts.new(Path(skin['library']).name+'/'+name).write((Path(skin['library'])/name).read_text())
for filename in ['scene.xml','materials.xml']:bpy.data.texts[filename].clear();bpy.data.texts[filename].write((w/'candidate'/filename).read_text())
texture=Path(skin['library'])/skin['runtimeTextureAlias'];alias=pack/'textures/volcano-remake-fidelity-v9'/texture.name;alias.parent.mkdir(exist_ok=True);alias.write_bytes(texture.read_bytes());a['textures'][texture.name]={'source':str(texture),'packPath':str(alias),'bytes':texture.stat().st_size,'sha256':hashlib.sha256(texture.read_bytes()).hexdigest(),'poolId':'volcano-fidelity-v9-castle-texture-alias','reusedPixelsPoolId':'lap-v1-texture-3cef9b82dce3'}
a['newPrototypes']=[row];a['reusedPrototypeIds']=[q['id']for q in a['objects']if q['id']!=row['id']];a['visualLibrary']=str(mod/'Volcano Remake Castle Library.blend');bpy.data.libraries.write(a['visualLibrary'],{proto},fake_user=True,compress=True)
model=mod/Path(skin['adaptedModel']).name;model.write_bytes(Path(skin['adaptedModel']).read_bytes())
a.update({'finalBlend':str(native/'Volcano Remake.blend'),'mainBufferUpdates':updates,'status':'V9 gray pooled tower with true red conical roof; protected map collision exact. Source tower body and local bounds/origin/axes exact; top reshaped to cone; model plus texture weight decreased. Map bytes decrease including new shared resources. Production unchanged.'})
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=a['finalBlend']);(w/'asset-registration.json').write_text(json.dumps(a,indent=2));print('V9_NATIVE_READY',len(a['objects']),len(a['nativeSharedInstances']),flush=True)
