__author__ = "Laura Martinez Sanchez"
__license__ = "GPL"
__version__ = "1.0"
__email__ = "lmartisa@gmail.com"

import sys
import os
syspath = "{}/code/scripts/GDAL-python".format(os.environ['DIR'])
sys.path.append(syspath)
import shapefile
import raster
from shutil import copy2
import time
import multiprocessing as mp
import ogr
import json
import shutil


if  len(sys.argv) < 5:
    raise ValueError("the number of arguments passed is not correct")
else:
    inpath = sys.argv[1]
    outpathwith = sys.argv[2]
    outpathwithout = sys.argv[3]
    shpname = sys.argv[4]
    json_f = sys.argv[5]


def create_image_part(img, name, image_id):
    """
    Create a dictionary representing an image and its ID, given the image array, name, and ID.
    
    Args:
        img (numpy array): The image as a numpy array.
        name (str): The name of the image file.
        image_id (int): The unique identifier of the image.
        
    Returns:
        A tuple containing the image dictionary and its ID.
    """
    
    image = {
        'id': image_id,
        'width': img.shape[0],
        'height': img.shape[1],
        'file_name': name,
        'license': 0,
        "flickr_url": "",
        "coco_url": "",
        "date_captured": 0
    }
    return image, image_id

def preprocessshape(file, img_id, annotation_id, images, annotations, outpathwith = outpathwith, outpathwithout = outpathwithout, shpname = shpname):
    """
    This function is used to preprocess a raster file and a corresponding shapefile containing object polygons. 
    It extracts the objects in the raster and creates annotations for them in COCO format
    
    Args:
        file is the path to the input image file, 
        img_id is an integer representing the ID of the current image, 
        annotation_id is an integer representing the ID of the current annotation, 
        images and annotations are lists that store image and annotation data, respectively. 
        Three optional arguments: outpathwith, outpathwithout, and shpname are paths to output directories and the shapefile containing the objects of interest, respectively
        
    Returns:
        img_id, annotation_id, images, annotations
    """
        
    if file.endswith(".tif"):
        basename = os.path.basename(file)
        array, geoTran, proj, datasource = raster.readraster(file, True)
        
        # open shp with the objects       
        layer, driver, dataSource = shapefile.openshp(shpname, 0)
        
        # Check the geometry is inside the bbox of the raster
        xLeft, xRight, yTop, yBottom = raster.GetPointsRaster(datasource)
        rastextend = raster.BBoxAsgeom(xLeft, xRight, yTop, yBottom)
        
        #check the spatial with mask or not mask
        layer.SetSpatialFilter(rastextend)
        if layer.GetFeatureCount() == 0:
            shutil.move(file, outpathwithout)
            
            
        else:
            image, img_id = create_image_part(array, basename, img_id)
            #append the image to the images json list
            shutil.move(file, outpathwith)
            images.append(image)
            for feature in layer:
                geom = feature.GetGeometryRef()
                wkt = geom.ExportToWkt()
                a_string = wkt.split('POLYGON ((')[1].split('))')[0].replace(',',' ')
                a_list = a_string.split()
                map_object = map(float, a_list)
                aux = list(map_object)     
                poly_coords = []  
                for i,k in zip(aux[0::2], aux[1::2]):
                    points = raster.world2Pixel(geoTran, i, k)
                    #handle negative points falling on the edge of the tile
                    if points[0]<0:
                        poly_coords.append(0)
                    else:
                        poly_coords.append(points[0])
                    if points[1]<0:
                        poly_coords.append(0)
                    else:      
                        # handle y coord since in gdal is in the top corner and in python is the bottom corner
                        poly_coords.append(points[1])
                
                bbox = [raster.world2Pixel(geoTran, geom.GetEnvelope()[0], geom.GetEnvelope()[2])[0],
                        
                        raster.world2Pixel(geoTran, geom.GetEnvelope()[1], geom.GetEnvelope()[3])[1],
                        
                        (raster.world2Pixel(geoTran, geom.GetEnvelope()[1], geom.GetEnvelope()[3])[0]) - 
                        (raster.world2Pixel(geoTran, geom.GetEnvelope()[0], geom.GetEnvelope()[2])[0]),
                        
                        (raster.world2Pixel(geoTran, geom.GetEnvelope()[0], geom.GetEnvelope()[2])[1]) - 
                        (raster.world2Pixel(geoTran, geom.GetEnvelope()[1], geom.GetEnvelope()[3])[1])]
        
                #Add the annotation of the polygon to the json list
                annotation = {'id': annotation_id,
                              'image_id': img_id,
                              'category_id': 1,
                              'segmentation': [poly_coords],
                              'area': geom.Area(),
                              'bbox': bbox,
                              'iscrowd': 0,
                              "attributes": {"occluded": "false"}}
                
                annotations.append(annotation)
                annotation_id +=1
                
                
            layer.ResetReading()
            img_id +=1 
            
            res_dict = {"licenses": [{"name": "Swalim project", "id": 0, "url": ""}],
                    "info": {"contributor": "", "date_created": "", "description": "", "url": "", "version": "", "year": ""},
                    "categories": [{"id": 1,"name": "kiln","supercategory": ""}],
                    "images": images,
                    "annotations": annotations}
        
            with open(json_f,'w') as outfile:
                json.dump(res_dict, outfile)
                
    return img_id, annotation_id, images, annotations
 

def main():
    
    start = time.time()
    with open(inpath, 'r') as f:
        list_files = {line.strip() for line in f}
        
    images=[]
    annotations=[]
    img_id = 0
    annotations_id = 0
    for f in list_files:
        img_id, annotations_id, images, annotations = preprocessshape(f, img_id, annotations_id, images, annotations)

    end = time.time()
    print("Finish!!! :). Execution time: {}".format(end - start))
    sys.exit(0)
    
    
if __name__ == '__main__':
    main()
