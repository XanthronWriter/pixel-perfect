# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import bpy
import sys
import importlib

bl_info = {
    "name": "Pixel Perfect",
    "author": "Xanthron",
    "description": "Generate UVs for 3D Pixelart",
    "blender": (3, 1, 2),
    "version": (1, 0, 1),
    "location": "",
    "warning": "",
    "category": "UV"
}

module_names = ["unwrap_pixel_perfect", "export_pixel_uv_layout"]


def register():
    for module_name in module_names:
        globals()[module_name].register()


def unregister():
    for module_name in module_names:
        globals()[module_name].unregister()


if __name__ == "__main__":
    for module_name in module_names:
        module = bpy.data.texts[f"{module_name}.py"].as_module()
        globals()[module_name] = module
    register()
else:
    for module_name in module_names:
        module = importlib.import_module(f"{__name__}.{module_name}")
        globals()[module_name] = module
