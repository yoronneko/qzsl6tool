# QZS L6 Tool: quasi-zenith satellite L6-band tool

https://github.com/yoronneko/qzsl6tool

（日本語の説明は[こちら](readme.md)です）

## Summary

This is a collection of tools that display messages broadcast by the Quasi-Zenith Satellite, petnamed Michibiki, in the L6 frequency band. This was created for my own research, but I think it would be useful for many people.

![QZS L6 Tool](img/test-transmission-of-qzss-madoca-ppp.jpg)

## Application program

This toolkit consists of a python program that receives messages on standard input and sequentially outputs the conversion results to standard output. By using ``nc`` of netcat or ``str2str`` of [RTKLIB](https://github.com/tomojitakasu/RTKLIB), it is possible to utilize information on the network. Standard error output is also available if desired.

This Python code makes use of the ``bitstring`` module. Please install this module with a command ``pip3 install bitstring``.

This toolkit consists of the following programs:
- A program to convert raw data in Michibiki L6 format to RTCM format (``qzsl62rtcm``)
- Programs to extract payload from raw data output of Michibiki L6 band signal receiver (Allystar HD9310C: ``alst2qzsl6.py``, [Pocket SDR](https://github.com/tomojitakasu/PocketSDR): ``pksdr2qzsl6.py``)
- A program to display RTCM messages (``showrtcm.py``)
- Programs to mutually convert between GPS time and UTC (universal coordinate time) (``gps2utc.py``, ``utc2gps.py``)
- Programs to mutually convert between latitude/longitude/elliptical height coordinates and ECEF (earth-centered earth-fixed) coordinates (``llh2ecef.py``, ``ecef2llh.py``)

Here is the directory structure:
```
├── img
│   └── test-transmission-of-qzss-madoca-ppp.jpg
├── license.txt
├── python
│   ├── alst2qzsl6.py
│   ├── ecef2llh.py
│   ├── gps2utc.py
│   ├── libqzsl6tool.py
│   ├── llh2ecef.py
│   ├── pksdr2qzsl6.py
│   ├── qzsl62rtcm.py
│   ├── showrtcm.py
│   └── utc2gps.py
├── readme.md
├── readme-en.md
├── sample
│   ├── 2018001A.l6
│   ├── 20211226-082212pocketsdr-clas.txt
│   ├── 20211226-082212pocketsdr-mdc.txt
│   ├── 2022001A.l6
│   ├── 20220326-231200clas.alst
│   ├── 20220326-231200mdc.alst
│   ├── 20221130-125237mdc-ppp.alst
│   ├── 20221213-010900.rtcm
│   └── readme.txt
└── test
    ├── do_test.sh
    ├── expect
    │   ├── 20211226-082212pocketsdr-clas.l6
    │   ├── 20211226-082212pocketsdr-mdc.l6
    │   ├── 20220326-231200clas.l6
    │   ├── 20220326-231200clas.rtcm
    │   ├── 20220326-231200clas.rtcm.txt
    │   ├── 20220326-231200clas.txt
    │   ├── 20220326-231200mdc.l6
    │   ├── 20220326-231200mdc.rtcm
    │   ├── 20220326-231200mdc.rtcm.txt
    │   ├── 20220326-231200mdc.txt
    │   ├── 20221130-125237mdc-ppp.l6
    │   ├── 20221130-125237mdc-ppp.rtcm
    │   ├── 20221130-125237mdc-ppp.rtcm.txt
    │   ├── 20221130-125237mdc-ppp.txt
    │   └── 20221213-010900.rtcm.txt
    └── readme.md
```

### qzsl62rtcm.py

This is a program that converts raw data in Michibiki L6 format into RTCM format. If no options are specified, the results of decoding Michibiki control station and L6 messages are displayed on the standard output.

CLAS (centimeter level augmentation service), MADOCA (multi-GNSS advanced demonstration tool for orbit and clock analysis), MADOCA-PPP (Multi-GNSS Advanced Orbit and Clock Augmentation - Precise Point Positioning) can be handled as raw data in L6 format. It can also be converted to messages in RTCM (Radio Technical Commission for Maritime Services) format.

We can display the options it accepts by giving the ``--help`` option.

```
usage: qzsl62rtcm.py [-h] [-t TRACE] [-r] [-s] [-m]

Quasi-zenith satellite (QZS) L6 message to RTCM converter

options:
  -h, --help            show this help message and exit
  -t TRACE, --trace TRACE
                        trace level for debug: 1=subtype detail, 2=subtype and
                        bit image
  -r, --rtcm            RTCM message output, supress QZS messages (unless -s
                        is specified)
  -s, --statistics      show CSSR statistics
  -m, --message         show QZS messages and statistics to stderr
```

Decryption example of CLAS message

For example, in the ``python`` directory, if you give the L6 raw data to the standard input of ``qzsl62rtcm.py`` with the following command, the contents will be displayed.
```
cat ../sample/20220326-231200clas.alst | python alst2qzsl6.py -l | python qzsl62rtcm.py

199 Hitachi-Ota:1  CLAS
(...snip...)
194 Hitachi-Ota:1  CLAS
194 Hitachi-Ota:1  CLAS  SF1 DP1 ST1 ST3 ST2 ST4...
196 Hitachi-Ota:1  CLAS  SF1 DP2 ST4 ST7 ST11 ST6 ST12...
(...snip...)
```

``alst2qzsl6.py`` is a program that reads the sample data collected by the Allystar receiver. If you give it the ``-l`` option, it will output L6 raw data to standard output.

Upon receiving a Subtype 1 message, this program will start decoding the CLAS message. ``...`` indicates the message continues to the next data part. On the other hand, ``(null)`` indicates the entire data part is null. The first number in each line is the PRN (pseudo random noise) number, the next column is the control station (Hitachi-Ota or Kobe), the next number (0 or 1) is the transmitting system number, and the next column indicates the CLAS message. increase. ``SF`` is the subframe number, and ``DP`` is the data part number.  
Reference: [Compact SSR display capability on QZS L6 Tool](https://s-taka.org/en/qzsl6tool-20220329upd/)

By using RTKLIB's command line application ``str2str``, we can use real-time stream data provided on the Internet.
```
str2str -in ntrip://ntrip.phys.info.hiroshima-cu.ac.jp:80/CLAS 2> /dev/null | alst2qzsl6.py -l | qzsl62rtcm.py
```

Giving a number 1 or 2 along with the ``-t`` option to ``qzsl62rtcm.py``, we can obtain the details of the message as the output. A value of 1 outputs the message content, and a value of 2 outputs a bit image in addition to the message content.

Also, if we give the ``-s`` option, it will output statistics every time subtype 1 is received.
```
stat n_sat 17 n_sig 48 bit_sat 13050 bit_sig 5114 bit_other 1931 bit_null 5330 bit_total 25425
```
``n_sat`` is the number of satellites to be augmented, ``n_sig`` is the number of signals, ``bit_sat`` is the number of information bits about satellites, ``bit_sig`` is the number of information bits about signals, ``bit_other`` is the number of information bits not related to satellites nor signals, ``bit_null`` is the number of null bits, and ``bit_total`` is the total number of message bits.  
Reference: [Capacity analysis of CLAS satellite augmentation information using QZSS archive data](https://s-taka.org/en/202206ipntj-clas-capacity/)

Giving the ``-r`` option to ``qzsl62rtcm.py`` suppresses the display of message contents and outputs RTCM messages to the standard output. At this time, if the ``-m`` option is also specified, the RTCM message will be output to the standard output, while the message content will be output to the standard error output.

However, Compact SSR (space state representation) messages of CLAS and MADOCA-PPP are output as RTCM message type 4073, so we cannot be directly used as the augmentation messages for, say, RTKLIB.

Decoding example of MADOCA message

No MADOCA messages are currently being sent. For example, in the ``python`` directory, we can view the contents of MADOCA messages by running the following command.
```
cat ../sample/20220326-231200mdc.alst | python alst2qzsl6.py -l | python qzsl62rtcm.py

209 Hitachi-Ota:0* MADOCA 2022-03-26 23:11:44 RTCM 1062(26) RTCM 1068(17)
206 Hitachi-Ota:0* MADOCA 2022-03-26 23:11:44 RTCM 1057(8) RTCM 1061(8)
206 Hitachi-Ota:0* MADOCA 2022-03-26 23:11:46 RTCM 1062(26) RTCM 1068(17)
206 Hitachi-Ota:0* MADOCA 2022-03-26 23:11:46 RTCM 1057(8) RTCM 1061(8)
(...snip...)
```
For example, the first line, from PRN 209 (QZS-3), is the message generated from the first of the two systems at the Hitachi-Ota control station, alert flag on (shown as asterisk), time, and RTCM message, the type and the number of augmentation satellites.

Here, the included RTCM message number and the number of satellites to be augmented are displayed in parentheses. In order to observe the contents, give the ``-r`` option to ``qzsl62rtcm.py`` to output the RTCM message, and observe the RTCM message with ``showrtcm.py``.

```
cat ../sample/20220326-231200mdc.alst | python alst2qzsl6.py -l | python qzsl62rtcm.py -r | python showrtcm.py

RTCM 1062 G SSR hr clock  G01 G02 G03 G05 G06 G07 G08 G09 G10 G12 G13 G15 G16 G1
7 G19 G20 G21 G22 G24 G25 G26 G27 G29 G30 G31 G32 (nsat=26 iod=12)
RTCM 1068 R SSR hr clock  R01 R02 R03 R04 R05 R07 R08 R12 R13 R14 R15 R17 R18 R1
9 R20 R21 R22 (nsat=17 iod=8)
RTCM 1057 G SSR orbit     G10 G12 G13 G15 G16 G17 G19 G20 (nsat=8 iod=13 cont.)
(...snip...)
```

Decoding example of MADOCA-PPP message

Running the following command prints the contents of the MADOCA-PPP message.
```
cat ../sample/20221130-125237mdc-ppp.alst | python alst2qzsl6.py -l | python qzsl62rtcm.py

205 Hitachi-Ota:1  MADOCA-PPP
205 Hitachi-Ota:1  MADOCA-PPP
205 Hitachi-Ota:1  QZNMA
205 Hitachi-Ota:1  QZNMA
205 Hitachi-Ota:1  MADOCA-PPP
205 Hitachi-Ota:1  MADOCA-PPP
205 Hitachi-Ota:1  MADOCA-PPP
205 Hitachi-Ota:1  MADOCA-PPP  SF1 DP1 (Clk/Eph LNAV) ST1 ST2...
205 Hitachi-Ota:1  MADOCA-PPP  SF1 DP2 (Clk/Eph LNAV) ST2...
205 Hitachi-Ota:1  MADOCA-PPP  SF1 DP3 (Clk/Eph LNAV) ST2 ST3
205 Hitachi-Ota:1  MADOCA-PPP  SF1 DP4 (Clk/Eph LNAV) (null)
205 Hitachi-Ota:1  MADOCA-PPP  SF1 DP5 (Clk/Eph LNAV) (null)
(...snip...)
```

We can also observe the contents of the MADOCA-PPP real-time stream provided on the Internet.
```
str2str -in ntrip://ntrip.phys.info.hiroshima-cu.ac.jp:80/MADOCA 2> /dev/null | alst2qzsl6.py -l | qzsl62rtcm.py
```

Reference: [Trial delivery of QZSS's MADOCA-PPP started](https://s-taka.org/en/test-transmission-of-qzss-madoca-ppp/)

### showrtcm.py

``showrtcm.py`` is a program that receives RTCM messages on standard input and displays the contents on standard output. It can also interpret the state-space representation (SSR) of MADOCA. For example, ``showrtcm.py`` is used as follows:
```
cat ../sample/20220326-231200mdc.alst | python alst2qzsl6.py -l | python qzsl62rtcm.py -r | python showrtcm.py

RTCM 1062 G SSR hr clock  G01 G02 G03 G05 G06 G07 G08 G09 G10 G12 G13 G15 G16 G1
7 G19 G20 G21 G22 G24 G25 G26 G27 G29 G30 G31 G32 (nsat=26 iod=12)
```

Using the RTKLIB ``str2str`` application, it is possible to display the RTCM message of, say, the [RTK reference station](https://s-taka.org/en/rtk-reference-station/).
```
str2str -in ntrip://ntrip.phys.info.hiroshima-cu.ac.jp:80/OEM7 2> /dev/null | python showrtcm.py

RTCM 1005   Position      34.4401061 132.4147804 233.362
RTCM 1033   Ant/Rcv info  JAVGRANT_G5T NONE s/n 0 rcv "NOV OEM729" ver OM7MR0810RN0000
RTCM 1045 E F/NAV         E30
RTCM 1046 E I/NAV         E30
RTCM 1077 G MSM7          G04 G07 G08 G09 G16 G18 G21 G26 G27
RTCM 1087 R MSM7          R09 R15 R17 R18 R19
RTCM 1097 E MSM7          E02 E03 E10 E11 E25 E30 E34 E36
RTCM 1117 J MSM7          J02 J03 J04 J07
RTCM 1127 C MSM7          C03 C04 C06 C07 C09 C10 C11 C16 C23 C39
RTCM 1127 C MSM7          C01 C02 C12 C25 C28 C34 C37 C40 C43 C59
RTCM 1137 I MSM7          I02 I03 I04 I07
RTCM 1045 E F/NAV         E02
RTCM 1046 E I/NAV         E02
RTCM 1020 R NAV           R17
```

### alst2qzsl6.py

This program reads the raw data of the Allystar HD9310 Option C receiver from standard input and displays its status on standard output. In each row of the status display, the 1st column is the PRN number, the 2nd and 3rd columns are the GPS week number and second, the 4th column is the C/No [dB Hz], and the 5th column is the error if any. Each represents its contents. The ``--help`` option displays the options it accepts.
```
usage: alst2qzsl6.py [-h] [-l | -u] [-m]

Allystar HD9310 to Quasi-zenith satellite (QZS) L6 message converter

options:
  -h, --help     show this help message and exit
  -l, --l6       L6 message output
  -u, --ubx      u-blox L6 raw message output
  -m, --message  show Allystar messages to stderr
```

If we run ``alst2qzsl6.py`` with the ``-l`` option, L6 messages will be output to the standard output instead of the status display. It selects the satellite with the highest signal strength among multiple Michibiki satellites that it can receive and outputs its 2,000 bytes L6 raw data to standard output. If we specify the ``-m`` option together with the ``-l`` option, L6 raw data will be output to the standard output, and the reception status will be output to the standard error output.

If the ``-u`` option is given, it will output L6 messages in u-blox format to standard output. Given this message to a u-blox F9P receiver, it should be able to do a CLAS fix as well as a message generated by a D9C receiver. But there still seems to be an error in the code and it doesn't work.

### pksdr2qzsl6.py

This is the code to extract L6 messages from the log file of [Pocket SDR](https://github.com/tomojitakasu/PocketSDR), a software defined radio.
参考：[Awesome PocketSDR (L6 band signal decode)](https://s-taka.org/en/awesome-pocketsdr-l6/#l6e)

### ecef2llh.py

Converts ECEF (earth-centered, earth-fix) coordinates to latitude, longitude, and ellipsoidal height. An execution example is as follows:
```
python ecef2llh.py -3551876.829 3887786.860 3586946.387

34.4401061 132.4147804 233.362
```

### llh2ecef.py

Convert latitude, longitude, and ellipsoidal height to ECEF coordinates. An execution example is as follows:
```
python llh2ecef.py 34.4401061 132.4147804 233.362

-3551876.829 3887786.860 3586946.387
```

### gps2utc.py

Convert GPS time to UTC time. An execution example is as follows:
```
python gps2utc.py 2238 305575

2022-11-30 12:52:37
```

### utc2gps.py

Convert UTC time to GPS time. An execution example is as follows:
```
python utc2gps.py 2022-11-30 12:52:37

2238 305575
```

## License

The [BSD 2-clause license](https://opensource.org/licenses/BSD-2-Clause) is applied to this toolkit. You may use this program for commercial or non-commercial purposes, with or without modification, but this copyright notice is required. A part of [RTKLIB](https://github.com/tomojitakasu/RTKLIB) 2.4.3b34 functions of getbitu(), getbits(), setbitu(), setbits(), getbits38(), getbits38(), rtk_crc32(), rtk_crc24q (), rtk_crc16 () are used in ``libqzsl6tool.py``.

Copyright (c) 2022 by Satoshi Takahashi  
Copyright (c) 2007-2020 by Tomoji TAKASU