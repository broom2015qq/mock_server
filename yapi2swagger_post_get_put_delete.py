# 对post缩略信息进行填充
import pymongo
import ast
import ruamel.yaml
from ruamel.yaml import YAML
import json
import sys
from ruamel.yaml.comments import CommentedSeq
from collections import OrderedDict
# yapi mongodb地址
host = "39.105.158.218"
port = 27017
def file_output(dataMap,dir):
    yaml = ruamel.yaml.YAML()
    yaml.indent(mapping=4)
    yaml.preserve_quotes = True
    # allow_unicode = True yaml对中文的处理
    with open(dir+'/result.yaml', 'w+', encoding='utf8') as loadfile:
        yaml.dump(dataMap, loadfile)
# 修正yapi(enum)和swagger(example)的错位
def check_enum(cur_body):
    if("properties" in cur_body):
        # print("本层有properties")
        check_enum(cur_body["properties"])
    else:
        if("type" in cur_body):
            if(cur_body["type"] == "object"):
                check_enum(cur_body["properties"])
            elif(cur_body["type"] == "array"):
                check_enum(cur_body["items"])
            elif(cur_body["type"] == "string"):
                cur_body["example"] = cur_body["enum"][0]
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
def generate_top(item,type):
    client = pymongo.MongoClient(host, port)
    yapi = client['yapi']
    yaml = ruamel.yaml.YAML()
    yaml.indent(mapping=4)
    yaml.preserve_quotes = True
    file_name = type+".yaml"
    with open(file_name, 'r', encoding='utf-8') as loadfile:
        print(item)
        dataMap = yaml.load(loadfile)
        # title写服务名
        project = yapi['project']
        yaml = ruamel.yaml.YAML()
        yaml.indent(mapping=4)
        yaml.preserve_quotes = True
        print(item["project_id"])
        for project in project.find({"_id": item["project_id"]}):
            dataMap["info"]["title"] = project["name"]
        # dataMap["info"]["title"] = item["path"].replace("/", '_').strip('_')
        # 这个字段需要上线后定
        dataMap["host"] = 'locahost:8080'
        # tags应该写yapi的分类信息
        dataMap["paths"]["to_fill_in"][type]["summary"] = item["title"]
        # 这个字段可能没有
        if "desc" in item:
            dataMap["paths"]["to_fill_in"][type]["description"] = item["desc"]
        # 生成服务总述
        interface_cat = yapi['interface_cat']
        yaml = ruamel.yaml.YAML()
        yaml.indent(mapping=4)
        yaml.preserve_quotes = True
        for item_cat in interface_cat.find({"_id": item["catid"]}):
            dataMap["tags"][0]["name"] = item_cat["name"]
            dataMap["tags"][0]["description"] = item_cat["desc"]
            dataMap["paths"]["to_fill_in"][type]["tags"] = item_cat["name"]
        return dataMap

def generate_post_yml(item,dir):
    print("生成post类型的yml文件")
    dataMap = generate_top(item,"post")
    # 这个参数是对req的总述，在yapi里没有地写
    # parameters
    yaml_str = """\
    name: to_fill_in
    in: query
    description: to_fill_in
    required: true
    type: string
    example: True
    """
    # 一种formdata最少量的post请求类型,req_body_type有form 还有json
    # 这个参数是form时候，就不需要构造'#/definitions/ServiceRequest,parameters这一项也可以没有了
    if (item["req_body_type"] == "form"):
        # consumes参数要修改，防止codegen不识别
        dataMap["consumes"] = ["application/x-www-form-urlencoded"]
        for query_para in item["req_body_form"]:
            # append内容应该是CommentedMap
            y_temp = YAML()
            data = y_temp.load(yaml_str)
            data['name'] = query_para['name']
            data['in'] = "formData"
            data['description'] = query_para['desc']
            if("example" in data):
                data['example'] = query_para['example']
            if query_para['required'] == 0:
                data['required'] = False
            else:
                data['required'] = True
            dataMap["paths"]["to_fill_in"]["post"]["parameters"].append(data)
            # 这里删除 #/definitions/ServiceRequest 是第0个，因为后面是append的
            dataMap["paths"]["to_fill_in"]["post"]["parameters"].pop(0)
            # 再删除definitions引用对象ServiceRequest
            dataMap["definitions"].pop("ServiceRequest")
    # req的body部分
    if ("req_body_other" in item):
        # req = ast.literal_eval(item["req_body_other"])
        req = json.loads(item["req_body_other"])
        if ('$$ref' in req.keys()):
            req.pop("$$ref")
        dataMap["definitions"]["ServiceRequest"] = req
        check_enum(req["properties"])
    # req的query部分
    if ("req_query" in item):
        # item["req_query"]是list
        for query_para in item["req_query"]:
            # append内容应该是CommentedMap
            y_temp = YAML()
            data = y_temp.load(yaml_str)
            # print(query_para['name'])
            data['name'] = query_para['name']
            data['description'] = query_para['desc']
            data['example'] = query_para['example']
            if query_para['required'] == 0:
                data['required'] = False
            else:
                data['required'] = True
            dataMap["paths"]["to_fill_in"]["post"]["parameters"].append(data)
    # req的path部分
    if ("req_params" in item and item["req_params"] != []):
        for query_para in item["req_params"]:
            # append内容应该是CommentedMap
            y_temp = YAML()
            data = y_temp.load(yaml_str)
            data['name'] = query_para['name']
            data['in'] = 'path'
            data['description'] = query_para['desc']
            data['example'] = query_para['example']
            data['required'] = True
            dataMap["paths"]["to_fill_in"]["post"]["parameters"].append(data)
        # header部分，判断是否有header
        for query_para in item["req_headers"]:
            y_temp = YAML()
            data = y_temp.load(yaml_str)
            data['name'] = query_para['name']
            data['in'] = "header"
            if ("desc" in query_para):
                data['description'] = query_para['desc']
            if ("example" in query_para):
                data['example'] = query_para['example']
            data['required'] = True
            dataMap["paths"]["to_fill_in"]["post"]["parameters"].append(data)

    # response部分
    # string转换为dict
    # resp = ast.literal_eval(item["res_body"])
    resp = json.loads(item["res_body"])
    if ('$$ref' in resp.keys()):
        resp.pop("$$ref")
    if("properties" in resp):
        check_enum(resp["properties"])
    else:
        check_enum(resp)
    dataMap["definitions"]["ServiceResponse"] = resp

    # 替换path 的key值
    dict_temp = dataMap["paths"]
    dataMap["paths"][item["path"]] = dict_temp.pop("to_fill_in")
    yaml = ruamel.yaml.YAML()
    yaml.indent(mapping=4)
    yaml.preserve_quotes = True
    # allow_unicode = True yaml对中文的处理
    # with open('result/result.yaml', 'w+', encoding='utf8') as loadfile:
    #     yaml.dump(dataMap, loadfile)
    file_output(dataMap,dir)
def generate_get_yml(item,dir):
    print("生成get类型的yml文件")
    dataMap = generate_top(item,"get")
    # parameters
    yaml_str = """\
        name: to_fill_in
        in: query
        description: to_fill_in
        required: true
        type: string
        example: True
        """
    # req的query部分
    if ("req_query" in item):
        # item["req_query"]是list
        for query_para in item["req_query"]:
            # append内容应该是CommentedMap
            y_temp = YAML()
            data = y_temp.load(yaml_str)
            # print(query_para['name'])
            data['name'] = query_para['name']
            data['description'] = query_para['desc']
            if("example" in query_para):
                data['example'] = query_para['example']
            if query_para['required'] == 0:
                data['required'] = False
            else:
                data['required'] = True
            dataMap["paths"]["to_fill_in"]["get"]["parameters"].append(data)
        dataMap["paths"]["to_fill_in"]["get"]["parameters"].pop(0)
    # req的path部分
    if ("req_params" in item and item["req_params"] != []):
        for query_para in item["req_params"]:
            # append内容应该是CommentedMap
            y_temp = YAML()
            data = y_temp.load(yaml_str)
            data['name'] = query_para['name']
            data['in'] = 'path'
            data['description'] = query_para['desc']
            if("example" in query_para):
                data['example'] = query_para['example']
            data['required'] = True
            dataMap["paths"]["to_fill_in"]["get"]["parameters"].append(data)
        # header部分，判断是否有header
        if("req_headers" in item and item["req_headers"] !=[]):
            for query_para in item["req_headers"]:
                y_temp = YAML()
                data = y_temp.load(yaml_str)
                data['name'] = query_para['name']
                data['in'] = "header"
                if ("desc" in query_para):
                    data['description'] = query_para['desc']
                if ("example" in query_para):
                    data['example'] = query_para['example']
                data['required'] = True
                dataMap["paths"]["to_fill_in"]["get"]["parameters"].append(data)

    # response部分
    # string转换为dict
    # resp = ast.literal_eval(item["res_body"])
    resp = json.loads(item["res_body"])
    if ('$$ref' in resp.keys()):
        resp.pop("$$ref")
    print("--------resp-----------")
    print(resp)
    if ("properties" in resp):
        check_enum(resp["properties"])
    else:
        check_enum(resp)
    dataMap["definitions"]["ServiceResponse"] = resp

    # 替换path 的key值
    dict_temp = dataMap["paths"]
    dataMap["paths"][item["path"]] = dict_temp.pop("to_fill_in")
    yaml = ruamel.yaml.YAML()
    yaml.indent(mapping=4)
    yaml.preserve_quotes = True
    # allow_unicode = True yaml对中文的处理
    # with open('result/result.yaml', 'w+', encoding='utf8') as loadfile:
    #     yaml.dump(dataMap, loadfile)
    file_output(dataMap, dir)
def generate_put_yml(item,dir):
    print("生成put类型的yml文件")
    dataMap = generate_top(item, "put")
    # 这个参数是对req的总述，在yapi里没有地写
    # parameters
    yaml_str = """\
        name: to_fill_in
        in: query
        description: to_fill_in
        required: true
        type: string
        example: True
        """
    # 一种formdata最少量的post请求类型,req_body_type有form 还有json
    # 这个参数是form时候，就不需要构造'#/definitions/ServiceRequest,parameters这一项也可以没有了
    if (item["req_body_type"] == "form"):
        # consumes参数要修改，防止codegen不识别
        dataMap["consumes"] = ["application/x-www-form-urlencoded"]
        for query_para in item["req_body_form"]:
            # append内容应该是CommentedMap
            y_temp = YAML()
            data = y_temp.load(yaml_str)
            data['name'] = query_para['name']
            data['in'] = "formData"
            data['description'] = query_para['desc']
            if ("example" in data):
                data['example'] = query_para['example']
            if query_para['required'] == 0:
                data['required'] = False
            else:
                data['required'] = True
            dataMap["paths"]["to_fill_in"]["put"]["parameters"].append(data)
            # 这里删除 #/definitions/ServiceRequest 是第0个，因为后面是append的
            dataMap["paths"]["to_fill_in"]["put"]["parameters"].pop(0)
            # 再删除definitions引用对象ServiceRequest
            dataMap["definitions"].pop("ServiceRequest")
    # req的body部分
    if ("req_body_other" in item):
        # req = ast.literal_eval(item["req_body_other"])
        req = json.loads(item["req_body_other"])
        if ('$$ref' in req.keys()):
            req.pop("$$ref")
        dataMap["definitions"]["ServiceRequest"] = req
        check_enum(req["properties"])
    # req的query部分
    if ("req_query" in item):
        # item["req_query"]是list
        for query_para in item["req_query"]:
            # append内容应该是CommentedMap
            y_temp = YAML()
            data = y_temp.load(yaml_str)
            # print(query_para['name'])
            data['name'] = query_para['name']
            data['description'] = query_para['desc']
            data['example'] = query_para['example']
            if query_para['required'] == 0:
                data['required'] = False
            else:
                data['required'] = True
            dataMap["paths"]["to_fill_in"]["post"]["parameters"].append(data)
    # req的path部分
    if ("req_params" in item and item["req_params"] != []):
        for query_para in item["req_params"]:
            # append内容应该是CommentedMap
            y_temp = YAML()
            data = y_temp.load(yaml_str)
            data['name'] = query_para['name']
            data['in'] = 'path'
            data['description'] = query_para['desc']
            if("example" in query_para):
                data['example'] = query_para['example']
            data['required'] = True
            dataMap["paths"]["to_fill_in"]["put"]["parameters"].append(data)
        # header部分，判断是否有header
        for query_para in item["req_headers"]:
            y_temp = YAML()
            data = y_temp.load(yaml_str)
            data['name'] = query_para['name']
            data['in'] = "header"
            if ("desc" in query_para):
                data['description'] = query_para['desc']
            if ("example" in query_para):
                data['example'] = query_para['example']
            data['required'] = True
            dataMap["paths"]["to_fill_in"]["put"]["parameters"].append(data)

    # response部分
    # string转换为dict
    # resp = ast.literal_eval(item["res_body"])
    resp =item["res_body"]
    try:
        resp = json.loads(item["res_body"])
    except:
        print("res_body不能解析为json格式")
    else:
        if ('$$ref' in resp.keys()):
            resp.pop("$$ref")
        if ("properties" in resp):
            check_enum(resp["properties"])
        else:
            check_enum(resp)
    finally:
        dataMap["definitions"]["ServiceResponse"] = resp





    # 替换path 的key值
    dict_temp = dataMap["paths"]
    dataMap["paths"][item["path"]] = dict_temp.pop("to_fill_in")
    yaml = ruamel.yaml.YAML()
    yaml.indent(mapping=4)
    yaml.preserve_quotes = True
    # allow_unicode = True yaml对中文的处理
    # with open('result/result.yaml', 'w+', encoding='utf8') as loadfile:
    #     yaml.dump(dataMap, loadfile)
    file_output(dataMap,dir)
def generate_delete_yml(item,dir):
    print("生成delete类型的yml文件")
    dataMap = generate_top(item, "delete")
    # 这个参数是对req的总述，在yapi里没有地写
    # parameters
    yaml_str = """\
        name: to_fill_in
        in: query
        description: to_fill_in
        required: true
        type: string
        example: True
        """
    # 一种formdata最少量的post请求类型,req_body_type有form 还有json
    # 这个参数是form时候，就不需要构造'#/definitions/ServiceRequest,parameters这一项也可以没有了
    if (item["req_body_type"] == "form"):
        # consumes参数要修改，防止codegen不识别
        dataMap["consumes"] = ["application/x-www-form-urlencoded"]
        for query_para in item["req_body_form"]:
            # append内容应该是CommentedMap
            y_temp = YAML()
            data = y_temp.load(yaml_str)
            data['name'] = query_para['name']
            data['in'] = "formData"
            data['description'] = query_para['desc']
            if ("example" in data):
                data['example'] = query_para['example']
            if query_para['required'] == 0:
                data['required'] = False
            else:
                data['required'] = True
            dataMap["paths"]["to_fill_in"]["put"]["parameters"].append(data)
            # 这里删除 #/definitions/ServiceRequest 是第0个，因为后面是append的
            dataMap["paths"]["to_fill_in"]["put"]["parameters"].pop(0)
            # 再删除definitions引用对象ServiceRequest
            dataMap["definitions"].pop("ServiceRequest")
    # req的body部分
    if ("req_body_other" in item):
        # req = ast.literal_eval(item["req_body_other"])
        req = json.loads(item["req_body_other"])
        if ('$$ref' in req.keys()):
            req.pop("$$ref")
        dataMap["definitions"]["ServiceRequest"] = req
        check_enum(req["properties"])
    # req的query部分
    if ("req_query" in item):
        # item["req_query"]是list
        for query_para in item["req_query"]:
            # append内容应该是CommentedMap
            y_temp = YAML()
            data = y_temp.load(yaml_str)
            # print(query_para['name'])
            data['name'] = query_para['name']
            data['description'] = query_para['desc']
            data['example'] = query_para['example']
            if query_para['required'] == 0:
                data['required'] = False
            else:
                data['required'] = True
            dataMap["paths"]["to_fill_in"]["delete"]["parameters"].append(data)
    # req的path部分
    if ("req_params" in item and item["req_params"] != []):
        for query_para in item["req_params"]:
            # append内容应该是CommentedMap
            y_temp = YAML()
            data = y_temp.load(yaml_str)
            data['name'] = query_para['name']
            data['in'] = 'path'
            data['description'] = query_para['desc']
            if("example" in query_para):
                data['example'] = query_para['example']
            data['required'] = True
            dataMap["paths"]["to_fill_in"]["delete"]["parameters"].append(data)
        # header部分，判断是否有header
        for query_para in item["req_headers"]:
            y_temp = YAML()
            data = y_temp.load(yaml_str)
            data['name'] = query_para['name']
            data['in'] = "header"
            if ("desc" in query_para):
                data['description'] = query_para['desc']
            if ("example" in query_para):
                data['example'] = query_para['example']
            data['required'] = True
            dataMap["paths"]["to_fill_in"]["delete"]["parameters"].append(data)

    # response部分
    # string转换为dict
    # resp = ast.literal_eval(item["res_body"])
    resp = json.loads(item["res_body"])
    if ('$$ref' in resp.keys()):
        resp.pop("$$ref")
    if ("properties" in resp):
        check_enum(resp["properties"])
    else:
        check_enum(resp)
    dataMap["definitions"]["ServiceResponse"] = resp

    # 替换path 的key值
    dict_temp = dataMap["paths"]
    dataMap["paths"][item["path"]] = dict_temp.pop("to_fill_in")
    yaml = ruamel.yaml.YAML()
    yaml.indent(mapping=4)
    yaml.preserve_quotes = True
    # allow_unicode = True yaml对中文的处理
    # with open('result/result.yaml', 'w+', encoding='utf8') as loadfile:
    #     yaml.dump(dataMap, loadfile)
    file_output(dataMap,dir)
def generate_yml(project_id,interface_id,dir):
    # 连接数据库
    client = pymongo.MongoClient(host,port)
    yapi = client['yapi']
    interface = yapi['interface']
    # 此处固定一个接口
    # yapi录入
    yaml = ruamel.yaml.YAML()
    yaml.indent(mapping=4)
    yaml.preserve_quotes = True
    # post类型接口
    # for item in interface.find({"_id": 6826, "project_id": 9243}):
    for item in interface.find({"_id": int(interface_id), "project_id": int(project_id)}):
    # post form-data类型接口
    # for item in interface.find({"_id":267,"project_id":9}):
    # get类型接口 path+query
    # for item in interface.find({"_id": 375, "project_id": 15}):
    # get类型接口 path+query+header
    # for item in interface.find({"_id": 399, "project_id": 15}):
    # put类接口
    # for item in interface.find({"_id": 1089, "project_id": 69}):
    # put类接口 body
    # for item in interface.find({"_id": 873, "project_id": 15}):
    # delete类接口
    # for item in interface.find({"_id": 1155, "project_id": 72}):
        # 判断请求类型
        print("-------item全部信息如下-------")
        # print(item)
        if(("method"in item) and item["method"]=="POST"):
            print("-------POST类接口生成yml-------")
            generate_post_yml(item,dir)
        elif(("method"in item) and item["method"]=="GET"):
            print("-------GET类接口生成yml-------")
            generate_get_yml(item,dir)
        elif(("method"in item) and item["method"]=="PUT"):
            print("-------PUT类接口生成yml-------")
            generate_put_yml(item,dir)
        elif (("method" in item) and item["method"] == "DELETE"):
            print("-------DELETE类接口生成yml-------")
            generate_delete_yml(item,dir)
        else:
            print("未知请求类型，请检查")
#
#
def main():
    if (len(sys.argv) >= 3):
        generate_yml(sys.argv[1],sys.argv[2],sys.argv[3])
    else:
        print("运行示例：python genYaml.py 5 12 .,第一个参数为project_id 第二个参数为interface_id 第三个参数为生成yaml文件的路径")
    # generate_yml(5,12,'./')

if __name__ == '__main__':
    main()
# generate_yml(11,20,'.')
# generate_yml(9224,6815,'.')