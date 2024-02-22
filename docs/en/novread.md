## novread.py

This program reads the raw data of NovAtel OEM729 receiver and extracts
Galileo E6B message (HAS, ``-e`` option). The ``--help`` option displays the options it accepts.

```
$ novread.py --help
usage: novread.py [-h] [-c] [-e] [-l] [-m] [-s] [-t TRACE]

NovAtel message read

options:
  -h, --help            show this help message and exit
  -c, --color           apply ANSI color escape sequences even for non-
                        terminal.
  -e, --e6b             send E6B C/NAV messages to stdout, and also turns off
                        display message.
  -l, --l6              send L6 messages to stdout, and also turns off display
                        message.
  -m, --message         show display messages to stderr
  -s, --statistics      show HAS statistics in display messages.
  -t TRACE, --trace TRACE
                        show display verbosely: 1=detail, 2=bit image.
```
When the ``-c`` option is given, it forces the status display to appear in color. By default, if the output destination is a terminal, the status display appears in color. If the output destination is something else, color display is not used.

When the ``-m`` option is given, it outputs the status display to standard error output.

The `-s` and `-t` options are for [compatibility purposes](compatibility.md) and are not used anymore.

The `-l` option was for extracting L6 messages from the first QZSS satellite, which is not available now.
