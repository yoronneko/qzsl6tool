#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# libqzsl6.py: library for QZS L6 message processing
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022 Satoshi Takahashi
#
# Released under BSD 2-clause license.
#
# References:
# [1] Cabinet Office of Japan, Quasi-Zenith Satellite System Interface
#     Specification Centimeter Level Augmentation Service,
#     IS-QZSS-L6-005, Sept. 21, 2022.
# [2] Global Positioning Augmentation Service Corporation (GPAS),
#     Quasi-Zenith Satellite System Correction Data on Centimeter Level
#     Augmentation Serice for Experiment Data Format Specification,
#     1st ed., Nov. 2017.
# [3] Cabinet Office of Japan, Quasi-Zenith Satellite System Interface
#     Specification Multi-GNSS Advanced Orbit and Clock Augmentation
#     - Precise Point Positioning, IS-QZSS-MDC-001, Feb., 2022.
# [4] Radio Technical Commission for Maritime Services (RTCM),
#     Differential GNSS (Global Navigation Satellite Systems) Services
#     - Version 3, RTCM Standard 10403.3, Apr. 24 2020.

import sys
import gps2utc
import libcolor
import libssr
from librtcm import send_rtcm, msgnum2satsys, msgnum2mtype
try:
    import bitstring
except ModuleNotFoundError:
    print('''\
    QZS L6 Tool needs bitstring module.
    Please install this module such as \"pip install bitstring\".
    ''', file=sys.stderr)
    sys.exit(1)

class QzsL6:
    "Quasi-Zenith Satellite L6 message process class"
# --- private
    dpart = bitstring.BitArray()    # data part
    dpn = 0                         # data part number
    sfn = 0                         # subframe number
    prn = 0                         # psedudo random noise number
    vendor = ''                     # vendor name
    facility = ''                   # facility name
    servid = ''                     # service name
    msg_ext = ''                    # extension (LNAV or CNAV)
    sf_ind = 0                      # subframe indicator (0 or 1)
    alert = 0                       # alert flag (0 or 1)
    run = False                     # CSSR decode in progress
    payload = bitstring.BitArray()  # QZS L6 payload
    msgnum = 0                      # message type number
    hepoch = 0                      # hourly epoch
    interval = 0                    # update interval
    mmi = 0                         # multiple message indication
    iod = 0                         # SSR issue of data

    def __init__(self, fp_rtcm, fp_disp, t_level, color, stat):
        self.fp_rtcm = fp_rtcm
        self.fp_disp = fp_disp
        self.t_level = t_level
        self.msg_color = libcolor.Color(fp_disp, color)
        self.stat = stat
        self.ssr = libssr.Ssr(fp_disp, t_level, self.msg_color)

    def __del__(self):
        if self.stat:
            ssr.show_cssr_stat()

# --- public
    def read_l6_msg(self):  # ref. [1]
        sync = [b'0x00' for i in range(4)]
        ok = False
        try:
            while not ok:
                b = sys.stdin.buffer.read(1)
                if not b:
                    return False
                sync = sync[1:4] + [b]
                if sync == [b'\x1a', b'\xcf', b'\xfc', b'\x1d']:
                    ok = True
            b = sys.stdin.buffer.read(1+1+212+32)
            if not b:
                return False
        except KeyboardInterrupt:
            color = libcolor.Color(sys.stderr)
            print(color.fg('yellow') + \
                  "User break - terminated" + \
                  color.fg(), file=sys.stderr)
            return False
        pos = 0
        self.prn = int.from_bytes(b[pos:pos+1], 'big')
        pos += 1
        mtid = int.from_bytes(b[pos:pos+1], 'big')
        pos += 1
        dpart = bitstring.BitArray(b[pos:pos+212])
        pos += 212
        rs = b[pos:pos+32]
        vid = mtid >> 5  # vender ID
        if vid == 0b001:
            self.vendor = "MADOCA"
        elif vid == 0b010:
            self.vendor = "MADOCA-PPP"
        elif vid == 0b011:
            self.vendor = "QZNMA"
        elif vid == 0b101:
            self.vendor = "CLAS"
        else:
            self.vendor = f"vendor 0b{vid:03b}"
        self.facility = "Kobe" if (mtid >> 4) & 1 else "Hitachi-Ota"
        self.facility += ":" + str((mtid >> 3) & 1)
        self.servid = "Ionosph" if (mtid >> 2) & 1 else "Clk/Eph"
        self.msg_ext = "CNAV" if (mtid >> 1) & 1 else "LNAV"
        self.sf_ind = mtid & 1  # subframe indicator
        self.alert = dpart[0:1]
        self.dpart = dpart[1:]
        return True

    def show_l6_msg(self):
        if self.vendor == "MADOCA":
            msg = self.show_mdc_msg()
        elif self.vendor in {"CLAS", "MADOCA-PPP"}:
            msg = self.show_cssr_msg()
        elif self.vendor == "QZNMA":
            msg = self.show_qznma_msg()
        else:  # unknown vendor
            msg = self.show_unknown_msg()
        if not self.fp_disp:
            return
        try:
            message = self.msg_color.fg('green')
            message += f'{self.prn} {self.facility:13s}'
            if self.alert:
                message += self.msg_color.fg('red') + '* '
            else:
                message += '  '
            message += self.msg_color.fg('yellow') + self.vendor
            message += self.msg_color.fg() + ' ' + msg
            print(message, file=self.fp_disp)
        except (BrokenPipeError, IOError):
            sys.exit()

# --- private
    def trace(self, level, *args):
        if self.t_level < level:
            return
        for arg in args:
            try:
                print(arg, end='', file=self.fp_disp)
            except (BrokenPipeError, IOError):
                sys.exit()

    def mdc2rtcm(self):  # ref. [2]
        '''returns true if success in decoding MADOCA'''
        if len(self.dpart) < 12:
            return False
        pos = 0
        msgnum = self.dpart[pos:pos + 12].uint
        pos += 12
        if msgnum == 0:
            return False
        satsys = msgnum2satsys(msgnum)
        mtype = msgnum2mtype(msgnum)
        pos = self.ssr.ssr_decode_head(self.dpart, pos, satsys, mtype)
        if mtype == 'SSR orbit':
            pos, msg= self.ssr.ssr_decode_orbit(self.dpart, pos, satsys)
        elif mtype == 'SSR clock':
            pos, msg= self.ssr.ssr_decode_clock(self.dpart, pos, satsys)
        elif mtype == 'SSR code bias':
            pos, msg = self.ssr.ssr_decode_code_bias(self.dpart, pos, satsys)
        elif mtype == 'SSR URA':
            pos, msg = self.ssr.ssr_decode_ura(self.dpart, pos, satsys)
        elif mtype == 'SSR hr clock':
            pos, msg = self.ssr.ssr_decode_hr_clock(self.dpart, pos, satsys)
        else:
            raise Exception(f'unsupported message type: {msgnum}')
        if pos % 8 != 0:  # byte align
            pos += 8 - (pos % 8)
        send_rtcm(self.fp_rtcm, self.dpart[0:pos])
        del self.dpart[0:pos]
        self.msgnum = msgnum
        return True

    def cssr2rtcm(self):  # ref. [1]
        '''returns bit size of CSSR data'''
        if not self.run:
            return 0
        pos = self.ssr.decode_cssr_head(self.payload)
        if pos == 0:
            return 0
        if self.ssr.subtype == 1:
            pos = self.ssr.decode_cssr_st1(self.payload, pos)
        elif self.ssr.subtype == 2:
            pos = self.ssr.decode_cssr_st2(self.payload, pos)
        elif self.ssr.subtype == 3:
            pos = self.ssr.decode_cssr_st3(self.payload, pos)
        elif self.ssr.subtype == 4:
            pos = self.ssr.decode_cssr_st4(self.payload, pos)
        elif self.ssr.subtype == 5:
            pos = self.ssr.decode_cssr_st5(self.payload, pos)
        elif self.ssr.subtype == 6:
            pos = self.ssr.decode_cssr_st6(self.payload, pos)
        elif self.ssr.subtype == 7:
            pos = self.ssr.decode_cssr_st7(self.payload, pos)
        elif self.ssr.subtype == 8:
            pos = self.ssr.decode_cssr_st8(self.payload, pos)
        elif self.ssr.subtype == 9:
            pos = self.ssr.decode_cssr_st9(self.payload, pos)
        elif self.ssr.subtype == 10:
            pos = self.ssr.decode_cssr_st10(self.payload, pos)
        elif self.ssr.subtype == 11:
            pos = self.ssr.decode_cssr_st11(self.payload, pos)
        elif self.ssr.subtype == 12:
            pos = self.ssr.decode_cssr_st12(self.payload, pos)
        else:
            raise Exception(f"Unknown CSSR subtype: {self.ssr.subtype}")
        if 0 < pos:
            send_rtcm(self.fp_rtcm, self.payload[:pos])  # RTCM MT 4073
            self.payload = self.payload[pos:]
        return pos

    def show_mdc_msg(self):
        '''returns decoded message'''
        dpart = self.dpart
        pos = 0
        self.tow = dpart[pos:pos+20].uint
        pos += 20
        self.wn = dpart[pos:pos+13].uint
        pos += 13
        self.dpart = dpart[pos:]
        message = gps2utc.gps2utc(self.wn, self.tow) + ' '
        while self.mdc2rtcm():
            message += f'RTCM {self.msgnum}({self.ssr.ssr_nsat}) '
        return message

    def show_cssr_msg(self):
        '''returns decoded message'''
        if self.sf_ind:  # first data part
            self.dpn = 1
            self.payload = bitstring.BitArray(self.dpart)
            if not self.ssr.decode_cssr_head(self.payload):
                self.payload = bitstring.BitArray()
            elif self.ssr.subtype == 1:
                self.sfn = 1
                self.run = True
            else:
                if self.run:  # first data part but subtype is not ST1
                    self.sfn += 1
                else:  # first data part but ST1 has not beed received
                    self.payload = bitstring.BitArray()
        else:  # continual data part
            if self.run:
                self.dpn += 1
                if self.dpn == 6:  # data part number should be less than 6
                    self.trace(1, "Warning: too many datapart\n")
                    self.run = False
                    self.dpn = 0
                    self.sfn = 0
                    self.payload = bitstring.BitArray()
                else:
                    self.payload.append(self.dpart)
        message = ''
        if self.sfn != 0:
            message += ' SF' + str(self.sfn) + ' DP' + str(self.dpn)
            if self.vendor == "MADOCA-PPP":
                message += f' ({self.servid} {self.msg_ext})'
        if not self.cssr2rtcm():  # could not decode CSSR any messages
            if self.run and self.ssr.subtype == 0:  # whole message is null
                message += self.msg_color.dec('dark')
                message += ' (null)'
                message += self.msg_color.dec()
                self.payload = bitstring.BitArray()
            elif self.run:  # or, continual message
                message += f' ST{self.ssr.subtype}' + \
                    self.msg_color.fg('yellow') + '...' + \
                    self.msg_color.fg()
            else:  # ST1 mask message has not been found yet
                message += self.msg_color.dec('dark')
                message += ' (syncing)'
                message += self.msg_color.dec()
        else:  # found a CSSR message
            message += f' ST{self.ssr.subtype}'
            while self.cssr2rtcm():  # try to decode next message
                message += f' ST{self.ssr.subtype}'
            if self.ssr.subtype != 0:  # continues to next datapart
                message += f' ST{self.ssr.subtype}' + \
                    self.msg_color.fg('yellow') + '...' + \
                    self.msg_color.fg()
            else:  # end of message in the subframe
                self.payload = bitstring.BitArray()
        return message

    def show_qznma_msg(self):
        '''returns decoded message'''
        payload = bitstring.BitArray(self.dpart)
        self.trace(2, f"QZNMA dump: {payload.bin}\n")
        return ''

    def show_unknown_msg():
        '''returns decoded message'''
        payload = bitstring.BitArray(self.dpart)
        self.trace(2, f"Unknown dump: {payload.bin}\n")
        return ''

# EOF
