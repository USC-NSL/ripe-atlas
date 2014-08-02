#!/usr/bin/python
import cookielib
import urllib
import urllib2
import urllib3
import time
import json
import sys
import traceback
from atlas import measure_baseclass

login_url = 'https://access.ripe.net'
udm_url = 'https://atlas.ripe.net/atlas/udm.html'
data_url = 'https://atlas.ripe.net/atlas/udmgrid.json'
cookie_filename = '/tmp/ripeatlas.cookie'
login_test_url = '/atlas/user'
new_url = 'https://atlas.ripe.net/atlas/newudm.json'

class Atlas:

    def __init__(self, username, password, inputfile, connection_pool_size=10):
        self.username = username
        self.password = password
        self.inputfile = inputfile
        self.sleep = 60
        
        self.pool = urllib3.connection_from_url('https://atlas.ripe.net', maxsize=connection_pool_size)
        self.headers = [('User-agent', 'Mozilla/5.0'),
                                  ('Referer', 'https://atlas.ripe.net/atlas/udm.html'),
                                  ('Host', 'atlas.ripe.net'),
                                  ('Origin', 'https://atlas.ripe.net'),
                                  ('X-Requested-With', 'XMLHttpRequest')]
        self.login()
        self.target_dict = measure_baseclass.load_input(self.inputfile)
        
        """
        self.target_list = []
        f = open(self.inputfile)
        for line in f:
            line = line.strip()
            chunks = line.split()
            target = chunks[0]
            probes = chunks[1:]
        
            #if target in self.target_list:
            #    sys.stderr.write('Already saw target %s\n' % target)
            #    continue

            self.target_list.append((target, probes))
        f.close()       
        """

        """
        f = open(self.inputfile)
        for line in f:
            line = line.strip()
            chunks = line.split(' ')
            nodeid = chunks[0]
            targetip = chunks[1]
            self.target_list.append((nodeid, targetip))
        f.close()
        """

    def login(self):

        self.cookiejar = cookielib.LWPCookieJar()
        self.opener = urllib2.build_opener(
            urllib2.HTTPRedirectHandler(),
            urllib2.HTTPHandler(debuglevel=0),
            urllib2.HTTPSHandler(debuglevel=0),
            urllib2.HTTPCookieProcessor(self.cookiejar))
        self.opener.addheaders = self.headers
        
        login_data = urllib.urlencode({
                'username' : self.username,
                'password' : self.password,
         })

        self.opener.open(login_url, login_data)

        for cookie in self.cookiejar:
            if cookie.name == 'crowd.token_key':
                self.token = cookie.value
            elif cookie.name == 'JSESSIONID':
                self.session_id = cookie.value

        if self.token and self.session_id:
            self.headers.append(('Cookie', 'JSESSIONID='+self.session_id+'; crowd.token_key='+self.token+'; csrftoken='+self.token))

    def runall(self, req, description, interval):
        timestr = time.strftime('%Y-%m-%d %H:%M:%S')

        target_len = len(self.target_dict)
        targets = self.target_dict.keys()
        i = 0

        while i < target_len:
            target = targets[i]
            probe_list = self.target_dict[target]

            url = 'http://'+target+'/'+req

            """
            The maxmimum number of probes per requet is 500 so we need to break
            this is up into several requests.
            """
            probe_list_chunks = [probe_list[x:x+500] for x in xrange(0, len(probe_list), 500)]
            for probe_list_chunk in probe_list_chunks:
            
                try:
                    response = self.run(probe_list_chunk, url, description, interval) 
                except:
                    traceback.print_exc(file=sys.stderr)
                    sys.stderr.write('Got some kind of network exception. Sleeping for '+str(self.sleep)+'\n')
                    time.sleep(self.sleep)
                    continue

                if not response['success']:
                    if 'Not authenticated or session is expired' in response['errorMessage']:
                        self.login()                    

                    sys.stderr.write(response['errorMessage']+'\n')
                    sys.stderr.write('Sleeping for '+str(self.sleep)+'\n')
                    time.sleep(self.sleep)
                else:
                    i += 1
                    sys.stderr.write(str(i)+'/'+str(target_len)+'\n')

    def run(self, probe_list, url, description, interval):

        probe_list_str = ','.join(probe_list)
        isoneoff = '"oneoff":"on",' if interval == '-1' else ''
        if interval == '-1':
            interval = '900' #change to something valid

        """ Without oneoff
        {"types":[{"intvl":"900","method":"method_get","httpver":"httpver11","headbytes":"","useragent":"httpget for atlas.ripe.net","url":"http://fi-hel-as3292.anchors.atlas.ripe.net","public":"1","descr":"http://fi-hel-as3292.anchors.atlas.ripe.net","typeid":"httpget"}],"sources":[{"probesreqlist":[4788,4906],"typeid":"probes"}]}
        """

        """ With oneoff
        data:{"oneoff":"on","types":[{"intvl":"900","method":"method_get","httpver":"httpver11","headbytes":"","useragent":"httpget for atlas.ripe.net","url":"http://gr-ath-as5408.anchors.atlas.ripe.net","public":"1","descr":"http://gr-ath-as5408.anchors.atlas.ripe.net","typeid":"httpget"}],"sources":[{"probesreqlist":[3775,3992],"typeid":"probes"}]}
        """

        data = {}
        data['csrfmiddlewaretoken'] = self.token
        data['data'] = '{%s"types":[{"intvl":"%s","method":"method_get","httpver":"httpver11","headbytes":"","useragent":"Mozilla","url":"%s","public":"1","descr":"%s","typeid":"httpget"}],"sources":[{"probesreqlist":[%s],"typeid":"probes"}]}' % (isoneoff, interval, url, description, probe_list_str)
        
        response = self.pool.request('POST', new_url, data, self.headers)
        response_str = response.data
        return json.loads(response_str)

if __name__ == '__main__':

    if len(sys.argv) != 7:
        sys.stderr.write('Usage: <username> <password> <probeid-ip-file> <request (search?q=dogs)> <collection-identifier> <repeat-interval-secs (-1 for one off)>\n')
        sys.exit(1)

    user = sys.argv[1]
    password = sys.argv[2]
    probe_file = sys.argv[3]
    req = sys.argv[4]
    description = sys.argv[5]
    repeat_interval = sys.argv[6]

    http = Atlas(user, password, probe_file)
    http.runall(req, description, repeat_interval)
