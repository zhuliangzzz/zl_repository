#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------#
#               VTG.SH SOFTWARE GROUP                     #
# ---------------------------------------------------------#
# @Author       :    Song
# @Mail         :    
# @Date         :    2022/03/21
# @Revision     :    1.0.0
# @File         :    check_bars_in_area.py
# @Software     :    PyCharm
# @Usefor       :    检测板边标靶（DLD，五代靶、Xray）是否在干膜线内，电镀夹头范围内
# @url          :    http://192.168.2.120:82/zentao/story-view-4012.html
# @from         :    sr_pitch_check.py of Michael
# @Modify：2022.12.21 Song 更改靶标到干膜线的的检测为靶边到干膜线的检测变更为靶中心的检测。
# http://192.168.2.120:82/zentao/story-view-5005.html
# 2023.01.03 增加pe冲孔类的检测
# 2023.02.03 更改电镀夹头区域的其中一个区间 160-220 更改为160-225
# ---------------------------------------------------------#


import sys
import os
import platform
import re
import json
from PyQt4 import QtCore, QtGui, Qt
from PyQt4.QtGui import QMessageBox

from datetime import datetime

PRODUCT = os.environ.get('INCAM_PRODUCT', None)
if platform.system() == "Windows":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package")
    # sys.path.insert(0, "D:/genesis/sys/scripts/Package")

else:
    scriptPath = "%s/scripts" % os.environ.get('SCRIPTS_DIR', '/incam/server/site_data')
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")
# --导入Package
import genCOM_26
import Oracle_DB
from messageBox import msgBox
import autocheckUI_V2 as UI

from get_erp_job_info import get_inplan_mrp_info

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s


# --所有与InPlan查询相关的全部写到InPlan类中
class InPlan(object):
    def __init__(self, job_name):
        self.JOB_SQL = job_name.upper().split('-')[0] if '-' in job_name else job_name.upper()

        # --Oracle相关参数定义
        self.DB_O = Oracle_DB.ORACLE_INIT()
        self.dbc_h = self.DB_O.DB_CONNECT(host='172.20.218.193', servername='inmind.fls', port='1521',
                                          username='GETDATA', passwd='InplanAdmin')
        # self.lamination,self.lam_rout = self.get_lamination_info()
        if not self.dbc_h:
            msg_box = msgBox()
            msg_box.critical(self, '错误', 'InPlan无法连接，程序退出', QMessageBox.Ok)
            sys.exit()

    def __del__(self):
        # --关闭数据库连接
        if self.dbc_h:
            self.DB_O.DB_CLOSE(self.dbc_h)

    def getLaminData(self):
        """
        获取压合信息
        2021.12.16 增加线路四靶X数据
        :return:
        """
        sql = """
        SELECT
            a.item_name AS job_name,
            d.mrp_name AS mrpName,
            e.process_num_ AS process_num,
            b.pnl_size_x / 1000 AS pnlXInch,
            b.pnl_size_Y / 1000 AS pnlYInch,
            e.pressed_pnl_x_ / 1000 AS pnlroutx,
            e.pressed_pnl_y_ / 1000 AS pnlrouty,
            round( e.target_x1_ / 39.37, 4 ) bar4x1,
            round( e.target_y1_ / 39.37, 4 ) bar4y1,
            round( e.target_x2_ / 39.37, 4 ) bar4x2,
            round( e.target_y2_ / 39.37, 4 ) bar4y2,
            round( e.target_backup_x_ / 39.37, 4 ) bar3x,
            round( e.target_backup_y_ / 39.37, 4 ) bar3y,
            (case when  e.film_bg_ not like '%%,%%' then
            'L'|| TO_CHAR(TO_NUMBER(substr(REGEXP_SUBSTR( d.mrp_name, '[^-]+', 1,2 ),2,2), '99')) else 
            REGEXP_SUBSTR( e.film_bg_, '[^,]+', 1, 1 ) end) fromLay,
            (case when  e.film_bg_ not like '%%,%%' then
            'L'|| TO_CHAR(TO_NUMBER(substr(REGEXP_SUBSTR( d.mrp_name, '[^-]+', 1,2 ),4,2), '99')) else 
            REGEXP_SUBSTR( e.film_bg_, '[^,]+', 1, 2 ) end) toLay,
            ROUND( e.PRESSED_THICKNESS_ / 39.37, 2 ) AS yhThick,
            ROUND( e.PRESSED_THICKNESS_TOL_PLUS_ / 39.37, 2 ) AS yhThkPlus,
            ROUND( e.PRESSED_THICKNESS_TOL_MINUS_ / 39.37, 2 ) AS yhThkDown,
            e.LASER_BURN_TARGET_ V5laser,
            round( e.OUTER_TARGET_Y1_ / 39.37, 4 ) sig4y1,
            round( e.OUTER_TARGET_Y2_ / 39.37, 4 ) sig4y2,
            round( e.OUTER_TARGET_X1_ / 39.37, 4 ) sig4x1,
            round( e.OUTER_TARGET_X2_ / 39.37, 4 ) sig4x2  
        FROM
            vgt_hdi.items a
            INNER JOIN vgt_hdi.job b ON a.item_id = b.item_id 
            AND a.last_checked_in_rev = b.revision_id
            INNER JOIN vgt_hdi.public_items c ON a.root_id = c.root_id
            INNER JOIN vgt_hdi.process d ON c.item_id = d.item_id 
            AND c.revision_id = d.revision_id
            INNER JOIN vgt_hdi.process_da e ON d.item_id = e.item_id 
            AND d.revision_id = e.revision_id 
        WHERE
            a.item_name = '%s'
            AND d.proc_type = 1 
            AND d.proc_subtype IN ( 28, 29 ) 
        ORDER BY
            e.process_num_""" % self.JOB_SQL
        process_data = self.DB_O.SELECT_DIC(self.dbc_h, sql)
        return process_data

    def get_split_num(self):
        """
        获取料号的分割次数
        :return:
        """
        sql = """
            SELECT
                i.ITEM_NAME AS JobName,
                p.value,
                job.ES_ELIC_ 是否任意互连ELIC
            FROM
                VGT_hdi.PUBLIC_ITEMS i,
                VGT_hdi.JOB_DA job,
                    VGT_HDI.field_enum_translate p   
            where  
                i.ITEM_NAME = '%s'
                AND i.item_id = job.item_id
                AND i.revision_id = job.revision_id
                and p.fldname = 'PNL_PARCELLATION_METHOD_'
                and p.enum=job.PNL_PARCELLATION_METHOD_
                and p.intname = 'JOB'""" % self.JOB_SQL
        process_data = self.DB_O.SELECT_DIC(self.dbc_h, sql)
        split_job = 'yes'
        anylayer = "no"
        if len(process_data) == 0:
            # === 无此料号时，按不分割处理
            return None, None
        else:
            if process_data[0]['VALUE'] == '无需分割':
                split_job = 'no'
            elif process_data[0]['VALUE'] == 'Unknown':
                split_job = 'unknown'
                
            anylayer = "yes" if process_data[0]['是否任意互连ELIC'] == 1 else "no"

        return split_job, anylayer

    def get_laser_dielectric_thick(self):
        """
        获取镭射层介质厚度
        :return:
        """
        sql="""
            SELECT
                JOB_NAME,
                PROGRAM_NAME,
                START_INDEX,
                END_INDEX,
                ROUND( DRILL_DEPTH, 2 ) - 0.2 AS DRILL_DEPTH 
            FROM
                VGT_HDI.RPT_DRILL_PROGRAM_LIST 
            WHERE
                DRILL_TECHNOLOGY = 2 
                AND job_name = '%s' 
        """ % self.JOB_SQL
        process_data = self.DB_O.SELECT_DIC(self.dbc_h, sql)
        print process_data
        redeal_dict = {}
        for line in process_data:
            layer = 'l%s' % line['START_INDEX']
            redeal_dict[layer] = {'drill_depth': line['DRILL_DEPTH']}
        return redeal_dict    

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
        process_data = self.DB_O.SELECT_DIC(self.dbc_h, sql)
        return process_data
    
    def get_stackup_pp_foil_info(self):
        sql = """select j.proc_mrp_name,j.segment_type_t,
	j.pressed_thickness,j.cust_req_thickness_,
        j.stackup_seg_index
	from VGT_HDI.rpt_job_process_stk_seg_list j 
	where j.job_name = upper('{0}')
	and j.proc_mrp_name is not null
	and j.pressed_thickness is not null
	order by stackup_seg_index"""
        stackup_data = self.DB_O.SELECT_DIC(self.dbc_h, sql.format(self.JOB_SQL))
        return stackup_data
    
    def get_laser_config(self):
        """
        取镭射层镭射参数及镭射介质厚度
        :return:
        """
        sql = """
    SELECT
        a.item_name,
        e.item_name as INPLAN_LAYER_NAME,
        d.laser_drl_parameter_ as LASER_PARM,
        c.start_index as START_INDEX,
        c.end_index AS END_INDEX,
        ROUND( c.DRILL_DEPTH, 2 ) - 0.2 AS DRILL_DEPTH 
    FROM
        vgt_hdi.Items A,
        VGT_HDI.JOB b,
        VGT_HDI.DRILL_PROGRAM c,
        vgt_hdi.drill_program_da d,
        vgt_hdi.public_items e 
    WHERE
        a.item_id = b.item_id 
        AND a.last_checked_in_rev = b.revision_id 
        AND a.root_id = e.root_id 
        AND e.item_id = c.item_id 
        AND e.revision_id = c.revision_id 
        AND c.item_id = d.item_id 
        AND c.revision_id = d.revision_id 
        and a.item_name = '%s'
        AND c.drill_technology = 2""" % self.JOB_SQL

        query_result = self.DB_O.SELECT_DIC(self.dbc_h, sql)
        laser_data = []
        for info_dict in query_result:
            cur_layer_name = 's%s-%s' % (info_dict['START_INDEX'], info_dict['END_INDEX'])
            laser_data.append(dict(layer_name=cur_layer_name,
                                   laser_parm=info_dict['LASER_PARM'],
                                   laser_depth_mil=info_dict['DRILL_DEPTH']))
        return laser_data


class MyApp(object):
    def __init__(self, step_name):
        self.GEN = genCOM_26.GEN_COM()
        self.job_name = os.environ.get('JOB')
        self.step_name = step_name
        self.g_steps_list = self.get_step_list()
        self.fill_layer = 'sr_fill'
        self.flat_layer = 'sr_fill_flat'
        self.out_step_fill = '_out_fill_flat'
        self.pnl_out_copper = '_pnl_out_flat'
        self.pnl_coupon_copper = '_pnl_coupon'
        # self.close_sr = 'close_sr'
        self.md_clip = 'md_clip'
        self.md_cover = 'md_cover'
        # === 定义全局变量，以下单位为mm
        self.check_dist = 0.500
        self.out_dist = 0.5 * float(self.check_dist)
        self.xllc_dist = 0.5 * float(self.check_dist + 0.25)

        self.dis2sr = 0.1
        self.drill_layers = self.get_end_coupon_names()
        self.inplan = InPlan(self.job_name)
        self.lamin_data = self.inplan.getLaminData()
        #http://192.168.2.120:82/zentao/story-view-6298.html 增加任意介条件获取 20240109 by lyh
        self.job_split,self.anylayer = self.inplan.get_split_num()
        if "-lyh" in self.job_name:
            self.GEN.PAUSE(self.anylayer)
            
        self.laser_dielectric = self.inplan.get_laser_dielectric_thick()
        
        self.layer_cu_info = self.inplan.get_Layer_Info()        
        self.stackup_pp_foil_info = self.inplan.get_stackup_pp_foil_info()
        self.get_laser_config = self.inplan.get_laser_config()
        
        self.yh_num = None
        if len(self.lamin_data) == 0:
            warn_text.append({
                "content": u'Inplan中无料号:%s的压合数据,无法检测' % (self.inplan.JOB_SQL),
                "type": "critical",
            })
        else:
            for index, cur_lamin_dict in enumerate(self.lamin_data):
                self.lamin_data[index]['pnl_routx_mm'] = float(cur_lamin_dict['PNLROUTX']) * 25.4
                self.lamin_data[index]['pnl_routy_mm'] = float(cur_lamin_dict['PNLROUTY']) * 25.4
                if len(self.lamin_data) == 1 and self.lamin_data[index]['pnl_routx_mm'] == 0 and self.lamin_data[index]['pnl_routy_mm'] == 0:
                    # 单双面板的情况
                    self.lamin_data[index]['layer_list'] = ["l1", "l2"]
                else:
                    self.lamin_data[index]['layer_list'] = ['l%s' % i for i in range(int(cur_lamin_dict['FROMLAY'].strip('L')),
                                                                                     int(cur_lamin_dict['TOLAY'].strip(
                                                                                         'L')) + 1)]
                self.lamin_data[index]['cur_lamin_num'] = int(cur_lamin_dict['PROCESS_NUM']) - 1
                self.yh_num = max(self.yh_num, self.lamin_data[index]['cur_lamin_num'])
                self.lamin_data[index]['pnlx_mm'] = float(cur_lamin_dict['PNLXINCH']) * 25.4
                self.lamin_data[index]['pnly_mm'] = float(cur_lamin_dict['PNLYINCH']) * 25.4
                self.lamin_data[index]['cut_x'] = (float(cur_lamin_dict['PNLXINCH']) * 25.4 - float(
                    cur_lamin_dict['PNLROUTX']) * 25.4) * 0.5
                self.lamin_data[index]['cut_y'] = (float(cur_lamin_dict['PNLYINCH']) * 25.4 - float(
                    cur_lamin_dict['PNLROUTY']) * 25.4) * 0.5
            self.pnl_x = self.lamin_data[0]['pnlx_mm']
            self.pnl_y = self.lamin_data[0]['pnly_mm']

            self.pnl_cent_x = self.pnl_x * 0.5
            self.pnl_cent_y = self.pnl_y * 0.5
        # print json.dumps(self.lamin_data, indent=2)
        self.sr_xmin, self.sr_xmax, self.sr_ymin, self.sr_ymax, self.out_step, self.panel_repeat = self.get_SR_AREA()
        self.out_step = list(set(self.out_step))

        # === TODO 获取镭射层别列表，归类到压合中 ===
        self.long_side_cu = '__long_cu__'

    def __del__(self):
        self.GEN.COM('disp_on')

    def run(self):
        if len(self.lamin_data) == 0:
            return False
        if mode == 'check':
            items = [u"系统判断",  u"长边", u"短边",]
            item, okPressed = QtGui.QInputDialog.getItem(QtGui.QWidget(), u"夹头位置选择", u"夹头在长短边选择，若不想让系统自动判断，请选择下拉列表中的长边或短边:",
                                                         items, 0, False, Qt.Qt.WindowStaysOnTopHint)
            self.jiatou_area = unicode(item.toUtf8(), 'utf8', 'ignore').encode(
                        'gb2312').decode("cp936").strip()

            if not okPressed:
                sys.exit()
        else:
            self.jiatou_area = u"系统判断"
            
        self.GEN.COM('disp_off')
        self.GEN.OPEN_STEP(self.step_name)
        self.GEN.CHANGE_UNITS('mm')
        self.GEN.CLEAR_LAYER()
        self.GEN.VOF()
        self.GEN.DELETE_LAYER(self.flat_layer)
        self.GEN.DELETE_LAYER(self.out_step_fill)
        self.GEN.DELETE_LAYER(self.fill_layer)
        self.GEN.DELETE_LAYER(self.md_clip)
        self.GEN.DELETE_LAYER(self.md_cover)
        self.GEN.DELETE_LAYER(self.pnl_coupon_copper)
        self.GEN.CREATE_LAYER(self.fill_layer)
        self.GEN.CREATE_LAYER(self.pnl_coupon_copper)
        self.GEN.VON()
        self.fill_sr(self.step_name)
        self.flatten_layer()
        self.flatten_out_step_layer()
        self.fill_coupon_copper_in_panel()

        self.check_coupon_in_out_step()
        warn_mess = self.fill_panel_by_lamin()               

        # === 以下用于外部调用 ===
        # self.clip_panel_area()
        # self.check_panel_area()

        # self.GEN.VOF()
        # self.GEN.DELETE_LAYER(self.md_cover)
        # self.GEN.VON()
        # if len(warn_mess) != 0:
        #     msg_box = msgBox()
        #     msg_box.critical(None, '程序运行完成，检测到如下错误', '%s' % '\n'.join(warn_mess), QMessageBox.Ok)
        # else:
        #     msg_box = msgBox()
        #     msg_box.information(None, 'Step:%s五代靶检测' % self.step_name, '已完成！', QMessageBox.Ok)

    def get_job_laser_list(self):

        blind_list = []
        blind_Reg = re.compile(r'^s\d+-\d+$')

        # --从料号info中获取层别及信息
        info = self.GEN.DO_INFO('-t matrix -e %s/matrix -m script -d ROW' % self.job_name)
        for i, name in enumerate(info['gROWname']):
            context = info['gROWcontext'][i]
            layer_type = info['gROWlayer_type'][i]
            # --获取钻孔层
            if context == 'board' and layer_type == 'drill':
                # --匹配镭射钻孔层
                if blind_Reg.match(name):
                    blind_list.append(name)
                    
        return blind_list

    def get_SR_AREA(self):
        """
        获取edit|set|icg类step的SR尺寸
        :return:
        """
        gp = self.GEN.DO_INFO("-t step -e %s/%s -d REPEAT" % (self.job_name, self.step_name))
        sr_xmin = None
        sr_xmax = None
        sr_ymin = None
        sr_ymax = None
        step_reg = re.compile('set|edit|icg')
        out_step = []
        for index, step_name in enumerate(gp['gREPEATstep']):
            if step_reg.search(step_name):
                out_step.append(step_name)
                if not sr_xmin:
                    sr_xmin = float(gp['gREPEATxmin'][index])
                else:
                    sr_xmin = min(sr_xmin, float(gp['gREPEATxmin'][index]))

                if not sr_xmax:
                    sr_xmax = float(gp['gREPEATxmax'][index])
                else:
                    sr_xmax = max(sr_xmax, float(gp['gREPEATxmax'][index]))

                if not sr_ymin:
                    sr_ymin = float(gp['gREPEATymin'][index])
                else:
                    sr_ymin = min(sr_ymin, float(gp['gREPEATymin'][index]))

                if not sr_ymax:
                    sr_ymax = float(gp['gREPEATymax'][index])
                else:
                    sr_ymax = max(sr_ymax, float(gp['gREPEATymax'][index]))
        return sr_xmin, sr_xmax, sr_ymin, sr_ymax,out_step,gp

    def fill_sr(self, step_now):
        """
        填充子排版,如果子排版中还有子排版，会递归调用
        :return: None
        """
        fill_layer = self.fill_layer
        SR = self.get_step_list(step_now)
        for step in SR:
            if step in self.drill_layers:
                # === 尾孔模块不铺铜 ===
                continue
            self.GEN.OPEN_STEP(step)
            self.GEN.CHANGE_UNITS('mm')
            self.GEN.WORK_LAYER(fill_layer)
            # 每个step在fill的时候，都附加一个.string=step的属性
            self.GEN.COM('cur_atr_reset')
            self.GEN.COM('cur_atr_set,attribute=.string,text=%s' % step)
            sr_info = self.GEN.DO_INFO('-t step -e %s/%s -m script -d SR' % (self.job_name, step))

            out_dist = self.out_dist
            if step == 'xllc-coupon':
                out_dist = self.xllc_dist
            self.GEN.COM('sr_fill,polarity=%s,step_margin_x=%s,step_margin_y=%s,step_max_dist_x=%s,step_max_dist_y=%s,'
                         'sr_margin_x=%s,sr_margin_y=%s,sr_max_dist_x=%s,sr_max_dist_y=%s,nest_sr=no,stop_at_steps=,'
                         'consider_feat=no,consider_drill=no,consider_rout=no,dest=affected_layers,attributes=yes'
                         % ('positive', '-' + str(out_dist), '-' + str(out_dist), 2540, 2540, 0, 0, 0, 0))
            self.GEN.COM('cur_atr_reset')
            self.GEN.CLEAR_LAYER()
            self.GEN.CLOSE_STEP()
            if len(sr_info['gSRstep']) > 0:
                # --递归调用，子排版中存在子排版
                self.fill_sr(step)

    def get_step_list(self, cur_step='panel'):
        sr_list = []
        info = self.GEN.DO_INFO('-t step -e %s/%s -m script -d SR' % (self.job_name, cur_step))
        for step in info['gSRstep']:
            if step not in sr_list:
                sr_list.append(step)
        return sr_list

    def flatten_layer(self):
        self.GEN.OPEN_STEP(self.step_name)
        self.GEN.COM('flatten_layer,source_layer=%s,target_layer=%s' % (self.fill_layer, self.flat_layer))

    def flatten_out_step_layer(self):
        for o_step in self.out_step:
            self.GEN.OPEN_STEP(o_step)
            self.GEN.COM('flatten_layer,source_layer=%s,target_layer=%s' % (self.fill_layer, self.out_step_fill))
            self.GEN.AFFECTED_LAYER(self.out_step_fill,'yes')
            self.GEN.SEL_CONTOURIZE(breakSurface='no')
            self.GEN.CLOSE_STEP()
        self.GEN.OPEN_STEP(self.step_name)
        self.GEN.COM('flatten_layer,source_layer=%s,target_layer=%s' % (self.out_step_fill, self.pnl_out_copper))

    def fill_coupon_copper_in_panel(self):
        self.GEN.OPEN_STEP(self.step_name)
        # self.GEN.COM('flatten_layer,source_layer=%s,target_layer=%s' % (self.fill_layer, self.flat_layer))
        # for line in self.panel_repeat:
        #     print line
        self.GEN.CLEAR_LAYER()
        self.GEN.AFFECTED_LAYER(self.pnl_coupon_copper,'yes')
        for index, step_name in enumerate(self.panel_repeat['gREPEATstep']):
            if step_name not in self.out_step:
                x1 = self.panel_repeat['gREPEATxmin'][index]
                x2 = self.panel_repeat['gREPEATxmax'][index]
                y1 = self.panel_repeat['gREPEATymin'][index]
                y2 = self.panel_repeat['gREPEATymax'][index]
                self.add_area_copper(x1, x2, y1, y2, pol='positive')
        self.GEN.CLEAR_LAYER()

    def check_coupon_in_out_step(self):
        """
        检测模块在panel中是否进单元
        :return:
        """
        self.GEN.OPEN_STEP(self.step_name)
        error_layer = '__coupon_touch_sr__'
        self.GEN.DELETE_LAYER(error_layer)
        self.GEN.CLEAR_LAYER()
        self.GEN.FILTER_RESET()
        self.GEN.AFFECTED_LAYER(self.pnl_coupon_copper,'yes')
        self.GEN.SEL_REF_FEAT(self.pnl_out_copper,'touch')
        if int(self.GEN.GET_SELECT_COUNT()) > 0:
            self.GEN.SEL_COPY(error_layer)
            warn_text.append({
                "content": u'模块进单元，详见层别%s' % (error_layer),
                "type": "critical",
                "layers":[error_layer]
            })
        else:
            warn_text.append({
                "content": u'模块在panel中未进单元',
                "type": "information",
            })
            self.GEN.DELETE_LAYER(self.pnl_out_copper)
            self.GEN.DELETE_LAYER(self.pnl_coupon_copper)
        self.GEN.CLEAR_LAYER()

    def fill_panel_by_lamin(self):
        """
        BY 压合次数填铜，板外距离锣边5mm，距离拼版1mm（自定值，无0.1mm需求）
        :return:
        """
        warn_mess = []
        self.GEN.CLEAR_LAYER()
        # === 板边电镀夹头层 ===
        # check_clamping = self.check_clamping

        # === 板内区域层，目前主要用来看看 ===
        # pnlcu_in_sr = '__pnl_cu_in_sr'
        long_side_cu = self.long_side_cu
        # self.GEN.DELETE_LAYER(check_clamping)
        self.GEN.DELETE_LAYER(long_side_cu)
        # self.GEN.CREATE_LAYER(check_clamping)
        self.GEN.CREATE_LAYER(long_side_cu)

        # === 在sr区域填铜 ===
        # self.GEN.DELETE_LAYER(pnlcu_in_sr)
        # self.GEN.CREATE_LAYER(pnlcu_in_sr)
        # self.GEN.AFFECTED_LAYER(pnlcu_in_sr, 'yes')
        # self.add_area_copper(self.sr_xmin, self.sr_xmax, self.sr_ymin, self.sr_ymax, pol='positive')
        # self.GEN.AFFECTED_LAYER(pnlcu_in_sr, 'no')

        self.GEN.AFFECTED_LAYER(long_side_cu, 'yes')
        self.GEN.FILL_SUR_PARAMS()
        self.GEN.SR_FILL('positive', step_margin_x=0, step_margin_y=0, step_max_dist_x=self.sr_xmin,
                         step_max_dist_y=0, sr_margin_x=self.dis2sr, sr_margin_y=self.dis2sr, nest_sr='no')
        self.GEN.AFFECTED_LAYER(long_side_cu, 'no')

        for index, cur_lamin_dict in enumerate(self.lamin_data):
            coupons_in_area = 'no'
            if int(cur_lamin_dict['cur_lamin_num']) == self.yh_num:
                coupons_in_area = 'yes'
            warn_mess = self.check_v5_dld_in_area(cur_lamin_dict, warn_mess, coupons_in_area=coupons_in_area)

            if int(cur_lamin_dict['cur_lamin_num']) == 1:
                # === 当一压时，检测零压的dld ;电镀层，才检测干膜线5mm ===
                cur_lamin_dict['cur_lamin_num'] = 0
                cur_lamin_dict['cut_x'] = 0
                cur_lamin_dict['cut_y'] = 0
                cur_lamin_dict['layer_list'] = cur_lamin_dict['layer_list'][1:-1]
                if len(cur_lamin_dict['layer_list']) == 2:
                    start_num = cur_lamin_dict['layer_list'][0].strip('l')
                    end_num = cur_lamin_dict['layer_list'][1].strip('l')
                    b_layer = 'b%s-%s' % (start_num, end_num)
                    s_layer = 's%s-%s' % (start_num, end_num)
                    if self.GEN.LAYER_EXISTS(s_layer) == 'yes' or self.GEN.LAYER_EXISTS(b_layer) == 'yes':
                        j_clamp_chk = 'yes'
                    else:
                        j_clamp_chk = 'no'
                else:
                    j_clamp_chk = 'no'
                warn_mess = self.check_v5_dld_in_area(cur_lamin_dict, warn_mess, v5_check='no', clamp_chk=j_clamp_chk)

        self.GEN.DELETE_LAYER(long_side_cu)
        self.GEN.FILTER_RESET()
        return warn_mess

    def check_v5_dld_in_area(self, cur_lamin_dict, warn_mess, v5_check='yes', clamp_chk='yes', coupons_in_area='no'):
        """
        靶标（五代靶，DLD，标靶）是否在板边有效区域的检测
        :param cur_lamin_dict: dict类型，当前压合的信息
        :param warn_mess: list类型，用于传递错误信息的
        :param v5_check: yes|no是否进行五代靶检测
        :param clamp_chk: yes|no是否进行电镀夹头的检测
        :return: warn_mess 用于回传新增的错误信息
        """
        cur_fill_pnl = '__lamin_%s_cu' % cur_lamin_dict['cur_lamin_num']
        cur_dld_pnl = '__pnl_%s_dld' % cur_lamin_dict['cur_lamin_num']
        bars_layer = '__chk_v5bar_%s' % cur_lamin_dict['cur_lamin_num']
        v5_touch_clamp = '__v5_touch_clamp_%s' % cur_lamin_dict['cur_lamin_num']
        v5_not_in_gm = '__v5_not_in_gm_%s_' % cur_lamin_dict['cur_lamin_num']

        v5_top_bar = '__v5_top_bar_%s_' % cur_lamin_dict['cur_lamin_num']
        v5_bot_bar = '__v5_bot_bar_%s_' % cur_lamin_dict['cur_lamin_num']

        dlds_layer = '__chk_dld_%s' % cur_lamin_dict['cur_lamin_num']
        dld_not_in_area = '__dld_out_area_%s_' % cur_lamin_dict['cur_lamin_num']
        dld_not_in_dis30 = '__dld_not_in30dis_%s' % cur_lamin_dict['cur_lamin_num']
        dld_touch_clamp = '__dld_touch_clamp_%s' % cur_lamin_dict['cur_lamin_num']
        dld_not_in_gm = '__dld_not_in_gm_%s_' % cur_lamin_dict['cur_lamin_num']
        dld_not_only_in_long = '__dld_not_only_in_long_%s_' % cur_lamin_dict['cur_lamin_num']

        xbars_layer = '__chk_xbars_%s' % cur_lamin_dict['cur_lamin_num']
        xbar_touch_clamp = '__xbar_touch_clamp_%s' % cur_lamin_dict['cur_lamin_num']
        xbar_not_in_gm = '__xbar_not_in_gm_%s_' % cur_lamin_dict['cur_lamin_num']
        check_clamping = '_chk_clamping_%s' % cur_lamin_dict['cur_lamin_num']

        pe_layer = '__chk_pe_%s' % cur_lamin_dict['cur_lamin_num']
        pe_touch_clamp = '__pe_touch_clamp_%s' % cur_lamin_dict['cur_lamin_num']
        pe_not_in_gm = '__pe_not_in_gm_%s_' % cur_lamin_dict['cur_lamin_num']

        coupons_in_gm = '__coupons_in_gm__%s' % cur_lamin_dict['cur_lamin_num']
        coupons_touch_clamp = '__coupons_touch_clamp_%s' % cur_lamin_dict['cur_lamin_num']
        coupons_not_in_gm = '__coupons_not_in_gm_%s_' % cur_lamin_dict['cur_lamin_num']

        cur_tlyr = cur_lamin_dict['layer_list'][0]
        cur_blyr = cur_lamin_dict['layer_list'][-1]

        gm_area = '__gm_%s_%s_' % (cur_tlyr, cur_blyr)
        delete_layers = [cur_fill_pnl, cur_dld_pnl, bars_layer, dlds_layer, dld_not_in_area, dld_not_in_dis30,
                         dld_touch_clamp, dld_not_in_gm, dld_not_only_in_long, xbars_layer, xbar_touch_clamp,
                         xbar_not_in_gm, cur_fill_pnl, gm_area, check_clamping, coupons_in_gm, v5_touch_clamp,
                         v5_not_in_gm, coupons_touch_clamp, coupons_not_in_gm, v5_top_bar, v5_bot_bar,pe_layer,
                         pe_touch_clamp, pe_not_in_gm ]
        persist_layer_list = []

        for dlayer in delete_layers:
            self.GEN.DELETE_LAYER(dlayer)

        self.GEN.CREATE_LAYER(cur_fill_pnl)
        self.GEN.CREATE_LAYER(cur_dld_pnl)
        self.GEN.CREATE_LAYER(check_clamping)

        fill_x = cur_lamin_dict['cut_x'] + 5
        fill_y = cur_lamin_dict['cut_y'] + 5
        dld_xs = cur_lamin_dict['cut_x'] + 38
        dld_xe = cur_lamin_dict['cut_x'] + 92

        # dld_ys = cur_lamin_dict['cut_y'] + 50
        # dld_ye = cur_lamin_dict['cut_y'] + 80
        self.GEN.AFFECTED_LAYER(cur_fill_pnl, 'yes')
        self.GEN.FILL_SUR_PARAMS()
        self.GEN.SR_FILL('positive', step_margin_x=fill_x, step_margin_y=fill_y, step_max_dist_x=2540,
                         step_max_dist_y=2540, sr_margin_x=self.dis2sr, sr_margin_y=self.dis2sr, nest_sr='no')
        self.GEN.AFFECTED_LAYER(cur_fill_pnl, 'no')
        # === 短边dld检测层填铜 ===
        self.GEN.AFFECTED_LAYER(cur_dld_pnl, 'yes')
        self.GEN.SR_FILL('positive', step_margin_x=dld_xs, step_margin_y=fill_y, step_max_dist_x=dld_xe,
                         step_max_dist_y=fill_y, sr_margin_x=self.dis2sr, sr_margin_y=self.dis2sr, nest_sr='no')
        self.GEN.AFFECTED_LAYER(cur_dld_pnl, 'no')

        # === 创建干膜线层 ===
        self.GEN.AFFECTED_LAYER(cur_tlyr, 'yes')
        self.GEN.AFFECTED_LAYER(cur_blyr, 'yes')
        self.GEN.FILTER_RESET()
        self.GEN.FILTER_SET_TYP('line')
        self.GEN.FILTER_SET_INCLUDE_SYMS('r1')
        self.GEN.FILTER_SELECT()
        if int(self.GEN.GET_SELECT_COUNT()) != 8:
            self.GEN.CLEAR_LAYER()
            warn_text.append({
                "content": u'层别:%s,干膜线数量不为8,不能进行标靶是否在干膜内5mm的检查' % (','.join([cur_tlyr, cur_blyr])),
                "type": "critical",
                'layers': [cur_tlyr, cur_blyr]
            })
        else:
            self.GEN.SEL_COPY(gm_area)
            self.GEN.CLEAR_LAYER()
            self.GEN.AFFECTED_LAYER(gm_area, 'yes')
            self.GEN.COM('sel_polarity,polarity=positive')
            # === 线转铜皮 ===
            self.GEN.SEL_CUT_DATA(ignore_width='yes')
            self.GEN.SEL_RESIZE('-6000')
            self.GEN.AFFECTED_LAYER(gm_area, 'no')
            # === 删除转铜生成的+++层
            self.GEN.DELETE_LAYER('%s+++' % gm_area)
        self.GEN.CLEAR_LAYER()

        # === 创建电镀夹头区域 ===
        clamp_cu_area_x = cur_lamin_dict['cut_x']
        clamp_cu_area_y = cur_lamin_dict['cut_y']
        if len(self.lamin_data) == 1:
            # 只有一次压合时按开料尺寸来计算
            clamp_cu_area_x = 0
            clamp_cu_area_y = 0

        self.GEN.AFFECTED_LAYER(check_clamping, 'yes')
        if self.jiatou_area == u"系统判断":            
            if float(cur_lamin_dict['PNLROUTY']) >= 24.5:
                range_list = [(2.5, 80), (155, 225), (self.pnl_cent_y - clamp_cu_area_x - 35, self.pnl_cent_y - clamp_cu_area_x)]
                self.add_surface_c(dis_x=10 + clamp_cu_area_x,range_list=range_list, pol='positive')
            else:
                range_list = [(2.5, 80), (155, 225), (self.pnl_cent_x - clamp_cu_area_y - 35, self.pnl_cent_x - clamp_cu_area_y)]
                self.add_surface_b(dis_y=10 + clamp_cu_area_y, range_list=range_list,pol='positive')
        else:
            if self.jiatou_area == u"长边":
                range_list = [(2.5, 80), (155, 225), (self.pnl_cent_y - clamp_cu_area_x - 35, self.pnl_cent_y - clamp_cu_area_x)]
                self.add_surface_c(dis_x=10 + clamp_cu_area_x,range_list=range_list, pol='positive')
            else:
                range_list = [(2.5, 80), (155, 225), (self.pnl_cent_x - clamp_cu_area_y - 35, self.pnl_cent_x - clamp_cu_area_y)]
                self.add_surface_b(dis_y=10 + clamp_cu_area_y, range_list=range_list,pol='positive')
                
        self.GEN.AFFECTED_LAYER(check_clamping, 'no')

        if v5_check == 'yes':
            # === 1.0检测五代靶
            # === 1.1检测五代靶是否在有效区域内裁磨5mm ====
            self.GEN.AFFECTED_LAYER(cur_tlyr, 'yes')
            self.GEN.AFFECTED_LAYER(cur_blyr, 'yes')

            self.GEN.FILTER_RESET()
            self.GEN.FILTER_SET_INCLUDE_SYMS('hdi-dwpad')
            self.GEN.FILTER_SELECT()
            self.GEN.FILTER_RESET()

            if int(self.GEN.GET_SELECT_COUNT()) > 0:
                self.GEN.SEL_COPY(bars_layer)
                self.GEN.CLEAR_LAYER()
                self.GEN.AFFECTED_LAYER(bars_layer, 'yes')
                # === 避免标靶负片影响，改为s5080 ===
                self.GEN.SEL_CHANEG_SYM('s5080')
                self.GEN.SEL_REF_FEAT(cur_fill_pnl, 'cover')
                # if int(self.GEN.GET_SELECT_COUNT()) > 0:
                #     self.GEN.SEL_DELETE()
                self.GEN.SEL_REVERSE()
                if int(self.GEN.GET_SELECT_COUNT()) > 0:
                    self.GEN.CLEAR_LAYER()
                    warn_text.append({
                        "content": u'压合:%s,有五代靶未设计在压合锣边5mm内,详见层别:%s,%s' % (
                            cur_lamin_dict['cur_lamin_num'], cur_fill_pnl, bars_layer),
                        "type": "critical",
                        "layers":[bars_layer,cur_fill_pnl]
                    })
                    persist_layer_list += [cur_fill_pnl, bars_layer]
                else:
                    warn_text.append({
                        "content": u'压合:%s,有五代靶设计在压合锣边5mm内' % (cur_lamin_dict['cur_lamin_num']),
                        "type": "information",
                    })
                # else:
                #     # self.GEN.DELETE_LAYER(cur_fill_pnl)
                #     self.GEN.DELETE_LAYER(bars_layer)
                # === 1.2 检测五代靶是否与电镀夹头区域相交
                self.GEN.CLEAR_LAYER()
                self.GEN.AFFECTED_LAYER(bars_layer, 'yes')
                self.GEN.FILTER_RESET()
                self.GEN.SEL_REF_FEAT(check_clamping, 'touch')
                if int(self.GEN.GET_SELECT_COUNT()) > 0:
                    self.GEN.SEL_COPY(v5_touch_clamp)
                    warn_text.append({
                        "content": u'层别:%s,五代靶与电镀夹头区域相交,详见层别%s,%s' % (
                            ','.join([cur_tlyr, cur_blyr]), v5_touch_clamp, check_clamping),
                        "type": "critical",
                        "layers": [v5_touch_clamp, check_clamping, cur_tlyr, cur_blyr]
                    })
                    persist_layer_list += [v5_touch_clamp, check_clamping]
                else:
                    warn_text.append({
                        "content": u'层别:%s,五代靶与电镀夹头区域不相交' % (','.join([cur_tlyr, cur_blyr])),
                        "type": "information",
                    })
                self.GEN.CLEAR_LAYER()
                # === 1.3 检测是否在干膜线5mm内 ===
                if self.GEN.LAYER_EXISTS(gm_area) == 'yes':
                    self.GEN.AFFECTED_LAYER(bars_layer, 'yes')
                    self.GEN.SEL_CHANEG_SYM('s4000')
                    self.GEN.FILTER_RESET()
                    self.GEN.SEL_REF_FEAT(gm_area, 'cover')
                    self.GEN.SEL_REVERSE()
                    if int(self.GEN.GET_SELECT_COUNT()) > 0:
                        self.GEN.SEL_COPY(v5_not_in_gm)
                        warn_text.append({
                            "content": u'层别:%s,五代靶靶中心距离干膜线不足5mm,详见层别%s,%s' % (
                                ','.join([cur_tlyr, cur_blyr]), v5_not_in_gm, gm_area),
                            "type": "critical",
                            "layers": [v5_not_in_gm, gm_area,cur_tlyr, cur_blyr]
                        })
                        persist_layer_list += [v5_not_in_gm, gm_area]
                    else:
                        warn_text.append({
                            "content": u'层别:%s,五代靶在干膜线有效范围内' % (','.join([cur_tlyr, cur_blyr])),
                            "type": "information",
                        })
                    self.GEN.CLEAR_LAYER()
            else:
                self.GEN.CLEAR_LAYER()
                if cur_lamin_dict["V5LASER"] == '1':
                    warn_text.append({
                        "content": u'压合:%s,应设计五代靶,但未设计' % (cur_lamin_dict['cur_lamin_num']),
                        "type": "warning",
                    })
                # else:
                #     warn_text.append({
                #         "content": u'压合:%s,inplan中未设计五代靶' % (cur_lamin_dict['cur_lamin_num']),
                #         "type": "warning",
                #     })
            # === 1.4 五代靶的1通2，1通3设计
            self.GEN.AFFECTED_LAYER(cur_tlyr, 'yes')
            self.GEN.FILTER_RESET()
            self.GEN.FILTER_SET_INCLUDE_SYMS('hdi-dwpad')
            self.GEN.FILTER_SELECT()
            top_v5_num = int(self.GEN.GET_SELECT_COUNT())
            if top_v5_num > 0:
                # 按panel的添加工规则 1to3 1to4等取最深层加五代靶 其余层次不检测                
                for num in range(1, 10)[::-1]:
                    laser_drill_layer = "s{0}-{1}".format(int(cur_tlyr[1:]), int(cur_tlyr[1:]) + num)
                    if self.GEN.LAYER_EXISTS(laser_drill_layer) == 'yes' and \
                       laser_drill_layer in [i["layer_name"] for i in self.get_laser_config ]:
                        break
                    
                check_result = self.get_v5_check_type(laser_drill_layer,
                                                      self.laser_dielectric[cur_tlyr]['drill_depth'],
                                                      "top",
                                                      int(cur_tlyr[1:]))
                
                next_one_layer = 'l%s' % (int(cur_tlyr[1:]) + 1)
                next_two_layer = 'l%s' % (int(cur_tlyr[1:]) + 2)

                self.GEN.SEL_COPY(v5_top_bar)
                self.GEN.CLEAR_LAYER()
                self.GEN.AFFECTED_LAYER(v5_top_bar,'yes')
                # === 更改标靶为实体 ===
                self.GEN.SEL_CHANEG_SYM('s6000')
                #if (float(self.laser_dielectric[cur_tlyr]['drill_depth']) >= 2.1 and self.anylayer == "yes") or \
                   #self.anylayer == "no":
                if check_result == "1to2":                    
                    # === 大于等于2.1 1通2
                    self.GEN.FILTER_RESET()
                    self.GEN.SEL_REF_FEAT(next_one_layer,'include',pol='positive',f_type='pad',include='s5080')
                    include_num = int(self.GEN.GET_SELECT_COUNT())
                    if include_num != top_v5_num:
                        warn_text.append({
                        "content": u'层别:%s,五代靶应设计为1通2,但层:%s s5080的Symbol应选中数:%s,实际选中数:%s,请检查五代靶hdi-dwpad跟下方s5080的位置是否有偏移！！' % (cur_tlyr,next_one_layer,top_v5_num,include_num),
                        "type": "critical",
                        "layers":[v5_top_bar,next_one_layer]
                        })
                    self.GEN.CLEAR_LAYER()
                else:
                    # === 大于等于2.1 1通3
                    self.GEN.FILTER_RESET()
                    self.GEN.SEL_REF_FEAT(next_one_layer,'include',pol='negative',f_type='pad',include='s5080')
                    include_num = int(self.GEN.GET_SELECT_COUNT())
                    if include_num != top_v5_num:
                        warn_text.append({
                        "content": u'层别:%s,五代靶应设计为1通3,但层:%s s5080的Symbol应选中数:%s,实际选中数:%s,请检查五代靶hdi-dwpad跟下方s5080的位置是否有偏移！！' % (cur_tlyr,next_one_layer,top_v5_num,include_num),
                        "type": "critical",
                        "layers":[v5_top_bar,next_one_layer]
                        })
                    self.GEN.FILTER_RESET()
                    self.GEN.CLEAR_LAYER()
                    #增加过滤元素 防止误判 20231226 by lyh
                    self.GEN.FILTER_SET_INCLUDE_SYMS('hdi-dwpad')
                    self.GEN.AFFECTED_LAYER(cur_tlyr, 'yes')
                    self.GEN.SEL_REF_FEAT(next_two_layer,'include',pol='positive',f_type='pad',include='s5080')
                    include_num = int(self.GEN.GET_SELECT_COUNT())
                    if include_num != top_v5_num:
                        warn_text.append({
                        "content": u'层别:%s,五代靶应设计为1通3,但层:%s s5080的Symbol应选中数:%s,实际选中数:%s,请检查五代靶hdi-dwpad跟下方s5080的位置是否有偏移！！' % (cur_tlyr,next_two_layer,top_v5_num,include_num),
                        "type": "critical",
                        "layers":[v5_top_bar,next_two_layer]
                        })
                    self.GEN.CLEAR_LAYER()

            self.GEN.AFFECTED_LAYER(cur_blyr, 'yes')
            self.GEN.FILTER_RESET()
            self.GEN.FILTER_SET_INCLUDE_SYMS('hdi-dwpad')
            self.GEN.FILTER_SELECT()
            bot_v5_num = int(self.GEN.GET_SELECT_COUNT())
            if bot_v5_num > 0:
                # 按panel的添加工规则 1to3 1to4等取最深层加五代靶 其余层次不检测                
                for num in range(1, 10)[::-1]:
                    laser_drill_layer = "s{0}-{1}".format(int(cur_blyr[1:]), int(cur_blyr[1:]) - num)
                    if self.GEN.LAYER_EXISTS(laser_drill_layer) == 'yes' and \
                       laser_drill_layer in [i["layer_name"] for i in self.get_laser_config ]:
                        break
                    
                check_result = self.get_v5_check_type(laser_drill_layer,
                                                      self.laser_dielectric[cur_blyr]['drill_depth'],
                                                      "bot",
                                                      int(cur_blyr[1:]))
                
                next_one_layer = 'l%s' % (int(cur_blyr[1:]) - 1)
                next_two_layer = 'l%s' % (int(cur_blyr[1:]) - 2)
                self.GEN.SEL_COPY(v5_bot_bar)
                self.GEN.CLEAR_LAYER()
                self.GEN.AFFECTED_LAYER(v5_bot_bar,'yes')
                # === 更改标靶为实体 ===
                self.GEN.SEL_CHANEG_SYM('s6000')
                #if (float(self.laser_dielectric[cur_blyr]['drill_depth']) >= 2.1 and self.anylayer == "yes") or \
                   #self.anylayer == "no":
                if check_result == "1to2":                    
                    # === 大于等于2.1 1通2
                    self.GEN.FILTER_RESET()
                    self.GEN.SEL_REF_FEAT(next_one_layer,'include',pol='positive',f_type='pad',include='s5080')
                    include_num = int(self.GEN.GET_SELECT_COUNT())
                    if include_num != bot_v5_num:
                        warn_text.append({
                        "content": u'层别:%s,五代靶应设计为1通2,但层:%s s5080的Symbol应选中数:%s,实际选中数:%s,请检查五代靶hdi-dwpad跟下方s5080的位置是否有偏移！！' % (cur_blyr,next_one_layer,bot_v5_num,include_num),
                        "type": "critical",
                        "layers":[v5_bot_bar,next_one_layer]
                        })
                    self.GEN.CLEAR_LAYER()
                else:
                    # === 大于等于2.1 1通3
                    self.GEN.FILTER_RESET()
                    self.GEN.SEL_REF_FEAT(next_one_layer,'include',pol='negative',f_type='pad',include='s5080')
                    include_num = int(self.GEN.GET_SELECT_COUNT())
                    if include_num != bot_v5_num:
                        warn_text.append({
                        "content": u'层别:%s,五代靶应设计为1通3,但层:%s s5080的Symbol应选中数:%s,实际选中数:%s,请检查五代靶hdi-dwpad跟下方s5080的位置是否有偏移！！' % (cur_blyr,next_one_layer,bot_v5_num,include_num),
                        "type": "critical",
                        "layers":[v5_bot_bar,next_one_layer]
                        })
                    self.GEN.FILTER_RESET()
                    self.GEN.CLEAR_LAYER()
                    #增加过滤元素 防止误判 20231226 by lyh
                    self.GEN.FILTER_SET_INCLUDE_SYMS('hdi-dwpad')
                    self.GEN.AFFECTED_LAYER(cur_blyr, 'yes')
                    self.GEN.SEL_REF_FEAT(next_two_layer,'include',pol='positive',f_type='pad',include='s5080')
                    include_num = int(self.GEN.GET_SELECT_COUNT())
                    if include_num != bot_v5_num:
                        warn_text.append({
                        "content": u'层别:%s,五代靶应设计为1通3,但层:%s s5080的Symbol应选中数:%s,实际选中数:%s,请检查五代靶hdi-dwpad跟下方s5080的位置是否有偏移！！' % (cur_blyr,next_two_layer,bot_v5_num,include_num),
                        "type": "critical",
                        "layers":[v5_bot_bar,next_two_layer]
                        })
                    self.GEN.CLEAR_LAYER()

        # === 2. 检测dld是否在有效区域内裁磨5mm ====
        self.GEN.CLEAR_LAYER()
        self.GEN.AFFECTED_LAYER(cur_tlyr, 'yes')
        self.GEN.AFFECTED_LAYER(cur_blyr, 'yes')

        self.GEN.FILTER_RESET()
        self.GEN.FILTER_SET_INCLUDE_SYMS('sh-ldi')
        self.GEN.FILTER_SELECT()
        self.GEN.FILTER_RESET()
        if int(self.GEN.GET_SELECT_COUNT()) > 0:
            self.GEN.SEL_COPY(dlds_layer)
            #  === 2.1 检测是否在锣边有效区域内 ===
            self.GEN.CLEAR_LAYER()
            self.GEN.AFFECTED_LAYER(dlds_layer, 'yes')
            # === 忽略负片影响，更改sh-ldi为s3500进行检测
            self.GEN.SEL_CHANEG_SYM('s3500')
            self.GEN.SEL_REF_FEAT(cur_fill_pnl, 'cover')
            # if int(self.GEN.GET_SELECT_COUNT()) > 0:
            #     # === dld标靶不删除,用于后续检测 ===
            #     self.GEN.SEL_DELETE()
            self.GEN.SEL_REVERSE()
            if int(self.GEN.GET_SELECT_COUNT()) > 0:
                self.GEN.SEL_COPY(dld_not_in_area)
                self.GEN.CLEAR_LAYER()
                warn_text.append({
                    "content": u'层别:%s,有dld未设计在压合锣边5mm内,详见层别:%s,%s' % (
                        ','.join([cur_tlyr, cur_blyr]), cur_fill_pnl, dld_not_in_area),
                    "type": "critical",
                    'layers': [dld_not_in_area, cur_fill_pnl, cur_tlyr, cur_blyr]
                })

                persist_layer_list += [cur_fill_pnl, dld_not_in_area]
            else:
                warn_text.append({
                    "content": u'层别:%s,有dld均设计在压合锣边5mm内' % (','.join([cur_tlyr, cur_blyr])),
                    "type": "information",
                })

            # else:
            #     self.GEN.DELETE_LAYER(dlds_layer)
            # === 2.2 判断dld是在长边还是短边 ===
            # dld_in_long_yn = None
            self.GEN.CLEAR_LAYER()
            self.GEN.AFFECTED_LAYER(dlds_layer, 'yes')
            self.GEN.FILTER_RESET()
            self.GEN.SEL_REF_FEAT(self.long_side_cu, 'cover')
            if int(self.GEN.GET_SELECT_COUNT()) > 0:
                self.GEN.SEL_REVERSE()                
                dld_in_long_yn = 'yes'
                if int(self.GEN.GET_SELECT_COUNT()) > 0:
                    self.GEN.SEL_COPY(dld_not_only_in_long)
                    warn_text.append({
                        "content": u'层别:%s,有dld未单纯设计在长边,查看层别%s' % (
                        ','.join([cur_tlyr, cur_blyr]), dld_not_only_in_long),
                        "type": "warning",
                        "layers":[dld_not_only_in_long,cur_tlyr, cur_blyr]
                    })
                    # warn_mess.append('层别：%s,有dld未单纯设计在长边,查看层别%s' % ([cur_tlyr, cur_blyr], dld_not_only_in_long))
                    dld_in_long_yn = 'no'
                    persist_layer_list += [dld_not_only_in_long]
            else:
                dld_in_long_yn = 'no'
            self.GEN.CLEAR_LAYER()
            #  === 2.3 dld 在短边时，判断是否添加在40-90的范围内，且不与电镀夹头区域相交，且在干膜线内5mm
            if dld_in_long_yn == 'no' or dld_in_long_yn == 'yes':
                if self.job_split != 'yes':
                    if not self.job_split:
                        warn_text.append({
                            "content": u'料号:%s,在inplan中无数据，使用不分割进行检测DLD' % (self.job_name),
                            "type": "warning",
                        })
                    if self.job_split == 'unknown':
                        warn_text.append({
                            "content": u'料号:%s,在inplan中无分割参数为%s的数据，使用不分割进行检测DLD' % (self.job_name, self.job_split),
                            "type": "warning",
                        })
                    #短边才检测50-80范围
                    if dld_in_long_yn == 'no':
                        # === 2.3.1 检测是否在短边50-80范围 ===
                        self.GEN.AFFECTED_LAYER(dlds_layer, 'yes')
                        self.GEN.FILTER_RESET()
                        self.GEN.SEL_REF_FEAT(cur_dld_pnl, 'cover')
                        self.GEN.SEL_REVERSE()
                        if int(self.GEN.GET_SELECT_COUNT()) > 0:
                            self.GEN.SEL_COPY(dld_not_in_dis30)
                            warn_text.append({
                                "content": u'层别:%s,dld未在短边40-90范围内,详见层别%s,%s' % (
                                    ','.join([cur_tlyr, cur_blyr]), dld_not_in_dis30, cur_dld_pnl),
                                "type": "critical",
                                "layers": [dld_not_in_dis30, cur_dld_pnl, cur_tlyr, cur_blyr]
                            })
                            persist_layer_list += [dld_not_in_dis30, cur_dld_pnl]
                        self.GEN.CLEAR_LAYER()
                else:
                    warn_text.append({
                        "content": u'层别:%s,料号为分割料号,不进行dld在短边40-90范围的检测' % (','.join([cur_tlyr, cur_blyr])),
                        "type": "information",
                    })
                # === 2.3.2 检测是否与电镀夹头区域相交 ===
                if clamp_chk == 'yes':
                    self.GEN.AFFECTED_LAYER(dlds_layer, 'yes')
                    self.GEN.FILTER_RESET()
                    self.GEN.SEL_REF_FEAT(check_clamping, 'touch')
                    if int(self.GEN.GET_SELECT_COUNT()) > 0:
                        self.GEN.SEL_COPY(dld_touch_clamp)
                        warn_text.append({
                            "content": u'层别:%s,dld与电镀夹头区域相交,详见层别%s,%s' % (
                                ','.join([cur_tlyr, cur_blyr]), dld_touch_clamp, check_clamping),
                            "type": "critical",
                            "layers": [dld_touch_clamp, check_clamping, cur_tlyr, cur_blyr]
                        })
                        persist_layer_list += [dld_touch_clamp, check_clamping]
                    else:
                        warn_text.append({
                            "content": u'层别:%s,dld与电镀夹头区域不相交' % (','.join([cur_tlyr, cur_blyr])),
                            "type": "information",
                        })
                self.GEN.CLEAR_LAYER()
                # === 2.3.3 检测是否在干膜线5mm内 ===
                if self.GEN.LAYER_EXISTS(gm_area) == 'yes':
                    self.GEN.AFFECTED_LAYER(dlds_layer, 'yes')
                    self.GEN.SEL_CHANEG_SYM('s4000')
                    self.GEN.FILTER_RESET()
                    self.GEN.SEL_REF_FEAT(gm_area, 'cover')
                    self.GEN.SEL_REVERSE()
                    if int(self.GEN.GET_SELECT_COUNT()) > 0:
                        self.GEN.SEL_COPY(dld_not_in_gm)
                        warn_text.append({
                            "content": u'层别:%s,dld靶中心距离干膜线不足5mm,详见层别%s,%s' % (
                                ','.join([cur_tlyr, cur_blyr]), dld_not_in_gm, gm_area),
                            "type": "critical",
                            "layers": [dld_not_in_gm, gm_area, cur_tlyr, cur_blyr],
                        })
                    else:
                        warn_text.append({
                            "content": u'层别:%s,dld靶中心在干膜线已大于5mm' % (','.join([cur_tlyr, cur_blyr])),
                            "type": "information",
                        })

                    self.GEN.CLEAR_LAYER()
        # === 3. 检测标靶是否在有效区域内 ====
        self.GEN.CLEAR_LAYER()
        self.GEN.AFFECTED_LAYER(cur_tlyr, 'yes')
        self.GEN.AFFECTED_LAYER(cur_blyr, 'yes')

        self.GEN.FILTER_RESET()
        self.GEN.FILTER_SET_INCLUDE_SYMS('hdi1-ba*\;hdi1-baj*\;hdi1-bs*\;sh-dwtop\;sh-dwbot\;hdi-dwtop-tt\;hdi-dwbot-tt')
        self.GEN.FILTER_SELECT()
        if int(self.GEN.GET_SELECT_COUNT()) > 0:
            self.GEN.SEL_COPY(xbars_layer)
            self.GEN.CLEAR_LAYER()
            if clamp_chk == 'yes':
                self.GEN.AFFECTED_LAYER(xbars_layer, 'yes')
                # === 3.1 检测靶位是否与电镀夹头区域相交 ===
                self.GEN.FILTER_RESET()
                self.GEN.SEL_REF_FEAT(check_clamping, 'touch')
                if int(self.GEN.GET_SELECT_COUNT()) > 0:
                    self.GEN.SEL_COPY(xbar_touch_clamp)
                    warn_text.append({
                        "content": u'层别:%s,X_Ray 靶位与电镀夹头区域相交,详见层别%s,%s' % (
                            ','.join([cur_tlyr, cur_blyr]), xbar_touch_clamp, check_clamping),
                        "type": "critical",
                        "layers": [xbar_touch_clamp, check_clamping, cur_tlyr, cur_blyr],
                    })
                    # warn_mess.append('层别:%s,X_Ray 靶位与电镀夹头区域相交,详见层别%s,%s' % (
                    #     [cur_tlyr, cur_blyr], xbar_touch_clamp, check_clamping))
                    persist_layer_list += [xbar_touch_clamp, check_clamping]
                else:
                    warn_text.append({
                        "content": u'层别:%s,X_Ray 靶位与电镀夹头区域不相交' % (','.join([cur_tlyr, cur_blyr])),
                        "type": "information",
                    })
                self.GEN.CLEAR_LAYER()
            # === 3.2 检测靶位是否在干膜线5mm内 ===
            if self.GEN.LAYER_EXISTS(gm_area) == 'yes':
                self.GEN.AFFECTED_LAYER(xbars_layer, 'yes')
                self.GEN.SEL_CHANEG_SYM('s4000')
                self.GEN.FILTER_RESET()
                self.GEN.SEL_REF_FEAT(gm_area, 'cover')
                self.GEN.SEL_REVERSE()
                if int(self.GEN.GET_SELECT_COUNT()) > 0:
                    self.GEN.SEL_COPY(xbar_not_in_gm)
                    warn_text.append({
                        "content": u'层别:%s,X_Ray 靶中心距离干膜线不足5mm,详见层别%s,%s' % (
                            ','.join([cur_tlyr, cur_blyr]), xbar_not_in_gm, gm_area),
                        "type": "critical",
                        "layers": [xbar_not_in_gm, gm_area, cur_tlyr, cur_blyr],
                    })
                    # warn_mess.append('层别:%s,X_Ray 靶位未在干膜线范围内，详见层别%s,%s' % (
                    #     [cur_tlyr, cur_blyr], xbar_not_in_gm, gm_area))
                    persist_layer_list += [xbar_not_in_gm, gm_area]
                else:
                    warn_text.append({
                        "content": u'层别:%s,X_Ray 靶位在干膜线有效范围内' % (','.join([cur_tlyr, cur_blyr])),
                        "type": "information",
                    })
                self.GEN.CLEAR_LAYER()

        # === 3.3铆钉类symbol是否在干膜线5mm内
        self.GEN.CLEAR_LAYER()
        self.GEN.AFFECTED_LAYER(cur_tlyr, 'yes')
        self.GEN.AFFECTED_LAYER(cur_blyr, 'yes')

        self.GEN.FILTER_RESET()
        self.GEN.FILTER_SET_INCLUDE_SYMS('sh-bb\;sh-bb1\;sh-b12013\;sh-b2013\;sh-rj3\;sh-fdk\;hdi1-mdk-t\;hdi1-mdk-b')
        self.GEN.FILTER_SELECT()
        if int(self.GEN.GET_SELECT_COUNT()) > 0:
            self.GEN.SEL_COPY(pe_layer)
            self.GEN.CLEAR_LAYER()
            if clamp_chk == 'yes':
                self.GEN.AFFECTED_LAYER(pe_layer, 'yes')
                # === 3.1 检测靶位是否与电镀夹头区域相交 ===
                self.GEN.FILTER_RESET()
                self.GEN.SEL_REF_FEAT(check_clamping, 'touch')
                if int(self.GEN.GET_SELECT_COUNT()) > 0:
                    self.GEN.SEL_COPY(pe_touch_clamp)
                    warn_text.append({
                        "content": u'层别:%s,PE 靶位与电镀夹头区域相交,详见层别%s,%s' % (
                            ','.join([cur_tlyr, cur_blyr]), pe_touch_clamp, check_clamping),
                        "type": "critical",
                        "layers": [pe_touch_clamp, check_clamping, cur_tlyr, cur_blyr],
                    })
                    persist_layer_list += [pe_touch_clamp, check_clamping]
                else:
                    warn_text.append({
                        "content": u'层别:%s,PE 靶位与电镀夹头区域不相交' % (','.join([cur_tlyr, cur_blyr])),
                        "type": "information",
                    })
                self.GEN.CLEAR_LAYER()
            # === 3.4 检测靶位是否在干膜线5mm内 ===
            if self.GEN.LAYER_EXISTS(gm_area) == 'yes':
                self.GEN.AFFECTED_LAYER(pe_layer, 'yes')
                self.GEN.FILTER_RESET()
                self.GEN.FILTER_SET_INCLUDE_SYMS('sh-bb\;sh-bb1\;sh-b12013\;sh-b2013')
                self.GEN.FILTER_SELECT()
                if int(self.GEN.GET_SELECT_COUNT()) > 0:
                    self.GEN.SEL_CHANEG_SYM('r762')
                self.GEN.FILTER_RESET()
                self.GEN.FILTER_SET_INCLUDE_SYMS('sh-rj3\;sh-fdk\;hdi1-mdk-t\;hdi1-mdk-b')
                self.GEN.FILTER_SELECT()
                if int(self.GEN.GET_SELECT_COUNT()) > 0:
                    self.GEN.SEL_CHANEG_SYM('s4000')
                self.GEN.FILTER_RESET()
                self.GEN.SEL_REF_FEAT(gm_area, 'cover')
                self.GEN.SEL_REVERSE()
                if int(self.GEN.GET_SELECT_COUNT()) > 0:
                    self.GEN.SEL_COPY(pe_not_in_gm)
                    warn_text.append({
                        "content": u'层别:%s,PE 靶中心距离干膜线不满足要求：PE光点边距3mm，铆钉中心距5mm,详见层别%s,%s' % (
                            ','.join([cur_tlyr, cur_blyr]), pe_not_in_gm, gm_area),
                        "type": "critical",
                        "layers": [pe_not_in_gm, gm_area, cur_tlyr, cur_blyr],
                    })
                    persist_layer_list += [pe_not_in_gm, gm_area]
                else:
                    warn_text.append({
                        "content": u'层别:%s,PE 靶位在干膜线有效范围内' % (','.join([cur_tlyr, cur_blyr])),
                        "type": "information",
                    })
                self.GEN.CLEAR_LAYER()


        self.GEN.CLEAR_LAYER()
        # === 4.板边模块检测
        # === 4.1 检测最后一次压合时，板边模块是否在干膜4mm有效区域内。
        if coupons_in_area == 'yes':
            if self.GEN.LAYER_EXISTS(gm_area) == 'yes':
                self.GEN.AFFECTED_LAYER(gm_area, 'yes')
                # === 干膜层是-5mm进行检测，coupon在干膜中是检测3mm （+2000 + 250） * 2===
                # === coupon铺铜,多出单边0.25mm
                self.GEN.SEL_COPY(coupons_in_gm, size='500')
                self.GEN.AFFECTED_LAYER(gm_area, 'no')
                self.GEN.AFFECTED_LAYER(self.flat_layer, 'yes')
                self.GEN.FILTER_RESET()
                self.GEN.SEL_REF_FEAT(coupons_in_gm, 'cover')
                if int(self.GEN.GET_SELECT_COUNT()) > 0:
                    # self.GEN.SEL_DELETE()
                    self.GEN.SEL_REVERSE()
                    if int(self.GEN.GET_SELECT_COUNT()) > 0:
                        self.GEN.SEL_COPY(coupons_not_in_gm)
                        warn_text.append({
                            "content": u'模块未在干膜线范围3mm内,详见层别%s,%s' % (coupons_in_gm, coupons_not_in_gm),
                            "type": "critical",
                            "layers": [coupons_in_gm, coupons_not_in_gm],
                        })
                        # warn_mess.append('模块未在干膜线范围4mm内，详见层别%s,%s' % (coupons_in_gm, coupons_not_in_gm))
                        persist_layer_list += [coupons_in_gm, coupons_not_in_gm]
                    else:
                        warn_text.append({
                            "content": u'模块在干膜线范围3mm内',
                            "type": "information",
                        })
            self.GEN.CLEAR_LAYER()
            # === 4.2 检测最后一次压合时，板边模块是否与电镀夹头区域相交。
            self.GEN.AFFECTED_LAYER(self.flat_layer, 'yes')
            self.GEN.FILTER_RESET()
            self.GEN.SEL_REF_FEAT(check_clamping, 'touch')
            if int(self.GEN.GET_SELECT_COUNT()) > 0:
                self.GEN.SEL_COPY(coupons_touch_clamp)
                warn_text.append({
                    "content": u'模块与电镀夹头区域相交,详见层别%s,%s' % (coupons_touch_clamp, check_clamping),
                    "type": "critical",
                    "layers": [coupons_touch_clamp, check_clamping],
                })
                # warn_mess.append('模块与电镀夹头区域相交，详见层别%s,%s' % (coupons_touch_clamp, check_clamping))
                persist_layer_list += [coupons_touch_clamp, check_clamping]
            else:
                warn_text.append({
                    "content": u'模块与电镀夹头区域不相交',
                    "type": "information",
                })
        for dlayer in list(set(delete_layers) - set(persist_layer_list)):
            self.GEN.DELETE_LAYER(dlayer)

        return warn_mess
    
    def get_v5_check_type(self, layer, laser_depth, top_or_bot, index_start):
        """检测五代靶的新检测模式"""
        layer_cu_info = self.layer_cu_info
        stackup_pp_foil_info = self.stackup_pp_foil_info
        laser_config = self.get_laser_config
        blind_list = self.get_job_laser_list()
        mrp_info = get_inplan_mrp_info(self.job_name.upper(), condtion="1=1")
        
        try:
            
            laser_depth = [i["laser_depth_mil"] for i in laser_config if i["layer_name"] == layer][0]
        except:
            pass
        # http://192.168.2.120:82/zentao/story-view-6298.html
        # 五代靶按介质厚度判断1to2或1to3只适用于任意介 其他情况都按1to2 20240108 by lyh
        # 取消任意介的判断 按新的工艺要求来判断 20240311 by lyh
        # 新工艺需求 http://192.168.2.120:82/zentao/story-view-6566.html
        # if self.parm.anylayer == "yes":
        #if "-lyh" in self.job_name:
            #self.GEN.PAUSE(str([layer, ]))
            
        index_start = int(layer.split("-")[0][1:])
        index_end = int(layer.split("-")[1])
            
        is_warning = False             
        if top_or_bot == "bot":
            
            next_n_1_layer = 'l%s' % int(index_start - abs(index_start-index_end))
            next_n_2_layer = 'l%s' % int(index_start - abs(index_start-index_end) - 1)
            next_laser_drill_layer = "s{0}-{1}".format(next_n_1_layer[1:], next_n_2_layer[1:])         
            if next_laser_drill_layer in blind_list:
                try:
                    next_depth = [i["laser_depth_mil"] for i in laser_config if i["layer_name"] == next_laser_drill_layer][0]                    
                except:
                    msg_box = msgBox()
                    msg_box.critical(self, u'错误', u'料号:%s 资料内镭射层名%s 在inplan未匹配到，请反馈MI同事检查！' % (self.job_name, next_laser_drill_layer), QMessageBox.Ok)
                    sys.exit()
                    
                layer_copper_thick = [i["CAL_CU_THK"] for i in layer_cu_info if i["LAYER_NAME"] == next_n_1_layer][0]
                if laser_depth + next_depth + layer_copper_thick > 10:
                    # warn_content = u"{1}五代靶添加：当N至 N-2层的厚度[实际厚度{0}]:总厚度>10mil时，请提出评审，工艺根据电镀铜厚判断。"
                    # msg_dict = {'type': 'critical',
                    #             'content': warn_content.format(laser_depth+next_depth + layer_copper_thick, layer, laser_depth)}
                    # # warn_text.append(warn_content.format(laser_depth+next_depth + layer_copper_thick, layer, laser_depth))
                    # warn_text.append(msg_dict)
                    is_warning = True
            else:
                layer_copper_thick = [i["CAL_CU_THK"] for i in layer_cu_info if i["LAYER_NAME"] == next_n_1_layer]
                if layer_copper_thick:                                
                    pp_thick = 0                            
                    #for dic_info in mrp_info:
                        #if dic_info["TOLAY"] is None:
                            #continue                                    

                        #if dic_info["TOLAY"].lower() == next_n_1_layer:
                    seg_index = 0
                    array_seg_index = []
                    start_seg_index = 0                    
                    for stackup_info in sorted(stackup_pp_foil_info, key=lambda x: x["STACKUP_SEG_INDEX"] * -1):
                        
                        mrp_name = stackup_info["PROC_MRP_NAME"]
                        mrp_fromlay = ""
                        mrp_tolay = ""
                        for dic_info in mrp_info:
                            if dic_info["FROMLAY"] is None:
                                continue
                            
                            if mrp_name == dic_info["MRPNAME"]:                                            
                                mrp_fromlay = dic_info["FROMLAY"].lower()
                                mrp_tolay = dic_info["TOLAY"].lower()
                                
                        if mrp_tolay == next_n_1_layer:
                            start_seg_index = stackup_info["STACKUP_SEG_INDEX"]
                            
                        # 例如DA8606GB807B1 s6-4的情况
                        if mrp_fromlay == next_n_1_layer:
                            start_seg_index = stackup_info["STACKUP_SEG_INDEX"]
                            continue
                        
                        if seg_index and next_n_2_layer in [mrp_fromlay, mrp_tolay]:
                            break
                        
                        # if stackup_info["PROC_MRP_NAME"] == dic_info["MRPNAME"]:
                        if start_seg_index:                            
                            if stackup_info["SEGMENT_TYPE_T"] == "Isolator":
                                pp_thick += stackup_info["CUST_REQ_THICKNESS_"]
                                seg_index = stackup_info["STACKUP_SEG_INDEX"]
                                array_seg_index.append(seg_index)                                
                                # break
                            if stackup_info["SEGMENT_TYPE_T"] == "Core":
                                # pp_thick = dic_info["YHTHICK"] * 39.37 # - layer_copper_thick[0] * 2
                                # break
                                pp_thick += stackup_info["CUST_REQ_THICKNESS_"]
                                seg_index = stackup_info["STACKUP_SEG_INDEX"]
                                array_seg_index.append(seg_index)
                                
                                
                        if seg_index and pp_thick == 0 and array_seg_index[0] - stackup_info["STACKUP_SEG_INDEX"] == 1:
                            # 例如D51910PBBE7A1 s9-8                                               
                            if stackup_info["SEGMENT_TYPE_T"] == "Core":
                                pp_thick = stackup_info["CUST_REQ_THICKNESS_"]
                                
                            if pp_thick:
                                break                                                    
                                
                        if seg_index and array_seg_index[0] - stackup_info["STACKUP_SEG_INDEX"] > 2:
                            break
                        
                        if seg_index and next_n_2_layer in [mrp_fromlay, mrp_tolay]:
                            break                        
                                                                            
                            # break
                    #if "-lyh" in self.job_name:
                        #self.GEN.PAUSE(str([layer, next_n_1_layer, laser_depth , pp_thick , layer_copper_thick[0]]))
                    if laser_depth + pp_thick + layer_copper_thick[0] > 10:
                        # warn_content = u"{1}五代靶添加：当N至 N-2层的厚度[实际厚度{0}]:总厚度>10mil时，请提出评审，工艺根据电镀铜厚判断。"
                        # msg_dict = {'type': 'critical',
                        #             'content': warn_content.format(laser_depth+pp_thick + layer_copper_thick[0], layer, laser_depth)}
                        # # warn_text.append(warn_content.format(laser_depth+pp_thick + layer_copper_thick[0], layer, laser_depth))
                        # warn_text.append(msg_dict)
                        is_warning = True
                          
        else: 
            next_n_1_layer = 'l%s' % int(index_start + abs(index_start-index_end))
            next_n_2_layer = 'l%s' % int(index_start + abs(index_start-index_end) + 1)
            next_laser_drill_layer = "s{0}-{1}".format(next_n_1_layer[1:], next_n_2_layer[1:])
            if next_laser_drill_layer in blind_list:
                try:
                    next_depth = [i["laser_depth_mil"] for i in laser_config if i["layer_name"] == next_laser_drill_layer][0]
                except:
                    msg_box = msgBox()
                    msg_box.critical(self, u'错误', u'料号:%s 资料内镭射层名%s 在inplan未匹配到，请反馈MI同事检查！' % (self.job_name, next_laser_drill_layer), QMessageBox.Ok)
                    sys.exit()
                    
                layer_copper_thick = [i["CAL_CU_THK"] for i in layer_cu_info if i["LAYER_NAME"] == next_n_1_layer][0]
                if laser_depth + next_depth + layer_copper_thick > 10:
                    # warn_content = u"{1}五代靶添加：当N至 N-2层的厚度[实际厚度{0}]:总厚度>10mil时，请提出评审，工艺根据电镀铜厚判断。"
                    # msg_dict = {'type': 'critical',
                    #             'content': warn_content.format(laser_depth + next_depth + layer_copper_thick, layer, laser_depth)}
                    # # warn_text.append(warn_content.format(laser_depth + next_depth + layer_copper_thick, layer, laser_depth))
                    # warn_text.append(msg_dict)
                    is_warning = True
            else:
                layer_copper_thick = [i["CAL_CU_THK"] for i in layer_cu_info if i["LAYER_NAME"] == next_n_1_layer]
                if layer_copper_thick:                                
                    pp_thick = 0                            
                    #for dic_info in mrp_info:
                        #if dic_info["FROMLAY"] is None:
                            #continue
                        
                        #if dic_info["FROMLAY"].lower() == next_n_1_layer:
                    seg_index = 0
                    array_seg_index = []
                    start_seg_index = 0                          
                    for stackup_info in sorted(stackup_pp_foil_info, key=lambda x: x["STACKUP_SEG_INDEX"]):
                        
                        mrp_name = stackup_info["PROC_MRP_NAME"]
                        mrp_fromlay = ""
                        mrp_tolay = ""
                        for dic_info in mrp_info:
                            if dic_info["FROMLAY"] is None:
                                continue
                            
                            if mrp_name == dic_info["MRPNAME"]:                                            
                                mrp_fromlay = dic_info["FROMLAY"].lower()
                                mrp_tolay = dic_info["TOLAY"].lower()
                                
                        if mrp_fromlay == next_n_1_layer:
                            start_seg_index = stackup_info["STACKUP_SEG_INDEX"]
                            
                        # 例如DA8606GB807B1 s1-3的情况
                        if mrp_tolay == next_n_1_layer:
                            start_seg_index = stackup_info["STACKUP_SEG_INDEX"]
                            continue
                        
                        if seg_index and next_n_2_layer in [mrp_fromlay, mrp_tolay]:
                            break
                        
                        # # if stackup_info["PROC_MRP_NAME"] == dic_info["MRPNAME"]:
                        if start_seg_index:                            
                            if stackup_info["SEGMENT_TYPE_T"] == "Isolator":
                                pp_thick += stackup_info["CUST_REQ_THICKNESS_"]
                                seg_index = stackup_info["STACKUP_SEG_INDEX"]
                                array_seg_index.append(seg_index)                                
                                # break
                            if stackup_info["SEGMENT_TYPE_T"] == "Core":
                                # pp_thick = dic_info["YHTHICK"] * 39.37 # - layer_copper_thick[0] * 2
                                # break
                                pp_thick += stackup_info["CUST_REQ_THICKNESS_"]
                                seg_index = stackup_info["STACKUP_SEG_INDEX"]
                                array_seg_index.append(seg_index)
                                
                        #
                        if seg_index and pp_thick == 0 and stackup_info["STACKUP_SEG_INDEX"] - array_seg_index[0] == 1:
                            # 例如D51910PBBE7A1 s2-3的情况
                            if stackup_info["SEGMENT_TYPE_T"] == "Core":
                                pp_thick = stackup_info["CUST_REQ_THICKNESS_"]
                            
                            if pp_thick:
                                break
                                
                        if seg_index and stackup_info["STACKUP_SEG_INDEX"] - array_seg_index[0] > 2:
                            break

                        if seg_index and next_n_2_layer in [mrp_fromlay, mrp_tolay]:
                            break                            
                    
                    if laser_depth +  pp_thick + layer_copper_thick[0] > 10:
                        # warn_content = u"{1}五代靶添加：当N至 N-2层的厚度[实际厚度{0}]:总厚度>10mil时，请提出评审，工艺根据电镀铜厚判断。"
                        # msg_dict = {'type': 'critical',
                        #             'content': warn_content.format(laser_depth +  pp_thick + layer_copper_thick[0], layer, laser_depth)}
                        # warn_text.append(warn_content.format(laser_depth +  pp_thick + layer_copper_thick[0], layer, laser_depth))
                        # warn_text.append(msg_dict)
                        is_warning = True                               

        #if not is_warning:                        
            #layer_mid = 'l%s' % int(index_start + 1)
            #layer_to = 'l%s' % int(index_start + 2)
        #else:
            #layer_mid = None
            #layer_to = 'l%s' % int(index_start + 1)
        if not is_warning:                        
            return "1to3"
        else:
            return "1to2"

    def add_surface_b(self, range_list=[(0, 45), (60, 70), (160, 225)], dis_y=10, pol='negative'):
        """
        短边电镀夹头区域铺负片，2022.02.03 160-220 更改为 160-225
        夹头区域改为 0-80 155-225 左右两边35 20230612 by lyh
        :param range_list:x方向距离中心线的区间距离
        :param dis_y:夹头区域大小，最小10mm最优12mm
        :return:
        """
        # 0-45 60-70 160-220

        # pnl_cent_x - 45 ~ pnl_cent_x + 45
        # pnl_cent_x + 160 ~ pnl_cent_x + 220

        # pnl_cent_x - 220 ~ pnl_cent_x + 160
        # pnl_cent_x - 70 ~ pnl_cent_x - 60

        # pnl_cent_x + 60 ~ pnl_cent_x + 70
        for cur_range in range_list:
            for cur_dis_y in [(0, dis_y), (self.pnl_y, self.pnl_y - dis_y)]:
                y1 = cur_dis_y[0]
                y2 = cur_dis_y[1]
                for cur_dis_x in [(self.pnl_cent_x + cur_range[0], self.pnl_cent_x + cur_range[1]),
                                  (self.pnl_cent_x - cur_range[0], self.pnl_cent_x - cur_range[1])]:
                    x1 = cur_dis_x[0]
                    x2 = cur_dis_x[1]
                    self.add_area_copper(x1, x2, y1, y2, pol=pol)

    def add_surface_c(self, range_list=[(0, 45), (60, 70), (160, 225)], dis_x=10, pol='negative'):
        """
        长边电镀夹头区域铺负片，2022.02.03 160-220 更改为 160-225
        夹头区域改为 0-80 155-225 左右两边35 20230612 by lyh
        :param range_list:x方向距离中心线的区间距离
        :param dis_y:夹头区域大小，最小10mm最优12mm
        :return:
        """
        # 0-45 60-70 160-220

        # pnl_cent_x - 45 ~ pnl_cent_x + 45
        # pnl_cent_x + 160 ~ pnl_cent_x + 220

        # pnl_cent_x - 220 ~ pnl_cent_x + 160
        # pnl_cent_x - 70 ~ pnl_cent_x - 60

        # pnl_cent_x + 60 ~ pnl_cent_x + 70
        for cur_range in range_list:
            for cur_dis_x in [(0, dis_x), (self.pnl_x, self.pnl_x - dis_x)]:
                x1 = cur_dis_x[0]
                x2 = cur_dis_x[1]
                for cur_dis_y in [(self.pnl_cent_y + cur_range[0], self.pnl_cent_y + cur_range[1]),
                                  (self.pnl_cent_y - cur_range[0], self.pnl_cent_y - cur_range[1])]:
                    y1 = cur_dis_y[0]
                    y2 = cur_dis_y[1]
                    self.add_area_copper(x1, x2, y1, y2, pol=pol)

    def add_area_copper(self, x1, x2, y1, y2, pol='negative'):
        self.GEN.COM('add_surf_strt,surf_type=feature')
        self.GEN.COM('add_surf_poly_strt,x=%s,y=%s' % (x1, y1))
        self.GEN.COM('add_surf_poly_seg,x=%s,y=%s' % (x1, y2))
        self.GEN.COM('add_surf_poly_seg,x=%s,y=%s' % (x2, y2))
        self.GEN.COM('add_surf_poly_seg,x=%s,y=%s' % (x2, y1))
        self.GEN.COM('add_surf_poly_seg,x=%s,y=%s' % (x1, y1))
        self.GEN.COM('add_surf_poly_end')
        self.GEN.COM('add_surf_end,attributes=no,polarity=%s' % pol)

    def clip_panel_area(self):
        """
        切板边铜
        :return:
        """
        self.GEN.OPEN_STEP(self.step_name)
        self.GEN.CHANGE_UNITS('mm')
        self.GEN.CLEAR_LAYER()
        # === 线路层和防焊层切铜 ===
        self.GEN.COM('affected_filter,filter=(type=signal|solder_mask&context=board)')

        self.GEN.COM('clip_area_strt')
        self.GEN.COM('clip_area_end,layers_mode=affected_layers,layer=,area=reference,area_type=rectangle,inout=inside,'
                     'contour_cut=no,margin=0,ref_layer=%s,feat_types=surface' % self.flat_layer)
        self.GEN.CLEAR_LAYER()

        # === 挡点层要套出货单元。（厂内单元为：1.对准度 # 2.防漏接 3.钻孔测试条 4.hct-coupon 5.尾孔 6.	防爆偏 7.线路测量coupon）
        self.get_md_clip_copper()
        self.GEN.AFFECTED_LAYER('md1', 'yes')
        self.GEN.AFFECTED_LAYER('md2', 'yes')
        self.GEN.COM('clip_area_strt')
        self.GEN.COM('clip_area_end,layers_mode=affected_layers,layer=,area=reference,area_type=rectangle,inout=inside,'
                     'contour_cut=no,margin=0,ref_layer=%s,feat_types=surface' % self.md_clip)
        self.GEN.CLEAR_LAYER()

    def get_md_clip_copper(self):

        self.GEN.CLEAR_LAYER()
        flat_layer = self.flat_layer
        # DO_INFO获取surface的index,因为可能有多块金手指对应的防焊开窗，所以要迭代处理
        info = self.GEN.INFO(
            '-t layer -e %s/%s/%s -m script -d FEATURES -o feat_index' % (self.job_name, self.step_name, flat_layer))
        # 只检测edit,set,zk等step,因为其它step经常间距不足1mm
        indexRegex = re.compile(
            r'^#\d+\s+#S P 0;.pattern_fill,.string=(dzd.*|.*floujie|drill_test_coupon|hct-coupon|sm4-coupon|1-2sm4-coupon|xllc-coupon)')
        indexRegex2 = re.compile(r'^#\d+\s+#S P 0;.pattern_fill,.string=')
        for line in info:
            if re.search(indexRegex2, line):
                if re.search(indexRegex, line):
                    # === 挡点覆盖层 ===
                    index = line.strip().split()[0].strip('#')
                    self.GEN.WORK_LAYER(flat_layer)
                    self.GEN.VOF()
                    self.GEN.COM('sel_layer_feat,operation=select,layer=%s,index=%s' % (flat_layer, index))
                    count = self.GEN.GET_SELECT_COUNT()
                    if count > 0:
                        self.GEN.SEL_COPY(self.md_cover)
                else:
                    index = line.strip().split()[0].strip('#')
                    self.GEN.WORK_LAYER(flat_layer)
                    self.GEN.VOF()
                    self.GEN.COM('sel_layer_feat,operation=select,layer=%s,index=%s' % (flat_layer, index))
                    count = self.GEN.GET_SELECT_COUNT()
                    if count > 0:
                        self.GEN.SEL_COPY(self.md_clip)

        self.GEN.CLEAR_LAYER()

    def check_panel_area(self):
        """
        检测是否切铜
        :return:
        """
        self.GEN.OPEN_STEP(self.step_name)
        self.GEN.CHANGE_UNITS('mm')

    def get_end_coupon_names(self):
        """
        获取料号钻孔层名列表
        :return:
        """
        drill_layers = self.GEN.GET_ATTR_LAYER('drill')
        print drill_layers
        return drill_layers


class Window(QtGui.QDialog):
    def __init__(self, step, warn_text,show_time,exit_num):
        QtGui.QDialog.__init__(self)
        # Dialog = QtGui.QDialog()
        self.JOB = os.environ.get('JOB')
        self.STEP = step
        self.GEN = genCOM_26.GEN_COM()
        self.GEN.COM('get_user_name')
        self.user = self.GEN.COMANS
        if os.environ.get('JOB_USER_DIR'):
            self.userPath = os.environ.get('JOB_USER_DIR')
        else:
            self.userPath = os.path.join(os.environ.get('GENESIS_DIR'), 'fw', 'jobs', self.JOB, 'user')
        self.cwd = os.path.dirname(sys.argv[0])
        self.warn_text = warn_text
        self.show_time = show_time
        self.exit_num = exit_num
        # self.save_Json_file()
        self.pushDict = {}
        self.ui = UI.Ui_Dialog()
        self.ui.setupUi(self)
        self.retran_ui()

    def retran_ui(self):
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(r"%s/logo.ico" % self.cwd), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)
        self.ui.label_job.setText(u'料号名：%s' % self.JOB)
        self.ui.label_time.setText(u'时间：%s' % self.show_time)
        self.ui.label_ver.setText(u"版本：%s" % 'V1.0.0')
        self.ui.label_usr.setText(u'用户：%s' % self.user)
        self.connect(self.ui.pushButton_close, QtCore.SIGNAL("clicked()"), self.close)

        if self.exit_num == 0:
            self.ui.pushButton_close.setText(u'退出')
        else:
            self.ui.pushButton_close.setText(u'以10004退出')

        self.ui.tableWidget.setRowCount(len(self.warn_text))
        tableRowWidth = [40, 400]
        for rr in range(len(tableRowWidth)):
            self.ui.tableWidget.setColumnWidth(rr, tableRowWidth[rr])
        for i, cur_dict in enumerate(self.warn_text):
            print i
            item = QtGui.QTableWidgetItem()
            # --样式（背景色）
            brush = QtGui.QBrush(QtGui.QColor(253, 199, 77))
            brush.setStyle(QtCore.Qt.SolidPattern)
            item.setBackground(brush)
            # --样式（前景色）
            brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
            brush.setStyle(QtCore.Qt.NoBrush)
            item.setForeground(brush)
            # --位置
            self.ui.tableWidget.setItem(i, 0, item)
            item = self.ui.tableWidget.item(i, 0)
            item.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter | QtCore.Qt.AlignCenter)
            item.setText(str(int(i) + 1))

            item = QtGui.QTableWidgetItem()
            # self.ui.tableWidget.setItem(i, 1, item)
            self.ui.tableWidget.setItem(i, 1, QtGui.QTableWidgetItem(_fromUtf8(cur_dict['content'])))

            # item.setText(str(u'%s' % cur_dict['content']))
            item = QtGui.QTableWidgetItem()
            if cur_dict['type'] == 'information':
                self.ui.tableWidget.setItem(i, 2, QtGui.QTableWidgetItem(_fromUtf8('通过')))
                self.ui.tableWidget.item(i, 2).setBackground(QtGui.QBrush(QtGui.QColor('green')))
                self.ui.tableWidget.item(i, 2).setForeground(QtGui.QBrush(QtGui.QColor('white')))
                self.ui.tableWidget.hideRow(i)
            elif cur_dict['type'] == 'critical':
                self.ui.tableWidget.setItem(i, 2, QtGui.QTableWidgetItem(_fromUtf8('警告')))
                self.ui.tableWidget.item(i, 2).setBackground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
                self.ui.tableWidget.item(i, 2).setForeground(QtGui.QBrush(QtGui.QColor('white')))

            elif cur_dict['type'] == 'warning':
                self.ui.tableWidget.setItem(i, 2, QtGui.QTableWidgetItem(_fromUtf8('检查')))
                self.ui.tableWidget.item(i, 2).setBackground(QtGui.QBrush(QtGui.QColor('yellow')))
            if 'layers' in cur_dict:
                self.pushDict[i] = QtGui.QPushButton()
                self.pushDict[i].setText(u'打开层别')
                # 添加样式集
                self.pushDict[i].setObjectName(_fromUtf8("push_%s" % i))
                self.ui.tableWidget.setCellWidget(i, 3, self.pushDict[i])
                self.pushDict[i].clicked.connect(lambda: self.buttonClicked(self.sender()))

    def closeEvent(self, event):
        print exit_num,'xxxxxxxxxxxxxxxxxxx'
        sys.exit(exit_num)

    def buttonClicked(self, inp):
        # === 暂时未找到好的方法，只能通过objectName做中转 ===
        # === 如果直接传行号，存在的问题为传递值始终为x的最终赋值
        self.GEN.COM('disp_on')

        # self.hide()
        # print inp.objectName()
        # === 截取当前的序号
        tmp = inp.objectName()
        currentindex = int(tmp[5:])
        # print currentindex
        show_layers = self.warn_text[currentindex]['layers']
        # print show_layers
        # inp.setText(u'层别打开中,请点击Continue继续')
        self.GEN.CLEAR_LAYER()
        for i, s_layer in enumerate(show_layers):
            self.GEN.WORK_LAYER(s_layer, i + 1)
        self.GEN.PAUSE('PLEASE_CHECK NUM:%s' % (currentindex + 1))

    def save_Json_file(self):
        jsonFile = 'Check_Bars_in_area.json'
        result_dict = {'warn_text':self.warn_text}
        with open(os.path.join(self.userPath, jsonFile), 'w') as f:
            f.write(json.dumps(result_dict, sort_keys=True, indent=4, separators=(', ', ': '), ensure_ascii=False))


# # # # --程序入口
if __name__ == "__main__":
    mode = 'auto_check' if len(sys.argv) > 1 else 'check'
    # 结果写入到文件中
    tmp_file = '/tmp/check_bars_in_area.log'
    appc = QtGui.QApplication(sys.argv)

    # app = MyApp('panel')
    # === 与TOPCAM结合，关联工作Steo ===
    step = os.environ.get('STEP', None)
    if not step:
        exit(1)
    warn_text = []

    app = MyApp(step)
    app.run()

    exit_num = 0
    msgInfo = u'<table border="1"><tr><th>类型</th><th>内容</th></tr>'
    for msg_dict in warn_text:

        if msg_dict['type'] == 'information':
            msgInfo += u'<tr><td bgcolor=%s><font color="#FFFFFF">%s</td><td>%s</td></tr>' % (
                'green', u'提示', msg_dict['content'])
        elif msg_dict['type'] == 'warning':
            msgInfo += u'<tr><td bgcolor=%s><font color="#FFFFFF">%s</td><td>%s</td></tr>' % (
                'orange', u'检查', msg_dict['content'])
            # exit_num = 1
        elif msg_dict['type'] == 'critical':
            msgInfo += u'<tr><td bgcolor=%s><font color="#FFFFFF">%s</td><td>%s</td></tr>' % (
                'red', u'警告', msg_dict['content'])
            exit_num = 1

    date_time = datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")
    msgInfo += u'</table><br><br>%s 以上警告信息，请注意检查！！！' % date_time

    import TOPCAM_IKM
    param_exist = os.environ.get('PARAM')
    if param_exist:
        paramJson = json.loads(param_exist.replace(';', ','))
        processID = int(paramJson['process_id'])
        jobID = int(paramJson['job_id'])
        if mode == 'check':
            IKM = TOPCAM_IKM.IKM()
            IKM.update_flow_report(processID, jobid=jobID, report=msgInfo)
    # msg_box = msgBox()
    # if exit_num == 0:
    #     msg_box.warning(None, u'检查程序运行完成，有如下提醒：', u'%s' % '\n'.join([i['content'] for i in warn_text]), QMessageBox.Ok)
    # else:
    #     msg_box.warning(None, u'检查程序运行完成，有如下提醒：', u'%s\n\n =========程序将以10004退出！' % '\n'.join([i['content'] for i in warn_text]), QMessageBox.Ok)
    if exit_num == 0:
        if mode == 'check':
            msg_box = msgBox()
            msg_box.information(None, u'检查程序运行完成：', u'无报错项目，详情查看topcam的运行记录' , QMessageBox.Ok)
    else:
        if mode == 'auto_check':
            with open(tmp_file, 'w') as writer:
                writer.write(json.dumps(warn_text))
        else:
            appb = Window(step, warn_text, date_time, exit_num)
            appb.show()
            sys.exit(appb.exec_())
    # sys.exit(exit_num)

"""
        [
  {
    "SIG4X1": 0, 
    "FROMLAY": "L2", 
    "BAR4Y1": 595.00120000000004, 
    "BAR4Y2": 597.00120000000004, 
    "MRPNAME": "I12606GI248A2-10205", 
    "PROCESS_NUM": 2, 
    "SIG4Y1": 0, 
    "SIG4Y2": 0, 
    "YHTHKPLUS": 0.080000000000000002, 
    "JOB_NAME": "I12606GI248A2", 
    "PNLROUTX": 21.219999999999999, 
    "PNLROUTY": 24.260000000000002, 
    "V5LASER": 0, 
    "BAR4X2": 451.84090000000003, 
    "BAR4X1": 451.84090000000003, 
    "YHTHKDOWN": 0.080000000000000002, 
    "PNLYINCH": 24.420000000000002, 
    "SIG4X2": 0, 
    "PNLXINCH": 21.379999999999999, 
    "TOLAY": "L5", 
    "BAR3Y": 595.00120000000004, 
    "BAR3X": 91.694200000000009, 
    "YHTHICK": 0.93000000000000005
  }, 
  {
    "SIG4X1": 482.00100000000003, 
    "FROMLAY": "L1", 
    "BAR4Y1": 595.00120000000004, 
    "BAR4Y2": 597.00120000000004, 
    "MRPNAME": "I12606GI248A2", 
    "PROCESS_NUM": 3, 
    "SIG4Y1": 595.00120000000004, 
    "SIG4Y2": 597.00120000000004, 
    "YHTHKPLUS": 0.10000000000000001, 
    "JOB_NAME": "I12606GI248A2", 
    "PNLROUTX": 21.100000000000001, 
    "PNLROUTY": 24.140000000000001, 
    "V5LASER": 0, 
    "BAR4X2": 462.0009, 
    "BAR4X1": 462.0009, 
    "YHTHKDOWN": 0.10000000000000001, 
    "PNLYINCH": 24.420000000000002, 
    "SIG4X2": 482.00100000000003, 
    "PNLXINCH": 21.379999999999999, 
    "TOLAY": "L6", 
    "BAR3Y": 595.00120000000004, 
    "BAR3X": 101.85420000000001, 
    "YHTHICK": 1.0700000000000001
  }
]
"""
# === GENCOM26包cutting data部分有修正
