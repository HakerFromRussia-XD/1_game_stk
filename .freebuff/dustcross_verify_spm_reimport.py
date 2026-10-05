# Re-import the exported scenery SPM into a TEMP scene to verify what the game loads.
import bpy, mathutils

spm = "/Users/motoricallc/Downloads/fluxara-drift/track-reworks/dust-cross-split-combat/dust-cross_scenery.spm"

old_scene = bpy.context.scene
tmp = bpy.data.scenes.new("SPM_VERIFY_TMP")
bpy.context.window.scene = tmp

try:
    bpy.ops.import_scene.spm(filepath=spm)
    objs = [o for o in tmp.objects if o.type == "MESH"]
    print("SPM objects:", len(objs))

    mn = [1e9] * 3
    mx = [-1e9] * 3
    for o in objs:
        for c in o.bound_box:
            w = o.matrix_world @ mathutils.Vector(c)
            for i in range(3):
                mn[i] = min(mn[i], w[i])
                mx[i] = max(mx[i], w[i])
    print("bounds min:", [round(v, 1) for v in mn])
    print("bounds max:", [round(v, 1) for v in mx])

    # largest objects by bbox diagonal
    def diag(o):
        pts = [o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
        xs = [p.x for p in pts]; ys = [p.y for p in pts]; zs = [p.z for p in pts]
        return ((max(xs)-min(xs))**2 + (max(ys)-min(ys))**2 + (max(zs)-min(zs))**2) ** 0.5

    big = sorted(objs, key=diag, reverse=True)[:12]
    for o in big:
        print(f"BIG {diag(o):7.1f}  {o.name[:60]}")
    print("VERIFY_OK")
finally:
    bpy.context.window.scene = old_scene
    bpy.data.scenes.remove(tmp)
