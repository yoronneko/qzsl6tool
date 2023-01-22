#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# libeph.py: library for RTCM ephemeride message processing
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022 Satoshi Takahashi
#
# Released under BSD 2-clause license.
#
# References:
# [1] Radio Technical Commission for Maritime Services (RTCM),
#     Differential GNSS (Global Navigation Satellite Systems) Services
#     - Version 3, RTCM Standard 10403.3, Apr. 24 2020.

class Eph:
    '''Ephemeris class'''
    def __init__(self, fp_disp, t_level, msg_color):
        self.fp_disp = fp_disp
        self.t_level = t_level
        self.msg_color = msg_color

    def trace(self, level, *args):
        if self.t_level < level:
            return
        for arg in args:
            try:
                print(arg, end='', file=self.fp_disp)
            except (BrokenPipeError, IOError):
                sys.exit()

    def decode_ephemerides(self, payload, pos, satsys, mtype):
        '''returns pos and string'''
        string = ''
        if satsys == 'G':  # GPS ephemerides
            svid = payload[pos:pos+6].uint  # satellite id
            pos += 6
            string = f'G{svid:02d}'
            wn = payload[pos:pos+10].uint  # week number
            pos += 10
            string += f' WN={wn}'
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
            pos += 8
            string += f' IODE={iode}'
            pos += 16 + 8 + 16 + 22
            iodc = payload[pos:pos+10].uint  # IODC
            pos += 10
            string += f' IODC={iodc}'
            pos += 16 + 16 + 32 + 16 + 32 + 16 + 32 + 16 + 16 + 32 + \
                16 + 32 + 16 + 32 + 24 + 8
            health = payload[pos:pos+6].uint
            pos += 6
            if health:
                string += ' health=' + self.msg_color.fg('red') + \
                    f'{health:02x}' + self.msg_color.fg()
            else:
                string += f' health={health:02x}'
            l2p = payload[pos:pos+1]  # P code nav flag: 0-on, 1-off
            pos += 1
            pos += 1  # fit interval
        elif satsys == 'R':  # GLONASS ephemerides
            svid = payload[pos:pos+6].uint  # satellite id
            pos += 6
            string =f'R{svid:02d}'
            fcn = payload[pos:pos+5].uint  # frequency channel number
            pos += 5
            string +=f' freq={fcn:<2d}'
            health = payload[pos:pos+1].uint  # almanac health
            pos += 1
            if health:
                string += ' health=' + self.msg_color.fg('red') + \
                    f'{health:02x}' + self.msg_color.fg()
            else:
                string += f' health={health:02x}'
            pos += 2 + 12 + 1 + 1 + 7 + 24 + 27 + 5 + 24 + 27 + \
                5 + 24 + 27 + 5 + 1 + 11 + 2 + 1 + 22 + 5 + \
                5 + 1 + 4 + 11 + 2 + 1 + 11 + 32 + 5 + 22 + \
                1 + 7
        elif satsys == 'E':  # Galileo ephemerides
            svid = payload[pos:pos+6].uint  # satellite id
            pos += 6
            string = f'E{svid:02d}'
            wn = payload[pos:pos+12].uint  # week number
            pos += 12
            string += f' WN={wn}'
            iodnav = payload[pos:pos+10].uint  # IODnav
            pos += 10
            string += f' IODnav={iodnav}'
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
            af0 = payload[pos:pos+31].int  # a_{f0}
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
            if mtype == 'F/NAV':
                os_hs = payload[pos:pos+2]  # open signal health status
                pos += 2
                os_vs = payload[pos:pos+1]  # open signal validity status
                pos += 1
                pos += 7  # reserved
                if os_hs:
                    string += ' OS_health=' + self.msg_color.fg('red') + \
                        f'{os_hs.int}' + self.msg_color.fg()
                else:
                    string += f' OS_health={os_hs.int}'
                if os_vs:
                    string += self.msg_color.fg('red') + '*' + \
                        self.msg_color.fg()
            else:
                bgd_e5be1 = payload[pos:pos+10].int  # BGD_{E5b/E1}
                pos += 10
                e5b_hs = payload[pos:pos+2]  # E5b signal health status
                pos += 2
                e5b_vs = payload[pos:pos+1]  # E5b data validity status
                pos += 1
                e1b_hs = payload[pos:pos+2]  # E1b signal health status
                pos += 2
                e1b_vs = payload[pos:pos+1]  # E1b signal validity status
                pos += 1
                pos += 2  # reserved
                if e5b_hs:
                    string += ' E5b_health=' + self.msg_color.fg('red') + \
                        f'{e5b_hs.int}' + self.msg_color.fg()
                else:
                    string += f' E5b_health={e5b_hs.int}'
                if e5b_vs:
                    string += self.msg_color.fg('red') + '*' + \
                        self.msg_color.fg()
                if e1b_hs:
                    string += ' E1b_health=' + self.msg_color.fg('red') + \
                        f'{e1b_hs.int}' + self.msg_color.fg()
                else:
                    string += f' E1b_health={e1b_hs.int}'
                if e1b_vs:
                    string += self.msg_color.fg('red') + '*' + \
                        self.msg_color.fg()
        elif satsys == 'J':  # QZSS ephemerides
            svid = payload[pos:pos+4].uint
            string =f'J{svid:02d}'
            pos += 4
            pos += 16 + 8 + 16 + 22 + 8 + 16 + 16 + 32 + 16 + 32 + \
                16 + 32 + 16 + 16 + 32 + 16 + 32 + 16 + 32 + 24 + \
                14 + 2
            wn = payload[pos:pos+10].uint
            string += f' WN={wn}'
            pos += 10
            pos += 4  # URA
            health = payload[pos:pos+6].uint
            if health:  # to be determined: L1 C/B operation
                string +=' health=' + self.msg_color.fg('red') + \
                    f'{health:02x}' + self.msg_color.fg()
            else:
                string += f' health={health:02x}'
            pos += 6
            pos += 8  # T_{GD}
            iodc = payload[pos:pos+10].uint
            string += f' IODC={iodc}'
            pos += 10
            pos += 1
        elif satsys == 'C':  # BeiDou ephemerides
            svid = payload[pos:pos+6].uint
            string =f'C{svid:02d}'
            pos += 6
            wn = payload[pos:pos+13].uint
            string += f' WN={wn}'
            pos += 13
            pos += 4 + 14 + 5 + 17 + 11 + 22 + 24 + 5 + 18 + 16 + \
                32 + 18 + 32 + 18 + 32 + 17 + 18 + 32 + 18 + 32 + \
                18 + 32 + 24 + 10 + 10
            health = payload[pos:pos+1].uint
            if health:
                string += ' health=' + self.msg_color.fg('red') + \
                    f'{health:02x}' + self.msg_color.fg()
            else:
                string += f' health={health:02x}'
            pos += 1
        elif satsys == 'I':  # NavIC ephemerides
            svid = payload[pos:pos+6].uint
            string =f'I{svid:02d}'
            pos += 6
            wn = payload[pos:pos+10].uint
            pos += 10
            pos += 22 + 16 + 8 + 4 + 16 + 8 + 22
            iodec = payload[pos:pos+8].uint  # issue of data ephemeris & clock
            string += f' IODEC={iodec}'
            pos += 8
            pos += 10  # reserved bits after IODEC
            health = payload[pos:pos+1].uint  # L5_flag & S_flag
            if health:
                string += ' health=' + self.msg_color.fg('red') + \
                    f'{health:02x}' + self.msg_color.fg()
            else:
                string += f' health={health:02x}'
            pos += 1
            pos += 15 + 15 + 15 + 15 + 15 + 15 + 14 + 32 + 16 + 32 + \
                32 + 32 + 32 + 22 + 32 + 2 + 2
        else:
            raise Exception(f'satsys={satsys}')
        return pos, string

# EOF
