#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# librtcm.py: library for RTCM message processing
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022 Satoshi Takahashi
# Copyright (c) 2007-2020 by T.TAKASU
#
# The function rtk_crc24q () is from rtkcmn.c of RTKLIB 2.4.3b34,
# https://github.com/tomojitakasu/RTKLIB
#
# Released under BSD 2-clause license.
#
# References:
# [1] Radio Technical Commission for Maritime Services (RTCM),
#     Differential GNSS (Global Navigation Satellite Systems) Services
#     - Version 3, RTCM Standard 10403.3, Apr. 24 2020.
# [2] Global Positioning Augmentation Service Corporation (GPAS),
#     Quasi-Zenith Satellite System Correction Data on Centimeter Level
#     Augmentation Serice for Experiment Data Format Specification,
#     1st ed., Nov. 2017, in Japanese.
#     http://file.gpas.co.jp/L6E_MADOCA_DataFormat.pdf
# [3] Global Positioning Augmentation Service Corporation (GPAS),
#     Interface specification for GPAS-MADOCA Product
#     https://www.gpas.co.jp/data/GPAS-MADOCA_Interface_Specification_en.pdf

import sys
import ecef2llh
import libcolor
import libeph
import libobs
import libssr
try:
    import bitstring
except ModuleNotFoundError:
    print('''\
    QZS L6 Tool needs bitstring module.
    Please install this module such as \"pip install bitstring\".
    ''', file=sys.stderr)
    sys.exit(1)

class Rtcm:
    '''RTCM message process class'''
# --- private
    readbuf = b''                   # read buffer, used as static variable
    payload = bitstring.BitArray()  # payload excluding head, length, and CRC

    def __init__(self, fp_disp, t_level, color):
        self.fp_disp = fp_disp
        self.t_level = t_level
        self.msg_color = libcolor.Color(fp_disp, color)
        self.eph = libeph.Eph(fp_disp, t_level, self.msg_color)  # ephemeris
        self.obs = libobs.Obs(fp_disp, t_level, self.msg_color)  # observation
        self.ssr = libssr.Ssr(fp_disp, t_level, self.msg_color)  # SSR

# --- public
    def read_rtcm_msg(self):
        '''returns true if successfully reading an RTCM message'''
        BUFMAX = 1000  # maximum length of buffering RTCM message
        BUFADD =   20  # length of buffering additional RTCM message
        ok = False
        color = libcolor.Color(sys.stderr)
        while not ok:
            if BUFMAX < len(self.readbuf):
                print(color.fg('red') + \
                    "RTCM buffer exhausted" + \
                    color.fg(), file=sys.stderr)
                return False
            try:
                b = sys.stdin.buffer.read(BUFADD)
            except KeyboardInterrupt:
                print(color.fg('yellow') + \
                     "User break - terminated" + \
                     color.fg(), file=sys.stderr)
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
            if bc == rtk_crc24q(frame, len(frame)):
                ok = True
                self.readbuf = self.readbuf[pos+3+mlen+3:]
            else:  # CRC error
                print(color.fg('red') + \
                     "CRC error" + \
                     color.fg(), file=sys.stderr)
                self.readbuf = self.readbuf[pos + 1:]
                continue
        self.payload = bitstring.BitArray(bp)
        self.string = ''
        return True

    def decode_rtcm_msg(self):
        payload = self.payload
        pos = 0
        msgnum = payload[pos:pos+12].uint  # message number
        pos += 12
        satsys = msgnum2satsys(msgnum)
        mtype = msgnum2mtype(msgnum)
        msg = ''
        if mtype == 'Ant/Rcv info':
            pos, msg = self.decode_ant_info(payload, pos, msgnum)
        elif mtype == 'Position':
            pos, msg = self.decode_antenna_position(payload, pos, msgnum)
        elif mtype == 'CodePhase bias':
            pos, msg = self.decode_code_phase_bias(payload, pos)
        elif 'Obs' in mtype:
            pos, msg = self.obs.decode_obs(payload, pos, satsys, mtype)
        elif 'MSM' in mtype:
            pos, msg = self.obs.decode_msm(payload, pos, satsys, mtype)
        elif 'NAV' in mtype:
            pos, msg = self.eph.decode_ephemerides(payload, pos, satsys, mtype)
        elif mtype == 'CSSR':  # put before SSR, otherwise never selected
            pos, msg = self.ssr.decode_cssr(payload)  # needs message type info
        elif 'SSR' in mtype:
            pos = self.ssr.ssr_decode_head(payload, pos, satsys, mtype)
            if mtype == 'SSR orbit':
                pos, msg = self.ssr.ssr_decode_orbit(payload, pos, satsys)
            elif mtype == 'SSR clock':
                pos, msg = self.ssr.ssr_decode_clock(payload, pos, satsys)
            elif mtype == 'SSR code bias':
                pos, msg = self.ssr.ssr_decode_code_bias(payload, pos, satsys)
            elif mtype == 'SSR URA':
                pos, msg = self.ssr.ssr_decode_ura(payload, pos, satsys)
            elif mtype == 'SSR hr clock':
                pos, msg = self.ssr.ssr_decode_hr_clock(payload, pos, satsys)
            else:
                pass  # unsupported message type
        else:
            pass  # unsupported message type
        message = self.msg_color.fg('green') + f'RTCM {msgnum} '
        message += self.msg_color.fg('yellow')
        message += f'{satsys:1} {mtype:14}'
        message += self.msg_color.fg() + msg
        if pos % 8 != 0:  # byte align
            pos += 8 - (pos % 8)
        #if pos != len(payload.bin):
        #    message += self.msg_color.fg('red') + \
        #        ' RTCM packet size error:' + \
        #        f'expected {len(payload.bin)}, actual {pos}' + \
        #        self.msg_color.fg()
        try:
            print(message, file=self.fp_disp)
            self.fp_disp.flush()
        except (BrokenPipeError, IOError):
            sys.exit()

# --- private
    def trace(self, level, *args):
        if self.t_level < level:
            return
        for arg in args:
            try:
                print(arg, end='', file=self.fp_disp)
            except (BrokenPipeError, IOError):
                sys.exit()

    def decode_antenna_position(self, payload, pos, msgnum):
        '''returns pos and string'''
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
        return pos, string

    def decode_ant_info(self, payload, pos, msgnum):
        '''returns pos and string'''
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
        return pos, string

    def decode_code_phase_bias(self, payload, pos):
        '''decodes code-and-phase bias for GLONASS'''
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
        string = ''
        return pos, string

def send_rtcm(fp, rtcm_payload):
    if not fp:
        return
    r = rtcm_payload.tobytes()
    rtcm = b'\xd3' + len(r).to_bytes(2, 'big') + r
    rtcm_crc = rtk_crc24q(rtcm, len(rtcm))
    fp.buffer.write(rtcm)
    fp.buffer.write(rtcm_crc)
    fp.flush()

def msgnum2satsys(msgnum):  # message number to satellite system
    satsys = ''
    if msgnum in {1001, 1002, 1003, 1004, 1019, 1071, 1072, 1073, 1074,
                1075, 1076, 1077, 1057, 1058, 1059, 1060, 1061, 1062,
                11}:
        satsys = 'G'
    elif msgnum in {1009, 1010, 1011, 1012, 1020, 1081, 1081, 1082, 1083,
                1084, 1085, 1086, 1087, 1063, 1064, 1065, 1066, 1067,
                1068, 1230}:
        satsys = 'R'
    elif msgnum in {1045, 1046, 1091, 1092, 1093, 1094, 1095, 1096, 1097,
                1240, 1241, 1242, 1243, 1244, 1245, 12}:
        satsys = 'E'
    elif msgnum in {1044, 1111, 1112, 1113, 1114, 1115, 1116, 1117, 1246,
                1247, 1248, 1249, 1250, 1251, 13}:
        satsys = 'J'
    elif msgnum in {1042, 63, 1121, 1122, 1123, 1124, 1125, 1126, 1127, 1258,
                1259, 1260, 1261, 1262, 1263, 14}:
        satsys = 'C'
    elif msgnum in {1101, 1102, 1103, 1104, 1105, 1106, 1107}:
        satsys = 'S'
    elif msgnum in {1041, 1131, 1132, 1133, 1134, 1135, 1136, 1137}:
        satsys = 'I'
    return satsys

def msgnum2mtype(msgnum):  # message number to message type
    mtype = f'MT{msgnum:<4d}'
    if msgnum in {1001, 1009}:
        mtype = 'Obs L1'
    elif msgnum in {1002, 1010}:
        mtype = 'Obs Full L1'
    elif msgnum in {1003, 1011}:
        mtype = 'Obs L1L2'
    elif msgnum in {1004, 1012}:
        mtype = 'Obs Full L1L2'
    elif msgnum in {1019, 1020, 1044, 1042, 1041, 63}:
        mtype = 'NAV'
    elif msgnum == 1230:
        mtype = 'CodePhase bias'
    elif msgnum == 1045:
        mtype = 'F/NAV'
    elif msgnum == 1046:
        mtype = 'I/NAV'
    elif (1071 <= msgnum and msgnum <= 1077) or \
       (1081 <= msgnum and msgnum <= 1087) or \
       (1091 <= msgnum and msgnum <= 1097) or \
       (1101 <= msgnum and msgnum <= 1137):
        mtype = f'MSM{msgnum % 10}'
    elif msgnum in {1057, 1063, 1240, 1246, 1258}:
        mtype = 'SSR orbit'
    elif msgnum in {1058, 1064, 1241, 1247, 1259}:
        mtype = 'SSR clock'
    elif msgnum in {1059, 1065, 1242, 1248, 1260}:
        mtype = 'SSR code bias'
    elif msgnum in {1060, 1066, 1243, 1249, 1261}:
        mtype = 'SSR obt/clk'
    elif msgnum in {1061, 1067, 1244, 1250, 1262}:
        mtype = 'SSR URA'
    elif msgnum in {1062, 1068, 1245, 1251, 1263}:
        mtype = 'SSR hr clock'
    elif msgnum in {11, 12, 13, 14}:
        mtype = 'SSR phase bias'
    elif msgnum in {1007, 1008, 1033}:
        mtype = 'Ant/Rcv info'
    elif msgnum in {1005, 1006}:
        mtype = 'Position'
    elif msgnum == 4073:
        mtype = 'CSSR'
    return mtype

tbl_CRC24Q = [
    0x000000, 0x864CFB, 0x8AD50D, 0x0C99F6, 0x93E6E1, 0x15AA1A, 0x1933EC, 0x9F7F17,
    0xA18139, 0x27CDC2, 0x2B5434, 0xAD18CF, 0x3267D8, 0xB42B23, 0xB8B2D5, 0x3EFE2E,
    0xC54E89, 0x430272, 0x4F9B84, 0xC9D77F, 0x56A868, 0xD0E493, 0xDC7D65, 0x5A319E,
    0x64CFB0, 0xE2834B, 0xEE1ABD, 0x685646, 0xF72951, 0x7165AA, 0x7DFC5C, 0xFBB0A7,
    0x0CD1E9, 0x8A9D12, 0x8604E4, 0x00481F, 0x9F3708, 0x197BF3, 0x15E205, 0x93AEFE,
    0xAD50D0, 0x2B1C2B, 0x2785DD, 0xA1C926, 0x3EB631, 0xB8FACA, 0xB4633C, 0x322FC7,
    0xC99F60, 0x4FD39B, 0x434A6D, 0xC50696, 0x5A7981, 0xDC357A, 0xD0AC8C, 0x56E077,
    0x681E59, 0xEE52A2, 0xE2CB54, 0x6487AF, 0xFBF8B8, 0x7DB443, 0x712DB5, 0xF7614E,
    0x19A3D2, 0x9FEF29, 0x9376DF, 0x153A24, 0x8A4533, 0x0C09C8, 0x00903E, 0x86DCC5,
    0xB822EB, 0x3E6E10, 0x32F7E6, 0xB4BB1D, 0x2BC40A, 0xAD88F1, 0xA11107, 0x275DFC,
    0xDCED5B, 0x5AA1A0, 0x563856, 0xD074AD, 0x4F0BBA, 0xC94741, 0xC5DEB7, 0x43924C,
    0x7D6C62, 0xFB2099, 0xF7B96F, 0x71F594, 0xEE8A83, 0x68C678, 0x645F8E, 0xE21375,
    0x15723B, 0x933EC0, 0x9FA736, 0x19EBCD, 0x8694DA, 0x00D821, 0x0C41D7, 0x8A0D2C,
    0xB4F302, 0x32BFF9, 0x3E260F, 0xB86AF4, 0x2715E3, 0xA15918, 0xADC0EE, 0x2B8C15,
    0xD03CB2, 0x567049, 0x5AE9BF, 0xDCA544, 0x43DA53, 0xC596A8, 0xC90F5E, 0x4F43A5,
    0x71BD8B, 0xF7F170, 0xFB6886, 0x7D247D, 0xE25B6A, 0x641791, 0x688E67, 0xEEC29C,
    0x3347A4, 0xB50B5F, 0xB992A9, 0x3FDE52, 0xA0A145, 0x26EDBE, 0x2A7448, 0xAC38B3,
    0x92C69D, 0x148A66, 0x181390, 0x9E5F6B, 0x01207C, 0x876C87, 0x8BF571, 0x0DB98A,
    0xF6092D, 0x7045D6, 0x7CDC20, 0xFA90DB, 0x65EFCC, 0xE3A337, 0xEF3AC1, 0x69763A,
    0x578814, 0xD1C4EF, 0xDD5D19, 0x5B11E2, 0xC46EF5, 0x42220E, 0x4EBBF8, 0xC8F703,
    0x3F964D, 0xB9DAB6, 0xB54340, 0x330FBB, 0xAC70AC, 0x2A3C57, 0x26A5A1, 0xA0E95A,
    0x9E1774, 0x185B8F, 0x14C279, 0x928E82, 0x0DF195, 0x8BBD6E, 0x872498, 0x016863,
    0xFAD8C4, 0x7C943F, 0x700DC9, 0xF64132, 0x693E25, 0xEF72DE, 0xE3EB28, 0x65A7D3,
    0x5B59FD, 0xDD1506, 0xD18CF0, 0x57C00B, 0xC8BF1C, 0x4EF3E7, 0x426A11, 0xC426EA,
    0x2AE476, 0xACA88D, 0xA0317B, 0x267D80, 0xB90297, 0x3F4E6C, 0x33D79A, 0xB59B61,
    0x8B654F, 0x0D29B4, 0x01B042, 0x87FCB9, 0x1883AE, 0x9ECF55, 0x9256A3, 0x141A58,
    0xEFAAFF, 0x69E604, 0x657FF2, 0xE33309, 0x7C4C1E, 0xFA00E5, 0xF69913, 0x70D5E8,
    0x4E2BC6, 0xC8673D, 0xC4FECB, 0x42B230, 0xDDCD27, 0x5B81DC, 0x57182A, 0xD154D1,
    0x26359F, 0xA07964, 0xACE092, 0x2AAC69, 0xB5D37E, 0x339F85, 0x3F0673, 0xB94A88,
    0x87B4A6, 0x01F85D, 0x0D61AB, 0x8B2D50, 0x145247, 0x921EBC, 0x9E874A, 0x18CBB1,
    0xE37B16, 0x6537ED, 0x69AE1B, 0xEFE2E0, 0x709DF7, 0xF6D10C, 0xFA48FA, 0x7C0401,
    0x42FA2F, 0xC4B6D4, 0xC82F22, 0x4E63D9, 0xD11CCE, 0x575035, 0x5BC9C3, 0xDD8538
]

def rtk_crc24q(buff, length):
    crc = 0
    for i in range(length):
        crc = ((crc << 8) & 0xffffff) ^ tbl_CRC24Q[(crc >> 16) ^ buff[i]]
    return crc.to_bytes(3, 'big')

# EOF
