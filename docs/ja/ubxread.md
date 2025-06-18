# ubxread.py

このプログラムは、u-blox ZED-F9P受信機の生データから、

- みちびきL1Sメッセージ（``--l1s``オプション）
- みちびきL1S NMEAメッセージ（``--qzqsm``オプション）
- SBAS（satellite based augmentation system）メッセージ（``--sbas``オプション）
- GPS/QZSS LNAVメッセージ（``-l``オプション）
- Galileo E1B I/NAVメッセージ（``-i``オプション）

を抽出するプログラムです。``--help``オプションで、受け付けるオプションを表示します。

```bash
$ ubxread.py --help
usage: ubxread.py [-h] [--l1s | --qzqsm | --sbas | -l | -i] [-d] [-c] [-m] [-p PRN]

u-blox message read, QZS L6 Tool ver.x.x.x

options:
  -h, --help         show this help message and exit
  --l1s              send QZS L1S messages to stdout
  --qzqsm            send QZS L1S DCR NMEA messages to stdout
  --sbas             send SBAS messages to stdout
  -l, --lnav         send GPS or QZS LNAV messages to stdout
  -i, --inav         send GAL I/NAV messages to stdout
  -d, --duplicate    allow duplicate QZS L1S DCR NMEA sentences (currently, all QZS sats send the same DCR messages)
  -c, --color        apply ANSI color escape sequences even for non-terminal.
  -m, --message      show display messages to stderr
  -p PRN, --prn PRN  specify satellite PRN (PRN=0 means all sats)
```

``-c``オプションを与えると、強制的にカラーにて状態表示します。デフォルトでは、出力先がターミナルであれば、状態表示はカラーにて表示されます。出力先がそれ以外であれば、カラー表示されません。

``-m``オプションを与えると、状態表示を標準エラー出力に出力します。

``-d``オプションを与えると、みちびきL1S災害・危機通報の重複したNMEAメッセージも出力します。現在、すべてのみちびき衛星は、同一のメッセージを送信しています。デフォルトでは、重複したメッセージを出力しません。

``-p``オプションを与えると、指定したPRNの衛星を用います。このオプションがなければ、すべての衛星を用います。
