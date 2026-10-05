from pathlib import Path
import sys,xml.etree.ElementTree as E,json
r=Path(__file__).resolve().parent;repo=Path('/Users/motoricallc/Downloads/fluxara-drift');sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
scene=E.parse(r/'before/scene.xml').getroot();rows={}
for name in sorted(set(q.get('name') for q in scene.findall('library'))):
 folder=repo/'iosApp/FluxaraResources/library'/name;root=E.parse(folder/'node.xml').getroot();vs=[];tri=0;models=[e for e in root.findall('object') if e.get('model') and e.get('interaction')!='physicsonly']
 for group in root.findall('./lod/group'):
  if list(group):models.append(list(group)[0])
 for q in models:
  d=parse(folder/q.get('model'));tri+=sum(len(b['indices'])//3 for b in d['buffers']);vs.extend(v['position'] for b in d['buffers'] for v in b['vertices'])
 physics=[q for q in root.findall('object') if q.get('interaction')=='physicsonly']
 rows[name]={'visualBounds':[[min(v[k] for v in vs),max(v[k] for v in vs)] for k in range(3)] if vs else None,'triangles':tri,'physics':[dict(q.attrib) for q in physics],'instances':sum(q.get('name')==name for q in scene.findall('library'))}
(r/'shared-source-inspection.json').write_text(json.dumps(rows,indent=2));print('ORIGINAL_MAIN_PLUS_INSTANCES',187169+sum(q['triangles']*q['instances'] for q in rows.values()))
