#!/bin/sh

# your location
POS_LATITUDE="35.675889"
POS_LONGITUDE="139.744972"

# preference params
RANGE_MAX_DISTANCE=180
RANGE_MIN_DISTANCE=80
MAX_ROUTE_TIME_TO_TOZANGUCHI=3:30

MIN_CLIMB_TIME=3:00
MAX_CLIMB_TIME=8:00
MIN_ALTITUDE=800
MAX_ALTITUDE=2500
MIN_DISTANCE=4
MAX_DISTANCE=15
MAX_ELEVATION=1400

# script paths and the prompt
ROUTE_TIME_TO_TOZANGUCHI=~/work/tozanguchi/get_route_time_to_tozanguchi.py
RECENT_RECORD=~/work/mountainRecord/get_recent_record2.py
DETAIL_RECORD=~/work/mountainRecord/get_detail_record.py
MOUNTAIN_LIST=~/bin/get_mountain_list.py
GET_TENKURA_CANDIDATE_DAYS=tenkura_get_candidate_days.py
GET_TENKURA_WEATHER=~/bin/tenkura_get_weather.py
LLM_CLI=~/work/aws_bedrock_playground/claude3-cli.py
