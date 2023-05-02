import bpy
import mathutils
import math
from sys import float_info
from .. import helper


class UVMapper:
    def __init__(self) -> None:
        self.width, self.height = helper.get_width_height()
        self.unit_scale = bpy.context.scene.unit_settings.scale_length

    def map_x(self, x: float) -> float:
        return x * self.unit_scale / self.width

    def map_y(self, y: float) -> float:
        return y * self.unit_scale / self.height


class OT_UnwrapByDirection(bpy.types.Operator):
    bl_idname = "uv.unwrap_by_direction"
    bl_label = "Unwrap by Direction"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Use a vector as normal for a projection plane and project all selected faces"

    vector: bpy.props.FloatVectorProperty(name="Direction", description="The direction of the projection plane normal", default=(0, 0, 0))

    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')

        vector = mathutils.Vector(self.vector)
        sign = 1
        if vector.y < 0:
            sign = -1
        quaternion = mathutils.Vector((0, 1, 0)).rotation_difference(vector * mathutils.Vector((1, sign, 1)))

        uv_mapper = UVMapper()

        for selected_object in context.selected_objects:
            if not selected_object.type == "MESH":
                continue
            mesh_data: bpy.types.Mesh = selected_object.data
            for polygon in mesh_data.polygons:
                if polygon.select:
                    for i in polygon.loop_indices:
                        co = quaternion @ mesh_data.vertices[mesh_data.loops[i].vertex_index].co
                        mesh_uv_loop = mesh_data.uv_layers.active.data[i]
                        mesh_uv_loop.uv.x = uv_mapper.map_x(co.x)
                        mesh_uv_loop.uv.y = uv_mapper.map_y(co.z)

        bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}


class OT_UnwrapByNormal(bpy.types.Operator):
    bl_idname = "uv.unwrap_by_normal"
    bl_label = "Unwrap by Normal"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "For every selected face use its normal for a projection plane"

    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')

        uv_mapper = UVMapper()

        for selected_object in context.selected_objects:
            if not selected_object.type == "MESH":
                continue
            mesh_data: bpy.types.Mesh = selected_object.data
            for polygon in mesh_data.polygons:
                if polygon.select:
                    uvs = mesh_data.uv_layers.active.data
                    center = mathutils.Vector((0, 0))
                    for i in polygon.loop_indices:
                        center += uvs[i].uv
                    center /= len(polygon.loop_indices)

                    for i in polygon.loop_indices:
                        n = polygon.normal
                        sign = 1
                        if n.y < 0:
                            sign = -1
                        quaternion = mathutils.Vector((0, 1, 0)).rotation_difference(n * mathutils.Vector((1, sign, 1)))

                        co = quaternion @ (mesh_data.vertices[mesh_data.loops[i].vertex_index].co - polygon.center)

                        uv = uvs[i].uv
                        uv.x = uv_mapper.map_x(co.x)
                        uv.y = uv_mapper.map_y(co.z)
                        uv += center

        bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}


class DirectionPolygons:
    def __init__(self, direction: mathutils.Vector) -> None:
        self.direction = direction
        self.polygons: list[bpy.types.MeshPolygon] = []

    def try_append(self, polygon: bpy.types.MeshPolygon, angle: float) -> bool:
        if angle < polygon.normal.angle(self.direction, 360):
            return False
        else:
            self.polygons.append(polygon)
            return True

    def get_directed(self, uv_mapper: UVMapper):
        return DirectedPolygons(self, uv_mapper)


class DirectedPolygons:
    def __init__(self, direction_polygons: DirectionPolygons, uv_mapper: UVMapper) -> None:
        uvs = []
        if len(direction_polygons.polygons) > 0:
            mesh_data: bpy.types.Mesh = direction_polygons.polygons[0].id_data
            sign = 1
            if direction_polygons.direction.y < 0:
                sign = -1
            quaternion = mathutils.Vector((0, 1, 0)).rotation_difference(direction_polygons.direction * mathutils.Vector((1, sign, 1)))

            min_x = float_info.max
            min_y = float_info.max
            max_x = -float_info.max
            max_y = -float_info.max

            for polygon in direction_polygons.polygons:
                for i in polygon.loop_indices:
                    co = quaternion @ (mesh_data.vertices[mesh_data.loops[i].vertex_index].co)
                    uv = mesh_data.uv_layers.active.data[i].uv
                    uv.x = uv_mapper.map_x(co.x)
                    uv.y = uv_mapper.map_y(co.z)

                    min_x = min(uv.x, min_x)
                    min_y = min(uv.y, min_y)
                    max_x = max(uv.x, max_x)
                    max_y = max(uv.y, max_y)

                    uvs.append(uv)

            self.min = mathutils.Vector((min_x, min_y))
            self.max = mathutils.Vector((max_x, max_y))
            self.size = self.max - self.min
        else:
            self.min = mathutils.Vector((0, 0))
            self.max = mathutils.Vector((0, 0))
        self.uvs: list(mathutils.Vector) = uvs
        self.size = self.max - self.min

    def move(self, vector: mathutils.Vector):
        for uv in self.uvs:
            self.min += vector
            self.max += vector
            uv += vector


class OT_UnwrapByAutoDirection(bpy.types.Operator):
    bl_idname = "uv.unwrap_by_auto_direction"
    bl_label = "Unwrap Auto Direction"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Use the major facing direction of a selected face and use this vector as normal for a projection plane"

    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')

        uv_mapper = UVMapper()

        selected_polygons = []
        for selected_object in context.selected_objects:
            if not selected_object.type == "MESH":
                continue
            mesh_data: bpy.types.Mesh = selected_object.data
            for polygon in mesh_data.polygons:
                if polygon.select:
                    selected_polygons.append(polygon)

        direction_polygons = [
            DirectionPolygons(mathutils.Vector((0, 1, 0))),
            DirectionPolygons(mathutils.Vector((0, -1, 0))),
            DirectionPolygons(mathutils.Vector((1, 0, 0))),
            DirectionPolygons(mathutils.Vector((-1, 0, 0))),
            DirectionPolygons(mathutils.Vector((0, 0, 1))),
            DirectionPolygons(mathutils.Vector((0, 0, -1))),
        ]
        for angle in [math.pi / 4, math.pi / 3, math.pi / 2]:
            i = 0
            while i < len(selected_polygons):
                for direction_polygon in direction_polygons:
                    if direction_polygon.try_append(selected_polygons[i], angle):
                        selected_polygons.pop(i)
                        i -= 1
                        break
                i += 1
                pass

        p_y = direction_polygons[0].get_directed(uv_mapper)
        n_y = direction_polygons[1].get_directed(uv_mapper)
        p_x = direction_polygons[2].get_directed(uv_mapper)
        n_x = direction_polygons[3].get_directed(uv_mapper)
        p_z = direction_polygons[4].get_directed(uv_mapper)
        n_z = direction_polygons[5].get_directed(uv_mapper)

        m_p_y = mathutils.Vector((
            -p_y.min.x,
            - p_y.max.y + 1 - p_z.size.y
        ))
        m_n_y = mathutils.Vector((
            -n_y.min.x + p_y.size.x + n_x.size.x,
            - n_y.max.y + 1 - p_z.size.y
        ))
        m_p_x = mathutils.Vector((
            -p_x.min.x + p_y.size.x + n_x.size.x + n_y.size.x,
            - p_x.max.y + 1 - p_z.size.y
        ))
        m_n_x = mathutils.Vector((
            -n_x.min.x + p_y.size.x,
            - n_x.max.y + 1 - p_z.size.y
        ))
        m_p_z = mathutils.Vector((
            -p_z.min.x + p_y.size.x + n_x.size.x,
            - p_z.max.y + 1
        ))
        m_n_z = mathutils.Vector((
            -n_z.min.x + p_y.size.x + n_x.size.x,
            - n_z.max.y + 1 - p_z.size.y - p_y.size.y
        ))

        p_y.move(m_p_y)
        n_y.move(m_n_y)
        p_x.move(m_p_x)
        n_x.move(m_n_x)
        p_z.move(m_p_z)
        n_z.move(m_n_z)

        bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}


class UNWRAP_MT_UnwrapPixelPerfect(bpy.types.Menu):
    bl_idname = "UNWRAP_MT_pixel_perfect"
    bl_label = "Unwrap Pixel Perfect"

    def draw(self, context):
        self.layout.operator(OT_UnwrapByAutoDirection.bl_idname, text="Auto Direction")
        self.layout.separator()
        self.layout.operator(OT_UnwrapByNormal.bl_idname, text="Normal Direction")
        self.layout.separator()
        x = self.layout.operator(OT_UnwrapByDirection.bl_idname, text="X Direction")
        if x:
            x.vector = (1, 0, 0)
        y = self.layout.operator(OT_UnwrapByDirection.bl_idname, text="Y Direction")
        if y:
            y.vector = (0, 1, 0)
        z = self.layout.operator(OT_UnwrapByDirection.bl_idname, text="Z Direction")
        if z:
            z.vector = (0, 0, 1)
        self.layout.separator()
        self.layout.operator(OT_UnwrapByDirection.bl_idname, text="Custom Direction")


def add_menu_item(self: bpy.types.Menu, context):
    self.layout.menu(UNWRAP_MT_UnwrapPixelPerfect.bl_idname)
    self.layout.separator()


def register():
    bpy.utils.register_class(OT_UnwrapByDirection)
    bpy.utils.register_class(OT_UnwrapByNormal)
    bpy.utils.register_class(OT_UnwrapByAutoDirection)
    bpy.utils.register_class(UNWRAP_MT_UnwrapPixelPerfect)

    bpy.types.VIEW3D_MT_uv_map.prepend(add_menu_item)


def unregister():
    bpy.utils.unregister_class(OT_UnwrapByDirection)
    bpy.utils.unregister_class(OT_UnwrapByNormal)
    bpy.utils.unregister_class(OT_UnwrapByAutoDirection)
    bpy.utils.unregister_class(UNWRAP_MT_UnwrapPixelPerfect)

    bpy.types.VIEW3D_MT_uv_map.remove(add_menu_item)


if __name__ == "__main__":
    register()
