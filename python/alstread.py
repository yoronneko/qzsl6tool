#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# alstread.py: Allystar HD9310 option C raw data read
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022-2026 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.
#
# References:
# [1] Justin Yang, QZSS L6 Enabled Multi-band Multi-GNSS Receiver
#     https://docs.datagnss.com/rtk-board/firmware/L6/L6DE_tech_intro.pdf

import argparse
import os
import sys
from typing import TextIO

sys.path.append(os.path.dirname(__file__))
import libgnsstime
import libqzsl6tool
import libtrace

class AllystarReceiver:
    dict_snr  = {}   # SNR dictionary
    dict_data = {}   # payload data dictionary
    last_gpst = 0    # last received GPS time
    l6        = b''  # L6 message

    def __init__(self, trace: libtrace.Trace):
        self.trace = trace

    def read(self):  # ref. [1]
        sync = bytes(4)
        while True:
            b = sys.stdin.buffer.read(1)
            if not b:
                return False
            sync = sync[1:4] + b
            if sync == b'\xf1\xd9\x02\x10':
                break
        l6   = sys.stdin.buffer.read(266)
        csum = sys.stdin.buffer.read(2)
        if not l6 or not csum:
            return False
        l6 = b'\x02\x10' + l6
        len_l6    = int.from_bytes(l6[ 2: 4], 'little')
        self.prn  = int.from_bytes(l6[ 4: 6], 'little') - 700
        freqid    = int.from_bytes(l6[ 6: 7], 'little')
        len_data  = int.from_bytes(l6[ 7: 8], 'little') - 2
        self.gpsw = int.from_bytes(l6[ 8:10], 'big')
        self.gpst = int.from_bytes(l6[10:14], 'big')
        self.snr  = int.from_bytes(l6[14:15], 'big')
        flag      = int.from_bytes(l6[15:16], 'big')
        self.data = l6[16:268]
        if self.last_gpst == 0:
            self.last_gpst = self.gpst
        self.err = ""
        csum1, csum2 = libqzsl6tool.checksum(l6)
        if csum[0] != csum1 or csum[1] != csum2: self.err += "CS "
        if len_l6 != 264                       : self.err += "Payload "
        if len_data !=  63                     : self.err += "Data "
        if flag & 0x01                         : self.err += "RS "
        if flag & 0x02                         : self.err += "Week "
        if flag & 0x04                         : self.err += "TOW "
        return True

    def select_sat(self, s_prn: int) -> None:
        ''' selects satellite and displays message '''
        self.p_prn  = 0    # PRN    of satellite that has the strongest C/No
        self.p_snr  = 0    # C/No   of satellite that has the strongest C/No
        self.l6 = b''  # L6 msg of satellite that has the strongest C/No
        disp_msg = ''
        if self.last_gpst != self.gpst and len(self.dict_snr) != 0:
            # A change in gpst means possible sats data correction is finished.
            self.last_gpst = self.gpst
            if s_prn:  # if specified satellite is used
                self.p_prn = s_prn
            else:      # otherwise, we use the satellite that has max C/No
                self.p_prn = sorted(self.dict_snr.items(),
                           key=lambda x: x[1], reverse=True)[0][0]
            self.p_snr = self.dict_snr.get (self.p_prn, 0)
            self.l6    = self.dict_data.get(self.p_prn, b'')
            disp_msg  += f"---> prn {self.p_prn} (C/No {self.p_snr} dB)\n"
            self.dict_snr.clear()
            self.dict_data.clear()
        # then, we add the current data to the dictionaries when no errors found
        if not self.err:
            self.dict_snr [self.prn] = self.snr
            self.dict_data[self.prn] = self.data
        disp_msg += \
            self.trace.msg(0, f'{self.prn} ', fg='green') + \
            self.trace.msg(0, libgnsstime.gps2utc(self.gpsw, self.gpst // 1000) , fg='yellow') + \
            self.trace.msg(0, f' {self.snr}')
        if self.err:
            disp_msg += self.trace.msg(0, ' ' + self.err, fg='red')
        self.trace.show(0, disp_msg)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description=f'Allystar HD9310 message read, QZS L6 Tool ver.{libqzsl6tool.VERSION}')
    parser_group = parser.add_mutually_exclusive_group()
    parser.add_argument(
        '-c', '--color', action='store_true',
        help='apply ANSI color escape sequences even for non-terminal.')
    parser_group.add_argument(
        '-l', '--l6', action='store_true',
        help='send QZS L6 messages to stdout (it also turns off Allystar and u-blox messages).')
    parser.add_argument(
        '-m', '--message', action='store_true',
        help='show Allystar messages to stderr.')
    parser.add_argument(
        '-p', '--prn', type=int, default=0,
        help='satellite PRN to be specified (0, 193-211).')
    args = parser.parse_args()
    fp_disp, fp_raw = sys.stdout, None
    if args.l6:  # QZS L6 raw message output to stdout
        fp_disp, fp_raw = None, sys.stdout
    if args.message:  # Allystar message to stderr
        fp_disp = sys.stderr
    if (args.prn < 193 or 211 < args.prn) and args.prn != 0:
        libtrace.warn("QZS L6 PRN is in range of 193-211 or 0")
        args.prn = 0
    trace = libtrace.Trace(fp_disp, 0, args.color)
    rcv = AllystarReceiver(trace)
    try:
        while rcv.read():
            rcv.select_sat(args.prn)
            if rcv.l6 and fp_raw:
                fp_raw.buffer.write(rcv.l6)
                fp_raw.flush()
    except (BrokenPipeError, IOError):
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(1)
    except KeyboardInterrupt:
        libtrace.warn("User break - terminated")
        sys.exit()

# EOF
