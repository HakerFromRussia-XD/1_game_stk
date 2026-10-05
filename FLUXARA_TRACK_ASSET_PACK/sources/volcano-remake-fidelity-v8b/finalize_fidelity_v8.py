from pathlib import Path
import bpy,json,sys,xml.etree.ElementTree as E,hashlib
from mathutils import Matrix
r=Path(__file__).resolve().parent;w=r/'fidelity-v8';native=w/'native';native.mkdir(exist_ok=True);pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK');pool=json.loads(Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_POOL.json').read_text())
a=json.loads((r/'fidelity-v7b/asset-registration.json').read_text());bpy.ops.wm.open_mainfile(filepath=a['finalBlend']);bpy.context.preferences.filepaths.save_version=0;sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
def mesh_from_buffer(name,b,materials):
    mesh=bpy.data.meshes.new(name);mesh.from_pydata([(v['position'][0],v['position'][2],v['position'][1])for v in b['vertices']],[],[tuple(reversed(b['indices'][t:t+3]))for t in range(0,len(b['indices']),3)]);uv=mesh.uv_layers.new(name='UVMap')if b['vertices'][0].get('uv')else None;col=mesh.color_attributes.new(name='Color',type='BYTE_COLOR',domain='CORNER')
    for mat in materials:mesh.materials.append(mat)
    normals=[]
    for polygon in mesh.polygons:
        polygon.use_smooth=True
        for loop in polygon.loop_indices:
            v=b['vertices'][mesh.loops[loop].vertex_index]
            if uv:uv.data[loop].uv=v['uv']
            col.data[loop].color_srgb=tuple(x/255 for x in v.get('color',(255,255,255)))+(1,)
            n=[((v['normal']>>(10*k))&1023)for k in range(3)];n=[(v-1024 if v>511 else v)/511 for v in n];normals.append((n[0],n[2],n[1]))
    mesh.normals_split_custom_set(normals);return mesh
main=parse(w/'candidate/volcano_track.spm');updates=[]
for index,texture in [(6,'castelwall.jpg'),(14,'roof_3.jpg')]:
    targets=[obj for obj in bpy.data.objects if obj.type=='MESH'and Path(obj.get('source_model','')).name=='volcano_track.spm'and any(any(n.type=='TEX_IMAGE'and n.image and Path(n.image.filepath).name==texture for n in m.node_tree.nodes)for m in obj.data.materials if m and m.use_nodes)]
    assert len(targets)==1,(texture,[o.name for o in targets]);obj=targets[0];old=obj.data;mesh=mesh_from_buffer('VRV8_MainBuffer_'+str(index),main['buffers'][index],list(old.materials))
    for linked in bpy.data.objects:
        if linked.type=='MESH'and linked.data==old:linked.data=mesh
    updates.append({'object':obj.name,'buffer':index,'texture':texture,'vertices':len(mesh.vertices),'triangles':len(main['buffers'][index]['indices'])//3})
for obj in bpy.data.objects:
    if Path(obj.get('source_model','')).name=='volcano_track.spm':obj['source_model']=str(w/'candidate/volcano_track.spm')
row=next(q for q in pool['objects']if q['id']=='lap-v1-f4c4d2b2153a47ef');matrow=next(q for q in pool['materials']if q['id']=='lap-v1-material-00515707869a')
with bpy.data.libraries.load(row['physicalSourcePath'],link=False)as(src,dest):dest.objects=[row['name']]
proto=dest.objects[0];assert proto.name==row['name'];prototype_col=bpy.data.collections['Volcano Remake Asset Prototypes'];prototype_col.objects.link(proto);proto.hide_set(True);proto.hide_render=True;proto['asset_id']=row['id'];proto['source_model']=row['sourceModel'];a['objects'].append({k:row[k]for k in ['id','name','sourceModel','triangles','materials']});a['materials'].append({k:matrow[k]for k in ['id','name','textures']})
scene=E.parse(w/'candidate/scene.xml').getroot();shared=bpy.data.collections['Volcano Remake Shared Instances'];controls=bpy.data.collections['Volcano Remake Protected Gameplay']
for change in json.loads((w/'castle-changes.json').read_text()):
    xyz=change['xyz'];scale=change['scale'];matrix=Matrix.Translation((xyz[0],xyz[2],xyz[1]))@Matrix.Diagonal((scale[0],scale[2],scale[1],1));obj=bpy.data.objects.new(change['id'],proto.data);shared.objects.link(obj);obj.matrix_world=matrix;obj['shared_runtime_library']='fluxara_driftlib_castle_tower_v1';obj['source_prototype']=proto.name;a['nativeSharedInstances'].append({'name':obj.name,'prototype':proto.name,'library':'fluxara_driftlib_castle_tower_v1','matrix':[list(v)for v in matrix]})
    xml=next(q for q in scene.findall('object')if q.get('model')==change['collider']);d=parse(w/'candidate'/change['collider']);mesh=mesh_from_buffer(xml.get('id'),d['buffers'][0],[]);obj=bpy.data.objects.new(xml.get('id'),mesh);controls.objects.link(obj);obj.hide_set(True);obj.hide_render=True;obj['source_model']=str(w/'candidate'/change['collider']);obj['source_xml']=E.tostring(xml,encoding='unicode');obj['protected_original_collision']=True;a['nativeOriginalObjects'].append({'name':obj.name,'model':change['collider'],'matrix':[list(v)for v in Matrix.Identity(4)],'sourceXml':obj['source_xml']})
lib='fluxara_driftlib_castle_tower_v1';a['runtimeLibrarySources'][lib]=str(Path(row['sourceModel']).parent)
if not bpy.data.texts.get(lib+'/node.xml'):bpy.data.texts.new(lib+'/node.xml').write((Path(row['sourceModel']).parent/'node.xml').read_text())
texture=next(q for q in pool['textures']if q['id']in matrow['dependencies']);path=Path(texture['canonicalPackPath']);a['textures']['lap-catch-tower/dp_palette.png']={'source':str(Path(row['sourceModel']).parent/'dp_palette.png'),'packPath':str(path),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'poolId':texture['id'],'namespace':'Existing tower-local palette; distinct from map-local palettes with the same filename.'}
for filename in ['scene.xml','materials.xml']:bpy.data.texts[filename].clear();bpy.data.texts[filename].write((w/'candidate'/filename).read_text())
a.update({'finalBlend':str(native/'Volcano Remake.blend'),'newPrototypes':[],'reusedPrototypeIds':[q['id']for q in a['objects']],'mainBufferUpdates':updates,'status':'V8 castle reuse draft; two existing pooled towers, original collision retained in map-only physics meshes. Production unchanged.'})
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=a['finalBlend']);(w/'asset-registration.json').write_text(json.dumps(a,indent=2));print('V8_NATIVE_READY',len(a['objects']),len(a['nativeSharedInstances']),flush=True)
