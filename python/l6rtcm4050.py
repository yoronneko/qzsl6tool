#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# l6rtcm4050.py: QZS L6 message to RTCM message type 4050 conversion
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2024 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.
#
# # References:
# [1] Cabinet Office, Government of Japan, Quasi-Zenith Satellite System
#     Interface Specification Centimeter Level Augmentation Service,
#     IS-QZSS-L6-005, Sept. 21, 2022.

import argparse
import os
import sys
import libtrace
from   librtcm import send_rtcm
try:
    import bitstring
except ModuleNotFoundError:
    libtrace.err('''\
    This code needs bitstring module.
    Please install this module such as \"pip install bitstring\".
    ''')
    sys.exit(1)

def read_l6():  # ref. [1]
    ''' reads L6 message and returns True if success '''
    sync = bytes(4)
    while sync != b'\x1a\xcf\xfc\x1d':
        b = sys.stdin.buffer.read(1)
        if not b:
            return None
        sync = sync[1:4] + b
    b = sys.stdin.buffer.read(1+1+212+32)
    if not b:
        return None
    return sync + b

def write_rtcm4050(l6msg):
    ''' reads QZS L6 messages from stdin and writes RTCM message type 4050 to stdout
        l6msg: 2000 bit (250 byte)
        rtcm:  1776 bit (222 byte)
    '''
    l6 = bitstring.BitStream(l6msg)
    l6.pos += 32  # Preamble 0x1ACFFC1D
    prn   = l6.read(8)  # PRN number
    mtid  = l6.read(8)  # Message type ID
    alert = l6.read(1)  # Alert flag
    rtcm  =  bitstring.BitArray('u12=4050')          # message type 4050
    rtcm  += bitstring.Bits('u4=0')                  # reserved
    rtcm  += bitstring.Bits('u20=0')                 # TOW (time of week), but it is unknown
    rtcm  += bitstring.Bits('u4=0')                  # number of correction error bits, but it is also unknown
    rtcm  += bitstring.Bits(uint=prn.u,   length=8)  # pseudo-random noise number
    rtcm  += bitstring.Bits(uint=mtid.u,  length=8)  # CSSR message type ID (4073)
    rtcm  += bitstring.Bits(uint=alert.u, length=1)  # alert flag
    rtcm  += l6[49:-256]                             # L6 message without preamble and RS error correction bits
    send_rtcm(sys.stdout, rtcm)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
    description='QZS L6 message to RTCM message type 4050 conversion')
    args = parser.parse_args()
    try:
        l6msg = read_l6()
        while l6msg:
            write_rtcm4050(l6msg)
            l6msg = read_l6()
    except (BrokenPipeError, IOError):
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(1)
    except KeyboardInterrupt:
        libtrace.warn("User break - terminated")
        sys.exit()

# EOF
