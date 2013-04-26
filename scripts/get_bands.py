from osgeo import gdal

def select_band(path_to_hdf, bandid):
    """
    Process for user to select band for downloaded map.

    If user chooses default, takes first band.
    """
    gdal_data = gdal.Open("{0}".format(path_to_hdf))
    bands = gdal_data.GetSubDatasets()
    return bands[bandid][0]