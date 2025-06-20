#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:makeEntityDxf20240816_ezdxf0_16.py
   @author:zl
   @time:2022/10/12 09:53
   @software:PyCharm
   @desc:
"""
import datetime
import os
import sys
import time
import re

import ezdxf
import qtawesome
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from ezdxf import units

import makeEntityDxfUI as ui

sys.path.append('/genesis/sys/scripts/zl/lib')
import genClasses as gen
import ZL_mysqlCon as zlmysql

# sys.path.append('/genesis/sys/scripts/zl/python/images')
import res_rc


class MakeEntityDxf(QWidget, ui.Ui_Form):
    def __init__(self):
        super(MakeEntityDxf, self).__init__()
        self.setupUi(self)
        self.title.setText('Job:%s\t\tStep:%s' % (jobname, stepname))
        rows = job.matrix.returnRows()
        boardlays = job.matrix.returnRows('board')
        self.listWidget.addItems(rows)
        self.listWidget.setSelectionMode(QAbstractItemView.MultiSelection)
        for i in range(len(rows)):
            if self.listWidget.item(i).text() in boardlays:
                self.listWidget.item(i).setSelected(True)
        header = ["层名", "层文字", '层备注说明']
        self.tableWidget.setColumnCount(len(header))
        self.tableWidget.setHorizontalHeaderLabels(header)
        self.tableWidget.setColumnWidth(2, 224)
        # self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # self.tableWidget.setRowCount(len(boardlays))
        self.loadingTable()
        # for i in range(len(boardlays)):
        #     self.tableWidget.setItem(i, 0, QTableWidgetItem(boardlays[i]))
        #     self.tableWidget.setCellWidget(i, 1, QLineEdit())
        #     self.tableWidget.setCellWidget(i, 2, QTextEdit())
        # self.path = '/io_files/fpc/%s/' % user
        self.path = 'D:/tmp/%s/' % user
        self.path_input.setText(self.path)
        self.path_input.setEnabled(False)
        self.path_input.setStyleSheet('color:#000;')
        self.pushButton_3.setIcon(qtawesome.icon('fa.dot-circle-o', scale_factor=1, color='cyan'))
        self.pushButton_3.setCursor(QCursor(Qt.PointingHandCursor))
        self.pushButton.setIcon(qtawesome.icon('fa.upload', scale_factor=1, color='cyan'))
        self.pushButton.setCursor(QCursor(Qt.PointingHandCursor))
        self.pushButton_2.setIcon(qtawesome.icon('fa.arrow-circle-o-right', scale_factor=1, color='cyan'))
        self.pushButton_2.setCursor(QCursor(Qt.PointingHandCursor))
        self.setStyleSheet('QPushButton{background-color:#0081a6;color:white;} QPushButton:hover{background:black;}')
        self.listWidget.itemClicked.connect(self.loadingTable)
        # 重置
        self.pushButton_3.clicked.connect(self.reset)
        # 导出
        self.pushButton.clicked.connect(self.generateDxf)
        self.pushButton_2.clicked.connect(lambda: sys.exit())
        # self.move((app.desktop().width() - self.geometry().width()) / 2,
        #           (app.desktop().height() - self.geometry().height()) / 2)

    def __getattr__(self, item):
        if item == 'username':
            self.username = self.getNameByGenesisUser()
            return self.username
        if item == 'layermap':
            self.layermap = self.getLayerMap()
            return self.layermap

    def loadingTable(self):
        items = self.listWidget.selectedItems()
        self.tableWidget.setRowCount(0)
        self.tableWidget.clearContents()
        self.tableWidget.setRowCount(len(items))
        for i, item in enumerate(items):
            self.tableWidget.setItem(i, 0, QTableWidgetItem(item.text()))
            if re.match(r'in(\d+)$', item.text()):
                # 层文字
                layer_words = 'L%s面线路' % re.match(r'in(\d+)$', item.text()).group(1)
            else:
                if self.layermap.get(item.text()):
                    layer_words = self.layermap.get(item.text())
                else:
                    layer_words = item.text()
            self.tableWidget.setCellWidget(i, 1, QLineEdit(layer_words))
            self.tableWidget.setCellWidget(i, 2, QTextEdit())

    def reset(self):
        self.listWidget.clearSelection()
        self.tableWidget.setRowCount(0)
        self.tableWidget.clearContents()
        self.tableWidget.setColumnWidth(2, 268)

    def generateDxf(self):
        if not self.tableWidget.rowCount():
            QMessageBox.warning(None, 'warning', '请先选择层！')
            return
        if not os.path.exists(self.path):
            QMessageBox.warning(None, 'warning', '该路径不存在！')
            return
        # 取信息
        # for row in range(self.tableWidget.rowCount()):
        #     text = self.tableWidget.item(row, 0).text()
        #     text2 = self.tableWidget.cellWidget(row, 1).text()
        #     text3 = self.tableWidget.cellWidget(row, 2).toPlainText()
        #     print(text, text2, text3)
        cus_number = self.cus_number.text().strip()
        # 层导出dxf
        step = job.steps.get(stepname)
        layer_dxfpath = 'D:/tmp/zl/tmp/'
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        step.initStep()
        # 缩放大小   60 80 1:1
        scale = 11 / step.profile2.xsize
        # 外形
        prof_lay = 'myprof+++' + str(job.pid)
        step.prof_to_rout(prof_lay, 10)
        for row in range(self.tableWidget.rowCount()):
            lay = self.tableWidget.item(row, 0).text()
            tmp = lay + '+++' + str(job.pid)
            step.affect(lay)
            step.copySel(tmp)
            step.unaffectAll()
            step.affect(tmp)
            step.VOF()
            status = step.Contourize(accuracy=50.8)
            if status:
                step.Contourize()
            step.VON()
            step.unaffectAll()
            step.affect(prof_lay)
            step.copyToLayer(tmp)
            step.unaffectAll()
            step.DxfOut(tmp, layer_dxfpath, prefix=timestamp, surface_mode='fill',
                        x_offset=-step.profile2.xmin, y_offset=-step.profile2.ymin, draft='no')
            step.removeLayer(tmp)
        step.removeLayer(prof_lay)
        doc = ezdxf.new("R2004", setup=True)
        msp = doc.modelspace()
        block1 = doc.blocks.new("frame")
        doc.styles.new('宋体', dxfattribs={'font': 'simsun.ttc'})
        block1.add_line((181.3036, -26.2706), (273.4984, -26.2706), {'color': 4})
        block1.add_line((273.4984, -26.2706), (273.4984, 38.0087), {'color': 4})
        block1.add_line((273.4984, 38.0087), (181.3036, 37.8384), {'color': 4})
        block1.add_line((181.3036, 37.8384), (181.3036, -26.2706), {'color': 4})
        block1.add_lwpolyline(
            [(180.4175, -27.3362), (274.5537, -27.3362), (274.5537, 39.0763), (180.4175, 39.0763),
             (180.4175, -27.3362)],
            dxfattribs={'color': 4})
        # 下
        block1.add_line((192.2952, -26.2706), (192.2952, -27.3697), {'color': 4})
        block1.add_line((203.2867, -26.2706), (203.2867, -27.3697), {'color': 4})
        block1.add_line((214.2783, -26.2706), (214.2783, -27.3697), {'color': 4})
        block1.add_line((229.5322, -26.2706), (229.5322, -27.3697), {'color': 4})
        block1.add_line((240.5238, -26.2706), (240.5238, -27.3697), {'color': 4})
        block1.add_line((251.5153, -26.2706), (251.5153, -27.3697), {'color': 4})
        block1.add_line((262.5069, -26.2706), (262.5069, -27.3697), {'color': 4})
        block1.add_text('1', {'style': '宋体', 'height': 0.8793, 'color': 4}).set_pos((186.4850, -26.8202),
                                                                                    align="Middle")
        block1.add_text('2', {'style': '宋体', 'height': 0.8793, 'color': 4}).set_pos((197.4766, -26.8202),
                                                                                    align="Middle")
        block1.add_text('3', {'style': '宋体', 'height': 0.8793, 'color': 4}).set_pos((208.4681, -26.8202),
                                                                                    align="Middle")
        block1.add_text('4', {'style': '宋体', 'height': 0.8793, 'color': 4}).set_pos((222.2318, -26.8202),
                                                                                    align="Middle")
        block1.add_text('5', {'style': '宋体', 'height': 0.8793, 'color': 4}).set_pos((234.7136, -26.8202),
                                                                                    align="Middle")
        block1.add_text('6', {'style': '宋体', 'height': 0.8793, 'color': 4}).set_pos((245.7052, -26.8202),
                                                                                    align="Middle")
        block1.add_text('7', {'style': '宋体', 'height': 0.8793, 'color': 4}).set_pos((256.6967, -26.8202),
                                                                                    align="Middle")
        block1.add_text('8', {'style': '宋体', 'height': 0.8793, 'color': 4}).set_pos((267.6883, -26.8202),
                                                                                    align="Middle")
        # 上
        block1.add_line((192.2952, 37.9877), (192.2952, 39.057), {'color': 4})
        block1.add_line((203.2867, 37.9877), (203.2867, 39.057), {'color': 4})
        block1.add_line((214.2783, 37.9877), (214.2783, 39.057), {'color': 4})
        block1.add_line((229.5322, 37.9877), (229.5322, 39.057), {'color': 4})
        block1.add_line((251.5153, 37.9877), (251.5153, 39.057), {'color': 4})
        block1.add_line((262.5069, 37.9877), (262.5069, 39.057), {'color': 4})
        block1.add_text('1', {'style': '宋体', 'height': 0.8793, 'color': 4}).set_pos((186.4850, 38.5043), align="Middle")
        block1.add_text('2', {'style': '宋体', 'height': 0.8793, 'color': 4}).set_pos((197.4766, 38.5043), align="Middle")
        block1.add_text('3', {'style': '宋体', 'height': 0.8793, 'color': 4}).set_pos((208.4681, 38.5043), align="Middle")
        block1.add_text('4', {'style': '宋体', 'height': 0.8793, 'color': 4}).set_pos((222.2318, 38.5043), align="Middle")
        block1.add_text('5', {'style': '宋体', 'height': 0.8793, 'color': 4}).set_pos((234.7136, 38.5043), align="Middle")
        block1.add_text('6', {'style': '宋体', 'height': 0.8793, 'color': 4}).set_pos((245.7052, 38.5043), align="Middle")
        block1.add_text('7', {'style': '宋体', 'height': 0.8793, 'color': 4}).set_pos((256.6967, 38.5043), align="Middle")
        block1.add_text('8', {'style': '宋体', 'height': 0.8793, 'color': 4}).set_pos((267.6883, 38.5043), align="Middle")
        # 左
        block1.add_line((180.4175, 31.8334), (181.3036, 31.8334), {'color': 4})
        block1.add_line((180.4175, 25.4261), (181.3036, 25.4261), {'color': 4})
        block1.add_line((180.4175, 16.3882), (181.3036, 16.3882), {'color': 4})
        block1.add_line((180.4175, 6.9432), (181.3036, 6.9432), {'color': 4})
        block1.add_line((180.4175, -4.6314), (181.3036, -4.6314), {'color': 4})
        block1.add_line((180.4175, -15.6454), (181.3036, -15.6454), {'color': 4})
        block1.add_text('A', {'style': '宋体', 'height': 0.8793, 'color': 4}).set_pos((180.9135, 34.1678), align="Middle")
        block1.add_text('B', {'style': '宋体', 'height': 0.8793, 'color': 4}).set_pos((180.9135, 28.3864), align="Middle")
        block1.add_text('C', {'style': '宋体', 'height': 0.8793, 'color': 4}).set_pos((180.9135, 20.2578), align="Middle")
        block1.add_text('D', {'style': '宋体', 'height': 0.8793, 'color': 4}).set_pos((180.9135, 10.8593), align="Middle")
        block1.add_text('E', {'style': '宋体', 'height': 0.8793, 'color': 4}).set_pos((180.9135, 0.2478), align="Middle")
        block1.add_text('F', {'style': '宋体', 'height': 0.8793, 'color': 4}).set_pos((180.9135, -10.3672),
                                                                                    align="Middle")
        block1.add_text('G', {'style': '宋体', 'height': 0.8793, 'color': 4}).set_pos((180.9135, -20.3168),
                                                                                    align="Middle")
        # 右
        block1.add_line((273.5344, 31.8334), (274.5537, 31.8334), {'color': 4})
        block1.add_line((273.5344, 25.4261), (274.5537, 25.4261), {'color': 4})
        block1.add_line((273.5344, 16.3882), (274.5537, 16.3882), {'color': 4})
        block1.add_line((273.5344, 6.9432), (274.5537, 6.9432), {'color': 4})
        block1.add_line((273.5344, -4.6314), (274.5537, -4.6314), {'color': 4})
        block1.add_line((273.5344, -15.6454), (274.5537, -15.6454), {'color': 4})
        block1.add_text('A', {'style': '宋体', 'height': 0.8793, 'color': 4}).set_pos((274.0387, 34.1678), align="Middle")
        block1.add_text('B', {'style': '宋体', 'height': 0.8793, 'color': 4}).set_pos((274.0387, 28.3864), align="Middle")
        block1.add_text('C', {'style': '宋体', 'height': 0.8793, 'color': 4}).set_pos((274.0387, 20.2578), align="Middle")
        block1.add_text('D', {'style': '宋体', 'height': 0.8793, 'color': 4}).set_pos((274.0387, 10.8593), align="Middle")
        block1.add_text('E', {'style': '宋体', 'height': 0.8793, 'color': 4}).set_pos((274.0387, 0.2478), align="Middle")
        block1.add_text('F', {'style': '宋体', 'height': 0.8793, 'color': 4}).set_pos((274.0387, -10.3672),
                                                                                    align="Middle")
        block1.add_text('G', {'style': '宋体', 'height': 0.8793, 'color': 4}).set_pos((274.0387, -20.3168),
                                                                                    align="Middle")
        # 多行文字
        mtext = block1.add_mtext("""
            说明：
            1、成品厚度:FPC=0.10mm±0.03mm、RFPC=0.40±0.05mm、RFPC+油墨区=0.45±0.05mm、
            2、材料：覆盖膜:1/2milPI 1/2milAD,
            双面无胶高压延铜:1/3 oz CU  1 mil PI)
            3.表面处理：镍钯金（ENEPIG:Au≥0.05um，Pd≥0.05,5≤Ni≤9um)
            4.防焊：PSR黑色哑光油墨
            5.SMT回流焊后漏铜接地阻抗：<1Ω, .差分阻抗：90±10%Ω
            6.芯吸长度≤80um;钻孔粗糙度≤15um;软硬交接区溢胶量≤0.5mm;
            7.凹蚀深度:正凹蚀深度5-80um 负凹蚀深度≤12.5um
            """, {'style': '宋体', 'color': 3})
        mtext.dxf.char_height = 0.8105
        mtext.dxf.width = 41.6821
        # mtext.set_location(insert=(182.5080, -7.4038, 0), rotation=0, attachment_point=1)
        mtext.set_location(insert=(182.5080, -10, 0), rotation=0, attachment_point=1)
        # 右上角
        block1.add_line((252.6743, 37.9877), (252.6743, 32.9082), {'color': 4})
        block1.add_line((252.6743, 32.9082), (273.4984, 32.9082), {'color': 4})
        block1.add_line((263.0746, 32.9082), (263.0746, 37.9877), {'color': 4})
        mtext = block1.add_mtext('{\\fSimSun|b0|i0|c134|p2;HSF}', {'color': 4})
        mtext.dxf.char_height = 2.9638
        mtext.set_location((253.6488, 36.9030, 0), rotation=0, attachment_point=1)
        mtext = block1.add_mtext('{\\fSimSun|b0|i0|c134|p2;RoHS}', {'color': 4})
        mtext.dxf.char_height = 2.9638
        mtext.set_location((264.0631, 36.9030, 0), rotation=0, attachment_point=1)
        # block1.add_text('{\\fSimSun|b0|i0|c134|p2;RoHS}', {'height': 2.9638, 'color': 4}).set_pos((264.0631, 36.9030), align="TOP_LEFT")
        # 右下角表格
        block1.add_line((230.0462, -26.2762), (230.0462, -13.2427), {'color': 4})
        block1.add_line((230.0462, -13.2427), (273.4984, -13.2427), {'color': 4})
        block1.add_line((230.0462, -17.2702), (273.4984, -17.2702), {'color': 4})
        block1.add_line((230.0462, -20.4129), (273.4984, -20.4129), {'color': 4})
        block1.add_line((230.0462, -22.8616), (273.4984, -22.8616), {'color': 4})
        block1.add_line((258.5831, -26.2762), (258.5831, -22.8616), {'color': 4})
        block1.add_line((263.8014, -26.2762), (263.8014, -22.8616), {'color': 4})
        # 制表
        block1.add_line((236.3279, -22.8616), (236.3279, -17.2702), {'color': 4})
        posx = 232.1666
        if len(self.username) > 2:
            posx = 231.7365
        block1.add_text(self.username, {'style': '宋体', 'height': 0.6785, 'color': 4}).set_pos((posx, -21.4772),
                                                                                              align="TOP_LEFT")
        # ##  填充
        block1.add_text('制表', {'style': '宋体', 'height': 0.6785, 'color': 4}).set_pos((232.1666, -18.6371),
                                                                                     align="TOP_LEFT")
        # 审核
        block1.add_line((242.4088, -22.8616), (242.4088, -17.2702), {'color': 4})
        block1.add_text('审核', {'style': '宋体', 'height': 0.6785, 'color': 4}).set_pos((238.5348, -18.6371),
                                                                                     align="TOP_LEFT")
        block1.add_text('刘晖', {'style': '宋体', 'height': 0.6785, 'color': 4}).set_pos((238.4096, -21.4772),
                                                                                     align="TOP_LEFT")
        # 批准
        block1.add_line((248.3822, -22.8616), (248.3822, -17.2702), {'color': 4})
        block1.add_text('批准', {'style': '宋体', 'height': 0.6785, 'color': 4}).set_pos((244.3122, -18.6371),
                                                                                     align="TOP_LEFT")
        block1.add_text('陈盛新', {'style': '宋体', 'height': 0.6785, 'color': 4}).set_pos((243.7593, -21.4772),
                                                                                      align="TOP_LEFT")
        # FileName
        block1.add_line((260.8797, -22.8616), (260.8797, -17.2702), {'color': 4})
        block1.add_text('File name', {'style': '宋体', 'height': 0.6785, 'color': 4}).set_pos((252.6638, -18.6371),
                                                                                            align="TOP_LEFT")
        block1.add_text(jobname, {'style': '宋体', 'height': 0.6785, 'color': 4}).set_pos((249.8348, -21.4772),
                                                                                        align="TOP_LEFT")
        # date
        block1.add_line((266.8273, -22.8616), (266.8273, -17.2702), {'color': 4})
        block1.add_text('Date', {'style': '宋体', 'height': 0.6785, 'color': 4}).set_pos((263.0242, -18.6371),
                                                                                       align="TOP_LEFT")
        # Scale
        block1.add_text('Scale', {'style': '宋体', 'height': 0.6785, 'color': 4}).set_pos((269.2613, -18.6371),
                                                                                        align="TOP_LEFT")
        block1.add_line((267.8004, -21.5820), (267.9937, -21.5820), {'color': 4})
        block1.add_line((268.0868, -21.5820), (268.1798, -21.5820), {'color': 4})
        block1.add_line((268.3241, -21.5820), (268.5056, -21.5820), {'color': 4})
        block1.add_line((268.6406, -21.5820), (268.7849, -21.5820), {'color': 4})
        block1.add_line((268.9198, -21.5820), (269.1339, -21.5820), {'color': 4})
        block1.add_line((269.2363, -21.5820), (269.3759, -21.5820), {'color': 4})
        block1.add_line((269.4969, -21.5820), (269.6924, -21.5820), {'color': 4})
        block1.add_line((269.7286, -21.5820), (273.3558, -21.5820), {'color': 4})
        block1.add_circle((268.7466, -21.5601), 0.3699, {'color': 4})
        block1.add_circle((268.7466, -21.5601), 0.6627, {'color': 4})
        block1.add_line((268.7466, -20.8188), (268.7466, -20.6233), {'color': 4})
        block1.add_line((268.7466, -21.0794), (268.7466, -20.9398), {'color': 4})
        block1.add_line((268.7466, -21.3959), (268.7466, -21.1818), {'color': 4})
        block1.add_line((268.7466, -21.6751), (268.7466, -21.5308), {'color': 4})
        block1.add_line((268.7466, -21.9916), (268.7466, -21.81), {'color': 4})
        block1.add_line((268.7466, -22.2289), (268.7466, -22.1358), {'color': 4})
        block1.add_line((268.7466, -22.5153), (268.7466, -22.322), {'color': 4})
        #
        block1.add_line((270.7, -21.1747), (270.7, -21.9851), {'color': 4})
        block1.add_line((272.0860, -20.8708), (272.0860, -22.242), {'color': 4})
        block1.add_line((270.7, -21.1747), (272.0860, -20.8708), {'color': 4})
        block1.add_line((270.7, -21.9851), (272.0860, -22.242), {'color': 4})
        #
        block1.add_line((271.3933, -22.5265), (271.3933, -20.637), {'color': 4})
        #
        # 客户编号
        block1.add_text('客户编号：', {'style': '宋体', 'height': 0.8706, 'color': 4}).set_pos((230.8343, -24.3404),
                                                                                        align="TOP_LEFT")
        if cus_number:
            block1.add_text(cus_number, {'style': '宋体', 'height': 0.8706, 'color': 4}).set_pos((237, -24.3404),
                                                                                               align="TOP_LEFT")
        # 图纸名称
        block1.add_text('图纸名称：', {'style': '宋体', 'height': 0.6785, 'color': 4}).set_pos((259.167, -24.3404),
                                                                                        align="TOP_LEFT")
        block1.add_text('单件图', {'style': '宋体', 'height': 1.2724, 'color': 4}).set_pos((265.2669, -24.1882),
                                                                                  align="TOP_LEFT")
        msp.add_blockref('frame', (0, 0), {
            'xscale': 1,
            'yscale': 1,
            'zscale': 1
        })
        # logo
        # readfile = ezdxf.readfile('/genesis/sys/scripts/zl/python/images/logo.dxf')
        # logomsp = readfile.modelspace()
        # logo = doc.blocks.new('logo')
        # for entity in logomsp:
        #     logo.add_entity(entity.copy())
        # logo.units = units.MM
        # msp.add_blockref('logo', (240, -16.67), {
        #     'xscale': .8,
        #     'yscale': .8,
        #     # 'zscale': 0.3,
        #     'color': 3
        # })
        # 加公司文字  江西红板科技股份有限公司 Jiangxi Redboard Technology Co., Ltd.
        msp.add_text('江西红板科技股份有限公司', {'style': '宋体', 'height': 1}).set_pos((245.2536, -15.1102),
                                                                           align="LEFT")
        msp.add_text('Jiangxi Redboard Technology Co., Ltd.', {'style': '宋体', 'height': 1}).set_pos(
            (245.1233, -16.7272),
            align="LEFT")
        # doc.saveas(self.path + 'makeEntity%s.dxf' % timestamp)
        # 备注高度
        mark_h = 0
        for n in range(self.tableWidget.rowCount()):
            readfile = ezdxf.readfile(
                layer_dxfpath + timestamp + self.tableWidget.item(n, 0).text() + '+++' + str(job.pid) + '.dxf')
            dxfmsp = readfile.modelspace()
            block2 = doc.blocks.new(str(n))
            block2.units = units.MM
            for entity in dxfmsp:
                block2.add_entity(entity.copy())
            # 位置 34 - height
            posx = 183 + (n % 6) * 14
            # 备注文字的高度
            strip = self.tableWidget.cellWidget(n, 2).toPlainText().strip()
            if strip:
                mark_h = max(mark_h, (strip.count('\n') + 1) * 1)
            if n % 6 == 0:
                last_mark_h = mark_h
                mark_h = 0
            # 当换行排列时 往下移mark_h
            if n // 6:
                posy = 33 - (step.profile2.ysize * scale * (n // 6 + 1)) - 2.5 * (n // 6) - last_mark_h
            else:
                posy = 33 - (step.profile2.ysize * scale * (n // 6 + 1)) - 2.5 * (n // 6)
            msp.add_blockref(str(n), (posx, posy), {
                'xscale': scale,
                'yscale': scale,
                # 'zscale': 0.3,
                'color': 4
            })
            msp.add_text(self.tableWidget.cellWidget(n, 1).text(),
                         {'style': '宋体', 'height': 1, 'color': 3}).set_pos((posx + 2, posy - 1.8), align="LEFT")
            if self.tableWidget.cellWidget(n, 2).toPlainText().strip():
                mtext = msp.add_mtext(self.tableWidget.cellWidget(n, 2).toPlainText().strip(),
                                      {'style': '宋体', 'color': 3})
                mtext.dxf.char_height = 0.8572
                mtext.set_location(insert=(posx, posy - 2.5, 0), rotation=0, attachment_point=1)
            os.remove(layer_dxfpath + timestamp + self.tableWidget.item(n, 0).text() + '+++' + str(job.pid) + '.dxf')
        doc.saveas(self.path + '%s_makeEntity%s.dxf' % (jobname, timestamp))
        QMessageBox.information(None, 'info', '导出完成!')

    def getNameByGenesisUser(self):
        sql = 'select user_name from tab_user where user_genesis = %s'
        cursor.execute(sql, user)
        res = cursor.fetchone()
        username = ''
        if res:
            username = res[0]
        return username

    # 定义层名和名称映射
    def getLayerMap(self):
        hashmap = {
            'l1': '正面线路',
            f'l{job.SignalNum}': '反面线路',
            'gts': '正面阻焊开窗',
            'gbs': '反面阻焊开窗',
            'gto': '正面字符',
            'gbo': '反面字符',
        }
        return hashmap


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setStyleSheet('QMessageBox {font-size:12pt;}')
    app.setWindowIcon(QIcon(':/res/demo.png'))
    if not os.environ.get('JOB'):
        QMessageBox.warning(None, 'warning', '请打开料号！')
        sys.exit()
    if not os.environ.get('STEP'):
        QMessageBox.warning(None, 'warning', '请打开step！')
        sys.exit()
    jobname = os.environ.get('JOB')
    stepname = os.environ.get('STEP')
    job = gen.Job(jobname)
    user = job.getUser()
    db_connect = zlmysql.DBConnect()
    connection = db_connect.connection
    cursor = db_connect.cursor
    makeEntityDxf = MakeEntityDxf()
    makeEntityDxf.show()
    sys.exit(app.exec_())
