#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# libssr.py: library for SSR and compact SSR message processing
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022-2023 Satoshi Takahashi
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
# [5] Europea Union Agency for the Space Programme,
#     Galileo High Accuracy Service Signal-in-Space Interface Control
#     Document (HAS SIS ICD), Issue 1.0 May 2022.

import sys
import bitstring

INVALID = 0  # invalid value indication for CSSR message show
HAS_VALIDITY_INTERVAL = [
    5, 10, 15, 20, 30, 60, 90, 120, 180, 240, 300, 600, 900, 1800, 3600, 0
]

class Ssr:
    """class of state space representation (SSR) and compact SSR process"""
# --- public
    subtype = 0     # subtype number
# --- private
    ssr_nsat = 0    # number of satellites
    ssr_mmi = 0     # multiple message indicator
    ssr_iod = 0     # iod ssr
    epoch = 0       # epoch
    hepoch = 0      # hourly epoch
    interval = 0    # update interval
    mmi = 0         # multiple message indication
    iod = 0         # issue of data
    satsys = []     # array of satellite system
    nsatmask = []   # array of number of satellite mask
    nsigmask = []   # array of number of signal mask
    cellmask = []   # array of cell mask
    gsys = {}       # dict of sat   name from system name
    gsig = {}       # dict of sigal name from system name
    stat = False    # statistics output
    stat_nsat = 0   # stat: number of satellites
    stat_nsig = 0   # stat: number of signals
    stat_bsat = 0   # stat: bit number of satellites
    stat_bsig = 0   # stat: bit number of signals
    stat_both = 0   # stat: bit number of other information
    stat_bnull = 0  # stat: bit number of null

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

    def ssr_decode_head(self, payload, pos, satsys, mtype):
        '''returns SSR header pos'''
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

    def ssr_decode_orbit(self, payload, pos, satsys):
        '''decodes SSR orbit correction and returns pos and string'''
        strsat = ''
        # satid bit width changes according to satellite system
        if satsys == 'J':    # ref. [2]
            bw = 4
        elif satsys == 'R':  # ref. [1]
            bw = 5
        else:                # ref. [1]
            bw = 6
        for i in range(self.ssr_nsat):
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
        string = f"{strsat}(nsat={self.ssr_nsat} iod={self.ssr_iod}" + \
                      f"{' cont.' if self.ssr_mmi else ''})"
        return pos, string

    def ssr_decode_clock(self, payload, pos, satsys):
        '''decodes SSR clock correction and returns pos and string'''
        strsat = ''
        # satid bit width changes according to satellite system
        if satsys == 'J':    # ref. [2]
            bw = 4
        elif satsys == 'R':  # ref. [1]
            bw = 5
        else:                # ref. [1]
            bw = 6
        for i in range(self.ssr_nsat):
            satid = payload[pos:pos+bw].uint  # satellite ID
            pos += bw
            dc0 = payload[pos:pos+22].int     # delta clock c0
            pos += 22
            dc1 = payload[pos:pos+21].int     # delta clock c1
            pos += 21
            dc2 = payload[pos:pos+27].int     # delta clock c2
            pos += 27
            strsat += f"{satsys}{satid:02} "
        string = f"{strsat}(nsat={self.ssr_nsat} iod={self.ssr_iod}" + \
                      f"{' cont.' if self.ssr_mmi else ''})"
        return pos, string

    def ssr_decode_code_bias(self, payload, pos, satsys):
        '''decodes SSR code bias and returns pos and string'''
        strsat = ''
        # satid bit width changes according to satellite system
        if satsys == 'J':    # ref. [2]
            bw = 4
        elif satsys == 'R':  # ref. [1]
            bw = 5
        else:                # ref. [1]
            bw = 6
        for i in range(self.ssr_nsat):
            satid = payload[pos:pos+bw].uint  # satellite ID
            pos += bw
            ncb = payload[pos:pos+5].uint     # code bias number
            pos += 5
            strsat += f"{satsys}{satid:02} "
            for j in range(ncb):
                stmi = payload[pos:pos+5].uint
                        # signal & tracking mode indicator
                pos += 5
                cb = payload[pos:pos+14].int  # code bias
                pos += 14
        string = f"{strsat}(nsat={self.ssr_nsat} iod={self.ssr_iod}" + \
                      f"{' cont.' if self.ssr_mmi else ''})"
        return pos, string

    def ssr_decode_ura(self, payload, pos, satsys):
        '''decodes SSR user range accuracy and returns pos and string'''
        strsat = ''
        # satid bit width changes according to satellite system
        if satsys == 'J':    # ref. [2]
            bw = 4
        elif satsys == 'R':  # ref. [1]
            bw = 5
        else:                # ref. [1]
            bw = 6
        for i in range(self.ssr_nsat):
            satid = payload[pos:pos+bw].uint  # satellite ID
            pos += bw
            ura = payload[pos:pos+6].uint  # user range accuracy
            pos += 6
            strsat += f"{satsys}{satid:02} "
        string = f"{strsat}(nsat={self.ssr_nsat} iod={self.ssr_iod}" + \
                      f"{' cont.' if self.ssr_mmi else ''})"
        return pos, string

    def ssr_decode_hr_clock(self, payload, pos, satsys):
        '''decodes SSR high rate clock and returns pos and string'''
        strsat = ''
        # satid bit width changes according to satellite system
        if satsys == 'J':
            bw = 4
        elif satsys == 'R':
            bw = 5
        else:
            bw = 6
        for i in range(self.ssr_nsat):
            satid = payload[pos:pos+bw].uint  # satellite ID
            pos += bw
            hrc = payload[pos:pos+22].int  # high rate clock
            pos += 22
            strsat += f"{satsys}{satid:02} "
        string = f"{strsat}(nsat={self.ssr_nsat} iod={self.ssr_iod}" + \
                      f"{' cont.' if self.ssr_mmi else ''})"
        return pos, string

    def decode_cssr(self, payload):
        "returns pos and string"
        pos = self.decode_cssr_head(payload)
        if pos == 0:
            return 0, ''
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
        string = f'ST{self.subtype:<2d}'
        if self.subtype == 1:
            string += f' epoch={self.epoch} iod={self.iod}'
        else:
            string += f' hepoch={self.hepoch} iod={self.iod}'
        return pos, string

    def show_cssr_stat(self):
        bit_total = self.stat_bsat + self.stat_bsig + self.stat_both + \
                self.stat_bnull
        msg = f'stat n_sat {self.stat_nsat} n_sig {self.stat_nsig} ' + \
              f'bit_sat {self.stat_bsat} bit_sig {self.stat_bsig} ' + \
              f'bit_other {self.stat_both} bit_null {self.stat_bnull} ' + \
              f'bit_total {bit_total}'
        self.trace(0, msg)

    def decode_cssr_head(self, payload):
        '''returns bit size of cssr header'''
        len_payload = len(payload)
        pos = 0
        if '0b1' not in payload:  # Zero padding detection
            self.trace(2,
                f"CSSR null data {len(payload.bin)} bits\n",
                f"CSSR dump: {payload.bin}\n")
            self.stat_bnull += len(payload.bin)
            self.subtype = 0  # no subtype number
            return 0
        if len_payload < 12:
            self.msgnum = 0   # could not retreve the message number
            self.subtype = 0  # could not retreve the subtype number
            return 0
        self.msgnum = payload[pos:pos + 12].uint
        pos += 12  # message num, 4073
        if self.msgnum != 4073:  # CSSR message number should be 4073
            self.trace(2,
                f"CSSR msgnum should be 4073 ({self.msgnum})\n",
                f"{len(payload.bin)} bits\n",
                f"CSSR dump: {payload.bin}\n")
            self.stat_bnull += len(payload.bin)
            self.subtype = 0  # no subtype number
            return 0
        if len_payload < pos + 4:
            self.subtype = 0  # could not retreve the subtype number
            return 0
        self.subtype = payload[pos:pos + 4].uint  # subtype
        pos += 4
        if self.subtype == 1:  # Mask message
            if len_payload < pos + 20:  # could not retreve the epoch
                return 0
            self.epoch = payload[pos:pos + 20].uint  # GPS epoch time 1s
            pos += 20
        elif self.subtype == 10:  # Service Information
            return pos
        else:
            if len_payload < pos + 12:  # could not retreve the hourly epoch
                return 0
            self.hepoch = payload[pos:pos + 12].uint  # GNSS hourly epoch
            pos += 12
        if len_payload < pos + 4 + 1 + 4:
            return 0
        self.interval = payload[pos:pos + 4].uint  # update interval
        pos += 4
        self.mmi = payload[pos:pos + 1].uint  # multiple message indication
        pos += 1
        self.iod = payload[pos:pos + 4].uint  # SSR issue of data
        pos += 4
        return pos

    def _decode_mask(self, payload, pos, ssr_type):
        '''ssr_type: cssr or has'''
        if ssr_type not in {'cssr', 'has'}:
            raise
        len_payload = len(payload)
        if len_payload < pos + 4:
            return 0
        ngnss = payload[pos:pos + 4].uint  # numer of GNSS
        pos += 4
        if len(payload) < 49 + 61 * ngnss:
            return 0
        satsys   = [None for i in range(ngnss)]
        nsatmask = [None for i in range(ngnss)]
        nsigmask = [None for i in range(ngnss)]
        cellmask = [None for i in range(ngnss)]
        navmsg   = [None for i in range(ngnss)]
        gsys = {}
        gsig = {}
        for ignss in range(ngnss):
            ugnssid  = payload[pos:pos +  4].uint; pos +=  4
            bsatmask = payload[pos:pos + 40]     ; pos += 40
            bsigmask = payload[pos:pos + 16]     ; pos += 16
            cmavail  = payload[pos:pos +  1]     ; pos +=  1
            t_satsys = gnssid2satsys(ugnssid)
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
                bcellmask = payload[pos:pos + ncell]
                pos += ncell
            else:
                bcellmask = bitstring.BitArray('0b1') * ncell
            nm = 0
            if ssr_type == 'has':
                nm = payload[pos:pos + 3].uint; pos += 3
            cellmask[ignss] = bcellmask
            satsys[ignss]   = t_satsys
            nsatmask[ignss] = t_satmask
            nsigmask[ignss] = t_sigmask
            gsys[t_satsys]  = t_gsys
            gsig[t_satsys]  = t_gsig
            navmsg[ignss]   = nm
        if ssr_type == 'has':
            pos += 6  # researved
        self.satsys   = satsys    # satellite system
        self.nsatmask = nsatmask  # number of satellite mask
        self.nsigmask = nsigmask  # number of signal mask
        self.cellmask = cellmask  # cell mask
        self.gsys     = gsys      # dict of sat   name from system name
        self.gsig     = gsig      # dict of sigal name from system name
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
                    mask = self.cellmask[i][pos_mask]
                    pos_mask += 1
                    if not mask:
                        continue
                    msg_trace1 += ' ' + gsig
                    self.stat_nsig += 1
                msg_trace1 += '\n'
            if ssr_type == 'has' and navmsg[i] != 0:
                msg_trace1 += '\nWarning: HAS NM is not zero.'
        self.trace(1, msg_trace1)
        if self.stat:
            self.show_cssr_stat()
        self.stat_bsat = 0
        self.stat_bsig = 0
        self.stat_both = pos
        self.stat_bnull = 0
        return pos

    def decode_cssr_st1(self, payload, pos):
        return self._decode_mask(payload, pos, 'cssr')

    def decode_has_mt1_mask(self, has_msg, pos):
        return self._decode_mask(has_msg, pos, 'has')

    def decode_cssr_st2(self, payload, pos):
        len_payload = len(payload)
        stat_pos = pos
        msg_trace1 = ''
        for satsys in self.satsys:
            w_iode = 10 if satsys == 'E' else 8  # IODE bit width
            for gsys in self.gsys[satsys]:
                if len_payload < pos + w_iode + 15 + 13 + 13:
                    return 0
                iode = payload[pos:pos + w_iode].uint
                pos += w_iode
                i_radial = payload[pos:pos + 15].int; pos += 15
                i_along  = payload[pos:pos + 13].int; pos += 13
                i_cross  = payload[pos:pos + 13].int; pos += 13
                d_radial = i_radial * 0.0016 if i_radial != -16384 else INVALID
                d_along  = i_along  * 0.0064 if i_along  != -16384 else INVALID
                d_cross  = i_cross  * 0.0064 if i_cross  != -16384 else INVALID
                msg_trace1 += \
                    f'ST2 {gsys} IODE={iode:4d} d_radial={d_radial:5.1f}m' + \
                    f' d_along={d_along:5.1f}m d_cross={d_cross:5.1f}m\n'
        self.trace(1, msg_trace1)
        self.stat_both += stat_pos
        self.stat_bsat += pos - stat_pos
        return pos

    def decode_has_mt1_orbit(self, payload, pos):
        len_payload = len(payload)
        stat_pos = pos
        if len_payload < pos + 4:
            return 0
        vi = payload[pos:pos + 4].uint; pos += 4
        msg_trace1 = f'ORBIT validity_interval={HAS_VALIDITY_INTERVAL[vi]}s'
        msg_trace1 += f' ({vi})\n'
        for satsys in self.satsys:
            w_iode = 10 if satsys == 'E' else 8  # IODE bit width
            for gsys in self.gsys[satsys]:
                if len_payload < pos + w_iode + 13 + 12 + 12:
                    return 0
                iode = payload[pos:pos + w_iode].uint
                pos += w_iode
                i_radial = payload[pos:pos + 13]; pos += 13
                i_along  = payload[pos:pos + 12]; pos += 12
                i_cross  = payload[pos:pos + 12]; pos += 12
                d_radial = i_radial.int * 0.0025 \
                    if i_radial.bin != '1000000000000' else INVALID
                d_along  = i_along.int * 0.0080 \
                    if i_along.bin  != '100000000000'  else INVALID
                d_cross  = i_cross.int * 0.0080 \
                    if i_cross.bin  != '100000000000'  else INVALID
                msg_trace1 += \
                    f'ORBIT {gsys} IODE={iode:4d} d_radial={d_radial:7.4f}m' + \
                    f' d_track={d_along:7.4f}m d_cross={d_cross:7.4f}m\n'
        self.trace(1, msg_trace1)
        self.stat_both += stat_pos
        self.stat_bsat += pos - stat_pos
        return pos

    def decode_cssr_st3(self, payload, pos):
        len_payload = len(payload)
        stat_pos = pos
        msg_trace1 = ''
        for i, satsys in enumerate(self.satsys):
            for gsys in self.gsys[satsys]:
                if len_payload < pos + 15:
                    return 0
                ic0 = payload[pos:pos + 15].int
                pos += 15
                c0 = ic0 * 0.0016 if ic0 != -16384 else INVALID
                msg_trace1 += f"ST3 {gsys} d_clock={c0:4.1f}m\n"
        self.trace(1, msg_trace1)
        self.stat_both += stat_pos
        self.stat_bsat += pos - stat_pos
        return pos

    def decode_has_mt1_ckful(self, payload, pos):
        len_payload = len(payload)
        stat_pos = pos
        if len_payload < pos + 4:
            return 0
        vi = payload[pos:pos + 4].uint; pos += 4
        msg_trace1 = f'CKFUL validity_interval={HAS_VALIDITY_INTERVAL[vi]}s'
        msg_trace1 += f' ({vi})\n'
        if len_payload < pos + 2 * len(self.satsys):
            return 0
        multiplier = [1 for i in range(len(self.satsys))]
        for i, satsys in enumerate(self.satsys):
            multiplier[i] = payload[pos:pos + 2].uint + 1
            pos += 2
        for i, satsys in enumerate(self.satsys):
            for gsys in self.gsys[satsys]:
                if len_payload < pos + 13:
                    return 0
                ic0 = payload[pos:pos + 13];
                pos += 13
                if ic0.bin == '1000000000000':  # not available
                    c0 = INVALID
                elif ic0.bin == '0111111111111':  # the sat shall not be used
                    c0 = INVALID
                else:
                    c0 = ic0.int * 0.0025
                msg_trace1 += f"CKFUL {gsys} d_clock={c0:7.3f}m"
                msg_trace1 += f" (multiplier={multiplier[i]})\n"
        self.trace(1, msg_trace1)
        self.stat_both += stat_pos
        self.stat_bsat += pos - stat_pos
        return pos

    def decode_has_mt1_cksub(self, payload, pos):
        len_payload = len(payload)
        stat_pos = pos
        if len_payload < pos + 4 + 2:
            return 0
        ugnssid    = payload[pos:pos + 4].uint    ; pos +=  4
        multiplier = payload[pos:pos + 2].uint + 1; pos += 1
        msg_trace1 = ''
        for gsys in self.gsys[ugnss]:
            if len_payload < pos + 13:
                return 0
            ic0 = payload[pos:pos + 13];
            pos += 13
            if ic0.bin == '1000000000000':  # not available
                c0 = INVALID
            elif ic0.bin == '0111111111111':  # the sat shall not be used
                    c0 = INVALID
            else:
                c0 = multiplier * ic0.int * 0.0025
            msg_trace1 += f"CKSUB {gsys} d_clock={c0:7.3f}m"
            msg_trace1 += f" (x{multiplier[i]})\n"
        self.trace(1, msg_trace1)
        self.stat_both += stat_pos
        self.stat_bsat += pos - stat_pos
        return pos

    def _decode_code_bias(self, payload, pos, ssr_type):
        '''ssr_type: cssr or has'''
        if ssr_type not in {'cssr', 'has'}:
            raise
        len_payload = len(payload)
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
        msg_trace1 = ''
        if ssr_type == 'has':
            if len_payload < pos + 4:
                return 0
            vi = payload[pos:pos + 4].uint; pos += 4
            msg_trace1 = f'CBIAS validity_interval={HAS_VALIDITY_INTERVAL[vi]}s'
            msg_trace1 += f' ({vi})\n'
        if len(payload) < pos + 11 * nsigsat:
            return 0
        stat_pos = pos
        for i, satsys in enumerate(self.satsys):
            pos_mask = 0  # mask position
            for j, gsys in enumerate(self.gsys[satsys]):
                for k, gsig in enumerate(self.gsig[satsys]):
                    mask = self.cellmask[i][pos_mask]
                    pos_mask += 1
                    if not mask:
                        continue
                    cb = payload[pos:pos + 11].int
                    pos += 11
                    code_bias = cb * 0.02 if cb != -1024 else INVALID
                    if ssr_type == "cssr":
                        msg_trace1 += "ST4"
                    else:
                        msg_trace1 += "CBIAS"
                    msg_trace1 += f" {gsys} {gsig:13s} code_bias={code_bias:5.2f}m\n"
        self.trace(1, msg_trace1)
        self.stat_both += stat_pos
        self.stat_bsig += pos - stat_pos
        return pos

    def decode_cssr_st4(self, payload, pos):
        return self._decode_code_bias(payload, pos, 'cssr')

    def decode_has_mt1_cbias(self, payload, pos):
        return self._decode_code_bias(payload, pos, 'has')

    def decode_cssr_st5(self, payload, pos):
        len_payload = len(payload)
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
                    if len_payload < pos + 15 + 2:
                        return 0
                    pb = payload[pos:pos + 15].int ; pos += 15
                    di = payload[pos:pos +  2].uint; pos +=  2
                    phase_bias = pb * 0.001 if pb != -16384 else INVALID
                    msg_trace1 += \
                        f'ST5 {gsys} {gsig:13s}' + \
                        f' phase_bias={phase_bias:4.1f}m' + \
                        f' discont_indicator={di}\n'
        self.trace(1, msg_trace1)
        self.stat_both += stat_pos
        self.stat_bsig += pos - stat_pos
        return pos

    def decode_has_mt1_pbias(self, payload, pos):
        len_payload = len(payload)
        if len_payload < pos + 4:
            return 0
        vi = payload[pos:pos + 4].uint; pos += 4
        msg_trace1 = f'PBIAS validity_interval={HAS_VALIDITY_INTERVAL[vi]}s'
        msg_trace1 += f' ({vi})\n'
        stat_pos = pos
        for i, satsys in enumerate(self.satsys):
            pos_mask = 0
            for gsys in self.gsys[satsys]:
                for gsig in self.gsig[satsys]:
                    mask = self.cellmask[i][pos_mask]
                    pos_mask += 1
                    if not mask:
                        continue
                    if len_payload < pos + 11 + 2:
                        return 0
                    pb = payload[pos:pos + 11].int ; pos += 11
                    di = payload[pos:pos +  2].uint; pos +=  2
                    phase_bias = pb * 0.01 if pb != -1024 else INVALID
                    msg_trace1 += \
                        f'PBIAS {gsys} {gsig:13s}' + \
                        f' phase_bias={phase_bias:6.2f}cycle' + \
                        f' discont_indicator={di}\n'
        self.trace(1, msg_trace1)
        self.stat_both += stat_pos
        self.stat_bsig += pos - stat_pos
        return pos

    def decode_cssr_st6(self, payload, pos):
        len_payload = len(payload)
        if len_payload < 45:
            return 0
        stat_pos = pos
        f_cb = payload[pos:pos + 1].uint  # code bias existing flag
        pos += 1
        f_pb = payload[pos:pos + 1].uint  # phase bias existing flag
        pos += 1
        f_nb = payload[pos:pos + 1].uint  # network bias existing flag
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
            cnid = payload[pos:pos + 5].uint  # compact network ID
            pos += 5
            msg_trace1 += f"ST6 NID={cnid}\n"
            for satsys in self.satsys:
                ngsys = len(self.gsys[satsys])
                if len_payload < pos + ngsys:
                    return 0
                svmask[satsys] = payload[pos:pos + ngsys]
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
                        if len_payload < pos + 11:
                            return 0
                        cb = payload[pos:pos + 11].int
                        code_bias = cb * 0.02 if cb != -1024 else INVALID
                        pos += 11  # code bias
                        msg_trace1 += f" code_bias={code_bias:4.1f}m"
                    if f_pb:
                        if len_payload < pos + 15 + 2:
                            return 0
                        pb = payload[pos:pos + 15].int
                        phase_bias = pb * 0.001 if pb != -16384 else INVALID
                        pos += 15
                        di = payload[pos:pos + 2].uint
                        pos += 2
                        msg_trace1 += \
                        f" phase_bias={phase_bias:6.3f}m discont_indi={di}"
                    msg_trace1 += '\n'
        self.trace(1, msg_trace1)
        self.stat_both += stat_pos + 3
        self.stat_bsig += pos - stat_pos - 3
        return pos

    def decode_cssr_st7(self, payload, pos):
        len_payload = len(payload)
        if len_payload < 37:
            return 0
        stat_pos = pos
        msg_trace1 = ''
        for satsys in self.satsys:
            for gsys in self.gsys[satsys]:
                if len_payload < pos + 6:
                    return 0
                ura = payload[pos:pos + 6].uint
                pos += 6
                msg_trace1 += f"ST7 {gsys} URA {ura}\n"
        self.trace(1, msg_trace1)
        self.stat_both += stat_pos
        self.stat_bsat += pos - stat_pos
        return pos

    def decode_cssr_st8(self, payload, pos):
        len_payload = len(payload)
        if len_payload < 44:
            return 0
        stat_pos = pos
        stec_type = payload[pos:pos + 2].uint  # STEC correction type
        pos += 2
        cnid = payload[pos:pos + 5].uint  # compact network ID
        pos += 5
        svmask = {}
        for satsys in self.satsys:
            ngsys = len(self.gsys[satsys])
            if len_payload < pos + ngsys:
                return 0
            svmask[satsys] = payload[pos:pos + ngsys]
            pos += ngsys
        msg_trace1 = ''
        for satsys in self.satsys:
            for i, gsys in enumerate(self.gsys[satsys]):
                if not svmask[satsys][i]:
                    continue
                if len_payload < pos + 6 + 14:
                    return 0
                qi = payload[pos:pos + 6].uint  # quality indicator
                pos += 6
                ic00 = payload[pos:pos + 14].int
                c00 = ic00 * 0.05 if ic00 != -8192 else INVALID
                msg_trace1 += f"ST8 {gsys} c00={c00:5.2f}TECU"
                pos += 14
                if 1 <= stec_type:
                    if len_payload < pos + 12 + 12:
                        return 0
                    ic01 = payload[pos:pos + 12].int
                    c01 = ic01 * 0.02 if ic01 != -2048 else INVALID
                    pos += 12
                    ic10 = payload[pos:pos + 12].int
                    c10 = ic10 * 0.02 if ic10 != -2048 else INVALID
                    pos += 12
                    msg_trace1 += \
                        f" c01={c01:5.2f}TECU/deg c10={c10:5.2f}TECU/deg"
                if 2 <= stec_type:
                    if len_payload < pos + 10:
                        return 0
                    ic11 = payload[pos:pos + 10].int
                    c11 = ic11 * 0.02 if ic11 != -512 else INVALID
                    pos += 10
                    msg_trace1 += f" c11={c11:5.2f}TECU/deg^2"
                if 3 <= stec_type:
                    if len_payload < pos + 8 + 8:
                        return 0
                    ic02 = payload[pos:pos + 8].int
                    c02 = ic02 * 0.005 if ic02 != -128 else INVALID
                    pos += 8
                    ic20 = payload[pos:pos + 8].int
                    c20 = ic20 * 0.005 if ic20 != -128 else INVALID
                    pos += 8
                    msg_trace1 += \
                        f" c02={c02:5.2f}TECU/deg^2 c20={c20:5.2f}TECU/deg^2"
                msg_trace1 += '\n'
        self.trace(1, msg_trace1)
        self.stat_both += stat_pos + 7
        self.stat_bsat += pos - stat_pos - 7
        return pos

    def decode_cssr_st9(self, payload, pos):
        len_payload = len(payload)
        if len_payload < 45:
            return 0
        tctype = payload[pos:pos + 2].uint  # tropospheric correction type
        pos += 2
        crange = payload[pos:pos + 1].uint  # tropospheric correction range
        bw = 16 if crange else 7
        pos += 1
        cnid = payload[pos:pos + 5].uint  # compact network ID
        pos += 5
        svmask = {}
        for satsys in self.satsys:
            ngsys = len(self.gsys[satsys])
            if len_payload < pos + ngsys:
                return 0
            svmask[satsys] = payload[pos:pos + ngsys]
            pos += ngsys
        if len_payload < pos + 6 + 6:
            return 0
        tqi = payload[pos:pos + 6].uint  # tropospheric quality indicator
        pos += 6
        ngrid = payload[pos:pos + 6].uint  # number of grids
        pos += 6
        msg_trace1 = \
            f"ST9 Trop correct_type={tctype}" + \
            f" NID={cnid} quality={tqi} ngrid={ngrid}\n"
        for i in range(ngrid):
            if len_payload < pos + 9 + 8:
                return 0
            ivd_h = payload[pos:pos + 9].int  # hydrostatic vertical delay
            vd_h = ivd_h * 0.004 if ivd_h != -256 else INVALID
            pos += 9
            ivd_w = payload[pos:pos + 8].int  # wet vertical delay
            vd_w = ivd_w * 0.004 if ivd_w != -128 else INVALID
            pos += 8
            msg_trace1 += \
                f'ST9 Trop     grid {i+1:2d}/{ngrid:2d}' + \
                f' dry-delay={vd_h:6.3f}m wet-delay={vd_w:6.3f}m\n'
            for satsys in self.satsys:
                for j, gsys in enumerate(self.gsys[satsys]):
                    if not svmask[satsys][j]:
                        continue
                    if len_payload < pos + bw:
                        return 0
                    res = payload[pos:pos + bw].int
                    residual = res * 0.04
                    if (crange == 1 and res == -32767) or \
                       (crange == 0 and res == -64):
                        residual = INVALID
                    pos += bw
                    msg_trace1 += \
                        f'ST9 STEC {gsys} grid {i+1:2d}/{ngrid:2d}' + \
                        f' residual={residual:5.2f}TECU ({bw}bit)\n'
        self.trace(1, msg_trace1)
        self.stat_both += pos
        return pos

    def decode_cssr_st10(self, payload, pos):
        len_payload = len(payload)
        if len_payload < 5:
            return 0
        counter = payload[pos:pos+3].uint  # infomation message counter
        pos += 3
        datasize = (payload[pos:pos+2].uint + 1) * 40  # data size
        pos += 2
        if len_payload < pos + datasize:
            return 0
        aux_frame_data = payload[pos:pos+datasize]
        self.trace(1, f'ST10 {counter}:{aux_frame_data.hex}')
        pos += datasize
        self.stat_both += pos
        return pos

    def decode_cssr_st11(self, payload, pos):
        len_payload = len(payload)
        if len_payload < 40:
            return 0
        stat_pos = pos
        f_o = payload[pos:pos + 1].uint  # orbit existing flag
        pos += 1
        f_c = payload[pos:pos + 1].uint  # clock existing flag
        pos += 1
        f_n = payload[pos:pos + 1].uint  # network correction
        pos += 1
        msg_trace1 = \
            f"ST11 Orb={'on' if f_o else 'off'} " + \
            f"Clk={'on' if f_c else 'off'} " + \
            f"Net={'on' if f_n else 'off'}\n"
        if f_n:
            if len_payload < pos + 5:
                return 0
            cnid = payload[pos:pos + 5].uint  # compact network ID
            pos += 5
            msg_trace1 += f"ST11 NID={cnid}\n"
            svmask = {}
            for satsys in self.satsys:
                ngsys = len(self.gsys[satsys])
                if len_payload < pos + ngsys:
                    return 0
                svmask[satsys] = payload[pos:pos + ngsys]
                pos += ngsys
            for satsys in self.satsys:
                for i, gsys in enumerate(self.gsys[satsys]):
                    if not svmask[satsys][i]:
                        continue
                    msg_trace1 += f"ST11 {gsys}"
                    if f_o:
                        w_iode = 10 if satsys == 'E' else 8  # IODE width
                        if len_payload < pos + w_iode + 15 + 13 + 13:
                            return 0
                        iode = payload[pos:pos + w_iode].uint
                        pos += w_iode
                        id_radial = payload[pos:pos + 15].int
                        d_radial = id_radial * 0.0016 if id_radial != -16384 \
                                   else INVALID
                        pos += 15
                        id_along = payload[pos:pos + 13].int
                        d_along = id_along * 0.0064 if id_along != -4096 \
                                    else INVALID
                        pos += 13
                        id_cross = payload[pos:pos + 13].int
                        d_cross = id_cross * 0.0064 if id_cross != -4096 \
                                    else INVALID
                        pos += 13
                        msg_trace1 += \
                            f" IODE={iode:4d} d_radial={d_radial:5.1f}m" + \
                            f" d_along={d_along:5.1f}m d_cross={d_cross:5.1f}m"
                    if f_c:
                        if len_payload < pos + 15:
                            return 0
                        ic0 = payload[pos:pos + 15].int
                        c0 = ic0 * 0.0016 if ic0 != -16384 else INVALID
                        pos += 15
                        msg_trace1 += f" c0={c0:5.1f}m"
                    msg_trace1 += "\n"
        self.trace(1, msg_trace1)
        self.stat_both += stat_pos + 3
        self.stat_bsat += pos - stat_pos - 3
        if f_n:  # correct bit number because because we count up bsat as NID
            self.stat_both += 5
            self.stat_bsat -= 5
        return pos

    def decode_cssr_st12(self, payload, pos):
        len_payload = len(payload)
        if len_payload < 52:
            return 0
        tropo = payload[pos:pos + 2]  # Tropospheric correction avail
        pos += 2
        stec = payload[pos:pos + 2]  # STEC correction avail
        pos += 2
        cnid = payload[pos:pos + 5].uint  # compact network ID
        pos += 5
        ngrid = payload[pos:pos + 6].uint  # number of grids
        pos += 6
        msg_trace1 = \
            f"ST12 tropo={tropo} stec={stec} NID={cnid} ngrid={ngrid}\n" + \
            f"ST12 Trop"
        if tropo[0]:
            # 0 <= ttype (forward reference)
            if len_payload < pos + 6 + 2 + 9:
                return 0
            tqi = payload[pos:pos + 6].uint  # tropo quality indicator
            pos += 6
            ttype = payload[pos:pos + 2].uint  # tropo correction type
            pos += 2
            it00 = payload[pos:pos + 9].int  # tropo poly coeff
            t00 = it00 * 0.004 if it00 != -256 else INVALID
            pos += 9
            msg_trace1 += f" quality={tqi} correct_type(0-2)={ttype}" + \
                          f" t00={t00:6.2f}m"
            if 1 <= ttype:
                if len_payload < pos + 7 + 7:
                    return 0
                it01 = payload[pos:pos + 7].int
                t01 = it01 * 0.002 if it01 != -64 else INVALID
                pos += 7
                it10 = payload[pos:pos + 7].int
                t10 = it10 * 0.002 if it10 != -64 else INVALID
                pos += 7
                msg_trace1 += f" t01={t01:5.2f}m/deg t10={t10:5.2f}m/deg"
            if 2 <= ttype:
                if len_payload < pos + 7:
                    return 0
                it11 = payload[pos:pos + 7].int
                t11 = it11 * 0.001 if it11 != -64 else INVALID
                pos += 7
                msg_trace1 += f" t11={t11:5.2f}m/deg^2"
            msg_trace1 += '\n'
        if tropo[1]:
            if len_payload < pos + 1 + 4:
                return 0
            trs = payload[pos:pos + 1].uint  # tropo residual size
            pos += 1
            bw = 8 if trs else 6
            itro = payload[pos:pos + 4].uint  # tropo residual offset
            pos += 4
            tro = itro * 0.02
            msg_trace1 += f"ST12 Trop offset={tro:5.2f}m\n"
            if len_payload < pos + bw * ngrid:
                return 0
            for i in range(ngrid):
                itr = payload[pos:pos + bw].int  # troposphere residual
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
                if len_payload < pos + ngsys:
                    return 0
                svmask[satsys] = payload[pos:pos + ngsys]
                pos += ngsys
            for satsys in self.satsys:
                for i, gsys in enumerate(self.gsys[satsys]):
                    if not svmask[satsys][i]:
                        continue
                    if len_payload < pos + 6 + 2 + 14:
                        return 0
                    sqi = payload[pos:pos + 6].uint  # quality indicator
                    pos += 6
                    sct = payload[pos:pos + 2].uint  # correction type
                    pos += 2
                    ic00 = payload[pos:pos + 14].int
                    c00 = ic00 * 0.05 if ic00 != -8192 else INVALID
                    pos += 14
                    msg_trace1 += \
                        f"ST12 STEC {gsys} quality={sqi:02x} type={sct}" + \
                        f" c00={c00:.1f}TECU"
                    if 1 <= sct:
                        if len_payload < pos + 12 + 12:
                            return 0
                        ic01 = payload[pos:pos + 12].int
                        c01 = ic01 * 0.02 if ic01 != -2048 else INVALID
                        pos += 12
                        ic10 = payload[pos:pos + 12].int
                        c10 = ic10 * 0.02 if ic10 != -2048 else INVALID
                        pos += 12
                        msg_trace1 += \
                            f" c01={c01:.1f}TECU/deg c10={c10:.1f}TECU/deg"
                    if 2 <= sct:
                        if len_payload < pos + 10:
                            return 0
                        ic11 = payload[pos:pos + 10].int
                        c11 = ic11 * 0.02 if ic11 != -512 else INVALID
                        pos += 10
                        msg_trace1 += f" c11={c11:.1f}TECU/deg^2"
                    if 3 <= sct:
                        if len_payload < pos + 8 + 8:
                            return 0
                        ic02 = payload[pos:pos + 8].int
                        c02 = ic02 * 0.005 if ic02 != -128 else INVALID
                        pos += 8
                        ic20 = payload[pos:pos + 8].int
                        c20 = ic20 * 0.005 if ic20 != -128 else INVALID
                        pos += 8
                        msg_trace1 += \
                            f" c02={c02:.1f}TECU/deg^2 c20={c20:.1f}TECU/deg^2"
                    msg_trace1 += '\n'
                    if len_payload < pos + 2:
                        return 0
                    srs = payload[pos:pos + 2].uint  # STEC residual size
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
                        if len_payload < pos + bw:
                            return 0
                        isr = payload[pos:pos + bw].int
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
        self.trace(1, msg_trace1)
        self.stat_both += stat_pos
        self.stat_bsat += pos - stat_pos
        return pos

def gnssid2satsys(gnssid):
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

def sigmask2signame(satsys, sigmask):
    signame = f'satsys={satsys} sigmask={sigmask}'
    if satsys == 'G':
        signame = [
            "L1 C/A",
            "L1 P",
            "L1 Z-tracking",
            "L1C(D)",
            "L1C(P)",
            "L1C(D+P)",
            "L2 CM",
            "L2 CL",
            "L2 CM+CL",
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
            "E1 B",
            "E1 C",
            "E1 B+C",
            "E5a I",
            "E5a Q",
            "E5a I+Q",
            "E5b I",
            "E5b Q",
            "E5b I+Q",
            "E5 I",
            "E5 Q",
            "E5 I+Q",
            "E6 B",
            "E6 C",
            "E6 B+C",
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

# EOF
