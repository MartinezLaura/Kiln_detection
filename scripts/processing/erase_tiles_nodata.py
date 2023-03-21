__author__ = "Laura Martinez Sanchez"
__license__ = "GPL"
__version__ = "1.0"
__email__ = "lmartisa@gmail.com"

#heavy process
import time
from osgeo import gdal
import sys
import csv
import os
import shutil
import multiprocessing as mp

#set parent direcory
print(os.environ['DIR'])

inputpath = "{}/inputs/list_tiles.csv".format(os.environ['DIR'])
pancro_out = "{}/inputs/Tiled/pancro/".format(os.environ['DIR'])
RGB_out = "{}/inputs/Tiled/RGB/".format(os.environ['DIR'])


def erase_empty(file):
    """
    Check for empty values in a raster file using GDAL library.
    If the raster file has no data, the function removes the file and its corresponding .tfw file.
    If the raster file has one band, the function moves it to a pancromatic folder.
    If the raster file has three bands, the function moves it to an RGB folder.
    
    Args:
        file (str): The path to the raster file to be checked.
        
    Returns:
        None.
    """
    minv = 0
    maxv = 0
    # this allows GDAL to throw Python Exceptions
    gdal.UseExceptions()
    print(file)
    
    if os.path.isfile(file): 
        try:
            src_ds = gdal.Open(file)
        except:
            print('Unable to open {}'.format(file))
            sys.exit(1)
        try:
            band_num = src_ds.RasterCount
        except:
            # for example, try GetRasterBand(10)
            print('{} bands found :('.format(band_num))
            sys.exit(1)
        for band in range(band_num):
            band += 1
            srcband = src_ds.GetRasterBand(band)
            if srcband is None:
                continue
            stats = srcband.GetStatistics( True, True )
            if stats is None:
                continue
            #check if max an min value are the same and remove file
            minv = minv+stats[0]
            maxv = maxv+stats[1] 

        if minv==0.0 and maxv==0.0:
            remove = file[:-3]
            print("File {} removed. No data on the raster".format(file))
            os.remove(file)
            os.remove(remove+'tfw')
        elif (os.path.isfile(file)) and (band_num == 1):
            print("move it to pancro folder")
            shutil.move(file, pancro_out)

        elif (os.path.isfile(file)) and (band_num == 3):
            print("move it to RGB folder")
            shutil.move(file, RGB_out)
        else:
            print("NEW number of bads on the set {}".format(band_num))

def main():
    
    start = time.time()
    print(mp.cpu_count()-10)
    pool = mp.Pool(mp.cpu_count()-10)
    with open(inputpath, 'r') as f:
        list_files = {line.strip() for line in f}
    pool.map(erase_empty, [file for file in list_files])
    pool.close()
    end = time.time()
    print("Finish!!! :). Execution time: {}".format(end - start))
    sys.exit(0)

if __name__ == '__main__':
    main()