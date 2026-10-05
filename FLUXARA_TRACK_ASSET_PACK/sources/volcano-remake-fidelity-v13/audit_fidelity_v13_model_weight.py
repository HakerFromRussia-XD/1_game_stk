from pathlib import Path
import sys,json
r=Path(__file__).resolve().parent;sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
w=r/'fidelity-v13';before=r/'fidelity-v12/candidate';c=w/'candidate';f=json.loads((w/'fountain-changes.json').read_text());globaltex=Path(f['newGlobalTexture']);repo=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources');rows=[]
def deps(p):
 names={n for row in parse(p)['materials']for n in row if n};files={};missing=[]
 for name in names:
  candidates=[p.parent/name,repo/'textures'/name]
  if name==f['textureAlias']:candidates.insert(0,globaltex)
  path=next((x for x in candidates if x.is_file()),None)
  if path:files[name]=path.stat().st_size
  else:missing.append(name)
 return files,sorted(missing)
for p in sorted(c.glob('*.spm')):
 q=before/p.name
 if not q.is_file():continue
 a,miss1=deps(q);b,miss2=deps(p);assert miss1==miss2,(p.name,miss1,miss2)
 assert sorted(a.values())==sorted(b.values()),p.name
 pre=q.stat().st_size+sum(a.values());post=p.stat().st_size+sum(b.values());model_change=(p.stat().st_size/q.stat().st_size-1)*100;assert model_change<=20,p.name
 # Any identical unresolved/shared texture dependency can only reduce a positive percentage.
 rows.append({'model':p.name,'beforeModelAndResolvedTextureBytes':pre,'afterModelAndResolvedTextureBytes':post,'modelBytesChangePercent':model_change,'modelWithTextureIncreaseUpperBoundPercent':max(model_change,0),'unchangedTextureNamesNotResolvedByThisLocalDirectoryCheck':miss1,'upper20PercentPassed':True})
proof={'scope':'Every retained map SPM against V12. Model-byte growth is a conservative upper bound when all texture dependency byte sizes stay equal; filenames of equal-byte texture aliases may change. Inherited image references outside local/global texture directories are listed, not asserted resolved. New fountain compared separately with known original component and texture. These per-model counts are not summed app size.','models':rows,'newFountainModelWithTextureChangePercent':f['modelWithTextureWeightChangePercent'],'allUpper20PercentPassed':True};(w/'model-texture-weight-audit.json').write_text(json.dumps(proof,indent=2));print('V13_RETAINED_MODELS_WEIGHT_UPPER_BOUND_VERIFIED',len(rows),max(x['modelWithTextureIncreaseUpperBoundPercent']for x in rows))
