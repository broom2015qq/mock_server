# 对post缩略信息进行填充
import pymongo
import ast
# import yaml
import ruamel.yaml

from collections import OrderedDict
# yapi mongodb地址
host = "10.161.66.55"
port = 27017

# 修正yapi(enum)和swagger(example)的错位
def check_properties(properties):
    for key, value in properties.items():
        if(properties[key]["type"]=="object"):
            check_properties(properties[key]["properties"])
        else:
            # 处理enum
            # print(properties[key]["enum"])
            properties[key]["example"] = properties[key]["enum"][0]
# 生成yaml文件
def generate_yml():
    # 连接数据库
    client = pymongo.MongoClient(host,port)
    yapi = client['yapi']
    interface = yapi['interface']
    # 此处固定一个接口
    # yapi录入
    yaml = ruamel.yaml.YAML()
    yaml.indent(mapping=4)
    yaml.preserve_quotes = True
    for item in interface.find({"_id":9,"project_id":106}):
    # yapi录入
    # for item in interface.find({"_id":33,"project_id":106}):
        # if("_id" in item):
        #   print(item["_id"])
        with open('post.yaml', 'r',encoding='utf-8') as loadfile:
            dataMap = yaml.load(loadfile)
            print(dataMap['info'])

            dataMap["info"]["title"] = item["path"].replace("/",'_').strip('_')
            # 待定
            dataMap["host"] = '10.161.67.230:14707'
            # controller的类名，传参进来？
            dataMap["paths"]["to_fill_in"]["post"]["tags"] = [item["path"].replace("/",'-').strip('-')+"-controller"]
            dataMap["paths"]["to_fill_in"]["post"]["summary"] = item["title"]
            dataMap["paths"]["to_fill_in"]["post"]["description"] = item["desc"]
            # 这固定了
            dataMap["paths"]["to_fill_in"]["post"]["parameters"][0]["description"] = "入参，PROVINCE_CODE必需，其他参数有3种组合：TRADE_ID 或 USER_ID 或 NET_TYPE_CODE+SERIAL_NUMBER"
            # 替换path 的key值
            # print(dataMap["paths"]["to_fill_in"])
            dict_temp = dataMap["paths"]
            dataMap["paths"][item["path"]] = dict_temp.pop("to_fill_in")
            # string转换为dict
            resp = ast.literal_eval(item["res_body"])
            if ('$$ref' in resp.keys()):
                resp.pop("$$ref")
            check_properties(resp["properties"])
            dataMap["definitions"]["ServiceResponse"] = resp
            req = ast.literal_eval(item["req_body_other"])
            if ('$$ref' in req.keys()):
                req.pop("$$ref")
            dataMap["definitions"]["ServiceRequest"] = req
            check_properties(req["properties"])

        # allow_unicode = True yaml对中文的处理
        with open('post_result.yaml','w+',encoding='utf8') as loadfile:
            print(dataMap)
            yaml.dump(dataMap,loadfile)
generate_yml()