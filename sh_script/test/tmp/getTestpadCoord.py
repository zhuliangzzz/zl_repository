#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --------------------------------------------------------- #
#                VTG.SH SOFTWARE GROUP                      #
# --------------------------------------------------------- #
# @Author       :    LiuChuang
# @Mail         :    Chuang_cs@163.com
# @Date         :    2021/09/23
# @Revision     :    1.7.0
# @File         :    getTestpadCoord.py
# @Software     :    PyCharm
# @Usefor       :    用于获取六处Panel板边的测试Pad，以供X-RAY设备打靶测量涨缩用
# @PRD link     :    http://192.168.2.120:82/zentao/story-view-3540.html
# --------------------------------------------------------- #
# region
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
# endregion

import math
import os
import platform
import sys

if platform.system() == "Windows":
    if os.environ.get('USERNAME') == '477723':
        sys.path.insert(0, "D:/genesis/sys/scripts/Package")
    else:
        sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package")
else:
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")

import genCOM_26 as genCOM
import gClasses

from get_erp_job_info import get_mysql_target_info
from genesisPackages import innersignalLayers, signalLayers
from create_ui_model import showMessageInfo, app

from create_xact_layer_info_xml import xact_layer_xml
xml_main = xact_layer_xml()

# --此环境变量在hooks下的scripts_start.csh配置中有定义
# sys.path.append(r"%s/sys/scripts/Package" % os.environ.get('SCRIPTS_DIR'))
# import genCOM_26 as genCOM

# from mwClass_V2 import showMsg


class Main:
    def __init__(self):
        self.GEN = genCOM.GEN_COM()
        self.JOB = os.environ.get('JOB')
        self.STEP = os.environ.get('STEP')
        self.tmpLay = '-++coortmp++-'
        
        job = gClasses.Job(self.JOB)
        self.step = gClasses.Step(job, self.STEP)        
        
        # if self.GEN.getEnv()['system'] == 'linux':
        ##template默认为yes，当传参数时，接收参数值
        ##选择template时输出路径为料号名文件夹，选择Twopin时，输出路径为料号名-tuopin文件夹，单独时，按料号名文件夹
        self.template = 'yes'
        if len(sys.argv) == 2:
            self.template = sys.argv[1]

        if self.template == 'yes':
            if self.GEN.getEnv()['system'] == 'Linux':
                self.outputPath = os.path.abspath('/id/workfile/film/%s' % self.JOB)
            else:
                self.outputPath = os.path.abspath('D:\\disk\\film\\' + self.JOB)
        else:
            if self.GEN.getEnv()['system'] == 'Linux':
                self.outputPath = os.path.abspath('/id/workfile/film/%s-tuopin' % self.JOB)
            else:
                self.outputPath = os.path.abspath('D:\\disk\\film\\' + self.JOB+'-tuopin')


        self.center_x = None
        self.center_y = None
        #self.allMarkCoord = {}
        #self.writeLog = {}
        try:
            self.layCount = int(self.JOB[4:6])
        except:
            # showMsg(u'从型号第五第六位无法获取层数，程序中止！')
            showMessageInfo(u'从型号第五第六位无法获取层数，程序中止！')
            sys.exit(1)

        # --旧的工具文件存在，直接删除
        if not os.path.exists(self.outputPath):
            os.mkdir(self.outputPath)
        else:
            if os.path.exists(os.path.join(self.outputPath, self.JOB + '.i2x')):
                os.unlink(os.path.join(self.outputPath, self.JOB + '.i2x'))

    # def __del__(self):
        #if "-lyh" in self.JOB:
            #self.GEN.PAUSE("333")        
        #self.GEN.FILTER_RESET()
        #self.GEN.DELETE_LAYER(self.tmpLay)
        #if "-lyh" in self.JOB:
            #self.GEN.PAUSE("444")           

    def DoMain(self):
        """
        执行的主入口
        :return: None
        """
        # --重新打开STEP，并还原设置
        self.GEN.OPEN_STEP(self.STEP, self.JOB)
        self.GEN.CLEAR_LAYER()
        self.GEN.CHANGE_UNITS('mm')

        mrp_info = get_mysql_target_info(self.JOB)
        
        for dic_info in mrp_info:
            self.allMarkCoord = {}
            self.writeLog = {}            
            top_layer = dic_info["FROMLAY"]
            bot_layer = dic_info["TOLAY"]
            mrp_name = dic_info["MRPNAME"]
            
            # --创建外围线；
            self.createProfileLine()
    
            # --copy测试图形至其它层（取其一层l2层）
            if not self.copy_testMark_1(top_layer.lower(), bot_layer.lower()):
                return False
    
            # --以profile中心旋转
            self.rotateTmpLayer()
    
            # --获取对应mark的坐标
            self.getMarkCoord()
    
            # --写头部的固定数据
            self.f = open(os.path.join(self.outputPath, mrp_name + '.ix'), 'w')
    
            # --根据板层数，算出各组匹配的坐标（及测试pad的相对坐标）
            if not self.calTestCoord():
                self.GEN.LOG(u'工具输出失败...')
                self.f.close()
                os.unlink(os.path.join(self.outputPath, mrp_name + '.ix'))
            else:
                self.f.close()        
        
        # if "-lyh" in self.JOB:
        self.GEN.DELETE_LAYER(self.tmpLay)
        # try:
            # if "-lyh" in self.JOB:
        xml_main.create_ui_params()
        xml_main.show()
        sys.exit(app.exec_())                
            # else:
            # res = os.system("python {0}/create_xact_layer_info_xml.py".format(os.path.dirname(sys.argv[0])))
          
            #if "-lyh" in self.JOB:
                #showMessageInfo(u'输出完成，资料存放路径:{0}'.format(self.outputPath))
            # exit(0)
        #except Exception as e:
            #print("------------>1111", e)
        
    def createProfileLine(self):
        """
        按profile线创建外围线，以供中心旋转参与
        :return: None
        """
        self.GEN.DELETE_LAYER(self.tmpLay)
        self.GEN.CREATE_LAYER(self.tmpLay)
        self.GEN.COM("profile_to_rout,layer=%s,width=10.1" % self.tmpLay)

    def copy_testMark_1(self, top_layer, bot_layer):
        """
        copy测试图形至其它层（取其一层l2层）
        :return:
        """
        step = self.step
        step.open()
        step.COM("units,type=mm")
        step.clearAll()
        index1 = signalLayers.index(top_layer)
        index2 = signalLayers.index(bot_layer)
        num = 0
        for i, layer in enumerate(innersignalLayers):
            index = signalLayers.index(layer)
            if index2 > index > index1:
                step.clearAll()
                step.affect(layer)
                num += 1
                step.resetFilter()
                step.setSymbolFilter("measure_l*;measure_fd_l*")
                step.selectAll()
                if step.featureSelected():
                    step.removeLayer(layer+"_tmp_symbol")
                    step.copySel(layer+"_tmp_symbol")                    
                    step.clearAll()
                    step.affect(layer+"_tmp_symbol")
                    step.resetFilter()
                    step.selectAll()
                    step.COM("sel_break_level,attr_mode=merge")
                    
                    step.resetFilter()
                    step.filter_set(feat_types='pad', polarity='positive')
                    if num > 1:
                        step.selectSymbol("r1524")                        
                    else:
                        step.selectSymbol("r2000;r2500;r1524")

                    if step.featureSelected():
                        step.copySel(self.tmpLay)
                    else:
                        self.GEN.LOG(u'symbol获取异常...')
                        return False
                else:
                    self.GEN.LOG(u'symbol获取异常...')
                    return False                    

        return True

    def delUnusePad(self, tmpLayer):
        """
        删除无用的pad（取出两颗挨得最近的孔，并删除左边的一个，即X坐标小的那个）
        :return: None
        """
        self.GEN.SEL_COPY(tmpLayer)
        fx_info = self.GEN.INFO('-t layer -e %s/%s/%s -m script -d FEATURES -o break_sr'
                                % (self.JOB, self.STEP, tmpLayer))
        # --初始化最小坐标为取出的profile的最大值
        min_x, min_y = self.GEN.GET_PROFILE_SIZE(self.JOB, self.STEP)
        maxLen = math.sqrt(min_x ** 2 + min_y ** 2)
        # --循环所有坐标，取出左下角非防呆坐标（算法：距离原点最近的直线距离的孔，三角函数）
        for markinfo in fx_info:
            splitList = markinfo.split(' ')
            # --当为Pad时
            if splitList[0] == '#P':
                coorLen = math.sqrt(float(splitList[1]) ** 2 + float(splitList[2]) ** 2)
                if coorLen < maxLen:
                    maxLen = coorLen
                    # --定义最短距离时的坐标
                    min_x = splitList[1]
                    min_y = splitList[2]
                pass

        # --删除左下角非防呆的图形
        self.GEN.WORK_LAYER(tmpLayer)
        self.GEN.COM('sel_single_feat,operation=select,x=%s,y=%s,tol=2331.1775,cyclic=yes' % (min_x, min_y))
        if self.GEN.GET_SELECT_COUNT() > 0:
            self.GEN.SEL_DELETE()

        # --返回
        return True

    def rotateTmpLayer(self):
        """
        旋转临时层
        :return: True or False
        """
        self.pnl_x, self.pnl_y = self.GEN.GET_PROFILE_SIZE(self.JOB, self.STEP)
        self.center_x = float(self.pnl_x) / 2
        self.center_y = float(self.pnl_y) / 2
        # --逆时针旋转90度
        self.GEN.WORK_LAYER(self.tmpLay)
        self.GEN.COM('sel_transform,mode=anchor,oper=rotate,duplicate=no,x_anchor=%s,y_anchor=%s,angle=270,'
                     'x_scale=1,y_scale=1,x_offset=0,y_offset=0' % (self.center_x, self.center_y))

    def getMarkCoord(self):
        """
        获取对应mark的坐标
        :return: None
        """
        step = self.step
        step.open()
        step.COM("units,type=mm")
        
        layer_cmd = gClasses.Layer(step, self.tmpLay)
        feat_out = layer_cmd.featOut(units="mm")["pads"]
        
        for obj in feat_out:
            mark_x = float(obj.x) - self.center_x
            mark_y = float(obj.y) - self.center_y
            symbol = obj.symbol
            if symbol not in self.allMarkCoord.keys():
                self.allMarkCoord[symbol] = []
            self.allMarkCoord[symbol].append((mark_x, mark_y, getattr(obj, "string", "")))
            
        #self.GEN.WORK_LAYER(self.tmpLay)
        ## --删掉外围线-其实删不删都没什么影响
        #self.GEN.FILTER_SET_INCLUDE_SYMS('r10.1')
        #if self.GEN.GET_SELECT_COUNT() > 0:
            #self.GEN.SEL_DELETE()
        ## --获取四个参考图形的坐标 rect3540x5340 ，用于推算出其它几个测试pad的坐标
        ##self.GEN.FILTER_SET_INCLUDE_SYMS('rect3540x5340', reset=1)
        ##self.GEN.FILTER_SELECT()
        ## region # --打散后的数据坐标
        #selInfo = self.GEN.INFO('-t layer -e %s/%s/%s -m script -d FEATURES -o break_sr'
                                #% (self.JOB, self.STEP, self.tmpLay))
        ## endregion
        #for markinfo in selInfo:
            #splitList = markinfo.split(' ')
            ## --当为Pad时
            #if splitList[0] == '#P':
                ## --转换以中心点为相对原点
                #mark_x = float(splitList[1]) - self.center_x
                #mark_y = float(splitList[2]) - self.center_y
                #symbol = splitList[3]
                #if symbol not in self.allMarkCoord.keys():
                    #self.allMarkCoord[symbol] = []
                #self.allMarkCoord[symbol].append((mark_x, mark_y))

        # --循环存储的数据结构样式
        # a = {'rect5340x3540': [('433.36', '65.661375'), ('-21.36', '65.661375'), ('433.36', '402.338625')],
        #      's2540': [('434.76', '68.901375'), ('434.76', '71.641375'), ('434.76', '74.381375')]}
        self.GEN.LOG(self.allMarkCoord)
        # self.GEN.PAUSE(str(self.allMarkCoord))

    def calTestCoord(self):
        """
        计算出所有测试图形有相对坐标（注意方位）
        :return: None
        """
        self.twoInnGF5 = []
        self.twoInnGF6 = []
        # --取出L靶中的中间两靶（即两个Y值一样），用于计算各角孔相对于它的位置
        #for symbol in self.allMarkCoord.keys():
            ## --inn层的L靶标
            #if symbol == 'r3125':
                #for innMark in self.allMarkCoord[symbol]:
                    #OF_X = float(innMark[0])
                    #OF_Y = float(innMark[1])
                    #for loop in self.allMarkCoord[symbol]:
                        #ofx = float(loop[0])
                        #ofy = float(loop[1])
                        #if OF_X == ofx and OF_Y == ofy:
                            #continue
                        #if OF_X != ofx and OF_Y == ofy:
                            #self.twoInnGF5 = [OF_X, OF_Y]
                            #self.twoInnGF6 = [ofx, ofy]
                            #self.GEN.LOG(u"part0:存储L靶位孔中心线上的两个孔")
                #break

        ## --分出左右
        #if len(self.twoInnGF5) == len(self.twoInnGF6) == 2:
            #if self.twoInnGF5[0] > self.twoInnGF6[1]:
                #tmpList = []
                #tmpList = self.twoInnGF5
                #self.twoInnGF5 = self.twoInnGF6
                #self.twoInnGF6 = tmpList
            #else:
                #pass
        #else:
            #self.GEN.LOG(u"无法获取Inn层中的两个夹Pin孔...")

        # --四次循环，写各层的测试pad数据
        for symbol in self.allMarkCoord.keys():
            if symbol == 'r2500':
                for oneMark in self.allMarkCoord[symbol]:
                    OF_X = float(oneMark[0])
                    OF_Y = float(oneMark[1])
                    # --判断对应mark的方向-旋转后的方向左上-OF11、右上OF12、左下OF21、右下OF22
                    if OF_X < 0 and OF_Y > 0:
                        self.writeLog['part1'] = True
                        # --写头部数据
                        self.writeHead(abs(OF_X))

                        self.GEN.LOG("OF11 X %s Y %s SIZE 2.5" % (OF_X, OF_Y))
                        self.f.write("OF11 X %s Y %s SIZE 2.5\n" % (OF_X, OF_Y))
                        self.getlayMarkCoord('OF11', OF_X, OF_Y)
                        self.GEN.LOG(u"part1：左上：OF11")
                        self.GEN.LOG(u"part1:第一次循环...")

                        # --追加距离夹pin孔的数据 SF5 DX 1.07 DY-196.692 SIZE 2.0 （这里都-0.1是工艺要求的：“DY值短边数据是测不了的，机台系统就会默认为0，这样就会导致测量板后数据导不出来，系统会报异常”
                        # @formatter:off
                        #try:
                            #self.f.write("SF%s DX %s DY %s SIZE 2.0\n" % ((self.layCount-1), (self.twoInnGF5[0]-OF_X), (self.twoInnGF5[1]-OF_Y+0.1)))
                        #except IndexError:
                            #showMsg(u'超范围，文件可能不完整，请检查输出文件！并请确认是否是三靶定位后重新输出！')

                        # @formatter:on
                        break
                break

        for symbol in self.allMarkCoord.keys():
            if symbol == 'r2000':
                for oneMark in self.allMarkCoord[symbol]:
                    OF_X = float(oneMark[0])
                    OF_Y = float(oneMark[1])
                    if OF_X > 0 and OF_Y > 0:
                        self.writeLog['part2'] = True
                        self.GEN.LOG("OF12 X %s Y %s SIZE 2.0" % (OF_X, OF_Y))
                        self.f.write("\nOF12 X %s Y %s SIZE 2.0\n" % (OF_X, OF_Y))
                        self.getlayMarkCoord('OF12', OF_X, OF_Y)
                        self.GEN.LOG(u"part2：右上：OF12")
                        self.GEN.LOG(u"part2:第二次循环...")
                        # @formatter:off
                        # self.f.write("SF%s DX %s DY %s SIZE 2.0\n" % ((self.layCount-1), (self.twoInnGF6[0]-OF_X), (self.twoInnGF6[1]-OF_Y+0.1)))
                        # @formatter:on
                break

        for symbol in self.allMarkCoord.keys():
            if symbol == 'r2500':
                for oneMark in self.allMarkCoord[symbol]:
                    OF_X = float(oneMark[0])
                    OF_Y = float(oneMark[1])
                    if OF_X < 0 and OF_Y < 0:
                        self.writeLog['part3'] = True
                        self.GEN.LOG("OF21 X %s Y %s SIZE 2.5" % (OF_X, OF_Y))
                        self.f.write("\nOF21 X %s Y %s SIZE 2.5\n" % (OF_X, OF_Y))
                        self.getlayMarkCoord('OF21', OF_X, OF_Y)
                        self.GEN.LOG(u"part3：左下：OF21")
                        self.GEN.LOG(u"part3:第三次循环...")

                        # --追加距离夹pin孔的数据 SF5 DX 1.07 DY-196.692 SIZE 2.0
                        # @formatter:off
                        # self.f.write("SF%s DX %s DY %s SIZE 2.0\n" % ((self.layCount-1), (self.twoInnGF5[0]-OF_X), (self.twoInnGF5[1]-OF_Y-0.1)))
                        # @formatter:on
                break

        for symbol in self.allMarkCoord.keys():
            if symbol == 'r2500':
                for oneMark in self.allMarkCoord[symbol]:
                    OF_X = float(oneMark[0])
                    OF_Y = float(oneMark[1])
                    if OF_X > 0 and OF_Y < 0:
                        self.writeLog['part4'] = True
                        self.GEN.LOG("OF22 X %s Y %s SIZE 2.5" % (OF_X, OF_Y))
                        self.f.write("\nOF22 X %s Y %s SIZE 2.5\n" % (OF_X, OF_Y))
                        self.getlayMarkCoord('OF22', OF_X, OF_Y)
                        self.GEN.LOG(u"part4：右下：OF22")
                        self.GEN.LOG(u"part4:第四次循环...")
                        # @formatter:off
                        # self.f.write("SF%s DX %s DY %s SIZE 2.0\n" % ((self.layCount-1), (self.twoInnGF6[0]-OF_X), (self.twoInnGF6[1]-OF_Y-0.1)))
                        # @formatter:on
                break

        # --第五次循环写入外层四个CCD对位用的靶标孔
        #for symbol in self.allMarkCoord.keys():
            ## --inn层的L靶标
            #if symbol in ('sh-baccd', 's4429', 'r3150', 's3683'):
                #self.f.write("\n")
                #for innMark in self.allMarkCoord[symbol]:
                    #GF_Num = self.allMarkCoord[symbol].index(innMark) + 1
                    #OF_X = float(innMark[0])
                    #OF_Y = float(innMark[1])
                    #self.writeLog['part5'] = True
                    #self.f.write("//GF%d X%s	Y%s SIZE 2.8\n" % (GF_Num, OF_X, OF_Y))
                    #self.GEN.LOG(u"part5:第五次循环写入外层四个CCD对位用的靶标孔")
                #break

        ## --循环写入外层四个T对位用的靶标孔 http://192.168.2.120:82/zentao/story-view-5028.html  20231116 钟利东
        #for symbol in self.allMarkCoord.keys():
            ## --inn层的L靶标
            #if symbol in ('sh-baa-sh6-t'):
                #self.f.write("\n")
                #for innMark in self.allMarkCoord[symbol]:
                    #GF_Num = self.allMarkCoord[symbol].index(innMark) + 1
                    #OF_X = float(innMark[0])
                    #OF_Y = float(innMark[1])
                    #self.writeLog['part5'] = True
                    #self.f.write("//TF%d X%s	Y%s SIZE 2.0\n" % (GF_Num, OF_X, OF_Y))
                    #self.GEN.LOG(u"part5:第五次循环写入外层四个T对位用的靶标孔")
                #break

        ## --第六次循环写入L靶位孔
        #for symbol in self.allMarkCoord.keys():
            ## --inn层的L靶标
            #if symbol == 'r3125':
                #self.f.write("\nT1 D3.175\n//DOP GF\n//DOP TF\n\n//OPD\n")
                #for innMark in self.allMarkCoord[symbol]:
                    #OF_X = float(innMark[0])
                    #OF_Y = float(innMark[1])
                    #self.writeLog['part6'] = True
                    #self.f.write("//X %s Y %s\n" % (OF_X, OF_Y))
                    #self.GEN.LOG(u"part6:第六次循环写入L靶位孔")
                #break

        ## --第七次循环写入L靶位孔中心线上的两个孔（即两个Y值一样）
        #if len(self.twoInnGF5) == len(self.twoInnGF6) == 2:
            #self.f.write("\nGF5 X %s Y %s SIZE 2.0\n" % (self.twoInnGF5[0], self.twoInnGF5[1]))
            #self.f.write("GF6 X %s Y %s SIZE 2.0\n" % (self.twoInnGF6[0], self.twoInnGF6[1]))
            #self.writeLog['part7'] = True
            #self.GEN.LOG(u"part7:第七部分写入L靶位孔")
        ## for symbol in self.allMarkCoord.keys():
        ##     # --inn层的L靶标
        ##     if symbol == 'r3125':
        ##         for innMark in self.allMarkCoord[symbol]:
        ##             OF_X = float(innMark[0])
        ##             OF_Y = float(innMark[1])
        ##             for loop in self.allMarkCoord[symbol]:
        ##                 ofx = float(loop[0])
        ##                 ofy = float(loop[1])
        ##                 if OF_X == ofx and OF_Y == ofy:
        ##                     continue
        ##                 if OF_X != ofx and OF_Y == ofy:
        ##                     self.f.write("\nGF5 X %s Y %s SIZE 2.0\n" % (OF_X, OF_Y))
        ##                     self.f.write("GF6 X %s Y %s SIZE 2.0\n" % (ofx, ofy))
        ##                     self.GEN.LOG(u"part7:第七次循环写入L靶位中轴线的孔")
        ##                     break

        ## --第八次循环写入线补偿 DREF GF5,GF6
        #for symbol in self.allMarkCoord.keys():
            ## --inn层的L靶标
            #if symbol == 'r3125':
                #self.f.write("\nDREF GF5,GF6\n")
                #for innMark in self.allMarkCoord[symbol]:
                    #OF_X = float(innMark[0])
                    #OF_Y = float(innMark[1])
                    #self.f.write("X %s Y %s\n" % (OF_X, OF_Y))
                    #self.GEN.LOG(u"part8:第八次循环写入L靶位孔")
                #break

        # --返回是否有完整的写完
        #if 'part1' in self.writeLog.keys() and 'part2' in self.writeLog.keys() and 'part3' in self.writeLog.keys() \
                #and 'part4' in self.writeLog.keys() and 'part5' in self.writeLog.keys() and 'part6' in self.writeLog.keys():
            #return True
        #else:
            #return False
        return True

    def getlayMarkCoord(self, OF_type, OF_X, OF_Y):
        """
        计算所有层标的坐标
        :param OF_type: OF11 OF12 OF21 OF22
        :return: None
        """        
        for symbol in self.allMarkCoord.keys():
            if symbol == 'r1524':
                num = 0
                for oneMark in sorted(self.allMarkCoord[symbol], key= lambda x: x[2]):
                    SF_X = float(oneMark[0])
                    SF_Y = float(oneMark[1])
                    if OF_type == "OF11":
                        if SF_X < 0 and SF_Y > 0:
                            num += 1
                            dx = SF_X - OF_X
                            dy = SF_Y - OF_Y
                            self.f.write("SF%s DX %s DY %s\n" % (num, dx, dy))
                            self.GEN.LOG("SF%s DX %s DY %s" % (num, dx, dy))
                            
                    if OF_type == "OF12":
                        if SF_X > 0 and SF_Y > 0:
                            num += 1
                            dx = SF_X - OF_X
                            dy = SF_Y - OF_Y
                            self.f.write("SF%s DX %s DY %s\n" % (num, dx, dy))
                            self.GEN.LOG("SF%s DX %s DY %s" % (num, dx, dy))
                            
                    if OF_type == "OF21":
                        if SF_X < 0 and SF_Y < 0:
                            num += 1
                            dx = SF_X - OF_X
                            dy = SF_Y - OF_Y
                            self.f.write("SF%s DX %s DY %s\n" % (num, dx, dy))
                            self.GEN.LOG("SF%s DX %s DY %s" % (num, dx, dy))
                            
                    if OF_type == "OF22":
                        if SF_X > 0 and SF_Y < 0:
                            num += 1
                            dx = SF_X - OF_X
                            dy = SF_Y - OF_Y
                            self.f.write("SF%s DX %s DY %s\n" % (num, dx, dy))
                            self.GEN.LOG("SF%s DX %s DY %s" % (num, dx, dy))                                    
                        
        #if OF_type in ("OF11", "OF12"):
            #for num in range(2, self.layCount):
                #if num % 2 == 0:
                    #dx = -1.4
                #else:
                    #dx = 1.4
                #dy = (2.74 * int((self.layCount - (num + 1)) / 2) + 3.24) * -1
                #self.f.write("SF%s DX %s DY %s\n" % (num - 1, dx, dy))
                #self.GEN.LOG("SF%s DX %s DY %s" % (num - 1, dx, dy))
        #elif OF_type in ("OF21", "OF22"):
            #for num in range(2, self.layCount):
                #if num % 2 == 0:
                    #dx = -1.4
                #else:
                    #dx = 1.4
                #dy = 2.74 * int((num - 2) / 2) + 3.24
                #self.f.write("SF%s DX %s DY %s\n" % (num - 1, dx, dy))
                #self.GEN.LOG("SF%s DX %s DY %s" % (num - 1, dx, dy))

    def writeHead(self, of11_x):
        """
        写固定的文件头部信息
        TODO：TCL部分需要重新定义，待出内联单更新（改为板边打码位置，用于分批码钻孔）
        :param of11_x: of11_x
        :return:
        """
        headText = """// X-Rays
KVOLT 85

// Vision
CONTR 255
BRIGH 50
CCDFR 1
INTFR 2

//Pads
SHAPE    CIRC
SIZE     1.5
SMODE    3
PTPTOL   0.200
DISTOL   0.200
GLBTOL   0.200
SFDISTOL  0.15
LBOFS %s,%s
//END SECTION HEADER

// PROGRAM
""" % (float(self.pnl_y) / 2 - float(of11_x) if float(self.pnl_y) / 2 < float(of11_x) else float(of11_x) - float(self.pnl_y) / 2,
       float(self.pnl_x) / 2 - 160)
        self.f.write(headText)


if __name__ == '__main__':     
    M = Main()
    M.DoMain()


    # succeedMes = """<div style="background-color:rgb(133,205,0);">
    #                 <span style="color:white;font-size:16px"><strong>%s<strong></span>
    #                 </div>""" % (u'资料成功输出')
    # showMsg(succeedMes)

"""
__END__:
日期  ：20240307
更新人：lyh
版本  ：V1.1.0 
更新内容：
1.参考多层 开发HDI的输出模式
"""
