'''
Ryan Blanchard
rmblanch@uci.edu
Gather data from Amplifi Alien Router
'''
import requests
import csv
import argparse
from datetime import datetime
import re
import time

#from requests.sessions import session

'''
Wifi Data Example

"Address": "10.0.1.210",
"Description": "*****",
"HappinessScore": 100,
"HostName": "*****",
"Inactive": 0,
"LeaseValidity": 82318,
"MaxBandwidth": 80,
"MaxSpatialStreams": 3,
"Mode": "802.11ac",
"RadioMode": "802.11ax",
"RxBitrate": 1300000,
"RxBytes": 4294967295,
"RxBytes64": 4429155451, //Bytes64 unknown, doesnt exist for all clients, larger RxBytes datatype???
"RxBytes_15sec": 11982,
"RxBytes_30sec": 18465,
"RxBytes_5sec": 3521,
"RxBytes_60sec": 94676,
"RxMcs": 9,
"RxMhz": 80,
"SignalQuality": 99,
"TxBitrate": 1300000,
"TxBytes": 1184629011,
"TxBytes_15sec": 11020,
"TxBytes_30sec": 18099,
"TxBytes_5sec": 2736,
"TxBytes_60sec": 148526,
"TxMcs": 9,
"TxMhz": 80
'''


class AmplifiGather():
    def __init__(self, ip, password, debug=False):
        self.main = ""
        self.mesh = ""
        self.GIG = 1000000000
        self.url = "http://" + ip + '/'
        self.password = password # should probably be an environment variable
        self.debug = debug

        self.token = ""
        self.infotoken = ""
        self.session = ""
        self.json = {}
        self.wifidb = {}
        self.ethernetdb = {}
        self.time = ""
        self.wifidevices = 0
        self.ethernetdevices = 0

    def get_token(self):
        r = requests.get(self.url + 'login.php')
        token = re.findall(r"value=\'([A-Za-z0-9]{16})\'", r.text)[0]
        self.token = token
        if self.debug: print(f"DEBUG: Got token {token}")
        return token

    def get_info_token(self):
        r = requests.get(self.url + 'info.php', cookies={'webui-session': self.session })
        token = re.findall(r"token=\'([A-Za-z0-9]{16})\'", r.text)[0]
        self.infotoken = token
        if self.debug: print(f"DEBUG: Got info token {token}")
        return token

    def login(self):
        self.get_token()
        r = requests.post(self.url + 'login.php', data={"token": self.token, "password": self.password})
        self.session = r.cookies['webui-session']
        if self.debug: print(f"DEBUG: Logged in with session {self.session}")
        self.get_info_token()

    def get_data(self) -> dict:
        if not (self.token and self.session and self.infotoken):
            print("ERROR: Attempted to get data with no session or tokens")
            quit()
        r = requests.post(self.url + 'info-async.php', data='do=full&token=' + self.infotoken, cookies={'webui-session': self.session })
        if r.status_code != 200:
            print('ERROR:')
            print(r.status_code)
            print(r.content)
            self.json = ""
            return {}
        else:
            self.json = r.json()
            self.time = datetime.now().strftime("%H:%M:%S")
            self.get_MACs()
            return self.json

    def check_data(self) -> None:
        if self.json == "":
            print('ERROR: No Data')
            quit()

    def get_MACs(self) -> None:
        #print(self.json[0])
        for mac in self.json[0]:
            self.main = mac
            break
        try:
            for child in self.json[0][self.main]:
                #print(f"CHILD: {child}")
                for t in self.json[0][self.main][child]:
                    #print(f"TYPE: {t}")
                    for mac in self.json[0][self.main][child][t]:
                        #print(f"MAC: {mac}")
                        self.mesh = mac
                        break
                    break
                break
        except:
            self.mesh = None
        #print(self.main, self.mesh)

    def get_wifi_data(self) -> dict:
        self.check_data()
        db = {}
        for rmac in self.json[1]:
            for net in self.json[1][rmac]:
                for t in self.json[1][rmac][net]:
                    for mac in self.json[1][rmac][net][t]:
                        if "Internal" not in t: # ignore internal net devices (mesh connection)
                            db[mac] = self.json[1][rmac][net][t][mac]
                            if "Device" in t:
                                db[mac]['Type'] = "DS"
                            elif "Guest" in t:
                                db[mac]['Type'] = "G"
                            else:
                                db[mac]['Type'] = "U"
                            if "2.4" in net:
                                db[mac]['Band'] = "2.4"
                            else:
                                db[mac]['Band'] = "5"
                            if self.main == rmac:
                                db[mac]['Router'] = 'Main'
                            elif self.mesh == rmac:
                                db[mac]['Router'] = 'Mesh'
                            else:
                                print("Error: Unknown router source??")
                            #print(f"DEBUG: The mac is {mac} and the net is {net} on type {t}")
        self.wifidb = db
        return db

    def get_ethernet_data(self) -> dict:
        self.check_data()
        db = {}
        for mac in self.json[2]:
            if self.json[2][mac]['connection'] == 'ethernet':
                db[mac] = self.json[2][mac]
                ''' Ethernet has no peer
                if self.main == self.json[2][mac]['peer']:
                    db[mac]['Router'] = 'Main'
                elif self.mesh == self.json[2][mac]['peer']:
                    db[mac]['Router'] = 'Mesh'
                else:
                    print("Error: Unknown router source??")
                #print(self.json[2][mac]['description'])
                '''
        #print(db)
        self.ethernetdb = db
        self.ethernetdevices = len(db)
        return db

    def parse_all(self):
        self.get_wifi_data()
        self.get_ethernet_data()

    def data_use_to_csv(self, file: str) -> None:
        db = self.get_wifi_data()
        with open(file, 'w', encoding='utf8', newline='') as f:
            csvwriter = csv.writer(f)
            for k in db:
                csvwriter.writerow([k, db[k]['Description'], db[k]['TxBytes'], db[k]['RxBytes']])

    def check_join(self, prev: dict, t: str) -> list:
        l = []
        if t == 'w':
            db = self.wifidb
        else:
            db = self.ethernetdb
        for key1 in db:
            if key1 not in prev:
                l.append(key1)
        return l

    def check_leave(self, prev: dict, t: str) -> list:
        l = []
        if t == 'w':
            db = self.wifidb
        else:
            db = self.ethernetdb
        for key1 in prev:
            if key1 not in db:
                l.append(key1)
        return l    

    def network_monitor(self, interval: int, sound: bool, file: bool, ignore: str, exp: bool) -> None:
        if ignore == None:
            ignore = "NULL"
        #print(ignore)
        self.login()
        self.get_data()
        self.parse_all()
        wifiolddb = self.wifidb
        etholddb = self.ethernetdb
        #print(f"Wifi: {wific}, Eth: {ethc}")
        while True:
            #print("==========NEW LOOP==========")
            now = datetime.now().strftime(r"%m-%d-%Y")
            s = []
            try:
                self.get_data()
            except:
                self.login()
                self.get_data()
            self.parse_all()
            wifinew = self.check_join(wifiolddb, 'w')
            ethnew = self.check_join(etholddb, 'e')
            wifileave = self.check_leave(wifiolddb, 'w')
            ethleave = self.check_leave(etholddb, 'e')
            #print(wifinew)
            #print(wifileave)
            for newmac in wifinew:
                if sound: chime.info()
                try:
                    #print(f"Wifi device {self.wifidb[newmac]['Description']} ({self.wifidb[newmac]['Address']}) joined @ {self.time} +-{interval}s")
                    if ignore in self.wifidb[newmac]['Description']: 
                        continue
                    s.append(f"{self.wifidb[newmac]['Router']} {self.wifidb[newmac]['Band']}GHz {self.wifidb[newmac]['Type']}: Wifi device {self.wifidb[newmac]['Description']} ({self.wifidb[newmac]['Address']}) joined @ {self.time} +-{interval}s\n")
                except KeyError:
                    try:
                        s.append(f"{self.wifidb[newmac]['Router']} {self.wifidb[newmac]['Band']}GHz {self.wifidb[newmac]['Type']}: Wifi device {self.wifidb[newmac]['HostName']} ({self.wifidb[newmac]['Address']}) joined @ {self.time} +-{interval}s\n")
                    except KeyError:
                        s.append(f"Wifi device joined with MAC {newmac}")
            for newmac in ethnew:
                if sound: chime.info()
                try:
                    s.append(f"Ethernet device {self.ethernetdb[newmac]['description']} ({self.ethernetdb[newmac]['ip']}) joined @ {self.time} +-{interval}s\n")
                except KeyError:
                    try:
                        s.append(f"Ethernet device {self.ethernetdb[newmac]['host_name']} ({self.ethernetdb[newmac]['ip']}) joined @ {self.time} +-{interval}s\n")
                    except KeyError:
                        s.append(f"Ethernet device joined with MAC {newmac}")
            for newmac in wifileave:
                if sound: chime.error()
                try:
                    if ignore in wifiolddb[newmac]['Description']: continue
                    s.append(f"{wifiolddb[newmac]['Router']} {wifiolddb[newmac]['Band']}GHz {wifiolddb[newmac]['Type']}: Wifi device {wifiolddb[newmac]['Description']} ({wifiolddb[newmac]['Address']}) left @ {self.time} +-{interval}s\n")
                except KeyError:
                    try:
                        s.append(f"{wifiolddb[newmac]['Router']} {wifiolddb[newmac]['Band']}GHz {wifiolddb[newmac]['Type']}: Wifi device {wifiolddb[newmac]['HostName']} ({wifiolddb[newmac]['Address']}) left @ {self.time} +-{interval}s\n")
                    except KeyError:
                        s.append(f"Wifi device left with MAC {newmac}")
            for newmac in ethleave:
                if sound: chime.error()
                try:
                    s.append(f"Ethernet device {etholddb[newmac]['description']} ({etholddb[newmac]['ip']}) left @ {self.time} +-{interval}s\n")
                except KeyError:
                    try:
                        s.append(f"Ethernet device {etholddb[newmac]['host_name']} ({etholddb[newmac]['ip']}) left @ {self.time} +-{interval}s\n")
                    except KeyError:
                        s.append(f"Ethernet device left with MAC {newmac}")
            for mac in self.wifidb:
                try:
                    if ignore in self.wifidb[mac]['Description']: continue
                except:
                    pass
                try:
                    if self.wifidb[mac]['TxBytes_60sec'] > 50000000: # 50 MB, upstream has less bandwidth capacity
                        if sound: chime.warning()
                        s.append(f"{self.wifidb[mac]['Router']} {self.wifidb[mac]['Band']}GHz {self.wifidb[mac]['Type']}: Wifi device {self.wifidb[mac]['Description']} is slamming the upstream with {round(self.wifidb[mac]['TxBytes_60sec'] / self.GIG, 4)} GBTx/60s @ {self.time}\n")
                except KeyError:
                    try:
                        if self.wifidb[mac]['TxBytes_60sec'] > 50000000: # 50 MB, upstream has less bandwidth capacity
                            if sound: chime.warning()
                            s.append(f"{self.wifidb[mac]['Router']} {self.wifidb[mac]['Band']}GHz {self.wifidb[mac]['Type']}: Wifi device {self.wifidb[mac]['HostName']} is slamming the upstream with {round(self.wifidb[mac]['TxBytes_60sec'] / self.GIG, 4)} GBTx/60s @ {self.time}\n")
                    except KeyError:
                        pass
                try:
                    if self.wifidb[mac]['RxBytes_60sec'] > 500000000: # 500 MB
                        if sound: chime.warning()
                        s.append(f"{self.wifidb[mac]['Router']} {self.wifidb[mac]['Band']}GHz {self.wifidb[mac]['Type']}: Wifi device {self.wifidb[mac]['Description']} is slamming the downstream with {round(self.wifidb[mac]['RxBytes_60sec'] / self.GIG, 4)} GBRx/60s @ {self.time}\n")
                except KeyError:
                    try:
                        if self.wifidb[mac]['RxBytes_60sec'] > 500000000: # 500 MB
                            if sound: chime.warning()
                            s.append(f"{self.wifidb[mac]['Router']} {self.wifidb[mac]['Band']}GHz {self.wifidb[mac]['Type']}: Wifi device {self.wifidb[mac]['HostName']} is slamming the downstream with {round(self.wifidb[mac]['RxBytes_60sec'] / self.GIG, 4)} GBRx/60s @ {self.time}\n")
                    except KeyError:
                        pass
                try:
                    if self.wifidb[mac]['SignalQuality'] < 60 and self.wifidb[mac]['SignalQuality'] - wifiolddb[mac]['SignalQuality'] > 10:
                        if sound: chime.warning()
                        s.append(f"{self.wifidb[mac]['Router']} {self.wifidb[mac]['Band']}GHz {self.wifidb[mac]['Type']}: Wifi device {self.wifidb[mac]['Description']} has poor signal quality {self.wifidb[mac]['SignalQuality']} @ {self.time}\n")
                except KeyError:
                    try:
                        if self.wifidb[mac]['SignalQuality'] < 60 and self.wifidb[mac]['SignalQuality'] - wifiolddb[mac]['SignalQuality'] > 10:
                            if sound: chime.warning()
                            s.append(f"{self.wifidb[mac]['Router']} {self.wifidb[mac]['Band']}GHz {self.wifidb[mac]['Type']}: Wifi device {self.wifidb[mac]['HostName']} has poor signal quality {self.wifidb[mac]['SignalQuality']} @ {self.time}\n")
                    except KeyError:
                        pass
                if exp:
                    try:
                        if self.wifidb[mac]['RxBytes'] < 1000:
                            s.append(f"EXP: Wifi device {self.wifidb[mac]['Description']} has low RxBytes value ({self.wifidb[mac]['RxBytes']}) with lease {self.wifidb[mac]['LeaseValidity']}s @ {self.time}\n")
                    except KeyError:
                        pass
            for line in s:
                print(line, end='')
            if file and s:
                filename = now + '-netlog.txt'
                with open(filename, 'a+', encoding='utf8', newline='') as f:
                    f.writelines(s)
            wifiolddb = self.wifidb
            etholddb = self.ethernetdb
            time.sleep(interval)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='alien_monitor.py',
                                    description='Monitors connections and disconnections from your Amplifi Alien network')
    parser.add_argument('ip', action='store', type=str, help="The ip address of your main Amplifi Alien Router")
    parser.add_argument('password', action='store', type=str, help="The password to your router")
    parser.add_argument('-v','--verbose', action='store_true', help="Enable debug messages")
    parser.add_argument('-i','--interval', action='store', type=int, default=10, help="Interval to get data from router in seconds (default is 10)")
    parser.add_argument('-o','--outfile', action='store_true', help="Saves log in current directory, will append if file exists (Month-Day-Year-netlog.txt)")
    parser.add_argument('-s','--sound', action='store_true', help="Enable sounds for device updates and warnings (Requires chime library)")
    parser.add_argument('-b','--block', action='store', type=str, help="Will not record or print info for devices containing this string")
    parser.add_argument('-e','--exp', action='store_true', help="Enable expiremental features")

    args = parser.parse_args()
    if args.sound:
        import chime
        chime.theme('material')
    #print(args)
    ag = AmplifiGather(args.ip, args.password, args.verbose)
    ag.network_monitor(args.interval, args.sound, args.outfile, args.block, args.exp)
