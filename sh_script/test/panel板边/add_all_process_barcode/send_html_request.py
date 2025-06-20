#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = "luthersy"
__date__    = "20230401"
__version__ = "Revision: 1.0.0 "
__credits__ = u"""发送网页请求 """

import requests
import json


def post_message(**kwargs): 
    #url="http://172.20.218.42:8080/api/dataportal/invoke" #测试环境
    url="http://172.20.217.246:89/api/dataportal/invoke"
    headers = {'Content-Type': 'application/json'}
       
    jsondata = {
    "ApiType": "CodePrintController",
    "Parameters": [
        {
            "Value": {
                "ItemNo": kwargs["jobname"],
                "Layer": kwargs["layer"],
                "Inner": {
                    "SiteX": kwargs.get("inner_x", ""),
                    "SiteY": kwargs.get("inner_y", "")
                },
                "InnerL2L3": {
                    "SiteX": kwargs.get("innerl2l3_x", ""),
                    "SiteY": kwargs.get("innerl2l3_y", "")
                },
                "Out": {
                    "SiteX": kwargs.get("out_x", ""),
                    "SiteY": kwargs.get("out_y", "")
                }
            }
        }
    ],
    "Method": "SaveEngineerPnlCoordinate"
    }   
    
    responsere=requests.post(url=url, headers=headers,data=json.dumps(jsondata))
    # print "-------->", responsere.json()
    if not responsere.json()['Success']:        
        return u'内层追溯码坐标信息上传失败!请知悉！{0}'.format(responsere.json())
    
    return 0