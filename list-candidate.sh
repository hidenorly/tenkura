#!/bin/sh
POS_LONGITUDE="139.744972"
POS_LATITUDE="35.675889"
python3 ~/bin/get_mountain_list.py $POS_LATITUDE $POS_LONGITUDE --rangeMin=80 --rangeMax=180 --famous -nn | xargs python3 ~/bin/tenkura_get_weather.py -a A,B -c -m -w rain,thunder -t 6-15 -dw -c -ns