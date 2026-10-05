from pathlib import Path
import json,hashlib,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v6';base=r/'fidelity-v5-alpha/candidate';candidate=w/'candidate'
old=E.parse(base/'scene.xml').getroot();new=E.parse(candidate/'scene.xml').getroot();changes=json.loads((w/'layout-changes.json').read_text())
for row in changes:
    a=next(e for e in old.findall('object')if e.get('id')==row['id']);b=next(e for e in new.findall('object')if e.get('id')==row['id'])
    assert E.tostring(a,encoding='unicode')==row['originalXml'];assert E.tostring(b,encoding='unicode')==row['candidateXml']
    assert a.get('interaction')==b.get('interaction')=='ghost'
    assert all(a.get(k)==b.get(k)for k in a.attrib if k not in ['xyz','scale'])
    av=list(map(float,a.get('xyz').split()));bv=list(map(float,b.get('xyz').split()));assert bv[0]==av[0]and bv[2]==av[2]and abs(bv[1]-av[1]-row['heightOffset'])<1e-6
    assert all(abs(x*y-z)<1e-6 for x,y,z in zip(map(float,a.get('scale').split()),row['scaleFactors'],map(float,b.get('scale').split())))
    assert len(a.findall('curve'))==len(b.findall('curve'))
    for ca,cb in zip(a.findall('curve'),b.findall('curve')):
        assert ca.attrib==cb.attrib
        for pa,pb in zip(ca.findall('p'),cb.findall('p')):
            assert pa.attrib.keys()==pb.attrib.keys()
            for key in pa.attrib:
                af,ay=map(float,pa.get(key).split());bf,by=map(float,pb.get(key).split());assert af==bf
                channel=ca.get('channel');expected=ay+row['heightOffset']if channel=='LocY'else ay*row['scaleFactors'][['ScaleX','ScaleY','ScaleZ'].index(channel)]if channel in ['ScaleX','ScaleY','ScaleZ']else ay
                assert abs(by-expected)<1e-6
    replacement=E.fromstring(row['originalXml']);replacement.tail=a.tail;new.remove(b);new.insert(list(old).index(a),replacement)
assert E.tostring(old)==E.tostring(new)
for p in base.iterdir():
    if p.is_file()and p.name!='scene.xml':assert p.read_bytes()==(candidate/p.name).read_bytes(),p.name
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
road=lambda d:next(b for b in d['buffers']if d['materials'][b['material']][0]=='track01.png')
a=road(parse(r/'before/volcano_track.spm'));b=road(parse(candidate/'volcano_track.spm'));assert a['indices']==b['indices'];assert len(a['vertices'])==len(b['vertices']);assert all(all(x.get(k)==y.get(k)for k in ['position','normal','uv','color'])for x,y in zip(a['vertices'],b['vertices']))
names=['track.xml','quads.xml','graph.xml','scripting.as','easter_eggs.xml']
for name in names:assert(candidate/name).read_bytes()==(r/'before'/name).read_bytes()
prod=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources/tracks/fluxara-user-volcano-remake')
assert all(p.read_bytes()==(prod/p.name).read_bytes()for p in(r/'fidelity-v2/baseline').iterdir()if p.is_file())
(w/'preservation.json').write_text(json.dumps({'originalRoadPositionsNormalsUvsColoursAndIndicesExact':True,'originalGameplayFilesExact':names,'allNonSceneFilesExactV5Alpha':True,'allOtherSceneNodesExactV5Alpha':True,'changedDecorativeGhostInstances':len(changes),'onlyChanges':changes,'productionIntegrated':False,'productionSourceUnchanged':True,'sceneSha256':hashlib.sha256((candidate/'scene.xml').read_bytes()).hexdigest()},indent=2));print('V6_PRESERVATION_VERIFIED')
