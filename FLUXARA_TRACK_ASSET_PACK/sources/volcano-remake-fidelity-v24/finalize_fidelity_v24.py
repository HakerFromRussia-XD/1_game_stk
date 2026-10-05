from pathlib import Path
import bpy,json,shutil,sys,hashlib,xml.etree.ElementTree as E
from mathutils import Vector,Matrix,Euler
r=Path(__file__).resolve().parent;w=r/'fidelity-v24';pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK');mod=pack/'models/volcano-remake-fidelity-v24';mod.mkdir(exist_ok=True);native=w/'native';native.mkdir(exist_ok=True)
a=json.loads((r/'fidelity-v23/asset-registration.json').read_text());p=json.loads((w/'atmosphere-changes.json').read_text());assert(w/'preservation-verification.json').is_file()
bpy.ops.wm.open_mainfile(filepath=a['finalBlend']);bpy.context.preferences.filepaths.save_version=0
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
helper=(r/'finalize_fidelity_v9.py').read_text();exec(helper[helper.index('def mesh_from_buffer'):helper.index('updates=a')]);helper=(r/'finalize_fidelity_v15.py').read_text();exec(helper[helper.index('def native_mesh'):helper.index('newrows=[]')])
col=bpy.data.collections['Volcano Remake Asset Prototypes'];inst=bpy.data.collections['Volcano Remake Shared Instances'];mat=bpy.data.materials['VRV16_GrassLipVertexColor'];rows=[];changed=[]
for q in p['smoke']:
    path=w/'candidate'/q['model'];stem=Path(q['model']).stem;proto=bpy.data.objects.new('VRV24_Cloud_'+stem,native_mesh('VRV24_Mesh_'+stem,parse(path)['buffers'][0],[mat]));col.objects.link(proto);proto.hide_set(True);proto.hide_render=True
    proto['asset_id']='volcano-fidelity-v24-cloud-'+stem.lower();proto['source_model']=str(path);proto['source_buffer']=0
    row={'id':proto['asset_id'],'name':proto.name,'sourceModel':str(path),'sourceBuffer':0,'triangles':q['triangles'],'materials':[mat.name],'sourcePoolObjectId':q['sourcePoolObjectId'],'role':'Source smoke geometry, normals, indices, local bounds and placement retained. Vertex colors provide warm undersides and cooler gray tops, using the existing plain vertex-color material without texture pixels.'};rows.append(row)
    oldrow=next(x for x in a['objects']if x['id']==q['sourcePoolObjectId']);a['objects'].remove(oldrow)
    for o in bpy.data.objects:
        if o.type=='MESH'and o.name!=proto.name and not o.hide_render and Path(o.get('source_model','')).name==q['model']:
            o.data=proto.data;o['source_model']=str(path);o['source_prototype']=proto.name;o['asset_id']=proto['asset_id'];changed.append(o.name)
    shutil.copy2(path,mod/path.name)
assert len(changed)==3
torchfile=Path(p['existingTorchPack'])/'Fluxara Bronze Wall Torch.blend';materialnames=['gfxGlow_yellow_a','gfx_distord_AlphaTested','fluxara_drifttex_animatedFire_a','fluxara_torch_bronze']
assert all(not bpy.data.materials.get(name)for name in materialnames)
with bpy.data.libraries.load(str(torchfile),link=False)as(src,dest):dest.materials=materialnames
materialnames=[m.name for m in dest.materials]
reused=[]
for m in dest.materials:
    textures=sorted({Path(n.image.filepath).name for n in m.node_tree.nodes if n.type=='TEX_IMAGE'and n.image})
    reused.append({'id':'volcano-fidelity-v24-reused-torch-material-'+hashlib.sha256(m.name.encode()).hexdigest()[:12],'name':m.name,'textures':textures,'reuseTier':'direct','sourcePoolMaterialGroupId':'shared-bronze-wall-torch-materials-v1','adaptation':'Existing pooled torch material, copied into target native project without authoring new material or pixels.'})
torchpath=Path(p['existingTorchLibrary'])/'fluxara_driftlib_aztekTorch_a_main.spm';td=parse(torchpath);merged={'vertices':[],'indices':[],'material':0};ranges=[]
for b in td['buffers']:
    offset=len(merged['vertices']);start=len(merged['indices'])//3;merged['vertices']+=b['vertices'];merged['indices'] +=[offset+i for i in b['indices']];ranges.append((start,len(merged['indices'])//3,b['material']))
assert not bpy.data.objects.get('Fluxara_Bronze_Wall_Torch')
proto=bpy.data.objects.new('Fluxara_Bronze_Wall_Torch',native_mesh('VRV24_ReusedBronzeTorchMesh',merged,[bpy.data.materials[name]for name in materialnames]));col.objects.link(proto);proto.hide_set(True);proto.hide_render=True
for start,end,slot in ranges:
    for face in proto.data.polygons[start:end]:face.material_index=slot
proto['asset_id']=p['torchPoolObjectId'];proto['source_model']=str(torchpath)
torchrow={'id':p['torchPoolObjectId'],'name':proto.name,'sourceModel':str(torchpath),'sourceBuffers':[0,1,2,3],'triangles':218,'materials':materialnames,'role':'Direct reuse of the existing bronze torch runtime geometry and pooled materials, no source changes.'}
for q in p['newTorchPlacements']:
    o=bpy.data.objects.new(q['id'],proto.data);inst.objects.link(o);o['asset_id']=p['torchPoolObjectId'];o['source_model']=str(torchpath);o['source_prototype']=proto.name
    # GameXYZ -> BlenderXZY, yaw uses the same conversion as all prior libraries.
    xyz=q['xyz'];size=q['scale'];o.matrix_world=Matrix.Translation((xyz[0],xyz[2],xyz[1]))@Euler((0,0,-3.141592653589793),'XZY').to_matrix().to_4x4()@Matrix.Diagonal((size[0],size[2],size[1],1))
    xml=E.parse(w/'candidate/scene.xml').getroot().find(f'library[@id="{q["id"]}"]');o['source_xml']=E.tostring(xml,encoding='unicode')
    a['nativeSharedInstances'].append({'name':o.name,'prototype':proto.name,'library':Path(p['existingTorchLibrary']).name,'matrix':[list(v)for v in o.matrix_world],'sourcePlacementId':q['id']})
a['objects']+=rows+[torchrow];a['materials']+=reused;a['newPrototypes']=rows;a['reusedPrototypes']=[torchrow];a['newMaterialVariants']=[];a['reusedMaterialVariants']=reused;a['changedSmokeNativeObjects']=changed
a['runtimeLibrarySources'][Path(p['existingTorchLibrary']).name]=p['existingTorchLibrary']
for name in ['node.xml','materials.xml']:
    bpy.data.texts.new('fluxara_driftlib_aztekTorch_a/'+name).write((Path(p['existingTorchLibrary'])/name).read_text())
bpy.data.texts['scene.xml'].clear();bpy.data.texts['scene.xml'].write((w/'candidate/scene.xml').read_text())
a['visualLibrary']=str(mod/'Volcano Remake Warm Smoke Library.blend');bpy.data.libraries.write(a['visualLibrary'],{bpy.data.objects[q['name']]for q in rows},fake_user=True,compress=True)
a.update({'finalBlend':str(native/'Volcano Remake.blend'),'status':'V24 warm vertex-color smoke with source geometry unchanged and six directly reused bronze torches on battlements. Existing stone/course/control geometry and pixels retained; native candidate, not integrated.'})
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=a['finalBlend']);(w/'asset-registration.json').write_text(json.dumps(a,indent=2));print('V24_NATIVE_WARM_SMOKE_AND_REUSED_TORCHES_SAVED',len(a['objects']),len(a['materials']),len(a['nativeSharedInstances']),flush=True)
