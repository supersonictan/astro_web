# -*- coding: utf-8 -*-
import configparser

import web
import sys
from typing import Dict, List
import os
import pickle


sys.path.append('/root/code/astro_web')

import common
from common import build_result
from common import basic_analyse
from common import get_session, set_session
from common import init_session
from Const import *
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
ID_SET_WHITELIST = {'1', '2', '3', '4', '5', '6', '7'}

class Handle():
    def POST(self):
        try:
            set_session(ERROR, '')
            webData = web.data()

            recMsg, from_user, to_user, content = parse_request_data(webData=webData)
            if not (isinstance(recMsg, receive.Msg) and recMsg != 'text'):
                logger.fatal('暂不处理')
                return 'success'

            # 加载文件、初始化存结果的dict
            init_session()
            if get_session(ERROR) != '':
                replyMsg = reply.TextMsg(from_user, to_user, get_session(ERROR))
                return 'success'
                # return replyMsg.send()

            # 非数字 & 有缓存 --> 返回缓存结果
            if get_session(HAS_REPORT_FILE) and not get_session(IS_INPUT_NUM):
                logger.debug('非数字 & 有缓存 --> 返回缓存结果...')
                reply_str = build_result()
                replyMsg = reply.TextMsg(from_user, to_user, reply_str)
                return replyMsg.send()
            elif not get_session(IS_INPUT_NUM) and not get_session(HAS_REPORT_FILE):
                # 非数字 & 无缓存 --> http咯
                logger.debug('非数字 & 无缓存 --> http咯...')
                basic_analyse()
                if get_session(ERROR) != '':
                    reply_str = get_session(ERROR)
                else:
                    reply_str = build_result()

                replyMsg = reply.TextMsg(from_user, to_user, reply_str)
                return replyMsg.send()
            elif get_session(IS_INPUT_NUM) and get_session(HAS_REPORT_FILE):
                # 数字 & 有缓存 --> 返回缓存结果
                logger.debug('数字 & 有缓存 --> 返回缓存结果...')
                reply_str = build_result(get_session(TargetDomain))
                replyMsg = reply.TextMsg(from_user, to_user, reply_str)
                return replyMsg.send()
            elif get_session(IS_INPUT_NUM) and not get_session(HAS_REPORT_FILE):
                logger.debug('数字 & 无缓存 --> 返回异常结果...')
                # 数字 & 无缓存 --> 返回异常结果
                replyMsg = reply.TextMsg(from_user, to_user, get_session(COMMON_ERR_MSG))
                return replyMsg.send()

        except Exception as e:
            logger.error(e.with_traceback())
            return e



urls = (
    '/wx_hello_astro', 'Handle',
)

if __name__ == '__main__':
    app = web.application(urls, globals())
    app.run()


def parse_request_data(webData):
    recMsg = receive.parse_xml(webData)
    toUser = recMsg.ToUserName
    fromUser = recMsg.FromUserName
    content = recMsg.Content.decode('utf-8')

    set_session(TOUSER, toUser)
    set_session(FROMUSER, fromUser)
    set_session(CONTENT, content)

    # logger.debug(f'----------> FromUser:{get_session(FROMUSER)} ToUser:{get_session(TOUSER)} Content:{get_session(CONTENT)}')

    return recMsg, fromUser, toUser, content

