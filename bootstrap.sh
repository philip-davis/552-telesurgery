#!/bin/bash

sudo apt-get update
sudo apt install git
cd /root
rm -rf 552-telesurgery-*
git clone  https://github.com/philip-davis/552-telesurgery.git
git --git-dir /root/552-telesurgery checkout postdev

# Retrieve the server-generated RSA private key.
geni-get key > $HOME/.ssh/id_rsa
chmod 600 $HOME/.ssh/id_rsa

# Derive the corresponding public key portion.
ssh-keygen -y -f $HOME/.ssh/id_rsa > $HOME/.ssh/id_rsa.pub

# If you want to permit login authenticated by the auto-generated key,
# then append the public half to the authorized_keys file:
grep -q -f $HOME/.ssh/id_rsa.pub $HOME/.ssh/authorized_keys || cat $HOME/.ssh/id_rsa.pub >> $HOME/.ssh/authorized_keys
