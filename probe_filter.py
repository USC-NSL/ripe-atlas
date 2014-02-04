#!/usr/bin/python
import sys
import fetch_active

class Filter(object):
    
    def __init__(self, probe_list):
        self.probe_list = probe_list

    def within(self, lat, lon, max_dist):
        import hmvp

        points = []     # [(probe['latitude'], probe['longitude']) for probe in self.probe_list]
        good_probes = [] #terrible name. fix me please
        for probe in self.probe_list:
            try:
                point = (probe['latitude'], probe['longitude'])
                points.append(point)
                good_probes.append(probe)
            except:
                continue

        if len(points) != len(good_probes):
            raise Exception('Number of points is not same as number of probes')
        
        filtered = hmvp.distance.within((lat,lon), points, good_probes, max_dist)
        #filtered is a list of (distance, probe) tuples so just extract the probes
        return zip(*filtered)[1]

    def separated_by(self, distance):
        import hmvp
    
        asn_probes = {}
        #separate probes by asn
        for probe in self.probe_list:
            try:
                try:
                    asn = probe['asn_v4']
                except:
                    continue                

                asn_probes[asn].append(probe)
            except KeyError:
                asn_probes[asn] = [probe]
        
        """
        For each set of probes in each ASN,  
        """ 
        filtered_probes = []      
        for asn, probe_list in asn_probes.items():
            points =  [(p['latitude'], p['longitude']) for p in probe_list]
            filtered = hmvp.distance.dist_filter(points, probe_list, distance)
            filtered_probes.extend(filtered)
    
        return filtered_probes    

if __name__ == '__main__':
    
    if len(sys.argv) != 5:
        sys.stderr.write('Usage: probe-file lat lon max-dist\n')
        sys.exit(1)
        
    input_file = sys.argv[1]
    lat = float(sys.argv[2])
    lon = float(sys.argv[3])
    max_dist = float(sys.argv[4])

    probe_list = fetch_active.load(input_file)
    
    filter = Filter(probe_list)
    
    #Amsterdam
    #lat = 52.370216
    #lon = 4.895168
    filtered_probes = filter.within(lat, lon, max_dist)
    lines = fetch_active.json2tab(filtered_probes)
    print('\n'.join(lines))
