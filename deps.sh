#!/bin/bash

sudo apt-get update
sudo apt install -y python3-pip python3-opencv iperf ffmpeg linux-tools-common linux-tools-5.4.0-51-generic
sudo pip3 install imagezmq zmq shutils numpy pythonping matplotlib
