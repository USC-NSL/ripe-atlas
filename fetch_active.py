#!/usr/bin/python
import json
import sys
import requests
import traceback

URL = 'https://atlas.ripe.net/api/v1/probe/?limit=10000&format=txt'
keys = ['id', 'asn_v4', 'asn_v6', 'prefix_v4', 'prefix_v6', 'status_name', 'country_code', 'latitude', 'longitude']

def _str(s):
    if s == '' or s == ' ':
        return 'None'
    elif s == 'Never Connected':
        return 'NeverConnected'
    else:
        return str(s)

def _int(i):
    try:
        return int(i)
    except:
        return None

def json2tab(probe_list):

    lines = []
    for probe in probe_list:
        values = map(lambda x: _str(probe[x]), keys)
        line = ' '.join(values)
        lines.append(line)
    return lines

def usage_and_error():
    sys.stderr.write('Usage: <json|tab>\n')
    sys.exit(1)

def loadtab(data):
    types = [_int, _int, _int, str, str, str, str, float, float]
    probe_list = []

    for line in data.split('\n'):
        try:
            chunks = line.split(' ')
            
            """
            types is a list of functions. the ith function gets
            applied to the ith chunk using the lambda.
            """
            typed_chunks = map(lambda x,y:x(y), types, chunks)
            """
            This creates a dictionary by making the list, keys,
            to be keys and its corresponding position in typed_chunks
            to be the value.
            """
            probe_dict = dict(zip(keys, typed_chunks)) #nice!
                    
            probe_list.append(probe_dict)
        except:
            sys.stderr.write('Got error loading line: %s\n' % line)
            continue
        
    return probe_list

def load(file):
    """
    Returns a tuple with the file format and then a list of probe data
    """
    f = open(file)
    try:
        data = f.read()
        try:
            return json.loads(data)
        except:
            #probably not json
            return loadtab(data)
    finally:
        f.close()

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
        lines = json2tab(probe_list)
        print('\n'.join(lines))
