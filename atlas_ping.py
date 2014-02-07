#!/usr/bin/python
import sys
import traceback
import measure_baseclass
from measure_baseclass import MeasurementBase
from measure_baseclass import load_input, readkey, process_response

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

    if not target_dict:
        sys.stderr.write('No targets defined\n')
        sys.exit(1)

    try:
        outf = open(outfile, 'w')

        for target, probe_list in target_dict.items():
            ping = Ping(target, key, probe_list=probe_list, num_packets=num_packets)
            ping.description = description
            ping.af = 4 if not ipv6 else 6

            response = ping.run()
            status, result = process_response(response)

            if status == 'error':
                sys.stderr.write('Request got error %s\n' % result)
            else:
                measurement_list = result
                measurement_list_str = map(str, measurement_list)
                outstr = '\n'.join(measurement_list_str)
                outf.write(outstr)
                print(outstr)
    except:
        sys.stderr.write('Got error making ping request\n')
        traceback.print_exc(file=sys.stderr)
    finally:
        outf.close()
