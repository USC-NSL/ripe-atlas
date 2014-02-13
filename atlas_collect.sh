#!/bin/bash

ids=$(cat) #read from stdin
ids=$(echo "$ids" | tr '\n' ',' | sed 's/.$//') #remove the last char from the line
url="https://atlas.ripe.net/api/v1/measurement/{$ids}/result/?format=txt"
#echo $url
curl --silent -w "\n" $url #fetch all ids and write newline after each success

#while read -r id; do
#    curl --silent "https://atlas.ripe.net/api/v1/measurement/$id/result/?format=txt" 
#done <<< "$ids"
