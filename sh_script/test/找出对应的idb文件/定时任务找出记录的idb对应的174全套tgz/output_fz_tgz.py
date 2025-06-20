#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = "luthersy"
__date__ = "20230616"
__version__ = "Revision: 1.0.0 "
__credits__ = u"""自动输出飞针tgz资料 """

import os
import sys
if sys.platform == "win32":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package")
else:
    scriptPath = "%s/scripts" % os.environ.get('SCRIPTS_DIR', '/incam/server/site_data')
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")
    
import gClasses
import shutil
import socket
from genesisPackages import job, matrixInfo, get_panelset_sr_step, \
     signalLayers, solderMaskLayers
# from scriptsRunRecordLog import uploadinglog

localip = socket.gethostbyname_ex(socket.gethostname())
computer_id = localip[2][0]

all_drillLayer = [lay for i, lay in enumerate(matrixInfo["gROWname"])

                 if matrixInfo["gROWcontext"][i] == "board"

                 and matrixInfo["gROWlayer_type"][i] == "drill"] 

from create_ui_model import showMessageInfo, \
     QtGui, Qt, widget, QtCore

if "combine" in sys.argv[1:]:
    showMessageInfo(u"确定后，即将输出飞针测试资料！！")

if "172.28.30" in computer_id:
    db = "db3"
else:
    db = "db1"
    
job.COM("copy_entity,type=job,source_job={0},"
        "source_name={0},dest_job={1},"
        "dest_name={1},dest_database={2},"
        "remove_from_sr=yes".format(job.name, job.name+"-et", db))

jobname = job.name + "-et"
job = gClasses.Job(jobname)
job.open(1)

if not job.name.endswith("-et"):
    showMessageInfo(u"飞针电测资料输出要修改edit，且会保存输出，请将型号名命名成：-et 结尾的非正式型号！")
    sys.exit()
    
set_step = "set"
if set_step not in matrixInfo["gCOLstep_name"]:
    set_step = "edit"
    #showMessageInfo(u"set不存在，暂时不能输出飞针资料！")
    #sys.exit()    

if set_step not in matrixInfo["gCOLstep_name"]:
    showMessageInfo(u"edit跟set都不存在，请检查！")
    sys.exit()
    
orig_steps = []
edit_steps = []
while not orig_steps or not edit_steps:
    
    dialog = QtGui.QDialog()
    layerout = QtGui.QGridLayout()
    label = QtGui.QLabel(u"请选择原稿跟工作稿step，若有多个step的请按住CTRL多选")
    orig_widget = QtGui.QListWidget()
    edit_widget = QtGui.QListWidget()
    orig_widget.setSelectionMode(3)
    edit_widget.setSelectionMode(3)
    label1 = QtGui.QLabel(u"原稿step:")
    label2 = QtGui.QLabel(u"工作稿step:")
    start_btn = QtGui.QPushButton(u"开始输出")
    end_btn = QtGui.QPushButton(u"退出")
    start_btn.clicked.connect(dialog.accept)
    end_btn.clicked.connect(sys.exit)
    start_btn.setFixedWidth(150)
    end_btn.setFixedWidth(120)
    layerout.addWidget(label, 0, 0, 1, 2)
    layerout.addWidget(label1, 1, 0, 1, 1)
    layerout.addWidget(label2, 1, 1, 1, 1)
    layerout.addWidget(orig_widget, 3, 0, 1, 1)
    layerout.addWidget(edit_widget, 3, 1, 1, 1)
    layerout.addWidget(start_btn, 4, 0, 1, 1)
    layerout.addWidget(end_btn, 4, 1, 1, 1)
    dialog.setLayout(layerout)
    
    edit_step = "edit"
    for name in matrixInfo["gCOLstep_name"]:
        if edit_step in name:
            edit_widget.addItem(name)
    
    for index in range(edit_widget.count()):
        item = edit_widget.item(index)
        if item.text() == edit_step:
            edit_widget.setCurrentRow(index)
            
    orig_step = "orig"
    for name in matrixInfo["gCOLstep_name"]:
        if orig_step in name:
            orig_widget.addItem(name)
            
    for index in range(orig_widget.count()):
        item = orig_widget.item(index)
        if item.text() == orig_step:
            orig_widget.setCurrentRow(index)
   
    dialog.exec_()
    
    for item in orig_widget.selectedItems():
        # item = orig_widget.item(index)
        orig_steps.append(str(item.text()))
        
    for item in edit_widget.selectedItems():
        # item = edit_widget.item(index)
        edit_steps.append(str(item.text()))
        
    if not orig_steps or not edit_steps:
        showMessageInfo(u"原稿step 或工作稿step 没选择，请检查！")
    
all_steps = [set_step] + orig_steps

job.open(1)
step = gClasses.Step(job, set_step)
step.open()
step.COM("units,type=mm")

drill_layer = "drl"
if not step.isLayer(drill_layer):
    drill_layer = "cdc"
    if not step.isLayer(drill_layer):
        drill_layer = "cds"
        if not step.isLayer(drill_layer):
            items = matrixInfo["gCOLstep_name"]
            item, okPressed = QtGui.QInputDialog.getItem(widget,
                                                         u"提示", u"请选择通孔钻带层:",
                                                         items, 0, False,
                                                         Qt.Qt.WindowStaysOnTopHint)
            if not okPressed:
                sys.exit()        
            drill_layer = str(item)

if set_step == "set":    
    for layer in [drill_layer, "ww"]:    
        step.flatten_layer(layer, layer+"_tmp")
        step.copyLayer(job.name, step.name, layer+"_tmp", layer)
        step.removeLayer(layer+"_tmp")
        
    #step.flatten_layer("m1", "m1_et")
    #step.flatten_layer("m2", "m2_et")
    for layer in solderMaskLayers:
        step.flatten_layer(layer, layer+"_et")
    
    for name in edit_steps:    
        job.removeStep(name)
        
    for layer in all_drillLayer + signalLayers + solderMaskLayers:    
        step.flatten_layer(layer, layer+"_tmp")
        step.copyLayer(job.name, step.name, layer+"_tmp", layer)
        step.removeLayer(layer+"_tmp")
else:
    all_steps = orig_steps  
    #step.clearAll()
    #step.flatten_layer("m1", "m1_et")
    #step.flatten_layer("m2", "m2_et")
    #for layer in signalLayers + all_drillLayer:
        #if layer == drill_layer:
            #continue
        #step.affect(layer)
    
    #step.selectDelete()
    
all_layers = [drill_layer, "ww"] + all_drillLayer + signalLayers + solderMaskLayers
if set_step == "set":    
    for layer in solderMaskLayers:
        all_layers.append(layer+"_et")
        
#all_layers.append("m1_et")
#all_layers.append("m2_et")
#step.clearAll()
#for i, layer in enumerate(matrixInfo["gROWname"]):
    #if matrixInfo["gROWcontext"][i] == "board":
        #step.copyLayer(job.name, orig_step, layer, layer)        
        
#for i, layer in enumerate(matrixInfo["gROWname"]):
    #if matrixInfo["gROWcontext"][i] == "board":
        #step.affect(layer)

#step.COM("clip_area_end,layers_mode=affected_layers,layer=,"
         #"area=profile,area_type=rectangle,inout=outside,"
         #"contour_cut=yes,margin=50.8,feat_types=line\;pad\;surface\;arc\;text,"
         #"pol_types=positive\;negative")

job.save()
output_dir = "/tmp/"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
    
job.COM("export_job,job={0},path={1},mode=tar_gzip,submode=partial,"
        "steps_mode=include,steps={2},lyrs_mode=include,lyrs={3},"
        "overwrite=yes".format(job.name, output_dir, ";".join(all_steps), ";".join(all_layers)))
job.close(1)
job.COM("delete_entity,job={0},name={0},type=job".format(job.name))

tgz_path = os.path.join(output_dir, job.name+".tgz")
dest_dir = ur"/windows/174.file/ET测试资料/{0}/{1}".format(job.name[1:4], job.name.split("-")[0])
if not os.path.exists(dest_dir):
    os.makedirs(dest_dir)
    
dest_path = ur"{0}/{1}.tgz".format(dest_dir, job.name.split("-")[0])
if os.path.exists(tgz_path):
    shutil.copy(tgz_path, dest_path)
    net_picture_dir = ur"/windows/174.file/Drawing/{0}系列".format(job.name[1:4].upper())
    if not os.path.exists(net_picture_dir):
        net_picture_dir = ur"/windows/174.file/Drawing/{0}系列".format(job.name[1:4])
        
    if os.path.exists(net_picture_dir):
        if os.path.exists(os.path.join(dest_dir, u"开短路图片明细")):
            shutil.rmtree(os.path.join(dest_dir, u"开短路图片明细"))        
        for name in os.listdir(net_picture_dir):
            if job.name.split("-")[0].lower() in name.lower():
                job_dir = os.path.join(net_picture_dir, name)
                for root, dirs, files in os.walk(job_dir):
                    for dirname in dirs:
                        if "et".lower() == dirname.lower():
                            shutil.copytree(os.path.join(root, dirname), os.path.join(dest_dir, u"开短路图片明细"))
                            break
                break
        
    showMessageInfo(ur"输出成功：\\192.168.2.174\GCfiles\ET测试资料\{0}\{1}\{1}.tgz".format(job.name[1:4], job.name.split("-")[0]))
    os.system("rm -rf {0}".format(tgz_path))
else:
    showMessageInfo(u"输出异常，请反馈程序工程师查看")
