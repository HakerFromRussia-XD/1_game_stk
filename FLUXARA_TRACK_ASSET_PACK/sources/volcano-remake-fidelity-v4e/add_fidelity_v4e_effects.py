from pathlib import Path
import bpy,json,sys
r=Path(__file__).resolve().parent
work=r/'fidelity-v4e'
reg_path=work/'asset-registration.json'
reg=json.loads(reg_path.read_text())
bpy.ops.wm.open_mainfile(filepath=reg['finalBlend'])
sys.path.insert(0,str(r.parent/'shared-object-redesign'))
from spm_io import parse
d=parse(work/'candidate/volcano_track.spm')
b=d['buffers'][1]
indices=b['indices'][-900:]
used=sorted(set(indices))
mapping={old:new for new,old in enumerate(used)}
vertices=[b['vertices'][i] for i in used]
faces=[tuple(mapping[i] for i in reversed(indices[t:t+3])) for t in range(0,len(indices),3)]
mesh=bpy.data.meshes.new('VRV4E_StonePortal')
mesh.from_pydata([(v['position'][0],v['position'][2],v['position'][1]) for v in vertices],[],faces)
mesh.uv_layers.new(name='UVMap')
mesh.color_attributes.new(name='Color',type='BYTE_COLOR',domain='CORNER')
uv=mesh.uv_layers['UVMap']
colors=mesh.color_attributes['Color']
for polygon in mesh.polygons:
    for loop in polygon.loop_indices:
        v=vertices[mesh.loops[loop].vertex_index]
        uv.data[loop].uv=v['uv']
        colors.data[loop].color_srgb=tuple(x/255 for x in v['color'])+(1,)
material=next(m for m in bpy.data.materials if m.name.startswith('VRV4E_') and 'vr_arch_stone' in m.name)
mesh.materials.append(material)
portal=bpy.data.objects.new('VRV4E_StonePortal',mesh)
portal.hide_render=True
collection=bpy.data.collections['Volcano Remake Asset Prototypes']
collection.objects.link(portal)
bpy.context.view_layer.update()
portal.hide_set(True)
portal['asset_id']='volcano-fidelity-v4e-stone-portal'
portal['source_model']=str(work/'candidate/volcano_track.spm')
portal['source_component']='Replacement of the original 294-triangle decorative entrance; inherited world origin and axes.'
reg['objects'].append({'id':portal['asset_id'],'name':portal.name,'sourceModel':portal['source_model'],
    'triangles':300,'materials':[material.name],'role':'Authored decorative stone entrance; currently a candidate.'})
# Original card meshes are reusable effects, distinct from the protected route.
for name in ['AshCloud2.spm','AshCloudEffect.spm','AshColumnEffect.spm','EruptionAsh.spm','PyroclasticFlowAsh.spm']:
    parsed=parse(work/'candidate'/name)
    allvertices=[];allfaces=[];face_materials=[];slot_names=[]
    for buffer in parsed['buffers']:
        texture=parsed['materials'][buffer['material']][0]
        matname=next(q['name'] for q in reg['materials'] if texture in q['textures'])
        if matname not in slot_names:slot_names.append(matname)
        offset=len(allvertices);allvertices.extend(buffer['vertices'])
        allfaces.extend(tuple(offset+i for i in reversed(buffer['indices'][t:t+3])) for t in range(0,len(buffer['indices']),3))
        face_materials.extend([slot_names.index(matname)]*(len(buffer['indices'])//3))
    effect_mesh=bpy.data.meshes.new('VRV4E_'+Path(name).stem+'_FullCards')
    effect_mesh.from_pydata([(v['position'][0],v['position'][2],v['position'][1]) for v in allvertices],[],allfaces)
    effect_mesh.uv_layers.new(name='UVMap');effect_mesh.color_attributes.new(name='Color',type='BYTE_COLOR',domain='CORNER')
    for matname in slot_names:effect_mesh.materials.append(bpy.data.materials[matname])
    for polygon,mi in zip(effect_mesh.polygons,face_materials):
        polygon.material_index=mi
        for loop in polygon.loop_indices:
            v=allvertices[effect_mesh.loops[loop].vertex_index]
            effect_mesh.uv_layers['UVMap'].data[loop].uv=v['uv']
            effect_mesh.color_attributes['Color'].data[loop].color_srgb=tuple(x/255 for x in v['color'])+(1,)
    # Preserve both sides explicitly: the generic importer removed coincident back faces.
    for original in list(bpy.data.objects):
        if original.type=='MESH' and original.get('source_model')==str(work/'candidate'/name):
            previous=original.data
            for linked in list(bpy.data.objects):
                if linked.type=='MESH' and linked.data==previous:linked.data=effect_mesh
    obj=bpy.data.objects.new('VRV4E_Effect_'+Path(name).stem,effect_mesh)
    collection.objects.link(obj)
    obj.hide_render=True;obj.hide_set(True)
    obj['asset_id']='volcano-fidelity-v4e-effect-'+Path(name).stem.lower()
    obj['source_model']=str(work/'candidate'/name)
    obj.data.calc_loop_triangles()
    reg['objects'].append({'id':obj['asset_id'],'name':obj.name,'sourceModel':obj['source_model'],'triangles':len(obj.data.loop_triangles),'materials':[m.name for m in obj.data.materials],'role':'Authored overlapping smoke billow cards; original bounds and triangle budget retained, full-sprite UVs.'})
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=reg['finalBlend'])
reg['status']='Candidate only; production track and approved sources not replaced.'
reg_path.write_text(json.dumps(reg,indent=2))
bpy.data.libraries.write(reg['visualLibrary'],set(collection.objects)|set(bpy.data.materials),fake_user=True)
print('FIDELITY_NATIVE_CANDIDATE_READY',work/'native/Volcano Remake.blend',flush=True)
