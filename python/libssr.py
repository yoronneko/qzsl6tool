#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# libssr.py: library for SSR and compact SSR message processing
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022-2024 Satoshi Takahashi
#
# Released under BSD 2-clause license.
#
# References:
# [1] Cabinet Office of Japan, Quasi-Zenith Satellite System Interface
#     Specification Centimeter Level Augmentation Service,
#     IS-QZSS-L6-005, Sept. 21, 2022.
# [2] Global Positioning Augmentation Service Corporation (GPAS),
#     Quasi-Zenith Satellite System Correction Data on Centimeter Level
#     Augmentation Serice for Experiment Data Format Specification,
#     1st ed., Nov. 2017.
# [3] Cabinet Office of Japan, Quasi-Zenith Satellite System Interface
#     Specification Multi-GNSS Advanced Orbit and Clock Augmentation
#     - Precise Point Positioning, IS-QZSS-MDC-001, Feb., 2022.
# [4] Radio Technical Commission for Maritime Services (RTCM),
#     Differential GNSS (Global Navigation Satellite Systems) Services
#     - Version 3, RTCM Standard 10403.3, Apr. 24 2020.
# [5] European Union Agency for the Space Programme,
#     Galileo High Accuracy Service Signal-in-Space Interface Control
#     Document (HAS SIS ICD), Issue 1.0 May 2022.

import sys

import libtrace

try:
    import bitstring
except ModuleNotFoundError:
    libtrace.err('''\
    This code needs bitstring module.
    Please install this module such as \"pip install bitstring\".
    ''')
    sys.exit(1)

INVALID = 0  # invalid value indication for CSSR message show
#UI = [  # CSSR update interval [s] [3], Table 4.2.2-6
#    1, 2, 5, 10, 15, 30, 60, 120, 240, 300, 600, 900, 1800, \
#    3600, 7200, 10800]

HAS_VI = [  # HAS validity interval
    5, 10, 15, 20, 30, 60, 90, 120, 180, 240, 300, 600, 900, 1800, 3600, 0
]
FMT_ORB  = '7.4f'  # format string for orbit
FMT_CLK  = '7.3f'  # format string for clock
FMT_CB   = '7.3f'  # format string for code bias
FMT_PB   = '7.3f'  # format string for phase bias
FMT_TROP = '7.3f'  # format string for troposphere residual
FMT_TECU = '6.3f'  # format string for TECU
FMT_IODE = '4d'    # format string for issue of data ephemeris
FMT_GSIG = '13s'   # format string for GNSS signal name

class Ssr:
    """class of state space representation (SSR) and compact SSR process"""
    subtype    = 0      # subtype number
    ssr_nsat   = 0      # number of satellites
    ssr_mmi    = 0      # multiple message indicator
    ssr_iod    = 0      # iod ssr
    epoch      = 0      # epoch
    hepoch     = 0      # hourly epoch
    interval   = 0      # update interval
    mmi        = 0      # multiple message indication
    iod        = 0      # issue of data
    satsys     = []     # array of satellite system
    nsatmask   = []     # array of number of satellite mask
    nsigmask   = []     # array of number of signal mask
    cellmask   = []     # array of cell mask
    gsys       = {}     # dict of sat   name from system name
    gsig       = {}     # dict of sigal name from system name
    stat       = False  # statistics output
    stat_nsat  = 0      # stat: number of satellites
    stat_nsig  = 0      # stat: number of signals
    stat_bsat  = 0      # stat: bit number of satellites
    stat_bsig  = 0      # stat: bit number of signals
    stat_both  = 0      # stat: bit number of other information
    stat_bnull = 0      # stat: bit number of null

    def __init__(self, trace):
        self.trace = trace

    def ssr_decode_head(self, payload, satsys, mtype):
        ''' stores ssr_epoch, ssr_interval, ssr_mmi, ssr_iod, ssr_nsat'''
        # bit format of ssr_epoch changes according to satellite system
        bw = 'u20' if satsys != 'R' else 'u17'
        self.ssr_epoch     = payload.read(  bw )  # epoch time
        self.ssr_interval  = payload.read( 'u4')  # ssr update interval
        self.ssr_mmi       = payload.read( 'u1')  # multiple msg ind
        if mtype == 'SSR orbit' or mtype == 'SSR obt/clk':
            self.ssr_sdat  = payload.read( 'u1')  # sat ref datum
        self.ssr_iod       = payload.read( 'u4')  # iod ssr
        self.ssr_pid       = payload.read('u16')  # ssr provider id
        self.ssr_sid       = payload.read( 'u4')  # ssr solution id
        # bit format of nsat changes with satsys
        bw = 'u6' if satsys != 'J' else 'u4'
        self.ssr_nsat      = payload.read(  bw )

    def ssr_decode_orbit(self, payload, satsys):
        ''' decodes SSR orbit correction and returns string '''
        strsat = ''
        # bit format of satid changes according to satellite system
        if   satsys == 'J': bw = 'u4'  # ref. [2]
        elif satsys == 'R': bw = 'u5'  # ref. [1]
        else:               bw = 'u6'  # ref. [1]
        for i in range(self.ssr_nsat):
            satid  = payload.read(  bw )  # satellite ID, DF068
            iode   = payload.read( 'u8')  # IODE, DF071
            drad   = payload.read('i22')  # delta radial, DF365
            daln   = payload.read('i20')  # delta along track, DF366
            dcrs   = payload.read('i20')  # delta cross track, DF367
            ddrad  = payload.read('i21')  # d_delta radial, DF368
            ddaln  = payload.read('i19')  # d_delta along track, DF369
            ddcrs  = payload.read('i19')  # d_delta cross track, DF370
            vdrad  = drad  * 1e-4         # 0.1   mm   (1e-4 m)
            vdaln  = daln  * 4e-4         # 0.4   mm   (4e-4 m)
            vdcrs  = dcrs  * 4e-5         # 0.4   mm   (4e-4 m)
            vddrad = ddrad * 1e-6         # 0.001 mm/s (1e-6 m/s)
            vddaln = ddaln * 4e-6         # 0.004 mm/s (4e-6 m/s)
            vddcrs = ddcrs * 4e-6         # 0.004 mm/s (4e-6 m/s)
            strsat += f"{satsys}{satid:02} "
            self.trace.show(1, f'{satsys}{satid:02d} d_radial={vdrad:{FMT_ORB}}m d_along={vdaln:{FMT_ORB}}m d_cross={vdcrs:{FMT_ORB}}m dot_d_radial={vddrad:{FMT_ORB}}m/s dot_d_along={vddaln:{FMT_ORB}}m/s dot_d_cross={vddcrs:{FMT_ORB}}m/s')
        string = f"{strsat}(nsat={self.ssr_nsat} iod={self.ssr_iod}" + \
                      f"{' cont.' if self.ssr_mmi else ''})"
        return string

    def ssr_decode_clock(self, payload, satsys):
        ''' decodes SSR clock correction and returns string '''
        # bit format of satid changes according to satellite system
        if   satsys == 'J': bw = 'u4'  # ref. [2]
        elif satsys == 'R': bw = 'u5'  # ref. [1]
        else              : bw = 'u6'  # ref. [1]
        strsat = ''
        for _ in range(self.ssr_nsat):
            satid = payload.read(  bw )  # satellite ID
            c0    = payload.read('i22')  # delta clock c0, DF376
            c1    = payload.read('i21')  # delta clock c1, DF377
            c2    = payload.read('i27')  # delta clock c2, DF378
            vc0   = c0 * 1e-4            # 0.1     mm     (1e-4 m)
            vc1   = c1 * 1e-6            # 0.001   mm/s   (1e-7 m/s)
            vc2   = c2 * 2e-9            # 0.00002 mm/s^2 (2e-9 m/s^2)
            strsat += f"{satsys}{satid:02d} "
            self.trace.show(1, f'{satsys}{satid:02d} c0={vc0:{FMT_CLK}}m, c1={vc1:{FMT_CLK}}m, c2={vc2:{FMT_CLK}}m')
        string = f"{strsat}(nsat={self.ssr_nsat} iod={self.ssr_iod}" + \
                      f"{' cont.' if self.ssr_mmi else ''})"
        return string

    def ssr_decode_code_bias(self, payload, satsys):
        ''' decodes SSR code bias and returns string '''
        # bit format of satid changes according to satellite system
        if   satsys == 'J': bw = 'u4'   # ref. [2]
        elif satsys == 'R': bw = 'u5'   # ref. [1]
        else              : bw = 'u6'   # ref. [1]
        strsat = ''
        for _ in range(self.ssr_nsat):
            satid = payload.read( bw )  # satellite ID, DF068, ...
            ncb   = payload.read('u5')  # code bias number, DF383
            strsat += f"{satsys}{satid:02d} "
            for j in range(ncb):
                stmi  = payload.read( 'u5')  # sig&trk mode ind, DF380
                cb    = payload.read('i14')  # code bias, DF383
                vcb   = cb * 1e-2
                sstmi = sigmask2signame(satsys, stmi)
                self.trace.show(1, f'{satsys}{satid:02d} {sstmi:{FMT_GSIG}} code_bias={vcb:{FMT_CB}}m')
        string = f"{strsat}(nsat={self.ssr_nsat} iod={self.ssr_iod}" + \
                      f"{' cont.' if self.ssr_mmi else ''})"
        return string

    def ssr_decode_ura(self, payload, satsys):
        ''' decodes SSR user range accuracy and returns string '''
        # bit format of satid changes according to satellite system
        if   satsys == 'J': bw = 'u4'  # ref. [2]
        elif satsys == 'R': bw = 'u5'  # ref. [1]
        else              : bw = 'u6'  # ref. [1]
        strsat = ''
        for i in range(self.ssr_nsat):
            satid = payload.read(bw)  # satellite ID, DF068
            ura   = payload.read( 6)  # user range accuracy, DF389
            if   ura.bin == 0b000000:   # undefined or unknown
                vura = INVALID
            elif ura.bin == 0b111111:   # URA more than 5466.5 mm
                vura = INVALID
            else:
                cls  = ura[4:7].uint
                val  = ura[0:4].uint
                vura = 3 ** cls * (1 + val / 4) - 1
            self.trace.show(1, f'{satsys}{satid:02d} ura={vura:7.2f} mm')
            strsat += f"{satsys}{satid:02} "
        string = f"{strsat}(nsat={self.ssr_nsat} iod={self.ssr_iod}" + \
                      f"{' cont.' if self.ssr_mmi else ''})"
        return string

    def ssr_decode_hr_clock(self, payload, satsys):
        '''decodes SSR high rate clock and returns string'''
        # bit format of satid changes according to satellite system
        if   satsys == 'J': bw = 'u4'
        elif satsys == 'R': bw = 'u5'
        else              : bw = 'u6'
        strsat = ''
        for _ in range(self.ssr_nsat):
            satid = payload.read(  bw )  # satellite ID
            hrc   = payload.read('i22')  # high rate clock
            vhrc  = hrc * 1e-4          # 0.1mm (DF390) or 1e-4 m
            strsat += f"{satsys}{satid:02} "
            self.trace.show(1, f'{satsys}{satid:02} high_rate_clock={vhrc:{FMT_CLK}}m')
        string = f"{strsat}(nsat={self.ssr_nsat} iod={self.ssr_iod}" + \
                      f"{' cont.' if self.ssr_mmi else ''})"
        return string

    def decode_cssr(self, payload):
        ''' calls cssr decode functions and returns True if success '''
        if not self.decode_cssr_head(payload):
            return 'Could not decode CSSR header'
        if self.subtype == 1:
            self.decode_cssr_st1(payload)
        elif self.subtype == 2:
            self.decode_cssr_st2(payload)
        elif self.subtype == 3:
            self.decode_cssr_st3(payload)
        elif self.subtype == 4:
            self.decode_cssr_st4(payload)
        elif self.subtype == 5:
            self.decode_cssr_st5(payload)
        elif self.subtype == 6:
            self.decode_cssr_st6(payload)
        elif self.subtype == 7:
            self.decode_cssr_st7(payload)
        elif self.subtype == 8:
            self.decode_cssr_st8(payload)
        elif self.subtype == 9:
            self.decode_cssr_st9(payload)
        elif self.subtype == 10:
            self.decode_cssr_st10(payload)
        elif self.subtype == 11:
            self.decode_cssr_st11(payload)
        elif self.subtype == 12:
            self.decode_cssr_st12(payload)
        else:
            raise Exception(f"unknown CSSR subtype: {self.subtype}")
        string = f'ST{self.subtype:<2d}'
        if self.subtype == 1:
            string += f' epoch={self.epoch} iod={self.iod}'
        else:
            string += f' hepoch={self.hepoch} iod={self.iod}'
        return string

    def show_cssr_stat(self):
        bit_total = self.stat_bsat + self.stat_bsig + self.stat_both + \
                self.stat_bnull
        msg = f'stat n_sat {self.stat_nsat} n_sig {self.stat_nsig} ' + \
              f'bit_sat {self.stat_bsat} bit_sig {self.stat_bsig} ' + \
              f'bit_other {self.stat_both} bit_null {self.stat_bnull} ' + \
              f'bit_total {bit_total}'
        self.trace.show(0, msg)

    def decode_cssr_head(self, payload):
        ''' decode CSSR header and returns True if success '''
        if payload.all(0):  # payload is zero padded
            self.trace.show(2, f"CSSR null data {len(payload.bin)} bits")
            self.subtype = 0  # no subtype number
            return False
        len_payload = len(payload)
        if len_payload < 12:
            self.msgnum  = 0  # could not retreve the message number
            self.subtype = 0  # could not retreve the subtype number
            return False
        self.msgnum = payload.read('u12')
        if self.msgnum != 4073:  # CSSR message number should be 4073
            self.trace.show(2, f"CSSR msgnum should be 4073 ({self.msgnum})" + \
                f"{len(payload.bin)} bits\nCSSR dump: {payload.bin}\n")
            self.subtype = 0  # no subtype number
            return False
        if len_payload < payload.pos + 4:
            self.subtype = 0  # could not retreve the subtype number
            return False
        self.subtype = payload.read('u4')  # subtype
        if self.subtype == 1:  # Mask message
            if len_payload < payload.pos + 20:  # could not retreve the epoch
                return False
            self.epoch = payload.read('u20')  # GPS epoch time 1s
        elif self.subtype == 10:  # Service Information
            return True
        else:
            if len_payload < payload.pos + 12:  # could not retreve hourly epoch
                return False
            self.hepoch = payload.read('u12')  # GNSS hourly epoch
        if len_payload < payload.pos + 4 + 1 + 4:
            return False
        self.interval = payload.read('u4')  # update interval
        self.mmi      = payload.read('u1')  # multi msg ind
        self.iod      = payload.read('u4')  # SSR issue of data
        return True

    def _decode_mask(self, payload, ssr_type):
        ''' decode mask information and returns True if success
            ssr_type: cssr or has
        '''
        if ssr_type not in {'cssr', 'has'}:
            raise Exception(f'unknown ssr_type: {ssr_type}')
        len_payload = len(payload)
        if len_payload < payload.pos + 4:
            return False
        ngnss = payload.read('u4')  # numer of GNSS
        if len_payload < payload.pos + 61 * ngnss:
            return False
        satsys   = [None for i in range(ngnss)]
        nsatmask = [None for i in range(ngnss)]
        nsigmask = [None for i in range(ngnss)]
        cellmask = [None for i in range(ngnss)]
        navmsg   = [None for i in range(ngnss)]
        gsys     = {}
        gsig     = {}
        for ignss in range(ngnss):
            ugnssid   = payload.read('u4')
            bsatmask  = payload.read( 40 )
            bsigmask  = payload.read( 16 )
            cmavail   = payload.read('u1')
            t_satsys  = gnssid2satsys(ugnssid)
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
                    t_gsig.append(sigmask2signame(t_satsys, i))
            ncell = t_satmask * t_sigmask
            if cmavail:
                bcellmask = payload.read(ncell)
            else:
                bcellmask = bitstring.ConstBitStream('0b1') * ncell
            nm = 0  # navigation message (HAS)
            if ssr_type == 'has':
                nm = payload.read('u3')
            cellmask[ignss]    = bcellmask  # cell mask
            satsys  [ignss]    = t_satsys   # satellite system
            nsatmask[ignss]    = t_satmask  # satellite mask
            nsigmask[ignss]    = t_sigmask  # signal mask
            gsys    [t_satsys] = t_gsys     # GNSS system
            gsig    [t_satsys] = t_gsig     # GNSS signal
            navmsg  [ignss]    = nm         # navigation message (HAS)
        if ssr_type == 'has':
            payload.pos += 6       # reserved
        self.satsys    = satsys    # satellite system
        self.nsatmask  = nsatmask  # number of satellite mask
        self.nsigmask  = nsigmask  # number of signal mask
        self.cellmask  = cellmask  # cell mask
        self.gsys      = gsys      # dict of sat   name from system name
        self.gsig      = gsig      # dict of sigal name from system name
        self.stat_nsat = 0
        self.stat_nsig = 0
        msg_trace1 = ''
        for i, satsys in enumerate(self.satsys):
            pos_mask = 0  # mask position
            for j, gsys in enumerate(self.gsys[satsys]):
                self.stat_nsat += 1
                if ssr_type == 'cssr':
                    msg_trace1 += 'ST1 ' + gsys
                else:
                    msg_trace1 += 'MASK ' + gsys
                for gsig in self.gsig[satsys]:
                    mask = self.cellmask[i][pos_mask]; pos_mask += 1
                    if not mask:
                        continue
                    msg_trace1 += ' ' + gsig
                    self.stat_nsig += 1
                msg_trace1 += '\n'
            if ssr_type == 'has' and navmsg[i] != 0:
                msg_trace1 += '\n{satsys}: NavMsg should be zero.\n'
        self.trace.show(1, msg_trace1, end='')
        if self.stat:
            self.show_cssr_stat()
        self.stat_bsat  = 0
        self.stat_bsig  = 0
        self.stat_both  = payload.pos
        self.stat_bnull = 0
        return True

    def decode_cssr_st1(self, payload):
        ''' decode CSSR ST1 mask message and returns True if success '''
        return self._decode_mask(payload, 'cssr')

    def decode_has_mask(self, has_msg):
        ''' decode HAS mask message and returns True if success '''
        return self._decode_mask(has_msg, 'has')

    def decode_cssr_st2(self, payload):
        ''' decode CSSR ST2 orbit message and returns True if success '''
        len_payload = len(payload)
        stat_pos    = payload.pos
        msg_trace1  = ''
        for satsys in self.satsys:
            bw = 10 if satsys == 'E' else 8  # IODE bit width
            for gsys in self.gsys[satsys]:
                if len_payload < payload.pos + bw + 15 + 13 + 13:
                    return False
                fbw  = f'u{bw}'
                iode = payload.read( fbw )
                rad  = payload.read('i15')  # radial
                alg  = payload.read('i13')  # along
                crs  = payload.read('i13')  # cros
                vrad = rad * 0.0016 if rad != -16384 else INVALID
                valg = alg * 0.0064 if alg != -16384 else INVALID
                vcrs = crs * 0.0064 if crs != -16384 else INVALID
                msg_trace1 += \
                    f'ST2 {gsys} IODE={iode:{FMT_IODE}} ' + \
                    f'd_radial={vrad:{FMT_ORB}}m ' + \
                    f'd_along={ valg:{FMT_ORB}}m ' + \
                    f'd_cross={ vcrs:{FMT_ORB}}m\n'
        self.trace.show(1, msg_trace1, end='')
        self.stat_both += stat_pos
        self.stat_bsat += payload.pos - stat_pos
        return True

    def decode_has_orbit(self, payload):
        ''' decode HAS orbit message and returns True if success '''
        len_payload = len(payload)
        stat_pos    = payload.pos
        if len_payload < payload.pos + 4:
            return False
        vi = payload.read('u4')
        msg_trace1 = f'ORBIT validity_interval={HAS_VI[vi]}s ({vi})\n'
        for satsys in self.satsys:
            if satsys == 'E': bw = 10
            else            : bw =  8
            for gsys in self.gsys[satsys]:
                if len_payload < payload.pos + bw + 13 + 12 + 12:
                    return False
                fbw  = f'u{bw}'
                iode = payload.read(fbw)
                rad  = payload.read( 13)  # radial
                alg  = payload.read( 12)  # along
                crs  = payload.read( 12)  # cross
                vrad = rad.int * 0.0025 \
                    if rad.bin != '1000000000000' else INVALID
                valg = alg.int * 0.0080 \
                    if alg.bin  != '100000000000'  else INVALID
                vcrs = crs.int * 0.0080 \
                    if crs.bin  != '100000000000'  else INVALID
                msg_trace1 += \
                    f'ORBIT {gsys} IODE={iode:{FMT_IODE}} ' + \
                    f'd_radial={vrad:{FMT_ORB}}m ' + \
                    f'd_track={ valg :{FMT_ORB}}m ' + \
                    f'd_cross={ vcrs :{FMT_ORB}}m\n'
        self.trace.show(1, msg_trace1, end='')
        self.stat_both += stat_pos
        self.stat_bsat += payload.pos - stat_pos
        return True

    def decode_cssr_st3(self, payload):
        ''' decode CSSR ST3 clock message and returns True if success '''
        len_payload = len(payload)
        stat_pos    = payload.pos
        msg_trace1 = ''
        for satsys in self.satsys:
            for gsys in self.gsys[satsys]:
                if len_payload < payload.pos + 15:
                    return False
                c0  = payload.read('i15')
                vc0 = c0 * 0.0016 if c0 != -16384 else INVALID
                msg_trace1 += f"ST3 {gsys} d_clock={vc0:{FMT_CLK}}m\n"
        self.trace.show(1, msg_trace1, end='')
        self.stat_both += stat_pos
        self.stat_bsat += payload.pos - stat_pos
        return True

    def decode_has_ckful(self, payload):
        ''' decode HAS clock full message and returns True if success '''
        len_payload = len(payload)
        stat_pos    = payload.pos
        if len_payload < payload.pos + 4:
            return False
        vi = payload.read('u4')
        msg_trace1 = f'CKFUL validity_interval={HAS_VI[vi]}s ({vi})\n'
        if len_payload < payload.pos + 2 * len(self.satsys):
            return False
        multiplier = [1 for i in range(len(self.satsys))]
        for i, satsys in enumerate(self.satsys):
            multiplier[i] = payload.read('u2') + 1
        for i, satsys in enumerate(self.satsys):
            for gsys in self.gsys[satsys]:
                if len_payload < payload.pos + 13:
                    return False
                c0 = payload.read(13)
                if   c0.bin == '1000000000000':  # not available
                    vc0 = INVALID
                elif c0.bin == '0111111111111':  # the sat shall not be used
                    vc0 = INVALID
                else:
                    vc0 = c0.int * 0.0025 * multiplier[i]
                msg_trace1 += f"CKFUL {gsys} d_clock={vc0:{FMT_CLK}}m (multiplier={multiplier[i]})\n"
        self.trace.show(1, msg_trace1, end='')
        self.stat_both += stat_pos
        self.stat_bsat += payload.pos - stat_pos
        return True

    def decode_has_cksub(self, payload):
        ''' decode HAS clock subset message and returns True if success '''
        len_payload = len(payload)
        stat_pos    = payload.pos
        if len_payload < payload.pos + 4 + 2:
            return False
        vi = payload.read('u4')
        ns = payload.read('u2')  # GNSS subset number
        msg_trace1 = f'CKFUL validity_interval={HAS_VI[vi]}s ({vi}), n_sub={ns}\n'
        for i in range(ns):
            if len_payload < payload.pos + 6:
                return False
            satsys        = payload.read('u4')
            multiplier[i] = payload.read('u2') + 1
            if len_payload < payload.pos + 13:
                return False
            c0 = payload.read(13)
            if   c0.bin == '1000000000000':  # not available
                vc0 = INVALID
            elif c0.bin == '0111111111111':  # the sat shall not be used
                vc0 = INVALID
            else:
                vc0 = c0.int * 0.0025 * multiplier[i]
            msg_trace1 += f"CKSUB {gsys} d_clock={vc0:{FMT_CLK}}m (x{multiplier[i]})\n"
        self.trace.show(1, msg_trace1, end='')
        self.stat_both += stat_pos
        self.stat_bsat += payload.pos - stat_pos
        return True

    def _decode_code_bias(self, payload, ssr_type):
        ''' decode code bias information and returns True if success
            ssr_type: cssr or has
        '''
        if ssr_type not in {'cssr', 'has'}:
            raise Exception(f'unknow ssr_type: {ssr_type}')
        nsigsat = 0  # Nsig * Nsat
        for i, satsys in enumerate(self.satsys):
            pos_mask = 0  # mask position
            for gsys in self.gsys[satsys]:
                for gsig in self.gsig[satsys]:
                    mask = self.cellmask[i][pos_mask]; pos_mask += 1
                    if not mask:
                        continue
                    nsigsat += 1
        len_payload = len(payload)
        stat_pos    = payload.pos
        msg_trace1 = ''
        if ssr_type == 'has':
            if len_payload < payload.pos + 4:
                return False
            vi = payload.read('u4')
            msg_trace1 = f'CBIAS validity_interval={HAS_VI[vi]}s ({vi})\n'
        if len(payload) < payload.pos + 11 * nsigsat:
            return False
        for i, satsys in enumerate(self.satsys):
            pos_mask = 0  # mask position
            for j, gsys in enumerate(self.gsys[satsys]):
                for k, gsig in enumerate(self.gsig[satsys]):
                    mask = self.cellmask[i][pos_mask]; pos_mask += 1
                    if not mask:
                        continue
                    cb  = payload.read('i11')
                    vcb = cb * 0.02 if cb != -1024 else INVALID
                    if ssr_type == "cssr": msg_trace1 += "ST4"
                    else                 : msg_trace1 += "CBIAS"
                    msg_trace1 += f" {gsys} {gsig:{FMT_GSIG}} code_bias={vcb:{FMT_CB}}m\n"
        self.trace.show(1, msg_trace1, end='')
        self.stat_both += stat_pos
        self.stat_bsig += payload.pos - stat_pos
        return True

    def decode_cssr_st4(self, payload):
        ''' decode CSSR ST4 code bias message and returns True if success '''
        return self._decode_code_bias(payload, 'cssr')

    def decode_has_cbias(self, payload):
        ''' decode HAS code bias message and returns True if success '''
        return self._decode_code_bias(payload, 'has')

    def decode_cssr_st5(self, payload):
        ''' decode CSSR ST5 phase bias message and returns True if success '''
        len_payload = len(payload)
        stat_pos    = payload.pos
        msg_trace1  = ''
        for i, satsys in enumerate(self.satsys):
            pos_mask = 0
            for gsys in self.gsys[satsys]:
                for gsig in self.gsig[satsys]:
                    mask = self.cellmask[i][pos_mask]; pos_mask += 1
                    if not mask:
                        continue
                    if len_payload < payload.pos + 15 + 2:
                        return False
                    pb  = payload.read('i15')
                    di  = payload.read( 'u2')
                    vpb = pb * 0.001 if pb != -16384 else INVALID
                    msg_trace1 += \
                        f'ST5 {gsys} {gsig:{FMT_GSIG}}' + \
                        f' phase_bias={vpb:{FMT_PB}}m' + \
                        f' discont_indicator={di}\n'
        self.trace.show(1, msg_trace1, end='')
        self.stat_both += stat_pos
        self.stat_bsig += payload.pos - stat_pos
        return True

    def decode_has_pbias(self, payload):
        ''' decode HAS phase bias message and returns True if success '''
        len_payload = len(payload)
        stat_pos    = payload.pos
        if len_payload < payload.pos + 4:
            return False
        vi = payload.read('u4')
        msg_trace1 = f'PBIAS validity_interval={HAS_VI[vi]}s ({vi})\n'
        for i, satsys in enumerate(self.satsys):
            pos_mask = 0
            for gsys in self.gsys[satsys]:
                for gsig in self.gsig[satsys]:
                    mask = self.cellmask[i][pos_mask]; pos_mask += 1
                    if not mask:
                        continue
                    if len_payload < payload.pos + 11 + 2:
                        return False
                    pb  = payload.read('i11')
                    di  = payload.read( 'u2')
                    vpb = pb * 0.01 if pb != -1024 else INVALID
                    msg_trace1 += \
                        f'PBIAS {gsys} {gsig:{FMT_GSIG}}' + \
                        f' phase_bias={vpb:{FMT_PB}}cycle' + \
                        f' discont_indicator={di}\n'
        self.trace.show(1, msg_trace1, end='')
        self.stat_both += stat_pos
        self.stat_bsig += payload.pos - stat_pos
        return True

    def decode_cssr_st6(self, payload):
        ''' decode CSSR ST6 network bias message and returns True if success '''
        len_payload = len(payload)
        stat_pos    = payload.pos
        if len_payload < 45:
            return False
        f_cb = payload.read('u1')  # code    bias existing flag
        f_pb = payload.read('u1')  # phase   bias existing flag
        f_nb = payload.read('u1')  # network bias existing flag
        svmask = {}
        cnid = 0
        for satsys in self.satsys:
            bcellmask = bitstring.ConstBitStream('0b1') * len(self.gsys[satsys])
        msg_trace1 = \
            f"ST6 code_bias={'on' if f_cb else 'off'}" + \
            f" phase_bias={  'on' if f_pb else 'off'}" + \
            f" network_bias={'on' if f_nb else 'off'}\n"
        if f_nb:
            cnid = payload.read('u5')  # compact network ID
            msg_trace1 += f"ST6 NID={cnid}\n"
            for satsys in self.satsys:
                ngsys = len(self.gsys[satsys])
                if len_payload < payload.pos + ngsys:
                    return False
                svmask[satsys] = payload.read(ngsys)
        for i, satsys in enumerate(self.satsys):
            pos_mask = 0  # mask position
            for j, gsys in enumerate(self.gsys[satsys]):
                for gsig in self.gsig[satsys]:
                    mask = self.cellmask[i][pos_mask]; pos_mask += 1
                    if not svmask[satsys][j] or not mask:
                        continue
                    msg_trace1 += f"ST6 {gsys} {gsig:{FMT_GSIG}}"
                    if f_cb:
                        if len_payload < payload.pos + 11:
                            return False
                        cb  = payload.read('i11')  # code bias
                        vcb = cb * 0.02 if cb != -1024 else INVALID
                        msg_trace1 += f" code_bias={vcb:{FMT_CB}}m"
                    if f_pb:
                        if len_payload < payload.pos + 15 + 2:
                            return False
                        pb  = payload.read('i15')  # phase bias
                        di  = payload.read( 'u2')  # disc ind
                        vpb = pb * 0.001 if pb != -16384 else INVALID
                        msg_trace1 += \
                            f" phase_bias={vpb:{FMT_PB}}m discont_indi={di}"
                    msg_trace1 += '\n'
        self.trace.show(1, msg_trace1, end='')
        self.stat_both += stat_pos + 3
        self.stat_bsig += payload.pos - stat_pos - 3
        return True

    def decode_cssr_st7(self, payload):
        ''' decode CSSR ST7 user range accuracy message and returns True if success '''
        len_payload = len(payload)
        stat_pos    = payload.pos
        if len_payload < 37:
            return False
        msg_trace1 = ''
        for satsys in self.satsys:
            for gsys in self.gsys[satsys]:
                if len_payload < payload.pos + 6:
                    return False
                ura  = payload.read(6)     # [3], Sect.4.2.2.7
                if   ura.bin == 0b000000:  # undefined or unknown
                    vura = INVALID
                elif ura.bin == 0b111111:  # URA more than 5466.5 mm
                    vura = INVALID
                else:
                    cls  = ura[4:7].uint
                    val  = ura[0:4].uint
                    vura = 3 ** cls * (1 + val / 4) - 1
                msg_trace1 += f"ST7 {gsys} URA {vura:7.2f} mm\n"
        self.trace.show(1, msg_trace1, end='')
        self.stat_both += stat_pos
        self.stat_bsat += payload.pos - stat_pos
        return True

    def decode_cssr_st8(self, payload):
        ''' decode CSSR ST8 STEC message and returns True if success '''
        len_payload = len(payload)
        stat_pos    = payload.pos
        if len_payload < 44:
            return False
        stec_type = payload.read('u2')  # STEC correction type
        cnid      = payload.read('u5')  # compact network ID
        svmask = {}
        for satsys in self.satsys:
            ngsys = len(self.gsys[satsys])
            if len_payload < payload.pos + ngsys:
                return False
            svmask[satsys] = payload.read(ngsys)
        msg_trace1 = ''
        for satsys in self.satsys:
            for i, gsys in enumerate(self.gsys[satsys]):
                if not svmask[satsys][i]:
                    continue
                if len_payload < payload.pos + 6 + 14:
                    return False
                qi   = payload.read( 'u6')  # quality indicator
                c00  = payload.read('i14')
                vc00 = c00 * 0.05 if c00 != -8192 else INVALID
                msg_trace1 += f"ST8 {gsys} c00={vc00:{FMT_TECU}}TECU"
                if 1 <= stec_type:
                    if len_payload < payload.pos + 12 + 12:
                        return False
                    c01  = payload.read('i12')
                    c10  = payload.read('i12')
                    vc01 = c01 * 0.02 if c01 != -2048 else INVALID
                    vc10 = c10 * 0.02 if c10 != -2048 else INVALID
                    msg_trace1 += \
                        f" c01={vc01:{FMT_TECU}}TECU/deg c10={vc10:{FMT_TECU}}TECU/deg"
                if 2 <= stec_type:
                    if len_payload < payload.pos + 10:
                        return False
                    c11  = payload.read('i10')
                    vc11 = c11 * 0.02 if c11 != -512 else INVALID
                    msg_trace1 += f" c11={vc11:{FMT_TECU}}TECU/deg^2"
                if 3 <= stec_type:
                    if len_payload < payload.pos + 8 + 8:
                        return False
                    c02  = payload.read('i8')
                    c20  = payload.read('i8')
                    vc02 = c02 * 0.005 if c02 != -128 else INVALID
                    vc20 = c20 * 0.005 if c20 != -128 else INVALID
                    msg_trace1 += \
                        f" c02={vc02:{FMT_TECU}}TECU/deg^2 c20={vc20:{FMT_TECU}}TECU/deg^2"
                msg_trace1 += '\n'
        self.trace.show(1, msg_trace1, end='')
        self.stat_both += stat_pos + 7
        self.stat_bsat += payload.pos - stat_pos - 7
        return True

    def decode_cssr_st9(self, payload):
        ''' decode CSSR ST9 trop correction message and returns True if success '''
        len_payload = len(payload)
        if len_payload < 45:
            return False
        tctype = payload.read('u2')  # trop correction type
        crange = payload.read('u1')  # trop correction range
        bw = 16 if crange else 7
        cnid   = payload.read('u5')  # compact network ID
        svmask = {}
        for satsys in self.satsys:
            ngsys = len(self.gsys[satsys])
            if len_payload < payload.pos + ngsys:
                return False
            svmask[satsys] = payload.read(ngsys)
        if len_payload < payload.pos + 6 + 6:
            return False
        tqi   = payload.read('u6')  # tropo quality indicator
        ngrid = payload.read('u6')  # number of grids
        msg_trace1 = \
            f"ST9 Trop correct_type={tctype}" + \
            f" NID={cnid} quality={tqi} ngrid={ngrid}\n"
        for i in range(ngrid):
            if len_payload < payload.pos + 9 + 8:
                return False
            vd_h = payload.read('i9')  # hydrostatic vert delay
            vd_w = payload.read('i8')  # wet vert delay
            vvd_h  = vd_h * 0.004 if vd_h != -256 else INVALID
            vvd_w  = vd_w * 0.004 if vd_w != -128 else INVALID
            msg_trace1 += \
                f'ST9 Trop     grid {i+1:2d}/{ngrid:2d}' + \
                f' dry-delay={vvd_h:6.3f}m wet-delay={vvd_w:6.3f}m\n'
            for satsys in self.satsys:
                for j, gsys in enumerate(self.gsys[satsys]):
                    if not svmask[satsys][j]:
                        continue
                    if len_payload < payload.pos + bw:
                        return False
                    fbw  = f'i{bw}'
                    res  = payload.read(fbw)  # residual
                    vres = res * 0.04
                    if (crange == 1 and res == -32767) or \
                       (crange == 0 and res == -64):
                        residual = INVALID
                    msg_trace1 += \
                        f'ST9 STEC {gsys} grid {i+1:2d}/{ngrid:2d}' + \
                        f' residual={vres:{FMT_TECU}}TECU ({bw}bit)\n'
        self.trace.show(1, msg_trace1, end='')
        self.stat_both += payload.pos
        return True

    def decode_cssr_st10(self, payload):
        ''' decode CSSR ST10 auxiliary message and returns True if success '''
        len_payload = len(payload)
        if len_payload < 5:
            return False
        counter = payload.read('u3')  # info message counter
        dsize   = payload.read('u2')  # data size
        vdsize  = (dsize + 1) * 40
        if len_payload < payload.pos + vdsize:
            return False
        aux_frame_data = payload.read(vdsize)
        self.trace.show(1, f'ST10 {counter}:{aux_frame_data.hex}')
        self.stat_both += payload.pos
        return True

    def decode_cssr_st11(self, payload):
        ''' decode CSSR ST11 network correction message and returns True if success '''
        len_payload = len(payload)
        stat_pos    = payload.pos
        if len_payload < 40:
            return False
        f_o = payload.read('u1')  # orbit existing flag
        f_c = payload.read('u1')  # clock existing flag
        f_n = payload.read('u1')  # network correction
        msg_trace1 = \
            f"ST11 Orb={'on' if f_o else 'off'} " + \
            f"Clk={     'on' if f_c else 'off'} " + \
            f"Net={     'on' if f_n else 'off'}\n"
        if f_n:
            if len_payload < payload.pos + 5:
                return False
            cnid = payload.read('u5')  # compact network ID
            msg_trace1 += f"ST11 NID={cnid}\n"
            svmask = {}
            for satsys in self.satsys:
                ngsys = len(self.gsys[satsys])
                if len_payload < payload.pos + ngsys:
                    return False
                svmask[satsys] = payload.read(ngsys)
            for satsys in self.satsys:
                for i, gsys in enumerate(self.gsys[satsys]):
                    if not svmask[satsys][i]:
                        continue
                    msg_trace1 += f"ST11 {gsys}"
                    if f_o:
                        bw = 10 if satsys == 'E' else 8  # IODE width
                        if len_payload < payload.pos + bw + 15 + 13 + 13:
                            return False
                        fbw  = f'u{bw}'
                        iode = payload.read(fbw)
                        rad  = payload.read('i15')  # radial
                        alg  = payload.read('i13')  # along
                        crs  = payload.read('i13')  # cross
                        vrad = rad * 0.0016 if rad != -16384 else INVALID
                        valg = alg * 0.0064 if alg !=  -4096 else INVALID
                        vcrs = crs * 0.0064 if crs !=  -4096 else INVALID
                        msg_trace1 += \
                            f' IODE={iode:{FMT_IODE}} ' + \
                            f'd_radial={vrad:{FMT_ORB}}m ' + \
                            f'd_along={ valg:{FMT_ORB}}m ' + \
                            f'd_cross={ vcrs:{FMT_ORB}}m'
                    if f_c:
                        if len_payload < payload.pos + 15:
                            return 0
                        c0  = payload.read('i15')
                        vc0 = c0 * 0.0016 if c0 != -16384 else INVALID
                        msg_trace1 += f" c0={vc0:{FMT_CLK}}m"
                    msg_trace1 += "\n"
        self.trace.show(1, msg_trace1, end='')
        self.stat_both += stat_pos + 3
        self.stat_bsat += payload.pos - stat_pos - 3
        if f_n:  # correct bit number because because we count up bsat as NID
            self.stat_both += 5
            self.stat_bsat -= 5
        return True

    def decode_cssr_st12(self, payload):
        ''' decode CSSR ST12 network and troposphere corrections message and returns True if success '''
        len_payload = len(payload)
        if len_payload < 52:
            return False
        tropo = payload.read(  2 )  # tropo correction avail
        stec  = payload.read(  2 )  # STEC correction avail
        cnid  = payload.read('u5')  # compact network ID
        ngrid = payload.read('u6')  # number of grids
        msg_trace1 = \
            f"ST12 tropo={tropo} stec={stec} NID={cnid} ngrid={ngrid}\n" + \
            "ST12 Trop"
        if tropo[0]:
            # 0 <= ttype (forward reference)
            if len_payload < payload.pos + 6 + 2 + 9:
                return False
            tqi   = payload.read( 'u6')  # tropo quality ind
            ttype = payload.read( 'u2')  # tropo correction type
            t00   = payload.read( 'i9')  # tropo poly coeff
            vt00  = t00 * 0.004 if t00 != -256 else INVALID
            msg_trace1 += f" quality={tqi} correct_type(0-2)={ttype}" + \
                          f" t00={vt00:.3f}m"
            if 1 <= ttype:
                if len_payload < payload.pos + 7 + 7:
                    return False
                t01  = payload.read('i7')
                t10  = payload.read('i7')
                vt01 = t01 * 0.002 if t01 != -64 else INVALID
                vt10 = t10 * 0.002 if t10 != -64 else INVALID
                msg_trace1 += f" t01={vt01:.3f}m/deg t10={vt10:.3f}m/deg"
            if 2 <= ttype:
                if len_payload < payload.pos + 7:
                    return False
                t11  = payload.read('i7')
                vt11 = t11 * 0.001 if t11 != -64 else INVALID
                msg_trace1 += f" t11={vt11:.3f}m/deg^2"
            msg_trace1 += '\n'
        if tropo[1]:
            if len_payload < payload.pos + 1 + 4:
                return False
            trs  = payload.read('u1')  # tropo residual size
            tro  = payload.read('u4')  # tropo residual offset
            bw   = 8 if trs else 6
            vtro = tro * 0.02
            msg_trace1 += f"ST12 Trop offset={vtro:.3f}m\n"
            if len_payload < payload.pos + bw * ngrid:
                return False
            for i in range(ngrid):
                fbw = f'i{bw}'
                tr  = payload.read(fbw)  # tropo residual
                vtr = tr * 0.004
                if (trs == 0 and tr != -32) or (trs == 1 and tr != -128):
                    vtr = INVALID
                msg_trace1 += \
                    f"ST12 Trop grid {i+1:2d}/{ngrid:2d}" + \
                    f" residual={vtr:{FMT_TROP}}m ({bw}bit)\n"
        stat_pos = payload.pos
        if stec[0]:
            svmask = {}
            for satsys in self.satsys:
                ngsys = len(self.gsys[satsys])
                if len_payload < payload.pos + ngsys:
                    return False
                svmask[satsys] = payload.read(ngsys)
            for satsys in self.satsys:
                for i, gsys in enumerate(self.gsys[satsys]):
                    if not svmask[satsys][i]:
                        continue
                    if len_payload < payload.pos + 6 + 2 + 14:
                        return False
                    sqi  = payload.read( 'u6')  # quality ind
                    sct  = payload.read( 'u2')  # correct type
                    c00  = payload.read('i14')
                    vc00 = c00 * 0.05 if c00 != -8192 else INVALID
                    msg_trace1 += \
                        f"ST12 STEC {gsys} quality={sqi:02x} type={sct}" + \
                        f" c00={vc00:{FMT_TECU}}TECU"
                    if 1 <= sct:
                        if len_payload < payload.pos + 12 + 12:
                            return False
                        c01  = payload.read('i12')
                        c10  = payload.read('i12')
                        vc01 = c01 * 0.02 if c01 != -2048 else INVALID
                        vc10 = c10 * 0.02 if c10 != -2048 else INVALID
                        msg_trace1 += \
                            f" c01={vc01:{FMT_TECU}}TECU/deg c10={vc10:{FMT_TECU}}TECU/deg"
                    if 2 <= sct:
                        if len_payload < payload.pos + 10:
                            return False
                        c11  = payload.read('i10')
                        vc11 = c11 * 0.02 if c11 != -512 else INVALID
                        msg_trace1 += f" c11={vc11:{FMT_TECU}}TECU/deg^2"
                    if 3 <= sct:
                        if len_payload < payload.pos + 8 + 8:
                            return False
                        c02  = payload.read('i8')
                        c20  = payload.read('i8')
                        vc02 = c02 * 0.005 if c02 != -128 else INVALID
                        vc20 = c20 * 0.005 if c20 != -128 else INVALID
                        msg_trace1 += \
                            f" c02={vc02:{FMT_TECU}}TECU/deg^2 c20={vc20:{FMT_TECU}}TECU/deg^2"
                    msg_trace1 += '\n'
                    if len_payload < payload.pos + 2:
                        return False
                    # STEC residual size
                    srs = payload.read('u2')
                    bw  = [   4,    4,    5,    7][srs]
                    lsb = [0.04, 0.12, 0.16, 0.24][srs]
                    for i in range(ngrid):
                        if len_payload < payload.pos + bw:
                            return False
                        fbw = f'i{bw}'
                        sr  = payload.read(fbw)
                        vsr = sr * lsb
                        if srs == 0 and sr ==  -8: vsr = INVALID
                        if srs == 1 and sr ==  -8: vsr = INVALID
                        if srs == 2 and sr == -16: vsr = INVALID
                        if srs == 3 and sr == -64: vsr = INVALID
                        msg_trace1 += \
                            f"ST12 STEC {gsys} grid {i+1:2d}/{ngrid:2d} " + \
                            f"residual={vsr:{FMT_TECU}}TECU ({bw}bit)\n"
        self.trace.show(1, msg_trace1, end='')
        self.stat_both += stat_pos
        self.stat_bsat += payload.pos - stat_pos
        return True

def gnssid2satsys(gnssid):
    ''' convert gnss id to satellite system '''
    if   gnssid == 0: satsys = 'G'
    elif gnssid == 1: satsys = 'R'
    elif gnssid == 2: satsys = 'E'
    elif gnssid == 3: satsys = 'C'
    elif gnssid == 4: satsys = 'J'
    elif gnssid == 5: satsys = 'S'
    else: raise Exception(f'undefined gnssid {gnssid}')
    return satsys

def sigmask2signame(satsys, sigmask):
    ''' convert satellite system and signal mask to signal name '''
    signame = f'satsys={satsys} sigmask={sigmask}'
    if satsys == 'G':
        signame = [ "L1 C/A", "L1 P", "L1 Z-tracking", "L1C(D)", "L1C(P)",
            "L1C(D+P)", "L2 CM", "L2 CL", "L2 CM+CL", "L2 P", "L2 Z-tracking",
            "L5 I", "L5 Q", "L5 I+Q", "", ""][sigmask]
    elif satsys == 'R':
        signame = [ "G1 C/A", "G1 P", "G2 C/A", "G2 P", "G1a(D)", "G1a(P)",
            "G1a(D+P)", "G2a(D)", "G2a(P)", "G2a(D+P)", "G3 I", "G3 Q",
            "G3 I+Q", "", "", "", ""][sigmask]
    elif satsys == 'E':
        signame = [ "E1 B", "E1 C", "E1 B+C", "E5a I", "E5a Q", "E5a I+Q",
            "E5b I", "E5b Q", "E5b I+Q", "E5 I", "E5 Q", "E5 I+Q",
            "E6 B", "E6 C", "E6 B+C", ""][sigmask]
    elif satsys == 'C':
        signame = [ "B1 I", "B1 Q", "B1 I+Q", "B3 I", "B3 Q", "B3 I+Q",
            "B2 I", "B2 Q", "B2 I+Q", "", "", "", "", "", "", "", ""][sigmask]
    elif satsys == 'J':
        signame = [ "L1 C/A", "L1 L1C(D)", "L1 L1C(P)", "L1 L1C(D+P)",
            "L2 L2C(M)", "L2 L2C(L)", "L2 L2C(M+L)", "L5 I", "L5 Q",
            "L5 I+Q", "", "", "", "", "", ""][sigmask]
    elif satsys == 'S':
        signame = [
            "L1 C/A", "L5 I", "L5 Q", "L5 I+Q", "", "", "", "", "", "",
            "", "", "", "", "", "", ""][sigmask]
    else:
        raise Exception(
            f'unassigned signal name for satsys={satsys} and sigmask={sigmask}')
    return signame

# EOF
