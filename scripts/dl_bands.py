from bs4 import BeautifulSoup
import urllib2
import cPickle as pickle
import re
import os

def dl_details():

    details = open('./description_of_maps.p', 'rb')
    d_dict = pickle.load(details)
    
    band_dict = {}
    num = len(d_dict.keys())

    if os.path.isfile('./bands.p'):
        print "Already downloaded bands data"
        return
    print "Downloading bands for {0} maps.".format(num)
    for counter, m in enumerate(d_dict.keys()):
        print counter
        url = d_dict[m][0]
        try:
            page = urllib2.urlopen(url)
        except:
            print "Could not find bands for {0} ({1})".format(m, d_dict[m][0])
            continue
        soup = BeautifulSoup(page.read())
        table = soup.findAll('table')[0]
        band_dict[m] = []
        for row in table.findAll('tr'):
            data = [td.text.strip() for td in row.findAll('td')]
            relevant = False
            for d in data:
                if re.search('-bit', d):
                    relevant = True
            if relevant == False:
                continue
            try:
                band = row.find('td').text.strip()
                band_dict[m].append(band)
            except:
                print "No bands for {0} ({1})".format(m, d_dict[m][0])
        output = open('./bands.p', 'wb')
        pickle.dump(band_dict, output)
        output.close()

if __name__ == '__main__':
    dl_details()