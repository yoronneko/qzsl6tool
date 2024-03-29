# Test shell script for QZS L6 Tool functions

Please execute ``do_test.sh`` by
```bash
./do_test.sh
```

This test compares the code result with the previously obtained result stored in ``expect`` directory, and the result should be as follows:

```
Pocket SDR log data conversion:
- QZS L6 (psdrread.py -l)
  20211226-082212clas.psdr: Passed.
  20211226-082212mdc.psdr: Passed.
- GAL E6B (psdrread.py -e)
  20230305-063900has.psdr: Passed.

Allystar raw data conversion:
- QZS L6 (alstread.py -l)
  20220326-231200clas.alst: Passed.
  20220326-231200mdc.alst: Passed.
  20221130-125237mdc-ppp.alst: Passed.

NovAtel raw data conversion:
- GAL E6B (novread.py -e)
  20230819-053733has.nov: Passed.
  20230819-053733has.nov: Passed.

Septentrio raw data conversion:
- QZS L6 (septread.py -l)
  20230819-082130clas.sept: Passed.
  20230819-085030mdc-ppp.sept: Passed.
- GAL E6B (septread.py -e)
  20230819-081730hasbds.sept: Passed.

QZS L6 message read (qzsl6read.py -t 2):
  20220326-231200clas.l6: Passed.
  20220326-231200mdc.l6: Passed.
  20221130-125237mdc-ppp.l6: Passed.
  20230819-082130clas.l6: Passed.
  20230819-085030mdc-ppp.l6: Passed.

QZS L6 to RTCM message conversion (qzsl6read.py -r)
  20220326-231200clas.l6: Passed.
  20220326-231200mdc.l6: Passed.
  20221130-125237mdc-ppp.l6: Passed.

RTCM message read (rtcmread.py )
  20220326-231200clas.rtcm: Passed.
  20220326-231200mdc.rtcm: Passed.
  20221130-125237mdc-ppp.rtcm: Passed.
  20221213-010900.rtcm: Passed.

GAL E6 message read (gale6read.py -t 2)
  20230305-063900has.e6b: OMP: Info #276: omp_set_nested routine deprecated, please use omp_set_max_active_levels instead.
Passed.
  20230819-081730hasbds.e6b: OMP: Info #276: omp_set_nested routine deprecated, please use omp_set_max_active_levels instead.
Passed.

--- Compatibility test: you may see update note ---

Pocket SDR to QZS L6 message conversion (pksdr2qzsl6.py)
  20211226-082212clas.psdr: Notice: please use "pksdrread.py -l" (-l option is needed), instead of "pksdr2qzsl6.py" that will be removed.
Passed.
  20211226-082212mdc.psdr: Notice: please use "pksdrread.py -l" (-l option is needed), instead of "pksdr2qzsl6.py" that will be removed.
Passed.

Pocket SDR HAS message read (pksdr2has.py -t 2)
  20220930-115617has.psdr: Notice: please use "pksdrread.py -e | gale6read.py (-e option is needed)", instead of "pksdr2has.py" that will be removed.
OMP: Info #276: omp_set_nested routine deprecated, please use omp_set_max_active_levels instead.
Passed.

NovAtel HAS message read (nov2has.py -t 2)
  20230819-053733has.nov: Notice: please use "novread.py -e | gale6read", instead of "nov2has.py" that will be removed.
OMP: Info #276: omp_set_nested routine deprecated, please use omp_set_max_active_levels instead.
Passed.
```

