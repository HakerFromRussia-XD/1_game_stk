from pathlib import Path
import bpy,json,sys
r=Path(__file__).resolve().parent
work=r/'fidelity-v3'
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
mesh=bpy.data.meshes.new('VRV3_StonePortal')
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
material=next(m for m in bpy.data.materials if m.name.startswith('VRV3_') and 'vr_arch_stone' in m.name)
mesh.materials.append(material)
portal=bpy.data.objects.new('VRV3_StonePortal',mesh)
portal.hide_render=True
collection=bpy.data.collections['Volcano Remake Asset Prototypes']
collection.objects.link(portal)
bpy.context.view_layer.update()
portal.hide_set(True)
portal['asset_id']='volcano-fidelity-v3-stone-portal'
portal['source_model']=str(work/'candidate/volcano_track.spm')
portal['source_component']='Replacement of the original 294-triangle decorative entrance; inherited world origin and axes.'
reg['objects'].append({'id':portal['asset_id'],'name':portal.name,'sourceModel':portal['source_model'],
    'triangles':300,'materials':[material.name],'role':'Authored decorative stone entrance; currently a candidate.'})
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=reg['finalBlend'])
reg['status']='Candidate only; production track and approved sources not replaced.'
reg_path.write_text(json.dumps(reg,indent=2))
bpy.data.libraries.write(reg['visualLibrary'],set(collection.objects)|set(bpy.data.materials),fake_user=True)
print('FIDELITY_NATIVE_CANDIDATE_READY',work/'native/Volcano Remake.blend',flush=True)
