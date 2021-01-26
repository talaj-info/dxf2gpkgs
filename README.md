dxf2gpkgs
=========
converts the features of a DXF file to separate GPKG files

Installation:
=============

1. Install Python. During installation make sure Python is added to your system PATH
2. Install Python dependencies: **python-slugify** and **GDAL**. As direct GDAL installation is hard with PIP, I put the necessary wheel files in the `dependencies` folder for Python versions 3.8 and 3.9. You should call `pip install mydependencywheelfile.whl` from command line with the wheel file which do match your system and Python version.
3. Copy the contents of the `scripts` directory to `C:\scripts`.
4. Copy the `DXF Break.lnk` shortcut to your Desktop.
5. Now you should be able to drag and drop a DXF file to your *DXF Break* desktop shortcut; it will convert the DXF to several GPKG files. You will find the GPKG files in a subdirectory next to your DXF file.