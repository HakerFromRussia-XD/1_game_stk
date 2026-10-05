import bpy,sys,math,json,random,bmesh
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
r=Path(__file__).resolve().parent;f=r/'candidate';pack=Path('/Users/motoricallc/Downloads/fluxara-drift/FLUXARA_TRACK_ASSET_PACK');rng=random.Random(126)
bpy.ops.wm.open_mainfile(filepath=str(r/'source-inspection.blend'));bpy.context.preferences.filepaths.save_version=0
# Original road and terrain BVHs are used only for exclusion and ground placement.
roads=[];groundvs=[];groundfs=[]
for o in list(bpy.context.scene.objects):
 if o.type!='MESH':continue
 tex={Path(n.image.filepath).name for m in o.data.materials if m and m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image}
 if tex & {'AC_auto1.jpg','Aoitori_road3.jpg','msl2-road1_r.jpg'}:
  for v in o.data.vertices:roads.append(o.matrix_world@v.co)
 if any('grass' in t.lower() or t=='kusaiwa.jpg' for t in tex):
  off=len(groundvs);groundvs.extend(o.matrix_world@v.co for v in o.data.vertices);groundfs.extend(tuple(off+j for j in p.vertices) for p in o.data.polygons)
terrain=BVHTree.FromPolygons(groundvs,groundfs)
# Route exclusion uses actual drivable triangles, not only driveline points.
rv=[];rf=[]
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 tex={Path(n.image.filepath).name for m in o.data.materials if m and m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image}
 if tex & {'AC_auto1.jpg','Aoitori_road3.jpg','msl2-road1_r.jpg','Tunnel_AC_auto1.jpg'}:
  off=len(rv);rv.extend(o.matrix_world@v.co for v in o.data.vertices);rf.extend(tuple(off+j for j in p.vertices) for p in o.data.polygons)
roadbvh=BVHTree.FromPolygons(rv,rf)
for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
col=bpy.data.collections.new('DP Reference Scenery');bpy.context.scene.collection.children.link(col)
m=bpy.data.materials.new('DP Reference Palette');m.use_nodes=True;t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(f/'dp_palette.png'));s=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');m.node_tree.links.new(t.outputs['Color'],s.inputs['Base Color']);s.inputs['Roughness'].default_value=.78
P=lambda c:((c%4+.5)/4,1-(c//4+.5)/4)
def paint(o,fn):
 oldidx=[p.material_index for p in o.data.polygons];o.data.materials.clear();o.data.materials.append(m)
 while o.data.color_attributes:o.data.color_attributes.remove(o.data.color_attributes[0])
 uv=o.data.uv_layers[0] if o.data.uv_layers else o.data.uv_layers.new(name='UVMap')
 for p,old in zip(o.data.polygons,oldidx):
  c=fn(p,old);p.material_index=0
  for j in p.loop_indices:uv.data[j].uv=P(c)
 return o

def append(file,name,newname,target):
 with bpy.data.libraries.load(str(pack/file),link=False) as (a,b):b.objects=[name]
 o=b.objects[0];col.objects.link(o);o.name=newname;o.location=(0,0,0);o.rotation_euler=(0,0,0);o.scale=(1,1,1)
 bpy.context.view_layer.objects.active=o;o.select_set(True);o.data=o.data.copy()
 if name=='Fluxara_Autumn_E_High':
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.delete(bm,geom=[p for p in bm.faces if p.material_index==1],context='FACES');bm.to_mesh(o.data);bm.free()
 o.data.calc_loop_triangles();dec=o.modifiers.new('Race-distance budget','DECIMATE');dec.ratio=min(1,target/max(1,len(o.data.loop_triangles)));bpy.ops.object.modifier_apply(modifier=dec.name);o.select_set(False)
 return o

tree=append('models/shared/fluxara_autumn_trees_efg_v1/Fluxara Autumn Volume Trees.blend','Fluxara_Autumn_E_High','DP_RoundedTree_Prototype',370)
paint(tree,lambda p,i:7 if i==1 else 4);
bush=append('models/shared/fluxara_autumn_rounded_bush_v1/Fluxara Autumn Rounded Bush.blend','Fluxara_Autumn_Rounded_Bush','DP_RoundedBush_Prototype',100);paint(bush,lambda p,i:4)
fir=append('models/shared/fluxara_green_firs_v1/Fluxara Green Firs.blend','Fluxara_GreenFir_A_Medium','DP_Fir_Prototype',290);paint(fir,lambda p,i:7 if p.center.z<1.2 else 4)
# Normalize donor meshes for documented placements; source libraries are untouched.
for o in [tree,bush,fir]:
 lo=[min(v.co[k] for v in o.data.vertices) for k in range(3)];hi=[max(v.co[k] for v in o.data.vertices) for k in range(3)]
 for v in o.data.vertices:
  for k in range(3):v.co[k]=(v.co[k]-(lo[k] if k==2 else (lo[k]+hi[k])/2))/(hi[k]-lo[k])
 if o==tree:
  for v in o.data.vertices:v.co.z=.25+v.co.z*.75
 for p in o.data.polygons:p.use_smooth=True
 o.data.update()
# Stable rounded crown topology: five low-poly ellipsoids follow the donor's clustered silhouette.
# Rebuilding their coarse latitude rings avoids the spiky collapses produced by aggressive decimation.
def ellipsoid_cluster(o,clusters,segments,rings):
 vs=[];faces=[]
 for cx,cy,cz,sx,sy,sz in clusters:
  off=len(vs);vs.append((cx,cy,cz+sz));
  for j in range(1,rings):
   th=math.pi*j/rings
   for i in range(segments):
    a=math.tau*i/segments;vs.append((cx+sx*math.sin(th)*math.cos(a),cy+sy*math.sin(th)*math.sin(a),cz+sz*math.cos(th)))
  bot=len(vs);vs.append((cx,cy,cz-sz))
  for i in range(segments):faces.append((off,off+1+i,off+1+(i+1)%segments))
  for j in range(rings-2):
   for i in range(segments):
    q=off+1+j*segments;faces.append((q+i,q+segments+i,q+segments+(i+1)%segments,q+(i+1)%segments))
  q=off+1+(rings-2)*segments
  for i in range(segments):faces.append((q+i,bot,q+(i+1)%segments))
 me=bpy.data.meshes.new(o.name+'_Rounded');me.from_pydata(vs,[],faces);me.update();o.data=me;paint(o,lambda p,i:4)
 for p in me.polygons:p.use_smooth=True
ellipsoid_cluster(tree,[(0,0,.72,.29,.3,.29),(-.28,0,.6,.24,.25,.24),(.28,.03,.64,.25,.24,.25),(0,.26,.61,.26,.23,.24),(0,-.25,.64,.26,.25,.24),(-.15,-.17,.86,.22,.23,.2),(.16,.17,.83,.24,.25,.23)],10,5)
ellipsoid_cluster(bush,[(0,0,.48,.3,.32,.38),(-.27,0,.36,.23,.25,.28),(.27,.04,.32,.24,.23,.25),(0,-.25,.32,.25,.22,.27),(0,.24,.38,.24,.24,.28)],6,4)
# A dedicated pooled foliage variant supplies painted leaf detail, while preserving the clustered crown style.
lm=bpy.data.materials.new('DP Painted Green Foliage');lm.use_nodes=True;lt=lm.node_tree.nodes.new('ShaderNodeTexImage');lt.image=bpy.data.images.load(str(f/'dp_leaf_v2.png'));lm.node_tree.links.new(lt.outputs['Color'],lm.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
def leaf_uv(o):
 o.data.materials.clear();o.data.materials.append(lm);uv=o.data.uv_layers[0]
 for p in o.data.polygons:
  p.material_index=0;axis=max(range(3),key=lambda k:abs(p.normal[k]));axes=[k for k in range(3) if k!=axis]
  for li in p.loop_indices:
   co=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(co[axes[0]]*2.4,co[axes[1]]*2.4)
leaf_uv(tree);leaf_uv(bush)
# Fir donor silhouette is retained; trunk polygons keep the brown atlas cell.
fir.data.materials.append(lm)
for p in fir.data.polygons:
 if p.center.z>.1:
  p.material_index=1
  for li in p.loop_indices:
   co=fir.data.vertices[fir.data.loops[li].vertex_index].co;fir.data.uv_layers[0].data[li].uv=(co.x*2.3,co.z*2.3)
bpy.ops.mesh.primitive_cone_add(vertices=8,radius1=.065,radius2=.04,depth=.46,location=(0,0,.23));tr=bpy.context.object;paint(tr,lambda p,i:7)
bpy.ops.object.select_all(action='DESELECT');tr.select_set(True);tree.select_set(True);bpy.context.view_layer.objects.active=tree;bpy.ops.object.join();tree.select_set(False)
protos=[tree,bush,fir];rows=[];treepoints=[]
def ground(x,y):
 hit=terrain.ray_cast(Vector((x,y,250)),Vector((0,0,-1)),500)[0]
 return hit.z if hit else None

def clear_road(x,y,radius):
 for dx,dy in [(0,0),(radius,0),(-radius,0),(0,radius),(0,-radius),(radius*.707,radius*.707),(-radius*.707,radius*.707),(radius*.707,-radius*.707),(-radius*.707,-radius*.707)]:
  if roadbvh.ray_cast(Vector((x+dx,y+dy,250)),Vector((0,0,-1)),500)[0] is not None:return False
 return True

def place(proto,name,x,y,z,w,d,h,angle=0):
 o=bpy.data.objects.new(name,proto.data);col.objects.link(o);o.location=(x,y,z);o.scale=(w,d,h);o.rotation_euler.z=angle;rows.append({'name':name,'prototype':proto.name,'xyz':[x,z,y],'dimensions':[w,h,d],'rotationZRadians':angle});return o
components=json.loads((r/'components.json').read_text());candidates=[]
for key in ['40','68','51']:
 for box in components[key]['components']:
  lo,hi=box['lo'],box['hi'];x=(lo[0]+hi[0])/2;y=(lo[2]+hi[2])/2;h=hi[1]-lo[1]
  if h<3 or abs(x)>335 or y>235 or y<-200:continue
  candidates.append((x,y,h))
rng.shuffle(candidates)
for x,y,h in candidates:
 if len(treepoints)>=95:break
 if any((x-a)**2+(y-b)**2<12**2 for a,b in treepoints):continue
 w=rng.uniform(7.5,10.5);h=rng.uniform(9,12);z=ground(x,y)
 if z is None or not clear_road(x,y,w*.62+1):continue
 proto=fir if len(treepoints)%5==0 else tree;w=w*.73 if proto==fir else w
 place(proto,f'DP_Tree_{len(treepoints):03}',x,y,z-.15,w,w*.9,h,rng.uniform(0,6.28));treepoints.append((x,y))
# Dense new outer perimeter groups. Every root grounded in the original terrain and checked against all road triangles.
for i in range(98):
 a=i*math.tau/98;x=40+math.cos(a)*rng.uniform(265,310);y=15+math.sin(a)*rng.uniform(145,205)
 if any((x-aa)**2+(y-b)**2<13**2 for aa,b in treepoints):continue
 z=ground(x,y);w=rng.uniform(9,15)
 if z is None or not clear_road(x,y,w*.6+2):continue
 proto=fir if i%4==0 else tree;place(proto,f'DP_Tree_{len(treepoints):03}',x,y,z-.1,w,w*.85,rng.uniform(13,18),rng.uniform(0,6.28));treepoints.append((x,y))
# Lower shrubs replace the old grass billboards close to the barriers.
shrubs=[];spots=components['3']['components'];rng.shuffle(spots)
for box in spots:
 if len(shrubs)>=60:break
 lo,hi=box['lo'],box['hi'];x=(lo[0]+hi[0])/2;y=(lo[2]+hi[2])/2
 if any((x-a)**2+(y-b)**2<4.5**2 for a,b in shrubs):continue
 z=ground(x,y)
 if z is None or not clear_road(x,y,1.1):continue
 w=rng.uniform(1.5,2.5);place(bush,f'DP_Bush_{len(shrubs):03}',x,y,z-.08,w,w*.85,w*.7,rng.uniform(0,6.28));shrubs.append((x,y))
# Resolve the programmed quad corners without changing their source XML.
import xml.etree.ElementTree as E
qs=[]
for e in E.parse(r/'before/quads.xml').getroot().findall('quad'):
 q=[]
 for j in range(4):
  v=e.get('p'+str(j))
  if ':' in v:aa,bb=map(int,v.split(':'));p=qs[aa][bb]
  else:p=tuple(map(float,v.split()))
  q.append(p)
 qs.append(q)
centers=[Vector(((q[0][0]+q[1][0])/2,(q[0][2]+q[1][2])/2)) for q in qs]
# Close foliage forms continuous groups around both sides of the circuit.
for idx in range(0,len(qs),7):
 q=qs[idx];c=centers[idx];left=Vector((q[0][0],q[0][2]));right=Vector((q[1][0],q[1][2]));across=(left-right).normalized();half=(left-right).length/2
 for side in [-1,1]:
  for off in [half+2.4,half+5.4]:
   p=c+across*side*off;x,y=p;z=ground(x,y)
   if z is not None and clear_road(x,y,1.15) and not any((x-a)**2+(y-b)**2<2.7**2 for a,b in shrubs):
    w=rng.uniform(1.9,3.0);place(bush,f'DP_Bush_{len(shrubs):03}',x,y,z-.12,w,w*.9,w*.72,rng.uniform(0,6.28));shrubs.append((x,y))
    if len(shrubs)>=185:break
  if len(shrubs)>=185:break
 if len(shrubs)>=185:break
for idx in range(0,len(qs),13):
 q=qs[idx];c=centers[idx];across=Vector((q[0][0]-q[1][0],q[0][2]-q[1][2])).normalized();half=Vector((q[0][0]-q[1][0],q[0][2]-q[1][2])).length/2
 for side in [-1,1]:
  p=c+across*side*(half+rng.uniform(10,18));x,y=p;z=ground(x,y);w=rng.uniform(8,12)
  if z is None or not clear_road(x,y,w*.62+1) or any((x-a)**2+(y-b)**2<8**2 for a,b in treepoints):continue
  place(tree if idx%5 else fir,f'DP_Tree_{len(treepoints):03}',x,y,z-.12,w,w*.92,rng.uniform(8.8,11.5),rng.uniform(0,6.28));treepoints.append((x,y))
  if len(treepoints)>=260:break
 if len(treepoints)>=260:break
# A rounded hillside variant is needed: the donor mesa's straight vertical walls dominated the gameplay camera.
# Preserve that donor; author a low-poly rounded hill outside all drivable geometry.
bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=10,radius=1);mesa=bpy.context.object;mesa.name='DP_RoundedHill_Prototype'
for c in list(mesa.users_collection):c.objects.unlink(mesa)
col.objects.link(mesa)
for v in mesa.data.vertices:v.co.z=max(0,v.co.z)
paint(mesa,lambda p,i:14 if p.center.z>.70 else 8 if p.center.z>.1 else 7)
for p in mesa.data.polygons:p.use_smooth=True
for i,(x,y,w,d,h) in enumerate([(-120,205,100,85,39),(20,205,125,100,46),(160,190,90,100,36),(320,60,100,160,35),(295,-135,100,100,39),(85,-200,190,120,32),(-120,-190,110,100,40),(-320,-20,110,180,34)]):
 if not clear_road(x,y,min(w,d)*.57):continue
 z=ground(x,y)
 if z is None:continue
 place(mesa,f'DP_Hill_{i}',x,y,z-5,w*.5,d*.5,h*.72)
 for j in range(4):
  xx=x+rng.uniform(-w*.26,w*.26);yy=y+rng.uniform(-d*.22,d*.22);place(fir if j%3==0 else tree,f'DP_HillTree_{i}_{j}',xx,yy,z-5+h*.72*math.sqrt(max(0,1-((xx-x)/(w*.5))**2-((yy-y)/(d*.5))**2))-.3,10,9,rng.uniform(10,15),rng.uniform(0,6.28))
protos.append(mesa)
# Small white daisies from the reference, placed within the shrub beds.
fm=bpy.data.materials.new('DP White Daisy');fm.use_nodes=True;ft=fm.node_tree.nodes.new('ShaderNodeTexImage');ft.image=bpy.data.images.load(str(f/'dp_flower.png'));fs=next(n for n in fm.node_tree.nodes if n.type=='BSDF_PRINCIPLED');fm.node_tree.links.new(ft.outputs['Color'],fs.inputs['Base Color']);fm.node_tree.links.new(ft.outputs['Alpha'],fs.inputs['Alpha'])
me=bpy.data.meshes.new('DP_Daisy_Cross');me.from_pydata([(-.5,0,0),(.5,0,0),(.5,0,1),(-.5,0,1),(0,-.5,0),(0,.5,0),(0,.5,1),(0,-.5,1)],[],[(0,1,2,3),(4,5,6,7)]);me.materials.append(fm);uv=me.uv_layers.new(name='UVMap')
for p in me.polygons:
 for j,co in zip(p.loop_indices,[(0,0),(1,0),(1,1),(0,1)]):uv.data[j].uv=co
flower=bpy.data.objects.new('DP_Daisy_Prototype',me);col.objects.link(flower);protos.append(flower)
for i,(x,y) in enumerate(shrubs[::2]):
 z=ground(x,y);place(flower,f'DP_Daisy_{i}',x+.3,y-.35,z+.65,.9,.9,.9,rng.uniform(0,6.28))
# More small daisies and grass clusters in the close beds.
for i,(x,y) in enumerate(shrubs):
 for j in range(3):
  xx=x+rng.uniform(-1.4,1.4);yy=y+rng.uniform(-1.4,1.4);z=ground(xx,yy)
  if z is not None and clear_road(xx,yy,.25):place(flower,f'DP_FlowerBed_{i}_{j}',xx,yy,z+.15,.6,.6,.6,rng.uniform(0,6.28))
vs=[];ff=[]
for j in range(9):
 a=j*2.399;cx=math.cos(a)*.3;cy=math.sin(a)*.3;h=.45+(j%3)*.13;off=len(vs);vs.extend([(cx-.07,cy,0),(cx+.07,cy,0),(cx+.12,cy+.03,h)]);ff.append((off,off+1,off+2))
me=bpy.data.meshes.new('Grass tuft');me.from_pydata(vs,[],ff);tuft=bpy.data.objects.new('DP_GrassTuft_Prototype',me);col.objects.link(tuft);paint(tuft,lambda p,i:5 if p.index%3 else 4);protos.append(tuft)
for i,(x,y) in enumerate(shrubs):
 for j in range(3):
  xx=x+rng.uniform(-2,2);yy=y+rng.uniform(-2,2);z=ground(xx,yy)
  if z is not None and clear_road(xx,yy,.6):place(tuft,f'DP_Grass_{i}_{j}',xx,yy,z,1.1,1.1,1.1,rng.uniform(0,6.28))
# Wooden rails replace the old photographic wire-fence strips.
def boxmesh(name,boxes):
 vs=[];fs=[]
 for x,y,z,w,d,h in boxes:
  off=len(vs);vs.extend([(x+sx*w/2,y+sy*d/2,z+sz*h/2) for sx,sy,sz in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]);fs.extend(tuple(off+j for j in q) for q in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);col.objects.link(o);return o
rail=boxmesh('DP_WoodRail_Prototype',[(-.48,0,.7,.045,.16,1.4),(.48,0,.7,.045,.16,1.4),(0,0,.5,1,.1,.15),(0,0,1.05,1,.1,.15)]);paint(rail,lambda p,i:7);protos.append(rail)
for idx in range(0,len(qs),5):
 c=centers[idx];q=qs[idx];t=(centers[(idx+2)%len(qs)]-c).normalized();across=Vector((q[0][0]-q[1][0],q[0][2]-q[1][2])).normalized();half=Vector((q[0][0]-q[1][0],q[0][2]-q[1][2])).length/2
 for side in [-1,1]:
  x,y=c+across*side*(half+6.5);z=ground(x,y)
  if z is not None and clear_road(x,y,2):place(rail,f'DP_Rail_{idx}_{side}',x,y,z,6.7,1,1,math.atan2(t.y,t.x))
# Coral, gold and blue pennant strings provide the festival detail of the reference.
bunting=boxmesh('DP_Bunting_Prototype',[(-.49,0,.5,.018,.07,1),(.49,0,.5,.018,.07,1),(0,0,.96,1,.018,.018)]);paint(bunting,lambda p,i:7);oldverts=[tuple(v.co) for v in bunting.data.vertices];oldfaces=[tuple(p.vertices) for p in bunting.data.polygons];flagstart=len(oldfaces)
for j in range(9):
 x=-.47+j*.106;off=len(oldverts);sag=.09*(1-(x/.5)**2);oldverts.extend([(x,0,.955-sag),(x+.09,0,.955-sag),(x+.045,0,.73-sag)]);oldfaces.append((off,off+1,off+2))
me=bpy.data.meshes.new('Pennants');me.from_pydata(oldverts,[],oldfaces);me.update();bunting.data=me;paint(bunting,lambda p,i:7 if p.index<flagstart else [1,9,2,13][(p.index-flagstart)%4]);protos.append(bunting)
for idx in range(0,len(qs),43):
 q=qs[idx];c=centers[idx];t=(centers[(idx+3)%len(qs)]-c).normalized();across=Vector((q[0][0]-q[1][0],q[0][2]-q[1][2])).normalized();half=Vector((q[0][0]-q[1][0],q[0][2]-q[1][2])).length/2
 for side in [-1,1]:
  x,y=c+across*side*(half+9);z=ground(x,y)
  if z is not None and clear_road(x,y,5.5):place(bunting,f'DP_Pennants_{idx}_{side}',x,y,z,13,1,3.8,math.atan2(t.y,t.x))
# Turn signs are generated from actual local course curvature, with front facing approaching traffic.
for direction in ['Left','Right']:
 sm=bpy.data.materials.new('DP Turn '+direction);sm.use_nodes=True;nt=sm.node_tree;tx=nt.nodes.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(str(f/('dp_turn_'+direction.lower()+'.png')));nt.links.new(tx.outputs['Color'],nt.nodes.get('Principled BSDF').inputs['Base Color'])
 sign=boxmesh('DP_Turn'+direction+'_Prototype',[(-.38,0,.44,.055,.09,.88),(.38,0,.44,.055,.09,.88),(0,0,.87,1,.055,.4)]);paint(sign,lambda p,i:3);sign.data.materials.append(sm)
 uv=sign.data.uv_layers[0]
 for p in sign.data.polygons:
  if p.center.z>.66 and p.normal.y<-.8:
   p.material_index=1
   for li in p.loop_indices:
    co=sign.data.vertices[sign.data.loops[li].vertex_index].co;uv.data[li].uv=(co.x+.5,(co.z-.67)/.4)
 protos.append(sign)
 signs=[]
 for idx in range(8,len(qs)-9,3):
  t0=(centers[idx]-centers[idx-7]).normalized();t1=(centers[idx+7]-centers[idx]).normalized();angle=math.atan2(t0.x*t1.y-t0.y*t1.x,t0.dot(t1))
  if abs(angle)<.22 or (direction=='Left')!=(angle>0):continue
  c=centers[idx]
  if any((c-p).length<22 for p in signs):continue
  q=qs[idx];across=Vector((q[0][0]-q[1][0],q[0][2]-q[1][2])).normalized();half=Vector((q[0][0]-q[1][0],q[0][2]-q[1][2])).length/2
  # Outer side of the curve. Local -Y face is pointed upstream.
  outside=Vector((t0.y,-t0.x))*(1 if angle>0 else -1);x,y=c+outside*(half+2.5);z=ground(x,y)
  if z is not None and clear_road(x,y,1.8):
   rot=math.atan2(t0.y,t0.x)-math.pi/2;place(sign,f'DP_Turn{direction}_{idx}',x,y,z,3.3,1,3.3,rot);signs.append(c)
# Bake directional and cavity shading as vertex color so it also renders in the simulator's fixed pipeline.
for o in protos:
 me=o.data;me.update();colors=me.vertex_colors.new(name='DP Baked Light')
 for p in me.polygons:
  for li in p.loop_indices:
   v=me.vertices[me.loops[li].vertex_index];n=v.normal;z=v.co.z
   light=.79+.21*max(0,n.dot(Vector((-.4,-.35,.85)).normalized()))
   if o in [tree,bush,fir]:light*=.87+.13*min(1,max(0,z))
   colors.data[li].color=(min(1,light*1.02),light,min(1,light*.94),1)
# Store authored/adapted prototypes in reusable source, outside runtime scene.
proto_col=bpy.data.collections.new('DP Reusable Prototypes')
for o in protos:
 for c in list(o.users_collection):c.objects.unlink(o)
 proto_col.objects.link(o)
# Save intermediate source with source metadata, then export all visible scenery only.
bpy.ops.object.select_all(action='DESELECT')
for o in col.objects:o.select_set(True)
sys.path.insert(0,'/Users/motoricallc/Library/Application Support/Blender/4.5/scripts/addons');import io_scene_spm
if not hasattr(bpy.types,'SPM_Export_Operator'): 
 try:io_scene_spm.register()
 except:pass
bpy.ops.screen.spm_export(filepath=str(f/'dp_scenery.spm'),selection_type='selected',localsp=False,applymodifiers=True,export_normal=True,export_vcolor=True,export_tangent=False)
bpy.data.libraries.write(str(r/'DP Reusable Scenery.blend'),set(protos)|{proto_col},fake_user=True)
# Add exact imported runtime track for final editable scene, preserving route/gameplay nodes as metadata.
bpy.ops.screen.spm_import(filepath=str(f/'dp-motorsports-land-ii_track.spm'),extra_tex_path=str(f))
bpy.context.scene['source_scene_xml']=(r/'before/scene.xml').read_text();bpy.context.scene['protected_quads_xml']=(r/'before/quads.xml').read_text();bpy.context.scene['protected_graph_xml']=(r/'before/graph.xml').read_text()
bpy.ops.wm.save_as_mainfile(filepath=str(r/'DP Motorsports Land II.blend'))
(r/'placements.json').write_text(json.dumps(rows,indent=2));print('SCENERY_DONE',len(treepoints),'trees',len(shrubs),'bushes',len(rows),'instances')
