import bpy
import bpy_extras
import hashlib
from array import array
from bpy.props import BoolProperty, PointerProperty, StringProperty

from .globals import has_meshify_data, get_meshify_data, get_meshify_enum, make_meshify_data
from .utils import Lockable, hash_mesh, if_unlocked


def is_meshify_source(obj):
    return "meshify_source" in obj and obj["meshify_source"]


def set_meshify_source(obj):
    obj["meshify_source"] = True


# noinspection PyPep8Naming
def DigestProperty():
    return StringProperty(
        name="Mesh digest",
        default="",
        description="Mesh digest to detect changes")


# noinspection PyPep8Naming
def KeepInSyncProperty(update=None):
    return BoolProperty(
        name="Keep in sync",
        default=True,
        description="Keep in sync with source object",
        update=update)


# noinspection PyPep8Naming
def MakeFanFaceEnabledProperty(update=None):
    return BoolProperty(
        name="Enable Make Fan Face",
        default=False,
        description="Make a fan face from the curve",
        update=update)


# noinspection PyPep8Naming
def RemoveDoubleProperty(update=None):
    return BoolProperty(
        name="RemoveDouble",
        default=False,
        description="Remove doubles by merging vertices by distance",
        update=update)


# noinspection PyPep8Naming
def SourceObjectProperty(update=None):
    return PointerProperty(
        name="Source object",
        description="Source object to stay in sync with (non-modifiable)",
        type=bpy.types.Object,
        update=update)


# noinspection PyPep8Naming
def SyncLocationProperty(update=None):
    return BoolProperty(
        name="Location",
        default=False,
        description="Sync object location",
        update=update)


# noinspection PyPep8Naming
def SyncMeshProperty(update=None):
    return BoolProperty(
        name="Mesh data",
        default=True,
        description="Sync mesh data",
        update=update)


# noinspection PyPep8Naming
def SyncRotationProperty(update=None):
    return BoolProperty(
        name="Rotation",
        default=True,
        description="Sync object rotation",
        update=update)


# noinspection PyPep8Naming
def SyncScaleProperty(update=None):
    return BoolProperty(
        name="Scale",
        default=True,
        description="Sync object scale",
        update=update)


class MeshifyData(bpy.types.PropertyGroup, Lockable):

    def meshify(self, context):
        obj: bpy.types.Object = self.id_data
        if self.source_object is not None and self.keep_in_sync:
            if self.sync_location:
                if obj.location != self.source_object.location:
                    obj.location = self.source_object.location

            if self.sync_mesh:
                depsgraph = context.evaluated_depsgraph_get()
                evaluated_object = self.source_object.evaluated_get(depsgraph)
                evaluated_mesh = bpy.data.meshes.new_from_object(evaluated_object)

                source_hash = hashlib.sha1()
                hash_mesh(source_hash, evaluated_mesh)
                source_hash.update(array("l", [self.make_fan_face_enabled, self.sync_location, self.sync_mesh, self.sync_rotation,
                                              self.sync_scale]))
                source_digest = source_hash.hexdigest()
                if self.digest != source_digest:
                    self.digest = source_digest

                    obj.data = evaluated_mesh
                    if self.make_fan_face_enabled:
                        previous_selection = bpy.context.view_layer.objects.active
                        bpy.context.view_layer.objects.active = obj
                        bpy.ops.object.mode_set(mode="EDIT")
                        bpy.ops.mesh.select_all(action="SELECT")
                        bpy.ops.mesh.edge_face_add()
                        bpy.ops.mesh.poke()
                        bpy.ops.mesh.dissolve_limited()
                        bpy.ops.object.mode_set(mode="OBJECT")
                        bpy.context.view_layer.objects.active = previous_selection

                    if self.remove_doubles:
                        previous_selection = bpy.context.view_layer.objects.active
                        bpy.context.view_layer.objects.active = self.id_data
                        bpy.ops.object.mode_set(mode="EDIT")
                        bpy.ops.mesh.select_all(action="SELECT")
                        bpy.ops.mesh.remove_doubles(threshold=0.002)
                        bpy.ops.object.mode_set(mode="OBJECT")
                        bpy.context.view_layer.objects.active = previous_selection

            if self.sync_rotation:
                if obj.rotation_euler != self.source_object.rotation_euler:
                    obj.rotation_euler = self.source_object.rotation_euler

            if self.sync_scale:
                if obj.scale != self.source_object.scale:
                    obj.scale = self.source_object.scale

    digest: DigestProperty()
    keep_in_sync: KeepInSyncProperty(update=if_unlocked(meshify))
    make_fan_face_enabled: MakeFanFaceEnabledProperty(update=if_unlocked(meshify))
    remove_doubles: RemoveDoubleProperty(update=if_unlocked(meshify))
    source_object: SourceObjectProperty(update=if_unlocked(meshify))
    sync_location: SyncLocationProperty(update=if_unlocked(meshify))
    sync_mesh: SyncMeshProperty(update=if_unlocked(meshify))
    sync_rotation: SyncRotationProperty(update=if_unlocked(meshify))
    sync_scale: SyncScaleProperty(update=if_unlocked(meshify))


class Meshify(bpy.types.Operator):
    bl_idname = "object.meshify"
    bl_description = "Turn an object into a mesh and keep it in sync"
    bl_label = "Meshify"
    bl_options = {"REGISTER", "UNDO"}

    keep_in_sync: KeepInSyncProperty()
    sync_location: SyncLocationProperty()
    sync_mesh: SyncMeshProperty()
    sync_rotation: SyncRotationProperty()
    sync_scale: SyncScaleProperty()

    @staticmethod
    def is_meshifiable(obj: bpy.types.Object) -> bool:
        return obj.type in {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META'}

    def execute(self, context):
        if len(context.selected_objects) != 1 or context.object is None:
            self.report({"WARNING"}, "One object to meshify must be selected")
            return {"CANCELLED"}

        if not Meshify.is_meshifiable(context.object):
            self.report({"WARNING"}, "Object can not be meshified")
            return {"CANCELLED"}

        selected_obj = context.object
        set_meshify_source(selected_obj)

        mesh = bpy.data.meshes.new("Meshify")
        obj = bpy_extras.object_utils.object_data_add(context,
                                                      obdata=mesh,
                                                      operator=None,
                                                      name=selected_obj.name + " meshify")
        meshify_data: MeshifyData = make_meshify_data(obj)
        meshify_data.lock()
        meshify_data.source_object = selected_obj

        if self.keep_in_sync != meshify_data.keep_in_sync:
            meshify_data.keep_in_sync = self.keep_in_sync
        if self.sync_location != meshify_data.sync_location:
            meshify_data.sync_location = self.sync_location
        if self.sync_mesh != meshify_data.sync_mesh:
            meshify_data.sync_mesh = self.sync_mesh
        if self.sync_rotation != meshify_data.sync_rotation:
            meshify_data.sync_rotation = self.sync_rotation
        if self.sync_scale != meshify_data.sync_scale:
            meshify_data.sync_scale = self.sync_scale

        meshify_data.unlock()
        meshify_data.meshify(context)
        return {"FINISHED"}


class MeshifyToggleSource(bpy.types.Operator):
    bl_idname = "object.meshify_toggle_source"
    bl_description = "Toggle source object visibility"
    bl_label = "Toggle source"

    source_visibility: BoolProperty(
        name="Source visibility",
        default=True,
        description="Toggle source object visibility")

    def execute(self, context):
        obj = context.object
        if not has_meshify_data(obj):
            self.report({"WARNING"}, "Source visibility must be toggled from a meshify object")
            return {"CANCELLED"}

        source_object = get_meshify_data(obj).source_object
        source_object.hide_set(not source_object.hide_get())
        return {"FINISHED"}


class MeshifyEditPanel(bpy.types.Panel):
    """Creates a Panel in the data context of the properties editor"""
    bl_idname = "DATA_PT_Meshify"
    bl_context = "object"
    bl_label = "Meshify data"
    bl_region_type = "WINDOW"
    bl_space_type = "PROPERTIES"

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0 \
               and has_meshify_data(context.object) \
               and context.object in context.selected_objects

    def draw(self, context):
        obj = context.object
        meshify_data = get_meshify_data(obj)
        meshify_enum = get_meshify_enum(obj)
        meshify_props = meshify_data.bl_rna.properties

        layout = self.layout
        layout.use_property_split = True
        layout.label(text="Type: %s" % meshify_enum.name, icon="MESH_CUBE")

        object_col = layout.column(align=True)
        object_col.enabled = False
        object_col.prop(meshify_data, "source_object", text=meshify_props["source_object"].name)

        layout.prop(meshify_data, "keep_in_sync", text=meshify_props["keep_in_sync"].name)
        sync_col = layout.column(align=True)
        sync_col.enabled = meshify_data.keep_in_sync
        sync_col.prop(meshify_data, "sync_location", text=meshify_props["sync_location"].name)
        sync_col.prop(meshify_data, "sync_mesh", text=meshify_props["sync_mesh"].name)
        sync_col.prop(meshify_data, "sync_rotation", text=meshify_props["sync_rotation"].name)
        sync_col.prop(meshify_data, "sync_scale", text=meshify_props["sync_scale"].name)
        sync_col.separator()
        sync_col.prop(meshify_data, "remove_doubles", text=meshify_props["remove_doubles"].name)

        if meshify_data.source_object is not None:
            if meshify_data.source_object.type == "CURVE":
                layout.prop(meshify_data, "make_fan_face_enabled", text=meshify_props["make_fan_face_enabled"].name)

            is_source_visible = meshify_data.source_object.hide_get()
            source_visibility_operator = layout.operator(MeshifyToggleSource.bl_idname,
                                                         text="Show source" if is_source_visible else "Hide source",
                                                         icon="CONSOLE")
            source_visibility_operator.source_visibility = is_source_visible


@bpy.app.handlers.persistent
def detect_changes(_):
    processed_list = detect_changes.processed_list
    context = bpy.context
    depsgraph = context.evaluated_depsgraph_get()
    is_depsgraph_update_root = len(processed_list) == 0

    def find_all_meshify_obj_from_source(source_obj):
        return [other_obj for other_obj in bpy.data.objects
                if has_meshify_data(other_obj) and get_meshify_data(other_obj).source_object == source_obj]

    def update_meshify_obj(meshify_obj, processed_list):
        if meshify_obj not in processed_list:
            processed_list.append(meshify_obj)
            meshify_data = get_meshify_data(meshify_obj)
            meshify_data.meshify(context)

    for changed_obj in [obj for obj in map(lambda _: _.id.original, depsgraph.updates)]:
        if is_meshify_source(changed_obj):
            for meshify_obj in find_all_meshify_obj_from_source(changed_obj):
                update_meshify_obj(meshify_obj, processed_list)

        if has_meshify_data(changed_obj):
            update_meshify_obj(changed_obj, processed_list)

    if is_depsgraph_update_root:
        detect_changes.processed_list = list()


def register():
    detect_changes.processed_list = list()

    bpy.utils.register_class(MeshifyData)
    bpy.utils.register_class(Meshify)
    bpy.utils.register_class(MeshifyToggleSource)
    bpy.utils.register_class(MeshifyEditPanel)
    bpy.app.handlers.depsgraph_update_post.append(detect_changes)


def unregister():
    bpy.app.handlers.depsgraph_update_post.remove(detect_changes)
    bpy.utils.unregister_class(MeshifyEditPanel)
    bpy.utils.unregister_class(Meshify)
    bpy.utils.unregister_class(MeshifyToggleSource)
    bpy.utils.unregister_class(MeshifyData)
