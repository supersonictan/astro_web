# coding=utf-8


"""
File: handle.py
Date: 2023/11/01 12:11:35
Brief: 
"""
import sys
sys.path.append('/root/code/astro_web')
from typing import Tuple
import reply
import receive
import web
import re
import cpca
import os
from bs4 import BeautifulSoup
from common import prepare_http_data

from util import star_dict, house_dict
from util import all_trace_dict
from util import parse_glon_glat
from util import dump_load_http_result, logger, build_almuten_http_data
from util import fetch_almuten_soup, fetch_ixingpan_soup
from util import load_knowledge_file, load_knowledge_data_old, load_jobs_file
from util import parse_almuten_star, parse_almuten_house
from util import parse_ixingpan_star, parse_ixingpan_house, parse_ixingpan_aspect
from basic_analyse import *
from basic_analyse import get_square, get_house_energy
from basic_analyse import parse_love, parse_marrage_2, parse_marrage, parse_wealth, parse_health, parse_work, parse_asc_star, parse_study, parse_nature


USE_CACHE = True
IS_DEBUG = True



if __name__ == '__main__':
    inp_str_vec = ['山东省济南市历下区，时间是1989年8月5日下午12点58分',
               '山东省济南市历下区，时间是:1989.8.5 12点58分']
    for inp_str in inp_str_vec:
        #print(parse_time(inp_str))
        pass

    import time

    stime = time.strptime("1998-08-05 12:58", "%Y-%m-%d %H:%M")
    print(bool(stime.tm_isdst))
