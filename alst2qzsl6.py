#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# alst2qzsl6.py: Allystar HD9310C raw to quasi-zenith satellite (QZS) L6 raw converter
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.

import sys
from libbit import *
from gps2utc import *

class alst_t:
    dict_snr = {}; dict_data = {}; last_gpst = 0

    def receive (self):
        sync = [b'0x00' for i in range (4)]
        ok = False
        try:
            while not ok:
                b = sys.stdin.buffer.read(1)
                if not b: return False
                sync = sync[1:4] + [b]
                if sync == [b'\xf1', b'\xd9', b'\x02', b'\x10']: ok = True
            payld = b'\x02\x10' + sys.stdin.buffer.read (266)
            csum  = sys.stdin.buffer.read (2)
        except KeyboardInterrupt:
            print ("User break - terminated", file = sys.stderr)
            return False
        len_payld = int.from_bytes (payld[ 2:  4], 'little')
        prn       = int.from_bytes (payld[ 4:  6], 'little') - 700
        freqid    = int.from_bytes (payld[ 6:  7], 'little')
        len_data  = int.from_bytes (payld[ 7:  8], 'little') - 2
        gpsw      = int.from_bytes (payld[ 8: 10], 'big'   )
        gpst      = int.from_bytes (payld[10: 14], 'big'   ) // 1000
        snr       = int.from_bytes (payld[14: 15], 'big'   )
        flag      = int.from_bytes (payld[15: 16], 'big'   )
        data      =                 payld[16:268]
        err = ""
        csum1, csum2 = rtk_checksum (payld)
        if csum[0] != csum1 or csum[1] != csum2: err += "CS "
        if len_payld != 264: err += "Payload "
        if len_data  !=  63: err += "Data "
        if flag & 0x01     : err += "RS "
        if flag & 0x02     : err += "Week "
        if flag & 0x04     : err += "TOW "
        self.data = data
        self.prn  = prn
        self.gpsw = gpsw
        self.gpst = gpst
        self.snr  = snr
        self.err  = err
        if self.last_gpst == 0: self.last_gpst = gpst
        return True

    def pick_up (self):
        prn = 0; snr = 0; data = b''
        if self.last_gpst != self.gpst and len (self.dict_snr) != 0:
            self.last_gpst = self.gpst
            prn = sorted (self.dict_snr.items(),
                key=lambda x:x[1], reverse=True)[0][0]
            snr  = self.dict_snr[prn]
            data = self.dict_data[prn]
            print ("---> prn {} (snr {})" .format (prn, snr), file=sys.stderr)
            self.dict_snr.clear (); self.dict_data.clear ();
        elif not self.err:
            self.dict_snr [self.prn] = self.snr
            self.dict_data[self.prn] = self.data
        return prn, snr, data

    def show (self):
        print ("{} {} {} {}".format (
            self.prn, gps2utc (self.gpsw, self.gpst), self.snr, self.err),
            file=sys.stderr)

def send_l6raw (data):
    sys.stdout.buffer.write (data)
    sys.stdout.flush ()

def send_ubxl6 (prn, snr, data):
    ubxpld = b'\x02\x72'                             # class ID
    ubxpld += (264).to_bytes (2, byteorder='little') # message length
    ubxpld += b'\x01'                                # message version
    ubxpld += (prn-192).to_bytes (2, byteorder='little')   # SVID
    ubxpld += snr.to_bytes (2, byteorder='little')   # C/No
    ubxpld += (0).to_bytes (4, byteorder='little')   # local time tag
    ubxpld += (0).to_bytes (1, byteorder='little')   # L6 group delay
    ubxpld += (0).to_bytes (1, byteorder='little')   # corrected bit num
    ubxpld += (0).to_bytes (1, byteorder='little')   # chanel info.
    ubxpld += (0).to_bytes (2, byteorder='little')   # reserved
    ubxpld += data                                   # CLAS data
    csum1, csum2 = rtk_checksum (ubxpld)
    sys.stdout.buffer.write( 
        b'\xb5\x62' + \
        csum1.to_bytes (1, 'little') + \
        csum2.to_bytes (1, 'little') + \
        ubxpld
    )
    sys.stdout.flush()

if __name__ == '__main__':
    alst = alst_t ()
    while alst.receive ():
        prn, snr, data = alst.pick_up ()
        try:
            if prn:
                # send_ubxl6 (prn, snr, data)
                send_l6raw (data)
            alst.show ()
        except BrokenPipeError:
            sys.exit ()

# EOF
