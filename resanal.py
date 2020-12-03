#!/usr/bin/python3

from statistics import stdev
import pickle
import sys

with open(sys.argv[1], 'rb') as filehandle:
    ftimes = pickle.load(filehandle)
with open(sys.argv[2], 'rb') as filehandle:
    ctimes = pickle.load(filehandle)

max_frame = max(max(ftimes["left"].keys()),max(ftimes["right"].keys()))
lost = 0
halflost = 0
totaldiff = 0
maxdiff = -1
first_count = -1
last_good = -1
jitter_total = 0
num_good = 0
drop = 0
late = 0
late_time = 0
latest = -1
good_diffs = list()
for count in range(1, max_frame):
    if not count in ftimes["left"] and not count in ftimes["right"]:
        lost += 1
    elif not count in ftimes["left"] or not count in ftimes["right"]:
        halflost += 1
    else:
        arr_time = max(ftimes["left"][count], ftimes["right"][count])
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
            num_good += 1
        diff = abs(ftimes["left"][count] - ftimes["right"][count])
        totaldiff += diff
        if(diff > maxdiff):
            maxdiff = diff
        good_diffs.append(diff)
        last_good = count
        last_time = arr_time
nframes = max_frame - (lost + halflost)
print("{total} frames recv, {lost} both missing, {halflost} half missing".format(total=nframes, lost=lost, halflost=halflost))
print("{drop} frames arrived too late".format(drop=drop))
if late > 0:
    print("{late} frames arrived late, but still usable. Average lateness {avg} ms, worse is {worst} ms.".format(late=late, avg=1000*(late_time/late),worst=latest))
print("average disparity is {avg} ms, stdev is {stdevi} ms , max disparity is {maxdiff} ms".format(avg=(1000*totaldiff)/nframes,stdevi=1000*stdev(good_diffs), maxdiff=1000*maxdiff))
print("avg jitter is {jitter} ms".format(jitter=1000*(jitter_total/num_good)))


del ctimes[-1]

