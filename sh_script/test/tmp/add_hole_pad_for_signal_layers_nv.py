#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = "luthersy"
__date__ = "20230103"
__version__ = "Revision: 1.0.0 "
__credits__ = u"""NV大于1mm孔对应线路加pad """

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
from genesisPackages import job, matrixInfo, \
     lay_num, get_panelset_sr_step, innersignalLayers
from create_ui_model import showQuestionMessageInfo, \
     showMessageInfo

drl_drills = []
tkykj_drills = []
for i, name in enumerate(matrixInfo["gROWname"]):
    if matrixInfo["gROWlayer_type"][i] == "drill" and \
       matrixInfo["gROWcontext"][i] == "board":
        if name in ["cdc", "cds", "2nd", "3nd"] or \
           re.match("^drl$|^drl_ccd$", name):
            if name + ".ykj" in matrixInfo["gROWname"]:
                tkykj_drills.append(name + ".ykj")
            else:
                drl_drills.append(name)
        
        if ".ykj" in name:
            tkykj_drills.append(name)

tkykj_drills = list(set(tkykj_drills))
            
if drl_drills:
    arraylist_logs = []
    dic_zu = {}
    # 20250313 zl 添加和检测只针对拼入set的 step。没有set时识别edit 提出人：翟鸣
    if "set" in matrixInfo["gCOLstep_name"]:
        all_steps = get_panelset_sr_step(job.name, "set")
    else:
        all_steps = get_panelset_sr_step(job.name, "edit")
    for stepname in list(set(all_steps)):
        step = gClasses.Step(job, stepname)
        step.open()
        step.COM("units,type=mm")
        dic_zu[stepname] = []
        step.clearAll()        
        for sig_layer in innersignalLayers:
            step.affect(sig_layer)
        step.resetFilter()
        step.filter_set(feat_types='pad;line', polarity='positive')
        step.setAttrFilter(".string,text=nv_resize_pad")
        step.selectAll()
        if step.featureSelected():
            step.selectDelete()
        
        step.removeLayer("pad_tmp")
        for drill_layer in drl_drills + tkykj_drills:
            step.clearAll()
            step.affect(drill_layer)            
            step.resetFilter()
            step.selectAll()
            layer_cmd = gClasses.Layer(step, drill_layer)
            if drill_layer in drl_drills:                
                feat_out = layer_cmd.featSelOut(units="mm")["pads"]
                if not tkykj_drills:
                    feat_out += layer_cmd.featSelOut(units="mm")["lines"]
            else:
                feat_out = layer_cmd.featSelOut(units="mm")["lines"]
            symbols = list(set([obj.symbol for obj in feat_out
                                if float(obj.symbol[1:]) >= 1000]))
            if not symbols:
                continue
            step.selectNone()
            step.selectSymbol(";".join(symbols))
            if step.featureSelected():                           
                step.copySel("pad_tmp")
                step.clearAll()
                step.affect("pad_tmp")
                step.resetFilter()
                step.selectAll()
                step.addAttr(".string", attrVal='nv_resize_pad',
                             valType='text', change_attr="yes")
        
        # 
        if step.isLayer("pad_tmp"):            
            for sig_layer in innersignalLayers:
                step.copyLayer(job.name, step.name, sig_layer, sig_layer+"_check_pad")
                step.clearAll()
                step.affect(sig_layer+"_check_pad")
                step.resetFilter()
                step.refSelectFilter("pad_tmp")
                if step.featureSelected():
                    step.VOF()
                    step.contourize(accuracy=0)
                    if step.STATUS > 0:
                        step.selectNone()
                        step.contourize()
                    step.VON()
                    
                step.clearAll()
                step.affect("pad_tmp")
                step.resetFilter()
                step.refSelectFilter(sig_layer+"_check_pad", mode="cover")
                step.COM("sel_reverse")
                #if "hct" in stepname:                    
                    #step.PAUSE(str([stepname, sig_layer]))
                    
                if step.featureSelected():
                    #layer_cmd = gClasses.Layer(step, "pad_tmp")             
                    #feat_out = layer_cmd.featSelOut(units="mm")["pads"]
                    #feat_out += [obj for obj in layer_cmd.featSelOut(units="mm")["lines"]]
                    #symbols = list(set([obj.symbol for obj in feat_out]))                    
                    dic_zu[stepname].append(sig_layer)
                    step.copyToLayer(sig_layer, size=-12*25.4)
                    
                step.removeLayer(sig_layer+"_check_pad")
        
        step.clearAll()
        step.removeLayer("pad_tmp")
        
    for key, value in dic_zu.iteritems():
        if value:            
            arraylist_logs.append(u"{0}--->{1}".format(key, value))
            
    if arraylist_logs:        
        showMessageInfo(u"运行完毕，请检查添加的pad是否异常(属性.string=nv_resize_pad)！以下step 的孔径在内层线路加了pad:<br>", *arraylist_logs)
    else:
        showMessageInfo(u"未发现资料内有大于1.0mm的npth孔！")
else:
    showMessageInfo(u"未发现通孔钻带！")