## This is just a sample script used to transform HDF files into ARG files
## added as a point of reference, in case it's useful.

import os
import glob

## Download yearly MODIS land cover data (500m) for the following year
## and generate an arg for a specific layer.

year = "2011"
layer_name = "Land_Cover_Type_1"

files = glob.glob("*A%s*hdf" % year)
file_string = " ".join(files)

layer_string = "%s_%s" % (layer_name, year)
cmd1_start = "gdalbuildvrt %s.vrt " % (layer_string)

def makeLayer(filename):
  return "HDF4_EOS:EOS_GRID:\"%s\":MOD12Q1:%s" % (filename, layer_name)

layers = map(makeLayer, files)
layers_list = " ".join(layers)
cmd1 = cmd1_start + layers_list
print(cmd1)
os.system(cmd1)

cmd2 = "gdal_translate -of GTiff %s.vrt %s_orig.tif" % (layer_string, layer_string)
print(cmd2)
os.system(cmd2)


web_mercator = True
reproject = ""
if web_mercator: 
  reproject = "-t_srs EPSG:3857"

## -10018754.171394622
 
cmd3 = "gdalwarp -t_srs EPSG:3857 -dstnodata 128 %s_orig.tif %s.tif" % (layer_string, layer_string) 
cmd3a = "gdalwarp -dstnodata 128 %s_orig.tif %s_sinusoidal.tif" % (layer_string, layer_string) 
print(cmd3)
print(cmd3a)

os.system(cmd3)
os.system(cmd3a)
cmd4 = "gdal_translate -of ARG %s.tif %s.arg" % (layer_string, layer_string)
cmd4a = "gdal_translate -of ARG %s_sinusoidal.tif %s_sinusoidal.arg" % (layer_string, layer_string)
print(cmd4)
print(cmd4a)
os.system(cmd4)
os.system(cmd4a)

cmd5 = "sed -i 's/uint/int/g' %s.json" % ( layer_string )
cmd5a = "sed -i 's/uint/int/g' %s_sinusoidal.json" % ( layer_string )
print(cmd5)
print(cmd5a)
os.system(cmd5)
os.system(cmd5a)

