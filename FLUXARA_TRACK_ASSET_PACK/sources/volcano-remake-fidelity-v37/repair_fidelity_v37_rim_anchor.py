from pathlib import Path
import collections,copy,hashlib,json,math,shutil,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v37';c=w/'candidate';rejected_dir=w/'rejected-interface-draft'
if not rejected_dir.exists():
 rejected_dir.mkdir()
 for name in ['rim-preflight.json','background-preflight.json','asset-registration.json','final-blend-verification.json','native-finalize.log','preservation.log']:
  if(w/name).is_file():shutil.copy2(w/name,rejected_dir/name)
 shutil.copy2(c/'scene.xml',rejected_dir/'scene.xml');shutil.copytree(w/'native',rejected_dir/'native');shutil.copytree(w/'screenshots',rejected_dir/'screenshots')
 (rejected_dir/'rejection.json').write_text(json.dumps({'reason':'Source verifier rejected interface error0.502243689m: bbox minimum used instead of actual open-boundary height. This static/native experiment is not accepted.','productionIntegrated':False,'runtimeGameplayChecked':False},indent=2))
base_rim37=json.loads((rejected_dir/'rim-preflight.json').read_text())
res=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources');sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse;from terrain_triangle_distance import triangle_distance,point_triangle_distance
tree=E.parse(c/'scene.xml');root=tree.getroot()
for q in base_rim37['rims']:
 e=root.find('library[@id="'+q['before']['id']+'"]');e.attrib.clear();e.attrib.update(q['before'])
 for ch in q['linkedPlants']:
  e=root.find('library[@id="'+ch['before']['id']+'"]');e.attrib.clear();e.attrib.update(ch['before'])
plants=json.loads((r/'fidelity-v36/plant-grounding.json').read_text())['placements'];groups=json.loads((r/'fidelity-v32/seam-changes.json').read_text())['placements'];s=(r/'build_fidelity_v37_rims.py').read_text();exec(s[s.index('def tris('):s.index("gd=model('fluxara_driftlib_volcano_grass_cap_v32')")])
gd=model('fluxara_driftlib_volcano_grass_cap_v32');buf=gd['buffers'][0]
def key(i):return tuple(round(v,6)for v in buf['vertices'][i]['position'])
edges=collections.Counter(tuple(sorted((key(buf['indices'][j+k]),key(buf['indices'][j+(k+1)%3]))))for j in range(0,len(buf['indices']),3)for k in range(3));pts={v for edge,n in edges.items()if n==1 for v in edge};edge_y={v['position'][1]for v in buf['vertices']if tuple(round(x,6)for x in v['position'])in pts};assert len(edge_y)==1;anchor=next(iter(edge_y))
body=s[s.index("gd=model('fluxara_driftlib_volcano_grass_cap_v32')"):s.index("unused=c/'Lava_004_NORM.jpg'")];body=body.replace("cap_anchor=gd['bounds'][1]","cap_anchor=anchor");exec(body);tree.write(c/'scene.xml',encoding='unicode');base=json.loads((r/'fidelity-v36/preservation-verification.json').read_text());size=sum(f.stat().st_size for f in c.rglob('*')if f.is_file());shared=base['acceptedSharedHistoryBytes']+base['acceptedSharedTextureHistoryBytes']+base['newSharedRuntimeAllFilesBytes']+base['newSharedGlobalAliasesAllFilesBytes'];total=size+shared;assert total<base['allCandidateAndAcceptedHistoryBytes']
proof={'baseCandidate':'V36','rims':rows,'rejectedHigherVariants':rejected,'reusedSources':sources,'changedCapInstances':sum(q['before']!=q['after']for q in rows),'linkedPlantInstances':sum(len(q['linkedPlants'])for q in rows),'minimumRequiredRoadTriangleClearanceMeters':.25,'protectedRoadTriangles':2032,'newSPMTextureMaterialPayloadBytes':0,'removedUnusedCandidateImage':base_rim37['removedUnusedCandidateImage'],'candidateAllFilesBytes':size,'allCandidateAndAcceptedHistoryBytes':total,'savingVsV36Bytes':base['allCandidateAndAcceptedHistoryBytes']-total,'v1Bytes':base['integratedV1BaselineBytes'],'actualWeldedOpenBoundaryAnchorLocalY':anchor,'lipHeightMeaning':'Height above the open interface, not bounding-box height. Actual planar interface retained at old world height.','originalBoundingMinAnchorDraftRejected':True,'productionIntegrated':False,'referenceAcceptance':False};(w/'rim-preflight.json').write_text(json.dumps(proof,indent=2));bg=json.loads((w/'background-preflight.json').read_text());bg.update({'candidateAllFilesBytes':size,'allCandidateAndAcceptedHistoryBytes':total,'savingVsV36Bytes':base['allCandidateAndAcceptedHistoryBytes']-total});(w/'background-preflight.json').write_text(json.dumps(bg,indent=2));print('V37_CORRECT_INTERFACE_ANCHOR_AND_STRONGER_RIMS_READY',anchor,total,flush=True)
