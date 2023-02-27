# Test for QZS L6 Tool functions

Please execute ``do_test.sh`` by
```bash
./do_test
```

This test compares the code result with the previously obtained result stored in ``expect`` directory, and the result should be as follows:

```
1. Pocket SDR to QZS L6 message conversion (pksdr2qzsl6.py)
  20211226-082212pocketsdr-clas.txt: Passed.
  20211226-082212pocketsdr-mdc.txt: Passed.

2. Allystar to QZS L6 message conversion (alst2qzsl6.py)
  20220326-231200clas.alst: Passed.
  20220326-231200mdc.alst: Passed.
  20221130-125237mdc-ppp.alst: Passed.

3. QZS L6 message dump with -t 2 option (qzsl62rtcm.py)
  20220326-231200clas.l6: Passed.
  20220326-231200mdc.l6: Passed.
  20221130-125237mdc-ppp.l6: Passed.

4. QZS L6 to RTCM message conversion (qzsl62rtcm.py)
  20220326-231200clas.l6: Passed.
  20220326-231200mdc.l6: Passed.
  20221130-125237mdc-ppp.l6: Passed.

5. RTCM message dump (showrtcm.py)
  20220326-231200clas.rtcm: Passed.
  20220326-231200mdc.rtcm: Passed.
  20221130-125237mdc-ppp.rtcm: Passed.
  20221213-010900.rtcm: Passed.

6. Galileo HAS message dump (pksdr2has.py)
  20220930-115617pocketsdr-e6b.txt: OMP: Info #276: omp_set_nested routine deprecated, please use omp_set_max_active_levels instead.
Passed.
  20230219-133831pocketsdr-e6b.txt: OMP: Info #276: omp_set_nested routine deprecated, please use omp_set_max_active_levels instead.
Passed.
```

