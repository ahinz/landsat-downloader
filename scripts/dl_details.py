"""Outputs a pickled dictionary with information on each
available map to download."""

from bs4 import BeautifulSoup
import urllib2
import cPickle as pickle

product_table = 'https://lpdaac.usgs.gov/products/modis_products_table'
products = urllib2.urlopen(product_table)
soup = BeautifulSoup(products.read())

base_url = 'https://lpdaac.usgs.gov'

datasets = soup.findAll('td', {"class": 'views-field views-field-title'})

description_dict = {}
for d in datasets:
    description_dict[d.text.strip()] = [base_url+d.find('a')['href'], ]

print "Downloading {0} dataset information.".format(len(description_dict.keys()))
for counter, k in enumerate(description_dict.keys()):
    print "Downloaded {0} files".format(counter)
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