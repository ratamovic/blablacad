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


def hash_curve(hash_algo, curve: bpy.types.Curve):
    spline: bpy.types.Spline
    point: bpy.types.SplinePoint
    bezier_point: bpy.types.BezierSplinePoint

    hash_algo.update(array("l", [curve.resolution_u, curve.resolution_v]))
    hash_algo.update(bytes(curve.dimensions, "ascii"))
    for spline in curve.splines:
        hash_algo.update(bytes(spline.type, "ascii"))
        hash_algo.update(bytes(spline.radius_interpolation, "ascii"))
        hash_algo.update(bytes(spline.tilt_interpolation, "ascii"))
        hash_algo.update(array("l", [
            spline.order_u, spline.order_v, spline.resolution_u,
            spline.resolution_v, spline.use_bezier_u,
            spline.use_bezier_v, spline.use_cyclic_u, spline.use_cyclic_v,
            spline.use_endpoint_u, spline.use_endpoint_v, spline.use_smooth]))
        for bezier_point in spline.bezier_points:
            hash_algo.update(array("d", bezier_point.co))
            hash_algo.update(array("d", bezier_point.handle_left))
            hash_algo.update(array("d", bezier_point.handle_right))
            hash_algo.update(bytes(bezier_point.handle_right_type, "ascii"))
            hash_algo.update(bytes(bezier_point.handle_left_type, "ascii"))
        for point in spline.points:
            hash_algo.update(array("d", point.co))
            hash_algo.update(array("d", [point.tilt, point.weight]))


def copy_curve(to_curve: bpy.types.Curve, from_curve: bpy.types.Curve):
    from_spline: bpy.types.Spline
    from_point: bpy.types.SplinePoint
    from_bezier_point: bpy.types.BezierSplinePoint

    if len(to_curve.splines) > 0:
        to_curve.splines.clear()

    to_curve.dimensions = from_curve.dimensions
    to_curve.resolution_u = from_curve.resolution_u
    to_curve.resolution_v = from_curve.resolution_v

    for from_spline in from_curve.splines:
        to_spline: bpy.types.Spline = to_curve.splines.new(from_spline.type)
        if to_spline.type == "BEZIER":
            to_spline.bezier_points.add(len(from_spline.bezier_points) - 1)
            for i, from_bezier_point in enumerate(from_spline.bezier_points):
                to_spline.bezier_points[i].co = from_bezier_point.co
                to_spline.bezier_points[i].handle_left_type = from_bezier_point.handle_left_type
                to_spline.bezier_points[i].handle_left = from_bezier_point.handle_left
                to_spline.bezier_points[i].handle_right_type = from_bezier_point.handle_right_type
                to_spline.bezier_points[i].handle_right = from_bezier_point.handle_right
                to_spline.bezier_points[i].hide = from_bezier_point.hide
                to_spline.bezier_points[i].radius = from_bezier_point.radius
                to_spline.bezier_points[i].select_control_point = from_bezier_point.select_control_point
                to_spline.bezier_points[i].select_left_handle = from_bezier_point.select_left_handle
                to_spline.bezier_points[i].select_right_handle = from_bezier_point.select_right_handle
                to_spline.bezier_points[i].tilt = from_bezier_point.tilt
                to_spline.bezier_points[i].weight_softbody = from_bezier_point.weight_softbody
        else:
            to_spline.points.add(len(from_spline.points) - 1)
            for i, from_point in enumerate(from_spline.points):
                to_spline.points[i].co = from_point.co
                to_spline.points[i].hide = from_point.hide
                to_spline.points[i].tilt = from_point.tilt
                to_spline.points[i].weight = from_point.weight

        to_spline.hide = from_spline.hide
        to_spline.order_u = from_spline.order_u
        to_spline.order_v = from_spline.order_v
        to_spline.radius_interpolation = from_spline.radius_interpolation
        to_spline.resolution_u = from_spline.resolution_u
        to_spline.resolution_v = from_spline.resolution_v
        to_spline.tilt_interpolation = from_spline.tilt_interpolation
        to_spline.use_bezier_u = from_spline.use_bezier_u
        to_spline.use_bezier_v = from_spline.use_bezier_v
        to_spline.use_cyclic_u = from_spline.use_cyclic_u
        to_spline.use_cyclic_v = from_spline.use_cyclic_v
        to_spline.use_endpoint_u = from_spline.use_endpoint_u
        to_spline.use_endpoint_v = from_spline.use_endpoint_v
        to_spline.use_smooth = from_spline.use_smooth


def hash_mesh(hash_algo, mesh: bpy.types.Mesh):
    edge: bpy.types.MeshEdge
    vertex: bpy.types.MeshVertex
    loop: bpy.types.MeshLoop
    polygon: bpy.types.MeshPolygon

    for vertex in mesh.vertices:
        hash_algo.update(array("d", [vertex.bevel_weight]))
        hash_algo.update(array("d", vertex.co))
        hash_algo.update(array("d", vertex.normal))

    for edge in mesh.edges:
        hash_algo.update(array("d", [edge.bevel_weight, edge.crease, edge.crease]))
        hash_algo.update(array("l", edge.vertices))
        hash_algo.update(array("l", [edge.is_loose, edge.use_edge_sharp, edge.use_seam]))

    for loop in mesh.loops:
        hash_algo.update(array("l", [loop.edge_index, loop.vertex_index]))
        hash_algo.update(array("d", loop.normal))

    for polygon in mesh.polygons:
        hash_algo.update(array("d", [polygon.loop_start, polygon.loop_total]))
        hash_algo.update(array("d", polygon.normal))
        hash_algo.update(array("l", [polygon.use_smooth]))
        hash_algo.update(array("l", polygon.vertices))
