"""
    Records videos of a specific length (specified int he config file) 

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





def signal_handler(sig, frame):
    """
        Handles the sigint interrupt that is sent to this program when it is in execution if logging_mode is 0.  
    """
    print("*************************************** Handling Keyboard Interrupt **************************************") 
    global running_rec_processes
    for video_rec in running_rec_processes:
        os.kill(video_rec.pid, signal.SIGINT) # kill the process that runs the Gstreamer pipeline. 
    sys.exit(0)



signal.signal(signal.SIGINT, signal_handler)




while True:

    running_rec_processes = []

    with open("/home/g/workdisk/workspace/jetson-deepstream/bscripts/logging/logging_config.yaml", "r") as yamlfile:
        data = yaml.load(yamlfile, Loader=SafeLoader)
        camera_info = dict(ChainMap(*data['camera_info']))
        log_dir = data['logging_settings'][2]['logged_data_dir']
        serial_number = data['vehicle_info'][0]['serial_number']
        log_durarion = data['logging_settings'][1]['max_log_duration']
        
        yamlfile.close()

        

    for camera in camera_info['used_cameras']:
        running_rec_processes.append(subprocess.Popen(["sh", "/home/g/workdisk/workspace/jetson-deepstream/bscripts/logging/video_recording/./nozzle_camera_capture.sh", camera_info[camera][0]['path'], log_dir, camera, serial_number, str(log_durarion)]))


    time.sleep(log_durarion)


    for video_rec in running_rec_processes:
        # Kill the video logging process.
        os.kill(video_rec.pid, signal.SIGINT)


