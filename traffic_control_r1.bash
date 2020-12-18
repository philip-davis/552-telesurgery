#!/bin/bash


# set interface var for bottleneck link to surgeon

if [[ $# -ne 1 ]] ; then
    echo "need the congestion interface as an argument"
    exit -1
fi

IF_r1_bottleneck=$1


############

# FUNCTIONS


clean () {

	echo "======================================"

	echo "Cleaning qdiscs to setup..."

	sudo tc qdisc del dev $IF_r1_bottleneck root

	echo "All qdiscs have been reset"

	echo "======================================"

}


# remove current qdisc on router, but keep the htb max link rate

reset_qdisc () {

	echo "======================================"

	echo "Resetting qdisc for next test..."

	sudo tc qdisc del dev $IF_r1_bottleneck parent 1:1

	echo "The qdisc has been reset"

	echo "======================================"

}


# set max link rate to 50 Mbps with htb qdisc; this will remain throughout all the tests

setup () {

	sudo tc qdisc add dev $IF_r1_bottleneck root handle 1: htb default 1

	sudo tc class add dev $IF_r1_bottleneck parent 1: classid 1:1 htb rate 50Mbit

}


# pause to allow user to run patient/surgeon scripts

run () {

	echo "Please run patient and server programs now [$1]"

	read -p "Once ready, press any key to continue... " -n1 -s

	echo ""

}


############

# CLASSLESS TESTS


clean


run "default: pfifo_fast"


setup


# set up a netem qdisc with delay to ensure setup works properly

sudo tc qdisc add dev $IF_r1_bottleneck parent 1:1 handle 10: netem delay 200ms


run "200ms delay test"


# set up a pfifo qdisc with 30p buffer

reset_qdisc

sudo tc qdisc add dev $IF_r1_bottleneck parent 1:1 handle 10: pfifo limit 30


run "pfifo w/ 30p buffer"


# set up a fq qdisc

reset_qdisc

sudo tc qdisc add dev $IF_r1_bottleneck parent 1:1 handle 10: fq


run "fair queue"


# set up an sfq qdisc

reset_qdisc

sudo tc qdisc add dev $IF_r1_bottleneck parent 1:1 handle 10: sfq


run "stochastic fair queue"


# set up a hhf qdisc

reset_qdisc

sudo tc qdisc add dev $IF_r1_bottleneck parent 1:1 handle 10: hhf


run "heavy-hitter filter"


############

# CLASSFUL TESTS


# set up a prio qdisc

reset_qdisc

sudo tc qdisc add dev $IF_r1_bottleneck parent 1:1 handle 10: prio

sudo tc qdisc add dev $IF_r1_bottleneck parent 10:1 handle 100: sfq

sudo tc qdisc add dev $IF_r1_bottleneck parent 10:2 handle 200: sfq

sudo tc qdisc add dev $IF_r1_bottleneck parent 10:3 handle 300: sfq


run "prio"


# set up an htb qdisc

reset_qdisc

sudo tc qdisc del dev $IF_r1_bottleneck root

sudo tc qdisc add dev $IF_r1_bottleneck root handle 10: htb default 300
sudo tc class add dev $IF_r1_bottleneck parent 10: classid 10:1 htb rate 50Mbit burst 256000
sudo tc class add dev $IF_r1_bottleneck parent 10:1 classid 10:100 htb rate 20Mbit burst 128000 prio 1 ceil 50Mbit
sudo tc class add dev $IF_r1_bottleneck parent 10:1 classid 10:200 htb rate 20Mbit burst 128000 prio 1 ceil 50Mbit
sudo tc class add dev $IF_r1_bottleneck parent 10:1 classid 10:300 htb rate 10Mbit ceil 25Mbit prio 2
sudo tc qdisc add dev $IF_r1_bottleneck parent 10:100 handle 100: pfifo limit 30
sudo tc qdisc add dev $IF_r1_bottleneck parent 10:200 handle 200: pfifo limit 30
sudo tc qdisc add dev $IF_r1_bottleneck parent 10:300 handle 300: pfifo limit 30
sudo tc filter add dev $IF_r1_bottleneck protocol ip parent 10:0 prio 1 u32 match ip sport 5555 0xffff flowid 10:100
sudo tc filter add dev $IF_r1_bottleneck protocol ip parent 10:0 prio 1 u32 match ip sport 5556 0xffff flowid 10:200

run "htb"
