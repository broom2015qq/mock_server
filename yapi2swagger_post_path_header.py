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
def check_enum(cur_body):
    if("properties" in cur_body):
        print("本层有properties")
        check_enum(cur_body["properties"])
    else:
        if("type" in cur_body):
            if(cur_body["type"] == "object"):
                check_enum(cur_body["properties"])
            elif(cur_body["type"] == "array"):
                check_enum(cur_body["items"])
        else:
            # 本层没有type，该到具体业务逻辑了
            for key, value in cur_body.items():
                if("type" in cur_body[key]):
                    if(cur_body[key]["type"]=="object"):
                        check_enum(cur_body[key]["properties"])
                    elif(cur_body[key]["type"]=="array"):
                        check_enum(cur_body[key]["items"])
                    elif(cur_body[key]["type"]=="string"):
                        # 处理enum
                        # print(cur_body[key]["enum"])
                        try:
                            cur_body[key]["example"] = cur_body[key]["enum"][0]
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
    for item in interface.find({"_id":141,"project_id":106}):
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
            yaml_str = """\
            name: to_fill_in
            in: query
            description: to_fill_in
            required: true
            type: string
            example: True
            """
            # req的body部分
            if("req_body_other" in item):
                req = ast.literal_eval(item["req_body_other"])
                if ('$$ref' in req.keys()):
                    req.pop("$$ref")
                dataMap["definitions"]["ServiceRequest"] = req
                check_enum(req["properties"])
            # req的query部分
            if("req_query" in item):
                # item["req_query"]是list
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
            # req的path部分
            if("req_params" in item):
                for query_para in item["req_params"]:
                    # append内容应该是CommentedMap
                    y_temp = YAML()
                    data = y_temp.load(yaml_str)
                    data['name'] =query_para['name']
                    data['description'] = query_para['desc']
                    data['example'] = query_para['example']
                    data['required'] = True
                    dataMap["paths"]["to_fill_in"]["post"]["parameters"].append(data)
                # header部分
                for query_para in item["req_headers"]:
                    y_temp = YAML()
                    data = y_temp.load(yaml_str)
                    data['name'] =query_para['name']
                    data['in'] = "header"
                    if("desc" in query_para):
                        data['description'] = query_para['desc']
                    if ("example" in query_para):
                        data['example'] = query_para['example']
                    data['required'] = True
                    dataMap["paths"]["to_fill_in"]["post"]["parameters"].append(data)

            # response部分
            # string转换为dict
            resp = ast.literal_eval(item["res_body"])
            if ('$$ref' in resp.keys()):
                resp.pop("$$ref")
            # print(resp)
            #     check_enum(resp["properties"])
            dataMap["definitions"]["ServiceResponse"] = resp

            # 替换path 的key值
            dict_temp = dataMap["paths"]
            dataMap["paths"][item["path"]] = dict_temp.pop("to_fill_in")

        # allow_unicode = True yaml对中文的处理
        with open('post_result.yaml','w+',encoding='utf8') as loadfile:
            yaml.dump(dataMap,loadfile)
generate_yml()