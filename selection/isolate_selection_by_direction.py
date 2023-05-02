import bpy
import math


class OT_IsolateSelectionByDirection(bpy.types.Operator):
    bl_idname = "uv.isolate_selection_by_direction"
    bl_label = "Isolate by Direction"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Use a vector as normal for a projection plane. From all selected faces isolate those who are facing the plane with a defined angle or narrower"

    vector: bpy.props.FloatVectorProperty(name="Direction", description="The direction of the projection plane normal", default=(0, 0, 0))
    max_angle: bpy.props.FloatProperty(name="Max Angle", description="The maximum angle a face normal is valid", default=math.pi/4, soft_min=0.0, unit="ROTATION")

    def execute(self, context):
        bpy.ops.object.mode_set(mode='OBJECT')
        v = self.vector

        for selected_object in context.selected_objects:
            if not selected_object.type == "MESH":
                continue
            selected_polygons = []
            polygons: bpy.types.MeshPolygons = selected_object.data.polygons
            for polygon in polygons:
                if polygon.select:
                    n = polygon.normal
                    angle = n.angle(v, 0)
                    if angle <= self.max_angle:
                        selected_polygons.append(polygon)
                    polygon.select = False

            vertices: bpy.types.MeshVertices = selected_object.data.vertices
            for vertex in vertices:
                vertex.select = False
            edges: bpy.types.MeshVertices = selected_object.data.edges
            for edge in edges:
                edge.select = False

            for polygon in selected_polygons:
                polygon.select = True

        bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}


class VIEW3D_MT_IsolateSelectionByDirection(bpy.types.Menu):
    bl_idname = "VIEW3D_MT_isolate_selection_by_direction"
    bl_label = "Isolate by Direction"

    def draw(self, context):

        x = self.layout.operator(OT_IsolateSelectionByDirection.bl_idname, text="+ X")
        if x:
            x.vector = (1, 0, 0)
        y = self.layout.operator(OT_IsolateSelectionByDirection.bl_idname, text="+ Y")
        if y:
            y.vector = (0, 1, 0)
        z = self.layout.operator(OT_IsolateSelectionByDirection.bl_idname, text="+ Z")
        if z:
            z.vector = (0, 0, 1)

        x = self.layout.operator(OT_IsolateSelectionByDirection.bl_idname, text="- X")
        if x:
            x.vector = (-1, 0, 0)
        y = self.layout.operator(OT_IsolateSelectionByDirection.bl_idname, text="- Y")
        if y:
            y.vector = (0, -1, 0)
        z = self.layout.operator(OT_IsolateSelectionByDirection.bl_idname, text="- Z")
        if z:
            z.vector = (0, 0, -1)

        self.layout.separator()
        self.layout.operator(OT_IsolateSelectionByDirection.bl_idname, text="Custom")


def add_menu_item(self: bpy.types.Menu, context):
    self.layout.separator()
    self.layout.menu(VIEW3D_MT_IsolateSelectionByDirection.bl_idname)


def register():
    bpy.utils.register_class(VIEW3D_MT_IsolateSelectionByDirection)
    bpy.utils.register_class(OT_IsolateSelectionByDirection)

    bpy.types.VIEW3D_MT_edit_mesh_context_menu.append(add_menu_item)
    bpy.types.VIEW3D_MT_edit_mesh_faces.append(add_menu_item)
    bpy.types.VIEW3D_MT_edit_mesh_edges.append(add_menu_item)
    bpy.types.VIEW3D_MT_edit_mesh_vertices.append(add_menu_item)


def unregister():
    bpy.utils.unregister_class(VIEW3D_MT_IsolateSelectionByDirection)
    bpy.utils.unregister_class(OT_IsolateSelectionByDirection)

    bpy.types.VIEW3D_MT_edit_mesh_context_menu.remove(add_menu_item)
    bpy.types.VIEW3D_MT_edit_mesh_faces.remove(add_menu_item)
    bpy.types.VIEW3D_MT_edit_mesh_edges.remove(add_menu_item)
    bpy.types.VIEW3D_MT_edit_mesh_vertices.remove(add_menu_item)


if __name__ == "__main__":
    register()
