#!/bin/bash 
#
# maketiles.sh
# 
# version 9: 17-November-2014
#
#  Morgan Hite, www.hesperus-wild.org
#
# This is a bash script written under Ubuntu linux. It uses the GDAL utility 'gdal_translate' to 
# cut a tif image into tiles, and produce corresponding Tiff World Files (TFW) for each tile. 
#
# The user passes the dimensions of the original image, the desired dimension of the tiles
# (all tiles are assumed to be square), and the amount of desired tile overlap to the script as parameters 
# on the command line. All measurements are in pixels. A prefix for the naming of the 
# tile files is also required.
#
# The script will 'nudge in' the final column and row of tiles to retain the specified tile
# dimensions. For this reason the overlap between the last row and the previous row, 
# and the last column and the previous column, can be larger than the requested overlap.
#
# Command line usage:
#
#        ./maketiles.sh <image file> <desired tile size in pixels> <number of columns in image> <number of rows in image> <tile_filename_prefix> <overlap>
#
# Example: you have a tif image ("mytif.tif") whose dimensions are 5864x3488, and you want to cut it 
# into 2000x2000 pixel tiles with an overlap of 300 pixels. Each tile file should begin with "mytif_tile". 
# Your command line would be:
#
#      ./maketiles.sh mytif.tif 2000 5864 3488 mytif_tile 300
#
# If you don't know the dimensions of your image, you can use
#
#     gdalinfo mytif.tif
#
# maketiles.sh makes tiles named with a "_x_y.tif" suffix, where x is a row and y is a column in the final 
# tiled image. In the above example they would be named "mytif_tile_1_1.tif", "mytif_tile_1_2.tif",
#  "mytif_tile_1_3.tif" etc.
#
# Each tif file produced also has a corresponding TFW file, e.g., mytif_tile_1_1.tfw", "mytif_tile_1_2.tfw",
#  "mytif_tile_1_3.tfw" etc.
#
#
#
#
# Collect parameters from the command line
#
imageFile=$1
tileSize=$2
echo "-------------------------------------------------------------"$1
imageXMax=`file $1 | cut -d'=' -f7` #width
imageYMax=`file $1 | cut -d'=' -f3 | cut -d',' -f1` #height
prefix=$3
overlap=$4
outdir=$5

if [ -z "$2" ] 
 then
   echo "maketiles.sh version 9"
   echo "USAGE: ./maketiles.sh <image file> <desired tile size in pixels> <number of columns in image> <number of rows in image> <tile_filename_prefix> <overlap>"
  exit
fi
# report (for debugging) the parameters
#
echo "image file is $imageFile"
echo "desired tile size is " $2 "x" $2
echo "image is " $imageXMax "columns by " $imageYMax " rows"
echo "prefix is $prefix"
echo "overlap is $overlap pixels."
echo

#Bail if the input image is too small to cut into tiles
#
if [ $imageXMax -lt $tileSize ] || [ $imageYMax -lt $tileSize ]
 then
  echo "Image is too small to be tiled!"
  exit
fi
#
# ---------------------- ESTIMATE TILES -------------------------
#
#Estimate what we will produce
#
if [ $imageXMax -eq $tileSize ]
 then
  expectedColumnsOfTiles=1
 else
  expectedColumnsOfTiles=$(( imageXMax/tileSize+1))
fi

if [ $imageYMax -eq $tileSize ]
 then
   expectedRowsOfTiles=1
 else
  expectedRowsOfTiles=$(( imageYMax/tileSize+1))
fi
echo "Estimating $expectedColumnsOfTiles columns of tiles (X), by $expectedRowsOfTiles rows of tiles (Y)."

#Do we need to increase the number of tiles to make sure we have the right overlap?
#
# COLUMNS
#
finalColumn=$(( ($tileSize) + ($expectedColumnsOfTiles - 1) * ($tileSize-$overlap)  ))
shortFall=$(( ($imageXMax) -  ($finalColumn) ))
#
# report (for debugging) the finalColumn
#
echo
echo "Taking a closer look at columns."
echo "When laying out $expectedColumnsOfTiles columns of tiles, it looks like the final column will fall at $finalColumn pixels."
#
# if shortFall is greater than 0, add one more column of tiles 
#
if [ $shortFall -eq 0 ]
 then
  echo "That's exactly the image size."
fi
if [ $shortFall -gt 0 ] 
 then 
   expectedColumnsOfTiles=$(( $expectedColumnsOfTiles+1 )) 
   echo "That won't even make it to the end of the image! The overlap requires creating one more column of tiles than I had estimated."
   echo "Trying now with $expectedColumnsOfTiles columns."
   finalColumn=$(( ($tileSize) + ($expectedColumnsOfTiles - 1) * ($tileSize-$overlap)  ))
   shortFall=$(( ($imageXMax) -  ($finalColumn) ))
   finalOverlap=$(( $finalColumn + $overlap - $imageXMax))
   echo "When laying out $expectedColumnsOfTiles columns of tiles, it looks like the final column will fall at $finalColumn pixels."
fi
#
# If shortFall is negative, report finaOverlap
#
if [ $shortFall -lt 0 ]
 then
  finalOverlap=$(( $finalColumn + $overlap - $imageXMax))
  echo "That's bigger than the image, so we'll back off the final column of tiles to begin at $(( $imageXMax - $tileSize)) and end exactly at $imageXMax."
  echo "This final column of tiles will overlap the second-to-last column by $finalOverlap pixels."
fi
#
# ROWS
#
finalRow=$(( ($tileSize) + ($expectedRowsOfTiles - 1) * ($tileSize-$overlap) ))
shortFall=$(( ($imageYMax) -  ($finalRow) ))
#
# report (for debugging) the finalRow
#
echo
echo "Taking a closer look at rows."
echo "When laying out $expectedRowsOfTiles row of tiles, it looks like the final row will fall at $finalRow pixels."
#
# if shortFall is greater than 0, add one more row of tiles 
#
if [ $shortFall -eq 0 ]
 then
  echo "That's exactly the image size."
fi
if [ $shortFall -gt 0 ]
 then expectedRowsOfTiles=$(( $expectedRowsOfTiles+1 )) 
 echo "That won't even make it to the end of the image! The overlap requires creating one more row of tiles than I had estimated."
 echo "Trying now with $expectedRowsOfTiles rows."
 finalRow=$(( ($tileSize) + ($expectedRowsOfTiles - 1) * ($tileSize-$overlap)  ))
 shortFall=$(( ($imageYMax) -  ($finalRow) ))
 finalOverlap=$(( $finalRow + $overlap - $imageYMax))
 echo "When laying out $expectedRowsOfTiles rows of tiles, it looks like the final row will fall at $finalRow pixels."
fi
#
# If shortFall is negative or zero, report finaOverlap
#
if [ $shortFall -lt 0 ]
 then finalOverlap=$(( $finalRow + $overlap - $imageYMax))
 echo "That's bigger than the image, so we'll back off the final row of tiles to begin at $(( $imageYMax - $tileSize)) and end exactly at $imageYMax."
 echo "This final row of tiles will overlap the second-to-last row by $finalOverlap pixels."
fi
#
#Report how many tiles we expect to make
#
echo
echo "Layout has $(($expectedRowsOfTiles*$expectedColumnsOfTiles)) tiles in $expectedRowsOfTiles rows and $expectedColumnsOfTiles columns."
#
# ---------------------- SUGGEST OPTIMAL OVERLAP -------------------------
#
bestOverlapX=$(( (($tileSize * $expectedColumnsOfTiles) - $imageXMax) / ($expectedColumnsOfTiles - 1) ))
#echo "bestOverlapX is $bestOverlapX"
bestOverlapY=$(( (($tileSize * $expectedRowsOfTiles) - $imageYMax) / ($expectedRowsOfTiles - 1) ))
#echo "bestOverlapY is $bestOverlapY"
bestOverlap=$bestOverlapY
if [ $bestOverlapX -lt $bestOverlapY ]
 then bestOverlap=$bestOverlapX
fi
echo "Would you like to go with an overlap of $bestOverlap, which would spread the overlap out but keep the same number of tiles? [Y/n]"
read a
case  $a in
 "n")
  echo "Overlap remains at $overlap."
 ;;
 *)
  overlap=$bestOverlap
  echo "Overlap set to $bestOverlap."
 ;;
esac
echo "overlap is $overlap."
echo
echo "Hit Enter to proceed with cutting tiles, or Ctrl-C to exit."
read a
#
# ---------------------- CUT TILES -------------------------
#
#
#
# Set the index pointers
#
presentRow=1              #presentRow is, at all times, the row of the tile we're ABOUT to make
presentColumn=1        #presentColumn is, at all times, the column of the tile we're ABOUT to make
presentXMin=0              #presentXMin is, at all times, the lowest pixel column of the tile we're ABOUT to make
presentXMax=$tileSize   #presentXMax is, at all times, the highest pixel column of the tile we're ABOUT to make
presentYMin=0              #presentYMin is, at all times, the lowest pixel row of the tile we're ABOUT to make
presentYMax=$tileSize   #presentYMax is, at all times, the highest pixel row of the tile we're ABOUT to make
presentTileType=0
#
# OUTER LOOP -- for rows
#
while [ $presentRow -le $expectedRowsOfTiles ]
 do
#
# INNER LOOP -- for columns
#
# DEBUG
#    echo "DEBUG: Entering INNER LOOP. presentRow is $presentRow and presentColumn is $presentColumn.  expectedColumnsOfTiles is $expectedColumnsOfTiles. presentXMin is $presentXMin and presentXMax is $presentXMax."
#
#while [ $presentXMax -lt $imageXMax ]    
while [ $presentColumn -le $expectedColumnsOfTiles ]    
  do
#
#cut the tile
#
  tileFileName=$prefix"_"$presentRow"_"$presentColumn".tif"
  echo 
  echo "Producing tile $tileFileName (row $presentRow, column $presentColumn).  Extents: ($presentXMin, $presentYMin) to ($presentXMax, $presentYMax)."
#
# report (for debugging) the gdal_translate line we're using
#
   echo "gdal_translate  -co \"TFW=YES\" -srcwin $presentXMin $presentYMin $tileSize $tileSize $imageFile $tileFileName"
   echo
   gdal_translate  -co "TFW=YES" -srcwin $presentXMin $presentYMin $tileSize $tileSize $imageFile $outdir$tileFileName
#
#step us forward to the next column
#
      presentXMin=$(( $presentXMin+$tileSize-$overlap))
      presentXMax=$(( $presentXMin+$tileSize))
      presentColumn=$(( presentColumn+1 ))
# DEBUG
#      echo "DEBUG: Having stepped forward to the next column, presentRow is $presentRow and presentColumn is $presentColumn.  expectedColumnsOfTiles is $expectedColumnsOfTiles. presentXMin is $presentXMin and presentXMax is $presentXMax."
#
# skip this IF block if we just did the last tile in the row
#
   if [ $presentColumn -le $expectedColumnsOfTiles ] 
    then
#
# test if we are within one tile of the end of the row, and if so, back off
#
      if [ $presentXMax -gt $imageXMax ]
       then
#
# report (for debugging) that we've reached the end of the row
#
        echo
        echo "The final tile in the row will be a bit too big."
        presentXMax=$imageXMax
        echo "To keep all tiles the same size, I'm backing off the upper left corner of this tile from ($presentXMin,$presentYMin) to ($(( $presentXMax-$tileSize)),$presentYMin)."
        presentXMin=$(( $presentXMax-$tileSize))
      fi
    fi
 done
#
# report that the row is finished
#
echo "ROW IS FINISHED."
#
#step us forward to the next row
#
  presentYMin=$(( $presentYMin+$tileSize-$overlap))
  presentYMax=$(( $presentYMin+$tileSize))
  presentRow=$(( $presentRow+1 ))
#
# reset X parameters to the beginning of the row
#
  presentColumn=1
  presentXMin=0
  presentXMax=$tileSize
# DEBUG
#    echo "DEBUG: Changing rows: presentRow is $presentRow and presentColumn is $presentColumn.  expectedColumnsOfTiles is $expectedColumnsOfTiles. presentXMin is $presentXMin and presentXMax is $presentXMax."
#
# skip this IF block if we just did the last row
#
   if [ $presentRow -le $expectedRowsOfTiles ] 
    then
#
# test if we are within one tile of the bottom of the image, and if so, back off
#
     if [ $presentYMax -gt $imageYMax ]
      then
#
# report (for debugging) that we've reached the bottom of the image
#
      echo
      echo "Tiles in the final row will be a bit too tall."
      presentYMax=$imageYMax
      echo "To keep all tiles the same size, I'm backing off the upper left corner of the first tile in the final row from (0,$presentYMin) to (0,$(( $presentYMax-$tileSize)))."
    presentYMin=$(( $presentYMax-$tileSize))
    fi
  fi
 done
echo "IMAGE IS FINISHED."
