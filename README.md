##Requirements

The atlas client libraries require the "requests" library. The traceroute service additionally requires "jsonrpclib".

##Measurement scripts

There are several measurement scripts in place for running traceroute, ping, ssl etc... Most scripts double as Python class modules and command-line scripts. As command-line scripts, each one typically takes a probe-target file as the first argument and an output file to write measurement ids as the second argument. The probe-target file is a space-separated probeid, target pair per line such as
```
4125 www.google.com
4156 204.57.0.5
...
```

Example usage of ping.
```
atlas_ping.py probe-targets-file probe-targets-measurementids
```

Each measurement script has it's own set of independent options so check out the usage output for each one.

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
This currently relies on GNU parallel but there are other versions commented out in the source.

```
./atlas_collect.sh probe-targets-file 4 > results.json 
```

###Parsing/Format JSON results into a TAB format
All data is present in the original JSON format but this is nicer to work with if you prefer standard Unix tools.

```
./atlas_retrieve ping results.json > results.tab
```

##Traceroute Service

###Available Methods

__Submits a traceroute request__
```
submit(probe_list, target)
```
Returns a measurement_id.


__Retrieve the status of a measurement__
```
status(measurement_id)
```

__Retrieve the active probes, optionally within a specific asn__
```
active(asn), active()
```

__Retrieve the ASes with active probes__
```
ases()
```

__Retrieve the traceroutes for the given measurement_id__
```
results(measurement_id)
```
