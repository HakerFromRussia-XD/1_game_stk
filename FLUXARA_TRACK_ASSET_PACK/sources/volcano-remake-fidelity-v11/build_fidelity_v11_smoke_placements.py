from pathlib import Path
import json,shutil,sys,hashlib,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v11';w.mkdir(exist_ok=True);c=w/'candidate';old=r/'fidelity-v10b/candidate';shutil.copytree(old,c,dirs_exist_ok=True)
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
# Unrotated original volcano placements; upper-ring vertex mean locates each vent.
targets={'AshCloud.spm':('vulcan_02.spm',(277.64,-51.25,-59.99),2.47,.45),
 'AshColumn.spm':('vulcan_03.spm',(-37.24,-6.08,207.57),1,.45),
 'PyroclasticFlow.spm':('vulcan_02.spm',(-152.53,-7.28,-35.39),1,.45)}
scene=E.parse(c/'scene.xml');rows=[]
for o in scene.getroot().findall('object'):
 if o.get('model')not in targets:continue
 name=o.get('model');volcano,origin,vs,shrink=targets[name];d=parse(c/volcano);vv=[v['position']for b in d['buffers']for v in b['vertices']];top=max(v[1]for v in vv);ring=[v for v in vv if v[1]>top-1];vent=[origin[k]+vs*sum(v[k]for v in ring)/len(ring)for k in range(3)]
 smoke=parse(c/name);sv=[v['position']for b in smoke['buffers']for v in b['vertices']];bottom=min(v[1]for v in sv);lowest=[v for v in sv if abs(v[1]-bottom)<.001];anchor=[sum(v[k]for v in lowest)/len(lowest)for k in range(3)];scale=[float(x)*shrink for x in o.get('scale').split()];xyz=[vent[k]-scale[k]*anchor[k]for k in range(3)];xyz[1]-=2
 before=E.tostring(o,encoding='unicode');o.set('xyz',' '.join(f'{v:.9f}'for v in xyz));o.set('scale',' '.join(f'{v:.9f}'for v in scale));assert o.get('interaction')=='ghost';bounds=[[xyz[k]+scale[k]*smoke['bounds'][k+j]for k in range(3)]for j in [0,3]]
 rows.append({'id':o.get('id'),'model':name,'volcanoModel':volcano,'originalVolcanoPlacementGame':origin,'volcanoScale':vs,'ventWorld':vent,'baseAnchoredTwoMetresInsideVent':True,'uniformWorldScaleMultiplier':shrink,'worldBounds':bounds,'originalXml':before,'candidateXml':E.tostring(o,encoding='unicode'),'modelBytesAndLocalBoundsAndOriginAxesUnchanged':True})
assert len(rows)==3;scene.write(c/'scene.xml',encoding='unicode')
def norm(e):return (e.tag,sorted(e.attrib.items()),(e.text or '').strip(),[norm(ch)for ch in e])
left=E.parse(old/'scene.xml').getroot();right=E.parse(c/'scene.xml').getroot();names=set(targets)
for root in [left,right]:
 for o in list(root.findall('object')):
  if o.get('model')in names:root.remove(o)
assert norm(left)==norm(right),'Non-smoke scene content changed'
assert all(p.read_bytes()==(old/p.name).read_bytes()for p in c.iterdir()if p.is_file()and p.name!='scene.xml')
b=json.loads((r/'fidelity-v10b/budget.json').read_text());b['candidateTrackBytes']=sum(p.stat().st_size for p in c.iterdir()if p.is_file());b['newBytesIncludingNewSharedRuntime']=b['candidateTrackBytes']+b['newSharedRuntimeBytes'];b['savedBytesAgainstPrevious']=b['previousTrackBytes']-b['newBytesIncludingNewSharedRuntime'];assert b['savedBytesAgainstPrevious']>0
(w/'smoke-placement-changes.json').write_text(json.dumps(rows,indent=2));(w/'budget.json').write_text(json.dumps(b,indent=2));(w/'preservation.json').write_text(json.dumps({'allRuntimeFilesExceptSceneByteIdenticalToV10B':True,'sceneChangesOnlyThreeDecorativeGhostSmokeTransforms':True,'protectedCourseAndGameplayControlsUnchanged':True,'allModelsWithTexturesWeightChangePercent':0,'noNewSharedGameResources':True,'source':str(old.resolve())},indent=2));print('V11_CONNECTED_SMALLER_SMOKE_READY',b['newBytesIncludingNewSharedRuntime'],flush=True)
