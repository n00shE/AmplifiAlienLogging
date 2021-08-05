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
Class must be initialized with ip of router and password.  
```
ag = AmplifiGather(args.ip, args.password)
``` 

Call login to gather tokens and session cookie.  
``` 
ag.login()  
```  

Now you can gather the raw json data.  
```
json = ag.get_data()  
```  

"Parse all" gathers data into two flat dictionaries keyed by MAC address.  
```
ag.parse_all()  
wifiInfo = ag.wifidb
ethernetInfo = ag.ethernetdb  
```
These dictionaries can be gathered individually with the following methods.  
```
wifiInfo = ag.get_wifi_data()  
ethernetInfo = ag.get_ethernet_data()
```

"Check join" and "Check leave" require a dictionary to compare to and a character to specify wifi ('w') or ethernet ('e').  
Returns list of MAC addresses that have joined or left, respectively.  
```
wifinew = ag.check_join(wifiolddb, 'w')
ethnew = ag.check_join(etholddb, 'e')
wifileave = ag.check_leave(wifiolddb, 'w')
ethleave = ag.check_leave(etholddb, 'e')
```

"Network monitor" combines all of these functions to create the logging functionality. (This method loops infinitely)  
```
ag.network_monitor(interval: int, sound: bool, file: bool, ignore: str, exp: bool) -> None:
```

## Network Monitor Output
Here is an example of a connection message.  
```
Main 2.4GHz U: Wifi device Johns-iPhone (10.0.1.100) joined @ 10:42:40 +-10s
Mesh 2.4GHz U: Wifi device Johns-iPhone (10.0.1.100) left @ 10:43:52 +-10s
```
Main or Mesh: specifies which router the device is connected to. (Router or MeshPoint)
2.4GHz or 5GHz: specifies which frequency the device is on.  
U or DS or G: specifices whether the device is on the User network (regular), Device specific (separate SSID setting on Router), or Guest network.  
Script will use description for device name if set in the Amplifi app, otherwise hostname. If no hostname, just MAC address is printed.  
Then the IP address is printed along with the time +- the polling interval.  

### Message Types:
Join and leave messages.  
```
Main 2.4GHz U: Wifi device Johns-iPhone (10.0.1.100) joined @ 10:42:40 +-10s
Mesh 2.4GHz U: Wifi device Johns-iPhone (10.0.1.100) left @ 10:43:52 +-10s
```
Signal quality messages. (Only available for Wifi clients)   
```
Main 5GHz U: Wifi device Johns-iPhone has poor signal quality 47 @ 11:02:26
```
Large upstream or downstream bandwidth usage over the last 60 seconds. (Only available for Wifi clients)   
```
Main 5GHz U: Wifi device Johns-iPhone is slamming the downstream with 0.8484 GBRx/60s @ 11:02:36
```

## ToDo and Limitations
Make ignore/block a list of strings instead of a single string.  
Script assumes you have either just a router or a router and a single meshpoint, multiple meshpoints are not supported.  
