#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# libobs.py: library for RTCM observation message processing
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

class Obs:
    '''RTCM observation class'''
    def __init__(self, fp_disp, t_level, msg_color):
        self.fp_disp   = fp_disp
        self.t_level   = t_level
        self.msg_color = msg_color

    def trace(self, level, *args):
        if self.t_level < level or not self.fp_disp:
            return
        for arg in args:
            try:
                print(arg, end='', file=self.fp_disp)
            except (BrokenPipeError, IOError):
                sys.exit()

    def decode_obs(self, payload, pos, satsys, mtype):
        '''decodes observation message and returns pos and string'''
        be = 30 if satsys != 'R' else 27  # bit width of epoch time
        bp = 24 if satsys != 'R' else 25  # bit width of pseudorange (pr)
        bi = 8  if satsys != 'R' else  7  # bit width of pr ambiguity
        sid  = payload[pos:pos+12].uint; pos += 12  # station id, DF003
        tow  = payload[pos:pos+be].uint; pos += be  # epoch time
        sync = payload[pos:pos+ 1]     ; pos +=  1  # synchronous flag
        nsat = payload[pos:pos+ 5].uint; pos +=  5  # number of signals
        sind = payload[pos:pos+ 1]     ; pos +=  1  # smoothing indicator
        sint = payload[pos:pos+ 3]     ; pos +=  3  # smoothing interval
        for i in range(nsat):
            satid     = payload[pos:pos+ 6].uint; pos +=  6  # satellite id
            cind1     = payload[pos:pos+ 1]     ; pos +=  1  # L1 code indicator
            if satsys == 'R':
                fc    = payload[pos:pos+ 5].uint; pos +=  5  # freq ch
            pr1       = payload[pos:pos+bp].uint; pos += bp  # L1 pseudorange
            phpr1     = payload[pos:pos+20].int ; pos += 20  # L1 phase-pr
            lti1      = payload[pos:pos+ 7].uint; pos +=  7  # L1 locktime ind
            if mtype in 'Full':
                pma1  = payload[pos:pos+bi].uint; pos += bi  # pr ambiguity
                cnr1  = payload[pos:pos+ 8].uint; pos +=  8  # L1 CNR
            if mtype in 'L2':
                cind2 = payload[pos:pos+ 2]     ; pos +=  2  # L2 code indicator
                prd   = payload[pos:pos+14].int ; pos += 14  # L2-L1 pr diff
                phpr2 = payload[pos:pos+20].int ; pos += 20  # L2 phase-L1 pr
                lti2  = payload[pos:pos+ 7].uint; pos +=  7  # L2 locktime ind
                cnr2  = payload[pos:pos+ 8].uint; pos +=  8  # L2 CNR
        string = ''
        return pos, string

    def decode_msm(self, payload, pos, satsys, mtype):
        '''decodes MSM message and returns pos and string'''
        rsid   = payload[pos:pos+12].uint; pos += 12  # reference station id
        epoch  = payload[pos:pos+30].uint; pos += 30  # GNSS epoch time
        mm     = payload[pos:pos+ 1]     ; pos +=  1  # multiple message bit
        iods   = payload[pos:pos+ 3].uint; pos +=  3  # issue of data station
        pos += 7                                      # reserved
        clk_s  = payload[pos:pos+ 2].uint; pos +=  2  # clock steering ind
        cls_e  = payload[pos:pos+ 2].uint; pos +=  2  # external clock ind
        smth   = payload[pos:pos+ 1]     ; pos +=  1  # smoothing indicator
        tint_s = payload[pos:pos+ 3].uint; pos +=  3  # smoothing interval
        sat_mask = [0 for i in range(64)]
        n_sat = 0
        for i in range(64):
            mask = payload[pos:pos+1]; pos +=  1  # satellite mask
            if mask:
                sat_mask[n_sat] = i
                n_sat += 1
        sig_mask = [0 for i in range(32)]
        n_sig = 0
        for i in range(32):
            mask = payload[pos:pos+1]; pos += 1  # signal mask
            if mask:
                sig_mask[n_sig] = i
                n_sig += 1
        cell_mask = [0 for i in range(n_sat * n_sig)]
        n_cell_mask = 0
        for i in range(n_sat * n_sig):
            mask = payload[pos:pos+1]; pos += 1  # cell mask
            cell_mask[i] = mask
            if mask:
                n_cell_mask += 1
        if '4' in mtype or '5' in mtype or '6' in mtype or '7' in mtype:
            for i in range(n_sat):
                rng   = payload[pos:pos+ 8].uint; pos +=  8  # rough ranges
        if '5' in mtype or '7' in mtype:
            for i in range(n_sat):
                einfo = payload[pos:pos+ 4].uint; pos +=  4 # extended info
        for i in range(n_sat):
            rng_m     = payload[pos:pos+10].uint; pos += 10 # range mod 1 ms
        if '5' in mtype or '7' in mtype:
            for i in range(n_sat):
                prr   = payload[pos:pos+14].int ; pos += 14 # phase range rates
        for i in range(n_sat * n_sig):  # pseudorange
            if not cell_mask[i]:
                continue
            bfpsr = 15  # bit size of fine pseudorange
            bfphr = 22  # bit size of fine phaserange
            blti  =  4  # bit size of lock time indicator
            bcnr  =  6  # bit size of CNR
            if '6' in mtype or '7' in mtype:
                bfpsr = 20  # extended bit size for fine pseudorange
                bfphr = 24  # extended bit size for fine phaserange
                blti  = 10  # extended bit size for lock time indicator
                bcnr  = 10  # extended bit size for CNR
            if '1' in mtype or '3' in mtype or '4' in mtype or \
               '5' in mtype or '6' in mtype or '7' in mtype:
                fpsr = payload[pos:pos+bfpsr].int ; pos += bfpsr  # fine pr
            if '2' in mtype or '3' in mtype or '4' in mtype or \
               '5' in mtype or '6' in mtype or '7' in mtype:
                fphr = payload[pos:pos+bfphr].int ; pos += bfphr  # fine phase
                lti  = payload[pos:pos+ blti].uint; pos +=  blti  # lock time
                hai  = payload[pos:pos+    1]     ; pos +=     1  # half amb
            if '4' in mtype or '5' in mtype or '6' in mtype or '7' in mtype:
                cnr  = payload[pos:pos+ bcnr].uint; pos +=  bcnr  # CNR
            if '5' in mtype or '7' in mtype:
                fphr = payload[pos:pos+   15].int ; pos +=    15  # fine phase
        string = ''
        if satsys != 'S':
            for i in range(n_sat):
                string += f'{satsys}{sat_mask[i]+1:02} '
        else:
            for i in range(n_sat):
                string += f'{satsys}{sat_mask[i]+119:3} '
        return pos, string

# EOF

