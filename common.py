# -*- coding: utf-8 -*-
from typing import Dict, List, Tuple
import json
import datetime
import os
import requests
import re
from enum import Enum
from bs4 import BeautifulSoup
import configparser
import cpca

import logging
import pickle


# 创建日志记录器
logger = logging.getLogger('commonLogger')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


logger.setLevel(logging.DEBUG)
USE_CACHE = True


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


def basic_analyse(customer_name, content) -> Tuple[str, str]:
    error_msg, soup_ixingpan, soup_almuten = _get_basic_soup_from_http(customer_name=customer_name, content=content)

    if error_msg != '':
        return error_msg, None

    # 加载知识库
    # knowledge_dict, knowledge_dict_old, jobs_dict, jobs_star_dict = _load_local_file()
    _parse_almuten_star(soup_almuten)
    parse_almuten_house()

    # 解析爱星盘结果
    parse_ixingpan_star(soup_ixingpan)
    parse_ixingpan_house(soup_ixingpan)
    parse_ixingpan_aspect(soup_ixingpan)

    get_square()
    get_house_energy()

    if IS_DEBUG:
        for star, star_obj in star_dict.items():
            print(f'{star_obj}')

        for k, v in house_dict.items():
            print(f'{v}')

    parse_love()
    parse_marrage_2()
    parse_marrage()
    parse_wealth()
    parse_health()
    print('----------------------------')
    parse_work()
    parse_asc_star()
    parse_study()
    parse_nature()

    ret_vec = []
    logger.error("~~~~~~~~~~~~~~~~~~~~~~~~~~")
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')

    key_vec = ['个性显现及生活领域上的重点', '恋爱', '婚姻', '财富', '事业', '健康', '学业', '性格分析']
    for key in key_vec:
        if key not in all_trace_dict:
            continue

        field_dict = all_trace_dict[key]

        ret_vec.append(f'解析「{key}」')
        # f.writelines(f'\n--------------------------- 解析「{key}」---------------------------')
        for biz, sub_vec in field_dict.items():
            ret_vec.append(f'『{biz}』:')
            # f.writelines(f'\n『{biz}』:\n')
            # print(f'\n『{biz}』:')
            for index, sub in enumerate(sub_vec, start=1):
                # print(f'{index}、{sub}')
                # f.writelines(f'{index}、{sub}\n')
                ret_vec.append(f'{index}、{sub}')


def _get_basic_soup_from_http(customer_name, content) -> Tuple[str, BeautifulSoup, BeautifulSoup]:
    logger.debug('---------------invoke get_basic_soup_from_http ---------------------')
    folder_path = f'./cache/basic/{customer_name}'
    os.makedirs(folder_path, exist_ok=True)

    """ ixingpan Http Result. 有 cache 文件则从文件加载，没有走 http 请求 """
    filename_ixingpan = f'{folder_path}/{customer_name}_ixingpan.pickle'

    error_msg, birthday, dist, is_dst, toffset, location = _prepare_http_data(content=content, name=customer_name)
    if error_msg != '':
        return error_msg, None, None

    if USE_CACHE and os.path.exists(filename_ixingpan):
        soup_ixingpan = _dump_or_load_http_result(filename=filename_ixingpan, is_load_mode=True)
        logger.info(f'成功从本地加载本命盘数据，File=[{filename_ixingpan}]')
    else:
        soup_ixingpan = _fetch_ixingpan_soup(name=customer_name, dist=dist, birthday_time=birthday, dst=is_dst, female=1)
        _dump_or_load_http_result(filename=filename_ixingpan, soup_obj=soup_ixingpan, is_load_mode=False)
        logger.info(f'走Http请求获取爱星盘排盘信息，并且 Dump BeautifulSoup to File:{filename_ixingpan}')

    # Update 宫神星要用到的:glon_deg, glat_deg. 取自ixingpan结果中的
    err_no, glon_deg, glat_deg = _parse_glon_glat(soup=soup_ixingpan)
    if err_no != '':
        return err_no, None, None

    """ almuten Http Result. """
    filename_almuten = f'{folder_path }/{customer_name}_almuten.pickle'

    if USE_CACHE and os.path.exists(filename_almuten):
        soup_almuten = _dump_or_load_http_result(filename=filename_almuten, is_load_mode=True)
        logger.info(f'成功从本地加载本命盘数据，File=[{filename_almuten}]')
    else:
        post_data = _build_almuten_http_data(name=customer_name, birthinfo=birthday, loc=location, glon_deg=glon_deg, glat_deg=glat_deg, toffset=toffset, is_dst=is_dst)
        soup_almuten = _fetch_almuten_soup(post_data)

        _dump_or_load_http_result(filename=filename_almuten, soup_obj=soup_almuten, is_load_mode=False)
        logger.info(f'走Http请求获取「宫神星」排盘信息，并且 Dump BeautifulSoup to File:{filename_almuten}')

    return error_msg, soup_ixingpan, soup_almuten


def _prepare_http_data(content, name=None) -> Tuple[str, str, str, str, str, str]:
    """
    获取http请求所需的参数：birthday, dist, is_dst, toffset, f'{province}{city}{area}'
    :param content:
    :param name:
    :return: error_msg, birthday, dist, is_dst, toffset, f'{province}{city}{area}'
    """
    def _parse_location(inp_str) -> Tuple[str, str, str]:
        df = cpca.transform([inp_str])

        province = df.iloc[0]['省']
        city = df.iloc[0]['市']
        area = df.iloc[0]['区']

        return province, city, area

    def _parse_time(text: str) -> str:
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

    def _get_dist_by_location(target_province, target_city, target_district) -> Tuple[str, str]:
        '''
        根据 ixingpan_area.json文件、用户输入的省、市、区来查找 dist（爱星盘http参数）
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

                    dist = kv[target_district] if target_district in kv else kv[target_province]
                else:
                    error_msg = f'未找到:{target_province}'

                return error_msg, dist

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

    province, city, area = _parse_location(content)
    birthday = _parse_time(content)

    if not province or not city or not area or not birthday:
        return '解析出生地/生时失败', birthday, '', '', '', ''

    error_msg, dist = _get_dist_by_location(target_province=province, target_city=city, target_district=area)

    # TODO: dynamic
    is_dst = '0'
    toffset = 'GMT_ADD_8'

    return error_msg, birthday, dist, is_dst, toffset, f'{province}{city}{area}'


def _dump_or_load_http_result(filename, soup_obj=None, is_load_mode=True):
    def _load_http_result(sub_file) -> BeautifulSoup:
        with open(sub_file, 'rb') as file:
            deserialized_soup = pickle.load(file)

            return deserialized_soup

    def _dump_http_result(sub_file: str, sub_soup_obj: BeautifulSoup):
        # 将 soup 对象序列化到文件
        with open(sub_file, 'wb') as file:
            pickle.dump(sub_soup_obj, file)

    if is_load_mode:
        return _load_http_result(filename)
    else:
        _dump_http_result(filename, soup_obj)


def _fetch_ixingpan_soup(name, female=1, dist='1550', birthday_time='1962-08-08 20:00', dst='0'):
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


def _parse_glon_glat(soup) -> Tuple[str, str, str]:
    '''

    :param soup:
    :return:
    '''
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
        return '服务器内部错误', '', ''

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
        return '服务器内部错误', '', ''

    return '', glon_deg, glat_deg


def _build_almuten_http_data(name, birthinfo, loc, glon_deg, glat_deg, toffset, is_dst):
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
    data['hsys'] = 'P'

    _almuten_toffset_dict = {
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

    data['toffset'] = _almuten_toffset_dict[toffset]

    return data


def _fetch_almuten_soup(data):
    URL_ALMUTEN = "https://almuten.net/"

    response = requests.post(URL_ALMUTEN, data=data)

    html = response.text
    soup = BeautifulSoup(html, 'html.parser')

    return soup


def _load_local_file():
    """
    knowledge_web.ini
    knowledge.csv
    jobs.csv
    ixingpan_area.json

    :return:
    """
    knowledge_dict: Dict[str, Dict[str, str]] = {}
    knowledge_dict_old: Dict[str, str] = {}
    jobs_dict: Dict[str, Tuple[str, str]] = {}
    jobs_star_dict: Dict[str, str] = {}

    def _load_knowledge_file():
        # Load knowledge_web.ini
        config = configparser.ConfigParser()

        file_name = './file/knowledge_web.ini'
        config.read(file_name)

        # 遍历指定section的所有option
        for section_name in config.sections():

            for option_name in config.options(section_name):
                value = config.get(section_name, option_name)

                if section_name in knowledge_dict:
                    knowledge_dict[section_name][option_name] = value
                else:
                    knowledge_dict[section_name] = {option_name: value}

    def _load_knowledge_data_old():
        with open('./file/knowledge.csv', 'r') as f:
            for line in f.readlines():
                line = line.strip()
                key = line.split(',')[0]
                val = line.split(',')[1]
                knowledge_dict_old[key] = val

    def _load_jobs_file():
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
        file_path = './file/jobs.csv'
        parsed_data = parse_jobs_csv(file_path)

        # 解析工作星性
        def parse_jobs_star_csv(file_path):
            flag = False
            with open(file_path, 'r') as file:
                lines = file.readlines()
                for line in lines:
                    line = line.strip()
                    if line == '':
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

        parse_jobs_star_csv(file_path)
        return parsed_data

    _load_knowledge_file()
    _load_knowledge_data_old()
    _load_jobs_file()

    return knowledge_dict, knowledge_dict_old, jobs_dict, jobs_star_dict


def _parse_almuten_star(soup):
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

