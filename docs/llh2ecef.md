## llh2ecef.py

緯度・経度・楕円体高（LLH: latitude, longitude, and ellipsoidal height）をECEF（earth-centered, earth-fix）座標に変換します。

```
$ llh2ecef.py --help
Latitude Longitude and Height to ECEF
Usage: /Users/sat/bin/llh2ecef.py lat lon height
```

例えば、北緯34.4401061度、東経132.4147804度、楕円体高233.362メートルを変換すると、ECEF座標 x=-3551876.829, y=3887786.860, z=3586946.387になります。

```
$ llh2ecef.py 34.4401061 132.4147804 233.362

-3551876.829 3887786.860 3586946.387
```
