#!/bin/bash

# preference params
MAX_ROUTE_TIME_TO_TOZANGUCHI=3:30
MIN_CLIMB_TIME=3:00
MAX_CLIMB_TIME=8:00
MIN_ALTITUDE=800
MAX_ALTITUDE=2500
MIN_DISTANCE=4
MAX_DISTANCE=15
MAX_ELEVATION=1400

# script paths and the prompt
TEMP_OUT=~/tmp/park-info.txt
ROUTE_TIME_TO_TOZANGUCHI=~/work/tozanguchi/get_route_time_to_tozanguchi.py
RECENT_RECORD=~/work/mountainRecord/get_recent_record2.py
DETAIL_RECORD=~/work/mountainRecord/get_detail_record.py
LLM_CLI=~/work/aws_bedrock_playground/claude3-cli.py
LLM_PROMPT=~/work/openai_playground/better_mountain.json

# mountain candidate enumeration
echo "" > $TEMP_OUT
echo "the followings are candidate of mountains. Please choose better candidates from the additional related information below." >> $TEMP_OUT
tozan_candidate.sh $1 $2 $3 $4 $5 -nn | xargs python3 $ROUTE_TIME_TO_TOZANGUCHI --maxTime=$MAX_ROUTE_TIME_TO_TOZANGUCHI -u $MAX_CLIMB_TIME -m $MIN_CLIMB_TIME -nn  >> $TEMP_OUT

# mountain's park info including transportation time
echo "" >> $TEMP_OUT
echo "以下は候補となる山に関する登山口駐車場に関する情報です。また登山口からの標準登山時間を含んでいます。登山口への移動時間の記載の無い登山口には交通規制などでいけないので候補に含めないでください。" >> $TEMP_OUT
tozan_candidate.sh  $1 $2 $3 $4 $5 -nn | xargs python3 $ROUTE_TIME_TO_TOZANGUCHI --maxTime=$MAX_ROUTE_TIME_TO_TOZANGUCHI -u $MAX_CLIMB_TIME -m $MIN_CLIMB_TIME | grep -v https | grep -v "0分" | grep -v 住所 | grep -v 緯度経度 | grep -v トイレ>> $TEMP_OUT

# recent mountain report
echo "" >> $TEMP_OUT
echo "以下は候補となる山に関する、登山レポートで、登山した人のその山に関する印象や登山中に気づいたこと、登山道に関する危険情報などもありますので、選ぶのに参考にしてください。基本的にはこの記録のある山を優先してください。理由は直近で山に登った記録であるためです。この記録がないのは冬期通行止めなどでいけない可能性があります。なお危険な行程がある登山口からの登山レポートは避けるべきです" >> $TEMP_OUT
tozan_candidate.sh  $1 $2 $3 $4 $5 -nn | xargs python3 $ROUTE_TIME_TO_TOZANGUCHI --maxTime=$MAX_ROUTE_TIME_TO_TOZANGUCHI -u $MAX_CLIMB_TIME -m $MIN_CLIMB_TIME -nn | xargs python3 $RECENT_RECORD -n 1 -g $MIN_ALTITUDE -u $MAX_ALTITUDE -nd | xargs python3 $DETAIL_RECORD -p -d $MAX_DISTANCE -s $MIN_DISTANCE -e $MAX_ELEVATION -f "actual_duration|rest_duration|date|weather|pace|level|access"| grep -v None | grep -v http | grep -v photo_captions >> $TEMP_OUT

# generate recommendation report based on the above info.
cat $TEMP_OUT | python3 $LLM_CLI -p $LLM_PROMPT
