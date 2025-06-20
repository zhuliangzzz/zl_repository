#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------#
#               VGT SOFTWARE GROUP                        #
# ---------------------------------------------------------#
# @Author       :    LiuChuang
# @Mail         :    Chuang_cs@163.com
# @Date         :    2021.10.19
# @Revision     :    2.0.0
# @File         :    Add_Hole_YK_SJ.py
# @Software     :    PyCharm
# @Usefor       :    自动添加引孔(Slot+圆孔)
# V2.0 2022.07.28 Song 4.0以上加6孔导引孔 http://192.168.2.120:82/zentao/story-view-4457.html
# 2022.08.18 使用inplan的导引孔孔径
# 2022.08.23 函数getInplanDrlData运行时，会存在sql运行错误的情况，导引孔关系不能一一对应，增加try判断，并提示用户
# ---------------------------------------------------------#

_remark = {
    'description': '''
    This module defines classes to be used with Genesis 2000
    标准如下：
        http://192.168.2.120:82/zentao/story-view-3569.html
    '''
}


# --导入package
import math
import os
import sys
import csv
from PyQt4.QtGui import *

# --加载自定义package
sys.path.append(r"%s/sys/scripts/Package" % os.environ.get('SCRIPTS_DIR'))
#sys.path.append(r"d:/genesis/sys/scripts/Package")
from genesisPackages import  get_panelset_sr_step

import genCOM_26
import Oracle_DB
from mwClass_V2 import showMsg
from messageBoxPro import msgBox

# --初始化参数
GEN = genCOM_26.GEN_COM()
job = os.environ.get('JOB', None)
drl_list = []
step_list = []
# --定义扩孔的边界值
addMin_size = 3500
addMid_size = 4000
addMax_size = 6360
# --定义添加的预钻孔与大孔边距L=4mil
edge2edge = 101.6


# --主程式
def main():
    """定义全局变量"""
    global drl_list, step_list, inplan_drill_info
    # --获取钻带列表
    inplan_drill_info = getInplanDrlData(job)
    print inplan_drill_info
    PRINT(u'获取钻带列表..')
    drl_list = GEN.GET_ATTR_LAYER('drill')
    # PRINT(eval(drl_list))

    # --获取STEP列表
    PRINT(u'获取STEP列表..')
    step_list = get_panelset_sr_step(job, "panel")

    # --循环STEP处理钻带
    PRINT(u'开始循环所有Step，处理事件...')
    LOOP_STEP()


# --循环STEP列表
def LOOP_STEP():
    for step in step_list:
        PRINT(u'匹配panel内的Step...')
        # match = re.compile(r'^(edit|set)')
        # --当匹配时，跳过循环
        # if 'edit' in step:
        # --打开STEP
        PRINT(u'打开STEP:' + str(step) + '...')
        GEN.OPEN_STEP(step)
        PRINT(u'清除当前STEP显示及影响层...')
        GEN.CLEAR_LAYER()
        GEN.CHANGE_UNITS('mm')
        # --循环处理DRL层
        PRINT(u'开始循环' + str(step) + u'中的DRL列表...')
        LOOP_DRL(step)

        # --还原属性列表
        GEN.FILTER_RESET()

        # --关闭STEP(保留当前STEP不关闭)
        if step != 'edit':
            PRINT(u'关闭STEP:' + str(step))
            GEN.CLOSE_STEP()


# --循环Drl列表
def LOOP_DRL(step):
    global gDATUMx, gDATUMy
    # --取出当前Step的信息
    # datuMxy = GEN.DO_INFO('-t step -e %s/%s -m script -d DATUM' % (job, step))

    # gDATUMx = float(datuMxy['gDATUMx'])
    # gDATUMy = float(datuMxy['gDATUMy'])

    # --从资料中随便选择一个孔，用于判断是否有改动过初始的origin
    datumDic = GEN.getDatum(job, step, drl_list[0], units='mm')
    gDATUMx = datumDic['datum_x']
    gDATUMy = datumDic['datum_y']
    # GEN.PAUSE("DATUMx:%s DATUMy:%s" % (gDATUMx, gDATUMy))

    for drl in drl_list:
        PRINT(u'匹配非drl|2nd的钻孔层...')
        # --当匹配时，跳过循环
        if 'drl' != drl and '2nd' != drl:
            continue

        # --Do_Info孔信息 (当需要考虑共刀的情况时，需要doinfo checkStep)
        # allSize = GEN.DO_INFO('-t layer -e %s/%s/%s -m script -d TOOL -p drill_size -o break_sr' % (job, step, drl))
        allSize = GEN.DO_INFO('-t layer -e %s/%s/%s -m script -d TOOL' % (job, step, drl))

        # --打开工作层
        GEN.CLEAR_LAYER()
        # --备份层
        # GEN.DELETE_LAYER(drl + '++')
        bakDrl = drl + '++'
        if GEN.LAYER_EXISTS(bakDrl,job=job,step=step) == 'yes':
            # === 清空备份层，避免重复备份
            GEN.AFFECTED_LAYER(bakDrl,'yes')
            GEN.SEL_DELETE()
            GEN.AFFECTED_LAYER(bakDrl,'no')
        GEN.WORK_LAYER(drl)
        GEN.COPY_LAYER(job, step, drl, bakDrl)
        GEN.SEL_COPY(bakDrl)
        # --判断是否存在.bit='yk'属性的孔
        PRINT(u'判断是否存在.bit=yk属性的孔...')
        GEN.FILTER_TEXT_ATTR('.bit', 'yk', reset=1)
        GEN.FILTER_SELECT()
        if int(GEN.GET_SELECT_COUNT()) > 0:
            PRINT(u'存在,删除...')
            GEN.SEL_DELETE()
        else:
            PRINT(u'不存在,继续...')
        # --取出drl层中所有Symbol图形
        PRINT(u'取出drl层中所有Symbol图形...')
        gtool = GEN.DO_INFO('-t layer -e %s/%s/%s -m script -d TOOL' % (job, step, drl))

        # --循环drlill_size
        PRINT(u'再次循环所有Symbol List...')
        # n = -1
        hasAdd = {}
        for n,drl_size in enumerate(gtool['gTOOLdrill_size']):
            tool_count = int(gtool['gTOOLcount'][n])
            # n = gtool['gTOOLdrill_size'].index(drl_size)
            # n += 1
            # --可能会存在不同D码同一大小的孔（保存添加记录，以免重复添加）
            if 'r' + str(drl_size) in hasAdd.keys():
                continue
            else:
                hasAdd['r' + str(drl_size)] = True

            if step == 'set':
                PRINT('ID:%s shape:%s size:%s num:%s' % (n, gtool['gTOOLshape'][n], eval(drl_size), tool_count))
            # --取出 4.0<=D<=6.5mm的孔
            if gtool['gTOOLshape'][n] == 'hole' and addMin_size <= eval(drl_size) < addMid_size:
                PRINT(u'3.0mm≤D＜4.0mm除去3.175的孔，添加3个引孔，3个引孔成正三边形，引孔与大孔孔边相切')
                # --定义孔属性（可能存在属性不一样，或完成孔径不一样，有两个或多外同一孔径的数据）
                drl_attr = gtool['gTOOLtype'][n]
                ADD_YK('TYPE2', step, drl, drl_attr, eval(drl_size), tool_count)
            elif gtool['gTOOLshape'][n] == 'hole' and addMid_size <= eval(drl_size) < addMax_size:
                # PRINT(u'加6个孔')
                # --定义孔属性（可能存在属性不一样，或完成孔径不一样，有两个或多外同一孔径的数据）
                drl_attr = gtool['gTOOLtype'][n]
                ADD_YK('TYPE3', step, drl, drl_attr, eval(drl_size), tool_count)


# --添加扩孔引孔
def ADD_YK(type_, step, drl, drl_attr, drl_size, drl_count):
    # --打开工作层
    GEN.WORK_LAYER(drl)
    # --挑出此类孔，并取出坐标
    in_sym = 'r' + str(drl_size)
    GEN.FILTER_SET_INCLUDE_SYMS(in_sym, reset=1)
    GEN.FILTER_OPTION_ATTR('.drill', drl_attr)
    GEN.FILTER_SELECT()
    GEN.FILTER_RESET()
    get_count = int(GEN.GET_SELECT_COUNT())
    if get_count != drl_count:
        showMsg(u'层别：%s 孔径：%s，选中属性为%s的钻孔数量应为%s，实际为%s，请定义属性' % (drl,drl_size,drl_attr,drl_count,get_count))

    # --是否有选中物体
    if get_count > 0:
        # --INFO取出来的数据全部为字符格式，需要格式转换
        s_info = GEN.INFO('-t layer -e %s/%s/%s -m script -d FEATURES  -o select' % (job, step, drl))
        coord = []
        # --循环所有行（取出坐标信息）
        for line in s_info:
            if '#P' in line:
                # --以空格分隔成数组，取出坐标
                line_ = line.split(' ')
                coord.append([eval(line_[1]), eval(line_[2])])
                # GEN.PAUSE(line_[1])
        # --清除高亮
        GEN.CLEAR_FEAT()
        # --添加PAD
        if type_ == 'TYPE2':
            ADD_TYPE2_HOLE(drl_size, coord, drl_attr,drl)
        if type_ == 'TYPE3':
            ADD_TYPE3_HOLE(drl_size, coord, drl_attr,drl)


# --添加正常孔的预钻PAD
def ADD_TYPE2_HOLE(drl_size, coord, yk_attr,drl):
    # --设定孔属性
    GEN.CUR_ATR_SET('.bit', text='yk', reset=1)
    GEN.CUR_ATR_SET('.drill,option=%s' % yk_attr)
    # --计算出预钻孔M的直径
    # # d_size = int(drl_size / 2) - 200
    # d_size = (drl_size - 2*100 - 1000)/3
    #
    # # --取出50进位的孔
    # d_size = EXTRA_VAL(d_size)
    d_size = get_bit_inplan(drl_size,drl)
    print 'inplan',d_size
    if not d_size:
        d_size = get_burr_hole(drl_size)
    if not d_size:
        PRINT(u'规范表中无%s的导引孔钻咀...' % drl_size)
        d_size = (drl_size - 2 * 100 - 1000) / 3
        d_size = EXTRA_VAL(d_size)
    # GEN.PAUSE("%s"%d_size)
    # --判断此孔是否能与板内的孔共用
    # PRINT(u'取出与板内共用的预钻孔...')
    # # GEN.PAUSE("yksize:%s share_list:%s" % (d_size, allSize))
    # d_size=SHARE_HOLE(d_size, allSize)

    # --计算出大圆中心到小圆中心的距离
    # d2D = (float(drl_size / 4)) / 1000
    d2D = (float(drl_size / 2) - (edge2edge + float(d_size / 2))) / 1000

    # --五边开中的内角为72度，需要求出36度的正弦sin 与 余弦cos的值，首先需要先将角度转化为弧度
    sin30 = math.sin(math.radians(30))
    cos30 = math.cos(math.radians(30))
    # --当R<6.5MM时，添加中间的大孔
    for xy in coord:
        # --计算四个孔的坐标
        PRINT(u'计算三个预钻孔坐标...')
        # --上
        dx_1 = xy[0] + gDATUMx
        dy_1 = float(xy[1] + d2D) + gDATUMy
        # GEN.PAUSE("X:%s Y:%s" %(dx_1, dy_1))
        # --左下
        dx_2 = float(xy[0] - d2D * cos30) + gDATUMx
        dy_2 = float(xy[1] - d2D * sin30) + gDATUMy
        # --右下
        dx_3 = float(xy[0] + d2D * cos30) + gDATUMx
        dy_3 = float(xy[1] - d2D * sin30) + gDATUMy

        # --添加预钻孔
        PRINT(u'\n添加上边预钻孔...')
        GEN.ADD_PAD(dx_1, dy_1, 'r' + str(d_size), attr='yes')
        PRINT(u'\n添加左下边预钻孔...')
        GEN.ADD_PAD(dx_2, dy_2, 'r' + str(d_size), attr='yes')
        PRINT(u'\n添加右下边预钻孔...')
        GEN.ADD_PAD(dx_3, dy_3, 'r' + str(d_size), attr='yes')
    # --还原属性列表
    GEN.CUR_ART_RESET()
    GEN.FILTER_RESET()


# --添加正常孔的预钻PAD
def ADD_TYPE3_HOLE(drl_size, coord, yk_attr,drl):
    """
    6孔预钻孔
    :param drl_size:
    :param coord:
    :param yk_attr:
    :return:
    """
    # --设定孔属性
    GEN.CUR_ATR_SET('.bit', text='yk', reset=1)
    GEN.CUR_ATR_SET('.drill,option=%s' % yk_attr)
    # --计算出预钻孔M的直径
    # # d_size = int(drl_size / 2) - 200
    # d_size = (drl_size - 2*100 - 1000)/3
    #
    # # --取出50进位的孔
    # d_size = EXTRA_VAL(d_size)
    d_size = get_bit_inplan(drl_size,drl)
    if not d_size:
        d_size = get_burr_hole(drl_size)
    if not d_size:
        PRINT(u'规范表中无%s的导引孔钻咀...' % drl_size)
        d_size = (drl_size - 2 * 100 - 1000) / 3
        d_size = EXTRA_VAL(d_size)
    # GEN.PAUSE("%s"%d_size)
    # --判断此孔是否能与板内的孔共用
    # PRINT(u'取出与板内共用的预钻孔...')
    # # GEN.PAUSE("yksize:%s share_list:%s" % (d_size, allSize))
    # d_size=SHARE_HOLE(d_size, allSize)

    # --计算出大圆中心到小圆中心的距离
    # d2D = (float(drl_size / 4)) / 1000
    d2D = (float(drl_size / 2) - (edge2edge + float(d_size) * 0.5)) / 1000

    # --需要求出3的正弦sin 与 余弦cos的值，首先需要先将角度转化为弧度
    sin60 = math.sin(math.radians(60))
    cos60 = math.cos(math.radians(60))
    # --当R<6.5MM时，添加中间的大孔
    for xy in coord:
        # --计算6个孔的坐标
        PRINT(u'计算六个预钻孔坐标...')
        # --左
        dx_1 = xy[0] - d2D + gDATUMx
        dy_1 = xy[1] + gDATUMy
        # GEN.PAUSE("X:%s Y:%s" %(dx_1, dy_1))
        # --左下
        dx_2 = float(xy[0] - d2D * cos60) + gDATUMx
        dy_2 = float(xy[1] - d2D * sin60) + gDATUMy
        # --右下
        dx_3 = float(xy[0] + d2D * cos60) + gDATUMx
        dy_3 = float(xy[1] - d2D * sin60) + gDATUMy

        # -- 右
        dx_4 = xy[0] + d2D + gDATUMx
        dy_4 = xy[1] + gDATUMy
        # --右上
        dx_5 = float(xy[0] + d2D * cos60) + gDATUMx
        dy_5 = float(xy[1] + d2D * sin60) + gDATUMy

        # --左上
        dx_6 = float(xy[0] - d2D * cos60) + gDATUMx
        dy_6 = float(xy[1] + d2D * sin60) + gDATUMy
        # --添加预钻孔
        GEN.ADD_PAD(dx_1, dy_1, 'r' + str(d_size), attr='yes')
        GEN.ADD_PAD(dx_2, dy_2, 'r' + str(d_size), attr='yes')
        GEN.ADD_PAD(dx_3, dy_3, 'r' + str(d_size), attr='yes')
        GEN.ADD_PAD(dx_4, dy_4, 'r' + str(d_size), attr='yes')
        GEN.ADD_PAD(dx_5, dy_5, 'r' + str(d_size), attr='yes')
        GEN.ADD_PAD(dx_6, dy_6, 'r' + str(d_size), attr='yes')
    # --还原属性列表
    GEN.CUR_ART_RESET()
    GEN.FILTER_RESET()


# --考虑与板内的刀共刀
def SHARE_HOLE(holeSize, Drills, shareType='Normal'):
    """
    与板内的孔共刀
    :param shareType: 共享的类型（Slot引孔只允许向下取）
    :param holeSize:传入的孔大小
    :param Drills: 所有孔大小列表
    :return: 返回计算后的结果
    """

    if str(holeSize) in Drills:
        # GEN.PAUSE("A:%sB:%s" % (holeSize, Drills))
        pass
    # --非Slot引孔向下取
    elif str(holeSize + 50) in Drills and shareType == 'Normal':
        # GEN.PAUSE("AA:%sB:%s" % (holeSize, Drills))
        holeSize += 50
    elif str(holeSize - 50) in Drills:
        # GEN.PAUSE("AAA:%sB:%s" % (holeSize, Drills))
        holeSize -= 50
    else:
        # GEN.PAUSE("AAAA:%sB:%s" % (holeSize, Drills))
        pass
    # --返回最终判断结果
    # GEN.PAUSE('holeS:%s' % holeSize)
    return holeSize


# --取出50进位的孔
def EXTRA_VAL(yk_size):
    # --为与Inplan保持一至，先转换为MM四舍五入，保留两位小数，再还原为um
    yk_size = int(round(float(yk_size) / 1000, 2) * 1000)
    remainder = yk_size % 50
    if remainder == 0:
        return yk_size
    else:
        # --去掉余数的整数部分
        yk_size -= remainder
        # --就近取出对应50钻咀
        if 0 < remainder < 50:
            e_val = 0
        else:
            e_val = 50
        # --返回数据
        yk_size += e_val
        return yk_size


def get_burr_hole(holeSize):
    """
    根据钻孔表csv取孔径
    :param holeSize:
    :return:
    """
    scrDir = os.path.split(os.path.abspath(sys.argv[0]))[0]
    tool_select_list = []
    # D:\genesis\sys\scripts\sh_script\Add_Hole_YK\tool_select.csv
    with open(scrDir + '/tool_select.csv') as f:
        f_csv = csv.DictReader(f)
        for row in f_csv:
            tool_select_list.append(row)
    # print tool_select_list
    print 'holeSize:',holeSize
    burr_size = None
    for line in tool_select_list:
        if int(line['drill_lower']) < int(holeSize) < int(line['drill_upper']):
            burr_size = int(line['burr_hole'])
    print burr_size
    return burr_size


#  --转换中文
def ZH_CODE(zh, code='utf-8'):
    """
    转换中文编码
    :param zh   : uncode格式式的中文字符
    :param code : 转换中文的格式
    :return     : 返回转换后的中文
    """
    zh = zh
    code = code
    return zh.encode(code)


def PRINT(log_msg, code='utf-8'):
    """
    记录日志文件至tmp盘
    :param log_msg: 传入的日志信息
    :param code: 传入的字符编码，默认gb2312中文
    :return: None
    """
    # --Linux系统下中文需转为utf-8
    if os.name != 'nt':
        code = 'utf-8'
    # now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    try:
        log_msg = ZH_CODE(log_msg, code=code)
    except:
        log_msg = str(log_msg)
    print log_msg


def getInplanDrlData(job_name,):
    DB_O = Oracle_DB.ORACLE_INIT()
    dbc_o = DB_O.DB_CONNECT(host='172.20.218.193', servername='inmind.fls', port='1521',
                                      username='GETDATA', passwd='InplanAdmin')
    job_upper13 = job_name.upper()[0:13]
    # sql = """
    # SELECT
    #     cnt.item_name AS 料号名,
    #     lower(cnp.item_name) 钻带,
    #     round( dh.actual_drill_size / 39.37, 3 ) AS 钻咀,
    #     round( dh.FINISHED_SIZE / 39.37, 3 ) AS 成品孔径,
    #     (
    #     SELECT
    #         round( AA.ACTUAL_DRILL_SIZE / 39.37, 2 )
    #     FROM
    #         VGT_HDI.drill_hole AA,
    #         vgt_hdi.drill_hole_da BB
    #     WHERE
    #         AA.ITEM_ID = bb.item_id
    #         AND aa.revision_id = bb.revision_id
    #         AND aa.sequential_index = bb.sequential_index
    #         AND aa.item_id = dh.item_id
    #         AND aa.revision_id = dh.revision_id
    #         AND bb.drill_notes_ LIKE '%%成品%%' || round( dh.FINISHED_SIZE / 39.37, 3 ) || 'mm%%的导引孔%%'
    #     ) AS 导引孔
    # FROM
    #     VGT_HDI.Public_Items cnt,
    #     VGT_HDI.JOB job,
    #     VGT_HDI.Public_Items cnp,
    #     VGT_HDI.drill_program dp,
    #     VGT_HDI.drill_hole dh,
    #     vgt_hdi.drill_hole_da dh_a
    # WHERE
    #     cnt.item_id = job.item_id
    #     AND cnt.revision_id = job.revision_id
    #     AND cnt.root_id = cnp.root_id
    #     AND cnp.item_id = dp.item_id
    #     AND cnp.revision_id = dp.revision_id
    #     AND dp.item_id = dh.item_id
    #     AND dp.revision_id = dh.revision_id
    #     AND dh.item_id = dh_a.item_id
    #     AND dh.revision_id = dh_a.revision_id
    #     AND dh.sequential_index = dh_a.sequential_index
    #     AND cnp.item_name IN ( 'drl', 'DRL', 'Drl'，'2nd' ) --筛选钻带
    #     AND cnt.item_name = '%s' --料号名
    # """ % job_upper13


    sql = """
    SELECT
	cnt.item_name AS 料号名,
	cnp.item_name 钻带,
	round( dh.actual_drill_size / 39.37, 3 ) AS 钻咀,
	round( dh.FINISHED_SIZE / 39.37, 3 ) AS 成品孔径,
	(CASE WHEN dh_a.hole_mark_ IS NULL
                THEN NULL          
                ELSE 
	(SELECT
		distinct(round( AA.ACTUAL_DRILL_SIZE / 39.37, 2 ))
	FROM
		VGT_HDI.drill_hole AA,
		vgt_hdi.drill_hole_da BB 
	WHERE
		AA.ITEM_ID = bb.item_id 
		AND aa.revision_id = bb.revision_id 
		AND aa.sequential_index = bb.sequential_index 
		AND aa.item_id = dh.item_id 
		AND aa.revision_id = dh.revision_id 
		AND bb.drill_notes_ LIKE '%%' || dh_a.hole_mark_ || '%%引孔%%' 
	) END) AS 导引孔 
FROM
	VGT_HDI.Public_Items cnt,
	VGT_HDI.JOB job,
	VGT_HDI.Public_Items cnp,
	VGT_HDI.drill_program dp,
	VGT_HDI.drill_hole dh,
	vgt_hdi.drill_hole_da dh_a 
WHERE
	cnt.item_id = job.item_id 
	AND cnt.revision_id = job.revision_id 
	AND cnt.root_id = cnp.root_id 
	AND cnp.item_id = dp.item_id 
	AND cnp.revision_id = dp.revision_id 
	AND dp.item_id = dh.item_id 
	AND dp.revision_id = dh.revision_id 
	AND dh.item_id = dh_a.item_id 
	AND dh.revision_id = dh_a.revision_id 
	AND dh.sequential_index = dh_a.sequential_index 
	AND dh.TYPE NOT IN ( 4, 5 ) --slot类型
	AND cnp.item_name IN ( 'drl', 'DRL', 'Drl'，'2nd' ) --筛选钻带
	AND cnt.item_name = '%s' --料号名
""" % job_upper13
    queryRes = DB_O.SELECT_DIC(dbc_o, sql)
    DB_O.DB_CLOSE(dbc_o)
    # print queryRes
    try:
        if len(queryRes):
            return queryRes
        else:
            showMsg(u'JOB:%s Oracle数据库查询%s, 没有导引孔数据!' % (job_name, job_upper13))
            return None
    except TypeError:
        showMsg(u'JOB:%s Oracle数据库查询%s, 没有导引孔数据!' % (job_name, job_upper13))
        return None


def get_bit_inplan(drill_size, cur_layer, cut_tail='yes'):
    """
    从inplan中获取槽孔导引孔大小
    :return:
    """
    if not inplan_drill_info:
        return None
    info_list = inplan_drill_info
    bit_size = None
    c_diameter = drill_size * 1
    if cut_tail == 'yes':
        c_diameter = float(int(drill_size * 1000 / 25) * 25) / 1000
    for info in info_list:
        if info['钻带'] == cur_layer:
            inplan_size = info['钻咀'] * 1000
            if abs(inplan_size - c_diameter) < 0.001:
                # 取整的问题，不能用==,只能比较差值
                if info['导引孔']:
                    bit_size = info['导引孔'] * 1000
    PRINT(u'*%s,计算大小:%s引孔大小:%s!' % (drill_size,c_diameter,bit_size))

    return bit_size


# --MAIN主程式
if __name__ == '__main__':
    main()
    PRINT(u'***************************')
    PRINT(u'*引孔添加程序运行结束!')
    PRINT(u'***************************\n')
    showMsg(u'drl层预钻孔添加完成，原drl备份至drl++')
    # sys.exit(1)
