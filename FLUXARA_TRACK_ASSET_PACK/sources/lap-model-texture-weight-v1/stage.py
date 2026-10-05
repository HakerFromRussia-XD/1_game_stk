from pathlib import Path
import hashlib,json,shutil,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;root=r.parents[2];repo=Path('/Users/motoricallc/Downloads/fluxara-drift');res=repo/'iosApp/FluxaraResources';sys.path.insert(0,str(root/'output/shared-object-redesign'));from spm_io import parse,rewrite_texture_names
aliases={};proofs=[];leaf='fluxara_lc_leaf_72.png'
for role,sourceName,newName in [('tree','fluxara_driftlib_round_tree_green_v2','fluxara_driftlib_lc_light_tree_v1'),('bush','fluxara_driftlib_round_bush_green_v2','fluxara_driftlib_lc_light_bush_v1')]:
 source=res/'library'/sourceName;dest=r/'new-library'/newName;dest.mkdir(parents=True,exist_ok=True)
 for f in source.iterdir():
  if f.is_file():shutil.copy2(f,dest/f.name)
 for file in dest.glob('*.spm'):
  before=parse(file);names=[[leaf if n=='fluxara_circuit_leaf_v2.png'else n for n in pair]for pair in before['materials']];file.write_bytes(rewrite_texture_names(before,names));after=parse(file);oldOffset=30+sum(2+sum(len(n.encode())for n in pair)for pair in before['materials']);newOffset=30+sum(2+sum(len(n.encode())for n in pair)for pair in after['materials']);exact=before['raw'][oldOffset:]==after['raw'][newOffset:];assert exact;proofs.append({'role':role,'library':newName,'model':str(file),'geometryVertexRecordsNormalsColorsUVAndIndicesExact':exact,'originalModel':str(source/file.name),'originalSha256':hashlib.sha256((source/file.name).read_bytes()).hexdigest(),'currentSha256':hashlib.sha256(file.read_bytes()).hexdigest()})
 m=dest/'materials.xml'
 if m.exists():m.write_text(m.read_text().replace('fluxara_circuit_leaf_v2.png',leaf))
 (dest/leaf).unlink(missing_ok=True)
 if role=='bush':(dest/'dp_palette.png').unlink(missing_ok=True)
 (r/'new-textures').mkdir(exist_ok=True);shutil.copy2(r/leaf,r/'new-textures'/leaf)
 aliases[role]=newName
pairs={'fluxara_driftlib_lc_green_accacia_a_v1':aliases['tree'],'fluxara_driftlib_lc_green_agave_a_v1':aliases['bush'],'fluxara_driftlib_lc_green_autumnSmallBush_a_v1':aliases['bush']};wrappers=r/'wrappers';wrappers.mkdir(exist_ok=True)
for name,lib in pairs.items():
 source=res/'library'/name;dest=wrappers/name;shutil.copytree(source,dest,dirs_exist_ok=True);node=E.parse(dest/'node.xml')
 for el in node.getroot().findall('library'):el.set('name',lib)
 node.write(dest/'node.xml',encoding='utf-8',xml_declaration=True)
groups=json.loads((root/'output/shared-placement-1-10/model-texture-weight/library-groups.json').read_text());weights=[]
for q in groups:
 current=q['current'].get('library')
 if current not in pairs:continue
 folder=r/'new-library'/pairs[current];modelBytes=sum(f.stat().st_size for f in folder.glob('*.spm'));used={n for model in folder.glob('*.spm')for d in [parse(model)]for b in d['buffers']if b['indices']for n in d['materials'][b['material']]if n};textureBytes=sum(((folder/n)if(folder/n).exists()else r/'new-textures'/n).stat().st_size for n in used);new=modelBytes+textureBytes;old=q['original']['totalModelAndTextureBytes'];pct=100*(new/old-1);assert pct<=20;weights.append({'originalObjectFamily':q['original']['library'],'wrapper':current,'originalModelPlusTexturesBytes':old,'candidateModelBytes':modelBytes,'candidateUsedTextureBytes':textureBytes,'candidateModelPlusTexturesBytes':new,'changePercent':pct,'within20Percent':True})
q={'stage':'Isolated candidate only; not integrated into project, native final or installed app','scope':'Technical texture-resolution variant for three low-byte original model families. Same tree/bush geometry, shaders, UV and placements. Higher-resolution donor untouched.','leafTextureResolution':[72,72],'leafTextureBytes':(r/leaf).stat().st_size,'originalLeafTextureBytes':(res/'textures/fluxara_circuit_leaf_v2.png').stat().st_size,'models':proofs,'wrapperLibraryNamesChangedOnly':pairs,'weights':weights};(r/'candidate.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n');print('LAP_THREE_REPLACEMENT_FAMILIES_WEIGHT_CANDIDATE_READY',weights,flush=True)
