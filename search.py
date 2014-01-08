import requests
import logging
import json

HOST = 'https://atlas.ripe.net'
URL = 'https://atlas.ripe.net/api/v1/measurement/?limit=%d&type=%d&%s=%s&format=txt' 

class Search(object):

    def __init__(self, param, value, type=2, limit=20):

        self.logger = logging.getLogger(__name__)

        valid_params = ['dst_asn', 'dst_name', 'dst_addr']

        if param not in valid_params:
            logger.error('Invalid param value %s' % param)
            raise Exception('Must specify param for at least one of %s, %s, %s', tuple(valid_params))
        
        self.type = type
        self.param = param
        self.value = value

        self.max_requests = None #largely useful for debugging
        self.req_count = 0

        self.__offset = None
        self.__total = None
        self.__limit = limit
        self.__next_url = None

        #self.results = list()
        #self.cache = False

    def has_next(self):
        if self.__total is None:
            return True #we haven't made any request yet
        elif self.max_requests and self.req_count == self.max_requests:
            return False
        elif self.__offset+self.__limit < self.__total:
            return True
        else:
            return False

    def next(self):
        
        if not self.has_next():
            self.logger.error('No requests left to make in this search')
            return

        url = self.__next_url if self.__next_url else URL % (self.__limit, self.type, self.param, self.value)
        self.logger.info(url)

        response = requests.get(url)
        self.req_count += 1

        json_response = json.loads(response.text)

        meta = json_response['meta']
        self.__total = meta['total_count']
        self.__offset = meta['offset']
        self.__next_url = HOST+meta['next'] if meta['next'] else None

        limit = meta['limit']
        if self.__limit != limit:
            self.logger.warn('Initial limit was %d but request has %d' % (self.__limit, limit))
            self.__limit = limit

        results = json_response['objects']
        #for result in results:
        #    msm_id = result['msm_id']
        #    probe_count = result['participant_count']
        return results
        
