from pathlib import Path
import bpy, math, random, json, shutil, struct, sys, hashlib
from mathutils import Vector

r = Path(__file__).resolve().parent
w = r/'fidelity-v19'
w.mkdir(exist_ok=True)
c = w/'candidate'
assert not c.exists(), 'Do not overwrite an existing iteration'
shutil.copytree(r/'fidelity-v18/candidate', c)
sys.path.insert(0, str(r.parent/'shared-object-redesign'))
from spm_io import parse
helper = (r/'fidelity_v2.py').read_text()
ns = {'math': math, 'struct': struct}
exec(helper[helper.index('def encode_buffer'):helper.index('new_vertices, new_indices')], ns)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version = 0

def encode(buf, materials, bounds):
    raw = bytearray(b'SP'+bytes([10, 1])+struct.pack('<6f', *bounds)+struct.pack('<H', len(materials)))
    for pair in materials:
        for name in pair:
            s = name.encode(); raw += bytes([len(s)])+s
    raw += struct.pack('<HH', 1, 1)+struct.pack('<IIH', len(buf['vertices']), len(buf['indices']), 0)
    for v in buf['vertices']:
        raw += struct.pack('<3fI2e', *v['position'], v['normal'], *v['uv'])
    raw += struct.pack('<'+str(len(buf['indices']))+('B' if len(buf['vertices']) <= 255 else 'H'), *buf['indices'])
    return raw

records = []
for num, (name, face_budget) in enumerate([('AshCloud.spm', 960), ('AshColumn.spm', 1050), ('PyroclasticFlow.spm', 650)]):
    source = r/'fidelity-v18/candidate'/name
    d = parse(source)
    lo, hi = d['bounds'][:3], d['bounds'][3:]
    rng = random.Random(190031+num)
    # Isosurface of the union of overlapping ellipsoids. One continuous surface,
    # with offset secondary billows, rather than intersecting separate spheres.
    kernels = []
    for j in range(9):
        t = j/8
        if num == 0:
            center = (.18+.65*t, .32+.21*math.sin(t*2.4), .76-.56*t)
        elif num == 1:
            center = (.69-.35*t, .16+.68*t, .80-.63*t)
        else:
            center = (.28+.35*t, .79-.57*t, .78-.58*t)
        rad = .12+.055*t
        kernels.append((center, (rad*1.15, rad, rad*1.06)))
        for q in range(5):
            angle = q*2*math.pi/5+j*1.73
            offset = (math.cos(angle), math.sin(angle), math.cos(angle+1.4))
            norm = math.sqrt(sum(v*v for v in offset))
            cc = tuple(center[k]+rad*1.10*v/norm for k, v in enumerate(offset))
            rr = rad*rng.uniform(.72, 1.05)
            kernels.append((cc, (rr*rng.uniform(.8, 1.2), rr, rr*rng.uniform(.85, 1.15))))
    resolution = 40
    grid = {}
    def value(p):
        return max(1.0-sum(((p[k]-cc[k])/rr[k])**2 for k in range(3)) for cc, rr in kernels)-.017341
    for x in range(resolution+1):
        for y in range(resolution+1):
            for z in range(resolution+1):
                p = (x/resolution*1.4-.2, y/resolution*1.4-.2, z/resolution*1.4-.2)
                grid[(x,y,z)] = (p, value(p))
    vertices, faces, edges = [], [], {}
    def edge(a, b):
        key = tuple(sorted((a, b)))
        if key not in edges:
            pa, va = grid[a]; pb, vb = grid[b]
            t = va/(va-vb)
            edges[key] = len(vertices)
            vertices.append(tuple(pa[k]+t*(pb[k]-pa[k]) for k in range(3)))
        return edges[key]
    # Consistent six-tetrahedra decomposition around each cube diagonal.
    offsets = [(0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,1),(0,1,1)]
    tetrahedra = [(0,1,2,6),(0,2,3,6),(0,3,7,6),(0,7,4,6),(0,4,5,6),(0,5,1,6)]
    for x in range(resolution):
        for y in range(resolution):
            for z in range(resolution):
                ids = [tuple(v+w for v,w in zip((x,y,z), off)) for off in offsets]
                for tet in tetrahedra:
                    inside = [ids[i] for i in tet if grid[ids[i]][1] > 0]
                    outside = [ids[i] for i in tet if grid[ids[i]][1] <= 0]
                    if len(inside) in [0,4]: continue
                    if len(inside) == 1:
                        faces.append(tuple(edge(inside[0], q) for q in outside))
                    elif len(inside) == 3:
                        faces.append(tuple(edge(outside[0], q) for q in inside))
                    else:
                        a,b = inside; e,f = outside
                        ae,af,be,bf = edge(a,e),edge(a,f),edge(b,e),edge(b,f)
                        faces.extend([(ae,be,bf),(ae,bf,af)])
    mesh = bpy.data.meshes.new(name+'DensitySurface')
    mesh.from_pydata(vertices, [], faces)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    # Orient the closed implicit surface, then collapse only decorative mesh.
    import bmesh
    bm = bmesh.new(); bm.from_mesh(mesh)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
    bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-8)
    assert all(len(e.link_faces)==2 for e in bm.edges), (name,"initial surface not closed")
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh); bm.free()
    initial_faces = len(mesh.polygons)
    modifier = obj.modifiers.new('DensitySurfaceBudget', 'DECIMATE')
    modifier.ratio = face_budget/initial_faces
    modifier.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    # Preserve source box exactly, using the actual vertices after simplification.
    mins = [min(v.co[k] for v in obj.data.vertices) for k in range(3)]
    maxs = [max(v.co[k] for v in obj.data.vertices) for k in range(3)]
    for v in obj.data.vertices:
        v.co = tuple(lo[k]+(v.co[k]-mins[k])/(maxs[k]-mins[k])*(hi[k]-lo[k]) for k in range(3))
    obj.data.update()
    bm = bmesh.new(); bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-5)
    bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces)); bm.to_mesh(obj.data)
    components = 0; unseen = set(bm.verts)
    while unseen:
        components += 1; stack = [unseen.pop()]
        while stack:
            v = stack.pop()
            for edge_ in v.link_edges:
                other = edge_.other_vert(v)
                if other in unseen: unseen.remove(other); stack.append(other)
    assert components == 1, (name, components)
    assert all(len(e.link_faces)==2 for e in bm.edges), (name,'Closed smoke surface required',[(len(e.link_faces),tuple(v.index for v in e.verts))for e in bm.edges if len(e.link_faces)!=2][:8])
    bm.free(); obj.data.update()
    buf = {'vertices': [], 'indices': [], 'material': 0}
    for v in obj.data.vertices:
        y = (v.co.y-lo[1])/(hi[1]-lo[1])
        # Retain existing two-tone smoke texture, avoid new raster assets.
        buf['vertices'].append({'position': tuple(v.co), 'normal': ns['packed_normal'](tuple(v.normal)),
                                'uv': (.25, .5)})
    for polygon in obj.data.polygons:
        assert len(polygon.vertices)==3
        buf['indices'].extend(polygon.vertices)
    raw = encode(buf, d['materials'], d['bounds'])
    palette = c/d['materials'][0][0]
    original_model=r/'fidelity-v2/baseline'/name
    assert len(raw)+palette.stat().st_size <= 1.2*(original_model.stat().st_size+palette.stat().st_size)
    (c/name).write_bytes(raw)
    made = parse(c/name)
    extremes = [min(v['position'][k] for v in made['buffers'][0]['vertices']) for k in range(3)]+[max(v['position'][k] for v in made['buffers'][0]['vertices']) for k in range(3)]
    assert max(abs(a-b) for a,b in zip(extremes,d['bounds'])) < .0001
    records.append({'model':name, 'sourceModel':str(source), 'sourceBounds':list(d['bounds']),
                    'continuousClosedConnectedComponents':components, 'densityKernels':len(kernels),
                    'initialIsosurfaceTriangles':initial_faces, 'triangles':len(buf['indices'])//3,
                    'vertices':len(buf['vertices']), 'sourceBytesWithTexture':original_model.stat().st_size+palette.stat().st_size,
                    'weightBaselineModel':str(original_model), 'previousV18BytesWithTexture':source.stat().st_size+palette.stat().st_size,
                    'adaptedBytesWithTexture':len(raw)+palette.stat().st_size,
                    'changePercent':((len(raw)+palette.stat().st_size)/(original_model.stat().st_size+palette.stat().st_size)-1)*100,
                    'paletteSha256':hashlib.sha256(palette.read_bytes()).hexdigest(), 'texturePixelsRetained':True,
                    'originalLocalBoundsAxesOriginAndPlacementRetained':True})
    obj.select_set(False)
proof={'baseCandidate':'V18','smoke':records,'newTextures':0,'newImagePixels':False,
       'sourceObjectsRetained':True,'productionIntegrated':False,'referenceAcceptance':False}
(w/'smoke-changes.json').write_text(json.dumps(proof,indent=2))
print('V19_CONTINUOUS_DENSITY_SMOKE_MODELS_READY',records,flush=True)
