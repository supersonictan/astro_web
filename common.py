# -*- coding: utf-8 -*-
from typing import Dict, List, Tuple
import web
import json
import datetime
import os
import requests
import re
from bs4 import BeautifulSoup
import configparser
import cpca

import logging
import pickle
from Const import *


# 创建日志记录器
logger = logging.getLogger('common.py')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


logger.setLevel(logging.DEBUG)
# USE_CACHE = True
KNOWLEDGE_KEY = 'knowledge_dict'

NUM_WHITELIST = {'1', '2', '3', '4', '5', '6', '7'}


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


def basic_analyse():
    logger.debug('-------------- invoke basic_analyse --------------------')
    customer_name = get_session(FROMUSER)
    content = get_session(CONTENT)

    soup_ixingpan, soup_almuten = None, None
    error_msg, soup_ixingpan, soup_almuten = _get_basic_soup_from_http(customer_name=customer_name, content=content)
    if error_msg != '':
        set_session(ERROR, COMMON_ERR_MSG)
        logger.error(f'basic_analyse._get_basic_soup_from_http 执行失败，err={error_msg}')
        return

    dump_obj(soup_ixingpan, get_session(FILENAME_SOUP1))
    dump_obj(soup_almuten, get_session(FILENAME_SOUP2))

    # 解析宫神星网结果
    _parse_almuten_star(soup_almuten)

    # 解析爱星盘结果
    _parse_ixingpan_star(soup_ixingpan)
    _parse_ixingpan_house(soup_ixingpan)
    _parse_ixingpan_aspect(soup_ixingpan)

    if False:
        house_dict_tmp = get_session(SESS_KEY_HOUSE)
        for id, house_obj in house_dict_tmp.items():
            logger.debug(f'{id}宫，宫内星: {house_obj.loc_star}')

        logger.debug('-----------------------------')
        star_dict_tmp = get_session(SESS_KEY_STAR)
        for name, star_obj in star_dict_tmp.items():
            logger.debug(f'{name}, {star_obj.house}宫')

    get_square()

    parse_asc_star()
    parse_love()
    parse_marrage_2()
    parse_marrage()
    parse_work()
    parse_study()

    dump_obj(get_session(SESSION_KEY_TRACE), get_session(FILENAME_REPORT))
    # return error_msg, soup_ixingpan, soup_almuten
    # get_house_energy()



    # parse_wealth()
    # parse_health()
    # print('----------------------------')


    # parse_nature()
    #
    # ret_vec = []
    # logger.error("~~~~~~~~~~~~~~~~~~~~~~~~~~")
    # print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    #
    # key_vec = ['个性显现及生活领域上的重点', '恋爱', '婚姻', '财富', '事业', '健康', '学业', '性格分析']
    # for key in key_vec:
    #     if key not in all_trace_dict:
    #         continue
    #
    #     field_dict = all_trace_dict[key]
    #
    #     ret_vec.append(f'解析「{key}」')
    #     # f.writelines(f'\n--------------------------- 解析「{key}」---------------------------')
    #     for biz, sub_vec in field_dict.items():
    #         ret_vec.append(f'『{biz}』:')
    #         # f.writelines(f'\n『{biz}』:\n')
    #         # print(f'\n『{biz}』:')
    #         for index, sub in enumerate(sub_vec, start=1):
    #             # print(f'{index}、{sub}')
    #             # f.writelines(f'{index}、{sub}\n')
    #             ret_vec.append(f'{index}、{sub}')


def parse_study():
    # 解析：初等学业、高等学业
    is_debug = web.ctx.env['is_debug']
    star_dict = web.ctx.env["star_dict"]
    house_dict = web.ctx.env["house_dict"]
    knowledge_dict = web.ctx.env[KNOWLEDGE_KEY]

    ruler_3 = house_dict[3].ruler
    ruler_9 = house_dict[9].ruler

    ruler_3_house = star_dict[ruler_3].house
    ruler_9_house = star_dict[ruler_9].house

    key3 = f'3飞{ruler_3_house}'
    key9 = f'9飞{ruler_9_house}'
    junior_desc = knowledge_dict['初等学业飞星'][key3]
    senior_desc = knowledge_dict['高等学业飞星'][key9]

    set_trace_info('学业', '高中前', [junior_desc])
    set_trace_info('学业', '高中后', [senior_desc])

    # 3、9宫落⭐️
    star_in_3 = house_dict[3].loc_star
    star_in_9 = house_dict[9].loc_star

    for id in [3, 9]:
        for s in house_dict[id].loc_star:
            key = f'{s}{id}宫'

            sub_dict = knowledge_dict['初等学业飞星'] if id == 3 else knowledge_dict['高等学业飞星']

            if id == 3 and key in sub_dict:
                set_trace_info('学业', '高中前', [sub_dict[key]])
            elif id == 9 and key in sub_dict:
                set_trace_info('学业', '高中后', [sub_dict[key]])

def parse_asc_star():
    is_debug = web.ctx.env['is_debug']
    star_dict = web.ctx.env["star_dict"]
    house_dict = web.ctx.env["house_dict"]
    knowledge_dict = web.ctx.env[KNOWLEDGE_KEY]

    # 解析命主星落宫
    asc_star = house_dict[1].ruler
    asc_house = star_dict[asc_star].house

    key = f'命主星{asc_house}宫'
    # logger.debug(key)
    desc = knowledge_dict['命主星落宫'][key]
    logger.debug('3333333333333333333333333')

    reason_debug = f'【{key}】' if is_debug else ''

    set_trace_info(DomainAsc, '重点概括', [f'{reason_debug}{desc}'])


def parse_work():
    # 10r 飞宫

    """
    10宫飞1宫
    关键词：自我价值实现
    职业：运动员、主持人、模特、销售、自由职业、创业
    """
    is_debug = web.ctx.env['is_debug']
    star_dict = web.ctx.env["star_dict"]
    house_dict = web.ctx.env["house_dict"]
    jobs_dict = web.ctx.env['knowledge_dict']['职业-飞星']
    jobs_star_dict = web.ctx.env['knowledge_dict']['职业-星性']

    # 获取10r飞宫
    ruler10 = house_dict[10].ruler
    ruler10_loc = star_dict[ruler10].house

    key = f'10宫飞{ruler10_loc}宫'
    answer = jobs_dict[key]
    work_keyword = answer.split('可能的职业：')[0].split('关键词-')[-1]
    work_job = answer.split('可能的职业：')[1]
    # work_trace_dict['事业关键词'] = [f'【{key}】{work_keyword}']
    reason_debug = f'【{key}】' if is_debug else ''
    set_trace_info('事业', '事业关键词', [f'{reason_debug}{work_keyword}'])

    set_trace_info('事业', '一档适合的职业', [f'{reason_debug}{work_job}'])

    sub_vec = []
    for loc_star in house_dict[10].loc_star:
        search_key = f'{loc_star}10宫'
        val = jobs_star_dict[search_key]

        reason_debug = f'【{search_key}】' if is_debug else ''
        sub_vec.append(f'{reason_debug}{val}')

    if len(sub_vec) > 0:
        set_trace_info('事业', '二档适合的职业', sub_vec)


def parse_marrage():
    is_debug = web.ctx.env['is_debug']
    star_dict = web.ctx.env["star_dict"]
    house_dict = web.ctx.env["house_dict"]

    """1. 配偶是什么类型？观测7宫的宫内星和宫主星，星性可代表特征、类型。"""
    appearance_dict = web.ctx.env['knowledge_dict']['7宫星看配偶']
    ruler_7 = house_dict[7].ruler

    trace_vec_appearance = []
    reason_debug = f'【7r={ruler_7}】' if is_debug else ''
    msg = f'{reason_debug}{appearance_dict[ruler_7]}'
    trace_vec_appearance.append(msg)

    for star_name in house_dict[7].loc_star:
        if star_name in {'冥王', '天王', '海王', '北交'}:
            continue

        reason_debug = f'【7宫内{star_name}】' if is_debug else ''
        trace_vec_appearance.append(f'{reason_debug}{appearance_dict[star_name]}')

    set_trace_info('婚姻', '配偶是什么类型的', trace_vec_appearance)

    '''
    黄道状态是否良好（分数的高低）代表配偶自身的能力or先天健康
    7飞去的宫位，代表了配們追逐or重视的领域，例如：7飞10.
    代表『伴信有事业心•追求建功动业，社会地位，或省一分注重樂省价子等
    TODO：替换受克，得吉
    '''

    knowledge_dict_old = web.ctx.env['knowledge_dict']['宫主飞星']
    ruler_7_house = star_dict[ruler_7].house
    search_key = f'7飞{ruler_7_house}'
    reason_debug = f'【{search_key}】' if is_debug else ''
    knowledge_msg = f'{reason_debug}{knowledge_dict_old[search_key]}'
    set_trace_info('婚姻', '配偶特点', [knowledge_msg])

    '''
    2. 配偶什么年纪？
    - 木星土星主大5-7岁
    - 日月主大3-5岁
    - 金水火主上下三岁
    - 甚至偏小，但是同时要参专盘主的命主星，比大小；
    - 7宫多星时可尝试叠加
    '''
    marriage_age_dict = web.ctx.env['knowledge_dict']['7宫星看配偶年龄']

    reason_debug = f'【7r={ruler_7}】' if is_debug else ''
    trace_age_vec = [f'{reason_debug}配偶{marriage_age_dict[ruler_7]}']
    for star_name in house_dict[7].loc_star:
        if star_name in {'冥王', '天王', '海王', '北交'}:
            continue

        reason_debug = f'【7宫内{star_name}】' if is_debug else ''
        trace_age_vec.append(f'{reason_debug}配偶{marriage_age_dict[star_name]}')

    set_trace_info('婚姻', '配偶年龄', trace_age_vec)

    '''
    3. 会不会离婚
    传统说，我们不喜欢太多的星进入婚姻宮，尤其是三王星，
    - 冥王，代表离异 or 复婚。
    - 天王，代表聚少离多 or 离异 or 不寻常的、有违世俗的婚姻。
    - 海王，一般多婚，或婚姻纠缠不清
    - 土星，年龄大，压力大
    - 1r-7r 对冲，轴线也算，无论是宫内星对冲，还是飞出去对冲，都代表大妻矛店大，容易不相让。
    - 1r-7r 黃道分数相差过大，也容易阴阳失衡，
    - 有时候日月相差过大也会有这种阴阳失调的问题
    - 7r 被克，被任何星体沖，都不理想：
    - 凶星（土火三王）5度以内，压上升轴or 下降轴，都会特别发凶，影响感情和决策。
    '''
    is_pluto_7 = 1 if '冥王' in house_dict[7].loc_star else 0
    is_uranus_7 = 1 if '天王' in house_dict[7].loc_star else 0
    is_neptune_7 = 1 if '海王' in house_dict[7].loc_star else 0
    is_1r_7r_bad = 0
    is_1r_7r_score_diff = 0

    ruler_1 = house_dict[1].ruler

    r1_aspect_vec = list(star_dict[ruler_1].aspect_dict.values())
    for obj in r1_aspect_vec:
        if ruler_7 == obj.star_b and obj.aspect in {'刑', '冲'}:
            is_1r_7r_bad = 1
            break

    score_7r = star_dict[ruler_7].score
    score_1r = star_dict[ruler_1].score
    is_1r_7r_score_diff = abs(int(score_1r) - int(score_7r))

    # 下降相位
    axis_vec = []
    for _, obj in star_dict['下降'].aspect_dict.items():
        if obj.aspect != '合':
            continue

        if obj.star_b in {'冥王', '天王', '海王', '土星', '火星'}:
            axis_vec.append(f'{obj.star_b}合下降轴,特别发凶,会影响感情和决策')


    trace_divorce_vec = []
    msg_pluto = '有可能出现离婚或离婚再复婚的情况' if is_pluto_7 else ''
    msg_uranus = '有可能出现聚少离多或离异的情况' if is_uranus_7 else ''
    msg_neptune = '有可能出现多次婚姻或者婚姻纠缠不清的情况' if is_neptune_7 else ''

    if len(axis_vec) != 0:
        trace_divorce_vec.extend(axis_vec)

    if msg_pluto != '':
        trace_divorce_vec.append(msg_pluto)
    if msg_uranus != '':
        trace_divorce_vec.append(msg_uranus)
    if msg_neptune != '':
        trace_divorce_vec.append(msg_neptune)

    trace_divorce_vec = [item for item in trace_divorce_vec if item != '']
    if len(trace_divorce_vec) == 0:
        trace_divorce_vec.append('0')
    set_trace_info('婚姻', '未来离婚概率', trace_divorce_vec)

    '''
    4. 配偶是否有外遇？
    7-11, 7-11-12， 7-12，一般来说，看到这个配置，我们可以断定盘主配偈的桃花非常的旺盛，
    但是在实际论盘中，需要考虑飞星和接纳的因素，飞星和接纳都是有方向的
    因此通过这个可以断定，是桃花主动来找这个人的配個，还是配偶主动去找桃花，互容真的相互的。
    从这个层面来给客户建议：7-11-1 的黄道状态来判定三人之间的实力。
    '''
    trace_affair_vec = []

    if search_key == '7飞11':
        trace_affair_vec.append(f'有可能配偶去找桃花。{knowledge_dict_old[search_key]}')
    # if search_key == '7飞11':
    #     trace_affair_vec.append(f'【{search_key}】可能配偶去找桃花。{knowledge_dict_old[search_key]}')
    # else:
    #     trace_affair_vec.append(f'未检测到！！{search_key}: 可能配偶去找桃花。')

    # 是否有11飞7，7飞12
    ruler_11, ruler_12 = house_dict[11].ruler, house_dict[12].ruler
    ruler_11_loc, ruler_12_loc = star_dict[ruler_11].house, star_dict[ruler_12].house
    tmp_key = '11飞7'
    if ruler_11_loc == 7:
        trace_affair_vec.append(f'可能有桃花来找配偶。{knowledge_dict_old[tmp_key]}')

    # tmp_key = '12飞7'
    # if ruler_12_loc == 7:
    #     trace_affair_vec.append(f'【{tmp_key}】可能有桃花来找配偶。{knowledge_dict_old[tmp_key]}')
    # else:
    #     trace_affair_vec.append(f'未检测到！！{tmp_key}: 可能有桃花来找配偶。')

    # trace_affair_vec.append(f'需要check下「互溶、接纳」再来确定！7r:{ruler_7}，11r:{ruler_11}, 12r:{ruler_12}')

    if len(trace_affair_vec) == 0:
        trace_affair_vec.append('新盘显示不会离婚.')

    set_trace_info('婚姻', '未来配偶有外遇的概率', trace_affair_vec)

    '''
    5. 婚姻/配偶能否给自己带财？
    - 1r2r 得7r接纳，或者 1r2r 与7互容时候，婚姻可带财。
    - 7r 飞 1r2r 也会有类似作用，但是能量低些，且最好 7r庙旺。
    - 如若 7r接纳互容5r，说明有了孩子，伴侣会给孩子钱
    :return:
    '''
    trace_money_vec = []

    ruler_2 = house_dict[2].ruler

    msg = ''
    # msg = f'未检测到！！1r={ruler_1}被7r={ruler_7}接纳！'
    if ruler_7 in star_dict[ruler_1].recepted_dict:
        msg = f'1r{ruler_1}被7r{ruler_7}{star_dict[ruler_1].recepted_dict[ruler_7].action_name}，可利财！'

    if msg != '':
        trace_money_vec.append(msg)

    msg = ''
    if ruler_7 in star_dict[ruler_2].recepted_dict:
        msg = f'2r{ruler_2}被7r{ruler_7}{star_dict[ruler_2].recepted_dict[ruler_7].action_name}，可利财！'

    if msg != '':
        trace_money_vec.append(msg)

    msg = f'未检测到！！7r{ruler_7}与1、2r互容！'
    for key, obj in star_dict[ruler_7].recepted_dict.items():
        if '互容' not in obj.action_name:
            continue

        if obj.star_b == ruler_1:
            msg = f'7r{ruler_7}与1r{ruler_1}{obj.action_name}，可利财！'
            trace_money_vec.append(msg)

        if obj.star_b == ruler_2:
            msg = f'7r{ruler_7}与2r{ruler_2}{obj.action_name}，可利财！'
            trace_money_vec.append(msg)

    # if msg == f'未检测到！！7r{ruler_7}与1、2宫主互容！':
    #     trace_money_vec.append(msg)

    # 看7r是否飞1、2
    is_7r_loc1 = 1 if star_dict[ruler_7].house == 1 else 0
    is_7r_loc2 = 1 if star_dict[ruler_7].house == 2 else 0

    if is_7r_loc1:
        trace_money_vec.append('7飞1，配偶可以帮你')
    if is_7r_loc2:
        trace_money_vec.append('7飞2，配偶可以利你财')

    # trace_money_vec.append(f'7飞1={is_7r_loc1}, 7飞2={is_7r_loc2}, 7r score={score_7r}')

    # marriage_trace_dict['婚姻/配偶能否给自己带财?'] = trace_money_vec
    set_trace_info('婚姻', '婚姻/配偶能否给自己带财', trace_money_vec)


def parse_love():
    is_debug = web.ctx.env['is_debug']
    '''
    1、入星
    一般米说，进入5宮的星体，或者5宫主，代表"自己容易遇到的类型"，
    或者我们实际恋爱对象的特征，这个和"我们自己喜欢的类型"不是一回事。
    日、月、木：大星体，代表桃花多旺，但不一定好。要好至少是苗旺的，或至少和1~2宫发生关联的。
    三王星与 5r/金星：桃花容易问题多，烂桃花，不伦恋，多角恋
    '''
    star_dict = web.ctx.env["star_dict"]
    house_dict = web.ctx.env["house_dict"]

    loc_star_5_dict = web.ctx.env['knowledge_dict']['5宫落星的恋爱解释']

    # check 日、月、木是否在5宫
    ruler_5 = house_dict[5].ruler
    ruler5_score = int(star_dict[ruler_5].score)

    tmp_set = {'太阳', '月亮', '木星'}
    n = len(tmp_set & set(house_dict[5].loc_star))
    msg = '【没有太阳、月亮、木星在5宫】桃花数量不属于多的。' if is_debug else '桃花数量不属于多的.'
    if n > 0:
        msg = f'桃花数量属于多的，太阳、月亮、木星有{n}个在5宫.' if is_debug else '桃花数量属于多的.'

    if is_debug:
        web.ctx.env['trace_info']['恋爱']['5r得分'] = [f'5r score={ruler5_score}']

    web.ctx.env['trace_info']['恋爱']['桃花数量'] = [msg]

    trace_loc_star_vec = []
    loc_star_vec = house_dict[5].loc_star
    for star, msg in loc_star_5_dict.items():
        if star in loc_star_vec:
            msg_loc = f'【{star}落5宫】{msg}' if is_debug else f'{msg}'
            trace_loc_star_vec.append(msg_loc)

    msg_loc_star = f'(不一定发生)【5宫主{ruler_5}】{loc_star_5_dict[ruler_5]}' if is_debug else f'(不一定发生){loc_star_5_dict[ruler_5]}'
    trace_loc_star_vec.append(msg_loc_star)

    # check 三王星和5r/金星相位
    tmp_vec = [ruler_5, '金星']
    bad_tmp_vec = ['冥王', '海王', '天王']
    for target in tmp_vec:
        for bad_star in bad_tmp_vec:
            if bad_star in star_dict[target].aspect_dict and star_dict[target].aspect_dict[bad_star].aspect in {'冲', '刑'}:
                msg = loc_star_5_dict[bad_star]

                if bad_star in star_dict[target].aspect_dict and star_dict[target].aspect_dict[bad_star].aspect in {'冲', '刑'}:
                    msg = loc_star_5_dict[bad_star]

                    reason = f'【{target}{star_dict[target].aspect_dict[bad_star].aspect}{bad_star}】'
                    if not is_debug:
                        reason = ''

                    trace_loc_star_vec.append(f'{reason}{msg}')

    web.ctx.env['trace_info']['恋爱']['恋爱容易遇到的类型'] = trace_loc_star_vec


    '''
    2、飞星
    1飞5，容易恋爱脑，尤其是1落馅时
    5飞1，桃花来找自己，如果5庙旺，容易生小孩，如果落陷，来讨货
    5飞8，5飞12 不太容易受孕，生小孩会晚，秘密恋情或地下恋情
    5飞9异地恋，5飞10和领导上级恋爱，5飞6办公室恋情
    5特別容易与2r、8r产生刑克，代表容易因为桃花破财
    '''
    ruler5_fly_dict = web.ctx.env['knowledge_dict']['5飞星的恋爱解释']

    star_5_loc = star_dict[ruler_5].house
    ruler1_score = int(star_dict[house_dict[1].ruler].score)
    star_1_loc = star_dict[house_dict[1].ruler].house

    ruler2 = house_dict[2].ruler
    ruler8 = house_dict[8].ruler

    # '1飞5': '容易恋爱脑，尤其是1落馅时'
    tmp_vec = []
    if star_1_loc == 5 and ruler1_score <= 0:
        tmp_reason = '【1飞5,且1r 分数<0】' if is_debug else ''
        tmp_vec.append(f'{tmp_reason}有可能是恋爱脑的配置.')

    # logger.debug('!4.2 4.2 4.2 4.2 4.2')
    tmp_key = f'5飞{star_5_loc}'
    if tmp_key in ruler5_fly_dict:
        tmp_reason = f'【{tmp_key}】' if is_debug else ''
        tmp_vec.append(f'{tmp_reason}{ruler5_fly_dict[tmp_key]}')


    # 5r, 2r, 8r 是否刑克
    if ruler2 in star_dict[ruler_5].aspect_dict and star_dict[ruler_5].aspect_dict[ruler2].aspect in {'刑'}:
        msg = '【5r刑2r】有可能因为桃花破财' if is_debug else '有可能因为桃花破财'
        tmp_vec.append(msg)
    if ruler8 in star_dict[ruler_5].aspect_dict and star_dict[ruler_5].aspect_dict[ruler8].aspect in {'刑'}:
        msg = '【5r刑8r】容易因为桃花破财' if is_debug else '容易因为桃花破财'
        tmp_vec.append(msg)

    # logger.debug('!66666666666666666666666666666666')
    '''
    3. 相位——宫性
    5-7关系最好和谐的，不和谐的最好相亲，因为恋爱久了结不了婚
    5-11 对冲，会出现恋爱出轨/劈腿，俗称熟人挖墙脚。影响 papapa 和或者堕胎/生育困难
    '''
    ruler11 = house_dict[11].ruler
    if ruler11 in star_dict[ruler_5].aspect_dict and star_dict[ruler_5].aspect_dict[ruler11].aspect == '冲':
        reason_tmp = '【5r冲11r】' if is_debug else ''
        tmp_vec.append(f'{reason_tmp}可能会出现恋爱出轨/劈腿，俗称熟人挖墙脚。影响 papapa 和或者堕胎/生育困难.')

    ruler7 = house_dict[7].ruler
    if ruler7 in star_dict[ruler_5].aspect_dict and star_dict[ruler_5].aspect_dict[ruler7].aspect in {'冲','刑'}:
        reason_tmp = '【5r刑冲7r】' if is_debug else ''
        tmp_vec.append(f'{reason_tmp}因为恋爱久了可能结不了婚，可以选择相亲.')
    '''
    4、相位二星性
    金火产生相位都很容易恋爱，吉有不错的愉悦感受。
    金月颤抖，男：婆媳关系混乱。女：不够温柔等
    '''

    web.ctx.env['trace_info']['恋爱']['恋爱深层解析'] = tmp_vec


def parse_marrage_2():
    is_debug = web.ctx.env['is_debug']
    star_dict = web.ctx.env["star_dict"]
    house_dict = web.ctx.env["house_dict"]

    # 婚神星落宫
    love_star_house = star_dict['婚神'].house
    key = f'婚神{love_star_house}宫'

    knowledge_dict = web.ctx.env['knowledge_dict']
    desc = knowledge_dict['婚神星落宫'][key]
    # logger.debug(desc)

    reason = f'【{key}】' if is_debug else ''
    set_trace_info('婚姻', '整体', [f'{reason}{desc}'])
    # web.ctx.env[]['婚姻']['婚神星表现'] = [f'{reason}{desc}']


def set_trace_info(key, sub_key, msg_vec):
    if key not in web.ctx.env['trace_info']:
        logger.error(f'{key} not in web.ctx.env.trace_info...')

    if key in web.ctx.env['trace_info'] and sub_key in web.ctx.env['trace_info'][key]:
        web.ctx.env['trace_info'][key][sub_key].extend(msg_vec)
        return

    web.ctx.env['trace_info'][key][sub_key] = msg_vec


def _get_basic_soup_from_http(customer_name, content) -> Tuple[str, BeautifulSoup, BeautifulSoup]:
    logger.debug('---------------invoke get_basic_soup_from_http ---------------------')
    error_msg, birthday, dist, is_dst, toffset, location = _prepare_http_data(content=content, name=customer_name)

    """ ixingpan Http Result. """
    if error_msg != '':
        return error_msg, None, None

    soup_ixingpan = _fetch_ixingpan_soup(name=customer_name, dist=dist, birthday_time=birthday, dst=is_dst, female=1)
    logger.debug('成功通过HTTP获取「爱星盘」排盘信息...')

    # Update 宫神星要用到的:glon_deg, glat_deg. 取自ixingpan结果中的
    err_no, glon_deg, glat_deg = _parse_glon_glat(soup=soup_ixingpan)
    if err_no != '':
        return err_no, None, None

    """ almuten Http Result. """
    post_data = _build_almuten_http_data(name=customer_name, birthinfo=birthday, loc=location, glon_deg=glon_deg, glat_deg=glat_deg, toffset=toffset, is_dst=is_dst)
    soup_almuten = _fetch_almuten_soup(post_data)
    logger.debug(f'成功通过HTTP获取「宫神星」排盘信息')

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
    is_dst = 0
    toffset = 'GMT_ADD_8'

    return error_msg, birthday, dist, is_dst, toffset, f'{province}{city}{area}'


def generate_random_string():
    import random, string
    length = random.randint(3, 9)  # 随机生成长度在4到8之间的整数
    characters = string.ascii_lowercase + string.digits  # 包含小写字母和数字的字符集
    return ''.join(random.choice(characters) for _ in range(length))


def _fetch_ixingpan_soup(name, female=1, dist='1550', birthday_time='1962-08-08 20:00', dst='0'):
    # dst: Daylight Saving Time
    birthday = birthday_time.split(' ')[0]
    birth_time = birthday_time.split(' ')[1]

    new_name = generate_random_string()
    url = f"https://xp.ixingpan.com/xp.php?type=natal&name={new_name}&sex={female}&dist={dist}&date={birthday}&time={birth_time}&dst={dst}&hsys=P"
    logger.debug(f'爱星盘请求串 {url}')

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
    new_name = generate_random_string()
    data['name'] = new_name

    birthday = birthinfo.split(' ')[0]

    data['month'] = str(int(birthday.split('-')[1]))
    data['day'] = str(int(birthday.split('-')[2]))
    data['year'] = birthday.split('-')[0]

    brith_time = birthinfo.split(' ')[-1]
    data['hour'] = str(int(brith_time.split(':')[0]))

    if is_dst:
        logger.debug('@@@@@@@@@@@@@@@@@@@@@@@')
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

        logger.debug(f'+++++++++++{star}\t{house}')

        star_obj = Star(star=star, house=house, score=score, lord_house_vec=lord_house_vec)

        if star in ['上升', '中天']:
            continue

        web.ctx.env['star_dict'][star] = star_obj

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

        # 互溶接纳、接纳只保留互溶接纳
        if star_b in web.ctx.env['star_dict'][star_a].recepted_dict and \
                web.ctx.env['star_dict'][star_a].recepted_dict[star_b].action_name == '接纳' and feature == '互容接纳':
            web.ctx.env['star_dict'][star_a].recepted_dict[star_b] = r
        elif star_b not in web.ctx.env['star_dict'][star_a].recepted_dict:
            web.ctx.env['star_dict'][star_a].recepted_dict[star_b] = r

    # Parse almuten house
    # Fill house_dict
    for star_name, star_obj in web.ctx.env['star_dict'].items():
        # 宫主星啥，几飞几，宫内星哪些
        if star_name not in ['天王', '海王', '冥王', '北交']:
            for house in star_obj.lord_house_vec:
                house_obj = House(house_num=house, ruler=star_name, ruler_loc=star_obj.house)
                web.ctx.env['house_dict'][house] = house_obj

    for star_name, star_obj in web.ctx.env['star_dict'].items():
        house = star_obj.house
        web.ctx.env['house_dict'][house].loc_star.append(star_name)


pattern_constellation = re.compile(r'\([^)]*\)')
pattern_house = re.compile(r'\d+')
def _parse_ixingpan_star(soup):
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

        logger.debug(f'--------->{star}\t{house}')

        constellation = pattern_constellation.sub('', constellation).strip()

        match = pattern_house.search(house)

        if match:
            house = int(match.group())
        else:
            house = -1

        # 重新填充 star_dict
        if star in web.ctx.env['star_dict']:
            web.ctx.env['star_dict'][star].constellation = constellation

            if house != web.ctx.env['star_dict'][star].house:
                pass
                # print(f'{star} {star_dict[star].house} {house}')
        else:
            r = Star(star=star, house=house)
            r.constellation = constellation
            web.ctx.env['star_dict'][star] = r


def _parse_ixingpan_house(soup):
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
        if house in web.ctx.env['star_dict']:
            web.ctx.env['house_dict'][house].constellation = constellation


def _parse_ixingpan_aspect(soup):
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

        aspect = aspect if aspect != '拱' else '三合'

        aspect_obj = Aspect(star_b=star_b, aspect=aspect)
        # star_dict[star_a].aspect_vec_old.append(aspect_obj)
        web.ctx.env['star_dict'][star_a].aspect_dict[star_b] = aspect_obj

        # 反过来填充
        aspect_obj_reverse = Aspect(star_b=star_a, aspect=aspect)
        web.ctx.env['star_dict'][star_b].aspect_dict[star_a] = aspect_obj_reverse


def get_square():
    '''
    灾星系统
        第一档（被一个克到就有明显事件）：8宫主 ≥ 命主星(上升点也算) > 12宫主
        第二档（被两个克到才有明显事件）：土星 = 海王 = 冥王 = 天王
        第三档（辅助参考）：火星 = 凯龙

    受克程度：0° > 90 > 180
    宫主星与灾星受克：
        1. 与灾星0、90、180
        2. 与除灾星外的宫主星形成：0、90、180
        3. 与四轴成0度，等同于
    :return: 几宫主被一档灾星8宫主（火星）克
    '''

    # Step 1. 获取三挡灾星
    ruler_1 = web.ctx.env['house_dict'][1].ruler
    ruler_8 = web.ctx.env['house_dict'][8].ruler
    ruler_12 = web.ctx.env['house_dict'][12].ruler

    trace_square_vec = [f'背景信息:\n\t第一档灾星: 8r ≥ 1r ＞ 12r\n\t第二档灾星: 土星 = 海王 = 冥王 = 天王\n\t第三档灾星: 土星 = 凯龙', f'盘主: 8r=「{ruler_8}」, 1r=「{ruler_1}」，12r=「{ruler_12}」']
    # print(f'\n\n第一档灾星(被一个克到就有明显事件)：1宫主「{ruler_1}」，8宫主「{ruler_8}」，12宫主「{ruler_12}」')

    sorted_dict = dict(sorted(web.ctx.env['house_dict'].items(), key=lambda x: x[0]))

    total_square_vec = []

    for house_id, obj in sorted_dict.items():
        ruler = obj.ruler  # 宫主星
        house_msg_vec = [f'{house_id}r={ruler}']

        # 宫主星==灾星
        if ruler == ruler_8:
            house_msg_vec.append(f'与8r同星(一档灾星)')
        elif ruler == ruler_12:
            house_msg_vec.append(f'与12r同星(一档灾星)')

        # 解析宫主星受克情况
        aspect_vec = list(web.ctx.env['star_dict'][ruler].aspect_dict.values())

        for aspect_obj in aspect_vec:
            star_b = aspect_obj.star_b
            aspect_info = aspect_obj.aspect

            if aspect_info in {'三合', '六合'}:
                continue

            if star_b not in web.ctx.env['star_dict']:
                continue

            square_msg = ''
            if star_b == ruler_8:
                square_msg = f'被8r({star_b})克({aspect_info}, 一档灾星)'
            elif star_b == ruler_1:
                square_msg = f'被1r（{star_b}）克({aspect_info}, 一档灾星)'
            elif star_b == ruler_12:
                square_msg = f'被12r（{star_b}）克({aspect_info}, 一档灾星)'
            elif star_b in {'土星', '海王', '冥王', '天王'}:
                square_msg = f'被{star_b}克({aspect_info}, 二档灾星)'
            elif star_b in {'火星'}:
                square_msg = f'被{star_b} 克({aspect_info}, 三档灾星)'

            if square_msg and square_msg not in house_msg_vec:
                house_msg_vec.append(square_msg)

        total_square_vec.append(house_msg_vec)

    for msg_vec in total_square_vec:
        if len(msg_vec) == 1:
            continue

        trace_square_vec.append(', '.join(msg_vec))
        # print(', '.join(msg_vec))

    web.ctx.env['trace_info']['灾星系统']['盘主灾星信息'] = trace_square_vec

# ------------------------ Dump 数据 ---------------------
def dump_obj(obj, filepath):
    with open(filepath, 'wb') as file:
        pickle.dump(obj, file)

    logger.debug(f'成功Dump文件, {filepath}')


# ------------------------- 生成返回结果 ---------------------
def build_result(domain=DomainAsc):
    trace_dict = get_session(SESSION_KEY_TRACE)
    if domain not in trace_dict:
        logger.warning(f'解析失败！trace_dict 不存在 key:{domain}')
        set_session(ERROR, COMMON_ERR_MSG)
        return

    report = []
    report.append(f'『解析{domain}』')
    field_dict = trace_dict[domain]

    idx = -1
    no_vec = ['一', '二', '三', '四', '五', '六', '七', '八']
    for biz, sub_vec in field_dict.items():
        idx += 1

        if len(sub_vec) > 1:
            sub_vec_with_numbers = [f"{i + 1}、{item}" for i, item in enumerate(sub_vec)]
        else:
            sub_vec_with_numbers = [f"{item}" for i, item in enumerate(sub_vec)]

        msg = '\n'.join(sub_vec_with_numbers)
        report.append(f'\n{no_vec[idx]}、{biz}: {msg}')

    msg1 = '\n'.join(report)
    msg2 = get_more_result()
    ret = f'{msg1}\n{msg2}'

    return ret


index_dict = {'❶': DomainAsc, '❷': DomainLove, '❸': DomainMarriage, '❹': DomainStudy,
              '❺': DomainWork, '❻': DomainHealth, '❼': DomainMoney}

index_dict_inner = {'1': DomainAsc, '2': DomainLove, '3': DomainMarriage, '4': DomainStudy,
              '5': DomainWork, '6': DomainHealth, '7': DomainMoney}


'''
❶ YouTube/Netflix双语翻译（支持DeepL）
❷ 智能分句，多视图查看字幕内容
❸ 沉浸式网页翻译
❹ 智能语法与单词分析
❺ 将视频转换为练习材料，同时练习听力、口语、拼写等
❻ 自动高亮任何已经学习过的单词
❼ 在学习中心统一管理学过的视频、单词与例句
❽ 与智能语音助手对话学习外语
❾ 支持iPad，iPhone，Android等PWA程序
'''

def get_more_result():
    msg = '\n\n更多解析请回复：\n'
    index_str = '\n'.join([f" {key}  {value}" for key, value in index_dict.items()])
    return ''.join([msg, index_str])


# --------------------------- get set session 变量-----------------
def get_session(key):
    if key not in web.ctx.env:
        logger.warning(f'get_sess error, key:{key} not exists...')
        return None

    return web.ctx.env[key]


def set_session(key, val):
    web.ctx.env[key] = val

# ----------------------------- 各种 init -------------------------
def init_session():
    """
    加载文件、初始化context字典
    session变量：
        文件名：
        是否cache
        用户dist、brithday等信息
    """
    init_knowledge_dict()
    logger.debug('成功加载字典文件...')

    init_trace()
    logger.debug('成功初始化trace变量...')

    """ Init birthday, dist, location(province, city, area) """
    init_user_attri()
    if get_session(ERROR) != '':
        return
    logger.debug('成功解析用户消息中的生日等属性信息...')

    """ Init 文件名 & 检测缓存文件 """
    init_check_cache()
    logger.debug('成功初始化缓存文件名、缓存是否存在变量...')


def init_knowledge_dict():
    knowledge_dict: Dict[str, Dict[str, str]] = {}

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

    _load_knowledge_file()
    set_session(SESS_KEY_KNOWLEDGE, knowledge_dict)


def init_trace():
    if SESS_KEY_STAR not in web.ctx.env:
        star_dict: Dict[str, Star] = {}
        set_session(SESS_KEY_STAR, star_dict)

    if SESS_KEY_HOUSE not in web.ctx.env:
        house_dict: Dict[int, House] = {}
        set_session(SESS_KEY_HOUSE, house_dict)

    all_trace_dict: Dict[str, Dict[str, List[str]]] = {}

    disaster_trace_dict: Dict[str, List[str]] = {}
    love_trace_dict: Dict[str, List[str]] = {}
    marriage_trace_dict: Dict[str, List[str]] = {}
    work_trace_dict: Dict[str, List[str]] = {}
    asc_trace_dict: Dict[str, List[str]] = {}
    study_trace_dict: Dict[str, List[str]] = {}

    all_trace_dict['灾星系统'] = disaster_trace_dict
    all_trace_dict[DomainLove] = love_trace_dict
    all_trace_dict[DomainMarriage] = marriage_trace_dict
    all_trace_dict[DomainWork] = work_trace_dict
    all_trace_dict[DomainAsc] = asc_trace_dict
    all_trace_dict[DomainStudy] = study_trace_dict

    # web.ctx.env['trace_info'] = all_trace_dict
    set_session(SESSION_KEY_TRACE, all_trace_dict)

    web.ctx.env['is_debug'] = False

    wealth_trace_dict: Dict[str, List[str]] = {}
    health_trace_dict: Dict[str, List[str]] = {}
    nature_trace_dict: Dict[str, List[str]] = {}


def init_user_attri():
    content = get_session(CONTENT)
    if content in NUM_WHITELIST:
        set_session(IS_INPUT_NUM, True)

        trans_content = index_dict_inner[content]
        set_session(TargetDomain, trans_content)

        # 设置 BIRTHDAY_KEY2, DIST_KEY
        filename = f'./cache/basic/{get_session(FROMUSER)}/request.log'
        last_line = None
        if os.path.exists(filename):
            with open(filename, 'r') as file:
                for line in file:
                    last_line = line

            vec = last_line.split('\t')
            birth = vec[0]
            dist = vec[1]

            set_session(BIRTHDAY_KEY2, birth)
            set_session(DIST_KEY, dist)

    else:
        set_session(IS_INPUT_NUM, False)
        err, birthday, dist, is_dst, toffset, location = _prepare_http_data(content=get_session(CONTENT), name=get_session(FROMUSER))
        if err != '':
            set_session(ERROR, '【排盘失败】\n, 请重新输入...')
            return

        set_session(BIRTHDAY_KEY, birthday)
        set_session(DIST_KEY, dist)
        set_session(IS_DST_KEY, is_dst)
        set_session(TOFFSET_KEY, toffset)
        set_session(LOCATION_KEY, location)

        birthday_concat = birthday.replace(" ", "").replace(":", "").replace("-", "")
        set_session(BIRTHDAY_KEY2, birthday_concat)


def init_check_cache():
    filename_report, filename_req, filename_soup1, filename_soup2 = None, None, None, None
    content, from_user = get_session(CONTENT), get_session(FROMUSER)

    folder_path = f'./cache/basic/{from_user}'
    set_session(FOLDERPATH, folder_path)
    os.makedirs(get_session(FOLDERPATH), exist_ok=True)

    filename_req = f'{folder_path}/request.log'
    filename_report = f'{folder_path}/report_{from_user}_{get_session(BIRTHDAY_KEY2)}_{get_session(DIST_KEY)}.pkl'
    filename_soup1 = f'{folder_path}/soup_{from_user}_{get_session(BIRTHDAY_KEY2)}_{get_session(DIST_KEY)}_almuten.pickle'
    filename_soup2 = f'{folder_path}/soup_{from_user}_{get_session(BIRTHDAY_KEY2)}_{get_session(DIST_KEY)}_ixingpan.pickle'

    set_session(FILENAME_REQ, filename_req)
    set_session(FILENAME_REPORT, filename_report)
    set_session(FILENAME_SOUP1, filename_soup1)
    set_session(FILENAME_SOUP2, filename_soup2)

    # check 文件存在否
    a = [HAS_REQ_FILE, HAS_REPORT_FILE, HAS_SOUP1_FILE, HAS_SOUP2_FILE]
    b = [filename_req, filename_report, filename_soup1, filename_soup2]
    for k, v in zip(a, b):
        b = True if os.path.exists(v) else False
        set_session(k, b)

    if get_session(HAS_REPORT_FILE):
        with open(get_session(FILENAME_REPORT), 'rb') as file:
            all_trace_dict = pickle.load(file)

            set_session(SESSION_KEY_TRACE, all_trace_dict)
            logger.debug(f'成功从[{get_session(FILENAME_REPORT)}] 加载 all_trace_dict')


    # Append birthday_key2, dist to request.log
    with open(filename_req, "w") as file:
        file.write(f"{get_session(BIRTHDAY_KEY2)}\t{get_session(DIST_KEY)}")
    logger.debug(f'成功写文件, [{filename_req}]...')


