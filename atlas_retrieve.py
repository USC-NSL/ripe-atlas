#!/usr/bin/python
import json
import os
import sys
import time
import requests

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

    def fetch_traceroute_results(self):
        #offer simplified result
        fetched_result = self.fetch_results()

        processed_results = []
        for traceroute in fetched_result:
            hop_list = []
            
            target = traceroute['dst_name']
            probe_id = traceroute['prb_id']
            hop_data_list = traceroute['result']
            
            #hop_data_list = data[0]['result']
            for hop_data in hop_data_list:
                hop_num = hop_data['hop']

                #hop = hop_data['result'][0]
                hop_found = False
                for hop in hop_data['result']: #usually 3 results for each hop
                    if 'from' in hop: #if this hop had a response
                        host = hop['from']
                        #rtt can sometimes be missing if there was a host 
                        #unreachable error
                        rtt = hop.get('rtt', -1.0)
                        ttl = hop.get('ttl', -1.0)
                        hop_list.append((hop_num, (host, rtt, ttl)))
                        hop_found = True
                        break
                
                #if we didn't find a response for this hop then 
                #fill in with anonymous router
                if not hop_found:
                    hop_list.append((hop_num, ('* * *', 0, 0)))

            hop_list.sort()
            hop_list = [x[1] for x in hop_list]
            
            result = {'status': 'finished', 'target': target, 'probe_id': probe_id, 'hops': hop_list}
            processed_results.append(result)

        return processed_results
    
    def parse_dns_results(self, json_results):
        results = []
        
        for line in json_results.split('\n'):
            line = line.strip()

            record = json.loads(line)

            if 'result' not in record:
                continue

            try:
                probeid = record['prb_id']
                timestamp = record['timestamp']
                r = record['result']

                abuf = r['abuf']
                dnsmsg = dns.message.from_wire(base64.b64decode(abuf))

                for rr in dnsmsg.answer:
                    arecstr = str(rr)
                    a_record_lines = arecstr.split('\n')

                    ip_list = list()

                    for a_record in a_record_lines:
                        a_record_chunks = a_record.split(' ')
                        ip_list.append(a_record_chunks[4])

                    dns_results = ' '.join(ip_list)
                    results.append((probeid, timestamp, dns_results))
            except:
                continue

        return results
        
    def fetch_ping_results(self):

        results = self.fetch_results()

        for (m_id, result) in results:
                
            probeid = result["prb_id"]
            target = result["dst_addr"]
            rtts = []

            for measurement in result["result"]:
                if measurement.has_key("rtt"):
                    rtt = measurement["rtt"]
                    rtts.append(rtt)
                elif measurement.has_key("error"):
                    num_error += 1
                else:
                    sys.stderr.write("measurement: "+m_id+" result has no field rtt and not field error\n")
            
            #TODO finish this


