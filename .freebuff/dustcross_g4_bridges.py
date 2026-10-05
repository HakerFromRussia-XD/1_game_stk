# Pass B, Group 4: bridges. Wooden arched bridge across the bowl's NW gap,
# second elevated silhouette bridge near the NE mesa (ref-03 left tower+bridge).
import bpy, math
from mathutils import Vector, Euler

LIB = "/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK/blender/FLUXARA_Track_Asset_Library.blend"
col = bpy.data.collections["DC_G4_Bridges"]
for o in list(col.objects):
    bpy.data.objects.remove(o)

names = ["FD_CanyonArchedBridge", "FD_CanyonBridgePost", "FD_CanyonBridgeRail", "FD_CanyonBridgeEnd"]
with bpy.data.libraries.load(LIB) as (src, dst):
    dst.objects = [n for n in names if n in src.objects]

def link(o):
    for c in list(o.users_collection): c.objects.unlink(o)
    col.objects.link(o)

def recenter(o):
    me = o.data
    xs=[v.co.x for v in me.vertices]; ys=[v.co.y for v in me.vertices]; zs=[v.co.z for v in me.vertices]
    cx, cy, cz = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2, (min(zs)+max(zs))/2
    for v in me.vertices:
        v.co.x -= cx; v.co.y -= cy; v.co.z -= cz
    return (max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs))

wood = bpy.data.materials.get("DC_Bridge_Wood_Honey")
if wood is None:
    wood = bpy.data.materials.new("DC_Bridge_Wood_Honey")
    wood.use_nodes = True
    b = wood.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (0.62, 0.42, 0.22, 1.0)
    b.inputs["Roughness"].default_value = 0.8

bridge = bpy.data.objects["FD_CanyonArchedBridge"]
link(bridge)
bridge.data = bridge.data.copy()
size = recenter(bridge)
print("bridge size:", [round(v,1) for v in size])
for nm in ("FD_CanyonBridgePost", "FD_CanyonBridgeRail", "FD_CanyonBridgeEnd"):
    o = bpy.data.objects[nm]
    link(o)
    o.data = o.data.copy()
    recenter(o)

# main crossing: NW->N across bowl edge at x~-215..-40 (over the gap between mesa-01 and bowl rim)
# span ~170m along +x, deck height from mesa base ledge ~14 up to rim 8
S = 175.0 / max(size[0], 0.001) * 0.55   # partial span for the arched segment
bridge.scale = (S, S, S)
bridge.rotation_euler = Euler((0, 0, math.radians(15)))
bridge.location = (-130.0, 95.0, 22.0)

# assign wood to bridge + rails/posts/ends
for nm in names:
    o = bpy.data.objects.get(nm)
    if not o: continue
    o.data.materials.clear()
    o.data.materials.append(wood)

# posts/rails/ends arranged along the bridge axis (local x before rotation)
posts = bpy.data.objects["FD_CanyonBridgePost"]
rails = bpy.data.objects["FD_CanyonBridgeRail"]
ends = bpy.data.objects["FD_CanyonBridgeEnd"]
psize = recenter(posts); rsize = recenter(rails); esize = recenter(ends)
import random
random.seed(7)
base_loc = Vector((-160.0, 82.0, 16.0))
step = Vector((22.0, 5.6, 0.0))
for i in range(8):
    p = posts.copy(); p.data = posts.data; link(p)
    p.scale = (1.4, 1.4, 1.4)
    p.rotation_euler = Euler((0,0,math.radians(15)))
    p.location = base_loc + step*i
    p.location.z = 16.0 + math.sin(i/7*math.pi)*8.0
for i in range(6):
    r = rails.copy(); r.data = rails.data; link(r)
    r.scale = (1.4, 1.4, 1.4)
    r.rotation_euler = Euler((0,0,math.radians(15)))
    r.location = base_loc + step*i + Vector((11,2.8,3.2))
    r.location.z = 19.0 + math.sin((i+0.5)/6*math.pi)*8.0
for i in range(2):
    e = ends.copy(); e.data = ends.data; link(e)
    e.scale = (1.4,1.4,1.4)
    e.rotation_euler = Euler((0,0,math.radians(15)))
    e.location = base_loc + step*(i*7) 

# NE silhouette bridge: small arched bridge standing on mesa-02 top (x~210,y~220,z~96)
b2 = bridge.copy(); b2.data = bridge.data; link(b2)
S2 = 90.0 / max(size[0], 0.001) * 0.5
b2.scale = (S2, S2, S2)
b2.rotation_euler = Euler((0, 0, math.radians(115)))
b2.location = (225.0, 245.0, 99.0)

bpy.context.view_layer.update()
bpy.ops.wm.save_mainfile()
dg = bpy.context.evaluated_depsgraph_get()
for o in [bridge, b2]:
    oe = o.evaluated_get(dg)
    pts = [oe.matrix_world @ Vector(c) for c in oe.bound_box]
    xs=[p.x for p in pts]; ys=[p.y for p in pts]; zs=[p.z for p in pts]
    print(o.name, "x[%.0f,%.0f] y[%.0f,%.0f] z[%.0f,%.0f]" % (min(xs),max(xs),min(ys),max(ys),min(zs),max(zs)))
print("G4 objects:", len(col.objects))
print("SCRIPT_OK")
