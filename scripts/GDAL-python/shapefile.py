__author__ = "Laura Martinez Sanchez"
__license__ = "GPL"
__version__ = "1.0"
__email__ = "lmartisa@gmail.com"


from osgeo import osr, ogr, gdal
import os, raster, sys


def openshp(shapePath, type):
    """
    Open the shapefile and resturns the datasource, driver and the layer
    for types :
    0 means read-only. 1 means writeable.
    
    Args:
        shapePath (srt): Tthe path to the shapefile to open.
        
    Returns:
        ogr.Layer: Layer just opened.
        ogr.driver: driver used to open the layer, ESRI Shapefile.
        ogr.datasource: Datasource belonging to the shapefile opened
    
    """
    driver = ogr.GetDriverByName("ESRI Shapefile")
    if driver is None:
        print ('Unable to open %s' % shapePath)
        sys.exit(1)
    dataSource = driver.Open(shapePath, type)
    layer = dataSource.GetLayer()
    return layer, driver, dataSource


def ArrayToPoly(pathimg, control, outname, submit_dir, weights_path, probas):
    """
    First save the array in a raster and then does the polygonization
    if you want to erase the raster just set erasetif = True

    Args:
    pathimg (str): The path to the input raster image
    control (numpy.ndarray): The array to be converted into a polygon
    outname (str): The name of the output shapefile
    submit_dir (str): The directory where the input raster image is located
    weights_path (str): The path to the weights
    probas (numpy.ndarray): The probabilities of the polygons

    Returns:
    None
    """
    
    img = gdal.Open(pathimg)
    if img is None:
        print ('Unable to open %s' % pathimg)
        sys.exit(1)
    geoTrans = img.GetGeoTransform()
    proj = img.GetProjection()
    driver = gdal.GetDriverByName('MEM')
    
    dataset = driver.Create('', control.shape[1], control.shape[0], 1, gdal.GDT_UInt16)
    dataset.GetRasterBand(1).WriteArray(control)
    dataset.SetGeoTransform(geoTrans)
    dataset.SetProjection(proj)
    
    #create path 
    aux = outname.split('/')[:-1] 
    outname = '/'.join(aux)+'/FinalGeoms'
    drv = ogr.GetDriverByName("ESRI Shapefile")
    print(outname)
    # Remove output shapefile if it already exists
    if os.path.exists(outname+'.shp'):
        dst_ds = drv.Open(outname+'.shp', 1)
        dst_layer = dst_ds.GetLayer()

    else:
        dst_ds = drv.CreateDataSource(outname+'.shp')
        srs = osr.SpatialReference()
        srs.ImportFromWkt(proj)
        dst_layer = dst_ds.CreateLayer('results', srs = srs, geom_type = ogr.wkbMultiPolygon)
        
        new_field = ogr.FieldDefn("submitname", ogr.OFTString)
        dst_layer.CreateField(new_field)
        new_field = ogr.FieldDefn("weightname", ogr.OFTString)
        dst_layer.CreateField(new_field)
        new_field = ogr.FieldDefn("proba", ogr.OFTReal)
        dst_layer.CreateField(new_field)

    drvMEM = ogr.GetDriverByName("MEMORY")
    dst_ds_pol = drvMEM.CreateDataSource('MemData')
    srs = osr.SpatialReference()
    srs.ImportFromWkt(proj)
    dst_layer_pol = dst_ds_pol.CreateLayer('', srs = srs, geom_type = ogr.wkbMultiPolygon)
    new_field = ogr.FieldDefn("submitname", ogr.OFTString)
    dst_layer_pol.CreateField(new_field)
    new_field = ogr.FieldDefn("weightname", ogr.OFTString)
    dst_layer_pol.CreateField(new_field)
    new_field = ogr.FieldDefn("proba", ogr.OFTReal)
    dst_layer_pol.CreateField(new_field)
 
    featureDefn = dst_layer.GetLayerDefn()
    gdal.Polygonize(dataset.GetRasterBand(1), dataset.GetRasterBand(1), dst_layer_pol, 0, [], callback = None)
    count = 0
    for feature in dst_layer_pol:
        print(probas[count].item())
        outFeature = ogr.Feature(featureDefn)
        outFeature.SetField('proba', probas[count].item())
        outFeature.SetField('submitname', submit_dir)
        outFeature.SetField('weightname', weights_path)
        outFeature.SetGeometry(feature.GetGeometryRef())
        #Not SetFeature in layer that does not has that feature, but create a new feature!
        dst_layer.CreateFeature(outFeature)
        outFeature = None
        dst_layer.SyncToDisk()
        count = count + 1

    dst_ds_pol = None
    dst_layer = None
    dst_ds = None
    dataset.FlushCache()
    dataset = None


def CreatFeatfromGeom(listgeom, layer):
    """
    Convert a list of geometry objects into a list of features and add them to an OGR layer.
    
    Args:
        listgeom: List of geometry objects to be converted into features.
        layer: OGR layer to add the features to.
    
    Returns:
        List of newly created features.
    """
    layer_defn = layer.GetLayerDefn()  # gets parameters of the current shapefile
    listfeat = []
    fI = 0  # this will be the first point in our dataset
    ##now lets write this into our layer/shape file:
    for geom in listgeom:
        feature = ogr.Feature(layer_defn)
        feature.SetGeometry(geom)
        feature.SetFID(fI)
        layer.CreateFeature(feature)
        fI += 1
        listfeat.append(feature)
        feature = None
    return listfeat


def CreateshpFromFeat(namelayer, proj,  geoTrans, shape, listfeat=None, fromgeom = None, mem = False):
    """
    Creates a shapefile from a list of OGR features or geometries.
    
    Args:
        namelayer: Name of the layer or shapefile to be created.
        proj: Well-known text (WKT) representation of the spatial reference system (SRS).
        geoTrans: A tuple containing the geotransform parameters for the rasterization process.
        shape: A tuple containing the shape of the output raster, as (x_min, x_max, y_min, y_max).
        listfeat: Optional. A list of OGR feature objects to be used to create the shapefile. If not provided,
                         `fromgeom` must be provided instead.
        fromgeom: Optional. A list of OGR geometry objects to be converted into features and used to create the
                         shapefile. If not provided, `listfeat` must be provided instead.
        mem: Optional. A boolean indicating whether
    
    Returns:
        the output layer as an OGR Layer object.
    """

    if mem:
        # create an output datasource in memory
        outdriver = ogr.GetDriverByName('MEMORY')
        source = outdriver.CreateDataSource('memData')
        # open the memory datasource with write access
        tmp = outdriver.Open('memData', 1)
    else:
        # set up the shapefile driver
        driver = ogr.GetDriverByName("ESRI Shapefile")
        # create the data source
        source = driver.CreateDataSource(namelayer+'.shp')

    srs = osr.SpatialReference()
    srs.ImportFromWkt(proj)

    layer = source.CreateLayer(namelayer, srs = srs, geom_type=ogr.wkbPolygon)
    if fromgeom is not None:
        listfeat = CreatFeatfromGeom(fromgeom, layer)
    for feature in listfeat:
        layer.CreateFeature(feature)
    Rasteriz(namelayer, layer, geoTrans, proj, shape)
    return layer


def Rasteriz(outname, layer, geoTrans, proj, shape):
    """
    Rasterizes a vector layer into a raster dataset.

    Args:
        outname (str): name of the output raster dataset.
        layer (ogr.Layer): input vector layer to be rasterized.
        geoTrans (tuple): geotransform parameters of the output raster.
        proj (str): projection of the output raster.
        shape (tuple): shape (width, height) of the output raster.
        
    Returns:
        None
    """
    dataset = raster.emptyrast(outname, geoTrans, proj, shape)
    gdal.RasterizeLayer(dataset, [1], layer, burn_values=[1])
    dataset = None



