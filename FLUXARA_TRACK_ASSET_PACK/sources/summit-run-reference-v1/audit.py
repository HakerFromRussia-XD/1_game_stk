from pathlib import Path
import sys,json,hashlib,xml.etree.ElementTree as E,shutil
r=Path(__file__).resolve().parent;repo=Path('/Users/motoricallc/Downloads/fluxara-drift');f=r/'candidate';sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();tri=lambda p:sum(len(b['indices'])//3 for b in parse(p)['buffers']);b=r/'before'
protected=['iceCube.spm','fallRock.spm','treeMod1_LOD80.spm','treeMod1_LOD170.spm','track.xml','quads.xml','graph.xml','ansu.music','horo.ogg','horoF.ogg']
for n in protected:assert sha(b/n)==sha(f/n),n
a,d=parse(f/'ancient-summits_track.spm'),parse(b/'ancient-summits_track.spm');assert a['bounds']==d['bounds'] and a['materials']==d['materials'] and len(a['buffers'])==len(d['buffers'])
for i,(x,y) in enumerate(zip(a['buffers'],d['buffers'])):
 assert x['indices']==y['indices'] and len(x['vertices'])==len(y['vertices'])
 for v,w in zip(x['vertices'],y['vertices']):
  assert v['position']==w['position'] and v.get('normal')==w.get('normal')
  if i!=9:assert v['uv']==w['uv']
for n in ['treeMod1_LOD80.spm','treeMod1_LOD170.spm','Balloon.spm']:
 a,d=parse(f/n),parse(b/n);assert a['bounds']==d['bounds']
 for x,y in zip(a['buffers'],d['buffers']):assert x['indices']==y['indices'] and all(v['position']==w['position'] and v.get('normal')==w.get('normal') and v['uv']==w['uv'] for v,w in zip(x['vertices'],y['vertices']))
def sig(e):return [e.tag,sorted(e.attrib.items()),(e.text or '').strip(),[sig(q) for q in e]]
rows=json.load(open(r/'placements.json'));ids={q['name'] for q in rows};old=E.parse(b/'scene.xml').getroot();new=E.parse(f/'scene.xml').getroot();assert [sig(q) for q in old if q.tag not in ['sun','sky-box','track']]==[sig(q) for q in new if q.tag not in ['sun','sky-box','track'] and q.get('id') not in ids]
assert old.find('track').attrib==new.find('track').attrib
for a,c in zip(old.find('track'),new.find('track')):
 assert all(a.get(k)==c.get(k) for k in ['xyz','hpr','scale'])
 assert c.get('model')=='treeMod1_LOD80.spm' and c.get('interaction')=='physics-only'
om=E.parse(b/'materials.xml').getroot();nm=E.parse(f/'materials.xml').getroot();assert all(sig(q)==sig(next(x for x in nm if x.get('name')==q.get('name'))) for q in om)
# The old tree geometry is loaded as an exact collision-only static mesh and its render node is removed.
allspm=[parse(p) for p in f.glob('*.spm')];used={s for d in allspm for pair in d['materials'] for s in pair if s};used|={n.replace('stk','fluxara_drift') for n in used};used.update(new.find('sky-box').get('texture').split());used.add('screenshot.png');used.update(q.get('gloss-map') for q in nm if q.get('gloss-map'))
archive=r/'archived-unused';archive.mkdir(exist_ok=True);removed=[]
for p in f.iterdir():
 if p.suffix.lower() in ['.png','.jpg','.dds'] and p.name not in used:shutil.copy2(p,archive/p.name);p.unlink();removed.append(p.name)
libs={};refs=[]
for q in rows:
 n=q['library'];folder=repo/'iosApp/FluxaraResources/library'/n
 if n not in libs:
  s=E.parse(folder/'node.xml').getroot();models=[o.get('model') for o in s.findall('object') if o.get('model') and o.get('interaction')!='physicsonly']+[list(g)[0].get('model') for g in s.findall('./lod/group')];libs[n]=sum(tri(folder/m) for m in models);refs.append({'library':n,'folder':str(folder),'triangles':libs[n]})
ot=tri(b/'ancient-summits_track.spm')+32*tri(b/'treeMod1_LOD80.spm')+sum(tri(b/o.get('model')) for o in old.findall('object') if o.get('model'));nt=ot-32*tri(b/'treeMod1_LOD80.spm')+sum(libs[q['library']] for q in rows)
size=lambda p:sum(q.stat().st_size for q in p.iterdir() if q.is_file());shared=json.load(open(r/'new-shared-runtime.json'));sb=sum(q['bytes'] for q in shared['libraries']);total=size(f)+sb
result={'originalBytes':size(b),'trackFolderBytes':size(f),'newSharedBytes':sb,'trackAndNewSharedBytes':total,'byteChangePercent':100*(total/size(b)-1),'originalTriangles':ot,'newTriangles':nt,'triangleChangePercent':100*(nt/ot-1),'newSharedPlacementCount':len(rows),'protectedFilesByteExact':protected,'allMainMeshPositionsNormalsIndicesExact':True,'allMainUvExactExceptSnowCliffBuffer9':True,'allOriginalSceneGameplayAndTreeTransformsExact':True,'treeColliderGeometryNormalsIndicesUvExact':True,'animatedBalloonGeometryNormalsUvIndicesExact':True,'originalMaterialDefinitionsExact':True,'weightNotIncreased':total<=size(b),'triangleBudgetPassed':.8*ot<=nt<=1.2*ot,'logicalVisualCountExcludesHiddenOriginalTreeColliders':True,'sourceUnusedTexturesArchived':removed}
(r/'preservation-audit.json').write_text(json.dumps(result,indent=2));(r/'shared-runtime.json').write_text(json.dumps({'libraries':refs,'newExports':shared['libraries'],'placements':rows,'instances':len(rows),'newLibraryBytes':sb},indent=2));print(json.dumps(result));assert result['weightNotIncreased'] and result['triangleBudgetPassed']
