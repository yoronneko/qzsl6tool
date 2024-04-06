# qzsl6read.py

This program reads QZS L6 raw data from standard input and prints its contents to standard output.

This program can handle raw data in L6 format as

- CLAS (centimeter level augmentation service),
- MADOCA (multi-GNSS advanced demonstration tool for orbit and clock analysis), and
- MADOCA-PPP (Multi-GNSS Advanced Orbit and Clock Augmentation - Precise Point Positioning).

MADOCA is in RTCM (Radio Technical Commission for Maritime Services) SSR (State Space Representation) format, and CLAS and MADOCA-PPP are in CSSR (Compact SSR) format.

The ``--help`` option displays the options it accepts.

```bash
$ qzsl6read.py --help
usage: qzsl6read.py [-h] [-c] [-m] [-r] [-s] [-t TRACE]

Quasi-zenith satellite (QZS) L6 message read

options:
  -h, --help            show this help message and exit
  -c, --color           apply ANSI color escape sequences even for non- terminal.
  -m, --message         show display messages to stderr
  -r, --rtcm            send RTCM messages to stdout (it also turns off display messages unless -m is specified).
  -s, --statistics      show CSSR statistics in display messages.
  -t TRACE, --trace TRACE show display verbosely: 1=subtype detail, 2=subtype and bit image.
```

Terminal output is displayed in color using ANSI escape sequences. Redirecting terminal output does not print escape sequences. You can turn off color display using a redirect (``qzsl6read.py < qzss_file.l6 | cat``). On the other hand, to display colors on pagers such as ``less`` and ``lv``, use the ``-c`` option (``qzsl6read.py -c < qzss_file.l6 | lv``).

When the ``-c`` option is given, it forces the status display to appear in color. By default, if the output destination is a terminal, the status display appears in color. If the output destination is something else, color display is not used.

When the ``-m`` option is given, it outputs the status display to standard error output.

When the ``-s`` option is given, it also outputs the statistics information.

When the ``-t`` option is given, it output detail on the messages. This option needs integer argument. The value 1 produces the detailed information, and the value 2 provides bit image display in addition of the detailed information.

By using RTKLIB's ``str2str``, you can also use real-time streams.

````bash
str2str -in ntrip://ntrip.phys.info.hiroshima-cu.ac.jp:80/CLAS 2> /dev/null | alstread.py -l | qzsl6read.py
````

### CLAS decode example

For example, we extract QZS L6 raw data from Allystar receiver raw data sample ``20220326-231200clas.alst`` with [alstread.py](alstread.md), and display it with ``qzsl6read.py``:

```bash
alstread.py -l < sample/20220326-231200clas.alst | qzsl6read.py

199 Hitachi-Ota:1  CLAS  (syncing)
199 Hitachi-Ota:1  CLAS  SF1 DP1 ST1 ST3 ST2 ST4...
199 Hitachi-Ota:1  CLAS  SF1 DP2 ST4 ST7 ST11 ST6 ST12...
199 Hitachi-Ota:1  CLAS  SF1 DP3 ST12 ST6 ST12...
199 Hitachi-Ota:1  CLAS  SF1 DP4 ST12
199 Hitachi-Ota:1  CLAS  SF1 DP5 (null)
199 Hitachi-Ota:1  CLAS  SF2 DP1 ST3 ST11 ST6 ST12...
199 Hitachi-Ota:1  CLAS  SF2 DP2 ST12...
199 Hitachi-Ota:1  CLAS  SF2 DP3 ST12 ST6...
199 Hitachi-Ota:1  CLAS  SF2 DP4 ST6 ST12...
199 Hitachi-Ota:1  CLAS  SF2 DP5 ST12
```

The first number in each line is the PRN (pseudo random noise) number, the next column is the control station (Hitachi-Ota or Kobe), the next number (0 or 1) is the transmitting system number, and the next column indicates the CLAS message. increase. ``SF`` is the subframe number, and ``DP`` is the data part number.  

Upon receiving a Subtype 1 (ST1) message, this program will start decoding the CLAS message. 

``...`` indicates that the message continues to the next data part. In the example above, DP1 has ST1, ST3, ST2, and ST4 follows the next data part. DP2 is headed by ``ST4``, which is the continuation ST4 message from DP1.

On the other hand, ``(null)`` indicates the entire data part is null.

Reference: [Compact SSR display capability on QZS L6 Tool](https://s-taka.org/en/qzsl6tool-20220329upd/)

Giving ``-t 2`` option to ``qzsl6read.py``, we can obtain the details of the message as the output:

```bash
alstread.py -l < sample/20220326-231200clas.alst | qzsl6read.py -t 2

199 Hitachi-Ota:1  CLAS  (syncing)
...
ST1 G10 L1 C/A L2 CM+CL L2 Z-tracking L5 I+Q
ST1 G12 L1 C/A L2 CM+CL L2 Z-tracking
ST1 G22 L1 C/A L2 Z-tracking
...
ST3 G10 d_clock= -0.883m
ST3 G12 d_clock=  0.773m
ST3 G22 d_clock=  0.069m
...
ST2 G10 IODE=  10 d_radial= 0.0272m d_along= 0.2432m d_cross=-0.5952m
ST2 G12 IODE=  56 d_radial=-0.0704m d_along= 1.4912m d_cross= 0.0448m
ST2 G22 IODE=  35 d_radial=-0.0304m d_along=-1.3440m d_cross=-0.6464m
...
```

If we give the ``-s`` option to ``qzsl6read.py``, it will output statistics every time subtype 1 is received:

```text
stat n_sat 17 n_sig 48 bit_sat 13050 bit_sig 5114 bit_other 1931 bit_null 5330 bit_total 25425
```

Where,

- ``n_sat`` is the number of satellites to be augmented,
- ``n_sig`` is the number of signals,
- ``bit_sat`` is the number of information bits about satellites,
- ``bit_sig`` is the number of information bits about signals,
- ``bit_other`` is the number of information bits not related to satellites nor signals,
- ``bit_null`` is the number of null bits, and
- ``bit_total`` is the total number of message bits.  

Reference: [Capacity analysis of CLAS satellite augmentation information using QZSS archive data](https://s-taka.org/en/202206ipntj-clas-capacity/)

### MADOCA-PPP decode example

We extract and display QZS L6 raw data from Allystar receiver raw data sample ``20221130-125237mdc-ppp.alst``:

```bash
alstread.py -l < sample/20221130-125237mdc-ppp.alst | qzsl6read.py

205 Hitachi-Ota:1  MADOCA-PPP  (syncing)
205 Hitachi-Ota:1  QZNMA       (inactive) (inactive)
205 Hitachi-Ota:1  QZNMA       (inactive) (inactive)
205 Hitachi-Ota:1  MADOCA-PPP  (syncing)
205 Hitachi-Ota:1  MADOCA-PPP  (syncing)
205 Hitachi-Ota:1  MADOCA-PPP  (syncing)
205 Hitachi-Ota:1  MADOCA-PPP  SF1 DP1 (Clk/Eph LNAV) ST1 ST2...
205 Hitachi-Ota:1  MADOCA-PPP  SF1 DP2 (Clk/Eph LNAV) ST2...
205 Hitachi-Ota:1  MADOCA-PPP  SF1 DP3 (Clk/Eph LNAV) ST2 ST3
205 Hitachi-Ota:1  MADOCA-PPP  SF1 DP4 (Clk/Eph LNAV) (null)
...
```

Similar to CLAS, in MADOCA-PPP, the ``-t 2`` option to ``qzsl6read.py`` will display details (Reference: [Trial delivery of QZSS's MADOCA-PPP started](https://s-taka.org/en/test-transmission-of-qzss-madoca-ppp/)).


### MADOCA decode example

MADOCA message distribution has ended.

We extract and display QZS L6 raw data from Allystar receiver raw data sample ``20220326-231200mdc.alst``:

```bash
alstread.py -l < sample/20220326-231200mdc.alst| qzsl6read.py

209 Hitachi-Ota:0* MADOCA 2022-03-26 23:11:44 RTCM 1062(26) RTCM 1068(17)
209 Hitachi-Ota:0* MADOCA 2022-03-26 23:11:44 RTCM 1057(8) RTCM 1061(8)
206 Hitachi-Ota:0* MADOCA 2022-03-26 23:11:46 RTCM 1062(26) RTCM 1068(17)
206 Hitachi-Ota:0* MADOCA 2022-03-26 23:11:46 RTCM 1057(8) RTCM 1061(8)
...
```

For example, the first line, from PRN 209 (QZS-3), is the message generated from the first of the two systems at the Hitachi-Ota control station, alert flag on (shown as asterisk), time, and RTCM message, the type and the number of augmentation satellites.

Here, the included RTCM message number and the number of satellites to be augmented are displayed in parentheses.

Here, the included RTCM message number and the number of satellites to be augmented are displayed in parentheses. You can display the reinforcement content by giving the ``-t 2`` option to ``qzsl6read.py``:

```bash
alstread.py -l < sample/20220326-231200mdc.alst| qzsl6read.py -t 2

G01 high_rate_clock=  0.430m
G02 high_rate_clock=  0.106m
G03 high_rate_clock= -0.745m
...
209 Hitachi-Ota:0* MADOCA 2022-03-26 23:11:44 RTCM 1062(26) RTCM 1068(17)
G10 d_radial= 0.0038m d_along= 0.6916m d_cross=-0.0513m dot_d_radial=-0.0002m/s
dot_d_along=-0.0005m/s dot_d_cross= 0.0001m/s
...
G10 ura=   3.50 mm
G12 ura=   3.50 mm
G13 ura=   3.50 mm
...
09 Hitachi-Ota:0* MADOCA 2022-03-26 23:11:44 RTCM 1057(8) RTCM 1061(8)
G01 high_rate_clock=  0.429m
G02 high_rate_clock=  0.107m
G03 high_rate_clock= -0.745m
...
```
