import bpy
from . import move_uv_to_closest_pixel, rotate_uvs_to_closest_orthogonal, mirror_uv_around_vertex


def add_menu_item(self, context):
    self.layout.separator()
    self.layout.operator(move_uv_to_closest_pixel.OT_MoveUVToClosestPixel.bl_idname, icon="TRANSFORM_ORIGINS")
    self.layout.operator(rotate_uvs_to_closest_orthogonal.OT_RotateUVsToClosestOrthogonal.bl_idname, icon="DRIVER_ROTATIONAL_DIFFERENCE")
    self.layout.operator(mirror_uv_around_vertex.OT_MirrorUVAroundVertex.bl_idname, icon="MOD_MIRROR")


def register():
    move_uv_to_closest_pixel.register()
    mirror_uv_around_vertex.register()
    rotate_uvs_to_closest_orthogonal.register()

    bpy.types.IMAGE_MT_uvs_snap.append(add_menu_item)


def unregister():
    move_uv_to_closest_pixel.unregister()
    mirror_uv_around_vertex.unregister()
    rotate_uvs_to_closest_orthogonal.unregister()

    bpy.types.IMAGE_MT_uvs_snap.remove(add_menu_item)
