#!/bin/bash

cd /home/liujs/crawler/direction_baidu/backup
file_path="crawler/directionbaidu/source_delta_2019-07-19"
base_name=`basename "$file_path"`

hdfs dfs -get $file_path &
TASK_PID=$!
sleep 60

name="backup_source_"
name+=`date +"%Y-%m-%d"`
mv "$base_name" "$name"

kill $TASK_PID
