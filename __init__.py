# https://github.com/WiresoulStudio/W_Mesh_28x/blob/327bf7a5d26f134288627b253732a8470e05f7b9/__init__.py
import bpy
from bpy.props import PointerProperty, EnumProperty

from . import sinegear
from .meshify import Meshify, MeshifyData
from .sinegear import SineGear, SineGearData

bl_info = {
    "name": "BlaBlaCAD",
    "blender": (2, 82, 0),
    "category": "Object",
}


# noinspection PyPep8Naming
def TypeProperty():
    return EnumProperty(
        items=[
            ("NONE", "None", ""),
            ("MESHIFY", "Meshify", ""),
            ("SINEGEAR", "Sine Gear", "")],
        name="Type",
        description="Type",
        default="NONE")


class BlaBlaCADData(bpy.types.PropertyGroup):
    meshify_data: PointerProperty(type=MeshifyData)
    sinegear_data: PointerProperty(type=SineGearData)
    type: TypeProperty()


class BlaBlaCADMenu(bpy.types.Menu):
    bl_label = "BlaBlaCAD"
    bl_idname = "OBJECT_MT_blablacad"

    def draw(self, context):
        self.layout.label(text="BlaBlaCAD", icon='WORLD_DATA')
        self.layout.operator(Meshify.bl_idname)
        self.layout.operator(SineGear.bl_idname)


def blablacad_menu(self, context):
    self.layout.menu(BlaBlaCADMenu.bl_idname)


def register():
    meshify.register()
    sinegear.register()

    bpy.utils.register_class(BlaBlaCADData)
    bpy.types.Object.blablacad_data = PointerProperty(type=BlaBlaCADData)
    bpy.utils.register_class(BlaBlaCADMenu)
    bpy.types.VIEW3D_MT_mesh_add.append(blablacad_menu)


def unregister():
    bpy.types.VIEW3D_MT_mesh_add.remove(blablacad_menu)
    bpy.utils.unregister_class(BlaBlaCADMenu)
    del bpy.types.Object.blablacad_data
    bpy.utils.unregister_class(BlaBlaCADData)

    sinegear.unregister()
    meshify.unregister()


if __name__ == "__main__":
    register()
