#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------#
#               VTG.SH SOFTWARE GROUP                     #
# ---------------------------------------------------------#
# @Author       :    Song
# @Mail         :    
# @Date         :    2022/03/25
# @Revision     :    1.0.0
# @File         :    out_comp.py
# @Software     :    PyCharm
# @Usefor       :    外层线路补偿，业务与界面分离改写
# ---------------------------------------------------------#

_header = {
    'description': '''
    -> 本程序主要服务于胜宏科技（惠州），任何其他团体或个人如需使用，必须经胜宏科技（惠州）相关负责
       人及作者的批准，并遵守以下约定；
    1> 本着尊重创作者的劳动成果，任何团体或个人在使用此程序的时候，均需要知会此程序的原始创作者；
    2> 在任何场合宣导、宣传，在任何文件、报告、邮件中提及本程序的全部或部分功能，均需要声明此程序的
       原始创作者；
    3> 在任何时候对本程序做部分修改或者是升级时，必须要保留文件的原始信息，包括原始文件名、创作者及
       联系方式、创作日期等信息，且不得删除程序中的源代码，只能进行注释处理；
'''
}
# --导入Package
import sys
from PyQt4 import QtCore, QtGui
import platform
import os
import lineCompUI as L_UI
import csv
import json
from PyQt4.QtGui import QMessageBox

# --加载相对位置，以实现InCAM与Genesis共用
if platform.system() == "Windows":
    # sys.path.append('C:/genesis/sys/scripts/pythondir/')
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
    # scr_file = "C:/genesis/sys/scripts/hdi_scr/Etch/"
else:
    sys.path.append('/incam/server/site_data/scripts/Package/')

import genCOM_26
from messageBox import msgBox
import Oracle_DB

import gClasses
from genesisPackages import outsignalLayers

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s


class OutComp(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.job_name = os.environ.get('JOB')
        self.step_name = os.environ.get('STEP')
        self.GEN = genCOM_26.GEN_COM()

        self.GEN.COM('get_affect_layer')
        slayers = self.GEN.COMANS.split(' ')
        self.slayers = [x for x in slayers if x != '']
        if "autocheck" in sys.argv[1:]:
            self.slayers = [x.split("-ls")[0] for x in outsignalLayers]
        
        self.warn_list = []
        
        if len(self.slayers) == 0:
            if "autocheck" in sys.argv[1:]:
                self.warn_list.append(u'影响的工作层为空，程序退出')
                return
            else:
                msg_box = msgBox()
                msg_box.warning(self, '错误', '影响的工作层为空，程序退出', QMessageBox.Ok)
                exit(0)
        self.ui = L_UI.Ui_MainWindow()
        self.ui.setupUi(self)
        self.scrDir = os.path.split(os.path.abspath(sys.argv[0]))[0]

        self.config_file = self.scrDir + '/etch_data-hdi1-out.csv'
        if self.job_name[1:4] in ["a86", "d10"]:
            self.config_file = self.scrDir + '/etch_data-hdi1-out_nv.csv'
          
        self.out_comp_rule = []
        with open(self.config_file) as f:
            f_csv = csv.DictReader(f)
            for row in f_csv:
                self.out_comp_rule.append(row)
        # 获取铜厚范围，多层选择如果铜厚一样则合并
        get_sel_chicks = self.get_layer_copper_chink(self.slayers)
        self.combox_index = 0
        out_comp = [i['range_type'] for i in self.out_comp_rule]
        # sys.exit(0)
        if len(get_sel_chicks) == 1:

            for i, rw in enumerate(out_comp):
                min_num, max_num = float(rw[:3]), float(rw[-3:])
                if min_num <=get_sel_chicks.values()[0] < max_num:
                    self.combox_index = i + 1
        else:
            thick_index = []
            for val in get_sel_chicks.values():
                for i, rw in enumerate(out_comp):
                    min_num, max_num = float(rw[:3]), float(rw[-3:])
                    if min_num <= val < max_num:
                        thick_index.append(i)
            thick_index_numbers = list(set(thick_index))
            if len(thick_index_numbers) == 1:
                self.combox_index = thick_index_numbers[0] + 1

        print json.dumps(self.out_comp_rule, indent=2)
        self.app_version = '1.5'
        self.app_update = '2022.10.19'
        self.set_UI_by_file()

    def get_layer_copper_chink(self, sel_layers):
        think_dict = {}
        con = Oracle_DB.ORACLE_INIT()
        dbc_h = con.DB_CONNECT(host='172.20.218.193', servername='inmind.fls', port='1521',
                               username='GETDATA', passwd='InplanAdmin')
        inplan_job = self.job_name[:13].upper()
        thick_list = con.getLayerThkInfo_plate(dbc_h, inplan_job, "outer")
        for d in thick_list:
            if d['LAYER_NAME'] and d['LAYER_NAME'] in sel_layers:
                think_dict[d['LAYER_NAME']] = d['CAL_CU_THK']
        return think_dict

    def set_UI_by_file(self):

        self.ui.label_9.setText(u"版权所有：胜宏科技 版本:%s 日期：%s" % (self.app_version, self.app_update))
        self.ui.comboBox.addItems([u'请选择'] + [i['range_type'] for i in self.out_comp_rule])
        # self.ui.label_12.setText(u"当前工作层为：%s" % self.slayers)
        self.ui.label_layers.setText(str(';'.join(self.slayers)))
        self.ui.comboBox.setCurrentIndex(self.combox_index)
        if self.combox_index  != 0:
            self.Fill()
        QtCore.QObject.connect(self.ui.pushButton, QtCore.SIGNAL(_fromUtf8("clicked()")), self.on_DoIt)
        QtCore.QObject.connect(self.ui.comboBox, QtCore.SIGNAL(_fromUtf8("currentIndexChanged(int)")), self.Fill)

    def Fill(self):
        try:
            show_cu_thick = str(self.ui.comboBox.currentText())
            for index, cur_dict in enumerate(self.out_comp_rule):
                if show_cu_thick == cur_dict['range_type']:
                    self.ui.lineEdit_baseComp.setText(cur_dict['base_comp'])
                    self.ui.lineEdit_impComp.setText(cur_dict['imp_comp'])
                    self.ui.lineEdit_smallBGA.setText(cur_dict['bgalow12'])
                    self.ui.lineEdit_bigBGA.setText(cur_dict['bgaup12'])
                    self.ui.lineEdit_smallSMD.setText(cur_dict['smdlow12'])
                    self.ui.lineEdit_bigSMD.setText(cur_dict['smdup12'])
                    # === V1.3 取消铜的补偿 ===
                    # self.ui.lineEdit_cuComp.setText(cur_dict['bgalow12'])
                    self.ui.lineEdit_cuComp.setText('0')
                    # self.ui.lineEdit_otherPadComp.setText(cur_dict['base_comp'])
                    self.ui.lineEdit_otherPadComp.setText(cur_dict['smdlow12'])
        except:
                self.ui.lineEdit_baseComp.setText('')
                self.ui.lineEdit_impComp.setText('')
                self.ui.lineEdit_smallBGA.setText('')
                self.ui.lineEdit_bigBGA.setText('')
                self.ui.lineEdit_smallSMD.setText('')
                self.ui.lineEdit_bigSMD.setText('')
                # === V1.3 取消铜的补偿 ===
                # self.ui.lineEdit_cuComp.setText(cur_dict['bgalow12'])
                self.ui.lineEdit_cuComp.setText('0')
                # self.ui.lineEdit_otherPadComp.setText(cur_dict['base_comp'])
                self.ui.lineEdit_otherPadComp.setText('')

    def add_orig_line_width_attr(self):
        """运行补偿前把线路的原稿尺寸记录在属性内 20240926 by lyh"""
        job = gClasses.Job(self.job_name)
        step = gClasses.Step(job, self.step_name)
        step.open()
        step.COM("units,type=inch")
        for worklayer in self.slayers:
            step.clearAll()
            step.affect(worklayer)
            step.resetFilter()
            step.filter_set(feat_types='line;arc', polarity='positive')
            step.selectAll()
            step.resetAttr()
            if step.featureSelected():
                layer_cmd = gClasses.Layer(step, worklayer)
                feat_out = layer_cmd.featSelOut(units="inch")["lines"]
                line_symbols = list(set([obj.symbol for obj in feat_out]))
                for symbolname in line_symbols:
                    step.selectNone()
                    step.selectSymbol(symbolname)
                    if step.featureSelected():
                        step.addAttr(".orig_size_inch", attrVal=symbolname, valType='text', change_attr="yes")
                        
                    step.selectSymbol(symbolname)
                    if step.featureSelected():
                        step.addAttr(".string", attrVal="set_orig_size", valType='text', change_attr="yes")
            step.resetAttr()
        step.clearAll()
        step.resetFilter()

    def check_compensate_is_right(self):
        """检测补偿是否一致"""
        job = gClasses.Job(self.job_name)
        step = gClasses.Step(job, self.step_name)
        step.open()
        step.COM("units,type=inch")
        
        yiban_lbc = self.ui.lineEdit_baseComp.text()
        imp_lbc = self.ui.lineEdit_impComp.text()
        if not str(yiban_lbc):
            yiban_lbc = "0.2"            
            
        if not str(imp_lbc):
            imp_lbc = "0.2"
            
        for layer in self.slayers:
            step.removeLayer(layer+"_base_compensate_error_+++")
            step.clearAll()
            step.copyLayer(job.name, step.name, layer, layer+"_check")
            step.affect(layer+"_check")
            
            layer_cmd = gClasses.Layer(step, layer+"_check")
            dic_size = {"yibanline": yiban_lbc,"impline": imp_lbc,}
            base_compensate_not_same_indexes = {}
            not_orig_size_lines_info = {}
            for line_type in ["yibanline", 'impline']:
                step.removeLayer(layer+"_"+line_type+"_"+dic_size[line_type])
                not_orig_size_lines_info[line_type] = []
                step.selectNone()
                self.Adv_filter(select_type=line_type)
                if step.featureSelected():
                    select_feat = layer_cmd.featout_dic_Index(units="inch", options="feat_index+select")
                    feat_out = select_feat["lines"]
                    feat_out += select_feat["arcs"]                    
                    
                    for obj in feat_out:
                        if getattr(obj, "orig_size_inch", None) is None:
                            if not getattr(obj, "patch", None) and not getattr(obj, "tear_drop", None):
                                not_orig_size_lines_info[line_type].append(int(obj.feat_index))
                            continue
                        
                        orig_size = getattr(obj, "orig_size_inch", None)
                        if orig_size:
                            # print(obj.symbol , orig_size , dic_size[line_type] , 111111111111111)
                            if abs(float(obj.symbol[1:]) - float(orig_size[1:]) - 0.2 ) > 0.05 and \
                               float(obj.symbol[1:]) < float(orig_size[1:]) + 0.2:
                                if base_compensate_not_same_indexes.has_key(orig_size):
                                    base_compensate_not_same_indexes[orig_size].append(int(obj.feat_index))
                                else:
                                    base_compensate_not_same_indexes[orig_size] = [int(obj.feat_index)]
            
            if base_compensate_not_same_indexes:
                step.selectNone()
                bc_value = dic_size[line_type]
                for orig_size, indexes in base_compensate_not_same_indexes.iteritems():
                    step.selectNone()
                    step.resetFilter()
                    group_indexes = self.group_and_limit_numbers(indexes)
                    for group in group_indexes:
                        step.resetFilter()
                        step.COM("adv_filter_reset")
                        step.COM("adv_filter_set,filter_name=popup,active=yes,limit_box=no,bound_box=no,"
                                 "indexes={0},srf_values=no,srf_area=no,mirror=any,ccw_rotations=".format(group))
                        step.selectAll()                    
                        if step.featureSelected():
                            step.addAttr(".orig_size_inch", attrVal="orig_size={0} bc_vaule={1}"
                                         .format(orig_size, bc_value), valType='text', change_attr="yes")
                        
                        step.COM("adv_filter_reset")
                        step.COM("adv_filter_set,filter_name=popup,active=yes,limit_box=no,bound_box=no,"
                                 "indexes={0},srf_values=no,srf_area=no,mirror=any,ccw_rotations=".format(group))
                        step.selectAll()
                        if step.featureSelected():                       
                            step.copyToLayer(layer+"_base_compensate_error_+++")
                
                self.warn_list.append(u"{2}检测到{0}层线路基础补偿跟程序自动补偿有差异，请到{1}层比对检查异常位置(每根线中的属性orig_size为原稿大小，bc_vaule为自动补偿值)！！"
                                      .format(layer, layer+"_base_compensate_error_+++", step.name))
            
            step.selectNone()                    
            for line_type, indexes in not_orig_size_lines_info.iteritems():
                step.selectNone()
                if indexes:
                    group_indexes = self.group_and_limit_numbers(indexes)                            
                    for group in group_indexes:
                        step.resetFilter()
                        step.COM("adv_filter_reset")
                        step.COM("adv_filter_set,filter_name=popup,active=yes,limit_box=no,bound_box=no,"
                                 "indexes={0},srf_values=no,srf_area=no,mirror=any,ccw_rotations=".format(group))
                        step.selectAll()
                        if step.featureSelected():
                            step.copySel(layer+"_"+line_type+"_check_"+dic_size[line_type])
                
            step.removeLayer(layer+"_check")
                        
            step.clearAll()
            
    def group_and_limit_numbers(self, numbers, max_length=198):
        if not numbers:
            return []
        
        # 1. 先对数字进行排序并分组连续数字
        sorted_numbers = sorted(numbers)
        groups = []
        start = sorted_numbers[0]
        prev = start
    
        for num in sorted_numbers[1:]:
            if num == prev + 1:
                prev = num
            else:
                if start == prev:
                    groups.append(str(start))
                else:
                    groups.append("%d:%d" % (start, prev))
                start = num
                prev = num
    
        # 处理最后一组
        if start == prev:
            groups.append(str(start))
        else:
            groups.append("%d:%d" % (start, prev))
    
        # 2. 将分组用分号连接，同时限制字符串长度
        result = []
        current_str = ""
    
        for group in groups:
            # 如果是第一个分组，直接添加
            if not current_str:
                current_str = group
            else:
                # 检查添加分号和新分组后是否超过长度限制
                if len(current_str) + len(group) + 1 <= max_length:
                    current_str += ";" + group
                else:
                    result.append(current_str)
                    current_str = group
    
        # 添加最后一个字符串
        if current_str:
            result.append(current_str)
    
        return result              

    def on_DoIt(self):
        """
        执行线路补偿
        :return:
        """
        yiban_lbc = self.ui.lineEdit_baseComp.text()
        imp_lbc = self.ui.lineEdit_impComp.text()
        low_bgabc = self.ui.lineEdit_smallBGA.text()
        up_bgabc = self.ui.lineEdit_bigBGA.text()
        low_smdbc = self.ui.lineEdit_smallSMD.text()
        up_smdbc = self.ui.lineEdit_bigSMD.text()
        # === V1.3 取消铜的补偿 ===
        cu_bc = self.ui.lineEdit_cuComp.text()
        pad_bc = self.ui.lineEdit_otherPadComp.text()
        slayers = self.slayers
        
        self.add_orig_line_width_attr()
        
        self.GEN.CLEAR_LAYER()
        self.GEN.COM("units,type=inch")
        for layer in slayers:
            self.GEN.COM("affected_layer,name=%s,mode=single,affected=yes" % (layer))

        # 一般线路补偿
        self.Adv_filter(select_type='yibanline')
        if self.GEN.GET_SELECT_COUNT() != 0:
            # job.PAUSE('yiban_lbc')
            self.GEN.COM("sel_resize,size=%s,corner_ctl=no" % (yiban_lbc))

        self.GEN.COM("clear_layers")
        # 阻抗线补偿
        self.Adv_filter(select_type='impline')
        if self.GEN.GET_SELECT_COUNT() != 0:
            # job.PAUSE('imp_lbc')
            self.GEN.COM("sel_resize,size=%s,corner_ctl=no" % (imp_lbc))

        self.GEN.COM("clear_layers")
        # 大于12mil的bga，使用反选形式
        self.Adv_filter(select_type="bgapad", usesize="no")
        self.Adv_filter(select_type="bgapad", usesize="yes", minwidth="0", maxwidth="0.012", select_mode='no')
        if self.GEN.GET_SELECT_COUNT() != 0:
            # job.PAUSE('up_bga_bc')
            self.GEN.COM("sel_resize,size=%s,corner_ctl=no" % (up_bgabc))

        # 小于12mil的bga
        self.GEN.COM("clear_layers")
        self.Adv_filter(select_type="bgapad", usesize="yes", minwidth="0", maxwidth="0.012")
        if self.GEN.GET_SELECT_COUNT() != 0:
            # job.PAUSE('lowbga_bc')
            self.GEN.COM("sel_resize,size=%s,corner_ctl=no" % (low_bgabc))

        self.GEN.COM("clear_layers")
        # 大于12mil的smd，使用反选形式
        self.Adv_filter(select_type="smdpad", usesize="no")
        self.Adv_filter(select_type="smdpad", usesize="yes", minwidth="0", maxwidth="0.012", select_mode='no')
        if self.GEN.GET_SELECT_COUNT() != 0:
            # job.PAUSE('up_smd_bc')
            self.GEN.COM("sel_resize,size=%s,corner_ctl=no" % (up_smdbc))

        # 小于12mil的SMD
        self.GEN.COM("clear_layers")
        self.Adv_filter(select_type="smdpad", usesize="yes", minwidth="0", maxwidth="0.012")
        if self.GEN.GET_SELECT_COUNT() != 0:
            # job.PAUSE('lowsmd_bc')
            self.GEN.COM("sel_resize,size=%s,corner_ctl=no" % (low_smdbc))

        self.GEN.COM("clear_layers")
        # 补偿带有surface属性的铜皮
        self.Adv_filter(select_type="surfacecu")

        if self.GEN.GET_SELECT_COUNT() != 0:
            # job.PAUSE('cu_bc')
            self.GEN.COM("sel_resize,size=%s,corner_ctl=no" % (cu_bc))

        self.GEN.COM("clear_layers")
        # 补偿一般oad
        self.Adv_filter(select_type="yibanpad")
        if self.GEN.GET_SELECT_COUNT() != 0:
            # job.PAUSE('padbc')
            self.GEN.COM("sel_resize,size=%s,corner_ctl=no" % (pad_bc))

        msg_box = msgBox()
        msg_box.information(self, '提示', '层别:%s,预补偿完成' % self.slayers, QMessageBox.Ok)
        exit(0)

    def Adv_filter(self, select_type='bgapad', usesize='no', minwidth='0', maxwidth='0.012', select_mode='yes'):
        in_logic = "and"
        ex_logic = "or"
        include_attr = []
        exclude_attr = []
        if select_type == 'bgapad':
            filter_type = "lines=no,pads=yes,surfaces=no,arcs=no,text=no"
            include_attr.append(".bga")
        elif select_type == 'smdpad':
            filter_type = "lines=no,pads=yes,surfaces=no,arcs=no,text=no"
            include_attr.append(".smd")
        elif select_type == 'impline':
            filter_type = "lines=yes,pads=no,surfaces=no,arcs=yes,text=yes"
            include_attr.append(".imp_line")
        elif select_type == 'yibanline':
            filter_type = "lines=yes,pads=no,surfaces=no,arcs=yes,text=yes"
            exclude_attr.append(".imp_line")
        elif select_type == 'yibanpad':
            filter_type = "lines=no,pads=yes,surfaces=no,arcs=no,text=no"
            exclude_attr.append(".bga")
            exclude_attr.append(".smd")
            ex_logic = "or"
        elif select_type == 'surfacecu':
            filter_type = "lines=no,pads=no,surfaces=yes,arcs=no,text=no"

        if select_mode == "yes":
            select_opt = 'select'
        elif select_mode == "no":
            select_opt = 'unselect'

        self.GEN.COM("reset_filter_criteria,filter_name=,criteria=all")
        # 五种类型选哪个
        self.GEN.COM("set_filter_type,filter_name=,%s" % filter_type)
        # 正极性还是负极性
        self.GEN.COM("set_filter_polarity,filter_name=,positive=yes,negative=no")
        # profile内外
        self.GEN.COM("reset_filter_criteria,filter_name=,criteria=profile")
        self.GEN.COM("reset_filter_criteria,filter_name=popup,criteria=inc_attr")
        # 包含的属性
        if len(include_attr) != 0:
            for ii in include_attr:
                self.GEN.COM("set_filter_attributes,filter_name=popup,exclude_attributes=no,condition=no,attribute=%s,"
                             "min_int_val=0,max_int_val=0,min_float_val=0,max_float_val=0,option=,text=" % ii)
            # 包含的属性是以及还是或者的关系
            self.GEN.COM("set_filter_and_or_logic,filter_name=popup,criteria=inc_attr,logic=%s" % in_logic)
        # 不包含的属性
        self.GEN.COM("reset_filter_criteria,filter_name=popup,criteria=exc_attr")
        if len(exclude_attr) != 0:
            for ee in exclude_attr:
                self.GEN.COM("set_filter_attributes,filter_name=popup,exclude_attributes=yes,condition=no,attribute=%s,"
                             "min_int_val=0,max_int_val=0,min_float_val=0,max_float_val=0,option=,text=" % ee)
            self.GEN.COM("set_filter_and_or_logic,filter_name=popup,criteria=exc_attr,logic=%s" % ex_logic)
        # === V1.5 8mil以上线不补偿
        # if select_type == 'yibanline':
        #     self.GEN.COM("set_filter_symbols,filter_name=,exclude_symbols=no,symbols=r0.1:r%s;s0.1:s%s" % (
        #         '7.99', '7.99'))
        # else:
        #     self.GEN.COM("set_filter_symbols,filter_name=,exclude_symbols=no,symbols=")
        # http://192.168.2.120:82/zentao/story-view-7205.html 取消8mil以上线不补偿 ynh 20240807
        self.GEN.COM("set_filter_symbols,filter_name=,exclude_symbols=no,symbols=")
        # 不包含的symbol
        self.GEN.COM("set_filter_symbols,filter_name=,exclude_symbols=yes,symbols=")
        self.GEN.COM("reset_filter_criteria,filter_name=,criteria=text")
        self.GEN.COM("reset_filter_criteria,filter_name=,criteria=dcode")
        self.GEN.COM("reset_filter_criteria,filter_name=,criteria=net")
        self.GEN.COM("set_filter_length")
        self.GEN.COM("set_filter_angle")
        self.GEN.COM("adv_filter_reset")
        # 大小过滤 0-12mil box size设定
        if usesize != 'no':
            self.GEN.COM(
                "adv_filter_set,filter_name=popup,active=yes,limit_box=no,bound_box=yes,min_width=%s,max_width=%s,"
                "min_length=0,max_length=0,srf_values=no,srf_area=no,mirror=any,ccw_rotations=" % (
                    minwidth, maxwidth))

        self.GEN.COM("filter_area_strt")
        # 选择 还是不选择
        self.GEN.COM("filter_area_end,filter_name=popup,operation=%s" % select_opt)


# # # # --程序入口
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = OutComp()
    if "autocheck" in sys.argv[1:]:        
        myapp.check_compensate_is_right()
        if len(myapp.warn_list) > 0:
            #arraylist_log = []
            #for s_i in myapp.warn_list:
                #arraylist_log.append(s_i['text'])
            
            with open("/tmp/check_outer_compensate_error_{0}.log".format(myapp.job_name), "w") as f:
                f.write("<br>".join(myapp.warn_list).encode("cp936"))
        else:
            with open("/tmp/check_outer_compensate_success_{0}.log".format(myapp.job_name), "w") as f:
                f.write("yes")
            
        sys.exit(0)
    else:    
        myapp.show()
        sys.exit(app.exec_())

# Version：1.1
# Song
# 2020.06.03
# 1.增加参数05.29

# Version：1.2
# Song
# 2021.03.15
# 1.参数更改 http://192.168.2.120:82/zentao/story-view-2731.html

# Version：1.3
# Song
# 2022.03.10
# 1.不补偿铜皮 http://192.168.2.120:82/zentao/story-view-4078.html

# Version：1.4
# Song
# 2022.03.25
# 1.改写程序由line_compensation.py 更改为 out_comp.py
# 2.更改补偿参数文件由txt，更改为csv文档
# 3.更改BGA及SMD补偿 http://192.168.2.120:82/zentao/story-view-4091.html

# Version：1.5
# Song
# 2022.09.23 上线日期：2022.10.19
# 1.更改部分补偿参数：更新etch_data-hdi1-out.csv
# 2.≥8mil的线路不基础补偿 http://192.168.2.120:82/zentao/story-view-4458.html


