#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Python 3.6

import re
import xml.etree.cElementTree as ET


sOSMFILE = 'sample_beijing_china.osm'
OSMFILE = 'beijing_china.osm'

       
#-------- 清洗电话号码 -----------       
       
def is_phone_standard(phone_number):
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
        

def update_phone_number(phone_value):
    '''清洗单个电话号码，将不符合标准格式的电话号码转换成标准格式，不能转换的返回空字符。
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
        styled_value = ''  # 如果不能标准化，则返回空字符串

    return styled_value



def update_phone(phone_value): 
    '''清洗单个或多个电话号码的情况'''
    
    phone_number = ''

    if len(phone_value) >= 17:   # 处理可能的多个电话号码的情况
        if phone_value.find('/') > 0:          
            phone_list = phone_value.split('/')
            phone_number = ';'.join(update_phone_number(x) for x in phone_list)
        elif phone_value.find(';') > 0:
            phone_list = phone_value.split(';')
            phone_number = ';'.join(update_phone_number(x) for x in phone_list)
        elif phone_value.find('；') > 0:
            phone_list = phone_value.split('；')
            phone_number = ';'.join(update_phone_number(x) for x in phone_list)        
        else:  
            phone_number = update_phone_number(phone_value)            
    else:  # 处理单个电话号码
        phone_number = update_phone_number(phone_value)

    if phone_number in [';', ';;', ';;;']:  # 如果多个号码均为空（不能被标准化），则返回空字符
        phone_number = ''
            
    return phone_number
     



def audit_phone(filename):
    '''审查文件中的电话号码是否符合标准，返回不符合标准的号码'''
    
    osm_file = open(filename, 'r')
    wrong_numbers = []   # 记录不符合标准的号码
    
    for event, elem in ET.iterparse(osm_file):
    
        if  elem.tag == 'tag':   # 获取tag的元素
            if elem.attrib['k'] in ['phone', 'contact:phone']:
                phone_number = elem.attrib['v']
                if not is_phone_standard(phone_number):  # 判断是否符合标准
                    wrong_numbers.append(phone_number)

    return wrong_numbers





#--------- 清洗邮政编码 ---------------  


def is_postcode(code):
    '''判断是否符合北京邮政编码格式，是返回True，不是返回False。'''

    # 定义邮编的正则表达式，北京地区邮编以100、101、102开头，共6位数字
    postcode_parttern = r'^10[0-2]\d{3}$'
    
    return re.fullmatch(postcode_parttern, code)
    
    
    
    
def update_postcode(code):
    '''清洗邮编数据，如果符合标准，原样返回；如果不符合标准，则返回空字符。'''
    
    new_code = code
    if not is_postcode(code):
        new_code = ''
    
    return new_code    
    
    
    
    
def audit_postcode(filename):
    '''审查数据中的邮政编码，返回值是错误的邮编。'''

    wrong_list = []
    osm_file = open(filename, 'r')
    
    for event, elem in ET.iterparse(osm_file):
        if  elem.tag == 'tag':   # 获取tag的元素
            if elem.attrib['k'] == 'addr:postcode':
                code =  elem.attrib['v']
                if not is_postcode(code):  # 是否符合邮编格式
                    wrong_list.append(code)
    
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




def update_hour(hour):
    '''清洗营业时间数据，将之统一成标准格式。'''
    
    if hour.find(';') > 0: #处理用分号分隔的时间数据
        hour_list = hour.split(';')
        new_hour = ';'.join(style_hour(h) for h in hour_list)
        
    else:
        new_hour = style_hour(hour)
        if not is_hour(new_hour):
            new_hour = ''
    
    return new_hour
    
    
def audit_hour(filename):
    '''审查营业时间数据，返回不符合标准格式的数据。'''
    
    osm_file = open(filename, 'r')
    wrong_list = []   # 记录不符合标准的数据
    
    for event, elem in ET.iterparse(osm_file):
    
        if  elem.tag == 'tag':   # 获取tag的元素
            if elem.attrib['k'] == 'opening_hours':
                hour = elem.attrib['v']
                
                if hour.find(';') > 0: #处理用分号分隔的时间数据
                    hour_list = hour.split(';')
                    for h in hour_list:
                        if not is_hour(h.strip()):
                            wrong_list.append(h)
                else:               
                    if not is_hour(hour):  # 判断是否符合标准
                        wrong_list.append(hour)

    return wrong_list

              
              
 
 
 
 
 
 
#---------- 清洗门牌号码 -------------

def is_house_number(value):
    '''如果输入值不包含数字，则认为是不正确的门牌，返回False；否则返回True。'''
    
    return re.search('\d', value)  # 是否包含数字
        



def update_house_number(value):
    '''清洗门牌数据，如果不包含数字则返回空字符，否则原样返回。'''

    house_number = value
    if not is_house_number(value): 
        house_number = ''
        
    return house_number


     
def audit_house_number(filename):
    '''审查数据中的门牌号，返回值是错误的门牌号。'''

    wrong_list = []
    osm_file = open(filename, 'r')
    
    for event, elem in ET.iterparse(osm_file):
        if  elem.tag == 'tag':   # 获取tag的元素
            if elem.attrib['k'] == 'addr:housenumber':
                value =  elem.attrib['v']
                if not is_house_number(value):  
                    wrong_list.append(value)
    
    return wrong_list
 
 

# ----------- 整体清洗 ----------


def update_value(key, value):
    if key == 'phone':
        return update_phone(value)
    elif key == 'postcode':
        return update_postcode(value)
    elif key == 'housenumber':
        return update_house_number(value)
    elif key == 'opening_hours':
        return update_hour(value)
    else:
        return value

