## rtcmread.py

このプログラムは、RTCM（Radio Technical Commission for Maritime Services）メッセージを標準入力から読み取り、その内容を標準出力に出力します。

``--help``オプションを与えると、受け付けるオプションを表示できます。

```
usage: rtcmread.py [-h] [-c] [-t TRACE]

RTCM message read

options:
  -h, --help            show this help message and exit
  -c, --color           apply ANSI color escape sequences even for non-
                        terminal.
  -t TRACE, --trace TRACE
                        show display verbosely: 1=subtype detail, 2=subtype
                        and bit image.
```

端末出力に対しては、ANSIエスケープ・シーケンスによりカラー表示します。端末出力のリダイレクトを行うと、エスケープ・シーケンスを出力しません。リダイレクトを利用すれば、カラー表示をオフにできます（``rtcmread.py < rtcm_file.rtcm | cat``）。一方、``less``や``lv``などのページャー上でカラー表示するためには、``-c``オプションを利用します（``rtcmread.py -c < rtcm_file.rtcm | lv``）。

``-c``オプションを与えると、強制的にカラーにて状態表示します。デフォルトでは、出力先がターミナルであれば、状態表示はカラーにて表示されます。出力先がそれ以外であれば、カラー表示されません。

``-t``オプションを与えると、メッセージ内容の詳細が表示されます。このオプションは整数値とともに用います。数値1では詳細を、数値2ではそれに加えて、ビットイメージを表示します。

RTKLIBの``str2str``を利用すると、リアルタイムストリームなども利用できます。
```
str2str -in ntrip://ntrip.phys.info.hiroshima-cu.ac.jp:80/OEM7 2> /dev/null | rtcmread.py
```

例えば、サンプルディレクトリにあるRTCMデータ``20220326-231200clas.alst``を``rtcmread.py``にて内容表示します。

```
rtcmread.py < sample/20221213-010900.rtcm

RTCM 1087 R MSM7          R01 R02 R03 R11 R12 R13 R17 R18 R19
RTCM 1097 E MSM7          E02 E03 E05 E08 E13 E15 E24 E25 E34
RTCM 1117 J MSM7          J02 J03 J04
RTCM 1127 C MSM7          C02 C05 C06 C16 C19 C20 C36 C38 C39 C46
RTCM 1127 C MSM7          C01 C03 C04 C08 C09 C13 C22 C35 C37 C60
RTCM 1127 C MSM7          C59
RTCM 1137 I MSM7          I01 I03 I04 I05 I07 I09
RTCM 1005   Position      34.4401061 132.4147804 233.362
RTCM 1033   Ant Rcv info  JAVGRANT_G5T NONE s/n 0 rcv "NOV OEM729" ver OM7MR0810
RN0000
```

また、SSR（状態空間表現, state space representation）も表示可能です。かつて、JAXAがインターネット配信していたRTCM形式のMADOCAは次のように表示できます。

```
RTCM 1057 G SSR orbit     G01 G02 G03 G05 G06 G07 G08 G09 G10 G12 G13 G15 G16 G17 G19 G20 G21 G22 G24 G25 G26 G27 G28 G29 G30 G31 G32 (nsat=27 iod=3)
RTCM 1063 R SSR orbit     R01 R02 R03 R04 R05 R07 R08 R12 R13 R14 R15 R16 R17 R18 R19 R21 R22 R24 (nsat=18 iod=3)
RTCM 1058 G SSR clock     G01 G02 G03 G05 G06 G07 G08 G09 G10 G12 G13 G15 G16 G17 G19 G20 G21 G22 G24 G25 G26 G27 G28 G29 G30 G31 G32 (nsat=27 iod=3)
RTCM 1064 R SSR clock     R01 R02 R03 R04 R05 R07 R08 R12 R13 R14 R15 R16 R17 R18 R19 R21 R22 R24 (nsat=18 iod=3)
```

``rtcmread.py``に``-t 2``オプションを与えると、SSRの詳細が表示されます。

```
G01 d_radial= 0.5433m d_along=-0.9076m d_cross=-0.0215m dot_d_radial=-0.0000m/s
dot_d_along= 0.0000m/s dot_d_cross=-0.0001m/s
G02 d_radial= 0.6324m d_along= 1.6912m d_cross=-0.1118m dot_d_radial=-0.0003m/s
dot_d_along= 0.0001m/s dot_d_cross=-0.0001m/s
G03 d_radial= 0.6558m d_along= 0.7412m d_cross=-0.0547m dot_d_radial=-0.0003m/s
dot_d_along=-0.0000m/s dot_d_cross=-0.0002m/s
G05 d_radial= 0.6480m d_along= 1.0068m d_cross= 0.0016m dot_d_radial=-0.0002m/s
dot_d_along= 0.0002m/s dot_d_cross= 0.0001m/s
G06 d_radial= 0.3876m d_along=-0.3432m d_cross=-0.0224m dot_d_radial=-0.0000m/s
dot_d_along=-0.0002m/s dot_d_cross=-0.0001m/s
...
G01 c0= -0.051m, c1=  0.000m, c2=  0.000m
G02 c0= -0.399m, c1=  0.000m, c2=  0.000m
G03 c0= -0.226m, c1=  0.000m, c2=  0.000m
G05 c0= -0.255m, c1=  0.000m, c2=  0.000m
G06 c0= -0.255m, c1=  0.000m, c2=  0.000m
...
G01 L1 C/A        code_bias=  0.340m
G01 L5 I          code_bias= -2.090m
G02 L1 C/A        code_bias= -0.500m
G02 L5 I          code_bias=  2.330m
G03 L1 C/A        code_bias=  0.430m
G03 L5 I          code_bias= -1.480m
G05 L1 C/A        code_bias=  0.260m
G05 L5 I          code_bias=  1.060m
G06 L1 C/A        code_bias=  0.420m
G06 L5 I          code_bias= -1.900m
...
```
