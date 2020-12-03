#!/bin/bash

sudo apt-get update
sudo apt install -y python3-pip python3-opencv iperf ffmpeg
sudo pip3 install imagezmq zmq shutils numpy pythonping
