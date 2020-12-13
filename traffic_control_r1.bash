#!/bin/bash


# set interface var for bottleneck link to surgeon

IF_r1_bottleneck=eth1 #10.10.5.1


# set max link rate to 50 Mbps with htb qdisc; this will remain throughout all the tests

sudo tc qdisc add dev $IF_r1_bottleneck root handle 1: htb default 1

sudo tc class add dev $IF_r1_bottleneck parent 1: classid 1:1 htb rate 50Mbit


############

# FUNCTIONS


# remove current qdisc on router, but keep the htb max link rate

clean () {

	echo "======================================"

	echo "Cleaning qdisc for next test..."

	sudo tc qdisc del dev $IF_r1_bottleneck parent 1:1

	echo "The qdisc has been reset"

	echo "======================================"

}


# pause to allow user to run patient/surgeon scripts

run () {

	echo "Please run patient and server programs now [$1]"

	read -p "Once ready, press any key to continue... " -n1 -s

	echo ""

}


############

# CLASSLESS TESTS


run "baseline test"


# set up a netem qdisc with delay to ensure setup works properly

clean

sudo tc qdisc add dev $IF_r1_bottleneck parent 1:1 handle 10: netem delay 200ms


run "200ms delay test"


# set up a pfifo qdisc with 30p buffer

clean

sudo tc qdisc add dev $IF_r1_bottleneck parent 1:1 handle 10: pfifo limit 30


run "pfifo w/ 30p buffer"


# set up a pfifo_fast qdisc

clean

sudo tc qdisc add dev $IF_r1_bottleneck parent 1:1 handle 10: pfifo_fast


run "pfifo_fast"


# set up a fq qdisc

clean

sudo tc qdisc add dev $IF_r1_bottleneck parent 1:1 handle 10: fq


run "fair queue"


# set up an sfq qdisc

clean

sudo tc qdisc add dev $IF_r1_bottleneck parent 1:1 handle 10: sfq


run "stochastic fair queue"


# set up a hhf qdisc

clean

sudo tc qdisc add dev $IF_r1_bottleneck parent 1:1 handle 10: hhf


run "heavy-hitter filter"


############

# CLASSFUL TESTS


# set up a prio qdisc

clean

sudo tc qdisc add dev $IF_r1_bottleneck parent 1:1 handle 10: prio

sudo tc qdisc add dev $IF_r1_bottleneck parent 10:1 handle 100: sfq

sudo tc qdisc add dev $IF_r1_bottleneck parent 10:2 handle 200: sfq

sudo tc qdisc add dev $IF_r1_bottleneck parent 10:3 handle 300: sfq


run "prio"


# set up an htb qdisc

#clean

#################################################################sudo tc qdisc add dev $IF_r1_bottleneck parent 1:1 handle 10: htb


#run "htb"
