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
import bitstring
import gps2utc
import librtcm
import libcssr
import libqzsl6tool
import libcolor

class QzsL6(libcssr.Cssr, librtcm.Rtcm):
    "Quasi-Zenith Satellite L6 message process class"
    fp_trace = sys.stdout         # file pointer for trace
    fp_rtcm = None                # file pointer for rtcm output
    fp_msg = sys.stdout           # message output file pointer
    dpn = 0                       # data part number
    sfn = 0                       # subframe number
    vendor = ''                   # QZS L6 vendor name
    l6msg = bitstring.BitArray()  # QZS L6 message
    subtype = 0                   # CSSR subtype number
    run = False                   # CSSR decode start
    t_level = 0                   # trace level

    def __init__(self):
        pass

    def __del__(self):
        if self.stat:
            self.show_cssr_stat()

    def trace(self, level, *args):
        if self.t_level < level:
            return
        for arg in args:
            try:
                print(arg, end='', file=self.fp_trace)
            except (BrokenPipeError, IOError):
                sys.exit()

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
            prn = int.from_bytes(sys.stdin.buffer.read(1), 'big')
            mtid = int.from_bytes(sys.stdin.buffer.read(1), 'big')
            dpart = bitstring.BitArray(sys.stdin.buffer.read(212))
            rs = sys.stdin.buffer.read(32)
        except KeyboardInterrupt:
            print("User break - terminated", file=sys.stderr)
            return False
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
        facility = "Kobe" if (mtid >> 4) & 1 else "Hitachi-Ota"
        facility += ":" + str((mtid >> 3) & 1)
        servid = "Ionosph" if (mtid >> 2) & 1 else "Clk/Eph"
        msg_ext = "CNAV" if (mtid >> 1) & 1 else "LNAV"
        sf_ind = mtid & 1  # subframe indicator
        self.prn = prn
        self.vendor = vendor
        self.facility = facility
        self.servid = servid
        self.msg_ext = msg_ext
        self.sf_ind = sf_ind
        self.alert = dpart[0:1].uint
        self.dpart = dpart[1:]
        return True

    def mdc2rtcm(self):
        if len(self.dpart) < 12:
            return False
        self.pos = 0
        msgnum = self.dpart[self.pos:self.pos + 12].uint
        self.pos += 12
        if msgnum == 0:
            return False
        if not self.decode_ssr(msgnum, self.dpart):
            return False
        if self.pos % 8 != 0:
            self.pos += 8 - (self.pos % 8)  # byte align
        self.rtcm = self.dpart[0:self.pos].tobytes()
        del self.dpart[0:self.pos]
        self.msgnum = msgnum
        return True

    def cssr2rtcm(self):
        if not self.run:
            return False
        if not self.decode_cssr_head():
            return False
        if self.subtype == 1:
            return self.decode_cssr_st1()
        elif self.subtype == 2:
            return self.decode_cssr_st2()
        elif self.subtype == 3:
            return self.decode_cssr_st3()
        elif self.subtype == 4:
            return self.decode_cssr_st4()
        elif self.subtype == 5:
            return self.decode_cssr_st5()
        elif self.subtype == 6:
            return self.decode_cssr_st6()
        elif self.subtype == 7:
            return self.decode_cssr_st7()
        elif self.subtype == 8:
            return self.decode_cssr_st8()
        elif self.subtype == 9:
            return self.decode_cssr_st9()
        elif self.subtype == 10:
            return self.decode_cssr_st10()
        elif self.subtype == 11:
            return self.decode_cssr_st11()
        elif self.subtype == 12:
            return self.decode_cssr_st12()
        raise Exception(f"Unknown CSSR subtype: {self.subtype}")

    def decode_cssr_head(self):
        l6msg = self.l6msg
        l6msglen = len(l6msg)
        pos = 0
        if '0b1' not in l6msg:  # Zero padding detection
            self.trace(2, f"CSSR null data {len(self.l6msg.bin)} bits\n")
            self.trace(2, f"CSSR dump: {self.l6msg.bin}\n")
            self.stat_bnull += len(self.l6msg.bin)
            self.l6msg = bitstring.BitArray()
            self.subtype = 0  # no subtype number
            return False
        if l6msglen < 12:
            self.msgnum = 0   # could not retreve the message number
            self.subtype = 0  # could not retreve the subtype number
            return False
        self.msgnum = l6msg[pos:pos + 12].uint
        pos += 12  # message num, 4073
        if self.msgnum != 4073:  # CSSR message number should be 4073
            self.trace(2, f"CSSR msgnum should be 4073 ({self.msgnum})\n")
            self.trace(2, f"{len(self.l6msg.bin)} bits\n")
            self.trace(2, f"CSSR dump: {self.l6msg.bin}\n")
            self.stat_bnull += len(self.l6msg.bin)
            self.l6msg = bitstring.BitArray()
            self.subtype = 0  # no subtype number
            return False
        if l6msglen < pos + 4:
            self.subtype = 0  # could not retreve the subtype number
            return False
        self.subtype = l6msg[pos:pos + 4].uint  # subtype
        pos += 4
        if self.subtype == 10:  # Service Information --- not implemented
            self.pos = pos
            return False
        elif self.subtype == 1:  # Mask message
            if l6msglen < pos + 20:  # could not retreve the epoch
                return False
            self.epoch = l6msg[pos:pos + 20].uint  # GPS epoch time 1s
            pos += 20
        else:
            if l6msglen < pos + 12:  # could not retreve the hourly epoch
                return False
            self.hepoch = l6msg[pos:pos + 12].uint  # GNSS hourly epoch
            pos += 12
        if l6msglen < pos + 4 + 1 + 4:
            return False
        self.interval = l6msg[pos:pos + 4].uint  # update interval
        pos += 4
        self.mmi = l6msg[pos:pos + 1].uint  # multiple message indication
        pos += 1
        self.iod = l6msg[pos:pos + 4].uint  # IOD SSR
        pos += 4
        self.pos = pos
        return True

    def send_rtcm(self):
        if not self.fp_rtcm:
            return
        rtcm = b'\xd3' + len(self.rtcm).to_bytes(2, 'big') + self.rtcm
        rtcm_crc = libqzsl6tool.rtk_crc24q(rtcm, len(rtcm))
        self.fp_rtcm.buffer.write(rtcm)
        self.fp_rtcm.buffer.write(rtcm_crc)
        self.fp_rtcm.flush()

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
                message += msg_color.fg('red') + '*'
            else:
                message += ' '
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
            self.send_rtcm()
        self.show_msg(message)

    def show_cssr_msg(self):
        if self.sf_ind:  # first data part
            self.dpn = 1
            self.l6msg = bitstring.BitArray(self.dpart)
            if not self.decode_cssr_head():
                self.l6msg = bitstring.BitArray()
            elif self.subtype == 1:
                self.sfn = 1
                self.run = True
            else:
                if self.run:  # first data part but subtype is not ST1
                    self.sfn += 1
                else:  # first data part but ST1 has not beed received
                    self.l6msg = bitstring.BitArray()
        else:  # continual data part
            if self.run:
                self.dpn += 1
                if self.dpn == 6:  # data part number should be less than 6
                    self.trace(1, "Warning: too many datapart\n")
                    self.run = False
                    self.dpn = 0
                    self.sfn = 0
                    self.l6msg = bitstring.BitArray()
                else:
                    self.l6msg.append(self.dpart)
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
            self.send_rtcm()
            while self.cssr2rtcm():  # try to decode next message
                message += f' ST{self.subtype}'
                self.send_rtcm()
            if len(self.l6msg) != 0:  # continues to next datapart
                message += f' ST{self.subtype}' + \
                    msg_color.fg('yellow') + '...' + \
                    msg_color.fg('default')
        self.show_msg(message)

    def show_qznma_msg(self):
        l6msg = bitstring.BitArray(self.dpart)
        self.trace(2, f"QZNMA dump: {l6msg.bin}\n")
        self.show_msg('')

    def show_unknown_msg():
        l6msg = bitstring.BitArray(self.dpart)
        self.trace(2, f"Unknown dump: {l6msg.bin}\n")
        self.show_msg('')

# EOF
