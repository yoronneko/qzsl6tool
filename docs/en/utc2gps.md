# utc2gps.py

This program converts UTC time to GPS time, Galileo Standard Time (GST), and BeiDou Standard Time (BST).

```bash
$ utc2gps.py
UTC to GNSS time conversion
Usage: /Users/sat/bin/utc2gps.py YYYY-MM-DD hh:mm:ss
Current GNSS time (week number, time of week):
GPS 2302 396952
GST 1278 396947
BDT 946 396938
```

An execution example to provide the UTC of 2022-11-30 12:52:37 is as follows:

```bash
utc2gps.py 2022-11-30 12:52:37

GPS 2238 305575
GST 1214 305570
BDT 882 305561
```

This results show:

- for GPS time, the week number (WN) of GPS time is2238, the seconds from the week (TOW: time of week) is 305575,
- for GST, WN is 1214 and TOW is 305570, and
- for BST, WN is 882 and TOW is 305561.
