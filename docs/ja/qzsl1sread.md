# qzsl1sread.py

このプログラムは、みちびきL1S形式データ、およびSBAS（satellite based augmentation system）L1C/A形式データを標準入力またはファイルから読み取り、その内容を標準出力に出力します。両者は同じ250ビットのメッセージ構造（プリアンブル8ビット、メッセージタイプ6ビット、データフィールド212ビット、CRC24ビット）を持つため、ひとつのプログラムで扱います。

このプログラムが解読するメッセージタイプ（MT）は次のとおりです。

| MT | 内容 | 種別 |
|:--:|:--|:--:|
| 0 | テストモード | L1S / SBAS |
| 1 | SBAS PRNマスク | SBAS |
| 2-5 | 高速補正（fast corrections）1-4 | SBAS |
| 6 | インテグリティ情報 | SBAS |
| 7 | 高速補正劣化係数 | SBAS |
| 9 | GEO測距機能パラメータ | SBAS |
| 10 | 劣化係数 | SBAS |
| 12 | SBASネットワーク時刻/UTCオフセットパラメータ | SBAS |
| 17 | GEO衛星アルマナック | SBAS |
| 18 | 電離層グリッドポイント（IGP）マスク | SBAS |
| 20 | SBAS L1認証メッセージ | SBAS |
| 21 | SBAS無線鍵更新（OTAR: over the air rekeying） | SBAS |
| 24 | 高速/長期衛星補正混合 | SBAS |
| 25 | 長期衛星誤差補正 | SBAS |
| 26 | 電離層遅延補正 | SBAS |
| 28 | 時計・軌道共分散行列 | SBAS |
| 43 | 災害・危機管理通報（DCR: disaster and crisis management report） | L1S |
| 44 | 拡張災害・危機管理通報（DCX: DC report extended） | L1S |
| 47 | 監視局情報 | L1S |
| 48 | PRNマスク | L1S |
| 49 | データ発行番号 | L1S |
| 50 | DGPS補正 | L1S |
| 51 | 衛星ヘルス | L1S |
| 63 | ヌルメッセージ | L1S / SBAS |

MT20とMT21は、ICAO SARPsのドラフト（変更される可能性があります）に基づいています。

``--help``オプションで、受け付けるオプションを表示します。

```bash
$ qzsl1sread.py --help
usage: qzsl1sread.py [-h] [-c] [-t TRACE] [--jp] [file ...]

Quasi-zenith satellite (QZS) L1S message read, QZS L6 Tool ver.x.x.x

positional arguments:
  file                  L1S file(s) obtained from the QZS archive, https://sys.qzss.go.jp/dod/archives/slas.html

options:
  -h, --help            show this help message and exit
  -c, --color           apply ANSI color escape sequences even for non-terminal.
  -t TRACE, --trace TRACE
                        show display verbosely: 1=subtype detail, 2=subtype and bit image.
  --jp                  show DCR (disaster and crisis management report) in Japanese.
```

## 入力形式

ファイル名が与えられた場合、入力形式は、みちびき公式ページの[SLASアーカイブ](https://sys.qzss.go.jp/dod/en/archives/slas.html)と同様です。最初に1バイト（8ビット）のPRN（pseudo random noise）番号があり、その後に、GPS週番号（12ビット）、GPS週秒（20ビット）、L1Sメッセージ（250ビット）、パディング（6ビット）からなる36バイトのレコードが続きます。

ファイル名が与えられなければ、標準入力から読み取ります。この場合の入力形式は、PRN番号（8ビット）、L1SまたはSBASメッセージ（250ビット）、パディング（6ビット）からなる33バイトのレコードの繰り返しです。[ubxread.py](ubxread.md)の``--l1s``オプションの出力がこの形式です。サンプルディレクトリの``.l1s``ファイルおよび``.sbas``ファイル（``20230919-114418.l1s``を除く）も、この標準入力形式です。

## 表示

出力の各行は、PRN番号、メッセージタイプ番号（``MT``）、メッセージ名の順に表示されます。補正メッセージがマスクメッセージ（SBASではMT1のPRNマスクとMT18のIGPマスク、L1SではMT48のPRNマスク）より前に受信された場合、``(waiting for PRN mask, MT1)``のように、マスク待ちであることを表示します。

端末出力に対しては、ANSIエスケープ・シーケンスによりカラー表示します。端末出力のリダイレクトを行うと、エスケープ・シーケンスを出力しません。リダイレクトを利用すれば、カラー表示をオフにできます（``qzsl1sread.py < qzss_file.l1s | cat``）。一方、``less``や``lv``などのページャー上でカラー表示するためには、``-c``オプションを利用します（``qzsl1sread.py -c < qzss_file.l1s | lv``）。

``-c``オプションを与えると、強制的にカラーにて状態表示します。デフォルトでは、出力先がターミナルであれば、状態表示はカラーにて表示されます。出力先がそれ以外であれば、カラー表示されません。

``-t``オプションを与えると、メッセージ内容の詳細が表示されます。このオプションは整数値とともに用います。数値1では詳細を、数値2ではそれに加えて、ビットイメージを表示します。

``--jp``オプションを与えると、災害・危機管理通報（DCR）を日本語で表示します。デフォルトでは英語表示です。

## みちびきL1S復号例

サンプルディレクトリにあるu-blox ZED-F9P受信機生データファイル``20230919-114418.ubx``を[ubxread.py](ubxread.md)にてL1S生データを抽出し、``qzsl1sread.py``にて内容表示します。

```bash
$ ubxread.py --l1s < sample/20230919-114418.ubx | qzsl1sread.py -t 2

PRN137:MT25: Long-term satellite error corrections (waiting for PRN mask, MT1)
PRN186:MT50: DGPS correction (waiting for PRN mask, MT48)
PRN128:MT03: Fast corrections 2 (waiting for PRN mask, MT1)
PRN184:MT50: DGPS correction (waiting for PRN mask, MT48)
PRN137:MT10: Degradation factors
PRN186:MT43: DCR: Marine (Normal) 09-19 08:40 UTC
PRN128:MT02: Fast corrections 1 (waiting for PRN mask, MT1)
PRN184:MT43: DCR: Marine (Normal) 09-19 08:40 UTC
...
PRN186:MT48: PRN mask: selected sats: G03 G04 G16 G18 G25 G26 G27 G28 G29 G31 G32 J02 J03 J04 J07 (15 sats, IODP=2)
...
PRN186:MT49: Data issue number: IODI=3 IODP=2
PRN IOD
G03 100
G04 184
G16   4
G18  50
G25  18
G26  20
G27   8
G28 112
G29  47
G31  27
G32 115
J02  13
J03  13
J04  13
J07  13
 (15 sats)
...
PRN186:MT50: DGPS correction: Sapporo
PRN PRC[m]
G16  -3.08
G26   1.28
G28   2.40
G29   1.36
G31   3.08
G32  -3.28
J02   3.56
J04  -4.00
J07  -1.28
 (9 sats)
```

この例では、みちびきのL1S信号（PRN 184、186）と、SBAS信号（GAGANのPRN 128、みちびきSBASのPRN 137）が混在しています。``ubxread.py``の``-p``オプションで衛星を指定すると、特定の衛星のメッセージだけを取り出せます。

データの読み方は次のページをご参照ください：[QZS L6 ToolのみちびきL1S信号対応](https://s-taka.org/qzsl6tool-20231111upd/)

## 災害・危機管理通報（DCR、DCX）復号例

サンプルディレクトリにあるみちびき3号機（PRN 189）のL1Sデータ``20260901-040000.l1s``を内容表示します。

```bash
$ qzsl1sread.py < sample/20260901-040000.l1s

PRN189:MT50: DGPS correction (waiting for PRN mask, MT48)
PRN189:MT43: DCR: Typhoon (Normal) 09-01 03:45 UTC
PRN189:MT48: PRN mask: selected sats: G05 G10 G12 G14 G15 G18 G20 G21 G22 G23 G24 G29 J02 J03 J07 (15 sats, IODP=2)
PRN189:MT44: DCX (NULL message)
PRN189:MT49: Data issue number: IODI=2 IODP=2 (15 sats)
PRN189:MT43: DCR: Marine (Normal) 09-01 02:35 UTC
PRN189:MT50: DGPS correction: Sapporo (8 sats)
...
```

``--jp``オプションを与えると、DCRを日本語で表示します。

```bash
$ qzsl1sread.py --jp < sample/20260901-040000.l1s

PRN189:MT43: DCR: 台風 (通常) 09-01 03:45 UTC
PRN189:MT43: DCR: 海上 (通常) 09-01 02:35 UTC
...
```

DCX（MT44）は、IS-QZSS-DCX-004に基づく拡張災害・危機管理通報で、海外向けの通報を含みます。``-t 1``以上で内容を表示します。通常時のDCXはヌルメッセージ（``DCX (NULL message)``）ですが、月に2回（第1週火曜午後と第3週木曜午前、JST）、[試験データの配信](https://qzss.go.jp/technical/dod/dc-report/dcx-test-data-distribution.html)があります。このサンプルは2026年9月1日13:00 JST（04:00 UTC）からの試験配信中のもので、メッセージタイプが``Test``の通報を含みます。

```bash
$ qzsl1sread.py -t 1 < sample/20260901-040000.l1s

...
PRN189:MT44: DCX: Test CBRNE - Air strike (Unknown)
Japan, FMMC (L-Alert)
onset: this week Tue 04:00 UTC, duration 12-24h
library: country/region #1
instruction: ""
target area code: 01101
...
```

試験配信の1時間分は、次のように表示できます（配信内容は上記ページ内の資料を参照）。

```bash
curl https://rnav.info.hiroshima-cu.ac.jp/gnss/f9p/202609/20260901e.ubx | ubxread.py --l1s -p 189 | qzsl1sread.py -t 1
```

海外向け通報など、より多くの種類の例として、サンプルディレクトリの合成データ``synthetic-dcx.l1s``を示します。これは実際の放送ではなく、IS-QZSS-DCX-004の計算例などをもとに``sample/make_synthetic_dcx.py``で作成したビットパターンです。

```bash
$ qzsl1sread.py -t 1 < sample/synthetic-dcx.l1s

PRN186:MT44: DCX (NULL message)
PRN186:MT44: DCX: Alert GEO - Tsunami (Extreme)
Japan, FMMC (L-Alert)
onset: this week Tue 09:30 UTC, duration <6h
library: country/region #1
instruction: "Move to/toward 3rd floor or higher."
ellipse: centre 35.688 139.691, semi-major 10.933[km], semi-minor 4.421[km], azimuth 45.00[deg]
target area code: 01100
PRN186:MT44: DCX: Alert CBRNE - Air strike (Extreme)
Japan, FDMA (J-Alert)
onset: this week Tue 06:40 UTC, duration <6h
library: country/region #1
instruction: "Missile launched, missile launched. It is believed that a missile was launched. Please take shelter inside buildings or underground."
target prefectures: Hokkaido Aomori Iwate
PRN186:MT44: DCX: Alert MET - Storm or thunderstorm (Severe)
Zambia, provider 1
onset: next week Mon 00:00 UTC, duration 12-24h
library: international #1
instruction: IC-A-04 "Seek shelter in a building immediately. Stay under cover and stay informed."
             IC-B-02 "Check with the weather services and local authorities for additional information"
ellipse: centre 0.001 0.001, semi-major 90.407[km], semi-minor 49.439[km], azimuth 0.00[deg]
hazard centre: 0.158 -9.999 (delta +0.15625 -10.00000[deg])
...
```

## SBAS復号例

サンプルディレクトリにあるGAGAN（インドのSBAS、PRN 128、GSAT-10）のSBASデータ``20260912-034300.sbas``を内容表示します。この``.sbas``ファイルは、u-blox ZED-F9P受信機の生データから``ubxread.py --l1s -p 128``で抽出したものです。

```bash
$ qzsl1sread.py -t 2 < sample/20260912-034300.sbas

...
PRN128:MT01: SBAS PRN mask
selected sats: G01 G02 G03 G04 G05 G06 G07 G08 G09 G10 G11 G12 G13 G14 G15 G16 G17 G18 G19 G20 G21 G22 G23 G24 G25 G26 G27 G28 G29 G30 G31 G32 S127 S128 S132 (35 sats, IODP=3)
...
PRN128:MT02: Fast corrections 1
SAT correction[m] (IODF=1), IODP=3
G01 :   -0.500, UDREI=7
G02 :   -0.125, UDREI=6
G03 :     VOID, UDREI=14
G04 :   -0.500, UDREI=5
...
PRN128:MT25: Long-term satellite error corrections
G03  IOD=62 daf0= 9.313e-09[s] daf1=-3.638e-12[s/s] ti=48624[s]
      dx= 0.000e+00[m]    dy=-3.500e+00[m]    dz=-2.625e+00[m]
     ddx= 0.000e+00[m/s] ddy=-4.883e-04[m/s] ddz= 4.883e-04[m/s]
...
PRN128:MT18: Ionospheric grid point masks
Total_IGP=3 IGP_band=5 IODI=3 IGP_mask_pattern=0 (5 IGPs)
IGP lat[deg] lon[deg]
193       15       55
194       20       55
...
PRN128:MT26: Ionospheric delay corrections
IGP_band=6 IGP_block=2 IODI=3 (15 IGPs)
IGP lat[deg] lon[deg] delay[m] GIVE[m]
 89       -5       75    3.000    15.0
 90        0       75    3.875     6.0
 91        5       75    4.875     6.0
...
PRN128:MT09: GEO ranging function parameters
  t0=48576[s] URA=15 a_Gf0=0.0[s] a_Gf1= 4.547e-12[s/s]
  Xg= 5.141e+03[km]       Yg= 4.185e+04[km]       Zg= 2.155e+01[km]
 dXg=-9.050e-01[m/s]     dYg= 1.975e-01[m/s]     dZg= 4.840e-01[m/s]
ddXg= 3.750e-05[m/s^2]  ddYg= 6.250e-05[m/s^2]  ddZg=-1.250e-04[m/s^2]
...
PRN128:MT17: GEO satellite almanacs
S127 data_ID=0 provider=GAGAN service: ranging corrections integrity
     Xg=  24107.2[km] Yg=  34567.0[km] Zg=    338.0[km] dXg=   0[m/s] dYg=   0[m/s] dZg= -81.92[m/s]
S128 data_ID=0 provider=GAGAN service: ranging corrections integrity
     Xg=   5140.2[km] Yg=  41847.0[km] Zg=     26.0[km] dXg=   0[m/s] dYg=   0[m/s] dZg=   0.00[m/s]
...
PRN128:MT28: Clock-ephemeris covariance matrix
G09  scale_exp=1 (SF=2^-4) E11=342 E22=277 E33=504 E44=16 E12=-32 E13=-12 E14=-73 E23=33 E24=-251 E34=108
     relative covariance matrix (x, y, z, clock):
      4.56891e+02 -4.27500e+01 -1.60312e+01 -9.75234e+01
     -4.27500e+01  3.03723e+02  3.72070e+01 -2.62465e+02
...
```

みちびきのSBAS信号（PRN 137、みちびき3号機）のデータ``20260914-045300.sbas``も同様に表示できます。

SBAS認証メッセージ（MT20、MT21）の例として、サンプルディレクトリの合成データ``synthetic-sbas-auth.sbas``を示します。これは実際の放送ではなく、ICAO SARPsのドラフト形式に従って``sample/make_synthetic_sbas_auth.py``で作成したビットパターンです。

```bash
$ qzsl1sread.py -t 1 < sample/synthetic-sbas-auth.sbas

PRN128:MT20: SBAS L1 authentication message
beMAC1=1111111 beMAC2=2222222 aMAC=3333333
TESLA hash point=000000000000000000000000deadbeef
PRN128:MT21: SBAS over the air rekeying (OTAR)
IODK_lvl3=3 page=0 level 3 key material, payload 1:
IODK_lvl2=5 MT20_slot=2 validity: start WN=2400 frame=1000, duration 2[week] + 50000[frame]
applicability=SBAS system technique=TESLA hash=SHA-256 valid IODK_lvl3: 0 2
TESLA confirmed hash point=0000000000000000000000000000cafe
...
```

## リアルタイムストリーム

[ubxread.py](ubxread.md)とRTKLIBの``str2str``を利用すると、リアルタイムストリームなども利用できます。

```bash
str2str -in ntrip://ntrip.phys.info.hiroshima-cu.ac.jp:80/F9PR 2> /dev/null | ubxread.py --l1s | qzsl1sread.py
```

## 参考文献

- 内閣府, サブメータ級測位補強サービス アーカイブ, https://sys.qzss.go.jp/dod/archives/slas.html
- 内閣府, みちびきインタフェース仕様書 災害・危機管理通報サービス, IS-QZSS-DCR-011, 2023年10月
- 内閣府, みちびきインタフェース仕様書 サブメータ級測位補強サービス, IS-QZSS-L1S-006, 2023年10月
- 内閣府, みちびきインタフェース仕様書 災害・危機管理通報サービス（拡張）, IS-QZSS-DCX-004, 2026年5月
- 電子航法研究所, SBAS/L1-SAIFメッセージ仕様, https://www.enri.go.jp/jp/research/organization/nav/program/message.html
- RTCA, Minimum operational performance standards for global positioning system/satellite-based augmentation system airborne equipment, DO-229D, 2006年12月
- K. Alexander, T. Walter, A. Neish, J. Anderson, "SBAS authentication standards," Proc. ION GNSS+ 2024, 2024年9月（ICAO SARPsドラフト、変更の可能性あり）
