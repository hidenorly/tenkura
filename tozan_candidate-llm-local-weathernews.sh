#!/bin/bash

lms server stop
lms unload gemma-3-4b-it > /dev/null 2>&1 
lms load --gpu=1.0 --context-length=32768 gemma-3-4b-it-GGUF > /dev/null 2>&1 
lms server start > /dev/null 2>&1 


is_fallback=false
filtered_args=()
for arg in "$@"; do
  if [[ "$arg" == "--fallback" ]]; then
    is_fallback=true
  else
    filtered_args+=("$arg")
  fi
done

if ! $is_fallback; then
  MOUNTAIN_LIST_WEATHERNEWS=`tozan_candidate.sh "${filtered_args[@]}" -nn`
  MOUNTAIN_LIST_WEATHERNEWS=`tozan_candidate_weathernews.sh "${filtered_args[@]}" -nn`
  MOUNTAIN_LIST="$MOUNTAIN_LIST_TENKURA $MOUNTAIN_LIST_WEATHERNEWS"
else
    MOUNTAIN_LIST=`python3 ~/bin/tenkura_get_weather.py -i ~/tochigi100.csv -i ~/yamanashi100.csv -i ~/gunma100.csv -e ~/excludes.csv -nn -w "" "${filtered_args[@]}"`
fi

echo $MOUNTAIN_LIST

echo "" > ~/tmp/park-info.txt
echo "the followings are candidate of mountains. Please choose better candidates from the additional related information below." >> ~/tmp/park-info.txt
echo $MOUNTAIN_LIST | xargs python3 ~/work/tozanguchi/get_route_time_to_tozanguchi.py --maxTime=3:30 -u 8:00 -m 3:00 -nn  >> ~/tmp/park-info.txt
echo "" >> ~/tmp/park-info.txt
echo "以下は候補となる山に関する登山口駐車場に関する情報です。また登山口からの標準登山時間を含んでいます。登山口への移動時間の記載の無い登山口には交通規制などでいけないので候補に含めないでください。" >> ~/tmp/park-info.txt
echo $MOUNTAIN_LIST | xargs python3 ~/work/tozanguchi/get_route_time_to_tozanguchi.py --maxTime=3:30 -u 8:00 -m 3:00 | grep -v https | grep -v "0分" | grep -v 住所 | grep -v 緯度経度 | grep -v トイレ>> ~/tmp/park-info.txt
echo "" >> ~/tmp/park-info.txt
echo "以下は候補となる山に関する、登山レポートで、登山した人のその山に関する印象や登山中に気づいたこと、登山道に関する危険情報などもありますので、選ぶのに参考にしてください。基本的にはこの記録のある山を優先してください。理由は直近で山に登った記録であるためです。この記録がないのは冬期通行止めなどでいけない可能性があります。なお危険な行程がある登山口からの登山レポートは避けるべきです。また凍結路面などアクセス道や駐車場や登山道などもできるだけ避けましょう。" >> ~/tmp/park-info.txt
echo $MOUNTAIN_LIST | xargs python3 ~/work/tozanguchi/get_route_time_to_tozanguchi.py --maxTime=3:30 -u 8:00 -m 3:00 -nn | xargs python3 ~/work/mountainRecord/get_recent_record2.py -n 1 -g 800 -u 2500 -nd | xargs python3 ~/work/mountainRecord/get_detail_record.py -p -d 15 -s 4 -e 1400 -f "actual_duration|rest_duration|date|weather|pace|level|access"| grep -v None | grep -v http | grep -v photo_captions >> ~/tmp/park-info.txt
cat ~/tmp/park-info.txt | python3 ~/work/openai_playground/gpt_compatible-cli.py -e http://localhost:1234/v1/chat/completions -p ~/work/openai_playground/better_mountain.json

lms server stop
lms unload gemma-3-4b-it > /dev/null 2>&1 
