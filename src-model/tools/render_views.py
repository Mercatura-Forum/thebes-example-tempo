"""
Eyeball renders of out/tempo-can.glb: front, three-quarter, back (texture
seam), top/bottom rim details, and the label-repeat junction (junctions sit
at +/-X, so a camera on +X faces one dead-centre). Cycles CPU.

Run: blender -b -P render_views.py     -> out/renders/*.png
"""
import bpy, os
from mathutils import Vector

TOOLS = os.path.dirname(os.path.abspath(__file__))
GLB = os.path.join(TOOLS, 'out', 'tempo-can.glb')
OUTDIR = os.path.join(TOOLS, 'out', 'renders')
os.makedirs(OUTDIR, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=GLB)

sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.samples = 160
sc.cycles.use_denoising = False

# world: soft studio gradient so the metal has something to reflect
w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes['Background']
bg.inputs['Color'].default_value = (0.92, 0.92, 0.94, 1.0)
bg.inputs['Strength'].default_value = 0.7

def light(name, loc, energy, size):
    d = bpy.data.lights.new(name, 'AREA'); d.energy = energy; d.size = size
    o = bpy.data.objects.new(name, d); o.location = loc
    o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = (-Vector(loc)).to_track_quat('-Z', 'Y')
    sc.collection.objects.link(o)
light('key', (3, -4, 4), 900, 3.0)
light('fill', (-4, -2, 2), 350, 4.0)
light('rim', (0, 5, 3), 500, 3.0)

bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
plane = bpy.context.object
pm = bpy.data.materials.new('Ground'); pm.use_nodes = True
pm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.9, 0.9, 0.92, 1)
pm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.9
plane.data.materials.append(pm)

cam = bpy.data.cameras.new('C'); cam.lens = 65
co = bpy.data.objects.new('C', cam); sc.collection.objects.link(co); sc.camera = co

CENTER = Vector((0, 0, 1.0))   # can axis = world Z, height ~2
def shoot(name, offset, look=CENTER, res=(720, 1024)):
    co.location = look + Vector(offset)
    co.rotation_mode = 'QUATERNION'
    co.rotation_quaternion = (co.location - look).to_track_quat('Z', 'Y')
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.filepath = os.path.join(OUTDIR, name + '.png')
    bpy.ops.render.render(write_still=True)
    print('rendered', name)

D = 4.6
shoot('front', (0, -D, 0.15))
shoot('three_quarter', (D * 0.62, -D * 0.72, 0.9))
shoot('back_seam', (0, D, 0.15))
shoot('top_detail', (0, -2.6, 2.3), look=Vector((0, 0, 1.55)), res=(900, 700))
shoot('bottom_detail', (0, -2.4, 0.5), look=Vector((0, 0, 0.22)), res=(900, 700))
shoot('junction', (D, 0, 0.15))
