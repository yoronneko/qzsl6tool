# gps2utc.py

This program converts GPS time, Galileo Standard Time (GST), and BeiDou Standard Time (BST) to UTC time. This program reads the week number (WN) and the second from the week (TOW: time of week), and displays their times.

```bash
$ gps2utc.py
GNSS time to UTC conversion
Usage: /Users/sat/bin/gps2utc.py week_no time_of_week
```

An execution example to provide the WN of 2238 and the TOW of 305575 is as follows:

```bash
$ gps2utc.py 2238 305575
GPS 2022-11-30 12:52:37
GST 2042-07-16 12:52:42
BDT 2048-11-25 12:52:51
```

This results show:

- 2022-11-30 12:52:37 as GPS time,
- 2042-07-16 12:52:42 as GST, and
- 2048-11-25 12:52:51 as BST.
