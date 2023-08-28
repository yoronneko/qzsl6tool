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
        if self.t_level < level or not self.fp_disp:
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
            svid = payload[pos:pos+ 6].uint; pos +=  6  # satellite id
            wn   = payload[pos:pos+10].uint; pos += 10  # week number
            string = f'G{svid:02d} WN={wn}'
            pos += 4                                    # GPS SV accuracy
            gps_code = payload[pos:pos+2]; pos += 2     # GPS code L2
            if   gps_code == '0b01': string += ' L2P'
            elif gps_code == '0b10': string += ' L2C/A'
            elif gps_code == '0b11': string += ' L2C'
            else: raise Exception('undefined GPS code on L2')
            pos += 14                       # i-dot
            iode = payload[pos:pos+8].uint; pos += 8 # IODE
            string += f' IODE={iode}'
            pos += 16 + 8 + 16 + 22
            iodc = payload[pos:pos+10].uint; pos += 10 # IODC
            string += f' IODC={iodc}'
            pos += 16 + 16 + 32 + 16 + 32 + 16 + 32 + 16 + 16 + 32 + \
                16 + 32 + 16 + 32 + 24 + 8
            health = payload[pos:pos+6].uint; pos += 6
            if health:
                string += ' health=' + self.msg_color.fg('red') + \
                    f'{health:02x}' + self.msg_color.fg()
            else:
                string += f' health={health:02x}'
            l2p = payload[pos:pos+1]; pos += 1 # P code nav flag: 0-on, 1-off
            pos += 1                           # fit interval
        elif satsys == 'R':  # GLONASS ephemerides
            svid = payload[pos:pos+6].uint; pos += 6 # satellite id
            fcn  = payload[pos:pos+5].uint; pos += 5 # frequency channel number
            string = f'R{svid:02d} freq={fcn:<2d}'
            health = payload[pos:pos+1].uint; pos += 1 # almanac health
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
            svid   = payload[pos:pos+ 6].uint; pos +=  6  # satellite id
            wn     = payload[pos:pos+12].uint; pos += 12  # week number
            iodnav = payload[pos:pos+10].uint; pos += 10  # IODnav
            string = f'E{svid:02d} WN={wn} IODnav={iodnav}'
            sisa   = payload[pos:pos+ 8].uint; pos +=  8 # SISA
            idot   = payload[pos:pos+14].int ; pos += 14 # i-dot
            toc    = payload[pos:pos+14].uint; pos += 14 # t_{oc}
            af2    = payload[pos:pos+ 6].int ; pos +=  6 # a_{f2}
            af1    = payload[pos:pos+21].int ; pos += 21 # a_{f1}
            af0    = payload[pos:pos+31].int ; pos += 31 # a_{f0}
            crs    = payload[pos:pos+16].int ; pos += 16 # C_{rs}
            dn     = payload[pos:pos+16].int ; pos += 16 # delta n
            m0     = payload[pos:pos+32].int ; pos += 32 # M_0
            cuc    = payload[pos:pos+16].int ; pos += 16 # C_{uc}
            e      = payload[pos:pos+32].uint; pos += 32 # e
            cus    = payload[pos:pos+16].int ; pos += 16 # C_{us}
            a12    = payload[pos:pos+32].uint; pos += 32 # sqrt{a}
            toe    = payload[pos:pos+14].uint; pos += 14 # t_{oe}
            cic    = payload[pos:pos+16].int ; pos += 16 # C_{ic}
            omg0   = payload[pos:pos+32].int ; pos += 32 # Omega_0
            cis    = payload[pos:pos+16].int ; pos += 16 # C_{is}
            i0     = payload[pos:pos+32].int ; pos += 32 # i_0
            crc    = payload[pos:pos+16].int ; pos += 16 # C_{rc}
            omg    = payload[pos:pos+32].int ; pos += 32 # omega
            omgd0  = payload[pos:pos+24].int ; pos += 24 # Omega-dot 0
            bdg_e5ae1 = payload[pos:pos+10].int; pos += 10 # BGD_{E5a/E1}
            if mtype == 'F/NAV':
                os_hs = payload[pos:pos+2]; pos += 2 # open signal health
                os_vs = payload[pos:pos+1]; pos += 1 # open signal validity
                pos += 7                             # reserved
                if os_hs:
                    string += ' OS_health=' + self.msg_color.fg('red') + \
                        f'{os_hs.int}' + self.msg_color.fg()
                else:
                    string += f' OS_health={os_hs.int}'
                if os_vs:
                    string += self.msg_color.fg('red') + '*' + \
                        self.msg_color.fg()
            else:
                bgd_e5be1 = payload[pos:pos+10].int; pos += 10 # BGD_{E5b/E1}
                e5b_hs = payload[pos:pos+2]; pos += 2 # E5b signal health
                e5b_vs = payload[pos:pos+1]; pos += 1 # E5b data validity
                e1b_hs = payload[pos:pos+2]; pos += 2 # E1b signal health
                e1b_vs = payload[pos:pos+1]; pos += 1 # E1b signal validity
                pos += 2                              # reserved
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
            svid = payload[pos:pos+4].uint; pos += 4
            pos += 16 + 8 + 16 + 22 + 8 + 16 + 16 + 32 + 16 + 32 + \
                16 + 32 + 16 + 16 + 32 + 16 + 32 + 16 + 32 + 24 + \
                14 + 2
            wn = payload[pos:pos+10].uint; pos += 10
            pos += 4  # URA
            health = payload[pos:pos+6].uint; pos += 6
            string =f'J{svid:02d} WN={wn}'
            if health:  # to be determined: L1 C/B operation
                string +=' health=' + self.msg_color.fg('red') + \
                    f'{health:02x}' + self.msg_color.fg()
            else:
                string += f' health={health:02x}'
            pos += 8  # T_{GD}
            iodc = payload[pos:pos+10].uint
            string += f' IODC={iodc}'
            pos += 10
            pos += 1
        elif satsys == 'C':  # BeiDou ephemerides
            svid = payload[pos:pos+6].uint; pos += 6
            wn = payload[pos:pos+13].uint; pos += 13
            string =f'C{svid:02d} WN={wn}'
            pos += 4 + 14 + 5 + 17 + 11 + 22 + 24 + 5 + 18 + 16 + \
                32 + 18 + 32 + 18 + 32 + 17 + 18 + 32 + 18 + 32 + \
                18 + 32 + 24 + 10 + 10
            health = payload[pos:pos+1].uint; pos += 1
            if health:
                string += ' health=' + self.msg_color.fg('red') + \
                    f'{health:02x}' + self.msg_color.fg()
            else:
                string += f' health={health:02x}'
        elif satsys == 'I':  # NavIC ephemerides
            svid = payload[pos:pos+6].uint; pos += 6
            wn = payload[pos:pos+10].uint; pos += 10
            pos += 22 + 16 + 8 + 4 + 16 + 8 + 22
            # issue of data ephemeris & clock
            iodec = payload[pos:pos+8].uint; pos += 8
            string =f'I{svid:02d} WN={wn} IODEC={iodec}'
            pos += 10  # reserved bits after IODEC
            health = payload[pos:pos+1].uint; pos += 1 # L5_flag & S_flag
            if health:
                string += ' health=' + self.msg_color.fg('red') + \
                    f'{health:02x}' + self.msg_color.fg()
            else:
                string += f' health={health:02x}'
            pos += 15 + 15 + 15 + 15 + 15 + 15 + 14 + 32 + 16 + 32 + \
                32 + 32 + 32 + 22 + 32 + 2 + 2
        else:
            raise Exception(f'satsys={satsys}')
        return pos, string

# EOF
