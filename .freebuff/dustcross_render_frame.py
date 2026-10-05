# Render the control camera to the given output path. argv[0] = output png path.
import bpy, sys, os, traceback
raw = argv[0] if argv else "/tmp/dc_frame.png"
out = raw if raw.startswith("/") else os.path.join(
    "/Users/motoricallc/Downloads/fluxara-drift", raw)
os.makedirs(os.path.dirname(out), exist_ok=True)
try:
    sc = bpy.context.scene
    sc.render.filepath = out
    sc.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
    print("rendered:", out)
    print("SCRIPT_OK")
except Exception:
    traceback.print_exc()
    print("SCRIPT_FAIL")
