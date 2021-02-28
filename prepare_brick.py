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
				potential_example_faces = [f for f, n in faces_normal.items() if self.__same_direction(f, n)]
				median_normal_z = np.median([faces_normal[f][2] for f in potential_example_faces])
				potential_example_faces = sorted(potential_example_faces, key=lambda f: abs(faces_normal[f][2] - median_normal_z))

				if len(potential_example_faces) == 0:
					print("ERROR: no faces found that match the 'same direction' condition")
					return {'FINISHED'}

				example_face = potential_example_faces[0]
				example_normal_z = faces_normal[example_face][2]

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

			bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')

		return {'FINISHED'}

	def __same_direction(self, face, normal):
		origin_to_face_vector = face.verts[0].co

		if np.isclose(normal[2], -1, rtol=0.0001, atol=0.0001):
			# Some errors occurred for the bricks at the bottom, such that no faces were selected
			# This if-statement should take care of that
			return True

		return np.sign(origin_to_face_vector[0]) == np.sign(normal[0]) and np.sign(origin_to_face_vector[1]) == np.sign(normal[1])

def menu_func(self, context):
	self.layout.operator(PrepareBrick.bl_idname)

def register():
	bpy.utils.register_class(PrepareBrick)
	bpy.types.VIEW3D_MT_object.append(menu_func)

def unregister():
	bpy.utils.unregister_class(PrepareBrick)
	bpy.types.VIEW3D_MT_object.remove(menu_func)
