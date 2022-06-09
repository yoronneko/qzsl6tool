#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# qzsl62rtcm.py: quasi-zenith satellite (QZS) L6 message to RTCM message converter
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.

import argparse
import bitstring
import sys
from   gps2utc import *
from   libbit  import *

class qzsl6_t:
    fp_trace = sys.stdout               # file pointer for trace
    fp_rtcm  = None                     # file pointer for rtcm output
    fp_msg   = sys.stdout               # message output file pointer
    dpn      = 0                        # data part number
    sfn      = 0                        # subframe number
    l6msg    = bitstring.BitArray ()    # QZS L6 message
    run      = False                    # CSSR decode start
    t_level  = 0                        # trace level
    ipntj_nsat = 0
    ipntj_nsig = 0
    ipntj_bsat = 0
    ipntj_bsig = 0
    ipntj_both = 0
    ipntj_bnull = 0

    def trace (self, level, *args):
        if level <= self.t_level and self.fp_trace:
            for arg in args:
                print (arg, file=self.fp_trace)

    def receive (self):
        sync = [b'0x00' for i in range (4)]
        ok = False
        try:
            while not ok:
                b = sys.stdin.buffer.read(1)
                if not b: return False
                sync = sync[1:4] + [b]
                if sync == [b'\x1a', b'\xcf', b'\xfc', b'\x1d']: ok = True
            prn   = int.from_bytes     (sys.stdin.buffer.read (  1), 'big')
            mtid  = int.from_bytes     (sys.stdin.buffer.read (  1), 'big')
            dpart = bitstring.BitArray (sys.stdin.buffer.read (212))
            rs    =                     sys.stdin.buffer.read ( 32)
        except KeyboardInterrupt:
            print ("User break - terminated", file=sys.stderr)
            return False
        vid = mtid >> 5 # vender ID
        if   vid == 0b001: vendor = "MADOCA"
        elif vid == 0b010: vendor = "MADOCA-PPP"
        elif vid == 0b011: vendor = "QZNMA"
        elif vid == 0b101: vendor = "CLAS"
        else: raise Exception (f"unknown vendor ID: {vid}")
        facility = "Kobe"            if (mtid >> 4) & 1 else "Hitachi-Ota"
        facility += ":" +          str ((mtid >> 3) & 1)
        servid   = "Clock/Ephemeris" if (mtid >> 2) & 1 else "Ionospheric"
        msg_ext  = "CNAV"            if (mtid >> 1) & 1 else "LNAV"
        sf_ind   = mtid & 1 # subframe indicator
        self.prn      = prn
        self.vendor   = vendor
        self.facility = facility
        self.servid   = servid
        self.msg_ext  = msg_ext
        self.sf_ind   = sf_ind
        self.alert    = dpart[0:1].uint
        self.dpart    = dpart[1:]
        return True

    def mdc_l6_head (self):
        dpart = self.dpart
        pos = 0
        self.tow   = dpart[pos:pos+20].uint; pos += 20
        self.wn    = dpart[pos:pos+13].uint; pos += 13
        self.dpart = dpart[pos:]

    def mdc2rtcm (self):
        dpart = self.dpart
        if len (dpart) < 12: return False
        pos = 0
        msgnum = dpart[pos:pos+12].uint; pos += 12
        if msgnum == 0: return False
        elif msgnum in {1057, 1059, 1061, 1062}:
            be = 20; bs = 6 # bit size of epoch and numsat for GPS
        elif msgnum in {1246, 1248, 1250, 1251}:
            be = 20; bs = 4 # bit size of epoch and numsat for QZSS
        elif msgnum in {1063, 1065, 1067, 1068}:
            be = 17; bs = 6 # bit size of epoch and numsat for GLONASS
        else:
            self.trace (1, f"Unknown message number {msgnum}")
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
        elif msgnum == 1250: pos +=  10 * numsat # QZSS URA
        elif msgnum == 1251: pos +=  26 * numsat # QZSS hr clock correction
        elif msgnum == 1063: pos += 134 * numsat # GLONASS orbit correction
        elif msgnum == 1065:                     # GLONASS code bias
            for i in range(numsat):
                satid = dpart[pos:pos+ 5].uint; pos += 5
                numcb = dpart[pos:pos+ 5].uint; pos += 5
                pos += numcb * 19
        elif msgnum == 1067: pos += 11 * numsat # GLONASS URA
        elif msgnum == 1068: pos += 27 * numsat # GLONASS hr clock correction
        else:
            self.trace (1, f"Warning: msgnum {msgnum} drop {len (dpart)} bit:")
            self.trace (1, f"{dpart.bin}")
            return False
        if pos % 8 != 0: pos += 8 - (pos % 8) # byte align
        self.rtcm   = dpart[0:pos].tobytes (); del dpart[0:pos]
        self.dpart  = dpart
        self.msgnum = msgnum
        self.numsat = numsat
        return True

    def cssr_l6_head (self):
        if self.sf_ind: # first data part
            self.dpn = 1
            self.l6msg = bitstring.BitArray (self.dpart)
            if not self.decode_cssr_head (): return False
            if self.subtype == 1:
                self.sfn = 1
                self.run = True
            else:
                if self.run: self.sfn += 1
        else: # continual data part
            if not self.run: return False
            self.dpn += 1
            if self.dpn == 6: # data part number should be less than 6
                self.trace (1, f"Warning: too many datapart")
                self.run = False
                self.dpn = 0; self.sfn = 0
                self.l6msg = bitstring.BitArray ()
                return False
            self.l6msg.append (self.dpart)

    def cssr2rtcm (self):
        if not self.run: return False
        if not self.decode_cssr_head (): return False
        if   self.subtype ==  1: return self.decode_cssr_st1  ()
        elif self.subtype ==  2: return self.decode_cssr_st2  ()
        elif self.subtype ==  3: return self.decode_cssr_st3  ()
        elif self.subtype ==  4: return self.decode_cssr_st4  ()
        elif self.subtype ==  5: return self.decode_cssr_st5  ()
        elif self.subtype ==  6: return self.decode_cssr_st6  ()
        elif self.subtype ==  7: return self.decode_cssr_st7  ()
        elif self.subtype ==  8: return self.decode_cssr_st8  ()
        elif self.subtype ==  9: return self.decode_cssr_st9  ()
        elif self.subtype == 10: return self.decode_cssr_st10 ()
        elif self.subtype == 11: return self.decode_cssr_st11 ()
        elif self.subtype == 12: return self.decode_cssr_st12 ()
        raise Exception (f"Unknown CSSR subtype: {self.subtype}")

    def decode_cssr_head (self):
        l6msg = self.l6msg
        l6msglen = len (l6msg)
        pos = 0
        if l6msglen < 12 + 4: return False
        self.msgnum = l6msg[pos:pos+12].uint; pos += 12 # message num, 4073
        if self.msgnum == 0:
            self.trace (2, f"CSSR Header: Null data {len(self.l6msg.bin)} bits")
            self.trace (2, f"CSSR dump: {self.l6msg.bin}")
            self.ipntj_bnull += len(self.l6msg.bin)
            self.l6msg = bitstring.BitArray ()
            return False
        if self.msgnum != 4073:
            self.trace (2, f"CSSR dump: {self.l6msg.bin}")
            self.trace (2, f"4073={bitstring.Bits(uint=4073, length=12).bin}")
            raise Exception (f"wrong CSSR message number: {self.msgnum}")
        self.subtype = l6msg[pos:pos+ 4].uint; pos +=  4 # subtype
        if self.subtype == 1:    # Mask message
            if l6msglen < pos + 20: return False
            self.epoch  = l6msg[pos:pos+20].uint; pos += 20 # GPS epoch time 1s
        elif self.subtype == 10: # Service Information
            self.pos = pos
            return False
        else:
            if l6msglen < pos + 12: return False
            self.hepoch = l6msg[pos:pos+12].uint; pos += 12 # GNSS hourly epoch
        if l6msglen < pos + 4 + 1 + 4: return False
        self.interval = l6msg[pos:pos+ 4].uint; pos +=  4 # update interval
        self.mmi      = l6msg[pos:pos+ 1].uint; pos +=  1 # multiple message
        self.iod      = l6msg[pos:pos+ 4].uint; pos +=  4 # IOD SSR
        self.pos      = pos
        return True

    def gnssid2satsys (self, gnssid):
        if   gnssid == 0: satsys = 'G'
        elif gnssid == 1: satsys = 'R'
        elif gnssid == 2: satsys = 'E'
        elif gnssid == 3: satsys = 'C'
        elif gnssid == 4: satsys = 'J'
        elif gnssid == 5: satsys = 'S'
        else: raise Exception (f'undefined gnssid {gnssid}')
        return satsys

    def sigmask2signame (self, satsys, sigmask):
        signame = f'satsys={satsys} sigmask={sigmask}'
        if satsys == 'G':
            signame = [
                "L1 C/A", "L1 P", "L1 Z-tracking", "L1 L1C(D)", "L1 L1C(P)",
                "L1 L1C(D+P)", "L2 L2C(M)", "L2 L2C(L)", "L2 L2C(M+L)",
                "L2 P", "L2 Z-tracking", "L5 I", "L5 Q", "L5 I+Q", "", ""]\
                [sigmask]
        elif satsys == 'R':
            signame = [
                "G1 C/A", "G1 P", "G2 C/A", "G2 P", "G1a(D)", "G1a(P)",
                "G1a(D+P)", "G2a(D)", "G2a(P)", "G2a(D+P)", "G3 I",
                "G3 Q", "G3 I+Q", "", "", "", ""]\
                [sigmask]
        elif satsys == 'E':
            signame = [
                "E1 B I/NAV OS/CS/SoL", "E1 C no data", "E1 B+C",
                "E5a I F/NAV OS", "E5a Q no data", "E5a I+Q",
                "E5b I I/NAV OS/CS/SoL", "E5b Q no data", "E5b I+Q",
                "E5 I", "E5 Q", "E5 I+Q", "Service specific 1",
                "Service specific 2", "Service specific 3", ""]\
                [sigmask]
        elif satsys == 'C':
            signame = [
                "B1 I", "B1 Q", "B1 I+Q", "B3 I", "B3 Q", "B3 I+Q",
                "B2 I", "B2 Q", "B2 I+Q", "", "", "", "", "", "",
                "", ""]\
                [sigmask]
        elif satsys == 'J':
            signame = [
                "L1 C/A", "L1 L1C(D)", "L1 L1C(P)", "L1 L1C(D+P)",
                "L2 L2C(M)", "L2 L2C(L)", "L2 L2C(M+L)", "L5 I",
                "L5 Q", "L5 I+Q", "", "", "", "", "", ""]\
                [sigmask]
        elif satsys == 'S':
            signame = [
                "L1 C/A", "L5 I", "L5 Q", "L5 I+Q", "", "", "", "",
                "", "", "", "", "", "", "", "", ""]\
                [sigmask]
        else:
            raise Exception (f"unassigned signal name for satsys={satsys} and sigmask={sigmask}")
        return signame

    def decode_cssr_st1 (self):
        l6msg = self.l6msg
        l6msglen = len (l6msg)
        if l6msglen < 49: return False
        pos   = self.pos
        ngnss = l6msg[pos:pos+ 4].uint; pos +=  4 # numer of GNSS
        if len (l6msg) < 49 + 61 * ngnss: return False
        satsys   = [None for i in range (ngnss)]
        nsatmask = [None for i in range (ngnss)]
        nsigmask = [None for i in range (ngnss)]
        cellmask = [None for i in range (ngnss)]
        gsys = {}
        gsig = {}
        for ignss in range (ngnss):
            ugnssid   = l6msg[pos:pos+ 4].uint; pos +=  4
            bsatmask  = l6msg[pos:pos+40]     ; pos += 40
            bsigmask  = l6msg[pos:pos+16]     ; pos += 16
            cmavail   = l6msg[pos:pos+ 1]     ; pos +=  1
            t_satsys  = self.gnssid2satsys (ugnssid)
            t_satmask = 0
            t_sigmask = 0
            t_gsys = []
            t_gsig = []
            for i, val in enumerate (bsatmask):
                if val:
                    t_satmask += 1
                    t_gsys.append (t_satsys+f'{i + 1:02d}')
            for i, val in enumerate (bsigmask):
                if val:
                    t_sigmask += 1
                    t_gsig.append (self.sigmask2signame (t_satsys, i))
            ncell = t_satmask * t_sigmask
            if cmavail:
                bcellmask = l6msg[pos:pos+ncell]; pos += ncell
            else:
                bcellmask = bitstring.BitArray ('0b1') * ncell
            cellmask[ignss] = bcellmask
            satsys  [ignss] = t_satsys
            nsatmask[ignss] = t_satmask
            nsigmask[ignss] = t_sigmask
            gsys [t_satsys] = t_gsys
            gsig [t_satsys] = t_gsig
        self.satsys   = satsys        # satellite system
        self.nsatmask = nsatmask    # number of satellite mask
        self.nsigmask = nsigmask    # number of signal mask
        self.cellmask = cellmask    # cell mask
        self.gsys     = gsys        # dict of sat   name from system name
        self.gsig     = gsig        # dict of sigal name from system name
        if self.fp_trace:
            self.ipntj_nsat = 0
            self.ipntj_nsig = 0
            for i, satsys in enumerate (self.satsys):
                pos_mask = 0 # mask position
                for j, gsys in enumerate (self.gsys[satsys]):
                    self.ipntj_nsat += 1
                    msg_trace = 'ST1 '+ gsys
                    for gsig in self.gsig[satsys]:
                        mask = self.cellmask[i][pos_mask]
                        pos_mask += 1
                        if not mask: continue
                        msg_trace += ' ' + gsig
                        self.ipntj_nsig += 1
                    self.trace (1, msg_trace)
        self.rtcm  = l6msg[:pos].tobytes ()
        self.l6msg = l6msg[pos:] # removal of ST1 message
# IPNTJ
        if self.fp_trace: self.trace (3, f'IPNTJ {self.ipntj_nsat} {self.ipntj_nsig} {self.ipntj_bsat} {self.ipntj_bsig} {self.ipntj_both} {self.ipntj_bnull} {self.ipntj_bsat + self.ipntj_bsig + self.ipntj_both + self.ipntj_bnull}')
        self.ipntj_bsat = 0
        self.ipntj_bsig = 0
        self.ipntj_both = pos
        self.ipntj_bnull= 0
        return True

    def decode_cssr_st2 (self):
        l6msg = self.l6msg
        l6msglen = len (l6msg)
        pos = self.pos
        ipntj_pos = pos
        for satsys in self.satsys:
            w_iode = 10 if satsys == 'E' else 8 # IODE bit width
            for gsys in self.gsys[satsys]:
                if l6msglen < pos + w_iode + 15 + 13 + 13: return False
                iode     = l6msg[pos:pos+w_iode].uint; pos += w_iode
                d_radial = l6msg[pos:pos+15].int; pos += 15
                d_along  = l6msg[pos:pos+13].int; pos += 13
                d_cross  = l6msg[pos:pos+13].int; pos += 13
                radial = d_radial * 0.0016 if d_radial != -16384 else 9999
                along  = d_radial * 0.0064 if d_along  != -16384 else 9999
                cross  = d_radial * 0.0064 if d_cross  != -16384 else 9999
                self.trace (1, f"ST2 {gsys} IODE={iode:3d} radial={radial:4.1f} along={along:4.1f} cross={cross:4.1f}")
        self.rtcm  = l6msg[:pos].tobytes ()
        self.l6msg = l6msg[pos:] # removal of ST2 message
        self.ipntj_both += ipntj_pos
        self.ipntj_bsat += pos - ipntj_pos
        return True

    def decode_cssr_st3 (self):
        l6msg = self.l6msg
        l6msglen = len (l6msg)
        pos = self.pos
        ipntj_pos = pos
        for i, satsys in enumerate (self.satsys):
            for gsys in self.gsys[satsys]:
                if l6msglen < pos + 15: return False
                ic0 = l6msg[pos:pos+15].int; pos += 15
                c0 = ic0 * 0.0016 if ic0 != -16384 else 9999
                self.trace (1, f"ST3 {gsys} {c0:4.1f}")
        self.rtcm  = l6msg[:pos].tobytes ()
        self.l6msg = l6msg[pos:] # rmoval of ST3 message
        self.ipntj_both += ipntj_pos
        self.ipntj_bsat += pos - ipntj_pos
        return True

    def decode_cssr_st4 (self):
        l6msg = self.l6msg
        nsigsat = 0 # Nsig * Nsat
        for i, satsys in enumerate (self.satsys):
            pos_mask = 0 # mask position
            for gsys in self.gsys[satsys]:
                for gsig in self.gsig[satsys]:
                    mask = self.cellmask[i][pos_mask]
                    pos_mask += 1
                    if not mask: continue
                    nsigsat += 1
        if len (l6msg) < 37 + 11 * nsigsat: return False
        pos = self.pos # mask position
        ipntj_pos = pos
        for i, satsys in enumerate (self.satsys):
            pos_mask = 0 # mask position
            for j, gsys in enumerate (self.gsys[satsys]):
                for k, gsig in enumerate (self.gsig[satsys]):
                    mask = self.cellmask[i][pos_mask]
                    pos_mask += 1
                    if not mask: continue
                    cb = l6msg[pos:pos+11].int; pos += 11
                    code_bias = cb * 0.02 if cb != -1024 else 9999
                    self.trace (1, f"ST4 {gsys} {gsig:13s} code_bias={code_bias:4.1f}")
        self.rtcm  = l6msg[:pos].tobytes ()
        self.l6msg = l6msg[pos:] # removal of ST4 message
        self.ipntj_both += ipntj_pos
        self.ipntj_bsig += pos - ipntj_pos
        return True

    def decode_cssr_st5 (self):
        l6msg = self.l6msg
        l6msglen = len (l6msg)
        pos = self.pos
        ipntj_pos = pos
        for i, satsys in enumerate (self.satsys):
            pos_mask = 0
            for gsys in self.gsys[satsys]:
                for gsig in self.gsig[satsys]:
                    mask = self.cellmask[i][pos_mask]
                    pos_mask += 1
                    if not mask: continue
                    if l6msglen < pos + 15 + 2: return False
                    pb = l6msg[pos:pos+15].int ; pos += 15
                    di = l6msg[pos:pos+ 2].uint; pos +=  2
                    phase_bias = pb * 0.001 if pb != -16384 else 9999
                    self.trace (1, f"ST5 {gsys} {gsig:13s} phase_bias={phase_bias:4.1f} discont={di}")
        self.rtcm  = l6msg[:pos].tobytes ()
        self.l6msg = l6msg[pos:] # removal of ST5 message
        self.ipntj_both += ipntj_pos
        self.ipntj_bsig += pos - ipntj_pos
        return True

    def decode_cssr_st6 (self):
        l6msg = self.l6msg
        l6msglen = len (l6msg)
        if l6msglen < 45: return False
        pos = self.pos
        ipntj_pos = pos
        f_cb = l6msg[pos:pos+1].uint; pos += 1 # code bias existing flag
        f_pb = l6msg[pos:pos+1].uint; pos += 1 # phase bias existing flag
        f_nb = l6msg[pos:pos+1].uint; pos += 1 # network bias existing flag
        svmask = {}
        cnid = 0
        for satsys in self.satsys:
            bcellmask = bitstring.BitArray ('0b1') * len (self.gsys[satsys])
        self.trace (1, f"ST6 code_bias={'on' if f_cb else 'off'} phase_bias={'on' if f_pb else 'off'} network_bias={'on' if f_nb else 'off'}")
        if f_nb:
            cnid = l6msg[pos:pos+5].uint; pos += 5 # compact network ID
            for satsys in self.satsys:
                ngsys = len (self.gsys[satsys])
                if l6msglen < pos + ngsys: return False
                svmask[satsys] = l6msg[pos:pos+ngsys]; pos += ngsys
                self.trace (2, f"ST6 {satsys} NID={cnid} mask={svmask[satsys].bin}")
        for i, satsys in enumerate (self.satsys):
            pos_mask = 0 # mask position
            for j, gsys in enumerate (self.gsys[satsys]):
                for gsig in self.gsig[satsys]:
                    mask = self.cellmask[i][pos_mask]
                    pos_mask += 1
                    if not svmask[satsys][j] or not mask: continue
                    cb = -1024; pb = -16384; pdi = 0
                    if f_cb:
                        if l6msglen < pos + 11: return False
                        cb = l6msg[pos:pos+11].int; pos += 11 # code bias
                    if f_pb:
                        if l6msglen < pos + 15 + 2: return False
                        pb = l6msg[pos:pos+15].int ; pos += 15
                        di = l6msg[pos:pos+ 2].uint; pos +=  2
                    code_bias  = cb * 0.02  if cb !=  -1024 else 9999
                    phase_bias = pb * 0.001 if cb != -16384 else 9999
                    self.trace (1, f"ST6 {gsys} {gsig:13s} code_bias={code_bias:4.1f} phase_bias={phase_bias:6.3f} discont={di}")
        self.rtcm  = l6msg[:pos].tobytes ()
        self.l6msg = l6msg[pos:] # removal of ST6 message
        self.ipntj_both += ipntj_pos + 3
        self.ipntj_bsig += pos-ipntj_pos-3
        return True

    def decode_cssr_st7 (self):
        l6msg = self.l6msg
        l6msglen = len (l6msg)
        if l6msglen < 37: return False
        pos = self.pos
        ipntj_pos = pos
        for satsys in self.satsys:
            for gsys in self.gsys[satsys]:
                if l6msglen < pos + 6: return False
                ura = l6msg[pos:pos+6].uint; pos += 6
                self.trace (1, f"ST7 {gsys} URA {ura}")
        self.rtcm  = l6msg[:pos].tobytes ()
        self.l6msg = l6msg[pos:] # removal of ST7 message
        self.ipntj_both += ipntj_pos
        self.ipntj_bsat += pos-ipntj_pos
        return True

    def decode_cssr_st8 (self):
        l6msg = self.l6msg
        l6msglen = len (l6msg)
        if l6msglen < 44: return False
        pos = self.pos
        ipntj_pos = pos
        stec_type = l6msg[pos:pos+2].uint; pos += 2 # STEC correction type
        cnid      = l6msg[pos:pos+5].uint; pos += 5 # compact network ID
        svmask = {}
        for satsys in self.satsys:
            ngsys = len (self.gsys[satsys])
            if l6msglen < pos + ngsys: return False
            svmask[satsys] = l6msg[pos:pos+ngsys]; pos += ngsys
        for satsys in self.satsys:
            for i, gsys in enumerate (self.gsys[satsys]):
                if not svmask[satsys][i]: continue
                if l6msglen < pos + 6 + 14: return False
                qi   = l6msg[pos:pos+ 6].uint; pos +=  6 # quality indicator
                ic00 = l6msg[pos:pos+14].int ; pos += 14
                ic01 = -2048; ic10 = -2048; ic11 = -512
                ic02 =  -128; ic20 =  -128
                if 1 <= stec_type:
                    if l6msglen < pos + 12 + 12: return False
                    ic01 = l6msg[pos:pos+12].int ; pos += 12
                    ic10 = l6msg[pos:pos+12].int ; pos += 12
                if 2 <= stec_type:
                    if l6msglen < pos + 10: return False
                    ic11 = l6msg[pos:pos+10].int ; pos += 10
                if 3 <= stec_type:
                    if l6msglen < pos + 8 + 8: return False
                    ic02 = l6msg[pos:pos+ 8].int ; pos +=  8
                    ic20 = l6msg[pos:pos+ 8].int ; pos +=  8
                c00 = ic00 * 0.05  if ic00 != -8192 else 9999
                c01 = ic01 * 0.02  if ic01 != -2048 else 9999
                c10 = ic10 * 0.02  if ic10 != -2048 else 9999
                c11 = ic11 * 0.02  if ic11 !=  -512 else 9999
                c02 = ic02 * 0.005 if ic02 !=  -128 else 9999
                c20 = ic20 * 0.005 if ic20 !=  -128 else 9999
                self.trace (1, f"ST8 {gsys} c00={c00:.2f} c01={c01:.2f} c10={c10:.2f} c11={c11:.2f} c02={c02:.2f} c20={c20:.2f}")
        self.rtcm  = l6msg[:pos].tobytes ()
        self.l6msg = l6msg[pos:] # removal of ST8 message
        self.ipntj_both += ipntj_pos + 7
        self.ipntj_bsat += pos-ipntj_pos-7
        return True

    def decode_cssr_st9 (self):
        l6msg = self.l6msg
        l6msglen = len (l6msg)
        if l6msglen < 45: return False
        pos = self.pos
        ctype  = l6msg[pos:pos+2].uint; pos += 2 # correction type
        crange = l6msg[pos:pos+1].uint; pos += 1 # correction range
        cnid   = l6msg[pos:pos+5].uint; pos += 5
        svmask = {}
        for satsys in self.satsys:
            ngsys = len (self.gsys[satsys])
            if l6msglen < pos + ngsys: return False
            svmask[satsys] = l6msg[pos:pos+ngsys]; pos += ngsys
        if l6msglen < pos + 6 + 6: return False
        tqi   = l6msg[pos:pos+6].uint; pos += 6 # tropo quality indicator
        ngrid = l6msg[pos:pos+6].uint; pos += 6 # number of grids
        for i in range (ngrid):
            if l6msglen < pos + 9 + 8: return False
            ivd_hs = l6msg[pos:pos+9].int; pos += 9 # hydrostatic vertical delay
            ivd_w  = l6msg[pos:pos+8].int; pos += 8 # wet vertical delay
            vd_hs = ivd_hs * 0.004 if ivd_hs != -256 else 9999
            vd_w  = ivd_w  * 0.004 if ivd_w  != -128 else 9999
            for satsys in self.satsys:
                for j, gsys in enumerate (self.gsys[satsys]):
                    if not svmask[satsys][j]: continue
                    if crange:
                        if l6msglen < pos + 16: return False
                        res = l6msg[pos:pos+16].int; pos += 16
                        residual = res * 0.04 if res != -32767 else 9999
                    else:
                        if l6msglen < pos + 7: return False
                        res = l6msg[pos:pos+7].int; pos += 7
                        residual = res * 0.04 if res != -64 else 9999
                    self.trace (1, f'ST9 grid {i+1:2d}/{ngrid:2d} {gsys} dry-delay={vd_hs:6.3f} wet-delay={vd_w:6.3f} residual={residual:5.2f}')
        self.trace (1, f"ST9 correct_type={ctype} correction_range={crange} NID={cnid} quality={tqi} ngrid={ngrid}")
        self.rtcm  = l6msg[:pos].tobytes ()
        self.l6msg = l6msg[pos:] # removal of ST9 message
        self.both += pos
        return True

    def decode_cssr_st10 (self):
        self.trace (1, f"ST10")
        self.l6msg = bitstring.BitArray ()
        return False

    def decode_cssr_st11 (self):
        l6msg = self.l6msg
        l6msglen = len (l6msg)
        if l6msglen < 40: return False
        pos = self.pos
        ipntj_pos = pos
        f_o = l6msg[pos:pos+1].uint; pos += 1 # orbit existing flag
        f_c = l6msg[pos:pos+1].uint; pos += 1 # clock existing flag
        f_n = l6msg[pos:pos+1].uint; pos += 1 # network correction
        self.trace (1, f"ST11 Orb={'on' if f_o else 'off'} Clk={'on' if f_c else 'off'} Net={'on' if f_n else 'off'}")
        if f_n:
            if l6msglen < pos + 5: return False
            cnid = l6msg[pos:pos+5].uint; pos += 5 # compact network ID
            self.trace (1, f"ST11 NID={cnid}")
            svmask = {}
            for satsys in self.satsys:
                ngsys = len (self.gsys[satsys])
                if l6msglen < pos + ngsys: return False
                svmask[satsys] = l6msg[pos:pos+ngsys]; pos += ngsys
            for satsys in self.satsys:
                for i, gsys in enumerate (self.gsys[satsys]):
                    if not svmask[satsys][i]: continue
                    iode = 0
                    id_radial = -16384; id_along = -4096; id_cross = -4096
                    id_clock  = -16384
                    if f_o:
                        w_iode = 10 if satsys == 'E' else 8 # IODE width
                        if l6msglen < pos + w_iode + 15 + 13 + 13: return False
                        iode = l6msg[pos:pos+w_iode].uint; pos += w_iode
                        id_radial = l6msg[pos:pos+15].int; pos += 15
                        id_along  = l6msg[pos:pos+13].int; pos += 13
                        id_cross  = l6msg[pos:pos+13].int; pos += 13
                    if f_c:
                        if l6msglen < pos + 15: return False
                        ic0  = l6msg[pos:pos+15].int; pos += 15
                    d_radial = id_radial * 0.0016 if id_radial != -16384 else 9999
                    d_along = id_along * 0.0064 if id_along != -4096 else 9999
                    d_cross = id_cross * 0.0064 if id_cross != -4096 else 9999
                    c0 = ic0 * 0.0016 if ic0 != -16384 else 9999
                    self.trace (1, f"ST11 {gsys} radial={d_radial:5.1f} along={d_along:5.1f} cross={d_cross:5.1f} c0={c0:5.1f}")
        self.rtcm  = l6msg[:pos].tobytes ()
        self.l6msg = l6msg[pos:] # removal of ST11 message
        self.ipntj_both += ipntj_pos + 3
        self.ipntj_bsat += pos - ipntj_pos - 3
        if f_n: # NIDをbsatとしてカウントしてしまったことを補正する
            self.ipntj_both += 5
            self.ipntj_bsat -= 5
        return True

    def decode_cssr_st12 (self):
        l6msg = self.l6msg
        l6msglen = len (l6msg)
        if l6msglen < 52: return False
        pos = self.pos
        tropo = l6msg[pos:pos+2]     ; pos += 2 # Tropo correction avail
        stec  = l6msg[pos:pos+2]     ; pos += 2 # STEC correction avail
        cnid  = l6msg[pos:pos+5].uint; pos += 5 # compact network ID
        ngrid = l6msg[pos:pos+6].uint; pos += 6 # number of grids
        self.trace (1, f"ST12 tropo={tropo} stec={stec} NID={cnid} ngrid={ngrid}")
        it00 = -256; it01 = -64; it10 = -64; it11 = -64
        tro = 9999; trs = 9999
        if tropo[0]:
            # 0 <= ttype (forward reference)
            if l6msglen < pos + 6 + 2 + 9: return False
            tqi   = l6msg[pos:pos+6].uint; pos += 6 # tropo quality indicator
            ttype = l6msg[pos:pos+2].uint; pos += 2 # tropo correction type
            it00  = l6msg[pos:pos+9].int ; pos += 9 # tropo poly coeff
            if 1 <= ttype:
                if l6msglen < pos + 7 + 7: return False
                it01 = l6msg[pos:pos+7].int; pos += 7
                it10 = l6msg[pos:pos+7].int; pos += 7
            if 2 <= ttype:
                if l6msglen < pos + 7: return False
                it11 = l6msg[pos:pos+7].int; pos += 7
            t00 = it00 * 0.004 if it00 !=  -256 else 9999
            t01 = it01 * 0.002 if it01 !=   -64 else 9999
            t10 = it10 * 0.002 if it10 !=   -64 else 9999
            t11 = it11 * 0.001 if it11 !=   -64 else 9999
            self.trace (1, f"ST12 Tropo quality={tqi} correction_type(0-2)={ttype} t00={t00} t01={t01} t10={t10} t11={t11}")
        if tropo[1]:
            if l6msglen < pos + 1 + 4: return False
            trs  = l6msg[pos:pos+1].uint; pos += 1 # tropo residual size
            itro = l6msg[pos:pos+4].uint; pos += 4 # tropo residual offset
            tro  = itro * 0.02
            self.trace (2, f"ST12 Tropo offset={tro}")
            wb = 8 if trs else 6
            if l6msglen < pos + wb * ngrid: return False
            for i in range (ngrid):
                itr = l6msg[pos:pos+wb].int; pos += wb # troposphere residual
                tr = itr * 0.004
                if (trs == 0 and itr != -32) or (trs == 1 and itr != -128):
                    tr = 9999
                self.trace (2, f"ST12 Tropo grid {i+1}/{ngrid} residual={tr:5.2f}")
        ipntj_pos = pos
        if stec[0]:
            svmask = {}
            for satsys in self.satsys:
                ngsys = len (self.gsys[satsys])
                if l6msglen < pos + ngsys: return False
                svmask[satsys] = l6msg[pos:pos+ngsys]; pos += ngsys
            for satsys in self.satsys:
                for i, gsys in enumerate (self.gsys[satsys]):
                    if not svmask[satsys][i]: continue
                    if l6msglen < pos + 6 + 2 + 14: return False
                    sqi  = l6msg[pos:pos+ 6].uint; pos +=  6 # quality indicator
                    sct  = l6msg[pos:pos+ 2].uint; pos +=  2 # correction type
                    ic00 = l6msg[pos:pos+14].int ; pos += 14
                    ic01 = -2048; ic10 = -2048; ic11 = -512
                    ic02 =  -128; ic20 =  -128
                    if 1 <= sct:
                        if l6msglen < pos + 12 + 12: return False
                        ic01 = l6msg[pos:pos+12].int; pos += 12
                        ic10 = l6msg[pos:pos+12].int; pos += 12
                    if 2 <= sct:
                        if l6msglen < pos + 10: return False
                        ic11 = l6msg[pos:pos+10].int; pos += 10
                    if 3 <= sct:
                        if l6msglen < pos + 8 + 8: return False
                        ic02 = l6msg[pos:pos+8].int; pos += 8
                        ic20 = l6msg[pos:pos+8].int; pos += 8
                    c00 = ic00 * 0.05  if ic00 != -8192 else 9999
                    c01 = ic01 * 0.02  if ic01 != -2048 else 9999
                    c10 = ic10 * 0.02  if ic10 != -2048 else 9999
                    c11 = ic11 * 0.02  if ic11 !=  -512 else 9999
                    c02 = ic02 * 0.005 if ic02 !=  -128 else 9999
                    c20 = ic20 * 0.005 if ic20 !=  -128 else 9999
                    self.trace (1, f"ST12 STEC {gsys} quality={sqi:02x} type={sct} c00={c00:.1f} c01={c01:.1f} c10={c10:.1f} c11={c11:.1f} c02={c02:.1f} c20={c20:.1f}")
                    if l6msglen < pos + 2: return False
                    srs = l6msg[pos:pos+2].uint; pos += 2 # STEC residual size
                    bw = 4; lsb = 0.04
                    if srs == 1:
                        bw = 4; lsb = 0.12
                    elif srs == 2:
                        bw = 5; lsb = 0.16
                    elif srs == 3:
                        bw = 7; lsb = 0.24
                    for i in range (ngrid):
                        if l6msglen < pos + bw: return False
                        isr = l6msg[pos:pos+bw].int; pos += bw
                        if   srs == 0 and isr !=  -8: sr = isr * 0.04
                        elif srs == 1 and isr !=  -8: sr = isr * 0.12
                        elif srs == 2 and isr != -16: sr = isr * 0.16
                        elif srs == 3 and isr != -64: sr = isr * 0.24
                        else:                         sr = 9999
                        self.trace (1, f"ST12 STEC {gsys} grid {i+1:2d}/{ngrid:2d} residual={sr:5.2f}")
        self.rtcm  = l6msg[:pos].tobytes ()
        self.l6msg = l6msg[pos:] # removal of ST12 message
        self.ipntj_both += ipntj_pos
        self.ipntj_bsat += pos - ipntj_pos
        return True

    def show (self, message):
        if self.fp_msg:
            print ("{} {:13s}{} {}".format (
                self.prn, self.facility, "*" if self.alert else " ",
                message), file=self.fp_msg)

    def send_rtcm (self):
        if not self.fp_rtcm: return
        rtcm = b'\xd3' + len (self.rtcm).to_bytes(2, 'big') + self.rtcm
        rtcm_crc = rtk_crc24q (rtcm, len (rtcm))
        self.fp_rtcm.buffer.write (rtcm)
        self.fp_rtcm.buffer.write (rtcm_crc)
        self.fp_rtcm.flush ()

if __name__ == '__main__':
    qzsl6 = qzsl6_t ()
    parser = argparse.ArgumentParser (
        description = 'Quasi-zenith satellite (QZS) L6 message to RTCM converter')
    parser.add_argument (
        '-t', '--trace', type = int, default = 0,
        help = 'trace level (integer) for debug')
    parser.add_argument (
        '-r', '--rtcm', action='store_true',
        help = 'RTCM message output')
    parser.add_argument (
        '-m', '--message', action='store_true',
        help = 'show QZS messages to stderr')
    args = parser.parse_args ()
    if 0 < args.trace: qzsl6.t_level = args.trace
    if args.rtcm: # RTCM message output to stdout
        qzsl6.t_level = 0
        qzsl6.fp_rtcm = sys.stdout
        qzsl6.fp_msg = None
    if args.message: # show QZS message to stderr
        qzsl6.fp_msg = sys.stderr
    while qzsl6.receive ():
        message = ''
        if qzsl6.vendor == "MADOCA":
            qzsl6.mdc_l6_head ()
            message += gps2utc (qzsl6.wn, qzsl6.tow) + ' '
            while qzsl6.mdc2rtcm ():
                message += str (qzsl6.msgnum) + '(' + str (qzsl6.numsat) + ') '
                qzsl6.send_rtcm ()
        elif qzsl6.vendor in {"CLAS", "MADOCA-PPP"}:
            qzsl6.cssr_l6_head ()
            message += qzsl6.vendor + ' '
            if qzsl6.sfn != 0:
                message += 'SF' + str (qzsl6.sfn) + ' DP' + str (qzsl6.dpn)
            while qzsl6.cssr2rtcm ():
                message += f' ST{qzsl6.subtype}'
                qzsl6.send_rtcm ()
        elif qzssl6.vendor == "QZNMA":
            qzsl6.cssr_l6_head ()
            message += qzsl6.vendor
        else: raise Exception (f"Unknown vender name: {qzssl6.vendor}")
        qzsl6.show (message)
    if qzsl6.fp_trace: qzsl6.trace (3, f'IPNTJ {qzsl6.ipntj_nsat} {qzsl6.ipntj_nsig} {qzsl6.ipntj_bsat} {qzsl6.ipntj_bsig} {qzsl6.ipntj_both} {qzsl6.ipntj_bnull} {qzsl6.ipntj_bsat + qzsl6.ipntj_bsig + qzsl6.ipntj_both + qzsl6.ipntj_bnull}')

# EOF
