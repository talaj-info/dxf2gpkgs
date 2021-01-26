import collections
import os
import pathlib
import sys
import warnings

# dependencies
from osgeo import ogr, osr, gdal
from slugify import slugify


DXF_EXTENSION = ".dxf"
os.environ['DXF_ENCODING'] = "utf-8"


in_driver = ogr.GetDriverByName("DXF")
out_driver_memory = ogr.GetDriverByName("MEMORY")
out_driver_gpkg = ogr.GetDriverByName("GPKG")

DEFAULT_EPSG = 23700  # Hardcoded at this point; replace manually for the desired spatial reference system.


def dxf2gpkglayers(dxf_file, *, epsg=None, out_dir=None, verbose=False):
    epsg = epsg or DEFAULT_EPSG
    spatialref = osr.SpatialReference()
    spatialref.ImportFromEPSG(epsg)

    dxf = in_driver.Open(str(dxf_file), 0)
    in_entities = dxf.GetLayer("entities")
    layers = collections.defaultdict(list)
    for feature in in_entities:
        layer = feature.GetField("Layer")
        layers[layer].append(feature)

    # We create memory files to avoid excessive disk usage and slowness.

    for layer, features in layers.items():

        # We add features to the appropriate memory file first.  

        slugname = slugify(layer)
        p = filename = f'{slugname}.gpkg'
        if verbose:
            print(filename)
        if out_dir:
            p = pathlib.Path(out_dir) / filename
        
        out_datasource_gpkg = out_driver_gpkg.CreateDataSource(str(p))
        if out_datasource_gpkg is None:  # unpythonic: requires explicit None check
            warnings.warn(f'ERROR: layer "{slugname}" was not created')
            out_datasource_gpkg = None  # unpythonic: osgeo module weirdness
            continue
        out_datasource_memory = out_driver_memory.CreateDataSource(str(p))
        
        out_entities = out_datasource_memory.CreateLayer("entities")

        in_layerdefn = in_entities.GetLayerDefn()
        for i in range(0, in_layerdefn.GetFieldCount()):
            fielddefn = in_layerdefn.GetFieldDefn(i)
            out_entities.CreateField(fielddefn)

        out_layerdefn = out_entities.GetLayerDefn()
        for fn, in_feature in enumerate(features):
            out_feature = ogr.Feature(out_layerdefn)
            for i in range(0, out_layerdefn.GetFieldCount()):
                nameref = out_layerdefn.GetFieldDefn(i).GetNameRef()
                try:
                    out_feature.SetField(nameref, in_feature.GetField(i))
                except RuntimeError:
                    warnings.warn(f'ERROR: layer "{slugname}" feature#{fn} {nameref} was not copied')
                    out_feature.SetField(nameref, "")
                    pass
            geom = in_feature.GetGeometryRef()
            geom.AssignSpatialReference(spatialref)
            in_feature = None  # unpythonic: osgeo module weirdness
            out_feature.SetGeometry(geom)
            out_entities.CreateFeature(out_feature)
            out_feature = None  # unpythonic: osgeo module weirdness

        # Now once the memory file is done, we copy them to disk files.

        out_entities2 = out_datasource_gpkg.CopyLayer(out_entities, "entities", ['OVERWRITE=YES'])

        out_datasource_memory = None  # unpythonic: osgeo module weirdness
        out_datasource_gpkg = None  # unpythonic: osgeo module weirdness


def main():
    good, bad = [], []
    for a in sys.argv[1:]:
        p = pathlib.Path(a)
        if not p.is_file():
            bad.append(a)
            continue
        if p.suffix.lower() != DXF_EXTENSION:
            bad.append(a)
            continue
        good.append(p)
    if bad:
        for a in bad:
            print(f'ERROR: not DXF file: "{a}"')
        return 2
    if good:
        for p in good:
            out_dir = p.parent / f'{p.stem.replace(".", "-")}-layers'
            if not out_dir.is_dir():
                out_dir.mkdir()
            dxf2gpkglayers(p, out_dir=out_dir, verbose=True)
    else:
        print("ERROR: no DXF file was given")
        return 1
    return 0




if __name__ == "__main__":
    sys.exit(main())
