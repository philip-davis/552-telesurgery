#!/usr/bin/python3

import pickle
import sys
from math import floor
import numpy as np
from statistics import stdev
import matplotlib.pyplot as plt

with open(sys.argv[1], 'r') as reader:
    tx_ts = list()
    for line in reader.readlines():
        (seq_str, lts, rts) = (line[:-1]).split(',')
        tx_ts.append((int(seq_str), float(lts), float(rts)))

for idx in range(len(tx_ts)):
    if tx_ts[idx][0] != idx:
        print("complain")

with open(sys.argv[2], 'rb') as reader:
    surg=pickle.load(reader)

dcount = surg['left'][0]['dcount']
fcount = int(len(tx_ts) / (dcount + 1))

rx_ts = list()
for idx in range(len(tx_ts)):
    seq = tx_ts[idx][0]
    frame_id = floor(seq / (dcount + 1))
    if (seq % (dcount + 1)) == 0:
        try:
            lts = surg['left'][frame_id]['htime']
        except KeyError:
            lts = 0.
        try:
            rts = surg['right'][frame_id]['htime']
        except KeyError:
            rts = 0.    
        rx_ts.append((seq, lts, rts))
    else:
        fseq = (seq % (dcount + 1)) - 1
        try:    
            lts = surg['left'][frame_id]['dtimes'][fseq]
        except KeyError:
            lts = 0.    
        try:    
            rts = surg['right'][frame_id]['dtimes'][fseq]
        except KeyError:
            rts = 0.
        rx_ts.append((seq, lts, rts))

tx_pkt_disp = [abs(i[1] - i[2]) for i in tx_ts]
rx_pkt_disp = [abs(i[1] - i[2]) for i in rx_ts]

tx_ftimes = list()
rx_ftimes = list()
for frame_id in range(fcount):
   frame_seq = frame_id*(dcount+1)
   next_frame_seq = (frame_id+1)*(dcount+1)
   txl_ftime = max([i[1] for i in tx_ts[frame_seq:next_frame_seq]])
   txr_ftime = max([i[2] for i in tx_ts[frame_seq:next_frame_seq]])
   tx_ftimes.append((txl_ftime, txr_ftime))
   rxl_ftime = max([i[1] for i in rx_ts[frame_seq:next_frame_seq]])
   rxr_ftime = max([i[2] for i in rx_ts[frame_seq:next_frame_seq]]) 
   rx_ftimes.append((rxl_ftime, rxr_ftime))

tx_frame_disp = [abs(i[0] - i[1]) for i in tx_ftimes]
rx_frame_disp = [abs(i[0] - i[1]) for i in rx_ftimes]

"""
print("average tx frame disp: ", np.average(tx_frame_disp))
print("average rx frame disp: ", np.average(rx_frame_disp))
print("average tx pkt disp: ", np.average(tx_pkt_disp))
print("average rx pkt disp: ", np.average(rx_pkt_disp))
"""

time_list = list()
clean_tx_disp = list()
clean_rx_disp = list()
net_disp = list()
for seq in range(len(tx_ts)):
    if tx_ts[seq][1] != 0 and tx_ts[seq][2] != 0 and rx_ts[seq][1] != 0 and rx_ts[seq][2] != 0:
        clean_tx_disp.append(abs(tx_ts[seq][1] - tx_ts[seq][2]))
        clean_rx_disp.append(abs(rx_ts[seq][1] - rx_ts[seq][2]))
        net_disp.append((abs(tx_ts[seq][1] - tx_ts[seq][2])) - (abs(rx_ts[seq][1] - rx_ts[seq][2])))
        time_list.append(tx_ts[seq][1] - tx_ts[0][1])
        
print("all times in seconds:")
print(" average tx pkt disp: ", np.average(clean_tx_disp))
print(" average rx pkt disp: ", np.average(clean_rx_disp))
print(" max tx pkt disp: ", max(clean_tx_disp))
print(" max rx pkt disp: ", max(clean_rx_disp))
print(" stdev tx pkt disp: ", stdev(clean_tx_disp))
print(" stdev rx pkt disp: ", stdev(clean_rx_disp))
print(" average net pkt disp: ", np.average(net_disp))
print(" max net pkt disp: ", max(net_disp))
print(" min net pkg disp: ", min(net_disp))
print(" stdev net pkg disp: ", stdev(net_disp))

"""
for i in range(len(tx_pkt_disp)):
    if(tx_pkt_disp[i] == max(tx_pkt_disp)):
        print(tx_pkt_disp[i])
        print(tx_ts[i])
        print(rx_ts[i])
"""

fig, ax1 = plt.subplots()
ax1.set_xlabel('time (s)')
ax1.set_ylabel('packet disparity (s)')
ax1.plot(time_list, clean_tx_disp, color='red', label='patient (tx)')
ax1.plot(time_list, clean_rx_disp, color='blue', label='surgeon (rx)')
ax1.legend()

fig.tight_layout()
plt.savefig("pkt_disp.png")

plt.figure(2)
fig, ax1 = plt.subplots()
ax1.set_xlabel('time (s)')
ax1.set_ylabel('net packet disparity (s)')
ax1.plot(time_list, net_disp, color='green')

fig.tight_layout()
plt.savefig("net_pkt_disp.png")
