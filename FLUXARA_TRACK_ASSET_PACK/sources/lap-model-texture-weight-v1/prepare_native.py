from pathlib import Path
import bpy,hashlib,json,shutil,subprocess
r=Path(__file__).resolve().parent;root=r.parents[2];repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK';final=root/'output/fluxara-user-lap-catch-final/Lap Catch.blend';before=r/'before';before.mkdir(exist_ok=True)
if not(before/'Lap Catch.blend').exists():shutil.copy2(final,before/'Lap Catch.blend')
tex=pack/'textures/lap-texture-weight-v1/fluxara_lc_leaf_72.png';tex.parent.mkdir(exist_ok=True);shutil.copy2(r/'new-textures'/tex.name,tex)
bpy.ops.wm.open_mainfile(filepath=str(before/'Lap Catch.blend'));bpy.context.preferences.filepaths.save_version=0
image=bpy.data.images.load(str(tex));image.name='LCW1_Leaf_72';image.pack();materials={};prototypes=[];mapping={};sourceNames=['LC_Prototype_fluxara_driftlib_round_tree_green_v2_main_0','LC_Prototype_fluxara_driftlib_round_tree_green_v2_main_1','LC_Prototype_fluxara_driftlib_round_bush_green_v2_main_0'];collection=bpy.data.collections.new('Lap Catch Lightweight Texture Exports');bpy.context.scene.collection.children.link(collection)
def shape(mesh):return hashlib.sha256(str(([tuple(v.co)for v in mesh.vertices],[tuple(p.vertices)for p in mesh.polygons],[[tuple(x.uv)for x in layer.data]for layer in mesh.uv_layers])).encode()).hexdigest()
for name in sourceNames:
 source=bpy.data.objects[name];o=bpy.data.objects.new('LCW1_'+name,source.data.copy());collection.objects.link(o);o.matrix_world=source.matrix_world.copy();o.hide_set(True);o.hide_render=True;o['source_prototype']=name;o['runtime_library']='fluxara_driftlib_lc_light_bush_v1'if'bush'in name else 'fluxara_driftlib_lc_light_tree_v1';o['texture_export_resolution']='72x72; original source artwork retained';o['asset_id']='lap-weight-v1-proto-'+hashlib.sha256(name.encode()).hexdigest()[:16]
 for i,m in enumerate(o.data.materials):
  if m is None:continue
  if m.name not in materials:
   copy=m.copy();copy.name='LCW1_'+m.name
   if copy.use_nodes:
    for node in copy.node_tree.nodes:
     if node.type=='TEX_IMAGE'and node.image and Path(bpy.path.abspath(node.image.filepath)).name=='fluxara_circuit_leaf_v2.png':node.image=image
   materials[m.name]=copy
  o.data.materials[i]=materials[m.name]
 assert shape(source.data)==shape(o.data);mapping[name]=o;prototypes.append({'id':o['asset_id'],'name':o.name,'sourcePrototype':name,'shapeUVExact':True,'shapeHash':shape(o.data),'runtimeLibrary':o['runtime_library'],'materials':[m.name for m in o.data.materials if m]})
prefixes=('fluxara_driftlib_accacia_a_main_proxy','fluxara_driftlib_agave_a_main_proxy','fluxara_driftlib_autumnSmallBush_a_main_proxy');updated=[]
for o in list(bpy.context.scene.objects):
 if o.type!='MESH' or not o.name.startswith(prefixes):continue
 match=next((src for src in sourceNames if o.data==bpy.data.objects[src].data),None)
 if match is None:continue
 o.data=mapping[match].data;o['source_prototype']=mapping[match].name;o['shared_runtime_library']=mapping[match]['runtime_library'];updated.append({'object':o.name,'prototype':mapping[match].name,'worldMatrix':[list(v)for v in o.matrix_world]})
assert updated
proof={'prototypes':prototypes,'changedNativeParts':len(updated),'placements':updated,'originalObjectTransformsNotEdited':True,'originalGeometryNotEdited':True,'originalHighResolutionLeafImageUnchanged':True,'newModelGeometry':False,'newRuntimeTestsPerformed':False};text=bpy.data.texts.new('LightweightTextureExports.json');text.write(json.dumps(proof,indent=2))
for name,newlib in json.loads((r/'candidate.json').read_text())['wrapperLibraryNamesChangedOnly'].items():
 node=(r/'wrappers'/name/'node.xml').read_text();t=bpy.data.texts.get(name+'/node.xml')or bpy.data.texts.new(name+'/node.xml');t.clear();t.write(node)
for folder in (r/'new-library').iterdir():
 t=bpy.data.texts.get(folder.name+'/node.xml')or bpy.data.texts.new(folder.name+'/node.xml');t.clear();t.write((folder/'node.xml').read_text())
mods=pack/'models/lap-texture-weight-v1';mods.mkdir(exist_ok=True);visual=mods/'Lap Catch Lightweight Export Library.blend';bpy.data.libraries.write(str(visual),set(mapping.values())|set(materials.values()),fake_user=True)
bpy.ops.wm.save_as_mainfile(filepath=str(final));proof['finalNative']={'path':str(final),'bytes':final.stat().st_size,'sha256':hashlib.sha256(final.read_bytes()).hexdigest()};proof['variantVisualLibrary']=str(visual)
canon=pack/'blender/FLUXARA_Track_Asset_Library.blend';backup=before/'canonical-before-lightweight.blend'
if not backup.exists():subprocess.run(['cp','-c',str(canon),str(backup)],check=True)
proof['canonicalBeforeSHA256']=hashlib.sha256(canon.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(canon));bpy.context.preferences.filepaths.save_version=0
with bpy.data.libraries.load(str(visual),link=False)as(a,b):b.objects=[p['name']for p in prototypes]
collection=bpy.data.collections.new('Lap Catch Lightweight Texture Exports');bpy.context.scene.collection.children.link(collection)
for o in b.objects:
 collection.objects.link(o);o.hide_render=True;o.hide_set(True)
bpy.ops.wm.save_as_mainfile(filepath=str(canon));proof['canonicalAfterSHA256']=hashlib.sha256(canon.read_bytes()).hexdigest();proof['canonicalPath']=str(canon);(r/'native.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n');print('LAP_LIGHTWEIGHT_NATIVE_AND_CANONICAL_SAVED',len(updated),len(prototypes),flush=True)
