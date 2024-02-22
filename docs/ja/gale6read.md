## gale6read.py

Galileo HAS (high accuracy service) の生データを標準入力から読み取り、その内容を標準出力に出力します。

この入力は、1バイトのPRNと、62バイト（HAS生データの492ビット）からなります。

``--help``オプションで、受け付けるオプションを表示します。

```
$ gale6read.py --help
usage: gale6read.py [-h] [-c] [-m] [-r] [-s] [-t TRACE]

Galileo E6B message read

options:
  -h, --help            show this help message and exit
  -c, --color           apply ANSI color escape sequences even for non-terminal.
  -m, --message         show display messages to stderr
  -r, --rtcm            send RTCM messages to stdout (not implemented yet, it also turns off display messages unless -m is specified).
  -s, --statistics      show HAS statistics in display messages.
  -t TRACE, --trace TRACE show display verbosely: 1=detail, 2=bit image.
```

``-c``オプションを与えると、強制的にカラーにて状態表示します。デフォルトでは、出力先がターミナルであれば、状態表示はカラーにて表示されます。出力先がそれ以外であれば、カラー表示されません。

``-m``オプションを与えると、状態表示を標準エラー出力に出力します。

``-s``オプションを与えると、メッセージの統計情報も出力されます。

``-t``オプションを与えると、メッセージ内容の詳細が表示されます。このオプションは整数値とともに用います。数値1では詳細を、数値2ではそれに加えて、ビットイメージを表示します。

例えば、サンプルディレクトリにあるPocket SDRログファイル``20230305-063900has.psdr``を[psdrread.py](psdrread.md)にてHAS生データを抽出し、``gale6read.py``にて内容表示します。

```
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

参考: [Galileo HAS（high accuracy service）その2](https://s-taka.org/galileo-has-part2/), [QZS L6 ToolのHASメッセージ対応](https://s-taka.org/qzsl6tool-20230305upd/)

