#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:fpcRunIncamSM-0106.py
   @author:zl
   @time:2022/01/05 10:24
   @software:PyCharm
   @desc:自动制作蚀刻定义的PAD开窗的脚本
"""
# 线路振粗整体 +1.6
# 小开窗red单边: 0.6
# 小开窗jt单边: 0.8

# 20201112 s20-2677aisx-sm donut_r52.781x25.959 开小窗
# 20201123 hmx 修改制作方式
# 20201125 hmx 修复开小窗问题
# 20201207 hmx 加入创建nsmd层
# 20210716 YLC 王芳飞:s21-1858a 跑出来有细丝，原因补偿太大
import sys, os, re, time, datetime, pymysql

# sys.path.append('/genesis/sys/scripts/py/lib/hmxlib')
import genClasses
import os, sys, re
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *


class CamApp(QWidget):
    def __init__(self):
        super().__init__()
        # self.desktop_width = QApplication.desktop().width()  # 屏幕尺寸
        # self.desktop_height = QApplication.desktop().height()
        self.resize(400, 630)
        # self.move((self.desktop_width - self.width()) / 2, (self.desktop_height - self.height()) / 2)  # 将窗口放在屏幕中间
        self.setWindowFlags(Qt.WindowStaysOnTopHint)  # 置顶
        self.DoGui()  # 界面

    def DoApp(self):
        """开始"""

        # self.DoCheckSurfaceSmd()
        self.hide()
        # self.test()

        self.DoStart()  # 初始变量;备份层;创建临时层t1,t2,t3,t4,t5

        #   sys.exit()
        self.DoAddPad()  # 定孔属性
        self.DoCheckNegativeSmdAndBga()  # 检测是否存在负性smd ,bga
        self.DoSignalRemoval()  # 删重pad smd合并,去属性
        self.DoRemoveClearance()  # 删除所有开窗
        self.DoShareCoverage()  # 削SMD盖线,桥

        self.DoRemoveInSmd()  # 删除SMD中的小PAD,小线  s20-2592a c面一处smd中心里有一根粗线导致该smd开小窗,删掉泪滴

        self.DoShrinkAll()  # 除smd,bga以外的物件-0.5  相应盖线+0.5

        self.DoSmdRunClearance()  # 制作smd开窗
        # s.PAUSE('1')
        self.DoSmdRunClearance_add()  # 制作smd开窗,解决小开窗的情况
        self.DoAddSmallSmd()  # 加上smd小开窗
        # s.PAUSE('2')

        # sys.exit()
        self.DoSmdMoveBackCover()  # 移回盖线
        #
        self.DoSmdEnd()  # 保存跑好的smd
        # s.PAUSE('end')
        self.DoBgaRunClearance()  # 制作bga开窗
        self.DoGoBackSignal()  # 还原线路层
        self.DoSmdAndBgaJoin()  # 将跑好的bga,smd开窗合并
        self.DoCheckLineClearance()  # 检测连线未开小窗
        # s.PAUSE('end')
        self.DoAddNpthClearance()  # 无铜孔加开窗
        self.DoEnd()  # 收尾删除临时层
        """结束"""
        ##检测负性smd,bga 有无smd
        self.DoReturnDrill()  # 返回修改前的孔层
        # job.COM(
        #     "script_run,name=/genesis/sys/scripts/hmx/python/camCreatensmdLay.py,dirmode=global,params=,env1=JOB=%s,env2=STEP=%s" % (
        #         job_name, step_name))

        QMessageBox.information(self, "ok", 'ok,已完成!', QMessageBox.Ok)
        sys.exit()

    # def DoCheckSurfaceSmd(self):
    #     # 铜皮smd转pad
    #     s.clearAll()
    #     s.clearAndReset()
    #     if setValue["runSmdLayerList"]:
    #         for lay in setValue["runSmdLayerList"]:
    #             s.affect(lay)
    #         s.setAttrFilter('.smd')
    #         s.setTypeFilter('surface')
    #         s.selectSymbol()
    #         s.resetFilter()
    #         if s.Selected_count():
    #             button = QMessageBox.question(self, "Question", "注意,检测到有Surface的SMD,将不会做大开窗,继续执行？",
    #                                           QMessageBox.Ok | QMessageBox.Cancel, QMessageBox.Ok)
    #             if button == QMessageBox.Cancel:
    #                 sys.exit()
    #     s.clearAll()

    def test(self):
        """手动做防焊,测试"""
        s.clearAll()
        s.clearAndReset()
        s.setUnits('mm')
        s.VOF()
        s.removeLayer('sm_123')
        s.removeLayer('sig_123')
        s.removeLayer('tmp_123')
        s.removeLayer('sig_tmp_123')
        s.removeLayer('sm_tmp_123')
        s.removeLayer('smd_arc')
        s.VON()
        s.createLayer('sm_123')
        s.createLayer('sig_123')
        s.createLayer('tmp_123')
        s.createLayer('sig_tmp_123')
        s.createLayer('sm_tmp_123')
        s.createLayer('smd_arc')

        s.truncate_layer('sm')
        s.affect('ss')
        s.setAttrFilter('.smd')
        s.selectSymbol()
        s.resetFilter()
        s.copyToLayer('sm', size=101.6)
        s.clearAll()
        # 1
        s.affect('ss')
        s.setAttrFilter('.smd')
        s.selectSymbol()
        s.resetFilter()
        s.copyToLayer('sm_123', size=101.6)
        s.clearAll()
        # 2
        s.copyLayer(job_name, step_name, 'ss', 'sig_123')
        # 3
        s.srFill('tmp_123')
        # s.PAUSE('1')
        # 4
        s.copyLayer(job_name, step_name, 'sm_123', 'tmp_123', 'append', 'yes')
        # 5
        s.affect('tmp_123')
        s.Contourize(0.25, 'yes', 3)
        s.clearAll()
        # 6
        s.copyLayer(job_name, step_name, 'tmp_123', 'sig_123', 'append', 'yes')

        # 7
        s.affect('sig_123')
        s.Contourize(0.25, 'yes', 3)
        s.clearAll()
        # 8
        s.affect('sig_123')
        s.resize(50.8)
        s.clearAll()
        # 9
        s.copyLayer(job_name, step_name, 'tmp_123', 'sig_123', 'append', 'yes')
        # 10
        s.affect('sig_123')
        s.Contourize(0.25, 'yes', 3)
        s.clearAll()
        # 11
        s.copyLayer(job_name, step_name, 'sig_123', 'sig_tmp_123')
        # 12
        s.affect('sig_tmp_123')
        s.selectFill(38.1)
        s.clearAll()

        # 13
        s.affect('sig_123')
        s.Contourize(0.25, 'yes', 3)
        s.COM('sel_feat2outline,width=2.57')
        s.clearAll()

        # 14
        s.affect('sig_123')
        s.refSelectFilter('sig_tmp_123', mode='disjoint')
        if s.Selected_count():
            s.selectDelete()
        s.clearAll()
        # 15
        s.affect('sig_123')
        s.selectChange('r63.5')
        s.clearAll()
        # 16
        s.copyLayer(job_name, step_name, 'sm_123', 'sm_tmp_123')
        # 17
        s.affect('sm_tmp_123')
        s.Contourize(0.25, 'yes', 3)
        s.clearAll()
        # 18
        s.affect('sm_tmp_123')
        s.Contourize(0.25, 'yes', 3)
        s.COM('sel_feat2outline,width=80')
        s.Contourize(0.25, 'yes', 3)
        s.clearAll()
        # 19
        s.affect('sig_123')
        s.refSelectFilter('sm_tmp_123', mode='cover')
        if s.Selected_count():
            s.copyToLayer('smd_arc')
        s.clearAll()
        sys.exit()

    def DoReturnDrill(self):
        # 返回修改前的孔层
        for layName in self.drillList:
            bflay = layName + '_bf1'
            s.copyLayer(job_name, step_name, bflay, layName)
            s.removeLayer(bflay)

    def DoRemoveInSmd(self):
        """ 删除SMD中的小PAD,小线  s20-2592a c面一处smd中心里有一根粗线导致该smd开小窗"""
        s.COM("truncate_layer,layer=tmp1")
        s.COM("truncate_layer,layer=tmp2")
        s.COM("truncate_layer,layer=tmp3")
        s.COM("truncate_layer,layer=tmp4")
        s.COM("truncate_layer,layer=tmp5")
        s.clearAll()
        s.clearAndReset()
        # 删泪滴
        for lay in setValue["runSmdLayerList"]:
            s.affect(lay)
            s.setAttrFilter('.tear_drop')
            s.selectSymbol()
            s.resetFilter()
            if s.Selected_count() > 0:
                s.selectDelete()
            s.clearAll()
        s.clearAll()
        # 删smd内东西
        for lay in setValue["runSmdLayerList"]:
            s.affect(lay)
            s.setAttrFilter('.smd')
            s.selectSymbol()
            s.resetFilter()
            if s.Selected_count() > 0:
                s.copyToLayer('tmp1', size=-0.5)
                s.refSelectFilter('tmp1', mode='cover')
                if s.Selected_count() > 0:
                    s.selectDelete()
            s.clearAll()
            s.truncate_layer('tmp1')
        s.clearAll()
        s.clearAndReset()

    def DoAddPad(self):
        s.clearAll()
        s.clearAndReset()

        self.drillList = []
        info = job.matrix.info
        for name, type, context in zip(info['gROWname'], info['gROWlayer_type'], info['gROWcontext']):
            if name and context == 'board' and type == 'drill':
                self.drillList.append(name)
        # 遍历钻孔层
        for layName in self.drillList:
            bflay = layName + '_bf1'
            if s.isLayer(bflay):
                s.removeLayer(bflay)
            s.copyLayer(job_name, step_name, layName, bflay)
            s.affect(layName)
            info = s.DO_INFO('-t layer -e %s/%s/%s -d TOOL' % (job_name, step_name, layName))
            for drillSize in info['gTOOLdrill_size']:
                symbolName = 'r' + str(drillSize)
                if float(drillSize) <= 5:  # 定义为laser
                    s.setTypeFilter('pad')
                    s.setPolarityFilter('positive')
                    s.selectSymbol(symbolName)
                    if s.Selected_count():
                        s.COM("cur_atr_reset")
                        s.COM(" cur_atr_set,attribute=.drill,option=via")
                        s.COM(" cur_atr_set,attribute=.via_type,option=laser")
                        # s.COM(" sel_change_atr,mode=add")
                        s.COM(" sel_change_atr,mode=replace")
                        s.COM("cur_atr_reset")
                    s.clearAndReset()
                elif float(drillSize) > 5 and float(drillSize) <= 15.748:  # 定义为via
                    s.setTypeFilter('pad')
                    s.setPolarityFilter('positive')
                    s.selectSymbol(symbolName)
                    # 20210130 hmx
                    s.resetFilter()
                    s.setAttrFilter('.drill', 'non_plated')
                    s.unselectSymbol()
                    s.resetFilter()
                    ###
                    if s.Selected_count():
                        s.sel_options('clear_none')
                        s.copyToLayer('via_layer')
                        s.sel_options('clear_after')
                        s.COM("cur_atr_reset")
                        s.COM(" cur_atr_set,attribute=.drill,option=via")
                        # s.COM(" sel_change_atr,mode=add")
                        s.COM(" sel_change_atr,mode=replace")
                        s.COM("cur_atr_reset")
                        s.clearAndReset()
                        s.affect(layName)
            s.clearAndReset()
            s.clearAll()

    def DoEnd(self):
        s.VOF()
        s.removeLayer('tmp1')
        s.removeLayer('tmp2')
        s.removeLayer('tmp3')
        s.removeLayer('tmp4')
        s.removeLayer('tmp5')
        s.removeLayer('cm_smd_ok')
        s.removeLayer('sm_smd_ok')
        s.removeLayer('cm_bga_ok')
        s.removeLayer('sm_bga_ok')
        s.removeLayer('cm_smd_cover')
        s.removeLayer('sm_smd_cover')
        s.removeLayer('cs_shrink_pre')
        s.removeLayer('ss_shrink_pre')
        s.removeLayer('cm+++')
        s.removeLayer('sm+++')
        s.VON()

    def DoAddNpthClearance(self):
        """无铜孔加开窗"""
        s.COM("truncate_layer,layer=tmp1")
        s.COM("truncate_layer,layer=tmp2")
        s.COM("truncate_layer,layer=tmp3")
        s.COM("truncate_layer,layer=tmp4")
        s.COM("truncate_layer,layer=tmp5")
        s.clearAll()
        s.clearAndReset()
        npthLay = []
        for name, type, context in zip(job.matrix.info["gROWname"], job.matrix.info["gROWlayer_type"],
                                       job.matrix.info["gROWcontext"]):
            if name and type == 'drill' and context == 'board':
                npthLay.append(name)
        if npthLay:
            for i in npthLay:
                s.affect(i)
            s.setAttrFilter('.drill', 'non_plated')
            s.selectSymbol('')
            if s.Selected_count():
                s.copyToLayer('tmp1', size=12)
                s.clearAndReset()
                s.clearAll()
                if 'cs' in setValue["runSmdLayerList"]:
                    s.copyLayer(job_name, step_name, 'tmp1', 'cm', mode='append')
                if 'ss' in setValue["runSmdLayerList"]:
                    s.copyLayer(job_name, step_name, 'tmp1', 'sm', mode='append')
        s.clearAll()
        s.clearAndReset()
        s.COM("truncate_layer,layer=tmp1")

    def DoGoBackSignal(self):
        # 还原线路层
        for lay in setValue["runAllLayerList"]:
            s.copyLayer(job_name, step_name, lay + '_bf', lay)

    def DoCheckLineClearance(self):
        '''检测连线未开小窗'''
        s.COM("truncate_layer,layer=tmp1")
        s.COM("truncate_layer,layer=tmp2")
        s.COM("truncate_layer,layer=tmp3")
        s.COM("truncate_layer,layer=tmp4")
        s.COM("truncate_layer,layer=tmp5")
        if s.isLayer('cm_er1'):
            s.removeLayer('cm_er1')
        if s.isLayer('sm_er1'):
            s.removeLayer('sm_er1')
        smdValue = (float(setValue["smdSurfaceCoveEnlarge"]) - float(setValue["smdCompensation"]) / 2) * 2 + 1  # 小开窗大小
        bgaValue = (float(setValue["bgaSurfaceCoveEnlarge"]) - float(setValue["bgaCompensation"]) / 2) * 2 + 1  # 小开窗大小
        if 'cs' in setValue["runSmdLayerList"] or 'cs' in setValue["runBgaLayerList"]:
            s.copyLayer(job_name, step_name, 'cm', 'tmp1')
            s.affect('cs')
            # 选smd
            s.setAttrFilter('.smd')
            s.selectSymbol('')
            if s.Selected_count():
                s.copyToLayer('tmp1', 'yes', size=smdValue)
            s.clearAndReset()
            # 选bga
            s.setAttrFilter('.bga')
            s.selectSymbol('')
            if s.Selected_count():
                s.copyToLayer('tmp1', 'yes', size=bgaValue)
            s.clearAndReset()
            # 选线
            s.setTypeFilter("line\;arc")
            s.setPolarityFilter("positive")
            s.selectSymbol('')
            s.resetFilter()
            # 去泪滴
            s.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=.tear_drop')
            s.COM('filter_area_strt')
            s.COM('filter_area_end,layer=,filter_name=popup,operation=unselect')
            s.resetFilter()
            if s.Selected_count():
                s.copyToLayer('tmp2')
                s.clearAll()
                s.clearAndReset()
                # 转铜
                s.affect('tmp1')
                ##删除小孔开窗
                s.setFilterTypes('pad')
                s.setPolarityFilter('positive')
                s.selectSymbol('r8\;r9\;r10\;r11\;r12\;r13\;r14\;r8.*\;r9.*\;r10.*\;r11.*\;r12.*\;r13.*\;r14.*')
                s.resetFilter()
                s.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=.smd')
                s.COM('filter_area_strt')
                s.COM('filter_area_end,layer=,filter_name=popup,operation=unselect')
                s.resetFilter()
                s.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=.bga')
                s.COM('filter_area_strt')
                s.COM('filter_area_end,layer=,filter_name=popup,operation=unselect')
                s.resetFilter()
                if s.Selected_count():
                    s.selectDelete()
                ##删除小孔开窗end
                s.VOF()
                text = s.Contourize(0.1, clean_hole_size=1)
                s.VON()
                if text:
                    s.COM('optimize_levels,layer=tmp1,opt_layer=tmp5,levels=1')
                    s.copyLayer(job_name, step_name, 'tmp5', 'tmp1')
                s.clearAll()
                # touch
                s.affect('tmp2')
                s.selectChange('r1')
                s.refSelectFilter('tmp1')
                # s.PAUSE('111')
                if s.Selected_count():
                    # s.PAUSE('1111111111111')
                    # 创建cm_er1层
                    job.matrix.getInfo()
                    for i in range(0, len(job.matrix.info["gROWcontext"])):
                        if job.matrix.info["gROWname"][i] == 'cm':
                            job.matrix.addLayer('cm_er1', i + 1, 'board', 'document')
                            break
                    s.copyToLayer('cm_er1')
                    s.clearAll()
                    s.clearAndReset()
            s.clearAll()

        s.COM("truncate_layer,layer=tmp1")
        s.COM("truncate_layer,layer=tmp2")
        s.COM("truncate_layer,layer=tmp3")
        s.COM("truncate_layer,layer=tmp4")
        s.COM("truncate_layer,layer=tmp5")
        if 'ss' in setValue["runSmdLayerList"] or 'ss' in setValue["runBgaLayerList"]:
            s.copyLayer(job_name, step_name, 'sm', 'tmp1')
            s.affect('ss')
            # 选smd
            s.setAttrFilter('.smd')
            s.selectSymbol('')
            if s.Selected_count():
                s.copyToLayer('tmp1', 'yes', size=smdValue)
            s.clearAndReset()
            # 选bga
            s.setAttrFilter('.bga')
            s.selectSymbol('')
            if s.Selected_count():
                s.copyToLayer('tmp1', 'yes', size=bgaValue)
            s.clearAndReset()
            # 选线
            s.setTypeFilter("line\;arc")
            s.setPolarityFilter("positive")
            s.selectSymbol('')
            s.resetFilter()
            # 去泪滴
            s.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=.tear_drop')
            s.COM('filter_area_strt')
            s.COM('filter_area_end,layer=,filter_name=popup,operation=unselect')
            s.resetFilter()
            if s.Selected_count():
                s.copyToLayer('tmp2')
                s.clearAll()
                s.clearAndReset()
                # 转铜
                s.affect('tmp1')
                ##删除小孔开窗
                s.setTypeFilter('pad')
                s.setPolarityFilter('positive')
                s.selectSymbol('r8\;r9\;r10\;r11\;r12\;r13\;r14\;r8.*\;r9.*\;r10.*\;r11.*\;r12.*\;r13.*\;r14.*')
                s.resetFilter()
                s.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=.smd')
                s.COM('filter_area_strt')
                s.COM('filter_area_end,layer=,filter_name=popup,operation=unselect')
                s.resetFilter()
                s.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=.bga')
                s.COM('filter_area_strt')
                s.COM('filter_area_end,layer=,filter_name=popup,operation=unselect')
                s.resetFilter()
                if s.Selected_count():
                    s.selectDelete()
                ##删除小孔开窗end
                s.VOF()
                text = s.Contourize(0.1, clean_hole_size=3)
                s.VON()
                if text:
                    s.COM('optimize_levels,layer=tmp1,opt_layer=tmp5,levels=1')
                    s.copyLayer(job_name, step_name, 'tmp5', 'tmp1')
                s.clearAll()
                # touch
                s.affect('tmp2')
                s.selectChange('r1')
                s.refSelectFilter('tmp1')
                if s.Selected_count():
                    # s.PAUSE('2222222222222')
                    # 创建cm_er1层
                    job.matrix.getInfo()
                    for i in range(0, len(job.matrix.info["gROWcontext"])):
                        if job.matrix.info["gROWname"][i] == 'sm':
                            job.matrix.addLayer('sm_er1', i + 2, 'board', 'document')
                            break
                    s.copyToLayer('sm_er1')
                    s.clearAll()
                    s.clearAndReset()
            s.clearAll()

    def DoShrinkAll(self):
        # # 除smd,bga以外的物件缩小0.5
        # for lay in setValue["runAllLayerList"]:
        #     s.affect(lay)
        #     s.copyToLayer(lay + '_shrink_pre')
        #     #s.setAttrFilter('.smd')
        #     #s.selectSymbol()
        #     s.resetFilter()
        #     if s.Selected_count():
        #         s.selectReverse()
        #         if s.Selected_count():
        #             s.setPolarityFilter('negative')
        #             s.COM('filter_area_strt')
        #             s.COM('filter_area_end,layer=,filter_name=popup,operation=unselect,\
        #             area_type=none,inside_area=no,intersect_area=no,lines_only=no,\
        #             ovals_only=no,min_len=0,max_len=0,min_angle=0,max_angle=0')
        #             s.resetFilter()
        #             if s.Selected_count():
        #                 s.resize(-0.5)
        #     s.clearAll()
        # # 盖线相应加大
        # setValue["smdCoverageMin"] =  str(float(setValue["smdCoverageMin"])+ 0.25)
        # setValue["smdCoverageOpt"] =  str(float(setValue["smdCoverageOpt"])+ 0.25)
        #
        # setValue["smdCompensation"] = str(float(setValue["smdCompensation"]) - 0.5)
        # setValue["bgaCompensation"] = str(float(setValue["bgaCompensation"]) - 0.5)
        #     #cs_shrink_pre

        # 除smd,bga以外的物件缩小0.5
        for lay in setValue["runAllLayerList"]:
            s.affect(lay)
            s.copyToLayer(lay + '_shrink_pre')
            s.setAttrFilter('.smd')
            s.selectSymbol()
            s.resetFilter()
            s.setAttrFilter('.bga')
            s.selectSymbol()
            s.resetFilter()
            if s.Selected_count():
                s.selectReverse()
                if s.Selected_count():
                    s.setPolarityFilter('negative')
                    s.COM('filter_area_strt')
                    s.COM('filter_area_end,layer=,filter_name=popup,operation=unselect,\
                           area_type=none,inside_area=no,intersect_area=no,lines_only=no,\
                           ovals_only=no,min_len=0,max_len=0,min_angle=0,max_angle=0')
                    s.resetFilter()
                    if s.Selected_count():
                        s.resize(-0.5)
            s.clearAll()
        # 盖线相应加大
        # s.PAUSE('3333 %s %s %s %s' % (setValue['bgaCoverageMin'],float(setValue["smdCoverageMin"]),float(setValue["smdCoverageMin"]) + 0.25,str(float(setValue["smdCoverageMin"]) + 0.25)))
        setValue["smdCoverageMin"] = str(float(setValue["smdCoverageMin"]) + 0.25)
        setValue["smdCoverageOpt"] = str(float(setValue["smdCoverageOpt"]) + 0.25)
        setValue["bgaCoverageMin"] = str(float(setValue["bgaCoverageMin"]) + 0.25)
        setValue["bgaCoverageOpt"] = str(float(setValue["bgaCoverageOpt"]) + 0.25)

    # s.PAUSE('222222 %s' % (setValue['bgaCoverageMin']))
    # setValue["smdCompensation"] = str(float(setValue["smdCompensation"]) - 0.5)
    # setValue["bgaCompensation"] = str(float(setValue["bgaCompensation"]) - 0.5)
    # cs_shrink_pre

    def DoSmdAndBgaJoin(self):
        """将跑好的bga,smd开窗合并"""
        for lay in setValue["runAllLayerList"]:
            if lay == 'cs':
                soldName = 'cm'
            elif lay == 'ss':
                soldName = 'sm'
            s.copyLayer(job_name, step_name, soldName + '_smd_ok', soldName, mode='append')
            s.copyLayer(job_name, step_name, soldName + '_bga_ok', soldName, mode='append')

    def DoBgaRunClearance(self):
        '''制作bga开窗'''
        s.COM("truncate_layer,layer=tmp1")
        s.COM("truncate_layer,layer=tmp2")
        s.COM("truncate_layer,layer=tmp3")
        s.COM("truncate_layer,layer=tmp4")
        s.COM("truncate_layer,layer=tmp5")
        for layerName in setValue["runBgaLayerList"]:
            if layerName == 'cs':
                solderLayName = 'cm'
                runOkLayName = 'cm_bga_ok'
            elif layerName == 'ss':
                solderLayName = 'sm'
                runOkLayName = 'sm_bga_ok'
            else:
                QMessageBox.warning(self, "warning", '已中止,%s层错误,不认识' % layerName, QMessageBox.Ok)
                sys.exit()
            s.affect(layerName)
            s.setAttrFilter('.bga')
            s.selectSymbol('')
            if s.Selected_count():
                s.copyToLayer('tmp1')
                s.copyLayer(job_name, step_name, 'tmp1', 'tmp2')
                s.clearAll()
                s.affect('tmp2')
                # s.resize('40')
                s.resize('30')  # 20201114 hmx s20-2652a
                s.Contourize(0.25, clean_hole_size=3)
                # s.COM('sel_decompose,overlap=yes')
                s.moveSel('tmp3')
                s.copyLayer(job_name, step_name, 'tmp3', 'tmp2')
                s.COM("truncate_layer,layer=tmp3")
                s.clearAndReset()
                s.selectSymbol('')
                mn = s.Selected_count()
                s.clearAndReset()
                for i in range(0, mn):
                    myindex = i + 1
                    s.selIndexLayer('tmp2', myindex)
                    s.COM("cur_atr_set,attribute=.string,text=%s" % myindex)
                    s.COM("sel_change_atr,mode=replace")
                    s.resetAttr()
                    s.clearAndReset()
                s.clearAll()

                # 计算每组bga桥
                for index in range(1, mn + 1):
                    s.COM("truncate_layer,layer=tmp3")
                    s.affect('tmp2')
                    s.selIndexLayer('tmp2', index)
                    s.moveSel('tmp3')
                    s.clearAll()
                    s.affect('tmp1')
                    s.refSelectFilter('tmp3', mode='cover')
                    # s.PAUSE('11')
                    if s.Selected_count():
                        # s.PAUSE('33')
                        s.COM(" chklist_cupd,chklist=system_sm,nact=3,params=((pp_layer=tmp1)(pp_spacing=10)(pp_r2c=25)"
                              "(pp_d2c=14)(pp_sliver=10)(pp_min_pad_overlap=5)(pp_tests=Spacing)(pp_selected=Selected)"
                              "(pp_check_missing_pads_for_drills=Yes)(pp_use_compensated_rout=No)(pp_sm_spacing=No)),mode=regular")
                        s.COM(" chklist_run,chklist=system_sm,nact=3,area=global,async_run=no")
                        info = s.INFO('-t check -e %s/%s/system_sm -d MEAS -o action=3,angle_direction=ccw' % (
                            job_name, step_name))
                        ####
                        Clearance_Opt_Value = float(setValue["bgaClearanceOpt"]) - float(
                            setValue["bgaCompensation"]) / 2  # 大开窗单边
                        Clearance_Min_Value = float(setValue["bgaSurfaceCoveEnlarge"]) - float(
                            setValue["bgaCompensation"]) / 2  # 小开窗单边
                        # Embedded_Value = 0
                        if info:
                            p2p_min_val = float(list(info[0].split())[2])  # bga pad 到pad的最小距离
                            allow_big_value = (p2p_min_val - float(setValue["bgaBridgeOpt"])) / 2  # 考虑到桥允许最大的开窗尺寸
                            if Clearance_Opt_Value > allow_big_value:
                                Clearance_Opt_Value = allow_big_value
                        # if Clearance_Min_Value < 0.1:
                        #     Embedded_Value = Clearance_Min_Value - 0.1
                        #     Clearance_Min_Value = 0.1
                        add_val = 0  # 附加值 开窗整体附加 (因为小开窗在-0.1~0.1之间时 有些异性pad开窗不会加大)
                        # if Clearance_Min_Value >= 0 and Clearance_Min_Value < 0.1:
                        #     add_val = 0.1
                        # elif Clearance_Min_Value < 0 and Clearance_Min_Value > -0.1:
                        #     add_val = -0.1
                        add_val = 0.1 - Clearance_Min_Value
                        Clearance_Min_Value += add_val
                        Clearance_Opt_Value += add_val
                        # setValue['bgaCoverageMin'] = str(float(setValue['bgaCoverageMin']) + add_val)
                        # setValue['bgaCoverageOpt'] = str(float(setValue['bgaCoverageOpt']) + add_val)

                        s.copyToLayer(solderLayName, size=Clearance_Min_Value * 2)
                        s.clearAll()
                        # s.PAUSE('11111111')
                        if Clearance_Opt_Value < 0:
                            Clearance_Opt_Value = 0
                        # 开始跑bga
                        s.COM(" chklist_open,chklist=system_sm")
                        s.COM(" chklist_show,chklist=system_sm,nact=1,pinned=yes,pinned_enabled=yes")
                        s.COM(" chklist_close,chklist=valor_analysis_sm,mode=hide")
                        # s.COM(" chklist_cupd,chklist=system_sm,nact=1,params=((pp_layer="+layerName+")(pp_min_clear="+str(Clearance_Min_Value)+")(pp_opt_clear="+str(Clearance_Opt_Value)+")(pp_min_cover="+setValue['bgaCoverageMin']+")(pp_opt_cover="+setValue['bgaCoverageOpt']+")(pp_min_bridge="+setValue['bgaBridgeMin']+")(pp_opt_bridge="+setValue['bgaBridgeOpt']+")(pp_selected=All)(pp_use_mask=Yes)(pp_use_shave=Yes)(pp_shave_cu=)(pp_rerout_line=)(pp_min_cu_width=5)(pp_min_cu_spacing=2.5)(pp_min_pth_ar=5)(pp_min_via_ar=5)(pp_fix_coverage=PTH\;Via\;NPTH\;SMD\;BGA)(pp_fix_bridge=PTH\;Via\;NPTH\;SMD\;BGA)(pp_split_clr_for_pad=PTH\;Via\;SMD\;BGA\;Other)(pp_partial=)(pp_gasket_smd_as_regular=2)(pp_gasket_bga_as_regular=2)(pp_gasket_pth_as_regular=2)(pp_gasket_via_as_regular=2)(pp_do_small_clearances=)(pp_handle_same_size=)(pp_handle_embedded_as_regular=)(pp_partial_embedded_mode=Split Clearance)),mode=regular")
                        s.COM(
                            " chklist_cupd,chklist=system_sm,nact=1,params=((pp_layer=" + layerName + ")(pp_min_clear=0)(pp_opt_clear=" + str(
                                Clearance_Opt_Value) + ")(pp_min_cover=" + setValue[
                                'bgaCoverageMin'] + ")(pp_opt_cover=" + setValue[
                                'bgaCoverageOpt'] + ")(pp_min_bridge=" + setValue['bgaBridgeMin'] + ")(pp_opt_bridge=" +
                            setValue[
                                'bgaBridgeOpt'] + ")(pp_selected=All)(pp_use_mask=Yes)(pp_use_shave=Yes)(pp_shave_cu=)(pp_rerout_line=)(pp_min_cu_width=5)(pp_min_cu_spacing=2.5)(pp_min_pth_ar=5)(pp_min_via_ar=5)(pp_fix_coverage=PTH\;Via\;NPTH\;SMD\;BGA)(pp_fix_bridge=PTH\;Via\;NPTH\;SMD\;BGA)(pp_split_clr_for_pad=PTH\;Via\;SMD\;BGA\;Other)(pp_partial=)(pp_gasket_smd_as_regular=2)(pp_gasket_bga_as_regular=2)(pp_gasket_pth_as_regular=2)(pp_gasket_via_as_regular=2)(pp_do_small_clearances=)(pp_handle_same_size=)(pp_handle_embedded_as_regular=)(pp_partial_embedded_mode=Split Clearance)),mode=regular")
                        # s.COM(" chklist_erf_variable,chklist=system_sm,nact=1,variable=v_enlarge_embedded_pth,value="+str(Embedded_Value)+",options=0")
                        # s.COM(" chklist_erf_variable,chklist=system_sm,nact=1,variable=v_enlarge_embedded_smd,value="+str(Embedded_Value)+",options=0")
                        # s.COM(" chklist_erf_variable,chklist=system_sm,nact=1,variable=v_enlarge_embedded_bga,value="+str(Embedded_Value)+",options=0")
                        # s.COM(" chklist_erf_variable,chklist=system_sm,nact=1,variable=v_enlarge_embedded_via,value="+str(Embedded_Value)+",options=0")
                        # s.COM(" chklist_erf_variable,chklist=system_sm,nact=1,variable=v_enlarge_embedded_normal,value="+str(Embedded_Value)+",options=0")
                        # s.COM(" chklist_erf_variable,chklist=system_sm,nact=1,variable=v_split_embedded_pth,value="+str(Embedded_Value)+",options=0")
                        # s.COM(" chklist_erf_variable,chklist=system_sm,nact=1,variable=v_split_embedded_smd,value="+str(Embedded_Value)+",options=0")
                        # s.COM(" chklist_erf_variable,chklist=system_sm,nact=1,variable=v_split_embedded_bga,value="+str(Embedded_Value)+",options=0")
                        # s.COM(" chklist_erf_variable,chklist=system_sm,nact=1,variable=v_split_embedded_via,value="+str(Embedded_Value)+",options=0")
                        # s.COM(" chklist_erf_variable,chklist=system_sm,nact=1,variable=v_split_embedded_normal,value="+str(Embedded_Value)+",options=0")
                        s.COM(" chklist_erf_variable,chklist=system_sm,nact=1,variable=min_trace_to_split,value=" +
                              setValue['bgaTraceSplitMin'] + ",options=0")
                        s.COM(" chklist_cnf_act,chklist=system_sm,nact=1,cnf=no")
                        s.COM(" chklist_run,chklist=system_sm,nact=1,area=global,async_run=yes")
                        # s.PAUSE('11 %s %s' % (Clearance_Min_Value,add_val))

                        # 减回附加值
                        s.affect(solderLayName)
                        s.setPolarityFilter('positive')
                        s.selectSymbol()
                        s.resetFilter()
                        if s.Selected_count():
                            back_val = 0 - add_val
                            s.resize(back_val * 2)
                        s.clearAll()
                        #  s.PAUSE('2222')

                        # 加上小开窗
                        s.affect('tmp1')
                        s.refSelectFilter('tmp3', mode='cover')
                        # s.PAUSE('11')
                        if s.Selected_count():
                            # if Clearance_Min_Value == 0:
                            #     s.copyToLayer(solderLayName, size=Embedded_Value * 2)
                            # else:
                            #     s.copyToLayer(solderLayName, size=Clearance_Min_Value * 2)
                            back_val = 0 - add_val
                            # s.copyToLayer(solderLayName, size=(Clearance_Min_Value + back_val) * 2)
                            # 负片要放上面
                            s.copyToLayer('tmp4', size=(Clearance_Min_Value + back_val) * 2)
                            s.copyLayer(job_name, step_name, solderLayName, 'tmp4', 'append')
                            s.copyLayer(job_name, step_name, 'tmp4', solderLayName)
                            s.COM("truncate_layer,layer=tmp4")
                        s.clearAll()

                        # 移到ok层中
                        s.affect(solderLayName)
                        s.moveSel(runOkLayName)
                        s.clearAll()
                        s.COM("truncate_layer,layer=tmp3")
            s.COM("truncate_layer,layer=tmp1")
            s.COM("truncate_layer,layer=tmp2")
            s.COM("truncate_layer,layer=tmp3")
            s.COM("truncate_layer,layer=tmp4")
            s.COM("truncate_layer,layer=tmp5")
            s.clearAll()

        s.COM("truncate_layer,layer=tmp1")
        s.COM("truncate_layer,layer=tmp2")
        s.COM("truncate_layer,layer=tmp3")
        s.COM("truncate_layer,layer=tmp4")
        s.COM("truncate_layer,layer=tmp5")
        s.clearAll()

    def DoSmdEnd(self):
        '''保存跑好的smd'''
        if 'cs' in setValue["runSmdLayerList"]:
            if s.isLayer('cm_smd_ok'):
                s.removeLayer('cm_smd_ok')
            s.copyLayer(job_name, step_name, 'cm', 'cm_smd_ok')
            s.COM("truncate_layer,layer=cm")
        if 'ss' in setValue["runSmdLayerList"]:
            if s.isLayer('sm_smd_ok'):
                s.removeLayer('sm_smd_ok')
            s.copyLayer(job_name, step_name, 'sm', 'sm_smd_ok')
            s.COM("truncate_layer,layer=sm")

    # def DoSmdRunCoverage(self):
    #     if setValue["runSmdLayerList"]:
    #         '''削盖线'''
    #         if 'cs' in setValue["runSmdLayerList"] or 'cs' in setValue["runBgaLayerList"]:
    #             s.copyLayer(job_name, step_name, 'cs', 'cs_tmp886')
    #             s.copyLayer(job_name, step_name, 'cs_bf', 'cs')
    #         if 'ss' in setValue["runSmdLayerList"] or 'ss' in setValue["runBgaLayerList"]:
    #             s.copyLayer(job_name, step_name, 'ss', 'ss_tmp886')
    #             s.copyLayer(job_name, step_name, 'ss_bf', 'ss')
    #         myValue1 = '\;'.join(setValue["runSmdLayerList"])
    #         ###
    #         # s.VOF()
    #         # s.COM(" chklist_delete,chklist=system_sm")
    #         # s.COM(" chklist_delete,chklist=checklist")
    #         # s.VON()
    #         # s.COM(" chklist_from_lib,chklist=system_sm,profile=none,customer=")
    #         # s.COM(" chklist_open,chklist=system_sm")
    #         ###
    #         s.COM(" chklist_cupd,chklist=system_sm,nact=2,params=((pp_layer="+ myValue1 +")(pp_min_clear=0)(pp_opt_clear=0)"
    #               "(pp_min_cover="+ setValue['smdCoverageMin'] +")(pp_opt_cover="+ setValue['smdCoverageOpt'] +")(pp_min_bridge="
    #               + setValue['smdBridgeMin'] +")(pp_opt_bridge="+ setValue['smdBridgeOpt'] +")(pp_selected=All)"
    #               "(pp_use_mask=Yes)(pp_use_shave=Yes)(pp_shave_cu=)(pp_rerout_line=)(pp_min_cu_width=5)(pp_min_cu_spacing=2.5)"
    #               "(pp_min_pth_ar=5)(pp_min_via_ar=5)(pp_fix_coverage=PTH\;Via\;NPTH\;SMD\;BGA)(pp_fix_bridge=PTH\;Via\;NPTH\;SMD\;BGA)"
    #               "(pp_split_clr_for_pad=)(pp_partial=)(pp_gasket_smd_as_regular=0)(pp_gasket_bga_as_regular=0)"
    #               "(pp_gasket_pth_as_regular=0)(pp_gasket_via_as_regular=0)(pp_do_small_clearances=)(pp_handle_same_size=)"
    #               "(pp_handle_embedded_as_regular=)(pp_partial_embedded_mode=As Embedded)),mode=regular")
    #         s.COM(" chklist_cnf_act,chklist=system_sm,nact=2,cnf=no")
    #         s.COM(" chklist_run,chklist=system_sm,nact=2,area=global,async_run=no")
    #
    #         if 'cs' in setValue["runSmdLayerList"] or 'cs' in setValue["runBgaLayerList"]:
    #             s.copyLayer(job_name, step_name, 'cs_tmp886', 'cs')
    #         if 'ss' in setValue["runSmdLayerList"] or 'ss' in setValue["runBgaLayerList"]:
    #             s.copyLayer(job_name, step_name, 'ss_tmp886', 'ss')

    def DoSignalRemoval(self):
        s.COM("truncate_layer,layer=tmp1")
        s.COM("truncate_layer,layer=tmp2")
        s.COM("truncate_layer,layer=tmp3")
        s.COM("truncate_layer,layer=tmp4")
        s.COM("truncate_layer,layer=tmp5")
        s.clearAndReset()
        s.clearAll()
        # 铜皮smd转pad
        for lay in setValue["runSmdLayerList"]:
            s.affect(lay)
            s.setAttrFilter('.smd')
            s.setTypeFilter('surface')
            s.selectSymbol()
            s.resetFilter()
            if s.Selected_count():
                # s.VOF()
                s.COM('sel_cont2pad,match_tol=0.1,restriction=,min_size=1,max_size=500,suffix=+++')
                # s.VON()

            s.clearAll()
        s.COM('check_resized_sym,job=%s' % job_name)
        s.clearAll()
        # s.PAUSE('222')

        alllay = list(set(setValue["runSmdLayerList"] + setValue["runBgaLayerList"]))
        # smd.bga转铜转pad
        for lay in alllay:
            s.affect(lay)
            s.setPolarityFilter('positive')
            s.setAttrFilter('.bga')
            s.selectSymbol()
            s.resetFilter()
            s.setPolarityFilter('positive')
            s.setAttrFilter('.smd')
            s.selectSymbol()
            if s.Selected_count():
                s.moveSel('tmp2')
                s.clearAll()
                s.affect('tmp2')
                # s.Contourize(0,'yes',3)
                # s.COM('sel_decompose,overlap=yes')
                # s.COM('sel_cont2pad,match_tol=0.1,restriction=,min_size=1,max_size=500,suffix=+++')
                # my $pp_layer = $matrix_hash{'out_signal_layer'}[0].'\;'.$matrix_hash{'out_signal_layer'}[1];

                # s.COM("chklist_single,show=yes,action=valor_dfm_nfpr")
                # s.COM("chklist_cupd,chklist=valor_dfm_nfpr,nact=1,params=((pp_layer=tmp2)(pp_delete=Duplicate)(pp_work=Features)(pp_drill=)(pp_non_drilled=No)(pp_in_selected=All)(pp_remove_mark=Remove)),mode=regular")
                # s.COM("chklist_cnf_act,chklist=valor_dfm_nfpr,nact=1,cnf=no")
                # s.COM("chklist_set_hdr,chklist=valor_dfm_nfpr,save_res=no,stop_on_err=no,run=activated,area=global,mask=None,mask_usage=include")
                # s.COM("chklist_run,chklist=valor_dfm_nfpr,nact=1,area=global,async_run=yes")

                s.COM(" chklist_single,show=yes,action=valor_dfm_nfpr")
                s.COM(
                    " chklist_cupd,chklist=valor_dfm_nfpr,nact=1,params=((pp_layer=.affected)(pp_delete=Duplicate\;Covered)(pp_work=Features)(pp_drill=)(pp_non_drilled=No)(pp_in_selected=All)(pp_remove_mark=Remove)),mode=regular")
                s.COM(
                    " chklist_erf_variable,chklist=valor_dfm_nfpr,nact=1,variable=do_isolated_by_hole_type,value=0,options=0")
                s.COM(" chklist_erf_variable,chklist=valor_dfm_nfpr,nact=1,variable=v_immunity_attr,value=,options=0")
                s.COM(
                    " chklist_erf_variable,chklist=valor_dfm_nfpr,nact=1,variable=v_tolerance,value=0.01,options=0")  #
                s.COM(" chklist_cnf_act,chklist=valor_dfm_nfpr,nact=1,cnf=no")
                s.COM(
                    " chklist_set_hdr,chklist=valor_dfm_nfpr,save_res=no,stop_on_err=no,run=activated,area=global,mask=None,mask_usage=include")
                s.COM(" chklist_run,chklist=valor_dfm_nfpr,nact=1,area=global,async_run=yes")

                s.copyLayer(job_name, step_name, lay, 'tmp2', 'append')
                s.copyLayer(job_name, step_name, 'tmp2', lay)
            s.clearAll()
            if s.isLayer('tmp2+++'):
                s.removeLayer('tmp2+++')
            s.COM("truncate_layer,layer=tmp1")
            s.COM("truncate_layer,layer=tmp2")
            s.COM("truncate_layer,layer=tmp3")
            s.COM("truncate_layer,layer=tmp4")
            s.COM("truncate_layer,layer=tmp5")
        s.clearAll()
        s.clearAndReset()

        # s.PAUSE('111')

        # 删除线路bga上的smd属性######################################
        if 'cs' in setValue["runSmdLayerList"] or 'cs' in setValue["runBgaLayerList"]:
            s.affect('cs')
            s.setAttrFilter('.bga')
            s.selectSymbol('')
            if s.Selected_count():
                s.COM('sel_delete_atr,attributes=.smd')
            s.clearAndReset()
            s.clearAll()
        if 'ss' in setValue["runSmdLayerList"] or 'ss' in setValue["runBgaLayerList"]:
            s.affect('ss')
            s.setAttrFilter('.bga')
            s.selectSymbol('')
            if s.Selected_count():
                s.COM('sel_delete_atr,attributes=.smd')
            s.clearAndReset()
            s.clearAll()
        #########################################################

    def DoRemoveClearance(self):
        """删除所有开窗"""
        for lay in ['cm', 'sm']:
            if s.isLayer(lay):
                s.COM("truncate_layer,layer=" + lay)

    def DoShareCoverage(self):
        """削盖线,桥"""
        runLayStr = '\;'.join(setValue["runSmdLayerList"])
        Clearance_Opt_Value = (float(setValue["smdClearanceOpt"]) - float(setValue["smdCompensation"]) / 2)  # 大开窗大小单边
        Clearance_Min_Value = (
                float(setValue["smdSurfaceCoveEnlarge"]) - float(setValue["smdCompensation"]) / 2)  # 小开窗大小单边
        s.COM("truncate_layer,layer=tmp1")
        s.COM("truncate_layer,layer=tmp2")
        s.COM("truncate_layer,layer=tmp3")
        s.COM("truncate_layer,layer=tmp4")
        s.COM("truncate_layer,layer=tmp5")
        s.clearAll()
        s.clearAndReset()
        for lay in setValue["runSmdLayerList"]:
            if lay == 'cs':
                s.COM("truncate_layer,layer=cm")
            elif lay == 'ss':
                s.COM("truncate_layer,layer=sm")
        # 防焊层加开窗############################################
        for lay in setValue["runSmdLayerList"]:
            if lay == 'cs':
                soldName = 'cm'
            elif lay == 'ss':
                soldName = 'sm'
            else:
                QMessageBox.warning(self, "warning", '已中止,%s层错误,不认识' % lay, QMessageBox.Ok)
                sys.exit()
            s.affect(lay)
            s.setAttrFilter('.smd')
            s.selectSymbol()
            s.resetFilter()
            if s.Selected_count():
                s.copyToLayer(soldName, size=Clearance_Opt_Value * 2)
            s.clearAll()
        s.clearAll()
        # 跑DFM
        if setValue["runSmdLayerList"]:
            s.COM(" chklist_open,chklist=system_sm")
            s.COM(" chklist_show,chklist=system_sm,nact=1,pinned=yes,pinned_enabled=yes")
            s.COM(" chklist_close,chklist=valor_analysis_sm,mode=hide")
            s.COM(
                " chklist_cupd,chklist=system_sm,nact=2,params=((pp_layer=" + runLayStr + ")(pp_min_clear=0)(pp_opt_clear=0)(pp_min_cover=" +
                setValue['smdCoverageMin'] + ")(pp_opt_cover=" + setValue['smdCoverageOpt'] + ")(pp_min_bridge=" +
                setValue['smdBridgeMin'] + ")(pp_opt_bridge=" + setValue[
                    'smdBridgeOpt'] + ")(pp_selected=All)(pp_use_mask=Yes)(pp_use_shave=Yes)(pp_shave_cu=)(pp_rerout_line=)(pp_min_cu_width=5)(pp_min_cu_spacing=2.5)(pp_min_pth_ar=5)(pp_min_via_ar=5)(pp_fix_coverage=PTH\;Via\;NPTH\;SMD\;BGA)(pp_fix_bridge=PTH\;Via\;SMD\;BGA)(pp_split_clr_for_pad=)(pp_partial=)(pp_gasket_smd_as_regular=0)(pp_gasket_bga_as_regular=0)(pp_gasket_pth_as_regular=0)(pp_gasket_via_as_regular=0)(pp_do_small_clearances=)(pp_handle_same_size=)(pp_handle_embedded_as_regular=)(pp_partial_embedded_mode=As Embedded)),mode=regular")
            s.COM(" chklist_cnf_act,chklist=system_sm,nact=2,cnf=no")
            s.COM(" chklist_run,chklist=system_sm,nact=2,area=global,async_run=yes")

        for lay in setValue["runSmdLayerList"]:
            if lay == 'cs':
                soldName = 'cm'
            elif lay == 'ss':
                soldName = 'sm'
            s.affect(soldName)
            s.setPolarityFilter('negative')
            s.selectSymbol()
            s.resetFilter()
            # s.PAUSE('3')
            if s.Selected_count():
                s.copyToLayer(soldName + '_smd_cover')
            s.clearAll()
        s.clearAll()

    def DoSmdMoveBackCover(self):
        """移回SMD盖线"""
        for lay in setValue["runSmdLayerList"]:
            if lay == 'cs':
                soldName = 'cm'
            elif lay == 'ss':
                soldName = 'sm'
            coverLay = soldName + '_smd_cover'
            s.copyLayer(job_name, step_name, coverLay, soldName, 'append')

    ############################################################################

    def DoSmdRunClearance_add(self):
        """制作smd开窗 防止开小窗,与smdpad中心相同的再跑一遍,线路形式"""
        if not setValue["runSmdLayerList"]:
            return
        runLayStr = '\;'.join(setValue["runSmdLayerList"])
        Clearance_Opt_Value = (float(setValue["smdClearanceOpt"]) - float(setValue["smdCompensation"]) / 2)  # 大开窗大小单边
        Clearance_Min_Value = (
                float(setValue["smdSurfaceCoveEnlarge"]) - float(setValue["smdCompensation"]) / 2)  # 小开窗大小单边

        add_val = 0.1 - Clearance_Min_Value
        Clearance_Min_Value += add_val
        Clearance_Opt_Value += add_val

        s.COM("truncate_layer,layer=tmp1")
        s.COM("truncate_layer,layer=tmp2")
        s.COM("truncate_layer,layer=tmp3")
        s.COM("truncate_layer,layer=tmp4")
        s.COM("truncate_layer,layer=tmp5")

        s.clearAll()
        s.clearAndReset()

        s.VOF()
        s.removeLayer('cm_ok_01')
        s.removeLayer('sm_ok_01')
        s.VON()
        s.createLayer('cm_ok_01')
        s.createLayer('sm_ok_01')
        # s.PAUSE('1')

        # 只留下中心相同的pad,
        for lay in setValue["runSmdLayerList"]:
            if lay == 'cs':
                soldName = 'cm'
                oksmlay = 'cm_ok_01'
            elif lay == 'ss':
                soldName = 'sm'
                oksmlay = 'sm_ok_01'
            s.affect(lay)
            s.setTypeFilter('pad')
            s.setAttrFilter('.smd')
            s.setPolarityFilter('positive')
            s.selectSymbol()
            s.resetFilter()
            if s.Selected_count():
                s.copyToLayer('tmp1')
            s.clearAll()
            s.affect(soldName)
            s.setTypeFilter('pad')
            s.setAttrFilter('.smd')
            s.setPolarityFilter('positive')
            s.refSelectFilter('tmp1', mode='same_center')
            # s.PAUSE('3333')
            s.resetFilter()
            # if s.Selected_count():
            #     s.selectReverse()
            #     if s.Selected_count():
            #         s.moveSel(oksmlay)
            s.selectReverse()
            if s.Selected_count():
                s.moveSel(oksmlay)

            #  s.PAUSE('2')
            # 去除被线路铜皮覆盖的pad
            s.clearAll()
            s.affect(soldName)
            s.setTypeFilter('pad')
            s.setAttrFilter('.smd')
            s.setPolarityFilter('positive')
            # s.refSelectFilter(lay, mode='cover',)
            # s.COM('sel_ref_feat,layers=%s,use=filter,mode=%s,f_types=line\;pad\;surface\;arc\;text,polarity=positive\;negative,include_syms=,exclude_syms=' % (lay,'cover'))
            s.COM(
                'sel_ref_feat,layers=%s,use=filter,mode=%s,f_types=line\;surface\;arc\;text,polarity=positive,include_syms=,exclude_syms=' % (
                    lay, 'cover'))
            s.resetFilter()
            # s.PAUSE('3')
            if s.Selected_count():
                s.moveSel('tmp2')
            s.copyLayer(job_name, step_name, oksmlay, 'tmp2', 'append')
            s.copyLayer(job_name, step_name, 'tmp2', oksmlay)
            s.clearAll()
            s.COM("truncate_layer,layer=tmp1")
            s.COM("truncate_layer,layer=tmp2")

            # 删除原本的小开窗
            s.copyLayer(job_name, step_name, lay, 'tmp1')
            s.affect('tmp1')
            s.setAttrFilter('.smd')
            s.selectSymbol()
            s.resetFilter()
            if s.Selected_count():
                #  s.PAUSE('1')
                s.moveSel('tmp2', size=1)
                s.clearAll()
                s.affect('tmp2')
                s.COM(
                    'sel_ref_feat,layers=%s,use=filter,mode=%s,f_types=line\;pad\;surface\;arc\;text,polarity=positive,include_syms=,exclude_syms=' % (
                        'tmp1', 'cover'))

                if s.Selected_count():
                    #     s.PAUSE('2')
                    s.moveSel('tmp3', size=Clearance_Opt_Value * 2 + 3)
            s.clearAll()
            s.affect(soldName)
            s.refSelectFilter('tmp3', mode='cover')
            if s.Selected_count():
                #  s.PAUSE('3')

                s.moveSel('tmp4')
                s.copyLayer(job_name, step_name, oksmlay, 'tmp4', 'append')
                s.copyLayer(job_name, step_name, 'tmp4', oksmlay)
            s.clearAll()
            s.truncate_layer('tmp1')
            s.truncate_layer('tmp2')
            s.truncate_layer('tmp3')
            s.truncate_layer('tmp4')

            # 剩下的开窗换成大smd开窗
            s.copyLayer(job_name, step_name, soldName, 'tmp1')
            s.truncate_layer(soldName)
            s.affect(lay)
            s.setTypeFilter('pad')
            s.setAttrFilter('.smd')
            s.setPolarityFilter('positive')
            s.refSelectFilter('tmp1', mode='same_center')
            s.resetFilter()
            if s.Selected_count():
                s.copyToLayer(soldName, size=Clearance_Opt_Value * 2)
            s.clearAll()
            s.truncate_layer('tmp1')
        s.clearAll()
        #   s.PAUSE('end')

        # surface的smd也移回绿油层重跑
        for lay in setValue["runSmdLayerList"]:
            if lay == 'cs':
                soldName = 'cm'
                oksmlay = 'cm_ok_01'
            elif lay == 'ss':
                soldName = 'sm'
                oksmlay = 'sm_ok_01'

            s.truncate_layer('tmp1')
            s.affect(lay)
            s.setTypeFilter('surface')
            s.setAttrFilter('.smd')
            s.selectSymbol()
            s.resetFilter()
            # s.PAUSE('2')
            if s.Selected_count():
                # s.copyToLayer('tmp1',size=Clearance_Opt_Value*2+3)
                s.copyToLayer('tmp1')
                s.copyLayer(job_name, step_name, 'tmp1', 'tmp2')
                s.clearAll()
                s.affect('tmp2')
                s.resize(Clearance_Opt_Value * 2 + 3)

                s.clearAll()
                s.affect(oksmlay)
                s.setAttrFilter('.smd')
                s.refSelectFilter('tmp2', mode='cover')
                s.resetFilter()
                #  s.PAUSE('3')
                if s.Selected_count():
                    s.selectDelete()
            s.clearAll()
            s.affect('tmp1')
            s.copyToLayer(soldName, size=Clearance_Opt_Value * 2)
            s.clearAll()
            s.truncate_layer('tmp1')

            tmpchecklay = soldName + '_tmp1'
            if s.isLayer(tmpchecklay):
                s.removeLayer(tmpchecklay)
            s.copyLayer(job_name, step_name, soldName, tmpchecklay)
        s.clearAll()

        # s.PAUSE('end')

        # 线路临时去负片
        for lay in setValue["runSmdLayerList"]:
            if lay == 'cs':
                soldName = 'cm'
                oksmlay = 'cm_ok_01'
                tmpsiglay = 'cs_tmp_01'
            elif lay == 'ss':
                soldName = 'sm'
                oksmlay = 'sm_ok_01'
                tmpsiglay = 'ss_tmp_01'
            s.copyLayer(job_name, step_name, lay, tmpsiglay)
            s.affect(lay)
            s.setPolarityFilter('negative')
            s.selectSymbol()
            s.resetFilter()
            if s.Selected_count():
                s.selectDelete()
            s.clearAll()

        # # 剩下在中心的Pad 再优化一次 org_signal
        # for lay in setValue["runSmdLayerList"]:
        #     if lay == 'cs':
        #         soldName = 'cm'
        #         oksmlay = 'cm_ok_01'
        #         tmpsiglay = 'cs_tmp_01'
        #     elif lay == 'ss':
        #         soldName = 'sm'
        #         oksmlay = 'sm_ok_01'
        #         tmpsiglay = 'ss_tmp_01'
        #     s.copyLayer(job_name,step_name,soldName,'tmp1')
        #     s.truncate_layer(soldName)
        #     s.affect(lay)
        #     s.setTypeFilter('pad')
        #     s.setAttrFilter('.smd')
        #     s.setPolarityFilter('positive')
        #     s.refSelectFilter('tmp1', mode='same_center')
        #     s.resetFilter()
        #     if s.Selected_count():
        #         s.copyToLayer(soldName,size=Clearance_Opt_Value*2)
        #     s.clearAll()

        s.clearAll()
        #  s.PAUSE('11')
        if setValue["runSmdLayerList"]:
            # s.COM(" chklist_from_lib,chklist=sm_hmx,profile=none,customer=") # 已经重新载入了
            s.COM(" chklist_open,chklist=sm_hmx")
            s.COM(" chklist_show,chklist=sm_hmx,nact=1,pinned=yes,pinned_enabled=yes")
            s.COM(" chklist_close,chklist=valor_analysis_sm,mode=hide")
            # s.COM(" chklist_cupd,chklist=sm_hmx,nact=1,params=((pp_layer="+runLayStr+")(pp_min_clear="+str(Clearance_Min_Value)+")(pp_opt_clear="+str(Clearance_Opt_Value)+")(pp_min_cover="+setValue['smdCoverageMin']+")(pp_opt_cover="+setValue['smdCoverageOpt']+")(pp_min_bridge="+setValue['smdBridgeMin']+")(pp_opt_bridge="+setValue['smdBridgeOpt']+")(pp_selected=All)(pp_use_mask=Yes)(pp_use_shave=Yes)(pp_shave_cu=)(pp_rerout_line=)(pp_min_cu_width=5)(pp_min_cu_spacing=2.5)(pp_min_pth_ar=5)(pp_min_via_ar=5)(pp_fix_coverage=PTH\;Via\;NPTH\;SMD\;BGA)(pp_fix_bridge=PTH\;Via\;NPTH\;SMD\;BGA)(pp_split_clr_for_pad=PTH\;Via\;SMD\;BGA\;Other)(pp_partial=)(pp_gasket_smd_as_regular=2)(pp_gasket_bga_as_regular=2)(pp_gasket_pth_as_regular=2)(pp_gasket_via_as_regular=2)(pp_do_small_clearances=)(pp_handle_same_size=)(pp_handle_embedded_as_regular=)(pp_partial_embedded_mode=Split Clearance)),mode=regular")
            s.COM(
                " chklist_cupd,chklist=sm_hmx,nact=1,params=((pp_layer=" + runLayStr + ")(pp_min_clear=0)(pp_opt_clear=" + str(
                    Clearance_Opt_Value) + ")(pp_min_cover=" + setValue['smdCoverageMin'] + ")(pp_opt_cover=" +
                setValue['smdCoverageOpt'] + ")(pp_min_bridge=" + setValue['smdBridgeMin'] + ")(pp_opt_bridge=" +
                setValue[
                    'smdBridgeOpt'] + ")(pp_selected=All)(pp_use_mask=Yes)(pp_use_shave=Yes)(pp_shave_cu=)(pp_rerout_line=)(pp_min_cu_width=5)(pp_min_cu_spacing=2.5)(pp_min_pth_ar=5)(pp_min_via_ar=5)(pp_fix_coverage=PTH\;Via\;NPTH\;SMD\;BGA)(pp_fix_bridge=PTH\;Via\;NPTH\;SMD\;BGA)(pp_split_clr_for_pad=PTH\;Via\;SMD\;BGA\;Other)(pp_partial=)(pp_gasket_smd_as_regular=2)(pp_gasket_bga_as_regular=2)(pp_gasket_pth_as_regular=2)(pp_gasket_via_as_regular=2)(pp_do_small_clearances=)(pp_handle_same_size=)(pp_handle_embedded_as_regular=)(pp_partial_embedded_mode=Split Clearance)),mode=regular")
            s.COM(" chklist_erf_variable,chklist=sm_hmx,nact=1,variable=v_enlarge_embedded_pth,value=" + str(
                Clearance_Min_Value) + ",options=0")
            s.COM(" chklist_erf_variable,chklist=sm_hmx,nact=1,variable=v_enlarge_embedded_smd,value=" + str(
                Clearance_Min_Value) + ",options=0")
            s.COM(" chklist_erf_variable,chklist=sm_hmx,nact=1,variable=v_enlarge_embedded_bga,value=" + str(
                Clearance_Min_Value) + ",options=0")
            s.COM(" chklist_erf_variable,chklist=sm_hmx,nact=1,variable=v_enlarge_embedded_via,value=" + str(
                Clearance_Min_Value) + ",options=0")
            s.COM(" chklist_erf_variable,chklist=sm_hmx,nact=1,variable=v_enlarge_embedded_normal,value=" + str(
                Clearance_Min_Value) + ",options=0")
            s.COM(" chklist_erf_variable,chklist=sm_hmx,nact=1,variable=v_split_embedded_pth,value=" + str(
                Clearance_Min_Value) + ",options=0")
            s.COM(" chklist_erf_variable,chklist=sm_hmx,nact=1,variable=v_split_embedded_smd,value=" + str(
                Clearance_Min_Value) + ",options=0")
            s.COM(" chklist_erf_variable,chklist=sm_hmx,nact=1,variable=v_split_embedded_bga,value=" + str(
                Clearance_Min_Value) + ",options=0")
            s.COM(" chklist_erf_variable,chklist=sm_hmx,nact=1,variable=v_split_embedded_via,value=" + str(
                Clearance_Min_Value) + ",options=0")
            s.COM(" chklist_erf_variable,chklist=sm_hmx,nact=1,variable=v_split_embedded_normal,value=" + str(
                Clearance_Min_Value) + ",options=0")
            s.COM(" chklist_erf_variable,chklist=sm_hmx,nact=1,variable=min_trace_to_split,value=" + setValue[
                'smdTraceSplitMin'] + ",options=0")
            s.COM(" chklist_cnf_act,chklist=sm_hmx,nact=1,cnf=no")
            s.COM(" chklist_run,chklist=sm_hmx,nact=1,area=global,async_run=yes")
            s.clearAll()
        s.clearAll()
        # s.PAUSE('5')
        # 减回附加值
        for lay in setValue["runSmdLayerList"]:
            if lay == 'cs':
                s.affect('cm')
            elif lay == 'ss':
                s.affect('sm')
        s.setPolarityFilter('positive')
        s.selectSymbol()
        s.resetFilter()
        if s.Selected_count():
            back_val = 0 - add_val
            # 解决锯齿状
            s.sel_options('clear_none')
            s.resize(back_val * 2)
            s.resize(add_val * 2)
            s.resize(back_val * 2)
            s.sel_options('clear_after')
        s.clearAll()
        # s.PAUSE('eend')
        # 最后恢复绿油(合起来),恢复线路,删除临时层
        for lay in setValue["runSmdLayerList"]:
            s.truncate_layer('tmp1')
            if lay == 'cs':
                soldName = 'cm'
                oksmlay = 'cm_ok_01'
                tmpsiglay = 'cs_tmp_01'
            elif lay == 'ss':
                soldName = 'sm'
                oksmlay = 'sm_ok_01'
                tmpsiglay = 'ss_tmp_01'
            s.affect(soldName)
            s.setPolarityFilter('positive')
            s.selectSymbol()
            s.resetFilter()
            if s.Selected_count():
                s.moveSel('tmp1')
            # 绿油
            s.copyLayer(job_name, step_name, oksmlay, 'tmp1', 'append')
            s.copyLayer(job_name, step_name, soldName, 'tmp1', 'append')
            s.copyLayer(job_name, step_name, 'tmp1', soldName)

            # 线路
            s.copyLayer(job_name, step_name, tmpsiglay, lay)
            s.clearAll()
            s.truncate_layer('tmp1')
            s.removeLayer(oksmlay)
            s.removeLayer(tmpsiglay)
        s.VOF()
        s.removeLayer('cm_ok_01')
        s.removeLayer('sm_ok_01')
        s.VON()
        # sys.exit()

    def DoSmdRunClearance(self):
        """制作smd开窗"""
        if not setValue["runSmdLayerList"]:
            return
        runLayStr = '\;'.join(setValue["runSmdLayerList"])
        Clearance_Opt_Value = (float(setValue["smdClearanceOpt"]) - float(setValue["smdCompensation"]) / 2)  # 大开窗大小单边
        Clearance_Min_Value = (
                float(setValue["smdSurfaceCoveEnlarge"]) - float(setValue["smdCompensation"]) / 2)  # 小开窗大小单边
        # Embedded_Value = 0
        # if Clearance_Min_Value < 0.1:
        #     # Embedded_Value = Clearance_Min_Value
        #     # Clearance_Min_Value = 0
        #     Embedded_Value = Clearance_Min_Value - 0.1
        #     Clearance_Min_Value = 0.1
        # Parameter_Clearance_min = 0
        add_val = 0  # 附加值 开窗整体附加 (因为小开窗在-0.1~0.1之间时 有些异性pad开窗不会加大)
        # if Clearance_Min_Value >= 0 and Clearance_Min_Value < 0.1:
        #     add_val = 0.1
        # elif Clearance_Min_Value < 0 and Clearance_Min_Value > -0.1:
        #     add_val = -0.1
        add_val = 0.1 - Clearance_Min_Value
        Clearance_Min_Value += add_val
        Clearance_Opt_Value += add_val
        # setValue['smdCoverageMin'] = str(float(setValue['smdCoverageMin']) + add_val)
        # setValue['smdCoverageOpt'] = str(float(setValue['smdCoverageOpt']) + add_val)

        s.COM("truncate_layer,layer=tmp1")
        s.COM("truncate_layer,layer=tmp2")
        s.COM("truncate_layer,layer=tmp3")
        s.COM("truncate_layer,layer=tmp4")
        s.COM("truncate_layer,layer=tmp5")
        s.clearAll()
        s.clearAndReset()
        for lay in setValue["runSmdLayerList"]:
            if lay == 'cs':
                s.COM("truncate_layer,layer=cm")
            elif lay == 'ss':
                s.COM("truncate_layer,layer=sm")
        # 防焊层加开窗############################################
        for lay in setValue["runSmdLayerList"]:
            if lay == 'cs':
                soldName = 'cm'
            elif lay == 'ss':
                soldName = 'sm'
            else:
                QMessageBox.warning(self, "warning", '已中止,%s层错误,不认识' % lay, QMessageBox.Ok)
                sys.exit()
            s.affect(lay)
            s.setAttrFilter('.smd')
            s.selectSymbol()
            s.resetFilter()
            if s.Selected_count():
                # if Clearance_Min_Value == 0:
                #     s.copyToLayer(soldName, size=0.001)
                # else:
                #     s.copyToLayer(soldName, size=Clearance_Min_Value * 2)
                s.copyToLayer(soldName, size=Clearance_Min_Value * 2)
            s.clearAll()
        s.clearAll()
        # s.PAUSE('111111111111 %s ' % Clearance_Min_Value )
        #########################################################
        if setValue["runSmdLayerList"]:
            # s.COM(" chklist_from_lib,chklist=system_sm,profile=none,customer=") 已经重新载入了
            s.COM(" chklist_open,chklist=system_sm")
            s.COM(" chklist_show,chklist=system_sm,nact=1,pinned=yes,pinned_enabled=yes")
            s.COM(" chklist_close,chklist=valor_analysis_sm,mode=hide")
            # s.COM(" chklist_cupd,chklist=system_sm,nact=1,params=((pp_layer="+runLayStr+")(pp_min_clear="+str(Clearance_Min_Value)+")(pp_opt_clear="+str(Clearance_Opt_Value)+")(pp_min_cover="+setValue['smdCoverageMin']+")(pp_opt_cover="+setValue['smdCoverageOpt']+")(pp_min_bridge="+setValue['smdBridgeMin']+")(pp_opt_bridge="+setValue['smdBridgeOpt']+")(pp_selected=All)(pp_use_mask=Yes)(pp_use_shave=Yes)(pp_shave_cu=)(pp_rerout_line=)(pp_min_cu_width=5)(pp_min_cu_spacing=2.5)(pp_min_pth_ar=5)(pp_min_via_ar=5)(pp_fix_coverage=PTH\;Via\;NPTH\;SMD\;BGA)(pp_fix_bridge=PTH\;Via\;NPTH\;SMD\;BGA)(pp_split_clr_for_pad=PTH\;Via\;SMD\;BGA\;Other)(pp_partial=)(pp_gasket_smd_as_regular=2)(pp_gasket_bga_as_regular=2)(pp_gasket_pth_as_regular=2)(pp_gasket_via_as_regular=2)(pp_do_small_clearances=)(pp_handle_same_size=)(pp_handle_embedded_as_regular=)(pp_partial_embedded_mode=Split Clearance)),mode=regular")
            s.COM(
                " chklist_cupd,chklist=system_sm,nact=1,params=((pp_layer=" + runLayStr + ")(pp_min_clear=0)(pp_opt_clear=" + str(
                    Clearance_Opt_Value) + ")(pp_min_cover=" + setValue['smdCoverageMin'] + ")(pp_opt_cover=" +
                setValue['smdCoverageOpt'] + ")(pp_min_bridge=" + setValue['smdBridgeMin'] + ")(pp_opt_bridge=" +
                setValue[
                    'smdBridgeOpt'] + ")(pp_selected=All)(pp_use_mask=Yes)(pp_use_shave=Yes)(pp_shave_cu=)(pp_rerout_line=)(pp_min_cu_width=5)(pp_min_cu_spacing=2.5)(pp_min_pth_ar=5)(pp_min_via_ar=5)(pp_fix_coverage=PTH\;Via\;NPTH\;SMD\;BGA)(pp_fix_bridge=PTH\;Via\;NPTH\;SMD\;BGA)(pp_split_clr_for_pad=PTH\;Via\;SMD\;BGA\;Other)(pp_partial=)(pp_gasket_smd_as_regular=2)(pp_gasket_bga_as_regular=2)(pp_gasket_pth_as_regular=2)(pp_gasket_via_as_regular=2)(pp_do_small_clearances=)(pp_handle_same_size=)(pp_handle_embedded_as_regular=)(pp_partial_embedded_mode=Split Clearance)),mode=regular")
            # s.COM(" chklist_erf_variable,chklist=system_sm,nact=1,variable=v_enlarge_embedded_pth,value="+str(Embedded_Value)+",options=0")
            # s.COM(" chklist_erf_variable,chklist=system_sm,nact=1,variable=v_enlarge_embedded_smd,value="+str(Embedded_Value)+",options=0")
            # s.COM(" chklist_erf_variable,chklist=system_sm,nact=1,variable=v_enlarge_embedded_bga,value="+str(Embedded_Value)+",options=0")
            # s.COM(" chklist_erf_variable,chklist=system_sm,nact=1,variable=v_enlarge_embedded_via,value="+str(Embedded_Value)+",options=0")
            # s.COM(" chklist_erf_variable,chklist=system_sm,nact=1,variable=v_enlarge_embedded_normal,value="+str(Embedded_Value)+",options=0")
            # s.COM(" chklist_erf_variable,chklist=system_sm,nact=1,variable=v_split_embedded_pth,value="+str(Embedded_Value)+",options=0")
            # s.COM(" chklist_erf_variable,chklist=system_sm,nact=1,variable=v_split_embedded_smd,value="+str(Embedded_Value)+",options=0")
            # s.COM(" chklist_erf_variable,chklist=system_sm,nact=1,variable=v_split_embedded_bga,value="+str(Embedded_Value)+",options=0")
            # s.COM(" chklist_erf_variable,chklist=system_sm,nact=1,variable=v_split_embedded_via,value="+str(Embedded_Value)+",options=0")
            # s.COM(" chklist_erf_variable,chklist=system_sm,nact=1,variable=v_split_embedded_normal,value="+str(Embedded_Value)+",options=0")
            s.COM(" chklist_erf_variable,chklist=system_sm,nact=1,variable=min_trace_to_split,value=" + setValue[
                'smdTraceSplitMin'] + ",options=0")
            s.COM(" chklist_cnf_act,chklist=system_sm,nact=1,cnf=no")

            s.COM(" chklist_run,chklist=system_sm,nact=1,area=global,async_run=yes")
            #  s.PAUSE('1')
            #########################################################

            # contruct smd 不开小窗解决办法
            for lay in setValue["runSmdLayerList"]:
                s.affect(lay)
            s.setPolarityFilter('positive')
            s.setAttrFilter('.smd')
            # s.selectSymbol()
            s.selectSymbol('construct*')
            s.resetFilter()
            if s.Selected_count():
                s.COM(" chklist_open,chklist=system_sm")
                s.COM(" chklist_show,chklist=system_sm,nact=8,pinned=yes,pinned_enabled=yes")
                s.COM(" chklist_close,chklist=valor_analysis_sm,mode=hide")
                s.COM(" chklist_cupd,chklist=system_sm,nact=8,params=((pp_layer=" + runLayStr + ")(pp_min_clear=" + str(
                    Clearance_Opt_Value) + ")(pp_opt_clear=" + str(Clearance_Opt_Value) + ")(pp_min_cover=" + setValue[
                          'smdCoverageMin'] + ")(pp_opt_cover=" + setValue['smdCoverageOpt'] + ")(pp_min_bridge=" +
                      setValue['smdBridgeMin'] + ")(pp_opt_bridge=" + setValue[
                          'smdBridgeOpt'] + ")(pp_selected=Selected)(pp_use_mask=Yes)(pp_use_shave=Yes)(pp_shave_cu=)(pp_rerout_line=)(pp_min_cu_width=5)(pp_min_cu_spacing=2.5)(pp_min_pth_ar=5)(pp_min_via_ar=5)(pp_fix_coverage=PTH\;Via\;NPTH\;SMD\;BGA)(pp_fix_bridge=PTH\;Via\;NPTH\;SMD\;BGA)(pp_split_clr_for_pad=PTH\;Via\;SMD\;BGA\;Other)(pp_partial=)(pp_gasket_smd_as_regular=2)(pp_gasket_bga_as_regular=2)(pp_gasket_pth_as_regular=2)(pp_gasket_via_as_regular=2)(pp_do_small_clearances=)(pp_handle_same_size=)(pp_handle_embedded_as_regular=)(pp_partial_embedded_mode=Split Clearance)),mode=regular")
                s.COM(" chklist_erf_variable,chklist=system_sm,nact=8,variable=v_enlarge_embedded_pth,value=" + str(
                    Clearance_Min_Value) + ",options=0")
                s.COM(" chklist_erf_variable,chklist=system_sm,nact=8,variable=v_enlarge_embedded_smd,value=" + str(
                    Clearance_Min_Value) + ",options=0")
                s.COM(" chklist_erf_variable,chklist=system_sm,nact=8,variable=v_enlarge_embedded_bga,value=" + str(
                    Clearance_Min_Value) + ",options=0")
                s.COM(" chklist_erf_variable,chklist=system_sm,nact=8,variable=v_enlarge_embedded_via,value=" + str(
                    Clearance_Min_Value) + ",options=0")
                s.COM(" chklist_erf_variable,chklist=system_sm,nact=8,variable=v_enlarge_embedded_normal,value=" + str(
                    Clearance_Min_Value) + ",options=0")
                s.COM(" chklist_erf_variable,chklist=system_sm,nact=8,variable=v_split_embedded_pth,value=" + str(
                    Clearance_Min_Value) + ",options=0")
                s.COM(" chklist_erf_variable,chklist=system_sm,nact=8,variable=v_split_embedded_smd,value=" + str(
                    Clearance_Min_Value) + ",options=0")
                s.COM(" chklist_erf_variable,chklist=system_sm,nact=8,variable=v_split_embedded_bga,value=" + str(
                    Clearance_Min_Value) + ",options=0")
                s.COM(" chklist_erf_variable,chklist=system_sm,nact=8,variable=v_split_embedded_via,value=" + str(
                    Clearance_Min_Value) + ",options=0")
                s.COM(" chklist_erf_variable,chklist=system_sm,nact=8,variable=v_split_embedded_normal,value=" + str(
                    Clearance_Min_Value) + ",options=0")
                s.COM(" chklist_erf_variable,chklist=system_sm,nact=8,variable=min_trace_to_split,value=" + setValue[
                    'smdTraceSplitMin'] + ",options=0")
                s.COM(" chklist_cnf_act,chklist=system_sm,nact=8,cnf=no")
                s.COM(" chklist_run,chklist=system_sm,nact=8,area=global,async_run=yes")
                # Embedded_Value
                # 将负片浮上来
                s.clearAll()
                s.COM("truncate_layer,layer=tmp1")
                for lay in setValue["runSmdLayerList"]:
                    if lay == 'cs':
                        soldName = 'cm'
                    elif lay == 'ss':
                        soldName = 'sm'
                    s.affect(soldName)
                    s.setPolarityFilter('negative')
                    s.selectSymbol()
                    s.resetFilter()
                    if s.Selected_count():
                        s.moveSel('tmp1')
                    s.copyLayer(job_name, step_name, 'tmp1', soldName, 'append')
                    s.clearAll()
                    s.COM("truncate_layer,layer=tmp1")
                s.clearAll()
            s.clearAll()

            # s.PAUSE('111')

            #####################################################

            # # 减回附加值
            # for lay in setValue["runSmdLayerList"]:
            #     if lay == 'cs':
            #         s.affect('cm')
            #     elif lay == 'ss':
            #         s.affect('sm')
            # s.setPolarityFilter('positive')
            # s.PAUSE('ESA')
            # s.selectSymbol()
            # s.resetFilter()
            # if s.Selected_count():
            #     back_val = 0 - add_val
            #     #解决锯齿状
            #     s.sel_options('clear_none')
            #     s.PAUSE('ESA2')
            #     s.resize(back_val * 2)
            #     s.PAUSE('ESA3')
            #     s.resize(add_val * 2)
            #     s.PAUSE('ESA4')
            #     s.resize(back_val * 2)
            #     s.PAUSE('ESA5')
            #     s.sel_options('clear_after')
            # s.clearAll()

            myayrtmp = ''
            # s.PAUSE(setValue["smdCompensation"])
            if float(setValue["smdCompensation"]) >= 3.5:  ### YLC 增加去细丝步骤 2021-7-16 11:58:07
                for lay in setValue["runSmdLayerList"]:
                    if lay == 'cs':
                        myayrtmp = 'cm'
                    elif lay == 'ss':
                        myayrtmp = 'sm'

                    s.affect(myayrtmp)

                    s.setPolarityFilter('negative')
                    s.selectSymbol()
                    s.resetFilter()
                    if s.Selected_count():
                        s.moveSel(myayrtmp + pid)
                    back_val = 0 - add_val
                    s.resize(back_val * 2)
                    s.COM(
                        "sel_fill, type = solid, solid_type = fill, min_brush = 1, use_arcs = yes, cut_prims = no, outline_draw = yes, outline_width = 0, outline_invert = no")

                    s.Contourize(0.25, 'yes', 3)
                    s.resize(add_val * 2)
                    s.clearAll()
                    if s.isLayer(myayrtmp + pid):
                        s.affect(myayrtmp + pid)
                        s.copyToLayer(myayrtmp)
                        s.clearAll()
                    s.clearAll()

            # # 减回附加值
            for lay in setValue["runSmdLayerList"]:
                if lay == 'cs':
                    s.affect('cm')
                elif lay == 'ss':
                    s.affect('sm')
            s.setPolarityFilter('positive')
            # s.PAUSE('ESA')
            s.selectSymbol()
            s.resetFilter()
            if s.Selected_count():
                back_val = 0 - add_val
                # 解决锯齿状
                s.sel_options('clear_none')

                s.resize(back_val * 2)

                s.resize(add_val * 2)

                s.resize(back_val * 2)

                s.sel_options('clear_after')
            s.clearAll()

    def DoAddSmallSmd(self):
        """加上小开窗"""
        s.truncate_layer('tmp1')
        s.truncate_layer('tmp2')
        s.truncate_layer('tmp3')
        s.truncate_layer('tmp4')
        Clearance_Min_Value = (
                float(setValue["smdSurfaceCoveEnlarge"]) - float(setValue["smdCompensation"]) / 2)  # 小开窗大小单边

        for layerName in setValue["runSmdLayerList"]:
            if layerName == 'cs':
                solderLayName = 'cm'
            elif layerName == 'ss':
                solderLayName = 'sm'

            # 加上小开窗
            s.affect(layerName)
            s.setAttrFilter('.smd')
            s.selectSymbol()
            s.resetFilter()
            if s.Selected_count():
                s.copyToLayer('tmp1', size=Clearance_Min_Value * 2)
                s.clearAll()
                s.copyLayer(job_name, step_name, solderLayName, 'tmp1', 'append')
                s.copyLayer(job_name, step_name, 'tmp1', solderLayName)
            s.truncate_layer('tmp1')
            s.clearAll()

    def DoCheckNegativeSmdAndBga(self):
        """检测是否存在负性smd ,bga"""
        s.clearAndReset()
        s.clearAll()
        if 'cs' in setValue["runSmdLayerList"] or 'cs' in setValue["runBgaLayerList"]:
            s.affect('cs')
            s.setAttrFilter('.smd')
            s.setPolarityFilter('negative')
            s.selectSymbol('')
            if s.Selected_count():
                QMessageBox.warning(self, "warning", '已中止,检测到有负性smd', QMessageBox.Ok)
                s.resetFilter()
                sys.exit()
        if 'ss' in setValue["runSmdLayerList"] or 'cs' in setValue["runBgaLayerList"]:
            s.affect('ss')
            s.setAttrFilter('.smd')
            s.setPolarityFilter('negative')
            s.selectSymbol('')
            if s.Selected_count():
                QMessageBox.warning(self, "warning", '已中止,检测到有负性smd', QMessageBox.Ok)
                s.resetFilter()
                sys.exit()
        s.clearAll()
        s.clearAndReset()

    def DoStart(self):
        setValue["smdClearanceMin"] = self.group1_lined1.text()
        setValue["smdClearanceOpt"] = self.group1_lined2.text()
        setValue["smdCoverageMin"] = self.group1_lined3.text()
        setValue["smdCoverageOpt"] = self.group1_lined4.text()
        setValue["smdBridgeMin"] = self.group1_lined5.text()
        setValue["smdBridgeOpt"] = self.group1_lined6.text()
        setValue["smdTraceSplitMin"] = self.group1_lined7.text()
        setValue["bgaClearanceMin"] = self.group2_lined1.text()
        setValue["bgaClearanceOpt"] = self.group2_lined2.text()
        setValue["bgaCoverageMin"] = self.group2_lined3.text()
        setValue["bgaCoverageOpt"] = self.group2_lined4.text()
        setValue["bgaBridgeMin"] = self.group2_lined5.text()
        setValue["bgaBridgeOpt"] = self.group2_lined6.text()
        setValue["bgaTraceSplitMin"] = self.group2_lined7.text()
        setValue["smdCompensation"] = self.group3_lined1.text()
        setValue["bgaCompensation"] = self.group3_lined2.text()
        setValue["smdSurfaceCoveEnlarge"] = self.group3_lined3.text()
        setValue["bgaSurfaceCoveEnlarge"] = self.group3_lined4.text()
        setValue["runSmdLayerList"] = []
        setValue["runBgaLayerList"] = []
        if self.hbox1_checkBoxTopSmd.isChecked():
            setValue["runSmdLayerList"].append('cs')
        if self.hbox1_checkBoxBotSmd.isChecked():
            setValue["runSmdLayerList"].append('ss')
        if self.hbox1_checkBoxTopBga.isChecked():
            setValue["runBgaLayerList"].append('cs')
        if self.hbox1_checkBoxBotBga.isChecked():
            setValue["runBgaLayerList"].append('ss')
        if setValue["runBgaLayerList"] == [] and setValue["runSmdLayerList"] == []:
            QMessageBox.warning(self, "warning", '啥也不用跑!', QMessageBox.Ok)
            sys.exit()

        setValue["runAllLayerList"] = list(set(setValue["runSmdLayerList"] + setValue["runBgaLayerList"]))
        if self.hbox_radio_radio1.isChecked():
            setValue["bgaShape"] = "round"  # 圆形
        else:
            setValue["bgaShape"] = "square"  # 方形

        if 'cs' in setValue["runSmdLayerList"] or 'cs' in setValue["runBgaLayerList"]:
            if s.isLayer('cm'):
                if s.isLayer('cm_bf'):
                    s.removeLayer('cm_bf')
                s.copyLayer(job_name, step_name, 'cm', 'cm_bf')
            if s.isLayer('cs_bf'):
                s.removeLayer('cs_bf')
            s.copyLayer(job_name, step_name, 'cs', 'cs_bf')
        if 'ss' in setValue["runSmdLayerList"] or 'ss' in setValue["runBgaLayerList"]:
            if s.isLayer('ss_bf'):
                s.removeLayer('ss_bf')
            s.copyLayer(job_name, step_name, 'ss', 'ss_bf')
            if s.isLayer('sm'):
                if s.isLayer('sm_bf'):
                    s.removeLayer('sm_bf')
                s.copyLayer(job_name, step_name, 'sm', 'sm_bf')
        for i in ['tmp1', 'tmp2', 'tmp3', 'tmp4', 'tmp5']:
            if s.isLayer(i):
                s.removeLayer(i)
            s.createLayer(i, laytype='signal')
        for i in ['cm_smd_ok', 'sm_smd_ok', 'cm_bga_ok', 'sm_bga_ok', 'cs_shrink_pre', 'ss_shrink_pre', 'cm_smd_cover',
                  'sm_smd_cover']:
            if s.isLayer(i):
                s.removeLayer(i)
            s.createLayer(i)

        if 'system_sm' in s.getChecks():
            s.COM(" chklist_delete,chklist=system_sm")
        s.COM(" chklist_from_lib,chklist=system_sm,profile=none,customer=")
        s.COM(" chklist_open,chklist=system_sm")

        if 'sm_hmx' in s.getChecks():
            s.COM(" chklist_delete,chklist=sm_hmx")
        s.COM(" chklist_from_lib,chklist=sm_hmx,profile=none,customer=")
        s.COM(" chklist_open,chklist=sm_hmx")

    def DoUpdataCheckBox(self):
        """初始化checkbox"""
        self.hbox1_checkBoxTopSmd.setChecked(0)
        self.hbox1_checkBoxTopBga.setChecked(0)
        self.hbox1_checkBoxBotSmd.setChecked(0)
        self.hbox1_checkBoxBotBga.setChecked(0)

        self.hbox1_checkBoxTopSmd.setEnabled(0)
        self.hbox1_checkBoxTopBga.setEnabled(0)
        self.hbox1_checkBoxBotSmd.setEnabled(0)
        self.hbox1_checkBoxBotBga.setEnabled(0)

        s.clearAll()
        s.clearAndReset()
        s.setUnits('inch')

        if s.isLayer('cs'):
            info = s.Features_INFO('cs', all=1)
            # info = s.INFO(' -t layer -e ' + job_name + '/' + step_name + '/%s -d FEATURES' % 'cs')
            for i in info:
                text = ' '.join(i)
                if re.search(r'\.smd', text):
                    self.hbox1_checkBoxTopSmd.setChecked(1)
                    self.hbox1_checkBoxTopSmd.setEnabled(1)
                    break
            for i in info:
                text = ' '.join(i)
                if re.search(r'\.bga', text):
                    self.hbox1_checkBoxTopBga.setChecked(1)
                    self.hbox1_checkBoxTopBga.setEnabled(1)
                    break
        if s.isLayer('ss'):
            info = s.Features_INFO('ss', all=1)
            for i in info:
                text = ' '.join(i)
                if re.search(r'\.smd', text):
                    self.hbox1_checkBoxBotSmd.setChecked(1)
                    self.hbox1_checkBoxBotSmd.setEnabled(1)
                    break
            for i in info:
                text = ' '.join(i)
                if re.search(r'\.bga', text):
                    self.hbox1_checkBoxBotBga.setChecked(1)
                    self.hbox1_checkBoxBotBga.setEnabled(1)
                    break

    def DoExit(self):
        sys.exit()

    def DoPause(self):
        self.hide()
        s.PAUSE('你已暂停!')
        self.show()

    def DoChangeRadio(self, myWidget):
        """圆形 or 方形"""
        if myWidget == self.hbox_radio_radio1:
            self.hbox_radio_radio1.setChecked(1)
            self.hbox_radio_radio2.setChecked(0)
        else:
            self.hbox_radio_radio1.setChecked(0)
            self.hbox_radio_radio2.setChecked(1)

    def DoGui(self):
        # 控件
        self.frame1 = QFrame(self)
        self.grid1 = QGridLayout(self.frame1)

        self.group1 = QGroupBox("SMD")
        self.group2 = QGroupBox("BGA")
        self.group3 = QGroupBox("补偿")

        self.group1_grid1 = QGridLayout()
        self.group1_lab1 = QLabel("最小值")
        self.group1_lab2 = QLabel("最优值")
        self.group1_lab3 = QLabel("开窗:")
        self.group1_lab4 = QLabel("盖线:")
        self.group1_lab5 = QLabel("桥:")
        self.group1_lab6 = QLabel("SMD开小窗连线:")
        self.group1_lab7 = QLabel("MIL")
        self.group1_lab8 = QLabel("MIL")
        self.group1_lab9 = QLabel("MIL")
        self.group1_lab10 = QLabel("MIL")
        self.group1_lined1 = QLineEdit(setValue["smdClearanceMin"])
        self.group1_lined2 = QLineEdit(setValue["smdClearanceOpt"])
        self.group1_lined3 = QLineEdit(setValue["smdCoverageMin"])
        self.group1_lined4 = QLineEdit(setValue["smdCoverageOpt"])
        self.group1_lined5 = QLineEdit(setValue["smdBridgeMin"])
        self.group1_lined6 = QLineEdit(setValue["smdBridgeOpt"])
        self.group1_lined7 = QLineEdit(setValue["smdTraceSplitMin"])

        self.group2_grid1 = QGridLayout()
        self.group2_lab0 = QLabel("类型:")
        self.group2_lab1 = QLabel("最小值")
        self.group2_lab2 = QLabel("最优值")
        self.group2_lab3 = QLabel("开窗:")
        self.group2_lab4 = QLabel("盖线:")
        self.group2_lab5 = QLabel("桥:")
        self.group2_lab6 = QLabel("BGA开小窗连线:")
        self.group2_lab7 = QLabel("MIL")
        self.group2_lab8 = QLabel("MIL")
        self.group2_lab9 = QLabel("MIL")
        self.group2_lab10 = QLabel("MIL")

        self.group2_lined1 = QLineEdit(setValue["bgaClearanceMin"])
        self.group2_lined2 = QLineEdit(setValue["bgaClearanceOpt"])
        self.group2_lined3 = QLineEdit(setValue["bgaCoverageMin"])
        self.group2_lined4 = QLineEdit(setValue["bgaCoverageOpt"])
        self.group2_lined5 = QLineEdit(setValue["bgaBridgeMin"])
        self.group2_lined6 = QLineEdit(setValue["bgaBridgeOpt"])
        self.group2_lined7 = QLineEdit(setValue["bgaTraceSplitMin"])

        self.group3_grid1 = QGridLayout()
        self.group3_lab1 = QLabel("SMD振粗:")
        self.group3_lab2 = QLabel("BGA振粗:")
        self.group3_lab3 = QLabel("铜皮内SMD开窗:")
        self.group3_lab4 = QLabel("铜皮内BGA开窗:")
        self.group3_lab5 = QLabel("MIL")
        self.group3_lab6 = QLabel("MIL")
        self.group3_lab7 = QLabel("MIL")
        self.group3_lab8 = QLabel("MIL")
        self.group3_lined1 = QLineEdit(setValue["smdCompensation"])
        self.group3_lined2 = QLineEdit(setValue["bgaCompensation"])
        self.group3_lined3 = QLineEdit(setValue["smdSurfaceCoveEnlarge"])
        self.group3_lined4 = QLineEdit(setValue["bgaSurfaceCoveEnlarge"])

        self.hbox_radio = QHBoxLayout()
        self.hbox_radio_radio1 = QCheckBox('圆形')
        self.hbox_radio_radio2 = QCheckBox('方形')

        self.hbox1 = QHBoxLayout()
        self.hbox1_lab1 = QLabel("Top面:")
        self.hbox1_checkBoxTopSmd = QCheckBox("SMD")
        self.hbox1_checkBoxTopBga = QCheckBox("BGA")
        self.hbox1_lab2 = QLabel("Bot面:")
        self.hbox1_checkBoxBotSmd = QCheckBox("SMD")
        self.hbox1_checkBoxBotBga = QCheckBox("BGA")

        self.hbox2 = QHBoxLayout()
        self.hbox2_lab1 = QLabel(job_name + '   油墨颜色: ')
        self.hbox2_lab2 = QComboBox()
        self.hbox2_lab2.addItems(['绿色', '蓝色', '黄色', '黑色'])
        # self.hbox2_lab3 = QLabel('未知')
        self.hbox3 = QHBoxLayout()
        self.appButton = QPushButton("开始")
        self.pauseButton = QPushButton("暂停")
        self.exitButton = QPushButton("退出")
        # 属性
        self.hbox1_lab1.setObjectName('L1')
        self.hbox1_lab2.setObjectName('L1')
        self.hbox_radio_radio1.setObjectName('R1')
        self.hbox_radio_radio2.setObjectName('R1')
        self.hbox_radio_radio1.setChecked(1)
        # self.hbox2_lab1.setAlignment(Qt.AlignCenter)
        # self.hbox2_lab2.setAlignment(Qt.AlignCenter)
        self.hbox2_lab1.setObjectName('L2')
        self.hbox2_lab2.setObjectName('L3')
        # self.hbox2_lab3.setObjectName('L3')
        self.hbox2.setSpacing(0)
        # 布局
        self.grid1.addLayout(self.hbox2, 0, 1)
        self.grid1.addWidget(self.group1, 1, 1)
        self.grid1.addWidget(self.group2, 2, 1)
        self.grid1.addWidget(self.group3, 3, 1)
        self.grid1.addLayout(self.hbox1, 4, 1)
        self.grid1.addLayout(self.hbox3, 5, 1)

        self.group1.setLayout(self.group1_grid1)
        self.group1_grid1.addWidget(self.group1_lab1, 0, 1, 1, 1, Qt.AlignCenter)
        self.group1_grid1.addWidget(self.group1_lab2, 0, 2, 1, 1, Qt.AlignCenter)
        self.group1_grid1.addWidget(self.group1_lab3, 1, 0, 1, 1, Qt.AlignRight)
        self.group1_grid1.addWidget(self.group1_lab4, 2, 0, 1, 1, Qt.AlignRight)
        self.group1_grid1.addWidget(self.group1_lab5, 3, 0, 1, 1, Qt.AlignRight)
        self.group1_grid1.addWidget(self.group1_lab6, 4, 0, 1, 1, Qt.AlignRight)
        self.group1_grid1.addWidget(self.group1_lab7, 1, 3, 1, 1, Qt.AlignLeft)
        self.group1_grid1.addWidget(self.group1_lab8, 2, 3, 1, 1, Qt.AlignLeft)
        self.group1_grid1.addWidget(self.group1_lab9, 3, 3, 1, 1, Qt.AlignLeft)
        self.group1_grid1.addWidget(self.group1_lab10, 4, 3, 1, 1, Qt.AlignLeft)
        self.group1_grid1.addWidget(self.group1_lined1, 1, 1, 1, 1)
        self.group1_grid1.addWidget(self.group1_lined2, 1, 2, 1, 1)
        self.group1_grid1.addWidget(self.group1_lined3, 2, 1, 1, 1)
        self.group1_grid1.addWidget(self.group1_lined4, 2, 2, 1, 1)
        self.group1_grid1.addWidget(self.group1_lined5, 3, 1, 1, 1)
        self.group1_grid1.addWidget(self.group1_lined6, 3, 2, 1, 1)
        self.group1_grid1.addWidget(self.group1_lined7, 4, 1, 1, 2)

        self.group2.setLayout(self.group2_grid1)
        # self.group2_grid1.addWidget(self.group2_lab1, 0, 1, 1, 1, Qt.AlignCenter)
        # self.group2_grid1.addWidget(self.group2_lab2, 0, 2, 1, 1, Qt.AlignCenter)
        # self.group2_grid1.addLayout(self.hbox_radio,  0, 1, 1, 2)
        # self.group2_grid1.addWidget(self.group2_lab0, 0, 0, 1, 1, Qt.AlignRight)
        self.group2_grid1.addWidget(self.group2_lab3, 1, 0, 1, 1, Qt.AlignRight)
        self.group2_grid1.addWidget(self.group2_lab4, 2, 0, 1, 1, Qt.AlignRight)
        self.group2_grid1.addWidget(self.group2_lab5, 3, 0, 1, 1, Qt.AlignRight)
        self.group2_grid1.addWidget(self.group2_lab6, 4, 0, 1, 1, Qt.AlignRight)
        self.group2_grid1.addWidget(self.group2_lab7, 1, 3, 1, 1, Qt.AlignLeft)
        self.group2_grid1.addWidget(self.group2_lab8, 2, 3, 1, 1, Qt.AlignLeft)
        self.group2_grid1.addWidget(self.group2_lab9, 3, 3, 1, 1, Qt.AlignLeft)
        self.group2_grid1.addWidget(self.group2_lab10, 4, 3, 1, 1, Qt.AlignLeft)
        self.group2_grid1.addWidget(self.group2_lined1, 1, 1, 1, 1)
        self.group2_grid1.addWidget(self.group2_lined2, 1, 2, 1, 1)
        self.group2_grid1.addWidget(self.group2_lined3, 2, 1, 1, 1)
        self.group2_grid1.addWidget(self.group2_lined4, 2, 2, 1, 1)
        self.group2_grid1.addWidget(self.group2_lined5, 3, 1, 1, 1)
        self.group2_grid1.addWidget(self.group2_lined6, 3, 2, 1, 1)
        self.group2_grid1.addWidget(self.group2_lined7, 4, 1, 1, 2)
        # self.group2_grid1.addLayout(self.hbox_radio, 4, 2, 1, 2)
        # self.hbox_radio.addWidget(self.group2_lab10)
        # self.hbox_radio.addStretch(1)
        # self.hbox_radio.addWidget(self.hbox_radio_radio1)
        # self.hbox_radio.addWidget(self.hbox_radio_radio2)
        self.group3.setLayout(self.group3_grid1)
        self.group3_grid1.addWidget(self.group3_lab1, 0, 0, 1, 1, Qt.AlignRight)
        self.group3_grid1.addWidget(self.group3_lab2, 1, 0, 1, 1, Qt.AlignRight)
        self.group3_grid1.addWidget(self.group3_lab3, 2, 0, 1, 1, Qt.AlignRight)
        self.group3_grid1.addWidget(self.group3_lab4, 3, 0, 1, 1, Qt.AlignRight)
        self.group3_grid1.addWidget(self.group3_lab5, 0, 2, 1, 1, Qt.AlignLeft)
        self.group3_grid1.addWidget(self.group3_lab6, 1, 2, 1, 1, Qt.AlignLeft)
        self.group3_grid1.addWidget(self.group3_lab7, 2, 2, 1, 1, Qt.AlignLeft)
        self.group3_grid1.addWidget(self.group3_lab8, 3, 2, 1, 1, Qt.AlignLeft)
        self.group3_grid1.addWidget(self.group3_lined1, 0, 1, 1, 1)
        self.group3_grid1.addWidget(self.group3_lined2, 1, 1, 1, 1)
        self.group3_grid1.addWidget(self.group3_lined3, 2, 1, 1, 1)
        self.group3_grid1.addWidget(self.group3_lined4, 3, 1, 1, 1)

        self.hbox1.addWidget(self.hbox1_lab1)
        self.hbox1.addWidget(self.hbox1_checkBoxTopSmd)
        self.hbox1.addWidget(self.hbox1_checkBoxTopBga)
        self.hbox1.addStretch(1)
        self.hbox1.addWidget(self.hbox1_lab2)
        self.hbox1.addWidget(self.hbox1_checkBoxBotSmd)
        self.hbox1.addWidget(self.hbox1_checkBoxBotBga)

        # self.hbox2.addStretch(1)
        self.hbox2.addWidget(self.hbox2_lab1)
        self.hbox2.addWidget(self.hbox2_lab2)
        # self.hbox2.addWidget(self.hbox2_lab3)
        self.hbox2.addStretch(1)
        self.hbox3.addWidget(self.appButton)
        self.hbox3.addWidget(self.pauseButton)
        self.hbox3.addWidget(self.exitButton)
        # 槽函数
        self.exitButton.clicked.connect(self.DoExit)
        self.pauseButton.clicked.connect(self.DoPause)
        self.appButton.clicked.connect(self.DoApp)
        self.hbox_radio_radio1.clicked.connect(lambda: self.DoChangeRadio(self.hbox_radio_radio1))
        self.hbox_radio_radio2.clicked.connect(lambda: self.DoChangeRadio(self.hbox_radio_radio2))
        self.group1_lined1.textChanged.connect(lambda: self.DoTextChangeSmd())
        self.group1_lined2.textChanged.connect(lambda: self.DoTextChangeSmd())
        self.group2_lined1.textChanged.connect(lambda: self.DoTextChangeBga())
        self.group2_lined2.textChanged.connect(lambda: self.DoTextChangeBga())
        # 样式
        self.setStyleSheet(
            'QWidget{font: 10pt "WenQuanYi Zen Hei";background:#CDD2E4;}'  # background:#52CEAF
            'QGroupBox{color:#990000}'
            'QCheckBox#R1{color:#138535 }'  # E54747
            'QLineEdit{background:#ffffff;}'
            'QLabel#L1{color:#00A47B;}'
            'QLabel#L2{color:#000000}'
            'QLabel#L3{color:#138535;font:10pt }'
        )
        # background:#FAE387
        self.DoUpdataCheckBox()  # 初始

    def DoTextChangeSmd(self):
        # 开窗最小值 最优值一样大
        text = self.sender().text()
        self.group1_lined1.setText(text)
        self.group1_lined2.setText(text)

    def DoTextChangeBga(self):
        # 开窗最小值 最优值一样大
        text = self.sender().text()
        self.group2_lined1.setText(text)
        self.group2_lined2.setText(text)


if __name__ == '__main__':
    f = genClasses
    pid = str(f.Top().pid)
    # f.Top().PAUSE(pid)
    if 'JOB' not in os.environ.keys():
        f.Top().PAUSE('Did not open JOB!')
        sys.exit()
    job_name = os.environ.get('JOB')
    job = f.Job(job_name)
    if 'STEP' not in os.environ.keys():
        f.Top().PAUSE('Did not open STEP!')
        sys.exit()
    step_name = os.environ.get('STEP')
    s = job.steps[step_name]
    setValue = {
        "smdClearanceMin": "2.2",
        "smdClearanceOpt": "2.2",
        "smdCoverageMin": "1.83",
        "smdCoverageOpt": "1.83",
        "smdBridgeMin": "2.51",
        "smdBridgeOpt": "2.51",
        "smdTraceSplitMin": "1",
        "bgaClearanceMin": "2.2",
        "bgaClearanceOpt": "2.2",
        "bgaCoverageMin": "1.52",
        "bgaCoverageOpt": "1.52",
        "bgaBridgeMin": "1.51",
        "bgaBridgeOpt": "1.51",
        "bgaTraceSplitMin": "1",
        "smdCompensation": "1.6",
        "bgaCompensation": "1.9",
        "smdSurfaceCoveEnlarge": "0.6",
        "bgaSurfaceCoveEnlarge": "0.6",
    }
    if re.search(r'.jt', job_name):
        setValue['smdSurfaceCoveEnlarge'] = '0.8'
        setValue['bgaSurfaceCoveEnlarge'] = '0.8'

    # # 上传记录
    # userName = f.Top().getUser()
    # DBI = pymysql.connect('192.168.8.200', 'root', 'redboard', 'ppe', charset='utf8')
    # cursor = DBI.cursor()
    # Sql = "insert into redboardppe.camact (JOBNAME,STEPNAME,USERNAME,act,scripts,hosts) values( '%s','%s','%s','Start','/genesis/sys/scripts/hmx/python/camRunIncamSignalDynamic.py','incam')" % (job_name, step_name, userName)
    # cursor.execute(Sql)
    # DBI.commit()
    # DBI.close()
    # 油墨颜色
    sm_color = '黑色'
    if '黑' in sm_color:
        setValue['smdBridgeMin'] = '3.51'
        setValue['smdBridgeOpt'] = '3.51'
        setValue['bgaBridgeMin'] = '2.01'
        setValue['bgaBridgeOpt'] = '2.01'
    elif '哑绿色' in sm_color:
        setValue['smdBridgeMin'] = '3'
        setValue['smdBridgeOpt'] = '3'
    # 铜厚
    cu_thickness = 2
    if cu_thickness >= 2:
        setValue['smdClearanceMin'] = '3'
        setValue['smdClearanceOpt'] = '3'

        setValue['bgaClearanceMin'] = '3'
        setValue['bgaClearanceOpt'] = '3'

    app = QApplication(sys.argv)
    app.setStyle('fusion')
    ex = CamApp()
    ex.show()
    sys.exit(app.exec_())
