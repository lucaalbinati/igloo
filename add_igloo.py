import os
import math
import numpy as np

import bpy
import bmesh
from bpy.props import BoolProperty, IntProperty, FloatProperty

from .utils import object_mode, edit_mode, select_objs, select_obj, delete_objs, delete_obj

IGLOO_OBJ_NAME = 'igloo'
IGLOO_TOP_OBJ_NAME = 'igloo_top'

HIGH_PRECISION = 128
LOW_PRECISION = 32

class Igloo(bpy.types.Operator):

	bl_idname = "mesh.igloo_add"
	bl_label = "Igloo"
	bl_options = {'REGISTER', 'UNDO'}
	
	high_precision : BoolProperty(
		name = "High Precision",
		description = "Whether to use high or low precision",
		default = False
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
		igloo_obj = self.__create_igloo_base()
		print("Created igloo demi-sphere.")

		# Divide the igloo vertically
		vertical_angle = int(90 / self.nb_bricks_vertical)
		vertical_angles = []
		curr = vertical_angle
		while curr < 90:
			vertical_angles.append(curr)
			curr += vertical_angle
		igloo_top_radius = self.__create_cones_and_cut_igloo(igloo_obj, vertical_angles)
		print("Cut igloo, vertically.")

		# Separate the top from the rest
		igloo_obj, igloo_top_obj = self.__separate_igloo_top(igloo_obj)
		print("Separate igloo top from the rest.")

		# Fix bottom face bug
		self.__fix_negative_bug(igloo_obj)

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

	def __create_igloo_base(self):
		def create_demi_sphere(radius):
			# Create sphere object
			precision = HIGH_PRECISION if self.high_precision else LOW_PRECISION
			bpy.ops.mesh.primitive_uv_sphere_add(segments=precision, ring_count=precision, radius=radius, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
			sphere_obj = bpy.context.active_object

			# Remove bottom half
			edit_mode()
			bpy.ops.mesh.select_all(action='DESELECT')
			bm = bmesh.from_edit_mesh(sphere_obj.data)
			for face in bm.faces:
				if all(vert.co[2] <= 0 for vert in face.verts):
					face.select = True
			bpy.ops.mesh.delete(type='FACE')
			object_mode()

			return sphere_obj

		sphere_obj = create_demi_sphere(radius=self.radius)

		inner_radius = (1 - self.thickness_ratio) * self.radius
		inner_sphere_obj = create_demi_sphere(radius=inner_radius)

		# Join both demi spheres
		select_objs([inner_sphere_obj, sphere_obj])
		bpy.ops.object.join()
		sphere_obj.name = IGLOO_OBJ_NAME

		# Merge bottom edges
		# For some reason, creating a face from ALL the edges fills the whole bottom face, so instead we make a face between all the edges except two facing edges, which we then do separately
		edit_mode()
		bpy.ops.mesh.select_all(action='DESELECT')
		bm = bmesh.from_edit_mesh(sphere_obj.data)
		special_edges = []
		for edge in bm.edges:			
			if all(np.isclose(vert.co[2], 0, atol=0.01, rtol=0.01) for vert in edge.verts):
				if any(v.co[0] == 0 for v in edge.verts) and any(v.co[0] > 0 for v in edge.verts):
					special_edges.append(edge)
					continue
				edge.select = True
		bpy.ops.mesh.edge_face_add()
		bpy.ops.mesh.select_all(action='DESELECT')
		for edge in special_edges:
			edge.select = True
		bpy.ops.mesh.edge_face_add()
		object_mode()

		return sphere_obj

	def __create_cones_and_cut_igloo(self, igloo_obj, vertical_angles):
		object_mode()

		# Create all cones
		vertical_angles = sorted(vertical_angles, reverse=True) # such that the variable 'radius' holds the radius of the top part (i.e. the last part)
		cone_objs = []
		for vertical_angle in vertical_angles:
			# Compute cone dimensions based on 'vertical_angle'
			depth = self.radius
			radius = depth * math.tan(math.radians(vertical_angle))
			print("{}: {}".format(vertical_angle, radius))

			# Create cone
			precision = HIGH_PRECISION if self.high_precision else LOW_PRECISION
			bpy.ops.mesh.primitive_cone_add(radius1=radius, depth=depth, vertices=precision, end_fill_type='NOTHING', enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
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
		bpy.context.object.modifiers["Boolean"].solver = 'FAST'
		bpy.ops.object.modifier_apply(modifier="Boolean")

		# Delete the difference object
		delete_obj(difference_obj)

		return radius

	def __separate_igloo_top(self, igloo_obj):
		# Separate igloo
		self.__separate_igloo_into_blocks(igloo_obj)

		# Find the 'igloo' object with the highest z-coordinate center of geometry
		objs = [obj for obj in bpy.data.objects if obj.name.startswith("igloo")]
		for obj in objs:
			bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')
		igloo_top_obj = sorted(objs, key=lambda o: o.location[2], reverse=True)[0]
		igloo_top_obj.name = IGLOO_TOP_OBJ_NAME

		# Find and merge the other 'igloo' objects
		select_objs([obj for obj in objs if obj != igloo_top_obj])
		bpy.ops.object.join()
		igloo_obj = bpy.context.active_object
		igloo_obj.name = IGLOO_OBJ_NAME

		# Reset 'igloo_obj's origin to the global origin
		bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')

		return igloo_obj, igloo_top_obj

	def __fix_negative_bug(self, igloo_obj):
		# Sometimes, depending on the precision, a negative z-coordinate face is created, which we remove here
		edit_mode()
		bpy.ops.mesh.select_all(action='DESELECT')
		bm = bmesh.from_edit_mesh(igloo_obj.data)
		for face in bm.faces:
			for vert in face.verts:
				if vert.co[2] < 0 and not np.isclose(vert.co[2], 0, rtol=0.0001, atol=0.0001):
					face.select = True
		bpy.ops.mesh.delete(type='FACE')
		object_mode()

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
		bpy.context.object.modifiers["Boolean"].solver = 'FAST'
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
