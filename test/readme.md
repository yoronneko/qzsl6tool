# Test shell script for QZS L6 Tool functions

Please execute ``do_test.sh`` by

```bash
./do_test.sh
```

This test compares the code result with the previously obtained result stored in ``expect`` directory, and the result should be as follows:

```text
$ ./do_test.sh
Pocket SDR log data conversion:
- QZS L6 (../python/psdrread.py -l)
  20211226-082212clas.psdr: Passed.
  20211226-082212mdc.psdr: Passed.
- GAL E6B (../python/psdrread.py -e)
  20230305-063900has.psdr: Passed.

Allystar raw data conversion:
- QZS L6 (../python/alstread.py -l)
  20220326-231200clas.alst: Passed.
  20220326-231200mdc.alst: Passed.
  20221130-125237mdc-ppp.alst: Passed.
  20260908f.alst: Passed.

NovAtel raw data conversion:
- GAL E6B (../python/novread.py -e)
  20230819-053733has.nov: Passed.
  20230819-061342qlnav.nov: Passed.

Septentrio raw data conversion:
- QZS L6 (../python/septread.py -l)
  20230819-082130clas.sbf: Passed.
  20230819-085030mdc-ppp.sbf: Passed.
- GAL E6B (../python/septread.py -e)
  20230819-081730hasbds.sbf: Passed.
- BDS B2b (../python/septread.py -b)
  20230819-081730hasbds.sbf: Passed.

u-blox raw data conversion:
- QZS L1S (../python/ubxread.py --l1s -p 186)
  20230919-114418.ubx: Passed.
- GAL I/NAV (../python/ubxread.py -i)
  20230919-114418.ubx: Passed.

QZS L6 message read (../python/qzsl6read.py -t 2):
  20220326-231200clas.l6: Passed.
  20220326-231200mdc.l6: Passed.
  20221130-125237mdc-ppp.l6: Passed.
  20230819-082130clas.l6: Passed.
  20230819-085030mdc-ppp.l6: Passed.
  20260908f.l6: Passed.
  20260908f-p194.l6: Passed.
  2019001A.l6: Passed.
  2022001A.l6: Passed.
  2024214A.200.l6: Passed.

QZS L1S message read (../python/qzsl1sread.py -t 2):
  20230919-114418.l1s: Passed.

QZS L6 old MADOCA to RTCM SSR message conversion (../python/qzsl6read.py -r)
  20220326-231200mdc.l6: Passed.

QZS L6 CSSR to RTCM 4073 message conversion (../python/qzsl6read.py -r)
  20220326-231200clas.l6: Passed.
  20221130-125237mdc-ppp.l6: Passed.

QZS L6 CSSR to RTCM 4050 message conversion (../python/l6rtcm4050.py )
  2022001A.l6: Passed.

RTCM message read (../python/rtcmread.py -t 2)
  20190529hiroshima.rtcm: Passed.
  20210101jaxamdc.rtcm: Passed.
  20221213-010900.rtcm: Passed.
  20220326-231200clas.4073.rtcm: Passed.
  20220326-231200mdc.rtcm: Passed.
  20221130-125237mdc-ppp.4073.rtcm: Passed.

GAL I/NAV message read (../python/galinavread.py )
  20230919-114418.inav: Passed.

GAL E6 message read (../python/gale6read.py -t 2)
  20230305-063900has.e6b: Passed.
  20230819-081730hasbds.e6b: Passed.

BDS B2 message read (../python/bdsb2read.py -t 2 -p 60)
  20230819-081730hasbds.b2b: Passed.
  ```
