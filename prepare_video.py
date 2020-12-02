#!/usr/bin/python3

import pickle
import cv2
import sys

infile = sys.argv[1]
outfile = sys.argv[2]

vid = cv2.VideoCapture(infile)

success, image = vid.read()

print("preparing encoding")
frames = list()
count = 1
while success:
    success, image = vid.read()
    if success:
        ret, frame = cv2.imencode('.PNG', image, [cv2.IMWRITE_PNG_COMPRESSION, 9])
        frames.append(frame)
    print('frame ', count)
    count += 1
print("encoding complete")

with open(outfile, 'wb') as filehandle:
    pickle.dump(frames, filehandle)
