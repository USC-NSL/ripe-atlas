#!/usr/bin/python
import sys
import time
import socket
import traceback
from atlas import measure_baseclass
from measure_baseclass import MeasurementBase
from measure_baseclass import load_input, readkey, process_response
from measure_baseclass import SLEEP_TIME

class Ping(MeasurementBase):
    
    def __init__(self, target, key, probe_list=None, sess=None, num_packets=3):
        super(Ping, self).__init__(target, key, probe_list, sess)
        self.measurement_type = 'ping'
        self.num_packets = num_packets
    
    def setup_definitions(self):
        definitions = super(Ping, self).setup_definitions() 
        definitions['packets'] = self.num_packets

        return definitions
    
def config_argparser():
    parser = measure_baseclass.config_argparser()
    parser.add_argument('-n', '--num-packets', default=[3], nargs=1, help='Number of packets (default: 3)')
    return parser
 
if __name__ == '__main__':
    parser = config_argparser()      
    args = parser.parse_args()

    try:
        key_file = args.key_file[0]
        key = readkey(key_file)          #read in Atlas API key
    except:
        #traceback.print_exc(file=sys.stderr)
        sys.stderr.write('Error reading key file at %s\n' % key_file)
        sys.exit(1)

    target_dict = load_input(args.target_list[0])    
    outfile = args.meas_id_output[0]

    ipv6 = args.ipv6
    description = args.description[0]
    num_packets = args.num_packets[0]
    repeating = args.repeats[0]
    is_public = args.private   
 
    if not target_dict:
        sys.stderr.write('No targets defined\n')
        sys.exit(1)

    #for target, probe_list in target_dict.items():
    #    if len(probe_list) > 500:
    #        sys.stderr.write('Warning: There are more than 500 probes for target %s\n' % target)
    
    """ """
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
                    ping = Ping(target, key, probe_list=probe_list_chunk, num_packets=num_packets)
                    ping.description = description
                    ping.is_public = is_public
                    ping.af = 4 if not ipv6 else 6
                    ping.is_oneoff = True if repeating == 0 else False
                    if not ping.is_oneoff: ping.interval = repeating #set the repeating interval

                    response = ping.run()
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
        sys.stderr.write('Got error making ping request\n')
        traceback.print_exc(file=sys.stderr)
    finally:
        outf.close()
