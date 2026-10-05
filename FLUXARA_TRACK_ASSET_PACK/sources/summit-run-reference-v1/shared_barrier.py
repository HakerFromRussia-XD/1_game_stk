from pathlib import Path
import sys,json,shutil,struct,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK';sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse,rewrite_texture_names
src=pack/'models/ski-dash-clean-barrier-v2/fluxara_driftlib_skiDashBarrier_a_main.spm';name='fluxara_driftlib_alpine_coral_barrier_v1';out=pack/'models/summit-run-reference-v1/runtime-library'/name;out.mkdir(parents=True,exist_ok=True);d=parse(src)
for b in d['buffers']:
 for v in b['vertices']:struct.pack_into('<2e',d['raw'],v['uv_offset'],.375,.875)
(out/'alpine_coral_barrier_main.spm').write_bytes(rewrite_texture_names(d,[['dp_palette.png',''] for _ in d['materials']]))
root=E.Element('scene');E.SubElement(root,'object',id='AlpineCoralBarrier',model='alpine_coral_barrier_main.spm',type='animation',xyz='0 0 0',hpr='0 0 0',scale='1 1 1',interaction='ghost',**{'skeletal-animation':'false'});E.ElementTree(root).write(out/'node.xml',encoding='unicode');E.ElementTree(E.Element('materials')).write(out/'materials.xml',encoding='unicode');shutil.copytree(out,repo/'iosApp/FluxaraResources/library'/name,dirs_exist_ok=True)
a=json.load(open(r/'new-shared-runtime.json'));a['libraries']=[q for q in a['libraries'] if q['library']!=name]+[{'library':name,'path':str(out),'bytes':sum(p.stat().st_size for p in out.iterdir() if p.is_file()),'source':str(src),'reuseTier':'adapt','adaptation':'Pooled red-white barrier geometry and vertex colors retained; only UV/texture name uses existing white palette swatch'}];(r/'new-shared-runtime.json').write_text(json.dumps(a,indent=2));print('BARRIER_REUSED')
