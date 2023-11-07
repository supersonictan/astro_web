# -*- coding: utf-8 -*-
import configparser

import web
import sys
from typing import Dict, List
import os
import pickle

sys.path.append('/root/code/astro_web')

import common
from common import get_session, set_session
from common import FROMUSER, TOUSER, CONTENT, FOLDERPATH, FILE_REPORT, FILE_REQ, FILE_SOUP1, FILE_SOUP2, DIST
import logging
import reply
import receive

logger = logging.getLogger('run_web_bak.py')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

logger.setLevel(logging.DEBUG)


DEBUG_BLACK_SET = {'ACTUAL_SERVER_PROTOCOL', 'PATH_INFO', 'QUERY_STRING', 'REMOTE_ADDR', 'REMOTE_PORT', 'REQUEST_METHOD', 'REQUEST_URI', 'SCRIPT_NAME', 'SERVER_NAME', 'SERVER_PROTOCOL', 'SERVER_SOFTWARE', 'wsgi.errors', 'wsgi.input', 'wsgi.input_terminated', 'wsgi.multiprocess', 'wsgi.multithread', 'wsgi.run_once', 'wsgi.url_scheme', 'wsgi.version', 'SERVER_PORT', 'HTTP_USER_AGENT', 'HTTP_ACCEPT', 'HTTP_HOST', 'HTTP_PRAGMA', 'CONTENT_TYPE', 'CONTENT_LENGTH'}




"""
    1、第一轮对话
        - 先check缓存是否有结果对象的pkl，命中缓存则返回
        - 未命中缓存，走排盘http请求，并将：①http得到的BeautifulSoup、②解盘结果、③用户本次请求的location + birthday写文件
    2、非第一轮对话
        - 加载本地结果对象的pkl，并返回对应结果
            需要获取之前用户输入的location + birthday
"""

class Handle():
    def POST(self):
        try:
            webData = web.data()
            logger.debug(f"Handle Post webdata is {webData}")

            recMsg, from_user, to_user, content = parse_request_data(webData=webData)
            if not (isinstance(recMsg, receive.Msg) and recMsg != 'text'):
                logger.fatal('暂不处理')
                return 'success'

            # 加载文件、初始化存结果的dict
            init_context()

            """ 获取缓存文件名 """
            err = get_cache_filename()
            if err != '':
                replyMsg = reply.TextMsg(from_user, to_user, f'【排盘失败】\n{err}, 请重新检查输入...')
                return replyMsg.send()

            """ Round 1. 第一轮对话，先check缓存 """
            if content not in NUM_WHITELIST:
                report = get_and_dump_report(filename=get_session(FILE_REPORT), load_key='', is_load=True)
                if report is not None:
                    logger.debug(f'第一轮对话，命中缓存！openid:{from_user}, 文本:{content}...')
                    ret = append_msg(report)
                    replyMsg = reply.TextMsg(from_user, to_user, ret)
                    return replyMsg.send()

                """ 未命中缓存..."""
                logger.debug('第一轮对话，未命中缓存, 开始执行请求 HTTP 逻辑...')
                err, soup_ixingpan, soup_almuten = common.basic_analyse(customer_name=from_user, content=content)
                if err != '':
                    replyMsg = reply.TextMsg(from_user, to_user, f'【排盘失败】\n{err}, 请重新检查输入...')
                    return replyMsg.send()

                logger.debug('成功通过HTTP请求排盘, 并解盘! ')

                logger.debug('准备将report文件写入缓存...')
                report = get_and_dump_report(from_user=from_user, file_name=filename_report, load_key='', is_load=False)

                # 写如soup、profile
                reply_str = append_msg(report)






            err, birthday, dist, is_dst, toffset, location = common._prepare_http_data(content=content, name=from_user)
            if err != '':
                replyMsg = reply.TextMsg(from_user, to_user, f'【排盘失败】\n{err}, 请重新检查输入...')
                return replyMsg.send()


            birthday_concat = birthday.replace(" ", "").replace(":", "").replace("-", "")
            dump_filename = f'{folder_path}/report_{from_user}_{birthday_concat}_{dist}.pkl'

            # 非第一轮对话：读pkl，并返回对应结果
            if content in {'1', '2', '3', '4', '5', '6', '7'}:
                report = get_and_dump_report(dump_filename, load_key=content)

                if report is None:
                    replyMsg = reply.TextMsg(from_user, to_user, f'【排盘失败】\n, 请重新检查输入...')
                    return replyMsg.send()

                replyMsg = reply.TextMsg(from_user, to_user, report)
                return replyMsg.send()


            replyMsg = reply.TextMsg(from_user, to_user, reply_str)

            return replyMsg.send()

        except Exception as Argument:
            logger.error(Argument)
            return Argument


index_dict = {'1': '别人眼中自己', '2': '恋爱', '3': '婚姻', '4': '学业', '5': '事业', '6': '财富'}


def parse_request_data(webData):
    recMsg = receive.parse_xml(webData)
    toUser = recMsg.ToUserName
    fromUser = recMsg.FromUserName

    content = recMsg.Content
    content = content.decode('utf-8')

    set_session(TOUSER, toUser)
    set_session(FROMUSER, fromUser)
    set_session(CONTENT, content)

    logger.debug(f'----------> FromUser:{get_session(FROMUSER)} ToUser:{get_session(TOUSER)} Content:{get_session(CONTENT)}')

    return recMsg, fromUser, toUser, content


def get_cache_filename():
    """
    文件名规则：
        1、报告文件
            report_{from_user}_{birthtime}_{dist}.pkl, eg: report_oNs7B6jSxAAWiFbnc1TgesXo1BHc_202310231525_1550.pkl
        2、历史请求日志
            req_{from_user}.log, 每次请求后append信息
        3、http抓结果的 BeautifulSoup 的 pickle 文件
            soup_{from_user}_{birthtime}_{dist}_almuten.pickle
            soup_{from_user}_{birthtime}_{dist}_ixingpan.pickle

    :param from_user:
    :param to_user:
    :param content:
    :return:
    """
    filename_report, filename_req, filename_soup1, filename_soup2 = None, None, None, None
    content, from_user = get_session(CONTENT), get_session(FROMUSER)

    folder_path = f'./cache/basic/{from_user}'
    set_session(FOLDERPATH, folder_path)

    # 第2+轮对话
    if content not in NUM_WHITELIST:
        err, birthday, dist, is_dst, toffset, location = common._prepare_http_data(content=content, name=from_user)
        if err != '':
            logger.warning(f'解析birthday、dist失败!! openid:{get_session(FROMUSER)}; 消息内容:{get_session(CONTENT)}')
            set_session(FILE_REPORT, filename_report)
            set_session(FILE_REQ, filename_req)
            set_session(FILE_SOUP1, filename_soup1)
            set_session(FILE_SOUP2, filename_soup2)

            return err

        birthday_concat = birthday.replace(" ", "").replace(":", "").replace("-", "")
        filename_report = f'report_{from_user}_{birthday_concat}_{dist}.pkl'
        filename_req = f'req_{from_user}.log'
        filename_soup1 = f'soup_{from_user}_{birthday_concat}_{dist}_almuten.pickle'
        filename_soup2 = f'soup_{from_user}_{birthday_concat}_{dist}_ixingpan.pickle'

        set_session(FILE_REPORT, filename_report)
        set_session(FILE_REQ, filename_req)
        set_session(FILE_SOUP1, filename_soup1)
        set_session(FILE_SOUP2, filename_soup2)

        return err

    # 第一轮对话
    if content in NUM_WHITELIST:
        err = ''
        # 读文件，加载最后一次输入的 loc（dist）+ birthday
        # last_line: logtime \t birthday \t dist \t location, eg: 20231107 10:12:57 \t 2023-11-07 10:12:57 \t 1550 \t 广东省深圳市南山区
        last_line = None
        with open('file.txt', 'r') as file:
            for line in file:
                last_line = line

        field = last_line.split('\t')
        if len(field) != 4:
            logger.warning(f'解析「用户历史请求」失败！！ 数组长度!=4，last_line={last_line}')
            err = '程序错误'

            set_session(FILE_REPORT, filename_report)
            set_session(FILE_REQ, filename_req)
            set_session(FILE_SOUP1, filename_soup1)
            set_session(FILE_SOUP2, filename_soup2)

            return err

        birthday = field[1]
        dist = field[2]
        birthday_concat = birthday.replace(" ", "").replace(":", "").replace("-", "")
        filename_report = f'report_{from_user}_{birthday_concat}_{dist}.pkl'
        filename_req = f'req_{from_user}.log'
        filename_soup1 = f'soup_{from_user}_{birthday_concat}_{dist}_almuten.pickle'
        filename_soup2 = f'soup_{from_user}_{birthday_concat}_{dist}_ixingpan.pickle'

        set_session(FILE_REPORT, filename_report)
        set_session(FILE_REQ, filename_req)
        set_session(FILE_SOUP1, filename_soup1)
        set_session(FILE_SOUP2, filename_soup2)

        return err

    # content中没有 location、birthday信息


def write_profile_and_soup(ixingpan, almuten):
    pass


# --------------------------- OLD ---------------------

def get_and_dump_report(filename, load_key='', is_load=True, overwrite=False):
    os.makedirs(get_session(FOLDERPATH), exist_ok=True)

    filepath = f'{get_session(FOLDERPATH)}/{filename}'

    if load_key != '':
        if load_key not in index_dict:
            logger.error(f'解析失败!! 用户输入Key:{load_key} not exists...')
            return None

        load_key = index_dict[load_key]

        if not os.path.exists(filename):
            logger.error(f'用户输入Key:{load_key} 但文件:{filename} 不存在...')
            return None

        with open(filename, 'rb') as file:
            all_trace_dict = pickle.load(file)

            if load_key not in all_trace_dict:
                logger.error(f'Load Pickle File Error!! Key:{load_key} not exists...')
                return None

            report = _gen_report(key=load_key, all_trace_dict=all_trace_dict)
            return report

    if is_load:
        if not os.path.exists(filepath):
            logger.debug(f'文件:{filepath} 不存在... 将走排盘逻辑')
            return None

        with open(filepath, 'rb') as file:
            all_trace_dict = pickle.load(file)
            logger.debug(f'成功加载文件: {filepath}')

            return _gen_report(key='上升点', all_trace_dict=all_trace_dict)

    # 写缓存 + 返回第一轮report
    all_trace_dict = web.ctx.env['trace_info']

    if os.path.exists(filepath):
        if not overwrite:
            logger.debug(f'缓存文件已存在, 直接返回report结果！路径:{filepath}')
            return _gen_report(key='上升点', all_trace_dict=all_trace_dict)

    logger.debug(f'写入/覆盖缓存文件, 并返回report结果！路径:{filepath}')
    with open(filepath, 'wb') as file:
        pickle.dump(all_trace_dict, file)
        report = _gen_report(key='上升点', all_trace_dict=all_trace_dict)
        return report


def _gen_report(key: str, all_trace_dict) -> str:
    logger.debug(f'_gen_report...')
    report = []
    report.append(f'『解析{key}』')

    field_dict = all_trace_dict[key]

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

    return '\n'.join(report)


index_str = '  '.join([f"{key}: {value}" for key, value in index_dict.items()])


def append_msg(report):
    v = [report]
    v.append(index_str)

    return '\n\n\n'.join(v)


def init_context():
    """
    加载文件、初始化context字典
    """
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

    web.ctx.env['knowledge_dict'] = knowledge_dict

    if 'star_dict' not in web.ctx.env:
        star_dict: Dict[str, common.Star] = {}
        web.ctx.env['star_dict'] = star_dict

    if 'house_dict' not in web.ctx.env:
        house_dict: Dict[int, common.House] = {}
        web.ctx.env['house_dict'] = house_dict

    all_trace_dict: Dict[str, Dict[str, List[str]]] = {}

    disaster_trace_dict: Dict[str, List[str]] = {}
    love_trace_dict: Dict[str, List[str]] = {}
    marriage_trace_dict: Dict[str, List[str]] = {}
    work_trace_dict: Dict[str, List[str]] = {}
    asc_trace_dict: Dict[str, List[str]] = {}
    study_trace_dict: Dict[str, List[str]] = {}

    all_trace_dict['灾星系统'] = disaster_trace_dict
    all_trace_dict['恋爱'] = love_trace_dict
    all_trace_dict['婚姻'] = marriage_trace_dict
    all_trace_dict['事业'] = work_trace_dict
    all_trace_dict['上升点'] = asc_trace_dict
    all_trace_dict['学业'] = study_trace_dict

    web.ctx.env['trace_info'] = all_trace_dict

    web.ctx.env['is_debug'] = False

    wealth_trace_dict: Dict[str, List[str]] = {}
    health_trace_dict: Dict[str, List[str]] = {}
    nature_trace_dict: Dict[str, List[str]] = {}



urls = (
    '/wx_hello_astro', 'Handle',
)

if __name__ == '__main__':
    app = web.application(urls, globals())
    app.run()
