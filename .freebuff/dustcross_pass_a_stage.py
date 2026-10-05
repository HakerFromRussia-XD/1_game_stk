# Pass A: organize the workfile stage.
# - move imported Dust Cross course underlay into a protected read-only collection
# - move all donor canyon course objects into a hidden legacy staging collection
# - create rebuild collections for the new groups
# - write a staging manifest (provenance of moved objects)
import bpy, json, os

BASE = "/Users/motoricallc/Downloads/fluxara-drift/track-reworks/dust-cross-split-combat"
sc = bpy.context.scene
sc.name = "DustCross"

UNDERLAY_NAMES = {
    "metalgrid.png__", "mudwater.png__", "stk_generic_sand_b.png__",
    "stklama_gravelSide_a.png__", "stklama_road_a.png__",
    "stktex_generic_gravelA.png__", "waterLC.png__", "zippercom.png__",
}

def get_col(name):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        sc.collection.children.link(col)
    return col

def move_obj(obj, col):
    for uc in list(obj.users_collection):
        uc.objects.unlink(obj)
    col.objects.link(obj)

# 1) underlay -> protected collection
under = get_col("DustCross_CourseUnderlay_READ_ONLY")
under_objs = []
for name in UNDERLAY_NAMES:
    o = bpy.data.objects.get(name)
    if o:
        move_obj(o, under)
        under_objs.append(name)
        o.hide_render = False
        o.hide_viewport = False
for o in under.objects:  # lock transforms
    o.lock_location = (True, True, True)
    o.lock_rotation = (True, True, True)
    o.lock_scale = (True, True, True)

# 2) donor legacy -> hidden staging
legacy = get_col("DonorLegacy_Stage_HIDDEN")
moved = 0
for c in bpy.data.collections:
    if c.name in ("DustCross_CourseUnderlay_READ_ONLY", "DonorLegacy_Stage_HIDDEN"):
        continue
    for o in list(c.objects):
        move_obj(o, legacy)
        moved += 1
# hide the whole legacy collection from viewport+render
lc = sc.collection.children.get("DonorLegacy_Stage_HIDDEN")
lc.hide_viewport = True
lc.hide_render = True
for o in legacy.objects:
    o.hide_render = True
    o.hide_viewport = True

# 3) rebuild group collections (visible, empty for now)
groups = [
    "DC_G1_Mesas", "DC_G2_ArenaWalls", "DC_G3_Waterfall",
    "DC_G4_Bridges", "DC_G5_GrandstandsFlags", "DC_G6_Ramps",
]
for g in groups:
    get_col(g)

# manifest of staging decisions
manifest = {
    "workfile": "dust-cross-canyon-work.blend",
    "underlayProtected": under_objs,
    "underlayPolicy": "read-only reference; transforms locked; geometry/UVs must not change",
    "legacyMovedCount": moved,
    "legacyPolicy": "donor canyon course hidden (viewport+render); kept for append-copy reuse; excluded from exports",
    "groups": groups,
}
with open(os.path.join(BASE, "staging-manifest.json"), "w") as f:
    json.dump(manifest, f, indent=2)

print("underlay:", len(under_objs), "| legacy moved:", moved)
print("scene objects total:", len(sc.objects))
print("SCRIPT_OK")
