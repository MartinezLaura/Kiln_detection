
__author__ = "Laura Martinez Sanchez"
__license__ = "GPL"
__version__ = "1.0"
__email__ = "lmartisa@gmail.com"

import numpy as np
from shapefile import *
import matplotlib.pyplot as plt


def plotras(image):
    """
    This function takes in a four-band image as input and displays each of the bands
    separately using matplotlib's subplots. The function expects the image to be in 
    the format of an array with shape (height, width, 4), where the fourth dimension 
    represents the different bands (red, green, blue, and nir).
    
    Args:
    - image: numpy array, four-band image with shape (height, width, 4)
    
    Returns:
    - None, displays a plot of the four bands using matplotlib
    """

    fig, axes = plt.subplots(2, 2, figsize = (20, 20))
    ax = axes.flatten()

    ax[0].imshow(image[:,:,0])
    ax[0].set_axis_off()
    ax[0].set_title("red", fontsize = 12)

    ax[1].imshow(image[:,:,1])
    ax[1].set_axis_off()
    ax[1].set_title("green", fontsize = 12)

    ax[2].imshow(image[:,:,2])
    ax[2].set_axis_off()
    ax[2].set_title("blue", fontsize = 12)

    ax[3].imshow(image[:,:,3])
    ax[3].set_axis_off()
    ax[3].set_title("nir", fontsize = 12)
    fig.tight_layout()
    plt.show()

def world2Pixel(geoMatrix, x, y):
    """
    Uses a gdal geomatrix (gdal.GetGeoTransform()) to calculate the pixel location
    of a geospatial coordinate. The function takes in a geotransform matrix, which
    is a six-element tuple containing information about the origin, pixel size, and
    rotation of an image in geographic coordinates. The function then uses this
    information to convert a given point (specified by its x and y coordinates in
    geographic space) to pixel coordinates in the corresponding image space.
    
    Args:
    - geoMatrix: tuple, six-element tuple containing geotransform matrix information
    - x: float, x-coordinate of the point to be converted
    - y: float, y-coordinate of the point to be converted
    
    Returns:
    - pixel: int, the pixel coordinate of the input point in the image
    - line: int, the line coordinate of the input point in the image
    """
    
    ulX = geoMatrix[0]
    ulY = geoMatrix[3]
    xDist = geoMatrix[1]
    yDist = geoMatrix[5]
    pixel = int((x - ulX) / xDist)
    line = int((y - ulY) / yDist)
    return pixel, line


def Pixel2World(geoMatrix, cols, rows):
    """
    Uses a gdal geomatrix (gdal.GetGeoTransform()) to calculate the geospatial
    coordinates corresponding to a pixel location in an image. The function takes
    in a geotransform matrix, which is a six-element tuple containing information
    about the origin, pixel size, and rotation of an image in geographic coordinates.
    The function also takes in the column and row indices of the pixel whose
    geospatial coordinates are to be calculated, and returns the corresponding
    x and y coordinates in geographic space.
    
    Args:
    - geoMatrix: tuple, six-element tuple containing geotransform matrix information
    - cols: int, the column index of the pixel whose coordinates are to be calculated
    - rows: int, the row index of the pixel whose coordinates are to be calculated
    
    Returns:
    - xLeft: float, the x-coordinate of the left edge of the specified pixel in geographic space
    - xRight: float, the x-coordinate of the right edge of the specified pixel in geographic space
    - yTop: float, the y-coordinate of the top edge of the specified pixel in geographic space
    - yBottom: float, the y-coordinate of the bottom edge of the specified pixel in geographic space
    """
    pixelWidth = geoMatrix[1]
    pixelHeight = geoMatrix[5]

    xLeft = geoMatrix[0]
    yTop = geoMatrix[3]
    xRight = xLeft + cols * pixelWidth
    yBottom = yTop + rows * pixelHeight

    return xLeft, xRight, yTop, yBottom


def readraster(pathimg, array = False):
    """
    Opens a raster file and returns its geotransform and projection information.
    If the optional argument `array` is set to `True`, the function also returns
    the raster data as a NumPy array.
    
    Args:
    - pathimg: str, the path to the raster file to be opened
    - array: bool, optional argument indicating whether or not to return raster data as a NumPy array
    
    Returns:
    - If `array` is False, returns a tuple containing the following items:
        - geoTrans: tuple, six-element tuple containing geotransform matrix information
        - proj: str, string containing projection information
        - img: gdal.Dataset, GDAL dataset object representing the opened raster file
    - If `array` is True, returns a tuple containing the following items:
        - array: np.ndarray, NumPy array containing the raster data
        - geoTrans: tuple, six-element tuple containing geotransform matrix information
        - proj: str, string containing projection information
        - img: gdal.Dataset, GDAL dataset object representing the opened raster file
    """
    img = gdal.Open(pathimg)
    if img is None:
        print ('Unable to open %s' % pathimg)
        sys.exit(1)
    geoTrans = img.GetGeoTransform()
    proj = img.GetProjection()
    if array:
        array = img.ReadAsArray()
        return array, geoTrans, proj, img
    else:
        return geoTrans, proj, img


def saveraster(outname, array, geoTrans, proj, shape):
    '''
    Saves a raster file with the specified name, raster data, geotransform and projection information.

    Args:
    - outname: str, full path and name (without extension) for the output raster file
    - array: np.ndarray, NumPy array containing the raster data to be saved
    - geoTrans: tuple, six-element tuple containing geotransform matrix information
    - proj: str, string containing projection information
    - shape: tuple, three-element tuple containing the number of bands, x-dimension, and y-dimension of the raster data
    
    Returns:
    - None
    
    Note: The output raster file will be saved in GeoTIFF format with a data type of UInt16.
    '''
    driver = gdal.GetDriverByName('GTiff')
    dataset = driver.Create(outname + '.tif', shape[1], shape[2], shape[0], gdal.GDT_UInt16)
    dataset.GetRasterBand(1).WriteArray(array)
    dataset.SetGeoTransform(geoTrans)
    dataset.SetProjection(proj)
    dataset.FlushCache()
    dataset = None


def emptyrast(outname,geoTrans, proj, shape):
    '''
    Creates an empty raster file with the specified name, geotransform and projection information.

    Args:
    - outname: str, full path and name (without extension) for the output raster file
    - geoTrans: tuple, six-element tuple containing geotransform matrix information
    - proj: str, string containing projection information
    - shape: tuple, three-element tuple containing the number of bands, x-dimension, and y-dimension of the raster data
    
    Returns:
    - dataset: gdal.Dataset, an empty GDAL dataset object
    
    Note: The output raster file will be created in GeoTIFF format with a data type of Int32.
    '''

    driver = gdal.GetDriverByName('GTiff')
    dataset = driver.Create(outname + '.tif', shape[1], shape[2], shape[0], gdal.GDT_Int32)
    dataset.SetGeoTransform(geoTrans)
    dataset.SetProjection(proj)
    return dataset



def GetPointsRaster(dataSource):
    """
    Returns the bounding box of a raster as a tuple of (xLeft, xRight, yTop, yBottom).
    
    Args:
    - dataSource: a gdal DataSource object representing the raster
    
    Returns:
    - A tuple of (xLeft, xRight, yTop, yBottom)
    """
    
    transform = dataSource.GetGeoTransform()
    pixelWidth = transform[1]
    pixelHeight = transform[5]
    cols = dataSource.RasterXSize
    rows = dataSource.RasterYSize

    xLeft = transform[0]
    yTop = transform[3]
    xRight = xLeft + cols * pixelWidth
    yBottom = yTop + rows * pixelHeight
    return xLeft, xRight, yTop, yBottom


def BBoxAsgeom(xLeft, xRight, yTop, yBottom):
    """
    Converts the bounding box coordinates into a polygon geometry using OGR.

    Args:
        xLeft (float): The minimum x coordinate.
        xRight (float): The maximum x coordinate.
        yTop (float): The maximum y coordinate.
        yBottom (float): The minimum y coordinate.

    Returns:
        ogr.Geometry: A polygon geometry representing the bounding box.
    """
    
    ring = ogr.Geometry(ogr.wkbLinearRing)
    ring.AddPoint(xLeft, yTop)
    ring.AddPoint(xLeft, yBottom)
    ring.AddPoint(xRight, yBottom)
    ring.AddPoint(xRight, yTop)
    ring.AddPoint(xLeft, yTop)
    envelope = ogr.Geometry(ogr.wkbPolygon)
    envelope.AddGeometry(ring)
    return envelope


    return layer, driver, dataSource

