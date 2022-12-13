#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# libqzsl6tool.py: library for QZS L6 Tool
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022 Satoshi Takahashi
# Copyright (c) 2007-2020 by T.TAKASU
#
# Functions of getbitu(), getbits(), setbitu(), setbits(), getbits38(),
# getbits38(), rtk_crc32(), rtk_crc24q (), rtk_crc16 () are from
# rtkcmn.c of RTKLIB 2.4.3b34, https://github.com/tomojitakasu/RTKLIB
#
# Released under BSD 2-clause license.

import sys
import bitstring
import ecef2llh
import gps2utc

INVALID = 0  # invalid value indication for CSSR message show

tbl_CRC16 = [
    0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50A5, 0x60C6, 0x70E7,
    0x8108, 0x9129, 0xA14A, 0xB16B, 0xC18C, 0xD1AD, 0xE1CE, 0xF1EF,
    0x1231, 0x0210, 0x3273, 0x2252, 0x52B5, 0x4294, 0x72F7, 0x62D6,
    0x9339, 0x8318, 0xB37B, 0xA35A, 0xD3BD, 0xC39C, 0xF3FF, 0xE3DE,
    0x2462, 0x3443, 0x0420, 0x1401, 0x64E6, 0x74C7, 0x44A4, 0x5485,
    0xA56A, 0xB54B, 0x8528, 0x9509, 0xE5EE, 0xF5CF, 0xC5AC, 0xD58D,
    0x3653, 0x2672, 0x1611, 0x0630, 0x76D7, 0x66F6, 0x5695, 0x46B4,
    0xB75B, 0xA77A, 0x9719, 0x8738, 0xF7DF, 0xE7FE, 0xD79D, 0xC7BC,
    0x48C4, 0x58E5, 0x6886, 0x78A7, 0x0840, 0x1861, 0x2802, 0x3823,
    0xC9CC, 0xD9ED, 0xE98E, 0xF9AF, 0x8948, 0x9969, 0xA90A, 0xB92B,
    0x5AF5, 0x4AD4, 0x7AB7, 0x6A96, 0x1A71, 0x0A50, 0x3A33, 0x2A12,
    0xDBFD, 0xCBDC, 0xFBBF, 0xEB9E, 0x9B79, 0x8B58, 0xBB3B, 0xAB1A,
    0x6CA6, 0x7C87, 0x4CE4, 0x5CC5, 0x2C22, 0x3C03, 0x0C60, 0x1C41,
    0xEDAE, 0xFD8F, 0xCDEC, 0xDDCD, 0xAD2A, 0xBD0B, 0x8D68, 0x9D49,
    0x7E97, 0x6EB6, 0x5ED5, 0x4EF4, 0x3E13, 0x2E32, 0x1E51, 0x0E70,
    0xFF9F, 0xEFBE, 0xDFDD, 0xCFFC, 0xBF1B, 0xAF3A, 0x9F59, 0x8F78,
    0x9188, 0x81A9, 0xB1CA, 0xA1EB, 0xD10C, 0xC12D, 0xF14E, 0xE16F,
    0x1080, 0x00A1, 0x30C2, 0x20E3, 0x5004, 0x4025, 0x7046, 0x6067,
    0x83B9, 0x9398, 0xA3FB, 0xB3DA, 0xC33D, 0xD31C, 0xE37F, 0xF35E,
    0x02B1, 0x1290, 0x22F3, 0x32D2, 0x4235, 0x5214, 0x6277, 0x7256,
    0xB5EA, 0xA5CB, 0x95A8, 0x8589, 0xF56E, 0xE54F, 0xD52C, 0xC50D,
    0x34E2, 0x24C3, 0x14A0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
    0xA7DB, 0xB7FA, 0x8799, 0x97B8, 0xE75F, 0xF77E, 0xC71D, 0xD73C,
    0x26D3, 0x36F2, 0x0691, 0x16B0, 0x6657, 0x7676, 0x4615, 0x5634,
    0xD94C, 0xC96D, 0xF90E, 0xE92F, 0x99C8, 0x89E9, 0xB98A, 0xA9AB,
    0x5844, 0x4865, 0x7806, 0x6827, 0x18C0, 0x08E1, 0x3882, 0x28A3,
    0xCB7D, 0xDB5C, 0xEB3F, 0xFB1E, 0x8BF9, 0x9BD8, 0xABBB, 0xBB9A,
    0x4A75, 0x5A54, 0x6A37, 0x7A16, 0x0AF1, 0x1AD0, 0x2AB3, 0x3A92,
    0xFD2E, 0xED0F, 0xDD6C, 0xCD4D, 0xBDAA, 0xAD8B, 0x9DE8, 0x8DC9,
    0x7C26, 0x6C07, 0x5C64, 0x4C45, 0x3CA2, 0x2C83, 0x1CE0, 0x0CC1,
    0xEF1F, 0xFF3E, 0xCF5D, 0xDF7C, 0xAF9B, 0xBFBA, 0x8FD9, 0x9FF8,
    0x6E17, 0x7E36, 0x4E55, 0x5E74, 0x2E93, 0x3EB2, 0x0ED1, 0x1EF0
]

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


def getbitu(buff, pos, length):
    bits = 0
    for i in range(pos, pos + length):
        bits = (bits << 1) + ((buff[i // 8] >> (7 - i % 8)) & 1)
    return bits


def getbits(buff, pos, length):
    bits = getbitu(buff, pos, length)
    # if length <= 0 or 32 <= length or not bits & (1 << (length - 1)):
    if length <= 0 or 32 < length or not bits & (1 << (length - 1)):
        return bits
    return bits | (~0 << length)


def setbitu(buff, pos, length, data):
    mask = 1 << (length - 1)
    if length <= 0 or 32 < length:
        return
    for i in range(pos, pos + length):
        if data & mask:
            buff[i // 8] |= 1 << (7 - i % 8)
        else:
            buff[i // 8] &= ~(1 << (7 - i % 8))
        mask >>= 1


def setbits(buff, pos, length, data):
    if data < 0:
        data |= 1 << (length - 1)
    else:
        data &= ~(1 << (length - 1))
    setbitu(buff, pos, length, data)


def getbits38(buff, pos):
    return getbits(buff, pos, 32) * 64. + getbitu(buff, pos + 32, 6)


def rtk_crc32(buff, length):
    POLYCRC32 = 0xEDB88320  # CRC32  polynomial
    crc = 0
    for i in range(length):
        crc ^= buff[i]
        for j in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ POLYCRC32
            else:
                crc >> 1
    return crc.to_bytes(4, 'big')


def rtk_crc24q(buff, length):
    crc = 0
    for i in range(length):
        crc = ((crc << 8) & 0xffffff) ^ tbl_CRC24Q[(crc >> 16) ^ buff[i]]
    return crc.to_bytes(3, 'big')


def rtk_crc16(buff, length):
    crc = 0
    for i in range(length):
        crc = (crc << 8) ^ tbl_CRC16[((crc >> 8) ^ buff[i]) & 0xff]
    return crc.to_bytes(2, 'big')


def rtk_checksum(payload):
    checksum1 = 0
    checksum2 = 0
    for b in payload:
        checksum1 += b
        checksum2 += checksum1
        checksum1 &= 0xff
        checksum2 &= 0xff
    return checksum1, checksum2


class QzsL6:
    fp_trace = sys.stdout         # file pointer for trace
    fp_rtcm = None                # file pointer for rtcm output
    fp_msg = sys.stdout           # message output file pointer
    dpn = 0                       # data part number
    sfn = 0                       # subframe number
    vendor = ''                   # QZS L6 vendor name
    l6msg = bitstring.BitArray()  # QZS L6 message
    subtype = 0                   # CSSR subtype number
    run = False                   # CSSR decode start
    t_level = 0                   # trace level
    stat = False                  # statistics output
    stat_nsat = 0                 # stat: number of satellites
    stat_nsig = 0                 # stat: number of signals
    stat_bsat = 0                 # stat: bit number of satellites
    stat_bsig = 0                 # stat: bit number of signals
    stat_both = 0                 # stat: bit number of other information
    stat_bnull = 0                # stat: bit number of null

    def __init__(self):
        pass

    def __del__(self):
        if self.stat:
            self.show_cssr_stat()

    def show_cssr_stat(self):
        msg = f'stat n_sat {self.stat_nsat} n_sig {self.stat_nsig} ' + \
              f'bit_sat {self.stat_bsat} bit_sig {self.stat_bsig} ' + \
              f'bit_other {self.stat_both} bit_null {self.stat_bnull} ' + \
              f'bit_total {self.stat_bsat + self.stat_bsig + self.stat_both + self.stat_bnull}'
        print(msg, file=self.fp_trace)

    def trace(self, level, *args):
        if self.t_level < level:
            return
        for arg in args:
            try:
                print(arg, end='', file=self.fp_trace)
            except (BrokenPipeError, IOError):
                sys.exit()

    def receive_l6_msg(self):
        sync = [b'0x00' for i in range(4)]
        ok = False
        try:
            while not ok:
                b = sys.stdin.buffer.read(1)
                if not b:
                    return False
                sync = sync[1:4] + [b]
                if sync == [b'\x1a', b'\xcf', b'\xfc', b'\x1d']:
                    ok = True
            prn = int.from_bytes(sys.stdin.buffer.read(1), 'big')
            mtid = int.from_bytes(sys.stdin.buffer.read(1), 'big')
            dpart = bitstring.BitArray(sys.stdin.buffer.read(212))
            rs = sys.stdin.buffer.read(32)
        except KeyboardInterrupt:
            print("User break - terminated", file=sys.stderr)
            return False
        vid = mtid >> 5  # vender ID
        if vid == 0b001:
            vendor = "MADOCA"
        elif vid == 0b010:
            vendor = "MADOCA-PPP"
        elif vid == 0b011:
            vendor = "QZNMA"
        elif vid == 0b101:
            vendor = "CLAS"
        else:
            vendor = f"unknown (vendor ID 0b{vid:03b})"
        facility = "Kobe" if (mtid >> 4) & 1 else "Hitachi-Ota"
        facility += ":" + str((mtid >> 3) & 1)
        servid = "Ionosph" if (mtid >> 2) & 1 else "Clk/Eph"
        msg_ext = "CNAV" if (mtid >> 1) & 1 else "LNAV"
        sf_ind = mtid & 1  # subframe indicator
        self.prn = prn
        self.vendor = vendor
        self.facility = facility
        self.servid = servid
        self.msg_ext = msg_ext
        self.sf_ind = sf_ind
        self.alert = dpart[0:1].uint
        self.dpart = dpart[1:]
        return True

    def mdc2rtcm(self):
        dpart = self.dpart
        if len(dpart) < 12:
            return False
        pos = 0
        msgnum = dpart[pos:pos + 12].uint
        pos += 12
        if msgnum == 0:
            return False
        elif msgnum in {1057, 1059, 1061, 1062}:
            be = 20
            bs = 6  # bit size of epoch and numsat for GPS
        elif msgnum in {1246, 1248, 1250, 1251}:
            be = 20
            bs = 4  # bit size of epoch and numsat for QZSS
        elif msgnum in {1063, 1065, 1067, 1068}:
            be = 17
            bs = 6  # bit size of epoch and numsat for GLONASS
        else:
            self.trace(1, f"Unknown message number {msgnum}\n")
            return False
        epoch = dpart[pos:pos + be].uint
        pos += be
        interval = dpart[pos:pos + 4].uint
        pos += 4
        multind = dpart[pos:pos + 1].uint
        pos += 1
        if msgnum in {1057, 1246, 1063}:
            satref = dpart[pos:pos + 1].uint
            pos += 1
        iod = dpart[pos:pos + 4].uint
        pos += 4
        provider = dpart[pos:pos + 16].uint
        pos += 16
        solution = dpart[pos:pos + 4].uint
        pos += 4
        numsat = dpart[pos:pos + bs].uint
        pos += bs
        if msgnum == 1057:
            pos += 135 * numsat  # GPS orbit correction
        elif msgnum == 1059:     # GPS code bias
            for i in range(numsat):
                satid = dpart[pos:pos + 6].uint
                pos += 6
                numcb = dpart[pos:pos + 5].uint
                pos += 5
                pos += numcb * 19
        elif msgnum == 1061:
            pos += 12 * numsat  # GPS URA
        elif msgnum == 1062:
            pos += 28 * numsat  # GPS hr clock correction
        elif msgnum == 1246:
            pos += 133 * numsat  # QZSS orbit correction
        elif msgnum == 1248:     # QZSS code bias
            for i in range(numsat):
                satid = dpart[pos:pos + 4].uint
                pos += 4
                numcb = dpart[pos:pos + 5].uint
                pos += 5
                pos += numcb * 19
        elif msgnum == 1250:
            pos += 10 * numsat  # QZSS URA
        elif msgnum == 1251:
            pos += 26 * numsat  # QZSS hr clock correction
        elif msgnum == 1063:
            pos += 134 * numsat  # GLONASS orbit correction
        elif msgnum == 1065:     # GLONASS code bias
            for i in range(numsat):
                satid = dpart[pos:pos + 5].uint
                pos += 5
                numcb = dpart[pos:pos + 5].uint
                pos += 5
                pos += numcb * 19
        elif msgnum == 1067:
            pos += 11 * numsat  # GLONASS URA
        elif msgnum == 1068:
            pos += 27 * numsat  # GLONASS hr clock correction
        else:
            self.trace(
                1, f"Warning: msgnum {msgnum} drop {len (dpart)} bit:\n")
            self.trace(1, f"{dpart.bin}\n")
            return False
        if pos % 8 != 0:
            pos += 8 - (pos % 8)  # byte align
        self.rtcm = dpart[0:pos].tobytes()
        del dpart[0:pos]
        self.dpart = dpart
        self.msgnum = msgnum
        self.numsat = numsat
        return True

    def cssr2rtcm(self):
        if not self.run:
            return False
        if not self.decode_cssr_head():
            return False
        if self.subtype == 1:
            return self.decode_cssr_st1()
        elif self.subtype == 2:
            return self.decode_cssr_st2()
        elif self.subtype == 3:
            return self.decode_cssr_st3()
        elif self.subtype == 4:
            return self.decode_cssr_st4()
        elif self.subtype == 5:
            return self.decode_cssr_st5()
        elif self.subtype == 6:
            return self.decode_cssr_st6()
        elif self.subtype == 7:
            return self.decode_cssr_st7()
        elif self.subtype == 8:
            return self.decode_cssr_st8()
        elif self.subtype == 9:
            return self.decode_cssr_st9()
        elif self.subtype == 10:
            return self.decode_cssr_st10()
        elif self.subtype == 11:
            return self.decode_cssr_st11()
        elif self.subtype == 12:
            return self.decode_cssr_st12()
        raise Exception(f"Unknown CSSR subtype: {self.subtype}")

    def decode_cssr_head(self):
        l6msg = self.l6msg
        l6msglen = len(l6msg)
        pos = 0
        if '0b1' not in l6msg:  # Zero padding detection
            self.trace(2, f"CSSR null data {len(self.l6msg.bin)} bits\n")
            self.trace(2, f"CSSR dump: {self.l6msg.bin}\n")
            self.stat_bnull += len(self.l6msg.bin)
            self.l6msg = bitstring.BitArray()
            self.subtype = 0  # no subtype number
            return False
        if l6msglen < 12:
            self.msgnum = 0   # could not retreve the message number
            self.subtype = 0  # could not retreve the subtype number
            return False
        self.msgnum = l6msg[pos:pos + 12].uint
        pos += 12  # message num, 4073
        if self.msgnum != 4073:  # CSSR message number should be 4073
            self.trace(2, f"CSSR msgnum should be 4073 ({self.msgnum})\n")
            self.trace(2, f"{len(self.l6msg.bin)} bits\n")
            self.trace(2, f"CSSR dump: {self.l6msg.bin}\n")
            self.stat_bnull += len(self.l6msg.bin)
            self.l6msg = bitstring.BitArray()
            self.subtype = 0  # no subtype number
            return False
        if l6msglen < pos + 4:
            self.subtype = 0  # could not retreve the subtype number
            return False
        self.subtype = l6msg[pos:pos + 4].uint  # subtype
        pos += 4
        if self.subtype == 10:  # Service Information --- not implemented
            self.pos = pos
            return False
        elif self.subtype == 1:  # Mask message
            if l6msglen < pos + 20:  # could not retreve the epoch
                return False
            self.epoch = l6msg[pos:pos + 20].uint  # GPS epoch time 1s
            pos += 20
        else:
            if l6msglen < pos + 12:  # could not retreve the hourly epoch
                return False
            self.hepoch = l6msg[pos:pos + 12].uint  # GNSS hourly epoch
            pos += 12
        if l6msglen < pos + 4 + 1 + 4:
            return False
        self.interval = l6msg[pos:pos + 4].uint  # update interval
        pos += 4
        self.mmi = l6msg[pos:pos + 1].uint  # multiple message indication
        pos += 1
        self.iod = l6msg[pos:pos + 4].uint  # IOD SSR
        pos += 4
        self.pos = pos
        return True

    def gnssid2satsys(self, gnssid):
        if gnssid == 0:
            satsys = 'G'
        elif gnssid == 1:
            satsys = 'R'
        elif gnssid == 2:
            satsys = 'E'
        elif gnssid == 3:
            satsys = 'C'
        elif gnssid == 4:
            satsys = 'J'
        elif gnssid == 5:
            satsys = 'S'
        else:
            raise Exception(f'undefined gnssid {gnssid}')
        return satsys

    def sigmask2signame(self, satsys, sigmask):
        signame = f'satsys={satsys} sigmask={sigmask}'
        if satsys == 'G':
            signame = [
                "L1 C/A",
                "L1 P",
                "L1 Z-tracking",
                "L1 L1C(D)",
                "L1 L1C(P)",
                "L1 L1C(D+P)",
                "L2 L2C(M)",
                "L2 L2C(L)",
                "L2 L2C(M+L)",
                "L2 P",
                "L2 Z-tracking",
                "L5 I",
                "L5 Q",
                "L5 I+Q",
                "", ""][sigmask]
        elif satsys == 'R':
            signame = [
                "G1 C/A",
                "G1 P",
                "G2 C/A",
                "G2 P",
                "G1a(D)",
                "G1a(P)",
                "G1a(D+P)",
                "G2a(D)",
                "G2a(P)",
                "G2a(D+P)",
                "G3 I",
                "G3 Q",
                "G3 I+Q",
                "", "", "", ""][sigmask]
        elif satsys == 'E':
            signame = [
                "E1 B I/NAV OS/CS/SoL",
                "E1 C no data",
                "E1 B+C",
                "E5a I F/NAV OS",
                "E5a Q no data",
                "E5a I+Q",
                "E5b I I/NAV OS/CS/SoL",
                "E5b Q no data",
                "E5b I+Q",
                "E5 I",
                "E5 Q",
                "E5 I+Q",
                "Service specific 1",
                "Service specific 2",
                "Service specific 3",
                ""][sigmask]
        elif satsys == 'C':
            signame = [
                "B1 I",
                "B1 Q",
                "B1 I+Q",
                "B3 I",
                "B3 Q",
                "B3 I+Q",
                "B2 I",
                "B2 Q",
                "B2 I+Q",
                "", "", "", "", "", "", "", ""][sigmask]
        elif satsys == 'J':
            signame = [
                "L1 C/A",
                "L1 L1C(D)",
                "L1 L1C(P)",
                "L1 L1C(D+P)",
                "L2 L2C(M)",
                "L2 L2C(L)",
                "L2 L2C(M+L)",
                "L5 I",
                "L5 Q",
                "L5 I+Q",
                "", "", "", "", "", ""][sigmask]
        elif satsys == 'S':
            signame = [
                "L1 C/A",
                "L5 I",
                "L5 Q",
                "L5 I+Q",
                "", "", "", "", "", "", "", "", "", "", "", "", ""][sigmask]
        else:
            raise Exception(f'unassigned signal name for satsys={satsys} ' +
                            f'and sigmask={sigmask}')
        return signame

    def decode_cssr_st1(self):
        l6msg = self.l6msg
        l6msglen = len(l6msg)
        if l6msglen < 49:
            return False
        pos = self.pos
        ngnss = l6msg[pos:pos + 4].uint
        pos += 4  # numer of GNSS
        if len(l6msg) < 49 + 61 * ngnss:
            return False
        satsys = [None for i in range(ngnss)]
        nsatmask = [None for i in range(ngnss)]
        nsigmask = [None for i in range(ngnss)]
        cellmask = [None for i in range(ngnss)]
        gsys = {}
        gsig = {}
        for ignss in range(ngnss):
            ugnssid = l6msg[pos:pos + 4].uint
            pos += 4
            bsatmask = l6msg[pos:pos + 40]
            pos += 40
            bsigmask = l6msg[pos:pos + 16]
            pos += 16
            cmavail = l6msg[pos:pos + 1]
            pos += 1
            t_satsys = self.gnssid2satsys(ugnssid)
            t_satmask = 0
            t_sigmask = 0
            t_gsys = []
            t_gsig = []
            for i, val in enumerate(bsatmask):
                if val:
                    t_satmask += 1
                    t_gsys.append(t_satsys + f'{i + 1:02d}')
            for i, val in enumerate(bsigmask):
                if val:
                    t_sigmask += 1
                    t_gsig.append(self.sigmask2signame(t_satsys, i))
            ncell = t_satmask * t_sigmask
            if cmavail:
                bcellmask = l6msg[pos:pos + ncell]
                pos += ncell
            else:
                bcellmask = bitstring.BitArray('0b1') * ncell
            cellmask[ignss] = bcellmask
            satsys[ignss] = t_satsys
            nsatmask[ignss] = t_satmask
            nsigmask[ignss] = t_sigmask
            gsys[t_satsys] = t_gsys
            gsig[t_satsys] = t_gsig
        self.satsys = satsys      # satellite system
        self.nsatmask = nsatmask  # number of satellite mask
        self.nsigmask = nsigmask  # number of signal mask
        self.cellmask = cellmask  # cell mask
        self.gsys = gsys          # dict of sat   name from system name
        self.gsig = gsig          # dict of sigal name from system name
        self.stat_nsat = 0
        self.stat_nsig = 0
        msg_trace1 = ''
        for i, satsys in enumerate(self.satsys):
            pos_mask = 0  # mask position
            for j, gsys in enumerate(self.gsys[satsys]):
                self.stat_nsat += 1
                msg_trace1 += 'ST1 ' + gsys
                for gsig in self.gsig[satsys]:
                    mask = self.cellmask[i][pos_mask]
                    pos_mask += 1
                    if not mask:
                        continue
                    msg_trace1 += ' ' + gsig
                    self.stat_nsig += 1
                msg_trace1 += '\n'
        self.rtcm = l6msg[:pos].tobytes()
        self.l6msg = l6msg[pos:]  # removal of ST1 message
        self.trace(1, msg_trace1)
        if self.stat:
            self.show_cssr_stat()
        self.stat_bsat = 0
        self.stat_bsig = 0
        self.stat_both = pos
        self.stat_bnull = 0
        return True

    def decode_cssr_st2(self):
        l6msg = self.l6msg
        l6msglen = len(l6msg)
        pos = self.pos
        stat_pos = pos
        msg_trace1 = ''
        for satsys in self.satsys:
            w_iode = 10 if satsys == 'E' else 8  # IODE bit width
            for gsys in self.gsys[satsys]:
                if l6msglen < pos + w_iode + 15 + 13 + 13:
                    return False
                iode = l6msg[pos:pos + w_iode].uint
                pos += w_iode
                i_radial = l6msg[pos:pos + 15].int
                d_radial = i_radial * 0.0016 if i_radial != -16384 else INVALID
                pos += 15
                i_along = l6msg[pos:pos + 13].int
                d_along = i_radial * 0.0064 if i_along != -16384 else INVALID
                pos += 13
                i_cross = l6msg[pos:pos + 13].int
                d_cross = i_radial * 0.0064 if i_cross != -16384 else INVALID
                pos += 13
                msg_trace1 += f'ST2 {gsys} IODE={iode:4d}' + \
                              f' d_radial={d_radial:4.1f}m' + \
                              f' d_along={d_along:4.1f}m' + \
                              f' d_cross={d_cross:4.1f}m\n'
        self.rtcm = l6msg[:pos].tobytes()
        self.l6msg = l6msg[pos:]  # removal of ST2 message
        self.trace(1, msg_trace1)
        self.stat_both += stat_pos
        self.stat_bsat += pos - stat_pos
        return True

    def decode_cssr_st3(self):
        l6msg = self.l6msg
        l6msglen = len(l6msg)
        pos = self.pos
        stat_pos = pos
        msg_trace1 = ''
        for i, satsys in enumerate(self.satsys):
            for gsys in self.gsys[satsys]:
                if l6msglen < pos + 15:
                    return False
                ic0 = l6msg[pos:pos + 15].int
                pos += 15
                c0 = ic0 * 0.0016 if ic0 != -16384 else INVALID
                msg_trace1 += f"ST3 {gsys} d_clock={c0:4.1f}m\n"
        self.rtcm = l6msg[:pos].tobytes()
        self.l6msg = l6msg[pos:]  # rmoval of ST3 message
        self.trace(1, msg_trace1)
        self.stat_both += stat_pos
        self.stat_bsat += pos - stat_pos
        return True

    def decode_cssr_st4(self):
        l6msg = self.l6msg
        nsigsat = 0  # Nsig * Nsat
        for i, satsys in enumerate(self.satsys):
            pos_mask = 0  # mask position
            for gsys in self.gsys[satsys]:
                for gsig in self.gsig[satsys]:
                    mask = self.cellmask[i][pos_mask]
                    pos_mask += 1
                    if not mask:
                        continue
                    nsigsat += 1
        if len(l6msg) < 37 + 11 * nsigsat:
            return False
        pos = self.pos  # mask position
        stat_pos = pos
        msg_trace1 = ''
        for i, satsys in enumerate(self.satsys):
            pos_mask = 0  # mask position
            for j, gsys in enumerate(self.gsys[satsys]):
                for k, gsig in enumerate(self.gsig[satsys]):
                    mask = self.cellmask[i][pos_mask]
                    pos_mask += 1
                    if not mask:
                        continue
                    cb = l6msg[pos:pos + 11].int
                    pos += 11
                    code_bias = cb * 0.02 if cb != -1024 else INVALID
                    msg_trace1 += f"ST4 {gsys} {gsig:13s} " +  \
                                  f"code_bias={code_bias:4.1f}m\n"
        self.rtcm = l6msg[:pos].tobytes()
        self.l6msg = l6msg[pos:]  # removal of ST4 message
        self.trace(1, msg_trace1)
        self.stat_both += stat_pos
        self.stat_bsig += pos - stat_pos
        return True

    def decode_cssr_st5(self):
        l6msg = self.l6msg
        l6msglen = len(l6msg)
        pos = self.pos
        stat_pos = pos
        msg_trace1 = ''
        for i, satsys in enumerate(self.satsys):
            pos_mask = 0
            for gsys in self.gsys[satsys]:
                for gsig in self.gsig[satsys]:
                    mask = self.cellmask[i][pos_mask]
                    pos_mask += 1
                    if not mask:
                        continue
                    if l6msglen < pos + 15 + 2:
                        return False
                    pb = l6msg[pos:pos + 15].int
                    pos += 15
                    di = l6msg[pos:pos + 2].uint
                    pos += 2
                    phase_bias = pb * 0.001 if pb != -16384 else INVALID
                    msg_trace1 += f'ST5 {gsys} {gsig:13s}' + \
                                  f' phase_bias={phase_bias:4.1f}m' + \
                                  f' discont_indicator={di}\n'
        self.rtcm = l6msg[:pos].tobytes()
        self.l6msg = l6msg[pos:]  # removal of ST5 message
        self.trace(1, msg_trace1)
        self.stat_both += stat_pos
        self.stat_bsig += pos - stat_pos
        return True

    def decode_cssr_st6(self):
        l6msg = self.l6msg
        l6msglen = len(l6msg)
        if l6msglen < 45:
            return False
        pos = self.pos
        stat_pos = pos
        f_cb = l6msg[pos:pos + 1].uint  # code bias existing flag
        pos += 1
        f_pb = l6msg[pos:pos + 1].uint  # phase bias existing flag
        pos += 1
        f_nb = l6msg[pos:pos + 1].uint  # network bias existing flag
        pos += 1
        svmask = {}
        cnid = 0
        for satsys in self.satsys:
            bcellmask = bitstring.BitArray('0b1') * len(self.gsys[satsys])
        msg_trace1 = \
            f"ST6 code_bias={'on' if f_cb else 'off'}" + \
            f" phase_bias={'on' if f_pb else 'off'}" + \
            f" network_bias={'on' if f_nb else 'off'}\n"
        if f_nb:
            cnid = l6msg[pos:pos + 5].uint  # compact network ID
            pos += 5
            msg_trace1 += f"ST6 NID={cnid}\n"
            for satsys in self.satsys:
                ngsys = len(self.gsys[satsys])
                if l6msglen < pos + ngsys:
                    return False
                svmask[satsys] = l6msg[pos:pos + ngsys]
                pos += ngsys
        for i, satsys in enumerate(self.satsys):
            pos_mask = 0  # mask position
            for j, gsys in enumerate(self.gsys[satsys]):
                for gsig in self.gsig[satsys]:
                    mask = self.cellmask[i][pos_mask]
                    pos_mask += 1
                    if not svmask[satsys][j] or not mask:
                        continue
                    msg_trace1 += f"ST6 {gsys} {gsig:13s}"
                    if f_cb:
                        if l6msglen < pos + 11:
                            return False
                        cb = l6msg[pos:pos + 11].int
                        code_bias = cb * 0.02 if cb != -1024 else INVALID
                        pos += 11  # code bias
                        msg_trace1 += f" code_bias={code_bias:4.1f}m"
                    if f_pb:
                        if l6msglen < pos + 15 + 2:
                            return False
                        pb = l6msg[pos:pos + 15].int
                        phase_bias = pb * 0.001 if pb != -16384 else INVALID
                        pos += 15
                        di = l6msg[pos:pos + 2].uint
                        pos += 2
                        msg_trace1 += f" phase_bias={phase_bias:6.3f}m" +  \
                                      f" discont_indi={di}"
                    msg_trace1 += '\n'
        self.rtcm = l6msg[:pos].tobytes()
        self.l6msg = l6msg[pos:]  # removal of ST6 message
        self.trace(1, msg_trace1)
        self.stat_both += stat_pos + 3
        self.stat_bsig += pos - stat_pos - 3
        return True

    def decode_cssr_st7(self):
        l6msg = self.l6msg
        l6msglen = len(l6msg)
        if l6msglen < 37:
            return False
        pos = self.pos
        stat_pos = pos
        msg_trace1 = ''
        for satsys in self.satsys:
            for gsys in self.gsys[satsys]:
                if l6msglen < pos + 6:
                    return False
                ura = l6msg[pos:pos + 6].uint
                pos += 6
                msg_trace1 += f"ST7 {gsys} URA {ura}\n"
        self.rtcm = l6msg[:pos].tobytes()
        self.l6msg = l6msg[pos:]  # removal of ST7 message
        self.trace(1, msg_trace1)
        self.stat_both += stat_pos
        self.stat_bsat += pos - stat_pos
        return True

    def decode_cssr_st8(self):
        l6msg = self.l6msg
        l6msglen = len(l6msg)
        if l6msglen < 44:
            return False
        pos = self.pos
        stat_pos = pos
        stec_type = l6msg[pos:pos + 2].uint  # STEC correction type
        pos += 2
        cnid = l6msg[pos:pos + 5].uint  # compact network ID
        pos += 5
        svmask = {}
        for satsys in self.satsys:
            ngsys = len(self.gsys[satsys])
            if l6msglen < pos + ngsys:
                return False
            svmask[satsys] = l6msg[pos:pos + ngsys]
            pos += ngsys
        msg_trace1 = ''
        for satsys in self.satsys:
            for i, gsys in enumerate(self.gsys[satsys]):
                if not svmask[satsys][i]:
                    continue
                if l6msglen < pos + 6 + 14:
                    return False
                qi = l6msg[pos:pos + 6].uint  # quality indicator
                pos += 6
                ic00 = l6msg[pos:pos + 14].int
                c00 = ic00 * 0.05 if ic00 != -8192 else INVALID
                msg_trace1 += f"ST8 {gsys} c00={c00:5.2f}TECU"
                pos += 14
                if 1 <= stec_type:
                    if l6msglen < pos + 12 + 12:
                        return False
                    ic01 = l6msg[pos:pos + 12].int
                    c01 = ic01 * 0.02 if ic01 != -2048 else INVALID
                    pos += 12
                    ic10 = l6msg[pos:pos + 12].int
                    c10 = ic10 * 0.02 if ic10 != -2048 else INVALID
                    pos += 12
                    msg_trace1 += f" c01={c01:5.2f}TECU/deg c10={c10:5.2f}TECU/deg"
                if 2 <= stec_type:
                    if l6msglen < pos + 10:
                        return False
                    ic11 = l6msg[pos:pos + 10].int
                    c11 = ic11 * 0.02 if ic11 != -512 else INVALID
                    pos += 10
                    msg_trace1 += f" c11={c11:5.2f}TECU/deg^2"
                if 3 <= stec_type:
                    if l6msglen < pos + 8 + 8:
                        return False
                    ic02 = l6msg[pos:pos + 8].int
                    c02 = ic02 * 0.005 if ic02 != -128 else INVALID
                    pos += 8
                    ic20 = l6msg[pos:pos + 8].int
                    c20 = ic20 * 0.005 if ic20 != -128 else INVALID
                    pos += 8
                    msg_trace1 += f" c02={c02:5.2f}TECU/deg^2 c20={c20:5.2f}TECU/deg^2"
                msg_trace1 += '\n'
        self.rtcm = l6msg[:pos].tobytes()
        self.l6msg = l6msg[pos:]  # removal of ST8 message
        self.trace(1, msg_trace1)
        self.stat_both += stat_pos + 7
        self.stat_bsat += pos - stat_pos - 7
        return True

    def decode_cssr_st9(self):
        l6msg = self.l6msg
        l6msglen = len(l6msg)
        if l6msglen < 45:
            return False
        pos = self.pos
        tctype = l6msg[pos:pos + 2].uint  # tropospheric correction type
        pos += 2
        crange = l6msg[pos:pos + 1].uint  # tropospheric correction range
        bw = 16 if crange else 7
        pos += 1
        cnid = l6msg[pos:pos + 5].uint  # compact network ID
        pos += 5
        svmask = {}
        for satsys in self.satsys:
            ngsys = len(self.gsys[satsys])
            if l6msglen < pos + ngsys:
                return False
            svmask[satsys] = l6msg[pos:pos + ngsys]
            pos += ngsys
        if l6msglen < pos + 6 + 6:
            return False
        tqi = l6msg[pos:pos + 6].uint  # tropospheric quality indicator
        pos += 6
        ngrid = l6msg[pos:pos + 6].uint  # number of grids
        pos += 6
        msg_trace1 = f"ST9 Trop correct_type={tctype}" + \
                     f" NID={cnid} quality={tqi} ngrid={ngrid}\n"
        for i in range(ngrid):
            if l6msglen < pos + 9 + 8:
                return False
            ivd_h = l6msg[pos:pos + 9].int  # hydrostatic vertical delay
            vd_h = ivd_h * 0.004 if ivd_h != -256 else INVALID
            pos += 9
            ivd_w = l6msg[pos:pos + 8].int  # wet vertical delay
            vd_w = ivd_w * 0.004 if ivd_w != -128 else INVALID
            pos += 8
            msg_trace1 += \
                f'ST9 Trop     grid {i+1:2d}/{ngrid:2d}' + \
                f' dry-delay={vd_h:6.3f}m wet-delay={vd_w:6.3f}m\n'
            for satsys in self.satsys:
                for j, gsys in enumerate(self.gsys[satsys]):
                    if not svmask[satsys][j]:
                        continue
                    if l6msglen < pos + bw:
                        return False
                    res = l6msg[pos:pos + bw].int
                    residual = res * 0.04
                    if (crange == 1 and res == -32767) or \
                       (crange == 0 and res == -64):
                        residual = INVALID
                    pos += bw
                    msg_trace1 += \
                        f'ST9 STEC {gsys} grid {i+1:2d}/{ngrid:2d}' + \
                        f' residual={residual:5.2f}TECU ({bw}bit)\n'
        self.trace(1, msg_trace1)
        self.rtcm = l6msg[:pos].tobytes()
        self.l6msg = l6msg[pos:]  # removal of ST9 message
        self.stat_both += pos
        return True

    def decode_cssr_st10(self):  # not implemented
        self.trace(1, f"ST10 --- not implemented")
        self.l6msg = bitstring.BitArray()  # removal of ST10 message
        return False

    def decode_cssr_st11(self):
        l6msg = self.l6msg
        l6msglen = len(l6msg)
        if l6msglen < 40:
            return False
        pos = self.pos
        stat_pos = pos
        f_o = l6msg[pos:pos + 1].uint  # orbit existing flag
        pos += 1
        f_c = l6msg[pos:pos + 1].uint  # clock existing flag
        pos += 1
        f_n = l6msg[pos:pos + 1].uint  # network correction
        pos += 1
        msg_trace1 = f"ST11 Orb={'on' if f_o else 'off'} " + \
                     f"Clk={'on' if f_c else 'off'} " + \
                     f"Net={'on' if f_n else 'off'}\n"
        if f_n:
            if l6msglen < pos + 5:
                return False
            cnid = l6msg[pos:pos + 5].uint  # compact network ID
            pos += 5
            msg_trace1 += f"ST11 NID={cnid}\n"
            svmask = {}
            for satsys in self.satsys:
                ngsys = len(self.gsys[satsys])
                if l6msglen < pos + ngsys:
                    return False
                svmask[satsys] = l6msg[pos:pos + ngsys]
                pos += ngsys
            for satsys in self.satsys:
                for i, gsys in enumerate(self.gsys[satsys]):
                    if not svmask[satsys][i]:
                        continue
                    msg_trace1 += f"ST11 {gsys}"
                    if f_o:
                        w_iode = 10 if satsys == 'E' else 8  # IODE width
                        if l6msglen < pos + w_iode + 15 + 13 + 13:
                            return False
                        iode = l6msg[pos:pos + w_iode].uint
                        pos += w_iode
                        id_radial = l6msg[pos:pos + 15].int
                        d_radial = id_radial * 0.0016 if id_radial != -16384 else INVALID
                        pos += 15
                        id_along = l6msg[pos:pos + 13].int
                        d_along = id_along * 0.0064 if id_along != -4096 else INVALID
                        pos += 13
                        id_cross = l6msg[pos:pos + 13].int
                        d_cross = id_cross * 0.0064 if id_cross != -4096 else INVALID
                        pos += 13
                        msg_trace1 += \
                            f" IODE={iode:4d}" +\
                            f" d_radial={d_radial:5.1f}m" + \
                            f" d_along={d_along:5.1f}m" + \
                            f" d_cross={d_cross:5.1f}m"
                    if f_c:
                        if l6msglen < pos + 15:
                            return False
                        ic0 = l6msg[pos:pos + 15].int
                        c0 = ic0 * 0.0016 if ic0 != -16384 else INVALID
                        pos += 15
                        msg_trace1 += f" c0={c0:5.1f}m"
                    msg_trace1 += "\n"
        self.rtcm = l6msg[:pos].tobytes()
        self.l6msg = l6msg[pos:]  # removal of ST11 message
        self.trace(1, msg_trace1)
        self.stat_both += stat_pos + 3
        self.stat_bsat += pos - stat_pos - 3
        if f_n:  # correct bit number because because we count up bsat as NID
            self.stat_both += 5
            self.stat_bsat -= 5
        return True

    def decode_cssr_st12(self):
        l6msg = self.l6msg
        l6msglen = len(l6msg)
        if l6msglen < 52:
            return False
        pos = self.pos
        tropo = l6msg[pos:pos + 2]  # Tropospheric correction avail
        pos += 2
        stec = l6msg[pos:pos + 2]  # STEC correction avail
        pos += 2
        cnid = l6msg[pos:pos + 5].uint  # compact network ID
        pos += 5
        ngrid = l6msg[pos:pos + 6].uint  # number of grids
        pos += 6
        msg_trace1 = \
            f"ST12 tropo={tropo} stec={stec} NID={cnid} ngrid={ngrid}\n" + \
            f"ST12 Trop"
        if tropo[0]:
            # 0 <= ttype (forward reference)
            if l6msglen < pos + 6 + 2 + 9:
                return False
            tqi = l6msg[pos:pos + 6].uint  # tropo quality indicator
            pos += 6
            ttype = l6msg[pos:pos + 2].uint  # tropo correction type
            pos += 2
            it00 = l6msg[pos:pos + 9].int  # tropo poly coeff
            t00 = it00 * 0.004 if it00 != -256 else INVALID
            pos += 9
            msg_trace1 += f" quality={tqi} correct_type(0-2)={ttype}" + \
                          f" t00={t00:6.2f}m"
            if 1 <= ttype:
                if l6msglen < pos + 7 + 7:
                    return False
                it01 = l6msg[pos:pos + 7].int
                t01 = it01 * 0.002 if it01 != -64 else INVALID
                pos += 7
                it10 = l6msg[pos:pos + 7].int
                t10 = it10 * 0.002 if it10 != -64 else INVALID
                pos += 7
                msg_trace1 += f" t01={t01:5.2f}m/deg t10={t10:5.2f}m/deg"
            if 2 <= ttype:
                if l6msglen < pos + 7:
                    return False
                it11 = l6msg[pos:pos + 7].int
                t11 = it11 * 0.001 if it11 != -64 else INVALID
                pos += 7
                msg_trace1 += f" t11={t11:5.2f}m/deg^2"
            msg_trace1 += '\n'
        if tropo[1]:
            if l6msglen < pos + 1 + 4:
                return False
            trs = l6msg[pos:pos + 1].uint  # tropo residual size
            pos += 1
            bw = 8 if trs else 6
            itro = l6msg[pos:pos + 4].uint  # tropo residual offset
            pos += 4
            tro = itro * 0.02
            msg_trace1 += f"ST12 Trop offset={tro:5.2f}m\n"
            if l6msglen < pos + bw * ngrid:
                return False
            for i in range(ngrid):
                itr = l6msg[pos:pos + bw].int  # troposphere residual
                pos += bw
                tr = itr * 0.004
                if (trs == 0 and itr != -32) or (trs == 1 and itr != -128):
                    tr = INVALID
                msg_trace1 += \
                    f"ST12 Trop grid {i+1:2d}/{ngrid:2d}" + \
                    f" residual={tr:5.2f}m ({bw}bit)\n"
        stat_pos = pos
        if stec[0]:
            svmask = {}
            for satsys in self.satsys:
                ngsys = len(self.gsys[satsys])
                if l6msglen < pos + ngsys:
                    return False
                svmask[satsys] = l6msg[pos:pos + ngsys]
                pos += ngsys
            for satsys in self.satsys:
                for i, gsys in enumerate(self.gsys[satsys]):
                    if not svmask[satsys][i]:
                        continue
                    if l6msglen < pos + 6 + 2 + 14:
                        return False
                    sqi = l6msg[pos:pos + 6].uint  # quality indicator
                    pos += 6
                    sct = l6msg[pos:pos + 2].uint  # correction type
                    pos += 2
                    ic00 = l6msg[pos:pos + 14].int
                    c00 = ic00 * 0.05 if ic00 != -8192 else INVALID
                    pos += 14
                    msg_trace1 += \
                        f"ST12 STEC {gsys} quality={sqi:02x} type={sct}" + \
                        f" c00={c00:.1f}TECU"
                    if 1 <= sct:
                        if l6msglen < pos + 12 + 12:
                            return False
                        ic01 = l6msg[pos:pos + 12].int
                        c01 = ic01 * 0.02 if ic01 != -2048 else INVALID
                        pos += 12
                        ic10 = l6msg[pos:pos + 12].int
                        c10 = ic10 * 0.02 if ic10 != -2048 else INVALID
                        pos += 12
                        msg_trace1 += f" c01={c01:.1f}TECU/deg c10={c10:.1f}TECU/deg"
                    if 2 <= sct:
                        if l6msglen < pos + 10:
                            return False
                        ic11 = l6msg[pos:pos + 10].int
                        c11 = ic11 * 0.02 if ic11 != -512 else INVALID
                        pos += 10
                        msg_trace1 += f" c11={c11:.1f}TECU/deg^2"
                    if 3 <= sct:
                        if l6msglen < pos + 8 + 8:
                            return False
                        ic02 = l6msg[pos:pos + 8].int
                        c02 = ic02 * 0.005 if ic02 != -128 else INVALID
                        pos += 8
                        ic20 = l6msg[pos:pos + 8].int
                        c20 = ic20 * 0.005 if ic20 != -128 else INVALID
                        pos += 8
                        msg_trace1 += f" c02={c02:.1f}TECU/deg^2 c20={c20:.1f}TECU/deg^2"
                    msg_trace1 += '\n'
                    if l6msglen < pos + 2:
                        return False
                    srs = l6msg[pos:pos + 2].uint  # STEC residual size
                    pos += 2
                    bw = 4
                    lsb = 0.04
                    if srs == 1:
                        bw = 4
                        lsb = 0.12
                    elif srs == 2:
                        bw = 5
                        lsb = 0.16
                    elif srs == 3:
                        bw = 7
                        lsb = 0.24
                    for i in range(ngrid):
                        if l6msglen < pos + bw:
                            return False
                        isr = l6msg[pos:pos + bw].int
                        sr = isr * lsb
                        if (srs == 0 and isr == -8) or \
                           (srs == 1 and isr == -8) or \
                           (srs == 2 and isr == -16) or \
                           (srs == 3 and isr == -64):
                            sr = INVALID
                        pos += bw
                        msg_trace1 += \
                            f"ST12 STEC {gsys} grid {i+1:2d}/{ngrid:2d} " + \
                            f"residual={sr:5.2f}TECU ({bw}bit)\n"
        self.rtcm = l6msg[:pos].tobytes()
        self.l6msg = l6msg[pos:]  # removal of ST12 message
        self.trace(1, msg_trace1)
        self.stat_both += stat_pos
        self.stat_bsat += pos - stat_pos
        return True

    def send_rtcm(self):
        if not self.fp_rtcm:
            return
        rtcm = b'\xd3' + len(self.rtcm).to_bytes(2, 'big') + self.rtcm
        rtcm_crc = rtk_crc24q(rtcm, len(rtcm))
        self.fp_rtcm.buffer.write(rtcm)
        self.fp_rtcm.buffer.write(rtcm_crc)
        self.fp_rtcm.flush()

    def show_l6_msg(self):
        if self.vendor == "MADOCA":
            self.show_mdc_msg()
        elif self.vendor in {"CLAS", "MADOCA-PPP"}:
            self.show_cssr_msg()
        elif self.vendor == "QZNMA":
            self.show_qznma_msg()
        else:  # unknown vendor
            self.show_unknown_msg()

    def show_msg(self, message):
        if not self.fp_msg:
            return
        try:
            print(
                f'{self.prn} {self.facility:13s}' +
                f'{"*" if self.alert else " "} {self.vendor} {message}',
                file=self.fp_msg)
        except (BrokenPipeError, IOError):
            sys.exit()

    def show_mdc_msg(self):
        dpart = self.dpart
        pos = 0
        self.tow = dpart[pos:pos + 20].uint
        pos += 20
        self.wn = dpart[pos:pos + 13].uint
        pos += 13
        self.dpart = dpart[pos:]
        message = gps2utc.gps2utc(self.wn, self.tow) + ' '
        while self.mdc2rtcm():
            message += 'RTCM ' + str(self.msgnum) + \
                       '(' + str(self.numsat) + ') '
            self.send_rtcm()
        self.show_msg(message)

    def show_cssr_msg(self):
        if self.sf_ind:  # first data part
            self.dpn = 1
            self.l6msg = bitstring.BitArray(self.dpart)
            if not self.decode_cssr_head():
                self.l6msg = bitstring.BitArray()
            elif self.subtype == 1:
                self.sfn = 1
                self.run = True
            else:
                if self.run:  # first data part but subtype is not ST1
                    self.sfn += 1
                else:  # first data part but ST1 has not beed received
                    self.l6msg = bitstring.BitArray()
        else:  # continual data part
            if self.run:
                self.dpn += 1
                if self.dpn == 6:  # data part number should be less than 6
                    self.trace(1, "Warning: too many datapart\n")
                    self.run = False
                    self.dpn = 0
                    self.sfn = 0
                    self.l6msg = bitstring.BitArray()
                else:
                    self.l6msg.append(self.dpart)
        message = ''
        if self.sfn != 0:
            message += ' SF' + str(self.sfn) + ' DP' + str(self.dpn)
            if self.vendor == "MADOCA-PPP":
                message += f' ({self.servid} {self.msg_ext})'
        if not self.cssr2rtcm():  # could not decode any message
            if self.run and self.subtype == 0:  # whole message is null
                message += ' (null)'
            elif self.run:  # continual message
                message += f' ST{self.subtype}...'
        else:
            message += f' ST{self.subtype}'
            self.send_rtcm()
            while self.cssr2rtcm():  # try to decode next message
                message += f' ST{self.subtype}'
                self.send_rtcm()
            if len(self.l6msg) != 0:  # continues to next datapart
                message += f' ST{self.subtype}...'
        self.show_msg(message)

    def show_qznma_msg(self):
        l6msg = bitstring.BitArray(self.dpart)
        self.trace(2, f"QZNMA dump: {l6msg.bin}\n")
        self.show_msg('')

    def show_unknown_msg():
        l6msg = bitstring.BitArray(self.dpart)
        self.trace(2, f"Unknown dump: {l6msg.bin}\n")
        self.show_msg('')


class Rtcm:
    t_level = 0  # trace level

    def receive_rtcm_msg(self):
        b = b''
        try:
            while (b != b'\xd3'):
                b = sys.stdin.buffer.read(1)
                if not b:
                    return False
            bl = sys.stdin.buffer.read(2)     # possible length
            mlen = getbitu(bl, 6, 10)         # message length
            bp = sys.stdin.buffer.read(mlen)  # possible payload
            bc = sys.stdin.buffer.read(3)     # possible CRC
            if not bl or not bp or not bc:
                return False
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
                        if not bl or not bp or not bc:
                            return False
                        frame = b'\xd3' + bl + bp
        except KeyboardInterrupt:
            print("User break - terminated", file=sys.stderr)
            return False
        self.payload = frame[3:]
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
        self.ssr_epoch = getbitu(payload, pos, bw)  # ephch time
        pos += bw
        self.ssr_ntvl = getbitu(payload, pos, 4)  # ssr update interval
        pos += 4
        self.ssr_mmi = getbitu(payload, pos, 1)  # multiple message indicator
        pos += 1
        if mtype == 'SSR orbit' or mtype == 'SSR obt/clk':
            self.ssr_sdat = getbitu(payload, pos, 1)  # satellite ref datum
            pos += 1
        self.ssr_iod = getbitu(payload, pos, 4)  # iod ssr
        pos += 4
        self.ssr_pid = getbitu(payload, pos, 16)  # ssr provider id
        pos += 16
        self.ssr_sid = getbitu(payload, pos, 4)  # ssr solution id
        pos += 4
        bw = 6 if satsys != 'J' else 4
        # bit width changes according to satellite system
        self.ssr_nsat = getbitu(payload, pos, bw)  # number of satellites
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
            satid = getbitu(payload, pos, bw)  # satellite ID
            pos += bw
            iode = getbitu(payload, pos, 8)  # IODE
            pos += 8
            drad = getbits(payload, pos, 22)  # delta radial
            pos += 22
            dalng = getbits(payload, pos, 20)  # delta along track
            pos += 20
            dcrs = getbits(payload, pos, 20)  # delta cross track
            pos += 20
            ddrad = getbits(payload, pos, 21)  # delta radial
            pos += 21
            ddalng = getbits(payload, pos, 19)  # delta along track
            pos += 19
            ddcrs = getbits(payload, pos, 19)  # delta cross track
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
            satid = getbitu(payload, pos, bw)  # satellite ID
            pos += bw
            dc0 = getbits(payload, pos, 22)  # delta clock c0
            pos += 22
            dc1 = getbits(payload, pos, 21)  # delta clock c1
            pos += 21
            dc2 = getbits(payload, pos, 27)  # delta clock c2
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
            satid = getbitu(payload, pos, bw)  # satellite ID
            pos += bw
            ncb = getbitu(payload, pos, 5)  # code bias number
            pos += 5
            strsat += f"{self.satsys}{satid:02} "
            for j in range(ncb):
                stmi = getbitu(payload, pos, 5)
                # signal & tracking mode indicator
                pos += 5
                cb = getbits(payload, pos, 14)  # code bias
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
            satid = getbitu(payload, pos, bw)  # satellite ID
            pos += bw
            ura = getbits(payload, pos, 6)  # user range accuracy
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
            satid = getbitu(payload, pos, bw)  # satellite ID
            pos += bw
            hrc = getbits(payload, pos, 22)  # high rate clock
            pos += 22
            strsat += f"{self.satsys}{satid:02} "
        self.string = f"{strsat}(nsat={self.ssr_nsat} iod={self.ssr_iod}" + \
                      f"{' cont.' if self.ssr_mmi else ''})"

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
        interval = getbitu(payload, pos, 4)  # update interval
        pos += 4
        mmi = getbitu(payload, pos, 1)  # multiple message
        pos += 1
        iod = getbitu(payload, pos, 4)  # issue of data
        pos += 4
        self.string += f' iod={iod}'

    def decode_antenna_position(self):  # decode antenna position
        payload = self.payload
        pos = self.pos
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
        if self.msgnum == 1006:  # antenna height for RTCM 1006
            ahgt = getbitu(payload, pos, 16) * 1e-4
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
        stid = getbitu(payload, pos, 12)
        pos += 12
        l = getbitu(payload, pos, 8)
        pos += 8
        for i in range(l):
            str_ant += chr(getbitu(payload, pos, 8))
            pos += 8
        ant_setup = getbitu(payload, pos, 8)
        pos += 8
        if self.msgnum == 1008 or self.msgnum == 1033:
            l = getbitu(payload, pos, 8)
            pos += 8
            if 31 < l:
                l = 31
            for i in range(l):
                str_ser += chr(getbitu(payload, pos, 8))
                pos += 8
        if self.msgnum == 1033:
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
            svid = getbitu(payload, pos, 6)
            pos += 6
            pos += 10 + 4 + 2 + 14 + 8 + 16 + 8 + 16 + 22 + 10 + 16 + 16 + 32 + \
                16 + 32 + 16 + 32 + 16 + 16 + 32 + 16 + 32 + 16 + 32 + 24 + 8
            svh = getbitu(payload, pos, 6)
        elif satsys == 'R':  # GLONASS ephemerides
            svid = getbitu(payload, pos, 6)
            pos += 6
        elif satsys == 'I':  # NavIC ephemerides
            svid = getbitu(payload, pos, 6)
            pos += 6
            pos += 10 + 22 + 16 + 8 + 4 + 16 + 8 + 22 + 8 + 10
            svh = getbitu(payload, pos, 2)
        elif satsys == 'J':  # QZSS ephemerides
            svid = getbitu(payload, pos, 4)
            pos += 4
            pos += 16 + 8 + 16 + 22 + 8 + 16 + 16 + 32 + 16 + 32 + 16 + \
                32 + 16 + 16 + 32 + 16 + 32 + 16 + 32 + 24 + 14 + 2 + 10 + 4
            svh = getbitu(payload, pos, 6)
        elif mtype == 'F/NAV':  # Galileo F/NAV ephemerides
            svid = getbitu(payload, pos, 6)
            pos += 6
        elif mtype == 'I/NAV':  # Galileo I/NAV ephemerides
            svid = getbitu(payload, pos, 6)
            pos += 6
        elif satsys == 'C':  # BeiDou ephemerides
            svid = getbitu(payload, pos, 6)
            pos += 6
            pos += 13 + 4 + 14 + 5 + 17 + 11 + 22 + 24 + 5 + 18 + 16 + 32 + 18 + \
                32 + 18 + 32 + 17 + 18 + 32 + 18 + 32 + 18 + 32 + 24 + 10 + 10
            svh = getbitu(payload, pos, 1)
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
        string = ''
        for i in range(n_sat_mask):
            string += f'{self.satsys}{sat_mask[i]+1:02} '
        self.string = string  # update string

    def decode_rtcm_msg(self):  # decode RTCM message
        # parse RTCM header
        self.msgnum = getbitu(self.payload, 0, 12)  # message number
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
            raise Exception(f'unknown message type: {self.mtype}')
        try:
            print(f"RTCM {self.msgnum} {self.satsys:1} {self.mtype:14}"
                  f"{self.string}")
            sys.stdout.flush()
        except BrokenPipeError:
            sys.exit()

# EOF
