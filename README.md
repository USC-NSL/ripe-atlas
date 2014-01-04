##Requirements

The atlas client libraries require the "requests" library. The traceroute service additionally requires "jsonrpclib".

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
