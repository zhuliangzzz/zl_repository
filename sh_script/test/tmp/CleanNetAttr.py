#!/usr/bin/env python26
# -*- coding: utf-8 -*-
# --------------------------------------------------------- #
#                VTG.SH SOFTWARE GROUP                      #
# --------------------------------------------------------- #
# @Author       :    consenmy(吕康侠)
# @Mail         :    1943719064qq.com
# @Date         :    2022/03/28
# @Revision     :    1.0.0
# @File         :    CleanNetAttr.py
# @Software     :    PyCharm
# @Usefor       :    
# --------------------------------------------------------- #
import platform,sys
from PyQt4 import QtGui
from PyQt4.QtGui import QMessageBox
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
if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
from messageBoxPro import msgBox
import genCOM_26
app = QtGui.QApplication(sys.argv)

g=genCOM_26.GEN_COM()
g.OPEN_STEP("net")
intlay=g.GET_ATTR_LAYER("inner")
if not intlay:
    msg_box = msgBox()
    msg_box.warning(None, u"提示", u"双面板不需要运行该流程！", QMessageBox.Yes)
    sys.exit()
g.CLEAR_LAYER()
for inl in intlay:g.AFFECTED_LAYER(inl,"yes")
g.COM("sel_delete_atr,attributes=.smd\;.bga")
g.SEL_BREAK()
g.CLEAR_LAYER()
g.CLOSE_STEP()
msg_box = msgBox()
msg_box.information(None, u"提示", u"net内层清除属性/打散完成！", QMessageBox.Yes)

