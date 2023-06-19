"""
    Controls logging and log file reformatting.
    Starts logging data everytime the logging_mode in the config file is set to 1 and stops when it is set to 0, 
    but it only stops processing log files after an amount of time equals to the max_log_duration / 120 to make sure all logs are reformatted while the device is powered up.

    Author: Bouchra Mohamed Lemine

"""

import os
import signal 
import subprocess 
import time
from threading import Thread
import yaml
from yaml.loader import SafeLoader




"""

if power fail flag is set:

    if logging:
        kill logging process
         
    
    if reformatting: 
        wait 5 secs 
        kill post_processing process
    
    
    exit


"""

power_fail_flag = 0



# Make sure the serial number is found before starting any data logging.
os.system("/home/g/.pyenv/versions/AIPY/bin/python3 /home/g/workdisk/workspace/jetson-deepstream/bscripts/logging/find_serial_number/set_serial_number.py")


logging = False
processing_log_files = False 



def stop_processing(process):
    print(f"************* Going to stop reformatting after 5 seconds ***************")
    
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1 wait for the maximum amount of time it can take to process a log file
    
    time.sleep(5) # 5 seconds is the time it takes to reformat a 10 minutes log. 
    os.kill(process.pid, signal.SIGINT)

    global processing_log_files 
    processing_log_files = False

    print("************************ Post-processing is", processing_log_files)


 

while True:
    try:
        if os.popen("cat /sys/class/gpio/PG.02/value").read():
            if logging:
                os.kill(can_logging.pid, signal.SIGINT)
                os.kill(video_rec.pid, signal.SIGINT)
            
            if processing_log_files:
                time.sleep(5) # 5 seconds is the time it takes to reformat a 10 minutes log. 
                os.kill(log_file_processing.pid, signal.SIGINT)                                            

            os.system("/usr/bin/sudo poweroff")



        with open('/home/g/workdisk/workspace/jetson-deepstream/bscripts/logging/logging_config.yaml') as f:
            data = yaml.load(f, Loader=SafeLoader)
    
            if data['logging_settings'][0]['logging_mode'] and not logging:
                print("starting .....")
                can_logging = subprocess.Popen(['/home/g/.pyenv/versions/AIPY/bin/python3', '/home/g/workdisk/workspace/jetson-deepstream/bscripts/logging/can_logging/log_can_msgs.py']) #, stdout=subprocess.PIPE, stderr=subprocess.PIPE) 
                video_rec = subprocess.Popen(['/home/g/.pyenv/versions/AIPY/bin/python3', "/home/g/workdisk/workspace/jetson-deepstream/bscripts/logging/video_recording/record_videos.py"]) #, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                logging = True

            if data['logging_settings'][0]['logging_mode'] and not processing_log_files:
                print("Reformatting ...")
                log_file_processing = subprocess.Popen(['/home/g/.pyenv/versions/AIPY/bin/python3', '/home/g/workdisk/workspace/jetson-deepstream/bscripts/logging/can_logging/post_process_can_logs.py']) #, stdout=subprocess.PIPE, stderr=subprocess.PIPE) 
                processing_log_files = True
            

            if not data['logging_settings'][0]['logging_mode'] and logging:
                print("Stopping ...")
                os.kill(can_logging.pid, signal.SIGINT)
                os.kill(video_rec.pid, signal.SIGINT)

                logging = False

                # Run a thread that stops post processing log files after max_log_duration / 2. 
                thread = Thread(target = stop_processing, args = (log_file_processing, ))
                thread.start()
            

    
    except Exception as e:
        print("!!!!!!!!!!!!!!!!!!! Exception !!!!!!!!!!!!!!!!!!!", e)
        continue

