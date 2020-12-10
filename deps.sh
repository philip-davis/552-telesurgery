#!/bin/bash

sudo apt-get update
sudo apt install -y python3-pip python3-opencv iperf ffmpeg linux-tools-common linux-tools-4.15.0-121-generic
sudo pip3 install imagezmq zmq shutils numpy pythonping
