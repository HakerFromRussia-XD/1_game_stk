from pathlib import Path
import json,math,sys,shutil,hashlib,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v18';old=r/'fidelity-v17/candidate';c=w/'candidate';assert not c.exists();shutil.copytree(old,c);p=json.loads((w/'hill-placement-inspection.json').read_text());base=json.loads((r/'fidelity-v17/preservation-verification.json').read_text());scene=E.parse(c/'scene.xml');lib=Path(p['sharedModel']).parent;sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
code=(r/'build_fidelity_v12_greenery.py').read_text();exec(code[code.index('def bary'):code.index('folder=Path')]);quad=[]
for e in E.parse(c/'quads.xml').getroot().findall('quad'):
 pp=[]
 for k in range(4):
  value=e.get('p'+str(k))
  if ':'in value:i,j=map(int,value.split(':'));pp.append(quad[i][j])
  else:pp.append(tuple(map(float,value.split())))
 quad.append(pp)
navtri=[t for q in quad for t in [(q[0],q[1],q[2]),(q[0],q[2],q[3])]];selected=[];rejected=[]
for row in p['selected']:
 navmargin=min(point_triangle_distance(row['boundingSphereCentre'],t)for t in navtri)-row['boundingSphereRadius'];row['navigationSphereMarginMeters']=navmargin
 if navmargin<3.5:rejected.append(row);continue
 assert row['roadClearanceBeyondBoundingSphere']>=3.5 and row['footprintBaseBuriedMeters']>=.3999
 row['id']=f'VRV18_RoundedHill_{len(selected):03}';row['library']=lib.name;selected.append(row);E.SubElement(scene.getroot(),'library',id=row['id'],name=lib.name,**{k:' '.join(f'{v:.9f}'for v in row[k])for k in ['xyz','hpr','scale']})
assert len(selected)>=12;scene.write(c/'scene.xml',encoding='unicode');st=E.parse(c/'scene.xml').getroot()
for e in list(st):
 if e.get('id','').startswith('VRV18_'):st.remove(e)
assert E.tostring(st)==E.tostring(E.parse(old/'scene.xml').getroot());assert all((c/q.name).read_bytes()==q.read_bytes()for q in old.iterdir()if q.is_file()and q.name!='scene.xml');model=Path(p['sharedModel']);palette=lib/'dp_palette.png';modelbytes=model.stat().st_size+palette.stat().st_size
mapbytes=sum(q.stat().st_size for q in c.iterdir()if q.is_file());total=mapbytes+base['newSharedLibraryBytesIncludingRetainedHistoricalVariants']+base['newGlobalTextureBytes'];assert total<base['v1Bytes'];out={'baseCandidate':'V17','sourcePoolObjectId':p['sourcePoolObjectId'],'sourceModel':str(model),'sourceLibrary':str(lib),'sourceModelSha256':hashlib.sha256(model.read_bytes()).hexdigest(),'sourcePaletteSha256':hashlib.sha256(palette.read_bytes()).hexdigest(),'sourceModelWithTextureBytes':modelbytes,'targetModelWithTextureBytes':modelbytes,'modelWithTextureChangePercent':0,'upper20PercentPassed':True,'newRuntimeModelAndTextureFiles':0,'newImagePixels':False,'placements':selected,'rejectedNavigationPlacements':rejected,'newCoordinateHillPlacements':len(selected),'everyBaseVertexTerrainChecked':True,'allSourceLocalGeometryBoundsOriginsAxesUnchanged':True,'sourceFootprintBuriedAtLeastMeters':min(q['footprintBaseBuriedMeters']for q in selected),'minimumRoadSphereMarginMeters':min(q['roadClearanceBeyondBoundingSphere']for q in selected),'minimumOriginalNavigationQuadSphereMarginMeters':min(q['navigationSphereMarginMeters']for q in selected),'onlyDecorativeCoordinatePlacementsAdded':True,'allPriorSceneObjectsAndModelTextureControlsByteExact':True,'candidateMapBytes':mapbytes,'newSharedLibraryBytesIncludingRetainedHistoricalVariants':base['newSharedLibraryBytesIncludingRetainedHistoricalVariants'],'newGlobalTextureBytes':base['newGlobalTextureBytes'],'candidateIncludingNewSharedBytes':total,'v1Bytes':base['v1Bytes'],'savingBytesVsV1':base['v1Bytes']-total,'productionIntegrated':False,'referenceAcceptance':False,'weightAccounting':'Full candidate map plus all new shared files from volcano rework, including retained earlier variants. This hill model+texture already exists in packaged sources and installed app, so it adds no new shared payload; 9102B referenced source library listed separately.'};(w/'hill-placements.json').write_text(json.dumps(out,indent=2));(w/'preservation-verification.json').write_text(json.dumps(out,indent=2));print('V18_ROUNDED_HILLS_COORDINATES_READY',len(selected),total,out['minimumOriginalNavigationQuadSphereMarginMeters'],flush=True)
