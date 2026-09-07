# QZS L6 Tool: quasi-zenith satellite L6-band tool, ver.0.1.7a2

![QZS L6 Tool](https://raw.githubusercontent.com/yoronneko/qzsl6tool/main/docs/img/qzsl6tool.png)

[日本語](https://github.com/yoronneko/qzsl6tool/blob/main/readme.md)

## Summary

- This set of tools displays GNSS (Global Navigation Satellite System) messages and extracts specific formatted data from the raw data of GNSS receivers, for example, RTCM format and Michibiki L6 format.
- The suite consists of Python code that receives the messages via standard input, and the conversion results are sequentially outputted to the standard output. The use of standard error output is also possible as needed.
- It is designed to be used in conjunction with tools such as ``nc`` of netcat, and ``str2str`` of [RTKLIB](https://github.com/tomojitakasu/RTKLIB).
- Initially, it aimed to display the content of augmentation messages broadcasted by the quasi-zenith satellite Michibiki (QZS) in the L6 frequency band, including CLAS and MADO. However, it is now also capable of displaying Galileo HAS messages.
- [Semantic versioning](https://packaging.python.org/en/latest/discussions/versioning/#choosing-a-versioning-scheme) has been applied since 2024-08-11.
- [Release note](https://github.com/yoronneko/qzsl6tool/blob/main/release_note.md)

## Operating Environment

- It is intended for use on the command line of Linux or macOS.
- Python 3.10 or later is required.
- With a Docker environment such as Docker Desktop, this tool can also be used on Windows, macOS, Linux, and Raspberry Pi OS inside a Linux container. The Docker image includes the Python runtime, ``nc``, and ``str2str`` from RTKLIB 2.4.3 b34.

Installing from PyPI

```bash
python3 -m pip install qzsl6tool
qzsl6read.py < sample/2022001A.l6
str2str -in ntrip://ntrip.rnav.info.hiroshima-cu.ac.jp:80/OEM7 2>/dev/null | rtcmread.py
```

The PyPI package installs the required Python dependencies such as ``bitstring``, ``galois``, and ``numpy``. External command-line tools such as ``nc`` and RTKLIB ``str2str`` should be installed separately when needed.

Building a Docker image

```bash
docker build -t qzsl6tool .
```

Executing a docker image

```bash
docker run -it --rm qzsl6tool "cd /root/qzsl6tool/test; ./do_test.sh"
docker run -it --rm qzsl6tool "qzsl6read.py < /root/qzsl6tool/sample/2022001A.l6"
docker run -it --rm qzsl6tool "str2str -in ntrip://ntrip.rnav.info.hiroshima-cu.ac.jp:80/OEM7 2>/dev/null | rtcmread.py"
docker run -it --rm -v .:/mnt qzsl6tool "qzsl6read.py < my_l6_data.l6"
```

When handling GNSS binary data on Windows, do not pass the binary stream through ``cmd.exe`` or PowerShell pipes. Keep input acquisition and the processing pipeline inside the container like above.

Those who use Windows Git CLI, please execute ``git config --global core.autocrlf input`` before cloning this repository. This is to avoid CR inclusion in line ends of a Python code.

## Satellite Signal Display

| display | code |
|:----:|:-------:|
| RTCM |[rtcmread.py](https://github.com/yoronneko/qzsl6tool/blob/main/docs/en/rtcmread.md) |
| QZSS L6 |[qzsl6read.py](https://github.com/yoronneko/qzsl6tool/blob/main/docs/en/qzsl6read.md) |
| QZSS L1S | [qzsl1sread.py](https://github.com/yoronneko/qzsl6tool/blob/main/docs/en/qzsl1sread.md) |
| Galileo I/NAV | [galinavread.py](https://github.com/yoronneko/qzsl6tool/blob/main/docs/en/galinavread.md) |
| Galileo HAS |[gale6read.py](https://github.com/yoronneko/qzsl6tool/blob/main/docs/en/gale6read.md) |
|BeiDou PPP-B2b | [bdsb2read.py](https://github.com/yoronneko/qzsl6tool/blob/main/docs/en/bdsb2read.md)|

## RTCM Format Conversion

| conversion | code |
|:----:|:-------:|
| QZS L6 &rarr; RTCM message type 4050 | [l6rtcm4050.py](https://github.com/yoronneko/qzsl6tool/blob/main/docs/en/l6rtcm4050.md) |

## GNSS Receiver Data Conversion

| GNSS receiver | code | QZS L6 | SBAS / QZS L1S | Galileo HAS | Galileo I/NAV | BeiDou B2b | GLONASS L1OF | BeiDou B1I |
|:----:|:---:| :-------:|:-----------:|:--------:|:---:|:---:|:---:|:---:|
| Allystar HD9310 option C | [alstread.py](https://github.com/yoronneko/qzsl6tool/blob/main/docs/en/alstread.md) |``-l`` option | | | | | | |
| [Pocket SDR](https://github.com/tomojitakasu/PocketSDR) | [psdrread.py](https://github.com/yoronneko/qzsl6tool/blob/main/docs/en/psdrread.md) | ``-l`` option |  | ``-e`` option | ``-i`` option| ``-b`` option| | |
| NovAtel OEM729 | [novread.py](https://github.com/yoronneko/qzsl6tool/blob/main/docs/en/novread.md) | | | ``-e`` option | | | | |
| Septentrio mosaic-X5 | [septread.py](https://github.com/yoronneko/qzsl6tool/blob/main/docs/en/septread.md) | | | ``-e`` option | | ``-b`` option| | |
| Septentrio mosaic-CLAS | [septread.py](https://github.com/yoronneko/qzsl6tool/blob/main/docs/en/septread.md) |``-l`` option | | | | | | |
| u-blox ZED-F9P | [ubxread.py](https://github.com/yoronneko/qzsl6tool/blob/main/docs/en/ubxread.md) | | ``--l1s`` option | | ``-i`` option| | ``--l1of`` option | ``--b1i`` option |

## Time & Coordinate Conversion

| conversion | code |
|:--:|:--:|
|GPS time, GST, BST &rarr; UTC time | [gps2utc.py](https://github.com/yoronneko/qzsl6tool/blob/main/docs/en/gps2utc.md) |
|UTC time &rarr; GPS time, GST, BST | [utc2gps.py](https://github.com/yoronneko/qzsl6tool/blob/main/docs/en/utc2gps.md)|
|LLH &rarr;  ECEF | [llh2ecef.py](https://github.com/yoronneko/qzsl6tool/blob/main/docs/en/llh2ecef.md)|
|ECEF &rarr;  LLH | [ecef2llh.py](https://github.com/yoronneko/qzsl6tool/blob/main/docs/en/ecef2llh.md)|

## Directory Structure

```text
├── docs/        (documentation directory)
├── license.txt  (license description)
├── python/      (code directory)
├── readme-en.md (English document)
├── readme.md    (this file, Japanese document)
├── sample/      (sample data directory)
└── test/        (directory to test the tools)
```

## License

This project is licensed under the [BSD 2-clause license](https://opensource.org/licenses/BSD-2-Clause).

Users are permitted to use this program for commercial and non-commercial purposes, with or without modification, but this copyright notice is required. The function rtk_crc24q() in ``librtcm.py`` utilizes the achievements of [RTKLIB](https://github.com/tomojitakasu/RTKLIB) ver.2.4.3b34.

Copyright (c) 2022-2026 by Satoshi Takahashi  
Copyright (c) 2007-2020 by Tomoji TAKASU
