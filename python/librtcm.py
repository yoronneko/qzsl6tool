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
    fp_rtcm = None                  # file pointer for RTCM message output
    fp_trace = sys.stdout           # file pointer for trace
    t_level = 0                     # trace level
    ansi_color = False              # ANSI escape sequences
# protected
    ssr_nsat = 0                    # number of satellites
# private
    readbuf = b''                   # read buffer, used as static variable
    payload = bitstring.BitArray()  # payload excluding head, length, and CRC
    string = ''                     # information string
    ssr_mmi = 0                     # multiple message indicator
    ssr_iod = 0                     # iod ssr

    def trace(self, level, *args):
        if self.t_level < level:
            return
        for arg in args:
            try:
                print(arg, end='', file=self.fp_trace)
            except (BrokenPipeError, IOError):
                sys.exit()

    def read_rtcm_msg(self):
        "returns true if success in receing RTCM message"
        BUFMAX = 1000  # maximum length of buffering RTCM message
        BUFADD =   20  # length of buffering additional RTCM message
        ok = False
        while not ok:
            if BUFMAX < len(self.readbuf):
                print("RTCM buffer exhausted", file=sys.stderr)
                return False
            try:
                b = sys.stdin.buffer.read(BUFADD)
            except KeyboardInterrupt:
                msg_color = libcolor.Color(sys.stderr, self.ansi_color)
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
                msg_color = libcolor.Color(sys.stderr, self.ansi_color)
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

    def msgnum2mtype(self, msgnum):  # message number to message type
        mtype = f'MT{msgnum:<4d}'
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
        ssr_intvl = payload[pos:pos+4].uint  # ssr update interval
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
        strsat = ''
        svh = 0xff
        postop = pos
        if satsys == 'G':  # GPS ephemerides
            svid = payload[pos:pos+6].uint
            pos += 6
            pos += 10 + 4 + 2 + 14 + 8 + 16 + 8 + 16 + 22 + 10 + 16 + 16 + 32 + \
                16 + 32 + 16 + 32 + 16 + 16 + 32 + 16 + 32 + 16 + 32 + 24 + 8
            svh = payload[pos:pos+6].uint
        elif satsys == 'R':  # GLONASS ephemerides
            svid = payload[pos:pos+6].uint
            pos += 6
        elif satsys == 'I':  # NavIC ephemerides
            svid = payload[pos:pos+6].uint
            pos += 6
            pos += 10 + 22 + 16 + 8 + 4 + 16 + 8 + 22 + 8 + 10
            svh = payload[pos:pos+2].uint
        elif satsys == 'J':  # QZSS ephemerides
            svid = payload[pos:pos+4].uint
            pos += 4
            pos += 16 + 8 + 16 + 22 + 8 + 16 + 16 + 32 + 16 + 32 + 16 + \
                32 + 16 + 16 + 32 + 16 + 32 + 16 + 32 + 24 + 14 + 2 + 10 + 4
            svh = payload[pos:pos+6].uint
        elif mtype == 'F/NAV':  # Galileo F/NAV ephemerides
            svid = payload[pos:pos+6].uint
            pos += 6
        elif mtype == 'I/NAV':  # Galileo I/NAV ephemerides
            svid = payload[pos:pos+6].uint
            pos += 6
        elif satsys == 'C':  # BeiDou ephemerides
            svid = payload[pos:pos+6].uint
            pos += 6
            pos += 13 + 4 + 14 + 5 + 17 + 11 + 22 + 24 + 5 + 18 + 16 + 32 + 18 + \
                32 + 18 + 32 + 17 + 18 + 32 + 18 + 32 + 18 + 32 + 24 + 10 + 10
            svh = payload[pos:pos+1].uint
        string = f"{satsys}{svid:02d}"
        if svh != 0xff:
            string += f' svh={svh:02x}'
        self.string = string  # update string
        return pos

    def decode_msm(self, payload, satsys):  # decode MSM message
        "returns size of data"
        pos = 0
        stid = payload[pos:pos+12].uint
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
        sync = payload[pos:pos+1].uint
        pos += 1
        iod = payload[pos:pos+3].uint
        pos += 3
        time_s = payload[pos:pos+7].uint
        pos += 7
        clk_s = payload[pos:pos+2].uint
        pos += 2
        cls_e = payload[pos:pos+2].uint
        pos += 2
        smth = payload[pos:pos+1].uint
        pos += 1
        tint_s = payload[pos:pos+3].uint
        pos += 3
        sat_mask = [0 for i in range(64)]
        n_sat_mask = 0
        for i in range(64):
            mask = payload[pos:pos+1].uint
            pos += 1
            if mask:
                sat_mask[n_sat_mask] = i
                n_sat_mask += 1
        sig_mask = [0 for i in range(32)]
        n_sig_mask = 0
        for i in range(32):
            mask = payload[pos:pos+1]
            pos += 1
            if mask:
                sig_mask[n_sig_mask] = i
                n_sig_mask += 1
        cell_mask = [0 for i in range(n_sat_mask * n_sig_mask)]
        for i in range(n_sat_mask * n_sig_mask):
            cell_mask[i] = payload[pos:pos+1]
            pos += 1
        for i in range(n_sat_mask):  # range
            rng = payload[pos:pos+8].uint
            pos += 8
        for i in range(n_sat_mask):
            rng_m = payload[pos:pos+10].uint
            pos += 10
        for i in range(n_sat_mask * n_sig_mask):  # pseudorange
            if not cell_mask[i]:
                continue
            prv = payload[pos:pos+15].uint
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

    def decode_rtcm_msg(self):  # decode RTCM message
        # parse RTCM header
        payload = self.payload
        pos = 0
        msgnum = payload[pos:pos+12].uint  # message number
        pos += 12
        satsys = self.msgnum2satsys(msgnum)
        mtype = self.msgnum2mtype(msgnum)
        if 'Obs' in mtype:
            pass  # to be implemented
        elif 'NAV' in mtype:
            pos += self.decode_ephemerides(payload[pos:], satsys, mtype)
        elif mtype == 'CodePhase bias':
            pass  # to be implemented
        elif mtype in {'MSM4', 'MSM7'}:
            pos += self.decode_msm(payload[pos:], satsys)
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
        msg_color = libcolor.Color(self.fp_msg, self.ansi_color)
        message = msg_color.fg('green') + f'RTCM {msgnum} '
        message += msg_color.fg('yellow')
        message += f'{satsys:1} {mtype:14}'
        message += msg_color.fg('default') + self.string
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
