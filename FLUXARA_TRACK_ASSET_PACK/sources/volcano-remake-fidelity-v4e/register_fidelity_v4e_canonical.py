from pathlib import Path
import bpy
r=Path(__file__).resolve().parent
code=(r/'register_canonical.py').read_text()
code=code.replace("r/'asset-registration.json'", "r/'fidelity-v4e/asset-registration.json'")
code=code.replace("r/'canonical-before-volcano-remake.blend'", "r/'fidelity-v4e/canonical-before-fidelity-v4e.blend'")
code=code.replace("'volcano-v1-'", "'volcano-fidelity-v4e-'")
code=code.replace("'VRV1_'", "'VRV4E_'")
code=code.replace("'Volcano Remake Shared Assets'", "'Volcano Remake Candidate V4E Assets'")
code=code.replace("r/'canonical-registration.json'", "r/'fidelity-v4e/canonical-registration.json'")
exec(compile(code,str(r/'register_canonical.py'),'exec'))
