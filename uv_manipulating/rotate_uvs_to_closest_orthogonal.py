import bpy
import bmesh
import mathutils
from sys import float_info


class OT_RotateUVsToClosestOrthogonal(bpy.types.Operator):
    bl_idname = "uv.rotate_uv_to_closest_orthogonal"
    bl_label = "Groupe to orthogonal Line"
    bl_description = "Select two vertex and rotate them so they are parallel to either the x ore the y axises"
    bl_options = {"REGISTER", "UNDO"}

    mouse_x: bpy.props.IntProperty()
    mouse_y: bpy.props.IntProperty()

    def execute(self, context):

        uvs = []
        mouse = mathutils.Vector(context.region.view2d.region_to_view(self.mouse_x, self.mouse_y))
        direction = mathutils.Vector((float_info.max, float_info.max))
        closest = mathutils.Vector((float_info.max, float_info.max))
        distance = float_info.max

        for selected_object in context.selected_objects:
            if not selected_object.type == "MESH":
                continue

            mesh: bpy.types.Mesh = selected_object.data
            bm = bmesh.from_edit_mesh(mesh)
            uv_layer = bm.loops.layers.uv.verify()

            for face in bm.faces:
                uv1 = face.loops[-2][uv_layer]
                uv2 = face.loops[-1][uv_layer]
                for point in face.loops:
                    uv3 = point[uv_layer]

                    if uv2.select:
                        uvs.append(uv2.uv)
                        new_distance = (mouse - uv2.uv).length_squared

                        d1 = (mouse - uv2.uv).project(uv1.uv - uv2.uv) - (mouse - uv2.uv)
                        d3 = (mouse - uv2.uv).project(uv3.uv - uv2.uv) - (mouse - uv2.uv)

                        if new_distance < distance:
                            if (d1 < d3 or not uv3.select) and uv1.select:
                                distance = new_distance
                                closest = uv2.uv
                                direction = d1
                            if (d3 <= d1 or not uv1.select) and uv3.select:
                                distance = new_distance
                                closest = uv2.uv
                                direction = d3

                    uv1 = uv2
                    uv2 = uv3

        if len(uvs) < 2:
            return {"FINISHED"}

        angles = [
            -mathutils.Vector((1, 0)).angle_signed(direction, 0),
            -mathutils.Vector((0, 1)).angle_signed(direction, 0),
            -mathutils.Vector((-1, 0)).angle_signed(direction, 0),
            -mathutils.Vector((0, -1)).angle_signed(direction, 0),
        ]

        angle = 1000000
        for a in angles:
            if abs(a) < abs(angle):
                angle = a

        mat_rot = mathutils.Matrix.Rotation(angle, 3, 'Z').to_2x2()

        for uv in uvs:
            vec = ((uv - closest) @ mat_rot) + closest
            uv[0] = vec[0]
            uv[1] = vec[1]

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}

    def invoke(self, context, event):
        self.mouse_x = event.mouse_region_x
        self.mouse_y = event.mouse_region_y
        return self.execute(context)


def add_menu_item(self, context):
    self.layout.operator(OT_RotateUVsToClosestOrthogonal.bl_idname, icon="DRIVER_ROTATIONAL_DIFFERENCE")


def add_pie_item(self: bpy.types.Menu, context):
    self.layout.menu_pie().operator(OT_RotateUVsToClosestOrthogonal.bl_idname, icon="DRIVER_ROTATIONAL_DIFFERENCE")


def register():
    bpy.utils.register_class(OT_RotateUVsToClosestOrthogonal)

    bpy.types.IMAGE_MT_uvs_snap.append(add_menu_item)
    # bpy.types.IMAGE_MT_uvs_snap_pie.append(add_pie_item)


def unregister():
    bpy.utils.unregister_class(OT_RotateUVsToClosestOrthogonal)

    bpy.types.IMAGE_MT_uvs_snap.remove(add_menu_item)
    # bpy.types.IMAGE_MT_uvs_snap_pie.remove(add_pie_item)
