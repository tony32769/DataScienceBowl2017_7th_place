import os,sys
import numpy as np
import xml.etree.ElementTree as ET
import SimpleITK
import pandas as pd
import cv2


def normalize_scan_hounsfield(img_array_input):
  
  debug = False
  img_array = np.copy(img_array_input.astype(float))
  
  min_hu = -1000
  max_hu = 200
  
  img_array[img_array<min_hu]=min_hu
  img_array[img_array>max_hu]=max_hu
  

  diff = max_hu - min_hu
  img_array = img_array - min_hu
  
  img_array = img_array / float(diff)
  
  if(debug):
    print "normalize_scan_debug:"
    print sh
    print min_img_array
    print max_img_array
    print (x_center_start,x_center_end)
    print (y_center_start,y_center_end)
    print (np.min(img_array),np.max(img_array))
  
  return np.copy(img_array)


def z_world_to_sliceIdx(z_world,z_offset, z_spacing):

  idxSlice_float =  float(z_world - z_offset ) / z_spacing
  idxSlice_top = int(idxSlice_float) +1
  idxSlice = int(idxSlice_float)
  
  # check ob schlecht gerundet wurde
  if( abs(idxSlice_top - idxSlice_float) < abs(idxSlice - idxSlice_float) ):
    idxSlice += 1
   
  return idxSlice

def get_nodule_info(nodule_id, roi, idxSlice, prefix):
  
  x_min = float("inf")
  x_max = float("-inf")
  y_min = float("inf")
  y_max = float("-inf")

  
  for edgeMap in roi.iter('{'+prefix+'}edgeMap'): # loop iver all edgeMaps
      xCoord = int(edgeMap.findall('{'+prefix+'}xCoord')[0].text)
      yCoord = int(edgeMap.findall('{'+prefix+'}yCoord')[0].text)
      
      x_min = min(xCoord,x_min)
      x_max = max(xCoord,x_max)
      y_min = min(yCoord,y_min)
      y_max = max(yCoord,y_max)
  
  
  x_center = int( (x_min + x_max)/2 )
  y_center = int( (y_min + y_max)/2 )
 
  return [nodule_id, (x_center,y_center,idxSlice),(x_min,x_max),(y_min,y_max)]


xml_path_lst_unblinded = np.genfromtxt('/media/philipp/qnap/LIDC/preprocessing/2_get_xml_paths_unblinded_read/xml_path_lst_unblinded_read.csv', delimiter=",",dtype=str)
original_spacing_df = pd.read_csv("/media/philipp/qnap/LIDC/preprocessing/3_write_original_spacing_info/original_spacings.csv",header=0,sep="\t")



debug = True

nodule_info_lst = []

radiologist_id_lst = []

nodule_id_lst = []
dcm_path_lst = []

nodule_x_center_lst = []
nodule_y_center_lst = []
nodule_z_center_lst = []

nodule_x_min_lst = []
nodule_x_max_lst = []

nodule_y_min_lst = []
nodule_y_max_lst = []

total_len = len(xml_path_lst_unblinded)
counter = 0

for xml_path in xml_path_lst_unblinded:
  print (counter,total_len)
  counter += 1


  
  dcm_path = os.path.dirname(os.path.abspath(xml_path))

  
  
  this_spacing_df = original_spacing_df[original_spacing_df['dcm_path'] == dcm_path]
  
  if(len(this_spacing_df) != 1): # if dcm_path does not exist in dcm_path_df: maxbe wrong username?
    print "dcm_path not found in /media/philipp/qnap/LIDC/preprocessing/3_write_original_spacing_info/original_spacings.csv"
    print "wrong username?"
    sys.exit()
  
  z_spacing = this_spacing_df["z_spacing"].values[0]
  z_offset = this_spacing_df["z_offset"].values[0]
  
  
  tree = ET.parse(xml_path)
  root = tree.getroot()
  
  
  img_array = None
  if(debug):
    reader = SimpleITK.ImageSeriesReader()
    filenamesDICOM = reader.GetGDCMSeriesFileNames(dcm_path)
    reader.SetFileNames(filenamesDICOM)
    imgOriginal = reader.Execute()
    img_array = SimpleITK.GetArrayFromImage(imgOriginal)

  if(len(root.attrib.keys()) == 1):
    print xml_path +  "  -  incorrect header"
    continue # falls header nciht sauber geschrieben wurde ("," fehlt)

  if(root.attrib.keys()[0] != "uid"):
    prefix =  root.attrib[ root.attrib.keys()[0] ].split()[0]
  else:
    prefix =  root.attrib[ root.attrib.keys()[1] ].split()[0]


  for readingSession in range(4): # loop over all 4 radiologists
    zPos_lst = []
    for nodule in root[readingSession+1].iter('{'+prefix+'}unblindedReadNodule'): #loop over all nodules
      
      
      nodule_id = str(nodule.findall('{'+prefix+'}noduleID')[0].text)

      characteristics_exist = False
      for i in nodule.iter('{'+prefix+'}characteristics'):
	characteristics_exist = True
	#print i[0].text
      
      if(characteristics_exist): #this means the nodule is > 3mm
	
	for roi in nodule.iter('{'+prefix+'}roi'): # loop iver all regions of interest
	  
	  inclusion = roi.findall('{'+prefix+'}inclusion')[0].text
	  if(inclusion == "TRUE"):
	    z_world = float(roi.findall('{'+prefix+'}imageZposition')[0].text)

	    idxSlice = z_world_to_sliceIdx(z_world,z_offset, z_spacing)

	    
	    nodule_info = get_nodule_info(nodule_id, roi, idxSlice, prefix)
	    nodule_info_lst += [nodule_info]
	    
	    radiologist_id_lst += [readingSession]

	    nodule_id_lst += [nodule_info[0]]
	    dcm_path_lst += [dcm_path]

	    nodule_x_center_lst += [nodule_info[1][0]]
	    nodule_y_center_lst += [nodule_info[1][1]]
	    nodule_z_center_lst += [nodule_info[1][2]]

	    nodule_x_min_lst += [nodule_info[2][0]]
	    nodule_x_max_lst += [nodule_info[2][1]]

	    nodule_y_min_lst += [nodule_info[3][0]]
	    nodule_y_max_lst += [nodule_info[3][1]]
	    
	    
	    if(debug):
	      print img_array.shape
	      img_arr_slice = img_array[idxSlice,:,:].copy()
	      img_arr_slice = normalize_scan_hounsfield(img_arr_slice)
	      img_arr_slice *= 255
	      img_arr_slice = img_arr_slice.astype(np.uint8)
	      cv2.rectangle(img_arr_slice,(nodule_info[2][0],nodule_info[3][0]),(nodule_info[2][1],nodule_info[3][1]),(255,255,255),1)
	      cv2.imshow("tester",img_arr_slice)
	      cv2.waitKey(0)
	    
'''
df = pd.DataFrame()
df.insert(0,"radiologist_id",radiologist_id_lst)
df.insert(1,"nodule_id",nodule_id_lst)
df.insert(2,"dcm_path",dcm_path_lst)
df.insert(3,"x_center",nodule_x_center_lst)
df.insert(4,"y_center",nodule_y_center_lst)
df.insert(5,"sliceIdx",nodule_z_center_lst)
df.insert(6,"x_min",nodule_x_min_lst)
df.insert(7,"x_max",nodule_x_max_lst)
df.insert(8,"y_min",nodule_y_min_lst)
df.insert(9,"y_max",nodule_y_max_lst)

df.to_csv('dataframe_nodules_gt3mm.csv', sep = '\t')
'''