from pathlib import Path
import hashlib,json,math,sys,xml.etree.ElementTree as E
r=Path(__file__).resolve().parent;w=r/'fidelity-v38';c=w/'candidate';res=Path('/Users/motoricallc/Downloads/fluxara-drift/iosApp/FluxaraResources');sys.path.insert(0,str(r.parent/'shared-object-redesign'));from spm_io import parse
from terrain_triangle_distance import triangle_distance,point_triangle_distance
tree=E.parse(c/'scene.xml');root=tree.getroot();s=(r/'build_fidelity_v37_rims.py').read_text();exec(s[s.index('def tris('):s.index("gd=model('fluxara_driftlib_volcano_grass_cap_v32')")]);
for lib in (w/'shared-runtime').iterdir():cache[lib.name]=parse(lib/E.parse(lib/'node.xml').getroot().find('object').get('model'))
s=(r/'build_fidelity_v37_background.py').read_text();exec(s[s.index('def height('):s.index('choices=')]);bgentry=root.find('library[@name="fluxara_driftlib_volcano_rolling_terrain_v38"]');bgtris=[[world(v,bgentry.attrib)for v in t]for t in tris(model(bgentry.get('name')))];bgbox=[box(t)for t in bgtris];mounds=[];rows=[]
for q in json.loads((r/'fidelity-v37/background-preflight.json').read_text())['placements']:
 el=root.find('library[@id="'+q['attrs']['id']+'"]');prev=dict(el.attrib);p,sc,yaw=params(prev);radius=sc[0]if q['role']=='Mound'else sc[1]*.6;sample=[height(bgtris,bgbox,p[0],p[2])]+[height(bgtris,bgbox,p[0]+radius*math.cos(a),p[2]+radius*math.sin(a))for a in [j*math.pi/4 for j in range(8)]];assert all(h is not None for h in sample)
 y=min(sample)-.18 if q['role']=='Mound'else max([sample[0]]+[h for t,b in mounds if(h:=height(t,b,p[0],p[2]))is not None]);a=dict(prev);a['xyz']=f'{p[0]:.8f} {y:.8f} {p[2]:.8f}';valid,proof=certificate(a,required=2.);assert valid,(a,proof);el.attrib.clear();el.attrib.update(a);rows.append({'role':q['role'],'before':prev,'after':a,'groundSamples':sample,'clearance':proof})
 if q['role']=='Mound':t=[[world(v,a)for v in z]for z in tris(model(a['name']))];mounds.append((t,[box(z)for z in t]))
assert len(rows)==84;tree.write(c/'scene.xml',encoding='unicode');(w/'background-grounding.json').write_text(json.dumps({'placements':rows,'backgroundTrees':64,'backgroundMounds':20,'unchangedXZOrientationScale':True},indent=2));print('V38_BACKGROUND_GROUNDED',len(rows),flush=True)
