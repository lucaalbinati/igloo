# igloo

## Description

Uses the blender python library ```bpy``` to create an igloo blender mesh.
Moreover, ```script.py``` programmatically generates STL files for each distinct block needed to build an igloo.

## Install Add-on

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

If you don't care about adding the ```Igloo``` mesh to your scene and only want the STL files, you can use ```script.py```.
This will do all the work for you:
- adding an igloo, with default parameters,
- exporting each distinct object into an STL file that you can find in the new folder ```output```.

### Run script in blender

Open an instance of blender and open the ```Scripting``` view.
Open ```script.py```, modify the default parameters (if you want) and run it!

### Run script in the terminal

First you need to find your blender application, so that you can call it from the terminal.
In macOS BigSur, you should find it at:
```
/Applications/Blender.app/Contents/MacOS/Blender
```
Then you can run the command:
```
/Applications/Blender.app/Contents/MacOS/Blender --background --python script.py
```
Note that the terminal has to be in the repository's directory.
Otherwise you should specifiy the path to the file ```script.py```.

## 🛠 Improvements

Feel free to create an issue or a pull request in case you find bugs or want to add a feature!
