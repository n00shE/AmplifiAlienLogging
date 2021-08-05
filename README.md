# Amplifi Alien Logging and Monitoring

## Required Packages
```requests
csv
argparse
datetime
re
time
```
To enable sound effects chime is required.
```
chime
```

## Usage
```
usage: alien_monitor.py [-h] [-v] [-i INTERVAL] [-o] [-s] [-b BLOCK] [-e] ip password

Monitors connections and disconnections from your Amplifi Alien network

positional arguments:
  ip                    The ip address of your main Amplifi Alien Router
  password              The password to your router

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Enable debug messages
  -i INTERVAL, --interval INTERVAL
                        Interval to check router for data in seconds (default is 10)
  -o, --outfile         Saves log in current directory, will append if file exists (Month-Day-Year-
                        netlog.txt)
  -s, --sound           Enable sounds for device updates and warnings (Requires chime library)
  -b BLOCK, --block BLOCK
                        Will not record or print info for devices containing this string
  -e, --exp             Enable expiremental features
```

## Class Methods
TODO
