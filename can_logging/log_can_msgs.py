"""
    Logs CAN messages sent on the telematics bus in a csv file. 

    Author: Bouchra Mohamed Lemine
"""

import time
from random import random
import can
import cantools
import subprocess
from multiprocessing import Process, Lock, cpu_count, Pool, active_children, current_process
from can.interface import Bus
import datetime
import threading
import os
import numpy as np 
import csv
import yaml
from yaml.loader import SafeLoader
import signal
import sys
from threading import Thread
from datasize import DataSize




# The list of the CAN signals that will be logged (they will be saved in the log file in this order).
columns = [
"time", "avifileindex", "Longitude", "Latitude", "Altitude", "Satellites", "Heading", "Nozzle1downTMSCS", "Nozzle2downTMS", "SideBrush1downTMS", "SideBrush2downTMS", "BrushCurrent", "SideBrush1ExtendTMSCS", 
"SideBrush2ExtendTMSCS", "SideBrush1RetractTMSCS", "SideBrush2RetractTMSCS", "Nozzle1WaterSprayOnOffTMS", "Nozzle2WaterSprayOnOffTMS", 
"SideBrush1WaterSprayTMS", "SideBrush2WaterSprayTMS", "WSBMotoronoffTMS", "FanOnTMS", "WorkLight1OnOffTMS", "WorkLight2OnOffTMS", "NozGapOpen", 
"NozGapClose", "Pause_active", "AutoSweepActive", "EngineType", "EngineSpeed", "RoadSpeedTMSCS", "EngineFuelRateTMSCS", "FanSpeed", "TotalFuelConsumption", "WaterTankLevel", 
"JVMheartbeat", "JVMALerts", "modbus_id", "pm_sensor_serious_fault", "pm_sensor_fault", "pm_sensor_is_degraded_mode", 
"pm_sensor_is_ready", "pm_1", "pm_2_5", "pm_10", "temperature", "firmware_version", "humidity", "error"
]


# Filter the messages read by the device to only include the ones that will be saved in the log files.
filters = [
    {"can_id": 0x203, "can_mask": 0xFFF, "extended": False},
    {"can_id": 0x202, "can_mask": 0xFFF, "extended": False},
    {"can_id": 0x303, "can_mask": 0xFFF, "extended": False},
    {"can_id": 0x714, "can_mask": 0xFFF, "extended": False},
    {"can_id": 0x505, "can_mask": 0xFFF, "extended": False},
    {"can_id": 0x504, "can_mask": 0xFFF, "extended": False},
    {"can_id": 0x403, "can_mask": 0xFFF, "extended": False},
    {"can_id": 0x123, "can_mask": 0xFFF, "extended": False},
    {"can_id": 0x456, "can_mask": 0xFFF, "extended": False},
    {"can_id": 0x100, "can_mask": 0xFFF, "extended": False},
    {"can_id": 0x101, "can_mask": 0xFFF, "extended": False},
    {"can_id": 0x102, "can_mask": 0xFFF, "extended": False}
]

# Create a can bus instance.
bus = Bus(interface = 'socketcan', channel = 'can0', bitrate = 250000, can_filters = filters)

# Create a CAN data decoder using the DBC file.
db = cantools.database.load_file('/mnt/ssd-1/workspace/jetson-deepstream/bscripts/logging/logged_can_signals_16_02_2023.DBC')





def parse_config_file():
    """
        Reads and returns the vehicle's serial number that will form part of the log file's name, the log duration, the path to the folder that the log files must be saved in, the logging device name and the cameras used.
    """

    with open("/mnt/ssd-1/workspace/jetson-deepstream/bscripts/logging/logging_config.yaml", "r") as yamlfile:
        data = yaml.load(yamlfile, Loader=SafeLoader)
        yamlfile.close()
        return  data['logging_settings'][2]['logged_data_dir'], data['logging_settings'][1]['max_log_duration'], data['vehicle_info'][0]['serial_number'], data['device_info'][0]['device_name'], " ".join(data['camera_info'][0]['used_cameras'])





def log_can_messages():
    """
        The task that the 8  processes are running. It logs every received CAN message to the same log file.
    """

    with open(file_name, 'a') as f:

        while True:
            try:     
                # Decode the CAN message.           
                msg = bus.recv()
                can_msg_dict = db.decode_message(msg.arbitration_id, msg.data)


                # print("**************************************", can_msg_dict)

                # Create a dict with null values except the time.
                data_dict = dict.fromkeys(columns, np.nan) 
                data_dict["time"] = f'{datetime.datetime.now().strftime("%H:%M:%S.%f")[:-5]}00'

                # Update the dict keys with the received CAN messages.
                for key in can_msg_dict:
                    if key in data_dict:
                        data_dict[key] = can_msg_dict[key] 

                # Append dict values to the log file.
                # csv.DictWriter(f, data_dict.keys()).writerow(data_dict)
                f.write('\n' + ','.join(str(x) for x in list(data_dict.values())))

                f.flush() 
    
            except Exception as e:
                print(e)
                # pass

            



def signal_handler(sig, frame):
    """
        Handles the sigint interrupt that can be sent from the logging_controller.py process or the keyboard.
    """
    print("*************************************** Handling Keyboard Interrupt **************************************") 

    try:

        pool.terminate() # Terminate the processes logging CAN messages 
    
        with open(file_name, "a+") as f:
            f.seek(0) # go to the top of the file before reading.
            # Write the last line to the log file only if it has some data.
            if len(f.readlines()) > 1:
                f.write("\n" + ",".join([f'{datetime.datetime.now().strftime("%H:%M:%S.%f")[:-5]}00'] + [str(np.nan) for _ in columns[1:]]))
            
            f.close()
        
        
        # Wait for the log file processing to complete before exiting.
        subprocess.call(['/home/ganindu/.pyenv/versions/AIPY/bin/python3', '/mnt/ssd-1/workspace/jetson-deepstream/bscripts/logging/can_logging/post_process_can_logs.py', file_name, logging_device, used_cameras])

    except Exception as e: 
        print("!!!!!!!!!!!!!!!!!!!!!!!! Exception while terminating the CAN message logging", e) 

    print("exiting now")

    sys.exit(0)
 




if __name__ == '__main__':

    signal.signal(signal.SIGINT, signal_handler)

    while True:

        log_dir, log_duration, serial_number, logging_device, used_cameras = parse_config_file()

        # Before starting a new logging session, check if there is enough space left on the SD card. If there isn't, don't log any data
        if DataSize(os.popen(f"df -H {log_dir} | awk '{{print $4}}'").read().split("\n")[1]) > DataSize(f"{log_duration / 600}G"):

            print("****************** Writing to a CAN log file")

            # Create an empty file to be logged to.
            file_name = f'{serial_number}_{str("_".join(str(datetime.datetime.now()).split(" ")).split(".")[0][:-2]).replace("-", "_").replace(":", "")}.csv'  
            
            file_name = os.path.join(log_dir, file_name)
            
            # Write the header row to this file if it is empty.
            #if not os.path.exists(file_name) or os.stat(file_name).st_size == 0:
            with open(file_name, "w") as f:
                f.write(f'{",".join(columns)}\n')
                f.write(",".join([f'{datetime.datetime.now().strftime("%H:%M:%S.%f")[:-5]}00'] + [str(np.nan) for _ in columns[1:]]))


            # Create a pool of processes and start it.
            pool = Pool(processes=8)
            pool.apply_async(log_can_messages)

            time.sleep(log_duration - 0.2)

            pool.terminate()

            # Write a line of null values (except time) to the log file to know when logging stopped, which is important when syncing log files with videos. 
            with open(file_name, "a") as f:
                f.write("\n" + ",".join([f'{datetime.datetime.now().strftime("%H:%M:%S.%f")[:-5]}00'] + [str(np.nan) for _ in columns[1:]]))
                f.close()


            # Process this log file to give it a format similar to the vbo files, while starting with the next logging session.
            thread = Thread(target = lambda: subprocess.Popen(['/home/ganindu/.pyenv/versions/AIPY/bin/python3', '/mnt/ssd-1/workspace/jetson-deepstream/bscripts/logging/can_logging/post_process_can_logs.py', file_name, logging_device, used_cameras]))
            thread.start()


        # If there is no space left on the device, exit this CAN logging program.
        else:
            print("No space left on the device !!!!!!!!!!!!!!!!!!!!!!!")

            try:
                thread.join() 
            except:
                pass
            sys.exit(0)
        

    

