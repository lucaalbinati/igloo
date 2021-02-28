import os
import bpy
import math
import numpy as np

OUTPUT_DIR = "/Users/lucaalbinati/Documents/MyDocuments/Programmation/blender/addons/igloo/output"

def select_obj(obj):
	bpy.ops.object.select_all(action='DESELECT')
	obj.select_set(True)

def get_angle(loc):
	x = loc[0]
	y = loc[1]
	return math.atan2(y, x)

precision = 128
nb_bricks_vertical = 5
nb_bricks_radial = 6

bpy.ops.mesh.igloo_add(precision=precision, nb_bricks_vertical=nb_bricks_vertical, nb_bricks_radial=nb_bricks_radial)

if not os.path.isdir(OUTPUT_DIR):
	os.makedirs(OUTPUT_DIR)

igloo_objs = [obj for obj in bpy.context.scene.objects if obj.name.startswith('igloo')]

for igloo_obj in igloo_objs:
	select_obj(igloo_obj)
	bpy.ops.operator.prepare_brick()

igloo_objs_and_angles = [(igloo_obj, round(get_angle(igloo_obj.location), 1)) for igloo_obj in igloo_objs]
igloo_objs_and_angles = [(igloo_obj, angle) for igloo_obj, angle in igloo_objs_and_angles if angle > 0]
igloo_objs_and_angles = sorted(igloo_objs_and_angles, key=lambda x: x[1])

model_angle = igloo_objs_and_angles[0][1]

unique_igloo_objs = [igloo_obj for igloo_obj, angle in igloo_objs_and_angles if angle == model_angle]
unique_igloo_objs.append(next(igloo_obj for igloo_obj in igloo_objs if 'top' in igloo_obj.name))
unique_igloo_objs = sorted(unique_igloo_objs, key=lambda x: x.location[2])

for i, igloo_obj in enumerate(unique_igloo_objs):
	select_obj(igloo_obj)
	stl_path = os.path.join("{}/igloo_brick_{}.stl".format(OUTPUT_DIR, i))
	bpy.ops.export_mesh.stl(filepath=stl_path, use_selection=True)