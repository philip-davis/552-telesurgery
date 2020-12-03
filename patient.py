#!/usr/bin/python3

"""https://stackoverflow.com/questions/33311153/python-extracting-and-saving-video-frames"""
"""https://github.com/jeffbass/imagezmq/blob/master/examples/pub_sub_broadcast.py"""

import sys
from shutil import copyfile
import cv2
import time
import threading
import imagezmq
import numpy as np
import zmq
import pickle

b = threading.Barrier(2)

class VideoStreamer:
    def __init__(self, name, port):
        self.port = port
        #stage = '/tmp/{file}'.format(file=name)
        #copyfile(name, stage)
        #self.vid = cv2.VideoCapture(stage)
        with open(name, 'rb') as filehandle:
            self.frames = pickle.load(filehandle)
        self._sender = imagezmq.ImageSender('tcp://*:{port}'.format(port=self.port), REQ_REP=False)
        self._done = threading.Event()
        self._thread = threading.Thread(target=self._run, args=())
        self._thread.daemon = True
        self._thread.start()
    
    def _run(self):
        '''
        success, image = self.vid.read()
        frames = list()
        print("preparing encoding")
        count = 1
        while success:
            success, image = self.vid.read()
            if success:
                ret, frame = cv2.imencode('.PNG', image, [cv2.IMWRITE_PNG_COMPRESSION, 9])
                frames.append(frame)
            print('frame ', count)
            count += 1
        print("encoding complete")
        '''
        time.sleep(5)
        self.time = time.time()
        count = 1
        for frame in self.frames:
            b.wait()
            print(frame.shape)
            self._sender.send_image(str(count), frame)
            count += 1
            self.time += .033
            sleep_time = self.time - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)               
        done_image = np.zeros(shape=[1,1,3], dtype=np.uint8)
        self._sender.send_image("done", done_image)
        print("done")
        self._sender.close()
        self._done.set()

    def close(self):
        flag = self._done.wait()


class VideoStreamerCombined:
    def __init__(self, lname, lport, rname, rport):
        self.lport = lport
        self.rport = rport
        left_stage = '/tmp/{file}'.format(file=lname)
        right_stage = '/tmp/{file}'.format(file=rname)
        copyfile(lname, left_stage)
        copyfile(rname, right_stage)
        self.l_vid = cv2.VideoCapture(left_stage)
        self.r_vid = cv2.VideoCapture(right_stage)
        self._done = threading.Event()
        self._thread = threading.Thread(target=self._run, args=())
        self._thread.daemon = True
        self._thread.start()
    
    def _run(self):
        l_sender = imagezmq.ImageSender('tcp://*:{port}'.format(port=self.lport), REQ_REP=False)   
        r_sender = imagezmq.ImageSender('tcp://*:{port}'.format(port=self.rport), REQ_REP=False)
        time.sleep(5)
        l_success, image = self.l_vid.read()
        r_success, image = self.r_vid.read()
        self.time = time.time()
        count = 1
        while l_success and r_success:
            l_success, l_image = self.l_vid.read()
            r_success, r_image = self.r_vid.read()
            if l_success and r_success:
                l_sender.send_image(str(count), l_image)
                r_sender.send_image(str(count), r_image)
            count += 1
            self.time += .033
            sleep_time = self.time - time.time()
            if sleep_time > 0:
                time.sleep(sleep_time)
        done_image = np.zeros(shape=[1,1,3], dtype=np.uint8)
        l_sender.send_image("done", done_image)
        r_sender.send_image("done", done_image)
        l_sender.close()
        r_sender.close()
        print("done")
        self._done.set()

    def close(self):
        flag = self._done.wait()

if len(sys.argv) !=3:
    print('Usage: client.py <video file> <video file>')
    exit(-1)

#camera = VideoStreamerCombined(sys.argv[1], 5555, sys.argv[2], 5556)
#camera.close()
l_camera = VideoStreamer(sys.argv[1], 5555)
r_camera = VideoStreamer(sys.argv[2], 5556)

context = zmq.Context()
sub = context.socket(zmq.SUB)
sub.connect('tcp://10.10.1.3:5557')
sub.setsockopt_string(zmq.SUBSCRIBE, '')

lost = 0
last = 0
commands = {}
while(True):
    cmd = sub.recv_string().split()
    count = int(cmd[0])
    delay = float(cmd[1])
    commands[count] = (time.time(), delay)
    print('got command ', count)
    if count == -1:
        break
    if(count > last + 1):
        lost += count - (last + 1)
    last = count 
l_camera.close()
r_camera.close()

with open('cmdtimes.dat', 'wb') as filehandle:
    pickle.dump(commands, filehandle)

print('lost {} commands'.format(lost))
