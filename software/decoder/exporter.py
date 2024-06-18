#!/usr/bin/python3

# #{ imports

# math, arrays, etc.
import numpy
import os
import math
import csv

import mysql.connector
from datetime import datetime

from src.structures import *
from src.parse_file import *

from src.export_methods import *

# #} end of imports

# #{ exportDsc()


mydb = mysql.connector.connect(
  host="localhost",
  user="grim",
  password="password",
  database="TE1_data"
)

mycursor = mydb.cursor()



def format_date(input_date_str):
    # Define the input date format
    input_format = "%a %b %d %H:%M:%S %Y"
    
    # Parse the input date string to a datetime object
    datetime_obj = datetime.strptime(input_date_str, input_format)
    
    # Define the output date format
    output_format = "%Y-%m-%d %H:%M:%S"
    
    # Format the datetime object to the desired output format
    formatted_date_str = datetime_obj.strftime(output_format)
    
    return formatted_date_str


def exportDsc(file_path, image_mode, image_id, acq_time, acq_start_time):
    sql = "INSERT INTO meta (FrameID, AcqTime, Timestamp) VALUES (%s, %s, %s)"
    val = (image_id, acq_time, acq_start_time)
    mycursor.execute(sql, val)
    mydb.commit()
    print(mycursor.rowcount, "record inserted.")
    with open(file_path, "w") as dsc_file:

        dsc_file.write("A{0:09d}\r\n\
[F0]\r\n\
Type=double matrix width={1} height={2}\r\n\
\"Frame Name\" (\"Frame Name\"):\r\n\
char[3]\r\n\
{3}\r\n\
".format(1, 256, 256, image_mode))

        dsc_file.write("\r\n")

        dsc_file.write("\"ImageID\" (\"Unique ID assigned to the image by the satellite\"):\r\n\
u32[1]\r\n\
{}\r\n".format(image_id))
        dsc_file.write("\r\n")
        dsc_file.write("\"Acq Time\" (\"Acquisition time [ms]\"):\r\n\
u32[1]\r\n\
{}\r\n".format(acq_time))
        dsc_file.write("\r\n")
        dsc_file.write("\"Start Time (string)\" (\"Start Time String\"):\r\n\
char[64]\r\n\
{}\r\n".format(acq_start_time))

# #} end of exportDsc()

# #{ exportData()

def exportData(file_path, image, imageID, type="toa"):

    with open(file_path, "w") as data_file:

        writer = csv.writer(data_file, quoting=csv.QUOTE_NONE, delimiter=' ')

        for i in range(0, 256):
            for x in image[i, :]:
                writer.writerow(["{}".format(x)])
                sql = " INSERT INTO {} (x, y, {}) VALUES (%s, %s, %s)".format(imageID, type)
                val = (imageID, i, x)
                mycursor.execute(sql, val)
                mydb.commit()
# #} end of exportData()

def importMetadata(file_path, key):
    try:
        with open(file_path, "r") as metadata_file:
            reader = csv.reader(metadata_file, delimiter=',')
            for row in reader:
                if row[0] == str(key):
                    return row[1].lstrip(), row[2].lstrip()
            return 0, 0
    except:
        print("[Error]: can not open metadata file!")
        return -1, 'unknown'
# the file should containt 1 packet of FrameDataMsg_t() per line in HEXadecimal form
file_path = "data/data_flight_G08-W0086/data"
meta_file_path = "data/data_flight_G08-W0086/meta"
write_path = "data_export/data_flight_G08"

if __name__ == '__main__':

    # #{ open the input file => list of "frame_data"
    for filename in os.listdir(file_path):
        print(filename)
        name, ext = filename.split(".")
        try:
            infile = open(file_path+ "/" + filename, "r", encoding="ascii")
        except:
            print("[Error]: can not open input file!")
            exit()
        try:
            os.makedirs(write_path + "/" + name + "/toa")
            os.makedirs(write_path + "/" + name + "/tot")
        except:
            print("[Error]: can not create output directories or are already made")

        # parse the input file, dehexify the data and decode the pixel values
        # frame_data = list of all decoded messages from the MUI
        frame_data = parseFile(infile)

        # #} open the input file

        # #{ frame_data => list of numpy images

        # image data map: image id => numpy image
        images_data = {}

        # enumerate the frame_data (decoded packets) and stitch them together
        for idx,frame in enumerate(frame_data):

            # if this is the first occurance of this frame_id, initialize new numpy image for it
            if images_data.get(frame.frame_id) == None:

                # initialize the right type of image
                if frame.mode == LLCP_TPX3_PXL_MODE_TOA_TOT:
                    images_data[frame.frame_id] = ImageToAToT()
                elif frame.mode == LLCP_TPX3_PXL_MODE_TOA:
                    images_data[frame.frame_id] = ImageToA()
                elif frame.mode == LLCP_TPX3_PXL_MODE_MPX_ITOT:
                    images_data[frame.frame_id] = ImageMpxiToT()

            # iterate over all the pixels within the frame and copy the pixel values to the numpy image
            for idx,pixel in enumerate(frame.pixel_data):

                if frame.mode == LLCP_TPX3_PXL_MODE_TOA_TOT:

                    if isinstance(images_data[frame.frame_id], ImageToAToT):

                        # TOA is the prettiest part and it shows nicely in log()
                        # this is not, ofcourse, an official transformation, please DO NOT USE it if you are going to process the data
                        images_data[frame.frame_id].tot[pixel.x, pixel.y]  = math.log(pixel.tot) if pixel.tot > 0 else 0
                        # images_data[frame.frame_id].tot[pixel.x, pixel.y]  pixel.tot

                        images_data[frame.frame_id].toa[pixel.x, pixel.y]  = pixel.toa
                        images_data[frame.frame_id].ftoa[pixel.x, pixel.y] = pixel.ftoa

                elif frame.mode == LLCP_TPX3_PXL_MODE_TOA:

                    if isinstance(images_data[frame.frame_id], ImageToA):
                        images_data[frame.frame_id].toa[pixel.x, pixel.y]  = pixel.toa
                        images_data[frame.frame_id].ftoa[pixel.x, pixel.y] = pixel.ftoa

                elif frame.mode == LLCP_TPX3_PXL_MODE_MPX_ITOT:

                    if isinstance(images_data[frame.frame_id], ImageMpxiToT):
                        images_data[frame.frame_id].mpx[pixel.x, pixel.y]  = pixel.mpx
                        images_data[frame.frame_id].itot[pixel.x, pixel.y] = pixel.itot

        # sort the image data by id
        sorted_keys = list(images_data.keys())
        sorted_keys.sort()
        sorted_data = {i: images_data[i] for i in sorted_keys}

        images_data = sorted_data

        # #} end of frame_data => list of numpy images

        ## | -------------------- export the images ------------------- |

        for idx,key in enumerate(images_data):

            image = images_data.get(key)

            print("exporting: {}".format(key))
            acq_time, acq_start_time = importMetadata(meta_file_path + "/" + name + "_meta.txt", key)
            acq_start_time = format_date(acq_start_time)

            if isinstance(image, ImageToAToT):

                dsc_toa_file_path = write_path + "/" + name + "/toa/toa_{}.txt.dsc".format(key)
                dsc_tot_file_path = write_path + "/" + name + "/tot/tot_{}.txt.dsc".format(key)
                toa_file_path = write_path + "/" + name + "/toa/toa_{}.txt".format(key)
                tot_file_path = write_path + "/" + name + "/tot/tot_{}.txt".format(key)

                mycursor.execute("CREATE TABLE IF NOT EXISTS {} (x INT, y INT, toa DOUBLE, tot DOUBLE, PRIMARY KEY (x,y))".format(key))
                exportDsc(dsc_toa_file_path, "ToA", key, acq_time, acq_start_time)
                exportDsc(dsc_tot_file_path, "ToT", key, acq_time, acq_start_time)
                exportData(toa_file_path, image.toa, type="toa")
                exportData(tot_file_path, image.tot, type="tot")

            if isinstance(image, ImageToA):

                dsc_file_path = "data_export/{}.dsc".format(key)
                toa_file_path = "data_export/toa_{}.txt".format(key)

                exportDsc(dsc_file_path, key, "ToA")
                exportData(toa_file_path, image.toa)

            if isinstance(image, ImageMpxiToT):

                dsc_file_path = "data_export/{}.dsc".format(key)
                mpx_file_path = "data_export/mpx_{}.txt".format(key)
                itot_file_path = "data_export/itot_{}.txt".format(key)

                exportDsc(dsc_file_path, key, "MpxiToT")
                exportData(mpx_file_path, image.mpx)
                exportData(itot_file_path, image.itot)
