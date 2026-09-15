# QZS L6 Tool: quasi-zenith satellite L6-band tool, ver.0.1.11

![QZS L6 Tool](https://raw.githubusercontent.com/yoronneko/qzsl6tool/main/docs/img/qzsl6tool.png)

[English](https://github.com/yoronneko/qzsl6tool/blob/main/readme-en.md)

## 概要

- このツール集は、GNSS（測位衛星: Global Navigation Satellite System）のメッセージを表示し、また、GNSS受信機の生データから特定的形式データ（例えばRTCM形式、みちびきL6形式）を抽出します。
- このツール集は、メッセージを標準入力で受け取り、変換結果を逐次的に標準出力に出力するPythonコードからなります。必要に応じて、標準エラー出力も利用できます。
- netcatの``nc``や、[RTKLIB](https://github.com/tomojitakasu/RTKLIB)の``str2str``などと一緒に利用することを想定しています。
- 当初、準天頂衛星みちびき（QZS: quasi-zenith satellite）がL6周波数帯にて放送する補強メッセージ（CLASやMADOCA-PPP）の内容表示を目指していましたが、Galileo HASメッセージなども表示できるようになりました。
- 2024年8月11日バージョンから[セマンテック・バージョニング](https://packaging.python.org/en/latest/discussions/versioning/#choosing-a-versioning-scheme)を導入しました。
- [リリースノート](https://github.com/yoronneko/qzsl6tool/blob/main/release_note.md)

## 動作環境

### 前提条件

本ツールは、次のいずれかの環境で利用できます。

- **Linux・macOSで直接実行する場合**：Python 3.10以降とpipが必要です。コマンドラインから利用します。
- **Dockerで実行する場合**：Docker Desktopなど、Linuxコンテナを実行できるDocker環境が必要です。Windows、macOS、Linux、Raspberry Pi OSで利用できます。DockerイメージにはPython実行環境、``nc``、RTKLIB 2.4.3 b34の``str2str``が含まれるため、これらをホスト側にインストールする必要はありません。

### セットアップ

**PyPIからインストールする場合**

Linux・macOSでは、次のコマンドでインストールすると、直接実行できるようになります。

```bash
python3 -m pip install qzsl6tool
```

``bitstring``、``galois``、``numpy``などのPython依存パッケージも一緒にインストールされます。``nc``やRTKLIBの``str2str``などの外部コマンドは、必要に応じて別途インストールしてください。

**リポジトリーの取得（Dockerのビルドやサンプルの利用に必要）**

Dockerイメージをビルドする場合や、付属のサンプル・テストを利用する場合は、Gitでリポジトリーを取得します。すでに取得済みの場合は、そのリポジトリーのルートへ移動してください。

WindowsのGit CLIを利用する場合は、Pythonコードの行末にCRが混入しないよう、cloneする前に次の設定を行ってください。

```bash
git config --global core.autocrlf input
```

```bash
git clone https://github.com/yoronneko/qzsl6tool.git
cd qzsl6tool
```

**Dockerで実行する場合**

リポジトリーのルートで、次のコマンドを実行してDockerイメージをビルドします。

```bash
docker build -t qzsl6tool .
```

イメージには実行環境とコードのみが含まれ、Git、ビルドツール、テスト、サンプルは含まれません。サンプルやテストを利用する際は、次の利用例のようにホスト側のリポジトリーをコンテナにマウントします。

### 利用例

**PyPIからインストールしたツールの実行**

付属のL6サンプルを表示するには、リポジトリーのルートで次のコマンドを実行します。

```bash
qzsl6read.py < sample/2022001A.l6
```

RTKLIBの``str2str``をインストールしている場合は、NTRIPで取得したRTCMメッセージを表示できます。

```bash
str2str -in ntrip://ntrip.rnav.info.hiroshima-cu.ac.jp:80/OEM7 2>/dev/null | rtcmread.py
```

**Dockerでの実行**

付属のL6サンプルを表示するには、リポジトリーのルートで次のコマンドを実行します。``-v .:/mnt``は、ホスト側のカレントディレクトリーをコンテナ内の``/mnt``にマウントする指定です。

```bash
docker run -it --rm -v .:/mnt qzsl6tool "qzsl6read.py < /mnt/sample/2022001A.l6"
```

NTRIPで取得したRTCMメッセージを表示する場合は、次のように実行します。

```bash
docker run -it --rm qzsl6tool "str2str -in ntrip://ntrip.rnav.info.hiroshima-cu.ac.jp:80/OEM7 2>/dev/null | rtcmread.py"
```

自分で用意したL6データを表示する場合は、そのファイルがあるディレクトリーで次のように実行します。``my_l6_data.l6``は実際のファイル名に置き換えてください。

```bash
docker run -it --rm -v .:/mnt qzsl6tool "qzsl6read.py < /mnt/my_l6_data.l6"
```

WindowsでGNSSバイナリデータを扱う場合は、上記の例のように、入力の取得とパイプ処理をコンテナ内で完結させてください。``cmd.exe``やPowerShellのパイプにはバイナリデータを流さないでください。

**Dockerイメージ内のコードの検証**

リポジトリーのルートで次のコマンドを実行すると、ホスト側のテストとサンプルを使って、イメージ内のPythonコードを検証できます。

```bash
docker run -it --rm -v .:/mnt -e CODEDIR=/root/qzsl6tool/python/ qzsl6tool "cd /mnt/test && bash do_test.sh"
```

## 衛星信号表示

| display | code |
|:----:|:-------:|
| RTCM |[rtcmread.py](https://github.com/yoronneko/qzsl6tool/blob/main/docs/ja/rtcmread.md) |
| QZSS L6 |[qzsl6read.py](https://github.com/yoronneko/qzsl6tool/blob/main/docs/ja/qzsl6read.md) |
| QZSS L1S | [qzsl1sread.py](https://github.com/yoronneko/qzsl6tool/blob/main/docs/ja/qzsl1sread.md) |
| Galileo I/NAV | [galinavread.py](https://github.com/yoronneko/qzsl6tool/blob/main/docs/ja/galinavread.md) |
| Galileo HAS |[gale6read.py](https://github.com/yoronneko/qzsl6tool/blob/main/docs/ja/gale6read.md) |
|BeiDou PPP-B2b | [bdsb2read.py](https://github.com/yoronneko/qzsl6tool/blob/main/docs/ja/bdsb2read.md)|

## RTCM形式変換

| conversion | code |
|:----:|:-------:|
| QZS L6 &rarr; RTCM message type 4050 | [l6rtcm4050.py](https://github.com/yoronneko/qzsl6tool/blob/main/docs/ja/l6rtcm4050.md) |

## GNSS受信機データ変換

| GNSS receiver | code | QZS L6 | SBAS / QZS L1S | Galileo HAS | Galileo I/NAV | BeiDou B2b | GLONASS L1OF | BeiDou B1I |
|:----:|:---:| :-------:|:-----------:|:--------:|:---:|:---:|:---:|:---:|
| Allystar HD9310 option C | [alstread.py](https://github.com/yoronneko/qzsl6tool/blob/main/docs/ja/alstread.md) |``-l`` option | | | | | | |
| [Pocket SDR](https://github.com/tomojitakasu/PocketSDR) | [psdrread.py](https://github.com/yoronneko/qzsl6tool/blob/main/docs/ja/psdrread.md) | ``-l`` option |  | ``-e`` option | ``-i`` option| ``-b`` option| | |
| NovAtel OEM729 | [novread.py](https://github.com/yoronneko/qzsl6tool/blob/main/docs/ja/novread.md) | | | ``-e`` option | | | | |
| Septentrio mosaic-X5 | [septread.py](https://github.com/yoronneko/qzsl6tool/blob/main/docs/ja/septread.md) | | | ``-e`` option | | ``-b`` option| | |
| Septentrio mosaic-CLAS | [septread.py](https://github.com/yoronneko/qzsl6tool/blob/main/docs/ja/septread.md) |``-l`` option | | | | | | |
| u-blox ZED-F9P | [ubxread.py](https://github.com/yoronneko/qzsl6tool/blob/main/docs/ja/ubxread.md) | | ``--l1s`` option | | ``-i`` option| | ``--l1of`` option | ``--b1i`` option |

## 時刻・座標変換

| conversion | code |
|:--:|:--:|
|GPS time, GST, BST &rarr; UTC time | [gps2utc.py](https://github.com/yoronneko/qzsl6tool/blob/main/docs/ja/gps2utc.md) |
|UTC time &rarr; GPS time, GST, BST | [utc2gps.py](https://github.com/yoronneko/qzsl6tool/blob/main/docs/ja/utc2gps.md)|
|LLH &rarr; ECEF | [llh2ecef.py](https://github.com/yoronneko/qzsl6tool/blob/main/docs/ja/llh2ecef.md)|
|ECEF &rarr; LLH | [ecef2llh.py](https://github.com/yoronneko/qzsl6tool/blob/main/docs/ja/ecef2llh.md)|

## ディレクトリ構造

```text
├── c/               (contributed C source code)
├── dist/            (PyPI build artifacts; generated, not tracked by git)
├── docs/            (documentation directory)
├── python/          (Python source code directory)
├── sample/          (sample data directory)
├── test/            (test tool directory)
├── typings/         (local type stubs for pyright/Pylance)
├── CLAUDE.md        (documentation for Claude)
├── Dockerfile       (Docker image production procedure)
├── license.txt      (license description)
├── pyproject.toml   (configuration for PyPI)
├── readme-en.md     (English document)
├── readme.md        (this file, Japanese document)
├── release_note.md  (release note)
├── requirements.txt (declaration of Python package dependencies)
└── SECURITY.md      (description of reporting security vulnerabilities responsibly)
```

## ライセンス

ライセンスとして、[BSD 2-clause license](https://opensource.org/licenses/BSD-2-Clause)を適用します。

利用者は、商用・非商用、修正の有無を問わず、このプログラムを利用できますが、この著作権表示が必要です。``librtcm.py``の関数 rtk_crc24q ()に[RTKLIB](https://github.com/tomojitakasu/RTKLIB) ver.2.4.3b34の成果を利用しています。

Copyright (c) 2022-2026 by Satoshi Takahashi  
Copyright (c) 2007-2020 by Tomoji TAKASU
