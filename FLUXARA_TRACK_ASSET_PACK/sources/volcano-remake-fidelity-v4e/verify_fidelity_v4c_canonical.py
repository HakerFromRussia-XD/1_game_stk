from pathlib import Path
import bpy
r=Path(__file__).resolve().parent
code=(r/'verify_canonical.py').read_text()
code=code.replace("'volcano-remake-rework']", "'volcano-remake-rework','volcano-remake-rework/fidelity-v4c']")
code=code.replace("root/'volcano-remake-rework/canonical-bindings-verification.json'", "root/'volcano-remake-rework/fidelity-v4c/canonical-bindings-verification.json'")
exec(compile(code,str(r/'verify_canonical.py'),'exec'))
for name in ['fluxara_chalet_window','fluxara_cottage_windows',
             'LCV1_fluxara_chalet_window.png','LCV1_fluxara_cottage_windows.png']:
    material=bpy.data.materials[name]
    emit=[n for n in material.node_tree.nodes if n.type=='EMISSION']
    assert emit and all(n.inputs['Strength'].default_value>=1 for n in emit),name
print('SHARED_WINDOW_EMISSION_PRESERVED',flush=True)
