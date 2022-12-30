#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# librtcm.py: library for RTCM message processing
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022 Satoshi Takahashi
#
# Released under BSD 2-clause license.

import sys
import ecef2llh
import libqzsl6tool
import libcolor

class Rtcm:
    "RTCM message process class"
    rtcm_buf = b''
    t_level = 0  # trace level

    def receive_rtcm_msg(self):
        BUFMAX = 1000  # maximum length of buffering RTCM message
        BUFADD =   20  # length of buffering additional RTCM message
        try:
            ok = False
            while not ok:
                if BUFMAX < len(self.rtcm_buf):
                    print("RTCM buffer exhausted", file=sys.stderr)
                    return False
                b = sys.stdin.buffer.read(BUFADD)
                if not b:
                    return False
                self.rtcm_buf += b
                len_rtcm_buf = len(self.rtcm_buf)
                pos = 0
                found_sync = False
                while pos != len_rtcm_buf and not found_sync:
                    if self.rtcm_buf[pos:pos+1] == b'\xd3':
                        found_sync = True
                    else:
                        pos += 1
                if not found_sync:
                    self.rtcm_buf = b''
                    continue
                if len_rtcm_buf < pos + 3:  # cannot read message length
                    self.rtcm_buf = self.rtcm_buf[pos:]
                    continue
                bl = self.rtcm_buf[pos+1:pos+3]  # possible message length
                mlen = libqzsl6tool.getbitu(bl, 6, 10)
                if len_rtcm_buf < pos + 3 + mlen + 3:  # cannot read message
                    self.rtcm_buf = self.rtcm_buf[pos:]
                    continue
                bp = self.rtcm_buf[pos+3:pos+3+mlen]  # possible payload
                bc = self.rtcm_buf[pos+3+mlen:pos+3+mlen+3]  # possible CRC
                frame = b'\xd3' + bl + bp
                if bc == libqzsl6tool.rtk_crc24q(frame, len(frame)):
                    ok = True
                    self.rtcm_buf = self.rtcm_buf[pos+3+mlen+3:]
                else:  # CRC error
                    print("RTCM CRC error", file=sys.stderr)
                    self.rtcm_buf = self.rtcm_buf[pos + 1:]
                    continue
        except KeyboardInterrupt:
            print("User break - terminated", file=sys.stderr)
            return False
        self.payload = bp
        self.mlen = mlen
        self.string = ''
        return True

    def msgnum2satsys(self, msgnum=0):  # message number to satellite system
        satsys = ''
        if msgnum == 0:
            msgnum = self.msgnum
        if msgnum in {1001, 1002, 1003, 1004, 1019, 1071, 1072, 1073, 1074,
                    1075, 1076, 1077, 1057, 1058, 1059, 1060, 1061, 1062,
                    1230, 11}:
            satsys = 'G'
        if msgnum in {1009, 1010, 1011, 1012, 1020, 1081, 1081, 1082, 1083,
                    1084, 1085, 1086, 1087, 1063, 1064, 1065, 1066, 1067,
                    1068}:
            satsys = 'R'
        if msgnum in {1045, 1046, 1091, 1092, 1093, 1094, 1095, 1096, 1097,
                    1240, 1241, 1242, 1243, 1244, 1245, 12}:
            satsys = 'E'
            return satsys
        if msgnum in {1044, 1111, 1112, 1113, 1114, 1115, 1116, 1117, 1246,
                    1247, 1248, 1249, 1250, 1251, 13}:
            satsys = 'J'
        if msgnum in {1042, 63, 1121, 1122, 1123, 1124, 1125, 1126, 1127, 1258,
                    1259, 1260, 1261, 1262, 1263, 14}:
            satsys = 'C'
        if msgnum in {1101, 1102, 1103, 1104, 1105, 1106, 1107}:
            satsys = 'S'
        if msgnum in {1041, 1131, 1132, 1133, 1134, 1135, 1136, 1137}:
            satsys = 'I'
        return satsys

    def msgnum2mtype(self, msgnum=0):  # message number to message type
        mtype = ''
        if msgnum == 0:
            msgnum = self.msgnum
        if msgnum in {1001, 1009}:
            mtype = 'Obs Comp L1'
        if msgnum in {1002, 1010}:
            mtype = 'Obs Full L1'
        if msgnum in {1003, 1011}:
            mtype = 'Obs Comp L1L2'
        if msgnum in {1004, 1012}:
            mtype = 'Obs Full L1L2'
        if msgnum in {1019, 1020, 1044, 1042, 1041, 63}:
            mtype = 'NAV'
        if msgnum == 1230:
            mtype = 'CodePhase bias'
        if msgnum == 1045:
            mtype = 'F/NAV'
        if msgnum == 1046:
            mtype = 'I/NAV'
        if (1071 <= msgnum and msgnum <= 1097) or \
           (1101 <= msgnum and msgnum <= 1137):
            mtype = f'MSM{msgnum % 10}'
        if msgnum in {1057, 1063, 1240, 1246, 1258}:
            mtype = 'SSR orbit'
        if msgnum in {1058, 1064, 1241, 1247, 1259}:
            mtype = 'SSR clock'
        if msgnum in {1059, 1065, 1242, 1248, 1260}:
            mtype = 'SSR code bias'
        if msgnum in {1060, 1066, 1243, 1249, 1261}:
            mtype = 'SSR obt/clk'
        if msgnum in {1061, 1067, 1244, 1250, 1262}:
            mtype = 'SSR URA'
        if msgnum in {1062, 1068, 1245, 1251, 1263}:
            mtype = 'SSR hr clock'
        if msgnum in {11, 12, 13, 14}:
            mtype = 'SSR phase bias'
        if msgnum in {1007, 1008, 1033}:
            mtype = 'Ant/Rcv info'
        if msgnum in {1005, 1006}:
            mtype = 'Position'
        if msgnum == 4073:
            mtype = 'CSSR'
        return mtype

    def ssr_head_decode(self):  # ssr
        payload = self.payload
        pos = self.pos
        mtype = self.mtype
        satsys = self.satsys
        bw = 20 if satsys != 'R' else 17
        # bit width changes according to satellite system
        self.ssr_epoch = libqzsl6tool.getbitu(payload, pos, bw)  # ephch time
        pos += bw
        self.ssr_ntvl = libqzsl6tool.getbitu(payload, pos, 4)  # ssr update interval
        pos += 4
        self.ssr_mmi = libqzsl6tool.getbitu(payload, pos, 1)  # multiple message indicator
        pos += 1
        if mtype == 'SSR orbit' or mtype == 'SSR obt/clk':
            self.ssr_sdat = libqzsl6tool.getbitu(payload, pos, 1)  # satellite ref datum
            pos += 1
        self.ssr_iod = libqzsl6tool.getbitu(payload, pos, 4)  # iod ssr
        pos += 4
        self.ssr_pid = libqzsl6tool.getbitu(payload, pos, 16)  # ssr provider id
        pos += 16
        self.ssr_sid = libqzsl6tool.getbitu(payload, pos, 4)  # ssr solution id
        pos += 4
        bw = 6 if satsys != 'J' else 4
        # bit width changes according to satellite system
        self.ssr_nsat = libqzsl6tool.getbitu(payload, pos, bw)  # number of satellites
        pos += bw
        self.pos = pos  # update pos

    def ssr_decode_orbit(self):  # decode SSR orbit correction
        payload = self.payload
        pos = self.pos
        strsat = ''
        for i in range(self.ssr_nsat):
            if self.satsys == 'J':
                bw = 4
            elif self.satsys == 'R':
                bw = 5
            else:
                bw = 6
            # bit width changes according to satellite system
            satid = libqzsl6tool.getbitu(payload, pos, bw)  # satellite ID
            pos += bw
            iode = libqzsl6tool.getbitu(payload, pos, 8)  # IODE
            pos += 8
            drad = libqzsl6tool.getbits(payload, pos, 22)  # delta radial
            pos += 22
            dalng = libqzsl6tool.getbits(payload, pos, 20)  # delta along track
            pos += 20
            dcrs = libqzsl6tool.getbits(payload, pos, 20)  # delta cross track
            pos += 20
            ddrad = libqzsl6tool.getbits(payload, pos, 21)  # delta radial
            pos += 21
            ddalng = libqzsl6tool.getbits(payload, pos, 19)  # delta along track
            pos += 19
            ddcrs = libqzsl6tool.getbits(payload, pos, 19)  # delta cross track
            pos += 19
            strsat += f"{self.satsys}{satid:02} "
        self.string = f"{strsat}(nsat={self.ssr_nsat} iod={self.ssr_iod}" + \
                      f"{' cont.' if self.ssr_mmi else ''})"

    def ssr_decode_clock(self):  # decode SSR clock correction
        payload = self.payload
        pos = self.pos
        strsat = ''
        for i in range(self.ssr_nsat):
            if self.satsys == 'J':
                bw = 4
            elif self.satsys == 'R':
                bw = 5
            else:
                bw = 6
            # bit width changes according to satellite system
            satid = libqzsl6tool.getbitu(payload, pos, bw)  # satellite ID
            pos += bw
            dc0 = libqzsl6tool.getbits(payload, pos, 22)  # delta clock c0
            pos += 22
            dc1 = libqzsl6tool.getbits(payload, pos, 21)  # delta clock c1
            pos += 21
            dc2 = libqzsl6tool.getbits(payload, pos, 27)  # delta clock c2
            pos += 27
            strsat += f"{self.satsys}{satid:02} "
        self.string = f"{strsat}(nsat={self.ssr_nsat} iod={self.ssr_iod}" + \
                      f"{' cont.' if self.ssr_mmi else ''})"

    def ssr_decode_code_bias(self):  # decode SSR code bias
        payload = self.payload
        pos = self.pos
        strsat = ''
        for i in range(self.ssr_nsat):
            if self.satsys == 'J':
                bw = 4
            elif self.satsys == 'R':
                bw = 5
            else:
                bw = 6
            # bit width changes according to satellite system
            satid = libqzsl6tool.getbitu(payload, pos, bw)  # satellite ID
            pos += bw
            ncb = libqzsl6tool.getbitu(payload, pos, 5)  # code bias number
            pos += 5
            strsat += f"{self.satsys}{satid:02} "
            for j in range(ncb):
                stmi = libqzsl6tool.getbitu(payload, pos, 5)
                # signal & tracking mode indicator
                pos += 5
                cb = libqzsl6tool.getbits(payload, pos, 14)  # code bias
                pos += 14
        self.string = f"{strsat}(nsat={self.ssr_nsat} iod={self.ssr_iod}" + \
                      f"{' cont.' if self.ssr_mmi else ''})"

    def ssr_decode_ura(self):  # decode SSR user range accuracy
        payload = self.payload
        pos = self.pos
        strsat = ''
        for i in range(self.ssr_nsat):
            if self.satsys == 'J':
                bw = 4
            elif self.satsys == 'R':
                bw = 5
            else:
                bw = 6
            # bit width changes according to satellite system
            satid = libqzsl6tool.getbitu(payload, pos, bw)  # satellite ID
            pos += bw
            ura = libqzsl6tool.getbits(payload, pos, 6)  # user range accuracy
            pos += 6
            strsat += f"{self.satsys}{satid:02} "
        self.string = f"{strsat}(nsat={self.ssr_nsat} iod={self.ssr_iod}" + \
                      f"{' cont.' if self.ssr_mmi else ''})"

    def ssr_decode_hr_clock(self):  # decode SSR high rate clock
        payload = self.payload
        pos = self.pos
        strsat = ''
        for i in range(self.ssr_nsat):
            if self.satsys == 'J':
                bw = 4
            elif self.satsys == 'R':
                bw = 5
            else:
                bw = 6
            # bit width changes according to satellite system
            satid = libqzsl6tool.getbitu(payload, pos, bw)  # satellite ID
            pos += bw
            hrc = libqzsl6tool.getbits(payload, pos, 22)  # high rate clock
            pos += 22
            strsat += f"{self.satsys}{satid:02} "
        self.string = f"{strsat}(nsat={self.ssr_nsat} iod={self.ssr_iod}" + \
                      f"{' cont.' if self.ssr_mmi else ''})"

    def decode_cssr(self):  # decode CSSR
        payload = self.payload
        pos = self.pos
        subtype = libqzsl6tool.getbitu(payload, pos, 4)
        pos += 4
        self.mtype += f' ST{subtype}'
        if subtype == 1:  # mask information
            epoch = libqzsl6tool.getbitu(payload, pos, 20)
            pos += 20
            self.string += f' epoch={epoch}'
        elif subtype == 10:  # service information
            pass
        else:
            hepoch = libqzsl6tool.getbitu(payload, pos, 12)
            pos += 12
            self.string += f' hepoch={hepoch}'
        interval = libqzsl6tool.getbitu(payload, pos, 4)  # update interval
        pos += 4
        mmi = libqzsl6tool.getbitu(payload, pos, 1)  # multiple message
        pos += 1
        iod = libqzsl6tool.getbitu(payload, pos, 4)  # issue of data
        pos += 4
        self.string += f' iod={iod}'

    def decode_antenna_position(self):  # decode antenna position
        payload = self.payload
        pos = self.pos
        stid = libqzsl6tool.getbitu(payload, pos, 12)
        pos += 12
        itrf = libqzsl6tool.getbitu(payload, pos, 6)
        pos += 6 + 4
        px = libqzsl6tool.getbits38(payload, pos) * 1e-4
        pos += 38 + 2
        py = libqzsl6tool.getbits38(payload, pos) * 1e-4
        pos += 38 + 2
        pz = libqzsl6tool.getbits38(payload, pos) * 1e-4
        pos += 38
        if self.msgnum == 1006:  # antenna height for RTCM 1006
            ahgt = libqzsl6tool.getbitu(payload, pos, 16) * 1e-4
            if ahgt != 0:
                string += f' (ant {ahgt:.3f})'
        lat, lon, height = ecef2llh.ecef2llh(px, py, pz)
        string = f'{lat:.7f} {lon:.7f} {height:.3f}'
        self.string = string  # update string

    def decode_ant_info(self):  # decode antenna and receiver info
        payload = self.payload
        pos = self.pos
        str_ant = ''
        str_ser = ''
        str_rcv = ''
        str_ver = ''
        str_rsn = ''
        stid = libqzsl6tool.getbitu(payload, pos, 12)
        pos += 12
        l = libqzsl6tool.getbitu(payload, pos, 8)
        pos += 8
        for i in range(l):
            str_ant += chr(libqzsl6tool.getbitu(payload, pos, 8))
            pos += 8
        ant_setup = libqzsl6tool.getbitu(payload, pos, 8)
        pos += 8
        if self.msgnum == 1008 or self.msgnum == 1033:
            l = libqzsl6tool.getbitu(payload, pos, 8)
            pos += 8
            if 31 < l:
                l = 31
            for i in range(l):
                str_ser += chr(libqzsl6tool.getbitu(payload, pos, 8))
                pos += 8
        if self.msgnum == 1033:
            l = libqzsl6tool.getbitu(payload, pos, 8)
            pos += 8
            if 31 < l:
                l = 31
            for i in range(l):
                str_rcv += chr(libqzsl6tool.getbitu(payload, pos, 8))
                pos += 8
            l = libqzsl6tool.getbitu(payload, pos, 8)
            pos += 8
            if 31 < l:
                l = 31
            for i in range(l):
                str_ver += chr(libqzsl6tool.getbitu(payload, pos, 8))
                pos += 8
            l = libqzsl6tool.getbitu(payload, pos, 8)
            pos += 8
            if 31 < l:
                l = 31
            for i in range(l):
                str_rsn += chr(libqzsl6tool.getbitu(payload, pos, 8))
                pos += 8
        string = ''
        if stid != 0:
            string += f'{stid} '
        string += f'{str_ant}'
        if ant_setup != 0:
            string += f' {ant_setup}'
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
        if satsys == 'G':  # GPS ephemerides
            svid = libqzsl6tool.getbitu(payload, pos, 6)
            pos += 6
            pos += 10 + 4 + 2 + 14 + 8 + 16 + 8 + 16 + 22 + 10 + 16 + 16 + 32 + \
                16 + 32 + 16 + 32 + 16 + 16 + 32 + 16 + 32 + 16 + 32 + 24 + 8
            svh = libqzsl6tool.getbitu(payload, pos, 6)
        elif satsys == 'R':  # GLONASS ephemerides
            svid = libqzsl6tool.getbitu(payload, pos, 6)
            pos += 6
        elif satsys == 'I':  # NavIC ephemerides
            svid = libqzsl6tool.getbitu(payload, pos, 6)
            pos += 6
            pos += 10 + 22 + 16 + 8 + 4 + 16 + 8 + 22 + 8 + 10
            svh = libqzsl6tool.getbitu(payload, pos, 2)
        elif satsys == 'J':  # QZSS ephemerides
            svid = libqzsl6tool.getbitu(payload, pos, 4)
            pos += 4
            pos += 16 + 8 + 16 + 22 + 8 + 16 + 16 + 32 + 16 + 32 + 16 + \
                32 + 16 + 16 + 32 + 16 + 32 + 16 + 32 + 24 + 14 + 2 + 10 + 4
            svh = libqzsl6tool.getbitu(payload, pos, 6)
        elif mtype == 'F/NAV':  # Galileo F/NAV ephemerides
            svid = libqzsl6tool.getbitu(payload, pos, 6)
            pos += 6
        elif mtype == 'I/NAV':  # Galileo I/NAV ephemerides
            svid = libqzsl6tool.getbitu(payload, pos, 6)
            pos += 6
        elif satsys == 'C':  # BeiDou ephemerides
            svid = libqzsl6tool.getbitu(payload, pos, 6)
            pos += 6
            pos += 13 + 4 + 14 + 5 + 17 + 11 + 22 + 24 + 5 + 18 + 16 + 32 + 18 + \
                32 + 18 + 32 + 17 + 18 + 32 + 18 + 32 + 18 + 32 + 24 + 10 + 10
            svh = libqzsl6tool.getbitu(payload, pos, 1)
        string = f"{satsys}{svid:02d}"
        if svh != 0xff:
            string += f' svh={svh:02x}'
        self.string = string  # update string

    def decode_msm(self):  # decode MSM message
        payload = self.payload
        pos = self.pos
        satsys = self.satsys
        stid = libqzsl6tool.getbitu(payload, pos, 12)
        pos += 12
        if satsys == 'R':
            dow = libqzsl6tool.getbitu(payload, pos, 3)
            pos += 3
            tod = libqzsl6tool.getbitu(payload, pos, 27) // 1000
            pos += 27
        elif satsys == 'C':
            tow = libqzsl6tool.getbitu(payload, pos, 30) // 1000
            pos += 30
            tow += 14  # BDT -> GPST
        else:
            tow = libqzsl6tool.getbitu(payload, pos, 30) // 1000
            pos += 30
        sync = libqzsl6tool.getbitu(payload, pos, 1)
        pos += 1
        iod = libqzsl6tool.getbitu(payload, pos, 3)
        pos += 3
        time_s = libqzsl6tool.getbitu(payload, pos, 7)
        pos += 7
        clk_s = libqzsl6tool.getbitu(payload, pos, 2)
        pos += 2
        cls_e = libqzsl6tool.getbitu(payload, pos, 2)
        pos += 2
        smth = libqzsl6tool.getbitu(payload, pos, 1)
        pos += 1
        tint_s = libqzsl6tool.getbitu(payload, pos, 3)
        pos += 3
        sat_mask = [0 for i in range(64)]
        n_sat_mask = 0
        for i in range(64):
            mask = libqzsl6tool.getbitu(payload, pos, 1)
            pos += 1
            if mask:
                sat_mask[n_sat_mask] = i
                n_sat_mask += 1
        sig_mask = [0 for i in range(32)]
        n_sig_mask = 0
        for i in range(32):
            mask = libqzsl6tool.getbitu(payload, pos, 1)
            pos += 1
            if mask:
                sig_mask[n_sig_mask] = i
                n_sig_mask += 1
        cell_mask = [0 for i in range(n_sat_mask * n_sig_mask)]
        for i in range(n_sat_mask * n_sig_mask):
            cell_mask[i] = libqzsl6tool.getbitu(payload, pos, 1)
            pos += 1
        for i in range(n_sat_mask):  # range
            rng = libqzsl6tool.getbitu(payload, pos, 8)
            pos += 8
        for i in range(n_sat_mask):
            rng_m = libqzsl6tool.getbitu(payload, pos, 10)
            pos += 10
        for i in range(n_sat_mask * n_sig_mask):  # pseudorange
            if not cell_mask[i]:
                continue
            prv = libqzsl6tool.getbitu(payload, pos, 15)
            pos += 15
        string = ''
        for i in range(n_sat_mask):
            string += f'{self.satsys}{sat_mask[i]+1:02} '
        self.string = string  # update string

    def decode_ssr(self, msgnum, payload):
        pos = self.pos
        if msgnum in {1057, 1059, 1061, 1062}:
            be = 20  # bit size of epoch and numsat for GPS
            bs = 6
        elif msgnum in {1246, 1248, 1250, 1251}:
            be = 20  # bit size of epoch and numsat for QZSS
            bs = 4
        elif msgnum in {1063, 1065, 1067, 1068}:
            be = 17  # bit size of epoch and numsat for GLONASS
            bs = 6
        else:
            self.trace(1, f"Unknown message number {msgnum}\n")
            return False
        epoch = payload[pos:pos + be].uint
        pos += be
        interval = payload[pos:pos + 4].uint
        pos += 4
        multind = payload[pos:pos + 1].uint
        pos += 1
        if msgnum in {1057, 1246, 1063}:
            satref = payload[pos:pos + 1].uint
            pos += 1
        iod = payload[pos:pos + 4].uint
        pos += 4
        provider = payload[pos:pos + 16].uint
        pos += 16
        solution = payload[pos:pos + 4].uint
        pos += 4
        numsat = payload[pos:pos + bs].uint
        pos += bs
        if msgnum == 1057:  # GPS orbit correction
            pos += 135 * numsat
        elif msgnum == 1059:  # GPS code bias
            for i in range(numsat):
                satid = payload[pos:pos + 6].uint
                pos += 6
                numcb = payload[pos:pos + 5].uint
                pos += 5
                pos += numcb * 19
        elif msgnum == 1061:  # GPS URA
            pos += 12 * numsat
        elif msgnum == 1062:  # GPS hr clock correction
            pos += 28 * numsat
        elif msgnum == 1246:  # QZSS orbit correction
            pos += 133 * numsat
        elif msgnum == 1248: # QZSS code bias
            for i in range(numsat):
                satid = payload[pos:pos + 4].uint
                pos += 4
                numcb = payload[pos:pos + 5].uint
                pos += 5
                pos += numcb * 19
        elif msgnum == 1250:  # QZSS URA
            pos += 10 * numsat
        elif msgnum == 1251:  # QZSS hr clock correction
            pos += 26 * numsat
        elif msgnum == 1063:  # GLONASS orbit correction
            pos += 134 * numsat
        elif msgnum == 1065:  # GLONASS code bias
            for i in range(numsat):
                satid = payload[pos:pos + 5].uint
                pos += 5
                numcb = payload[pos:pos + 5].uint
                pos += 5
                pos += numcb * 19
        elif msgnum == 1067:  # GLONASS URA
            pos += 11 * numsat
        elif msgnum == 1068:  # GLONASS hr clock correction
            pos += 27 * numsat
        else:
            self.trace(
                1, f"Warning: msgnum {msgnum} drop {len (payload)} bit:\n")
            self.trace(1, f"{payload.bin}\n")
            return False
        self.pos = pos
        self.numsat = numsat
        return True

    def decode_rtcm_msg(self):  # decode RTCM message
        # parse RTCM header
        self.msgnum = libqzsl6tool.getbitu(self.payload, 0, 12)  # message number
        self.pos = 12
        self.satsys = self.msgnum2satsys()
        self.mtype = self.msgnum2mtype()
        if self.mtype == 'CSSR':
            self.decode_cssr()
        elif 'SSR' in self.mtype:
            self.ssr_head_decode()
            if self.mtype == 'SSR orbit':
                self.ssr_decode_orbit()
            elif self.mtype == 'SSR clock':
                self.ssr_decode_clock()
            elif self.mtype == 'SSR code bias':
                self.ssr_decode_code_bias()
            elif self.mtype == 'SSR URA':
                self.ssr_decode_ura()
            elif self.mtype == 'SSR hr clock':
                self.ssr_decode_hr_clock()
        elif self.mtype == 'Position':
            self.decode_antenna_position()
        elif self.mtype == 'Ant/Rcv info':
            self.decode_ant_info()
        elif 'NAV' in self.mtype:
            self.decode_ephemerides()
        elif self.mtype in {'MSM4', 'MSM7'}:
            self.decode_msm()
        elif self.mtype == 'CodePhase bias':
            pass
        else:
            raise Exception(f'unknown message type: {self.msgnum} ({self.mtype})')
        try:
            msg_color = libcolor.Color()
            message = msg_color.fg('green') + f'RTCM {self.msgnum} '
            message += msg_color.fg('yellow')
            message += f'{self.satsys:1} {self.mtype:14}'
            message += msg_color.fg('default') + self.string
            print(message)
            sys.stdout.flush()
        except BrokenPipeError:
            sys.exit()

# EOF
