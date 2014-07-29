#!/bin/bash

if [ $# -ne 2 ]; then
    echo "Usage: mid-file num-parallel-downloads" >&2
    exit 1
fi

#Version3.lol.
midfile=$1
jobs=$2
cat $midfile | parallel -j $jobs "curl --silent https://atlas.ripe.net/api/v1/measurement/{}/result/?format=txt; echo ''"

#Version2
#ids=$(cat) #read from stdin
#ids=$(echo "$ids" | tr '\n' ',' | sed 's/.$//') #remove the last char from the line
#url="https://atlas.ripe.net/api/v1/measurement/{$ids}/result/?format=txt"
#curl --silent -w "\n" $url #fetch all ids and write newline after each success

#Version1
#while read -r id; do
#    curl --silent "https://atlas.ripe.net/api/v1/measurement/$id/result/?format=txt" 
#done <<< "$ids"
