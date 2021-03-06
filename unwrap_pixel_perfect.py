import math
from enum import Enum

import bpy
import mathutils


class Direction(Enum):
    POSITIVE_X = 0
    NEGATIVE_X = 1
    POSITIVE_Y = 2
    NEGATIVE_Y = 3
    POSITIVE_Z = 4
    NEGATIVE_Z = 5

    def get_inverse(self):
        if self == Direction.POSITIVE_X:
            return Direction.NEGATIVE_X
        elif self == Direction.NEGATIVE_X:
            return Direction.POSITIVE_X
        elif self == Direction.POSITIVE_Y:
            return Direction.NEGATIVE_Y
        elif self == Direction.NEGATIVE_Y:
            return Direction.POSITIVE_Y
        elif self == Direction.POSITIVE_Z:
            return Direction.NEGATIVE_Z
        elif self == Direction.NEGATIVE_Z:
            return Direction.POSITIVE_Z

    def get_index(self):
        return self.value


class Angle:
    def __init__(self, normal: mathutils.Vector, direction: Direction):
        # Somehow the Vector.angle(...) function calculates wrong values...
        def calc_angle(vec1: mathutils.Vector, vec2: mathutils.Vector):
            return (1 - (vec1.dot(vec2) / (vec1.length * vec2.length))) * 90

        if direction == Direction.POSITIVE_X:
            self.raw_angle: float = calc_angle(normal, mathutils.Vector((1, 0, 0)))
            # print("X", normal, (1, 0, 0), self.raw_angle)
        elif direction == Direction.POSITIVE_Y:
            self.raw_angle: float = calc_angle(normal, mathutils.Vector((0, 1, 0)))
            # print("Y", normal, (0, 1, 0), self.raw_angle)
        elif direction == Direction.POSITIVE_Z:
            self.raw_angle: float = calc_angle(normal, mathutils.Vector((0, 0, 1)))
            # print("Z", normal, (0, 0, 1), self.raw_angle)
        else:
            raise Exception("Unsupported Direction in Angle")
        self.abs_angle: float = abs(abs(self.raw_angle - 90) - 90)
        self.direction: Direction = direction
        if self.raw_angle > 90.0:
            self.direction = direction.get_inverse()


class UVInfo:
    def __init__(self, vertex: list[float], direction: Direction):
        self.direction = direction

        if self.direction == Direction.POSITIVE_X:
            self.x = vertex.y
            self.y = vertex.z
        elif self.direction == Direction.NEGATIVE_X:
            self.x = -vertex.y
            self.y = vertex.z
        elif self.direction == Direction.POSITIVE_Y:
            self.x = vertex.x
            self.y = vertex.z
        elif self.direction == Direction.NEGATIVE_Y:
            self.x = -vertex.x
            self.y = vertex.z
        elif self.direction == Direction.POSITIVE_Z:
            self.x = vertex.x
            self.y = vertex.y
        elif self.direction == Direction.NEGATIVE_Z:
            self.x = -vertex.x
            self.y = vertex.y


class OT_UnwrapPixelPerfectByDirection(bpy.types.Operator):
    bl_idname = "uv.unwrap_pixel_perfect_by_direction"
    bl_label = "Unwrap Pixel Perfect by Direction"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Generates pixel perfect uvs based on the face direction"

    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')

        width, height = get_width_height()

        unit_scale = bpy.context.scene.unit_settings.scale_length

        for selected_object in bpy.context.selected_objects:
            mesh_data: bpy.types.Mesh = selected_object.data

            raw_uvs = []
            directions = []
            for polygon in mesh_data.polygons:
                # Only on selected
                normal: mathutils.Vector = polygon.normal
                angle_x: Angle = Angle(normal, Direction.POSITIVE_X)
                angle_y: Angle = Angle(normal, Direction.POSITIVE_Y)
                angle_z: Angle = Angle(normal, Direction.POSITIVE_Z)

                direction: Direction

                # get new uvs
                if angle_x.abs_angle <= angle_y.abs_angle and angle_x.abs_angle <= angle_z.abs_angle:
                    direction = angle_x.direction
                elif angle_y.abs_angle <= angle_z.abs_angle:
                    direction = angle_y.direction
                else:
                    direction = angle_z.direction

                for i in polygon.vertices:
                    raw_uvs.append(get_uv_from_vertex_by_direction(mesh_data.vertices[i].co, direction))
                    directions.append(direction)

            recalculate_uv_positions_by_direction(raw_uvs, directions, unit_scale * 1.0, width, height)

            for polygon in mesh_data.polygons:
                for i in polygon.loop_indices:
                    if polygon.select:
                        mesh_uv_loop = mesh_data.uv_layers.active.data[i]
                        raw_uv = raw_uvs[i]

                        mesh_uv_loop.uv.x = raw_uv[0]
                        mesh_uv_loop.uv.y = raw_uv[1]

        bpy.ops.object.mode_set(mode='EDIT')

        return {'FINISHED'}


class OT_UnwrapPixelPerfectBySize(bpy.types.Operator):
    bl_idname = "uv.unwrap_pixel_perfect_by_size"
    bl_label = "Unwrap Pixel Perfect by Size"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Generates pixel perfect uvs based on the size"

    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')

        width, height = get_width_height()

        unit_scale = bpy.context.scene.unit_settings.scale_length

        for selected_object in bpy.context.selected_objects:
            mesh_data: bpy.types.Mesh = selected_object.data

            raw_uvs = []
            directions = []
            for polygon in mesh_data.polygons:
                # Only on selected
                normal: mathutils.Vector = polygon.normal
                angle_x: Angle = Angle(normal, Direction.POSITIVE_X)
                angle_y: Angle = Angle(normal, Direction.POSITIVE_Y)
                angle_z: Angle = Angle(normal, Direction.POSITIVE_Z)

                direction: Direction

                a: mathutils.Vector

                # get new uvs
                if angle_x.abs_angle <= angle_y.abs_angle and angle_x.abs_angle <= angle_z.abs_angle:
                    a = mathutils.Vector((0, 1, 0)).cross(normal)
                    direction = angle_x.direction
                elif angle_y.abs_angle <= angle_z.abs_angle:
                    a = mathutils.Vector((0, 0, 1)).cross(normal)
                    direction = angle_y.direction
                else:
                    a = mathutils.Vector((1, 0, 0)).cross(normal)
                    direction = angle_z.direction

                b = a.cross(normal)

                t = mathutils.Matrix(((normal.x, a.x, b.x), (normal.y, a.y, b.y), (normal.z, a.z, b.z)))
                t.invert()

                for i in polygon.vertices:
                    vertex = t @ mesh_data.vertices[i].co
                    # TODO Rotate vector based on direction
                    raw_uvs.append([vertex.y, vertex.z])
                    directions.append(Direction.POSITIVE_X)

            # FIXME UVs are overlapping instead of sequence
            recalculate_uv_positions_by_direction(raw_uvs, directions, unit_scale * 1.0, width, height)

            for polygon in mesh_data.polygons:
                for i in polygon.loop_indices:
                    if polygon.select:
                        mesh_uv_loop = mesh_data.uv_layers.active.data[i]
                        raw_uv = raw_uvs[i]

                        mesh_uv_loop.uv.x = raw_uv[0]
                        mesh_uv_loop.uv.y = raw_uv[1]

        bpy.ops.object.mode_set(mode='EDIT')

        return {'FINISHED'}


# TODO Move to different script since it is used in multiple files
def get_width_height():
    for area in bpy.context.screen.areas:
        if area.type == 'IMAGE_EDITOR':
            image_editor: bpy.types.SpaceImageEditor = area.spaces.active
            image = image_editor.image
            if image is None:
                return 1, 1
            else:
                image_size = image_editor.image.size
                return image_size[0], image_size[1]


def recalculate_uv_positions_by_direction(raw_uvs: list[UVInfo], directions: list[Direction], scale: float, width: float, height: float):
    min_x = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    max_x = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    add_x = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    for i in range(len(raw_uvs)):
        value = directions[i].get_index()
        min_x[value] = min(min_x[value], raw_uvs[i][0])
        max_x[value] = max(max_x[value], raw_uvs[i][1])

    max_x.insert(0, 0.0)

    temp_add_x = 0.0
    for i in range(7):
        temp_add_x += max_x[i] - min_x[i]
        add_x[i] += temp_add_x

    for i in range(len(raw_uvs)):
        value = directions[i].get_index()
        raw_uvs[i][0] += add_x[value]

        raw_uvs[i][0] = round(raw_uvs[i][0] * scale) / width
        raw_uvs[i][1] = round(raw_uvs[i][1] * scale) / height


def get_uv_from_vertex_by_direction(vertex: list[float], direction: Direction):
    if direction == Direction.POSITIVE_X:
        return [vertex.y, vertex.z]
    elif direction == Direction.NEGATIVE_X:
        return [-vertex.y, vertex.z]
    elif direction == Direction.POSITIVE_Y:
        return [vertex.x, vertex.z]
    elif direction == Direction.NEGATIVE_Y:
        return [-vertex.x, vertex.z]
    elif direction == Direction.POSITIVE_Z:
        return [vertex.x, vertex.y]
    elif direction == Direction.NEGATIVE_Z:
        return [-vertex.x, vertex.y]


def add_menu_item(self, context):
    self.layout.operator("uv.unwrap_pixel_perfect_by_direction")
    self.layout.operator("uv.unwrap_pixel_perfect_by_size")


def register():
    bpy.utils.register_class(OT_UnwrapPixelPerfectByDirection)
    bpy.utils.register_class(OT_UnwrapPixelPerfectBySize)

    bpy.types.VIEW3D_MT_uv_map.append(add_menu_item)


def unregister():
    bpy.utils.unregister_class(OT_UnwrapPixelPerfectByDirection)
    bpy.utils.unregister_class(OT_UnwrapPixelPerfectBySize)

    bpy.types.VIEW3D_MT_uv_map.remove(add_menu_item)


if __name__ == "__main__":
    register()


# Edit UVS from https://b3d.interplanety.org/en/working-with-uv-maps-through-the-blender-api/
