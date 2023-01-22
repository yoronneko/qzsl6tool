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

    def decode_obs(self, payload, pos, satsys, mtype):
        '''decodes observation message and returns pos and string'''
        sid = payload[pos:pos+12].uint
        pos += 12
        # reference station id
        be = 30 if satsys != 'R' else 27 # bit width of GPS epoch time
        bp = 24 if satsys != 'R' else 25 # bit width of GPS pseudorange
        bi = 8  if satsys != 'R' else  7
                    # bit width of GPS integer phase modurus ambiguity
        tow = payload[pos:pos+be].uint  # epoch time
        pos += be
        sync_flag = payload[pos:pos+1]  # synchronous GNSS flag
        pos += 1
        nsat = payload[pos:pos+5].uint  # num of satellite signals processed
        pos += 5
        sind = payload[pos:pos+1]  # divergence-free smooting indicator
        pos += 1
        sint = payload[pos:pos+3]  # smoothing interval
        pos += 3  # GPS 64 bit GLO 61 bit
        for i in range(nsat):
            satid = payload[pos:pos+6].uint  # satellite id
            pos += 6
            cind1 = payload[pos:pos+1]  # L1 code indicator
            pos += 1
            if satsys == 'R':
                fnc = payload[pos:pos+5].uint  # frequency channel number
                pos += 5
            pr1 = payload[pos:pos+bp].uint  # L1 pseudorange
            pos += bp
            phpr1 = payload[pos:pos+20].int  # L1 phaserange-pseudorange
            pos += 20
            lti1 = payload[pos:pos+7].uint  # L1 lock time indicator
            pos += 7  # 58 bit
            if mtype in 'Full':
                pma1 = payload[pos:pos+bi].uint  # interger pseudorange modulus ambiguity
                pos += bi
                cnr1 = payload[pos:pos+8].uint  # L1 CNR
                pos += 8
            if mtype in 'L2':
                cind2 = payload[pos:pos+2].int  # L2 code indicator
                pos += 2
                prd = payload[pos:pos+14].int  # L2-L1 pseudorange difference
                pos += 14
                phpr2 = payload[pos:pos+20].int  # L2 phase-L1 pseudo range
                pos += 20
                lti2 = payload[pos:pos+7].uint  # L2 locktime indicator
                pos += 7
                cnr2 = payload[pos:pos+8].uint  # L2 CNR
                pos += 8
        string = ''
        return pos, string

    def decode_msm(self, payload, pos, satsys, mtype):
        '''decodes MSM message and returns pos and string'''
        rsid = payload[pos:pos+12].uint  # reference station id
        pos += 12
        epoch = payload[pos:pos+30].uint  # GNSS epoch time
        pos += 30
        mm = payload[pos:pos+1]  # multiple message bit
        pos += 1
        iods = payload[pos:pos+3].uint  # issue of data station
        pos += 3
        pos += 7  # reserved
        clk_s = payload[pos:pos+2].uint  # clock steering indicator
        pos += 2
        cls_e = payload[pos:pos+2].uint  # external clock indicator
        pos += 2
        smth = payload[pos:pos+1]  # divergence-free smoothing indicator
        pos += 1
        tint_s = payload[pos:pos+3].uint  # smoothing interval
        pos += 3
        sat_mask = [0 for i in range(64)]
        n_sat = 0
        for i in range(64):
            mask = payload[pos:pos+1]  # satellite mask
            pos += 1
            if mask:
                sat_mask[n_sat] = i
                n_sat += 1
        sig_mask = [0 for i in range(32)]
        n_sig = 0
        for i in range(32):
            mask = payload[pos:pos+1]  # signal mask
            pos += 1
            if mask:
                sig_mask[n_sig] = i
                n_sig += 1
        cell_mask = [0 for i in range(n_sat * n_sig)]
        n_cell_mask = 0
        for i in range(n_sat * n_sig):
            mask = payload[pos:pos+1]  # cell mask
            cell_mask[i] = mask
            pos += 1
            if mask:
                n_cell_mask += 1
        if '4' in mtype or '5' in mtype or '6' in mtype or '7' in mtype:
            for i in range(n_sat):
                rng = payload[pos:pos+8].uint  # rough ranges
                pos += 8
        if '5' in mtype or '7' in mtype:
            for i in range(n_sat):
                esatinfo = payload[pos:pos+4].uint  # extended satellite info
                pos += 4
        for i in range(n_sat):
            rng_m = payload[pos:pos+10].uint  # rough ranges modulo 1 ms
            pos += 10
        if '5' in mtype or '7' in mtype:
            for i in range(n_sat):
                prr = payload[pos:pos+14].int  # rough phase range rates
                pos += 14
        for i in range(n_sat * n_sig):  # pseudorange
            if not cell_mask[i]:
                continue
            bfpsr = 15  # bit size of fine pseudorange
            bfphr = 22  # bit size of fine phaserange
            blti = 4    # bit size of lock time indicator
            bcnr = 6    # bit size of CNR
            if '6' in mtype or '7' in mtype:
                bfpsr = 20  # extended bit size for fine pseudorange
                bfphr = 24  # extended bit size for fine phaserange
                blti = 10   # extended bit size for lock time indicator
                bcnr = 10   # extended bit size for CNR
            if '1' in mtype or '3' in mtype or '4' in mtype or \
               '5' in mtype or '6' in mtype or '7' in mtype:
                fpsr = payload[pos:pos+bfpsr].int  # fine pseudorange
                pos += bfpsr
            if '2' in mtype or '3' in mtype or '4' in mtype or \
               '5' in mtype or '6' in mtype or '7' in mtype:
                fphr = payload[pos:pos+bfphr].int  # fine phaserange
                pos += bfphr
                lti = payload[pos:pos+blti].uint  # lock time indicator
                pos += blti
                hai = payload[pos:pos+1]  # half ambiguity indicator
                pos += 1
            if '4' in mtype or '5' in mtype or '6' in mtype or '7' in mtype:
                cnr = payload[pos:pos+bcnr].uint  # CNR
                pos += bcnr
            if '5' in mtype or '7' in mtype:
                fphrr = payload[pos:pos+15].int  # fine phaserange rates
                pos += 15
        string = ''
        if satsys != 'S':
            for i in range(n_sat):
                string += f'{satsys}{sat_mask[i]+1:02} '
        else:
            for i in range(n_sat):
                string += f'{satsys}{sat_mask[i]+119:3} '
        return pos, string

# EOF
