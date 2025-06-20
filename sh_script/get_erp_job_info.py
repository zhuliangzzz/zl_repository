#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = "luthersy"
__date__    = "20190507"
__version__ = "Revision: 1.0.0 "
__credits__ = u"""获取erp料号信息 """

import os
import sys
import re
if sys.platform == "win32":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    scriptPath = "%s/scripts" % os.environ.get('SCRIPTS_DIR', '/incam/server/site_data')
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")
    
from oracleConnect import oracleConn

import MySQL_DB
conn = MySQL_DB.MySQL()
dbc_h = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='hdi_engineering', prod=3306,
                           username='root', passwd='k06931!')
dbc_p = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='project_status', prod=3306,
                           username='root', passwd='k06931!')

ozList = ["", '1/3OZ', 'HOZ',
          '1OZ', '1.5OZ', '2OZ',
          '2.5OZ', '3OZ', '3.5OZ',
          '4OZ', '4.5OZ', '5OZ']

ozDic = {
    '0.32': '1/3OZ', '0.33': '1/3OZ', '0.34': '1/3OZ',
    '0.49': 'HOZ', '0.50': 'HOZ', '0.51': 'HOZ',
    '0.99': '1OZ', '1.00': '1OZ', '1.01': '1OZ',
    '1.49': '1.5OZ', '1.50': '1.5OZ', '1.51': '1.5OZ',
    '1.99': '2OZ', '2.00': '2OZ', '2.01': '2OZ',
    '2.49': '2.5OZ', '2.50': '2.5OZ', '2.51': '2.5OZ',
    '2.99': '3OZ', '3.00': '3OZ', '3.01': '3OZ',
    '3.49': '3.5OZ', '3.50': '3.5OZ', '3.51': '3.5OZ',
    '3.99': '4OZ', '4.00': '4OZ', '4.01': '4OZ',
    '4.49': '4.5OZ', '4.50': '4.5OZ', '4.51': '4.5OZ',
    '4.99': '5OZ', '5.00': '5OZ', '5.01': '5OZ'
}

def get_vcut_params_info(inplan_job):
    conn=oracleConn("inmind")    
    sql=u"""select Rjob.JOB_NAME,
    CUSTOMER_THICKNESS,
    VCUT_ANGLE_ as V_CUT角度,
    VCUT_RESERVES_DEPTH_ as V_CUT保留深度,
    TRIMMING_TOP_ as 锣边TOP,
    TRIMMING_LEFT_ as 锣边LEFT,
    PRESSED_PNL_X_/1000 as 捞边后尺寸X,
    PRESSED_PNL_Y_/1000  as 捞边后尺寸Y
    from vgt_hdi.rpt_job_list Rjob
    left join (SELECT job_name,TRIMMING_TOP_,TRIMMING_LEFT_,
    PRESSED_PNL_X_,PRESSED_PNL_Y_ FROM vgt_hdi.RPT_JOB_PROCESS_LIST
    WHERE PROC_TYPE=1 and PROC_SUBTYPE=29) p on Rjob.JOB_NAME=p.JOB_NAME
    left join (SELECT distinct CUSTOMER_THICKNESS,JOB_NAME
    FROM vgt_hdi.rpt_job_stackup_cont_list) Stk on Rjob.JOB_NAME= Stk.JOB_NAME
    where Rjob.JOB_NAME='{0}'"""
    data_info=conn.executeSql(sql.format(inplan_job.split("-")[0]))
    return data_info

def dic_get_face_tech_value():
    dic_value = {0: u"unknown",
                 1 : u"无铅喷锡", 
                 2 : u"OSP", 
                 3 : u"化银", 
                 4 : u"化锡", 
                 5 : u"化金", 
                 6 : u"化金+OSP", 
                 7 : u"化金+电镀金", 
                 8 : u"GF+OSP", 
                 9 : u"GF+化金", 
                 10 : u"电镀金", 
                 11 : u"镍钯金", 
                 12 : u"GF+化银", 
                 13 : u"GF+化锡", 
                 14 : u"OSP+碳油", 
                 15 : u"GF+化金+OSP", 
                 16 : u"裸铜板", 
                 17 : u"镍钯金+OSP", 
                 18 : u"化金+碳油", 
                 19 : u"光板", 
                 20 : u"GP+镍钯金", 
                 21 : u"有铅喷锡", 
                 }    
    return dic_value

def get_face_tech_params(inplan_job):
    """获取表面处理方式"""
    conn=oracleConn("inmind")
    sql = u"""select JOB_NAME ,
    a.VALUE as 表面处理
    from vgt_hdi.rpt_job_list Rjob,
    vgt_hdi.enum_values a
    where JOB_NAME='{0}'
    AND Rjob.SURFACE_FINISH_ = a.enum
    AND a.enum_type = '1000' """
    data_info=conn.executeSql(sql.format(inplan_job.split("-")[0]))
    return data_info


def get_barcode_mianci(inplan_job):
    """获取二维码 蚀刻面次"""
    conn=oracleConn("inmind")
    sql = u"""SELECT
    i.ITEM_NAME AS JobName,
    p.value 
    FROM
    VGT_hdi.PUBLIC_ITEMS i,
    VGT_hdi.JOB_DA job,
    VGT_HDI.field_enum_translate p 
    WHERE
    i.ITEM_NAME = '{0}' 
    AND i.item_id = job.item_id 
    AND i.revision_id = job.revision_id 
    AND p.fldname = 'CI_2D_BARCODE_POSITION_SET_' 
    AND p.enum = job.CI_2D_BARCODE_POSITION_SET_ 
    AND p.intname = 'JOB'"""
    # print sql.format(inplan_job)
    data_info=conn.executeSql(sql.format(inplan_job.split("-")[0]))
    return data_info

def get_drill_information(inplan_job,return_type='array'):
    """获取钻孔表信息"""
    conn=oracleConn("inmind")
    sql = u"""SELECT
    item_for_job.item_name,
    dp_da.DRILL_LAYER_,
    CASE 
    when drill_hole_da.bit_name_ is not null THEN drill_hole_da.bit_name_ else drill_hole.name END name,
    TYPE_ENUM.value TYPE,
    drill_hole.length,
    CASE
    WHEN TYPE_ENUM.value LIKE '%N%' THEN
    'N' ELSE 'Y' 
    END PLATING_TYPE,
    round(drill_hole.ACTUAL_DRILL_SIZE*25.4,0) DRILL_SIZE,
    DRILL_TYPE_enum.value DRILL_TYPE_,
    drill_hole_da.ERP_FINISH_size_ ,
    drill_hole.PCB_COUNT,
    drill_hole.PANEL_COUNT,
    drill_hole_da.dist_size_mark_ as hole_suffix,
    ROUND(dp_da.VONDER_DRILL_DEPTH_/39.37,4) as VONDER_DRL_DEPTH_
    FROM
    VGT_HDI.all_items all_items,
    VGT_HDI.items item_for_job,
    VGT_HDI.items item_for_dp,
    VGT_HDI.DRILL_HOLE drill_hole,
    VGT_HDI.DRILL_HOLE_DA drill_hole_da,
    VGT_HDI.drill_program_da dp_da,
    VGT_HDI.field_enum_translate DRILL_TYPE_ENUM,
    VGT_HDI.field_enum_translate TYPE_ENUM 
    WHERE
    item_for_job.item_name = '{0}' 
    AND all_items.item_type = 5 
    AND all_items.root_id = item_for_job.root_id 
    AND item_for_job.item_type = 2 
    AND item_for_dp.item_type = 5 
    AND item_for_dp.root_id = item_for_job.root_id 
    AND dp_da.item_id = item_for_dp.item_id 
    AND dp_da.revision_id = all_items.revision_id 
    AND drill_hole.item_id = all_items.item_id 
    AND drill_hole.revision_id = all_items.revision_id 
    AND drill_hole_da.item_id = all_items.item_id 
    AND drill_hole_da.revision_id = all_items.revision_id 
    AND drill_hole.sequential_index = drill_hole_da.sequential_index 
    AND DRILL_TYPE_ENUM.intname = 'DRILL_HOLE' 
    AND DRILL_TYPE_ENUM.fldname = 'DRILL_TYPE_' 
    AND DRILL_TYPE_ENUM.enum = drill_hole_da.DRILL_TYPE_ 
    AND TYPE_ENUM.intname = 'DRILL_HOLE' 
    AND TYPE_ENUM.fldname = 'TYPE' 
    AND TYPE_ENUM.enum = drill_hole.TYPE"""
    if return_type == 'array':
        data_info = conn.executeSql(sql.format(inplan_job.split("-")[0]))
    else:
        data_info = conn.select_dict(sql.format(inplan_job.split("-")[0]))

    return data_info

def get_drill_information_for_BackDrillDepth(inplan_job,return_type='array'):
    """获取钻孔表信息"""
    conn=oracleConn("inmind")
    sql = u"""SELECT
    item_for_job.item_name,
    dp_da.DRILL_LAYER_,
    CASE 
    when drill_hole_da.bit_name_ is not null THEN drill_hole_da.bit_name_ else drill_hole.name END name,
    TYPE_ENUM.value TYPE,
    drill_hole.length,
    CASE
    WHEN TYPE_ENUM.value LIKE '%N%' THEN
    'N' ELSE 'Y' 
    END PLATING_TYPE,
    round(drill_hole.ACTUAL_DRILL_SIZE*25.4,0) DRILL_SIZE,
    DRILL_TYPE_enum.value DRILL_TYPE_,
    drill_hole_da.ERP_FINISH_size_ ,
    drill_hole.PCB_COUNT,
    drill_hole.PANEL_COUNT,
    drill_hole_da.dist_size_mark_ as hole_suffix,
    ROUND(dp_da.VONDER_DRILL_DEPTH_/39.37,4) as VONDER_DRL_DEPTH_,
    h.VALUE as set_hole_type_,
    drill_hole_da.is_addi_hole_
    FROM
    VGT_HDI.all_items all_items,
    VGT_HDI.items item_for_job,
    VGT_HDI.items item_for_dp,
    VGT_HDI.DRILL_HOLE drill_hole,
    VGT_HDI.DRILL_HOLE_DA drill_hole_da,
    VGT_HDI.drill_program_da dp_da,
    VGT_HDI.field_enum_translate DRILL_TYPE_ENUM,
    VGT_HDI.field_enum_translate TYPE_ENUM ,
    VGT_HDI.enum_values h
    WHERE
    item_for_job.item_name = '{0}' 
    AND all_items.item_type = 5 
    AND all_items.root_id = item_for_job.root_id 
    AND item_for_job.item_type = 2 
    AND item_for_dp.item_type = 5 
    AND item_for_dp.root_id = item_for_job.root_id 
    AND dp_da.item_id = item_for_dp.item_id 
    AND dp_da.revision_id = all_items.revision_id 
    AND drill_hole.item_id = all_items.item_id 
    AND drill_hole.revision_id = all_items.revision_id 
    AND drill_hole_da.item_id = all_items.item_id 
    AND drill_hole_da.revision_id = all_items.revision_id 
    AND drill_hole.sequential_index = drill_hole_da.sequential_index 
    AND DRILL_TYPE_ENUM.intname = 'DRILL_HOLE' 
    AND DRILL_TYPE_ENUM.fldname = 'DRILL_TYPE_' 
    AND DRILL_TYPE_ENUM.enum = drill_hole_da.DRILL_TYPE_ 
    AND TYPE_ENUM.intname = 'DRILL_HOLE' 
    AND TYPE_ENUM.fldname = 'TYPE' 
    AND TYPE_ENUM.enum = drill_hole.TYPE
    and drill_hole_da.set_hole_type_ = h.enum and h.enum_type = '1042'
    and drill_hole_da.set_hole_type_ = h.enum
    and h.enum_type = '1042'"""
    if return_type == 'array':
        data_info = conn.executeSql(sql.format(inplan_job.split("-")[0]))
    else:
        data_info = conn.select_dict(sql.format(inplan_job.split("-")[0]))

    return data_info

def get_cu_weight(inplan_job, select_dic=False):
    """获取铜厚及线宽线距信息"""
    conn=oracleConn("inmind")
    sql = u"""SELECT
    a.item_name job_name,
    LOWER(c.item_name) layer_name,
    d.layer_position,
    d.layer_index,
    d.LAYER_ORIENTATION,
    round( d.required_cu_weight / 28.3495, 2 ) AS CU_WEIGHT,
    round(e.finish_cu_thk_,3)  客户要求完成铜mil,
    round(e.cal_cu_thk_,3)  厂内管控计算铜mil,
    round(e.LW_ORG_,2) 原稿线宽,
    round(e.LS_ORG_,2) 原稿线距,
    round(e.LW_FINISH_,2) 成品线宽,
    round(e.ls_finish_,2) 成品线距 
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
    AND a.item_name = '{0}' 
    ORDER BY
    d.layer_index"""
    if select_dic:
        data_info = conn.select_dict(sql.format(inplan_job.split("-")[0]))
    else:             
        data_info=conn.executeSql(sql.format(inplan_job.split("-")[0]))
        
    return data_info    
    
    
def get_inplan_all_flow(inplan_job, select_dic=False):
    """
    从inplan获取当前料号的所有流程
    :return:
    """
    conn=oracleConn("inmind")
    sql = u"""
    SELECT 
    RJTSL.JOB_NAME,
    RJTSL.DESCRIPTION process_description,
    RJTSL.ORDER_NUM,
    RJTSL.TRAVELER_ORDERING_INDEX,
    RJTSL.work_center_code,
    ats.description work_description,
    ats.value_as_string,
    nts.note_string,
    RJTSL.SITE_NAME,
    RJTSL.operation_code,
    proc.mrp_name
    FROM VGT_HDI.RPT_JOB_TRAV_SECT_LIST RJTSL
    left JOIN VGT_HDI.process proc
    on RJTSL.proc_item_id = proc.item_id 
    and RJTSL.proc_revision_id = proc.revision_id 
    left JOIN VGT_HDI.note_trav_sect nts
    ON RJTSL.item_id = nts.item_id
    and RJTSL.revision_id = nts.revision_id
    and RJTSL.sequential_index = nts.section_sequential_index
    left JOIN VGT_HDI.attr_trav_sect ats
    ON RJTSL.item_id = ats.item_id
    and RJTSL.revision_id = ats.revision_id
    and RJTSL.sequential_index = ats.section_sequential_index
    WHERE RJTSL.JOB_NAME = UPPER('{0}')
    ORDER BY RJTSL.ORDER_NUM, RJTSL.TRAVELER_ORDERING_INDEX
    """
    # print sql.format(inplan_job.split("-")[0])
    if select_dic:
        data_info = conn.select_dict(sql.format(inplan_job.split("-")[0]), is_arraysize=False)
    else:        
        data_info = conn.executeSql(sql.format(inplan_job.split("-")[0]), is_arraysize=False)
        
    return data_info

def get_process_is_plug(inplan_job):
    """判断是否有树脂塞孔 Q20706GIN31A1"""
    conn=oracleConn("inmind")
    sql = u"""select job_name,
    MRP_NAME,
    PROC_SUBTYPE,
    RESIN_PLUG_TYPE_   --2表示有树脂塞孔，但不能表有几次塞
    from vgt_hdi.RPT_JOB_PROCESS_LIST
    where PROC_TYPE=1
    and job_name ='{0}'"""
    data_info = conn.select_dict(sql.format(inplan_job.split("-")[0]))
    return data_info

def getBackDrillDepth(inplan_job):
    """
    获取inplan中的背钻深度，20200423更改获取的栏位为ERP的备注项目
    :param M:
    :param dbc:
    :param strJOB:
    :return:
    """
    conn=oracleConn("inmind")
    sql = u"""
    select a.item_name job_name_,
    c.item_name layer_name_,
    e.DRILL_GROUP_,
    e.DRILL_LAYER_,
    decode(d.drill_technology,1,'Controll Depth',5,'Countersink',6,'Counterbore',7,'Backdrill') as drill_type,
    f.name tnum,
    ROUND(f.finished_size/39.37,4) as finished_size,
    ROUND(f.actual_drill_size/39.37,4) as actual_drill_size,
    decode(f.type,4,'Plated Slot',0,'PTH',1,'Via',2,'NPTH',3,'Micro Via',5,'Non-Plated Slot') as hole_type,
    ROUND(g.BACK_DRILL_FOR_THROUGH_HOLE_/39.37,4) as BKDRL_THROUGH_HOLE_,
    g.DRILL_TOL_,
    ROUND(e.VONDER_DRILL_DEPTH_/39.37,4) as VONDER_DRL_DEPTH_,
    d.start_index,
    e.non_drill_layer_,
    d.end_index,
    ROUND(e.cus_drill_depth_/39.37,4) as cus_drill_depth_,
    ROUND(e.stub_drill_depth_/39.37,4) as stub_drill_depth_,
    f.pcb_count,
    g.hole_qty_,
    g.drill_notes_,
    g.erp_finish_size_,
    g.BIT_NAME_
    from vgt_hdi.items a
    inner join vgt_hdi.job b
    on a.item_id = b.item_id
    and  a.last_checked_in_rev = b.revision_id
    inner join vgt_hdi.items c
    on a.root_id = c.root_id
    inner join vgt_hdi.drill_program d
    on c.item_id = d.item_id 
    and c.last_checked_in_rev = d.revision_id
    inner join vgt_hdi.drill_program_da e
    on d.item_id = e.item_id 
    and d.revision_id = e.revision_id
    inner join vgt_hdi.drill_hole f
    on d.item_id = f.item_id 
    and d.revision_id = f.revision_id
    inner join vgt_hdi.drill_hole_da g
    on f.item_id = g.item_id 
    and f.revision_id = g.revision_id
    and f.sequential_index=g.sequential_index
    where  d.drill_technology in (1,5,6,7) and a.item_name =  '{0}'
    order by e.DRILL_LAYER_,f.name"""
    data_info = conn.select_dict(sql.format(inplan_job.split("-")[0]))
    return data_info

def getJobData(inplan_job):
    """
    获取inplan中各种参数
    # 0料号名 1客户名 2客户品名 3工厂 4订单类型	5出货方式 6出货尺寸宽
    # 7出货尺寸长	8成品板厚	9表面处理	10阻焊次数	11阻焊面别
    # 12阻焊颜色	13字符次数	14字符面别	15字符颜色	16是否有雷雕
    # 17.PCS_X	18.PSC_Y	19.SET_X	20.SET_Y
    # 21.PNL中的SET数	22.SET中的PCS数	23.周期面别	24.周期格式	25.大板VCUT	26.UL面别 27.UL标记
    :param M:
    :param dbc:
    :param strJOB:
    :return:
    """
    conn=oracleConn("inmind")
    sql = u"""select a.item_name 料号名,
    d.customer_name 客户名,
    c.customer_job_name_ 客户品名,
    h.value 工厂,
    i.value 订单类型,
    j.value 出货方式,
    round(c.delivery_width_ / 39.37, 3) 出货尺寸宽,
    round(c.delivery_length_ / 39.37, 3) 出货尺寸长,
    round(f.customer_thickness / 39.37,3) 成品板厚,
    k.value  表面处理,
    l.value 阻焊次数,
    m.value 阻焊面别,
    (select enu.value
    from vgt_hdi.items sm   
    inner join vgt_hdi.mask_layer sm2
    on sm.item_id = sm2.item_id
    and sm.last_checked_in_rev = sm2.revision_id
    inner join vgt_hdi.mask_layer_da sm3
    on sm2.item_id = sm3.item_id
    and sm2.revision_id = sm3.revision_id
    inner join vgt_hdi.enum_values enu
    on sm3.sm_color_ = enu.enum
    where sm.root_id = a.root_id
    and sm2.mask_type = 0
    and enu.enum_type = 214
    and enu.value is not null
    and rownum = 1) 阻焊颜色,
    n.value 字符次数,
    o.value 字符面别,
    (select enu.value
    from vgt_hdi.items ss   
    inner join vgt_hdi.mask_layer ss2
    on ss.item_id = ss2.item_id
    and ss.last_checked_in_rev = ss2.revision_id
    inner join vgt_hdi.mask_layer_da ss3
    on ss2.item_id = ss3.item_id
    and ss2.revision_id = ss3.revision_id
    inner join vgt_hdi.enum_values enu
    on ss3.ss_color_ = enu.enum
    where ss.root_id = a.root_id
    and ss2.mask_type = 2
    and enu.enum_type = 1025
    and enu.value is not null
    and rownum = 1) 字符颜色,
    decode(c.has_qr_code_,0,'无',1,'有') 是否有雷雕,
    round(g.pcb_size_x/39.37,3) PCS_X,
    round(g.pcb_size_y/39.37,3) PSC_Y,
    round(c.set_size_x_/39.37,3) SET_X,
    round(c.set_size_y_/39.37,3) SET_Y,
    b.num_arrays PNL中的Set数,
    c.pcs_per_set_ SET中的Pcs数,
    p.value 周期面别,
    q.value 周期格式,
    r.value 大板Vcut,
    s.value UL面别,
    t.value UL标记,
    c.es_elic_ 是否ELIC,
    decode(c.sm_plug_type_,0,'no',1,'no',2,'yes',3,'yes')  是否阻焊塞,
    (select decode(proda.resin_plug_type_,0,'no',1,'no',2,'yes')
    from vgt_hdi.public_items pb
    inner join vgt_hdi.process pro
    on pb.item_id = pro.item_id
    and pb.revision_id = pro.revision_id
    inner join vgt_hdi.process_da proda
    on pro.item_id = proda.item_id
    and pro.revision_id = proda.revision_id
    where pb.root_id = a.root_id
    and pro.proc_subtype = 29)  是否树脂塞
    from vgt_hdi.items a
    inner join vgt_hdi.job b
    on a.item_id = b.item_id
    and a.last_checked_in_rev = b.revision_id
    inner join vgt_hdi.job_da c
    on b.item_id = c.item_id
    and b.revision_id = c.revision_id
    inner join vgt_hdi.customer d
    on b.customer_id = d.cust_id
    inner join vgt_hdi.items e
    on a.root_id = e.root_id
    inner join vgt_hdi.stackup f
    on e.item_id = f.item_id
    and e.last_checked_in_rev = f.revision_id
    inner join vgt_hdi.part g
    on b.item_id = g.item_id
    and b.revision_id = g.revision_id
    inner join vgt_hdi.enum_values h
    on c.site_ = h.enum
    inner join vgt_hdi.enum_values i
    on c.order_type_ = i.enum
    inner join vgt_hdi.enum_values j
    on c.delivery_unit_ = j.enum
    inner join vgt_hdi.enum_values k
    on c.surface_finish_ = k.enum
    inner join vgt_hdi.enum_values l
    on c.sm_print_times_ = l.enum
    inner join vgt_hdi.enum_values m
    on c.sm_side_ = m.enum 
    inner join vgt_hdi.enum_values n
    on c.ss_print_times_ = n.enum
    inner join vgt_hdi.enum_values o
    on c.ss_side_ = o.enum 
    inner join vgt_hdi.enum_values p
    on c.dc_side_ = p.enum
    inner join vgt_hdi.enum_values q
    on c.dc_type_ = q.enum
    inner join vgt_hdi.enum_values r
    on c.rout_process_ = r.enum 
    inner join vgt_hdi.enum_values s
    on c.ul_side_ = s.enum
    inner join vgt_hdi.enum_values t
    on c.ul_mark_ = t.enum                     
    where a.item_name = '{0}'
    and h.enum_type = 1057
    and i.enum_type = 1007
    and j.enum_type = 1029
    and k.enum_type = 1000
    and l.enum_type = 1114
    and m.enum_type = 1015
    and n.enum_type = 1113
    and o.enum_type = 1038
    and p.enum_type = 1022
    and q.enum_type = 1001
    and r.enum_type = 1045
    and s.enum_type = 1020
    and t.enum_type = 1019"""
    data_info = conn.executeSql(sql.format(inplan_job.split("-")[0]), is_arraysize=False)
    dic_info = {}
    if data_info:        
        recs = data_info[0]
        dic_info ={'job_name':recs[0],
                   'cust_name': recs[1],
                   'cust_pn': recs[2],
                   'factory': recs[3],
                   'job_type': recs[4],
                   'out_type': recs[5],
                   'out_witdth': recs[6],
                   'out_length': recs[7],
                   'out_thick': recs[8],
                   'out_coat': recs[9],
                   'sm_time': recs[10],
                   'sm_side': recs[11],
                   'sm_color': recs[12],
                   'cs_time': recs[13],
                   'cs_side': recs[14],
                   'cs_color': recs[15],
                   'laser_carve': recs[16],
                   'pcsX': recs[17],
                   'pcsY': recs[18],
                   'setX': recs[19],
                   'setY': recs[20],
                   'setInPnl': recs[21],
                   'pcsinSet': recs[22],
                   'dc_side': recs[23],
                   'dc_format': recs[24],
                   'vcutmode': recs[25],
                   'ulSide': recs[26],
                   'ulMark': recs[27],
                   'ELIC': recs[28],
                   'SM_PLUG': recs[29],
                   'RESIN_PLUG': recs[30]}
        
    return dic_info

def get_is_ks_rout_process(inplan_job):
    """检测是否有控深铣流程"""
    conn=oracleConn("inmind")
    sql = """select JOB_NAME,PROCESS_NAME,WORK_CENTER_CODE,
    OPERATION_CODE,DESCRIPTION
    from vgt_hdi.rpt_job_trav_sect_list
    where OPERATION_CODE in ('HDI15701','HDI22501')    
    and JOB_NAME = '{0}'"""
    data_info = conn.select_dict(sql.format(inplan_job.split("-")[0]))
    return data_info

def get_mrp_name(inplan_job):
    """获取mrp_name"""
    conn=oracleConn("inmind")
    sql = """SELECT
    a.MRP_NAME MRP_NAME
    FROM
    vgt_hdi.RPT_JOB_PROCESS_LIST a
    WHERE a.job_name = '{0}'"""
    data_info = conn.select_dict(sql.format(inplan_job.split("-")[0]))
    return data_info

def get_inplan_imp(inplan_job):
    """
    从inplan获取阻抗信息，2021.11.16变更开窗阻抗部分
    :param dbc:
    :param strJOB:
    :return:
    """
    conn=oracleConn("inmind")
    sql = u"""
    select a.item_name cur_job, 
    d.imp_group_ igroup,
    decode(d.model_type_,0,'特性',1,'差动',2,'特性共面',3,'差动共面') imodel,
    c.original_trace_width org_width,
    c.design_trace_trace_spacing org_spc,
    c.design_trace_ground_spacing org_cu_spc,
    d.trace_layer_,
    d.ref_layer_,
    d.finish_lw_,
    d.finish_ls_,
    d.spacing_2_copper_ spc2cu,
    d.eq_ls_,
    d.eq_lw_,
    d.eq_spacing_2_copper_,
    c.customer_required_impedance cusimp,
    round(c.artwork_trace_width,2) work_width,
    case
    when c.model_name like '%%uncoated%%' and  (substr(d.trace_layer_,2,2) = '1')
    then '是'
    when c.model_name like '%%uncoated%%' and substr(d.trace_layer_,2,2) = ltrim(substr(a.item_name,5,2),'0')
    then '是'
    else '否'
    end  solderopen,
    decode(c.constraint_is_up_to_date,0,'否',1,'是') imp_update,
    c.stackup_ordering_index Ord_index 
     from vgt_hdi.items a
    inner join vgt_hdi.public_items b
     on a.root_id = b.root_id
    inner join vgt_hdi.impedance_constraint c
     on b.item_id = c.item_id
    and b.REVISION_ID = c.revision_id
    inner join vgt_hdi.impedance_constraint_da d
     on c.item_id = d.item_id
    and c.revision_id = d.revision_id
    and c.sequential_index = d.sequential_index
    where a.ITEM_NAME = '{0}'"""
    data_info = conn.select_dict(sql.format(inplan_job.split("-")[0]))
    return data_info
    # 料号名 ，分组，阻抗类型，原始线宽，原始间距，原始铜距，阻抗层，参考层，出货线宽，出货线距，出货铜距，客户需求阻值，是否开窗阻抗
    
def get_inplan_mrp_info(inplan_job, condtion="d.proc_subtype IN ( 28, 29 ) "):
    conn=oracleConn("inmind")
    sql = u"""SELECT
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
    a.item_name = UPPER('{0}')
    AND d.proc_type = 1 
    AND {1}
    ORDER BY e.process_num_
    """
    # print(sql.format(inplan_job.split("-")[0], condtion))
    data_info = conn.select_dict(sql.format(inplan_job.split("-")[0], condtion))
    return data_info

def get_inplan_mrp_info_new(inplan_job, condtion="d.proc_subtype IN ( 28, 29 ) "):
    conn=oracleConn("inmind")
    sql = u"""SELECT
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
    round( e.OUTER_TARGET_X2_ / 39.37, 4 ) sig4x2,
    round( e.left_border_size_ / 39.37, 4 ) left_b,
    round( e.top_border_size_ / 39.37, 4 ) top_b
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
    a.item_name = UPPER('{0}')
    AND d.proc_type = 1 
    AND {1}
    ORDER BY e.process_num_
    """
    data_info = conn.select_dict(sql.format(inplan_job.split("-")[0], condtion), is_arraysize=False)
    return data_info

def get_plating_type(inplan_job):
    """获取一次铜 二次铜"""
    conn=oracleConn("inmind")
    sql = u"""select a.item_name jobname,
    c.item_name process_name,
    e.film_bg_ layer_name,
    d.MRP_NAME mrp_name,
    e.PRESS_PROGRAM_,
    e.process_num_ ,
    e.FILM_PF_,
    e.df_width_ / 1000 ganmo_size,
    e.Plating_Type_
    -- 1代表一次铜，2代表二次铜
    from vgt_hdi.items a
    inner join vgt_hdi.job b
    on a.item_id = b.item_id
    and a.last_checked_in_rev = b.revision_id
    inner join vgt_hdi.items c
    on a.root_id = c.root_id
    inner join vgt_hdi.process d
    on c.item_id = d.item_id
    and c.last_checked_in_rev = d.revision_id
    inner join vgt_hdi.process_da e
    on d.item_id = e.item_id
    and d.revision_id = e.revision_id
    where d.proc_type=1 and a.item_name = upper('{0}')
    order by e.process_num_ desc"""
    data_info = conn.select_dict(sql.format(inplan_job.split("-")[0]))
    return data_info

def get_outer_target_condition(inplan_job):
    """获取是否有外四靶条件"""
    conn=oracleConn("inmind")
    sql = u"""select p.job_name JOB_NAME,
    p.MRP_NAME MRP_NAME,
    p.PROC_SUBTYPE PROC_SUBTYPE,
    P.PROCESS_LEVEL_ PROCESS_LEVEL,
    LASER_BURN_TARGET_ LASER_BURN_TARGET,
    d.Drill_name DRL_NAME, 
    L.Drill_name LASER_NAME
    from vgt_hdi.RPT_JOB_PROCESS_LIST p
    left join (Select JOB_NAME,PARENT_PROCESS_, listagg (program_name, ',')
    WITHIN GROUP (ORDER BY DRL_PROCESS_NUM_) Drill_name
    from vgt_hdi.RPT_DRILL_PROGRAM_LIST where drill_technology IN (0,1, 5, 6, 7)
    GROUP BY JOB_NAME,PARENT_PROCESS_) d on d.job_name=p.job_name
    and d.PARENT_PROCESS_ =p.MRP_NAME
    left join (Select JOB_NAME,PARENT_PROCESS_, listagg (program_name, ',')
    WITHIN GROUP (ORDER BY DRL_PROCESS_NUM_) Drill_name
    from vgt_hdi.RPT_DRILL_PROGRAM_LIST
    where drill_technology IN (2)   GROUP BY JOB_NAME,PARENT_PROCESS_ ) L on L.job_name=p.job_name
    and L.PARENT_PROCESS_ =p.MRP_NAME
    where p.PROC_TYPE=1
    and p.job_name ='{0}'
    """
    data_info = conn.select_dict(sql.format(inplan_job.split("-")[0]))
    return data_info    
    
def get_laser_fg_type(inplan_job):
    """获取镭射是否有分割"""
    conn=oracleConn("inmind")
    sql = u"""select JOB_NAME,PNL_PARCELLATION_METHOD_   -- 0表用户没选择，1表无需分割，2、3、4有分割
    from vgt_hdi.RPT_JOB_LIST 
    where job_name ='{0}'
    """
    data_info = conn.select_dict(sql.format(inplan_job.split("-")[0]))
    return data_info

def get_target_distance_info(inplan_job):
    """TC_AAC27	靶孔间距X
    TC_AAC28	靶孔间距Y
    TC_AAC29	备用靶孔
    TC_AAC231	靶孔间距X1
    TC_AAC232	靶孔间距Y1
    TC_AAC233	靶孔间距X2
    TC_AAC234	靶孔间距Y2
    TC_AAC235	八靶外四靶靶孔间距(X1)
    TC_AAC236	八靶外四靶靶孔间距(Y1)
    TC_AAC237	八靶外四靶靶孔间距(X2)
    TC_AAC238 	八靶外四靶靶孔间距(Y2)"""
    conn=oracleConn("topprod")
    sql = u"""select TC_AAC27 L_X,
    TC_AAC28 L_Y,
    TC_AAC231 X1,
    TC_AAC232 Y1,
    TC_AAC233 X2,
    TC_AAC234 Y2,
    TC_AAC235 W_X1,
    TC_AAC236 W_Y1,
    TC_AAC237 W_X2,
    TC_AAC238 W_Y2
    from tc_aac_file
    where tc_aac01 ='{0}'
    """
    data_info = conn.select_dict(sql.format(inplan_job))
    return data_info

def get_zk_tolerance(inplan_job):
    conn=oracleConn("topprod")
    sql = u"""SELECT DISTINCT TC_AAM04 层名,TC_AAM05 参考层,TC_AAM09 阻值,TC_AAM41 as 阻抗线公差正,
    TC_AAM42 as 阻抗线公差负
    FROM TC_AAM_FILE
    WHERE TC_AAM01='{0}A'"""
    data_info = conn.select_dict(sql.format(inplan_job.split("-")[0].upper()))
    return data_info

def get_min_line_tolerance(inplan_job):
    conn=oracleConn("topprod")
    sql = u"""SELECT TC_AAC548 as 一般线公差正,TC_AAC549 as 一般线公差负
    ,TC_AAC554 as BGA公差正,TC_AAC555 as BGA公差负
    ,TC_AAC551 as SMD公差正,TC_AAC552 as SMD公差负
    FROM TC_AAC_FILE
    WHERE TC_AAC01='{0}'"""
    data_info = conn.select_dict(sql.format(inplan_job.split("-")[0].upper()))
    return data_info    

def get_led_board(inplan_job):
    """
    判断是否为LED板
    :return:
    """
    conn=oracleConn("inmind")
    sql = """
    SELECT
            i.ITEM_NAME AS JobName,
            job.es_led_board_,
            JOB.JOB_PRODUCT_LEVEL3_
    FROM
            VGT_hdi.PUBLIC_ITEMS i,
            VGT_hdi.JOB_DA job
    WHERE
            i.ITEM_NAME = '{0}'
            AND i.item_id = job.item_id
            AND i.revision_id = job.revision_id"""
    process_data = conn.select_dict(sql.format(inplan_job.upper().split("-")[0]))
    if len(process_data) > 0:
        if process_data[0]['ES_LED_BOARD_'] == 1 :                 
            return True
        elif "LED" in str(process_data[0]['JOB_PRODUCT_LEVEL3_']).upper():
            if process_data[0]['JOB_PRODUCT_LEVEL3_'].decode("utf8") not in (u'LED照明(如应急、工业、矿山等）',u'LED-连接板'):
                return True
            return False
        else:
            return False
    else:
        return False
    
def get_job_type(inplan_job):
    """
    判断是否为LED板 汽车板等情况
    :return:
    """
    conn=oracleConn("inmind")
    sql = """
    SELECT
            i.ITEM_NAME AS JobName,
            job.es_led_board_,
            JOB.JOB_PRODUCT_LEVEL3_,
            JOB.JOB_PRODUCT_LEVEL1_, 
            JOB.ES_CAR_BOARD_ ,
            JOB.ES_BATTERY_BOARD_
    FROM
            VGT_hdi.PUBLIC_ITEMS i,
            VGT_hdi.JOB_DA job
    WHERE
            i.ITEM_NAME = '{0}'
            AND i.item_id = job.item_id
            AND i.revision_id = job.revision_id"""
    data_info = conn.select_dict(sql.format(inplan_job.upper().split("-")[0]))
    return data_info
    
def get_ks_bd_target_info(inplan_job):
    """获取控深及背钻的靶距信息"""
    conn=oracleConn("inmind")
    sql = u"""SELECT
    a.job_name,
    a.MRP_NAME,
    b.program_name as ODB_DRILL_NAME,
    b.DRILL_LAYER_,
    decode( b.drill_technology, 0, 'Mechanical', 1, 'Controll Depth',
    5, 'Countersink', 6, 'Counterbore', 7, 'Backdrill' ) AS drill_type,
    round( a.PROCESS_LEVEL_ - 1 ) AS PROCESS_LEVEL,
    b.start_index AS start_index,
    b.end_index AS end_index,
    round( b.TARGET_X1_ / 39.37, 4 ) AS TARGET_X1,
    round( b.TARGET_Y1_ / 39.37, 4 ) AS TARGET_Y1,
    round( b.TARGET_X2_ / 39.37, 4 ) AS TARGET_X2,
    round( b.TARGET_Y2_ / 39.37, 4 ) AS TARGET_Y2 
    FROM
    vgt_hdi.RPT_JOB_PROCESS_LIST a,
    vgt_hdi.RPT_DRILL_PROGRAM_LIST b 
    WHERE
    a.root_id = b.root_id 
    AND a.MRP_NAME = b.PARENT_PROCESS_ 
    AND b.drill_technology IN ( 1, 5, 6, 7 ) 
    AND a.job_name = '{0}'"""
    data_info = conn.select_dict(sql.format(inplan_job.split("-")[0]))
    return data_info

def get_ks_bd_target_info_detail(inplan_job):
    """获取控深及背钻的关联机械孔信息"""
    conn=oracleConn("inmind")
    sql = u"""select a.job_name,
    a.MRP_NAME,
    b.program_name as ODB_DRILL_NAME,
    b.DRILL_LAYER_,
    decode( b.drill_technology, 0, 'Mechanical', 1, 'Controll Depth',
    5, 'Countersink', 6, 'Counterbore', 7, 'Backdrill' ) AS drill_type,
    round( a.PROCESS_LEVEL_ - 1 ) AS PROCESS_LEVEL,
    b.start_index AS start_index,
    b.end_index AS end_index,       
    C.NAME,
    round(c.finished_size*0.0254,3) as 成品孔径,
    c.pcb_count,
    c.type_t,
    c.IS_ADDI_HOLE_ as 是否附加孔
    from vgt_hdi.RPT_JOB_PROCESS_LIST A,
    VGT_HDI.RPT_DRILL_PROGRAM_LIST   b,
    VGT_HDI.Rpt_Drill_Hole_Info   c
    where a.root_id = b.root_id
    and a.MRP_NAME=b.PARENT_PROCESS_
    and b.ITEM_ID=c.ITEM_ID
    and b.REVISION_ID=c.REVISION_ID
    and b.drill_technology in (0,1,5,6,7)
    and a.job_name ='{0}'"""
    data_info = conn.select_dict(sql.format(inplan_job.split("-")[0]))
    return data_info

def get_mysql_target_info(inplan_job, database="hdi_engineering.incam_process_info"):
    """
    获取压合信息
    从mysql数据库获取 压合靶距信息 20230511 by lyh
    :return:
    """
    dbc_h = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='hdi_engineering', prod=3306,
                               username='root', passwd='k06931!')    
    sql = """select JOB_NAME,MRPNAME,PROCESS_NUM,
    PNLXINCH,PNLYINCH,PNLROUTX,PNLROUTY,
    BAR4X1,BAR4Y1,BAR4X2,BAR4Y2,BAR3X,
    BAR3Y,FROMLAY,TOLAY,YHTHICK,YHTHKPLUS,
    YHTHKDOWN,V5LASER,SIG4Y1,SIG4Y2,SIG4X1,SIG4X2,COORDINATE_JSON
    from {1} where job_name = '{0}'"""
    # print"-------->", sql.format(inplan_job.split("-")[0], database)
    data_info = conn.SELECT_DIC(dbc_h, sql.format(inplan_job.split("-")[0], database))
    # print "---->", [data_info]
    return data_info

def get_mysql_all_target_info(inplan_job, database="hdi_engineering.incam_process_info"):
    """
    获取压合信息
    从mysql数据库获取 压合靶距信息 20230511 by lyh
    :return:
    """
    dbc_h = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='hdi_engineering', prod=3306,
                               username='root', passwd='k06931!')      
    sql = """select * from {1} where job_name = '{0}'"""
    # print"-------->", sql.format(inplan_job.split("-")[0], database)
    data_info = conn.SELECT_DIC(dbc_h, sql.format(inplan_job.split("-")[0], database))

    return data_info

def get_mysql_ks_bd_target_info(inplan_job, database="hdi_engineering.incam_drillprogram_info"):
    """
    获取背钻及控深靶孔信息
    从mysql数据库获取 压合靶距信息 20230511 by lyh
    :return:
    """
    dbc_h = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='hdi_engineering', prod=3306,
                               username='root', passwd='k06931!')      
    sql = """select JOB_NAME,
    MRP_NAME,
    ODB_DRILL_NAME,
    DRILL_LAYER_,
    DRILL_TYPE,
    PROCESS_LEVEL,
    START_INDEX,
    END_INDEX,
    TARGET_X1,
    TARGET_Y1,
    TARGET_X2,
    TARGET_Y2,
    ID
    from {1} where job_name = '{0}'"""
    data_info = conn.SELECT_DIC(dbc_h, sql.format(inplan_job.split("-")[0], database))

    return data_info

def get_mysql_ks_bd_all_target_info(inplan_job, database="hdi_engineering.incam_drillprogram_info"):
    """
    获取背钻及控深靶孔信息
    从mysql数据库获取 压合靶距信息 20230511 by lyh
    :return:
    """
    dbc_h = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='hdi_engineering', prod=3306,
                               username='root', passwd='k06931!')      
    sql = """select * 
    from {1} where job_name = '{0}'"""
    data_info = conn.SELECT_DIC(dbc_h, sql.format(inplan_job.split("-")[0], database))

    return data_info

def get_expose_area_from_erp(inplan_job):
    """从erp内获取金面积"""
    conn=oracleConn("topprod")
    sql = u"""select tc_aac01 JOBNAME,TC_AAC123 TOP_AREA,TC_AAC125 BOT_AREA from tc_aac_file where tc_aac01 = UPPER('{0}')
    """
    data_info = conn.select_dict(sql.format(inplan_job.split("-")[0]))
    return data_info

def get_StackupData(inplan_job):
    """获取叠构干膜尺寸等信息"""
    conn=oracleConn("inmind")
    sql = u""" SELECT
    a.item_name AS JOB_NAME,
    c.item_name AS PRESS_NAME,
    e.film_bg_,
    e.process_num_,
    d.MRP_NAME,
    e.PRESS_PROGRAM_,
    e.FILM_PF_,
    e.Plating_Type_,
    -- 1代表一次铜，2代表二次铜 0代表NONE
    e.df_width_ / 1000 AS DF_WIDTH,
    -- 树脂塞孔 0,'Unknown',1,'不塞孔',2,'树脂塞孔'
    e.resin_plug_type_ 
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
    d.proc_type = 1 
    AND a.item_name = '{0}' 
    AND	c.item_name NOT LIKE '%%光板%%'
    ORDER BY
    e.process_num_ DESC"""
    data_info = conn.select_dict(sql.format(inplan_job.split("-")[0]))
    return data_info

def getPanelSRTable(inplan_job):
    conn=oracleConn("inmind")
    sql=u'''select a.item_name JOB_NAME,
    e.item_name PANEL_STEP,
    case when d.coupon_sequential_index >0
    then (select coup.name from vgt_hdi.coupon coup
    where coup.item_id = b.item_id
    and coup.revision_id = b.revision_id
    and d.coupon_sequential_index = coup.sequential_index)
    Else (select decode(count(*), 1, 'PCS', 2, 'SET', 3, 'SET', 4, 'SET')
    from vgt_hdi.panel pnl, vgt_hdi.public_items im2
    where im2.root_id = a.root_id
    and pnl.item_id = im2.item_id
    and pnl.revision_id = im2.revision_id)
    end OP_STEP,
    case when d.coupon_sequential_index >0
    then (select round(coup.size_y/1000,1)||'' from vgt_hdi.coupon coup
    where coup.item_id = b.item_id
    and coup.revision_id = b.revision_id
    and d.coupon_sequential_index = coup.sequential_index)
    Else 'No'
    end COUPON_HEIGHT,
    case when d.coupon_sequential_index >0
    then (select round(coup.size_x/1000,1)||'' from vgt_hdi.coupon coup
    where coup.item_id = b.item_id
    and coup.revision_id = b.revision_id
    and d.coupon_sequential_index = coup.sequential_index)
    Else 'No'
    end COUPON_LENGTH,
    round(d.start_x / 1000,10) start_x,--单位inch
    round(d.start_y / 1000,10) start_y,--单位inch
    d.number_x X_NUM,
    d.number_y Y_NUM,
    round(d.delta_x / 1000,10) delta_x,--单位inch
    round(d.delta_y / 1000,10) delta_y,--单位inch
    d.rotation_angle,--旋转角度
    d.flip--是否镜像
    from vgt_hdi.public_items  a,
    vgt_hdi.job           b,
    vgt_hdi.public_items  e,
    vgt_hdi.panel         c,
    vgt_hdi.layout_repeat d
    where a.item_id = b.item_id
    and a.revision_id = b.revision_id
    and a.root_id = e.root_id
    and e.item_id = c.item_id
    and e.revision_id = c.revision_id
    and c.item_id = d.item_id
    and c.revision_id = d.revision_id
    -- and e.item_name = 'Panel' --默认只筛选Panel
    and e.item_name like 'Panel%%' --默认只筛选Panel
    and a.item_name = '{0}'--变量料号名
    and c.is_main = 1'''
    # 更新自动抓取AB板 新增条件 c.is_main = 1 20230424 by lyh
    data_info = conn.select_dict(sql.format(inplan_job.split("-")[0]))
    return data_info

def get_laser_depth_width_rate(inplan_job):
    """获取镭射纵横比"""
    conn=oracleConn("inmind")
    sql = u"""select a.job_name,
    a.MRP_NAME,
    b.program_name,
    b.drill_technology,
    b.start_index AS 起始层,
    b.end_index  AS 结束层,
    b.ASPECT_RATIO_ as 纵横比
    from vgt_hdi.RPT_JOB_PROCESS_LIST   a,
    vgt_hdi.RPT_DRILL_PROGRAM_LIST  b
    where a.root_id = b.root_id
    and a.MRP_NAME=b.PARENT_PROCESS_
    and b.drill_technology IN ( 0, 2 ) 
    and a.job_name = '{0}'"""
    data_info = conn.select_dict(sql.format(inplan_job.upper().split("-")[0]))
    return data_info

def get_user_authority(user, authority_name):    
    sql = "select * from hdi_engineering.incam_user_authority "
    data_info = conn.SELECT_DIC(dbc_h, sql)
    for dic_info in data_info:
        if str(dic_info["user_id"]) == user:
            if dic_info["Authority_Name"] == authority_name and \
               dic_info["Authority_Status"] == u"是":
                return True
            
    return False
  
def get_all_job_creation_date():
    """获取料号的创建时间"""
    conn=oracleConn("inmind")
    sql = """SELECT
    job_name,creation_date
    FROM
    vgt_hdi.rpt_job_list"""
    data_info = conn.select_dict(sql)
    return data_info

def get_drill_info_detail(inplan_job):
    """获取钻带详细信息"""
    conn=oracleConn("inmind")
    sql = u"""select a.job_name,
    a.MRP_NAME,
    b.program_name as ODB_DRILL_NAME,
    b.DRILL_LAYER_,
    decode( b.drill_technology, 0, 'Mechanical', 1, 'Controll Depth',
    5, 'Countersink', 6, 'Counterbore', 7, 'Backdrill' ) AS drill_type,
    round( a.PROCESS_LEVEL_ - 1 ) AS PROCESS_LEVEL,
    b.start_index AS start_index,
    b.end_index AS end_index,       
    C.NAME,
    round(c.finished_size*0.0254,3) as 成品孔径,
    c.pcb_count,
    c.type_t,
    c.IS_ADDI_HOLE_ as 是否附加孔
    from vgt_hdi.RPT_JOB_PROCESS_LIST A,
    VGT_HDI.RPT_DRILL_PROGRAM_LIST   b,
    VGT_HDI.Rpt_Drill_Hole_Info   c
    where a.root_id = b.root_id
    and a.MRP_NAME=b.PARENT_PROCESS_
    and b.ITEM_ID=c.ITEM_ID
    and b.REVISION_ID=c.REVISION_ID
    and a.job_name ='{0}'"""
    data_info = conn.select_dict(sql.format(inplan_job.split("-")[0]))
    return data_info
    
    
def get_inplan_jobs_for_uploading_layer_info(delay=180):
    """获取inplan料号"""
    conn=oracleConn("inmind")
    sql = """SELECT
    job_name,creation_date
    FROM
    vgt_hdi.rpt_job_list
    where length(job_name) = 13
    and SYSDATE - creation_date < {0}""".format(delay)
    data_info = conn.select_dict(sql)
    return data_info

def get_inplan_gold_area(inplan_job):
    """获取inplan镀金面积 20240422 by lyh"""
    conn=oracleConn("inmind")
    sql = """SELECT
    i.ITEM_NAME AS JobName,
    round(job.PG_AREA_C_/39.37/39.37,4) as GOLD_C,
    round(JOB.PG_AREA_S_/39.37/39.37,4) as GOLD_S
    FROM
    VGT_hdi.PUBLIC_ITEMS i,
    VGT_hdi.JOB_DA job
    WHERE
    i.ITEM_NAME = upper('{0}')
    AND i.item_id = job.item_id
    AND i.revision_id = job.revision_id"""
    # print(sql.format(inplan_job.split("-")[0]))
    data_info = conn.select_dict(sql.format(inplan_job.split("-")[0]))
    return data_info

def get_laser_params(inplan_job):
    """获取镭射参数包"""
    conn=oracleConn("inmind")
    sql = u"""		SELECT
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
    and a.item_name = '{0}'
    AND c.drill_technology = 2
    """
    data_info = conn.select_dict(sql.format(inplan_job.split("-")[0]))
    return data_info

def get_mysql_mi_drawing_mark_info(inplan_job, database="hdi_engineering.incam_process_info"):
    """
    获取MI标注的坐标信息 20240819 by lyh
    :return:
    """
    dbc_h = conn.MYSQL_CONNECT(hostName='192.168.2.19', database='hdi_engineering', prod=3306,
                               username='root', passwd='k06931!')      
    sql = """select * from hdi_engineering.drawings_marked where job_name like '{0}%' order by update_time desc"""
    data_info = conn.SELECT_DIC(dbc_h, sql.format(inplan_job.split("-")[0], database))

    return data_info

    