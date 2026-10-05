from pathlib import Path
import bpy,copy,hashlib,json,sys
from mathutils import Vector
r=Path(__file__).resolve().parent;w=r/'fidelity-v41';native=w/'native';native.mkdir(exist_ok=True)
assert(w/'preservation-verification.json').is_file()
a=json.loads((r/'fidelity-v40/asset-registration.json').read_text());p=json.loads((w/'barrier-smoke-preflight.json').read_text())
bpy.ops.wm.open_mainfile(filepath=a['finalBlend']);bpy.context.preferences.filepaths.save_version=0
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
s=(r/'finalize_fidelity_v9.py').read_text();exec(s[s.index('def mesh_from_buffer'):s.index('updates=a')])
s=(r/'finalize_fidelity_v15.py').read_text();exec(s[s.index('def native_mesh'):s.index('newrows=[]')])
def geometry(o,colors=True):
 m=o.data;return (tuple(tuple(v.co)for v in m.vertices),tuple(tuple(q.vertices)for q in m.polygons),tuple((l.name,tuple(tuple(v.uv)for v in l.data))for l in m.uv_layers),tuple(tuple(v.vector)for v in m.corner_normals),tuple((c.name,c.data_type,c.domain,tuple(tuple(v.color)for v in c.data))for c in m.color_attributes)if colors else (),tuple(x.name if x else None for x in m.materials),tuple(q.material_index for q in m.polygons))
snapshot={o.name:geometry(o)for o in bpy.data.objects if o.type=='MESH'};poses={name:tuple(tuple(v)for v in bpy.data.objects[name].matrix_world)for name in snapshot}
wallbuf=parse(w/'candidate/volcano_track.spm')['buffers'][5]
walls=[o for o in bpy.data.objects if o.type=='MESH'and len(o.data.polygons)==7260 and len(o.data.vertices)==11187 and any(m and 'BrickAlias'in m.name for m in o.data.materials)]
assert len(walls)==1,[(o.name,[m.name for m in o.data.materials])for o in walls]
wall=walls[0];wallbase=geometry(wall,False);wall.data=wall.data.copy();wall.data.name='VRV41_RoadsideBrickColors'
values=[]
for loop in wall.data.loops:values.extend([q/255 for q in wallbuf['vertices'][loop.vertex_index]['color']]+[1])
wall.data.color_attributes['Color'].data.foreach_set('color',values)
assert geometry(wall,False)==wallbase
wall['source_model']=str(w/'candidate/volcano_track.spm');changed=[wall.name]
alias=Path(p['paletteAlias']['path']);image=bpy.data.images.load(str(alias),check_existing=False);image.name=alias.name;image.pack()
mat=bpy.data.materials.new('VRV41_VolcanicSmokeUnlit');mat.use_nodes=True;mat['asset_id']='volcano-fidelity-v41-smoke-material';nt=mat.node_tree;nt.nodes.clear()
out=nt.nodes.new('ShaderNodeOutputMaterial');emit=nt.nodes.new('ShaderNodeEmission');tex=nt.nodes.new('ShaderNodeTexImage');tex.image=image;col=nt.nodes.new('ShaderNodeVertexColor');col.layer_name='Color';mul=nt.nodes.new('ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=1
nt.links.new(tex.outputs['Color'],mul.inputs[1]);nt.links.new(col.outputs['Color'],mul.inputs[2]);nt.links.new(mul.outputs[0],emit.inputs['Color']);nt.links.new(emit.outputs[0],out.inputs['Surface']);emit.inputs['Strength'].default_value=1
matrow={'id':mat['asset_id'],'name':mat.name,'textures':[alias.name],'adaptation':'Opaque reused Orbital palette cell multiplied by baked vertex lighting; scoped emission matches runtime unlit smoke material. Source geometry and donor assets unchanged.','sourcePoolTextureId':p['palettePoolId']}
rows=[];proto_col=bpy.data.collections['Volcano Remake Asset Prototypes']
for q in p['smoke']:
 stem=Path(q['model']).stem;oldrow=next(x for x in a['objects']if x['name']=='VRV24_Cloud_'+stem);oldproto=bpy.data.objects[oldrow['name']];path=w/'candidate'/q['model'];buf=parse(path)['buffers'][0]
 proto=bpy.data.objects.new('VRV41_Cloud_'+stem,native_mesh('VRV41_Mesh_'+stem,buf,[mat]));proto_col.objects.link(proto);proto.hide_set(True);proto.hide_render=True;proto['asset_id']='volcano-fidelity-v41-cloud-'+stem.lower();proto['source_model']=str(path)
 users=[o for o in bpy.data.objects if o.type=='MESH'and o!=oldproto and o.data==oldproto.data];assert len(users)==1,(stem,[o.name for o in users])
 for o in users:
  o.data=proto.data;o['source_model']=str(path);o['source_prototype']=proto.name;o['asset_id']=proto['asset_id'];changed.append(o.name)
 rows.append({'id':proto['asset_id'],'name':proto.name,'sourceModel':str(path),'sourceBuffer':0,'triangles':len(buf['indices'])//3,'materials':[mat.name],'sourcePoolObjectId':oldrow['id'],'role':'Existing smoke mesh with warm underside and baked lighting; exact local geometry, origin, axes and world transforms.'})
a['objects']+=rows;a['materials'].append(matrow);a['newPrototypes']=rows;a['newMaterialVariants']=[matrow];a['changedNativeGeometry']=changed;a['changedNativeMatrices']=[]
assert len(changed)==4
for name,g in snapshot.items():
 if name not in changed:assert geometry(bpy.data.objects[name])==g,name
 assert tuple(tuple(v)for v in bpy.data.objects[name].matrix_world)==poses[name],name
for name in ['scene.xml','materials.xml']:bpy.data.texts[name].clear();bpy.data.texts[name].write((w/'candidate'/name).read_text())
a['textures'][alias.name]={'source':str(alias),'packPath':str(alias),'bytes':alias.stat().st_size,'sha256':hashlib.sha256(alias.read_bytes()).hexdigest(),'poolId':'volcano-fidelity-v41-smoke-palette-alias','reusedPixelsPoolId':p['palettePoolId'],'reusedPixelsSource':p['paletteSource']['path']}
a['visualLibrary']=str(native/'Volcano Remake Smoke Variant.blend');bpy.data.libraries.write(a['visualLibrary'],{bpy.data.objects[q['name']]for q in rows}|{mat},fake_user=True,compress=True)
a['finalBlend']=str(native/'Volcano Remake.blend');a['status']='V41 working draft. Stone texture retained; 128 existing low roadside blocks colored red/white. Three source smoke meshes use scoped baked lighting and exact reused palette pixels. Road, collision, controls, geometry and all previous world matrices retained. Production integration and reference acceptance pending.'
stone=next(n.image for n in bpy.data.materials['VRV4E_Rock13_col.jpg'].node_tree.nodes if n.type=='TEX_IMAGE');assert hashlib.sha256(stone.packed_file.data).hexdigest()=='6c765884a7846501355a429f3548d2df78698798a97a0318aefe358d0bdafdfd'
wallname=wall.name;imagename=image.name
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=a['finalBlend']);(w/'asset-registration.json').write_text(json.dumps(a,indent=2));bpy.ops.wm.open_mainfile(filepath=a['finalBlend'])
for name,g in snapshot.items():
 if name not in changed:assert geometry(bpy.data.objects[name])==g,name
 assert tuple(tuple(v)for v in bpy.data.objects[name].matrix_world)==poses[name],name
assert geometry(bpy.data.objects[wallname],False)==wallbase
for q in a['nativeSharedInstances']:assert bpy.data.objects[q['name']].data==bpy.data.objects[q['prototype']].data,q['name']
for q in rows:
 o=bpy.data.objects[q['name']];o.data.calc_loop_triangles();assert len(o.data.loop_triangles)==q['triangles'];assert [m.name for m in o.data.materials]==q['materials'];assert sum(z.type=='MESH'and z!=o and z.data==o.data for z in bpy.data.objects)==1
proof={'finalBlendOpens':True,'allPreviousNativeObjectsRetained':len(snapshot),'allOtherNativeMeshGeometryUVNormalsColorsMaterialsExactV40':len(snapshot)-len(changed),'allPreviousNativeMatricesExactV40':len(poses),'changedExistingSharedMatrices':0,'changedNativeMeshUsers':changed,'newSourcePrototypes':rows,'meshObjects':sum(o.type=='MESH'for o in bpy.data.objects),'nativePrototypeCount':len(a['objects']),'nativeMaterialDefinitionCount':len(a['materials']),'nativeSharedParts':len(a['nativeSharedInstances']),'roadsideWallOnlyColorsChanged':True,'sharedMeshPointersExactAfterReopen':True,'stonePackedPixelsExact':True,'smokePalettePackedPixelsExact':hashlib.sha256(bpy.data.images[imagename].packed_file.data).hexdigest()==hashlib.sha256(alias.read_bytes()).hexdigest(),'canonicalPending':True,'newMaterials':1,'newRasterPixels':False,'runtimeAndReferenceAcceptanceSeparate':True}
(w/'final-blend-verification.json').write_text(json.dumps(proof,indent=2));print('V41_NATIVE_REOPEN_STONE_SMOKE_AND_MATRICES_VERIFIED',proof,flush=True)
