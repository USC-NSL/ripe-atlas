##Introduction

This project is a set of command line scripts that double as Python libraries for creating measurements for RIPE Atlas. It uses the more recent [RESTful API](https://atlas.ripe.net/docs/rest/). 
This project will be most useful for those who prefer to work on the command-line or need a higher level of flexability when issuing and collecting measurements.

If you are looking for a library to assist in parsing Atlas data then please check out the [analysis tools](https://github.com/RIPE-Atlas-Community/ripe-atlas-community-contrib).

The code started off from a very nice tutorial by Stéphane Bortzmeyer (http://www.bortzmeyer.org/ripe-atlas-api.html). I continue to use the "authentication key" configuration from the tutorial script.

##Measurement scripts

There are several measurement scripts in place for running traceroute, ping, ssl etc... Most scripts double as Python class modules and command-line scripts. As command-line scripts, each typically takes a probe-target file as the first argument and an output file to write measurement ids as the second argument. The probe-target file is a space-separated probeid, target pair per line such as
```
4125 www.google.com
4156 204.57.0.5
...
```

Measurements are target-centric. When measurements are issued, all probes measuring the same target will be batched together is a single measurement. This reduces load on the RIPE Atlas backend scheduling platform.


Example usage of ping.
```
atlas_ping.py probe-targets-file probe-targets-measurementids
```

Each measurement script has it's own set of independent options so check out the usage output for each one. Measurement ids are also printed to stderr as a status indicator.


##Configure Auth Key
Measurement scripts require an auth key file at ~/.atlas/auth with the key as a single line. Alternatively, a key can be passed as a parameter to most scripts.

##Utilities

###Check status of measurements
```
./atlas_status probe-targets-measurementids
```

###Fetching active probes
```
./fetch_active.py tab true > active_probes
```

The first argument specifies space-separated tabular format as the output. Otherwise the output is JSON. The format of the tab file is

<sub>
Probe ID | IPv4 ASN | IPv6 ASN | IPv4 Address | IPv6 Address | IPv4 Prefix | IPv6 Prefix | Connected Status | Country Code | Latitude | Longitude
</sub>

<!-- | -------- | -------- | -------- | -------- | -------- | -------- | -------- | -------- | -------- | -------- | -------- | -->


###Downloading measurements
This currently relies on GNU parallel. It seems to work with versions >= 20130222 but older versions may have problems. There are other implementations of download commented out in the source if parallel is not available but they will be much slower.

```
./atlas_collect.sh probe-targets-file 4 > results.json 
```

###Stop repeating measurements
```
./stop_measurements.sh probe-targets-measurementids
```

##My Workflow
These scripts don't implement the full convenience of probe selection that is possible in the web UI. Instead, you must create an input file with a list of all the probes you want to use. My workflow generally looks something like this.

First, fetch a fresh copy of the list of probes that are currently online. ```$./fetch_active.py tab true > active_probes.txt``` Then I pick out the specific probes I want for a target with standard unix tools. For example, if I want to use all the probes hosted in AT&T in the U.S. to measure Google, I would do something like this. ```$awk '{ if($2 == 7018 && $9 == "US") print "www.google.com",$1}' active_probes.txt > probe_targets.txt``` It's a bit of manual work but it allowed me much more control with my experiments than I could get with the UI.`

Then you should be able to run your measurements. For traceroutes, your would do ```$./atlas_traceroute.py probe_targets.txt measure_ids.txt```. 

Check their status with ```$./atlas_status.py measure_ids.txt```. When all are complete, collect them with ```$./atlas_collect.sh measure_ids.txt 4 > results.json```.

If you want to run repeating measurements then you should be able to pass the interval in seconds using ```--repeats`` flag (I think this works but I generally don't use it much). This will keep going unless you stop it.

##Dependencies
The atlas client libraries require the [Requests](http://docs.python-requests.org/en/latest) library.

##Licence
[The MIT License (MIT)](http://opensource.org/licenses/MIT)

Copyright (c) 2015 Matt Calder & The University of Southern California.
