import bpy,json
from pathlib import Path
from mathutils import Matrix
r=Path(__file__).resolve().parent;a=json.loads((r/'asset-registration.json').read_text());bpy.ops.wm.open_mainfile(filepath=a['finalBlend']);missing=[]
for image in bpy.data.images:
 if image.source=='FILE' and not image.packed_file and not Path(bpy.path.abspath(image.filepath)).is_file():missing.append(image.filepath)
assert not missing,missing
error=0
for row in a['nativeSharedInstances']:
 o=bpy.data.objects[row['name']];assert o.data==bpy.data.objects[row['prototype']].data
 error=max(error,max(abs(o.matrix_world[i][j]-row['matrix'][i][j]) for i in range(4) for j in range(4)))
assert error<.002,error
for n in ['scene.xml','track.xml','materials.xml','quads.xml','graph.xml']:assert bpy.data.texts[n].as_string()==(r/'candidate'/n).read_text(),n
assert len(list(Path(a['finalBlend']).parent.glob('*.blend')))==1
(r/'final-blend-verification.json').write_text(json.dumps({'finalBlendOpens':True,'sharedInstancesMatch':len(a['nativeSharedInstances']),'maxTransformError':error,'missingTextures':missing,'xmlTextsExact':True,'protectedQuads':a['protectedQuads'],'meshObjects':sum(o.type=='MESH' for o in bpy.data.objects)},indent=2));print('FINAL_BLEND_VERIFIED',error)
