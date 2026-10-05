from pathlib import Path
import bpy,json,math,shutil,xml.etree.ElementTree as E
from mathutils import Matrix,Vector
r=Path(__file__).resolve().parent;w=r/'fidelity-v27';pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK')
mod=pack/'models/volcano-remake-fidelity-v27';mod.mkdir(exist_ok=True);native=w/'native';native.mkdir(exist_ok=True)
a=json.loads((r/'fidelity-v26/asset-registration.json').read_text());p=json.loads((w/'column-changes.json').read_text())
assert json.loads((r/'fidelity-v26/final-blend-verification.json').read_text())['sourceCentralStone64ColliderFacesExactV24']
assert (w/'preservation-verification.json').is_file()
bpy.ops.wm.open_mainfile(filepath=a['finalBlend']);bpy.context.preferences.filepaths.save_version=0
scene=E.parse(w/'candidate/scene.xml').getroot();parts={q['part']:q for q in p['parts']};changed=[]
for q in p['placements']:
    for role,part,proto in [('grass','grass_cap','VRV22_Prototype_GrassLip'),('stone','stone_column','VRV22_Prototype_StoneBody')]:
        row=next(v for v in a['nativeSharedInstances']if v.get('sourcePlacementId')==q['source']['id']and v['prototype']==proto)
        obj=bpy.data.objects[row['name']];xml=scene.find(f'library[@id="{q[role]["id"]}"]')
        e=q[role];xyz=list(map(float,e['xyz'].split()));s=list(map(float,e['scale'].split()));yaw=math.radians(float(e['hpr'].split()[1]))
        matrix=Matrix.Translation(Vector((xyz[0],xyz[2],xyz[1])))@Matrix.Rotation(-yaw,4,'Z')@Matrix.Diagonal((s[0],s[2],s[1],1))
        if role=='grass':assert max(abs(matrix[i][j]-obj.matrix_world[i][j])for i in range(4)for j in range(4))<.002
        else:changed.append(obj.name)
        obj.matrix_world=matrix;obj['source_xml']=E.tostring(xml,encoding='unicode');obj['source_model']=parts[part]['model'];obj['source_buffer']=0;obj['shared_runtime_library']=xml.get('name')
        row=next(v for v in a['nativeSharedInstances']if v['name']==obj.name);row.update({'library':xml.get('name'),'matrix':[list(v)for v in matrix],'sourcePlacementId':xml.get('id')})
for q in p['parts']:
    name=Path(q['library']).name;a['runtimeLibrarySources'][name]=q['library']
    for filename in ['node.xml','materials.xml']:bpy.data.texts.new(name+'/'+filename).write((Path(q['library'])/filename).read_text())
    for source in Path(q['library']).iterdir():
        if source.is_file():shutil.copy2(source,mod/source.name)
bpy.data.texts['scene.xml'].clear();bpy.data.texts['scene.xml'].write((w/'candidate/scene.xml').read_text())
a['newPrototypes']=[];a['newMaterialVariants']=[];a['reusedMaterialVariants']=[]
a['reusedPrototypes']=[{'id':'volcano-fidelity-v22-'+('grasslip'if q['part']=='grass_cap'else'stonebody'),
    'name':q['nativePrototype'],'sourceModel':q['model'],'sourceBuffer':0,'triangles':q['triangles'],
    'materials':[m.name for m in bpy.data.objects[q['nativePrototype']].data.materials],'role':'Exact pooled component geometry, normal, UV, color and local bounds reused. Split runtime export; coordinates only change stone instance height.'}for q in p['parts']]
a['changedStoneColumnNativeObjects']=changed;a['tallColumnNativeParts']=116
a['visualLibrary']=str(mod/'Volcano Remake Tall Stone Columns Library.blend')
bpy.data.libraries.write(a['visualLibrary'],{bpy.data.objects[q['nativePrototype']]for q in p['parts']},fake_user=True,compress=True)
a.update({'finalBlend':str(native/'Volcano Remake.blend'),'status':'V27 directly reuses grass/stone component geometry with58 taller stone coordinate placements and preserved grass poses. V26 central support retained; rejected V25 excluded. Native candidate; overall reference match and integration unfinished.'})
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=a['finalBlend']);(w/'asset-registration.json').write_text(json.dumps(a,indent=2))
print('V27_NATIVE_COORDINATE_COLUMNS_SAVED',len(a['objects']),len(a['materials']),len(a['nativeSharedInstances']),flush=True)
