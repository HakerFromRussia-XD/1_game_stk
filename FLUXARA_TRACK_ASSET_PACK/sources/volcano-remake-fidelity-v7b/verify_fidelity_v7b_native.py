from pathlib import Path
import bpy,json,sys
r=Path(__file__).resolve().parent;w=r/'fidelity-v7b';code=(r/'verify_blend.py').read_text().replace("r/'asset-registration.json'","r/'fidelity-v7b/asset-registration.json'").replace("r/'candidate'","r/'fidelity-v7b/candidate'").replace("r/'final-blend-verification.json'","r/'fidelity-v7b/final-blend-verification.json'");exec(compile(code,str(r/'verify_blend.py'),'exec'))
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
reg=json.loads((w/'asset-registration.json').read_text());checks=[]
for row in reg['newPrototypes']:
 obj=bpy.data.objects[row['name']];d=parse(row['sourceModel']);b=d['buffers'][0];assert len(obj.data.vertices)==len(b['vertices'])
 assert max(abs(x-y)for v,src in zip(obj.data.vertices,b['vertices'])for x,y in zip(v.co,(src['position'][0],src['position'][2],src['position'][1])))<1e-6
 faces=[tuple(reversed(b['indices'][t:t+3]))for t in range(0,len(b['indices']),3)];assert [tuple(p.vertices)for p in obj.data.polygons]==faces
 assert all(tuple(obj.data.uv_layers['UVMap'].data[loop].uv)==b['vertices'][obj.data.loops[loop].vertex_index]['uv']for loop in range(len(obj.data.loops)))
 assert d['geometry_end']==len(d['raw']);assert all(0<=i<len(b['vertices'])for i in b['indices'])
 obj.data.calc_loop_triangles();assert len(obj.data.loop_triangles)==row['triangles'];checks.append({'name':obj.name,'triangles':row['triangles'],'positionsUvsIndicesMatchSpm':True})
p=w/'final-blend-verification.json';a=json.loads(p.read_text());a['newCloudPrototypes']=checks;p.write_text(json.dumps(a,indent=2));print('V5_ALPHA_NATIVE_VERIFIED',flush=True)
from mathutils import Matrix
import xml.etree.ElementTree as E,hashlib
models={q['model']for q in json.loads((w/'smoke-changes.json').read_text())};bounds=[]
road=parse(w/'candidate/volcano_track.spm');roadbuf=next(b for b in road['buffers']if road['materials'][b['material']][0]=='track01.png');ceiling=max(v['position'][1]for v in roadbuf['vertices'])+3.5
for row in reg['nativeOriginalObjects']:
    xml=E.fromstring(row['sourceXml'])
    if xml.get('model')not in models:continue
    obj=bpy.data.objects[row['name']];assert obj.animation_data is None;xyz=list(map(float,xml.get('xyz').split()));scale=list(map(float,xml.get('scale').split()));matrix=Matrix.Translation((xyz[0],xyz[2],xyz[1]))@Matrix.Diagonal((scale[0],scale[2],scale[1],1));error=max(abs(obj.matrix_world[i][j]-matrix[i][j])for i in range(4)for j in range(4));assert error<.002
    minimum=min((obj.matrix_world@v.co).z for v in obj.data.vertices);assert minimum>ceiling
    bounds.append({'id':xml.get('id'),'model':xml.get('model'),'matrixMaxError':error,'minimumHeight':minimum,'roadHeightWithMargin':ceiling,'static':True})
assert len(bounds)==3
for row in reg['newPrototypes']:
    obj=bpy.data.objects[row['name']];assert obj.location.length<1e-7
    for mat in obj.data.materials:
        for node in mat.node_tree.nodes:
            if node.type=='TEX_IMAGE':
                image=node.image;assert image.packed_file;entry=reg['textures'][Path(image.filepath).name];assert hashlib.sha256(image.packed_file.data).hexdigest()==entry['sha256']
data=json.loads((w/'final-blend-verification.json').read_text());data['threeVolumetricPlumesAboveRoad']=bounds;data['newPrototypePalettePixelsMatchPool']=True;(w/'final-blend-verification.json').write_text(json.dumps(data,indent=2));print('V7B_NATIVE_AND_PLACEMENTS_VERIFIED',flush=True)
