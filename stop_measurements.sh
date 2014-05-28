#!/bin/bash

if [ $# -ne 1 ]; then
    echo "Usage: measurement-id-file"
    exit 1
fi

key=$(cat ~/.atlas/stopkey)
if [[ -z "$key" ]]; then
    echo "Error: need to configure ~/.atlas/stopkey"
    exit 1
fi

while read line; do
    curl --dump-header - -X DELETE https://atlas.ripe.net/api/v1/measurement/$line/?key=$key
done < $1
