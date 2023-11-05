# -*- coding: utf-8 -*-
import configparser

import web
import sys
from typing import Dict, List


sys.path.append('/root/code/astro_web')

import common
import logging
import reply
import receive

# 创建日志记录器
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# console_handler = logging.StreamHandler()
# console_handler.setFormatter(formatter)
# logger.addHandler(console_handler)


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

    # web.ctx.env['knowledge_dict'] = knowledge_dict

    if 'star_dict' not in web.ctx.env:
        star_dict: Dict[str, common.Star] = {}
        web.ctx.env['star_dict'] = star_dict

    if 'house_dict' not in web.ctx.env:
        house_dict: Dict[int, common.House] = {}
        web.ctx.env['house_dict'] = house_dict

    all_trace_dict: Dict[str, Dict[str, List[str]]] = {}

    disaster_trace_dict: Dict[str, List[str]] = {}
    all_trace_dict['灾星系统'] = disaster_trace_dict

    web.ctx.env['trace_info'] = all_trace_dict


    marriage_trace_dict: Dict[str, List[str]] = {}
    love_trace_dict: Dict[str, List[str]] = {}
    wealth_trace_dict: Dict[str, List[str]] = {}
    health_trace_dict: Dict[str, List[str]] = {}
    work_trace_dict: Dict[str, List[str]] = {}
    asc_trace_dict: Dict[str, List[str]] = {}
    study_trace_dict: Dict[str, List[str]] = {}
    nature_trace_dict: Dict[str, List[str]] = {}


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

            logger.debug(f'FromUser:{recMsg.FromUserName} ToUser:{recMsg.ToUserName} Content:{content}')

            init_context()

            err, reply_str = common.basic_analyse(customer_name=recMsg.FromUserName, content=content)
            logger.debug('After basic_analyse.....')
            if err != '':
                replyMsg = reply.TextMsg(toUser, fromUser, f'【排盘失败】\n{err}, 请重新检查输入...')
                return replyMsg.send()

            # DEBUG
            for k, v in web.ctx.env.items():
                if k not in DEBUG_BLACK_SET:
                    print(f'------------> key:{k}\tval:{v.values()}')

            reply_str = 'hahahaahh'
            replyMsg = reply.TextMsg(toUser, fromUser, reply_str)

            return replyMsg.send()

        except Exception as Argument:
            print(Argument)
            return Argument



urls = (
    '/wx_hello_astro', 'Handle',
)

if __name__ == '__main__':

    app = web.application(urls, globals())
    app.run()
