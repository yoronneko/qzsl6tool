# novread.py

This program reads the raw data of NovAtel OEM729 receiver and extracts
Galileo E6B message (HAS, ``-e`` option). The ``--help`` option displays the options it accepts.

```bash
$ novread.py --help
usage: novread.py [-h] [-e | -q] [-c] [-m]

NovAtel message read, QZS L6 Tool ver.x.x.x

options:
  -h, --help     show this help message and exit
  -e, --e6b      send E6B C/NAV messages to stdout, and also turns off display message.
  -q, --qlnav    send QZSS LNAV messages to stdout, and also turns off display message.
  -c, --color    apply ANSI color escape sequences even for non-terminal.
  -m, --message  show display messages to stderr
  ```

When the ``-c`` option is given, it forces the status display to appear in color. By default, if the output destination is a terminal, the status display appears in color. If the output destination is something else, color display is not used.

When the ``-m`` option is given, it outputs the status display to standard error output.
