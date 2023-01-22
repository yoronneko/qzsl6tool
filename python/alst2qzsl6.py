#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# alst2qzsl6.py: Allystar HD9310C raw to quasi-zenith satellite (QZS)
#                L6 message converter
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.
#
# References:
# [1] Justin Yang, QZSS L6 Enabled Multi-band Multi-GNSS Receiver
#     https://docs.datagnss.com/rtk-board/firmware/L6/L6DE_tech_intro.pdf
# [2] u-blox, F9 high precision GNSS receiver interface description,
#     F9 HPG 1.30, UBX-21046737, Dec. 2021.

import argparse
import sys
import gps2utc
import libcolor

class AllystarReceiver:
    dict_snr  = {}  # SNR dictionary
    dict_data = {}  # payload data dictionary
    last_gpst = 0   # last received GPS time

    def __init__(self, fp_disp, ansi_color, fp_l6, fp_ubx):
        self.fp_disp   = fp_disp
        self.fp_l6     = fp_l6
        self.fp_ubx    = fp_ubx
        self.msg_color = libcolor.Color(fp_disp, ansi_color)

    def read_alst_msg(self):  # ref. [1]
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
            if not payld or not csum:
                return False
        except KeyboardInterrupt:
            color = libcolor.Color(sys.stderr)
            print(color.fg('yellow') + \
                  "User break - terminated" + \
                  color.fg('default'), file=sys.stderr)
            return False
        len_payld = int.from_bytes(payld[2: 4], 'little')
        self.prn  = int.from_bytes(payld[4: 6], 'little') - 700
        freqid    = int.from_bytes(payld[6: 7], 'little')
        len_data  = int.from_bytes(payld[7: 8], 'little') - 2
        self.gpsw = int.from_bytes(payld[8: 10], 'big')
        self.gpst = int.from_bytes(payld[10: 14], 'big') // 1000
        self.snr  = int.from_bytes(payld[14: 15], 'big')
        flag      = int.from_bytes(payld[15: 16], 'big')
        self.data = payld[16:268]
        self.err = ""
        csum1, csum2 = rtk_checksum(payld)
        if csum[0] != csum1 or csum[1] != csum2:
            self.err += "CS "
        if len_payld != 264:
            self.err += "Payload "
        if len_data != 63:
            self.err += "Data "
        if flag & 0x01:
            self.err += "RS "
        if flag & 0x02:
            self.err += "Week "
        if flag & 0x04:
            self.err += "TOW "
        if self.last_gpst == 0:
            self.last_gpst = self.gpst
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
            if fp_disp:
                print(f"---> prn {p_prn} (C/No {p_snr} dB)", file=self.fp_disp)
            self.dict_snr.clear()
            self.dict_data.clear()
        elif not self.err:
            self.dict_snr[self.prn] = self.snr
            self.dict_data[self.prn] = self.data
        self.p_prn  = p_prn   # picked up PRN
        self.p_snr  = p_snr   # picked up SNR
        self.p_data = p_data  # picked up data

    def show_alst_msg(self):
        if self.prn == 0 or not self.fp_disp:
            return
        msg = self.msg_color.fg('green') + f'{self.prn} ' + \
              self.msg_color.fg('yellow') + \
              gps2utc.gps2utc(self.gpsw, self.gpst) + \
              self.msg_color.fg('default') + f' {self.snr}'
        if self.err:
            msg += self.msg_color.fg('red') + \
            ' ' + self.err + \
            self.msg_color.fg('default')
        print(msg, file=self.fp_disp)

    def send_l6_msg(self):
        if self.p_prn == 0 or not self.fp_l6:
            return
        self.fp_l6.buffer.write(self.p_data)
        self.fp_l6.flush()

    def send_ubxl6_msg(self):  # ref. [2]
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

def rtk_checksum(payload):  # ref. [1]
    checksum1 = 0
    checksum2 = 0
    for b in payload:
        checksum1 += b
        checksum2 += checksum1
        checksum1 &= 0xff
        checksum2 &= 0xff
    return checksum1, checksum2

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
    parser_group.add_argument(
        '-u', '--ubx', action='store_true',
        help='send u-blox L6 message to stdout (experimental, it also turns off QZS L6 and Allystar messages).')
    args = parser.parse_args()
    fp_disp = sys.stdout
    fp_l6   = None
    fp_ubx  = None
    force_ansi_color = False
    if args.l6:  # QZS L6 raw message output to stdout
        fp_disp = None
        fp_l6   = sys.stdout
        fp_ubx  = None
    if args.ubx:  # u-blox L6 raw message output to stdout
        fp_disp = None
        fp_l6   = None
        fp_ubx  = sys.stdout
    if args.message:  # Allystar message to stderr
        fp_disp = sys.stderr
    if args.color:  # force ANSI color escape sequences
        force_ansi_color = True
    alst = AllystarReceiver(fp_disp, force_ansi_color, fp_l6, fp_ubx)
    while alst.read_alst_msg():
        alst.pick_up()
        try:
            alst.send_l6_msg()
            alst.send_ubxl6_msg()
            alst.show_alst_msg()
        except (BrokenPipeError, IOError):
            sys.exit()

# EOF
