#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = "luthersy"
__date__ = "20230103"
__version__ = "Revision: 1.0.0 "
__credits__ = u"""控深孔外层加pad """

import os
import sys
import re
if sys.platform == "win32":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package")
else:
    scriptPath = "%s/scripts" % os.environ.get('SCRIPTS_DIR', '/incam/server/site_data')
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")
    
import gClasses
from get_erp_job_info import getBackDrillDepth
from genesisPackages import job, matrixInfo, \
     lay_num, get_panelset_sr_step
from create_ui_model import showQuestionMessageInfo, \
     showMessageInfo

inplanData = getBackDrillDepth(job.name.upper())

arraylist_kz_hole_symbol = []
for i in range(len(inplanData)):
    drillSize = round(inplanData[i]['ACTUAL_DRILL_SIZE'], 3)
    through_note = ['曝光对位孔', '印刷对位孔', '限位孔', '工艺边上孔', '控深漏钻检测孔','控深漏钻监测孔',
                    '料号孔', '批号孔', '工艺边定位孔', '背钻漏钻监测孔', '背钻可视孔', 'HCT coupon定位孔',
                    '料号孔和批号孔','通孔HCT定位','通孔']
    if inplanData[i]['ERP_FINISH_SIZE_']:
        through_list = [t for t in through_note if t in inplanData[i]['ERP_FINISH_SIZE_']]
        if len(through_list) != 0:
            continue

    # 更改限位孔ERP尺寸为0.45，对应钻带为0.452,料号孔ERP尺寸为0.45，对应钻带为0.452，批号孔ERP尺寸为0.45，对应钻带为0.46
    if abs(drillSize - 0.45) < 0.0001 and inplanData[i]['ERP_FINISH_SIZE_'] == '限位孔':
        drillSize = 0.452
    if abs(drillSize - 0.45) < 0.0001 and inplanData[i]['ERP_FINISH_SIZE_'] == '料号孔':
        drillSize = 0.452
    if abs(drillSize - 0.45) < 0.0001 and inplanData[i]['ERP_FINISH_SIZE_'] == '批号孔':
        drillSize = 0.46
    # === 2020.01.08 增加料号孔和批号孔合刀的情况 ===
    if abs(drillSize - 0.45) < 0.0001 and inplanData[i]['ERP_FINISH_SIZE_'] == '料号孔和批号孔':
        drillSize = 0.46
    # ==2020.04.28 Song==
    # 增加控深深度测试孔的深度添加判断，当备注信息为控深深度测试孔，在inplan的钻咀信息的钻径大小上减0.001
    if inplanData[i]['ERP_FINISH_SIZE_']:
        if inplanData[i]['ERP_FINISH_SIZE_'] == '控深深度测试孔' \
                or inplanData[i]['ERP_FINISH_SIZE_'] == '背钻深度测试孔' \
                or inplanData[i]['ERP_FINISH_SIZE_'] == '背钻对准测试孔'\
                or inplanData[i]['ERP_FINISH_SIZE_'] == '深度测试孔控深深度测试孔'\
                or '控深深度测试孔' in inplanData[i]['ERP_FINISH_SIZE_']:
            drillSize = drillSize - 0.001
            
    arraylist_kz_hole_symbol.append("r{0}".format(drillSize*1000))

kz_drills = []
for i, name in enumerate(matrixInfo["gROWname"]):
    if matrixInfo["gROWlayer_type"][i] == "drill" and \
       matrixInfo["gROWcontext"][i] == "board":
        if name in ["cdc", "cds"] or \
           re.match("^cd[0-9]{1,2}-[0-9]{1,2}[cs]$", name):
            kz_drills.append(name)
            
if kz_drills:
    arraylist_logs = []
    dic_zu = {}
    for layer in kz_drills:
        if layer == "cdc":
            log = u"检测到{0} 控深层NPTH孔需在线路面{1} 添加比孔小0.2mm的pad".format(layer, "l1")
            arraylist_logs.append(log)
            dic_zu[layer] = "l1"
        if layer == "cds":
            log = u"检测到{0} 控深层NPTH孔需在线路面l{1} 添加比孔小0.2mm的pad".format(layer, int(lay_num))
            arraylist_logs.append(log)
            dic_zu[layer] = "l{0}".format(int(lay_num))
        result = re.match("^cd([0-9]{1,2})-([0-9]{1,2})[cs]$", layer)
        if result:
            if layer.endswith("c"):
                log = u"检测到{0} 控深层NPTH孔需在线路面l{1} 添加比孔小0.2mm的pad".format(layer, result[0])
                arraylist_logs.append(log)
                dic_zu[layer] = "l{0}".format(*result)
            if layer.endswith("s"):
                log = u"检测到{0} 控深层NPTH孔需在线路面l{1} 添加比孔小0.2mm的pad".format(layer, result[1])
                arraylist_logs.append(log)
                dic_zu[layer] = "l{1}".format(*result)
                
    if arraylist_logs:
        arraylist_logs.append(u"请检查以上信息是否正确，若不正确，请返回重新修改钻带。")
        res = showQuestionMessageInfo(*arraylist_logs)
        if res:
            if "panel" in matrixInfo["gCOLstep_name"]:
                all_steps = get_panelset_sr_step(job.name, "panel")
            else:
                all_steps = [name for name in matrixInfo["gROWname"]
                             if name not in ["orig", "net", "icg"]]
            
            for stepname in all_steps:
                step = gClasses.Step(job, stepname)
                step.open()
                step.COM("units,type=mm")
                for drill_layer, sig_layer in dic_zu.iteritems():
                    step.clearAll()
                    step.affect(drill_layer)
                    step.resetFilter()
                    step.setAttrFilter(".drill,option=non_plated")
                    step.selectSymbol(";".join(arraylist_kz_hole_symbol))
                    if step.featureSelected():
                        step.copyToLayer(sig_layer, size=-200)
                
                step.clearAll()
                
            showMessageInfo(u"运行完毕，请检查添加的pad是否异常！")
else:
    showMessageInfo(u"未发现控深钻带！")