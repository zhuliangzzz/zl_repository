#!/usr/bin/env python26
# -*- coding: utf-8 -*-
# --------------------------------------------------------- #
#                VTG.SH SOFTWARE GROUP                      #
# --------------------------------------------------------- #
# @Author       :    consenmy(吕康侠)
# @Mail         :    1943719064qq.com
# @Date         :    2024/09/05
# @Revision     :    1.0.0
# @File         :    MakeCoupon.py
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
import platform,sys,os
if platform.system() == "Windows":
    sys.path.append("Z:/incam/genesis/sys/scripts/Package")
else:
    sys.path.append("/incam/server/site_data/scripts/Package")
import genCOM_26
G=genCOM_26.GEN_COM()
from PyQt4.QtGui import QMessageBox
from PyQt4 import QtGui
class Coupon():
    def __init__(self):
        self.JOB=os.environ.get("JOB")
        self.STEP=os.environ.get("STEP")
        self.couponName='vip_coupon'
        self.drl= 'sz.via' if G.LAYER_EXISTS('sz.via') == 'yes' else 'drl'
        self.minSize=self.GetViaSize()
        self.outer=G.GET_ATTR_LAYER('outer')
        self.start_X=6
        self.start_Y=1.5
    def DeleteStep(self):
        if self.couponName in  G.GET_STEP_LIST():
            G.COM('delete_entity,job=%s,type=step,name=%s'%(self.JOB,self.couponName))
    def CreatCoupon(self,x,y):
        G.CREATE_ENTITY('',self.JOB,step=self.couponName)
        G.OPEN_STEP(self.couponName)
        G.CHANGE_UNITS('mm')
        G.COM('panel_size,width=%s,height=%s'%(x,y))
        G.COM('profile_to_rout,layer=ww,width=125')

    def PutCu(self):
        for l in G.GET_ATTR_LAYER('inner'):
            G.COM('sr_fill,polarity=positive,step_margin_x=0,step_margin_y=0,step_max_dist_x=100,step_max_dist_y=100,sr_margin_x=0,sr_margin_y=0,sr_max_dist_x=0,sr_max_dist_y=0,nest_sr=yes,stop_at_steps=,consider_feat=no,consider_drill=no,consider_rout=no,dest=layer_name,layer=%s,attributes=no'%l)
    def GetViaSize(self):
        info=G.DO_INFO('-t layer -e %s/panel/%s -m script -d SYMS_HIST'%(self.JOB,self.drl))
        if not info:
            QMessageBox.warning(None, u'错误', u'获取最小孔失败！请检查'+self.drl,QMessageBox.Ok)
            return
        drillList=sorted(info['gSYMS_HISTsymbol'],key=lambda x:float(x[1:]))
        return drillList[0]
    def AddJOB(self):
        G.CLEAR_LAYER()
        G.AFFECTED_LAYER('l1','yes')
        #add_text,attributes=no,type=string,x=4.4825825,y=1.486795,text=$$job,x_size=1.016,y_size=1.146,w_factor=0.6666666865,polarity=positive,angle=0,mirror=no,fontname=simplex,ver=1
        G.ADD_TEXT(2.5,7,"$$JOB",x_size=1.016,y_size=1.146,w_factor=0.6666666865,font="simplex")
    def ADDPAD(self):
        G.CLEAR_LAYER()
        for l in [self.drl]+self.outer:
            start_X = self.start_X
            size = self.minSize if l ==self.drl else 'r2000'
            G.CLEAR_LAYER()
            G.AFFECTED_LAYER(l,'yes')
            for h in range(3):
                start_Y = self.start_Y
                for s in range(2):
                    G.ADD_PAD(start_X,start_Y,size)
                    start_Y+=4
                start_X += 4
            G.CLEAR_LAYER()
    def Make(self):
        self.DeleteStep()
        self.CreatCoupon(20,9)
        self.PutCu()
        self.AddJOB()
        self.ADDPAD()
        QMessageBox.information(None, u'提示', u'制作完成！请检查！', QMessageBox.Ok)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    Coupon().Make()
