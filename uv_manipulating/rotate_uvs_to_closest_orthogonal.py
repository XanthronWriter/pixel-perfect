import bpy
import bmesh
import mathutils
import math
import gpu
from gpu_extras.batch import batch_for_shader
from sys import float_info
from .. import helper


class OT_RotateUVsToClosestOrthogonal(bpy.types.Operator):
    bl_idname = "uv.rotate_uv_to_closest_orthogonal"
    bl_label = "Groupe to orthogonal Line"
    bl_description = "Select two vertex and rotate them so they are parallel to either the x ore the y axises"
    bl_options = {"REGISTER", "UNDO"}

    def __init__(self) -> None:
        self.pressed_left = False
        self.uvs = []
        self.dirs = []
        self.edges = []
        super().__init__()

    def end(self, context):
        if not self._handler == None:
            bpy.types.SpaceImageEditor.draw_handler_remove(self._handler, 'WINDOW')
        context.area.tag_redraw()
        pass

    def get_uvs(self, context):
        self.uvs.clear()
        self.dirs.clear()
        self.edges.clear()
        for selected_object in context.selected_objects:
            if not selected_object.type == "MESH":
                continue
            mesh: bpy.types.Mesh = selected_object.data
            bm = bmesh.from_edit_mesh(mesh)
            uv_layer = bm.loops.layers.uv.verify()

            for face in bm.faces:
                uv1 = face.loops[-2][uv_layer]
                uv2 = face.loops[-1][uv_layer]
                for loop in face.loops:
                    uv3 = loop[uv_layer]
                    if uv2.select:
                        self.uvs.append(mathutils.Vector(uv2.uv))
                        d = []
                        if uv1.select:
                            self.edges.append(mathutils.Vector(uv1.uv))
                            self.edges.append(mathutils.Vector(uv2.uv))
                            d.append(mathutils.Vector(uv1.uv))
                        if uv3.select:
                            d.append(mathutils.Vector(uv3.uv))
                        self.dirs.append(d)
                    uv1 = uv2
                    uv2 = uv3

    def get_move(self, context, event):
        mouse = mathutils.Vector(context.region.view2d.region_to_view(event.mouse_region_x, event.mouse_region_y))
        distance = float_info.max
        closest_uv = mathutils.Vector((0, 0))
        direction = mathutils.Vector((0, 0))
        for i, uv in enumerate(self.uvs):
            d = self.dirs[i]
            if len(d) > 0:
                new_distance = (mouse-uv).length_squared
                if new_distance < distance:
                    distance = new_distance
                    closest_uv = uv
                    uv1 = d[0]
                    d1 = (mouse - uv1).project(uv1 - uv)
                    if len(d) == 1:
                        direction = uv1 - uv
                    else:
                        uv3 = d[1]
                        d3 = (mouse - uv3).project(uv3 - uv)
                        if d1 < d3:
                            direction = d1
                        else:
                            direction = d3
        self.closest_uv = closest_uv
        self.direction = direction.normalized()

    def get_angle(self, context, event):
        mouse_dir = self.closest_uv - mathutils.Vector(context.region.view2d.region_to_view(event.mouse_region_x, event.mouse_region_y))
        axis: mathutils.Vector
        if abs(mouse_dir[0]) > abs(mouse_dir[1]):
            axis = mathutils.Vector((mouse_dir[0], 0))
        else:
            axis = mathutils.Vector((0, mouse_dir[1]))

        self.angle = -axis.angle_signed(self.direction, 0)

    def invoke(self, context, event):
        self.get_uvs(context)
        self.get_move(context, event)
        self.get_angle(context, event)
        context.window_manager.modal_handler_add(self)

        shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')

        zoom_multiplier = 1
        image_editor = helper.get_image_editor()
        if image_editor.image:
            zoom_multiplier = image_editor.image_size[0] * 250
            print(zoom_multiplier)
        zoom = context.space_data.zoom[0] * zoom_multiplier

        def draw():
            shader.uniform_float("color", (1, 1, 1, 1))
            rotation = mathutils.Matrix.Rotation(self.angle, 3, 'Z').to_2x2()

            edges = []
            for edge in self.edges:
                edges.append(((edge - self.closest_uv) @ rotation) + self.closest_uv)
            batch_for_shader(shader, 'LINES', {"pos": edges}).draw(shader)

            uvs = []
            for uv in self.uvs:
                uvs.append(((uv - self.closest_uv) @ rotation) + self.closest_uv)
            batch_for_shader(shader, 'POINTS', {"pos": uvs}).draw(shader)

            r = 0.025 / zoom
            circle = []
            for i in range(10):
                a = i/10 * 2 * math.pi
                circle.append(mathutils.Vector((math.sin(a) * r, math.cos(a) * r)) + self.closest_uv)
            batch_for_shader(shader, 'LINE_LOOP', {"pos": circle}).draw(shader)

            if abs(self.angle) > 0:
                r = 0.1 / zoom
                p = self.direction * r
                angle = [self.closest_uv]
                for i in range(10):
                    rotation = mathutils.Matrix.Rotation(self.angle * (i) / 9 + math.pi, 3, 'Z').to_2x2()
                    angle.append((p @ rotation) + self.closest_uv)
                batch_for_shader(shader, 'LINE_LOOP', {"pos": angle}).draw(shader)

            pass

        self._handler = bpy.types.SpaceImageEditor.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')

        context.area.tag_redraw()
        return {'RUNNING_MODAL'}

    def execute(self, context):
        rotation = mathutils.Matrix.Rotation(self.angle, 3, 'Z').to_2x2()

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
                        uv.uv = ((uv.uv - self.closest_uv) @ rotation) + self.closest_uv

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        return {"FINISHED"}

    def modal(self, context, event):
        if event.type == "MOUSEMOVE":
            if not self.pressed_left:
                self.get_move(context, event)
            self.get_angle(context, event)
            context.area.tag_redraw()
        elif event.type == "LEFTMOUSE":
            if self.pressed_left:
                self.execute(context)
                self.end(context)
                return {'FINISHED'}
            else:
                self.pressed_left = True
        elif event.type in {"RIGHTMOUSE", "ESC"}:
            self.end(context)
            return {"CANCELLED"}
        return {'RUNNING_MODAL'}


def register():
    bpy.utils.register_class(OT_RotateUVsToClosestOrthogonal)


def unregister():
    bpy.utils.unregister_class(OT_RotateUVsToClosestOrthogonal)
