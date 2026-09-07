# Release Note on QZS L6 Tool

## ver.0.1.7a2 (2026-09-07)

- ubxread.py: `--l1s` now outputs both SBAS and QZS L1S messages (the `--sbas` option was removed); added `--l1of` (GLONASS L1OF/L2OF) and `--b1i` (BeiDou B1I) options.
- Fixed GNSS decoder conditions and the frame detection loop in the receiver readers.
- Fixed latent runtime errors: the CRC-error message in qzsl1sread.py (`.hex` is a property), and the SVID2/SVID3 almanac indexing in galinavread.py.
- Temporarily disabled the CLAS pattern ID display until the test data is updated.
- Type-checking cleanup: added a local `bitstring` type stub (`typings/bitstring.pyi`) and a `[tool.pyright]` section in `pyproject.toml` so that Pylance/pyright resolve the sources in `python/` and infer `read().u` correctly; removed all `# type: ignore` comments and redundant `BitStream()` conversions; navigation message containers (`libnav.NavNull`) now declare their dynamic attributes.
- Documentation: updated ubxread.py docs and the README receiver tables; documented l6rtcm4050.py and previously undocumented CLI options.

## ver.0.1.7a1 (2026-06-15)

- Fixed PyPI project description links to Japanese/English README files, release notes, documentation files, and the project image.

## ver.0.1.7 (2026-05-24)

- Added Dockerfile for Windows, macOS, and Linux usage through Docker Desktop.
- Docker image includes Python dependencies, netcat, and RTKLIB 2.4.3 b34 str2str.
- Added Docker usage notes to README files.

## ver.0.1.6 (2026-01-19)

- CLAS transmission pattern (qzsl6read.py)

## ver.0.1.5 (2025-06-08)

- Version display (all apps)
- Pocket SDR new format (psdrread.py)

## ver.0.1.4 (2024-09-11)

- Added RTCM3 detailed information (rtcmread.py)

## ver.0.1.3 (2024-09-07)

- Bug fix: RTCM Galileo navigation message

## ver.0.1.2 (2024-08-30)

- Usage of bitstring's read: e.g. df.read('u10') -> df.read(10).u
- Merge libobs.py to rtcmread.py

## ver.0.1.1 (2024-08-22)

- Added a test of l6rtcm4050.py
- Indicating RTCM MT 4073 and RTCM MT 4050 messages in test/expect directory
- Merge librtcm.py to rtcmread.py

## ver.0.1.0 (2024-08-16)

- Semantic versioning
- Capable of reading MADOCA-PPP Ionospheric augmentation message
- l6rtcm4050.py: QZS L6 raw to RTCM MT 4050 conversion
