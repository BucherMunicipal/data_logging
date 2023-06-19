#!/bin/bash 

echo 373 > /sys/class/gpio/export # export the gpio pin 


/usr/bin/sudo busybox devmem 0x0c303010 w 0x400
/usr/bin/sudo busybox devmem 0x0c303018 w 0x458
# add can drivers to the kernel 
/usr/bin/sudo /usr/sbin/modprobe can
/usr/bin/sudo /usr/sbin/modprobe can_raw
/usr/bin/sudo /usr/sbin/modprobe mttcan
# setup and bring up can0 interface 
/usr/bin/sudo ip link set can0 type can bitrate 250000 berr-reporting on restart-ms 2000 
/usr/bin/sudo ip link set can0 up 
