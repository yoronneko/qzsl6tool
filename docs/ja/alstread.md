# alstread.py

このプログラムは、Allystar HD9310オプションC受信機の生データを標準入力から読み取り、標準出力にその状態を表示します。

状態表示の各行において、1列目はPRN番号を、2列目と3列目はGPS週番号と秒を、4列目はC/No [dB Hz]を、5列目はエラーがあればその内容を、それぞれ表します。``--help``オプションで、受け付けるオプションを表示します。

```bash
$ alstread.py --help
usage: alstread.py [-h] [-c] [-l] [-m] [-p PRN]

Allystar HD9310 message read, QZS L6 Tool ver.x.x.x

options:
  -h, --help         show this help message and exit
  -c, --color        apply ANSI color escape sequences even for non-terminal.
  -l, --l6           send QZS L6 messages to stdout (it also turns off status display).
  -m, --message      show status display to stderr.
  -p PRN, --prn PRN  satellite PRN to be specified (0, 193-211); with -l, CLAS Transmit Pattern 2 messages of this satellite are also output.
```

``-c``オプションを与えると、強制的にカラーにて状態表示します。デフォルトでは、出力先がターミナルであれば、状態表示はカラーにて表示されます。出力先がそれ以外であれば、カラー表示されません。

``-l``オプションを与えると、状態表示の代わりに、みちびきL6メッセージを標準出力に出力します。これは、受信できる複数のみちびき衛星のうちで最も信号強度の高い衛星を選択して、出力します。CLAS（Vendor ID 101）については、マルチストリーム伝送のCLAS Transmit Pattern 1と2（IS-QZSS-L6-008 Table 4.1.2-2のパターンIDビットが0と1）のうち、Pattern 1のメッセージのみを出力します。Pattern 2のメッセージは、状態表示に``(skipped CLAS Pattern 2)``と表示して出力しません。Pattern 1とPattern 2は補強対象衛星の組み合わせが異なる独立したCompact SSRストリームであり、混在させると``qzsl6read.py``で正しく復号できないためです。

``-m``オプションを与えると、状態表示を標準エラー出力に出力します。このオプションは、``-l``オプションとともに用います。

``-p``オプションを与えると、信号強度が最も高い衛星の代わりに、指定したPRNの衛星を用います。このオプションは、``-l``オプションとともに用います。指定した衛星がCLAS Pattern 2を送信している場合（例えば``-p 194``）には、そのPattern 2のメッセージを出力します。この出力を``qzsl6read.py``で復号するには、``qzsl6read.py``に``-P 2``オプションを与えてください。
