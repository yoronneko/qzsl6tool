#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# alst2qzsl6.py: Allystar HD9310C raw to quasi-zenith satellite (QZS) L6 raw converter
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.

import argparse
import sys
from libbit import *
from gps2utc import *


class alst_t:
    fp_trace = sys.stdout # file pointer for trace
    fp_l6 = None          # file pointer for QZS L6 output
    fp_ubx = None         # file pointer for u-blox L6 raw output
    fp_msg = sys.stdout   # message output file pointer
    t_level = 0           # trace level
    dict_snr = {}         # SNR dictionary
    dict_data = {}        # payload data dictionary
    last_gpst = 0         # last received GPS time

    def trace(self, level, *args):
        if level <= self.t_level and self.fp_trace:
            for arg in args:
                print(arg, file=self.fp_trace)

    def receive(self):
        sync = [b'0x00' for i in range(4)]
        ok = False
        try:
            while not ok:
                b = sys.stdin.buffer.read(1)
                if not b:
                    return False
                sync = sync[1:4] + [b]
                if sync == [b'\xf1', b'\xd9', b'\x02', b'\x10']:
                    ok = True
            payld = b'\x02\x10' + sys.stdin.buffer.read(266)
            csum = sys.stdin.buffer.read(2)
        except KeyboardInterrupt:
            print("User break - terminated", file=sys.stderr)
            return False
        len_payld = int.from_bytes(payld[2: 4], 'little')
        prn = int.from_bytes(payld[4: 6], 'little') - 700
        freqid = int.from_bytes(payld[6: 7], 'little')
        len_data = int.from_bytes(payld[7: 8], 'little') - 2
        gpsw = int.from_bytes(payld[8: 10], 'big')
        gpst = int.from_bytes(payld[10: 14], 'big') // 1000
        snr = int.from_bytes(payld[14: 15], 'big')
        flag = int.from_bytes(payld[15: 16], 'big')
        data = payld[16:268]
        err = ""
        csum1, csum2 = rtk_checksum(payld)
        if csum[0] != csum1 or csum[1] != csum2:
            err += "CS "
        if len_payld != 264:
            err += "Payload "
        if len_data != 63:
            err += "Data "
        if flag & 0x01:
            err += "RS "
        if flag & 0x02:
            err += "Week "
        if flag & 0x04:
            err += "TOW "
        self.data = data
        self.prn = prn
        self.gpsw = gpsw
        self.gpst = gpst
        self.snr = snr
        self.err = err
        if self.last_gpst == 0:
            self.last_gpst = gpst
        return True

    def pick_up(self):
        p_prn = 0
        p_snr = 0
        p_data = b''
        if self.last_gpst != self.gpst and len(self.dict_snr) != 0:
            self.last_gpst = self.gpst
            p_prn = sorted(self.dict_snr.items(),
                           key=lambda x: x[1], reverse=True)[0][0]
            p_snr = self.dict_snr[p_prn]
            p_data = self.dict_data[p_prn]
            print(f"---> prn {p_prn} (snr {p_snr})", file=self.fp_msg)
            self.dict_snr.clear()
            self.dict_data.clear()
        elif not self.err:
            self.dict_snr[self.prn] = self.snr
            self.dict_data[self.prn] = self.data
        self.p_prn = p_prn   # picked up PRN
        self.p_snr = p_snr   # picked up SNR
        self.p_data = p_data # picked up data

    def show(self):
        if self.prn == 0 or not self.fp_msg:
            return
        print(
            f"{self.prn} {gps2utc (self.gpsw, self.gpst)} {self.snr} {self.err}",
            file=self.fp_msg)

    def send_l6raw(self):
        if self.p_prn == 0 or not self.fp_l6:
            return
        self.fp_l6.buffer.write(self.p_data)
        self.fp_l6.flush()

    def send_ubxl6(self):
        if self.p_prn == 0 or not self.fp_ubx:
            return
        ubxpld = b'\x02\x72'                            # class ID
        ubxpld += (264).to_bytes(2, byteorder='little') # message length
        ubxpld += b'\x01'                               # message version
        ubxpld += (self.p_prn - 192).to_bytes(2, byteorder='little') # SVID
        ubxpld += self.p_snr.to_bytes(2, byteorder='little')         # C/No
        ubxpld += (0).to_bytes(4, byteorder='little')   # local time tag
        ubxpld += (0).to_bytes(1, byteorder='little')   # L6 group delay
        ubxpld += (0).to_bytes(1, byteorder='little')   # corrected bit num
        ubxpld += (0).to_bytes(1, byteorder='little')   # chanel info.
        ubxpld += (0).to_bytes(2, byteorder='little')   # reserved
        ubxpld += self.p_data                           # CLAS data
        csum1, csum2 = rtk_checksum(ubxpld)
        self.fp_ubx.buffer.write(
            b'\xb5\x62' +
            ubxpld +
            csum1.to_bytes(1, 'little') +
            csum2.to_bytes(1, 'little')
        )
        self.fp_ubx.flush()


if __name__ == '__main__':
    alst = alst_t()
    parser = argparse.ArgumentParser(
        description='Allystar HD9310 to Quasi-zenith satellite (QZS) L6 message converter')
    parser_group = parser.add_mutually_exclusive_group()
    parser.add_argument(
        '-t', '--trace', type=int, default=0,
        help='trace level (integer) for debug')
    parser_group.add_argument(
        '-l', '--l6', action='store_true',
        help='L6 message output')
    parser_group.add_argument(
        '-u', '--ubx', action='store_true',
        help='u-blox L6 raw  message output')
    parser.add_argument(
        '-m', '--message', action='store_true',
        help='show Allystar messages to stderr')
    args = parser.parse_args()
    if 0 < args.trace:
        alst.t_level = args.trace
    if args.l6:  # QZS L6 raw output to stdout
        alst.fp_l6 = sys.stdout
        alst.fp_trace = sys.stderr
        alst.fp_ubx = None
        alst.fp_msg = None
    if args.ubx:  # u-blox L6 raw output to stdout
        alst.fp_l6 = None
        alst.fp_trace = sys.stderr
        alst.fp_ubx = sys.stdout
        alst.fp_msg = None
    if args.message:  # show Allystar message to stderr
        fp_msg = sys.stderr
    while alst.receive():
        alst.pick_up()
        try:
            alst.send_l6raw()
            alst.send_ubxl6()
            alst.show()
        except BrokenPipeError:
            sys.exit()

# EOF
