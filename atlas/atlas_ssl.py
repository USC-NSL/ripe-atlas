#!/usr/bin/python
import sys
import time
import socket
import traceback
from atlas import measure_baseclass
from measure_baseclass import MeasurementBase
from measure_baseclass import load_input, readkey, process_response
from measure_baseclass import SLEEP_TIME

class SSL(MeasurementBase):
    
    def __init__(self, target, key, probe_list=None, sess=None):
        super(SSL, self).__init__(target, key, probe_list, sess)
        self.measurement_type = 'sslcert'
    
    def setup_definitions(self):
        definitions = super(SSL, self).setup_definitions() 
        return definitions
 
def config_argparser():
    parser = measure_baseclass.config_argparser()
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
    repeating = args.repeats[0]
    is_public = args.private

    if not target_dict:
        sys.stderr.write('No targets defined\n')
        sys.exit(1)

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
                 
                    ssl = SSL(target, key, probe_list=probe_list_chunk)
                    ssl.description = description
                    ssl.af = 4 if not ipv6 else 6
                    ssl.is_oneoff = True if repeating == 0 else False
                    if not ssl.is_oneoff: ssl.interval = repeating #set the repeating interval
                    ssl.is_public = is_public

                    response = ssl.run()
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
        sys.stderr.write('Got error making SSL request\n')
        traceback.print_exc(file=sys.stderr)
    finally:
        outf.close()
