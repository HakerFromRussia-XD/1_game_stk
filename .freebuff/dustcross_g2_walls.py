# Pass B, Group 2: arena perimeter walls (red-white barrier modules).
import bpy, math
from mathutils import Vector, Euler

LIB = "/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK/blender/FLUXARA_Track_Asset_Library.blend"
col = bpy.data.collections["DC_G2_ArenaWalls"]

# purge stale
for o in list(col.objects):
    bpy.data.objects.remove(o)

# append ONE prototype module
proto_name = "SkiDash_ArenaBarrier_00_000"
with bpy.data.libraries.load(LIB) as (src, dst):
    dst.objects = [proto_name]
proto = bpy.data.objects[proto_name]
for c in list(proto.users_collection):
    c.objects.unlink(proto)
col.objects.link(proto)

# make it independent: local copy of mesh
proto.data = proto.data.copy()

# measure module size in world units after normalize
bpy.context.view_layer.update()
raw = Vector(proto.dimensions)
print("proto raw dims:", tuple(round(v, 2) for v in raw))
TARGET_LEN = 7.5   # world meters along track
s = TARGET_LEN / max(raw.x, 0.001) * 0.365   # correction: measured 20.5 after scale 7.5/2.49 -> shrink to ~7.5
proto.scale = (s, s, s)
bpy.context.view_layer.update()
dims = Vector(proto.dimensions)
print("proto scaled dims:", tuple(round(v, 1) for v in dims))

# ring placement: bowl inner walls x[-160,153] y[-179,180]; use ellipse radius
cx, cy = -3.0, 0.0
rx, ry = 175.0, 195.0
N = 150
z_rim = 8.0   # approximate rim height of inner bowl walls
for i in range(N):
    a = 2 * math.pi * i / N
    x = cx + rx * math.cos(a)
    y = cy + ry * math.sin(a)
    o = proto.copy()               # linked duplicate: shared mesh
    o.data = proto.data
    col.objects.link(o)
    o.location = (x, y, z_rim)
    o.rotation_euler = Euler((0, 0, a + math.pi / 2))
    o.scale = (s, s, s)

bpy.context.view_layer.update()
bpy.ops.wm.save_mainfile()
print("barrier modules placed:", len(col.objects))
print("SCRIPT_OK")
