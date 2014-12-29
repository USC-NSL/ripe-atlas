#!/bin/bash

if [ $# -ne 1 ]; then
    echo "usage: probe-file" >&2
    exit 1
fi

desc=sibyl-ip-test1
traceroute=~/ripe-atlas/bin/atlas_http.py
dst=6z5sgs1.egg.maas.uscnsl.net
user=calderm@usc.edu
pass=USCatlas
sleeptime=20

probefile=$1

while read probe; do
    echo "$probe $dst" > /tmp/$probe
    $traceroute $user $pass /tmp/$probe "test.html?q=$probe" $desc -1 
    sleep $sleeptime 
done < $probefile
