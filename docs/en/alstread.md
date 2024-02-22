## alstread.py

This program reads the raw data of the Allystar HD9310 Option C receiver from standard input and displays its status on standard output.

In each row of the status display, the 1st column is the PRN number, the 2nd and 3rd columns are the GPS week number and second, the 4th column is the C/No [dB Hz], and the 5th column is the error if any. Each represents its contents. The ``--help`` option displays the options it accepts.

```
$ alstread.py --help
usage: alstread.py [-h] [-c] [-l] [-m] [-p PRN]

Allystar HD9310 message read

options:
  -h, --help         show this help message and exit
  -c, --color        apply ANSI color escape sequences even for non-terminal.
  -l, --l6           send QZS L6 messages to stdout (it also turns off Allystar and u-blox messages).
  -m, --message      show Allystar messages to stderr.
  -p PRN, --prn PRN  satellite PRN to be specified.
```

When the `-c` option is given, it forces the status display to appear in color. By default, if the output destination is a terminal, the status display appears in color. If the output destination is something else, color display is not used.

When the `-l` option is given, instead of a status display, it outputs the QZSS L6 messages to standard output. This selects and outputs the satellite with the highest signal strength among the multiple QZSS satellites that can be received.

When the `-m` option is given, it outputs the status display to standard error output. This option is used together with the `-l` option.

When the `-p` option is given, instead of using the satellite with the highest signal strength, it uses the satellite specified by the given PRN. This option is used together with the `-l` option.
