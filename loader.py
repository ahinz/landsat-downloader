#!/usr/bin/python
from subprocess import check_call
import os
import hashlib
import argparse

from scripts import xml_downloader

def get_tile_names(*args, **kwargs):
    return [ "http://e4ftl01.cr.usgs.gov/MODIS_Composites/MOTA/MCD12Q1.005/2002.01.01/MCD12Q1.A2002001.h10v08.005.2011090163708.hdf",
             "http://e4ftl01.cr.usgs.gov/MODIS_Composites/MOTA/MCD12Q1.005/2002.01.01/MCD12Q1.A2002001.h10v07.005.2011090163853.hdf",
             "http://e4ftl01.cr.usgs.gov/MODIS_Composites/MOTA/MCD12Q1.005/2002.01.01/MCD12Q1.A2002001.h11v07.005.2011090163921.hdf"
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

def mergeit(tiles):
    outputpath,filename = os.path.split(tiles[0])

    outputsha = hashlib.md5("|".join(tiles)).hexdigest()
    outputfile_tmpl = os.path.join(outputpath, "%s__%s.%%s" % (filename.split('.')[0],outputsha))

    vrtfile = outputfile_tmpl % 'vrt'
    tiffile = outputfile_tmpl % 'tif'
    
    if not os.path.exists(tiffile):
        check_call(['gdalbuildvrt', vrtfile] + tiles)
        check_call(['gdal_translate','-of', 'GTiff', vrtfile, tiffile])

    return [tiffile]

def main():
    tiles = get_tile_names()

    # Download the tiles of DOOM
    rawhdfs = download(tiles)

    print rawhdfs

    # Extract relevant band
    band = 'HDF4_EOS:EOS_GRID:"%s":MOD12Q1:Land_Cover_Type_1'
    bandtifs = extract_bands(rawhdfs, band)

    print bandtifs

    joinedtifs = mergeit(bandtifs)

    reprojs = reproject(joinedtifs)
    print reprojs

    colors = colorize(reprojs)
    print colors


# sub-command functions
def list_sets(args):
    adict = xml_downloader.get_dict()
    if args.dataset:
        data = adict[args.dataset]
    else:
        data = adict.keys

    print '\n'.join(["%03d %s" % (a,b) for (a,b) in zip(range(0,len(adict.keys())), data)])

if __name__=='__main__':
    #adict = xml_downloader.get_dict()
    #main()

    # create the top-level parser
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    # create the parser for the "foo" command
    parser_list = subparsers.add_parser('list')
    parser_list.add_argument('dataset', type=str, nargs='?')
    parser_list.set_defaults(func=list_sets)

    # parse the args and call whatever function was selected
    args = parser.parse_args()
    args.func(args)
