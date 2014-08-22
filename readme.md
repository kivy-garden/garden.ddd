kivy.ddd
========

ddd is a set of widgets and tools to display 3d meshes in a kivy
program. It can load simple .obj+mtl files on its own, but deffer to the
assimp lib to do the heavy work of loading numerous formats and fixing
the common errors in their formats, saving a lot of pain.

The module also provides a simple multitouch navigation system, as a
separate class (MultitouchCamera), demonstrated in the example.

Assimp usage
------------

You need to have at least assimp 3.1.1 to use this loader.

you need to make python/kivy aware of the lib presence.
on windows, you can edit the portable package to add the port/PyAssimp
dir to PYTHONPATH, and the bin32 dir to PATH, so both the lib and the
dll are found.

on linux, you can add the port/PyAssimp dir to PYTHONPATH as usual,
pyassimp will look in /usr/lib and /usr/local/lib for the .so file, or
you can patch pyassimp/helper.py to add your own path, adding
LD_LIBRARY_PATH support is a good idea, so you can export the lib path
from the shell.


Examples
--------

ddd/view.py can be run as a standalone example, loading .obj/.3ds files
placed in the data/3d dir that accompies it. Textures of the mesh
usually needs to be put in the same dir, or in a relative path refered
to by the material file, tests using files from various places on the
web indicates that textures filenames very often require manual fixing,
especially on unix systems, pay attention to the filenames kivy is
trying to load if you have missing textures.


Issues
------

File loading is currenctly not async, causing the interface to freeze
for several seconds when loasing a big mesh file.

Rendering has visible issues, light modeling is based on Blinn-Phong
model, but is not perfect, there are also issues with polygon borders in
some cases, if someone finds the reason, that's most welcome :).
