# Pass B, Group 6: ramps (jumps) — authored minimal, per ref-01.
# Two ramps: metal grid deck sloped up, chevron face at front, side panels.
import bpy, math, bmesh
from mathutils import Vector, Euler

col = bpy.data.collections["DC_G6_Ramps"]
for o in list(col.objects):
    bpy.data.objects.remove(o)

def mat(name, color, rough=0.6, emit=0.0):
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

m_metal = mat("DC_Ramp_MetalGrid", (0.35, 0.38, 0.42, 1.0), rough=0.45, emit=0.0)
m_chev  = mat("DC_Chevron_Yellow", (0.92, 0.70, 0.10, 1.0))
m_frame = mat("DC_Ramp_Frame", (0.75, 0.15, 0.10, 1.0))
m_gate  = mat("DC_Ramp_Gate", (0.85, 0.83, 0.78, 1.0))

def wedge(name, length, width, height):
    """Sloped ramp: rises along +Y from 0 to height, length along Y."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    verts = [
        bm.verts.new((-width/2, -length/2, 0)), bm.verts.new((width/2, -length/2, 0)),
        bm.verts.new((width/2,  length/2, height)), bm.verts.new((-width/2, length/2, height)),
        bm.verts.new((-width/2, -length/2, -0.8)), bm.verts.new((width/2, -length/2, -0.8)),
        bm.verts.new((width/2,  length/2, -0.8)), bm.verts.new((-width/2, length/2, -0.8)),
    ]
    faces = [
        (verts[0], verts[1], verts[2], verts[3]),  # deck (sloped)
        (verts[4], verts[5], verts[6], verts[7]),  # bottom
        (verts[0], verts[1], verts[5], verts[4]),  # back
        (verts[1], verts[2], verts[6], verts[5]),  # side +x
        (verts[2], verts[3], verts[7], verts[6]),  # front (tall)
        (verts[3], verts[0], verts[4], verts[7]),  # side -x
    ]
    for f in faces:
        try: bm.faces.new(f)
        except ValueError: pass
    bm.normal_update()
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    col.objects.link(o)
    o.data.materials.append(m_metal)
    return o

def slab(name, sx, sy, sz, matx, loc, rz=0.0):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    col.objects.link(o)
    o.scale = (sx, sy, sz)
    o.location = loc
    o.rotation_euler = Euler((0,0,rz))
    o.data.materials.append(matx)
    return o

# Ramp A: center-north, facing north (car launches over the bowl center)
rA = wedge("DC_RampA", 26.0, 14.0, 6.5)
rA.location = (0.0, 60.0, 0.5)
slab("DC_RampA_FrontChev", 13.5, 0.5, 5.5, m_chev, (0.0, 73.2, 3.2))
slab("DC_RampA_SideL", 0.6, 26.0, 3.0, m_frame, (-7.2, 60.0, 2.5))
slab("DC_RampA_SideR", 0.6, 26.0, 3.0, m_frame, ( 7.2, 60.0, 2.5))
# start gate: two posts + top bar
slab("DC_RampA_PostL", 1.0, 1.0, 9.0, m_gate, (-7.5, 47.0, 4.5))
slab("DC_RampA_PostR", 1.0, 1.0, 9.0, m_gate, ( 7.5, 47.0, 4.5))
slab("DC_RampA_TopBar", 16.0, 1.2, 1.2, m_gate, (0.0, 47.0, 9.0))

# Ramp B: east, rotated to face west
rB = wedge("DC_RampB", 24.0, 13.0, 6.0)
rB.location = (95.0, -20.0, 0.5)
rB.rotation_euler = Euler((0, 0, math.radians(-90)))
slab("DC_RampB_FrontChev", 12.5, 0.5, 5.0, m_chev, (81.6, -20.0, 3.0), rz=math.radians(-90))
slab("DC_RampB_SideL", 0.6, 24.0, 2.8, m_frame, (95.0, -26.8, 2.4))
slab("DC_RampB_SideR", 0.6, 24.0, 2.8, m_frame, (95.0, -13.2, 2.4))
slab("DC_RampB_PostL", 1.0, 1.0, 8.5, m_gate, (108.0, -27.5, 4.2))
slab("DC_RampB_PostR", 1.0, 1.0, 8.5, m_gate, (108.0, -12.5, 4.2))
slab("DC_RampB_TopBar", 1.2, 16.0, 1.2, m_gate, (108.0, -20.0, 8.5))

bpy.context.view_layer.update()
bpy.ops.wm.save_mainfile()
print("G6 objects:", len(col.objects))
print("SCRIPT_OK")
