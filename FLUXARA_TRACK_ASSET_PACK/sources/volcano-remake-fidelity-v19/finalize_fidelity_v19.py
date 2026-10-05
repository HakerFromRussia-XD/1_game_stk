from pathlib import Path
import bpy, json, sys, shutil
from mathutils import Vector

r = Path(__file__).resolve().parent; w = r/'fidelity-v19'
pack = Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK')
mod = pack/'models/volcano-remake-fidelity-v19'; mod.mkdir(exist_ok=True)
native = w/'native'; native.mkdir(exist_ok=True)
a = json.loads((r/'fidelity-v18/asset-registration.json').read_text())
proof = json.loads((w/'smoke-changes.json').read_text())
bpy.ops.wm.open_mainfile(filepath=a['finalBlend'])
bpy.context.preferences.filepaths.save_version = 0
sys.path.insert(0, str(r.parent/'shared-object-redesign'))
from spm_io import parse
helper = (r/'finalize_fidelity_v9.py').read_text()
exec(helper[helper.index('def mesh_from_buffer'):helper.index('updates=a')])
helper = (r/'finalize_fidelity_v15.py').read_text()
exec(helper[helper.index('def native_mesh'):helper.index('newrows=[]')])
protos = bpy.data.collections['Volcano Remake Asset Prototypes']
newrows, retired, changed = [], [], []
for row in proof['smoke']:
    model = row['model']
    oldrow = next(q for q in a['objects'] if q['name']=='VRV15_Cloud_'+Path(model).stem)
    oldproto = bpy.data.objects[oldrow['name']]
    oldmesh = oldproto.data
    source = w/'candidate'/model
    d = parse(source)
    name = 'VRV19_Cloud_'+Path(model).stem
    mesh = native_mesh(name+'Mesh', d['buffers'][0], list(oldmesh.materials))
    proto = bpy.data.objects.new(name, mesh); protos.objects.link(proto)
    proto.hide_set(True); proto.hide_render=True
    proto['asset_id'] = 'volcano-fidelity-v19-cloud-'+Path(model).stem.lower()
    proto['source_model'] = str(source)
    for o in list(bpy.data.objects):
        if o.type=='MESH' and o!=oldproto and o.data==oldmesh:
            o.data=mesh; o['source_model']=str(source); changed.append(o.name)
    newrows.append({'id':proto['asset_id'],'name':name,'sourceModel':str(source),'sourceBuffer':0,
                    'triangles':row['triangles'],'materials':[m.name for m in mesh.materials],
                    'sourcePoolObjectId':oldrow['id'],
                    'role':'Continuous closed union of irregular overlapping billows. Original local box, origin, axes and placement retained; existing smoke palette pixels/material reused.'})
    retired.append(oldrow['name']); bpy.data.objects.remove(oldproto,do_unlink=True)
    shutil.copy2(source,mod/model)
a['objects']=[q for q in a['objects'] if q['name'] not in retired]+newrows
for name in ['scene.xml','materials.xml']:
    bpy.data.texts[name].clear(); bpy.data.texts[name].write((w/'candidate'/name).read_text())
a['newPrototypes']=newrows; a['newMaterialVariants']=[]
a['retiredPrototypeNames']=retired; a['smokeChangedNativeObjectNames']=changed
a['visualLibrary']=str(mod/'Volcano Remake Billowing Smoke Library.blend')
bpy.data.libraries.write(a['visualLibrary'],{bpy.data.objects[q['name']] for q in newrows},fake_user=True,compress=True)
a.update({'finalBlend':str(native/'Volcano Remake.blend'),
          'status':'V19 continuous overlapping smoke billows; unchanged source boxes, origins, axes, ghost transforms, existing smoke palette and all other V18 geometry. Isolated candidate; visual reference work remains.'})
bpy.ops.file.pack_all(); bpy.ops.wm.save_as_mainfile(filepath=a['finalBlend'])
(w/'asset-registration.json').write_text(json.dumps(a,indent=2))
print('V19_NATIVE_CONTINUOUS_SMOKE_SAVED',len(a['objects']),len(a['materials']),len(a['nativeSharedInstances']),changed,flush=True)
