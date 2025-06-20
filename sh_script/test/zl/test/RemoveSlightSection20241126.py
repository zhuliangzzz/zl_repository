#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:RemoveSlightSection20241125.py
   @author:zl
   @time: 2024/11/22 12:09
   @software:PyCharm
   @desc:
"""
import math
import os
import re
import sys
import platform
reload(sys)
sys.setdefaultencoding('utf8')
from PyQt4 import QtCore, QtGui, Qt

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
    sys.path.append(r"\\192.168.2.33\incam-share\incam\Path\OracleClient_x86\instantclient_11_1")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

# from create_ui_model import showMessageInfo
import genClasses_zl as gen
from genCOM_26 import GEN_COM
GEN = GEN_COM()
import Oracle_DB
# from genesisPackages import outsignalLayers
import RemoveSlightSectionUI_pyqt4 as ui


class RemoveSlightSection(QtGui.QWidget, ui.Ui_Form):
    def __init__(self):
        super(RemoveSlightSection, self).__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        signals = job.matrix.returnRows('board', 'signal|power_ground')
        # for signal in outsignalLayers:
        #     signals.remove(signal)
        # print signals
        self.header = [u'勾选', u'层列表', u'极性', u'panel铺铜']
        self.tableWidget.setColumnCount(len(self.header))
        self.tableWidget.setHorizontalHeaderLabels(self.header)
        self.tableWidget.verticalHeader().hide()
        self.tableWidget.setColumnWidth(0, 40)
        # # self.tableWidget.setColumnWidth(1, 200)
        # # self.tableWidget.setColumnWidth(2, 80)
        # # self.tableWidget.setColumnWidth(3, 80)
        # self.tableWidget.setColumnWidth(6, 40)
        # self.tableWidget.setColumnWidth(7, 60)
        # self.tableWidget.setColumnWidth(8, 60)
        self.tableWidget.horizontalHeader().setResizeMode(1, QtGui.QHeaderView.Stretch)
        self.tableWidget.horizontalHeader().setResizeMode(2, QtGui.QHeaderView.Stretch)
        self.tableWidget.horizontalHeader().setResizeMode(3, QtGui.QHeaderView.Stretch)
        # self.tableWidget.setItemDelegateForColumn(1, EmptyDelegate(self))
        # self.tableWidget.setItemDelegateForColumn(2, EmptyDelegate(self))
        # self.tableWidget.setItemDelegateForColumn(3, EmptyDelegate(self))
        self.lineEdit_size.setValidator(QtGui.QDoubleValidator(self.lineEdit_size))
        self.lineEdit_size.setText('6')
        self.lineEdit_bak_name.setText('_bak')
        self.checkBox.clicked.connect(self.select_all)
        self.pushButton_exec.clicked.connect(self.run)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())
        self.move((app.desktop().width() - self.geometry().width()) / 2,
                  (app.desktop().height() - self.geometry().height()) / 2)
        # self.setStyleSheet(
        #     'QPushButton{background-color:#0081a6;color:white;} QPushButton:hover{background:black;}')
        self.setStyleSheet(
            '''QPushButton {background:rgb(49,194,124);color:white;} QPushButton:hover{background:#F7D674; color:black;}
            QListWidget{outline: 0px;border:0px;min-width: 260px;color:black;background:white;font:14px;}
            QComboBox{background:rgb(49,194,124);color:black;}
            QComboBox::Item:hover,QListWidget::Item:hover{background:#F7D674; color:black;}
            QListWidget::Item{height:24px;border-radius:1.5px;} QMessageBox{font-size:10pt;} QListWidget::Item:selected{background:rgb(49,194,124);color:white;}''')
        self.loadTable()

    def select_all(self):
        if self.checkBox.isChecked():
            for row in range(self.tableWidget.rowCount()):
                self.tableWidget.cellWidget(row, 0).setChecked(True)
        else:
            for row in range(self.tableWidget.rowCount()):
                self.tableWidget.cellWidget(row, 0).setChecked(False)

    def loadTable(self):
        self.tableWidget.setRowCount(0)
        self.tableWidget.clearContents()
        self.tableWidget.setRowCount(len(pb.inner))
        for row, data in enumerate(pb.inner):
            check = QtGui.QCheckBox()
            check.setStyleSheet('margin-left:10px;')
            self.tableWidget.setCellWidget(row, 0, check)
            item = QtGui.QTableWidgetItem(str(data['name']))
            # item.setTextAlignment(Qt.AlignCenter)
            self.tableWidget.setItem(row, 1, item)
            item = QtGui.QTableWidgetItem(str(data['pol']))
            self.tableWidget.setItem(row, 2, item)
            methods = QComboBox()
            font = QtGui.QFont('微软雅黑', 10)
            methods.setFont(font)
            methods.addItems([u'蜂窝', u'梯形', u'None'])
            self.tableWidget.setCellWidget(row, 3, methods)

    def run(self):
        flag = False
        for row in range(self.tableWidget.rowCount()):
            if self.tableWidget.cellWidget(row, 0).isChecked():
                flag = True
                break
        if not flag:
            QtGui.QMessageBox.information(self, u'提示', u'未勾选层')
            return
        section_size = self.lineEdit_size.text()  # 细丝大小
        if not section_size:
            QtGui.QMessageBox.warning(self, u'提示', u'细丝大小不能为空')
            return
        # self.hide()
        section_size = float(section_size)
        bak_name = self.lineEdit_bak_name.text()
        step = gen.Step(job, 'panel')
        step.initStep()
        step.setUnits('inch')
        add_list = []
        add_outdata = {}
        for i in range(self.tableWidget.rowCount()):
            if self.tableWidget.cellWidget(i, 0).isChecked():
                layer = self.tableWidget.item(i, 1).text()
                add_dict = {}
                add_dict['name'] = self.tableWidget.item(i, 1).text()
                add_dict['pol'] = self.tableWidget.item(i, 2).text()
                add_dict['panel'] = self.tableWidget.cellWidget(i, 3).currentText()
                add_list.append(add_dict)
                # 备份
                bak_layer = layer + bak_name  # 备份层
                step.removeLayer(bak_layer)
                step.affect(layer)
                step.copySel(bak_layer)
                step.unaffectAll()
        add_outdata['list'] = add_list
        # 重新铺铜
        Count_copper_area(add_outdata)
        # if res.res:
        #     showMessageInfo(u"板边铺铜已完成")
        step.setUnits('inch')
        for dict_ in add_outdata.get('list'):
                layer = dict_.get('name')
                tmp_signal = layer + '+++'
                tmp_surface = layer + '_surface'
                tmp_symbol = layer + '_symbol'
                tmp_symbol_ = layer + '_symbol+++'
                bak_layer = layer + bak_name  # 备份层
                step.removeLayer(tmp_signal)
                step.removeLayer(tmp_surface)
                step.removeLayer(tmp_symbol)
                step.removeLayer(tmp_symbol_)
                step.affect(bak_layer)
                step.copySel(tmp_signal)
                step.unaffectAll()
                step.affect(layer)
                step.copySel(tmp_surface)
                step.unaffectAll()
                step.affect(tmp_signal)
                step.setFilterTypes('surface')
                # step.setAttrFilter('.pattern_fill')
                step.selectAll()
                if step.Selected_count():
                    step.selectReverse()
                    if step.Selected_count():
                        step.copySel(tmp_symbol)
                    else:
                        step.removeLayer(tmp_signal)
                        continue
                step.unaffectAll()
                step.resetFilter()
                info = step.Features_INFO(tmp_symbol, 'feat_index')
                index_list = []
                for line in info:
                    if line and re.match('#\d+', line[0]):
                        index_list.append(int(line[0].replace('#', '')))
                for index in index_list:
                    step.affect(tmp_symbol)
                    step.selectByIndex(tmp_symbol, index)
                    step.copySel(tmp_symbol_)
                    step.unaffectAll()
                    step.affect(tmp_symbol_)
                    step.selectBreak()
                    step.unaffectAll()
                step.affect(tmp_symbol_)
                step.setFilterTypes(polarity='positive')
                step.selectAll()
                step.resetFilter()
                if step.Selected_count():
                    step.selectDelete()
                # 上下板边有跟负性线排除掉
                step.setFilterTypes('line', 'negative')
                step.setSymbolFilter('r0*')
                step.selectAll()
                step.resetFilter()
                if step.Selected_count():
                    step.selectDelete()
                step.selectPolarity()
                # 有些symbol是负性的外形线 这里填充一下
                # step.selectCutData(ignore_width='no') #  不忽略线宽
                step.COM(
                    'sel_cut_data,det_tol=1,con_tol=1,rad_tol=0.1,ignore_width=no,filter_overlaps=no,delete_doubles=no,use_order=yes,ignore_holes=none,start_positive=yes,polarity_of_touching=same,contourize=yes,simplify=yes,resize_thick_lines=no')
                step.Contourize(0)
                step.unaffectAll()
                step.affect(tmp_surface)
                step.clip_area(margin=0, ref_layer=tmp_symbol_)
                step.selectResize(-section_size)
                step.selectResize(section_size)
                step.PAUSE(layer)
                step.unaffectAll()
                step.affect(tmp_symbol)
                step.copySel(tmp_surface)
                step.unaffectAll()
                # 先将layer层清除
                step.truncate(layer)
                step.affect(tmp_surface)
                step.moveSel(layer)
                step.unaffectAll()
                step.removeLayer(tmp_signal)
                step.removeLayer(tmp_surface)
                step.removeLayer(tmp_symbol)
                step.removeLayer(tmp_symbol_)
                step.removeLayer(tmp_symbol_ + '+++')
        QtGui.QMessageBox.information(self, u'提示', u'执行完成！请检查')
        sys.exit()


class Count_copper_area:
    """
    铺铜
    """
    def __init__(self, data):
        # 'list':'name','pol','set',pnl  'lx',;'yx'
        self.dict = data
        self.meth = Methon()
        self.add_process = False
        self.type_cu_list = [u"实心铜皮", u"菱形铜块", u"圆形铜豆", u"方形铜块"]
        self.tempLay = {
            'fill_cu': "fill_cu_tmp",
            'fill_cu_1': "fill_cu_tmp_1",
            'fill_cu_2': "fill_cu_tmp_2",
            'fill_parten': "fill_parten_tmp",
            'fill_ng': "fill_nagetive_tmp",
            'fill_out_flatten': "fill_out_flatten_tmp",
            'ww_bk': 'ww_bk_tmp'
        }
        # self.tempLj_layer = {'lj_evenlayer': "add_copper_enveljcao", 'lj_oddlayer': "add_copper_eoddljcao"}
        # self.fill_set_copper()
        self.del_tmpLayer()
        self.res, self.pcr = self.fill_pnl_copper()

    # def fill_set_copper(self):
    #     """
    #     SET铺铜
    #     """
    #     lj_str = '39.37'
    #     list_lx, list_yx, list_fx, list_cu = [], [], [], []
    #     for d in self.dict['list']:
    #         # 内层和外层铺铜类型分下类，提高运行效率
    #         if d['set'] == self.type_cu_list[1]:
    #             list_lx.append(d)
    #         elif d['set'] == self.type_cu_list[2]:
    #             list_yx.append(d)
    #         elif d['set'] == self.type_cu_list[3]:
    #             list_fx.append(d)
    #         else:
    #             list_cu.append(d)
    #     stepName = 'set_m'
    #     step_cmd = gClasses.Step(job_cmd, stepName)
    #     # if list_cu:
    #     #     add_lj = True
    #     # else:
    #     #     add_lj = False
    #     step_cmd.open()
    #     step_cmd.clearAll()
    #     for lay in pb.inner:
    #         step_cmd.affect(lay['name'])
    #     step_cmd.resetFilter()
    #     # step_cmd.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=.area_name,text=fill_copper')
    #     step_cmd.selectAll()
    #     if step_cmd.featureSelected():
    #         step_cmd.selectDelete()
    #     step_cmd.resetFilter()
    #     self.del_tmpLayer()
    #     self.creat_tmpLayer()
    #     step_cmd.COM("units,type=inch")
    #     pf_info = step_cmd.getProfile()
    #     pf_xmin = pf_info.xmin
    #     pf_xmax = pf_info.xmax
    #     pf_ymin = pf_info.ymin
    #     pf_ymax = pf_info.ymax
    #     # 处理辅助层
    #     step_cmd.clearAll()
    #     step_cmd.affect(self.tempLay['fill_cu'])
    #     self.meth.sr_fill_surface()
    #     step_cmd.COM("sel_resize,size=-40,corner_ctl=yes" )
    #     step_cmd.unaffect(self.tempLay['fill_cu'])
    #     step_cmd.COM('flatten_layer,source_layer=out,target_layer=%s' % self.tempLay['fill_out_flatten'])
    #     if step_cmd.isLayer('ww'):
    #         step_cmd.affect('ww')
    #         step_cmd.COM('sel_change_sym,symbol=r20,reset_angle=no')
    #         step_cmd.copySel(self.tempLay['fill_cu'], invert='yes')
    #         step_cmd.unaffect('ww')
    #     step_cmd.affect(self.tempLay['fill_out_flatten'])
    #     # 掏50mil
    #     step_cmd.COM('sel_change_sym,symbol=r100,reset_angle=no')
    #     step_cmd.copySel(self.tempLay['fill_cu'],invert='yes')
    #     step_cmd.unaffect(self.tempLay['fill_out_flatten'])
    #     step_cmd.affect(self.tempLay['fill_cu'])
    #     step_cmd.contourize(units ='inch')
    #     step_cmd.unaffect(self.tempLay['fill_cu'])
    #
    #     # 处理单只里面锣空区
    #     # 合并out,ww层
    #     step_cmd.affect(self.tempLay['fill_cu_1'])
    #     self.meth.sr_fill_surface('positive', -0.001, -0.001, 100, 100,
    #                               sr_margin_x=-100, sr_margin_y=-100, sr_max_dist_x=0.001, sr_max_dist_y=0.001,
    #                               nest_sr='yes')
    #     step_cmd.copySel(self.tempLay['fill_cu_2'])
    #     step_cmd.COM("sel_resize,size=-6,corner_ctl=no")
    #     step_cmd.COM("sel_surf2outline,width=5")
    #     step_cmd.unaffect(self.tempLay['fill_cu_1'])
    #     step_cmd.COM("flatten_layer,source_layer=out,target_layer=%s" % self.tempLay['ww_bk'])
    #     if step_cmd.isLayer('ww'):
    #         step_cmd.affect('ww')
    #         step_cmd.copySel(self.tempLay['ww_bk'])
    #         step_cmd.unaffect('ww')
    #     step_cmd.affect(self.tempLay['ww_bk'])
    #     step_cmd.changeSymbol('r5')
    #     step_cmd.copySel(self.tempLay['fill_cu_2'], invert='yes')
    #     step_cmd.unaffect(self.tempLay['ww_bk'])
    #     step_cmd.affect(self.tempLay['fill_cu_2'])
    #     step_cmd.contourize(units='inch')
    #     # step_cmd.COM('sel_decompose,overlap=yes')
    #     step_cmd.refSelectFilter(self.tempLay['fill_cu_1'], mode='disjoint')
    #     if step_cmd.featureSelected():
    #         step_cmd.moveSel(self.tempLay['fill_cu'])
    #     step_cmd.unaffect(self.tempLay['fill_cu_2'])
    #     # 给fill_cu层定属性
    #     # step_cmd.resetFilter()
    #     # step_cmd.COM("cur_atr_set,attribute=.area_name,text=fill_copper")
    #     # step_cmd.resetFilter()
    #     # 分类型转铜
    #     if list_lx:
    #         # 菱形铜块,自建symbol
    #         wd_lx = self.dict['lx']['size']
    #         sp_lx = self.dict['lx']['space']
    #         symbol_lx = 'lx_copper_symbol' + '_' + wd_lx + '_' + sp_lx
    #         space_pad = math.sin(math.radians(45)) * ((float(wd_lx) + float(sp_lx)) / 1000)
    #         # 没有symbol则建立
    #         if step_cmd.DO_INFO("-t symbol -e %s/%s -d EXISTS" % (jobname, symbol_lx))['gEXISTS'] == 'no':
    #             symbol_layer = 'lx_symbol_angle_tmp'
    #             step_cmd.removeLayer(symbol_layer)
    #             self.meth.createLayer(symbol_layer)
    #             step_cmd.clearAll()
    #             step_cmd.affect(symbol_layer)
    #             leng_di = round(math.sqrt(float(wd_lx) ** 2 * 2), 3)
    #             symbol_pad = 'di%sx%s' % (leng_di, leng_di)
    #             step_cmd.COM("add_pad,attributes=no,x=%s,y=%s,symbol=%s,polarity=positive" % (0, 0, symbol_pad))
    #             step_cmd.COM(
    #                 "add_pad,attributes=no,x=%s,y=%s,symbol=%s,polarity=positive" % (space_pad, space_pad, symbol_pad))
    #             step_cmd.COM('sel_reverse')
    #             step_cmd.COM(
    #                 "sel_create_sym,symbol=%s,x_datum=%s,y_datum=%s,delete=no,fill_dx=0.1,fill_dy=0.1,attach_atr=no,retain_atr=no" % (
    #                     symbol_lx, space_pad / 2, space_pad / 2))
    #             step_cmd.unaffect(symbol_layer)
    #             step_cmd.removeLayer(symbol_layer)
    #         step_cmd.removeLayer(self.tempLay['fill_parten'])
    #         step_cmd.createLayer(self.tempLay['fill_parten'])
    #         step_cmd.copyLayer(jobname,stepName,self.tempLay['fill_cu'], self.tempLay['fill_parten'])
    #         step_cmd.affect(self.tempLay['fill_parten'])
    #         cut_yes_no = 'yes'
    #         self.meth.fill_copper_type(symbol_lx, space_pad + space_pad, space_pad + space_pad, cut_p=cut_yes_no)
    #         self.clip_fill_copper()
    #         step_cmd.resetFilter()
    #         step_cmd.COM("cur_atr_set,attribute=.area_name,text=fill_lx")
    #         step_cmd.COM("sel_change_atr,mode=add")
    #         step_cmd.resetFilter()
    #         for d in list_lx:
    #             step_cmd.copySel(d['name'])
    #         step_cmd.unaffect(self.tempLay['fill_parten'])
    #
    #     if list_yx:
    #         # 圆形铜豆
    #         step_cmd.removeLayer(self.tempLay['fill_parten'])
    #         step_cmd.createLayer(self.tempLay['fill_parten'])
    #         step_cmd.copyLayer(jobname, stepName, self.tempLay['fill_cu'], self.tempLay['fill_parten'])
    #         step_cmd.affect(self.tempLay['fill_parten'])
    #         symbol_name = 'r' + self.dict['yx']['size']
    #         space_yx = (float(self.dict['yx']['size']) + float(self.dict['yx']['space'])) / 1000
    #         cut_yes_no = 'no'
    #         self.meth.fill_copper_type(symbol_name, space_yx, space_yx, cut_p= cut_yes_no)
    #         step_cmd.resetFilter()
    #         step_cmd.COM("cur_atr_set,attribute=.area_name,text=fill_yx")
    #         step_cmd.COM("sel_change_atr,mode=add")
    #         step_cmd.resetFilter()
    #         for d in list_yx:
    #             step_cmd.copySel(d['name'])
    #         step_cmd.unaffect(self.tempLay['fill_parten'])
    #
    #     if list_fx:
    #         # 方形铜块
    #         step_cmd.removeLayer(self.tempLay['fill_parten'])
    #         step_cmd.createLayer(self.tempLay['fill_parten'])
    #         step_cmd.copyLayer(jobname, stepName, self.tempLay['fill_cu'], self.tempLay['fill_parten'])
    #         step_cmd.affect(self.tempLay['fill_parten'])
    #         symbol_name = 's' + self.dict['fx']['size']
    #         space_fx = (float(self.dict['fx']['size']) + float(self.dict['fx']['space'])) / 1000
    #         cut_yes_no = 'yes'
    #         self.meth.fill_copper_type(symbol_name, space_fx, space_fx, cut_p=cut_yes_no)
    #         self.clip_fill_copper()
    #         step_cmd.resetFilter()
    #         step_cmd.COM("cur_atr_set,attribute=.area_name,text=fill_fx")
    #         step_cmd.COM("sel_change_atr,mode=add")
    #         step_cmd.resetFilter()
    #         for d in list_fx:
    #             step_cmd.copySel(d['name'])
    #         step_cmd.unaffect(self.tempLay['fill_parten'])
    #
    #     # 如果需要加内层流胶槽，则创建层
    #     if list_cu:
    #         # 开流胶槽
    #         step_cmd.removeLayer(self.tempLj_layer['lj_evenlayer'])
    #         step_cmd.removeLayer(self.tempLj_layer['lj_oddlayer'])
    #         self.meth.createLayer(self.tempLj_layer['lj_evenlayer'])
    #         self.meth.createLayer(self.tempLj_layer['lj_oddlayer'])
    #         lj_wd = float(lj_str) / 1000
    #         size_y = pf_ymax - pf_ymin
    #         size_x = pf_xmax - pf_xmin
    #         step_cmd.affect(self.tempLj_layer['lj_evenlayer'])
    #         step_cmd.addLine(xs=pf_xmin + ((size_x / 3) - (lj_wd * 3)), ys=pf_ymin,
    #                          xe=pf_xmin + ((size_x / 3) - (lj_wd * 3)), ye=pf_ymax,
    #                          symbol='s' + lj_str, polarity='positive')
    #         step_cmd.addLine(xs=pf_xmax - ((size_x / 3) - (lj_wd * 3)), ys=pf_ymin,
    #                          xe=pf_xmax - ((size_x / 3) - (lj_wd * 3)), ye=pf_ymax,
    #                          symbol='s' + lj_str, polarity='positive')
    #         step_cmd.addLine(xs=pf_xmin, ys=pf_ymin + ((size_y / 3) - (lj_wd * 3)),
    #                          xe=pf_xmax, ye=pf_ymin + ((size_y / 3) - (lj_wd * 3)),
    #                          symbol='s' + lj_str, polarity='positive')
    #         step_cmd.addLine(xs=pf_xmin, ys=pf_ymax - ((size_y / 3) - (lj_wd * 3)),
    #                          xe=pf_xmax, ye=pf_ymax - ((size_y / 3) - (lj_wd * 3)),
    #                          symbol='s' + lj_str, polarity='positive')
    #         step_cmd.unaffect(self.tempLj_layer['lj_evenlayer'])
    #         step_cmd.affect(self.tempLj_layer['lj_oddlayer'])
    #         step_cmd.addLine(xs=pf_xmin + ((size_x / 3) + (lj_wd * 3)), ys=pf_ymin,
    #                          xe=pf_xmin + ((size_x / 3) + (lj_wd * 3)), ye=pf_ymax,
    #                          symbol='s' + lj_str, polarity='positive')
    #         step_cmd.addLine(xs=pf_xmax - ((size_x / 3) + (lj_wd * 3)), ys=pf_ymin,
    #                          xe=pf_xmax - ((size_x / 3) + (lj_wd * 3)), ye=pf_ymax,
    #                          symbol='s' + lj_str, polarity='positive')
    #         step_cmd.addLine(xs=pf_xmin, ys=pf_ymin + ((size_y / 3) + (lj_wd * 3)),
    #                          xe=pf_xmax, ye=pf_ymin + ((size_y / 3) + (lj_wd * 3)),
    #                          symbol='s' + lj_str, polarity='positive')
    #         step_cmd.addLine(xs=pf_xmin, ys=pf_ymax - ((size_y / 3) + (lj_wd * 3)),
    #                          xe=pf_xmax, ye=pf_ymax - ((size_y / 3) + (lj_wd * 3)),
    #                          symbol='s' + lj_str, polarity='positive')
    #         step_cmd.unaffect(self.tempLj_layer['lj_oddlayer'])
    #         # 创建两层
    #         step_cmd.removeLayer('fill_cu_tmp1_')
    #         step_cmd.removeLayer('fill_cu_tmp2_')
    #         step_cmd.createLayer('fill_cu_tmp1_')
    #         step_cmd.createLayer('fill_cu_tmp2_')
    #         step_cmd.copyLayer(jobname, stepName, self.tempLay['fill_cu'],  'fill_cu_tmp1_')
    #         step_cmd.copyLayer(jobname, stepName, self.tempLay['fill_cu'], 'fill_cu_tmp2_')
    #         step_cmd.clearAll()
    #         step_cmd.affect('fill_cu_tmp1_')
    #         self.meth.clip_area_copper(refLay=self.tempLj_layer['lj_evenlayer'])
    #         step_cmd.resetFilter()
    #         step_cmd.COM("cur_atr_set,attribute=.area_name,text=fill_cu")
    #         step_cmd.COM("sel_change_atr,mode=add")
    #         step_cmd.resetFilter()
    #         step_cmd.unaffect('fill_cu_tmp1_')
    #         step_cmd.affect('fill_cu_tmp2_')
    #         self.meth.clip_area_copper(refLay=self.tempLj_layer['lj_oddlayer'])
    #         step_cmd.resetFilter()
    #         step_cmd.COM("cur_atr_set,attribute=.area_name,text=fill_cu")
    #         step_cmd.COM("sel_change_atr,mode=add")
    #         step_cmd.resetFilter()
    #         step_cmd.unaffect('fill_cu_tmp2_')
    #         for d in list_cu:
    #             if int(d['name'][1:]) % 2:
    #                 step_cmd.affect('fill_cu_tmp1_')
    #                 step_cmd.copySel(d['name'])
    #                 step_cmd.unaffect('fill_cu_tmp1_')
    #             else:
    #                 step_cmd.affect('fill_cu_tmp2_')
    #                 step_cmd.copySel(d['name'])
    #                 step_cmd.unaffect('fill_cu_tmp2_')
    #         step_cmd.removeLayer('fill_cu_tmp1_')
    #         step_cmd.removeLayer('fill_cu_tmp2_')
    #     step_cmd.resetFilter()
    #     # 将内层负性的反向
    #     for d in self.dict['list']:
    #         if d['pol'] == 'negative':
    #             step_cmd.affect(self.tempLay['fill_ng'])
    #             step_cmd.selectDelete()
    #             self.meth.sr_fill_surface(step_margin_x= -0.01,step_margin_y=-0.01)
    #             step_cmd.unaffect(self.tempLay['fill_ng'])
    #             step_cmd.affect(d['name'])
    #             step_cmd.moveSel(self.tempLay['fill_ng'], invert='yes')
    #             step_cmd.unaffect(d['name'])
    #             step_cmd.affect(self.tempLay['fill_ng'])
    #             step_cmd.moveSel(d['name'])
    #             step_cmd.unaffect(self.tempLay['fill_ng'])
    #     step_cmd.close()

    def clip_fill_copper(self):
        # 去除细丝
        GEN.COM("sel_resize,size=-10,corner_ctl=no")
        GEN.COM("sel_resize,size=10,corner_ctl=no")
        GEN.COM("fill_params,type=solid,origin_type=limits,solid_type=fill,std_type=line,min_brush=5,use_arcs=yes")
        GEN.COM("sel_fill")
        GEN.SEL_CONTOURIZE(accuracy=0.1, clean_hole_size=3)

    def fill_pnl_copper(self):
        # pnl边铺铜
        res = Pnl_fill_copper(self.dict['list'])
        # if res.res:
        #     showMessageInfo(u"板边铺铜已完成")
        return res.re_back, res.pc_areas

    def del_tmpLayer(self):
        for lay in self.tempLay.values():
            GEN.VOF()
            GEN.DELETE_LAYER(lay)
            GEN.VON()

    def creat_tmpLayer(self):
        for lay in self.tempLay.values():
            GEN.VOF()
            GEN.CREATE_LAYER(lay)
            GEN.VON()

    def __del__(self):
        # self.del_tmpLayer()
        pass

class Methon:

    def __init__(self):
        pass

    def setCheckBox(self, wgt):
        STR = ("#%s{\n"
               "font-size: 15px;\n"
               "}\n"
               " \n"
               "#%s::indicator {\n"
               "padding-top: 1px;\n"
               "width: 30px;\n"
               "height: 30px;border: none;\n"
               "}\n"
               " \n"
               "#%s::indicator:unchecked {\n"
               "    image: url(:pic/png/unchecked.png);\n"
               "}\n"
               " \n"
               "#%s::indicator:checked {\n"
               "    image: url(:pic/png/right.png);\n"
               "}" % (wgt, wgt, wgt, wgt))
        return STR

    def clip_area_copper(self, refLay='', size=0):
        GEN.COM("clip_area_strt")
        GEN.COM("clip_area_end,layers_mode=affected_layers,layer=,area=reference,area_type=rectangle,inout=inside,"
                "contour_cut=yes,margin=%s,ref_layer=%s,feat_types=line\;pad\;surface\;arc\;text" % (size, refLay))

    def set_fill_parm(self, typ='solid', sym='', cut_p='no', d_x=0.1, d_y=0.1):
        """
        typ ='solid','pattern'
        """
        GEN.COM("fill_params,type=%s,origin_type=datum,solid_type=surface,std_type=line,min_brush=1,"
                "use_arcs=yes,symbol=%s,dx= %s,dy= %s,std_angle=45,std_line_width=10,std_step_dist=50,std_indent=odd,"
                "break_partial=yes,cut_prims=%s,outline_draw=no,outline_width=0,outline_invert=no" % (
                    typ, sym, d_x, d_y, cut_p))

    def sr_fill_surface(self, polarity='positive', step_margin_x=0, step_margin_y=0, step_max_dist_x=100,
                        step_max_dist_y=100,
                        sr_margin_x=0, sr_margin_y=0, sr_max_dist_x=0, sr_max_dist_y=0, nest_sr='yes'):
        GEN.COM('fill_params,type=solid,origin_type=limits,solid_type=surface')
        GEN.COM('sr_fill, polarity=%s, step_margin_x=%s, step_margin_y=%s, step_max_dist_x=%s, step_max_dist_y=%s,'
                'sr_margin_x=%s, sr_margin_y=%s, sr_max_dist_x=%s, sr_max_dist_y=%s, nest_sr=%s, stop_at_steps=,'
                'consider_feat=no, consider_drill=no, consider_rout=no, dest=affected_layers, attributes=no'
                % (polarity, step_margin_x, step_margin_y, step_max_dist_x, step_max_dist_y, sr_margin_x, sr_margin_y,
                   sr_max_dist_x, sr_max_dist_y, nest_sr))

    def fill_copper_type(self, sym, dsx, dsy, cut_p='yes'):
        GEN.COM(
            "fill_params,type=pattern,origin_type=limits,solid_type=surface,std_type=line,min_brush=0.5,use_arcs=yes,symbol=%s,dx=%s,dy=%s,std_angle=45,"
            "std_line_width=10,std_step_dist=50,std_indent=odd,break_partial=yes,cut_prims=%s,outline_draw=no,outline_width=0,outline_invert=no" % (
                sym, dsx, dsy, cut_p))
        GEN.COM("sel_fill")

    def createLayer(self, name, context='misc', laytype='document', polarity='positive', ins_layer=""):
        STR = 'create_layer,layer=%s,context=%s,type=%s,polarity=%s,ins_layer=%s' % (
            name, context, laytype, polarity, ins_layer)
        GEN.COM(STR)

class Parm:
    def __init__(self):
        self.fill_array = []
        info_pr = GEN.getProMinMax(jobname, 'panel')
        self.profile_xmin = float(info_pr['proXmin'])
        self.profile_ymin = float(info_pr['proYmin'])
        self.profile_xmax = float(info_pr['proXmax'])
        self.profile_ymax = float(info_pr['proYmax'])
        info_sr = GEN.getSrMinMax(jobname, 'panel')
        self.sr_xmin = float(info_sr['srXmin'])
        self.sr_ymin = float(info_sr['srYmin'])
        self.sr_xmax = float(info_sr['srXmax'])
        self.sr_ymax = float(info_sr['srYmax'])
        self.lamin_data = lamin_data_check

        self.lamin_num = self.get_yh_number()
        self.yh_num = max([int(i['PROCESS_NUM']) for i in self.lamin_data]) - 1
        # --设置锣边后尺寸
        self.lam_rout = [
            (int(i['PROCESS_NUM']) - 1, float(i['PNLROUTX']) * 25.4, float(i['PNLROUTY']) * 25.4) for i in
            self.lamin_data]
        self.rout_x = [i['PNLROUTX'] for i in self.lamin_data if (int(i['PROCESS_NUM']) - 1) == self.yh_num][0] * 25.4
        self.rout_y = [i['PNLROUTY'] for i in self.lamin_data if (int(i['PROCESS_NUM']) - 1) == self.yh_num][0] * 25.4
        if self.rout_x == 0 and self.rout_y == 0:
            # === 双面板此项为0，四层板以上有检测
            self.top_after_margin = self.sr_ymin
            self.left_after_margin = self.sr_xmin
        else:
            self.top_after_margin = self.sr_ymin - (self.profile_ymax - self.rout_y) * 0.5
            self.left_after_margin = self.sr_xmin - (self.profile_xmax - self.rout_x) * 0.5

    def get_yh_number(self):
        dict = {}
        for i in self.lamin_data:
            dict[str(i.get('FROMLAY')).lower()] = i['PROCESS_NUM']
            dict[str(i.get('TOLAY')).lower()] = i['PROCESS_NUM']
        return dict

class Pnl_fill_copper:
    """
    pnl板边铺铜
    """
    def __init__(self, data):
        self.fill_array = data
        self.meth = Methon()
        self.re_back = False
        self.pc_areas = []
        self.parm = Parm()
        self.GEN = GEN_COM()
        self.GEN.OPEN_STEP('panel')
        self.GEN.FILTER_RESET()
        self.GEN.CHANGE_UNITS('mm')
        self.JOB = os.environ.get('JOB', None)
        self.STEP = 'panel'
        for d in data:
            self.GEN.AFFECTED_LAYER(d['name'], affected='yes')
        self.GEN.SEL_DELETE()
        self.GEN.CLEAR_LAYER()
        self.del_tmplayers()
        self.create_honeycomb_tmp()
        self.get_sr_honeycomb()
        self.cusNo = self.JOB[1:4]
        self.put_copper()

    def __del__(self):
        self.del_tmplayers()

    def del_tmplayers(self):
        # --删除临时层别
        self.GEN.VOF()
        self.GEN.DELETE_LAYER('honeycomb-t')
        self.GEN.DELETE_LAYER('honeycomb-b')
        self.GEN.DELETE_LAYER('honeycomb-tsr')
        self.GEN.DELETE_LAYER('honeycomb-bsr')
        self.GEN.DELETE_LAYER('honeycomb-tmp1')
        self.GEN.DELETE_LAYER('honeycomb-tmp2')
        self.GEN.DELETE_LAYER('honeycomb-tmp3')
        self.GEN.DELETE_LAYER('honeycomb-tmp4')
        self.GEN.DELETE_LAYER('honeycomb-tmp5')
        self.GEN.DELETE_LAYER('honeycomb-tok')
        self.GEN.DELETE_LAYER('honeycomb-bok')
        self.GEN.VON()

    def get_copper_area(self, lay_1):
        unit = self.GEN.GET_UNITS()
        if unit == 'mm':
            self.GEN.CHANGE_UNITS('inch')
        self.GEN.VOF()
        self.GEN.COM(
            'copper_area, layer1 = %s, layer2 = , drills = no, consider_rout = no, ignore_pth_no_pad = no, drills_source = matrix,thickness = 0, '
            'resolution_value = 1, x_boxes = 3, y_boxes = 3, area = no, dist_map = yes' % lay_1)
        Arec_V = self.GEN.COMANS
        area = self.GEN.STATUS
        self.GEN.VON()
        self.GEN.CHANGE_UNITS(unit)
        # --返回
        if area == 0:
            # --以空格分隔出数组
            # Area = '%.1f' % float(Arec_V.split(' ')[0])
            PerCent = '%.1f' % float(Arec_V.split(' ')[1])
            return PerCent
        else:
            return False

    def put_copper(self):
        """
        依据fill_array指定的铺铜方式进行铺铜
        :return:
        :rtype:
        """
        fill_sym_list = [d['panel'] for d in self.fill_array]
        lam_rout = self.parm.lam_rout

        if u'蜂窝' in fill_sym_list:
            self.create_honeycomb_sym()
        if u'梯形' in fill_sym_list:
            self.create_ladder_sym()
            # self.GEN.PAUSE("tt")
        for d in self.fill_array:
            layer_name = str(d['name'])
            layer_side = d['pol']
            panel_fill = d['panel']
            try:
                cur_lamin_num = self.parm.lamin_num[layer_name] - 1
            except:
                cur_lamin_num = 0
            source_layer = ''
            if panel_fill == u'梯形':
                layer_num = layer_name[1:]
                if int(layer_num) % 2 == 0:
                    source_layer = 'ladder_top%s' % cur_lamin_num
                else:
                    source_layer = 'ladder_bot%s' % cur_lamin_num
            elif panel_fill == u'蜂窝':
                layer_num = layer_name[1:]
                if int(layer_num) % 2 == 0:
                    source_layer = 'honeycomb-tok%s' % cur_lamin_num
                else:
                    source_layer = 'honeycomb-bok%s' % cur_lamin_num
            self.GEN.CLEAR_LAYER()
            self.GEN.FILTER_RESET()
            if layer_side == 'negative':
                self.GEN.AFFECTED_LAYER(layer_name, affected='yes')
                self.meth.sr_fill_surface(step_margin_x=-0.254,step_margin_y=-0.254,
                                          step_max_dist_x=2540, step_max_dist_y=2540,nest_sr='no')
                self.GEN.AFFECTED_LAYER(layer_name, affected='no')
                self.GEN.AFFECTED_LAYER(source_layer, affected='yes')
                self.GEN.SEL_COPY(layer_name, invert='yes')
                self.GEN.AFFECTED_LAYER(source_layer, affected='no')
            else:
                self.GEN.COPY_LAYER(jobName, 'panel', source_layer, layer_name, invert='no')

        for i in range(len(lam_rout) + 1):
            self.GEN.DELETE_LAYER('ladder_top%s' % i)
            self.GEN.DELETE_LAYER('ladder_bot%s' % i)
            self.GEN.DELETE_LAYER('honeycomb-tok%s' % i)
            self.GEN.DELETE_LAYER('honeycomb-bok%s' % i)
        self.GEN.DELETE_LAYER('assist_copper')
        self.GEN.DELETE_LAYER('eagle-clear-pitch')
        self.GEN.DELETE_LAYER('eagle-cu-pitch')
        self.GEN.DELETE_LAYER('eagle-dot-pitch')
        # fill = CalculateCopperArea()
        # 计算铜面积

        # for d in self.fill_array:
        #     disk = {}
        #     disk['name'] = str(d['name'])
        #     disk['pc'] = self.get_copper_area(disk['name'])
        #     self.pc_areas.append(disk)
        #     self.GEN.AFFECTED_LAYER(disk['name'], affected='yes')
        #     self.GEN.CHANGE_UNITS('inch')
        #     self.GEN.COM("cur_atr_set,attribute=.area_name,text=copper_persen")
        #     self.GEN.ADD_TEXT(0, -0.02, disk['pc'], 0.05, 0.05, attr='yes')
        #     self.GEN.FILTER_RESET()
        #     self.GEN.AFFECTED_LAYER(disk['name'], affected='no')
        # self.re_back = True

    def create_PHOTOVOLTAIC_copper(self):
        """
        光电板sr2.5mm范围内铺铜
        :return:
        :rtype:
        """
        sr_xmin = self.parm.sr_xmin
        sr_xmax = self.parm.sr_xmax
        sr_ymin = self.parm.sr_ymin
        sr_ymax = self.parm.sr_ymax
        self.create_tmp_layer('photo_copper')
        self.GEN.CLEAR_LAYER()
        self.GEN.COM("affected_layer,name=photo_copper,mode=single,affected=yes")
        # --定义并添加bot砖块,从左至右
        x1_bot = sr_xmin + 1.6
        x2_bot = x1_bot + 1.25
        y1_bot = sr_ymin - 0.2 - 0.25 - 1.4
        y2_bot = y1_bot + 0.25 * 2 + 0.2
        dy1_bot = 1400
        dy2_bot = 0
        ny1_bot = 2
        ny2_bot = 1
        dx1_bot = 2500
        dx2_bot = 2500
        nx1_bot = (sr_xmax - 1.6 * 2 - sr_xmin) / 2.5
        nx1_bot = math.modf(nx1_bot)[1] + 1
        nx2_bot = (sr_xmax - 1.6 * 2 - sr_xmin - 2.5) / 2.5
        nx2_bot = math.modf(nx2_bot)[1] + 1
        self.GEN.ADD_PAD(x1_bot, y1_bot, 'rect2000x500', nx=nx1_bot, ny=ny1_bot, dx=dx1_bot, dy=dy1_bot)
        self.GEN.ADD_PAD(x2_bot, y2_bot, 'rect2000x500', nx=nx2_bot, ny=ny2_bot, dx=dx2_bot, dy=dy2_bot)

        # --定义并添加top砖块,从右至左
        x1_top = sr_xmax - 1.6
        x2_top = x1_top - 1.25
        y1_top = sr_ymax + 0.2 + 0.25
        y2_top = y1_top + 0.25 * 2 + 0.2
        dy1_top = 1400
        dy2_top = 0
        ny1_top = 2
        ny2_top = 1
        dx1_top = -2500
        dx2_top = -2500
        nx1_top = (sr_xmax - 1.6 * 2 - sr_xmin) / 2.5
        nx1_top = math.modf(nx1_top)[1] + 1
        nx2_top = (sr_xmax - 1.6 * 2 - sr_xmin - 2.5) / 2.5
        nx2_top = math.modf(nx2_top)[1] + 1
        self.GEN.ADD_PAD(x1_top, y1_top, 'rect2000x500', nx=nx1_top, ny=ny1_top, dx=dx1_top, dy=dy1_top)
        self.GEN.ADD_PAD(x2_top, y2_top, 'rect2000x500', nx=nx2_top, ny=ny2_top, dx=dx2_top, dy=dy2_top)

        # --定义并添加right砖块,从下至上
        y1_right = sr_ymin + 1.6
        y2_right = y1_right + 1.25
        x1_right = sr_xmax + 0.2 + 0.25
        x2_right = x1_right + 0.25 * 2 + 0.2
        dx1_right = 1400
        dx2_right = 0
        nx1_right = 2
        nx2_right = 1
        dy1_right = 2500
        dy2_right = 2500
        ny1_right = (sr_ymax - 1.6 * 2 - sr_ymin) / 2.5
        ny1_right = math.modf(ny1_right)[1] + 1
        ny2_right = (sr_ymax - 1.6 * 2 - sr_ymin - 2.5) / 2.5
        ny2_right = math.modf(ny2_right)[1] + 1
        self.GEN.ADD_PAD(x1_right, y1_right, 'rect500x2000', nx=nx1_right, ny=ny1_right, dx=dx1_right, dy=dy1_right)
        self.GEN.ADD_PAD(x2_right, y2_right, 'rect500x2000', nx=nx2_right, ny=ny2_right, dx=dx2_right, dy=dy2_right)

        # --定义并添加left砖块,从上至下
        y1_left = sr_ymax - 1.6
        y2_left = y1_left - 1.25
        x1_left = sr_xmin - 0.2 - 0.25 - 1.4
        x2_left = x1_left + 0.25 * 2 + 0.2
        dx1_left = 1400
        dx2_left = 0
        nx1_left = 2
        nx2_left = 1
        dy1_left = -2500
        dy2_left = -2500
        ny1_left = (sr_ymax - 1.6 * 2 - sr_ymin) / 2.5
        ny1_left = math.modf(ny1_left)[1] + 1
        ny2_left = (sr_ymax - 1.6 * 2 - sr_ymin - 2.5) / 2.5
        ny2_left = math.modf(ny2_left)[1] + 1
        self.GEN.ADD_PAD(x1_left, y1_left, 'rect500x2000', nx=nx1_left, ny=ny1_left, dx=dx1_left, dy=dy1_left)
        self.GEN.ADD_PAD(x2_left, y2_left, 'rect500x2000', nx=nx2_left, ny=ny2_left, dx=dx2_left, dy=dy2_left)
        self.GEN.COM("affected_layer,name=photo_copper,mode=single,affected=no")

    def create_assist_copper(self):
        """
        创建辅助层铺铜
        :return:
        :rtype:
        """
        profile_xmin = self.parm.profile_xmin
        profile_xmax = self.parm.profile_xmax
        profile_ymin = self.parm.profile_ymin
        profile_ymax = self.parm.profile_ymax
        xmin = profile_xmin - 0.254
        ymin = profile_ymin - 0.254
        xmax = profile_xmax + 0.254
        ymax = profile_ymax + 0.254
        self.create_tmp_layer('assist_copper')
        self.GEN.WORK_LAYER('assist_copper')
        self.GEN.COM("units,type=mm")
        self.GEN.COM("add_surf_strt,surf_type=feature")
        self.GEN.COM("add_surf_poly_strt,x=%s,y=%s" % (xmin, ymin))
        self.GEN.COM("add_surf_poly_seg,x=%s,y=%s" % (xmin, ymax))
        self.GEN.COM("add_surf_poly_seg,x=%s,y=%s" % (xmax, ymax))
        self.GEN.COM("add_surf_poly_seg,x=%s,y=%s" % (xmax, ymin))
        self.GEN.COM("add_surf_poly_seg,x=%s,y=%s" % (xmin, ymin))
        self.GEN.COM("add_surf_poly_end")
        self.GEN.COM("add_surf_end,attributes=no,polarity=positive")

    def create_ladder_sym(self):
        """
        创建梯形的板边铺铜symbol
        :return:
        :rtype:
        """
        sr_xmin = self.parm.sr_xmin
        sr_ymin = self.parm.sr_ymin
        sr_xmax = self.parm.sr_xmax
        sr_ymax = self.parm.sr_ymax
        rout_x = self.parm.rout_x
        rout_y = self.parm.rout_y
        profile_xmin = self.parm.profile_xmin
        profile_xmax = self.parm.profile_xmax
        profile_ymin = self.parm.profile_ymin
        profile_ymax = self.parm.profile_ymax
        # job_signal_numbers = self.parm.job_signal_numbers
        lam_rout = self.parm.lam_rout
        lenth = 13
        width = 63
        # --长边clip板内坐标定义
        clip_Iy_xmax = sr_xmin - 2.5
        clip_Iy_xmin = sr_xmax + 2.5
        clip_Iy_ymin = profile_ymin - 5
        clip_Iy_ymax = profile_ymax + 5
        # --短边clip板内坐标定义
        clip_Ix_xmin = sr_xmin - 2.5 - 5
        clip_Ix_xmax = sr_xmax + 2.5 + 5
        clip_Ix_ymin = sr_ymin - 2.5
        clip_Ix_ymax = sr_ymax + 2.5
        # --短边clip板外坐标定义
        clip_Ox_xmin = sr_xmin - 2.5 - 5
        clip_Ox_xmax = sr_xmax + 2.5 + 5

        clip_out_dict = {}
        for lamin_i in lam_rout:
            cur_lamin_num = lamin_i[0]
            cur_lamin_routx = lamin_i[1]
            cur_lamin_routy = lamin_i[2]
            clip_Oy_xmin = profile_xmin + (profile_xmax - cur_lamin_routx) * 0.5 + 2
            clip_Oy_xmax = profile_xmax - (profile_xmax - cur_lamin_routx) * 0.5 - 2
            clip_Oy_ymin = profile_ymin + (profile_ymax - cur_lamin_routy) * 0.5 + 2
            clip_Oy_ymax = profile_ymax - (profile_ymax - cur_lamin_routy) * 0.5 - 2
            clip_Ox_ymin = profile_ymin + (profile_ymax - cur_lamin_routy) * 0.5 + 2
            clip_Ox_ymax = profile_ymax - (profile_ymax - cur_lamin_routy) * 0.5 - 2
            clip_out_dict[cur_lamin_num] = {
                'clip_Oy_xmin': clip_Oy_xmin,
                'clip_Oy_xmax': clip_Oy_xmax,
                'clip_Oy_ymin': clip_Oy_ymin,
                'clip_Oy_ymax': clip_Oy_ymax,
                'clip_Ox_xmin': clip_Ox_xmin,
                'clip_Ox_xmax': clip_Ox_xmax,
                'clip_Ox_ymin': clip_Ox_ymin,
                'clip_Ox_ymax': clip_Ox_ymax,
            }
        # === 增加0压数据 ===
        clip_out_dict[0] = {
            'clip_Oy_xmin': profile_xmin + 2,
            'clip_Oy_xmax': profile_xmax - 2,
            'clip_Oy_ymin': profile_ymin + 2,
            'clip_Oy_ymax': profile_ymax - 2,
            'clip_Ox_xmin': clip_Ox_xmin,
            'clip_Ox_xmax': clip_Ox_xmax,
            'clip_Ox_ymin': profile_ymin + 2,
            'clip_Ox_ymax': profile_ymax - 2
        }
        # # --长边clip板外坐标定义
        # clip_Oy_xmin = profile_xmin - 5
        # clip_Oy_xmax = profile_xmax + 5
        # clip_Oy_ymin = profile_ymin - 5
        # clip_Oy_ymax = profile_ymax + 5
        #
        #
        # clip_Ox_ymin = profile_ymin - 5
        # clip_Ox_ymax = profile_ymax + 5
        # --20210118新规则,所有板层同六层板
        # --20210209内层铺铜，四层板仍然要求距锣边1mm
        # if job_signal_numbers == 4:
        #     # --四层板距锣边(profile)1mm
        #     clip_Oy_xmin = profile_xmin + (profile_xmax - rout_x)*0.5 + 1
        #     clip_Oy_xmax = profile_xmax - (profile_xmax - rout_x)*0.5 - 1
        #     clip_Oy_ymin = profile_ymin + (profile_ymax - rout_y)*0.5 + 1
        #     clip_Oy_ymax = profile_ymax - (profile_ymax - rout_y)*0.5 - 1
        #     clip_Ox_ymin = profile_ymin + (profile_ymax - rout_y)*0.5 + 1
        #     clip_Ox_ymax = profile_ymax - (profile_ymax - rout_y)*0.5 - 1
        # --计算长边偏移值
        long_offset_top = 0
        # --注意bot只是在top面的基础上再偏移1.5(默认,后面会调整)
        long_offset_bot = 3
        long_side_top = sr_xmin - 2.5 - clip_Oy_xmin
        long_side_bot = sr_xmin - 2.5 - clip_Oy_xmin + long_offset_bot
        long_model_top = long_side_top % 6.5
        long_model_bot = long_side_bot % 6.5
        long_model_top = float('%.3f' % long_model_top)
        long_model_bot = float('%.3f' % long_model_bot)
        # --最内侧铜皮保留(封口)宽度
        long_revise_top = 5
        long_revise_bot = 5 - long_offset_bot

        # --计算短边偏移值
        short_offset_top = 3
        short_offset_bot = 0
        short_side_bot = sr_ymin - 2.5 - clip_Ox_ymin
        short_side_top = sr_ymin - 2.5 - clip_Ox_ymin + short_offset_top
        short_model_bot = short_side_bot % 6.5
        short_model_top = short_side_top % 6.5
        short_model_top = float('%.3f' % short_model_top)
        short_model_bot = float('%.3f' % short_model_bot)
        short_revise_bot = 5
        short_revise_top = 5 - short_offset_top

        # --长边添加pad的x坐标,5.75为fill_ladder_top中心到边缘的距离,以top面为基准
        x1_top = sr_xmin - 5.75 - 2.5 + long_offset_top
        x2_top = sr_xmax + 5.75 + 2.5 - long_offset_top
        x1_bot = sr_xmin - 5.75 - 2.5 + long_offset_bot
        x2_bot = sr_xmax + 5.75 + 2.5 - long_offset_bot
        # --短边添加pad的y坐标,以bot面为基准
        y1_bot = sr_ymin - 5.75 - 2.5 + short_offset_bot
        y2_bot = sr_ymax + 5.75 + 2.5 - short_offset_bot
        y1_top = sr_ymin - 5.75 - 2.5 + short_offset_top
        y2_top = sr_ymax + 5.75 + 2.5 - short_offset_top
        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        for side in ('top', 'bot'):
            if side == 'top':
                layer_y = 'ladder_y_top'
                layer_x = 'ladder_x_top'
                # === TODO 此处应为列表 ===
                layer = 'ladder_top'
                sym = 'fill_ladder_top'
                x1 = x1_top
                x2 = x2_top
                # --设置clip参数使长短边交汇处平齐
                clip_Ox_xmin = sr_xmin - 2.5 - long_revise_top
                clip_Ox_xmax = sr_xmax + 2.5 + long_revise_top
                # --top面短边靠近板内做3.5mm
                y1 = y1_top
                y2 = y2_top
            else:
                layer_y = 'ladder_y_bot'
                layer_x = 'ladder_x_bot'
                layer = 'ladder_bot'
                sym = 'fill_ladder_bot'
                # --bot面长边靠近板内做3.5mm
                x1 = x1_bot
                x2 = x2_bot
                y1 = y1_bot
                y2 = y2_bot
                # --设置clip参数使长短边交汇处平齐
                clip_Ox_xmin = sr_xmin - 2.5 - long_revise_bot
                clip_Ox_xmax = sr_xmax + 2.5 + long_revise_bot
            self.create_tmp_layer(layer_y)
            self.create_tmp_layer(layer_x)
            for cur_lamin_num in clip_out_dict.keys():
                self.create_tmp_layer('%s%s' % (layer, cur_lamin_num))
            self.GEN.WORK_LAYER(layer_y)
            self.GEN.SEL_DELETE()
            # --定义长边添加symbol的参数
            nx = int(long_side_top / lenth) + 2
            ny = int((profile_ymax - profile_ymin) / width) + 2
            y = (profile_ymax - profile_ymin) / 2 - (ny - 1) * width / 2
            dx = lenth * 1000
            dy = width * 1000
            self.GEN.ADD_PAD(x1, y, sym, nx=nx, ny=ny, dx=-dx, dy=dy)
            self.GEN.ADD_PAD(x2, y, sym, nx=nx, ny=ny, dx=dx, dy=dy)
            # print "long_model_top",long_model_top
            # print "long_model_bot",long_model_bot
            # self.GEN.PAUSE("add long pad")
            # --长边板内clip
            self.GEN.COM("clip_area_strt")
            self.GEN.COM("clip_area_xy,x=%s,y=%s" % (clip_Iy_xmin, clip_Iy_ymin))
            self.GEN.COM("clip_area_xy,x=%s,y=%s" % (clip_Iy_xmax, clip_Iy_ymax))
            self.GEN.COM(
                "clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=rectangle,inout=inside,"
                "contour_cut=yes,margin=0,feat_types=line\;pad\;surface\;arc\;text")
            # self.GEN.PAUSE("clip pad long inner")
            # --长边板外clip
            for cur_lamin_num in range(0, len(lam_rout)):
                # for item in lam_rout:
                #     if item[0] ==  cur_lamin_num:
                self.GEN.COM("clip_area_strt")
                # self.GEN.COM("clip_area_xy,x=%s,y=%s" % (clip_Oy_xmin, clip_Oy_ymin))
                # self.GEN.COM("clip_area_xy,x=%s,y=%s" % (clip_Oy_xmax, clip_Oy_ymax))
                self.GEN.COM("clip_area_xy,x=%s,y=%s" % (
                    clip_out_dict[cur_lamin_num]['clip_Oy_xmin'], clip_out_dict[cur_lamin_num]['clip_Oy_ymin']))
                self.GEN.COM("clip_area_xy,x=%s,y=%s" % (
                    clip_out_dict[cur_lamin_num]['clip_Oy_xmax'], clip_out_dict[cur_lamin_num]['clip_Oy_ymax']))

                self.GEN.COM(
                    "clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=rectangle,inout=outside,"
                    "contour_cut=yes,margin=0,feat_types=line\;pad\;surface\;arc\;text")
                # self.GEN.PAUSE("clip pad long outer")
                self.GEN.SEL_COPY("%s%s" % (layer, cur_lamin_num))
            # --定义短边添加symbol的参数
            ny = int(short_side_bot / lenth) + 2
            nx = int((profile_xmax - profile_xmin) / width) + 2
            dy = lenth * 1000
            dx = width * 1000
            x = (profile_xmax - profile_xmin) / 2 - (nx - 1) * width / 2
            self.GEN.WORK_LAYER(layer_x)
            self.GEN.SEL_DELETE()
            self.GEN.ADD_PAD(x, y1, sym, nx=nx, ny=ny, dx=dx, dy=-dy, angle=90)
            self.GEN.ADD_PAD(x, y2, sym, nx=nx, ny=ny, dx=dx, dy=dy, angle=90)
            # print "short_model_bot",short_model_bot
            # print "short_model_top",short_model_top
            # self.GEN.PAUSE("add short pad")
            # --短边板内clip
            self.GEN.COM("clip_area_strt")
            self.GEN.COM("clip_area_xy,x=%s,y=%s" % (clip_Ix_xmin, clip_Ix_ymin))
            self.GEN.COM("clip_area_xy,x=%s,y=%s" % (clip_Ix_xmax, clip_Ix_ymax))
            self.GEN.COM(
                "clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=rectangle,inout=inside,"
                "contour_cut=yes,margin=0,feat_types=line\;pad\;surface\;arc\;text")
            # self.GEN.PAUSE("clip pad short inner")
            # --短边板外clip
            for cur_lamin_num in range(0, len(lam_rout)):
                # for item in lam_rout:
                #     if item[0] ==  cur_lamin_num:
                self.GEN.COM("clip_area_strt")
                # self.GEN.COM("clip_area_xy,x=%s,y=%s" % (clip_Oy_xmin, clip_Oy_ymin))
                # self.GEN.COM("clip_area_xy,x=%s,y=%s" % (clip_Oy_xmax, clip_Oy_ymax))
                self.GEN.COM("clip_area_xy,x=%s,y=%s" % (
                    clip_out_dict[cur_lamin_num]['clip_Ox_xmin'], clip_out_dict[cur_lamin_num]['clip_Ox_ymin']))
                self.GEN.COM("clip_area_xy,x=%s,y=%s" % (
                    clip_out_dict[cur_lamin_num]['clip_Ox_xmax'], clip_out_dict[cur_lamin_num]['clip_Ox_ymax']))

                self.GEN.COM(
                    "clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=rectangle,inout=outside,"
                    "contour_cut=yes,margin=0,feat_types=line\;pad\;surface\;arc\;text")
                # self.GEN.PAUSE("clip pad long outer")
                self.GEN.SEL_COPY("%s%s" % (layer, cur_lamin_num))

            # --删除临时层别
            self.GEN.DELETE_LAYER(layer_x)
            self.GEN.DELETE_LAYER(layer_y)
        # self.GEN.PAUSE("check")
        # --通过两次resize,去掉尖角和小于5mil的surface
        for cur_lamin_num in range(0, len(lam_rout)):
            top_layer = 'ladder_top%s' % (cur_lamin_num)
            bot_layer = 'ladder_bot%s' % (cur_lamin_num)
            self.remove_small_surface(size=1000, target_top=top_layer, target_bot=bot_layer)
            # --将梯形铺铜整体化成一整块surface,方便框选其它symbol
            self.GEN.CLEAR_LAYER()
            self.GEN.AFFECTED_LAYER(top_layer, 'yes')
            self.GEN.AFFECTED_LAYER(bot_layer, 'yes')
            self.GEN.COM('sel_contourize, accuracy=6.35, break_to_islands=no, clean_hole_size=76.2')
            self.GEN.CLEAR_LAYER()
            # --品字形排版sr范围内铺蜂窝铜
            self.copy_sr_honeycomb(target_top=top_layer, target_bot=bot_layer)
            # --排版间距里铺铜条
            for direct in ('horizontal', 'vertical'):
                self.fill_pitch(direct, target_top=top_layer, target_bot=bot_layer)
            # --四角铺铜皮,940,968转角不铺铜皮 === HDI无此要求 ===
            # if self.cusNo not in ('940', '968'):
            self.corner_copper(copper_dis=60, target_top=top_layer, target_bot=bot_layer, cur_lamin_num=cur_lamin_num)
            # --绕内profile一圈添加金线,光电板不需要
            # if not self.parm.is_PHOTOVOLTAIC_board:
            self.add_gold_line(target_top=top_layer, target_bot=bot_layer)
            # --增加属性,方便后续作业
            self.add_attribute(layer=top_layer, attribute='.bit,text=pnl_ladder_cu')
            self.add_attribute(layer=bot_layer, attribute='.bit,text=pnl_ladder_cu')
            self.add_attribute(layer=top_layer, attribute='.string,text=ladder_top')
            self.add_attribute(layer=bot_layer, attribute='.string,text=ladder_bot')
        self.GEN.CLEAR_LAYER()

    def create_honeycomb_sym(self):
        """
        创建蜂窝形状的板边铺铜symbol
        :return:
        :rtype:
        """
        # job_signal_numbers = self.parm.job_signal_numbers
        sr_xmin = self.parm.sr_xmin
        sr_ymin = self.parm.sr_ymin
        sr_xmax = self.parm.sr_xmax
        sr_ymax = self.parm.sr_ymax
        profile_xmin = self.parm.profile_xmin
        profile_xmax = self.parm.profile_xmax
        profile_ymin = self.parm.profile_ymin
        profile_ymax = self.parm.profile_ymax
        # rout_x = self.parm.rout_x
        # rout_y = self.parm.rout_y
        # top_after_margin = self.parm.top_after_margin
        # left_after_margin = self.parm.left_after_margin

        lam_rout = self.parm.lam_rout

        # --将蜂窝临时层的内容物copy到正式层然后clip
        self.GEN.CLEAR_LAYER()
        self.create_tmp_layer('honeycomb-tok')
        self.create_tmp_layer('honeycomb-bok')
        for cur_lamin_num in range(len(lam_rout) + 1):
            self.create_tmp_layer('honeycomb-tok%s' % cur_lamin_num)
            self.create_tmp_layer('honeycomb-bok%s' % cur_lamin_num)
        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.GEN.COM("affected_layer,name=honeycomb-t,mode=single,affected=yes")
        # --top临时层copy到top_ok
        self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=honeycomb-tok,invert=no,dx=0,dy=0,"
                     "size=0,x_anchor=0,y_anchor=0,rotation=0,mirror=none")
        # --bot临时层copy到bot_ok
        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.GEN.COM("affected_layer,name=honeycomb-b,mode=single,affected=yes")
        self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=honeycomb-bok,invert=no,dx=0,dy=0,size=0,"
                     "x_anchor=0,y_anchor=0,rotation=0,mirror=none")
        # --切铜参数定义

        # === 使用距离板内2.5mm的铺铜距离，不区分几层板
        cut_copper_x1 = sr_xmin - 2.5
        cut_copper_y1 = sr_ymin - 2.5
        cut_copper_x2 = sr_xmax + 2.5
        cut_copper_y2 = sr_ymax + 2.5

        clip_out_dict = {}
        for cur_lamin_num in range(len(lam_rout) + 1):
            if cur_lamin_num == 0:
                clip_out_dict[0] = dict(
                    cut_copper_x3=profile_xmin + 2,
                    cut_copper_y3=profile_ymin + 2,
                    cut_copper_x4=profile_xmax - 2,
                    cut_copper_y4=profile_ymax - 2
                )
            else:
                cur_lamin_routx = lam_rout[cur_lamin_num - 1][1]
                cur_lamin_routy = lam_rout[cur_lamin_num - 1][2]
                clip_out_dict[cur_lamin_num] = dict(
                    cut_copper_x3=profile_xmin + (profile_xmax - cur_lamin_routx) * 0.5 + 2,
                    cut_copper_y3=profile_ymin + (profile_ymax - cur_lamin_routy) * 0.5 + 2,
                    cut_copper_x4=profile_xmax - (profile_xmax - cur_lamin_routx) * 0.5 - 2,
                    cut_copper_y4=profile_ymax - (profile_ymax - cur_lamin_routy) * 0.5 - 2)

        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.GEN.COM("affected_layer,name=honeycomb-tok,mode=single,affected=yes")
        self.GEN.COM("affected_layer,name=honeycomb-bok,mode=single,affected=yes")
        # --伸到板内部分进行clip
        self.GEN.COM("clip_area_strt")
        self.GEN.COM("clip_area_xy,x=%s,y=%s" % (cut_copper_x1, cut_copper_y1))
        self.GEN.COM("clip_area_xy,x=%s,y=%s" % (cut_copper_x2, cut_copper_y2))
        self.GEN.COM("clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=rectangle,inout=inside,"
                     "contour_cut=yes,margin=0,feat_types=line\;pad\;surface\;arc\;text")

        cut_copper_x3 = clip_out_dict[0]['cut_copper_x3']
        cut_copper_y3 = clip_out_dict[0]['cut_copper_y3']
        cut_copper_x4 = clip_out_dict[0]['cut_copper_x4']
        cut_copper_y4 = clip_out_dict[0]['cut_copper_y4']

        # --伸出板外部分进行clip
        self.GEN.COM("clip_area_strt")
        self.GEN.COM("clip_area_xy,x=%s,y=%s" % (cut_copper_x3, cut_copper_y3))
        self.GEN.COM("clip_area_xy,x=%s,y=%s" % (cut_copper_x4, cut_copper_y4))
        self.GEN.COM("clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=rectangle,inout=outside,"
                     "contour_cut=yes,margin=0,feat_types=line\;pad\;surface\;arc\;text")

        # --品字形sr范围内铺蜂窝铜
        self.copy_sr_honeycomb(target_top='honeycomb-tok', target_bot='honeycomb-bok')
        # --排版间距里铺铜条
        for direct in ('horizontal', 'vertical'):
            self.fill_pitch(direct, target_top='honeycomb-tok', target_bot='honeycomb-bok')
        # --通过两次resize,去掉尖角和小于5mil的surface
        self.remove_small_surface(target_top='honeycomb-tok', target_bot='honeycomb-bok')
        # --四角铺铜皮
        self.corner_copper(target_top='honeycomb-tok', target_bot='honeycomb-bok')
        # --绕内profile一圈添加金线
        self.add_gold_line(target_top='honeycomb-tok', target_bot='honeycomb-bok')

        for cur_lamin_num in range(len(lam_rout) + 1):
            cut_copper_x3 = clip_out_dict[cur_lamin_num]['cut_copper_x3']
            cut_copper_y3 = clip_out_dict[cur_lamin_num]['cut_copper_y3']
            cut_copper_x4 = clip_out_dict[cur_lamin_num]['cut_copper_x4']
            cut_copper_y4 = clip_out_dict[cur_lamin_num]['cut_copper_y4']
            self.GEN.CLEAR_LAYER()
            self.GEN.AFFECTED_LAYER('honeycomb-tok', 'yes')
            self.GEN.AFFECTED_LAYER('honeycomb-bok', 'yes')

            # --伸出板外部分进行clip 放在此位置，避免多次运行
            self.GEN.COM("clip_area_strt")
            self.GEN.COM("clip_area_xy,x=%s,y=%s" % (cut_copper_x3, cut_copper_y3))
            self.GEN.COM("clip_area_xy,x=%s,y=%s" % (cut_copper_x4, cut_copper_y4))
            self.GEN.COM(
                "clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=rectangle,inout=outside,"
                "contour_cut=yes,margin=0,feat_types=line\;pad\;surface\;arc\;text")
            self.GEN.CLEAR_LAYER()
            self.GEN.AFFECTED_LAYER('honeycomb-tok', 'yes')
            self.GEN.SEL_COPY('honeycomb-tok%s' % cur_lamin_num)
            self.GEN.CLEAR_LAYER()
            self.GEN.AFFECTED_LAYER('honeycomb-bok', 'yes')
            self.GEN.SEL_COPY('honeycomb-bok%s' % cur_lamin_num)
            self.GEN.CLEAR_LAYER()

            self.add_attribute(layer='honeycomb-tok%s' % cur_lamin_num, attribute='surface,text=copper')
            self.add_attribute(layer='honeycomb-bok%s' % cur_lamin_num, attribute='surface,text=copper')
            self.add_attribute(layer='honeycomb-tok%s' % cur_lamin_num, attribute='.string,text=ladder_top')
            self.add_attribute(layer='honeycomb-bok%s' % cur_lamin_num, attribute='.string,text=ladder_bot')
        self.GEN.CLEAR_LAYER()

        # --创建symbol,由于创建symbol会导致在panel查看时移动较卡，所以取消
        # self.GEN.COM("clear_layers")
        # self.GEN.COM("affected_layer,mode=all,affected=no")
        # self.GEN.COM("affected_layer,name=honeycomb-tok,mode=single,affected=yes")
        # self.GEN.COM("sel_create_sym,symbol=panel_symbol_top,x_datum=0,y_datum=0,delete=no,fill_dx=2.54,fill_dy=2.54,"
        #              "attach_atr=no,retain_atr=no")
        #
        # self.GEN.COM("clear_layers")
        # self.GEN.COM("affected_layer,mode=all,affected=no")
        # self.GEN.COM("affected_layer,name=honeycomb-bok,mode=single,affected=yes")
        # self.GEN.COM("sel_create_sym,symbol=panel_symbol_bot,x_datum=0,y_datum=0,delete=no,fill_dx=2.54,fill_dy=2.54,"
        #              "attach_atr=no,retain_atr=no")

    def add_attribute(self, layer=None, attribute=None):
        """
        将铺铜的surface加上属性
        :return:
        :rtype:
        """
        self.GEN.CLEAR_LAYER()
        self.GEN.AFFECTED_LAYER(layer, 'yes')
        self.GEN.COM('cur_atr_reset')
        self.GEN.COM('cur_atr_set,attribute=%s' % attribute)
        self.GEN.COM('sel_change_atr,mode=add')
        self.GEN.COM('cur_atr_reset')
        self.GEN.AFFECTED_LAYER(layer, 'no')

    def create_honeycomb_tmp(self):
        """
        创建蜂窝临时层别
        :return:
        :rtype:
        """
        self.GEN.OPEN_STEP(self.STEP)
        self.GEN.CLEAR_LAYER()
        self.create_tmp_layer('honeycomb-t')
        self.create_tmp_layer('honeycomb-b')
        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        # --top面与bot面用同样的参数fill
        self.GEN.COM("affected_layer,name=honeycomb-t,mode=single,affected=yes")
        self.GEN.COM("affected_layer,name=honeycomb-b,mode=single,affected=yes")
        self.GEN.COM("fill_params,type=pattern,origin_type=datum,solid_type=surface,std_type=line,min_brush=25.4,"
                     "use_arcs=yes,symbol=2oz_fw,dx=9.72312,dy=5.588,std_angle=45,std_line_width=254,"
                     "std_step_dist=1270,std_indent=odd,break_partial=yes,cut_prims=yes,outline_draw=no,"
                     "outline_width=0,outline_invert=no")
        # --超出内profile10mm,超出profile也是10mm
        self.GEN.COM("sr_fill,polarity=positive,step_margin_x=-10,step_margin_y=-10,step_max_dist_x=2540,"
                     "step_max_dist_y=2540,sr_margin_x=-10,sr_margin_y=-10,sr_max_dist_x=0,sr_max_dist_y=0,nest_sr=no,"
                     "consider_feat=no,consider_drill=no,consider_rout=no,dest=affected_layers,attributes=no")
        # --top面与bot面错位3.14mm
        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.GEN.COM("affected_layer,name=honeycomb-t,mode=single,affected=yes")
        self.GEN.COM("sel_move,dx=3.14,dy=0")

    def get_sr_honeycomb(self):
        """
        sr范围内铺蜂窝铜,品字形拼板才会有
        :return:
        :rtype:
        """
        sr_xmin = self.parm.sr_xmin
        sr_ymin = self.parm.sr_ymin
        sr_xmax = self.parm.sr_xmax
        sr_ymax = self.parm.sr_ymax
        # --删除并重新创建临时层别
        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.create_tmp_layer('honeycomb-tmp1')
        self.create_tmp_layer('honeycomb-tmp2')
        # --用solid fill tmp1,距内profile 2.5mm,外面超出profile 5mm,以下步骤对品字形排版有用
        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.GEN.COM("affected_layer,name=honeycomb-tmp1,mode=single,affected=yes")
        self.GEN.COM("fill_params,type=solid,origin_type=datum,solid_type=surface,std_type=line,min_brush=25.4,"
                     "use_arcs=yes,symbol=2oz_fw,dx=9.72312,dy=5.588,std_angle=45,std_line_width=254,std_step_dist=1270,"
                     "std_indent=odd,break_partial=yes,cut_prims=yes,outline_draw=no,outline_width=0,outline_invert=no")
        self.GEN.COM("sr_fill,polarity=positive,step_margin_x=-5,step_margin_y=-5,step_max_dist_x=2540,"
                     "step_max_dist_y=2540,sr_margin_x=2.5,sr_margin_y=2.5,sr_max_dist_x=0,sr_max_dist_y=0,nest_sr=no,"
                     "consider_feat=no,consider_drill=no,consider_rout=no,dest=affected_layers,attributes=no")
        # --用solid fill tmp2,铺进板内1000mm,以下步骤对品字形排版有用
        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.GEN.COM("affected_layer,name=honeycomb-tmp2,mode=single,affected=yes")
        self.GEN.COM("fill_params,type=solid,origin_type=datum,solid_type=surface,std_type=line,min_brush=25.4,"
                     "use_arcs=yes,symbol=2oz_fw,dx=9.72312,dy=5.588,std_angle=45,std_line_width=254,std_step_dist=1270,"
                     "std_indent=odd,break_partial=yes,cut_prims=yes,outline_draw=no,outline_width=0,outline_invert=no")
        self.GEN.COM("sr_fill,polarity=positive,step_margin_x=-5,step_margin_y=-5,step_max_dist_x=2540,"
                     "step_max_dist_y=2540,sr_margin_x=-1000,sr_margin_y=-1000,sr_max_dist_x=0,sr_max_dist_y=0,"
                     "nest_sr=no,consider_feat=no,consider_drill=no,consider_rout=no,dest=affected_layers,attributes=no")
        # --tmp1 copy到tmp2,两者合并得到超出内profile 2.5mm的铺满整个内容物的铜皮
        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.GEN.COM("affected_layer,name=honeycomb-tmp1,mode=single,affected=yes")
        self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=honeycomb-tmp2,invert=yes,dx=0,dy=0,size=0,"
                     "x_anchor=0,y_anchor=0,rotation=0,mirror=none")

        # --对honeycomb-t和honeycomb-b进行clip,保留sr范围内的部分
        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.GEN.COM("affected_layer,name=honeycomb-t,mode=single,affected=yes")
        self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=honeycomb-tsr,invert=no,dx=0,dy=0,size=0,"
                     "x_anchor=0,y_anchor=0,rotation=0,mirror=none")

        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.GEN.COM("affected_layer,name=honeycomb-b,mode=single,affected=yes")
        self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=honeycomb-bsr,invert=no,dx=0,dy=0,size=0,"
                     "x_anchor=0,y_anchor=0,rotation=0,mirror=none")

        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.GEN.COM("affected_layer,name=honeycomb-tsr,mode=single,affected=yes")
        self.GEN.COM("affected_layer,name=honeycomb-bsr,mode=single,affected=yes")

        # cut_copper_x5 = sr_xmin + 1
        # cut_copper_y5 = sr_ymin + 1
        # cut_copper_x6 = sr_xmax - 1
        # cut_copper_y6 = sr_ymax - 1
        cut_copper_x5 = sr_xmin - 2
        cut_copper_y5 = sr_ymin - 2
        cut_copper_x6 = sr_xmax + 2
        cut_copper_y6 = sr_ymax + 2

        self.GEN.COM("clip_area_strt")
        self.GEN.COM("clip_area_xy,x=%s,y=%s" % (cut_copper_x5, cut_copper_y5))
        self.GEN.COM("clip_area_xy,x=%s,y=%s" % (cut_copper_x6, cut_copper_y6))
        self.GEN.COM("clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=rectangle,inout=outside,"
                     "contour_cut=yes,margin=0,feat_types=line\;pad\;surface\;arc\;text")

        # === v2.12 铺铜距离加大后，限位孔角线被覆盖，切掉多余铜 ===
        # === 1.左下
        self.GEN.COM('clip_area_strt')
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmin - 2.5), (sr_ymin - 2.5)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmin + 2.5), (sr_ymin - 2.5)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmin + 2.5), (sr_ymin)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmin), (sr_ymin)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmin), (sr_ymin + 2.5)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmin - 2.5), (sr_ymin + 2.5)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmin - 2.5), (sr_ymin - 2.5)))
        self.GEN.COM(
            'clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=polygon,inout=inside,contour_cut=no,margin=0,feat_types=surface')
        # === 2.右下
        self.GEN.COM('clip_area_strt')
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmax + 2.5), (sr_ymin - 2.5)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmax - 2.5), (sr_ymin - 2.5)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmax - 2.5), (sr_ymin)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmax), (sr_ymin)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmax), (sr_ymin + 2.5)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmax + 2.5), (sr_ymin + 2.5)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmax + 2.5), (sr_ymin - 2.5)))
        self.GEN.COM(
            'clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=polygon,inout=inside,contour_cut=no,margin=0,feat_types=surface')
        # === 3.右上
        self.GEN.COM('clip_area_strt')
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmax + 2.5), (sr_ymax + 2.5)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmax - 2.5), (sr_ymax + 2.5)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmax - 2.5), (sr_ymax)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmax), (sr_ymax)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmax), (sr_ymax - 2.5)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmax + 2.5), (sr_ymax - 2.5)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmax + 2.5), (sr_ymax + 2.5)))
        self.GEN.COM(
            'clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=polygon,inout=inside,contour_cut=no,margin=0,feat_types=surface')
        # === 4.左上
        self.GEN.COM('clip_area_strt')
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmin - 2.5), (sr_ymax + 2.5)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmin + 2.5), (sr_ymax + 2.5)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmin + 2.5), (sr_ymax)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmin), (sr_ymax)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmin), (sr_ymax - 2.5)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmin - 2.5), (sr_ymax - 2.5)))
        self.GEN.COM('clip_area_xy,x=%s,y=%s' % ((sr_xmin - 2.5), (sr_ymax + 2.5)))
        self.GEN.COM(
            'clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=polygon,inout=inside,contour_cut=no,margin=0,feat_types=surface')

        # --tmp2整体化后copy到honeycomb-tsr和honeycomb-bsr
        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.GEN.COM("affected_layer,name=honeycomb-tmp2,mode=single,affected=yes")
        self.GEN.COM("sel_contourize,accuracy=50.8,break_to_islands=yes,clean_hole_size=76.2,clean_hole_mode=x_and_y")
        self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=honeycomb-tsr,invert=yes,dx=0,dy=0,size=0,"
                     "x_anchor=0,y_anchor=0,rotation=0,mirror=none")
        self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=honeycomb-bsr,invert=yes,dx=0,dy=0,size=0,"
                     "x_anchor=0,y_anchor=0,rotation=0,mirror=none")
        # --honeycomb-tsr和honeycomb-bsr进行整体化,这几步对品字形排版有用,对正正排版是在做无用功，copy空气到tok和bok
        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.GEN.COM("affected_layer,name=honeycomb-tsr,mode=single,affected=yes")
        self.GEN.COM("affected_layer,name=honeycomb-bsr,mode=single,affected=yes")
        # self.GEN.COM("sel_contourize,accuracy=50.8,break_to_islands=yes,clean_hole_size=76.2,clean_hole_mode=x_and_y")
        # --整体化成一整块
        self.GEN.COM("sel_contourize,accuracy=50.8,break_to_islands=no,clean_hole_size=76.2,clean_hole_mode=x_and_y")
        self.GEN.CLEAR_LAYER()

    def copy_sr_honeycomb(self, target_top=None, target_bot=None):
        """
        品字形,sr范围内的蜂窝铜copy到相应层别
        :param target_top: 内层top面
        :param target_bot: 内层bot面
        :return:
        """
        # --分别copy到honeycomb-tok和honeycomb-bok
        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.GEN.COM("affected_layer,name=honeycomb-tsr,mode=single,affected=yes")
        self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=%s,invert=no,dx=0,dy=0,size=0,"
                     "x_anchor=0,y_anchor=0,rotation=0,mirror=none" % target_top)

        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.GEN.COM("affected_layer,name=honeycomb-bsr,mode=single,affected=yes")
        self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=%s,invert=no,dx=0,dy=0,size=0,"
                     "x_anchor=0,y_anchor=0,rotation=0,mirror=none" % target_bot)

    def remove_small_surface(self, size=431, target_top='honeycomb-tok', target_bot='honeycomb-bok'):
        """
        通过两次resize,去掉尖角和小于5mil的surface
        :return:
        :rtype:
        """
        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.GEN.COM("affected_layer,name=%s,mode=single,affected=yes" % target_top)
        self.GEN.COM("affected_layer,name=%s,mode=single,affected=yes" % target_bot)
        if size == 1000:
            if platform.system() == "Windows":
                # windows环境下,梯形symbol的尖角在resize时没有圆角处理，导致output时报SIP错误
                # 李家兴2019.11.08依据story-view-156修改
                self.GEN.COM('sel_resize,size=-1000,corner_ctl=yes')
                self.GEN.COM('sel_resize,size=1000,corner_ctl=yes')
                self.GEN.COM('fill_params,type=solid,origin_type=datum,solid_type=fill,std_type=line,min_brush=999,'
                             'use_arcs=yes,symbol=,dx=2.54,dy=2.54,std_angle=45,std_line_width=254,std_step_dist=1270,'
                             'std_indent=odd,break_partial=yes,cut_prims=no,outline_draw=no,outline_width=0,outline_invert=no')
                self.GEN.COM('sel_fill')
                self.GEN.FILL_SUR_PARAMS()
                self.GEN.COM('sel_contourize, accuracy=6.35, break_to_islands=no, clean_hole_size=76.2')
            else:
                self.GEN.SEL_RESIZE(-1000)
                self.GEN.SEL_RESIZE(1000)
        else:
            self.GEN.COM("sel_resize,size=-%s,corner_ctl=no" % size)
            self.GEN.COM("sel_resize,size=%s,corner_ctl=no" % size)
            self.GEN.COM('sel_contourize, accuracy=6.35, break_to_islands=no, clean_hole_size=76.2')

    def corner_copper(self, copper_dis=None, target_top='honeycomb-tok', target_bot='honeycomb-bok',
                      cur_lamin_num=None):
        """
        四角铺铜皮
        :return:
        :rtype:
        """
        job_signal_numbers = len(pb.inner) + 2
        sr_xmin = self.parm.sr_xmin
        sr_ymin = self.parm.sr_ymin
        sr_xmax = self.parm.sr_xmax
        sr_ymax = self.parm.sr_ymax
        profile_xmin = self.parm.profile_xmin
        profile_ymin = self.parm.profile_ymin
        profile_xmax = self.parm.profile_xmax
        profile_ymax = self.parm.profile_ymax
        rout_x = self.parm.rout_x
        rout_y = self.parm.rout_y
        top_after_margin = self.parm.top_after_margin
        left_after_margin = self.parm.left_after_margin
        lam_rout = self.parm.lam_rout
        # --切铜参数定义
        # --20210118新规则,所有板层同六层板
        # --20210209内层铺铜，四层板仍然要求距锣边1mm
        if job_signal_numbers == 4:
            if left_after_margin >= 7:
                cut_corner_x1 = sr_xmin - 2.5
                cut_corner_x2 = sr_xmax + 2.5
            else:
                cut_corner_x1 = sr_xmin - 1.5
                cut_corner_x2 = sr_xmax + 1.5
            if top_after_margin >= 7:
                cut_corner_y2 = sr_ymax + 2.5
                cut_corner_y1 = sr_ymin - 2.5
            else:
                cut_corner_y2 = sr_ymax + 1.5
                cut_corner_y1 = sr_ymin - 1.5
        else:
            cut_corner_x1 = sr_xmin - 2.5
            cut_corner_y1 = sr_ymin - 2.5
            cut_corner_x2 = sr_xmax + 2.5
            cut_corner_y2 = sr_ymax + 2.5
        # cut_corner_x1 = sr_xmin - 2.5
        # cut_corner_y1 = sr_ymin - 2.5
        # cut_corner_x2 = sr_xmax + 2.5
        # cut_corner_y2 = sr_ymax + 2.5
        # --四角铺铜皮
        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.create_tmp_layer('honeycomb-tmp2')
        self.GEN.COM("affected_layer,name=honeycomb-tmp2,mode=single,affected=yes")
        self.GEN.COM("fill_params,type=solid,origin_type=datum,solid_type=surface,std_type=line,min_brush=25.4,"
                     "use_arcs=yes,symbol=,dx=2.54,dy=2.54,std_angle=45,std_line_width=254,std_step_dist=1270,"
                     "std_indent=odd,break_partial=yes,cut_prims=no,outline_draw=no,outline_width=0,outline_invert=no")
        # --20210118新规则,所有板层同六层板
        # --20210209内层铺铜，四层板仍然要求距锣边1mm
        if cur_lamin_num:
            for item in lam_rout:
                if item[0] == cur_lamin_num:
                    cur_routx = item[1]
                    cur_routy = item[2]
                    # --四层板距profile(锣边)1mm === HDI距每次锣边 2mm
                    step_margin_x = (profile_xmax - cur_routx) * 0.5 + 2
                    step_margin_y = (profile_ymax - cur_routy) * 0.5 + 2
                    self.GEN.COM("sr_fill,polarity=positive,step_margin_x=%s,step_margin_y=%s,step_max_dist_x=2540,"
                                 "step_max_dist_y=2540,sr_margin_x=0,sr_margin_y=0,sr_max_dist_x=0,sr_max_dist_y=0,nest_sr=no,"
                                 "consider_feat=no,consider_drill=no,consider_rout=no,dest=affected_layers,attributes=no"
                                 % (step_margin_x, step_margin_y))

        else:
            # step_margin_x = '-5'
            # step_margin_y = '-5'
            step_margin_x = 2
            step_margin_y = 2
            self.GEN.COM("sr_fill,polarity=positive,step_margin_x=%s,step_margin_y=%s,step_max_dist_x=2540,"
                         "step_max_dist_y=2540,sr_margin_x=2.5,sr_margin_y=2.5,sr_max_dist_x=0,sr_max_dist_y=0,nest_sr=no,"
                         "consider_feat=no,consider_drill=no,consider_rout=no,dest=affected_layers,attributes=no"
                         % (step_margin_x, step_margin_y))
        # self.GEN.COM("sr_fill,polarity=positive,step_margin_x=-5,step_margin_y=-5,step_max_dist_x=2540,"
        #              "step_max_dist_y=2540,sr_margin_x=2.5,sr_margin_y=2.5,sr_max_dist_x=0,sr_max_dist_y=0,nest_sr=no,"
        #              "consider_feat=no,consider_drill=no,consider_rout=no,dest=affected_layers,attributes=no")
        self.GEN.COM("clip_area_strt")
        self.GEN.COM("clip_area_xy,x=%s,y=%s" % (cut_corner_x1, cut_corner_y1))
        self.GEN.COM("clip_area_xy,x=%s,y=%s" % (cut_corner_x2, cut_corner_y2))
        self.GEN.COM("clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=rectangle,"
                     "inout=inside,contour_cut=yes,margin=0,feat_types=line\;pad\;surface\;arc\;text")
        # --判断sr距profile够不够55mm.
        enough_dis_y = sr_ymin - profile_ymin
        enough_dis_x = sr_xmin - profile_xmin
        if enough_dis_y <= 55:
            cut_corner_y1 = profile_ymin + 60
            cut_corner_y2 = profile_ymax - 60
            if copper_dis:
                # --梯形板边封角为60mm
                cut_corner_y1 = profile_ymin + copper_dis
                cut_corner_y2 = profile_ymax - copper_dis
        else:
            enough_dis_y = enough_dis_y + 5
            cut_corner_y1 = profile_ymin + enough_dis_y
            cut_corner_y2 = profile_ymax - enough_dis_y
        cut_corner_x1 = profile_xmin - 6
        cut_corner_x2 = profile_xmax + 6
        self.GEN.COM("clip_area_strt")
        self.GEN.COM("clip_area_xy,x=%s,y=%s" % (cut_corner_x1, cut_corner_y1))
        self.GEN.COM("clip_area_xy,x=%s,y=%s" % (cut_corner_x2, cut_corner_y2))
        self.GEN.COM("clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=rectangle,inout=inside,"
                     "contour_cut=yes,margin=0,feat_types=line\;pad\;surface\;arc\;text")
        if enough_dis_x <= 55:
            cut_corner_x1 = profile_xmin + 60
            cut_corner_x2 = profile_xmax - 60
        else:
            enough_dis_x = enough_dis_x + 5
            cut_corner_x1 = profile_xmin + enough_dis_x
            cut_corner_x2 = profile_xmax - enough_dis_x
        cut_corner_y1 = profile_ymin - 6
        cut_corner_y2 = profile_ymax + 6
        self.GEN.COM("clip_area_strt")
        self.GEN.COM("clip_area_xy,x=%s,y=%s" % (cut_corner_x1, cut_corner_y1))
        self.GEN.COM("clip_area_xy,x=%s,y=%s" % (cut_corner_x2, cut_corner_y2))
        self.GEN.COM("clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=rectangle,inout=inside,"
                     "contour_cut=yes,margin=0,feat_types=line\;pad\;surface\;arc\;text")
        self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=%s,invert=no,dx=0,dy=0,size=0,"
                     "x_anchor=0,y_anchor=0,rotation=0,mirror=none" % target_top)
        self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=%s,invert=no,dx=0,dy=0,size=0,"
                     "x_anchor=0,y_anchor=0,rotation=0,mirror=none" % target_bot)

    def add_gold_line(self, target_top=None, target_bot=None):
        """
        绕内profile一圈添加金线
        :return:
        :rtype:
        """
        job_signal_numbers = len(pb.inner) + 2
        sr_xmin = self.parm.sr_xmin
        sr_ymin = self.parm.sr_ymin
        sr_xmax = self.parm.sr_xmax
        sr_ymax = self.parm.sr_ymax
        profile_xmin = self.parm.profile_xmin
        profile_ymin = self.parm.profile_ymin
        profile_xmax = self.parm.profile_xmax
        profile_ymax = self.parm.profile_ymax
        pn_eight = self.JOB[7]
        if pn_eight in ['y', 'r', 'l']:
            if job_signal_numbers >= 4:
                line_x1 = sr_xmin - 1.25
                line_x2 = sr_xmin + 15
                line_x3 = sr_xmax - 15
                line_x4 = sr_xmax + 1.25
                line_y1 = sr_ymin - 1.25
                line_y2 = sr_ymin + 15
                line_y3 = sr_ymax - 15
                line_y4 = sr_ymax + 1.25
                self.GEN.COM("clear_layers")
                self.GEN.COM("affected_layer,mode=all,affected=no")
                self.create_tmp_layer('honeycomb-tmp2')
                self.GEN.COM("affected_layer,name=honeycomb-tmp2,mode=single,affected=yes")
                self.GEN.COM(
                    "add_line,attributes=no,xs=%s,ys=%s,xe=%s,ye=%s,symbol=s1500,polarity=positive,bus_num_lines=0,"
                    "bus_dist_by=pitch,bus_distance=0,bus_reference=left" % (line_x1, line_y2, line_x1, line_y3))
                self.GEN.COM(
                    "add_line,attributes=no,xs=%s,ys=%s,xe=%s,ye=%s,symbol=s1500,polarity=positive,bus_num_lines=0,"
                    "bus_dist_by=pitch,bus_distance=0,bus_reference=left" % (line_x4, line_y2, line_x4, line_y3))
                self.GEN.COM(
                    "add_line,attributes=no,xs=%s,ys=%s,xe=%s,ye=%s,symbol=s1500,polarity=positive,bus_num_lines=0,"
                    "bus_dist_by=pitch,bus_distance=0,bus_reference=left" % (line_x2, line_y1, line_x3, line_y1))
                self.GEN.COM(
                    "add_line,attributes=no,xs=%s,ys=%s,xe=%s,ye=%s,symbol=s1500,polarity=positive,bus_num_lines=0,"
                    "bus_dist_by=pitch,bus_distance=0,bus_reference=left" % (line_x2, line_y4, line_x3, line_y4))
                loop_num_y = int((sr_ymax - sr_ymin - 30) / 22)
                loop_num_x = int((sr_xmax - sr_xmin - 30) / 22)
                # --线水平方向
                for i in range(1, loop_num_y + 1):
                    s_pad_y = sr_ymin + 22 * i
                    self.GEN.COM("add_line,attributes=no,xs=%s,ys=%s,xe=%s,ye=%s,symbol=s3000,polarity=negative,"
                                 "bus_num_lines=0,bus_dist_by=pitch,bus_distance=0,bus_reference=left"
                                 % (profile_xmin, s_pad_y, profile_xmax, s_pad_y))
                # --线垂直方向
                for i in range(1, loop_num_x + 1):
                    s_pad_x = sr_xmin + 22 * i
                    self.GEN.COM("add_line,attributes=no,xs=%s,ys=%s,xe=%s,ye=%s,symbol=s3000,polarity=negative,"
                                 "bus_num_lines=0,bus_dist_by=pitch,bus_distance=0,bus_reference=left"
                                 % (s_pad_x, profile_ymin, s_pad_x, profile_ymax))
                self.GEN.COM(
                    "sel_contourize,accuracy=50.8,break_to_islands=yes,clean_hole_size=76.2,clean_hole_mode=x_and_y")
                self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=%s,invert=no,dx=0,dy=0,size=0,"
                             "x_anchor=0,y_anchor=0,rotation=0,mirror=none" % target_top)
                self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=%s,invert=no,dx=0,dy=0,size=0,"
                             "x_anchor=0,y_anchor=0,rotation=0,mirror=none" % target_bot)

    def fill_pitch(self, direct, target_top=None, target_bot=None):
        """
        排版间距之间的铺铜
        :return:
        :rtype:
        """
        sr_xmin = self.parm.sr_xmin
        sr_ymin = self.parm.sr_ymin
        sr_xmax = self.parm.sr_xmax
        sr_ymax = self.parm.sr_ymax
        add_eagle_panel = '否'
        # add_eagle_panel = self.parm.add_eagle_panel
        # --solid fill tmp2
        if direct == 'horizontal':
            margin_x = 10
            margin_y = 0.5

            margin2_x = 0
            margin2_y = 2.0
        else:
            margin_y = 10
            margin_x = 0.5

            margin2_y = 0
            margin2_x = 2.0
        self.GEN.CLEAR_LAYER()
        self.GEN.DELETE_LAYER('eagle-clear-pitch')
        if add_eagle_panel == '是':
            self.GEN.COM("copy_layer,source_job=%s,source_step=%s,source_layer=eagle-dot-pitch,"
                         "dest=layer_name,dest_layer=eagle-clear-pitch,mode=append,invert=no" % (self.JOB, self.STEP))
            self.GEN.AFFECTED_LAYER('eagle-clear-pitch', 'yes')
            self.GEN.SEL_CHANEG_SYM('s1651')
            self.GEN.CLEAR_LAYER()

        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.create_tmp_layer('honeycomb-tmp1')

        self.create_tmp_layer('honeycomb-tmp2')
        self.create_tmp_layer('honeycomb-tmp3')

        self.create_tmp_layer('honeycomb-tmp4')
        self.create_tmp_layer('honeycomb-tmp5')

        self.GEN.COM("affected_layer,name=honeycomb-tmp2,mode=single,affected=yes")
        self.GEN.COM("fill_params,type=solid,origin_type=datum,solid_type=surface,std_type=line,min_brush=25.4,"
                     "use_arcs=yes,symbol=2oz_fw,dx=9.72312,dy=5.588,std_angle=45,std_line_width=254,std_step_dist=1270,"
                     "std_indent=odd,break_partial=yes,cut_prims=yes,outline_draw=no,outline_width=0,outline_invert=no")
        self.GEN.COM("sr_fill,polarity=positive,step_margin_x=-5,step_margin_y=-5,step_max_dist_x=2540,"
                     "step_max_dist_y=2540,sr_margin_x=%s,sr_margin_y=%s,sr_max_dist_x=0,sr_max_dist_y=0,nest_sr=no,"
                     "consider_feat=no,consider_drill=no,consider_rout=no,dest=affected_layers,attributes=no"
                     % (margin_x, margin_y))

        # --clip掉板外部分
        self.GEN.COM("clip_area_strt")
        self.GEN.COM("clip_area_xy,x=%s,y=%s" % (sr_xmin, sr_ymin))
        self.GEN.COM("clip_area_xy,x=%s,y=%s" % (sr_xmax, sr_ymax))
        self.GEN.COM("clip_area_end,layers_mode=affected_layers,layer=,area=manual,area_type=rectangle,inout=outside,"
                     "contour_cut=yes,margin=0,feat_types=line\;pad\;surface\;arc\;text")

        # --solid fill tmp1,以下步骤对品字形排版有用
        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.GEN.COM("affected_layer,name=honeycomb-tmp1,mode=single,affected=yes")
        self.GEN.COM("fill_params,type=solid,origin_type=datum,solid_type=surface,std_type=line,min_brush=25.4,"
                     "use_arcs=yes,symbol=2oz_fw,dx=9.72312,dy=5.588,std_angle=45,std_line_width=254,std_step_dist=1270,"
                     "std_indent=odd,break_partial=yes,cut_prims=yes,outline_draw=no,outline_width=0,outline_invert=no")
        self.GEN.COM("sr_fill,polarity=positive,step_margin_x=-5,step_margin_y=-5,step_max_dist_x=2540,"
                     "step_max_dist_y=2540,sr_margin_x=2.5,sr_margin_y=2.5,sr_max_dist_x=0,sr_max_dist_y=0,nest_sr=no,"
                     "consider_feat=no,consider_drill=no,consider_rout=no,dest=affected_layers,attributes=no")
        # --resize tmp1然后copy到tmp2
        self.GEN.COM("sel_resize,size=4000,corner_ctl=no")
        self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=honeycomb-tmp2,invert=yes,dx=0,dy=0,size=0,"
                     "x_anchor=0,y_anchor=0,rotation=0,mirror=none")
        self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=honeycomb-tmp4,invert=no,dx=0,dy=0,size=0,"
                     "x_anchor=0,y_anchor=0,rotation=0,mirror=none")
        # -- 在tmp5层别铺铜，延step外围 后续此层别被替换为反面外围铜
        self.GEN.CLEAR_LAYER()
        self.GEN.AFFECTED_LAYER('honeycomb-tmp5', 'yes')
        self.GEN.COM("fill_params,type=solid,origin_type=datum,solid_type=surface,std_type=line,min_brush=25.4,"
                     "use_arcs=yes,symbol=2oz_fw,dx=9.72312,dy=5.588,std_angle=45,std_line_width=254,std_step_dist=1270,"
                     "std_indent=odd,break_partial=yes,cut_prims=yes,outline_draw=no,outline_width=0,outline_invert=no")
        self.GEN.COM("sr_fill,polarity=positive,step_margin_x=-5,step_margin_y=-5,step_max_dist_x=2540,"
                     "step_max_dist_y=2540,sr_margin_x=%s,sr_margin_y=%s,sr_max_dist_x=0,sr_max_dist_y=0,nest_sr=no,"
                     "consider_feat=no,consider_drill=no,consider_rout=no,dest=affected_layers,attributes=no"
                     % (margin2_x, margin2_y))
        self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=honeycomb-tmp4,invert=yes,dx=0,dy=0,size=0,"
                     "x_anchor=0,y_anchor=0,rotation=0,mirror=none")
        self.GEN.CLEAR_LAYER()
        self.GEN.AFFECTED_LAYER('honeycomb-tmp4', 'yes')
        # === 让出角线位置
        self.GEN.ADD_PAD(sr_xmin, sr_ymin, 's5000', pol='negative')
        self.GEN.ADD_PAD(sr_xmax, sr_ymin, 's5000', pol='negative')
        self.GEN.ADD_PAD(sr_xmin, sr_ymax, 's5000', pol='negative')
        self.GEN.ADD_PAD(sr_xmax, sr_ymax, 's5000', pol='negative')

        self.GEN.COM("sel_contourize,accuracy=50.8,break_to_islands=yes,clean_hole_size=76.2,clean_hole_mode=x_and_y")
        self.GEN.COM('clip_area_strt')
        self.GEN.COM(
            'clip_area_end,layers_mode=affected_layers,layer=,area=profile,area_type=rectangle,inout=outside,contour_cut=no,margin=0,feat_types=line\;pad\;surface\;arc\;text')
        # === 外围一圈线
        self.GEN.COM("copy_layer,source_job=%s,source_step=%s,source_layer=honeycomb-tmp4,"
                     "dest=layer_name,dest_layer=honeycomb-tmp5,mode=replace,invert=no" % (self.JOB, self.STEP))
        # self.GEN.SEL_COPY('honeycomb-tmp2')
        self.GEN.CLEAR_LAYER()

        # --整体化tmp2
        self.GEN.COM("clear_layers")
        self.GEN.COM("affected_layer,mode=all,affected=no")
        self.GEN.COM("affected_layer,name=honeycomb-tmp2,mode=single,affected=yes")
        self.GEN.COM("sel_contourize,accuracy=50.8,break_to_islands=yes,clean_hole_size=76.2,clean_hole_mode=x_and_y")
        self.GEN.SEL_COPY('honeycomb-tmp3')
        # --挑选出排版间距之间的铺铜
        self.GEN.COM("filter_reset,filter_name=popup")
        self.GEN.COM("filter_set,filter_name=popup,update_popup=no,feat_types=surface")
        self.GEN.COM("filter_set,filter_name=popup,update_popup=no,polarity=positive")
        self.GEN.FILTER_SELECT()
        self.GEN.COM("affected_layer,name=honeycomb-tmp4,mode=single,affected=yes")

        count = self.GEN.GET_SELECT_COUNT()
        if count > 0:
            # === 为区分正反面，增加层别 ===
            self.GEN.COM('sel_clear_feat')
            if add_eagle_panel == '是':
                self.GEN.COM("copy_layer,source_job=%s,source_step=%s,source_layer=eagle-clear-pitch,"
                             "dest=layer_name,dest_layer=honeycomb-tmp2,mode=append,invert=yes" % (self.JOB, self.STEP))
                self.GEN.COM("affected_layer,name=honeycomb-tmp2,mode=single,affected=no")

            # === top面 ===
            line_length = 5
            line_gap = 2
            split_length = line_length + line_gap
            gap_sym = 's%s' % (line_gap * 1000)
            # 用线去填充.
            loop_num_y = int((sr_ymax - sr_ymin) / split_length)
            loop_num_x = int((sr_xmax - sr_xmin) / split_length)

            fix_start_x = sr_xmin - 3
            fix_end_x = sr_xmax + 3
            fix_start_y = sr_ymin - 3
            fix_end_y = sr_ymax + 3
            # --线水平方向
            if direct == 'vertical':
                for i in range(1, loop_num_y + 1):
                    s_pad_y = sr_ymin + split_length * i
                    self.GEN.COM("add_line,attributes=no,xs=%s,ys=%s,xe=%s,ye=%s,symbol=%s,polarity=negative,"
                                 "bus_num_lines=0,bus_dist_by=pitch,bus_distance=0,bus_reference=left"
                                 % (fix_start_x, s_pad_y, fix_end_x, s_pad_y, gap_sym))
            # --线垂直方向
            if direct == 'horizontal':
                for i in range(1, loop_num_x + 1):
                    s_pad_x = sr_xmin + split_length * i
                    self.GEN.COM("add_line,attributes=no,xs=%s,ys=%s,xe=%s,ye=%s,symbol=%s,polarity=negative,"
                                 "bus_num_lines=0,bus_dist_by=pitch,bus_distance=0,bus_reference=left"
                                 % (s_pad_x, fix_start_y, s_pad_x, fix_end_y, gap_sym))
                # === V2.00 按需求3689 取消 ===
                # gold_finger_c = self.JOB[7]
                # if gold_finger_c == "n":
                #     self.GEN.COM ("sel_delete")

            self.GEN.CLEAR_LAYER()
            self.GEN.AFFECTED_LAYER('honeycomb-tmp2', 'yes')
            self.GEN.COM(
                "sel_contourize,accuracy=50.8,break_to_islands=yes,clean_hole_size=76.2,clean_hole_mode=x_and_y")
            self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=%s,invert=no,dx=0,dy=0,size=0,"
                         "x_anchor=0,y_anchor=0,rotation=0,mirror=none" % target_top)
            self.GEN.CLEAR_LAYER()

            self.GEN.AFFECTED_LAYER('honeycomb-tmp4', 'yes')
            self.GEN.COM(
                "sel_contourize,accuracy=50.8,break_to_islands=yes,clean_hole_size=76.2,clean_hole_mode=x_and_y")
            self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=%s,invert=no,dx=0,dy=0,size=0,"
                         "x_anchor=0,y_anchor=0,rotation=0,mirror=none" % target_top)
            self.GEN.CLEAR_LAYER()

            self.GEN.AFFECTED_LAYER('honeycomb-tmp3', 'yes')
            self.GEN.AFFECTED_LAYER('honeycomb-tmp5', 'yes')

            if add_eagle_panel == '是':
                self.GEN.COM("copy_layer,source_job=%s,source_step=%s,source_layer=eagle-clear-pitch,"
                             "dest=layer_name,dest_layer=honeycomb-tmp3,mode=append,invert=yes" % (self.JOB, self.STEP))
                self.GEN.AFFECTED_LAYER('honeycomb-tmp3', 'no')

            # === bot 面 ===
            line_length = 5
            line_gap = 2
            split_length = line_length + line_gap
            gap_sym = 's%s' % (line_gap * 1000)
            # 用线去填充.
            loop_num_y = int((sr_ymax - sr_ymin) / split_length)
            loop_num_x = int((sr_xmax - sr_xmin) / split_length)
            fix_start_x = sr_xmin - 3
            fix_end_x = sr_xmax + 3
            fix_start_y = sr_ymin - 3
            fix_end_y = sr_ymax + 3
            # --线水平方向
            if direct == 'vertical':
                for i in range(1, loop_num_y + 1):
                    s_pad_y = sr_ymin + split_length * i - 2
                    self.GEN.COM("add_line,attributes=no,xs=%s,ys=%s,xe=%s,ye=%s,symbol=%s,polarity=negative,"
                                 "bus_num_lines=0,bus_dist_by=pitch,bus_distance=0,bus_reference=left"
                                 % (fix_start_x, s_pad_y, fix_end_x, s_pad_y, gap_sym))
            # --线垂直方向
            if direct == 'horizontal':
                for i in range(1, loop_num_x + 1):
                    s_pad_x = sr_xmin + split_length * i - 2
                    self.GEN.COM("add_line,attributes=no,xs=%s,ys=%s,xe=%s,ye=%s,symbol=%s,polarity=negative,"
                                 "bus_num_lines=0,bus_dist_by=pitch,bus_distance=0,bus_reference=left"
                                 % (s_pad_x, fix_start_y, s_pad_x, fix_end_y, gap_sym))
            # === V2.00 按需求3689 取消 ===
            # gold_finger_c = self.JOB[7]
            # if gold_finger_c == "n":
            #     self.GEN.COM ("sel_delete")

            self.GEN.CLEAR_LAYER()
            self.GEN.AFFECTED_LAYER('honeycomb-tmp3', 'yes')
            self.GEN.COM(
                "sel_contourize,accuracy=50.8,break_to_islands=yes,clean_hole_size=76.2,clean_hole_mode=x_and_y")
            self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=%s,invert=no,dx=0,dy=0,size=0,"
                         "x_anchor=0,y_anchor=0,rotation=0,mirror=none" % target_bot)
            self.GEN.CLEAR_LAYER()

            self.GEN.AFFECTED_LAYER('honeycomb-tmp5', 'yes')
            self.GEN.COM(
                "sel_contourize,accuracy=50.8,break_to_islands=yes,clean_hole_size=76.2,clean_hole_mode=x_and_y")
            self.GEN.COM("sel_copy_other,dest=layer_name,target_layer=%s,invert=no,dx=0,dy=0,size=0,"
                         "x_anchor=0,y_anchor=0,rotation=0,mirror=none" % target_bot)
            self.GEN.CLEAR_LAYER()

    def create_tmp_layer(self, layer):
        """
        创建临时层别
        :return:
        :rtype:
        """
        info = self.GEN.DO_INFO('-t layer -e %s/panel/%s -d EXISTS' % (jobname, layer))
        if info['gEXISTS'] == "no":
            self.GEN.COM('create_layer,layer=%s,context=misc,type=signal,polarity=positive,ins_layer=' % layer)
        else:
            # --删除当前panel中内容物，这样不用创建新层，其它step中的内容会被保留
            self.GEN.AFFECTED_LAYER(layer, 'yes')
            self.GEN.COM('sel_delete')
            self.GEN.AFFECTED_LAYER(layer, 'no')

    def add_inn_eagle_pad(self):
        """
        在铺铜时已经添加好的层别进行鹰眼pad的copy
        :return:
        """

        fill_array = self.parm.fill_array

        self.GEN.CLEAR_LAYER()
        for fill_hash in fill_array:
            layer_name = fill_hash.layer_name
            layer_mode = fill_hash.layer_mode
            if layer_mode == 'sec':
                if self.GEN.LAYER_EXISTS('song-tmp', job=self.JOB, step=self.STEP) == 'yes':
                    self.GEN.AFFECTED_LAYER('song-tmp', 'yes')
                    self.GEN.SEL_COPY(layer_name)
                self.GEN.CLEAR_LAYER()
                if self.GEN.LAYER_EXISTS('song-create-tmp', job=self.JOB, step=self.STEP) == 'yes':
                    # --song-create-tmp板边的蝴蝶pad
                    self.GEN.AFFECTED_LAYER('song-create-tmp', 'yes')
                    # --删除与外层symbol相连接的鹰眼pad
                    self.GEN.FILTER_RESET()
                    self.GEN.SEL_REF_FEAT(layer_name, 'disjoint', f_type='line;pad;arc;text')
                    if int(self.GEN.GET_SELECT_COUNT()) > 0:
                        self.GEN.SEL_COPY(layer_name)
                self.GEN.CLEAR_LAYER()
        # === pad eagle
        self.GEN.DELETE_LAYER('song-tmp')
        self.GEN.DELETE_LAYER('song-create-tmp')

class InPlan:
    def __init__(self, job):
        # --Oracle相关参数定义
        self.JOB_SQL = job.replace(jobname[13:], '').upper()
        self.DB_O = Oracle_DB.ORACLE_INIT()
        self.dbc_h = self.DB_O.DB_CONNECT(host='172.20.218.193', servername='inmind.fls', port='1521',
                                          username='GETDATA', passwd='InplanAdmin')
        if not self.dbc_h:
            pass

    def __del__(self):
        # --关闭数据库连接
        if self.dbc_h:
            self.DB_O.DB_CLOSE(self.dbc_h)

    def get_Layer_Info(self):
        """
        铜厚信息
        """
        sql = """        
        SELECT            
            a.item_name,
            LOWER(c.item_name) AS LAYER_NAME, 
            round( d.required_cu_weight / 28.3495, 2 )  AS CU_WEIGHT           
            FROM
            vgt_hdi.ALL_ITEMS a,
             vgt_hdi.job b,
            vgt_hdi.ALL_ITEMS c,
            vgt_hdi.copper_layer d
            WHERE

            a.item_id = b.item_id  
             and a.revision_id= b.revision_id
             and a.ITEM_TYPE = 2
              AND a.root_id = c.root_id 
                and c.ITEM_TYPE = 3
            AND c.item_id = d.item_id 
            and c.revision_id = d.revision_id
         AND a.item_name = '%s' 
            ORDER BY
            d.layer_index
        """ % self.JOB_SQL
        process_data = self.DB_O.SELECT_DIC(self.dbc_h, sql)
        return process_data

    def getLaminData(self):
        """
        获取压合信息
        :return:
        """
        sql = """
        SELECT            
         a.item_name AS job_name,
          p.mrp_name AS mrpName,
        d.process_num_ AS process_num,
        d.pressed_pnl_x_ / 1000 AS pnlroutx,
        d.pressed_pnl_y_ / 1000 AS pnlrouty,
        'L'|| d.layer_index_top_ AS fromLay, 
         'L'|| d.layer_index_bot_ AS toLay    
    FROM
        vgt_hdi.ALL_ITEMS a,
        vgt_hdi.job b,
         vgt_hdi.ALL_ITEMS c,
         vgt_hdi.process p,
         vgt_hdi.process_da d
    WHERE
            a.item_id = b.item_id  
            and a.revision_id= b.revision_id
            and a.ITEM_TYPE = 2
            AND a.root_id = c.root_id 
            and c.ITEM_TYPE = 7
            AND c.item_id = p.item_id 
            and c.revision_id = p.revision_id
            AND p.item_id = d.item_id 
            AND p.revision_id = d.revision_id 
            AND P.proc_subtype IN ( 28, 29 ) 
            AND a.item_name = '%s'
        ORDER BY
              d.process_num_ """ % self.JOB_SQL
        process_data = self.DB_O.SELECT_DIC(self.dbc_h, sql)

        return process_data

    # def getLaminData(self):
    #     """
    #     获取压合信息
    #     :return:
    #     """
    #     sql = """
    #     SELECT
    #         a.item_name AS job_name,
    #         d.mrp_name AS mrpName,
    #         e.process_num_ AS process_num,
    #         b.pnl_size_x / 1000 AS pnlXInch,
    #         b.pnl_size_Y / 1000 AS pnlYInch,
    #         e.pressed_pnl_x_ / 1000 AS pnlroutx,
    #         e.pressed_pnl_y_ / 1000 AS pnlrouty,
    #         (case when  e.film_bg_ not like '%%,%%' then
    #                     'L'|| TO_CHAR(TO_NUMBER(substr(REGEXP_SUBSTR( d.mrp_name, '[^-]+', 1,2 ),2,2), '99')) else
    #                     REGEXP_SUBSTR( e.film_bg_, '[^,]+', 1, 1 ) end) fromLay,
    #         (case when  e.film_bg_ not like '%%,%%' then
    #         'L'|| TO_CHAR(TO_NUMBER(substr(REGEXP_SUBSTR( d.mrp_name, '[^-]+', 1,2 ),4,2), '99')) else
    #         REGEXP_SUBSTR( e.film_bg_, '[^,]+', 1, 2 ) end) toLay,
    #         ROUND( e.PRESSED_THICKNESS_ / 39.37, 2 ) AS yhThick,
    #         ROUND( e.PRESSED_THICKNESS_TOL_PLUS_ / 39.37, 2 ) AS yhThkPlus,
    #         ROUND( e.PRESSED_THICKNESS_TOL_MINUS_ / 39.37, 2 ) AS yhThkDown,
    #         e.LASER_BURN_TARGET_ V5laser
    #     FROM
    #         vgt_hdi.items a
    #         INNER JOIN vgt_hdi.job b ON a.item_id = b.item_id
    #         AND a.last_checked_in_rev = b.revision_id
    #         INNER JOIN vgt_hdi.public_items c ON a.root_id = c.root_id
    #         INNER JOIN vgt_hdi.process d ON c.item_id = d.item_id
    #         AND c.revision_id = d.revision_id
    #         INNER JOIN vgt_hdi.process_da e ON d.item_id = e.item_id
    #         AND d.revision_id = e.revision_id
    #     WHERE
    #         a.item_name = '%s'
    #         AND d.proc_type = 1
    #         AND d.proc_subtype IN ( 28, 29 )
    #     ORDER BY
    #         e.process_num_""" % self.JOB_SQL
    #     process_data = self.DB_O.SELECT_DIC(self.dbc_h,sql)
    #
    #     return process_data

    def get_stuck_data(self):
        """
        获取排版尺寸信息
        """
        sql = """
            SELECT ITEM_NAME as JOB_NAME，
                (select Round(PCB_SIZE_X/39.37,3) from VGT_HDI.PART where item_id=ITEM.ITEM_ID   and REVISION_ID=ITEM.REVISION_ID) as PCB_X，
                (select Round(PCB_SIZE_Y/39.37,3) from VGT_HDI.PART where item_id=ITEM.ITEM_ID   and REVISION_ID=ITEM.REVISION_ID) as PCB_Y，
                 Round(SET_SIZE_X_/39.37,3) as SET_X，
                 Round(SET_SIZE_Y_/39.37,3) as SET_Y，
                 Round(PNL_SIZE_X/1000,2) as PNL_X，
                 Round(PNL_SIZE_Y/1000,2) as PNL_Y，
                 PCS_PER_SET_  as SET_PCS，
                 NUM_PCBS as Panel_PCS，
                 NUM_ARRAYS as Panel_SET，
                 SPACING_X_ as Spacing_X，
                 SPACING_Y_ as Spacing_Y
            FROM VGT_HDI.ALL_ITEMS ITEM,  VGT_HDI.JOB,  VGT_HDI.JOB_DA,   VGT_HDI.REV_CONTROLLED_LOB
            where ITEM.item_id=Job.item_id
                and  ITEM.revision_id=Job.REVISION_ID
                and ITEM.item_id=JOB_DA.item_id
                and  ITEM.revision_id=JOB_DA.REVISION_ID
                and JOB_DA.STACKUP_IMAGE_=REV_CONTROLLED_LOB.LOB_ID
                and ITEM_TYPE = 2
                and ITEM_NAME='%s'
                    """ % self.JOB_SQL
        job_data = self.DB_O.SELECT_DIC(self.dbc_h, sql)[0]
        return job_data

    def getPanelSRTable(self):
        sql = '''select a.item_name JOB_NAME,
               e.item_name PANEL_STEP,
               case when d.coupon_sequential_index >0
               then (select coup.name from vgt_hdi.coupon coup
                     where coup.item_id = b.item_id
                       and coup.revision_id = b.revision_id
                       and d.coupon_sequential_index = coup.sequential_index)
               Else (select decode(count(*), 1, 'PCS', 2, 'SET', 3, 'SET', 4, 'SET')
                    from vgt_hdi.panel pnl, vgt_hdi.public_items im2
                    where im2.root_id = a.root_id
                    and pnl.item_id = im2.item_id
                    and pnl.revision_id = im2.revision_id)
               end OP_STEP,
               case when d.coupon_sequential_index >0
               then (select round(coup.size_y/1000,1)||'' from vgt_hdi.coupon coup
                     where coup.item_id = b.item_id
                       and coup.revision_id = b.revision_id
                       and d.coupon_sequential_index = coup.sequential_index)
               Else 'No'
               end COUPON_HEIGHT,
               case when d.coupon_sequential_index >0
               then (select round(coup.size_x/1000,1)||'' from vgt_hdi.coupon coup
                     where coup.item_id = b.item_id
                       and coup.revision_id = b.revision_id
                       and d.coupon_sequential_index = coup.sequential_index)
               Else 'No'
               end COUPON_LENGTH,
               round(d.start_x / 1000,4) start_x,--单位inch
               round(d.start_y / 1000,4) start_y,--单位inch
               d.number_x X_NUM,
               d.number_y Y_NUM,
               round(d.delta_x / 1000,4) delta_x,--单位inch
               round(d.delta_y / 1000,4) delta_y,--单位inch
               d.rotation_angle,--旋转角度
               d.flip--是否镜像
          from vgt_hdi.public_items  a,
               vgt_hdi.job           b,
               vgt_hdi.public_items  e,
               vgt_hdi.panel         c,
               vgt_hdi.layout_repeat d
         where a.item_id = b.item_id
           and a.revision_id = b.revision_id
           and a.root_id = e.root_id
           and e.item_id = c.item_id
           and e.revision_id = c.revision_id
           and c.item_id = d.item_id
           and c.revision_id = d.revision_id
           -- and e.item_name = 'Panel' --默认只筛选Panel
           and e.item_name like 'Panel%%' --默认只筛选Panel
           and a.item_name = '%s'--变量料号名
           and c.is_main = 1''' % self.JOB_SQL
        # 更新自动抓取AB板 新增条件 c.is_main = 1 20230424 by lyh
        dataVal = self.DB_O.SELECT_DIC(self.dbc_h, sql)
        return dataVal

    def get_Cu_thickness(self):
        """
        获取铜厚信息
        """
        ozList = ['1/3OZ', 'HOZ', '1OZ', '1.5OZ', '2OZ', '2.5OZ', '3OZ', '3.5OZ', '4OZ', '4.5OZ', '5OZ']
        ozDic = {
            '0.32': '1/3OZ', '0.33': '1/3OZ', '0.34': '1/3OZ',
            '0.49': 'HOZ', '0.50': 'HOZ', '0.51': 'HOZ',
            '0.99': '1OZ', '1.00': '1OZ', '1.01': '1OZ',
            '1.49': '1.5OZ', '1.50': '1.5OZ', '1.51': '1.5OZ',
            '1.99': '2OZ', '2.00': '2OZ', '2.01': '2OZ',
            '2.49': '2.5OZ', '2.50': '2.5OZ', '2.51': '2.5OZ',
            '2.99': '3OZ', '3.00': '3OZ', '3.01': '3OZ',
            '3.49': '3.5OZ', '3.50': '3.5OZ', '3.51': '3.5OZ',
            '3.99': '4OZ', '4.00': '4OZ', '4.01': '4OZ',
            '4.49': '4.5OZ', '4.50': '4.5OZ', '4.51': '4.5OZ',
            '4.99': '5OZ', '5.00': '5OZ', '5.01': '5OZ'
        }
        dict = {}
        list_data = self.get_Layer_Info()
        if list_data:
            for i in list_data:
                cu_oz = str("%0.2f" % i['CU_WEIGHT'])
                dict[i.get('LAYER_NAME')] = ozDic.get(cu_oz)
            return dict
        else:
            return None

class InfoJob:
    def __init__(self):
        self.inner = []
        res = self.checkJob()
        if res:
            self.getInfo()
        else:
            sys.exit(0)

    def checkJob(self):
        res_check = True
        inner_layers = GEN.GET_ATTR_LAYER('inner')
        inner_num = int(jobname[4:6]) - 2
        if inner_num != len(inner_layers):
            showMessageInfo(u"层数不对,请检查!")
            res_check = False
        try:
            list_numbers = [int(i[1:]) - 2 for i in inner_layers]
            list_numbers.sort()
            if list_numbers != range(inner_num):
                showMessageInfo(u"内层命名错误，请修正!")
                res_check = False
        except:
            showMessageInfo(u"内层命名错误，请修正1!")
            res_check = False
        return res_check

    def getInfo(self):
        matrixInfo = GEN.DO_INFO('-t matrix -e %s/matrix' % jobname)
        for i, lay in enumerate(matrixInfo["gROWname"]):
            if matrixInfo["gROWcontext"][i] == "board":
                if matrixInfo["gROWlayer_type"][i] == "signal" or matrixInfo["gROWlayer_type"][i] == "power_ground":
                    if matrixInfo["gROWside"][i] == "inner":
                        dict_signal = {}
                        dict_signal['name'] = lay
                        if matrixInfo["gROWpolarity"][i] == "positive":
                            dict_signal['pol'] = "positive"
                        else:
                            dict_signal['pol'] = "negative"
                        self.inner.append(dict_signal)

    def pnl_exits(self):
        if 'panel' in GEN.GET_STEP_LIST():
            return True
        else:
            return False

class QComboBox(QtGui.QComboBox):
    def wheelEvent(self, event):
        pass


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    app.setStyle('Cleanlooks')
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    try:
        jobName = os.environ.get("JOB")
        job_cmd = gen.Job(jobName)
    except:
        jobName = 'ha0112gi262a1'
    if not jobName:
        showMessageInfo(u"必须打开料号再运行此程序")
    if 'panel' not in job.getSteps():
        QtGui.QMessageBox.warning(None, u'警告', u'没有panel')
        sys.exit()
    pb = InfoJob()
    inplan = InPlan(jobName)
    lamin_data_check = inplan.getLaminData()
    window = RemoveSlightSection()
    window.show()
    sys.exit(app.exec_())
