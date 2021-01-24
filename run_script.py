import bpy
import os
import sys

# add python 'igloo' src folder to path
sys.path.append('/Users/lucaalbinati/Documents/MyDocuments/Programmation/blender/Igloo/igloo')

filename = '/Users/lucaalbinati/Documents/MyDocuments/Programmation/blender/Igloo/igloo/main.py'
exec(compile(open(filename).read(), filename, 'exec'))