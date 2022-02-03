# QZS L6 Tool: quasi-zenith satellite L6-band tool

https://github.com/yoronneko/qzsl6tool

## 概要

これは準天頂衛星みちびき（QZS: quasi-zenith satellite）のメッセージなどを表示・加工するツール集です。私が自らのために作成したツール集ですが、多くの方に役立つと思い、公開します。

Pythonの``bitstring``モジュールを利用しますので、あらかじめ``pip3 install bitstring``によりこのモジュールをインストールしてください。

## 機能

このツール集の主要なプログラムは、Allystar HD9310オプションCのL6信号の生データを解釈してみちびきL6帯ペイロードを抽出するプログラム（alst2qzssl6.py）、L6帯ペイロードからCLAS（centimeter level augmentation service）またはMADOCA（multi-GNSS advanced demonstration tool for orbit and clock analysis）の種別を読み出してRTCM（Radio Technical Commission for Maritime Services）形式のメッセージに変換するプログラム（qzsl62rtcm.py）です。ただし、現時点では、CLASメッセージからRTCMメッセージへの変換は未実装です。

このツールは、みちびきメッセージ等をパイプを用いてリアルタイム逐次的に処理することを意図しています。シリアルポートやTCP/IPストリームのAllystar HD9310オプションC生データやNTRIP（networked transport of RTCM via Internet protocol）を標準入力で受け取り、変換結果を標準出力に出力します。また、デバッグメッセージを標準エラー出力に出力します。したがって、不要なメッセージを``/dev/null``にリダイレクトしてご使用ください。また、ファイルから入力するときは``cat``コマンドなどをご利用ください。

また、MADOCAの状態空間表現（SSR: space state representation）を含むRTCMメッセージを表示するプログラム（showrtcm.py）、GPS時刻とUTC（universal coordinate time）とを相互変換するプログラム（gps2utc.py、utc2gps.py）、緯度・経度・楕円体高とECEF（earth-centered earth-fixed）座標とを相互変換するプログラム（llh2ecef.py、ecef2llh.py）を含みます。

## プログラム説明

### alst2qzsl6.py

Allystar HD9310オプションCの生データを標準入力から受け取り、追尾する複数のみちびき衛星の生データを復号して、最も信号強度の高い衛星を選択して、その2,000バイトL6信号形式生データを標準出力に出力します。また、PRN（pseudo random noise）番号や信号強度などのデバッグメッセージを標準エラー出力に出力します。

例えば、Raspberry PiのUSBポートに接続したHD9310を、RTKLIB str2strにてTCP/IP 2000番ポートからアクセスできるようにしたとします。別のPCから``nc``コマンドにてこの観測データを読み出し、内容をモニタするには次のようにします。

```
nc IPアドレス 2000 | ./alst2qzsl6.py > /dev/null
```

例えば、次のような出力を得ます。

```
195 2195 94409 38
193 2195 94409 43
194 2195 94409 42
199 2195 94409 43
---> prn 193 (snr 43)
```

1列目はPRN番号、2列目と3列目はGPS週番号と秒、4列目はC/No [dB Hz]、5列目はエラーがあればその内容です。

### qzsl62rtcm.py

これは、みちびきL6形式の生データからRTCM形式に変換するプログラムです。標準エラー出力には管制局や含まれるRTCMメッセージ番号と、括弧書きで補強対象衛星数が表示されます。

例えば、MADOCAファームウェアのHD9310開発キットのシリアルポートがTCP/IP 2001番ポートにてアクセスできるとします。

```
nc IPアドレス 2001 | ./alst2qzsl6.py 2>/dev/null | ./qzsl62rtcm.py >/dev/null
```

これにより、例えば次のような出力を得ます。

```
209 Hitachi-Ota:0* 2022-02-03 11:22:44 1062(25) 1068(16) 1251(1)
```

これは、PRN 209（みちびき3号機）のもので、常陸太田管制局にある2系統の最初の設備から生成されたメッセージであり、アラートフラグオン（アスタリスク）、時刻、そして、RTCMメッセージタイプとその補強衛星数を表しています。

### showrtcm.py

これは、RTCMメッセージ内容を表示するプログラムです。例えば、

```
nc IPアドレス 2001 | ./alst2qzsl6.py 2>/dev/null | ./qzsl62rtcm.py 2>/dev/null | ./showrtcm.py
```

とすると、結局、MADOCAファームウェアのHD9310が受信する情報のRTCMメッセージを観測できます。

```
RTCM 1062 G SSR hr clock   G01 G02 G03 G05 G06 G07 G08 G09 G10 G12 G13 G15 G16 G17 G19 G20 G21 G24 G25 G26 G27 G29 G30 G31 G32 (nsat=25 iod=14)
```

## その他のツール

- ecef2llh.py: ECEF座標を緯度・経度・楕円体高に変換します。
- llh2ecef.py: 緯度・経度・楕円体高をECEF座標に変換します。
- gps2utc.py: GPS時刻をUTC時刻に変換します。
- utc2gps.py: UTC時刻をGPS時刻に変換します。

## ライセンス

[BSD 2-clause license](https://opensource.org/licenses/BSD-2-Clause)を適用します。利用者は、商用・非商用、修正の有無を問わず、このプログラムを利用できますが、この著作権表示が必要です。``libbit.py``に[RTKLIB](https://github.com/tomojitakasu/RTKLIB)の成果を利用しています。

