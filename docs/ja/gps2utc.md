## gps2utc.py

GPS時刻、GST（Galileo Standard Time）、BDT（BeiDou Standard Time）をUTC時刻に変換します。週と秒を与えると、それぞれの時刻を出力します。

```
$ gps2utc.py
GNSS time to UTC conversion
Usage: /Users/sat/bin/gps2utc.py week_no time_of_week
```

週番号（WN: week number）が2238、週初めからの秒数（TOW: time of week）が305575のときの実行例は次のとおりです。

```
$ gps2utc.py 2238 305575
GPS 2022-11-30 12:52:37
GST 2042-07-16 12:52:42
BDT 2048-11-25 12:52:51
```

この結果は、

- GPS時刻では、2022-11-30 12:52:37、
- GSTでは、2042-07-16 12:52:42、
- BSTでは、2048-11-25 12:52:51

であることを表しています。
