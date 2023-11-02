# -*- coding: utf-8 -*-

import web
# import logging
from handle import Handle

# logging.basicConfig(filename='webapp.log', level=logging.INFO)

urls = (
    '/wx_hello_astro', 'Handle',
)

if __name__ == '__main__':
    app = web.application(urls, globals())
    app.run()
