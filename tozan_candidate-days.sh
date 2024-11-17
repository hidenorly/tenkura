#!/bin/bash
source config.sh
MOUNTAINS=`./list-mountains.sh`
echo $MOUNTAINS
python3 $GET_TENKURA_CANDIDATE_DAYS --args="$MOUNTAINS" -dw $@