#!/bin/bash

ids=$(cat) #read from stdin

while read -r id; do
    curl --silent "https://atlas.ripe.net/api/v1/measurement/$id/result/?format=txt" 
done <<< "$ids"
