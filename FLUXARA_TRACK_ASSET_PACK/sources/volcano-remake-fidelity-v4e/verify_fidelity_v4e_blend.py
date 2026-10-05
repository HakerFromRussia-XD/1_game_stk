from pathlib import Path
import bpy
r=Path(__file__).resolve().parent
code=(r/'verify_blend.py').read_text()
code=code.replace("r/'asset-registration.json'", "r/'fidelity-v4e/asset-registration.json'")
code=code.replace("r/'candidate'", "r/'fidelity-v4e/candidate'")
code=code.replace("r/'final-blend-verification.json'", "r/'fidelity-v4e/final-blend-verification.json'")
exec(compile(code,str(r/'verify_blend.py'),'exec'))
portal=bpy.data.objects['VRV4E_StonePortal']
portal.data.calc_loop_triangles()
assert len(portal.data.loop_triangles)==300
assert portal.hide_render
print('FIDELITY_PORTAL_VERIFIED',len(portal.data.loop_triangles),flush=True)
import json,sys
sys.path.insert(0,str(r.parent/'shared-object-redesign'))
from spm_io import parse
work=r/'fidelity-v4e';reg=json.loads((work/'asset-registration.json').read_text());checks=[]
for row in reg['objects']:
 if '-effect-' not in row['id']:continue
 obj=bpy.data.objects[row['name']];source=parse(row['sourceModel']);verts=[v for b in source['buffers'] for v in b['vertices']]
 expected=[(v['position'][0],v['position'][2],v['position'][1]) for v in verts]
 assert len(obj.data.vertices)==len(expected)
 assert max(abs(a-b) for v,e in zip(obj.data.vertices,expected) for a,b in zip(v.co,e))<1e-6
 obj.data.calc_loop_triangles();assert len(obj.data.loop_triangles)==sum(len(b['indices'])//3 for b in source['buffers'])
 assert all(tuple(loop.uv) in [(0,0),(0,1),(1,0),(1,1)] for loop in obj.data.uv_layers['UVMap'].data)
 checks.append({'name':obj.name,'triangles':len(obj.data.loop_triangles),'vertexPositionsExactWithin':1e-6,'uvCornersExact':True,'bothSidesRetained':True})
assert len(checks)==5
path=work/'final-blend-verification.json';result=json.loads(path.read_text());result['smokePrototypes']=checks;result['portalTriangles']=300;result['registeredPrototypes']=len(reg['objects']);path.write_text(json.dumps(result,indent=2));print('FIDELITY_SMOKE_NATIVE_VERIFIED',flush=True)
