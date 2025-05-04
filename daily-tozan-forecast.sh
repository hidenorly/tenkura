#!/bin/bash

DAILY_REPORT=~/tmp/daily-report.md
REPORT_CSS=~/bin/bootstrap-md.css
REPORT_DATE=$(date +%Y%m%d)
EMAIL_TO="xxx@gmail.com"
EMAIL_CC="yyy@gmail.com"

WEATHER_PIC_BASE=~/tmp

# clean up
echo "" > $DAILY_REPORT

echo "# 土日のどちらが良いか?" >> $DAILY_REPORT
echo "" >> $DAILY_REPORT
tozan_candidate-days.sh -dw | grep -E "20..\/.*\:" | sed -e "s/^/* /" >> $DAILY_REPORT
echo "" >> $DAILY_REPORT
echo "The following is by weather news" >> $DAILY_REPORT
echo "" >> $DAILY_REPORT
list-mountains.sh | xargs python3 ~/bin/get_weather_mountain_detail.py -dw -s -w rain,snow,thunder  | sed -e "s/^/* /" >> $DAILY_REPORT

echo "" >> $DAILY_REPORT
echo "# 週末良さそうなエリア(A)" >> $DAILY_REPORT
echo "" >> $DAILY_REPORT
tozan_candidate-area.sh -dw | sed -e "s/\.csv//" | sed -e "s/\.\///" | sed -e "s/^/* /" >> $DAILY_REPORT

# retreive latest saturday/sunday weather pic
~/bin/get_weather_from_weathernews.sh

echo "" >> $DAILY_REPORT
echo "# 登山口の天気" >> $DAILY_REPORT
echo "" >> $DAILY_REPORT
echo "| Saturday | Sunday |" >> $DAILY_REPORT
echo "| :--: | :--: |" >> $DAILY_REPORT
#echo "| ![Saturday](cid:$WEATHER_PIC_BASE/saturday.png) | ![Sunday](cid:$WEATHER_PIC_BASE/sunday.png) |" >> $DAILY_REPORT
echo "| <img src="cid:saturday.png" width="200" alt="Saturday"> | <img src="cid:sunday.png" width="200" alt="Sunday"> |" >> $DAILY_REPORT

echo "" >> $DAILY_REPORT
echo "# 週末候補の山(A,B & no rain)" >> $DAILY_REPORT
echo "" >> $DAILY_REPORT
tozan_candidate.sh -dw -nn >> $DAILY_REPORT

echo "" >> $DAILY_REPORT
echo "# LLMのおすすめ" >> $DAILY_REPORT
echo "" >> $DAILY_REPORT
tozan_candidate-llm-local.sh -dw >> $DAILY_REPORT

echo "" >> $DAILY_REPORT
echo "# 直近の登山レポート" >> $DAILY_REPORT
echo "" >> $DAILY_REPORT
tozan_candidate-oneline.sh -dw | sed -e "s/^/* /" >> $DAILY_REPORT

python3 ~/bin/md2htmlpy3.py $DAILY_REPORT -s $REPORT_CSS -t "週末候補の山 ($REPORT_DATE)" -m mail | python3 ~/bin/mail.py -s "週末候補の山 ($REPORT_DATE)" -t html -c $EMAIL_CC $EMAIL_TO -r $WEATHER_PIC_BASE/saturday.png,$WEATHER_PIC_BASE/sunday.png


