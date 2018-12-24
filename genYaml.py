import pymongo
import ast
import ruamel.yaml
from ruamel.yaml import YAML
import json
import sys
host = "39.105.158.218"
port = 27017
def file_output(dataMap,dir):
    yaml = ruamel.yaml.YAML()
    yaml.indent(mapping=4)
    yaml.preserve_quotes = True
    # allow_unicode = True yaml对中文的处理
    with open(dir+'/result.yaml', 'w+', encoding='utf8') as loadfile:
        yaml.dump(dataMap, loadfile)

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

def generate_yml(project_id,dir):
    # 连接数据库
    client = pymongo.MongoClient(host,port)
    yapi = client['yapi']
    interface = yapi['interface']
    interface_cat = yapi['interface_cat']
    yaml = ruamel.yaml.YAML()
    yaml.indent(mapping=4)
    yaml.preserve_quotes = True
    tags = """\
                name: to_fill_in
                description: to_fill_in
                """
    # 读入模板template.yaml
    with open("./template.yaml", 'r', encoding='utf-8') as loadfile:
        dataMap = yaml.load(loadfile)
        # title写服务名
        project = yapi['project']
        yaml = ruamel.yaml.YAML()
        yaml.indent(mapping=4)
        yaml.preserve_quotes = True
        for project in project.find({"_id": int(project_id)}):
            dataMap["info"]["title"] = project["name"]
        dataMap["host"] = 'locahost:8080'
        # 生成总的tags
        for item in interface_cat.find({"project_id": int(project_id)}):
            y_temp = YAML()
            data = y_temp.load(tags)
            data['name'] = item["name"]
            data['description'] = item["desc"]
            dataMap["tags"].append(data)

        # pop 掉模板数据和公共分类
        dataMap["tags"].pop(0)
        dataMap["tags"].pop(0)

        count = 1
        # 遍历服务下的所有接口
        for item in interface.find({"project_id": int(project_id)}):
            # paths
            with open("./paths.yaml", 'r', encoding='utf-8') as loadfile:
                dataMap_paths = yaml.load(loadfile)
                if (("method" in item)):
                    type = item["method"]
                    # type后面的结构接到get put(type)后面去
                    dataMap_paths[type] = dataMap_paths.pop("type")
                    # parameters 里的in: body  当方法为get或者 请求类型为formdata这个参数是没有的（并且definations里也应该删掉）
                    if(type =="GET" or item["req_body_type"] == "form" ):
                        dataMap_paths[type]["parameters"].pop(0)
                        # definitions引用对象ServiceRequest不写入
                    else:
                        dataMap_paths[type]["parameters"][0]["schema"]["$ref"] = dataMap_paths[type]["parameters"][0]["schema"]["$ref"]+str(count)
                    # response 任何时候都存在
                    dataMap_paths[type]["responses"]['200']["schema"]["$ref"] = dataMap_paths[type]["responses"]['200']["schema"]["$ref"]+str(count)

                    # ----通用部分-----
                    # 指定tags
                    for item_cat in interface_cat.find({"_id": item["catid"]}):
                        dataMap_paths[type]["tags"] = item_cat["name"]

                    # 指定summary
                    dataMap_paths[type]["summary"] = item["title"]

                    # 指定description
                    if "desc" in item:
                        dataMap_paths[type]["description"] = item["desc"]
                    print(item["req_body_type"])

                    yaml_str = """\
                        name: to_fill_in
                        in: query
                        description: to_fill_in
                        required: true
                        type: string
                        example: True
                        """

                    # req_body_type
                    if (item["req_body_type"] == "form"):
                        # consumes参数要修改，防止codegen不识别
                        dataMap_paths[type]["consumes"] = ["application/x-www-form-urlencoded"]
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
                            dataMap_paths[type]["parameters"].append(data)
                    if (item["req_body_type"] == "json" and "req_body_other" in item):
                        req = json.loads(item["req_body_other"])
                        if ('$$ref' in req.keys()):
                            req.pop("$$ref")
                        check_enum(req["properties"])
                        # definitions 里的serviceRequest
                        dataMap["definitions"].insert(1,"ServiceRequest"+str(count),req,comment="request类")
                    if ("req_query" in item):
                        # item["req_query"]是list
                        for query_para in item["req_query"]:
                            # append内容应该是CommentedMap
                            y_temp = YAML()
                            data = y_temp.load(yaml_str)
                            # print(query_para['name'])
                            data['name'] = query_para['name']
                            data['description'] = query_para['desc']
                            if ("example" in query_para):
                                data['example'] = query_para['example']
                            if query_para['required'] == 0:
                                data['required'] = False
                            else:
                                data['required'] = True
                            dataMap_paths[type]["parameters"].append(data)
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
                            dataMap_paths[type]["parameters"].append(data)
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
                            dataMap_paths[type]["parameters"].append(data)
                    # definitions 里的response
                    resp = ""
                    if("res_body" in item):
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
                            dataMap["definitions"].insert(1, "ServiceResponse" + str(count), resp, comment="response")






                    # paths下层的url最后赋值 url相同方法不同的处理逻辑
                    if(item["path"] in dataMap["paths"]):
                        dataMap["paths"][item["path"]].insert(1,type,dataMap_paths.get(type),comment=item["title"])
                        # 直接构造paths.yaml的内容，追加到url后面
                    else:
                        dataMap["paths"].insert(count, item["path"], dataMap_paths, comment=item["title"])
                    count= count +1
        file_output(dataMap, dir)
        # 生成definations

    #     if (("method" in item) and item["method"] == "POST"):
    #         print("-------POST类接口生成yml-------")
    #     elif(("method"in item) and item["method"]=="GET"):
    #         print("-------GET类接口生成yml-------")
    #     elif(("method"in item) and item["method"]=="PUT"):
    #         print("-------PUT类接口生成yml-------")
    #     elif (("method" in item) and item["method"] == "DELETE"):
    #         print("-------DELETE类接口生成yml-------")
    #     else:
    #         print("未知请求类型，请检查")

def main():
    if (len(sys.argv) >= 2):
        generate_yml(sys.argv[1],sys.argv[2])
    else:
        print("运行示例：python genYaml.py 5 .,第一个参数为project_id 第二个参数为生成yaml文件的路径")
if __name__ == '__main__':
    main()