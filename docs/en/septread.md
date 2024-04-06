# septread.py

This program reads the raw data of Septentrio's mosaic-X5 receiver or mosaic-CLAS receiver, and extracts

- QZS L6 messages (``-l`` option),
- Galileo E6B message (HAS, ``-e`` option),
- BeiDou B2b message (``-b`` option).

The ``--help`` option displays the options it accepts.

```bash
$ septread.py --help
usage: septread.py [-h] [-c] [-e] [-l] [-m]

Septentrio message read

options:
  -h, --help     show this help message and exit
  -c, --color    apply ANSI color escape sequences even for non-terminal.
  -e, --e6b      send E6B messages to stdout, and also turns off display message.
  -l, --l6       send QZS L6 messages to stdout (it also turns off Septentrio messages).
  -b, --b2b      send BDS B2b messages to stdout, and also turns off display message.
  -m, --message  show display messages to stderr
```

When the ``-c`` option is given, it forces the status display to appear in color. By default, if the output destination is a terminal, the status display appears in color. If the output destination is something else, color display is not used.

When the ``-m`` option is given, it outputs the status display to standard error output.
