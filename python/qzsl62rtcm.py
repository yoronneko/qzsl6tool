#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# qzsl62rtcm.py: quasi-zenith satellite (QZS) L6 message to RTCM message converter
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.

import sys
import bitstring
from gps2utc import *
from libbit import *

class qzsl6_t:
    dpn    = 0  # data part number
    sfn    = 0  # subframe number
    #msgnum = 0  # message number
    #numsat = 0  # number of satellites

    def receive (self):
        sync = [b'0x00' for i in range (4)]
        ok = False
        while not ok:
            b = sys.stdin.buffer.read(1)
            if not b: return False
            sync = sync[1:4] + [b]
            if sync == [b'\x1a', b'\xcf', b'\xfc', b'\x1d']: ok = True
        prn   = int.from_bytes     (sys.stdin.buffer.read (  1), 'big')
        mtid  = int.from_bytes     (sys.stdin.buffer.read (  1), 'big')
        dpart = bitstring.BitArray (sys.stdin.buffer.read (212))
        rs   =                      sys.stdin.buffer.read ( 32)
        vid = mtid >> 5
        vendor = ""
        if   vid == 0b001: vendor = "MADOCA"
        elif vid == 0b101: vendor = "CLAS"
        else: print ("Unknown vendor (code: {})".format (vid))
        facility = "Kobe" if (mtid >> 4) & 1 else "Hitachi-Ota"
        facility += ":" + str ((mtid >> 3) & 1)
        sf_ind   = mtid & 1 # subframe indicator
        pos = 0
        self.alert    = dpart[pos:pos+ 1].uint; pos +=  1
        self.tow      = dpart[pos:pos+20].uint; pos += 20
        self.wn       = dpart[pos:pos+13].uint; pos += 13
        self.dpart    = dpart[pos:]
        self.prn      = prn
        self.vid      = vid
        self.vendor   = vendor
        self.facility = facility
        self.sf_ind   = sf_ind
        return True

    def mdc2rtcm (self):
        dpart = self.dpart
        if len (dpart) < 12+20: return False
        msgnum = dpart[0:12].uint; pos = 12
        if msgnum == 0: return False
        elif msgnum in {1057, 1059, 1061, 1062}: # for GPS
            be = 20; bs = 6  # bit size of epoch and numsat
        elif msgnum in {1246, 1248, 1250, 1251}: # for QZSS
            be = 20; bs = 4
        elif msgnum in {1063, 1065, 1067, 1068}: # for GLONASS
            be = 17; bs = 6
        else:
            print ("Unknown message number {}".format (msgnum), file=sys.stderr)
            return False
        epoch     = dpart[pos:pos+be].uint; pos += be
        interval  = dpart[pos:pos+ 4].uint; pos +=  4
        multind   = dpart[pos:pos+ 1].uint; pos +=  1
        if msgnum in {1057, 1246, 1063}:
            satref= dpart[pos:pos+ 1].uint; pos +=  1
        iod       = dpart[pos:pos+ 4].uint; pos +=  4
        provider  = dpart[pos:pos+16].uint; pos += 16
        solution  = dpart[pos:pos+ 4].uint; pos +=  4
        numsat    = dpart[pos:pos+bs].uint; pos += bs
        if   msgnum == 1057: pos += 135 * numsat # GPS orbit correction
        elif msgnum == 1059:                     # GPS code bias
            for i in range(numsat):
                satid = dpart[pos:pos+ 6].uint; pos += 6
                numcb = dpart[pos:pos+ 5].uint; pos += 5
                pos += numcb * 19
        elif msgnum == 1061: pos +=  12 * numsat # GPS URA
        elif msgnum == 1062: pos +=  28 * numsat # GPS hr clock correction
        elif msgnum == 1246: pos += 133 * numsat # QZSS orbit correction
        elif msgnum == 1248:                     # QZSS code bias
            for i in range(numsat):
                satid = dpart[pos:pos+ 4].uint; pos += 4
                numcb = dpart[pos:pos+ 5].uint; pos += 5
                pos += numcb * 19
        elif msgnum == 1250: pos += 10 * numsat  # QZSS URA
        elif msgnum == 1251: pos += 26 * numsat  # QZSS hr clock correction
        elif msgnum == 1063: pos += 134 * numsat # GLONASS orbit correction
        elif msgnum == 1065:                     # GLONASS code bias
            for i in range(numsat):
                satid = dpart[pos:pos+ 5].uint; pos += 5
                numcb = dpart[pos:pos+ 5].uint; pos += 5
                pos += numcb * 19
        elif msgnum == 1067: pos += 11 * numsat # GLONASS URA
        elif msgnum == 1068: pos += 27 * numsat # GLONASS hr clock correction
        else:
            print ("msgnum {} drop {} bit: {}".format (
                msgnum, len (dpart), dpart.bin), file=sys.stderr)
            return False
        if pos % 8 != 0: pos += 8 - (pos % 8) # byte align
        self.rtcm   = dpart[0:pos].tobytes (); del dpart[0:pos]
        self.dpart  = dpart
        self.msgnum = msgnum
        self.numsat = numsat
        self.pos    = pos
        return True

    def clas2rtcm (self):
        print ("Sorry, the CLAS decode function is not implemented yet.",
            file = sys.stderr)
        sys.exit (1)

def send_rtcm (rtcm_data):
    rtcm = b'\xd3' + len (rtcm_data).to_bytes(2, 'big') + rtcm_data;
    rtcm_crc = rtk_crc24q (rtcm, len (rtcm))
    sys.stdout.buffer.write (rtcm)
    sys.stdout.buffer.write (rtcm_crc)
    sys.stdout.flush ()

if __name__ == '__main__':
    qzsl6 = qzsl6_t ()
    while qzsl6.receive ():
        if qzsl6.vendor == "CLAS":
            message = ''
            while qzsl6.clas2rtcm ():
                message += 'DPN' + str (qzsl6.dpn) + 'SFN' + str (qzsl6.sfn)
                # send_rtcm (qzsl6.rtcm)
            print ("{} {:13s}{} {}".format(
                qzsl6.prn, qzsl6.facility,
                "*" if qzsl6.alert else " ",
                message), file=sys.stderr)
        elif qzsl6.vendor == "MADOCA":
            message = ''
            while qzsl6.mdc2rtcm ():
                message += str (qzsl6.msgnum) + '(' + str (qzsl6.numsat) + ') '
                send_rtcm (qzsl6.rtcm)
            print ("{} {:13s}{} {} {}".format (
                qzsl6.prn, qzsl6.facility,
                "*" if qzsl6.alert else " ",
                gps2utc (qzsl6.wn, qzsl6.tow), message), file=sys.stderr)

# EOF

