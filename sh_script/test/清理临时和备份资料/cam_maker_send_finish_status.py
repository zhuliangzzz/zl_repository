#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = "luthersy"
__date__ = "20241219"
__version__ = "Revision: 1.0.0 "
__credits__ = u"""CAM制作送审 """
"""sh_hdi_warning_director_process"""


import os
import sys
if sys.platform == "win32":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    scriptPath = "%s/scripts" % os.environ.get('SCRIPTS_DIR', '/incam/server/site_data')
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")

import json
import MySQL_DB
import GetData
import time
import re
import gClasses
import subprocess
conn = MySQL_DB.MySQL()
dbc_m = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='hdi_engineering', prod=3306,
                           username='root', passwd='k06931!')
dbc_p = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='project_status', prod=3306,
                           username='root', passwd='k06931!')

from create_ui_model import showMessageInfo, app, \
     showQuestionMessageInfo, show_message_picture_ui
from genesisPackages import job, matrixInfo, \
     outsignalLayers, innersignalLayers, solderMaskLayers, \
     silkscreenLayers, signalLayers, get_sr_area_flatten

from PyQt4 import QtCore, QtGui, Qt
try:
    from TOPCAM_IKM import IKM
    ikm_fun = IKM()
except Exception, e:
    showMessageInfo(u"连接topcam数据库异常，请联系程序组处理:", str(e))
    exit(1)
    
baju_not_defender_jobs = []
check_log_file = "/id/workfile/lyh/check_job/joblist.log"
if os.path.exists(check_log_file):
    baju_not_defender_jobs = [x.strip().upper() for x in file(check_log_file).readlines()]    
    
try:            
    paramJson = json.loads(os.environ.get('PARAM').replace(';', ','))
    processID = int(paramJson['process_id'])
    jobID = int(paramJson['job_id'])
    user = paramJson['user']
    jobname = os.environ["JOB"]
except Exception, e:
    showMessageInfo(u"topcam数据json异常，请联系程序组处理:", str(e))
    exit(1)
    
make_type = sys.argv[1]

userDir = os.environ.get('JOB_USER_DIR', None)
#记录状态
status_file = os.path.join(userDir, 'cam_finish_status_{0}.log'.format(job.name))

lock_json_file = os.path.join(userDir, '{0}_job_lock.json'.format(job.name))

from mwClass_V2 import AboutDialog

def send_message_to_director(message_result, job_name, label_result):
    """发送审批结果界面 20221122 by lyh"""
    submitData = {
        'site': u'HDI板事业部',
        'job_name': job_name,
        'pass_tpye': 'CAM',
        'pass_level': 8,
        'assign_approve': '43982|44566|44024|84310|83288|68027|91259',
        'pass_title': message_result,
    }
    Dialog = AboutDialog(label_result, cancel=True, appCheck=True, appData=submitData, style=None)
    Dialog.exec_()

    # --根据审批的结果返回值
    if Dialog.selBut in ['x', 'cancel']:
        return False
    if Dialog.selBut == 'ok':
        return True
    
    return False

sys.path.insert(0, "/incam/server/site_data/scripts/lyh")
from auto_sh_hdi_check_rules import auto_check_rule    
check_rule = auto_check_rule()

class send_finish_status(QtGui.QWidget):
    """"""

    def __init__(self):
        """Constructor"""
        super(send_finish_status, self).__init__()
        self.setMainUIstyle()
        self.getDATA = GetData.Data()
        
        self.lock_info = self.getJOB_LockInfo(dataType='locked_info')
        
        self.job_make_info = self.getJOB_LockInfo(dataType='job_make_status')
        if self.job_make_info:            
            with open(status_file, 'w') as file_obj:
                json.dump(self.job_make_info, file_obj)
            
        self.show_ui()
        
    def get_process_is_running(self, process_id, job_id, condition="status = 'Done'"):
        
        sql = """select * from pdm_job_workflow where process_id = {0} and job_id = {1} and {2}"""
        data_info = ikm_fun.PG.SELECT_DIC(ikm_fun.dbc_p, sql.format(process_id, job_id, condition))

        return data_info   
    
    def convert_message(self, warn_text):
        msgInfo = u'<table border="1"><tr><th>类型</th><th>检测项目</th><th>内容</th></tr>'
        for msg_dict in warn_text:
            if msg_dict['type'] == 'information':
                msgInfo += u'<tr><td bgcolor=%s>%s</td><td>%s</td><td>%s</td></tr>' % (
                'green', u'提示',msg_dict["check_type"], msg_dict['content'])
            elif msg_dict['type'] == 'warning':
                msgInfo += u'<tr><td bgcolor=%s>%s</td><td>%s</td><td>%s</td></tr>' % (
                'gray', u'检查',msg_dict["check_type"], msg_dict['content'])
            elif msg_dict['type'] == 'forbiding':
                msgInfo += u'<tr><td bgcolor=%s>%s</td><td>%s</td><td>%s</td></tr>' % (
                'orange', u'警告', msg_dict["check_type"],msg_dict['content'])
            elif msg_dict['type'] == 'forbiding_not_output':
                msgInfo += u'<tr><td bgcolor=%s>%s</td><td>%s</td><td bgcolor=red>%s</td></tr>' % (
                'red', u'禁止输出', msg_dict["check_type"],msg_dict['content'])                

        msgInfo += u'</table></body></html><br><br> 注意：检查信息请自行检查核对，但警告信息必须处理，警告信息不能处理的，请申请主管放行！'
        return msgInfo
                
    def check_tgz_output_warning_log(self, check_description_list=[],
                                     check_inner_outer=None):
        """检测tgz输出前 全自动检测记录拦截信息审批"""
        #sql = u"""select * from pdm_job_check_log_list
        #where job_id = '{0}'
        #and (check_process like '检测异常%%' or check_process = '' or check_process is null)
        #and check_status = 'normal'
        #and check_user = '{1}'"""
        #array_job_info = ikm_fun.PG.SELECT_DIC(ikm_fun.dbc_p, sql.format(jobID, user))
        #if not array_job_info:
            #sql = u"""select * from pdm_job_check_log_list
            #where job_id = '{0}'
            #and (check_process like '检测异常%%' or check_process = '' or check_process is null)
            #and check_status = 'normal' order by id desc"""
            #array_job_info = ikm_fun.PG.SELECT_DIC(ikm_fun.dbc_p, sql.format(jobID, user))
        
        # new_array_job_info = array_job_info
        # if "H60614YB119B1" in job.name.upper():
            # job.PAUSE("ddd")
        sql = u"""select * from pdm_job_check_log_list
        where job_id = '{0}'            
        and check_status = 'normal' order by id desc"""
        array_job_info = ikm_fun.PG.SELECT_DIC(ikm_fun.dbc_p, sql.format(jobID, user))
        
        new_array_job_info = []
        functions = list(set([dic_info["check_function_name"] for dic_info in array_job_info]))
        for name in functions:
            array_function = [dic_info for dic_info in array_job_info
                              if  dic_info["check_function_name"] == name]
            # job.PAUSE(str(array_function))
            if len(array_function) > 1:
                for dic_info in array_function:
                    if dic_info["check_process"] is None or dic_info["check_process"] == "":
                        continue
                    else:
                        if u"检测异常" in dic_info["check_process"].decode("utf8"):                                
                            new_array_job_info.append(dic_info)
                            
                        break
                else:
                    new_array_job_info.append(array_function[0])
            else:
                if len(array_function) == 1:
                    if array_function[0]["check_process"] is None or \
                       array_function[0]["check_process"] == "" or \
                       u"检测完成" not in array_function[0]["check_process"].decode("utf8"):     
                        new_array_job_info.append(array_function[0])
                        
        # print(new_array_job_info)
        label_arraylist_log = []
        message_arraylist_log = []
        must_check = False
        if new_array_job_info:            
            for dic_info in new_array_job_info:
                
                if check_inner_outer and check_inner_outer != "lock_inner_outer":
                    if dic_info["note"] in ["inner", "outer", "coreinner"]:                        
                        if dic_info["note"] not in check_inner_outer:
                            continue
                        
                dic_label_msg = {}
                dic_send_msg = {}
                dic_label_msg["check_type"] = dic_info["function_description"].decode("utf8")
                if len(dic_label_msg["check_type"]) > 40:
                    dic_label_msg["check_type"] = dic_info["function_description"].decode("utf8")[:40] + "..."
                    
                dic_send_msg["check_type"] = dic_info["function_description"].decode("utf8")
                
                function_name = dic_info["check_function_name"]
                if check_description_list and \
                   function_name not in check_description_list:
                    continue
                
                #print("------------------------------------------>")
                #if dic_info["check_function_name"] == 'check_target_distance_uploading_to_erp check_current_job_same_size_defender':
                    #print(dic_info)
                
                #if "-lyh" in jobname:
                    #showMessageInfo(dic_info["check_process"].decode("utf8"))
                # 翟鸣通知暂时屏蔽 20241213 by lyh 
                # 先测试送审的必须查看 20250110 by lyh
                #if processID in [2173, ]:                    
                if dic_info["check_process"] and \
                   dic_info["check_process"].decode("utf8") == u"检测异常" and \
                   u"已查看" not in dic_info["check_process"].decode("utf8"):
                    dic_label_msg["type"] = "forbiding_not_output"
                    dic_send_msg["type"] = "forbiding_not_output"
                    dic_label_msg["content"] = u"此项目检测异常，但异常内容未检查，请点击查看标记或异常已查！"
                    dic_send_msg["content"] = u"此项目检测异常，但异常内容未检查，请点击查看标记或异常已查！"
                    label_arraylist_log.append(dic_label_msg)                               
                    message_arraylist_log.append(dic_send_msg)
                    must_check = True
                    continue                
                
                if dic_info["check_process"] and \
                   u"审核放行" in dic_info["check_process"].decode("utf8"):
                    continue
                
                #if user in ["84310"]:                    
                    #if dic_info["check_process"] and \
                       #u"已查看" in dic_info["check_process"].decode("utf8"):
                        #continue                   
                
                if dic_info["forbid_or_information"].decode("utf8") != u"拦截(不放行)" and \
                   dic_info["check_process"] and \
                   u"已查看" in dic_info["check_process"].decode("utf8"):
                    if (dic_info["check_log"] and u"运行异常中断，请尝试手动运行试试！" in dic_info["check_log"].decode("utf8")) or\
                       (dic_info["check_process"] and u"检测中" in dic_info["check_process"].decode("utf8")) or \
                       (dic_info["check_process"] is None or dic_info["check_process"] == ""):
                        pass
                    else:
                        continue
                
                if job.name.upper() in baju_not_defender_jobs:
                    if dic_label_msg["check_type"] in [u"同料号不同版本靶距是否防呆"]:
                        continue

                if dic_info["check_process"] is None or dic_info["check_process"] == "":
                    dic_label_msg["content"] = u"此项目未运行，请运行检测程序后再输出tgz！"
                    dic_send_msg["content"] = u"此项目未运行，请运行检测程序后再输出tgz！"
                else:                        
                    dic_label_msg["content"] = dic_info["check_log"].decode("utf8")
                    if len(dic_label_msg["content"]) > 50:
                        dic_label_msg["content"] = dic_info["check_log"].decode("utf8")[:50] + "..."
                        
                    dic_send_msg["content"] = dic_info["check_log"].decode("utf8")
                    
                if dic_info["forbid_or_information"].decode("utf8") == u"提示":
                    dic_label_msg["type"] = "warning"
                    dic_send_msg["type"] = "warning"
                elif dic_info["forbid_or_information"].decode("utf8") == u"拦截(不放行)":
                    dic_label_msg["type"] = "forbiding_not_output"
                    dic_send_msg["type"] = "forbiding_not_output"
                    must_check = True
                elif dic_info["forbid_or_information"].decode("utf8") == u"拦截":
                    dic_label_msg["type"] = "forbiding"
                    dic_send_msg["type"] = "forbiding"
                    must_check = True
                    if dic_label_msg["check_type"] in [u"检测金手指引线导通性"]:
                        if u"未发现定义属性.string=gf 的金手指pad" in dic_send_msg["content"]:                            
                            dic_label_msg["type"] = "forbiding_not_output"
                            dic_send_msg["type"] = "forbiding_not_output"
                    
                    if dic_send_msg["content"] and u"运行异常中断，请尝试手动运行试试！" in dic_send_msg["content"]:
                        dic_label_msg["type"] = "forbiding_not_output"
                        dic_send_msg["type"] = "forbiding_not_output"
                        
                    if dic_info["check_process"] and u"检测中" in dic_info["check_process"].decode("utf8"):
                        dic_label_msg["type"] = "forbiding_not_output"
                        dic_send_msg["type"] = "forbiding_not_output"
                        dic_label_msg["content"] = u"此项目未运行，请运行检测程序后再输出tgz！"
                        dic_send_msg["content"] = u"此项目未运行，请运行检测程序后再输出tgz！"                        
                                              
                    
                if dic_info["check_process"] is None or dic_info["check_process"] == "":
                    dic_label_msg["type"] = "forbiding"
                    dic_send_msg["type"] = "forbiding"
                    must_check = True
                    #if dic_label_msg["check_type"] in [u"化金面积检测",
                                                       #u"检测金手指漏镀&蚀刻引线&镀金面积上传",]:                                        
                        #dic_label_msg["type"] = "forbiding_not_output"
                        #dic_send_msg["type"] = "forbiding_not_output"
                        
                    if dic_info["forbid_or_information"].decode("utf8") == u"拦截" or \
                       dic_info["forbid_or_information"].decode("utf8") == u"拦截(不放行)":
                        dic_label_msg["type"] = "forbiding_not_output"
                        dic_send_msg["type"] = "forbiding_not_output"                          

                label_arraylist_log.append(dic_label_msg)                               
                message_arraylist_log.append(dic_send_msg)
                
        if must_check:            
            return self.convert_message(label_arraylist_log), self.convert_message(message_arraylist_log)
        
        return None    
        
    def show_ui(self):
        self.setGeometry(700, 300, 0, 0)

        self.setWindowFlags(Qt.Qt.Window | Qt.Qt.WindowStaysOnTopHint)
        self.setObjectName("mainWindow")
        layer_out = self.creat_ui()
        # layer_out.setSizeConstraint(Qt.QLayout.SetFixedSize)
        self.setLayout(layer_out)

        self.setFixedWidth(400)
        layer_out.setSizeConstraint(Qt.QLayout.SetFixedSize)
        
        self.setMainUIstyle()
        self.setWindowTitle(u"CAM资料送审退送信息界面 %s" % __version__)
        
        if make_type == "cam_maker":
            self.widget2.setEnabled(False)
            self.director_finish_btn.setEnabled(False)
            self.director_reback_btn.setEnabled(False)
        else:
            self.widget1.setEnabled(False)
            self.cam_finish_btn.setEnabled(False)
            self.clear_status_btn.setEnabled(False)
           
        self.initial_value()
        
        self.setValue()
        
        self.set_enable_disable()
        
    def set_enable_disable(self):
        for key1, key2,key3 in [(u"内层完成送审", u"内层送审状态", u"内层审核状态"),
                                (u"外层完成送审",u"外层送审状态",u"外层审核状态"),
                                (u"全套完成送审",u"全套送审状态",u"全套审核状态"),
                                (u"临时层完成送审",u"临时层送审状态",u"临时层审核状态")] :
            if self.dic_editor[key3].text() == QtCore.QString(u"审核完成") and key1 != u"临时层完成送审":
                self.dic_editor[key1].setEnabled(False)        
        
    def initial_value(self):
        """初始化参数"""
        self.dic_label[u"内层审核状态"].hide()
        self.dic_label[u"外层审核状态"].hide()
        self.dic_label[u"临时层审核状态"].hide()
        self.dic_label[u"全套审核状态"].hide()    
        self.dic_label[u"内层送审状态"].hide()
        self.dic_label[u"外层送审状态"].hide()
        self.dic_label[u"临时层送审状态"].hide()
        self.dic_label[u"全套送审状态"].hide()        
        self.dic_label[u"(芯板)内层送审状态"].hide()
        self.dic_label[u"(芯板)内层审核状态"].hide()        
        
        if "linshi_modify" in sys.argv[1:]:
            """此条件仅限凌戈夫使用"""
            for key1, key2,key3 in [(u"(芯板)内层完成送审", u"(芯板)内层送审状态", u"(芯板)内层审核状态"),
                                    (u"内层完成送审", u"内层送审状态", u"内层审核状态"),
                                    (u"外层完成送审",u"外层送审状态",u"外层审核状态"),
                                    (u"全套完成送审",u"全套送审状态",u"全套审核状态"),
                                    (u"临时层完成送审",u"临时层送审状态",u"临时层审核状态")] :
                if key1 != u"临时层完成送审":
                    self.dic_editor[key1].setEnabled(False)
        
    def get_current_format_time(self):
        time_form = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        return time_form
    
    def check_record_week_picihao_info(self):
        # 检测是否登记周期信息 20241021 by lyh          
        res = check_rule.get_week_picihao_banci_info()
        if res:
            dic_tgz_week_layers, dic_tgz_barcode_week_layers, dic_tgz_banci_layers, dic_tgz_picihao_layers, week_font = res
            if dic_tgz_week_layers or dic_tgz_barcode_week_layers or dic_tgz_banci_layers or dic_tgz_picihao_layers:
                data_info3 = self.get_process_is_running(1860, jobID)
                if not data_info3:
                    # showMessageInfo()
                    return "error", [u"检测到外层资料已添加周期或批次号，但未登记公共程序内的 CAM资料数据记录程序，请先登记！"]
                else:
                    check_type = ["signal", "solder_mask", "silk_screen"]
                    res = check_rule.check_week_picihao_banci_diff_mysql_record({"warning_text": u"检测到外层资料已添加周期或批次号，但未登记公共程序内的 CAM资料数据记录程序，请先登记！",},
                                                                                *check_type)                        
                    return res
        
        return "success", None    
        
    def start_run(self):
        """开始送审"""
        changes = self.get_modify_layers_info()
        if changes and make_type == "cam_maker":          
            showMessageInfo(u"制作完成送审会自动锁定层别，发现资料未保存，请先保存再送审！")
            exit(1)
            
        res = self.get_item_value()
        if not res:
            return
        
        if self.unlock_panel.isChecked():
            self.dic_item_value["unlock_panelization_status"] = "yes"
        else:
            self.dic_item_value["unlock_panelization_status"] = "no"
        
        if "send_unlock_type" in sys.argv[1:]:            
            self.send_unlock_layer_process()            
            return
        
        for key, value in self.dic_editor.iteritems():
            if isinstance(self.dic_editor[key], QtGui.QRadioButton):
                if self.dic_editor[key].isChecked():
                    break
        else:
            showMessageInfo(u"未选择要送审或审核的项目，请检查！")
            return
        
        ls_layers = []
        for index in range(self.select_layer_listbox.count()):
            item = self.select_layer_listbox.item(index)
            text = str(item.text().split("-->")[0])
            if item.checkState() == 2:
                ls_layers.append(text)          
        
        if self.sender().text() == QtCore.QString(u"清除状态"):
            arraylist = []
            for key, value in self.dic_item_value.iteritems():
                if value in [u"送审中", u"已退审"]:
                    arraylist.append("{0}-->{1}".format(key, value))
                    self.dic_item_value[key] = ""
                    
            if not self.select_layer_listbox.isHidden():
                if not ls_layers:
                    showMessageInfo(u"未勾选要清除状态的临时层，请检查！！！")
                    return
                else:
                    if self.dic_item_value.get("linshi_layer_lock_info", None):                        
                        for key, value in self.dic_item_value["linshi_layer_lock_info"].iteritems():
                            if key in ls_layers:
                                self.dic_item_value["linshi_layer_lock_info"][key] = ""
                    
            if arraylist:
                res = showQuestionMessageInfo(u"确认要清除以下制作状态：",  *arraylist)
                if res:
                    with open(status_file, 'w') as file_obj:
                        json.dump(self.dic_item_value, file_obj)
                    
                    sql = u"update hdi_engineering.job_lock_data  set job_make_status=%s where job_name = '{0}'".format(job.name)
                    conn.SQL_EXECUTE(dbc_m, sql, (json.dumps(self.dic_item_value), ))
                    
                    showMessageInfo(u"清除成功！")
                    exit(0)
                else:
                    return
            else:
                showMessageInfo(u"未发现要清除的送审中或退审的状态，请检查！")
                
            exit(0)     

        # step_list, inner_layers, outer_layers, drill_layers,board_layers = self.get_job_matrix()      
        # m_info = matrixInfo
        # step_list = m_info['gCOLstep_name']
        # time_form = time.strftime('%y%m', time.localtime(time.time()))
        #for row in m_info['gROWrow']:
            #num = m_info['gROWrow'].index(row)
            #if "-ls{0}".format(time_form) in m_info['gROWname'][num]:
                #ls_layers.append(m_info['gROWname'][num])
                
        lock_type = ""
        auto_check_type = ""
        if make_type == "cam_maker":
            for key1, key2,key3 in [(u"(芯板)内层完成送审", u"(芯板)内层送审状态", u"(芯板)内层审核状态"),
                                    (u"内层完成送审", u"内层送审状态", u"内层审核状态"),
                                    (u"外层完成送审",u"外层送审状态",u"外层审核状态"),
                                    (u"全套完成送审",u"全套送审状态",u"全套审核状态"),
                                    (u"临时层完成送审",u"临时层送审状态",u"临时层审核状态")] :
                if self.dic_item_value[key1]:
                    self.dic_item_value[key2] = u"送审中"
                    self.dic_item_value[key3] = u"送审中"
                    
                    self.dic_item_value[key1+u"时间"] = self.get_current_format_time()
                    if u"内层" in key3:
                        lock_type = "lock_inner"
                        auto_check_type = "lock_inner"
                        if u"(芯板)" in key3:
                            lock_type = "lock_core_inner"
                            auto_check_type = "lock_coreinner"
                            
                            res = self.get_process_is_running(2222, jobID)
                            if not res:
                                showMessageInfo(u"11.4 全自动(core)内层检测程序未运行，或运行结果异常，请运行后再审核完成！！！")
                                exit(1)
                        else:
                            res = self.get_process_is_running(1648, jobID)
                            if not res:
                                showMessageInfo(u"11.5 全自动内层检测程序未运行，或运行结果异常，请运行后再审核完成！！！")
                                exit(1)                            
                                
                    elif u"外层" in key3 or u"全套" in key3:
                        lock_type = "lock_outer"
                        auto_check_type = "lock_outer"
                        if u"全套" in key3:
                            auto_check_type = "lock_inner_outer"
                            
                        res = self.get_process_is_running(1647, jobID)
                        if not res:
                            showMessageInfo(u"11.6 全自动外层检测程序未运行，或运行结果异常，请运行后再审核完成！！！")
                            exit(1)
                            
                        res = self.get_process_is_running(1810, jobID)
                        if not res:
                            showMessageInfo(u"8.14 检测铜面smd bga补偿及开窗是否一致 未正常运行，请先运行检测程序！")
                            exit(1)
                            
                        res = self.check_record_week_picihao_info()
                        if res[0] != "success":
                            showMessageInfo(*res[1])
                            exit(1)                        
                            
                        if jobname.split("-")[0][-1] == "1" and jobname.split("-")[0][-2] in list("abcdefghijklmnopqrstuvwxyz"):
                            res = self.get_process_is_running(1910, jobID)
                            if not res:                            
                                showMessageInfo(u"11.8 客户型号检测确认 未正常运行，请先运行程序！")
                                exit(1)
                            
                    elif u"临时层" in key3:
                        lock_type = "lock_linshi"
                        if not ls_layers:
                            showMessageInfo(u"未勾选要送审的临时层，请检查！！！")
                            return
                        dic_linshi_info = {}
                        for lay in ls_layers:
                            dic_linshi_info[lay] = u"送审中"
                        
                        if self.dic_item_value.get("linshi_layer_lock_info", None):                            
                            self.dic_item_value["linshi_layer_lock_info"].update(dic_linshi_info)
                        else:
                            self.dic_item_value["linshi_layer_lock_info"] = dic_linshi_info
                            
                        # if "-lyh" in job.name: 
                        res = self.get_process_is_running(2186, jobID) or \
                            self.get_process_is_running(2186, jobID, condition="status='Error'")
                        if not res:
                            showMessageInfo(u"临时层比对程序未运行，或运行结果异常，请处理正常后，才能送审！！！")
                            exit(1)
                        
                        self.hide()
                        pre_status = subprocess.call(["perl", "/incam/server/site_data/hooks/line_hooks/export_job.pre", job.name])
                        if pre_status != 0:
                            exit(1)
                        self.show()                        
                        
        else:
            if self.sender().text() == QtCore.QString(u"审核完成"):
                check_type_text = u"审核完成"
            else:
                check_type_text = u"已退审"
                    
            for key1, key2,key3 in [(u"(芯板)内层审核", u"(芯板)内层审核状态", u"(芯板)内层送审状态"),
                                    (u"内层审核", u"内层审核状态", u"内层送审状态"),
                                    (u"外层审核",u"外层审核状态",u"外层送审状态"),
                                    (u"全套审核",u"全套审核状态",u"全套送审状态"),
                                    (u"临时层审核",u"临时层审核状态",u"临时层送审状态")] :
                if self.dic_item_value[key1]:
                    self.dic_item_value[key2] = check_type_text
                    self.dic_item_value[key3] = check_type_text
                    
                    if check_type_text == u"审核完成":
                        
                        if u"外层" in key3 or u"全套" in key3:
                            res = self.check_week_director(job.name)
                            if res:
                                return
                        
                        self.dic_item_value[key1+u"时间"] = self.get_current_format_time()
                        if u"内层" in key3:
                            lock_type = "lock_inner"
                            auto_check_type = "lock_inner"                           
                            if u"(芯板)" in key3:
                                lock_type = "lock_core_inner"
                                auto_check_type = "lock_coreinner"
                                
                                res = self.get_process_is_running(2220, jobID)
                                if not res:
                                    showMessageInfo(u"2.6.3 全自动(core)内层检测程序未运行，或运行结果异常，请运行后再审核完成！！！")
                                    exit(1)                                 
                            else:
                                res = self.get_process_is_running(1675, jobID)
                                if not res:
                                    showMessageInfo(u"2.6.2 全自动内层检测程序未运行，或运行结果异常，请运行后再审核完成！！！")
                                    exit(1)
                                    
                        elif u"外层" in key3 or u"全套" in key3:
                            lock_type = "lock_outer"
                            auto_check_type = "lock_outer"
                            res = self.get_process_is_running(1677, jobID)
                            if not res:
                                showMessageInfo(u"3.5.2 全自动外层检测程序未运行，或运行结果异常，请运行后再审核完成！！！")
                                exit(1)                             
                            if u"全套" in key3:
                                res = self.get_process_is_running(1675, jobID)
                                if not res:
                                    showMessageInfo(u"2.6.2 全自动内层检测程序未运行，或运行结果异常，请运行后再审核完成！！！")
                                    exit(1)                                 
                                auto_check_type = "lock_inner_outer"
                                
                            res = self.get_process_is_running(2100, jobID)
                            if not res:
                                showMessageInfo(u" CAM资料数据记录程序(审核专用)程序未运行，或运行结果异常，请运行后再审核完成！！！")
                                exit(1)                                 
                            
                        elif u"临时层" in key3:
                            lock_type = "lock_linshi"
                            if not ls_layers:
                                showMessageInfo(u"未勾选要审核完成的临时层，请检查！！！")
                                return                            
                            dic_linshi_info = {}
                            for lay in ls_layers:
                                dic_linshi_info[lay] = u"审核完成"
                            
                            if self.dic_item_value.get("linshi_layer_lock_info", None):                            
                                self.dic_item_value["linshi_layer_lock_info"].update(dic_linshi_info)
                            else:
                                self.dic_item_value["linshi_layer_lock_info"] = dic_linshi_info                            
                    else:
                        if u"临时层" in key3:
                            if not ls_layers:
                                showMessageInfo(u"未勾选要退审的临时层，请检查！！！")
                                return                            
                            dic_linshi_info = {}
                            for lay in ls_layers:
                                dic_linshi_info[lay] = u"已退审"
                            
                            if self.dic_item_value.get("linshi_layer_lock_info", None):                            
                                self.dic_item_value["linshi_layer_lock_info"].update(dic_linshi_info)
                            else:
                                self.dic_item_value["linshi_layer_lock_info"] = dic_linshi_info
                                
                        self.dic_item_value[key1+u"退审时间"] = self.get_current_format_time()
                        # 先改成仅提示
                        showMessageInfo(u"退审需解锁相应step的层别给到制作修改，请检查是否已经解锁了相应层别！！！")                        
                                
                        #if u"内层" in key3:
                            #unlock_layers = inner_layers + drill_layers
                        #elif u"外层" in key3 or u"全套" in key3:
                            #unlock_layers = outer_layers+inner_layers + drill_layers+board_layers
                        #elif u"临时层" in key3:
                            #unlock_layers = ls_layers
                            
                        #self.pre_lock = self.getJOB_LockInfo(dataType='locked_info')
                        #find_not_lock_layers = []
                        #for worklayer in unlock_layers:            
                            #for stepname in matrixInfo["gCOLstep_name"]:
                                #lock = False
                                #for lock_step in self.pre_lock:
                                    #if lock_step == stepname:
                                        #if worklayer in self.pre_lock[lock_step]:    
                                            #lock = True
                                            
                                #if not lock:
                                    #find_not_lock_layers.append(worklayer)
                                    
                        #if not find_not_lock_layers:
                            #showMessageInfo(u"退审需解锁相应step的层别给到制作修改，请检查是否已经解锁了相应层别！！！")
        
        if auto_check_type:
            res = self.check_tgz_output_warning_log(check_inner_outer=auto_check_type)
            if res and job.name.upper() not in ["111", "HE0516GH011C2"]:
                if u"禁止输出" in res[0] :
                    showMessageInfo(u"检测到必运行项或必处理项目检测异常，请运行或处理后再送审！！！！",
                                    res[0],
                                    scoll_bar="yes", 
                                    scoll_widht_height=[1200, 800])
                    #os.system("python /incam/server/site_data/scripts/sh_script/sh_hdi_auto_check_list/sh_hdi_check_ui_new.py check_all_error_item {0}".format(
                        #auto_check_type.split("_")[-1] if auto_check_type <> "lock_inner_outer" else "all"
                    #))
                    #return
                    exit(0)
                    
                result = send_message_to_director(res[1], job.name, res[0])                        
                if not result:
                    exit(0)
                else:
                    sql = u"""update pdm_job_check_log_list set check_process = '检测异常(审核放行)'
                    where  job_id = '{0}'
                    and check_process = '检测异常'
                    and check_status = 'normal'"""
                    ikm_fun.PG.SQL_EXECUTE(ikm_fun.dbc_p, sql.format(jobID, user))
            
            pic_path = os.path.join(os.path.dirname(sys.argv[0]) , "check_detail.png")
            show_message_picture_ui(u"提示", u"确定后将重新执行图片内的检测程序,<br>审核人会关闭料号重新打开来检测！！", pic_path)
            if make_type == "cam_director":
                job.close(0)
                job.open(0)            
            pre_status = subprocess.call(["perl", "/incam/server/site_data/hooks/line_hooks/export_job.pre", job.name])
            if pre_status != 0:
                exit(1)                  
            os.system("python /incam/server/site_data/scripts/sh_script/sh_hdi_auto_check_list/sh_hdi_check_ui_new.py {0} inner".format(
                auto_check_type+"_recheck_item"
            ))
            
            check_list = []
            if "inner" in auto_check_type:
                check_list = ["check_pth_hole_ring", "job_foolproof_detection"]
            if "outer" in auto_check_type:
                check_list = ["check_add_dynamics_jobname", "check_pth_hole_ring"]
                if "inner" in auto_check_type:
                    check_list.append("job_foolproof_detection")
            
            res = self.check_tgz_output_warning_log(check_description_list=check_list,
                                                    check_inner_outer=auto_check_type)
            if res and job.name.upper() not in ["111", "HE0516GH011C2"]:
                if u"禁止输出" in res[0] :
                    showMessageInfo(u"检测到必运行项或必处理项目检测异常，请运行或处理后再送审！！！！",
                                    res[0],
                                    scoll_bar="yes", 
                                    scoll_widht_height=[1200, 800])
                    exit(0)
                    
                result = send_message_to_director(res[1], job.name, res[0])                        
                if not result:
                    exit(0)
                else:
                    sql = u"""update pdm_job_check_log_list set check_process = '检测异常(审核放行)'
                    where  job_id = '{0}'
                    and check_process = '检测异常'
                    and check_status = 'normal'"""
                    ikm_fun.PG.SQL_EXECUTE(ikm_fun.dbc_p, sql.format(jobID, user))            
        
        # if "-lyh" not in job.name:            
        with open(status_file, 'w') as file_obj:
            json.dump(self.dic_item_value, file_obj)
        
        sql = u"update hdi_engineering.job_lock_data  set job_make_status=%s where job_name = '{0}'".format(job.name)
        conn.SQL_EXECUTE(dbc_m, sql, (json.dumps(self.dic_item_value), ))
        # showMessageInfo(lock_type)
        if lock_type:
            os.system("python /incam/server/site_data/scripts/hdi_scr/Tools/job_lock/open_job_lock.py {0} {1}".format(job.name, lock_type))
                
        if make_type == "cam_maker":
            showMessageInfo(u"已送审，请通知审核人审核！")
        else:
            showMessageInfo(u"{0}，请通知制作人！".format(check_type_text))
            
        exit(0)
        
    def check_week_director(self, jobname):
        sql = "select job_detail_info_for_output from hdi_engineering.incam_job_layer_info\
        where job_name = '{0}' and job_detail_info_for_output is not null \
        and job_detail_info_for_output <> ''"
        data_info = conn.SELECT_DIC(dbc_m, sql.format(jobname.split("-")[0]))
        if data_info:
            try:
                job_detail_info_for_output = json.loads(data_info[0]["job_detail_info_for_output"], encoding='utf8')
            except:
                job_detail_info_for_output = {}
            
            check_status = "success"
            not_director_info = []
            for key, value in job_detail_info_for_output.iteritems():
                if key == "week_table":
                    for info in value:
                        if info[-1] != u"审核OK":
                            check_status = "error"
                            if info[1] not in not_director_info:                                    
                                not_director_info.append(info[1])
                
            if check_status == "error":
                showMessageInfo(u"检测到资料 CAM资料数据记录程序 有周期数据未审核【{0}】，请到 CAM资料数据记录程序 审核！".format(" ".join(not_director_info)))
                return 1
        
        return 0
        
    def send_unlock_layer_process(self):
        """发送资料解锁送审流程"""
        unlock_layers = []
        for index in range(self.select_layer_listbox.count()):
            item = self.select_layer_listbox.item(index)
            text = str(item.text())
            if item.checkState() == 2:
                unlock_layers.append(text)
                
        unlock_steps = []
        for index in range(self.select_step_listbox.count()):
            item = self.select_step_listbox.item(index)
            text = str(item.text())
            if item.checkState() == 2:
                unlock_steps.append(text)        
        
        if not unlock_steps and not self.unlock_panel.isChecked():
            showMessageInfo(u"未选中要解锁的step，请勾选！")
            return
        
        if not unlock_layers and not self.unlock_panel.isChecked():
            showMessageInfo(u"未选中要解锁的layer，请勾选！")
            return
        # if self.sender().text() == QtCore.QString(u"一键上锁"):
        text = unicode(self.sender().text(
            ).toUtf8(), 'utf8', 'ignore').encode('cp936').decode("cp936")        
        logs = [u"确定要{0}以下step中的层！".format(text), u"steps:{0}".format(unlock_steps), 
                u"layers:{0}".format(unlock_layers)]
        if unlock_steps and unlock_layers:            
            res = showQuestionMessageInfo(*logs)
            if not res:
                return
        else:
            logs = [u"确定要{0} panel 拼版".format(text)]
            res = showQuestionMessageInfo(*logs)
            if not res:
                return            
        
        matrixInfo = job.matrix.getInfo()
        if make_type == "cam_maker":
            unlock_info = {"step": unlock_steps,"layer": unlock_layers,"lock_type": "unlock",
                           "unlock_panelization_status": [self.dic_item_value["unlock_panelization_status"]],}
            self.job_make_info["unlock_info"] = unlock_info
            
            self.job_make_info["unlock_normal_layer_status"] = u"状态：解锁送审中"
            self.unlock_normal_layer_status.setText(u"状态：解锁送审中")
            
            time_form = time.strftime('%y%m%d.%H%M', time.localtime(time.time()))
            lock_info = self.getJOB_LockInfo()
            lock_layers = []
            for layer in unlock_layers:
                lock_layers.append(layer+"-bf{0}".format(time_form))
            
            if self.dic_item_value["unlock_panelization_status"] == "yes":
                # lock_info["unlock_panelization_status"] = ["yes"]
                get_sr_area_flatten("unlock_panel_fill{0}".format(time_form))
                lock_layers.append("unlock_panel_fill{0}".format(time_form))
            
            for stepname in matrixInfo["gCOLstep_name"]:
                if lock_info.has_key(stepname):
                    lock_info[stepname] = list(set(lock_layers + lock_info[stepname]))
                else:
                    lock_info[stepname] = lock_layers
                    
                #step = gClasses.Step(job, stepname)
                #step.open()
                #for layer in unlock_layers:
                    #step.copyLayer(job.name, step.name, layer, layer+"-bf{0}".format(time_form))
                
                #step.close()
                
            middle_siglayer = signalLayers[len(signalLayers) / 2]
            for layer in unlock_layers:
                new_layer = layer +"-bf{0}".format(time_form)                        
                matrixInfo = job.matrix.getInfo()
                for i in xrange(len(matrixInfo['gROWcontext'])):
                    if matrixInfo['gROWname'][i] == layer:
                        origRow = matrixInfo["gROWrow"][i]
                        middle_siglayer_index = matrixInfo['gROWname'].index(middle_siglayer)
                        if i < middle_siglayer_index:
                            toRow = origRow
                        else:
                            toRow = origRow + 1                        
                        job.COM("matrix_copy_row,job={0},matrix=matrix,row={1},ins_row={2}".format(job.name,origRow,toRow))
                        new_matrixInfo = job.matrix.getInfo()
                        toRow_name = [ name for name in new_matrixInfo['gROWname'] if name not in matrixInfo['gROWname']]            
                                
                        if len(toRow_name) == 1:
                            toRow_name = toRow_name[0]
                            job.COM("matrix_rename_layer,job={0},matrix=matrix,layer={1},new_name={2}".format(job.name, toRow_name, new_layer))
                            job.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=misc".format(job.name, new_layer))
                            job.COM("matrix_refresh,job={0},matrix=matrix".format(job.name))
                            break                
            
            with open(status_file, 'w') as file_obj:
                json.dump(self.job_make_info, file_obj)
            
            sql = u"update hdi_engineering.job_lock_data  set job_make_status=%s,locked_info=%s where job_name = '{0}'".format(job.name.split("-")[0])
            conn.SQL_EXECUTE(dbc_m, sql, (json.dumps(self.job_make_info), json.dumps(lock_info)))
            
            # lock_info = self.getJOB_LockInfo()
            self.write_file(lock_info)
            job.save()
            showMessageInfo(u"解锁送审成功，请通知审核解锁！")
            
        else:
            if self.sender().text() == QtCore.QString(u"一键上锁"):
                unlock_info = {"step": unlock_steps,"layer": unlock_layers,"lock_type": "lock",
                               "unlock_panelization_status": [self.dic_item_value["unlock_panelization_status"]],}
                self.job_make_info["unlock_info"] = unlock_info
                self.job_make_info["unlock_normal_layer_status"] = u"状态：已上锁"
                self.unlock_normal_layer_status.setText(u"状态：已上锁")
                log = u"上锁成功"
            else:
                unlock_info = {"step": unlock_steps,"layer": unlock_layers,"lock_type": "unlock",
                               "unlock_panelization_status": self.dic_item_value["unlock_panelization_status"],}
                self.job_make_info["unlock_info"] = unlock_info                
                self.job_make_info["unlock_normal_layer_status"] = u"状态：已解锁"
                self.unlock_normal_layer_status.setText(u"状态：已解锁")
                log = u"解锁成功"
            
            with open(status_file, 'w') as file_obj:
                json.dump(self.job_make_info, file_obj)
            
            sql = u"update hdi_engineering.job_lock_data  set job_make_status=%s where job_name = '{0}'".format(job.name.split("-")[0])
            conn.SQL_EXECUTE(dbc_m, sql, (json.dumps(self.job_make_info), ))            
        
            os.system("python /incam/server/site_data/scripts/hdi_scr/Tools/job_lock/open_job_lock.py {0} {1}".format(job.name, "unlock_normal_layer"))

            showMessageInfo(log)
            
        exit(0)
            
    def write_file(self, lock_info):
        """
        用json把参数字典直接写入user文件夹中的job_lock.json
        json_str = json.dumps(self.parm)将字典dump成string的格式
        :return:
        :rtype:
        """
        # 将收集到的数据以json的格式写入user/param
        # stat_file = os.path.join(self.userDir, desfile)
        fd = open(lock_json_file, 'w')
        json.dump(lock_info, fd, ensure_ascii=False, indent=4, separators=(', ', ': '), sort_keys=True)
        fd.close()            
        
    def get_modify_layers_info(self):
        info = job.INFO("-t job -e %s -d CHANGES" % job.name)
        return info
        
    def getJOB_LockInfo(self, dataType='locked_info'):
        """
        从数据库中获取料号的锁记录
        :param dataType: 获取的数据类型（status:locked_info log:locked_log）
        :return:dict
        """
        
        lockData = self.getDATA.getLock_Info(job.name.split("-")[0])

        try:
            return json.loads(lockData[dataType].replace("\r", ""), encoding='utf8')
        except:
            # print u'传入的数据参数异常'
            return {}  

    def get_job_matrix(self):

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
        """
        other_layers = [x.strip() for x in other_layers.split("\n")]
        
        m_info = matrixInfo# GEN.DO_INFO("-t matrix -e %s/matrix" % self.job_name)
        step_list = m_info['gCOLstep_name']
        layer_list = m_info['gROWname']
        for row in m_info['gROWrow']:
            num = m_info['gROWrow'].index(row)
            if m_info['gROWcontext'][num] == 'board' or m_info['gROWname'][num] in other_layers:
                board_layers.append(m_info['gROWname'][num])                
            if m_info['gROWcontext'][num] == 'board' and m_info['gROWlayer_type'][num] == 'drill':                
                drill_layers.append(m_info['gROWname'][num])
            
            #翟鸣通知增加铝片 导气板 树脂塞孔20241213 by lyh
            if m_info['gROWlayer_type'][num] == 'drill':
                if m_info['gROWname'][num] in ['lp', 'sz.lp', 'sz...dq'] or \
                   re.match("^sz.*\.lp$|^sz.*\.\.\.dq$", m_info['gROWname'][num]):
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
    
    def creat_ui(self):
        self.cam_finish_btn = QtGui.QPushButton(u"送审")
        self.director_reback_btn = QtGui.QPushButton(u"退审")
        self.director_finish_btn = QtGui.QPushButton(u"审核完成")
        self.end_btn = QtGui.QPushButton(u"退出")
        self.clear_status_btn = QtGui.QPushButton(u"清除状态")
        
        self.unlock_panel = QtGui.QCheckBox()
        
        self.unlock_normal_layer_status = QtGui.QLabel(u"状态:")
        
        self.cam_finish_btn.clicked.connect(self.start_run)
        self.director_reback_btn.clicked.connect(self.start_run)
        self.director_finish_btn.clicked.connect(self.start_run)
        self.clear_status_btn.clicked.connect(self.start_run)
        self.end_btn.clicked.connect(sys.exit)

        self.dic_editor = {}
        self.dic_label = {}
        arraylist2 = [{u"(芯板)内层审核": "QRadioButton"},{u"(芯板)内层审核状态": "QLabel"},
                      {u"内层审核": "QRadioButton"},{u"内层审核状态": "QLabel"},
                      {u"外层审核": "QRadioButton"},{u"外层审核状态": "QLabel"},
                      {u"全套审核": "QRadioButton"},{u"全套审核状态": "QLabel"},
                      {u"临时层审核": "QRadioButton"},{u"临时层审核状态": "QLabel"},                
                      ]

        arraylist1 = [{u"(芯板)内层完成送审": "QRadioButton"},{u"(芯板)内层送审状态": "QLabel"},
                      {u"内层完成送审": "QRadioButton"},{u"内层送审状态": "QLabel"},
                      {u"外层完成送审": "QRadioButton"},{u"外层送审状态": "QLabel"},
                      {u"全套完成送审": "QRadioButton"},{u"全套送审状态": "QLabel"},
                      {u"临时层完成送审": "QRadioButton"},{u"临时层送审状态": "QLabel"},
                      ]
        
        self.select_step_listbox = QtGui.QListWidget()
        self.select_layer_listbox = QtGui.QListWidget()        
        if "send_unlock_type" in sys.argv[1:]:
            self.groupbox2 = QtGui.QGroupBox()
            self.groupbox2.setTitle(u"选择step&&layer")
            self.groupbox2.setStyleSheet("QGroupBox:title{color:green}")	
            step_layer_layerout = self.create_select_layer_box()
            self.groupbox2.setLayout(step_layer_layerout)
            
            if "cam_director" in sys.argv[1:]:
                exists_cam_send_info = False
                self.select_step_listbox.setEnabled(False)
                self.select_layer_listbox.setEnabled(False)
                for key, value in self.job_make_info.iteritems():
                    if key in ["unlock_normal_layer_status"]:
                        self.unlock_normal_layer_status.setText(value)
                            
                    if key in ["unlock_info"]:
                        if "yes" in value.get("unlock_panelization_status", []):
                            exists_cam_send_info = True
                            self.unlock_panel.setChecked(True)
                                
                        for stepname in value["step"]:
                            for index in range(self.select_step_listbox.count()):
                                item = self.select_step_listbox.item(index)
                                text = str(item.text())
                                exists_cam_send_info = True
                                if text == stepname:
                                    item.setCheckState(2)
                                #else:
                                    #item.setFlags(item.flags() & ~QtCore.Qt.ItemIsSelectable & ~QtCore.Qt.ItemIsUserCheckable)
                                    
                        for layer in value["layer"]:
                            for index in range(self.select_layer_listbox.count()):
                                item = self.select_layer_listbox.item(index)
                                text = str(item.text())
                                exists_cam_send_info = True
                                if text == layer:
                                    item.setCheckState(2)
                                #else:
                                    #item.setFlags(item.flags() & ~QtCore.Qt.ItemIsSelectable & ~QtCore.Qt.ItemIsUserCheckable)               
                
                if not exists_cam_send_info:
                    self.director_reback_btn.setEnabled(False)
                    self.director_finish_btn.setEnabled(False)
                    
        group_box_font = QtGui.QFont()
        group_box_font.setBold(True)
        self.widget1 = self.set_widget(group_box_font,
                                  arraylist1,
                                   u"CAM制作",
                                   "")
        
        self.widget2 = self.set_widget(group_box_font,
                                  arraylist2,
                                   u"CAM审核",
                                   "")                   
        layout2 = QtGui.QGridLayout()
        if "send_unlock_type" in sys.argv[1:]:
            self.cam_finish_btn.setText(u"解锁送审")
            self.director_reback_btn.setText(u"一键解锁")
            self.director_finish_btn.setText(u"一键上锁")
            layout2.addWidget(self.groupbox2 , 3, 0, 1, 5)
            layout2.addWidget(self.unlock_normal_layer_status , 4, 0, 1, 5)
            self.unlock_normal_layer_status.setStyleSheet("""color: red;""")
            self.clear_status_btn.hide()
            
            if "cam_director" in sys.argv[1:]:
                self.out_checkbox.setEnabled(False)
                self.inn_checkbox.setEnabled(False)
                self.silk_checkbox.setEnabled(False)
                self.mask_checkbox.setEnabled(False)
                self.drill_checkbox.setEnabled(False)
                self.board_checkbox.setEnabled(False)
                self.all_checkbox.setEnabled(False)
                self.select_all_steps_checkbox.setEnabled(False)
        else:            
            layout2.addWidget(self.widget1 , 1, 0, 1, 5)
            layout2.addWidget(self.widget2 , 2, 0, 1, 5)            
            layout2.addWidget(self.select_layer_listbox , 1, 6, 5, 4)
            
            time_form = time.strftime('%y%m', time.localtime(time.time()))
            find_linshi_layers = []
            for i, layer in enumerate(matrixInfo["gROWname"]):
                if "-ls{0}".format(time_form) in layer:
                    if self.job_make_info.get("linshi_layer_lock_info", None):
                        if layer in self.job_make_info["linshi_layer_lock_info"]:
                            if self.job_make_info["linshi_layer_lock_info"][layer]:
                                find_linshi_layers.append(u"{0}-->{1}".format(
                                    layer, self.job_make_info["linshi_layer_lock_info"][layer])                                                    
                                                       )
                            else:
                                find_linshi_layers.append(layer)
                        else:
                            find_linshi_layers.append(layer)
                    else:
                        find_linshi_layers.append(layer)
            
            for layer in sorted(find_linshi_layers, key=lambda x: x.split("-ls")[1], reverse=True):
                self.select_layer_listbox.addItem(layer)
                                    
            for index in range(self.select_layer_listbox.count()):
                item = self.select_layer_listbox.item(index)
                item.setCheckState(0)
            
            self.select_layer_listbox.hide()
            
        layout2.addWidget(self.cam_finish_btn,  5, 0, 1, 1)
        layout2.addWidget(self.clear_status_btn,  5, 1, 1, 1)
        layout2.addWidget(self.director_reback_btn,  5, 2, 1, 1)
        layout2.addWidget(self.director_finish_btn,  5, 3, 1, 1)
        layout2.addWidget(self.end_btn,  5, 4, 1, 1)

        return layout2

    def show_linshi_select_layer_box(self):
        if self.sender() == self.dic_editor[u"临时层完成送审"] or \
           self.sender() == self.dic_editor[u"临时层审核"]:
            self.select_layer_listbox.show()
        else:
            self.select_layer_listbox.hide()            
    
    def select_layers(self):
        layers = []
        for name in [u"外层线路", u"内层线路", u"文字层",
                     u"阻焊层", u"钻孔层", u"board层", u"选择所有层"]:
            if self.sender().text() == QtCore.QString(name):                
                if name == u"外层线路":
                    layers = outsignalLayers
                elif name == u"内层线路":
                    layers = innersignalLayers
                elif name == u"文字层":
                    layers = silkscreenLayers
                elif name == u"阻焊层":
                    layers = solderMaskLayers
                elif name == u"钻孔层":
                    for i, layer in enumerate(matrixInfo["gROWname"]):
                        if matrixInfo["gROWcontext"][i] == "board" and matrixInfo["gROWlayer_type"][i] == "drill":
                            layers.append(layer)                  
                elif name == u"board层":
                    for i, layer in enumerate(matrixInfo["gROWname"]):
                        if matrixInfo["gROWcontext"][i] == "board":
                            layers.append(layer)
                elif name == u"选择所有层":
                    layers = matrixInfo["gROWname"]
                            
        if self.sender().isChecked():            
            for index in range(self.select_layer_listbox.count()):
                item = self.select_layer_listbox.item(index)
                text = str(item.text())
                if text in layers:
                    self.select_layer_listbox.setItemSelected(item, True)
                    item.setCheckState(2)
        else:
            for index in range(self.select_layer_listbox.count()):
                item = self.select_layer_listbox.item(index)                
                text = str(item.text())
                if text in layers:
                    self.select_layer_listbox.setItemSelected(item, False)
                    item.setCheckState(0)
    
    def select_steps(self):
        if self.sender().isChecked():            
            for index in range(self.select_step_listbox.count()):
                item = self.select_step_listbox.item(index)
                # text = str(item.text())
                # if text in layers:
                self.select_step_listbox.setItemSelected(item, True)
                item.setCheckState(2)
        else:
            for index in range(self.select_step_listbox.count()):
                item = self.select_step_listbox.item(index)                
                # text = str(item.text())
                # if text in layers:
                self.select_step_listbox.setItemSelected(item, False)
                item.setCheckState(0)        
    
    def create_select_layer_box(self):
        
        self.select_layer_listbox.setSelectionMode(3)
        self.select_layer_listbox.setFixedHeight(500)
        self.select_layer_listbox.clear()
        
        for i, layer in enumerate(matrixInfo["gROWname"]):
            for lock_step in self.lock_info:
                if layer in self.lock_info[lock_step]:               
                    self.select_layer_listbox.addItem(layer)
                    break
                
        for index in range(self.select_layer_listbox.count()):
            item = self.select_layer_listbox.item(index)
            item.setCheckState(0)
        
        for lock_step in self.lock_info:
            if "orig" in lock_step:
                continue
            if "net" in lock_step:
                continue
            if lock_step not in ["lock_panelization_status",
                                 "unlock_panelization_status"]:                
                self.select_step_listbox.addItem(lock_step)
            
        for index in range(self.select_step_listbox.count()):
            item = self.select_step_listbox.item(index)
            item.setCheckState(0)            
                
        label = QtGui.QLabel(u"请按住CTRL键进行多选")
        self.select_all_steps_checkbox = QtGui.QCheckBox(u"选择所有STEP")
        
        self.unlock_panel = QtGui.QCheckBox(u"解锁panel排版")
        self.out_checkbox = QtGui.QCheckBox(u"外层线路")
        self.inn_checkbox = QtGui.QCheckBox(u"内层线路")
        self.silk_checkbox = QtGui.QCheckBox(u"文字层")
        self.mask_checkbox = QtGui.QCheckBox(u"阻焊层")
        self.drill_checkbox = QtGui.QCheckBox(u"钻孔层")
        self.board_checkbox = QtGui.QCheckBox(u"board层")
        self.all_checkbox = QtGui.QCheckBox(u"选择所有层")
        
        #self.insert_layer_btn = QtGui.QPushButton(u"确定")
        #self.insert_layer_btn.clicked.connect(self.insert_layers)
        
        self.out_checkbox.clicked.connect(self.select_layers)
        self.inn_checkbox.clicked.connect(self.select_layers)
        self.silk_checkbox.clicked.connect(self.select_layers)
        self.mask_checkbox.clicked.connect(self.select_layers)
        self.drill_checkbox.clicked.connect(self.select_layers)
        self.board_checkbox.clicked.connect(self.select_layers)
        self.all_checkbox.clicked.connect(self.select_layers)
        self.select_all_steps_checkbox.clicked.connect(self.select_steps)
        
        # self.unlock_panel.hide()
        #self.dic_editor = {}
        #self.dic_label = {}
        
        #arraylist1 = [{u"固定后缀(不可编辑)": "QLineEdit"},
                      #{u"自定义后缀": "QLineEdit"},]
        #if "restore_linshi_layer" in sys.argv[1:]:
            #arraylist1.append({u"筛选后缀": "QComboBox"})
            
        #if "restore_normal_layer" in sys.argv[1:]:
            #arraylist1.append({u"还原模式": "QComboBox"})
            #arraylist1.append({u"筛选后缀": "QComboBox"})

        #group_box_font = QtGui.QFont()
        #group_box_font.setBold(True)    
        #self.widget3 = self.set_widget(group_box_font,
                                       #arraylist1,
                                       #u"基本信息确认",
                                       #"")
        
        gridlayout = QtGui.QGridLayout()
        # gridlayout.addWidget(self.widget3, 0, 0, 1, 1)
        gridlayout.addWidget(self.select_step_listbox, 0, 0, 10, 1)
        gridlayout.addWidget(self.select_layer_listbox, 0, 1, 10, 1)
        gridlayout.addWidget(self.out_checkbox, 3, 2, 1, 1)
        gridlayout.addWidget(self.inn_checkbox, 4, 2, 1, 1)
        gridlayout.addWidget(self.silk_checkbox, 5, 2, 1, 1)
        gridlayout.addWidget(self.mask_checkbox, 6, 2, 1, 1)
        gridlayout.addWidget(self.drill_checkbox, 7, 2, 1, 1)
        gridlayout.addWidget(self.board_checkbox, 8, 2, 1, 1)
        gridlayout.addWidget(self.all_checkbox, 9, 2, 1, 1)
        gridlayout.addWidget(self.select_all_steps_checkbox, 10, 2, 1, 1)
        gridlayout.addWidget(self.unlock_panel, 11, 2, 1, 1)
        # gridlayout.addWidget(label, 20, 0, 1, 1)
        # gridlayout.addWidget(self.insert_layer_btn, 20, 1, 1, 1)

        return gridlayout    

    def get_item_value(self):
        """获取界面参数"""	
        self.dic_item_value = {}
        if os.path.exists(status_file):
            with open(status_file) as file_obj:
                self.dic_item_value = json.load(file_obj)
                
        for key, value in self.dic_editor.iteritems():
            if isinstance(self.dic_editor[key], QtGui.QLineEdit):
                self.dic_item_value[key] = unicode(self.dic_editor[key].text(
                    ).toUtf8(), 'utf8', 'ignore').encode('cp936').decode("cp936")
            elif isinstance(self.dic_editor[key], QtGui.QComboBox):
                self.dic_item_value[key] = unicode(self.dic_editor[key].currentText(
                    ).toUtf8(), 'utf8', 'ignore').encode('cp936').decode("cp936")
            elif isinstance(self.dic_editor[key], QtGui.QRadioButton):
                self.dic_item_value[key] = self.dic_editor[key].isChecked()
            elif isinstance(self.dic_editor[key], QtGui.QLabel):
                self.dic_item_value[key] = unicode(self.dic_editor[key].text(
                    ).toUtf8(), 'utf8', 'ignore').encode('cp936').decode("cp936")                
                
        arraylist = [u"字高(mil)", u"字宽(mil)",
                     u"线宽(mil)"]
        
        if self.dic_item_value.get("unlock_panelization_status", None) == "yes":
            self.unlock_panel.setChecked(True)
        
        for key in arraylist:
            if self.dic_item_value.has_key(key):
                try:
                    self.dic_item_value[key] = float(self.dic_item_value[key])
                except:
                    QtGui.QMessageBox.information(self, u'提示', u'检测到 %s 参数[ %s ]为空或非法数字,请检查~' % (
                        key, self.dic_item_value[key]), 1)
                    # self.show()
                    return 0
        return 1
    
    def setValue(self):
        res = 0
        if os.path.exists(status_file):
            with open(status_file) as file_obj:
                self.dic_make_info = json.load(file_obj)

            for key, value in self.dic_editor.iteritems():
                if self.dic_make_info.get(key):		    
                    if isinstance(self.dic_editor[key], QtGui.QLineEdit):
                        if isinstance(self.dic_make_info[key], float):
                            self.dic_editor[key].setText("%s" % self.dic_make_info[key])
                        else:
                            self.dic_editor[key].setText(self.dic_make_info[key])
                    elif isinstance(self.dic_editor[key], QtGui.QComboBox):
                        pos = self.dic_editor[key].findText(
                            self.dic_make_info[key], QtCore.Qt.MatchExactly)
                        self.dic_editor[key].setCurrentIndex(pos)
                    elif isinstance(self.dic_editor[key], QtGui.QLabel):                        
                        if self.dic_make_info.get(key.replace(u"状态", u"时间"), None) and "-lyh" in job.name:
                            if key.replace(u"状态", u"时间") == key:
                                self.dic_editor[key].setText(self.dic_make_info[key])
                            else:
                                self.dic_editor[key].setText(self.dic_make_info[key]+" "+\
                                                             self.dic_make_info[key.replace(u"状态", u"时间")])
                        else:
                            self.dic_editor[key].setText(self.dic_make_info[key])
                        
        else:
            res = 1
                
        return res
    
    def set_widget(self, font, arraylist, title, checkbox):
        groupbox = QtGui.QGroupBox()
        groupbox.setTitle(title)
        groupbox.setStyleSheet("QGroupBox:title{color:green}")
        groupbox.setFont(font)	
        gridlayout = self.get_layout(arraylist, checkbox)
        groupbox.setLayout(gridlayout)
        return groupbox

    def get_layout(self, arraylist, checkbox):

        gridlayout = QtGui.QGridLayout()
        for i, name in enumerate(arraylist):
            for key, value in name.iteritems():
                self.dic_label[key] = QtGui.QLabel()
                self.dic_label[key].setText(key)
                self.dic_editor[key] = getattr(QtGui, value)()
                col = 2 if i % 2 else 0
                row = -1 if col else 0
                
                gridlayout.addWidget(self.dic_editor[key], i + 1 + row, 1 + col, 1, 1)
                gridlayout.addWidget(self.dic_label[key], i + 1 + row, 2 + col, 1, 1)                
                
                if isinstance(self.dic_editor[key], QtGui.QRadioButton):                    
                    self.dic_editor[key].clicked.connect(self.show_linshi_select_layer_box)
               
                if key in [u"内层审核状态",u"外层审核状态",u"全套审核状态",u"临时层审核状态",
                           u"内层送审状态",u"外层送审状态",u"全套送审状态",u"临时层送审状态",
                           u"(芯板)内层送审状态", u"(芯板)内层审核状态",]:
                    self.dic_editor[key].setStyleSheet("""color: red;""")

        gridlayout.setSpacing(5)
        gridlayout.setContentsMargins(5, 5,5, 5)
        gridlayout.setAlignment(QtCore.Qt.AlignLeft)

        return gridlayout

    def setMainUIstyle(self):  # 设置风格
        file = QtCore.QFile(':/pic/fblue.qss')
        file.open(QtCore.QFile.ReadOnly)
        styleSheet = file.readAll()
        styleSheet = unicode(styleSheet, encoding='gb2312')
        QtGui.qApp.setStyleSheet(styleSheet) 
    
if __name__ == "__main__":
    # app = QtGui.QApplication(sys.argv)
    main_widget = send_finish_status()
    main_widget.show()
    sys.exit(app.exec_())        