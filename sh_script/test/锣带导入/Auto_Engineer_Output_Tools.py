#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = "luthersy"
__date__ = "20231204"
__version__ = "Revision: 1.0.0 "
__credits__ = u"""自动输出程序模块 """

import sys
import os
if sys.platform == "win32":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package_HDI")    
else:
    scriptPath = "%s/scripts" % os.environ.get('SCRIPTS_DIR', '/incam/server/site_data')
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")

if sys.platform == "win32":      
    from autoConvertLaserfiles_auto import laser_convert
    convert_laser_fun = laser_convert()
    
    if "auto_create_barcode_xml_files" in sys.argv[1:]:
        from auto_create_silk_barcode_xml_info import create_xml_info
        auto_barcode_xml_fun = create_xml_info()

import gClasses
import string
import re
import pic
import json
import shutil
import time
import threading
import requests    
from PyQt4 import QtCore, QtGui, Qt
from scriptsRunRecordLog import uploadinglog
from genesisPackages import job, top, matrixInfo, \
     outputgerber274x_incam, innersignalLayers, lay_num, \
     get_sr_limits, compareLayersForOutput, outputgerber274x, \
     get_panelset_sr_step, get_profile_limits, outsignalLayers, \
     solderMaskLayers, get_drill_start_end_layers, tongkongDrillLayer, \
     mai_drill_layers, mai_man_drill_layers, get_sr_area_for_step_include, \
     get_sr_area_flatten, auto_add_features_in_panel_edge_new, rout_layers, \
     get_layer_selected_limits, laser_drill_layers, silkscreenLayers, \
     output_opfx, signalLayers, exportRout, genesisFlip

import socket
localip = socket.gethostbyname_ex(socket.gethostname())

from get_erp_job_info import get_inplan_mrp_info, get_cu_weight, \
     get_plating_type, getJobData, get_led_board, get_inplan_all_flow, \
     get_laser_depth_width_rate, get_job_type

if sys.platform != "win32": 
    from auto_create_icg_test_point_auto import test_point_create
    test_point_program = test_point_create()
    
    from auto_create_width_spacing_measure_coordinate import measure_coordinate
    measure_coordinate_program = measure_coordinate()    

    sys.path.insert(0, "/incam/server/site_data/scripts/lyh")
    from auto_sh_hdi_check_rules import auto_check_rule    
    check_rule = auto_check_rule()
    
    import pexpect

compare_output = compareLayersForOutput()
flip = genesisFlip()

try:    
    from Dingtalk import TopApi
    send_talk = TopApi()
    access_token = send_talk.getToken()
    import random
except Exception as e:
    print(e)
    
if sys.platform == "win32":  
    import psutil
    from pywinauto import Application
    from pywinauto import mouse
    from pywinauto.keyboard import send_keys
    
    import win32gui
    import win32ui
    import win32con
    import win32api
    def screen_capture(filename):
        # 获取当前活动的窗口的句柄
        hwnd = win32gui.GetDesktopWindow()
    
        # 获取窗口的设备上下文（DC）
        hwndDC = win32gui.GetWindowDC(hwnd)
    
        # 创建一个与窗口DC兼容的内存DC
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
    
        # 创建一个与mfcDC兼容的内存DC
        saveDC = mfcDC.CreateCompatibleDC()
    
        # 创建一个位图对象
        saveBitmap = win32ui.CreateBitmap()
    
        # 获取监视器信息，确定截图的大小
        monitorDev = win32api.EnumDisplayMonitors(None, None)
        width = monitorDev[0][2][2]
        height = monitorDev[0][2][3]
    
        # 为saveBitmap分配空间
        saveBitmap.CreateCompatibleBitmap(mfcDC, width, height)
    
        # 将saveBitmap选入saveDC
        saveDC.SelectObject(saveBitmap)
    
        # 执行位块传输，将截图保存到saveBitmap
        saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)
    
        # 保存位图文件
        saveBitmap.SaveBitmapFile(saveDC, filename)
    
        # 释放资源
        saveDC.DeleteDC()
        mfcDC.DeleteDC()
        win32gui.ReleaseDC(hwnd, hwndDC)
        win32gui.DeleteObject(saveBitmap.GetHandle())

try:
    from getFactory import __factory__
    SITE_ID = __factory__
except Exception, e:
    print e
    SITE_ID = "" 
    
array_jobtype_info = get_job_type(os.environ.get('JOB', None))
car_type = [info for info in array_jobtype_info
            if (info["JOB_PRODUCT_LEVEL1_"] and u"汽车" in info["JOB_PRODUCT_LEVEL1_"].decode("utf8"))
            or info["ES_CAR_BOARD_"] == 1]
battery_type = [info for info in array_jobtype_info
            if (info["JOB_PRODUCT_LEVEL1_"] and u"电池" in info["JOB_PRODUCT_LEVEL1_"].decode("utf8"))
            or info["ES_BATTERY_BOARD_"] == 1]        

check_car_type = 0
if os.environ.get('JOB', "").startswith("q") or car_type:
    check_car_type = 1
    
check_battery_type = 0
if battery_type:
    check_battery_type = 1
    
check_nv_type = 0
if os.environ.get('JOB', "")[1:4] in ["a86", "d10"]:
    check_nv_type = 1    
    
import MySQL_DB
conn = MySQL_DB.MySQL()
#dbc_m = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='hdi_engineering', prod=3306,
                           #username='root', passwd='k06931!')
#dbc_p = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='project_status', prod=3306,
                           #username='root', passwd='k06931!')

if sys.platform == "win32":
    tmp_path = "c:/tmp"
    incam_or_genesis = "genesis"
else:
    tmp_path = "/tmp"
    incam_or_genesis = "incam"

class engineer_output_tool(object):
    def __init__(self):
        self.setMainUIstyle()
        script_dir = os.path.dirname(sys.argv[0])
        os.system("python {0}/{1}.py".format(script_dir, "update_users_week_format_config"))
        
    def get_mysql_data(self, condtion="1=1"):
        dbc_m = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='hdi_engineering', prod=3306,
                                   username='root', passwd='k06931!')           
        sql = u"""SELECT * FROM  hdi_electron_tools.hdi_job_tools
        where {0}""".format(condtion)
        data_info = conn.SELECT_DIC(dbc_m, sql)
        dbc_m.close()
        return data_info

    def get_mysql_data_1(self, sql):
        dbc_m = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='hdi_engineering', prod=3306,
                                   username='root', passwd='k06931!')           
        data_info = conn.SELECT_DIC(dbc_m, sql)
        dbc_m.close()
        return data_info
    
    def update_mysql_data(self, params, condition="id = -1"):
        dbc_m = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='hdi_engineering', prod=3306,
                                   username='root', passwd='k06931!')        
        sql = u"""update hdi_electron_tools.hdi_job_tools set {0} where {1}"""
        conn.SQL_EXECUTE(dbc_m, sql.format(",".join(params), condition))
        dbc_m.close()
        
    def delete_mysql_data(self, sql):
        dbc_m = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='hdi_electron_tools', prod=3306,
                                   username='hdi_web', passwd='!QAZ2wsx')
        conn.SQL_EXECUTE(dbc_m, sql)
        dbc_m.close()        
        
    def get_current_format_time(self):
        time_form = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        return time_form
    
    def colseJob(self, jobname):
        top.VOF()			
        STR1 ='close_job,job=%s' %jobname
        top.COM(STR1)        
        #STR2='close_form,job=%s' %jobname
        #STR3='close_flow,job=%s' %jobname
        #top.COM(STR2)
        #top.COM(STR3)
        top.VON()
    
    def __delete__(self):
        if func == "output_scale_rout_file":
            app = Application(backend="win32").connect(title_re=".*Toolkit.*", timeout=10)
            if app.is_process_running():
                app.kill()
        
    def check_get_process_is_run_normal(self, *args):
        """检测genesis是否卡死"""
        while True:
            try:
                output_id, worklayer = args
                genesis_log_lines = []
                if os.environ.get("GENESIS_PID", None) is not None:                    
                    prefix_genesis = "log-genesis186"
                    prefix_incam = "log-incampro186"
                    if sys.platform == "win32":
                        tmp_path = "c:/tmp"                        
                    else:
                        tmp_path = "/tmp"                        
        
                    pid = os.environ["GENESIS_PID"]
                    for name in os.listdir(tmp_path):
                        if (prefix_genesis in name or
                                prefix_incam in name) and \
                           name.endswith("." + pid):
        
                            for line in file(tmp_path + "/" + name).readlines()[-1000:]:
                                if "gen__mem_free/ error at file" in line:                            
                                    genesis_log_lines.append(line)
                                    
                if len(genesis_log_lines) > 100:
                    self.write_finish_log(output_id)
                    start_time = self.get_current_format_time()
                    warning_log = u"genesis输出{0}内存不足，转incam输出 {1}<br>".format(worklayer, start_time)
                    self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常"),
                                            u"Status = '{0}'".format(u"输出中"),
                                            u"AlarmLog = concat(AlarmLog,'{0}')".format(warning_log)],
                                           condition="id={0}".format(output_id))
                    pid = os.environ["GENESIS_PID"]
                    if sys.platform == "win32":                        
                        kill_cmd = "taskkill /f /pid %s" % pid.strip()
                    else:
                        kill_cmd = "kill %s" % pid.strip()
                    print kill_cmd
                    with open("/tmp/{0}_{1}_mem_free.log".format(job.name, worklayer), "w") as f:
                        f.write("yes")
                    os.system(kill_cmd)
                    break
                
                calc_time = 2
                if "incam" in sys.argv[1:]:
                    calc_time = 4
                if "test_point" == worklayer:
                    calc_time = 1
                    
                res = self.kill_process_for_genesis("{0}/calc_time_{1}_{2}.log".format(tmp_path, output_id, worklayer),
                                                    os.environ["GENESIS_PID"],
                                                    output_id, worklayer, calc_time)
                if res:
                    break
                
                if self.kill_thread:
                    break
                    
                #with open("c:/tmp/check.log", "w") as f:
                    #f.write(str(os.environ.get("GENESIS_PID", None)) + str(time.time()))
                time.sleep(10)
            except Exception as e:
                #with open("c:/tmp/check.log", "w") as f:
                    #f.write(str(e) + str(time.time()))
                    
                time.sleep(10)

    def kill_process_for_genesis(self, filepath, pid, output_id, worklayer, time_calc=1):
        """杀死超过60分钟未有变化的genesis所有进程 20231213 by lyh"""
        #for name in os.listdir("c:/tmp"):
            #if filename == name:
                #filepath = "c:/tmp/" + name
        if os.path.exists(filepath) and time.time() - os.path.getmtime(filepath) > 60 * 60 * time_calc:
            
            self.write_finish_log(output_id)
            start_time = self.get_current_format_time()
            warning_log = u"genesis输出{0}卡死，转incam输出 {1}<br>".format(worklayer, start_time)
            if "incam" in sys.argv[1:]:
                warning_log = u"incampro输出{0}卡死，请手动输出 {1}<br>".format(worklayer, start_time)
                
            self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常"),
                                    u"Status = '{0}'".format(u"输出中"),
                                    u"AlarmLog = concat(AlarmLog,'{0}')".format(warning_log)],
                                   condition="id={0}".format(output_id))
            if sys.platform == "win32":                        
                kill_cmd = "taskkill /f /pid %s" % pid.strip()
            else:
                kill_cmd = "kill %s" % pid.strip()
            print kill_cmd
            with open("/tmp/{0}_{1}_mem_free.log".format(job.name, worklayer), "w") as f:
                f.write("yes")            
            os.system(kill_cmd)
            os.unlink(filepath)
            return 1
        
        return 0
    
    def write_calc_time_log(self, output_id):
        # if sys.platform == "win32":
        with open("{0}/calc_time_{1}.log".format(tmp_path, output_id), "w") as f:
            f.write(str(output_id))
            
    def create_job_open_for_hold_license(self, *args):
        """自动登录云incampro 打开型号 占住HDI的license"""
        jobname = args[0]
        self.colseJob(jobname)
        job.open(0)
        job.PAUSE("check")
        exit(0)
        
    def output_odb_tgz_for_genesis(self, *args):
        """输出tgz给genesis调用输出gerber资料用"""
        jobname = args[0]        
        os.system("rm -rf /tmp/tgz/{0}/{0}.tgz".format(jobname))        
        try:
            os.makedirs("/tmp/tgz/{0}".format(jobname))
        except Exception as e:
            print(e)
        top.COM("""export_job,job={0},path=/tmp/tgz/{0},mode=tar_gzip,submode=partial,
        del_elements=forms\;wheels\;checklists\;unused_symbols\;input\;output\;user\;extension\;components,
        steps_mode=include,steps=,lyrs_mode=include,lyrs=,format=genesis,overwrite=yes""".format(jobname))
                
    def auto_convert_laser_files(self, *args):
        """镭射自动转档"""
        
        jobname = args[0]
        self.colseJob(jobname)
        
        output_id = args[1]
        filename = args[2]
        stepname = "panel"
        job.open(0)
        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=mm")
        
        # index = jobname[1:4]
        # dir_path = ur"\\192.168.2.174\GCfiles\Program\工程辅助资料\{0}系列\{1}".format(index, jobname)
        laser_drill_info = get_laser_depth_width_rate(jobname)
        
        dest_net_path = ""
        output_layers = []
        data_info = self.get_mysql_data(condtion="id = {0}".format(output_id))
        dataname = ""
        for info in sorted(data_info, key=lambda x: x["workLevel"] * -1):                    
            dest_net_path = info["OutputPath"] # os.path.join(info["OutputPath"], jobname)
            if u"自动镭射转档测试" in dest_net_path and info["dataName"] == u"镭射转档资料":
                dest_net_path = ur"\\192.168.2.174\GCfiles\Program\Laser\5代机6H代机钻带(有效65X65)\{0}系列\{1}".format(jobname[1:4], jobname)
                
            output_layers = [x for x in info["OutLayer"].split(";") if x.strip()]
            
            dataname = info["dataName"]

        try:
            os.makedirs(dest_net_path)
        except Exception, e:
            print(e)
    
        if dataname in [u"UV机_只加工skip via孔_UV" ,
                        u"UV机_只加工清孔底_CL",
                        u"UV机_UV开铜_CU"]:
            mrp_name = ""
            for dic_info in laser_drill_info:
                if dic_info["PROGRAM_NAME"] and dic_info["PROGRAM_NAME"].lower() in filename :
                    mrp_name = dic_info["MRP_NAME"]
                    break
            
            if mrp_name:
                # print("-------------------->", mrp_name)
                process_data_info = get_inplan_all_flow(jobname.upper(), select_dic=True)
                log = ""
                #方松通知 这两种 暂时不检测 20240627 by lyh
                #if dataname in [u"UV机_只加工skip via孔_UV" ,u"UV机_只加工清孔底_CL",]:
                    #log = u"{0}未检测到{1} 激光钻流程中存在 UV镭射机 备注字样，请确认申请是否正常！"
                if dataname in [u"UV机_UV开铜_CU" ]:
                    log = u"{0}未检测到{1} 激光钻流程中存在 UV开窗 或 UV开铜窗 备注字样，请确认申请是否正常！"                      
                for dic_process_info in process_data_info:
                    if dic_process_info["WORK_CENTER_CODE"] and \
                       u"激光钻" in dic_process_info["WORK_CENTER_CODE"].decode("utf8") and \
                       mrp_name.upper() == dic_process_info["MRP_NAME"]:
                        if dic_process_info["NOTE_STRING"]:
                            if dataname in [u"UV机_只加工skip via孔_UV" ,u"UV机_只加工清孔底_CL",] and \
                               u"UV" in dic_process_info["NOTE_STRING"].decode("utf8").upper():
                                log = ""  
                            if dataname in [u"UV机_UV开铜_CU" ] and \
                               (u"UV开窗" in dic_process_info["NOTE_STRING"].decode("utf8").upper() or \
                               u"UV开铜窗" in dic_process_info["NOTE_STRING"].decode("utf8").upper()):
                                log = ""                                                                                                    
                            
                if log:
                    warnging_log = log.format(filename, mrp_name)
                    self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                            u"Status = '{0}'".format(u"输出异常"),
                                            u"AlarmLog = concat(AlarmLog,'{0}')".format("<br>"+warnging_log)],
                                           condition="id={0}".format(output_id))                                
                    self.write_finish_log(str(output_id) +"_check_error")
                    return
        #if os.path.exists(dir_path):
            #for name in os.listdir(dir_path):
                #if name.endswith(".write"):
                    #filepath = "d:/disk/laser/{0}".format(name)
                    #if os.path.exists(filepath):
                        #continue
                    
        log, convert_files = convert_laser_fun.start_convert(self, filename, output_id, dataname)
        if log:
            # step.PAUSE("ddd")
            log.append("<br>")
            self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                    u"Status = '{0}'".format(u"输出异常"),
                                    u"AlarmLog = concat(AlarmLog,'{0}')".format("<br>".join(log))],
                                   condition="id={0}".format(output_id))
            
            self.write_finish_log(str(output_id) +"_check_error")
            
            for filepath in convert_files:
                os.unlink(filepath)            
            
        else:                
            # print(convert_files)
            for filepath in convert_files:
                new_filename = os.path.basename(filepath)
                if dataname == u"UV机_只加工skip via孔_UV":
                    new_filename = "UV-" + new_filename
                if dataname == u"UV机_只加工清孔底_CL":
                    new_filename = "CL-" + new_filename                    
                if dataname == u"UV机_UV开铜_CU":
                    new_filename = "CU-" + new_filename
                if dataname == u"备靶_选择备靶管位_LSBT":
                    new_filename = jobname+"-drb" + "/" + "LSBT-" + new_filename
                    try:
                        os.makedirs(dest_net_path+"/"+jobname+"-drb")
                    except:
                        pass
                    
                shutil.copy2(filepath, os.path.join(dest_net_path, new_filename))
                
                os.unlink(filepath)
            
            if u"自动镭射转档测试" not in dest_net_path:
                mrp_name = ""
                for dic_info in laser_drill_info:
                    if dic_info["PROGRAM_NAME"] and dic_info["PROGRAM_NAME"].lower() in filename :
                        mrp_name = dic_info["MRP_NAME"]
                        break
                
                if mrp_name:                
                    url = "http://192.168.2.122/HdiZs-Base/api/zsInPlanUpdate/Update_JgzDrill?Job={0}"
                    with open("c:/tmp/sql.log", "a") as f:
                        f.write(url.format(mrp_name) + "\n")
                    requests.get(url=url.format(mrp_name))
                                
        self.write_finish_log(output_id)
        
        # self.write_finish_log(output_id+"_"+filename)
        
    def auto_output_wangping(self, *args):
        """自动输出网屏tgz资料"""
        global solderMaskLayers
        jobname = args[0]
        self.colseJob(jobname)
        
        output_id = args[1]
        stepname = "panel"
        job.open(1)
        
        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=mm")
        
        get_sr_area_flatten("fill", get_sr_step=True)        
        f_xmin, f_ymin, f_xmax, f_ymax = get_profile_limits(step)        
        data_info = self.get_mysql_data(condtion="id = {0}".format(output_id))
        for info in sorted(data_info, key=lambda x: x["workLevel"] * -1):            
            """Circle_Year,Circle_Month,Circle_Day,Circle_YearWeekNo,\
            Circle_WeekDay,Circle_WorkShift,Circle_LotsNum"""
            ID = info["id"]
            tmp_dir = "{0}/{1}/{2}/{3}".format(tmp_path, job.name, "jinxin", ID)
            year = info["Circle_Year"]
            month = info["Circle_Month"]
            day = info["Circle_Day"]
            week = info["Circle_YearWeekNo"]
            xingqi = info["Circle_WeekDay"]
            banci = info["Circle_WorkShift"]
            picihao = info["Circle_LotsNum"]
            layers = info["OutLayer"]
            if picihao is None or picihao == "":
                picihao = "None"
                
            #还原临时层
            os.system('python /incam/server/site_data/scripts/sh_script/zl/check/TempLayerCheck.py {0} restore_normal'.format(job.name))
            
            for worklayer in layers.split(";"):            
                if not step.isLayer(worklayer):
                    log = u"输出层{0} 不存在，请检查tgz资料是否正常！<br>".format(worklayer)
                    self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                           condition="id={0}".format(ID))                        
                    self.write_finish_log(output_id+"_check_error")                    
                    return
                else:
                    step.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=board".format(job.name, worklayer))
            
            for worklayer in job.matrix.getInfo()["gROWname"]:
                if "-ls" in worklayer or "-bf" in worklayer:
                    step.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=misc".format(job.name, worklayer))            
            
            solderMaskLayers = layers.split(";")
            #检测周期数量
            check_types = ["solder_mask"]
            res = check_rule.check_record_week_picihao_to_mysql(*check_types)
            #if jobname == "c18304oi868c1":
                #job.PAUSE("ddd1")
                
            if res[0] != "success":
                self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                        u"Status = '{0}'".format(u"输出异常"),
                                        u"AlarmLog = concat(AlarmLog,'{0}')".format("<br>".join(res[1]))],
                                       condition="id={0}".format(output_id))                
                self.write_finish_log(str(output_id) +"_check_error")
                return                      
            
            # 改周期批次
            print("------------>", year, month, day, week, banci, xingqi, picihao, layers, ID)
            os.system(r'python /incam/server/site_data/scripts/lyh/auto_modify_week_picihao.py auto_output {0} {1} {2} {3} {4} {5} {6} "{7}" {8}'.format(
                year, month, day, week, banci, xingqi, picihao, layers, ID
            ))
            # job.PAUSE("ddd1")
            error_file = os.path.join("/tmp", "success_{0}_check_error.log".format(ID))
            if os.path.exists(error_file):
                return
            
            #输出tgz
            # 改动态层跟时间为静态
            change_system_time_log = "/tmp/change_system_time.log"
            num = 1
            while os.path.exists(change_system_time_log):
                time.sleep(1)
                num += 1
                if num > 1800:
                    break
                
            with open(change_system_time_log, "w") as f:
                f.write(jobname+"\n")            
            self.modify_dynamic_layer_text(layers.split(";"))
            os.system("rm -rf {0}".format(change_system_time_log))
            
            job.save()
            
            start_time = self.get_current_format_time()
            log = u"开始输出网屏tgz {0} <br>".format(start_time)
            self.update_mysql_data([u"Status = '{0}'".format(u"输出中"),
                                    u"OutputStatus = '{0}'".format(u"输出中"),
                                    u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                    condition="id={0}".format(ID))             
            os.system(r'python /incam/server/site_data/scripts/hdi_scr/Output/output_wp_tgz/output_wp_tgz_auto.py {0} {1} {2} "{3}"'.format(
                "wangping", jobname, ID, layers
            ))
            # job.PAUSE("ddd2")
            error_file = os.path.join("/tmp", "success_{0}_check_error.log".format(ID))
            if os.path.exists(error_file):
                return
            
            # 输出奥宝EDI资料
            self.output_orbotech_ldi_opfx(*([x for x in args]+["wangping"]))
            if "gui_run" in args:
                job.PAUSE("check")            
            error_file = os.path.join("/tmp", "success_{0}_check_error.log".format(ID))
            if os.path.exists(error_file):
                return 
                    
            # 比对是否有动态周期 动态批次号等未改到的情况
            try:
                change_system_time_log = "/tmp/change_system_time.log"
                num = 1
                while os.path.exists(change_system_time_log):
                    time.sleep(1)
                    num += 1
                    if num > 1800:
                        break
                    
                with open(change_system_time_log, "w") as f:
                    f.write(jobname+"\n")
                    
                res = self.compare_layer_week_is_modify_success(step, layers.split(";"), year, month, day, xingqi, banci, picihao)                    
                #if "m1" in layers:
                    #step.PAUSE("dddd")
                    
                os.system("rm -rf {0}".format(change_system_time_log))
            except Exception as e:
                os.system("rm -rf {0}".format(change_system_time_log))
                print(e)
                with open("/tmp/compare_error.log", "w") as f:
                    f.write(str(e))
                res = u"比对异常"
            
            if "gui_run" in args:
                job.PAUSE("check")                
            if res:
                self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                        u"Status = '{0}'".format(u"输出异常"),
                                        u"AlarmLog = concat(AlarmLog,'{0}')".format(res)],
                                       condition="id={0}".format(output_id))                
                self.write_finish_log(str(output_id) +"_check_error")
                return            
            
        
        # self.write_finish_log(output_id)        
        
    def auto_output_jinxin(self, *args):
        """自动输出劲鑫tgz资料"""
        global silkscreenLayers
        jobname = args[0]
        self.colseJob(jobname)
        
        output_id = args[1]
        stepname = "panel"
        job.open(1)
        
        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=mm")
        
        get_sr_area_flatten("fill", get_sr_step=True)        
        f_xmin, f_ymin, f_xmax, f_ymax = get_profile_limits(step)        
        data_info = self.get_mysql_data(condtion="id = {0}".format(output_id))
        for info in sorted(data_info, key=lambda x: x["workLevel"] * -1):            
            """Circle_Year,Circle_Month,Circle_Day,Circle_YearWeekNo,\
            Circle_WeekDay,Circle_WorkShift,Circle_LotsNum"""
            ID = info["id"]
            tmp_dir = "{0}/{1}/{2}/{3}".format(tmp_path, job.name, "jinxin", ID)
            year = info["Circle_Year"]
            month = info["Circle_Month"]
            day = info["Circle_Day"]
            week = info["Circle_YearWeekNo"]
            xingqi = info["Circle_WeekDay"]
            banci = info["Circle_WorkShift"]
            picihao = info["Circle_LotsNum"]
            layers = info["OutLayer"]
            if picihao is None or picihao == "":
                picihao = "None"
                
            #还原临时层
            os.system('python /incam/server/site_data/scripts/sh_script/zl/check/TempLayerCheck.py {0} restore_normal'.format(job.name))
            
            
            for worklayer in layers.split(";"):            
                if not step.isLayer(worklayer):
                    log = u"输出层{0} 不存在，请检查tgz资料是否正常！<br>".format(worklayer)
                    self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                           condition="id={0}".format(ID))                        
                    self.write_finish_log(ID+"_check_error")                    
                    return
                else:
                    step.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=board".format(job.name, worklayer))
            
            for worklayer in job.matrix.getInfo()["gROWname"]:
                if "-ls" in worklayer or "-bf" in worklayer:
                    step.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=misc".format(job.name, worklayer))
                    
            if not solderMaskLayers:
                # 重新再获取下            
                for i, lay in enumerate(job.matrix.getInfo()["gROWname"]):
                    if job.matrix.getInfo()["gROWlayer_type"][i] == "solder_mask":
                        if lay in ["m1", "m2", "m1-1", "m1-2", "m2-1", "m2-2"]:
                            step.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=board".format(job.name, lay))
                    
            silkscreenLayers = layers.split(";")
            
            #检测周期数量
            check_types = ["silk_screen"]
            res = check_rule.check_record_week_picihao_to_mysql(*check_types)

            if res[0] != "success":
                self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                        u"Status = '{0}'".format(u"输出异常"),
                                        u"AlarmLog = concat(AlarmLog,'{0}')".format("<br>".join(res[1]))],
                                       condition="id={0}".format(ID))                
                self.write_finish_log(str(ID) +"_check_error")
                return
            
            start_time = self.get_current_format_time()
            log = u"开始修改周期 {0} <br>".format(start_time)            
            self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出中"),
                                    u"Status = '{0}'".format(u"输出中"),
                                    u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                   condition="id={0}".format(ID))             
            # 改周期批次
            print("------------>", year, month, day, week, banci, xingqi, picihao, layers, ID)
            os.system(r'python /incam/server/site_data/scripts/lyh/auto_modify_week_picihao.py auto_output {0} {1} {2} {3} {4} {5} {6} "{7}" {8}'.format(
                year, month, day, week, banci, xingqi, picihao, layers, ID
            ))
            # job.PAUSE("ddd1")
            error_file = os.path.join("/tmp", "success_{0}_check_error.log".format(ID))
            if os.path.exists(error_file):
                return
            
            
            #输出tgz
            # 改动态层跟时间为静态
            change_system_time_log = "/tmp/change_system_time.log"
            num = 1
            while os.path.exists(change_system_time_log):
                time.sleep(1)
                num += 1
                if num > 1800:
                    break
                
            with open(change_system_time_log, "w") as f:
                f.write(jobname+"\n")             
            self.modify_dynamic_layer_text(layers.split(";"))
            os.system("rm -rf {0}".format(change_system_time_log))
            job.save()
            start_time = self.get_current_format_time()
            log = u"开始输出tgz {0} <br>".format(start_time)              
            self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出中"),
                                    u"Status = '{0}'".format(u"输出中"),
                                    u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                   condition="id={0}".format(ID))             
            os.system(r'python /incam/server/site_data/scripts/sh_script/jin_xin/jinxin_tgz_auto.py {0} {1} {2} "{3}"'.format(
                "jinxin", jobname, ID, layers
            ))
            
            if "gui_run" in args:
                job.PAUSE("check")
                
            error_file = os.path.join("/tmp", "success_{0}_check_error.log".format(ID))
            if os.path.exists(error_file):
                return
            
            success_file = os.path.join("/tmp", "success_{0}.log".format(ID))
            if not os.path.exists(success_file):
                self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                        u"Status = '{0}'".format(u"输出异常"),
                                        u"AlarmLog = concat(AlarmLog,'{0}')".format(u"输出tgz失败！！<br>")],
                                       condition="id={0}".format(ID))
                return
            
            start_time = self.get_current_format_time()
            log = u"开始比对动态周期 {0} <br>".format(start_time)              
            self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出中"),
                                    u"Status = '{0}'".format(u"输出中"),
                                    u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                   condition="id={0}".format(ID))             
            # 比对是否有动态周期 动态批次号等未改到的情况
            try:
                change_system_time_log = "/tmp/change_system_time.log"
                num = 1
                while os.path.exists(change_system_time_log):
                    time.sleep(1)
                    num += 1
                    if num > 1800:
                        break
                    
                with open(change_system_time_log, "w") as f:
                    f.write(jobname+"\n")                    
                res = self.compare_layer_week_is_modify_success(step, layers.split(";"), year, month, day, xingqi, banci, picihao)
                os.system("rm -rf {0}".format(change_system_time_log))
            except Exception as e:
                print(e)
                with open("/tmp/compare_error.log", "w") as f:
                    f.write(str(e))                
                os.system("rm -rf {0}".format(change_system_time_log))
                res = u"比对异常"                
                
            if res:
                self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                        u"Status = '{0}'".format(u"输出异常"),
                                        u"AlarmLog = concat(AlarmLog,'{0}')".format(res)],
                                       condition="id={0}".format(ID))                
                self.write_finish_log(str(ID) +"_check_error")
                return 
        
        # self.write_finish_log(output_id)
        
    def compare_layer_week_is_modify_success(self, step, compare_layers,
                                             year, month, day, xingqi,
                                             banci, picihao):
        """检测层别的周期等是否修改一致"""
        step = gClasses.Step(job, step.name)
        step.open()
        step.COM("units,type=mm")
        
        # self.modify_dynamic_layer_text(compare_layers)
        
        symbol_list = step.DO_INFO("-t job -e {0} -m script -d SYMBOLS_LIST".format(job.name))
        
        symbol_list = list(set([x for x in symbol_list if not ("construct" in x or "i274x" in x)]))
        
        for worklayer in compare_layers:
            step.flatten_layer(worklayer, worklayer+"_flt")
            step.clearAll()
            step.affect(worklayer+"_flt")
            #if "m1" not in "".join(compare_layers):                
                #step.contourize()
            #else:
            step.resetFilter()
            step.selectSymbol(";".join(symbol_list), 1, 1)
            if step.featureSelected():
                step.moveSel(worklayer+"_symbol_tmp")
                step.clearAll()
                step.affect(worklayer+"_symbol_tmp")
                step.contourize()
                step.copySel(worklayer+"_flt")
            
        
        # if "m1" in "".join(compare_layers):    
        # 将所有动态txt改为静态
        self.modify_dynamic_layer_text([x + "_flt" for x in compare_layers], change_all_dynamic=True)        
        
        child = pexpect.spawn("su -")
        child.expect(u"Password:|密码：".encode("utf8"), timeout=10)
        child.sendline("VGT-InCAM$.")        
        child.expect(u"# ".encode("utf8"), timeout=10)
        child.sendline('date -s "20{0}-{1}-{2} 00:00:00"'.format(year, month, day))
        time.sleep(0.5)        
        child.expect(u"# ".encode("utf8"), timeout=10)
        child.sendline("exit")
        
        month_text = month.rjust(2, "0") if re.match("\d{1,2}", month) else month
        day_text = day.rjust(2, "0") if re.match("\d{1,2}", day) else day        
           
        step.COM("set_attribute,type=job,job=%s,name1=,name2=,name3=,attribute=xingqi,value=%s,units=inch" % (job.name,xingqi))     
        step.COM("set_attribute,type=job,job=%s,name1=,name2=,name3=,attribute=banci,value=%s,units=inch" % (job.name,banci))
        step.COM("set_attribute,type=job,job=%s,name1=,name2=,name3=,attribute=picihao,value=%s,units=inch" % (job.name,picihao))         
        step.COM("set_attribute,type=job,job=%s,name1=,name2=,name3=,attribute=year,value=%s,units=inch" % (job.name,year[-1]))
        step.COM("set_attribute,type=job,job=%s,name1=,name2=,name3=,attribute=month,value=%s,units=inch" % (job.name,month_text))
        step.COM("set_attribute,type=job,job=%s,name1=,name2=,name3=,attribute=day,value=%s,units=inch" % (job.name,day_text))
        
        for worklayer in compare_layers:
            step.flatten_layer(worklayer, worklayer+"_compare")
            step.clearAll()
            step.affect(worklayer+"_compare")
            #if "m1" not in "".join(compare_layers):    
                #step.contourize()
            #else:
            step.resetFilter()
            step.selectSymbol(";".join(symbol_list), 1, 1)
            if step.featureSelected():
                step.moveSel(worklayer+"_symbol_tmp")
                step.clearAll()
                step.affect(worklayer+"_symbol_tmp")
                step.contourize()
                step.copySel(worklayer+"_flt")                
        
        # if "m1" in "".join(compare_layers): 
        # 将所有动态txt改为静态
        self.modify_dynamic_layer_text([x + "_compare" for x in compare_layers], change_all_dynamic=True)            
        
        child = pexpect.spawn("su -")
        child.expect(u"Password:|密码：".encode("utf8"), timeout=10)
        child.sendline("VGT-InCAM$.")        
        child.expect(u"# ".encode("utf8"), timeout=10)
        child.sendline("/usr/sbin/ntpdate -u 192.168.2.126")
        time.sleep(0.5)        
        child.expect(u"# ".encode("utf8"), timeout=10)
        child.sendline("exit")
        
        step.VOF()
        for worklayer in compare_layers:
            step.COM("compare_layers,layer1=%s,job2=%s,step2=%s,\
            layer2=%s,layer2_ext=,tol=%s,area=global,consider_sr=yes,\
            ignore_attr=,map_layer=%s_diff,map_layer_res=%s" % (
            worklayer+"_flt", job.name, step.name, worklayer + "_compare", 25.4, worklayer, 2540))
            if step.STATUS > 0:
                return u"比对{0} 时报内存不足，请手动输出！".format(worklayer)
            
            if step.isLayer(worklayer+"_diff"):                
                step.clearAll()
                step.affect(worklayer+"_diff")
                step.resetFilter()
                step.selectSymbol("r0", 1, 1)
                if step.featureSelected():
                    return u"比对{0} 时周期修改跟动态周期不一致，请手动输出！".format(worklayer)
        
        step.VON()        

    def modify_dynamic_layer_text(self, check_layers, change_all_dynamic=False):
        """修改动态层别 text层名"""
        all_steps = get_panelset_sr_step(job.name, "panel")
        for stepname in all_steps + ["panel"]:            
            step = gClasses.Step(job, stepname)
            step.open()           
            for worklayer in check_layers:
                if not step.isLayer(worklayer):
                    continue
                step.clearAll()
                step.affect(worklayer)
                step.resetFilter()
                step.filter_set(feat_types='text')
                step.selectAll()
                layer_cmd = gClasses.Layer(step, worklayer)
                find_indexes = []
                find_texts = []
                if step.featureSelected():
                    feat_out = layer_cmd.featout_dic_Index(options="feat_index+select")["text"]
                    barcode_feat_out = layer_cmd.featout_dic_Index(options="feat_index+select")["barcodes"]
                    for obj in feat_out + barcode_feat_out:                        
                        
                        if change_all_dynamic:                           
                            if "$$" in str(obj.text).lower():
                                find_indexes.append(obj.feat_index)
                                find_texts.append(str(obj.text).replace("'", "").replace('"', ""))
                        else:
                            if "$$layer" in str(obj.text).lower() or "$$date" in str(obj.text).lower():
                                find_indexes.append(obj.feat_index)
                                find_texts.append(str(obj.text).replace("'", "").replace('"', ""))                            
                
                if find_indexes:
                    step.clearAll()
                    step.affect(worklayer)
                    step.resetFilter()
                    for i, index in enumerate(find_indexes):
                        step.selectNone()
                        step.selectFeatureIndex(worklayer, index)
                        if step.featureSelected():
                            text = find_texts[i].upper(
                                
                            ).replace("$$LAYER", worklayer.split("-ls")[0].upper(
                                
                            )).replace("$$DATE", "$#DATE")
                            
                            if change_all_dynamic:
                                text = find_texts[i].upper(
                                    
                                ).replace("$$","$#")
                                
                            step.COM("sel_change_txt,text={0},x_size=-1,y_size=-1,w_factor=-1,"
                                     "polarity=no_change,mirror=no_change,fontname=".format(text))
                            
                        step.selectFeatureIndex(worklayer, index)
                        if step.featureSelected():
                            step.addAttr(".string", attrVal=find_texts[i], valType='text', change_attr="yes")
                            
                        step.selectFeatureIndex(worklayer, index)
                        if step.featureSelected():                            
                            step.addAttr(".bit", attrVal="linshi_layer_text", valType='text', change_attr="yes")
                            
                if stepname == "panel":
                    #if "m1" in worklayer and not change_all_dynamic:
                        #step.COM("units,type=mm")
                        #step.addText(0, 0, "$$yy$$ww", 1, 1, 0.98, polarity="negative")
                        
                    self.change_panel_symbol_dynamic_layer(step, worklayer)
                    
            step.clearAll()
            
    def change_panel_symbol_dynamic_layer(self, step, worklayer):
        """修改symbol内的动态layer名"""
        step = gClasses.Step(job, step.name)
        step.selectNone()
        step.resetFilter()
        step.selectSymbol("sh-op*", 1, 1)
        if step.featureSelected():
            layer_cmd = gClasses.Layer(step, worklayer)
            feat_out = layer_cmd.featout_dic_Index(units="mm", options="feat_index+select")["pads"]            
            step.removeLayer("symbol_tmp")
            step.createLayer("symbol_tmp")
            for obj in feat_out:
                step.clearAll()
                step.affect("symbol_tmp")
                step.COM("truncate_layer,layer=symbol_tmp")
                step.addPad(0, 0, obj.symbol)
                step.resetFilter()
                step.selectSymbol(obj.symbol, 1, 1)
                if step.featureSelected():
                    step.COM("sel_break_level,attr_mode=merge")                    
                    
                    step.resetFilter()
                    step.filter_set(feat_types='text')
                    step.selectAll()
                    layer_cmd = gClasses.Layer(step, "symbol_tmp")
                    find_indexes = []
                    find_texts = []
                    if step.featureSelected():
                        feat_out = layer_cmd.featout_dic_Index(options="feat_index+select")["text"]
                        barcode_feat_out = layer_cmd.featout_dic_Index(options="feat_index+select")["barcodes"]
                        for text_obj in feat_out + barcode_feat_out:                        
                            if "$$layer" in str(text_obj.text).lower() or "$$date" in str(text_obj.text).lower():
                                find_indexes.append(text_obj.feat_index)
                                find_texts.append(str(text_obj.text).replace("'", "").replace('"', ""))
                    
                    if find_indexes:
                        for i, index in enumerate(find_indexes):
                            step.selectNone()
                            step.selectFeatureIndex("symbol_tmp", index)
                            if step.featureSelected():
                                text = find_texts[i].upper(
                                    
                                ).replace("$$LAYER", worklayer.split("-ls")[0].upper(
                                    
                                )).replace("$$DATE", "$#DATE")
                                step.COM("sel_change_txt,text={0},x_size=-1,y_size=-1,w_factor=-1,"
                                         "polarity=no_change,mirror=no_change,fontname=".format(text))
                    
                    step.selectNone()
                    step.resetFilter()
                    step.selectAll()
                    step.COM("sel_create_sym,symbol={0},x_datum=0,"
                    "y_datum=0,delete=no,fill_dx=2.54,fill_dy=2.54,"
                    "attach_atr=no,retain_atr=no".format(obj.symbol+"-ls-"+worklayer.split("-ls")[0]))
                    
                    step.clearAll()
                    step.affect(worklayer)
                    step.resetFilter()
                    step.selectSymbol(obj.symbol, 1, 1)
                    if step.featureSelected():
                        step.changeSymbol(obj.symbol+"-ls-"+worklayer.split("-ls")[0])                        
    
        step.removeLayer("symbol_tmp")            
        
    def auto_create_barcode_xml_files(self, *args):
        """喷印二维码XML文件自动生成"""
        "https://oapi.dingtalk.com/robot/send?access_token=a07fd9bfaa1069c0aa1921f141abbf1c2144a5e21ae6d9f765ebd5d24074836b"
        jobname = args[0]
        self.colseJob(jobname)
        
        output_id = args[1]
        stepname = "panel"
        job.open(0)
        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=inch")
        
        dest_net_path = ""
        data_info = self.get_mysql_data(condtion="id = {0}".format(output_id))
        for info in sorted(data_info, key=lambda x: x["workLevel"] * -1):                    
            dest_net_path = info["OutputPath"]  
            
        res = auto_barcode_xml_fun.create_xml_file(output_dir=dest_net_path)        
        if res[0] != "success":
            self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                    u"Status = '{0}'".format(u"输出异常"),
                                    u"AlarmLog = concat(AlarmLog,'{0}')".format("<br>"+res[1])],
                                   condition="id={0}".format(output_id))
            
            self.write_finish_log(str(output_id) +"_check_error") 
            
        self.write_finish_log(output_id)
    
    def auto_ouput_test_point_info(self, *args):
        """自动输出阻抗测点坐标信息"""
        "https://oapi.dingtalk.com/robot/send?access_token=a07fd9bfaa1069c0aa1921f141abbf1c2144a5e21ae6d9f765ebd5d24074836b"
        jobname = args[0]
        self.colseJob(jobname)
        
        output_id = args[1]
        stepname = "net"
        job.open(0)
        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=mm")
        
        self.kill_thread = False

        thrd = threading.Thread(target=self.check_get_process_is_run_normal, args=(output_id, "test_point"))
        thrd.start()
        
        with open("{0}/outputing_test_point_calc_time.log".format(tmp_path), "w") as f:
            f.write(os.environ.get("GENESIS_PID", "error"))
            
        log = test_point_program.write_test_point_file()        
        if log:
            self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                    u"Status = '{0}'".format(u"输出异常"),
                                    u"AlarmLog = concat(AlarmLog,'{0}')".format("<br>"+log)],
                                   condition="id={0}".format(output_id))
            
            self.write_finish_log(str(output_id) +"_check_error")                                 
        
        pid = os.environ.get("GENESIS_PID", None)
        if pid:
            os.system("kill {0}".format(pid.strip()))
        else:
            self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                    u"Status = '{0}'".format(u"输出异常"),
                                    u"AlarmLog = concat(AlarmLog,'{0}')".format(u"找不到incampro进程pid，请联系程序工程师！")],
                                   condition="id={0}".format(output_id))
            
        if os.path.exists("{0}/outputing_test_point_calc_time.log".format(tmp_path)):
            os.unlink("{0}/outputing_test_point_calc_time.log".format(tmp_path))
            
        self.write_finish_log(output_id)
        self.kill_thread = True
        
    def auto_ouput_measure_coodinate_info(self, *args):
        """自动输出正业量测坐标信息"""
        jobname = args[0]
        self.colseJob(jobname)
        
        output_id = args[1]
        stepname = "edit"
        job.open(0)
        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=mm")
        
        output_dir = "{0}/{1}/{2}/{3}".format(tmp_path, jobname, "measure_coodinate", output_id)
            
        log = measure_coordinate_program.calc_mark_point_info(output_dir, "yes")
        if log and "not_delete" not in log:
            sql = "select id from hdi_engineering.meascoordinate_base where job = '{0}'".format(jobname.split("-")[0].upper())
            datainfo = self.get_mysql_data_1(sql)
            # print(sql, datainfo, "-------------->")
            if datainfo:
                sql = "delete from hdi_engineering.meascoordinate_base where id = {0}"
                # print("--------------->", sql.format(datainfo[0]["id"]))
                self.delete_mysql_data(sql.format(datainfo[0]["id"]))
                
            self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                    u"Status = '{0}'".format(u"输出异常"),
                                    u"AlarmLog = concat(AlarmLog,'{0}')".format("<br>"+log)],
                                   condition="id={0}".format(output_id))
            
            self.write_finish_log(str(output_id) +"_check_error")
            
        if log and "not_delete" in log:
            self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                    u"Status = '{0}'".format(u"输出异常"),
                                    u"AlarmLog = concat(AlarmLog,'正常坐标已输出，异常部分请手动制作量测坐标。<br>{0}')".format("<br>"+log)],
                                   condition="id={0}".format(output_id))
            self.write_finish_log(str(output_id) +"_check_error")
            
        self.write_finish_log(output_id)
        self.kill_thread = True 
                
    def auto_uploading_target_info_to_erp(self, *args):
        """上传靶距信息到erp"""
        jobname = args[0]
        self.colseJob(jobname)
        
        output_id = args[1]
        # worklayer = args[2]
        stepname = "panel"
        job.open(0)
        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=mm")
        
        res = check_rule.check_target_distance_uploading_to_erp(uploading_to_erp="atuo_uploading")
        if res:
            if res[0] == "success":
                self.write_finish_log(output_id)
            else:
                if isinstance(res[0], (list, tuple)):
                    log = "<br>".join(res[0])
                else:
                    log = res[0]
                self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                        u"Status = '{0}'".format(u"输出异常"),
                                        u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                       condition="id={0}".format(output_id))
                
    def get_scale_rout_files(self, *args, **kwargs):
        """获取网络上1:1的锣带"""
        
        jobname = kwargs["Job"].lower()
        # dirpath = ur"\\192.168.2.174\GCfiles\CNC\成型锣带资料\{2}\{0}系列\{1}"
        dirpath = ur"\\192.168.2.172\GCfiles\锣带备份\锣带备份\{0}系列\{1}".format(jobname[1:4],jobname)
        arraylist_filepath = []
        #for rout_type in [u"普通锣机资料", u"CCD资料", u"锣斜边资料", u"盲锣资料"]:
            #job_dirpath = dirpath.format(jobname[1:4], jobname, rout_type)
            #if os.path.exists(job_dirpath):
        for name in os.listdir(dirpath):
            if "rout" in name and "xbk" not in name and "pnl" not in name and "rout-fb" not in name:
                filepath = os.path.join(dirpath, name)
                if "M48\n" in file(filepath).readlines():                    
                    arraylist_filepath.append(filepath)
            
        return arraylist_filepath, "success"

    def compare_rout_layer(self, **kwargs):
        """比对1:1的锣带是否跟资料一致"""
        filepath = kwargs["filepath"]
        worklayer = kwargs["worklayer"]
        jobname = kwargs["jobname"]
        stepname = kwargs["stepname"]
        step = kwargs["step"]                     
                
        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=mm")
        
        rout_temp_filepath = "c:/tmp/{0}".format(os.path.basename(filepath))
        shutil.copy(filepath, rout_temp_filepath)
        new_lines = []
        not_check_index = 0
        x_mirror = "no"
        y_mirror = "no"
        for i, line in enumerate(file(rout_temp_filepath).readlines()):
            if "%" in line:
                not_check_index = i
                
            if "M252" in line:
                line = line.replace("M252", "")
                
            if not_check_index > 0:
                new_lines.append(line)
            else:
                new_lines.append(line.replace(";", ""))

            if "/user" in line.lower():
                result = re.findall("(Mirror:.*) Mode:", line)
                if result:
                    if "No" in result[0]:
                        x_mirror = "no"
                        y_mirror = "no"
                    if "X方向" in result[0]:
                        x_mirror = "yes"
                        y_mirror = "no"
                    if "Y方向" in result[0]:
                        x_mirror = "no"
                        y_mirror = "yes"                 
        
        with open(rout_temp_filepath, "w") as f:
            f.write("".join(new_lines))
        
        step.removeLayer(worklayer+"_compare")
        step.removeLayer("r0_tmp")
        compare_output.input_drill_file(jobname, stepname, rout_temp_filepath, worklayer)
        
        os.unlink(rout_temp_filepath)
        
        if step.isLayer(worklayer+"_compare"):
            
            step.clearAll()                  
            step.affect(worklayer+"_compare")
            
            step.resetFilter()
            step.selectAll()
            
            comp_limits = get_layer_selected_limits(step, worklayer+"_compare")
            step.selectNone()
            
            panel_step = gClasses.Step(job, "panel")            
            f_xmin, f_ymin, f_xmax, f_ymax = get_profile_limits(panel_step)            
            
            rect= get_sr_area_for_step_include(panel_step.name, include_sr_step=["edit", "set"])
            sr_xmin = min([min(x1, x2) for x1, y1, x2, y2 in rect])    
            sr_ymin = min([min(y1, y2) for x1, y1, x2, y2 in rect])   
            sr_xmax = max([max(x1, x2) for x1, y1, x2, y2 in rect])    
            sr_ymax = max([max(y1, y2) for x1, y1, x2, y2 in rect])
            
            # 获取脚线区域 判断有小sr的区域
            panel_step.COM("units,type=mm")
            layer_cmd = gClasses.Layer(panel_step, signalLayers[0])
            feat_out = layer_cmd.featCurrent_LayerOut(units="mm")["pads"]
            jx_symbol_obj = [obj for obj in feat_out if obj.symbol in ("sh-con2", "sh-con")]
            all_jx_x = [obj.x for obj in jx_symbol_obj]
            all_jx_y = [obj.y for obj in jx_symbol_obj]
            if all_jx_x and all_jx_y:           
                min_jx_x = min(all_jx_x)
                max_jx_x = max(all_jx_x)
                min_jx_y = min(all_jx_y)
                max_jx_y = max(all_jx_y)
                
                STR = '-t step -e %s/%s -d REPEAT,units=mm' % (job.name, panel_step.name)
                gREPEAT_info = panel_step.DO_INFO(STR)
                gREPEATstep = gREPEAT_info['gREPEATstep']
                gREPEATxmax = gREPEAT_info['gREPEATxmax']
                gREPEATymax = gREPEAT_info['gREPEATymax']
                gREPEATxmin = gREPEAT_info['gREPEATxmin']
                gREPEATymin = gREPEAT_info['gREPEATymin']
                
                set_rect_area = []
                for i, name in enumerate(gREPEATstep): 
                    if gREPEATxmin[i] > min_jx_x and gREPEATymin[i] > min_jx_y and \
                       gREPEATxmax[i] < max_jx_x and gREPEATymax[i] < max_jx_y and \
                       ("set" in name or "edit" in name or "icg" in name):
                        set_rect_area.append(
                            [gREPEATxmin[i], gREPEATymin[i], gREPEATxmax[i], gREPEATymax[i]])
                try:                    
                    sr_xmin = min([min(x1, x2) for x1, y1, x2, y2 in set_rect_area])    
                    sr_ymin = min([min(y1, y2) for x1, y1, x2, y2 in set_rect_area])   
                    sr_xmax = max([max(x1, x2) for x1, y1, x2, y2 in set_rect_area])    
                    sr_ymax = max([max(y1, y2) for x1, y1, x2, y2 in set_rect_area])
                except:
                    pass
                
            step.COM("sel_transform,mode=anchor,oper=scale,duplicate=no,\
                x_anchor=%s,y_anchor=%s,angle=0,x_scale=%s,y_scale=%s,x_offset=%s,\
                y_offset=%s" % (0, 0, 1, 1, sr_xmin, sr_ymin))
            
            if x_mirror == "yes":
                step.COM("sel_transform,mode=anchor,oper=mirror,duplicate=no,\
                    x_anchor=%s,y_anchor=%s,angle=0,x_scale=%s,y_scale=%s,x_offset=%s,\
                    y_offset=%s" % ((f_xmin+f_xmax) *0.5, (f_ymin+f_ymax) *0.5, 1, 1, 0, 0))
                
            if y_mirror == "yes":
                step.COM("sel_transform,mode=anchor,oper=y_mirror,duplicate=no,\
                    x_anchor=%s,y_anchor=%s,angle=0,x_scale=%s,y_scale=%s,x_offset=%s,\
                    y_offset=%s" % ((f_xmin+f_xmax) *0.5, (f_ymin+f_ymax) *0.5, 1, 1, 0, 0))                 
        
            step.clearAll()
            step.flatten_layer(worklayer, worklayer+"_flt")
            
            step.affect(worklayer+"_flt")
            step.resetFilter()
            step.selectAll()
            flt_limits = get_layer_selected_limits(step, worklayer+"_flt")
            step.selectNone()
            
            step.clearAll()
            step.affect(worklayer+"_compare")            
            step.resetFilter()
            step.filter_set(feat_types='pad', polarity='positive')
            step.selectAll()
            count1 = step.featureSelected()
            step.selectNone()
            step.refSelectFilter(worklayer+"_flt", mode='cover', f_types="pad", polarity="positive")
            count2 = step.featureSelected()
            if count1 != count2:
                step.COM("register_layers,reference_layer={0},tolerance=38.1,"
                         "mirror_allowed=yes,rotation_allowed=yes,zero_lines=no,"
                         "reg_mode=affected_layers,register_layer=".format(worklayer+"_flt"))
                step.selectNone()
                step.refSelectFilter(worklayer+"_flt", mode='touch', f_types="pad", polarity="positive")
                count2 = step.featureSelected()
                if count1 != count2:
                    if worklayer != "rout":
                        if abs(abs(flt_limits[0]-flt_limits[2]) - abs(comp_limits[0]-comp_limits[2]))> 10 and\
                           abs(abs(flt_limits[1]-flt_limits[3]) - abs(comp_limits[1]-comp_limits[3]))> 10:
                            return u"set输出不用拉伸"
                            
                    if stepname == "panel":                        
                        return u"回读1:1 锣带资料{0}对齐失败，请手动输出拉伸锣带！".format(worklayer)
                    else:
                        return u"回读拉伸锣带资料{0}对齐失败，请手动输出拉伸锣带！".format(worklayer)
            
            if "ccd" in worklayer:
                # ccd锣有光点回读进来没有尺寸大小 需处理一下
                step.resetFilter()
                step.selectSymbol("r0", 1, 1)
                if step.featureSelected():
                    step.clearAll()
                    step.affect(worklayer+"_flt")
                    step.resetFilter()
                    step.filter_set(feat_types='pad')
                    step.refSelectFilter(worklayer+"_compare", mode='include', f_types="pad", include_syms="r0", polarity="positive")
                    if step.featureSelected():
                        step.copySel(worklayer+"_compare")
                
            #给后续提取step排序用
            step.copyLayer(job.name, step.name, worklayer+"_compare", worklayer+"_origin_output")
            #step.affect(worklayer+"_compare")
            #step.selectAll()
            #if step.featureSelected():
                #step.selectDelete()
            
            step.clearAll()
            step.VOF()
            step.COM("compare_layers,layer1=%s,job2=%s,step2=%s,\
            layer2=%s,layer2_ext=,tol=%s,area=global,consider_sr=yes,\
            ignore_attr=,map_layer=%s_diff,map_layer_res=%s" % (
            worklayer+"_flt", jobname, stepname, worklayer + "_compare", 25.4, worklayer, 254))
            if step.STATUS > 0:
                return u"比对{0} 时报内存不足，请手动输出！".format(worklayer)
            
            step.VON()
            if step.isLayer(worklayer+"_diff"):                
                step.clearAll()
                step.affect(worklayer+"_diff")
                step.resetFilter()
                step.selectSymbol("r0", 1, 1)
                if step.featureSelected():
                    if worklayer != "rout":
                        if abs(abs(flt_limits[0]-flt_limits[2]) - abs(comp_limits[0]-comp_limits[2]))> 10 and\
                           abs(abs(flt_limits[1]-flt_limits[3]) - abs(comp_limits[1]-comp_limits[3]))> 10:
                            return u"set输出不用拉伸"
                        
                    if stepname == "panel":      
                        return u"{0} 1:1锣带跟tgz资料内{1}层回读比对不一致，请手动输出！".format(os.path.basename(filepath), worklayer)
                    else:
                        return u"{0} 拉伸锣带跟tgz资料内{1}层回读比对不一致，请手动输出！".format(os.path.basename(filepath), worklayer)

        else:
            if stepname == "panel":  
                return u"{0} 1:1锣带回读异常，不能正常比对，请手动输出！".format(os.path.basename(filepath))
            else:
                return u"{0} 拉伸锣带回读异常，不能正常比对，请手动输出！".format(os.path.basename(filepath))
        
        step.removeLayer(worklayer+"_compare")
        step.removeLayer("r0_tmp")
        step.removeLayer(worklayer+"_flt")
        
        return None
    
    def auto_set_rout_step_order(self, **kwargs):
        """根据1:1锣带提取step的排刀序"""    
        
        if kwargs:            
            worklayer = kwargs["worklayer"]
            jobname = kwargs["jobname"]
            stepname = kwargs["stepname"]
            step = kwargs["step"]
            mirror = kwargs["mirror"]
                    
            step = gClasses.Step(job, step.name)
        else:
            worklayer = "test"
            step = gClasses.Step(job, "panel")
            mirror = "no"
        
        csh_script_cmd = "c:/tmp/{0}_sort_rout_order_cmd.log".format(jobname)
        if os.path.exists(csh_script_cmd):
            os.unlink(csh_script_cmd)
            
        step.COM("units,type=mm")        
        STR = '-t step -e %s/%s -d REPEAT,units=mm' % (job.name, step.name)
        gREPEAT_info = step.DO_INFO(STR)
        gREPEATstep = gREPEAT_info['gREPEATstep']
        gREPEATxmax = gREPEAT_info['gREPEATxmax']
        gREPEATymax = gREPEAT_info['gREPEATymax']
        gREPEATxmin = gREPEAT_info['gREPEATxmin']
        gREPEATymin = gREPEAT_info['gREPEATymin']
        
        sr_step = step.getSr()
        
        dic_rect_sr_line = {}
        repeat_num = -1
        for num, table_info in enumerate(sr_step.table):
            xnum = table_info.xnum
            ynum = table_info.ynum
            repeat_num += xnum * ynum
    
            if re.match(r'edit|set', table_info.step):
                for i in xrange(len(gREPEATstep)):
                    if (xnum == 1 and ynum == 1 and i == repeat_num) or \
                           ((xnum > 1 or ynum > 1) and repeat_num - xnum * ynum < i <= repeat_num):
                        x1 = gREPEATxmin[i]
                        x2 = gREPEATxmax[i]
                        y1 = gREPEATymin[i]
                        y2 = gREPEATymax[i]
                        for nx in range(1, xnum + 1):
                            for ny in range(1, ynum + 1):
                                #print num, repeat_num, i, i - \
                                    #(repeat_num - xnum * ynum + 1) + \
                                    #1, nx * ny, nx, ny				
                                if i - (repeat_num - xnum * ynum + 1) + 1 == ny + (nx - 1) * ynum:
                                    dic_rect_sr_line[(x1, y1, x2, y2)] = [num + 1, nx, ny]        
        
        layer_cmd = gClasses.Layer(step, worklayer+"_origin_output")
        feat_out = layer_cmd.featOut(units="mm")["lines"]
        feat_out += layer_cmd.featOut(units="mm")["arcs"]
        symbols = list(set([obj.symbol for obj in feat_out]))
        symbols = []
        
        pad_feat_out = layer_cmd.featOut(units="mm")["pads"]
        pad_symbols = list(set([obj.symbol for obj in pad_feat_out]))
        
        if not pad_symbols and mirror == "yes":
            return u"获取1:1step排序异常，请手动输出!<br>"
        
        get_sr_area_flatten("set_area", include_sr_step=["set", "edit"])
        step.clearAll()
        step.affect("set_area")
        step.contourize()
        
        step.clearAll()
        step.affect(worklayer+"_origin_output")
        step.resetFilter()
        
        set_rect_area = []
        sorted_keys = []
        for symbolname in pad_symbols + symbols:
            dic_rect_index = {}
            has_set_edit = False
            for i, name in enumerate(gREPEATstep):
                set_rect_area.append(
                    [gREPEATxmin[i], gREPEATymin[i], gREPEATxmax[i], gREPEATymax[i]])
                
                step.removeLayer("set_area_tmp")
                if step.isLayer("set_area"):
                    step.clearAll()
                    step.affect("set_area")
                    step.resetFilter()
                    step.selectRectangle(gREPEATxmin[i], gREPEATymin[i], gREPEATxmax[i], gREPEATymax[i], intersect='yes')
                    if step.featureSelected() == 1:
                        step.copyToLayer("set_area_tmp", size=254)
                    elif step.featureSelected() > 1:
                        surface_layer_cmd = gClasses.Layer(step, "set_area")
                        surface_indexes = surface_layer_cmd.featSelIndex()
                        step.selectNone()
                        print("---------->", surface_indexes)
                        for index in surface_indexes:
                            step.selectNone()
                            step.selectFeatureIndex("set_area", index)
                            x1, y1, x2, y2 = get_layer_selected_limits(step, "set_area")
                            if abs(x1 - gREPEATxmin[i]) < 1 and abs(y1 - gREPEATymin[i]) < 1 and \
                               abs(x2 - gREPEATxmax[i]) < 1 and abs(y2 - gREPEATymax[i]) < 1:
                                step.copyToLayer("set_area_tmp", size=254)
                                break                        
                
                step.clearAll()
                step.affect(worklayer+"_origin_output")
                step.resetFilter()
                step.selectNone()
                step.setSymbolFilter(symbolname)
                
                #if mirror == "yes":                    
                    #step.setAttrFilter(".comp,option=none")
                    
                if step.isLayer("set_area_tmp"):
                    step.refSelectFilter("set_area_tmp")
                    # step.PAUSE(symbolname)
                else:
                    step.selectRectangle(gREPEATxmin[i], gREPEATymin[i], gREPEATxmax[i], gREPEATymax[i], intersect='yes')
                rect = (gREPEATxmin[i], gREPEATymin[i], gREPEATxmax[i], gREPEATymax[i])
                if step.featureSelected():                    
                    layer_cmd = gClasses.Layer(step, worklayer+"_origin_output")
                    indexes = [int(x) for x in layer_cmd.featSelIndex()]
                    dic_rect_index[rect] = min(indexes)
                    if re.match("edit|set", name):
                        has_set_edit = True
                        
            if has_set_edit:
                # 提取最多step的的symbol排序
                if len(dic_rect_index.keys()) > len(sorted_keys):                    
                    sorted_keys = sorted(dic_rect_index.keys(), key=lambda key: dic_rect_index[key])
                    #if mirror == "yes":
                        #sorted_keys = sorted(dic_rect_index.keys(), key=lambda key: dic_rect_index[key] * -1)
                        
            if symbolname in pad_symbols and has_set_edit:
                # step.PAUSE(str([symbolname, len(dic_rect_sr_line) , len(dic_rect_index), has_set_edit]))
                if len(dic_rect_sr_line) == len(dic_rect_index):
                    break
        
        # print(sorted_keys, dic_rect_sr_line)
        arraylist = []
        step.clearAll()
        step.removeLayer("check_order")
        step.createLayer("check_order")
        step.affect("check_order")
        for i, rect in enumerate(sorted_keys):
            if dic_rect_sr_line.has_key(rect):
                # cmd = "nc_order,serial={0},sr_line={1},sr_nx={2},sr_ny={3},mode=lrbt,snake=yes\n"
                cmd = "ncr_order,sr_line={1},sr_nx={2},sr_ny={3},serial={0},optional=no,mode=one,snake=no,full=0,nx=0,ny=0\n"
                arraylist.append(cmd.format(i+1, *dic_rect_sr_line[rect]))
                text = "{0} {1} {2} {3}".format(i+1, *dic_rect_sr_line[rect])
                
                step.addText((rect[0]+rect[2]) *0.5, (rect[1]+rect[3]) *0.5, text, 5, 5, 1)
        
        step.clearAll()
        # step.PAUSE("ddd")
        if arraylist:
            with open(csh_script_cmd, "w") as f:
                f.write("".join(arraylist))
        else:
            layer_cmd = gClasses.Layer(step, worklayer)
            feat_out = layer_cmd.featOut(units="mm")["lines"]
            feat_out += layer_cmd.featOut(units="mm")["arcs"]
            
            current_feat_out = layer_cmd.featCurrent_LayerOut(units="mm")["lines"]
            current_feat_out += layer_cmd.featCurrent_LayerOut(units="mm")["arcs"]
            
            #锣带全部做在panel内的 不做涨缩输出
            if len(feat_out) == len(current_feat_out):
                return "not output"
            
        if not os.path.exists(csh_script_cmd):
            return u"获取1:1step排序异常，请手动输出2!<br>"
            
        return None
                
    def set_output_rout_by_origin_tool_order(self, jobname, stepname, worklayer, origin_filepath):
        """按1:1锣带提取刀序"""
        origin_lines = file(origin_filepath).readlines()
        origin_headerIndex = origin_lines.index('%\n')
        origin_Holes_T = []
        origin_Holes_size = {}
        rout_Holes_size = {}
        x_mirror = None
        y_mirror = None
        for i in range(origin_headerIndex):
            if re.match('^T.*', origin_lines[i]):
                result = re.findall("(^T\d+);?C(\d+\.?\d+)", origin_lines[i])
                if result:
                    origin_Holes_T.append(result[0][0])
                    origin_Holes_size[result[0][0]] = result[0][1]
                    if "DRL" not in origin_lines[i] and "ZZ" not in origin_lines[i]:
                        rout_Holes_size[result[0][0]] = result[0][1]
                        
        for line in origin_lines:
            if "/user" in line.lower():
                result = re.findall("(Mirror:.*) Mode:", line)
                print("----------->", result)
                if result:
                    if "No" in result[0]:
                        x_mirror = "no"
                        y_mirror = "no"
                    if "X方向" in result[0]:
                        x_mirror = "yes"
                        y_mirror = "no"
                    if "Y方向" in result[0]:
                        x_mirror = "no"
                        y_mirror = "yes"                          
        
        # 有相同刀的情况需到tgz内提取第四位刀径
        if len(rout_Holes_size.values()) != len(set(rout_Holes_size.values())): # or "gui_run" in sys.argv:
            step = gClasses.Step(job, stepname)
            step.open()
            
            sizes = rout_Holes_size.values()
            same_size = list(set([x for i, x in enumerate(sizes) if x in sizes[i+1:]]))
            
            dic_same_size = {}
            
            rout_temp_filepath = "c:/tmp/modify_{0}".format(os.path.basename(origin_filepath))
            shutil.copy(origin_filepath, rout_temp_filepath)
            
            new_lines = []
            not_check_index = 0
            for i, line in enumerate(file(rout_temp_filepath).readlines()):
                if "%" in line:
                    not_check_index = i
                    
                if "M252" in line:
                    line = line.replace("M252", "")                
                    
                if not_check_index > 0:
                    if re.match('^T.*', line):
                        result = re.findall("(^T\d+);?C(\d+\.?\d+)", line)
                        if result:
                            if result[0][1] in same_size:
                                new_lines.append("{0}C{1}".format(result[0][0], dic_same_size[result[0][0]]) + "\n")
                            else:
                                new_lines.append(line)
                                
                            # new_lines.append("{0}C{1}.000".format(result[0][0], int(result[0][0][1:])) + "\n")
                    else:
                        new_lines.append(line)
                else:
                    if re.match('^T.*', line):
                        result = re.findall("(^T\d+);?C(\d+\.?\d+)", line)
                        if result:
                            if result[0][1] in same_size:
                                new_lines.append("{0}C{1}".format(result[0][0], float(result[0][1]) + (i+10)*0.001) + "\n")
                                dic_same_size[result[0][0]] = float(result[0][1]) + (i + 10)*0.001
                            else:
                                new_lines.append(line)
                                #new_lines.append("{0}C{1}".format(result[0][0], float(result[0][1]) + 0.001) + "\n")
                                #dic_same_size[result[0][0]] = float(result[0][1]) + 0.001
                                
                            # new_lines.append("{0}C{1}.000".format(result[0][0], int(result[0][0][1:])) + "\n")
                    else:
                        new_lines.append(line)
            
            with open(rout_temp_filepath, "w") as f:
                f.write("".join(new_lines))
                
            step.removeLayer(worklayer+"_compare")
            compare_output.input_drill_file(jobname, stepname, rout_temp_filepath, worklayer)                     
            
            os.unlink(rout_temp_filepath)
            step.clearAll()
            step.affect(worklayer+"_compare")            
            step.COM("register_layers,reference_layer={0},tolerance=38.1,"
                     "mirror_allowed=yes,rotation_allowed=yes,zero_lines=no,"
                     "reg_mode=affected_layers,register_layer=".format(worklayer+"_origin_output"))            
            
            step.COM("compensate_layer,source_layer={0},dest_layer={1},dest_layer_type=document".format(worklayer+"_compare", worklayer+"_compare_comp"))
            step.COM("compensate_layer,source_layer={0},dest_layer={1},dest_layer_type=document".format(worklayer, worklayer+"_comp"))
            
            arraylist_t_order = []
            for key, value in origin_Holes_size.iteritems():
                if value in same_size and key in rout_Holes_size.keys():
                # if key in rout_Holes_size.keys():
                    step.clearAll()
                    step.affect(worklayer+"_compare_comp")
                    # step.selectSymbol("r{0}".format(int(key[1:]) *1000))
                    step.selectSymbol("r{0}".format(dic_same_size[key]*1000), 1, 1)
                    if step.featureSelected():
                        step.removeLayer("check_tmp_line")
                        step.copySel("check_tmp_line")
                        step.clearAll()
                        # step.affect("check_tmp_line")
                        # step.changeSymbol("r{0}".format(float(value)*1000+len(origin_Holes_size) + 3))
                        
                        step.clearAll()
                        step.affect(worklayer+"_comp")
                        step.resetFilter()
                        step.filter_set(feat_types='line;arc')                        
                        step.refSelectFilter("check_tmp_line", mode='cover')
                        if step.featureSelected():
                            layer_cmd = gClasses.Layer(step, worklayer+"_comp")
                            dic_symbol = {}
                            feat_out = layer_cmd.featSelOut(units="mm")["lines"]
                            feat_out += layer_cmd.featSelOut(units="mm")["arcs"]
                            for obj in feat_out:                                
                                # if abs(float(obj.symbol[1:]) - dic_same_size[key]*1000) <= 35:                                    
                                if dic_symbol.has_key(obj.symbol):                                    
                                    dic_symbol[obj.symbol] += obj.len
                                else:
                                    dic_symbol[obj.symbol] = obj.len
                            
                            count = max(dic_symbol.values())
                            size = None
                            for symbol, value in dic_symbol.iteritems():
                                if value == count:
                                    size = "%.4f" % (float(symbol[1:]) *0.001)
                                    break
                            
                            if size:
                                arraylist_t_order.append("{0}C{1}".format(key, size))
                else:
                    arraylist_t_order.append("{0}C{1}".format(key, value))
            
            print(len(arraylist_t_order), arraylist_t_order)
            print(len(origin_Holes_size), origin_Holes_size)
            if len(arraylist_t_order) == len(origin_Holes_size):
                
                arraylist_t_size = [t.split("C")[1] for t in sorted(arraylist_t_order, key=lambda x: int(x[1:3]))]
                
                if "M252" in "".join(origin_lines):
                    size = ""
                    for line in origin_lines[::-1]:
                        if "M252" in line:
                            size = float(line.split("C")[1].strip()) + 0.002
                            if str(size) != arraylist_t_size[0]:
                                arraylist_t_size.insert(0, str(size))
                            
                with open("c:/tmp/{0}_rout_tool_order.log".format(job.name), "w") as f:
                    f.write("\n".join(arraylist_t_size))
                    
                return arraylist_t_order, x_mirror, y_mirror
            
            return "error", x_mirror, y_mirror        
        
        else:
            arraylist_t_size = [origin_Holes_size[t] for t in sorted(origin_Holes_size.keys(), key=lambda x: int(x[1:3]))]
            
            if "M252" in "".join(origin_lines):
                size = ""
                for line in origin_lines[::-1]:
                    if "M252" in line:
                        size = float(line.split("C")[1].strip()) + 0.002
                        if str(size) != arraylist_t_size[0]:                            
                            arraylist_t_size.insert(0, str(size))
                        
            with open("c:/tmp/{0}_rout_tool_order.log".format(job.name), "w") as f:
                f.write("\n".join(arraylist_t_size))
                
        return "sucess", x_mirror, y_mirror
    
    def check_output_order(self, output_filepath, origin_filepath, zscode):
        """检测最终输出的刀序是否一致"""
        origin_lines = file(origin_filepath).readlines()
        origin_headerIndex = origin_lines.index('%\n')
        origin_Holes_T = []
        origin_Holes_size = {}
        origin_Holes_T_body = {}
        for i in range(origin_headerIndex):
            if re.match('^T.*', origin_lines[i]):
                result = re.findall("(^T\d+);?C(\d+\.?\d+)", origin_lines[i])
                if result:
                    origin_Holes_T.append(result[0][0])
                    origin_Holes_size[result[0][0]] = round(float(result[0][1]) *1000, 1)                    
    
        for i, line in enumerate(origin_lines):
            if i >= origin_headerIndex:
                if line == '%\n':
                    key = ""
                if line.startswith("T") or line.startswith("/T"):
                    key = line.strip()
                if line == 'M30\n':
                    break
                if line == "/M30\n":
                    continue
    
                if key:
                    result = re.findall("(T\d+)", key)
                    if origin_Holes_T_body.has_key(result[0]):
                        if key not in line:                            
                            origin_Holes_T_body[result[0]].append(line)
                    else:
                        origin_Holes_T_body[result[0]] = []                     
    
        output_lines = file(output_filepath).readlines()
        output_headerIndex = output_lines.index('%\n')
        output_Holes_T = []
        output_Holes_size = {}
        output_Holes_T_body = {}
        params = {}
        for i in range(output_headerIndex):
            if re.match('^T.*', output_lines[i]):
                result = re.findall("(^T\d+);?C(\d+\.?\d+)", output_lines[i])
                if result:
                    output_Holes_T.append(result[0][0])
                    if "S" in output_lines[i] and "F" in output_lines[i]:
                        output_Holes_size[result[0][0]] = [round(float(result[0][1]) *1000, 1), "chain"]
                    else:
                        output_Holes_size[result[0][0]] = [round(float(result[0][1]) *1000, 1), "hole"]
                    params[result[0][0]] = output_lines[i].split(result[0][1])[1]
    
    
        for i, line in enumerate(output_lines):
            if i >= output_headerIndex:
                if line == '%\n':
                    key = ""
                if line.startswith("T") or line.startswith("/T"):
                    key = line.strip()
                if line == 'M30\n':
                    break
                if line == "/M30\n":
                    continue
    
                if key:
                    result = re.findall("(T\d+)", key)
                    if output_Holes_T_body.has_key(result[0]):
                        if key not in line:                            
                            output_Holes_T_body[result[0]].append(line)
                    else:
                        output_Holes_T_body[result[0]] = []                    
    
        if len(origin_Holes_T) != len(output_Holes_T):
            return u"1:1原稿锣带跟拉伸输出的锣带刀序总数量不一致，请手动输出!<br>"
    
        screen_picture = "d:/rout_order_picture/{0}.png".format(os.path.basename(output_filepath))
        clear_log = ""
        if not os.path.exists(screen_picture):
            clear_log = u"请尝试清除报警状态重新输出，{1}若还是报警，{0}".format(screen_picture, getattr(self, "reoutput_rout", "no"))
            
        for key1, value1 in output_Holes_size.iteritems():
            for key2, value2 in origin_Holes_size.iteritems():
                if key1 == key2 and value1[0] <> value2:
                    return u"拉伸输出的锣带刀序跟1:1原稿不一致1，输出异常，{0}请手动输出!<br>".format(clear_log)
    
                if key1 == key2:
                    origin_coor = [line for line in origin_Holes_T_body[key1]
                                   if "X" in line and "Y" in line and "M02" not in line]
                    output_coor = [line for line in output_Holes_T_body[key1]
                                   if "X" in line and "Y" in line and "M02" not in line]
                    if len(origin_coor) <> len(output_coor):
                        return u"拉伸输出的锣带刀序跟1:1原稿不一致2，输出异常，请手动输出!<br>"
                    
                    if value1[1] == "hole":
                        continue                    
    
                    origin_M02_coor = [line for line in origin_Holes_T_body[key1]
                                       if "X" in line and "Y" in line and "M02" in line]
    
                    output_M02_coor = [line for line in output_Holes_T_body[key1]
                                       if "X" in line and "Y" in line and "M02" in line]
                    try:                        
                        for i, line in enumerate(origin_M02_coor):
                            origin_coor_xy = line.strip().replace("M02","").replace("M70","").replace("M90","").replace("M80","").replace("/","").replace("X+","  ").replace("Y+","  ").replace("X"," ").replace("Y"," ")
                            origin_coor_xy_list = origin_coor_xy.split()
                            if i > len(output_M02_coor) - 1:
                                continue                            
        
                            output_coor_xy = output_M02_coor[i].strip().replace("M02","").replace("M70","").replace("M90","").replace("M80","").replace("/","").replace("X+","  ").replace("Y+","  ").replace("X"," ").replace("Y"," ")
                            output_coor_xy_list = output_coor_xy.split()
                            for a, b in zip(origin_coor_xy_list, output_coor_xy_list):
                                if abs(float(a) - float(b)) > 1:
                                    return u"拉伸输出的锣带set排序跟1:1原稿不一致1，输出异常，请手动输出!<br>"
                    except:
                        return u"拉伸输出的锣带set排序跟1:1原稿不一致2，输出异常，请手动输出!<br>"
    
        return None
                
    def sort_output_rout_by_origin_rout(self, output_filepath, origin_filepath):
        """按1:1锣带进行排序"""
        origin_lines = file(origin_filepath).readlines()
        origin_headerIndex = origin_lines.index('%\n')
        origin_Holes_T = []
        origin_Holes_size = {}
        for i in range(origin_headerIndex):
            if re.match('^T.*', origin_lines[i]):
                result = re.findall("(^T\d+);?C(\d+\.?\d+)", origin_lines[i])
                if result:
                    origin_Holes_T.append(result[0][0])
                    origin_Holes_size[result[0][0]] = round(float(result[0][1]) *1000, 1)                    
        
        output_lines = file(output_filepath).readlines()
        headerIndex = output_lines.index('%\n')
        Holes_T = []
        Holes_size = {}
        params = {}
        for i in range(headerIndex):
            if re.match('^T.*', output_lines[i]):
                result = re.findall("(^T\d+);?C(\d+\.?\d+)", output_lines[i])
                if result:
                    Holes_T.append(result[0][0])
                    if "S" in output_lines[i] and "F" in output_lines[i]:
                        Holes_size[result[0][0]] = [round(float(result[0][1]) *1000, 1), "chain"]
                    else:
                        Holes_size[result[0][0]] = [round(float(result[0][1]) *1000, 1), "hole"]
                    # Holes_size[result[0][0]] = round(float(result[0][1]) *1000, 1)
                    params[result[0][0]] = output_lines[i].split(result[0][1])[1]
                    
        if len(origin_Holes_T) != len(Holes_T):
            return u"1:1原稿锣带跟拉伸输出的锣带刀序总数量不一致，系统无法自动排序，请手动输出!"
        
        for key, value in Holes_size.iteritems():
            if value[0] not in origin_Holes_size.values():
                return u"拉伸输出的锣带刀径{0} 不存在1:1原稿锣带中，系统无法自动排序，请手动输出!".format(value[0]*0.001)
                   
        Holes_T_body = {}
        
        rout_end_info = ""
        for i, line in enumerate(output_lines):
            if "/user" in line.lower():
                rout_end_info = line
                
        for i, line in enumerate(output_lines):
            if i >= headerIndex:
                if line == '%\n':
                    key = ""
                if line.startswith("T") or line.startswith("/T"):
                    key = line.strip()
                if line == 'M30\n':
                    break
                if line == "/M30\n":
                    continue
                
                if key:                    
                    if Holes_T_body.has_key(key):
                        if key not in line:                            
                            Holes_T_body[key].append(line)
                    else:
                        Holes_T_body[key] = []
                        
        arraylist_header = []
        arraylist_body = []
        for i, line in enumerate(origin_lines):
            if re.match('^T.*', origin_lines[i]):
                result = re.findall("(^T\d+);?C(\d+\.?\d+)", origin_lines[i])
                if result:
                    param = None
                    body_key = None
                    for key, value in Holes_size.iteritems():
                        if value[0] == round(float(result[0][1]) *1000, 1):
                            if "S" in line and "F" in line:
                                if "chain" in value:
                                    param = params[key]
                                    body_key = key
                            else:
                                if "hole" in value:
                                    param = params[key]
                                    body_key = key                                
                    
                    if param is None:
                        return u"{0}刀径参数匹配失败，请手动输出！".format(result[0][1])
                    
                    if ";" in line:
                        arraylist_header.append(";C".join(result[0]) + param)
                    else:
                        arraylist_header.append("C".join(result[0]) + param)
                    
                    for key, value in Holes_T_body.iteritems():
                        if body_key in key:
                            if ";" in line:                                
                                if "/" in key:
                                    arraylist_body.append("/"+result[0][0]+"\n")
                                else:
                                    if "/M30\n" not in arraylist_body:
                                        arraylist_body.append("/M30\n")
                                        
                                    arraylist_body.append(result[0][0]+"\n")
                            else:
                                arraylist_body.append("C".join(result[0]) + param)
                                
                            arraylist_body += value
                else:
                    return u"1:1原稿锣带刀头分析异常，请手动输出！"
            else:
                arraylist_header.append(line)
            
            if i == origin_headerIndex:
                break
            
        arraylist_body.append("M30"+"\n")
        arraylist = arraylist_header + arraylist_body + [rout_end_info]
        with open(output_filepath, "w") as f:
            f.write("".join(arraylist))
            
    def delete_empty_step(self):
        """删除空的step 或空的层"""
        cols = []
        rows = []        
        
        while True:
            matrixInfo = job.matrix.getInfo()
            for i, _type in enumerate(matrixInfo["gCOLtype"]):
                if _type == "empty":
                    col = matrixInfo["gCOLcol"][i]
                    job.COM("matrix_delete_col,job=%s,matrix=matrix,col=%s" % (job.name, col))
                    cols.append(col)
                    cols.append(matrixInfo["gCOLstep_name"][i])
                    break
            else:
                break
            
        while True:
            matrixInfo = job.matrix.getInfo()
            for i, _type in enumerate(matrixInfo["gROWtype"]):
                if _type == "empty":
                    row = matrixInfo["gROWrow"][i]
                    job.COM("matrix_delete_row,job=%s,matrix=matrix,row=%s" % (job.name, row))
                    rows.append(row)
                    rows.append(matrixInfo["gROWname"][i])
                    break
            else:
                break
                
    def output_scale_rout_file(self, *args):
        """自动输出锣带拉伸资料"""
        jobname = args[0]
        self.colseJob(jobname)
        
        if "gui_run" in sys.argv:
            os.system("rm -rf c:/tmp/check_app_pause.log")
            os.system("rm -rf c:/tmp/exit_app.log")
            thrd1 = threading.Thread(target=self.kill_rout_output_error_stop, args=(jobname))
            thrd1.start()
            
            with open("c:/tmp/check_app_pause.log", "w") as f:
                f.write("yes")
            job.PAUSE("start-->output")
        
        output_id = args[1]
        # worklayer = args[2]
        stepname = "panel"
        job.open(1)
        
        self.delete_empty_step()
        
        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=mm")
        
        if not flip.is_exists_flip():
            #for layer in innersignalLayers + solderMaskLayers + silkscreenLayers:
                #step.removeLayer(layer)
                
            d = job.matrix.getInfo()
            for i, layer in enumerate(d["gROWname"]):
                if d["gROWlayer_type"][i] == "rout":
                    if job.name in layer:
                        step.removeLayer(layer)     
                    continue
                if layer in outsignalLayers:
                    continue
                #if d["gROWcontext"][i] == "board":
                    #continue
                step.removeLayer(layer)     
            
            job.save()
            job.close(1)
            
            self.colseJob(jobname)
            job.open(0)
            step = gClasses.Step(job, stepname)
            step.open()
            step.COM("units,type=mm")
            
        
        get_sr_area_flatten("fill", get_sr_step=True)        
        f_xmin, f_ymin, f_xmax, f_ymax = get_profile_limits(step)        
        data_info = self.get_mysql_data(condtion="id = {0}".format(output_id))
        for info in sorted(data_info, key=lambda x: x["workLevel"] * -1):            
            
            ID = info["id"]
            tmp_dir = "{0}/{1}/{2}/{3}".format(tmp_path, job.name, "rout", ID)            

            if info["XzsRatio"] is None or info["YzsRatio"] is None:
                log = u"登记系数异常，scalex:{XzsRatio},scale_y:{YzsRatio},请重新登记！".format(**info)
                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                       condition="id={0}".format(ID))                        
                self.write_finish_log(output_id+"_check_error")                    
                return
            
            scale_x = float(info["XzsRatio"])
            scale_y = float(info["YzsRatio"])
            
            if scale_x <= 0 or scale_y <= 0:
                log = u"登记系数异常，scalex:{XzsRatio},scale_y:{YzsRatio},请重新登记！".format(**info)
                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                       condition="id={0}".format(ID))                        
                self.write_finish_log(output_id+"_check_error")                    
                return                
            
            zscode = info["ZsCode"]
            if zscode.startswith("N"):
                zscode = "zs"
                    
            get_filepath,status = self.get_scale_rout_files(**info)
            if status == "error":
                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(get_filepath)],
                                       condition="id={0}".format(ID))                        
                self.write_finish_log(output_id+"_check_error")                    
                return    
                
            if not get_filepath:
                log = u"未找到已输出的1:1的锣带，请先输出1:1锣带后，再清除报警状态，让系统拉伸输出！<br>"
                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                       condition="id={0}".format(ID))
                self.write_finish_log(output_id+"_check_error")                    
                return
            
            output_layers = []
            dic_layer_contact_path = {}
            for num, x in enumerate(get_filepath):
                try:                    
                    layer = x.lower().split(jobname.lower() + ".")[1]
                except:
                    layer = os.path.basename(x).lower().split(".")[1]
                    
                output_layers.append(layer)
                # dic_layer_contact_path[layer] = os.path.join(tmp_dir,os.path.basename(x))
                dic_layer_contact_path[x] = layer
                    
            print(get_filepath, output_layers)
            not_exists_layers = []
            for worklayer in output_layers:            
                if not step.isLayer(worklayer):
                    not_exists_layers.append(worklayer)
                    
            if not_exists_layers:                
                log = u"输出层{0} 不存在，请检查tgz资料是否正常！<br>".format(" ".join(not_exists_layers))
                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                       condition="id={0}".format(ID))                        
                self.write_finish_log(output_id+"_check_error")                    
                return
            
            # if info["quadrant"] in [u"一锣", u"半孔锣", u"CCD精锣", u"PTH锣",u"控深铣",]:
            if info["dataName"] == u"产线临时资料":   
                for origin_filepath in get_filepath:
                    rout_layer = dic_layer_contact_path[origin_filepath]                
                    check_exists_layer = ""
                    if info["quadrant"] == u"一锣":
                        check_exists_layer = "rout"
                    if info["quadrant"] == u"半孔锣":
                        check_exists_layer = "half-rout"
                    if info["quadrant"] == u"CCD精锣":
                        check_exists_layer = "ccd-rout"
                    if info["quadrant"] == u"PTH锣":
                        check_exists_layer = "pth-rout"
                    if info["quadrant"] == u"控深铣":
                        check_exists_layer = "rout-cdc;rout-cds"
                    if info["quadrant"] == u"中锣":
                        check_exists_layer = "mid-rout"
                
                    if check_exists_layer:
                        if (rout_layer == check_exists_layer or \
                                (";" in check_exists_layer and rout_layer in check_exists_layer)):
                            break
                else:
                    log = u"检测到输出{0} 层不存在，请手动输出！<br>".format(info["quadrant"])
                    self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                           condition="id={0}".format(ID))                        
                    self.write_finish_log(output_id+"_check_error")
                    return                        
            
            arraylist = []
            
            for origin_filepath in get_filepath:
                
                start_time = self.get_current_format_time()
                
                # output_path = os.path.join(tmp_dir, os.path.basename(origin_filepath))                
                
                rout_layer = dic_layer_contact_path[origin_filepath]
                #for key, value in dic_layer_contact_path.iteritems():
                    #if value == output_path:
                        #rout_layer = key
                        #break
                # if info["quadrant"] in [u"一锣", u"半孔锣", u"CCD精锣", u"PTH锣",u"控深铣",]:
                if info["dataName"] == u"产线临时资料":
                    check_exists_layer = ""
                    if info["quadrant"] == u"一锣":
                        check_exists_layer = "rout"
                    if info["quadrant"] == u"半孔锣":
                        check_exists_layer = "half-rout"
                    if info["quadrant"] == u"CCD精锣":
                        check_exists_layer = "ccd-rout"
                    if info["quadrant"] == u"PTH锣":
                        check_exists_layer = "pth-rout"
                    if info["quadrant"] == u"控深铣":
                        check_exists_layer = "rout-cdc;rout-cds"
                    if info["quadrant"] == u"中锣":
                        check_exists_layer = "mid-rout"                        
                
                    if check_exists_layer:
                        if not (rout_layer == check_exists_layer or \
                                (";" in check_exists_layer and rout_layer in check_exists_layer)):
                            continue
                        
                log = u"开始输出拉伸锣带{0}  {1} <br>".format(rout_layer, start_time)
                self.update_mysql_data([u"Status = '{0}'".format(u"输出中"),
                                        u"OutputStatus = '{0}'".format(u"输出中"),
                                        u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                        condition="id={0}".format(ID)) 
                
                flip.release_flip()

                res = self.compare_rout_layer(worklayer=str(rout_layer),
                                                              stepname=str(stepname),
                                                              jobname=str(job.name),
                                                              filepath=origin_filepath.encode("cp936").replace("\\", "/"),
                                                              step=step)
                if res and u"报内存不足" in res:
                    self.colseJob(jobname)
                    # top.PAUSE("check")
                    job.open(0)
                    step = gClasses.Step(job, stepname)
                    step.open()
                    res = self.compare_rout_layer(worklayer=str(rout_layer),
                                                                  stepname=str(stepname),
                                                                  jobname=str(job.name),
                                                                  filepath=origin_filepath.encode("cp936").replace("\\", "/"),
                                                                  step=step)
                    # top.PAUSE("check1")
                    
                if res == u"set输出不用拉伸":
                    # job.PAUSE("ddd")
                    # if info["quadrant"] in [u"一锣", u"半孔锣", u"CCD精锣", u"PTH锣",u"控深铣",]:
                    if info["dataName"] == u"产线临时资料":   
                        self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{1} {0},请手动输出!<br>')".format(res, rout_layer)],
                                               condition="id={0}".format(ID))                        
                        self.write_finish_log(output_id+"_check_error")  
                    else:
                        self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{1} {0}<br>')".format(res, rout_layer)],
                                               condition="id={0}".format(ID))                        
                        continue
                
                if res:                    
                    self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(res)],
                                           condition="id={0}".format(ID))                        
                    self.write_finish_log(output_id+"_check_error")                    
                    return
                
                res,x_mirror,y_mirror = self.set_output_rout_by_origin_tool_order(str(job.name), str(stepname),str(rout_layer),origin_filepath)
                
                os.environ["ORIGIN_ROUT_T_ORDER"] = "@@".join(res)
                
                if "error" == res:
                    log = u"检测到有相同刀，但程序未能正常区分，请手动输出！<br>"
                    self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                           condition="id={0}".format(ID))                        
                    #self.write_finish_log(output_id+"_check_error")                    
                    #return
                
                if x_mirror is None or y_mirror is None:
                    log = u"获取1:1原稿镜像失败，请手动输出！<br>"
                    self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                           condition="id={0}".format(ID))                        
                    self.write_finish_log(output_id+"_check_error")                    
                    return                    
                    
                res = self.auto_set_rout_step_order(worklayer=str(rout_layer),
                                                    stepname=str(stepname),
                                                    jobname=str(job.name),                                               
                                                    step=step,
                                                    mirror=x_mirror)
                if res:                    
                    if res == "not output":
                        log = u"{0}锣带做在panel当中，无需涨缩输出！<br>".format(rout_layer)
                        self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                               condition="id={0}".format(ID))                      
                        continue
                    else:
                        self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(res)],
                                               condition="id={0}".format(ID))
                        self.write_finish_log(output_id+"_check_error") 
                        return                        
                
                step.VOF()
                # 关闭型号再次打开
                #self.colseJob(jobname)
                #job.open(0)
                #step = gClasses.Step(job, stepname)
                #step.open()
                #step.COM("units,type=mm")
                if "zs.{0}".format(stepname) in job.matrix.getInfo()["gCOLstep_name"]:
                    job.removeStep("zs.{0}".format(stepname))
                
                step.COM("copy_entity,type=step,source_job={0},source_name={1},"
                         "dest_job={0},dest_name=zs.{1},dest_database=".format(job.name, stepname))
                if step.STATUS > 0:
                    log = u"copy zs.panel报内存不足，重新打开型号！<br>"
                    self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                           condition="id={0}".format(ID))
                    
                    self.colseJob(jobname)
                    job.open(0)
                    step = gClasses.Step(job, stepname)
                    step.open()
                    step.COM("units,type=mm")                    
                    step.COM("copy_entity,type=step,source_job={0},source_name={1},"
                             "dest_job={0},dest_name=zs.{1},dest_database=".format(job.name, stepname))
                    if step.STATUS > 0:
                        log = u"重新打开料号copy zs.panel报内存不足，请手动输出！<br>"
                        self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                               condition="id={0}".format(ID))
                        return
                    
                flip.release_flip()
                if step.STATUS > 0:
                    log = u"阴阳拼板更新失败，请手动输出！<br>"
                    self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                           condition="id={0}".format(ID))                                           
                    return         
                step.VON()                
                
                # 当一个层对应多个锣带拉伸时 比如有镜像跟不镜像 命名需处理下
                if jobname + "." + rout_layer <> os.path.basename(origin_filepath).lower():
                    zscode = "xxx" + zscode
                    
                output_filepath = os.path.join(tmp_dir,"{2}-{0}.{1}".format(jobname, rout_layer, zscode))   
                os.environ["STEP"] = stepname               
                os.environ["ORIGIN_ROUT_FILE_PATH"] = origin_filepath.encode("cp936")
                os.environ["OUTPUT_ID"] = output_id
                os.environ["OUTPUT_ROUT_FILE_PATH"] = output_filepath
                if "gui_run" in sys.argv:                    
                    #thrd = threading.Thread(target=self.auto_click_rout_output_table_popup, args=(zscode, jobname, rout_layer))
                    #thrd.start()                    
                    os.system(r'Z:\incam\Path\Perl\bin\perl Z:\incam\genesis\sys\scripts\hdi-scr\Output\output_rout\rout_output_auto_gui_run.pl {0} "{1}" {2} {3} {4} {5} {6} {7}'.format(jobname, zscode, output_id, scale_x, scale_y, rout_layer, x_mirror, y_mirror))
                else:
                    os.system(r'Z:\incam\Path\Perl\bin\perl Z:\incam\genesis\sys\scripts\hdi-scr\Output\output_rout\rout_output_auto.pl {0} "{1}" {2} {3} {4} {5} {6} {7}'.format(jobname, zscode, output_id, scale_x, scale_y, rout_layer, x_mirror, y_mirror))
                if os.path.exists("{0}/success_{1}.log".format(tmp_path, output_id)):
                    pass
                else:
                    return
                
                if os.path.exists("{0}/success_{1}.log".format(tmp_path, output_id)):
                    os.unlink("{0}/success_{1}.log".format(tmp_path, output_id))
                # 关闭型号再次打开
                #self.colseJob(jobname)
                #job.open(0)
                #step = gClasses.Step(job, stepname)
                #step.open()
                #step.COM("units,type=mm")
                step.COM("config_edit,name=iol_fix_ill_polygon,value=yes,mode=user")            
                
                # for worklayer in output_layers:
                start_time = self.get_current_format_time()
                log = u"开始回读比对{0}  {1} <br>".format(rout_layer, start_time)
                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                       condition="id={0}".format(ID))                  
                    
                self.write_calc_time_log(ID)                
                
                
                print("-------->", output_filepath)
                warning_log = ""
                if os.path.exists(output_filepath):
                    
                    res = self.check_output_order(output_filepath, origin_filepath, zscode)
                    if res:
                        if u"请尝试清除报警状态重新输出" in res and \
                           getattr(self, "reoutput_rout", "no") <> "yes":                                
                            self.reoutput_rout = "yes"
                            self.output_scale_rout_file(*args)                        
                            return
                        
                        warning_log = rout_layer + res                            
                    else:
                        warning_log = self.compare_rout_layer(worklayer=str(rout_layer),
                                                              stepname=str("zs."+stepname),
                                                              jobname=str(job.name),
                                                              filepath=output_filepath.encode("cp936").replace("\\", "/"),
                                                              step=step)
                    if "xxx" in zscode:
                        new_output_filepath = os.path.join(tmp_dir,
                                                           "{0}-{1}".format(info["ZsCode"],
                                                            os.path.basename(origin_filepath)))
                        os.rename(output_filepath, new_output_filepath)
                else:
                    warning_log = u"拉伸锣带{0}输出异常，未找到输出的锣带资料，请手动输出！<br>".format(rout_layer)
                
                if warning_log:
                    arraylist.append(warning_log) 
                
            if arraylist:
                self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常"),
                                        u"Status = '{0}'".format(u"输出中"),
                                        u"AlarmLog = concat(AlarmLog,'{0}')".format("".join(arraylist))],
                                       condition="id={0}".format(ID))
                self.write_finish_log(output_id+"_check_error")
                return

        self.write_finish_log(output_id)
        
    def kill_rout_output_error_stop(self, *args):
        """杀死20分钟还未输出完的锣带genesis输出界面"""
        
        app = Application(backend="win32").connect(title_re=".*Toolkit.*", timeout=10)       
        while not app.is_process_running():
            # print("app running", app.is_process_running())                     
            app = Application(backend="win32").connect(title_re=".*Toolkit.*")
        
        try:            
            dlg = app.window(title="Dialog Box")
            while dlg.exists(): 
                dlg.set_focus()
                time.sleep(1)
                send_keys("{VK_RETURN}")
                dlg = app.window(title="Dialog Box")
        except Exception as e:
            print(e)
            if "There is no active desktop required for moving mouse cursor" in str(e):
                send_talk.send_work_notice(access_token, '84310', '', u"远程桌面被锁定{0}".format(random.random()), u"远程桌面异常")            
        
        os.system("rm -rf c:/tmp/check_app_pause.log")
        
        num = 1
        while True:
            time.sleep(1)
            num += 1
            if os.path.exists("c:/tmp/exit_app.log"):
                os.unlink("c:/tmp/exit_app.log")
                return
            
            if os.path.exists("c:/tmp/check_app_pause.log"):                
                try:                    
                    app = Application(backend="win32").connect(title_re=".*Toolkit.*", timeout=10)
                    while not app.is_process_running():
                        # print("app running", app.is_process_running())
                        app = Application(backend="win32").connect(title_re=".*Toolkit.*")
                        
                    dlg1 = app.window(title="NC Table popup")
                    dlg2 = app.window(title="Dialog Box")
                    # print("NC Table popup-->exists", dlg1.exists())
                    if dlg1.exists() and dlg2.exists():                           
                        self.auto_click_rout_output_table_popup(*args)
                except Exception as e:
                    print(e)
            
            if num > 1200:
                break
            
        if "192.168.19.243" not in localip[2]:
            self.colseJob(job.name)
            pid = os.environ.get("GENESIS_PID", None)
            if pid:
                psutil.Process(int(pid)).kill()            
    
    def auto_click_rout_output_table_popup(self, *args):
        """自动点击锣带输出排序"""
        # zscode, jobname, rout_layer = args
        # name = "{2}-{0}-{1}".format(jobname, rout_layer, zscode)
        name = job.name
        if os.environ.get("OUTPUT_ROUT_FILE_PATH"):
            name = os.path.basename(os.environ["OUTPUT_ROUT_FILE_PATH"])
            
        try:
            app = Application(backend="win32").connect(title_re=".*Toolkit.*", timeout=10)
            while not app.is_process_running():
                # print("app running", app.is_process_running())
                app = Application(backend="win32").connect(title_re=".*Toolkit.*")
                
            dlg = app.window(title="NC Table popup")
             
            time.sleep(5)
            rect = dlg.rectangle()
            # print(rect)
            # 计算出相对于屏幕的坐标 sort
            x = rect.right - 40
            y = rect.bottom - 55
            
            dlg.set_focus()
            time.sleep(1)
            mouse.click(coords=(x, y))
            time.sleep(1)
            mouse.click(coords=(x, y))
            
            # 计算出相对于屏幕的坐标 apply
            x = rect.left + 100
            y = rect.bottom - 25
            
            # 在窗口的相对位置上点击
            dlg.set_focus()
            time.sleep(1)
            mouse.click(coords=(x, y))            
            time.sleep(1)
            mouse.click(coords=(x, y))    
            
            # dlg.set_focus()
            # dlg.maximize()
            # time.sleep(1)
            # 对整个窗体进行截图
            # screenshot = dlg.capture_as_image()
            
            # 将截图保存到文件
            # screenshot.save("d:/rout_order_picture/{0}.png".format(name))
            screen_capture("d:/rout_order_picture/{0}.png".format(name))
            time.sleep(1)
            # dlg.restore()
            
            #time.sleep(2)
            #dlg = app.window(title="NC Table popup")
            #rect = dlg.rectangle()
            ## 计算出相对于屏幕的坐标 close
            #x = rect.right - 100
            #y = rect.bottom - 25
            
            ## 在窗口的相对位置上点击
            #dlg.set_focus()
            #time.sleep(1)
            #mouse.click(coords=(x, y))            
            #time.sleep(1)
            
            dlg = app.window(title="Dialog Box")
            while dlg.exists(): 
                dlg.set_focus()
                time.sleep(1)
                send_keys("{VK_RETURN}")
                dlg = app.window(title="Dialog Box")
            
            os.system("rm -rf c:/tmp/check_app_pause.log")
        except Exception as e:
            print(e)
            if "192.168.19.243" not in localip[2]:
                self.colseJob(job.name)
                pid = os.environ.get("GENESIS_PID", None)
                if pid:
                    psutil.Process(int(pid)).kill()                
                
    def get_scale_drill_files(self, *args, **kwargs):
        """获取网络上1:1的钻带"""
        
        jobname = kwargs["Job"].lower()
        drill_name = kwargs["dataName"]
        drill_layers = kwargs["OutLayer"]
        drill_type = kwargs["data_type"]
        dirpath = ur"\\192.168.2.174\GCfiles\Program\工程辅助资料\{0}系列\{1}".format(jobname[1:4], jobname)
        if not os.path.exists(dirpath):
            return u"1:1钻带路径不存在：{0}".format(dirpath), "error"
        
        # print([drill_name])
        filepath = []
        if drill_name == u"通孔": 
            for name in os.listdir(dirpath):
                # print(name.lower(), "{0}.drl$|{0}.cdc$|{0}.cds$|{0}.bdc$|{0}.bds$".format(jobname))
                if re.match("{0}.drl$|{0}.cdc$|{0}.cds$|{0}.tk.ykj$|{0}.bdc$|"
                "{0}.bds$|{0}.lp$".format(jobname), name.lower()):
                    if "szsk" in name.lower():
                        if "...dq" not in name.lower():
                            filepath.append(os.path.join(dirpath, name))
                    else:
                        filepath.append(os.path.join(dirpath, name))
                    
                    if "tk.ykj" not in name.lower() and "szsk" not in name.lower() and ".lp" not in name.lower():
                        inn_path = os.path.join(dirpath, name) + ".inn"
                        if not os.path.exists(inn_path):
                            inn_path = os.path.join(dirpath, jobname+".inn")
                            
                        filepath.append(inn_path)
                        
        if drill_name == u"临时二钻": 
            for name in os.listdir(dirpath):
                
                if kwargs.get("2nd_erp_drill_layer"):
                    for erp_drill in kwargs.get("2nd_erp_drill_layer"):
                        if str(jobname+"."+erp_drill).lower() == name.lower() and "2nd" in name.lower():
                            filepath.append(os.path.join(dirpath, name))
                    continue
                
                if "2nd" in name.lower() or "3nd" in name.lower():
                    filepath.append(os.path.join(dirpath, name))                    
                    #if ".ykj" not in name.lower():
                        #inn_path = os.path.join(dirpath, name) + ".inn"
                        #filepath.append(inn_path)                         
        
        if drill_name in [u"盲埋孔", "Drill"]:
            if lay_num > 2:                
                a, b = drill_layers.split(";")
                for name in os.listdir(dirpath):                
                    if re.match("{0}.b{1}-{2}$|{0}.m{1}-{2}$|{0}.lr{1}-{2}$|{0}.lr{1}{2}$".format(jobname, a[1:], b[1:]), name.lower()):                    
                        filepath.append(os.path.join(dirpath, name))
                        
                        if ".lp" not in name.lower() and ".lr" not in name.lower():                            
                            filepath.append(os.path.join(dirpath, name) + ".inn")
                            
                        if drill_name == "Drill":
                            if "tk.ykj" not in name.lower() and "szsk" not in name.lower() \
                               and ".lp" not in name.lower() and ".lr" not in name.lower():  
                                filepath.append(os.path.join(dirpath, name) + ".dbk")
            else:
                # 双面板
                if drill_name == "Drill":
                    for name in os.listdir(dirpath):
                        # print(name.lower(), "{0}.drl$|{0}.cdc$|{0}.cds$".format(jobname))
                        if re.match("{0}.drl$|{0}.cdc$|{0}.cds$|{0}.tk.ykj$|{0}.bdc$|"
                        "{0}.bds$|{0}.lp$".format(jobname), name.lower()):
                            if "szsk" in name.lower():
                                if "...dq" not in name.lower():
                                    filepath.append(os.path.join(dirpath, name))
                            else:
                                filepath.append(os.path.join(dirpath, name))
                            
                            if "tk.ykj" not in name.lower() and "szsk" not in name.lower() and ".lp" not in name.lower():                        
                                filepath.append(os.path.join(dirpath, name) + ".inn") 
                            
                                filepath.append(os.path.join(dirpath, jobname) + ".dbk")
                    
        if drill_name in [u"树脂铝片", u"塞孔铝片"]:
            if lay_num > 2:        
                a, b = drill_layers.split(";")
                for name in os.listdir(dirpath):
                    if kwargs.get("sz_erp_drill_layer"):
                        for erp_drill in kwargs.get("sz_erp_drill_layer"):
                            if str(jobname+"."+erp_drill).lower() == name.lower() or \
                               str(jobname+"."+erp_drill+".lp").lower() == name.lower():
                                filepath.append(os.path.join(dirpath, name))
                        continue
                                
                    if re.match("{0}.sz{1}-{2}.lp$|{0}.sz{1}-{2}-[cs].lp$|"
                    "{0}.sz{1}-{2}-\d+.lp$|{0}.szsk-({1})?({2})?.lp".format(jobname, a[1:], b[1:]), name.lower()):                    
                        filepath.append(os.path.join(dirpath, name))
                    if drill_layers.startswith("L1;") and \
                       re.match("{0}.sz.lp$|{0}.sz-[cs].lp$|{0}.szsk2-[12].lp|{0}.szsk-[cs].lp".format(jobname), name.lower()):
                        filepath.append(os.path.join(dirpath, name)) 
            else:
                for name in os.listdir(dirpath):
                    
                    if kwargs.get("sz_erp_drill_layer"):
                        for erp_drill in kwargs.get("sz_erp_drill_layer"):
                            if str(jobname+"."+erp_drill).lower() == name.lower() or \
                               str(jobname+"."+erp_drill+".lp").lower() == name.lower():
                                filepath.append(os.path.join(dirpath, name))
                        continue
                    
                    if re.match("{0}.szsk[.-].+|{0}.sz.lp$|{0}.szsk2-[12].lp".format(jobname), name.lower()):
                        filepath.append(os.path.join(dirpath, name))                    
            
        return filepath, "success"
    
    def modify_xy(self, modx):
        tmpmodx = str(abs(modx)).rjust(6,"0").rstrip("0")
        if modx < 0:
            tmpmodx = "-"+tmpmodx
        if tmpmodx == "":
            tmpmodx = "0"
        return tmpmodx
    
    def scale_list(self, lineList, scale_x, scale_y,
                   anchor_x, anchor_y, zscode,
                   worklayer, readd_text_status_log):
        checkerrs = 0
        ftmpxys = [[],[]]
        allmodifys = []
        m97zzz = 0
        m30indexs = 0
        for fff in lineList:
            m97zzz += 1
            if fff.find("M01") == 0:
                checkerrs += 1
                print "Err",fff
                break
            #elif fff.find("M9") == 0 and fff.find("W") > 0 and fff.find("L") > 0:
                #checkerrs += 1
                #print "Err",fff
                #break
            elif fff.find("X") == 0 or fff.find("Y") == 0:
                if fff.find("^") > 0 or fff.find(".") > 0:
                    checkerrs += 1
                    print "Err",fff
                    break
                sssfff = fff.split("G84")[0].strip().replace("G85","   ").replace("X-","  ").replace("Y-","  ").replace("X+","  ").replace("Y+","  ").replace("X"," ").replace("Y"," ")
                ssplit = sssfff.split()
                ssplits = []
                for z in ssplit:
                    if len(z) <= 6:
                        try:
                            zf = float(z.ljust(6,"0")) / (10 ** 3)
                        except:
                            zf = 2000.0
                    else:
                        zf = 2000.0
                    if zf > 999.999:
                        checkerrs += 1
                        print m97zzz,z,zf,"err"
                    ssplits.append(zf)
                if checkerrs:
                    print "Err",fff
                    break
                zstr = ""
                for z in range(len(sssfff)):
                    if sssfff[z] == " ":
                        zstr += fff[z]
                    else:
                        zstr += "^"
                zstr += fff[len(sssfff):]
                zsplit = []
                for z in zstr.split("^"):
                    if z != "":
                        zsplit.append(z)
                modifyxystr = ""
                for z in range(len(ssplits)):
                    zzzxy = ssplits[z]
                    if zsplit[z].find("-") > 0:
                        zzzxy = 0 - ssplits[z]
                    if zsplit[z].find("X") >= 0:
                        ftmpxys[0].append(zzzxy)                        
                        # modx = int(round(zzzxy * (10000 + scale_x) / 10.0 - anchor_x))
                        modx = int((zzzxy + (zzzxy-anchor_x)*(scale_x-1)) *1000)
                    else:
                        ftmpxys[1].append(zzzxy)
                        # modx = int(round(zzzxy * (10000 + scale_y) / 10.0 - anchor_y))
                        modx = int((zzzxy + (zzzxy-anchor_y)*(scale_y-1)) *1000)

                    tmpmodx = self.modify_xy(modx)
                    modifyxystr += zsplit[z].replace("-","").replace("+","")
                    modifyxystr += tmpmodx
                modifyxystr += string.join(zsplit[z+1:])
                allmodifys.append(modifyxystr)
            else:
                add_text = False
                if ("M98" in fff or "M97" in fff) and \
                   ".lp" not in worklayer and \
                   ".sz" not in worklayer:
                    m97_m98, text = fff.split(",")
                    if "-" in text:
                        a, b = text.strip().split("-")[:2]
                        if (a.lower() in job.name or a.lower() in "wl" + job.name) and \
                           b.lower() in job.name:
                            scale_text = ""
                            #if scale_y != 1:
                                #scale_text += " L{0}".format(scale_y)
                            #if scale_x != 1:
                                #scale_text += " W{0}".format(scale_x) 
                            line = "{0},{1}{2}{3}\n".format(m97_m98, zscode.upper(), text.strip(), scale_text)
                            if readd_text_status_log == "two_text":
                                # 系数跟字唛分开添加的情况 20240112 by lyh
                                allmodifys.append(fff)
                            else:
                                allmodifys.append(line)
                            add_text = True
                        else:                            
                            print(text, " not in jobname:", job.name)
                            checkerrs += 1
                            
                if not add_text:                    
                    allmodifys.append(fff)
                    
                if fff.find("M30") == 0:
                    m30indexs = m97zzz - 1
        if m30indexs == 0:
            m30indexs = m97zzz
        if checkerrs > 0:
            return (checkerrs,allmodifys)
        if ftmpxys[0] == [] or ftmpxys[1] == []:
            checkerrs += 1
            return (checkerrs,allmodifys)
        if len(allmodifys) != len(lineList):
            checkerrs += 1
            return (checkerrs,allmodifys)
        minmaxx = abs(min(ftmpxys[0])-max(ftmpxys[0]))
        minmaxy = abs(min(ftmpxys[1])-max(ftmpxys[1]))
        print ["sise:",minmaxx,minmaxy]
        if minmaxx > 999.9 or minmaxy > 999.9:
            checkerrs += 1
            return (checkerrs,allmodifys)
        
        return (checkerrs,allmodifys)
    
    def check_text_is_touch_other_features(self, step, drill_layer,
                                           scale_x, scale_y, zscode,
                                           checklayer_list, change_text=True,
                                           is_lp=False):
        """检测加涨缩系数后的字唛孔是否会更其他物件接触"""
        step = gClasses.Step(job, step.name)
        step.open()
        step.COM("units,type=mm")
        
        step.clearAll()
        for reflayer in checklayer_list:
            step.affect(reflayer)
        step.resetFilter()
        step.setAttrFilter(".area_name,text=expose_area")
        step.selectAll()
        if step.featureSelected():
            step.selectDelete()
            
        step.clearAll()
        step.affect(drill_layer)
        step.copyLayer(job.name, step.name, drill_layer, drill_layer+"_change_text_bak")
        step.resetFilter()
        layer_cmd = gClasses.Layer(step, drill_layer)
        text_feat = layer_cmd.featout_dic_Index(options="feat_index", units="mm")["text"]
        modify_text_xy = []
        origin_text_xy = []
        if text_feat:
            find_text_obj = [obj for obj in text_feat if "zuanzi" in obj.text or "8888" in obj.text]
            if not find_text_obj and (".lp" in drill_layer or drill_layer == "lp"):
                find_text_obj = [obj for obj in text_feat if "$$layer" in obj.text.lower() ]
                
            if find_text_obj:
                for obj in find_text_obj:
                    step.clearAll()
                    step.affect(drill_layer)                    
                    step.selectNone()
                    step.selectFeatureIndex(drill_layer, obj.feat_index)
                    if step.featureSelected():
                        xmin, ymin, xmax, ymax = get_layer_selected_limits(step, drill_layer)
                        origin_text_xy.append([xmin, ymin, xmax, ymax])
                        
                        # scale_text = " L1.000000 W1.000000"
                        # http://192.168.2.120:82/zentao/story-view-6897.html 取消加涨缩系数 20241210 by lyh
                        scale_text = ""
                        if is_lp:                            
                            if scale_y != 1:
                                scale_text += " L{0}".format(scale_y)
                            if scale_x != 1:
                                scale_text += " W{0}".format(scale_x)
                        if change_text:
                            text = "{0} {1}{2}\n".format(zscode.upper(), obj.text.replace("$$", "$#").replace("'", ""), scale_text)
                            step.COM("sel_change_txt,text={0},x_size=-1,y_size=-1,w_factor=-1,\
                            polarity=no_change,mirror=no_change,fontname=".format(text))
                        else:
                            text = "{0}\n".format(obj.text.replace("$$", "$#").replace("'", ""))
                            step.COM("sel_change_txt,text={0},x_size=-1,y_size=-1,w_factor=-1,\
                            polarity=no_change,mirror=no_change,fontname=".format(text))
                            
                        step.selectFeatureIndex(drill_layer, obj.feat_index)
                        if step.featureSelected():
                            xmin, ymin, xmax, ymax = get_layer_selected_limits(step, drill_layer)
                            modify_text_xy.append([xmin, ymin, xmax, ymax])
                        
                    step.selectFeatureIndex(drill_layer, obj.feat_index)
                    if step.featureSelected():
                        step.removeLayer("text_tmp")
                        step.copySel("text_tmp")
                        step.clearAll()
                        step.affect("text_tmp")
                        step.resetFilter()

                        step.COM("sel_break")
                        # step.COM("sel_resize,size=500")
                        
                        for reflayer in checklayer_list:
                            if drill_layer == reflayer:
                                continue
                            if not reflayer:
                                continue
                            if reflayer == "fill":
                                step.refSelectFilter(reflayer)
                            else:
                                if drill_layer in ["drl", "cds", "cdc"]:
                                    step.refSelectFilter(reflayer, f_types="pad\;text",
                                                         exclude_syms="rect30000x7000;rect30500x7500;eagle-mark-dot;et_rj_pad*;gold_sq")
                                else:
                                    step.refSelectFilter(reflayer, f_types="pad\;text",
                                                         exclude_syms="eagle-mark-dot;et_rj_pad*")
                            if step.featureSelected():
                                if step.isLayer(drill_layer+"_change_text_bak"):
                                    step.copyLayer(job.name, step.name, drill_layer+"_change_text_bak", drill_layer)
                                return 1,modify_text_xy, origin_text_xy
                            
        if step.isLayer(drill_layer+"_change_text_bak"):
            step.copyLayer(job.name, step.name, drill_layer+"_change_text_bak", drill_layer)
            
        return 0,modify_text_xy,origin_text_xy                        
    
    def calc_drill_text_coordinate_info(self, step, drill_layer, scale_x, scale_y, zscode, **info):
        """自动计算钻字的位置来重新修改 钻字坐标"""
        
        f_xmin, f_ymin, f_xmax, f_ymax = get_profile_limits(step)
        rect= get_sr_area_for_step_include(step.name, include_sr_step=["edit", "set", "icg", "zk"])
        sr_xmin = min([min(x1, x2) for x1, y1, x2, y2 in rect])    
        sr_ymin = min([min(y1, y2) for x1, y1, x2, y2 in rect])   
        sr_xmax = max([max(x1, x2) for x1, y1, x2, y2 in rect])    
        sr_ymax = max([max(y1, y2) for x1, y1, x2, y2 in rect])
        
        # 获取脚线区域 判断有小sr的区域
        step.COM("units,type=mm")
        if signalLayers:            
            layer_cmd = gClasses.Layer(step, signalLayers[0])
            feat_out = layer_cmd.featCurrent_LayerOut(units="mm")["pads"]
            jx_symbol_obj = [obj for obj in feat_out if obj.symbol in ("sh-con2", "sh-con")]
            all_jx_x = [obj.x for obj in jx_symbol_obj]
            all_jx_y = [obj.y for obj in jx_symbol_obj]
            if all_jx_x and all_jx_y:           
                min_jx_x = min(all_jx_x)
                max_jx_x = max(all_jx_x)
                min_jx_y = min(all_jx_y)
                max_jx_y = max(all_jx_y)
                
                STR = '-t step -e %s/%s -d REPEAT,units=mm' % (job.name, step.name)
                gREPEAT_info = step.DO_INFO(STR)
                gREPEATstep = gREPEAT_info['gREPEATstep']
                gREPEATxmax = gREPEAT_info['gREPEATxmax']
                gREPEATymax = gREPEAT_info['gREPEATymax']
                gREPEATxmin = gREPEAT_info['gREPEATxmin']
                gREPEATymin = gREPEAT_info['gREPEATymin']
                
                set_rect_area = []
                for i, name in enumerate(gREPEATstep): 
                    if gREPEATxmin[i] > min_jx_x and gREPEATymin[i] > min_jx_y and \
                       gREPEATxmax[i] < max_jx_x and gREPEATymax[i] < max_jx_y and \
                       ("set" in name or "edit" in name or "icg" in name):
                        set_rect_area.append(
                            [gREPEATxmin[i], gREPEATymin[i], gREPEATxmax[i], gREPEATymax[i]])
                
                try:                
                    sr_xmin = min([min(x1, x2) for x1, y1, x2, y2 in set_rect_area])    
                    sr_ymin = min([min(y1, y2) for x1, y1, x2, y2 in set_rect_area])   
                    sr_xmax = max([max(x1, x2) for x1, y1, x2, y2 in set_rect_area])    
                    sr_ymax = max([max(y1, y2) for x1, y1, x2, y2 in set_rect_area])
                except :
                    pass
            
        try:        
            array_mrp_info = get_inplan_mrp_info(job.name, "1=1")  
            
            dic_inner_zu = {}
            dic_sec_zu = {}
            dic_outer_zu = {}
            out_lb_x = 0
            out_lb_y = 0    
            for dic_info in array_mrp_info:
                top_layer = dic_info["FROMLAY"]
                bot_layer = dic_info["TOLAY"]
                process_num = dic_info["PROCESS_NUM"]
                mrp_name = dic_info["MRPNAME"]
                pnl_routx = round(dic_info["PNLROUTX"] * 25.4, 3)
                pnl_routy = round(dic_info["PNLROUTY"] * 25.4, 3)
                
                #只取当次锣边的数据
                if not (top_layer.upper().strip() in info["OutLayer"] and \
                   bot_layer.upper().strip() in info["OutLayer"]):
                    continue
                
                out_lb_x = (f_xmax - pnl_routx) * 0.5
                out_lb_y = (f_ymax - pnl_routy) * 0.5                
                
                if process_num == 1:
                    if not dic_inner_zu.has_key(process_num):
                        dic_inner_zu[process_num] = []            
                    dic_inner_zu[process_num].append([mrp_name, top_layer, bot_layer, pnl_routx, pnl_routy, 0])
                else:
                    if "-" in mrp_name:
                        if not dic_sec_zu.has_key(process_num):
                            dic_sec_zu[process_num] = []                
                        dic_sec_zu[process_num].append([mrp_name, top_layer, bot_layer, pnl_routx, pnl_routy, 0])
                    else:
                        if not dic_outer_zu.has_key(process_num):
                            dic_outer_zu[process_num] = []                    
                        dic_outer_zu[process_num].append([mrp_name, top_layer, bot_layer, pnl_routx, pnl_routy, 0])
        except:
            out_lb_x = 2
            out_lb_y = 2
            
        if lay_num <= 2:
            out_lb_x = 2
            out_lb_y = 2             
        
        dic_symbol_info = {}
        if sys.platform == "win32":            
            symbol_info_path = "{0}/fw/lib/symbols/symbol_info.json".format(os.environ["GENESIS_DIR"])
        else:
            symbol_info_path = "/incam/server/site_data/library/symbol_info.json"
        if not os.path.exists(symbol_info_path):
            symbol_info_path = os.path.join(os.path.dirname(sys.argv[0]), "symbol_info.json")
            
        if os.path.exists(symbol_info_path):
            with open(symbol_info_path) as file_obj:
                dic_symbol_info = json.load(file_obj)
        
        drill_info_path = "d:/drill_info/drill_info.json"
        drill_coordinate_info = {}
        if os.path.exists(drill_info_path):
            with open(drill_info_path) as file_obj:
                drill_coordinate_info = json.load(file_obj)
                
        if not drill_coordinate_info.get(job.name):
            drill_coordinate_info[job.name] = {}
            
        if not drill_coordinate_info[job.name].get(drill_layer):
            drill_coordinate_info[job.name][drill_layer] = []    
         
        drill_throu_layers = get_drill_start_end_layers(matrixInfo, drill_layer)
        if "lr" in drill_layer:
            drill_throu_layers = ["l{0}".format(drill_layer.split("-")[0][2:]),
                                  "l{0}".format(drill_layer.split("-")[1])]
        
        inn_layers = [lay for i, lay in enumerate(matrixInfo["gROWname"])
                      if matrixInfo["gROWcontext"][i] == "board"
                      and matrixInfo["gROWlayer_type"][i] == "drill"
                      and (re.match("^inn.*", lay))]           
        checklayer_list = [x for x in drill_throu_layers] + tongkongDrillLayer + \
            mai_drill_layers + mai_man_drill_layers + inn_layers + \
            laser_drill_layers
        
        if step.isLayer("l2") and drill_layer in ["drl", "cdc", "cds"]:
            checklayer_list.append("l2")
            #step.clearAll()
            #step.affect("l2")
            #step.resetFilter()
            #step.selectSymbol("eagle-mark-dot", 1, 1)
            #if step.featureSelected():
                #step.selectDelete()
            #step.clearAll()
        
        if step.isLayer("fill"):
            checklayer_list.append("fill")
            
        # 中间偏左区域尽量不要添加
        x1 = f_xmax * 0.5 - 70
        y1 = out_lb_y
        x2 = f_xmax * 0.5
        y2 = out_lb_y + 6.5
        step.clearAll()
        step.affect("fill")
        avoid_symbol = "rect{0}x{1}".format((x2-x1) *1000, (y2-y1) *1000)
        step.addPad((x1+x2) *0.5, (y1+y2) *0.5, avoid_symbol)
        step.addPad((x1+x2) *0.5, f_ymax - (y1+y2) *0.5, avoid_symbol)
        step.clearAll()            
        
        checklayer_list = [x for x in checklayer_list if x.strip()]
        
        #需避开其他钻带的字唛位置 20240110 by lyh
        if drill_coordinate_info[job.name]:
            if info["dataName"] == u"临时二钻":
                for layer in drill_coordinate_info[job.name].keys():
                    if drill_coordinate_info[job.name][layer] and layer in ["drl", "cdc", "cds"]:
                        step.clearAll()
                        step.affect("fill")
                        for symbol, x, y in drill_coordinate_info[job.name][layer]:
                            step.addPad(x, y, symbol)
            else:
                for layer in drill_coordinate_info[job.name].keys():
                    if drill_coordinate_info[job.name][layer] and layer != drill_layer and layer != "tk.ykj":
                        step.clearAll()
                        step.affect("fill")
                        for symbol, x, y in drill_coordinate_info[job.name][layer]:
                            step.addPad(x, y, symbol)
            
            # step = gClasses.Step(job, step.name)
            #之前已添加的位置在检查位置是否正常 若正常即不在重复计算 20240201 by lyh
            for layer in drill_coordinate_info[job.name].keys():
                if drill_coordinate_info[job.name][layer] and layer == drill_layer:
                    step.removeLayer("text_tmp")
                    step.createLayer("text_tmp")
                    recalc_coordinate = False
                    for symbol, add_x, add_y in drill_coordinate_info[job.name][layer]:
                        if symbol not in ["rect3800x42000", "rect3800x23000"]:    
                            step.clearAll()
                            step.affect("text_tmp")
                            step.addPad(add_x, add_y, symbol)
                            step.resetFilter()
                            for reflayer in checklayer_list:
                                if drill_layer == reflayer:
                                    continue
                                if not reflayer:
                                    continue
                                if reflayer == "fill":
                                    step.refSelectFilter(reflayer)
                                else:
                                    step.refSelectFilter(reflayer, f_types="pad\;text")
                                if step.featureSelected():
                                    recalc_coordinate = True
                                    break
                                
                    if not recalc_coordinate:
                        for symbol,add_x, add_y in drill_coordinate_info[job.name][layer]:   
                            if symbol == "rect42000x3800":
                                return add_x - 20.5 + 0.23, add_y - 1.9 + 0.23, "one_text"
                            elif symbol == "rect12000x3800":
                                return add_x - 5.5 + 0.23, add_y - 1.9 + 0.23, "two_text"
                            else:
                                return 0, 0, "not_modify"                            
        
        step.removeLayer("text_tmp")
        res,avoid_text_area,origin_text_area = self.check_text_is_touch_other_features(step, drill_layer, scale_x,
                                                                                       scale_y, zscode, checklayer_list)
        
        if drill_layer == "tk.ykj" or (info["dataName"] == u"临时二钻" and ".ykj" in drill_layer):
            if drill_layer == "tk.ykj":                
                drl_list = ["drl", "cdc", "cds"]
            else:
                drl_list = [drill_layer.replace(".ykj", "")]
            
            for name in drl_list:
                if drill_coordinate_info[job.name].get(name):
                    for symbol, add_x, add_y in drill_coordinate_info[job.name][name]:
                        drill_coordinate_info[job.name][drill_layer] = drill_coordinate_info[job.name][name]
                        with open(drill_info_path, 'w') as file_obj:
                            json.dump(drill_coordinate_info, file_obj)                          
                        if symbol == "rect42000x3800":
                            return add_x - 20.5 + 0.23, add_y - 1.9 + 0.23, "one_text"
                        elif symbol == "rect12000x3800":
                            return add_x - 5.5 + 0.23, add_y - 1.9 + 0.23, "two_text"
                        else:
                            return 0, 0, "not_modify"
                        
        if not res:
            
            if avoid_text_area:
                for xmin, ymin, xmax, ymax in avoid_text_area:
                    symbol = "rect{0}x{1}".format((xmax-xmin) *1000, (ymax-ymin) *1000)
                    text_x = (xmin + xmax) * 0.5
                    text_y = (ymin + ymax) * 0.5
                    drill_coordinate_info[job.name][drill_layer] = [(symbol, text_x, text_y)]
                    
                with open(drill_info_path, 'w') as file_obj:
                    json.dump(drill_coordinate_info, file_obj)
                
            return 0, 0, "not_modify"                
       
        add_x = sr_xmax *0.3
        add_y = f_ymin + 5
        move_model_fx = "X"
        angle = 0        
        area_x = [sr_xmin + 5, sr_xmax - 5, 1]
        area_y = [sr_ymin - 4, f_ymin + out_lb_y + 1, -0.25]
        
        symbolname = "rect42000x3800"
        worklayer = "drill_text_tmp"        

        step.clearAll()
        if not step.isLayer(worklayer):
            step.createLayer(worklayer)
            
            #step.affect(worklayer)
            #step.addRectangle(area_x[0], area_y[0], area_x[1], area_y[1])
            #step.PAUSE("1111")
        exclude_symbols = ["et_rj_pad", "et_rj_pad_p","et_rj_pad_n","chris-rjpad"]
        if drill_layer in ["drl", "cdc", "cds"]:
            exclude_symbols = ["rect30000x7000", "rect30500x7500", "et_rj_pad", "et_rj_pad_p","et_rj_pad_n", "chris-rjpad"]
            
        msg = u"计算坐标位置失败，需人工手动输出！".encode("cp936")
        result = auto_add_features_in_panel_edge_new(step, add_x, add_y, worklayer,
                                                     symbolname, checklayer_list,
                                                     msg, 1, 0,  angle, 
                                                     area_x=area_x, area_y=area_y,
                                                     move_length=1, 
                                                     move_model_fx=move_model_fx,
                                                     to_sr_area=1, max_min_area_method="yes",
                                                     dic_all_symbol_info=dic_symbol_info,
                                                     manual_add="no", to_feat_size=0.5,
                                                     exclude_symbols=exclude_symbols)
        if not result:
            area_y = [sr_ymax + 4, f_ymax - out_lb_y - 1, 0.25]
            result = auto_add_features_in_panel_edge_new(step, add_x, add_y, worklayer,
                                                         symbolname, checklayer_list,
                                                         msg, 1, 0,  angle,
                                                         area_x=area_x, area_y=area_y,
                                                         move_length=1,
                                                         move_model_fx=move_model_fx,
                                                         to_sr_area=1, max_min_area_method="yes",
                                                         dic_all_symbol_info=dic_symbol_info,
                                                         manual_add="no", to_feat_size=0.5,
                                                         exclude_symbols=exclude_symbols)            
            
            
        if result:
            add_x, add_y, angle, _ = result            
            
            drill_coordinate_info[job.name][drill_layer] = [(symbolname, add_x, add_y)]
            with open(drill_info_path, 'w') as file_obj:
                json.dump(drill_coordinate_info, file_obj)
            
            return add_x - 20.5 + 0.23, add_y - 1.9 + 0.23, "one_text"
        else:            
            symbolname = "rect12000x3800"
            result = auto_add_features_in_panel_edge_new(step, add_x, add_y, worklayer,
                                                         symbolname, checklayer_list,
                                                         msg, 1, 0,  angle, 
                                                         area_x=area_x, area_y=area_y,
                                                         move_length=1, 
                                                         move_model_fx=move_model_fx,
                                                         to_sr_area=1, max_min_area_method="yes",
                                                         dic_all_symbol_info=dic_symbol_info,
                                                         manual_add="no", to_feat_size=0.5,
                                                         exclude_symbols=exclude_symbols)    
            if result:
                add_x, add_y, angle, _ = result
                
                drill_coordinate_info[job.name][drill_layer] = [(symbolname, add_x, add_y)]                
                if origin_text_area:
                    for xmin, ymin, xmax, ymax in origin_text_area:
                        symbol = "rect{0}x{1}".format((xmax-xmin) *1000, (ymax-ymin) *1000)
                        text_x = (xmin + xmax) * 0.5
                        text_y = (ymin + ymax) * 0.5
                        drill_coordinate_info[job.name][drill_layer].append((symbol, text_x, text_y))
                        
                with open(drill_info_path, 'w') as file_obj:
                    json.dump(drill_coordinate_info, file_obj)                    
                    
                return add_x - 5.5 + 0.23, add_y - 1.9 + 0.23, "two_text"
        
        return 0, 0, "error"

    def calc_drill_text_coordinate_info_jitaihao(self, step, drill_layer, **info):
        """自动计算钻字的位置来重新修改 钻字坐标 机台号"""
        dic_symbol_info = {}
        if sys.platform == "win32":            
            symbol_info_path = "{0}/fw/lib/symbols/symbol_info.json".format(os.environ["GENESIS_DIR"])
        else:
            symbol_info_path = "/incam/server/site_data/library/symbol_info.json"
        if not os.path.exists(symbol_info_path):
            symbol_info_path = os.path.join(os.path.dirname(sys.argv[0]), "symbol_info.json")
            
        if os.path.exists(symbol_info_path):
            with open(symbol_info_path) as file_obj:
                dic_symbol_info = json.load(file_obj)
        
        drill_info_path = "d:/drill_info/drill_info.json"
        drill_coordinate_info = {}
        if os.path.exists(drill_info_path):
            with open(drill_info_path) as file_obj:
                drill_coordinate_info = json.load(file_obj)
                
        if not drill_coordinate_info.get(job.name):
            drill_coordinate_info[job.name] = {}
            
        if not drill_coordinate_info[job.name].get(drill_layer):
            drill_coordinate_info[job.name][drill_layer] = []            
         
        drill_throu_layers = get_drill_start_end_layers(matrixInfo, drill_layer)
        symbolname = "rect3800x42000"
        if info["dataName"] == u"临时二钻":
            symbolname = "rect3800x23000"
            
        worklayer = "drill_text_tmp"
        inn_layers = [lay for i, lay in enumerate(matrixInfo["gROWname"])
                      if matrixInfo["gROWcontext"][i] == "board"
                      and matrixInfo["gROWlayer_type"][i] == "drill"
                      and (re.match("^inn.*", lay))]           
        checklayer_list = [x for x in drill_throu_layers] + tongkongDrillLayer + \
            mai_drill_layers + mai_man_drill_layers + inn_layers + \
            laser_drill_layers
        
        ##
        f_xmin, f_ymin, f_xmax, f_ymax = get_profile_limits(step)
        rect= get_sr_area_for_step_include(step.name, include_sr_step=["edit", "set", "icg", "zk"])
        sr_xmin = min([min(x1, x2) for x1, y1, x2, y2 in rect])    
        sr_ymin = min([min(y1, y2) for x1, y1, x2, y2 in rect])   
        sr_xmax = max([max(x1, x2) for x1, y1, x2, y2 in rect])    
        sr_ymax = max([max(y1, y2) for x1, y1, x2, y2 in rect])
        
        # 获取脚线区域 判断有小sr的区域
        step.COM("units,type=mm")
        if signalLayers:  
            layer_cmd = gClasses.Layer(step, signalLayers[0])
            feat_out = layer_cmd.featCurrent_LayerOut(units="mm")["pads"]
            jx_symbol_obj = [obj for obj in feat_out if obj.symbol in ("sh-con2", "sh-con")]
            all_jx_x = [obj.x for obj in jx_symbol_obj]
            all_jx_y = [obj.y for obj in jx_symbol_obj]
            if all_jx_x and all_jx_y:            
                min_jx_x = min(all_jx_x)
                max_jx_x = max(all_jx_x)
                min_jx_y = min(all_jx_y)
                max_jx_y = max(all_jx_y)            
                
                STR = '-t step -e %s/%s -d REPEAT,units=mm' % (job.name, step.name)
                gREPEAT_info = step.DO_INFO(STR)
                gREPEATstep = gREPEAT_info['gREPEATstep']
                gREPEATxmax = gREPEAT_info['gREPEATxmax']
                gREPEATymax = gREPEAT_info['gREPEATymax']
                gREPEATxmin = gREPEAT_info['gREPEATxmin']
                gREPEATymin = gREPEAT_info['gREPEATymin']
                
                set_rect_area = []
                for i, name in enumerate(gREPEATstep): 
                    if gREPEATxmin[i] > min_jx_x and gREPEATymin[i] > min_jx_y and \
                       gREPEATxmax[i] < max_jx_x and gREPEATymax[i] < max_jx_y and \
                       ("set" in name or "edit" in name or "icg" in name):
                        set_rect_area.append(
                            [gREPEATxmin[i], gREPEATymin[i], gREPEATxmax[i], gREPEATymax[i]])
                try:                
                    sr_xmin = min([min(x1, x2) for x1, y1, x2, y2 in set_rect_area])    
                    sr_ymin = min([min(y1, y2) for x1, y1, x2, y2 in set_rect_area])   
                    sr_xmax = max([max(x1, x2) for x1, y1, x2, y2 in set_rect_area])    
                    sr_ymax = max([max(y1, y2) for x1, y1, x2, y2 in set_rect_area])
                except:
                    pass
                
        ##
        try:        
            array_mrp_info = get_inplan_mrp_info(job.name, "1=1")  
            
            dic_inner_zu = {}
            dic_sec_zu = {}
            dic_outer_zu = {}
            out_lb_x = 0
            out_lb_y = 0    
            for dic_info in array_mrp_info:
                top_layer = dic_info["FROMLAY"]
                bot_layer = dic_info["TOLAY"]
                process_num = dic_info["PROCESS_NUM"]
                mrp_name = dic_info["MRPNAME"]
                pnl_routx = round(dic_info["PNLROUTX"] * 25.4, 3)
                pnl_routy = round(dic_info["PNLROUTY"] * 25.4, 3)
                
                #只取当次锣边的数据
                if not (top_layer.upper().strip() in info["OutLayer"] and \
                   bot_layer.upper().strip() in info["OutLayer"]):
                    continue
                
                out_lb_x = (f_xmax - pnl_routx) * 0.5
                out_lb_y = (f_ymax - pnl_routy) * 0.5
                
                if process_num == 1:
                    if not dic_inner_zu.has_key(process_num):
                        dic_inner_zu[process_num] = []            
                    dic_inner_zu[process_num].append([mrp_name, top_layer, bot_layer, pnl_routx, pnl_routy, 0])
                else:
                    if "-" in mrp_name:
                        if not dic_sec_zu.has_key(process_num):
                            dic_sec_zu[process_num] = []                
                        dic_sec_zu[process_num].append([mrp_name, top_layer, bot_layer, pnl_routx, pnl_routy, 0])                      
                    else:
                        if not dic_outer_zu.has_key(process_num):
                            dic_outer_zu[process_num] = []                    
                        dic_outer_zu[process_num].append([mrp_name, top_layer, bot_layer, pnl_routx, pnl_routy, 0])
                        
        except:
            out_lb_x = 2
            out_lb_y = 2
            
        if lay_num <= 2:
            out_lb_x = 2
            out_lb_y = 2            
        
        if step.isLayer("l2") and drill_layer in ["drl", "cdc", "cds"]:
            checklayer_list.append("l2")
            #step.clearAll()
            #step.affect("l2")
            #step.resetFilter()
            #step.selectSymbol("eagle-mark-dot", 1, 1)
            #if step.featureSelected():
                #step.selectDelete()
            #step.clearAll()            
        
        if step.isLayer("fill"):
            checklayer_list.append("fill")
            
        checklayer_list = [x for x in checklayer_list if x.strip()]
        
        #需避开其他钻带的字唛位置 20240110 by lyh
        if drill_coordinate_info[job.name]:
            if info["dataName"] == u"临时二钻":
                for layer in drill_coordinate_info[job.name].keys():
                    if drill_coordinate_info[job.name][layer] and layer in ["drl", "cdc", "cds"]:
                        step.clearAll()
                        step.affect("fill")
                        for symbol, x, y in drill_coordinate_info[job.name][layer]:
                            step.addPad(x, y, symbol)
            else:            
                for layer in drill_coordinate_info[job.name].keys():
                    if drill_coordinate_info[job.name][layer] and layer != drill_layer and layer != "tk.ykj":
                        step.clearAll()
                        step.affect("fill")
                        for symbol, x, y in drill_coordinate_info[job.name][layer]:
                            step.addPad(x, y, symbol)
                        
            # step = gClasses.Step(job, step.name)
            #之前已添加的位置在检查位置是否正常 若正常即不在重复计算 20240201 by lyh
            for layer in drill_coordinate_info[job.name].keys():
                if drill_coordinate_info[job.name][layer] and layer == drill_layer:
                    step.removeLayer("text_tmp")
                    step.createLayer("text_tmp")
                    recalc_coordinate = False
                    for symbol, add_x, add_y in drill_coordinate_info[job.name][layer]:
                        if symbol in ["rect3800x42000", "rect3800x23000"]:                            
                            step.clearAll()
                            step.affect("text_tmp")
                            step.addPad(add_x, add_y, symbol)
                            step.resetFilter()
                            for reflayer in checklayer_list:
                                if drill_layer == reflayer:
                                    continue
                                if reflayer == "fill":
                                    step.refSelectFilter(reflayer)
                                else:
                                    step.refSelectFilter(reflayer, f_types="pad\;text")
                                if step.featureSelected():
                                    recalc_coordinate = True
                                    break
                                
                    if not recalc_coordinate:
                        for symbol,add_x, add_y in drill_coordinate_info[job.name][layer]:   
                            if symbol in ["rect3800x42000", "rect3800x23000"]:
                                if sr_xmin > 15:
                                    # 留边大于15的情况 若字唛距板外小于2mm 重新计算 20240725
                                    if add_x - 1.9 - (f_xmin + out_lb_x) <= 2:
                                        break
                                    
                                # 方松通知机台号距有效单元需大于3.5mm 20240420 by lyh
                                if sr_xmin - (add_x + 1.9 - 0.23) >= 3.5 or \
                                   (add_x + 1.9 - 0.23) - sr_xmax >= 3.5:                                    
                                    # return add_x + 1.9 - 0.23, add_y - 32 + 0.23, "success"
                                    if symbol == "rect3800x42000":
                                        return add_x + 1.9 - 0.23, add_y - 20.5 + 0.23, "success"  
                                    if symbol == "rect3800x23000":
                                        return add_x + 1.9 - 0.23, add_y - 11 + 0.23, "success"                                  
        
        if drill_layer == "tk.ykj" or (info["dataName"] == u"临时二钻" and ".ykj" in drill_layer):
            if drill_layer == "tk.ykj":                
                drl_list = ["drl", "cdc", "cds"]
            else:
                drl_list = [drill_layer.replace(".ykj", "")]
            
            for name in drl_list:
                if drill_coordinate_info[job.name].get(name):
                    for symbol, add_x, add_y in drill_coordinate_info[job.name][name]:
                        drill_coordinate_info[job.name][drill_layer] = drill_coordinate_info[job.name][name]
                        with open(drill_info_path, 'w') as file_obj:
                            json.dump(drill_coordinate_info, file_obj)                          
                        if symbol == "rect3800x42000":
                            return add_x + 1.9 - 0.23, add_y - 20.5 + 0.23, "success"  
                        if symbol == "rect3800x23000":
                            return add_x + 1.9 - 0.23, add_y - 11 + 0.23, "success"  
        
            
        #if lay_num <= 10:
            #to_sr = 2
        #else:
            #to_sr = 2.5
        # 方松通知全部改为距成型3.5mm
        to_sr = 3.5
       
        add_x = sr_xmin - to_sr - 2.1
        add_y = f_ymax * 0.5
        move_model_fx = "Y"
        angle = 0        
        # area_x = [sr_xmin - to_sr, f_xmin + out_lb_x + 1, -0.25]
        # 批号距离当层次PNL板边5MM,间距不足最小1mm
        
        # 方松通知 20240506 翟工开会回来说钻带都屏蔽掉，全部重新输出，
        # 靠外面边统一2MM，距离不够靠外边最小按准则1MM，
        # 靠成型边大于等于3.5mm,间距不够的情况外层通孔靠成型边最小可以做到大于等于2mm
        
        #area_x = [f_xmin + out_lb_x + 2, sr_xmin - to_sr, 0.25]
        #area_y = [sr_ymin + 50, sr_ymax - 50, 1]
        msg = u"计算坐标位置失败，需人工手动输出！".encode("cp936")
        
        # 因从板外往内加钻孔会钻在板外导致断刀 故从板内往外5mm计算一次 没找到位置再从板外往内加 20240725 
        area_x = [sr_xmin - 5,f_xmin + out_lb_x + 2, -0.25]
        area_y = [sr_ymin + 50, sr_ymax - 50, 1]
        
        #step.clearAll()
        #if not step.isLayer(worklayer):
            #step.createLayer(worklayer)
        #step.affect(worklayer)
        #step.addRectangle(area_x[0], area_y[0], area_x[1], area_y[1])
        #step.PAUSE("111")        
        
        result = auto_add_features_in_panel_edge_new(step, add_x, add_y, worklayer,
                                                     symbolname, checklayer_list,
                                                     msg, 1, 0,  angle, 
                                                     area_x=area_x, area_y=area_y,
                                                     move_length=1, 
                                                     move_model_fx=move_model_fx,
                                                     to_sr_area=to_sr, max_min_area_method="yes",
                                                     dic_all_symbol_info=dic_symbol_info,
                                                     manual_add="no", to_feat_size=0.5,
                                                     exclude_symbols=["et_rj_pad", "et_rj_pad_p","et_rj_pad_n", "chris-rjpad"])        

        if not result:            
            area_x = [f_xmin + out_lb_x + 2, sr_xmin - to_sr, 0.25]
            area_y = [sr_ymin + 50, sr_ymax - 50, 1]  
            
            result = auto_add_features_in_panel_edge_new(step, add_x, add_y, worklayer,
                                                         symbolname, checklayer_list,
                                                         msg, 1, 0,  angle, 
                                                         area_x=area_x, area_y=area_y,
                                                         move_length=1, 
                                                         move_model_fx=move_model_fx,
                                                         to_sr_area=to_sr, max_min_area_method="yes",
                                                         dic_all_symbol_info=dic_symbol_info,
                                                         manual_add="no", to_feat_size=0.5,
                                                         exclude_symbols=["et_rj_pad", "et_rj_pad_p","et_rj_pad_n", "chris-rjpad"])
        if not result:
            area_x = [f_xmin + out_lb_x + 1, sr_xmin - to_sr, 0.25]
            #step.clearAll()
            #if not step.isLayer(worklayer):
                #step.createLayer(worklayer)
            #step.affect(worklayer)
            #step.addRectangle(area_x[0], area_y[0], area_x[1], area_y[1])
            #step.PAUSE("ddd")            
            result = auto_add_features_in_panel_edge_new(step, add_x, add_y, worklayer,
                                                         symbolname, checklayer_list,
                                                         msg, 1, 0,  angle, 
                                                         area_x=area_x, area_y=area_y,
                                                         move_length=1, 
                                                         move_model_fx=move_model_fx,
                                                         to_sr_area=to_sr, max_min_area_method="yes",
                                                         dic_all_symbol_info=dic_symbol_info,
                                                         manual_add="no", to_feat_size=0.5,
                                                         exclude_symbols=["et_rj_pad", "et_rj_pad_p","et_rj_pad_n", "chris-rjpad"])
            
            if not result and drill_layer in ["drl", "cdc", "cds"]:
                area_x = [f_xmin + out_lb_x + 1, sr_xmin - 2, 0.25]            
                result = auto_add_features_in_panel_edge_new(step, add_x, add_y, worklayer,
                                                             symbolname, checklayer_list,
                                                             msg, 1, 0,  angle, 
                                                             area_x=area_x, area_y=area_y,
                                                             move_length=1, 
                                                             move_model_fx=move_model_fx,
                                                             to_sr_area=2, max_min_area_method="yes",
                                                             dic_all_symbol_info=dic_symbol_info,
                                                             manual_add="no", to_feat_size=0.5,
                                                             exclude_symbols=["et_rj_pad", "et_rj_pad_p","et_rj_pad_n", "chris-rjpad"])             
        if not result:
            area_x = [sr_xmax + to_sr, f_xmax - out_lb_x - 1, 0.25]
            area_y = [sr_ymin + 50, sr_ymax - 50, 1]
            result = auto_add_features_in_panel_edge_new(step, add_x, add_y, worklayer,
                                                         symbolname, checklayer_list,
                                                         msg, 1, 0,  angle, 
                                                         area_x=area_x, area_y=area_y,
                                                         move_length=1, 
                                                         move_model_fx=move_model_fx,
                                                         to_sr_area=to_sr, max_min_area_method="yes",
                                                         dic_all_symbol_info=dic_symbol_info,
                                                         manual_add="no", to_feat_size=0.5,
                                                         exclude_symbols=["et_rj_pad", "et_rj_pad_p","et_rj_pad_n", "chris-rjpad"])
            
        if result:
            add_x, add_y, angle, _ = result            
            if drill_coordinate_info[job.name].get(drill_layer, None):
                
                new_array = [(name , x, y) for name , x, y in drill_coordinate_info[job.name][drill_layer]
                             if name != symbolname]
                if new_array:
                    drill_coordinate_info[job.name][drill_layer] = new_array + [(symbolname, add_x, add_y)]
                else:                        
                    drill_coordinate_info[job.name][drill_layer].append((symbolname, add_x, add_y))
            else:
                drill_coordinate_info[job.name][drill_layer] = [(symbolname, add_x, add_y)]
            with open(drill_info_path, 'w') as file_obj:
                json.dump(drill_coordinate_info, file_obj)
                
            if info["dataName"] == u"临时二钻":
                return add_x + 1.9 - 0.23, add_y - 11 + 0.23, "success"
            else:
                return add_x + 1.9 - 0.23, add_y - 20.5 + 0.23, "success"
        
        return 0, 0, "error"
    
    def modify_text_coordinate(self, lineList, x, y, readd_text_status_log, zscode, scale_x, scale_y):
        """修改text坐标"""
        modify = False
        coordinate_text = ""
        modx = int(x * 1000)
        tmpmodx = self.modify_xy(modx)
        coordinate_text += "X{0}".format(tmpmodx)                        
        mody = int(y * 1000)
        tmpmody = self.modify_xy(mody)
        coordinate_text += "Y{0}".format(tmpmody)
        text = ""
        for i, line in enumerate(lineList):
            if "M97" in line:
                print(line)
                if readd_text_status_log == "one_text":                    
                    m97_m98, text = line.split(",")
                    print(text, job.name)
                    if "-" in text:
                        a, b = text.strip().split("-")[:2]
                        if (a.lower() in job.name or a.lower() in "wl" + job.name)and\
                           b.lower() in job.name:                                               
                            lineList[i+1] = coordinate_text + "\n"
                            modify = True
                            break
                else:
                    scale_text = ""
                    if scale_y != 1:
                        scale_text += " L{0}".format(scale_y)
                    if scale_x != 1:
                        scale_text += " W{0}".format(scale_x) 
                    text = "M97,{1}{2}\n".format("", zscode.upper(), scale_text)                    
                    lineList.insert(i, coordinate_text + "\n")
                    lineList.insert(i, text)
                    modify = True
                    break                    
                        
        return lineList, modify, text

    def modify_text_coordinate_jitaihao(self, lineList, x, y):
        """修改机台号坐标"""
        modify = False
        coordinate_text = ""
        modx = int(x * 1000)
        tmpmodx = self.modify_xy(modx)
        coordinate_text += "X{0}".format(tmpmodx)                        
        mody = int(y * 1000)
        tmpmody = self.modify_xy(mody)
        coordinate_text += "Y{0}".format(tmpmody)         
        for i, line in enumerate(lineList):
            if "M98,*" in line:                                             
                lineList[i+1] = coordinate_text + "\n"
                modify = True
                
        return lineList, modify
    
    def modify_lp_text(self, **kwargs):
        """修改铝片的字唛孔"""
        stepname = kwargs["stepname"]
        lines = kwargs["lines"]
        worklayer = kwargs["worklayer"]
        zscode = kwargs["ZsCode"]
        if zscode.startswith("N"):
            zscode = "ZS"
            
        scale_x = kwargs["scale_x"]
        scale_y = kwargs["scale_y"]
        
        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=mm")
        
        if not step.isLayer(worklayer):
            return lines
        
        layer_cmd = gClasses.Layer(step, worklayer)
        feat_pad = layer_cmd.featCurrent_LayerOut(units="mm")["pads"]
        feat_pad += layer_cmd.featCurrent_LayerOut(units="mm")["lines"]
        
        feat_text = layer_cmd.featCurrent_LayerOut(units="mm")["text"]
        has_r508 = [obj for obj in feat_pad if obj.symbol == "r508"]
        
        r508_lines = []
        
        scale_text = ""
        if scale_y != 1:
            scale_text += " L{0}".format("%.6f" % scale_y).rstrip("0")
        if scale_x != 1:
            scale_text += " W{0}".format("%.6f" % scale_x).rstrip("0")
        
        time_form = time.strftime('%m/%d/%y', time.localtime(time.time()))
        if feat_text:
            for obj in feat_text:
                mianci = obj.text.split(" ")[0].replace("'", "")
                if "c" in mianci.lower():
                    if "VER,4\n" in lines:
                        return "error", u"检测铝片钻字为C，但资料为镜像，请重新输出1:1铝片资料！"
                if "s" in mianci.lower():
                    if "VER,1\n" in lines:
                        return "error", u"检测铝片钻字为S，但资料非镜像，请重新输出1:1铝片资料！"
                                       
                m97_98 = ""
                if obj.rotation == 0:
                    m97_98 = "M97"
                if obj.rotation == 270:
                    m97_98 = "M98"
                
                if m97_98:                    
                    text = "{6},{0} {1} {2} {3} {4} {5}".format(zscode.upper(), mianci, worklayer.upper(),
                                                                job.name.upper(), time_form,
                                                                scale_text, m97_98)
                    
                    checklayer_list = signalLayers + tongkongDrillLayer + mai_drill_layers + mai_man_drill_layers
                    
                    if step.isLayer("fill"):
                        checklayer_list.append("fill")
                        
                    step.removeLayer("text_tmp")
                    res,_,_ = self.check_text_is_touch_other_features(step, worklayer, scale_x,
                                                                      scale_y, zscode, checklayer_list,
                                                                      is_lp=True)
                    # step.PAUSE(str(res))
                    if res:
                        r508_lines.append(text+"\n")
                        coordinate_text = ""
                        modx = int(-4 * 1000) if obj.rotation == 270 else int(obj.x * 1000)
                        tmpmodx = self.modify_xy(modx)
                        coordinate_text += "X{0}".format(tmpmodx)                        
                        
                        mody = int(-4 * 1000) if obj.rotation == 0 else int(obj.y * 1000)                             
                        tmpmody = self.modify_xy(mody)
                        coordinate_text += "Y{0}".format(tmpmody)
                        r508_lines.append(coordinate_text+"\n")                        
                    else:
                        r508_lines.append(text+"\n")
                        coordinate_text = ""
                        modx = int(obj.x * 1000)
                        tmpmodx = self.modify_xy(modx)
                        coordinate_text += "X{0}".format(tmpmodx)
                        
                        mody = int(obj.y * 1000)
                        tmpmody = self.modify_xy(mody)
                        coordinate_text += "Y{0}".format(tmpmody)
                        r508_lines.append(coordinate_text+"\n")
                    
            for obj in has_r508:
                coordinate_text = ""
                modx = int(obj.xe * 1000) if obj.shape == "Line" else int(obj.x * 1000)
                tmpmodx = self.modify_xy(modx)
                coordinate_text += "X{0}".format(tmpmodx)
                
                mody = int(obj.ye * 1000) if obj.shape == "Line" else int(obj.y * 1000)
                tmpmody = self.modify_xy(mody)
                coordinate_text += "Y{0}".format(tmpmody)
                r508_lines.append(coordinate_text+"\n")
        
        new_lines = []
        if r508_lines:
            r508_t_header = ""
            line_append = True
            for num, line in enumerate(lines):
                if re.match("T\d+C0.508", line):
                    r508_t_header = line.split("C")[0]
                
                if r508_t_header and line == r508_t_header + "\n":
                    line_append = False
                    new_lines.append(line)
                    new_lines += r508_lines
                    
                if not line_append and line != r508_t_header + "\n" and line.startswith("T"):
                    line_append = True                    
                
                if line_append:
                    new_lines.append(line)
                    
            if "M30\n" not in new_lines:
                new_lines.append("M30\n")
                
        if new_lines:
            return new_lines
        
        return lines
    
    def modify_beiba_inn_coordinate(self, **kwargs):
        """修改备靶 的靶孔坐标"""        
        stepname = kwargs["stepname"]
        lines = kwargs["lines"]
        worklayer = kwargs["worklayer"]
        scale_x = kwargs["scale_x"]
        scale_y = kwargs["scale_y"]
        a, b = kwargs["OutLayer"].split(";")
        top_layer = "l{0}".format(int(a[1:]) + 1)
        bot_layer = "l{0}".format(int(b[1:]) - 1)
        
        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=mm")
        
        if not step.isLayer(worklayer):
            return lines, u"{0}层不存在，请手动输出钻带！".format(worklayer), None
        
        if not step.isLayer(top_layer):
            return lines, u"{0}层不存在，请手动输出钻带！".format(top_layer), None
        
        step.clearAll()
        step.affect(top_layer)
        step.resetFilter()
        step.selectSymbol("hdi1-by*;hdi1-byj*", 1, 1)
        layer_cmd = gClasses.Layer(step, top_layer)
        feat_out = layer_cmd.featSelOut(units="mm")["pads"]
        byb_obj = [obj for obj in feat_out if getattr(obj, "string", None) != "yh_py_pad"]
        if len(byb_obj) == 4:            
            all_x = [obj.x for obj in byb_obj]
            all_y = [obj.y for obj in byb_obj]
            
            step.clearAll()
            step.affect(worklayer)
            feat_out1 = layer_cmd.featOut(units="mm")["pads"]
            step.resetFilter()
            step.selectDelete()
            new_lines = [line for line in lines if "X" not in line and "Y" not in line and "M30" not in line]
            for obj in byb_obj:
                step.addPad(obj.x, obj.y, feat_out1[0].symbol)
                coordinate_text = ""
                modx = int(obj.x * 1000)
                tmpmodx = self.modify_xy(modx)
                coordinate_text += "X{0}".format(tmpmodx)
                
                mody = int(obj.y * 1000)
                tmpmody = self.modify_xy(mody)
                coordinate_text += "Y{0}".format(tmpmody)
                new_lines.append(coordinate_text+"\n")
            new_lines.append("M30\n")
            
            step.clearAll()
            #计算树脂铝片的拉伸值
            distance_x = max(all_x) - min(all_x)
            distance_y = max(all_y) - min(all_y)            
            
            #sz_scale_x = (distance_x * scale_x - 0.12) / distance_x
            #sz_scale_y = (distance_y * scale_y - 0.15) / distance_y
            # http://192.168.2.120:82/zentao/story-view-7803.html 20241212 by lyh
            if check_car_type or check_nv_type:                
                sz_scale_x = (distance_x * scale_x - 0.05) / distance_x
                sz_scale_y = (distance_y * scale_y - 0.07) / distance_y
            else:
                sz_scale_x = scale_x
                sz_scale_y = scale_y
            
            return new_lines, 0, (sz_scale_x, sz_scale_y)
    
        return lines, u"{0}层备用靶识别不正常，请手动输出钻带！".format(top_layer), None
    
    def find_exists_drill_file(self, **kwargs):
        """从已输出的涨缩钻带内获取*号或钻字的坐标"""
        jobname = kwargs["Job"].lower()
        origin_filepath = kwargs["filepath"]
        anchor_x = kwargs["anchor_x"]
        anchor_y = kwargs["anchor_y"]
        dirpath = ur"\\192.168.2.174\GCfiles\Program\Mechanical\压合涨缩钻带\{0}系列".format(jobname[1:4])
        m97_coors = []
        m98_coors = []
        scale_x = 1
        scale_y = 1        
        if os.path.exists(dirpath):
            for name in os.listdir(dirpath):
                if jobname in name.lower():
                    job_dir = os.path.join(dirpath, name)
                    for filename in os.listdir(job_dir):
                        if filename.lower().endswith(os.path.basename(origin_filepath)):
                            find_file_path = os.path.join(job_dir, filename)
                            lines = file(find_file_path).readlines()
                            for i, line in enumerate(lines):
                                if "M97" in line:
                                    m97_coors.append(lines[i+1])
                                    res = re.findall("L\d+(?:\.\d+)?", line)
                                    if res:                                        
                                        scale_y = float(res[0][1:])
                                        
                                    res = re.findall("W\d+(?:\.\d+)?", line)
                                    if res:                                        
                                        scale_x = float(res[0][1:])                                    
                                        
                                if "M98" in line:
                                    m98_coors.append(lines[i+1])
                            break
                        
                if m97_coors and m98_coors:
                    break
        
        new_m97_coors = [self.get_scale_coor_origin_coor(line, 1/scale_x, 1/scale_y, anchor_x, anchor_y) for line in m97_coors]
        new_m98_coors = [self.get_scale_coor_origin_coor(line, 1/scale_x, 1/scale_y, anchor_x, anchor_y) for line in m98_coors]
        # job.PAUSE(str([new_m97_coors, new_m98_coors, m97_coors, m98_coors, scale_x, scale_y, ]))
        return new_m97_coors, new_m98_coors
    
    def get_scale_coor_origin_coor(self, line, scale_x, scale_y, anchor_x, anchor_y):
        
        sssfff = line.split("G84")[0].strip().replace("G85","   ").replace("X-","  ").replace("Y-","  ").replace("X+","  ").replace("Y+","  ").replace("X"," ").replace("Y"," ")
        ssplit = sssfff.split()
        ssplits = []
        checkerrs = 0
        for z in ssplit:
            if len(z) <= 6:
                try:
                    zf = float(z.ljust(6,"0")) / (10 ** 3)
                except:
                    zf = 2000.0
            else:
                zf = 2000.0
            if zf > 999.999:
                checkerrs += 1
            ssplits.append(zf)
            
        if checkerrs:
            return line
        
        zstr = ""
        for z in range(len(sssfff)):
            if sssfff[z] == " ":
                zstr += line[z]
            else:
                zstr += "^"
        zstr += line[len(sssfff):]
        zsplit = []
        for z in zstr.split("^"):
            if z != "":
                zsplit.append(z)
        modifyxystr = ""
        for z in range(len(ssplits)):
            zzzxy = ssplits[z]
            if zsplit[z].find("-") > 0:
                zzzxy = 0 - ssplits[z]
            if zsplit[z].find("X") >= 0:
                modx = int((zzzxy + (zzzxy-anchor_x)*(scale_x-1)) *1000)
            else:
                modx = int((zzzxy + (zzzxy-anchor_y)*(scale_y-1)) *1000)

            tmpmodx = self.modify_xy(modx)
            modifyxystr += zsplit[z].replace("-","").replace("+","")
            modifyxystr += tmpmodx
        modifyxystr += string.join(zsplit[z+1:])
        
        return modifyxystr
    
    def compare_drill_layer(self, **kwargs):
        """比对1:1的钻带是否跟资料一致"""
        filepath = kwargs["filepath"]
        worklayer = kwargs["worklayer"]
        jobname = kwargs["jobname"]
        stepname = kwargs["stepname"]
        step = kwargs["step"]
        
        text_area = []
        weikong_step_area = []
        #因加了text 回读会有差异 故将比对层跟工作层text删除后再比对            
        step.clearAll()
        step.affect(worklayer)
        step.copyLayer(jobname, stepname, worklayer, worklayer+"_tmp_bak") 
        step.resetFilter()
        step.filter_set(feat_types='text')
        step.selectAll()
        if step.featureSelected():
            layer_cmd = gClasses.Layer(step, worklayer)
            indexes = layer_cmd.featSelIndex()
            for index in indexes:
                step.selectNone()
                step.selectFeatureIndex(worklayer, index)
                xmin, ymin, xmax, ymax = get_layer_selected_limits(step, worklayer)
                text_area.append([xmin - 0.3, ymin - 0.3, xmax + 0.3, ymax + 0.3])
                # step.PAUSE(str(text_area))
                
        if worklayer in matrixInfo["gCOLstep_name"]:
            weikong_step_area = get_sr_area_for_step_include(step.name, include_sr_step=[worklayer])
            
        if "tk.ykj" in worklayer:
            weikong_step_area = get_sr_area_for_step_include(step.name, include_sr_step=["drl"])                
                
        step = gClasses.Step(job, step.name)
        step.removeLayer(worklayer+"_compare")
        step.removeLayer("r0_tmp")
        compare_output.input_drill_file(jobname, stepname, filepath, worklayer)
        if step.isLayer(worklayer+"_compare"):
            step.clearAll()
            step.affect(worklayer)                    
            step.affect(worklayer+"_compare")
            
            if "inn" in worklayer:
                step.changeSymbol("r3175")
                
            step.resetFilter()
            step.filter_set(feat_types='text')
            step.selectAll()
            if step.featureSelected():
                step.selectDelete()
                
            step.COM("compare_layers,layer1=%s,job2=%s,step2=%s,\
            layer2=%s,layer2_ext=,tol=%s,area=global,consider_sr=yes,\
            ignore_attr=,map_layer=%s_diff,map_layer_res=%s" % (
            worklayer, jobname, stepname, worklayer + "_compare", 25.4, worklayer, 254))
            if step.isLayer(worklayer+"_diff"):                
                step.clearAll()
                step.affect(worklayer+"_diff")
                step.resetFilter()
                step.selectSymbol("r0", 1, 1)
                if step.featureSelected():
                    step.copySel("r0_tmp")
                    if text_area:
                        step.clearAll()
                        step.affect("r0_tmp")
                        for x1, y1, x2, y2 in text_area:
                            step.selectRectangle(x1, y1, x2, y2, intersect="yes")
                            if step.featureSelected():
                                step.selectDelete()
                                
                        # step.PAUSE("eee")
                    
                    if weikong_step_area:                        
                        step.clearAll()
                        step.affect("r0_tmp")                    
                        for sr_xmin, sr_ymin, sr_xmax, sr_ymax in weikong_step_area:
                            step.selectRectangle(sr_xmin-0.3, sr_ymin-0.3, sr_xmax+0.3, sr_ymax+0.3)
                            if step.featureSelected():
                                step.selectDelete()                                  
                                
                    step.clearAll()
                    step.affect("r0_tmp")
                    step.resetFilter()
                    step.selectAll()
                    if step.featureSelected():                        
                        return u"{0} 1:1钻带跟tgz资料内{1}层回读比对不一致，请手动输出！".format(os.path.basename(filepath), worklayer)

        else:
            return u"{0} 1:1钻带回读异常，不能正常比对，请手动输出！".format(os.path.basename(filepath))
        
        step.copyLayer(jobname, stepname, worklayer+"_tmp_bak", worklayer)
        step.removeLayer(worklayer+"_compare")
        step.removeLayer("r0_tmp")
        step.removeLayer(worklayer+"_tmp_bak")
        return None
    
    def output_scale_drill_file(self, *args):
        """自动拉伸钻带资料"""
        jobname = args[0]
        self.colseJob(jobname)
        
        output_id = args[1]
        # worklayer = args[2]
        stepname = "panel"
        job.open(0)
        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=mm")      
        
        get_sr_area_flatten("fill", get_sr_step=True)
        
        f_xmin, f_ymin, f_xmax, f_ymax = get_profile_limits(step)
        
        data_info = self.get_mysql_data(condtion="id = {0}".format(output_id))
        
        self.kill_thread = False
        
        # 检测是否有铝片塞孔
        process_data_info = get_inplan_all_flow(jobname, select_dic=True)
        lp_process = ['HDI12302']
        array_lp_info = [dic_info for dic_info in process_data_info
                    if dic_info["OPERATION_CODE"] in lp_process]
        lp_tools = list(set([x["VALUE_AS_STRING"] for x in array_lp_info if x["VALUE_AS_STRING"] and "lp" in x["VALUE_AS_STRING"]]))        
        
        #if sys.platform == "win32":
            #thrd = threading.Thread(target=self.check_get_process_is_run_normal, args=(output_id, "drill"))
            #thrd.start()
         
        for info in sorted(data_info, key=lambda x: x["workLevel"] * -1):            
            
            ID = info["id"]
            tmp_dir = "{0}/{1}/{2}/{3}".format(tmp_path, job.name, "drill", ID)            

            if info["XzsRatio"] is None or info["YzsRatio"] is None:
                log = u"登记系数异常，scalex:{XzsRatio},scale_y:{YzsRatio},请重新登记！".format(**info)
                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                       condition="id={0}".format(ID))                        
                self.write_finish_log(output_id+"_check_error")                    
                return
            
            scale_x = float(info["XzsRatio"])
            scale_y = float(info["YzsRatio"])
            
            if scale_x <= 0 or scale_y <= 0:
                log = u"登记系数异常，scalex:{XzsRatio},scale_y:{YzsRatio},请重新登记！".format(**info)
                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                       condition="id={0}".format(ID))                        
                self.write_finish_log(output_id+"_check_error")                    
                return                
            
            zscode = info["ZsCode"]
            if zscode.startswith("N"):
                zscode = "zs"
            
            get_filepath,status = self.get_scale_drill_files(**info)
            #测试
            #get_filepath = []
            #status = "success"
            #test_dir = r"\\192.168.2.126\workfile\lyh\hb0612ob006a1-test"
            #for name in os.listdir(test_dir):
                #path = os.path.join(test_dir, name)
                #if ".tgz" not in path and "2nd" in name:                    
                    #get_filepath.append(path)
                
            if status == "error":
                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(get_filepath)],
                                       condition="id={0}".format(ID))                        
                self.write_finish_log(output_id+"_check_error")                    
                return
            
            # 当申请备用靶拉伸时 需增加树脂铝片钻带
            # 测试
            # sql = "select * from drillzhangsuodb.tabResizeDrillHdi where id ={0} and isBackup = 1 "
            sql = "select * from drill_zsDb_Hdi.tabResizeDrillHdi where id ={0} and isBackup = 1 "
            beiyongba_info = self.get_mysql_data_1(sql.format(info["SourceId"]))
            
            sql1 = "select DrillLayer from drill_zsDb_Hdi.tabResizeDrillHdi where id ={0} and job = '{1}'"
            sql2 = "select DrillLayer from drill_zsDb_Hdi.tabfirstdrillhdi where id ={0} and job = '{1}' "
            array_mrp_info = self.get_mysql_data_1(sql1.format(info["SourceId"], jobname)) or \
                self.get_mysql_data_1(sql2.format(info["SourceId"], jobname)) 
                
            if info["dataName"] in [u"树脂铝片", u"塞孔铝片"]:
                mrp_name = jobname.upper()
                for dic_mrp_info in array_mrp_info:
                    if dic_mrp_info["DrillLayer"]:                        
                        mrp_name = jobname.upper() + "-" + dic_mrp_info["DrillLayer"]                
                
                erp_sz_get_filepath = []                
                arraylist_erp_drill = []
                #job.PAUSE(str(mrp_name))
                #print(process_data_info)
                for dic_process_info in process_data_info:
                    if dic_process_info["WORK_CENTER_CODE"] and \
                       u"树脂塞孔" in dic_process_info["WORK_CENTER_CODE"].decode("utf8") and \
                       mrp_name.upper() == dic_process_info["MRP_NAME"]:
                        if dic_process_info["NOTE_STRING"] and \
                           (u"树脂塞孔铝片" in dic_process_info["NOTE_STRING"].decode("utf8").replace("\n", "") or \
                            u"铝片" in dic_process_info["NOTE_STRING"].decode("utf8").replace("\n", "")):
                            find_sting = re.findall("(sz\S+)", dic_process_info["NOTE_STRING"].decode("utf8").lower())
                            # print(find_sting)
                            if find_sting:
                                for x in find_sting:
                                    new_x = ""
                                    for t in x:
                                        if ord(t) in [45,46,48, 49,50,51,52,53,54,55,56,57,99,107,108,112,115,122]:
                                            new_x += t
                                        else:
                                            new_x += " "
                                            
                                    arraylist_erp_drill += new_x.split(" ")
                                
                        if dic_process_info["WORK_DESCRIPTION"] and \
                           u"树脂塞孔铝片" in dic_process_info["WORK_DESCRIPTION"].decode("utf8"):
                            if dic_process_info["VALUE_AS_STRING"]:                                
                                arraylist_erp_drill += [dic_process_info["VALUE_AS_STRING"]]
                
                if not arraylist_erp_drill:
                    for dic_process_info in process_data_info:
                        if dic_process_info["WORK_CENTER_CODE"] and \
                           u"树脂塞孔" in dic_process_info["WORK_CENTER_CODE"].decode("utf8") and \
                           mrp_name.upper() == dic_process_info["MRP_NAME"]:                    
                            if dic_process_info["NOTE_STRING"]:
                                find_sting = re.findall("(sz\S+)", dic_process_info["NOTE_STRING"].decode("utf8").lower())
                                # print(find_sting)
                                if find_sting:
                                    for x in find_sting:
                                        new_x = ""
                                        for t in x:
                                            if ord(t) in [45,46,48, 49,50,51,52,53,54,55,56,57,99,107,108,112,115,122]:
                                                new_x += t
                                            else:
                                                new_x += " "
                                                
                                        arraylist_erp_drill += new_x.split(" ")                
                # job.PAUSE(str(mrp_name))
                if arraylist_erp_drill:
                    get_filepath = []
                    new_dic_info = {}
                    for key, value in info.iteritems():
                        new_dic_info[key] = value
                        if key == "dataName":
                            new_dic_info[key] = u"树脂铝片"
                    new_dic_info["sz_erp_drill_layer"] = list(set(arraylist_erp_drill))
                    erp_sz_get_filepath,status = self.get_scale_drill_files(**new_dic_info)
                    # job.PAUSE(str([erp_sz_get_filepath, list(set(arraylist_erp_drill))]))
                    if not erp_sz_get_filepath:
                        log = u"未找到cam输出的1:1的铝片钻带：{0}，请通知cam输出！".format(" ".join(list(set(arraylist_erp_drill))))
                        self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                               condition="id={0}".format(ID))                        
                        self.write_finish_log(output_id+"_check_error")                    
                        return
                    
                    get_filepath += erp_sz_get_filepath
                else:
                    log = u"获取erp的铝片钻带工具为空，请检查erp工具信息并反馈给程序工程师，请手动输出！"
                    self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                           condition="id={0}".format(ID))                        
                    self.write_finish_log(output_id+"_check_error")                    
                    return                    
                            
            get_filepath = list(set(get_filepath))
            # job.PAUSE(str([get_filepath, arraylist_erp_drill]))
            # if "192.168.19.243" in localip[2]:
            sz_get_filepath = ""
            if beiyongba_info:                
                new_dic_info = {}
                for key, value in info.iteritems():
                    new_dic_info[key] = value
                    if key == "dataName":
                        new_dic_info[key] = u"树脂铝片"
                sz_get_filepath,status = self.get_scale_drill_files(**new_dic_info)
                get_filepath += sz_get_filepath
                
            if not get_filepath:
                log = u"未找到cam输出的1:1的钻带：{0}，请通知cam输出！".format(info["dataName"])
                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                       condition="id={0}".format(ID))                        
                self.write_finish_log(output_id+"_check_error")                    
                return
            
            if lp_tools and (info["dataName"] == u"通孔" or \
                             (info["dataName"] == u"开料钻申请" and 'L1;' in info["OutLayer"] )):
                if ".lp" not in "".join(get_filepath):
                    log = u"检测到此型号有防焊塞孔铝片流程，未找到cam输出的1:1的铝片钻带：{0}，请通知cam输出！".format(info["dataName"])
                    self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                           condition="id={0}".format(ID))                        
                    self.write_finish_log(output_id+"_check_error")                    
                    return
                
            output_layers = []
            dic_layer_contact_path = {}
            for num, x in enumerate(get_filepath):
                layer = x.lower().split(jobname.lower() + ".")[1]
                if layer.endswith("inn"):
                    if info["dataName"] == u"通孔":
                        if re.match("cdc|cds|bdc|bds", layer.lower()):
                            output_layers.append(layer)
                            dic_layer_contact_path[layer] = os.path.join(tmp_dir,os.path.basename(x))
                        else:
                            output_layers.append("inn")
                            dic_layer_contact_path["inn"] = os.path.join(tmp_dir,os.path.basename(x))
                    elif info["dataName"] == u"临时二钻":
                        output_layers.append(layer)
                        dic_layer_contact_path[layer] = os.path.join(tmp_dir,os.path.basename(x))                        
                    else:
                        if lay_num > 2:
                            if layer.startswith("m"):
                                output_layers.append(layer)
                                dic_layer_contact_path[layer] = os.path.join(tmp_dir,os.path.basename(x))
                            else:
                                a, b = info["OutLayer"].split(";")
                                output_layers.append("inn{0}{1}".format(a[1:], b[1:]))
                                dic_layer_contact_path["inn{0}{1}".format(a[1:], b[1:])] = os.path.join(tmp_dir,os.path.basename(x))
                        else:
                            output_layers.append("inn")
                            dic_layer_contact_path["inn"] = os.path.join(tmp_dir,os.path.basename(x))                            
                elif layer.endswith("dbk"):
                    if lay_num > 2:      
                        a, b = info["OutLayer"].split(";")
                        if layer.startswith("m"):
                            output_layers.append("dbkm{0}-{1}".format(a[1:], b[1:]))
                            if not os.path.exists(x):
                                get_filepath[num] = os.path.join(os.path.dirname(x), jobname+"."+"dbkm{0}-{1}".format(a[1:], b[1:]))
                                dic_layer_contact_path["dbkm{0}-{1}".format(a[1:], b[1:])] = os.path.join(tmp_dir,jobname+"."+"dbkm{0}-{1}".format(a[1:], b[1:]))
                            else:
                                dic_layer_contact_path["dbkm{0}-{1}".format(a[1:], b[1:])] = os.path.join(tmp_dir,os.path.basename(x))
                        else:
                            output_layers.append("dbkb{0}-{1}".format(a[1:], b[1:]))
                            if not os.path.exists(x):
                                get_filepath[num] = os.path.join(os.path.dirname(x), jobname+"."+"dbkb{0}-{1}".format(a[1:], b[1:]))
                                dic_layer_contact_path["dbkb{0}-{1}".format(a[1:], b[1:])] = os.path.join(tmp_dir,jobname+"."+"dbkb{0}-{1}".format(a[1:], b[1:]))
                            else:
                                dic_layer_contact_path["dbkb{0}-{1}".format(a[1:], b[1:])] = os.path.join(tmp_dir,os.path.basename(x))
                    else:
                        output_layers.append("dbk")
                        dic_layer_contact_path["dbk"] = os.path.join(tmp_dir,os.path.basename(x))                         
                else:
                    output_layers.append(layer)
                    dic_layer_contact_path[layer] = os.path.join(tmp_dir,os.path.basename(x))
                    
            print(get_filepath, output_layers)
            not_exists_layers = []
            exists_drl_layers = []
            for worklayer in output_layers:            
                if not step.isLayer(worklayer):
                    not_exists_layers.append(worklayer)

                for lay in ["drl", "cdc", "cds"]:
                    if lay in worklayer:
                        exists_drl_layers.append(lay)

            if (info["dataName"] == u"通孔" or \
                (info["dataName"] == u"开料钻申请" and 'L1;' in info["OutLayer"] )):
                if not exists_drl_layers:                    
                    log = u"未找到cam输出的1:1的通孔钻带：{0}，请通知cam输出！".format(info["dataName"])
                    self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                           condition="id={0}".format(ID))                        
                    self.write_finish_log(output_id+"_check_error")                    
                    return

            if not_exists_layers:                
                log = u"输出层{0} 不存在，请检查tgz资料是否正常！<br>".format(" ".join(not_exists_layers))
                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                       condition="id={0}".format(ID))                        
                self.write_finish_log(output_id+"_check_error")                    
                return
            
            dic_new_scale_info = {}
            
            tk_ykj = [x for x in get_filepath if ".ykj" in x]
            get_filepath = [x for x in get_filepath if x not in tk_ykj]
            for filepath in get_filepath + tk_ykj:
                if not os.path.exists(filepath):
                    log = u"拉伸文件{0} 不存在，请通知cam是否漏输出资料！<br>".format(os.path.basename(filepath))
                    self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                           condition="id={0}".format(ID))                        
                    self.write_finish_log(output_id+"_check_error")                    
                    return
                
                start_time = self.get_current_format_time()
                log = u"开始拉伸钻带{0} cartype:{2} {1} <br>".format(os.path.basename(filepath), start_time, check_car_type)
                self.update_mysql_data([u"Status = '{0}'".format(u"输出中"),
                                        u"OutputStatus = '{0}'".format(u"输出中"),
                                        u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                        condition="id={0}".format(ID))
                
                output_path = os.path.join(tmp_dir, os.path.basename(filepath))                
                lineList = file(filepath).readlines()
                
                drill_layer = ""
                for key, value in dic_layer_contact_path.iteritems():
                    if value == output_path:
                        drill_layer = key
                        break
                
                res = self.compare_drill_layer(worklayer=str(drill_layer),
                                               stepname=str(stepname),
                                               jobname=str(job.name),
                                               filepath=filepath.encode("cp936").replace("\\", "/"),
                                               step=step)
                if res:                    
                    self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(res)],
                                           condition="id={0}".format(ID))                        
                    self.write_finish_log(output_id+"_check_error")                    
                    return                    
                
                if beiyongba_info and ".inn" in os.path.basename(filepath):
                    lineList,status,lp_scale_xy = self.modify_beiba_inn_coordinate(lines=lineList,
                                                                                   worklayer=drill_layer,
                                                                                   stepname=stepname,
                                                                                   scale_x=scale_x,
                                                                                   scale_y=scale_y, 
                                                                                   **info)                    
                    if status:
                        self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(status)],
                                               condition="id={0}".format(ID))                        
                        self.write_finish_log(output_id+"_check_error")                    
                        return
                      
                    sz_lp_scale_x, sz_lp_scale_y = lp_scale_xy
                    
                new_drill_mode = False
                
                add_text_x, add_text_y, readd_text_status_log = 0, 0, "not_modify"
                if ".lp" in os.path.basename(filepath) or info["dataName"] in [u"树脂铝片", u"塞孔铝片"]:
                    if filepath in sz_get_filepath:
                        lineList = self.modify_lp_text(lines=lineList,
                                                       worklayer=drill_layer,
                                                       stepname=stepname,
                                                       scale_x=sz_lp_scale_x,
                                                       scale_y=sz_lp_scale_y, 
                                                       **info)
                    else:
                        lineList = self.modify_lp_text(lines=lineList,
                                                       worklayer=drill_layer,
                                                       stepname=stepname,
                                                       scale_x=scale_x,
                                                       scale_y=scale_y, 
                                                       **info)
                    if "error" in lineList:
                        self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(lineList[1])],
                                               condition="id={0}".format(ID))                        
                        self.write_finish_log(output_id+"_check_error")                    
                        return                        
                else:
                    if "M97,8888\n" in lineList:
                        
                        drill_throu_layers = get_drill_start_end_layers(matrixInfo, drill_layer)
                        if "lr" in drill_layer:
                            drill_throu_layers = ["l{0}".format(drill_layer.split("-")[0][2:]),
                                                  "l{0}".format(drill_layer.split("-")[1])]
                        
                        inn_layers = [lay for i, lay in enumerate(matrixInfo["gROWname"])
                                      if matrixInfo["gROWcontext"][i] == "board"
                                      and matrixInfo["gROWlayer_type"][i] == "drill"
                                      and (re.match("^inn.*", lay))]           
                        checklayer_list = [x for x in drill_throu_layers] + tongkongDrillLayer + \
                            mai_drill_layers + mai_man_drill_layers + inn_layers + \
                            laser_drill_layers
                        
                        if step.isLayer("l2") and drill_layer in ["drl", "cdc", "cds"]:
                            checklayer_list.append("l2")
                        
                        if step.isLayer("fill"):
                            checklayer_list.append("fill")
                        
                        res = 0
                        if ".ykj" not in drill_layer:                            
                            res,avoid_text_area,origin_text_area = self.check_text_is_touch_other_features(step, drill_layer, scale_x,
                                                                                                           scale_y, zscode, checklayer_list,
                                                                                                           change_text=False)
                        if res:
                            log = u"钻带{0}输出检测到机台号或字唛孔有钻到板边其他物件无法移开，请手动输出！<br>".format(os.path.basename(filepath))
                            self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                                   condition="id={0}".format(ID))                        
                            self.write_finish_log(output_id+"_check_error")                    
                            return                            
                        
                        new_drill_mode = True
                        # 新输出模式 不在找*号坐标 及字唛位置 直接改text内容即可 20241210 by lyh
                        for i, line in enumerate(lineList):
                            if "M97,8888\n" == line:
                                lineList[i] = "M97,{0}\n".format(zscode.upper())                                
                    else:
                        if info["dataName"] == u"临时二钻" and ".inn" not in drill_layer:
                            if "M97" not in "".join(lineList) and "M98,*" not in "".join(lineList):
                                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0} {1}')".format(drill_layer, u"1:1钻带内未发现批号及机台号字唛，请通知CAM重新输出1:1钻带！")],
                                                       condition="id={0}".format(ID))                        
                                self.write_finish_log(output_id+"_check_error")                    
                                return

                        if "M97" in "".join(lineList): # or (info["dataName"] == u"临时二钻" and ".inn" not in drill_layer):
                            add_text_x, add_text_y, readd_text_status_log = self.calc_drill_text_coordinate_info(step, drill_layer,
                                                                                                                 scale_x, scale_y,
                                                                                                                 zscode, **info)
                            if readd_text_status_log in ("one_text", "two_text"):
                                lineList ,modify_status,text = self.modify_text_coordinate(lineList, add_text_x, add_text_y,
                                                                                           readd_text_status_log, zscode,
                                                                                           scale_x, scale_y)
                                
                                log = u"已优化调整字唛位置:{0}<br>".format(readd_text_status_log)
                                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                                       condition="id={0}".format(ID))                              
                                if not modify_status:
                                    log = u"钻带{0}输出添加型号涨缩字唛孔位置异常，文件内的M97 text:{1} 跟料号名不一致，请手动输出！<br>".format(os.path.basename(filepath), text)
                                    self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                                           condition="id={0}".format(ID))                        
                                    self.write_finish_log(output_id+"_check_error")                    
                                    return
                                
                            elif readd_text_status_log == "error":
                                m97_coors, m98_coors = self.find_exists_drill_file(filepath=filepath,
                                                                                   anchor_x=(f_xmin+f_xmax) *0.5,
                                                                                   anchor_y=(f_ymin+f_ymax) *0.5, 
                                                                                   **info)
                                modify_status = False
                                if len(m97_coors) == 1:
                                    for i, line in enumerate(lineList):
                                        if "M97," in line:                                             
                                            m97_m98, text = line.split(",")
                                            print(text, job.name)
                                            if "-" in text:
                                                a, b = text.strip().split("-")[:2]
                                                if (a.lower() in job.name or a.lower() in "wl" + job.name)and\
                                                   b.lower() in job.name:                                               
                                                    lineList[i+1] = m97_coors[0]
                                                    modify_status = True
                                                    readd_text_status_log = "one_text"
                                                    log = u"从已输出文件中获取字唛位置:{0}<br>".format(m97_coors[0])
                                                    self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                                                           condition="id={0}".format(ID))                                                  
                                                    break
                                            
                                if not modify_status:
                                    
                                    log = u"钻带{0}输出添加型号涨缩字唛孔位置不足，系统无法正确找到合适位置，请手动输出！<br>".format(os.path.basename(filepath))
                                    self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                                           condition="id={0}".format(ID))                        
                                    self.write_finish_log(output_id+"_check_error")                    
                                    return
                            
                        if "M98,*" in "".join(lineList): # or (info["dataName"] == u"临时二钻" and ".inn" not in drill_layer):
                            add_text_x, add_text_y, jitaihao_status_log = self.calc_drill_text_coordinate_info_jitaihao(step, drill_layer, **info)
                            if jitaihao_status_log == "success":
                                lineList ,modify_status = self.modify_text_coordinate_jitaihao(lineList, add_text_x, add_text_y)
                                if not modify_status:
                                    log = u"钻带{0}输出添加机台号*位置不足2，系统无法正确找到合适位置，请手动输出！<br>".format(os.path.basename(filepath))
                                    self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                                           condition="id={0}".format(ID))                        
                                    self.write_finish_log(output_id+"_check_error")                    
                                    return
                            else:
                                # 查找已存在的钻带 从中提取*号的坐标 20240618 by lyh
                                m97_coors, m98_coors = self.find_exists_drill_file(filepath=filepath,
                                                                                   anchor_x=(f_xmin+f_xmax) *0.5,
                                                                                   anchor_y=(f_ymin+f_ymax) *0.5, 
                                                                                   **info)
                                modify_status = False
                                if len(m98_coors) == 1:
                                    for i, line in enumerate(lineList):
                                        if "M98,*" in line:                                             
                                            lineList[i+1] = m98_coors[0]
                                            modify_status = True
                                            log = u"从已输出文件中获取机台号位置:{0}<br>".format(m98_coors[0])
                                            self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                                                   condition="id={0}".format(ID))                                         
                                            break
                                
                                # job.PAUSE(str([m98_coors, modify_status, m97_coors]))
                                if not modify_status:
                                    log = u"钻带{0}输出添加机台号*位置不足，系统无法正确找到合适位置，请手动输出！<br>".format(os.path.basename(filepath))
                                    self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                                           condition="id={0}".format(ID))                        
                                    self.write_finish_log(output_id+"_check_error")                    
                                    return
                
                new_scale_x = scale_x
                new_scale_y = scale_y
                if beiyongba_info and filepath in sz_get_filepath:
                    new_scale_x = sz_lp_scale_x
                    new_scale_y = sz_lp_scale_y
                
                dic_new_scale_info[output_path] = (new_scale_x, new_scale_y)
                
                if new_drill_mode:
                    status, new_lines = self.scale_list(lineList, new_scale_x, new_scale_y,
                                                        (f_xmin+f_xmax) *0.5, (f_ymin+f_ymax) *0.5, "",
                                                        os.path.basename(filepath), readd_text_status_log)                    
                else:
                    status, new_lines = self.scale_list(lineList, new_scale_x, new_scale_y,
                                                        (f_xmin+f_xmax) *0.5, (f_ymin+f_ymax) *0.5, zscode+" ",
                                                        os.path.basename(filepath), readd_text_status_log)
                if not status:
                    with open(output_path, "w") as f:
                        f.write("".join(new_lines))
                
                print(status, "-------------->")
                if status:
                    return
                
            # 关闭型号再次打开
            #self.colseJob(jobname)
            #job.open(0)
            #step = gClasses.Step(job, stepname)
            #step.open()
            #step.COM("units,type=mm")
            step.COM("config_edit,name=iol_fix_ill_polygon,value=yes,mode=user")
            
            arraylist = []
            for worklayer in output_layers:
                start_time = self.get_current_format_time()
                log = u"开始回读比对{0}  {1} <br>".format(worklayer, start_time)
                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                       condition="id={0}".format(ID))                  
                    
                self.write_calc_time_log(ID)
                
                #if worklayer == "inn":
                    #filepath = os.path.join(tmp_dir,"{0}.drl.{1}".format(jobname, worklayer))
                #else:
                filepath = dic_layer_contact_path[worklayer]# os.path.join(tmp_dir,"{0}.{1}".format(jobname, worklayer))
                new_scale_x, new_scale_y = dic_new_scale_info[filepath]      
                # step.VOF()
                warning_log = ""
                if os.path.exists(filepath):
                    diff_cout, diff_info,compare_status = compare_output.compare_drill(jobname, step.name, worklayer,
                                                                                      "no", new_scale_x, new_scale_y,
                                                                                      filepath.encode("cp936").replace("\\", "/"),
                                                                                      "drill", (f_xmin+f_xmax) *0.5, (f_ymin+f_ymax) *0.5,
                                                                                      "layer_compare")                    
                    if sys.platform <> "win32":                        
                        if diff_cout:
                            diff_cout, diff_info,compare_status = compare_output.compare_drill(jobname, step.name, worklayer,
                                                                                              "no", new_scale_x, new_scale_y,
                                                                                              filepath.encode("cp936").replace("\\", "/"),
                                                                                              "drill", (f_xmin+f_xmax) *0.5, (f_ymin+f_ymax) *0.5,
                                                                                              "step_compare")
                            
                    if compare_status == 0 and diff_cout == 0:                        
                        self.write_finish_log(output_id+"_"+worklayer)
                        
                        #修改钻带命名
                        #dir_path = os.path.dirname(filepath)
                        #filename = os.path.basename(filepath)
                        #new_filename = filename.replace(jobname, jobname+"-"+"x{0}y{1}".format(new_scale_x, new_scale_y))
                        #shutil.move(filepath, os.path.join(dir_path, new_filename))
                        
                    if compare_status > 0:
                        warning_log = u"{0}  {1}拉伸钻带回读比对比对报内存不足,异常状态[{2}],请手动输出！<br>".format(start_time, worklayer, compare_status)
                        
                    if diff_cout:                            
                        warning_log = u"{0}  {1}拉伸钻带回读比对不一致({2}),请手动输出！<br>".format(start_time, worklayer, diff_info)
                else:                    
                    warning_log = u"{0}层拉伸异常失败，请手动输出！<br>".format(worklayer)
                
                if warning_log:
                    arraylist.append(warning_log)                  
                
                # step.VON()
                
            if arraylist:
                self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常"),
                                        u"Status = '{0}'".format(u"输出中"),
                                        u"AlarmLog = concat(AlarmLog,'{0}')".format("".join(arraylist))],
                                       condition="id={0}".format(ID))
                self.write_finish_log(output_id+"_check_error")
                return
        
        self.kill_thread = True
        self.write_finish_log(output_id)
                
    def output_orbotech_ldi_opfx(self, *args):
        """输出奥宝LDI资料"""
        jobname = args[0]
        self.colseJob(jobname)
        
        output_id = args[1]
        # worklayer = args[2]
        stepname = "panel"
        job.open(0)
        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=mm")
        step.COM("import_lib_item_to_job,src_category=symbols,src_profile=system,src_customer=,dst_names=hdi_orbldi_stamp_1")
        step.COM("import_lib_item_to_job,src_category=symbols,src_profile=system,src_customer=,dst_names=hdi_orbldi_stamp")        
        
        f_xmin, f_ymin, f_xmax, f_ymax = get_profile_limits(step)
        
        data_info = self.get_mysql_data(condtion="id = {0}".format(output_id))
        
        self.kill_thread = False
        
        if sys.platform == "win32":
            thrd = threading.Thread(target=self.check_get_process_is_run_normal, args=(output_id, "ldi"))
            thrd.start()
            
        dic_layer_info,warning_log = self.get_layer_pol_and_mirror(job.name)
        if warning_log:
            self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format("".join(warning_log))],
                                   condition="id={0}".format(output_id))
            self.write_finish_log(output_id+"_check_error")             
            return          
        
        led_type = get_led_board(job.name)
        # try:            
        for info in sorted(data_info, key=lambda x: x["workLevel"] * -1):
            
            output_layers = [x for x in info["OutLayer"].split(";") if x.strip()]                
            ID = info["id"]
            tmp_dir = "{0}/{1}/{2}/{3}".format(tmp_path, job.name, "ldi", ID)
            
            try:                                
                os.makedirs(tmp_dir)
            except Exception, e:
                print(e)
                pass
            
            
            erros = []
            
            if info["data_type"] == u"输出奥宝LDI资料(线路及辅助)": 
                rate_copper = self.get_copper_rate(step, output_layers)
                for k_lay, v_rate in rate_copper.items():
                    if v_rate is None:
                        erros.append(u"%s层没有添加铜面积" % k_lay)
                    else:
                        texts = list(set(v_rate))
                        if len(texts) > 1:
                            erros.append(u"%s层存在多种铜面积，且数据不一致" % k_lay)
                        
            if erros:                
                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format("<br>".join(erros))],
                                       condition="id={0}".format(ID))                        
                self.write_finish_log(output_id+"_check_error")                    
                return
            
            os.environ["SHOW_UI"] = "no"
            res = check_rule.check_aobao_danymic_text_info(*output_layers)
            if res[0] != "success":
                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format("<br>".join(res[0]))],
                                       condition="id={0}".format(ID))                        
                self.write_finish_log(output_id+"_check_error")                    
                return                
            
            for worklayer in output_layers:
            
                if not step.isLayer(worklayer):
                    log = u"输出层{0} 不存在，请检查tgz资料是否正常！<br>".format(worklayer)
                    self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                           condition="id={0}".format(ID))                        
                    self.write_finish_log(output_id+"_check_error")                    
                    return
                
                if led_type and worklayer in solderMaskLayers:
                    log = u"LED板,不输出LDI格式防焊资料{0}！<br>".format(worklayer)
                    self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                           condition="id={0}".format(ID))
                    self.write_finish_log(output_id+"_check_error")   
                    return
                
                if "wangping" not in args:                    
                    res = self.check_ldi_r0_is_right(step, worklayer, dic_layer_info) or \
                        self.get_week_picihao_banci_info(step, worklayer)
                    
                    if res:
                        self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(res+"<br>")],
                                               condition="id={0}".format(ID))
                        self.write_finish_log(output_id+"_check_error")             
                        return
            
            error_modify_layers = []
            for worklayer in output_layers:
                
                start_time = self.get_current_format_time()
                log = u"开始输出层{0}  {1} <br>".format(worklayer, start_time)
                self.update_mysql_data([u"Status = '{0}'".format(u"输出中"),
                                        u"OutputStatus = '{0}'".format(u"输出中"),
                                        u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                       condition="id={0}".format(ID))
                                
                self.write_calc_time_log(ID)                
                
                core = "no"
                mirror = "none"
                if dic_layer_info.get(worklayer):                    
                    mirror = dic_layer_info[worklayer]["mirror"]
                    core = dic_layer_info[worklayer]["core"]
                    
                #调用值班程序输出
                if info["data_type"] == u"输出奥宝LDI资料(线路及辅助)": 
                    os.system(r'perl /incam/server/site_data/scripts/sh_script/ldi_orbotech/output_ldi_win_hdi_auto.pl {0} {1} {2} {3}'.format(output_id, worklayer,core, mirror))
                else:
                    os.system(r'perl /incam/server/site_data/scripts/sh_script/ldi_orbotech/output_ldi_sm_auto.pl {0} {1}  {2} {3}'.format(output_id, worklayer, core, mirror))
                
                error_file = os.path.join(tmp_path, "success_{0}_check_error.log".format(output_id))
                if os.path.exists(error_file):
                    error_step = self.get_error_log()
                    if error_step:
                        edit_step = gClasses.Step(job, error_step)
                        edit_step.open()
                        edit_step.COM("units,type=mm")
                        edit_step.resetFilter()
                        edit_step.clearAll()
                        edit_step.affect(worklayer)
                        edit_step.setAttrFilter(".orbotech_plot_stamp")
                        edit_step.selectAll()
                        edit_step.COM("sel_reverse")
                        edit_step.contourize()
                        os.unlink(error_file)
                        error_modify_layers.append(worklayer)
                        if info["data_type"] == u"输出奥宝LDI资料(线路及辅助)": 
                            os.system(r'perl /incam/server/site_data/scripts/sh_script/ldi_orbotech/output_ldi_win_hdi_auto.pl {0} {1} {2} {3}'.format(output_id, worklayer,core, mirror))
                        else:
                            os.system(r'perl /incam/server/site_data/scripts/sh_script/ldi_orbotech/output_ldi_sm_auto.pl {0} {1}  {2} {3}'.format(output_id, worklayer, core, mirror))                                                
                    
                if os.path.exists("{0}/success_{1}.log".format(tmp_path, output_id)):                    
                    for name in os.listdir(tmp_dir):
                        if "{0}@{1}".format(jobname, worklayer.replace(".", "")) in name:
                            filepath = os.path.join(tmp_dir, name)
                            new_filepath = os.path.join(tmp_dir, "{0}@{1}".format(jobname, worklayer))
                            os.rename(filepath, new_filepath)
                            
                            #防焊输出需加一个参数
                            if worklayer in solderMaskLayers:
                                lines = file(new_filepath).readlines()
                                index = None
                                for i, line in enumerate(lines):
                                    if line.startswith("PRIORITY"):
                                        index = i
                                    if line.startswith("LINES_NUM"):
                                        _, num = line.split("=")
                                        lines[i] = "LINES_NUM = {0}\n".format(int(num) + 1)
                                if index:
                                    lines.insert(index+1, "COMPENSATION_CODE = HDI\n")
                                    
                                with open(new_filepath, "w") as f:
                                    f.write("".join(lines))                                        
                else:
                    error_file = os.path.join(tmp_path, "success_{0}_check_error.log".format(output_id))
                    if os.path.exists(error_file):                        
                        log = file(error_file).readlines()
                        self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常(推送消息)"),
                                                u"AlarmLog = concat(AlarmLog,'{0}<br>')".format("<br>".join(log).decode("utf8")),
                                                u"Status = '{0}'".format(u"输出异常"),],
                                               condition="id={0}".format(output_id))
                        os.unlink(error_file)
                    continue
                
                if os.path.exists("{0}/success_{1}.log".format(tmp_path, output_id)):
                    os.unlink("{0}/success_{1}.log".format(tmp_path, output_id))
                    
                #step.clearAll()
                #step.affect(worklayer)
                #x_center = (f_xmin + f_xmax) * 0.5
                #y_center = (f_ymin + f_ymax) * 0.5
                #dic_output_args = {}
                #dic_output_args["job"] = job.name                    
                #dic_output_args["step"] = step.name
                #dic_output_args["layer"] = worklayer
                #dic_output_args["polarity"] = dic_layer_info[worklayer]["pol"]
                #dic_output_args["xstretch"] = 100
                #dic_output_args["ystretch"] = 100
                #if dic_layer_info[worklayer]["mirror"] == "no":                        
                    #dic_output_args["xmirror"] = 0
                    #dic_output_args["ymirror"] = 0
                #else:
                    #dic_output_args["xmirror"] = x_center
                    #dic_output_args["ymirror"] = 0
                    
                #dic_output_args["xcenter"] = x_center
                #dic_output_args["ycenter"] = y_center
                #dic_output_args["swap_axes"] = "no_swap"
                #dic_output_args["x_anchor"] = x_center
                #dic_output_args["y_anchor"] = y_center
                
                #dic_output_args["clip_size"] = "{0} {1}".format(dic_layer_info[worklayer]["board_x"],dic_layer_info[worklayer]["board_y"])
                #dic_output_args["clip_orig"] = "{0} {1}".format(dic_layer_info[worklayer]["cut_x"],dic_layer_info[worklayer]["cut_y"])
                #dic_output_args["clip_width"] = dic_layer_info[worklayer]["board_x"]
                #dic_output_args["clip_height"] = dic_layer_info[worklayer]["board_y"]
                #dic_output_args["clip_orig_x"] = dic_layer_info[worklayer]["cut_x"]
                #dic_output_args["clip_orig_y"] = dic_layer_info[worklayer]["cut_y"]
                #dic_output_args["resolution_value"] = 2
                #dic_output_args["dir_path"] = tmp_dir
                #dic_output_args["step_obj"] = step
                
                #output_opfx(**dic_output_args)
                    
                #error_num = step.STATUS
                #if error_num > 0:                    
                    #if error_num == 45005:
                        ##进行sip 处理
                        #self.opt_layer_to_output(worklayer)
                        #output_opfx(**dic_output_args)
                        #error_num = step.STATUS
                        #if error_num > 0:
                            #if "gui_run" in sys.argv:                                
                                #step.PAUSE(str([error_num, 2]))
                            #self.get_error_log()                            
                    #else:
                        ##进行sip 处理
                        #self.opt_layer_to_output(worklayer)
                        
                        #output_opfx(**dic_output_args)
                        
                        #error_num = step.STATUS
                        #if error_num > 0:
                            #if "gui_run" in sys.argv:   
                                #step.PAUSE(str([error_num, 1]))
                            #self.get_error_log()
                            
                #for name in os.listdir(tmp_dir):
                    #if "{0}@{1}".format(jobname, worklayer) in name:
                        #filepath = os.path.join(tmp_dir, name)
                        #new_filepath = os.path.join(tmp_dir, "{0}@{1}".format(jobname, worklayer))
                        #os.rename(filepath, new_filepath)
                        
                #step.VON()
                
            # 关闭型号再次打开
            # self.colseJob(jobname)
            # job.open(0)
            step = gClasses.Step(job, stepname)
            step.open()
            step.COM("units,type=mm")
            step.COM("config_edit,name=iol_fix_ill_polygon,value=yes,mode=user")
                
            for worklayer in [x for x in output_layers if x not in error_modify_layers] + error_modify_layers:
                if worklayer in error_modify_layers:
                    # 关闭型号再次打开
                    self.colseJob(jobname)
                    job.open(0)
                    step = gClasses.Step(job, stepname)
                    step.open()
                    step.COM("units,type=mm")
                    
                start_time = self.get_current_format_time()
                log = u"开始输回读比对{0}  {1} <br>".format(worklayer, start_time)
                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                       condition="id={0}".format(ID))                  
                    
                self.write_calc_time_log(ID)
                
                filepath = os.path.join(tmp_dir,"{0}@{1}".format(jobname, worklayer))
                # step.VOF()
                warning_log = ""
                if os.path.exists(filepath):
                    # step.removeLayer(worklayer+"_compare")
                    # step.createLayer(worklayer+"_compare")
                    step.removeLayer(worklayer+"+1")
                    diff_cout, diff_info,compare_status = compare_output.compare_opfx(jobname, step.name, worklayer,
                                                                                      "no", 1, 1,
                                                                                      filepath.encode("cp936").replace("\\", "/"),
                                                                                      "opfx", 0, 0, "layer_compare")                    
                    #if sys.platform <> "win32":                        
                        #if diff_cout:
                            ## step.removeLayer(worklayer+"_compare")
                            #step.removeLayer(worklayer+"+1")
                            #diff_cout, diff_info,compare_status = compare_output.compare_opfx(jobname, step.name, worklayer,
                                                                                              #"no", 1, 1,
                                                                                              #filepath.encode("cp936").replace("\\", "/"),
                                                                                              #"opfx", 0, 0, "step_compare")
                            
                    if compare_status == 0 and diff_cout == 0:                            
                        self.write_finish_log(output_id+"_"+worklayer)
                        
                    if compare_status > 0:
                        warning_log = u"{1}输出opfx回读比对比对报内存不足,异常状态[{2}],请手动输出！ {0}<br>".format(start_time, worklayer, compare_status)
                        
                    if diff_cout:
                        warning_log = u"{1}输出opfx回读比对不一致({2}),请手动输出！ {0} <br>".format(start_time, worklayer, diff_info)
                else:                    
                    warning_log = u"{0}层输出输出失败，请手动输出！<br>".format(worklayer)
                
                if warning_log:                        
                    self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常"),
                                            u"Status = '{0}'".format(u"输出中"),
                                            u"AlarmLog = concat(AlarmLog,'{0}')".format(warning_log)],
                                           condition="id={0}".format(ID))                    
                # step.VON()
           
        self.kill_thread = True
        self.write_finish_log(output_id)

    def get_copper_rate(self, step, get_layers):
        """镀孔菲林检测是否跑镀孔面积"""
        dict={}
        for layer in get_layers:
            if not re.match("l\d+-dk|l\d+-gk", layer):
                continue
            layer_cmd = gClasses.Layer(step, layer)
            step.affect(layer)
            step.filter_set(feat_types='text')
            step.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=.area_name,text=copper_rate')
            step.selectAll()
            if step.featureSelected():
                info = layer_cmd.featSelOut()['text']
                texts = [obj.text for obj in info]
                dict[layer] = texts
            else:
                dict[layer] = None
            step.unaffect(layer)
        step.resetFilter()
        return dict
            
    def get_week_picihao_banci_info(self, step, worklayer):
        """获取周期 批次 班次信息"""
        
        dic_info = getJobData(job.name.upper())
        if dic_info:
            ERPPeriod = dic_info["dc_format"]
            layer_side = dic_info["dc_side"].decode("utf8")
            dic_side_layer = {u"文字C面": ["c1"],
                              u"文字C面+S面": ["c1", "c2"],
                              u"文字S面": ["c2"],
                              u"蚀刻C面": ["l1"],
                              u"蚀刻S面": [outsignalLayers[-1]],
                              u"蚀刻C面+S面": outsignalLayers,
                              u"蚀刻C面+文字S面": ["l1", "c2"],
                              u"蚀刻S面+文字C面": [outsignalLayers[-1], "c1"],
                              u"防焊C面": ["m1"],
                              u"防焊S面": ["m2"],
                              u"防焊C面+S面": ["m1", "m2"],
                              }
            inplan_check_layer = dic_side_layer.get(layer_side, [])
            if worklayer in inplan_check_layer:
                return u"检测到{0}层存在动态周期{1}制作不允许输出外层带周期的LDI,由值班人员输出!".format(worklayer, ERPPeriod)
            
        step = gClasses.Step(job, step.name)
        step.open()
        step.clearAll()
        step.flatten_layer(worklayer, worklayer+"_flt")
        step.affect(worklayer+"_flt")
        
        dic_tgz_week_layers = {}
        dic_tgz_barcode_week_layers = {}
        dic_tgz_banci_layers = {}
        dic_tgz_picihao_layers = {}
        week_font = []
        
        step.resetFilter()
        step.filter_set(feat_types='text')
        step.selectAll()
        layer_cmd = gClasses.Layer(step, worklayer)
        feat_out = layer_cmd.featSelOut(units="mm")["text"]
        
        for obj in feat_out:
            for wwyy in ["$$yy", "$$ww"]:
                if wwyy in str(obj.text).replace("{", "").replace("}", "").lower():                                
                    if dic_tgz_week_layers.has_key(worklayer):
                        dic_tgz_week_layers[worklayer] += [str(obj.text).lower()]
                        week_font.append(obj.font)
                    else:
                        dic_tgz_week_layers[worklayer] = [str(obj.text).lower()]
                        week_font.append(obj.font)
                        
            for banci_pici in ["$$banci", "$$picihao"]:
                if banci_pici in str(obj.text).replace("{", "").replace("}", "").lower():
                    if banci_pici == "$$banci":                                    
                        if dic_tgz_banci_layers.has_key(worklayer):
                            dic_tgz_banci_layers[worklayer] += [str(obj.text).lower()]
                            week_font.append(obj.font)
                        else:
                            dic_tgz_banci_layers[worklayer] = [str(obj.text).lower()]
                            week_font.append(obj.font)
                            
                    if banci_pici == "$$picihao":
                        if dic_tgz_picihao_layers.has_key(worklayer):
                            dic_tgz_picihao_layers[worklayer] += [str(obj.text).lower()]
                            week_font.append(obj.font)
                        else:
                            dic_tgz_picihao_layers[worklayer] = [str(obj.text).lower()]
                            week_font.append(obj.font)                                    
                        
        feat_out = layer_cmd.featSelOut(units="mm")["barcodes"]
        for obj in feat_out:
            for wwyy in ["$$yy", "$$ww"]:                        
                if wwyy in str(obj.text).replace("{", "").replace("}", "").lower():
                    
                    if dic_tgz_barcode_week_layers.has_key(worklayer):
                        dic_tgz_barcode_week_layers[worklayer] += [str(obj.text).lower()]
                        week_font.append(obj.font)
                    else:
                        dic_tgz_barcode_week_layers[worklayer] = [str(obj.text).lower()]
                        week_font.append(obj.font)
                        
            for banci_pici in ["$$banci", "$$picihao"]:
                if banci_pici in str(obj.text).replace("{", "").replace("}", "").lower():
                    if banci_pici == "$$banci":                                    
                        if dic_tgz_banci_layers.has_key(worklayer):
                            dic_tgz_banci_layers[worklayer] += [str(obj.text).lower()]
                            week_font.append(obj.font)
                        else:
                            dic_tgz_banci_layers[worklayer] = [str(obj.text).lower()]
                            week_font.append(obj.font)
                            
                    if banci_pici == "$$picihao":
                        if dic_tgz_picihao_layers.has_key(worklayer):
                            dic_tgz_picihao_layers[worklayer] += [str(obj.text).lower()]
                            week_font.append(obj.font)
                        else:
                            dic_tgz_picihao_layers[worklayer] = [str(obj.text).lower()]
                            week_font.append(obj.font)                                      
        
        step.resetFilter()
        step.selectNone()
        step.selectSymbol("zq-2wm;zq-ewm;zq-wm", 1, 1)        
        feat_out = layer_cmd.featSelOut(units="mm")["pads"]
        for obj in feat_out:
            if obj.symbol in ["zq-2wm", "zq-ewm","zq-wm"]:                
                if dic_tgz_week_layers.has_key(worklayer):
                    dic_tgz_week_layers[worklayer] += [obj.symbol for obj in feat_out]
                else:
                    dic_tgz_week_layers[worklayer] = [obj.symbol for obj in feat_out]
                    
        if dic_tgz_week_layers or dic_tgz_barcode_week_layers or dic_tgz_banci_layers or dic_tgz_picihao_layers:
            text = dic_tgz_week_layers.values() + dic_tgz_barcode_week_layers.values() + \
                   dic_tgz_banci_layers.values() + dic_tgz_picihao_layers.values()
            return u"检测到{0}层存在动态周期{1}制作不允许输出外层带周期的LDI,由值班人员输出!".format(worklayer, list(set(text)))
        
        return 0
    
    def check_ldi_stamp(self, step, worklayer, dic_layer_info):
        
        if not dic_layer_info.get(worklayer):
            return 0
        # 其他层别不检测
        if dic_layer_info[worklayer]["layer_type"] == "other_layer":
            return 0
        
        step = gClasses.Step(job, step.name)
        step.open()
        step.clearAll()
        step.affect(worklayer)
        step.resetFilter()
        step.selectSymbol("orbldi_stamp", 1, 1)
        if step.featureSelected():
            step.selectDelete()
        step.selectSymbol("sh-sh", 1, 1)
        if step.featureSelected():
            step.selectDelete()
            
        step.resetFilter()
        step.selectSymbol("*hdi_orbldi_stamp*", 1, 1)
        if step.featureSelected():
            step.changeSymbol("*hdi_orbldi_stamp_1*")
            step.selectNone()
            step.selectSymbol("*hdi_orbldi_stamp_1*", 1, 1)
            if step.featureSelected():
                step.COM("sel_ref_feat,layers=,use=select,mode=touch,pads_as=shape,"
                         "f_types=line\;pad\;surface\;arc\;text,polarity=positive\;negative,"
                         "include_syms=,exclude_syms=")
                if step.featureSelected():
                    return u"Stamp 图形与层别：{0} 中其他pad有相交,请手动输出！".format(worklayer)
            else:
                return u"LDI stamp图形hdi_orbldi_stamp_1 不存在，请手动输出！" 
        else:
            return u"LDI stamp图形symbol 不存在，请手动输出！"
        
        return 0
            
    def check_ldi_r0_is_right(self, step, worklayer, dic_layer_info={}):
        """检测LDI r0点是否正确"""
        if not dic_layer_info.get(worklayer):
            return 0
        
        step = gClasses.Step(job, step.name)
        step.open()
        step.clearAll()
        step.affect(worklayer)
        step.resetFilter()
        print(dic_layer_info)
        if dic_layer_info[worklayer].get("core", None) == "no":
            # 监测分割靶点
            step.resetFilter()
            step.setAttrFilter(".fiducial_name,text=300.measure")
            step.selectAll()
            fg_count = step.featureSelected()
            if fg_count:
                step.selectNone()
                step.resetFilter()
                step.setAttrFilter(".fiducial_name,text=317.reg")
                step.selectAll()
                count = step.featureSelected()
                if count:
                    return u"{0}层分割设计,图形中r0(.fiducial_name=317.reg)对位靶点不应存在，请确认资料!".format(worklayer)
                
                if count % 4:
                    return u"{0}层分割图形中r0(.fiducial_name=300.measure)对位靶点数量不是4的整数倍，请确认资料!".format(worklayer)
                
                step.selectNone()
                step.resetFilter()
                step.setAttrFilter(".fiducial_name,text=300.trmv")
                step.selectAll()                
                trv_count = step.featureSelected()
                step.selectNone()
                step.resetFilter()
                step.setAttrFilter(".fiducial_name,text=300.trmh")
                step.selectAll()                
                trh_count = step.featureSelected()
                if trh_count + trv_count == 0:
                    return u"{0}层分割图形中r0(.fiducial_name=300.trmv或.fiducial_name=300.trmh)不存在，请确认资料!".format(worklayer)
                
                fg_times = fg_count / 4
                if fg_times == 1:
                    return u"{0}层分割光点数量为4，不合理，请确认资料!".format(worklayer)
                elif fg_times == 2:
                    if trh_count + trv_count != 1:
                        return u"{0}层光点数量为8应为2分割,分割线r0数量不正确,请确认资料!".format(worklayer)
                elif fg_times == 3:
                    if trh_count ==2 or trv_count == 2:
                        pass
                    else:
                        return u"{0}层光点数量为12应为3分割,分割线r0数量应横向2或纵向2,目前数量不正确,请确认资料!".format(worklayer)
                elif fg_times == 4:
                    if trh_count == 1 and trv_count == 1:
                        pass
                    else:
                        return u"{0}层光点数量为16应为4分割,分割线r0数量应横向1+纵向1,目前数量不正确,请确认资料!".format(worklayer)
                elif fg_times == 6:
                    if (trh_count == 2 and trv_count == 1) or (trh_count == 1 and trv_count == 2):
                        pass
                    else:
                        return u"{0}层光点数量为24应为6分割,分割线r0数量应横向1+纵向2或者横向2+纵向1,目前数量不正确,请确认资料!".format(worklayer)
                else:
                    return u"目前仅支持2分割及4分割,{1}层光点数量:{0} 数量不正确,请确认资料!".format(fg_count, worklayer)
                
            else:
                step.selectNone()
                step.resetFilter()
                step.filter_set(feat_types='pad', include_syms='r0')
                step.setAttrFilter(".fiducial_name,text=317.reg")
                #if dic_layer_info[worklayer]["layer_type"] == "inner":                    
                    #inn_layer = dic_layer_info[worklayer].get("inn_layer", "none")                    
                    #if step.isLayer(inn_layer):
                        #if dic_layer_info[worklayer]["layer_type"] == "inner":
                            #step.refSelectFilter(inn_layer, mode="cover")
                    #else:
                        #return u"{0}层对应的靶孔层{1} 不存在，无法检测线路r0点位置是否正常！".format(worklayer, inn_layer)                    
                #else:
                step.selectAll()
                if step.featureSelected() == 4:
                    return 0
                else:
                    return u"{0}层图形中r0(.fiducial_name=317.reg)对位靶点数量不对，请检查板边是否有以下Symbol:\
                    chris-3683symbol\; sh-pindount\; sh-dwtop2013-chris\; sh-dwbot2013-chris\; sh-dwtop2013\; dwbot2013".format(worklayer)
        
        return 0        
        
    def get_layer_pol_and_mirror(self, jobname):
        """获取层极性及镜像关系 以及外层是否二次铜
        LAYER_ORIENTATION laySide = ( '1' => 'top', '0' => 'bot');"""
        data_info = get_inplan_mrp_info(jobname.upper(), "1=1")
        cu_info = get_cu_weight(jobname.upper(), select_dic=True)
        plating_info = get_plating_type(jobname.upper())
        dic_layer_info = {}
        arraylist_log = []
        if not cu_info:           
            log = u"获取inplan 层镜像信息为空，请反馈MI是否checkin！<br>"
            arraylist_log.append(log)
            
        if not data_info:           
            log = u"获取inplan 层压合叠构信息为空，请反馈MI是否checkin！<br>"
            arraylist_log.append(log)
            
        if not plating_info:           
            log = u"获取inplan 层二次铜信息为空，请反馈MI是否checkin！<br>"
            arraylist_log.append(log)                
        
        #print plating_info
        #print cu_info
        for info in data_info:
            mrp_name = info["MRPNAME"]
            
            if "光板" in mrp_name:
                continue
            
            rout_x = info["PNLROUTX"] * 25.4
            rout_y = info["PNLROUTY"] * 25.4
            pnl_size_x = info["PNLXINCH"] * 25.4
            pnl_size_y = info["PNLYINCH"] * 25.4
            cut_x = (pnl_size_x - rout_x) * 0.5
            cut_y = (pnl_size_y - rout_y) * 0.5            
         
            FROMLAY = info["FROMLAY"].lower()
            TOLAY = info["TOLAY"].lower()
            pol = ""
            if "-" in mrp_name:
                pol = "positive"
            else:
                for dic_info in plating_info:
                    if dic_info["MRP_NAME"] == mrp_name:
                        if dic_info.get("PLATING_TYPE_", "") == 2:
                            pol = "negative"
                        else:
                            pol = "positive"
            if not pol:
                log = u"获取{0} {1}层 极性失败，请手动输出！<br>".format(FROMLAY, TOLAY)
                arraylist_log.append(log)
                
            dic_layer_info[FROMLAY] = {}
            dic_layer_info[TOLAY] = {}
            dic_mirror = {1: "no",0: "yes",}
            for layer in [FROMLAY, TOLAY]:
                dic_layer_info[layer]["pol"] = pol                
                for dic_info in cu_info:
                        if dic_info["LAYER_NAME"] == layer:
                            dic_layer_info[layer]["mirror"] = dic_mirror[dic_info["LAYER_ORIENTATION"]]
                            
                dic_layer_info[layer]["cut_x"] = cut_x
                dic_layer_info[layer]["cut_y"] = cut_y
                dic_layer_info[layer]["board_x"] = rout_x
                dic_layer_info[layer]["board_y"] = rout_y
                if rout_x == 0 and rout_y == 0:
                    dic_layer_info[layer]["board_x"] = pnl_size_x
                    dic_layer_info[layer]["board_y"] = pnl_size_y
                    
                dic_layer_info[layer]["core"] = "yes" if info["PROCESS_NUM"] == 1 else "no"
                if "-" in mrp_name:                    
                    dic_layer_info[layer]["inn_layer"] = "inn{0}{1}".format(FROMLAY[1:], TOLAY[1:])
                    dic_layer_info[layer]["layer_type"] = "inner"
                else:
                    dic_layer_info[layer]["inn_layer"] = "inn"
                    dic_layer_info[layer]["layer_type"] = "outer"
                    
                for i, name in enumerate(matrixInfo["gROWname"]):
                    if "-gk" in name and name.startswith(layer):
                        dic_layer_info[name] = {}
                        dic_layer_info[name]["mirror"] = dic_layer_info[layer]["mirror"]
                        dic_layer_info[name]["pol"] = "negative"       
                        dic_layer_info[name]["core"] = "no"
                        dic_layer_info[name]["layer_type"] = "gk"
                        dic_layer_info[name]["cut_x"] = 0
                        dic_layer_info[name]["cut_y"] = 0
                        dic_layer_info[name]["board_x"] = pnl_size_x
                        dic_layer_info[name]["board_y"] = pnl_size_y
                        
                    if "-dk" in name and name.startswith(layer):
                        dic_layer_info[name] = {}
                        dic_layer_info[name]["mirror"] = dic_layer_info[layer]["mirror"]
                        dic_layer_info[name]["pol"] = "negative"       
                        dic_layer_info[name]["core"] = "no"
                        dic_layer_info[name]["layer_type"] = "dk"
                        #dic_layer_info[name]["cut_x"] = 0
                        #dic_layer_info[name]["cut_y"] = 0
                        #dic_layer_info[name]["board_x"] = pnl_size_x
                        #dic_layer_info[name]["board_y"] = pnl_size_y
                        dic_layer_info[name]["cut_x"] = cut_x
                        dic_layer_info[name]["cut_y"] = cut_y
                        dic_layer_info[name]["board_x"] = rout_x
                        dic_layer_info[name]["board_y"] = rout_y
                        if rout_x == 0 and rout_y == 0:
                            dic_layer_info[name]["board_x"] = pnl_size_x
                            dic_layer_info[name]["board_y"] = pnl_size_y                        

            if "-" not in mrp_name:
                # 定义其他层的属性
                for i, name in enumerate(matrixInfo["gROWname"]):                    
                    if matrixInfo["gROWside"][i] in ["top", "bottom"] and matrixInfo["gROWlayer_type"][i] != "signal":
                        dic_layer_info[name] = {}
                        dic_layer_info[name]["core"] = "no"
                        dic_layer_info[name]["layer_type"] = "other_layer"
                        if name in solderMaskLayers:
                            dic_layer_info[name]["layer_type"] = "mask_layer"
                            
                        dic_layer_info[name]["mirror"] = "no" if matrixInfo["gROWside"][i] == "top" else "yes"
                        
                        dic_layer_info[name]["pol"] = "negative"
                        if "etch" in name:
                            dic_layer_info[name]["pol"] = "positive"
                            
                        dic_layer_info[name]["cut_x"] = cut_x
                        dic_layer_info[name]["cut_y"] = cut_y
                        dic_layer_info[name]["board_x"] = rout_x
                        dic_layer_info[name]["board_y"] = rout_y
                        if rout_x == 0 and rout_y == 0:
                            dic_layer_info[name]["cut_x"] = 0
                            dic_layer_info[name]["cut_y"] = 0                            
                            dic_layer_info[name]["board_x"] = pnl_size_x
                            dic_layer_info[name]["board_y"] = pnl_size_y                        
                
        return dic_layer_info, arraylist_log
    
    def add_silk_scacle_text_for_gerber_output(self, step, worklayer, add_text):
        """字符输出添加拉伸系数"""
        
        dic_symbol_info = {}
        if sys.platform == "win32":            
            symbol_info_path = "{0}/fw/lib/symbols/symbol_info.json".format(os.environ["GENESIS_DIR"])
        else:
            symbol_info_path = "/incam/server/site_data/library/symbol_info.json"
        if not os.path.exists(symbol_info_path):
            symbol_info_path = os.path.join(os.path.dirname(sys.argv[0]), "symbol_info.json")
            
        if os.path.exists(symbol_info_path):
            with open(symbol_info_path) as file_obj:
                dic_symbol_info = json.load(file_obj)
                
        drill_info_path = "d:/drill_info/drill_info.json"
        if sys.platform != "win32":
            drill_info_path = "/tmp/drill_info.json"
            
        drill_coordinate_info = {}
        if os.path.exists(drill_info_path):
            with open(drill_info_path) as file_obj:
                drill_coordinate_info = json.load(file_obj)
                
        if not drill_coordinate_info.get(job.name):
            drill_coordinate_info[job.name] = {}
            
        if not drill_coordinate_info[job.name].get(worklayer):
            drill_coordinate_info[job.name][worklayer] = []                 
        
        get_sr_area_flatten("fill", get_sr_step=True)
        
        symbolname = "rect3000x43000"
        tmp_layer = "drill_text_tmp"
        inn_layers = [lay for i, lay in enumerate(matrixInfo["gROWname"])
                      if matrixInfo["gROWcontext"][i] == "board"
                      and matrixInfo["gROWlayer_type"][i] == "drill"
                      and (re.match("^inn.*", lay))]           
        checklayer_list = tongkongDrillLayer + outsignalLayers + solderMaskLayers + \
            mai_drill_layers + mai_man_drill_layers + rout_layers + inn_layers + silkscreenLayers
        
        for layer in silkscreenLayers:
            if step.isLayer(layer+"_check_area"):
                checklayer_list.append(layer+"_check_area")
                
        if step.isLayer("fill"):
            checklayer_list.append("fill")
        
        f_xmin, f_ymin, f_xmax, f_ymax = get_profile_limits(step)
        rect= get_sr_area_for_step_include(step.name, include_sr_step=["edit", "set", "icg", "zk"])
        sr_xmin = min([min(x1, x2) for x1, y1, x2, y2 in rect])    
        sr_ymin = min([min(y1, y2) for x1, y1, x2, y2 in rect])   
        sr_xmax = max([max(x1, x2) for x1, y1, x2, y2 in rect])    
        sr_ymax = max([max(y1, y2) for x1, y1, x2, y2 in rect])       
        
        try:        
            array_mrp_info = get_inplan_mrp_info(job.name, "1=1")  
            
            dic_inner_zu = {}
            dic_sec_zu = {}
            dic_outer_zu = {}
            out_lb_x = 0
            out_lb_y = 0    
            for dic_info in array_mrp_info:
                top_layer = dic_info["FROMLAY"]
                bot_layer = dic_info["TOLAY"]
                process_num = dic_info["PROCESS_NUM"]
                mrp_name = dic_info["MRPNAME"]
                pnl_routx = round(dic_info["PNLROUTX"] * 25.4, 3)
                pnl_routy = round(dic_info["PNLROUTY"] * 25.4, 3)
                
                if process_num == 1:
                    if not dic_inner_zu.has_key(process_num):
                        dic_inner_zu[process_num] = []            
                    dic_inner_zu[process_num].append([mrp_name, top_layer, bot_layer, pnl_routx, pnl_routy, 0])
                else:
                    if "-" in mrp_name:
                        if not dic_sec_zu.has_key(process_num):
                            dic_sec_zu[process_num] = []                
                        dic_sec_zu[process_num].append([mrp_name, top_layer, bot_layer, pnl_routx, pnl_routy, 0])
                    else:
                        if not dic_outer_zu.has_key(process_num):
                            dic_outer_zu[process_num] = []                    
                        dic_outer_zu[process_num].append([mrp_name, top_layer, bot_layer, pnl_routx, pnl_routy, 0])
                        
                        out_lb_x = (f_xmax - pnl_routx) * 0.5
                        out_lb_y = (f_ymax - pnl_routy) * 0.5
        except:
            out_lb_x = 2
            out_lb_y = 2        
       
        add_x = sr_xmax + 5
        add_y = f_ymax * 0.5
        move_model_fx = "Y"
        angle = 0        
        area_x = [f_xmax - 30, f_xmax - out_lb_x, 0.25]
        area_y = [sr_ymin + 100, sr_ymax - 100, 1]

        step.clearAll()
        if not step.isLayer(tmp_layer):
            step.createLayer(tmp_layer)
            #step.affect(tmp_layer)
            #step.addRectangle(area_x[0], area_y[0], area_x[1], area_y[1])
            #step.PAUSE("ddd")
            
        msg = u"计算坐标位置失败，需人工手动输出！".encode("cp936")
        result = auto_add_features_in_panel_edge_new(step, add_x, add_y, tmp_layer,
                                                     symbolname, checklayer_list,
                                                     msg, 1, 0,  angle, 
                                                     area_x=area_x, area_y=area_y,
                                                     move_length=1, 
                                                     move_model_fx=move_model_fx,
                                                     to_sr_area=1, max_min_area_method="yes",
                                                     dic_all_symbol_info=dic_symbol_info,
                                                     manual_add="no")
        if not result:
            area_y = [sr_ymin + 10, sr_ymax - 10, 1]
            result = auto_add_features_in_panel_edge_new(step, add_x, add_y, tmp_layer,
                                                         symbolname, checklayer_list,
                                                         msg, 1, 0,  angle, 
                                                         area_x=area_x, area_y=area_y,
                                                         move_length=1, 
                                                         move_model_fx=move_model_fx,
                                                         to_sr_area=1, max_min_area_method="yes",
                                                         dic_all_symbol_info=dic_symbol_info,
                                                         manual_add="no")            
            
        if result:
            add_x, add_y, angle, _ = result
            x = add_x + 1.1
            y = add_y - 21.5
            
            if "c2" in worklayer:
                mirror = "yes"
            else:
                mirror = "no"
            step.clearAll()
            step.affect(worklayer)
            step.addText(x if mirror == "no" else x-2.54+0.3, y, add_text, 2.54, 2.54, 1,
                         angle=270,mirror=mirror )
            # step = gClasses.Step(job, step.name)
            step.resetFilter()
            step.selectSymbol("sh-dwsd2014*", 1, 1)
            if step.featureSelected():
                layer_cmd = gClasses.Layer(step, worklayer)
                feat_out = layer_cmd.featSelOut(units="mm")["pads"]
                for obj in feat_out:
                    step.addPad(obj.x, obj.y, "r9.9")
            
            #step.selectNone()
            #step.selectSymbol("r9.9", 1, 1)
            #if step.featureSelected():
                #step.COM("sel_ref_feat,layers=,use=select,mode=touch,"
                         #"pads_as=shape,f_types=line\;pad\;surface\;arc\;text,"
                         #"polarity=positive\;negative,include_syms=,exclude_syms=")
                #if step.featureSelected():
                    #step.COM("sel_copy,dx=0,dy=0")
            
            #记住坐标信息 供后续回读比对 不一致的位置来排除此位置 
            drill_coordinate_info[job.name][worklayer] = [(symbolname, add_x, add_y)]
            with open(drill_info_path, 'w') as file_obj:
                json.dump(drill_coordinate_info, file_obj)
                
        else:
            return u"添加字符拉伸系数位置无法确定，请手动输出字符层！"
                
    def genesis_output_gerber(self, *args):
        """输出gerber 测试用"""        
        jobname = args[0]
        self.colseJob(jobname)
        
        output_id = args[1]
        worklayer = args[2]
        stepname = "panel"
        job.open(0)
        if "incam" in sys.argv[1:]:
            job.VOF()
            job.COM('check_inout,mode=in,type=job,job=%s' % jobname)
            job.VON()
            
        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=mm")
        
        step.VOF()
        step.COM("config_edit,name=check_out_on_first_change,value=no,mode=user")
        step.VON()
        
        # if jobname.upper() in ["SD1024E6225A6", "DA8612OD783C3"]:
        if os.path.exists("/tmp/{0}_{1}_mem_free.log".format(jobname, worklayer)):
            if worklayer in innersignalLayers:
                if "edit" in matrixInfo["gCOLstep_name"]:                    
                    edit_step = gClasses.Step(job, "edit")
                    edit_step.open()
                    edit_step.COM("units,type=mm")
                    edit_step.clearAll()
                    edit_step.affect(worklayer)
                    edit_step.contourize()
        
        f_xmin, f_ymin, f_xmax, f_ymax = get_profile_limits(step)
        step.VOF()
        get_sr_area_flatten("fill")
        step.VON()   
        
        data_info = self.get_mysql_data(condtion="id = {0}".format(output_id))
        
        self.kill_thread = False
        
        # if sys.platform == "win32":
        thrd = threading.Thread(target=self.check_get_process_is_run_normal, args=(output_id, worklayer))
        thrd.start()
        
        dic_contourize_layer = {}
        for info in sorted(data_info, key=lambda x: x["workLevel"] * -1):            
            
            ID = info["id"]
            tmp_dir = "{0}/{1}/{2}/{3}".format(tmp_path, job.name, "gerber", ID)
                
            worklayer = worklayer.strip()
            
            if not step.isLayer(worklayer):
                log = u"输出层{0} 不存在，请检查tgz资料是否正常！<br>".format(worklayer)
                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)], condition="id={0}".format(ID))
                return
            
            dest_net_path = info["OutputPath"]
            dest_net_path2 = ur"\\192.168.2.57\临时文件夹\系列资料临时存放区\03.CAM制作资料暂放（勿删）\000勿删\GB输出测试\{0}".format(jobname.upper())
            if sys.platform != "win32":
                #if "gui_run" in sys.argv:   
                    #job.PAUSE(dest_net_path.encode("cp936"))                
                dest_net_path1 = dest_net_path.replace("\\", "/")
                dest_net_path1 = dest_net_path1.replace(ur"//192.168.2.57/临时文件夹/系列资料临时存放区/", "/windows/33.file/")
                if os.path.isfile(dest_net_path1):
                    os.unlink(dest_net_path1)

                #if "gui_run" in sys.argv:   
                    #job.PAUSE(dest_net_path1.encode("cp936"))
                    
                if not os.path.exists(dest_net_path1):
                    os.makedirs(dest_net_path1)                
                
                dest_net_path2 = dest_net_path2.replace("\\", "/")
                dest_net_path2 = dest_net_path2.replace(ur"//192.168.2.57/临时文件夹/系列资料临时存放区/", "/windows/33.file/")
                if not os.path.exists(dest_net_path2):
                    os.makedirs(dest_net_path2)
                    
                #if "gui_run" in sys.argv:   
                    #job.PAUSE(dest_net_path2.encode("cp936"))                    
            
            if worklayer in silkscreenLayers:
                scale_x = 0.9999
                scale_y = 0.9997
                if jobname[1:4] == "a86" and jobname[8:11] == "784":
                    scale_x = 0.99995
                    scale_y = 1
                    
                x_anchor = (f_xmin + f_xmax) * 0.5 / 25.4
                y_anchor = (f_ymin + f_ymax) *0.5 / 25.4
                if "Only_Compare" not in sys.argv[1:]:
                    res = self.add_silk_scacle_text_for_gerber_output(step,worklayer, "x={0} y={1}".format(scale_x, scale_y))
                    if res:
                        self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(res)], condition="id={0}".format(ID))
                        self.kill_thread = True
                        self.write_finish_log(output_id)
                        self.colseJob(jobname)                    
                        return
            else:
                scale_x = 1
                scale_y = 1
                x_anchor = 0
                y_anchor = 0
                
            start_time = self.get_current_format_time()
            step.VOF()
            
            self.write_calc_time_log(str(ID)+"_"+worklayer)
                
            step.clearAll()
            step.affect(worklayer)
            #step.contourize(accuracy=0)
            #step.COM("sel_resize,size=5,corner_ctl=no")
            #step.COM("sel_resize,size=-5,corner_ctl=yes")
            # 传入Only_Compare 环境变量 给仅回读使用 20240124 by lyh
            # if os.environ.get("Only_Compare", None) != "YES":
            if "incam" in sys.argv[1:]:
                gen_or_incam = "incampro"
            else:
                gen_or_incam = "genesis"
                
            if "Only_Compare" not in sys.argv[1:]:
                os.system("rm -rf {0}/{1}_conturize.log".format(tmp_dir, worklayer))
                log = u"{0}开始输出层{1}  {2} <br>".format(gen_or_incam, worklayer, start_time)
                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)], condition="id={0}".format(ID))
                outputgerber274x(step, worklayer, "no", scale_x, scale_y,
                                 jobname, stepname, tmp_dir, "", "", "inch",
                                 x_anchor=x_anchor, y_anchor=y_anchor)
                
            filepath = os.path.join(tmp_dir,worklayer)
            error_num = step.STATUS
            if error_num > 0 and not os.path.exists(filepath):
                dic_contourize_layer[worklayer] = "yes"
                
                with open("{0}/{1}_conturize.log".format(tmp_dir, worklayer), "w") as f:
                    f.write("yes")
                    
                step.removeLayer(worklayer+"_bak_1")
                step.copyLayer(job.name, step.name, worklayer, worklayer+"_bak_1")
                #进行sip 处理
                self.opt_layer_to_output(worklayer)
                if step.isLayer("fill"):
                    step.clearAll()
                    step.affect(worklayer+"_bak_1")
                    step.resetFilter()
                    step.filter_set(polarity='negative')
                    step.refSelectFilter("fill", mode="cover")
                    if step.featureSelected():
                        step.copySel(worklayer)
                        
                outputgerber274x(step, worklayer, "no", scale_x, scale_y,
                                 jobname, stepname, tmp_dir, "", "", "inch",
                                 x_anchor=x_anchor, y_anchor=y_anchor)
                
                error_num = step.STATUS
                if error_num > 0:
                    if "gui_run" in sys.argv:   
                        step.PAUSE(str([error_num, 1]))
                    self.get_error_log()
                        
            step.VON()
            
            filepath = os.path.join(tmp_dir,worklayer)
            #监测文件是否输出完整
            destroy_filepath = os.path.join(tmp_dir, worklayer+".xhdr")
            if os.path.exists(destroy_filepath):
                try:
                    os.unlink(filepath)
                    os.unlink(destroy_filepath)
                except:
                    pass            
            
            if "Only_Output" in sys.argv[1:]:                    
                self.kill_thread = True
                self.write_finish_log(output_id)
                self.colseJob(jobname)
                
                if os.path.exists(filepath):
                    shutil.copy(filepath, dest_net_path2+"/")
                    
                return            
            
            # 关闭型号再次打开
            self.colseJob(jobname)
            job.open(0)
            if "incam" in sys.argv[1:]:            
                job.VOF()
                job.COM('check_inout,mode=in,type=job,job=%s' % jobname)
                job.VON()      
            step = gClasses.Step(job, stepname)
            step.open()
            step.COM("units,type=mm")
            step.VOF()
            step.COM("config_edit,name=iol_fix_ill_polygon,value=yes,mode=user")
            step.COM("config_edit,name=iol_274x_ill_polygon,value=yes,mode=user")
            step.VON()
                
            start_time = self.get_current_format_time()
            log = u"{0}开始回读比对{1}  {2} <br>".format(gen_or_incam, worklayer, start_time)
            self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)], condition="id={0}".format(ID))                  
                
            self.write_calc_time_log(str(ID)+"_"+worklayer)
            
            step.VOF()
            warning_log = ""
            if os.path.exists(filepath):
                step.removeLayer(worklayer+"_compare")
                step.createLayer(worklayer+"_compare")
                # if dic_contourize_layer.get(worklayer):
                if os.path.exists("{0}/{1}_conturize.log".format(tmp_dir, worklayer)):                    
                    step.removeLayer(worklayer+"_compare_contourize")
                    step.createLayer(worklayer+"_compare_contourize")
                    os.system("rm -rf {0}/{1}_conturize.log".format(tmp_dir, worklayer))
                    
                diff_cout, diff_info,compare_status = compare_output.compare_gerber274x(jobname, step.name, worklayer,
                                                                         "no", scale_x, scale_y,
                                                                         filepath.encode("cp936").replace("\\", "/"),
                                                                         None, x_anchor, y_anchor, "layer_compare", "gerber274x")
                
                if "incam" in sys.argv[1:] and diff_cout > 0:                    
                    diff_cout,compare_status = self.check_compare_layer_diff_area(step, worklayer, worklayer+"_compare")
                    
                    
                #输出有掉pad的情况 genesis 再次优化输出
                if diff_cout > 0 and "in_pcs" in diff_info and "incam" not in sys.argv[1:] and worklayer not in silkscreenLayers:
                    self.write_calc_time_log(str(ID)+"_"+worklayer)
                    step.flatten_layer(worklayer, worklayer+"_flt")
                    # step.removeLayer(worklayer)
                    step.COM("matrix_rename_layer,job={0},matrix=matrix,layer={1},new_name={1}_bak++++".format(job.name, worklayer))                    
                    step.copyLayer(job.name, step.name, worklayer+"_flt", worklayer)
                    
                    step.clearAll()
                    step.affect(worklayer)
                    step.contourize(accuracy=0)
                    step.COM("sel_resize,size=10")
                    step.contourize(accuracy=0)
                    step.COM("sel_resize,size=-10")
                    
                    outputgerber274x(step, worklayer, "no", scale_x, scale_y,
                                     jobname, stepname, tmp_dir, "", "", "inch",
                                     x_anchor=x_anchor, y_anchor=y_anchor)
                    #再次回读
                    self.write_calc_time_log(str(ID)+"_"+worklayer)
                    self.colseJob(jobname)
                    job.open(0)
                    if "incam" in sys.argv[1:]:            
                        job.VOF()
                        job.COM('check_inout,mode=in,type=job,job=%s' % jobname)
                        job.VON()                       
                    step = gClasses.Step(job, stepname)
                    step.open()
                    step.COM("units,type=mm")
                    step.COM("config_edit,name=iol_fix_ill_polygon,value=yes,mode=user")
                    step.COM("config_edit,name=iol_274x_ill_polygon,value=yes,mode=user")
                    step.removeLayer(worklayer+"_compare")
                    step.createLayer(worklayer+"_compare")
                    step.removeLayer(worklayer+"_compare_contourize")
                    step.createLayer(worklayer+"_compare_contourize")
                    
                    diff_cout, diff_info,compare_status = compare_output.compare_gerber274x(jobname, step.name, worklayer,
                                                                                            "no", scale_x, scale_y,
                                                                                            filepath.encode("cp936").replace("\\", "/"),
                                                                                            None, x_anchor, y_anchor, "layer_compare", "gerber274x")

                if compare_status == 0 and diff_cout == 0:                            
                    self.write_finish_log(output_id+"_"+worklayer)
                    
                    shutil.copy(filepath, dest_net_path1+"/")
                    shutil.copy(filepath, dest_net_path2+"/")
                    
                    
                if compare_status > 0:
                    warning_log = u"{3} {1}输出gerber回读比对比对报内存不足,异常状态[{2}],请手动输出！{0}<br>".format(start_time, worklayer, compare_status, gen_or_incam)
                    
                if diff_cout:                            
                    warning_log = u"{3} {1}输出gerber回读比对不一致({2}),请手动输出！{0}<br>".format(start_time, worklayer, diff_info, gen_or_incam)
                    if "incam" not in sys.argv[1:]:                        
                        if os.path.exists(filepath):                        
                            os.unlink(filepath)
                        
                    self.write_finish_log(output_id+"_"+worklayer+"_diff")
            else:                    
                warning_log = u"{1} {0}层输出输出失败，请手动输出！<br>".format(worklayer, gen_or_incam)
            
            if warning_log:                        
                self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常"),
                                        u"Status = '{0}'".format(u"输出中"),
                                        u"AlarmLog = concat(AlarmLog,'{0}')".format(warning_log)],
                                       condition="id={0}".format(ID))                    
            step.VON()
            if "gui_run" in sys.argv:    
                step.PAUSE("ddd")
            
        self.kill_thread = True
        self.write_finish_log(output_id)
            
    def incampro_output_gerber(self, *args):
        """输出gerber 测试用"""        
        jobname = args[0]
        self.colseJob(jobname)
        
        output_id = args[1]
        stepname = "panel"
        job.open(0)
        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=mm")
        
        f_xmin, f_ymin, f_xmax, f_ymax = get_profile_limits(step)
        get_sr_area_flatten("fill")
        
        data_info = self.get_mysql_data(condtion="id = {0}".format(output_id))
        # data_info = [{"id": output_id,"TempOutputPath": "/tmp/{0}".format(jobname),"workLevel": 1,}]
        
        self.kill_thread = False
        
        if sys.platform == "win32":
            thrd = threading.Thread(target=self.check_get_process_is_run_normal, args=(output_id, ))
            thrd.start()
            
        for info in sorted(data_info, key=lambda x: x["workLevel"] * -1):               
            
            ID = str(info["id"])
            
            dest_net_path = os.path.join(info["TempOutputPath"], jobname)
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
                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)], condition="id={0}".format(ID))                    
                return
            
            # if info["PathType"] == u"测试":
            # 测试用
            if sys.platform == "win32":                
                output_path = r"\\192.168.2.126\workfile\lyh\output\{0}".format(jobname)
                try:
                    os.makedirs(output_path)
                except:
                    pass                      
            else:                                  
                output_path = "/id/workfile/lyh/output/{0}".format(jobname)
                try:
                    os.makedirs(output_path)
                except:
                    pass
            
            output_layers = []
            reoutput_layers_log_file = os.path.join(output_path, ID, "reoutput_layers.log")
            recompare_layers_log_file = os.path.join(output_path, ID, "recompare_layers.log")
            
            if os.path.exists(reoutput_layers_log_file):
                output_layers = [x.strip() for x in file(reoutput_layers_log_file).readlines() if x.strip()]
            else:
                output_layers = []
                
            if not os.path.exists(reoutput_layers_log_file) and not os.path.exists(recompare_layers_log_file):
                output_layers = [x for x in info["OutLayer"].split(";") if x.strip()] 

            tmp_dir = "{0}/{1}/{2}/{3}".format(tmp_path, job.name, "gerber", ID)
            #if os.path.exists(tmp_dir):
                #shutil.rmtree(tmp_dir)
            #else:
                #os.makedirs(tmp_dir)
            
            self.update_mysql_data([u"OutputStatus = '{0}'".format(incam_or_genesis+u"输出中"),
                                    u"Status = '{0}'".format(u"输出中"),
                                    "OutputStartTime = now()", ], condition="id={0}".format(ID))

            warning_log = []
            dic_contourize_layer = {}
            for worklayer in set(output_layers):
                
                worklayer = worklayer.strip()
                
                if not step.isLayer(worklayer):
                    warning_log.append( u"输出层{0} 不存在，请检查tgz资料是否正常！<br>".format(worklayer))
                    continue
                
                if worklayer in silkscreenLayers:
                    scale_x = 0.9999
                    scale_y = 0.9997
                    if jobname[1:4] == "a86" and jobname[8:11] == "784":
                        scale_x = 0.99995
                        scale_y = 1                    
                    x_anchor = (f_xmin + f_xmax) * 0.5
                    y_anchor = (f_ymin + f_ymax) *0.5
                    res = self.add_silk_scacle_text_for_gerber_output(step,worklayer, "x={0} y={1}".format(scale_x, scale_y))
                    if res:
                        self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(res)], condition="id={0}".format(ID))
                        return                      
                else:
                    scale_x = 1
                    scale_y = 1
                    x_anchor = 0
                    y_anchor = 0               
                
                start_time = self.get_current_format_time()
                log = u"开始incampro输出层{0}  {1} <br>".format(worklayer, start_time)
                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)], condition="id={0}".format(ID))
                step.VOF()
                #step.COM("config_edit,name=out_274x_stop_ill_polygon,value=yes,mode=user")
                #step.COM("config_edit,name=edt_decompose_overlap_method,value=1,mode=user")
                #if sys.platform == "win32":
                    #outputgerber274x(step, worklayer, "no", 1, 1,
                                 #jobname, stepname, tmp_dir, "", "", "inch")
                #else:
                
                self.write_calc_time_log(ID)
                    
                step.clearAll()
                step.affect(worklayer)
                step.copyLayer(job.name, step.name, worklayer, worklayer+"_check_area")            
                
                if scale_x != 1 or scale_y != 1:                    
                    outputgerber274x_incam(step, worklayer, "no", scale_x, scale_y,
                                     jobname, stepname, tmp_dir, "", "", "inch",
                                     x_anchor=x_anchor, y_anchor=y_anchor)
                else:
                    #step.contourize(accuracy=0)
                    #step.COM("sel_resize,size=5,corner_ctl=no")
                    #step.COM("sel_resize,size=-5,corner_ctl=yes")                
                    outputgerber274x(step, worklayer, "no", scale_x, scale_y,
                                     jobname, stepname, tmp_dir, "", "", "inch",
                                     x_anchor=x_anchor, y_anchor=y_anchor)
                    
                error_num = step.STATUS
                if error_num > 0:
                    dic_contourize_layer[worklayer] = "yes"
                    if error_num == 45005:
                        step.removeLayer(worklayer+"_bak_1")
                        step.copyLayer(job.name, step.name, worklayer, worklayer+"_bak_1")
                        #进行sip 处理
                        self.opt_layer_to_output(worklayer)
                        if step.isLayer("fill"):
                            step.clearAll()
                            step.affect(worklayer+"_bak_1")
                            step.resetFilter()
                            step.filter_set(polarity='negative')
                            step.refSelectFilter("fill", mode="cover")
                            if step.featureSelected():
                                step.copySel(worklayer)
                                
                        if scale_x != 1 or scale_y != 1:                    
                            outputgerber274x_incam(step, worklayer, "no", scale_x, scale_y,
                                             jobname, stepname, tmp_dir, "", "", "inch",
                                             x_anchor=x_anchor, y_anchor=y_anchor)
                        else:                        
                            outputgerber274x(step, worklayer, "no", scale_x, scale_y,
                                             jobname, stepname, tmp_dir, "", "", "inch",
                                             x_anchor=x_anchor, y_anchor=y_anchor)                        
                        error_num = step.STATUS
                        if error_num > 0:
                            if "gui_run" in sys.argv:                                
                                step.PAUSE(str([error_num, 2]))
                            self.get_error_log()                            
                    else:
                        step.removeLayer(worklayer+"_bak_1")
                        step.copyLayer(job.name, step.name, worklayer, worklayer+"_bak_1")
                        #进行sip 处理
                        self.opt_layer_to_output(worklayer)
                        if step.isLayer("fill"):
                            step.clearAll()
                            step.affect(worklayer+"_bak_1")
                            step.resetFilter()
                            step.filter_set(polarity='negative')
                            step.refSelectFilter("fill", mode="cover")
                            if step.featureSelected():
                                step.copySel(worklayer)
                                
                        if scale_x != 1 or scale_y != 1:                    
                            outputgerber274x_incam(step, worklayer, "no", scale_x, scale_y,
                                             jobname, stepname, tmp_dir, "", "", "inch",
                                             x_anchor=x_anchor, y_anchor=y_anchor)
                        else:                        
                            outputgerber274x(step, worklayer, "no", scale_x, scale_y,
                                             jobname, stepname, tmp_dir, "", "", "inch",
                                             x_anchor=x_anchor, y_anchor=y_anchor)
                        
                        error_num = step.STATUS
                        if error_num > 0:
                            if "gui_run" in sys.argv:   
                                step.PAUSE(str([error_num, 1]))
                            self.get_error_log()
                            
                step.VON() 
                
            # 关闭型号再次打开
            self.colseJob(jobname)
            job.open(0)
            step = gClasses.Step(job, stepname)
            step.open()
            step.COM("units,type=mm")
            step.COM("config_edit,name=iol_fix_ill_polygon,value=yes,mode=user")
            # step.COM("config_edit,name=edt_compare_contour_based,value=yes,mode=user")
            
            if os.path.exists(recompare_layers_log_file):                    
                for layer in file(recompare_layers_log_file).readlines():
                    if layer.strip():
                        filepath = os.path.join(output_path, ID, layer.strip())
                        if os.path.exists(filepath):
                            shutil.copy(filepath, tmp_dir)
                            output_layers.append(layer.strip())

            for worklayer in set(output_layers):
                warning_log = ""
                start_time = self.get_current_format_time()
                log = u"开始incampro回读比对{0}  {1} <br>".format(worklayer, start_time)
                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)], condition="id={0}".format(ID))                  
                    
                self.write_calc_time_log(ID)
                
                if worklayer in silkscreenLayers:
                    scale_x = 0.9999
                    scale_y = 0.9997
                    if jobname[1:4] == "a86" and jobname[8:11] == "784":
                        scale_x = 0.99995
                        scale_y = 1                    
                    x_anchor = (f_xmin + f_xmax) * 0.5
                    y_anchor = (f_ymin + f_ymax) *0.5
                else:
                    scale_x = 1
                    scale_y = 1
                    x_anchor = 0
                    y_anchor = 0               
                
                filepath = os.path.join(tmp_dir,worklayer)
                step.VOF()                    
                if os.path.exists(filepath):
                    step.removeLayer(worklayer+"_compare")
                    step.createLayer(worklayer+"_compare")
                    if dic_contourize_layer.get(worklayer):
                        step.removeLayer(worklayer+"_compare_contourize")
                        step.createLayer(worklayer+"_compare_contourize")
                        
                    diff_cout, diff_info,compare_status = compare_output.compare_gerber274x(jobname, step.name, worklayer,
                                                                             "no", scale_x, scale_y,
                                                                             filepath.encode("cp936").replace("\\", "/"),
                                                                             None, x_anchor, y_anchor, "layer_compare", "gerber274x")
                    if diff_cout:
                        diff_cout,compare_status = self.check_compare_layer_diff_area(step, worklayer, worklayer+"_compare")
                        
                    if diff_cout > 0 and "out_pcs" in diff_info:
                        step.clearAll()
                        step.affect(worklayer)
                        step.contourize(accuracy=0)
                        step.COM("sel_resize,size=2")
                        step.contourize(accuracy=0)
                        step.COM("sel_resize,size=-2")
                        diff_cout, diff_info,compare_status = compare_output.compare_gerber274x(jobname, step.name, worklayer,
                                                                                 "no", scale_x, scale_y,
                                                                                 filepath.encode("cp936").replace("\\", "/"),
                                                                                 None, x_anchor, y_anchor, "layer_compare", "gerber274x")                        
                    
                    #输出有掉pad的情况 genesis 再次优化输出
                    if diff_cout > 0 and "in_pcs" in diff_info and worklayer not in silkscreenLayers:
                        # self.write_calc_time_log(str(ID)+"_"+worklayer)
                        start_time = self.get_current_format_time()
                        log = u"开始incampro优化输出层{0}  {1} <br>".format(worklayer, start_time)
                        self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)], condition="id={0}".format(ID))
                        
                        step.flatten_layer(worklayer, worklayer+"_flt")
                        step.removeLayer(worklayer)                    
                        step.copyLayer(job.name, step.name, worklayer+"_flt", worklayer)
                        step.clearAll()
                        step.affect(worklayer)
                        step.contourize(accuracy=0)
                        step.COM("sel_resize,size=2")
                        step.contourize(accuracy=0)
                        step.COM("sel_resize,size=-2")
                        
                        outputgerber274x(step, worklayer, "no", scale_x, scale_y,
                                         jobname, stepname, tmp_dir, "", "", "inch",
                                         x_anchor=x_anchor, y_anchor=y_anchor)
                        if os.path.exists(filepath):
                            #再次回读
                            # self.write_calc_time_log(str(ID)+"_"+worklayer)
                            start_time = self.get_current_format_time()
                            log = u"开始incampro优化输出后回读层{0}  {1} <br>".format(worklayer, start_time)
                            self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)], condition="id={0}".format(ID))
                            
                            step.COM("config_edit,name=iol_fix_ill_polygon,value=yes,mode=user")
                            # step.COM("config_edit,name=iol_274x_ill_polygon,value=yes,mode=user")
                            step.removeLayer(worklayer+"_compare")
                            step.createLayer(worklayer+"_compare")
                            step.removeLayer(worklayer+"_compare_contourize")
                            # step.createLayer(worklayer+"_compare_contourize")                
                            diff_cout, diff_info,compare_status = compare_output.compare_gerber274x(jobname, step.name, worklayer,
                                                                                                    "no", scale_x, scale_y,
                                                                                                    filepath.encode("cp936").replace("\\", "/"),
                                                                                                    None, x_anchor, y_anchor, "layer_compare", "gerber274x")
                        
                    if sys.platform <> "win32":                        
                        if diff_cout and "10.3.7.10" not in localip[2]:                                
                            step.removeLayer(worklayer+"_compare")
                            step.createLayer(worklayer+"_compare")
                            diff_cout, diff_info,compare_status = compare_output.compare_gerber274x(jobname, step.name, worklayer,
                                                                                     "no", scale_x, scale_y,
                                                                                     filepath.encode("cp936").replace("\\", "/"),
                                                                                     None, x_anchor, y_anchor, "step_compare", "gerber274x")                            
                        
                    #
                    if compare_status == 0 and diff_cout == 0:
                        shutil.copy(filepath, dest_net_path)
                    
                    end_time = self.get_current_format_time()
                    if compare_status > 0:
                        warning_log = u"InCAMPro {0}  {1}输出gerber回读比对比对报内存不足,异常状态[{2}],请手动输出此层！<br>".format(end_time, worklayer, compare_status)
                        os.unlink(filepath)
                        
                    if diff_cout:                        
                        outputgerber274x(step, worklayer+"_diff", "no", 1, 1,
                                         jobname, stepname, tmp_dir, "", "", "inch",
                                         x_anchor=0, y_anchor=0)                        
                        warning_log = u"InCAMPro {0}  {1}输出gerber回读比对不一致({2}),请到compare_error夹子内回读{1}、{3}两层，检查{3}层标记区域是否异常！<br>".format(end_time, worklayer, diff_info, worklayer+"_diff_area")
                        error_dir = os.path.join(dest_net_path, "compare_error")
                        try:
                            os.makedirs(error_dir)
                        except:
                            pass
                        if os.path.exists(filepath):                            
                            shutil.copy(filepath, error_dir)
                            os.unlink(filepath)
                        else:
                            filepath = os.path.join(output_path, ID, worklayer)
                            shutil.copy(filepath, error_dir)
                            
                        compare_filepath = os.path.join(tmp_dir,worklayer+"_diff")
                        if os.path.exists(compare_filepath):
                            shutil.copy(compare_filepath, error_dir+"/"+worklayer+"_diff_area")
                            os.unlink(compare_filepath)
                            
                else:
                    # print([filepath])
                    # step.PAUSE(filepath)
                    diff_cout = 0
                    warning_log = u"InCAMPro {0}层输出失败，请手动输出此层！<br>".format(worklayer)
                
                if warning_log:
                    if diff_cout and diff_info == "in_pcs" and "10.3.7.10" in localip[2]:
                        OutputStatus = u"输出异常(in_pcs)"
                        self.write_finish_log(str(output_id) + "_in_pcs")
                    else:
                        OutputStatus = u"输出异常"
                    self.update_mysql_data([u"OutputStatus = '{0}'".format(OutputStatus),
                                            u"Status = '{0}'".format(u"输出异常"),
                                            u"AlarmLog = concat(AlarmLog,'{0}')".format(warning_log)],
                                           condition="id={0}".format(ID)) 
                step.VON()
        
        if output_layers and not warning_log:                
            for layer in output_layers:
                filepath = os.path.join(dest_net_path, layer)
                if not os.path.exists(filepath):
                    break
            else:                    
                self.update_mysql_data([u"OutputStatus = '{0}'".format(u"incam输出完成"),
                                        u"Status = '输出完成'"], condition="id={0}".format(ID))
        else:
            end_time = self.get_current_format_time()            
            success_file_in_pcs = os.path.join("/tmp", "success_{0}_in_pcs.log".format(output_id))
            if os.path.exists(success_file_in_pcs):
                OutputStatus = u"输出异常(in_pcs)"
            else:
                OutputStatus = u"输出异常"                
            
            warning_log = u"InCAMPro 程序异常，请清除异常状态重新输出试试，若还是异常，请反馈程序工程师处理！{0} <br>".format(end_time)         
            self.update_mysql_data([u"OutputStatus = '{0}'".format(OutputStatus),
                                    u"Status = '{0}'".format(u"输出异常"),
                                    u"AlarmLog = concat(AlarmLog,'{0}')".format(warning_log)],
                                   condition="id={0}".format(ID))                
            
        self.write_finish_log(output_id)
    
    def check_compare_layer_diff_area(self, step, worklayer, compare_layer):
        """检测比对层不一致地方面积 若面积区域小于12.5um (0.05mil)忽略"""
        step = gClasses.Step(job, step.name)
        if not step.isLayer(worklayer+"_diff"):
            return 1, 0
            
        step.clearAll()
        step.affect(worklayer)
        step.removeLayer(worklayer+"_flt")
        step.flatten_layer(worklayer, worklayer+"_flt")
        # step.removeLayer(worklayer)
        step.COM("matrix_rename_layer,job={0},matrix=matrix,layer={1},new_name={1}_bak++++".format(job.name, worklayer))
        
        step.copyLayer(job.name, step.name, worklayer+"_flt", worklayer)
        
        step.clearAll()
        step.affect(worklayer+"_diff")
        step.resetFilter()
        step.selectSymbol("r0", 1, 1)
        if step.featureSelected():
            step.selectDelete()
        
        step.copyToLayer(worklayer, invert="yes")
        step.copyToLayer(compare_layer, invert="yes")
        
        step.clearAll()
        step.affect(worklayer)
        step.affect(compare_layer)
        step.contourize(accuracy=0)
        step.COM("sel_resize,size=5")
        step.contourize(accuracy=0)
        step.COM("sel_resize,size=-30.4")
        step.contourize(accuracy=0)
        step.COM("sel_resize,size=25.4")
        
        step.COM("compare_layers,layer1=%s,job2=%s,step2=%s,\
        layer2=%s,layer2_ext=,tol=%s,area=global,consider_sr=yes,\
        ignore_attr=,map_layer=%s_diff2,map_layer_res=%s" % (
        worklayer, job.name, step.name, compare_layer, 25.4, worklayer, 254))
        if step.isLayer(worklayer+"_diff2"):
            
            if worklayer in silkscreenLayers:
                drill_info_path = "d:/drill_info/drill_info.json"
                if sys.platform != "win32":
                    drill_info_path = "/tmp/drill_info.json"                
                
                #gerber加系数的位置计算出来 
                drill_coordinate_info = {}
                if os.path.exists(drill_info_path):
                    with open(drill_info_path) as file_obj:
                        drill_coordinate_info = json.load(file_obj)
                
                gerber_scale_text_area = []                
                if drill_coordinate_info.get(job.name):                    
                    if drill_coordinate_info[job.name].has_key(worklayer):
                        for symbol, x, y in drill_coordinate_info[job.name][worklayer]:
                            if symbol == "rect3000x43000":
                                gerber_scale_text_area.append([x - 2 - 5, y - 23 - 5, x + 2 + 5, y + 23 + 5])
                                
                step.clearAll()       
                step.affect(worklayer+"_diff2")                    
                step.resetFilter()
                step.COM(
                    "filter_set,filter_name=popup,update_popup=no,feat_types=pad,polarity=positive")
                step.selectSymbol("r0")
                if step.featureSelected():
                    step.removeLayer("r0_tmp")
                    step.copySel("r0_tmp")
                    step.clearAll()
                    step.affect("r0_tmp")
                    step.resetFilter()
                    if gerber_scale_text_area:
                        for sr_xmin, sr_ymin, sr_xmax, sr_ymax in gerber_scale_text_area:
                            step.selectRectangle(sr_xmin, sr_ymin, sr_xmax, sr_ymax)
                            if step.featureSelected():
                                step.selectDelete()
                    
                    step.selectAll()
                    if step.featureSelected():
                        return 1, 0
                    
                return 0, 0
                    
            step.clearAll()       
            step.affect(worklayer+"_diff2")                    
            step.resetFilter()
            step.COM(
                "filter_set,filter_name=popup,update_popup=no,feat_types=pad,polarity=positive")
            step.selectSymbol("r0")
            if step.featureSelected():                    
                return 1, 0
        
        return 0, 0
        
    def output_gerber(self, *args):
        """输出gerber 测试用"""        
        jobname = args[0]
        self.colseJob(jobname)
        
        output_id = args[1]
        stepname = "panel"
        job.open(0)
        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=mm")
        
        f_xmin, f_ymin, f_xmax, f_ymax = get_profile_limits(step)
        
        data_info = self.get_mysql_data(condtion="id = {0}".format(output_id))
        
        self.kill_thread = False
        
        #if sys.platform == "win32":
            #thrd = threading.Thread(target=self.check_get_process_is_run_normal, args=(output_id, ))
            #thrd.start()
            
        try:            
            for info in sorted(data_info, key=lambda x: x["workLevel"] * -1): 
                output_layers = [x for x in info["OutLayer"].split(";") if x.strip()]              
                output_path = os.path.join(info["OutputPath"], jobname)
                try:
                    os.makedirs(output_path)
                except:
                    pass
                
                # if info["PathType"] == u"测试":
                start_calc_time = time.time()
                # 测试用
                if sys.platform == "win32":                
                    output_path = r"\\192.168.2.126\workfile\lyh\output\{0}".format(jobname)
                    try:
                        os.makedirs(output_path)
                    except:
                        pass                      
                else:                                  
                    output_path = "/id/workfile/lyh/output/{0}".format(jobname)
                    try:
                        os.makedirs(output_path)
                    except:
                        pass
                
                ID = info["id"]
                tmp_dir = "{0}/{1}/{2}/{3}".format(tmp_path, job.name, "gerber", ID)
                if os.path.exists(tmp_dir):
                    shutil.rmtree(tmp_dir)
                else:
                    os.makedirs(tmp_dir)
                
                self.update_mysql_data([u"OutputStatus = '{0}'".format(incam_or_genesis+u"输出中"),
                                        u"Status = '{0}'".format(u"输出中"),
                                        "OutputStartTime = now()", 
                                        u"AlarmLog = ''"], condition="id={0}".format(ID))
                #此状态给杀死进程使用
                self.error_status = u"输出异常(转incam输出)"
                warning_log = []
                for worklayer in output_layers:
                    
                    worklayer = worklayer.strip()
                    
                    if not step.isLayer(worklayer):
                        warning_log.append( u"输出层{0} 不存在，请检查tgz资料是否正常！<br>".format(worklayer))
                        continue
                    
                    if worklayer in silkscreenLayers:
                        scale_x = 0.9999
                        scale_y = 0.9997
                        if jobname[1:4] == "a86" and jobname[8:11] == "784":
                            scale_x = 0.99995
                            scale_y = 1                        
                        x_anchor = (f_xmin + f_xmax) * 0.5
                        y_anchor = (f_ymin + f_ymax) *0.5
                        res = self.add_silk_scacle_text_for_gerber_output(step, worklayer, "x={0} y={1}".format(scale_x, scale_y))
                        if res:
                            self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(res)], condition="id={0}".format(ID))
                            return                          
                    else:
                        scale_x = 1
                        scale_y = 1
                        x_anchor = 0
                        y_anchor = 0                   
                    
                    start_time = self.get_current_format_time()
                    log = u"开始输出层{0}  {1} <br>".format(worklayer, start_time)
                    self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)], condition="id={0}".format(ID))
                    step.VOF()
                    #step.COM("config_edit,name=out_274x_stop_ill_polygon,value=yes,mode=user")
                    #step.COM("config_edit,name=edt_decompose_overlap_method,value=1,mode=user")
                    #if sys.platform == "win32":
                        #outputgerber274x(step, worklayer, "no", 1, 1,
                                     #jobname, stepname, tmp_dir, "", "", "inch")
                    #else:
                    
                    self.write_calc_time_log(ID)
                        
                    step.clearAll()
                    step.affect(worklayer)
                    step.copyLayer(job.name, step.name, worklayer, worklayer+"_check_area")
                    #step.contourize(accuracy=0)
                    #step.COM("sel_resize,size=5,corner_ctl=no")
                    #step.COM("sel_resize,size=-5,corner_ctl=yes")
                    self.opt_layer_to_output(worklayer)
                    outputgerber274x(step, worklayer, "no", scale_x, scale_y,
                                     jobname, stepname, tmp_dir, "", "", "inch",
                                     x_anchor=x_anchor, y_anchor=y_anchor)
                        
                    error_num = step.STATUS
                    if error_num > 0:                    
                        if error_num == 45005:
                            step.removeLayer(worklayer+"_bak_1")
                            step.copyLayer(job.name, step.name, worklayer, worklayer+"_bak_1")
                            #进行sip 处理
                            self.opt_layer_to_output(worklayer)
                            if step.isLayer("fill"):
                                step.clearAll()
                                step.affect(worklayer+"_bak_1")
                                step.resetFilter()
                                step.filter_set(polarity='negative')
                                step.refSelectFilter("fill", mode="cover")
                                if step.featureSelected():
                                    step.copySel(worklayer)
                                    
                            outputgerber274x(step, worklayer, "no", scale_x, scale_y,
                                             jobname, stepname, tmp_dir, "", "", "inch",
                                             x_anchor=x_anchor, y_anchor=y_anchor)                        
                            error_num = step.STATUS
                            if error_num > 0:
                                if "gui_run" in sys.argv:                                
                                    step.PAUSE(str([error_num, 2]))
                                self.get_error_log()                            
                        else:
                            step.removeLayer(worklayer+"_bak_1")
                            step.copyLayer(job.name, step.name, worklayer, worklayer+"_bak_1")
                            #进行sip 处理
                            self.opt_layer_to_output(worklayer)
                            if step.isLayer("fill"):
                                step.clearAll()
                                step.affect(worklayer+"_bak_1")
                                step.resetFilter()
                                step.filter_set(polarity='negative')
                                step.refSelectFilter("fill", mode="cover")
                                if step.featureSelected():
                                    step.copySel(worklayer)
                            outputgerber274x(step, worklayer, "no", scale_x, scale_y,
                                             jobname, stepname, tmp_dir, "", "", "inch",
                                             x_anchor=x_anchor, y_anchor=y_anchor)
                            
                            error_num = step.STATUS
                            if error_num > 0:
                                if "gui_run" in sys.argv:   
                                    step.PAUSE(str([error_num, 1]))
                                self.get_error_log()
                                
                        # step.PAUSE(str([error_num, 3]))
                                
                    step.VON()                
                
                copyfiles = os.listdir(tmp_dir)
                if len(copyfiles) == len(output_layers):                
                    self.error_status = u"回读异常(转incam比对)"
                    
                # 关闭型号再次打开
                self.colseJob(jobname)
                job.open(0)
                step = gClasses.Step(job, stepname)
                step.open()
                step.COM("units,type=mm")
    
                for worklayer in output_layers:
                    
                    start_time = self.get_current_format_time()
                    log = u"开始输回读比对{0}  {1} <br>".format(worklayer, start_time)
                    self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(log)], condition="id={0}".format(ID))                  
                        
                    self.write_calc_time_log(ID)
                    
                    if worklayer in silkscreenLayers:
                        scale_x = 0.9999
                        scale_y = 0.9997
                        if jobname[1:4] == "a86" and jobname[8:11] == "784":
                            scale_x = 0.99995
                            scale_y = 1                        
                        x_anchor = (f_xmin + f_xmax) * 0.5
                        y_anchor = (f_ymin + f_ymax) *0.5           
                    else:
                        scale_x = 1
                        scale_y = 1
                        x_anchor = 0
                        y_anchor = 0                    
                    
                    filepath = os.path.join(tmp_dir,worklayer)
                    step.VOF()
                    if os.path.exists(filepath):
                        step.removeLayer(worklayer+"_compare")
                        step.createLayer(worklayer+"_compare")
                        diff_cout, diff_info,compare_status = compare_output.compare_gerber274x(jobname, step.name, worklayer,
                                                                                 "no", scale_x, scale_y,
                                                                                 filepath.encode("cp936").replace("\\", "/"),
                                                                                 None, x_anchor, y_anchor, "layer_compare", "gerber274x")
                        #if sys.platform <> "win32":                        
                            #if diff_cout:
                                #step.removeLayer(worklayer+"_compare")
                                #diff_cout, diff_info,compare_status = compare_output.compare_gerber274x(jobname, step.name, worklayer,
                                                                                         #"no", scale_x, scale_y,
                                                                                         #filepath.encode("cp936").replace("\\", "/"),
                                                                                         #None, x_anchor, y_anchor, "step_compare", "gerber274x")
                            
                        if compare_status > 0:
                            warning_log.append( u"{0}  {1}输出gerber回读比对比对报内存不足,请手动重新输出此层！<br>".format(start_time, worklayer))
                            
                        if diff_cout:                            
                            warning_log.append( u"{0}  {1}输出gerber回读比对不一致({2}),请手动重新输出此层！<br>".format(start_time, worklayer, diff_info))
                    else:                    
                        # step.PAUSE(worklayer)
                        warning_log.append( u"{0}层输出输出失败，请手动重新输出此层！<br>".format(worklayer))
                    step.VON()
                    
                if warning_log:
                    
                    copyfiles = os.listdir(tmp_dir)
                    if len(copyfiles) != len(output_layers):
                        self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常"),
                                                u"Status = '{0}'".format(u"输出异常"),
                                                u"AlarmLog = concat(AlarmLog,'{0}')".format("".join(warning_log))],
                                               condition="id={0}".format(ID))
                    else:
                        if sys.platform == "win32":
                            try:
                                for name in os.listdir(tmp_dir):
                                    filepath = os.path.join(tmp_dir, name)
                                    shutil.copy(filepath, output_path)
                                    print("copy {0} --> {1}".format(filepath, output_path))
                                    
                                shutil.rmtree(tmp_dir)
                            except:
                                pass                    
                            self.update_mysql_data([u"OutputStatus = '{0}'".format(u"回读异常(转incam比对)"),
                                                    u"Status = '{0}'".format(u"输出异常"),
                                                    u"AlarmLog = concat(AlarmLog,'{0}')".format("".join(warning_log))],
                                                   condition="id={0}".format(ID))
                        else:
                            self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常"),
                                                    u"Status = '{0}'".format(u"输出异常"),
                                                    u"AlarmLog = concat(AlarmLog,'{0}')".format("".join(warning_log))],
                                                   condition="id={0}".format(ID))                        
                else:
                    try:
                        copyfiles = []
                        for name in os.listdir(tmp_dir):
                            filepath = os.path.join(tmp_dir, name)
                            shutil.copy(filepath, output_path)
                            print("copy {0} --> {1}".format(filepath, output_path))
                            copyfiles.append(name)
                            
                        shutil.rmtree(tmp_dir)
                    except:
                        pass
                    if len(copyfiles) != len(output_layers):
                        not_copy_layers = [x for x in output_layers if x not in copyfiles]
                        log = u"输出文件数量{0}->[{1}]跟输出层{2}->[{3}] 不一致，请手动再次输出缺失的层[{4}] <br>".format(len(copyfiles), " ".join(copyfiles),
                                                                                                                len(output_layers), " ".join(output_layers),
                                                                                                                " ".join(not_copy_layers))
                        self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出异常"),
                                                u"Status = '{0}'".format(u"输出异常"),
                                                u"AlarmLog = concat(AlarmLog,'{0}')".format(log)],
                                                condition="id={0}".format(ID))       
                    else:
                        self.update_mysql_data([u"OutputStatus = '{0}'".format(u"输出完成"),
                                                u"Status = '输出完成'"], condition="id={0}".format(ID))
                        
                end_calc_time = time.time()
                seconds = end_calc_time - start_calc_time
                time_log = u"总耗时:{0}分钟 <br>".format(round(seconds/60, 1))
                self.update_mysql_data([u"AlarmLog = concat(AlarmLog,'{0}')".format(time_log),
                                        "OutputTime = now()", ],
                                       condition="id={0}".format(ID))               
                
            self.write_finish_log(output_id)            
            self.kill_thread = True
            step.PAUSE(str(diff_cout))
        except Exception, e:
            print(e)
            self.kill_thread = True
        
    def opt_layer_to_output(self, worklayer):
        """找出异常位置优化重新输出"""
        """{'gNOTEdate': ['12/08/2023'],
        'gNOTEuser': ['RS274X output'],
        'gNOTEtext': ['Found a contour with SIP'],
        'gNOTEtime': ['09:29:38'],
        'gNOTEy': [34.156469999999999],
        'gNOTEx': [406.809485]}
        """
        #check_stepname = self.get_error_log()
        #if check_stepname:
            #if check_stepname in matrixInfo["gCOLstep_name"]:                
                #check_step = gClasses.Step(job, check_stepname)
                #check_step.open()
                #check_step.COM("units,type=mm")
                #check_step.clearAll()
                #check_step.affect(worklayer)                
                #check_step.contourize(accuracy=0)
                #check_step.COM("sel_resize,size=2,corner_ctl=no")
                ## check_step.contourize(accuracy=0)
                #check_step.COM("sel_resize,size=-2,corner_ctl=yes")
        #else:
        for name in get_panelset_sr_step(job.name, "panel") + ["panel"]:
            check_step = gClasses.Step(job, name)
            cmd = "-t notes -e {0}/{1}/{2}/notes,units=mm".format(job.name, name, worklayer)
            dic_info = check_step.DO_INFO(cmd)            
            print (dic_info)                
            check_step = gClasses.Step(job, name)
            check_step.open()
            check_step.COM("units,type=mm")
            check_step.clearAll()
            check_step.affect(worklayer)          
            
            if worklayer in silkscreenLayers:                
                check_step.resetFilter()
                check_step.selectAll()
                check_step.filter_set(feat_types='pad', include_syms='barcode*;num_250;2dbc_*mm;r9.9')
                check_step.COM("filter_area_end,layer=,filter_name=popup,operation=unselect,area_type=none,inside_area=no,intersect_area=no")
            
            check_step.contourize(accuracy=0)
            check_step.COM("sel_resize,size=2,corner_ctl=no")
            
            if worklayer in silkscreenLayers:   
                check_step.resetFilter()
                check_step.selectAll()
                check_step.filter_set(feat_types='pad', include_syms='barcode*;num_250;2dbc_*mm;r9.9')
                check_step.COM("filter_area_end,layer=,filter_name=popup,operation=unselect,area_type=none,inside_area=no,intersect_area=no")
            
            check_step.contourize(accuracy=0)
            check_step.COM("sel_resize,size=-2,corner_ctl=yes")              
            check_step.close()          
                
            #cmd = "-t notes -e {0}/{1}/{2}/notes,units=mm".format(job.name, check_stepname, worklayer)
            #dic_info = check_step.DO_INFO(cmd)            
            ## print (dic_info)
            #sip_layer = "sip_point_tmp"
            #if dic_info:                    
                #check_step.removeLayer(sip_layer)
                #check_step.createLayer(sip_layer)
                #check_step.clearAll()
                #check_step.affect(sip_layer)
                #for i, coor_x in enumerate(dic_info["gNOTEx"]):
                    #coor_y = dic_info["gNOTEy"][i]                        
                    #check_step.addPad(coor_x, coor_y, "r100")
                
                #check_step.clearAll()
                #check_step.affect(worklayer)
                #check_step.resetFilter()
                #check_step.setSymbolFilter("hdi_orbldi*")
                #check_step.refSelectFilter(sip_layer)
                #if check_step.featureSelected():
                    #pass
                #else:
                    #check_step.selectNone()
                    
                    #check_step.contourize(accuracy=0)
                    #check_step.refSelectFilter(sip_layer)
                    #if check_step.featureSelected():
                        #check_step.COM("sel_resize,size=2")
                        
                    #check_step.refSelectFilter(sip_layer)
                    #if check_step.featureSelected():
                        #check_step.contourize(accuracy=0)

                    #check_step.refSelectFilter(sip_layer)
                    #if check_step.featureSelected():
                        #check_step.COM("sel_resize,size=-2")

        
            # check_step.removeLayer(sip_layer)
            
    def get_error_log(self):
        stepname = None
        genesis_log_lines = []
        if os.environ.get("GENESIS_PID", None) is not None:                    
            prefix_genesis = "log-genesis186"
            prefix_incam = "log-incampro186"
            if sys.platform == "win32":
                tmp_path = "c:/tmp"                        
            else:
                tmp_path = "/tmp"                        

            pid = os.environ["GENESIS_PID"]
            for name in os.listdir(tmp_path):
                if (prefix_genesis in name or
                        prefix_incam in name) and \
                   name.endswith("." + pid):

                    for line in file(tmp_path + "/" + name).readlines()[-200:]:
                        genesis_log_lines.append(line)
                        
        if genesis_log_lines:
            logs = "".join(genesis_log_lines)
            
            self.send_warnging_log(logs.replace("'", ""))
            
            for line in genesis_log_lines:
                if "The problematic contour is in Step" in line:
                    stepname = line.split()[6].replace(",", "")
                    
        return stepname

    def write_finish_log(self, output_id):
        """写入完成log"""
        success_file = os.path.join(tmp_path, "success_{0}.log".format(output_id))
        with open(success_file, "w") as f:
            f.write("")        

    def send_warnging_log(self, log):
        try:
            uploadinglog(__credits__, __version__ + log,
                         os.environ.get("STEP") or "", GEN_USER=top.getUser())
        except Exception, e:
            print e

    def setMainUIstyle(self):  # 设置风格
        file = QtCore.QFile(':/pic/fblue.qss')
        file.open(QtCore.QFile.ReadOnly)
        styleSheet = file.readAll()
        styleSheet = unicode(styleSheet, encoding='gb2312')
        QtGui.qApp.setStyleSheet(styleSheet)

if __name__ == "__main__":    
    app = QtGui.QApplication(sys.argv)
    main = engineer_output_tool()
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
    #if func is None:
        #func = "set_dl_negative_process_fill_cu"
        #args = ['100332344s0699a01', 'panel']
    ####
    # print("--------------------->", sys.argv[1:], hasattr(main, func), args)       
    if hasattr(main, func):
        if args:
            result = getattr(main, func)(*args)
        else:
            result = getattr(main, func)()

        if result:
            try:
                uploadinglog(__credits__, __version__ + " %s %s" %
                             (func, result),
                             os.environ.get("STEP") or "", GEN_USER=top.getUser())
            except Exception, e:
                print e
                
        if "gui_run" in sys.argv and "192.168.19.243" not in localip[2]:
            try:
                main.colseJob(job.name)
                pid = os.environ.get("GENESIS_PID", None)
                if pid:
                    psutil.Process(int(pid)).kill()                
                with open("c:/tmp/exit_app.log", "w") as f:
                    f.write("yes")
            except Exception as e:
                print("---------------->error", e)
                pass                
