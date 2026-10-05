# Compute arena bounds from the protected underlay, save workfile, add control camera.
import bpy, json, os
from mathutils import Vector

BASE = "/Users/motoricallc/Downloads/fluxara-drift/track-reworks/dust-cross-split-combat"
under = bpy.data.collections["DustCross_CourseUnderlay_READ_ONLY"]

def world_bbox(objs):
    pts = []
    for o in objs:
        if o.type != "MESH":
            continue
        for c in o.bound_box:
            pts.append(o.matrix_world @ Vector(c))
    xs = [p.x for p in pts]; ys = [p.y for p in pts]; zs = [p.z for p in pts]
    return (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))

bx = world_bbox(under.objects)
print("underlay bbox: x[%.1f, %.1f] y[%.1f, %.1f] z[%.1f, %.1f]" % bx)

# inner bowl walls (gravel) — the playable arena extent
inner = [o for o in under.objects if "gravel" in o.name.lower()]
ibx = world_bbox(inner)
print("inner bowl bbox: x[%.1f, %.1f] y[%.1f, %.1f] z[%.1f, %.1f]" % ibx)

# control camera: arena center, gameplay-like height, looking north
cx, cy = (bx[0]+bx[1])/2, (bx[2]+bx[3])/2
cam_data = bpy.data.cameras.new("DC_ControlCam")
cam = bpy.data.objects.new("DC_ControlCam", cam_data)
bpy.context.scene.collection.objects.link(cam)
cam.location = (cx, cy - ibx[3]*0.55, 26.0)   # south-ish inside bowl, low
cam.rotation_euler = (1.35, 0, 0)             # mostly horizontal, slight down
cam_data.lens = 28
bpy.context.scene.camera = cam

# render settings for control frames
sc = bpy.context.scene
sc.render.resolution_x = 800
sc.render.resolution_y = 450

bpy.ops.wm.save_mainfile()
print("camera at", tuple(round(v,1) for v in cam.location))
with open(os.path.join(BASE, "arena-bounds.json"), "w") as f:
    json.dump({"underlayBBox": bx, "innerBowlBBox": ibx, "controlCam": list(cam.location)}, f, indent=2)
print("SCRIPT_OK")
