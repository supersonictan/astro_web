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
from bs4 import BeautifulSoup
from project_util import all_trace_dict
from project_util import get_dist_by_location
from project_util import parse_glon_glat
from project_util import dump_load_http_result, logger, build_almuten_http_data
from project_util import fetch_almuten_soup, fetch_ixingpan_soup
from project_util import load_knowledge_file, load_knowledge_data_old, load_jobs_file
from project_util import parse_almuten_star, parse_almuten_house
from project_util import parse_ixingpan_star, parse_ixingpan_house, parse_ixingpan_aspect
from basic_analyse import get_square, get_house_energy
from basic_analyse import parse_love, parse_marrage_2, parse_marrage, parse_wealth, parse_health, parse_work, parse_asc_star, parse_study, parse_nature


USE_CACHE = True

def load_local_file():
    """
    knowledge_web.ini
    knowledge.csv
    jobs.csv
    ixingpan_area.json

    :return:
    """
    load_knowledge_file()
    load_knowledge_data_old()
    load_jobs_file()


def get_basic_soup_from_http(customer_name, content) -> Tuple[str, BeautifulSoup, BeautifulSoup]:
    folder_path = f'../cache/basic/{customer_name}'
    os.makedirs(folder_path, exist_ok=True)

    """ ixingpan Http Result. 有 cache 文件则从文件加载，没有走 http 请求 """
    filename_ixingpan = f'{folder_path}/{customer_name}_ixingpan.pickle'

    error_msg, birthday, dist, is_dst, toffset, location = prepare_http_data(content=content, name=customer_name)
    if error_msg != '':
        return error_msg, None, None

    print(error_msg, birthday, dist)
    logger.error(birthday,dist)

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

            if not (isinstance(recMsg, receive.Msg) and recMsg != 'text'):
                logger.fatal('暂不处理')
                return 'success'

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
                replyMsg = reply.TextMsg(toUser, fromUser, f'【排盘失败】\n{error_msg}, 请重新检查输入...')
                return replyMsg.send()

            # 加载知识库
            load_local_file()
            parse_almuten_star(soup_almuten)
            parse_almuten_house()

            # 解析爱星盘结果
            parse_ixingpan_star(soup_ixingpan)
            parse_ixingpan_house(soup_ixingpan)
            parse_ixingpan_aspect(soup_ixingpan)

            get_square()
            get_house_energy()

            parse_love()
            parse_marrage_2()
            parse_marrage()
            parse_wealth()
            parse_health()
            parse_work()
            parse_asc_star()
            parse_study()
            parse_nature()

            ret_vec = []

            key_vec = ['个性显现及生活领域上的重点', '恋爱', '婚姻', '财富', '事业', '健康', '学业', '性格分析']
            for key in key_vec:
                if key not in all_trace_dict:
                    continue

                field_dict = all_trace_dict[key]

                ret_vec.append(f'\n解析「{key}」')
                # f.writelines(f'\n--------------------------- 解析「{key}」---------------------------')
                for biz, sub_vec in field_dict.items():
                    ret_vec.append(f'『{biz}』:')
                    # f.writelines(f'\n『{biz}』:\n')
                    # print(f'\n『{biz}』:')
                    for index, sub in enumerate(sub_vec, start=1):
                        # print(f'{index}、{sub}')
                        # f.writelines(f'{index}、{sub}\n')
                        ret_vec.append(f'{index}、{sub}')

                replyMsg = reply.TextMsg(toUser, fromUser, '\n'.join(ret_vec))

                return replyMsg.send()

        except Exception as Argument:
            print(Argument)
            return Argument


if __name__ == '__main__':
    inp_str_vec = ['山东省济南市历下区，时间是1989年8月5日下午12点58分',
               '山东省济南市历下区，时间是:1989.8.5 12点58分']
    for inp_str in inp_str_vec:
        #print(parse_time(inp_str))
        pass

    import time

    stime = time.strptime("1998-08-05 12:58", "%Y-%m-%d %H:%M")
    print(bool(stime.tm_isdst))
