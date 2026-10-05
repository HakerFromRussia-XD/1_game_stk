from pathlib import Path
import sys,json,hashlib,xml.etree.ElementTree as E,shutil,math
r=Path(__file__).resolve().parent;repo=Path('/Users/motoricallc/Downloads/fluxara-drift');f=r/'candidate';sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();b=parse(r/'before/motorsport-land_track.spm');a=parse(f/'motorsport-land_track.spm');remap=json.load(open(r/'material-remap.json'));keep=remap['retainedOriginalBuffers'];assert a['bounds']==b['bounds'];assert len(a['buffers'])==len(keep)
proof=[]
for aa,bi in zip(a['buffers'],keep):
 bb=b['buffers'][bi];assert aa['indices']==bb['indices'];assert len(aa['vertices'])==len(bb['vertices'])
 for va,vb in zip(aa['vertices'],bb['vertices']):assert va['position']==vb['position'] and va.get('normal')==vb.get('normal')
 if bi in [10,4]:assert [v['uv'] for v in aa['vertices']]==[v['uv'] for v in bb['vertices']]
 proof.append(bi)
for n in ['track.xml','graph.xml','quads.xml']:assert sha(f/n)==sha(r/'before'/n)
def sig(e):return [e.tag,sorted(e.attrib.items()),(e.text or '').strip(),[sig(q) for q in e]]
rows=json.load(open(r/'placements.json'));ids={x['name'] for x in rows};sx=E.parse(r/'before/scene.xml').getroot();sy=E.parse(f/'scene.xml').getroot();assert [sig(q) for q in sx if q.tag not in ['sun','sky-box']]==[sig(q) for q in sy if q.tag not in ['sun','sky-box'] and q.get('id') not in ids]
visual={'name','shader','gloss-map','normal-map','mirror-axis'}
oldmat={e.get('name'):e for e in E.parse(r/'before/materials.xml').getroot()};newmat={e.get('name'):e for e in E.parse(f/'materials.xml').getroot()}
def physical(e):return None if e is None else [{k:v for k,v in e.attrib.items() if k not in visual},[sig(q) for q in e]]
for bi,aa in zip(keep,a['buffers']):
 oldname=b['materials'][b['buffers'][bi]['material']][0];newname=a['materials'][aa['material']][0];po=physical(oldmat.get(oldname));pn=physical(newmat.get(newname))
 if po is None:po=[{},[]]
 if pn is None:pn=[{},[]]
 assert po==pn,(bi,oldname,newname,po,pn)
used={s for q in a['materials'] for s in q if s};used.update(sy.find('sky-box').get('texture').split());used.add('screenshot.jpg');used.update(q.get('gloss-map') for q in newmat.values() if q.get('name') in used and q.get('gloss-map'))
archive=r/'archived-unused';archive.mkdir(exist_ok=True);removed=[]
for p in f.iterdir():
 if p.suffix.lower() in ['.png','.jpg','.dds'] and p.name not in used:shutil.copy2(p,archive/p.name);p.unlink();removed.append(p.name)
tri=lambda d:sum(len(q['indices'])//3 for q in d['buffers']);libs={};refs=[]
for row in rows:
 n=row['library'];folder=repo/'iosApp/FluxaraResources/library'/n
 if n not in libs:
  s=E.parse(folder/'node.xml').getroot();models=[q.get('model') for q in s.findall('object') if q.get('model')];libs[n]=sum(tri(parse(folder/q)) for q in models);refs.append({'library':n,'folder':str(folder),'triangles':libs[n]})
oldtri=tri(b);newtri=tri(a)+sum(libs[x['library']] for x in rows);size=lambda p:sum(x.stat().st_size for x in p.iterdir() if x.is_file());original=size(r/'before');newshared=json.load(open(r/'new-shared-runtime.json'));sharedbytes=sum(x['bytes'] for x in newshared['libraries']);total=size(f)+sharedbytes
qs=[]
for e in E.parse(r/'before/quads.xml').getroot().findall('quad'):
 q=[]
 for j in range(4):
  s=e.get('p'+str(j));q.append(qs[int(s.split(':')[0])][int(s.split(':')[1])] if ':' in s else tuple(map(float,s.split())))
 qs.append(q)
for row in rows:
 if row['role']!='turn':continue
 i=row['quadIndex'];cs=lambda j:((qs[j][0][0]+qs[j][1][0])/2,(qs[j][0][2]+qs[j][1][2])/2);c,pr=cs(i),cs(i-6);dx,dz=c[0]-pr[0],c[1]-pr[1];h=math.hypot(dx,dz);rot=row['rotationZRadians'];assert -(math.sin(rot)*dx-math.cos(rot)*dz)/h>.99
result={'originalBytes':original,'trackFolderBytes':size(f),'newSharedBytes':sharedbytes,'trackAndNewSharedBytes':total,'byteChangePercent':100*(total/original-1),'originalTriangles':oldtri,'newTriangles':newtri,'triangleChangePercent':100*(newtri/oldtri-1),'newSharedPlacementCount':len(rows),'retainedOriginalBuffersPositionsNormalsIndicesExact':proof,'drivingRoadAndKerbUvExact':True,'protectedXmlExact':True,'allGameplaySceneNodesExact':True,'physicalMaterialPropertiesExact':True,'weightNotIncreased':total<=original,'triangleBudgetPassed':.8*oldtri<=newtri<=1.2*oldtri,'sourceUnusedTexturesArchived':removed}
(r/'preservation-audit.json').write_text(json.dumps(result,indent=2));(r/'shared-runtime.json').write_text(json.dumps({'libraries':refs,'newExports':newshared['libraries'],'placements':rows,'instances':len(rows),'newLibraryBytes':sharedbytes},indent=2));print(json.dumps(result));assert result['weightNotIncreased'] and result['triangleBudgetPassed']
