#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# libqzsl6.py: library for QZS L6 message processing
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022-2024 Satoshi Takahashi
#
# Released under BSD 2-clause license.
#
# References:
# [1] Cabinet Office of Japan, Quasi-Zenith Satellite System Interface
#     Specification Centimeter Level Augmentation Service,
#     IS-QZSS-L6-005, Sept. 21, 2022.
# [2] Global Positioning Augmentation Service Corporation (GPAS),
#     Quasi-Zenith Satellite System Correction Data on Centimeter Level
#     Augmentation Service for Experiment Data Format Specification,
#     1st ed., Nov. 2017.
# [3] Cabinet Office of Japan, Quasi-Zenith Satellite System Interface
#     Specification Multi-GNSS Advanced Orbit and Clock Augmentation
#     - Precise Point Positioning, IS-QZSS-MDC-001, Feb., 2022.
# [4] Radio Technical Commission for Maritime Services (RTCM),
#     Differential GNSS (Global Navigation Satellite Systems) Services
#     - Version 3, RTCM Standard 10403.3, Apr. 24 2020.

import os
import sys

sys.path.append(os.path.dirname(__file__))
from   librtcm     import send_rtcm, msgnum2satsys, msgnum2mtype
import libgnsstime
import libqznma
import libssr
import libtrace

try:
    import bitstring
except ModuleNotFoundError:
    libtrace.err('''\
    This code needs bitstring module.
    Please install this module such as \"pip install bitstring\".
    ''')
    sys.exit(1)

class QzsL6:
    "Quasi-Zenith Satellite L6 message process class"
    dpart    = bitstring.BitStream()  # data part
    dpn      = 0                     # data part number
    sfn      = 0                     # subframe number
    prn      = 0                     # psedudo random noise number
    vendor   = ''                    # vendor name
    facility = ''                    # facility name
    servid   = ''                    # service name
    msg_ext  = ''                    # extension (LNAV or CNAV)
    sf_ind   = 0                     # subframe indicator (0 or 1)
    alert    = 0                     # alert flag (0 or 1)
    run      = False                 # CSSR decode in progress
    payload  = bitstring.BitStream()  # QZS L6 payload
    msgnum   = 0                     # message type number
    hepoch   = 0                     # hourly epoch
    interval = 0                     # update interval
    mmi      = 0                     # multiple message indication
    iod      = 0                     # SSR issue of data

    def __init__(self, fp_rtcm, trace, stat):
        self.fp_rtcm = fp_rtcm
        self.trace   = trace
        self.stat    = stat
        self.ssr     = libssr.Ssr(trace)
        self.qznma   = libqznma.Qznma(trace)

    def __del__(self):
        if self.stat:
            self.ssr.show_cssr_stat()

    def read(self):  # ref. [1]
        ''' reads L6 message and returns True if success '''
        sync = bytes(4)
        while sync != b'\x1a\xcf\xfc\x1d':
            b = sys.stdin.buffer.read(1)
            if not b:
                return False
            sync = sync[1:4] + b
        b = sys.stdin.buffer.read(1+1+212+32)
        if not b:
            return False
        pos = 0
        self.prn = int.from_bytes(b[pos:pos+1], 'big'); pos += 1
        mtid     = int.from_bytes(b[pos:pos+1], 'big'); pos += 1
        data     = b[pos:pos+212]; pos += 212
        rs       = b[pos:pos+ 32]; pos += 32
        vid = mtid >> 5  # vender ID
        if   vid == 0b001: self.vendor = "MADOCA"
        elif vid == 0b010: self.vendor = "MADOCA-PPP"
        elif vid == 0b011: self.vendor = "QZNMA"
        elif vid == 0b101: self.vendor = "CLAS"
        else:              self.vendor = f"vendor 0b{vid:03b}"
        self.facility = "Kobe" if (mtid >> 4) & 1 else "Hitachi-Ota"
        self.facility += ":" + str((mtid >> 3) & 1)
        self.servid   = "Ionosph" if (mtid >> 2) & 1 else "Clk/Eph"
        self.msg_ext  = "CNAV"    if (mtid >> 1) & 1 else "LNAV"
        self.sf_ind   = mtid & 1  # subframe indicator
        bdata         = bitstring.BitStream(data)
        self.alert    = bdata[0]
        self.dpart    = bdata[1:]
        return True

    def show(self):
        ''' calls message decode functions and shows decoded message '''
        msg = self.trace.msg(0, f'{self.prn} {self.facility:13s}', fg='green')
        if self.alert:
            msg += self.trace.msg(0, '* ', fg='red')
        else:
            msg += '  '
        msg += self.trace.msg(0, self.vendor, fg='yellow') + ' '
        if self.vendor == "MADOCA":
            msg += self.show_mdc_msg()
        elif self.vendor in {"CLAS", "MADOCA-PPP"}:
            msg += self.show_cssr_msg()
        elif self.vendor == "QZNMA":
            msg += self.show_qznma_msg()
        else:  # unknown vendor
            msg += self.show_unknown_msg()
        self.trace.show(0, msg)

    def read_madoca(self):  # ref. [2]
        ''' returns True if success in decoding MADOCA message '''
        if len(self.dpart) < 12:
            return False
        msgnum = self.dpart.read('u12')
        if msgnum == 0:
            return False
        satsys = msgnum2satsys(msgnum)
        mtype  = msgnum2mtype(msgnum)
        self.ssr.ssr_decode_head(self.dpart, satsys, mtype)
        if mtype == 'SSR orbit':
            msg = self.ssr.ssr_decode_orbit(self.dpart, satsys)
        elif mtype == 'SSR clock':
            msg = self.ssr.ssr_decode_clock(self.dpart, satsys)
        elif mtype == 'SSR code bias':
            msg = self.ssr.ssr_decode_code_bias(self.dpart, satsys)
        elif mtype == 'SSR URA':
            msg = self.ssr.ssr_decode_ura(self.dpart, satsys)
        elif mtype == 'SSR hr clock':
            msg = self.ssr.ssr_decode_hr_clock(self.dpart, satsys)
        else:
            raise Exception(f'unsupported message type: {msgnum}')
        self.trace.show(1, msg)
        if self.dpart.pos % 8 != 0:  # byte align
            self.dpart.pos += 8 - (self.dpart.pos % 8)
        send_rtcm(self.fp_rtcm, self.dpart[0:self.dpart.pos])
        self.dpart = self.dpart[self.dpart.pos:]  # discard decoded part
        self.dpart.pos = 0
        self.msgnum = msgnum
        return True

    def read_cssr(self):  # ref. [1]
        ''' reads CSSR message and returns True if success '''
        if not self.run:
            return False
        if not self.ssr.decode_cssr_head(self.payload):
            return False
        if   self.ssr.subtype == 1:
            decoded = self.ssr.decode_cssr_st1(self.payload)
        elif self.ssr.subtype == 2:
            decoded = self.ssr.decode_cssr_st2(self.payload)
        elif self.ssr.subtype == 3:
            decoded = self.ssr.decode_cssr_st3(self.payload)
        elif self.ssr.subtype == 4:
            decoded = self.ssr.decode_cssr_st4(self.payload)
        elif self.ssr.subtype == 5:
            decoded = self.ssr.decode_cssr_st5(self.payload)
        elif self.ssr.subtype == 6:
            decoded = self.ssr.decode_cssr_st6(self.payload)
        elif self.ssr.subtype == 7:
            decoded = self.ssr.decode_cssr_st7(self.payload)
        elif self.ssr.subtype == 8:
            decoded = self.ssr.decode_cssr_st8(self.payload)
        elif self.ssr.subtype == 9:
            decoded = self.ssr.decode_cssr_st9(self.payload)
        elif self.ssr.subtype == 10:
            decoded = self.ssr.decode_cssr_st10(self.payload)
        elif self.ssr.subtype == 11:
            decoded = self.ssr.decode_cssr_st11(self.payload)
        elif self.ssr.subtype == 12:
            decoded = self.ssr.decode_cssr_st12(self.payload)
        else:
            raise Exception(f"Unknown CSSR subtype: {self.ssr.subtype}")
        if decoded:
            send_rtcm(self.fp_rtcm, self.payload[:self.payload.pos])  # RTCM MT 4073
            self.payload = self.payload[self.payload.pos:]  # discard decoded part
            self.payload.pos = 0
        return decoded

    def show_mdc_msg(self):
        ''' returns decoded message '''
        self.tow   = self.dpart.read('u20')
        self.wn    = self.dpart.read('u13')
        self.dpart = self.dpart[self.dpart.pos:]  # discard decoded part
        self.dpart.pos = 0
        msg   = libgnsstime.gps2utc(self.wn, self.tow) + ' '
        while self.read_madoca():
            msg += f'RTCM {self.msgnum}({self.ssr.ssr_nsat}) '
        return msg

    def show_cssr_msg(self):
        ''' returns decoded message '''
        if self.sf_ind:         # first data part
            self.dpn = 1
            self.payload = bitstring.BitStream(self.dpart)
            if not self.ssr.decode_cssr_head(self.payload): # could not decode CSSR head
                self.payload = bitstring.BitStream()
            elif self.ssr.subtype == 1:
                self.payload.pos = 0  # restore position
                self.sfn = 1
                self.run = True
            else:
                if self.run:  # first data part but subtype is not ST1
                    self.payload.pos = 0  # restore position
                    self.sfn += 1
                else:  # first data part but ST1 has not been received
                    self.payload = bitstring.BitStream()
        else:  # continual data part
            if self.run:
                self.dpn += 1
                if self.dpn == 6:  # data part number should be less than 6
                    self.trace.show(1, "Warning: too many datapart")
                    self.run = False
                    self.dpn = 0
                    self.sfn = 0
                    self.payload = bitstring.BitStream()
                else:  # append next data part to the payload
                    pos = self.payload.pos  # save position
                    self.payload += self.dpart
                    self.payload.pos = pos  # restore position
        msg = ''
        if self.sfn != 0:
            msg += ' SF' + str(self.sfn) + ' DP' + str(self.dpn)
            if self.vendor == "MADOCA-PPP":
                msg += f' ({self.servid} {self.msg_ext})'
        #pos = self.payload.pos  # save position
        if self.read_cssr():  # found a CSSR message
            msg += f' ST{self.ssr.subtype}'
            #self.trace.show(1, f"1: pos={pos} payload.pos={self.payload.pos}")
            #pos = self.payload.pos  # save position
            while self.read_cssr():  # try to decode next message
                msg += f' ST{self.ssr.subtype}'
                #self.trace.show(1, f"2: pos={pos} payload.pos={self.payload.pos}")
                #pos = self.payload.pos  # save position
            #zeros = self.payload[pos:].all(0)
            #zeros = self.payload.all(0)
            #if not zeros:   # continues to next datapart
            if not self.payload.all(0):   # continues to next datapart
                #self.trace.show(1, f"3: pos={pos} payload.pos={self.payload.pos}")
                #self.payload.pos = pos  # restore position
                self.payload.pos = 0
                msg += f' ST{self.ssr.subtype}' + \
                    self.trace.msg(0, '...', fg='yellow')
            else:  # end of message in the subframe
                self.payload = bitstring.BitStream()
        else:  # could not decode CSSR any messages
            if self.run and self.ssr.subtype == 0:  # whole message is null
                msg += self.trace.msg(0, ' (null)', dec='dark')
                self.payload = bitstring.BitStream()
            elif self.run:  # or, continual message
                #self.payload.pos = pos  # restore position
                self.payload.pos = 0
                msg += f' ST{self.ssr.subtype}' + \
                    self.trace.msg(0, '...', 'yellow')
            else:  # ST1 mask message has not been found yet
                #self.payload.pos = pos  # restore position
                self.payload.pos = 0
                msg += self.trace.msg(0, ' (syncing)', dec='dark')
        return msg

    def show_qznma_msg(self):
        '''returns decoded message'''
        payload = bitstring.BitStream(self.dpart)
        return self.qznma.decode(payload)

    def show_unknown_msg(self):
        '''returns decoded message'''
        payload = bitstring.BitStream(self.dpart)
        self.trace.show(2, f"Unknown dump: {payload.bin}")
        return ''

# EOF
