#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:AddGoldPlatedDryFilm.py
   @author:zl
   @time: 2024/10/26 14:06
   @software:PyCharm
   @desc:
   20241109 zl 手指带90°或270° 宽度和高度的值互换
"""

import os
import re
import sys
import platform

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
    sys.path.append(r"\\192.168.2.33\incam-share\incam\Path\OracleClient_x86\instantclient_11_1")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

import gClasses
import genClasses_zl as gen

from oracleConnect import oracleConn

from PyQt4 import QtCore, QtGui

job_name = os.environ.get('JOB')
Gjob = gClasses.Job(job_name)
matrixinfo = Gjob.matrix.getInfo()

step = gen.Step(Gjob, 'edit')

import AddGoldPlatedDryFilmUI_pyqt4 as ui


class AddGoldPlatedDryFilm(QtGui.QWidget, ui.Ui_Form):
    def __init__(self):
        super(AddGoldPlatedDryFilm, self).__init__()
        self.setupUi(self)
        self.render()

    def render(self):

        self.etch_process = [u'酸性蚀刻', u'碱性蚀刻', u'无蚀刻引线']
        self.comboBox.addItems(self.etch_process)
        self.comboBox.currentIndexChanged.connect(self.toggleProcess)
        self.comboBox.setCurrentIndex(self.get_etch_leads_flow())
        self.lineEdit.setValidator(QtGui.QDoubleValidator(self.lineEdit))
        self.lineEdit_2.setValidator(QtGui.QDoubleValidator(self.lineEdit_2))
        self.lineEdit_3.setValidator(QtGui.QDoubleValidator(self.lineEdit_3))
        self.lineEdit.setToolTip('0.0127mm~0.152mm')
        self.lineEdit.setText('0.0127')
        self.lineEdit_2.setText('0.075')
        self.lineEdit_2.setReadOnly(True)
        self.lineEdit_3.setText('3')
        self.toggleProcess()
        self.pushButton.clicked.connect(self.make)
        self.pushButton_2.clicked.connect(lambda: sys.exit())
        self.move((app.desktop().width() - self.geometry().width()) / 2,
                  (app.desktop().height() - self.geometry().height()) / 2)
        self.setStyleSheet(
            'QPushButton{background-color:#0081a6;color:white;} QPushButton:hover{background:black;}')

    def toggleProcess(self):
        if self.comboBox.currentText() == u'酸性蚀刻':
            self.lineEdit_2.setVisible(True)
            self.lineEdit_3.setVisible(True)
            self.label_3.setVisible(True)
            self.label_4.setVisible(True)
            self.label_7.setVisible(True)
            self.label_8.setVisible(True)
            # self.label_2.setVisible(True)
            # self.label_6.setVisible(True)
            # self.lineEdit.setVisible(True)
        elif self.comboBox.currentText() == u'碱性蚀刻':
            self.lineEdit_2.setVisible(False)
            self.lineEdit_3.setVisible(False)
            self.label_3.setVisible(False)
            self.label_4.setVisible(False)
            self.label_7.setVisible(False)
            self.label_8.setVisible(False)
            # self.label_2.setVisible(True)
            # self.label_6.setVisible(True)
            # self.lineEdit.setVisible(True)
        else:
            self.lineEdit_2.setVisible(False)
            self.lineEdit_3.setVisible(False)
            self.label_3.setVisible(False)
            self.label_4.setVisible(False)
            self.label_7.setVisible(False)
            self.label_8.setVisible(False)
            # self.label_2.setVisible(False)
            # self.label_6.setVisible(False)
            # self.lineEdit.setVisible(False)
        self.adjustSize()

    def make(self):
        # if 'edit' not in matrixinfo["gCOLstep_name"]:
        #     QtGui.QMessageBox.warning(self, '警告','没有edit')
        #     sys.exit()
        top_spc = self.lineEdit.text()  # 上方曝光开窗大小
        bot_spc = self.lineEdit_2.text()  # 下方曝光开窗大小
        bot_oli_area = self.lineEdit_3.text()  # 下油区大小
        if self.comboBox.currentText() == u'酸性蚀刻':
            if not top_spc or not bot_spc or not bot_oli_area:
                QtGui.QMessageBox.warning(self, u'提示', u'参数不能为空')
                return
            top_spc = float(top_spc)
            bot_spc = float(bot_spc)
            bot_oli_area = float(bot_oli_area) * 25.4
        elif self.comboBox.currentText() == u'碱性蚀刻':
            if not top_spc:
                QtGui.QMessageBox.warning(self, u'提示', u'参数不能为空')
                return
            top_spc = float(top_spc)
            bot_spc = 0
            bot_oli_area = float(bot_oli_area) * 25.4
        else:
            if not top_spc:
                QtGui.QMessageBox.warning(self, u'提示', u'参数不能为空')
                return
            top_spc = float(top_spc)
            bot_oli_area = float(bot_oli_area) * 25.4
        step.initStep()
        xlym_list = {'xlym-c': 'l1', 'xlym-s': 'l%s' % len(Gjob.matrix.returnRows('board', 'signal|power_ground'))}
        if self.comboBox.currentText() == u'无蚀刻引线':
            for xlym in xlym_list:
                sm = 'm1' if xlym == 'xlym-c' else 'm2'
                step.removeLayer(xlym)
                step.createLayer(xlym)
                step.affect(sm)
                step.copyToLayer(xlym, size=254)
                step.unaffectAll()
        else:
            for xlym, signal in xlym_list.items():
                step.removeLayer(xlym)
                step.createLayer(xlym)
                step.prof_to_rout(xlym)
                step.affect(xlym)
                step.selectCutData()
                step.selectResize(508)
                step.unaffectAll()
                # 用引线去找手指（不准确）
                tmp = '%s+++%s' % (signal, step.pid)
                tmp_ = '%s+++' % tmp
                # step.affect(signal)
                # step.setAttrFilter2('.n_electric')
                # step.setAttrFilter2('.patch')
                # step.setAttrFilter2('.gold_plating')
                # step.setAttrLogic(0)
                # step.selectAll()
                # step.resetFilter()
                # if step.Selected_count():
                #     step.copySel(tmp)
                #     step.setSymbolFilter('rect*')
                #     step.refSelectFilter(tmp)
                #     step.resetFilter()
                #     if step.Selected_count():
                #         step.truncate(tmp)
                #         step.copySel(tmp)
                # step.unaffectAll()
                # 属性去找
                step.affect(signal)
                step.resetFilter()
                step.setAttrFilter('.string', 'text=gf')
                step.selectAll()
                step.resetFilter()
                if step.Selected_count():
                    step.copySel(tmp)
                else:
                    step.unaffectAll()
                    continue
                step.unaffectAll()
                step.affect(tmp)
                step.copySel(tmp_)
                step.unaffectAll()
                step.affect(tmp_)
                step.Contourize()
                step.selectResize(-1)
                step.unaffectAll()
                step.affect(tmp)
                step.refSelectFilter(tmp_, mode='cover')
                if step.Selected_count():
                    step.selectDelete()
                step.unaffectAll()
                info = step.Features_INFO(tmp)
                rects = []
                for d in info:
                    x, y, symbol, angle = float(d[1]), float(d[2]), d[3], d[6]
                    if symbol.startswith('rect'):
                        rects.append([x, y, symbol, angle])
                rects = sorted(rects, key=lambda k: k[0])
                # print(rects)
                step.removeLayer(tmp)
                step.removeLayer(tmp_)
                lines = []
                # 3mil * 25.4 = 76.2um
                for i in range(len(rects)-1):
                    cx1, cy1 = rects[i][0], rects[i][1]
                    if rects[i][3] in ['90', '270']:
                        w1, h1 = float(rects[i][2].replace('rect', '').split('x')[1])/1000, float(
                            rects[i][2].replace('rect', '').split('x')[0])/1000
                    else:
                        w1, h1 = float(rects[i][2].replace('rect', '').split('x')[0]) / 1000, float(
                            rects[i][2].replace('rect', '').split('x')[1]) / 1000
                    cx2, cy2 = rects[i + 1][0], rects[i + 1][1]
                    if rects[i][3] in ['90', '270']:
                        w2, h2 = float(rects[i + 1][2].replace('rect', '').split('x')[1])/1000, float(
                            rects[i + 1][2].replace('rect', '').split('x')[0])/1000
                    else:
                        w2, h2 = float(rects[i + 1][2].replace('rect', '').split('x')[0]) / 1000, float(
                            rects[i + 1][2].replace('rect', '').split('x')[1]) / 1000
                    # xs1, xs2 = cx1 - w1/2, cx2 - w2/2
                    # xe1, xe2 = cx1 - w1/2, cx2 + w2/2
                    # ybe, ys2= cy1 + h1/2, cy2 + h2/2
                    xts1, xts2 = cx1 - w1 / 2, cx2 - w2 / 2     # 上方x起始值
                    xte1, xte2 = cx1 + w1 / 2, cx2 + w2 / 2     # 上方x终止值
                    yts1, yts2 = cy1 + h1 / 2 + top_spc, cy2 + h2 / 2 + top_spc    # 上方y值
                    yte1, yte2 = cy1 - h1 / 2 - bot_spc, cy2 - h2 / 2 - bot_spc    # 下方y值
                    # 第一个位置
                    if i == 0:
                        lines.append([xts1 - 0.0762, yts1, xts1 - 0.0762, yte1])
                    lines.append([xts1 - 0.0762, yts1, xte1 + 0.0762, yts1])
                    if yts1 != yts2:
                        if yts1 > yts2:
                            lines.append([xte1 + 0.0762, yts1, xte1 + 0.0762, yts2])    # 起伏处的竖线
                            lines.append([xte1 + 0.0762, yts2, xts2 - 0.0762, yts2])
                        else:
                            lines.append([xte1 + 0.0762, yts1, xts2 - 0.0762, yts1])
                            lines.append([xts2 - 0.0762, yts1, xts2 - 0.0762, yts2])    # 起伏处的竖线
                    else:
                        lines.append([xte1 + 0.0762, yts2, xts2 - 0.0762, yts2])
                    #
                    lines.append([xts1 - 0.0762, yte1, xte1 + 0.0762, yte1])
                    if yte1 != yte2:
                        if yte1 < yte2:
                            lines.append([xte1 + 0.0762, yte1, xte1 + 0.0762, yte2])    # 起伏处的竖线
                            lines.append([xte1 + 0.0762, yte2, xts2 - 0.0762, yte2])
                        else:
                            lines.append([xte1 + 0.0762, yte1, xts2 - 0.0762, yte1])
                            lines.append([xts2 - 0.0762, yte1, xts2 - 0.0762, yte2])    # 起伏处的竖线
                    else:
                        lines.append([xte1 + 0.0762, yte2, xts2 - 0.0762, yte2])
                    i += 1
                else:
                    # 补充循环外最后一个位置的处理
                    lines.append([xts2 - 0.0762, yts2, xte2 + 0.0762, yts2])
                    lines.append([xts2 - 0.0762, yte2, xte2 + 0.0762, yte2])
                    lines.append([xte2 + 0.0762, yts2, xte2 + 0.0762, yte2])
                test_xlym = 'test_%s' % xlym
                step.removeLayer(test_xlym)
                step.createLayer(test_xlym)
                step.affect(test_xlym)
                for line in lines:
                    step.addLine(line[0], line[1], line[2], line[3], 'r10')
                step.selectCutData()
                step.copyToLayer(xlym, 'yes', size=7516)
                step.unaffectAll()
                step.affect(xlym)
                step.Contourize()
                step.unaffectAll()
                step.affect('drl')
                step.setFilterTypes('line')
                step.selectAll()
                step.resetFilter()
                if step.Selected_count():
                    step.copyToLayer(test_xlym, size=254)
                step.unaffectAll()
                step.affect(test_xlym)
                step.Contourize()
                step.copySel(xlym)
                step.unaffectAll()
                step.removeLayer(test_xlym)
                step.removeLayer(test_xlym + '+++')
                step.removeLayer(xlym + '+++')
        QtGui.QMessageBox.information(self, u'提示', u'制作完成！')
    # 获取蚀刻引线流程
    def get_etch_leads_flow(self):
        etch_leads_flow = 2
        conn = oracleConn("inmind")
        sql = '''
             SELECT 
        RJTSL.JOB_NAME,
        RJTSL.DESCRIPTION process_description,
        RJTSL.ORDER_NUM,
        RJTSL.TRAVELER_ORDERING_INDEX,
        RJTSL.work_center_code,
        ats.description work_description,
        ats.value_as_string,
        nts.note_string,
        RJTSL.SITE_NAME,
        RJTSL.operation_code,
        proc.mrp_name
        FROM VGT_HDI.RPT_JOB_TRAV_SECT_LIST RJTSL
        left JOIN VGT_HDI.process proc
        on RJTSL.proc_item_id = proc.item_id 
        and RJTSL.proc_revision_id = proc.revision_id 
        left JOIN VGT_HDI.note_trav_sect nts
        ON RJTSL.item_id = nts.item_id
        and RJTSL.revision_id = nts.revision_id
        and RJTSL.sequential_index = nts.section_sequential_index
        left JOIN VGT_HDI.attr_trav_sect ats
        ON RJTSL.item_id = ats.item_id
        and RJTSL.revision_id = ats.revision_id
        and RJTSL.sequential_index = ats.section_sequential_index
        WHERE RJTSL.JOB_NAME = '%s' and RJTSL.work_center_code = '金手指去导线SES'
        ORDER BY RJTSL.ORDER_NUM, RJTSL.TRAVELER_ORDERING_INDEX''' % job_name.upper()[:13]
        data_info = conn.select_dict(sql, is_arraysize=False)
        if data_info:
            process = list(map(lambda info: info['PROCESS_DESCRIPTION'], data_info))
            if process:
                etch_leads_flow = process[0]
        if etch_leads_flow == '酸性蚀刻':
            etch_leads_flow = 0
        elif etch_leads_flow == '碱性蚀刻':
            etch_leads_flow = 1
        return etch_leads_flow


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    add_gold_plated_dry_film = AddGoldPlatedDryFilm()
    add_gold_plated_dry_film.show()
    sys.exit(app.exec_())
