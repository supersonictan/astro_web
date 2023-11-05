# -*- coding: utf-8 -*-
from typing import Tuple

import requests
from enum import Enum
from bs4 import BeautifulSoup
from util import Aspect, Star, House
from util import *
from util import marriage_trace_dict


def get_house_energy():
    '''
    规则1：金星、木星落入宫内
    规则2：宫主星* 与金星、木星有任何相位
    规则3：宫主星与金星火木星存在互溶
    规则4：宫主星与宫内星有相位或者互溶
    规则5：宫主星落本宫
    :return: 几宫主能量 2/8
    '''
    sorted_dict = dict(sorted(house_dict.items(), key=lambda x: x[0]))

    debug_info = ''
    debug_vec = []
    for house_id, obj in sorted_dict.items():
        house_debug_vec = []

        energy_max = 0
        energy_house = 0
        ruler = obj.ruler  # 宫主星
        loc_star_vec = obj.loc_star

        '''规则1-宫内星看：金星、木星、宫主星落入宫内'''
        energy_max += 3
        for target in ['金星', '木星', ruler]:
            if target in loc_star_vec:
                energy_house += 1

                addition = '宫主星' if target == ruler else ''
                debug_info = f'{house_id}宫, {addition}{target}落本宫, 能量+1'
                house_debug_vec.append(debug_info)

        '''规则2-相位看： 宫主星与 [金、木、宫内星]有任何相位'''
        target_set = {'金星', '木星'}
        for star_a, star_obj in star_dict.items():
            # aspect_obj_vec = star_obj.aspect_vec_old
            aspect_obj_vec = list(star_obj.aspect_dict.values())
            aspect_vec = [item.star_b for item in aspect_obj_vec]

            # ruler 与金木有相位
            if star_a == ruler and len(target_set & set(aspect_vec)) > 0:
                energy_house += len(target_set & set(aspect_vec))
                debug_info = f'{house_id}宫, 宫主星与 [金、木、宫内星]有任何相位, 能量+1'
                house_debug_vec.append(debug_info)

            # 金木和 ruler 有相位
            if star_a in target_set and ruler in aspect_vec:
                energy_house += 1
                debug_info = f'{house_id}宫, 宫主星与 [金、木、宫内星]有任何相位, 能量+1'
                house_debug_vec.append(debug_info)

        '''规则3-从互溶接纳看：宫主星与 [金、木、宫内星]有互溶，或ruler被接纳'''
        target_set.update(set([item for item in loc_star_vec if item in {'太阳', '月亮', '水星', '金星', '火星', '木星', '土星'}]))

        recepted_dup_set = set()

        for star_a, star_obj in star_dict.items():
            # recepted_obj_vec = star_obj.recepted_vec_old
            recepted_obj_dict = star_obj.recepted_dict

            for key, recepted_obj in recepted_obj_dict.items():
                star_b, action_name = recepted_obj.star_b, recepted_obj.action_name

                # ruler 与金木宫内星有互溶
                if action_name in {'互容接纳', '互容'} and star_a == ruler and star_b in target_set and star_b not in recepted_dup_set:
                    energy_house += 1
                    debug_info = f'{house_id}宫, 宫主星与 {star_b}有互溶, 能量+1'
                    house_debug_vec.append(debug_info)
                    recepted_dup_set.add(star_b)

                #
                if action_name in {'互容接纳', '互容'} and star_b == ruler and star_a in target_set and star_a not in recepted_dup_set:
                    energy_house += 1
                    debug_info = f'{house_id}宫, 宫主星与 {star_a}有互溶, 能量+1'
                    house_debug_vec.append(debug_info)
                    recepted_dup_set.add(star_a)

                # 接纳
                if star_a == ruler and action_name == '接纳' and star_b not in recepted_dup_set:
                    energy_house += 1

                    debug_info = f'{house_id}宫, 宫主星被 {star_b}接纳, 能量+1'
                    house_debug_vec.append(debug_info)
                    recepted_dup_set.add(star_b)

        msg_tmp = f'\n{house_id}宫, 能量:{energy_house}'
        house_debug_vec.insert(0, msg_tmp)
        debug_vec.append(house_debug_vec)

    # for sub_vec in debug_vec:
    #     print('\n'.join(sub_vec))


def get_star_square_info(star: str) -> Tuple[List[str], List[str], str]:
    # Step 1. 判断被1挡灾星克的情况
    ruler_1 = house_dict[1].ruler
    ruler_8 = house_dict[8].ruler
    ruler_12 = house_dict[12].ruler

    msg_vec = []
    for r, desc in zip([ruler_8, ruler_1, ruler_12], ['8r', '1r', '12r']):
        if star in star_dict[r].aspect_dict and star_dict[r].aspect_dict[star].aspect in {'冲', '刑'}:
            msg_vec.append(f'{star}{star_dict[r].aspect_dict[star].aspect}{desc}')

    # Step 2. 获取2档灾星
    msg_vec2 = []
    for r in ['冥王', '海王', '天王']:
        if star in star_dict[r].aspect_dict and star_dict[r].aspect_dict[star].aspect in {'冲', '刑'}:
            msg_vec2.append(f'{star}{star_dict[r].aspect_dict[star].aspect}')

    msg_vec3 = [';'.join(msg_vec), ';'.join(msg_vec2)]
    bad_desc = ';'.join(msg_vec3)

    return msg_vec, msg_vec2, bad_desc


def get_house_square_info(house_id: int) -> Tuple[List[str], List[str], str]:
    star = house_dict[house_id].ruler

    msg_vec, msg_vec2, bad_desc = get_star_square_info(star)

    return msg_vec, msg_vec2, bad_desc



def parse_marrage():
    """1. 配偶是什么类型？观测7宫的宫内星和宫主星，星性可代表特征、类型。"""
    appearance_dict = {'太阳': '长相属于大气的类型，个子也会偏高，积极向上，并且是充满了自信。',
                       '月亮': '整体形象方面会偏向肉肉的感觉，身高中等，性格温柔体贴，懂得照顾另一半，顾家的类型，和另一半有情绪上的共鸣。',
                       '水星': '另一半会显得比较年轻，头脑灵活又聪明，有灵气。在沟通方面会给你不错的体验感，好像彼此有聊不完的话题，是有趣的一类人。',
                       '金星': '颜值会不错，气质与亲和力也很好。会注重另一半的外在形象，有较好的社交能力，双方相处也会感到和谐甜蜜。',
                       '火星': '精力充沛活泼类型，会喜欢运动，浑身带有力量和冲劲。另一半是相对外向性格，热情积极坦率，彼此能够相互促进，哪怕有争吵也是越吵越好',
                       '木星': '身材偏高大，性格上也是爽朗豁达，性格乐观且具有奉献精神，也是博闻广识的一类人，也有可能异地。',
                       '土星': '另一半整体气质是沉稳的，显得比较内敛，显得比较稳重可靠务实。懂得规划生活，对方有责任心和担当。'}
    ruler_7 = house_dict[7].ruler

    trace_vec_appearance = []
    msg = f'【7r={ruler_7}】{appearance_dict[ruler_7]}'
    trace_vec_appearance.append(msg)

    for star_name in house_dict[7].loc_star:
        if star_name in {'冥王', '天王', '海王', '北交'}:
            continue
        trace_vec_appearance.append(f'【7宫内{star_name}】{appearance_dict[star_name]}')

    marriage_trace_dict['配偶是什么类型的'] = trace_vec_appearance

    '''
    黄道状态是否良好（分数的高低）代表配偶自身的能力or先天健康
    7飞去的宫位，代表了配們追逐or重视的领域，例如：7飞10.
    代表『伴信有事业心•追求建功动业，社会地位，或省一分注重樂省价子等
    TODO：替换受克，得吉
    '''
    ruler_7_house = star_dict[ruler_7].house
    search_key = f'7飞{ruler_7_house}'
    knowledge_msg = f'【{search_key}】{knowledge_dict_old[search_key]}'
    marriage_trace_dict['配偶特点'] = [knowledge_msg]

    '''
    2. 配偶什么年纪？
    - 木星土星主大5-7岁
    - 日月主大3-5岁
    - 金水火主上下三岁
    - 甚至偏小，但是同时要参专盘主的命主星，比大小；
    - 7宫多星时可尝试叠加
    '''
    marriage_age_dict = {'木星': '比你大5~7岁', '土星': '比你大5~7岁',
                         '太阳': '比你大3~5岁', '月亮':'比你大3~5岁',
                         '金星': '与你同龄，上下3岁左右', '水星': '与你同龄，上下3岁左右', '火星': '与你同龄，上下3岁左右'}
    trace_age_vec = [f'【7r={ruler_7}】配偶{marriage_age_dict[ruler_7]}']
    for star_name in house_dict[7].loc_star:
        if star_name in {'冥王', '天王', '海王', '北交'}:
            continue
        trace_age_vec.append(f'【7宫内{star_name}】配偶{marriage_age_dict[star_name]}')

    marriage_trace_dict['配偶年龄'] = trace_age_vec

    '''
    3. 会不会离婚
    传统说，我们不喜欢太多的星进入婚姻宮，尤其是三王星，
    - 冥王，代表离异 or 复婚。
    - 天王，代表聚少离多 or 离异 or 不寻常的、有违世俗的婚姻。
    - 海王，一般多婚，或婚姻纠缠不清
    - 土星，年龄大，压力大
    - 1r-7r 对冲，轴线也算，无论是宫内星对冲，还是飞出去对冲，都代表大妻矛店大，容易不相让。
    - 1r-7r 黃道分数相差过大，也容易阴阳失衡，
    - 有时候日月相差过大也会有这种阴阳失调的问题
    - 7r 被克，被任何星体沖，都不理想：
    - 凶星（土火三王）5度以内，压上升轴or 下降轴，都会特别发凶，影响感情和决策。
    '''
    is_pluto_7 = 1 if '冥王' in house_dict[7].loc_star else 0
    is_uranus_7 = 1 if '天王' in house_dict[7].loc_star else 0
    is_neptune_7 = 1 if '海王' in house_dict[7].loc_star else 0
    is_1r_7r_bad = 0
    is_1r_7r_score_diff = 0

    ruler_1 = house_dict[1].ruler

    r1_aspect_vec = list(star_dict[ruler_1].aspect_dict.values())
    for obj in r1_aspect_vec:
        if ruler_7 == obj.star_b and obj.aspect in {'刑', '冲'}:
            is_1r_7r_bad = 1
            break

    score_7r = star_dict[ruler_7].score
    score_1r = star_dict[ruler_1].score
    is_1r_7r_score_diff = abs(int(score_1r) - int(score_7r))

    # 下降相位
    axis_vec = []
    for _, obj in star_dict['下降'].aspect_dict.items():
        if obj.aspect != '合':
            continue

        if obj.star_b in {'冥王', '天王', '海王', '土星', '火星'}:
            axis_vec.append(f'{obj.star_b}合下降轴,特别发凶,影响感情和决策')


    trace_divorce_vec = []
    trace_divorce_vec.append(f'【冥王代表离异or复婚】盘主冥王落7宫={is_pluto_7}')
    trace_divorce_vec.append(f'【天王代表<聚少离多>或<离异>或<不寻常的、有违世俗的婚姻>】盘主天王落7宫={is_uranus_7}')
    trace_divorce_vec.append(f'【海王一般多婚，或婚姻纠缠不清】盘主海王落7宫={is_neptune_7}')
    trace_divorce_vec.append(f'【7r、1r对冲】={is_1r_7r_bad}')
    trace_divorce_vec.append(f'【7r、1r分差过大】分差={is_1r_7r_score_diff}，7r：{score_7r}，1r：{score_1r}')
    if len(axis_vec) != 0:
        trace_divorce_vec.extend(axis_vec)
    else:
        trace_divorce_vec.append('未检测到凶星压下降轴！！凶星（土火三王）5度以内，压上升轴or 下降轴，都会特别发凶，影响感情和决策')

    marriage_trace_dict['未来离婚概率'] = trace_divorce_vec

    '''
    4. 配偶是否有外遇？
    7-11, 7-11-12， 7-12，一般来说，看到这个配置，我们可以断定盘主配偈的桃花非常的旺盛，
    但是在实际论盘中，需要考虑飞星和接纳的因素，飞星和接纳都是有方向的
    因此通过这个可以断定，是桃花主动来找这个人的配個，还是配偶主动去找桃花，互容真的相互的。
    从这个层面来给客户建议：7-11-1 的黄道状态来判定三人之间的实力。
    '''
    trace_affair_vec = []
    if search_key == '7飞11':
        trace_affair_vec.append(f'【{search_key}】可能配偶去找桃花。{knowledge_dict_old[search_key]}')
    else:
        trace_affair_vec.append(f'未检测到！！{search_key}: 可能配偶去找桃花。')

    # 是否有11飞7，7飞12
    ruler_11, ruler_12 = house_dict[11].ruler, house_dict[12].ruler
    ruler_11_loc, ruler_12_loc = star_dict[ruler_11].house, star_dict[ruler_12].house
    tmp_key = '11飞7'
    if ruler_11_loc == 7:
        trace_affair_vec.append(f'【{tmp_key}】可能有桃花来找配偶。{knowledge_dict_old[tmp_key]}')
    else:
        trace_affair_vec.append(f'未检测到！！{tmp_key}: 可能有桃花来找配偶。')

    tmp_key = '12飞7'
    if ruler_12_loc == 7:
        trace_affair_vec.append(f'【{tmp_key}】可能有桃花来找配偶。{knowledge_dict_old[tmp_key]}')
    else:
        trace_affair_vec.append(f'未检测到！！{tmp_key}: 可能有桃花来找配偶。')

    trace_affair_vec.append(f'需要check下「互溶、接纳」再来确定！7r:{ruler_7}，11r:{ruler_11}, 12r:{ruler_12}')

    marriage_trace_dict['未来配偶有外遇的概率'] = trace_affair_vec

    '''
    5. 婚姻/配偶能否给自己带财？
    - 1r2r 得7r接纳，或者 1r2r 与7互容时候，婚姻可带财。
    - 7r 飞 1r2r 也会有类似作用，但是能量低些，且最好 7r庙旺。
    - 如若 7r接纳互容5r，说明有了孩子，伴侣会给孩子钱
    :return:
    '''
    trace_money_vec = []

    ruler_2 = house_dict[2].ruler

    msg = f'未检测到！！1r={ruler_1}被7r={ruler_7}接纳！'
    if ruler_7 in star_dict[ruler_1].recepted_dict:
        msg = f'1r{ruler_1}被7r{ruler_7}{star_dict[ruler_1].recepted_dict[ruler_7].action_name}，可利财！'

    trace_money_vec.append(msg)

    msg = f'未检测到！！2r{ruler_2}被7r{ruler_7}接纳！'
    if ruler_7 in star_dict[ruler_2].recepted_dict:
        msg = f'2r{ruler_2}被7r{ruler_7}{star_dict[ruler_2].recepted_dict[ruler_7].action_name}，可利财！'

    trace_money_vec.append(msg)

    msg = f'未检测到！！7r{ruler_7}与1、2r互容！'
    for key, obj in star_dict[ruler_7].recepted_dict.items():
        if '互容' not in obj.action_name:
            continue

        if obj.star_b == ruler_1:
            msg = f'7r{ruler_7}与1r{ruler_1}{obj.action_name}，可利财！'
            trace_money_vec.append(msg)

        if obj.star_b == ruler_2:
            msg = f'7r{ruler_7}与2r{ruler_2}{obj.action_name}，可利财！'
            trace_money_vec.append(msg)

    if msg == f'未检测到！！7r{ruler_7}与1、2宫主互容！':
        trace_money_vec.append(msg)

    # 看7r是否飞1、2
    is_7r_loc1 = 1 if star_dict[ruler_7].house == 1 else 0
    is_7r_loc2 = 1 if star_dict[ruler_7].house == 2 else 0
    trace_money_vec.append(f'7飞1={is_7r_loc1}, 7飞2={is_7r_loc2}, 7r score={score_7r}')

    marriage_trace_dict['婚姻/配偶能否给自己带财?'] = trace_money_vec

    all_trace_dict['婚姻'] = marriage_trace_dict


def parse_wealth():
    """1. 钱怎么来，1r、2r得到接纳 互容"""

    '''
    【1】福点与金星有相位+1
    【2】福点与木星有相位 +1
    【3】福点与2宫主有相位+1
    
    【4】福点定位星与金星有相位+1
    【5】福点定位星与木星有相位+1
    【7】福点定位星与2宫主有相位+1

    【6】福点与福点定位星有相位+1
    【8】2宫主与2宫内行星有相位+1
    【9】2宫内落入金星+1
    【10】2宫内落入木星+1
    【11】2宫主与金星有相位 +1
    【12】2宫主与木星有相位+1
    '''
    constellation_dict = {'狮子': '太阳',
                        '巨蟹': '月亮',
                        '白羊': '火星',
                        '天蝎': '火星',
                        '金牛': '金星',
                        '天秤': '金星',
                        '双子': '水星',
                        '处女': '水星',
                        '射手': '木星',
                        '双鱼': '木星',
                        '摩羯': '土星',
                        '水瓶': '土星'}

    trace_wealth_vec = []
    ruler2 = house_dict[2].ruler
    ruler_fudian = constellation_dict[star_dict['福点'].constellation]

    energy = 0
    aspect_dict = {}  # {冲: 2}
    # 福点、福点定位星合 [金星，木星，2r] 有相位
    for star in ['金星', '木星', ruler2]:
        for target in ['福点', ruler_fudian]:
            if star in star_dict[target].aspect_dict:
                energy += 1
                trace_wealth_vec.append(f'{target}与{star}有相位')
                asp = star_dict[target].aspect_dict[star].aspect
                if asp in aspect_dict:
                    aspect_dict[asp] += 1
                else:
                    aspect_dict[asp] = 0

    # 福点定位星是否本身就行 金星、木星
    if ruler_fudian in ['金星', '木星']:
        trace_wealth_vec.append(f'福点定位星是金星 or 木星')
        energy += 1

    # 福点定位星和福点相位
    if ruler_fudian in star_dict['福点'].aspect_dict:
        trace_wealth_vec.append(f'福点定位星和福点有相位')
        energy += 1

    # 2宫主和宫内星有相位
    for star_in_house in house_dict[2].loc_star:
        if star_in_house in {'福点','北交','凯龙','婚神','冥王','海王','天王'}:
            continue
        if star_in_house in star_dict[ruler2].aspect_dict:
            trace_wealth_vec.append(f'2r和宫内星有相位')
            energy += 1

    # 金星 or 木星落2宫内
    for target in ['金星', '木星']:
        if target in house_dict[2].loc_star:
            trace_wealth_vec.append(f'2金星 or 木星落2宫内')
            energy += 1

    # 2r和金星 or 木星有相位
    for target in ['金星', '木星']:
        if target in star_dict[ruler2].aspect_dict:
            trace_wealth_vec.append(f'2r和金星 or 木星有相位')
            energy += 1

    # 2r是否是金木
    # if ruler2 in ['金星', '木星']:
    #     trace_wealth_vec.append(f'2r是金星 or 木星')
    #     energy += 1

    # trace_wealth_vec.append(f'2宫总能量数={energy}')
    trace_wealth_vec.insert(0, f'2宫总能量数={energy}')
    wealth_trace_dict['财富宫的能量'] = trace_wealth_vec

    """2. 钱从哪里来，所接纳自己的星体代表的宫位
        2: 父母财，固定工资
        3: 兄弟姐妹帮助自己
        4: 父母、房子
        5: 桃花子女财
        6: 技术财、工作财
        7: 配偶财、客户财
        8: 金融财、保险财
        9: 高等学历财、官司、法律、异地
        10: 权利变现、公职、大企业等
        11: 粉丝经济、互联网效应、人群、流量
        12:暗财，贪污受贿等
    """
    search_dict = { '2被1接纳':  '财星入命，自己带财，不愁吃喝',
                    '2被2接纳':  '父母财，固定工资',
                    '2被3接纳':  '兄弟姐妹帮助自己',
                    '2被4接纳':  '父母、房子',
                    '2被5接纳':  '桃花子女财',
                    '2被6接纳':  '技术财、工作财',
                    '2被7接纳':  '配偶财、客户财',
                    '2被8接纳':  '金融财、保险财',
                    '2被9接纳':  '高等学历财、撰写、官司、法律、异地',
                    '2被10接纳': '权利变现、公职、大企业等',
                    '2被11接纳': '粉丝经济、互联网效应、人群、流量变现',
                    '2被12接纳': '暗财，玄学，贪污受贿等'}

    # 判断接纳和飞行
    n_jiena = 0
    for star_b, recepted in star_dict[ruler2].recepted_dict.items():
        if '接纳' in recepted.action_name:
            n_jiena += 1

    trace_wealth_vec2 = [f'接纳数={n_jiena}']
    wealth_trace_dict['接纳数'] = trace_wealth_vec2

    # 从哪里得财（可能没有）:接纳了2r
    tmp_result_vec = []
    for star_b, recepted_obj in star_dict[ruler2].recepted_dict.items():
        level = recepted_obj.level
        lord_house_vec = star_dict[star_b].lord_house_vec
        for house_id in lord_house_vec:
            tmp_key = f'2被{house_id}接纳'
            tmp_result_vec.append(f'【{tmp_key}({level})】{search_dict[tmp_key]}')

    wealth_trace_dict['从哪里得财'] = tmp_result_vec

    ruler2_loc = star_dict[ruler2].house
    key = f'2飞{ruler2_loc}'
    wealth_trace_dict['钱会花在什么地方'] = [f'【{key}】{knowledge_dict_old[key]}']
    all_trace_dict['财富'] = wealth_trace_dict


def parse_health():
    trace_vec_health = {}
    """
    1、身体残疾的星盘:
        对6宫来说，1、11、8是凶宫
        身体残疾可能性较高的配置
        1）1r、11r、8r落6宫并严重受克
        2）6r落1、11、8宫并严重受克

        也有一定风险的配置：
        6r落其他宫位且严重受克
    """
    tmp_vec = []

    # Step1. 判断6r是否严重受克
    ruler6 = house_dict[6].ruler
    is_6r_attacked = False
    bad_vec1, bad_vec2, bad_desc = get_star_square_info(ruler6)
    if len(bad_vec1) >= 1 or len(bad_vec2) >= 2:
        is_6r_attacked = True

    # Step2. 判断1r 11r 8r 是否落6宫，或者6r落1,11,8宫
    if is_6r_attacked:
        find_num = 0
        for tmp_ruler, ruler_name in zip([house_dict[1].ruler, house_dict[8].ruler, house_dict[11].ruler], ['1r', '8r', '11r']):
            if tmp_ruler in house_dict[6].loc_star:
                tmp_vec.append(f'【凶星{ruler_name}={tmp_ruler}落6，并6r严重受克，具体信息:{bad_desc}】检测到身体有可能患有残疾.')
                find_num += 1

        for house_id, house_name in zip([1, 8, 11], ['1宫', '8宫', '11宫']):
            if ruler6 in house_dict[house_id].loc_star:
                tmp_vec.append(f'【6r落凶宫，并6r严重受克，受克信息:{bad_desc}】检测到身体有可能患有残疾.')
                find_num += 1

        if find_num == 0:
            tmp_vec.append('【6r受克，但未落凶宫】身体有一定概率落下残疾')

    else:
        tmp_vec.append('【6r未受克】未发现身体落下残疾的星象')

    health_trace_dict['发生残疾的概率'] = tmp_vec

    """
    2、性取向或偏好异常
        1）8r、12r受克，尤其是被海王、冥王刑克更为明确
        2）8r、12r落8，12宫
        3）8r、12r克命主 or 上升点
        4）8r与12r相克
    """

    ruler8 = house_dict[6].ruler
    is_8r_attacked = False
    bad_vec1, bad_vec2, bad_desc_8r = get_star_square_info(ruler8)
    if len(bad_vec1) >= 1 or len(bad_vec2) >= 2:
        is_8r_attacked = True

    """
    3、死于他杀或意外的配置
        1）8r严重受克，尤其是频繁形成中点相位
        2）8落2、7、3、1、8、12宫，且严重受克
        3）2r、7r、3r、1r、8r、12r落8宫且严重受克
    """
    tmp_vec = []
    if is_8r_attacked:
        find_num = 0
        for house_id, house_name in zip([2, 7, 3, 1, 8, 12], ['2宫', '7宫', '3宫', '1宫', '8宫', '12宫']):
            if ruler8 in house_dict[house_id].loc_star:
                health_trace_dict['发生他杀或意外死亡的概率'] = [f'【8r落凶宫，并8r严重受克，受克信息:{bad_desc_8r}】检测到有可能意外死亡.']
                find_num += 1
                break

        tmp_star = [house_dict[2].ruler, house_dict[7].ruler, house_dict[3].ruler, house_dict[1].ruler, house_dict[8].ruler]
        tmp_star_name = ['2r', '7r', '3r', '1r', '8r']

        for tmp_ruler, ruler_name in zip(tmp_star, tmp_star_name):
            if tmp_ruler in house_dict[8].loc_star:
                tmp_vec.append(f'【8r的凶星{ruler_name}={tmp_ruler}落8宫，并8r严重受克，具体信息:{bad_desc_8r}】检测到身体有可能患有残疾.')
                find_num += 1

        if find_num  == 0:
            tmp_vec.append('【8r受克，但未落凶宫】有一定概率死于意外')

        health_trace_dict['发生他杀或意外死亡的概率'] = tmp_vec

    else:
        health_trace_dict['发生他杀或意外死亡的概率'] = ['【8r未严重受克】未发死于他杀或意外的星象']

    """
    4、自杀星盘
        1）月亮严重受克，8宫主严重受克
    :return:
    """
    is_moon_attacked = False
    bad_vec1, bad_vec2, bad_desc = get_star_square_info('月亮')
    if len(bad_vec1) >= 1 or len(bad_vec2) >= 2:
        is_moon_attacked = True

    if is_moon_attacked and is_8r_attacked:
        health_trace_dict['发生自杀的概率'] = ['【月亮严重受克，8宫主严重受克】有一定概率因为内心想不开而自杀']
    else:
        health_trace_dict['发生自杀的概率'] = ['【月亮、8宫主未受克】没有发现自杀星象']

    all_trace_dict['健康'] = health_trace_dict



def parse_asc_star():
    # 解析命主星落宫
    asc_star = house_dict[1].ruler
    asc_house = star_dict[asc_star].house

    key = f'命主星{asc_house}宫'
    desc = knowledge_dict['命主星落宫'][key]
    asc_trace_dict['重点概括'] = [f'【{key}】{desc}']

    all_trace_dict['个性显现及生活领域上的重点'] = asc_trace_dict


def parse_study():
    # 解析：初等学业、高等学业
    ruler_3 = house_dict[3].ruler
    ruler_9 = house_dict[9].ruler

    ruler_3_house = star_dict[ruler_3].house
    ruler_9_house = star_dict[ruler_9].house

    key3 = f'3飞{ruler_3_house}'
    key9 = f'9飞{ruler_9_house}'
    junior_desc = knowledge_dict['初等学业飞星'][key3]
    senior_desc = knowledge_dict['高等学业飞星'][key9]

    study_trace_dict['高中前'] = [junior_desc]
    study_trace_dict['高中后'] = [senior_desc]

    # 3、9宫落⭐️
    star_in_3 = house_dict[3].loc_star
    star_in_9 = house_dict[9].loc_star

    for id in [3, 9]:
        for s in house_dict[id].loc_star:
            key = f'{s}{id}宫'

            sub_dict = knowledge_dict['初等学业飞星'] if id == 3 else knowledge_dict['高等学业飞星']

            if id == 3 and key in sub_dict:
                study_trace_dict['高中前'].append(sub_dict[key])
            elif id == 9 and key in sub_dict:
                study_trace_dict['高中后'].append(sub_dict[key])


    all_trace_dict['学业'] = study_trace_dict


def parse_nature():
    sub_vec = []
    for star_a, obj in star_dict.items():
        if star_a not in short_mapping:
            continue
        star_a = short_mapping[star_a]

        for star_b, asp in obj.aspect_dict.items():
            if asp.aspect not in ['合', '冲', '刑']:
                continue

            if star_b not in short_mapping:
                continue
            star_b = short_mapping[star_b]

            key = f'{star_a}{star_b}{asp.aspect}'

            if key in knowledge_dict['行星相位']:
                sub_vec.append(f"【{key}】{knowledge_dict['行星相位'][key]}")

    nature_trace_dict['性格分析'] = sub_vec
    all_trace_dict['性格分析'] = nature_trace_dict


