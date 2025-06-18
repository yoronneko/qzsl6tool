# galinavread.py

This program reads Galileo I/NAV raw data from standard input and prints its contents to standard output.

The ``--help`` option displays the options it accepts.

```bash
$ galinavread.py --help
usage: galinavread.py [-h] [-c]

Galileo I/NAV message read, QZS L6 Tool ver.x.x.x

options:
  -h, --help   show this help message and exit
  -c, --color  apply ANSI color escape sequences even for non-terminal.
```

When the ``-c`` option is given, it forces the status display to appear in color. By default, if the output destination is a terminal, the status display appears in color. If the output destination is something else, color display is not used.

For example, we extract I/NAV raw data from receiver raw data ``20230919-114418.ubx`` with [ubxread.py](ubxread.md), and display it with ``galinavread.py``:

```bash
$ ubxread.py -i < 20230919-114418.ubx| galinavread.py
E05 SSP2 Word 10 (09)
E09 SSP2 Word 10 (09)
E24 SSP2 Word 10 (09)
E25 SSP2 Word 10 (09)
E18      Word 10
E02 SSP2 Word 10 (09)
E03 SSP2 Word 10 (09)
E05 SSP3 Word 18 (11)
E09 SSP3 Word 18 (11)
E24 SSP3 Word 18 (11)
E25 SSP3 Word 18 (11)
E18      Word  0       2023-09-19 11:44:28 (1256 215081)
E02 SSP3 Word 18 (11)
E03 SSP3 Word 18 (11)
E18      Word  0       2023-09-19 11:44:30 (1256 215083)
E02 SSP1 Word 20 (13)
E03 SSP1 Word 20 (13)
E05 SSP1 Word 20 (13)
E09 SSP1 Word 20 (13)
E24 SSP1 Word 20 (13)
E25 SSP1 Word 20 (13)
E05 SSP2 Word 16 (15)
E09 SSP2 Word 16 (15)
E24 SSP2 Word 16 (15)
E25 SSP2 Word 16 (15)
E18      Word  0       2023-09-19 11:44:32 (1256 215085)
E02 SSP2 Word 16 (15)
E03 SSP2 Word 16 (15)
...
```

This output consists of the satellite number (e.g. E05), the SSP (secondary synchronization pattern) number (repeat from 1 to 3), the word number, and the time within a 30 second period estimated from the SSP number and word number.

Older satellites (e.g. E18) do not display SSP numbers. The launch date of the Galileo satellite can be found on the [Quasi-Zenith Satellite homepage, Cabinet Office of Japan](https://qzss.go.jp/en/technical/satellites/index.html#Galileo).
