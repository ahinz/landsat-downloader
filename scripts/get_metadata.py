import json

def load_metadata():
    """Load metadata from JSON file. Return a dictionary with data."""
    raw_json = open('./scripts/ProductMetadata.json', 'r')
    metadata = json.loads(raw_json.read())
    raw_json.close()
    return metadata

def product_meta(product, version=None):
    """Helper function for loading product specific metadata"""
    metadata = load_metadata()

    try:
        if version:
            return  metadata[product]['version'][version]
        else:
            return metadata[product]
    except KeyError:
        print 'Product not found in available data, please check spelling'
        return

    
def list_products():
    """Lists all available products"""
    metadata = load_metadata()
    for prod in metadata.keys():
        print '{0}: {1}'.format(prod, metadata[prod]['title'].encode('utf-8', 'ignore'))

def product_description(product):
    """Lists full description for product"""
    prod_meta = product_meta(product)
    print "Full Description for {0}\n".format(product)
    print "Title: {0}\n".format(prod_meta['title'].encode('utf-8', 'ignore'))

    versions = prod_meta['version'].keys()
    if len(versions) > 1:
        print "Versions Available:"
    else:
        print "Version Available:"
    for v in versions:
        print " -",v
    print "\nDescription: {0}\n".format(prod_meta['description'].encode('utf-8', 'ignore'))
    print "Title and Description taken from <{0}>. Please visit there for more information".format(prod_meta['url'].encode('utf-8', 'ignore'))

def product_bands(product, version):
    """List band names for a product.version"""
    prod_meta = product_meta(product, version)
    print "Available bands for {0}.{1}".format(product, version)
    print "ID:Name"
    for counter, band in enumerate(prod_meta['bands']):
        print "{0}: {1}".format(counter, band['name'])

def band_color_definitions(product, version, bandid):
    prod_meta = product_meta(product, version)
    
    try:
        colors = prod_meta['bands'][bandid]['colors']
    except IndexError:
        print "Error: Band ID not found, please try again."
        return

    print "Color Definition for {0}.{1}".format(product, version)
    for color in colors:
        print " -",color

def parse_dates(urls):
    """Processes URL with dates from version information"""
    return [x.split('/')[-2] for x in urls]

def product_dates(product, version, verbose=False):
    """Lists dates for a product.version"""
    prod_meta = product_meta(product)

    try:
        urls = prod_meta['version'][version]['dates']
        dates = parse_dates(urls)
    except KeyError:
        print "Error: Could not find version for product. To see available versions please run the product versions command."

    if len(dates) < 20 or verbose == True:
        print "Found {0} dates for {1}.{2}".format(len(dates), product, version)
        for d in dates:
            print " -",d
    else:
        print "Found {0} dates. To print all of them use the --verbose option".format(len(dates))

