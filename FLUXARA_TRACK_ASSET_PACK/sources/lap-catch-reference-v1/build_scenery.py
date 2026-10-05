import bpy,sys,json,math,shutil,random,xml.etree.ElementTree as E
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
r=Path(__file__).resolve().parent;f=r/'candidate';repo=Path('/Users/motoricallc/Downloads/fluxara-drift');pack=repo/'FLUXARA_TRACK_ASSET_PACK';rng=random.Random(727)
bpy.ops.wm.open_mainfile(filepath=str(r/'source-inspection.blend'));bpy.context.preferences.filepaths.save_version=0
# Original triangles define grounding; all original quads reserve the driving corridor.
gv=[];gf=[]
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 names={Path(n.image.filepath).name for m in o.data.materials if m and m.use_nodes for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image}
 if any('grass' in n or 'sand' in n or n in ['snow.png','snowrock.jpg','city_ground.jpg','city_rock.jpg','rock_mountain.jpg','blackrock.jpg','rockred.jpg','170.jpg','173.jpg','173b.jpg'] for n in names):
  off=len(gv);gv.extend(v.co for v in o.data.vertices);gf.extend(tuple(off+j for j in p.vertices) for p in o.data.polygons)
terrain=BVHTree.FromPolygons(gv,gf)
quads=[]
for e in E.parse(r/'before/quads.xml').getroot().findall('quad'):
 q=[]
 for k in range(4):
  t=e.get('p'+str(k));v=quads[int(t.split(':')[0])][int(t.split(':')[1])] if ':' in t else tuple(map(float,t.split()));q.append(v)
 quads.append(q)
rv=[(v[0],v[2],0) for q in quads for v in q];rf=[tuple(i*4+j for j in range(4)) for i in range(len(quads))];road=BVHTree.FromPolygons(rv,rf)
def ground(x,y):
 v=terrain.ray_cast(Vector((x,y,220)),Vector((0,0,-1)),350)[0];return v.z if v else None
def clear(x,y,radius):
 for i in range(17):
  a=(i-1)*math.tau/16;dx=0 if i==0 else math.cos(a)*radius;dy=0 if i==0 else math.sin(a)*radius
  if road.ray_cast(Vector((x+dx,y+dy,10)),Vector((0,0,-1)),20)[0]:return False
 return True
for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
col=bpy.data.collections.new('Lap Catch Shared Scenery');bpy.context.scene.collection.children.link(col)
# Direct reuse of sixth's actual prototype meshes/materials. Donor library is untouched.
with bpy.data.libraries.load(str(r.parent/'dp-motorsports-rework/DP Reusable Scenery.blend'),link=False) as(a,b):b.objects=[n for n in a.objects if n.endswith('_Prototype')]
protos={o.name:o for o in b.objects}
for o in protos.values():col.objects.link(o);o.hide_render=True;o.hide_set(True)
# Authored castellated tower combines low-poly rounded stone volumes and flag details from the reference.
mat=bpy.data.materials.new('LC Reference Palette');mat.use_nodes=True;t=mat.node_tree.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(f/'dp_palette.png'));mat.node_tree.links.new(t.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
vs=[];faces=[];cols=[]
def box(cx,cy,cz,w,d,h,c):
 n=len(vs);vs.extend([(cx+x*w/2,cy+y*d/2,cz+z*h/2) for x,y,z in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]);faces.extend([tuple(n+j for j in q) for q in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]]);cols.extend([c]*6)
def ring(z,rad,h,c,segments=12):
 n=len(vs)
 for zz in [z,z+h]:
  for k in range(segments):a=k*math.tau/segments;vs.append((rad*math.cos(a),rad*math.sin(a),zz))
 faces.extend([tuple(n+k for k in reversed(range(segments))),tuple(n+segments+k for k in range(segments))]);cols.extend([c,c])
 for k in range(segments):faces.append((n+k,n+(k+1)%segments,n+segments+(k+1)%segments,n+segments+k));cols.append(c)
ring(0,.23,.075,0);ring(.075,.19,.70,0);ring(.22,.198,.035,1);ring(.47,.198,.035,1);ring(.775,.23,.085,1);ring(.86,.21,.055,0)
for k in range(8):a=k*math.tau/8;box(.175*math.cos(a),.175*math.sin(a),.95,.085,.085,.095,0)
box(0,-.192,.42,.08,.013,.13,3);box(0,.192,.42,.08,.013,.13,3);box(-.192,0,.64,.013,.08,.12,3);box(.192,0,.64,.013,.08,.12,3)
ring(.99,.009,.27,7,6);n=len(vs);vs.extend([(0,0,1.25),(.15,0,1.21),(0,0,1.15)]);faces.append((n,n+1,n+2));cols.append(1)
me=bpy.data.meshes.new('LC Castle Tower');me.from_pydata(vs,[],faces);me.materials.append(mat);uv=me.uv_layers.new()
for p,c in zip(me.polygons,cols):
 for j in p.loop_indices:uv.data[j].uv=((c%4+.5)/4,1-(c//4+.5)/4)
o=bpy.data.objects.new('LC_CastleTower_Prototype',me);col.objects.link(o);o.hide_set(True);o.hide_render=True;protos[o.name]=o
# Reuse the actual Spell Lab stone arch mesh, normalized as a reusable decoration.
with bpy.data.libraries.load(str(pack/'models/spell-lab-reference-v1/Spell Lab Visual Library.blend'),link=False) as(a,b):b.objects=['SpellLab_Asset_a4d944905aa91b13']
o=b.objects[0];col.objects.link(o);o.name='LC_StoneArch_Prototype';o.data=o.data.copy()
lo=[min(v.co[k] for v in o.data.vertices) for k in range(3)];hi=[max(v.co[k] for v in o.data.vertices) for k in range(3)]
for v in o.data.vertices:
 for k in range(3):v.co[k]=(v.co[k]-(lo[k] if k==2 else (lo[k]+hi[k])/2))/(hi[k]-lo[k])
o.data.materials.clear();o.data.materials.append(mat)
for p in o.data.polygons:
 p.material_index=0
 for j in p.loop_indices:o.data.uv_layers[0].data[j].uv=(.125,.875)
o.hide_set(True);o.hide_render=True;protos[o.name]=o
# Physical pack donor water flow: remove only coincident reverse faces, retain flowing silhouette.
with bpy.data.libraries.load(str(pack/'blender/FLUXARA_Track_Asset_Library.blend'),link=False) as(a,b):b.objects=['FD_LowerCascadeFlow']
o=b.objects[0];col.objects.link(o);o.name='LC_Waterfall_Prototype';o.data=o.data.copy()
import bmesh
bm=bmesh.new();bm.from_mesh(o.data);seen=set();remove=[]
for face in bm.faces:
 key=tuple(sorted(tuple(round(c,5) for c in v.co) for v in face.verts))
 if key in seen:remove.append(face)
 else:seen.add(key)
bmesh.ops.delete(bm,geom=remove,context='FACES');bm.to_mesh(o.data);bm.free()
lo=[min(v.co[k] for v in o.data.vertices) for k in range(3)];hi=[max(v.co[k] for v in o.data.vertices) for k in range(3)]
for v in o.data.vertices:
 for k in range(3):v.co[k]=(v.co[k]-(lo[k] if k==2 else (lo[k]+hi[k])/2))/(hi[k]-lo[k])
o.hide_set(True);o.hide_render=True;protos[o.name]=o
rows=[]
def place(proto,x,y,z,w,d,h,angle=0,role='detail'):
 o=bpy.data.objects.new('LC_'+role+'_'+str(len(rows)).zfill(4),protos[proto].data);col.objects.link(o);o.location=(x,y,z);o.scale=(w,d,h);o.rotation_euler.z=angle;rows.append({'name':o.name,'prototype':proto,'xyz':[x,z,y],'scale':[w,h,d],'rotationZRadians':angle,'role':role});return o
# Group trees and shrubs along every biome's original terrain around the unchanged route.
points=[]
for q in quads[::12]:
 x=sum(p[0] for p in q)/4;y=sum(p[2] for p in q)/4
 for side in [-1,1]:
  for attempt in range(6):
   a=rng.uniform(0,math.tau);d=rng.uniform(14,31);xx=x+math.cos(a)*d;yy=y+math.sin(a)*d;z=ground(xx,yy);w=rng.uniform(6,10)
   if z is None or z>90 or not clear(xx,yy,w*.65+2) or any((xx-a)**2+(yy-b)**2<14**2 for a,b in points):continue
   place('DP_RoundedTree_Prototype',xx,yy,z-.12,w,w*.9,rng.uniform(9,15),rng.uniform(0,math.tau),'tree');points.append((xx,yy))
   for j in range(3):
    xx2=xx+rng.uniform(-6,6);yy2=yy+rng.uniform(-6,6);z2=ground(xx2,yy2)
    if z2 is not None and clear(xx2,yy2,2.3):place('DP_RoundedBush_Prototype',xx2,yy2,z2,2.8,2.4,1.6,rng.uniform(0,math.tau),'bush')
   break
  if len(points)>=75:break
 if len(points)>=75:break
# Small repeated details make roadside patches denser without copying model geometry.
for i in range(700):
 if not points:break
 x,y=rng.choice(points);x+=rng.uniform(-11,11);y+=rng.uniform(-11,11);z=ground(x,y)
 if z is None or not clear(x,y,.8):continue
 proto='DP_Daisy_Prototype' if i%2 else 'DP_GrassTuft_Prototype';place(proto,x,y,z+.025,rng.uniform(.4,.9),rng.uniform(.4,.9),rng.uniform(.4,.9),rng.uniform(0,math.tau),'flower' if i%2 else 'grass')
# Distant landmark clusters stand off-course; arches remain decorative and do not become new roadways.
landmarks=[(-85,-78,25),(-310,225,34),(-492,434,31),(-335,-61,38),(-180,-280,33),(270,-210,28),(500,120,32),(520,440,40),(410,760,36),(128,499,25),(240,615,29)]
for x,y,height in landmarks:
 z=ground(x,y)
 if z is None or not clear(x,y,height*.3+2):continue
 place('LC_CastleTower_Prototype',x,y,z,height*.6,height*.6,height,rng.uniform(0,math.tau),'tower')
 for s in [-1,1]:
  xx=x+s*height*.55;yy=y+height*.1;zz=ground(xx,yy)
  if zz is not None and clear(xx,yy,height*.20+2):place('LC_CastleTower_Prototype',xx,yy,zz,height*.38,height*.38,height*.65,0,'tower')
# Pennants anchored in cleared ground groups, away from the programmed corridor.
for x,y in points[::4]:
 z=ground(x,y)
 if clear(x,y,6):place('DP_Bunting_Prototype',x,y,z,10,2,3,rng.uniform(0,math.tau),'pennants')
# Exposed cliff waterfalls, paired with green-capped shared hills. Clearance checks include their complete footprints.
for x,y,angle in [(-130,-105,0),(-410,310,1.3),(630,490,1.6),(630,795,1.6),(298,-110,-1.0)]:
 z=ground(x,y)
 if z is not None and clear(x,y,10):
  place('DP_RoundedHill_Prototype',x,y,z-.5,28,23,20,angle,'cliff')
  place('LC_Waterfall_Prototype',x,y-9,z,9,1.8,18,angle,'waterfall')
# Keep only prototypes used by the map; existing runtime DP prototypes are not re-exported.
used={p['prototype'] for p in rows}|{'LC_CastleTower_Prototype','LC_StoneArch_Prototype','LC_Waterfall_Prototype'}
bpy.data.libraries.write(str(r/'Lap Catch Reusable Scenery.blend'),{protos[n] for n in used},fake_user=True)
for o in list(protos.values()):
 if o.users_collection:o.hide_render=True
bpy.ops.wm.save_as_mainfile(filepath=str(r/'Lap Catch Scenery Layout.blend'));(r/'placements.json').write_text(json.dumps(rows,indent=2));print('SCENERY_BUILT',len(rows),len(points),len(used))
