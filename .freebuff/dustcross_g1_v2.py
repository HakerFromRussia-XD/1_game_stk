# Pass B, Group 1 (v2): mesas skyline with mesh-local placement.
# Library objects carry baked world transforms and origins at (0,0,0), so we
# scale the mesh-local coordinates via object scale and treat location as the
# world anchor. Purge failed attempts first, then append + place + save.
import bpy
from mathutils import Vector, Euler

LIB = "/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK/blender/FLUXARA_Track_Asset_Library.blend"

# ---- purge failed first attempt
col = bpy.data.collections["DC_G1_Mesas"]
for o in list(col.objects):
    bpy.data.objects.remove(o)
for nm in [n for n in bpy.data.objects.keys() if n.startswith("SkiDash_SnowCliff")]:
    bpy.data.objects.remove(bpy.data.objects[nm])

ROCK_A = (0.735, 0.290, 0.155, 1.0)
ROCK_B = (0.800, 0.380, 0.200, 1.0)
CAP    = (0.930, 0.700, 0.430, 1.0)

def make_mat(name, color, rough=0.9):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = color
    b.inputs["Roughness"].default_value = rough
    return m

mat_rock_a = make_mat("DC_Sandstone_Red_A", ROCK_A)
mat_rock_b = make_mat("DC_Sandstone_Red_B", ROCK_B)
mat_cap = make_mat("DC_Sandstone_Cap_Pale", CAP)

names = ["SkiDash_SnowCliff_01_Rock", "SkiDash_SnowCliff_01_Cap",
         "SkiDash_SnowCliff_02_Rock", "SkiDash_SnowCliff_02_Cap",
         "SkiDash_SnowCliff_03_Rock", "SkiDash_SnowCliff_03_Cap"]
with bpy.data.libraries.load(LIB) as (src, dst):
    dst.objects = [n for n in names if n in src.objects]

appended = [bpy.data.objects[n] for n in names if n in bpy.data.objects]
print("appended:", [o.name for o in appended])

def link(o):
    for c in list(o.users_collection):
        c.objects.unlink(o)
    col.objects.link(o)

# mesh-local bbox per object (pre-transform)
def local_span(o):
    me = o.data
    xs = [v.co.x for v in me.vertices]; ys = [v.co.y for v in me.vertices]
    zs = [v.co.z for v in me.vertices]
    return (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))

rocks = sorted([o for o in appended if o.name.endswith("_Rock")], key=lambda x: x.name)
caps = sorted([o for o in appended if o.name.endswith("_Cap")], key=lambda x: x.name)

# reskin with independent data
for i, r in enumerate(rocks):
    r.data = r.data.copy()
    r.data.materials.clear()
    r.data.materials.append(mat_rock_a if i % 2 == 0 else mat_rock_b)
for c in caps:
    c.data = c.data.copy()
    c.data.materials.clear()
    c.data.materials.append(mat_cap)

# placements: anchor = desired world center of rock base; rock mesh-local z spans 0..1
placements = {
    "SkiDash_SnowCliff_01": ((-215.0, 155.0), 90.0, 0.35),
    "SkiDash_SnowCliff_02": ((210.0, 220.0), 110.0, -0.5),
    "SkiDash_SnowCliff_03": ((250.0, -180.0), 80.0, 2.4),
}
for prefix, ((ax, ay), height, rz) in placements.items():
    rock = bpy.data.objects[prefix + "_Rock"]
    cap = bpy.data.objects[prefix + "_Cap"]
    link(rock); link(cap)
    sx, sy, sz = local_span(rock)[0], local_span(rock)[1], local_span(rock)[5]
    s = height / sz  # uniform scale from local height
    rock.scale = (s, s, s)
    rock.rotation_euler = Euler((0, 0, rz))
    # rock local center xy ~ 0; mesh spans -0.5..0.5 xy, 0..1 z; anchor at base => z offset -12
    rock.location = (ax, ay, -12.0)
    # cap: local z span likely 0..0.1 or similar; compute after rock scale
    bpy.context.view_layer.update()
    cap_scale = s * 0.92
    cap.scale = (cap_scale, cap_scale, s)
    cap.rotation_euler = Euler((0, 0, rz))
    cap.location = (ax, ay, -12.0 + height - 1.5)

bpy.context.view_layer.update()
bpy.ops.wm.save_mainfile()
# report world bboxes
dg = bpy.context.evaluated_depsgraph_get()
from mathutils import Vector
for prefix in placements:
    for part in ("_Rock", "_Cap"):
        o = bpy.data.objects[prefix + part].evaluated_get(dg)
        pts = [o.matrix_world @ Vector(cor) for cor in o.bound_box]
        xs = [p.x for p in pts]; ys = [p.y for p in pts]; zs = [p.z for p in pts]
        print(prefix + part, "x[%.0f,%.0f] y[%.0f,%.0f] z[%.0f,%.0f]" % (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)))
print("SCRIPT_OK")
