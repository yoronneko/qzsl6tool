#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# novread.py: NovAtel receiver raw message reader
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022-2023 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.
#
# References:
# [1] NovAtel, OEM7 Commands and Logs Reference Manual, v24, July 2023.

import argparse
import os
import sys

sys.path.append(os.path.dirname(__file__))
import gps2utc
import libcolor

LEN_CNAV_PAGE = 62  # C/NAV page size is 492 bit (61.5 byte)

def crc32(data):
    polynomial = 0xedb88320
    crc = 0
    for byte in data:
        tmp2 = (crc ^ byte) & 0xff
        for _ in range(8):
            if tmp2 & 1:
                tmp2 = (tmp2 >> 1) ^ polynomial
            else:
                tmp2 = tmp2 >> 1
        tmp1 = (crc >> 8) & 0x00ffffff
        crc = tmp1 ^ tmp2
    return crc.to_bytes(4,'little')

class NovReceiver:
    def __init__(self, fp_disp, ansi_color):
        self.fp_disp   = fp_disp
        self.msg_color = libcolor.Color(fp_disp, ansi_color)

    def read(self):
        ''' reads standard input as NovAtel raw, [1]
            and returns true if successful '''
        sync = bytes(3)
        try:
            while True:
                while sync != b'\xaa\x44\x12':
                    b = sys.stdin.buffer.read(1)
                    if not b:
                        return False
                    sync = sync[1:3] + b
                head_len = sys.stdin.buffer.read(1)
                if not head_len:
                    return False
                u_head_len = int.from_bytes(head_len, 'little')
                head = sys.stdin.buffer.read(u_head_len-4)
                if not head:
                    return False
                self.parse_head(head)
                payload = sys.stdin.buffer.read(self.msg_len)
                if not payload:
                    return False
                crc = sys.stdin.buffer.read(4)
                if not crc:
                    return False
                crc_cal = crc32(sync + head_len + head + payload)
                if crc == crc_cal:
                    break
                else:
                    print(libcolor.Color().fg('red') + \
                        f'CRC error: {crc.hex()} != {crc_cal.hex()}' + \
                        libcolor.Color().fg(), file=sys.stderr)
                    continue
            self.payload = payload
        except KeyboardInterrupt:
            print(libcolor.Color().fg('yellow') + "User break - terminated" + \
                  libcolor.Color().fg(), file=sys.stderr)
            sys.exit()
        return True

    def parse_head(self, head):
        ''' stores header info '''
        pos = 0
        if len(head) != 24:
            print(libcolor.Color().fg('yellow') + \
                f'warning: header length mismatch: {len(head)} != 24' + \
                libcolor.Color().fg(), file=sys.stderr)
        self.msg_id   = int.from_bytes(head[pos:pos+2], 'little'); pos += 2
        self.msg_type = int.from_bytes(head[pos:pos+1], 'little'); pos += 1
        self.port     = int.from_bytes(head[pos:pos+1], 'little'); pos += 1
        self.msg_len  = int.from_bytes(head[pos:pos+2], 'little'); pos += 2
        self.seq      = int.from_bytes(head[pos:pos+2], 'little'); pos += 2
        self.t_idle   = int.from_bytes(head[pos:pos+1], 'little'); pos += 1
        self.t_stat   = int.from_bytes(head[pos:pos+1], 'little'); pos += 1
        self.gpsw     = int.from_bytes(head[pos:pos+2], 'little'); pos += 2
        self.gpst     = int.from_bytes(head[pos:pos+4], 'little'); pos += 4
        self.stat     = int.from_bytes(head[pos:pos+4], 'little'); pos += 4
        self.reserved = int.from_bytes(head[pos:pos+2], 'little'); pos += 2
        self.ver      = int.from_bytes(head[pos:pos+2], 'little'); pos += 2
        self.msg_name = self.NOV_MSG_NAME.get(self.msg_id, f"MT{self.msg_id}")

    def qzssrawsubframe(self):
        ''' returns hex-decoded message
            ref.[1], p.822 3.148 QZSSRAWSUBFRAME (1330)
        '''
        QZSS_ID = {  # dictionary of sat id from prn
            193: 'J01', 194: 'J02', 199: 'J03', 195: 'J04', 196: 'J05', }
        payload = self.payload
        if len(payload) != 4+4+32+4:
            print(libcolor.Color().fg('red') + \
                f"messge length mismatch: {len(payload)} != {4+4+32+4}" + \
                libcolor.Color().fg(), file=sys.stderr)
            return False
        pos = 0
        prn   = int.from_bytes(payload[pos:pos+4], 'little'); pos +=  4
        sfid  = int.from_bytes(payload[pos:pos+4], 'little'); pos +=  4
        sfraw = payload[pos:pos+32]                         ; pos += 32
        chno  = int.from_bytes(payload[pos:pos+4], 'little'); pos +=  4
        msg = self.msg_color.fg('green') + \
            gps2utc.gps2utc(self.gpsw, self.gpst // 1000) + ' ' + \
            self.msg_color.fg('cyan') + self.msg_name + ' ' + \
            self.msg_color.fg('yellow') + \
            f'{QZSS_ID.get(prn, "J??")}:{sfid} ' + \
            self.msg_color.fg() + sfraw.hex()
        return msg

    def galcnavrawpage(self):
        ''' returns hex-decoded messages and stores CNAV messages
            ref.[1], p.591 3.40 GALCNAVRAWPAGE (2239)
        '''
        payload = self.payload
        if len(payload) != 4+4+2+2+58:
            print(libcolor.Color().fg('red') + \
                f"messge length mismatch: {len(payload)} != {4+4+2+2+58}" + \
                libcolor.Color().fg(), file=sys.stderr)
            return False
        pos = 0
        sig_ch  = int.from_bytes(payload[pos:pos+4], 'little'); pos +=  4
        prn     = int.from_bytes(payload[pos:pos+4], 'little'); pos +=  4
        msg_id  = int.from_bytes(payload[pos:pos+2], 'little'); pos +=  2
        page_id = int.from_bytes(payload[pos:pos+2], 'little'); pos +=  2
        e6b     = payload[pos:pos+58]                         ; pos += 58
        self.satid = prn
        # NovAtel C/NAV data excludes 24-bit CRC and 6-bit tail bits.
        # Threrfore, 3 bytes (24 bit) are padded for CRC, tail, and padding
        # self.e6b = e6b + b'\x00\x00\x00'
        self.e6b = e6b + bytes(LEN_CNAV_PAGE - 58)
        msg = self.msg_color.fg('green') + \
            gps2utc.gps2utc(self.gpsw, self.gpst // 1000) + ' ' + \
            self.msg_color.fg('cyan') + self.msg_name + ' ' + \
            self.msg_color.fg('yellow') + \
            f'E{prn:02d}:{msg_id}:{page_id} ' + \
            self.msg_color.fg() + e6b.hex()
        return msg

    NOV_MSG_NAME = {  # dictionary for obtaining message name from ID
           8: 'IONUTC'         ,
          41: 'RAWEPHEM'       ,
          43: 'RANGE'          ,
         140: 'RANGECMP'       ,
         287: 'RAWWAASFRAME'   ,
         723: 'GLOEPHEMERIS'   ,
         973: 'RAWSBASFRAME'   ,
        1121: 'GALCLOCK'       ,
        1122: 'GALEPHEMERIS'   ,
        1127: 'GALIONO'        ,
        1330: 'QZSSRAWSUBFRAME',
        1331: 'QZSSRAWEPHEM'   ,
        1347: 'QZSSIONUTC'     ,
        1696: 'BDSEPHEMERIS'   ,
        2123: 'NAVICEPHEMERIS' ,
        2239: 'GALCNAVRAWPAGE' ,
    }

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='NovAtel message reader')
    parser.add_argument(
        '-c', '--color', action='store_true',
        help='apply ANSI color escape sequences even for non-terminal.')
    parser.add_argument(
        '-e', '--e6b', action='store_true',
        help='send E6B C/NAV messages to stdout, and also turns off display message.')
    parser.add_argument(
        '-l', '--l6', action='store_true',
        help='send L6 messages to stdout, and also turns off display message.')
    parser.add_argument(
        '-m', '--message', action='store_true',
        help='show display messages to stderr')
    parser.add_argument(
        '-s', '--statistics', action='store_true',
        help='show HAS statistics in display messages.')
    parser.add_argument(
        '-t', '--trace', type=int, default=0,
        help='show display verbosely: 1=detail, 2=bit image.')
    args = parser.parse_args()
    fp_e6b  = None
    fp_l6   = None
    fp_disp = sys.stdout
    fp_rtcm = None
    has_decode = False
    if args.trace < 0:
        print(libcolor.Color().fg('red') + 'trace level should be positive ({args.trace}).' + libcolor.Color().fg(), file=sys.stderr)
        sys.exit(1)
    if args.e6b:
        fp_disp = None
        fp_e6b  = sys.stdout
        fp_l6   = None
    if args.l6:
        fp_disp = None
        fp_e6b  = None
        fp_l6   = sys.stdout
    if args.message:  # show HAS message to stderr
        fp_disp = sys.stderr
    if 'nov2has.py' in sys.argv[0]:  # for compatibility of nov2has.py
        print(libcolor.Color().fg('yellow') + 'Notice: please use "novread.py -e | gale6read", instead of "nov2has.py" that will be removed.' + libcolor.Color().fg(), file=sys.stderr)
        has_decode = True
        import libgale6
        gale6 = libgale6.GalE6(fp_rtcm, fp_disp, args.trace, args.color, args.statistics)
    rcv = NovReceiver(fp_disp, args.color)
    while rcv.read():
        #print(rcv.msg_name, file=fp_disp)
        if   rcv.msg_name == 'QZSSRAWSUBFRAME':
            msg = rcv.qzssrawsubframe()
            if fp_l6:
                fp_l6.buffer.write(rcv.l6)
                fp_l6.flush()
        elif rcv.msg_name == 'GALCNAVRAWPAGE':
            msg = rcv.galcnavrawpage()
            if fp_e6b:
                fp_e6b.buffer.write(rcv.satid.to_bytes(1, byteorder='little'))
                fp_e6b.buffer.write(rcv.e6b)
                fp_e6b.flush()
            if has_decode:  # for compatibility of nov2has.py
                if gale6.ready_decoding_has(rcv.satid, rcv.e6b):
                    gale6.decode_has_message()
        else:
            msg = rcv.msg_color.fg('green') + \
                gps2utc.gps2utc(rcv.gpsw, rcv.gpst // 1000) + \
                rcv.msg_color.fg() + ' ' + \
                rcv.msg_color.dec('dark') + rcv.msg_name + \
                rcv.msg_color.dec()
        if fp_disp and not has_decode:
            try:
                print(msg, file=fp_disp)
            except (BrokenPipeError, IOError):
                sys.exit()

# EOF
