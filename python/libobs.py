#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# libobs.py: library for RTCM observation message processing
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022-2024 Satoshi Takahashi
#
# Released under BSD 2-clause license.
#
# References:
# [1] Radio Technical Commission for Maritime Services (RTCM),
#     Differential GNSS (Global Navigation Satellite Systems) Services
#     - Version 3, RTCM Standard 10403.3, Apr. 24 2020.

class Obs:
    '''RTCM observation class'''
    def __init__(self, trace):
        self.trace = trace

    def decode_obs(self, payload, satsys, mtype):
        ''' decodes observation message and returns message '''
        be = 'u30' if satsys != 'R' else 'u27'  # bit format of epoch time
        bp = 'u24' if satsys != 'R' else 'u25'  # bit format of pseudorange
        bi =  'u8' if satsys != 'R' else  'u7'  # bit format of pseudorange mod ambiguity
        sid   = payload.read('u12')  # reference station id, DF003
        tow   = payload.read(  be )  # epoch time, DF004 (GPS), DF034 (GLONASS)
        sync  = payload.read( 'u1')  # synchronous flag, DF005
        nsat  = payload.read( 'u5')  # number of signals, DF006 (GPS)
        smind = payload.read( 'u1')  # divrgence-free smoothing ind, DF007
        smint = payload.read( 'u3')  # smoothing interval, DF008
        msg = ''
        for _ in range(nsat):
            satid     = payload.read( 'u6')  # satellite id, DF009, DF038
            cind1     = payload.read( 'u1')  # L1 code indicator, DF010, DF039
            if satsys == 'R':
                fc    = payload.read( 'u5')  # freq. channel number, DF040
            pr1       = payload.read(  bp )  # L1 pseudorange, DF011, DF041
            phpr1     = payload.read('i20')  # L1 phaserange-pseudorange, DF012, DF042
            lti1      = payload.read( 'u7')  # L1 locktime ind, DF013, DF043
            if 'Full' in mtype:
                pma1  = payload.read(  bi )  # L1 pseudorange modulus ambiguity, DF014, DF044
                cnr1  = payload.read( 'u8')  # L1 CNR, DF015, DF045
            if 'L2' in mtype:
                cind2 = payload.read( 'u2')  # L2 code indicator, DF016, DF046
                prd   = payload.read('i14')  # L2-L1 pseudorange difference, DF017, DF047
                phpr2 = payload.read('i20')  # L2 phaserange-L1 pseudorange, DF018, DF048
                lti2  = payload.read( 'u7')  # L2 locktime ind, DF019, DF049
                if mtype in 'Full':
                    cnr2  = payload.read( 'u8')  # L2 CNR, DF020, DF050
            if satsys != 'S':
                msg += f'{satsys}{satid:02} '
            else:
                msg += f'{satsys}{satid+119:3} '
        return msg

    def decode_msm(self, payload, satsys, mtype):
        ''' decodes MSM message and returns message '''
        sid    = payload.read('u12')  # reference station id, DF003
        epoch  = payload.read('u30')  # GNSS epoch time, DF004
        mm     = payload.read( 'u1')  # multiple message bit, DF393
        iods   = payload.read( 'u3')  # issue of data station, DF409
        payload.pos += 7              # reserved, DF001
        csi    = payload.read( 'u2')  # clock steering ind, DF411
        eci    = payload.read( 'u2')  # external clock ind, DF412
        smind  = payload.read( 'u1')  # divergence-free smoothing ind, DF417
        smint  = payload.read( 'u3')  # smoothing interval, DF418
        sat_mask = [0 for _ in range(64)]
        nsat = 0
        for satid in range(64):
            mask = payload.read('u1')  # satellite mask, DF394
            if mask:
                sat_mask[nsat] = satid
                nsat += 1
        sig_mask = [0 for _ in range(32)]
        nsig = 0
        for sigid in range(32):
            mask = payload.read('u1')  # signal mask, DF395
            if mask:
                sig_mask[nsig] = sigid
                nsig += 1
        cell_mask = [0 for _ in range(nsat * nsig)]
        n_cell_mask = 0
        for maskpos in range(nsat * nsig):
            mask = payload.read('u1')  # cell mask, DF396
            cell_mask[maskpos] = mask
            if mask:
                n_cell_mask += 1
        if '4' in mtype or '5' in mtype or '6' in mtype or '7' in mtype:
            for _ in range(nsat):
                rng  = payload.read('u8')   # rough ranges, DF398
        if '5' in mtype or '7' in mtype:
            for _ in range(nsat):
                einf = payload.read('u4')   # sat specific extended info
        for _ in range(nsat):
            rng_m    = payload.read('u10')  # range mod 1 ms, DF398
        if '5' in mtype or '7' in mtype:
            for _ in range(nsat):
                prr  = payload.read('i14')  # phase range rates, DF399
        for maskpos in range(nsat * nsig):
            if not cell_mask[maskpos]:
                continue
            bfpsr = 'i15'  # bit format of fine pseudorange
            bfphr = 'i22'  # bit format of fine phaserange
            blti  =  'u4'  # bit format of lock time indicator
            bcnr  =  'u6'  # bit format of CNR
            if '6' in mtype or '7' in mtype:
                bfpsr = 'i20'  # extended bit format for fine pseudorange
                bfphr = 'i24'  # extended bit format for fine phaserange
                blti  = 'u10'  # extended bit format for lock time indicator
                bcnr  = 'u10'  # extended bit format for CNR
            if '1' in mtype or '3' in mtype or '4' in mtype or \
               '5' in mtype or '6' in mtype or '7' in mtype:
                fpsr = payload.read(bfpsr)  # fine pseudorange, DF400, DF405
            if '2' in mtype or '3' in mtype or '4' in mtype or \
               '5' in mtype or '6' in mtype or '7' in mtype:
                fphr = payload.read(bfphr)  # fine phaserange, DF401, DF406
                lti  = payload.read( blti)  # lock time ind, DF402, DF407
                hai  = payload.read(   1 )  # half-cycle ambiguity, DF420
            if '4' in mtype or '5' in mtype or '6' in mtype or '7' in mtype:
                cnr  = payload.read(bcnr )  # CNR, DF403, 408
            if '5' in mtype or '7' in mtype:
                fphr = payload.read('i15')  # fine phaserange rate, DF404
        msg = ''
        if satsys != 'S':
            for satid in range(nsat):
                msg += f'{satsys}{sat_mask[satid]+1:02} '
        else:
            for satid in range(nsat):
                msg += f'{satsys}{sat_mask[satid]+119:3} '
        return msg

# EOF
