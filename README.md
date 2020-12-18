# CS552 Final Project - Evaluation of the effect of Queuing Discipline upon Telesurgery traffic
This project seeks to understand the impact of the queuing discipline used by routers carrying telesurgery traffic in a congested environment; specifically upon synchronized video flows. The software in this repo simulates a pair of synchronized, compressed 1080p video streams, sending a packetized frame from each stream every 33ms to achieve 30 frames per second in each flow.

The software consists of a program simulating the patient side (generating the video) and a program simulating the surgeon side (receiving the video.) The surgeon-side program is implemented in Python, and the patient-side program is implemented in C.

## Building the software
The patient-side program must be compiled from source. The included Makefile should work out of the box.

## The testbed environment
This workflow is designed and configured to run on CloudLab infrastructure. This repo includes an experiment profile, `profile1.xml` that can be used to reproduce the experimental environment. The profile creates patient and surgeon machines, as well as dedicated interference machines and a software router in the middle.

The script `deps.sh` should be run on the patient and surgeon nodes before the simulation is run. This installs necessary programs, libraries, and python modules.

## Running the simulation
The surgeon program (`usurgeon.py`) should be run on the surgeon node and the patient program (`patient`) should be run on the patient node. `patient` should be started before `usurgeon`. 

### Running `patient`
`patient` needs to be run with either sudo or root access. It takes two arguments: the interface to listen on and its output file. Runs of `patient` end up looking like:

`sudo ./patient vlan1132 patient.dat`

If you are using the included CloudLab profile, `vlan1132` should be replaced with whichever address is carrying the IP `10.10.2.2`. To work with the results-collecting script, the output file should have the format `patient_<something>.dat`, where <something> is arbitrary.

### Running `usurgeon.py`
`usurgeon.py` takes two arguments: the target IP (the one that `patient` is listening on) and an output file. If you are using the attached `profile1.xml`, this looks like:

`./usurgeon.py 10.10.2.2 surgeon.dat`

To work with the results-collecting script, the output file should have the format `surgeon_<something>.dat`, where <something> matches whatever was used in `patient`.

If everything works correcltly, you will see the two programs marching through 300 frames in lockstep:

patient side:
```
24300 packets total in the stream.
24300 packets total in the stream.
waiting for surgeon
waiting for surgeon
0
0
1
1
2
2
3
...
296
296
297
297
298
298
299
299
300
300
```

surgeon side:
```
sent
sent
0
0
1
1
2
2
3
3
4
4
5
5
6
...
297
297
298
298
299
299
300
300
got terminator
got terminator
done
done
```

It is normal and expected that each number will appear twice.

## Adding interference traffic
There are two nodes for generating interference traffic. Traffic sent in the direction `interfere-2 -> interfere-1` will be competetive with the video stream traffic. The `iperf` utility can be used to generate this interfering traffic.

On `interfere-1`, run `iperf -s -u`, and on `interfere-2` run `iperf -c 10.10.1.2 -u -b 20m -t 600 -i 10`. This will generate 10 minutes of 20Mbit/s UDP traffic. This should be running during all non-baseline experiments.

## Adding congestion and configuring queuing disciplines
The script `traffic_control_r1.bash` should be run on the `router` node. This is an interactive script that will iteratively configure different queuing displines, waiting for the user to run the simulation and retrieve results at each different configuration. `traffic_control_r1.bash` takes an argument of the surgeon-facing interface; in the Cloudlab profile, it is the interface that carries `10.10.1.1`.

## Collecting results
The `generate_results.sh` will analyze the ouputs of `patient` and `surgeon.py` and package-up graphs and data in a tarball for easy export. `generate_results.sh` takes a single argument: the suffix that was used in the patient and surgeon output files, i.e. <something> in `patient_<something>.dat`. This will produce `<something>.tar` with the following contents:
  
```
<something>.dir/
   <something>.txt - summary statistics
   results_<something>.csv - a comma-seperated list of <something>,average disparity, max disparity, stdev of disparity
   
   pkt_disp_<something>.png - TX- and RX-side disparities over time graphed together based on NIC timers
   
   net_pkt_disp_<something>.png - difference between TX and RX-side disparities based on NIC timers
   
   net_pkt_hist_<something>.png - histogram of the net_pkt_disp_<something> data
   
   stack_pkt_disp_<something>.png - difference between disparity measured by RX NIC timer and disparity measured in the application using software timers.
   
   latency_net_<something>.png - a graph of net disparity as measured at the NIC vs average latency of the pair of packets
   The original data files from the two applications.
```







 

