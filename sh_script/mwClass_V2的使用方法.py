#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --------------------------------------------------------- #
#                VTG.SH SOFTWARE GROUP                      #
# --------------------------------------------------------- #
# @Author       :    LiuChuang
# @Mail         :    Chuang_cs@163.com
# @Date         :    2020/03/12
# @Revision     :    1.0.0
# @File         :    mw_gui.py
# @Software     :    PyCharm
# @Usefor       :
# --------------------------------------------------------- #

_header = {
    'description': '''
    -> 本程序主要服务于胜宏科技（惠州），任何其他团体或个人如需使用，必须经胜宏科技（惠州）相关负责
       人及作者的批准，并遵守以下约定；
    1> 本着尊重创作者的劳动成果，任何团体或个人在使用此程序的时候，均需要知会此程序的原始创作者；
    2> 在任何场合宣导、宣传，在任何文件、报告、邮件中提及本程序的全部或部分功能，均需要声明此程序的
       原始创作者；
    3> 在任何时候对本程序做部分修改或者是升级时，必须要保留文件的原始信息，包括原始文件名、创作者及
       联系方式、创作日期等信息，且不得删除程序中的源代码，只能进行注释处理；
'''
}
'''
                   _ooOoo_
                  o8888888o
                  88" . "88
                  (| -_- |)
                  O\  =  /O
               ____/`---'\____
             .'  \\|     |//  `.
            /  \\|||  :  |||//  \
           /  _||||| -:- |||||-  \
           |   | \\\  -  /// |   |
           | \_|  ''\---/''  |   |
           \  .-\__  `-`  ___/-. /
         ___`. .'  /--.--\  `. . __
      ."" '<  `.___\_<|>_/___.'  >'"".
     | | :  `- \`.;`\ _ /`;.`/ - ` : | |
     \  \ `-.   \_ __\ /__ _/   .-` /  /
======`-.____`-.___\_____/___.-`____.-'======
                   `=---='
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
           佛祖保佑       永无BUG
'''

import platform
import sys

from PyQt4 import QtGui, QtCore

# --加载相对位置，以实现InCAM与Genesis共用
if platform.system() == "Windows":
    sys.path.append(r"D:/genesis/sys/scripts/Package")

# --注意此模块的引入方式
from mwClass_V2 import *


class Example(QtGui.QWidget):

    def __init__(self):
        super(Example, self).__init__()

        self.initUI()

    def initUI(self):
        self.label = QtGui.QLabel("Ubuntu", self)

        self.label.move(55, 50)

        ok_button = QtGui.QPushButton(self)
        ok_button.setText('OK')
        ok_button.move(50, 100)

        self.connect(ok_button, QtCore.SIGNAL("clicked()"), self.onClick)

        self.setGeometry(250, 200, 350, 150)
        self.setWindowTitle('QComboBox')

        self.label.setText('Hello World...')

    def onClick(self):
        """
        绑定的click事件
        :return: None
        """
        M = AboutDialog(u'这是一个模态提示（选择后对象属性改变）...', cancel=True)
        M.exec_()
        self.label.setText(u'你选择的按钮时：\'%s\'' % M.selBut)
        self.label.adjustSize()


def main():
    app = QtGui.QApplication([])
    ex = Example()
    ex.show()
    app.exec_()


if __name__ == '__main__':
    main()
    selButton = showMsg(u'这是一个非模态提示，注意看终端打印信息...', Msg2=u'可接收第二个参数信息并显示', cancel=True)
    print (u'你选择的按钮时：\'%s\'' % selButton)
    # --
    selButton = showMsg(u"界面可先参数有：Msg2='', okButton='OK', cancel=False, cancelButton='Cancel''", cancel=True, cancelButton=u'取消')
