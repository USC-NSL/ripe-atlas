#!/usr/bin/python
from atlas import measure_baseclass
from measure_baseclass import MeasurementBase
from measure_baseclass import load_input, readkey, process_response
from measure_baseclass import SLEEP_TIME
import sys
import traceback
import socket
import time

class DNS(MeasurementBase):
    
    def __init__(self, query_class, query_type, query_arg, target, key, probe_list=None, sess=None):
        super(DNS, self).__init__(target, key, probe_list, sess)
        self.measurement_type = 'dns'
        self.query_class = query_class
        self.query_type = query_type
        self.query_arg = target
 
    def setup_definitions(self):
        definitions = super(DNS, self).setup_definitions() 
    
        definitions['query_class'] = self.query_class
        definitions['query_type'] = self.query_type

        if self.query_arg: # if not None
            definitions['query_argument'] = self.query_arg

        #redundant
        definitions['use_probe_resolver'] = definitions['resolve_on_probe']

        return definitions

def config_argparser():
    parser = measure_baseclass.config_argparser()
    parser.add_argument('--query-class', default=['IN'], nargs=1, help='Must be "IN" or "CHAOS" (Default: "IN")')
    parser.add_argument('--query-type', default=['A'], nargs=1, help='"A", "AAAA", "PTR", ... (Default: "A")')
    parser.add_argument('--query-arg', default=['None'], nargs=1, help='DNS Resolver to use. (Default: Use probe\'s resolver')
    parser.add_argument('--protocol', default=['UDP'], nargs=1, help='Must be "TCP" or "UDP" (Default: "UDP")')
    return parser
 
if __name__ == '__main__':
    parser = config_argparser()      
    args = parser.parse_args()
    
    try:
        key_file = args.key_file[0]
        key = readkey(key_file)          #read in Atlas API key
    except:
        sys.stderr.write('Error reading key file at %s\n' % key_file)
        sys.exit(1)

    target_dict = load_input(args.target_list[0])    
    outfile = args.meas_id_output[0]

    ipv6 = args.ipv6
    description = args.description[0]
    repeating = args.repeats[0]
    resolve_on_probe = not args.dont_resolve_on_probe
    is_public = args.private

    if not target_dict:
        sys.stderr.write('No targets defined\n')
        sys.exit(1)

    query_class = args.query_class[0]
    query_type = args.query_type[0]
    query_arg = args.query_arg[0]
    #should do arg validation here...

    try:
        outf = open(outfile, 'w')

        i = 0
        target_list = target_dict.keys()
        while i < len(target_list):
           
            try: 
                target = target_list[i]
                probe_list = target_dict[target]
                
                """
                The maxmimum number of probes per requet is 500 so we need to break
                this is up into several requests.
                """
                probe_list_chunks = [probe_list[x:x+500] for x in xrange(0, len(probe_list), 500)]
                j = 0
                #for probe_list_chunk in probe_list_chunks:
                while j < len(probe_list_chunks):

                    probe_list_chunk = probe_list_chunks[j]
                 
                    dns = DNS(query_class, query_type, query_arg, target, key, probe_list=probe_list_chunk)
                    dns.resolve_on_probe = resolve_on_probe
                    dns.is_public = is_public
                    dns.description = description
                    dns.af = 4 if not ipv6 else 6
                    dns.is_oneoff = True if repeating == 0 else False
                    if not dns.is_oneoff: dns.interval = repeating #set the repeating interval

                    response = dns.run()
                    status, result = process_response(response)

                    if status == 'error':
                        sys.stderr.write('Request got error %s. Sleeping for %d seconds\n' % (result, SLEEP_TIME))
                        time.sleep(SLEEP_TIME)
                        continue #try again
                    else:  #on success
                        measurement_list = result
                        measurement_list_str = map(str, measurement_list)
                        outstr = '\n'.join(measurement_list_str)
                        outf.write(outstr+'\n')
                        print(outstr)
                        j += 1 #only increment on success

                i += 1
            except socket.error:
                sys.stderr.write('Got network error. Going to sleep for %d seconds\n' % SLEEP_TIME)
                traceback.print_exc(file=sys.stderr)
                time.sleep(SLEEP_TIME)
    except:
        sys.stderr.write('Got error making DNS request\n')
        traceback.print_exc(file=sys.stderr)
    finally:
        outf.close()  
