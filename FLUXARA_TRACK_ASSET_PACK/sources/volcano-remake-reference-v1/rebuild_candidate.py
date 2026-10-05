from pathlib import Path
import subprocess,sys
r=Path(__file__).resolve().parent;node='/Users/motoricallc/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
# Reproducible candidate; original baseline and approved donor files remain outside the output.
steps=[[node,str(r/'prepare_palette.js')],[sys.executable,str(r/'stage.py')],[sys.executable,str(r/'polish_materials.py')],[sys.executable,str(r/'polish_smoke_uv.py')],[node,str(r/'smoke_atlas.js')],[sys.executable,str(r/'remove_legacy_bump_maps.py')],[sys.executable,str(r/'reskin_arch.py')],['/Applications/Blender.app/Contents/MacOS/Blender','-b','-t','4','-P',str(r/'layout.py')],[sys.executable,str(r/'scale_smoke.py')],[node,str(r/'cloud_palette.js')],['/Applications/Blender.app/Contents/MacOS/Blender','-b','-t','4','-P',str(r/'smoke_volumes.py')],[sys.executable,str(r/'audit.py')]]
if __name__=='__main__':
 for cmd in steps:subprocess.run(cmd,check=True)
