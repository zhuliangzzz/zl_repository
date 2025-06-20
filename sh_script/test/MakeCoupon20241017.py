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
import Oracle_DB
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

    def AddDC(self):
        JOB_SQL = self.JOB.upper().split('-')[0] if '-' in self.JOB else self.JOB.upper()
        DB_O = Oracle_DB.ORACLE_INIT()
        self.dbc_h = DB_O.DB_CONNECT(host='172.20.218.193', servername='inmind.fls', port='1521',
                                          username='GETDATA', passwd='InplanAdmin')
        # 获取面次和类型
        sql2 = """
                   SELECT
                       i.ITEM_NAME AS JobName,
                       p.value
                   FROM
                       VGT_hdi.PUBLIC_ITEMS i,
                       VGT_hdi.JOB_DA job,
                           VGT_HDI.field_enum_translate p   
                   where  
                       i.ITEM_NAME = '%s'
                       AND i.item_id = job.item_id
                       AND i.revision_id = job.revision_id
                       and p.fldname = 'DC_SIDE_'
                       and p.enum=job.DC_SIDE_
                       and p.intname = 'JOB'		""" % JOB_SQL
        job_data2 = DB_O.SELECT_DIC(self.dbc_h, sql2)
        if not job_data2:
            return
        dc_side_dict = job_data2[0]
        # === 获取周期类型 ===
        sql3 = """
                   SELECT
                       i.ITEM_NAME AS JobName,
                       p.value
                   FROM
                       VGT_hdi.PUBLIC_ITEMS i,
                       VGT_hdi.JOB_DA job,
                           VGT_HDI.field_enum_translate p   
                   where  
                       i.ITEM_NAME = '%s'
                       AND i.item_id = job.item_id
                       AND i.revision_id = job.revision_id
                       and p.fldname = 'DC_TYPE_'
                       and p.enum=job.DC_TYPE_
                       and p.intname = 'JOB'""" % JOB_SQL
        job_data3 = DB_O.SELECT_DIC(self.dbc_h, sql3)
        if not job_data3:
            return
        dc_type_dict = job_data3[0]
        dc_layer = None
        mir = False
        if '文字' in dc_side_dict['VALUE']:
            if 'C' in dc_side_dict['VALUE']:
                dc_layer = 'c1'
            else:
                dc_layer = 'c2'
                mir = True
        if '阻焊' in dc_side_dict['VALUE']:
            if 'C' in dc_side_dict['VALUE']:
                dc_layer = 'm1'
            else:
                dc_layer = 'm2'
                mir = True
        if not dc_layer:
            return
        if dc_type_dict['VALUE'] in ['WWYY', "YYWW"]:
            type_value = dc_type_dict['VALUE'].replace("WW", "$$WW").replace("YY", "$$YY")
        else:
            type_value = dc_type_dict['VALUE'].replace("WW", "$$WW").replace("YY", "$$YY").replace("DD", "$$DD")
        if G.LAYER_EXISTS(dc_layer, job=self.JOB, step=self.couponName):
            G.CLEAR_LAYER()
            G.AFFECTED_LAYER(dc_layer, 'yes')
            G.COM('add_text,type=string,polarity=positive,attributes=no,x=0.5691,y=2.8975,text=%s,fontname=vgt_date,height=5.08,style=exact_size,width=exact_size,'
                  'mirror=no,angle=0,direction=cw,bar_type=upc39,bar_char_set=ascii,bar128_code=b,matrix=minimal,qr_matrix=minimal,bar_checksum=no,bar_background=yes,'
                  'bar_add_string=yes,bar_add_string_pos=top,bar_marks=yes,bar_width=0.2032,bar_height=5.08,bar_text_line=0,'
                  'x_size=1.016,x_space=0,y_size=1.27,w_factor=0.5,ver=1,datum_point=bottom_left,adjust_to_selected=no,delete_selected=no'% type_value)
            if mir:
                # 中心镜像
                infoDict = G.DO_INFO(' -t layer -e %s/%s/%s -d LIMITS,units=mm' % (self.JOB, self.couponName, dc_layer))
                xmin = infoDict['gLIMITSxmin']
                ymin = infoDict['gLIMITSymin']
                xmax = infoDict['gLIMITSxmax']
                ymax = infoDict['gLIMITSymax']
                xc = (xmin + xmax) / 2
                yc = (ymin + ymax) / 2
                G.COM(
                    'sel_transform,oper=mirror,x_anchor=%s,y_anchor=%s,angle=0,direction=ccw,x_scale=1,y_scale=1,x_offset=0,y_offset=0,mode=axis,duplicate=no' % (xc, yc))
            G.CLEAR_LAYER()
        # G.ADD_TEXT(2.5, 7, type_value, x_size=1.016, y_size=1.146, w_factor=0.6666666865, font="simplex")


    def Make(self):
        self.DeleteStep()
        self.CreatCoupon(20,9)
        self.PutCu()
        self.AddJOB()
        self.ADDPAD()
        # 20241010 加周期
        self.AddDC()
        QMessageBox.information(None, u'提示', u'制作完成！请检查！', QMessageBox.Ok)


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    Coupon().Make()
