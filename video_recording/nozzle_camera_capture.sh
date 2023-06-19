#!/bin/bash

# The Gstreamer pipeline that records videos.

exec gst-launch-1.0 -e nvv4l2camerasrc device=$1 ! \
	queue flush-on-eos=True max-size-buffers=1 ! \
	nvvideoconvert ! \
	nvv4l2h264enc bitrate=6000000 insert-sps-pps=1 qos=True  ! \
	h264parse ! \
	splitmuxsink location="$2/$3_$4_$(date '+%Y_%m_%d_%H%M')_0001.mp4" max-files=1 max-size-time=$(($5 * 1000000000))



 