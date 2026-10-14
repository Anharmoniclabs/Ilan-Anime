import bpy, bmesh, json
from pathlib import Path
root=Path(__file__).parent
base=root.parents[1]/'models/finished-textured'
rows=[]
for source in ('source-10','source-11','source-12'):
 path=base/source/(source+'.blend')
 bpy.ops.wm.open_mainfile(filepath=str(path))
 meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
 row=dict(source=source,blender_version=bpy.app.version_string,path=str(path),mesh_objects=len(meshes),
  vertices=sum(len(o.data.vertices) for o in meshes),faces=sum(len(o.data.polygons) for o in meshes),
  uv_layers={o.name:[uv.name for uv in o.data.uv_layers] for o in meshes},
  packed_images=[dict(name=i.name,size=list(i.size)) for i in bpy.data.images if i.packed_file],
  armatures=sum(o.type=='ARMATURE' for o in bpy.context.scene.objects),nonmanifold_edges=0,loose_vertices=0)
 for o in meshes:
  bm=bmesh.new();bm.from_mesh(o.data)
  row['nonmanifold_edges']+=sum(not e.is_manifold for e in bm.edges)
  row['loose_vertices']+=sum(not v.link_edges for v in bm.verts)
  bm.free()
 rows.append(row)
(root/'blender-audit.json').write_text(json.dumps(rows,indent=2))
print(json.dumps(rows))
