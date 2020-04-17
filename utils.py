import bpy
import hashlib
import math
from array import array


def r(x, y, center=None):
    center_x, center_y = center or (0, 0)
    math.sqrt(math.pow(center_x - x, 2) + math.pow(center_y - y, 2))


def theta(x, y, center=None):
    center_x, center_y = center or (0, 0)
    math.atan2(center_y - y, center_x - x)


def polar_to_xy(r, theta):
    return r * math.cos(theta), r * math.sin(theta)


class Lockable:
    def lock(self):
        self["lock"] = True

    def unlock(self):
        del self["lock"]


def if_unlocked(func):
    def _if_unlocked(self, context):
        if not self.get("lock", False):
            func(self, context)

    return _if_unlocked


def hash_curve(other_hash, other_curve: bpy.types.Curve):
    other_spline: bpy.types.Spline
    other_point: bpy.types.SplinePoint
    other_bezier_point: bpy.types.BezierSplinePoint

    other_hash.update(array("l", [other_curve.resolution_u, other_curve.resolution_v]))
    other_hash.update(bytes(other_curve.dimensions, "ascii"))
    for other_spline in other_curve.splines:
        other_hash.update(bytes(other_spline.type, "ascii"))
        other_hash.update(bytes(other_spline.radius_interpolation, "ascii"))
        other_hash.update(bytes(other_spline.tilt_interpolation, "ascii"))
        other_hash.update(array("l", [
            other_spline.order_u, other_spline.order_v, other_spline.resolution_u,
            other_spline.resolution_v, other_spline.use_bezier_u,
            other_spline.use_bezier_v, other_spline.use_cyclic_u, other_spline.use_cyclic_v,
            other_spline.use_endpoint_u, other_spline.use_endpoint_v, other_spline.use_smooth]))
        for other_bezier_point in other_spline.bezier_points:
            other_hash.update(array("d", other_bezier_point.co))
            other_hash.update(array("d", other_bezier_point.handle_left))
            other_hash.update(array("d", other_bezier_point.handle_right))
            other_hash.update(bytes(other_bezier_point.handle_right_type, "ascii"))
            other_hash.update(bytes(other_bezier_point.handle_left_type, "ascii"))
        for other_point in other_spline.points:
            other_hash.update(array("d", other_point.co))
            other_hash.update(array("d", [other_point.tilt, other_point.weight]))


def copy_curve(curve: bpy.types.Curve, other_curve: bpy.types.Curve):
    other_spline: bpy.types.Spline
    other_point: bpy.types.SplinePoint
    other_bezier_point: bpy.types.BezierSplinePoint

    if len(curve.splines) > 0:
        curve.splines.clear()
    point: bpy.types.SplinePoint
    bezier_point: bpy.types.BezierSplinePoint

    curve.dimensions = other_curve.dimensions
    curve.resolution_u = other_curve.resolution_u
    curve.resolution_v = other_curve.resolution_v

    for other_spline in other_curve.splines:
        spline: bpy.types.Spline = curve.splines.new(other_spline.type)
        if spline.type == "BEZIER":
            spline.bezier_points.add(len(other_spline.bezier_points) - 1)
            for i, bezier_point in enumerate(other_spline.bezier_points):
                spline.bezier_points[i].co = bezier_point.co
                spline.bezier_points[i].handle_left_type = bezier_point.handle_left_type
                spline.bezier_points[i].handle_left = bezier_point.handle_left
                spline.bezier_points[i].handle_right_type = bezier_point.handle_right_type
                spline.bezier_points[i].handle_right = bezier_point.handle_right
                spline.bezier_points[i].hide = bezier_point.hide
                spline.bezier_points[i].radius = bezier_point.radius
                spline.bezier_points[i].select_control_point = bezier_point.select_control_point
                spline.bezier_points[i].select_left_handle = bezier_point.select_left_handle
                spline.bezier_points[i].select_right_handle = bezier_point.select_right_handle
                spline.bezier_points[i].tilt = bezier_point.tilt
                spline.bezier_points[i].weight_softbody = bezier_point.weight_softbody
        else:
            spline.points.add(len(other_spline.points) - 1)
            for i, point in enumerate(other_spline.points):
                spline.points[i].co = point.co
                spline.points[i].hide = point.hide
                spline.points[i].tilt = point.tilt
                spline.points[i].weight = point.weight

        spline.hide = other_spline.hide
        spline.order_u = other_spline.order_u
        spline.order_v = other_spline.order_v
        spline.radius_interpolation = other_spline.radius_interpolation
        spline.resolution_u = other_spline.resolution_u
        spline.resolution_v = other_spline.resolution_v
        spline.tilt_interpolation = other_spline.tilt_interpolation
        spline.use_bezier_u = other_spline.use_bezier_u
        spline.use_bezier_v = other_spline.use_bezier_v
        spline.use_cyclic_u = other_spline.use_cyclic_u
        spline.use_cyclic_v = other_spline.use_cyclic_v
        spline.use_endpoint_u = other_spline.use_endpoint_u
        spline.use_endpoint_v = other_spline.use_endpoint_v
        spline.use_smooth = other_spline.use_smooth

