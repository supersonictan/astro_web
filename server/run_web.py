# -*- coding: utf-8 -*-
import configparser

import web
import sys
from typing import Dict, List
import os
import pickle

sys.path.append('/root/code/astro_web')

import common
import logging
import reply
import receive


logger = logging.getLogger('run_web.py')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

logger.setLevel(logging.DEBUG)


DEBUG_BLACK_SET = {'ACTUAL_SERVER_PROTOCOL', 'PATH_INFO', 'QUERY_STRING', 'REMOTE_ADDR', 'REMOTE_PORT', 'REQUEST_METHOD', 'REQUEST_URI', 'SCRIPT_NAME', 'SERVER_NAME', 'SERVER_PROTOCOL', 'SERVER_SOFTWARE', 'wsgi.errors', 'wsgi.input', 'wsgi.input_terminated', 'wsgi.multiprocess', 'wsgi.multithread', 'wsgi.run_once', 'wsgi.url_scheme', 'wsgi.version', 'SERVER_PORT', 'HTTP_USER_AGENT', 'HTTP_ACCEPT', 'HTTP_HOST', 'HTTP_PRAGMA', 'CONTENT_TYPE', 'CONTENT_LENGTH'}

class Handle():
    def POST(self):
        try:
            webData = web.data()
            logger.error(f"Handle Post webdata is {webData}")

            recMsg = receive.parse_xml(webData)

            if not (isinstance(recMsg, receive.Msg) and recMsg != 'text'):
                logger.fatal('暂不处理')
                return 'success'

            toUser = recMsg.FromUserName
            fromUser = recMsg.ToUserName

            content = recMsg.Content
            content = content.decode('utf-8')

            logger.debug(f'----------> FromUser:{recMsg.FromUserName} ToUser:{recMsg.ToUserName} Content:{content}')

            init_context()

            err, birthday, dist, is_dst, toffset, location = common._prepare_http_data(content=content, name=recMsg.FromUserName)
            if err != '':
                replyMsg = reply.TextMsg(toUser, fromUser, f'【排盘失败】\n{err}, 请重新检查输入...')
                return replyMsg.send()

            folder_path = f'./cache/basic/{recMsg.FromUserName}'
            birthday_concat = birthday.replace(" ", "").replace(":", "").replace("-", "")
            dump_filename = f'{folder_path}/report_{recMsg.FromUserName}_{birthday_concat}_{dist}.pkl'

            # 非第一轮对话：读pkl，并返回对应结果
            if content in {'1', '2', '3', '4', '5', '6', '7'}:
                report = get_and_dump_report(dump_filename, load_key=content)

                if report is None:
                    replyMsg = reply.TextMsg(toUser, fromUser, f'【排盘失败】\n, 请重新检查输入...')
                    return replyMsg.send()

                replyMsg = reply.TextMsg(toUser, fromUser, report)
                return replyMsg.send()

            # 第一轮对话，先check缓存
            report = get_and_dump_report(dump_filename, load_key='', is_load=True)
            if report is not None:
                logger.debug('第一轮对话，缓存未命中')
                ret = append_msg(report)
                replyMsg = reply.TextMsg(toUser, fromUser, ret)
                return replyMsg.send()

            logger.debug('第一轮对话，查http')
            err, reply_str = common.basic_analyse(customer_name=recMsg.FromUserName, content=content)
            logger.debug('After basic_analyse.....')
            if err != '':
                replyMsg = reply.TextMsg(toUser, fromUser, f'【排盘失败】\n{err}, 请重新检查输入...')
                return replyMsg.send()

            report = get_and_dump_report(dump_filename, load_key='', is_load=False)

            reply_str = append_msg(report)
            replyMsg = reply.TextMsg(toUser, fromUser, reply_str)

            return replyMsg.send()

        except Exception as Argument:
            print(Argument)
            return Argument


index_dict = {'1': '别人眼中自己', '2': '恋爱', '3': '婚姻', '4': '学业', '5': '事业', '6': '财富'}


def get_and_dump_report(filename, load_key='', is_load=True):
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
        logger.debug(f'尝试加载缓存文件...')
        if not os.path.exists(filename):
            logger.debug(f'文件:{filename} 不存在... 将走排盘逻辑')
            return None

        with open(filename, 'rb') as file:
            all_trace_dict = pickle.load(file)
            return _gen_report(key='上升点', all_trace_dict=all_trace_dict)

    all_trace_dict = web.ctx.env['trace_info']

    if os.path.exists(filename):
        logger.debug(f'找到缓存文件...')
        return _gen_report(key='上升点', all_trace_dict=all_trace_dict)

    with open(filename, 'wb') as file:
        pickle.dump(all_trace_dict, file)

        logger.debug(f'before _gen_report...')
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

    return '\n\n'.join(v)


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
