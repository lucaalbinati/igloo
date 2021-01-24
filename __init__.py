import os
import bpy

bl_info = {
	"name": "Igloo",
	"author": "Luca Albinati",
	"version": (1, 0, 0),
	"blender": (2, 91, 0),
	"location": "View3D > Add > Mesh > Igloo",
	"description": "Adds an Igloo"
}

from . import add_igloo
from . import utils

from importlib import reload
reload(add_igloo)
reload(utils)

def register():
	add_igloo.register()

def unregister():
	add_igloo.unregister()

if __name__ == "__main__":
	register()