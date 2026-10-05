from pathlib import Path
import collections,copy,hashlib,json,math,shutil,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v37';w.mkdir(exist_ok=True);c=w/'candidate';
if c.exists():
 assert not(w/'rim-preflight.json').exists();assert all((c/f.name).read_bytes()==f.read_bytes()for f in (r/'fidelity-v36/candidate').iterdir()if f.is_file())
else:shutil.copytree(r/'fidelity-v36/candidate',c)
res=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources');sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
from terrain_triangle_distance import triangle_distance,point_triangle_distance
tree=E.parse(c/'scene.xml');root=tree.getroot();plants=json.loads((r/'fidelity-v36/plant-grounding.json').read_text())['placements'];groups=json.loads((r/'fidelity-v32/seam-changes.json').read_text())['placements']
def tris(d):return [[b['vertices'][i]['position']for i in b['indices'][j:j+3]]for b in d['buffers']for j in range(0,len(b['indices']),3)]
def params(a):return list(map(float,a['xyz'].split())),list(map(float,a['scale'].split())),math.radians(float(a['hpr'].split()[1]))
def world(v,a):
 p,s,y=params(a);co,si=math.cos(y),math.sin(y);return(p[0]+co*v[0]*s[0]+si*v[2]*s[2],p[1]+v[1]*s[1],p[2]-si*v[0]*s[0]+co*v[2]*s[2])
def box(vv):return tuple(min(v[k]for v in vv)for k in range(3))+tuple(max(v[k]for v in vv)for k in range(3))
def dsq(a,b):return sum(max(a[k]-b[k+3],b[k]-a[k+3],0)**2 for k in range(3))
main=parse(c/'volcano_track.spm');road=[t for b in main['buffers']if main['materials'][b['material']][0]in ['track01.png','stktex_generic_WoodA.png','stkflag_blackBooster_a.png','stkflag_blackBooster_b.png','stk_generic_gridA.png','stk_generic_gravalSnow_a.png']for t in tris({'buffers':[b]})]
for e in root.findall('object'):
 if e.get('driveable')=='true':road.extend([[world(v,e.attrib)for v in t]for t in tris(parse(c/e.get('model')))])
assert len(road)==2032;rb=[box(t)for t in road];cache={};sources=[]
def model(lib):
 if lib not in cache:
  folder=res/'library'/lib;node=E.parse(folder/'node.xml').getroot().find('object');assert node.get('interaction')=='ghost'and node.get('xyz')=='0 0 0'and node.get('scale')=='1 1 1';path=folder/node.get('model');cache[lib]=parse(path);sources.append({'path':str(path),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
 return cache[lib]
def certificate(attrs,required=.25):
 tt=[[world(v,attrs)for v in t]for t in tris(model(attrs['name']))];whole=box([v for t in tt for v in t]);near=[(t,b)for t,b in zip(road,rb)if dsq(whole,b)<=required**2]
 pairs=0;best=math.inf
 for t in tt:
  b=box(t)
  for q,qb in near:
   if dsq(b,qb)<=required**2:
    d=triangle_distance(t,q);best=min(best,d);pairs+=1
    if d<=required:return False,{'requiredMeters':required,'exactNearTrianglePairChecks':pairs,'rejectedDistance':d}
 return True,{'requiredMeters':required,'exactNearTrianglePairChecks':pairs,'nearRoadTriangleCount':len(near),'geometryTriangles':len(tt),'minimumNearPairDistance':best if math.isfinite(best)else None,'allOtherTrianglePairsAABBLowerBoundGreaterThanRequired':True}
gd=model('fluxara_driftlib_volcano_grass_cap_v32');cap_anchor=gd['bounds'][1];thickness=gd['bounds'][4]-cap_anchor;rows=[];rejected=[]
for cap in [e for e in root.findall('library')if e.get('name')=='fluxara_driftlib_volcano_grass_cap_v32']:
 old=dict(cap.attrib);pos,scale,yaw=params(old);width=max((gd['bounds'][3]-gd['bounds'][0])*scale[0],(gd['bounds'][5]-gd['bounds'][2])*scale[2]);target=max(scale[1]*thickness,min(8.,max(2.8,width*.125)));newsy=target/thickness
 children=[q for q in plants if q['supportingGrassPlacementId']==cap.get('id')];tg=next((q for q in groups if q['parts'][1]['id']==cap.get('id')),None);chosen=None
 for fraction in [1.,.75,.5,.25,0.]:
  sy=scale[1]+fraction*(newsy-scale[1]);attrs=copy.deepcopy(old);attrs['scale']=' '.join(f'{v:.8f}'for v in [scale[0],sy,scale[2]]);attrs['xyz']=' '.join(f'{v:.8f}'for v in [pos[0],pos[1]+cap_anchor*(scale[1]-sy),pos[2]]);np,ns,_=params(attrs);ok,proof=certificate(attrs);linked=[]
  if not ok:rejected.append({'id':cap.get('id'),'fraction':fraction,'role':'cap','proof':proof});continue
  for q in children:
   e=root.find('library[@id="'+q['after']['id']+'"]');a=dict(e.attrib);ep,es,_=params(a);oldh=q['sampledTopHeights'][0]if q['role']=='Bush'else min(q['sampledTopHeights']);newh=np[1]+(oldh-pos[1])*ns[1]/scale[1];a['xyz']=' '.join(f'{v:.8f}'for v in [ep[0],ep[1]+newh-oldh,ep[2]]);valid,pr=certificate(a)
   if not valid:ok=False;rejected.append({'id':cap.get('id'),'fraction':fraction,'role':q['role'],'proof':pr});break
   linked.append({'before':dict(e.attrib),'after':a,'proof':pr,'sourceGroundingRole':q['role']})
  if not ok:continue
  if tg:
   e=root.find('library[@id="'+tg['parts'][2]['id']+'"]');a=dict(e.attrib);ep,es,_=params(a);local=tg['treeBaseOnCapLocalPoint'];ep[1]=np[1]+local[1]*ns[1];a['xyz']=' '.join(f'{v:.8f}'for v in ep);valid,pr=certificate(a)
   if not valid:rejected.append({'id':cap.get('id'),'fraction':fraction,'role':'tree','proof':pr});continue
   linked.append({'before':dict(e.attrib),'after':a,'proof':pr,'sourceGroundingRole':'Tree'})
  chosen=(attrs,proof,linked,fraction);break
 assert chosen is not None,cap.attrib;attrs,proof,linked,fraction=chosen;cap.attrib.clear();cap.attrib.update(attrs)
 for q in linked:e=root.find('library[@id="'+q['after']['id']+'"]');e.attrib.clear();e.attrib.update(q['after'])
 rows.append({'before':old,'after':attrs,'beforeLipHeightMeters':scale[1]*thickness,'afterLipHeightMeters':float(attrs['scale'].split()[1])*thickness,'bottomInterfaceWorldHeightBefore':pos[1]+cap_anchor*scale[1],'bottomInterfaceWorldHeightAfter':np[1]+cap_anchor*ns[1],'selectedIncreaseFraction':fraction,'sourceGeometryUnchanged':True,'clearanceProof':proof,'linkedPlants':linked});print('V37_RIM_READY',cap.get('id'),fraction,rows[-1]['beforeLipHeightMeters'],rows[-1]['afterLipHeightMeters'],flush=True)
unused=c/'Lava_004_NORM.jpg';assert unused.is_file();refs={n for f in c.glob('*.spm')for pair in parse(f)['materials']for n in pair if n};assert unused.name not in refs
assert all(unused.name not in f.read_text()for f in c.iterdir()if f.suffix in ['.xml','.as']);assert 'normal-map="Lava_004_NORM.jpg"'not in(c/'materials.xml').read_text();removed={'path':str(unused),'bytes':unused.stat().st_size,'sha256':hashlib.sha256(unused.read_bytes()).hexdigest(),'preservedSource':str(r/'fidelity-v36/candidate'/unused.name),'reason':'No SPM slot or XML/script reference. Material.cpp normal map loading requires explicit normal-map attribute; Lava_004_COLOR material has none.'};unused.unlink()
tree.write(c/'scene.xml',encoding='unicode');base=json.loads((r/'fidelity-v36/preservation-verification.json').read_text());size=sum(f.stat().st_size for f in c.rglob('*')if f.is_file());total=size+base['acceptedSharedHistoryBytes']+base['acceptedSharedTextureHistoryBytes']+base['newSharedRuntimeAllFilesBytes']+base['newSharedGlobalAliasesAllFilesBytes'];assert total<base['allCandidateAndAcceptedHistoryBytes'];proof={'baseCandidate':'V36','rims':rows,'rejectedHigherVariants':rejected,'reusedSources':sources,'changedCapInstances':sum(q['before']!=q['after']for q in rows),'linkedPlantInstances':sum(len(q['linkedPlants'])for q in rows),'minimumRequiredRoadTriangleClearanceMeters':.25,'protectedRoadTriangles':2032,'newSPMTextureMaterialPayloadBytes':0,'removedUnusedCandidateImage':removed,'candidateAllFilesBytes':size,'allCandidateAndAcceptedHistoryBytes':total,'savingVsV36Bytes':base['allCandidateAndAcceptedHistoryBytes']-total,'v1Bytes':base['integratedV1BaselineBytes'],'productionIntegrated':False,'referenceAcceptance':False};(w/'rim-preflight.json').write_text(json.dumps(proof,indent=2));print('V37_RIMS_SOURCE_READY',proof['changedCapInstances'],proof['linkedPlantInstances'],total,flush=True)
