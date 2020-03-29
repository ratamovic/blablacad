import bpy


def get_meshify_data(obj):
    return obj.blablacad_data.meshify_data


def get_meshify_enum(obj):
    blablacad_data = obj.blablacad_data
    type_enum = blablacad_data.bl_rna.properties['type'].enum_items
    return type_enum[blablacad_data.type]


def has_meshify_data(obj):
    return isinstance(obj, bpy.types.Object) and obj.blablacad_data.type == "MESHIFY"


def make_meshify_data(obj):
    blablacad_data = obj.blablacad_data
    blablacad_data.type = "MESHIFY"
    return blablacad_data.meshify_data


def get_sinegear_data(obj):
    return obj.blablacad_data.sinegear_data


def get_sinegear_enum(obj):
    blablacad_data = obj.blablacad_data
    type_enum = blablacad_data.bl_rna.properties['type'].enum_items
    return type_enum[blablacad_data.type]


def has_sinegear_data(obj):
    return obj.blablacad_data.type == "SINEGEAR"


def make_sinegear_data(obj):
    blablacad_data = obj.blablacad_data
    blablacad_data.type = "SINEGEAR"
    return blablacad_data.sinegear_data
