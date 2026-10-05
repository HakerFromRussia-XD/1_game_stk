"""Build a separate editable draft without replacing the delivered track or donors."""
from pathlib import Path
import bpy
import json
import sys

r=Path(__file__).resolve().parent
work=r/'fidelity-v2'
code=(r/'finalize.py').read_text()
old="f=r/'candidate';out=r.parent/'fluxara-user-volcano-remake-final'"
new="f=r/'fidelity-v2/candidate';out=r/'fidelity-v2/native'"
assert old in code
code=code.replace(old,new)
code=code.replace("tex=pack/'textures/volcano-remake-reference-v1';mod=pack/'models/volcano-remake-reference-v1';sources=pack/'sources/volcano-remake-reference-v1'",
                  "tex=pack/'textures/volcano-remake-fidelity-v2';mod=pack/'models/volcano-remake-fidelity-v2';sources=pack/'sources/volcano-remake-fidelity-v2'")
code=code.replace("(r/'asset-registration.json')", "(r/'fidelity-v2/asset-registration.json')")
code=code.replace("'VRV1_'", "'VRV2_'")
code=code.replace("'volcano-v1-'", "'volcano-fidelity-v2-'")
code=code.replace("'volcano-v1-material-'", "'volcano-fidelity-v2-material-'")
code=code.replace("'VR_Prototype_'", "'VRV2_Prototype_'")
exec(compile(code,str(r/'finalize.py'),'exec'))
print('FIDELITY_NATIVE_BASE_READY',work/'native/Volcano Remake.blend',flush=True)
