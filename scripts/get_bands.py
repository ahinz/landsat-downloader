import sys
from osgeo import gdal

def user_select_band(path_to_hdf, default=None):
    """
    Process for user to select band for downloaded map.

    If user chooses default, takes first band.
    """
    gdal_data = gdal.Open(path_to_hdf)
    bands = gdal_data.GetSubDatasets()
    if default != None:
        return default, bands[default][0]

    print 'Please enter a selection for band to use for this map:'
    selection = False
    while selection == False:
        acceptable = []
        for counter, band in enumerate(bands):
            relevant = band[0].split(':')[-1]
            print "{0}: {1}".format(counter, relevant)
            acceptable.append(counter)
        user_input = raw_input("Please enter integer of your choice:")
        user_input = int(user_input)
        if user_input in acceptable:
            selection = True
        else:
            print "Error: Not acceptable selection, please enter an integer of one of the following choices"
    return user_input, bands[user_input][0]