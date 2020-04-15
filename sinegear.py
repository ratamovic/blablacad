import bmesh
import bpy
import bpy_extras
import math
from bpy.props import BoolProperty, FloatProperty, EnumProperty, IntProperty
from mathutils import Vector

from .globals import has_sinegear_data, get_sinegear_data, get_sinegear_enum, make_sinegear_data
from .utils import polar_to_xy, Lockable, if_unlocked


# noinspection PyPep8Naming
def MakeFaceProperty(update=None):
    return BoolProperty(
        name="MakeFace",
        default=True,
        description="Make face",
        update=update)


# noinspection PyPep8Naming
def RadiusProperty(update=None):
    return FloatProperty(
        name="Radius",
        default=1.0,
        description="Radius",
        min=0.0,
        soft_min=0.0,
        step=1,
        unit="LENGTH",
        update=update)


# noinspection PyPep8Naming
def ResolutionProperty(update=None):
    return IntProperty(
        name="Resolution",
        default=2,
        description="Resolution",
        min=2,
        soft_min=2,
        step=1,
        update=update)


# noinspection PyPep8Naming
def TeethCountProperty(update=None):
    return IntProperty(
        name="TeethCount",
        description="Teeth count",
        default=16,
        min=1,
        soft_min=1,
        step=1,
        update=update)


# noinspection PyPep8Naming
def TeethLengthProperty(update=None):
    return FloatProperty(
        name="TeethLength",
        default=0.1,
        description="Teeth length",
        min=0.0,
        soft_min=0.0,
        step=1,
        unit="LENGTH",
        update=update)


# noinspection PyPep8Naming
def TypeProperty(update=None):
    return EnumProperty(
        items=[
            ("MESH", "Mesh", ""),
            ("POLY", "Poly", "")],
        name="Type",
        description="Type",
        default="POLY",
        update=update)


class SineGearData(bpy.types.PropertyGroup, Lockable):

    def generate(self, context):
        points_count = self.resolution * self.teeth_count

        def step_to_theta(i):
            theta_min = -180
            theta_max = 180
            return math.radians(theta_min + (i * (theta_max - theta_min) / points_count))

        polar_path = [(self.radius + (math.sin(theta * self.teeth_count) * self.teeth_length), theta)
                      for theta in map(step_to_theta, range(0, points_count))]
        path = [polar_to_xy(r, theta) for r, theta in polar_path]
        if self.type == "MESH":
            self.generate_mesh(path)
        elif self.type == "POLY":
            self.generate_curve(path)
        else:
            raise RuntimeError(f"Unknown object type {self.type}")

    def generate_curve(self, path):
        curve: bpy.types.Curve = self.id_data.data
        curve.dimensions = "2D"
        curve.resolution_u = 2
        curve.splines.clear()
        polyline = curve.splines.new('POLY')

        polyline.points.add(len(path) - 1)
        for i, (x, y) in enumerate(path):
            polyline.points[i].co = (x, y, 0.0, 1.0)

        polyline.use_cyclic_u = True
        polyline.use_cyclic_v = True
        bpy.context.object.data.fill_mode = "BOTH" if self.make_face else "NONE"

        # bpy.ops.object.mode_set(mode="EDIT")
        # bpy.ops.curve.select_all(action="SELECT")
        # bpy.ops.curvetools.add_toolpath_offset_curve(offset=-0.1, pitch=-0.09, step_angle=0.0245437, count=1)
        # curve.splines.remove(curve.splines.active)
        # bpy.ops.object.mode_set(mode="OBJECT")

    def generate_mesh(self, path):
        bm = bmesh.new()
        verts = [bm.verts.new(Vector((x, y, 0.0))) for (x, y) in path]
        if not self.make_face:
            [bm.edges.new((verts[i], verts[(i + 1) % len(verts)])) for i in range(0, len(verts))]
        else:
            bm.faces.new(verts)

        if self.id_data.data.is_editmode:
            bpy.ops.object.mode_set(mode='OBJECT')
        bm.to_mesh(self.id_data.data)
        bm.free()
        self.id_data.data.update()

    make_face: MakeFaceProperty(update=if_unlocked(generate))
    radius: RadiusProperty(update=if_unlocked(generate))
    resolution: ResolutionProperty(update=if_unlocked(generate))
    teeth_count: TeethCountProperty(update=if_unlocked(generate))
    teeth_length: TeethLengthProperty(update=if_unlocked(generate))
    type: TypeProperty(update=if_unlocked(generate))


class SineGear(bpy.types.Operator):
    bl_idname = "object.sinegear"
    bl_description = "Sinusoidal gear shape"
    bl_label = "Sine Gear"
    bl_options = {"REGISTER", "UNDO"}

    make_face: MakeFaceProperty()
    radius: RadiusProperty()
    resolution: ResolutionProperty()
    teeth_count: TeethCountProperty()
    teeth_length: TeethLengthProperty()
    type: TypeProperty()

    def execute(self, context):
        if self.type == "MESH":
            obdata = bpy.data.meshes.new("SineGear")
        elif self.type == "POLY":
            obdata = bpy.data.curves.new("Sinegear", type='CURVE')
        else:
            raise RuntimeError(f"Unknown object type {self.type}")

        obj = bpy_extras.object_utils.object_data_add(context,
                                                      obdata=obdata,
                                                      operator=None)

        sinegear_data: SineGearData = make_sinegear_data(obj)
        sinegear_data.lock()
        if self.make_face != sinegear_data.make_face:
            sinegear_data.make_face = self.make_face
        if self.radius != sinegear_data.radius:
            sinegear_data.radius = self.radius
        if self.resolution != sinegear_data.resolution:
            sinegear_data.resolution = self.resolution
        if self.teeth_count != sinegear_data.teeth_count:
            sinegear_data.teeth_count = self.teeth_count
        if self.teeth_length != sinegear_data.teeth_length:
            sinegear_data.teeth_length = self.teeth_length
        if self.type != sinegear_data.type:
            sinegear_data.type = self.type

        sinegear_data.unlock()
        sinegear_data.generate(context)
        return {"FINISHED"}


class SineGearEditPanel(bpy.types.Panel):
    """Creates a Panel in the data context of the properties editor"""
    bl_idname = "DATA_PT_SineGear"
    bl_context = "object"
    bl_label = "Sine Gear data"
    bl_region_type = "WINDOW"
    bl_space_type = "PROPERTIES"

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0 \
               and has_sinegear_data(context.object) \
               and context.object in context.selected_objects

    def draw(self, context):
        sinegear_data = get_sinegear_data(context.object)
        sinegear_enum = get_sinegear_enum(context.object)
        sinegear_props = sinegear_data.bl_rna.properties

        layout = self.layout
        layout.use_property_split = True
        layout.label(text="Type: %s" % sinegear_enum.name, icon="MESH_CUBE")
        layout.prop(sinegear_data, "radius", text=sinegear_props["radius"].description)
        layout.prop(sinegear_data, "resolution", text=sinegear_props["resolution"].description)
        layout.prop(sinegear_data, "teeth_count", text=sinegear_props["teeth_count"].description)
        layout.prop(sinegear_data, "teeth_length", text=sinegear_props["teeth_length"].description)
        layout.prop(sinegear_data, "make_face", text=sinegear_props["make_face"].description)


def register():
    bpy.utils.register_class(SineGearData)
    bpy.utils.register_class(SineGear)
    bpy.utils.register_class(SineGearEditPanel)


def unregister():
    bpy.utils.unregister_class(SineGearEditPanel)
    bpy.utils.unregister_class(SineGear)
    bpy.utils.unregister_class(SineGearData)
