#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# novread.py: NovAtel receiver raw message read
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022-2026 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.
#
# References:
# [1] NovAtel, OEM7 Commands and Logs Reference Manual, v24, July 2023.

import argparse
import os
import sys
from typing import TextIO

sys.path.append(os.path.dirname(__file__))
import libgnsstime
import libqzsl6tool
import libtrace

LEN_CNAV_PAGE: int = 62  # C/NAV page size is 492 bit (61.5 byte)
NOV_MSG_NAME : dict[int, str] = {    # dictionary for obtaining message name from ID
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

def crc32(data: bytes) -> bytes:
    polynomial: int = 0xedb88320
    crc: int = 0
    for byte in data:
        tmp2: int = (crc ^ byte) & 0xff
        for _ in range(8):
            if tmp2 & 1:
                tmp2 = (tmp2 >> 1) ^ polynomial
            else:
                tmp2 = tmp2 >> 1
        tmp1: int = (crc >> 8) & 0x00ffffff
        crc = tmp1 ^ tmp2
    return crc.to_bytes(4,'little')

class NovReceiver:
    def __init__(self, trace: libtrace.Trace) -> None:
        self.trace: libtrace.Trace = trace
        self.payload : bytes = bytes()
        self.msg_id  : int = 0
        self.msg_type: int = 0
        self.port    : int = 0
        self.msg_len : int = 0
        self.seq     : int = 0
        self.t_idle  : int = 0
        self.t_stat  : int = 0
        self.gpsw    : int = 0
        self.gpst    : int = 0
        self.stat    : int = 0
        self.reserved: int = 0
        self.ver     : int = 0
        self.msg_name: str = ''
        self.satid   : int = 0
        self.raw     : bytes = bytes()


    def read(self) -> bool:
        ''' reads standard input as NovAtel raw, [1]
            and returns true if successful '''
        while True:
            sync: bytes = bytes(3)
            while sync != b'\xaa\x44\x12':
                b: bytes = sys.stdin.buffer.read(1)
                if not b:
                    return False
                sync = sync[1:3] + b
            head_len: bytes = sys.stdin.buffer.read(1)
            if not head_len:
                return False
            u_head_len: int = int.from_bytes(head_len, 'little')
            head: bytes = sys.stdin.buffer.read(u_head_len - 4)
            if not head:
                return False
            self.parse_head(head)
            payload: bytes = sys.stdin.buffer.read(self.msg_len)
            if not payload:
                return False
            crc: bytes = sys.stdin.buffer.read(4)
            if not crc:
                return False
            crc_cal: bytes = crc32(sync + head_len + head + payload)
            if crc == crc_cal:
                break
            else:
                libtrace.err(f'CRC error: {crc.hex()} != {crc_cal.hex()}')
                continue
        self.payload = payload
        return True

    def parse_head(self, head: bytes) -> None:
        ''' stores header info '''
        pos: int = 0
        if len(head) != 24:
            self.trace.show(0, f'warning: header length mismatch: {len(head)} != 24', fg='yellow')
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
        self.msg_name = NOV_MSG_NAME.get(self.msg_id, f"MT{self.msg_id}")

    def qzssrawsubframe(self) -> str:
        ''' returns hex-decoded message
            ref.[1], p.822 3.148 QZSSRAWSUBFRAME (1330)
        '''
        payload = self.payload
        if len(payload) != 4+4+32+4:
            return self.trace.msg(0, f"message length mismatch: {len(payload)} != {4+4+32+4}", fg='red')

        pos = 0
        prn   = int.from_bytes(payload[pos:pos+ 4], 'little'); pos +=  4
        sfid  = int.from_bytes(payload[pos:pos+ 4], 'little'); pos +=  4
        raw   =                payload[pos:pos+32]           ; pos += 32
        chno  = int.from_bytes(payload[pos:pos+ 4], 'little'); pos +=  4
        self.satid = prn
        self.raw   = prn.to_bytes(1, 'little') + raw
        msg = self.trace.msg(0, libgnsstime.gps2utc(self.gpsw, self.gpst // 1000), fg='green') + ' ' + \
              self.trace.msg(0, self.msg_name + ' ', fg='cyan') + \
              self.trace.msg(0, f'J{prn-192:02d}:{sfid} ', fg='yellow') + \
            raw.hex()
        return msg

    def galcnavrawpage(self) -> str:
        ''' returns hex-decoded messages and stores CNAV messages
            ref.[1], p.591 3.40 GALCNAVRAWPAGE (2239)
        '''
        payload = self.payload
        if len(payload) != 4+4+2+2+58:
            return self.trace.msg(0, f"message length mismatch: {len(payload)} != {4+4+2+2+58}", fg='red')
        pos = 0
        sig_ch  = int.from_bytes(payload[pos:pos+4], 'little'); pos +=  4  # signal channel, not used
        prn     = int.from_bytes(payload[pos:pos+4], 'little'); pos +=  4
        msg_id  = int.from_bytes(payload[pos:pos+2], 'little'); pos +=  2
        page_id = int.from_bytes(payload[pos:pos+2], 'little'); pos +=  2
        e6b     = payload[pos:pos+58]                         ; pos += 58
        self.satid = prn
        # NovAtel C/NAV data excludes 24-bit CRC and 6-bit tail bits.
        # Threrfore, 3 bytes (24 bit) are padded for CRC, tail, and padding
        self.raw = self.satid.to_bytes(1, byteorder='little') + \
            e6b + bytes(LEN_CNAV_PAGE - 58)
        msg = self.trace.msg(0, libgnsstime.gps2utc(self.gpsw, self.gpst // 1000), fg='green') + ' ' + \
            self.trace.msg(0, self.msg_name, fg='cyan') + ' ' + \
            self.trace.msg(0, f'E{prn:02d}:{msg_id}:{page_id} ', fg='yellow') + e6b.hex()
        return msg

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=f'NovAtel message read, QZS L6 Tool ver.{libqzsl6tool.VERSION}')
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '-e', '--e6b', action='store_true',
        help='send E6B C/NAV messages to stdout, and also turns off display message.')
    group.add_argument(
        '-q', '--qlnav', action='store_true',
        help='send QZSS LNAV messages to stdout, and also turns off display message.')
    parser.add_argument(
        '-c', '--color', action='store_true',
        help='apply ANSI color escape sequences even for non-terminal.')
    parser.add_argument(
        '-m', '--message', action='store_true',
        help='show display messages to stderr')
    args = parser.parse_args()
    fp_disp: TextIO | None = sys.stdout
    fp_raw : TextIO | None = None
    if args.e6b:
        fp_disp: TextIO | None = None
        fp_raw : TextIO | None = sys.stdout
    if args.qlnav:
        fp_disp: TextIO | None = None
        fp_raw : TextIO | None = sys.stdout
    if args.message:  # send display messages to stderr
        fp_disp = sys.stderr
    trace = libtrace.Trace(fp_disp, 0, args.color)
    rcv = NovReceiver(trace)
    try:
        while rcv.read():
            #print(rcv.msg_name, file=fp_disp)
            if rcv.msg_name == 'GALCNAVRAWPAGE':
                msg = rcv.galcnavrawpage()
            elif rcv.msg_name == 'QZSSRAWSUBFRAME':
                msg = rcv.qzssrawsubframe()
            else:
                msg = rcv.trace.msg(0, libgnsstime.gps2utc(rcv.gpsw, rcv.gpst // 1000), fg='green') + ' ' + rcv.trace.msg(0, rcv.msg_name, dec='dark')
                rcv.raw = bytearray()
            rcv.trace.show(0, msg)
            if (args.e6b   and rcv.msg_name == 'GALCNAVRAWPAGE' ) or \
               (args.qlnav and rcv.msg_name == 'QZSSRAWSUBFRAME'):
                if fp_raw:
                    fp_raw.buffer.write(rcv.raw)
                    fp_raw.flush()
    except (BrokenPipeError, IOError):
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(1)
    except KeyboardInterrupt:
        libtrace.warn("User break - terminated")
        sys.exit()

# EOF
