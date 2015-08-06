#!/usr/bin/python
import json
import sys
import requests
import traceback
import logging
import time
from requests.exceptions import ConnectionError

URL = 'https://atlas.ripe.net/api/v1/probe/?limit=100'
HOST = 'https://atlas.ripe.net'
keys = ['id', 'asn_v4', 'asn_v6', 'address_v4', 'address_v6', 'prefix_v4', 'prefix_v6', 'status_name', 'country_code', 'latitude', 'longitude']

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
        values = []
        for key in keys:
            try:
                values.append(_str(probe[key]))
            except KeyError:
                values.append('None')            
        
        line = ' '.join(values)
        lines.append(line)
    return lines

def filter_active(probe_list):
    return filter(lambda x: x['status_name'] == 'Connected', probe_list)

def loadtab(data):
    """
    Returns a list of probe dictionarys
    """
    types = [_int, _int, _int, str, str, str, str, str, str, float, float]
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
            traceback.print_exc(file=sys.stderr)
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

def dump(probe_list, filename):
    
    probe_values = []
    for probe in probe_list:
        values = [str(probe[key]) for key in keys]
        probe_values.append(' '.join(values))

    lines = '\n'.join(probe_values)
    f = open(filename, 'w')
    f.write(lines)
    f.close()

class Page(object):

    def __init__(self):

        self.logger = logging.getLogger(__name__)
        self.initial_url = URL
        self.__offset = None
        self.__total = None
        self.__limit = 100
        self.__next_url = None
        self.req_count = 0
    
    def __iter__(self):
        return self

    def has_next(self):
        if self.__total is None:
            return True #we haven't made any request yet
        elif self.__offset+self.__limit < self.__total:
            return True
        else:
            return False

    def total(self):
        return self.__total if self.__total else 0

    def next(self):
        
        if not self.has_next():
            raise StopIteration

        url = self.__next_url if self.__next_url else self.initial_url

        response = requests.get(url) #make request
 
        json_response = json.loads(response.text)
        if 'error' in json_response:
            err_msg = 'Error: %s' % json_response['error']
            self.logger.error(err_msg)
            raise Exception(err_msg)

        self.req_count += 1

        meta = json_response['meta']
        self.__total = meta['total_count']
        self.__offset = meta['offset']
        self.__next_url = HOST+meta['next'] if meta['next'] else None

        limit = meta['limit']
        if self.__limit != limit:
            self.logger.warn('Initial limit was %d but request has %d' % (self.__limit, limit))
            self.__limit = limit

        results = json_response['objects']
        return results

def fetch_probes(onlyactive = True, max_requests = -1, inter_req_wait = 5, error_wait = 60, max_retries = 100):
    probe_list = []
    page = Page()

    retry_count = 0
    req_count = 0
    
    while page.has_next() and (max_requests <= 0 or req_count < max_requests):
        try:
            p = page.next()
            probe_list.extend(p)
            req_count += 1
            time.sleep(inter_req_wait)
        except StopIteration:
            break
        except ConnectionError:
            sys.stderr.write('ConnectionError fetching active probe list. Sleeping for %d\n' % error_wait)
            retry_count += 1
        
            if retry_count == max_retries:
                raise Exception("Reached maximum number of network retries fetching active probe list.")
        
            time.sleep(error_wait)

    return probe_list

def usage_and_error():
    sys.stderr.write('Usage: <json|tab> <only-active (true|false)>\n')
    sys.exit(1)

if __name__ == '__main__':

    if len(sys.argv) != 3:
        usage_and_error()

    format = sys.argv[1].lower()
    if format != 'json' and format != 'tab':
        usage_and_error()
   
    onlyactive = sys.argv[2].lower() == 'true'
    if onlyactive:
        URL = URL + '&status=1' #set flag to fetch only "connected" probes

    probe_list = []
    page = Page()
    for p in page:
        probe_list.extend(p)
 
    if format == 'json':
        print(json.dumps(probe_list, sort_keys=True, indent=4, separators=(',', ': ')))
    else: #
        lines = json2tab(probe_list)
        print('\n'.join(lines))
