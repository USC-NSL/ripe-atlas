#!/usr/bin/python
import measure_baseclass

class DNS(MeasurementBase):
    
    def __init__(self, query_class, query_type, query_arg, target, key, sess=None):
        super(DNS, self).__init__(target, key, sess)
        self.measurement_type = 'dns'
        self.query_class = query_class
        self.query_type = query_type
        self.query_arg = query_arg
    
    def setup_definitions(self):
        definitions = super(DNS, self).setup_definitions() 
    
        definitions['query_class'] = self.query_class
        definitions['query_type'] = self.query_type
        definitions['query_argument'] = self.query_arg

def config_argparser()
    parser = measure_baseclass.config_argparser('Issue DNS measurements to RIPE Atlas')

    parser.

    return parser
 
if __name__ == '__main__':
    parser = config_argparser()      
    args = parser.parse_args()

    try:
        key_file = args.key_file[0]
        key = readkey(key_file)          #read in Atlas API key
    except:
        sys.stderr.write('Error reading key file at '+key_file)
        sys.exit(1)

    args.probe_file    

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
                 
