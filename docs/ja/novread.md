## novread.py

このプログラムは、NovAtel OEM729受信機の生データファイルから、Galileo E6Bメッセージ（HAS, ``-e``オプション）を抽出するプログラムです。``--help``オプションで、受け付けるオプションを表示します。

```
$ novread.py --help
usage: novread.py [-h] [-c] [-e] [-l] [-m] [-s] [-t TRACE]

NovAtel message read

options:
  -h, --help            show this help message and exit
  -c, --color           apply ANSI color escape sequences even for non-terminal.
  -e, --e6b             send E6B C/NAV messages to stdout, and also turns off display message.
  -l, --l6              send L6 messages to stdout, and also turns off display message.
  -m, --message         show display messages to stderr
  -s, --statistics      show HAS statistics in display messages.
  -t TRACE, --trace TRACE show display verbosely: 1=detail, 2=bit image.
```

``-c``オプションを与えると、強制的にカラーにて状態表示します。デフォルトでは、出力先がターミナルであれば、状態表示はカラーにて表示されます。出力先がそれ以外であれば、カラー表示されません。

``-m``オプションを与えると、状態表示を標準エラー出力に出力します。

``-s``オプション、``-t``オプションは、[互換性のためのもので](compatibility.md)、現在は使用しません。

``-l``オプションは、現在、利用できない、みちびき初号機のL6メッセージを抽出するためのものでした。

