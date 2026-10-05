from pathlib import Path
import collections,copy,hashlib,json,math,shutil,struct,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v36';w.mkdir(exist_ok=True);c=w/'candidate';assert not c.exists();shutil.copytree(r/'fidelity-v35/candidate',c);shared=w/'shared-runtime';shared.mkdir();tex=w/'shared-textures';tex.mkdir()
res=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources');pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK');sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse,rewrite_texture_names
ns={'math':math,'struct':struct};s=(r/'fidelity_v2.py').read_text();exec(s[s.index('def encode_buffer'):s.index('new_vertices, new_indices')],ns)
def info(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
alias='fluxara_volcano_bubbling_lava_v36.jpg';shutil.copy2(c/'blackrock_lava.jpg',tex/alias)
mudsrc=res/'library/fluxara_driftlib_mudpot_a';mudlib=shared/'fluxara_driftlib_volcano_mudpot_v36';mudlib.mkdir();gloss='vr_v36_mudpot_gloss.png';shutil.copy2(mudsrc/'fluxara_drift_mudpot_a_gloss.png',mudlib/gloss)
mudmodels=[]
for name in ['animated_bubble.spm','fluxara_driftlib_mudpot_a_main.spm']:
 d=parse(mudsrc/name);names=[[alias if n=='fluxara_drift_mudpot_a.png'else n for n in pair]for pair in d['materials']];(mudlib/name).write_bytes(rewrite_texture_names(d,names));mudmodels.append({'before':info(mudsrc/name),'after':info(mudlib/name)})
mt=E.parse(mudsrc/'materials.xml');mt.getroot()[0].set('name',alias);mt.getroot()[0].set('gloss-map',gloss);mt.write(mudlib/'materials.xml',encoding='unicode')
node=E.parse(mudsrc/'node.xml');next(e for e in node.getroot().iter('animated-texture')).set('name',alias);node.write(mudlib/'node.xml',encoding='unicode')
mudBefore=sum(q['before']['bytes']for q in mudmodels)+(mudsrc/'fluxara_drift_mudpot_a.png').stat().st_size+(mudsrc/'fluxara_drift_mudpot_a_gloss.png').stat().st_size;mudAfter=sum(q['after']['bytes']for q in mudmodels)+(tex/alias).stat().st_size+(mudlib/gloss).stat().st_size;assert mudAfter<=mudBefore*1.2
scene=E.parse(c/'scene.xml');root=scene.getroot();mudposes=[]
for e in root.findall('library'):
 if e.get('name')==mudsrc.name:old=dict(e.attrib);e.set('name',mudlib.name);mudposes.append({'before':old,'after':dict(e.attrib)})
mapModels=[]
for f in sorted(c.glob('*.spm')):
 d=parse(f);names=[[alias if n in ['stk_mudpot_a.png','fluxara_drift_mudpot_a.png']else n for n in pair]for pair in d['materials']]
 if names!=d['materials']:oldhash=hashlib.sha256(f.read_bytes()).hexdigest();f.write_bytes(rewrite_texture_names(d,names));mapModels.append({'name':f.name,'oldSha256':oldhash,'newSha256':hashlib.sha256(f.read_bytes()).hexdigest(),'materialAliasOnly':True})
mt=E.parse(c/'materials.xml');oldmud=next(q for q in mt.getroot()if q.get('name')=='fluxara_drift_mudpot_a.png');oldMudMat=copy.deepcopy(oldmud.attrib);oldmud.set('name',alias);newMudMat=copy.deepcopy(oldmud.attrib);mt.write(c/'materials.xml',encoding='unicode')
# This candidate-owned image is unreferenced after every SPM and material alias is updated; source archives remain intact.
assert all('fluxara_drift_mudpot_a.png'not in str(parse(f)['materials'])for f in c.glob('*.spm'))
assert 'fluxara_drift_mudpot_a.png'not in(c/'scene.xml').read_text()and 'fluxara_drift_mudpot_a.png'not in(c/'materials.xml').read_text()
removed=[info(c/'fluxara_drift_mudpot_a.png')];(c/'fluxara_drift_mudpot_a.png').unlink()
# Textured terracotta copy: keep the16-face roof and flag; simplify only the tiny pole8->4sides to cover UV bytes.
roofsrc=res/'library/fluxara_driftlib_volcano_castle_roof_v15/fluxara_castle_v15_roof.spm';d=parse(roofsrc);old=d['buffers'][0];ids=list(range(17))+[17,19,21,23,25,27,29,31]+[33,34,35];mapping={v:i for i,v in enumerate(ids)};vv=[copy.deepcopy(old['vertices'][i])for i in ids]
for i,v in zip(ids,vv):
 x,y,z=v['position'];v['uv']=(4*(x/.46+.5),4*(z/.46+.5));v['color']=(255,143,88)if i<17 else old['vertices'][i]['color']
ii=list(old['indices'][:48])
for k in range(4):a=17+2*k;b=17+2*((k+1)%4);aa=25+2*k;bb=25+2*((k+1)%4);ii.extend([a,aa,b,b,aa,bb])
ii.extend(old['indices'][-3:]);buf={'vertices':vv,'indices':[mapping[i]for i in ii],'material':0};names=[['fluxara_castle_brick_v15.jpg','']]
raw=bytearray(b'SP'+bytes([10,3])+struct.pack('<6f',*d['bounds'])+struct.pack('<H',1))
for pair in names:
 for name in pair:bb=name.encode();raw+=bytes([len(bb)])+bb
raw+=struct.pack('<HH',1,1)+ns['encode_buffer'](buf,names);rooflib=shared/'fluxara_driftlib_volcano_tile_roof_v36';rooflib.mkdir();roofpath=rooflib/'vr_v36_tiled_roof.spm';roofpath.write_bytes(raw);assert len(raw)<=len(d['raw']),(len(raw),len(d['raw']))
rt=E.parse(roofsrc.parent/'node.xml');rt.getroot().find('object').set('model',roofpath.name);rt.write(rooflib/'node.xml',encoding='unicode');shutil.copy2(roofsrc.parent/'materials.xml',rooflib/'materials.xml');roofposes=[]
for e in root.findall('library'):
 if e.get('name')==roofsrc.parent.name:oldattrs=dict(e.attrib);e.set('name',rooflib.name);roofposes.append({'before':oldattrs,'after':dict(e.attrib)})
# Four small wooden cones, not the bridge or rail components: vertex paint only, exact physical material/geometry/UV.
main=parse(c/'volcano_track.spm');wi=next(i for i,b in enumerate(main['buffers'])if main['materials'][b['material']][0]=='stktex_generic_WoodA.png');wood=copy.deepcopy(main['buffers'][wi]);groups=ns['component_triangles'](wood);painted=[]
for group in groups:
 if len(group)!=16:continue
 for i in sorted({i for j in group for i in wood['indices'][j*3:j*3+3]}):wood['vertices'][i]['color']=(255,100,66);painted.append(i)
assert len([g for g in groups if len(g)==16])==4
(c/'volcano_track.spm').write_bytes(ns['replace_buffers'](main,{wi:wood}))
# Reuse the existing first-map blue sky cube, under unique shared filenames.
skyBefore=dict(root.find('sky-box').attrib);skyNames=[];skySources=[]
for side in ['top','bottom','east','west','south','north']:
 src=pack/'textures/canyon-shared-placement-v1'/('genericskybox_'+side+'.jpg');name='vr_v36_lava_sky_'+side+'.jpg';shutil.copy2(src,tex/name);skyNames.append(name);skySources.append({'side':side,'source':info(src),'alias':info(tex/name)})
root.find('sky-box').set('texture',' '.join(skyNames))
for name in skyBefore['texture'].split():
 assert all(name not in str(parse(f)['materials'])for f in c.glob('*.spm'))
 assert name not in(c/'materials.xml').read_text();removed.append(info(c/name));(c/name).unlink()
sun=root.find('sun');sunBefore=dict(sun.attrib);sun.set('sun-diffuse','225 172 125');sun.set('ambient','85 88 112');sun.set('sun-specular','255 190 95');sun.set('fog-max','.14')
# Lean the visual smoke around its own low centroid; exact local source model/bounds and eruption anchor remain.
smoke=root.find('object[@model="AshColumn.spm"]');smokeBefore=dict(smoke.attrib);sd=parse(c/'AshColumn.spm');sv=[v['position']for b in sd['buffers']for v in b['vertices']];low=sorted(sv,key=lambda v:v[1])[:max(8,len(sv)//16)];pivot=[sum(v[k]for v in low)/len(low)for k in range(3)];pos=list(map(float,smoke.get('xyz').split()));scale=list(map(float,smoke.get('scale').split()));q=[pivot[k]*scale[k]for k in range(3)];co=math.cos(math.radians(-50));si=math.sin(math.radians(-50));rot=[co*q[0]-si*q[1],si*q[0]+co*q[1],q[2]];pos=[pos[k]+q[k]-rot[k]for k in range(3)];smoke.set('xyz',' '.join(f'{v:.9f}'for v in pos));smoke.set('hpr','0 0 -50')
scene.write(c/'scene.xml',encoding='unicode')
proof={'baseCandidate':'V35','stage':'Early coherent visual batch. Bush and mound grounding is the next source step; independent/native/runtime gates separate.','mudSourceLibrary':str(mudsrc),'newMudLibrary':str(mudlib),'mudSourceModels':mudmodels,'newMudTextureAlias':info(tex/alias),'newMudGlossAlias':info(mudlib/gloss),'mudModelsAndUsedTexturesBytesBefore':mudBefore,'mudModelsAndUsedTexturesBytesAfter':mudAfter,'mudOriginalPoseChangesNameOnly':mudposes,'mapMudModelAliasChanges':mapModels,'oldMapMudMaterial':oldMudMat,'newMapMudMaterial':newMudMat,'newRoofModel':info(roofpath),'sourceRoofModel':info(roofsrc),'roofTrianglesBefore':33,'roofTrianglesAfter':25,'roofHeaderAndActiveBoundsRetained':True,'roofOriginalCone16FacesAndFlagRetained':True,'roofVertexColoursAndUVAuthored':True,'roofOriginalPoseChangesNameOnly':roofposes,'woodBuffer':wi,'woodRoofVertexColorIndices':sorted(set(painted)),'woodPositionsNormalsIndicesUVPhysicalMaterialRetained':True,'skyBefore':skyBefore,'skyAfter':root.find('sky-box').attrib,'reusedSkyTextureSources':skySources,'sunBefore':sunBefore,'sunAfter':dict(sun.attrib),'smokeBefore':smokeBefore,'smokeAfter':dict(smoke.attrib),'smokeLocalPivot':pivot,'smokeSourceLocalModelUnchanged':True,'removedCandidateOwnedUnreferencedImages':removed,'originalSourceImagesAndDonorsPreserved':True,'newPixels':False,'productionIntegrated':False,'referenceAcceptance':False}
(w/'visual-batch-preflight.json').write_text(json.dumps(proof,indent=2));print('V36_VISUAL_BATCH_SOURCE_READY',mudBefore,mudAfter,len(raw),len(removed),flush=True)
