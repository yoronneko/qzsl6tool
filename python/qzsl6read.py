#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# qzsl6read.py: quasi-zenith satellite (QZS) L6 message read
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022-2024 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.
#
# References:
# [1] Cabinet Office, Government of Japan, Quasi-Zenith Satellite System
#     Interface Specification Centimeter Level Augmentation Service,
#     IS-QZSS-L6-005, Sept. 21, 2022.
# [2] Global Positioning Augmentation Service Corporation (GPAS),
#     Quasi-Zenith Satellite System Correction Data on Centimeter Level
#     Augmentation Service for Experiment Data Format Specification,
#     1st ed., Nov. 2017.
# [3] Cabinet Office, Government of Japan, Quasi-Zenith Satellite System
#     Interface Specification Multi-GNSS Advanced Orbit and Clock Augmentation
#     - Precise Point Positioning, IS-QZSS-MDC-002, Nov., 2023.
# [4] Radio Technical Commission for Maritime Services (RTCM),
#     Differential GNSS (Global Navigation Satellite Systems) Services
#     - Version 3, RTCM Standard 10403.3, Apr. 24 2020.

import argparse
import os
import sys

sys.path.append(os.path.dirname(__file__))
import libgnsstime
import libqznma
import libssr
import libtrace
from   rtcmread import send_rtcm, msgnum2satsys, msgnum2mtype

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
    dpn      = 0                      # data part number
    sfn      = 0                      # subframe number
    prn      = 0                      # psedudo random noise number
    vendor   = ''                     # vendor name
    facility = ''                     # facility name
    servid   = ''                     # service name
    msg_ext  = ''                     # extension (LNAV or CNAV)
    sf_ind   = 0                      # subframe indicator (0 or 1)
    alert    = 0                      # alert flag (0 or 1)
    run      = False                  # CSSR decode in progress
    payload  = bitstring.BitStream()  # QZS L6 payload
    hepoch   = 0                      # hourly epoch
    interval = 0                      # update interval
    mmi      = 0                      # multiple message indication
    iod      = 0                      # SSR issue of data

    def __init__(self, trace, stat):
        self.trace   = trace
        self.stat    = stat
        self.fp_rtcm = None
        self.ssr     = libssr.Ssr(trace)
        self.qznma   = libqznma.Qznma(trace)

    def __del__(self):
        if self.stat:
            self.ssr.show_cssr_stat()

    def read(self):  # ref. [1]
        ''' reads L6 message and returns True if success in read '''
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
        rs       = b[pos:pos+ 32]; pos +=  32  # not used
        vid = mtid >> 5                        # vender ID
        if   vid == 0b001: self.vendor = "MADOCA"
        elif vid == 0b010: self.vendor = "MADOCA-PPP"
        elif vid == 0b011: self.vendor = "QZNMA"
        elif vid == 0b101: self.vendor = "CLAS"
        else:              self.vendor = f"vendor 0b{vid:03b}"
        self.facility = "Kobe" if (mtid >> 4) & 1 else "Hitachi-Ota"
        self.facility += ":" + str((mtid >> 3) & 1)
        self.servid   = "Iono" if (mtid >> 2) & 1 else "Clk/Eph"
        self.msg_ext  = "CNAV" if (mtid >> 1) & 1 else "LNAV"
        self.sf_ind   = mtid & 1  # subframe indicator
        bdata         = bitstring.BitStream(data)
        self.alert    = bdata[0]
        self.dpart    = bdata[1:]
        return True

    def show(self):
        ''' calls message decode functions and shows the messages '''
        msg = self.trace.msg(0, f'{self.prn} {self.facility:13s}', fg='green')
        if self.alert:
            msg += self.trace.msg(0, '* ', fg='red')
        else:
            msg += '  '
        msg += self.trace.msg(0, self.vendor, fg='yellow') + ' '
        if self.vendor == "MADOCA":
            msg += self.show_madoca_msg()
        elif self.vendor == "MADOCA-PPP" and self.servid == "Iono":
            msg += self.show_mdcppp_iono_msg()
        elif self.vendor in {"CLAS", "MADOCA-PPP"}:
            msg += self.show_cssr_msg()
        elif self.vendor == "QZNMA":
            msg += self.show_qznma_msg()
        else:  # unknown vendor
            msg += self.show_unknown_msg()
        self.trace.show(0, msg)

    def show_madoca_msg(self):
        ''' returns decoded (old) MADOCA messages '''
        self.tow   = self.dpart.read('u20')
        self.wn    = self.dpart.read('u13')
        self.dpart = self.dpart[self.dpart.pos:]  # discard decoded part
        self.dpart.pos = 0
        msg   = libgnsstime.gps2utc(self.wn, self.tow) + ' '
        while self.decode_madoca():
            msg += f'RTCM {self.ssr.msgnum}({self.ssr.ssr_nsat}) '
        return msg

    def decode_madoca(self):  # ref. [2]
        ''' decodes (old) MADOCA messages and returns True if success '''
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
        if self.fp_rtcm:
            send_rtcm(self.fp_rtcm, self.dpart[0:self.dpart.pos])
        self.dpart = self.dpart[self.dpart.pos:]  # discard decoded part
        self.dpart.pos = 0
        self.ssr.msgnum = msgnum
        return True

    def show_cssr_msg(self):
        ''' returns decoded CSSR messages '''
        if self.sf_ind:  # first data part
            self.dpn = 1
            self.payload = bitstring.BitStream(self.dpart)
            if not self.ssr.decode_cssr_head(self.payload):  # could not decode CSSR head
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
                    self.trace.show(1, "Warning: too many datapart", fg='red')
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
        if self.read_cssr():  # found a CSSR message
            msg += f' ST{self.ssr.subtype}'
            while self.read_cssr():  # try to decode next message
                msg += f' ST{self.ssr.subtype}'
            if not self.payload.all(0):   # continues to next datapart
                self.payload.pos = 0
                msg += f' ST{self.ssr.subtype}' + self.trace.msg(0, '...', fg='yellow')
            else:  # end of message in the subframe
                self.payload = bitstring.BitStream()
        else:  # could not decode CSSR any messages
            if self.run and self.ssr.subtype == 0:  # whole message is null
                msg += self.trace.msg(0, ' (null)', dec='dark')
                self.payload = bitstring.BitStream()
            elif self.run:  # or, continual message
                self.payload.pos = 0
                msg += f' ST{self.ssr.subtype}' + self.trace.msg(0, '...', 'yellow')
            else:  # ST1 mask message has not been found yet
                self.payload.pos = 0
                msg += self.trace.msg(0, ' (syncing)', dec='dark')
        return msg

    def read_cssr(self):  # ref. [1, 3]
        ''' reads CSSR messages and returns True if success '''
        if not self.run:
            return False
        if not self.ssr.decode_cssr_head(self.payload):
            return False
        if self.ssr.msgnum != 4073:
            self.trace.show(0, f"Unknown message number: {self.ssr.msgnum}", fg='red')
            return False
        # CLAS (ref.[1]) and MADOCA-PPP orbit & clock augmentation (ref.[3])
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
            if self.fp_rtcm:
                send_rtcm(self.fp_rtcm, self.payload[:self.payload.pos])  # RTCM MT 4073
            self.payload = self.payload[self.payload.pos:]  # discard decoded part
            self.payload.pos = 0
        return decoded

    def show_qznma_msg(self):
        ''' returns decoded QZNMA messages '''
        payload = bitstring.BitStream(self.dpart)
        return self.qznma.decode(payload)

    def show_mdcppp_iono_msg(self):
        ''' returns decoded MADOCA-PPP ionospheric messages '''
        if self.sf_ind:  # first data part
            self.dpn = 1
            self.payload = bitstring.BitStream(self.dpart)
            if not self.ssr.decode_mdcppp_iono_head(self.payload):  # could not decode CSSR head
                if not self.payload.all(0):
                    self.trace.show(1, f"found sf_ind but couldn't decode: {self.payload.bin}", fg='cyan')
                self.payload = bitstring.BitStream()
                self.run = False
            else:
                self.payload.pos = 0  # restore position
                self.sfn = 1
                self.run = True
        else:  # continual data part
            if self.run:
                self.dpn += 1
                pos = self.payload.pos  # save position
                self.payload += self.dpart # append next data part to the payload
                self.payload.pos = pos  # restore position
            # else:
                # if not self.dpart.all(0):
                    # self.trace.show(1, f"continual but couldn't decode: {self.dpart.bin}", fg='cyan')
        msg = f' ({self.servid})'
        if self.read_mdcppp_iono():
            msg += self.brief_disp_mdcppp_iono()
            while self.read_mdcppp_iono():
                msg += self.brief_disp_mdcppp_iono()
            if self.payload and not self.payload.all(0):
                self.payload.pos = 0
                msg += self.trace.msg(0, '...', fg='yellow')
            else:
                self.payload = bitstring.BitStream()
        else:
            if not self.payload or self.payload.all(0):
                msg += self.trace.msg(0, ' (null)', dec='dark')
            else:
                msg += self.trace.msg(1, f'Undecoded message: {self.payload.bin}', fg='red')
            # msg += f' run={self.run}' # msgnum={self.ssr.msgnum}'
            # if self.run and self.ssr.msgnum == 0:  # no message in the subframe
            #     msg += self.trace.msg(0, ' (null)', dec='dark')
            #     self.payload = bitstring.BitStream()
            # elif self.run:
            #     self.payload.pos = 0
            #     msg += self.trace.msg(0, '...', fg='yellow')
            # else:  # subframe indication has not been received
            #     self.payload.pos = 0
            #     # msg += self.trace.msg(0, ' (syncing)', dec='dark')
        return msg

    def brief_disp_mdcppp_iono(self):
        ''' returns brief display of MADOCA-PPP ionospheric messages '''
        msg = f' MT{self.ssr.msgnum}(IOD={self.ssr.iodssr}, Reg{self.ssr.region_id}'
        if self.ssr.msgnum == 1:
            msg += f', {self.ssr.n_areas})'
        else:
            msg += f' #{self.ssr.area})'
        return self.trace.msg(0, msg, fg='cyan')

    def read_mdcppp_iono(self):
        ''' reads MADOCA-PPP ionospheric messages and returns True if success '''
        if not self.run:
            return False
        if not self.ssr.decode_mdcppp_iono_head(self.payload):
            return False
        if self.ssr.msgnum == 1:
            decoded = self.ssr.decode_mdcppp_mt1(self.payload)
        elif self.ssr.msgnum == 2:
            decoded = self.ssr.decode_mdcppp_mt2(self.payload)
        else:
            self.trace.show(1, f"Unknown message number: {self.ssr.msgnum}", fg='red')
            decoded = False
        if decoded:
            self.payload = self.payload[self.payload.pos:]  # discard decoded part
            self.payload.pos = 0
        return decoded

    def show_unknown_msg(self):
        ''' returns dump of unknown messages '''
        payload = bitstring.BitStream(self.dpart)
        self.trace.show(2, f"Unknown dump: {payload.bin}")
        return ''


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Quasi-zenith satellite (QZS) L6 message read')
    parser.add_argument(
        '-c', '--color', action='store_true',
        help='apply ANSI color escape sequences even for non-terminal.')
    parser.add_argument(
        '-m', '--message', action='store_true',
        help='show display messages to stderr')
    parser.add_argument(
        '-r', '--rtcm', action='store_true',
        help='send RTCM messages to stdout (it also turns off display messages unless -m is specified).')
    parser.add_argument(
        '-s', '--statistics', action='store_true',
        help='show CSSR statistics in display messages.')
    parser.add_argument(
        '-t', '--trace', type=int, default=0,
        help='show display verbosely: 1=subtype detail, 2=subtype and bit image.')
    args = parser.parse_args()
    fp_disp, fp_rtcm = sys.stdout, None
    if args.trace < 0:
        libtrace.err(f'trace level should be positive ({args.trace}).')
        sys.exit(1)
    if args.rtcm:  # RTCM message output to stdout
        fp_disp, fp_rtcm = None, sys.stdout
    if args.message:  # show QZS message to stderr
        fp_disp = sys.stderr
    trace = libtrace.Trace(fp_disp, args.trace, args.color)
    qzsl6 = QzsL6(trace, args.statistics)
    qzsl6.fp_rtcm = fp_rtcm
    try:
        while qzsl6.read():
            qzsl6.show()
    except (BrokenPipeError, IOError):
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(1)
    except KeyboardInterrupt:
        libtrace.warn("User break - terminated")
        sys.exit()

# EOF
