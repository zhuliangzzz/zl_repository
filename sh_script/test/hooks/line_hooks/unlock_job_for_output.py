#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = "luthersy"
__date__ = "20221223"
__version__ = "Revision: 1.0.0 "
__credits__ = u"""解锁资料输出权限 """

"""http://192.168.2.120:82/zentao/story-view-5012.html"""

import os
import sys
if sys.platform == "win32":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package")
else:
    scriptPath = "%s/scripts" % os.environ.get('SCRIPTS_DIR', '/incam/server/site_data')
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")

from create_ui_model import showMessageInfo

try:
    from TOPCAM_IKM import IKM
    ikm_fun = IKM()
except Exception, e:
    showMessageInfo(u"连接topcam数据库异常，请联系程序组处理:", str(e))
    sys.exit()
    
from mwClass_V2 import AboutDialog

def send_message_to_director(result, job_name):
    """发送审批结果界面 20221122 by lyh"""
    submitData = {
        'site': u'HDI板事业部',
        'job_name': job_name,
        'pass_tpye': 'CAM',
        'pass_level': 8,
        'assign_approve': '44024|51059|44813|83288|84310',
        'pass_title': result,
    }
    Dialog = AboutDialog(submitData['pass_title'], cancel=True, appCheck=True, appData=submitData)
    Dialog.exec_()
    # endregion

    # --根据审批的结果返回值
    if Dialog.selBut in ['x', 'cancel']:
        return False
    if Dialog.selBut == 'ok':
        return True
    
    return False

try:
    jobname = sys.argv[1]
except:    
    jobname = os.environ.get("JOB", None)

if jobname:    
    sql = "select lock_job_status,lock_job_reason from pdm_lock_job_for_output where jobname = '{0}'" 
    data_info = ikm_fun.PG.SQL_EXECUTE(ikm_fun.dbc_p, sql.format(jobname.lower()))
    if data_info:
        if data_info[0][0] == "all":
            log = u"此型号禁止输出资料，原因：{0},若要进行资料输出,请通知相关人员彭仁强、伍青、周燕、翟鸣放行！".format(data_info[0][1])
            res = send_message_to_director(log, jobname)
            if res:
                sql = u"update pdm_lock_job_for_output set lock_job_status='no', note='{1}' where jobname = '{0}'"
                ikm_fun.PG.SQL_EXECUTE(ikm_fun.dbc_p, sql.format(jobname.lower(), u"已被相关人放行"))