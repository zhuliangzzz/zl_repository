#!/usr/bin/env python
# -*-coding: Utf-8 -*-
# @File : check_gk_cu_areas
# @author: tiger
# @Time：2024/2/20 
# @version: v1.0
# @note: 

import os, sys,re
import platform
import math
reload(sys)
sys.setdefaultencoding('utf8')
if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package-HDI")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
import gClasses
from create_ui_model import showMessageInfo, app
from PyQt4.QtGui import QVBoxLayout,QHBoxLayout,QLineEdit,QLabel,QDialog
from PyQt4 import QtGui,QtCore
from genesisPackages import  mai_drill_layers, tongkongDrillLayer, ksz_layers,get_panelset_sr_step,laser_drill_layers

from get_erp_job_info import get_inplan_mrp_info

get_layers = sys.argv[2]
job_name = sys.argv[1]
job = gClasses.Job(job_name)
if 'panel' not in job.getSteps():
    sys.exit(0)
else:
    step = gClasses.Step(job, 'panel')
    step.open()
    step.clearAll()
    step.COM("units,type=mm")
    step.resetFilter()

class Main:
    def __init__(self):
        erros = []
        self.password = None
        rate_copper = self.get_copper_rate()
        pnl_steps = get_panelset_sr_step(job_name, step.name)
        for k_lay, v_rate in rate_copper.items():
            # 盲孔不能做镀孔
            dk_laser = []
            touch_laser = []
            if '-dk' in k_lay:
                start_num = k_lay.replace('-dk', '').replace('l','')
                for laser_name in laser_drill_layers:
                    laser_start = str(laser_name).replace('s','').split('-')[0]
                    if laser_start == start_num:
                        dk_laser.append(laser_name)
                if not dk_laser:
                    continue
                tmp_dklayer =  k_lay +'_dk_tmp1'
                step.removeLayer(tmp_dklayer)
                step.flatten_layer(k_lay, tmp_dklayer)
                # 去除切片coupon的邮票孔部分
                tmp_qp1 = k_lay + '_qp_tmp1'
                tmp_qp2 = k_lay + '_qp_tmp2'
                step.removeLayer(tmp_qp1)
                step.removeLayer(tmp_qp2)
                for s in job.getSteps():
                    if s in ['coupon-qp', 'coupon-1', 'coupon-2']:
                        stem_cmd = gClasses.Step(job, s)
                        stem_cmd.open()
                        stem_cmd.clearAll()
                        stem_cmd.resetFilter()
                        stem_cmd.COM("units,type=mm")
                        pf_qp = stem_cmd.getProfile()
                        pf_xmin = pf_qp.xmin * 25.4
                        pf_ymin = pf_qp.ymin * 25.4
                        pf_xmax = pf_qp.xmax * 25.4
                        pf_ymax = pf_qp.ymax * 25.4
                        stem_cmd.affect(k_lay)
                        stem_cmd.selectRectangle(pf_xmin + 0.5, pf_ymin + 0.5, pf_xmax - 0.5, pf_ymax - 0.5)
                        stem_cmd.COM("sel_reverse")
                        if stem_cmd.featureSelected():
                            stem_cmd.copyToLayer(tmp_qp1)
                        stem_cmd.clearAll()
                        stem_cmd.close()
                step.open()
                step.clearAll()
                step.resetFilter()
                if step.isLayer(tmp_qp1):
                    step.flatten_layer(tmp_qp1, tmp_qp2)
                    # 去除和tmp_qp2接触的
                    step.affect(tmp_dklayer)
                    step.refSelectFilter(tmp_qp2)
                    if step.featureSelected():
                        step.selectDelete()
                    step.clearAll()
                    step.removeLayer(tmp_qp1)
                    step.removeLayer(tmp_qp2)

                for laser_name in dk_laser:
                    # pnl边的孔不考虑
                    tmp_laser = laser_name +'_dk_tmp1'
                    step.removeLayer(tmp_laser)
                    step.flatten_layer(laser_name, tmp_laser)
                    step.clearAll()
                    step.affect(tmp_laser)
                    step.refSelectFilter(laser_name)
                    if step.featureSelected():
                        step.selectDelete()
                    step.selectNone()
                    step.refSelectFilter(tmp_dklayer)
                    if step.featureSelected():
                        step.PAUSE(u"盲孔不能按镀孔制作，检测到{0}中{1}存在盲孔镀孔设计，请检查！".format(k_lay, laser_name))
                        sys.exit(1)
                    else:
                        step.removeLayer(tmp_laser)
                step.removeLayer(tmp_dklayer)
                if touch_laser:
                    showMessageInfo(u"盲孔不能按镀孔制作，检测到{0}中{1}存在盲孔镀孔设计，请检查！".format(k_lay, ';'.join(touch_laser)))
                    sys.exit(1)

            # 检测是否添加铜PAD
            pf = step.getProfile()
            pf_xmin = pf.xmin * 25.4
            pf_ymin = pf.ymin * 25.4
            pf_xmax = pf.xmax * 25.4
            pf_ymax = pf.ymax * 25.4
            if 'dk' in k_lay:
                step.clearAll()
                step.getProfile()
                step.affect(k_lay)
                step.filter_set(feat_types='pad;line;surface')
                step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.pattern_fill")
                for tur in [(pf_xmin, pf_ymin, pf_xmin + 80, pf_ymax),
                            (pf_xmin, pf_ymin, pf_xmax, pf_ymin + 80),
                            (pf_xmin, pf_ymax - 80, pf_xmax, pf_ymax),
                            (pf_xmax - 80, pf_ymin, pf_xmax, pf_ymax)]:
                    step.selectNone()
                    step.selectRectangle(tur[0],tur[1],tur[2],tur[3])
                    if step.featureSelected() < 5000:
                        showMessageInfo(u"{0}层未添加抢电PAD或部分区域添加不完整，请检查，程序退出".format(k_lay))
                        step.display(k_lay)
                        sys.exit(1)
            step.clearAll()
            step.resetFilter()
            # {'l1-dk': {'pr': ["'17.4%'"], 'ar': ["'0.8'"]}, 'l22-dk': {'pr': ["'17.4%'"], 'ar': ["'0.8'"]}}
            if not v_rate['pr']  or not v_rate['ar'] :
                if v_rate['pr'] is None:
                    erros.append(u"%s层没有添加铜面积百分比" % k_lay)
                else:
                    erros.append(u"%s层没有添加铜面积" % k_lay)
            else:
                if len(v_rate['pr']) > 1:
                    erros.append(u"%s层存在多种铜面积百分比，且数据不一致" % k_lay)
                if len(v_rate['ar']) > 1:
                    erros.append(u"%s层存在多种铜面积，且数据不一致" % k_lay)
        if not erros:
            #添加了铜面积则实际运行看是否有差异
            get_areas = self.re_count_area()
            # 两者对比 all_get[b_layer] = {'area': area, 'percent': PerCent}
            # {'l16-gk': {'pr': [], 'ar': []}, 'l1-gk': {'pr': [], 'ar': []}}
            for k_lay, d_val in rate_copper.items():
                per_add = str(d_val['pr'][0]).replace('%' ,'').replace("'",'')
                areas_add = str(d_val['ar'][0]).replace("'",'')
                if get_areas.has_key(k_lay):
                    per_calc = get_areas[k_lay]['percent']
                    areas_calc = get_areas[k_lay]['area']
                    if abs(float(per_add) - float(per_calc)) > 1:
                        erros.append(u"{0}层资料上铜面积百分比为{1},程序计算为{2}，两者不一致！".format(k_lay,per_add,per_calc))
                    if abs(float(areas_add) - float(areas_calc)) > 0.02:
                        erros.append(u"{0}层资料上铜面积为{1},程序计算为{2}，两者不一致！".format(k_lay,areas_add, areas_calc))

        if erros:
            # showMessageInfo(*(erros))
            win = PassWrod(erros)
            win.show()
            win.move(550, 300)
            win.exec_()
            if win.pw != 'sh-pw':
                sys.exit(1)
            sys.exit(0)
        else:
            sys.exit(0)
            # self.re_count_area(rate_copper)

    def re_count_area(self):
        """
        重新计算铜面积
        """
        all_get = {}
        dklayers = str(get_layers).split(':')
        mrp_info = get_inplan_mrp_info(job_name)
        if not mrp_info:
            return {}
        dict_dklayer = {}
        for mrp in mrp_info:
            from_layer = str(mrp['FROMLAY']).lower().strip()
            to_layer = str(mrp['TOLAY']).lower().strip()
            key = from_layer + to_layer
            dk_list = []
            for dk in dklayers:
                if from_layer == dk.split('-')[0]:
                    dk_list.append(dk)
            for dk in dklayers:
                if to_layer in dk.split('-')[0]:
                    dk_list.append(dk)
            if dk_list:
                if len(dk_list) == 2:
                    dict_dklayer[key] = {'layers': dk_list, 'thick': mrp['YHTHICK'], 'cutx': mrp['PNLROUTX'],
                                         'cuty': mrp['PNLROUTY']}

        for i, dict_sel in enumerate(dict_dklayer.values()):
            # 计算镀孔层对应的钻孔层
            t_layer, b_layer = dict_sel['layers']
            t_num, b_num = int(str(t_layer).split('-')[0].replace('l', '')), int(str(b_layer).split('-')[0].replace('l', ''))
            sel_drill = []
            if t_num == 1:
                if 'drl' in tongkongDrillLayer:
                    sel_drill.append('drl')
                if 'cdc' in ksz_layers:
                    sel_drill.append('cdc')
                if 'cds' in ksz_layers:
                    sel_drill.append('cds')
            else:
                # 查看是否存在埋孔层
                mai_drill = 'b{0}-{1}'.format(t_num, b_num)
                if mai_drill in mai_drill_layers:
                    sel_drill.append(mai_drill)

            step.open()
            step.clearAll()
            step.resetFilter()
            step.COM("units,type=mm")
            t_layer, b_layer = dict_sel['layers']
            thick_board = float(dict_sel['thick']) * 1000
            step.COM("matrix_layer_type,job={0},matrix=matrix,layer={1},type=signal".format(job_name,t_layer))
            step.COM("matrix_layer_type,job={0},matrix=matrix,layer={1},type=signal".format(job_name, b_layer))
            back_drl_list = []
            if sel_drill:
                for dr in sel_drill:
                    back_layer = dr + 'calcooper'
                    back_drl_list.append(back_layer)
                    step.removeLayer(back_layer)
                    step.flatten_layer(dr, back_layer)
                    step.COM("matrix_layer_type,job={0},matrix=matrix,layer={1},type=drill".format(job_name, back_layer))
                    step.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=board".format(job_name,back_layer))
                    step.COM("matrix_layer_drill,job={0},matrix=matrix,layer={1},start={2},end={3}".format(job_name,back_layer,t_layer,b_layer))
            str_drill_list = '\;'.join(back_drl_list)
            if not sel_drill:
                incolse_drill = 'no'
            else:
                incolse_drill = 'yes'
            # step.PAUSE(str_drill_list)
            step.COM("copper_area,layer1={0},layer2={1},drills={2},consider_rout=no,ignore_pth_no_pad=yes,drills_source=matrix,"
                     "drills_list={3},thickness={4},resolution_value=25.4,x_boxes=3,y_boxes=3,area=no,dist_map=yes,out_file=/tmp/copper_result,out_layer=first"
                     .format(t_layer,b_layer,incolse_drill, str_drill_list, thick_board))
            area, PerCent = self.get_copper_area()
            all_get[t_layer] = {'area' : area , 'percent': PerCent }
            step.COM(
                "copper_area,layer1={0},layer2={1},drills={2},consider_rout=no,ignore_pth_no_pad=yes,drills_source=matrix,"
                "drills_list={3},thickness={4},resolution_value=25.4,x_boxes=3,y_boxes=3,area=no,dist_map=yes,out_file=/tmp/copper_result,out_layer=second"
                .format(t_layer, b_layer, incolse_drill, str_drill_list, thick_board))
            area, PerCent = self.get_copper_area()
            all_get[b_layer] = {'area': area, 'percent': PerCent}
            step.COM("matrix_layer_type,job={0},matrix=matrix,layer={1},type=solder_paste".format(job_name, t_layer))
            step.COM("matrix_layer_type,job={0},matrix=matrix,layer={1},type=solder_paste".format(job_name, b_layer))
            if back_drl_list:
                for dr in back_drl_list:
                    step.removeLayer(dr)

        return all_get

    def get_copper_rate(self):
        """获取板内是否已经添加铜面积"""
        dict={}
        for layer in str(get_layers).split(':'):
            per, area = [], []
            layer_cmd = gClasses.Layer(step, layer)
            step.affect(layer)
            step.resetFilter()
            step.filter_set(feat_types='text')
            # 百分比
            step.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=.area_name,text=copper_rate')
            step.selectAll()
            if step.featureSelected():
                info = layer_cmd.featSelOut()['text']
                texts = [obj.text for obj in info]
                per = list(set(texts))
            step.resetFilter()
            step.selectNone()
            step.filter_set(feat_types='text')
            # 实际面积大小
            step.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=.area_name,text=copper_area')
            step.selectAll()
            if step.featureSelected():
                info = layer_cmd.featSelOut()['text']
                texts = [obj.text for obj in info]
                area = list(set(texts))
            step.unaffect(layer)
            dict[layer] = {'pr' : per, 'ar' : area}
        step.resetFilter()
        return dict

    def get_copper_area(self):
        with open('/tmp/copper_result', 'r') as f:
            lines = f.readlines()
        area, PerCent = None, None
        for line in lines:
            if re.search('Total copper', line):
                area = str(round(float(line.split(':')[1].split()[0].strip()) / 92903.04, 2))
            if re.search('Percentage', line):
                PerCent = str(round(float(line.split(':')[1].strip()), 1))
        return area, PerCent

class PassWrod(QDialog):
    def __init__(self, info_x):
        super(PassWrod,self).__init__()
        self.erros = info_x
        self.pw = ''
        self.setupUi()

    def setupUi(self):
        self.setFixedSize(500,250)
        self.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        font = QtGui.QFont()
        self.setWindowTitle(u"解锁设定")
        self.vh = QVBoxLayout()
        self.plainTextEdit = QtGui.QPlainTextEdit()
        self.plainTextEdit.setPlainText("检测到:\n\n  " + '\n  '.join(self.erros) + '\n\n\n' + '  点击取消返回修改铜面积，否则请输入密码解锁')
        self.plainTextEdit.setMaximumSize(QtCore.QSize(480, 220))
        self.plainTextEdit.setStyleSheet(("color: rgb(255, 0, 0);"))
        self.plainTextEdit.setReadOnly(True)
        self.vh.addWidget(self.plainTextEdit)
        lb=QLabel(u"放行请输入密码:")
        font.setPointSize(12)
        lb.setFont(font)
        self.lineEdit_pw = QLineEdit()
        self.lineEdit_pw.setFont(font)
        self.lineEdit_pw.setEchoMode(QLineEdit.Password)
        vh = QHBoxLayout()
        vh.addWidget(lb)
        vh.addWidget(self.lineEdit_pw)
        self.vh.addLayout(vh)
        self.setLayout(self.vh)
        self.buttonBox = QtGui.QDialogButtonBox()
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok)
        self.vh.addWidget(self.buttonBox)
        self.buttonBox.accepted.connect(self.apply)  # 确定
        self.buttonBox.rejected.connect(self.exit_win)  # 取消
        self.lineEdit_pw.returnPressed.connect(self.apply)

    def apply(self):
        self.pw = self.lineEdit_pw.text()
        # 放行密码
        if self.pw == 'sh-pw':
            self.close()
        else:
            showMessageInfo(u"密码不正确，请重新输入！")

    def exit_win(self):
        self.pw = ''
        self.close()

if __name__ == "__main__":
    Main()
