
# -*- coding: utf-8 -*-
from typing import Dict, List, Tuple
import web
import json
import os
import requests
import re
from bs4 import BeautifulSoup
import configparser
import cpca

import logging
import pickle
from Const import *
from common import _get_basic_soup_from_http, set_session, get_session, dump_obj, _parse_ixingpan_house, _parse_ixingpan_star, _parse_ixingpan_aspect
from common import is_received_or_mutal, set_session_afflict
# import common

# 创建日志记录器
logger = logging.getLogger('llm.py')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

logger.setLevel(logging.DEBUG)

LOC_MODE = 'loc'
FLY_MODE = 'fly'
REC_MODE = 'rec'


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

    dump_obj(soup_ixingpan, get_session(FILENAME_SOUP2))

    # 解析爱星盘结果
    _parse_ixingpan_house(soup_ixingpan)
    _parse_ixingpan_star(soup_ixingpan)
    _parse_ixingpan_aspect(soup_ixingpan)

    # 互溶接纳
    is_received_or_mutal()

    # 设置受克信息
    set_session_afflict()

    if True:
        logger.debug('\n------------------- Debug 宫位信息 --------------------')
        house_dict_tmp = get_session(SESS_KEY_HOUSE)
        for id, house_obj in house_dict_tmp.items():
            logger.debug(f'{id}宫\t宫主星:{house_obj.ruler}\t宫内星: {house_obj.loc_star}')

        logger.debug('\n---------------------Debug 行星信息--------------------')
        star_dict_tmp = get_session(SESS_KEY_STAR)
        for name, star_obj in star_dict_tmp.items():
            # logger.debug(f'{name}, {star_obj.house}宫')
            const = star_obj.constellation
            degree = star_obj.degree
            house = star_obj.house
            score = star_obj.score
            is_domicile = star_obj.is_domicile
            is_exaltation = star_obj.is_exaltation
            is_triplicity = star_obj.is_triplicity
            is_term = star_obj.is_term
            is_face = star_obj.is_face

            rec_vec = []
            for k, obj in star_obj.recepted_dict.items():
                msg = f'与「{obj.star_b}」互容'

                if obj.action_name == '接纳':
                    msg = f'被「{obj.star_b}」接纳'

                rec_vec.append(msg)

            rec_msg2 = ''
            if len(rec_vec) != 0:
                rec_msg = ';'.join(rec_vec)
                rec_msg2 = f'接纳信息: {rec_msg}'


            # logger.debug(f'-->{name} 落{house}宫 {const}座 {degree}° 分:{score} 庙:{is_domicile} 旺:{is_exaltation} 三:{is_triplicity} 界:{is_term} 十:{is_face}')
            logger.debug(f'-->{name}\t落{house}宫\t{const}座\t{degree}°\t得分:{score}\t受克:{star_obj.is_afflicted}\t守护宫:{star_obj.lord_house_vec}\t{rec_msg2}')

        logger.debug('\n------------------- Debug 星座信息 --------------------')
        dict_tmp = get_session(SESS_KEY_CONST)
        for const_name, obj in dict_tmp.items():
            if len(obj.star_vec) == 0:
                continue
            logger.debug(f'{const_name}座\t星体:{" ".join(obj.star_vec)}')

        logger.debug('\n------------------- Debug 受克信息 --------------------')
        dict_tmp = get_session(SESS_KEY_AFFLICT)
        for star, obj in dict_tmp.items():
            logger.debug(f'星体:{star}\t一档受克:{" ".join(obj.level_1)}\t二挡受克:{" ".join(obj.level_2)}')

    solar_moon_const = get_solar_moon_const()
    asc_const, asc_solar_const = get_asc_const()
    context_solar_moon_asc = [asc_const, solar_moon_const, asc_solar_const]

    star_loc_vec, ruler_loc_vec, rec_vec, final_key_vec = get_llm_recall_keys()

    guest_vec = get_guest_info(rec_vec)
    logger.debug(';'.join(guest_vec))

    llm_knowledge_dict = get_session(SESS_KEY_LLM_KNOWLEDGE)

    context = []

    for key in final_key_vec:
        for section, sub_dict in llm_knowledge_dict.items():
            if key in sub_dict:
                msg = f'{key}={sub_dict[key]}'
                context.append(msg)
            else:
                # logger.debug(f'key:{key} not found...')
                pass
    
    context = list(set(context))
    logger.debug('')
    logger.debug('\n'.join(context))

    logger.debug('\n\n\n')
    get_llm_input(context_solar_moon_asc, '帮我占星下')
    # parse_asc_star()
    # parse_love()
    # parse_marrage_2()
    # parse_marrage()
    # parse_work_new()
    # parse_work()
    # parse_study()

    # parse_wealth()
    # dump_obj(get_session(SESSION_KEY_TRACE), get_session(FILENAME_REPORT))
    # return error_msg, soup_ixingpan, soup_almuten
    # get_house_energy()


def get_llm_input(recall_vec, question):
    # inp_old = ""
    #     Use the following pieces of context to answer the user's question. 
    #     If you don't know the answer, just say that you don't know, don't try to make up an answer. 星体得分>1会表现为正面，<-1为负面
    #     Context: {context} 
    #     Question: {question} 
    #     Always say "thanks for asking!" at the end of the answer. 
    # """

    context = get_context_by_key(recall_vec)
    
    inp = """你现在是一名占星师，请使用下面的上下文回答用户问题，如果你不知道答案，就回答不知道，不要试图美化回答。
        注意星体得分>1会更多表现旺的一面，<-1更多表现衰的一面
        上下文:{}
        问题:{}
        Always say "thanks for asking!" at the end of the answer. 
        """.format(context, question)

    logger.debug(inp)


def get_context_by_key(recall_vec):
    llm_knowledge_dict = get_session(SESS_KEY_LLM_KNOWLEDGE)
    context = []

    for key in recall_vec:
        for section, sub_dict in llm_knowledge_dict.items():
            if key in sub_dict:
                msg = f'{key}={sub_dict[key]}'
                context.append(msg)
            else:
                # logger.debug(f'key:{key} not found...')
                pass
    
    context = list(set(context))

    return '\n'.join(context)


def get_guest_info(rec_vec):
    star_dict = get_session(SESS_KEY_STAR)
    star_loc_vec = []

    for star_name, star_obj in star_dict.items():
        if star_name in {'北交', '上升', '中天', '下降', '天底'}:
            continue

        degree = star_obj.degree
        house = star_obj.house
        score = star_obj.score
        is_afflicted = ',受克' if star_obj.is_afflicted else ''
        lord_house_vec = star_obj.lord_house_vec

        msg_lord = '、'.join([str(item) for item in lord_house_vec])
        final_msg_lord = f'是{msg_lord}宫的宫主星,' if msg_lord != '' else ''

        msg_score = f'，星体得分:{score}' if star_name in seven_star_list else ''

        # 互溶接纳
        msg_rec = '、'.join(rec_vec) if len(rec_vec) != 0 else ''
        final_rec = f',接纳信息:{msg_rec}' if msg_rec != '' else ''

        
        msg = f'{star_name}{final_msg_lord}落在{house}宫{msg_score}{is_afflicted}'

        star_loc_vec.append(msg)

    return star_loc_vec


def get_llm_recall_keys():
    star_dict = get_session(SESS_KEY_STAR)
    house_dict = get_session(SESS_KEY_HOUSE)
    constellation_dict = get_session(SESS_KEY_CONST)

    # llm 召回的key
    star_loc_vec = get_star_loc_house()  # 星体落宫: ['太阳落1宫', '月亮落2宫', '冥王落12宫', '凯龙落9宫', '婚神落7宫', '福点落11宫']
    ruler_loc_vec = get_ruler_loc_house()  # 宫主星落宫: ['9R落1宫', '5R落8宫','1R落10宫', '命主星落10宫', '4R落10宫', '2R落2宫', '3R落2宫']
    rec_vec = get_ruler_rec()  # 宫主星接纳: ['8R被2R接纳', '8R被3R接纳', '7R被1R接纳', '7R被4R接纳']
    logger.debug(star_loc_vec)
    logger.debug(ruler_loc_vec)
    logger.debug(rec_vec)

    final_key_vec = []
    final_key_vec.extend(star_loc_vec)
    final_key_vec.extend(ruler_loc_vec)
    final_key_vec.extend(rec_vec)
    final_key_vec = list(set(final_key_vec))

    return star_loc_vec, ruler_loc_vec, rec_vec, final_key_vec



def get_star_loc_house() -> List[str]:
    star_dict = get_session(SESS_KEY_STAR)
    house_dict = get_session(SESS_KEY_HOUSE)
    star_loc_vec = []

    for star_name, star_obj in star_dict.items():
        if star_name in {'北交', '上升', '中天', '下降', '天底'}:
            continue

        degree = star_obj.degree
        house = star_obj.house
        score = star_obj.score
        is_afflicted = '严重受克' if star_obj.is_afflicted else ''
        constellation = star_obj.constellation
        lord_house_vec = star_obj.lord_house_vec

        # 搞落宫
        star_loc_vec.append(get_key(star_name, house, mode=LOC_MODE))

    return star_loc_vec


def get_ruler_loc_house() -> List[str]:
    star_dict = get_session(SESS_KEY_STAR)
    house_dict = get_session(SESS_KEY_HOUSE)
    ruler_loc_vec = []

    # 搞飞宫
    for star_name, star_obj in star_dict.items():
        if star_name in {'北交', '上升', '中天', '下降', '天底'}:
            continue

        degree = star_obj.degree
        house = star_obj.house
        score = star_obj.score
        is_afflicted = '严重受克' if star_obj.is_afflicted else ''
        constellation = star_obj.constellation
        lord_house_vec = star_obj.lord_house_vec

        if star_name in seven_star_list:
            for lord_house in lord_house_vec:
                ruler_loc_vec.append(get_key(lord_house, house, mode=FLY_MODE))

                if lord_house == 1:
                    ruler_loc_vec.append(f'命主星落{house}宫')

    return ruler_loc_vec


def get_ruler_rec() -> List[str]:
    star_dict = get_session(SESS_KEY_STAR)
    house_dict = get_session(SESS_KEY_HOUSE)
    rec_vec = []

    for star_name, star_obj in star_dict.items():
        if star_name not in seven_star_list:
            # logger.debug(f'{star_name} continue....')
            continue

        degree = star_obj.degree
        house = star_obj.house
        score = star_obj.score
        is_afflicted = '严重受克' if star_obj.is_afflicted else ''
        constellation = star_obj.constellation
        lord_house_vec = star_obj.lord_house_vec

        # 互容接纳
        # logger.debug(f'recepted_dict size is:{len(star_obj.recepted_dict)}')
        for k, obj in star_obj.recepted_dict.items():
            star_b = obj.star_b

            if star_b in star_dict:
                lord_vec_b = star_dict[star_b].lord_house_vec

                for lord_a in lord_house_vec:
                    for lord_b in lord_vec_b:
                        # logger.debug(f'obj.action_name is:{obj.action_name}')
                        if obj.action_name == '接纳':
                            msg = get_key(lord_a, lord_b, mode=REC_MODE)
                            rec_vec.append(msg)

    return rec_vec


def get_solar_moon_const() -> str:
    star_dict = get_session(SESS_KEY_STAR)
    house_dict = get_session(SESS_KEY_HOUSE)
    rec_vec = []

    solar = ''
    moon = ''
    for star_name, star_obj in star_dict.items():
        if star_name not in {'太阳', '月亮'}:
            # logger.debug(f'{star_name} continue....')
            continue

        degree = star_obj.degree
        house = star_obj.house
        score = star_obj.score
        is_afflicted = '严重受克' if star_obj.is_afflicted else ''
        constellation = star_obj.constellation

        if star_name == '太阳':
            solar = constellation
        elif star_name == '月亮':
            moon = constellation
    
    return f'太阳{solar}月亮{moon}'



def get_asc_const() -> Tuple[str, str]:
    star_dict = get_session(SESS_KEY_STAR)
    house_dict = get_session(SESS_KEY_HOUSE)
    rec_vec = []

    solar = ''
    asc = ''
    for star_name, star_obj in star_dict.items():
        if star_name not in {'太阳', '上升'}:
            continue

        degree = star_obj.degree
        house = star_obj.house
        score = star_obj.score
        is_afflicted = '严重受克' if star_obj.is_afflicted else ''
        constellation = star_obj.constellation

        if star_name == '太阳':
            solar = constellation
        elif star_name == '上升':
            asc = constellation
    
    return f'上升{asc}', f'上升{asc}太阳{solar}'


def get_star_loc_ruler() -> List[str]:
    pass


def get_key(a, b, mode='loc'):
    if mode == LOC_MODE:
        return star_loc_pattern.format(a, b)
    elif mode == FLY_MODE:
        return ruler_loc_pattern.format(a, b)
    elif mode == REC_MODE:
        return recepted_pattern.format(a, b)
    # star_loc_pattern = '{}落{}宫'
    # ruler_loc_pattern = '{}R落{}宫'
    # recepted_pattern = '{}R被{}R接纳'