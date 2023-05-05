import bpy
from . import isolate_selection_by_direction


def register():
    isolate_selection_by_direction.register()


def unregister():
    isolate_selection_by_direction.unregister()
