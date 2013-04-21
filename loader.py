#!/usr/bin/python
from subprocess import check_call
import os
import hashlib
import argparse
from scripts import xml_downloader
from scripts import dl_xml
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

def get_tile_names2(latmin,lngmin,latmax,lngmax):
    dataset = 'MCD12Q1.005'
    date = '2002.01.01'

    xmlfiles = dl_xml.download_xml(dataset, date)
    selected = []
    for xmlfile in xmlfiles:
        bb = get_xml_boundary(xmlfile)
        (bb_lon_min, bb_lat_min), (bb_lon_max, bb_lat_max) = get_latlon_minmax(bb)
        if (latmax > bb_lat_min and latmin < bb_lat_max and
            lngmax > bb_lon_min and lngmin < bb_lon_max):
            _, xmlfile = os.path.split(xmlfile)
            selected.append('http://e4ftl01.cr.usgs.gov/MODIS_Composites/MOTA/%s/%s/%s' %
                            (dataset, date, '.'.join(xmlfile.split('.')[:-1])))

    return selected

def get_tile_names(latmin,lngmin,latmax,lngmax):
    dataset = 'MCD12Q1.005'
    date = '2002.01.01'

    import pyproj
    p = pyproj.Proj("+proj=sinu +lon_0=0 +x_0=0 +y_0=0 +a=6371007.181 +b=6371007.181 +units=m +no_defs")
    xmin,ymin = p(lngmin, latmin)
    xmax,ymax = p(lngmax, latmax)

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

def clipit(tiles):
    outputs = []
    extent = ['-8434677', '4971129', '-8248774', '4734571']
    #extent = ['-75.77','39.09','-74.10','40.72']

    for tile in tiles:
        filepath,filename = os.path.split(tile)
        outputfile = '.'.join(filename.split('.')[0:-1]) + '__clipped.tif'
        outputpath = os.path.join(filepath,outputfile)
        outputs.append(outputpath)

        if not os.path.exists(outputpath):
            check_call(['gdal_translate', '-projwin'] + extent + [tile, outputpath])

    return outputs


def main():
    tiles = get_tile_names(39.09, -75.77, 40.72, -74.10)

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

    # COLORIZE FIRST, *THEN* reproject
    colors = colorize(reprojs)
    print colors

    clips = clipit(colors)
    print clips


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
            dl_xml.download_xml(dataset, args.date)
        else:
            print "That date wasn't found"
    else:
        if dataset:
            data = adict[dataset]
        else:
            data = adict.keys()

        print '\n'.join(["%03d:  %s" % (a,b) for (a,b) in zip(range(0,len(adict.keys())), data)])

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

    # parse the args and call whatever function was selected
    args = parser.parse_args()
    #args.func(args)

    main()
    #tiles = get_tile_names(39.09, -75.77, 40.72, -74.10)
    #print tiles
