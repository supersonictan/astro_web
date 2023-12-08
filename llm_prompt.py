
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


# 创建日志记录器
logger = logging.getLogger('common.py')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


logger.setLevel(logging.DEBUG)


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

    parse_asc_star()
    parse_love()
    parse_marrage_2()
    parse_marrage()
    parse_work_new()
    parse_work()
    parse_study()

    parse_wealth()
    dump_obj(get_session(SESSION_KEY_TRACE), get_session(FILENAME_REPORT))
    # return error_msg, soup_ixingpan, soup_almuten
    # get_house_energy()

