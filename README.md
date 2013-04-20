README

```
$ landsat search land cover
MCD12Q1.005 --- LAND COVER TYPE

$ landsat info MCD12Q1
Version:
005

Dates:
1 2006.01.01
2 2007.01.01
3 2008.01.01
4 2009.01.01

Bands:
1   Land_Cover_Type_1 (8 bit unsigned)
2   Land_Cover_Type_2 (8 bit unsigned)
3   Land_Cover_Type_3 (8 bit unsigned)
4   Land_Cover_Type_4 (8 bit unsigned)
6   Land_Cover_Type_5 (8 bit unsigned)
7   Land_Cover_Type_1 (8 bit signed)
8   Land_Cover_Type_2 (8 bit signed)
9   Land_Cover_Type_3 (8 bit signed)
10  Land_Cover_Type_4 (8 bit signed)
11  Land_Cover_Type_5 (8 bit signed)

$ landsat tiles --date 2006.01.01
                --band #3 
                --layer MCD12Q1
                --output tiles/
                --bbox -120.0,-123.0,45.0,48.0
                 
Downloaded 2.4GB
Created 10003 tiles in "tiles/"
```
