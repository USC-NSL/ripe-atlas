#!/usr/bin/python
import json
import sys
import traceback
import os
import requests
import argparse

SLEEP_TIME = 60
debug = False
key_loc = '~/.atlas/auth'

class MeasurementBase(object):

    def __init__(self, target, key, probe_list=None, sess=None):
        
        self.target = target
        self.description = ''
        self.af = 4
        self.is_oneoff = True
        self.resolve_on_probe = True
        
        self.key = key
        self.sess = sess if sess else requests

        if probe_list:
            self.num_probes = len(probe_list)
            self.probe_type = 'probes'
            self.probe_value = setup_probe_value('probe_type', probe_list)

    def setup_definitions(self):
    
        definitions = {}
        definitions['target'] = self.target
        definitions['description'] = self.description
        definitions['af'] = self.af #set ip version 
        definitions['type'] = self.measurement_type
        definitions['is_oneoff'] = str(self.is_oneoff).lower()
        definitions['resolve_on_probe'] = str(self.resolve_on_probe).lower()
        
        return definitions

    def setup_probes(self):

        probes = {}
        probes['requested'] = self.num_probes
        probes['type'] = self.probe_type
        probes['value'] = self.probe_value

        return probes

    def run(self):

        key = self.key
        
        definitions = self.setup_definitions()
        probes = self.setup_probes()

        data = {'definitions': [definitions], 'probes': [probes]}
        data_str = json.dumps(data) 

        headers =  {'content-type': 'application/json', 'accept': 'application/json'}
    
        response = self.sess.post('https://atlas.ripe.net/api/v1/measurement/?key='+key, data_str, headers=headers)
        response_str = response.text

        return json.loads(response_str)

def readkey(keyfile=key_loc):
    auth_file = os.path.expanduser(keyfile)
    f = open(auth_file)
    key = f.read().strip()
    f.close()
    
    if len(key) <= 0:
        sys.stderr.write('Meaurement key is too short!\n')

    return key

def setup_probe_value(type, arg_values):
        """
        type is the probe type.
        arg_values is a list of args passed in by user
        """

        if type == 'asn' or type == 'msm':
            return int(arg_values[0])   #return an integer value
        elif type == 'probes':
            arg_values = map(str, arg_values)
            return ','.join(arg_values) #return command separated list of probe ids
        else:
            return arg_values[0]        #for everything else just return single item from list

def load_input(inputfile):
    target_dict = {}

    f = open(inputfile)
    for line in f:
        line = line.strip()

        if not line: #empty
            continue

        chunks = line.split(' ')
        nodeid = chunks[0]
        targetip = chunks[1]

        try:
            target_dict[targetip].append(nodeid)
        except KeyError:
            target_dict[targetip] = [nodeid]

    f.close()

    return target_dict

def process_response(response):
    if 'error' in response:
        error_details = response['error']
        code = error_details['code']
        message = error_details['message']
        #return a tuple with error message and code
        return 'error', '%s code: %d' % (message, code) 
    elif 'measurements' in response:
        measurement_list = response['measurements']
        return 'ok', measurement_list
    else:
        return 'error', 'Unknown response: %s' % str(response)

def format_response(response):
    
    if 'error' in response:
        error_details = response['error']
        code = error_details['code']
        message = error_details['message']
        return message+' code: '+str(code)
    elif 'measurements' in response:
        measurement_list = response['measurements']
        measurement_list_str = map(str, measurement_list)
        return '\n'.join(measurement_list_str)
    else:
        return 'Error processing response: '+str(response)

def config_argparser():

    parser = argparse.ArgumentParser()
        
    parser.add_argument('-d', '--description', default=[''], nargs=1, help='measurement description (default: empty)')
    parser.add_argument('-k', '--key-file', default=[key_loc], nargs=1, help='Path to RIPE Atlas API key (default: '+key_loc+')')
    parser.add_argument('-r', '--resolve-on-probe', action='store_true',
                        help='Do DNS resolution on probe. (default: on)')
    parser.add_argument('--ipv6', action='store_true', help='Use IPv6 instead of IPv4 (default: IPv4)')
    parser.add_argument('target_list', nargs=1, help='Path to target-list')
    parser.add_argument('meas_id_output', nargs=1, help='Path to file where measurement ids will be written')
    return parser
