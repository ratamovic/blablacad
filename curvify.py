import math

import bpy
import bpy_extras
import hashlib
from array import array
from bpy.props import BoolProperty, FloatProperty, PointerProperty, StringProperty
from curve_tools import internal as curve_tools
from mathutils import Vector

from .globals import get_curvify_data, get_curvify_enum, has_curvify_data, make_curvify_data
from .utils import Lockable, hash_curve, if_unlocked, copy_curve


def is_curvify_source(obj):
    return "curvify_source" in obj and obj["curvify_source"]


def set_curvify_source(obj):
    obj["curvify_source"] = True


# noinspection PyPep8Naming
def DigestProperty():
    return StringProperty(
        name="Curve digest",
        default="",
        description="Curve digest to detect changes")


# noinspection PyPep8Naming
def KeepInSyncProperty(update=None):
    return BoolProperty(
        name="Keep in sync",
        default=True,
        description="Keep in sync with source object",
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
def SyncCurveProperty(update=None):
    return BoolProperty(
        name="Curve data",
        default=True,
        description="Sync curve data",
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


# noinspection PyPep8Naming
def OffsetProperty(update=None):
    return FloatProperty(
        name="Offset",
        default=1.0,
        description="Distance between the original and the first trace",
        unit="LENGTH",
        update=update)


# noinspection PyPep8Naming
def OffsetEnabledProperty(update=None):
    return BoolProperty(
        name="Enable Offset",
        default=False,
        description="Offset the curve",
        update=update)


# noinspection PyPep8Naming
def ResolutionProperty(update=None):
    return FloatProperty(
        name="Resolution",
        default=math.pi / 16,
        description="Smaller values make curves smoother by adding more vertices",
        min=math.pi / 128,
        unit="ROTATION",
        update=update)


# noinspection PyPep8Naming
def RoundLineJoinProperty(update=None):
    return BoolProperty(
        name="Round Line Join",
        default=True,
        description="Insert circle arcs at convex corners",
        update=update)


class CurvifyData(bpy.types.PropertyGroup, Lockable):

    def curvify(self, context):
        if self.source_object is not None and self.keep_in_sync:
            obj: bpy.types.Object = self.id_data
            spline: bpy.types.Spline

            if self.sync_location:
                if obj.location != self.source_object.location:
                    obj.location = self.source_object.location
            if self.sync_curve:
                depsgraph = context.evaluated_depsgraph_get()
                source_evaluated_object = self.source_object.evaluated_get(depsgraph)
                source_curve: bpy.types.Curve = source_evaluated_object.data

                source_hash = hashlib.sha1()
                hash_curve(source_hash, source_curve)
                source_hash.update(array("d", [self.offset, self.resolution]))
                source_digest = source_hash.hexdigest()

                if self.digest != source_digest:
                    self.digest = source_digest
                    if obj.type == "MESH":
                        bpy.ops.object.mode_set(mode="EDIT")
                        try:
                            bpy.ops.mesh.select_all(action='SELECT')
                            bpy.ops.mesh.delete(type='VERT')
                        except:
                            pass
                        bpy.ops.mesh.primitive_plane_add(enter_editmode=False, location=(0, 0, 0))
                        bpy.ops.object.mode_set(mode="OBJECT")
                        bpy.ops.object.convert(target="CURVE", keep_original=False)
                        bpy.ops.object.mode_set(mode="EDIT")
                        try:
                            bpy.ops.curve.select_all(action='SELECT')
                            bpy.ops.curve.delete(type='VERT')
                        except:
                            pass
                        bpy.ops.object.mode_set(mode="OBJECT")

                    curve: bpy.types.Curve = obj.data
                    copy_curve(curve, source_curve)

                    for spline in curve.splines:
                        if self.offset_enabled:
                            origin = Vector((0.0, 0.0, 0.0))
                            traces = curve_tools.offsetPolygonOfSpline(spline,
                                                                       self.offset,
                                                                       self.resolution,
                                                                       self.round_line_join)
                            for trace in traces:
                                curve_tools.addPolygonSpline(obj,
                                                             spline.use_cyclic_u,
                                                             [vertex - origin for vertex in trace])

                            curve.splines.remove(spline)

            if self.sync_rotation:
                if obj.rotation_euler != self.source_object.rotation_euler:
                    obj.rotation_euler = self.source_object.rotation_euler
            if self.sync_scale:
                if obj.scale != self.source_object.scale:
                    obj.scale = self.source_object.scale

    digest: DigestProperty()
    keep_in_sync: KeepInSyncProperty(update=if_unlocked(curvify))
    source_object: SourceObjectProperty(update=if_unlocked(curvify))
    sync_location: SyncLocationProperty(update=if_unlocked(curvify))
    sync_curve: SyncCurveProperty(update=if_unlocked(curvify))
    sync_rotation: SyncRotationProperty(update=if_unlocked(curvify))
    sync_scale: SyncScaleProperty(update=if_unlocked(curvify))

    offset: OffsetProperty(update=if_unlocked(curvify))
    offset_enabled: OffsetEnabledProperty(update=if_unlocked(curvify))
    resolution: ResolutionProperty(update=if_unlocked(curvify))
    round_line_join: RoundLineJoinProperty(update=if_unlocked(curvify))


class Curvify(bpy.types.Operator):
    bl_idname = "object.curvify"
    bl_description = "Transform a curve into another and keep it in sync"
    bl_label = "Curvify"
    bl_options = {"REGISTER", "UNDO"}

    keep_in_sync: KeepInSyncProperty()
    sync_location: SyncLocationProperty()
    sync_curve: SyncCurveProperty()
    sync_rotation: SyncRotationProperty()
    sync_scale: SyncScaleProperty()

    @staticmethod
    def is_curvifiable(obj: bpy.types.Object) -> bool:
        return obj.type in {"CURVE"}

    def execute(self, context):
        if len(context.selected_objects) != 1 or context.object is None:
            self.report({"WARNING"}, "One object to curvify must be selected")
            return {"CANCELLED"}

        if not Curvify.is_curvifiable(context.object):
            self.report({"WARNING"}, "Object can not be curvified")
            return {"CANCELLED"}

        selected_obj = context.object
        set_curvify_source(selected_obj)

        curve = bpy.data.curves.new("Curvify", type="CURVE")
        obj = bpy_extras.object_utils.object_data_add(context,
                                                      obdata=curve,
                                                      operator=None,
                                                      name=selected_obj.name + " curvify")
        curvify_data: CurvifyData = make_curvify_data(obj)
        curvify_data.lock()
        curvify_data.source_object = selected_obj

        if self.keep_in_sync != curvify_data.keep_in_sync:
            curvify_data.keep_in_sync = self.keep_in_sync
        if self.sync_location != curvify_data.sync_location:
            curvify_data.sync_location = self.sync_location
        if self.sync_curve != curvify_data.sync_curve:
            curvify_data.sync_curve = self.sync_curve
        if self.sync_rotation != curvify_data.sync_rotation:
            curvify_data.sync_rotation = self.sync_rotation
        if self.sync_scale != curvify_data.sync_scale:
            curvify_data.sync_scale = self.sync_scale

        curvify_data.unlock()
        curvify_data.curvify(context)
        return {"FINISHED"}


class CurvifyToggleSource(bpy.types.Operator):
    bl_idname = "object.curvify_toggle_source"
    bl_description = "Toggle source object visibility"
    bl_label = "Toggle source"

    source_visibility: BoolProperty(
        name="Source visibility",
        default=True,
        description="Toggle source object visibility")

    def execute(self, context):
        obj = context.object
        if not has_curvify_data(obj):
            self.report({"WARNING"}, "Source visibility must be toggled from a curvify object")
            return {"CANCELLED"}

        source_object = get_curvify_data(obj).source_object
        source_object.hide_set(not source_object.hide_get())
        return {"FINISHED"}


class CurvifyEditPanel(bpy.types.Panel):
    """Creates a Panel in the data context of the properties editor"""
    bl_idname = "DATA_PT_Curvify"
    bl_context = "object"
    bl_label = "Curvify data"
    bl_region_type = "WINDOW"
    bl_space_type = "PROPERTIES"

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0 \
               and has_curvify_data(context.object) \
               and context.object in context.selected_objects

    def draw(self, context):
        obj = context.object
        curvify_data = get_curvify_data(obj)
        curvify_enum = get_curvify_enum(obj)
        curvify_props = curvify_data.bl_rna.properties

        layout = self.layout
        layout.use_property_split = True
        layout.label(text="Type: %s" % curvify_enum.name, icon="MESH_CUBE")

        object_col = layout.column(align=True)
        object_col.enabled = False
        object_col.prop(curvify_data, "source_object", text=curvify_props["source_object"].name)

        layout.prop(curvify_data, "keep_in_sync", text=curvify_props["keep_in_sync"].name)
        sync_col = layout.column(align=True)
        sync_col.enabled = curvify_data.keep_in_sync
        sync_col.prop(curvify_data, "sync_location", text=curvify_props["sync_location"].name)
        sync_col.prop(curvify_data, "sync_curve", text=curvify_props["sync_curve"].name)
        sync_col.prop(curvify_data, "sync_rotation", text=curvify_props["sync_rotation"].name)
        sync_col.prop(curvify_data, "sync_scale", text=curvify_props["sync_scale"].name)

        self.layout.separator()
        layout.prop(curvify_data, "offset_enabled", text=curvify_props["offset_enabled"].name)
        offset_col = layout.column(align=True)
        offset_col.prop(curvify_data, "offset", text=curvify_props["offset"].name)
        offset_col.prop(curvify_data, "resolution", text=curvify_props["resolution"].name)
        offset_col.prop(curvify_data, "round_line_join", text=curvify_props["round_line_join"].name)

        if curvify_data.source_object is not None:
            is_source_visible = curvify_data.source_object.hide_get()
            source_visibility_operator = layout.operator(CurvifyToggleSource.bl_idname,
                                                         text="Show source" if is_source_visible else "Hide source",
                                                         icon="CONSOLE")
            source_visibility_operator.source_visibility = is_source_visible


@bpy.app.handlers.persistent
def detect_changes(_):
    processed_list = detect_changes.processed_list
    context = bpy.context
    depsgraph = context.evaluated_depsgraph_get()
    is_depsgraph_update_root = len(processed_list) == 0

    def find_all_curvify_obj_from_source(source_obj):
        return [other_obj for other_obj in bpy.data.objects
                if has_curvify_data(other_obj) and get_curvify_data(other_obj).source_object == source_obj]

    def update_curvify_obj(curvify_obj, processed_list):
        if curvify_obj not in processed_list:
            processed_list.append(curvify_obj)
            curvify_data = get_curvify_data(curvify_obj)
            curvify_data.curvify(context)

    for changed_obj in [obj for obj in map(lambda _: _.id.original, depsgraph.updates)]:
        if is_curvify_source(changed_obj):
            for curvify_obj in find_all_curvify_obj_from_source(changed_obj):
                update_curvify_obj(curvify_obj, processed_list)

        if has_curvify_data(changed_obj):
            update_curvify_obj(changed_obj, processed_list)

    if is_depsgraph_update_root:
        detect_changes.processed_list = list()


def register():
    detect_changes.processed_list = list()

    bpy.utils.register_class(CurvifyData)
    bpy.utils.register_class(Curvify)
    bpy.utils.register_class(CurvifyToggleSource)
    bpy.utils.register_class(CurvifyEditPanel)
    bpy.app.handlers.depsgraph_update_post.append(detect_changes)


def unregister():
    bpy.app.handlers.depsgraph_update_post.remove(detect_changes)
    bpy.utils.unregister_class(CurvifyEditPanel)
    bpy.utils.unregister_class(Curvify)
    bpy.utils.unregister_class(CurvifyToggleSource)
    bpy.utils.unregister_class(CurvifyData)
