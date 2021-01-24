import bpy

# Utility methods

# Context switching
def object_mode():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

def edit_mode():
    if bpy.context.mode != 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')

# Selecting objects
def select_objs(objs, enter_editmode=False):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objs:
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

    if enter_editmode:
        edit_mode()

def select_obj(obj, enter_editmode=False):
    return select_objs([obj], enter_editmode)

# Deleting objects
def delete_objs(objs):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objs:
        select_obj(obj)
        bpy.ops.object.delete(use_global=False)

def delete_obj(obj):
    return delete_objs([obj])