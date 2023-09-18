#!/bin/bash
MOUNTAINS=`./list-mountains.sh`
echo $MOUNTAINS
python3 tenkura_get_candidate_days.py --args="$MOUNTAINS" -dw $@