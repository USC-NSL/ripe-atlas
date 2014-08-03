#!/usr/bin/python
import sys
import requests
import json

class Retrieve(object):

    URL = 'https://atlas.ripe.net/api/v1/measurement'
    
    def __init__(self, measurement_id, key=None, start=None, stop=None, sess=None):
        self.measurement_id = measurement_id
        self.key = key
        self.start = start
        self.stop = stop
        self.sess = sess if sess else requests

    def check_status(self): 
        
        """
        It turns out that the data is actually available way before the status
        page is updated so we check that first. If the returned result list is 
        not empty then we assume the measurement is complete and has been successful.
        """
        #looks like byte range is currently not accepted
        fetch_headers = {'accept':'application/json', 'range':'bytes=0-2'} 
        results = self.fetch_results(fetch_headers)
        if len(results) > 0: #lolhax
            return 'Stopped'

        #fall back to status request
        status_list = list()
        headers =  {'accept': 'application/json'}
        
        req_url = '%s/%s/%s' % (Retrieve.URL, self.measurement_id, '?fields=status')
        if self.key:
            req_url += '&key=%s' % self.key
        
        response = self.sess.get(req_url, headers=headers)
        response_str = response.text

        results = json.loads(response_str)
        status = results['status']['name']

        return status
    
    def fetch_results(self, headers={'accept':'application/json'}):

        req_url = '%s/%s/result/?' % (Retrieve.URL, self.measurement_id) 
        if self.start and self.stop:
            req_url += '&start=%d&stop=%d' % (self.start, self.stop)
        if self.key:
            req_url += '&key=%s' % self.key

        response = self.sess.get(req_url, headers=headers)
        response_str = response.text
            
        results = json.loads(response_str)

        return results

if __name__ == '__main__':
    
    if len(sys.argv) != 2:
        sys.stderr.write('Usage: mid-file\n')
        sys.exit(1)

    mfile = sys.argv[1]
    f = open(mfile)
    for line in f:
        mid = line.strip()
        r = Retrieve(mid)
        status = r.check_status()
        print('%s %s' % (mid, status))
    f.close() 
