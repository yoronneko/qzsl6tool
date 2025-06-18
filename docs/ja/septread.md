# septread.py

このプログラムは、Septentrioのmosaic-X受信機またはmosaic-CLAS受信機の生データから、

- みちびきL6メッセージ（``-l``オプション）
- Galileo E6Bメッセージ（HAS, ``-e``オプション）
- BeiDou B2bメッセージ（``-b``オプション）

を抽出するプログラムです。``--help``オプションで、受け付けるオプションを表示します。

```bash
$ septread.py --help
usage: septread.py [-h] [-e | -l | -b] [-c] [-m]

Septentrio message read, QZS L6 Tool ver.x.x.x

options:
  -h, --help     show this help message and exit
  -e, --e6b      send E6B messages to stdout, and also turns off display message.
  -l, --l6       send QZS L6 messages to stdout (it also turns off Septentrio messages).
  -b, --b2b      send BDS B2b messages to stdout, and also turns off display message.
  -c, --color    apply ANSI color escape sequences even for non-terminal.
  -m, --message  show display messages to stderr
```

``-c``オプションを与えると、強制的にカラーにて状態表示します。デフォルトでは、出力先がターミナルであれば、状態表示はカラーにて表示されます。出力先がそれ以外であれば、カラー表示されません。

``-m``オプションを与えると、状態表示を標準エラー出力に出力します。
