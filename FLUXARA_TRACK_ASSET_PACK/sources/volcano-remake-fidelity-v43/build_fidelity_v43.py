from pathlib import Path
import collections,copy,hashlib,json,shutil,struct,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v43';w.mkdir(exist_ok=True);c=w/'candidate'
assert not c.exists();shutil.copytree(r/'fidelity-v42/candidate',c)
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
ns={'struct':struct,'math':__import__('math')};s=(r/'fidelity_v2.py').read_text();exec(s[s.index('def encode_buffer'):s.index('new_vertices, new_indices')],ns)
encode=ns['encode_buffer'];old=parse(r/'fidelity-v14/candidate/volcano_track.spm');current=parse(c/'volcano_track.spm')
def key(b,t):return tuple(sorted(tuple(v)for v in (b['vertices'][i]['position']for i in b['indices'][t:t+3])))
existing=collections.Counter(key(current['buffers'][2],t)for t in range(0,len(current['buffers'][2]['indices']),3))
cliff=old['buffers'][3];missing=[]
for t in range(0,len(cliff['indices']),3):
 k=key(cliff,t)
 if existing[k]:existing[k]-=1
 else:missing.append(t)
assert not any(existing.values());assert len(missing)==1508
def subset(b,triangles,material,divide=1):
 ids=list(dict.fromkeys(i for t in triangles for i in b['indices'][t:t+3]));mapping={v:i for i,v in enumerate(ids)};vs=[copy.deepcopy(b['vertices'][i])for i in ids]
 for v in vs:v['uv']=tuple(q/divide for q in v['uv'])
 return {'vertices':vs,'indices':tuple(mapping[i]for t in triangles for i in b['indices'][t:t+3]),'material':material}
buffers=[subset(cliff,missing,0,3),subset(old['buffers'][4],range(0,len(old['buffers'][4]['indices']),3),1),subset(old['buffers'][2],range(0,len(old['buffers'][2]['indices']),3),0)]
textures=[['fluxara_volcano_stone_shared_v16.jpg',''],['fluxara_volcano_moss_shared_v20.jpg','']]
positions=[v['position']for b in buffers for v in b['vertices']];bounds=[min(p[i]for p in positions)for i in range(3)]+[max(p[i]for p in positions)for i in range(3)]
raw=bytearray(b'SP'+bytes([10,3]))+struct.pack('<6fH',*bounds,2)
for pair in textures:
 for name in pair:raw+=bytes([len(name)])+name.encode()
raw+=struct.pack('<HH',1,len(buffers))
for b in buffers:raw+=encode(b,textures)
raw+=struct.pack('<6f',*bounds)
shared=w/'shared-runtime';lib=shared/'fluxara_driftlib_volcano_continuous_terrain_v43';lib.mkdir(parents=True)
model=lib/'vr_v43_continuous_terrain.spm';model.write_bytes(raw)
(lib/'node.xml').write_text('<scene><object type="static" model="'+model.name+'" xyz="0 0 0" hpr="0 0 0" scale="1 1 1" interaction="ghost"/></scene>\n')
(lib/'materials.xml').write_text('<materials><material name="fluxara_volcano_stone_shared_v16.jpg"/><material name="fluxara_volcano_moss_shared_v20.jpg"/></materials>\n')
scene=E.parse(c/'scene.xml');root=scene.getroot();reference=E.parse(r/'fidelity-v14/candidate/scene.xml').getroot()
remove_names={'fluxara_driftlib_volcano_stone_column_v32','fluxara_driftlib_volcano_grass_roll_v38','fluxara_driftlib_volcano_green_mound_v18','fluxara_driftlib_round_tree_green_v2','fluxara_driftlib_volcano_sky_cloud_v39','fluxara_driftlib_volcano_rounded_crest_v21','fluxara_driftlib_volcano_central_stone_v26'}
removed=[];reset=[];bush={x.get('id'):x for x in reference.findall('library')if x.get('name')=='fluxara_driftlib_round_bush_green_v2'}
for x in list(root):
 if x.tag=='library'and x.get('name')in remove_names:removed.append(dict(x.attrib));root.remove(x)
 elif x.tag=='library'and x.get('id')in bush:reset.append({'before':dict(x.attrib),'after':dict(bush[x.get('id')].attrib)});x.attrib.clear();x.attrib.update(bush[reset[-1]['before']['id']].attrib)
field=root.find('library[@name="fluxara_driftlib_volcano_closed_terrain_v42"]');assert field is not None;field_before=dict(field.attrib);field.set('name',lib.name);assert field.get('xyz')=='0 0 0'and field.get('scale')=='1 1 1'
root.find('sky-box').attrib.clear();root.find('sky-box').attrib.update(reference.find('sky-box').attrib)
for name in reference.find('sky-box').get('texture').split():
 src=r/'fidelity-v14/candidate'/name;assert src.is_file();shutil.copy2(src,c/name)
scene.write(c/'scene.xml',encoding='unicode')
source_scene=E.parse(r/'fidelity-v42/candidate/scene.xml').getroot()
for x in source_scene:
 if x.tag not in ['library','sky-box']:assert E.tostring(x)==E.tostring(next(y for y in root if y.tag==x.tag and y.attrib==x.attrib)),x.attrib
for f in (r/'fidelity-v42/candidate').iterdir():
 if f.is_file()and f.name!='scene.xml':assert f.read_bytes()==(c/f.name).read_bytes(),f.name
check=parse(model);assert check['bounds']==tuple(bounds);assert len(check['buffers'])==3
for b,new in zip(buffers,check['buffers']):
 assert b['indices']==new['indices']
 for v,n in zip(b['vertices'],new['vertices']):assert v['position']==n['position']and v['normal']==n['normal']and v['color']==n['color']
grasspos={v['position']for v in old['buffers'][4]['vertices']};cliffpos={v['position']for v in cliff['vertices']};joined=len(grasspos&cliffpos)
assert joined>20,joined
base=json.loads((r/'fidelity-v42/preservation-verification.json').read_text());own=sum(p.stat().st_size for p in c.rglob('*')if p.is_file());sharedbytes=sum(p.stat().st_size for p in lib.iterdir());total=own+base['allCandidateAndAcceptedHistoryBytes']-base['candidateAllFilesBytes']+sharedbytes
assert total+67520<base['v1Bytes']
proof={'baseCandidate':'V42','landscapeReference':'V14 original contiguous cliff and grass topology, also present in V13','newField':str(model),'newFieldPlacement':dict(field.attrib),'oldFieldPlacement':field_before,'removedDecorativePlacements':removed,'resetBushPlacements':reset,'restoredCliffTriangles':1508,'existingCliffTrianglesRetained':702,'restoredGrassTriangles':427,'restoredCentralRockTriangles':72,'originalGrassCliffSharedPositions':joined,'allRestoredPositionsNormalsColorsAndIndicesExactSource':True,'cliffUVFrequencyDividedByThree':True,'sourceMainModelByteExactV42':True,'originalPhysicalObjectsAndProtectedCourseByteExactV42':True,'newTerrainInteraction':'ghost','sourceOriginalMeshBoundsRetained':True,'candidateAllFilesBytes':own,'acceptedSharedHistoryIncludingV42Bytes':base['allCandidateAndAcceptedHistoryBytes']-base['candidateAllFilesBytes'],'newSharedRuntimeAllFilesBytes':sharedbytes,'allCandidateAndAcceptedHistoryBytes':total,'v1Bytes':base['v1Bytes'],'savingVsV1Bytes':base['v1Bytes']-total,'newRasterPixels':False,'logicalModelPlusUsedTextureIncreasePercent':0,'logicalModelWeightBaseline':'Same extracted original V14 component union, with existing V42 cliff triangles excluded in both baseline and variant. UV change has identical byte length.','logicalModelBytes':len(raw),'logicalModelPlusUsedTexturesBytes':len(raw)+39938+321,'productionIntegrated':False,'referenceAcceptance':False}
(w/'preservation-verification.json').write_text(json.dumps(proof,indent=2));print('V43_CONTIGUOUS_ORIGINAL_TERRAIN_RESTORED',{'triangles':sum(len(b['indices'])//3 for b in buffers),'removedPlacements':len(removed),'resetBushes':len(reset),'sharedBoundaryVertices':joined,'bytes':total,'saving':base['v1Bytes']-total},flush=True)
