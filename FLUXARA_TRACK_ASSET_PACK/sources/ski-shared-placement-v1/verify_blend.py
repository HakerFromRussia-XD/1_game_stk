import bpy,json,hashlib
from pathlib import Path
r=Path(__file__).resolve().parent;a=json.load(open(r/'ski-extraction.json'));reg=json.load(open(r/'asset-registration.json'));bpy.ops.wm.open_mainfile(filepath=reg['finalBlend']);excluded={q['name'] for q in json.load(open(r/'native-inspection.json'))[0]['objects'] if q['name'].startswith(('SkiDash_ClifftopFir_','SkiDash_RelocatedFir_'))}|{q['sourceObject'] for q in a['placements'] if q.get('sourceObject') and not q.get('existingCoordinateInstance')};bad=[]
for q in json.load(open(r/'native-inspection.json'))[0]['objects']:
 if q['name'] in excluded:continue
 o=bpy.data.objects.get(q['name']);assert o,q['name'];assert max(abs(o.matrix_world[i][j]-q['matrix'][i][j]) for i in range(4) for j in range(4))<.00001,q['name'];o.data.calc_loop_triangles();assert len(o.data.loop_triangles)==q['triangles'],q['name']
maxerr=0
for q in reg['nativeSharedInstances']:
 o=bpy.data.objects[q['name']];maxerr=max(maxerr,max(abs(o.matrix_world[i][j]-q['matrix'][i][j]) for i in range(4) for j in range(4)));assert o.data==bpy.data.objects[q['prototype']].data
missing=[im.name for im in bpy.data.images if im.source=='FILE' and not im.packed_file and not Path(bpy.path.abspath(im.filepath)).is_file()];assert not missing;assert maxerr<.00001
for n in ['scene.xml','materials.xml','navmesh.xml','track.xml']:assert bpy.data.texts[n].as_string()==(r/'candidate'/n).read_text()
proof={'originalUnrelatedMeshObjectsRetained':len(json.load(open(r/'native-inspection.json'))[0]['objects'])-len(excluded),'unrelatedOriginalTransformsAndTriangleCountsExact':True,'linkedInstanceParts':len(reg['nativeSharedInstances']),'uniquePrototypeParts':len(reg['objects']),'missingImages':missing,'maxTransformError':maxerr,'originalProtectedXmlEmbeddedExact':True};(r/'native-verification.json').write_text(json.dumps(proof,indent=2));print('SKI_NATIVE_VERIFIED',proof,flush=True)
