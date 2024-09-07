# Release Note on QZS L6 Tool

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
