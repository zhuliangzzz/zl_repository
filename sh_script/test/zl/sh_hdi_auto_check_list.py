#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = "luthersy"
__date__    = "20230107"
__version__ = "Revision: 1.0.0 "
__credits__ = u"""胜宏HDI全自动检测程序 """

import os
import sys
if sys.platform == "win32":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package")
else:
    scriptPath = "%s/scripts" % os.environ.get('SCRIPTS_DIR', '/incam/server/site_data')
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")
    
import re
import pic
import json

from create_ui_model import showMessageInfo

try:            
    paramJson = json.loads(os.environ.get('PARAM').replace(';', ','))
    processID = int(paramJson['process_id'])
    jobID = int(paramJson['job_id'])
    user = paramJson['user']
    jobname = os.environ["JOB"]
except:
    # 手动测试用
    processID = -1
    jobID = -1
    user = "system"
    jobname = os.environ.get("JOB", "ha7712pf338f1-lyh")
    if os.environ.get("JOB", None) is None:
        os.environ["JOB"] = jobname
    
try:
    from TOPCAM_IKM import IKM
    ikm_fun = IKM()
except Exception, e:
    showMessageInfo(u"连接topcam数据库异常，请联系程序组处理:", str(e))
    sys.exit()
    
try:
    persona, inn_or_out = sys.argv[1:]
except:
    persona = "for_cam_maker"
    inn_or_out = "inner"
    
def set_check_function_name_from_erp(check_status="('normal')"):
    """先生成要检测的项目"""
    condition = u"{0} = '是' and check_inn_or_out in ('all','{1}')".format(persona, inn_or_out)
    sql = u"""select * from pdm_job_check_function_list
    where check_status in {1}
    and {0}
    order by id desc"""
    data_info = ikm_fun.PG.SELECT_DIC(ikm_fun.dbc_p, sql.format(condition, check_status))
    for info in sorted(data_info, key=lambda x: x["id"]):
        arraylist_keys = ['job_id', 'jobname', 'check_function_name',
                          'function_description', 'for_cam_maker',
                          'for_cam_director', 'check_user', 'check_status',
                          "check_inn_or_out", "script_path", "forbid_or_information",
                          "note"]
        insert_sql = "insert into pdm_job_check_log_list ({0}) values ({1})"
        dic_value = {}
        dic_value['job_id'] = jobID
        dic_value['jobname'] = jobname
        dic_value['check_user'] = user
        dic_value['check_status'] = 'normal'
        dic_value['inner_or_out'] = "({0})".format(inn_or_out) if info['check_inn_or_out'] == "all" else ""
        
        arraylist_values = ["'{%s}'" % x for x in arraylist_keys]
        for key, value in info.iteritems():
            if key in arraylist_keys:
                dic_value[key] = value
                
        dic_value['function_description'] = dic_value['function_description'] + dic_value['inner_or_out']
                
        sql = """select * from pdm_job_check_log_list where check_user = '{check_user}'
        and check_function_name = '{check_function_name}'
        and function_description = '{function_description}'
        and jobname = '{jobname}'
        and check_status ='{check_status}'"""
        data_info = ikm_fun.PG.SELECT_DIC(ikm_fun.dbc_p, sql.format(**dic_value))
        # print sql.format(**dic_value)
        if not data_info:
            ikm_fun.PG.SQL_EXECUTE(ikm_fun.dbc_p, insert_sql.format(",".join(arraylist_keys),
                                                                    ",".join(arraylist_values)).format(**dic_value))

def get_check_function_list(user,jobname, condition="1=1"):
    """获取当前型号检测项目列表"""
    sql = """select * from pdm_job_check_log_list where check_user = '{0}'
    and jobname = '{1}'
    and {2}"""
    data_info = ikm_fun.PG.SELECT_DIC(ikm_fun.dbc_p, sql.format(user, jobname, condition))
    return data_info

def update_current_job_check_log(check_id, params):
    """更新当前型号检测项目结果"""
    sql = u"""update pdm_job_check_log_list set {1},check_time=now() where id={0}"""
    ikm_fun.PG.SQL_EXECUTE(ikm_fun.dbc_p, sql.format(check_id, params))

def delete_current_job_check_item(check_id):
    """删除当前型号项目记录"""
    sql = "delete from pdm_job_check_log_list where id = {0}"
    ikm_fun.PG.SQL_EXECUTE(ikm_fun.dbc_p, sql.format(check_id))      
            
def get_check_data_info(condition="1=1"):
    """获取检测项目列表"""
    sql = """select * from pdm_job_check_function_list where {0}"""
    data_info = ikm_fun.PG.SELECT_DIC(ikm_fun.dbc_p, sql.format(condition))
    return data_info

def get_current_job_check_data_info(condition="1=1"):
    """获取当前型号检测项目列表"""
    sql = """select * from pdm_job_check_log_list where {0}"""
    data_info = ikm_fun.PG.SELECT_DIC(ikm_fun.dbc_p, sql.format(condition))
    return data_info

def get_user_data_info(condition="1=1"):
    """获取用户列表信息"""
    sql = """select * from pdm_job_check_user_list where {0}"""
    data_info = ikm_fun.PG.SELECT_DIC(ikm_fun.dbc_p, sql.format(condition))
    return data_info

def uploading_data(tablename=None, dic_value={}):
    """更新列表"""
    if tablename is None:
        return
    
    sql = "select * from {1} where id = {0}"
    if dic_value.get("id") is None:
        return
    
    data_info = ikm_fun.PG.SELECT_DIC(ikm_fun.dbc_p, sql.format(dic_value["id"], tablename))
    if data_info:
        sql = "delete from {1} where id = {0}"
        ikm_fun.PG.SQL_EXECUTE(ikm_fun.dbc_p, sql.format(dic_value["id"], tablename))        

    insert_sql = u"insert into {2} ({0}) values ({1})"
    arraylist_keys = dic_value.keys()    
    arraylist_values = ["'{%s}'" % x for x in arraylist_keys]
    ikm_fun.PG.SQL_EXECUTE(ikm_fun.dbc_p, insert_sql.format(",".join(arraylist_keys),
                                                            ",".join(arraylist_values),
                                                            tablename).format(**dic_value))
    
def get_process_is_running():
    """检测该项目是否运行过"""
    sql = """select * from pdm_job_workflow where process_id = {0} and job_id = {1}"""
    data_info = ikm_fun.PG.SELECT_DIC(ikm_fun.dbc_p, sql.format(processID, jobID))
    if not data_info:
        return False
    
    return True
    
    
    
