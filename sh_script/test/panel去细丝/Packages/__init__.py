#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --------------------------------------------------------- #
#                VTG.SH SOFTWARE GROUP                      #
# --------------------------------------------------------- #
# @Author       :    LiuChuang
# @Mail         :    Chuang_cs@163.com
# @Date         :    2023/02/06
# @Revision     :    1.0.0
# @File         :    __init__.py.py
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
'''版本记录
版本    ：V1.0.0
更新日期：2023/02/06
作者    ：Chuang.Liu
更新内容：

'''

import os
import sys

# --加载相对位置，以实现InCAM与Genesis共用
sys.path.append(r"%s/sys/scripts/Package" % os.getenv('SCRIPTS_DIR'))

import genCOM_26 as genCOM

GEN = genCOM.GEN_COM()
