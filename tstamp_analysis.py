#!/usr/bin/python3

import pickle
import sys
from math import floor
import numpy as np
from statistics import stdev
import matplotlib.pyplot as plt

if(len(sys.argv) != 4):
    print("usage: tstamp_analysis.py <patient file> <surgeon file> <output suffix>")
    exit(-1)

sfx = sys.argv[3]

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

#dcount = surg['left'][0]['dcount']
#fcount = int(len(tx_ts) / (dcount + 1))
raw_l_rx_ts = surg['lprecv']
raw_r_rx_ts = surg['rprecv']

l_rx_lost = 0
r_rx_lost = 0
pkt_count = 2 * len(tx_ts)

rx_ts = list()
for idx in range(len(tx_ts)):
    if idx not in raw_l_rx_ts:
        l_rx_lost += 1
    if idx not in raw_r_rx_ts:
        r_rx_lost += 1
    try:
        lswts = raw_l_rx_ts[idx][0]
        lts = raw_l_rx_ts[idx][1]
    except KeyError:
        lswts = 0.
        lts = 0.
    try:
        rswts = raw_r_rx_ts[idx][0]
        rts = raw_r_rx_ts[idx][1]
    except KeyError:
        rswts = 0.
        lts = 0.
    rx_ts.append((idx, lts, rts, lswts, rswts))

"""
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
        lswts = surg['left'][frame_id]['shtime']
        rswts = surg['right'][frame_id]['shtime']
        rx_ts.append((seq, lts, rts, lswts, rswts))
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
        lswts = surg['left'][frame_id]['sdtimes'][fseq]
        rswts = surg['right'][frame_id]['sdtimes'][fseq]
        rx_ts.append((seq, lts, rts, lswts, rswts))
"""

tx_pkt_disp = [abs(i[1] - i[2]) for i in tx_ts]
rx_pkt_disp = [abs(i[1] - i[2]) for i in rx_ts]

"""
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

print("average tx frame disp: ", np.average(tx_frame_disp))
print("average rx frame disp: ", np.average(rx_frame_disp))
print("average tx pkt disp: ", np.average(tx_pkt_disp))
print("average rx pkt disp: ", np.average(rx_pkt_disp))
"""

time_list = list()
clean_tx_disp = list()
clean_rx_disp = list()
net_disp = list()
rx_sw_disp = list()
rx_stack_disp = list()
faux_latency = list()
for seq in range(len(tx_ts)):
    if tx_ts[seq][1] != 0 and tx_ts[seq][2] != 0 and rx_ts[seq][1] != 0 and rx_ts[seq][2] != 0:
        clean_tx_disp.append(tx_ts[seq][1] - tx_ts[seq][2])
        clean_rx_disp.append(rx_ts[seq][1] - rx_ts[seq][2])
        net_disp.append(clean_rx_disp[-1] - clean_tx_disp[-1])
        time_list.append(tx_ts[seq][1] - tx_ts[0][1])
        rx_sw_disp.append(rx_ts[seq][3] - rx_ts[seq][4])
        rx_stack_disp.append(rx_sw_disp[-1] - clean_rx_disp[-1])
        l_delay = rx_ts[seq][1] - tx_ts[seq][1]
        r_delay = rx_ts[seq][2] - tx_ts[seq][2]
        faux_latency.append((l_delay + r_delay) / 2.)

lost = l_rx_lost + r_rx_lost

print("lost {lost} packets out of {np}".format(lost=lost,np=pkt_count))
print("\nall times in seconds:")
print(" average tx pkt disp: ", np.average(clean_tx_disp))
print(" average rx pkt disp: ", np.average(clean_rx_disp))
print(" max tx pkt disp: ", max(clean_tx_disp))
print(" max rx pkt disp: ", max(clean_rx_disp))
print(" stdev tx pkt disp: ", stdev(clean_tx_disp))
print(" stdev rx pkt disp: ", stdev(clean_rx_disp))
print(" average net pkt disp: ", np.average(net_disp))
print(" max net pkt disp: ", max(net_disp))
print(" min net pkt disp: ", min(net_disp))
print(" stdev net pkt disp: ", stdev(net_disp))
print(" average sw rx pkt disp: ", np.average(rx_sw_disp))
print(" max sw rx pkt disp: ", max(rx_sw_disp))
print(" stdev sw rx pkt disp: ", stdev(rx_sw_disp))
print(" average rx stack pkt disp: ", np.average(rx_stack_disp))
print(" max rx stack pkt disp: ", max(rx_stack_disp))
print(" min rx stack pkg disp: ", min(rx_stack_disp))
print(" stdev rx stack pkg disp: ", stdev(rx_stack_disp))

"""
for i in range(len(tx_pkt_disp)):
    if(net_disp[i] == min(net_disp)):
        print(i, net_disp[i])
        print(tx_ts[i][1], tx_ts[i][2])
        print(rx_ts[i][1], rx_ts[i][2])
"""

fig, ax1 = plt.subplots()
ax1.set_xlabel('time (s)')
ax1.set_ylabel('packet disparity (s)')
ax1.plot(time_list, clean_tx_disp, color='red', label='patient (tx)')
ax1.plot(time_list, clean_rx_disp, color='blue', label='surgeon (rx)')
ax1.legend()

fig.tight_layout()
plt.savefig("pkt_disp_{}.png".format(sfx))

plt.figure(2)
fig, ax1 = plt.subplots()
ax1.set_xlabel('time (s)')
ax1.set_ylabel('net packet disparity (s)')
ax1.scatter(time_list, net_disp, color='green')

fig.tight_layout()
plt.savefig("net_pkt_disp_{}.png".format(sfx))

plt.figure(3)
fig, ax1 = plt.subplots()
ax1.set_xlabel('net packet disparity (s)')
ax1.hist(net_disp)

fig.tight_layout()
plt.savefig("net_pkt_hist_{}.png".format(sfx))

plt.figure(4)
fig, ax1 = plt.subplots()
ax1.set_xlabel('time (s)')
ax1.set_ylabel('stack packet disparity (s)')
ax1.scatter(time_list, rx_stack_disp, color='orange')

fig.tight_layout()
plt.savefig("stack_pkt_disp_{}.png".format(sfx))

plt.figure(5)
fig, ax1 = plt.subplots()
ax1.set_xlabel('latency (s)')
ax1.set_ylabel('net packet disparity (s)')
ax1.scatter(faux_latency, net_disp, color='purple')

fig.tight_layout()
plt.savefig("latency_net_{}.png".format(sfx))

disp_avg = np.average(net_disp)
disp_max = max(net_disp)
disp_stdev = stdev(net_disp)
loss = lost / pkt_count
with open('results_{}.csv'.format(sfx), 'w') as writer:
    writer.write('{sfx},{disp_avg},{disp_max},{disp_stdev},{loss}\n'.format(sfx=sfx, disp_avg=disp_avg, disp_max=disp_max, disp_stdev=disp_stdev, loss=loss))
