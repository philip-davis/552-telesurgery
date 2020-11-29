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
            
            self._pub.send_string('{count} {xshift},{yshift},{zshift}'.format(count=count, xshift=random(), yshift=random(), zshift=random()))
            time.sleep(random())        
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
        self._stop = False
        self._data_ready = threading.Event()
        self._thread = threading.Thread(target=self._run, args=())
        self._thread.daemon = True
        self._thread.start()

    def receive(self):
        flag = self._data_ready.wait()
        if not flag:
            raise TimeoutError(
                "Timeout while reading from subscriber tcp://{}:{}".format(self.hostname, self.port))
        self._data_ready.clear()
        return self._recv_time, self._data

    def _run(self):
        receiver = imagezmq.ImageHub("tcp://{}:{}".format(self.hostname, self.port), REQ_REP=False)
        while not self._stop:
            self._data = receiver.recv_jpg()
            print("got frame ", self._data[0])
            self._recv_time = time.time()
            self._data_ready.set()
        receiver.close()

    def close(self):
        self._stop = True

hostname = '10.10.2.2'
lport = 5555
rport = 5556
l_receiver = VideoStreamSubscriber(hostname, lport)
r_receiver = VideoStreamSubscriber(hostname, rport)
control = SurgeonControl(5557)

count = 1
diff = 0.
lost = 0
halflost = 0
last = 0
while True:
    l_time, (l_msg, frame) = l_receiver.receive()
    r_time, (r_msg, frame) = r_receiver.receive()
    if l_msg != r_msg:
        halflost += 1
        if(int(l_msg) < int(r_msg)):
            l_receiver.receive()
        else:
            r_receiver.receive()
    if l_msg == "done" or r_msg == "done":
        break
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
finish_time = time.time()
control.close()
print('{count} frames received in {time} seconds ({fps} FPS.)'.format(count=count, time=finish_time-start_time, fps=count/(finish_time-start_time)))
print('average side disparity is {time} ms.'.format(time=(diff / count)*1000))
print('lost {} frames and {} frame halves.'.format(lost, halflost))
