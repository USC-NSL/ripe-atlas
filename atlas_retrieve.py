#!/usr/bin/python
import json
import os
import sys
import time
import requests

class Retrieve(object):

    URL = 'https://atlas.ripe.net/api/v1/measurement/'
    
    def __init__(self, measurement_ids, key):
        self.measurement_ids = measurement_ids
        self.key = key

    def check_status(self):

        status_list = list()
        headers =  {'accept': 'application/json'}

        for measurement_id in self.measurement_ids:
            
            response = requests.get("%s/%s/?key=%s" % (Retrieve.URL, measurement_id, self.key), headers=headers)
            response_str = response.text

            results = json.loads(response_str)
            status = results['status']['name']
            
            status_list.append((measurement_id, status))

        return status_list

    def fetch_results(self):

        headers =  {'accept': 'application/json'}
        results_list = list()

        for measurement_id in self.measurement_ids:
            
            response = requests.get("%s/%s/result/?key=%s" % (Retrieve.URL, measurement_id, self.key), headers=headers)
            response_str = response.text
            
            results = json.loads(response_str)            
            results_list.append((measurement_id, results))

        return results_list

    def fetch_traceroute_results(self):
        #offer simplified result
        fetched_results = self.fetch_results()
        processed_results = []

        for (m_id, data) in fetched_results:

            for traceroute in data:
                hop_list = []
                target = traceroute['dst_name']
                hop_data_list = traceroute['result']
            
                #hop_data_list = data[0]['result']
                for hop_data in hop_data_list:
                    hop_num = hop_data['hop']
                    hop = hop_data['result'][0]

                    if 'from' in hop: #if this hop had a response
                        host = hop['from']
                        rtt = hop['rtt']
                        ttl = hop['ttl']
                        hop_list.append((hop_num, (host, rtt, ttl)))
                    else:
                        hop_list.append((hop_num, ('* * *', 0, 0)))

                hop_list.sort()
                hop_list = [x[1] for x in hop_list]
                processed_results.append((m_id, target, hop_list))

        return processed_results
            
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

"""
if __name__ == '__main__':

    authfile = "%s/.atlas/auth" % os.environ['HOME']

    if not os.path.exists(authfile):
        raise CredentialsNotFound(authfile)

    auth = open(authfile)
    key = auth.readline()[:-1]
    auth.close()

    if len(sys.argv) != 2:
        sys.stderr.write("Usage: <measurement_id_file>\n")
        sys.exit(1)

    measurement_file = sys.argv[1]

    measurement_ids = set()

    f = open(measurement_file)
    for line in f:
        id = line.strip()
        measurement_ids.add(id)
    f.close()

    fetch_results(measurement_ids)
"""
