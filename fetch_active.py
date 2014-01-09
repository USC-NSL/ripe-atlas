#!/usr/bin/python
import json
import sys
import requests

URL = 'https://atlas.ripe.net/api/v1/probe/?limit=10000&format=txt'

def _str(s):
    """
    LOL
    """
    if s == '' or s == ' ':
        return 'None'
    elif s == 'Never Connected':
        return 'NeverConnected'
    else:
        return str(s)

def json2tab(probe_list):

    keys = ['id', 'asn_v4', 'asn_v6', 'prefix_v4', 'prefix_v6', 'status_name', 'country_code', 'latitude', 'longitude']

    for probe in probe_list:
        values = map(lambda x: _str(probe[x]), keys)
        line = ' '.join(values)
        print(line)

def usage_and_error():
    sys.stderr.write('Usage: <json|tab>\n')
    sys.exit(1)

if __name__ == '__main__':

    if len(sys.argv) != 2:
        usage_and_error()

    format = sys.argv[1].lower()
    if format != 'json' and format != 'tab':
        usage_and_error()
    
    response = requests.get(URL) #make request
    probe_list = json.loads(response.text)['objects'] #list
    
    if format == 'json':
        print(json.dumps(probe_list, sort_keys=True, indent=4, separators=(',', ': ')))
    else: #
        json2tab(probe_list)
        
        
    
