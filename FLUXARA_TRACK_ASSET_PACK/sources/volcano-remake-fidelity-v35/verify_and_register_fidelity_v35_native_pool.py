from pathlib import Path
r=Path(__file__).resolve().parent
for name in ['repair_fidelity_v35_floor_provenance.py','verify_fidelity_v35_native.py','register_fidelity_v35_canonical.py','verify_fidelity_v35_canonical.py']:
 exec(compile((r/name).read_text(),str(r/name),'exec'),{'__file__':str(r/name),'__name__':'__main__'})
print('V35_NATIVE_CANONICAL_PIPELINE_COMPLETE',flush=True)
