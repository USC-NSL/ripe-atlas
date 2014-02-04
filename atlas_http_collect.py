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

    def __init__(self, username, password, input_file):
        self.username = username
        self.password = password

        self.cookiejar = cookielib.LWPCookieJar()
        self.cookiejar.load(cookie_filename)

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
        

        inputs = list()
        f = open(file)
        for line in f:
            description = line.strip()
            inputs.append(description)
        f.close()
    
        for desc in inputs:
            measurement_ids = self.collect(desc)
            for m_id in measurement_ids:
                jayson = self.fetch_measurement(m_id)
                print(jayson)


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

    def collect(self, description):
        
        millis = int(round(time.time()*1000))
        
        data = {}
        data['_dc'] = str(millis)
        data['start'] = '0'
        data['limit'] = '1000'
        data['sort'] = 'msm_id'
        data['dir'] = 'ASC'
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

    if len(sys.argv) != 4:
        sys.stderr.write('Usage: <username> <password> <description-file>\n')
        sys.exit(1)

    filename = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]

    test = Atlas(username, password, filename)
