#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:check_flow.py
   @author:zl
   @time: 2024/10/11 12:10
   @software:PyCharm
   @desc:
   检查是否有相关流程
"""
import os
import sys
if sys.platform == "win32":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    scriptPath = "%s/scripts" % os.environ.get('SCRIPTS_DIR', '/incam/server/site_data')
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")
from oracleConnect import oracleConn

def check_flow():
    StatusCode = 0
    JOB_SQL = jobname.upper().split('-')[0] if '-' in jobname else jobname.upper()
    conn = oracleConn("inmind")
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
        WHERE RJTSL.JOB_NAME = '%s'
        ORDER BY RJTSL.ORDER_NUM, RJTSL.TRAVELER_ORDERING_INDEX
        """ % JOB_SQL
    data_info = conn.select_dict(sql, is_arraysize=False)
    flows = ('沉金', '化金', '沉镍钯金') if flow == '1' else ('电镀镍金')
    if data_info:
        datas = list(filter(lambda d: d.get('WORK_CENTER_CODE') in flows, data_info))
        if datas:
            StatusCode = 1
    sys.exit(StatusCode)




if __name__ == '__main__':
    jobname = os.environ['JOB']
    flow = sys.argv[1]
    check_flow()