# # 外部传参
# import sys
# import types
# if(len(sys.argv)>=2):
#     print(sys.argv[1])
#     print(sys.argv[2])
# else:
#     print('\033[1;31mpython yapi2swagger.py 后面请接一个参数(controller的类名) \n例:python yapi2swagger.py crm-trade-info-controller \033[0m')
#
# a = {"yuntian": "zero", "Alex": "Li"}
# a.update(Yuntian=a.pop("yuntian"))
# print(a)
#
# import ast
# # string转换为dict
# s = '{"host":"192.168.11.22", "port":3306, "user":"abc",\
#       "passwd":"123", "db":"mydb", "connect_timeout":10}'
# d = ast.literal_eval(s)
# print(type(d))
# print(d)
#
#
#
#
#
# def get_target_value(key, dic, tmp_list):
#     """
#     :param key: 目标key值
#     :param dic: JSON数据
#     :param tmp_list: 用于存储获取的数据
#     :return: list
#     """
#     if not isinstance(dic, dict) or not isinstance(tmp_list, list):  # 对传入数据进行格式校验
#         return 'argv[1] not an dict or argv[-1] not an list '
#
#     if key in dic.keys():
#         tmp_list.append(dic[key])  # 传入数据存在则存入tmp_list
#     else:
#         for value in dic.values():  # 传入数据不符合则对其value值进行遍历
#             if isinstance(value, dict):
#                 get_target_value(key, value, tmp_list)  # 传入数据的value值是字典，则直接调用自身
#             elif isinstance(value, (list, tuple)):
#                 _get_value(key, value, tmp_list)  # 传入数据的value值是列表或者元组，则调用_get_value
#     return tmp_list
#
#
# def _get_value(key, val, tmp_list):
#     for val_ in val:
#         if isinstance(val_, dict):
#             get_target_value(key, val_, tmp_list)  # 传入数据的value值是字典，则调用get_target_value
#         elif isinstance(val_, (list, tuple)):
#             _get_value(key, val_, tmp_list)   # 传入数据的value值是列表或者元组，则调用自身
#
#
# d = {'a':1,'b':2,'c':3}
# print(isinstance(d,dict))
#
# # 按键值倾倒dict
# import ruamel.yaml
#
# yaml = ruamel.yaml.YAML()
# yaml.indent(mapping=4)
# yaml.preserve_quotes = True
# with open("post_test.yaml", "r",encoding="utf-8") as docs:
# # with open("人资.yaml", "r", encoding="utf-8") as docs:
#     try:
#         alldata = yaml.load(docs)
#     except ruamel.yaml.YAMLError as exc:
#         print(exc)
#
# #修改
# alldata['host']='--------------'
# with open('post1.yaml', 'w+', encoding='utf8') as outfile:
# # with open('人资1.yaml', 'w+', encoding='utf8') as outfile:
#     yaml.dump(alldata, outfile)
#
# import ruamel.yaml
# from ruamel.yaml.comments import CommentedSeq
#
# d = {}
# for m in ['B1', 'B2', 'B3']:
#     d2 = {}
#     for f in ['A1', 'A2', 'A3']:
#         d2[f] = CommentedSeq(['test', 'test2'])
#         print(type(d2[f]))
#         if f != 'A2':
#             d2[f].fa.set_flow_style()
#     d[m] = d2
#
#     with open('test.yml', "w") as f:
#         f.write('# Data for Class A\n')
#         ruamel.yaml.dump(
#             d, f, Dumper=ruamel.yaml.RoundTripDumper,
#             default_flow_style=False, width=50, indent=8)
#
#     import sys
#     from ruamel.yaml import YAML
#
#     yaml_str = """\
#     first_name: Art
#     occupation: Architect  # This is an occupation comment
#     about: Art Vandelay is a fictional character that George invents...
#     """
#
#     yaml = YAML()
#     data = yaml.load(yaml_str)
#     data.insert(1, 'last name', 'Vandelay', comment="new key")
#     yaml.dump(data, sys.stdout)

import sys
from ruamel.yaml import YAML

yaml_str = """\
first_name: Art
occupation: Architect  # This is an occupation comment
about: Art Vandelay is a fictional character that George invents...
"""

yaml = YAML()
data = yaml.load(yaml_str)


# data.insert(1, 'last name', 'Vandelay', comment="new key")
# if('last name' in data):
#     print("---------")
#     print(data.pop('last name'))
#     print("---------")
#
# yaml.dump(data, sys.stdout)
import gitlab
# 登录
url = 'http://xxxxxxx'
token = 'xxxxxxxxxxxxxx'
gl = gitlab.Gitlab(url, token)
gl.user
