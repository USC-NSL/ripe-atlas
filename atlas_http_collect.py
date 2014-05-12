#!/usr/bin/python
import cookielib
import urllib
import urllib2
import time
import json
import sys

login_url = 'https://access.ripe.net'
udm_url = 'https://atlas.ripe.net/atlas/udm.html'
data_url = 'https://atlas.ripe.net/atlas/udmgrid.json'
cookie_filename = '/tmp/ripeatlas.cookie'
result_url = 'https://atlas.ripe.net/api/v1/measurement/'
login_test_url = 'https://atlas.ripe.net/atlas/user'

class Atlas:

    def __init__(self, username, password):
        self.username = username
        self.password = password

        self.cookiejar = cookielib.LWPCookieJar()
        try:
            self.cookiejar.load(cookie_filename)
        except:
            pass

        self.opener = urllib2.build_opener(
            urllib2.HTTPRedirectHandler(),
            urllib2.HTTPHandler(debuglevel=0),
            urllib2.HTTPSHandler(debuglevel=0),
            urllib2.HTTPCookieProcessor(self.cookiejar))
        self.opener.addheaders = [('User-agent', 'Mozilla/5.0'),
                                  ('Referer', 'https://atlas.ripe.net/atlas/udm.html'),
                                  ('Host', 'atlas.ripe.net'),
                                  ('X-Requested-With', 'XMLHttpRequest')
                                  ]

        sys.stderr.write('Checking if logged in...')
        if not self.loggedin():
            sys.stderr.write('No. Logging in.\n')
            self.login()
            self.cookiejar.save(cookie_filename, ignore_discard=True, ignore_expires=True)
        else:
            sys.stderr.write('Yep.\n')
    
    def loggedin(self):
        response = self.opener.open(login_test_url)
        resp_str = ''.join(response.readlines())
        
        if 'Forgot your password?' in resp_str:
            return False
        else:
            return True

    def login(self):
        login_data = urllib.urlencode({
                'username' : self.username,
                'password' : self.password,
         })

        self.opener.open(login_url, login_data)

    def collect(self, description, mtype):
        
        millis = int(round(time.time()*1000))
        
        data = {}
        data['_dc'] = str(millis)
        data['start'] = '0'
        data['limit'] = '10000'
        data['sort'] = 'msm_id'
        data['dir'] = 'ASC'

        if mtype == 'oneoff':
            data['filter'] = '[{"type":"list","value":["oneoff",8],"field":"type"},{"type":"string","value":"'+description+'","field":"descr"}]'
        elif mtype == 'repeating':
            data['filter'] = '[{"type":"list","value":[1,2],"field":"status"},{"type":"string","value":"'+description+'","field":"descr"}]'
        else:
            data['filter'] = '[{"type":"string","value":"'+description+'","field":"descr"}]'
         

        url_values = urllib.urlencode(data)
        
        url = data_url+'?'+url_values

        response = self.opener.open(url)
        s = ''.join(response.readlines())
        j = json.loads(s)

        measurements = j['data']
        measurement_ids = [ m['msm_id'] for m in measurements ]

        return measurement_ids

    def fetch_measurement(self, measurement_id):
        url = result_url+str(measurement_id)+'/result/'
        response = self.opener.open(url)
        s = ''.join(response.readlines())
        #j = json.loads(s)
        return s


if __name__ == '__main__':

    if len(sys.argv) != 5:
        sys.stderr.write('Usage: <username> <password> <description> <all|oneoff|repeating>\n')
        sys.exit(1)

    username = sys.argv[1]
    password = sys.argv[2]
    description = sys.argv[3]
    mtype = sys.argv[4]
    mtype = mtype.lower()
    
    if mtype != 'all' and mtype != 'oneoff' and mtype != 'repeating':
        sys.stderr.write('last arg must be one of all, oneoff or repeating\n')
        sys.exit(1)

    test = Atlas(username, password)
    measurement_ids = test.collect(description, mtype)
    
    str_ids = map(str, measurement_ids)
    output = '\n'.join(str_ids)
    print(output)

