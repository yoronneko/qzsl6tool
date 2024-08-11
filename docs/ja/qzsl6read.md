# qzsl6read.py

このプログラムは、みちびきL6形式の生データを標準入力から読み取り、その内容を標準出力に出力します。

このプログラムは、L6形式の生データとして、

- CLAS（centimeter level augmentation service）
- MADOCA（multi-GNSS advanced demonstration tool for orbit and clock analysis）
- MADOCA-PPP（Multi-GNSS Advanced Orbit and Clock Augmentation - Precise Point Positioning）（Clock/EphemerisとIonosphere）

を扱えます。

MADOCAはRTCM（Radio Technical Commission for Maritime Services） SSR（状態空間表現, State Space Representation）形式、CLASとMADOCA-PPPはCSSR（Compact SSR）形式です。

``--help``オプションで、受け付けるオプションを表示します。

```bash
$ qzsl6read.py --help
usage: qzsl6read.py [-h] [-c] [-m] [-r] [-s] [-t TRACE]

Quasi-zenith satellite (QZS) L6 message read

options:
  -h, --help            show this help message and exit
  -c, --color           apply ANSI color escape sequences even for non-terminal.
  -m, --message         show display messages to stderr
  -r, --rtcm            send RTCM messages to stdout (it also turns off display messages unless -m is specified).
  -s, --statistics      show CSSR statistics in display messages.
  -t TRACE, --trace TRACE show display verbosely: 1=subtype detail, 2=subtype and bit image.
```

端末出力に対しては、ANSIエスケープ・シーケンスによりカラー表示します。端末出力のリダイレクトを行うと、エスケープ・シーケンスを出力しません。リダイレクトを利用すれば、カラー表示をオフにできます（``qzsl6read.py < qzss_file.l6 | cat``）。一方、``less``や``lv``などのページャー上でカラー表示するためには、``-c``オプションを利用します（``qzsl6read.py -c < qzss_file.l6 | lv``）。

``-c``オプションを与えると、強制的にカラーにて状態表示します。デフォルトでは、出力先がターミナルであれば、状態表示はカラーにて表示されます。出力先がそれ以外であれば、カラー表示されません。

``-m``オプションを与えると、状態表示を標準エラー出力に出力します。

``-r``オプションを与えると、メッセージ内容表示を抑制し、標準出力にRTCMメッセージを出力します。このとき、``-m``オプションも指定すると、標準出力にはRTCMメッセージを、標準エラー出力にはメッセージ内容表示を、それぞれ出力します。

``-s``オプションを与えると、メッセージの統計情報も出力されます。

``-t``オプションを与えると、メッセージ内容の詳細が表示されます。このオプションは整数値とともに用います。数値1では詳細を、数値2ではそれに加えて、ビットイメージを表示します。

RTKLIBの``str2str``を利用すると、リアルタイムストリームなども利用できます。
```bash
str2str -in ntrip://ntrip.phys.info.hiroshima-cu.ac.jp:80/CLAS 2> /dev/null | alstread.py -l | qzsl6read.py
```

### CLAS復号例

例えば、サンプルディレクトリにあるAllystar受信機生データ``20220326-231200clas.alst``を[alstead.py](alstread.md)にてみちびきL6生データを抽出し、``qzsl6read.py``にて内容表示します。

```bash
alstread.py -l < sample/20220326-231200clas.alst | qzsl6read.py

199 Hitachi-Ota:1  CLAS  (syncing)
199 Hitachi-Ota:1  CLAS  SF1 DP1 ST1 ST3 ST2 ST4...
199 Hitachi-Ota:1  CLAS  SF1 DP2 ST4 ST7 ST11 ST6 ST12...
199 Hitachi-Ota:1  CLAS  SF1 DP3 ST12 ST6 ST12...
199 Hitachi-Ota:1  CLAS  SF1 DP4 ST12
199 Hitachi-Ota:1  CLAS  SF1 DP5 (null)
199 Hitachi-Ota:1  CLAS  SF2 DP1 ST3 ST11 ST6 ST12...
199 Hitachi-Ota:1  CLAS  SF2 DP2 ST12...
199 Hitachi-Ota:1  CLAS  SF2 DP3 ST12 ST6...
199 Hitachi-Ota:1  CLAS  SF2 DP4 ST6 ST12...
199 Hitachi-Ota:1  CLAS  SF2 DP5 ST12
...
```

各行の最初の数値はPRN（pseudo random noise）番号、次のカラムは管制局（常陸太田または神戸）、次の数値（0または1）は送信系番号、その次のカラムはCLASメッセージであることを表します。``SF``はサブフレーム番号、``DP``はデータパート番号を表します。  

Subtype 1 (ST1) メッセージを受信すると、このプログラムはCLASメッセージ解読を開始します。

``...``は、次のデータパートにまでメッセージが続くことを示しています。例えば、上の例において、DP1には、ST1、ST3、ST2があり、さらにST4が次のデータパートに続くことを示します。DP2の先頭には``ST4``があり、これはDP1からの継続ST4メッセージです。

一方、``(null)``は、データパート全体が無情報（ヌル）であることを示します。

参考：[QZS L6 ToolのCLASメッセージ対応](https://s-taka.org/qzsl6tool-20220329upd/)

``qzsl6read.py``に``-t 2``オプションを与えると、その詳細が表示されます。

```bash
alstread.py -l < sample/20220326-231200clas.alst | qzsl6read.py -t 2

199 Hitachi-Ota:1  CLAS  (syncing)
...
ST1 G10 L1 C/A L2 CM+CL L2 Z-tracking L5 I+Q
ST1 G12 L1 C/A L2 CM+CL L2 Z-tracking
ST1 G22 L1 C/A L2 Z-tracking
...
ST3 G10 d_clock= -0.883m
ST3 G12 d_clock=  0.773m
ST3 G22 d_clock=  0.069m
...
ST2 G10 IODE=  10 d_radial= 0.0272m d_along= 0.2432m d_cross=-0.5952m
ST2 G12 IODE=  56 d_radial=-0.0704m d_along= 1.4912m d_cross= 0.0448m
ST2 G22 IODE=  35 d_radial=-0.0304m d_along=-1.3440m d_cross=-0.6464m
...
```

また、``-s``オプションを与えると、サブタイプ1を受信するたびに、統計情報を出力します。

```text
stat n_sat 17 n_sig 48 bit_sat 13050 bit_sig 5114 bit_other 1931 bit_null 5330 bit_total 25425
```

ここで、

- ``n_sat``は補強対象衛星数を、
- ``n_sig``は信号数を、
- ``bit_sat``は衛星に関する情報ビット数を、
- ``bit_sig``は信号に関する情報ビット数を、
- ``bit_other``は衛星にも信号にも関しない情報ビット数を、
- ``bit_null``は無情報（ヌル）ビット数を、
- ``bit_total``は全メッセージビット数を

それぞれ表します（参考：[みちびきアーカイブデータを用いたCLAS衛星補強情報の容量解析](https://s-taka.org/202206ipntj-clas-capacity/)）。

### MADOCA-PPP復号例

サンプルディレクトリにあるAllystar受信機生データ``20221130-125237mdc-ppp.alst``を内容表示します。

```bash
alstread.py -l < sample/20221130-125237mdc-ppp.alst | qzsl6read.py

205 Hitachi-Ota:1  MADOCA-PPP  (syncing)
205 Hitachi-Ota:1  QZNMA       (inactive) (inactive)
205 Hitachi-Ota:1  QZNMA       (inactive) (inactive)
205 Hitachi-Ota:1  MADOCA-PPP  (syncing)
205 Hitachi-Ota:1  MADOCA-PPP  (syncing)
205 Hitachi-Ota:1  MADOCA-PPP  (syncing)
205 Hitachi-Ota:1  MADOCA-PPP  SF1 DP1 (Clk/Eph LNAV) ST1 ST2...
205 Hitachi-Ota:1  MADOCA-PPP  SF1 DP2 (Clk/Eph LNAV) ST2...
205 Hitachi-Ota:1  MADOCA-PPP  SF1 DP3 (Clk/Eph LNAV) ST2 ST3
205 Hitachi-Ota:1  MADOCA-PPP  SF1 DP4 (Clk/Eph LNAV) (null)
...
```

CLASと同様、MADOCA-PPPにおいても、``qzsl6read.py``に``-t 2``オプションを与えると、詳細が表示されます（参考：[みちびきMADOCA-PPPの試験配信開始](https://s-taka.org/test-transmission-of-qzss-madoca-ppp/)）。

### MADOCA復号例

MADOCAメッセージ配信は終了しました。

サンプルディレクトリにあるAllystar受信機生データ``20220326-231200mdc.alst``を内容表示します。

```bash
alstread.py -l < sample/20220326-231200mdc.alst| qzsl6read.py

209 Hitachi-Ota:0* MADOCA 2022-03-26 23:11:44 RTCM 1062(26) RTCM 1068(17)
209 Hitachi-Ota:0* MADOCA 2022-03-26 23:11:44 RTCM 1057(8) RTCM 1061(8)
206 Hitachi-Ota:0* MADOCA 2022-03-26 23:11:46 RTCM 1062(26) RTCM 1068(17)
206 Hitachi-Ota:0* MADOCA 2022-03-26 23:11:46 RTCM 1057(8) RTCM 1061(8)
...
```

例えば1行目は、PRN 209（みちびき3号機）のもので、常陸太田管制局にある2系統の最初の設備から生成されたメッセージであり、アラートフラグオン（アスタリスク）、時刻、そして、RTCMメッセージタイプとその補強衛星数を表しています。

ここでは、含まれるRTCMメッセージ番号と、括弧書きで補強対象衛星数が表示されます。``qzsl6read.py``に``-t 2``オプションを与えると、補強内容を表示できます。

```bash
alstread.py -l < sample/20220326-231200mdc.alst| qzsl6read.py -t 2

G01 high_rate_clock=  0.430m
G02 high_rate_clock=  0.106m
G03 high_rate_clock= -0.745m
...
209 Hitachi-Ota:0* MADOCA 2022-03-26 23:11:44 RTCM 1062(26) RTCM 1068(17)
G10 d_radial= 0.0038m d_along= 0.6916m d_cross=-0.0513m dot_d_radial=-0.0002m/s
dot_d_along=-0.0005m/s dot_d_cross= 0.0001m/s
...
G10 ura=   3.50 mm
G12 ura=   3.50 mm
G13 ura=   3.50 mm
...
09 Hitachi-Ota:0* MADOCA 2022-03-26 23:11:44 RTCM 1057(8) RTCM 1061(8)
G01 high_rate_clock=  0.429m
G02 high_rate_clock=  0.107m
G03 high_rate_clock= -0.745m
...
```
