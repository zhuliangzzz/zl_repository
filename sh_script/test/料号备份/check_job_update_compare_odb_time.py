#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = "luthersy"
__date__ = "20250102"
__version__ = "Revision: 1.0.0 "
__credits__ = u"""推送资料更新不一致 """

import sys
import os
if sys.platform == "win32":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package_HDI")   
else:
    scriptPath = "%s/scripts" % os.environ.get('SCRIPTS_DIR', '/incam/server/site_data')
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")
    
import time
import re
import GetData
import json
import MySQL_DB
conn = MySQL_DB.MySQL()
dbc_m = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='hdi_engineering', prod=3306,
                           username='root', passwd='k06931!')

class job_update_check:
    """"""

    def __init__(self):
        """Constructor"""
        self.getDATA = GetData.Data()
        
    
    def run_check(self):
        """开始检测"""
        sql = """select job_name from  hdi_engineering.job_lock_data
        where TIMESTAMPDIFF(MINUTE,  update_date,now()) < 1440*5"""
        data_info = conn.SELECT_DIC(dbc_m, sql)
        jobnames = [info["job_name"] for info in data_info]
        # status_change = {'lock_add': u'锁定', 'unlock': u'解锁'}
        
        arraylist = []
        for jobname in jobnames:
            #if jobname not in ["dd1012gh168a4"]:
                #continue
            lock_info = self.getJOB_LockInfo(jobname, dataType='locked_log')
            key_array = sorted(lock_info.keys(), reverse=True)
            check_save_log = False
            unlock_layers = []
            for unlock_time in key_array:
                # print (lock_info[unlock_time])
                if len(lock_info[unlock_time]["unlock"]) != 0:
                    for lock_i, lock_detail in enumerate(lock_info[unlock_time]["unlock"]):
                        # unlock_steps = lock_detail['step']
                        unlock_layers = lock_detail['layers']
                        lock_steps = []
                        lock_layers = []
                        for lock_time in key_array:
                            if len(lock_info[lock_time]["lock_add"]) != 0:
                                for lock_i, lock_detail in enumerate(lock_info[lock_time]["lock_add"]):                        
                                    lock_steps = lock_detail['step']
                                    lock_layers = lock_detail['layers']
                        
                            if lock_steps and lock_layers and \
                               int(lock_time) > int(unlock_time) and \
                               abs(int(unlock_time) - time.time()) < 60 * 60 * 24 * 3:
                                # print(int(unlock_time),  time.time(), abs(int(unlock_time) - time.time()), time.strftime('%Y%m%d %H:%M:%S', time.localtime(int(unlock_time))))
                                if set(lock_layers) & set(unlock_layers):
                                    check_save_log = True
                                    break
                                
                        if check_save_log:
                            break
                        
                if check_save_log:
                    break
                        
            if check_save_log:
                save_log_path = "/id/incamp_db1/jobs/{0}/user/save_log".format(jobname)
                arraylist_modify_layer = []
                if os.path.exists(save_log_path):
                    # print(jobname, save_log_path)
                    # arraylist.append(jobname)
                    lines = file(save_log_path).readlines()
                    check_modify = False
                    for line in lines:
                        if "Created" in line:
                            check_modify = False
                        if "Deleted" in line:
                            check_modify = False
                        if "Modifier" in line:
                            res = re.findall("(202\d/\d{2}/\d{2} \d{2}:\d{2}:\d{2})", line)
                            if res:
                                # print(res)
                                if res[0] > time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(int(unlock_time))):
                                    check_modify = True
                        
                        if check_modify:
                            if "LAYER" in line:                                
                                arraylist_modify_layer.append(line.split("-->")[-1])
        
                # print(arraylist_modify_layer)
                if arraylist_modify_layer:
                    matrixinfo=self.get_erp_job_matrixinfo(jobname)
                    if not matrixinfo:
                        continue
                    
                    step_list, inner_layers, outer_layers, drill_layers,board_layers = self.get_job_matrix(matrixinfo)
                    all_normal_layers = inner_layers+outer_layers+drill_layers+board_layers
                    modify_normal_layers = []
                    for layer_info in arraylist_modify_layer:
                        for layer in layer_info.split(","):
                            if layer.strip() in all_normal_layers:
                                # print(jobname, layer.strip())
                                if layer.strip() not in modify_normal_layers:                                    
                                    modify_normal_layers.append(layer.strip())
                    
                    if modify_normal_layers:                        
                        job_info_path = "/id/incamp_db1/jobs/{0}/misc/info".format(jobname)
                        hdi_tgz_path = u"/windows/174.file/HDI全套tgz/{0}系列/{1}.tgz".format(jobname[1:4].upper(), jobname)
                        if os.path.exists(job_info_path) and os.path.exists(hdi_tgz_path):                            
                            info_time = time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(os.path.getmtime(job_info_path)))
                            tgz_time = time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(os.path.getmtime(hdi_tgz_path)))
                            # print(jobname, "save_time:", info_time, "tgz_time:", tgz_time, "modify_layers", modify_normal_layers)
                            arraylist.append((jobname, u"保存时间:", info_time, "<br>", u"TGZ时间:", tgz_time, "<br>", u"被修改层次", " ".join(modify_normal_layers)))
        
        if arraylist:
            dbc_m1 = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='hdi_electron_tools', prod=3306,
                                       username='hdi_web', passwd='!QAZ2wsx')            
            for log in arraylist:                
                sql = u"select * from hdi_electron_tools.hdi_job_tools where job = '{0}' and isoutput = 'Y' and dataname = 'TGZ资料是否更新'".format(log[0])
                datainfo = conn.SELECT_DIC(dbc_m1, sql)
                if datainfo:
                    sql = u"update hdi_electron_tools.hdi_job_tools  \
                    set outputstatus=%s,alarmlog=%s where job = '{0}'".format(log[0])
                    conn.SQL_EXECUTE(dbc_m1, sql, (u"输出异常(推送消息)", "".join(log[1:])))
                else:
                    sql = u"insert into hdi_electron_tools.hdi_job_tools\
                    (job,facotry,type,data_type,dataname,outlayer,worklevel,\
                    status,appuser,appuserid,apptime,isoutput,outputstatus,pathtype,alarmlog) \
                    values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),%s,%s,%s,%s)"                    
                    conn.SQL_EXECUTE(dbc_m1, sql, (log[0], "S01H1", u"临时",
                                                  u"钉钉推送", u"TGZ资料是否更新", "",
                                                  "1", u"输出异常", u"系统",
                                                  "84310",  "Y",
                                                  u"输出异常(推送消息)",
                                                  u"正式",
                                                  "".join(log[1:]),
                                                  ))
                # break
            
            # print("--------------------------------->\n输出异常(推送消息)")            
            #for a in arraylist:
                #print(a)
                            
    def get_job_matrix(self, m_info):

        inner_layers = []
        outer_layers = []
        drill_layers = []
        board_layers = []
        other_layers = """blue-c
        blue-s
        blue_c
        blue_s
        blue_cs
        ty-c
        ty-s
        sgt-c
        sgt-s
        gold-c
        gold-s
        linemask-c
        linemask-s
        etch-c
        etch-s
        xlym-c
        xlym-s
        linek-c
        linek-s
        linek-c-1
        linek-s-1
        linek-c-2
        linek-s-2
        lp
        """
        other_layers = [x.strip() for x in other_layers.split("\n")]
        
        step_list = m_info['gCOLstep_name']
        layer_list = m_info['gROWname']
        for row in m_info['gROWrow']:
            num = m_info['gROWrow'].index(row)
            if "-ls" in m_info['gROWname'][num]:
                m_info['gROWname'][num] = m_info['gROWname'][num].split("-")[0]
                
            if m_info['gROWcontext'][num] == 'board' or m_info['gROWname'][num] in other_layers:
                board_layers.append(m_info['gROWname'][num])                
            if m_info['gROWcontext'][num] == 'board' and m_info['gROWlayer_type'][num] == 'drill':                
                drill_layers.append(m_info['gROWname'][num])
            
            #翟鸣通知增加铝片 导气板 树脂塞孔20241213 by lyh
            if m_info['gROWlayer_type'][num] == 'drill':
                if m_info['gROWname'][num] in ['sz.lp', 'sz...dq', "ww"] or \
                   re.match("^sz.*\.lp$|^sz.*\.\.\.dq$", m_info['gROWname'][num]) or \
                   re.match("^dld\d{1,2}-\d{1,2}$", m_info['gROWname'][num]):
                    drill_layers.append(m_info['gROWname'][num])                    
                    
            if m_info['gROWname'][num] in ["ww"] or \
               re.match("^dld\d{1,2}-\d{1,2}$", m_info['gROWname'][num]):
                drill_layers.append(m_info['gROWname'][num])                    

            if m_info['gROWcontext'][num] == 'board' and m_info['gROWside'][num] == 'inner':
                inner_layers.append(m_info['gROWname'][num])

            elif m_info['gROWcontext'][num] == 'board' and m_info['gROWlayer_type'][num] == 'signal' and (
                    m_info['gROWside'][num] == 'top' or m_info['gROWside'][num] == 'bottom'):
                outer_layers.append(m_info['gROWname'][num])

        # 周涌通知 外层盖孔资料需排除掉 20221117 by lyh       
        inner_layers = [layer for layer in inner_layers
                        if layer.split("-")[0] not in outer_layers]

        return step_list, inner_layers, outer_layers, drill_layers,board_layers                            
        
    def getJOB_LockInfo(self, jobname, dataType='locked_info'):
        """
        从数据库中获取料号的锁记录
        :param dataType: 获取的数据类型（status:locked_info log:locked_log）
        :return:dict
        """
        
        lockData = self.getDATA.getLock_Info(jobname)

        try:
            return json.loads(lockData[dataType], encoding='utf8')
        except:
            # print u'传入的数据参数异常'
            return {}
        
    def get_erp_job_matrixinfo(self, jobname):
        sql = "select * from hdi_engineering.incam_job_layer_info where job_name = '{0}'".format(jobname)
        datainfo = conn.SELECT_DIC(dbc_m, sql)
        dic_layer_info = {}
        if datainfo:
            try:
                dic_layer_info = json.loads(datainfo[0]["layer_info"], encoding='utf8')
            except:
                dic_layer_info = {}
                
        return dic_layer_info        
        
if __name__ == "__main__":
    main = job_update_check()
    main.run_check()
    