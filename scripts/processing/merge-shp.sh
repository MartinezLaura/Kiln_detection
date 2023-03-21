#!/bin/bash       
#title           :merge-shp.sh
#description     :merge several shp from a folder and output  it in merge.shp
#============================================================================== 
files=`cat $1`

for f in $files; 
do
  ogr2ogr -update -append $2 $f -f "ESRI Shapefile"; 
done;
