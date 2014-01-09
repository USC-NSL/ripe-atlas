#!/usr/bin/python
import json
import sys
import traceback
import os
import requests
import argparse

debug = False
key_loc = '~/.atlas/auth'

class Traceroute(object):

    def __init__(self, target, key):

        self.target = target
        self.description = ''
        self.dont_frag = False
        self.af = 4
        self.protocol = 'ICMP'
        self.is_oneoff = True
        self.resolve_on_probe = True
        self.timeout = 4000
        
        self.num_probes = 1
        self.probe_type = 'area'
        self.probe_value = 'WW'
        
        self.key = key

    def setup_definitions(self):
    
        definitions = {}
        definitions['target'] = self.target
        definitions['description'] = self.description
        definitions['dontfrag'] = str(self.dont_frag).lower()
        definitions['af'] = self.af #set ip version 
        definitions['type'] = 'traceroute'
        definitions['protocol'] = self.protocol
        definitions['is_oneoff'] = str(self.is_oneoff).lower()
        definitions['resolve_on_probe'] = str(self.resolve_on_probe).lower()
        definitions['timeout'] = self.timeout
        
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
    
        response = requests.post('https://atlas.ripe.net/api/v1/measurement/?key='+key, data_str, headers=headers)
        response_str = response.text

        return json.loads(response_str)

def readkey():
    auth_file = os.path.expanduser(key_loc)
    f = open(auth_file)
    key = f.read().strip()
    f.close()
    
    if len(key) <= 0:
        sys.stderr.write('Meaurement key is too short!\n')

    return key

def load_input(inputfile):
    target_dict = {}

    f = open(inputfile)
    for line in f:
        line = line.strip()

        if len(line) == 0:
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

def handle_single_target(args):
    target = args.target_[0]
    
    tr = Traceroute(target)
    tr.description = args.description[0]
    tr.dont_frag = args.dont_frag
    tr.af = 6 if args.ipv6 else 4
    tr.protocol = args.protocol[0]
    tr.resolve_on_probe = args.resolve_on_probe
    tr.timeout = args.timeout[0]
    
    tr.num_probes = args.num_probes
    tr.probe_type = args.probe_type
    tr.probe_value = setup_probe_value(ars.probe_type, args.value)

    return tr.run()

def handle_multi_targets(key, args, target_dict, output_file):
    
    f = open(output_file, 'w+')
    try:
        for target, probe_list in target_dict.items():
            definitions = setup_definitions(target, args.description[0], args.dont_frag, args.ipv6, 
                                    args.protocol[0], args.resolve_on_probe, args.timeout[0])
    
            probes = {}
            probes['requested'] = 1
            probes['type'] = 'probes'
            probes['value'] = setup_probe_value('probes', probe_list)

            data = {'definitions': [definitions], 'probes': [probes]}
        
            data_str = json.dumps(data)
            response = run(key, data_str)

            response_output = format_response(response)

            f.write(response_output+'\n')
            f.flush()
    finally:
       f.close()

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

    parser = argparse.ArgumentParser(description='Issue traceroutes to RIPE Atlas probes.')
        
    parser.add_argument('-d', '--description', default=[''], nargs=1, help='measurement description (default: empty)')
    parser.add_argument('-p', '--protocol', default=['ICMP'], nargs=1, help='Must be ICMP or UDP (default: ICMP)')
    parser.add_argument('-k', '--key-file', default=[key_loc], nargs=1, help='Path to RIPE Atlas API key (default: '+key_loc+')')
    #parser.add_argument('--debug', action='store_true', help='Print debugging information')
    #http://stackoverflow.com/questions/10588644/how-can-i-see-the-entire-request-thats-being-sent-to-paypal-in-my-python-applic

    #Optional
    parser.add_argument('-r', '--resolve-on-probe', action='store_true',
                        help='Do DNS resolution on probe. (default: on)')
    parser.add_argument('--ipv6', action='store_true', help='Use IPv6 instead of IPv4 (default: IPv4)')
    parser.add_argument('--dont-frag', action='store_true', help='Don\'t fragment the packet (default: off)')
    parser.add_argument('--paris', default=[0], type=int, 
                        help='Use Paris. Value must be between 1 and 16. (default: off)')
    parser.add_argument('--timeout', default=[4000], type=int,
                        help='Value (in milliseconds) must be between 1 and 60000 (default: 4000)')

    subparsers = parser.add_subparsers()
    
    ##
    target_list_parser = subparsers.add_parser('target-list', help='file with traceroute targets')
    target_list_parser.add_argument('target_list_file', nargs=1)
    target_list_parser.add_argument('output_file', nargs=1)

    ##
    target_parser = subparsers.add_parser('target', help='traceroute target')
    target_parser.add_argument('target_', nargs=1)
    target_parser.add_argument('--probe-type', required=True, choices=['area', 'country', 'prefix', 'asn', 'probes', 'msm'])
    target_parser.add_argument('--value', required=True, nargs='+', 
                               help='Depends on the choice of probe-type. See full documentation at https://atlas.ripe.net/docs/measurement-creation-api/')
    target_parser.add_argument('-n', '--num-probes', type=int, default=[500], 
                               help='Number of probes (default: 500')

    return parser

if __name__ == '__main__':
    
    parser = config_argparser()  #set up command line parameters
    args = parser.parse_args()

    #debug = args.debug

    try:
        key_file = args.key_file[0]
        key = readkey(key_file)          #read in Atlas API key
    except:
        sys.stderr.write('Error reading key file at '+key_file)
        sys.exit(1)

    if hasattr(args, 'target_'): #run single target command
        data = handle_single_target(args)
        response = run(key, data)
        response_output = format_response(response)
        print(response_output)
    else:                       #run multiple target command
        target_file = args.target_list_file[0]
        output_file = args.output_file[0]
        target_dict = load_input(target_file)
        handle_multi_targets(key, args, target_dict, output_file)
