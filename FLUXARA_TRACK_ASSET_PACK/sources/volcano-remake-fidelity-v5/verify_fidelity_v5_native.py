from pathlib import Path
import bpy,json,sys
r=Path(__file__).resolve().parent;w=r/'fidelity-v5';code=(r/'verify_blend.py').read_text().replace("r/'asset-registration.json'","r/'fidelity-v5/asset-registration.json'").replace("r/'candidate'","r/'fidelity-v5/candidate'").replace("r/'final-blend-verification.json'","r/'fidelity-v5/final-blend-verification.json'");exec(compile(code,str(r/'verify_blend.py'),'exec'))
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
reg=json.loads((w/'asset-registration.json').read_text());checks=[]
for row in reg['newPrototypes']:
 obj=bpy.data.objects[row['name']];d=parse(row['sourceModel']);b=d['buffers'][0];assert len(obj.data.vertices)==len(b['vertices'])
 assert max(abs(x-y)for v,src in zip(obj.data.vertices,b['vertices'])for x,y in zip(v.co,(src['position'][0],src['position'][2],src['position'][1])))<1e-6
 faces=[tuple(reversed(b['indices'][t:t+3]))for t in range(0,len(b['indices']),3)];assert [tuple(p.vertices)for p in obj.data.polygons]==faces
 assert all(tuple(obj.data.uv_layers['UVMap'].data[loop].uv)==b['vertices'][obj.data.loops[loop].vertex_index]['uv']for loop in range(len(obj.data.loops)))
 obj.data.calc_loop_triangles();assert len(obj.data.loop_triangles)==row['triangles'];checks.append({'name':obj.name,'triangles':row['triangles'],'positionsUvsIndicesMatchSpm':True})
p=w/'final-blend-verification.json';a=json.loads(p.read_text());a['newCloudPrototypes']=checks;p.write_text(json.dumps(a,indent=2));print('V5_NATIVE_VERIFIED',flush=True)
