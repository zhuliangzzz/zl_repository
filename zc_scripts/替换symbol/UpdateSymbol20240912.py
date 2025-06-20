#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:UpdateSymbol.py
   @author:zl
   @time:2023/11/02 10:25
   @software:PyCharm
   @desc:
"""
import os
import sys

import qtawesome
from PyQt5 import QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import UpdateSymbolUI as ui
import genClasses as gen
import res_rc


class UpdateSymbol(QWidget, ui.Ui_Form):
    def __init__(self):
        super(UpdateSymbol, self).__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        self.jobLabel.setText(f'JOB: {jobname}')
        self.SourceJobSelector.addItem('genesislib')
        info = job.DO_INFO(f'-t job -e {jobname} -d symbols_list')
        self.symbols = [str(symbol) for symbol in info.get('gSYMBOLS_LIST')]
        self.sourcejob = self.SourceJobSelector.currentText()
        self.libsymbols = [str(symbol) for symbol in
                           job.DO_INFO(f'-t job -e {self.sourcejob} -d symbols_list').get('gSYMBOLS_LIST')]
        self.SymbolSelector.addItems(self.symbols)
        # prepared symbols
        # Symbols = ['plotcode', 'fpc.zheng', 'fpc.fan', 'csx-cm2', 'cb810']
        # self.preparedSymbols = set(filter(lambda symbol: symbol in self.symbols, Symbols))
        # self.listWidget.addItems(self.preparedSymbols)
        self.listWidget.setSelectionMode(QAbstractItemView.MultiSelection)
        self.join_btn.setIcon(qtawesome.icon('fa.share', scale_factor=1, color='white'))
        self.unselect_btn.setIcon(qtawesome.icon('fa.reply', scale_factor=1, color='white'))
        self.unselectAll_btn.setIcon(qtawesome.icon('fa.reply-all', scale_factor=1, color='white'))
        self.symbol_clear_btn.setIcon(qtawesome.icon('fa.trash', scale_factor=1, color='white'))
        self.symbol_update_all_btn.setIcon(qtawesome.icon('mdi.update', scale_factor=1, color='white'))
        self.exec_btn.setIcon(qtawesome.icon('fa.download', scale_factor=1, color='white'))
        self.exit_btn.setIcon(qtawesome.icon('fa.sign-out', scale_factor=1, color='white'))
        self.join_btn.clicked.connect(self.join_symbol)
        self.unselect_btn.clicked.connect(self.unselect)
        self.unselectAll_btn.clicked.connect(self.unselectAll)
        self.symbol_clear_btn.clicked.connect(self.clearUnusedSymbols)
        self.symbol_update_all_btn.clicked.connect(self.update_all)
        self.exec_btn.clicked.connect(self.exec)
        self.exit_btn.clicked.connect(self.exit)
        self.setStyleSheet('''
            QComboBox{font-family:微软雅黑;}
            QPushButton{background-color:#0081a6;color:white;} QPushButton:hover{background:black;}
            #label_4,#label_5,QGroupBox,#label_3,#title,#jobLabel{color: #0081a6;}
            QListWidget{outline: 0px;border:0px;min-width: 120px;color:black;background:#ECE8E4;font:14px;background:white;} 
            QListWidget::Item{height:24px;border-radius:1.5px;} 
            QListWidget::Item:selected{background: #0081a6;color:white;}
            ''')

    def exec(self):
        if self.preparedSymbols:
            for symbol in self.preparedSymbols:
                job.COM(
                        f'copy_entity,type=symbol,source_job={self.sourcejob},source_name={symbol},dest_job={jobname},dest_name={symbol},dest_database=')
            gen_job.close(0)
            QMessageBox.information(None, 'tips', f'{"、".join(self.preparedSymbols)}已更新，请检查！')
            sys.exit()
        else:
            QMessageBox.information(None, 'tips', '请选择要更新的symbol！')

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        job.VOF()
        gen_job.close(0)
        job.VON()
        sys.exit()

    def exit(self):
        job.VOF()
        gen_job.close(0)
        job.VON()
        sys.exit()

    def join_symbol(self):
        this_sym = self.SymbolSelector.currentText()
        if this_sym not in self.symbols:
            QMessageBox.warning(None, 'tips', '请选择已有的symbol!')
            return
        if this_sym not in self.libsymbols:
            QMessageBox.warning(None, 'tips', 'symbol库中不含此symbol,无法更新!')
            return
        if this_sym not in self.preparedSymbols:
            self.preparedSymbols.add(this_sym)
            self.listWidget.addItem(this_sym)

    def unselect(self):
        if not self.listWidget.selectedItems():
            return
        self.preparedSymbols = self.preparedSymbols - {symbol.text() for symbol in self.listWidget.selectedItems()}
        self.listWidget.clear()
        self.listWidget.addItems(self.preparedSymbols)

    def unselectAll(self):
        self.listWidget.clear()
        self.preparedSymbols = set()

    def clearUnusedSymbols(self):
        job.COM(f'delete_unused_sym,job={jobname}')


    def update_all(self):
        illegal_symbols = []
        for symbol in self.symbols:
            if symbol in self.libsymbols:
                job.VOF()
                job.COM(
                    f'copy_entity,type=symbol,source_job={self.sourcejob},source_name={symbol},dest_job={jobname},dest_name={symbol},dest_database=')
                job.VON()
            else:
                illegal_symbols.append(symbol)
        gen_job.close(0)
        if illegal_symbols:
            QMessageBox.information(None, 'tips', f'已全部更新，请检查!')
        sys.exit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    app.setStyleSheet('QMessageBox{font:11pt;}')
    app.setWindowIcon(QIcon(':res/demo.png'))
    if not os.environ.get('JOB'):
        QMessageBox.warning(None, 'tips', '请打开料号!')
        sys.exit()
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    gen_job = gen.Job('genesislib')
    updateSymbol = UpdateSymbol()
    updateSymbol.show()
    sys.exit(app.exec_())
