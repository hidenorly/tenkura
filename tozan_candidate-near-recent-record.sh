#!/bin/bash

is_nd=""
is_open=""
filtered_args=()
for arg in "$@"; do
  if [[ "$arg" == "-nd" ]]; then
    is_nd="-nd"
  elif [[ "$arg" == "-o" ]]; then
  	is_open="-o"
  else
    filtered_args+=("$arg")
  fi
done


python3 ~/bin/tenkura_get_weather.py -i ~/tochigi100.csv -i ~/yamanashi100.csv -i ~/gunma100.csv -e ~/excludes.csv -nn -t 8-15 -w rain ${filtered_args[@]} | xargs python3 ~/bin/get_recent_record2.py -e ~/excludes.csv -e ~/excludes-alps.csv -e ~/far_prefecture.csv ${is_nd} ${is_open}