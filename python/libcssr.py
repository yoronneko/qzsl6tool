#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# libcssr.py: library for compact SSR message processing
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2022 Satoshi Takahashi
#
# Released under BSD 2-clause license.

import sys
import bitstring

INVALID = 0  # invalid value indication for CSSR message show

class Cssr:
    """Base class of compact space state representation (CSSR)"""
    stat = False    # statistics output
    stat_nsat = 0   # stat: number of satellites
    stat_nsig = 0   # stat: number of signals
    stat_bsat = 0   # stat: bit number of satellites
    stat_bsig = 0   # stat: bit number of signals
    stat_both = 0   # stat: bit number of other information
    stat_bnull = 0  # stat: bit number of null

    def show_cssr_stat(self):
        msg = f'stat n_sat {self.stat_nsat} n_sig {self.stat_nsig} ' + \
              f'bit_sat {self.stat_bsat} bit_sig {self.stat_bsig} ' + \
              f'bit_other {self.stat_both} bit_null {self.stat_bnull} ' + \
              f'bit_total {self.stat_bsat + self.stat_bsig + self.stat_both + self.stat_bnull}'
        print(msg, file=self.fp_trace)

    def gnssid2satsys(self, gnssid):
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

    def sigmask2signame(self, satsys, sigmask):
        signame = f'satsys={satsys} sigmask={sigmask}'
        if satsys == 'G':
            signame = [
                "L1 C/A",
                "L1 P",
                "L1 Z-tracking",
                "L1 L1C(D)",
                "L1 L1C(P)",
                "L1 L1C(D+P)",
                "L2 L2C(M)",
                "L2 L2C(L)",
                "L2 L2C(M+L)",
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
                "E1 B I/NAV OS/CS/SoL",
                "E1 C no data",
                "E1 B+C",
                "E5a I F/NAV OS",
                "E5a Q no data",
                "E5a I+Q",
                "E5b I I/NAV OS/CS/SoL",
                "E5b Q no data",
                "E5b I+Q",
                "E5 I",
                "E5 Q",
                "E5 I+Q",
                "Service specific 1",
                "Service specific 2",
                "Service specific 3",
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

    def decode_cssr_st1(self):
        l6msg = self.l6msg
        l6msglen = len(l6msg)
        if l6msglen < 49:
            return False
        pos = self.pos
        ngnss = l6msg[pos:pos + 4].uint
        pos += 4  # numer of GNSS
        if len(l6msg) < 49 + 61 * ngnss:
            return False
        satsys = [None for i in range(ngnss)]
        nsatmask = [None for i in range(ngnss)]
        nsigmask = [None for i in range(ngnss)]
        cellmask = [None for i in range(ngnss)]
        gsys = {}
        gsig = {}
        for ignss in range(ngnss):
            ugnssid = l6msg[pos:pos + 4].uint
            pos += 4
            bsatmask = l6msg[pos:pos + 40]
            pos += 40
            bsigmask = l6msg[pos:pos + 16]
            pos += 16
            cmavail = l6msg[pos:pos + 1]
            pos += 1
            t_satsys = self.gnssid2satsys(ugnssid)
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
                    t_gsig.append(self.sigmask2signame(t_satsys, i))
            ncell = t_satmask * t_sigmask
            if cmavail:
                bcellmask = l6msg[pos:pos + ncell]
                pos += ncell
            else:
                bcellmask = bitstring.BitArray('0b1') * ncell
            cellmask[ignss] = bcellmask
            satsys[ignss] = t_satsys
            nsatmask[ignss] = t_satmask
            nsigmask[ignss] = t_sigmask
            gsys[t_satsys] = t_gsys
            gsig[t_satsys] = t_gsig
        self.satsys = satsys      # satellite system
        self.nsatmask = nsatmask  # number of satellite mask
        self.nsigmask = nsigmask  # number of signal mask
        self.cellmask = cellmask  # cell mask
        self.gsys = gsys          # dict of sat   name from system name
        self.gsig = gsig          # dict of sigal name from system name
        self.stat_nsat = 0
        self.stat_nsig = 0
        msg_trace1 = ''
        for i, satsys in enumerate(self.satsys):
            pos_mask = 0  # mask position
            for j, gsys in enumerate(self.gsys[satsys]):
                self.stat_nsat += 1
                msg_trace1 += 'ST1 ' + gsys
                for gsig in self.gsig[satsys]:
                    mask = self.cellmask[i][pos_mask]
                    pos_mask += 1
                    if not mask:
                        continue
                    msg_trace1 += ' ' + gsig
                    self.stat_nsig += 1
                msg_trace1 += '\n'
        self.rtcm = l6msg[:pos].tobytes()
        self.l6msg = l6msg[pos:]  # removal of ST1 message
        self.trace(1, msg_trace1)
        if self.stat:
            self.show_cssr_stat()
        self.stat_bsat = 0
        self.stat_bsig = 0
        self.stat_both = pos
        self.stat_bnull = 0
        return True

    def decode_cssr_st2(self):
        l6msg = self.l6msg
        l6msglen = len(l6msg)
        pos = self.pos
        stat_pos = pos
        msg_trace1 = ''
        for satsys in self.satsys:
            w_iode = 10 if satsys == 'E' else 8  # IODE bit width
            for gsys in self.gsys[satsys]:
                if l6msglen < pos + w_iode + 15 + 13 + 13:
                    return False
                iode = l6msg[pos:pos + w_iode].uint
                pos += w_iode
                i_radial = l6msg[pos:pos + 15].int
                d_radial = i_radial * 0.0016 if i_radial != -16384 else INVALID
                pos += 15
                i_along = l6msg[pos:pos + 13].int
                d_along = i_radial * 0.0064 if i_along != -16384 else INVALID
                pos += 13
                i_cross = l6msg[pos:pos + 13].int
                d_cross = i_radial * 0.0064 if i_cross != -16384 else INVALID
                pos += 13
                msg_trace1 += f'ST2 {gsys} IODE={iode:4d}' + \
                              f' d_radial={d_radial:4.1f}m' + \
                              f' d_along={d_along:4.1f}m' + \
                              f' d_cross={d_cross:4.1f}m\n'
        self.rtcm = l6msg[:pos].tobytes()
        self.l6msg = l6msg[pos:]  # removal of ST2 message
        self.trace(1, msg_trace1)
        self.stat_both += stat_pos
        self.stat_bsat += pos - stat_pos
        return True

    def decode_cssr_st3(self):
        l6msg = self.l6msg
        l6msglen = len(l6msg)
        pos = self.pos
        stat_pos = pos
        msg_trace1 = ''
        for i, satsys in enumerate(self.satsys):
            for gsys in self.gsys[satsys]:
                if l6msglen < pos + 15:
                    return False
                ic0 = l6msg[pos:pos + 15].int
                pos += 15
                c0 = ic0 * 0.0016 if ic0 != -16384 else INVALID
                msg_trace1 += f"ST3 {gsys} d_clock={c0:4.1f}m\n"
        self.rtcm = l6msg[:pos].tobytes()
        self.l6msg = l6msg[pos:]  # rmoval of ST3 message
        self.trace(1, msg_trace1)
        self.stat_both += stat_pos
        self.stat_bsat += pos - stat_pos
        return True

    def decode_cssr_st4(self):
        l6msg = self.l6msg
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
        if len(l6msg) < 37 + 11 * nsigsat:
            return False
        pos = self.pos  # mask position
        stat_pos = pos
        msg_trace1 = ''
        for i, satsys in enumerate(self.satsys):
            pos_mask = 0  # mask position
            for j, gsys in enumerate(self.gsys[satsys]):
                for k, gsig in enumerate(self.gsig[satsys]):
                    mask = self.cellmask[i][pos_mask]
                    pos_mask += 1
                    if not mask:
                        continue
                    cb = l6msg[pos:pos + 11].int
                    pos += 11
                    code_bias = cb * 0.02 if cb != -1024 else INVALID
                    msg_trace1 += f"ST4 {gsys} {gsig:13s} " +  \
                                  f"code_bias={code_bias:4.1f}m\n"
        self.rtcm = l6msg[:pos].tobytes()
        self.l6msg = l6msg[pos:]  # removal of ST4 message
        self.trace(1, msg_trace1)
        self.stat_both += stat_pos
        self.stat_bsig += pos - stat_pos
        return True

    def decode_cssr_st5(self):
        l6msg = self.l6msg
        l6msglen = len(l6msg)
        pos = self.pos
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
                    if l6msglen < pos + 15 + 2:
                        return False
                    pb = l6msg[pos:pos + 15].int
                    pos += 15
                    di = l6msg[pos:pos + 2].uint
                    pos += 2
                    phase_bias = pb * 0.001 if pb != -16384 else INVALID
                    msg_trace1 += f'ST5 {gsys} {gsig:13s}' + \
                                  f' phase_bias={phase_bias:4.1f}m' + \
                                  f' discont_indicator={di}\n'
        self.rtcm = l6msg[:pos].tobytes()
        self.l6msg = l6msg[pos:]  # removal of ST5 message
        self.trace(1, msg_trace1)
        self.stat_both += stat_pos
        self.stat_bsig += pos - stat_pos
        return True

    def decode_cssr_st6(self):
        l6msg = self.l6msg
        l6msglen = len(l6msg)
        if l6msglen < 45:
            return False
        pos = self.pos
        stat_pos = pos
        f_cb = l6msg[pos:pos + 1].uint  # code bias existing flag
        pos += 1
        f_pb = l6msg[pos:pos + 1].uint  # phase bias existing flag
        pos += 1
        f_nb = l6msg[pos:pos + 1].uint  # network bias existing flag
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
            cnid = l6msg[pos:pos + 5].uint  # compact network ID
            pos += 5
            msg_trace1 += f"ST6 NID={cnid}\n"
            for satsys in self.satsys:
                ngsys = len(self.gsys[satsys])
                if l6msglen < pos + ngsys:
                    return False
                svmask[satsys] = l6msg[pos:pos + ngsys]
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
                        if l6msglen < pos + 11:
                            return False
                        cb = l6msg[pos:pos + 11].int
                        code_bias = cb * 0.02 if cb != -1024 else INVALID
                        pos += 11  # code bias
                        msg_trace1 += f" code_bias={code_bias:4.1f}m"
                    if f_pb:
                        if l6msglen < pos + 15 + 2:
                            return False
                        pb = l6msg[pos:pos + 15].int
                        phase_bias = pb * 0.001 if pb != -16384 else INVALID
                        pos += 15
                        di = l6msg[pos:pos + 2].uint
                        pos += 2
                        msg_trace1 += f" phase_bias={phase_bias:6.3f}m" +  \
                                      f" discont_indi={di}"
                    msg_trace1 += '\n'
        self.rtcm = l6msg[:pos].tobytes()
        self.l6msg = l6msg[pos:]  # removal of ST6 message
        self.trace(1, msg_trace1)
        self.stat_both += stat_pos + 3
        self.stat_bsig += pos - stat_pos - 3
        return True

    def decode_cssr_st7(self):
        l6msg = self.l6msg
        l6msglen = len(l6msg)
        if l6msglen < 37:
            return False
        pos = self.pos
        stat_pos = pos
        msg_trace1 = ''
        for satsys in self.satsys:
            for gsys in self.gsys[satsys]:
                if l6msglen < pos + 6:
                    return False
                ura = l6msg[pos:pos + 6].uint
                pos += 6
                msg_trace1 += f"ST7 {gsys} URA {ura}\n"
        self.rtcm = l6msg[:pos].tobytes()
        self.l6msg = l6msg[pos:]  # removal of ST7 message
        self.trace(1, msg_trace1)
        self.stat_both += stat_pos
        self.stat_bsat += pos - stat_pos
        return True

    def decode_cssr_st8(self):
        l6msg = self.l6msg
        l6msglen = len(l6msg)
        if l6msglen < 44:
            return False
        pos = self.pos
        stat_pos = pos
        stec_type = l6msg[pos:pos + 2].uint  # STEC correction type
        pos += 2
        cnid = l6msg[pos:pos + 5].uint  # compact network ID
        pos += 5
        svmask = {}
        for satsys in self.satsys:
            ngsys = len(self.gsys[satsys])
            if l6msglen < pos + ngsys:
                return False
            svmask[satsys] = l6msg[pos:pos + ngsys]
            pos += ngsys
        msg_trace1 = ''
        for satsys in self.satsys:
            for i, gsys in enumerate(self.gsys[satsys]):
                if not svmask[satsys][i]:
                    continue
                if l6msglen < pos + 6 + 14:
                    return False
                qi = l6msg[pos:pos + 6].uint  # quality indicator
                pos += 6
                ic00 = l6msg[pos:pos + 14].int
                c00 = ic00 * 0.05 if ic00 != -8192 else INVALID
                msg_trace1 += f"ST8 {gsys} c00={c00:5.2f}TECU"
                pos += 14
                if 1 <= stec_type:
                    if l6msglen < pos + 12 + 12:
                        return False
                    ic01 = l6msg[pos:pos + 12].int
                    c01 = ic01 * 0.02 if ic01 != -2048 else INVALID
                    pos += 12
                    ic10 = l6msg[pos:pos + 12].int
                    c10 = ic10 * 0.02 if ic10 != -2048 else INVALID
                    pos += 12
                    msg_trace1 += f" c01={c01:5.2f}TECU/deg c10={c10:5.2f}TECU/deg"
                if 2 <= stec_type:
                    if l6msglen < pos + 10:
                        return False
                    ic11 = l6msg[pos:pos + 10].int
                    c11 = ic11 * 0.02 if ic11 != -512 else INVALID
                    pos += 10
                    msg_trace1 += f" c11={c11:5.2f}TECU/deg^2"
                if 3 <= stec_type:
                    if l6msglen < pos + 8 + 8:
                        return False
                    ic02 = l6msg[pos:pos + 8].int
                    c02 = ic02 * 0.005 if ic02 != -128 else INVALID
                    pos += 8
                    ic20 = l6msg[pos:pos + 8].int
                    c20 = ic20 * 0.005 if ic20 != -128 else INVALID
                    pos += 8
                    msg_trace1 += f" c02={c02:5.2f}TECU/deg^2 c20={c20:5.2f}TECU/deg^2"
                msg_trace1 += '\n'
        self.rtcm = l6msg[:pos].tobytes()
        self.l6msg = l6msg[pos:]  # removal of ST8 message
        self.trace(1, msg_trace1)
        self.stat_both += stat_pos + 7
        self.stat_bsat += pos - stat_pos - 7
        return True

    def decode_cssr_st9(self):
        l6msg = self.l6msg
        l6msglen = len(l6msg)
        if l6msglen < 45:
            return False
        pos = self.pos
        tctype = l6msg[pos:pos + 2].uint  # tropospheric correction type
        pos += 2
        crange = l6msg[pos:pos + 1].uint  # tropospheric correction range
        bw = 16 if crange else 7
        pos += 1
        cnid = l6msg[pos:pos + 5].uint  # compact network ID
        pos += 5
        svmask = {}
        for satsys in self.satsys:
            ngsys = len(self.gsys[satsys])
            if l6msglen < pos + ngsys:
                return False
            svmask[satsys] = l6msg[pos:pos + ngsys]
            pos += ngsys
        if l6msglen < pos + 6 + 6:
            return False
        tqi = l6msg[pos:pos + 6].uint  # tropospheric quality indicator
        pos += 6
        ngrid = l6msg[pos:pos + 6].uint  # number of grids
        pos += 6
        msg_trace1 = f"ST9 Trop correct_type={tctype}" + \
                     f" NID={cnid} quality={tqi} ngrid={ngrid}\n"
        for i in range(ngrid):
            if l6msglen < pos + 9 + 8:
                return False
            ivd_h = l6msg[pos:pos + 9].int  # hydrostatic vertical delay
            vd_h = ivd_h * 0.004 if ivd_h != -256 else INVALID
            pos += 9
            ivd_w = l6msg[pos:pos + 8].int  # wet vertical delay
            vd_w = ivd_w * 0.004 if ivd_w != -128 else INVALID
            pos += 8
            msg_trace1 += \
                f'ST9 Trop     grid {i+1:2d}/{ngrid:2d}' + \
                f' dry-delay={vd_h:6.3f}m wet-delay={vd_w:6.3f}m\n'
            for satsys in self.satsys:
                for j, gsys in enumerate(self.gsys[satsys]):
                    if not svmask[satsys][j]:
                        continue
                    if l6msglen < pos + bw:
                        return False
                    res = l6msg[pos:pos + bw].int
                    residual = res * 0.04
                    if (crange == 1 and res == -32767) or \
                       (crange == 0 and res == -64):
                        residual = INVALID
                    pos += bw
                    msg_trace1 += \
                        f'ST9 STEC {gsys} grid {i+1:2d}/{ngrid:2d}' + \
                        f' residual={residual:5.2f}TECU ({bw}bit)\n'
        self.trace(1, msg_trace1)
        self.rtcm = l6msg[:pos].tobytes()
        self.l6msg = l6msg[pos:]  # removal of ST9 message
        self.stat_both += pos
        return True

    def decode_cssr_st10(self):  # not implemented
        self.trace(1, f"ST10 --- not implemented")
        self.l6msg = bitstring.BitArray()  # removal of ST10 message
        return False

    def decode_cssr_st11(self):
        l6msg = self.l6msg
        l6msglen = len(l6msg)
        if l6msglen < 40:
            return False
        pos = self.pos
        stat_pos = pos
        f_o = l6msg[pos:pos + 1].uint  # orbit existing flag
        pos += 1
        f_c = l6msg[pos:pos + 1].uint  # clock existing flag
        pos += 1
        f_n = l6msg[pos:pos + 1].uint  # network correction
        pos += 1
        msg_trace1 = f"ST11 Orb={'on' if f_o else 'off'} " + \
                     f"Clk={'on' if f_c else 'off'} " + \
                     f"Net={'on' if f_n else 'off'}\n"
        if f_n:
            if l6msglen < pos + 5:
                return False
            cnid = l6msg[pos:pos + 5].uint  # compact network ID
            pos += 5
            msg_trace1 += f"ST11 NID={cnid}\n"
            svmask = {}
            for satsys in self.satsys:
                ngsys = len(self.gsys[satsys])
                if l6msglen < pos + ngsys:
                    return False
                svmask[satsys] = l6msg[pos:pos + ngsys]
                pos += ngsys
            for satsys in self.satsys:
                for i, gsys in enumerate(self.gsys[satsys]):
                    if not svmask[satsys][i]:
                        continue
                    msg_trace1 += f"ST11 {gsys}"
                    if f_o:
                        w_iode = 10 if satsys == 'E' else 8  # IODE width
                        if l6msglen < pos + w_iode + 15 + 13 + 13:
                            return False
                        iode = l6msg[pos:pos + w_iode].uint
                        pos += w_iode
                        id_radial = l6msg[pos:pos + 15].int
                        d_radial = id_radial * 0.0016 if id_radial != -16384 else INVALID
                        pos += 15
                        id_along = l6msg[pos:pos + 13].int
                        d_along = id_along * 0.0064 if id_along != -4096 else INVALID
                        pos += 13
                        id_cross = l6msg[pos:pos + 13].int
                        d_cross = id_cross * 0.0064 if id_cross != -4096 else INVALID
                        pos += 13
                        msg_trace1 += \
                            f" IODE={iode:4d}" +\
                            f" d_radial={d_radial:5.1f}m" + \
                            f" d_along={d_along:5.1f}m" + \
                            f" d_cross={d_cross:5.1f}m"
                    if f_c:
                        if l6msglen < pos + 15:
                            return False
                        ic0 = l6msg[pos:pos + 15].int
                        c0 = ic0 * 0.0016 if ic0 != -16384 else INVALID
                        pos += 15
                        msg_trace1 += f" c0={c0:5.1f}m"
                    msg_trace1 += "\n"
        self.rtcm = l6msg[:pos].tobytes()
        self.l6msg = l6msg[pos:]  # removal of ST11 message
        self.trace(1, msg_trace1)
        self.stat_both += stat_pos + 3
        self.stat_bsat += pos - stat_pos - 3
        if f_n:  # correct bit number because because we count up bsat as NID
            self.stat_both += 5
            self.stat_bsat -= 5
        return True

    def decode_cssr_st12(self):
        l6msg = self.l6msg
        l6msglen = len(l6msg)
        if l6msglen < 52:
            return False
        pos = self.pos
        tropo = l6msg[pos:pos + 2]  # Tropospheric correction avail
        pos += 2
        stec = l6msg[pos:pos + 2]  # STEC correction avail
        pos += 2
        cnid = l6msg[pos:pos + 5].uint  # compact network ID
        pos += 5
        ngrid = l6msg[pos:pos + 6].uint  # number of grids
        pos += 6
        msg_trace1 = \
            f"ST12 tropo={tropo} stec={stec} NID={cnid} ngrid={ngrid}\n" + \
            f"ST12 Trop"
        if tropo[0]:
            # 0 <= ttype (forward reference)
            if l6msglen < pos + 6 + 2 + 9:
                return False
            tqi = l6msg[pos:pos + 6].uint  # tropo quality indicator
            pos += 6
            ttype = l6msg[pos:pos + 2].uint  # tropo correction type
            pos += 2
            it00 = l6msg[pos:pos + 9].int  # tropo poly coeff
            t00 = it00 * 0.004 if it00 != -256 else INVALID
            pos += 9
            msg_trace1 += f" quality={tqi} correct_type(0-2)={ttype}" + \
                          f" t00={t00:6.2f}m"
            if 1 <= ttype:
                if l6msglen < pos + 7 + 7:
                    return False
                it01 = l6msg[pos:pos + 7].int
                t01 = it01 * 0.002 if it01 != -64 else INVALID
                pos += 7
                it10 = l6msg[pos:pos + 7].int
                t10 = it10 * 0.002 if it10 != -64 else INVALID
                pos += 7
                msg_trace1 += f" t01={t01:5.2f}m/deg t10={t10:5.2f}m/deg"
            if 2 <= ttype:
                if l6msglen < pos + 7:
                    return False
                it11 = l6msg[pos:pos + 7].int
                t11 = it11 * 0.001 if it11 != -64 else INVALID
                pos += 7
                msg_trace1 += f" t11={t11:5.2f}m/deg^2"
            msg_trace1 += '\n'
        if tropo[1]:
            if l6msglen < pos + 1 + 4:
                return False
            trs = l6msg[pos:pos + 1].uint  # tropo residual size
            pos += 1
            bw = 8 if trs else 6
            itro = l6msg[pos:pos + 4].uint  # tropo residual offset
            pos += 4
            tro = itro * 0.02
            msg_trace1 += f"ST12 Trop offset={tro:5.2f}m\n"
            if l6msglen < pos + bw * ngrid:
                return False
            for i in range(ngrid):
                itr = l6msg[pos:pos + bw].int  # troposphere residual
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
                if l6msglen < pos + ngsys:
                    return False
                svmask[satsys] = l6msg[pos:pos + ngsys]
                pos += ngsys
            for satsys in self.satsys:
                for i, gsys in enumerate(self.gsys[satsys]):
                    if not svmask[satsys][i]:
                        continue
                    if l6msglen < pos + 6 + 2 + 14:
                        return False
                    sqi = l6msg[pos:pos + 6].uint  # quality indicator
                    pos += 6
                    sct = l6msg[pos:pos + 2].uint  # correction type
                    pos += 2
                    ic00 = l6msg[pos:pos + 14].int
                    c00 = ic00 * 0.05 if ic00 != -8192 else INVALID
                    pos += 14
                    msg_trace1 += \
                        f"ST12 STEC {gsys} quality={sqi:02x} type={sct}" + \
                        f" c00={c00:.1f}TECU"
                    if 1 <= sct:
                        if l6msglen < pos + 12 + 12:
                            return False
                        ic01 = l6msg[pos:pos + 12].int
                        c01 = ic01 * 0.02 if ic01 != -2048 else INVALID
                        pos += 12
                        ic10 = l6msg[pos:pos + 12].int
                        c10 = ic10 * 0.02 if ic10 != -2048 else INVALID
                        pos += 12
                        msg_trace1 += f" c01={c01:.1f}TECU/deg c10={c10:.1f}TECU/deg"
                    if 2 <= sct:
                        if l6msglen < pos + 10:
                            return False
                        ic11 = l6msg[pos:pos + 10].int
                        c11 = ic11 * 0.02 if ic11 != -512 else INVALID
                        pos += 10
                        msg_trace1 += f" c11={c11:.1f}TECU/deg^2"
                    if 3 <= sct:
                        if l6msglen < pos + 8 + 8:
                            return False
                        ic02 = l6msg[pos:pos + 8].int
                        c02 = ic02 * 0.005 if ic02 != -128 else INVALID
                        pos += 8
                        ic20 = l6msg[pos:pos + 8].int
                        c20 = ic20 * 0.005 if ic20 != -128 else INVALID
                        pos += 8
                        msg_trace1 += f" c02={c02:.1f}TECU/deg^2 c20={c20:.1f}TECU/deg^2"
                    msg_trace1 += '\n'
                    if l6msglen < pos + 2:
                        return False
                    srs = l6msg[pos:pos + 2].uint  # STEC residual size
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
                        if l6msglen < pos + bw:
                            return False
                        isr = l6msg[pos:pos + bw].int
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
        self.rtcm = l6msg[:pos].tobytes()
        self.l6msg = l6msg[pos:]  # removal of ST12 message
        self.trace(1, msg_trace1)
        self.stat_both += stat_pos
        self.stat_bsat += pos - stat_pos
        return True

# EOF
