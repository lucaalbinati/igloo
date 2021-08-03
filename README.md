# igloo

## Description

Uses the blender python library ```bpy``` to create an igloo blender mesh.
Moreover, ```script.py``` programmatically generates STL files for each distinct block needed to build an igloo.

## Add-on Setup

### Download the add-on
```
git clone git@github.com:lucaalbinati/igloo.git
```

### Install the add-on on blender

Open the blender application and navigate to ```Blender Preferences``` (Edit > Preferences…).
Then navigate to the ```Add-ons``` tab and click ```Install```.
Select the downloaded git repository folder and that should be it.
You should now see the 'Igloo' add-on in the list.

### Add the igloo object to your scene

In your scene, when adding a new object, you should see ```Igloo``` in the ```Mesh``` category.

## Generate STL files

### Run script
If you don't care about adding the ```Igloo``` mesh to your scene and only want the STL files, you can use ```script.py```.
Running this in a blender instance will do all the work for you:
- adding an igloo, with default parameters,
- exporting each distinct object into an STL file that you can find in the new folder ```output```.
