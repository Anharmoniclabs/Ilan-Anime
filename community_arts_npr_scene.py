# Run in Blender 4.1+:
# blender --background --python community_arts_npr_scene.py
# Creates community_arts_npr.blend and can be rendered headlessly.
import bpy, math, random
from mathutils import Vector

random.seed(16)
W, H, FPS = 1920, 1080, 24

def clear():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

def material(name, color, metallic=0.0, roughness=0.5, emission=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = color
    p.inputs['Metallic'].default_value = metallic
    p.inputs['Roughness'].default_value = roughness
    if emission:
        p.inputs['Emission Color'].default_value = emission
        p.inputs['Emission Strength'].default_value = 2.5
    return m

def cube(name, loc, scale, m, bevel=0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(m)
    if bevel:
        mod = o.modifiers.new('Soft_edges', 'BEVEL')
        mod.width, mod.segments = bevel, 2
    return o

def cylinder(name, loc, radius, depth, m, rotation=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=radius, depth=depth, location=loc, rotation=rotation)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(m)
    return o

def plane(name, loc, scale, m, rotation=(0,0,0)):
    bpy.ops.mesh.primitive_plane_add(size=2, location=loc, rotation=rotation)
    o = bpy.context.object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(m)
    return o

def area(name, loc, energy, size, color):
    bpy.ops.object.light_add(type='AREA', location=loc)
    o = bpy.context.object
    o.name = name
    o.data.energy, o.data.shape, o.data.size, o.data.color = energy, 'DISK', size, color
    o.rotation_euler = (0, 0, 0)
    return o

def aim(o, target):
    o.rotation_euler = (Vector(target) - o.location).to_track_quat('-Z', 'Y').to_euler()

clear()
brick = material('brick', (.23,.055,.025,1), roughness=.84)
trim = material('aged stone', (.22,.18,.13,1), metallic=.1, roughness=.6)
metal = material('charcoal metal', (.012,.016,.02,1), metallic=.55, roughness=.32)
wood = material('wood', (.09,.025,.008,1), roughness=.52)
wet = material('wet asphalt', (.008,.012,.018,1), metallic=.42, roughness=.17)
ink = material('ink', (.002,.003,.004,1), roughness=.7)
leaf = material('leaf', (.025,.09,.035,1), roughness=.62)
interior = material('warm interior', (.48,.16,.035,1), roughness=.58, emission=(1,.2,.025,1))
orange = material('orange reflection', (1,.21,.025,1), roughness=.35, emission=(1,.12,.01,1))
glass = material('glass', (.015,.028,.04,1), metallic=.25, roughness=.08)
glass.node_tree.nodes['Principled BSDF'].inputs['Transmission Weight'].default_value = .25

# Street, sidewalk and building.
plane('wet street', (0,-4,0), (22,15), wet)
cube('sidewalk', (0,-.1,.14), (13,2.2,.14), trim, .03)
cube('brick facade', (0,1.65,6.6), (10.7,.38,6.6), brick)
for z in [i*.42+.42 for i in range(27)]:
    offset = .20 if int(z/.42)%2 else 0
    for x in [i*.78-10+offset for i in range(27)]:
        if random.random() > .05:
            cube('brick course', (x,1.235,z), (.365,.035,.185), brick)

# Storefront with warm studio interior.
cube('header', (0,1.12,6.3), (8.15,.18,.72), metal, .03)
cube('lower fascia', (0,1.10,1.0), (8.15,.18,.95), metal, .03)
for x in (-8.05,-2.0,2.0,8.05): cube('vertical frame', (x,1.06,3.35), (.16,.2,2.9), metal, .02)
for x,w in [(-5,2.75),(-1.1,1.05),(1.1,1.05),(5,2.75)]:
    cube('warm interior', (x,1.32,3.5), (w,.035,2.1), interior)
    cube('window glass', (x,1.045,3.5), (w,.028,2.1), glass)
for x in (-.98,.98): cube('door mullion', (x,1.0,3.5), (.055,.12,2.18), metal)
for x in (-.26,.26): cube('door handle', (x,.88,3.15), (.04,.07,.38), trim, .03)
cube('community arts sign', (0,.85,6.55), (6.7,.08,.49), metal, .04)
bpy.ops.object.text_add(location=(-5.9,.73,6.31), rotation=(math.radians(90),0,0))
t = bpy.context.object
t.name = 'COMMUNITY ARTS sign'
t.data.body, t.data.align_x, t.data.size, t.data.extrude = 'COMMUNITY ARTS', 'LEFT', .78, .018
t.data.materials.append(trim)
for z in (5.72,7.32): cube('sign trim', (0,.78,z), (7.4,.12,.06), trim)
for x in (-5.3,-3.8,3.7,5.2):
    cube('work table', (x,.95,2.1), (.62,.38,.08), wood)
    for dx in (-.47,.47): cube('table leg', (x+dx,.95,1.35), (.04,.04,.65), metal)
    cylinder('stool', (x,.45,1.15), .18, .58, wood)
for x in (-4.3,4.7):
    cube('easel leg', (x,1.0,2.85), (.05,.05,.7), wood)
    cube('easel canvas', (x,1.0,3.3), (.45,.05,.58), trim)
for x in (-5.7,-3.5,-1.0,1.0,3.5,5.7):
    cylinder('lamp cord', (x,.78,5.36), .016, .72, metal)
    cylinder('pendant shade', (x,.78,4.77), .26, .14, metal)
    area('warm pendant', (x,.65,4.62), 120, .4, (1,.32,.09))
for x in (-6.5,6.4):
    cube('plant pot', (x,.86,1.25), (.25,.18,.26), wood)
    for _ in range(10):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=4, location=(x+random.uniform(-.22,.22),.78,1.6+random.uniform(0,.55)), scale=(.16,.06,.27))
        bpy.context.object.data.materials.append(leaf)

# Elevated rail, street lamps, distant buildings/cars.
for x in (-10.4,-8.0):
    cube('elevated steel pillar', (x,-.3,5.6), (.35,.35,5.6), metal, .08)
    for z in (2.5,7.4): cube('pillar brace', (x,-.3,z), (.7,.45,.1), metal)
for z in (8.4,9.15): cube('elevated beam', (-7.2,.2,z), (5.0,.35,.2), metal, .04)
for x in (-9.8,-8.5,-7.2,-5.9,-4.6): cube('track cross brace', (x,.2,8.8), (.08,.95,.07), metal)
cube('distant building', (-10.2,5.6,3.7), (3.7,.3,3.7), brick)
for x in (-12.2,-10.4,-8.5):
    for z in (2.5,4.4,6.2): cube('distant window', (x,5.24,z), (.44,.02,.56), interior)
for x in (-9.1,-6.8):
    cylinder('lamp post', (x,-1.5,2.7), .08, 4.7, metal)
    cube('lamp arm', (x+.45,-1.5,4.7), (.5,.08,.06), metal)
    cylinder('lamp head', (x+.9,-1.5,4.52), .18, .22, metal)
    area('street lamp', (x+.9,-1.8,4.36), 350, .7, (1,.16,.02))
for x in (-8.1,-6.4):
    cube('car body', (x,-2.4,.58), (1.0,.48,.35), metal, .18)
    cube('car roof', (x,-2.25,.98), (.55,.36,.22), metal, .16)
    for dx in (-.63,.63): cylinder('wheel', (x+dx,-2.72,.35), .22, .14, ink, (math.pi/2,0,0))
cylinder('fire hydrant', (-8.5,-.6,.58), .18, .8, orange)
cylinder('hydrant cap', (-8.5,-.6,1.04), .25, .13, orange)

# Stylized rain and warm puddle reflections.
for _ in range(180):
    x,y,z = random.uniform(-12,11),random.uniform(-3.5,3),random.uniform(.3,11)
    bpy.ops.mesh.primitive_cylinder_add(vertices=4, radius=.006, depth=random.uniform(.12,.34), location=(x,y,z), rotation=(math.radians(-25),0,0))
    bpy.context.object.data.materials.append(trim)
for _ in range(25):
    plane('warm puddle reflection', (random.uniform(-9,7),random.uniform(-3.7,-.7),.012), (random.uniform(.05,.32),random.uniform(.22,.65)), orange, (0,0,random.uniform(-.25,.25)))

# Camera, lighting, Eevee NPR-oriented render setup.
bpy.ops.object.camera_add(location=(0,-22,6.0))
cam = bpy.context.object
cam.data.lens = 44
aim(cam, (0,1.1,4.1))
bpy.context.scene.camera = cam
world = bpy.context.scene.world or bpy.data.worlds.new('World')
bpy.context.scene.world = world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (.002,.006,.018,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = .18
area('cool moon fill', (-7,-8,10), 700, 8, (.025,.06,.2))
s = bpy.context.scene
s.render.engine = 'BLENDER_EEVEE_NEXT'
s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage, s.render.fps = W, H, 60, FPS
s.render.image_settings.file_format = 'PNG'
s.render.filepath = '//community_arts_npr_render.png'
s.view_settings.view_transform = 'Standard'
s.view_settings.look = 'None'
bpy.ops.wm.save_as_mainfile(filepath=bpy.path.abspath('//community_arts_npr.blend'))
print('Created', bpy.path.abspath('//community_arts_npr.blend'))
