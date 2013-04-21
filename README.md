README

You have to have curl, gdal-bin, and python-gdal installed

Search for MODIS data:
```
$ python loader.py info 
000:  MCD12Q1.051
001:  MCD43B4.005
002:  MCD12C1.051
003:  MCD43C1.005
004:  MCD43C2.005
005:  MCD43A1.005
006:  MCD43B2.005
...
```

Determine what dates you can use:
```
$ python loader.py info MCD43A2
000:  2000.02.18
001:  2000.02.26
002:  2000.03.05
003:  2000.03.13
...
```

Download the data!
```
$ python loader.py download 
      --dataset MCD12Q1.051
      --date 2001.01.01 2006.01.01 2011.01.01
      --bbox -56.2 -78.7 -15.9 -63.8
      --tiles tiles
      --zoom 3-8
      
Creates zoom levels 3-8 in the "tiles" directory
```
