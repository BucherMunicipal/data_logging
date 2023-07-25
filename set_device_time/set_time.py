"""
    Sets the logging device time to the Proemion device time if they are different. 

    Author: Bouchra Mohamed Lemine
"""

import can
import cantools
from can.interface import Bus
import os
import math
import datetime




def unix_time_to_GMT(unix_time):
    """
    Converts the number of seconds since the Unix epoch to the current date and time (GMT time).
    """

    def get_seconds_in_months(year):
        return [2678400,  2505600 if (year - 2020)%4 == 0 else 2419200, 2678400, 2592000, 2678400, 2592000, 2678400, 2678400, 2592000, 2678400, 2592000, 2678400]

    # Getting the year 
    seconds_in_year = unix_time - 1672531200
    x = seconds_in_year
    i = 0
    while x >= sum(get_seconds_in_months(2023 + i)):
        x -= sum(get_seconds_in_months(2023 + i))
        i += 1
    year = i + 2023

    for i in range(year - 2023):
        seconds_in_year -= (sum(get_seconds_in_months(2023 + i)))

    # Getting the month 
    month = 1
    x = seconds_in_year
    while x >= get_seconds_in_months(year)[month - 1]:
        x -= get_seconds_in_months(year)[month - 1]
        if month < 12:
            month += 1
        else:
            month = 1

    if x - get_seconds_in_months(year)[month - 1] == -3600:
        month += 1

    # Getting the day
    day = math.ceil((seconds_in_year - sum(get_seconds_in_months(year)[:month - 1])) / 86400)

    # Getting the GMT time 
    seconds_in_day = seconds_in_year - (86400 * (seconds_in_year // 86400))
    hour = seconds_in_day // 3600
    minutes = (seconds_in_day - 3600 * hour) // 60
    seconds = seconds_in_day - 60 * (minutes + hour * 60)

    return f"{year}-{month}-{day} {hour}:{minutes}:{seconds}"





def set_date_time():
    """
    Decodes the date & time sent by the proemion and compares them to date & time on the logging device. 
    """

    while True:
        try:
            msg = bus.recv()
            unix_time = db.decode_message(msg.arbitration_id, msg.data)["Unix_time"]

            if int(str(datetime.datetime.now().timestamp()).split(".")[0]) != int(unix_time):
                # Run a command to set the date & time.
                os.system(f"/usr/bin/sudo date -s '{unix_time_to_GMT(unix_time + 1)}'")

            break

        except Exception as e:
            print(e)




if __name__ == "__main__":

    can.rc['interface'] = 'socketcan'
    can.rc['channel'] = 'can0'
    can.rc['bitrate'] = 250000
    can.rc['can_filters'] = [{"can_id": 0x100, "can_mask": 0xFFF, "extended": False}]

    bus = Bus()

    # Create a CAN message decoder using the DBC file.
    db = cantools.database.load_file('/mnt/ssd-1/workspace/jetson-deepstream/bscripts/logging/logged_can_signals_25_07_2023.DBC')

    set_date_time()


                                                                                                       
