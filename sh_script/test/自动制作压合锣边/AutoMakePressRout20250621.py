#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:AutoMakePressRout.py
   @author:zl
   @time: 2025/6/6 9:40
   @software:PyCharm
   @desc:
"""
import os
import platform
import re
import sys
import xlrd
from PyQt4 import QtCore, QtGui

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
import genClasses_zl as gen
from genesisPackages_zl import get_layer_limits
from get_erp_job_info import get_inplan_mrp_info, get_inplan_all_flow
import Oracle_DB


class AutoMakePressRout(object):
    def __init__(self):
        self.jobname = jobname[:13]
        mrp_info = get_inplan_mrp_info(self.jobname.upper())
        if not mrp_info:
            QtGui.QMessageBox.warning(self, 'tips', "没有压合数据")
        self.job = gen.Job(jobname)
        self.stepname = 'panel'
        if self.stepname not in self.job.getSteps():
            # return "没有panel"
            QtGui.QMessageBox.warning(self, 'tips', "没有panel")
        self.con = Oracle_DB.ORACLE_INIT()
        self.dbc_h = self.con.DB_CONNECT(host='172.20.218.193', servername='inmind.fls', port='1521',
                                         username='GETDATA', passwd='InplanAdmin')
        # self.output_path = '/windows/174.file/CNC/压合后锣边框'
        self.output_path = '/windows/174.file/CNC/临时'
        self.pnlrout_dic = {}
        for data in mrp_info:
            if data['PROCESS_NUM'] > 1:
                pnlrout = 'pnl_rout%s' % (data['PROCESS_NUM'] - 1)
                self.pnlrout_dic[pnlrout] = [data['FROMLAY'], data['TOLAY']]

    def make_press_rout(self):
        print(self.pnlrout_dic)
        step = gen.Step(self.job, self.stepname)
        gSRstep = step.DO_INFO('-t step -e %s/%s  -d SR' % (jobname, self.stepname)).get('gSRstep')
        for i, srname in enumerate(gSRstep):
            if re.search('set|edit', srname):
                self.set_order = i + 1
                break
        step.initStep()
        keys = sorted(self.pnlrout_dic.keys(), key=lambda i: int(i.split('pnl_rout')[1]))
        lastkey = keys[-1]
        inplan_all_flow = get_inplan_all_flow(self.jobname, True)
        output_routs = []
        board_process = self.get_process_by_job_name()
        print('aaa', board_process)
        self.rout_kanife_paramete = self.get_excel_kanife_parameters(board_process)
        # print(self.rout_kanife_paramete)
        # print(list(self.rout_kanife_paramete.keys()))
        # self.job.PAUSE('A')
        for data in inplan_all_flow:
            if data['WORK_CENTER_CODE'] == '打靶' and data['PROCESS_DESCRIPTION'] == 'X-RAY打靶':
                note_string = data['NOTE_STRING']
                # print(note_string)
                search = re.search('“(.*?)”', str(note_string))
                if not search:
                    continue
                pnl_rout_n = search.group(1)
                inn_layer = None
                if pnl_rout_n.upper() == 'T':
                    pnl_rout = lastkey
                    inn_layer = 'inn'
                else:
                    pnl_rout = 'pnl_rout%s' % pnl_rout_n
                if step.isLayer(pnl_rout):
                    # print(pnl_rout, self.pnlrout_dic.get(pnl_rout))
                    if not inn_layer:
                        inn_layer = 'inn%s%s' % (self.pnlrout_dic.get(pnl_rout)[0].replace('L', ''),
                                                 self.pnlrout_dic.get(pnl_rout)[1].replace('L', ''))
                        print(pnl_rout, inn_layer)
                    tmp_pnl_rout = '%s+++' % pnl_rout
                    step.removeLayer(tmp_pnl_rout)
                    step.COM('compensate_layer,source_layer=%s,dest_layer=%s,dest_layer_type=document' % (
                    pnl_rout, tmp_pnl_rout))
                    # step.affect(pnl_rout)
                    # step.copySel(tmp_pnl_rout)
                    # step.unaffectAll()
                    step.affect(tmp_pnl_rout)
                    step.setFilterTypes('pad')
                    step.selectAll()
                    step.resetFilter()
                    if step.Selected_count():
                        step.selectDelete()
                    step.selectCutData()
                    step.selectResize(-2400)
                    step.surf_outline()
                    step.selectSymbol('r0')
                    first_tool = None
                    if step.Selected_count():
                        gen_layer = gen.Layer(step, tmp_pnl_rout)
                        feats = gen_layer.featout_dic_Index(units='mm', options='feat_index+select')['lines']
                        xs, ys, xe, ye = feats[0].xs, feats[0].ys, feats[0].xe, feats[0].ye
                        xmin, xmax = min(xs, xe), max(xs, xe)
                        step.Transform('axis', y_offset=-1.2)
                        first_tool = [xmin, ys - 1.2, xmax, ye - 1.2]
                        # step.selectDelete()
                        # xmin, xmax = min(xs,xe), max(xs,xe)
                        # step.addLine(xmin - 1.2, ys, xmax - 1.2, ye, 'r100')
                        # first_tool = [xmin - 1.2, ys, xmax - 1.2, ye]
                    step.selectChange('r2400')
                    step.unaffectAll()
                    step.removeLayer('%s+++' % tmp_pnl_rout)
                    step.affect(inn_layer)
                    step.copySel(tmp_pnl_rout)
                    step.unaffectAll()
                    step.affect(tmp_pnl_rout)
                    step.setFilterTypes('pad')
                    step.selectAll()
                    step.resetFilter()
                    if step.Selected_count():
                        step.selectChange('r3100')
                    step.unaffectAll()
                    xmin, ymin, xmax, ymax = get_layer_limits(step, tmp_pnl_rout)
                    # xmin, ymin, xmax, ymax = xmin + 1.2, ymin + 1.2, xmax - 1.2, ymax - 1.2
                    gen_layer = gen.Layer(step, tmp_pnl_rout)
                    step.display(tmp_pnl_rout)
                    step.selectSingle(xmin + 1.2, (ymin + ymax) / 2)
                    feats = gen_layer.featout_dic_Index(units='mm', options='feat_index+select')['lines']
                    index, xs, ys, xe, ye = feats[0].feat_index, feats[0].xs, feats[0].ys, feats[0].xe, feats[0].ye
                    stretch_ys, stretch_y = min(ys, ye), max(ys, ye)
                    step.COM('stretch_feat,index=%s,x=%s,y=%s,xs=%s,ys=%s,xe=%s,ye=%s,tol=97.895' % (
                    int(index) - 1, xe, stretch_y, xs, stretch_ys, xe, ymax - 1.2))
                    step.clearSel()
                    step.addLine(xmax - 15.2, ymin + 1.2, xmax - 15.2, ymin + 4.2, 'r2400')
                    step.addLine(xmax - 15.2, ymin + 4.2, xmax - 9.2, ymin + 4.2, 'r2400')
                    step.addLine(xmax - 9.2, ymin + 4.2, xmax - 9.2, ymin + 1.2, 'r2400')
                    step.selectSingle((xmin + xmax) / 2, ymin + 1.2)
                    feats = gen_layer.featout_dic_Index(units='mm', options='feat_index+select')['lines']
                    index = feats[0].feat_index
                    step.COM('delete_feat,mode=intersect,index=%s,x=%s,y=%s,tol=76.645' % (
                    int(index) - 1, xmax - 12.2, ymin + 1.2))
                    self.job.matrix.modifyRow(tmp_pnl_rout, type='rout')
                    step.COM('chain_add,layer=%s,chain=1,size=2.4,comp=right,flag=0,feed=25,speed=0' % tmp_pnl_rout)
                    if first_tool:
                        xs, ys, xe, ye = first_tool[0], first_tool[1], first_tool[2], first_tool[3]
                        step.selectSingle(xs, ye)
                        step.COM('chain_add,layer=%s,chain=2,size=2.4,comp=right,flag=0,feed=25,speed=0' % tmp_pnl_rout)
                        step.COM('chain_list_reset')
                        step.COM('chain_list_add,chain=1')
                        step.COM('chain_list_add,chain=2')
                        step.COM('chain_merge,layer=%s,renumber_sequentially=no' % tmp_pnl_rout)
                    # step.COM('chain_add,layer=%s,chain_type=regular_chain,chain=1,size=2.4,flag=0,feed=0,speed=0,infeed_speed=0,retract_speed=0,pressure_foot=none,comp=right,repeat=no,plunge=no' % tmp_pnl_rout)
                    step.clearAll()
                    output_routs.append(tmp_pnl_rout)
                    # step.PAUSE(pnl_rout)
                    # self.output(tmp_pnl_rout)
        # self.job.PAUSE('ready')
        # 20250618 输出之前先清除out_file写入的文件
        tmp_file = 'c:/tmp/%s-rout-message' % self.jobname
        if os.path.exists(tmp_file):
            os.unlink(tmp_file)
        for output_rout in output_routs:
            self.output(output_rout)
            step.removeLayer('_nc_%s_out_' % output_rout)
            # step.removeLayer(output_rout)
        print('success')
        QtGui.QMessageBox.information(None, u'提示', u'压合锣边下发成功!!!')

    def get_excel_kanife_parameters(self, BoardProcess):
        kanife_data = {}
        print(BoardProcess.encode('utf8'))
        try:
            # 读取 Excel 文件
            # file_path = '//192.168.2.33/incam-share/incam/genesis/sys/scripts/hdi-scr/Output/output_rout/knife_too_parameter/hdi_kanife_parameter_list-2025.05.16.xls'
            file_path = '\\\\192.168.2.33\incam-share\incam\genesis\sys\scripts\hdi-scr\Output\output_rout\knife_too_ parameter\hdi_kanife_parameter_list-2025.05.16.xls'

            # 打开工作簿
            workbook = xlrd.open_workbook(file_path)

            # 循环读取 Excel 中的工作表
            for worksheet in workbook.sheets():
                sheet_name = worksheet.name
                # print('sheetname', sheet_name)
                if sheet_name == BoardProcess:
                    # 遍历行 (跳过标题行)
                    for row_idx in range(1, worksheet.nrows):  # 从第2行开始
                        # 获取行数据
                        row = worksheet.row_values(row_idx)

                        # 检查第一列是否有值
                        if not row[0]:  # 如果第一个单元格为空
                            break

                        kanife_size = row[0]
                        kanife_paramete = row[1]
                        compensate = row[2]

                        kanife_data[kanife_size] = {
                            'kanife_size': kanife_size,
                            'kanife_paramete': kanife_paramete,
                            'compensate': compensate
                        }

        except Exception as e:
            print(u"不能读取到excel刀具表数据 \n，%s！！！" % e)
            raise

        return kanife_data

    def get_process_by_job_name(self):
        sql = """
            select JOB_NAME,
		a.VALUE as 表面处理,
		ES_HALF_HOLE_BOARD_ as 半孔板,
		ES_LED_BOARD_ as LED,
		ES_BATTERY_BOARD_ AS 电池板,
		ES_WINDING_BOARD_ AS  线圈板,
		ES_FREE_HALOGEN_ AS 无卤素,
		ES_HIGH_TG_ AS 高TG,
		ES_CAR_BOARD_ AS 汽车板,
		ES_MEDICAL_BOARD_ AS 医疗板
   from vgt_hdi.rpt_job_list Rjob,
		vgt_hdi.enum_values a
   where JOB_NAME='%s' AND Rjob.SURFACE_FINISH_ = a.enum AND a.enum_type = '1000'
             """ % self.jobname.upper()
        recs = self.con.SQL_EXECUTE(self.dbc_h, sql)
        print(recs)
        # 查询是否有PTH 锣槽
        select_pth_sql = """
        SELECT JOB_NAME, PROCESS_NAME,	SEQUENTIAL_INDEX,	WORK_CENTER_CODE,	OPERATION_CODE,	S_DESCRIPTION
	FROM vgt_hdi.RPT_JOB_TRAV_SECT_LIST
	where OPERATION_CODE='HDI15201' and JOB_NAME='%s' order by SEQUENTIAL_INDEX
        """ % self.jobname.upper()
        recs_pth = self.con.SQL_EXECUTE(self.dbc_h, select_pth_sql)
        print(recs_pth)
        # 查询是否为罗杰斯板材
        board_rgs_sql = """SELECT JOB_NAME,
        LISTAGG(FAMILY_T, ', ') WITHIN GROUP (ORDER BY FAMILY_T) AS concatenated_values
        FROM (
        SELECT DISTINCT a.JOB_NAME, (VENDOR_T || FAMILY_T) FAMILY_T
        FROM vgt_hdi.rpt_job_stackup_cont_list a
        JOIN vgt_hdi.rpt_job_list j ON a.JOB_NAME=j.JOB_NAME 
        where TYPE in (0,3)
        and a.JOB_NAME= '%s') sub_Query GROUP BY JOB_NAME""" % self.jobname.upper()
        recs_rgs = self.con.SQL_EXECUTE(self.dbc_h, board_rgs_sql)
        print(recs_rgs)
        rou_tool_parameter = None
        if recs:
            if 'ROGERS' in recs_rgs[0][1]:
                rou_tool_parameter = 'Rogers（罗杰斯）板料（PTFE）'
            elif recs[0][2] == 1:
                rou_tool_parameter = '半孔.PTH槽参数'
            elif recs_pth:
                rou_tool_parameter = '半孔.PTH槽参数'
            elif re.search('.+金手指|GF\+', recs[0][1]):
                rou_tool_parameter = u'金手指卡板参数'
            elif recs[0][9] == 1:
                rou_tool_parameter = '医疗板参数'
            elif recs[0][4] == 1 or recs[0][5] == 1 or recs[0][6] == 1 or recs[0][7] == 1:
                rou_tool_parameter = '线圈板.无卤素.高TG.电池板'
            elif recs[0][3] == 1:
                rou_tool_parameter = '普通锣板参数.LED板参数.通孔板'
            else:
                rou_tool_parameter = '普通锣板参数.LED板参数.通孔板'
        else:
            rou_tool_parameter = '普通锣板参数.LED板参数.通孔板'
        if jobname[1:4] in ('d10', 'a86'):
            rou_tool_parameter = 'A86、D10'
        if jobname[1:4] == '183':
            zjb = self.get_183_board_type()
            if zjb:
                rou_tool_parameter = '183系列支架板'
        print(str(rou_tool_parameter))
        return rou_tool_parameter.decode('utf-8')

    def get_183_board_type(self):
        sql = """SELECT
                i.ITEM_NAME AS JobName,
                job.es_led_board_,
                JOB.JOB_PRODUCT_LEVEL3_
            FROM
                VGT_hdi.PUBLIC_ITEMS i,
                VGT_hdi.JOB_DA job
            WHERE
                i.ITEM_NAME = UPPER('%s')
            AND i.item_id = job.item_id
			AND JOB.JOB_PRODUCT_LEVEL3_ like '%支架板%'
            AND i.revision_id = job.revision_id""" % self.jobname
        res = self.con.SQL_EXECUTE(self.dbc_h, sql)
        if res:
            return 1
        return 0

    def add_config_data(self, output_file):
        print(output_file, self.rout_kanife_paramete)
        tool_num = self.get_tool_num_by_file(output_file)
        in_kanife_list = out_kanife_list = 0
        BC_rou_size = ''
        rout_body_kanife_paramete = {}
        strTemp = ''
        try:
            with open(output_file) as ncfile:
                for line in ncfile:
                    line = line.strip()
                    if line == 'M48':
                        in_kanife_list = 1
                    elif line == '%' and in_kanife_list:
                        out_kanife_list = 1
                    # if line == '%':
                    #     in_kanife_list = 1
                    # elif line == 'M48' and in_kanife_list:
                    #     out_kanife_list = 1
                    # # 判断是否在刀具列表里面，如果在里面就匹配刀具参数
                    # print(i, str(line))
                    # i+= 1
                    if in_kanife_list == 1 and out_kanife_list == 0 and self.rout_kanife_paramete != {}:
                        # if re.match('T\d+;C\d+\.\d+', line) and not re.search('DRL$|ZZ$', line):
                        if re.match('T\d+;C\d+\.\d+', line) and not re.search('DRL$|ZZ$', line):
                            rou_data_array = line.split()
                            split_array = rou_data_array[0].split('C')
                            rou_size = split_array[1]
                            rou_size = re.sub('\s','', rou_size)
                            # print('rou_size', rou_size, self.rout_kanife_paramete.get(float(rou_size)))
                            if len(split_array) == 2:
                                if self.rout_kanife_paramete.get(float(rou_size)):
                                    line = rou_data_array[0]
                                    tool_split = line.split(';')
                                    digital_tool = tool_split[0].split('T')
                                    line = re.sub('\s|;', '', line)
                                    change_patameter = self.rout_kanife_paramete.get(float(rou_size)).get('kanife_paramete')
                                    print('ppp', change_patameter)
                                    tail_zimu = ''
                                    if re.search('\d+\.\d\d[56]', rou_size):
                                        tail_zimu = 'FZ'
                                    if digital_tool[1] > tool_num - 2:
                                        change_patameter = re.sub('R\d+', 'R050', change_patameter)
                                        line = line + change_patameter + tail_zimu
                                        rout_body_kanife_paramete[tool_split[0]] = line
                                    else:
                                        line = line + change_patameter + tail_zimu
                                        rout_body_kanife_paramete[tool_split[0]] = line
                                    if len(rou_data_array) >= 3:
                                        rou_end_str = ''
                                        for i in range(2, len(rou_data_array)):
                                            rou_end_str = '%s%s' % (rou_end_str, rou_data_array[i])
                                        line = re.sub('\s+$', '', line)
                                        line = line + rou_end_str
                                    noCP = self.rout_kanife_paramete.get(float(rou_size))['compensate']
                                    noCP = re.sub('^CP','', noCP)
                                    BC_rou_size = BC_rou_size + 'CP%s,' % digital_tool[1] + noCP + '\n'
                    elif in_kanife_list and out_kanife_list and BC_rou_size:
                        line = BC_rou_size + line
                        BC_rou_size = ''
                        in_kanife_list = out_kanife_list = 0
                    if re.match('T\d+$', line):
                        rou_size_tmp = line
                        rou_size_tmp = re.sub('\s+$', '', rou_size_tmp)
                        if rout_body_kanife_paramete.get(rou_size_tmp):
                            line = rout_body_kanife_paramete.get(rou_size_tmp)
                            line = re.sub('FZ$', '', line)
                    line = re.sub('^/G05\n$', '', line)
                    line = re.sub('^/G40\n$', '', line)
                    strTemp = strTemp + line + '\n'
            # 将处理后的内容写回文件
            with open(output_file, 'w') as file:
                file.write(strTemp)
        # except FileNotFoundError:
        #     print('FileNotFoundError')
        except IOError as e:
            print(e)

    def get_tool_num_by_file(self, file_path):
        in_kanife_list = num_tool =  0
        try:
            with open(file_path) as ncfile:
                for line in ncfile:
                    if line == 'M48':
                        in_kanife_list = 1
                    elif line == '%' and in_kanife_list:
                        # out_kanife_list = 1
                        break
                    if in_kanife_list and re.match('T\d+;', line):
                        num_tool += 1
        # except FileNotFoundError:
        #     print('FileNotFoundError')
        except IOError as e:
            print(e)
        return num_tool


    def output(self, layer):
        ncPre = 'nc_%s' % layer
        offset_x, offset_y, op_scalex, scale_y, op_scaley, scale_center_y, xmirror, ymirror = 0, 0, 1, 1, 1, 1, 'no', 'no'
        if os.environ.get('INCAM_PRODUCT'):
            self.job.VOF()
            self.job.COM('nc_delete,layer=%s,ncset=%s' % (layer, ncPre))
            self.job.VON()
            self.job.COM('nc_create,ncset=%s,device=excellon_hdi,lyrs=%s,thickness=0' % (ncPre, layer))
            self.job.COM(
                'nc_set_advanced_params,layer=%s,ncset=%s,parameters=(rout_arc_as_ij=no)(out_exc_old_sr_syntax=no)' % (
                    layer, ncPre))
            self.job.COM('nc_set_current,job=%s,step=%s,layer=%s,ncset=%s' % (jobname, self.stepname, layer, ncPre))
            self.job.COM(
                'nc_set_file_params,output_path=%s,output_name=%s.%s,zeroes=trailing,units=mm,tool_units=mm,nf1=3,nf2=3,'
                'decimal=yes,modal_coords=no,single_sr=yes,sr_zero_set=no,repetitions=sr,incremental=no,ext_layer=ncr-drill,sr_zero_layer=,'
                'ccw=no,short_lines=none,allow_no_chain_f=no,no_chain_as_slot=no,keep_table_order=yes,max_arc_angle=180,comp_short_slot=no,'
                'gscale_file_name=,layer_datum=bottom_left,gscle_align_angle=0,gscl_offset_x=0,gscl_offset_y=0' % (
                    self.output_path, jobname.upper(), layer.replace('+', '')))
            self.job.COM(
                'nc_register,angle=0,xoff=0,yoff=0,version=1,xorigin=%s,yorigin=%s,xscale=%s,yscale=%s,xscale_o=%s,yscale_o=%s,xmirror=%s,ymirror=%s' % (
                offset_x, offset_y, op_scalex, scale_y, op_scaley, scale_center_y, xmirror, ymirror))
            self.job.COM('nc_order,serial=1,sr_line=%s,sr_nx=1,sr_ny=1,mode=lrbt,snake=yes' % self.set_order)
            # self.job.COM('top_tab,tab=NC Parameters Page')
            # self.job.COM('open_sets_manager,test_current=no')
            # self.job.PAUSE("请确认是否需要调整rout板顺序")
            self.job.COM('nc_cre_output,layer=%s,ncset=%s' % (layer, ncPre))
            # self.job.VOF()
            # self.job.matrix.deleteRow('_nc_%s_out_' % layer)
            # self.job.VON()
        else:
            # unicode_path = u'\\\\192.168.2.174\\GCfiles\\CNC\\压合后锣边框'
            unicode_path = u'D:\\disk\\rout\\%s' % jobname.upper()
            self.output_path = unicode_path.encode(sys.getfilesystemencoding())
            if not os.path.exists(self.output_path):
                os.makedirs(self.output_path)
            # print('aaaa', self.output_path+ '\n')
            self.job.COM("ncrset_page_open")
            self.job.COM("ncrset_cur,job=%s,step=%s,layer=%s,ncset=" % (jobname, self.stepname, layer))
            self.job.VOF()
            self.job.COM('ncrset_delete,name=%s' % ncPre)
            self.job.VON()
            self.job.COM("ncrset_create,name=%s" % ncPre)
            self.job.COM('ncrset_cur,job=%s,step=%s,layer=%s,ncset=%s' % (jobname, self.stepname, layer, ncPre))
            self.job.COM("ncr_set_machine,machine=excellon_hdi,thickness=0")
            self.job.COM(
                "ncr_set_params,format=excellon2,zeroes=trailing,units=mm,tool_units=mm,nf1=3,nf2=3,decimal=yes,modal_coords=no,single_sr=yes,sr_zero_set=no,repetitions=sr,drill_layer=ncr-drill,sr_zero_drill_layer=,break_sr=no,ccw=no,short_lines=none,press_down=no,last_z_up=16,max_arc_ang=180,sep_lyrs=no,allow_no_chain_f=no,keep_table_order=yes")
            self.job.COM(
                "ncr_register,angle=0,mirror=%s,xoff=0,yoff=0,version=1,xorigin=%s,yorigin=%s,xscale=%s,yscale=%s,xscale_o=%s,yscale_o=%s" % (
                xmirror, offset_x, offset_y, op_scalex, op_scaley, scale_center_y, scale_center_y))
            self.job.COM(
                "ncr_order,sr_line=%s,sr_nx=1,sr_ny=1,serial=1,optional=no,mode=lrbt,snake=yes,full=1,nx=0,ny=0" % self.set_order)
            # === 2023.03.11 转自多层，使用上次排刀序进行输出 ===
            # my $rout_table_list = "$logpath/$i"."_table_list"
            # my $now_table_list_path = "$logpath/$i"."_now_table_list"
            # &sort_table_by_last($i,$rout_table_list,$now_table_list_path)
            # self.job.PAUSE("please check rout Order")
            self.job.COM("ncr_table_close")
            self.job.COM("ncr_cre_rout")
            self.job.COM(
                "ncr_ncf_export,dir=%s,name=%s.%s" % (self.output_path, jobname.upper(), layer.replace('+', '')))
            # self.job.COM("ncr_ncf_export,dir=\\\\192.168.2.174\GCfiles\CNC\压合后锣边框,name=%s.%s" % (jobname, layer.replace('+', '')))
            # 2023.03.10 参考多层 输出指定锣带table 到user 路径唐成
            # self.job.COM("ncrset_units,units=mm")
            # self.job.COM("ncr_report,path=$rout_table_list")
            str_temp = ''
            file_path = '%s/%s.%s' % (self.output_path, jobname.upper(), layer.replace('+', ''))
            try:
                with open(file_path) as ncfile:
                    for line in ncfile:
                        # 移除/G05行
                        line = line.replace('/G05\n', '')
                        # 移除/G40行
                        line = line.replace('/G40\n', '')
                        str_temp += line
                # 将处理后的内容写回文件
                with open(file_path, 'w') as file:
                    file.write(str_temp)
            # except FileNotFoundError:
            #     print('FileNotFoundError')
            except IOError as e:
                print(e)
            self.add_config_data(file_path)
        '''
        foreach my $i (@selectlayers) {
		# --检查锣带销钉是否对称
		my $ncPre = "nc_".$i;
		my $pre_name = '';
		if ( defined $ENV{INCAM_PRODUCT} ) {
			$f->PAUSE("incam");
			$f->VOF;
				$f->COM("nc_delete,layer=$i,ncset=$ncPre");
			$f->VON;
			$f->COM("nc_create,ncset=$ncPre,device=excellon_hdi,lyrs=$i,thickness=0");
			$f->COM("nc_set_advanced_params,layer=$i,ncset=$ncPre,parameters=(rout_arc_as_ij=no)(out_exc_old_sr_syntax=no)");
			$f->COM("nc_set_current,job=$JOB,step=$op_step,layer=$i,ncset=$ncPre");
			$f->COM("nc_set_file_params,output_path=$current_path,output_name=$JOB.$i,zeroes=trailing,units=mm,tool_units=mm,nf1=3,nf2=3,decimal=yes,modal_coords=no,single_sr=yes,sr_zero_set=no,repetitions=sr,incremental=no,ext_layer=ncr-drill,sr_zero_layer=,ccw=no,short_lines=none,allow_no_chain_f=no,no_chain_as_slot=no,keep_table_order=yes,max_arc_angle=180,comp_short_slot=no,gscale_file_name=,layer_datum=bottom_left,gscle_align_angle=0,gscl_offset_x=0,gscl_offset_y=0");
			$f->COM("nc_register,angle=0,xoff=0,yoff=0,version=1,xorigin=$offset_x,yorigin=$offset_y,xscale=$op_scalex,yscale=$scale_y,xscale_o=$op_scaley,yscale_o=$scale_center_y,xmirror=$xmirror,ymirror=$ymirror");			
			$f->COM("nc_order,serial=1,sr_line=$set_order,sr_nx=1,sr_ny=1,mode=lrbt,snake=yes");
			#$f->COM("top_tab,tab=NC Parameters Page");
			#$f->COM("open_sets_manager,test_current=no");
			$f->PAUSE("请确认是否需要调整rout板顺序");
			$f->COM("nc_cre_output,layer=$i,ncset=$ncPre");
			$f->VOF;
			$f->COM("delete_layer,layer=_nc_$i\_out_");
			$f->VON;
		} else {
			#$f->PAUSE("Genesis");
			# --输出时料号名切换大写，后缀不变  --20191118  AresHe
            our $JobName = uc($JOB);
			# 做一个记录，是否用HDI的脚本输出
			my $recode_output_job_path = "C:/tmp/recode_hdi_output_name";
			open(FILE, '>',"$recode_output_job_path") or die "无法打开文件 $recode_output_job_path";;
			print FILE $JOB;
			close FILE;
			
            if (($i eq 'jp-rout' || $i eq 'ccd-rout') && $op_ccd_rout == 1) {
				# === 出货单元光学CCD锣带输出 ===
				
				&output_ccd_rout($i);
				#my $output_file = "$current_path/$JobName".uc($i);
				#if ($i eq 'jp.rou' ) { $output_file = "$current_path/$JobName.$i";}
				#&add_config_data($output_file,%rout_kanife_paramete);
				
			} else {
				$f->COM("ncrset_page_open");
				$f->COM("ncrset_cur,job=$JOB,step=$op_step,layer=$i,ncset=");
				$f->VOF;
					$f->COM("ncrset_delete,name=$ncPre");
				$f->VON;
				$f->COM("ncrset_create,name=$ncPre");
				$f->COM("ncrset_cur,job=$JOB,step=$op_step,layer=$i,ncset=$ncPre");
				$f->COM("ncr_set_machine,machine=excellon_hdi,thickness=0");
				$f->COM("ncr_set_params,format=excellon2,zeroes=trailing,units=mm,tool_units=mm,nf1=3,nf2=3,decimal=yes,modal_coords=no,single_sr=yes,sr_zero_set=no,repetitions=sr,drill_layer=ncr-drill,sr_zero_drill_layer=,break_sr=no,ccw=no,short_lines=none,press_down=no,last_z_up=16,max_arc_ang=180,sep_lyrs=no,allow_no_chain_f=no,keep_table_order=yes");
	
				$f->COM("ncr_register,angle=0,mirror=$xmirror,xoff=0,yoff=0,version=1,xorigin=$offset_x,yorigin=$offset_y,xscale=$op_scalex,yscale=$op_scaley,xscale_o=$scale_center_x,yscale_o=$scale_center_y");
				$f->COM("ncr_order,sr_line=$set_order,sr_nx=1,sr_ny=1,serial=1,optional=no,mode=lrbt,snake=yes,full=1,nx=0,ny=0");
				# === 2023.03.11 转自多层，使用上次排刀序进行输出 ===
				my $rout_table_list = "$logpath/$i"."_table_list";				
				my $now_table_list_path = "$logpath/$i"."_now_table_list";				
				&sort_table_by_last($i,$rout_table_list,$now_table_list_path);				
				$f->PAUSE("please check rout Order");
				
				$f->COM("ncr_table_close");		
				$f->COM("ncr_cre_rout");
				$f->COM("ncr_ncf_export,dir=$current_path,name=$pre_name$JobName.$i");
	
				# 2023.03.10 参考多层 输出指定锣带table 到user 路径唐成
				$f->COM("ncrset_units,units=mm");
				$f->COM("ncr_report,path=$rout_table_list");
				# 检测粗锣精修顺序 http://192.168.2.120:82/zentao/story-view-6803.html
				my $res = system "$pythonVer", "$scriptPath/hdi-scr/Output/output_rout/check_rou_index.py","check_index","$JOB","$i"."_table_list";
				if($res != 0){					
					return;
				}
				
				# 20200106李家兴添加，输出report,用来计算锣程
				$f->COM("ncrset_units,units=mm");
				my $report_file_path = "$current_path/$JobName.$i.report";
				$f->COM("ncr_report,path=$report_file_path");
				$f->COM("ncrset_units,units=inch");
				if ($softuser !~ /89627/) {
					system "//192.168.2.33/incam-share/incam/Path/Python26/python.exe","//192.168.2.33/incam-share/incam/genesis/sys/scripts/sh_script/nc_path/nc_path.py",$i,$report_file_path;
					system("rm -rf $report_file_path");
					#code
				}
				my $strTemp = "";
				open(FILE,"<$current_path/$pre_name$JobName.$i");
				while(<FILE>) {
			
					#先删除指定行（用空替换）
					$_ =~ s/^\/G05\n$//g;
					#再删除空行（用空替换）
					$_ =~ s/^\/G40\n$//g;
					$strTemp = $strTemp.$_;
				 }
				
				open(FILE,">$current_path/$pre_name$JobName.$i");
				print FILE $strTemp;
				close FILE;

                #锣带参数自动匹配
				&add_config_data("$current_path/$pre_name$JobName.$i", %rout_kanife_paramete);
			}
		}
		#$f->COM("set_subsystem,name=1-Up-Edit");	
		unlink("$output_message");
		
		# CCD锣带增加光学点检测及转换 http://192.168.2.120:82/zentao/story-view-6457.html
	if ($i =~ /^ccd|rout-cdc|rout-cds/ ) {
			my $res = system "$pythonVer", "$scriptPath/hdi-scr/Output/output_rout/re_write_ccd.py","$current_path","$pre_name$JobName.$i";	
				if($res != 0){
					$c->Messages('info',"CCD精修锣带参数写入文件失败！！！");					
					unlink "$current_path/$pre_name$JobName.$i";
					return;
				}
		}
		# 盖板作业增加M47指令，涨缩锣带自动对比正式锣带添加M47和ET字样
			# http://192.168.2.120:82/zentao/story-view-6605.html			
		if ($op_step =~ /panel/ && $i eq 'rout'){			
			my $res = system "$pythonVer", "$scriptPath/hdi-scr/Output/output_rout/re_write_M47_et.py","$current_path","$pre_name$JobName.$i","$scale_num","$JobName";	
				if($res != 0){
					$c->Messages('info',"写入M47&&ET指令失败！！！");					
					unlink "$current_path/$pre_name$JobName.$i";
					return;
				}
		}		
		
		# set输出锣带部分参数更新 
		if ($op_step =~ /set|edit/) {
			my $strTemp = "";
				open(FILE,"<$current_path/$pre_name$JobName.$i");
				while(<FILE>) {
					if ($_ !~ /M25\n$|M01\n$|M02\n$|M08\n$/){
						$strTemp = $strTemp.$_;
					}					
				 }
				
				open(FILE,">$current_path/$pre_name$JobName.$i");
				print FILE $strTemp;
				close FILE;
		}
		
		
		# --盲锣板输出自动化 AresHe 2021.10.29
		# --来源需求:http://192.168.2.120:82/zentao/story-view-3343.html
		if ($i =~ /^rout-cd[c|s]$|^ccd-rout-cd[c|s]$}/) {
			
			if (-f "$current_path/$pre_name$JobName.$i") {
				open(DATAFILE, "<$current_path/$pre_name$JobName.$i");
				my @DATALIST = <DATAFILE>;
				close DATAFILE;
				
				# --删除原文件
				unlink "$current_path/$pre_name$JobName.$i";
				
				# --保存文件
				open(WRITEFILE, ">$current_path/$pre_name$JobName.$i");
				
				my $flag;
				my $tool_count = 0;
				my $cp_count = 0;
				my $blind_tool;
				my $blind_first = 1;
				foreach my $des(@DATALIST){
					chomp $des;
					if ($des eq "M48") {
						$flag = "head";
					}elsif($flag eq "head"){
						if ($des =~ /\%/) {
							$flag = "boby";
						}
					}
					
					if ($flag eq "head") {
						if ($des =~ /^T\d+/) {
							if ($des =~ /ZZ$/i && $blind_first == 1) {
								my @tool_head = split(";",$des);								
								$blind_tool = $tool_head[0];
								$blind_first = 0;
							}else{
								if ($des =~ /^T\d+C/) {
									my @tool_head = split("C",$des);
									$tool_count = $tool_count + 1;
									my $tool = $tool_count;
									if ($tool < 10) {
										$tool = "0".$tool;
									}
									print WRITEFILE "T".$tool."C".$tool_head[1]."\n";
								}elsif($des =~ /^T(\d+);C(\d+\.\d+)(.*)/){
									# my @tool_head = split(";",$des);
									# my @tool_head = $1;
									$tool_count = $tool_count + 1;
									my $tool = $tool_count;									
									if ($tool < 10) {
										$tool = "0".$tool;
									}
									my $tool_new = int($2 * 100) / 100;	
									$tool_new = sprintf("%.3f", $tool_new);  #第3位小数变为0
									# print WRITEFILE "T$tool;$tool_head[1]\n";
									print WRITEFILE "T$tool;C$tool_new$3\n";  
								}
							}
						}else{
							if ($des =~ /^CP(\d+)(.*)/) {
								$cp_count = $1 * 1 - 1;
								my $tool = $cp_count;
								if ($tool < 10) {
									$tool = "0".$tool;
								}
								print WRITEFILE "CP".$tool.$2."\n";
							}else{
								print WRITEFILE "$des\n";
							}
						}
					}elsif($flag eq "boby"){
						if ($des eq $blind_tool) {
							print WRITEFILE "M127\n";
							print WRITEFILE "T98\n";
							$blind_first = 1;
						}elsif($des ne "G05"){
							if ($des =~ /^T(\d+)/) {
								$blind_first = 0;
								if ($1 > 1) {
									if ($des =~ /^T(\d+)$/) {
										my $tool = $1 * 1;
										$tool = $tool - 1;
										
										my $new_tool = $tool;
										if ($tool < 10) {
											$new_tool = "0".$tool;
										}
										print WRITEFILE "T$new_tool\n";
									}elsif($des =~ /^T(\d+)(C.*)/){
										my $tool = $1 * 1;
										$tool = $tool - 1;
										
										my $new_tool = $tool;
										if ($tool < 10) {
											$new_tool = "0".$tool;
										}
										print WRITEFILE "T".$new_tool.$2."\n";
									}
								}
							}else{
								print WRITEFILE "$des\n";
							}
						}elsif($des eq "G05" && $blind_first == 0){
							print WRITEFILE "$des\n";
						}
					}
				}
				close WRITEFILE;
			}
		}
		
		############## 输出记录
	    my $dbc_m = $o->CONNECT_MYSQL('host'=>'192.168.2.19', 'dbname'=>'hdi_engineering', 'port'=>'3306', 'user_name'=>'root', 'passwd'=>'k06931!');
		if (! $dbc_m)
		{
			$c->Messages('warning', '"工程数据库"连接失败-> 写入日志程序终止!');
			#exit(0);
			return;
		}

		open(OUT, ">>$logfile");
		if (-s "$logfile")
		{
		print OUT "\n";
		}
	
		print OUT "------------->>> $local_time\t$JOB\t$step_name\t\t$incam_user\t  at\tpc : $ipname\n
		$JOB,$i,$mirror,$offset_x,$offset_y,$scale_center_x,$scale_center_y,$scale_x,$scale_y,$mod_eng,$board_process,now(),$softuser,$ophost,$plat,$Version,$scale_num";
		
		#foreach my $i (@selectlayers)
		#{	
			#printf OUT "%-15s, 镜像:%s,\t偏移:%s,%s,\t涨缩中心(%s,%s),\tx涨缩：%s,\ty涨缩：%s\n ,\t涨缩方式: %s", $i,$mirror,$offset_x,$offset_y,$scale_center_x,$scale_center_y,$scale_x,$scale_y,$op_mode;
			#printf OUT "%-15s, Mirror:%s,\tOffset:%s,%s,\tScale_center:%s,%s,\txScale：%s,\t yScale：%s ,\t Scale_mode: %s\n", $i,$mirror,$offset_x,$offset_y,$scale_center_x,$scale_center_y,$scale_x,$scale_y,$mod_eng;
		my $sql = "insert into rout_output_log
		(job_name,layer,mirror,offset_x,offset_y,scale_center_x,scale_center_y,scale_x,scale_y,scale_mode,scale_num,param,log_time,creator,localhost,app_version)
		values('$JOB','$i','$mirror','$offset_x','$offset_y','$scale_center_x','$scale_center_y','$scale_x','$scale_y','$mod_eng','$scale_num','$board_process',now(),'$softuser','$ophost','$Version')";        
		my $sth = $dbc_m->prepare($sql);#结果保存在$sth中
		$sth->execute() or die "无法执行SQL语句:$dbc_m->errstr";
		#}
		close(OUT);
		$dbc_m->disconnect if ($dbc_m);  
		# if ($op_ccd_rout != 1) {
		# 	# 20200106李家兴添加，用来输出锣程,移至输出后立即执行
		# 	system "//192.168.2.33/incam-share/incam/Path/Python26/python.exe","//192.168.2.33/incam-share/incam/genesis/sys/scripts/sh_script/nc_path/nc_path_hdi.py",$current_path;
		# }
		
		# --不增加换行会导致COM命令失效。增加换行 song add 2022.01.04
		#print "\n";
		if ($scale_num ne "None") {
			my $get_result = system "$pythonVer", "$cur_script_dir/compare_rout.py",$JOB,$i,$scale_num,"$current_path/$pre_name$JobName.$i";
			my $result_num = &get_result_num($get_result);
			# 1——对应无法读取文件 100——非镜像 101——X镜像 102——Y镜像
			print '$result_num' . $result_num. "\n";
			if ($result_num == 1) {
				&message_show('是否退出?')
			}
		}
 	}
        '''


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    # app.setStyle('Cleanlooks')
    jobname = os.environ.get('JOB')
    auto_make_press_rout = AutoMakePressRout()
    auto_make_press_rout.make_press_rout()