import bpy
import bpy
from typing import Tuple


def get_width_height() -> Tuple[int, int]:
    for area in bpy.context.screen.areas:
        if area.type == "IMAGE_EDITOR":
            image_editor: bpy.types.SpaceImageEditor = area.spaces.active
            image = image_editor.image
            if image is None:
                return 1, 1
            else:
                image_size = image_editor.image.size
                return image_size[0], image_size[1]
    return 1, 1


def closes_pixel(x: float, y: float, width: int, height: int) -> Tuple[float, float]:
    return round(x * width) / width, round(y * height) / height


def get_uvs_list() -> list[list[(float, float)]]:
    """
    Get all UV groups of all selected feces of all selected objects.
    """
    bpy.ops.object.mode_set(mode='OBJECT')

    uvs_list: list[list[(float, float)]] = []
    for selected_object in bpy.context.selected_objects:
        mesh_data: bpy.types.Mesh = selected_object.data
        for polygon in mesh_data.polygons:
            if len(polygon.loop_indices) == 0:
                continue

            uvs = []
            for i in polygon.loop_indices:
                if polygon.select:
                    print("Selected UV", i)
                    mesh_uv_loop = mesh_data.uv_layers.active.data[i]
                    uvs.append((mesh_uv_loop.uv.x, mesh_uv_loop.uv.y))
            uvs_list.append(uvs)

    bpy.ops.object.mode_set(mode='EDIT')

    return uvs_list


def register():
    pass


def unregister():
    pass
