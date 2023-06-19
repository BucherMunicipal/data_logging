# Data Logging
Logs the videos and CAN signals and saves them as video-log_file pairs similar to the VBOX log files.

# File Overview
- `logging_controller.py`: the main program that manages logging.  
- `logging_config.yaml`: the config file that includes all the settings required to log data. 
- `can_logging/`: has the scripts that log CAN messages and post-process them to have a format live the VBO files. 
- `find_serial_number/`: contains the script that reads the serial number of the vehicle and saves it in the config file. 
- `set_device_time/`: ensures the device time is synced with the Proemion time by setting it every hour if it drifts.   
- `video_recording`: contains the gstreamer pipleine used to log the camera's input and the python script that runs it.
- `startup_services`: contains the systemd services that automate all the functions mentioned above.


# Dependencies

Create a pyenv virtual environment with the name ```AIPY```. Inside this venv install the packages below:
* [python-can](https://pypi.org/project/python-can/) 
* [cantools](https://pypi.org/project/cantools/) 
* [yaml](https://pypi.org/project/PyYAML/)
* [ruamel.yaml](https://pypi.org/project/ruamel.yaml/) 
* [pandas](https://pypi.org/project/pandas/)
* [numpy](https://pypi.org/project/numpy/)
* [opencv-python](https://pypi.org/project/opencv-python/)


# Autostartup
1. Copy the 3 services to ```/etc/systemd/system```<br>
2. Grant each service the necessary permissions - ```chmod 644 service_file_name```  
3. Make the services run when the device is booted. ```systemctl enable service_file_name```  

 
## @boot
[can_setup.service](startup_services/can_setup.service) - runs a shell scripts that sets CAN cummunication on can0.<br>
&darr;<br>
[setting_device_time.service](startup_services/setting_device_time.service) - runs a python script that sets the device time every hour if it drifts.<br>
[logging.service](startup_services/logging.service) - logs videos and CAN messages for the max_duration defined in the config file, while logging_mode = 1.




# Notes 
* The device time is set to GMT time. 

* Logging only starts after the serial number is found, therefore, since the cycle time of the CAN message that sends the serial number is 3 seconds, it might take up to 3 seconds to start logging when logging for the first time the serial number is set.   

* To stop or start logging, set ```loggig_mode``` in the config file to 0 or 1, respectively, instead of stopping and starting the ```logging``` service. 

 
 