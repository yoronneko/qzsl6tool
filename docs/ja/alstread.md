## alstread.py

このプログラムは、Allystar HD9310オプションC受信機の生データを標準入力から読み取り、標準出力にその状態を表示します。

状態表示の各行において、1列目はPRN番号を、2列目と3列目はGPS週番号と秒を、4列目はC/No [dB Hz]を、5列目はエラーがあればその内容を、それぞれ表します。``--help``オプションで、受け付けるオプションを表示します。

```bash
$ alstread.py --help
usage: alstread.py [-h] [-c] [-l] [-m] [-p PRN]

Allystar HD9310 message read

options:
  -h, --help         show this help message and exit
  -c, --color        apply ANSI color escape sequences even for non-terminal.
  -l, --l6           send QZS L6 messages to stdout (it also turns off Allystar and u-blox messages).
  -m, --message      show Allystar messages to stderr.
  -p PRN, --prn PRN  satellite PRN to be specified.
```

``-c``オプションを与えると、強制的にカラーにて状態表示します。デフォルトでは、出力先がターミナルであれば、状態表示はカラーにて表示されます。出力先がそれ以外であれば、カラー表示されません。

``-l``オプションを与えると、状態表示の代わりに、みちびきL6メッセージを標準出力に出力します。これは、受信できる複数のみちびき衛星のうちで最も信号強度の高い衛星を選択して、出力します。

``-m``オプションを与えると、状態表示を標準エラー出力に出力します。このオプションは、``-l``オプションとともに用います。

``-p``オプションを与えると、信号強度が最も高い衛星の代わりに、指定したPRNの衛星を用います。このオプションは、``-l``オプションとともに用います。
