from pathlib import Path
import bpy,json,sys,math,hashlib,collections
from mathutils import Vector
r=Path(__file__).resolve().parent;w=r/'fidelity-v17';pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK');mod=pack/'models/volcano-remake-fidelity-v17';mod.mkdir(exist_ok=True);native=w/'native';native.mkdir(exist_ok=True);a=json.loads((r/'fidelity-v16/asset-registration.json').read_text());p=json.loads((w/'green-crest-changes.json').read_text());bpy.ops.wm.open_mainfile(filepath=a['finalBlend']);bpy.context.preferences.filepaths.save_version=0;sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
helper=(r/'finalize_fidelity_v9.py').read_text();exec(helper[helper.index('def mesh_from_buffer'):helper.index('updates=a')]);helper=(r/'finalize_fidelity_v15.py').read_text();exec(helper[helper.index('def native_mesh'):helper.index('newrows=[]')]);main=parse(w/'candidate/volcano_track.spm');green=bpy.data.materials['VRV4E_vr_moss_palette.jpg'];stone=bpy.data.materials['VRV4E_Rock13_col.jpg'];cap=main['buffers'][3]
def key(points):return tuple(sorted(tuple(round(v,5)for v in xyz)for xyz in points))
caps=collections.Counter(key([(cap['vertices'][j]['position'][0],cap['vertices'][j]['position'][2],cap['vertices'][j]['position'][1])for j in cap['indices'][i:i+3]])for i in range(0,len(cap['indices']),3));obj=bpy.data.objects['VR_OriginalSurface_011'];mesh=obj.data;assert len(mesh.polygons)==604;assert mesh.materials[1]==stone;mesh.materials.append(green);changed=[]
for face in mesh.polygons:
 k=key([mesh.vertices[j].co for j in face.vertices])
 if caps[k]:
  assert face.material_index==1;face.material_index=2;changed.append(face.index)
  for loopid in face.loop_indices:mesh.uv_layers.active.data[loopid].uv=(.75,.5)
  caps[k]-=1
assert len(changed)==8 and sum(caps.values())==0
new=[];protos=[]
for bi,label,mat in [(2,'CentralStoneSupport',stone),(3,'CentralGreenCrest',green)]:
 m=native_mesh('VRV17_'+label+'Mesh',main['buffers'][bi],[mat]);o=bpy.data.objects.new('VRV17_Prototype_'+label,m);bpy.data.collections['Volcano Remake Asset Prototypes'].objects.link(o);o.hide_set(True);o.hide_render=True;o['asset_id']='volcano-fidelity-v17-'+label.lower();o['source_model']=str(w/'candidate/volcano_track.spm');o['source_buffer']=bi;new.append({'id':o['asset_id'],'name':o.name,'sourceModel':o['source_model'],'sourceBuffer':bi,'triangles':len(m.polygons),'materials':[mat.name],'sourcePoolObjectId':p['sourcePoolObjectId'],'role':'Original central rounded cliff support split into retained stone side and upper eight triangles using existing green terrain image. Positions, normals, colors, bounds, axes, physics and placement unchanged; stone UVs retained, green crest uses existing palette green cell.'});protos.append(o)
a['objects']=[q for q in a['objects']if q['id']!='volcano-fidelity-v14-central-rock']+new;a['newPrototypes']=new;a['newMaterialVariants']=[];a['visualLibrary']=str(mod/'Volcano Remake Green Crest Library.blend');bpy.data.libraries.write(a['visualLibrary'],set(protos),fake_user=True,compress=True);(mod/'volcano_track.spm').write_bytes((w/'candidate/volcano_track.spm').read_bytes())
for o in bpy.data.objects:
 if o.get('source_model')and 'fidelity-v16/candidate'in o['source_model']:o['source_model']=o['source_model'].replace('fidelity-v16/candidate','fidelity-v17/candidate')
bpy.data.objects['VRV14_Prototype_CentralRock']['source_model']=str(r/'fidelity-v14/candidate/volcano_track.spm')
a.update({'finalBlend':str(native/'Volcano Remake.blend'),'centralSupportCrestChangedMeshObjects':[obj.name],'changedNativeFaceIndices':changed,'status':'V17 original central rounded support retained; eight upper faces use existing moss material. All geometry, stone UVs, normals, physics, axes, bounds and placements unchanged. Only eight crest faces use existing palette green UV cell. No new textures. Isolated candidate.'});bpy.ops.wm.save_as_mainfile(filepath=a['finalBlend']);(w/'asset-registration.json').write_text(json.dumps(a,indent=2));print('V17_NATIVE_GREEN_CREST_SAVED',len(a['objects']),len(a['materials']),len(changed),flush=True)
