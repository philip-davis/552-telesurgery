#!/bin/bash -x

sfx=$1
patient_dat=patient_${sfx}.dat
surg_dat=surgeon_${sfx}.dat
ts_analysis=/proj/novel-scheduler-PG0/552-telesurgery/tstamp_analysis.py

if [[ $# -ne 1 ]] ; then
    echo "usage: generate_results.sh <suffix>"
    exit -1
fi

mkdir ${sfx}.dir
mv $patient_dat ${sfx}.dir
mv $surg_dat ${sfx}.dir
cd ${sfx}.dir
$ts_analysis $patient_dat $surg_dat ${sfx} > ${sfx}.txt
cd ..
tar cvf ${sfx}.tar ${sfx}.dir



