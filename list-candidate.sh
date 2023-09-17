#!/bin/sh
POS_LONGITUDE="139.744972"
POS_LATITUDE="35.675889"
MOUNTAINS=`./list-mountains.sh`
echo $MOUNTAINS | xargs python3 ~/bin/tenkura_get_weather.py -a A,B -c -m -w rain,thunder -t 6-15 -dw -c -ns