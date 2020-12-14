#!/usr/bin/python3

import matplotlib.pyplot as plt
from statistics import stdev
import pickle
import sys
import numpy as np

def get_arrival_time(frame):
    if frame['dcount'] > 0 and frame['dcount'] == len(frame['dtimes']):
        return(max(frame['dtimes'].values()))
    else
        return(0)

def get_raw_packet_counts(frame_list):
    packets = 0
    for frame_id, frame in frame_list:
        packets += len(frame['dtimes'])
    frames = len(frame_list) - 1
    packets += frames
    frames_exp = max(frame_list)
    packet_exp = frames_exp * 9

    return(packets, packet_exp)

if len(sys.argv) != 2:
    print("usage: uresanal.py <surgeon results>")

with open(sys.argv[1], 'rb') as filehandle:
    sframes = pickle.load(filehandle)

sleft = sframes['left']
sright = sframes['right']
last_frame_id = max(max(sleft), max(sright))
average_first_time = (get_arrival_time(sleft[0]) + get_arrival_time(sright[0])) / 2
deadline = average_first_time + (np.arange(1, last_frame_id + 1) * .033) 
disparities = np.zeros_like(deadline)
l_arrivals = np.zeros_like(deadline)
r_arrivals = np.zeros_like(deadline)

late = 0
half_late = 0

dropped = 0
half_dropped = 0

good_frames = 0

#last frame_id is a dummy terminator
for frame_id in range(last_frame_id):
    left_arrival = get_arrival_time(sleft[frame_id])
    right_arrival = get_arrival_time(sright[frameid])
    l_arrivals[frame_id] = left_arrival
    r_arrvals[framee_id] = right_arrival
    if left_arrival == 0 and right_arrival == 0:
        dropped += 1
    elif left_arrival == 0 or right_arrival == 0:
        half_dropped += 1
    else:
        frame_deadline = deadline[frame_id]
        if left_arrival > frame_deadline and right_arrival > frame_deadline:
            late += 1
        elif left_arrival > frame_deadline or ight_arrival > frame_deadline:
            half_late += 1
        else
            good_frames += 1
            disparities[frame_id] = abs(Left_arrival - right_arrival)

    
