from pathlib import Path
import bpy,json,sys,math,shutil,xml.etree.ElementTree as E
from mathutils import Matrix,Euler,Vector
r=Path(__file__).resolve().parent;w=r/'fidelity-v22';pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK');mod=pack/'models/volcano-remake-fidelity-v22';mod.mkdir(exist_ok=True);native=w/'native';native.mkdir(exist_ok=True)
a=json.loads((r/'fidelity-v21/asset-registration.json').read_text());proof=json.loads((w/'cliff-changes.json').read_text());assert (w/'preservation-verification.json').is_file();bpy.ops.wm.open_mainfile(filepath=a['finalBlend']);bpy.context.preferences.filepaths.save_version=0
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
helper=(r/'finalize_fidelity_v9.py').read_text();exec(helper[helper.index('def mesh_from_buffer'):helper.index('updates=a')]);helper=(r/'finalize_fidelity_v15.py').read_text();exec(helper[helper.index('def native_mesh'):helper.index('newrows=[]')])
d=parse(proof['newSharedCliffModel']);new=[];protos={};old_names=['VRV16_Prototype_GrassLip','VRV16_Prototype_StoneBody']
for bi,(label,matname)in enumerate([('GrassLip','VRV16_GrassLipVertexColor'),('StoneBody','VRV4E_Rock13_col.jpg')]):
    mat=bpy.data.materials[matname];mesh=native_mesh('VRV22_'+label+'Mesh',d['buffers'][bi],[mat]);o=bpy.data.objects.new('VRV22_Prototype_'+label,mesh);bpy.data.collections['Volcano Remake Asset Prototypes'].objects.link(o);o.hide_set(True);o.hide_render=True;o['asset_id']='volcano-fidelity-v22-'+label.lower();o['source_model']=proof['newSharedCliffModel'];o['source_buffer']=bi;protos[old_names[bi]]=o
    new.append({'id':o['asset_id'],'name':o.name,'sourceModel':proof['newSharedCliffModel'],'sourceBuffer':bi,'triangles':len(mesh.polygons),'materials':[matname],'sourcePoolObjectId':proof['sourcePoolObjectIds'][bi],
                'role':'Copied V16 grass/stone cliff with irregular inward contour and rounder green profile. Whole source model local bounds/origin/axes retained; stone UVs, colors and pixels unchanged. Applied to 58 new decorative instances with wider/shorter proportions and fixed top heights.'})
scene=E.parse(w/'candidate/scene.xml').getroot();changed=[]
for row in a['nativeSharedInstances']:
    if row['prototype']not in protos:continue
    obj=bpy.data.objects[row['name']];proto=protos[row['prototype']];xml=scene.find(f"library[@id='{row['sourcePlacementId']}']");xyz=list(map(float,xml.get('xyz').split()));sc=list(map(float,xml.get('scale').split()));hpr=list(map(float,xml.get('hpr').split()));rot=Euler(tuple(math.radians(-v)for v in [hpr[0],hpr[2],hpr[1]]),'XZY');matrix=Matrix.Translation((xyz[0],xyz[2],xyz[1]))@rot.to_matrix().to_4x4()@Matrix.Diagonal((sc[0],sc[2],sc[1],1))
    obj.data=proto.data;obj.matrix_world=matrix;obj['source_model']=proof['newSharedCliffModel'];obj['source_prototype']=proto.name;obj['asset_id']=proto['asset_id'];obj['shared_runtime_library']=xml.get('name');obj['source_xml']=E.tostring(xml,encoding='unicode');row.update({'prototype':proto.name,'library':xml.get('name'),'matrix':[list(v)for v in matrix]});changed.append(obj.name)
assert len(changed)==116
a['objects']=[q for q in a['objects']if q['name']not in old_names]+new;a['newPrototypes']=new;a['newMaterialVariants']=[];a['changedOrganicCliffNativeObjectNames']=changed;a['retiredActiveCliffPrototypeNames']=old_names
lib=Path(proof['newSharedCliffLibrary']);a['runtimeLibrarySources'][lib.name]=str(lib)
for filename in ['node.xml','materials.xml']:bpy.data.texts.new(lib.name+'/'+filename).write((lib/filename).read_text())
bpy.data.texts['scene.xml'].clear();bpy.data.texts['scene.xml'].write((w/'candidate/scene.xml').read_text());a['visualLibrary']=str(mod/'Volcano Remake Organic Cliffs Library.blend');bpy.data.libraries.write(a['visualLibrary'],set(protos.values()),fake_user=True,compress=True);shutil.copy2(proof['newSharedCliffModel'],mod/Path(proof['newSharedCliffModel']).name)
a.update({'finalBlend':str(native/'Volcano Remake.blend'),'status':'V22 adapts one pooled cliff mesh for 58 decorative coordinate placements: irregular rounded crest and wider/shorter instances. Existing stone UVs and pixels, source model bounds/axes/origin and all V21 road/collision/control data retained. Isolated candidate; reference, lighting and integration unfinished.'});bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=a['finalBlend']);(w/'asset-registration.json').write_text(json.dumps(a,indent=2));print('V22_NATIVE_ORGANIC_CLIFFS_SAVED',len(a['objects']),len(a['materials']),len(a['nativeSharedInstances']),flush=True)
