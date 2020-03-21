import math


def r(x, y, center=None):
    center_x, center_y = center or (0, 0)
    math.sqrt(math.pow(center_x - x, 2) + math.pow(center_y - y, 2))


def theta(x, y, center=None):
    center_x, center_y = center or (0, 0)
    math.atan2(center_y - y, center_x - x)


def polar_to_xy(r, theta):
    return r * math.cos(theta), r * math.sin(theta)
