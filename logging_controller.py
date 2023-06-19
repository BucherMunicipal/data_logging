"""
    Controls the video recording and CAN logging processes.

    Author: Bouchra Mohamed Lemine

"""


import pyinotify
import os
import signal 
import subprocess 
import time
from threading import Thread
import yaml
from yaml.loader import SafeLoader
from datasize import DataSize
import sys 
import datetime
import cv2


 
def stop_logging(sig, frame):
    """
        Gracefully stops the logging processes when a SIGINT interrupt is sent, either from the keyboard or "watch_gpio_pin.sh"
    """
    global logging  
    global can_logging 
    global video_rec 

    print("Exiting ...")
    if logging:
        os.kill(can_logging.pid, signal.SIGINT)
        os.kill(video_rec.pid, signal.SIGINT)

        while (os.popen(f"ps aux | grep {can_logging.pid} | awk '{{print $12}}'").read().split("\n")[0]) != "<defunct>":
            print("waiting for logging to complete")

    sys.exit(0)
 




def manage_logging():
    """
        Starts or stops the logging functionality depending on the value of "logging_mode" in the config file.
    """
    global logging  
    global can_logging 
    global video_rec 
    
    time.sleep(0.05) # Wait for 5 milliseconds to make sure the changes have been saved in the config file.
            
    with open(config_file) as f:
        data = yaml.load(f, Loader=SafeLoader) 

    if data['logging_settings'][0]['logging_mode'] and not logging:
        print("starting logging .....")

        # Before starting a new logging session, check if there is enough space left on the SD card. If there isn't, don't log any data.
        if DataSize(os.popen(f"df -H {data['logging_settings'][2]['logged_data_dir']} | awk '{{print $4}}'").read().split("\n")[1]) < DataSize(f"{data['logging_settings'][1]['max_log_duration'] / 600}G"):
            sys.exit(0)

        


        # To make sure the log files and video recordings start in the same minute, if there are less than 3 seconds left until the start of the next minute, pause for 3 seconds.
        if datetime.datetime.now().second >= 57:
            time.sleep(3)

        can_logging = subprocess.Popen(['/home/ganindu/.pyenv/versions/AIPY/bin/python3', '/mnt/ssd-1/workspace/jetson-deepstream/bscripts/logging/can_logging/log_can_msgs.py']) #, stdout=subprocess.PIPE, stderr=subprocess.PIPE) 
        video_rec = subprocess.Popen(['/home/ganindu/.pyenv/versions/AIPY/bin/python3', '/mnt/ssd-1/workspace/jetson-deepstream/bscripts/logging/video_recording/record_videos.py']) #, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging = True


    if not data['logging_settings'][0]['logging_mode'] and logging:
        print("Stopping logging ...")
        os.kill(can_logging.pid, signal.SIGINT)
        os.kill(video_rec.pid, signal.SIGINT)
        logging = False





def delete_corrupted_files():
    """ 
        Checks if there are corrupted files in the log dir.
    """

    with open(config_file) as f:
        data = yaml.load(f, Loader=SafeLoader) 

    data_dir = data['logging_settings'][2]['logged_data_dir']


    for video_file in [file for file in data_dir if file.endswith("mp4")]:
        if not cv2.VideoCapture(os.path.join(data_dir, video_file)).isOpened():
            os.remove(os.path.join(data_dir, video_file))
            try:
                os.remove(os.path.join(data_dir, f'{"_".join(video_file.split("_")[1:-1])}.log'))
            except:
                pass
 



# **************************************************** The main logging controller ****************************************************

# Make sure the serial number is found before starting any data logging.
os.system("/home/ganindu/.pyenv/versions/AIPY/bin/python3 /mnt/ssd-1/workspace/jetson-deepstream/bscripts/logging/find_serial_number/set_serial_number.py")

logging = False
can_logging = None
video_rec = None

config_file = '/mnt/ssd-1/workspace/jetson-deepstream/bscripts/logging/logging_config.yaml' 

signal.signal(signal.SIGINT, stop_logging)

delete_corrupted_files()

manage_logging()



# ----------------------- Set the interrupt that is triggered when the config file changes  ----------------------- 

class EventHandler(pyinotify.ProcessEvent):
    """
        Handles any changes made to the config file.
    """
    def process_IN_MODIFY(self, event):
        print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!IN_MODIFY event:", event.pathname)

        manage_logging()


# Create an instance of the EventHandler
handler = EventHandler()

# Create a WatchManager and Notifier
wm = pyinotify.WatchManager()
notifier = pyinotify.Notifier(wm, handler) 

# Add a watch for the file you want to monitor
wm.add_watch(config_file, pyinotify.IN_MODIFY)

# Start the monitoring process
notifier.loop()


