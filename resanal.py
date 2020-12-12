#!/usr/bin/python3

import matplotlib.pyplot as plt
from statistics import stdev
import pickle
import sys
import numpy as np

with open(sys.argv[1], 'rb') as filehandle:
    ftimes = pickle.load(filehandle)
with open(sys.argv[2], 'rb') as filehandle:
    ctimes = pickle.load(filehandle)
with open(sys.argv[3], 'rb') as filehandle:
    frames = pickle.load(filehandle)
with open(sys.argv[4], 'rb') as filehandle:
    stimes = pickle.load(filehandle)

max_frame = max(max(ftimes["left"].keys()),max(ftimes["right"].keys()))
lost = 0
halflost = 0
totaldiff = 0
maxdiff = -1
maxsenddiff = -1
first_count = -1
last_good = -1
jitter_total = 0
num_good = 0
drop = 0
late = 0
late_time = 0
latest = -1
good_diffs = list()

send_disp_total = 0
send_diffs = list()
disp_jitter = 0
send_jitter = 0
sd_jitter = 0
exptime = np.arange(max_frame) * .033
disptime = np.zeros_like(exptime)
snddisptime = np.zeros_like(exptime)
fsize = np.zeros_like(exptime)
for count in range(1, max_frame):
    if not count in ftimes["left"] and not count in ftimes["right"]:
        lost += 1
    elif not count in ftimes["left"] or not count in ftimes["right"]:
        halflost += 1
    else:
        disptime[count] = ftimes["left"][count] - ftimes["right"][count]
        snddisptime[count] = stimes["left"][count] - ftimes["right"][count]
        fsize[count] = np.prod(frames[count].shape)
        arr_time = max(ftimes["left"][count], ftimes["right"][count])
        dep_time = max(stimes["left"][count], stimes["right"][count])
        if first_count == -1:
            first_count = count
            first_time = arr_time
        deadline = first_time + (((count - first_count) + 1) * 0.033)
        if arr_time > deadline:
            drop += 1
            next
        elif arr_time > (deadline - 0.033):
            lateby = arr_time - (deadline - 0.033)
            late += 1
            late_time += lateby
            if(lateby > latest):
                latest = lateby
        if count == last_good + 1:
            jitter_total += abs((last_time + 0.033) - arr_time)
            send_jitter += abs((last_send_time + 0.033) - dep_time)
            #send_jitter += abs((snddisptime[count-1] + 0.033) - snddisptime[count])
            disp_jitter += abs(disptime[count] - disptime[count-1])
            sd_jitter += abs(snddisptime[count] - snddisptime[count-1])
            num_good += 1
        diff = abs(ftimes["left"][count] - ftimes["right"][count])
        senddiff = abs(stimes["left"][count] - stimes["right"][count])
        totaldiff += diff
        send_disp_total += senddiff
        if(diff > maxdiff):
            maxdiff = diff
        if(senddiff > maxsenddiff):
            maxsenddiff = senddiff
        good_diffs.append(diff)
        send_diffs.append(senddiff)
        last_good = count
        last_time = arr_time
        last_send_time = dep_time
nframes = max_frame - (lost + halflost + drop)
print("{total} frames recv ({fps} FPS,) {lost} both missing, {halflost} half missing".format(total=nframes, fps=nframes/(last_time-first_time), lost=lost, halflost=halflost))
print("{drop} frames arrived too late".format(drop=drop))
if late > 0:
    print("{late} frames arrived late, but still usable. Average lateness {avg} ms, worst is {worst} ms.".format(late=late, avg=1000*(late_time/late),worst=1000*latest))
print("average recv frame disparity is {avg} ms, stdev is {stdevi} ms, max disparity is {maxdiff} ms, disparity jitter is {disp_jitter} ms".format(avg=(1000*totaldiff)/nframes,stdevi=1000*stdev(good_diffs), maxdiff=1000*maxdiff, disp_jitter=1000*(disp_jitter/num_good)))
print("average send frame disparity is {avg} ms, stdev is {stdevi} ms, max disparity is {maxdiff} ms, disparity jitter is {disp_jitter} ms".format(avg=(1000*send_disp_total)/nframes,stdevi=1000*stdev(send_diffs), maxdiff=1000*maxsenddiff, disp_jitter=1000*(sd_jitter/num_good)))
print("avg frame jitter is {jitter} ms at the recv side, {sjitter} ms at the send side".format(jitter=1000*(jitter_total/num_good), sjitter=1000*(send_jitter/num_good)))

fig, ax1 = plt.subplots()
ax1.set_xlabel('time (s)')
ax1.set_ylabel('frame size (B)', color='red')
ax1.plot(exptime, fsize, color='red', label='frame size')
ax1.tick_params(axis='y', labelcolor='red')

ax2 = ax1.twinx()
ax2.set_ylabel('disparity (s)', color='blue')
ax2.plot(exptime, disptime, color='blue', label = 'recv disparity')
ax2.plot(exptime, snddisptime, color='green', label='send disparity')
ax2.tick_params(axis='y', labelcolor='blue')
ax2.legend()

fig.tight_layout()
plt.savefig("disp+size.png")

start_recv = (ftimes["left"][1] + ftimes["right"][1]) / 2
start_send = (stimes["left"][1] + stimes["right"][1]) / 2
exp_recv = np.arange(start_recv, start_recv + (max_frame * 0.033), 0.033)
exp_send = np.arange(start_send, start_recv + (max_frame * 0.033), 0.033)
lr_offset = np.zeros_like(exptime)
rr_offset = np.zeros_like(exptime)
ls_offset = np.zeros_like(exptime)
rs_offset = np.zeros_like(exptime)
for count in range(1, max_frame):
    lr_offset[count] = ftimes['left'][count] - exp_recv[count]
    rr_offset[count] = ftimes['right'][count] - exp_recv[count]
    ls_offset[count] = ftimes['left'][count] - exp_send[count]
    rs_offset[count] = ftimes['right'][count] - exp_send[count]

plt.figure(2)
fig, ax1 = plt.subplots()
ax1.set_xlabel('time (s)')
ax1.set_ylabel('offset (s)')
ax1.plot(exptime, lr_offset, color='red', label='left receive')
ax1.plot(exptime, rr_offset, color='blue', label='right receive')
ax1.plot(exptime, ls_offset, color='green', label='left send')
ax1.plot(exptime, rs_offset, color='orange', label='right send')
ax1.legend()

fig.tight_layout()
plt.savefig("offsets.png")

del ctimes[-1]
lost = 0
ncmd = 0
last_cmd = max(ctimes.keys())
last_good = -1
total_jitter = 0
for count in range(1, last_cmd):
    if not count in ctimes:
        lost += 1
    else:
        ncmd += 1
        (time, delay) = ctimes[count]
        if count == last_good + 1:
            myjitter = abs(time - (last_time + last_delay))
            total_jitter += myjitter
        last_good = count
        last_time = time
        last_delay = delay
print("{ncmd} commands received, and {lost} lost".format(ncmd=ncmd, lost=lost))
print("avg cmd jitter is {jitter} ms".format(jitter=1000*(total_jitter/ncmd)))
