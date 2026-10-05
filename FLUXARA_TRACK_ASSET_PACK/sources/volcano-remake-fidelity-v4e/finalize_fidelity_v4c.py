"""Build a separate editable draft without replacing the delivered track or donors."""
from pathlib import Path
import bpy
import json
import sys

r=Path(__file__).resolve().parent
work=r/'fidelity-v4c'
code=(r/'finalize.py').read_text()
old="f=r/'candidate';out=r.parent/'fluxara-user-volcano-remake-final'"
new="f=r/'fidelity-v4c/candidate';out=r/'fidelity-v4c/native'"
assert old in code
code=code.replace(old,new)
code=code.replace("tex=pack/'textures/volcano-remake-reference-v1';mod=pack/'models/volcano-remake-reference-v1';sources=pack/'sources/volcano-remake-reference-v1'",
                  "tex=pack/'textures/volcano-remake-fidelity-v4c';mod=pack/'models/volcano-remake-fidelity-v4c';sources=pack/'sources/volcano-remake-fidelity-v4c'")
code=code.replace("(r/'asset-registration.json')", "(r/'fidelity-v4c/asset-registration.json')")
code=code.replace("'VRV1_'", "'VRV4C_'")
code=code.replace("'volcano-v1-'", "'volcano-fidelity-v4c-'")
code=code.replace("'volcano-v1-material-'", "'volcano-fidelity-v4c-material-'")
code=code.replace("'VR_Prototype_'", "'VRV4C_Prototype_'")
code=code.replace("target=tex/name", "target=(tex/name) if name=='vr_volcanic_smoke.png' else pack/'textures/volcano-remake-fidelity-v3'/name")
code=code.replace("shutil.copy2(p,target)\n texture_sources", "if not target.exists():shutil.copy2(p,target)\n else:assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(target.read_bytes()).digest(), ('Unexpected donor mutation',name)\n texture_sources")
code=code.replace("'mansion_windows.png','chain.png','torch.png'", "'mansion_windows.png','chain.png','torch.png','vr_volcanic_smoke.png'")
exec(compile(code,str(r/'finalize.py'),'exec'))
print('FIDELITY_NATIVE_BASE_READY',work/'native/Volcano Remake.blend',flush=True)
