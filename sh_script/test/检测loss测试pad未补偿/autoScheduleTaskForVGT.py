#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = "luthersy"
__date__    = "20230525"
__version__ = "Revision: 1.0.0 "
__credits__ = u"""胜宏定时任务程序 """

'''
# 20250306 zl check_loss_test_pad_comp 增加检测loss测试pad是否补偿
'''


import os
import sys
import random
if sys.platform == "win32":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    scriptPath = "%s/scripts" % os.environ.get('SCRIPTS_DIR', '/incam/server/site_data')
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")

if sys.platform == "win32":    
    from pywinauto import Application

try:    
    import GetData
except Exception as e:
    print(e)
import re
import time
import shutil
import json
import requests
import subprocess
import datetime
from scriptsRunRecordLog import uploadinglog
from PyQt4 import QtCore, QtGui, Qt
from create_ui_model import app
from get_erp_job_info import get_inplan_jobs_for_uploading_layer_info, \
     get_inplan_mrp_info

import socket
localip = socket.gethostbyname_ex(socket.gethostname())
    
import MySQL_DB
conn = MySQL_DB.MySQL()
#dbc_m = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='hdi_engineering', prod=3306,
                           #username='root', passwd='k06931!')
#dbc_p = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='project_status', prod=3306,
                           #username='root', passwd='k06931!')

script_dir = os.path.dirname(sys.argv[0])
if sys.platform == "win32":
    login_soft_script_name = "no_gui_login_genesis"
    tmp_dir = "c:/tmp"
    #if "192.168.19.243" in localip[2]:
        #login_soft_script_name = "no_gui_login_incam_win"
else:
    login_soft_script_name = "no_gui_login_incam"
    tmp_dir = "/tmp"
    
    
class LongTimeRunThing(QtCore.QThread):
    def __init__(self, args, parent=None):
        super(LongTimeRunThing, self).__init__(parent)
        self.args = args

    def run(self):
        print(self.args)
        output_id = self.args[-4]
        worklayer = self.args[-3]
        user_id = self.args[-2]
        output_dir = self.args[-1]
        jobname = self.args[4]
        
        os.environ["GEN_LOGIN_USER"] = str(user_id)
        os.system("python {0}/{1}.py {2} {3} {4} {5} {6} Only_Output no_gui".format(*self.args))
        if os.path.exists("/tmp/{0}_{1}_mem_free.log".format(jobname, worklayer)):
            # 报内存不足时在执行一次 单元内转surface
            if worklayer.startswith("l") and worklayer.split("-")[0] not in ["l1", "l{0}".format(int(jobname[4:6]))]:
                os.system("python {0}/{1}.py {2} {3} {4} {5} {6} Only_Output no_gui".format(*self.args))
            
            os.unlink("/tmp/{0}_{1}_mem_free.log".format(jobname, worklayer))
             
        filepath =os.path.join(output_dir, worklayer)
        
        #监测文件是否输出完整
        destroy_filepath = os.path.join(output_dir, worklayer+".xhdr")
        if os.path.exists(destroy_filepath):
            try:
                os.unlink(filepath)
                os.unlink(destroy_filepath)
            except:
                pass
            
        if os.path.exists(filepath):
            os.environ["GEN_LOGIN_USER"] = str(15 + user_id)
            os.system("python {0}/{1}.py {2} {3} {4} {5} {6} Only_Compare no_gui".format(*self.args))            
        
        success_file = os.path.join(tmp_dir, "success_{0}_{1}.log".format(output_id, worklayer))
        
        if sys.platform <> "win32":
            os.environ["GEN_LOGIN_USER_{0}".format(worklayer.upper())] = str(user_id)
            if not os.path.exists(filepath):
                os.system("python {0}/no_gui_login_incam.py {2} {3} {4} {5} {6} Only_Output no_gui incam".format(*self.args))
                
                if os.path.exists("/tmp/{0}_{1}_mem_free.log".format(jobname, worklayer)):
                    # 报内存不足时在执行一次 单元内转surface
                    if worklayer.startswith("l") and worklayer.split("-")[0] not in ["l1", "l{0}".format(int(jobname[4:6]))]:
                        os.system("python {0}/no_gui_login_incam.py {2} {3} {4} {5} {6} Only_Output no_gui incam".format(*self.args))
                    
                    os.unlink("/tmp/{0}_{1}_mem_free.log".format(jobname, worklayer))                

            #若比对失败 在incam比对
            if not os.path.exists(success_file) and os.path.exists(filepath):
                # 跟翟鸣讨论后 内层线路不再回读
                if worklayer.startswith("l") and worklayer.split("-")[0] not in ["l1", "l{0}".format(int(jobname[4:6]))]:
                    with open(success_file, "w") as f:
                        f.write("not compare")                    
                else:
                    os.system("python {0}/no_gui_login_incam.py {2} {3} {4} {5} {6} Only_Compare no_gui incam".format(*self.args))

            
            #genesis在比对一次
            #if not os.path.exists(success_file) and os.path.exists(filepath):
                #os.environ["GEN_LOGIN_USER"] = str(15 + user_id)
                #os.system("python {0}/{1}.py {2} {3} {4} {5} {6} Only_Compare no_gui".format(*self.args)) 
            
        finish_file = os.path.join(tmp_dir, "finish_{0}_{1}.log".format(output_id, worklayer))
        with open(finish_file, "w") as f:
            f.write(str(output_id))


class scheduleTask(QtCore.QObject):

    def __init__(self, parent=None):
        super(scheduleTask, self).__init__(parent)
        try:  
            self.getDATA = GetData.Data()
        except Exception as e:
            print(e)
    
    def run(self):
        pass
    
    def getJOB_LockInfo(self, jobname, dataType='locked_info'):
        """
        从数据库中获取料号的锁记录
        :param dataType: 获取的数据类型（status:locked_info log:locked_log）
        :return:dict
        """        
        lockData = self.getDATA.getLock_Info(jobname.split("-")[0])

        try:
            return json.loads(lockData[dataType], encoding='utf8')
        except:
            # print u'传入的数据参数异常'
            return {}      
        
    def get_mysql_data(self, condtion="1=1"):
        dbc_m = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='hdi_engineering', prod=3306,
                                   username='root', passwd='k06931!')           
        sql = u"""SELECT * FROM  hdi_electron_tools.hdi_job_tools
        where {0}""".format(condtion)
        # print(sql)
        data_info = conn.SELECT_DIC(dbc_m, sql)
        dbc_m.close()
        return data_info
    
    def update_mysql_data(self, values, condition="id = -1", params=None):
        dbc_m = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='hdi_engineering', prod=3306,
                                   username='root', passwd='k06931!')        
        sql = u"""update hdi_electron_tools.hdi_job_tools set {0} where {1}"""
        if params:
            conn.SQL_EXECUTE(dbc_m, sql.format(",".join(values), condition), params)
        else:
            conn.SQL_EXECUTE(dbc_m, sql.format(",".join(values), condition))
        dbc_m.close()
        
    def get_current_format_time(self):
        time_form = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        return time_form    
            
    def run_all_output_type(self, *args):
        """输出所有类型工具"""
        
        while True:
            try:               
                dic_condition = {"Facotry": "S01H1","type": u"正式","isOutput": "Y",}
                param = []          
                for k, v in dic_condition.iteritems():
                    param.append(u"{0}='{1}'".format(k, v))        
                param.append("(OutputStatus is null or OutputStatus = '')")        
                
                if param:            
                    data_info = self.get_mysql_data(condtion=" and ".join(param))
                    #测试
                    if args:                        
                        data_info = self.get_mysql_data(condtion="id = {0}".format(*args))
                else:
                    data_info = []
                
                all_ouput_jobs = []
                dic_job_id = {}
                for info in sorted(data_info, key=lambda x: (x["workLevel"] * -1, x["appTime"])):
                    # gerber单独的 不在次模块中循环
                    if info["data_type"] == u"输出GB资料":
                        continue
                    # if info["Job"] not in all_ouput_jobs:
                    
                    if info["Job"] not in all_ouput_jobs:                        
                        all_ouput_jobs.append(info["Job"])
                        
                    if not dic_job_id.has_key(info["Job"].lower()):
                        dic_job_id[info["Job"].lower()] = [str(info["id"])]
                    else:
                        dic_job_id[info["Job"].lower()].append(str(info["id"]))

                # print(all_ouput_jobs)
                # if all_ouput_jobs:
                for name in all_ouput_jobs:
                    
                    if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)):
                        continue
                    
                    name = name.lower()
                    res = self.import_tgz(name, dic_job_id.get(name, []))
                    
                    if res:
                    
                        with open("{0}/outputing_{1}.log".format(tmp_dir, name), "w") as f:
                            f.write("running")            
                        
                        exists_run_id = []
                        for info in sorted(data_info, key=lambda x: x["workLevel"] * -1):
                            
                            jobname = info["Job"].lower()
                            if jobname != name:
                                continue 
                            
                            output_id = info["id"]
                            
                            # 检测资料是否有送审跟锁定状态
                            try:
                                
                                dic_make_info = self.getJOB_LockInfo(name, dataType='job_make_status')
                                finish_status = True
                                for key, value in dic_make_info.iteritems():
                                    if u"内层" in key:
                                        if isinstance(value, (str, unicode)) and value in [u"已退审", u"送审中"]:
                                            finish_status = False
                                            
                                if not finish_status:
                                    log = u"资料内层未审核完成，请通知审核处理！"
                                    self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                            u"Status = '{0}'".format(u"输出异常"),
                                                            u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                                           condition="id={0}".format(output_id))
                                    continue
                            except Exception as e:
                                print(e)
                            
                            run_scripts = os.path.join(script_dir, "Auto_Engineer_Output_Tools.py")
                            
                            finish_file = os.path.join(tmp_dir, "success_{0}.log".format(output_id))
                            os.system("rm -rf {0}".format(finish_file))
                            
                            if info["data_type"] == u"输出裁磨数据" or info["data_type"] == u"输出靶距信息":
                                
                                if output_id in exists_run_id:
                                    continue
                                
                                # 先上传靶距信息
                                if info["data_type"] == u"输出裁磨数据":
                                    baju_id = [x["id"] for x in data_info
                                               if x["Job"].lower() == name
                                               and x["data_type"] == u"输出靶距信息"]
                                    if baju_id and baju_id[0] not in exists_run_id:
                                        self.run_incam_pnlrout_output_type(baju_id[0], "not_import_tgz")
                                        exists_run_id.append(baju_id[0])
                                
                                if info["data_type"] == u"输出靶距信息":
                                    caimo_id = [x["id"] for x in data_info
                                               if x["Job"].lower() == name
                                               and x["data_type"] == u"输出裁磨数据"]
                                    if not caimo_id:
                                        log = u"检测到 没有登记 输出裁磨数据 ，不能自动上传靶距信息，请输出靶距信息 跟输出裁磨数据 同时登记<br>"                                
                                        self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                                u"Status = '{0}'".format(u"输出异常"),
                                                                u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                                               condition="id={0}".format(output_id))
                                        continue
                                    
                                self.run_incam_pnlrout_output_type(output_id, "not_import_tgz")
                            
                            print("---->", [info["data_type"]], )
                            if info["data_type"] in [u"输出奥宝LDI资料(线路及辅助)", u"输出奥宝LDI资料(盖孔及防焊后站)"]:
                                self.run_incam_ldi_opfx_output_type(output_id, "not_import_tgz")
                                
                            if info["data_type"] == u"输出长七短五涨缩靶坐标":
                                self.run_incam_yh_pad_output_type(output_id, "not_import_tgz")                                                                
                            
                            exists_run_id.append(output_id)
                            
                    if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)):
                        os.unlink("{0}/outputing_{1}.log".format(tmp_dir, name))
                        
                    run_scripts = "{0}/del_job.py no_gui".format(script_dir)
                    os.system("python {0}/{2}.py {1}".format(script_dir, run_scripts, login_soft_script_name))
                    
                    break
                
            except Exception, e:
                print(e)
                
            if args:
                break
            
            time.sleep(60)
            
    def run_all_output_type_linshi(self, *args):
        """输出所有临时申请类型工具"""
        
        while True:
            try:               
                dic_condition = {"Facotry": "S01H1","type": u"临时","isOutput": "Y",}
                param = []          
                for k, v in dic_condition.iteritems():
                    param.append(u"{0}='{1}'".format(k, v))        
                param.append("(OutputStatus is null or OutputStatus = '')")
                param.append("appTime > '2024-06-01 10:00:00'")  
                
                if param:            
                    data_info = self.get_mysql_data(condtion=" and ".join(param))
                    #测试
                    if args:                        
                        data_info = self.get_mysql_data(condtion="id = {0}".format(*args))
                else:
                    data_info = []
                
                all_ouput_jobs = []
                dic_job_id = {}
                for info in sorted(data_info, key=lambda x: (x["workLevel"] * -1, x["appTime"])):
                    
                    if info["data_type"] not in [u"临时字符", u"临时avi资料"]:
                        continue
                    
                    if info["Job"] not in all_ouput_jobs:                        
                        all_ouput_jobs.append(info["Job"])
                        
                    if not dic_job_id.has_key(info["Job"].lower()):
                        dic_job_id[info["Job"].lower()] = [str(info["id"])]
                    else:
                        dic_job_id[info["Job"].lower()].append(str(info["id"]))

                # print(all_ouput_jobs)
                # if all_ouput_jobs:
                for name in all_ouput_jobs:
                    
                    if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)):
                        continue
                    
                    name = name.lower()
                    res = 0
                    if sys.platform <> "win32":
                        # 先判断服务器db目录是否存在此型号 存在则优先使用服务器的资料
                        db_job_path = "/id/incamp_db1/jobs/{0}".format(name)
                        print("----------->",os.path.exists(db_job_path))                            
                        if os.path.exists(db_job_path):
                            print("----------->", db_job_path)
                            res = self.import_tgz(name, dic_job_id.get(name, []), "no_gui_login_incam", tgz_import_path=db_job_path)
                        else:                     
                            res = self.import_tgz(name, dic_job_id.get(name, []))
                    
                    if res:
                    
                        with open("{0}/outputing_{1}.log".format(tmp_dir, name), "w") as f:
                            f.write("running")            
                        
                        exists_run_id = []
                        for info in sorted(data_info, key=lambda x: x["workLevel"] * -1):
                            
                            jobname = info["Job"].lower()
                            if jobname != name:
                                continue 
                            
                            output_id = info["id"]
                            run_scripts = os.path.join(script_dir, "Auto_Engineer_Output_Tools.py")
                            
                            # 检测资料是否有送审跟锁定状态
                            dic_make_info = self.getJOB_LockInfo(name, dataType='job_make_status')
                            finish_status = True
                            for key, value in dic_make_info.iteritems():
                                if u"外层" in key or u"全套" in key:
                                    if isinstance(value, (str, unicode)) and value in [u"已退审", u"送审中"]:
                                        finish_status = False
                                        
                            if not finish_status:
                                log = u"资料外层未审核完成，请通知审核处理！"
                                self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                        u"Status = '{0}'".format(u"输出异常"),
                                                        u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                                       condition="id={0}".format(output_id))
                                continue                            
                            
                            finish_file = os.path.join(tmp_dir, "success_{0}.log".format(output_id))
                            os.system("rm -rf {0}".format(finish_file))
                                
                            if info["data_type"] in [u"临时字符"]:
                                if info["dataName"] in [u"文字喷墨"]:
                                    self.run_incam_jinxin_tgz_output_type(output_id, "not_import_tgz")
                                
                            if info["data_type"] == u"临时avi资料":
                                self.run_incam_avi_tgz_output_type(output_id, "not_import_tgz")                                                                
                            
                            exists_run_id.append(output_id)
                            
                    if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)):
                        os.unlink("{0}/outputing_{1}.log".format(tmp_dir, name))
                        
                    run_scripts = "{0}/del_job.py no_gui".format(script_dir)
                    os.system("python {0}/{2}.py {1}".format(script_dir, run_scripts, login_soft_script_name))
                    
                    break
                
            except Exception, e:
                print(e)
                
            if args:
                break
            
            time.sleep(60)

    def run_incam_jinxin_tgz_output_type(self, *args):
        """incam输出劲鑫TGZ 资料工具"""
        
        while True:
            try:             
                dic_condition = {"Facotry": "S01H1","type": u"临时","data_type": u"临时字符","dataName": u"文字喷墨","isOutput": "Y",}
                param = []          
                for k, v in dic_condition.iteritems():
                    param.append(u"{0}='{1}'".format(k, v))        
                param.append("(OutputStatus is null or OutputStatus = '')")       
                
                if param:            
                    data_info = self.get_mysql_data(condtion=" and ".join(param))
                    #测试
                    if args:                        
                        data_info = self.get_mysql_data(condtion="id = {0}".format(*args))
                else:
                    data_info = []                    
                
                all_ouput_jobs = []
                dic_job_id = {}
                for info in sorted(data_info, key=lambda x: (x["workLevel"] * -1, x["appTime"])):
                    
                    if info["Job"] not in all_ouput_jobs:                    
                        all_ouput_jobs.append(info["Job"])
                        
                    if not dic_job_id.has_key(info["Job"].lower()):
                        dic_job_id[info["Job"].lower()] = [str(info["id"])]
                    else:
                        dic_job_id[info["Job"].lower()].append(str(info["id"]))
    
                print(all_ouput_jobs)
                for name in all_ouput_jobs:            
                    output_name = name.lower()
                    
                    if "not_import_tgz" in args:
                        res = 1                        
                    else:
                        print(os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, output_name)))
                        if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, output_name)):
                            time.sleep(5)
                            continue
                        
                        res = 0
                        if sys.platform <> "win32":
                            # 先判断服务器db目录是否存在此型号 存在则优先使用服务器的资料
                            db_job_path = "/id/incamp_db1/jobs/{0}".format(output_name)
                            print("----------->",os.path.exists(db_job_path))                            
                            if os.path.exists(db_job_path):
                                print("----------->", db_job_path)
                                res = self.import_tgz(output_name, dic_job_id[output_name], "no_gui_login_incam", tgz_import_path=db_job_path)
                            else:                                
                                res = self.import_tgz(output_name, dic_job_id[output_name])                     
                    
                    print(res, os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, output_name)))
                    
                    if res:
                    
                        with open("{0}/outputing_{1}.log".format(tmp_dir, output_name), "w") as f:
                            f.write("running")
                            
                        start_calc_time = time.time()
                        
                        output_count = 0
                        for info in sorted(data_info, key=lambda x: (x["workLevel"] * -1, x["appTime"])):
                            
                            jobname = info["Job"].lower().strip()
                            if jobname != output_name:
                                continue
                            
                            output_id = info["id"]
                            
                            if output_count > 0:
                                # 第二次需重新导入tgz
                                self.update_mysql_data([u"OutputStatus = ''",
                                                        u"Status = ''",
                                                        u"AlarmLog = ''"],
                                                       u"id = {0}".format(output_id)) 
                                res = 0
                                if sys.platform <> "win32":
                                    # 先判断服务器db目录是否存在此型号 存在则优先使用服务器的资料
                                    db_job_path = "/id/incamp_db1/jobs/{0}".format(jobname)
                                    print("----------->2",os.path.exists(db_job_path))                            
                                    if os.path.exists(db_job_path):
                                        print("----------->2", db_job_path)
                                        res = self.import_tgz(jobname,  [str(output_id)], "no_gui_login_incam", tgz_import_path=db_job_path)
                                    else:                                
                                        res = self.import_tgz(jobname,  [str(output_id)])
                                
                                if not res:                                    
                                    continue
                            
                            output_count += 1 
                            # output_layers = [x for x in info["OutLayer"].split(";") if x.strip()]
                            
                            self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出中"),
                                                    u"Status = '{0}'".format(u"输出中"),
                                                    u"AlarmLog = ''"],
                                                   condition="id={0}".format(output_id))                            
                            
                            dest_net_path = info["OutputPath"]
                            if u"文字喷墨测试" not in dest_net_path:                                
                                dest_net_path = "\\192.168.2.57\临时文件夹\系列资料临时存放区\03.CAM制作资料暂放（勿删）\000勿删\文字喷墨测试\{0}系列\{1}".format(
                                    jobname[1:4].upper(), jobname.upper()
                                )
                            dest_net_path = dest_net_path.replace("\\", "/")
                            dest_net_path = dest_net_path.replace(ur"//192.168.2.57/临时文件夹/系列资料临时存放区/", "/windows/33.file/")
                            dest_net_path = dest_net_path.replace(ur"//192.168.2.174/GCfiles/", "/windows/174.file/")
                            # print([dest_net_path])
                            
                            try:
                                os.makedirs(dest_net_path)
                            except Exception, e:
                                print(e)
                            
                            if not os.path.exists(dest_net_path):                                
                                log = u"Linux中创建输出路径失败{0} <br>".format(dest_net_path)
                                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)], condition="id={0}".format(output_id))                    
                                continue
                            
                            output_dir = "{0}/{1}/{2}/{3}".format(tmp_dir, jobname, "jinxin", output_id)
                            if os.path.exists(output_dir):
                                shutil.rmtree(output_dir)
                            
                            try:                                
                                os.makedirs(output_dir)
                            except Exception, e:
                                print(e)
                                pass                            

                            # run_scripts = "/incam/server/site_data/scripts/sh_script/jin_xin/jinxin_tgz_auto.py"
                            run_scripts = os.path.join(script_dir, "Auto_Engineer_Output_Tools.py")
                            data_type = "auto_output_jinxin"
                            
                            # 检测资料是否有送审跟锁定状态
                            try:
                                try:                                    
                                    dic_make_info = self.getJOB_LockInfo(jobname, dataType='job_make_status')
                                except Exception as e:
                                    with open("/tmp/sql_error.log", "w") as f:
                                        f.write(str(e) + "\n")
                                # print("----------------->", dic_make_info)
                                finish_status = True
                                for key, value in dic_make_info.iteritems():
                                    if u"外层" in key or u"全套" in key:
                                        if isinstance(value, (str, unicode)) and value in [u"已退审", u"送审中"]:
                                            finish_status = False
                                            
                                if not finish_status:
                                    log = u"资料外层未审核完成，请通知审核处理！"
                                    self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                            u"Status = '{0}'".format(u"输出异常"),
                                                            u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                                           condition="id={0}".format(output_id))
                                    continue
                            except Exception as e:
                                print("--------------------->", e)
                                with open("/tmp/jinxin_error.log", "w") as f:
                                    f.write(str(jobname) + str(e))
                                # continue                                

                            success_file = os.path.join(tmp_dir, "success_{0}.log".format(output_id))
                            os.system("rm -rf {0}".format(success_file))
                            error_file = os.path.join(tmp_dir, "success_{0}_check_error.log".format(output_id))           
                            os.system("rm -rf {0}".format(error_file))
                            
                            os.environ["JOB"] = jobname
                            if "gui_run" in sys.argv[1:]:
                                os.system("python %s/%s.py %s %s %s %s %s" %
                                          (script_dir,login_soft_script_name, run_scripts, data_type, jobname, output_id, "gui_run"))                               
                            else:
                                os.system("python %s/%s.py %s %s %s %s %s" %
                                          (script_dir,login_soft_script_name, run_scripts, data_type, jobname, output_id, "no_gui"))                                

                            if os.path.exists(error_file):
                                log = file(error_file).readlines()
                                self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常"),
                                                        u"Status = '{0}'".format(u"输出异常"),
                                                        u"AlarmLog = concat(AlarmLog,'{0}')".format("<br>".join(log).decode("utf8"))
                                                        ],
                                                       condition="id={0}".format(output_id))
                                try:
                                    shutil.rmtree(dest_net_path)
                                except:
                                    pass                                
                            else:                                
                                if os.path.exists(success_file):
                                    success_log = False
                                    tgz_path = os.path.join(output_dir, jobname+".tgz")
                                    if os.path.exists(tgz_path):                                        
                                        success_log = True
                                            
                                    if success_log:
                                        self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出完成"),
                                                                u"Status = '输出完成'"], condition="id={0}".format(output_id)) 

                                        shutil.copy(tgz_path, dest_net_path+"/"+jobname+"_jinxin.tgz")
                                    else:
                                        log = u"输出文件{0}不存在，请手动输出！".format(jobname+".tgz")
                                        self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                                u"Status = '{0}'".format(u"输出异常"),
                                                                u"AlarmLog = concat(AlarmLog,'{0}')".format(log)
                                                                ],condition="id={0}".format(output_id))
                                        
                                else:
                                    change_system_time_log = "/tmp/change_system_time.log"
                                    os.system("rm -rf {0}".format(change_system_time_log))                                    
                                    log = u"INCAMPRO 输出程序异常中断，请手动输出劲鑫TGZ资料！<br>"                                
                                    self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                            u"Status = '{0}'".format(u"输出异常"),
                                                            u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                                           condition="id={0}".format(output_id))                                 

                            if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, jobname)):
                                os.unlink("{0}/outputing_{1}.log".format(tmp_dir, jobname))
                                
                            for filename in os.listdir(tmp_dir):
                                filepath = os.path.join(tmp_dir,filename)
                                if "success_{0}".format(output_id) in filename:
                                    os.unlink(filepath)
                                
                                if "finish_{0}".format(output_id) in filename:
                                    os.unlink(filepath)
                                    
                                if "calc_time_{0}".format(output_id) in filename:
                                    os.unlink(filepath)
                                    
                            if os.path.exists(output_dir):
                                shutil.rmtree(output_dir)
                        
                        end_calc_time = time.time()
                        seconds = end_calc_time - start_calc_time
                        time_log = u"<br>incam总耗时:{0}分钟 <br>".format(round(seconds/60, 2))
                        self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(time_log),
                                                "OutputTime = now()", ],
                                               condition="id={0}".format(output_id))
                    
                    if "not_import_tgz" not in args:                        
                        run_scripts = "{0}/del_job.py no_gui".format(script_dir)
                        if "192.168.19.243" not in localip[2]:
                            os.system("python {0}/{2}.py {1}".format(script_dir, run_scripts, login_soft_script_name))
                    
            except Exception as e:
                # print(e)
                with open("/tmp/error.log", "w") as f:
                    f.write(str(e))
                
            if args:
                break
            
            time.sleep(60)
            
            
    def run_incam_wangping_tgz_output_type(self, *args):
        """incam输出网屏TGZ 资料工具"""
        
        while True:
            try:             
                dic_condition = {"Facotry": "S01H1","type": u"临时","data_type": u"临时阻焊","dataName": u"网屏资料","isOutput": "Y",}
                param = []          
                for k, v in dic_condition.iteritems():
                    param.append(u"{0}='{1}'".format(k, v))        
                param.append("(OutputStatus is null or OutputStatus = '')")       
                
                if param:            
                    data_info = self.get_mysql_data(condtion=" and ".join(param))
                    #测试
                    if args:                        
                        data_info = self.get_mysql_data(condtion="id = {0}".format(*args))
                else:
                    data_info = []                          
                
                all_ouput_jobs = []
                dic_job_id = {}
                for info in sorted(data_info, key=lambda x: (x["workLevel"] * -1, x["appTime"])):
                    
                    if info["Job"] not in all_ouput_jobs:                    
                        all_ouput_jobs.append(info["Job"])
                        
                    if not dic_job_id.has_key(info["Job"].lower()):
                        dic_job_id[info["Job"].lower()] = [str(info["id"])]
                    else:
                        dic_job_id[info["Job"].lower()].append(str(info["id"]))
    
                print(all_ouput_jobs)
                for name in all_ouput_jobs:            
                    output_name = name.lower()
                    
                    if "not_import_tgz" in args:
                        res = 1                        
                    else:
                        print(os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, output_name)))
                        if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, output_name)):
                            time.sleep(5)
                            continue
                        
                        res = 0
                        if sys.platform <> "win32":
                            # 先判断服务器db目录是否存在此型号 存在则优先使用服务器的资料
                            db_job_path = "/id/incamp_db1/jobs/{0}".format(output_name)
                            print("----------->",os.path.exists(db_job_path))                            
                            if os.path.exists(db_job_path):
                                print("----------->", db_job_path)
                                res = self.import_tgz(output_name, dic_job_id[output_name], "no_gui_login_incam", tgz_import_path=db_job_path)
                            else:                                
                                res = self.import_tgz(output_name, dic_job_id[output_name])
                        #if res and os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)):
                            #self.update_mysql_data([u"OutputStatus = ''",
                                                    #u"Status = ''",
                                                    #u"AlarmLog = ''"],
                                                   #condition="id in ({0})".format(",".join(dic_job_id[name])))
                            #time.sleep(5)
                            #continue                        
                    
                    print(res, os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, output_name)))
                    
                    if res:
                    
                        with open("{0}/outputing_{1}.log".format(tmp_dir, output_name), "w") as f:
                            f.write("running")
                            
                        start_calc_time = time.time()
                        output_count = 0
                        for info in sorted(data_info, key=lambda x: (x["workLevel"] * -1, x["appTime"])):
                            
                            jobname = info["Job"].lower().strip()
                            if jobname != output_name:
                                continue
                            
                            output_id = info["id"]
                            
                            if output_count > 0:
                                # 第二次需重新导入tgz
                                self.update_mysql_data([u"OutputStatus = ''",
                                                        u"Status = ''",
                                                        u"AlarmLog = ''"],
                                                       u"id = {0}".format(output_id))                                
                                res = 0
                                if sys.platform <> "win32":
                                    # 先判断服务器db目录是否存在此型号 存在则优先使用服务器的资料
                                    db_job_path = "/id/incamp_db1/jobs/{0}".format(jobname)
                                    print("----------->2",os.path.exists(db_job_path))                            
                                    if os.path.exists(db_job_path):
                                        print("----------->2", db_job_path)
                                        res = self.import_tgz(jobname, [str(output_id)], "no_gui_login_incam", tgz_import_path=db_job_path)
                                    else:                                
                                        res = self.import_tgz(jobname, [str(output_id)])
                                
                                if not res:                                    
                                    continue                            
                            
                            output_count += 1                            
                            output_layers = [x for x in info["OutLayer"].split(";") if x.strip()]
                            
                            self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出中"),
                                                    u"Status = '{0}'".format(u"输出中"),
                                                    u"AlarmLog = ''"],
                                                   condition="id={0}".format(output_id))                            
                            
                            dest_net_path = info["OutputPath"]
                            if u"网屏资料测试" not in dest_net_path:                                
                                dest_net_path = "\\192.168.2.57\临时文件夹\系列资料临时存放区\03.CAM制作资料暂放（勿删）\000勿删\网屏资料测试\{0}系列\{1}".format(
                                    jobname[1:4].upper(), jobname.upper()
                                )
                            dest_net_path = dest_net_path.replace("\\", "/")
                            dest_net_path = dest_net_path.replace(ur"//192.168.2.57/临时文件夹/系列资料临时存放区/", "/windows/33.file/")
                            dest_net_path = dest_net_path.replace(ur"//192.168.2.174/GCfiles/", "/windows/174.file/")
                            # print([dest_net_path])
                            
                            try:
                                os.makedirs(dest_net_path)
                            except Exception, e:
                                print(e)
                            
                            if not os.path.exists(dest_net_path):                                
                                log = u"Linux中创建输出路径失败{0} <br>".format(dest_net_path)
                                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)], condition="id={0}".format(output_id))                    
                                continue
                            
                            output_dir = "{0}/{1}/{2}/{3}".format(tmp_dir, jobname, "wangping", output_id)
                            if os.path.exists(output_dir):
                                shutil.rmtree(output_dir)
                            
                            try:                                
                                os.makedirs(output_dir)
                            except Exception, e:
                                print(e)
                                pass                            

                            # run_scripts = "/incam/server/site_data/scripts/sh_script/jin_xin/jinxin_tgz_auto.py"
                            run_scripts = os.path.join(script_dir, "Auto_Engineer_Output_Tools.py")
                            data_type = "auto_output_wangping"
                            
                            try:                                
                                # 检测资料是否有送审跟锁定状态
                                dic_make_info = self.getJOB_LockInfo(jobname, dataType='job_make_status')
                                finish_status = True
                                for key, value in dic_make_info.iteritems():
                                    if u"外层" in key or u"全套" in key:
                                        if isinstance(value, (str, unicode)) and value in [u"已退审", u"送审中"]:
                                            finish_status = False
                                            
                                if not finish_status:
                                    log = u"资料外层未审核完成，请通知审核处理！"
                                    self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                            u"Status = '{0}'".format(u"输出异常"),
                                                            u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                                           condition="id={0}".format(output_id))
                                    continue
                            except Exception as e:
                                with open("/tmp/wangping_error.log", "w") as f:
                                    f.write(str(jobname) + str(e))                                

                            success_file = os.path.join(tmp_dir, "success_{0}.log".format(output_id))
                            os.system("rm -rf {0}".format(success_file))
                            error_file = os.path.join(tmp_dir, "success_{0}_check_error.log".format(output_id))           
                            os.system("rm -rf {0}".format(error_file))
                            
                            os.environ["JOB"] = jobname
                            if "gui_run" in sys.argv[1:]:
                                os.system("python %s/%s.py %s %s %s %s %s" %
                                          (script_dir,login_soft_script_name, run_scripts, data_type, jobname, output_id, "gui_run"))                               
                            else:
                                os.system("python %s/%s.py %s %s %s %s %s" %
                                          (script_dir,login_soft_script_name, run_scripts, data_type, jobname, output_id, "no_gui"))                                

                            if os.path.exists(error_file):
                                log = file(error_file).readlines()
                                self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常"),
                                                        u"Status = '{0}'".format(u"输出异常"),
                                                        u"AlarmLog = concat(AlarmLog,'{0}')".format("<br>".join(log).decode("utf8"))
                                                        ],
                                                       condition="id={0}".format(output_id))
                                try:
                                    shutil.rmtree(dest_net_path)
                                except:
                                    pass                                
                            else:                                
                                if os.path.exists(success_file):
                                    success_log = False
                                    tgz_path = os.path.join(output_dir, jobname+".tgz")
                                    if os.path.exists(tgz_path):                                        
                                        success_log = True
                                            
                                    if success_log:
                                        self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出完成"),
                                                                u"Status = '输出完成'"], condition="id={0}".format(output_id)) 
                                        try:
                                            os.makedirs(dest_net_path+"/"+"wangping")
                                        except Exception as e:
                                            print(e)
                                        shutil.copy(tgz_path, dest_net_path+"/wangping/"+jobname+".tgz")
                                    else:
                                        log = u"网屏tgz输出异常，请手动输出！"
                                        self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                                u"Status = '{0}'".format(u"输出异常"),
                                                                u"AlarmLog = concat(AlarmLog,'{0}')".format(log)
                                                                ],condition="id={0}".format(output_id))
                                        
                                    success_log = True
                                    arraylist_log = []
                                    output_dir1 = "{0}/{1}/{2}/{3}".format(tmp_dir, jobname, "ldi", output_id)
                                    for layer in output_layers:
                                        filepath =os.path.join(output_dir1, "{0}@{1}".format(jobname, layer))
                                        success_file = os.path.join(tmp_dir, "success_{0}_{1}.log".format(output_id, layer))  
                                        if not os.path.exists(filepath):
                                            log = u"输出奥宝OPFX 层{0} 异常，请手动输出！<br>".format(layer)
                                            arraylist_log.append(log)                                    
                                            success_log = False                                
                                        else:
                                            if not os.path.exists(success_file):
                                                log = u"输出奥宝OPFX 层{0}程序回读异常，请手动输出！<br>".format(layer)
                                                arraylist_log.append(log)
                                                success_log = False                                                                           
                                            else:
                                                shutil.copy(filepath, dest_net_path)
                                    
                                    if not success_log:                                        
                                        self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                                u"Status = '{0}'".format(u"输出异常"),
                                                                u"AlarmLog = concat(AlarmLog,'{0}')".format("<br>".join(arraylist_log))],
                                                               condition="id={0}".format(output_id))                                        
                                        
                                else:
                                    change_system_time_log = "/tmp/change_system_time.log"
                                    os.system("rm -rf {0}".format(change_system_time_log))
                                    
                                    log = u"INCAMPRO 输出程序异常中断，请手动输出网屏TGZ资料！<br>"                                
                                    self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                            u"Status = '{0}'".format(u"输出异常"),
                                                            u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                                           condition="id={0}".format(output_id))                                 

                            if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, jobname)):
                                os.unlink("{0}/outputing_{1}.log".format(tmp_dir, jobname))
                                
                            for filename in os.listdir(tmp_dir):
                                filepath = os.path.join(tmp_dir,filename)
                                if "success_{0}".format(output_id) in filename:
                                    os.unlink(filepath)
                                
                                if "finish_{0}".format(output_id) in filename:
                                    os.unlink(filepath)
                                    
                                if "calc_time_{0}".format(output_id) in filename:
                                    os.unlink(filepath)                                  
                                    
                            if os.path.exists(output_dir):
                                shutil.rmtree(output_dir)
                        
                        end_calc_time = time.time()
                        seconds = end_calc_time - start_calc_time
                        time_log = u"<br>incam总耗时:{0}分钟 <br>".format(round(seconds/60, 2))
                        self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(time_log),
                                                "OutputTime = now()", ],
                                               condition="id={0}".format(output_id))
                    
                    if "not_import_tgz" not in args:                        
                        run_scripts = "{0}/del_job.py no_gui".format(script_dir)
                        if "192.168.19.243" not in localip[2]:
                            os.system("python {0}/{2}.py {1}".format(script_dir, run_scripts, login_soft_script_name))
                    
            except Exception, e:
                # print(e)
                with open("/tmp/error.log", "w") as f:
                    f.write(str(e))                
                
            if args:
                break
            
            time.sleep(60)                
            
    def run_incam_avi_tgz_output_type(self, *args):
        """incam输出AVI tgz资料工具"""
        
        while True:
            try:             
                dic_condition = {"Facotry": "S01H1","type": u"临时","data_type": u"临时avi资料","isOutput": "Y",}
                param = []          
                for k, v in dic_condition.iteritems():
                    param.append(u"{0}='{1}'".format(k, v))        
                param.append("(OutputStatus is null or OutputStatus = '')")       
                
                if param:            
                    data_info = self.get_mysql_data(condtion=" and ".join(param))
                    #测试
                    if args:                        
                        data_info = self.get_mysql_data(condtion="id = {0}".format(*args))
                else:
                    data_info = []
                
                all_ouput_jobs = []
                dic_job_id = {}
                for info in sorted(data_info, key=lambda x: x["workLevel"] * -1):
                    # if info["Job"] not in all_ouput_jobs:
                    all_ouput_jobs.append(info["Job"])
                    if not dic_job_id.has_key(info["Job"].lower()):
                        dic_job_id[info["Job"].lower()] = [str(info["id"])]
                    else:
                        dic_job_id[info["Job"].lower()].append(str(info["id"]))                    
    
                print(all_ouput_jobs)
                for name in set(all_ouput_jobs):            
                    name = name.lower()
                    
                    if "not_import_tgz" in args:
                        res = 1                        
                    else:
                        print(os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)))
                        if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)):
                            time.sleep(5)
                            continue                        
                        res = self.import_tgz(name, dic_job_id[name])
                        
                        #if res and os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)):
                            #self.update_mysql_data([u"OutputStatus = ''",
                                                    #u"Status = ''",
                                                    #u"AlarmLog = ''"],
                                                   #condition="id in ({0})".format(",".join(dic_job_id[name])))
                            #time.sleep(5)
                            #continue                        
                    
                    print(res, os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)))
                    
                    if res:
                    
                        with open("{0}/outputing_{1}.log".format(tmp_dir, name), "w") as f:
                            f.write("running")
                            
                        start_calc_time = time.time()
                        
                        for info in sorted(data_info, key=lambda x: x["workLevel"] * -1):
                            
                            jobname = info["Job"].lower().strip()
                            if jobname != name:
                                continue
                            
                            output_id = info["id"]
                            # output_layers = [x for x in info["OutLayer"].split(";") if x.strip()]
                            
                            self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出中"),
                                                    u"Status = '{0}'".format(u"输出中"),
                                                    u"AlarmLog = ''"],
                                                   condition="id={0}".format(output_id))                            
                            
                            dest_net_path = os.path.join(info["OutputPath"], jobname)
                            dest_net_path = dest_net_path.replace("\\", "/")
                            dest_net_path = dest_net_path.replace(ur"//192.168.2.57/临时文件夹/系列资料临时存放区/", "/windows/33.file/")
                            dest_net_path = dest_net_path.replace(ur"//192.168.2.174/GCfiles/", "/windows/174.file/")
                            # print([dest_net_path])
                            try:
                                os.makedirs(dest_net_path)
                            except Exception, e:
                                print(e)
                            
                            if not os.path.exists(dest_net_path):                                
                                log = u"Linux中创建输出路径失败{0} <br>".format(dest_net_path)
                                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)], condition="id={0}".format(output_id))                    
                                continue
                            
                            output_dir = "{0}/{1}/{2}/{3}".format(tmp_dir, jobname, "avi", output_id)
                            if os.path.exists(output_dir):
                                shutil.rmtree(output_dir)
                            
                            try:                                
                                os.makedirs(output_dir)
                            except Exception, e:
                                print(e)
                                pass                            

                            run_scripts = "/incam/server/site_data/scripts/hdi_scr/Output/output_avi_tgz/output_avi_tgz_auto.py"
                            data_type = "avi"

                            success_file = os.path.join(tmp_dir, "success_{0}.log".format(output_id))
                            os.system("rm -rf {0}".format(success_file))
                            error_file = os.path.join(tmp_dir, "success_{0}_check_error.log".format(output_id))           
                            os.system("rm -rf {0}".format(error_file))
                            
                            os.environ["JOB"] = jobname
                            if "gui_run" in args:
                                os.system("python %s/%s.py %s %s %s %s %s" %
                                          (script_dir,login_soft_script_name, run_scripts, data_type, jobname, output_id, "gui_run"))                               
                            else:
                                os.system("python %s/%s.py %s %s %s %s %s" %
                                          (script_dir,login_soft_script_name, run_scripts, data_type, jobname, output_id, "no_gui"))                                

                            if os.path.exists(error_file):
                                log = file(error_file).readlines()
                                self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                        u"Status = '{0}'".format(u"输出异常"),
                                                        u"AlarmLog = concat(AlarmLog,'{0}')".format("<br>".join(log).decode("utf8"))
                                                        ],
                                                       condition="id={0}".format(output_id))
                                try:
                                    shutil.rmtree(dest_net_path)
                                except:
                                    pass                                
                            else:                                
                                if os.path.exists(success_file):
                                    success_log = False
                                    tgz_path = os.path.join(output_dir, jobname+".tgz")
                                    if os.path.exists(tgz_path):                                        
                                        success_log = True
                                            
                                    if success_log:
                                        self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出完成"),
                                                                u"Status = '输出完成'"], condition="id={0}".format(output_id)) 

                                        shutil.copy(tgz_path, dest_net_path+"/"+jobname+"_outavi.tgz")
                                    else:
                                        log = u"输出文件{0}不存在，请手动输出！".format(jobname+".tgz")
                                        self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                                u"Status = '{0}'".format(u"输出异常"),
                                                                u"AlarmLog = concat(AlarmLog,'{0}')".format(log)
                                                                ],condition="id={0}".format(output_id))
                                        
                                else:
                                    log = u"INCAMPRO 输出程序异常中断，请手动输出avi资料！<br>"                                
                                    self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                            u"Status = '{0}'".format(u"输出异常"),
                                                            u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                                           condition="id={0}".format(output_id))                                 

                            if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, jobname)):
                                os.unlink("{0}/outputing_{1}.log".format(tmp_dir, jobname))
                                
                            for name in os.listdir(tmp_dir):
                                filepath = os.path.join(tmp_dir,name)
                                if "success_{0}".format(output_id) in name:
                                    os.unlink(filepath)
                                
                                if "finish_{0}".format(output_id) in name:
                                    os.unlink(filepath)
                                    
                                if "calc_time_{0}".format(output_id) in name:
                                    os.unlink(filepath)                                  
                                    
                            #if os.path.exists(output_dir):
                                #shutil.rmtree(output_dir)
                        
                        end_calc_time = time.time()
                        seconds = end_calc_time - start_calc_time
                        time_log = u"<br>incam总耗时:{0}分钟 <br>".format(round(seconds/60, 2))
                        self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(time_log),
                                                "OutputTime = now()", ],
                                               condition="id={0}".format(output_id))
                    
                    if "not_import_tgz" not in args:                        
                        run_scripts = "{0}/del_job.py no_gui".format(script_dir)
                        if "192.168.19.243" not in localip[2]:
                            os.system("python {0}/{2}.py {1}".format(script_dir, run_scripts, login_soft_script_name))
                    
            except Exception, e:
                print(e)
                
            if args:
                break
            
            time.sleep(60)    
            
    def run_convert_laser_drill_files_output_type(self, *args):
        """镭射自动转档"""
        
        while True:
            try:             
                dic_condition = {"Facotry": "S01H1","type": u"临时","isOutput": "Y",}
                param = []          
                for k, v in dic_condition.iteritems():
                    param.append(u"{0}='{1}'".format(k, v))        
                param.append("(OutputStatus is null or OutputStatus = '')")
                param.append(u"(data_type = '镭射转档资料')")   
                
                if param:            
                    data_info = self.get_mysql_data(condtion=" and ".join(param))
                    #测试
                    if args:                        
                        data_info = self.get_mysql_data(condtion="id = {0}".format(*args))
                else:
                    data_info = []
                
                all_ouput_jobs = []
                dic_job_id = {}
                for info in sorted(data_info, key=lambda x: (x["workLevel"] * -1, x["appTime"])):
                    
                    if info["Job"] not in all_ouput_jobs:
                        all_ouput_jobs.append(info["Job"])
                        
                    if not dic_job_id.has_key(info["Job"].lower()):
                        dic_job_id[info["Job"].lower()] = [str(info["id"])]
                    else:
                        dic_job_id[info["Job"].lower()].append(str(info["id"]))                    
    
                print(all_ouput_jobs)
                for name in all_ouput_jobs:            
                    name = name.lower()
                    
                    if "not_import_tgz" in args:
                        res = 1                        
                    else:                    
                        print(os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)))
                        if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)):
                            time.sleep(5)
                            continue
                        
                        res = self.import_tgz(name, dic_job_id[name])
                        #if res and os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)):
                            #self.update_mysql_data([u"OutputStatus = ''",
                                                    #u"Status = ''",
                                                    #u"AlarmLog = ''"],
                                                   #condition="id in ({0})".format(",".join(dic_job_id[name])))
                            #time.sleep(5)
                            #continue                        
                    
                    print(res, os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)))
                    
                    if res:
                        
                        with open("{0}/outputing_{1}.log".format(tmp_dir, name), "w") as f:
                            f.write("running")
                        
                        for info in sorted(data_info, key=lambda x: x["workLevel"] * -1):
                            start_calc_time = time.time()
                            jobname = info["Job"].lower().strip()
                            if jobname != name:
                                continue
                            
                            output_id = info["id"]

                            self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出中"),
                                                    u"Status = '{0}'".format(u"输出中"),
                                                    u"AlarmLog = ''"],
                                                   condition="id={0}".format(output_id))
                            
                            dest_net_path = info["OutputPath"]
                            if u"自动镭射转档测试" in dest_net_path:
                                dest_net_path = ur"\\192.168.2.174\GCfiles\Program\Laser\5代机6H代机钻带(有效65X65)\{0}系列\{1}".format(jobname[1:4].upper(), jobname.upper())
                            
                            try:
                                os.makedirs(dest_net_path)
                            except Exception, e:
                                print(e)
                            
                            if not os.path.exists(dest_net_path):                                
                                log = u"genesis中创建输出路径失败{0} <br>".format(dest_net_path)
                                self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常"),
                                                        u"Status = '{0}'".format(u"输出异常"),
                                                        u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                                       condition="id={0}".format(output_id))                                
                                continue
                            
                            try:            
                                for name in os.listdir("d:/disk/laser"):
                                    os.system("rm -rf d:/disk/laser/{0}".format(name))
                            except Exception, e:
                                print e
                                
                            output_dir = "{0}/{1}/{2}/{3}".format(tmp_dir, jobname, "laser", output_id)
                            if os.path.exists(output_dir):
                                shutil.rmtree(output_dir)
                            
                            try:                                
                                os.makedirs(output_dir)
                            except Exception, e:
                                print(e)
                                pass                                                    
                            
                            run_scripts = os.path.join(script_dir, "Auto_Engineer_Output_Tools.py")
                            
                            success_file = os.path.join(tmp_dir, "success_{0}.log".format(output_id))
                            os.system("rm -rf {0}".format(success_file))
                            error_file = os.path.join(tmp_dir, "success_{0}_check_error.log".format(output_id))           
                            os.system("rm -rf {0}".format(error_file))
                            
                            if ";" in info["OutLayer"]:
                                output_layers = [x for x in info["OutLayer"].split(";") if x.strip()]
                            else:
                                output_layers = [x for x in info["OutLayer"].split(",") if x.strip()]
                            
                            # 清除旧钻带
                            try:
                                if info["dataName"] == u"镭射转档资料":                                    
                                    for name in output_layers:
                                        if name.endswith(".write"):
                                            # job_dir = os.path.join(dest_net_path, jobname)
                                            for filename in os.listdir(dest_net_path):
                                                if filename == name:                                                    
                                                    orig_file = os.path.join(dest_net_path, name)
                                                    if os.path.exists(orig_file):                                        
                                                        os.unlink(orig_file)
                                                        
                                                convert_file_name = name.replace(".write", "write").replace(".", "-")
                                                # print("------------------------------>", convert_file_name)
                                                if convert_file_name in filename:
                                                    convert_file = os.path.join(dest_net_path, filename)
                                                    if os.path.exists(convert_file):
                                                        os.unlink(convert_file)
                            except Exception as e:
                                print(e)
    
                            data_type = "auto_convert_laser_files"
                            
                            os.environ["JOB"] = jobname
                            if "gui_run" in args:
                                for name in output_layers:
                                    if name.endswith(".write"):
                                        filepath = "d:/disk/laser/{0}/{1}".format(jobname, name.replace(".write", "write").replace(".", "-"))
                                        if os.path.exists(filepath):
                                            continue
                                        
                                        os.system("python %s/%s.py %s %s %s %s %s %s" %
                                                  (script_dir,login_soft_script_name, run_scripts, data_type, jobname, output_id, name,  "gui_run"))
                            else:
                                for name in output_layers:
                                    if name.endswith(".write"):
                                        filepath = "d:/disk/laser/{0}/{1}".format(jobname, name.replace(".write", "write").replace(".", "-"))
                                        if os.path.exists(filepath):
                                            continue
                                        
                                        os.system("python %s/%s.py %s %s %s %s %s %s" %
                                                  (script_dir,login_soft_script_name, run_scripts, data_type, jobname, output_id, name, "no_gui"))
                                        
                            
                            if os.path.exists(error_file):                                
                                self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                        u"Status = '{0}'".format(u"输出异常"),
                                                        ],
                                                       condition="id={0}".format(output_id))
                                #try:
                                    #shutil.rmtree(dest_net_path)
                                #except:
                                    #pass
                            
                            else:
                                
                                if not os.path.exists(success_file):
                                    log = u"genesis 输出程序异常中断，请手动输出！<br>"                                
                                    self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                            u"Status = '{0}'".format(u"输出异常"),
                                                            u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                                           condition="id={0}".format(output_id))
                                    #try:
                                        #shutil.rmtree(dest_net_path)
                                    #except:
                                        #pass                                    
                                else:                                        
                                    self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出完成"),
                                                            u"Status = '已下发'"], condition="id={0}".format(output_id))                                     
                                    
                                end_calc_time = time.time()
                                seconds = end_calc_time - start_calc_time
                                time_log = u"genesis总耗时:{0}分钟 <br>".format(round(seconds/60, 1))
                                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(time_log),
                                                        "OutputTime = now()", ],
                                                       condition="id={0}".format(output_id))                                    
                                        
                            for filename in os.listdir(tmp_dir):
                                filepath = os.path.join(tmp_dir,filename)
                                if "success_{0}".format(output_id) in filename:
                                    os.unlink(filepath)
                                
                                if "finish_{0}".format(output_id) in filename:
                                    os.unlink(filepath)
                                    
                                if "calc_time_{0}".format(output_id) in filename:
                                    os.unlink(filepath)                                  
                                    
                            if os.path.exists(output_dir):
                                shutil.rmtree(output_dir)
                                
                            if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, jobname)):
                                os.unlink("{0}/outputing_{1}.log".format(tmp_dir, jobname))
                                
                        
                    if "not_import_tgz" not in args:    
                        run_scripts = "{0}/del_job.py no_gui".format(script_dir)
                        if "192.168.19.243" not in localip[2] and "test" not in sys.argv:
                            os.system("python {0}/{2}.py {1}".format(script_dir, run_scripts, login_soft_script_name))
                    
            except Exception, e:
                print(e)
                
            if args:
                break
            
            time.sleep(60)
            
    def run_create_barcode_xml_output_type(self, *args):
        """喷印二维码XML文件自动生成 20241211 by lyh"""
        
        while True:
            try:             
                dic_condition = {"Facotry": "S01H1","type": u"临时","isOutput": "Y",}
                param = []          
                for k, v in dic_condition.iteritems():
                    param.append(u"{0}='{1}'".format(k, v))        
                param.append("(OutputStatus is null or OutputStatus = '')")
                param.append(u"(data_type = '喷印二维码XML')")   
                
                if param:            
                    data_info = self.get_mysql_data(condtion=" and ".join(param))
                    #测试
                    if args:                        
                        data_info = self.get_mysql_data(condtion="id = {0}".format(*args))
                else:
                    data_info = []
                
                all_ouput_jobs = []
                dic_job_id = {}
                for info in sorted(data_info, key=lambda x: (x["workLevel"] * -1, x["appTime"])):
                    
                    if info["Job"] not in all_ouput_jobs:
                        all_ouput_jobs.append(info["Job"])
                        
                    if not dic_job_id.has_key(info["Job"].lower()):
                        dic_job_id[info["Job"].lower()] = [str(info["id"])]
                    else:
                        dic_job_id[info["Job"].lower()].append(str(info["id"]))                    
    
                print(all_ouput_jobs)
                for name in all_ouput_jobs:            
                    name = name.lower()
                    
                    if "not_import_tgz" in args:
                        res = 1                        
                    else:                    
                        print(os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)))
                        if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)):
                            time.sleep(5)
                            continue
                        
                        # tgz_file_path = ur"\\192.168.2.174\GCfiles\Silk\劲鑫文字喷墨\{0}系列\{1}_jinxin.tgz".format(name[1:4], name)
                        #if not os.path.exists(tgz_file_path):
                            #print(name, "tgz_path:not exists!")
                            #time.sleep(30)
                            #continue
                        # tgz_file_path = ur"\\192.168.2.174\GCfiles\Silk\临时劲鑫文字喷墨\2024年\12月\12.26\cd1024e7213b8-01\{0}_jinxin.tgz".format(name)
                        res = self.import_tgz(name, dic_job_id[name])
                        #if res and os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)):
                            #self.update_mysql_data([u"OutputStatus = ''",
                                                    #u"Status = ''",
                                                    #u"AlarmLog = ''"],
                                                   #condition="id in ({0})".format(",".join(dic_job_id[name])))
                            #time.sleep(5)
                            #continue                        
                    
                    print(res, os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)))
                    
                    if res:
                        
                        with open("{0}/outputing_{1}.log".format(tmp_dir, name), "w") as f:
                            f.write("running")
                        
                        for info in sorted(data_info, key=lambda x: x["workLevel"] * -1):
                            start_calc_time = time.time()
                            jobname = info["Job"].lower().strip()
                            if jobname != name:
                                continue
                            
                            output_id = info["id"]

                            self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出中"),
                                                    u"Status = '{0}'".format(u"输出中"),
                                                    u"AlarmLog = ''"],
                                                   condition="id={0}".format(output_id))
                            
                            dest_net_path = info["OutputPath"]

                            try:
                                os.makedirs(dest_net_path)
                            except Exception, e:
                                print(e)
                            
                            if not os.path.exists(dest_net_path):                                
                                log = u"genesis中创建输出路径失败{0} <br>".format(dest_net_path)
                                self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常"),
                                                        u"Status = '{0}'".format(u"输出异常"),
                                                        u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                                       condition="id={0}".format(output_id))                                
                                continue                                                                             
                            
                            run_scripts = os.path.join(script_dir, "Auto_Engineer_Output_Tools.py")
                            
                            success_file = os.path.join(tmp_dir, "success_{0}.log".format(output_id))
                            os.system("rm -rf {0}".format(success_file))
                            error_file = os.path.join(tmp_dir, "success_{0}_check_error.log".format(output_id))           
                            os.system("rm -rf {0}".format(error_file))
                            
                            data_type = "auto_create_barcode_xml_files"
                            
                            os.environ["JOB"] = jobname
                                        
                            os.system("python %s/%s.py %s %s %s %s %s %s" %
                                      (script_dir,login_soft_script_name, run_scripts, data_type, jobname, output_id, name, "no_gui"))
                                        
                            
                            if os.path.exists(error_file):                                
                                self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                        u"Status = '{0}'".format(u"输出异常"),
                                                        ],
                                                       condition="id={0}".format(output_id))
                                #try:
                                    #shutil.rmtree(dest_net_path)
                                #except:
                                    #pass
                            
                            else:
                                
                                if not os.path.exists(success_file):
                                    log = u"genesis 输出程序异常中断，请手动输出！<br>"                                
                                    self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                            u"Status = '{0}'".format(u"输出异常"),
                                                            u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                                           condition="id={0}".format(output_id))
                                    #try:
                                        #shutil.rmtree(dest_net_path)
                                    #except:
                                        #pass                                    
                                else:                                        
                                    self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出完成"),
                                                            u"Status = '已下发'"], condition="id={0}".format(output_id))                                     
                                    
                                end_calc_time = time.time()
                                seconds = end_calc_time - start_calc_time
                                time_log = u"genesis总耗时:{0}分钟 <br>".format(round(seconds/60, 1))
                                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(time_log),
                                                        "OutputTime = now()", ],
                                                       condition="id={0}".format(output_id))                                    
                                        
                            for filename in os.listdir(tmp_dir):
                                filepath = os.path.join(tmp_dir,filename)
                                if "success_{0}".format(output_id) in filename:
                                    os.unlink(filepath)
                                
                                if "finish_{0}".format(output_id) in filename:
                                    os.unlink(filepath)
                                    
                                if "calc_time_{0}".format(output_id) in filename:
                                    os.unlink(filepath) 
                                
                            if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, jobname)):
                                os.unlink("{0}/outputing_{1}.log".format(tmp_dir, jobname))                                
                        
                    if "not_import_tgz" not in args:    
                        run_scripts = "{0}/del_job.py no_gui".format(script_dir)
                        if "192.168.19.243" not in localip[2] and "test" not in sys.argv:
                            os.system("python {0}/{2}.py {1}".format(script_dir, run_scripts, login_soft_script_name))
                    
            except Exception, e:
                print(e)
                
            if args:
                break
            
            time.sleep(60)

    def sender_dingtalk_message(self, *args):
        """钉钉消息推送"""
        
        num = 0
        while True:            
            try:   
                dic_condition = {"Facotry": "S01H1","isOutput": "Y",}
                param = []          
                for k, v in dic_condition.iteritems():
                    param.append(u"{0}='{1}'".format(k, v))        

                param.append(u"Status = '输出异常'")         
                param.append("TIMESTAMPDIFF(MINUTE, OutputTime,now()) < 5 ")       
                
                if param:            
                    data_info = self.get_mysql_data(condtion=" and ".join(param))
                else:
                    data_info = []

                
                output_ids = [info["id"] for info in data_info]
                if output_ids:
                    os.system("python {0}/send_message_to_dingding_group.py {1}".format(script_dir, " ".join(output_ids)))
                    
            except Exception as e:
                print(e)
            
            time.sleep(300)
            
            num += 1
            if num > 11:
                break

    def run_delete_scale_drill_output_type(self, *args):
        """删除钻带拉伸作废记录的输出文件"""
        
        num = 0
        while True:            
            try:
                self.uploading_test_point_info_record()
                
                self.uploading_zy_measure_coordinate_info_record()
                
                dic_condition = {"Facotry": "S01H1","type": u"临时","isOutput": "N",}
                param = []          
                for k, v in dic_condition.iteritems():
                    param.append(u"{0}='{1}'".format(k, v))        
                param.append(u"(data_type = '临时钻带' or data_type = '开料钻申请' or data_type = '临时锣带')")
                param.append(u"(OutputStatus <> '已删除旧资料' or OutputStatus is null)")     
                param.append("appTime > '2024-01-29 10:00:00'")      
                param.append("datediff(now(),apptime) < 2 ")       
                
                if param:            
                    data_info = self.get_mysql_data(condtion=" and ".join(param))
                else:
                    data_info = []

                for info in sorted(data_info, key=lambda x: (x["workLevel"] * -1, x["appTime"])):
                    jobname = info["Job"].lower().strip()                    
                    zs_code = info["ZsCode"]
                    if zs_code.startswith("N"):
                        zs_code = "zs"                     
                    scale_x = float(info["XzsRatio"])
                    scale_y = float(info["YzsRatio"])
                    output_id = info["id"]
                    dest_net_path = info["OutputPath"]
                    if u"临时钻带拉伸测试" in dest_net_path:
                        dest_net_path = ur"\\192.168.2.174\GCfiles\Program\Mechanical\压合涨缩钻带\{1}系列\{0}".format(jobname, jobname[1:4])                    
                    #if dest_net_path is None:
                        #dest_net_path = ur"\\192.168.2.57\临时文件夹\系列资料临时存放区\03.CAM制作资料暂放（勿删）\000勿删\临时钻带拉伸测试\{1}系列\{0}".format(jobname, jobname[1:4])
                        
                    dest_net_path = os.path.join(os.path.dirname(dest_net_path) ,zs_code+ "-"+jobname)
                    
                    scale_text = ""
                    if scale_y != 1:
                        scale_text += " L{0}".format(scale_y)
                    if scale_x != 1:
                        scale_text += " W{0}".format(scale_x)
                        
                    if os.path.exists(dest_net_path):                            
                        for name in os.listdir(dest_net_path):
                            filepath = os.path.join(dest_net_path, name)
                            lines = file(filepath).readlines()
                            if scale_text and scale_text.strip() in "".join(lines):                                
                                shutil.rmtree(dest_net_path)
                                now_time = self.get_current_format_time()
                                print("delete job--->", jobname, now_time)
                                with open("d:/drill_info/delete_scale_drill.log", "a") as f:
                                    f.write(jobname+"---->"+now_time+"\n")                                 
                                break                            
                    else:
                        for dirname in os.listdir(os.path.dirname(dest_net_path)):
                            dirpath = os.path.join(os.path.dirname(dest_net_path), dirname)
                            if zs_code+ "-"+jobname in dirname and \
                               info["OutputTime"] is not None and \
                               time.mktime(info["OutputTime"].timetuple()) <= os.path.getmtime(dirpath):
                                for name in os.listdir(dirpath):
                                    filepath = os.path.join(dirpath, name)
                                    lines = file(filepath).readlines()
                                    if scale_text and scale_text.strip() in "".join(lines):               
                                        shutil.rmtree(dirpath)
                                        now_time = self.get_current_format_time()
                                        print("delete job--->", jobname, now_time)
                                        with open("d:/drill_info/delete_scale_drill.log", "a") as f:
                                            f.write(jobname+"---->"+now_time+"\n")                                          
                                        break
                                        
                    self.update_mysql_data([u"OutputStatus = '{0}'".format(u"已删除旧资料"),
                                            u"Status = '{0}'".format(u"已作废"),
                                            u"AlarmLog = ''"],
                                           condition="id={0}".format(output_id))
                    
                    os.system("rm -rf {0}".format("{0}/outputing_{1}.log".format(tmp_dir, jobname)))
                    
            except Exception as e:
                print(e)
            
            time.sleep(60)
            
            num += 1
            if num > 60:
                break

    def run_clear_scale_drill_output_type(self, *args):
        """清除钻带异常输出状态 重新输出"""
        
        num = 0
        while True:            
            try:   
                dic_condition = {"Facotry": "S01H1","type": u"临时","isOutput": "Y",}
                param = []          
                for k, v in dic_condition.iteritems():
                    param.append(u"{0}='{1}'".format(k, v))        
                param.append(u"(data_type = '临时钻带' or data_type = '开料钻申请' or data_type = '临时锣带')")
                param.append(u"(Status = '输出异常' and alarmlog like '%%tgz资料不存在%%')")     
                param.append("appTime > '2024-01-29 10:00:00'")      
                param.append("datediff(now(),apptime) < 30 ")       
                
                if param:            
                    data_info = self.get_mysql_data(condtion=" and ".join(param))
                else:
                    data_info = []

                for info in sorted(data_info, key=lambda x: (x["workLevel"] * -1, x["appTime"])):
                    jobname = info["Job"].lower().strip()
                    output_id = info["id"]
                    data_type = info["data_type"]
                    if data_type in (u'临时钻带' , u'开料钻申请'):                        
                        if sys.platform == "win32":            
                            import_job_path = ur"//192.168.2.174/GCfiles/HDI全套tgz/{0}系列/{1}.tgz".format(jobname[1:4], jobname)
                            if not os.path.exists(import_job_path):
                                import_job_path = ur"//192.168.2.174/GCfiles/HDI全套tgz/{0}系列/{1}-inn.tgz".format(jobname[1:4], jobname)
                        else:            
                            import_job_path = u"/windows/174.tgz/{0}系列/{1}.tgz".format(jobname[1:4].upper(), jobname)
                            if not os.path.exists(import_job_path):
                                import_job_path = u"/windows/174.tgz/{0}系列/{1}-inn.tgz".format(jobname[1:4].upper(), jobname)
                    else:
                        import_job_path = ur"//192.168.2.172/GCfiles/锣带备份/锣带备份/{0}系列/{1}/{1}.tgz".format(jobname[1:4].upper(), jobname)                    
                        
                    if os.path.exists(import_job_path):                        
                        self.update_mysql_data([u"OutputStatus = ''",
                                                u"Status = ''",
                                                u"AlarmLog = ''"],
                                               condition="id={0}".format(output_id))
                    
                self.auto_clear_warning_log()
                
                os.system("python {0}/send_message_to_dingding_group.py {1}".format(script_dir, "test_point"))
                
                os.system("python {0}/send_message_to_dingding_group.py {1}".format(script_dir, "cam_make"))
                
                os.system("python {0}/send_message_to_dingding_group.py {1}".format(script_dir, "imgkit"))
                
            except Exception as e:
                print(e)
            
            time.sleep(600)
            
            num += 1
            if num > 6:
                break
    
    def recycle_drill_file(self, **kwargs):
        """回收钻带"""
        if kwargs["recycle_type"] == "drill":
            recycle_path = kwargs["path"]
            print(recycle_path)
            dest_path = ur"D:\recycle_file\{0}".format(os.path.basename(recycle_path))
            if os.path.exists(dest_path):
                #log = u"已回收钻带{0}".format(os.path.split(recycle_path)[1])
                #dic_condition = {"Facotry": "S01H1","type": u"临时","isOutput": "Y",}
                #param = []          
                #for k, v in dic_condition.iteritems():
                    #param.append(u"{0}='{1}'".format(k, v))        
                #param.append(u"(data_type = '临时钻带' or data_type = '开料钻申请' or data_type = '临时锣带')")
                #param.append(u"(Status = '已下发' and alarmlog like '%%{0}%%')".format(log))       
                #param.append("TIMESTAMPDIFF(MINUTE,  apptime,now()) < 600 ")
                #try:                    
                    #data_info = self.get_mysql_data(condtion=" and ".join(param))
                    ## print(11111111111111111111111)
                #except:
                    #data_info = ""
                    #pass
                #if not data_info:
                dest_path = dest_path + "_{0}_{1}".format(kwargs["id"], time.time())
                #else:
                    #return
                    
            if os.path.exists(recycle_path):
                for name in os.listdir(recycle_path):
                    if name:                        
                        try:
                            shutil.copytree(recycle_path, dest_path, symlinks=True)
                            shutil.rmtree(recycle_path)
                            log = u"已回收钻带{0}<br>".format(os.path.split(recycle_path)[1])
                            print(3333333333333333333333)
                            try:
                                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                                       condition="id={0}".format(kwargs["id"]))
                            except:
                                pass
                        except Exception as e:
                            return u"回收旧钻带失败，请手动回收后再清除报警日志重新输出！{0}".format(e)
                        break
        
        return None
    
    def auto_clear_warning_log(self):
        """定时清除两小时内的异常日志 重新输出"""
        condition = u"""Facotry='S01H1'
        and type='临时'
        and isOutput='Y'
        -- and (data_type ='临时钻带' or data_type = '开料钻申请' or data_type = '临时锣带') 
        and alarmlog like '%%genesis 输出程序异常中断%%'
        and TIMESTAMPDIFF(MINUTE,  apptime,now()) < 120"""
        
        self.update_mysql_data([u"OutputStatus = ''",
                                u"Status = ''",
                                u"AlarmLog = ''"],
                               condition=condition)
        
        condition = u"""Facotry='S01H1'
        and type='临时'
        and isOutput='Y'
        and OutputStatus ='输出异常(推送消息)'
        and alarmlog is null
        and TIMESTAMPDIFF(MINUTE,  apptime,now()) < 120"""
        
        self.update_mysql_data([u"OutputStatus = ''",
                                u"Status = ''",
                                u"AlarmLog = ''"],
                               condition=condition)          
            
    def run_scale_drill_output_type(self, *args):
        """钻带拉伸工具输出"""
        
        while True:
            try:   
                dic_condition = {"Facotry": "S01H1","type": u"临时","isOutput": "Y",}
                param = []          
                for k, v in dic_condition.iteritems():
                    param.append(u"{0}='{1}'".format(k, v))        
                param.append("(OutputStatus is null or OutputStatus = '')")
                param.append(u"(data_type = '临时钻带' or data_type = '开料钻申请' or data_type = '临时二钻')")
                param.append("appTime > '2024-01-10 00:00:00'")
                param.append(u"appuser <> '锣带输出开发'")       
                
                if param:            
                    data_info = self.get_mysql_data(condtion=" and ".join(param))
                    #测试
                    if args:                        
                        data_info = self.get_mysql_data(condtion="id = {0}".format(*args))
                else:
                    data_info = []
                
                all_ouput_jobs = []
                dic_job_id = {}
                for info in sorted(data_info, key=lambda x: (x["workLevel"] * -1, x["appTime"])):
                    
                    if info["Job"] not in all_ouput_jobs:
                        all_ouput_jobs.append(info["Job"])
                        
                    if not dic_job_id.has_key(info["Job"].lower()):
                        dic_job_id[info["Job"].lower()] = [str(info["id"])]
                    else:
                        dic_job_id[info["Job"].lower()].append(str(info["id"]))
                
                error_recycle_jobs = []
                for name in all_ouput_jobs:            
                    name = name.lower()
                    for info in sorted(data_info, key=lambda x: x["workLevel"] * -1):
                        start_calc_time = time.time()
                        jobname = info["Job"].lower().strip()
                        if jobname != name:                              
                            continue
                        
                        output_id = info["id"]
                        zs_code = info["ZsCode"]
                        if zs_code.startswith("N"):
                            zs_code = "zs"                            
                        a, b = info["OutLayer"].split(";")
                        dest_net_path = info["OutputPath"]      
                        drill_name = info["dataName"]                          
                        if u"临时钻带拉伸测试" in dest_net_path:
                            dest_net_path = ur"\\192.168.2.174\GCfiles\Program\Mechanical\压合涨缩钻带\{1}系列\{0}".format(jobname, jobname[1:4])                        
                        
                        dest_net_path = os.path.join(os.path.dirname(dest_net_path) ,zs_code+ "-"+jobname)
                        if drill_name in [u"盲埋孔", "Drill", u"塞孔铝片", u"树脂铝片"]:
                            mrpnames = [x["MRPNAME"] for x in get_inplan_mrp_info(jobname.upper(),"1=1")]
                            # print(mrpnames)
                            suffix = []
                            for mrpname in mrpnames:
                                if "-" in mrpname and "{0}{1}".format(str(int(a[1:])).rjust(2, "0"), str(int(b[1:])).rjust(2, "0")) in mrpname.split("-")[1]:
                                    suffix.append(mrpname.split("-")[1])
                                    
                            if len(set(suffix)) == 1:                                    
                                dest_net_path = os.path.join(os.path.dirname(dest_net_path) ,zs_code+ "-"+jobname+"-"+suffix[0])
                                
                        # print(jobname,11111111111111111111111111111111111111111111111111, )
                        if info["remark"] == u"重新下发":
                            # print(jobname, 22222222222222222222222222222222222222222222)
                            res = self.recycle_drill_file(path=dest_net_path, recycle_type="drill", **info)
                            time.sleep(2)
                            if res:
                                self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                        u"Status = '{0}'".format(u"输出异常"),
                                                        u"AlarmLog = concat(AlarmLog,'{0}')".format(res)],
                                                       condition="id={0}".format(output_id))
                                error_recycle_jobs.append(jobname)
                            break
                # time.sleep(60)
                print(all_ouput_jobs)
                for name in all_ouput_jobs:            
                    name = name.lower()
                    
                    if name in error_recycle_jobs:
                        continue
                    
                    if "not_import_tgz" in args:
                        res = 1                        
                    else:                    
                        print(os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)))
                        if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)):
                            time.sleep(5)
                            continue
                        
                        # 测试
                        # import_tgz_path = ur"\\192.168.2.126\workfile\lyh\hb0612ob006a1-test\hb0612ob006a1-test.tgz"
                        
                        res = self.import_tgz(name, dic_job_id[name])
                        #if res and os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)):
                            #self.update_mysql_data([u"OutputStatus = ''",
                                                    #u"Status = ''",
                                                    #u"AlarmLog = ''"],
                                                   #condition="id in ({0})".format(",".join(dic_job_id[name])))
                            #time.sleep(5)
                            #continue
                    
                    print(res, os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)))
                    
                    if res:
                    
                        with open("{0}/outputing_{1}.log".format(tmp_dir, name), "w") as f:
                            f.write("running")
                        
                        recycle_job_info = []
                        
                        for info in sorted(data_info, key=lambda x: x["workLevel"] * -1):
                            start_calc_time = time.time()
                            jobname = info["Job"].lower().strip()
                            if jobname != name:                              
                                continue
                            
                            output_id = info["id"]
                            zs_code = info["ZsCode"]
                            if zs_code.startswith("N"):
                                zs_code = "zs"                            
                            a, b = info["OutLayer"].split(";")
                            drill_name = info["dataName"]
                            self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出中"),
                                                    u"Status = '{0}'".format(u"输出中"),
                                                    u"AlarmLog = ''"],
                                                   condition="id={0}".format(output_id))                            
                            
                            dest_net_path = info["OutputPath"]                            
                            if u"临时钻带拉伸测试" in dest_net_path:
                                dest_net_path = ur"\\192.168.2.174\GCfiles\Program\Mechanical\压合涨缩钻带\{1}系列\{0}".format(jobname, jobname[1:4])
                            # print([dest_net_path])
                            # print(drill_name)
                            # print(localip[2])
                            if "192.168.19.243" in localip[2]:
                                # dest_net_path = u"d:/tmp/{1}系列/{0}".format(jobname, jobname[1:4])
                                dest_net_path = ur"\\192.168.2.57\临时文件夹\系列资料临时存放区\03.CAM制作资料暂放（勿删）\000勿删\临时钻带拉伸测试\{1}系列\{0}".format(jobname.upper(), jobname[1:4].upper())
                                
                            dest_net_path = os.path.join(os.path.dirname(dest_net_path) ,zs_code+ "-"+jobname)
                            if drill_name in [u"盲埋孔", "Drill", u"塞孔铝片", u"树脂铝片"]:
                                mrpnames = [x["MRPNAME"] for x in get_inplan_mrp_info(jobname.upper(),"1=1")]
                                # print(mrpnames)
                                suffix = []
                                for mrpname in mrpnames:
                                    if "-" in mrpname and "{0}{1}".format(str(int(a[1:])).rjust(2, "0"), str(int(b[1:])).rjust(2, "0")) in mrpname.split("-")[1]:
                                        suffix.append(mrpname.split("-")[1])
                                        
                                if len(set(suffix)) == 1:                                    
                                    dest_net_path = os.path.join(os.path.dirname(dest_net_path) ,zs_code+ "-"+jobname+"-"+suffix[0])
                            
                            if sys.platform != "win32":                                
                                dest_net_path = dest_net_path.replace("\\", "/")
                                dest_net_path = dest_net_path.replace(ur"//192.168.2.57/临时文件夹/系列资料临时存放区/", "/windows/33.file/")
                                dest_net_path = dest_net_path.replace(ur"//192.168.2.174/GCfiles/", "/windows/174.file/")
                                
                            #try:
                                #shutil.rmtree(dest_net_path)
                            #except Exception as e:
                                #print(e)
                                
                            #if info["remark"] == u"重新下发" and jobname + "_" + info["ZsCode"] not in recycle_job_info:
                                #res = self.recycle_drill_file(path=dest_net_path, recycle_type="drill", **info)
                                #time.sleep(2)
                                #recycle_job_info.append(jobname + "_" + info["ZsCode"])
                                #if res:
                                    #self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                            #u"Status = '{0}'".format(u"输出异常"),
                                                            #u"AlarmLog = concat(AlarmLog,'{0}')".format(res)],
                                                           #condition="id={0}".format(output_id))
                                    ##if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, jobname)):
                                        ##os.unlink("{0}/outputing_{1}.log".format(tmp_dir, jobname))                                    
                                    #continue                                
                              
                            try:
                                os.makedirs(dest_net_path)
                            except Exception as e:
                                print(e)
                            
                            if not os.path.exists(dest_net_path):                                
                                log = u"genesis中创建输出路径失败{0} <br>".format(dest_net_path)
                                self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                        u"Status = '{0}'".format(u"输出异常"),
                                                        u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                                       condition="id={0}".format(output_id))
                                #if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, jobname)):
                                    #os.unlink("{0}/outputing_{1}.log".format(tmp_dir, jobname))                                
                                continue
                            
                            output_dir = "{0}/{1}/{2}/{3}".format(tmp_dir, jobname, "drill", output_id)
                            if os.path.exists(output_dir):
                                shutil.rmtree(output_dir)
                            
                            try:                                
                                os.makedirs(output_dir)
                            except Exception, e:
                                print(e)
                                pass                                                    
                            
                            run_scripts = os.path.join(script_dir, "Auto_Engineer_Output_Tools.py")
                            
                            success_file = os.path.join(tmp_dir, "success_{0}.log".format(output_id))
                            os.system("rm -rf {0}".format(success_file))
                            error_file = os.path.join(tmp_dir, "success_{0}_check_error.log".format(output_id))           
                            os.system("rm -rf {0}".format(error_file))                         
    
                            data_type = "output_scale_drill_file"
                            
                            os.environ["JOB"] = jobname
                            if "gui_run" in args:
                                os.system("python %s/%s.py %s %s %s %s %s" %
                                          (script_dir,login_soft_script_name, run_scripts, data_type, jobname, output_id, "gui_run"))                               
                            else:
                                os.system("python %s/%s.py %s %s %s %s %s" %
                                          (script_dir,login_soft_script_name, run_scripts, data_type, jobname, output_id, "no_gui"))                                
                            
                            if os.path.exists(error_file):                                
                                self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                        u"Status = '{0}'".format(u"输出异常"),
                                                        ],
                                                       condition="id={0}".format(output_id))
                                #try:
                                    #shutil.rmtree(dest_net_path)
                                #except:
                                    #pass
                            
                            else:
                                
                                if not os.path.exists(success_file):
                                    log = u"genesis 输出程序异常中断，请手动输出！<br>"                                
                                    self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                            u"Status = '{0}'".format(u"输出异常"),
                                                            u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                                           condition="id={0}".format(output_id))
                                    #try:
                                        #shutil.rmtree(dest_net_path)
                                    #except:
                                        #pass                                    
                                else:
                                    
                                    arraylist_file = []
                                    for filename in os.listdir(output_dir):
                                        filepath = os.path.join(output_dir, filename)
                                        shutil.copy(filepath, dest_net_path+"/"+zs_code.lower()+"-"+filename)
                                        arraylist_file.append(dest_net_path+"/"+zs_code.lower()+"-"+filename)
                                    
                                    self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}<br>')".format("<br>".join(arraylist_file).replace("\\", "/"))],
                                                           condition="id={0}".format(output_id))
                                    
                                    if info["data_type"] == u"临时钻带":
                                        url = "http://192.168.2.122/HdiZs-Base/api/zsInPlanUpdate/Update_resizeDrill?Id={0}&Job={1}"
                                    elif info["data_type"] == u"临时二钻":
                                        url = "http://192.168.2.122/HdiZs-Base/api/zsInPlanUpdate/Update_SecondDrill?Id={0}&job={1}"
                                    else:
                                        url = "http://192.168.2.122/HdiZs-Base/api/zsInPlanUpdate/Update_InnerDrill?Id={0}&Job={1}"
                                        
                                    if info["data_type"] <> u"临时二钻":
                                        responsere=requests.get(url=url.format(info["SourceId"], info["Job"]))
                                        print "-------->", responsere.json()
                                        if responsere.json()['msg'] == u"修改成功":                                        
                                            self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出完成"),
                                                                    u"Status = '已下发'"], condition="id={0}".format(output_id))
                                        else:
                                            if info["remark"] == u"重新下发":
                                                self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出完成"),
                                                                        u"Status = '已下发'"], condition="id={0}".format(output_id))
                                            else:
                                                self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                                        u"Status = '输出异常'",
                                                                        u"AlarmLog = concat(AlarmLog,'{0}')".format(responsere.json()['msg'])],
                                                                       condition="id={0}".format(output_id))
                                    else:
                                        self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出完成"),
                                                                u"Status = '输出完成'"], condition="id={0}".format(output_id))                                        
                                    
                                end_calc_time = time.time()
                                seconds = end_calc_time - start_calc_time
                                time_log = u"<br>genesis总耗时:{0}分钟 <br>".format(round(seconds/60, 1))
                                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(time_log),
                                                        "OutputTime = now()", ],
                                                       condition="id={0}".format(output_id))                                    
                                        
                            for filename in os.listdir(tmp_dir):
                                filepath = os.path.join(tmp_dir,filename)
                                if "success_{0}".format(output_id) in filename:
                                    os.unlink(filepath)
                                
                                if "finish_{0}".format(output_id) in filename:
                                    os.unlink(filepath)
                                    
                                if "calc_time_{0}".format(output_id) in filename:
                                    os.unlink(filepath)                                  
                                    
                            if os.path.exists(output_dir):
                                shutil.rmtree(output_dir)                                
                        
                    if "not_import_tgz" not in args:
                        time.sleep(10)
                        run_scripts = "{0}/del_job.py no_gui".format(script_dir)
                        if "192.168.19.243" not in localip[2]:
                            os.system("python {0}/{2}.py {1}".format(script_dir, run_scripts, login_soft_script_name))
                            
                        if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)):
                            os.unlink("{0}/outputing_{1}.log".format(tmp_dir, name))                            
                    
            except Exception, e:
                print(e)
                
            if args:
                break
            
            time.sleep(60)
            
    def get_outputing_other_toolings(self, data_type,jobname):
        """检测是否有其他工具再输出中"""
        param = []     
        if data_type == u"钻带":
            dic_condition = {"Facotry": "S01H1","type": u"临时","isOutput": "Y",}                 
            for k, v in dic_condition.iteritems():
                param.append(u"{0}='{1}'".format(k, v))        
            param.append(u"data_type = '临时钻带' and (OutputStatus is null or OutputStatus = '' or OutputStatus = '输出中')")
            param.append("TIMESTAMPDIFF(MINUTE,  apptime,now()) < 60")
            param.append("Job = '{0}'".format(jobname))

        if data_type == u"gerber":
            dic_condition = {"Facotry": "S01H1","type": u"正式","isOutput": "Y",}                 
            for k, v in dic_condition.iteritems():
                param.append(u"{0}='{1}'".format(k, v))        
            param.append(u"data_type <> '输出GB资料' and (OutputStatus is null or OutputStatus = '' or OutputStatus = '输出中')")
            param.append("TIMESTAMPDIFF(MINUTE,  apptime,now()) < 60")
            param.append("Job = '{0}'".format(jobname))
                
        if param:            
            data_info = self.get_mysql_data(condtion=" and ".join(param))
            if data_info:
                return True
            return False
        

    def run_genesis_scale_rout_output_type(self, *args):
        """锣带自动拉伸资料工具输出"""
        
        while True:
            try:             
                dic_condition = {"Facotry": "S01H1","type": u"临时","data_type": u"临时锣带","isOutput": "Y",}
                param = []          
                for k, v in dic_condition.iteritems():
                    param.append(u"{0}='{1}'".format(k, v))        
                param.append("(OutputStatus is null or OutputStatus = '')")
                # param.append(u"dataName = '锣带资料'")                
                
                if "test" in args:
                    dic_condition = {"Facotry": "S01H1","type": u"临时","isOutput": "Y",}
                    param = []          
                    for k, v in dic_condition.iteritems():
                        param.append(u"{0}='{1}'".format(k, v))        
                    param.append(u"data_type = '临时锣带'")
                    param.append(u"appTime > '2024-05-01 00:00:00' and OutputStatus <> '输出完成'")
                    # param.append(u"(OutputTime < '2024-05-10 00:00:00' or ( OutputTime > '2024-05-10 00:00:00' and OutputStatus <> '输出完成'))")
                    # param.append("OutputStatus <> '输出完成'")
                
                if param:            
                    data_info = self.get_mysql_data(condtion=" and ".join(param))
                    #测试
                    if args and "test" not in args and args[0] != "gui_run" :                        
                        data_info = self.get_mysql_data(condtion="id = {0}".format(*args))
                else:
                    data_info = []
                
                all_ouput_jobs = []
                dic_job_id = {}
                wait_time = 1
                for info in sorted(data_info, key=lambda x: (x["workLevel"] * -1, x["appTime"])):
                    
                    #res = self.get_outputing_other_toolings(u"钻带", info["Job"])
                    #if res:
                        #continue
                    
                    #if info["quadrant"] in [u"一锣", u"半孔锣", u"CCD精锣", u"PTH锣",u"控深铣",]:
                        #continue
                    
                    if info["Job"] not in all_ouput_jobs:
                        all_ouput_jobs.append(info["Job"])
                        
                    if not dic_job_id.has_key(info["Job"].lower()):
                        dic_job_id[info["Job"].lower()] = [str(info["id"])]
                    else:
                        dic_job_id[info["Job"].lower()].append(str(info["id"]))
                        
                    if info["workLevel"] == 0:
                        wait_time = 0
    
                #因临时钻带跟临时锣带会同时生成 临时锣带资料不急 故这里等待3分钟
                #if not args or not wait_time:                    
                    #time.sleep(180)
                
                print(all_ouput_jobs)
                for name in all_ouput_jobs:
                    
                    name = name.lower()
                    
                    if "not_import_tgz" in args:
                        res = 1                        
                    else:
                        print(os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)))
                        if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)):
                            time.sleep(5)
                            continue

                        import_tgz_path = ur"//192.168.2.172/GCfiles/锣带备份/锣带备份/{0}系列/{1}/{1}.tgz".format(name[1:4].upper(), name)
                        res = self.import_tgz(name, dic_job_id[name], tgz_import_path=import_tgz_path)
                        #if res and os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)):
                            #self.update_mysql_data([u"OutputStatus = ''",
                                                    #u"Status = ''",
                                                    #u"AlarmLog = ''"],
                                                   #condition="id in ({0})".format(",".join(dic_job_id[name])))
                            #time.sleep(5)
                            #continue
                            
                    # os.environ["GENESIS_EDIR"] = "d:/genesis/e105"
                    print(res, os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)))                    
                    if res:
                    
                        with open("{0}/outputing_{1}.log".format(tmp_dir, name), "w") as f:
                            f.write("running")
                            
                        start_calc_time = time.time()
                        
                        for info in sorted(data_info, key=lambda x: x["workLevel"] * -1):
                            
                            jobname = info["Job"].lower().strip()
                            if jobname != name:
                                continue
                            
                            output_id = info["id"]
                            # output_layers = [x for x in info["OutLayer"].split(";") if x.strip()]
                            
                            zs_code = info["ZsCode"]
                            if zs_code.startswith("N"):
                                zs_code = "zs"
                            
                            self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出中"),
                                                    u"Status = '{0}'".format(u"输出中"),
                                                    u"AlarmLog = ''"],
                                                   condition="id={0}".format(output_id))                            
                            
                            dest_net_path = info["OutputPath"]                            
                            if u"成型锣带资料" not in dest_net_path and info["dataName"] == u"锣带资料":                                
                                dest_net_path = ur"\\192.168.2.174\GCfiles\CNC\成型锣带资料\涨缩程式\{1}系列\{0}".format(jobname.upper(), jobname[1:4].upper())
                            # dest_net_path = os.path.join(os.path.dirname(dest_net_path) ,zs_code+ "-"+jobname)                                    
                            
                            if "192.168.19.243" in localip[2]:
                                dest_net_path = ur"\\192.168.2.57\临时文件夹\系列资料临时存放区\03.CAM制作资料暂放（勿删）\000勿删\临时锣带拉伸测试\{1}系列\{0}".format(jobname.upper(), jobname[1:4].upper())
                            try:
                                os.makedirs(dest_net_path)
                            except Exception as e:
                                print(e)
                                                                
                            
                            if not os.path.exists(dest_net_path):                                
                                log = u"Linux中创建输出路径失败{0} <br>".format(dest_net_path)
                                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)], condition="id={0}".format(output_id))                    
                                continue
                            
                            output_dir = "{0}/{1}/{2}/{3}".format(tmp_dir, jobname, "rout", output_id)
                            if os.path.exists(output_dir):
                                shutil.rmtree(output_dir)
                            
                            try:                                
                                os.makedirs(output_dir)
                            except Exception, e:
                                print(e)
                                pass
                            

                            run_scripts = os.path.join(script_dir, "Auto_Engineer_Output_Tools.py")
                            data_type = "output_scale_rout_file"

                            success_file = os.path.join(tmp_dir, "success_{0}.log".format(output_id))
                            os.system("rm -rf {0}".format(success_file))
                            error_file = os.path.join(tmp_dir, "success_{0}_check_error.log".format(output_id))           
                            os.system("rm -rf {0}".format(error_file))
                            
                            os.environ["JOB"] = jobname
                            if "gui_run" in args:
                                try:                                    
                                    app = Application(backend="win32").connect(title_re=".*Toolkit.*", timeout=10)
                                    if app.is_process_running():
                                        app.kill()
                                        print("kill---------------->", jobname)                                        
                                    time.sleep(1)                                    
                                except Exception as e:
                                    print(e)
                                
                                os.system("python %s/%s.py %s %s %s %s %s" %
                                          (script_dir,login_soft_script_name, run_scripts, data_type, jobname, output_id, "gui_run"))
                                
                                try:                                    
                                    app = Application(backend="win32").connect(title_re=".*Toolkit.*", timeout=10)
                                    if app.is_process_running():
                                        app.kill()
                                        print("kill---------------->", jobname)
                                    time.sleep(1)        
                                except Exception as e:
                                    print(e)                                
                            else:
                                os.system("python %s/%s.py %s %s %s %s %s" %
                                          (script_dir,login_soft_script_name, run_scripts, data_type, jobname, output_id, "no_gui"))                                
                             
                            if os.path.exists(error_file):
                                log = file(error_file).readlines()
                                try:                                    
                                    self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                            u"Status = '{0}'".format(u"输出异常"),
                                                            u"AlarmLog = concat(AlarmLog,'{0}')".format("<br>".join(log).decode("cp936"))
                                                            ],
                                                           condition="id={0}".format(output_id))
                                except Exception as e:
                                    print(e, 111111)
                                    self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                            u"Status = '{0}'".format(u"输出异常"),
                                                            u"AlarmLog = concat(AlarmLog,'{0}')".format("<br>".join(log).decode("utf8"))
                                                            ],
                                                           condition="id={0}".format(output_id))
                                    
                                #if info["quadrant"] not in [u"一锣", u"半孔锣", u"CCD精锣", u"PTH锣",u"控深铣",]:
                                    #try:
                                        #shutil.rmtree(dest_net_path)
                                    #except:
                                        #pass
                            else:
                                if os.path.exists(success_file):
                                    
                                    arraylist_file = []
                                    for filename in os.listdir(output_dir):
                                        filepath = os.path.join(output_dir,filename)
                                        # if info["quadrant"] in [u"一锣", u"半孔锣", u"CCD精锣", u"PTH锣",u"控深铣",]:
                                        if info["dataName"] == u"产线临时资料":  
                                            shutil.copy(filepath, dest_net_path+"/LS-"+filename)
                                            arraylist_file.append(os.path.join(dest_net_path, "LS-"+filename))
                                        else:
                                            shutil.copy(filepath, dest_net_path)
                                            arraylist_file.append(os.path.join(dest_net_path, filename))
                                        
                                    self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}<br>')".format("<br>".join(arraylist_file).replace("\\", "/"))],
                                                           condition="id={0}".format(output_id))
                                    
                                    ##
                                    # if info["quadrant"] in [u"一锣", u"半孔锣", u"CCD精锣", u"PTH锣",u"控深铣",]:
                                    if info["dataName"] == u"产线临时资料":                                        
                                        url = "http://192.168.2.122/HdiZs-Base/api/zsInPlanUpdate/Update_ResizeCnc?Id={0}&job={1}"                                        
                                        #self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出完成"),
                                                                #u"Status = '输出完成'"], condition="id={0}".format(output_id))
                                    elif info["quadrant"] and u"开料钻申请" in info["quadrant"]:
                                        url = "http://192.168.2.122/HdiZs-Base/api/zsInPlanUpdate/Update_InnerDrill_Rout?Id={0}&job={1}"
                                    else:
                                        url = "http://192.168.2.122/HdiZs-Base/api/zsInPlanUpdate/Update_resizeDrill_Rout?Id={0}&Job={1}"                                    
                                    responsere=requests.get(url=url.format(info["SourceId"], info["Job"]))
                                    if responsere.json()['msg'] == u"修改成功":                                        
                                        self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出完成"),
                                                                u"Status = '已下发'"], condition="id={0}".format(output_id))
                                    else:
                                        if info["remark"] == u"重新下发":
                                            self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出完成"),
                                                                    u"Status = '已下发'"], condition="id={0}".format(output_id))
                                        else:
                                            self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                                    u"Status = '输出异常'",
                                                                    u"AlarmLog = concat(AlarmLog,'{0}')".format(responsere.json()['msg'])],
                                                                   condition="id={0}".format(output_id))
                                                                      
                                else:
                                    log = u"<br>genesis 输出程序异常中断，请手动输出锣带拉伸资料！<br>"                                
                                    self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                            u"Status = '{0}'".format(u"输出异常"),
                                                            u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                                           condition="id={0}".format(output_id))
                                    
                                    #if info["quadrant"] not in [u"一锣", u"半孔锣", u"CCD精锣", u"PTH锣",u"控深铣",]:
                                        #try:
                                            #shutil.rmtree(dest_net_path)
                                        #except:
                                            #pass 
    
                            #if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, jobname)):
                                #os.unlink("{0}/outputing_{1}.log".format(tmp_dir, jobname))
                                
                            for filename in os.listdir(tmp_dir):
                                filepath = os.path.join(tmp_dir,filename)
                                if "success_{0}".format(output_id) in filename:
                                    os.unlink(filepath)
                                
                                if "finish_{0}".format(output_id) in filename:
                                    os.unlink(filepath)
                                    
                                if "calc_time_{0}".format(output_id) in filename:
                                    os.unlink(filepath)
                                    
                                if "{0}_sort_rout_order_cmd".format(jobname) in filename:
                                    os.unlink(filepath)
                                    
                            if os.path.exists(output_dir):
                                shutil.rmtree(output_dir)
                        
                        end_calc_time = time.time()
                        seconds = end_calc_time - start_calc_time
                        time_log = u"<br>genesis总耗时:{0}分钟 <br>".format(round(seconds/60, 2))
                        self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(time_log),
                                                "OutputTime = now()", ],
                                               condition="id={0}".format(output_id))
                    
                    if "not_import_tgz" not in args:                        
                        run_scripts = "{0}/del_job.py no_gui".format(script_dir)
                        if "192.168.19.243" not in localip[2]:
                            os.system("python {0}/{2}.py {1}".format(script_dir, run_scripts, login_soft_script_name))
    
                        if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)):
                            os.unlink("{0}/outputing_{1}.log".format(tmp_dir, name))                            
                            
                    
            except Exception, e:
                print(e)
                
            if args and "test" not in args and args[0] != "gui_run":
                break
            
            time.sleep(60)
            
    def run_test_point_info_output_type(self, *args):
        """阻抗测试点坐标信息自动输出"""
        
        while True:
            try:             
                dic_condition = {"Facotry": "S01H1","type": u"临时","data_type": u"阻抗测点输出","isOutput": "Y",}
                param = []          
                for k, v in dic_condition.iteritems():
                    param.append(u"{0}='{1}'".format(k, v))        
                param.append("(OutputStatus is null or OutputStatus = '')")
                # param.append(u"dataName = '锣带资料'")                
                
                if param:            
                    data_info = self.get_mysql_data(condtion=" and ".join(param))
                    #测试
                    if args:                        
                        data_info = self.get_mysql_data(condtion="id = {0}".format(*args))
                else:
                    data_info = []
                
                all_ouput_jobs = []
                dic_job_id = {}
                wait_time = 1
                for info in sorted(data_info, key=lambda x: (x["workLevel"] * -1, x["appTime"])):
                    
                    #res = self.get_outputing_other_toolings(u"钻带", info["Job"])
                    #if res:
                        #continue
                    
                    #if info["quadrant"] in [u"一锣", u"半孔锣", u"CCD精锣", u"PTH锣",u"控深铣",]:
                        #continue
                    
                    if info["Job"] not in all_ouput_jobs:
                        all_ouput_jobs.append(info["Job"])
                        
                    if not dic_job_id.has_key(info["Job"].lower()):
                        dic_job_id[info["Job"].lower()] = [str(info["id"])]
                    else:
                        dic_job_id[info["Job"].lower()].append(str(info["id"]))
                        
                    if info["workLevel"] == 0:
                        wait_time = 0
    
                #因临时钻带跟临时锣带会同时生成 临时锣带资料不急 故这里等待3分钟
                #if not args or not wait_time:                    
                    #time.sleep(180)
                
                print(all_ouput_jobs)
                for name in all_ouput_jobs:
                    
                    name = name.lower()
                    
                    start_calc_time = time.time()
                    
                    if "not_import_tgz" in args:
                        res = 1                        
                    else:
                        print(os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)))
                        if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)):
                            time.sleep(5)
                            continue

                        import_tgz_path = ur"/windows/33.file/03.CAM制作资料暂放（勿删）/000勿删/a86测点专用夹子/{0}.tgz".format(name)
                        res = self.import_tgz(name, dic_job_id[name], tgz_import_path=import_tgz_path)
                        #if res and os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)):
                            #self.update_mysql_data([u"OutputStatus = ''",
                                                    #u"Status = ''",
                                                    #u"AlarmLog = ''"],
                                                   #condition="id in ({0})".format(",".join(dic_job_id[name])))
                            #time.sleep(5)
                            #continue                        
                    jobname = name
                    print(res, os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)))                    
                    if res:
                    
                        with open("{0}/outputing_{1}.log".format(tmp_dir, name), "w") as f:
                            f.write("running")    
                        
                        for info in sorted(data_info, key=lambda x: x["workLevel"] * -1):
                            
                            jobname = info["Job"].lower().strip()
                            if jobname != name:
                                continue
                            
                            output_id = info["id"]
                            # output_layers = [x for x in info["OutLayer"].split(";") if x.strip()]                            
                            
                            self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出中"),
                                                    u"Status = '{0}'".format(u"输出中"),
                                                    u"AlarmLog = ''"],
                                                   condition="id={0}".format(output_id))                            
                            
                            dest_net_path = info["OutputPath"]
                            # dest_net_path = ur"\\192.168.2.57\临时文件夹\系列资料临时存放区\03.CAM制作资料暂放（勿删）\000勿删\阻抗测点输出\{0}".format(jobname.upper())
                            dest_net_path = dest_net_path.replace("\\", "/")
                            dest_net_path = dest_net_path.replace(ur"//192.168.2.57/临时文件夹/系列资料临时存放区/", "/windows/33.file/")
                            dest_net_path = dest_net_path.replace(ur"//192.168.2.174/GCfiles/", "/windows/174.file/")
                            
                            try:
                                os.makedirs(dest_net_path)
                            except Exception as e:
                                print(e)
                                                                
                            
                            if not os.path.exists(dest_net_path):                                
                                log = u"Linux中创建输出路径失败{0} <br>".format(dest_net_path)
                                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)], condition="id={0}".format(output_id))                    
                                continue
                            
                            for filename in os.listdir(dest_net_path):
                                if ".tgz" in filename or ".csv" in filename or ".png" in filename or "top" in filename or "bot" in filename:
                                    try:
                                        if os.path.isfile(os.path.join(dest_net_path, filename)):                                            
                                            os.unlink(os.path.join(dest_net_path, filename))
                                        else:
                                            shutil.rmtree(os.path.join(dest_net_path, filename))
                                    except :
                                        pass
                                        try:
                                            old = os.path.join(dest_net_path, filename)
                                            new = os.path.join(dest_net_path, filename+"_old.".format(time.time()))
                                            os.rename(old, new)
                                        except:
                                            pass
                            
                            output_dir = "/id/workfile/film/{0}-test".format(jobname)# "{0}/{1}/{2}/{3}".format(tmp_dir, jobname, "test_point", output_id)
                            
                            if os.path.exists(output_dir):
                                shutil.rmtree(output_dir)
                            
                            try:                                
                                os.makedirs(output_dir)
                            except Exception, e:
                                print(e)
                                pass                            

                            run_scripts = os.path.join(script_dir, "Auto_Engineer_Output_Tools.py")
                            data_type = "auto_ouput_test_point_info"

                            success_file = os.path.join(tmp_dir, "success_{0}.log".format(output_id))
                            os.system("rm -rf {0}".format(success_file))
                            error_file = os.path.join(tmp_dir, "success_{0}_check_error.log".format(output_id))           
                            os.system("rm -rf {0}".format(error_file))
                            
                            os.environ["JOB"] = jobname
                            # if "gui_run" in args:
                                
                            os.system("python %s/%s.py %s %s %s %s %s" %
                                      (script_dir,login_soft_script_name, run_scripts, data_type, jobname, output_id, "gui_run"))                                                               
                            #else:
                                #os.system("python %s/%s.py %s %s %s %s %s" %
                                          #(script_dir,login_soft_script_name, run_scripts, data_type, jobname, output_id, "no_gui"))                                
                             
                            if os.path.exists(error_file):
                                log = file(error_file).readlines()
                                try:                                    
                                    self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                            u"Status = '{0}'".format(u"输出异常"),
                                                            u"AlarmLog = concat(AlarmLog,'{0}')".format("<br>".join(log).decode("cp936"))
                                                            ],
                                                           condition="id={0}".format(output_id))
                                except Exception as e:
                                    print(e, 111111)
                                    self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                            u"Status = '{0}'".format(u"输出异常"),
                                                            u"AlarmLog = concat(AlarmLog,'{0}')".format("<br>".join(log).decode("utf8"))
                                                            ],
                                                           condition="id={0}".format(output_id))
                                    
                            else:
                                if os.path.exists(success_file):
                                    
                                    arraylist_file = []
                                    for filename in os.listdir(output_dir):
                                        filepath = os.path.join(output_dir,filename)
                                        print(filename)
                                        try:
                                            if os.path.isfile(filepath):                                                
                                                shutil.copy(filepath, dest_net_path)
                                            else:
                                                dest_net_path_dir = os.path.join(dest_net_path, filename.decode("utf8"))
                                                if os.path.exists(dest_net_path_dir):
                                                    shutil.rmtree(dest_net_path_dir)
                                                shutil.copytree(filepath, dest_net_path_dir)
                                        except Exception as e:
                                            print(e)
                                            win_dir = ur"\\192.168.2.174\GCfiles\Drawing\{0}系列\{1}\MI\阻抗测点\{2}".format(jobname[1:4], jobname, filename.decode("utf8"))
                                            log = u"<br>{0}  文件被打开，无法更新文件，请手动删除此文件！<br>".format(win_dir.replace("\\", "/"))                                
                                            self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                                    u"Status = '{0}'".format(u"输出异常"),
                                                                    u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                                                   condition="id={0}".format(output_id))
                                            
                                        arraylist_file.append(os.path.join(dest_net_path, filename.decode("utf8")))
                                    
                                    #if os.path.exists(os.path.join(dest_net_path, jobname+".tgz")):
                                        #shutil.copy(import_tgz_path, dest_net_path+"/"+jobname+"_{0}.tgz".format(time.time()))
                                    #else:
                                        #shutil.copy(import_tgz_path, dest_net_path)
                                                                                
                                    self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出完成"),
                                                            u"Status = '输出完成'", 
                                                            u"AlarmLog = concat(AlarmLog,'{0}<br>')".format("<br>".join(arraylist_file).replace("\\", "/"))],
                                                           condition="id={0}".format(output_id))                                                                      
                                else:
                                    log = u"<br>incampro 输出程序异常中断，请手动输出阻抗测点资料！<br>"                                
                                    self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                            u"Status = '{0}'".format(u"输出异常"),
                                                            u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                                           condition="id={0}".format(output_id))    
                                
                            for filename in os.listdir(tmp_dir):
                                filepath = os.path.join(tmp_dir,filename)
                                if "success_{0}".format(output_id) in filename:
                                    os.unlink(filepath)
                                
                                if "finish_{0}".format(output_id) in filename:
                                    os.unlink(filepath)
                                    
                                if "calc_time_{0}".format(output_id) in filename:
                                    os.unlink(filepath)
                                    
                                if "{0}_sort_rout_order_cmd".format(jobname) in filename:
                                    os.unlink(filepath)
                                    
                            if os.path.exists("{0}/outputing_test_point_calc_time.log".format(tmp_dir)):
                                os.unlink("{0}/outputing_test_point_calc_time.log".format(tmp_dir))
                                    
                            if os.path.exists(output_dir):
                                shutil.rmtree(output_dir)
                        
                        end_calc_time = time.time()
                        seconds = end_calc_time - start_calc_time
                        time_log = u"<br>incam总耗时:{0}分钟 <br>".format(round(seconds/60, 2))
                        self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(time_log),
                                                "OutputTime = now()", ],
                                               condition="id={0}".format(output_id))
                    
                    if "not_import_tgz" not in args:                        
                        run_scripts = "{0}/del_job.py no_gui".format(script_dir)
                        if "192.168.19.243" not in localip[2]:
                            os.system("python {0}/{2}.py {1}".format(script_dir, run_scripts, login_soft_script_name))
    
                        if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, jobname)):
                            os.unlink("{0}/outputing_{1}.log".format(tmp_dir, jobname)) 
                    
            except Exception, e:
                try:                    
                    if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)):
                        os.unlink("{0}/outputing_{1}.log".format(tmp_dir, name))
                except:
                    pass
                print(e)
                
            if args:
                break
            
            time.sleep(60)
            
    def get_cam_director_finish_status(self, jobname, process_type="ocheckfinish_time"):
        """获取审核的完成状态"""
        dbc_p = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='project_status', prod=3306,
                                   username='root', passwd='k06931!')        
        sql = """select psj.*
        from project_status_jobmanage psj
        WHERE job = '{0}'
        order by id desc"""
        job_process_info = conn.SELECT_DIC(dbc_p, sql.format(jobname))
            
        if job_process_info and job_process_info[0].get(process_type, ""):
            return True
        
        return False            
            
    def run_zy_measure_coodinate_info_output_type(self, *args):
        """正业量测坐标信息自动输出"""
        
        while True:
            try:             
                dic_condition = {"Facotry": "S01H1","type": u"临时","data_type": u"正业坐标量测资料","isOutput": "Y",}
                param = []          
                for k, v in dic_condition.iteritems():
                    param.append(u"{0}='{1}'".format(k, v))        
                param.append("(OutputStatus is null or OutputStatus = '')")                
                
                if param:            
                    data_info = self.get_mysql_data(condtion=" and ".join(param) + " order by appTime desc")
                    #测试
                    if args:                        
                        data_info = self.get_mysql_data(condtion="id = {0}".format(*args))
                else:
                    data_info = []
                
                all_ouput_jobs = []
                dic_job_id = {}
                wait_time = 1
                for info in sorted(data_info, key=lambda x: x["workLevel"] * -1):
                    
                    if info["Job"] not in all_ouput_jobs:
                        all_ouput_jobs.append(info["Job"])
                        
                    if not dic_job_id.has_key(info["Job"].lower()):
                        dic_job_id[info["Job"].lower()] = [str(info["id"])]
                    else:
                        dic_job_id[info["Job"].lower()].append(str(info["id"]))
                        
                    if info["workLevel"] == 0:
                        wait_time = 0
                
                print(all_ouput_jobs)
                for name in all_ouput_jobs:
                    
                    name = name.lower()
                    
                    start_calc_time = time.time()
                    
                    jobname = name
                    if "not_import_tgz" in args:
                        res = 1                        
                    else:
                        print(os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)))
                        if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)):
                            time.sleep(5)
                            continue
                        
                        #if sys.platform == "win32":                            
                            #import_job_path = ur"\\192.168.2.174\GCfiles\HDI全套tgz\{0}系列\{1}.tgz".format(jobname[1:4], jobname)
                            #if not os.path.exists(import_job_path):
                                #import_job_path = ur"\\192.168.2.172\GCfiles\工程cam资料\{0}系列\{2}\{1}\{2}.tgz".format(jobname[1:4], jobname[-2:], jobname)
                        #else:
                            #import_job_path = u"/windows/174.tgz/{0}系列/{1}.tgz".format(jobname[1:4].upper(), jobname)
                            #if not os.path.exists(import_job_path):
                                #import_job_path = u"/windows/172.tgz/{0}系列/{2}/{1}/{2}.tgz".format(jobname[1:4].upper(), jobname[-2:], jobname)                                
                            
                        # res = self.import_tgz(name, dic_job_id[name], tgz_import_path=import_job_path)
                        # res = self.import_tgz(name, dic_job_id[name])
                        # 先判断服务器db目录是否存在此型号 存在则优先使用服务器的资料
                        # 获取内层是否已审核
                        check_status = self.get_cam_director_finish_status(jobname, process_type="icheckfinish_time")
                        db_job_path = "/id/incamp_db1/jobs/{0}".format(jobname)                           
                        if os.path.exists(db_job_path) and check_status:
                            res = self.import_tgz(jobname, dic_job_id[name], "no_gui_login_incam", tgz_import_path=db_job_path)
                        else:                                
                            res = self.import_tgz(name, dic_job_id[name])
                        
                        if not res :
                            self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(u"，请手动制作量测坐标资料!")
                                                    ],
                                                   condition="id in ({0})".format(",".join(dic_job_id[name])))
                            time.sleep(5)
                            continue
                        
                    print(res, os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)))                    
                    if res:
                    
                        with open("{0}/outputing_{1}.log".format(tmp_dir, name), "w") as f:
                            f.write("running zy")    
                        
                        for info in sorted(data_info, key=lambda x: x["workLevel"] * -1):
                            
                            jobname = info["Job"].lower().strip()
                            if jobname != name:
                                continue
                            
                            output_id = info["id"]
                            # output_layers = [x for x in info["OutLayer"].split(";") if x.strip()]                            
                            
                            self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出中"),
                                                    u"Status = '{0}'".format(u"输出中"),
                                                    u"AlarmLog = ''"],
                                                   condition="id={0}".format(output_id))                            
                            
                            dest_net_path = info["OutputPath"]
                            # dest_net_path = ur"\\192.168.2.57\临时文件夹\系列资料临时存放区\03.CAM制作资料暂放（勿删）\000勿删\阻抗测点输出\{0}".format(jobname.upper())
                            dest_net_path = dest_net_path.replace("\\", "/")
                            dest_net_path = dest_net_path.replace(ur"//192.168.2.57/临时文件夹/系列资料临时存放区/", "/windows/33.file/")
                            dest_net_path = dest_net_path.replace(ur"//192.168.2.174/GCfiles/", "/windows/174.file/")
                            
                            try:
                                os.makedirs(dest_net_path)
                            except Exception as e:
                                print(e)                                                                
                            
                            if not os.path.exists(dest_net_path):                                
                                log = u"Linux中创建输出路径失败{0} <br>".format(dest_net_path)
                                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)], condition="id={0}".format(output_id))                    
                                continue                            
                            
                            output_dir = "{0}/{1}/{2}/{3}".format(tmp_dir, jobname, "measure_coodinate", output_id)
                            
                            if os.path.exists(output_dir):
                                shutil.rmtree(output_dir)
                            
                            try:                                
                                os.makedirs(output_dir)
                            except Exception, e:
                                print(e)
                                pass                            

                            run_scripts = os.path.join(script_dir, "Auto_Engineer_Output_Tools.py")
                            data_type = "auto_ouput_measure_coodinate_info"

                            success_file = os.path.join(tmp_dir, "success_{0}.log".format(output_id))
                            os.system("rm -rf {0}".format(success_file))
                            error_file = os.path.join(tmp_dir, "success_{0}_check_error.log".format(output_id))           
                            os.system("rm -rf {0}".format(error_file))
                            
                            os.environ["JOB"] = jobname
                            if "gui_run" in args:                                
                                os.system("python %s/%s.py %s %s %s %s %s" %
                                          (script_dir,login_soft_script_name, run_scripts, data_type, jobname, output_id, "gui_run"))                                                               
                            else:
                                os.system("python %s/%s.py %s %s %s %s %s" %
                                          (script_dir,login_soft_script_name, run_scripts, data_type, jobname, output_id, "no_gui"))                                
                             
                            if os.path.exists(error_file):
                                log = file(error_file).readlines()
                                try:                                    
                                    self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                            u"Status = '{0}'".format(u"输出异常"),
                                                            u"AlarmLog = concat(AlarmLog,'{0}')".format("<br>".join(log).decode("cp936"))
                                                            ],
                                                           condition="id={0}".format(output_id))
                                except Exception as e:
                                    print(e, 111111)
                                    self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                            u"Status = '{0}'".format(u"输出异常"),
                                                            u"AlarmLog = concat(AlarmLog,'{0}')".format("<br>".join(log).decode("utf8"))
                                                            ],
                                                           condition="id={0}".format(output_id))
                                    
                            else:
                                if os.path.exists(success_file):
                                    
                                    #arraylist_file = []
                                    #for filename in os.listdir(output_dir):
                                        #filepath = os.path.join(output_dir,filename)
                                        ## print(filename)
                                        #try:
                                            #if os.path.isfile(filepath):                                                
                                                #shutil.copy(filepath, dest_net_path)
                                            #else:
                                                #dest_net_path_dir = os.path.join(dest_net_path, filename.decode("utf8"))
                                                #if os.path.exists(dest_net_path_dir):
                                                    #shutil.rmtree(dest_net_path_dir)
                                                #shutil.copytree(filepath, dest_net_path_dir)
                                        #except Exception as e:
                                            #print(e)                                           
                                            
                                        #arraylist_file.append(os.path.join(dest_net_path, filename.decode("utf8")))                                    
                                                                                
                                    self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出完成"),
                                                            u"Status = '输出完成'", 
                                                            u"AlarmLog = concat(AlarmLog,'{0}<br>')".format(u"输出成功 请到【量测坐标申请】表中申请txt文档生成。")
                                                            ],
                                                           condition="id={0}".format(output_id))                                                                      
                                else:
                                    log = u"<br>incampro 输出程序异常中断，请手动制作线宽量测资料！<br>"                                
                                    self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                            u"Status = '{0}'".format(u"输出异常"),
                                                            u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                                           condition="id={0}".format(output_id))    
                                
                            for filename in os.listdir(tmp_dir):
                                filepath = os.path.join(tmp_dir,filename)
                                if "success_{0}".format(output_id) in filename:
                                    os.unlink(filepath)
                                
                                if "finish_{0}".format(output_id) in filename:
                                    os.unlink(filepath)
                                    
                                if "calc_time_{0}".format(output_id) in filename:
                                    os.unlink(filepath)
                                    
                                if "{0}_sort_rout_order_cmd".format(jobname) in filename:
                                    os.unlink(filepath)
                                    
                            if os.path.exists("{0}/outputing_test_point_calc_time.log".format(tmp_dir)):
                                os.unlink("{0}/outputing_test_point_calc_time.log".format(tmp_dir))
                                    
                            if os.path.exists(output_dir):
                                shutil.rmtree(output_dir)
                        
                        end_calc_time = time.time()
                        seconds = end_calc_time - start_calc_time
                        time_log = u"<br>incam总耗时:{0}分钟 <br>".format(round(seconds/60, 2))
                        self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(time_log),
                                                "OutputTime = now()", ],
                                               condition="id={0}".format(output_id))
                    
                    if "not_import_tgz" not in args:                        
                        run_scripts = "{0}/del_job.py no_gui".format(script_dir)
                        if "192.168.19.243" not in localip[2]:
                            os.system("python {0}/{2}.py {1}".format(script_dir, run_scripts, login_soft_script_name))
    
                        if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)):
                            os.unlink("{0}/outputing_{1}.log".format(tmp_dir, name)) 
                    
            except Exception, e:
                try:                    
                    if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)):
                        os.unlink("{0}/outputing_{1}.log".format(tmp_dir, name))
                except:
                    pass
                print(e)
                
            if args:
                break
            
            time.sleep(60)    
            
    def run_incam_yh_pad_output_type(self, *args):
        """incam输出输出长七短五涨缩靶坐标工具"""
        
        while True:
            try:             
                dic_condition = {"Facotry": "S01H1","type": u"正式","data_type": u"输出长七短五涨缩靶坐标","isOutput": "Y",}
                param = []          
                for k, v in dic_condition.iteritems():
                    param.append(u"{0}='{1}'".format(k, v))        
                param.append("(OutputStatus is null or OutputStatus = '')")       
                
                if param:            
                    data_info = self.get_mysql_data(condtion=" and ".join(param))
                    #测试
                    if args:                        
                        data_info = self.get_mysql_data(condtion="id = {0}".format(*args))
                else:
                    data_info = []
                
                all_ouput_jobs = []
                dic_job_id = {}
                for info in sorted(data_info, key=lambda x: x["workLevel"] * -1):
                    # if info["Job"] not in all_ouput_jobs:
                    all_ouput_jobs.append(info["Job"])
                    if not dic_job_id.has_key(info["Job"].lower()):
                        dic_job_id[info["Job"].lower()] = [str(info["id"])]
                    else:
                        dic_job_id[info["Job"].lower()].append(str(info["id"]))                    
    
                print(all_ouput_jobs)
                for name in set(all_ouput_jobs):            
                    name = name.lower()
                    
                    if "not_import_tgz" in args:
                        res = 1                        
                    else:
                        print(os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)))
                        if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)):
                            time.sleep(5)
                            continue                        
                        res = self.import_tgz(name, dic_job_id[name])
                        #if res and os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)):
                            #self.update_mysql_data([u"OutputStatus = ''",
                                                    #u"Status = ''",
                                                    #u"AlarmLog = ''"],
                                                   #condition="id in ({0})".format(",".join(dic_job_id[name])))
                            #time.sleep(5)
                            #continue                        
                    
                    print(res, os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)))
                    
                    if res:
                    
                        with open("{0}/outputing_{1}.log".format(tmp_dir, name), "w") as f:
                            f.write("running")
                            
                        start_calc_time = time.time()
                        
                        for info in sorted(data_info, key=lambda x: x["workLevel"] * -1):
                            
                            jobname = info["Job"].lower().strip()
                            if jobname != name:
                                continue
                            
                            output_id = info["id"]
                            # output_layers = [x for x in info["OutLayer"].split(";") if x.strip()]
                            
                            self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出中"),
                                                    u"Status = '{0}'".format(u"输出中"),
                                                    u"AlarmLog = ''"],
                                                   condition="id={0}".format(output_id))                            
                            
                            dest_net_path = info["OutputPath"]
                            dest_net_path = dest_net_path.replace("\\", "/")
                            dest_net_path = dest_net_path.replace(ur"//192.168.2.57/临时文件夹/系列资料临时存放区/", "/windows/33.file/")
                            dest_net_path = dest_net_path.replace(ur"//192.168.2.174/GCfiles/", "/windows/174.file/")
                            # print([dest_net_path])
                            try:
                                os.makedirs(dest_net_path)
                            except Exception, e:
                                print(e)
                            
                            if not os.path.exists(dest_net_path):                                
                                log = u"Linux中创建输出路径失败{0} <br>".format(dest_net_path)
                                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)], condition="id={0}".format(output_id))                    
                                continue
                            
                            output_dir = "{0}/{1}/{2}/{3}".format(tmp_dir, jobname, "yh_pad", output_id)
                            if os.path.exists(output_dir):
                                shutil.rmtree(output_dir)
                            
                            try:                                
                                os.makedirs(output_dir)
                            except Exception, e:
                                print(e)
                                pass                            

                            run_scripts = "/incam/server/site_data/scripts/sh_script/panel/add_new_yhpad/write_yh_pad_data_auto.py"
                            data_type = "yh_pad"

                            success_file = os.path.join(tmp_dir, "success_{0}.log".format(output_id))
                            os.system("rm -rf {0}".format(success_file))
                            error_file = os.path.join(tmp_dir, "success_{0}_check_error.log".format(output_id))           
                            os.system("rm -rf {0}".format(error_file))
                            
                            os.environ["JOB"] = jobname
                            if "gui_run" in args:
                                os.system("python %s/%s.py %s %s %s %s %s" %
                                          (script_dir,login_soft_script_name, run_scripts, data_type, jobname, output_id, "gui_run"))                               
                            else:
                                os.system("python %s/%s.py %s %s %s %s %s" %
                                          (script_dir,login_soft_script_name, run_scripts, data_type, jobname, output_id, "no_gui"))                                

                            if os.path.exists(error_file):
                                log = file(error_file).readlines()
                                self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                        u"Status = '{0}'".format(u"输出异常"),
                                                        u"AlarmLog = concat(AlarmLog,'{0}')".format("<br>".join(log).decode("utf8"))
                                                        ],
                                                       condition="id={0}".format(output_id))
                                #try:
                                    #shutil.rmtree(dest_net_path)
                                #except:
                                    #pass                                
                            else:                                
                                if os.path.exists(success_file):
                                    dirname = os.path.join(output_dir, jobname)
                                    success_log = False
                                    for root, dirs, files in os.walk(dirname):
                                        for filename in files:
                                            if "{0}_yh_pad.csv".format(jobname) in filename:                                                
                                                success_log = True
                                                break
                                            
                                    if success_log:
                                        self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出完成"),
                                                                u"Status = '输出完成'"], condition="id={0}".format(output_id)) 
                                        #try:
                                            #shutil.rmtree(dest_net_path)
                                        #except:
                                            #pass
                                        shutil.copytree(dirname, dest_net_path)
                                    else:
                                        log = u"输出文件{0}不存在，请手动输出！".format("{0}._yh_pad.csv".format(jobname))
                                        self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                                u"Status = '{0}'".format(u"输出异常"),
                                                                u"AlarmLog = concat(AlarmLog,'{0}')".format(log)
                                                                ],condition="id={0}".format(output_id))
                                        
                                else:
                                    log = u"INCAMPRO 输出程序异常中断，请手动输出长7短5涨缩数据！<br>"                                
                                    self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                            u"Status = '{0}'".format(u"输出异常"),
                                                            u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                                           condition="id={0}".format(output_id))                                 

                            if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, jobname)):
                                os.unlink("{0}/outputing_{1}.log".format(tmp_dir, jobname))
                                
                            for name in os.listdir(tmp_dir):
                                filepath = os.path.join(tmp_dir,name)
                                if "success_{0}".format(output_id) in name:
                                    os.unlink(filepath)
                                
                                if "finish_{0}".format(output_id) in name:
                                    os.unlink(filepath)
                                    
                                if "calc_time_{0}".format(output_id) in name:
                                    os.unlink(filepath)                                  
                                    
                            #if os.path.exists(output_dir):
                                #shutil.rmtree(output_dir)
                        
                        end_calc_time = time.time()
                        seconds = end_calc_time - start_calc_time
                        time_log = u"<br>incam总耗时:{0}分钟 <br>".format(round(seconds/60, 2))
                        self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(time_log),
                                                "OutputTime = now()", ],
                                               condition="id={0}".format(output_id))
                    
                    if "not_import_tgz" not in args:                        
                        run_scripts = "{0}/del_job.py no_gui".format(script_dir)
                        if "192.168.19.243" not in localip[2]:
                            os.system("python {0}/{2}.py {1}".format(script_dir, run_scripts, login_soft_script_name))
                    
            except Exception, e:
                print(e)
                
            if args:
                break
            
            time.sleep(60)

    def run_incam_pnlrout_output_type(self, *args):
        """incam输出裁磨线资料工具"""
        
        while True:
            try:             
                dic_condition = {"Facotry": "S01H1","type": u"正式","data_type": u"输出裁磨数据","isOutput": "Y",}
                param = []          
                for k, v in dic_condition.iteritems():
                    param.append(u"{0}='{1}'".format(k, v))        
                param.append("(OutputStatus is null or OutputStatus = '')")       
                
                if param:            
                    data_info = self.get_mysql_data(condtion=" and ".join(param))
                    #测试
                    if args:                        
                        data_info = self.get_mysql_data(condtion="id = {0}".format(*args))
                else:
                    data_info = []
                
                all_ouput_jobs = []
                dic_job_id = {}
                for info in sorted(data_info, key=lambda x: x["workLevel"] * -1):
                    # if info["Job"] not in all_ouput_jobs:
                    all_ouput_jobs.append(info["Job"])
                    if not dic_job_id.has_key(info["Job"].lower()):
                        dic_job_id[info["Job"].lower()] = [str(info["id"])]
                    else:
                        dic_job_id[info["Job"].lower()].append(str(info["id"]))                    
    
                print(all_ouput_jobs)
                for name in set(all_ouput_jobs):            
                    name = name.lower()
                    
                    if "not_import_tgz" in args:
                        res = 1                        
                    else:
                        print(os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)))
                        if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)):
                            time.sleep(5)
                            continue                        
                        res = self.import_tgz(name, dic_job_id[name])
                        #if res and os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)):
                            #self.update_mysql_data([u"OutputStatus = ''",
                                                    #u"Status = ''",
                                                    #u"AlarmLog = ''"],
                                                   #condition="id in ({0})".format(",".join(dic_job_id[name])))
                            #time.sleep(5)
                            #continue                        
                    
                    print(res, os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)))                    
                    if res:
                    
                        with open("{0}/outputing_{1}.log".format(tmp_dir, name), "w") as f:
                            f.write("running")
                            
                        start_calc_time = time.time()
                        
                        for info in sorted(data_info, key=lambda x: x["workLevel"] * -1):
                            
                            jobname = info["Job"].lower().strip()
                            if jobname != name:
                                continue
                            
                            output_id = info["id"]
                            # output_layers = [x for x in info["OutLayer"].split(";") if x.strip()]
                            
                            self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出中"),
                                                    u"Status = '{0}'".format(u"输出中"),
                                                    u"AlarmLog = ''"],
                                                   condition="id={0}".format(output_id))                            
                            
                            dest_net_path = os.path.join(info["OutputPath"], "PnlRout")
                            dest_net_path = dest_net_path.replace("\\", "/")
                            dest_net_path = dest_net_path.replace(ur"//192.168.2.57/临时文件夹/系列资料临时存放区/", "/windows/33.file/")
                            dest_net_path = dest_net_path.replace(ur"//192.168.2.174/GCfiles/", "/windows/174.file/")
                            # print([dest_net_path])
                            try:
                                os.makedirs(dest_net_path)
                            except Exception, e:
                                print(e)
                            
                            if not os.path.exists(dest_net_path):                                
                                log = u"Linux中创建输出路径失败{0} <br>".format(dest_net_path)
                                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)], condition="id={0}".format(output_id))                    
                                continue
                            
                            output_dir = "{0}/{1}/{2}/{3}".format(tmp_dir, jobname, "Pnl_Rout", output_id)
                            if os.path.exists(output_dir):
                                shutil.rmtree(output_dir)
                            
                            try:                                
                                os.makedirs(output_dir)
                            except Exception, e:
                                print(e)
                                pass
                            
                            data_type = ""
                            if info["data_type"] == u"输出裁磨数据":
                                run_scripts = "/incam/server/site_data/scripts/sh_script/auto_output_pnlrout/output_pnlrout_auto.pl"
                                data_type = "pnl_rout"
                            
                            if info["data_type"] == u"输出靶距信息":
                                run_scripts = os.path.join(script_dir, "Auto_Engineer_Output_Tools.py")
                                data_type = "auto_uploading_target_info_to_erp"
                            
                            if not data_type:
                                continue
                            
                            success_file = os.path.join(tmp_dir, "success_{0}.log".format(output_id))
                            os.system("rm -rf {0}".format(success_file))
                            error_file = os.path.join(tmp_dir, "success_{0}_check_error.log".format(output_id))           
                            os.system("rm -rf {0}".format(error_file))
                            
                            os.environ["JOB"] = jobname
                            if "gui_run" in args:
                                os.system("python %s/%s.py %s %s %s %s %s" %
                                          (script_dir,login_soft_script_name, run_scripts, data_type, jobname, output_id, "gui_run"))                               
                            else:
                                os.system("python %s/%s.py %s %s %s %s %s" %
                                          (script_dir,login_soft_script_name, run_scripts, data_type, jobname, output_id, "no_gui"))
                                
                            if info["data_type"] == u"输出裁磨数据":
                                if os.path.exists(error_file):
                                    log = file(error_file).readlines()
                                    self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                            u"Status = '{0}'".format(u"输出异常"),
                                                            u"AlarmLog = concat(AlarmLog,'{0}')".format("<br>".join(log).decode("utf8"))
                                                            ],
                                                           condition="id={0}".format(output_id))
                                    #try:
                                        #shutil.rmtree(dest_net_path)
                                    #except:
                                        #pass                                    
                                else:                                
                                    if os.path.exists(success_file):
                                        mrpname = [x["MRPNAME"] for x in get_inplan_mrp_info(jobname.upper())]
                                        dirname = os.path.join(output_dir, jobname)
                                        success_log = False
                                        num = 0
                                        if os.path.exists(dirname):
                                            num = len(os.listdir(dirname))
                                            if len(mrpname) == num:
                                                success_log = True
                                                
                                        if success_log:
                                            self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出完成"),
                                                                    u"Status = '输出完成'"], condition="id={0}".format(output_id))
                                            
                                            for name in os.listdir(dirname):
                                                path = os.path.join(dirname, name)
                                                #try:
                                                    #shutil.rmtree(os.path.join(dest_net_path, name))
                                                #except:
                                                    #pass
                                                shutil.copytree(path, os.path.join(dest_net_path, name))
                                        else:
                                            log = u"输出文件个数{0} 跟inplan压合数量{1}不一致，请手动输出！<br>".format(num, len(mrpname))
                                            self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                                    u"Status = '{0}'".format(u"输出异常"),
                                                                    u"AlarmLog = concat(AlarmLog,'{0}')".format(log)
                                                                    ],condition="id={0}".format(output_id))
                                            #try:
                                                #shutil.rmtree(dest_net_path)
                                            #except:
                                                #pass                                            
                                            
                                    else:
                                        log = u"<br>INCAMPRO 输出程序异常中断，请手动输出裁磨数据！<br>"                                
                                        self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                                u"Status = '{0}'".format(u"输出异常"),
                                                                u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                                               condition="id={0}".format(output_id))
                                        #try:
                                            #shutil.rmtree(dest_net_path)
                                        #except:
                                            #pass                                        
                            else:
                                if os.path.exists(success_file):
                                    self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出完成"),
                                                            u"Status = '输出完成'"], condition="id={0}".format(output_id))
                                else:
                                    log = u"<br>INCAMPRO 输出程序异常中断，请手动上传靶距数据！<br>"                                
                                    self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                            u"Status = '{0}'".format(u"输出异常"),
                                                            u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                                           condition="id={0}".format(output_id))
                                    #try:
                                        #shutil.rmtree(dest_net_path)
                                    #except:
                                        #pass                                    
    
                            if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, jobname)):
                                os.unlink("{0}/outputing_{1}.log".format(tmp_dir, jobname))
                                
                            for name in os.listdir(tmp_dir):
                                filepath = os.path.join(tmp_dir,name)
                                if "success_{0}".format(output_id) in name:
                                    os.unlink(filepath)
                                
                                if "finish_{0}".format(output_id) in name:
                                    os.unlink(filepath)
                                    
                                if "calc_time_{0}".format(output_id) in name:
                                    os.unlink(filepath)                                  
                                    
                            if os.path.exists(output_dir):
                                shutil.rmtree(output_dir)
                        
                        end_calc_time = time.time()
                        seconds = end_calc_time - start_calc_time
                        time_log = u"<br>incam总耗时:{0}分钟 <br>".format(round(seconds/60, 2))
                        self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(time_log),
                                                "OutputTime = now()", ],
                                               condition="id={0}".format(output_id))
                    
                    if "not_import_tgz" not in args:                        
                        run_scripts = "{0}/del_job.py no_gui".format(script_dir)
                        if "192.168.19.243" not in localip[2]:
                            os.system("python {0}/{2}.py {1}".format(script_dir, run_scripts, login_soft_script_name))
                    
            except Exception, e:
                print(e)
                
            if args:
                break
            
            time.sleep(60)
            
    def run_incam_ldi_opfx_output_type(self, *args):
        """incam输出ldi opfx工具"""
        
        while True:
            try:             
                dic_condition = {"Facotry": "S01H1","type": u"正式","isOutput": "Y",}
                param = []          
                for k, v in dic_condition.iteritems():
                    param.append(u"{0}='{1}'".format(k, v))        
                param.append("(OutputStatus is null or OutputStatus = '')")
                param.append(u"(data_type like '输出奥宝LDI资料%%')")                
                
                if param:            
                    data_info = self.get_mysql_data(condtion=" and ".join(param))
                    #测试
                    if args:                        
                        data_info = self.get_mysql_data(condtion="id = {0}".format(*args))
                else:
                    data_info = []
                
                all_ouput_jobs = []
                dic_job_id = {}
                for info in sorted(data_info, key=lambda x: x["workLevel"] * -1):
                    # if info["Job"] not in all_ouput_jobs:
                    all_ouput_jobs.append(info["Job"])
                    if not dic_job_id.has_key(info["Job"].lower()):
                        dic_job_id[info["Job"].lower()] = [str(info["id"])]
                    else:
                        dic_job_id[info["Job"].lower()].append(str(info["id"]))                    
    
                print(all_ouput_jobs)
                for name in set(all_ouput_jobs):            
                    name = name.lower()
                    
                    if "not_import_tgz" in args:
                        res = 1                        
                    else:                    
                        print(os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)))
                        if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)):
                            time.sleep(5)
                            continue
                        
                        res = self.import_tgz(name, dic_job_id[name])
                        #if res and os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)):
                            #self.update_mysql_data([u"OutputStatus = ''",
                                                    #u"Status = ''",
                                                    #u"AlarmLog = ''"],
                                                   #condition="id in ({0})".format(",".join(dic_job_id[name])))
                            #time.sleep(5)
                            #continue                        
                    
                    print(res, os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)))                    
                    if res:                    
                        with open("{0}/outputing_{1}.log".format(tmp_dir, name), "w") as f:
                            f.write("running")
                            
                        start_calc_time = time.time()
                        
                        for info in sorted(data_info, key=lambda x: x["workLevel"] * -1):
                            
                            jobname = info["Job"].lower().strip()
                            if jobname != name:
                                continue
                            
                            output_id = info["id"]
                            output_layers = [x for x in info["OutLayer"].split(";") if x.strip()]
                            
                            self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出中"),
                                                    u"Status = '{0}'".format(u"输出中"),
                                                    u"AlarmLog = ''"],
                                                   condition="id={0}".format(output_id))                            
                            
                            dest_net_path = info["OutputPath"]
                            dest_net_path = dest_net_path.replace("\\", "/")
                            dest_net_path = dest_net_path.replace(ur"//192.168.2.57/临时文件夹/系列资料临时存放区/", "/windows/33.file/")
                            dest_net_path = dest_net_path.replace(ur"//192.168.2.174/GCfiles/", "/windows/174.file/")
                            # print([dest_net_path])
                            try:
                                os.makedirs(dest_net_path)
                            except Exception, e:
                                print(e)
                            
                            if not os.path.exists(dest_net_path):                                
                                log = u"Linux中创建输出路径失败{0} <br>".format(dest_net_path)
                                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)], condition="id={0}".format(output_id))                    
                                continue
                            
                            output_dir = "{0}/{1}/{2}/{3}".format(tmp_dir, jobname, "ldi", output_id)
                            if os.path.exists(output_dir):
                                shutil.rmtree(output_dir)
                            
                            try:                                
                                os.makedirs(output_dir)
                            except Exception, e:
                                print(e)
                                pass                                                    
                            
                            run_scripts = os.path.join(script_dir, "Auto_Engineer_Output_Tools.py")
                            
                            success_file = os.path.join(tmp_dir, "success_{0}.log".format(output_id))
                            os.system("rm -rf {0}".format(success_file))                            
    
                            data_type = "output_orbotech_ldi_opfx"
                            
                            os.environ["JOB"] = jobname
                            if "gui_run" in args:
                                os.system("python %s/%s.py %s %s %s %s %s" %
                                          (script_dir,login_soft_script_name, run_scripts, data_type, jobname, output_id, "gui_run"))                               
                            else:
                                os.system("python %s/%s.py %s %s %s %s %s" %
                                          (script_dir,login_soft_script_name, run_scripts, data_type, jobname, output_id, "no_gui"))
                                
                            success_log = True
                            arraylist_log = []
                            for layer in output_layers:
                                filepath =os.path.join(output_dir, "{0}@{1}".format(jobname, layer))
                                success_file = os.path.join(tmp_dir, "success_{0}_{1}.log".format(output_id, layer))  
                                if not os.path.exists(filepath):
                                    log = u"输出层{0} 异常，请手动输出！<br>".format(layer)
                                    arraylist_log.append(log)                                    
                                    success_log = False                                
                                else:
                                    if not os.path.exists(success_file):
                                        log = u"输出层{0}程序回读异常，请手动输出！<br>".format(layer)
                                        arraylist_log.append(log)
                                        success_log = False                                                                           
                                    else:
                                        if info["data_type"] == u"输出奥宝LDI资料(线路及辅助)":
                                            dir1 = os.path.join(dest_net_path, "LDI_2.0Micron")
                                            dir2 = os.path.join(dest_net_path, "LDI_1.5Micron")
                                            try:
                                                os.makedirs(dir1)
                                            except:
                                                pass
                                            try:
                                                os.makedirs(dir2)
                                            except:
                                                pass 
                                            shutil.copy(filepath, dir1)
                                            
                                            lines = file(filepath).readlines()
                                            with open(filepath, "w") as f:
                                                f.write("".join(lines).replace("RESOLUTION = 2.000000, micron\n",
                                                                               "RESOLUTION = 1.500000, micron\n"))
                                            shutil.copy(filepath, dir2)
                                        else:
                                            print("------------------>", dest_net_path)
                                            shutil.copy(filepath, dest_net_path)
                            
                            error_file = os.path.join(tmp_dir, "success_{0}_check_error.log".format(output_id))
                            
                            if os.path.exists(error_file):
                                log = file(error_file).readlines()
                                self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                        u"AlarmLog = concat(AlarmLog,'{0}')".format("<br>".join(log).decode("utf8")),
                                                        u"Status = '{0}'".format(u"输出异常"),],
                                                       condition="id={0}".format(output_id))                                
                            else:
                                if success_log:
                                    self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出完成"),
                                                            u"Status = '输出完成'"], condition="id={0}".format(output_id))
                                else:
                                    self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                            u"Status = '{0}'".format(u"输出异常"),
                                                            u"AlarmLog = concat(AlarmLog,'{0}')".format(" ".join(arraylist_log))],
                                                       condition="id={0}".format(output_id))
                                    
                                success_file = os.path.join(tmp_dir, "success_{0}.log".format(output_id))  
                                if not os.path.exists(success_file):
                                    log = u"INCAMPRO 输出程序异常中断，请手动输出！<br>"                                
                                    self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                            u"Status = '{0}'".format(u"输出异常"),
                                                            u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                                           condition="id={0}".format(output_id))                                
    
                            if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, jobname)):
                                os.unlink("{0}/outputing_{1}.log".format(tmp_dir, jobname))
                                
                            for name in os.listdir(tmp_dir):
                                filepath = os.path.join(tmp_dir,name)
                                if "success_{0}".format(output_id) in name:
                                    os.unlink(filepath)
                                
                                if "finish_{0}".format(output_id) in name:
                                    os.unlink(filepath)
                                    
                                if "calc_time_{0}".format(output_id) in name:
                                    os.unlink(filepath)                                  
                                    
                            if os.path.exists(output_dir):
                                shutil.rmtree(output_dir)
                        
                        end_calc_time = time.time()
                        seconds = end_calc_time - start_calc_time
                        time_log = u"incam总耗时:{0}分钟 <br>".format(round(seconds/60, 1))
                        self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(time_log),
                                                "OutputTime = now()", ],
                                               condition="id={0}".format(output_id))
                        
                    if "not_import_tgz" not in args:    
                        run_scripts = "{0}/del_job.py no_gui".format(script_dir)
                        if "192.168.19.243" not in localip[2]:
                            os.system("python {0}/{2}.py {1}".format(script_dir, run_scripts, login_soft_script_name))
                    
            except Exception, e:
                print(e)
                
            if args:
                break
            
            time.sleep(60)

    def run_genesis_gerber_output_type(self, *args):
        """genesis输出gerber类型工具"""
        
        if sys.platform <> "win32":
            login_soft_script_name = "no_gui_login_genesis"
        else:
            login_soft_script_name = "no_gui_login_genesis_gfx"
        
        while True:
            try:
                
                h_time = time.strftime('%H', time.localtime(time.time()))
                if h_time == "07":        
                    for i in range(2):
                        try:    
                            for root, dirs, files in os.walk("/tmp"):
                                for dirname in dirs:
                                    try:
                                        dir_path = os.path.join(root, dirname)
                                        all_files = os.listdir(dir_path)
                                        if not all_files:                                            
                                            shutil.rmtree(dir_path.encode("cp936"))
                                            shutil.rmtree(dir_path)
                                    except Exception as e:
                                        print("errer11111:", e )
                            
                                for filename in files:
                                    try:                    
                                        filepath = os.path.join(root, filename)
                                        if time.time() - os.path.getmtime(filepath) > 60 * 60 * 12:
                                            os.unlink(filepath)
                                    except Exception as e:
                                        print("error22222", e)
                        except Exception as e:
                            print("error333333",e)
                            
                dic_condition = {"Facotry": "S01H1","type": u"正式", "data_type": u"输出GB资料","isOutput": "Y",}                
                
                if "second_process" in args:                    
                    self.update_mysql_data([u"OutputStatus = ''",
                                            u"Status = ''",
                                            u"AlarmLog = ''"],
                                           u"TIMESTAMPDIFF(MINUTE, apptime,now()) < 130 and "
                                           u"TIMESTAMPDIFF(MINUTE, apptime,now()) > 10 and "
                                           u"OutputStatus = '导入tgz成功，等待输出！' and "
                                           u"data_type='输出GB资料'")
                    
                #检测一直导入tgz失败，退出程序 重新打开20241214 by lyh                                      
                self.update_mysql_data([u"OutputStatus = ''",
                                        u"Status = ''",
                                        u"AlarmLog = ''"],
                                       u"TIMESTAMPDIFF(MINUTE, apptime,now()) < 10 and "
                                       u"AlarmLog like '%导入tgz失败%' and "
                                       u"data_type='输出GB资料'")                
                param = []          
                for k, v in dic_condition.iteritems():
                    param.append(u"{0}='{1}'".format(k, v))
                param.append(u"AlarmLog like '%导入tgz失败%'")
                param.append(u"TIMESTAMPDIFF(MINUTE, apptime,now()) > 20")
                param.append(u"TIMESTAMPDIFF(MINUTE, apptime,now()) < 40")
                data_info = self.get_mysql_data(condtion=" and ".join(param))
                if data_info:
                    #检测一直导入tgz失败，退出程序 重新打开20241214 by lyh                                      
                    self.update_mysql_data([u"OutputStatus = ''",
                                            u"Status = ''",
                                            u"AlarmLog = ''"],
                                           u"TIMESTAMPDIFF(MINUTE, apptime,now()) < 25 and "
                                           u"AlarmLog like '%导入tgz失败%' and "
                                           u"data_type='输出GB资料'")
                    h_time = time.strftime('%H:%M:%S', time.localtime(time.time()))
                    with open("/id/workfile/lyh/gerber_error.log", "a") as f:
                        f.write(h_time+"\n")
                    exit(0)
                #end
                
                param = []          
                for k, v in dic_condition.iteritems():
                    param.append(u"{0}='{1}'".format(k, v))
                param.append("(OutputStatus is null or OutputStatus = '')")
                # param.append(u"TIMESTAMPDIFF(MINUTE, apptime,now()) < 300")                
                
                if param:            
                    data_info = self.get_mysql_data(condtion=" and ".join(param))
                    #if "second_process" in args:
                        #dic_condition_new = {"Facotry": "S01H1","type": u"正式",
                                             #"data_type": u"输出GB资料","isOutput": "Y",
                                             #"Status" : u"输出中",}
                        #param_new = []          
                        #for k, v in dic_condition_new.iteritems():
                            #param_new.append(u"{0}='{1}'".format(k, v))
                                                 
                        #is_exists_runing_data = self.get_mysql_data(condtion=" and ".join(param_new))
                        #if not is_exists_runing_data:
                            #time.sleep(10)
                            #continue
                    #测试
                    if args and "second_process" not in args:                        
                        data_info = self.get_mysql_data(condtion="id = {0}".format(*args))
                else:
                    data_info = []
                
                all_ouput_jobs = []
                dic_job_id = {}
                dic_job_output_type = {}
                for info in sorted(data_info, key=lambda x: x["workLevel"] * -1):
                    # if info["Job"] not in all_ouput_jobs:
                    res = self.get_outputing_other_toolings("gerber", info["Job"])
                    if res:
                        continue
                    
                    all_ouput_jobs.append(info["Job"])
                    if not dic_job_id.has_key(info["Job"].lower()):
                        dic_job_id[info["Job"].lower()] = [str(info["id"])]
                        dic_job_output_type[info["Job"].lower()] = [str(info["remark"])]
                    else:
                        dic_job_id[info["Job"].lower()].append(str(info["id"]))
                        dic_job_output_type[info["Job"].lower()].append(str(info["remark"]))

                print(all_ouput_jobs)
                if all_ouput_jobs:                    
                    for name in all_ouput_jobs:
                        name = name.lower()                    
                        print(os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)))
                        if not os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)):
                            break
                    else:
                        time.sleep(5)
                        continue
                    
                    print(os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)))
                    if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)):
                        time.sleep(5)
                        continue 
                    
                    if "gui_run" not in args:
                        
                        genesis_manual_tgz_path = "/tmp/tgz/{0}/{0}.tgz".format(name)
                        os.system("rm -rf {0}".format(genesis_manual_tgz_path))        
                            
                        if sys.platform <> "win32":
                            # 先判断服务器db目录是否存在此型号 存在则优先使用服务器的资料
                            db_job_path = "/id/incamp_db1/jobs/{0}".format(name)
                            if os.path.exists(db_job_path):
                                print("----------->", db_job_path)
                                self.import_tgz(name, dic_job_id[name], "no_gui_login_incam", tgz_import_path=db_job_path)
                                
                                run_scripts = os.path.join(script_dir, "Auto_Engineer_Output_Tools.py")
                                data_type = "output_odb_tgz_for_genesis"
                                os.system("python %s/%s.py %s %s %s %s" %
                                          (script_dir,"no_gui_login_incam", run_scripts, data_type, name, "no_gui"))
                                #仅测试
                                #if os.path.exists(genesis_manual_tgz_path):
                                    #shutil.copy(genesis_manual_tgz_path, ur"/windows/33.file/03.CAM制作资料暂放（勿删）/000勿删/GB输出测试/")                                
                                    #os.system("rm -rf {0}".format(genesis_manual_tgz_path))   
                            else:
                                self.import_tgz(name, dic_job_id[name], "no_gui_login_incam")

                        if os.path.exists(genesis_manual_tgz_path):
                            shutil.copy(genesis_manual_tgz_path, ur"/windows/33.file/03.CAM制作资料暂放（勿删）/000勿删/GB输出测试/")
                            res = self.import_tgz(name, dic_job_id[name], log_incam_win_soft="no_gui_login_genesis",
                                                  tgz_import_path=genesis_manual_tgz_path)
                        else:
                            res = self.import_tgz(name, dic_job_id[name], log_incam_win_soft="no_gui_login_genesis")
                            
                        if not res and len(set(dic_job_output_type[name])) == 1 and dic_job_output_type[name][0] == "gerber_inner":
                            #此路径tgz只允许输出内层gerber
                            import_job_path = ur"/windows/33.file/{0}系列/{1}/{2}/{1}.tgz".format(name[1:4].upper(), name, name[-2:].upper())
                            if not os.path.exists(import_job_path):
                                import_job_path = ur"/windows/33.file/{0}系列/{1}/{2}/{1}-inn.tgz".format(name[1:4].upper(), name, name[-2:].upper())
                                
                            if os.path.exists(import_job_path):
                                if sys.platform <> "win32":                        
                                    self.import_tgz(name, dic_job_id[name],
                                                    log_incam_win_soft="no_gui_login_incam",
                                                    tgz_import_path=import_job_path)
                                
                                res = self.import_tgz(name, dic_job_id[name],
                                                      log_incam_win_soft="no_gui_login_genesis",
                                                      tgz_import_path=import_job_path)
                    else:
                        res = 1
                    
                    print(res, os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)))
                    
                    #if res and os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)):
                        #self.update_mysql_data([u"OutputStatus = ''",
                                                #u"Status = ''",
                                                #u"AlarmLog = ''"],
                                               #condition="id in ({0})".format(",".join(dic_job_id[name])))
                        #time.sleep(5)
                        #continue
                    
                    if res:
                    
                        with open("{0}/outputing_{1}.log".format(tmp_dir, name), "w") as f:
                            f.write("running")            
                        
                        start_calc_time = time.time()
                        
                        for info in sorted(data_info, key=lambda x: x["workLevel"] * -1):
                            
                            jobname = info["Job"].lower()
                            if jobname != name:
                                continue
                            
                            output_id = info["id"]
                            
                            for filename in os.listdir(tmp_dir):
                                filepath = os.path.join(tmp_dir,filename)
                                if "success_{0}".format(output_id) in filename:
                                    os.unlink(filepath)
                                
                                if "finish_{0}".format(output_id) in filename:
                                    os.unlink(filepath)
                                    
                                if "calc_time_{0}".format(output_id) in filename:
                                    os.unlink(filepath)                              
                            
                            dest_net_path = info["OutputPath"]
                            if sys.platform != "win32":
                                # dest_net_path = ur"\\192.168.2.57\临时文件夹\系列资料临时存放区\03.CAM制作资料暂放（勿删）\000勿删\GB输出测试\{0}".format(jobname.upper())
                                dest_net_path = dest_net_path.replace("\\", "/")
                                dest_net_path = dest_net_path.replace(ur"//192.168.2.57/临时文件夹/系列资料临时存放区/", "/windows/33.file/")
                                # dest_net_path = dest_net_path.replace(ur"//192.168.2.174/GCfiles/", "/windows/174.file/")
                                if os.path.isfile(dest_net_path):
                                    os.unlink(dest_net_path)
                                try:
                                    os.makedirs(dest_net_path)
                                except Exception, e:
                                    print(e)
                                
                                if not os.path.exists(dest_net_path):                                
                                    log = u"Linux中创建输出路径失败{0} <br>".format(dest_net_path)
                                    self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)], condition="id={0}".format(output_id))                    
                                    continue
                            else:
                                if os.path.isfile(dest_net_path):
                                    os.unlink(dest_net_path)                                
                                try:
                                    os.makedirs(dest_net_path)
                                except Exception, e:
                                    print(e)
                                
                                if not os.path.exists(dest_net_path):                                
                                    log = u"创建输出{0}路径失败，请清除异常状态重新输出试试，\
                                    若还是失败，请反馈程序工程师处理。<br>！".format(dest_net_path)
                                    self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常"),
                                                            u"Status = '{0}'".format(u"输出异常"),
                                                            u"AlarmLog = '{0}'".format(log)],
                                                           condition="id={0}".format(output_id))
                                    return
                            
                            self.update_mysql_data([u"OutputStatus = '{0}'".format(u"genesis输出中"),
                                                    u"Status = '{0}'".format(u"输出中"),
                                                    u"AlarmLog = '输出中<br>'"], condition="id={0}".format(output_id))                            
                            
                            output_dir = "{0}/{1}/{2}/{3}".format(tmp_dir, jobname, "gerber", output_id)
                            if os.path.exists(output_dir):
                                shutil.rmtree(output_dir)
                            
                            try:                                
                                os.makedirs(output_dir)
                            except Exception, e:
                                print(e)
                                pass
                                
                            run_scripts = os.path.join(script_dir, "Auto_Engineer_Output_Tools.py")
                            
                            output_layers = [x for x in info["OutLayer"].split(";") if x.strip()] 
                            for layer in output_layers:                                
                                success_file = os.path.join(tmp_dir, "success_{0}_{1}.log".format(output_id, layer))
                                os.system("rm -rf {0}".format(success_file))
                                finish_file = os.path.join(tmp_dir, "finish_{0}_{1}.log".format(output_id, layer))
                                os.system("rm -rf {0}".format(finish_file))
                            
                            data_type = ""
                            if info["data_type"] == u"输出GB资料":
                                data_type = "genesis_output_gerber"
                            
                            os.environ["JOB"] = jobname 

                            theads = []
                            self.Thread = {}
                            for i, layer in enumerate(output_layers):
                                # self.Thread[layer] = QtCore.QThread()
                                #self.run_genesis = LongTimeRunThing((script_dir,login_soft_script_name,
                                                                     #run_scripts, data_type, jobname,
                                                                     #output_id, layer, i if i <= 10 else i - 10, output_dir))
                                self.Thread[layer] = LongTimeRunThing((script_dir,login_soft_script_name,
                                                                     run_scripts, data_type, jobname,
                                                                     output_id, layer, i if i <= 10 else i - 10, output_dir))                                

                                # self.run_genesis.moveToThread(self.Thread[layer])
                                # self.Thread[layer].started.connect(self.run_genesis.Run)
                                self.Thread[layer].start()
                                # print("start------------>", layer, self.Thread[layer].isRunning())
                                # self.Thread[layer].thread.wait()
                                # self.Thread[layer].finished.connect(self.Thread[layer].quit)
                                time.sleep(15)
                                # print("start------------>", layer, self.Thread[layer].isRunning())
                                theads.append(self.Thread[layer])
                                
                                while True:                                        
                                    time.sleep(2)
                                    runing_thread_num = 0
                                    for thread in theads:
                                        if thread.isRunning():
                                            runing_thread_num += 1
                                        else:
                                            continue
                                            
                                        for key, value in self.Thread.iteritems():
                                            if thread == value:
                                                finish_file = os.path.join(tmp_dir, "finish_{0}_{1}.log".format(output_id, key))
                                                if os.path.exists(finish_file):
                                                    thread.quit()                                                    
                                                print("---------->runing:", key)
                                    
                                    # 保证四个get运行
                                    if runing_thread_num < 4 and i < len(output_layers) - 1:
                                        #if "second_process" in args:
                                            #pid = self.get_genesis_running()
                                            #if len(pid) < 3:
                                                #break
                                            
                                            #if runing_thread_num < 1:
                                                #break                                            
                                        #else:
                                        break
                                    
                                    if i == len(output_layers) - 1 and runing_thread_num < 1:
                                        break
                            
                            # 放入中转站
                            output_path = "/tmp"
                            if sys.platform == "win32":      
                                output_path = r"\\192.168.2.126\workfile\lyh\output\{0}\{1}".format(jobname, output_id)
                                try:
                                    os.makedirs(output_path)
                                except:
                                    pass

                            success_log = True
                            arraylist_log = []
                            copy_files = []
                                        
                            for layer in output_layers:
                                filepath =os.path.join(output_dir, layer)
                                success_file = os.path.join(tmp_dir, "success_{0}_{1}.log".format(output_id, layer))

                                if not os.path.exists(filepath):
                                    log = u"输出层{0}程序异常，请手动输出！<br>".format(layer)
                                    arraylist_log.append(log)                                    
                                    log_file = os.path.join(output_path, "reoutput_layers.log")
                                    with open(log_file, "a") as f:
                                        f.write(layer+"\n")
                                        
                                    success_log = False                                
                                else:
                                    if not os.path.exists(success_file):
                                        #if "c1" in layer or "c2" in layer:
                                            #log_file = os.path.join(output_path, "reoutput_layers.log")
                                            #with open(log_file, "a") as f:
                                                #f.write(layer+"\n")
                                            #continue
                                        
                                        log = u"输出层{0}程序回读异常，请手动输出！<br>".format(layer)
                                        arraylist_log.append(log)
                                        success_log = False
                                        
                                        log_file = os.path.join(output_path, "recompare_layers.log")
                                        with open(log_file, "a") as f:
                                            f.write(layer+"\n")
                                            
                                        copy_files.append(filepath)                                    
                                    else:
                                        shutil.copy(filepath, dest_net_path+"/")
                            
                            if copy_files:
                                # 拷贝到中专目录供incampro回读
                                for filepath in copy_files:                                    
                                    if os.path.exists(filepath):
                                        shutil.copy(filepath, output_path)
                                    
                            if success_log:
                                self.update_mysql_data([u"OutputStatus = '{0}'".format(u"genesis输出完成"),
                                                        u"Status = '输出完成'"], condition="id={0}".format(output_id))
                            else:
                                if sys.platform == "win32":                                    
                                    self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                            u"Status = '{0}'".format(u"输出异常"),
                                                            u"AlarmLog = concat(AlarmLog,'{0}')".format(" ".join(arraylist_log))],
                                                           condition="id={0}".format(output_id))
                                else:
                                    self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                            u"Status = '{0}'".format(u"输出异常"),
                                                            u"AlarmLog = concat(AlarmLog,'{0}')".format(" ".join(arraylist_log))],
                                                           condition="id={0}".format(output_id))                                    
                                    
                            end_calc_time = time.time()
                            seconds = end_calc_time - start_calc_time
                            time_log = u"genesis总耗时:{0}分钟 <br>".format(round(seconds/60, 1))
                            self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(time_log),
                                                    "OutputTime = now()", ],
                                                   condition="id={0}".format(output_id))
                        
                            if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, jobname)):
                                os.unlink("{0}/outputing_{1}.log".format(tmp_dir, jobname))
                                
                            for name in os.listdir(tmp_dir):
                                filepath = os.path.join(tmp_dir,name)
                                if "success_{0}".format(output_id) in name:
                                    os.unlink(filepath)
                                
                                if "finish_{0}".format(output_id) in name:
                                    os.unlink(filepath)
                                    
                                if "calc_time_{0}".format(output_id) in name:
                                    os.unlink(filepath)
                                    
                            if os.path.exists(output_dir):
                                shutil.rmtree(output_dir)
                                
                        process = os.popen("ps -ef | grep {0}".format(jobname))
                        # print("ps -ef | grep {0}".format(jobname))
                        log = process.read()
                        # print("------------------------------->", log)
                        process.close()      
                        if log:
                            for line in log.split("\n"):
                                if "genesis_output_gerber" in line:
                                    pid = line.split()[1]
                                    kill_cmd = "kill %s" % pid.strip()
                                    print kill_cmd
                                    os.system(kill_cmd) 
                    
                    # if "not_delete_tgz" not in args:                        
                    run_scripts = "{0}/del_job.py no_gui".format(script_dir)
                    if "192.168.19.243" not in localip[2]:
                        os.system("python {0}/{2}.py {1}".format(script_dir, run_scripts, login_soft_script_name))
                        
                        if sys.platform <> "win32":                            
                            run_scripts = "{0}/del_job.py no_gui".format(script_dir)
                            os.system("python {0}/{2}.py {1}".format(script_dir, run_scripts, "no_gui_login_incam"))                           
                
            except Exception, e:
                print(e)
                
            if args and "second_process" not in args:   
                break
            
            time.sleep(60)
            
    def get_genesis_running(self):
        """获取genesis运行中的个数"""
        process = subprocess.Popen("d:/genesis/e97/misc/gateway WHO", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE) 
        login_users_info = process.communicate()[0]
        return [x for x in login_users_info.split() if x.strip()]
            
    def run_incam_gerber_output_type(self, *args):
        """incam输出gerber工具"""
        
        while True:
            try:
             
                dic_condition = {"Facotry": "S01H1","type": u"正式","data_type": u"输出GB资料","isOutput": "Y",}
                param = []          
                for k, v in dic_condition.iteritems():
                    param.append(u"{0}='{1}'".format(k, v))
                
                if "10.3.7.10" in localip[2]:                    
                    param.append(u"OutputStatus like '%转incam输出%'")
                else:
                    param.append(u"OutputStatus like '%输出异常(in_pcs)%'")
                
                if param:            
                    data_info = self.get_mysql_data(condtion=" and ".join(param))
                    #测试
                    if args:                        
                        data_info = self.get_mysql_data(condtion="id = {0}".format(*args))
                else:
                    data_info = []
                
                all_ouput_jobs = []
                dic_job_id = {}
                for info in sorted(data_info, key=lambda x: x["workLevel"] * -1):
                    if info["Job"] not in all_ouput_jobs:
                        all_ouput_jobs.append(info["Job"])
                        if not dic_job_id.has_key(info["Job"].lower()):
                            dic_job_id[info["Job"].lower()] = [str(info["id"])]
                        else:
                            dic_job_id[info["Job"].lower()].append(str(info["id"]))                    
    
                print(all_ouput_jobs)
                if all_ouput_jobs:
                    
                    for name in all_ouput_jobs:
                        name = name.lower()                    
                        print(os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)))
                        if not os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)):
                            break
                    else:
                        time.sleep(5)
                        continue
                    
                    print(os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)))
                    if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)):
                        time.sleep(5)
                        continue                    
                    
                    #if sys.platform == "win32":
                        #res = self.import_tgz(name, dic_job_id[name], "no_gui_login_incam_win")
                    #else:
                    res = self.import_tgz(name, dic_job_id[name])
                    #if res and os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)):
                        #self.update_mysql_data([u"OutputStatus = ''",
                                                #u"Status = ''",
                                                #u"AlarmLog = ''"],
                                                #condition="id in ({0})".format(",".join(dic_job_id[name])))
                        #time.sleep(5)
                        #continue                    
                    
                    print(res, os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, name)))
                    
                    if res :
                    
                        with open("{0}/outputing_{1}.log".format(tmp_dir, name), "w") as f:
                            f.write("running")
                            
                        start_calc_time = time.time()
                        
                        for info in sorted(data_info, key=lambda x: x["workLevel"] * -1):
                            
                            jobname = info["Job"].lower().strip()
                            if jobname != name:
                                continue
                            
                            output_id = info["id"]
                            
                            dest_net_path = info["OutputPath"]
                            if sys.platform != "win32":                                
                                dest_net_path = dest_net_path.replace("\\", "/")
                                dest_net_path = dest_net_path.replace(ur"//192.168.2.57/临时文件夹/系列资料临时存放区/", "/windows/33.file/")
                                dest_net_path = dest_net_path.replace(ur"//192.168.2.174/GCfiles/", "/windows/174.file/")
                            # print([dest_net_path])
                            try:
                                os.makedirs(dest_net_path)
                            except Exception, e:
                                print(e)
                            
                            if not os.path.exists(dest_net_path):                                
                                log = u"Linux中创建输出路径失败{0} <br>".format(dest_net_path)
                                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)], condition="id={0}".format(output_id))                    
                                continue
                            
                            output_dir = "{0}/{1}/{2}/{3}".format(tmp_dir, jobname, "gerber", output_id)
                            if os.path.exists(output_dir):
                                shutil.rmtree(output_dir)
                            
                            try:                                
                                os.makedirs(output_dir)
                            except Exception, e:
                                print(e)
                                pass                                                    
                            
                            run_scripts = os.path.join(script_dir, "Auto_Engineer_Output_Tools.py")
                            
                            success_file = os.path.join(tmp_dir, "success_{0}.log".format(output_id))
                            #此文件存在 则不删除中转站文件 以便另一台电脑重新输出比对
                            success_file_in_pcs = os.path.join(tmp_dir, "success_{0}_in_pcs.log".format(output_id))
                            os.system("rm -rf {0}".format(success_file))                            
    
                            data_type = "incampro_output_gerber"
                            if sys.platform == "win32":            
                                data_type = "genesis_output_gerber"
                            
                            os.environ["JOB"] = jobname
                            if "gui_run" in args:
                                if sys.platform == "win32":
                                    output_layers = [x for x in info["OutLayer"].split(";") if x.strip()]
                                    for layer in output_layers:                                        
                                        os.system("python %s/%s.py %s %s %s %s %s %s" %
                                                  (script_dir,login_soft_script_name, run_scripts, data_type, jobname, output_id, layer, "gui_run"))
                                else:                                        
                                    os.system("python %s/%s.py %s %s %s %s %s" %
                                              (script_dir,login_soft_script_name, run_scripts, data_type, jobname, output_id, "gui_run"))                               
                            else:
                                if sys.platform == "win32":
                                    output_layers = [x for x in info["OutLayer"].split(";") if x.strip()]
                                    for layer in output_layers:
                                        os.system("python %s/%s.py %s %s %s %s %s %s" %
                                                  (script_dir,login_soft_script_name, run_scripts, data_type, jobname, output_id, layer, "no_gui"))
                                else:
                                    os.system("python %s/%s.py %s %s %s %s %s" %
                                              (script_dir,login_soft_script_name, run_scripts, data_type, jobname, output_id, "no_gui")) 
                            
                            if not os.path.exists(success_file):
                                log = u"INCAMPRO 输出程序异常中断，请手动输出！<br>"                                
                                self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                        u"Status = '{0}'".format(u"输出异常"),
                                                        u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                                       condition="id={0}".format(output_id))                                
    
                            if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, jobname)):
                                os.unlink("{0}/outputing_{1}.log".format(tmp_dir, jobname))
                                
                            for name in os.listdir(tmp_dir):
                                filepath = os.path.join(tmp_dir,name)
                                if "success_{0}".format(output_id) in name:
                                    os.unlink(filepath)
                                
                                if "finish_{0}".format(output_id) in name:
                                    os.unlink(filepath)
                                    
                                if "calc_time_{0}".format(output_id) in name:
                                    os.unlink(filepath)                                  
                                    
                            if os.path.exists(output_dir):
                                shutil.rmtree(output_dir)
                            
                            if not os.path.exists(success_file_in_pcs):                                
                                #清除中转站文件
                                output_path = "/id/workfile/lyh/output/{0}/{1}".format(jobname, output_id)
                                if os.path.exists(output_path):
                                    shutil.rmtree(output_path) 
                        
                        end_calc_time = time.time()
                        seconds = end_calc_time - start_calc_time
                        time_log = u"incam总耗时:{0}分钟 <br>".format(round(seconds/60, 1))
                        self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(time_log),
                                                "OutputTime = now()", ],
                                               condition="id={0}".format(output_id))
                        
                    run_scripts = "{0}/del_job.py no_gui".format(script_dir)
                    if "192.168.19.243" not in localip[2]:
                        os.system("python {0}/{2}.py {1}".format(script_dir, run_scripts, login_soft_script_name))
                    
            except Exception, e:
                print(e)
                
            if args:
                break
            
            time.sleep(60)
                    
    def import_tgz(self, jobname, job_ids, log_incam_win_soft=None, tgz_import_path=None):
        """导入tgz资料"""        
        if sys.platform == "win32":            
            import_job_path = ur"//192.168.2.174/GCfiles/HDI全套tgz/{0}系列/{1}.tgz".format(jobname[1:4], jobname)
            if not os.path.exists(import_job_path):
                import_job_path = ur"//192.168.2.174/GCfiles/HDI全套tgz/{0}系列/{1}-inn.tgz".format(jobname[1:4], jobname)
        else:            
            import_job_path = u"/windows/174.tgz/{0}系列/{1}.tgz".format(jobname[1:4].upper(), jobname)
            if not os.path.exists(import_job_path):
                import_job_path = u"/windows/174.tgz/{0}系列/{1}-inn.tgz".format(jobname[1:4].upper(), jobname)
        
        os.environ["TGZ_IMPORT_PATH"] = ""
        if tgz_import_path:
            import_job_path = tgz_import_path
            if sys.platform == "win32": 
                os.environ["TGZ_IMPORT_PATH"] = tgz_import_path.encode("cp936")
            else:
                os.environ["TGZ_IMPORT_PATH"] = tgz_import_path.encode("utf8")
            
        if not os.path.exists(import_job_path):
            self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                    u"Status = '{0}'".format(u"输出异常"),
                                    u"AlarmLog = '{0}'".format(u'tgz资料不存在'),
                                    u"export_server = '{0}'".format(localip[2][0])],
                                   condition=u"Job='{0}' and id in ({1})".format(jobname, ",".join(job_ids)))             
            return 0        
        
        self.update_mysql_data([u"OutputStatus = '{0}'".format(u"开始导入tgz！"),
                                "OutputStartTime = now()", 
                                u"Status = '{0}'".format(u"输出中"),
                                u"AlarmLog = '{0}'".format(u'输出中'),
                                u"export_server = '{0}'".format(localip[2][0])],
                               condition=u"Job='{0}' and id in ({1})".format(jobname, ",".join(job_ids)))
        
        with open("{0}/outputing_{1}.log".format(tmp_dir, jobname), "w") as f:
            f.write("running")        
        
        job_path = r"/frontline/incampro_output/incamp_db1/jobs/%s" % jobname        
        if sys.platform == "win32":
            os.environ["GENESIS_EDIR"] = "d:/genesis/e97"
            os.environ["GENESIS_DIR"] = "d:/genesis"
            # if log_incam_win_soft is None:    
            job_path = r"%s/fw/jobs/%s" % (os.environ["GENESIS_DIR"], jobname)
            #else:
                #job_path = r"c:/incam/incam_db1/jobs/%s" % jobname
        else:
            if log_incam_win_soft == "no_gui_login_genesis":                
                os.environ["GENESIS_EDIR"] = "/genesis/e100"
                os.environ["GENESIS_DIR"] = "/genesis"
                job_path = r"%s/fw/jobs/%s" % (os.environ["GENESIS_DIR"], jobname)
        
        os.environ["JOB"] = jobname
        run_scripts = "{0}/del_job.py no_gui".format(script_dir)
        if "192.168.19.243" not in localip[2]:
            os.system("python {0}/{2}.py {1}".format(script_dir, run_scripts, login_soft_script_name if log_incam_win_soft is None else log_incam_win_soft))
        
            if os.path.exists(job_path):
                if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, jobname)):
                    os.unlink("{0}/outputing_{1}.log".format(tmp_dir, jobname))                   
                self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                        u"Status = '{0}'".format(u"输出异常"),
                                        u"AlarmLog = concat(AlarmLog,'{0}')".format(u'导入tgz删除旧资料失败，请联系程序工程师处理！')],
                                       condition=u"Job='{0}' and id in ({1})".format(jobname, ",".join(job_ids)))
                return 0
        
        run_scripts = os.path.join(script_dir, "auto_import_tgz_vgt_dblist.py")
        
        if sys.platform == "win32":
            #incam_win_soft is None:                
            os.system("python %s/%s.py %s %s %s %s %s %s" %
                      (script_dir, login_soft_script_name,
                       run_scripts, jobname, "hdi1", "genesis", "genesis", "no_gui"))
            #else:
                #os.system("python %s/%s.py %s %s %s %s %s %s" %
                          #(script_dir, log_incam_win_soft,
                           #run_scripts, jobname, "hdi1", "incam", "db1", "no_gui"))                
        else:
            if log_incam_win_soft == "no_gui_login_genesis":
                os.system("python %s/%s.py %s %s %s %s %s %s" %
                          (script_dir, log_incam_win_soft,
                           run_scripts, jobname, "hdi1", "genesis", "genesis", "no_gui"))
                
                if not os.path.exists(job_path):
                    shutil.copy(import_job_path, "/tmp/{0}.tgz".format(jobname))
                    os.environ["TGZ_IMPORT_PATH"] = "/tmp/{0}.tgz".format(jobname)
                    os.system("python %s/%s.py %s %s %s %s %s %s" %
                              (script_dir, log_incam_win_soft,
                               run_scripts, jobname, "hdi1", "genesis", "genesis", "no_gui"))
                    
                    os.system("rm -rf /tmp/{0}.tgz".format(jobname))
                    
            else:  
                os.system("python %s/%s.py %s %s %s %s %s %s" %
                          (script_dir, login_soft_script_name,
                           run_scripts, jobname, "hdi1", "incam", "db1", "no_gui"))
            
        if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, jobname)):
            os.unlink("{0}/outputing_{1}.log".format(tmp_dir, jobname))            
        
        if not os.path.exists(job_path):
            
            if log_incam_win_soft == "no_gui_login_genesis":
                if os.path.exists("{0}/outputing_{1}.log".format(tmp_dir, jobname)):
                    os.unlink("{0}/outputing_{1}.log".format(tmp_dir, jobname))                    
            
                start_time = self.get_current_format_time()
                self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                        u"Status = '{0}'".format(u"输出异常"),
                                        u"AlarmLog = concat(AlarmLog,'{0} {1}')".format(u'导入tgz失败', start_time)],
                                       condition=u"Job='{0}' and id in ({1})".format(jobname, ",".join(job_ids)))
            return 0
        
        filetime = os.path.getmtime(import_job_path)
        self.update_mysql_data([u"OutputStatus = '{0}'".format(u"导入tgz成功，等待输出！"),
                                u"TgzPath = '{0}'".format(import_job_path),
                                u"TgzFileTime = %s",],
                               condition=u"Job='{0}' and id in ({1})".format(jobname, ",".join(job_ids)),
                               params=datetime.datetime.fromtimestamp(filetime))
        
        return 1
    
    def auto_login_cloud_incampro(self):
        """自动登录云incampro 打开型号 占住HDI的license"""
        run_scripts = os.path.join(script_dir, "Auto_Engineer_Output_Tools.py")
        data_type = "create_job_open_for_hold_license"
        import_tgz_path = "/id/workfile/lyh/hold_cloud_license.tgz"
        job_path = r"/frontline/incampro_output/incamp_db1/jobs/hold_cloud_license"
        if not os.path.exists(job_path):            
            self.import_tgz("hold_cloud_license", ["-1"], tgz_import_path=import_tgz_path)
        os.environ["JOB"] = "hold_cloud_license"
        os.environ["VNCDISP"] = ":30"
        os.environ["VNCSTARTPATH"] = "/usr/bin/"
        os.system("python %s/%s.py %s %s %s %s %s %s %s %s" %
                  (script_dir,login_soft_script_name, run_scripts, data_type, "hold_cloud_license", "", "", "gui_run", "", ""))

    def auto_login_normal_incampro(self):
        """自动登录incampro 打开型号 占住HDI的license"""
        run_scripts = os.path.join(script_dir, "Auto_Engineer_Output_Tools.py")
        data_type = "create_job_open_for_hold_license"
        import_tgz_path = "/id/workfile/lyh/hold_cloud_license.tgz"
        job_path = r"/frontline/incampro/incamp_db1/jobs/hold_cloud_license"
        os.environ["INCAM_PRODUCT"] = "/frontline/incampro/release"
        if not os.path.exists(job_path):            
            self.import_tgz("hold_cloud_license", ["-1"], tgz_import_path=import_tgz_path)
        os.environ["JOB"] = "hold_cloud_license"
        os.environ["VNCDISP"] = ":30"
        os.environ["VNCSTARTPATH"] = "/usr/bin/"
        os.system("python %s/%s.py %s %s %s %s %s %s %s %s" %
                  (script_dir,login_soft_script_name, run_scripts, data_type, "hold_cloud_license", "", "", "gui_run", "", ""))
        
    def auto_bak_incampro_jobs(self):
        """自动备份incampro的临时跟正式资料20250116 by lyh"""
        run_scripts = os.path.join(script_dir, "auto_clear_bak_linshi_tgz.py")
        os.environ["INCAM_PRODUCT"] = "/frontline/incampro/release"
        os.environ["VNCSTARTPATH"] = "/usr/bin/"
        os.system("python %s/%s.py %s %s" %
                  (script_dir,login_soft_script_name, run_scripts, "no_gui"))
        
    def auto_bak_linshi_incampro_jobs(self):
        """自动清理临时层及备份tgz资料 by zl 20250205"""
        run_scripts = "/frontline/incam/server/site_data/scripts/sh_script/zl/crontab/ClearTempAndBackupLayer-main.py"# os.path.join(script_dir, "auto_clear_bak_linshi_tgz.py")
        os.environ["INCAM_PRODUCT"] = "/frontline/incampro/release"
        os.environ["VNCSTARTPATH"] = "/usr/bin/"        
        os.system("python %s/%s.py %s %s" %
                  (script_dir,login_soft_script_name, run_scripts, "no_gui"))
    
    def get_mysql_layer_info_data(self, condtion="1=1"):
        dbc_m = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='hdi_engineering', prod=3306,
                                   username='root', passwd='k06931!')           
        sql = u"""SELECT * FROM  hdi_engineering.incam_job_layer_info
        where {0}""".format(condtion)
        data_info = conn.SELECT_DIC(dbc_m, sql)
        dbc_m.close()
        return data_info
    
    def uploading_incam_tgz(self):
        """自动导入tgz"""
        
        job_data_info = get_inplan_jobs_for_uploading_layer_info(360)
        
        exits_jobs = []
        try:            
            exits_jobs = [x.strip().lower() for x in file("/id/workfile/lyh/jobs.log").readlines()]
        except:
            pass        
        i = 0
        for info in job_data_info:
            jobname = info["JOB_NAME"].lower()
            i += 1
            if jobname in exits_jobs:
                continue
            
            if jobname[1:4] in ["a86", "d10"]:
                continue
            
            with open("/id/workfile/lyh/jobs.log", "a") as f:
                f.write(jobname+"\n")
                
            filepath = ur"/windows/174.tgz/{0}系列/{1}.tgz".format(jobname[1:4], jobname)                
            if not os.path.exists(filepath):
                with open("/id/workfile/lyh/import_jobs.log", "a") as f:
                    f.write(jobname+"--->"+"not tgz!"+"\n")            
                continue
            
            job_path = "/id/incamp_db1/jobs/%s" % jobname
            if os.path.exists(job_path):
                with open("/id/workfile/lyh/import_jobs.log", "a") as f:
                    f.write(jobname+"--->"+"exists!"+"\n")
                continue
                    
            with open("/tmp/outputing_%s.log" % jobname, "w") as f:
                f.write("running")            
            
            print("-------------->", i, len(job_data_info))
            os.environ["JOB"] = jobname
            run_scripts = os.path.join(os.path.dirname(
                sys.argv[0]), "auto_import_tgz_vgt_dblist.py")
            os.environ["INCAM_PRODUCT"] = "/frontline/incampro/release"
            os.system("python /incam/server/site_data/scripts/sh_script/autoScheduleTask/no_gui_login_incam.py %s %s %s %s %s %s" %
                      (run_scripts, jobname, "hdi1", "incam", "db1", "no_gui"))
            
            print("------------>", job_path)
            if not os.path.exists(job_path):
                with open("/id/workfile/lyh/import_jobs.log", "a") as f:
                    f.write(jobname+"--->"+"import error!"+"\n")
            else:
                run_scripts = "/incam/server/site_data/scripts/sh_script/autoScheduleTask/read_job_step.py"
                os.system(
                    "python /incam/server/site_data/scripts/sh_script/autoScheduleTask/no_gui_login_incam.py %s no_gui" % (run_scripts))                
                         
                time_format = self.get_current_format_time()
                with open("/id/workfile/lyh/import_jobs.log", "a") as f:
                    f.write(jobname+"--->"+"import OK!"+" "+time_format+"\n")
                
                if not os.path.exists("/tmp/check_job_{0}_ok.log".format(jobname)):
                    with open("/id/workfile/lyh/job_layers_error.log", "a") as f:
                        f.write(jobname+"--->"+"read error"+"\n")
                else:
                    os.unlink("/tmp/check_job_{0}_ok.log".format(jobname))

            if os.path.exists("/tmp/outputing_%s.log" % jobname):
                os.unlink("/tmp/outputing_%s.log" % jobname)
                
            # break
    
    def uploading_genesis_layer_info_new(self):
        """自动检查并自动上传层信息 20231204 by lyh"""

        os.environ["GENESIS_EDIR"] = "d:/genesis/e97"
        os.environ["GENESIS_DIR"] = "d:/genesis"
        
        job_data_info = get_inplan_jobs_for_uploading_layer_info(180)
        
        array_layer_info = self.get_mysql_layer_info_data()
        dic_layer_info = {}
        dic_step_info = {}
        dic_symbol_info = {}
        for info in array_layer_info:
            dic_layer_info[info["job_name"]] = info["layer_info"]
            dic_step_info[info["job_name"]] = info["step_info"]
            dic_symbol_info[info["job_name"]] = info["symbol_info"]
            
            
        # joblists = file("d:/tmp/jobs.txt").readlines()
        # joblists = ["HA0110GI272A1"]
        # joblists = random.sample(lines, int(random.random() *10))
        
        #for i, line in enumerate(joblists):
            #jobname = line.strip().lower()            
        
        for info in job_data_info:
            jobname = info["JOB_NAME"].lower()
            
            #if jobname.upper() in "SD1012GH221A1,DA8622O6784E1	,SD1024E7213B1,SD1018G6226A1,BA8618P5845A2,DA8606PH759A4,BA8618P5845A3":
                #print jobname
                #continue
            
            filepath = ur"\\192.168.2.174\GCfiles\HDI全套tgz\{0}系列\{1}.tgz".format(jobname[1:4], jobname)
            if not os.path.exists(filepath):
                filepath = ur"\\192.168.2.29\gc\原2.33暂存\胜宏\{0}系列\{1}.tgz".format(jobname[1:4], jobname)
                
            if not os.path.exists(filepath):
                print "not tgz", jobname              
                continue
            
            uploading_info = True
            if dic_layer_info.has_key(jobname):
                try:                    
                    layer_info = json.loads(dic_layer_info[jobname], encoding='utf8')
                    uploading_tgz_time = layer_info.get("tgz_modify_time", "")
                    current_tgz_time = os.path.getmtime(filepath)
                    if uploading_tgz_time and uploading_tgz_time >= current_tgz_time:
                        uploading_info = False
                    
                    if not uploading_tgz_time:
                        uploading_info = False
                except:
                    pass
                
                #try:                    
                    #if dic_symbol_info[jobname]:
                        #print(jobname, "-------------->")
                        #uploading_info = False
                #except:
                    #pass                
            
            if dic_step_info.has_key(jobname):
                if not dic_step_info[jobname]:
                    print("step_info------------------->", None)
                    uploading_info = True
            
            if not uploading_info:
                continue            
            
            #print "start", jobname
            #continue
            with open("d:/tmp/outputing_%s.log" % jobname, "w") as f:
                f.write("running")
                
            os.environ["JOB"] = jobname
            run_scripts = "d:/genesis/sys/scripts/lyh/del_job.py no_gui"
            os.system(
                "python d:/genesis/sys/scripts/lyh/no_gui_login_genesis.py %s" % run_scripts)
            
            job_path = r"d:\genesis\fw\jobs\%s" % jobname

            run_scripts = os.path.join(os.path.dirname(
                sys.argv[0]), "auto_import_tgz_genesis_dblist.py")

            os.system("python d:/genesis/sys/scripts/lyh/no_gui_login_genesis.py %s %s %s %s %s %s" %
                      (run_scripts, jobname, "hdi1", "genesis", "genesis", "no_gui"))

            if not os.path.exists(job_path):
                print "not job", " ", jobname
                        
                if os.path.exists("d:/tmp/outputing_%s.log" % jobname):
                    os.unlink("d:/tmp/outputing_%s.log" % jobname)                       
                continue
            
            run_scripts = "d:/genesis/sys/scripts/lyh/uploading_tgz_layer_info.py"
            os.system(
                "python d:/genesis/sys/scripts/lyh/no_gui_login_genesis.py %s no_gui" % (run_scripts))              
            
            run_scripts = "d:/genesis/sys/scripts/lyh/del_job.py no_gui"
            os.system(
                "python d:/genesis/sys/scripts/lyh/no_gui_login_genesis.py %s" % run_scripts)         

            if os.path.exists("d:/tmp/outputing_%s.log" % jobname):
                os.unlink("d:/tmp/outputing_%s.log" % jobname)
    
    def uploading_test_point_info_record(self):
        """自动检测 阻抗测点tgz 登记输出信息"""
        dbc_m = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='hdi_electron_tools', prod=3306,
                                   username='hdi_web', passwd='!QAZ2wsx')         
        dirpath = ur"\\192.168.2.57\临时文件夹\系列资料临时存放区\03.CAM制作资料暂放（勿删）\000勿删\a86测点专用夹子"
        record_text_file = os.path.join(dirpath, u"已登记型号.txt")
        exits_record_jobs = []
        if os.path.exists(record_text_file):
            exits_record_jobs = [x.strip().lower() for x in file(record_text_file).readlines()]
            
        for name in os.listdir(dirpath):
            if ".tgz" in name:
                filepath = os.path.join(dirpath, name)
                jobname = name.split(".")[0].lower()
                filetime = os.path.getmtime(filepath)
                if (jobname +"_" +str(filetime)) in exits_record_jobs:
                    # print(jobname, filetime)
                    continue
                # print (name, jobname, filetime)
                index = jobname[1:4]
                sql = u"insert into hdi_electron_tools.hdi_job_tools\
                (job,facotry,type,data_type,dataname,outlayer,worklevel,\
                status,appuser,appuserid,apptime,isoutput,outputpath,pathtype,TempOutputPath) \
                values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),%s,%s,%s,%s)"                    
                conn.SQL_EXECUTE(dbc_m, sql, (jobname.upper(), "S01H1", u"临时",
                                              u"阻抗测点输出", u"阻抗测点输出", "",
                                              "1", u"待输出", u"系统",
                                              "84310",  "Y",
                                              ur"\\192.168.2.174\GCfiles\Drawing\{0}系列\{1}\MI\阻抗测点".format(index.upper(), jobname.upper()),
                                              u"正式",
                                              ur"\\192.168.2.174\GCfiles\Drawing\{0}系列\{1}\MI\阻抗测点".format(index.upper(), jobname.upper()),
                                              ))
                
                with open(record_text_file, "a") as f:
                    f.write(jobname+"_"+str(filetime)+"\n")
                    
                    
    def uploading_zy_measure_coordinate_info_record(self):
        """自动检测正业坐标量测 登记输出信息"""
        dbc_m = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='hdi_electron_tools', prod=3306,
                                   username='hdi_web', passwd='!QAZ2wsx')         
        select_sql = u"""select * from hdi_engineering.drawings_marked
        where datediff(now(),update_time) < 30 and
        job_name not in (select Job from hdi_electron_tools.hdi_job_tools where 
        data_type='正业坐标量测资料' and TIMESTAMPDIFF(MINUTE, apptime,now()) < 1440 and isoutput = 'Y')
        order by update_time desc"""
        data_info = conn.SELECT_DIC(dbc_m, select_sql)
        
        sql = u"select * from hdi_engineering.meascoordinate_base"
        exist_uploading_data_info = conn.SELECT_DIC(dbc_m, sql)
        current_day = self.get_current_format_time().split(" ")[0]
        update_jobs = []
        if data_info:
            for info in data_info:
                jobname = info["job_name"].split("@")[0]
                if len(jobname) != 13:
                    continue
                
                #if jobname not in ["FA8622O6784H1"]:
                    #continue                
                
                filepath = ur"\\192.168.2.174\GCfiles\HDI全套tgz\{0}系列\{1}.tgz".format(jobname[1:4], jobname)
                if not os.path.exists(filepath):
                    filepath = ur"\\192.168.2.174\GCfiles\HDI全套tgz\{0}系列\{1}-inn.tgz".format(jobname[1:4], jobname)
                #if not os.path.exists(filepath):
                    #filepath = ur"\\192.168.2.29\gc\原2.33暂存\胜宏\{0}系列\{1}.tgz".format(jobname[1:4], jobname)
                    #if not os.path.exists(filepath):
                        #filepath = ur"\\192.168.2.172\GCfiles\工程cam资料\{0}系列\{2}\{1}\{2}.tgz".format(jobname[1:4], jobname[-2:], jobname)
                    
                if not os.path.exists(filepath):
                    print("not tgz", jobname )             
                    continue
                
                if jobname in update_jobs:
                    continue                
                
                print("start--->", jobname)
                if exist_uploading_data_info:
                    is_continue = False
                    for dic_info in exist_uploading_data_info:
                        if dic_info["Job"] == jobname.upper():
                            try:                        
                                update_time = eval(dic_info["Remark"])["update_time"]
                            except Exception as e:
                                # print(e, exist_data_info)
                                update_time = ""
                            # print(update_time)
                            if str(info["update_time"]) == update_time:
                                # print("same time", jobname)
                                is_continue = True
                                break
                            
                    if is_continue:
                        if not filepath.endswith("-inn.tgz"):
                            # 全套tgz资料
                            sql = u"select * from hdi_electron_tools.hdi_job_tools where job = '{0}'\
                            and data_type='正业坐标量测资料'\
                            and isoutput = 'Y'\
                            and TgzPath like '%-inn.tgz%'".format(jobname.upper())
                            exist_data_info = conn.SELECT_DIC(dbc_m, sql)
                            # print("----->1", exist_data_info)
                            if exist_data_info:
                                # 之前是内层登记的 清除记录 重新输出
                                sql = """update hdi_electron_tools.hdi_job_tools
                                set OutputStatus = '',Status = '',AlarmLog = '',remark = 'update_zy_outer'
                                where id = {0}"""
                                # print("----->", exist_data_info[0]["id"], sql)
                                conn.SQL_EXECUTE(dbc_m, sql.format(exist_data_info[0]["id"]))
                            
                        continue
                    else:
                        sql = u"select * from hdi_electron_tools.hdi_job_tools where job = '{0}'\
                        and data_type='正业坐标量测资料'\
                        and isoutput = 'Y'\
                        and (remark <> 'update_zy_MI_date_{1}' or remark is null)".format(jobname.upper(), current_day)
                        exist_data_info = conn.SELECT_DIC(dbc_m, sql)
                        # print("----->2", exist_data_info)
                        if exist_data_info:                        
                            sql = """update hdi_electron_tools.hdi_job_tools
                            set OutputStatus = '',Status = '',AlarmLog = '',remark = 'update_zy_MI_date_{1}'
                            where id = {0}"""
                            # print("----->", exist_data_info[0]["id"], sql)
                            conn.SQL_EXECUTE(dbc_m, sql.format(exist_data_info[0]["id"], current_day))
                            continue
                
                sql = u"select * from hdi_electron_tools.hdi_job_tools where job = '{0}'\
                and data_type='正业坐标量测资料'\
                and isoutput = 'Y'".format(jobname.upper())
                exist_data_info = conn.SELECT_DIC(dbc_m, sql)
                if exist_data_info:
                    continue                
                
                # print("update", jobname)
                update_jobs.append(jobname)
                index = jobname[1:4]
                sql = u"insert into hdi_electron_tools.hdi_job_tools\
                (job,facotry,type,data_type,dataname,outlayer,worklevel,\
                status,appuser,appuserid,apptime,isoutput,outputpath,pathtype,TempOutputPath) \
                values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),%s,%s,%s,%s)"                    
                conn.SQL_EXECUTE(dbc_m, sql, (jobname.upper(), "S01H1", u"临时",
                                              u"正业坐标量测资料", u"正业坐标量测资料", "",
                                              "1", u"待输出", u"系统",
                                              "84310",  "Y",
                                              ur"\\192.168.2.57\临时文件夹\系列资料临时存放区\03.CAM制作资料暂放（勿删）\000勿删\正业坐标量测资料\{0}\{1}".format(index.upper(), jobname.upper()),
                                              u"正式",
                                              ur"\\192.168.2.57\临时文件夹\系列资料临时存放区\03.CAM制作资料暂放（勿删）\000勿删\正业坐标量测资料\{0}\{1}".format(index.upper(), jobname.upper()),
                                              ))
        
        print(update_jobs)
        
    def uploading_laser_autoconvert_info(self):
        """镭射自动转档登记20240229 by lyh"""
        
        dbc_m = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='hdi_electron_tools', prod=3306,
                                   username='hdi_web', passwd='!QAZ2wsx')    
        
        select_sql = """select DISTINCT Job  from drill_zsDb_Hdi.HdiJgzMakeRecord where state = 0 and datediff(now(),applydate) < 60"""
        data_info = conn.SELECT_DIC(dbc_m, select_sql)
        if data_info:
            for info in data_info:
                jobname = info["Job"]
                
                sql = u"select * from hdi_electron_tools.hdi_job_tools where job = '{0}'\
                and data_type='镭射转档资料'\
                and TIMESTAMPDIFF(MINUTE, apptime,now()) < 1440".format(jobname.upper())
                data_info = conn.SELECT_DIC(dbc_m, sql)
                if data_info:
                    # print("exists", jobname)
                    continue
                
                filepath = ur"\\192.168.2.174\GCfiles\HDI全套tgz\{0}系列\{1}.tgz".format(jobname[1:4], jobname)
                outer_tgz = False
                if os.path.exists(filepath):
                    outer_tgz = True
                    
                try:        
                    lay_num = int(jobname[4:6])
                except:
                    pass
                
                index = jobname[1:4]
                dir_path = ur"\\192.168.2.174\GCfiles\Program\工程辅助资料\{0}系列\{1}".format(index, jobname)
                dest_path = ur"\\192.168.2.174\GCfiles\Program\Laser\5代机6H代机钻带(有效65X65)\{0}系列\{1}".format(index, jobname)
                laser_layers = []
                if os.path.exists(dir_path):
                    for name in os.listdir(dir_path):
                        # if name.endswith(".write") and jobname.lower() in name.lower():
                        if re.match("{0}.s\d+-\d+(-\d+)?(-\d+)?(-\d+)?(-\d+)?.write".format(jobname.lower()), name.lower()):
                            dest_file_path = os.path.join(dest_path, name)
                            current_file_path = os.path.join(dir_path, name)
                            
                            #外层未审核不转档外层镭射
                            if not outer_tgz:
                                if "s1-" in name.lower() or "s{0}-".format(lay_num) in name.lower():
                                    continue
                                
                            if not os.path.exists(dest_file_path):                        
                                laser_layers.append(name)
                            else:
                                dest_format = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(dest_file_path)))
                                current_format = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(current_file_path)))
                                # if os.path.getmtime(dest_file_path) < os.path.getmtime(current_file_path):
                                if dest_format != current_format:  
                                    laser_layers.append(name)
                                    #有镭射钻带更新资料，需清理旧转档再重新输出 20240309 by lyh
                                    for other_name in os.listdir(dest_path):
                                        if name.replace(".write", "write").replace(".", "-") in other_name:
                                            other_file_path = os.path.join(dest_path, other_name)
                                            os.unlink(other_file_path)
                                            
                # print(jobname, laser_layers)
                if laser_layers:                    
                    sql = u"insert into hdi_electron_tools.hdi_job_tools\
                    (job,facotry,type,data_type,dataname,outlayer,worklevel,\
                    status,appuser,appuserid,apptime,isoutput,outputpath,pathtype,TempOutputPath) \
                    values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),%s,%s,%s,%s)"                    
                    conn.SQL_EXECUTE(dbc_m, sql, (jobname.upper(), "S01H1", u"临时",
                                                  u"镭射转档资料", u"镭射转档资料", ";".join(laser_layers),
                                                  "1", u"待输出", u"系统",
                                                  "84310",  "Y",
                                                  ur"\\192.168.2.174\GCfiles\Program\Laser\5代机6H代机钻带(有效65X65)\{0}系列\{1}".format(index.upper(), jobname.upper()),
                                                  u"正式",
                                                  ur"\\192.168.2.174\GCfiles\Program\Laser\5代机6H代机钻带(有效65X65)\{0}系列\{1}".format(index.upper(), jobname.upper()),
                                                  ))
                    
    def uploading_laser_autoconvert_info_all(self):
        """镭射自动转档登记 比对最近一周输出的镭射钻带
        是否跟转档的镭射资料是否一致 不一致的重新登记 20241107 by Lyh"""
        
        dbc_p = conn.MYSQL_CONNECT(hostName='192.168.2.19',
                                   database='project_status', prod=3306,
                                   username='root', passwd='k06931!')
        dbc_m = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='hdi_electron_tools', prod=3306,
                                   username='hdi_web', passwd='!QAZ2wsx')         
        
        select_sql = """select DISTINCT job from engineering.laser_output_log where datediff(now(),log_time) < 30"""
        data_info = conn.SELECT_DIC(dbc_p, select_sql)
        if data_info:
            for info in data_info:
                jobname = info["job"]
                
                #if jobname.upper() not in ["HA7710PC467E1"]:
                    #continue
                #sql = u"select * from hdi_electron_tools.hdi_job_tools where job = '{0}'\
                #and data_type='镭射转档资料'\
                #and TIMESTAMPDIFF(MINUTE, apptime,now()) < 1440".format(jobname.upper())
                #data_info = conn.SELECT_DIC(dbc_m, sql)
                #if data_info:
                    ## print("exists", jobname)
                    #continue
                
                filepath = ur"\\192.168.2.174\GCfiles\HDI全套tgz\{0}系列\{1}.tgz".format(jobname[1:4], jobname)
                outer_tgz = False
                if os.path.exists(filepath):
                    outer_tgz = True
                    
                try:        
                    lay_num = int(jobname[4:6])
                except:
                    pass
                
                index = jobname[1:4]
                dir_path = ur"\\192.168.2.174\GCfiles\Program\工程辅助资料\{0}系列\{1}".format(index, jobname)
                dest_path = ur"\\192.168.2.174\GCfiles\Program\Laser\5代机6H代机钻带(有效65X65)\{0}系列\{1}".format(index, jobname)
                laser_layers = []
                if os.path.exists(dir_path):
                    for name in os.listdir(dir_path):
                        # if name.endswith(".write") and jobname.lower() in name.lower():
                        if re.match("{0}.s\d+-\d+(-\d+)?(-\d+)?(-\d+)?(-\d+)?.write".format(jobname.lower()), name.lower()):
                            dest_file_path = os.path.join(dest_path, name)
                            current_file_path = os.path.join(dir_path, name)
                            
                            #外层未审核不转档外层镭射
                            if not outer_tgz:
                                if "s1-" in name.lower() or "s{0}-".format(lay_num) in name.lower():
                                    continue
                                
                            #if not os.path.exists(dest_file_path):                        
                                #laser_layers.append(name)
                            #else:
                            if os.path.exists(dest_file_path):                                
                                try:
                                    dest_format = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(dest_file_path)))
                                    current_format = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(current_file_path)))
                                    # if os.path.getmtime(dest_file_path) < os.path.getmtime(current_file_path):
                                    if dest_format != current_format:                                    
                                        print(jobname, name, dest_format ,current_format)
                                        laser_layers.append(name)
                                        #有镭射钻带更新资料，需清理旧转档再重新输出 20240309 by lyh
                                        for other_name in os.listdir(dest_path):
                                            if name.replace(".write", "write").replace(".", "-") in other_name:
                                                other_file_path = os.path.join(dest_path, other_name)
                                                os.unlink(other_file_path)
                                except Exception as e:
                                    print(jobname, str(e))
                                                
                print(jobname, laser_layers)
                if laser_layers:                    
                    sql = u"insert into hdi_electron_tools.hdi_job_tools\
                    (job,facotry,type,data_type,dataname,outlayer,worklevel,\
                    status,appuser,appuserid,apptime,isoutput,outputpath,pathtype,TempOutputPath) \
                    values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),%s,%s,%s,%s)"                    
                    conn.SQL_EXECUTE(dbc_m, sql, (jobname.upper(), "S01H1", u"临时",
                                                  u"镭射转档资料", u"镭射转档资料", ";".join(laser_layers),
                                                  "1", u"待输出", u"系统1",
                                                  "84310",  "Y",
                                                  ur"\\192.168.2.174\GCfiles\Program\Laser\5代机6H代机钻带(有效65X65)\{0}系列\{1}".format(index.upper(), jobname.upper()),
                                                  u"正式",
                                                  ur"\\192.168.2.174\GCfiles\Program\Laser\5代机6H代机钻带(有效65X65)\{0}系列\{1}".format(index.upper(), jobname.upper()),
                                                  ))
                    
    def uploading_laser_barcode_info(self):
        """镭雕资料MI已维护信息登记 20241129 by lyh"""
        
        dbc_m = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='hdi_electron_tools', prod=3306,
                                   username='hdi_web', passwd='!QAZ2wsx')    
        
        select_sql = """
        SELECT DISTINCT a.* FROM project_Status.trace_code_record a,
        hdi_engineering.incam_job_layer_info c
        where 
        a.code_type = 1
        and a.mi_checker is not null 
        and a.mi_checker <> ''
        and c.job_name = a.job_name
        -- and a.job_name like '%183%912%'"""
        data_info = conn.SELECT_DIC(dbc_m, select_sql)
        if data_info:
            for info in data_info:
                jobname = info["job_name"]
                
                sql = u"select * from hdi_electron_tools.hdi_job_tools where job = '{0}'\
                and data_type='镭雕资料'".format(jobname.upper())
                data_info = conn.SELECT_DIC(dbc_m, sql)
                if data_info:
                    continue
                
                if info["tracing_code"] is None or info["tracing_code"] == "":
                    continue
                
                tracing_code = info["tracing_code"].split("|")[0]
                
                index = jobname[1:4]
                sql = u"insert into hdi_electron_tools.hdi_job_tools\
                (job,facotry,type,data_type,dataname,outlayer,worklevel,\
                status,appuser,appuserid,apptime,isoutput,outputpath,pathtype,TempOutputPath) \
                values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),%s,%s,%s,%s)"                    
                conn.SQL_EXECUTE(dbc_m, sql, (jobname.upper(), "S01H1", u"临时",
                                              u"镭雕资料", u"镭雕资料", tracing_code,
                                              "1", u"待输出", u"系统",
                                              "84310",  "Y",
                                              ur"\\192.168.2.174\GCfiles\Silk\镭雕资料\{0}系列\{1}".format(index.upper(), jobname.upper()),
                                              u"正式",
                                              ur"\\192.168.2.174\GCfiles\Silk\镭雕资料\{0}系列\{1}".format(index.upper(), jobname.upper()),
                                              ))

    def update_symbol_info_to_mysql(self):
        """根据工程任务计划状态 定时更新追溯码信息20241031 by lyh"""
        """"barcode_symbol_info": [{"edit": {"TOP": [], "BOT": [["barcode5x1.5", "58.3", "36.6", 250, "c2"]]},
        "d-coupon_1-3": {"TOP": [], "BOT": [["barcode5x1.5", "30.2", "6.8", 250, "c2"]]},
        "icg": {"TOP": [], "BOT": [["barcode5x1.5", "308.5", "3.9", 250, "c2"]]},
        "d-coupon_8-10": {"TOP": [], "BOT": [["barcode5x1.5", "29.9", "8.1", 250, "c2"]]}},
        {"vip_coupon": 1, "hct-coupon-2": 1, "hct-coupon": 1, "set": 9, "drill_test_coupon": 4,
        "edit": 18, "qie_hole_coupon_new_drl": 2, "hct_coupon_new": 1, "icg": 1, "plusa-floujie": 40,
        "plus1-floujie": 40, "hct_coupon_new_1": 1, "d-coupon_1-3": 1, "sm4-coupon": 9, "cu-coupon": 1,
        "dzd_cp": 13, "d-coupon_8-10": 1}]"""
        dbc_p = conn.MYSQL_CONNECT(hostName='192.168.2.19',
                                   database='project_status', prod=3306,
                                   username='root', passwd='k06931!') 
        sql = "select * from hdi_engineering.incam_job_layer_info\
        where datediff(now(),create_time) < 30"
        data_info = conn.SELECT_DIC(dbc_p, sql)
        
        for dic_info in data_info:
            jobname = dic_info["job_name"].lower()            
            
            if jobname != "cd1024e7213b8":
                continue
            
            # print(dic_info["symbol_Status"])
            #if not (dic_info["symbol_Status"] is None or dic_info["symbol_Status"] == ""):
                ## print(jobname, "0")
                #continue
            
            try:                        
                step_info = json.loads(dic_info["step_info"], encoding='utf8')
            except:
                # print(jobname, "1")
                continue
            try:
                mysql_symbol_info = json.loads(dic_info["symbol_info"], encoding='utf8')
            except Exception as e:
                # print(jobname, "2", e)
                mysql_symbol_info = None
                
            if step_info.get("barcode_symbol_info", None):
                dic_barcode_info, dic_step_nums = step_info["barcode_symbol_info"]
                dic_symbol_info = {"TOP":{"MM":{"SET":0,"PCS":0,"COUPON":0},"AM":{"SET":0,"PCS":0,"COUPON":0}},
                                   "BOT":{"MM":{"SET":0,"PCS":0,"COUPON":0},"AM":{"SET":0,"PCS":0,"COUPON":0}}}
                is_break = False
                for stepname, values in dic_barcode_info.iteritems():
                    if isinstance(values, list):
                        is_break = True
                        #with open("d:/symbol_info.log", "w") as f:
                            #f.write(jobname+"\n")
                        break
                    
                    for direct, array_symbol_info in values.iteritems():
                        for symbol_info in array_symbol_info:                                
                            if symbol_info[3] in [250, 260]:
                                symbol_type = "MM"
                            else:
                                symbol_type = "AM"                            
                            if re.match("^set(_\d+)?", stepname) and \
                                 "loss" not in stepname and \
                                 "coupon" not in stepname:
                                step_type = "SET"
                            elif re.match("^edit(_\d+)?", stepname) and \
                                 "loss" not in stepname and \
                                 "coupon" not in stepname:
                                step_type = "PCS"
                            else:
                                step_type = "PCS"
                            dic_symbol_info[direct][symbol_type][step_type] += dic_step_nums[stepname]
                            
                if is_break:
                    # print(jobname, "3")
                    continue
                
                if mysql_symbol_info:
                    uploading_type = False
                    for direct, values in mysql_symbol_info.iteritems():
                        if direct not in ["TOP", "BOT"]:
                            continue
                        for symbol_type, symbol_nums_info in values.iteritems():
                            for step_type,num in symbol_nums_info.iteritems():
                                if num != dic_symbol_info[direct][symbol_type][step_type]:
                                    uploading_type = True
                                    break
                else:
                    uploading_type = True
                
                #if not uploading_type:
                    #print(jobname, "4")
                    
                #if dic_info["symbol_Status"] is None:
                    #uploading_type = True
                #if dic_info["symbol_Status"] == "":
                    #uploading_type = True
                
                # print(jobname, "5")
                # continue
                if uploading_type and dic_barcode_info:
                    sql = """select psj.*
                    from project_status.project_status_jobmanage psj
                    WHERE job = '{0}'
                    order by id desc"""
                    job_process_info = conn.SELECT_DIC(dbc_p, sql.format(jobname))
                        
                    #已审核完的检测
                    # print(job_process_info, )
                    if job_process_info and job_process_info[0].get("ocheckfinish_time", ""):                    
                        dic_symbol_info["update_time"] = self.get_current_format_time()
                        sql = u"update hdi_engineering.incam_job_layer_info  set symbol_info=%s,symbol_Status=%s,\
                        create_time=now() where job_name = '{0}'".format(jobname)
                        conn.SQL_EXECUTE(dbc_p, sql, (json.dumps(dic_symbol_info),'new'))
        
    def uploading_genesis_layer_info(self):
        """批量自动上传层信息 20231204 by lyh"""

        os.environ["GENESIS_EDIR"] = "d:/genesis/e97"
        os.environ["GENESIS_DIR"] = "d:/genesis"       

        exists_jobs = []
        if os.path.exists("d:/tmp/finish_job.log"):
            exists_jobs = [name.strip() for name in file(
                "d:/tmp/finish_job.log").readlines()]
            
            
        if os.path.exists("d:/tmp/not_tgz.log"):
            exists_jobs += [name.strip() for name in file(
                "d:/tmp/not_tgz.log").readlines()]
            
        joblists = file("d:/tmp/jobs.txt").readlines()
        # joblists = ["HA0110GI272A1"]
        # joblists = random.sample(lines, int(random.random() *10))
        
        num = 0
        for i, line in enumerate(joblists):
            jobname = line.strip().lower()
            
            if os.path.exists("d:/tmp/outputing_%s.log" % jobname):
                continue
            
            #if os.path.exists("d:/tmp/finish_job.log"):
                #exists_jobs += [name.strip() for name in file(
                    #"d:/tmp/finish_job.log").readlines()]                
    
            if jobname in "".join(exists_jobs).lower():
                continue
            
            print "start", jobname
            filepath = ur"\\192.168.2.174\GCfiles\HDI全套tgz\{0}系列\{1}.tgz".format(jobname[1:4], jobname)
            if not os.path.exists(filepath):
                filepath = ur"\\192.168.2.29\gc\原2.33暂存\胜宏\{0}系列\{1}.tgz".format(jobname[1:4], jobname)
                
            if not os.path.exists(filepath):
                print "not tgz", jobname
                with open("d:/tmp/not_tgz.log", "a") as f:
                    f.write(jobname+"\n")                
                continue
            
            if len(jobname) not in [13]:
                print "len:", len(jobname), "--->", jobname
                continue
            
            with open("d:/tmp/outputing_%s.log" % jobname, "w") as f:
                f.write("running")
                
            os.environ["JOB"] = jobname
            run_scripts = "d:/genesis/sys/scripts/lyh/del_job.py no_gui"
            os.system(
                "python d:/genesis/sys/scripts/lyh/no_gui_login_genesis.py %s" % run_scripts)
            
            job_path = r"d:\genesis\fw\jobs\%s" % jobname

            run_scripts = os.path.join(os.path.dirname(
                sys.argv[0]), "auto_import_tgz_genesis_dblist.py")

            os.system("python d:/genesis/sys/scripts/lyh/no_gui_login_genesis.py %s %s %s %s %s %s" %
                      (run_scripts, jobname, "hdi1", "genesis", "genesis", "no_gui"))

            if not os.path.exists(job_path):
                print "not job", " ", jobname
                with open("d:/tmp/not_job_import.log", "a") as f:
                    f.write(jobname+"\n")
                        
                if os.path.exists("d:/tmp/outputing_%s.log" % jobname):
                    os.unlink("d:/tmp/outputing_%s.log" % jobname)                       
                continue
            
            exists_jobs.append(jobname)           
            
            run_scripts = "d:/genesis/sys/scripts/lyh/del_job.py no_gui"
            os.system(
                "python d:/genesis/sys/scripts/lyh/no_gui_login_genesis.py %s" % run_scripts)
            
            if os.path.exists("d:/tmp/finish_job.log"):
                exists_jobs += [name.strip() for name in file(
                    "d:/tmp/finish_job.log").readlines()]             

            with open("d:/tmp/finish_job.log", "a") as f:
                f.write(jobname + "\n")
                
            if os.path.exists("d:/tmp/outputing_%s.log" % jobname):
                os.unlink("d:/tmp/outputing_%s.log" % jobname)            
                
            num += 1
            if num > 40:
                break
            
    def find_slot_hole_info(self):
        """排查半槽 或半孔 20231215 by lyh"""

        os.environ["GENESIS_EDIR"] = "d:/genesis/e97"
        os.environ["GENESIS_DIR"] = "d:/genesis"       

        exists_jobs = []
        if os.path.exists("d:/tmp/finish_job.log"):
            exists_jobs = [name.strip() for name in file(
                "d:/tmp/finish_job.log").readlines()]
            
            
        if os.path.exists("d:/tmp/not_tgz.log"):
            exists_jobs += [name.strip() for name in file(
                "d:/tmp/not_tgz.log").readlines()]
            
        joblists = file("d:/tmp/jobs.txt").readlines()
        # joblists = ["HA0110GI272A1"]
        # joblists = random.sample(lines, int(random.random() *10))
        
        num = 0
        for i, line in enumerate(joblists):
            jobname = line.strip().lower()
            
            if len(jobname) != 13:
                continue
            
            if os.path.exists("d:/tmp/outputing_1%s.log" % jobname):
                continue
            
            #if os.path.exists("d:/tmp/finish_job.log"):
                #exists_jobs += [name.strip() for name in file(
                    #"d:/tmp/finish_job.log").readlines()]                
    
            if jobname in "".join(exists_jobs).lower():
                continue
            
            print "start", jobname
            filepath = ur"\\192.168.2.174\GCfiles\HDI全套tgz\{0}系列\{1}.tgz".format(jobname[1:4], jobname)
            if not os.path.exists(filepath):
                filepath = ur"\\192.168.2.29\gc\原2.33暂存\胜宏\{0}系列\{1}.tgz".format(jobname[1:4], jobname)
                
            if not os.path.exists(filepath):
                print "not tgz", jobname
                with open("d:/tmp/not_tgz.log", "a") as f:
                    f.write(jobname+"\n")                
                continue
            
            if len(jobname) not in [13]:
                print "len:", len(jobname), "--->", jobname
                continue
            
            with open("d:/tmp/outputing_1%s.log" % jobname, "w") as f:
                f.write("running")
            
            # os.system("python d:/genesis/sys/scripts/lyh/check_tgz_barcode_symbol.py {0}".format(filepath.encode("cp936").replace("\\", "/")))
            os.environ["JOB"] = jobname
            run_scripts = "d:/genesis/sys/scripts/lyh/del_job.py no_gui"
            os.system(
                "python d:/genesis/sys/scripts/lyh/no_gui_login_genesis.py %s" % run_scripts)
            
            job_path = r"d:\genesis\fw\jobs\%s" % jobname

            run_scripts = "d:/genesis/sys/scripts/lyh/auto_import_tgz_genesis_dblist.py"

            os.system("python d:/genesis/sys/scripts/lyh/no_gui_login_genesis.py %s %s %s %s %s %s" %
                      (run_scripts, jobname, "hdi1", "genesis", "genesis", "no_gui"))

            if not os.path.exists(job_path):
                print "not job", " ", jobname
                with open("d:/tmp/not_job_import.log", "a") as f:
                    f.write(jobname+"\n")
                        
                if os.path.exists("d:/tmp/outputing_1%s.log" % jobname):
                    os.unlink("d:/tmp/outputing_1%s.log" % jobname)                       
                continue
            
            os.environ["STEP"] = "panel"
            run_scripts = "d:/genesis/sys/scripts/lyh/check_all_process_barcode_info.py"
            os.system(
                "python d:/genesis/sys/scripts/lyh/no_gui_login_genesis.py %s no_gui" % (run_scripts))            
            
            run_scripts = "d:/genesis/sys/scripts/lyh/del_job.py no_gui"
            os.system(
                "python d:/genesis/sys/scripts/lyh/no_gui_login_genesis.py %s" % run_scripts)
                
            exists_jobs.append(jobname)

            if os.path.exists("d:/tmp/finish_job.log"):
                exists_jobs += [name.strip() for name in file(
                    "d:/tmp/finish_job.log").readlines()]             

            with open("d:/tmp/finish_job.log", "a") as f:
                f.write(jobname + "\n")
                
            if os.path.exists("d:/tmp/outputing_1%s.log" % jobname):
                os.unlink("d:/tmp/outputing_1%s.log" % jobname)            
                
            #num += 1
            #if num > 60:
                #break

    def check_loss_test_pad_comp(self):
        """检测loss测试pad是否补偿 20250306 by zl"""

        os.environ["GENESIS_EDIR"] = "d:/genesis/e97"
        os.environ["GENESIS_DIR"] = "d:/genesis"

        exists_jobs = []
        if os.path.exists("d:/tmp/finish_job.log"):
            exists_jobs = [name.strip() for name in file("d:/tmp/finish_job.log").readlines()]

        if os.path.exists("d:/tmp/not_tgz.log"):
            exists_jobs += [name.strip() for name in file("d:/tmp/not_tgz.log").readlines()]

        joblists = file("d:/tmp/check_loss_test_pad_comp_jobs.txt").readlines()
        # joblists = ["HA0110GI272A1"]
        # joblists = random.sample(lines, int(random.random() *10))

        # num = 0
        for i, line in enumerate(joblists):
            jobname = line.strip().lower()

            if len(jobname) != 13:
                continue

            if os.path.exists("d:/tmp/outputing_1%s.log" % jobname):
                continue

            # if os.path.exists("d:/tmp/finish_job.log"):
            # exists_jobs += [name.strip() for name in file(
            # "d:/tmp/finish_job.log").readlines()]

            if jobname in "".join(exists_jobs).lower():
                continue

            print "start", jobname
            filepath = ur"\\192.168.2.174\GCfiles\HDI全套tgz\{0}系列\{1}.tgz".format(jobname[1:4], jobname)
            if not os.path.exists(filepath):
                filepath = ur"\\192.168.2.29\gc\原2.33暂存\胜宏\{0}系列\{1}.tgz".format(jobname[1:4], jobname)

            if not os.path.exists(filepath):
                print "not tgz", jobname
                with open("d:/tmp/not_tgz.log", "a") as f:
                    f.write(jobname + "\n")
                continue

            if len(jobname) not in [13]:
                print "len:", len(jobname), "--->", jobname
                continue

            with open("d:/tmp/outputing_1%s.log" % jobname, "w") as f:
                f.write("running")

            # os.system("python d:/genesis/sys/scripts/lyh/check_tgz_barcode_symbol.py {0}".format(filepath.encode("cp936").replace("\\", "/")))
            os.environ["JOB"] = jobname
            run_scripts = "d:/genesis/sys/scripts/lyh/del_job.py no_gui"
            os.system(
                "python d:/genesis/sys/scripts/lyh/no_gui_login_genesis.py %s" % run_scripts)

            job_path = r"d:\genesis\fw\jobs\%s" % jobname

            run_scripts = "d:/genesis/sys/scripts/lyh/auto_import_tgz_genesis_dblist.py"

            os.system("python d:/genesis/sys/scripts/lyh/no_gui_login_genesis.py %s %s %s %s %s %s" %
                      (run_scripts, jobname, "hdi1", "genesis", "genesis", "no_gui"))

            if not os.path.exists(job_path):
                print "not job", " ", jobname
                with open("d:/tmp/not_job_import.log", "a") as f:
                    f.write(jobname + "\n")

                if os.path.exists("d:/tmp/outputing_1%s.log" % jobname):
                    os.unlink("d:/tmp/outputing_1%s.log" % jobname)
                continue

            os.environ["STEP"] = "panel"
            run_scripts = "d:/genesis/sys/scripts/zl/CheckLossTestPadComp-genesis.py"
            os.system(
                "python d:/genesis/sys/scripts/lyh/no_gui_login_genesis.py %s no_gui" % (run_scripts))

            run_scripts = "d:/genesis/sys/scripts/lyh/del_job.py no_gui"
            os.system(
                "python d:/genesis/sys/scripts/lyh/no_gui_login_genesis.py %s" % run_scripts)

            exists_jobs.append(jobname)

            if os.path.exists("d:/tmp/finish_job.log"):
                exists_jobs += [name.strip() for name in file(
                    "d:/tmp/finish_job.log").readlines()]

            with open("d:/tmp/finish_job.log", "a") as f:
                f.write(jobname + "\n")

            if os.path.exists("d:/tmp/outputing_1%s.log" % jobname):
                os.unlink("d:/tmp/outputing_1%s.log" % jobname)

            # num += 1
            # if num > 1:
            #     break

    def uploading_copper_usage(self):
        """自动上传残铜率 20230525 by lyh"""

        os.environ["GENESIS_EDIR"] = "c:/genesis/e97"
        os.environ["GENESIS_DIR"] = "c:/genesis"       

        exists_jobs = []
        if os.path.exists("c:/tmp/finish_job.log"):
            exists_jobs = [name.strip() for name in file(
                "c:/tmp/finish_job.log").readlines()]
            
            
        if os.path.exists("c:/tmp/not_tgz.log"):
            exists_jobs += [name.strip() for name in file(
                "c:/tmp/not_tgz.log").readlines()]
            
        lines = file("c:/tmp/jobs.txt").readlines()
        # lines = ["HB7810PI099A1"]
        joblists = random.sample(lines, int(random.random() *10))
        
        num = 0
        for i, line in enumerate(joblists):
            jobname = line.strip().lower()
            
            if os.path.exists("c:/tmp/outputing_%s.log" % jobname):
                continue
            
            #if os.path.exists("d:/tmp/finish_job.log"):
                #exists_jobs += [name.strip() for name in file(
                    #"d:/tmp/finish_job.log").readlines()]                
    
            if jobname in "".join(exists_jobs).lower():
                continue            
            
            print "start", jobname
            filepath = ur"\\192.168.2.174\GCfiles\HDI全套tgz\{0}系列\{1}.tgz".format(jobname[1:4], jobname)
            if not os.path.exists(filepath):
                filepath = ur"\\192.168.2.29\gc\原2.33暂存\胜宏\{0}系列\{1}.tgz".format(jobname[1:4], jobname)
                
            if not os.path.exists(filepath):
                print "not tgz", jobname
                with open("c:/tmp/not_tgz.log", "a") as f:
                    f.write(jobname+"\n")                
                continue
            
            if len(jobname) not in [13]:
                print "len:", len(jobname), "--->", jobname
                continue
            
            with open("c:/tmp/outputing_%s.log" % jobname, "w") as f:
                f.write("running")
                
            os.environ["JOB"] = jobname
            run_scripts = "c:/genesis/sys/scripts/lyh/del_job.py"
            os.system(
                "python c:/genesis/sys/scripts/lyh/no_gui_login_genesis.py %s" % run_scripts)
            
            job_path = r"c:\genesis\fw\jobs\%s" % jobname

            run_scripts = os.path.join(os.path.dirname(
                sys.argv[0]), "auto_import_tgz_genesis_dblist.py")

            os.system("python c:/genesis/sys/scripts/lyh/no_gui_login_genesis.py %s %s %s %s %s" %
                      (run_scripts, jobname, "hdi1", "genesis", "genesis"))

            if not os.path.exists(job_path):
                print "not job", " ", jobname
                with open("c:/tmp/not_job_import.log", "a") as f:
                    f.write(jobname+"\n")
                        
                if os.path.exists("c:/tmp/outputing_%s.log" % jobname):
                    os.unlink("c:/tmp/outputing_%s.log" % jobname)                       
                continue
            
            exists_jobs.append(jobname)
            
            run_scripts = "c:/genesis/sys/scripts/lyh/uploading_copper_usage.py"
            os.system(
                "python c:/genesis/sys/scripts/lyh/no_gui_login_genesis.py %s" % (run_scripts))
            
            run_scripts = "c:/genesis/sys/scripts/lyh/del_job.py"
            os.system(
                "python c:/genesis/sys/scripts/lyh/no_gui_login_genesis.py %s" % run_scripts)
            
            if os.path.exists("c:/tmp/finish_job.log"):
                exists_jobs += [name.strip() for name in file(
                    "c:/tmp/finish_job.log").readlines()]             

            with open("c:/tmp/finish_job.log", "a") as f:
                f.write(jobname + "\n")
                
            if os.path.exists("c:/tmp/outputing_%s.log" % jobname):
                os.unlink("c:/tmp/outputing_%s.log" % jobname)            
                
            num += 1
            if num > 30:
                break
    
if __name__ == "__main__":
    main = scheduleTask()
    func = None
    try:
        func = sys.argv[1]
    except Exception, e:
        print e
        
    args = []
    try:
        args = sys.argv[2:]
    except Exception, e:
        print 'args:', e
        
    # 测试    
    if func is None:
        func = "uploading_zy_measure_coordinate_info_record"
        # args = ["26953","gui_run"]
    ####

    if func is None:
        main.run()
    else:
        if hasattr(main, func):
            if args:
                result = getattr(main, func)(*args)
            else:
                result = getattr(main, func)()
            
            if result:
                try:
                    result = str(result) if not isinstance(
                        result, unicode) else result
                    uploadinglog(__credits__, __version__ +
                                 result + " " + func, "")
                except Exception, e:
                    print "uploading:", e                
                
            if func == "find_slot_hole_info" \
               or func == "uploading_genesis_layer_info_new" \
               or func == "run_delete_scale_drill_output_type"\
               or func == "uploading_laser_autoconvert_info"\
               or func == "run_clear_scale_drill_output_type"\
               or func == "uploading_laser_autoconvert_info_all"\
               or func == "update_symbol_info_to_mysql":                
                # 获取父进程ID
                import psutil
                parent_process = psutil.Process(psutil.Process().ppid())
                parent_process_id = parent_process.pid
                psutil.Process(parent_process_id).kill()                