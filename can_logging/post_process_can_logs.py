"""
    Processes the CAN log files and saves them in a format similar to the vbo files.

    Author: Bouchra Mohamed Lemine

"""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timezone
import yaml
from yaml.loader import SafeLoader
import time
import cv2
import sys



while True:
    
    with open("/home/g/workdisk/workspace/jetson-deepstream/bscripts/logging/logging_config.yaml", "r") as yamlfile:
        data = yaml.load(yamlfile, Loader=SafeLoader)
        max_logging_secs = data['logging_settings'][1]['max_log_duration'] 
        data_dir = data['logging_settings'][2]['logged_data_dir']
        logging_device = data['device_info'][0]['device_name']
        used_cameras = data['camera_info'][0]['used_cameras']
        yamlfile.close()
        
    
    for log_file in [x for x in os.listdir(data_dir) if x.endswith("csv")]:
        if all(cv2.VideoCapture(os.path.join(data_dir, video_file)).isOpened() for video_file in [file for file in os.listdir(data_dir) if (log_file.split(".")[0] in file and file.endswith("mp4"))]):

            time.sleep(1) # wait to make sure logging has completley stopped.

            try:

                df = pd.read_csv(os.path.join(data_dir, log_file))

                # Write the header data to this file.
                with open(os.path.join(data_dir, f'{log_file.split(".")[0]}.log'), "w") as f:
                    f.write(f"[device]\n{logging_device}\n\n[cameras]\n{used_cameras}\n\n[AVI]\n{log_file.split('.')[0]}_\n\n[column names]\n{' '.join(df.columns)}\n\n[data]\n")


                # Only do the post-processing if the df is not empty.
                if not df.empty: 

                    # If not all the column values are set in the last line, remove the last value if there is not a comma after it because that it is likely to not be correct. 
                    with open(os.path.join(data_dir, log_file), "r") as f: 
                        last_line = f.readlines()[-1].split(",")
                        if len(last_line) < len(df.columns) and last_line[-1] != ",":
                            df.loc[-1, len(last_line) - 1] = np.nan


                    # *********************** Group the df by time. If 2 rows have the same timestamp, merge them by keeping values in the last one. 
                    aggregation_functions = dict.fromkeys(df.columns, "last")   
                    df = df.groupby(df['time']).aggregate(aggregation_functions)


                    # *********************** Read the first and last time stamps in a datetime format.
                    start_time = datetime.combine(datetime.today(), datetime.strptime(df['time'].iloc[0], '%H:%M:%S.%f').time())
                    end_time = datetime.combine(datetime.today(), datetime.strptime(df['time'].iloc[-1], '%H:%M:%S.%f').time())


                    # *********************** Convert the start_time and end_time to Unix timestamps to make it easier to create a linear distribution from them.
                    start_timestamp = start_time.timestamp()
                    end_timestamp = end_time.timestamp()


                    # *********************** Create an evenly spaced list of all the timestamps that must be in the log file.
                    uniform_list = np.arange(start_timestamp, end_timestamp + 0.15, 0.1)


                    # *********************** Convert the Unix timestamps back to the original format.
                    uniform_time_list = [f"{datetime.fromtimestamp(ts).strftime('%H:%M:%S.%f')[:-5]}00" for ts in uniform_list]


                    # *********************** Create a df with all the timestamps. If CAN messages were received at a timestamp, copy them to the df, otherwise set their values to null. 
                    df = pd.DataFrame(list(map(lambda x: dict.fromkeys(df.columns, np.nan) if x not in list(df["time"]) else dict(zip(df.columns, df.loc[df['time'] == x].values.tolist()[0])), uniform_time_list)))
                    df["time"] = uniform_time_list


                    # *********************** Add the aviindex column (constant because the is only 1 video associated with each log file)
                    df["avifileindex"] = "0001"


                    # *********************** fill nul values
                    df.fillna(method="ffill", inplace = True)
                    df.fillna(method="bfill", inplace = True)


                    # *********************** If a signal was not logged at all, set it to the default value 0.
                    df.fillna(value=0, inplace = True)
                

                    # *********************** Save the df in a file 
                    df.to_csv(os.path.join(data_dir, f'{log_file.split(".")[0]}.log'), mode = "a", index = False, header = False, sep = " ")


                # Remove the original csv file.
                os.remove(os.path.join(data_dir, log_file))

            

            except Exception as e:
                print("Exception while post-processing log files .............", e)



