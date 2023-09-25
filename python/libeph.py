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

FMT_IODC = '<4d'    # format string for issue of data clock
FMT_IODE = '<4d'    # format string for issue of data ephemeris

class Eph:
    '''Ephemeris class'''
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

    def decode_ephemerides(self, payload, pos, satsys, mtype):
        '''returns pos and string'''
        payload.pos = pos
        string = ''
        if satsys == 'G':  # GPS ephemerides
            svid = payload.read( 'u6')  # satellite id, DF009
            wn   = payload.read('u10')  # week number, DF076
            sva  = payload.read( 'u4')  # SV accuracy DF077
            gpsc = payload.read(   2 )  # GPS code L2, DF078
            idot = payload.read('i14')  # IDOT, DF079
            iode = payload.read( 'u8')  # IODE, DF071
            toc  = payload.read('u16')  # t_oc, DF081
            af2  = payload.read( 'i8')  # a_f2, DF082
            af1  = payload.read('i16')  # a_f1, DF083
            af0  = payload.read('i22')  # a_f0, DF084
            iodc = payload.read('u10')  # IODC, DF085
            crs  = payload.read('i16')  # C_rs, DF086
            dn   = payload.read('i16')  # d_n,  DF087
            m0   = payload.read('i32')  # M_0,  DF088
            cuc  = payload.read('i16')  # C_uc, DF089
            e    = payload.read('u32')  # e,    DF090
            cus  = payload.read('i16')  # C_us, DF091
            a12  = payload.read('u32')  # a12,  DF092
            toe  = payload.read('u16')  # t_oe, DF093
            cic  = payload.read('i16')  # C_ic, DF094
            omg0 = payload.read('i32')  # Omg0, DF095
            cis  = payload.read('i16')  # C_is, DF096
            i0   = payload.read('i32')  # i_0,  DF097
            crc  = payload.read('i16')  # C_rc, DF098
            omg  = payload.read('i32')  # omg,  DF099
            omgd = payload.read('i24')  # Omg-dot, DF100
            tgd  = payload.read( 'i8')  # t_GD, DF101
            svh  = payload.read( 'u6')  # SV health, DF102
            l2p  = payload.read(   1 )  # P flag, DF103
            fi   = payload.read(   1 )  # fit interval, DF137
            string += f'G{svid:02d} WN={wn} IODE={iode:{FMT_IODE}} IODC={iodc:{FMT_IODC}}'
            if   gpsc == '0b01': string += ' L2P'
            elif gpsc == '0b10': string += ' L2C/A'
            elif gpsc == '0b11': string += ' L2C'
            else: raise Exception(f'undefined GPS code on L2: {gpsc}')
            if svh:
                string += self.msg_color.fg('red') + \
                    f' unhealthy({svh:02x})' + self.msg_color.fg()
        elif satsys == 'R':  # GLONASS ephemerides
            svid   = payload.read( 'u6')  # satellite id, DF038
            fcn    = payload.read( 'u5')  # freq ch, DF040
            svh    = payload.read(   1 )  # alm health DF104
            aha    = payload.read(   1 )  # alm health avail, DF105
            p1     = payload.read(   2 )  # P1, DF106
            tk     = payload.read(  12 )  # t_k, DF107
            bn     = payload.read(   1 )  # B_n word MSB, DF108
            p2     = payload.read(   1 )  # P2, DF109
            tb     = payload.read( 'u7')  # t_b, DF110
            _sgn   = payload.read( 'u1')  # x_n dot, DF111
            xnd    = payload.read('u23')  * (1 - _sgn * 2)
            sgn    = payload.read( 'u1')  # x_n, DF112
            xn     = payload.read('u26')  * (1 - _sgn * 2)
            _sgn   = payload.read( 'u1')  # x_n dot^2, DF113
            xndd   = payload.read( 'u4')  * (1 - _sgn * 2)
            _sgn   = payload.read( 'u1')  # y_n dot, DF114
            ynd    = payload.read('u23')  * (1 - _sgn * 2)
            _sgn   = payload.read( 'u1')  # y_n, DF115
            yn     = payload.read('u26')  * (1 - _sgn * 2)
            _sgn   = payload.read( 'u1')  # y_n dot^2, DF116
            yndd   = payload.read( 'u4')  * (1 - _sgn * 2)
            _sgn   = payload.read( 'u1')  # z_n dot, DF117
            znd    = payload.read('u23')  * (1 - _sgn * 2)
            _sgn   = payload.read( 'u1')  # z_n, DF118
            zn     = payload.read('u26')  * (1 - _sgn * 2)
            _sgn   = payload.read( 'u1')  # z_n dot^2, DF119
            zndd   = payload.read( 'u4')  * (1 - _sgn * 2)
            p3     = payload.read(   1 )  # P3, DF120
            _sgn   = payload.read( 'u1')  # gamma_n, DF121
            gmn    = payload.read('u10')  * (1 - _sgn * 2)
            p      = payload.read(   2 )  # P, DF122
            in3    = payload.read(   1 )  # I_n, DF123
            _sgn   = payload.read( 'u1')  # tau_n, DF124
            taun   = payload.read('u21')  * (1 - _sgn * 2)
            _sgn   = payload.read( 'u1')  # d_tau_n, DF125
            dtaun  = payload.read( 'u4')  * (1 - _sgn * 2)
            en     = payload.read( 'u5')  # E_n, DF126
            p4     = payload.read(   1 )  # P4, DF127
            ft     = payload.read( 'u4')  # F_t, DF128
            nt     = payload.read('u11')  # N_t, DF129
            m      = payload.read(   2 )  # M, DF130
            add    = payload.read(   1 )  # addition, DF131
            na     = payload.read('u11')  # N^A, DF132
            _sgn   = payload.read( 'u1')  # tau_c, DF133
            tauc   = payload.read('u31')  * (1 - _sgn * 2)
            n4     = payload.read( 'u5')  # N_4, DF134
            _sgn   = payload.read( 'u1')  # tau_GPS, DF135
            tgps   = payload.read('u21')  * (1 - _sgn * 2)
            in5    = payload.read(   1 )  # I_n, DF136
            payload.pos +=  7             # reserved
            string += f'R{svid:02d} f={fcn:02d} tk={tk[7:12].u:02d}:{tk[1:7].u:02d}:{tk[0:2].u*15:02d} tb={tb*15}min'
            if svh:
                string += self.msg_color.fg('red') + \
                    ' unhealthy' + self.msg_color.fg()
        elif satsys == 'E':  # Galileo ephemerides
            svid  = payload.read( 'u6')  # satellite id, DF252
            wn    = payload.read('u12')  # week number, DF289
            iodn  = payload.read('u10')  # IODnav, DF290
            sisa  = payload.read( 'u8')  # SIS Accracy, DF291
            idot  = payload.read('i14')  # IDOT, DF292
            toc   = payload.read('u14')  # t_oc, DF293
            af2   = payload.read( 'i6')  # a_f2, DF294
            af1   = payload.read('i21')  # a_f1, DF295
            af0   = payload.read('i31')  # a_f0, DF296
            crs   = payload.read('i16')  # C_rs, DF297
            dn    = payload.read('i16')  # delta n, DF298
            m0    = payload.read('i32')  # M_0, DF299
            cuc   = payload.read('i16')  # C_uc, DF300
            e     = payload.read('u32')  # e, DF301
            cus   = payload.read('i16')  # C_us, DF302
            a12   = payload.read('u32')  # sqrt_a, DF303
            toe   = payload.read('u14')  # t_oe, DF304
            cic   = payload.read('i16')  # C_ic, DF305
            omg0  = payload.read('i32')  # Omega_0, DF306
            cis   = payload.read('i16')  # C_is, DF307
            i0    = payload.read('i32')  # i_0, DF308
            crc   = payload.read('i16')  # C_rc, DF309
            omg   = payload.read('i32')  # omega, DF310
            omgd0 = payload.read('i24')  # Omega-dot0, DF311
            be5a  = payload.read('i10')  # BGD_E5aE1, DF312
            if   mtype == 'F/NAV':
                osh = payload.read(2)    # open signal health DF314
                osv = payload.read(1)    # open signal valid DF315
                payload.pos += 7         # reserved, DF001
            elif mtype == 'I/NAV':
                be5b = payload.read('i10')  # BGD_E5bE1 DF313
                e5h  = payload.read(   2 )  # E5b signal health, DF316
                e5v  = payload.read(   1 )  # E5b data validity, DF317
                e1h  = payload.read(   2 )  # E1b signal health, DF287
                e1v  = payload.read(   1 )  # E1b data validity, DF288
                payload.pos += 2            # reserved, DF001
            else:
                raise Exception(f'unknown Galileo nav message: {mtype}')
            string += f'E{svid:02d} WN={wn} IODnav={iodn}'
            if   mtype == 'F/NAV':
                if osh:
                    string += self.msg_color.fg('red') + \
                        f' unhealthy OS ({osh.int})' + self.msg_color.fg()
                if osv:
                    string += self.msg_color.fg('red') + \
                        ' invalid OS' + self.msg_color.fg()
            elif mtype == 'I/NAV':
                if e5h:
                    string += self.msg_color.fg('red') + \
                        f' unhealthy E5b ({e5h.int})' + self.msg_color.fg()
                if e5v:
                    string += self.msg_color.fg('red') + \
                        ' invalid E5b' + self.msg_color.fg()
                if e1h:
                    string += self.msg_color.fg('red') + \
                        f' unhealthy E1b ({e1h.int})' + self.msg_color.fg()
                if e1v:
                    string += self.msg_color.fg('red') + \
                        ' invalid E1b' + self.msg_color.fg()
            else:
                raise Exception(f'unknown Galileo nav message: {mtype}')
        elif satsys == 'J':  # QZSS ephemerides
            svid = payload.read( 'u4')  # satellite id, DF429
            toc  = payload.read('u16')  # t_oc, DF430
            af2  = payload.read(' i8')  # a_f2, DF431
            af1  = payload.read('i16')  # a_f1, DF432
            af0  = payload.read('i22')  # a_f0, DF433
            iode = payload.read(' u8')  # IODE, DF434
            crs  = payload.read('i16')  # C_rs, DF435
            dn0  = payload.read('i16')  # delta n_0, DF436
            m0   = payload.read('i32')  # M_0, DF437
            cuc  = payload.read('i16')  # C_uc, DF438
            e    = payload.read('u32')  # e, DF439
            cus  = payload.read('i16')  # C_uc, DF440
            a12  = payload.read('u32')  # sqrt_A, DF441
            toe  = payload.read('u16')  # t_oe, DF442
            cic  = payload.read('i16')  # C_ic, DF443
            omg0 = payload.read('i32')  # Omg_0, DF444
            cis  = payload.read('i16')  # C_is, DF445
            i0   = payload.read('i32')  # i_0, DF446
            crc  = payload.read('i16')  # C_rc, DF447
            omgn = payload.read('i32')  # omg_n, DF448
            omgd = payload.read('i24')  # Omg dot, DF449
            i0d  = payload.read('i14')  # i0 dot, DF450
            l2   = payload.read(   2 )  # L2 code, DF451
            wn   = payload.read('u10')  # week number, DF452
            ura  = payload.read(' u4')  # URA, DF453
            svh  = payload.read(' u6')  # SVH, DF454
            tgd  = payload.read(' i8')  # T_GD, DF455
            iodc = payload.read('u10')  # IODC, DF456
            fi   = payload.read(   1 )  # fit interval, DF457
            string += f'J{svid:02d} WN={wn} IODE={iode:{FMT_IODE}} IODC={iodc:{FMT_IODC}}'
            if svh:  # to be determined: L1 C/B operation
                string += self.msg_color.fg('red') + \
                    f' unhealthy ({svh:02x})' + self.msg_color.fg()
        elif satsys == 'C':  # BeiDou ephemerides
            svid = payload.read( 'u6')  # satellite id, DF488
            wn   = payload.read('u13')  # week number, DF489
            urai = payload.read(   4 )  # URA, DF490
            idot = payload.read('i14')  # IDOT, DF491
            aode = payload.read( 'u5')  # AODE, DF492
            toc  = payload.read('u17')  # t_oc, DF493
            a2   = payload.read('i11')  # a_2, DF494
            a1   = payload.read('i22')  # a_1, DF495
            a0   = payload.read('i24')  # a_0, DF496
            aodc = payload.read( 'u5')  # AODC, DF497
            crs  = payload.read('i18')  # C_rs, DF498
            dn   = payload.read('i16')  # delta n, DF499
            m0   = payload.read('i32')  # M_0, DF500
            cuc  = payload.read('i18')  # C_uc, DF501
            e    = payload.read('u32')  # e, DF502
            cus  = payload.read('i18')  # C_us, DF503
            a12  = payload.read('u32')  # sqrt_a, DF504
            toe  = payload.read('u17')  # t_oe, DF505
            cic  = payload.read('u18')  # C_ic, DF506
            omg0 = payload.read('i32')  # Omg_0, DF507
            cis  = payload.read('i18')  # C_is, DF508
            i0   = payload.read('i32')  # i_0, DF509
            crc  = payload.read('i18')  # C_rc, DF510
            omg  = payload.read('i32')  # omg, DF511
            omgd = payload.read('i24')  # Omg dot, DF512
            tgd1 = payload.read('i10')  # T_GD1, DF513
            tgd2 = payload.read('i10')  # T_GD2, DF514
            svh  = payload.read(   1 )  # SVH, DF515
            string +=f'C{svid:02d} WN={wn} AODE={aode}'
            if svh:
                string += self.msg_color.fg('red') + \
                    ' unhealthy' + self.msg_color.fg()
        elif satsys == 'I':  # NavIC ephemerides
            svid  = payload.read( 'u6')  # satellite id, DF516
            wn    = payload.read('u10')  # week number, DF517
            af0   = payload.read('i22')  # a_f0, DF518
            af1   = payload.read('i16')  # a_f1, DF519
            af2   = payload.read( 'i8')  # a_f2, DF520
            ura   = payload.read( 'u4')  # URA, DF521
            toc   = payload.read('u16')  # t_oc, DF522
            tgd   = payload.read( 'i8')  # t_GD, DF523
            dn    = payload.read('i22')  # delta n, DF524
            iodec = payload.read( 'u8')  # IODEC, DF525
            payload.pos += 10            # reserved, DF526
            hl5   = payload.read(   1 )  # L5_flag, DF527
            hs    = payload.read(   1 )  # S_flag, DF528
            cuc   = payload.read('i15')  # C_uc, DF529
            cus   = payload.read('i15')  # C_us, DF530
            cic   = payload.read('i15')  # C_ic, DF531
            cis   = payload.read('i15')  # C_is, DF532
            crc   = payload.read('i15')  # C_rc, DF533
            crs   = payload.read('i15')  # C_rs, DF534
            idot  = payload.read('i14')  # IDOT, DF535
            m0    = payload.read('i32')  # M_0, DF536
            toe   = payload.read('u16')  # t_oe, DF537
            e     = payload.read('u32')  # e, DF538
            a12   = payload.read('u32')  # sqrt_A, DF539
            omg0  = payload.read('i32')  # Omg0, DF540
            omg   = payload.read('i32')  # omg, DF541
            omgd  = payload.read('i22')  # Omg dot, DF542
            i0    = payload.read('i32')  # i0, DF543
            payload.pos += 2             # spare, DF544
            payload.pos += 2             # spare, DF545
            string += f'I{svid:02d} WN={wn} IODEC={iodec:{FMT_IODE}}'
            if hl5 or hs:
                string += self.msg_color.fg('red') + ' unhealthy'
                if hl5: string += ' L5'
                if hs : string += ' S'
                string += self.msg_color.fg()
        else:
            raise Exception(f'unknown satsys({satsys})')
        return payload.pos, string

# EOF

