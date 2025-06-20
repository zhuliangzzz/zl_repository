#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:AddGoldFingerLine.py
   @author:zl
   @time: 2025/2/12 11:48
   @software:PyCharm
   @desc:添加金手指引线
"""
import os
import sys

import platform
import AddGoldFingerLineUI_pyqt4 as ui

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

from genesisPackages_zl import outsignalLayers
import genClasses_zl as gen
from PyQt4 import QtCore, QtGui


class AddGoldFingerLine(QtGui.QWidget, ui.Ui_Form):
    def __init__(self):
        super(AddGoldFingerLine, self).__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        self.checkBox.clicked.connect(self.check_inner)
        self.setStyleSheet(
            '#pushButton_exec{background-color:#0081a6;color:white;}#pushButton_exit{background-color:#464646;color:white;} '
            '#pushButton_exec:hover,#pushButton_exit:hover{background:#882F09;}QMessageBox{font:10pt;}')
        self.pushButton_exec.clicked.connect(self.run)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())

    def check_inner(self):
        if self.checkBox.isChecked():
            self.stackedWidget.setCurrentIndex(1)
        else:
            self.stackedWidget.setCurrentIndex(0)

    def run(self):
        # spacing = 1.4
        is_inner = self.checkBox.isChecked()
        if not is_inner:
            spacing = self.doubleSpinBox.value()
            if not spacing:
                QtGui.QMessageBox.warning(self, u'验证', u'请输入引线超出profile的间距')
                return
        else:
            spacing = self.doubleSpinBox_2.value()
            if not spacing:
                QtGui.QMessageBox.warning(self, u'验证', u'请输入引线与手指中心的间距')
                return
        step.initStep()
        for outsignalLayer in outsignalLayers:
            tmp_signal = '%s+++' % outsignalLayer
            tmp_signal_ = '%s_+++' % outsignalLayer
            step.removeLayer(tmp_signal)
            step.removeLayer(tmp_signal_)
            step.affect(outsignalLayer)
            step.copySel(tmp_signal)
            step.unaffectAll()
            # 用引线去找手指（不准确）
            tmp = '%s_finger+++' % outsignalLayer
            step.removeLayer(tmp)
            # 属性去找
            step.affect(outsignalLayer)
            # step.setSymbolFilter('rect*\;psm*\;construct*')
            step.setAttrFilter('.string', 'text=gf')
            step.selectAll()
            step.resetFilter()
            if step.Selected_count():
                step.copySel(tmp)
            else:
                step.unaffectAll()
                continue
            step.unaffectAll()
            # 判断手指位置 上下左右
            area = None
            # 框选区域判断
            step.affect(tmp)
            step.selectRectangle(step.profile2.xmin, step.profile2.ymin, step.profile2.xmax, step.profile2.ycenter)
            if step.Selected_count():
                step.selectReverse()
                if not step.Selected_count():
                    area = 'b'
            if not area:
                step.selectRectangle(step.profile2.xmin, step.profile2.ycenter, step.profile2.xmax, step.profile2.ymax)
                if step.Selected_count():
                    step.selectReverse()
                    if not step.Selected_count():
                        area = 't'
            if not area:
                step.selectRectangle(step.profile2.xmin, step.profile2.ymin, step.profile2.xcenter, step.profile2.ymax)
                if step.Selected_count():
                    step.selectReverse()
                    if not step.Selected_count():
                        area = 'l'
            if not area:
                step.selectRectangle(step.profile2.xcenter, step.profile2.ymin, step.profile2.xmax, step.profile2.ymax)
                if step.Selected_count():
                    step.selectReverse()
                    if not step.Selected_count():
                        area = 'r'
            step.unaffectAll()
            if not area:
                QtGui.QMessageBox.warning(None, u'异常', u'未判断出手指方向,无法添加引线')
                exit()
            info = step.Features_INFO(tmp)
            step.affect(tmp_signal)
            step.setFilterTypes('line')
            step.COM(
                'set_filter_attributes,filter_name=popup,exclude_attributes=no,condition=no,attribute=.n_electric,min_int_val=0,max_int_val=0,min_float_val=0,max_float_val=0,option=,text=')
            step.COM(
                'set_filter_attributes,filter_name=popup,exclude_attributes=no,condition=no,attribute=.bit,min_int_val=0,max_int_val=0,min_float_val=0,max_float_val=0,option=,text=')
            step.COM('set_filter_and_or_logic,filter_name=popup,criteria=inc_attr,logic=or')
            step.selectAll()
            step.resetFilter()
            if step.Selected_count():
                step.selectDelete()
            # 再复制一层用来找网络
            if not is_inner:
                step.copySel(tmp_signal_)
            step.unaffectAll()
            step.truncate(tmp)
            coors = []
            for d in info:
                x, y = float(d[1]), float(d[2])
                coors.append((x, y))
            # 排序 保证留下的是最左边或最上面的那根引线 便于观察到同网络的引线
            if area in ('b', 't'):
                coors.sort(key=lambda k: k[0])
            else:
                coors.sort(key=lambda k: k[1], reverse=True)
            step.affect(tmp)
            step.addAttr_zl('.n_electric')
            if not is_inner:
                for x, y in coors:
                    if area == 'b':
                        step.addLine(x, y, x, step.profile2.ymin - spacing, 'r254', attributes='yes')
                    elif area == 't':
                        step.addLine(x, y, x, step.profile2.ymax + spacing, 'r254', attributes='yes')
                    elif area == 'l':
                        step.addLine(x, y, step.profile2.xmin - spacing, y, 'r254', attributes='yes')
                    else:
                        step.addLine(x, y, step.profile2.xmax + spacing, y, 'r254', attributes='yes')
                step.resetAttr()
                step.unaffectAll()
                tmp_finger = '%s_finger_+++' % outsignalLayer
                step.removeLayer(tmp_finger)
                layer_cmd = gen.Layer(step, tmp)
                # 每条网络对应的引线index
                finger_group = []
                for x, y in coors:
                    step.affect(tmp_signal_)
                    step.COM('sel_net_feat,operation=select,x=%s,y=%s,tol=10,use_ffilter=no' % (x, y))
                    if step.Selected_count():
                        step.moveSel(tmp_finger)
                        step.unaffectAll()
                        step.affect(tmp)
                        step.refSelectFilter(tmp_finger)
                        if step.Selected_count() > 1:
                            feat_out = layer_cmd.featout_dic_Index(options="feat_index+select")['lines']
                            finger_group.append([obj.feat_index for obj in feat_out])
                    step.unaffectAll()
                    step.VOF()
                    step.truncate(tmp_finger)
                    step.VON()
                step.removeLayer(tmp_finger)
                step.removeLayer(tmp_signal_)
                # 把引线index每组的第二个往后的index物件删掉只保留第一个，也就是同网络只留一根引线
                if finger_group:
                    step.affect(tmp)
                    for finger_indexs in finger_group:
                        for index in finger_indexs[1:]:
                            step.selectByIndex(tmp, index)
                    step.selectDelete()
                    step.moveSel(tmp_signal)
                    step.unaffectAll()
                step.removeLayer(tmp)
            else:
                if area == 'b':
                    y = max(map(lambda coor: coor[1], coors))
                elif area == 't':
                    y = min(map(lambda coor: coor[1], coors))
                elif area == 'l':
                    y = max(map(lambda coor: coor[0], coors))
                else:
                    y = min(map(lambda coor: coor[0], coors))
                for i in range(len(coors)-1):
                    if area == 'b':
                        step.addLine(coors[i][0], y + spacing, coors[i+1][0], y + spacing, 'r254', attributes='yes')
                    elif area == 't':
                        step.addLine(coors[i][0], y - spacing, coors[i+1][0], y - spacing, 'r254', attributes='yes')
                    elif area == 'l':
                        step.addLine(y + spacing, coors[i][1], y + spacing, coors[i+1][1], 'r254', attributes='yes')
                    else:
                        step.addLine(y - spacing, coors[i][1], y - spacing, coors[i+1][1], 'r254', attributes='yes')
                step.resetAttr()
                step.unaffectAll()
                step.affect(tmp)
                step.moveSel(tmp_signal)
                step.unaffectAll()
                step.removeLayer(tmp)
        QtGui.QMessageBox.information(None, u'运行完成', u'请查看:\n%s' % u'\n'.join(
            ['%s+++' % outsignalLayer for outsignalLayer in outsignalLayers]))
        exit()


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    app.setStyle('Cleanlooks')
    # app.setStyleSheet('*{font:11pt;selection-background-color: transparent; selection-color:black;}')
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    if 'edit' not in job.stepsList:
        exit()
    step = gen.Step(job, 'edit')
    addGoldFingerLine = AddGoldFingerLine()
    addGoldFingerLine.show()
    sys.exit(app.exec_())
