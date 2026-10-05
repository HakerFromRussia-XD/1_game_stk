from pathlib import Path
import sys,shutil,json,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v5-alpha';c=w/'candidate';w.mkdir(exist_ok=True);shutil.copytree(r/'fidelity-v4e/candidate',c,dirs_exist_ok=True)
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse,rewrite_texture_names
rows=[]
for name in ['AshCloud.spm','AshColumn.spm','PyroclasticFlow.spm']:
 d=parse(r/'before'/name);assert len(d['materials'])==1;original=[m[:]for m in d['materials']];names=[['vr_volcanic_smoke.png',m[1]]for m in d['materials']];raw=rewrite_texture_names(d,names);(c/name).write_bytes(raw);new=parse(c/name)
 assert new['bounds']==d['bounds'] and new['buffers']==d['buffers'] or all(a['indices']==b['indices']and all(all(v.get(k)==u.get(k)for k in ['position','normal','uv','color'])for v,u in zip(a['vertices'],b['vertices']))for a,b in zip(d['buffers'],new['buffers']))
 rows.append({'model':name,'geometry':'Original positions, normals, UVs, indices and bounds restored; only texture-table name changed.','triangles':sum(len(b['indices'])//3 for b in d['buffers']),'originalMaterials':original,'newMaterials':names,'originalBytes':len(d['raw']),'candidateBytes':len(raw)})
mt=E.parse(c/'materials.xml');next(m for m in mt.getroot()if m.get('name')=='vr_volcanic_smoke.png').set('shader','alphablend');mt.write(c/'materials.xml',encoding='unicode');(w/'changes.json').write_text(json.dumps(rows,indent=2));print('V5_ALPHA_CANDIDATE_READY',rows)
