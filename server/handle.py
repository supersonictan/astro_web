# coding=utf-8


"""
File: handle.py
Date: 2023/11/01 12:11:35
Brief: 
"""
import sys
sys.path.append('/root/code/astro_web')
from typing import Tuple
import reply
import receive
import web
import re
import cpca
import datetime
import os
import json
from project_util import get_dist_by_location
from project_util import parse_glon_glat
from project_util import dump_load_http_result, logger, build_almuten_http_data
from project_util import fetch_almuten_soup, fetch_ixingpan_soup
from bs4 import BeautifulSoup


USE_CACHE = True

def load_local_file():
    """
    knowledge_web.ini
    knowledge.csv
    jobs.csv
    ixingpan_area.json

    :return:
    """
    pass


def get_basic_soup_from_http(customer_name, content) -> Tuple[str, BeautifulSoup, BeautifulSoup]:
    folder_path = f'../cache/basic/{customer_name}'
    os.makedirs(folder_path, exist_ok=True)

    """ ixingpan Http Result. 有 cache 文件则从文件加载，没有走 http 请求 """
    filename_ixingpan = f'{folder_path}/{customer_name}_ixingpan.pickle'

    error_msg, birthday, dist, is_dst, toffset, location = prepare_http_data(content=content, name=customer_name)
    if error_msg != '':
        return error_msg, None, None

    print(error_msg, birthday, dist)

    if USE_CACHE and os.path.exists(filename_ixingpan):
        soup_ixingpan = dump_load_http_result(filename=filename_ixingpan, is_load_mode=True)
        logger.info(f'成功从本地加载本命盘数据，File=[{filename_ixingpan}]')
    else:
        soup_ixingpan = fetch_ixingpan_soup(name=customer_name, dist=dist, birthday_time=birthday, dst=is_dst, female=1)
        dump_load_http_result(filename=filename_ixingpan, soup_obj=soup_ixingpan, is_load_mode=False)
        logger.info(f'走Http请求获取爱星盘排盘信息，并且 Dump BeautifulSoup to File:{filename_ixingpan}')

    # Update glon_deg, glat_deg. 用ixingpan结果中的
    glon_deg, glat_deg = parse_glon_glat(soup=soup_ixingpan)

    """ almuten Http Result. """
    filename_almuten = f'{folder_path }/{customer_name}_almuten.pickle'

    if USE_CACHE and os.path.exists(filename_almuten):
        soup_almuten = dump_load_http_result(filename=filename_almuten, is_load_mode=True)
        logger.info(f'成功从本地加载本命盘数据，File=[{filename_almuten}]')
    else:
        post_data = build_almuten_http_data(name=customer_name, birthinfo=birthday, loc=location, glon_deg=glon_deg, glat_deg=glat_deg, toffset=toffset, is_dst=is_dst)
        soup_almuten = fetch_almuten_soup(post_data)

        dump_load_http_result(filename=filename_almuten, soup_obj=soup_almuten, is_load_mode=False)
        logger.info(f'走Http请求获取「宫神星」排盘信息，并且 Dump BeautifulSoup to File:{filename_almuten}')

    return error_msg, soup_ixingpan, soup_almuten


def prepare_http_data(content, name=None) -> Tuple[str, str, str, str, str, str]:
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

    def parse_location(inp_str) -> Tuple[str, str, str]:
        df = cpca.transform([inp_str])

        province = df.iloc[0]['省']
        city = df.iloc[0]['市']
        area = df.iloc[0]['区']

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

    province, city, area = parse_location(content)
    birthday = parse_time(content)

    if not province or not city or not area or not birthday:
        return '解析出生地/生时失败', birthday, '', '', '', ''

    error_msg, dist = get_dist_by_location(target_province=province, target_city=city, target_district=area)

    # TODO: dynamic
    is_dst = '0'
    toffset = 'GMT_ADD_8'

    return error_msg, birthday, dist, is_dst, toffset, f'{province}{city}{area}'


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
                # province, city, area = parse_location(content)
                # reply_str = f'省份: {province}\n城市: {city}\n区: {area}'
                error_msg, soup_ixingpan, soup_almuten = get_basic_soup_from_http(customer_name=fromUser, content=content)

                if error_msg != '':
                    replyMsg = reply.TextMsg(toUser, fromUser, f'排盘失败!\n{error_msg}, 请重新检查输入...')

                    return replyMsg.send()


                replyMsg = reply.TextMsg(toUser, fromUser, '没毛病')

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
