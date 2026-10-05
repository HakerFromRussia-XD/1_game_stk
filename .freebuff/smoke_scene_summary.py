import bpy
from collections import Counter

scene = bpy.context.scene
types = Counter(o.type for o in scene.objects)
collections = [c.name for c in bpy.data.collections]
print(f"scene={scene.name!r} objects={len(scene.objects)}")
print(f"types={dict(types)}")
print(f"collections={collections}")
print(f"images={len(bpy.data.images)} meshes={len(bpy.data.meshes)} materials={len(bpy.data.materials)}")
print("SCRIPT_OK" if scene.name else "SCRIPT_FAIL")
