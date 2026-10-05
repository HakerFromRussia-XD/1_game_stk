"""Restore thin smoke effects as transparent original cards, in an isolated draft."""
from pathlib import Path
import json,shutil,hashlib,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;work=r/'fidelity-v4';candidate=work/'candidate'
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
shutil.copytree(r/'fidelity-v3/candidate',candidate,dirs_exist_ok=True)
names=['AshCloud2.spm','AshCloudEffect.spm','AshColumnEffect.spm','EruptionAsh.spm'];rows=[]
for name in names:
 original=r/'before'/name;old=parse(original);previous=parse(r/'fidelity-v3/candidate'/name)
 shutil.copy2(original,candidate/name)
 rows.append({'model':name,'beforeTriangles':sum(len(b['indices'])//3 for b in previous['buffers']),'restoredTriangles':sum(len(b['indices'])//3 for b in old['buffers']),'geometry':'Original transparent-card geometry and UVs restored byte-for-byte','originalSha256':hashlib.sha256(original.read_bytes()).hexdigest()})
tree=E.parse(candidate/'materials.xml');root=tree.getroot()
entry=next(e for e in root if e.get('name')=='gfx_snowStormAnimated_a.png');assert entry.get('shader')=='solid';entry.set('shader','alphablend');tree.write(candidate/'materials.xml',encoding='unicode')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert all(sha(r/'fidelity-v3/candidate'/n)==sha(candidate/n) for n in ['volcano_track.spm','scene.xml','quads.xml','graph.xml','track.xml','scripting.as'])
(work/'changes.json').write_text(json.dumps({'parent':'V3','reference':'Figma 378:39','models':rows,'material':'gfx_snowStormAnimated_a.png: solid -> alphablend','newTexture':'Transparent generated billow cluster repeated in the original sixteen-frame vertical atlas layout','productionIntegrated':False,'roadAndGameplayFilesEqualV3':True},indent=2))
print('V4_SMOKE_CARDS_READY',rows)
