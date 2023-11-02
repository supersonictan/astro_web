# -*- coding: utf-8 -*-

import web
# import logging
from handle import Handle
import logging


# logging.basicConfig(filename='webapp.log', level=logging.INFO)
logger = logging.getLogger('my_logger')
logger.setLevel(logging.DEBUG)

file_logger = logging.getLogger('my_file_logger')
file_logger.setLevel(logging.INFO)


urls = (
    '/wx_hello_astro', 'Handle',
)

if __name__ == '__main__':
    app = web.application(urls, globals())
    app.run()
