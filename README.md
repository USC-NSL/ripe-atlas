This is a set of command line scripts that double as Python libraries for creating measurements for RIPE Atlas. This project will be most useful for those who prefer to work on the command-line or need a higher level of programmability when issuing measurements. 

The code started off from a very nice tutorial by Stéphane Bortzmeyer (http://www.bortzmeyer.org/ripe-atlas-api.html). I continue to use the "authentication key" configuration from the tutorial script. 

##Measurement scripts

There are several measurement scripts in place for running traceroute, ping, ssl etc... Most scripts double as Python class modules and command-line scripts. As command-line scripts, each typically takes a probe-target file as the first argument and an output file to write measurement ids as the second argument. The probe-target file is a space-separated probeid, target pair per line such as
```
4125 www.google.com
4156 204.57.0.5
...
```

Example usage of ping.
```
atlas_ping.py probe-targets-file probe-targets-measurementids
```

Each measurement script has it's own set of independent options so check out the usage output for each one. Measurement ids are also printed to stderr as a status indicator.


##Configure Auth Key
Measurement scripts require an auth key file at ~/.atlas/auth with the key as a single line. 

##Utilities

###Fetching active probes
```
./fetch_active.py tab true > active_probes
```

###Check status of measurements
```
./status probe-targets-measurementids
```

###Downloading measurements
This currently relies on GNU parallel. It seems to work with versions >= 20130222 but older versions may have problems. There are other implementations of download commented out in the source if parallel is not available but they will be much slower.

```
./atlas_collect.sh probe-targets-file 4 > results.json 
```

###Parsing/Format JSON results into a TAB format
All data is present in the original JSON format but this is nicer to work with if you prefer standard Unix tools.

```
./atlas_retrieve ping results.json > results.tab
```

##Dependencies

The atlas client libraries require the [Requests](http://docs.python-requests.org/en/latest) library.
