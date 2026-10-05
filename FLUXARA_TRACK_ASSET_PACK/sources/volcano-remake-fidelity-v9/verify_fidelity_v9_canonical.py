from pathlib import Path
import bpy,json
r=Path(__file__).resolve().parent;code=(r/'verify_canonical.py').read_text().replace("'volcano-remake-rework']","'volcano-remake-rework','volcano-remake-rework/fidelity-v4e','volcano-remake-rework/fidelity-v5','volcano-remake-rework/fidelity-v5-alpha','volcano-remake-rework/fidelity-v7b','volcano-remake-rework/fidelity-v8b','volcano-remake-rework/fidelity-v9']").replace("root/'volcano-remake-rework/canonical-bindings-verification.json'","root/'volcano-remake-rework/fidelity-v9/canonical-bindings-verification.json'");exec(compile(code,str(r/'verify_canonical.py'),'exec'))
for name in ['fluxara_chalet_window','fluxara_cottage_windows','LCV1_fluxara_chalet_window.png','LCV1_fluxara_cottage_windows.png']:
 nodes=[n for n in bpy.data.materials[name].node_tree.nodes if n.type=='EMISSION'];assert nodes and all(n.inputs['Strength'].default_value>=1 for n in nodes)
print('V5_SHARED_WINDOWS_VERIFIED',flush=True)
