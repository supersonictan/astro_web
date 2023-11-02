#!/bin/bash
#
# File: stop.sh
# Author: jackietan@tencent.com
# Date: 2023/11/01 23:11:34
# Brief: 

source activate astro

# 先kill已存在进程,再启动
pid=$(pgrep -f run_web.py)
if [ -n "$pid" ]; then
    kill -9 $pid
    echo "进程 $pid 已成功杀死..."
else
    echo "服务尚未启动,已直接启动服务..."
fi

nohup python ./server/run_web.py 80 stdout.log 2>&1 &
pid=$!
echo "服务已启动，进程ID为 $pid"
