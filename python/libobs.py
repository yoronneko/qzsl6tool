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
        '''decodes observation message and returns pos and string'''
        be = 'u30' if satsys != 'R' else 'u27'  # bit format of epoch time
        bp = 'u24' if satsys != 'R' else 'u25'  # bit format of pseudorange (pr)
        bi =  'u8' if satsys != 'R' else  'u7'  # bit format of pr ambiguity
        sid  = payload.read('u12')  # station id, DF003
        tow  = payload.read(  be )  # epoch time
        sync = payload.read( 'u1')  # synchronous flag
        n_sat = payload.read( 'u5')  # number of signals
        sind = payload.read( 'u1')  # smoothing indicator
        sint = payload.read( 'u3')  # smoothing interval
        string = ''
        for _ in range(n_sat):
            satid     = payload.read( 'u6')  # satellite id
            cind1     = payload.read( 'u1')  # L1 code indicator
            if satsys == 'R':
                fc    = payload.read( 'u5')  # freq ch
            pr1       = payload.read(  bp )  # L1 pseudorange
            phpr1     = payload.read('i20')  # L1 phase-pr
            lti1      = payload.read( 'u7')  # L1 locktime ind
            if mtype in 'Full':
                pma1  = payload.read(  bi )  # pr ambiguity
                cnr1  = payload.read( 'u8')  # L1 CNR
            if mtype in 'L2':
                cind2 = payload.read( 'u2')  # L2 code indicator
                prd   = payload.read('i14')  # L2-L1 pr diff
                phpr2 = payload.read('i20')  # L2 phase-L1 pr
                lti2  = payload.read( 'u7')  # L2 locktime ind
                cnr2  = payload.read( 'u8')  # L2 CNR
            if satsys != 'S':
                string += f'{satsys}{satid:02} '
            else:
                string += f'{satsys}{satid+119:3} '
        return string

    def decode_msm(self, payload, satsys, mtype):
        '''decodes MSM message and returns pos and string'''
        rid    = payload.read('u12')  # reference station id, DF003
        epoch  = payload.read('u30')  # GNSS epoch time
        mm     = payload.read( 'u1')  # multiple message bit, DF393
        iods   = payload.read( 'u3')  # issue of data station, DF409
        payload.pos += 7              # reserved, DF001
        csi    = payload.read( 'u2')  # clock steering ind, DF411
        eci    = payload.read( 'u2')  # external clock ind, DF412
        sid    = payload.read( 'u1')  # divergence-free smooting, DF417
        smint  = payload.read( 'u3')  # smoothing interval, DF418
        sat_mask = [0 for _ in range(64)]
        n_sat = 0
        for satid in range(64):
            mask = payload.read('u1')  # satellite mask, DF394
            if mask:
                sat_mask[n_sat] = satid
                n_sat += 1
        sig_mask = [0 for _ in range(32)]
        n_sig = 0
        for sigid in range(32):
            mask = payload.read('u1')  # signal mask, DF395
            if mask:
                sig_mask[n_sig] = sigid
                n_sig += 1
        cell_mask = [0 for _ in range(n_sat * n_sig)]
        n_cell_mask = 0
        for maskpos in range(n_sat * n_sig):
            mask = payload.read('u1')  # cell mask, DF396
            cell_mask[maskpos] = mask
            if mask:
                n_cell_mask += 1
        if '4' in mtype or '5' in mtype or '6' in mtype or '7' in mtype:
            for _ in range(n_sat):
                rng  = payload.read('u8')  # rough ranges, DF398
        if '5' in mtype or '7' in mtype:
            for _ in range(n_sat):
                einf = payload.read('u4')  # sat specific extended info
        for _ in range(n_sat):
            rng_m    = payload.read('u10')  # range mod 1 ms, DF398
        if '5' in mtype or '7' in mtype:
            for _ in range(n_sat):
                prr  = payload.read('i14')  # phase range rates, DF399
        for maskpos in range(n_sat * n_sig):
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
                fpsr = payload.read(bfpsr)  # fine pseudorange, DF400, 405
            if '2' in mtype or '3' in mtype or '4' in mtype or \
               '5' in mtype or '6' in mtype or '7' in mtype:
                fphr = payload.read(bfphr)  # fine phaserange, DF401, 406
                lti  = payload.read( blti)  # lock time ind, DF402, 407
                hai  = payload.read( 'u1')  # half-cycle ambiguity, DF420
            if '4' in mtype or '5' in mtype or '6' in mtype or '7' in mtype:
                cnr  = payload.read(bcnr )  # CNR, DF403, 408
            if '5' in mtype or '7' in mtype:
                fphr = payload.read('i15')  # fine phaserange rate, DF404
        string = ''
        if satsys != 'S':
            for satid in range(n_sat):
                string += f'{satsys}{sat_mask[satid]+1:02} '
        else:
            for satid in range(n_sat):
                string += f'{satsys}{sat_mask[satid]+119:3} '
        return string

# EOF
