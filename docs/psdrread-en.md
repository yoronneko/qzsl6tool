## psdrread.py

This program reads the logfile of [Pocket SDR](https://github.com/tomojitakasu/PocketSDR), a software defined radio, and extracts

- QZS L6 messages (``-l`` option),
- Galileo E6B message (HAS, ``-e`` option),
- Galileo E1B I/NAV message (``-i`` option), and
- BeiDou B2b message (``-b`` option).

The ``--help`` option displays the options it accepts.

```
$ psdrread.py --help
usage: psdrread.py [-h] [-c] [-b] [-i] [-e] [-l] [-m] [-s] [-t TRACE]

Pocket SDR message read

options:
  -h, --help            show this help message and exit
  -c, --color           apply ANSI color escape sequences even for non-terminal.
  -b, --b2b             send BDS B2b messages to stdout, and also turns off display message.
  -i, --inav            send GAL I/NAV messages to stdout, and also turns off display message.
  -e, --e6b             send GAL E6B messages to stdout, and also turns off display message.
  -l, --l6              send QZS L6 messages to stdout, and also turns off display message.
  -m, --message         show display messages to stderr
  -s, --statistics      show HAS statistics in display messages.
  -t TRACE, --trace TRACE show display verbosely: 1=detail, 2=bit image.
```
When the ``-c`` option is given, it forces the status display to appear in color. By default, if the output destination is a terminal, the status display appears in color. If the output destination is something else, color display is not used.

When the ``-m`` option is given, it outputs the status display to standard error output.

When the ``-s`` option is given, it also outputs the statistics information.

When the ``-t`` option is given, it output detail on the messages. This option needs integer argument. The value 1 produces the detailed information, and the value 2 provides bit image display in addition of the detailed information.


Reference：[Awesome PocketSDR (L6 band signal decode)](https://s-taka.org/en/awesome-pocketsdr-l6/#l6e)

