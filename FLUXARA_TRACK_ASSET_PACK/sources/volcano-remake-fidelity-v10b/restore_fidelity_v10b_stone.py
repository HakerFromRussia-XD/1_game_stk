from pathlib import Path
import sys,json,struct,shutil,hashlib
r=Path(__file__).resolve().parent;w=r/'fidelity-v10b';w.mkdir(exist_ok=True);c=w/'candidate';shutil.copytree(r/'fidelity-v10/candidate',c,dirs_exist_ok=True);sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse,rewrite_texture_names
changes=json.loads((r/'fidelity-v10/cliff-changes.json').read_text())
for row in changes:
 name=row['model'];d=parse(c/name);old=parse(r/'fidelity-v9/candidate'/name);materials=[list(v)for v in d['materials']]
 for q in row['buffers']:
  b=d['buffers'][q['buffer']];src=old['buffers'][q['buffer']];assert len(b['vertices'])==len(src['vertices'])
  for v,u in zip(b['vertices'],src['vertices']):assert v['position']==u['position'];struct.pack_into('<2e',d['raw'],v['uv_offset'],*u['uv'])
  materials[b['material']]=old['materials'][src['material']]
 (c/name).write_bytes(rewrite_texture_names(d,materials))
shutil.copy2(r/'fidelity-v9/candidate/Rock13_col.jpg',c/'Rock13_col.jpg');shutil.copy2(r/'fidelity-v9/candidate/materials.xml',c/'materials.xml')
(w/'stone-restoration.json').write_text(json.dumps({'userRequest':'С текстурой камня было лучше','restoredTexture':'Rock13_col.jpg','restoredTextureSha256':hashlib.sha256((c/'Rock13_col.jpg').read_bytes()).hexdigest(),'restoredUvsAndTextureBindingsExactV9':True,'retainedSmootherDecorativeNormalsExactV10':True,'redRoofTowerLibraryRetained':'fluxara_driftlib_volcano_castle_tower_v9','models':[q['model']for q in changes],'productionIntegrated':False},ensure_ascii=False,indent=2));print('V10B_STONE_TEXTURE_AND_UVS_RESTORED',flush=True)
