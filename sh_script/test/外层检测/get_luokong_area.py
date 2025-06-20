#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --加载相对位置，以实现InCAM与Genesis共用

import os
import platform
import sys
import itertools
import math
import re
from pprint import pprint
from datetime import datetime

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
    sys.path.append(r"Z:/incam/Path/OracleClient_x86/instantclient_11_1")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

# --参考料号m190/083b3;b06/202f2;a86/115a2(edit中有ww)
# --多层797/037a3待完善
import Oracle_DB
import genCOM_26 as genCOM
from collections import defaultdict,namedtuple
from operator import attrgetter


class create_luokong_layer(object):
    def __init__(self, parent=None, stepname=None):        
        self.JOB = os.environ.get('JOB', None)
        self.STEP = stepname if stepname else os.environ.get('STEP', None)
        self.JOB_SQL = self.JOB.upper()[:13]  # --截取前十三位料号名
        # self.JOB = 'SB2520GN003C1'
        # self.STEP = 'set'
        self.comBox = {}
        self.item_shape = {}
        self.item_pitch = {}
        self.layer_number = int(self.JOB[4:6])
        self.outer = ['l1','l%s' % self.layer_number]
        self.GEN = genCOM.GEN_COM()

        # --Oracle相关参数定义
        self.DB_O = Oracle_DB.ORACLE_INIT()
        self.dbc_o = self.DB_O.DB_CONNECT(host='172.20.218.193', servername='inmind.fls', port='1521',
                                          username='GETDATA', passwd='InplanAdmin')
        # --基本检测
        # self.checkEnv()

        # --参数配置文件定义
        self.cwd = os.path.dirname(sys.argv[0])

        # self.ui = FormUi.Ui_Form()
        # self.ui.setupUi(self)

        # --添加动态子部件
        # self.addPart_Ui()

        # --设置版本信息
        self.appVersion = 'V1.02'
        # date_today = datetime.strftime(datetime.now(),"%Y.%m.%d")
        # self.ui.topLabel.setText(u'Set自动铺铜程序 @ %s' % self.JOB)
        # self.ui.bottomLabel.setText(u'版权所有：胜宏科技 作者：Michael 日期：%s 版本：%s' % (date_today,self.appVersion))
        # self.setWindowTitle(u'Set自动铺铜程序 %s' % self.appVersion)

        # --定义临时层别
        self.fill_set_300um = 'fill_set_300um'
        self.fill_SR_lyr = 'fill_sr'
        self.fill_SR_cover = 'fill_sr_cover'
        self.tab_connect = 'tab_connect'
        self.fill_connect_300um = 'fill_connect_300um'
        self.fill_rout = 'fill_rout'
        self.fill_rout_300um = 'fill_rout_300um'
        self.rout_down = 'rout_down'
        self.pcs_rout_down = 'pcs_rout_down'
        self.tab_area = 'tab_area'
        self.surface_area = 'surface_area'
        self.ccw_hole = 'ccw_hole'
        self.cw_hole = 'cw_hole'
        self.index_move = 'index_move'
        self.index_touch = 'index_touch'
        self.clear_layers = [self.fill_set_300um,self.fill_SR_lyr,self.fill_SR_cover,self.pcs_rout_down,
                             self.tab_connect, self.fill_rout,self.fill_rout_300um,self.surface_area,
                             self.rout_down,self.tab_area,self.fill_connect_300um,
                             self.ccw_hole, self.cw_hole, self.index_move, self.index_touch,]
        setReg = re.compile(r'^set.*$')
        if setReg.match(self.STEP):
            self.pcs_area = self.fill_SR_cover
        else:
            self.pcs_area = self.fill_SR_lyr

    def __del__(self):
        # --关闭数据库连接
        if self.dbc_o:
            self.DB_O.DB_CLOSE(self.dbc_o)

    def get_Layer_Info(self):
        sql = """
        SELECT
            a.item_name AS JOB_NAME,
            LOWER(c.item_name) AS LAYER_NAME,
            d.layer_position,
            d.layer_index,
            d.LAYER_ORIENTATION,
            round( d.required_cu_weight / 28.3495, 2 )  AS CU_WEIGHT,
            e.finish_cu_thk_ AS FINISH_THICKNESS,
            e.cal_cu_thk_ AS cal_cu_thk
            --e.LW_ORG_ 原稿线宽,
            --e.LS_ORG_ 原稿线距,
            --e.LW_FINISH_ 成品线宽,
            --e.ls_finish_ 成品线距 
        FROM
            vgt_hdi.items a,
            vgt_hdi.job b,
            vgt_hdi.items c,
            vgt_hdi.copper_layer d,
            vgt_hdi.copper_layer_da e 
        WHERE
            a.item_id = b.item_id 
            AND a.last_checked_in_rev = b.revision_id 
            AND a.root_id = c.root_id 
            AND c.item_id = d.item_id 
            AND c.last_checked_in_rev = d.revision_id 
            AND d.item_id = e.item_id 
            AND d.revision_id = e.revision_id 
            AND a.item_name = '%s' 
        ORDER BY
            d.layer_index""" % self.JOB_SQL
        process_data = self.DB_O.SELECT_DIC (self.dbc_o, sql)
        return process_data

    def get_Cu_thickness(self, ozKey='None', func='getIndex'):
        """
        获取铜厚信息
        :param ozKey:传入的从Inplan获取的铜厚信息（保留了两位小数）
        :param func:默认功能为获取铜厚信息
        :return:根据条件返回
        """
        index = -1
        ozDes = 'None'
        ozList = []
        ozDic = [
            {'0.33': '1/3OZ'},
            {'0.50': 'HOZ'},
            {'1.00': '1OZ'},
            {'1.50': '1.5OZ'},
            {'2.00': '2OZ'},
            {'2.50': '2.5OZ'},
            {'3.00': '3OZ'},
            {'3.50': '3.5OZ'},
            {'4.00': '4OZ'},
            {'4.50': '4.5OZ'},
            {'5.00': '5OZ'}
        ]
        if func == 'getIndex':
            for oz_hash in ozDic:
                # --获取对应的铜厚
                if ozKey in oz_hash.keys():
                    ozDes = oz_hash[ozKey]
                    index = ozDic.index(oz_hash)
                    break

            # --返回获取的index（有可能为默认值：-1）
            return index
        elif func == 'getList':
            # --获取所有的铜厚列表
            for oz_hash in ozDic:
                for k in oz_hash.keys():
                    ozList.append(oz_hash[k])
            # --增加一个空选项
            ozList.append('None')
            # --返回列表
            return ozList
        elif func == 'getDes':
            for oz_hash in ozDic:
                # --获取对应的铜厚
                if ozKey in oz_hash.keys():
                    ozDes = oz_hash[ozKey]
                    break
            # --返回获取的铜厚对应的说明（有可能为默认值：None）
            return ozDes  

    def run(self):
        """
        具体执行铺铜的函数集合
        :return: None
        :rtype:
        """
        self.GEN.OPEN_STEP(self.STEP,job=self.JOB)
        self.orig_unit = self.GEN.GET_UNITS()
        self.GEN.COM('units,type=mm')
        self.GEN.CLEAR_LAYER()
        # --清除辅助层
        self.clean_tmp()
        self.break_ww_to_isl_hole()
        self.get_fill_SR_cover()
        self.get_laser_list()
        self.get_via_kong()
        self.get_fill_SR_lyr()
        self.get_tab_area()
        # self.get_fill_connect_300um()
        #if self.dig_fill_set_300um():
            #self.modify_copper()
            #self.cycle_layers()
            ## --脚本运行成功提醒
            #msg_box = msgBox()
            #msg_box.information(None, 'Set自动铺铜程序', '脚本运行成功，正式层别已经备份到xx_bei_fen', QMessageBox.Ok)
        # --清除辅助层
        self.clean_tmp(mode='end')

    def clean_tmp(self,mode='start'):
        """
        类或类实例回收时执行
        :return:
        """
        for layer in self.clear_layers + ['hole_lyr','isl_lyr','hole_300um','isl_300um','prof_rout','via_kong',]:
            if not mode == 'start':
                if layer not in [self.fill_set_300um, self.rout_down, self.tab_area]:
                    self.GEN.DELETE_LAYER(layer)
            else:
                self.GEN.DELETE_LAYER(layer)
                if layer in [self.ccw_hole,self.cw_hole,self.index_move,self.index_touch]:
                    self.GEN.CREATE_LAYER(layer)

    def break_ww_to_isl_hole(self):
        """
        ww整体化后扫行break_to_isl_hole命令
        :return: None
        :rtype: None
        """
        # --将所有的外型揉合在一起,包括profile
        self.GEN.COM('profile_to_rout,layer=prof_rout,width=508')
        self.GEN.COPY_LAYER(self.JOB,self.STEP,'ww',self.fill_rout)
        self.GEN.COPY_LAYER(self.JOB,self.STEP,'ww1',self.fill_rout,mode='append')
        self.GEN.COPY_LAYER(self.JOB,self.STEP,'prof_rout',self.fill_rout,mode='append')
        self.GEN.DELETE_LAYER('prof_rout')
        self.GEN.WORK_LAYER(self.fill_rout)
        # --所有外型大小统一为4mil
        self.GEN.COM('sel_change_sym,symbol=r101.6,reset_angle=no')
        self.GEN.SEL_CONTOURIZE(accuracy=0)
        self.GEN.COM('sel_break_isl_hole,islands_layer=isl_lyr,holes_layer=hole_lyr')
        # --加大单边498.4um copy到fill_rout_300um,保证距profile 0.3mm # 2022.09.08 更改为0.508mm（20mil）
        # self.GEN.COM('sel_resize,size=498.4,corner_ctl=yes')
        self.GEN.COM('sel_resize,size=914.4,corner_ctl=yes')
        self.GEN.COM('sel_break_isl_hole,islands_layer=isl_300um,holes_layer=hole_300um')
        self.GEN.SEL_COPY(self.fill_rout_300um,size=0)
        # --加大到单边2mm,保证右走刀的连接位被clip掉  # 2022.09.08 3400 更改为3000
        # self.GEN.COM('sel_resize,size=3400,corner_ctl=yes')
        self.GEN.COM('sel_resize,size=3000,corner_ctl=yes')
        # self.GEN.PAUSE("check break_ww_to_isl_hole")

    def get_fill_SR_cover(self):
        """
        填充set中的子排版
        :return: None
        :rtype: None
        """
        setReg = re.compile(r'^set.*$')
        if setReg.match(self.STEP):
            self.GEN.CREATE_LAYER(self.fill_SR_cover)
            self.GEN.WORK_LAYER(self.fill_SR_cover)
            self.GEN.COM('fill_params,type=solid')
            self.GEN.COM('sr_fill,polarity=positive,step_margin_x=0,step_margin_y=0,step_max_dist_x=2540,step_max_dist_y=2540,'
                         'sr_margin_x=-2540,sr_margin_y=-2540,sr_max_dist_x=0.127,sr_max_dist_y=0.127,nest_sr=yes,stop_at_steps=,'
                         'consider_feat=no,consider_drill=no,consider_rout=no,dest=affected_layers,attributes=no')

    def get_fill_SR_lyr(self):
        """
        edit中填充子排版
        :return: 
        :rtype: 
        """
        setReg = re.compile(r'^set.*$')
        if not setReg.match(self.STEP):
            # --hole_300um是前面break_ww_to_isl_hole函数产生的
            self.GEN.WORK_LAYER('hole_300um')
            # --TODO 与via_kong touch的为板内区
            self.GEN.CREATE_LAYER(self.fill_SR_lyr)
            self.GEN.FILTER_RESET()
            self.GEN.SEL_REF_FEAT('via_kong', 'touch')
            count = self.GEN.GET_SELECT_COUNT()
            if count > 0:
                # self.GEN.PAUSE("check hole_lyr touch via")
                self.GEN.SEL_MOVE(self.fill_SR_lyr,size=1016)

    def get_laser_list(self):
        """
        获取镭射层
        :return:
        :rtype:
        """
        self.laser_array = []
        laser_reg = re.compile(r's[0-9]{2,4}$|s[0-9]{1,2}-[0-9]{1,2}$')
        info = self.GEN.DO_INFO('-t matrix -e %s/matrix -m script -d ROW' % self.JOB)
        for i, name in enumerate(info['gROWname']):
            context = info['gROWcontext'][i]
            layer_type = info['gROWlayer_type'][i]
            if context == 'board' and layer_type == 'drill':
                if laser_reg.match(name):
                    # --将镭射孔大小压入数组
                    self.laser_array.append(name)

    def get_min_pth(self,step,layer):
        """
        获取最小的pth孔
        :return:
        :rtype:
        """
        min_pth = 2540
        info = self.GEN.DO_INFO('-t layer -e %s/%s/%s -m script -d TOOL' % (self.JOB,step,layer))
        for tool_type,tool_size in zip(info['gTOOLtype'],info['gTOOLdrill_size']):
            if tool_type == 'plated':
                if float(tool_size) < min_pth:
                    min_pth = float(tool_size)
        return min_pth

    def get_sr_step(self,step='set'):
        """
        获取set中的sr
        :return: set中的sr列表
        :rtype: list
        """
        sr_list = []
        info = self.GEN.DO_INFO('-t step -e %s/%s -m script -d SR -p step' % (self.JOB,step))
        for sr in info['gSRstep']:
            if sr not in sr_list:
                sr_list.append(sr)
        return sr_list

    def get_via_kong(self):
        """
        获取板内最小孔并copy到via_kong层
        :return:
        :rtype:
        """
        setReg = re.compile(r'^set.*$')
        if setReg.match(self.STEP):
            sr_list = self.get_sr_step(self.STEP)
            self.GEN.CREATE_LAYER('via_kong')
            for step in sr_list:
                self.GEN.OPEN_STEP(step, job=self.JOB)
                self.GEN.COM('units,type=mm')
                if len(self.laser_array) > 0:
                    # --将镭射孔加入via_kong,有镭射则不考虑通孔
                    for layer in self.laser_array:
                        self.GEN.COPY_LAYER(self.JOB, step, layer, 'via_kong', mode='append')
                else:
                    self.GEN.WORK_LAYER('drl')
                    self.GEN.FILTER_SET_INCLUDE_SYMS('r100:r1800', reset=1)
                    self.GEN.COM('filter_set,filter_name=popup,update_popup=no,profile=in')
                    self.GEN.FILTER_SELECT()
                    self.GEN.FILTER_RESET()
                    count = self.GEN.GET_SELECT_COUNT()
                    if count > 0:
                        self.GEN.SEL_COPY('via_kong')
                    else:
                        min_pth = self.get_min_pth(step, 'drl')
                        self.GEN.FILTER_RESET()
                        # --TODO 考虑到有的料号没有定义via及pth属性
                        # self.GEN.FILTER_OPTION_ATTR('.drill', 'plated', reset=1)
                        self.GEN.FILTER_SET_INCLUDE_SYMS('r%s' % min_pth)
                        self.GEN.FILTER_SELECT()
                        count = self.GEN.GET_SELECT_COUNT()
                        if count > 0:
                            self.GEN.SEL_COPY('via_kong')
                # --在profile上面的半孔删除
                self.GEN.COM('profile_to_rout,layer=prof_rout,width=508')
                self.GEN.WORK_LAYER('via_kong')
                self.GEN.SEL_REF_FEAT('prof_rout', 'touch')
                count = self.GEN.GET_SELECT_COUNT()
                if count > 0:
                    self.GEN.SEL_DELETE()
                self.GEN.CLOSE_STEP()
            self.GEN.OPEN_STEP(self.STEP,job=self.JOB)
            self.GEN.COM('flatten_layer,source_layer=via_kong,target_layer=via_kong_f')
            self.GEN.DELETE_LAYER('via_kong')
            self.GEN.WORK_LAYER('via_kong_f')
            # --被fill_sr_cover层uncover住的(半孔)删除
            self.GEN.FILTER_RESET()
            self.GEN.SEL_REF_FEAT(self.fill_SR_cover, 'cover')
            self.GEN.SEL_REVERSE()
            count = self.GEN.GET_SELECT_COUNT()
            if count > 0:
                self.GEN.SEL_DELETE()
            self.GEN.SEL_COPY('via_kong')
        else:
            self.GEN.OPEN_STEP('edit',job=self.JOB)
            if len(self.laser_array) > 0:
                # --将镭射孔加入via_kong,有镭射则不考虑通孔
                for layer in self.laser_array:
                    self.GEN.COPY_LAYER(self.JOB, 'edit', layer, 'via_kong', mode='append')
            else:
                self.GEN.WORK_LAYER('drl')
                # self.GEN.FILTER_OPTION_ATTR('.drill', 'via', reset=1)
                # --考虑profile外面有via孔的情况,参考b24/110a1
                # --没有set时,小于1mm的孔全部copy到via_kong
                self.GEN.FILTER_SET_INCLUDE_SYMS('r100:r1800', reset=1)
                self.GEN.COM('filter_set,filter_name=popup,update_popup=no,profile=in')
                self.GEN.FILTER_SELECT()
                self.GEN.FILTER_RESET()
                count = self.GEN.GET_SELECT_COUNT()
                if count > 0:
                    self.GEN.SEL_COPY('via_kong')
                else:
                    min_pth = self.get_min_pth('edit', 'drl')
                    self.GEN.FILTER_RESET()
                    # --TODO 考虑到有的料号没有定义via及pth属性
                    # self.GEN.FILTER_OPTION_ATTR('.drill', 'plated', reset=1)
                    self.GEN.FILTER_SET_INCLUDE_SYMS('r%s' % min_pth)
                    self.GEN.FILTER_SELECT()
                    count = self.GEN.GET_SELECT_COUNT()
                    if count > 0:
                        self.GEN.SEL_COPY('via_kong')
                    else:
                        self.GEN.CREATE_LAYER('via_kong')
            # --在profile上面的半孔删除
            self.GEN.COM('profile_to_rout,layer=prof_rout,width=508')
            self.GEN.WORK_LAYER('via_kong')
            self.GEN.SEL_REF_FEAT('prof_rout', 'touch')
            count = self.GEN.GET_SELECT_COUNT()
            if count > 0:
                self.GEN.SEL_DELETE()
            # --被fill_rout touch的是邮票孔或者槽头孔,要删除
            self.GEN.SEL_REF_FEAT(self.fill_rout, 'touch')
            count = self.GEN.GET_SELECT_COUNT()
            if count > 0:
                self.GEN.SEL_DELETE()
            # --被fill_rout cover的是假金手指孔(参考004/a14a1),要删除
            self.GEN.SEL_REF_FEAT(self.fill_rout, 'cover')
            # self.GEN.PAUSE("check via_kong cover by fill_rout")
            count = self.GEN.GET_SELECT_COUNT()
            if count > 0:
                self.GEN.SEL_DELETE()
        self.GEN.DELETE_LAYER('prof_rout')
        if setReg.match(self.STEP):
            # --删除flatten出来的via_kong_f
            self.GEN.DELETE_LAYER('via_kong_f')
        # self.GEN.PAUSE("get_via_kong")

    def get_fill_connect_300um(self):
        """
        获取锣空位
        :return:
        :rtype:
        """
        # --hole_lyr是前面break_ww_to_isl_hole函数产生的
        self.GEN.WORK_LAYER('hole_300um')
        self.GEN.FILTER_RESET()
        # --与外层内容物touch到的不是锣空区,反之move到fill_connect_300um
        self.GEN.SEL_REF_FEAT(self.rout_down, 'cover', f_type='surface')
        count = self.GEN.GET_SELECT_COUNT()
        if count > 0:
            self.GEN.SEL_MOVE(self.fill_connect_300um)
            # --删除小于(4.5-2)*(4.5-2)mm2以内的铺铜
            self.GEN.WORK_LAYER(self.fill_connect_300um)
            self.del_small_surface(6.25)
        else:
            self.GEN.CREATE_LAYER(self.fill_connect_300um)

    def get_tab_area(self):
        """
        不与pcs_area相连的都当成tab_area
        :return:
        :rtype:
        """
        self.GEN.DELETE_LAYER(self.rout_down)
        self.GEN.CREATE_LAYER(self.tab_area)
        self.GEN.WORK_LAYER('hole_lyr')
        self.GEN.FILTER_RESET()

        # --删除板内区,touch到via_kong的当成板内区
        self.GEN.SEL_REF_FEAT('via_kong', 'touch')
        count = self.GEN.GET_SELECT_COUNT()
        if count > 0:
            self.GEN.SEL_DELETE()

        # --删除板内锣空区pcs_rout_down,被pcs_area cover的当作板内锣空区pcs_rout_down
        layer_array = [self.tab_connect]
        self.GEN.SEL_REF_FEAT(self.pcs_area, 'cover', f_type='surface')
        count = self.GEN.GET_SELECT_COUNT()
        if count > 0:
            self.GEN.SEL_MOVE(self.pcs_rout_down)
            self.GEN.WORK_LAYER(self.pcs_rout_down)
            self.GEN.SEL_COPY(self.pcs_area,invert='yes',size=254)
            self.GEN.WORK_LAYER(self.pcs_area)
            self.GEN.SEL_CONTOURIZE(accuracy=0)
            # --layer_array分成两部分，板外，及板内捞空区，板内捞空区生成fz_kong时上限只能是2mm
            layer_array.append(self.pcs_rout_down)

        # --不与pcs_area接触的move到tab_area
        self.GEN.WORK_LAYER('hole_lyr')
        self.GEN.SEL_REF_FEAT(self.pcs_area, 'disjoint', f_type='surface')
        count = self.GEN.GET_SELECT_COUNT()
        if count > 0:
            self.GEN.SEL_MOVE(self.tab_area)

        self.GEN.COPY_LAYER(self.JOB,self.STEP,'hole_lyr',self.tab_connect,mode='replace')
        self.GEN.CLEAR_LAYER()
        for layer in layer_array:
            list_tuple = self.sort_surface_by_area(layer)
            for surf in list_tuple:
                index = surf.index
                self.GEN.CLEAR_LAYER()
                self.GEN.AFFECTED_LAYER(layer, 'yes')
                self.GEN.VOF()
                sel_status = self.GEN.COM('sel_layer_feat,operation=select,layer=%s,index=%s' % (layer, index))
                self.GEN.VON()
                if sel_status > 0:
                    # --如果surface已经被移到rout_down了，是选不到index的
                    continue
                this_sur = SurFace(layer,self.pcs_area,index)
                this_sur.parse_info()
                is_rout_down = this_sur.judge_rout_down()
                if is_rout_down:
                    # --将所有rout_down的index选中并move到rout_down
                    self.GEN.CLEAR_LAYER()
                    self.GEN.AFFECTED_LAYER(layer, 'yes')
                    self.GEN.VOF()
                    sel_status = self.GEN.COM('sel_layer_feat,operation=select,layer=%s,index=%s' % (layer, index))
                    self.GEN.VON()
                    if sel_status == 0:
                        self.GEN.SEL_MOVE(self.rout_down)

            # --TODO 区别对待板内区,挑出rout_down后剩下的当作tab_connect copy到tab_connect
            if layer == self.pcs_rout_down:
                self.GEN.WORK_LAYER(layer)
                self.GEN.FILTER_SELECT()
                count = self.GEN.GET_SELECT_COUNT()
                if count > 0:
                    self.GEN.SEL_MOVE(self.tab_connect)

        # --参考m190/083b3,最后修正,将tab_connect中不与rout_down相连的Move到rout_down
        self.GEN.WORK_LAYER(self.tab_connect)
        self.GEN.COM('sel_resize,size=254,corner_ctl=yes')
        if self.GEN.LAYER_EXISTS(self.rout_down, job=self.JOB, step=self.STEP) == 'yes':
            self.GEN.SEL_REF_FEAT(self.rout_down, 'disjoint', f_type='surface')
            count = self.GEN.GET_SELECT_COUNT()
            if count > 0:
                self.GEN.SEL_MOVE(self.rout_down,size=-254)
            self.GEN.COM('sel_resize,size=-254,corner_ctl=yes')
        #else:
            #msg_box = msgBox()
            #msg_box.critical(self, '警告', '没有需要铺铜的捞空区', QMessageBox.Ok)
            #sys.exit(-1)

        # --自动生成的各区域，不一定完全正确，提醒人员确认
        self.GEN.WORK_LAYER(self.rout_down)
        self.GEN.WORK_LAYER(self.tab_connect,number=2)
        #msg_box = msgBox()
        #msg_box.information(self, '确认层别', '请确认捞空区(层别名:rout_down)是否正确!', QMessageBox.Ok)
        # self.GEN.PAUSE("please check rout_down layer")

    def sort_surface_by_area(self,layer):
        """
        创建列表，以surface面积从大到小排序
        :return: reversed_list
        :rtype: list
        """
        self.GEN.CLEAR_LAYER()
        list_namedtuple = self.get_surface_list(layer)
        sort_list = sorted(list_namedtuple,key=attrgetter('area'))
        return sort_list

    def get_surface_list(self,layer):
        """
        按照DO_INFO的index,分别获取每个index的面积
        :return: list_dict具名元组所组成的列表
        :rtype: list
        """
        self.GEN.DELETE_LAYER(self.surface_area)
        self.GEN.CREATE_LAYER(self.surface_area)
        list_namedtuple = []
        index_area = namedtuple('index_area', 'index area')
        # --TODO DO_INFO获取surface的index
        info = self.GEN.INFO('-t layer -e %s/%s/%s -m script -d FEATURES -o feat_index' %
                             (self.JOB, self.STEP, layer))
        indexRegex = re.compile(r'^#(\d+)\s+#S P 0')
        for line in info:
            if re.match(indexRegex, line):
                match_obj = re.match(indexRegex, line)
                index = match_obj.groups()[0]
                # --清空surface_area层
                self.GEN.AFFECTED_LAYER(self.surface_area,'yes')
                self.GEN.SEL_DELETE()
                self.GEN.AFFECTED_LAYER(self.surface_area,'no')
                # --选中index并copy到surface_area
                self.GEN.AFFECTED_LAYER(layer,'yes')
                self.GEN.VOF()
                sel_status = self.GEN.COM('sel_layer_feat,operation=select,layer=%s,index=%s' % (layer,index))
                self.GEN.VON()
                if sel_status == 0:
                    self.GEN.SEL_COPY(self.surface_area)
                    # --计算面积
                    area_mm = self.get_surface_area()
                    idx_area = index_area(index,area_mm)
                    list_namedtuple.append(idx_area)
                self.GEN.AFFECTED_LAYER(layer, 'no')
        return list_namedtuple

    def get_surface_area(self):
        """
        获得surface面积
        :return: 面积平方mm
        :rtype: float
        """
        self.GEN.COM('copper_area,layer1=%s,layer2=,drills=yes,consider_rout=no,ignore_pth_no_pad=no,'
                     'drills_source=matrix,thickness=0,resolution_value=25.4,x_boxes=3,y_boxes=3,'
                     'area=no,dist_map=yes' % self.surface_area)
        ret_string = self.GEN.COMANS
        area_mm = float(ret_string.split()[0])
        return area_mm

    def del_small_surface(self,size):
        """
        删除小surfacee
        :param size: 尺寸
        :type size: str or float
        :return: None
        :rtype:
        """
        self.GEN.FILTER_RESET()
        # --删除4平方mm以下的surface
        self.GEN.FILTER_SET_TYP('surface')
        self.GEN.COM('adv_filter_set,filter_name=popup,update_popup=yes,srf_area=yes,min_area=0,max_area=%s' % size)
        self.GEN.FILTER_SELECT()
        self.GEN.FILTER_RESET()
        # self.GEN.PAUSE("check small surface")
        count = self.GEN.GET_SELECT_COUNT()
        if count > 0:
            self.GEN.SEL_DELETE()

    def dig_fill_set_300um(self):
        """
        用孔及成型掏铜
        :return: True or False
        :rtype: bool
        """
        setReg = re.compile(r'^set.*$')
        self.GEN.CLEAR_LAYER()
        self.GEN.WORK_LAYER(self.fill_connect_300um)
        self.GEN.FILTER_SET_POL('positive', reset=1)
        self.GEN.FILTER_SELECT()
        self.GEN.FILTER_RESET()
        info_300um = self.GEN.DO_INFO('-t layer -e %s/%s/%s -m script -d FEAT_HIST -o select' %
                                (self.JOB, self.STEP, self.fill_connect_300um))
        if info_300um['gFEAT_HISTtotal'] == '0':
            #msg_box = msgBox()
            #msg_box.critical(self, '警告', '没有需要铺铜的捞空区', QMessageBox.Ok)
            return False
        for layer in [self.fill_set_300um]:
            ref_layer = self.fill_connect_300um
            # --将连接位层fill_connect反极性copy到fill_set_dummy层
            self.GEN.COPY_LAYER(self.JOB,self.STEP,ref_layer,layer,mode='replace', invert='no')
            if setReg.match(self.STEP):
                # --参考A91-003A2，edit板边有清角孔，到set没有套铜，铺铜压合需要将set内的孔flatten出来套铜。
                self.GEN.COM('flatten_layer,source_layer=drl,target_layer=drl_f')
                self.GEN.WORK_LAYER('drl_f')
                self.GEN.SEL_COPY(layer,size=1016,invert='yes')
                self.GEN.DELETE_LAYER('drl_f')
            else:
                # --将孔加大40mil反极性copy到fill_set_dummy层
                self.GEN.WORK_LAYER('drl')
                self.GEN.SEL_COPY(layer,size=1016,invert='yes')
            # --将vcut加大2mm反极性copy到
            if self.GEN.LAYER_EXISTS('vcut', job=self.JOB, step=self.STEP) == 'yes':
                self.GEN.WORK_LAYER('vcut')
                self.GEN.SEL_COPY(layer, size=2032, invert='yes')
            # --将fill_set_dummy整体化
            self.GEN.WORK_LAYER(layer)
            self.GEN.SEL_CONTOURIZE(accuracy=0)
            # --fill_copper可能全是负性，没办法整体化，参考料号a39/179a1
            self.GEN.FILTER_SET_TYP('surface',reset=1)
            self.GEN.FILTER_SET_POL('positive')
            self.GEN.FILTER_SELECT()
            self.GEN.FILTER_RESET()
            count = self.GEN.GET_SELECT_COUNT()
            if count == 0:
                self.GEN.SEL_DELETE()
            else:
                self.GEN.CLEAR_FEAT()
            # --删除1平方mm以下的surface
            self.del_small_surface(1)
        return True

    def modify_copper(self):
        """
        修饰fill_set_copper层，删除4.5mm*4.5mm以内的铜皮，并重新用r10进行fill
        :return: None
        :rtype: None
        """
        self.GEN.WORK_LAYER(self.fill_set_300um)
        # --用20mil的brush进行fill
        self.GEN.COM('fill_params,type=solid,origin_type=datum,solid_type=fill,std_type=line,min_brush=%s,'
                     'use_arcs=yes,symbol=diamond_s5000xr1000,dx=2.54,dy=2.54,std_angle=45,std_line_width=254,'
                     'std_step_dist=1270,std_indent=odd,break_partial=yes,cut_prims=yes,outline_draw=no,'
                     'outline_width=0,outline_invert=no' % 508)
        self.GEN.COM('sel_fill')
        self.GEN.SEL_CONTOURIZE(accuracy=0)
        # --删除面积小于1mm2的小surface
        self.del_small_surface(1)

    def cycle_layers(self):
        """
        循环选中列表中的每一层
        :return: None
        :rtype: None
        """
        for layer_dict in self.parameterDic['List']:
            layer = layer_dict['layer']
            brk_layer = '%s_break_sym' % layer
            sym_layer = '%s_move_sym' % layer
            tmp_layer = '%s_tmp_surf' % layer
            bef_layer = '%s_bei_fen' % layer
            subs_lyr = self.fill_set_300um
            # --先备份层别
            self.GEN.COPY_LAYER(self.JOB,self.STEP,layer,bef_layer,mode='replace', invert='no')
            self.GEN.WORK_LAYER(layer)
            # --TODO 将touch到fill_set_copper层的symbol move到sym_layer,主要是锣槽防呆symbol
            self.GEN.FILTER_RESET()
            self.GEN.FILTER_SET_TYP('pad')
            self.GEN.SEL_REF_FEAT(subs_lyr, 'touch')
            count = self.GEN.GET_SELECT_COUNT()
            if count > 0:
                self.GEN.SEL_MOVE(sym_layer)
            # --TODO touch到的surface将会被替换，直接删除(460/004b1 l3层铜皮丢失)
            self.GEN.FILTER_RESET()
            self.GEN.FILTER_SET_TYP('surface')
            self.GEN.FILTER_SET_POL('positive')
            self.GEN.SEL_REF_FEAT(subs_lyr, 'touch')
            self.GEN.FILTER_RESET()
            count = self.GEN.GET_SELECT_COUNT()
            if count > 0:
                self.GEN.SEL_DELETE()
            # --替换原有的surface
            self.GEN.COPY_LAYER(self.JOB,self.STEP,subs_lyr,tmp_layer,mode='replace', invert='no')
            # --将symbol move回原层别
            if self.GEN.LAYER_EXISTS(sym_layer,job=self.JOB,step=self.STEP) == 'yes':
                # --仅当层别存在时才需要move回原层别
                self.GEN.WORK_LAYER(sym_layer)
                self.GEN.SEL_COPY(brk_layer)
                # --symbol直接resize会报错，此处先打散，转极性
                self.GEN.WORK_LAYER(brk_layer)
                self.GEN.COM('sel_break')
                self.GEN.VOF()
                self.GEN.COM('sel_decompose,overlap=yes')
                self.GEN.VON()
                # --删除负片
                self.GEN.FILTER_RESET()
                self.GEN.FILTER_SET_POL('negative')
                self.GEN.FILTER_SELECT()
                self.GEN.FILTER_RESET()
                count = self.GEN.GET_SELECT_COUNT()
                if count > 0:
                    self.GEN.SEL_DELETE()
                # --当前层的symbol保证到铜300um
                self.GEN.SEL_CONTOURIZE(accuracy=0)
                self.GEN.SEL_COPY(tmp_layer,size=1016,invert='yes')
                # --TODO 整体化并去除1平方mm以下的surface
                self.GEN.WORK_LAYER(tmp_layer)
                self.GEN.SEL_CONTOURIZE(accuracy=0)
                self.GEN.COM('fill_params,type=solid,origin_type=datum,solid_type=fill,std_type=line,min_brush=%s,'
                             'use_arcs=yes,symbol=diamond_s5000xr1000,dx=2.54,dy=2.54,std_angle=45,std_line_width=254,'
                             'std_step_dist=1270,std_indent=odd,break_partial=yes,cut_prims=yes,outline_draw=no,'
                             'outline_width=0,outline_invert=no' % 508)
                self.GEN.COM('sel_fill')
                self.GEN.SEL_CONTOURIZE(accuracy=0)
                self.del_small_surface(1)
                self.GEN.SEL_MOVE(layer)
                # --当前层的symbol move回原层别
                self.GEN.WORK_LAYER(sym_layer)
                self.GEN.SEL_MOVE(layer)
            else:
                self.GEN.WORK_LAYER(tmp_layer)
                # --TODO 没有symbol时，用300um的brush进行fill，去掉尖角
                self.GEN.COM('fill_params,type=solid,origin_type=datum,solid_type=fill,std_type=line,min_brush=%s,'
                             'use_arcs=yes,symbol=diamond_s5000xr1000,dx=2.54,dy=2.54,std_angle=45,std_line_width=254,'
                             'std_step_dist=1270,std_indent=odd,break_partial=yes,cut_prims=yes,outline_draw=no,'
                             'outline_width=0,outline_invert=no' % 508)
                self.GEN.COM('sel_fill')
                self.GEN.SEL_CONTOURIZE(accuracy=0)
                self.GEN.SEL_MOVE(layer)

            self.GEN.DELETE_LAYER(tmp_layer)
            self.GEN.DELETE_LAYER(sym_layer)
            self.GEN.DELETE_LAYER(brk_layer)

    def cycle_md(self):
        """
        将fill_set_copper copy到档点层(省防焊油墨)
        :return: None
        :rtype: None
        """
        self.GEN.WORK_LAYER(self.fill_set_300um)
        # --TODO 加大80mil,保证档点距锣边40mil
        self.GEN.COM('sel_resize,size=2032,corner_ctl=yes')
        for layer in ['md1','md2']:
            brk_layer = '%s_break_sym' % layer
            sym_layer = '%s_move_sym' % layer
            tmp_layer = '%s_tmp_surf' % layer
            bef_layer = '%s_bei_fen' % layer
            subs_lyr = self.fill_set_300um
            # --先备份层别
            self.GEN.COPY_LAYER(self.JOB,self.STEP,layer,bef_layer,mode='replace', invert='no')
            self.GEN.WORK_LAYER(layer)
            # --TODO 将touch到fill_set_copper层的symbol move到sym_layer,主要是锣槽防呆symbol
            self.GEN.FILTER_RESET()
            self.GEN.FILTER_SET_TYP('pad')
            self.GEN.SEL_REF_FEAT(subs_lyr, 'touch')
            count = self.GEN.GET_SELECT_COUNT()
            if count > 0:
                self.GEN.SEL_MOVE(sym_layer)
            # --TODO touch到的surface将会被替换，直接删除
            self.GEN.FILTER_RESET()
            self.GEN.FILTER_SET_TYP('surface')
            self.GEN.SEL_REF_FEAT(subs_lyr, 'touch')
            self.GEN.FILTER_RESET()
            count = self.GEN.GET_SELECT_COUNT()
            if count > 0:
                self.GEN.SEL_DELETE()
            # --替换原有的surface
            self.GEN.COPY_LAYER(self.JOB,self.STEP,subs_lyr,tmp_layer,mode='replace', invert='no')
            # --将symbol move回原层别
            if self.GEN.LAYER_EXISTS(sym_layer,job=self.JOB,step=self.STEP) == 'yes':
                # --仅当层别存在时才需要move回原层别
                self.GEN.WORK_LAYER(sym_layer)
                self.GEN.SEL_COPY(brk_layer)
                # --symbol直接resize会报错，此处先打散，转极性
                self.GEN.WORK_LAYER(brk_layer)
                self.GEN.COM('sel_break')
                self.GEN.VOF()
                self.GEN.COM('sel_decompose,overlap=yes')
                self.GEN.VON()
                # --删除负片
                self.GEN.FILTER_RESET()
                self.GEN.FILTER_SET_POL('negative')
                self.GEN.FILTER_SELECT()
                self.GEN.FILTER_RESET()
                count = self.GEN.GET_SELECT_COUNT()
                if count > 0:
                    self.GEN.SEL_DELETE()
                # --当前层的symbol保证到铜300um
                self.GEN.SEL_CONTOURIZE(accuracy=0)
                self.GEN.SEL_COPY(tmp_layer,size=1016,invert='yes')
                # --TODO 整体化并去除1平方mm以下的surface
                self.GEN.WORK_LAYER(tmp_layer)
                self.GEN.SEL_CONTOURIZE(accuracy=0)
                self.GEN.COM('fill_params,type=solid,origin_type=datum,solid_type=fill,std_type=line,min_brush=%s,'
                             'use_arcs=yes,symbol=diamond_s5000xr1000,dx=2.54,dy=2.54,std_angle=45,std_line_width=254,'
                             'std_step_dist=1270,std_indent=odd,break_partial=yes,cut_prims=yes,outline_draw=no,'
                             'outline_width=0,outline_invert=no' % 508)
                self.GEN.COM('sel_fill')
                self.GEN.SEL_CONTOURIZE(accuracy=0)
                # --TODO 比铜大单边10mil,前面resize加大过了，此处不再加大
                # self.GEN.COM('sel_resize,size=508,corner_ctl=yes')
                self.del_small_surface(1)
                self.GEN.SEL_MOVE(layer)
                # --当前层的symbol move回原层别
                self.GEN.WORK_LAYER(sym_layer)
                self.GEN.SEL_MOVE(layer)
            else:
                self.GEN.WORK_LAYER(tmp_layer)
                # --TODO 没有symbol时，用20mil的brush进行fill，去掉尖角
                self.GEN.COM('fill_params,type=solid,origin_type=datum,solid_type=fill,std_type=line,min_brush=%s,'
                             'use_arcs=yes,symbol=diamond_s5000xr1000,dx=2.54,dy=2.54,std_angle=45,std_line_width=254,'
                             'std_step_dist=1270,std_indent=odd,break_partial=yes,cut_prims=yes,outline_draw=no,'
                             'outline_width=0,outline_invert=no' % 508)
                self.GEN.COM('sel_fill')
                self.GEN.SEL_CONTOURIZE(accuracy=0)
                # --TODO 比铜大单边10mil,前面resize加大过了，此处不再加大
                # self.GEN.COM('sel_resize,size=508,corner_ctl=yes')
                self.GEN.SEL_MOVE(layer)

            self.GEN.DELETE_LAYER(tmp_layer)
            self.GEN.DELETE_LAYER(sym_layer)
            self.GEN.DELETE_LAYER(brk_layer)

class SurFace(object):
    """
    surface类
    """
    def __init__(self,layer,sr_layer,index):
        self.JOB = os.environ.get('JOB', None)
        self.STEP = os.environ.get('STEP', None)
        self.GEN = genCOM.GEN_COM()
        self.layer = layer
        self.rout_down = 'rout_down'
        self.index = index
        self.pcs_area = sr_layer
        self.ccw_hole = 'ccw_hole'
        self.cw_hole = 'cw_hole'
        self.index_move = 'index_move'
        self.index_touch = 'index_touch'
        # --逆时针方向圆弧
        self.counter_clockwise = []
        # --顺时针方向圆弧
        self.clockwise = []
        self.segment_num = 0

    def __del__(self):
        """
        实例回收时删除辅助层
        :return:
        :rtype:
        """
        pass

    def parse_info(self):
        """
        解析DO_INFO信息
        :return:
        :rtype:
        """
        # --清空辅助层
        self.GEN.CLEAR_LAYER()
        self.GEN.AFFECTED_LAYER(self.ccw_hole,'yes')
        self.GEN.AFFECTED_LAYER(self.cw_hole,'yes')
        self.GEN.AFFECTED_LAYER(self.index_move,'yes')
        self.GEN.AFFECTED_LAYER(self.index_touch,'yes')
        self.GEN.SEL_DELETE()
        self.GEN.CLEAR_LAYER()
        self.GEN.AFFECTED_LAYER(self.layer, 'yes')
        self.GEN.VOF()
        # --调用之前已经加了是否选中的限制条件，此处一定可以选中
        sel_status = self.GEN.COM('sel_layer_feat,operation=select,layer=%s,index=%s' % (self.layer, self.index))
        self.GEN.VON()
        info = self.GEN.INFO('-t layer -e %s/%s/%s -m script -d FEATURES -o feat_index+select' %
                             (self.JOB, self.STEP, self.layer))
        arcRegex = re.compile(r'^#\s+#OC')
        segRegex = re.compile(r'^#\s+#OS')
        bgnRegex = re.compile(r'^#\s+#OB')
        self.GEN.SEL_COPY(self.index_move,size=254)
        self.GEN.SEL_REF_FEAT(self.index_move, 'touch')
        count = self.GEN.GET_SELECT_COUNT()
        if count > 0:
            # --与当前index surface touch到的move到index_touch
            self.GEN.SEL_COPY(self.index_touch)
            self.GEN.AFFECTED_LAYER(self.layer, 'no')
            self.GEN.AFFECTED_LAYER(self.index_touch, 'yes')
            self.GEN.SEL_REF_FEAT(self.index_move, 'cover')
            count = self.GEN.GET_SELECT_COUNT()
            if count > 0:
                # --因为index_move是copy出去的，也会被cover，选中并删除
                self.GEN.SEL_DELETE()
        self.GEN.CLEAR_LAYER()
        seg_xs = None
        seg_ys = None
        for line in info:
            if re.match(arcRegex, line):
                columns = line.strip().split()
                xe = float(columns[2]) # --弧终点x坐标
                ye = float(columns[3]) # --弧终点y坐标
                xc = float(columns[4]) # --弧中点x坐标
                yc = float(columns[5]) # --弧中点y坐标
                YN = columns[6] # --弧方向，Y为顺时针，N代表逆时针
                if YN == 'N':
                    self.counter_clockwise_hole(xe, ye, xc, yc)
                else:
                    self.clockwise_hole(xe, ye, xc, yc)
                seg_xs = xe
                seg_ys = ye
            if re.match(segRegex, line):
                columns = line.strip().split()
                seg_xe = float(columns[2]) # --终点x坐标
                seg_ye = float(columns[3]) # --终点y坐标
                seg_len = math.hypot(seg_xe - seg_xs, seg_ye - seg_ys)
                if seg_len > 0.5:
                    self.segment_num += 1
                seg_xs = seg_xe
                seg_ys = seg_ye
            if re.match(bgnRegex, line):
                columns = line.strip().split()
                seg_xs = float(columns[2]) # --起点x坐标
                seg_ys = float(columns[3]) # --起点y坐标

    def counter_clockwise_hole(self,xe,ye,xc,yc):
        """
        在内R角圆弧处添加辅助孔
        :return:
        :rtype:
        """
        if self.layer == 'tab_connect':
            max_limit = 3.0
        else:
            max_limit = 2.0
        # --计算弧半径
        arc_radius = math.hypot(xe-xc,ye-yc)
        if arc_radius >= 0.5 and arc_radius < max_limit:
            # --只对弧半径小于等于1mm的弧进行处理
            self.GEN.AFFECTED_LAYER(self.ccw_hole, 'yes')
            sym = 'r%s' % (arc_radius*1000)
            self.GEN.COM('cur_atr_reset')
            self.GEN.COM('cur_atr_set,attribute=.string,text=index_%s' % self.index)
            self.GEN.ADD_PAD(xc,yc,sym,attr='yes')
            self.GEN.COM('cur_atr_reset')
            self.counter_clockwise.append('N')
            self.GEN.AFFECTED_LAYER(self.ccw_hole, 'no')

    def clockwise_hole(self,xe,ye,xc,yc):
        """
        外R角圆弧处添加辅助孔
        :return:
        :rtype:
        """
        # --槽头孔最大直径为2.0mm，半径为1.0mm
        max_limit = 1.0
        # --计算弧半径
        arc_radius = math.hypot(xe-xc,ye-yc)
        if arc_radius >= 0.25 and arc_radius <= max_limit:
            # --只对弧半径小于等于1mm的弧进行处理
            self.GEN.AFFECTED_LAYER(self.cw_hole, 'yes')
            sym = 'r%s' % (arc_radius*1000)
            self.GEN.COM('cur_atr_reset')
            self.GEN.COM('cur_atr_set,attribute=.string,text=index_%s' % self.index)
            self.GEN.ADD_PAD(xc,yc,sym,attr='yes')
            self.GEN.COM('cur_atr_reset')
            self.clockwise.append('Y')
            self.GEN.AFFECTED_LAYER(self.cw_hole, 'no')

    def judge_rout_down(self):
        """
        判断是否为锣空区
        :return:
        :rtype:
        """
        if len(self.counter_clockwise) > 0:
            self.GEN.CLEAR_LAYER()
            self.GEN.AFFECTED_LAYER(self.pcs_area,'yes')
            self.GEN.FILTER_RESET()
            self.GEN.SEL_REF_FEAT(self.ccw_hole,'touch')
            count = self.GEN.GET_SELECT_COUNT()
            if count > 0:
                # --内R角圆心添加的辅助孔与sr touch到的是锣空区
                self.GEN.CLEAR_FEAT()
                if self.index_move_touch_rout_down():
                    # --ccw_hole touch到sr的也有可能是连接位，参考料号a86/115a2
                    # self.GEN.PAUSE("touch sr and touch rout_down")
                    return False
                else:
                    # self.GEN.PAUSE("touch sr and disjoint rout_down")
                    return True

        # --TODO 如果无法通过内R角添加的辅助孔与sr touch来判断是否为锣空区,则通过cw_hole是否全落在自身来判断
        if len(self.clockwise) > 0:
            self.GEN.CLEAR_LAYER()
            self.GEN.AFFECTED_LAYER(self.cw_hole,'yes')
            self.GEN.SEL_REF_FEAT(self.index_move, 'cover')
            self.GEN.SEL_REVERSE()
            count = self.GEN.GET_SELECT_COUNT()
            if count == 0:
                if self.index_move_touch_rout_down():
                    # --与已经存在的锣空区touch的不是锣空区，返回False
                    # self.GEN.PAUSE("cover cw_hole but touch rout_down")
                    return False
                else:
                    # --故如果disjoint到rout_down的当作锣空区
                    # self.GEN.PAUSE("cover cw_hole and not touch rout_down")
                    return True

        # --TODO 无法判断是否为锣空区时,则开始判断是否为连接位
        is_tab_connect = self.judge_tab_connect()
        if is_tab_connect:
            # --能判断为连接位,则返回False
            return False
        else:
            # --TODO 不能确定为连接位，还有可能是tab_area工艺边，此处待完善
            return True

    def index_move_touch_rout_down(self):
        """
        查看index_move是否接触已经存在的rout_down
        :return:
        :rtype:
        """
        if self.GEN.LAYER_EXISTS(self.rout_down, job=self.JOB, step=self.STEP) == 'yes':
            # --外R角圆心添加的辅助孔全部被当前surface cover的视为锣空区
            self.GEN.CLEAR_LAYER()
            self.GEN.AFFECTED_LAYER(self.index_move,'yes')
            self.GEN.SEL_REF_FEAT(self.rout_down, 'touch')
            count = self.GEN.GET_SELECT_COUNT()
            if count == 0:
                # --index_move不与rout_down接触
                return False
            else:
                # --与已经存在的锣空区touch
                return True
        # --index_move不存在时返回False
        return False

    def move_index_touch_to_rout_down(self):
        """
        将index_touch move到rout_down，以节省时间
        :return:
        :rtype:
        """
        if self.GEN.LAYER_EXISTS(self.index_touch, job=self.JOB, step=self.STEP) == 'yes':
            self.GEN.CLEAR_LAYER()
            self.GEN.AFFECTED_LAYER(self.layer,'yes')
            self.GEN.SEL_REF_FEAT(self.index_touch, 'include')
            count = self.GEN.GET_SELECT_COUNT()
            if count > 0:
                # --与当前index surface touch到的move到index_touch
                self.GEN.SEL_MOVE(self.rout_down)

    def judge_tab_connect(self):
        """
        判断是否为连接位
        :return:
        :rtype:
        """
        print "self.clockwise",self.clockwise
        # --查看是否与index_touch include,有include则视作tab_connect,从而返回true
        if self.GEN.LAYER_EXISTS(self.index_touch, job=self.JOB, step=self.STEP) == 'yes':
            if len(self.counter_clockwise) > 0:
                self.GEN.CLEAR_LAYER()
                self.GEN.AFFECTED_LAYER(self.ccw_hole, 'yes')
                if self.GEN.LAYER_EXISTS(self.rout_down, job=self.JOB, step=self.STEP) == 'yes':
                    # --考虑半边index_touch已经Move到rout_down的情况
                    ref_layer = '\;'.join([self.index_touch,self.rout_down])
                else:
                    ref_layer = self.index_touch
                self.GEN.SEL_REF_FEAT(ref_layer, 'cover')
                self.GEN.SEL_REVERSE()
                count = self.GEN.GET_SELECT_COUNT()
                if count == 0:
                    # --此时不能排除tab_area,故如果touch到rout_down的肯定不是锣空区
                    self.move_index_touch_to_rout_down()
                    # self.GEN.PAUSE("check tab_connect ccw_hole cover by index_touch")
                    return True
        # --查看是否与rout_down touch,有touch则视作tab_connect,从而返回true
        if self.GEN.LAYER_EXISTS(self.rout_down, job=self.JOB, step=self.STEP) == 'yes':
            # --外R角圆心添加的辅助孔全部被当前surface cover的视为锣空区
            self.GEN.CLEAR_LAYER()
            self.GEN.AFFECTED_LAYER(self.index_move,'yes')
            self.GEN.SEL_REF_FEAT(self.rout_down, 'touch')
            count = self.GEN.GET_SELECT_COUNT()
            if count > 0:
                # --此时不能排除tab_area,故如果touch到rout_down的肯定不是锣空区
                self.move_index_touch_to_rout_down()
                # self.GEN.PAUSE("check tab_connect touch rout_down")
                return True
        if self.segment_num == 4 and len(self.clockwise) == 0:
            # --矩形的视作连接位，参考料号b06/210f2
            self.move_index_touch_to_rout_down()
            # self.GEN.PAUSE("rect tab_connect")
            return True
        # --以上均不能确认，返回False
        return False

if __name__ == '__main__':
    main = create_luokong_layer()
    main.run()
    
    #app = QtGui.QApplication(sys.argv)
    #myapp = MainWindow()

    ## --修改尺寸，并以桌面居中形式弹出
    #myapp.resize(453, 453)
    ## 先将窗口放到屏幕外，可避免移动窗口时的闪烁现象。
    #myapp.move(myapp.width() * -2, 0)
    #myapp.show()

    #desktop = QtGui.QApplication.desktop()
    #x = (desktop.width() - myapp.frameSize().width()) // 2
    #y = (desktop.height() - myapp.frameSize().height()) // 2

    ## --从屏幕外移回
    #myapp.move(x, y)

    #app.exec_()
    #sys.exit(0)

"""
李家兴
2021.11.16 Note by Song
原始需求：http://192.168.2.120:82/zentao/story-view-3645.html
宋超
2022.09.08
更改铺铜距离成型线距离0.3mm-->0.508mm
http://192.168.2.120:82/zentao/story-view-4604.html

"""