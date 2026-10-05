import bpy,json
from pathlib import Path
repo=Path('/Users/motoricallc/Downloads/fluxara-drift');root=Path('/Users/motoricallc/Downloads/stk-code-master/output');bpy.ops.wm.open_mainfile(filepath=str(repo/'FLUXARA_TRACK_ASSET_PACK/blender/FLUXARA_Track_Asset_Library.blend'));rows=[]
for folder in ['dp-motorsports-rework','lap-catch-rework','motorsport-land-rework','summit-run-rework','volcano-remake-rework','shared-placement-1-10']:
 a=json.load(open(root/folder/'asset-registration.json'))
 for q in a['objects']:
  o=bpy.data.objects.get(q['name']);assert o is not None,(folder,q['name']);assert [m.name if m else None for m in o.data.materials]==q.get('materials',q.get('dependencies')),(folder,q['name'],[m.name if m else None for m in o.data.materials],q.get('materials',q.get('dependencies')))
 for q in a['materials']:
  m=bpy.data.materials.get(q['name']);assert m is not None,(folder,q['name'])
  if m.use_nodes:
   names=sorted({Path(n.image.filepath).name for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image});assert names==q.get('textures',q.get('dependencies')),(folder,q['name'],names,q.get('textures',q.get('dependencies')))
 rows.append({'map':folder,'objects':len(a['objects']),'materials':len(a['materials']),'bindingsMatchRegistration':True})
(root/'shared-placement-1-10/canonical-bindings-verification.json').write_text(json.dumps(rows,indent=2));print('CANONICAL_BINDINGS_VERIFIED',rows)
