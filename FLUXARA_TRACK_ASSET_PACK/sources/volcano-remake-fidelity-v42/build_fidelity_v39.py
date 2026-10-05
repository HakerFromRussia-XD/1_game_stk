from pathlib import Path
import collections,copy,hashlib,json,math,shutil,struct,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v39';w.mkdir(exist_ok=True);c=w/'candidate';assert not c.exists();shutil.copytree(r/'fidelity-v38/candidate',c);shared=w/'shared-runtime';shared.mkdir();res=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources');sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
def info(f):f=Path(f);return {'path':str(f),'bytes':f.stat().st_size,'sha256':sha(f)}
ns={'math':math,'struct':struct};s=(r/'fidelity_v2.py').read_text();exec(s[s.index('def encode_buffer'):s.index('new_vertices, new_indices')],ns)
scene=E.parse(c/'scene.xml');root=scene.getroot();sun=root.find('sun');beforeSun=dict(sun.attrib);sun.set('ambient','162 153 166');sun.set('sun-diffuse','255 210 160');sun.set('sun-specular','255 219 160');sun.set('fog-color','200 161 143');sun.set('fog-max','.10')
# Remove the inherited green acid coloration; this is a below-road surface, not an acid game mode.
path=c/'volcano_track.spm';d=parse(path);oldmain=copy.deepcopy(d);lake=copy.deepcopy(d['buffers'][3]);assert d['materials'][lake['material']][0]=='acid_lake.jpg';d['materials'][lake['material']][0]='';lakecolors=[(192,65,11),(216,84,16),(186,52,9),(220,94,21)]
for v,color in zip(lake['vertices'],lakecolors):v['color']=color
# Four pre-existing decorative cone roofs get the existing tile-roof image/tint; driving bridge geometry and UV remain exact.
wood=oldmain['buffers'][19];groups=ns['component_triangles'](wood);roofs=[g for g in groups if len(g)==16];assert len(roofs)==4;roof_tri={j for g in roofs for j in g};roofUV={};roofcolors={};roofgroups=[]
for g in roofs:
 ids=sorted({i for j in g for i in wood['indices'][j*3:j*3+3]});cx=sum(wood['vertices'][i]['position'][0]for i in ids)/len(ids);cz=sum(wood['vertices'][i]['position'][2]for i in ids)/len(ids)
 for i in ids:x,y,z=wood['vertices'][i]['position'];roofUV[i]=(x*.65,z*.65);roofcolors[i]=(255,143,88)
 roofgroups.append({'triangles':g,'vertices':ids,'xzCenter':[cx,cz]})
def part(tris,material):
 ids=sorted({i for j in tris for i in wood['indices'][j*3:j*3+3]});mapping={v:i for i,v in enumerate(ids)};vertices=[copy.deepcopy(wood['vertices'][i])for i in ids]
 for oldid,v in zip(ids,vertices):
  if oldid in roofUV:v['uv']=roofUV[oldid];v['color']=roofcolors[oldid]
 return {'vertices':vertices,'indices':[mapping[i]for j in tris for i in wood['indices'][j*3:j*3+3]],'material':material},ids
brick=next(i for i,pair in enumerate(d['materials'])if pair[0]=='fluxara_castle_brick_v15.jpg');roadWood,roadIDs=part([j for j in range(len(wood['indices'])//3)if j not in roof_tri],wood['material']);roofWood,roofIDs=part(sorted(roof_tri),brick);raw=ns['replace_buffers'](d,{3:lake,19:[roadWood,roofWood]});path.write_bytes(raw)
# Sky-cloud colours respond to the actual ambient light; new copied variant preserves every geometry/normal/UV byte and bounds.
source=res/'library/fluxara_driftlib_volcano_sky_cloud_v38';lib=shared/'fluxara_driftlib_volcano_sky_cloud_v39';shutil.copytree(source,lib);f=next(lib.glob('*.spm'));cd=parse(f);buf=copy.deepcopy(cd['buffers'][0]);s=(r/'build_fidelity_v38.py').read_text();exec(s[s.index('def encode(d,b):'):s.index('def actual_bounds')])
for v in buf['vertices']:
 u=(v['position'][1]-cd['bounds'][1])/(cd['bounds'][4]-cd['bounds'][1]);v['color']=tuple(round(a+(b-a)*u)for a,b in zip((255,238,209),(255,253,242)))
cloudraw=encode(cd,buf);assert len(cloudraw)==len(cd['raw']);newfile=lib/'vr_v39_sky_cloud.spm';f.unlink();newfile.write_bytes(cloudraw);node=E.parse(lib/'node.xml');node.getroot().find('object').set('model',newfile.name);node.write(lib/'node.xml',encoding='unicode');cloudposes=[]
for e in root.findall('library'):
 if e.get('name')==source.name:before=dict(e.attrib);e.set('name',lib.name);cloudposes.append({'before':before,'after':dict(e.attrib)})
assert len(cloudposes)==8
# This inherited alias is unused by every own SPM and recursive library; keep its original source outside the candidate.
unused=c/'fluxara_drifttex_generic_lavaA.png';mat=E.parse(c/'materials.xml');removedMat=[]
for e in list(mat.getroot()):
 if e.get('name')==unused.name:removedMat.append(dict(e.attrib));mat.getroot().remove(e)
refs={n for f in c.glob('*.spm')for pair in parse(f)['materials']for n in pair if n};visited=set()
def visit(name):
 if name in visited:return
 visited.add(name);folder=(shared/name)if(shared/name).exists()else res/'library'/name;rt=E.parse(folder/'node.xml').getroot()
 for f in folder.glob('*.spm'):refs.update(n for pair in parse(f)['materials']for n in pair if n)
 for f in folder.glob('*.xml'):
  for e in E.parse(f).getroot().iter():refs.update(s for v in e.attrib.values()for s in v.split())
 for e in rt.findall('library'):visit(e.get('name'))
for e in root.findall('library'):visit(e.get('name'))
for f in c.glob('*.xml'):
 if f.name=='materials.xml':continue
 for e in E.parse(f).getroot().iter():refs.update(s for v in e.attrib.values()for s in v.split())
for e in mat.getroot().iter():refs.update(s for v in e.attrib.values()for s in v.split())
assert unused.name not in refs and unused.name not in(c/'scripting.as').read_text();removed=info(unused);removed['preservedSource']=str(r/'fidelity-v38/candidate'/unused.name);unused.unlink();mat.write(c/'materials.xml',encoding='unicode');scene.write(c/'scene.xml',encoding='unicode')
base=json.loads((r/'fidelity-v38/preservation-verification.json').read_text());size=sum(f.stat().st_size for f in c.iterdir()if f.is_file());history=base['acceptedSharedHistoryIncludingV37Bytes']+base['newSharedRuntimeAllFilesBytes'];newbytes=sum(f.stat().st_size for f in shared.rglob('*')if f.is_file());total=size+history+newbytes;assert total<base['allCandidateAndAcceptedHistoryBytes'];proof={'baseCandidate':'V38','sunBefore':beforeSun,'sunAfter':dict(sun.attrib),'mainBeforeBytes':len(oldmain['raw']),'mainAfterBytes':len(raw),'lakeOriginalMaterial':'acid_lake.jpg','lakeTriangles':2,'lakeColors':lakecolors,'lakeGeometryNormalsAndDefaultPhysicsRetained':True,'lakeOldTextureBytes':(r/'fidelity-v38/candidate/acid_lake.jpg').stat().st_size,'lakeNewUsedTextureBytes':0,'woodOriginalBuffer':19,'woodRoadOriginalVertexIds':roadIDs,'woodRoofOriginalVertexIds':roofIDs,'roofGroups':roofgroups,'woodRoadAndRoofsGeometryNormalsCountRetained':True,'roadWoodUVAndRGBRetained':True,'roofUsesExistingTexture':'fluxara_castle_brick_v15.jpg','roofNewVertexTint':[255,143,88],'roofOriginalUsedTextureBytes':13633,'roofNewUsedTextureBytes':5072,'cloudSourceModel':info(source/'vr_v38_sky_cloud.spm'),'newCloudModel':info(newfile),'cloudGeometryNormalsUVBoundsAndModelWeightRetained':True,'cloudPoses':cloudposes,'removedUnreferencedImage':removed,'removedUnreferencedMaterialEntries':removedMat,'allRecursiveLibrariesChecked':sorted(visited),'noNewRasterPixels':True,'candidateAllFilesBytes':size,'acceptedSharedHistoryIncludingV38Bytes':history,'newSharedRuntimeAllFilesBytes':newbytes,'allCandidateAndAcceptedHistoryBytes':total,'savingVsV38Bytes':base['allCandidateAndAcceptedHistoryBytes']-total,'v1Bytes':base['v1Bytes'],'productionIntegrated':False,'referenceAcceptance':False,'stage':'Early coherent lighting/material batch; independent preservation, engine/native/pool gates pending.'};(w/'visual-batch-preflight.json').write_text(json.dumps(proof,indent=2));print('V39_VISUAL_BATCH_SOURCE_READY',total,newbytes,flush=True)
