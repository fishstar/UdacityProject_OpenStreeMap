#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Python 3.6

import pandas as pd
import re

#-------- 清洗电话号码 -----------

def is_mobile_phone(value):
    '''判断是否是移动电话号码, 是则返回True，不是返回False。
    判断标准：位数是11位，且以特定的三位数字开头。'''
    
    start_number = ['133', '153', '180', '181', '189', '177', '173', '149',
                    '130', '131', '132', '155', '156', '145', '185', '186',
                    '176', '175', '134', '135', '136', '137', '138', '139', 
                    '150', '151', '152', '157', '158', '159', '182', '183',
                    '184', '187', '188', '147', '178']
    if (len(value) == 11) and (value[:3] in start_number): 
        return True
    else:
        return False
        

def style_phone_number(phone_value):
    '''将不符合标准格式的电话号码转换成标准格式。
    标准格式定义成：国家编号 + [区号] + 号码。'''

    # 去除非数字的字符
    digit_value = ''
    for char in phone_value:
        if char.isdigit():
            digit_value += char
    
    # 定义一些可能出现的号码格式
    # 以下列表中每一个元素都是数据中出现的号码格式，元组的第一个元素代表打头的数字，第二个元素代表位数
    phone_style = [('8610',12), ('86010', 13), ('008610', 14), ('010', 11), 
                    ('10', 10), ('86', 10), ('', 8) ]
    mobile_style = [('86', 13), ('0086', 15), ('', 11)]
    special_style = [('86400', 12), ('400', 10)]
        
    # 按固定电话、移动电话、400电话三种形式分别进行电话号码格式的标准化    
    if (digit_value[:-8], len(digit_value)) in phone_style:
        styled_value = '+86 10 ' + digit_value[-8:]
    elif ((digit_value[:-11], len(digit_value)) in mobile_style) \
            and is_mobile_phone(digit_value[-11:]):
        styled_value = '+86 ' + digit_value[-11:]
    elif (digit_value[:-7], len(digit_value)) in special_style:
        styled_value = '+86 ' + digit_value[-10:]
    else: 
        styled_value = digit_value

    return styled_value
    
    
def is_phone_styled(phone_number):
    '''判断电话号码是否符合标准格式。'''

    phone_pattern = r'^\+86 10 \d{8}$'
    mobile_phone_pattern = r'^\+86 \d{11}$'
    special_pattern = r'^\+86 400\d{7}$'
    if (re.fullmatch(phone_pattern, phone_number)  \
        or re.fullmatch(mobile_phone_pattern, phone_number) \
        or re.fullmatch(special_pattern, phone_number)):
        return True
    else:
        return False
        
        
def process_phone(df):
    '''清洗数据中的电话号码。
    返回的结果是被丢弃的不正确的电话号码，除此之外其他号码都被标准格式替代。'''

    # 用统一的格式替换原数据中各种类型的电话号码
    # 针对用分号分隔的多个电话号码，需要特殊对待
    for index, row in df.loc[df.key=='phone'].iterrows():
        phone_value = row['value']
        if len(phone_value) >= 17:
            if phone_value.find('/') > 0:          
                phone_list = phone_value.split('/')
                phone_number = ';'.join(style_phone_number(x) for x in phone_list)
            elif phone_value.find(';') > 0:
                phone_list = phone_value.split(';')
                phone_number = ';'.join(style_phone_number(x) for x in phone_list)
            elif phone_value.find('；') > 0:
                phone_list = phone_value.split('；')
                phone_number = ';'.join(style_phone_number(x) for x in phone_list)        
            else:
                phone_number = style_phone_number(phone_value)
        else:
            phone_number = style_phone_number(phone_value)

        df.loc[index, 'value'] = phone_number
    

    # 返回不正确的电话号码，并将它们从数据中删除
    wrong_number = []
    for index, row in df.loc[df.key=='phone'].iterrows():  
        phone_number = row['value']
        if phone_number.find(';') > 0:
            phone_list = phone_number.split(';') 
            for number in phone_list:
                if not is_phone_styled(number):
                    wrong_number.append(number)
                    df.drop(index, inplace=True)
        else:
            if not is_phone_styled(phone_number):
                wrong_number.append(phone_number)
                df.drop(index, inplace=True)    
 
        
    return wrong_number
    
    
    
    
 #--------- 清洗邮政编码 ---------------   
    
def process_postcode(df):
    '''清洗数据中的邮政编码。
    返回值是被丢弃的错误的邮编。 '''

    wrong_list = []
    # 定义邮编的正则表达式，北京地区邮编以100、101、102开头，共6位数字
    postcode_parttern = r'^10[0-2]\d{3}$'
    
    # 判断邮编是否符合以上定义的正则表达式，不符合则从数据中删除
    for index, row in df[df.key=='postcode'].iterrows():
        code = row['value']
        if not re.fullmatch(postcode_parttern, code):
            wrong_list.append(code)
            df.drop(index, inplace=True)
            
    return wrong_list    
    
    

#--------- 清洗营业时间数据-------------
    

def is_hour(value): 
    '''判断营业时间是否满足统一的格式'''

    # 关于小时、星期、月份的正则表达式
    h = '\d{1,2}:\d{1,2}'  
    w = '(Mo|Tu|We|Th|Fr|Sa|Su)'
    m = '(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)'
    md = m +' \d{1,2}'
    
    # 定义了营业时间的统一格式，共有10中形式
    p0 = '24/7'                    # 表示7天24小时都营业
    p1 = h + '-' + h               # e.g. 06:00-23:00
    p2 = w + '-' + w + ' ' + p1    # e.g. Mo-Su 06:00-23:00
    p3 = w + ' ' + p1              # e.g. Sat 09:30-22:00
    p4 = m + '-' + m + ' ' + p2    # e.g. Apr-Oct Mo-Su 05:00-24:00
    p5 = md + '-' + md + ' ' + p1  # e.g. Apr 1-Oct 31 05:00-24:00
    p6 = p2 + ', ' + p1            # e.g. Su-Fr 08:30-11:30, 13:30-17:00
    p7 = p1 + ', ' + p1            # e.g. 08:30-11:30, 13:30-17:00
    p8 = m + '-' + m + ' ' + p1    # e.g. Apr-Oct 08:00-17:00
    p9 = p1 + ',' + p1

    # 判断数据是否满足以上给出的统一格式，是则返回True，否则返回False
    if  (re.fullmatch(p1, value) \
        or re.fullmatch(p2, value) \
        or re.fullmatch(p3, value) \
        or re.fullmatch(p4, value) \
        or re.fullmatch(p5, value) \
        or re.fullmatch(p6, value) \
        or re.fullmatch(p7, value) \
        or re.fullmatch(p8, value) \
        or re.fullmatch(p9, value) \
        or value == p0):
        return True
    else:
        return False
      


def find_mess_hour(df):
    '''在数据中查找混乱的时间数据，返回相应的索引和对应的值。'''

    wrong_index = []
    wrong_hour = []
    for index, row in df[df.key=='opening_hours'].iterrows():
        hour = row['value']
        if hour.find(';') > 0:
            hour_list = hour.split(';')
            for h in hour_list:
                if not is_hour(h.strip()):
                    wrong_hour.append(h)
                    wrong_index.append(index)
        else:
            if not is_hour(hour):
                wrong_hour.append(hour)
                wrong_index.append(index)

    return wrong_index, wrong_hour
                        
                
                
def process_multi_hours(df):
    '''处理包含多个时间的情况。'''

    h = '\d{1,2}:\d{1,2}'
    p1 = h + '-' + h
    for index, row in df[df.key=='opening_hours'].iterrows():
        hour = row['value']
        find_list = re.findall(p1, hour)
            
        if (hour.find(';') < 0) and ((hour.find(',') < 0)) and (len(find_list) > 1):
            hour_list = []
            head_list = re.split(p1, hour)
            for i,s in enumerate(find_list):
                hour_list.append(head_list[i].strip() + ' ' + s)                
            df.loc[index, 'value'] = ';'.join(hour_list)
                


def style_hour(string):
    '''统一时间格式。'''

    # Mon to Mo
    w2 = '(Mon|Tue|Wed|Thu|Fri|Sat|Sun)'
    w2_list = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    slist = re.split(w2, string)
    for i, s in enumerate(slist):
        if s in w2_list:
            slist[i] = slist[i][:-1]
    string = ''.join(slist)
    
    # 24h
    list_24 = ['24h', '24小时', '24/24', 'ALL']
    if string in list_24:
        string = '24/7'
    
    
    # replace 'to' with '-' e.g. 9:00 to 22:00
    if string.find('to') > -1:
        string = string.replace('to', '-')
    
    # fix 9:30~21:30
    h = '\d{1,2}:\d{1,2}'
    wp1 = h + '~' + h
    if re.match(wp1, string):
        string = string.replace('~', '-')


    # fix 10.00-24.00
    wp4 = '\d{1,2}\.\d{1,2}'
    m = re.search(wp4, string)
    if m:
        string = string.replace('.', ':')
    
    # wrong '：' e.g. 10：00-24：00
    if re.search('：', string):
        string = string.replace('：', ':')
        

    # remove redundant ':', e.g. Jan-Dec: Mo-Su 11:00-23:00
    wp5 = '[A-Za-z]*: [A-Za-z]*'
    m = re.search(wp5, string)
    if m:
        s = m.start()
        e = m.end()
        string = string[:s] + m.group(0).replace(':', '') + string[e:]
        
        
    # am, pm 
    pam1 = '\d{1,2}:\d{1,2}(am|AM)'
    ppm1 = '\d{1,2}:\d{1,2}(pm|PM)'
    am1 = re.search(pam1, string)
    if am1:
        s = am1.start()
        e = am1.end()
        ho = string[s:e-2]
        string = string[:s] + ho + string[e:]

    pm1 = re.search(ppm1, string)
    if pm1:
        s = pm1.start()
        e = pm1.end()
        ho = string[s:e-2]
        sh = ho.split(':')
        ho = str(int(sh[0]) + 12) + ':' + sh[1]
        string = string[:s] + ho +string[e:]
    
    pam2 = '\d{1,2}(am|AM)'
    ppm2 = '\d{1,2}(pm|PM)'
    am2 = re.search(pam2, string)
    if am2 and (not am1):
        s = am2.start()
        e = am2.end()
        ho = string[s:e-2]
        string = string[:s] + ho + ':00'+string[e:]

    pm2 = re.search(ppm2, string)
    if pm2 and (not pm1):
        s = pm2.start()
        e = pm2.end()
        ho = string[s:e-2]
        ho = str(int(ho) + 12)
        string = string[:s] + ho + ':00'+string[e:]

    
    if string.find(':00am'):
        string = string.replace('am', '')
        
    # fix 06:00-10:00 am
    wp6 = h + '-' + h + ' am'
    m = re.search(wp6, string)
    if m:
        s = m.start()
        e = m.end()
        string = string[:s] + m.group(0).replace(' am', '') + string[e:]    
        
        
    # drop space e.g. 9:00 - 22:00  or 10：00-24：00
    wp2 = h + ' - ' + h
    wp3 = '\d{1,2}:\s\d{1,2}-\d{1,2}:\s\d{1,2}'
    if re.match(wp2, string) or re.match(wp3, string):
        string = ''.join(string.split(' '))
            
        
    return string.strip()

    
    
def process_opening_hours(df):
    '''清洗数据中的营业时间，统一成特定的格式；将不能统一的数据丢弃，并作为返回结果。'''
    
    process_multi_hours(df)
    
    for index, row in df[df.key=='opening_hours'].iterrows():
        hour = row['value']
        if hour.find(';') > 0:
            hour_list = hour.split(';')
            for h in hour_list:
                if not is_hour(h.strip()):
                    df.loc[index, 'value'] = style_hour(h)
        else:
            if not is_hour(hour):
                df.loc[index, 'value'] = style_hour(hour)
    
    wrong_index, wrong_hour = find_mess_hour(df)
    
    df.drop(wrong_index, inplace=True)
    
    return wrong_hour

              
              

#---------- 清洗门牌号码 -------------
    
def process_house_number(df):
    '''清洗数据中的门牌号码。
    如果housenumber字段中不包含数字，则认为是错误的门牌，会被丢弃。'''

    wrong_index = []
    wrong_list = []
    for index, row in df[df.key=='housenumber'].iterrows():
        house = row['value']
        if not re.search('\d', house):  # 判断是否包含数字
            wrong_index.append(index)
            wrong_list.append(house)
    
    df.drop(wrong_index, inplace=True)   # 删除数据中错误的门牌号码
    
    return wrong_list
    
    

#--------------- 补充缺失的name属性值 -----------------

def process_name(df):
    '''当同一id下，存在zh属性却不存在name属性时， 增加name属性值，其值等同于zh的值。'''

    groups = df.groupby('id')   # 根据id将数据分组
    
    for iid, group in groups:
        if (not (group.key=='name').any()) and (group.key=='zh').any():
            name = group.loc[group.key=='zh', 'value']
            new_row = pd.DataFrame({'id': iid, 'key': 'name', 'value':name, 'type': 'regular'})
            df = df.append(new_row, ignore_index=True)
    
    return df
    