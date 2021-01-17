import math
import numpy as np
import bpy
import bmesh
from mathutils import Vector

#################
### CONSTANTS ###
#################

IGLOO_RADIUS = 2.0 # in meters
IGLOO_THICKNESS = 0.15 * IGLOO_RADIUS
IGLOO_TOP_RADIUS = 0.25 * IGLOO_RADIUS
NB_BRICKS_HORIZONTAL = 18
assert(360 % NB_BRICKS_HORIZONTAL == 0)
NB_BRICKS_VERTICAL = 9
assert(90 % NB_BRICKS_VERTICAL == 0)
BRICKS_GAP = 0.03
PRECISION = 64

#############
### UTILS ###
#############

def object_mode():
    bpy.ops.object.mode_set(mode='OBJECT')

def edit_mode():
    bpy.ops.object.mode_set(mode='EDIT')

def select_objs(objs, enter_editmode=False):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objs:
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

    if enter_editmode:
        edit_mode()

def select_obj(obj, enter_editmode=False):
    return select_objs([obj], enter_editmode)

def delete_obj(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.object.delete(use_global=False)

###########################
### Create Demi Sphere ###
###########################

def create_demi_sphere(name, radius, thickness):
    # Create sphere object
    bpy.ops.mesh.primitive_uv_sphere_add(segments=PRECISION, ring_count=PRECISION, radius=radius, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    sphere_obj = bpy.context.active_object
    sphere_obj.name = name

    # Create cube, to be used as a boolean difference object
    bpy.ops.mesh.primitive_cube_add(enter_editmode=False, align='WORLD', location=(0, 0, -1), scale=(1, 1, 1))
    difference_obj = bpy.context.active_object
    bpy.ops.transform.resize(value=(2*IGLOO_RADIUS, 2*IGLOO_RADIUS, 1), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, True, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)

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
    bpy.context.object.modifiers["Solidify"].thickness = IGLOO_THICKNESS
    bpy.ops.object.modifier_apply(modifier="Solidify", report=True)

    return sphere_obj

igloo_obj = create_demi_sphere('igloo', IGLOO_RADIUS, IGLOO_THICKNESS)
print("Created igloo demi-sphere.")

################################
### DIVIDE IGLOO INTO BLOCKS ###
################################

###############################################
### DIVIDE VERTICALLY AND CUT OFF IGLOO TOP ###

def create_cones_and_cut_igloo(igloo_obj, vertical_angles):
    object_mode()

    # Create all cones
    cone_objs = []
    for vertical_angle in vertical_angles:
        # Compute cone dimensions based on 'vertical_angle'
        depth = IGLOO_RADIUS
        radius = depth * math.tan(math.radians(vertical_angle))

        # Create cone
        bpy.ops.mesh.primitive_cone_add(radius1=radius, depth=depth, vertices=PRECISION, end_fill_type='NOTHING', enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
        cone_objs.append(bpy.context.active_object)
        bpy.ops.transform.rotate(value=math.radians(180), orient_axis='Y', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, True, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
        bpy.ops.transform.translate(value=(0, 0, depth/2), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, False, True), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)

    # Join all cone objects together
    select_objs(cone_objs)
    bpy.ops.object.join()
    difference_obj = bpy.context.active_object

    # Apply 'Solidify' modifier
    bpy.ops.object.modifier_add(type='SOLIDIFY')
    bpy.context.object.modifiers["Solidify"].thickness = BRICKS_GAP/2
    bpy.ops.object.modifier_apply(modifier="Solidify", report=True)

    # Apply 'Boolean' modifier to the igloo
    select_obj(igloo_obj)
    bpy.ops.object.modifier_add(type='BOOLEAN')
    bpy.context.object.modifiers["Boolean"].object = difference_obj
    bpy.ops.object.modifier_apply(modifier="Boolean")

    # Delete the difference object
    delete_obj(difference_obj)

    return radius

def create_cone_and_cut_igloo(igloo_obj, vertical_angle):
    return create_cones_and_cut_igloo(igloo_obj, [vertical_angle])

angle = int(90 / NB_BRICKS_VERTICAL)

def separate_igloo_top(igloo_obj):
    radius = create_cone_and_cut_igloo(igloo_obj, angle)

    # Separate top from igloo
    select_obj(igloo_obj)
    edit_mode()
    bpy.ops.mesh.separate(type="LOOSE")
    object_mode()
    bpy.data.objects[igloo_obj.name + ".001"].name = "igloo_top"

    return igloo_obj, bpy.data.objects["igloo_top"], radius

# Cut off igloo top
igloo_obj, igloo_top_obj, igloo_top_radius = separate_igloo_top(igloo_obj)
print("Separated igloo top from igloo.")

# Divide the rest, vertically
angles = []
curr = 2 * angle
while curr < 90:
    angles.append(curr)
    curr += angle

create_cones_and_cut_igloo(igloo_obj, angles)

print("Cut igloo, vertically.")

###########################
### DIVIDE ALONG Z AXIS ###

def create_planes_and_cut_igloo(igloo_obj, igloo_top_radius, z_rotations):
    object_mode()

    plane_objs = []
    for z_rotation in z_rotations:
        # Create cube, to be used as a boolean difference object
        bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
        plane_objs.append(bpy.context.active_object)
        edit_mode()
        bpy.ops.transform.translate(value=(0, 1, 0), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, True, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
        object_mode()
        bpy.ops.transform.resize(value=(BRICKS_GAP/2, 2*IGLOO_RADIUS, 2 * IGLOO_RADIUS), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, False, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
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

angle = int(360 / NB_BRICKS_HORIZONTAL)
angles = []
curr = 0
while curr < 360:
    angles.append(curr)
    curr += angle

create_planes_and_cut_igloo(igloo_obj, igloo_top_radius, angles)

print("Cut igloo, along Z rotation axis.")

######################################
### MAKE BLOCK INTO ITS OWN OBJECT ###

select_obj(igloo_obj)
edit_mode()
bpy.ops.mesh.separate(type="LOOSE")
object_mode()

################################
### ISOLATE DIFFERENT BLOCKS ###
################################

unique_blocks_obj = []
unique_blocks_obj.append(igloo_top_obj)
unique_blocks_obj.append(igloo_obj)
for i in range(1, NB_BRICKS_VERTICAL-1):
    unique_blocks_obj.append(bpy.data.objects["igloo.{:03d}".format(i)])
