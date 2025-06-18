# gale6read.py

This program reads Galileo HAS (high accuracy service) raw data from standard input and prints its contents to standard output.

This input consists of 1 byte of PRN and 62 bytes (492 bits of HAS raw data).

The ``--help`` option displays the options it accepts.

```bash
$ gale6read.py --help
usage: gale6read.py [-h] [-c] [-m] [-s] [-t TRACE]

Galileo E6B message read, QZS L6 Tool ver.x.x.x

options:
  -h, --help            show this help message and exit
  -c, --color           apply ANSI color escape sequences even for non-terminal.
  -m, --message         show display messages to stderr
  -s, --statistics      show HAS statistics in display messages.
  -t TRACE, --trace TRACE show display verbosely: 1=detail, 2=bit image.
```

When the ``-c`` option is given, it forces the status display to appear in color. By default, if the output destination is a terminal, the status display appears in color. If the output destination is something else, color display is not used.

When the ``-m`` option is given, it outputs the status display to standard error output.

When the ``-s`` option is given, it also outputs the statistics information.

When the ``-t`` option is given, it output detail on the messages. This option needs integer argument. The value 1 produces the detailed information, and the value 2 provides bit image display in addition of the detailed information.

For example, we extract HAS raw data from Pocket SDR logfile ``20230305-063900has.psdr`` with [psdrread.py](psdrread.md), and display it with ``gale6read.py``:

```bash
$ psdrread.py -e < sample/20230305-063900has.psdr| gale6read.py -t 2

...
E12 HASS=Operational(1) MT=1 MID=17 MS=11 PID=161
------ HAS decode with the pages of MID=17 MS=11 ------
0x92ec806220ffbffb2f008140fbffffffeff7fb6fffffc13df914f36824820014a41b2e6a062320
12fef014abfefc1bc0145fd11ec7f9e05fe7feefe90d00080e7f4a0ffa3ff41f14c089fc0002a608
ce9bf7391f567e77fd297f54173ec067f8600bfb867e68fa6fb44c000010fee97809fe7bf704fff1
f8000efbe41f...
------
Time of hour TOH: 2350 s
Mask            : on
Orbit correction: on
Clock full-set  : off
Clock subset    : off
Code bias       : on
Phase bias      : off
Mask ID         : 3
IOD Set ID      : 2
MASK G01 L1 C/A L2 CL L2 P
MASK G02 L1 C/A L2 P
MASK G03 L1 C/A L2 CL L2 P
...
ORBIT validity_interval=300s (10)
ORBIT G01 IODE=  82 d_radial= 1.0850m d_track=-3.2480m d_cross= 0.7840m
ORBIT G02 IODE=  50 d_radial= 0.0925m d_track=-0.2720m d_cross= 0.3280m
ORBIT G03 IODE=  87 d_radial=-0.1625m d_track= 0.8880m d_cross= 0.0400m
ORBIT G04 IODE=  23 d_radial=-0.9400m d_track=-1.2560m d_cross=-0.3920m
ORBIT G05 IODE=   2 d_radial=-0.0625m d_track=-0.1440m d_cross=-0.1840m
ORBIT G06 IODE=  13 d_radial= 0.0025m d_track= 0.2240m d_cross=-0.1840m
ORBIT G07 IODE=  65 d_radial=-0.0600m d_track=-0.0240m d_cross= 0.9920m
```

Reference: [Galileo HAS (high accuracy service) Part 2](https://s-taka.org/en/galileo-has-part2/), [HAS message display capability on QZS L6 Tool](https://s-taka.org/en/qzsl6tool-20230305upd/)
