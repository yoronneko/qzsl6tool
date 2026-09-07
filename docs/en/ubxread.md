# ubxread.py

This program reads the raw data of u-blox ZED-F9P receiver, and extracts

- SBAS (satellite based augmentation system) and QZS L1S messages (``--l1s`` option),
- GLONASS L1OF/L2OF messages (``--l1of`` option),
- QZS L1S DCR NMEA messages (``--qzqsm`` option),
- GPS/QZSS LNAV messages (``-l`` option),
- BeiDou B1I messages (``--b1i`` option), and
- Galileo E1B I/NAV messages (``-i`` option).

The ``--help`` option displays the options it accepts.

```bash
$ ubxread.py --help
usage: ubxread.py [-h] [--l1s | --l1of | --qzqsm | -l | --b1i | -i] [-d] [-c] [-m] [-p PRN]

u-blox message read, QZS L6 Tool ver.x.x.x

options:
  -h, --help         show this help message and exit
  --l1s              send SBAS and QZS L1S messages to stdout
  --l1of             send GLO L1OF/L2OF messages to stdout
  --qzqsm            send QZS L1S DCR NMEA messages to stdout
  -l, --lnav         send GPS or QZS LNAV messages to stdout
  --b1i              send BDS B1I messages to stdout
  -i, --inav         send GAL I/NAV messages to stdout
  -d, --duplicate    allow duplicate QZS L1S DCR NMEA sentences (currently, all QZS sats send the same DCR messages)
  -c, --color        apply ANSI color escape sequences even for non-terminal.
  -m, --message      show display messages to stderr
  -p PRN, --prn PRN  specify satellite PRN (PRN=0 means all sats)
```

When the ``-c`` option is given, it forces the status display to appear in color. By default, if the output destination is a terminal, the status display appears in color. If the output destination is something else, color display is not used.

When the ``-m`` option is given, it outputs the status display to standard error output.

When the ``-d`` option is given, it also outputs duplicated NMEA messages from the QZSS L1S disaster and crisis warning system. Currently, all QZS satellites transmit the same message. By default, duplicated messages are not outputted.

When the ``-p`` option is given, it uses the satellite with the specified PRN. Without this option, it uses all satellites.
