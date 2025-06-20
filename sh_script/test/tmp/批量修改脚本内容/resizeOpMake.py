#!usr/bin/python
# -*- coding: utf-8 -*-

__author__  = "tiger"
__date__    = "20230804"
__version__ = "Revision: 1.0.0 "
__credits__ = u"""十字架光学点补偿 """

import platform
import sys
import os
import re
if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
    sys.path.append(r"D:/pythonfile/Package")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
import gClasses
# from messageBoxPro import msgBox
from PyQt4.QtGui import QMessageBox,QMainWindow,QApplication
from PyQt4 import QtCore, QtGui
from gFeatures import *
from genesisPackages import  top
from create_ui_model import showMessageInfo,app
import math
from ui_main import Ui_MainWindow

jobName =  top.currentJob()
stepName = os.environ.get('STEP')
if stepName:
    job = gClasses.Job(jobName)
    step = gClasses.Step(job,stepName)

else:
    showMessageInfo(u"请打开step运行此程序")
    sys.exit()

step.COM("affected_layer,mode=all,affected=no")
step.COM('get_work_layer')
seclect_layer = step.COMANS
if seclect_layer == 'mark_op_back' or seclect_layer == 'mark_op_resize':
    showMessageInfo(u'不能选择%s层中物件,请重新选择!' % seclect_layer)
    sys.exit()
seclect_number=step.featureSelected()
if not seclect_number:
    showMessageInfo(u"当前step中未选择需要补偿的十字光学点,请选择后再运行此程序!")
    sys.exit()


class MyWindow(QMainWindow, Ui_MainWindow):
    """
    前端界面
    """
    def __init__(self):
        super(MyWindow, self).__init__()
        self.initUI()
        self.signalControl()


    def initUI(self):
        self.setupUi(self)
        self.setWindowTitle(u'十字光点补偿')
        # self.LineEdit_cuoz.setText('1')
        # self.LineEdit_resize.setText('2.2')


    def signalControl(self):
        self.pushButton_apply.clicked.connect(self.runAdd)
        # 程序退出信号连接
        self.pushButton_exit.clicked.connect(self.WinExit)

    def WinExit(self):
        """
        :return:
        """
        sys.exit()

    def runAdd(self):
        dataerrs = []
        data = {}
        try:
            data['resize'] = float(self.LineEdit_resize.text())
        except:
            dataerrs.append(u'请填入正确的光学点补偿目标值!')
        try:
            data['cuoz'] = float(self.LineEdit_cuoz.text())
        except:
            dataerrs.append(u'请填入正确的铜厚')

        if dataerrs:
            str = '\n'.join(dataerrs)
            showMessageInfo(str)
        else:
            self.close()
            Main(data)

class Main:

    def __init__(self,d):
        self.mark_resize = d['resize']
        self.cu_oz = d['cuoz']
        self.bk_layers = ['mark_op1','mark_op2','mark_op3','mark_op4','mark_op5']
        self.initFeaTure()

    def initFeaTure(self):
        # 设定要转化的原始坐标值
        initmark_points = []
        self.del_bklayer()
        step.removeLayer('mark_op_back')
        step.createLayer('mark_op_back')
        step.removeLayer('mark_op_resize')
        step.createLayer('mark_op_resize')
        step.COM("affected_layer,mode=all,affected=no")
        step.COM('units, type=inch')
        step.resetFilter()
        step.copyToLayer('mark_op_back')
        step.clearAll()
        step.affect('mark_op_back')
        step.contourize(units='inch')
        step.unaffect('mark_op_back')
        infoLines = step.INFO("-t layer -e %s/%s/%s -d FEATURES " % (jobName, stepName,'mark_op_back'))
        for line in infoLines:
            point = {}
            if re.match('.*I$', line):
                point['x'] = line.split()[1]
                point['y'] = line.split()[2]
                initmark_points.append(point)
        # 对每个十字架光学点坐标分别进行处理
        for p in initmark_points:
            self.creat_bklayer()
            step.affect('mark_op_back')
            step.COM('sel_single_feat,operation=select,x=%s,y=%s,tol=10,cyclic=no' % (p['x'], p['y']))
            step.copyToLayer('mark_op1')
            step.unaffect('mark_op_back')
            self.convertSurface()
            self.del_bklayer()
        step.clearAll()
        step.affect('mark_op_resize')
        step.copyToLayer(seclect_layer)
        step.unaffect('mark_op_resize')
        # step.removeLayer('mark_op_back')
        step.display_layer(seclect_layer,num=1)
        step.display_layer('mark_op_back', num=2)
        step.removeLayer('mark_op_resize')
        showMessageInfo(u"程序运行完毕，请检查!")
        sys.exit()

    def convertSurface(self):
        line_45 = self.cu_oz / 2000
        leng_45 = line_45 * math.cos(math.radians(45))
        add_points = {}
        step.affect('mark_op1')
        step.COM('sel_resize,size=%s,corner_ctl=no' % str(self.mark_resize))
        step.copyToLayer('mark_op2')
        step.copyToLayer('mark_op3')
        step.copyToLayer('mark_op4')
        step.unaffect('mark_op1')
        step.affect('mark_op3')
        step.COM('sel_resize,size=%s,corner_ctl=no' % str(self.cu_oz*2))
        step.unaffect('mark_op3')
        step.affect('mark_op4')
        step.COM('sel_resize,size=-%s,corner_ctl=no' % str(self.mark_resize / 2))
        step.affect('mark_op2')
        step.affect('mark_op3')
        step.COM('sel_surf2outline,width=0.1')

        for lay in ['mark_op2','mark_op3','mark_op4']:
            mk = RelodeInfo()
            mk.get_marklayer_info(lay)
            for i in range(len(mk.fea_xe)):
                xe = mk.fea_xe[i]
                xs = mk.fea_xs[i]
                ye = mk.fea_ye[i]
                ys = mk.fea_ys[i]
                if lay == 'mark_op3':
                    if xe == xs == min(mk.fea_xe + mk.fea_xs):
                        add_points['2'] = (xe, ye)
                        add_points['24'] = (xs, ys)
                        if ye < ys:
                            add_points['2'], add_points['24'] = add_points['24'], add_points['2']
                    elif xe == xs == max(mk.fea_xe + mk.fea_xs):
                        add_points['12'] = (xe, ye)
                        add_points['14'] = (xs, ys)
                        if ye < ys:
                            add_points['12'], add_points['14'] = add_points['14'], add_points['12']
                    elif ye == ys == min(mk.fea_ye + mk.fea_ys):
                        add_points['18'] = (xe, ye)
                        add_points['20'] = (xs, ys)
                        if xe < xs:
                            add_points['20'], add_points['18'] = add_points['18'], add_points['20']
                    elif ye == ys == max(mk.fea_ye + mk.fea_ys):
                        add_points['6'] = (xe, ye)
                        add_points['8'] = (xs, ys)
                        if xe > xs:
                            add_points['6'], add_points['8'] = add_points['8'], add_points['6']

                elif lay == 'mark_op2' or lay == 'mark_op4':
                    pxs = list(set(mk.fea_xe + mk.fea_xs))
                    pys = list(set(mk.fea_ye + mk.fea_ys))
                    pxs.remove(min(pxs))
                    pxs.remove(max(pxs))
                    pys.remove(min(pys))
                    pys.remove(max(pys))
                    if lay == 'mark_op2':
                        if xe == xs == min(mk.fea_xe + mk.fea_xs):
                            add_points['1'] = (xs, ys + (ye - ys) / 2)
                        elif xe == xs == max(mk.fea_xe + mk.fea_xs):
                            add_points['13'] = (xs, ys + (ye - ys) / 2)
                        elif ye == ys == max(mk.fea_ye + mk.fea_ys):
                            add_points['7'] = (xs + (xe - xs) / 2, ys)
                        elif ye == ys == min(mk.fea_ye + mk.fea_ys):
                            add_points['19'] = (xs + (xe - xs) / 2, ys)
                        add_points['3'] = (min(pxs) - leng_45, max(pys))
                        add_points['5'] = (min(pxs), max(pys) + leng_45)
                        add_points['9'] = (max(pxs), max(pys) + leng_45)
                        add_points['11'] = (max(pxs) + leng_45, max(pys))
                        add_points['15'] = (max(pxs) + leng_45, min(pys))
                        add_points['17'] = (max(pxs), min(pys) - leng_45)
                        add_points['21'] = (min(pxs), min(pys) - leng_45)
                        add_points['23'] = (min(pxs) - leng_45, min(pys))
                    else:
                        add_points['4'] = (min(pxs), max(pys))
                        add_points['10'] = (max(pxs), max(pys))
                        add_points['16'] = (max(pxs), min(pys))
                        add_points['22'] = (min(pxs), min(pys))
        print add_points
        step.clearAll()
        step.affect('mark_op5')
        for i in range(len(add_points.keys())):
            fxs = add_points.get(str(i + 1))[0]
            fys = add_points.get(str(i + 1))[1]
            if i < 23:
                fxe = add_points.get(str(i + 2))[0]
                fye = add_points.get(str(i + 2))[1]
            else:
                fxe = add_points.get('1')[0]
                fye = add_points.get('1')[1]
            step.addLine(fxs,fys,fxe,fye,'r1')
        step.COM('sel_cut_data')
        step.copyToLayer('mark_op_resize')
        step.unaffect('mark_op5')

    def del_bklayer(self):
        """
        删除备份层
        :return:
        """
        for layer in self.bk_layers:
            step.removeLayer(layer)


    def creat_bklayer(self):
        """
        创建备份层
        :return:
        """
        for layer in self.bk_layers:
            step.createLayer(layer)


class RelodeInfo:
    def __init__(self):
        self.fea_xs, self.fea_ys, self.fea_xe, self.fea_ye = [], [], [], []

    def get_marklayer_info(self, layer):
        layer_cmd=gClasses.Layer(step,layer)
        feat_out=layer_cmd.featCurrent_LayerOut()
        for obj in feat_out["lines"]:
            self.fea_xs.append(obj.xs)
            self.fea_xe.append(obj.xe)
            self.fea_ys.append(obj.ys)
            self.fea_ye.append(obj.ye)
        pxs = list(set(self.fea_xs + self.fea_xe))
        pys = list(set(self.fea_ys + self.fea_ye ))
        if len(pxs) !=4 or len(pys)!=4:
            showMessageInfo(u"非标准类型十字光学点，暂不能运行此程序！")
            sys.exit()


if __name__ == "__main__":
    # app = QApplication(sys.argv)
    w = MyWindow()
    # 界面设置居中，改变linux时候不居中的情况
    screen = QtGui.QDesktopWidget().screenGeometry()
    size = w.geometry()
    w.move((screen.width() - size.width()) / 2, (screen.height() - size.height()) / 2)
    w.show()
    sys.exit(app.exec_())
