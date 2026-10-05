# Proper control camera: wide FOV + game-like clip range, stronger sun.
import bpy
from mathutils import Euler

sc = bpy.context.scene

# remove old control cameras, keep donor preview lights
for name in ("DC_ControlCam", "DC_SideCam", "DC_DiagCam"):
    o = bpy.data.objects.get(name)
    if o:
        bpy.data.objects.remove(o)

cam_data = bpy.data.cameras.new("DC_ControlCam")
cam = bpy.data.objects.new("DC_ControlCam", cam_data)
sc.collection.objects.link(cam)
# ref-01-like framing: from south bowl edge toward the ramps/mesas
cam.location = (0.0, -150.0, 14.0)
cam.rotation_euler = Euler((1.42, 0, 0))
cam_data.lens = 18          # wide, kart-cam feel
cam_data.clip_start = 0.5
cam_data.clip_end = 1750.0  # matches scene.xml camera far
sc.camera = cam

# stronger sun to mimic game day light
sun = bpy.data.lights.get("FD_PreviewSun")
if sun:
    sun.energy = 3.5
fill = bpy.data.lights.get("FD_PreviewFill")
if fill:
    fill.energy = 45000.0

# brighten world a bit
bg = sc.world.node_tree.nodes.get("Background")
bg.inputs[1].default_value = 1.0

sc.render.resolution_x = 800
sc.render.resolution_y = 450
bpy.ops.wm.save_mainfile()
print("camera:", tuple(round(v,1) for v in cam.location), "lens 18 clip 1750")
print("SCRIPT_OK")
