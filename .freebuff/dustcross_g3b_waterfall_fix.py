# Group 3 fix: pack flow meshes have baked local coords (like donor legacy).
# Recenter each mesh around origin, then position by location. Rescale to cliff.
import bpy
from mathutils import Vector, Euler

col = bpy.data.collections["DC_G3_Waterfall"]
names = ["FD_UpperCascadeFlow", "FD_LowerCascadeFlow",
         "FD_CascadeRockShelf", "FD_CascadeLipFoam", "FD_CascadeLandingPool"]

def recenter(o):
    me = o.data
    xs=[v.co.x for v in me.vertices]; ys=[v.co.y for v in me.vertices]; zs=[v.co.z for v in me.vertices]
    cx, cy, cz = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2, (min(zs)+max(zs))/2
    for v in me.vertices:
        v.co.x -= cx; v.co.y -= cy; v.co.z -= cz
    return (max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs))

sizes = {}
for n in names:
    o = bpy.data.objects.get(n)
    if not o: continue
    sizes[n] = recenter(o)
    o.location = (0,0,0)
    print("recentered", n, "size:", [round(v,1) for v in sizes[n]])

# target: waterfall on NW mesa cliff face, top ~70, base ~-16
# upper flow ~45 tall card, lower flow ~35, shelf wide flat
UP, LOW, SH, LIP, POOL = sizes.get("FD_UpperCascadeFlow",(45,3,20)), sizes.get("FD_LowerCascadeFlow",(40,3,20)), sizes.get("FD_CascadeRockShelf",(30,10,4)), sizes.get("FD_CascadeLipFoam",(12,2,2)), sizes.get("FD_CascadeLandingPool",(25,15,1))
def s_for(size, target_z): return target_z / max(size[2], 0.001)

anchors = {
    "FD_UpperCascadeFlow": ((-205.0, 143.0, 45.0), s_for(UP, 48.0), 0.35),
    "FD_LowerCascadeFlow": ((-201.0, 139.0, 6.0),  s_for(LOW, 40.0), 0.35),
    "FD_CascadeRockShelf": ((-198.0, 136.0, -14.0), 6.0, 0.35),
    "FD_CascadeLipFoam":   ((-206.0, 144.0, 70.0), 3.0, 0.35),
    "FD_CascadeLandingPool": ((-197.0, 135.0, -19.0), 2.0, 0.35),
}
water = bpy.data.materials["DC_Water_Turquoise"]
rock = bpy.data.materials["DC_Sandstone_Red_A"]
mats = {"FD_UpperCascadeFlow": water, "FD_LowerCascadeFlow": water,
        "FD_CascadeRockShelf": rock, "FD_CascadeLipFoam": water,
        "FD_CascadeLandingPool": water}

for n, (loc, s, rz) in anchors.items():
    o = bpy.data.objects[n]
    o.scale = (s, s, s)
    o.rotation_euler = Euler((0,0,rz))
    o.location = loc
    o.data.materials.clear()
    o.data.materials.append(mats[n])

bpy.context.view_layer.update()
bpy.ops.wm.save_mainfile()
dg = bpy.context.evaluated_depsgraph_get()
for n in anchors:
    oe = bpy.data.objects[n].evaluated_get(dg)
    pts = [oe.matrix_world @ Vector(c) for c in oe.bound_box]
    xs=[p.x for p in pts]; ys=[p.y for p in pts]; zs=[p.z for p in pts]
    print(n, "x[%.0f,%.0f] y[%.0f,%.0f] z[%.0f,%.0f]" % (min(xs),max(xs),min(ys),max(ys),min(zs),max(zs)))
print("SCRIPT_OK")
