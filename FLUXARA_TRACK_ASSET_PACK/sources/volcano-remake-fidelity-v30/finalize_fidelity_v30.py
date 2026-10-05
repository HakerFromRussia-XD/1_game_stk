from pathlib import Path
import bpy,json,hashlib,math,xml.etree.ElementTree as E
from mathutils import Matrix,Vector
r=Path(__file__).resolve().parent;w=r/'fidelity-v30';native=w/'native';native.mkdir(exist_ok=True);assert (w/'preservation-verification.json').is_file()
a=json.loads((r/'fidelity-v29/asset-registration.json').read_text());p=json.loads((w/'facade-placements.json').read_text());pool=json.loads(Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_POOL.json').read_text());tree=next(q for q in pool['objects']if q['id']=='dp-v2-dpv2-dp-roundedtree-prototype')
bpy.ops.wm.open_mainfile(filepath=a['finalBlend']);bpy.context.preferences.filepaths.save_version=0;assert bpy.data.objects.get(tree['name'])is None
source=Path(tree['physicalSourcePath']);assert hashlib.sha256(source.read_bytes()).hexdigest()==tree['file']['sha256']
with bpy.data.libraries.load(str(source),link=False)as(src,dest):assert tree['name']in src.objects;dest.objects=[tree['name']]
proto=dest.objects[0];proto.data.calc_loop_triangles();assert proto.name==tree['name']and len(proto.data.loop_triangles)==588
bpy.data.collections['Volcano Remake Asset Prototypes'].objects.link(proto);proto.hide_set(True);proto.hide_render=True;assert max(abs(proto.matrix_world[i][j]-Matrix.Identity(4)[i][j])for i in range(4)for j in range(4))<1e-6
proto['asset_id']=tree['id'];proto['source_model']=p['modelSources'][2]['path'];materials=[m.name for m in proto.data.materials]
row={'id':tree['id'],'name':proto.name,'sourceModel':p['modelSources'][2]['path'],'sourceBuffers':[0,1],'triangles':588,'materials':materials,'sourcePoolObjectId':tree['id'],'role':'Directly reused DP Motorsports rounded leaf tree, source native object/materials/images and runtime mesh unchanged. Newly placed on existing pooled cliff cap surfaces; no new game payload.'}
a['objects'].append(row);a['reusedPrototypes']=[row];a['newPrototypes']=[];a['newMaterialVariants']=[];a['reusedMaterialVariants']=[]
for name in materials:
    material=next(q for q in pool['materials']if q.get('name',q.get('displayName'))==name)
    if not any(q['name']==name for q in a['materials']):
        textures=sorted({Path(n.image.filepath).name for n in bpy.data.materials[name].node_tree.nodes if n.type=='TEX_IMAGE'and n.image})
        q={'id':material['id'],'name':name,'textures':textures,'sourcePoolMaterialId':material['id'],'role':'Existing pooled DP tree material; unchanged direct reuse.'};a['materials'].append(q);a['reusedMaterialVariants'].append(q)
scene=E.parse(w/'candidate/scene.xml').getroot();created=[]
for group in p['placements']:
    for attrs,prototype in zip(group['parts'],['VRV29_Prototype_GroundedStoneBody','VRV22_Prototype_GrassLip',tree['name']]):
        obj=bpy.data.objects.new(attrs['id'],bpy.data.objects[prototype].data);bpy.data.collections['Volcano Remake Shared Instances'].objects.link(obj)
        xyz=list(map(float,attrs['xyz'].split()));scale=list(map(float,attrs['scale'].split()));yaw=math.radians(float(attrs['hpr'].split()[1]));obj.matrix_world=Matrix.Translation(Vector((xyz[0],xyz[2],xyz[1])))@Matrix.Rotation(-yaw,4,'Z')@Matrix.Diagonal((scale[0],scale[2],scale[1],1))
        obj['source_prototype']=prototype;obj['source_model']=p['modelSources'][2]['path']if prototype==tree['name']else bpy.data.objects[prototype]['source_model'];obj['asset_id']=bpy.data.objects[prototype].get('asset_id');obj['shared_runtime_library']=attrs['name'];obj['protected_course_geometry']=False;obj['source_xml']=E.tostring(scene.find(f'library[@id="{attrs["id"]}"]'),encoding='unicode')
        a['nativeSharedInstances'].append({'name':obj.name,'prototype':prototype,'library':attrs['name'],'matrix':[list(v)for v in obj.matrix_world],'sourcePlacementId':attrs['id']});created.append(obj.name)
a['runtimeLibrarySources'][Path(p['modelSources'][2]['path']).parent.name]=str(Path(p['modelSources'][2]['path']).parent)
bpy.data.texts['scene.xml'].clear();bpy.data.texts['scene.xml'].write((w/'candidate/scene.xml').read_text());a['newFacadeNativeObjects']=created;a['directTreeSourceLibrary']=str(source)
a.update({'finalBlend':str(native/'Volcano Remake.blend'),'status':'V30 adds large pooled grass/stone facade groups with existing round leaf trees on actual cap triangles. Source local models/UVs/pixels and existing terrain/physics/road/control nodes unchanged. New coordinate scenery only; isolated candidate, reference fidelity and production/final/preview integration unfinished.'})
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=a['finalBlend']);(w/'asset-registration.json').write_text(json.dumps(a,indent=2));print('V30_POOLED_FACADES_NATIVE_SAVED',len(created),len(a['objects']),len(a['materials']),len(a['nativeSharedInstances']),flush=True)
