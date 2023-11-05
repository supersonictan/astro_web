# -*- coding: utf-8 -*-

import web
import sys
from typing import Dict

from common import *

sys.path.append('/root/code/astro_web')
import logging
import reply
import receive

# 创建日志记录器
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


def load_context_file():
    """
    knowledge_web.ini
    knowledge.csv
    jobs.csv
    ixingpan_area.json

    :return:
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

    return knowledge_dict




class Handle():
    def POST(self):
        try:
            webData = web.data()
            # print("Handle Post webdata is ", webData)

            recMsg = receive.parse_xml(webData)

            if not (isinstance(recMsg, receive.Msg) and recMsg != 'text'):
                logger.fatal('暂不处理')
                return 'success'

            toUser = recMsg.FromUserName
            fromUser = recMsg.ToUserName

            content = recMsg.Content
            content = content.decode('utf-8')

            # Init Context Variable
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

            err, reply_str = common.basic_analyse(customer_name=recMsg.FromUserName, content=content)
            if err != '':
                replyMsg = reply.TextMsg(toUser, fromUser, f'【排盘失败】\n{err}, 请重新检查输入...')
                return replyMsg.send()

            print(f'ret_vec len is:{len(ret_vec)}')
            reply_str = ','.join(ret_vec)
            reply_str = reply_str[:230]
            # replyMsg = reply.TextMsg(toUser, fromUser, reply_str)
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
