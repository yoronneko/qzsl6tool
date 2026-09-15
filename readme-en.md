# QZS L6 Tool: quasi-zenith satellite L6-band tool, ver.0.1.11

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

### Prerequisites

You can run these tools in either of the following environments:

- **Directly on Linux or macOS**: Python 3.10 or later and pip are required. Run the tools from the command line.
- **With Docker**: A Docker environment capable of running Linux containers, such as Docker Desktop, is required. You can use the tools on Windows, macOS, Linux, and Raspberry Pi OS. The Docker image includes the Python runtime, ``nc``, and ``str2str`` from RTKLIB 2.4.3 b34, so you do not need to install them on the host.

### Setup

**Installing from PyPI**

To run the tools directly on Linux or macOS, install them with:

```bash
python3 -m pip install qzsl6tool
```

The required Python dependencies, including ``bitstring``, ``galois``, and ``numpy``, are installed automatically. Install external command-line tools such as ``nc`` and RTKLIB's ``str2str`` separately as needed.

**Cloning the repository (required for Docker builds or sample data)**

Clone the repository with Git if you want to build the Docker image or use the included samples and tests. If you already have a clone, change to its root directory.

If you use the Windows Git CLI, apply the following setting before cloning to prevent CR characters from being added to Python line endings:

```bash
git config --global core.autocrlf input
```

```bash
git clone https://github.com/yoronneko/qzsl6tool.git
cd qzsl6tool
```

**Setting up Docker**

Build the Docker image from the root of the repository:

```bash
docker build -t qzsl6tool .
```

The image contains only the runtime and application code. It does not include Git, build tools, tests, or samples. To use the samples or tests, mount the host repository into the container as shown below.

### Usage Examples

**Running tools installed from PyPI**

To display the included L6 sample, run the following command from the root of the repository:

```bash
qzsl6read.py < sample/2022001A.l6
```

If you have installed RTKLIB's ``str2str``, you can display RTCM messages received via NTRIP:

```bash
str2str -in ntrip://ntrip.rnav.info.hiroshima-cu.ac.jp:80/OEM7 2>/dev/null | rtcmread.py
```

**Running tools with Docker**

To display the included L6 sample, run the following command from the root of the repository. The ``-v .:/mnt`` option mounts the host's current directory at ``/mnt`` inside the container.

```bash
docker run -it --rm -v .:/mnt qzsl6tool "qzsl6read.py < /mnt/sample/2022001A.l6"
```

To display RTCM messages received via NTRIP, run:

```bash
docker run -it --rm qzsl6tool "str2str -in ntrip://ntrip.rnav.info.hiroshima-cu.ac.jp:80/OEM7 2>/dev/null | rtcmread.py"
```

To display your own L6 data, run the following command from the directory containing the file. Replace ``my_l6_data.l6`` with the actual filename.

```bash
docker run -it --rm -v .:/mnt qzsl6tool "qzsl6read.py < /mnt/my_l6_data.l6"
```

When handling GNSS binary data on Windows, keep input acquisition and the processing pipeline inside the container, as shown above. Do not pass binary data through ``cmd.exe`` or PowerShell pipes.

**Testing the code inside the Docker image**

Run the following command from the root of the repository to test the Python code inside the image using the tests and samples on the host:

```bash
docker run -it --rm -v .:/mnt -e CODEDIR=/root/qzsl6tool/python/ qzsl6tool "cd /mnt/test && bash do_test.sh"
```

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
├── readme-en.md     (this file, English document)
├── readme.md        (Japanese document)
├── release_note.md  (release note)
├── requirements.txt (declaration of Python package dependencies)
└── SECURITY.md      (description of reporting security vulnerabilities responsibly)
```

## License

This project is licensed under the [BSD 2-clause license](https://opensource.org/licenses/BSD-2-Clause).

Users are permitted to use this program for commercial and non-commercial purposes, with or without modification, but this copyright notice is required. The function rtk_crc24q() in ``librtcm.py`` utilizes the achievements of [RTKLIB](https://github.com/tomojitakasu/RTKLIB) ver.2.4.3b34.

Copyright (c) 2022-2026 by Satoshi Takahashi  
Copyright (c) 2007-2020 by Tomoji TAKASU
