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
import math
import os
import sys
import re

import ezdxf
import qtawesome
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from ezdxf import units
from ezdxf.enums import TextEntityAlignment
from ezdxf.lldxf.const import MTEXT_TOP_LEFT

import makeEntityDxfUI as ui

sys.path.append('/genesis/sys/scripts/zl/lib')
import genClasses as gen

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
        self.tableWidget.setColumnWidth(0, 50)
        self.tableWidget.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tableWidget.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.tableWidget.verticalHeader().hide()
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.loadingTable()
        # 用户姓名
        self.usermap = {
            'zwc': '周文才',
            'gyl': '甘英连',
            'hjx': '黄景行',
            'hyl': '黄岳林',
            'why': '韦厚勇',
            'whm': '韦慧梅',
            'whh': '巫焕亨',
            '1': '测试号'
        }
        # 默认信息
        self.lineEdit_material.setText('CU 18um/ADH:13um/PI 12.5um(RA)')
        self.lineEdit_cov.setText('PI 12.5um/ADH 20um')
        self.lineEdit_character.setText('正反面白色字符')
        self.lineEdit_sup.setText('/')
        self.lineEdit_surface_treatment.setText('沉镍金 Ni:2-5um Au:0.03um-0.lum')
        self.lineEdit_acceptance_criteria.setText('IPC 6013 CLASS 2')
        self.lineEdit_rohs.setText('RoHS 2.0 REACH')
        # 公差
        self.lineEdit_general_tolerance_1.setText('丝印、补强对位公差:±0.30')
        self.lineEdit_general_tolerance_2.setText('孔径公差:士0.075')
        self.lineEdit_general_tolerance_3.setText('蚀刻公差:士20%')
        self.lineEdit_general_tolerance_4.setText('外形公差:士0.1')
        #
        # self.textEdit_other_require.setText('孔铜最小8UM，平均10UM,真空包装，尾数包加硬板保护，加防潮珠 。符合欧盟ROHS和REACH要求，并提供有效的检验报告。需要做盐雾测试及回流焊测试。')
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
        self.setStyleSheet('QPushButton{background-color:#0081a6;color:white;} QPushButton:hover{background:black;} QListWidget::Item{height:20px;} QListWidget::Item:selected{background: #0081a6;color:white;}')
        self.listWidget.itemClicked.connect(self.loadingTable)
        # 重置
        self.pushButton_3.clicked.connect(self.reset)
        # 导出
        self.pushButton.clicked.connect(self.generateDxf)
        self.pushButton_2.clicked.connect(lambda: sys.exit())

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
            lineEdit = QLineEdit(layer_words)
            lineEdit.setFont(QFont('黑体', 9))
            self.tableWidget.setCellWidget(i, 1, lineEdit)
            textEdit = QTextEdit()
            textEdit.setFont(QFont('黑体', 9))
            self.tableWidget.setCellWidget(i, 2, textEdit)

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
        material = self.lineEdit_material.text()
        cov_ = self.lineEdit_cov.text()
        character = self.lineEdit_character.text()
        sup = self.lineEdit_sup.text()
        treatment = self.lineEdit_surface_treatment.text()
        accept = self.lineEdit_acceptance_criteria.text()
        rohs = self.lineEdit_rohs.text()
        general_tolerance_1 = self.lineEdit_general_tolerance_1.text()
        general_tolerance_2 = self.lineEdit_general_tolerance_2.text()
        general_tolerance_3 = self.lineEdit_general_tolerance_3.text()
        general_tolerance_4 = self.lineEdit_general_tolerance_4.text()
        pn = self.lineEdit_signal_pn.text()
        other_require = self.textEdit_other_require.toPlainText()
        # 层导出dxf
        step = job.steps.get(stepname)
        layer_dxfpath = 'D:/tmp/zl/tmp/'
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        step.initStep()
        # 缩放大小   60 80 1:1
        scale = 20 / step.profile2.xsize
        # 外形
        prof_lay = 'myprof+++' + str(job.pid)
        step.prof_to_rout(prof_lay, 10)
        for row in range(self.tableWidget.rowCount()):
            lay = self.tableWidget.item(row, 0).text()
            tmp = lay + '+++' + str(job.pid)
            if lay == 'gko':
                self.makeDimensions(prof_lay)
            else:
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
            step.DxfOut(tmp, layer_dxfpath, prefix=timestamp, surface_mode='fill', x_offset=-step.profile2.xmin, y_offset=-step.profile2.ymin, draft='no')
            step.removeLayer(tmp)
        step.removeLayer(prof_lay)
        doc = ezdxf.new("R2004", setup=True, units=4)
        msp = doc.modelspace()
        block1 = doc.blocks.new("frame")
        doc.styles.new('宋体', dxfattribs={'font': 'simsun.ttc'})
        block1.add_line((110, -150), (270, -150), {'color': 0})
        block1.add_line((110, -150), (110, -40), {'color': 0})
        block1.add_line((110, -40), (270, -40), {'color': 0})
        block1.add_line((270, -40), (270, -150), {'color': 0})
        # 下
        # 下横
        block1.add_line((110, -147), (160, -147), {'color': 0})
        block1.add_line((110, -144), (160, -144), {'color': 0})
        block1.add_line((110, -141), (160, -141), {'color': 0})
        block1.add_line((110, -138), (160, -138), {'color': 0})
        block1.add_line((110, -135), (200, -135), {'color': 0})
        block1.add_line((110, -132), (160, -132), {'color': 0})
        block1.add_line((110, -129), (160, -129), {'color': 0})
        block1.add_line((110, -126), (200, -126), {'color': 0})
        # 未注公差
        block1.add_line((170, -132.75), (200, -132.75), {'color': 0})
        block1.add_line((170, -130.5), (200, -130.5), {'color': 0})
        block1.add_line((170, -128.25), (200, -128.25), {'color': 0})
        block1.add_line((170, -126), (200, -126), {'color': 0})
        # 下竖
        block1.add_line((200, -150), (200, -124), {'color': 0})
        block1.add_line((124, -150), (124, -126), {'color': 0})
        block1.add_line((160, -150), (160, -126), {'color': 0})
        block1.add_line((170, -150), (170, -126), {'color': 0})
        # 下lrc
        block1.add_line((200, -124), (270, -124), {'color': 0})
        block1.add_line((200, -144), (270, -144), {'color': 0})
        block1.add_line((200, -140), (230, -140), {'color': 0})
        block1.add_line((200, -137), (270, -137), {'color': 0})
        block1.add_line((200, -132.5), (270, -132.5), {'color': 0})
        # 第三视图法
        block1.add_line((230, -144), (230, -132.5), {'color': 0})
        block1.add_line((213, -150), (213, -137), {'color': 0})
        block1.add_line((221, -144), (221, -137), {'color': 0})
        block1.add_line((239, -144), (239, -132.5), {'color': 0})
        block1.add_line((248, -144), (248, -132.5), {'color': 0})
        block1.add_line((257, -150), (257, -124), {'color': 0})
        block1.add_line((257, -150), (257, -124), {'color': 0})
        block1.add_line((263, -150), (263, -132.5), {'color': 0})
        block1.add_line((259, -127), (259.3799, -127), {'color': 0})
        block1.add_line((260.2186, -127), (260.4016, -127), {'color': 0})
        block1.add_line((261.0373, -127), (261.3584, -127), {'color': 0})
        block1.add_line((261.5972, -127), (261.8524, -127), {'color': 0})
        block1.add_line((262.0913, -127), (262.4701, -127), {'color': 0})
        block1.add_line((262.6512, -127), (262.8982, -127), {'color': 0})
        block1.add_line((263.1123, -127), (263.4581, -127), {'color': 0})
        block1.add_line((263.5221, -127), (267.8684, -127), {'color': 0})
        block1.add_circle((261.7848, -127.0141), .6545, {'color': 0})
        block1.add_circle((261.7848, -127.0141), 1.1725, {'color': 0})
        block1.add_line((261.7581, -125.3937), (261.7581, -125.7356), {'color': 0})
        block1.add_line((261.754, -126.1637), (261.754, -126.4107), {'color': 0})
        block1.add_line((261.754, -126.7236), (261.754, -127.1024), {'color': 0})
        block1.add_line((261.754, -127.2176), (261.754, -127.4728), {'color': 0})
        block1.add_line((261.754, -127.7775), (261.754, -128.0986), {'color': 0})
        block1.add_line((261.754, -128.1974), (261.754, -128.3621), {'color': 0})
        block1.add_line((261.754, -128.704), (261.754, -129.0459), {'color': 0})
        # 梯形
        block1.add_line((266.698, -125.7349), (266.698, -128.1607), {'color': 0})
        block1.add_line((264.2467, -126.2726), (264.2467, -127.7064), {'color': 0})
        block1.add_line((264.2467, -126.2726), (266.698, -125.7349), {'color': 0})
        block1.add_line((264.2467, -127.7064), (266.698, -128.1607), {'color': 0})
        block1.add_text('第三视图法', dxfattribs={'style': '宋体', 'height': 0.7, 'color': 0}).set_placement((261, -130),align=TextEntityAlignment.MIDDLE_LEFT)
        # 右上角
        block1.add_line((221, -42.24), (270, -42.24), {'color': 0})
        block1.add_line((221, -44.48), (270, -44.48), {'color': 0})
        block1.add_line((221, -40), (221, -44.48), {'color': 0})
        block1.add_line((229, -40), (229, -44.48), {'color': 0})
        block1.add_line((259, -40), (259, -44.48), {'color': 0})
        # 文字
        block1.add_text('结构：', dxfattribs={'style': '宋体', 'height': 0.7, 'color': 0}).set_placement((112, -127.8245),align=TextEntityAlignment.MIDDLE_LEFT)
        block1.add_text('基材：', dxfattribs={'style': '宋体', 'height': 0.7, 'color': 0}).set_placement((112, -130.8245),align=TextEntityAlignment.MIDDLE_LEFT)
        block1.add_text('正反面覆盖膜：', dxfattribs={'style': '宋体', 'height': 0.7, 'color': 0}).set_placement((112, -133.8245),align=TextEntityAlignment.MIDDLE_LEFT)
        block1.add_text('字符：', dxfattribs={'style': '宋体', 'height': 0.7, 'color': 0}).set_placement((112, -136.8245),align=TextEntityAlignment.MIDDLE_LEFT)
        block1.add_text('辅料：', dxfattribs={'style': '宋体', 'height': 0.7, 'color': 0}).set_placement((112, -139.8245),align=TextEntityAlignment.MIDDLE_LEFT)
        block1.add_text('表面处理：', dxfattribs={'style': '宋体', 'height': 0.7, 'color': 0}).set_placement((112, -142.8245),align=TextEntityAlignment.MIDDLE_LEFT)
        block1.add_text('验收标准：', dxfattribs={'style': '宋体', 'height': 0.7, 'color': 0}).set_placement((112, -145.8245),align=TextEntityAlignment.MIDDLE_LEFT)
        block1.add_text('环保标准：', dxfattribs={'style': '宋体', 'height': 0.73, 'color': 0}).set_placement((112, -148.8245),align=TextEntityAlignment.MIDDLE_LEFT)
        block1.add_text('未注公差：', dxfattribs={'style': '宋体', 'height': 0.7, 'color': 0}).set_placement((162.5766, -130.671),align=TextEntityAlignment.MIDDLE_LEFT)
        block1.add_text('其他要求：', dxfattribs={'style': '宋体', 'height': 0.7, 'color': 0}).set_placement((162.5766, -143),align=TextEntityAlignment.MIDDLE_LEFT)
        # info
        block1.add_text('广东则成科技有限公司', dxfattribs={'style': '宋体', 'height': 1.3, 'color': 6}).set_placement((202, -129), align=TextEntityAlignment.MIDDLE_LEFT)
        block1.add_text('单体图', dxfattribs={'style': '宋体', 'height': 1.8, 'color': 0}).set_placement((209, -135), align=TextEntityAlignment.MIDDLE_LEFT)
        block1.add_text('设计', dxfattribs={'style': '宋体', 'height': 0.7, 'color': 0}).set_placement((233, -135), align=TextEntityAlignment.MIDDLE_LEFT)
        block1.add_text('审核', dxfattribs={'style': '宋体', 'height': 0.7, 'color': 0}).set_placement((242, -135), align=TextEntityAlignment.MIDDLE_LEFT)
        block1.add_text('批准', dxfattribs={'style': '宋体', 'height': 0.7, 'color': 0}).set_placement((251, -135), align=TextEntityAlignment.MIDDLE_LEFT)
        block1.add_text('比例', dxfattribs={'style': '宋体', 'height': 0.7, 'color': 0}).set_placement((259, -135), align=TextEntityAlignment.MIDDLE_LEFT)
        block1.add_text('1:1', dxfattribs={'style': '宋体', 'height': 0.7, 'color': 0}).set_placement((265, -135), align=TextEntityAlignment.MIDDLE_LEFT)
        block1.add_text('文件名', dxfattribs={'style': '宋体', 'height': 0.8, 'color': 0}).set_placement((206, -139), align=TextEntityAlignment.MIDDLE)
        block1.add_text('版 本', dxfattribs={'style': '宋体', 'height': 0.8, 'color': 0}).set_placement((217, -139), align=TextEntityAlignment.MIDDLE)
        block1.add_text('日期', dxfattribs={'style': '宋体', 'height': 0.8, 'color': 0}).set_placement((225, -139), align=TextEntityAlignment.MIDDLE)
        # 右上角
        date_ = datetime.datetime.now().strftime('%Y.%m.%d')
        block1.add_text('版次', dxfattribs={'style': '宋体', 'height': 0.8, 'color': 0}).set_placement((225, -41), align=TextEntityAlignment.MIDDLE)
        block1.add_text('变更内容', dxfattribs={'style': '宋体', 'height': 0.8, 'color': 0}).set_placement((244, -41), align=TextEntityAlignment.MIDDLE)
        block1.add_text('日期', dxfattribs={'style': '宋体', 'height': 0.8, 'color': 0}).set_placement((264, -41), align=TextEntityAlignment.MIDDLE)
        block1.add_text('1.0', dxfattribs={'style': '宋体', 'height': 0.8, 'color': 0}).set_placement((225, -43.5), align=TextEntityAlignment.MIDDLE)
        block1.add_text('首次打样', dxfattribs={'style': '宋体', 'height': 0.8, 'color': 0}).set_placement((244, -43.5), align=TextEntityAlignment.MIDDLE)
        block1.add_text(f'{date_}', dxfattribs={'style': '宋体', 'height': 0.8, 'color': 0}).set_placement((264, -43.5), align=TextEntityAlignment.MIDDLE)
        #
        if '-' in jobname:
            block1.add_text(f'{jobname.rsplit("-")[0]}', dxfattribs={'style': '宋体', 'height': 0.8, 'color': 0}).set_placement((206, -143), align=TextEntityAlignment.MIDDLE)
            block1.add_text(f'{jobname.rsplit("-")[1]}', dxfattribs={'style': '宋体', 'height': 0.8, 'color': 0}).set_placement((217, -143), align=TextEntityAlignment.MIDDLE)
        block1.add_text(f'{date_}', dxfattribs={'style': '宋体', 'height': 0.8, 'color': 0}).set_placement((225, -143), align=TextEntityAlignment.MIDDLE)
        # user
        check_user = '甘英莲'  # 审核
        approve_user = '黄亦安'
        block1.add_text(f'{self.username}', dxfattribs={'style': '宋体', 'height': 0.8, 'color': 0}).set_placement((234.5, -141), align=TextEntityAlignment.MIDDLE)
        block1.add_text(f'{check_user}', dxfattribs={'style': '宋体', 'height': 0.8, 'color': 0}).set_placement((243.5, -141), align=TextEntityAlignment.MIDDLE)
        block1.add_text(f'{approve_user}', dxfattribs={'style': '宋体', 'height': 0.8, 'color': 0}).set_placement((252.5, -141), align=TextEntityAlignment.MIDDLE)
        block1.add_text('单位', dxfattribs={'style': '宋体', 'height': 0.8, 'color': 0}).set_placement((260, -141), align=TextEntityAlignment.MIDDLE)
        block1.add_text('mm', dxfattribs={'style': '宋体', 'height': 0.8, 'color': 0}).set_placement((266, -141), align=TextEntityAlignment.MIDDLE)
        block1.add_text('线路PN:', dxfattribs={'style': '宋体', 'height': 0.8, 'color': 0}).set_placement((206, -147), align=TextEntityAlignment.MIDDLE)
        block1.add_text(f'{pn}', dxfattribs={'style': '宋体', 'height': 1.0488, 'color': 1}).set_placement((215, -147), align=TextEntityAlignment.MIDDLE_LEFT)
        block1.add_text(f'No.', dxfattribs={'style': '宋体', 'height': .7, 'color': 0}).set_placement((260, -147), align=TextEntityAlignment.MIDDLE)
        block1.add_text(f'1 OF 2', dxfattribs={'style': '宋体', 'height': .7, 'color': 0}).set_placement((266, -147), align=TextEntityAlignment.MIDDLE)
        # 多行文字
        if job.SignalNum == 1:
            signal_name = '单面'
        elif job.SignalNum == 2:
            signal_name = '双面'
        else:
            signal_name = f'{job.SignalNum}层'
        __type = jobname[:2]
        if __type == 'fp':
            type_name = '软板'
        elif __type == 'rf':
            type_name = '软硬结合板'
        elif __type == 'pc':
            type_name = '硬板'
        else:
            type_name = '其他'
        mtext = block1.add_mtext(f'{signal_name + type_name}', dxfattribs={'style': '宋体', 'color': 0}).set_location((126.4, -127))
        mtext.dxf.char_height = 0.7
        mtext.dxf.attachment_point = MTEXT_TOP_LEFT
        # text = '''CU 18um/ADH:13um/PI 12.5um(RA)'''
        mtext = block1.add_mtext(material, dxfattribs={'style': '宋体', 'color': 1}).set_location((126.4, -130))
        mtext.dxf.char_height = 0.7
        mtext.dxf.attachment_point = MTEXT_TOP_LEFT
        # text = '''PI 12.5um/ADH 20um'''
        mtext = block1.add_mtext(cov_, dxfattribs={'style': '宋体', 'color': 1}).set_location((126.4, -133))
        mtext.dxf.char_height = 0.7
        mtext.dxf.attachment_point = MTEXT_TOP_LEFT
        # text = '''正反面白色字符'''
        mtext = block1.add_mtext(character, dxfattribs={'style': '宋体', 'color': 0}).set_location((126.4, -136))
        mtext.dxf.char_height = 0.7
        mtext.dxf.attachment_point = MTEXT_TOP_LEFT
        # text = '''/'''
        mtext = block1.add_mtext(sup, dxfattribs={'style': '宋体', 'color': 0}).set_location((126.4, -139))
        mtext.dxf.char_height = 0.7
        mtext.dxf.attachment_point = MTEXT_TOP_LEFT
        # text = '''沉镍金 Ni:2-5um Au:0.03um-0.lum'''
        mtext = block1.add_mtext(treatment, dxfattribs={'style': '宋体', 'color': 0}).set_location((126.4, -142))
        mtext.dxf.char_height = 0.7
        mtext.dxf.attachment_point = MTEXT_TOP_LEFT
        # text = '''IPC 6013 CLASS 2'''
        mtext = block1.add_mtext(accept, dxfattribs={'style': '宋体', 'color': 0}).set_location((126.4, -145))
        mtext.dxf.char_height = 0.7
        mtext.dxf.attachment_point = MTEXT_TOP_LEFT
        # text = '''RoHS 2.0 REACH'''
        mtext = block1.add_mtext(rohs, dxfattribs={'style': '宋体', 'color': 3}).set_location((126.4, -148))
        mtext.dxf.char_height = 0.7
        mtext.dxf.attachment_point = MTEXT_TOP_LEFT
        # text = '''丝印、补强对位公差:±0.30'''
        mtext = block1.add_mtext(general_tolerance_1, dxfattribs={'style': '宋体', 'color': 0}).set_location((171, -127))
        mtext.dxf.char_height = 0.7
        mtext.dxf.attachment_point = MTEXT_TOP_LEFT
        # text = '''孔径公差:士0.075'''
        mtext = block1.add_mtext(general_tolerance_2, dxfattribs={'style': '宋体', 'color': 0}).set_location((171, -129.25))
        mtext.dxf.char_height = 0.7
        mtext.dxf.attachment_point = MTEXT_TOP_LEFT
        # text = '''蚀刻公差:士20%'''
        mtext = block1.add_mtext(general_tolerance_3, dxfattribs={'style': '宋体', 'color': 0}).set_location((171, -131.5))
        mtext.dxf.char_height = 0.7
        mtext.dxf.attachment_point = MTEXT_TOP_LEFT
        # text = '''未标注公差:士0.1'''
        mtext = block1.add_mtext(general_tolerance_4, dxfattribs={'style': '宋体', 'color': 0}).set_location((171, -133.75))
        mtext.dxf.char_height = 0.7
        mtext.dxf.attachment_point = MTEXT_TOP_LEFT
        # text = '''孔铜最小8UM，平均10UM,真空包装，尾数包加硬板保护，加防潮珠 。符合欧盟ROHS和REACH要求，并提供有效的检验报告。需要做盐雾测试及回流焊测试。'''
        mtext = block1.add_mtext(other_require, dxfattribs={'style': '宋体', 'color': 0}).set_location((171, -137))
        mtext.dxf.char_height = 0.7
        mtext.dxf.width = 13.6
        mtext.dxf.attachment_point = MTEXT_TOP_LEFT
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
        # 备注高度
        mark_h = 4
        for n in range(self.tableWidget.rowCount()):
            readfile = ezdxf.readfile(
                layer_dxfpath + timestamp + self.tableWidget.item(n, 0).text() + '+++' + str(job.pid) + '.dxf')
            dxfmsp = readfile.modelspace()
            block2 = doc.blocks.new(str(n))
            block2.units = units.MM
            for entity in dxfmsp:
                block2.add_entity(entity.copy())
            # 位置 -57 - height
            posx = 122 + (n % 4) * 24
            # 备注文字的高度
            strip = self.tableWidget.cellWidget(n, 2).toPlainText().strip()
            if strip:
                mark_h = max(mark_h, (strip.count('\n') + 1) * 2)
            if n % 4 == 0:
                last_mark_h = mark_h
                mark_h = 4
            # 当换行排列时 往下移mark_h
            if n // 4:
                posy = -50 - (step.profile2.ysize * scale * (n // 4 + 1)) - 5 * (n // 4) - last_mark_h
            else:
                posy = -50 - (step.profile2.ysize * scale * (n // 4 + 1)) - 5 * (n // 4)
            msp.add_blockref(str(n), (posx, posy), {
                'xscale': scale,
                'yscale': scale,
                # 'zscale': 0.3,
                'color': 4
            })
            msp.add_text(self.tableWidget.cellWidget(n, 1).text(),
                         dxfattribs={'style': '宋体', 'height': 2.4, 'color': 0}).set_placement((posx + 10, posy - 3.5), align=TextEntityAlignment.MIDDLE_CENTER)
            if self.tableWidget.cellWidget(n, 2).toPlainText().strip():
                mtext = msp.add_mtext(self.tableWidget.cellWidget(n, 2).toPlainText().strip(),
                                      {'style': '宋体', 'color': 0})
                mtext.dxf.char_height = 1
                mtext.set_location(insert=(posx, posy - 2.5, 0), rotation=0, attachment_point=1)
            os.remove(layer_dxfpath + timestamp + self.tableWidget.item(n, 0).text() + '+++' + str(job.pid) + '.dxf')
        doc.saveas(self.path + '%s_makeEntity%s.dxf' % (jobname, timestamp))
        QMessageBox.information(None, 'tips', '导出完成!')

    def getNameByGenesisUser(self):
        username = ''
        if self.usermap.get(user):
            username = self.usermap.get(user)
        return username

    # 定义层名和名称映射
    def getLayerMap(self):
        hashmap = {
            'gtl': '正面线路',
            'l1': '正面线路',
            f'l{job.SignalNum}': '反面线路',
            'gbl': '反面线路',
            'gts': '正面阻焊开窗',
            'gbs': '反面阻焊开窗',
            'gto': '正面字符',
            'gbo': '反面字符',
            'f1': '基材钻孔',
            'gko': '外形',
            'c1': '正面覆盖膜开窗',
            'c2': '反面覆盖膜开窗',
            'dkt': '正面选镀',
            'dkb': '反面选镀'
        }
        return hashmap

    def makeDimensions(self, lay):
        step = job.steps.get(stepname)
        step.initStep()
        # 获取层中心 参考与中心的相对位置来设置标注点的位置
        infoDict = step.DO_INFO(' -t layer -e %s/%s/%s -d LIMITS,units=mm' % (jobname, step.name, lay))
        xmin = infoDict['gLIMITSxmin']
        ymin = infoDict['gLIMITSymin']
        xmax = infoDict['gLIMITSxmax']
        ymax = infoDict['gLIMITSymax']
        cx = (xmin + xmax) / 2
        cy = (ymin + ymax) / 2
        features = step.INFO(' -t layer -e %s/%s/%s -d FEATURES,units=mm' % (jobname, step.name, lay))
        del features[0]
        lines = {'h': [], 'v': []}
        cirs = {}
        for feature in features:
            type_ = feature.split()[0]
            if type_ == '#L':
                (x1, y1, x2, y2) = [float(i) for i in feature.split()[1: 5]]
                if x1 == x2:
                    leng = round(abs(y1 - y2), 2)
                    lines['v'].append((x1, min(y1, y2), x2, max(y1, y2), leng))
                if y1 == y2:
                    leng = round(abs(x1 - x2), 2)
                    lines['h'].append((min(x1, x2), y1, max(x1, x2), y2, leng))
            elif type_ == '#A':
                (x1, y1, x2, y2, xc, yc) = [float(i) for i in feature.split()[1: 7]]
                if x1 == x2 and y1 == y2:  # 起点终点相同，则为circle
                    # 半径
                    r = float('%.2f' % math.sqrt(abs(x1 - xc) ** 2 + abs(y1 - yc) ** 2))
                    if not cirs.get(r):
                        cirs[r] = []
                    cirs[r].append((xc, yc))
        # 排序
        if lines.get('h'):
            lines.get('h').sort(key=lambda x: (x[1], x[0]))
        if lines.get('v'):
            lines.get('v').sort(key=lambda x: (x[0], x[1]))
        # 处理断线
        newinfo = []
        if lines.get('h'):
            tmp_coors = lines['h']
            i = 0
            while i < len(tmp_coors):
                xs, ys, xe, ye, len_1 = tmp_coors[i][0], tmp_coors[i][1], tmp_coors[i][2], tmp_coors[i][3], tmp_coors[i][4]
                # 找出同一条直线上的
                while True:
                    if i == len(tmp_coors) - 1 and len_1 > 8:
                        newinfo.append([xs, ys, tmp_coors[i][2], tmp_coors[i][3], len_1])
                        break
                    if i == len(tmp_coors) - 1:
                        break
                    xs_2, ys_2, xe_2, ye_2, len_2 = tmp_coors[i + 1][0], tmp_coors[i + 1][1], tmp_coors[i + 1][2], tmp_coors[i + 1][3], tmp_coors[i + 1][4]
                    if ye != ys_2 or xe != xs_2:
                        if len_1 > 8:
                            newinfo.append([xs, ys, tmp_coors[i][2], tmp_coors[i][3], len_1])
                        break
                    len_1 += len_2
                    i += 1
                i += 1
            lines['h'] = newinfo
        newinfo = []
        if lines.get('v'):
            tmp_coors = lines['v']
            i = 0
            while i < len(tmp_coors):
                xs, ys, xe, ye, len_1 = tmp_coors[i][0], tmp_coors[i][1], tmp_coors[i][2], tmp_coors[i][3], tmp_coors[i][4]
                # 找出同一条直线上的
                while True:
                    if i == len(tmp_coors) - 1 and len_1 > 8:
                        newinfo.append([xs, ys, tmp_coors[i][2], tmp_coors[i][3], len_1])
                        break
                    if i == len(tmp_coors) - 1:
                        break
                    xs_2, ys_2, xe_2, ye_2, len_2 = tmp_coors[i + 1][0], tmp_coors[i + 1][1], tmp_coors[i + 1][2], \
                    tmp_coors[i + 1][3], tmp_coors[i + 1][4]
                    if xe != xs_2 or ye != ys_2:
                        if len_1 > 8:
                            newinfo.append([xs, ys, tmp_coors[i][2], tmp_coors[i][3], len_1])
                        break
                    len_1 += len_2
                    i += 1
                i += 1
            lines['v'] = newinfo
        lay = 'gko'
        step.display(lay)
        step.COM(f'dimens_delete_drawing,lyr_name={lay}')
        step.COM(
            f'dimens_set_params,lyr_name={lay},post_decimal_dist=-1,post_decimal_pos=-1,post_decimal_angle=-1,line_width=0.2,font=standard,text_width=2,text_height=2,top_margin=19.05,bottom_margin=12.7,left_margin=19.05,right_margin=12.7,ext_overlen=1016,center_marker_len=1270,baseline_spacing=304.8,feature_color=0,dimens_color=0,dimens_text_color=0,profile_color=0,template_color=0,paren_loc_text=yes')
        st = sl = 1.5
        if lines.get('h'):
            for line in lines['h']:
                x1, y1, x2, y2, value = line[0], line[1], line[2], line[3], line[4]
                line_y = y1 + st if y1 > cy else y1 - st
                step.COM(
                    f'dimens_add,type=horiz,x1={x1},y1={y1},x2={x2},y2={y2},x3=0,y3=0,line_x={(x1 + x2) / 2},line_y={line_y},offset=0.01,prefix=,value={value},tol_up=,tol_down=,suffix=,note=,units=mm,view_units=yes,underline=no,merge_tol=no,to_arc_center=no,two_sided_diam=no,magnify=1,vert_dimens_text_orientation=left')
        if lines.get('v'):
            for line in lines['v']:
                x1, y1, x2, y2, value = line[0], line[1], line[2], line[3], line[4]
                line_x = x1 + sl if x1 > cx else x1 - sl
                step.COM(
                    f'dimens_add,type=vert,x1={x1},y1={y1},x2={x2},y2={y2},x3=0,y3=0,line_x={line_x},line_y={(y1 + y2) / 2},offset=0.02,prefix=,value={value},tol_up=,tol_down=,suffix=,note=,units=mm,view_units=yes,underline=no,merge_tol=no,to_arc_center=no,two_sided_diam=no,magnify=1,vert_dimens_text_orientation=right')
        # circle
        for r, coor in cirs.items():
            xc, yc = coor[-1][0], coor[-1][1]
            prefix = f'{len(coor)}*' if len(coor) > 1 else ''
            if xc >= cx:
                x1, y1 = xc + r, yc
                x2, y2 = xmax + 5, yc
            else:
                x1, y1 = xc - r, yc
                x2, y2 = xmin - 5, yc
            step.COM(
                f'dimens_add,type=diameter,x1={x1},y1={y1},x2={x2},y2={y2},x3={x2},y3={y2},line_x=8.15086,line_y=0.70104,offset=0.02,prefix={prefix},value={2 * r},tol_up=,tol_down=,suffix=,note=,units=mm,view_units=yes,underline=no,merge_tol=no,to_arc_center=no,two_sided_diam=no,magnify=1,vert_dimens_text_orientation=right')
        # draw to layer
        step.VOF()
        # 处理原点的线条 先把原点定义到profile外部 再去删除
        step.COM(f'dimens_set_origin,lyr_name={lay},x={xmin - 99},y={ymin - 99} ')
        step.VON()
        new_lyr = f'{lay}+++{step.pid}'
        step.COM(f'dimens_to_lyr,drawing_lyr={lay},new_lyr={new_lyr}')
        step.clearAll()
        step.affect(new_lyr)
        step.selectRectangle(xmin - 100, ymin - 100, xmin - 90, ymin - 90)
        if step.Selected_count():
            step.selectDelete()
        step.unaffectAll()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setStyleSheet('QMessageBox {font-size:12pt;}')
    app.setWindowIcon(QIcon(':/res/demo.png'))
    jobname = os.environ.get('JOB')
    stepname = os.environ.get('STEP')
    if not jobname:
        QMessageBox.warning(None, 'warning', '请打开料号！')
        sys.exit()
    if not stepname:
        QMessageBox.warning(None, 'warning', '请打开step！')
        sys.exit()
    job = gen.Job(jobname)
    user = job.getUser()
    makeEntityDxf = MakeEntityDxf()
    makeEntityDxf.show()
    sys.exit(app.exec_())
