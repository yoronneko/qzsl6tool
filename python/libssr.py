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

URA_INVALID = 0    # invalid user range accuracy
CSSR_UI = [        # CSSR update interval in second, ref.[3], Table 4.2.2-6
    1, 2, 5, 10, 15, 30, 60, 120, 240, 300, 600, 900, 1800, 3600, 7200, 10800
]
HAS_VI = [         # HAS validity interval in second
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
FMT_URA  = '7.2f'  # format string for URA

def epoch2time(epoch):
    ''' convert epoch to time
        epoch: epoch in second (0-86400)
    '''
    hour = epoch // 3600
    min  = (epoch % 3600) // 60
    sec  = epoch % 60
    return f'{hour:02d}:{min:02d}:{sec:02d}'
    # return f'{hour:02d}:{min:02d}:{sec:02d} ({epoch})'

def epoch2timedate(epoch):
    ''' convert epoch to time plus date'''
    return f'{epoch2time(epoch%86400)}+{epoch//86400}'

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

def ura2dist(ura):
    ''' converts user range accuracy (URA) code to accuracy in distance [mm] '''
    dist = 0.0
    if   ura.bin == 0b000000:   # undefined or unknown
        dist = URA_INVALID
    elif ura.bin == 0b111111:   # URA more than 5466.5 mm
        dist = 5466.5
    else:
        cls  = ura[4:7].u
        val  = ura[0:4].u
        dist = 3 ** cls * (1 + val / 4) - 1
    return dist


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
        self.ssr_interval  = payload.read( 'u4')  # SSR update interval
        self.ssr_mmi       = payload.read( 'u1')  # multiple message indication
        if mtype == 'SSR orbit' or mtype == 'SSR obt/clk':
            self.ssr_sdat  = payload.read( 'u1')  # sat ref datum
        self.ssr_iod       = payload.read( 'u4')  # IOD SSR
        self.ssr_pid       = payload.read('u16')  # SSR provider ID
        self.ssr_sid       = payload.read( 'u4')  # SSR solution ID
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
        for _ in range(self.ssr_nsat):
            satid  = payload.read(  bw )  # satellite ID, DF068
            iode   = payload.read( 'u8')  # IODE, DF071
            drad   = payload.read('i22')  # delta radial, DF365
            daln   = payload.read('i20')  # delta along track, DF366
            dcrs   = payload.read('i20')  # delta cross track, DF367
            ddrad  = payload.read('i21')  # d_delta radial, DF368
            ddaln  = payload.read('i19')  # d_delta along track, DF369
            ddcrs  = payload.read('i19')  # d_delta cross track, DF370
            strsat += f"{satsys}{satid:02} "
            self.trace.show(1, f'{satsys}{satid:02d} d_radial={drad*1e-4:{FMT_ORB}}m d_along={daln*4e-4:{FMT_ORB}}m d_cross={dcrs*4e-5:{FMT_ORB}}m dot_d_radial={ddrad*1e-6:{FMT_ORB}}m/s dot_d_along={ddaln*4e-6:{FMT_ORB}}m/s dot_d_cross={ddcrs*4e-6:{FMT_ORB}}m/s')
        string = f"{strsat}(nsat={self.ssr_nsat} iod={self.ssr_iod}{' cont.' if self.ssr_mmi else ''})"
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
            strsat += f"{satsys}{satid:02d} "
            self.trace.show(1, f'{satsys}{satid:02d} c0={c0*1e-4:{FMT_CLK}}m, c1={c1*1e-6:{FMT_CLK}}m/s, c2={c2*2e-8:{FMT_CLK}}m/s^2')
        string = f"{strsat}(nsat={self.ssr_nsat} iod={self.ssr_iod}{' cont.' if self.ssr_mmi else ''})"
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
                sstmi = sigmask2signame(satsys, stmi)
                self.trace.show(1, f'{satsys}{satid:02d} {sstmi:{FMT_GSIG}} code_bias={cb*1e-2:{FMT_CB}}m')
        string = f"{strsat}(nsat={self.ssr_nsat} iod={self.ssr_iod}{' cont.' if self.ssr_mmi else ''})"
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
            accuracy = ura2dist(ura)
            if accuracy != URA_INVALID:
                self.trace.show(1, f'{satsys}{satid:02d} ura={accuracy:{FMT_URA}} mm')
                strsat += f"{satsys}{satid:02} "
        string = f"{strsat}(nsat={self.ssr_nsat} iod={self.ssr_iod}{' cont.' if self.ssr_mmi else ''})"
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
            hrc   = payload.read('i22')  # high rate clock, DF390
            strsat += f"{satsys}{satid:02} "
            self.trace.show(1, f'{satsys}{satid:02} high_rate_clock={hrc*1e-4:{FMT_CLK}}m')
        string = f"{strsat}(nsat={self.ssr_nsat} iod={self.ssr_iod}{' cont.' if self.ssr_mmi else ''})"
        return string

    def decode_cssr(self, payload):
        ''' calls cssr decode functions and returns True if success '''
        if not self.decode_cssr_head(payload):
            return 'Could not decode CSSR header'
        if   self.subtype ==  1: self.decode_cssr_st1 (payload)
        elif self.subtype ==  2: self.decode_cssr_st2 (payload)
        elif self.subtype ==  3: self.decode_cssr_st3 (payload)
        elif self.subtype ==  4: self.decode_cssr_st4 (payload)
        elif self.subtype ==  5: self.decode_cssr_st5 (payload)
        elif self.subtype ==  6: self.decode_cssr_st6 (payload)
        elif self.subtype ==  7: self.decode_cssr_st7 (payload)
        elif self.subtype ==  8: self.decode_cssr_st8 (payload)
        elif self.subtype ==  9: self.decode_cssr_st9 (payload)
        elif self.subtype == 10: self.decode_cssr_st10(payload)
        elif self.subtype == 11: self.decode_cssr_st11(payload)
        elif self.subtype == 12: self.decode_cssr_st12(payload)
        else:
            raise Exception(f"unknown CSSR subtype: {self.subtype}")
        string = f'ST{self.subtype:<2d}'
        if self.subtype == 1:
            # string += f' epoch={self.epoch} iod={self.iodssr}'
            string += f' Epoch={epoch2timedate(self.epoch)} ({self.epoch}) UI={CSSR_UI[self.ui]:2d}s ({self.ui}) IODSSR={self.iod} {"cont." if self.mmi else ""}'
        else:
            # string += f' hepoch={self.hepoch} iod={self.iodssr}'
            etime=f'{self.hepoch//60:02d}:{self.hepoch%60:02d}'
            string += f' Epoch={etime} ({self.hepoch}) UI={CSSR_UI[self.ui]:2d}s ({self.ui}) IODSSR={self.iodssr}{" cont." if self.mmi else ""}'
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
        if len_payload < 12 + + 4:
            self.msgnum  = 0  # could not retreve the message number
            self.subtype = 0  # could not retreve the subtype number
            return False
        self.msgnum  = payload.read('u12')
        self.subtype = payload.read('u4')  # subtype
        if self.msgnum != 4073:  # CSSR message number should be 4073
            self.trace.show(2, f"CSSR msgnum should be 4073 ({self.msgnum})" + \
                f"{len(payload.bin)} bits\nCSSR dump: {payload.bin}\n")
            self.subtype = 0  # no subtype number
            return False
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
        self.ui     = payload.read('u4')  # update interval
        self.mmi    = payload.read('u1')  # multiple message indication
        self.iodssr = payload.read('u4')  # IOD SSR
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
                if rad == -16384 or alg == -16384 or crs == -16384:
                    continue
                msg_trace1 += f'ST2 {gsys} IODE={iode:{FMT_IODE}} d_radial={rad*0.0016:{FMT_ORB}}m d_along={ alg*0.0064:{FMT_ORB}}m d_cross={ crs*0.0064:{FMT_ORB}}m\n'
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
                if rad.bin == '1000000000000' or alg.bin == '100000000000' or crs.bin == '100000000000':
                    continue
                msg_trace1 += f'ORBIT {gsys} IODE={iode:{FMT_IODE}} d_radial={rad.i*0.0025:{FMT_ORB}}m d_track={ alg.i*0.0080 :{FMT_ORB}}m d_cross={ crs.i*0.0080 :{FMT_ORB}}m\n'
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
                c0 = payload.read('i15')
                if c0 == -16384:
                    continue
                msg_trace1 += f"ST3 {gsys} d_clock={c0*1.6e-3:{FMT_CLK}}m\n"
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
                if c0.bin == '1000000000000' or c0.bin == '0111111111111':
                    continue
                msg_trace1 += f"CKFUL {gsys} d_clock={c0.i*2.5e-3*multiplier[i]:{FMT_CLK}}m (multiplier={multiplier[i]})\n"
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
        multiplier = [1 for i in range(len(self.satsys))]
        for i in range(ns):
            if len_payload < payload.pos + 4 + 2:
                return False
            satsys        = payload.read('u4')
            multiplier[i] = payload.read('u2') + 1
            for gsys in self.gsys[satsys]:
                for gsig in self.gsig[satsys]:
                    if len_payload < payload.pos + 13:
                        return False
                    c0 = payload.read(13)
                    if c0.bin == '1000000000000' or c0.bin == '0111111111111':
                        continue
                    msg_trace1 += f"CKSUB {gsys} d_clock={c0.i*2.5e-3*multiplier[i]:{FMT_CLK}}m (x{multiplier[i]})\n"
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
                    if cb == -1024:
                        continue
                    if ssr_type == "cssr": msg_trace1 += "ST4"
                    else                 : msg_trace1 += "CBIAS"
                    msg_trace1 += f" {gsys} {gsig:{FMT_GSIG}} code_bias={cb*0.02:{FMT_CB}}m\n"
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
                    if pb == -16384:
                        continue
                    msg_trace1 += f'ST5 {gsys} {gsig:{FMT_GSIG}} phase_bias={pb*0.001:{FMT_PB}}m discont_indicator={di}\n'
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
                    if pb == -1024:
                        continue
                    msg_trace1 += \
                        f'PBIAS {gsys} {gsig:{FMT_GSIG}} phase_bias={pb*0.01:{FMT_PB}}cycle discont_indicator={di}\n'
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
        msg_trace1 = f"ST6 code_bias={'on' if f_cb else 'off'} phase_bias={  'on' if f_pb else 'off'} network_bias={'on' if f_nb else 'off'}\n"
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
                        if cb == -1024:
                            continue
                        msg_trace1 += f" code_bias={cb*0.02:{FMT_CB}}m"
                    if f_pb:
                        if len_payload < payload.pos + 15 + 2:
                            return False
                        pb  = payload.read('i15')  # phase bias
                        di  = payload.read( 'u2')  # disc ind
                        if pb == -16384:
                            continue
                        msg_trace1 += f" phase_bias={pb*0.001:{FMT_PB}}m discont_indi={di}"
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
                ura = payload.read(6)  # [3], Sect.4.2.2.7
                accuracy = ura2dist(ura)
                if accuracy != URA_INVALID:
                    msg_trace1 += f"ST7 {gsys} URA {accuracy:7.2f} mm\n"
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
        CSSR_STEC_CORR_TYPE = ['c00','c00, c01, c10', 'c00, c01, c10, c11', 'c00, c01, c10, c11, c02, c20',]
        msg_trace1 = f'ST8 STEC Correction: {CSSR_STEC_CORR_TYPE[stec_type]} ({stec_type}), NID={cnid}\n'
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
                if len_payload < payload.pos + 6 + 14:
                    return False
                qi   = payload.read(   6 )  # quality indicator
                c00  = payload.read('i14')
                if c00 == -8192:
                    continue
                msg_trace1 += f"ST8 {gsys} quality={ura2dist(qi)}TECU ({qi.u})\n"
                msg_trace1 += f"ST8 {gsys} c00={c00*0.05:{FMT_TECU}}TECU"
                if 1 <= stec_type:
                    if len_payload < payload.pos + 12 + 12:
                        return False
                    c01  = payload.read('i12')
                    c10  = payload.read('i12')
                    if c01 != -2048 and c10 != -2048:
                        msg_trace1 += f" c01={c01*0.02:{FMT_TECU}}TECU/deg c10={c10*0.02:{FMT_TECU}}TECU/deg"
                if 2 <= stec_type:
                    if len_payload < payload.pos + 10:
                        return False
                    c11  = payload.read('i10')
                    if c11 != -512:
                        msg_trace1 += f" c11={c11*0.02:{FMT_TECU}}TECU/deg^2"
                if 3 <= stec_type:
                    if len_payload < payload.pos + 8 + 8:
                        return False
                    c02  = payload.read('i8')
                    c20  = payload.read('i8')
                    if c02 != -128 and c20 != -128:
                        msg_trace1 += f" c02={c02*0.005:{FMT_TECU}}TECU/deg^2 c20={c20*0.005:{FMT_TECU}}TECU/deg^2"
                msg_trace1 += '\n'
        self.trace.show(1, msg_trace1, end='')
        self.stat_both += stat_pos + 7
        self.stat_bsat += payload.pos - stat_pos - 7
        return True

    def decode_cssr_st9(self, payload):
        ''' decode CSSR ST9 trop correction message and returns True if success '''
        len_payload = len(payload)
        if len_payload < 2 + 1 + 5:
            return False
        tctype = payload.read('u2')  # trop correction type
        crange = payload.read('u1')  # trop correction range
        cnid   = payload.read('u5')  # compact network ID
        svmask = {}
        for satsys in self.satsys:
            ngsys = len(self.gsys[satsys])
            if len_payload < payload.pos + ngsys:
                return False
            svmask[satsys] = payload.read(ngsys)
        if len_payload < payload.pos + 6 + 6:
            return False
        tqi   = payload.read(  6 )  # tropo quality indicator
        ngrid = payload.read('u6')  # number of grids
        bw = 16 if crange else 7    # bit width of residual correction
        CSSR_TROP_CORR_TYPE = ['Not included', 'Neill mapping function', 'Reserved', 'Reserved',]
        msg_trace1 = f"ST9 Trop Type: {CSSR_TROP_CORR_TYPE[tctype]} ({tctype}), resolution={bw} bit ({crange}), NID={cnid}, quality={ura2dist(tqi)} mm ({tqi.u}), ngrid={ngrid}\n"
        # we implicitly assume the tropospheric correction type (tctype) is 1. if tctype=0 (no topospheric correction), we don't know whether we read the following tropospheric correction data or not. Others are reserved.
        for grid in range(ngrid):
            if len_payload < payload.pos + 9 + 8:
                return False
            vd_h = payload.read('i9')  # hydrostatic vertical delay
            vd_w = payload.read('i8')  # wet         vertical delay
            if vd_h == -256 or vd_w == -128:
                continue
            msg_trace1 += f'ST9 grid {grid+1:2d}/{ngrid:2d} hydro_delay={2.3+vd_h*0.004:6.3f}m wet_delay={0.252+vd_w*0.004:6.3f}m\n'
            for satsys in self.satsys:
                for maskpos, gsys in enumerate(self.gsys[satsys]):
                    if not svmask[satsys][maskpos]:
                        continue
                    if len_payload < payload.pos + bw:
                        return False
                    res  = payload.read(f'i{bw}')  # residual
                    if (crange == 1 and res == -32768) or \
                       (crange == 0 and res == -64):
                        continue
                    msg_trace1 += f'ST9 grid {grid+1:2d}/{ngrid:2d} {gsys} STEC residual={res*0.04:{FMT_TECU}}TECU\n'
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
        size  = (dsize + 1) * 40
        if len_payload < payload.pos + size:
            return False
        aux_frame_data = payload.read(size)
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
        msg_trace1 = f"ST11 Orb={'on' if f_o else 'off'} Clk={'on' if f_c else 'off'} Net={'on' if f_n else 'off'}\n"
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
                    if f_o:
                        bw = 10 if satsys == 'E' else 8  # IODE bit width
                        if len_payload < payload.pos + bw + 15 + 13 + 13:
                            return False
                        iode = payload.read(f'u{bw}')  # IODE
                        rad  = payload.read('i15')     # radial
                        alg  = payload.read('i13')     # along
                        crs  = payload.read('i13')     # cross
                    if f_c:
                        if len_payload < payload.pos + 15:
                            return False
                        c0  = payload.read('i15')
                    f_o_ok = f_o and (rad != -16384 and alg != -4096 and crs != -4096)
                    f_c_ok = f_c and c0 != -16384
                    if f_o_ok or f_c_ok:
                        msg_trace1 += f"ST11 {gsys}"
                    if f_o_ok:
                        msg_trace1 += f' IODE={iode:{FMT_IODE}} d_radial={rad*0.0016:{FMT_ORB}}m d_along={alg*0.0064:{FMT_ORB}}m d_cross={crs*0.0064:{FMT_ORB}}m'
                    if f_c_ok:
                        msg_trace1 += f" c0={c0*1.6e-3:{FMT_CLK}}m"
                    if f_o_ok or f_c_ok:
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
        tavail = payload.read(  2 )  # troposhpere correction availability
        savail = payload.read(  2 )  # STEC        correction availability
        cnid   = payload.read('u5')  # compact network ID
        ngrid  = payload.read('u6')  # number of grids
        msg_trace1 = f"ST12 tropo={tavail} stec={savail} NID={cnid} ngrid={ngrid}\n"
        if tavail[0]:  # bool object
            # 0 <= ttype (forward reference)
            if len_payload < payload.pos + 6 + 2 + 9:
                return False
            tqi   = payload.read(  6 )  # tropo quality indication
            ttype = payload.read('u2')  # tropo correction type
            t00   = payload.read('i9')  # tropo poly coeff
            CSSR_TROP_CORR_TYPE12 = ['t00', 't00, t01, t10', 't00, t01, t10, t11']
            msg_trace1 += f"ST12 Trop quality={ura2dist(tqi)}mm ({tqi.u}) Correction: {CSSR_TROP_CORR_TYPE12[ttype]} ({ttype})\n"
            msg_trace1 += f"ST12 Trop"
            if t00 != -256:
                msg_trace1 += f" t00={t00*0.004:.3f}m"
            if 1 <= ttype:
                if len_payload < payload.pos + 7 + 7:
                    return False
                t01  = payload.read('i7')
                t10  = payload.read('i7')
                if t01 != -64 and t10 != -64:
                    msg_trace1 += f" t01={t01*0.002:.3f}m/deg t10={t10*0.002:.3f}m/deg"
            if 2 <= ttype:
                if len_payload < payload.pos + 7:
                    return False
                t11  = payload.read('i7')
                if t11 != -64:
                    msg_trace1 += f" t11={t11*0.001:.3f}m/deg^2"
            msg_trace1 += '\n'
        if tavail[1]:  # bool object
            if len_payload < payload.pos + 1 + 4:
                return False
            trs  = payload.read('u1')  # tropo residual size
            tro  = payload.read('u4')  # tropo residual offset
            bw   = 8 if trs else 6
            msg_trace1 += f"ST12 Trop offset={tro*0.02:.3f}m resolution={bw} bit\n"
            if len_payload < payload.pos + bw * ngrid:
                return False
            for grid in range(ngrid):
                tr = payload.read(f'i{bw}')  # tropo residual
                if (trs == 0 and tr != -32) or (trs == 1 and tr != -128):
                    continue
                msg_trace1 += f"ST12 Trop grid {grid+1:2d}/{ngrid:2d} residual={tr*0.004:{FMT_TROP}}m\n"
        stat_pos = payload.pos
        if savail[0]:  # bool object
            svmask = {}
            for satsys in self.satsys:
                ngsys = len(self.gsys[satsys])
                if len_payload < payload.pos + ngsys:
                    return False
                svmask[satsys] = payload.read(ngsys)
            for satsys in self.satsys:
                for maskpos, gsys in enumerate(self.gsys[satsys]):
                    if not svmask[satsys][maskpos]:
                        continue
                    if len_payload < payload.pos + 6 + 2 + 14:
                        return False
                    sqi = payload.read(   6 )  # STEC quality indication
                    sct = payload.read( 'u2')   # STEC correct type
                    c00 = payload.read('i14')
                    CSSR_STEC_CORR_TYPE12 = ['c00', 'c00, c01, c10', 'c00, c01, c10, c11', 'c00, c01, c10, c11, c02, c20']
                    msg_trace1 += f"ST12 STEC {gsys} quality={ura2dist(sqi)}TECU ({sqi.u}) Correction: {CSSR_STEC_CORR_TYPE12[sct]} ({sct})\n"
                    msg_trace1 += f"ST12 STEC {gsys}"
                    if c00 != -8192:
                        msg_trace1 += f" c00={c00*0.05:{FMT_TECU}}TECU"
                    if 1 <= sct:
                        if len_payload < payload.pos + 12 + 12:
                            return False
                        c01 = payload.read('i12')
                        c10 = payload.read('i12')
                        if c01 != -2048 and c10 != -2048:
                            msg_trace1 += f" c01={c01*0.02:{FMT_TECU}}TECU/deg c10={c10*0.02:{FMT_TECU}}TECU/deg"
                    if 2 <= sct:
                        if len_payload < payload.pos + 10:
                            return False
                        c11 = payload.read('i10')
                        if c11 != -512:
                            msg_trace1 += f" c11={c11* 0.02:{FMT_TECU}}TECU/deg^2"
                    if 3 <= sct:
                        if len_payload < payload.pos + 8 + 8:
                            return False
                        c02 = payload.read('i8')
                        c20 = payload.read('i8')
                        if c02 != -128 and c20 != -128:
                            msg_trace1 += f" c02={c02*0.005:{FMT_TECU}}TECU/deg^2 c20={c20*0.005:{FMT_TECU}}TECU/deg^2"
                    msg_trace1 += '\n'
                    if len_payload < payload.pos + 2:
                        return False
                    srs = payload.read('u2')  # STEC residual size
                    bw  = [   4,    4,    5,    7][srs]
                    lsb = [0.04, 0.12, 0.16, 0.24][srs]
                    for grid in range(ngrid):
                        if len_payload < payload.pos + bw:
                            return False
                        sr  = payload.read(f'i{bw}')  # STEC residual
                        if (srs == 0 and sr ==  -8) or \
                           (srs == 1 and sr ==  -8) or \
                           (srs == 2 and sr == -16) or \
                           (srs == 3 and sr == -64):
                            continue
                        msg_trace1 += f"ST12 STEC {gsys} grid {grid+1:2d}/{ngrid:2d} residual={sr*lsb:{FMT_TECU}}TECU ({bw}bit)\n"
        if savail[1]:  # bool object
            pass  # the use of this bit is not defined in ref.[1]
        self.trace.show(1, msg_trace1, end='')
        self.stat_both += stat_pos
        self.stat_bsat += payload.pos - stat_pos
        return True

# EOF

