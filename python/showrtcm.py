#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# showrtcm.py: RTCM message dump
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.

import sys
from ecef2llh import *
from libbit import *


class rtcm_t:
    class ssr_t:
        pass
    ssr = ssr_t()

    def receive(self):
        b = b''
        try:
            while (b != b'\xd3'):
                b = sys.stdin.buffer.read(1)
                if not b:
                    return False
            bl = sys.stdin.buffer.read(2)     # possible length
            mlen = getbitu(bl, 6, 10)
            bp = sys.stdin.buffer.read(mlen)  # possible payload
            bc = sys.stdin.buffer.read(3)     # possible CRC
            frame = b'\xd3' + bl + bp
            ok = False
            while not ok:
                if bc == rtk_crc24q(frame, len(frame)):
                    ok = True
                else:  # CRC error
                    frame = frame[1:] + bc
                    syncpos = -1
                    for i in range(len(frame)):
                        if frame[i] == b'\xd3':
                            syncpos = i
                            break
                    if 0 <= syncpos:
                        print("CRC error, using previously loaded data",
                              file=sys.stderr)
                        frame = frame[syncpos:]
                        bl = frame[1:3]
                        mlen = getbitu(bl, 6, 10)
                        frame += sys.stdin.buffer.read(mlen - len(frame))
                        bc = sys.stdin.buffer.read(3)
                    else:
                        print("CRC error, reloading data", file=sys.stderr)
                        while (b != b'\xd3'):
                            b = sys.stdin.buffer.read(1)
                            if not b:
                                return False
                        bl = sys.stdin.buffer.read(2)     # possible length
                        mlen = getbitu(bl, 6, 10)
                        bp = sys.stdin.buffer.read(mlen)  # possible payload
                        bc = sys.stdin.buffer.read(3)     # possible CRC
                        frame = b'\xd3' + bl + bp
        except KeyboardInterrupt:
            print("User break - terminated", file=sys.stderr)
            return False
        self.payload = frame[3:]
        self.mlen = mlen
        self.string = ''
        return True

    def parse_head(self):  # parse RTCM header
        self.mnum = getbitu(self.payload, 0, 12)  # message number
        self.pos = 12
        self.satsys = self.mnum2satsys()
        self.mtype = self.mnum2mtype()

    def mnum2satsys(self, mnum=0):  # message number to satellite system
        satsys = ''
        if mnum == 0:
            mnum = self.mnum
        if mnum in {1001, 1002, 1003, 1004, 1019, 1071, 1072, 1073, 1074,
                    1075, 1076, 1077, 1057, 1058, 1059, 1060, 1061, 1062,
                    1230, 11}:
            satsys = 'G'
        if mnum in {1009, 1010, 1011, 1012, 1020, 1081, 1081, 1082, 1083,
                    1084, 1085, 1086, 1087, 1063, 1064, 1065, 1066, 1067,
                    1068}:
            satsys = 'R'
        if mnum in {1045, 1046, 1091, 1092, 1093, 1094, 1095, 1096, 1097,
                    1240, 1241, 1242, 1243, 1244, 1245, 12}:
            satsys = 'E'
            return satsys
        if mnum in {1044, 1111, 1112, 1113, 1114, 1115, 1116, 1117, 1246,
                    1247, 1248, 1249, 1250, 1251, 13}:
            satsys = 'J'
        if mnum in {1042, 63, 1121, 1122, 1123, 1124, 1125, 1126, 1127, 1258,
                    1259, 1260, 1261, 1262, 1263, 14}:
            satsys = 'C'
        if mnum in {1101, 1102, 1103, 1104, 1105, 1106, 1107}:
            satsys = 'S'
        if mnum in {1041, 1131, 1132, 1133, 1134, 1135, 1136, 1137}:
            satsys = 'I'
        return satsys

    def mnum2mtype(self, mnum=0):  # message number to message type
        mtype = ''
        if mnum == 0:
            mnum = self.mnum
        if mnum in {1001, 1009}:
            mtype = 'Obs Comp L1'
        if mnum in {1002, 1010}:
            mtype = 'Obs Full L1'
        if mnum in {1003, 1011}:
            mtype = 'Obs Comp L1L2'
        if mnum in {1004, 1012}:
            mtype = 'Obs Full L1L2'
        if mnum in {1019, 1020, 1044, 1042, 1041, 63}:
            mtype = 'NAV'
        if mnum == 1230:
            mtype = 'CodePhase bias'
        if mnum == 1045:
            mtype = 'F/NAV'
        if mnum == 1046:
            mtype = 'I/NAV'
        if (1071 <= mnum and mnum <= 1097) or \
           (1101 <= mnum and mnum <= 1137):
            mtype = f'MSM{mnum % 10}'
        if mnum in {1057, 1063, 1240, 1246, 1258}:
            mtype = 'SSR orbit'
        if mnum in {1058, 1064, 1241, 1247, 1259}:
            mtype = 'SSR clock'
        if mnum in {1059, 1065, 1242, 1248, 1260}:
            mtype = 'SSR code bias'
        if mnum in {1060, 1066, 1243, 1249, 1261}:
            mtype = 'SSR obt/clk'
        if mnum in {1061, 1067, 1244, 1250, 1262}:
            mtype = 'SSR URA'
        if mnum in {1062, 1068, 1245, 1251, 1263}:
            mtype = 'SSR hr clock'
        if mnum in {11, 12, 13, 14}:
            mtype = 'SSR phase bias'
        if mnum in {1007, 1008, 1033}:
            mtype = 'Ant/Rcv info'
        if mnum in {1005, 1006}:
            mtype = 'Position'
        if mnum == 4073:
            mtype = 'CSSR'
        return mtype

    def ssr_head_decode(self):  # ssr
        payload = self.payload
        pos = self.pos
        mtype = self.mtype
        satsys = self.satsys
        ssr = self.ssr
        bw = 20  # bit width changes according to satellite system
        if satsys == 'R':
            bw = 17
        ssr.epoch = getbitu(payload, pos, bw)
        pos += bw  # ephch time
        ssr.intvl = getbitu(payload, pos, 4)
        pos += 4  # ssr update interval
        ssr.mmi = getbitu(payload, pos, 1)
        pos += 1  # multiple message indicator
        if mtype == 'SSR orbit' or mtype == 'SSR obt/clk':
            ssr.sdat = getbitu(payload, pos, 1)
            pos += 1  # satellite ref datum
        ssr.iod = getbitu(payload, pos, 4)
        pos += 4  # iod ssr
        ssr.pid = getbitu(payload, pos, 16)
        pos += 16  # ssr provider id
        ssr.sid = getbitu(payload, pos, 4)
        pos += 4  # ssr solution id
        bw = 6  # bit width changes according to satellite system
        if satsys == 'J':
            bw = 4
        ssr.nsat = getbitu(payload, pos, bw)
        pos += bw  # number of satellites
        self.pos = pos  # update pos
        self.ssr = ssr  # update ssr

    def ssr_decode_orbit(self):  # decode SSR orbit correction
        payload = self.payload
        pos = self.pos
        strsat = ''
        for i in range(self.ssr.nsat):
            bw = 6  # bit width changes according to satellite system
            if self.satsys == 'J':
                bw = 4
            if self.satsys == 'R':
                bw = 5
            satid = getbitu(payload, pos, bw)
            pos += bw  # satellite ID
            iode = getbitu(payload, pos, 8)
            pos += 8  # IODE
            drad = getbits(payload, pos, 22)
            pos += 22  # delta radial
            dalng = getbits(payload, pos, 20)
            pos += 20  # delta along track
            dcrs = getbits(payload, pos, 20)
            pos += 20  # delta cross track
            ddrad = getbits(payload, pos, 21)
            pos += 21  # delta radial
            ddalng = getbits(payload, pos, 19)
            pos += 19  # delta along track
            ddcrs = getbits(payload, pos, 19)
            pos += 19  # delta cross track
            strsat += f"{self.satsys}{satid:02} "
        self.string = f"{strsat}(nsat={self.ssr.nsat} iod={self.ssr.iod}" + \
                      f"{' cont.' if self.ssr.mmi else ''})"

    def ssr_decode_clock(self):  # decode SSR clock correction
        payload = self.payload
        pos = self.pos
        strsat = ''
        for i in range(self.ssr.nsat):
            bw = 6  # bit width changes according to satellite system
            if self.satsys == 'J':
                bw = 4
            if self.satsys == 'R':
                bw = 5
            satid = getbitu(payload, pos, bw)
            pos += bw  # satellite ID
            dc0 = getbits(payload, pos, 22)
            pos += 22  # delta clock c0
            dc1 = getbits(payload, pos, 21)
            pos += 21  # delta clock c1
            dc2 = getbits(payload, pos, 27)
            pos += 27  # delta clock c2
            strsat += f"{self.satsys}{satid:02} "
        self.string = f"{strsat}(nsat={self.ssr.nsat} iod={self.ssr.iod}" + \
                      f"{' cont.' if self.ssr.mmi else ''})"

    def ssr_decode_code_bias(self):  # decode SSR code bias
        payload = self.payload
        pos = self.pos
        strsat = ''
        for i in range(self.ssr.nsat):
            bw = 6  # bit width changes according to satellite system
            if self.satsys == 'J':
                bw = 4
            if self.satsys == 'R':
                bw = 5
            satid = getbitu(payload, pos, bw)
            pos += bw  # satellite ID
            ncb = getbitu(payload, pos, 5)
            pos += 5  # code bias number
            strsat += f"{self.satsys}{satid:02} "
            for j in range(ncb):
                stmi = getbitu(payload, pos, 5)
                pos += 5  # signal & tracking mode indicator
                cb = getbits(payload, pos, 14)
                pos += 14  # code bias
                #if self.satsys == 'J' and stmi == 0: strsat += 'L1C/A '
                #if self.satsys == 'J' and stmi == 1: strsat += 'L1C(D) '
                #if self.satsys == 'J' and stmi == 2: strsat += 'L1C(P) '
                #if self.satsys == 'J' and stmi == 3: strsat += 'L2C(M) '
                #if self.satsys == 'J' and stmi == 4: strsat += 'L2C(L) '
                #if self.satsys == 'J' and stmi == 5: strsat += 'L2C(L+M) '
                #if self.satsys == 'J' and stmi == 6: strsat += 'L5I '
                #if self.satsys == 'J' and stmi == 7: strsat += 'L5Q '
                #if self.satsys == 'J' and stmi == 8: strsat += 'L5I+Q '
        self.string = f"{strsat}(nsat={self.ssr.nsat} iod={self.ssr.iod}" + \
                      f"{' cont.' if self.ssr.mmi else ''})"

    def ssr_decode_ura(self):  # decode SSR user range accuracy
        payload = self.payload
        pos = self.pos
        strsat = ''
        for i in range(self.ssr.nsat):
            bw = 6  # bit width changes according to satellite system
            if self.satsys == 'J':
                bw = 4
            if self.satsys == 'R':
                bw = 5
            satid = getbitu(payload, pos, bw)
            pos += bw  # satellite ID
            ura = getbits(payload, pos, 6)
            pos += 6  # user range accuracy
            strsat += f"{self.satsys}{satid:02} "
        self.string = f"{strsat}(nsat={self.ssr.nsat} iod={self.ssr.iod}" + \
                      f"{' cont.' if self.ssr.mmi else ''})"

    def ssr_decode_hr_clock(self):  # decode SSR high rate clock
        payload = self.payload
        pos = self.pos
        strsat = ''
        for i in range(self.ssr.nsat):
            bw = 6  # bit width changes according to satellite system
            if self.satsys == 'J':
                bw = 4
            if self.satsys == 'R':
                bw = 5
            satid = getbitu(payload, pos, bw)
            pos += bw  # satellite ID
            hrc = getbits(payload, pos, 22)
            pos += 22  # high rate clock
            strsat += f"{self.satsys}{satid:02} "
        self.string = f"{strsat}(nsat={self.ssr.nsat} iod={self.ssr.iod}" + \
                      f"{' cont.' if self.ssr.mmi else ''})"

    def decode_cssr(self):  # decode CSSR
        payload = self.payload
        pos = self.pos
        subtype = getbitu(payload, pos, 4)
        pos += 4
        self.mtype += f' ST{subtype}'
        if subtype == 1:  # mask information
            epoch = getbitu(payload, pos, 20)
            pos += 20
            self.string += f' epoch={epoch}'
        elif subtype == 10:  # service information
            pass
        else:
            hepoch = getbitu(payload, pos, 12)
            pos += 12
            self.string += f' hepoch={hepoch}'
        interval = getbitu(payload, pos, 4)
        pos += 4  # update interval
        mmi = getbitu(payload, pos, 1)
        pos += 1  # multiple message
        iod = getbitu(payload, pos, 4)
        pos += 4  # issue of data
        self.string += f' iod={iod}'

    def decode_pos(self):  # decode antenna position
        payload = self.payload
        pos = self.pos
        ahgt = 0.  # antenna height for RTCM 1006
        stid = getbitu(payload, pos, 12)
        pos += 12
        itrf = getbitu(payload, pos, 6)
        pos += 6 + 4
        px = getbits38(payload, pos) * 1e-4
        pos += 38 + 2
        py = getbits38(payload, pos) * 1e-4
        pos += 38 + 2
        pz = getbits38(payload, pos) * 1e-4
        pos += 38
        if self.mnum == 1006:
            ahgt = getbitu(payload, pos, 16) * 1e-4
        lat, lon, height = ecef2llh(px, py, pz)
        string = f'{lat:.7f} {lon:.7f} {height:.3f}'
        if ahgt != 0:
            string += f' (ant {ahgt:.3f})'
        self.string = string  # update string

    def decode_ant_info(self):  # decode antenna and receiver info
        payload = self.payload
        pos = self.pos
        str_ant = ''
        str_ser = ''
        str_rcv = ''
        str_ver = ''
        str_rsn = ''
        stid = getbitu(payload, pos, 12)
        pos += 12
        l = getbitu(payload, pos, 8)
        pos += 8
        for i in range(l):
            str_ant += chr(getbitu(payload, pos, 8))
            pos += 8
        ant_setup = getbitu(payload, pos, 8)
        pos += 8
        if self.mnum == 1008 or self.mnum == 1033:
            l = getbitu(payload, pos, 8)
            pos += 8
            if 31 < l:
                l = 31
            for i in range(l):
                str_ser += chr(getbitu(payload, pos, 8))
                pos += 8
        if self.mnum == 1033:
            l = getbitu(payload, pos, 8)
            pos += 8
            if 31 < l:
                l = 31
            for i in range(l):
                str_rcv += chr(getbitu(payload, pos, 8))
                pos += 8
            l = getbitu(payload, pos, 8)
            pos += 8
            if 31 < l:
                l = 31
            for i in range(l):
                str_ver += chr(getbitu(payload, pos, 8))
                pos += 8
            l = getbitu(payload, pos, 8)
            pos += 8
            if 31 < l:
                l = 31
            for i in range(l):
                str_rsn += chr(getbitu(payload, pos, 8))
                pos += 8
        string = f'{stid} "{str_ant}" {ant_setup}'
        if str_ser != '':
            string += f' s/n {str_ser}'
        if str_rcv != '':
            string += f' rcv "{str_rcv}"'
        if str_ver != '':
            string += f' ver {str_ver}'
        if str_rsn != '':
            string += f' s/n {str_rsn}'
        self.string = string  # update string

    def decode_ephemerides(self):
        payload = self.payload
        pos = self.pos
        mtype = self.mtype
        satsys = self.satsys
        strsat = ''
        svh = 0xff
        postop = pos
        if satsys == 'G':  # type 1019 GPS ephemerides
            svid = getbitu(payload, pos, 6)
            pos += 6
            pos += 10 + 4 + 2 + 14 + 8 + 16 + 8 + 16 + 22 + 10 + 16 + 16 + 32 + \
                16 + 32 + 16 + 32 + 16 + 16 + 32 + 16 + 32 + 16 + 32 + 24 + 8
            svh = getbitu(payload, pos, 6)
            pos += 6
            pos += 1 + 1
        elif satsys == 'R':
            svid = getbitu(payload, pos, 6)
            pos += 6
            pos += 5 + 2 + 2 + 5 + 6 + 1 + 1 + 1 + 7 + 24 + 27 + 5 + \
                24 + 27 + 5 + 24 + 27 + 5 + 1 + 11 + 3 + 22 + 5 + 5
        elif satsys == 'I':
            svid = getbitu(payload, pos, 6)
            pos += 6
            pos += 10 + 22 + 16 + 8 + 4 + 16 + 8 + 22 + 8 + 10
            svh = getbitu(payload, pos, 2)
            pos += 2
            pos += 15 + 15 + 15 + 15 + 15 + 15 + 14 + 32 + 16 + 32 + 32 + 32 + 32 + 22 + 32
        elif satsys == 'J':
            svid = getbitu(payload, pos, 4)
            pos += 4
            pos += 16 + 8 + 16 + 22 + 8 + 16 + 16 + 32 + 16 + 32 + 16 + \
                32 + 16 + 16 + 32 + 16 + 32 + 16 + 32 + 24 + 14 + 2 + 10 + 4
            svh = getbitu(payload, pos, 6)
            pos += 6
            pos += 8 + 10 + 1
        elif mtype == 'F/NAV':  # type 1045 Galileo ephemerides
            svid = getbitu(payload, pos, 6)
            pos += 6
            pos += 12 + 10 + 8 + 14 + 14 + 6 + 21 + 31 + 16 + 16 + 32 + 16 + 32 + \
                16 + 32 + 14 + 16 + 32 + 16 + 32 + 16 + 32 + 24 + 10 + 2 + 1 + 7
        elif mtype == 'I/NAV':
            svid = getbitu(payload, pos, 6)
            pos += 6
            pos += 12 + 10 + 8 + 14 + 14 + 6 + 21 + 31 + 16 + 16 + 32 + 16 + 32 + 16 + \
                32 + 14 + 16 + 32 + 16 + 32 + 16 + 32 + 24 + 10 + 10 + 2 + 1 + 2 + 1
        elif satsys == 'C':
            svid = getbitu(payload, pos, 6)
            pos += 6
            pos += 13 + 4 + 14 + 5 + 17 + 11 + 22 + 24 + 5 + 18 + 16 + 32 + 18 + \
                32 + 18 + 32 + 17 + 18 + 32 + 18 + 32 + 18 + 32 + 24 + 10 + 10
            svh = getbitu(payload, pos, 1)
            pos += 1
        #streph = ''
        #leneph = pos - postop
        # while 0 < leneph:
        #    lenrd = 8 if 8<= leneph else leneph
        #    streph += '{:02x}'.format (getbitu (payload, postop, lenrd))
        #    postop += lenrd
        #    leneph -= lenrd
        string = f"{satsys}{svid:02d}"
        if svh != 0xff:
            string += f' svh={svh:02x}'
        self.string = string  # update string

    def decode_msm(self):  # decode MSM message
        payload = self.payload
        pos = self.pos
        satsys = self.satsys
        stid = getbitu(payload, pos, 12)
        pos += 12
        if satsys == 'R':
            dow = getbitu(payload, pos, 3)
            pos += 3
            tod = getbitu(payload, pos, 27) // 1000
            pos += 27
        elif satsys == 'C':
            tow = getbitu(payload, pos, 30) // 1000
            pos += 30
            tow += 14  # BDT -> GPST
        else:
            tow = getbitu(payload, pos, 30) // 1000
            pos += 30
        sync = getbitu(payload, pos, 1)
        pos += 1
        iod = getbitu(payload, pos, 3)
        pos += 3
        time_s = getbitu(payload, pos, 7)
        pos += 7
        clk_s = getbitu(payload, pos, 2)
        pos += 2
        cls_e = getbitu(payload, pos, 2)
        pos += 2
        smth = getbitu(payload, pos, 1)
        pos += 1
        tint_s = getbitu(payload, pos, 3)
        pos += 3
        sat_mask = [0 for i in range(64)]
        n_sat_mask = 0
        for i in range(64):
            mask = getbitu(payload, pos, 1)
            pos += 1
            if mask:
                sat_mask[n_sat_mask] = i
                n_sat_mask += 1
        sig_mask = [0 for i in range(32)]
        n_sig_mask = 0
        for i in range(32):
            mask = getbitu(payload, pos, 1)
            pos += 1
            if mask:
                sig_mask[n_sig_mask] = i
                n_sig_mask += 1
        cell_mask = [0 for i in range(n_sat_mask * n_sig_mask)]
        for i in range(n_sat_mask * n_sig_mask):
            cell_mask[i] = getbitu(payload, pos, 1)
            pos += 1
        for i in range(n_sat_mask):  # range
            rng = getbitu(payload, pos, 8)
            pos += 8
        for i in range(n_sat_mask):
            rng_m = getbitu(payload, pos, 10)
            pos += 10
        for i in range(n_sat_mask * n_sig_mask):  # pseudorange
            if not cell_mask[i]:
                continue
            prv = getbitu(payload, pos, 15)
            pos += 15
        lock = []
        # for i in range (n_sat_mask * n_sig_mask): # lock time
        #    if not cell_mask[i]: continue
        #    lock[i] = getbitu (payload, pos, 4); pos += 4
        #half = []
        # for i in range (n_sat_mask * n_sig_mask): # half-cycle ambiguity
        #    if not cell_mask[i]: continue
        #    half[i] = getbitu (payload, pos, 1); pos += 1
        #cnr = []
        # for i in range (n_sat_mask * n_sig_mask): # cnr
        #    if not cell_mask[i]: continue
        #    cnr[i] = getbitu (payload, pos, 7); pos += 6
        string = ''
        for i in range(n_sat_mask):
            string += f'{self.satsys}{sat_mask[i]+1:02} '
        self.string = string  # update string


if __name__ == '__main__':
    rtcm = rtcm_t()
    while rtcm.receive():
        rtcm.parse_head()
        if rtcm.mtype == 'CSSR':
            rtcm.decode_cssr()
        elif 'SSR' in rtcm.mtype:
            rtcm.ssr_head_decode()
            if rtcm.mtype == 'SSR orbit':
                rtcm.ssr_decode_orbit()
            elif rtcm.mtype == 'SSR clock':
                rtcm.ssr_decode_clock()
            elif rtcm.mtype == 'SSR code bias':
                rtcm.ssr_decode_code_bias()
            elif rtcm.mtype == 'SSR URA':
                rtcm.ssr_decode_ura()
            elif rtcm.mtype == 'SSR hr clock':
                rtcm.ssr_decode_hr_clock()
        elif rtcm.mtype == 'Position':
            rtcm.decode_pos()
        elif rtcm.mtype == 'Ant/Rcv info':
            rtcm.decode_ant_info()
        elif 'NAV' in rtcm.mtype:
            rtcm.decode_ephemerides()
        elif rtcm.mtype in {'MSM4', 'MSM7'}:
            rtcm.decode_msm()
        elif rtcm.mtype == 'CodePhase bias':
            pass
        else:
            raise Exception(f'unknown message type: {rtcm.mtype}')
        try:
            print(f"RTCM {rtcm.mnum} {rtcm.satsys:1} {rtcm.mtype:14}"
                  f"{rtcm.string}")
            sys.stdout.flush()
        except BrokenPipeError:
            sys.exit()
# EOF
