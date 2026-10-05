import bpy,json,shutil,hashlib
from pathlib import Path
r=Path(__file__).resolve().parent;repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK';work=r.parent.parent;paths=[work/'fluxara-user-ski-dash-final/Ski Dash.blend',pack/'blender/FLUXARA_Track_Asset_Library.blend',pack/'models/shared/fluxara_timber_cottage_v1/Fluxara Timber Cottage.blend',pack/'models/shared/fluxara_snowy_chalet_v1/Fluxara Snowy Wood Chalet.blend',work/'shared-object-redesign/wood-lodge/candidate/Fluxara Snowy Wood Chalet.blend',pack/'models/lap-catch-reference-v1/Lap Catch Visual Library.blend',work/'fluxara-user-lap-catch-final/Lap Catch.blend'];names={'fluxara_cottage_windows.png','fluxara_chalet_window.png'};rows=[]
for p in paths:
 assert p.is_file(),p;backup=r/'blend-before'/(hashlib.sha256(str(p).encode()).hexdigest()[:12]+'-'+p.name);backup.parent.mkdir(exist_ok=True)
 if not backup.exists():shutil.copy2(p,backup)
 bpy.ops.wm.open_mainfile(filepath=str(p));bpy.context.preferences.filepaths.save_version=0
 geometry=[(o.name,o.data.name if o.data else None,[list(v) for v in o.matrix_world],len(o.data.vertices) if o.type=='MESH' else None,len(o.data.polygons) if o.type=='MESH' else None) for o in bpy.data.objects];changed=[]
 for m in bpy.data.materials:
  if not m.use_nodes:continue
  candidates=[n for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and Path(n.image.filepath).name in names]
  if not candidates:continue
  assert len(candidates)==1,(m.name,[n.image.filepath for n in candidates]);color=candidates[0];output=next(n for n in m.node_tree.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output);em=m.node_tree.nodes.get('Fluxara Shared Window Emission') or m.node_tree.nodes.new('ShaderNodeEmission');em.name='Fluxara Shared Window Emission';em.label='Runtime shader: unlit';em.inputs['Strength'].default_value=1;m.node_tree.links.new(color.outputs['Color'],em.inputs['Color']);m.node_tree.links.new(em.outputs[0],output.inputs['Surface']);m['game_shader']='unlit';m['shared_window_lighting']='User requested globally glowing windows; original pixels and UVs unchanged';changed.append(m.name)
 assert changed,('No window material found',p)
 after=[(o.name,o.data.name if o.data else None,[list(v) for v in o.matrix_world],len(o.data.vertices) if o.type=='MESH' else None,len(o.data.polygons) if o.type=='MESH' else None) for o in bpy.data.objects];assert geometry==after
 bpy.ops.wm.save_as_mainfile(filepath=str(p));rows.append({'path':str(p),'materials':changed,'geometryAndTransformsUnchanged':True,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()});print('WINDOW_BLEND_UPDATED',p,len(changed),flush=True)
(r/'blend-update.json').write_text(json.dumps(rows,indent=2));print('WINDOW_BLENDS_DONE',len(rows),flush=True)
