import bpy,json,math
from pathlib import Path
r=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(r/'Lap Catch Reusable Scenery.blend'));bpy.context.preferences.filepaths.save_version=0
o=bpy.data.objects['LC_Waterfall_Prototype'];materials=list(o.data.materials);vs=[];fs=[];nu=6;nv=14
# Draped cascade matches the reused rounded hill, rather than floating above its crest.
for j in range(nv+1):
 t=j/nv;h=.07+.86*t
 for i in range(nu+1):
  x=i/nu-.5;y=-math.sqrt(max(.001,1-h*h-(x*9/28)**2))-.007;vs.append((x,y,h*20/18))
for j in range(nv):
 for i in range(nu):
  a=j*(nu+1)+i;fs.append((a,a+1,a+nu+2,a+nu+1))
me=bpy.data.meshes.new('LC_DrapedCascade');me.from_pydata(vs,[],fs);me.update();o.data=me
for m in materials:me.materials.append(m)
uv=me.uv_layers.new(name='UVMap')
for p in me.polygons:
 p.use_smooth=True
 for k in p.loop_indices:
  vi=me.loops[k].vertex_index;uv.data[k].uv=(vi%(nu+1)/nu,vi//(nu+1)/nv)
bpy.ops.wm.save_as_mainfile(filepath=str(r/'Lap Catch Reusable Scenery.blend'))
rows=json.loads((r/'placements.json').read_text());hills={x['name']:x for x in rows if x['role']=='cliff'};changes=[]
for x in rows:
 if x['role']!='waterfall':continue
 idx=int(x['name'].rsplit('_',1)[1])-1;hill=hills['LC_cliff_'+str(idx).zfill(4)];old=dict(x);x['xyz']=list(hill['xyz']);x['scale']=[9,18,23];x['rotationZRadians']=hill['rotationZRadians'];changes.append({'before':old,'after':dict(x)})
(r/'placements.json').write_text(json.dumps(rows,indent=2));(r/'waterfall-conformance.json').write_text(json.dumps(changes,indent=2))
bpy.ops.wm.open_mainfile(filepath=str(r/'Lap Catch Scenery Layout.blend'))
with bpy.data.libraries.load(str(r/'Lap Catch Reusable Scenery.blend'),link=False) as (a,b):b.objects=['LC_Waterfall_Prototype']
waterdata=b.objects[0].data
for x in rows:
 if x['role']=='waterfall':
  q=bpy.data.objects[x['name']];q.data=waterdata;q.location=(x['xyz'][0],x['xyz'][2],x['xyz'][1]);q.scale=(x['scale'][0],x['scale'][2],x['scale'][1]);q.rotation_euler.z=x['rotationZRadians']
bpy.ops.wm.save_as_mainfile(filepath=str(r/'Lap Catch Scenery Layout.blend'));print('DRAPED_WATERFALLS_UPDATED',len(changes))
