# psdrread.py

This program reads the logfile of [Pocket SDR](https://github.com/tomojitakasu/PocketSDR), a software defined radio, and extracts

- QZS L6 messages (``-l`` option),
- Galileo E6B message (HAS, ``-e`` option),
- Galileo E1B I/NAV message (``-i`` option), and
- BeiDou B2b message (``-b`` option).

The ``--help`` option displays the options it accepts.

```bash
$ psdrread.py --help
usage: psdrread.py [-h] [-c] [-b] [-i] [-e] [-l] [-m] [-s] [-t TRACE]

Pocket SDR message read

options:
  -h, --help   show this help message and exit
  -c, --color  apply ANSI color escape sequences even for non-terminal.
  -b, --b2b    send BDS B2b messages to stdout, and also turns off display message.
  -i, --inav   send GAL I/NAV messages to stdout, and also turns off display message.
  -e, --e6b    send GAL E6B messages to stdout, and also turns off display message.
  -l, --l6     send QZS L6 messages to stdout, and also turns off display message.
```

When the ``-c`` option is given, it forces the status display to appear in color. By default, if the output destination is a terminal, the status display appears in color. If the output destination is something else, color display is not used.

When the ``-m`` option is given, it outputs the status display to standard error output.

Reference：[Awesome PocketSDR (L6 band signal decode)](https://s-taka.org/en/awesome-pocketsdr-l6/#l6e)
