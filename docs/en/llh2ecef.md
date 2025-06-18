# llh2ecef.py

This program onverts latitude, longitude, and ellipsoidal height (LLH) to ECEF （earth-centered, earth-fix）coordinates.

```bash
$ llh2ecef.py
LLH to ECEF conversion, QZS L6 Tool ver.x.x.x
Usage: /Users/sat/env/bin/llh2ecef.py lat lon height
```

For example, converting a latitude of 34.4401061 degrees North, a longitude of 132.4147804 degrees East, and an ellipsoidal height of 233.362 meters results in
an ECEF coordinates of x=-3551876.829, y=3887786.860, and z=3586946.387.

```bash
$ llh2ecef.py 34.4401061 132.4147804 233.362

-3551876.829 3887786.860 3586946.387
```
