#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# libqzsl6.py: library for QZS L6 message processing
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022 Satoshi Takahashi
#
# Released under BSD 2-clause license.

import sys
import gps2utc
import libcolor
import libcssr
import libqzsl6tool
import librtcm
try:
    import bitstring
except ModuleNotFoundError:
    print('''\
    QZS L6 Tool needs bitstring module.
    Please install this module such as \"pip install bitstring\".
    ''', file=sys.stderr)
    sys.exit(1)

class QzsL6(libcssr.Cssr, librtcm.Rtcm):
    "Quasi-Zenith Satellite L6 message process class"
# public
    fp_msg = sys.stdout             # message output file pointer
# private
    dpart = bitstring.BitArray()    # data part
    dpn = 0                         # data part number
    sfn = 0                         # subframe number
    vendor = ''                     # QZS L6 vendor name
    prn = 0                         # psedudo random noise number
    vendor = ''                     # vendor name
    facility = ''                   # facility name
    servid = ''                     # L6 message service name
    msg_ext = ''                    # L6 message extension (LNAV or CNAV)
    sf_ind = 0                      # subframe indicator (0 or 1)
    alert = 0                       # alert flag (0 or 1)
    run = False                     # CSSR decode in progress
    payload = bitstring.BitArray()  # QZS L6 payload
    msgnum = 0                      # L6 message type number
    subtype = 0                     # L6 subtype number
    hepoch = 0                      # L6 hourly epoch
    interval = 0                    # L6 update interval
    mmi = 0                         # L6 multiple message indication
    iod = 0                         # SSR issue of data
    rtcm = bitstring.BitArray()     # RTCM payload

    def __init__(self):
        pass

    def __del__(self):
        if self.stat:
            self.show_cssr_stat()

    def receive_l6_msg(self):
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
            print("User break - terminated", file=sys.stderr)
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
            vendor = "MADOCA"
        elif vid == 0b010:
            vendor = "MADOCA-PPP"
        elif vid == 0b011:
            vendor = "QZNMA"
        elif vid == 0b101:
            vendor = "CLAS"
        else:
            vendor = f"unknown (vendor ID 0b{vid:03b})"
        self.vendor = vendor
        facility = "Kobe" if (mtid >> 4) & 1 else "Hitachi-Ota"
        facility += ":" + str((mtid >> 3) & 1)
        self.facility = facility
        self.servid = "Ionosph" if (mtid >> 2) & 1 else "Clk/Eph"
        self.msg_ext = "CNAV" if (mtid >> 1) & 1 else "LNAV"
        self.sf_ind = mtid & 1  # subframe indicator
        self.alert = dpart[0:1].uint
        self.dpart = dpart[1:]
        return True

    def mdc2rtcm(self):
        '''returns true if success in decoding MADOCA'''
        if len(self.dpart) < 12:
            return False
        pos = 0
        msgnum = self.dpart[pos:pos + 12].uint
        pos += 12
        if msgnum == 0:
            return False
        num_processed_bits = self.decode_ssr(msgnum, self.dpart[pos:])
        if num_processed_bits == 0:
            return False
        pos += num_processed_bits
        if pos % 8 != 0:  # byte align
            pos += 8 - (pos % 8)
        self.rtcm = self.dpart[0:pos].tobytes()
        del self.dpart[0:pos]
        self.msgnum = msgnum
        return True

    def cssr2rtcm(self):
        '''returns bit size of CSSR data'''
        if not self.run:
            return 0
        datasize = self.decode_cssr_head()
        if datasize == 0:
            return 0
        if self.subtype == 1:
            datasize = self.decode_cssr_st1(self.payload, datasize)
        elif self.subtype == 2:
            datasize = self.decode_cssr_st2(self.payload, datasize)
        elif self.subtype == 3:
            datasize = self.decode_cssr_st3(self.payload, datasize)
        elif self.subtype == 4:
            datasize = self.decode_cssr_st4(self.payload, datasize)
        elif self.subtype == 5:
            datasize = self.decode_cssr_st5(self.payload, datasize)
        elif self.subtype == 6:
            datasize = self.decode_cssr_st6(self.payload, datasize)
        elif self.subtype == 7:
            datasize = self.decode_cssr_st7(self.payload, datasize)
        elif self.subtype == 8:
            datasize = self.decode_cssr_st8(self.payload, datasize)
        elif self.subtype == 9:
            datasize = self.decode_cssr_st9(self.payload, datasize)
        elif self.subtype == 10:
            datasize = self.decode_cssr_st10(self.payload, datasize)
        elif self.subtype == 11:
            datasize = self.decode_cssr_st11(self.payload, datasize)
        elif self.subtype == 12:
            datasize = self.decode_cssr_st12(self.payload, datasize)
        else:
            raise Exception(f"Unknown CSSR subtype: {self.subtype}")
        if 0 < datasize:
            self.rtcm = self.payload[:datasize].tobytes()
            self.payload = self.payload[datasize:]
        return datasize

    def decode_cssr_head(self):
        '''returns bit size of cssr header'''
        payload = self.payload
        len_payload = len(payload)
        pos = 0
        if '0b1' not in payload:  # Zero padding detection
            self.trace(2, f"CSSR null data {len(self.payload.bin)} bits\n")
            self.trace(2, f"CSSR dump: {self.payload.bin}\n")
            self.stat_bnull += len(self.payload.bin)
            self.payload = bitstring.BitArray()
            self.subtype = 0  # no subtype number
            return 0
        if len_payload < 12:
            self.msgnum = 0   # could not retreve the message number
            self.subtype = 0  # could not retreve the subtype number
            return 0
        self.msgnum = payload[pos:pos + 12].uint
        pos += 12  # message num, 4073
        if self.msgnum != 4073:  # CSSR message number should be 4073
            self.trace(2, f"CSSR msgnum should be 4073 ({self.msgnum})\n")
            self.trace(2, f"{len(self.payload.bin)} bits\n")
            self.trace(2, f"CSSR dump: {self.payload.bin}\n")
            self.stat_bnull += len(self.payload.bin)
            self.payload = bitstring.BitArray()
            self.subtype = 0  # no subtype number
            return 0
        if len_payload < pos + 4:
            self.subtype = 0  # could not retreve the subtype number
            return 0
        self.subtype = payload[pos:pos + 4].uint  # subtype
        pos += 4
        if self.subtype == 1:  # Mask message
            if len_payload < pos + 20:  # could not retreve the epoch
                return 0
            self.epoch = payload[pos:pos + 20].uint  # GPS epoch time 1s
            pos += 20
        elif self.subtype == 10:  # Service Information
            return pos
        else:
            if len_payload < pos + 12:  # could not retreve the hourly epoch
                return 0
            self.hepoch = payload[pos:pos + 12].uint  # GNSS hourly epoch
            pos += 12
        if len_payload < pos + 4 + 1 + 4:
            return 0
        self.interval = payload[pos:pos + 4].uint  # update interval
        pos += 4
        self.mmi = payload[pos:pos + 1].uint  # multiple message indication
        pos += 1
        self.iod = payload[pos:pos + 4].uint  # SSR issue of data
        pos += 4
        return pos

    def show_l6_msg(self):
        if self.vendor == "MADOCA":
            self.show_mdc_msg()
        elif self.vendor in {"CLAS", "MADOCA-PPP"}:
            self.show_cssr_msg()
        elif self.vendor == "QZNMA":
            self.show_qznma_msg()
        else:  # unknown vendor
            self.show_unknown_msg()

    def show_msg(self, msg):
        if not self.fp_msg:
            return
        try:
            msg_color = libcolor.Color(self.fp_msg)
            message = msg_color.fg('green')
            message += f'{self.prn} {self.facility:13s}'
            if self.alert:
                message += msg_color.fg('red') + '* '
            else:
                message += '  '
            message += msg_color.fg('yellow') + self.vendor
            message += msg_color.fg('default') + ' ' + msg
            print(message, file=self.fp_msg)
        except (BrokenPipeError, IOError):
            sys.exit()

    def show_mdc_msg(self):
        dpart = self.dpart
        pos = 0
        self.tow = dpart[pos:pos + 20].uint
        pos += 20
        self.wn = dpart[pos:pos + 13].uint
        pos += 13
        self.dpart = dpart[pos:]
        message = gps2utc.gps2utc(self.wn, self.tow) + ' '
        while self.mdc2rtcm():
            message += 'RTCM ' + str(self.msgnum) + \
                       '(' + str(self.numsat) + ') '
            self.send_rtcm(self.rtcm)
        self.show_msg(message)

    def show_cssr_msg(self):
        if self.sf_ind:  # first data part
            self.dpn = 1
            self.payload = bitstring.BitArray(self.dpart)
            if not self.decode_cssr_head():
                self.payload = bitstring.BitArray()
            elif self.subtype == 1:
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
        msg_color = libcolor.Color(self.fp_msg)
        if self.sfn != 0:
            message += ' SF' + str(self.sfn) + ' DP' + str(self.dpn)
            if self.vendor == "MADOCA-PPP":
                message += f' ({self.servid} {self.msg_ext})'
        if not self.cssr2rtcm():  # could not decode any message
            if self.run and self.subtype == 0:  # whole message is null
                message += msg_color.dec('dark')
                message += ' (null)'
                message += msg_color.dec('default')
            elif self.run:  # continual message
                message += f' ST{self.subtype}' + \
                    msg_color.fg('yellow') + '...' + \
                    msg_color.fg('default')
        else:
            message += f' ST{self.subtype}'
            self.send_rtcm(self.rtcm)
            while self.cssr2rtcm():  # try to decode next message
                message += f' ST{self.subtype}'
                self.send_rtcm(self.rtcm)
            if len(self.payload) != 0:  # continues to next datapart
                message += f' ST{self.subtype}' + \
                    msg_color.fg('yellow') + '...' + \
                    msg_color.fg('default')
        self.show_msg(message)

    def show_qznma_msg(self):
        payload = bitstring.BitArray(self.dpart)
        self.trace(2, f"QZNMA dump: {payload.bin}\n")
        self.show_msg('')

    def show_unknown_msg():
        payload = bitstring.BitArray(self.dpart)
        self.trace(2, f"Unknown dump: {payload.bin}\n")
        self.show_msg('')

# EOF
