# Test for QZS L6 Tool functions

Please execute ``do_test.sh`` by
```bash
./do_test
```

This test compares the code result with the previously obtained result stored in ``expect`` directory, and the result should be as follows:

```
1. Pocket SDR to QZS L6 message conversion (../python/pksdr2l6.py)
  20211226-082212pocketsdr-clas.txt: Passed.
  20211226-082212pocketsdr-mdc.txt: Passed.

2. Allystar to QZS L6 message conversion (../python/alst2qzsl6.py)
  20220326-231200clas.alst: Passed.
  20220326-231200mdc.alst: Passed.
  20221130-125237mdc-ppp.alst: Passed.

3. QZS L6 message dump (../python/qzsl62rtcm.py)
  20220326-231200clas.l6: Passed.
  20220326-231200mdc.l6: Passed.
  20221130-125237mdc-ppp.l6: Passed.

4. QZS L6 to RTCM3 message conversion (../python/qzsl62rtcm.py)
  20220326-231200clas.l6: Passed.
  20220326-231200mdc.l6: Passed.
  20221130-125237mdc-ppp.l6: Passed.

5. QZS L6 to RTCM3 message conversion (../python/showrtcm.py)
  20220326-231200clas.rtcm: Passed.
  20220326-231200mdc.rtcm: Passed.
  20221130-125237mdc-ppp.rtcm: Passed.
```

