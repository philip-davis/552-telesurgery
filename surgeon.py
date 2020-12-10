#!/usr/bin/python3

"""https://github.com/jeffbass/imagezmq/blob/master/examples/pub_sub_receive.py"""
"""https://zguide.zeromq.org/docs/chapter1/"""

import sys

import cv2
import imagezmq
import threading
import time
import zmq
from random import random
import pickle

class SurgeonControl:
    def __init__(self, port):
        self.port = port
        ctx = zmq.Context.instance()
        self._pub = ctx.socket(zmq.PUB)
        self._pub.bind('tcp://*:{}'.format(port))
        time.sleep(5)
        self._done = False
        self._thread = threading.Thread(target=self._run, args=())
        self._thread.daemon = True
        self._thread.start()

    def _run(self):
        time.sleep(5)
        count = 0
        while True:
            count += 1
            sleep_time = random()
            self._pub.send_string('{count} {sleep_time} {xshift},{yshift},{zshift}'.format(count=count, sleep_time=sleep_time, xshift=random(), yshift=random(), zshift=random()))
            time.sleep(sleep_time)        
            if self._done:
                self._pub.send_string('-1 0 0 0')
                break

    def close(self):
        self._done = True
        self._thread.join()

class VideoStreamSubscriber:

    def __init__(self, hostname, port):
        self.hostname = hostname
        self.port = port
        self._done = threading.Event()
        self._data_ready = threading.Event()
        self._thread = threading.Thread(target=self._run, args=())
        self._thread.daemon = True
        self._thread.start()
        self.arrival_times = {}

    def receive(self):
        flag = self._data_ready.wait()
        if not flag:
            raise TimeoutError(
                "Timeout while reading from subscriber tcp://{}:{}".format(self.hostname, self.port))
        self._data_ready.clear()
        return self._recv_time, self._data

    def _run(self):
        receiver = imagezmq.ImageHub("tcp://{}:{}".format(self.hostname, self.port), REQ_REP=False)
        while True:
            self._data = receiver.recv_jpg()
            if(self._data[0] == 'done'):
                break
            self._recv_time = time.time()
            #print("got {count} at {time}".format(count=self._data[0],time=self._recv_time))
            self.arrival_times[int(self._data[0])] = self._recv_time
            self._data_ready.set()
        receiver.close()
        self._done.set()

    def close(self):
        self._done.wait()

hostname = '10.10.2.2'
lport = 5555
rport = 5556
l_receiver = VideoStreamSubscriber(hostname, lport)
r_receiver = VideoStreamSubscriber(hostname, rport)

#control_start = False
count = 1
diff = 0.
lost = 0
halflost = 0
last = 0

control = SurgeonControl(5557)

start_time = time.time()
l_receiver.close()
r_receiver.close()

'''
while True:
    l_time, (l_msg, frame) = l_receiver.receive()
    r_time, (r_msg, frame) = r_receiver.receive()
    if not control_start:
        control = SurgeonControl(5557)
        control_start = True
    if l_msg == 'done' or r_msg == 'done':
        break
    if l_msg != r_msg:
        halflost += 1
        if(int(l_msg) < int(r_msg)):
            l_receiver.receive()
        else:
            r_receiver.receive()
    if(l_msg == r_msg):
        frameno = int(l_msg)
        print('got frame {}'.format(frameno))
        if(frameno != last + 1):
            print('lost {} frame(s)!'.format(frameno - last))
            lost += (frameno - last)
        last = frameno
    if count == 1:
        start_time = time.time()
    #print("received frame pair ", count, abs(l_time-r_time))
    if count % 100 == 0:
        print('frame ', count)
    diff += abs(l_time - r_time)
    #print("received pair ", time.gmtime())
    count += 1
'''
finish_time = time.time()
control.close()
l_times = l_receiver.arrival_times
r_times = r_receiver.arrival_times
times = { "left": l_times, "right": r_times }
with open('frametimes.dat', 'wb') as filehandle:
    pickle.dump(times, filehandle)

last_frame = max(max(l_times.keys()), max(r_times.keys()))
for count in range (1, last_frame):
    if count not in l_times and count not in r_times:
        lost += 1
    elif count not in l_times or count not in r_times:
        halflost += 1
    else:
        diff += abs(l_times[count] - r_times[count])
print('{count} frames received in {time} seconds ({fps} FPS.)'.format(count=last_frame, time=finish_time-start_time, fps=last_frame/(finish_time-start_time)))
print('average side disparity is {time} ms.'.format(time=(diff / count)*1000))
print('lost {} frames and {} frame halves.'.format(lost, halflost))
