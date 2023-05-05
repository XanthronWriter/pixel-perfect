import bpy
import bmesh
import mathutils
import math
import gpu
from gpu_extras.batch import batch_for_shader
from sys import float_info
from .. import helper


class OT_MirrorUVAroundVertex(bpy.types.Operator):
    bl_idname = "uv.mirror_uvs_around_vertex"
    bl_label = "Mirror around Vertex"
    bl_description = "Select a vertex and mirror the Selection around it."
    bl_options = {"REGISTER", "UNDO"}

    def __init__(self) -> None:
        self.uvs = []
        self.edges = []
        self.pressed_left = False
        super().__init__()

    def end(self, context):
        if not self._handler == None:
            bpy.types.SpaceImageEditor.draw_handler_remove(self._handler, 'WINDOW')
        context.area.tag_redraw()
        pass

    def get_uvs(self, context):
        self.uvs.clear()
        self.edges.clear()
        for selected_object in context.selected_objects:
            if not selected_object.type == "MESH":
                continue
            mesh: bpy.types.Mesh = selected_object.data
            bm = bmesh.from_edit_mesh(mesh)
            uv_layer = bm.loops.layers.uv.verify()

            for face in bm.faces:
                old_uv = face.loops[-1][uv_layer]
                for loop in face.loops:
                    uv = loop[uv_layer]
                    if uv.select:
                        self.uvs.append(mathutils.Vector(uv.uv))
                        if old_uv.select:
                            self.edges.append(mathutils.Vector(old_uv.uv))
                            self.edges.append(mathutils.Vector(uv.uv))
                    old_uv = uv

    def get_selected(self, context, event):
        mouse = mathutils.Vector(context.region.view2d.region_to_view(event.mouse_region_x, event.mouse_region_y))
        distance = float_info.max
        selected_uv = self.uvs[0]
        for uv in self.uvs:
            new_distance = (mouse-uv).length_squared
            if new_distance < distance:
                distance = new_distance
                selected_uv = uv

        self.selected_uv = selected_uv

    def get_axis(self, context, event):
        mouse = mathutils.Vector(context.region.view2d.region_to_view(event.mouse_region_x, event.mouse_region_y)) - self.selected_uv

        axis = mathutils.Vector((1, -1))
        if abs(mouse[0]) < abs(mouse[1]):
            axis = mathutils.Vector((-1, 1))

        self.axis = axis

    def invoke(self, context, event):
        self.get_uvs(context)
        self.get_selected(context, event)
        self.get_axis(context, event)
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

            edges = []
            for edge in self.edges:
                edges.append((edge - self.selected_uv) * self.axis + self.selected_uv)
            shader.uniform_float("color", (1, 1, 1, 0.5))
            if self.axis[0] > 0:
                edges.append(self.selected_uv + mathutils.Vector((1000, 0)))
                edges.append(self.selected_uv + mathutils.Vector((-1000, 0)))
            else:
                edges.append(self.selected_uv + mathutils.Vector((0, 1000)))
                edges.append(self.selected_uv + mathutils.Vector((0, -1000)))

            batch_for_shader(shader, 'LINES', {"pos": edges}).draw(shader)

            uvs = []
            for uv in self.uvs:
                uvs.append((uv - self.selected_uv) * self.axis + self.selected_uv)
            batch_for_shader(shader, 'POINTS', {"pos": uvs}).draw(shader)

            r = 0.025 / zoom
            circle = []
            for i in range(10):
                a = i/10 * 2 * math.pi
                circle.append(mathutils.Vector((math.sin(a) * r, math.cos(a) * r)) + self.selected_uv)
            batch_for_shader(shader, 'LINE_LOOP', {"pos": circle}).draw(shader)

            pass

        self._handler = bpy.types.SpaceImageEditor.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')
        context.area.tag_redraw()
        return {'RUNNING_MODAL'}

    def modal(self, context, event):

        if event.type == "MOUSEMOVE":
            if self.pressed_left == False:
                self.get_selected(context, event)
            self.get_axis(context, event)
            context.area.tag_redraw()
        elif event.type == "LEFTMOUSE":
            if self.pressed_left == True:
                self.execute(context)
                self.end(context)
                return {'FINISHED'}
            else:
                self.pressed_left = True
        elif event.type in {"RIGHTMOUSE", "ESC"}:
            self.end(context)
            return {"CANCELLED"}
        return {'RUNNING_MODAL'}

    def execute(self, context):
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
                        uv.uv = (uv.uv - self.selected_uv) * self. axis + self.selected_uv

        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        return {"FINISHED"}


def register():
    bpy.utils.register_class(OT_MirrorUVAroundVertex)


def unregister():
    bpy.utils.unregister_class(OT_MirrorUVAroundVertex)
