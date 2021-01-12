import bpy
import os

filename = os.path.join(os.path.dirname(bpy.data.filepath), "generate_igloo.py")
exec(compile(open(filename).read(), filename, 'exec'))