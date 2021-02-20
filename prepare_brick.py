import numpy as np

import bpy
import bmesh
from bpy.props import FloatProperty

from .utils import object_mode, edit_mode, select_objs, select_obj, delete_objs, delete_obj

class PrepareBrick(bpy.types.Operator):

	bl_idname = "operator.prepare_brick"
	bl_label = "Prepare Brick"
	bl_description = "Prepare an igloo's brick, by solidifying it and opening a side"
	bl_options = {'REGISTER', 'UNDO'}

	thickness : FloatProperty(
		name = "Thickness",
		description = "The thickness of the brick's wall",
		default = 0.02,
		min = 0.005,
		max = 0.04
	)

	def execute(self, context):
		
		objects = bpy.context.selected_objects

		for obj in objects:
			select_obj(obj)

			bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')

			origin_to_object_vector = bpy.context.object.location

			edit_mode()

			bm = bmesh.from_edit_mesh(bpy.context.object.data)
			if 'top' in obj.name:
				# select the top faces, with a positive z-normal
				for face in bm.faces:
					if face.normal[2] >= 0:
						face.select = True
			else:
				faces_normal = dict()

				# get all the faces with a negative z-normal
				for face in bm.faces:
					if face.normal[2] < 0:
						faces_normal[face] = face.normal

				bpy.ops.mesh.select_all(action='DESELECT')

				# select one face from the "negative z-normal" faces that points in the same xy-direction as the "origin-to-face" vector
				example_face = next(f for f, n in faces_normal.items() if self.__same_direction(f, n))
				example_normal_z = faces_normal[example_face][2]

				if example_face == None:
					print("ERROR: no faces found that match the 'same direction' condition")
					return {'FINISHED'}

				# given this "example" face, find the other "negative z-normal" faces that have a very similar normal vector
				for face, normal in faces_normal.items():
					if np.isclose(normal[2], example_normal_z, rtol=0.01, atol=0.01):
						face.select = True

			bpy.ops.mesh.delete(type='FACE')

			object_mode()

			bpy.ops.object.modifier_add(type='SOLIDIFY')
			bpy.context.object.modifiers["Solidify"].offset = 1
			bpy.context.object.modifiers["Solidify"].thickness = self.thickness
			bpy.ops.object.modifier_apply(modifier="Solidify")

		return {'FINISHED'}

	def __same_direction(self, face, normal):
		origin_to_face_vector = face.verts[0].co

		return np.sign(origin_to_face_vector[0]) == np.sign(normal[0]) and np.sign(origin_to_face_vector[1]) == np.sign(normal[1])

def register():
	bpy.utils.register_class(PrepareBrick)

def unregister():
	bpy.utils.unregister_class(PrepareBrick)