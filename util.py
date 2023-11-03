# -*- coding: utf-8 -*-
from typing import Dict, List, Tuple
import json
import requests
import re
from enum import Enum
from bs4 import BeautifulSoup
import configparser

import logging
import pickle


# 创建日志记录器
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)

file_logger = logging.getLogger('my_file_logger')
file_logger.setLevel(logging.INFO)


class ReportMsg:
    def __init__(self):
        self.topic_dict: Dict[str, Dict[str, List[str]]] = {}

    def set_msg(self, topic, sub_topic, msg):
        if topic not in self.topic_dict:
            self.topic_dict[topic] = {sub_topic: [msg]}
        elif sub_topic not in self.topic_dict[topic]:
            self.topic_dict[topic].update({sub_topic: [msg]})
        else:
            self.topic_dict[topic][sub_topic].append(msg)

    def __str__(self):
        trace_vec = []
        for topic, sub_topic_dic in self.topic_dict.items():
            a = f'\n--------------------------- 解析「{topic}」---------------------------'
            trace_vec.append(a)

            for sub_topic, msg_vec in sub_topic_dic.items():
                trace_vec.append(f'\n『{sub_topic}』:')

                for id, msg in enumerate(msg_vec, start=1):
                    tmp = f'{id}、{msg}'
                    trace_vec.append(tmp)

        all = '\n'.join(trace_vec)
        return f"{all}"


almuten_star_sign_mapping = {
    'Q': '太阳',
    'E': '水星',
    'R': '金星',
    'W': '月亮',
    'T': '火星',
    'Y': '木星',
    'U': '土星',
    'I': '天王',
    'O': '海王',
    'P': '冥王',
    '‹': '北交',
    'Z': '上升',
    'X': '中天'
}

short_mapping = {
    '太阳': '日',
    '月亮': '月',
    '水星': '水',
    '金星': '金',
    '木星': '木',
    '火星': '火',
    '土星': '土',
    '天王': '天',
    '海王': '海',
    '冥王': '冥'
}


star_dict: Dict[str, Star] = {}
house_dict: Dict[int, House] = {}

all_trace_dict: Dict[str, Dict[str, List[str]]] = {}
disaster_trace_dict: Dict[str, List[str]] = {}
marriage_trace_dict: Dict[str, List[str]] = {}
love_trace_dict: Dict[str, List[str]] = {}
wealth_trace_dict: Dict[str, List[str]] = {}
health_trace_dict: Dict[str, List[str]] = {}
work_trace_dict: Dict[str, List[str]] = {}
asc_trace_dict: Dict[str, List[str]] = {}
study_trace_dict: Dict[str, List[str]] = {}
nature_trace_dict: Dict[str, List[str]] = {}

knowledge_dict: Dict[str, Dict[str, str]] = {}
knowledge_dict_old: Dict[str, str] = {}
jobs_dict: Dict[str, Tuple[str, str]] = {}
jobs_star_dict: Dict[str, str] = {}
# common_trace_vec = []  # for 简单的打印

report = ReportMsg()








def parse_almuten_house():
    # Fill house_dict
    for star_name, star_obj in star_dict.items():
        # 宫主星啥，几飞几，宫内星哪些
        if star_name not in ['天王', '海王', '冥王', '北交']:
            for house in star_obj.lord_house_vec:
                house_obj = House(house_num=house, ruler=star_name, ruler_loc=star_obj.house)
                house_dict[house] = house_obj

    for star_name, star_obj in star_dict.items():
        house = star_obj.house
        house_dict[house].loc_star.append(star_name)

    # for houseid, house_obj in house_dict.items():
    #     print(house_obj)


    # for star, star_obj in star_dict.items():
    #     print(f'{star_obj}')



pattern_constellation = re.compile(r'\([^)]*\)')
pattern_house = re.compile(r'\d+')


def parse_ixingpan_star(soup):
    '''
    解析包括：
        星体、四轴、富点、婚神、凯龙、北交
        落入星座
        落入宫位
    :param soup:
    :return:
    '''
    tables = soup.find_all('table')

    table = tables[5]
    tbody = table.find('tbody')
    trs = tbody.find_all('tr')
    for tr in trs:
        tds = tr.find_all('td')
        star = tds[0].text.strip()
        constellation = tds[1].text.strip()
        house = tds[2].text.strip()

        constellation = pattern_constellation.sub('', constellation).strip()

        match = pattern_house.search(house)

        if match:
            house = int(match.group())
        else:
            house = -1

        # 重新填充 star_dict
        if star in star_dict:
            star_dict[star].constellation = constellation

            if house != star_dict[star].house:
                pass
                # print(f'{star} {star_dict[star].house} {house}')
        else:
            r = Star(star=star, house=house)
            r.constellation = constellation
            star_dict[star] = r
        # print(star, constellation, house)


def parse_ixingpan_house(soup):
    '''
    解析包括：
        宫头宫位
    :param soup:
    :return:
    '''
    tables = soup.find_all('table')

    table = tables[6]
    tbody = table.find('tbody')
    trs = tbody.find_all('tr')
    for tr in trs:
        tds = tr.find_all('td')
        if len(tds) != 5:
            continue

        house = tds[0].text.strip()
        constellation = tds[1].text.strip()
        lord = tds[2].text.strip()
        lord_loc = tds[4].text.strip()

        constellation = pattern_constellation.sub('', constellation).strip()

        match = pattern_house.search(house)

        if match:
            house = int(match.group())
        else:
            house = -1

        # Update house_dict
        if house in house_dict:
            house_dict[house].constellation = constellation


def parse_ixingpan_aspect(soup):
    tables = soup.find_all('table')

    # 选择第7个<table>下的<td>标签
    table = tables[7]
    tbody = table.find('tbody')
    trs = tbody.find_all('tr')

    # print_module_info('DEBUG 爱星盘-相位信息')
    for tr in trs:
        tds = tr.find_all('td')
        star_a = tds[0].text.strip()
        star_b = tds[2].text.strip()
        aspect = tds[1].text.strip()

        # print(star_a, star_b, aspect)

        aspect = aspect if aspect != '拱' else '三合'

        # if star_a in ['上升', '中天', '婚神']:
        #     continue

        aspect_obj = Aspect(star_b=star_b, aspect=aspect)
        # star_dict[star_a].aspect_vec_old.append(aspect_obj)
        star_dict[star_a].aspect_dict[star_b] = aspect_obj

        # 反过来填充
        aspect_obj_reverse = Aspect(star_b=star_a, aspect=aspect)
        star_dict[star_b].aspect_dict[star_a] = aspect_obj_reverse
        # print(f'{star_a} {aspect} {star_b}')


def load_customer_info(customer_name='jackietan'):
    config = configparser.ConfigParser()

    # 读取配置文件
    config.read('./customer.ini')

    # 获取配置项的值
    name = config.get(customer_name, 'name')
    birthday = config.get(customer_name, 'birthday')
    location = config.get(customer_name, 'location')

    cur_loc = location
    if config.has_option(customer_name, 'cur_loc'):
        cur_loc = config.get(customer_name, 'cur_loc')

    glon_deg, glat_deg = '', ''

    # 如果指定就用指定的
    if config.has_option(customer_name, 'glon_deg'):
        glon_deg = config.get(customer_name, 'glon_deg')

    if config.has_option(customer_name, 'glat_deg'):
        glat_deg = config.get(customer_name, 'glat_deg')

    toffset = config.get(customer_name, 'toffset')
    is_dst = int(config.get(customer_name, 'is_dst'))
    # dist = config.get(customer_name, 'dist')
    dist = ''

    return name, birthday, location, cur_loc, glon_deg, glat_deg, toffset, is_dst, dist






class HSys(Enum):
    P = '普拉西德制'
    K = 'Koch制'
    O = 'Porphyrius制'
    R = '苪氏分宫制'
    C = 'Campanus制'
    E = '等宫制'
    W = '整宫制'
    B = '阿卡比特制'
    M = 'Morinus制'
    U = 'Krusinski-Pisa'
    Y = 'APC 宮位制'




if __name__ == '__main__':
    error_msg, dist = get_dist_by_location(target_province='山东省', target_city='济南市', target_district='长清区')
    print(error_msg, dist)

    from dateutil.parser import parse

    # text = "山东省济南市历下区。出生1989年8月5日 12点58分"
    text = "2022.1.1 12点58分"
    inp_time = parse(text)
    dt_str = inp_time.strftime("%Y-%m-%d %H:%M:%S")
    print(inp_time)
    print(type(inp_time))
    # load_knowledge_file()
    # print(knowledge_dict.keys())
    # load_jobs_file()
    # print(jobs_star_dict)
    # exit(0)
    # for a,b in zip([1,2,3], ['a','b', 'c']):
    #     print(a,b)

    name, birthday, location, glon_deg, glat_deg, toffset, is_dst, dist = load_customer_info(customer_name='jackietan')
    print(name, birthday, location, glon_deg, glat_deg, toffset, is_dst, dist)

    # 将 104°09E 30°00N 转换成：glon_deg:104 E 09	glat_deg:30 N 00
    input_str = '104°09E 30°00N'
    pattern = r'((\d+)°(\d+)[EW] (\d+)°(\d+)[NS])'
    match = re.search(pattern, input_str)

    if match:
        print(match.groups())
        print(type(match.groups()))

        groups = match.groups()
        glon_deg = f'{match.group(2)} E {match.group(3)}'
        glat_deg = f'{match.group(4)} N {match.group(5)}'
        print('获取经纬度结果：', glon_deg, glat_deg)



'''
data = {
    "name": "jackie_test",
    "month": "9",
    "day": "18",
    "year": "2018",
    "hour": "13",
    "min": "12",
    "location": "北京市",
    "glon_deg": "116",
    "glon_dir": "E",
    "glon_min": "24",
    "glat_deg": "39",
    "glat_dir": "N",
    "glat_min": "54",
    "toffset": "480",
    "hsys": "B"
}
'''
