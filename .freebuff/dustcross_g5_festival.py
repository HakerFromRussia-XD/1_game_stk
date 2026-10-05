# Pass B, Group 5: pennant lines, chevron boards, grandstand silhouettes.
import bpy, math
from mathutils import Vector, Euler

LIB = "/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK/blender/FLUXARA_Track_Asset_Library.blend"
col = bpy.data.collections["DC_G5_GrandstandsFlags"]
for o in list(col.objects):
    bpy.data.objects.remove(o)

names = ["FD_BridgeClothFlag", "FD_FlagPole" if "FD_FlagPole" in [] else "SkiDash_Reused_FlagPole",
         "SkiDash_ChevronBoard_v1", "SkiDash_BuntingSpan_v1"]
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

# materials
def mat(name, color, rough=0.85, emit=0.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = color
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = color
        b.inputs["Emission Strength"].default_value = emit
    return m

m_fab = mat("DC_Tent_Red", (0.82, 0.15, 0.12, 1.0))
m_fab2 = mat("DC_Tent_Yellow", (0.95, 0.75, 0.15, 1.0))
m_chev = mat("DC_Chevron_Yellow", (0.92, 0.70, 0.10, 1.0))
m_stand = mat("DC_Grandstand_Grey", (0.55, 0.55, 0.58, 1.0))
m_pole = mat("DC_Pole_Dark", (0.25, 0.27, 0.30, 1.0))

flag = bpy.data.objects.get("FD_BridgeClothFlag")
bunting = bpy.data.objects.get("SkiDash_BuntingSpan_v1")
chev = bpy.data.objects.get("SkiDash_ChevronBoard_v1")

# pennant line along the main bridge rails (bridge at NW, rotated 15deg)
if flag:
    link(flag)
    flag.data = flag.data.copy()
    fsize = recenter(flag)
    print("flag size:", [round(v,1) for v in fsize])
    proto_flag = flag
    import random
    random.seed(3)
    base = Vector((-165.0, 86.0, 22.5))
    dirv = Vector((math.cos(math.radians(15)), math.sin(math.radians(15)), 0))
    for i in range(16):
        f = proto_flag.copy(); f.data = proto_flag.data; link(f)
        s = 1.1
        f.scale = (s,s,s)
        f.rotation_euler = Euler((0, 0, math.radians(15) + math.pi))
        pos = base + dirv * (i * 11.5)
        pos.z = 23.0 + math.sin(i/15*math.pi)*8.0
        f.location = pos

# bunting spans across bowl (like ref-01/03 garlands)
if bunting:
    link(bunting)
    bunting.data = bunting.data.copy()
    bsize = recenter(bunting)
    print("bunting size:", [round(v,1) for v in bsize])
    S = 120.0 / max(bsize[0], 0.001) * 0.35
    for i, (loc, rz) in enumerate([
        ((-60.0, 150.0, 14.0), math.radians(8)),
        (( 60.0, 150.0, 14.0), math.radians(-8)),
        ((150.0, -40.0, 14.0), math.radians(100)),
        ((-150.0, -60.0, 14.0), math.radians(80)),
    ]):
        b = bunting.copy(); b.data = bunting.data; link(b)
        b.scale = (S, S, S)
        b.rotation_euler = Euler((0, 0, rz))
        b.location = loc

# chevron boards near rim curves
if chev:
    link(chev)
    chev.data = chev.data.copy()
    csize = recenter(chev)
    print("chevron size:", [round(v,1) for v in csize])
    s = 3.2 / max(csize[2], 0.001)
    chev.scale = (s, s, s)
    chev.data.materials.clear(); chev.data.materials.append(m_chev)
    spots = [(-95.0, 168.0, 9.5, math.radians(30)),
             ( 95.0, 168.0, 9.5, math.radians(-30)),
             (165.0, -80.0, 9.5, math.radians(120)),
             (-165.0, -95.0, 9.5, math.radians(-120))]
    for i, (x, y, z, rz) in enumerate(spots):
        c = chev.copy(); c.data = chev.data; link(c)
        c.scale = (s, s, s)
        c.rotation_euler = Euler((0, 0, rz))
        c.location = (x, y, z)

# grandstand silhouettes: simple tiered boxes at south rim (ref-01 back)
def box(name, sx, sy, sz, matx):
    me = bpy.data.meshes.new(name)
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    col.objects.link(o)
    o.scale = (sx, sy, sz)
    o.data.materials.append(matx)
    return o

# three grandstand tiers, south rim (y ~ -200..-230), facing north
for tier, (z, depth) in enumerate([(2.0, 10.0), (5.5, 10.0), (9.0, 10.0)]):
    b = box(f"DC_Grandstand_South_T{tier}", 90.0, depth, 4.0 + tier*3.5, m_stand)
    b.location = (0.0, -215.0 - tier*11.0, z + 4.0)

# tent canopies: colored slabs above stands (red/yellow alternating)
for i, x in enumerate((-60.0, -20.0, 20.0, 60.0)):
    t = box(f"DC_Tent_{i}", 26.0, 14.0, 1.0, m_fab if i%2==0 else m_fab2)
    t.location = (x, -212.0, 16.5)
    p = box(f"DC_TentPole_{i}", 0.8, 0.8, 14.0, m_pole)
    p.location = (x, -212.0, 9.0)

bpy.context.view_layer.update()
bpy.ops.wm.save_mainfile()
print("G5 objects:", len(col.objects))
print("SCRIPT_OK")
