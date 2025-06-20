#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:AddDcouponSerialNumber.py
   @author:zl
   @time: 2025/1/15 9:30
   @software:PyCharm
   @desc:
   添加d-coupon序列号
"""
import os
import platform
import sys, re

from PyQt4 import QtCore, QtGui, Qt

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
    sys.path.append(r"\\192.168.2.33\incam-share\incam\Path\OracleClient_x86\instantclient_11_1")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

from genesisPackages_zl import matrixInfo, get_panelset_sr_step, get_layer_selected_limits,get_profile_limits,get_sr_area_flatten

import AddSerialNumberUI_pyqt4 as ui

import genClasses_zl as gen


class AddDcouponSerialNumber(QtGui.QWidget, ui.Ui_Form):
    def __init__(self):
        super(AddDcouponSerialNumber, self).__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        all_steps = get_panelset_sr_step(jobname, "panel")
        d_coupons = list(filter(lambda step: 'd-coupon' in step, all_steps))
        self.listWidget.addItems(d_coupons)
        silkscreens = job.matrix.returnRows('board', 'silk_screen')
        self.comboBox_layer.addItem('')
        self.comboBox_layer.addItems(silkscreens)
        self.comboBox_number_type.addItems(["@_@", "@@_@", "@_@@", "@@_@@", "@@@_@"])
        self.comboBox_number_type.setCurrentIndex(1)
        self.comboBox_number_position.addItems(["", u"在前面", u"在后面"])
        self.comboBox_number_position.setCurrentIndex(1)
        self.comboBox_mirror.addItems(['', 'no', 'yes'])
        self.comboBox_angle.addItems(["0", "90", "180", "270"])
        self.listWidget.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        #
        self.comboBox_layer.currentIndexChanged.connect(self.signal_mirror)
        self.lineEdit_font_height.setText('42')
        self.lineEdit_font_width.setText('40')
        self.lineEdit_line_width.setText('5.5')
        #
        self.lineEdit_font_height.setValidator(QtGui.QDoubleValidator(self.lineEdit_font_height))
        self.lineEdit_font_width.setValidator(QtGui.QDoubleValidator(self.lineEdit_font_width))
        self.lineEdit_line_width.setValidator(QtGui.QDoubleValidator(self.lineEdit_line_width))
        self.pushButton_select_all.clicked.connect(lambda: self.listWidget.selectAll())
        self.pushButton_reset.clicked.connect(lambda: self.listWidget.clearSelection())
        self.pushButton_exec.clicked.connect(self.run)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())
        self.setStyleSheet(
            '''
            QListWidget::Item{height:24px;border-radius:1.5px;}QMessageBox{font-size:10pt;} QListWidget::Item:selected{background:#459B81;color:white;}
            QPushButton{background-color:#459B81;color:white;} QPushButton:hover{background:#333;}''')
        self.move((app.desktop().width() - self.geometry().width()) / 2,
                  (app.desktop().height() - self.geometry().height()) / 2)

    def signal_mirror(self):
        layer = str(self.comboBox_layer.currentText())
        if layer == '':
            self.comboBox_mirror.setCurrentIndex(0)
        else:
            if layer.startswith('c1'):
                self.comboBox_mirror.setCurrentIndex(1)
            else:
                self.comboBox_mirror.setCurrentIndex(2)

    def run(self):
        list_items = self.listWidget.selectedItems()
        if not list_items:
            QtGui.QMessageBox.warning(None, u'警告', u'请选择d_coupon！')
            return
        layer = str(self.comboBox_layer.currentText())
        if not layer:
            QtGui.QMessageBox.warning(self, u'提示', u'添加层别不能为空')
            return
        font_height = str(self.lineEdit_font_height.text())
        if not font_height:
            QtGui.QMessageBox.warning(self, u'提示', u'字高不能为空')
            return
        font_width = str(self.lineEdit_font_width.text())
        if not font_width:
            QtGui.QMessageBox.warning(self, u'提示', u'字宽不能为空')
            return
        line_width = str(self.lineEdit_line_width.text())
        if not line_width:
            QtGui.QMessageBox.warning(self, u'提示', u'线宽不能为空')
            return
        # 序号类型
        number_type = str(self.comboBox_number_type.currentText())
        number_postion = unicode(self.comboBox_number_position.currentText().toUtf8(), 'utf-8')
        # if not number_postion:
        #     QtGui.QMessageBox.warning(self, u'提示', u'序号位置不能为空')
        #     return
        number_mirror = str(self.comboBox_mirror.currentText())
        if not number_mirror:
            QtGui.QMessageBox.warning(self, u'提示', u'是否镜像不能为空')
            return
        self.hide()
        angle = str(self.comboBox_angle.currentText())
        if number_postion == u"在前面":
            pnl_format = len(number_type.split("_")[0])
            set_format = len(number_type.split("_")[1])
        elif number_postion == u"在后面":
            pnl_format = len(number_type.split("_")[1])
            set_format = len(number_type.split("_")[0])
        else:
            pnl_format = 2
            set_format = 0
        font_height, font_width, line_width = float(font_height) * 25.4/1000, float(font_width)*25.4/1000, float(line_width)*0.0833
        coupons = [str(item.text()) for item in list_items]
        # print(coupons)
        # print(font_height, font_width, line_width, number_postion)
        #
        panel_step = gen.Step(job, 'panel')
        panel_step.initStep()
        panel_step.affect(layer)
        for coupon in coupons:
            panel_step.resetFilter()
            panel_step.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=%s' % coupon)
            panel_step.selectAll()
        panel_step.resetFilter()
        if panel_step.Selected_count():
                res = QtGui.QMessageBox.warning(self, 'tips',
                                                u"检测到{0}存在已添加的序号，是否删除，重新添加？".format(panel_step.name),
                                                QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
                if res == QtGui.QMessageBox.Yes:
                    panel_step.selectDelete()
        for coupon in coupons:
            self.editAddText(layer, font_width, font_height, line_width, angle,
                             pnl_format, set_format, number_type,
                             coupon, number_postion, number_mirror)
        panel_step.removeLayer("draw_set_profile")
        panel_step.removeLayer("draw_set_profile_tmp")
        panel_step.createLayer('draw_set_profile')
        all_steps = get_panelset_sr_step(job.name, panel_step.name)

        panel_step.COM("profile_to_rout,layer=draw_set_profile,width=10")
        for stepname in all_steps:
            step = gen.Step(job, stepname)
            step.initStep()
            step.COM("profile_to_rout,layer=draw_set_profile,width=10")
        panel_step.initStep()
        panel_step.Flatten("draw_set_profile", "draw_set_profile_tmp")
        panel_step.clearAll()
        panel_step.affect("draw_set_profile_tmp")
        panel_step.COM("arc2lines,arc_line_tol=10")
        xmin, ymin, xmax, ymax = panel_step.profile2.xmin,panel_step.profile2.ymin,panel_step.profile2.xmax,panel_step.profile2.ymax
        layer_cmd = gen.Layer(panel_step, "draw_set_profile_tmp")
        feat_out = layer_cmd.featOut(units="mm")["lines"]
        x_resize = 700 / (xmax - xmin)
        y_resize = 700 / (ymax - ymin)

        xmin = xmin - 5
        ymax = ymax + 5

        arraylist_profile = [((obj.xs - xmin) * x_resize, (obj.ys - ymax) * y_resize,
                              (obj.xe - xmin) * x_resize, (obj.ye - ymax) * y_resize) for obj in feat_out]

        panel_step.Flatten(layer, layer + "_set_text")
        panel_step.clearAll()
        panel_step.affect(layer + "_set_text")
        for coupon in coupons:
            panel_step.resetFilter()
            panel_step.setAttrFilter(".string,text=%s" % coupon)
            panel_step.selectAll()
        panel_step.selectReverse()
        if panel_step.Selected_count():
            panel_step.selectDelete()

        panel_step.resetFilter()
        panel_step.refSelectFilter2(layer, mode="cover", types="text", polarity="positive")
        if panel_step.Selected_count():
            panel_step.selectDelete()

        if panel_step.name == "set":
            panel_step.removeLayer(layer + "_set_text_tmp")
            if number_postion == u"在后面":
                panel_step.resetFilter()
                panel_step.filter_set(feat_types='text', polarity='positive')
                panel_step.COM("filter_set,filter_name=popup,update_popup=no,feat_types=text,text=6")
                panel_step.selectAll()
                if panel_step.Selected_count():
                    panel_step.moveSel(layer + "_set_text_tmp")

            layer_cmd = gen.Layer(panel_step, layer + "_set_text")
            feat_out = layer_cmd.featout_dic_Index(units="mm")["text"]
            get_sr_area_flatten("surface_fill", stepname=panel_step.name, get_sr_step=True)
            arraylist_text_info = []
            for obj in feat_out:
                panel_step.clearAll()
                panel_step.affect(layer + "_set_text")
                panel_step.selectByIndex(layer + "_set_text", obj.feat_index)
                if panel_step.Selected_count():
                    panel_step.removeLayer("text_tmp")
                    panel_step.copySel("text_tmp")
                    panel_step.clearAll()
                    if panel_step.isLayer("surface_fill"):
                        panel_step.affect("surface_fill")
                        panel_step.resetFilter()
                        panel_step.refSelectFilter("text_tmp")
                        if panel_step.Selected_count():
                            sel_xmin, sel_ymin, sel_xmax, sel_ymax = get_layer_selected_limits(panel_step,
                                                                                               "surface_fill")
                            arraylist_text_info.append((obj.feat_index,
                                                        round(((sel_xmin + sel_xmax) * 0.5 - xmin) * x_resize,
                                                              0),
                                                        round(((sel_ymin + sel_ymax) * 0.5 - ymax) * y_resize,
                                                              0),))

            if not arraylist_text_info:
                arraylist_text_info = [(obj.feat_index, (obj.x - xmin) * x_resize, (obj.y - ymax) * y_resize)
                                       for obj in feat_out]

        else:
            STR = '-t step -e %s/%s -d REPEAT,units=mm' % (job.name, 'panel')
            gREPEAT_info = panel_step.DO_INFO(STR)
            gREPEATstep = gREPEAT_info['gREPEATstep']
            gREPEATxmax = gREPEAT_info['gREPEATxmax']
            gREPEATymax = gREPEAT_info['gREPEATymax']
            gREPEATxmin = gREPEAT_info['gREPEATxmin']
            gREPEATymin = gREPEAT_info['gREPEATymin']
            self.dic_rect = {}
            arraylist_text_info = []
            for i in xrange(len(gREPEATstep)):
                if gREPEATstep[i] in coupons:
                    xs = gREPEATxmin[i]
                    ys = gREPEATymin[i]
                    xe = gREPEATxmax[i]
                    ye = gREPEATymax[i]
                    panel_step.clearSel()
                    panel_step.setFilterTypes('text', 'positive')
                    panel_step.selectRectangle(xs, ys, xe, ye)
                    layer_cmd = gen.Layer(panel_step, layer + "_set_text")
                    feat_out = layer_cmd.featout_dic_Index(units="mm", options="feat_index+select")["text"]
                    indexes = [(obj.feat_index, obj.text.replace("'", "")) for obj in feat_out]
                    arraylist_text_info.append((tuple(indexes), round(((xs + xe) * 0.5 - xmin) * x_resize, 0),
                                                round(((ys + ye) * 0.5 - ymax) * y_resize, 0), gREPEATstep[i]))
        # 清空掉d-coupon加的序号66
        for coupon in coupons:
            edit = gen.Step(job, coupon)
            edit.initStep()
            edit.affect(layer)
            edit.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=%s' % coupon)
            edit.selectAll()
            edit.resetFilter()
            if edit.Selected_count():
                edit.selectDelete()
            edit.unaffectAll()
        panel_step.initStep()
        self.dic_order = {}
        set_ui = show_set_pnl_order(self, arraylist_profile=arraylist_profile,
                                    w_size=(xmax - xmin) * x_resize + 130,
                                    h_size=(ymax - ymin) * y_resize + 50,
                                    text_info=arraylist_text_info,
                                    title_name=u"请确认{0}序号".format(panel_step.name))
        set_ui.exec_()
       # {(('290120', '66'),): '1', (('293646', '66'),): '3', (('290116', '66'),): '7', (('290118', '66'),): '4', (('293645', '66'),): '5',
        # (('290119', '66'),): '2', (('293644', '66'),): '6', (('290117', '66'),): '8'}
        panel_step.affect(layer + "_set_text")
        for indexes, text in self.dic_order.items():
            panel_step.selectNone()
            if isinstance(indexes, str):
                # set序号
                panel_step.selectFeatureIndex(layer + "_set_text", indexes)
                if number_postion == u"在后面":
                    if set_format == 1:
                        if (re.match("\d+", text) and float(text) < 10) or \
                                re.match("[A-Z]", text):
                            panel_step.selectByIndex(layer + "_set_text", indexes)
                            if panel_step.isLayer(layer + "_set_text_tmp"):
                                if panel_step.Selected_count():
                                    panel_step.removeLayer("text_tmp")
                                    panel_step.moveSel("text_tmp")
                                    panel_step.clearAll()
                                    panel_step.resetFilter()
                                    panel_step.affect(layer + "_set_text_tmp")
                                    panel_step.refSelectFilter("text_tmp")
                                    if panel_step.Selected_count():
                                        panel_step.moveSel(layer + "_set_text")
                                    panel_step.clearAll()
                                    panel_step.affect(layer + "_set_text")
                                    panel_step.refSelectFilter("text_tmp")
                        else:
                            panel_step.selectByIndex(layer + "_set_text", indexes)
                    else:
                        panel_step.selectByIndex(layer + "_set_text", indexes)

            if isinstance(indexes, tuple):
                # panel序号
                find_indexes = []
                for index, sel_text in indexes:
                    # step.PAUSE(str([text, sel_text]))
                    # if pnl_format == 1 and number_postion == u"在前面":
                    #     if (re.match("\d+", text) and float(text) < 10) or \
                    #             re.match("[A-Z]", text):
                    #         if sel_text == "66":
                    #             panel_step.selectByIndex(layer + "_set_text", index)
                    #             if panel_step.Selected_count():
                    #                 panel_step.selectDelete()
                    #             continue
                    #     else:
                    #         if sel_text == "6":
                    #             panel_step.selectByIndex(layer + "_set_text", index)
                    #             if panel_step.Selected_count():
                    #                 panel_step.selectDelete()
                    #             continue

                    find_indexes.append(index)

                for index in find_indexes:
                    panel_step.selectByIndex(layer + "_set_text", index)

            if panel_step.Selected_count():

                # format_num = 0
                # if stepname == "set":
                #     if set_format > 1:
                #         format_num = set_format
                # else:
                #     if pnl_format > 1:
                #         format_num = pnl_format
                format_num = pnl_format
                if re.match("[A-Z]", str(text)):
                    add_text = str(text)
                else:
                    add_text = str(text).rjust(format_num, "0")
                panel_step.COM(
                    "sel_change_txt,text={0},x_size=-1,y_size=-1,w_factor=-1,polarity=no_change,mirror=no_change,fontname=".format(
                        add_text))

        panel_step.copySel(layer)
        panel_step.clearAll()
        panel_step.removeLayer("text_tmp")
        panel_step.removeLayer(layer + "_set_text")
        panel_step.removeLayer(layer + "_set_text_tmp")
        panel_step.removeLayer("surface_fill")
        panel_step.removeLayer("draw_set_profile")
        panel_step.removeLayer("draw_set_profile_tmp")
        QtGui.QMessageBox.information(self, 'tips', u"添加完成")
        sys.exit()

    def editAddText(self, layer, x_size, y_size, w_factor,
                    angle, pnl_format, set_format, order_type,
                    stepname, pnl_order_position, mirror):

        edit = gen.Step(job, stepname)
        edit.open()
        edit.clearAll()
        edit.display(layer)
        edit.COM("zoom_home")
        edit.COM("units,type=mm")
        edit.COM("negative_data,mode=dim")
        edit.resetFilter()
        edit.resetFilter()
        edit.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=%s' % stepname)
        edit.selectAll()
        edit.removeLayer(layer + "_exists_order")
        if edit.Selected_count():
            res = QtGui.QMessageBox.warning(self, u'提示', u"检测到{0}存在已添加的序号，是否删除，重新添加？".format(stepname), QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            if res == QtGui.QMessageBox.Yes:
                edit.selectDelete()
            else:
                edit.moveSel(layer + "_exists_order")
        edit.resetFilter()
        STR = u"请选择添加的位置"
        if sys.platform == "win32":
            edit.MOUSE('select a point to add Text')
        else:
            edit.MOUSE(STR.encode("utf8"))

        mouse_xy = edit.MOUSEANS
        mouse_x = float(mouse_xy.split()[0])
        mouse_y = float(mouse_xy.split()[1])
        edit.COM('cur_atr_reset')

        if order_type == "panel" and stepname != "set":
            if "set" in matrixInfo["gCOLstep_name"]:
                """存在set的情况"""
                if pnl_order_position == u"在前面":
                    edit.COM('cur_atr_set,attribute=.string,text=panel')
                else:
                    edit.COM('cur_atr_set,attribute=.string,text=set')
                edit.addText(mouse_x, mouse_y, '66' if pnl_format < 3 else "6" * pnl_format, x_size, y_size, w_factor,
                             polarity='positive', attributes='yes', fontname="simple")
                edit.COM('cur_atr_set,attribute=.string,text=set-dot')
                edit.addText(mouse_x + x_size * 2 if pnl_format < 3 else mouse_x + x_size * pnl_format, mouse_y, '-',
                             x_size, y_size, w_factor,
                             polarity='positive', attributes='yes', fontname="simple")
                if pnl_order_position == u"在前面":
                    edit.COM('cur_atr_set,attribute=.string,text=set')
                else:
                    edit.COM('cur_atr_set,attribute=.string,text=panel')
                edit.addText(mouse_x + x_size * 3 if pnl_format < 3 else mouse_x + x_size * (pnl_format + 1), mouse_y,
                             '66' if set_format < 3 else "6" * set_format, x_size, y_size, w_factor,
                             polarity='positive', attributes='yes', fontname="simple")
            else:
                """不存在set"""
                edit.COM('cur_atr_set,attribute=.string,text=panel')
                edit.addText(mouse_x, mouse_y, '66' if set_format < 3 else "6" * set_format, x_size, y_size, w_factor,
                             polarity='positive', attributes='yes', fontname="simple")
        else:
            if stepname == "set":
                edit.COM('cur_atr_set,attribute=.string,text=panel')
            else:
                edit.COM('cur_atr_set,attribute=.string,text=%s' % stepname)
            edit.addText(mouse_x, mouse_y, '66' if set_format < 3 else "6" * set_format, x_size, y_size, w_factor,
                         polarity='positive', attributes='yes', fontname="simple")

        if angle != 0:
            # edit.resetFilter()
            # edit.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=panel')
            # edit.selectAll()
            # edit.resetFilter()
            # edit.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=set-dot')
            # edit.selectAll()
            edit.resetFilter()
            edit.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=%s' % stepname)
            edit.selectAll()
            if edit.Selected_count():
                edit.COM("sel_transform,oper=rotate,x_anchor={0},y_anchor={1},angle={2},"
                         "x_scale=1,y_scale=1,x_offset=0,"
                         "y_offset=0,mode=anchor,duplicate=no".format(mouse_x, mouse_y, angle))

        if mirror == "yes":
            # edit.resetFilter()
            # edit.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=panel')
            # edit.selectAll()
            # edit.resetFilter()
            # edit.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=set-dot')
            # edit.selectAll()
            edit.resetFilter()
            edit.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=.string,text=%s' % stepname)
            edit.selectAll()
            if edit.Selected_count():
                xmin, ymin, xmax, ymax = get_layer_selected_limits(edit, layer)
                edit.COM("sel_transform,oper=mirror,x_anchor={0},y_anchor={1},angle=0,"
                         "x_scale=1,y_scale=1,x_offset=0,"
                         "y_offset=0,mode=anchor,duplicate=no".format((xmin + xmax) * 0.5, (ymin + ymax) * 0.5))

        edit.resetFilter()
        job.PAUSE('please check the Text....')
        edit.selectNone()
        edit.close()


class show_set_pnl_order(QtGui.QDialog):
    """"""

    def __init__(self, parent=None, *args, **kwargs):
        """Constructor"""
        super(show_set_pnl_order, self).__init__(parent)
        self.setObjectName("mainWindow")
        # self.setWindowFlags(QtCore.Qt.WindowMinMaxButtonsHint | QtCore.Qt.WindowStaysOnTopHint)
        self.width, self.height = kwargs["w_size"], kwargs["h_size"]
        self.resize(self.width, self.height)
        # self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

        self.dic_label = {}
        self.dic_ObjectName = {}
        self.dic_combox = {}
        self.parent = parent

        self.profile = kwargs["arraylist_profile"]
        self.arraylist_text_info = kwargs["text_info"]
        self.setMainUIstyle()
        self.setWindowTitle(kwargs["title_name"])
        self.set_ui_widget()
        self.move((app.desktop().width() - self.geometry().width()) / 2,
                  (app.desktop().height() - self.geometry().height()) / 2)
        self.setStyleSheet('QToolTip{color:black;}')

    def set_ui_widget(self):
        """设置控件"""
        # self.l2r_btn = QtGui.QRadioButton(self)
        # self.l2r_btn.setGeometry(QtCore.QRect(self.width - 130, 40, 80, 40))
        # self.l2r_btn.setText(u"从左到右")
        # self.l2r_btn.setChecked(True)
        #
        # self.u2d_btn = QtGui.QRadioButton(self)
        # self.u2d_btn.setGeometry(QtCore.QRect(self.width - 130, 90, 80, 40))
        # self.u2d_btn.setText(u"从上到下")

        # self.upper_calc_position_btn = QtGui.QCheckBox(u"坐上角开始算")
        # self.upper_calc_position_btn = QtGui.QCheckBox(self)
        # self.upper_calc_position_btn.setGeometry(QtCore.QRect(self.width - 130, 140, 140, 40))
        # self.upper_calc_position_btn.setText(u"左上角开始算")
        # self.upper_calc_position_btn.setChecked(True)
        #
        # # self.down_calc_position_btn = QtGui.QCheckBox(u"坐下角开始算")
        # self.down_calc_position_btn = QtGui.QCheckBox(self)
        # self.down_calc_position_btn.setGeometry(QtCore.QRect(self.width - 130, 190, 140, 40))
        # self.down_calc_position_btn.setText(u"左下角开始算")
        #
        # self.combine_row_btn = QtGui.QCheckBox(self)
        # self.combine_row_btn.setGeometry(QtCore.QRect(self.width - 130, 240, 120, 40))
        # self.combine_row_btn.setText(u"相邻两行合并")
        #
        # self.combine_col_btn = QtGui.QCheckBox(self)
        # self.combine_col_btn.setGeometry(QtCore.QRect(self.width - 130, 290, 120, 40))
        # self.combine_col_btn.setText(u"相邻两列合并")
        #
        # self.number_to_word_btn = QtGui.QCheckBox(self)
        # self.number_to_word_btn.setGeometry(QtCore.QRect(self.width - 130, 340, 120, 40))
        # self.number_to_word_btn.setText(u"转换成字母")
        #
        # self.back_to_transition_btn = QtGui.QCheckBox(self)
        # self.back_to_transition_btn.setGeometry(QtCore.QRect(self.width - 130, 380, 120, 40))
        # self.back_to_transition_btn.setText(u"回形路走法")

        self.conform_btn = QtGui.QPushButton(self)
        self.conform_btn.setGeometry(QtCore.QRect(self.width - 100, 440, 80, 40))
        self.conform_btn.setText(u"确认序号")

        # self.l2r_btn.clicked.connect(self.change_text_order)
        # self.u2d_btn.clicked.connect(self.change_text_order)
        # self.upper_calc_position_btn.clicked.connect(self.change_text_order)
        # self.down_calc_position_btn.clicked.connect(self.change_text_order)
        #
        # self.combine_row_btn.clicked.connect(self.change_text_order)
        # self.combine_col_btn.clicked.connect(self.change_text_order)
        # self.back_to_transition_btn.clicked.connect(self.change_text_order)
        self.conform_btn.clicked.connect(self.get_text_order)
        # self.number_to_word_btn.clicked.connect(self.change_number_to_word)

        # self.combine_row_btn.setEnabled(False)
        # self.combine_col_btn.setEnabled(False)
        dic_text_info = self.set_text_order("Y")
        # 判断是否有-1结尾的，如果有，则其他coupon从2开始
        d_coupons_01 = []
        for v in dic_text_info.values():
            if v[0][3].endswith('-1') or v[0][3].endswith('01'):
                d_coupons_01.append(v[0][3])
        print(d_coupons_01)
        print(dic_text_info)
        # self.dic_combox = {}
        self.check_index = []  # 需要检测序号是否正确的combobox
        start_num = 2 if d_coupons_01 else 1
        i = 2 if d_coupons_01 else 1
        end_num = len(self.arraylist_text_info) + 2 - len(d_coupons_01) if d_coupons_01 else len(self.arraylist_text_info) + 1
        for key in sorted(dic_text_info.keys(), key=lambda x: x * -1):
            for index, x, y, coupon_name in dic_text_info[key]:
                self.dic_combox[index] = QtGui.QComboBox(self)
                self.dic_combox[index].setGeometry(QtCore.QRect(x, y * -1, 50, 30))
                if coupon_name in d_coupons_01:
                    self.dic_combox[index].addItem(str(1))
                else:
                    for num in range(start_num, end_num):
                        self.dic_combox[index].addItem(str(num))
                    pos = self.dic_combox[index].findText(str(i), QtCore.Qt.MatchExactly)
                    self.dic_combox[index].setCurrentIndex(pos)
                    self.check_index.append(index)
                    i += 1
                self.dic_combox[index].setToolTip(coupon_name)


    def change_number_to_word(self):
        """数字转换成字母"""
        arraylist = "abcdefghijklmnopqrstuvwxyz"
        if len(self.dic_combox) > len(arraylist):
            # showMessageInfo(u"序号超过26个，不能进行字母转换")
            QtGui.QMessageBox.information(self, u"提示", u"序号超过26个，不能进行字母转换")
            self.sender().setChecked(False)
            return

        dic_zu_num_to_wor = {}
        dic_zu_wor_to_num = {}
        for i, word in enumerate(list(arraylist)):
            if i + 1 > len(self.dic_combox):
                break
            dic_zu_num_to_wor[str(i + 1)] = word.upper()
            dic_zu_wor_to_num[word.upper()] = str(i + 1)

        if self.number_to_word_btn.isChecked():
            self.l2r_btn.setEnabled(False)
            self.u2d_btn.setEnabled(False)
            self.combine_row_btn.setEnabled(False)
            self.combine_col_btn.setEnabled(False)
            for key, editor in self.dic_combox.iteritems():
                number = str(editor.currentText())
                editor.clear()
                for key in sorted(dic_zu_num_to_wor.keys(), key=lambda x: int(x)):
                    editor.addItem(dic_zu_num_to_wor[key].upper())

                pos = editor.findText(dic_zu_num_to_wor[number], QtCore.Qt.MatchExactly)
                editor.setCurrentIndex(pos)
        else:
            self.l2r_btn.setEnabled(True)
            self.u2d_btn.setEnabled(True)
            for key, editor in self.dic_combox.iteritems():
                word = str(editor.currentText())
                editor.clear()
                for value in sorted(dic_zu_wor_to_num.values(), key=lambda x: int(x)):
                    editor.addItem(value)

                pos = editor.findText(dic_zu_wor_to_num[word], QtCore.Qt.MatchExactly)
                editor.setCurrentIndex(pos)

    def change_text_order(self):
        if self.sender() == self.upper_calc_position_btn:
            self.down_calc_position_btn.setChecked(False)
        if self.sender() == self.down_calc_position_btn:
            self.upper_calc_position_btn.setChecked(False)

        if self.l2r_btn.isChecked():
            dic_text_info = self.set_text_order("Y")
            keys = sorted(dic_text_info.keys(), key=lambda x: x * -1)
            if self.down_calc_position_btn.isChecked():
                keys = sorted(dic_text_info.keys(), key=lambda x: x)
            self.combine_row_btn.setEnabled(True)
            self.combine_col_btn.setEnabled(False)
            self.combine_col_btn.setChecked(False)
            if self.combine_row_btn.isChecked():
                i = 0
                new_keys = []
                for key1, key2 in zip(keys, keys[1:]):
                    if i % 2:
                        i += 1
                        continue

                    i += 1
                    dic_text_info[key1] += dic_text_info[key2]
                    new_keys.append(key1)

                keys = sorted(new_keys, key=lambda x: x * -1)
                if self.down_calc_position_btn.isChecked():
                    keys = sorted(new_keys, key=lambda x: x)

            sort_index = 1
            flag = 1
        # elif self.u2d_btn.isChecked():
        #     dic_text_info = self.set_text_order("X")
        #     keys = sorted(dic_text_info.keys(), key=lambda x: x)
        #     self.combine_row_btn.setEnabled(False)
        #     self.combine_row_btn.setChecked(False)
        #     self.combine_col_btn.setEnabled(True)
        #     if self.combine_col_btn.isChecked():
        #         i = 0
        #         new_keys = []
        #         for key1, key2 in zip(keys, keys[1:]):
        #             if i % 2:
        #                 i += 1
        #                 continue
        #
        #             i += 1
        #             dic_text_info[key1] += dic_text_info[key2]
        #             new_keys.append(key1)
        #
        #         keys = sorted(new_keys, key=lambda x: x)
        #
        #     sort_index = 2
        #     flag = -1
        #     if self.down_calc_position_btn.isChecked():
        #         flag = 1
        else:
            return

        i = 1
        zu = 1
        for key in keys:
            if self.back_to_transition_btn.isChecked():
                if not zu % 2:
                    direction = -1
                else:
                    direction = 1
            else:
                direction = 1
            zu += 1
            for index, x, y in sorted(dic_text_info[key], key=lambda x: x[sort_index] * flag * direction):
                pos = self.dic_combox[index].findText(str(i), QtCore.Qt.MatchExactly)
                self.dic_combox[index].setCurrentIndex(pos)

                i += 1

    def get_text_order(self):
        index_list = []
        for key, editor in self.dic_combox.iteritems():
            index = str(self.dic_combox[key].currentText())
            self.parent.dic_order[key] = index
            if key in self.check_index:
                index_list.append(index)
        # 判断index是否正确
        uniques_nums = set()
        duplicates = []
        for index in index_list:
            if index in uniques_nums:
                if index not in duplicates:
                    duplicates.append(index)
            else:
                uniques_nums.add(index)
        if duplicates:
            QtGui.QMessageBox.warning(self, 'tips', u'序号%s重复，请重新选择！' % u'、'.join(duplicates))
        else:
            self.accept()


    def set_text_order(self, direct):
        # 按同一水平位置分组
        dic_zu = {}
        all_x = set([r[1] for r in self.arraylist_text_info])
        all_y = set([r[2] for r in self.arraylist_text_info])

        if direct == 'Y':
            for zu in all_y:
                dic_zu[zu] = []
                for index, x, y, coupon_name in self.arraylist_text_info:
                    if zu == y:
                        dic_zu[zu].append([index, x, y, coupon_name])
        else:
            for zu in all_x:
                dic_zu[zu] = []
                for index, x, y, coupon_name in self.arraylist_text_info:
                    if zu == x:
                        dic_zu[zu].append([index, x, y, coupon_name])

        return dic_zu

    def paintEvent(self, event):  # QPaintEvent *
        painter = QtGui.QPainter()
        painter.begin(self)
        painter.setPen(Qt.Qt.black)
        painter.scale(1, -1)
        for xs, ys, xe, ye in self.profile:
            painter.drawPolyline(QtCore.QPointF(xs, ys),
                                 QtCore.QPointF(xe, ye))

        painter.end()

    def setMainUIstyle(self):  # 设置风格
        file = QtCore.QFile(':/pic/fblue.qss')
        file.open(QtCore.QFile.ReadOnly)
        styleSheet = file.readAll()
        styleSheet = unicode(styleSheet, encoding='gb2312')
        QtGui.qApp.setStyleSheet(styleSheet)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    app.setStyle('Cleanlooks')
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    add_d_coupon_serial_number = AddDcouponSerialNumber()
    add_d_coupon_serial_number.show()
    sys.exit(app.exec_())
