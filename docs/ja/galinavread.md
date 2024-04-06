# galinavread.py

このプログラムは、Galileo I/NAV生データを標準入力から読み取り、その内容を標準出力に出力します。

``--help``オプションで、受け付けるオプションを表示します。

```bash
$ galinavread.py --help
usage: galinavread.py [-h] [-c]

Galileo I/NAV message read

options:
  -h, --help   show this help message and exit
  -c, --color  apply ANSI color escape sequences even for non-terminal.
```

``-c``オプションを与えると、強制的にカラーにて状態表示します。デフォルトでは、出力先がターミナルであれば、状態表示はカラーにて表示されます。出力先がそれ以外であれば、カラー表示されません。

例えば、サンプルディレクトリにあるu-blox ZED-F9P受信機生データ``20230919-114418.ubx``を[ubxread.py](ubxread.md)にてI/NAV生データを抽出し、``galinavread.py``にて内容表示します。

```bash
$ ubxread.py -i < 20230919-114418.ubx| galinavread.py
E05 SSP2 Word 10 (09)
E09 SSP2 Word 10 (09)
E24 SSP2 Word 10 (09)
E25 SSP2 Word 10 (09)
E18      Word 10
E02 SSP2 Word 10 (09)
E03 SSP2 Word 10 (09)
E05 SSP3 Word 18 (11)
E09 SSP3 Word 18 (11)
E24 SSP3 Word 18 (11)
E25 SSP3 Word 18 (11)
E18      Word  0       2023-09-19 11:44:28 (1256 215081)
E02 SSP3 Word 18 (11)
E03 SSP3 Word 18 (11)
E18      Word  0       2023-09-19 11:44:30 (1256 215083)
E02 SSP1 Word 20 (13)
E03 SSP1 Word 20 (13)
E05 SSP1 Word 20 (13)
E09 SSP1 Word 20 (13)
E24 SSP1 Word 20 (13)
E25 SSP1 Word 20 (13)
E05 SSP2 Word 16 (15)
E09 SSP2 Word 16 (15)
E24 SSP2 Word 16 (15)
E25 SSP2 Word 16 (15)
E18      Word  0       2023-09-19 11:44:32 (1256 215085)
E02 SSP2 Word 16 (15)
E03 SSP2 Word 16 (15)
...
```

この出力は、衛星番号（例えばE05）、SSP（secondary synchronization pattern）番号（1から3までを繰り返す）、ワード番号、SSP番号とワード番号から推定した30秒周期内の時刻、からなります。

古い衛星（例えばE18）にはSSP番号が表示されません。Galileo衛星の打ち上げ日は[みちびきホームページ](https://qzss.go.jp/en/technical/satellites/index.html#Galileo)にて確認できます。
