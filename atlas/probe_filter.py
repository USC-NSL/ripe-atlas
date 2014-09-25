#!/usr/bin/python
import sys
from atlas import fetch_active
from math import radians, sin, cos, sqrt, asin

class Filter(object):
    
    def __init__(self, probe_list):
        self.probe_list = probe_list

    def haversine(self, lat1, lon1, lat2, lon2):
        """
       Calculate the great circle distance between two points
       on the earth (specified in decimal degrees)
       """
        # convert decimal degrees to radians
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        # haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        km = 6367 * c
        return km
     
    def dist_filter(self, points, values, max_dist):
           
        if len(points) != len(values):
            raise Exception('points and values lists must be the same length!')
     
        p_len = len(points)
        range_list = range(0, p_len)
        discard_set = set()
        index_set = set(range_list)
     
        for i1 in range_list:
            for i2 in range_list:
                if i1 != i2 and i1 not in discard_set and i2 not in discard_set:
                    p1 = points[i1]
                    p2 = points[i2]
                    dist = self.haversine(p1[0], p1[1], p2[0], p2[1])
                    if dist <= max_dist:
                        discard_set.add(i2)
     
        keep = index_set.difference(discard_set)
       
        values = [values[i] for i in keep]    
        return values


    def separated_by(self, distance):
#        import hmvp
    
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
            filtered = self.dist_filter(points, probe_list, distance)
            filtered_probes.extend(filtered)
    
        return filtered_probes    

if __name__ == '__main__':
    
    if len(sys.argv) != 3:
        sys.stderr.write('Usage: probe-file max-dist\n')
        sys.exit(1)
        
    input_file = sys.argv[1]
    max_dist = float(sys.argv[2])

    probe_list = fetch_active.load(input_file)
    asn_dict = {} #organize by asn
    for probe in probe_list:
        try:
            asn = probe['asn_v4']
            if asn != None:
                try:
                    asn_dict[asn].append(probe)
                except:
                    asn_dict[asn] = [probe]
        except:
            pass

    for probe_sub_list in asn_dict.values():
        probe_filter = Filter(probe_sub_list)
        filtered_probes = probe_filter.separated_by(max_dist)
        lines = fetch_active.json2tab(filtered_probes)
        print('\n'.join(lines))
