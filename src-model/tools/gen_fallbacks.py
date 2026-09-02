"""
Regenerate the site's static fallback renders (one straight-on shot per
flavour, 600x900, transparent background, contact shadow) from
out/tempo-can.glb, swapping the label texture per flavour.

Colour notes: view_transform must be 'Standard' (AgX washes the flat label
colours) and light energy modest (overexposure clips citrus orange to yellow).

Run: blender -b -P gen_fallbacks.py    -> out/fallbacks/can_*.png
"""
import bpy, os
from mathutils import Vector

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(TOOLS, '..', '..'))
GLB = os.path.join(TOOLS, 'out', 'tempo-can.glb')
OUTDIR = os.path.join(TOOLS, 'out', 'fallbacks')
os.makedirs(OUTDIR, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)

sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.samples = 224
sc.cycles.use_denoising = False
sc.render.film_transparent = True
sc.view_settings.view_transform = 'Standard'
sc.render.resolution_x, sc.render.resolution_y = 600, 900

w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.9, 0.9, 0.93, 1.0)
bg.inputs['Strength'].default_value = 0.45

def light(name, loc, energy, size):
    d = bpy.data.lights.new(name, 'AREA'); d.energy = energy; d.size = size
    o = bpy.data.objects.new(name, d); o.location = loc
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = (-Vector(loc)).to_track_quat('-Z', 'Y')
    sc.collection.objects.link(o)
light('key', (2.5, -4, 4.5), 460, 3.0)
light('fill', (-3.5, -2.5, 2), 170, 4.0)
light('rim', (0.5, 5, 3.5), 320, 3.0)

bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
bpy.context.object.is_shadow_catcher = True

cam = bpy.data.cameras.new('C'); cam.lens = 65
co = bpy.data.objects.new('C', cam); sc.collection.objects.link(co); sc.camera = co
co.location = Vector((0, -5.93, 1.0))
co.rotation_mode = 'QUATERNION'
co.rotation_quaternion = (co.location - Vector((0, 0, 1.0))).to_track_quat('Z', 'Y')

mat = next(m for m in bpy.data.materials if m.name.startswith('Label'))
img_node = next(n for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE')

for k in ('citrus', 'berry', 'lime'):
    img = bpy.data.images.load(os.path.join(ROOT, 'assets', 'label_%s.png' % k))
    img.colorspace_settings.name = 'sRGB'
    img_node.image = img
    sc.render.filepath = os.path.join(OUTDIR, 'can_%s.png' % k)
    bpy.ops.render.render(write_still=True)
    print('rendered', k)
