import os
import math

import bpy
import bmesh
from bpy.props import IntProperty, FloatProperty

from .utils import object_mode, edit_mode, select_objs, select_obj, delete_objs, delete_obj

IGLOO_OBJ_NAME = 'igloo'
IGLOO_TOP_OBJ_NAME = 'igloo_top'

class Igloo(bpy.types.Operator):

	bl_idname = "mesh.igloo_add"
	bl_label = "Igloo"
	bl_options = {'REGISTER', 'UNDO'}
	
	precision : IntProperty(
	   name = "Precision",
	   description = "The number of vertices of the igloo's sphere",
	   default = 32,
	   min = 16,
	   max = 256
	)

	radius : FloatProperty(
	   name = "Radius",
	   description = "The radius of the igloo",
	   default = 2,
	   min = 0.05,
	   max = 5.0
	)

	thickness_ratio : FloatProperty(
		name = "Thickness Ratio",
		description = "The thickness ratio of the igloo's walls",
		default = 0.15,
		min = 0.1,
		max = 0.9
	)
	
	bricks_gap : FloatProperty(
		name = "Bricks Gap",
		description = "Gap between two bricks",
		default = 0.03,
		min = 0.005,
		max = 0.1
	)

	nb_bricks_vertical : IntProperty(
		name = "Vertical Bricks Count",
		description = "The number of vertical bricks",
		default = 5,
		min = 3,
		max = 20
	)

	nb_bricks_radial : IntProperty(
		name = "Radial Bricks Count",
		description = "The number of radial bricks",
		default = 6,
		min = 2,
		max = 20
	)

	def execute(self, context):
		if 90 % self.nb_bricks_vertical != 0:
			self.report({"ERROR"}, "The number of vertical bricks must be a multiple of 90 (i.e., 2, 3, 5, 6, 9, 15, 18, etc…)")
			return {"CANCELLED"}

		if 360 % self.nb_bricks_radial != 0:
			self.report({"ERROR"}, "The number of radial bricks must be a multiple of 360 (i.e., 2, 3, 4, 5, 6, 8, 9, 12, 15, 18, 20, etc…)")
			return {"CANCELLED"}

		igloo_obj, igloo_top_obj = self.__create()
		
		return {'FINISHED'}

	def __create(self):
		# Create igloo demi sphere
		igloo_obj = self.__create_demi_sphere()
		print("Created igloo demi-sphere.")

		# Cut off and separate igloo top
		vertical_angle = int(90 / self.nb_bricks_vertical)
		igloo_obj, igloo_top_obj, igloo_top_radius = self.__separate_igloo_top(igloo_obj, vertical_angle)
		print("Separated igloo top from igloo.")

		# Divide the rest, vertically
		vertical_angles = []
		curr = 2 * vertical_angle
		while curr < 90:
			vertical_angles.append(curr)
			curr += vertical_angle
		self.__create_cones_and_cut_igloo(igloo_obj, vertical_angles)
		print("Cut igloo, vertically.")

		# Divide the rest, radially
		radial_angle = int(360 / self.nb_bricks_radial)
		radial_angles = []
		curr = 0
		while curr < 360:
			radial_angles.append(curr)
			curr += radial_angle
		self.__create_planes_and_cut_igloo(igloo_obj, igloo_top_radius, radial_angles)
		print("Cut igloo, along Z rotation axis.")

		# Make each block into its own object
		self.__separate_igloo_into_blocks(igloo_obj)

		return igloo_obj, igloo_top_obj

	def __create_demi_sphere(self):
		# Create sphere object
		bpy.ops.mesh.primitive_uv_sphere_add(segments=self.precision, ring_count=self.precision, radius=self.radius, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
		sphere_obj = bpy.context.active_object
		sphere_obj.name = IGLOO_OBJ_NAME

		# Create cube, to be used as a boolean difference object
		bpy.ops.mesh.primitive_cube_add(enter_editmode=False, align='WORLD', location=(0, 0, -1), scale=(1, 1, 1))
		difference_obj = bpy.context.active_object
		bpy.ops.transform.resize(value=(2*self.radius, 2*self.radius, 1), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, True, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)

		# Apply 'Boolean' modifier to the sphere
		select_obj(sphere_obj)
		bpy.ops.object.modifier_add(type='BOOLEAN')
		bpy.context.object.modifiers["Boolean"].object = difference_obj
		bpy.ops.object.modifier_apply(modifier="Boolean", report=True)

		# Delete the difference object
		delete_obj(difference_obj)

		# Remove the bottom face
		select_obj(sphere_obj, enter_editmode=True)
		bpy.ops.mesh.select_all(action='DESELECT')
		bm = bmesh.from_edit_mesh(sphere_obj.data)
		for face in bm.faces:
			is_bottom_face = all(vert.co[2] == 0 for vert in face.verts)
			if is_bottom_face:
				bm.faces.remove(face)
		bpy.ops.object.mode_set(mode='OBJECT')

		# Apply 'Solidify' modifier
		bpy.ops.object.modifier_add(type='SOLIDIFY')
		bpy.context.object.modifiers["Solidify"].thickness = self.thickness_ratio * self.radius
		bpy.ops.object.modifier_apply(modifier="Solidify", report=True)

		return sphere_obj

	def __create_cones_and_cut_igloo(self, igloo_obj, vertical_angles):
		object_mode()

		# Create all cones
		cone_objs = []
		for vertical_angle in vertical_angles:
			# Compute cone dimensions based on 'vertical_angle'
			depth = self.radius
			radius = depth * math.tan(math.radians(vertical_angle))

			# Create cone
			bpy.ops.mesh.primitive_cone_add(radius1=radius, depth=depth, vertices=self.precision, end_fill_type='NOTHING', enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
			cone_objs.append(bpy.context.active_object)
			bpy.ops.transform.rotate(value=math.radians(180), orient_axis='Y', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, True, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
			bpy.ops.transform.translate(value=(0, 0, depth/2), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, False, True), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)

		# Join all cone objects together
		select_objs(cone_objs)
		bpy.ops.object.join()
		difference_obj = bpy.context.active_object

		# Apply 'Solidify' modifier
		bpy.ops.object.modifier_add(type='SOLIDIFY')
		bpy.context.object.modifiers["Solidify"].thickness = self.bricks_gap/2
		bpy.ops.object.modifier_apply(modifier="Solidify", report=True)

		# Apply 'Boolean' modifier to the igloo
		select_obj(igloo_obj)
		bpy.ops.object.modifier_add(type='BOOLEAN')
		bpy.context.object.modifiers["Boolean"].object = difference_obj
		bpy.ops.object.modifier_apply(modifier="Boolean")

		# Delete the difference object
		delete_obj(difference_obj)

		return radius

	def __create_cone_and_cut_igloo(self, igloo_obj, vertical_angle):
		return self.__create_cones_and_cut_igloo(igloo_obj, [vertical_angle])

	def __separate_igloo_top(self, igloo_obj, vertical_angle):
		radius = self.__create_cone_and_cut_igloo(igloo_obj, vertical_angle)

		# Separate top from igloo
		select_obj(igloo_obj)
		edit_mode()
		bpy.ops.mesh.separate(type="LOOSE")
		object_mode()
		
		# Find which object is the top, using their z-coordinate (after applying their origin to their respective geometry)
		objs = [igloo_obj, bpy.data.objects[igloo_obj.name + ".001"]]
		for obj in objs:
			select_obj(obj)
			bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')

		objs = sorted(objs, key=lambda obj: obj.location[2])

		objs[0].name = IGLOO_OBJ_NAME
		objs[1].name = IGLOO_TOP_OBJ_NAME
		
		return objs[0], objs[1], radius

	def __create_planes_and_cut_igloo(self, igloo_obj, igloo_top_radius, z_rotations):
		object_mode()

		plane_objs = []
		for z_rotation in z_rotations:
			# Create cube, to be used as a boolean difference object
			bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
			plane_objs.append(bpy.context.active_object)
			edit_mode()
			bpy.ops.transform.translate(value=(0, 1, 0), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, True, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
			object_mode()
			bpy.ops.transform.resize(value=(self.bricks_gap/4, 2*self.radius, 2 * self.radius), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, False, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
			edit_mode()
			bpy.ops.transform.translate(value=(0, igloo_top_radius/2, 0), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, True, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
			object_mode()

			# Rotate the object along the Z-axis
			bpy.ops.transform.rotate(value=math.radians(z_rotation), orient_axis='Z', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, False, True), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)

		# Join all plane objects together
		select_objs(plane_objs)
		bpy.ops.object.join()
		difference_obj = bpy.context.active_object

		# Apply 'Boolean' modifier to the sphere
		select_obj(igloo_obj)
		bpy.ops.object.modifier_add(type='BOOLEAN')
		bpy.context.object.modifiers["Boolean"].object = difference_obj
		bpy.ops.object.modifier_apply(modifier="Boolean")

		# Remove the difference object
		delete_obj(difference_obj)

	def __separate_igloo_into_blocks(self, igloo_obj):
		select_obj(igloo_obj)
		edit_mode()
		bpy.ops.mesh.separate(type="LOOSE")
		object_mode()


def menu_func(self, context):
	self.layout.operator(Igloo.bl_idname)

def register():
	bpy.utils.register_class(Igloo)
	bpy.types.VIEW3D_MT_mesh_add.append(menu_func)

def unregister():
	bpy.utils.unregister_class(Igloo)
	bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)