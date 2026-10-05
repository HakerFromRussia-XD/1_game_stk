from pathlib import Path
import sys,json,hashlib,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;f=r/'candidate';sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
b=parse(r/'before/dp-motorsports-land-ii_track.spm');a=parse(f/'dp-motorsports-land-ii_track.spm');removed=[3,9,10,40,51,68]
assert a['bounds']==b['bounds'];proof=[]
for aa,i in zip(a['buffers'],[i for i in range(72) if i not in removed]):
 bb=b['buffers'][i]
 assert len(aa['indices'])==len(bb['indices'])
 for ja,jb in zip(aa['indices'],bb['indices']):
  va,vb=aa['vertices'][ja],bb['vertices'][jb];assert va['position']==vb['position'];assert va.get('normal')==vb.get('normal')
 if i in [1,2,12,14,19,23,24,25,26,27,28,29,30,31,32,36,37,45,48]:assert aa['indices']==bb['indices']
 proof.append(i)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for n in ['track.xml','quads.xml','graph.xml']:assert sha(f/n)==sha(r/'before'/n)
def sig(e):return [e.tag,sorted(e.attrib.items()),(e.text or '').strip(),[sig(c) for c in e]]
x=E.parse(r/'before/scene.xml').getroot();y=E.parse(f/'scene.xml').getroot();assert [sig(e) for e in x if e.tag!='sky-box']==[sig(e) for e in y if e.tag not in ['sky-box','sun'] and e.get('id')!='DP_ReferenceScenery']
x=E.parse(r/'before/materials.xml').getroot();y=E.parse(f/'materials.xml').getroot();assert [sig(e) for e in x]==[sig(e) for e in y][:len(x)]
tris=lambda d:sum(len(q['indices'])//3 for q in d['buffers']);oldtris=tris(b);newtris=tris(a)+tris(parse(f/'dp_scenery.spm'));size=lambda p:sum(x.stat().st_size for x in p.iterdir() if x.is_file());old=size(r/'before');new=size(f)
result={'originalBytes':old,'newBytes':new,'originalTriangles':oldtris,'newTriangles':newtris,'triangleChangePercent':100*(newtris/oldtris-1),'retainedBuffersTriangleCornersPositionsNormalsIdentical':proof,'removedDecorativeBillboardBuffers':removed,'protectedXmlByteIdentical':True,'allGameplaySceneNodesIdentical':True,'physicalMaterialsIdentical':True,'weightNotIncreased':new<=old,'triangleBudgetPassed':.8*oldtris<=newtris<=1.2*oldtris};(r/'preservation-audit.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
assert result['weightNotIncreased'];assert result['triangleBudgetPassed']
