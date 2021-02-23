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
from . import prepare_brick
from . import utils

from importlib import reload
reload(add_igloo)
reload(prepare_brick)
reload(utils)

def register():
	add_igloo.register()
	prepare_brick.register()

def unregister():
	add_igloo.unregister()
	prepare_brick.unregister()

if __name__ == "__main__":
	register()
	