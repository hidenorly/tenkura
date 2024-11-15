#!/bin/bash
cd ~
export _ARGS=`echo $@`; find . -maxdepth 1 -type f | grep -E "\.csv$" | grep -v "yama.00\.csv" | grep -v "exclude" | xargs -n 1 /bin/bash -c 'TMP=$1; printf "%-20s: %3d / %3d\n" "$TMP" $(python3 ~/bin/tenkura_get_weather.py -c -a A -t 6-15 $_ARGS -nu -i $TMP -e ~/excludes.csv | grep " A" | wc -l) $(cat $1 | wc -l)' /bin/bash
