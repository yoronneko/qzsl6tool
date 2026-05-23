# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

QZS L6 Tool is a Python-based CLI toolkit for displaying and converting GNSS (Global Navigation Satellite System) messages. All tools read from **stdin** and write to **stdout**, designed for pipe-based workflows with tools like `nc` (netcat) and `str2str` (RTKLIB).

## Setup

```bash
pip3 install bitstring galois numpy
```

Python 3.8+ required.

## Running Tests

Tests live in `test/` and compare output against expected results stored in `test/expect/`:

```bash
cd test
./do_test.sh
```

The script runs all conversions and diffs output against `expect/`. On failure it shows a colorized diff and exits with code 1. Sample input data is in `sample/`.

## Architecture

### Two-layer structure

**Receiver reader scripts** (`alstread.py`, `psdrread.py`, `novread.py`, `septread.py`, `ubxread.py`) parse proprietary binary formats from specific GNSS receivers and extract raw signal payloads (L6, E6B, L1S, I/NAV, B2b). They output intermediate binary formats piped into message reader scripts.

**Message reader scripts** (`qzsl6read.py`, `gale6read.py`, `bdsb2read.py`, `rtcmread.py`, `qzsl1sread.py`, `galinavread.py`) decode the signal-level messages and display human-readable content, or convert to RTCM format with `-r` flag.

### Library modules (`lib*.py`)

| Module | Purpose |
|---|---|
| `libqzsl6tool.py` | CRC utilities (CRC24Q, CRC24, CRC16-CCITT, u-blox checksum), Septentrio endian permutation. Version string lives here. |
| `libssr.py` | Core SSR (State Space Representation) and Compact SSR decoding — orbit/clock corrections, code/phase biases, troposphere, VTEC. Used by `qzsl6read.py`, `gale6read.py`, `bdsb2read.py`. |
| `libnav.py` | Navigation message decoding and GNSS constants (satellite counts, physical constants). |
| `libgnsstime.py` | GPS/Galileo/BeiDou week+TOW ↔ UTC conversion. |
| `libecef.py` | ECEF ↔ LLH coordinate conversion (WGS-84). |
| `libtrace.py` | Colored terminal output via ANSI codes. `Trace` class controls verbosity level (`-t` flag). `libtrace.err/warn/info` write to stderr. |
| `libqznma.py` | QZSS Navigation Message Authentication (NMA) decoding. |

### Data flow example

```
receiver binary → alstread.py -l → .l6 stream → qzsl6read.py → human text
                                               → qzsl6read.py -r → RTCM stream → rtcmread.py
```

### Trace/verbosity system

All reader scripts accept `-t LEVEL` (trace level). `Trace` objects from `libtrace.py` gate output by level — higher levels show more detail. Output is colorized automatically when stdout is a TTY.

### RTCM output

`qzsl6read.py -r` converts CLAS→RTCM 4073 or MDC→RTCM SSR. `l6rtcm4050.py` converts CLAS→RTCM 4050. CRC24Q (from RTKLIB) is used for RTCM message integrity.

## File naming conventions in `sample/` and `test/`

Filenames follow `YYYYMMDD-HHMMSS<type>.<ext>` or `YYYYDDDX.<ext>` patterns. Extensions indicate signal type: `.l6` (QZS L6), `.e6b` (Galileo E6B HAS), `.l1s` (QZS L1S), `.inav` (Galileo I/NAV), `.b2b` (BeiDou B2b), `.rtcm` (RTCM3), `.alst`/`.psdr`/`.nov`/`.sbf`/`.ubx` (receiver-specific raw).
