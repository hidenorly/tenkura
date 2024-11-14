#!/bin/sh
source config.sh
MOUNTAINS=`./list-mountains.sh`
echo $MOUNTAINS | xargs python3 $GET_TENKURA_WEATHER -a A,B -c -m -w rain,thunder -t 6-15 -dw -c -ns