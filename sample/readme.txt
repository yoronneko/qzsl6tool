#
# QZS L6 Tool - Sample data
#

File 2018001A.l6 is removed because it used the draft version specification.

File Path : 2019001A.l6
Date Time : 2019-01-01 00:00:00 UTC
Duration  : 2 minutes (trancated from 1-day data)
Note      : QZS L6 CLAS raw data obtained from the official archive at
Note      : https://sys.qzss.go.jp/dod/archives/clas.html, by using:
Note      : curl https://sys.qzss.go.jp/archives/l6/2019/2019001A.l6 -o aaa.l6
Note      : dd if=aaa.l6 of=2019001A.l6 ibs=1000 count=30

File Path : 202201A.l6
Date Time : 2022-01-01 00:00:00 UTC
Duration  : 2 minutes (trancated from 1-day data)
Note      : QZS L6 CLAS raw data obtained from the official archive at
Note      : https://sys.qzss.go.jp/dod/archives/clas.html, by using:
Note      : curl https://sys.qzss.go.jp/archives/l6/2022/2022001A.l6 -o aaa.l6
Note      : dd if=aaa.l6 of=2022001A.l6 ibs=1000 count=30

File Path : 20190529hiroshima.rtcm
Date Time : 2019-05-29 ??:??:?? UTC
Duration  : 40 seconds
Note      : recorded in Hiroshima, Japan with Emlid Reach (u-blox M8T+RTKLIB, L1only)

File Path : 20210101jaxamdc.rtcm
Date Time : 2021-01-01 00:00:00 UTC
Duration  : 30 seconds
Note      : JAXA (Japan Aerospace Exploration Agency) RTCM SSR data
Note      : of MADOCA, provided through NTRIP

File Path : 20211226-082212clas.psdr
Date Time : 2021-12-26 08:22:12 UTC
Duration  : 30 seconds
Note      : L6 band signal reception and L6D decode sample of Pocket SDR by
Note      : Prof. Tomoji Takasu. https://github.com/tomojitakasu/PocketSDR
Note      : pocket_trk.py ../sample/L6_20211226_082212_12MHz_IQ.bin -prn 194 -f 12 -sig L6D -log 20211226-082212clas.psdr

File Path : 20211226-082212mdc.psdr
Date Time : 2021-12-26 08:22:12 UTC
Duration  : 30 seconds
Note      : L6 band signal reception and L6E decode sample of Pocket SDR by
Note      : Prof. Tomoji Takasu. https://github.com/tomojitakasu/PocketSDR
Note      : pocket_trk.py ../sample/L6_20211226_082212_12MHz_IQ.bin -prn 204 -f 12 -sig L6E -log 20211226-082212mdc.psdr

File Path : 20220326-231200clas.alst
Date Time : 2022-03-26 23:12:00 UTC
Duration  : 1 minute
Note      : Allystar raw data observed at Hiroshima, JP
Note      : with HD9310 (TAU1302) option C CLAS firmware

File Path : 20220326-231200mdc.alst
Date Time : 2022-03-26 23:12:00 UTC
Duration  : 1 minute
Note      : Allystar raw data observed at Hiroshima, JP
Note      : with HD9310 (TAU1302) option C MADOCA firmware

File Path : 20220930-115617has.psdr
Date Time : 2022-09-30 11:56:17 UTC
Duration  : 1 minute
Note      : E6B signal reception sample with Pocket SDR at Hiroshima, JP

File Path : 20221130-125237mdc-ppp.alst
Date Time : 2022-11-30 12:52:37 UTC
Duration  : 1 minute
Note      : Allystar raw data observed at Hiroshima, JP
Note      : with HD9310 (TAU1302) option C MADOCA firmware

File Path : 20221213-010900.rtcm
Date Time : 2022-12-13 01:09:00 UTC
Duration  : 1 minute
Note      : RTCM message obtained at Hiroshima, JP
Note      : with OEM729 and RTKLIB 2.4.3b34 str2str

File Path : 20230305-063900has.psdr
Date Time : 2023-03-05 06:39:00 UTC
Duration  : 1 minute
Note      : E6B signal reception sample with Pocket SDR at Hiroshima, JP

File Path : 20230819-053733has.nov
Date Time : 2023-08-19 05:37:33 UTC
Duration  : 43 seconds
Note      : E6B signal reception sample with NovAtel OEM729 at Hiroshima, JP

File Path : 20230819-061342qlnav.nov
Date Time : 2023-08-19 06:13:42 UTC
Duration  : 43 seconds
Note      : Navigation messages obtained with NovAtel OEM729 at Hiroshima, JP

File Path : 20230819-081730hasbds.sept
Date Time : 2023-08-19 08:17:30 UTC
Duration  : 31 seconds
Note      : HAS and PPP-B2b raw data obtained with Septentrio mosaic-X5 at Hiroshima, JP

File Path : 20230819-082130clas.sept
Date Time : 2023-08-19 08:21:30 UTC
Duration  : 61 seconds
Note      : CLAS raw data obtained with Septentrio mosaic-CLAS at Hiroshima, JP

File Path : 20230819-085030mdc-ppp.sept
Date Time : 2023-08-19 08:50:30 UTC
Duration  : 60 seconds
Note      : MADOCA-PPP raw data obtained with Septentrio mosaic-CLAS at Hiroshima, JP

File Path : 20230919-114418.ubx
Date Time : 2023-09-19 11:44:18 UTC
Duration  : 40 seconds
Note      : u-blox ZED-F9P raw data obtained at Hiroshima, JP

# EOF
