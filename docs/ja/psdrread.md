# psdrread.py

このプログラムは、ソフトウェア無線[Pocket SDR](https://github.com/tomojitakasu/PocketSDR)のログファイルから、

- みちびきL6メッセージ（``-l``オプション）
- Galileo E6Bメッセージ（HAS, ``-e``オプション）
- Galileo E1B I/NAVメッセージ（``-i``オプション）
- BeiDou B2bメッセージ（``-b``オプション）

を抽出するプログラムです。``--help``オプションで、受け付けるオプションを表示します。

```bash
$ psdrread.py --help
usage: psdrread.py [-h] [-c] [-b] [-i] [-e] [-l] [-m] [-s] [-t TRACE]

Pocket SDR message read

options:
  -h, --help   show this help message and exit
  -c, --color  apply ANSI color escape sequences even for non-terminal.
  -b, --b2b    send BDS B2b messages to stdout, and also turns off display message.
  -i, --inav   send GAL I/NAV messages to stdout, and also turns off display message.
  -e, --e6b    send GAL E6B messages to stdout, and also turns off display message.
  -l, --l6     send QZS L6 messages to stdout, and also turns off display message.
```

``-c``オプションを与えると、強制的にカラーにて状態表示します。デフォルトでは、出力先がターミナルであれば、状態表示はカラーにて表示されます。出力先がそれ以外であれば、カラー表示されません。

``-m``オプションを与えると、状態表示を標準エラー出力に出力します。

参考：[PocketSDRすごい（L6信号デコード編）](https://s-taka.org/awesome-pocketsdr-l6/#l6e)
