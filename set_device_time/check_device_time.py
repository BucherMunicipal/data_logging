"""
    Sets the logging device time to the Proemion time if it is different from it, by checking if they are the same every hour.

    Author: Bouchra Mohamed Lemine
"""


import os
import time


while True:
    os.system("/home/ganindu/.pyenv/versions/AIPY/bin/python3 /mnt/ssd-1/workspace/jetson-deepstream/bscripts/logging/set_device_time/set_time.py")
    time.sleep(3600)


