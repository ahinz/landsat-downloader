# Downloads Metadata #
import re
import urllib2
import os
from subprocess import check_call
import json
import sys

from bs4 import BeautifulSoup
import gdal

def url_finder(url, regex):
    page = urllib2.urlopen(url)
    html = page.read()
    links = []
    soup = BeautifulSoup(html)
    for tag in soup.findAll('a', href=True):
        if re.search(regex, tag['href']):
            links.append(url+tag['href'])
    return links

def get_dates():
    """
    Finds dates for all datasets.

    Returns a dictionary with
    - keys = product.version
    - values = list of urls for all dates available
    """
    mcd_links = url_finder('http://e4ftl01.cr.usgs.gov/MODIS_Composites/MOTA/', 'MCD')
    date_dict = {}
    print "Downloading dates for datasets"
    for counter, link in enumerate(mcd_links):
        sys.stdout.write('\r{0}/{1} downloaded'.format(counter, len(mcd_links)))
        sys.stdout.flush()
        dataset = link.split('/')[-2]
        date_dict[dataset] = url_finder(link, '\d{4}')
    return date_dict

def dl_band_info(date_dict):
    print "Downloading {0} metadata files - may take a while".format(len(date_dict))

    # Change Directory for Download #
    pwd = os.getcwd()
    os.chdir('tmp')
    for k, v in date_dict.items():
        links = url_finder(v[0], 'hdf$')
        filepath = os.path.join(pwd, 'tmp', links[0].split('/')[-1])
        if not os.path.exists(filepath):
            check_call(['curl','-O', links[0]])

def get_colors_metadata(band):
    """
    Grab colors from metadata after loading a band
    """
    band_data = gdal.Open(band)
    metadata = band_data.GetMetadata_List()
    rel_num = 0
    for m in metadata:
        if m.startswith('units='):
            break
        rel_num += 1
    return metadata[rel_num:]

def print_color_metadata(color_list):
    for entry in color_list:
        print entry

def process_metadata(path, date_dict):

    product_dict = {}
    
    # Process Dates #
    for k, v in date_dict.items():
        product, version = k.split('.')
        if product in product_dict.keys():
            product_dict[product]['version'][version] = {}
        else:
            product_dict[product] = {}
            product_dict[product]['version'] = {}
            product_dict[product]['version'][version] = {}
        product_dict[product]['version'][version]['dates'] = v


    # Get Band Information #
    hdfs = [os.path.join(path, f) for f in os.listdir(path) if re.search('hdf$', f)]
    for f in hdfs:
        info = f.split('/')[-1].split('.')
        product = info[0]
        version = ''
        for i in info:
            if re.search('\d{3}', i) and len(i) == 3:
                version = i
            else:
                continue
        product_dict[product]['version'][version]['bands'] = []
        gdal_data = gdal.Open("{0}".format(f))
        bands = gdal_data.GetSubDatasets()
        for band in bands:
            color_list = get_colors_metadata(band[0])
            relevant = band[0].split(':')[-1]
            band_dict = {'name': relevant, 'colors': color_list}
            product_dict[product]['version'][version]['bands'].append(band_dict)

    return product_dict

if __name__ == '__main__':
    date_dict = get_dates()

    dl_band_info(date_dict)
    
    product_dictionary = process_metadata('./tmp', date_dict)

    # Combine with Description Data #
    desc_json = open('./description_of_maps.json', 'r')
    descriptions = json.loads(desc_json.read())
    desc_json.close()

    for k in product_dictionary.keys():
        product_dictionary[k]['description'] = descriptions[k]['description']
        product_dictionary[k]['title'] = descriptions[k]['title']
        product_dictionary[k]['url'] = descriptions[k]['url']

    # Save to File #
    all_metadata = json.dumps(product_dictionary)
    output = open('./ProductMetadata.json', 'w')
    output.write(all_metadata)
    output.close()
    