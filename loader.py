#!/usr/bin/python
from subprocess import check_call
import os
import hashlib
import argparse
import pyproj
from scripts import xml_downloader
from scripts import dl_xml
from scripts.get_bands import select_band
from scripts.get_metadata import product_dates, product_bands, band_color_definitions
from bs4 import BeautifulSoup

def get_latlon_minmax(yxlist):
    """
    Given a list of 1 or more lat-lon coordinates, returns [(lon_min, lat_min), (lon_max, lat_max)]
    """
    lon_min = min(yxlist, key=lambda p: p[0])[0]
    lat_min = min(yxlist, key=lambda p: p[1])[1]
    lon_max = max(yxlist, key=lambda p: p[0])[0]
    lat_max = max(yxlist, key=lambda p: p[1])[1]
    return [(lon_min, lat_min), (lon_max, lat_max)]

def get_xml_boundary(path):
    """
    Returns the boundary defined in an xml metadata file, or None if an error occurs
    Result is an array of four (lon, lat) tuples corresponding to the corners of the boundary
    path:   The path to the xml file to read
    """
    try:
        with open(path, 'r') as f:
            # Sample path:
            # //GranuleURMetaData//SpatialDomainContainer//HorizontalSpatialDomainContainer//
            #   GPolygon//Boundary//Point//Point{Longitude,Latitude}
            xml_tree = BeautifulSoup(f, 'xml')
            bb = xml_tree.SpatialDomainContainer.HorizontalSpatialDomainContainer.GPolygon.Boundary
            points_raw = [(p.PointLongitude, p.PointLatitude) for p in bb.findChildren('Point')]
            points = [(float(lon.contents[0]), float(lat.contents[0])) for lon, lat in points_raw]
            return points
    except Exception as e:
        # Debug
        print("Exception: %s" % e)
        return None

def get_tile_names(dataset, date, latmin,lngmin,latmax,lngmax):

    p = pyproj.Proj("+proj=sinu +lon_0=0 +x_0=0 +y_0=0 +a=6371007.181 +b=6371007.181 +units=m +no_defs")
    xmin,ymin = p(lngmin, latmin)
    xmax,ymax = p(lngmax, latmax)

    if xmin > xmax:
        t = xmax
        xmax = xmin
        xmin = t

    tilewidth = 1111950.5196666666
    xoffset = -20015109.354
    yoffset = -10007554.677

    xtilemin = int((xmin - xoffset) / tilewidth)
    ytilemin = 17 - int((ymax - yoffset) / tilewidth)

    xtilemax = int((xmax - xoffset) / tilewidth)
    ytilemax = 17 - int((ymin - yoffset) / tilewidth)

    xmlfiles = dl_xml.download_xml(dataset, date)

    tiles = []
    for x in range(xtilemin, xtilemax+1):
        for y in range(ytilemin, ytilemax+1):
            s = '.h%02dv%02d.' % (x,y)
            for xmlfile in xmlfiles:
                if s in xmlfile:
                    _, filename = os.path.split(xmlfile)
                    tiles.append('http://e4ftl01.cr.usgs.gov/MODIS_Composites/MOTA/%s/%s/%s' %
                                 (dataset, date, '.'.join(filename.split('.')[:-1])))
                    break

    return tiles


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

def extract_bands(tiles):
    outputs = []
    band_selection = None
    for tile in tiles:
        band_selection, band = user_select_band(tile, band_selection)
        filepath,filename = os.path.split(tile)
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


def colorize(tiles, colors='../colors.txt'):
    outputs = []

    for tile in tiles:
        filepath,filename = os.path.split(tile)
        outputfile = '.'.join(filename.split('.')[0:-1]) + '__colored.tif'
        outputpath = os.path.join(filepath,outputfile)
        outputs.append(outputpath)

        if not os.path.exists(outputfile):
            check_call(['gdaldem', 'color-relief', tile, colors, outputfile])

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

def clipit(tiles, extent):
    outputs = []

    for tile in tiles:
        filepath,filename = os.path.split(tile)
        outputfile = '.'.join(filename.split('.')[0:-1]) + '__clipped.tif'
        outputpath = os.path.join(filepath,outputfile)
        outputs.append(outputpath)

        xmin,ymin,xmax,ymax = extent
        extent = [xmin,ymax,xmax,ymin]

        if not os.path.exists(outputpath):
            check_call(['gdal_translate', '-projwin'] + map(str,extent) + [tile, outputpath])

    return outputs


def process(dataset, date, extent_ll):
    #extent_ll = ['39.09','-75.77','40.72','-74.10']

    p = pyproj.Proj('+proj=merc +lon_0=0 +k=1 +x_0=0 +y_0=0 +a=6378137 +b=6378137 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs')
    xmin,ymin = p(extent_ll[1], extent_ll[0])
    xmax,ymax = p(extent_ll[3], extent_ll[2])
    extent = map(int,[xmin,ymin,xmax,ymax]) #['-8434677', '4971129', '-8248774', '4734571']

    #dataset = 'MCD12Q1.005'
    #date = '2002.01.01'

    tiles = get_tile_names(dataset, date, *extent_ll)

    # Download the tiles of DOOM
    rawhdfs = download(tiles)

    print "Select bands"

    # Extract relevant band
    bandtifs = extract_bands(rawhdfs)

    print "Merging bands into single image"

    joinedtifs = mergeit(bandtifs)

    print "Reprojecting to EPSG900913"

    reprojs = reproject(joinedtifs)

    print "Colorzing..."

    colors = colorize(reprojs)

    print "Clipping to your bounding box..."

    clips = clipit(colors, extent)

    print "Done!"

    return clips

# sub-command functions
def list_sets(args):
    adict = xml_downloader.get_dict()
    dataset = None
    if args.dataset:
        try:
            dataset = adict.keys()[int(args.dataset)]
        except:
            matches = filter(lambda z: z.startswith(args.dataset), adict.keys())
            if len(matches) == 1:
                dataset = matches[0]
            else:
                print "Too many matches:"
                print '\n'.join(matches)
                exit(1)

    if args.date and dataset:
        dates = adict[dataset]

        if args.date in dates:
            print "Downloading metadata xml..."
            dl_xml.download_xml(dataset, args.date)
        else:
            print "That date wasn't found"
    else:
        if dataset:
            data = adict[dataset]
        else:
            data = adict.keys()

        print '\n'.join(["%03d:  %s" % (a,b) for (a,b) in zip(range(0,len(adict.keys())), data)])

def download_entry(args):
    dataset = args.dataset
    dates = args.date
    extent = args.bbox

    # Some hanky-panky goes on... don't let it screw us over
    pwd = os.getcwd()

    tiles = []
    for date in dates:
        tiles += get_tile_names(dataset, date, *extent)

    print "Dataset: %s\nDates: %s\nTiles to Download:" % (dataset, ','.join(dates))
    print "\n".join(tiles)

    if args.info:
        return

    print "Starting download"
    results = []
    for date in dates:
        print "Processing date: %s" % date
        results += process(dataset, date, extent)
        os.chdir(pwd)

    print "Processs tiles"
    if args.tiles:
        for (result,date) in zip(results, dates):
            tile = args.tiles[0]
            check_call(['gdal2tiles.py','-z'] + args.zoom + [result] + [tile + '/' + date])

if __name__=='__main__':
    #adict = xml_downloader.get_dict()
    #main()

    # create the top-level parser
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    # create the parser for the "list" command
    parser_list = subparsers.add_parser('info')
    parser_list.add_argument('dataset', type=str, nargs='?')
    parser_list.add_argument('date', type=str, nargs='?')
    parser_list.set_defaults(func=list_sets)

    # create the parser for the "list" command
    parser_dl = subparsers.add_parser('download')
    parser_dl.add_argument('--dataset', type=str)
    parser_dl.add_argument('--date', type=str, nargs='+')
    parser_dl.add_argument('--tiles', type=str, nargs=1)
    parser_dl.add_argument('--zoom', type=str, nargs=1)
    parser_dl.add_argument('--bbox', type=str, nargs=4)    
    parser_dl.add_argument('--info', action='store_true')
    parser_dl.set_defaults(func=download_entry)

    # parse the args and call whatever function was selected
    args = parser.parse_args()
    args.func(args)

