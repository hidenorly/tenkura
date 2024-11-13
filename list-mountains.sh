#!/bin/sh
source config.sh
python3 $MOUNTAIN_LIST $POS_LATITUDE $POS_LONGITUDE --rangeMin=$RANGE_MIN_DISTANCE --rangeMax=$RANGE_MAX_DISTANCE --famous -nn