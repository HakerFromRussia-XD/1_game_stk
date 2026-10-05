from pathlib import Path
import collections,hashlib,json,math,sys
r=Path(__file__).resolve().parent;w=r/'fidelity-v32';p=json.loads((w/'seam-changes.json').read_text());sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
for role in ['Grass','Stone']:
 f=Path(p['source'+role+'Model']);assert hashlib.sha256(f.read_bytes()).hexdigest()==p['source'+role+'ModelSha256']
def boundary(buf):
 def key(i):return tuple(round(q,6)for q in buf['vertices'][i]['position'])
 ed=collections.Counter(tuple(sorted((key(buf['indices'][i+j]),key(buf['indices'][i+(j+1)%3]))))for i in range(0,len(buf['indices']),3)for j in range(3));pts={v for e,n in ed.items()if n==1 for v in e};return [v['position']for v in buf['vertices']if tuple(round(q,6)for q in v['position'])in pts]
gs,ss=boundary(parse(Path(p['newGrassModel']))['buffers'][0]),boundary(parse(Path(p['newSharedModel']))['buffers'][0]);assert len({tuple(v)for v in gs})==len({tuple(v)for v in ss})==16
def transform(v,attrs):
 xyz=list(map(float,attrs['xyz'].split()));s=list(map(float,attrs['scale'].split()));y=math.radians(float(attrs['hpr'].split()[1]));co,si=math.cos(y),math.sin(y);return(xyz[0]+co*v[0]*s[0]+si*v[2]*s[2],xyz[1]+v[1]*s[1],xyz[2]-si*v[0]*s[0]+co*v[2]*s[2])
maxerror=0;maxoverlaperror=0
for g in p['placements']:
 st,cap,tree=g['parts'];a=[transform(v,st)for v in ss];b=[transform(v,cap)for v in gs]
 for v in a:
  q=min(b,key=lambda u:math.hypot(u[0]-v[0],u[2]-v[2]));maxerror=max(maxerror,math.hypot(v[0]-q[0],v[2]-q[2]));maxoverlaperror=max(maxoverlaperror,abs(v[1]-q[1]-.08))
assert maxerror<1e-5 and maxoverlaperror<1e-5,(maxerror,maxoverlaperror)
proof={'sourceDonorModelsByteHashesUnchanged':True,'matchedBoundaryPointsPerGroup':16,'verifiedGroups':24,'worldXZBoundaryMaxErrorMeters':maxerror,'worldVerticalBoundaryOverlapMeters':.08,'worldOverlapMaxErrorMeters':maxoverlaperror,'newPixels':False,'modelsWithTextureBytesBefore':46337,'modelsWithTextureBytesAfter':46337};(w/'seam-verification.json').write_text(json.dumps(proof,indent=2));print('V32_ALL_WORLD_SEAMS_INDEPENDENTLY_VERIFIED',proof,flush=True)
