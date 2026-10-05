import bpy,json
from pathlib import Path
r=Path(__file__).resolve().parent;p=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK');rows={}
paths=[p/'models/spell-lab-reference-v1/Spell Lab Visual Library.blend',p/'blender/FLUXARA_Track_Asset_Library.blend']
for path in paths:
 with bpy.data.libraries.load(str(path),link=False) as(a,b):
  names=[n for n in a.objects if (any(s in n.lower() for s in ['archedbridge','cascadeflow','splitfalls']) or n in ['SpellLab_Asset_05b8778a796e49cb','SpellLab_Asset_7bb664f9662f2f7c','SpellLab_Asset_4bec4ae50401463b','SpellLab_Asset_a4d944905aa91b13'])]
  b.objects=names
 for o in b.objects:
  if o and o.type=='MESH':
   o.data.calc_loop_triangles();rows[o.name]={'source':str(path),'location':list(o.location),'dimensions':list(o.dimensions),'vertices':len(o.data.vertices),'triangles':len(o.data.loop_triangles),'bounds':[[min(v.co[k] for v in o.data.vertices),max(v.co[k] for v in o.data.vertices)] for k in range(3)],'materials':[m.name if m else None for m in o.data.materials],'textures':[str(n.image.filepath) for m in o.data.materials if m and m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]}
(r/'donor-inspection.json').write_text(json.dumps(rows,indent=2));print('DONORS_INSPECTED',len(rows));print(json.dumps(rows,indent=2))
