import rasterio as rio
from whitebox.whitebox_tools import WhiteboxTools

import os

wbt = WhiteboxTools()


def rasterize_sinks_shp(shpfile, outfile, basefile):
    wbt.vector_polygons_to_raster(shpfile, outfile, base=basefile)


def calc_karst_fraction(
    datadir, demfile, sinksfile=None, fill_pits=True, mean_filter=True
):
    basefilename = demfile.split(".")[0]

    # Define filenames
    dempath = os.path.join(datadir, demfile)
    pitfill_dempath = os.path.join(datadir, basefilename + "-pitfill.tif")
    smoothed_dempath = os.path.join(datadir, basefilename + "-smoothed.tif")
    sinkspath = os.path.join(datadir, basefilename + "-sinks.tif")
    d8path = os.path.join(datadir, basefilename + "-d8.tif")
    watershedspath = os.path.join(datadir, basefilename + "-wat.tif")

    if mean_filter:
        # Smooth dem
        wbt.mean_filter(dempath, smoothed_dempath, 5, 5)
    else:
        smoothed_dempath = dempath

    if fill_pits:
        # Fill single-cell pits
        wbt.fill_single_cell_pits(smoothed_dempath, pitfill_dempath)
    else:
        pitfill_dempath = smoothed_dempath

    # Find sinks
    if sinksfile is None:
        wbt.sink(pitfill_dempath, sinkspath, zero_background=True)
    elif ".tif" in sinksfile:
        # Use available sinks file
        sinkspath = sinksfile
    elif ".shp" in sinksfile:
        # We have a shapefile, need to rasterize
        sinkspath = os.path.join(datadir, sinksfile.split(".")[0] + ".tif")
        rasterize_sinks_shp(sinksfile, sinkspath, dempath)

    # Calculate d8 flow direction
    wbt.d8_pointer(pitfill_dempath, d8path)
    # Find watersheds of sinks
    wbt.watershed(d8path, sinkspath, watershedspath)
    wat_src = rio.open(watershedspath)
    wat = wat_src.read()
    nkarst = len(wat[wat > 0])
    nfluvial = len(wat[wat < 0])
    print("n karst draining pixels =", nkarst)
    print("n fluvial draining pixels =", nfluvial)
    print("percent karst =", nkarst / (nkarst + nfluvial))
    return wat
