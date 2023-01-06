#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# librtcm.py: library for RTCM message processing
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022 Satoshi Takahashi
#
# Released under BSD 2-clause license.
#
# References:
# 1. Radio Technical Commission for Maritime Services (RTCM),
#    Differential GNSS (Global Navigation Satellite Systems) Services
#    - Version 3, RTCM Standard 10403.3, Apr. 24 2020.

import sys
import ecef2llh
import libcolor
import libcssr
import libqzsl6tool
try:
    import bitstring
except ModuleNotFoundError:
    print('''\
    QZS L6 Tool needs bitstring module.
    Please install this module such as \"pip install bitstring\".
    ''', file=sys.stderr)
    sys.exit(1)

class Rtcm(libcssr.Cssr):
    "RTCM message process class"
# public
    fp_msg = sys.stdout             # message output file pointer
    ansi_color = False              # ANSI escape sequences
    msg_color = libcolor.Color(fp_msg, ansi_color)
    fp_rtcm = None                  # file pointer for RTCM message output
# protected
    ssr_nsat = 0                    # number of satellites
# private
    readbuf = b''                   # read buffer, used as static variable
    payload = bitstring.BitArray()  # payload excluding head, length, and CRC
    string = ''                     # information string
    ssr_mmi = 0                     # multiple message indicator
    ssr_iod = 0                     # iod ssr

    def read_rtcm_msg(self):
        "returns true if success in receing RTCM message"
        BUFMAX = 1000  # maximum length of buffering RTCM message
        BUFADD =   20  # length of buffering additional RTCM message
        ok = False
        msg_color = libcolor.Color(sys.stderr, self.ansi_color)
        while not ok:
            if BUFMAX < len(self.readbuf):
                print("RTCM buffer exhausted", file=sys.stderr)
                return False
            try:
                b = sys.stdin.buffer.read(BUFADD)
            except KeyboardInterrupt:
                print(msg_color.fg('yellow') + \
                     "User break - terminated" + \
                     msg_color.fg('default'), file=sys.stderr)
                return False
            if not b:
                return False
            self.readbuf += b
            len_readbuf = len(self.readbuf)
            pos = 0
            found_sync = False
            while pos != len_readbuf and not found_sync:
                if self.readbuf[pos:pos+1] == b'\xd3':
                    found_sync = True
                else:
                    pos += 1
            if not found_sync:
                self.readbuf = b''
                continue
            if len_readbuf < pos + 3:  # cannot read message length
                self.readbuf = self.readbuf[pos:]
                continue
            bl = self.readbuf[pos+1:pos+3]  # possible message length
            mlen = int.from_bytes(bl, 'big') & 0x3ff
            if len_readbuf < pos + 3 + mlen + 3:  # cannot read message
                self.readbuf = self.readbuf[pos:]
                continue
            bp = self.readbuf[pos+3:pos+3+mlen]  # possible payload
            bc = self.readbuf[pos+3+mlen:pos+3+mlen+3]  # possible CRC
            frame = b'\xd3' + bl + bp
            if bc == libqzsl6tool.rtk_crc24q(frame, len(frame)):
                ok = True
                self.readbuf = self.readbuf[pos+3+mlen+3:]
            else:  # CRC error
                print(msg_color.fg('red') + \
                     "CRC error" + \
                     msg_color.fg('default'), file=sys.stderr)
                self.readbuf = self.readbuf[pos + 1:]
                continue
        self.payload = bitstring.BitArray(bp)
        self.string = ''
        return True

    def msgnum2satsys(self, msgnum):  # message number to satellite system
        satsys = ''
        if msgnum in {1001, 1002, 1003, 1004, 1019, 1071, 1072, 1073, 1074,
                    1075, 1076, 1077, 1057, 1058, 1059, 1060, 1061, 1062,
                    11}:
            satsys = 'G'
        if msgnum in {1009, 1010, 1011, 1012, 1020, 1081, 1081, 1082, 1083,
                    1084, 1085, 1086, 1087, 1063, 1064, 1065, 1066, 1067,
                    1068, 1230}:
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

    def msgnum2mtype(self, msgnum):  # message number to message type
        mtype = f'MT{msgnum:<4d}'
        if msgnum in {1001, 1009}:
            mtype = 'Obs L1'
        if msgnum in {1002, 1010}:
            mtype = 'Obs Full L1'
        if msgnum in {1003, 1011}:
            mtype = 'Obs L1L2'
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
        if (1071 <= msgnum and msgnum <= 1077) or \
           (1081 <= msgnum and msgnum <= 1087) or \
           (1091 <= msgnum and msgnum <= 1097) or \
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

    def ssr_head_decode(self, payload, satsys, mtype):
        "returns data size of SSR header"
        pos = 0
        bw = 20 if satsys != 'R' else 17
        # bit width changes according to satellite system
        ssr_epoch = payload[pos:pos+bw].uint  # epoch time
        pos += bw
        ssr_interval = payload[pos:pos+4].uint  # ssr update interval
        pos += 4
        self.ssr_mmi = payload[pos:pos+1].uint  # multiple message indicator
        pos += 1
        if mtype == 'SSR orbit' or mtype == 'SSR obt/clk':
            ssr_sdat = payload[pos:pos+1].uint  # satellite ref datum
            pos += 1
        self.ssr_iod = payload[pos:pos+4].uint  # iod ssr
        pos += 4
        ssr_pid = payload[pos:pos+16].uint  # ssr provider id
        pos += 16
        ssr_sid = payload[pos:pos+4].uint  # ssr solution id
        pos += 4
        bw = 6 if satsys != 'J' else 4
        # bit width changes according to satellite system
        self.ssr_nsat = payload[pos:pos+bw].uint  # number of satellites
        pos += bw
        return pos

    def ssr_decode_orbit(self, payload, satsys):  # decode SSR orbit correction
        "returns size of data"
        pos = 0
        strsat = ''
        for i in range(self.ssr_nsat):
            if satsys == 'J':
                bw = 4
            elif satsys == 'R':
                bw = 5
            else:
                bw = 6
            # bit width changes according to satellite system
            satid = payload[pos:pos+bw].uint  # satellite ID
            pos += bw
            iode = payload[pos:pos+8].uint    # IODE
            pos += 8
            drad = payload[pos:pos+22].int    # delta radial
            pos += 22
            dalng = payload[pos:pos+20].int   # delta along track
            pos += 20
            dcrs = payload[pos:pos+20].int    # delta cross track
            pos += 20
            ddrad = payload[pos:pos+21].int   # delta^2 radial
            pos += 21
            ddalng = payload[pos:pos+19].int  # delta^2 along track
            pos += 19
            ddcrs = payload[pos:pos+19].int   # delta^2 cross track
            pos += 19
            strsat += f"{satsys}{satid:02} "
        self.string = f"{strsat}(nsat={self.ssr_nsat} iod={self.ssr_iod}" + \
                      f"{' cont.' if self.ssr_mmi else ''})"
        return pos

    def ssr_decode_clock(self, payload, satsys):  # decode SSR clock correction
        "returns size of data"
        pos = 0
        strsat = ''
        for i in range(self.ssr_nsat):
            if satsys == 'J':
                bw = 4
            elif satsys == 'R':
                bw = 5
            else:
                bw = 6
            # bit width changes according to satellite system
            satid = payload[pos:pos+bw].uint  # satellite ID
            pos += bw
            dc0 = payload[pos:pos+22].int  # delta clock c0
            pos += 22
            dc1 = payload[pos:pos+21].int  # delta clock c1
            pos += 21
            dc2 = payload[pos:pos+27].int  # delta clock c2
            pos += 27
            strsat += f"{satsys}{satid:02} "
        self.string = f"{strsat}(nsat={self.ssr_nsat} iod={self.ssr_iod}" + \
                      f"{' cont.' if self.ssr_mmi else ''})"
        return pos

    def ssr_decode_code_bias(self, payload, satsys):  # decode SSR code bias
        "returns size of data"
        pos = 0
        strsat = ''
        for i in range(self.ssr_nsat):
            if satsys == 'J':
                bw = 4
            elif satsys == 'R':
                bw = 5
            else:
                bw = 6
            # bit width changes according to satellite system
            satid = payload[pos:pos+bw].uint  # satellite ID
            pos += bw
            ncb = payload[pos:pos+5].uint  # code bias number
            pos += 5
            strsat += f"{satsys}{satid:02} "
            for j in range(ncb):
                stmi = payload[pos:pos+5].uint
                # signal & tracking mode indicator
                pos += 5
                cb = payload[pos:pos+14].int  # code bias
                pos += 14
        self.string = f"{strsat}(nsat={self.ssr_nsat} iod={self.ssr_iod}" + \
                      f"{' cont.' if self.ssr_mmi else ''})"
        return pos

    def ssr_decode_ura(self, payload, satsys):  # decode SSR user range accuracy
        "returns size of data"
        pos = 0
        strsat = ''
        for i in range(self.ssr_nsat):
            if satsys == 'J':
                bw = 4
            elif satsys == 'R':
                bw = 5
            else:
                bw = 6
            # bit width changes according to satellite system
            satid = payload[pos:pos+bw].uint  # satellite ID
            pos += bw
            ura = payload[pos:pos+6].uint  # user range accuracy
            pos += 6
            strsat += f"{satsys}{satid:02} "
        self.string = f"{strsat}(nsat={self.ssr_nsat} iod={self.ssr_iod}" + \
                      f"{' cont.' if self.ssr_mmi else ''})"
        return pos

    def ssr_decode_hr_clock(self, payload, satsys):  # decode SSR high rate clock
        "returns size of data"
        pos = 0
        strsat = ''
        for i in range(self.ssr_nsat):
            if satsys == 'J':
                bw = 4
            elif satsys == 'R':
                bw = 5
            else:
                bw = 6
            # bit width changes according to satellite system
            satid = payload[pos:pos+bw].uint  # satellite ID
            pos += bw
            hrc = payload[pos:pos+22].int  # high rate clock
            pos += 22
            strsat += f"{satsys}{satid:02} "
        self.string = f"{strsat}(nsat={self.ssr_nsat} iod={self.ssr_iod}" + \
                      f"{' cont.' if self.ssr_mmi else ''})"
        return pos

    def decode_cssr(self, payload):
        "returns size of data"
        pos = self.decode_cssr_head(payload)
        if pos == 0:
            return 0
        if self.subtype == 1:
            pos = self.decode_cssr_st1(payload, pos)
        elif self.subtype == 2:
            pos = self.decode_cssr_st2(payload, pos)
        elif self.subtype == 3:
            pos = self.decode_cssr_st3(payload, pos)
        elif self.subtype == 4:
            pos = self.decode_cssr_st4(payload, pos)
        elif self.subtype == 5:
            pos = self.decode_cssr_st5(payload, pos)
        elif self.subtype == 6:
            pos = self.decode_cssr_st6(payload, pos)
        elif self.subtype == 7:
            pos = self.decode_cssr_st7(payload, pos)
        elif self.subtype == 8:
            pos = self.decode_cssr_st8(payload, pos)
        elif self.subtype == 9:
            pos = self.decode_cssr_st9(payload, pos)
        elif self.subtype == 10:
            pos = self.decode_cssr_st10(payload, pos)
        elif self.subtype == 11:
            pos = self.decode_cssr_st11(payload, pos)
        elif self.subtype == 12:
            pos = self.decode_cssr_st12(payload, pos)
        else:
            raise Exception(f"Unknown CSSR subtype: {self.subtype}")
        self.string = f'ST{self.subtype:<2d}'
        if self.subtype == 1:
            self.string += f' epoch={self.epoch} iod={self.iod}'
        else:
            self.string += f' hepoch={self.hepoch} iod={self.iod}'
        return pos

    def decode_antenna_position(self, payload, msgnum):  # decode antenna position
        "returns size of data"
        pos = 0
        stid = payload[pos:pos+12].uint
        pos += 12
        itrf = payload[pos:pos+6].uint
        pos += 6 + 4
        px = payload[pos:pos+38].int * 1e-4
        pos += 38 + 2
        py = payload[pos:pos+38].int * 1e-4
        pos += 38 + 2
        pz = payload[pos:pos+38].int * 1e-4
        pos += 38
        if msgnum == 1006:  # antenna height for RTCM 1006
            ahgt = payload[pos:pos+16].uint * 1e-4
            if ahgt != 0:
                string += f' (ant {ahgt:.3f})'
        lat, lon, height = ecef2llh.ecef2llh(px, py, pz)
        string = f'{lat:.7f} {lon:.7f} {height:.3f}'
        self.string = string  # update string
        return pos

    def decode_ant_info(self, payload, msgnum):  # decode antenna and receiver info
        "returns size of data"
        pos = 0
        str_ant = ''
        str_ser = ''
        str_rcv = ''
        str_ver = ''
        str_rsn = ''
        stid = payload[pos:pos+12].uint
        pos += 12
        l = payload[pos:pos+8].uint
        pos += 8
        for i in range(l):
            str_ant += chr(payload[pos:pos+8].uint)
            pos += 8
        ant_setup = payload[pos:pos+8].uint
        pos += 8
        if msgnum == 1008 or msgnum == 1033:
            l = payload[pos:pos+8].uint
            pos += 8
            if 31 < l:
                l = 31
            for i in range(l):
                str_ser += chr(payload[pos:pos+8].uint)
                pos += 8
        if msgnum == 1033:
            l = payload[pos:pos+8].uint
            pos += 8
            if 31 < l:
                l = 31
            for i in range(l):
                str_rcv += chr(payload[pos:pos+8].uint)
                pos += 8
            l = payload[pos:pos+8].uint
            pos += 8
            if 31 < l:
                l = 31
            for i in range(l):
                str_ver += chr(payload[pos:pos+8].uint)
                pos += 8
            l = payload[pos:pos+8].uint
            pos += 8
            if 31 < l:
                l = 31
            for i in range(l):
                str_rsn += chr(payload[pos:pos+8].uint)
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
        return pos

    def decode_ephemerides(self, payload, satsys, mtype):
        "returns size of data"
        pos = 0
        string = f'{satsys}'
        if satsys == 'G':  # GPS ephemerides
            svid = payload[pos:pos+6].uint  # satellite id
            string += f'{svid:02d}'
            pos += 6
            wn = payload[pos:pos+10].uint  # week number
            string += f' WN={wn}'
            pos += 10
            pos += 4  # GPS SV accuracy
            gps_code = payload[pos:pos+2]  # GPS code L2: 01-P, 10-C/A 11-L2C
            if gps_code == '0b01':
                string += ' L2P'
            elif gps_code == '0b10':
                string += ' L2C/A'
            elif gps_code == '0b11':
                string += ' L2C'
            else:
                raise Exception('undefined GPS code on L2')
            pos += 2
            pos += 14  # i-dot
            iode = payload[pos:pos+8].uint  # IODE
            string += f' IODE={iode}'
            pos += 8
            pos += 16 + 8 + 16 + 22
            iodc = payload[pos:pos+10].uint  # IODC
            string += f' IODC={iodc}'
            pos += 10
            pos += 16 + 16 + 32 + 16 + 32 + 16 + 32 + 16 + 16 + 32 + \
                16 + 32 + 16 + 32 + 24 + 8
            health = payload[pos:pos+6].uint
            pos += 6
            l2p = payload[pos:pos+1]  # P code nav flag: 0-on, 1-off
            pos += 1
            pos += 1  # fit interval
        elif satsys == 'R':  # GLONASS ephemerides
            svid = payload[pos:pos+6].uint  # satellite id
            string +=f'{svid:02d}'
            pos += 6
            fcn = payload[pos:pos+5].uint  # frequency channel number
            string +=f' freq={fcn}'
            pos += 5
            health = payload[pos:pos+1].uint  # almanac health
            pos += 1
            pos += 2 + 12 + 1 + 1 + 7 + 24 + 27 + 5 + 24 + 27 + \
                5 + 24 + 27 + 5 + 1 + 11 + 2 + 1 + 22 + 5 + \
                5 + 1 + 4 + 11 + 2 + 1 + 11 + 32 + 5 + 22 + \
                1 + 7
        elif satsys == 'J':  # QZSS ephemerides
            svid = payload[pos:pos+4].uint
            string +=f'{svid:02d}'
            pos += 4
            pos += 16 + 8 + 16 + 22 + 8 + 16 + 16 + 32 + 16 + 32 + \
                16 + 32 + 16 + 16 + 32 + 16 + 32 + 16 + 32 + 24 + \
                14 + 2
            wn = payload[pos:pos+10].uint
            string += f' WN={wn}'
            pos += 10
            pos += 4  # URA
            health = payload[pos:pos+6].uint
            pos += 6
            pos += 8  # T_{GD}
            iodc = payload[pos:pos+10].uint
            string += f' IODC={iodc}'
            pos += 10
            pos += 1
        elif satsys == 'C':  # BeiDou ephemerides
            svid = payload[pos:pos+6].uint
            string +=f'{svid:02d}'
            pos += 6
            wn = payload[pos:pos+13].uint
            string += f' WN={wn}'
            pos += 13
            pos += 4 + 14 + 5 + 17 + 11 + 22 + 24 + 5 + 18 + 16 + \
                32 + 18 + 32 + 18 + 32 + 17 + 18 + 32 + 18 + 32 + \
                18 + 32 + 24 + 10 + 10
            health = payload[pos:pos+1].uint
            pos += 1
        elif satsys == 'I':  # NavIC ephemerides
            svid = payload[pos:pos+6].uint
            string +=f'{svid:02d}'
            pos += 6
            wn = payload[pos:pos+10].uint
            pos += 10
            pos += 22 + 16 + 8 + 4 + 16 + 8 + 22
            iodec = payload[pos:pos+8].uint  # issue of data ephemeris & clock
            string += f' IODEC={iodec}'
            pos += 8
            pos += 10  # reserved bits after IODEC
            health = payload[pos:pos+1].uint  # L5_flag & S_flag
            pos += 1
            pos += 15 + 15 + 15 + 15 + 15 + 15 + 14 + 32 + 16 + 32 + \
                32 + 32 + 32 + 22 + 32 + 2 + 2
        else:
            raise Exception(f'satsys={satsys}')
        string +=' health='
        if health:
            string += self.msg_color.fg('red')
        string += f'{health:02x}'
        if health:
            string += self.msg_color.fg('default')
        self.string = string  # update string
        return pos

    def decode_ephemerides_gal(self, payload, satsys, mtype):
        "returns size of data"
        pos = 0
        satid = payload[pos:pos+6].uint  # satellite id
        pos += 6
        wn = payload[pos:pos+12].uint  # week number
        pos += 12
        iodnav = payload[pos:pos+10].uint  # IODnav
        pos += 10
        sisa = payload[pos:pos+8].uint  # signal in space accuracy
        pos += 8
        idot = payload[pos:pos+14].int  # i-dot
        pos += 14
        toc = payload[pos:pos+14].uint  # t_{oc}
        pos += 14
        af2 = payload[pos:pos+6].int  # a_{f2}
        pos += 6
        af1 = payload[pos:pos+21].int  # a_{f1}
        pos += 21
        pf0 = payload[pos:pos+31].int  # a_{f0}
        pos += 31
        crs = payload[pos:pos+16].int  # C_{rs}
        pos += 16
        dn = payload[pos:pos+16].int  # delta n
        pos += 16
        m0 = payload[pos:pos+32].int  # M_0
        pos += 32
        cuc = payload[pos:pos+16].int  # C_{uc}
        pos += 16
        e = payload[pos:pos+32].uint  # e
        pos += 32
        cus = payload[pos:pos+16].int  # C_{us}
        pos += 16
        a12 = payload[pos:pos+32].uint  # sqrt{a}
        pos += 32
        toe = payload[pos:pos+14].uint  # t_{oe}
        pos += 14
        cic = payload[pos:pos+16].int  # C_{ic}
        pos += 16
        omega_o = payload[pos:pos+32].int  # Omega_0
        pos += 32
        cis = payload[pos:pos+16].int  # C_{is}
        pos += 16
        i0 = payload[pos:pos+32].int  # i_0
        pos += 32
        crc = payload[pos:pos+16].int  # C_{rc}
        pos += 16
        omega = payload[pos:pos+32].int  # omega
        pos += 32
        omegadot0 = payload[pos:pos+24].int  # Omega-dot 0
        pos += 24
        bdg_e5ae1 = payload[pos:pos+10].int  # BGD_{E5a/E1}
        pos += 10
        string = f'E{satid:02d} WN={wn} IODnav={iodnav}'
        if mtype == 'F/NAV':
            os_hs = payload[pos:pos+2]  # open signal health status
            pos =+ 2
            os_vs = payload[pos:pos+1]  # open signal validity status
            pos += 1
            string += ' OS_health='
            if os_hs:
                string += self.msg_color.fg('red')
            string += f'{os_hs.int}'
            if os_hs:
                string += self.msg_color.fg('default')
            if not os_vs:
                string += self.msg_color.fg('red') + '*' + self.msg_color.fg('default')
        else:
            bgd_e5be1 = payload[pos:pos+10].int  # BGD_{E5b/E1}
            pos += 10
            e5b_hs = payload[pos:pos+2]  # E5b signal health status
            pos += 2
            e5b_vs = payload[pos:pos+1]  # E5b data validity status
            pos += 1
            e1b_hs = payload[pos:pos+2]  # E1b signal health status
            pos =+ 2
            e1b_vs = payload[pos:pos+1]  # E1b signal validity status
            pos += 1
            string += ' E5b_health='
            if e5b_hs:
                string += self.msg_color.fg('red')
            string += f'{e5b_hs.int}'
            if e5b_hs:
                string += self.msg_color.fg('default')
            if not e5b_vs:
                string += self.msg_color.fg('red') + '*' + self.msg_color.fg('default')
            string += ' E1b_health='
            if e1b_hs:
                string += self.msg_color.fg('red')
            string += f'{e1b_hs.int}'
            if e1b_hs:
                string += self.msg_color.fg('default')
            if not e1b_vs:
                string += self.msg_color.fg('red') + '*' + self.msg_color.fg('default')
        pos += 7  # reserved
        self.string = string
        return pos

    def decode_msm(self, payload, satsys, mtype):  # decode MSM message
        "returns size of data"
        pos = 0
        sid = payload[pos:pos+12].uint  # reference station id
        pos += 12
        if satsys == 'R':
            dow = payload[pos:pos+3].uint
            pos += 3
            tod = payload[pos:pos+27].uint // 1000
            pos += 27
        elif satsys == 'C':
            tow = payload[pos:pos+30].uint // 1000
            pos += 30
            tow += 14  # BDT -> GPST
        else:
            tow = payload[pos:pos+30].uint // 1000
            pos += 30
        mm = payload[pos:pos+1]  # multiple message bit
        pos += 1
        iods = payload[pos:pos+3].uint  # issue of data station
        pos += 3
        time_s = payload[pos:pos+7].uint  # gnss specific
        pos += 7
        clk_s = payload[pos:pos+2].uint  # clock steering indicator
        pos += 2
        cls_e = payload[pos:pos+2].uint  # external clock indicator
        pos += 2
        smth = payload[pos:pos+1]  # divergence-free smoothing indicator
        pos += 1
        tint_s = payload[pos:pos+3].uint  # smoothing interval
        pos += 3
        sat_mask = [0 for i in range(64)]
        n_sat_mask = 0
        for i in range(64):
            mask = payload[pos:pos+1]  # satellite mask
            pos += 1
            if mask:
                sat_mask[n_sat_mask] = i
                n_sat_mask += 1
        sig_mask = [0 for i in range(32)]
        n_sig_mask = 0
        for i in range(32):
            mask = payload[pos:pos+1]  # signal mask
            pos += 1
            if mask:
                sig_mask[n_sig_mask] = i
                n_sig_mask += 1
        cell_mask = [0 for i in range(n_sat_mask * n_sig_mask)]
        for i in range(n_sat_mask * n_sig_mask):
            cell_mask[i] = payload[pos:pos+1]  # cell mask
            pos += 1
        if mtype in {'4', '5', '6', '7'}:
            for i in range(n_sat_mask):
                rng = payload[pos:pos+8].uint  # rough ranges
                pos += 8
        if mtype in {'5', '7'}:
            for i in range(n_sat_mask):
                esatinfo = payload[pos:pos+4].uint  # extended satellite info
                pos += 4
        for i in range(n_sat_mask):
            rng_m = payload[pos:pos+10].uint  # rough ranges modulo 1 ms
            pos += 10
        if mtype in {'5', '7'}:
            for i in range(n_sat_mask):
                prr = payload[pos:pos+14].int  # rough phase range rates
                pos += 14
        for i in range(n_sat_mask * n_sig_mask):  # pseudorange
            if not cell_mask[i]:
                continue
            bfpsr = 15  # bit size of fine pseudorange
            bfphr = 22  # bit size of fine phaserange
            blti = 4    # bit size of lock time indicator
            bcnr = 6    # bit size of CNR
            if mtype in {'6'}:
                bfpsr = 20  # extended bit size
                bfphr = 24  # extended bit size
                blti = 10   # extended bit size
            if mtype in {'1', '3', '4', '5', '6'}:
                fpsr = payload[pos:pos+bfpsr].uint  # fine pseudorange
                pos += bfpsr
            if mtype in {'2', '3', '4', '5', '6'}:
                fphr = payload[pos:pos+bfphr].uint  # fine phaserange
                pos += bfphr
                lti = payload[pos:pos+blti].uint  # lock time indicator
                pos += blti
                hai = payload[pos:pos+1]  # half ambiguity indicator
                pos += 1
            if mtype in {'4', '5', '6'}:
                cnr = payload[pos:pos+bcnr].uint  # CNR
                pos += bcnr
            if mtype in {'5'}:
                fphrr = payload[pos:pos+15].uint  # fine phaserange rates
                pos += 15
        string = ''
        if satsys != 'S':
            for i in range(n_sat_mask):
                string += f'{satsys}{sat_mask[i]+1:02} '
        else:
            for i in range(n_sat_mask):
                string += f'{satsys}{sat_mask[i]+119:3} '
        self.string = string  # update string
        return pos

    def decode_obs(self, payload, satsys, mtype):  # decode observation message
        "returns size of data"
        pos = 0
        sid = payload[pos:pos+12].uint  # reference station id
        pos += 12
        be = 30  # bit width of GPS epoch time
        bp = 24  # bit width of GPS pseudorange
        bi = 8   # bit width of GPS integer phase modurus ambiguity
        if satsys == 'R':
            be = 27
            bp = 25
            bi = 7
        tow = payload[pos:pos+be].uint  # epoch time
        pos += be
        sync_flag = payload[pos:pos+1]  # synchronous GNSS flag
        pos += 1
        nsat = payload[pos:pos+5].uint  # num of satellite signals processed
        pos += 5
        sind = payload[pos:pos+1]  # divergence-free smooting indicator
        pos += 1
        sint = payload[pos:pos+3]  # smoothing interval
        pos += 3  # GPS 64 bit GLO 61 bit
        for i in range(nsat):
            satid = payload[pos:pos+6].uint  # satellite id
            pos += 6
            cind1 = payload[pos:pos+1]  # L1 code indicator
            pos += 1
            if satsys == 'R':
                fnc = payload[pos:pos+5].uint  # frequency channel number
                pos += 5
            pr1 = payload[pos:pos+bp].uint  # L1 pseudorange
            pos += bp
            phpr1 = payload[pos:pos+20].int  # L1 phaserange-pseudorange
            pos += 20
            lti1 = payload[pos:pos+7].uint  # L1 lock time indicator
            pos += 7  # 58 bit
            if mtype in 'Full':
                pma1 = payload[pos:pos+bi].uint  # interger pseudorange modulus ambiguity
                pos += bi
                cnr1 = payload[pos:pos+8].uint  # L1 CNR
                pos += 8
            if mtype in 'L2':
                cind2 = payload[pos:pos+2].int  # L2 code indicator
                pos += 2
                prd = payload[pos:pos+14].int  # L2-L1 pseudorange difference
                pos += 14
                phpr2 = payload[pos:pos+20].int  # L2 phase-L1 pseudo range
                pos += 20
                lti2 = payload[pos:pos+7].uint  # L2 locktime indicator
                pos += 7
                cnr2 = payload[pos:pos+8].uint  # L2 CNR
                pos += 8
        return pos


    def decode_code_phase_bias(self, payload):  # decode code bias for GLO
        pos = 0
        sid = payload[pos:pos+12].uint  # reference station id
        pos += 12
        cpbi = payload[pos:pos+1]  # code-phase bias indicator
        pos += 1
        pos += 3  # reserved
        mask = payload[pos:pos+4]  # FDMA signal mask
        pos += 4
        l1ca_cpb = payload[pos:pos+16].int  # L1 C/A code-phase bias
        pos += 16
        l1p_cpb = payload[pos:pos+16].int  # L1 P code-phase bias
        pos += 16
        l2ca_cpb = payload[pos:pos+16].int # L2 C/A code-phase bias
        pos += 16
        l2p_cpb = payload[pos:pos+16].int  # L2 P  code-phase bias
        pos += 16
        return pos

    def decode_rtcm_msg(self):  # decode RTCM message
        # parse RTCM header
        payload = self.payload
        pos = 0
        msgnum = payload[pos:pos+12].uint  # message number
        pos += 12
        satsys = self.msgnum2satsys(msgnum)
        mtype = self.msgnum2mtype(msgnum)
        if 'Obs' in mtype:
            pos += self.decode_obs(payload[pos:], satsys, mtype)
        elif mtype == 'NAV':
            pos += self.decode_ephemerides(payload[pos:], satsys, mtype)
        elif mtype in {'F/NAV', 'I/NAV'}:
            pos += self.decode_ephemerides_gal(payload[pos:], satsys, mtype)
        elif mtype == 'CodePhase bias':
            pos += self.decode_code_phase_bias(payload[pos:])
        elif mtype in {'MSM4', 'MSM7'}:
            pos += self.decode_msm(payload[pos:], satsys, mtype)
        elif 'MSM' in mtype:
            pass  # to be implemented
        elif mtype == 'Ant/Rcv info':
            pos += self.decode_ant_info(payload[pos:], msgnum)
        elif mtype == 'Position':
            pos += self.decode_antenna_position(payload[pos:], msgnum)
        elif mtype == 'CSSR':
            pos += self.decode_cssr(payload)  # it needs message type info
        elif 'SSR' in mtype:
            pos += self.ssr_head_decode(payload[pos:], satsys, mtype)
            if mtype == 'SSR orbit':
                pos += self.ssr_decode_orbit(payload[pos:], satsys)
            elif mtype == 'SSR clock':
                pos += self.ssr_decode_clock(payload[pos:], satsys)
            elif mtype == 'SSR code bias':
                pos += self.ssr_decode_code_bias(payload[pos:], satsys)
            elif mtype == 'SSR URA':
                pos += self.ssr_decode_ura(payload[pos:], satsys)
            elif mtype == 'SSR hr clock':
                pos += self.ssr_decode_hr_clock(payload[pos:], satsys)
        else:
            pass  # unsupported message type
        message = self.msg_color.fg('green') + f'RTCM {msgnum} '
        message += self.msg_color.fg('yellow')
        message += f'{satsys:1} {mtype:14}'
        message += self.msg_color.fg('default') + self.string
        try:
            print(message, file=self.fp_msg)
            self.fp_msg.flush()
        except (BrokenPipeError, IOError):
            sys.exit()

    def send_rtcm(self, rtcm_payload):
        if not self.fp_rtcm:
            return
        r = rtcm_payload.tobytes()
        rtcm = b'\xd3' + len(r).to_bytes(2, 'big') + r
        rtcm_crc = libqzsl6tool.rtk_crc24q(rtcm, len(rtcm))
        self.fp_rtcm.buffer.write(rtcm)
        self.fp_rtcm.buffer.write(rtcm_crc)
        self.fp_rtcm.flush()

# EOF
