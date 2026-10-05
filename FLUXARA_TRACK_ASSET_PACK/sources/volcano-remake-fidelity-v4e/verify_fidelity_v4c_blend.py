from pathlib import Path
import bpy
r=Path(__file__).resolve().parent
code=(r/'verify_blend.py').read_text()
code=code.replace("r/'asset-registration.json'", "r/'fidelity-v4c/asset-registration.json'")
code=code.replace("r/'candidate'", "r/'fidelity-v4c/candidate'")
code=code.replace("r/'final-blend-verification.json'", "r/'fidelity-v4c/final-blend-verification.json'")
exec(compile(code,str(r/'verify_blend.py'),'exec'))
portal=bpy.data.objects['VRV4C_StonePortal']
portal.data.calc_loop_triangles()
assert len(portal.data.loop_triangles)==300
assert portal.hide_render
print('FIDELITY_PORTAL_VERIFIED',len(portal.data.loop_triangles),flush=True)
