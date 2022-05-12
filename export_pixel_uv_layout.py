import math
import os

import bpy
import bpy_extras.io_utils


class OT_ExportPixelUVLayoutFilebrowser(bpy.types.Operator, bpy_extras.io_utils.ExportHelper):
    bl_idname = "uv.export_pixel_uv_layout_filebrowser"
    bl_label = "Save UV Layout"
    bl_options = {"REGISTER"}

    filename_ext = ".png"

    filter_glob: bpy.props.StringProperty(default='*.png;*.jpg', options={'HIDDEN'})

    transparency: bpy.props.BoolProperty(name="Transparency", description='Should the image background be transparent?', default=True, )

    # TODO make with and height a size property for a cleaner look.
    width: bpy.props.IntProperty(
        name="Width",
        description="The width of the image.",
        default=1
    )
    height: bpy.props.IntProperty(
        name="Height",
        description="The height of the image.",
        default=1
    )

    def execute(self, context):
        filename, extension = os.path.splitext(self.filepath)

        width = self.width
        height = self.height

        uvs_list = get_uvs_list()

        print("get pixels")
        pixels = get_image(uvs_list, width, height, self.transparency)

        print("create image")
        image = bpy.data.images.new(filename, width, height, alpha=self.transparency)
        image.file_format = extension[1:].upper()
        image.filepath = self.filepath
        image.pixels = pixels[:]
        image.asset_generate_preview()
        image.update()
        image.save()

        bpy.data.batch_remove([image.id_data])

        return {'FINISHED'}


class OT_ExportPixelUVLayout(bpy.types.Operator):
    bl_label = "Export Pixel UV Layout"
    bl_idname = "uv.export_pixel_uv_layout"
    bl_options = {"REGISTER"}

    def execute(self, context):
        execute()
        return {'FINISHED'}


def execute():
    width, height = get_width_height()
    bpy.ops.uv.export_pixel_uv_layout_filebrowser('INVOKE_DEFAULT', width=width, height=height)


# TODO Move to different script since it is used in multiple files
def get_width_height():
    for area in bpy.context.screen.areas:
        if area.type == 'IMAGE_EDITOR':
            image_editor: bpy.types.SpaceImageEditor = area.spaces.active
            image = image_editor.image
            if image is None:
                return 64, 64
            else:
                image_size = image_editor.image.size
                return image_size[0], image_size[1]


def get_uvs_list():
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


def calculate_draw_pixel(uvs: list[(float, float)], width, height):
    pixel_index: list[int] = []

    middle_x = 0.0
    middle_y = 0.0

    for i in range(len(uvs)):
        middle_x += uvs[i][0]
        middle_y += uvs[i][1]

    middle_x = middle_x / (len(uvs)) * width
    middle_y = middle_y / (len(uvs)) * height

    uvs.append(uvs[0])

    for i in range(len(uvs) - 1):
        x1 = uvs[i][0] * width
        y1 = uvs[i][1] * height
        x2 = uvs[i + 1][0] * width
        y2 = uvs[i + 1][1] * height

        if abs(x2 - x1) > abs(y2 - y1):
            if x1 > x2:
                temp_x = x1
                x1 = x2
                x2 = temp_x
                temp_y = y1
                y1 = y2
                y2 = temp_y

            top = False
            if (y1 + y2) / 2 > middle_y:
                top = True
                y1 -= 1.01
                y2 -= 1.01
            else:
                y1 += 0.01
                y2 += 0.01

            if x1 != x2:
                y1 = y1 + (y2 - y1) * (math.floor(x1 + 0.01) - x1) / (x2 - x1)
                y2 = y1 + (y2 - y1) * (math.ceil(x2 - 0.01) - x1) / (x2 - x1)
            x1 = math.floor(x1 + 0.01)
            x2 = math.ceil(x2 - 0.01)

            for x in range(x1, x2):
                if y1 < y2:
                    if top:
                        y = math.ceil(y1 + (y2 - y1) / (x2 - x1) * (x + 1 - x1))
                    else:
                        y = math.floor(y1 + (y2 - y1) / (x2 - x1) * (x + 0 - x1))
                else:
                    if top:
                        y = math.ceil(y1 + (y2 - y1) / (x2 - x1) * (x + 0 - x1))
                    else:
                        y = math.floor(y1 + (y2 - y1) / (x2 - x1) * (x + 1 - x1))

                pixel_index.append((y * width + x) * 4)
        else:
            if y1 > y2:
                temp_x = x1
                x1 = x2
                x2 = temp_x
                temp_y = y1
                y1 = y2
                y2 = temp_y

            top = False
            if (x1 + x2) / 2 > middle_x:
                top = True
                x1 -= 1.01
                x2 -= 1.01
            else:
                x1 += 0.01
                x2 += 0.01

            if y1 != y2:
                x1 = x1 + (x2 - x1) * (math.floor(y1 + 0.01) - y1) / (y2 - y1)
                x2 = x1 + (x2 - x1) * (math.ceil(y2 - 0.01) - y1) / (y2 - y1)
            y1 = math.floor(y1 + 0.01)
            y2 = math.ceil(y2 - 0.01)

            for y in range(y1, y2):
                if x1 < x2:
                    if top:
                        x = math.ceil(x1 + (x2 - x1) / (y2 - y1) * (y + 1 - y1))
                    else:
                        x = math.floor(x1 + (x2 - x1) / (y2 - y1) * (y + 0 - y1))
                else:
                    if top:
                        x = math.ceil(x1 + (x2 - x1) / (y2 - y1) * (y + 0 - y1))
                    else:
                        x = math.floor(x1 + (x2 - x1) / (y2 - y1) * (y + 1 - y1))

                pixel_index.append((y * width + x) * 4)

    uvs.clear()
    return pixel_index


def get_image(uvs_list: list[list[(float, float)]], width: int, height: int, transparent: bool):
    pixels = [0.0] * width * height * 4

    if not transparent:
        for y in range(height):
            for x in range(width):
                i = (y * width + x) * 4
                if (x + y) % 2 == 0:
                    pixels[i] = 0.0
                    pixels[i + 1] = 0.0
                    pixels[i + 2] = 0.0
                else:
                    pixels[i] = 0.1
                    pixels[i + 1] = 0.1
                    pixels[i + 2] = 0.1

                pixels[i + 3] = 1

    print("UVs:", len(uvs_list), "Size: ", width, height)
    for uvs in uvs_list:
        if len(uvs) == 0:
            continue

        average_x = 0.0
        average_y = 0.0
        for uv in uvs:
            average_x += uv[0]
            average_y += uv[1]

        average_x = max(0.0, min(average_x / len(uvs), 1.0))
        average_y = max(0.0, min(average_y / len(uvs), 1.0))

        for i in calculate_draw_pixel(uvs, width, height):
            if i >= len(pixels) or i < 0:
                continue
            pixels[i] = average_x
            pixels[i + 1] = average_y
            pixels[i + 2] = 0
            pixels[i + 3] = 1

    return pixels


def add_menu_item(self, context):
    self.layout.operator("uv.export_pixel_uv_layout")


def register():
    bpy.utils.register_class(OT_ExportPixelUVLayoutFilebrowser)
    bpy.utils.register_class(OT_ExportPixelUVLayout)

    bpy.types.IMAGE_MT_uvs.append(add_menu_item)


def unregister():
    bpy.utils.unregister_class(OT_ExportPixelUVLayoutFilebrowser)
    bpy.utils.unregister_class(OT_ExportPixelUVLayout)

    bpy.types.IMAGE_MT_uvs.remove(add_menu_item)


if __name__ == "__main__":
    register()
    # bpy.utils.unregister_class(OT_ExportUVLayoutFilebrowser)
