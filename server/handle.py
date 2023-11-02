# coding=utf-8


"""
File: handle.py
Date: 2023/11/01 12:11:35
Brief: 
"""
from typing import Tuple
import hashlib
import reply
import receive
import web
import sys
import re
import cpca
import datetime


# print("Python版本：", sys.version)

def parse_area(inp_str) -> Tuple[str, str, str]:
    df = cpca.transform([inp_str])

    province = df.iloc[0]['省']
    city = df.iloc[0]['市']
    area = df.iloc[0]['区']

    if city == '市辖区':
        city = province
    
    return province, city, area


def parse_time(text: str) -> str:
    # 匹配日期的正则表达式模式
    date_pattern = r"(\d{4})[年.](\d{1,2})[月.](\d{1,2})[日]?"
    # 匹配时间的正则表达式模式
    time_pattern = r"([上下]午)?(\d{1,2})[点:](\d{1,2})[分]?"

    # 提取日期
    date_match = re.search(date_pattern, text)
    if not date_match:
        return None

    year = int(date_match.group(1))
    month = int(date_match.group(2))
    day = int(date_match.group(3))

    # 提取时间
    time_match = re.search(time_pattern, text)
    if not time_match:
        return None

    hour = int(time_match.group(2))
    minute = int(time_match.group(3))
    if time_match.group(1) == "下午" and hour < 12:
        hour += 12

    # 返回解析结果
    dt = datetime.datetime(year, month, day, hour, minute)

    return dt.strftime("%Y-%m-%d %H:%M:%S")


def get_astro_data(content, name=None):
    '''
    name, birthday, location, cur_loc, glon_deg, glat_deg, toffset, is_dst, _ = load_customer_info(customer_name=customer_name)
    load_knowledge_file()
    load_knowledge_data_old()
    load_jobs_file()

    姓名:july_friend3
    位置信息:黑龙江省鹤岗市鹤岗市
    出生信息:2004-07-04 21:40
    经纬度信息:130 E 16 47 N 20
    时区:GMT_ADD_8
    是否夏令时:0
    dist:3896
    '''

    province, city, area = parse_area(content)
    birthday = parse_time(content)
    toffset = 'GMT_ADD_8'
    is_dst = 0
    pass


class Handle(): 
    def POST(self):
        try:
            webData = web.data()
            # print("Handle Post webdata is ", webData)

            recMsg = receive.parse_xml(webData)

            if isinstance(recMsg, receive.Msg) and recMsg.MsgType == 'text':
                toUser = recMsg.FromUserName
                fromUser = recMsg.ToUserName

                content = recMsg.Content
                content = content.decode('utf-8')
                # print(type(content))

                # print(f'content:{content}')
                province, city, area = parse_area(content)

                reply_str = f'省份: {province}\n城市: {city}\n区: {area}'

                replyMsg = reply.TextMsg(toUser, fromUser, reply_str)

                return replyMsg.send()
            else:
                print("暂且不处理")
                return "success"
        except Exception as Argument:
            print(Argument)
            return Argument


if __name__ == '__main__':
    inp_str_vec = ['山东省济南市历下区，时间是1989年8月5日下午12点58分',
               '山东省济南市历下区，时间是:1989.8.5 12点58分']
    for inp_str in inp_str_vec:
        print(parse_time(inp_str))


    import time

    stime = time.strptime("1998-08-05 12:58", "%Y-%m-%d %H:%M")
    print(bool(stime.tm_isdst))
