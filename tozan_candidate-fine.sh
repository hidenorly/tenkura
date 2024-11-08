#!/bin/bash
tozan_candidate.sh $1 $2 $3 $4 $5 $6 $7 $8 $9 | grep "fine.*fine" | sed -E "s/ +\:.*//"