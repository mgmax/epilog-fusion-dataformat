#!/usr/bin/env python2
from __future__ import division

# LICENSE: GPLv3 (or do whatever you want, I don't care)

# A first attempt at reverse-engineering the network protocol of the Epilog Laser eView Camera system.
# - Open the Epilog Job Manager and view the top camera image
# - Capture the network data stream with wireshark (Please note: On Windows, PCAP has the known error of dropping packets if the buffer size is not increased significantly. Because of this, the example capture I have is corrupted. If you have a better one, please contact me.)
# - Set the filename and the TCP source port in this script
# - Run this script to extract the images as out-*.jpg and also show them in a OpenCV window.

from matplotlib import pylab as plt


import numpy as np
import cv2
import scapy.all as scapy

import itertools

def sort_uniq_filter(mylist, key, filt):
    keys = [key(x) for x in mylist if filt(x)]
    key_value_dict = {}
    for x in mylist:
        if filt(x):
            k = key(x)
            if not k in key_value_dict:
                key_value_dict[k]=x
    return [key_value_dict[i] for i in sorted(keys)]

filename = "./example.pcapng"
source_port = 37441
capture = scapy.rdpcap(filename)
sessions = capture.sessions()
image_count=0
for session in sessions:
    print "please wait"
    data = b''
    packets=sessions[session]
    filt = lambda packet: (scapy.TCP in packet and packet[scapy.TCP].sport == source_port)
    # filter,
    # sort by sequence number and deduplicate (-> reassemble TCP stream, like 'Follow TCP Stream' in Wireshark)
    # (note: this would probably also be possible with https://github.com/simsong/tcpflow/ )
    expected_sequence_number = None
    for packet in sort_uniq_filter(packets, key=lambda p: p[scapy.TCP].seq, filt=filt):
        seq = packet[scapy.TCP].seq
        print packet.summary()
        # zero-pad for missing packets
        p = packet[scapy.TCP].payload
        if not p:
            continue
        if isinstance(p, scapy.Padding):
            continue
        if expected_sequence_number is not None:
            if (seq - expected_sequence_number) > 0:
                print "Padded {0} bytes (missing packet in trace!)".format((seq - expected_sequence_number))
            data += b'\x00' * (seq - expected_sequence_number)
        new_data = str(p)
        data += new_data
        expected_sequence_number = seq + len(new_data)
    if len(data)<1000:
        print "data too short, discarding"
        continue
    print len(data)
    offset = 5184-1440
    image_yuv = np.fromstring(data[offset:], dtype='uint8', sep="")
    # bytes per row:
    w=5184
    # truncate incomplete last row:
    h=len(image_yuv)//w
    image_yuv=image_yuv[0:w*h]
    # reshape to 2 bytes (1 byte Y, 1 byte UV) per pixel
    image_yuv = image_yuv.reshape([h, w//2, 2])
    # convert to RGB
    image_rgb = cv2.cvtColor(image_yuv, cv2.COLOR_YUV2RGB_YUY2)
    # show data
    cv2.namedWindow( "Display window", cv2.CV_WINDOW_AUTOSIZE )
    #cv2.imshow( "Display window", image_rgb)
    #cv2.waitKey(0)
    cv2.imwrite(filename + ".out-{}.jpg".format(image_count), image_rgb)
    print "wrote image"
    image_count += 1
print "done"
