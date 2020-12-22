#!/bin/bash

sudo apt-get update
sudo apt install git
cd ..
rm -rf 552-telesurgery-*
git clone  https://github.com/philip-davis/552-telesurgery.git
