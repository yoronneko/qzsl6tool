#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# make_synthetic_sbas_auth.py: generate SYNTHETIC SBAS authentication messages (MT20, MT21)
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2026 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.
#
# The generated data is NOT a real satellite broadcast. It is a hand-made
# bit pattern that follows the draft SBAS authentication message formats
# (ref.[8] in qzsl1sread.py) so that the MT20/MT21 decoders can be tested
# until real broadcast data becomes available.
#
# Usage: ./make_synthetic_sbas_auth.py > ../sample/synthetic-sbas-auth.sbas

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'python'))
import libqzsl6tool

from bitstring import BitStream

PRN: int = 128  # arbitrary SBAS PRN for the synthetic stream

def u(value: int, length: int) -> BitStream:
    return BitStream(uint=value, length=length)

def frame(mt: int, df: BitStream) -> bytes:
    ''' builds one stdin record: [PRN(8)][L1S RAW(250)][padding(6)] '''
    assert len(df) == 212, f'data field must be 212 bits, got {len(df)}'
    body = u(0x53, 8) + u(mt, 6) + df  # preamble, message type, data field
    padded = (u(0, 6) + body).tobytes()
    crc = libqzsl6tool.rtk_crc24q(padded, len(padded))
    return (u(PRN, 8) + body + BitStream(bytes=crc) + u(0, 6)).tobytes()

def main() -> None:
    out = b''
    # MT20: beMAC1, beMAC2, aMAC (28 bits each) and TESLA hash point (128 bits)
    out += frame(20, u(0x1111111, 28) + u(0x2222222, 28) + u(0x3333333, 28) + u(0xdeadbeef, 128))
    # MT21 key material, payload 1 (page 0)
    payload1 = u(5, 3)       + \
               u(2, 3)       + \
               u(2400, 13)   + \
               u(1000, 17)   + \
               u(2, 3)       + \
               u(50000, 17)  + \
               u(2, 2)       + \
               u(1, 4)       + \
               u(0, 2)       + \
               u(0xcafe, 128) + \
               BitStream('bin=10100000') + \
               u(0, 5)
    out += frame(21, u(0, 1) + u(3, 3) + u(0, 3) + payload1)
    # MT21 key material, payload 2 (page 1): salt
    out += frame(21, u(0, 1) + u(3, 3) + u(1, 3) + u(0xabcd, 128) + u(0, 77))
    # MT21 level 2 signature, page 2
    out += frame(21, u(1, 1) + u(3, 3) + u(2, 3) + u(0x77, 205))
    # MT21 key material, undefined payload (page 5)
    out += frame(21, u(0, 1) + u(3, 3) + u(5, 3) + u(0x77, 205))
    sys.stdout.buffer.write(out)

if __name__ == '__main__':
    main()

# EOF
