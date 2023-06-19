
#!/bin/bash

#
# The script that is run by the systemd service to continuously log data while the device is powered up.
# 
# AUTHOR: Bouchra Mohamed Lemine
#


# Run the logging controller
/home/ganindu/.pyenv/versions/AIPY/bin/python3 /mnt/ssd-1/workspace/jetson-deepstream/bscripts/logging/logging_controller.py &


# Keep checking until the gpio pin value becomes 0, and then gracefully stop the logging and shut down the device.
while [ 1 = 1 ]; do

if [ $(cat /sys/class/gpio/PG.02/value) = 0 ]; then

echo "Going to poweroff the device"
kill -INT $! 
wait
echo "Stopped logging"
sudo poweroff

fi

done
