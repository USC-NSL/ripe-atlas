#!/usr/bin/python
from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer
import atlas_traceroute
import atlas_retrieve
import urllib
import datetime
import tempfile
import os
import sys
import threading
import glob
import json
import itertools

active_probes_url = 'https://atlas.ripe.net/api/v1/probe/?limit=10000&format=txt'
active_file = 'atlas-active-%d-%d-%d'

class TracerouteService(object):
    
    def __init__(self, port, api_key):
        self.last_active_date = datetime.datetime(1, 1, 1) 
        self.probes = None
        self.port = port
        self.key = api_key
        self.lock = threading.RLock()

    def submit(self):
        return 'submit'

    def status(self, measurement_id):
        """
        May be one of
          0: Specified
          1: Scheduled
          2: Ongoing
          4: Stopped
          5: Forced to stop
          6: No suitable probes
          7: Failed
          8: Archived
        """
        retrieve = atlas_retrieve.Retrieve([measurement_id], self.key)
        return retrieve.check_status()

    def active(self, asn = None):
        
        if asn is None:
            #flatten list of lists. this is magick.
            return list(itertools.chain(*self.probes.values()))
        else:
            try:
                return self.probes[asn]
            except KeyError:
                return []       #return empty list if this asn is not found

    def ases(self):
        return self.probes.keys()

    def results(self, measurement_id):
        retrieve = atlas_retrieve.Retrieve([measurement_id], self.key)
        return retrieve.fetch_traceroute_results()

    def check_active_probes(self):

        tempdir = tempfile.gettempdir()
        now = datetime.datetime.now()

        if self.probes is None:
            #this should only happen when we first start up
            
            active_probe_list = glob.glob(tempdir+os.sep+'atlas-active-*')
            active_probe_list.sort()

            if len(active_probe_list) > 0:
                most_recent_file = active_probe_list[-1]
                print('Most recent active probe file found: '+most_recent_file)

                basename = os.path.basename(most_recent_file)
                chunks = basename.split('-')

                year = int(chunks[2])
                month = int(chunks[3])
                day = int(chunks[4])

                most_recent_date = datetime.datetime(year, month, day)

                timediff = now - most_recent_date
                if timediff.days < 1:
                    self.load_probes(most_recent_file)
                    self.last_active_date = most_recent_date
                    return
            else:
                print('No active-probe files found')
        
        #first check that we have the latest file for today
        timediff = now - self.last_active_date
        if timediff.days >= 1:
        
            save_file_name = active_file % (now.year, now.month, now.day)
            save_file_path = '%s%s%s' % (tempdir, os.sep, save_file_name)
            #fetch new active file
            print('Fetching new active probe file to: '+save_file_path)
            urllib.urlretrieve(active_probes_url, save_file_path)
            print('Finished fetching')

            self.load_probes(save_file_path)
            self.last_active_date = now #update latest time we fetched
            
            return
        
        #file_name = active_file % (self.last_active_date.year, self.last_active_date.month, self.last_active_date.day)
        #file_path = '%s%s%s' % (tempdir, os.sep, file_name)
        #if not os.path.exists(file_path):
        #    urllib.urlretrieve(active_probes_url, file_path)
        #    self.last_active_date = now #update latest time we fetched
        #    self.load_probes(file_path)
        #    return

    def load_probes(self, file):
        
        f = open(file)
        probe_data = f.read()
        f.close()

        all_probes = json.loads(probe_data)

        #all_probes['meta'] #not using this right now
        active_probes = {}

        probes_dict = all_probes['objects']
        print('Processing '+str(len(probes_dict))+' probes')
        
        for probe in probes_dict:
            try:
                id = probe['id']
                status = probe['status_name']
                #prefix = probe['prefix_v4']
                #country = probe['country_code']
                asn = probe['asn_v4']
                
                if status == 'Connected':
                    try:
                        active_probes[asn].append(id)
                    except KeyError:
                        active_probes[asn] = [id]
            except:
                traceback.print_exc(file=sys.stdout)
                continue

        self.probes = active_probes

        num_probes = sum(len(l) for l in self.probes.values())
        print('Loaded: '+file+' with '+str(num_probes)+' active probes')

    def run(self):

        self.check_active_probes()

        server = SimpleJSONRPCServer(('localhost', self.port))

        server.register_function(self.ases, 'ases')
        server.register_function(self.submit, 'submit')
        server.register_function(self.active, 'active')
        server.register_function(self.results, 'results')
        server.register_function(self.status, 'status')

        server.serve_forever()


if __name__ == '__main__':
    
    if len(sys.argv) != 3:
        sys.stderr.write('Usage: <port> <key>\n')
        sys.exit(1)

    port = int(sys.argv[1])
    key = sys.argv[2]

    service = TracerouteService(port, key)
    service.run()
