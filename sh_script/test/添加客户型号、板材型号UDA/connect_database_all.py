#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__  = "tiger"
__date__    = "2024.06.28"
__version__ = "$Revision: 1.0 $"
__credits__ = "HDI数据库连接"

import sys
import platform
reload(sys)
sys.setdefaultencoding('utf8')
if platform.system() == "Windows":
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
import Oracle_DB
import MySQL_DB
import re

class InPlan:

    def __init__(self, job):
        # --Oracle相关参数定义
        self.JOB_SQL = job.replace(job[13:], '').upper()
        self.DB_O = Oracle_DB.ORACLE_INIT()
        self.dbc_h = self.DB_O.DB_CONNECT(host='172.20.218.193', servername='inmind.fls', port='1521',
                                          username='GETDATA', passwd='InplanAdmin')

    def __del__(self):
        # --关闭数据库连接
        if self.dbc_h:
            self.DB_O.DB_CLOSE(self.dbc_h)

    def get_pp_type(self):
        """
        获取板材型号
        """
        sql = """
        SELECT JOB_NAME,
        LISTAGG(FAMILY_T, ', ') WITHIN GROUP (ORDER BY FAMILY_T) AS concatenated_values
        FROM (
        SELECT DISTINCT a.JOB_NAME, (VENDOR_T || FAMILY_T) FAMILY_T
        FROM vgt_hdi.rpt_job_stackup_cont_list a
        JOIN vgt_hdi.rpt_job_list j ON a.JOB_NAME=j.JOB_NAME 
        where TYPE in (0,3)
        and a.JOB_NAME= '%s'
        ) sub_Query
        GROUP BY JOB_NAME
        """ % self.JOB_SQL
        res = self.DB_O.SELECT_DIC(self.dbc_h, sql)
        if res:
            return res[-1]['CONCATENATED_VALUES']
        else:
            return None

    def get_set_add_slot(self):
        """
        获取工艺边是否添加防呆半槽
        """
        sql = """
        select JOB_NAME ,
                a.VALUE as 是否增加防呆半槽,   
                round(CI_BREAK_OFF_HALF_SLOT_SIZE_*0.0254,2) AS slot_size
                from vgt_hdi.rpt_job_list Rjob,    
                vgt_hdi.enum_values a
                where JOB_NAME='%s'    
                AND Rjob.CI_BREAK_OFF_ADD_HALF_SLOT_ = a.enum   
                AND a.enum_type = '1127' 
                AND a.VALUE = '增加防呆半圆槽'
                """ %  self.JOB_SQL
        res = self.DB_O.SELECT_DIC(self.dbc_h, sql)
        return res


    def get_ppname_type(self):
        """
        获取pp类型
        """
        sql = """
           SELECT
                a.job_name as 料号,
                a.PRINT_NUM_ as 工序,
                a.LAYER_NAME_ as 层别,
				a.MAT_ENG_NAME_ as PP名称,
                decode( BOM_MAT_TYPE_, 1, 'TB', 2, 'JB', 3, 'PP' ) as 类型,
                A.MATERIAL_COUNT_ AS 张数
            FROM
                VGT_HDI.Rpt_Job_Bom_Component_List a
            WHERE
                a.job_name = '%s'
                AND a.BOM_MAT_TYPE_ IN ( 1, 2, 3 )
                AND a.COMPONENT_TYPE = 0
                AND A.MATERIAL_COUNT_ <> 0
            ORDER BY
                a.PRINT_NUM_
            """ % self.JOB_SQL
        res = self.DB_O.SELECT_DIC(self.dbc_h, sql)
        return res


    def get_type_board(self):
        """
        获取3级产品类型
        """
        sql = """
            SELECT
                i.ITEM_NAME AS JobName,
                job.es_led_board_,
                JOB.JOB_PRODUCT_LEVEL3_
            FROM
                VGT_hdi.PUBLIC_ITEMS i,
                VGT_hdi.JOB_DA job
            WHERE
                i.ITEM_NAME = '%s'
            AND i.item_id = job.item_id
            AND i.revision_id = job.revision_id
            """ % self.JOB_SQL
        res = self.DB_O.SELECT_DIC(self.dbc_h, sql)
        if res:
            return res[-1]['JOB_PRODUCT_LEVEL3_']
        else:
            return None


    def get_kk(self):
        sql = """
                SELECT
					PROC.MRP_NAME ,	
				RJTSL.work_center_code,			
					ats.description work_description,
					ats.value_as_string
				FROM 
					VGT_HDI.RPT_JOB_TRAV_SECT_LIST RJTSL
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
				WHERE 
					RJTSL.JOB_NAME = '{0}'
					AND ats.description like '%镀金面积%'
				    """ .format(self.JOB_SQL)
        getResult = self.DB_O.SELECT_DIC(self.dbc_h, sql)
        return getResult


    def get_inplan_drill_note(self):
        sql = """
            select a.item_name job_name_,
               c.item_name layer_name_,
                ROUND(f.finished_size/39.37,3) as finished_size,
                ROUND(f.actual_drill_size/39.37,3) as actual_drill_size,
								g.MACHINING_METHOD_ as rs_choose,
								g.is_addi_hole_,
                decode(f.type,4,'Plated Slot',0,'PTH',1,'Via',2,'NPTH',3,'Micro Via',5,'Non-Plated Slot') as hole_type,
								g.erp_finish_size_,
								g.DRILL_NOTES_
					from vgt_hdi.items a
             inner join vgt_hdi.job b
							on a.item_id = b.item_id
							and  a.last_checked_in_rev = b.revision_id						
           inner join vgt_hdi.items c
             on a.root_id = c.root_id						 
           inner join vgt_hdi.drill_program d
							on c.item_id = d.item_id 
							and c.last_checked_in_rev = d.revision_id
           inner join vgt_hdi.drill_hole f
							on d.item_id = f.item_id 
							and d.revision_id = f.revision_id	
						inner join vgt_hdi.drill_hole_da g
							on f.item_id = g.item_id 
							and f.revision_id = g.revision_id
							and f.sequential_index=g.sequential_index	
					 WHERE a.item_name = upper('{0}')
							and  d.drill_technology in (2)
							and g.is_addi_hole_ = 0
							and ROUND(f.actual_drill_size/39.37,3) > 0.127
           order by c.item_name,f.name """.format(self.JOB_SQL)

        getResult = self.DB_O.SELECT_DIC(self.dbc_h, sql)
        if getResult:
            return getResult
        else:
            return None

    def get_layers_cu_thick(self):
        sql = """
        SELECT
            job_name,
            Layer_name,
            ROUND(finish_cu_thk_ , 2) as FINISH_CU_THICK,            
            ROUND(CAL_CU_THK_ / 1.0, 2) as  REQUIRED_CU_WEIGHT
        FROM
            VGT_HDI.RPT_COPPER_LAYER_LIST
            where
            Job_NAME = UPPER('%s')
         """%(self.JOB_SQL)
        getResult = self.DB_O.SELECT_DIC(self.dbc_h, sql)
        if getResult:
            return getResult
        else:
            return None

    def get_layer_etch_thick(self):
        """
        获取各层的铜厚补偿标准
        """
        sql = """select JOB_NAME,CI_SET_NAME,CIT_NAME
                ,ci_note.pre_instantiated_string
                from vgt_hdi.rpt_job_cam_instruction_list ci_Job
                left join (select * from vgt_hdi.ci_note) ci_note on ci_Job.item_id=ci_note.item_id
                and ci_Job.revision_id=ci_note.revision_id
                and ci_Job.sequential_index=ci_note.ci_sequential_index
                where (CIT_NAME='E.外层PCB' or CIT_NAME='D.内层')
                and ci_note.pre_instantiated_string like '%%补偿%%'
                and JOB_NAME='{0}'""".format(self.JOB_SQL)
        data_info = self.DB_O.SELECT_DIC(self.dbc_h, sql)
        mi_report_layer_cu_thick = {}
        for dic_info in data_info:
            detail_string_info = dic_info["PRE_INSTANTIATED_STRING"]
            if detail_string_info:
                for info in detail_string_info.decode("utf8").split(u"；"):
                    if "OZ" in info:
                        pattern = re.compile(u'(l\d+)/(l\d+)层按：([0-9]\.?\d{0,})/([0-9]\.?\d{0,})OZ补偿')
                        res = re.search(pattern, info)
                        units = "OZ"
                    else:
                        pattern = re.compile(u'(l\d+)/(l\d+)层按：([0-9]\.?\d{0,})/([0-9]\.?\d{0,})mil补偿')
                        res = re.search(pattern, info)
                        units = "mil"

                    if res:
                        mi_report_layer_cu_thick[res.group(1)] = (float(res.group(3)), units)
                        mi_report_layer_cu_thick[res.group(2)] = (float(res.group(4)), units)

        return mi_report_layer_cu_thick

    def get_inplan_bar_tt(self):
        sql = """
        	SELECT      
		        JOB_NAME，
		        MRP_NAME,
		        XARY_TARGET_TYPE_,
		        PROCESS_NUM_
            FROM VGT_HDI.MY_GRAPH_PROCESS_LIST
            WHERE JOB_NAME = '{0}'
            AND PROC_TYPE = 1
        """
        query_result = self.DB_O.SELECT_DIC(self.dbc_h, sql.format(self.JOB_SQL))
        return query_result

    def get_inplan_mrp_info(self,condtion="d.proc_subtype IN ( 28, 29 ) "):
        sql = """SELECT
        a.item_name AS job_name,
        d.mrp_name AS mrpName,
        ff.XARY_TARGET_TYPE_,
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
        LEFT JOIN VGT_HDI.MY_GRAPH_PROCESS_LIST ff ON a.item_name = ff.JOB_NAME 
    	and d.mrp_name = ff.MRP_NAME
        WHERE
        a.item_name = UPPER('{0}')
        AND d.proc_type = 1 
        AND {1}
        ORDER BY e.process_num_
        """

        data_info = self.DB_O.SELECT_DIC(self.dbc_h,sql.format(self.JOB_SQL, condtion))
        return data_info

    def get_inplan_all_flow(self):
        """
        全流程查询
        """
        sql = """
          SELECT 
        RJTSL.JOB_NAME,
		MRP_NAME,
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
        query_result = self.DB_O.SELECT_DIC(self.dbc_h, sql.format(self.JOB_SQL))
        return query_result

    def get_Layer_Info(self):
        """

        """
        sql = """
        SELECT 
        RJTSL.JOB_NAME,
		MRP_NAME,
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
         ORDER BY RJTSL.ORDER_NUM, RJTSL.TRAVELER_ORDERING_INDEX""" % self.JOB_SQL
        process_data = self.DB_O.SELECT_DIC(self.dbc_h, sql)
        return process_data

    def get_x_ray_number_bar(self):
        """
        查询见靶打几孔
        """
        sql = """
            SELECT 
                 RJTSL.JOB_NAME, 
		        proc.mrp_name, 
                RJTSL.DESCRIPTION, 
                nts.note_string 
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
            WHERE RJTSL.JOB_NAME = '{0}'
			AND RJTSL.DESCRIPTION LIKE '%X-RAY打靶%' 
		    AND   nts.note_string LIKE '%见靶钻_孔%' 
            """
        process_data = self.DB_O.SELECT_DIC(self.dbc_h, sql.format(self.JOB_SQL))
        return process_data

    def getSurfaceTreatment(self):
        """
        获取 表面处理及板类型
        """
        sql = """
            select JOB_NAME,
		            a.VALUE as 表面处理,
		            ES_HALF_HOLE_BOARD_ as 半孔板,
		            ES_LED_BOARD_ as LED,
		            ES_BATTERY_BOARD_ AS 电池板,
		            ES_WINDING_BOARD_ AS  线圈板,
		            ES_FREE_HALOGEN_ AS 无卤素,
		            ES_HIGH_TG_ AS 高TG，
		            ES_CAR_BOARD_ as 汽车板
            from vgt_hdi.rpt_job_list Rjob,
		        vgt_hdi.enum_values a	
	        WHERE JOB_NAME = '{0}' AND Rjob.SURFACE_FINISH_ = a.enum AND a.enum_type = '1000'
            """
        process_data = self.DB_O.SELECT_DIC(self.dbc_h, sql.format(self.JOB_SQL))
        return process_data

    def get_inplan_usage(self):
        """
        InPlan铜面积
        """
        sql = """
                select JOB_NAME,
                    LAYER_INDEX,
                    LAYER_NAME,
                    COPPER_USAGE as 残铜率
                from vgt_hdi.rpt_copper_layer_list
                where job_name ='%s'
                """ % self.JOB_SQL

        process_data = self.DB_O.SELECT_DIC(self.dbc_h, sql)
        copper_dict = {}
        for i in process_data:
            copper_dict[i['LAYER_NAME']] = i['残铜率']
        return copper_dict


    def get_job_customer(self):
        # 查询客户料号名
        sql = """
            SELECT
                a.item_name 料号名,
                d.customer_name 客户名,
                c.customer_job_name_ 客户品名
            FROM
                vgt_hdi.items a
                INNER JOIN vgt_hdi.job b ON a.item_id = b.item_id AND a.last_checked_in_rev = b.revision_id
                INNER JOIN vgt_hdi.job_da c ON b.item_id = c.item_id AND b.revision_id = c.revision_id
            	INNER JOIN vgt_hdi.customer d ON b.customer_id = d.cust_id
              WHERE a.item_name = '%s'
            """ % self.JOB_SQL

        data = self.DB_O.SELECT_DIC(self.dbc_h, sql)
        if data and data[0].get('客户品名'):
            return data[0].get('客户品名')
        else:
            return None

    def getLaminData(self):
        """
        获取压合信息
        :return:
        """
        sql = """
        SELECT
            a.item_name AS job_name,
            d.mrp_name AS mrpName,
            e.process_num_ AS process_num,          
            e.pressed_pnl_x_ / 1000 AS pnlroutx,
            e.pressed_pnl_y_ / 1000 AS pnlrouty
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
        process_data = self.DB_O.SELECT_DIC(self.dbc_h,sql)
        return process_data

class ERP():
    def __init__(self):
        # --连接ERP oracle数据库
        self.DB_O = Oracle_DB.ORACLE_INIT()
        # --servername的连接模式
        self.dbc_e = self.DB_O.DB_CONNECT(host='172.20.218.247', servername='topprod', port='1521',
                                          username='zygc', passwd='ZYGC@2019')
        if not self.dbc_e:
            # --sid连接模式
            self.DB_O = Oracle_DB.ORACLE_INIT(tnsName='sid')
            self.dbc_e = self.DB_O.DB_CONNECT(host='172.20.218.247', servername='topprod1', port='1521',
                                              username='zygc', passwd='ZYGC@2019')

        if not self.dbc_e:
            pass




    def Get_pcs_count(self,jobname):
        sql = """
            SELECT tc_aac01 料号,
                     tc_aac05 厂别,
                     tc_aac213 SET数,
                     tc_aac227 as "Panel中Pcs数"
            FROM tc_aac_file 
            where tc_aac01 = '%s'
        """ % jobname[:13].upper()
        query_result = self.DB_O.SELECT_DIC(self.dbc_e, sql)
        if query_result:
            return query_result[0]
        else:
            return None



    def get_area(self, job_name):
        """
        获取已经上传的化金,镀金面积
        :return:
        :rtype:
        """
        sql = """
        SELECT
            tc_aac01 料号,
            tc_aac123 C面化金面积,
            tc_aac124 C面化金百分比,
            tc_aac125 S面化金面积,
            tc_aac126 S面化金百分比,
            tc_aac119 C面镀金面积,
            tc_aac120 S面镀金面积

        FROM
            TC_AAC_FILE 
        WHERE
            tc_aac01 = '%s'
        """ % job_name[:13].upper()
        query_result = self.DB_O.SELECT_DIC(self.dbc_e, sql)
        return query_result

    def __del__(self):
        '''
        程序结束时关闭数据库连接
        :return: None
        '''
        self.DB_O.DB_CLOSE(self.dbc_e)

    def get_ERP_stackup(self, jobName):
        # 从ERP数据库中查出3张pp相关层别
        JOB_like= '%' + str(jobName).strip().upper() + '%'
        job_del = '%-B'
        query_sql = """
        SELECT
                TC_AAG00 as 料号,
                TC_AAG02 as 层别,
                TC_AAG09 as 材料类型,
                TC_AAG09 as 类别,
                TC_AAG16 as 品名规格,
                TC_AAG03 as 材料编码,
                TC_AAG05 as 张数,
                TC_AAG29,
                TC_AAG12,
                TC_AAG20 as 制作序号,
                TC_AAG26 as 压合板厚
        FROM
            TC_AAG_FILE
        WHERE
            TC_AAG09 <> 'GB'
            AND TC_AAG00 LIKE '%s'
            AND TC_AAG00 NOT LIKE '%s'
            ORDER BY TC_AAG12
        """ % (JOB_like, job_del)
        query_result = self.DB_O.SELECT_DIC(self.dbc_e, query_sql)
        layer_array = []
        layer_list = []
        JB_layer = []
        pp_sum = 0
        pre_layer = ''
        for row in query_result:
            layer = row['层别']
            type = row['材料类型']
            pp_cnt = row['张数']
            if type == 'TB' or type == 'JB':
                pre_lyrs = pre_layer.split('-')
                cur_lyrs = layer.lower().split('-')
                # 夹三张以上pp的层别放入数组
                if pp_sum >= 3:
                    # 铜箔前累加pp张数大于等于3张时，将夹三张pp的两张TB或JB层加入数组
                    layer_array = layer_array + pre_lyrs + cur_lyrs
                layer_list = layer_list + pre_lyrs + cur_lyrs
                # 出现铜箔或者基板后，将pp_sum_next张数归零
                pp_sum = 0
                # 出现铜箔或者基板后，将pre_layer重置为当前铜箔或基板层
                pre_layer = layer.lower()
                # --如果Type是基板，而且当前层有两层
                if type == 'JB' and len(cur_lyrs) >= 2:
                    for layer_name in cur_lyrs:
                        # --获取基板层别列表
                        if layer_name not in JB_layer:
                            JB_layer.append(layer_name)
            if type == 'PP':
                # 累加pp张数
                pp_sum += pp_cnt

        # 去除重复数据,并保持层别排序
        sort_array = []
        for i, layer in enumerate(layer_array):
            if layer not in sort_array:
                # if layer != "l1" and layer != "l" + str (int (self.JOB[4:6])):
                sort_array.append(layer)
        # 去除重复数据,并保持层别排序
        sort_list = []
        for i, layer in enumerate(layer_list):
            if layer not in sort_list:
                sort_list.append(layer)
        info_dict = {
            'all_layer': sort_list,
            '3pp_layer': sort_array,
            'JB_layer': JB_layer
        }
        return info_dict


    def getData(self):
        """
        检索返单数据
        :return:
        """
        sql = """
            SELECT  distinct OEB04 料号,
                            TA_IMA07 终端,
                            TC_DICT04 订单类型,
                            OEA032 客户,
                            OEB12_MJ 订单面积,
                            OEA72 下单日期,
                            OEAUD03 生产类型
            FROM 
                VIEW_HDIGC_OEB
            WHERE 
                OEA72 IS NOT NULL 
            and OEAUD01='B'
            and TA_OEB16='2:旧单'
            and OEAUD03<>'C:其它'
            and length(OEB04)=13
            and OEA72 = trunc (sysdate-1)
                """
        query_result = self.DB_O.SELECT_DIC(self.dbc_e, sql)
        return query_result

class MySql:
    def __init__(self):
        self.DB_M = MySQL_DB.MySQL()
        self.db_m = self.DB_M.MYSQL_CONNECT(database='hdi_engineering')
        self.db_e = self.DB_M.MYSQL_CONNECT(database='engineering')
        self.db_s = self.DB_M.MYSQL_CONNECT(database='project_status')


    def __del__(self):
        '''
        程序结束时关闭数据库连接
        :return: None
        '''
        self.DB_M.DB_CLOSE(self.db_m)

    def get_wip_formation(self, station=None):
        """
        获取在线WIP状态
        """
        jobnames = []
        if station:
            sql = """SELECT * FROM project_status.project_status_wip WHERE WIPStation LIKE '{0}' """.format(station)
        else:
            sql = """SELECT * FROM project_status.project_status_wip"""

        data = self.DB_M.SELECT_DIC(self.db_s, sql)
        if data:
            jobnames = list(set([str(d['job']) for d in data]))
        return jobnames


    def get_set_mask_slot_data(self, jobname):
        sql = """
        SELECT 
           * 
        FROM 
            fd_data_addsetmark 
        WHERE 
            job_name = '%s'
        ORDER BY id
        """ % jobname[:12].upper()
        data = self.DB_M.SELECT_DIC(self.db_e, sql)
        return data

    def updata_set_mask_slot(self,job_upper, width, height, mark_pos, mark_data, mark_width, mark_depth, user, date, business_unit):
        """
        更新防呆锣槽数据
        """
        get_data = self.get_set_mask_slot_data(job_upper)
        sql = """
              UPDATE
                  fd_data_addsetmark 
              SET
                      unit_width='%s',
                      unit_height='%s',
                      addmark_position='%s',
                      mark_data='%s',
                      mark_width='%s',
                      mark_depth='%s',
                      create_by='%s',
                      create_date='%s',
                      business_unit='%s'                      
                  WHERE
                      job_name = '%s'
                """ % (width, height, mark_pos, mark_data, mark_width, mark_depth, user, date, business_unit,job_upper)
        if get_data:
            self.DB_M.SQL_EXECUTE(self.db_e, sql)



    def inser_set_mask_slot(self,job_upper, width, height, mark_pos, mark_data, mark_width, mark_depth, user, date, business_unit):
        """
        插入防呆锣槽数据
        """
        sql_insert = """insert into fd_data_addsetmark 
                        (job_name,unit_width,unit_height,addmark_position,mark_data,mark_width,mark_depth,create_by,create_date,business_unit) 
                        VALUES ('%s','%s','%s','%s','%s','%s','%s','%s','%s','%s')"""
        sql_insert = sql_insert % (
        job_upper, width, height, mark_pos, mark_data, mark_width, mark_depth, user, date, business_unit)
        self.DB_M.SQL_EXECUTE(self.db_e, sql_insert)

    def get_cu_area(self):
        """
        获取已经上传的化金面积
        :return:
        :rtype:
        """
        sql = """
            select 
    	        jobname	,	
    	        cu_cs_Mm2,
    	        cu_ss_Mm2		
            from engineering.surface_and_gold_area 
            WHERE cu_note LIKE '%含假手指镀金%'
            """
        query_result = self.DB_M.SELECT_DIC(self.db_m, sql)
        return query_result

    def get_gold_areas(self, jobname):
        """
        查询镀金面积
        """
        sql = """   select
			            jobname,
			            cu_cs_Mm2 c_area,
                        cu_ss_Mm2 s_area			            
                    from engineering.surface_and_gold_area 
                    where jobname = '{0}'                   
                    """.format(jobname)
        data = self.DB_M.SELECT_DIC(self.db_m, sql)

        if data:
            return data[0]
        else:
            return None


    def updata_gold_areas(self,jobName,send_data,user, note=''):
        # 先查询记录再插入
        ss= self.get_gold_areas(jobName)
        print ss
        if not ss:
            sql="""
            INSERT INTO engineering.surface_and_gold_area
                (cu_cs_Mm2, cu_ss_Mm2, create_by, data_time, cu_note, jobname)
            VALUES ('%s','%s','%s','%s','%s','%s')
            """ %(send_data['TOP'], send_data['BOTTOM'], user, send_data['post_time'], note, jobName)

        else:
            ##有数据更新数据
            sql = """
                  UPDATE
                      engineering.surface_and_gold_area
                  SET
                      cu_cs_Mm2='%s',
                      cu_ss_Mm2='%s',
                      create_by='%s',
                      data_time='%s',
                      cu_note='%s'
                    WHERE
                      jobname = '%s'
                    """ %(send_data['TOP'], send_data['BOTTOM'], user, send_data['post_time'], note, jobName)
        self.DB_M.SQL_EXECUTE(self.db_m,sql)

    def getLock_Info(self, jobName):
        """
        从DB中获取锁定层的数据
        :param jobName: 型号名
        :return: dict
        """
        sql = """select * from  hdi_engineering.job_lock_data jld where jld.job_name = '%s'""" % jobName
        result = self.DB_M.SELECT_DIC(self.db_m, sql)
        if not result:
            return []

        # --一个料号仅一条数据
        result_dict = result[0]

        return result_dict


    def insert_email_data(self,dict_data={}):
        """
        插入邮件
        """
        keys = dict_data.keys()
        values = []
        for k in keys:
            values.append(dict_data[k])
        insert_sql = "INSERT INTO mailsent_table ({0}) VALUES ({1})"
        self.DB_M.SQL_EXECUTE(self.db_s, insert_sql.format(",".join(keys), ",".join(["%s"] * len(keys))),
                              params=values)


    def get_job_org_code(self,jobname):
        sql = u"""
                    SELECT
                        job,
        		        Org_code        		       
                  FROM project_status_jobmanage 
                  WHERE job = UPPER('%s')
                    """ % jobname
        data = self.DB_M.SELECT_DIC(self.db_s, sql)
        if data and data[-1]['Org_code'] == 'HDI事业部' :
            return True
        else:
            return False


    def get_mimaker_checker(self, jobname):
        """获取料号的制作人和审核人"""
        sql = u"""
            SELECT
                job,
		        Org_code,
		        mi_maker,
		        mi_checker
          FROM project_status_jobmanage 
          WHERE job = UPPER('%s') and Org_code = 'HDI事业部' 
            """ % jobname
        data = self.DB_M.SELECT_DIC(self.db_s, sql)
        dict_users = {}
        if data:
            dict_users['maker'] = data[-1]['mi_maker']
            dict_users['checker'] = data[-1]['mi_checker']

        return dict_users

    def get_user_email(self, user_name):
            """获取人员的邮箱地址"""
            sql = u"""
                SELECT
	                nickname,
	                email,
	                org_code
                FROM project_status_user
                WHERE org_code = 'HDI事业部' 
                AND email LIKE '%%pcb.com%%'
                AND nickname = '{0}'
                """ .format(user_name)
            data = self.DB_M.SELECT_DIC(self.db_s, sql)

            if data:
                email_address =  data[-1]['email']
                return email_address
            else:
                return None


    def get_email_reg_address(self, sub = 'HDI每日返单型号排查'):
        """获取收件人和抄送人邮件地址"""
        sql = u"""SELECT 
                        recipient_Address,
                        cc_Address,
                        bcc_Address
                  FROM email_recipient_info
                  WHERE email_subject = '{0}'""".format(sub)
        info = self.DB_M.SELECT_DIC(self.db_m, sql)[0]
        address_dict = {'rec':[],
                        'cc': [],
                        'bcc': []
                        }
        if info['recipient_Address']:
            address_dict['rec'] = str(info['recipient_Address']).split(';')
        if info['cc_Address']:
            address_dict['cc'] = str(info['cc_Address']).split(';')
        if info['bcc_Address']:
            address_dict['bcc'] = str(info['bcc_Address']).split(';')
        return address_dict


    def write_log_sql(self, jobname, type, recode_data, recode_time):
        """
        记录排查异常
        """
        insert_sql = """
                INSERT INTO incam_check_abnormal_records(id, job_name, check_type, abnormal_record, check_date)
                VALUES(NULL,'%s', '%s','%s', '%s')
                """ % (jobname, type, recode_data,recode_time)
        self.DB_M.SQL_EXECUTE(self.db_m, insert_sql)

    def check_setmark_slot(self, set_x,set_y,add_fx,add_size,add_zb):
        # 查询SET边防呆半槽
        sql_qurey_org = """SELECT 
                                job_name
                            FROM 
                                engineering.fd_data_addsetmark
                            WHERE                    
                                ABS(unit_width-%s) < 0.1
                            AND ABS(unit_height-%s) <0.1 
                            AND addmark_position='%s' 
                            AND mark_width=%s
                            AND ABS(mark_data-%s) < 0.2
                            """
        sql_qurey = sql_qurey_org % (set_x, set_y, add_fx, add_size,add_zb)
        data = self.DB_M.SELECT_DIC(self.db_m, sql_qurey)
        if data:
            return [d['job_name'] for d in data]
        else:
            return None



if __name__ == "__main__":
    # 测试
    inplan = InPlan('SD1024E7213BC')
    kk = inplan.get_inplan_drill_note()
    for d in kk:
        for key, val in d.items():
            print key, val
