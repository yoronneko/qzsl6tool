# QZS L6 Tool: quasi-zenith satellite L6-band tool

[English description](readme-en.md)

- This set of tools displays GNSS (Global Navigation Satellite System) messages and extracts specific formatted data from the raw data of GNSS receivers, for example, RTCM format and Michibiki L6 format.
- The suite consists of Python code that receives the messages via standard input, and the conversion results are sequentially outputted to the standard output. The use of standard error output is also possible as needed.
- It is designed to be used in conjunction with tools such as ``nc`` of netcat, and ``str2str`` of [RTKLIB](https://github.com/tomojitakasu/RTKLIB).
- Initially, it aimed to display the content of augmentation messages broadcasted by the quasi-zenith satellite Michibiki (QZS) in the L6 frequency band, including CLAS and MADO. However, it is now also capable of displaying Galileo HAS messages.

![QZS L6 Tool](docs/img/qzsl6tool.jpg)

## Installation of Non-Standard Python Modules

- Python 3.7 or later and the `bitstring` module ver.4.0.2 are required.  
``pip3 install bitstring==4.0.2``
- For decoding Galileo HAS, the `galois` module and the `numpy` module are additionally required. Therefore, Python 3.10 is needed.  
``pip3 install galois numpy``
- In the future, we hope to remove these version restrictions.

## Satellite Signal Display

| display | code |
|:----:|:-------:|
| RTCM |[rtcmread.py](docs/rtcmread-en.md) |
| QZSS L6 |[qzsl6read.py](docs/qzsl6read-en.md) |
| QZSS L1S | [qzsl1sread.py](docs/qzsl1sread-en.md) |
| Galileo HAS |[gale6read.py](docs/gale6read-en.md) |

## GNSS Receiver Data Conversion

| GNSS receiver | code | QZS L6 | QZS L1S | Galileo HAS | Galileo I/NAV | BeiDou B2b |
|:----:|:---:| :-------:|:-----------:|:--------:|:---:|:---:|
| Allystar HD9310 option C | [alstread.py](docs/alstread.md) |``-l`` option | | | | |
| [Pocket SDR](https://github.com/tomojitakasu/PocketSDR) | [psdrread.py](docs/psdrread.py) | ``-l`` option | ``-l1s`` option | ``-e`` option | ``-i`` option| ``-b`` option|
| NovAtel OEM729 | [novread.py](docs/novread.md) | | | ``-e`` option | | |
| Septentrio mosaic-X5 | [septread.py](docs/septread.md) | | | ``-e`` option | | ``-b`` option|
| Septentrio mosaic-CLAS | [septread.py](docs/septread.md) |``-l`` option | | | | |
| u-blox ZED-F9P | [ubxread.py](docs/ubxread.md) | | ``-l1s`` option | | ``-i`` option| |

## Time & Coordinate Conversion

| conversion | code |
|:--:|:--:|
|GPS time, GST, BST &rarr; UTC time | [gps2utc.py](docs/gps2utc.md) |
|UTC time &rarr; GPS time, GST, BST | [utc2gps.py](docs/utc2gps.md)|
|LLH &rarr;  ECEF | [llh2ecef.py](docs/llh2ecef-en.md)|
|ECEF &rarr;  LLH | [ecef2llh.py](docs/ecef2llh-en.md)|

## Directory Structure

```
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

Copyright (c) 2022-2024 by Satoshi Takahashi  
Copyright (c) 2007-2020 by Tomoji TAKASU
