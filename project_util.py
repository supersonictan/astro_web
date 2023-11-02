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


class Recepted:
    def __init__(self, star_a, star_b, action_name, level=''):
        self.star_a = star_a
        self.star_b = star_b
        self.action_name = action_name
        self.level = level  # (本垣+三分)

    def get_debug_info(self):
        msg = f'{self.star_b}{self.action_name}({self.level})'

        return msg

    def __str__(self):
        # msg = f'{self.star_a} 被 {self.star_b} {self.action_name}({self.level})'
        msg = f'{self.star_b} {self.action_name}({self.level})'

        return msg


class Aspect:
    def __init__(self, star_b, aspect=''):
        self.star_b: str = star_b
        self.aspect: str = aspect  # 60°: 六合, 30°: 三合

    def get_debug_info(self):
        msg = f'{self.aspect}{self.star_b}'

        return msg


class Star:
    def __init__(self, star: str, house: int, score=-1, lord_house_vec=[]):
        self.star: str = star
        self.house: int = house  # 落宫
        self.score = score
        self.lord_house_vec: List = lord_house_vec  # 几宫主

        self.recepted_dict: Dict[str, Recepted] = {}  # {star_b: ReceptedObj}
        self.aspect_dict: Dict[str, Aspect] = {}  # {star_b, Aspect}

        # self.recepted_vec_old: List[Recepted] = []  # 被互溶接纳
        self.aspect_vec_old: List[Aspect] = []  # 相位

        self.jiena = []
        self.hurong = []
        
        self.constellation: str = ''

    def __str__(self):
        # msg_recepted = [msg.get_debug_info() for msg in self.recepted_vec_old]
        msg_recepted = [msg.get_debug_info() for key, msg in self.recepted_dict.items()]
        msg_aspect = [msg.get_debug_info() for key, msg in self.aspect_dict.items()]
        # msg_aspect = [msg.get_debug_info() for msg in self.aspect_vec_old]

        if len(msg_recepted) == 0:
            msg = f'{self.star}: {self.score}分，是{self.lord_house_vec}宫主, 飞{self.house}宫，{msg_aspect}, 无互容接纳.'
        else:
            msg = f'{self.star}: {self.score}分，是{self.lord_house_vec}宫主, 飞{self.house}宫，{msg_aspect}, 被{msg_recepted}'

        # if self.star in {'天王', '海王', '冥王', '北交', '凯龙', '婚神', '上升', '中天', '下降', '天底', '富点'}:
        #     msg = f'{self.star}: 落{self.house}宫, {msg_aspect}'

        return msg


class House:
    def __init__(self, house_num: int, ruler: str, ruler_loc: int):
        self.house_num = house_num
        self.ruler = ruler
        self.ruler_loc = ruler_loc
        self.loc_star: List[str] = []
        self.constellation: str = ''

    def __str__(self):
        return f'{self.house_num}宫主{self.ruler} 落{self.ruler_loc}宫, {self.house_num}宫宫内落星:{self.loc_star}, 宫头星座:{self.constellation}'


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


def dump_load_http_result(filename, soup_obj=None, is_load_mode=True):
    if is_load_mode:
        return _load_http_result(filename)
    else:
        _dump_http_result(filename, soup_obj)


def _dump_http_result(filename: str, soup_obj: BeautifulSoup):
    # 将 soup 对象序列化到文件
    with open(filename, 'wb') as file:
        pickle.dump(soup_obj, file)


def _load_http_result(filename) -> BeautifulSoup:
    with open(filename, 'rb') as file:
        deserialized_soup = pickle.load(file)

        return deserialized_soup


def load_knowledge_file():
    # Load knowledge_web.ini
    config = configparser.ConfigParser()

    file_name = './knowledge_web.ini'
    config.read(file_name)

    # 遍历指定section的所有option
    for section_name in config.sections():

        for option_name in config.options(section_name):
            value = config.get(section_name, option_name)

            if section_name in knowledge_dict:
                knowledge_dict[section_name][option_name] = value
            else:
                knowledge_dict[section_name] = {option_name: value}


def build_almuten_http_data(name, birthinfo, loc, glon_deg, glat_deg, toffset, is_dst):
    data = {}
    data['name'] = name

    birthday = birthinfo.split(' ')[0]

    data['month'] = str(int(birthday.split('-')[1]))
    data['day'] = str(int(birthday.split('-')[2]))
    data['year'] = birthday.split('-')[0]

    brith_time = birthinfo.split(' ')[-1]
    data['hour'] = str(int(brith_time.split(':')[0]))

    if is_dst:
        data['hour'] = str(int(data['hour']) - 1)

    data['min'] = brith_time.split(':')[1]
    data['location'] = loc
    data['glon_deg'] = glon_deg.split(' ')[0]
    data['glon_dir'] = glon_deg.split(' ')[1]
    data['glon_min'] = glon_deg.split(' ')[2]
    data['glat_deg'] = glat_deg.split(' ')[0]
    data['glat_dir'] = glat_deg.split(' ')[1]
    data['glat_min'] = glat_deg.split(' ')[2]
    data['toffset'] = almuten_toffset_dict[toffset]
    data['hsys'] = 'P'

    return data


def fetch_almuten_soup(data):
    URL_ALMUTEN = "https://almuten.net/"

    response = requests.post(URL_ALMUTEN, data=data)

    html = response.text
    soup = BeautifulSoup(html, 'html.parser')

    return soup


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


def parse_almuten_star(soup):
    tables = soup.find_all('table')

    table = tables[0]

    '''
    th info
        星體
        黃經度數
        落宮
        守護宮
        曜升宮
        先天黃道狀態
        附屬狀態
        本垣
        曜升
        三分
        界
        十度
        落
        陷
        分數
    '''
    trs = table.find_all('tr')[2:]

    for tr in trs:
        tds = tr.find_all('td')
        star = almuten_star_sign_mapping[tds[0].text.strip()]
        house = int(tds[5].text.strip())
        lord_house_vec = [int(item) if item != '' else -1 for item in tds[6].text.strip().split(' ')]
        score = tds[17].text.strip()
        score = 0 if score == '0 P' else score

        star_obj = Star(star=star, house=house, score=score, lord_house_vec=lord_house_vec)

        if star in ['上升', '中天']:
            continue

        star_dict[star] = star_obj

        # print(star_obj)

    # print('------------------ End star_obj ------------------')

    # 解析互溶接纳
    table_feature = tables[2]
    # print(f'\n宫神星网互溶接纳信息：{table_feature}')

    trs_feature = table_feature.find_all('tr')

    for tr in trs_feature:
        td = tr.find('td')

        if td is None:
            continue

        td_text = tr.find('td').text

        feature = ''
        if '互容接納' in td_text:
            feature = '互容接纳'
        elif '互容' in td_text:
            feature = '互容'
        elif '接納' in td_text:
            feature = '接纳'
        else:
            continue

        matches = re.findall(r'\((.*?)\)', td_text)

        star_a, star_b = almuten_star_sign_mapping[td.find_all('em')[0].text], almuten_star_sign_mapping[td.find_all('em')[1].text]

        r = Recepted(star_a=star_a, star_b=star_b, action_name=feature, level=matches[-1])
        # star_dict[star_a].recepted_vec_old.append(r)

        # 互溶接纳、接纳只保留互溶接纳
        if star_b in star_dict[star_a].recepted_dict and star_dict[star_a].recepted_dict[star_b].action_name == '接纳' and feature == '互容接纳':
            star_dict[star_a].recepted_dict[star_b] = r
        elif star_b not in star_dict[star_a].recepted_dict:
            star_dict[star_a].recepted_dict[star_b] = r


    # for star, star_obj in star_dict.items():
    #     print(f'{star_obj}')


def fetch_ixingpan_soup(name, female=1, dist=1550, birthday_time='1962-08-08 20:00', dst=0):
    # dst: Daylight Saving Time
    birthday = birthday_time.split(' ')[0]
    birth_time = birthday_time.split(' ')[1]

    url = f"https://xp.ixingpan.com/xp.php?type=natal&name={name}&sex={female}&dist={dist}&date={birthday}&time={birth_time}&dst={dst}&hsys=P"
    logger.info(f'爱星盘请求串 {url}')

    # 发送GET请求
    response = requests.get(url, cookies={'xp_planets_natal': '0,1,2,3,4,5,6,7,8,9,25,26,27,28,15,19,10,29'})

    # 获取返回的HTML源码
    html_str = response.text
    soup = BeautifulSoup(html_str, 'html.parser')

    return soup


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




almuten_toffset_dict = {
    'GMT_12': '-720',
    'GMT_11': '-660',
    'GMT_10': '-600',
    'GMT_9': '-540',
    'GMT_8': '-480',
    'GMT_7': '-420',
    'GMT_6': '-360',
    'GMT_5': '-300',
    'GMT_4': '-240',
    'GMT_3': '-180',
    'GMT_2': '-120',
    'GMT_1': '-60',
    'GMT_0': '0',
    'GMT_ADD_1': '60',
    'GMT_ADD_2': '120',
    'GMT_ADD_3': '180',
    'GMT_ADD_4': '240',
    'GMT_ADD_5': '300',
    'GMT_ADD_6': '360',
    'GMT_ADD_7': '420',
    'GMT_ADD_8': '480',
    'GMT_ADD_9': '540',
    'GMT_ADD_10': '600',
    'GMT_ADD_11': '660',
    'GMT_ADD_12': '720'
}


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


def load_knowledge_data_old():
    with open('./knowledge.csv', 'r') as f:
        for line in f.readlines():
            line = line.strip()
            key = line.split(',')[0]
            val = line.split(',')[1]
            knowledge_dict_old[key] = val


def load_jobs_file():
    def parse_jobs_csv(file_path):
        # jobs_dict = {}
        with open(file_path, 'r') as file:
            lines = file.readlines()
            i = 0

            key, keywords, job = '', '', ''

            for line in lines:
                line = line.strip()
                if line == '':
                    continue

                if line == '「星性」':
                    break

                if i == 0:
                    key = line
                    i += 1
                elif i == 1:
                    keywords = line
                    i += 1
                elif i == 2:
                    job = line
                    i += 1

                if i > 2:
                    i = 0

                    jobs_dict[key] = (keywords, job)
                    key, keywords, job = '', '', ''

        # return jobs_dict

    # 调用函数解析 "jobs.csv" 文件
    file_path = './jobs.csv'
    parsed_data = parse_jobs_csv(file_path)

    # 解析工作星性
    def parse_jobs_star_csv(file_path):
        flag = False
        with open(file_path, 'r') as file:
            lines = file.readlines()
            for line in lines:
                line = line.strip()
                if line  == '':
                    continue

                if line == '「星性」':
                    flag = True
                    continue

                if not flag:
                    continue

                # print(line)
                key = line.split('：')[0]
                val = line.split('：')[1]

                jobs_star_dict[key] = val

    parse_jobs_star_csv('./jobs.csv')
    return parsed_data


def get_dist_by_location(target_province, target_city, target_district) -> Tuple[str, str]:
    '''
    :param target_province:
    :param target_city:
    :param target_district:
    :return: [error_msg, dist_code]
    '''

    with open('./file/ixingpan_area.json', 'r') as file:
        json_data = json.load(file)

        error_msg, dist = '', ''
        # 直辖市直接找 target_district, 找不到当前信息，用上一层的
        if target_city == '市辖区':
            if target_province in json_data:
                input_string = json_data[target_province][target_province]
                kv = {pair.split('|')[0]: pair.split('|')[1] for pair in input_string.split(',')}

                if target_district in kv:
                    return error_msg, kv[target_district]
                else:
                    return error_msg, kv[target_province]

        # 非直辖市
        for key, desc in zip([target_province, target_city, target_district], ['省份', '城市', '区/市(县)']):
            if key not in json_data and desc in {'省份', '城市'}:
                return f'未找到{key}位置', ''

            if desc == '区/市(县)':
                input_string = json_data
                kv = {pair.split('|')[0]: pair.split('|')[1] for pair in input_string.split(',')}

                if key in kv:
                    return error_msg, kv[key]
                elif target_city in kv:
                    return error_msg, kv[target_city]
                else:
                    return f'未找到:{target_district}', ''

            json_data = json_data[key]



def parse_glon_glat(soup):
    tables = soup.find_all('table')
    table = tables[0]

    # print(table)
    tbody = table.find('tbody')
    trs = tbody.find_all('tr')

    soup_tmp = trs[1]
    td = trs[1].find_all('td')[1]
    # print(td)
    pattern = r'(\d+°\d+[EW]\s\d+°\d+[NS])'
    match = re.search(pattern, td.text.strip())

    if match:
        coordinates = match.group(1)
        logger.debug(f'获取经纬度结果：{coordinates}')
        # print('获取经纬度结果：', coordinates)
    else:
        logger.fatal('未匹配到数据')
        # print("未匹配到数据")
        exit(0)

    # 将 104°09E 30°00N 转换成：glon_deg:104 E 09	glat_deg:30 N 00
    input_str = coordinates.strip()

    trans_pattern = r'((\d+)°(\d+)[EW] (\d+)°(\d+)[NS])'
    match = re.search(trans_pattern, input_str)

    # print(match.groups())
    if match:
        glon_deg = f'{match.group(2)} E {match.group(3)}'
        glat_deg = f'{match.group(4)} N {match.group(5)}'

        logger.debug(f'解析经纬度结果：{glon_deg} {glat_deg}')
        # print('获取经纬度结果：', glon_deg, glat_deg)
    else:
        logger.fatal('ERROR！解析经纬度信息错误')
        # print('ERROR！解析经纬度信息错误')
        exit(0)


    return glon_deg, glat_deg


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
