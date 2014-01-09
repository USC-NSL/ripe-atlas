#!/usr/bin/python
from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer
from SocketServer import ForkingMixIn
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
import logging
import logging.config

ACTIVE_PROBES_URL = 'https://atlas.ripe.net/api/v1/probe/?limit=10000&format=txt'
ACTIVE_FILE = 'atlas-active-%d-%d-%d'

class SimpleForkingJSONRPCServer(ForkingMixIn, SimpleJSONRPCServer):
    pass

class TracerouteService(object):
    
    def __init__(self, port, api_key):
        self.logger = logging.getLogger(__name__)
        self.last_active_date = datetime.datetime(1, 1, 1) 
        self.probes = None
        self.port = port
        self.key = api_key
        self.lock = threading.RLock()

    def submit(self, probe_list, target):
        try:
            self.logger.info('Got submit request for target %s with %s probes' % (target, str(probe_list)))

            tr = atlas_traceroute.Traceroute(target, self.key)
            tr.num_probes = len(probe_list)
            tr.probe_type = 'probes'
            tr.probe_value = map(int, probe_list)

            response = tr.run()
            self.logger.info('Atlas response %s' % (str(response)))

            return_value = None
            if 'error' in response:
                error_details = response['error']
                code = error_details['code']
                message = error_details['message']
                return_value = ('error', message+' code: '+str(code))
            elif 'measurements' in response:
                measurement_list = response['measurements']
                measurement_list_str = map(str, measurement_list)
                return_value = ('success', '\n'.join(measurement_list_str))
            else:
                return_value = ('error', 'Error processing response: '+str(response))

            self.logger.info('submit returning (%s, %s)' % return_value)
            return return_value
        except Exception, e:
            self.logger.error('Got exception for submit request for target %s with %s probes' % 
                              (target, str(probe_list)), exc_info=True)
            raise e

    def status(self, measurement_id):
        try:
            self.logger.info('Got status request for measurement_id %d' % (measurement_id))
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
        except Exception, e:
            self.logger.error('Got exception for status with measurement_id %d' % measurement_id, exc_info=True)
            raise e

    def active(self, asn = None):
        try:
            self.logger.info('Got active request for asn: %s' % str(asn))

            if asn is None:
                #flatten list of lists. this is magick.
                return list(itertools.chain(*self.probes.values()))
            else:
                try:
                    return self.probes[asn]
                except KeyError:
                    return []       #return empty list if this asn is not found
        except Exception, e:
            self.logger.error('Got exception with active request for asn %s' % str(asn), exc_info=True)
            raise e

    def ases(self):
        try:
            self.logger.info('Got ases request')
            return self.probes.keys()
        except Exception, e:
            self.logger.error('Got exception for ases request', exc_info=True)
            raise e

    def results(self, measurement_id):
        try:
            self.logger.info('Got results request for measurement_id: %d' % measurement_id)
            retrieve = atlas_retrieve.Retrieve([measurement_id], self.key)
            results = retrieve.fetch_traceroute_results()
            #logger.info('measurementid: %d results: %s' % (measurement_id, str(results)))
            return results
        except Exception, e:
            self.logger.error('Got exception for results request for measurement_id: %d' % measurement_id, exc_info=True)
            raise e
    #
    #
    #

    def check_active_probes(self):

        tempdir = tempfile.gettempdir()
        now = datetime.datetime.now()

        if self.probes is None:
            self.logger.info('No probes configured')
            #this should only happen when we first start up
            
            active_probe_list = glob.glob(tempdir+os.sep+'atlas-active-*')
            active_probe_list.sort()

            if len(active_probe_list) > 0:
                most_recent_file = active_probe_list[-1]
                self.logger.info('Most recent active probe file found: '+most_recent_file)

                basename = os.path.basename(most_recent_file)
                chunks = basename.split('-')

                year = int(chunks[2])
                month = int(chunks[3])
                day = int(chunks[4])

                most_recent_date = datetime.datetime(year, month, day)

                timediff = now - most_recent_date
                if timediff.days < 1:
                    try:
                        self.load_probes(most_recent_file)
                        self.last_active_date = most_recent_date
                        self.logger.info('last_active_date for probe file is %s' % self.last_active_date)
                    except Exception, e:
                        self.logger.error('Failed to load %s' % most_recent_file, exc_info=True)
                        self.logger.error('Fetching new file instead')
                        self.fetch_new_probefile()
                    return
                else:
                    self.logger.info('Most recent file was out of date')
            else:
                self.logger.info('No active-probe files found')
        
        #first check that we have the latest file for today
        timediff = now - self.last_active_date
        if timediff.days >= 1:
            self.fetch_new_probefile()    
            return

    def fetch_new_probefile(self):

        now = datetime.datetime.now()
        tempdir = tempfile.gettempdir()

        save_file_name = ACTIVE_FILE % (now.year, now.month, now.day)
        save_file_path = '%s%s%s' % (tempdir, os.sep, save_file_name)
        #fetch new active file
        self.logger.info('Fetching new active probe file to: '+save_file_path)
        urllib.urlretrieve(ACTIVE_PROBES_URL, save_file_path)
        self.logger.info('Finished fetching')

        self.load_probes(save_file_path)
        self.last_active_date = now #update latest time we fetched
        self.logger.info('last_active_date for probe file is %s' % self.last_active_date)

    def load_probes(self, file):
        
        f = open(file)
        probe_data = f.read()
        f.close()

        all_probes = json.loads(probe_data)

        #all_probes['meta'] #not using this right now
        active_probes = {}

        probes_dict = all_probes['objects']
        self.logger.info('Processing '+str(len(probes_dict))+' probes')
        
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
        self.logger.info('Loaded: '+file+' with '+str(num_probes)+' active probes')

    def run(self):

        self.check_active_probes()

        server = SimpleForkingJSONRPCServer(('', self.port))

        server.register_function(self.ases, 'ases')
        server.register_function(self.submit, 'submit')
        server.register_function(self.active, 'active')
        server.register_function(self.results, 'results')
        server.register_function(self.status, 'status')

        self.logger.info('Starting service on port: %d' % self.port)
        server.serve_forever()

def setup_logging(default_path='logging.json', default_level=logging.INFO, env_key='LOG_CFG'):
    """
    Setup logging configuration
    """
    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)

if __name__ == '__main__':
    
    if len(sys.argv) != 3:
        sys.stderr.write('Usage: <port> <key>\n')
        sys.exit(1)

    port = int(sys.argv[1])
    key = sys.argv[2]

    setup_logging()

    service = TracerouteService(port, key)
    service.run()
