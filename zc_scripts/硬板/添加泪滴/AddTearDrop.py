#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:AddTearDrop.py
   @author:zl
   @time:2024/7/3 10:22
   @software:PyCharm
   @desc:
"""
import os
import sys

import qtawesome
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QDoubleValidator
from PyQt5.QtWidgets import QApplication, QWidget, QMessageBox, QAbstractItemView
import genClasses as gen
import res_rc

# foreach my $tmp_layer (@list) {
#     $layer = $elements[$tmp_layer]
# 	$f->COM(" affected_layer,name=$layer,mode=single,affected=yes")
# 	$wlhuse_method->copy_layer($layer.$$)
# }
# $f->COM(" chklist_single,action=frontline_dfm_tear_drop,show=no")
# $f->COM(" chklist_cupd,chklist=frontline_dfm_tear_drop,nact=1,params=((pp_layer=.affected)(pp_type=Filleted)(pp_target=Drilled Pads\;Undrilled Pads)(pp_radius_of_arc=$radius)(pp_radius_of_arc_min=1)(pp_ar=500)(pp_min_hole=0)(pp_max_hole=2032)(pp_spacing=$space)(pp_hole_spacing=0)(pp_del_old=No)(pp_selected=All)(pp_work_mode=Repair)(pp_handle_pads_drilled_by=PTH\;Via\;LASER-Via)),mode=regular")
# $f->COM(" chklist_run,chklist=frontline_dfm_tear_drop,nact=1,area=profile")
# $f->COM(" affected_layer,name=,mode=all,affected=no")

import AddTearDropUI as ui


class AddTearDrop(QWidget, ui.Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        self.label_title.setText(f'JOB:{jobname}\t Step:{stepname}')
        self.listWidget.addItems(job.SignalLayers)
        self.pushButton_selectAll.setIcon(qtawesome.icon('fa.reply-all', color='white'))
        self.pushButton_unselectAll.setIcon(qtawesome.icon('fa.undo', color='white'))
        self.pushButton_remove.setIcon(qtawesome.icon('fa.trash', color='white'))
        self.pushButton_exec.setIcon(qtawesome.icon('fa.download', color='white'))
        self.pushButton_exit.setIcon(qtawesome.icon('fa.sign-out', color='white'))
        self.lineEdit_size.setValidator(QDoubleValidator())
        self.lineEdit_spacing.setValidator(QDoubleValidator())
        self.lineEdit_size.setText('200')
        self.lineEdit_spacing.setText('50')
        self.listWidget.setSelectionMode(QAbstractItemView.MultiSelection)
        self.pushButton_selectAll.clicked.connect(lambda: self.listWidget.selectAll())
        self.pushButton_unselectAll.clicked.connect(lambda: self.listWidget.clearSelection())
        self.pushButton_remove.clicked.connect(self.removeTearDrop)
        self.pushButton_exec.clicked.connect(self.exec)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())
        self.setStyleSheet(
            'QPushButton{background-color:#0081a6;color:white;} QPushButton:hover{background:black;} QListWidget::Item:selected{background:#34AFD1;color:white;}')
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

    def removeTearDrop(self):
        items = self.listWidget.selectedItems()
        layers = [item.text() for item in items]
        if not layers:
            QMessageBox.warning(self, 'warning', '请选择线路层')
            return
        step.initStep()
        for layer in layers:
            step.affect(layer)
        step.setAttrFilter2('.tear_drop')
        step.selectAll()
        step.resetFilter()
        if step.Selected_count():
            step.selectDelete()
            step.unaffectAll()
            QMessageBox.information(self, '提示', '已删除.tear_drop属性的泪滴')
        else:
            step.unaffectAll()
            QMessageBox.information(self, '提示', '所选线路层未检测到.tear_drop属性的泪滴')


    def exec(self):
        size = self.lineEdit_size.text()
        spacing = self.lineEdit_spacing.text()
        items = self.listWidget.selectedItems()
        layers = [item.text() for item in items]
        if not layers:
            QMessageBox.warning(self, 'warning', '请选择线路层')
            return
        if size == '' or spacing == '':
            QMessageBox.warning(self, 'warning', '请检查参数是否输入')
            return
        step.initStep()
        # 备份
        for layer in layers:
            step.affect(layer)
            step.copySel(f'{layer}{step.pid}')
            step.unaffectAll()
        for layer in layers:
            step.affect(layer)
        checklist = gen.Checklist(step, type='frontline_dfm_tear_drop')
        checklist.action()
        # pp_layer =.affected)(pp_type=Filleted)(pp_target=Drilled
        # Pads\;Undrilled
        # Pads)(pp_radius_of_arc=$radius)(pp_radius_of_arc_min=1)(pp_ar=500)(pp_min_hole=0)(pp_max_hole=2032)(
        #     pp_spacing=$space)(pp_hole_spacing=0)(pp_del_old=No)(pp_selected=All)(pp_work_mode=Repair)(
        #     pp_handle_pads_drilled_by=PTH\;Via\;LASER - Via)
        params = {'pp_layer': '.affected',
                  'pp_type': 'Filleted',
                  'pp_target': 'Drilled Pads\;Undrilled Pads',
                  'pp_radius_of_arc': size,
                  'pp_radius_of_arc_min': '1',
                  'pp_ar': '500',
                  'pp_min_hole': '0',
                  'pp_max_hole': '2032',
                  'pp_spacing': spacing,
                  'pp_hole_spacing': '0',
                  'pp_del_old': 'No',
                  'pp_selected': 'All',
                  'pp_work_mode': 'Repair',
                  'pp_handle_pads_drilled_by': 'PTH\;Via\;LASER-Via'
                  }
        checklist.update(params=params)
        checklist.run()
        step.unaffectAll()
        # 删除生成的临时层
        for layer in layers:
            step.VOF()
            step.removeLayer(layer + '+++')
            step.VON()
        QMessageBox.information(self, '提示', '执行完成!')
        sys.exit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('fusion')
    app.setWindowIcon(QIcon(':/res/demo.png'))
    jobname = os.environ.get('JOB')
    stepname = os.environ.get('STEP')
    job = gen.Job(jobname)
    if not stepname:
        QMessageBox.warning(None, 'tips', '请打开step执行!')
        sys.exit()
    step = job.steps.get(stepname)
    ex = AddTearDrop()
    ex.show()
    sys.exit(app.exec_())
