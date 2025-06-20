#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:main.py
   @author:zl
   @time: 2024/10/11 19:25
   @software:PyCharm
   @desc:
"""
import sys

import testUI as ui

from PyQt4 import QtCore, QtGui


class Main(QtGui.QWidget, ui.Ui_Form):
    def __init__(self):
        super(Main, self).__init__()
        self.setupUi(self)
        app.desktop().width


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    print()
    main = Main()
    main.show()
    sys.exit(app.exec_())