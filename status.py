#!/usr/bin/python
import sys
import atlas_retrieve

if __name__ == '__main__':
    
    if len(sys.argv) != 2:
        sys.stderr.write('Usage: mfile\n')
        sys.exit(1)

    mfile = sys.argv[1]
    f = open(mfile)
    for line in f:
        mid = line.strip()
        r = atlas_retrieve.Retrieve(mid)
        status = r.check_status()
        print('%s %s' % (mid, status))
    f.close() 
