#!/usr/bin/python
from subprocess import check_call
import os
import hashlib

def get_tile_names(*args, **kwargs):
    return ["http://e4ftl01.cr.usgs.gov/MODIS_Composites/MOTA/MCD12Q1.005/2002.01.01/MCD12Q1.A2002001.h00v08.005.2011090163104.hdf",
            "http://e4ftl01.cr.usgs.gov/MODIS_Composites/MOTA/MCD12Q1.005/2002.01.01/MCD12Q1.A2002001.h00v09.005.2011090163209.hdf",
            "http://e4ftl01.cr.usgs.gov/MODIS_Composites/MOTA/MCD12Q1.005/2002.01.01/MCD12Q1.A2002001.h10v08.005.2011090163708.hdf"
            ]

verbose = True
def vprint(arg):
    if verbose:
        print arg

def download(tiles):
    outputdir = 'tmp'
    vprint('Downloading %s files to "%s"' % (len(tiles),outputdir))
    
    pwd = os.getcwd()
    os.chdir(outputdir)
    outputs = []
    for tile in tiles:
        filepath = os.path.join(pwd, outputdir, tile.split('/')[-1])

        if not os.path.exists(filepath):
            check_call(['curl','-O',tile])

        outputs.append(filepath)

    return outputs

def extract_bands(tiles, bandtmpl):
    outputs = []

    for tile in tiles:
        filepath,filename = os.path.split(tile)
        band = bandtmpl % filename
        bandsha1 = hashlib.md5(band).hexdigest()

        outputfile = '.'.join(filename.split('.')[0:-1]) + '__%s.tif' % bandsha1
        outputpath = os.path.join(filepath,outputfile)
        outputs.append(outputpath)

        if not os.path.exists(outputfile):
            check_call(['gdal_translate','-of','GTiff',band,outputfile])

    return outputs

def reproject(tiles):
    outputs = []

    for tile in tiles:
        filepath,filename = os.path.split(tile)
        outputfile = '.'.join(filename.split('.')[0:-1]) + '__reprojected.tif'
        outputpath = os.path.join(filepath,outputfile)
        outputs.append(outputpath)

        if not os.path.exists(outputfile):
            check_call(['gdalwarp','-t_srs','EPSG:3857',tile,outputfile])

    return outputs

def colorize(tiles):
    outputs = []

    for tile in tiles:
        filepath,filename = os.path.split(tile)
        outputfile = '.'.join(filename.split('.')[0:-1]) + '__colored.tif'
        outputpath = os.path.join(filepath,outputfile)
        outputs.append(outputpath)

        if not os.path.exists(outputfile):
            check_call(['gdaldem','color-relief',tile,'colors.txt', outputfile])

    return outputs

def main():
    tiles = get_tile_names()

    # Download the tiles of DOOM
    rawhdfs = download(tiles)

    print rawhdfs

    # Extract relevant band
    band = 'HDF4_EOS:EOS_GRID:"%s":MOD12Q1:Land_Cover_Type_1'
    bandtifs = extract_bands(rawhdfs, band)

#    gdalwarp -t_srs EPSG:3857 -dstnodata 128 MCD12Q1.A2001001.h12v12.051.Land_Cover_Type_1.tif land_cover_2001.tif

## create an ARG from geotiff
#gdal_translate -of ARG land_cover_2001.tif land_cover_2001.arg 

    print bandtifs

    reprojs = reproject(bandtifs)
    print reprojs

    colors = colorize(reprojs)
    print colors

if __name__=='__main__':
    main()
