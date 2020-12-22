#!/bin/bash

sudo apt-get update
sudo apt install git
cd /root
rm -rf 552-telesurgery-*
git clone  https://github.com/philip-davis/552-telesurgery.git
git --git-dir /root/552-telesurgery checkout postdev
