import bpy,json,sys,math,shutil,xml.etree.ElementTree as E
from pathlib import Path
r=Path(__file__).resolve().parent;f=r/'candidate';repo=Path('/Users/motoricallc/Downloads/fluxara-drift');dest=repo/'iosApp/FluxaraResources/library';pack=repo/'FLUXARA_TRACK_ASSET_PACK';libout=pack/'models/dp-motorsports-reference-v1/runtime-library';libout.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);sys.path.insert(0,'/Users/motoricallc/Library/Application Support/Blender/4.5/scripts/addons');import io_scene_spm;io_scene_spm.register()
with bpy.data.libraries.load(str(r/'DP Reusable Scenery.blend'),link=False) as(a,b):b.objects=[n for n in a.objects if n.endswith('_Prototype')]
protos={o.name:o for o in b.objects};names={'DP_RoundedTree_Prototype':'fluxara_driftlib_round_tree_green_v1','DP_RoundedBush_Prototype':'fluxara_driftlib_round_bush_green_v1','DP_Fir_Prototype':'fluxara_driftlib_circuit_fir_v1','DP_RoundedHill_Prototype':'fluxara_driftlib_grassy_hill_v1','DP_Daisy_Prototype':'fluxara_driftlib_white_daisy_v1'};exports=[]
for name,o in protos.items():
 folder=libout/names[name];folder.mkdir(exist_ok=True);bpy.context.scene.collection.objects.link(o);bpy.context.view_layer.objects.active=o;bpy.ops.object.select_all(action='DESELECT');o.select_set(True);o.location=(0,0,0);o.rotation_euler=(0,0,0);o.scale=(1,1,1)
 bpy.ops.screen.spm_export(filepath=str(folder/'model.spm'),selection_type='selected',localsp=False,applymodifiers=True,export_normal=True,export_vcolor=False,export_tangent=False)
 root=E.Element('scene');E.SubElement(root,'object',{'id':names[name]+'_mesh','type':'animation','model':'model.spm','xyz':'0 0 0','hpr':'0 0 0','scale':'1 1 1','interaction':'ghost','skeletal-animation':'false'});E.ElementTree(root).write(folder/'node.xml',encoding='unicode')
 texnames={Path(n.image.filepath).name for m in o.data.materials if m and m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image}
 for t in texnames:shutil.copy2(f/t,folder/t)
 root=E.Element('materials')
 for t in texnames:E.SubElement(root,'material',{'name':t,**({'shader':'alphatest','ignore':'Y'} if t=='dp_flower.png' else {})})
 E.ElementTree(root).write(folder/'materials.xml',encoding='unicode');shutil.copytree(folder,dest/folder.name,dirs_exist_ok=True);exports.append({'prototype':name,'library':folder.name,'folder':str(folder),'bytes':sum(p.stat().st_size for p in folder.iterdir() if p.is_file())})
# Reuse exact authored transforms, rather than rounded placement values.
bpy.ops.wm.open_mainfile(filepath=str(r/'DP Motorsports Land II.blend'));rows=json.loads((r/'placements.json').read_text());scene=E.parse(f/'scene.xml')
for e in list(scene.getroot()):
 if e.get('id')=='DP_ReferenceScenery':scene.getroot().remove(e)
for row in rows:
 o=bpy.data.objects[row['name']];loc,rot,scale=o.matrix_world.decompose();h=-math.degrees(rot.to_euler('XZY').z)
 E.SubElement(scene.getroot(),'library',{'name':names[row['prototype']],'id':row['name'],'xyz':f'{loc.x:.9f} {loc.z:.9f} {loc.y:.9f}','hpr':f'0 {h:.9f} 0','scale':f'{scale.x:.9f} {scale.z:.9f} {scale.y:.9f}'})
 row['rotationZRadians']=o.rotation_euler.z;row['library']=names[row['prototype']]
scene.write(f/'scene.xml',encoding='unicode');(r/'shared-runtime.json').write_text(json.dumps({'libraries':exports,'instances':len(rows),'libraryBytes':sum(x['bytes'] for x in exports),'placements':rows},indent=2))
# Preserve the baked export as an intermediate, remove it only from the candidate runtime payload.
shutil.copy2(f/'dp_scenery.spm',r/'baked-scenery-before-sharing.spm');(f/'dp_scenery.spm').unlink();print('SHARED_RUNTIME_EXPORTED',len(exports),len(rows),sum(x['bytes'] for x in exports))
