#!/usr/bin/python3

"""https://github.com/jeffbass/imagezmq/blob/master/examples/pub_sub_receive.py"""
"""https://zguide.zeromq.org/docs/chapter1/"""

import sys
import threading
import time
import pickle
import socket

class VideoStreamSubscriber:

    def __init__(self, hostname, port):
        self._done = threading.Event()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.patient_addr = (hostname, port)
        self.frames = {}
        self._thread = threading.Thread(target=self._run, args=())
        self._thread.daemon = True
        self._thread.start()

    def _run(self):
        def decode_header(dgram):
            serial = int.from_bytes(dgram[0:4], byteorder='big')
            frame_id = int.from_bytes(dgram[4:8], byteorder='big')
            dgram_count = int.from_bytes(dgram[8:12], byteorder='big')
            frame_size = int.from_bytes(dgram[12:16], byteorder='big')
            return serial, frame_id, dgram_count, frame_size        

        def decode_payload(dgram):
            serial = int.from_bytes(dgram[0:4], byteorder='big')
            frame_id = int.from_bytes(dgram[4:8], byteorder='big')
            seq = int.from_bytes(dgram[8:12], byteorder='big')
            frame_size = int.from_bytes(dgram[12:16], byteorder='big')
            return serial, frame_id, seq, frame_size

        def recv_dgram():
            dgram, addr = self.sock.recvfrom(4096)
 
            if len(dgram) == 16:
                serial, frame_id, dcount, frame_size = decode_header(dgram)
                self.frames[frame_id] = { 'htime':time.time(), 'dcount':dcount, 'dtimes': {}, 'fsize':frame_size, 'brecv':0}
                if dcount == 0:
                    print("got terminator")
                    return False
            else:
                payload_size = len(dgram) - 16
                serial, frame_id, seq, frame_size = decode_payload(dgram)
                self.frames[frame_id]['brecv'] += payload_size
                self.frames[frame_id]['dtimes'][seq] = time.time()
            return True
        try:
            data = bytearray(10)
            data[0] = 117
            self.sock.sendto(data, self.patient_addr)
            print("sent")
            while True:
                if not recv_dgram():
                    break
            print("done")
        finally:
            self.sock.close()
            self._done.set()

    def close(self):
        self._done.wait()

if len(sys.argv) != 3:
    print("usage: usurgeon.py <patient IP> <output file>")
    exit(-1)

l_receiver = VideoStreamSubscriber(sys.argv[1], 5555)
r_receiver = VideoStreamSubscriber(sys.argv[1], 5556)
l_receiver.close()
r_receiver.close()

results = {"left":l_receiver.frames,"right":r_receiver.frames}
with open(sys.argv[2], 'wb') as filehandle:
    pickle.dump(results, filehandle)
