from pathlib import Path
import bpy,json,math,xml.etree.ElementTree as E
from mathutils import Matrix,Vector
r=Path(__file__).resolve().parent;w=r/'fidelity-v28';native=w/'native';native.mkdir(exist_ok=True)
a=json.loads((r/'fidelity-v27/asset-registration.json').read_text());p=json.loads((w/'visible-cliff-changes.json').read_text());assert (w/'preservation-verification.json').is_file()
bpy.ops.wm.open_mainfile(filepath=a['finalBlend']);bpy.context.preferences.filepaths.save_version=0;scene=E.parse(w/'candidate/scene.xml').getroot();changed=[]
for group in p['changedGroups']:
    for attrs,proto in zip(group['after'],['VRV22_Prototype_GrassLip','VRV22_Prototype_StoneBody']):
        row=next(v for v in a['nativeSharedInstances']if v.get('sourcePlacementId')==attrs['id']and v['prototype']==proto)
        obj=bpy.data.objects[row['name']];e=scene.find(f'library[@id="{attrs["id"]}"]');xyz=list(map(float,e.get('xyz').split()));s=list(map(float,e.get('scale').split()));yaw=math.radians(float(e.get('hpr').split()[1]))
        obj.matrix_world=Matrix.Translation(Vector((xyz[0],xyz[2],xyz[1])))@Matrix.Rotation(-yaw,4,'Z')@Matrix.Diagonal((s[0],s[2],s[1],1))
        obj['source_xml']=E.tostring(e,encoding='unicode');row=next(v for v in a['nativeSharedInstances']if v['name']==obj.name);row['matrix']=[list(v)for v in obj.matrix_world];changed.append(obj.name)
bpy.data.texts['scene.xml'].clear();bpy.data.texts['scene.xml'].write((w/'candidate/scene.xml').read_text())
a.update({'finalBlend':str(native/'Volcano Remake.blend'),'changedVisibleCliffNativeObjectNames':changed,'status':'V28 repositions copied grass/stone groups toward outer faces of original cliffs. Exact source geometry, dimensions, pixels retained; only previously added instance coordinates changed. V26 rounded support and V27 tall parts retained. Isolated candidate; whole reference fidelity/integration unfinished.'})
bpy.ops.wm.save_as_mainfile(filepath=a['finalBlend']);(w/'asset-registration.json').write_text(json.dumps(a,indent=2));print('V28_NATIVE_VISIBLE_CLIFF_POSES_SAVED',len(changed),flush=True)
