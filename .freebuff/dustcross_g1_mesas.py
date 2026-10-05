# Pass B, Group 1: mesas skyline for Dust Cross.
# Appends SnowCliff rock/cap pairs from the shared pack, reskins materials to
# red sandstone palette (refs 02/03/04), arranges around the arena, saves.
import bpy
from mathutils import Vector, Euler

LIB = "/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK/blender/FLUXARA_Track_Asset_Library.blend"

ROCK_COL = (0.735, 0.290, 0.155, 1.0)
ROCK_COL2 = (0.800, 0.380, 0.200, 1.0)
CAP_COL = (0.930, 0.700, 0.430, 1.0)

def make_mat(name, color, rough=0.9):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = rough
    return m

rock_mat = make_mat("DC_Sandstone_Red_A", ROCK_COL)
rock_mat2 = make_mat("DC_Sandstone_Red_B", ROCK_COL2)
cap_mat = make_mat("DC_Sandstone_Cap_Pale", CAP_COL)

names = ["SkiDash_SnowCliff_01_Rock", "SkiDash_SnowCliff_01_Cap",
         "SkiDash_SnowCliff_02_Rock", "SkiDash_SnowCliff_02_Cap",
         "SkiDash_SnowCliff_03_Rock", "SkiDash_SnowCliff_03_Cap"]
before = set(o.name for o in bpy.data.objects)
with bpy.data.libraries.load(LIB) as (src, dst):
    dst.objects = [n for n in names if n in src.objects]
appended = [o for o in bpy.data.objects if o.name not in before]
print("appended:", len(appended))

col = bpy.data.collections["DC_G1_Mesas"]
def to_group(o):
    for c in list(o.users_collection): c.objects.unlink(o)
    if o.name not in col.objects:
        col.objects.link(o)

rocks, caps = [], []
for o in appended:
    to_group(o)
    (rocks if "_Rock" in o.name else caps).append(o)

# reskin: independent mesh data, single sandstone material each
for i, r in enumerate(sorted(rocks, key=lambda x: x.name)):
    r.data = r.data.copy()
    r.data.materials.clear()
    r.data.materials.append(rock_mat if i % 2 == 0 else rock_mat2)
for c in caps:
    c.data = c.data.copy()
    c.data.materials.clear()
    c.data.materials.append(cap_mat)

def rock_of(cap_name):
    return cap_name.replace("_Cap", "_Rock")

# arrange pairs around bowl perimeter (arena bowl ~313 x 359)
placements = {
    "SkiDash_SnowCliff_01": ((-215.0,  155.0, -12.0), 90.0, 0.35),
    "SkiDash_SnowCliff_02": (( 210.0,  220.0, -12.0), 110.0, -0.5),
    "SkiDash_SnowCliff_03": (( 250.0, -180.0, -12.0), 80.0, 2.4),
}
for prefix, (loc, height, rz) in placements.items():
    rock = bpy.data.objects[prefix + "_Rock"]
    cap = bpy.data.objects[prefix + "_Cap"]
    d = Vector(rock.dimensions)
    s = height / max(d.z, 0.001)
    rock.location = loc
    rock.rotation_euler = Euler((0, 0, rz))
    rock.scale = (s, s, s)
    bpy.context.view_layer.update()
    dz = Vector((0, 0, d.z * s / 2 - 1.0))
    cap.location = rock.location + dz
    cap.rotation_euler = Euler((0, 0, rz))
    cap.scale = (s * 0.92, s * 0.92, s)

bpy.context.view_layer.update()
bpy.ops.wm.save_mainfile()
for prefix in placements:
    r = bpy.data.objects[prefix + "_Rock"]
    print(prefix, "placed at", tuple(round(v, 1) for v in r.location),
          "dims", tuple(round(v, 1) for v in r.dimensions))
print("SCRIPT_OK")
