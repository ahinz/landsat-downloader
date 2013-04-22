"""Outputs a pickled dictionary with information on each
available map to download."""

from bs4 import BeautifulSoup
import urllib2
import cPickle as pickle
import sys, os

def dl_details():

    """Downloads details on available MODIS data. Creates and saves
    a dictionary with:

    keys = MODIS data name (e.g. MCD12Q1)
    values = list of url, title, and detailed description"""
    
    if os.path.isfile('./description_of_maps.p'):
        print "Already downloaded file descriptions"
        return
    
    product_table = 'https://lpdaac.usgs.gov/products/modis_products_table'
    products = urllib2.urlopen(product_table)
    soup = BeautifulSoup(products.read())

    base_url = 'https://lpdaac.usgs.gov'

    datasets = soup.findAll('td', {"class": 'views-field views-field-title'})
    
    description_dict = {}
    for d in datasets:
        description_dict[d.text.strip()] = [base_url+d.find('a')['href'], ]

    print "Downloading information for {0} maps.".format(len(description_dict.keys()))
    for counter, k in enumerate(description_dict.keys()):
        complete = int(100*(counter/float(len(description_dict.keys()))))
        sys.stdout.write("\r{0} percent complete ({1}/{2})".format(complete, counter, len(description_dict.keys())))
        url = description_dict[k][0]
        try:
            page = urllib2.urlopen(url)
        except urllib2.URLError:
            print "Could not get info for: {0} ({1})".format(k, url)
            description_dict[k].append('')
            description_dict[k].append('')
            continue
        soup = BeautifulSoup(page.read())
        title = soup.find('div', {'class': 'field-item even'})
        description_dict[k].append(title.text.strip())
        paragraph = soup.find('div', {'property': 'content:encoded'}).text.strip()
        description_dict[k].append(paragraph)

    output = open('./description_of_maps.p', 'wb')
    pickle.dump(description_dict, output)
    output.close()

if __name__ == '__main__':
    dl_details()