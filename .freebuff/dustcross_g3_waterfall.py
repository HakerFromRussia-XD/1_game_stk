# Pass B, Group 3: two-part waterfall on the NW cliff + cascade shelves.
import bpy
from mathutils import Vector, Euler

LIB = "/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK/blender/FLUXARA_Track_Asset_Library.blend"
col = bpy.data.collections["DC_G3_Waterfall"]

for o in list(col.objects):
    bpy.data.objects.remove(o)

names = ["FD_UpperCascadeFlow", "FD_LowerCascadeFlow",
         "FD_CascadeRockShelf", "FD_CascadeLipFoam", "FD_CascadeLandingPool"]
with bpy.data.libraries.load(LIB) as (src, dst):
    dst.objects = [n for n in names if n in src.objects]

objs = {n: bpy.data.objects[n] for n in names if n in bpy.data.objects}
for o in objs.values():
    for c in list(o.users_collection):
        c.objects.unlink(o)
    col.objects.link(o)

# water material (turquoise like refs 02/03)
water = bpy.data.materials.get("DC_Water_Turquoise")
if water is None:
    water = bpy.data.materials.new("DC_Water_Turquoise")
    water.use_nodes = True
    b = water.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (0.250, 0.720, 0.700, 1.0)
    b.inputs["Roughness"].default_value = 0.15
rock = bpy.data.materials.get("DC_Sandstone_Red_A")

def local_dims(o):
    xs=[v.co.x for v in o.data.vertices]; ys=[v.co.y for v in o.data.vertices]; zs=[v.co.z for v in o.data.vertices]
    return (min(xs),max(xs),min(ys),max(ys),min(zs),max(zs))

# upper flow: thin tall card pouring over cliff edge at NW (-215,155) area (mesa 01)
upper = objs["FD_UpperCascadeFlow"]
upper.data = upper.data.copy()
upper.data.materials.clear(); upper.data.materials.append(water)
u_span = local_dims(upper)
print("upper local span:", [round(v,2) for v in u_span])
# place at NW cliff: z from cliff top (~78) down to shelf
SC = 14.0
upper.scale = (SC, SC, SC)
upper.rotation_euler = Euler((0, 0, 0.35))
upper.location = (-200.0, 140.0, 12.0)

# lower flow continues to pool
lower = objs["FD_LowerCascadeFlow"]
lower.data = lower.data.copy()
lower.data.materials.clear(); lower.data.materials.append(water)
lower.scale = (SC, SC, SC)
lower.rotation_euler = Euler((0, 0, 0.35))
lower.location = (-196.0, 136.0, -14.0)

# shelf under the falls (rock material)
shelf = objs["FD_CascadeRockShelf"]
shelf.data = shelf.data.copy()
shelf.data.materials.clear(); shelf.data.materials.append(rock)
SS = 10.0
shelf.scale = (SS, SS, SS)
shelf.rotation_euler = Euler((0, 0, 0.35))
shelf.location = (-195.0, 135.0, -18.0)

# landing pool at base
pool = objs["FD_CascadeLandingPool"]
pool.data = pool.data.copy()
pool.data.materials.clear(); pool.data.materials.append(water)
PS = 8.0
pool.scale = (PS, PS, PS)
pool.rotation_euler = Euler((0, 0, 0.35))
pool.location = (-193.0, 133.0, -20.0)

# lip foam at the top edge
lip = objs["FD_CascadeLipFoam"]
lip.data = lip.data.copy()
lip.data.materials.clear(); lip.data.materials.append(water)
LS = 12.0
lip.scale = (LS, LS, LS)
lip.rotation_euler = Euler((0, 0, 0.35))
lip.location = (-201.0, 141.0, 20.0)

bpy.context.view_layer.update()
bpy.ops.wm.save_mainfile()
dg = bpy.context.evaluated_depsgraph_get()
for n, o in objs.items():
    oe = o.evaluated_get(dg)
    pts = [oe.matrix_world @ Vector(c) for c in oe.bound_box]
    xs=[p.x for p in pts]; ys=[p.y for p in pts]; zs=[p.z for p in pts]
    print(n, "x[%.0f,%.0f] y[%.0f,%.0f] z[%.0f,%.0f]" % (min(xs),max(xs),min(ys),max(ys),min(zs),max(zs)))
print("SCRIPT_OK")
