# 对post缩略信息进行填充
import pymongo
import ast
# import yaml
import ruamel.yaml
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedSeq
from collections import OrderedDict
# yapi mongodb地址
host = "10.161.66.55"
port = 27017

# 修正yapi(enum)和swagger(example)的错位
def check_properties(properties):
    for key, value in properties.items():
        if(properties[key]["type"]=="object"):
            check_properties(properties[key]["properties"])
        elif(properties[key]["type"]=="array"):
            print(key+"array类型")
            check_properties(properties[key]["items"]["properties"])
        else:
            # 处理enum
            # print(properties[key]["enum"])
            try:
                properties[key]["example"] = properties[key]["enum"][0]
            except:
                print("接口信息中"+key+"字段没有设置枚举信息，生成代码的时候没有example")

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
    for item in interface.find({"_id":93,"project_id":9}):
        with open('post.yaml', 'r',encoding='utf-8') as loadfile:
            dataMap = yaml.load(loadfile)
            dataMap["info"]["title"] = item["path"].replace("/",'_').strip('_')
            # 这个字段需要上线后定
            dataMap["host"] = 'locahost:8080'
            dataMap["paths"]["to_fill_in"]["post"]["tags"] = [item["path"].replace("/",'-').strip('-')+"-controller"]
            dataMap["paths"]["to_fill_in"]["post"]["summary"] = item["title"]
            dataMap["paths"]["to_fill_in"]["post"]["description"] = item["desc"]
            # 这个参数是对req的总述，在yapi里没有地写
            dataMap["paths"]["to_fill_in"]["post"]["parameters"][0]["description"] = "request"
            # parameters
            # req的body部分
            if("req_body_other" in item):
                req = ast.literal_eval(item["req_body_other"])
                if ('$$ref' in req.keys()):
                    req.pop("$$ref")
                dataMap["definitions"]["ServiceRequest"] = req
                # print(req)
                check_properties(req["properties"])
            # req的query部分
            if("req_query" in item):
                # item["req_query"]是list
                yaml_str = """\
                name: to_fill_in
                in: query
                description: to_fill_in
                required: true
                type: string
                example: True
                """
                for query_para in item["req_query"]:
                    # append内容应该是CommentedMap
                    y_temp = YAML()
                    data = y_temp.load(yaml_str)
                    # print(query_para['name'])
                    data['name'] =query_para['name']
                    data['description'] = query_para['desc']
                    data['example'] = query_para['example']
                    if query_para['required'] == 0:
                        data['required'] = False
                    else:
                        data['required'] = True
                    dataMap["paths"]["to_fill_in"]["post"]["parameters"].append(data)
            # response部分
            # string转换为dict
            resp = ast.literal_eval(item["res_body"])
            if ('$$ref' in resp.keys()):
                resp.pop("$$ref")
            print(resp)
            check_properties(resp["properties"])
            dataMap["definitions"]["ServiceResponse"] = resp

            # 替换path 的key值
            dict_temp = dataMap["paths"]
            dataMap["paths"][item["path"]] = dict_temp.pop("to_fill_in")

        # allow_unicode = True yaml对中文的处理
        with open('post_result.yaml','w+',encoding='utf8') as loadfile:
            yaml.dump(dataMap,loadfile)
generate_yml()