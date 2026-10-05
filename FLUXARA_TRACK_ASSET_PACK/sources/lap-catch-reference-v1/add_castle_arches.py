import bpy,json
from pathlib import Path
r=Path(__file__).resolve().parent;bpy.ops.wm.open_mainfile(filepath=str(r/'Lap Catch Scenery Layout.blend'));rows=json.loads((r/'placements.json').read_text());proto=bpy.data.objects['LC_StoneArch_Prototype'];col=bpy.data.collections['Lap Catch Shared Scenery']
for x,z in [(-180,-270),(-85,-68)]:
 name='LC_castle_arch_'+str(len(rows)).zfill(4);o=bpy.data.objects.new(name,proto.data);col.objects.link(o);o.location=(x,z,0);o.scale=(25,4,16);rows.append({'name':name,'prototype':proto.name,'xyz':[x,0,z],'scale':[25,16,4],'rotationZRadians':0,'role':'arch'})
(r/'placements.json').write_text(json.dumps(rows,indent=2));bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(r/'Lap Catch Scenery Layout.blend'));print('CASTLE_ARCHES_ADDED',len(rows))
