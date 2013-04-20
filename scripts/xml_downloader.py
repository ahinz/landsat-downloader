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
    mcd_links = url_finder('http://e4ftl01.cr.usgs.gov/MODIS_Composites/MOTA/', 'MCD')

    year_links = []
    for l in mcd_links:
        year_links += url_finder(l, '\d+')

    print "Finished getting year links"

    xml_links = []
    for y in year_links:
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