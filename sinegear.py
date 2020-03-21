import bmesh
import bpy
import bpy_extras
import math
from bpy.props import FloatProperty, BoolProperty, IntProperty
from mathutils import Vector

from .globals import is_sinegear_data, get_sinegear_data, get_sinegear_enum, make_sinegear_data
from .utils import polar_to_xy


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
        default=360,
        description="Resolution",
        min=3,
        soft_min=3,
        max=3600,
        soft_max=3600,
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


class SineGearData(bpy.types.PropertyGroup):

    def generate_mesh(self, context):
        def step_to_theta(i):
            theta_min = -180
            theta_max = 180
            return math.radians(theta_min + (i * (theta_max - theta_min) / self.resolution))

        polar_path = [(self.radius + (math.sin(theta * self.teeth_count) * self.teeth_length), theta)
                      for theta in map(step_to_theta, range(0, self.resolution))]
        path = [polar_to_xy(r, theta) for r, theta in polar_path]

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

    make_face: MakeFaceProperty(update=generate_mesh)
    radius: RadiusProperty(update=generate_mesh)
    resolution: ResolutionProperty(update=generate_mesh)
    teeth_count: TeethCountProperty(update=generate_mesh)
    teeth_length: TeethLengthProperty(update=generate_mesh)


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

    def execute(self, context):
        mesh = bpy.data.meshes.new("SineGear")
        obj = bpy_extras.object_utils.object_data_add(context, mesh, operator=None)

        sinegear_data: SineGearData = make_sinegear_data(obj)
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

        sinegear_data.generate_mesh(context)
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
               and context.object.type == "MESH" \
               and is_sinegear_data(context.object) \
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
