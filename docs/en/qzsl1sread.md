# qzsl1sread.py

This program reads QZSS L1S format data and SBAS (satellite based augmentation system) L1C/A format data from standard input or a file, and outputs its contents to standard output. Both share the same 250-bit message structure (8-bit preamble, 6-bit message type, 212-bit data field, and 24-bit CRC), so a single program handles them.

The message types (MT) decoded by this program are:

| MT | Contents | Signal |
|:--:|:--|:--:|
| 0 | Test mode | L1S / SBAS |
| 1 | SBAS PRN mask | SBAS |
| 2-5 | Fast corrections 1-4 | SBAS |
| 6 | Integrity information | SBAS |
| 7 | Fast correction degradation factor | SBAS |
| 9 | GEO ranging function parameters | SBAS |
| 10 | Degradation factors | SBAS |
| 12 | SBAS network time/UTC offset parameters | SBAS |
| 17 | GEO satellite almanacs | SBAS |
| 18 | Ionospheric grid point (IGP) masks | SBAS |
| 20 | SBAS L1 authentication message | SBAS |
| 21 | SBAS over the air rekeying (OTAR) | SBAS |
| 24 | Mixed fast/long-term satellite corrections | SBAS |
| 25 | Long-term satellite error corrections | SBAS |
| 26 | Ionospheric delay corrections | SBAS |
| 28 | Clock-ephemeris covariance matrix | SBAS |
| 43 | DCR (disaster and crisis management report) | L1S |
| 44 | DCX (DC report extended) | L1S |
| 47 | Monitoring station information | L1S |
| 48 | PRN mask | L1S |
| 49 | Data issue number | L1S |
| 50 | DGPS correction | L1S |
| 51 | Satellite health | L1S |
| 63 | Null message | L1S / SBAS |

MT20 and MT21 follow the draft ICAO SARPs, which are subject to change.

The ``--help`` option displays the options it accepts.

```bash
$ qzsl1sread.py --help
usage: qzsl1sread.py [-h] [-c] [-t TRACE] [--jp] [file ...]

Quasi-zenith satellite (QZS) L1S message read, QZS L6 Tool ver.x.x.x

positional arguments:
  file                  L1S file(s) obtained from the QZS archive, https://sys.qzss.go.jp/dod/archives/slas.html

options:
  -h, --help            show this help message and exit
  -c, --color           apply ANSI color escape sequences even for non-terminal.
  -t TRACE, --trace TRACE
                        show display verbosely: 1=subtype detail, 2=subtype and bit image.
  --jp                  show DCR (disaster and crisis management report) in Japanese.
```

## Input format

When a filename is given, the input format is the same as that of the [SLAS Archive](https://sys.qzss.go.jp/dod/en/archives/slas.html) on the QZSS official page: 1 byte (8 bits) of PRN (pseudo random noise) number, followed by 36-byte records each consisting of the GPS week number (12 bits), the GPS time of week (20 bits), an L1S message (250 bits), and padding (6 bits).

If no filename is given, it reads from standard input. In this case, the input is a sequence of 33-byte records each consisting of the PRN number (8 bits), an L1S or SBAS message (250 bits), and padding (6 bits). The ``--l1s`` option of [ubxread.py](ubxread.md) produces this format. The ``.l1s`` and ``.sbas`` files in the sample directory (except ``20230919-114418.l1s``) are also in this standard-input format.

## Display

Each output line shows the PRN number, the message type number (``MT``), and the message name. When a correction message is received before its mask message (MT1 PRN mask and MT18 IGP mask for SBAS, MT48 PRN mask for L1S), the line is marked as waiting for the mask, e.g. ``(waiting for PRN mask, MT1)``.

Terminal output is displayed in color using ANSI escape sequences. Redirecting terminal output does not print escape sequences. You can turn off color display using a redirect (``qzsl1sread.py < qzss_file.l1s | cat``). On the other hand, to display colors on pagers such as ``less`` and ``lv``, use the ``-c`` option (``qzsl1sread.py -c < qzss_file.l1s | lv``).

When the ``-c`` option is given, it forces the status display to appear in color. By default, if the output destination is a terminal, the status display appears in color. If the output destination is something else, color display is not used.

When the ``-t`` option is given, it outputs details of the messages. This option needs an integer argument. The value 1 produces the detailed information, and the value 2 provides the bit image display in addition to the detailed information.

When the ``--jp`` option is given, it shows the DCR (disaster and crisis management report) content in Japanese. By default, it is shown in English.

## QZSS L1S decode example

We extract QZS L1S raw data from the u-blox ZED-F9P receiver raw data sample ``20230919-114418.ubx`` with [ubxread.py](ubxread.md), and display it with ``qzsl1sread.py``:

```bash
$ ubxread.py --l1s < sample/20230919-114418.ubx | qzsl1sread.py -t 2

PRN137:MT25: Long-term satellite error corrections (waiting for PRN mask, MT1)
PRN186:MT50: DGPS correction (waiting for PRN mask, MT48)
PRN128:MT03: Fast corrections 2 (waiting for PRN mask, MT1)
PRN184:MT50: DGPS correction (waiting for PRN mask, MT48)
PRN137:MT10: Degradation factors
PRN186:MT43: DCR: Marine (Normal) 09-19 08:40 UTC
PRN128:MT02: Fast corrections 1 (waiting for PRN mask, MT1)
PRN184:MT43: DCR: Marine (Normal) 09-19 08:40 UTC
...
PRN186:MT48: PRN mask: selected sats: G03 G04 G16 G18 G25 G26 G27 G28 G29 G31 G32 J02 J03 J04 J07 (15 sats, IODP=2)
...
PRN186:MT49: Data issue number: IODI=3 IODP=2
PRN IOD
G03 100
G04 184
G16   4
G18  50
G25  18
G26  20
G27   8
G28 112
G29  47
G31  27
G32 115
J02  13
J03  13
J04  13
J07  13
 (15 sats)
...
PRN186:MT50: DGPS correction: Sapporo
PRN PRC[m]
G16  -3.08
G26   1.28
G28   2.40
G29   1.36
G31   3.08
G32  -3.28
J02   3.56
J04  -4.00
J07  -1.28
 (9 sats)
```

In this example, QZSS L1S signals (PRN 184 and 186) and SBAS signals (GAGAN PRN 128 and QZSS SBAS PRN 137) are mixed. The ``-p`` option of ``ubxread.py`` selects the messages of a single satellite.

Please refer to the following page to learn how to read the data: [L1S signal analysis with QZS L6 Tool](https://s-taka.org/en/qzsl6tool-20231111upd/)

## Disaster and crisis management report (DCR, DCX) decode example

We display the L1S data ``20260901-040000.l1s`` of QZS-3 (PRN 189) in the sample directory:

```bash
$ qzsl1sread.py < sample/20260901-040000.l1s

PRN189:MT50: DGPS correction (waiting for PRN mask, MT48)
PRN189:MT43: DCR: Typhoon (Normal) 09-01 03:45 UTC
PRN189:MT48: PRN mask: selected sats: G05 G10 G12 G14 G15 G18 G20 G21 G22 G23 G24 G29 J02 J03 J07 (15 sats, IODP=2)
PRN189:MT44: DCX (NULL message)
PRN189:MT49: Data issue number: IODI=2 IODP=2 (15 sats)
PRN189:MT43: DCR: Marine (Normal) 09-01 02:35 UTC
PRN189:MT50: DGPS correction: Sapporo (8 sats)
...
```

With the ``--jp`` option, the DCR is shown in Japanese:

```bash
$ qzsl1sread.py --jp < sample/20260901-040000.l1s

PRN189:MT43: DCR: 台風 (通常) 09-01 03:45 UTC
PRN189:MT43: DCR: 海上 (通常) 09-01 02:35 UTC
...
```

DCX (MT44) is the extended disaster and crisis management report defined in IS-QZSS-DCX-004, which also carries reports for regions outside Japan. Its contents are shown with ``-t 1`` or higher. Normally the DCX messages are null messages (``DCX (NULL message)``), but [test data is distributed](https://qzss.go.jp/technical/dod/dc-report/dcx-test-data-distribution.html) twice a month (Tuesday afternoon of the 1st week and Thursday morning of the 3rd week, JST). This sample was recorded during the test distribution starting at 13:00 JST (04:00 UTC) on 2026-09-01 and contains reports whose message type is ``Test``.

```bash
$ qzsl1sread.py -t 1 < sample/20260901-040000.l1s

...
PRN189:MT44: DCX: Test CBRNE - Air strike (Unknown)
Japan, FMMC (L-Alert)
onset: this week Tue 04:00 UTC, duration 12-24h
library: country/region #1
instruction: ""
target area code: 01101
...
```

The whole hour of the test distribution can be displayed as follows (the distributed contents are described in the documents on the page above):

```bash
curl https://rnav.info.hiroshima-cu.ac.jp/gnss/f9p/202609/20260901e.ubx | ubxread.py --l1s -p 189 | qzsl1sread.py -t 1
```

As an example with more kinds of reports, including those for regions outside Japan, we show the synthetic data ``synthetic-dcx.l1s`` in the sample directory. This is not a real broadcast but hand-made bit patterns generated by ``test/make_synthetic_dcx.py``, using the calculation examples in IS-QZSS-DCX-004 where available.

```bash
$ qzsl1sread.py -t 1 < sample/synthetic-dcx.l1s

PRN186:MT44: DCX (NULL message)
PRN186:MT44: DCX: Alert GEO - Tsunami (Extreme)
Japan, FMMC (L-Alert)
onset: this week Tue 09:30 UTC, duration <6h
library: country/region #1
instruction: "Move to/toward 3rd floor or higher."
ellipse: centre 35.688 139.691, semi-major 10.933[km], semi-minor 4.421[km], azimuth 45.00[deg]
target area code: 01100
PRN186:MT44: DCX: Alert CBRNE - Air strike (Extreme)
Japan, FDMA (J-Alert)
onset: this week Tue 06:40 UTC, duration <6h
library: country/region #1
instruction: "Missile launched, missile launched. It is believed that a missile was launched. Please take shelter inside buildings or underground."
target prefectures: Hokkaido Aomori Iwate
PRN186:MT44: DCX: Alert MET - Storm or thunderstorm (Severe)
Zambia, provider 1
onset: next week Mon 00:00 UTC, duration 12-24h
library: international #1
instruction: IC-A-04 "Seek shelter in a building immediately. Stay under cover and stay informed."
             IC-B-02 "Check with the weather services and local authorities for additional information"
ellipse: centre 0.001 0.001, semi-major 90.407[km], semi-minor 49.439[km], azimuth 0.00[deg]
hazard centre: 0.158 -9.999 (delta +0.15625 -10.00000[deg])
...
```

## SBAS decode example

We display the SBAS data ``20260912-034300.sbas`` of GAGAN (the Indian SBAS, PRN 128, GSAT-10) in the sample directory. This ``.sbas`` file was extracted from u-blox ZED-F9P receiver raw data with ``ubxread.py --l1s -p 128``.

```bash
$ qzsl1sread.py -t 2 < sample/20260912-034300.sbas

...
PRN128:MT01: SBAS PRN mask
selected sats: G01 G02 G03 G04 G05 G06 G07 G08 G09 G10 G11 G12 G13 G14 G15 G16 G17 G18 G19 G20 G21 G22 G23 G24 G25 G26 G27 G28 G29 G30 G31 G32 S127 S128 S132 (35 sats, IODP=3)
...
PRN128:MT02: Fast corrections 1
SAT correction[m] (IODF=1), IODP=3
G01 :   -0.500, UDREI=7
G02 :   -0.125, UDREI=6
G03 :     VOID, UDREI=14
G04 :   -0.500, UDREI=5
...
PRN128:MT25: Long-term satellite error corrections
G03  IOD=62 daf0= 9.313e-09[s] daf1=-3.638e-12[s/s] ti=48624[s]
      dx= 0.000e+00[m]    dy=-3.500e+00[m]    dz=-2.625e+00[m]
     ddx= 0.000e+00[m/s] ddy=-4.883e-04[m/s] ddz= 4.883e-04[m/s]
...
PRN128:MT18: Ionospheric grid point masks
Total_IGP=3 IGP_band=5 IODI=3 IGP_mask_pattern=0 (5 IGPs)
IGP lat[deg] lon[deg]
193       15       55
194       20       55
...
PRN128:MT26: Ionospheric delay corrections
IGP_band=6 IGP_block=2 IODI=3 (15 IGPs)
IGP lat[deg] lon[deg] delay[m] GIVE[m]
 89       -5       75    3.000    15.0
 90        0       75    3.875     6.0
 91        5       75    4.875     6.0
...
PRN128:MT09: GEO ranging function parameters
  t0=48576[s] URA=15 a_Gf0=0.0[s] a_Gf1= 4.547e-12[s/s]
  Xg= 5.141e+03[km]       Yg= 4.185e+04[km]       Zg= 2.155e+01[km]
 dXg=-9.050e-01[m/s]     dYg= 1.975e-01[m/s]     dZg= 4.840e-01[m/s]
ddXg= 3.750e-05[m/s^2]  ddYg= 6.250e-05[m/s^2]  ddZg=-1.250e-04[m/s^2]
...
PRN128:MT17: GEO satellite almanacs
S127 data_ID=0 provider=GAGAN service: ranging corrections integrity
     Xg=  24107.2[km] Yg=  34567.0[km] Zg=    338.0[km] dXg=   0[m/s] dYg=   0[m/s] dZg= -81.92[m/s]
S128 data_ID=0 provider=GAGAN service: ranging corrections integrity
     Xg=   5140.2[km] Yg=  41847.0[km] Zg=     26.0[km] dXg=   0[m/s] dYg=   0[m/s] dZg=   0.00[m/s]
...
PRN128:MT28: Clock-ephemeris covariance matrix
G09  scale_exp=1 (SF=2^-4) E11=342 E22=277 E33=504 E44=16 E12=-32 E13=-12 E14=-73 E23=33 E24=-251 E34=108
     relative covariance matrix (x, y, z, clock):
      4.56891e+02 -4.27500e+01 -1.60312e+01 -9.75234e+01
     -4.27500e+01  3.03723e+02  3.72070e+01 -2.62465e+02
...
```

The QZSS SBAS data ``20260914-045300.sbas`` (PRN 137, QZS-3) can be displayed in the same way.

As an example of the SBAS authentication messages (MT20 and MT21), we show the synthetic data ``synthetic-sbas-auth.sbas`` in the sample directory. This is not a real broadcast but hand-made bit patterns generated by ``test/make_synthetic_sbas_auth.py`` following the draft ICAO SARPs formats.

```bash
$ qzsl1sread.py -t 1 < sample/synthetic-sbas-auth.sbas

PRN128:MT20: SBAS L1 authentication message
beMAC1=1111111 beMAC2=2222222 aMAC=3333333
TESLA hash point=000000000000000000000000deadbeef
PRN128:MT21: SBAS over the air rekeying (OTAR)
IODK_lvl3=3 page=0 level 3 key material, payload 1:
IODK_lvl2=5 MT20_slot=2 validity: start WN=2400 frame=1000, duration 2[week] + 50000[frame]
applicability=SBAS system technique=TESLA hash=SHA-256 valid IODK_lvl3: 0 2
TESLA confirmed hash point=0000000000000000000000000000cafe
...
```

## Real-time streams

It is possible to use real-time streams with [ubxread.py](ubxread.md) and RTKLIB ``str2str``:

```bash
str2str -in ntrip://ntrip.phys.info.hiroshima-cu.ac.jp:80/F9PR 2> /dev/null | ubxread.py --l1s | qzsl1sread.py
```

## References

- Cabinet Office, Government of Japan, Sub-meter level augmentation service archive, https://sys.qzss.go.jp/dod/archives/slas.html
- Cabinet Office, Government of Japan, Quasi-zenith satellite system interface specification DC report service, IS-QZSS-DCR-011, Oct. 2023
- Cabinet Office, Government of Japan, Quasi-zenith satellite system interface specification Sub-meter level augmentation service, IS-QZSS-L1S-006, Oct. 2023
- Cabinet Office, Government of Japan, Quasi-zenith satellite system interface specification DCX report service, IS-QZSS-DCX-004, May 2026
- Electronic Navigation Research Institute, SBAS/L1-SAIF message specification, https://www.enri.go.jp/jp/research/organization/nav/program/message.html (in Japanese)
- RTCA, Minimum operational performance standards for global positioning system/satellite-based augmentation system airborne equipment, DO-229D, Dec. 2006
- K. Alexander, T. Walter, A. Neish, J. Anderson, "SBAS authentication standards," Proc. ION GNSS+ 2024, Sept. 2024 (draft ICAO SARPs, subject to change)
