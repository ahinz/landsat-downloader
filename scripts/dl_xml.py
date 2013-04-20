# Download XML Files for a Given dataset and year #
from xml_downloader import url_finder
import urllib2
import sys

def download_xml(dataset, year):
    """Downloads ALL XML dataset and writes to an output dir
    
    Arguments:
    - `dataset`: MODIS data
    - `year`: year/date to download
    - `outputdir`: directory to write XMLs to
    """
    url = 'http://e4ftl01.cr.usgs.gov/MODIS_Composites/MOTA/{0}/{1}/'.format(dataset, year)
    xml_links = url_finder(url, 'xml$')
    print "Found {0} XML links".format(len(xml_links))

    for counter, l in enumerate(xml_links):
        complete = int(100*(counter/float(len(xml_links))))
        sys.stdout.write("\r{0} percent complete".format(complete))
        fname = "___".join(l.split('/')[-3:])
        page = urllib2.urlopen(url+l)
        html = page.read()
        output = open('./tmp/{0}'.format(fname), 'w')
        output.write(html)
        output.close()
        sys.stdout.flush()
        print '\n'

if __name__ == '__main__':
    dataset = sys.argv[1]
    year = sys.argv[2]

    download_xml(dataset, year)