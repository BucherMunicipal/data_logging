"""
    Records videos of a specific length (specified in the config file) 

    Author: Bouchra Mohamed Lemine

"""


import subprocess 
import time
import os
import signal
import sys
import yaml
from yaml.loader import SafeLoader
from collections import ChainMap
from datasize import DataSize
import datetime




def signal_handler(sig, frame):
    """
        Handles the sigint interrupt that is sent to this program when it is in execution.  
    """
    print("*************************************** Handling Keyboard Interrupt **************************************") 
    for video_rec in running_rec_processes:
        os.kill(video_rec.pid, signal.SIGINT) # kill the process that runs the Gstreamer pipeline. 
    sys.exit(0)

 

if __name__=="__main__":

    signal.signal(signal.SIGINT, signal_handler)

    while True:

        with open("/mnt/ssd-1/workspace/jetson-deepstream/bscripts/logging/logging_config.yaml", "r") as yamlfile:
            data = yaml.load(yamlfile, Loader=SafeLoader)
            camera_info = dict(ChainMap(*data['camera_info']))
            log_dir = data['logging_settings'][2]['logged_data_dir']
            serial_number = data['vehicle_info'][0]['serial_number']
            log_duration = data['logging_settings'][1]['max_log_duration']
            
            yamlfile.close()


        # Before starting a new logging session, check if there is enough space left on the SD card. If there isn't, don't log any data.
        if DataSize(os.popen(f"df -H {log_dir} | awk '{{print $4}}'").read().split("\n")[1]) > DataSize(f"{log_duration / 600}G"):

            print("****************** Writing to an mp4 file")

            running_rec_processes = [] 

            for camera in camera_info['used_cameras']:
                running_rec_processes.append(subprocess.Popen(["sh", "/mnt/ssd-1/workspace/jetson-deepstream/bscripts/logging/video_recording/./nozzle_camera_capture.sh", camera_info[camera][0]['path'], log_dir, camera, serial_number, str(log_duration)]))


            time.sleep(log_duration)


            for video_rec in running_rec_processes:
                # Kill the video logging process.
                os.kill(video_rec.pid, signal.SIGINT)

        
        else:
            print("No space left on the device !!!!!!!!!!!!!!!!!!!!!!!")
            sys.exit(0)


