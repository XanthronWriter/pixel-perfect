import bpy
import bmesh
import mathutils
from sys import float_info
from .. import helper


class OT_MoveUVToClosestPixel(bpy.types.Operator):
    bl_idname = "uv.move_uv_to_closest_pixel"
    bl_label = "Group to Pixel"
    bl_description = "Select one vertex and snap it to the nearest pixel. Move every connected vertex respectively"
    bl_options = {"REGISTER", "UNDO"}

    mouse_x: bpy.props.IntProperty()
    mouse_y: bpy.props.IntProperty()

    def execute(self, context):

        uvs = []
        mouse = mathutils.Vector(context.region.view2d.region_to_view(self.mouse_x, self.mouse_y))

        distance = float_info.max
        mouse_uv = None

        for selected_object in context.selected_objects:
            if not selected_object.type == "MESH":
                continue
            mesh: bpy.types.Mesh = selected_object.data
            bm = bmesh.from_edit_mesh(mesh)
            uv_layer = bm.loops.layers.uv.verify()

            for face in bm.faces:
                for loop in face.loops:
                    uv = loop[uv_layer]
                    if uv.select:
                        uv = uv.uv
                        uvs.append(uv)
                        new_distance = (mouse - uv).length_squared
                        if new_distance < distance:
                            distance = new_distance
                            mouse_uv = uv

        if len(uvs) == 0:
            return {"FINISHED"}

        width, height = helper.get_width_height()
        closest = mathutils.Vector(helper.closes_pixel(mouse_uv[0], mouse_uv[1], width, height))
        move = closest - mouse_uv

        for uv in uvs:
            uv += move

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}

    def invoke(self, context, event):
        self.mouse_x = event.mouse_region_x
        self.mouse_y = event.mouse_region_y
        return self.execute(context)


def add_menu_item(self: bpy.types.Menu, context):
    self.layout.separator()
    self.layout.operator(OT_MoveUVToClosestPixel.bl_idname, icon="RESTRICT_SELECT_ON")


def add_pie_item(self: bpy.types.Menu, context):
    self.layout.menu_pie().operator(OT_MoveUVToClosestPixel.bl_idname, icon="RESTRICT_SELECT_ON")


def register():
    bpy.utils.register_class(OT_MoveUVToClosestPixel)

    bpy.types.IMAGE_MT_uvs_snap.append(add_menu_item)
    # bpy.types.IMAGE_MT_uvs_snap_pie.append(add_pie_item)


def unregister():
    bpy.utils.unregister_class(OT_MoveUVToClosestPixel)

    bpy.types.IMAGE_MT_uvs_snap.remove(add_menu_item)
    # bpy.types.IMAGE_MT_uvs_snap_pie.remove(add_pie_item)
