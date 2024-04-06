# Test shell script for QZS L6 Tool functions

Please execute ``do_test.sh`` by

```bash
./do_test.sh
```

This test compares the code result with the previously obtained result stored in ``expect`` directory, and the result should be as follows:

```text
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

NovAtel raw data conversion:
- GAL E6B (../python/novread.py -e)
  20230819-053733has.nov: Passed.
  20230819-061342qlnav.nov: Passed.

Septentrio raw data conversion:
- QZS L6 (../python/septread.py -l)
  20230819-082130clas.sept: Passed.
  20230819-085030mdc-ppp.sept: Passed.
- GAL E6B (../python/septread.py -e)
  20230819-081730hasbds.sept: Passed.
- BDS B2b (../python/septread.py -b)
  20230819-081730hasbds.sept: Passed.

u-blox raw data conversion:
- QZS L1S (../python/ubxread.py --l1s -p 186)
  20230919-114418.ubx: Passed.

QZS L6 message read (../python/qzsl6read.py -t 2):
  20220326-231200clas.l6: Passed.
  20220326-231200mdc.l6: Passed.
  20221130-125237mdc-ppp.l6: Passed.
  20230819-082130clas.l6: Passed.
  20230819-085030mdc-ppp.l6: Passed.

QZS L1S message read (../python/qzsl1sread.py ):
  20230919-114418.l1s: Passed.

QZS L6 to RTCM message conversion (../python/qzsl6read.py -r)
  20220326-231200clas.l6: Passed.
  20220326-231200mdc.l6: Passed.
  20221130-125237mdc-ppp.l6: Passed.

RTCM message read (../python/rtcmread.py )
  20220326-231200clas.rtcm: Passed.
  20220326-231200mdc.rtcm: Passed.
  20221130-125237mdc-ppp.rtcm: Passed.
  20221213-010900.rtcm: Passed.

GAL E6 message read (../python/gale6read.py -t 2)
  20230305-063900has.e6b: OMP: Info #276: omp_set_nested routine deprecated, please use omp_set_max_active_levels instead.
Passed.
  20230819-081730hasbds.e6b: OMP: Info #276: omp_set_nested routine deprecated, please use omp_set_max_active_levels instead.
Passed.

BDS B2 message read (../python/bdsb2read.py -t 2 -p 60)
  20230819-081730hasbds.b2b: Passed.
  ```

