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
NB_BRICKS_VERTICAL = 5
assert(90 % NB_BRICKS_VERTICAL == 0)
BRICKS_GAP = 0.1
PRECISION = 64

#############
### UTILS ###
#############

def select_obj(obj, enter_editmode=False):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    if enter_editmode:
        bpy.ops.object.mode_set(mode='EDIT')

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

    # Create cube used as boolean difference object
    bpy.ops.mesh.primitive_cube_add(enter_editmode=False, align='WORLD', location=(0, 0, -1), scale=(1, 1, 1))
    difference_obj = bpy.context.active_object
    bpy.ops.transform.resize(value=(2*IGLOO_RADIUS, 2*IGLOO_RADIUS, 1), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, True, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)

    # Apply 'Boolean' modifier to the sphere
    select_obj(sphere_obj)
    bpy.ops.object.modifier_add(type='BOOLEAN')
    bpy.context.object.modifiers["Boolean"].object = difference_obj
    bpy.ops.object.modifier_apply(modifier="Boolean", report=True)

    # Remove the difference object
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

    # for vert in bm.verts:
    #     if np.isclose(vert.co[2], 0, atol=1e-05):
    #         vert.select = True
    # bpy.ops.object.mode_set(mode='OBJECT')
    # bpy.ops.object.mode_set(mode='EDIT')
    # bpy.ops.mesh.delete(type='ONLY_FACE')
    # bpy.ops.object.mode_set(mode='OBJECT')

    # Apply 'Solidify' modifier
    bpy.ops.object.modifier_add(type='SOLIDIFY')
    bpy.context.object.modifiers["Solidify"].thickness = IGLOO_THICKNESS
    bpy.ops.object.modifier_apply(modifier="Solidify", report=True)

    return sphere_obj

igloo_obj = create_demi_sphere('igloo', IGLOO_RADIUS, IGLOO_THICKNESS)

# #######################################
# ### JOIN BOTH DEMI SPHERES INTO ONE ###
# #######################################

# # Join inner and outer sphere objects to form the igloo
# bpy.ops.object.select_all(action='DESELECT')
# outer_sphere_obj.select_set(True)
# inner_sphere_obj.select_set(True)
# bpy.ops.object.join()
# igloo_obj = bpy.context.object
# igloo_obj.name = 'igloo'

# # Connect them at the bottom
# bpy.ops.object.mode_set(mode='EDIT')
# bpy.ops.mesh.select_all(action='DESELECT')
# bm = bmesh.from_edit_mesh(igloo_obj.data)

# outer_bottom_edges ,inner_bottom_edges = [], []
# for edge in bm.edges:
#     is_bottom_edge = all([np.isclose(vert.co[2], 0, atol=1e-05) for vert in edge.verts])
    
#     if is_bottom_edge:
#         x, y = edge.verts[0].co[0], edge.verts[0].co[1]
#         dist = math.sqrt(x**2 + y**2)
#         if np.isclose(dist, IGLOO_RADIUS):
#             outer_bottom_edges.append(edge)
#         elif np.isclose(dist, IGLOO_RADIUS - IGLOO_THICKNESS):
#             inner_bottom_edges.append(edge)
        
# def eval_edge(edge):
#     # the y-coord is 0+ because otherwise some vertices get sorted at the end while their respective other at the beginning, resulting in weird faces
#     ref_vector=(1, 0.00001, 0)
#     val_1 = np.dot(ref_vector, edge.verts[0].co[:])
#     val_2 = np.dot(ref_vector, edge.verts[1].co[:])
#     return min(val_1, val_2)

# outer_bottom_edges = sorted(outer_bottom_edges, key=eval_edge)
# inner_bottom_edges = sorted(inner_bottom_edges, key=eval_edge)

# for outer_edge, inner_edge in zip(outer_bottom_edges, inner_bottom_edges):
#     bpy.ops.mesh.select_all(action='DESELECT')
#     outer_edge.select = True
#     inner_edge.select = True
#     bpy.ops.mesh.edge_face_add()

# bpy.ops.object.mode_set(mode='OBJECT')

###############################################
### LOOP CUT BEFORE SUBDIVIDING BOTTOM FACE ###
###############################################

# def loop_cut_and_scale(igloo_obj, scalar):
#     bpy.ops.object.mode_set(mode='OBJECT')
#     bpy.ops.object.select_all(action='DESELECT')
#     igloo_obj.select_set(True)
#     bpy.ops.object.mode_set(mode='EDIT')
    
#     win      = bpy.context.window
#     scr      = win.screen
#     areas3d  = [area for area in scr.areas if area.type == 'VIEW_3D']
#     region   = [region for region in areas3d[0].regions if region.type == 'WINDOW']
#     override = {'window':win,
#                 'screen':scr,
#                 'area'  :areas3d[0],
#                 'region':region[0],
#                 'scene' :bpy.context.scene,
#                 }
    
#     bpy.ops.mesh.loopcut_slide(override, MESH_OT_loopcut={"number_cuts":1, "smoothness":0, "falloff":'INVERSE_SQUARE', "object_index":0, "edge_index":8201, "mesh_select_mode_init":(False, False, True)}, TRANSFORM_OT_edge_slide={"value":0, "single_side":False, "use_even":False, "flipped":False, "use_clamp":True, "mirror":True, "snap":False, "snap_target":'CLOSEST', "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), "correct_uv":True, "release_confirm":True, "use_accurate":False})

#     bm = bmesh.from_edit_mesh(igloo_obj.data)
#     for vert in bm.verts:
#         if vert.select:
#             vert.co[0] *= scalar
#             vert.co[1] *= scalar
        
#     bpy.ops.object.mode_set(mode='OBJECT')


# length_outer = IGLOO_RADIUS
# length_inner = IGLOO_RADIUS - IGLOO_THICKNESS
# length_middle = (length_outer + length_inner) / 2

# inner_scalar = length_inner / length_middle
# #loop_cut_and_scale(igloo_obj, scalar=inner_scalar)
# outer_scalar = length_outer / length_middle
# #loop_cut_and_scale(igloo_obj, scalar=outer_scalar)

# # Subdivide
# #bpy.ops.object.modifier_add(type='SUBSURF')
# #bpy.context.object.modifiers["Subdivision"].levels = 2
# #bpy.context.object.modifiers["Subdivision"].render_levels = 5
# #bpy.ops.object.modifier_apply(modifier="Subdivision")


################################
### DIVIDE IGLOO INTO BLOCKS ###
################################

###############################################
### DIVIDE VERTICALLY AND CUT OFF IGLOO TOP ###

def create_cone_and_cut_igloo(igloo_obj, vertical_angle):
    bpy.ops.object.mode_set(mode='OBJECT')

    depth = IGLOO_RADIUS
    radius = depth * math.tan(math.radians(vertical_angle))

    bpy.ops.mesh.primitive_cone_add(radius1=radius, depth=depth, vertices=PRECISION, end_fill_type='NOTHING', enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    difference_obj = bpy.context.active_object
    bpy.ops.transform.rotate(value=math.radians(180), orient_axis='Y', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, True, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
    bpy.ops.transform.translate(value=(0, 0, depth/2), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, False, True), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)

    bpy.ops.object.modifier_add(type='SOLIDIFY')
    bpy.context.object.modifiers["Solidify"].thickness = IGLOO_THICKNESS/2
    bpy.ops.object.modifier_apply(modifier="Solidify", report=True)

    select_obj(igloo_obj)
    bpy.ops.object.modifier_add(type='BOOLEAN')
    bpy.context.object.modifiers["Boolean"].object = difference_obj
    bpy.ops.object.modifier_apply(modifier="Boolean")

    delete_obj(difference_obj)

angle = int(90 / NB_BRICKS_VERTICAL)

def separate_igloo_top(igloo_obj):
    create_cone_and_cut_igloo(igloo_obj, angle)

    # Separate top from igloo
    select_obj(igloo_obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.separate(type="LOOSE")
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.data.objects[igloo_obj.name + ".001"].name = "igloo_top"

    return igloo_obj, bpy.data.objects["igloo_top"]

# Cut off igloo top
igloo_obj, igloo_top_obj = separate_igloo_top(igloo_obj)

# Divide the rest, vertically
angles = []
curr = 2 * angle
while curr < 90:
    angles.append(curr)
    curr += angle

for angle in angles:
    create_cone_and_cut_igloo(igloo_obj, angle)

###########################
### DIVIDE ALONG Z AXIS ###

def create_plane_and_cut_igloo(igloo_obj, z_rotation):
    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    difference_obj = bpy.context.active_object
    bpy.ops.transform.resize(value=(BRICKS_GAP/2, 2*IGLOO_RADIUS, 2 * IGLOO_RADIUS), orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, False, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
    bpy.ops.transform.rotate(value=math.radians(z_rotation), orient_axis='Z', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(False, False, True), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)

    select_obj(igloo_obj)
    bpy.ops.object.modifier_add(type='BOOLEAN')
    bpy.context.object.modifiers["Boolean"].object = difference_obj
    bpy.ops.object.modifier_apply(modifier="Boolean")

    delete_obj(difference_obj)

angle = int(360 / NB_BRICKS_HORIZONTAL)
angles = []
curr = 0
while curr < 180:
    angles.append(curr)
    curr += angle

for angle in angles:
    create_plane_and_cut_igloo(igloo_obj, angle)
