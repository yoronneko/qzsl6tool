## qzsl1sread.py

This program reads QZSS L1S format data from standard input or a file and outputs its contents to standard output. The ``--help`` option displays the options it accepts.

```
$ qzsl1sread.py --help
usage: qzsl1sread.py [-h] [-c] [file ...]

Quasi-zenith satellite (QZS) L1S message read

positional arguments:
  file         L1S file(s) obtained from the QZS archive, https://sys.qzss.go.jp/dod/archives/slas.html

options:
  -h, --help   show this help message and exit
  -c, --color  apply ANSI color escape sequences even for non-terminal.
```

If no filename is provided, it reads from standard input. The input format is the same as the [SLAS Archive](https://sys.qzss.go.jp/dod/en/archives/slas.html) on the QZSS official page. Initially, 1 byte (8 bits) of PRN (pseudo random noise) number is followed by 32 bytes (250 bits, the rest is zero-padding) of data.

Terminal output is displayed in color using ANSI escape sequences. Redirecting terminal output does not print escape sequences. You can turn off color display using a redirect (``qzsl1sread.py < qzss_file.l1s | cat``). On the other hand, to display colors on pagers such as ``less`` and ``lv``, use the ``-c`` option (``qzsl1sread.py -c < qzss_file.l1s | lv``).

When the ``-c`` option is given, it forces the status display to appear in color. By default, if the output destination is a terminal, the status display appears in color. If the output destination is something else, color display is not used.

For example, we extract QZS L1S raw data from Allystar receiver raw data sample ``20230919-114418.ubx`` with [ubxread.py](ubxread.md), and display it with ``qzsl1sread.py``:

```
$ ubxread.py --l1s < sample/20230919-114418.ubx | qzsl1sread.py

PRN137: Long-term satellite error corrections
PRN186: DGPS correction: IODP mismatch (mask IODP=0, DGPS IODP=2)
PRN128: Fast corrections 2
PRN184: DGPS correction: IODP mismatch (mask IODP=0, DGPS IODP=2)
PRN137: Degradation parameters
PRN186: JMA DCR: Marine (Normal) 09-19 08:40 UTC
PRN128: Fast corrections 1
PRN184: JMA DCR: Marine (Normal) 09-19 08:40 UTC
...
PRN186: PRN mask: G03 G04 G16 G18 G25 G26 G27 G28 G29 G31 G32 J02 J03 J04 J07 (15 sats, IODP=2)
...
PRN186: Data issue number: IODI=3 IODP=2
  G03 IOD=100
  G04 IOD=184
  G16 IOD=  4
  G18 IOD= 50
  G25 IOD= 18
...
PRN186: DGPS correction: Sapporo
  G16 PRC= -3.08 m
  G26 PRC=  1.28 m
  G28 PRC=  2.40 m
  G29 PRC=  1.36 m
  G31 PRC=  3.08 m
  G32 PRC= -3.28 m
  J02 PRC=  3.56 m
  J04 PRC= -4.00 m
  J07 PRC= -1.28 m
```

Please refere the following page to know how you read the data: [L1S signal analysis with QZS L6 Tool](https://s-taka.org/en/qzsl6tool-20231111upd/)

Also, it is possible to use real-time streams with [ubxread.py](ubxread.md) and RTKLIB ``str2str``:

```
str2str -in ntrip://ntrip.phys.info.hiroshima-cu.ac.jp:80/F9PR 2> /dev/null | ubxread.py --l1s | qzsl1sread.py
```
