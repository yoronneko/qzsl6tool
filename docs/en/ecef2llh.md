## ecef2llh.py

This program converts ECEF (earth-centered, earth-fix) coordinates to latitude, longitude, and ellipsoidal height (LLH).

```bash
$ ecef2llh.py

ECEF to Latitude Longitude and Height
Usage: /Users/sat/bin/ecef2llh.py x y z
```

For example, converting the ECEF coordinates x=-3551876.829, y=3887786.860, z=3586946.387 results in a latitude of 34.4401061 degrees North, a longitude of 132.4147804 degrees East, and an ellipsoidal height of 233.362 meters.

```bash
$ ecef2llh.py -3551876.829 3887786.860 3586946.387

34.4401061 132.4147804 233.362
```
