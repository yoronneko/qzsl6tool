# bdsb2read.py

このプログラムは、BeiDou PPP-B2b生データを標準入力から読み取り、その内容を標準出力に出力します。

``--help``オプションで、受け付けるオプションを表示します。

```bash
$ bdsb2read.py --help
usage: bdsb2read.py [-h] [-c] [-m] [-p PRN] [-s] [-t TRACE]

BeiDou B2b message read

options:
  -h, --help            show this help message and exit
  -c, --color           apply ANSI color escape sequences even for non-terminal.
  -m, --message         show display messages to stderr
  -p PRN, --prn PRN     show B2b message for specified PRN only.
  -s, --statistics      show B2b statistics in display messages.
  -t TRACE, --trace TRACE show display verbosely: 1=detail, 2=bit image.
```

``-c``オプションを与えると、強制的にカラーにて状態表示します。デフォルトでは、出力先がターミナルであれば、状態表示はカラーにて表示されます。出力先がそれ以外であれば、カラー表示されません。

``-m``オプションを与えると、状態表示を標準エラー出力に出力します。

``-p``オプションを与えると、指定したPRNの衛星を用います。

``-s``オプションを与えると、メッセージの統計情報も出力されます。

``-t``オプションを与えると、メッセージ内容の詳細が表示されます。このオプションは整数値とともに用います。数値1では詳細を、数値2ではそれに加えて、ビットイメージを表示します。

例えば、サンプルディレクトリにあるSeptentrio mosaic-X5受信機生データ``20230819-081730hasbds.sept``を[septread.py](septread.md)にてB2b生データを抽出し、``bdsb2read.py``にて内容表示します。

```bash
$ septread.py -b < sample/20230819-081730hasbds.sept | bdsb2read.py -p 60 -t 1

C60 MT4  CLOCK 08:17:28 IODSSR=1 IODP=2 IODSSR mismatch
C60 MT4  CLOCK 08:17:28 IODSSR=1 IODP=2 IODSSR mismatch
C60 MT63 NULL
C60 MT63 NULL
C60 MT1  MASK  08:17:34 IODSSR=1 IODP=2 (updated)
 C19 C20 C21 C22 C23 C24 C25 C26 C27 C28 C29 C30 C32 C33 C34 C35 C36 C37 C38 C39 C40 C41 C42 C43 C44 C45 C46 G01 G02 G03 G04 G05 G06 G07 G08 G09 G10 G11 G12 G13 G14 G15 G16 G17 G18 G19 G20 G21 G22 G23 G24 G25 G26 G27 G28 G29 G30 G31 G32
C60 MT4  CLOCK 08:17:34 IODSSR=1 IODP=2
SAT IODCorr clock[m]
C19       4    0.483
C20       4   -0.035
C23       6   -0.050
C60 MT4  CLOCK 08:17:34 IODSSR=1 IODP=2
SAT IODCorr clock[m]
C24       6   -0.178
C26       4    0.000
C35       2    1.682
C37       3   -0.920
C39       2    0.339
C42       1    0.578
C45       0    0.443
C60 MT4  CLOCK 08:17:34 IODSSR=1 IODP=2
SAT IODCorr clock[m]
G01       0    0.000
G02       0    0.000
G03       0    0.000
G04       0    0.000
G05       0    0.000
G06       0    0.000
C60 MT3  CODE  08:17:27 IODSSR=1 numsat=3
SAT Signal Code   Code Bias[m]
C21 B1I                  3.383
C21 B1C(D)               4.369
C21 B1C(P)               4.539
C21 B2a(D)              -3.145
C21 B2a(P)              -2.091
C21 B2b-I               -1.887
C21 B2b-Q               -1.632
C21 B3 I                 0.000
C22 B1I                  4.097
C22 B1C(D)               5.168
C22 B1C(P)               5.219
C22 B2a(D)              -4.131
C22 B2a(P)              -3.281
C22 B2b-I               -2.856
C22 B2b-Q               -2.329
C22 B3 I                 0.000
C26 B1I                 -1.547
C26 B1C(D)              -0.136
C26 B1C(P)              -0.051
C26 B2a(D)              -5.814
C26 B2a(P)              -4.998
C26 B2b-I               -4.641
C26 B2b-Q               -4.080
C26 B3 I                 0.000
...
```
