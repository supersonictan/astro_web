# -*- coding: utf-8 -*-

import web
from handle import Handle
import logging


# formatter = logging.Formatter('%(levelname)s - %(message)s')
# console_handler = logging.StreamHandler()
# console_handler.setFormatter(formatter)
# 
# # logging.basicConfig(filename='webapp.log', level=logging.INFO)
# logger = logging.getLogger('my_logger')
# logger.setLevel(logging.DEBUG)
# logger.addHandler(console_handler)
# 
# file_logger = logging.getLogger('my_file_logger')
# file_logger.setLevel(logging.INFO)


urls = (
    '/wx_hello_astro', 'Handle',
)

if __name__ == '__main__':
    app = web.application(urls, globals())
    app.run()
