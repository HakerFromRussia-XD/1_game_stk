from pathlib import Path
import bpy
r=Path(__file__).resolve().parent
code=(r/'register_canonical.py').read_text()
code=code.replace("r/'asset-registration.json'", "r/'fidelity-v2/asset-registration.json'")
code=code.replace("r/'canonical-before-volcano-remake.blend'", "r/'fidelity-v2/canonical-before-fidelity-v2.blend'")
code=code.replace("'volcano-v1-'", "'volcano-fidelity-v2-'")
code=code.replace("'VRV1_'", "'VRV2_'")
code=code.replace("'Volcano Remake Shared Assets'", "'Volcano Remake Candidate V2 Assets'")
code=code.replace("r/'canonical-registration.json'", "r/'fidelity-v2/canonical-registration.json'")
exec(compile(code,str(r/'register_canonical.py'),'exec'))
