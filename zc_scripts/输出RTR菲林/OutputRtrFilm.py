#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:OutputRtrFilm.py
   @author:zl
   @time:2024/9/10 15:28
   @software:PyCharm
   @desc:输出RTR菲林
"""
import datetime
import os
import re
import sys

import qtawesome
from PyQt5.QtGui import QIcon, QIntValidator
from PyQt5.QtWidgets import QWidget, QApplication, QMessageBox
import OutputRtrFilmUI as ui
import genClasses as gen
import res_rc

class OutputRtrFilm(QWidget, ui.Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        self.label_title.setText(f'Job: {jobname}')
        self.listWidget.addItems(job.matrix.returnRows('board', 'signal'))
        self.lineEdit.setText(f'D:/{jobname}/FILM')
        self.lineEdit_xscale.setValidator(QIntValidator())
        self.lineEdit_yscale.setValidator(QIntValidator())
        self.lineEdit_xscale.setText('0')
        self.lineEdit_yscale.setText('0')
        self.pushButton_exec.setIcon(qtawesome.icon('fa.download', color='white'))
        self.pushButton_exit.setIcon(qtawesome.icon('fa.sign-out', color='white'))
        self.pushButton_exec.clicked.connect(self.exec)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())
        # self.setStyleSheet(
        #     '''
        #     QListWidget::Item{height:22px;} QListWidget::Item:selected{background-color:#459B81;}
        #     QPushButton{font:10pt;background-color:#459B81;color:white;} QPushButton:hover{background:#333;} #QCheckBox::indicator:checked{background:#459B81;} ''')
        self.setStyleSheet('''
        QPushButton{background-color:#0081a6;color:white;} QPushButton:hover{background:black;} QListWidget::Item{height:20px;} QListWidget::Item:selected{background: #0081a6;color:white;}
        ''')

    def exec(self):
        if not self.listWidget.selectedItems():
            QMessageBox.warning(self, '警告', '请选择线路层')
            return
        x_val = self.lineEdit_xscale.text()
        y_val = self.lineEdit_yscale.text()
        if x_val == '' and y_val == '':
            QMessageBox.warning(self, '警告', '请输入涨缩值')
            return
        x_val = float(x_val.replace('+', ''))
        y_val = float(y_val.replace('+', ''))
        path = self.lineEdit.text()
        signal = self.listWidget.selectedItems()[0].text()
        signal_b = f'{signal}-b'
        signal_c = f'{signal}-c'
        job.VOF()
        job.matrix.deleteRow(signal_b)
        job.matrix.deleteRow(signal_c)
        job.VON()
        job.matrix.copyRow(signal, signal_b)
        step = job.steps.get('pnl')
        self.step = step
        step.initStep()
        step.affect(signal_b)
        symbol = 'base_film_top'
        change_symbol = 'base_film_bot'
        if 'b' in signal:
            symbol = 'base_film_bot'
            change_symbol = 'base_film_top'
        step.selectSymbol(symbol)
        step.resetFilter()
        if step.Selected_count():
            step.moveSel(signal_c)
            step.unaffectAll()
            # profile
            prof = f'prof+++{step.pid}'
            pcs_fill = f'pcs+++{step.pid}'
            step.createLayer(prof)
            step.createLayer(pcs_fill)
            step.srFill(prof, sr_margin_x=-2540, sr_margin_y=-2540)
            step.srFill(pcs_fill)
            step.affect(pcs_fill)
            step.copySel(prof, 'yes')
            step.unaffectAll()
            step.affect(prof)
            step.Contourize()
            step.unaffectAll()
            step.affect(signal_c)
            step.selectChange(change_symbol)
            # 镜像
            step.Transform(oper='mirror', x_anchor=step.profile2.xcenter, y_anchor=step.profile2.ycenter)
            # 去除profile内1.5和pcs外2.0
            step.clip_area(margin=-1500, contour_cut='yes')
            step.clip_area('reference', contour_cut='yes', margin=2000, ref_layer=prof)
            step.unaffectAll()
            step.affect(signal_b)
            step.moveSel(signal_c)
            step.unaffectAll()
            step.affect(signal_c)
            step.moveSel(signal_b)
            step.unaffectAll()
            step.VOF()
            step.removeLayer(signal_c)
            step.removeLayer(prof)
            step.removeLayer(pcs_fill)
            step.VON()
        step.unaffectAll()
        step.getInfo()
        # 更新日期
        today = f'{datetime.date.today().year}.{"%02d" % datetime.date.today().month}.{datetime.date.today().day} '
        step.affect(signal_b)
        # 编号左移
        step.selectSymbol('zc-job*')
        step.resetFilter()
        if step.Selected_count():
            step.Transform(mode='axis', x_offset=-5)
        step.setFilterTypes('text')
        step.setTextFilter('*pcs/pnl*')
        step.selectAll()
        step.resetFilter()
        if step.Selected_count():
            lines = step.INFO(
                '-t layer -e %s/%s/%s -d features -o select,units=mm' % (jobname, step.name, signal_b))
            del lines[0]
            text = lines[0].split("'")[1]
            if not re.search('\d{4}\.\d+\.\d+', text):
                QMessageBox.warning(self, '警告', '日期不在pcs/pnl字符内，请检查！')
            else:
                newtext = re.sub('\d{4}\.\d+\.\d+', today, text)
                step.changeText(newtext)
        step.unaffectAll()
        x_scale = 1 - abs(x_val) / 10000 if x_val < 0 else 1 + x_val / 10000
        y_scale = 1 - abs(y_val) / 10000 if y_val < 0 else 1 + y_val / 10000
        step.layers.get(signal).setGenesisAttr('.out_x_scale', x_scale)
        step.layers.get(signal).setGenesisAttr('.out_y_scale', y_scale)
        step.layers.get(signal_b).setGenesisAttr('.out_x_scale', x_scale)
        step.layers.get(signal_b).setGenesisAttr('.out_y_scale', y_scale)
        step.Gerber274xOut(signal_b, path, x_scale=x_scale, y_scale=y_scale, line_units='mm', break_sr='no',
                           units='mm')
        step.Gerber274xOut(signal, path, x_scale=x_scale, y_scale=y_scale, line_units='mm', break_sr='no',
                           units='mm')
        # 回读
        different_layers = []
        for layer in (signal, signal_b):
            name = f'{layer}.gbr'
            step.COM('input_manual_reset')
            step.COM(
                f'input_manual_set,path={path}/{name},job={jobname},step={step.name},format=Gerber274x,data_type=ascii,units=mm,coordinates=absolute,zeroes=trailing,nf1=3,nf2=5,decimal=no,separator=*,tool_units=inch,layer={name},wheel=,wheel_template=,nf_comp=0,multiplier=1,text_line_width=0.0024,signed_coords=no,break_sr=yes,drill_only=no,merge_by_rule=no,threshold=200,resolution=3')
            step.COM('input_manual,script_path=')
            res = self.do_compare(layer, name, x_scale, y_scale)
            if res:
                different_layers.append(res)
        if different_layers:
            QMessageBox.warning(self, '提示',
                                f"导出完成！\n回读对比结果：{'、'.join(different_layers)}导出前后有差异，请检查!")
        else:
            QMessageBox.information(self, '提示', '导出完成！\n回读对比结果：导出前后无差异.')


    def do_compare(self, layer, layer_after, x_scale, y_scale):
        map_layer = f'{layer}+++compare'
        self.step.affect(layer_after)
        if x_scale != 1 or y_scale != 1:
            self.step.Transform(oper='scale', x_scale=2-x_scale, y_scale=2-y_scale)
        self.step.unaffectAll()
        self.step.VOF()
        self.step.compareLayers(layer, jobname, self.step.name, layer_after, tol=25.4, map_layer=map_layer, map_layer_res=200)
        self.step.VON()
        self.step.affect(map_layer)
        self.step.selectSymbol('r0')
        self.step.resetFilter()
        count = self.step.Selected_count()
        self.step.unaffectAll()
        self.step.removeLayer(map_layer)
        if count:
            return layer
        else:
            return None


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('fusion')
    app.setWindowIcon(QIcon(':/res/demo.png'))
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    if not job.steps.get('pnl'):
        QMessageBox.warning(None, 'tips', '没有pnl！')
        sys.exit()
    step = job.steps.get('pnl')
    outputRtrFilm = OutputRtrFilm()
    outputRtrFilm.show()
    sys.exit(app.exec_())
