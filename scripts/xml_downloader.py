# Downloads XML data for MCD12Q1.005 #

import urllib2
from bs4 import BeautifulSoup
import re
from multiprocessing import Pool
import os
import cPickle as pickle

def url_finder(url, regex):
    page = urllib2.urlopen(url)
    html = page.read()
    links = []
    soup = BeautifulSoup(html)
    for tag in soup.findAll('a', href=True):
        if re.search(regex, tag['href']):
            links.append(tag['href'])
    return links

def file_diff(file1, file2):
    check_exists(file2)
    f1 = open(file1, 'r')
    f2 = open(file2, 'r')
    f1list = f1.read().split('\n')
    f2list = f2.read().split('\n')
    f1set = set(f1list)
    f2set = set(f2list)
    uniq = f1set.difference(f2set)
    return list(uniq)

def check_exists(f):
    if os.path.exists(f):
        pass
    else:
        os.system('touch {0}'.format(f))

if __name__ == '__main__':

    # Get links for all MCD Directories #
    print "Getting MCD links"
    mota = 'http://e4ftl01.cr.usgs.gov/MODIS_Composites/MOTA/'
    mcd_links = url_finder('http://e4ftl01.cr.usgs.gov/MODIS_Composites/MOTA/', 'MCD')
    mcd_dict = {}
    for l in mcd_links:
        name = l.split('/')[-2]
        mcd_dict[name] = []
    print "Found {0} MCD links".format(len(mcd_links))
    print mcd_dict
    print "Getting Year links"
    for counter, l in enumerate(mcd_dict.keys()):
        urls = url_finder(mota + l, '\d+')
        for url in urls:
            year = url.split('/')[-2]
            mcd_dict[l].append(year)
    print "Finished getting year links"

    mcd_output = open('./mcd_output.p', 'wb')
    pickle.dump(mcd_dict, mcd_output)
    
