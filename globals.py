def is_sinegear_data(obj):
    return obj.blablacad_data.type == "SINEGEAR"


def get_sinegear_data(obj):
    return obj.blablacad_data.sinegear_data


def get_sinegear_enum(obj):
    blablacad_data = obj.blablacad_data
    type_enum = blablacad_data.bl_rna.properties['type'].enum_items
    return type_enum[blablacad_data.type]


def make_sinegear_data(obj):
    blablacad_data = obj.blablacad_data
    blablacad_data.type = "SINEGEAR"
    return blablacad_data.sinegear_data
