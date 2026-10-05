# Texture pass: replace flat DC materials with atlas/image materials.
# 1) restore donor materials by stripped object name (direct reuse)
# 2) mesas: cube-project UV + fluxara_sandstone_cliffs.png material
# 3) all other flat DC materials -> new image materials on the canyon atlas
# 4) save workfile + export SPM
import bpy, re, os, math

WS = "/Users/motoricallc/Downloads/fluxara-drift"
PACK = WS + "/FLUXARA_TRACK_ASSET_PACK/textures"
WORK = WS + "/track-reworks/dust-cross-split-combat/dust-cross-canyon-work.blend"
SPM_OUT = WS + "/track-reworks/dust-cross-split-combat/dust-cross_scenery.spm"

def log(*a):
    print("TP:", *a)

# ---------- load donor materials map ----------
donor_col = bpy.data.collections.get("DonorLegacy_Stage_HIDDEN")
hidden = set()
def walk(c):
    for o in c.objects:
        hidden.add(o.name)
    for ch in c.children:
        walk(ch)
walk(donor_col)

def strip(n):
    return re.sub(r"\.\d+$", "", n)

donor_mats = {}
for oname in hidden:
    o = bpy.context.scene.objects.get(oname)
    if not o or o.type != "MESH":
        continue
    ms = [s.material for s in o.material_slots if s.material]
    if not ms:
        continue
    has_img = any(m.use_nodes and m.node_tree and any(nd.type == "TEX_IMAGE" for nd in m.node_tree.nodes) for m in ms)
    if has_img:
        donor_mats.setdefault(strip(oname), [m.name for m in ms])

# ---------- image loader ----------
_img_cache = {}
def load_img(path, name):
    if name in _img_cache:
        return _img_cache[name]
    img = bpy.data.images.get(name)
    if img is None or not img.filepath:
        img = bpy.data.images.load(path)
        img.name = name
    _img_cache[name] = img
    return img

ATLAS = load_img(WS + "/track-reworks/canyon-assets/fluxara_canyon_atlas.png"
                 if os.path.exists(WS + "/track-reworks/canyon-assets/fluxara_canyon_atlas.png")
                 else WS + "/iosApp/FluxaraResources/tracks/fluxara-user-dust-cross-split-combat/fluxara_canyon_atlas.png",
                 "DC_FluxaraCanyonAtlas")
SAND  = load_img(PACK + "/3aa565f923a43d0c/fluxara_sandstone_cliffs.png", "DC_FluxaraSandstoneCliffs")
WATER = load_img(PACK + "/68ac94843ba81a16/fluxara_water_flow.png", "DC_FluxaraWaterFlow")

def make_img_mat(name, img, base=None):
    m = bpy.data.materials.get(name)
    if m and m.use_nodes and m.node_tree and any(nd.type == "TEX_IMAGE" for nd in m.node_tree.nodes):
        return m
    m = bpy.data.materials.new(name) if m is None else m
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Linear"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    if base:
        bsdf.inputs["Base Color"].default_value = base
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return m

# flat colors preserved as tint (multiplied over texture) for continuity
FLAT_TINTS = {}
for mn in ["DC_Sandstone_Red_A", "DC_Sandstone_Red_B", "DC_Sandstone_Cap_Pale",
           "DC_Water_Turquoise", "DC_Tent_Red", "DC_Tent_Yellow",
           "DC_Grandstand_Grey", "DC_Bridge_Wood_Honey", "DC_Pole_Dark",
           "DC_Ramp_Gate", "DC_Ramp_Frame", "DC_Chevron_Yellow", "DC_Ramp_MetalGrid"]:
    m = bpy.data.materials.get(mn)
    if m and m.use_nodes and m.node_tree:
        for nd in m.node_tree.nodes:
            if nd.type == "BSDF_PRINCIPLED":
                FLAT_TINTS[mn] = tuple(round(v, 3) for v in nd.inputs["Base Color"].default_value[:])

log("tints captured:", FLAT_TINTS)

# atlas-based materials (region-free full-atlas; UVs decide)
M_SANDSTONE  = make_img_mat("DCX_Sandstone_Atlas",  SAND)
M_ATLAS      = make_img_mat("DCX_CanyonAtlas",      ATLAS)
M_WATERFLOW  = make_img_mat("DCX_WaterFlow",        WATER, base=(0.55, 0.85, 0.9, 1))
M_TENT_RED   = make_img_mat("DCX_TentRed_Atlas",    ATLAS, base=(0.75, 0.12, 0.1, 1))
M_TENT_YEL   = make_img_mat("DCX_TentYellow_Atlas", ATLAS, base=(0.85, 0.65, 0.1, 1))
M_STAND      = make_img_mat("DCX_Stand_Atlas",      ATLAS, base=(0.55, 0.55, 0.58, 1))
M_WOOD       = make_img_mat("DCX_Wood_Atlas",       ATLAS, base=(0.6, 0.42, 0.2, 1))
M_CHEVRON    = make_img_mat("DCX_ChevronYellow_Atlas", ATLAS, base=(0.9, 0.75, 0.1, 1))
M_GATE       = make_img_mat("DCX_RampGate_Atlas",   ATLAS, base=(0.15, 0.15, 0.18, 1))
M_FRAME      = make_img_mat("DCX_RampFrame_Atlas",  ATLAS, base=(0.4, 0.4, 0.45, 1))
M_METALGRID  = make_img_mat("DCX_RampMetalGrid_Atlas", ATLAS, base=(0.35, 0.35, 0.4, 1))
M_POLE       = make_img_mat("DCX_PoleDark_Atlas",   ATLAS, base=(0.12, 0.12, 0.14, 1))

# ---------- 1) restore donor materials on matched DC objects ----------
restored = 0
for o in bpy.context.scene.objects:
    if o.type != "MESH" or not any(c.name.startswith("DC_") for c in o.users_collection):
        continue
    dm = donor_mats.get(strip(o.name))
    if not dm:
        continue
    while len(o.material_slots) < len(dm):
        o.data.materials.append(None)
    for i, mn in enumerate(dm):
        o.material_slots[i].material = bpy.data.materials[mn]
    restored += 1
log("donor materials restored on", restored, "objects")

# ---------- 2) mesas: cube-project UVs + sandstone ----------
def cube_uv(o, scale=0.022):
    me = o.data
    uv = me.uv_layers.get("DCX_CubeUV") or me.uv_layers.new(name="DCX_CubeUV")
    mesh_ws = [o.matrix_world @ v.co for v in me.vertices]
    for poly in me.polygons:
        n = (o.matrix_world.to_3x3() @ poly.normal).normalized()
        ax, ay, az = abs(n)
        if az >= ax and az >= ay:
            i0, i1 = 0, 1
        elif ax >= ay:
            i0, i1 = 1, 2
        else:
            i0, i1 = 0, 2
        for li in poly.loop_indices:
            vi = me.loops[li].vertex_index
            w = mesh_ws[vi]
            uv.data[li].uv = (w[i0] * scale, w[i1] * scale)

mesa_objs = [o for o in bpy.context.scene.objects
             if o.type == "MESH" and any(c.name == "DC_G1_Mesas" for c in o.users_collection)]
for o in mesa_objs:
    cube_uv(o)
    mname = "DCX_Sandstone_Red" if "_Rock" in o.name else "DCX_Sandstone_Cap"
    o.data.materials.clear()
    o.data.materials.append(bpy.data.materials[mname])
log("mesas retextured:", len(mesa_objs))

# waterfall rock shelf also sandstone (already has RockUV)
shelf = [o for o in bpy.context.scene.objects if strip(o.name) == "FD_CascadeRockShelf"]
for o in shelf:
    o.data.materials.clear()
    o.data.materials.append(M_SANDSTONE)
    # keep RockUV: generate cube UV too
    cube_uv(o, scale=0.02)

# ---------- 3) replace remaining flat materials on DC objects ----------
SWAP = {
    "DC_Water_Turquoise": M_WATERFLOW,
    "DC_Tent_Red": M_TENT_RED,
    "DC_Tent_Yellow": M_TENT_YEL,
    "DC_Grandstand_Grey": M_STAND,
    "DC_Bridge_Wood_Honey": M_WOOD,
    "DC_Chevron_Yellow": M_CHEVRON,
    "DC_Ramp_Gate": M_GATE,
    "DC_Ramp_Frame": M_FRAME,
    "DC_Ramp_MetalGrid": M_METALGRID,
    "DC_Pole_Dark": M_POLE,
    "DC_Sandstone_Red_A": M_SANDSTONE,
    "DC_Sandstone_Red_B": M_SANDSTONE,
    "DC_Sandstone_Cap_Pale": M_SANDSTONE,
}
swapped = 0
for o in bpy.context.scene.objects:
    if o.type != "MESH" or not any(c.name.startswith("DC_") for c in o.users_collection):
        continue
    for s in o.material_slots:
        if s.material and s.material.name in SWAP:
            s.material = SWAP[s.material.name]
            swapped += 1
log("material slots swapped:", swapped)

# ---------- save + export ----------
bpy.ops.wm.save_mainfile()
log("workfile saved")

bpy.ops.screen.spm_export(filepath=SPM_OUT)
log("SPM exported:", SPM_OUT)
print("TEXTURE_PASS_DONE")
