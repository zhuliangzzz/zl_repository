#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:UpdateSymbol.py
   @author:zl
   @time:2023/10/20 10:25
   @software:PyCharm
   @desc:
   更新symbol
"""
import os
import sys

import qtawesome
from PyQt5 import QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import UpdateSymbolUI as ui

sys.path.append('/genesis/sys/scripts/zl/lib')
import genClasses as gen


class UpdateSymbol(QWidget, ui.Ui_Form):
    def __init__(self):
        super(UpdateSymbol, self).__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        self.jobLabel.setText(f'JOB: {jobname}')
        self.SourceJobSelector.addItem('genesislib')
        self.symbolFilter.setPlaceholderText('输入symbol名过滤')
        info = job.DO_INFO(f'-t job -e {jobname} -d symbols_list')
        self.symbols = [str(symbol) for symbol in info.get('gSYMBOLS_LIST')]
        self.filter_symbols = ['plotcode'] if 'plotcode' in self.symbols else []
        self.sourcejob = self.SourceJobSelector.currentText()
        self.libsymbols = [str(symbol) for symbol in
                           job.DO_INFO(f'-t job -e {self.sourcejob} -d symbols_list').get('gSYMBOLS_LIST')]
        self.SymbolSelector.addItems(self.symbols)
        if self.filter_symbols:
            self.SymbolSelector.setCurrentText('plotcode')
        self.symbolFilter.textChanged.connect(self.filterSymbol)
        self.symbol_clear_btn.clicked.connect(self.clearUnusedSymbols)
        self.exec_btn.clicked.connect(self.exec)
        self.exit_btn.clicked.connect(self.exit)
        self.symbol_clear_btn.setIcon(qtawesome.icon('fa.trash', scale_factor=1, color='white'))
        self.exec_btn.setIcon(qtawesome.icon('fa.search', scale_factor=1, color='white'))
        self.exit_btn.setIcon(qtawesome.icon('fa.arrow-circle-o-right', scale_factor=1, color='white'))
        self.setStyleSheet(''' QPushButton{background: rgb(49,194,124);color:white;} 
            QPushButton:hover{background:#F7D674;color:black;}
            #label_4,QGroupBox,#label_3,#title,#jobLabel{color: green;}
            ''')
        self.move((app.desktop().width() - self.geometry().width()) / 2,
                  (app.desktop().height() - self.geometry().height()) / 2)

    def filterSymbol(self, t):
        t = t.strip()
        self.SymbolSelector.clear()
        if t == '':
            self.filter_symbols = self.symbols
        self.filter_symbols = list(filter(lambda s: t in s, self.symbols))
        self.SymbolSelector.addItems(self.filter_symbols)

    def exec(self):
        symbol = self.SymbolSelector.currentText()
        if symbol not in self.libsymbols:
            QMessageBox.warning(None, 'warning', f'{self.sourcejob}没有该symbol({symbol}),无法更新!')
            return
        job.COM(
            f'copy_entity,type=symbol,source_job={self.sourcejob},source_name={symbol},dest_job={jobname},dest_name={symbol},dest_database=')
        gen_job.close(0)
        QMessageBox.information(None, 'tips', f'{symbol}已更新，请检查！')
        sys.exit()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        gen_job.close(0)
        sys.exit()

    def exit(self):
        gen_job.close(0)
        sys.exit()

    def clearUnusedSymbols(self):
        job.COM(f'delete_unused_sym,job={jobname}')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setStyleSheet('QMessageBox{font:11pt;}')
    if not os.environ.get('JOB'):
        QMessageBox.warning(None, 'tips', '请打开料号')
        sys.exit()
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    gen_job = gen.Job('genesislib')
    updateSymbol = UpdateSymbol()
    updateSymbol.show()
    sys.exit(app.exec_())
