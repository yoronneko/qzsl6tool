#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# make_synthetic_dcx.py: generate SYNTHETIC QZSS DCX messages (L1S MT44)
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2026 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.
#
# The generated data is NOT a real satellite broadcast. It is a hand-made
# bit pattern that follows IS-QZSS-DCX-004 (ref.[5] in qzsl1sread.py) so that
# the MT44 decoder can be tested. Field values are taken from the calculation
# examples in the specification where available.
#
# Usage: ./make_synthetic_dcx.py > ../sample/synthetic-dcx.l1s

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'python'))
import libqzsl6tool

from bitstring import BitStream

PRN: int = 186  # QZS1R L1S

def u(value: int, length: int) -> BitStream:
    return BitStream(uint=value, length=length)

def frame(mt: int, df: BitStream) -> bytes:
    ''' builds one stdin record: [PRN(8)][L1S RAW(250)][padding(6)] '''
    assert len(df) == 212, f'data field must be 212 bits, got {len(df)}'
    body = u(0x53, 8) + u(mt, 6) + df  # preamble, message type, data field
    padded = (u(0, 6) + body).tobytes()
    crc = libqzsl6tool.rtk_crc24q(padded, len(padded))
    return (u(PRN, 8) + body + BitStream(bytes=crc) + u(0, 6)).tobytes()

def camf(a1: int, a2: int, a3: int, a4: int, a5: int, a6: int, a7: int, a8: int,
         a9: int, a10: int, a11: int, a12: int, a13: int, a14: int, a15: int,
         a16: int, a17: int, a18: int) -> BitStream:
    ''' common alert message format, 122 bits '''
    return u(a1, 2) + u(a2, 9) + u(a3, 5) + u(a4, 7) + u(a5, 2) + u(a6, 1) + \
           u(a7, 14) + u(a8, 2) + u(a9, 1) + u(a10, 3) + u(a11, 10) + u(a12, 16) + \
           u(a13, 17) + u(a14, 5) + u(a15, 5) + u(a16, 6) + u(a17, 2) + u(a18, 15)

def mt44(sdmt: int, sdm: int, camf_bits: BitStream, ext: BitStream) -> bytes:
    assert len(ext) == 74, f'extended message must be 74 bits, got {len(ext)}'
    return frame(44, u(sdmt, 1) + u(sdm, 9) + camf_bits + ext + u(0, 6))

JAPAN: int = 0b001101111
NO_EXT: BitStream = u(0, 74)

def main() -> None:
    out = b''
    # 1. NULL message with SD (service type): PRN183-186 for Japan, PRN189 abroad
    out += mt44(0, 0b000000100, camf(0, JAPAN, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0), NO_EXT)
    # 2. NULL message with SD (transmission status): PRN183, 184, 186, 189 on
    out += mt44(1, 0b110100100, camf(0, JAPAN, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0), NO_EXT)
    # 3. L-Alert: tsunami alert, ellipse from the spec calculation examples
    #    A12=45761 (35.688 deg), A13=116395 (139.691 deg), A16=48 (45.00 deg)
    #    onset: Tuesday 09:30 UTC this week = 1 + 1*1440 + 9*60 + 30
    ext = u(1100, 16) + u(0, 1) + u(0, 17) + u(0, 17) + u(0, 5) + u(0, 5) + u(0, 7) + u(1, 6)
    out += mt44(0, 0b000000100,
                camf(1, JAPAN, 1, 44, 3, 0, 1 + 1440 + 570, 1, 1, 0, 0b10_00000010,
                     45761, 116395, 13, 10, 48, 0, 0), ext)
    # 4. Local government: evacuation, additional ellipse from the spec examples
    #    EX3=91522 (35.687 deg), EX4=68950 (139.689 deg), EX7=96 (45.00 deg)
    ext = u(1100, 16) + u(1, 1) + u(91522, 17) + u(68950, 17) + u(8, 5) + u(6, 5) + u(96, 7) + u(1, 6)
    out += mt44(0, 0b000000100,
                camf(2, JAPAN, 4, 27, 2, 0, 1 + 1440 + 600, 2, 1, 0, 0b00_00000000,
                     0, 0, 0, 0, 0, 0, 0), ext)
    # 5. J-Alert (prefecture): missile launched, Hokkaido, Aomori, Iwate
    ext = u(0, 1) + u(0b111, 47) + u(0, 17) + u(0, 3) + u(1, 6)
    out += mt44(0, 0b000000100,
                camf(1, JAPAN, 2, 1, 3, 0, 1 + 1440 + 400, 1, 1, 0, 0b00_10000000,
                     0, 0, 0, 0, 0, 0, 0), ext)
    # 6. J-Alert (cities): test message, Sapporo (01100) and Hakodate (01202)
    ext = u(1, 1) + u(1100, 16) + u(1202, 16) + u(0, 16) + u(0, 16) + u(0, 3) + u(1, 6)
    out += mt44(0, 0b000000100,
                camf(0, JAPAN, 3, 113, 0, 0, 0, 0, 1, 0, 0b00_10001000,
                     0, 0, 0, 0, 0, 0, 0), ext)
    # 7. Outside Japan (Zambia = 248): storm, international library IC-A-04 / IC-B-02,
    #    B2 hazard centre offset C5=64 (+0.15625 deg), C6=0 (-10 deg)
    ext = u(0x5A5A5, 68) + u(1, 6)
    out += mt44(0, 0b000000100,
                camf(1, 248, 1, 77, 2, 1, 1, 3, 0, 0, (3 << 5) | 1,
                     32768, 65536, 20, 18, 32, 1, (64 << 8) | (0 << 1)), ext)
    # 8. Outside Japan (Italy = 108): earthquake, B4 detailed information
    #    D1=5 (M6.0-6.9), D2=4 (5 strong), D3=4 (90 deg), D4=6 (x5)
    ext = u(0, 68) + u(1, 6)
    out += mt44(0, 0b000000100,
                camf(1, 108, 2, 36, 3, 0, 1 + 3 * 1440 + 8 * 60, 1, 0, 0, (21 << 5) | 22,
                     50000, 70000, 15, 12, 40, 3, (5 << 11) | (4 << 8) | (4 << 4) | 6), ext)
    # 9. Outside Japan (Australia = 10): forest fire, B3 secondary ellipse
    #    C7=2 (shift 2 x L_M), C8=7 (x2), C9=16 (180 deg), C10=7 (IC-C-08)
    ext = u(0, 68) + u(1, 6)
    out += mt44(0, 0b000000100,
                camf(2, 10, 3, 27, 2, 0, 1 + 5 * 1440, 2, 0, 1, (26 << 5) | 17,
                     20000, 110000, 18, 16, 8, 2, (2 << 13) | (7 << 10) | (16 << 5) | 7), ext)
    # 10. L-Alert with B1 refined resolution: C1=4, C2=2, C3=1, C4=0
    ext = u(1100, 16) + u(0, 1) + u(0, 17) + u(0, 17) + u(0, 5) + u(0, 5) + u(0, 7) + u(1, 6)
    out += mt44(0, 0b000000100,
                camf(1, JAPAN, 1, 68, 2, 0, 1 + 1440 + 570, 1, 1, 0, 0b01_00000010,
                     45761, 116395, 13, 10, 48, 0, (4 << 12) | (2 << 9) | (1 << 6) | (0 << 3)), ext)
    sys.stdout.buffer.write(out)

if __name__ == '__main__':
    main()

# EOF
