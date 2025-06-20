#!/usr/bin/env python26
# -*- coding: utf-8 -*-
# --------------------------------------------------------- #
#                VTG.SH SOFTWARE GROUP                      #
# --------------------------------------------------------- #
# @Author       :    consenmy(吕康侠)
# @Mail         :    1943719064qq.com
# @Date         :    2022/03/07
# @Revision     :    1.0.0
# @File         :    ChangeEWMBll.py
# @Software     :    PyCharm
# @Usefor       :    
# --------------------------------------------------------- #
import datetime
import os
import re
import sys
import platform

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
    pass
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

import genCOM_26
g=genCOM_26.GEN_COM()
import Oracle_DB
from messageBoxPro import msgBox


class ChangeEWMBll():
    def __init__(self):
        self.JOB = os.environ.get("JOB", None)
        self.STEP = os.environ.get("STEP", None)
        self.User = g.getUser()
        self.GetStepList=g.GET_STEP_LIST(self.JOB)
        self.ZQlayerdic={}
        self.gs=''

    def GeteditWeek(self):
        """
        根据板内获取周期格式
        :return:
        """
        ZQLayer = self.GetZQBoardLayer()
        for l in ZQLayer:
            layline = g.INFO("-t layer -e %s/edit/%s -m display -d FEATURES" % (self.JOB, l))
            ZQG=''
            # if re.search("#P",re.IGNORECASE) 不区分大小写
            # P 3.0865596 -4.646504 zq-dynamic-yyww P 0 270 N
            # T -0.0295495 -0.0062186 vgt_date P 0 N 0.04 0.04 0.50000 '2121' 1;.nomenclature
            # T 10.533273 6.5290227 vgt_date P 0 N 0.2 0.2 2.00000 '2021' 1;.nomenclature
            for line in layline:
                if re.search("#P", line) and re.search("zq-", line,re.I):
                    linlist=line.strip().split(' ')
                    zqsy=linlist[3]
                    symline = g.INFO("-t symbol -e %s/%s -m display -d FEATURES"%(self.JOB,zqsy))
                    for sl in symline:
                        if re.search("#T", sl) and re.search("vgt_date", sl):
                            ZQG = sl.strip().split(' ')[10]

                elif re.search("#T", line) and re.search("vgt_date", line):
                    #ss=line.strip().split(' ')
                    ZQG=line.strip().split(' ')[10]

            ZQG=ZQG.strip("\'")

            if re.search("\$\$",ZQG):
                if re.search("\$\$\{?ww\}?\$\$\{?yy\}?", ZQG,re.I):
                    self.gs ='wwyy'
                elif re.search("\$\$\{?yy\}?\$\$\{?ww\}?", ZQG,re.I):
                    self.gs = 'yyww'
                ZQG=self.GetZQGS(ZQG)

            elif re.search("^\d{4}$", ZQG):
                ZQG = ZQG
            else:
                ZQG = ""
            if ZQG:self.ZQlayerdic[l] = ZQG

        for zqg in self.ZQlayerdic.keys():

            return (self.ZQlayerdic[zqg],self.gs) if self.ZQlayerdic[zqg] else ("","")

    def GetZQBoardLayer(self):
        return g.GET_ATTR_LAYER('silk_screen')+g.GET_ATTR_LAYER('solder_mask')+g.GET_ATTR_LAYER('outer')

    def GetZQGS(self,ZQG):
        data=''
        g.DELETE_LAYER("zqgs-tmp")
        ZQG1 = re.sub("\$\$", "$#",ZQG)
        g.OPEN_STEP("edit",job=self.JOB)
        g.CREATE_LAYER("zqgs-tmp","drl")
        g.CLEAR_LAYER()
        g.AFFECTED_LAYER("zqgs-tmp","yes")
        g.ADD_TEXT(0,0,ZQG1,1,1)

        line = g.INFO("-t layer -e %s/edit/zqgs-tmp -m display -d FEATURES" % (self.JOB))
        if "#T"in line[1]:
            datalist = line[1].strip().split(' ')
            data=datalist[10].strip("\'")
        g.DELETE_LAYER("zqgs-tmp")
        g.CLOSE_STEP()
        return data
    def CheckRun(self,editZQ,setZQ):
        """
        运行前检查
        :return:
        """
        ErrorList=[]
        if not "set" in self.GetStepList:
            ErrorList.append("没有set")
        if not "edit" in self.GetStepList:
            ErrorList.append("没有edit")
        # if setZQ and not re.search("\d{4,8}\-?\d*\-?\d*",setZQ):
        #     ErrorList.append("请输入正确的周期格式")
        pd=''
        data=GetInplanData().Getinplanzq(self.JOB.upper()[:13])
        zqgs=data[0]["DC_TYPE"]


        return ErrorList



    def CreadEWM(self,setzq,addmx,zqgs):
        """
        创建二维码
        :return:
        """
        g.OPEN_STEP("set")
        g.CHANGE_UNITS("mm")
        #strcode = "D%s;VLVGT4;" % setzq

        if platform.system() == "Windows":
            strcode = zqgs
        else:
            strcode=setzq
        i = 0
        retdic = {}
        while (i < 10):
            g.MOUSE("please select point")
            getpoint = g.MOUSEANS
            str1 = ''.join(getpoint)
            getpointarr = str1.split(' ')
            i += 1
            if i >= 10:
                self.ErrorBox(u"循环超过10次！程序退出")
            else:
                retdic[i] = self.AddERMZQ(getpointarr,  strcode, addmx)
                msg_box = msgBox()
                resu = msg_box.question(self, u"提示", u"已添加第%s个二维码，是否继续添加?" % i, QMessageBox.Yes, QMessageBox.No)
                if not resu == u"是": break
        msg_box = msgBox()
        msg_box.information(self, u"提示", u"添加完成请检查！", QMessageBox.Yes)
        for index in retdic.keys():
            for layer in retdic[index].keys():
                g.WORK_LAYER(layer)
                x1 = float(retdic[index][layer][0]) - 10
                y1 = float(retdic[index][layer][1]) + 23
                x2 = float(retdic[index][layer][0]) + 10
                y2 = float(retdic[index][layer][1]) - 23
                g.COM("zoom_area,x1=%s,y1=%s,x2=%s,y2=%s" % (x1, y1, x2, y2))
                g.PAUSE("Please Check")
        return
    def ChangeEwm(self,setzq,editzq):
        if editzq !=setzq[1:5]:self.ErrorBox(u"与板内周期不符!")
        ##symbol 形式
        g.OPEN_STEP("set")
        g.CHANGE_UNITS("mm")
        zqLayer = self.GetZQBoardLayer()
        symbollist=[]
        baklayer = []
        for ss in zqLayer:
            symboldictmp = g.DO_INFO("-t layer -e %s/set/%s -m script -d SYMS_HIST" % (self.JOB,ss))
            symbollist=symbollist+symboldictmp["gSYMS_HISTsymbol"]
        pd = 1
        new_list = list(set(symbollist))
        ##备份###
        for lay in zqLayer:
            g.CLEAR_LAYER()
            g.DELETE_LAYER(lay+"_bakk")
            g.AFFECTED_LAYER(lay,"yes")
            for sy in new_list:
                if re .search("zq-(2wm|ewm|wm)",sy):
                    g.FILTER_SET_INCLUDE_SYMS(sy,reset=1)
                    g.FILTER_SELECT()
                    if g.GET_SELECT_COUNT()>0:
                        baklayer.append(lay)
            g.CLEAR_LAYER()
        layerbak = list(set(baklayer))
        for bakl in layerbak:
            g.CLEAR_LAYER()
            g.AFFECTED_LAYER(bakl, "yes")
            g.SEL_COPY("%s_bakk"%bakl)
            g.CLEAR_LAYER()

        for sym in new_list:
            if re.search("zq-(2wm|ewm|wm)", sym):
                g.COM("open_entity,job=%s,type=symbol,name=%s,iconic=no" % (self.JOB, sym))
                g.AUX("set_group,group=" + g.COMANS)
                g.COM("units,type=mm")
                g.COM("display_layer,name=%s,display=yes,number=1" % sym)

                g.COM("work_layer,name=" + sym)

                g.FILTER_SELECT()
                g.COM(
                    "sel_change_txt,text=%s,x_size=-1,y_size=-1,w_factor=-1,polarity=no_change,mirror=no_change,fontname=" % setzq)
                g.COM("editor_page_close")

                pd = 2
        if pd == 2:
            pointlist = []
            layerpoint = {}
            #zqLayer = self.GetZQBoardLayer()
            for lay in zqLayer:
                line = g.INFO("-t layer -e %s/set/%s -m display -d FEATURES" % (self.JOB, lay))
                for lin in line:
                    if re.search("zq-(2wm|ewm|wm)", lin):
                        linelist = lin.strip().split(' ')
                        pointlist.append([linelist[1], linelist[2]])
                        layerpoint[lay] = pointlist
            msg_box = msgBox()
            msg_box.information(self, u"提示", u"修改完成请检查！", QMessageBox.Yes)
            g.OPEN_STEP("set")
            for k, v in layerpoint.items():
                g.WORK_LAYER(k)
                g.WORK_LAYER(k+"_bakk",2)
                for point in v:
                    x1 = float(point[0]) - 10
                    y1 = float(point[1]) + 23
                    x2 = float(point[0]) + 10
                    y2 = float(point[1]) - 23
                    g.COM("zoom_area,x1=%s,y1=%s,x2=%s,y2=%s" % (x1, y1, x2, y2))
                    g.PAUSE("Please Check")
            return
        #文字形式
        zqLayer = self.GetZQBoardLayer()
        pointlist = []
        layerpoint = {}

        for lay in zqLayer:
            line = g.INFO("-t layer -e %s/set/%s -m display -d FEATURES" % (self.JOB, lay))
            for lin in line:
                if re.search("(barcode|#B.*VLVGT4)", lin) and re.search("\sP\s",lin):
                    linelist = lin.strip().split(' ')
                    pointlist.append([linelist[1], linelist[2]])
                    baklayer.append(lay)
                    layerpoint[lay] = pointlist
        if not layerpoint:  self.ErrorBox("set 里没有找到二维码，请确定symbol名字")
        ##备份###
        layerbak = list(set(baklayer))
        for bakl in layerbak:
            g.CLEAR_LAYER()
            g.AFFECTED_LAYER(bakl, "yes")
            g.SEL_COPY("%s_bakk" % bakl)
            g.CLEAR_LAYER()
        for k, v in layerpoint.items():
            g.CLEAR_LAYER()
            g.AFFECTED_LAYER(k, "yes")
            for point in v:
                g.COM("sel_single_feat,operation=select,x=%s,y=%s,tol=367.47,cyclic=no" % (point[0], point[1]))
                aa = g.GET_SELECT_COUNT()
                if g.GET_SELECT_COUNT() > 0:
                    g.COM(
                        "sel_change_txt,text=%s,x_size=-25.4,y_size=-25.4,w_factor=-1,polarity=no_change,mirror=no_change,fontname=" % setzq)
            g.CLEAR_LAYER()
        msg_box = msgBox()
        msg_box.information(self, u"提示", u"修改完成请检查！", QMessageBox.Yes)
        for k, v in layerpoint.items():
            g.WORK_LAYER(k)
            g.WORK_LAYER(k+"_bakk",2)
            for point in v:
                x1 = float(point[0]) - 10
                y1 = float(point[1]) + 23
                x2 = float(point[0]) + 10
                y2 = float(point[1]) - 23
                g.COM("zoom_area,x1=%s,y1=%s,x2=%s,y2=%s" % (x1, y1, x2, y2))
                g.PAUSE("Please Check")
        return


    def GetSetEWMGS(self):
        zqLayer = self.GetZQBoardLayer()
        linelist=[]
        symbollist=[]
        for ss in zqLayer:
            symboldictmp = g.DO_INFO("-t layer -e %s/set/%s -m script -d SYMS_HIST" % (self.JOB, ss))
            symbollist = symbollist + symboldictmp["gSYMS_HISTsymbol"]
            line = g.INFO("-t layer -e %s/set/%s -m display -d FEATURES" % (self.JOB, ss))
            for l in line: linelist.append(l)
       
        pd = 1
        symboltext=[]
        new_list = list(set(symbollist))
       
        if re.search("zq-(2wm|ewm|wm)", "".join(new_list)):

            for sym in new_list:
                if re.search("zq-(2wm|ewm|wm)", sym):
                    symb=g.INFO("-t symbol -e %s/%s -m display -d FEATURES"%(self.JOB, sym))[1].strip().split(" ")
                   
                    if platform.system() == "Windows":
                        barcodetext=g.DO_INFO("-t symbol -e %s/%s -m script -d ATTR -p val"%(self.JOB,symb[3]))
                        dtat=barcodetext["gATTRval"][4].strip("\'")
                        symboltext.append(dtat)
                    else:
                        
                        zqq=str(symb[16].split(";.")[0].strip("\'"))
                        symboltext.append(zqq)
       
        if not symboltext:
            for zqlin in linelist:
                if re.search("barcode", zqlin) and \
                   re.search("\sP\s", zqlin) and \
                   not re.search(".string=auto_barcode", zqlin): # 增加剔除部分属性包含barcode的 例如s5500 pad
                    li=zqlin.strip().split(' ')[3]
                    barcodetext = g.DO_INFO("-t symbol -e %s/%s -m script -d ATTR -p val"%(self.JOB, li.strip()))

                    symboltext.append(barcodetext["gATTRval"][4])
                elif re.search("#B.*VLVGT4", zqlin) and re.search("\sP\s", zqlin):
                    li = zqlin.strip().split(' ')[16].strip("\'")
                    li=li.split(";.")[0].strip("\'")
                    
                    symboltext.append(li)
       
        return symboltext[0] if symboltext else ""
















        for lay in zqLayer:
            line = g.INFO("-t layer -e %s/set/%s -m display -d FEATURES" % (self.JOB, lay))
            for lin in line:
                if re.search("VLVGT4", lin) and re.search("\sP\s", lin):
                    linelist = lin.strip().split(' ')






    def ErrorBox(self,str):
        msg_box = msgBox()
        msg_box.critical(self, u"错误", str, QMessageBox.Yes)
        exit(0)

    # def AddERMZQbak(self,getpointarr,Old_or_new,strcode):
    #     """
    #     添加二维码
    #     :param getpointarr:
    #     :param Old_or_new:
    #     :return:
    #     """
    #     datadic={}
    #     for layer in self.ZQlayerdic .keys():
    #
    #         x, y = getpointarr
    #         g.CLEAR_LAYER()
    #         g.AFFECTED_LAYER(layer,"yes")
    #         Mirr = "no" if "1" in layer else "yes"
    #         if Mirr == 'yes':x=float (x)+7
    #         if Old_or_new == u"旧方式":
    #             g.COM("add_pad,attributes=no,x=%s,y=%s,symbol=zq-ewm,polarity=positive,angle=0,mirror=%s,nx=1,ny=1,dx=0,dy=0,xscale=1,yscale=1"%(x,y,Mirr))
    #         else:
    #             g.COM("add_text,attributes=no,type=barcode,x=%s,y=%s,text=%s,x_size=5.08,y_size=5.08,w_factor=2,polarity=positive,angle=0,mirror=%s,fontname=standard,bar_type=ECC-200,matrix=Minimal,bar_checksum=no,bar_background=no,bar_add_string=yes,bar_add_string_pos=top,bar_marks=no,bar_width=0.2032,bar_height=7,ver=1" % (x,y,strcode,Mirr))
    #         datadic[layer]=[x, y]
    #         g.CLEAR_LAYER()
    #     return datadic
    def AddERMZQ(self,getpointarr,strcode,addmax):
        """
        添加二维码
        :param getpointarr:
        :param

        Old_or_new:
        :return:
        """

        x, y = getpointarr
        datadic={}

        for layer in ["c1","c2"]:
            if addmax == u"C面" :
                if re.search("1$",layer):
                    g.CLEAR_LAYER()
                    g.AFFECTED_LAYER(layer,"yes")
                    Mirr = 'no'
                    g.COM("add_text,attributes=no,type=barcode,x=%s,y=%s,text=%s,x_size=5.08,y_size=5.08,w_factor=2,polarity=positive,angle=0,mirror=%s,fontname=standard,bar_type=ECC-200,matrix=Minimal,bar_checksum=no,bar_background=no,bar_add_string=yes,bar_add_string_pos=top,bar_marks=no,bar_width=0.2032,bar_height=7,ver=1" % (x,y,strcode,Mirr))
                    datadic[layer]=[x, y]
            elif addmax == u"S面" :
                if re.search("2$",layer):
                    g.CLEAR_LAYER()
                    g.AFFECTED_LAYER(layer, "yes")
                    Mirr = 'yes'
                    x = float(x) + 7
                    g.COM("add_text,attributes=no,type=barcode,x=%s,y=%s,text=%s,x_size=5.08,y_size=5.08,w_factor=2,polarity=positive,angle=0,mirror=%s,fontname=standard,bar_type=ECC-200,matrix=Minimal,bar_checksum=no,bar_background=no,bar_add_string=yes,bar_add_string_pos=top,bar_marks=no,bar_width=0.2032,bar_height=7,ver=1" % (
                            x, y, strcode, Mirr))
                    datadic[layer] = [x, y]
            elif addmax == u"双面":
                g.CLEAR_LAYER()
                g.AFFECTED_LAYER(layer, "yes")
                Mirr = "no" if "1" in layer else "yes"
                x, y = getpointarr
                if Mirr == 'yes': x = float(x) + 7

                g.COM("add_text,attributes=no,type=barcode,x=%s,y=%s,text=%s,x_size=5.08,y_size=5.08,w_factor=2,polarity=positive,angle=0,mirror=%s,fontname=standard,bar_type=ECC-200,matrix=Minimal,bar_checksum=no,bar_background=no,bar_add_string=yes,bar_add_string_pos=top,bar_marks=no,bar_width=0.2032,bar_height=7,ver=1" % (
                        x, y, strcode, Mirr))
                datadic[layer] = [x, y]
        g.CLEAR_LAYER()
        return datadic













class GetInplanData(ChangeEWMBll):
    def __init__(self):
        self.DB_O = Oracle_DB.ORACLE_INIT()
        self.dbc_o = self.DB_O.DB_CONNECT(host='172.20.218.193', servername='inmind.fls', port='1521',
                                          username='GETDATA', passwd='InplanAdmin')
        if not self.dbc_o:
            msg_box = msgBox()
            msg_box.critical(self, u"错误", u"连接inplan数据库失败（218.193）！", QMessageBox.Yes)
            exit(0)
    def Getinplanzq(self,JOB):
        sql="""
        SELECT
            dc_type.value DC_TYPE,
            dc_side.value DC_SIDE 
        FROM
            VGT_HDI.rpt_job_list j,
            VGT_HDI.field_enum_translate dc_type,
            VGT_HDI.field_enum_translate dc_side 
        WHERE
            job_name = '{0}' 
            AND dc_type.enum = j.dc_type_ 
            AND dc_type.intname = 'JOB' 
            AND dc_type.fldname = 'DC_TYPE_' 
            AND dc_side.enum = j.dc_side_ 
            AND dc_side.intname = 'JOB' 
            AND dc_side.fldname = 'DC_SIDE_'
        
        """.format(JOB.upper()[:13])
        print sql
        data = self.DB_O.SELECT_DIC(self.dbc_o, sql)
        self.__del__()
        return data

    def __del__(self):
        # --关闭数据库连接
        if self.dbc_o:
            self.DB_O.DB_CLOSE(self.dbc_o)

 # def Mainrun(self,setzq,Old_or_new,NewCheck,ChangeCheck,addmx):
    #     """
    #     主程序
    #     :param setzq:
    #     :param Old_or_new:
    #     :param NewCheck:
    #     :param ChangeCheck:
    #     :return:
    #     """
    #     g.OPEN_STEP("set")
    #     g.CHANGE_UNITS("mm")
    #     # GetInplanZQ=GetInplanData().Getinplanzq(self.JOB)
    #     # if not GetInplanZQ:self.ErrorBox(u"获取inplan周期数据失败！")
    #
    #     strcode="D%s;VLVGT4;"%setzq
    #
    #     #strcode = "D2210;VLVGT4;"
    #     #旧方式创建更新symbol
    #     if Old_or_new == u"旧方式" and NewCheck:
    #         g.VOF()
    #         g.COM("delete_entity,job=a03708gn741a1,type=symbol,name=zq-ewm")
    #         g.VON()
    #         g.DELETE_LAYER("crsy_tmp")
    #         g.CREATE_LAYER("crsy_tmp", "drl")
    #         g.CLEAR_LAYER()
    #         g.AFFECTED_LAYER("crsy_tmp", "yes")
    #         g.COM("add_text,attributes=no,type=barcode,x=0,y=0,text=%s,x_size=5.08,y_size=5.08,w_factor=2,polarity=positive,angle=0,mirror=no,fontname=standard,bar_type=ECC-200,matrix=Minimal,bar_checksum=no,bar_background=no,bar_add_string=yes,bar_add_string_pos=top,bar_marks=no,bar_width=0.2032,bar_height=7,ver=1"%strcode)
    #         g.COM("sel_create_sym,symbol=zq-ewm,x_datum=0,y_datum=0,delete=no,fill_dx=2.54,fill_dy=2.54,attach_atr=no,retain_atr=no")
    #         g.DELETE_LAYER("crsy_tmp")
    #
    #     if NewCheck:##添加
    #         i = 0
    #         retdic={}
    #         while (i < 10):
    #             g.MOUSE("please select point")
    #             getpoint = g.MOUSEANS
    #             str1 = ''.join(getpoint)
    #             getpointarr = str1.split(' ')
    #             i += 1
    #
    #             if i >= 10:
    #                 self.ErrorBox(u"循环超过10次！程序退出")
    #             else:
    #                 retdic[i]=self.AddERMZQ(getpointarr,Old_or_new,strcode,addmx)
    #                 msg_box = msgBox()
    #                 resu=msg_box.question(self, u"提示", u"已添加第%s个二维码，是否继续添加?"%i, QMessageBox.Yes,QMessageBox.No)
    #                 if not resu == u"是": break
    #         msg_box = msgBox()
    #         msg_box.information(self, u"提示", u"添加完成请检查！" , QMessageBox.Yes)
    #         for index in retdic.keys():
    #             for layer in retdic[index].keys():
    #
    #                 g.WORK_LAYER(layer)
    #                 x1=float(retdic[index][layer][0])-10
    #                 y1=float(retdic[index][layer][1])+23
    #                 x2 = float(retdic[index][layer][0]) +10
    #                 y2 = float(retdic[index][layer][1]) - 23
    #                 g.COM("zoom_area,x1=%s,y1=%s,x2=%s,y2=%s"%(x1,y1,x2,y2))
    #                 g.PAUSE("Please Check")
    #         return
    #
    #     if ChangeCheck:##修改
    #         if Old_or_new == u"旧方式" :
    #             symboldic=g.DO_INFO("-t job -e %s -m script -d SYMBOLS_LIST"%self.JOB)
    #             pd=1
    #             ss=symboldic["gSYMBOLS_LIST"]
    #             for sym in symboldic["gSYMBOLS_LIST"]:
    #                 if re.search("zq-(2wm|ewm|wm)",sym):
    #                     g.COM("open_entity,job=%s,type=symbol,name=%s,iconic=no"%(self.JOB,sym))
    #                     g.AUX ("set_group,group="+g.COMANS)
    #                     g.COM("units,type=mm")
    #
    #                     g.COM("display_layer,name=%s,display=yes,number=1"%sym)
    #
    #                     g.COM("work_layer,name="+sym)
    #
    #                     g.FILTER_SELECT()
    #                     g.COM("sel_change_txt,text=D%s\;VLVGT4\;,x_size=-1,y_size=-1,w_factor=-1,polarity=no_change,mirror=no_change,fontname="%setzq)
    #                     g.COM("editor_page_close")
    #                     pd=2
    #
    #             if pd == 1 :
    #                 self.ErrorBox("set 里没有找到二维码，请确定symbol名字")
    #             else:
    #
    #                 pointlist=[]
    #                 layerpoint={}
    #                 zqLayer = self.GetZQBoardLayer()
    #                 for lay in zqLayer:
    #                     line = g.INFO("-t layer -e %s/set/%s -m display -d FEATURES" % (self.JOB, lay))
    #                     for lin in line:
    #                         if re.search("zq-(2wm|ewm|wm)", lin):
    #                             linelist = lin.strip().split(' ')
    #                             pointlist.append([linelist[1], linelist[2]])
    #                             layerpoint[lay] = pointlist
    #                 msg_box = msgBox()
    #                 msg_box.information(self, u"提示", u"修改完成请检查！", QMessageBox.Yes)
    #                 g.OPEN_STEP("set")
    #                 for k, v in layerpoint.items():
    #                     g.WORK_LAYER(k)
    #                     for point in v:
    #                         x1 = float(point[0]) - 10
    #                         y1 = float(point[1]) + 23
    #                         x2 = float(point[0]) + 10
    #                         y2 = float(point[1]) - 23
    #                         g.COM("zoom_area,x1=%s,y1=%s,x2=%s,y2=%s" % (x1, y1, x2, y2))
    #                         g.PAUSE("Please Check")
    #             return
    #         if Old_or_new == u"新方式":
    #             zqLayer=self.GetZQBoardLayer()
    #             pointlist=[]
    #             layerpoint={}
    #             for lay in zqLayer:
    #                 line = g.INFO("-t layer -e %s/set/%s -m display -d FEATURES" % (self.JOB,lay))
    #                 for lin in line:
    #                     if re.search("(barcode|#B|VLVGT4)",lin):
    #                         linelist= lin.strip().split(' ')
    #                         pointlist.append([linelist[1],linelist[2]])
    #                         layerpoint[lay]=pointlist
    #                 if not layerpoint :  self.ErrorBox("set 里没有找到二维码，请确定symbol名字")
    #             for k,v in layerpoint.items():
    #                 g.CLEAR_LAYER()
    #                 g.AFFECTED_LAYER(k,"yes")
    #                 for point in v:
    #
    #                     g.COM("sel_single_feat,operation=select,x=%s,y=%s,tol=367.47,cyclic=no" % (point[0],point[1]))
    #                     aa=g.GET_SELECT_COUNT()
    #                     if g.GET_SELECT_COUNT()>0:
    #                         g.COM("sel_change_txt,text=D%s\;VLVGT4\;,x_size=-25.4,y_size=-25.4,w_factor=-1,polarity=no_change,mirror=no_change,fontname="%setzq)
    #                 g.CLEAR_LAYER()
    #             msg_box = msgBox()
    #             msg_box.information(self, u"提示", u"修改完成请检查！", QMessageBox.Yes)
    #             for k,v in layerpoint.items():
    #                 g.WORK_LAYER(k)
    #                 for point in v:
    #                     x1 = float(point[0]) - 10
    #                     y1 = float(point[1]) + 23
    #                     x2 = float(point[0]) + 10
    #                     y2 = float(point[1]) - 23
    #                     g.COM("zoom_area,x1=%s,y1=%s,x2=%s,y2=%s" % (x1, y1, x2, y2))
    #                     g.PAUSE("Please Check")
    #             return
