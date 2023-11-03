# -*- coding: utf-8 -*-

import web
import sys

import common

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
