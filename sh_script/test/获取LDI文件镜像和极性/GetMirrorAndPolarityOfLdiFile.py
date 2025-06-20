#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:GetMirrorAndPolarityOfLdiFile.py
   @author:zl
   @time: 2025/5/7 16:20
   @software:PyCharm
   @desc:
"""
import datetime
import glob
import os
import platform
import re
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import GetMirrorAndPolarityOfLdiFileUI_pyqt4 as ui

from PyQt4.QtGui import *
from PyQt4.QtCore import *

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")


class GetMirrorAndPolarityOfLdiFile(QWidget, ui.Ui_Form):
    def __init__(self):
        super(GetMirrorAndPolarityOfLdiFile, self).__init__()
        self.setupUi(self)
        self.render_()

    def render_(self):
        self.label_2.setText(u'Job：%s' % jobname)
        self.ldi_path = "/home/Incam/Desktop/%s系列\%s\%s" % (jobname[1:4].upper(),jobname.split('-')[0].upper(), jobname.split('-')[0][-2:].upper())
        ths = [u'文件名', u'镜像', u'极性']
        self.tableWidget.setColumnCount(len(ths))
        self.tableWidget.setHorizontalHeaderLabels(ths)
        self.tableWidget.horizontalHeader().setResizeMode(0, QHeaderView.Stretch)
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.setEditTriggers(QHeaderView.NoEditTriggers)
        self.radioButton.clicked.connect(self.radioButton_clicked)
        self.radioButton_2.clicked.connect(self.radioButton_clicked)
        self.pushButton_reload.clicked.connect(self.reload)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())
        self.setStyleSheet(
            '''
            QPushButton{font:10pt;background-color:#459B81;color:white;} QPushButton:hover{background:#333;}
            #label{background-color:#459B81;color:white;} #label_2{color:#459B81;}
            QTableWidget::Item:selected{background: rgb(224, 224, 224);color:black;}''')
        self.get_mirror_and_polarity()
        self.move((app.desktop().width() - self.geometry().width())/2, (app.desktop().height() - self.geometry().height())/2)

    def radioButton_clicked(self):
        if self.radioButton.isChecked():
            # print('radioButton_clicked')
            # self.ldi_path = "/windows/33.file/%s系列\%s\%s" % (jobname[1:4].upper(),jobname.split('-')[0].upper(), jobname.split('-')[0][-2:].upper())
            self.ldi_path = "/home/Incam/Desktop/临时文件夹/%s系列\%s\%s" % (jobname[1:4].upper(),jobname.split('-')[0].upper(), jobname.split('-')[0][-2:].upper())
        else:
            print('radioButton2_clicked')
            # 当天
            m, d = datetime.datetime.now().month, datetime.datetime.now().day
            # self.ldi_path = '/windows/33.file/03.CAM制作资料暂放（勿删）/000勿删/%s.%s' % (m, d)
            self.ldi_path = '/home/Incam/Desktop/000勿删/%s.%s' % (m, d)
        self.get_mirror_and_polarity()

    def get_mirror_and_polarity(self):
        # print(self.ldi_path)
        self.ldi_files = []
        # print(os.path.abspath(self.ldi_path))
        # print(os.listdir(self.ldi_path))
        self.tableWidget.clearContents()
        self.tableWidget.setRowCount(0)
        datas = []
        self.get_files(self.ldi_path)
        print(self.ldi_files)
        for file in self.ldi_files:
            if os.path.isfile(file):
                with open(file) as reader:
                    readlines = reader.readlines()
                if readlines:
                    mirror, polarity = 'no', None
                    # lines = list(filter(lambda readline: re.match('POLARITY|MIRRORY', readline.strip()), readlines))
                    lines = list((readline for readline in readlines if re.match('POLARITY|MIRRORY', readline.strip())))
                    if lines:
                        for line in lines:
                            if line.startswith('POLARITY'):
                                polarity = line.split('=')[1].strip()
                            if line.startswith('MIRRORY'):
                                mirror = line.split('=')[1].strip()
                    datas.append([file, mirror, polarity])
        self.tableWidget.setRowCount(len(datas))
        for row, data in enumerate(datas):
            self.tableWidget.setItem(row, 0, QTableWidgetItem(data[0]))
            self.tableWidget.setItem(row, 1, QTableWidgetItem(data[1]))
            item = QTableWidgetItem(data[2])
            if data[2] is None:
                item.setBackground(Qt.red)
            self.tableWidget.setItem(row, 2, item)


    def get_files(self, p_path):
        print(p_path)
        for path in glob.glob(os.path.join(p_path, '*')):
            print('1', path)
            if os.path.isdir(path):
                self.get_files(path)
            else:
                print(path)
                if os.path.basename(path).startswith('%s@' % jobname.split('-')[0]):
                    self.ldi_files.append(path.encode('utf-8').decode('utf-8'))


    def reload(self):
        self.get_mirror_and_polarity()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Cleanlooks')
    jobname = os.environ.get('JOB', None)
    get_mirror_and_polarity_of_ldi_file = GetMirrorAndPolarityOfLdiFile()
    get_mirror_and_polarity_of_ldi_file.show()
    sys.exit(app.exec_())
