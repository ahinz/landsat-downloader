# Downloads XML data for MCD12Q1.005 #

import urllib2
from bs4 import BeautifulSoup
import re
import multiprocessing

mcd_top = 'http://e4ftl01.cr.usgs.gov/MODIS_Composites/MOTA/'

def url_finder(url, regex):
    page = urllib2.urlopen(url)
    html = page.read()
    links = []
    soup = BeautifulSoup(html)
    for tag in soup.findAll('a', href=True):
        if re.search(regex, tag['href']):
            links.append(url+tag['href'])
    return links

if __name__ == '__main__':

    # Get links for all MCD Directories #
    print "Getting MCD links"
    mcd_links = url_finder('http://e4ftl01.cr.usgs.gov/MODIS_Composites/MOTA/', 'MCD')
    print "Found {0} MCD links".format(mcd_links)
    year_links = []

    print "Getting Year links"
    for counter, l in enumerate(mcd_links):
        print counter
        year_links += url_finder(l, '\d+')

    print "Finished getting year links"

    print "Finding all XML links"
    xml_links = []
    
    for counter, y in enumerate(year_links):
        print counter
        xml_links += url_finder(y, 'xml$')

    print "Need to download {0} XML files".format(len(xml_links))
    for counter, x in enumerate(xml_links):
        if counter % 30 == 0:
            print 'Finished downloading {0}'.format(counter)
        p = urllib2.urlopen(x)
        html = p.read()
        fname = "___".join(x.split('/')[-3:])
        output = open('./data/{0}'.format(fname), 'w')
        output.write(html)
        output.close()