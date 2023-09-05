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

FMT_IODC = '4d'    # format string for IODC

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
            svid   = payload[pos:pos+ 6].uint; pos +=  6  # satellite id, DF009
            wn     = payload[pos:pos+10].uint; pos += 10  # week number, DF076
            sva    = payload[pos:pos+ 4].uint; pos +=  4  # SV accuracy DF077
            gpsc   = payload[pos:pos+ 2]     ; pos +=  2  # GPS code L2, DF078
            idot   = payload[pos:pos+14].int ; pos += 14  # IDOT, DF079
            iode   = payload[pos:pos+ 8].uint; pos +=  8  # IODE, DF071
            toc    = payload[pos:pos+16].uint; pos += 16  # t_oc, DF081
            af2    = payload[pos:pos+ 8].int ; pos +=  8  # a_f2, DF082
            af1    = payload[pos:pos+16].int ; pos += 16  # a_f1, DF083
            af0    = payload[pos:pos+22].int ; pos += 22  # a_f0, DF084
            iodc   = payload[pos:pos+10].uint; pos += 10  # IODC, DF085
            crs    = payload[pos:pos+16].int ; pos += 16  # C_rs, DF086
            dn     = payload[pos:pos+16].int ; pos += 16  # d_n,  DF087
            m0     = payload[pos:pos+32].int ; pos += 32  # M_0,  DF088
            cuc    = payload[pos:pos+16].int ; pos += 16  # C_uc, DF089
            e      = payload[pos:pos+32].uint; pos += 32  # e,    DF090
            cus    = payload[pos:pos+16].int ; pos += 16  # C_us, DF091
            a12    = payload[pos:pos+32].uint; pos += 32  # a12,  DF092
            toe    = payload[pos:pos+16].uint; pos += 16  # t_oe, DF093
            cic    = payload[pos:pos+16].int ; pos += 16  # C_ic, DF094
            omg0   = payload[pos:pos+32].int ; pos += 32  # Omg0, DF095
            cis    = payload[pos:pos+16].int ; pos += 16  # C_is, DF096
            i0     = payload[pos:pos+32].int ; pos += 32  # i_0,  DF097
            crc    = payload[pos:pos+16].int ; pos += 16  # C_rc, DF098
            omg    = payload[pos:pos+32].int ; pos += 32  # omg,  DF099
            omgd   = payload[pos:pos+24].int ; pos += 24  # Omg-dot, DF100
            tgd    = payload[pos:pos+ 8].int ; pos +=  8  # t_GD, DF101
            health = payload[pos:pos+ 6].uint; pos +=  6  # SV health, DF102
            l2p    = payload[pos:pos+ 1]     ; pos +=  1  # P flag, DF103
            fitint = payload[pos:pos+ 1]     ; pos +=  1  # fit interval, DF137
            string += f'G{svid:02d} WN={wn}'
            if   gpsc == '0b01': string += ' L2P'
            elif gpsc == '0b10': string += ' L2C/A'
            elif gpsc == '0b11': string += ' L2C'
            else: raise Exception(f'undefined GPS code on L2: {gpsc}')
            string += f' IODE={iode}'
            string += f' IODC={iodc}'
            if health:
                string += ' health=' + self.msg_color.fg('red') + \
                    f'{health:02x}' + self.msg_color.fg()
            else:
                string += f' health={health:02x}'
        elif satsys == 'R':  # GLONASS ephemerides
            svid   = payload[pos:pos+ 6].uint; pos +=  6  # satellite id, DF038
            fcn    = payload[pos:pos+ 5].uint; pos +=  5  # freq ch, DF040
            health = payload[pos:pos+ 1].uint; pos +=  1  # almanac health DF104
            hai    = payload[pos:pos+ 1]     ; pos +=  1  # health avail, DF105
            p1     = payload[pos:pos+ 2]     ; pos +=  2  # P1, DF106
            tk     = payload[pos:pos+12]     ; pos += 12  # t_k, DF107
            bn     = payload[pos:pos+ 1]     ; pos +=  1  # B_n word MSB, DF108
            p2     = payload[pos:pos+ 1]     ; pos +=  1  # P2, DF109
            tb     = payload[pos:pos+ 7].uint; pos +=  7  # t_b, DF110
            xnd    = payload[pos:pos+24]     ; pos += 24  # x_n dot, DF111
            xn     = payload[pos:pos+27]     ; pos += 27  # x_n, DF112
            xndd   = payload[pos:pos+ 5]     ; pos +=  5  # x_n dot^2, DF113
            ynd    = payload[pos:pos+24]     ; pos += 24  # y_n dot, DF114
            yn     = payload[pos:pos+27]     ; pos += 27  # y_n, DF115
            yndd   = payload[pos:pos+ 5]     ; pos +=  5  # y_n dot^2, DF116
            znd    = payload[pos:pos+24]     ; pos += 24  # z_n dot, DF117
            zn     = payload[pos:pos+27]     ; pos += 27  # z_n, DF118
            zndd   = payload[pos:pos+ 5]     ; pos +=  5  # z_n dot^2, DF119
            p3     = payload[pos:pos+ 1]     ; pos +=  1  # P3, DF120
            gmn    = payload[pos:pos+11]     ; pos += 11  # gamma_n, DF121
            p      = payload[pos:pos+ 2]     ; pos +=  2  # P, DF122
            in3    = payload[pos:pos+ 1]     ; pos +=  1  # I_n, DF123
            taun   = payload[pos:pos+22]     ; pos += 22  # tau_n, DF124
            dtaun  = payload[pos:pos+ 5]     ; pos +=  5  # d_tau_n, DF125
            en     = payload[pos:pos+ 5].uint; pos +=  5  # E_n, DF126
            p4     = payload[pos:pos+ 1]     ; pos +=  1  # P4, DF127
            ft     = payload[pos:pos+ 4].uint; pos +=  4  # F_t, DF128
            nt     = payload[pos:pos+11].uint; pos += 11  # N_t, DF129
            m      = payload[pos:pos+ 2]     ; pos +=  2  # M, DF130
            add    = payload[pos:pos+ 1]     ; pos +=  1  # addition, DF131
            na     = payload[pos:pos+11].uint; pos += 11  # N^A, DF132
            tauc   = payload[pos:pos+32]     ; pos += 32  # tau_c, DF133
            n4     = payload[pos:pos+ 5].uint; pos +=  5  # N_4, DF134
            taug   = payload[pos:pos+22]     ; pos += 22  # tau_GPS, DF135
            in5    = payload[pos:pos+ 1]     ; pos +=  1  # I_n, DF136
            pos +=  7                                     # reserved
            string += f'R{svid:02d} freq={fcn:<2d}'
            if health:
                string += ' health=' + self.msg_color.fg('red') + \
                    f'{health:02x}' + self.msg_color.fg()
            else:
                string += f' health={health:02x}'
        elif satsys == 'E':  # Galileo ephemerides
            svid   = payload[pos:pos+ 6].uint; pos +=  6  # satellite id, DF252
            wn     = payload[pos:pos+12].uint; pos += 12  # week number, DF289
            iodnav = payload[pos:pos+10].uint; pos += 10  # IODnav, DF290
            sisa   = payload[pos:pos+ 8].uint; pos +=  8  # SIS Accracy, DF291
            idot   = payload[pos:pos+14].int ; pos += 14  # IDOT, DF292
            toc    = payload[pos:pos+14].uint; pos += 14  # t_oc, DF293
            af2    = payload[pos:pos+ 6].int ; pos +=  6  # a_f2, DF294
            af1    = payload[pos:pos+21].int ; pos += 21  # a_f1, DF295
            af0    = payload[pos:pos+31].int ; pos += 31  # a_f0, DF296
            crs    = payload[pos:pos+16].int ; pos += 16  # C_rs, DF297
            dn     = payload[pos:pos+16].int ; pos += 16  # delta n, DF298
            m0     = payload[pos:pos+32].int ; pos += 32  # M_0, DF299
            cuc    = payload[pos:pos+16].int ; pos += 16  # C_uc DF300
            e      = payload[pos:pos+32].uint; pos += 32  # e, DF301
            cus    = payload[pos:pos+16].int ; pos += 16  # C_us, DF302
            a12    = payload[pos:pos+32].uint; pos += 32  # sqrt_a, DF303
            toe    = payload[pos:pos+14].uint; pos += 14  # t_oe, DF304
            cic    = payload[pos:pos+16].int ; pos += 16  # C_ic, DF305
            omg0   = payload[pos:pos+32].int ; pos += 32  # Omega_0, DF306
            cis    = payload[pos:pos+16].int ; pos += 16  # C_is, DF307
            i0     = payload[pos:pos+32].int ; pos += 32  # i_0, DF308
            crc    = payload[pos:pos+16].int ; pos += 16  # C_rc, DF309
            omg    = payload[pos:pos+32].int ; pos += 32  # omega, DF310
            omgd0  = payload[pos:pos+24].int ; pos += 24  # Omega-dot0, DF311
            bdg_e5ae1 = payload[pos:pos+10].int; pos += 10 # BGD_E5aE1, DF312
            if   mtype == 'F/NAV':
                os_hs = payload[pos:pos+2]; pos += 2 # open signal health DF314
                os_vs = payload[pos:pos+1]; pos += 1 # open signal valid DF315
                pos += 7                             # reserved, DF001
            elif mtype == 'I/NAV':
                bgd_e5be1 = payload[pos:pos+10].int; pos += 10 # BGD_E5bE1 DF313
                e5b_hs = payload[pos:pos+2]; pos += 2 # E5b signal health, DF316
                e5b_vs = payload[pos:pos+1]; pos += 1 # E5b data validity, DF317
                e1b_hs = payload[pos:pos+2]; pos += 2 # E1b signal health, DF287
                e1b_vs = payload[pos:pos+1]; pos += 1 # E1b data validity, DF288
                pos += 2                              # reserved, DF001
            else:
                raise Exception(f'unknown Galileo nav message: {mtype}')
            string += f'E{svid:02d} WN={wn} IODnav={iodnav}'
            if   mtype == 'F/NAV':
                if os_hs:
                    string += ' OS_health=' + self.msg_color.fg('red') + \
                        f'{os_hs.int}' + self.msg_color.fg()
                else:
                    string += f' OS_health={os_hs.int}'
                if os_vs:
                    string += self.msg_color.fg('red') + '*' + \
                        self.msg_color.fg()
            elif mtype == 'I/NAV':
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
            else:
                raise Exception(f'unknown Galileo nav message: {mtype}')
        elif satsys == 'J':  # QZSS ephemerides
            svid   = payload[pos:pos+ 4].uint; pos +=  4  # satellite id, DF429
            toc    = payload[pos:pos+16].uint; pos += 16  # t_oc, DF430
            af2    = payload[pos:pos+ 8].int ; pos +=  8  # a_f2, DF431
            af1    = payload[pos:pos+16].int ; pos += 16  # a_f1, DF432
            af0    = payload[pos:pos+22].int ; pos += 22  # a_f0, DF433
            iode   = payload[pos:pos+ 8].uint; pos +=  8  # IODE, DF434
            crs    = payload[pos:pos+16].int ; pos += 16  # C_rs, DF435
            dn0    = payload[pos:pos+16].int ; pos += 16  # delta n_0, DF436
            m0     = payload[pos:pos+32].int ; pos += 32  # M_0, DF437
            cuc    = payload[pos:pos+16].int ; pos += 16  # C_uc, DF438
            e      = payload[pos:pos+32].uint; pos += 32  # e, DF439
            cus    = payload[pos:pos+16].int ; pos += 16  # C_uc, DF440
            a12    = payload[pos:pos+32].uint; pos += 32  # sqrt_A, DF441
            toe    = payload[pos:pos+16].uint; pos += 16  # t_oe, DF442
            cic    = payload[pos:pos+16].int ; pos += 16  # C_ic, DF443
            omg0   = payload[pos:pos+32].int ; pos += 32  # Omg_0, DF444
            cis    = payload[pos:pos+16].int ; pos += 16  # C_is, DF445
            i0     = payload[pos:pos+32].int ; pos += 32  # i_0, DF446
            crc    = payload[pos:pos+16].int ; pos += 16  # C_rc, DF447
            omgn   = payload[pos:pos+32].int ; pos += 32  # omg_n, DF448
            omgd   = payload[pos:pos+24].int ; pos += 24  # Omg dot, DF449
            i0d    = payload[pos:pos+14].int ; pos += 14  # i0 dot, DF450
            l2     = payload[pos:pos+ 2]     ; pos +=  2  # L2 code, DF451
            wn     = payload[pos:pos+10].uint; pos += 10  # week no, DF452
            ura    = payload[pos:pos+ 4].uint; pos +=  4  # URA, DF453
            health = payload[pos:pos+ 6].uint; pos +=  6  # SVH, DF454
            tgd    = payload[pos:pos+ 8].int ; pos +=  8  # T_GD, DF455
            iodc   = payload[pos:pos+10].uint; pos += 10  # IODC, DF456
            fi     = payload[pos:pos+ 1]     ; pos +=  1  # fit interval, DF457
            string += f'J{svid:02d} WN={wn}'
            if health:  # to be determined: L1 C/B operation
                string +=' health=' + self.msg_color.fg('red') + \
                    f'{health:02x}' + self.msg_color.fg()
            else:
                string += f' health={health:02x}'
            string += f' IODC={iodc:{FMT_IODC}}'
        elif satsys == 'C':  # BeiDou ephemerides
            svid   = payload[pos:pos+ 6].uint; pos +=  6  # satellite id, DF488
            wn     = payload[pos:pos+13].uint; pos += 13  # week no, DF489
            urai   = payload[pos:pos+ 4]     ; pos +=  4  # URA, DF490
            idot   = payload[pos:pos+14].int ; pos += 14  # IDOT, DF491
            aode   = payload[pos:pos+ 5].uint; pos +=  5  # AODE, DF492
            toc    = payload[pos:pos+17].uint; pos += 17  # t_oc, DF493
            a2     = payload[pos:pos+11].int ; pos += 11  # a_2, DF494
            a1     = payload[pos:pos+22].int ; pos += 22  # a_1, DF495
            a0     = payload[pos:pos+24].int ; pos += 24  # a_0, DF496
            aodc   = payload[pos:pos+ 5].uint; pos +=  5  # AODC, DF497
            crs    = payload[pos:pos+18].int ; pos += 18  # C_rs, DF498
            dn     = payload[pos:pos+16].int ; pos += 16  # delta n, DF499
            m0     = payload[pos:pos+32].int ; pos += 32  # M_0, DF500
            cuc    = payload[pos:pos+18].int ; pos += 18  # C_uc, DF501
            e      = payload[pos:pos+32].uint; pos += 32  # e, DF502
            cus    = payload[pos:pos+18].int ; pos += 18  # C_us, DF503
            a12    = payload[pos:pos+32].uint; pos += 32  # sqrt_a, DF504
            toe    = payload[pos:pos+17].uint; pos += 17  # t_oe, DF505
            cic    = payload[pos:pos+18].uint; pos += 18  # C_ic, DF506
            omg0   = payload[pos:pos+32].int ; pos += 32  # Omg_0, DF507
            cis    = payload[pos:pos+18].int ; pos += 18  # C_is, DF508
            i0     = payload[pos:pos+32].int ; pos += 32  # i_0, DF509
            crc    = payload[pos:pos+18].int ; pos += 18  # C_rc, DF510
            omg    = payload[pos:pos+32].int ; pos += 32  # omg, DF511
            omgd   = payload[pos:pos+24].int ; pos += 24  # Omg dot, DF512
            tgd1   = payload[pos:pos+10].int ; pos += 10  # T_GD1, DF513
            tgd2   = payload[pos:pos+10].int ; pos += 10  # T_GD2, DF514
            health = payload[pos:pos+ 1]     ; pos +=  1  # SVH, DF515
            string +=f'C{svid:02d} WN={wn}'
            if health:
                string += ' health=' + self.msg_color.fg('red') + \
                    f'{health:02x}' + self.msg_color.fg()
            else:
                string += f' health={health.uint:02x}'
        elif satsys == 'I':  # NavIC ephemerides
            svid   = payload[pos:pos+ 6].uint; pos +=  6  # satellite id, DF516
            wn     = payload[pos:pos+10].uint; pos += 10  # week no, DF517
            af0    = payload[pos:pos+22].int ; pos += 22  # a_f0, DF518
            af1    = payload[pos:pos+16].int ; pos += 16  # a_f1, DF519
            af2    = payload[pos:pos+ 8].int ; pos +=  8  # a_f2, DF520
            ura    = payload[pos:pos+ 4].uint; pos +=  4  # URA, DF521
            toc    = payload[pos:pos+16].uint; pos += 16  # t_oc, DF522
            tgd    = payload[pos:pos+ 8].int ; pos +=  8  # t_GD, DF523
            dn     = payload[pos:pos+22].int ; pos += 22  # delta n, DF524
            iodec  = payload[pos:pos+ 8].uint; pos +=  8  # IODEC, DF525
            pos += 10                                     # reserved, DF526
            l5     = payload[pos:pos+ 1]     ; pos +=  1  # L5_flag, DF527
            s      = payload[pos:pos+ 1]     ; pos +=  1  # S_flag, DF528
            cuc    = payload[pos:pos+15].int ; pos += 15  # C_uc, DF529
            cus    = payload[pos:pos+15].int ; pos += 15  # C_us, DF530
            cic    = payload[pos:pos+15].int ; pos += 15  # C_ic, DF531
            cis    = payload[pos:pos+15].int ; pos += 15  # C_is, DF532
            crc    = payload[pos:pos+15].int ; pos += 15  # C_rc, DF533
            crs    = payload[pos:pos+15].int ; pos += 15  # C_rs, DF534
            idot   = payload[pos:pos+14].int ; pos += 14  # IDOT, DF535
            m0     = payload[pos:pos+32].int ; pos += 32  # M_0, DF536
            toe    = payload[pos:pos+16].uint; pos += 16  # t_oe, DF537
            e      = payload[pos:pos+32].uint; pos += 32  # e, DF538
            a12    = payload[pos:pos+32].uint; pos += 32  # sqrt_A, DF539
            omg0   = payload[pos:pos+32].int ; pos += 32  # Omg0, DF540
            omg    = payload[pos:pos+32].int ; pos += 32  # omg, DF541
            omgd   = payload[pos:pos+22].int ; pos += 22  # Omg dot, DF542
            i0     = payload[pos:pos+32].int ; pos += 32  # i0, DF543
            pos +=  2                                     # spare, DF544
            pos +=  2                                     # spare, DF545
            string += f'I{svid:02d} WN={wn} IODEC={iodec}'
            if l5 or s:
                string += ' health=' + self.msg_color.fg('red') + \
                    'L5 ' if l5 else '' + 'S' if s else '' + self.msg_color.fg()
        else:
            raise Exception(f'satsys={satsys}')
        return pos, string

# EOF

