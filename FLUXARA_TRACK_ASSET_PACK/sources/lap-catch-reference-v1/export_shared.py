import bpy,sys,json,math,shutil,xml.etree.ElementTree as E,copy
from pathlib import Path
r=Path(__file__).resolve().parent;repo=Path('/Users/motoricallc/Downloads/fluxara-drift');dest=repo/'iosApp/FluxaraResources/library';pack=repo/'FLUXARA_TRACK_ASSET_PACK';out=pack/'models/lap-catch-reference-v1/runtime-library';out.mkdir(parents=True,exist_ok=True);f=r/'candidate'
bpy.ops.wm.read_factory_settings(use_empty=True);sys.path.insert(0,'/Users/motoricallc/Library/Application Support/Blender/4.5/scripts/addons');import io_scene_spm;io_scene_spm.register()
with bpy.data.libraries.load(str(r/'Lap Catch Reusable Scenery.blend'),link=False) as(a,b):b.objects=list(a.objects)
protos={o.name:o for o in b.objects};names={'DP_RoundedTree_Prototype':'fluxara_driftlib_round_tree_green_v2','DP_RoundedBush_Prototype':'fluxara_driftlib_round_bush_green_v2','DP_Fir_Prototype':'fluxara_driftlib_circuit_fir_v2','DP_RoundedHill_Prototype':'fluxara_driftlib_grassy_hill_v2','DP_Daisy_Prototype':'fluxara_driftlib_white_daisy_v2','DP_Bunting_Prototype':'fluxara_driftlib_circuit_pennants_v2','DP_GrassTuft_Prototype':'fluxara_driftlib_grass_tuft_v2','LC_CastleTower_Prototype':'fluxara_driftlib_castle_tower_v1','LC_StoneArch_Prototype':'fluxara_driftlib_stone_castle_arch_v1','LC_Waterfall_Prototype':'fluxara_driftlib_castle_waterfall_v1'};exports=[]
for n,o in protos.items():
 if not n.startswith('LC_'):continue
 folder=out/names[n];folder.mkdir(exist_ok=True);bpy.context.scene.collection.objects.link(o);o.hide_set(False);o.hide_render=False;o.location=(0,0,0);o.rotation_euler=(0,0,0);o.scale=(1,1,1);bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
 bpy.ops.screen.spm_export(filepath=str(folder/(names[n]+'_main.spm')),selection_type='selected',localsp=False,applymodifiers=True,export_normal=True,export_vcolor=True,export_tangent=False)
 root=E.Element('scene');obj=E.SubElement(root,'object',id=names[n]+'_mesh',type='animation',model=names[n]+'_main.spm',xyz='0 0 0',hpr='0 0 0',scale='1 1 1',interaction='ghost',**{'skeletal-animation':'false'})
 tex={Path(node.image.filepath).name:Path(node.image.filepath) for m in o.data.materials if m and m.use_nodes for node in m.node_tree.nodes if node.type=='TEX_IMAGE' and node.image}
 mats=E.Element('materials')
 for name,path in tex.items():
  assert path.exists(),path;shutil.copy2(path,folder/name)
  attrs={'name':name}
  if n=='LC_Waterfall_Prototype':attrs.update({'shader':'alphablend','disable-z-write':'Y','backface-culling':'N','ignore':'Y'});E.SubElement(obj,'animated-texture',name=name,dx='0',dy='0.12')
  E.SubElement(mats,'material',attrs)
 E.ElementTree(root).write(folder/'node.xml',encoding='unicode');E.ElementTree(mats).write(folder/'materials.xml',encoding='unicode');shutil.copytree(folder,dest/folder.name,dirs_exist_ok=True);exports.append({'prototype':n,'library':folder.name,'path':str(folder),'bytes':sum(p.stat().st_size for p in folder.iterdir() if p.is_file())})
# Leafy donor placements are adapted by wrappers sharing the same actual pooled mesh. Source libraries remain unchanged.
current=E.parse(f/'scene.xml');scene=E.parse(r/'before/scene.xml')
for tag in ['sun','sky-box']:
 old=scene.getroot().find(tag);idx=list(scene.getroot()).index(old);scene.getroot().remove(old);scene.getroot().insert(idx,copy.deepcopy(current.getroot().find(tag)))
source=json.loads((r/'shared-source-inspection.json').read_text());wrappers=[];adapted=[]
for old,info in source.items():
 if not any(s in old for s in ['pinetree','cypress','accacia','palmTree','autumnSmallBush','agave','autumnTree','modernHousing','RadioTower']):continue
 bb=info['visualBounds'];assert bb,old
 target='fluxara_driftlib_round_bush_green_v2' if any(s in old for s in ['Bush','agave']) else 'fluxara_driftlib_round_tree_green_v2'
 if any(s in old for s in ['modernHousing','RadioTower']):target='fluxara_driftlib_castle_tower_v1'
 dim=[b-a for a,b in bb];dim[1]=min(dim[1],65 if target=='fluxara_driftlib_castle_tower_v1' else 35);dim[0]=min(dim[0],18);dim[2]=min(dim[2],18)
 if target=='fluxara_driftlib_round_tree_green_v2':
  dim[1]=min(dim[1],20);dim[0]=max(dim[0],dim[1]*.65);dim[2]=max(dim[2],dim[1]*.65)
 new='fluxara_driftlib_lc_green_'+old.replace('fluxara_driftlib_','')+'_v1';folder=out/new;folder.mkdir(exist_ok=True);root=E.Element('scene')
 E.SubElement(root,'library',name=target,id=new+'_visual',xyz=f'{(bb[0][0]+bb[0][1])/2} {bb[1][0]} {(bb[2][0]+bb[2][1])/2}',hpr='0 0 0',scale=' '.join(map(str,dim)))
 original=E.parse(dest/old/'node.xml').getroot()
 for q in original.findall('object'):
  if q.get('interaction')=='physicsonly':
   root.append(copy.deepcopy(q));shutil.copy2(dest/old/q.get('model'),folder/q.get('model'))
 E.ElementTree(root).write(folder/'node.xml',encoding='unicode');E.ElementTree(E.Element('materials')).write(folder/'materials.xml',encoding='unicode');shutil.copytree(folder,dest/new,dirs_exist_ok=True)
 for q in scene.getroot().findall('library'):
  if q.get('name')==old:q.set('name',new);adapted.append(q.get('id'))
 wrappers.append({'library':new,'sourceLibrary':old,'sharedMesh':target,'instances':info['instances'],'physicalObjectNodesRetained':len(info['physics']),'bytes':sum(p.stat().st_size for p in folder.iterdir() if p.is_file())})
# Add coordinates only; no baked duplicate scenery model in the map folder.
rows=json.loads((r/'placements.json').read_text())
for row in rows:
 row['library']=names[row['prototype']];E.SubElement(scene.getroot(),'library',name=row['library'],id=row['name'],xyz=' '.join(f'{x:.8f}' for x in row['xyz']),hpr=f"0 {-math.degrees(row['rotationZRadians']):.8f} 0",scale=' '.join(f'{x:.8f}' for x in row['scale']))
scene.write(f/'scene.xml',encoding='unicode');(r/'shared-runtime.json').write_text(json.dumps({'exports':exports,'wrappers':wrappers,'adaptedOriginalPlacements':adapted,'newPlacements':rows,'newSharedBytes':sum(q['bytes'] for q in exports+wrappers),'newPlacementCount':len(rows)},indent=2));print('SHARED_EXPORTED',len(exports),len(wrappers),len(rows))
