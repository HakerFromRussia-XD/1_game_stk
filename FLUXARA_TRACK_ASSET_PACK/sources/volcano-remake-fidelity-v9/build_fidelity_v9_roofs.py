from pathlib import Path
import sys,json,struct,math,shutil,copy,hashlib,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v9';w.mkdir(exist_ok=True);c=w/'candidate';shutil.copytree(r/'fidelity-v8b/candidate',c,dirs_exist_ok=True)
sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
repo=Path('/Users/motoricallc/Downloads/fluxara-drift');base=repo/'iosApp/FluxaraResources/library/fluxara_driftlib_volcano_castle_tower_v8b';folder=repo/'iosApp/FluxaraResources/library/fluxara_driftlib_volcano_castle_tower_v9';folder.mkdir(exist_ok=True);model='vr_v9_castle_tower.spm';texture='vr_v9_castle_palette.png';d=parse(base/'vr_v8b_castle_tower.spm');b=d['buffers'][0];removed=[t for t in range(len(b['indices'])//3)if max(b['vertices'][i]['position'][1]for i in b['indices'][t*3:t*3+3])>.99];indices=[i for t in range(len(b['indices'])//3)if t not in removed for i in b['indices'][t*3:t*3+3]];used=sorted(set(indices));lookup={old:new for new,old in enumerate(used)};vertices=[copy.deepcopy(b['vertices'][i])for i in used];indices=[lookup[i]for i in indices]
def normal(v):
 length=math.sqrt(sum(x*x for x in v));return sum((round(x/length*511)&1023)<<(10*k)for k,x in enumerate(v))|(1<<30)
start=len(vertices);radius=d['bounds'][3];base_y=.96;peak=d['bounds'][4];segments=16
for i in range(segments):
 angle=2*math.pi*i/segments;x=radius*math.cos(angle);z=radius*math.sin(angle);vertices.append({'position':(x,base_y,z),'normal':normal((math.cos(angle),radius/(peak-base_y),math.sin(angle))),'uv':(.375,.125)})
vertices.append({'position':(0,peak,0),'normal':normal((0,1,0)),'uv':(.375,.125)})
for i in range(segments):indices.extend([start+i,start+segments,start+(i+1)%segments])
assert len(vertices)<=255
bounds=d['bounds'];name=texture.encode();raw=bytearray(b'SP'+bytes([10,1])+struct.pack('<6f',*bounds)+struct.pack('<H',1)+bytes([len(name)])+name+b'\0'+struct.pack('<HHIIH',1,1,len(vertices),len(indices),0))
for v in vertices:raw+=struct.pack('<3fI2e',*v['position'],v['normal'],*v['uv'])
raw+=struct.pack('<'+str(len(indices))+'B',*indices);(folder/model).write_bytes(raw);shutil.copy2(base/'vr_v8b_castle_palette.png',folder/texture);(folder/'node.xml').write_text(f'<scene><object id="VRV9_CastleTower" type="animation" model="{model}" xyz="0 0 0" hpr="0 0 0" scale="1 1 1" interaction="ghost" skeletal-animation="false" /></scene>');(folder/'materials.xml').write_text(f'<materials><material name="{texture}" shader="solid" /></materials>')
scene=E.parse(c/'scene.xml');changes=json.loads((r/'fidelity-v8b/castle-changes.json').read_text())
for q in changes:
 obj=next(e for e in scene.getroot().findall('library')if e.get('id')==q['id']);obj.set('name',folder.name);q['pooledSource']=str(folder/model);q['poolPrototypeId']='volcano-fidelity-v9-castle-tower';q['scope']='Gray castle tower with red cone roof; source origin/axes/local bounds retained, top crenellations/pole replaced. Existing map collision, road and gameplay remain exact.'
scene.write(c/'scene.xml',encoding='unicode');(w/'castle-changes.json').write_text(json.dumps(changes,indent=2));before=Path(changes[0]['originalPoolModel']).stat().st_size+Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources/library/fluxara_driftlib_castle_tower_v1/dp_palette.png').stat().st_size;after=(folder/model).stat().st_size+(folder/texture).stat().st_size
assert after<=1.2*before
(w/'skin-changes.json').write_text(json.dumps({'sourceModel':changes[0]['originalPoolModel'],'previousVariant':str(base/'vr_v8b_castle_tower.spm'),'adaptedModel':str(folder/model),'library':str(folder),'runtimeTextureAlias':texture,'paletteSource':str(base/'vr_v8b_castle_palette.png'),'palettePixelsUnchangedSha256':hashlib.sha256((folder/texture).read_bytes()).hexdigest(),'triangles':len(indices)//3,'sourceLocalBoundsUnchanged':True,'originAndAxesUnchanged':True,'removedPreviousTopTriangleIds':removed,'retainedPreviousVertexIndices':used,'retainedTriangles':len(indices)//3-segments,'newRoofTriangles':segments,'roofBaseHeight':base_y,'roofApexHeight':peak,'modelWithTextureBeforeBytes':before,'modelWithTextureAfterBytes':after,'weightChangePercent':100*(after/before-1),'weightWithin20Percent':True,'newSharedRuntimeBytes':sum(p.stat().st_size for p in folder.iterdir()if p.is_file())},indent=2));print('V9_RED_CONE_ROOF_READY',before,after,len(indices)//3,flush=True)
