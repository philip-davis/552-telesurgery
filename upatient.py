#!/usr/bin/python3

"""https://stackoverflow.com/questions/33311153/python-extracting-and-saving-video-frames"""
"""https://github.com/jeffbass/imagezmq/blob/master/examples/pub_sub_broadcast.py"""
"""https://pyzmq.readthedocs.io/en/latest/serialization.html"""
"""https://pymotw.com/2/socket/udp.html"""

import socket
import sys
import threading
import pickle
import numpy
import time

b = threading.Barrier(2)

class VideoStreamer:
    def __init__(self, port, dgram_payload=1000, framesize=80000, nframes=3600, tos=0):
        SO_TIMESTAMPING = 37
        TIMESTAMPING_TX_HARDWARE = 1
        SOF_TIMESTAMPING_RAW_HARDWARE = 64
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, SO_TIMESTAMPING, TIMESTAMPING_TX_HARDWARE | SOF_TIMESTAMPING_RAW_HARDWARE)
        self.sock.bind(('', port))
        self.serial = 0
        self.fsize = framesize
        self.nframes = nframes
        self.dgram_payload=dgram_payload
        self._done = threading.Event()
        self._thread = threading.Thread(target=self._run, args=())
        self._thread.daemon = True
        self._thread.start()

    def gen_seq(self):
         seq = self.serial
         self.serial += 1
         return seq

    def _run(self):
        header_dgram = bytearray(16) # seq, frame_id, payload_count, frame_size
        payload_dgram = bytearray(self.dgram_payload + 16)
        # dummy payload, 10101010..
        payload_dgram[16:] = [170 for i in range(self.dgram_payload)]       
 
        def send_frame_header(frame_id, payload_count):
            print(frame_id)
            dgram_seq = self.gen_seq()
            frame_size = self.dgram_payload * payload_count
            for i in range(4):
                header_dgram[i] = dgram_seq.to_bytes(4, byteorder='big')[i]
                header_dgram[i+4] = frame_id.to_bytes(4, byteorder='big')[i]
                header_dgram[i+8] = payload_count.to_bytes(4, byteorder='big')[i]
                header_dgram[i+12] = frame_size.to_bytes(4, byteorder='big')[i]
            self.sock.sendto(header_dgram, self.surgeon_addr)

        def send_payload_dgram(frame_id, seq, total):
            dgram_seq = self.gen_seq()
            for i in range(4):
                payload_dgram[i] = dgram_seq.to_bytes(4, byteorder='big')[i]
                payload_dgram[i+4] = frame_id.to_bytes(4, byteorder='big')[i]
                payload_dgram[i+8] = seq.to_bytes(4, byteorder='big')[i]
                payload_dgram[i+12] = total.to_bytes(4, byteorder='big')[i]
            self.sock.sendto(payload_dgram, self.surgeon_addr)
        
        def send_frame(frame_id):
            ndgrams = int(self.fsize / self.dgram_payload)
            send_frame_header(frame_id, ndgrams)
            for count in range(ndgrams):
                send_payload_dgram(frame_id, count, ndgrams)
        try:
            print("waiting for surgeon")
            data, address = self.sock.recvfrom(4096)
            self.surgeon_addr = address
            b.wait(2)
            start_time = time.time()
            for frame_id in range(self.nframes):
                b.wait(2)
                send_frame(frame_id)
                
                wait_time = (start_time + (0.033 * (frame_id + 1))) - time.time()
                if(wait_time > 0):
                    self.sock.settimeout(wait_time)
                    try:
                        raw_data, ancdata, flags, address = self.sock.recvmsg(4096, 1024)
                        print(ancdata)
                    except Exception:
                        pass
                    self.sock.settimeout(None)
                    wait_time = (start_time + (0.033 * (frame_id + 1))) - time.time()
                    if wait_time > 0:
                        time.sleep(wait_time)
                
                #raw_data, ancdata, flags, address = self.sock.recvmsg(4096, 1024)
                #print(ancdata)
            # terminator
            send_frame_header(self.nframes, 0)
        finally:
            self.sock.close()
            self._done.set()

    def close(self):
        flag = self._done.wait()

l_camera = VideoStreamer(5555, nframes=300)
r_camera = VideoStreamer(5556, nframes=300)
l_camera.close()
r_camera.close()
