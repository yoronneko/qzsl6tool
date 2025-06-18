# novread.py

このプログラムは、NovAtel OEM729受信機の生データファイルから、Galileo E6Bメッセージ（HAS, ``-e``オプション）を抽出するプログラムです。``--help``オプションで、受け付けるオプションを表示します。

```bash
$ novread.py --help
usage: novread.py [-h] [-e | -q] [-c] [-m]

NovAtel message read, QZS L6 Tool ver.x.x.x

options:
  -h, --help     show this help message and exit
  -e, --e6b      send E6B C/NAV messages to stdout, and also turns off display message.
  -q, --qlnav    send QZSS LNAV messages to stdout, and also turns off display message.
  -c, --color    apply ANSI color escape sequences even for non-terminal.
  -m, --message  show display messages to stderr
```

``-c``オプションを与えると、強制的にカラーにて状態表示します。デフォルトでは、出力先がターミナルであれば、状態表示はカラーにて表示されます。出力先がそれ以外であれば、カラー表示されません。

``-m``オプションを与えると、状態表示を標準エラー出力に出力します。
