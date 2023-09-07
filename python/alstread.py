#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# alstread.py: Allystar HD9310 option C raw data reader
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.
#
# References:
# [1] Justin Yang, QZSS L6 Enabled Multi-band Multi-GNSS Receiver
#     https://docs.datagnss.com/rtk-board/firmware/L6/L6DE_tech_intro.pdf

import argparse
import os
import sys

sys.path.append(os.path.dirname(__file__))
import gps2utc
import libcolor

def checksum(payload):  # ref. [1]
    csum1 = 0
    csum2 = 0
    for b in payload:
        csum1 = (csum1 + b    ) & 0xff
        csum2 = (csum1 + csum2) & 0xff
    return csum1, csum2

class AllystarReceiver:
    dict_snr  = {}   # SNR dictionary
    dict_data = {}   # payload data dictionary
    last_gpst = 0    # last received GPS time
    l6        = b''  # L6 message

    def __init__(self, fp_disp, ansi_color):
        self.fp_disp   = fp_disp
        self.msg_color = libcolor.Color(fp_disp, ansi_color)

    def read(self):  # ref. [1]
        sync = bytes(4)
        while True:
            b = sys.stdin.buffer.read(1)
            if not b:
                return False
            sync = sync[1:4] + b
            if sync == b'\xf1\xd9\x02\x10':
                break
        payld = b'\x02\x10' + sys.stdin.buffer.read(266)
        csum = sys.stdin.buffer.read(2)
        if not payld or not csum:
            return False
        len_payld = int.from_bytes(payld[ 2: 4], 'little')
        self.prn  = int.from_bytes(payld[ 4: 6], 'little') - 700
        freqid    = int.from_bytes(payld[ 6: 7], 'little')
        len_data  = int.from_bytes(payld[ 7: 8], 'little') - 2
        self.gpsw = int.from_bytes(payld[ 8:10], 'big')
        self.gpst = int.from_bytes(payld[10:14], 'big')
        self.snr  = int.from_bytes(payld[14:15], 'big')
        flag      = int.from_bytes(payld[15:16], 'big')
        self.data = payld[16:268]
        if self.last_gpst == 0:
            self.last_gpst = self.gpst
        self.err = ""
        csum1, csum2 = checksum(payld)
        if csum[0] != csum1 or csum[1] != csum2: self.err += "CS "
        if len_payld != 264                    : self.err += "Payload "
        if len_data  !=  63                    : self.err += "Data "
        if flag & 0x01                         : self.err += "RS "
        if flag & 0x02                         : self.err += "Week "
        if flag & 0x04                         : self.err += "TOW "
        return True

    def select_sat(self, s_prn):
        ''' returns display message '''
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
        disp_msg += self.msg_color.fg('green') + f'{self.prn} ' + \
            self.msg_color.fg('yellow') + \
            gps2utc.gps2utc(self.gpsw, self.gpst // 1000) + \
            self.msg_color.fg('default') + f' {self.snr}'
        if self.err:
            disp_msg += self.msg_color.fg('red') + ' ' + self.err + \
                self.msg_color.fg()
        return disp_msg

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Allystar HD9310 to Quasi-zenith satellite (QZS) L6 message converter')
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
        help='satellite PRN to be specified.')
    args    = parser.parse_args()
    fp_disp = sys.stdout
    fp_l6   = None
    if args.l6:  # QZS L6 raw message output to stdout
        fp_disp = None
        fp_l6   = sys.stdout
    if args.message:  # Allystar message to stderr
        fp_disp = sys.stderr
    if args.prn not in {0, 193, 194, 195, 196, 199}:
        print(libcolor.Color().fg('yellow') + "PRN to be specified is either 193-196, or 199, all PRNs are selected." + libcolor.Color().fg(), file=sys.stderr)
        args.prn = 0
    if 'alst2qzsl6.py' in sys.argv[0]:
        print(libcolor.Color().fg('yellow') + 'Notice: please use "alstdump.py", instead of "alst2qzsl6.py" that will be removed.' + libcolor.Color().fg(), file=sys.stderr)
    rcv = AllystarReceiver(fp_disp, args.color)
    try:
        while rcv.read():
            disp_msg = rcv.select_sat(args.prn)
            if fp_disp:
                print(disp_msg, file=fp_disp)
                fp_disp.flush()
            if rcv.l6 and fp_l6:
                fp_l6.buffer.write(rcv.l6)
                fp_l6.flush()
    except (BrokenPipeError, IOError):
        sys.exit()
    except KeyboardInterrupt:
        print(libcolor.Color().fg('yellow') + "User break - terminated" + libcolor.Color().fg(), file=sys.stderr)
        sys.exit()

# EOF
