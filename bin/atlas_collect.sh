#!/bin/bash
set -eu
set -x

# File with a download key ("Download results of a user defined measurement")
COLLECTION_KEY=$HOME/.atlas/get.auth

if [ ! -e $COLLECTION_KEY ] ; then
	echo "file $COLLECTION_KEY not found" >&2
	exit 1
fi


if [ $# -ne 2 ]; then
    echo "Usage: measurement-ids-file num-parallel-downloads" >&2
    exit 1
fi

midfile=$1
jobs=$2

key=$(cat $COLLECTION_KEY)
cat $midfile | parallel -j $jobs "curl --silent https://atlas.ripe.net/api/v1/measurement/{}/result/\?format=txt\&key=$key"
