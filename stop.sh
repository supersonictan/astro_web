#!/bin/bash
#
# Copyright (c) 2017 Tencent Inc. All Rights Reserved
#
# File: stop.sh
# Author: jackietan@tencent.com
# Date: 2023/11/01 23:11:34
# Brief: 


# 获取进程ID
pid=$(pgrep -f run_web.py)
# 杀死进程
if [ -n "$pid" ]; then
    kill -9 $pid
    echo "进程 $pid 已成功杀死"
else
    echo "未找到匹配的进程"
fi
