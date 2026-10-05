from pathlib import Path
import json,math,sys,hashlib,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v18';old=r/'fidelity-v17/candidate';c=w/'candidate';p=json.loads((w/'hill-placements.json').read_text());sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
for f in old.iterdir():
 if f.is_file()and f.name!='scene.xml':assert(c/f.name).read_bytes()==f.read_bytes(),f.name
s=E.parse(c/'scene.xml').getroot();added=[e for e in s if e.get('id','').startswith('VRV18_')];assert len(added)==32
for e in added:s.remove(e)
assert E.tostring(s)==E.tostring(E.parse(old/'scene.xml').getroot())
source=parse(p['sourceModel']);new=parse(p['adaptedModel']);assert source['bounds']==new['bounds'];a=source['buffers'][0];b=new['buffers'][0];assert a['indices']==b['indices'];assert all(x['position']==y['position']and x['normal']==y['normal']for x,y in zip(a['vertices'],b['vertices']));assert p['targetModelWithTextureBytes']<=p['sourceModelWithTextureBytes']*1.2
# Recompute the slope-aligned transformed source base and original navigation margin.
code=(r/'inspect_fidelity_v18_hill_placements.py').read_text();ctx={'__file__':str(r/'inspect_fidelity_v18_hill_placements.py')};exec(code[:code.index("lib=Path")],ctx);height=ctx['height'];closest=ctx['closest']
maxrotation=0;minbury=1e20;minroad=1e20
for q in p['placements']:
 x,y,z=map(math.radians,q['hpr']);cx,sx,cy,sy,cz,sz=math.cos(x),math.sin(x),math.cos(y),math.sin(y),math.cos(z),math.sin(z);R=[[cy*cz,sx*sy*cz-cx*sz,cx*sy*cz+sx*sz],[cy*sz,sx*sy*sz+cx*cz,cx*sy*sz-sx*cz],[-sy,sx*cy,cx*cy]]
 maxrotation=max(maxrotation,max(abs(R[k][j]-q['rotationColumns'][j][k])for k in range(3)for j in range(3)))
 for v in a['vertices']:
  vx,vy,vz=v['position']
  if vy<.0001:
   vv=[q['xyz'][k]+sum(R[k][j]*v['position'][j]*q['scale'][j]for j in range(3))for k in range(3)];h=height(vv[0],vv[2],vv[1]);assert h is not None;minbury=min(minbury,h-vv[1]);assert h-vv[1]>=.3999
 margin=closest(q['boundingSphereCentre'])-q['boundingSphereRadius'];minroad=min(minroad,margin);assert margin>=3.5
assert maxrotation<1e-12
protected=['track.xml','quads.xml','graph.xml','scripting.as','easter_eggs.xml'];assert all((c/n).read_bytes()==(r/'before'/n).read_bytes()for n in protected)
prod=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources/tracks/fluxara-user-volcano-remake');assert all((prod/f.name).read_bytes()==f.read_bytes()for f in(r/'fidelity-v2/baseline').iterdir()if f.is_file())
size=lambda folder:sum(f.stat().st_size for f in folder.rglob('*')if f.is_file());base=json.loads((r/'fidelity-v17/preservation-verification.json').read_text());total=size(c)+base['newSharedLibraryBytesIncludingRetainedHistoricalVariants']+size(Path(p['adaptedLibrary']))+base['newGlobalTextureBytes'];assert total==p['candidateIncludingNewSharedBytes']<p['v1Bytes'];out={**p,'footingWorldRotationIndependentlyVerified':True,'maxEulerRotationColumnDeviation':maxrotation,'allBaseVerticesIndependentlyBelowTerrainMeters':minbury,'roadSphereMarginIndependentlyRecomputed':minroad,'protectedControlBytesExact':protected,'productionStillExactV1':True};(w/'preservation-verification.json').write_text(json.dumps(out,indent=2));print('V18_ALL_PRIOR_GEOMETRY_CONTROLS_AND_NEW_HILL_FOOTING_VERIFIED',total,minbury,flush=True)
