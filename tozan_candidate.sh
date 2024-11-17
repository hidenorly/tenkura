#!/bin/bash
source config.sh
MOUNTAINS=`./list-mountains.sh`
echo $MOUNTAINS | xargs python3 $GET_TENKURA_WEATHER -e ~/excludes.csv -a A,B -c -m -w rain,thunder -t 6-15 -c -ns $1 $2 $3 $4 $5 $6 $7 $8 $9