import requests
import logging
import json
import datetime
#import pytz

HOST = 'https://atlas.ripe.net'
URL = 'https://atlas.ripe.net/api/v1/measurement/?limit=%d&type=%d&format=txt&use_iso_time=true' 
NO_REQ_MSG = 'No requests left to make in this search'
#UTC = pytz.UTC
dt_format = '%Y-%m-%d %H:%M:%S'

HOUR = 3600
DAY = 24 * HOUR
WEEK = DAY * 7
MONTH = 30 * DAY #No.

class Search(object):

    def __init__(self, type=2, limit=20, param=None, value=None, start_time=None, end_time=None):

        self.logger = logging.getLogger(__name__)

        valid_params = ['dst_asn', 'dst_name', 'dst_addr']

        if param and param not in valid_params:
            logger.error('Invalid param value %s' % param)
            raise Exception('Must specify param for at least one of %s, %s, %s', tuple(valid_params))
        
        self.type = type
        self.param = param
        self.value = value
        self.start_time = start_time
        self.end_time = end_time       
        
        self.initial_url = URL % (limit, type)
        if self.param and self.value:
            self.initial_url += '&'+param+'='+value
        if self.start_time:
            self.initial_url += '&start_time__gte='+str(start_time)
            #start_str = datetime.datetime.fromtimestamp(start_time, UTC).strftime(dt_format)
            #self.initial_url += '&start_time__gte='+str(start_str)
        if self.end_time:
            self.initial_url += '&stop_time__lte='+str(end_time)
            #end_str = datetime.datetime.fromtimestamp(end_time, UTC).strftime(dt_format)
            #self.initial_url += '&stop_time__lte='+str(end_str)

        self.max_requests = None #largely useful for debugging
        self.req_count = 0

        self.__offset = None
        self.__total = None
        self.__limit = limit
        self.__next_url = None

    def __iter__(self):
        return self

    def has_next(self):
        if self.__total is None:
            return True #we haven't made any request yet
        elif self.max_requests and self.req_count == self.max_requests:
            return False
        elif self.__offset+self.__limit < self.__total:
            return True
        else:
            return False

    def total(self):
        return self.__total if self.__total else 0

    def next(self):
        
        if not self.has_next():
            self.logger.info(NO_REQ_MSG)
            raise StopIteration

        url = self.__next_url if self.__next_url else self.initial_url
        self.logger.debug(url)

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
