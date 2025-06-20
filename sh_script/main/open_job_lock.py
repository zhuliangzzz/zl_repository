#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------#
#               VTG.SH SOFTWARE GROUP                     #
# ---------------------------------------------------------#
# @Author       :    Song
# @Mail         :    
# @Date         :    2022/02/14
# @Revision     :    1.0.0
# @File         :    pre_open_job_check.py
# @Software     :    PyCharm
# @Usefor       :    用于验证是否有内层审核完成时间，来锁定料号内层
# Note By Song 料号锁定的原理是，在工程管理系统中存在此料号，且已有内层资料下发时间
# 2023.02.25 Song 增加打开料号如果有edit step则锁定orig及net step
# http://192.168.2.120:82/zentao/story-view-5191.html
# ---------------------------------------------------------#

import os
import platform
import sys
import json
from PyQt4 import QtCore, QtGui
import time
import datetime
import ast
import re
import copy
from Packages import GetData

# --导入Package
# --加载相对位置，以实现InCAM与Genesis共用
if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
from messageBox import msgBox
import genCOM_26 as genCOM
import MySQL_DB
import Oracle_DB


GEN = genCOM.GEN_COM()


def unicode_convert(input):
    """
    用于解决json.load json中带u开头的问题
    :param input:
    :return:
    """
    if isinstance(input, dict):
        new_dict = {}
        for key, value in input.iteritems():
            new_dict[unicode_convert(key)] = unicode_convert(value)
        return new_dict
        # return {unicode_convert (key): unicode_convert (value) for key, value in input.iteritems ()}
    elif isinstance(input, list):
        return [unicode_convert(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input


class CheckUserOpenJob(object):
    def __init__(self):
        # hook_tmp_file = sys.argv[1]
        # hook_dict = self.get_parm_dict(hook_tmp_file)
        # self.job_name = hook_dict['job']
        self.job_name = sys.argv[1]
        user_dict, self.icheck_time,self.ocheck_time,self.director_user_info = self.get_authorization()
        if not user_dict:
            print 'Not Engineering Management System Job'
            exit(0)
        # 连接MySQL数据库，并获取授权用户，判断当前用户是否在授权范围内 ===
        # user_list = [i for i in user_dict.values() if i]
        # 当工程管理系统中无此料号时，不做管控 ===
        # cam_user_name = os.environ.get('USER', None)
        # GEN.COM('get_user_name')
        # cam_user_name = GEN.COMANS
        # === 暂不获取ERP用户
        # erp_user_name = self.get_ERP_user_name(cam_user_name)
        # if not erp_user_name:
        #     print 'Not ERP Employee ID '
        # print erp_user_name
        # === 暂时不做授权用户检测 ===
        # self.run(cam_user_name, erp_user_name, user_list)
        self.getDATA = GetData.Data()

        PRODUCT = os.environ.get('INCAM_PRODUCT', None)
        # print PRODUCT
        if platform.system() == "Windows":
            self.userDir = "%s/fw/jobs/%s/user" % (os.environ.get('GENESIS_DIR', 'D:/genesis'), self.job_name)
        else:
            self.userDir = os.environ.get('JOB_USER_DIR', None)
            # === input_tgz 程序引用此程序时 JOB_USER_DIR 可能延续上一个料号
            if self.userDir and '/' + self.job_name + '/' not in self.userDir:
                self.userDir = None
            if PRODUCT and not self.userDir:
                # === 开启了软件，但是没有打开料号时，无JOB_USER_DIR
                job_dir = os.popen(PRODUCT + '/bin/dbutil path jobs ' + self.job_name).readline().strip('\n')
                # print job_dir
                self.userDir = str(job_dir) + '/user'
                # print '===' * 10
                # print self.userDir
            if not PRODUCT and not self.userDir:
                # --Linux环境下网络版genesis没有定义INCAM_PRODUCT环境变量
                self.userDir = "%s/fw/jobs/%s/user" % (os.environ.get('GENESIS_DIR', '/genesis'), self.job_name)
        self.cwd = os.path.dirname(sys.argv[0])
        # print 'icheck_time：%s' % self.icheck_time
        print 'userDir:%s' % self.userDir
        self.job_lock = '%s_job_lock.json' % self.job_name
        if self.icheck_time:
            self.lock_inner_layers()
        
        #翟鸣通知 暂时不锁外层 20240110
        #if self.ocheck_time:
            #self.lock_outer_layers()

        self.lock_org_steps()
        
    def getJOB_LockInfo(self, dataType='locked_info'):
        """
        从数据库中获取料号的锁记录
        :param dataType: 获取的数据类型（status:locked_info log:locked_log）
        :return:dict
        """
        lockData = self.getDATA.getLock_Info(self.job_name.split("-")[0])

        try:
            return json.loads(lockData[dataType], encoding='utf8'), lockData
        except:
            # print u'传入的数据参数异常'
            return {}, {}

    def run(self, cam_user_name, erp_user_name, user_list):
        if erp_user_name not in cam_user_name:
            text = u"用户：%s，非工程管理系统的授权用户！\n————已授权————\n%s\n————————————" % (
                erp_user_name, ','.join(user_list))
            msg_box = msgBox()
            msg_box.warning(self, '无编辑权限', '%s' % text, QtGui.QMessageBox.Ok)
            exit(0)

    def get_parm_dict(self, hook_tmp_file):
        """
        解析hooks临时文件，生成dict
        :param hook_tmp_file:
        :return:
        """
        # === 读文件 ===
        lineList = open(hook_tmp_file, 'r').readlines()
        # os.unlink (self.tmpfile)
        infoDict = GEN.parseInfo(lineList)
        # print infoDict
        hook_dict = {}
        if len(infoDict['lnPARAM']) > 0 and len(infoDict['lnVAL']) > 0:
            for i, inparm in enumerate(infoDict['lnPARAM']):
                hook_dict[inparm] = infoDict['lnVAL'][i]
        return hook_dict

    def get_authorization(self):
        """
        在MySQL数据库中获取授权用户
        :return:
        """
        job_str = self.job_name
        DB_M = MySQL_DB.MySQL()
        dbc_m = DB_M.MYSQL_CONNECT(hostName='192.168.2.19', database='project_status', prod=3306, username='root',
                                   passwd='k06931!', )
        query_sql = u"""
        select   cam_d_checker	CAM外层复审人,
            cam_d_innerChecker	CAM内层复审人,
            panel_maker	拼版人,
            inner_maker	内层制作人,
            outer_maker	外层制作人,
            icheck_maker	内层审核人,
            ocheck_maker	外层审核人,
            input_maker	Input人,
            input_checker	input审核人,
            rout_maker	锣带制作人,
            rout_checker	锣带检查人,
            sub_maker	次外层制作人,
            sub_check_maker	次外层审核人
            from project_status_jobmanage psj
            --  and project_status_jobmanage.COLUMNS cname
        WHERE job = '%s'
        order by id desc """ % job_str.upper()
        query_result = DB_M.SELECT_DIC(dbc_m, query_sql)

        # ifinish_sql = u"""
        # select  icheckfinish_time 内层审核完成时间
        #     from project_status_jobmanage psj
        #      WHERE job = '%s'
        # order by id desc """ % job_str.upper()
        # time_result = DB_M.SELECT_DIC(dbc_m, ifinish_sql)

        dbc_m.close()
        if len(query_result) == 0:
            text = u"料号：%s\n未在工程管理系统中,不进行料号锁定动作!" % (job_str)
            msg_box = msgBox()
            msg_box.warning(self, '警告', '%s' % text, QtGui.QMessageBox.Ok)
            return False, None, None, None
        result_dict = query_result[0]
        dbc_m = DB_M.MYSQL_CONNECT(hostName='192.168.2.19', database='engineering', prod=3306, username='root',
                                   passwd='k06931!', )
        ifinish_sql = u"""
        SELECT
            hand_out_datetime 内层资料下发时间
        FROM
            engineering.logs_cam_qa_hand_out 
        WHERE
            job_name = '%s' 
            AND hand_out_type = 'inner' 
        ORDER BY
            id DESC 
            LIMIT 1
            """ % job_str.upper()
        inner_time_result = DB_M.SELECT_DIC(dbc_m, ifinish_sql)
        
        ofinish_sql = u"""
        SELECT
            hand_out_datetime 外层资料下发时间
        FROM
            engineering.logs_cam_qa_hand_out 
        WHERE
            job_name = '%s' 
            AND hand_out_type = 'outer' 
        ORDER BY
            id DESC 
            LIMIT 1
            """ % job_str.upper()
        outer_time_result = DB_M.SELECT_DIC(dbc_m, ofinish_sql)
        
        dbc_m = DB_M.MYSQL_CONNECT(hostName='192.168.2.19', database='hdi_engineering', prod=3306,
                                   username='root', passwd='k06931!')        
        sql = u"select * from hdi_engineering.incam_user_authority "
        director_user_info = DB_M.SELECT_DIC(dbc_m, sql)        
        
        dbc_m.close()

        # === 键为中文，需要带上u字符
        # for key in result_dict:
        #     if key == u'内层制作人':
        # print 'x' * 40
        if len(inner_time_result) == 0:
            inner_result = None
        else:
            inner_result = inner_time_result[0][u'内层资料下发时间']
            
        if len(outer_time_result) == 0:
            outer_result = None
        else:
            outer_result = outer_time_result[0][u'外层资料下发时间']            
            
        return result_dict, inner_result, outer_result, director_user_info

    def get_ERP_user_name(self, cam_user_name):
        """

        :return:
        """
        # === ERP连接 ===
        DB_O = Oracle_DB.ORACLE_INIT()
        dbc_e = DB_O.DB_CONNECT(host='172.20.218.247', servername='topprod', port='1521',
                                username='zygc', passwd='ZYGC@2019')
        query_sql = """
        SELECT gen02 姓名 FROM s01.gen_file WHERE gen01='%s'
        """ % cam_user_name
        query_result = DB_O.SQL_EXECUTE(dbc_e, query_sql)
        DB_O.DB_CLOSE(dbc_e)

        if query_result:
            e_user_name = query_result[0][0]
            # print  e_user_name.decode('utf8').encode('gbk') # 在Genesis下调试用
            return e_user_name.decode('utf8')
        else:
            text = u"用户：%s\n不在ERP用户中!" % (cam_user_name)
            msg_box = msgBox()
            msg_box.warning(self, '警告', '%s' % text, QtGui.QMessageBox.Ok)
            return False

    def get_job_matrix(self):

        inner_layers = []
        outer_layers = []
        drill_layers = []
        board_layers = []
        m_info = GEN.DO_INFO("-t matrix -e %s/matrix" % self.job_name)
        step_list = m_info['gCOLstep_name']
        layer_list = m_info['gROWname']
        for row in m_info['gROWrow']:
            num = m_info['gROWrow'].index(row)
            if m_info['gROWcontext'][num] == 'board' and m_info['gROWlayer_type'][num] not in ['components', 'solder_paste', 'rout']:
                board_layers.append(m_info['gROWname'][num])
            if m_info['gROWcontext'][num] == 'board' and m_info['gROWlayer_type'][num] == 'drill':
                if m_info['gROWname'][num] not in ['lp', 'sz.lp', 'sz...dq']:
                    drill_layers.append(m_info['gROWname'][num])

            if m_info['gROWcontext'][num] == 'board' and m_info['gROWside'][num] == 'inner':
                inner_layers.append(m_info['gROWname'][num])

            elif m_info['gROWcontext'][num] == 'board' and m_info['gROWlayer_type'][num] == 'signal' and (
                    m_info['gROWside'][num] == 'top' or m_info['gROWside'][num] == 'bottom'):
                outer_layers.append(m_info['gROWname'][num])

        # 周涌通知 外层盖孔资料需排除掉 20221117 by lyh       
        inner_layers = [layer for layer in inner_layers
                        if layer.split("-")[0] not in outer_layers]

        return step_list, inner_layers, outer_layers, drill_layers,board_layers

    def lock_inner_layers(self):
        step_list, inner_layers, outer_layers, drill_layers,board_layers = self.get_job_matrix()
        # === 读取锁定文件，并写锁定Log 用户使用不使用获取，使用Auto===
        # --从数据库中获取lock记录 获取不到在从文件内获取 20230904 by lyh
        pre_lock,data_info = self.getJOB_LockInfo(dataType='locked_info')
        if not pre_lock:
            pre_lock = self.read_file(sour_file=self.job_lock)
             
        #12小时内 审核人解锁的型号 暂时不自动上锁 20231121 by lyh
        for dic_info in self.director_user_info:
            if str(dic_info["user_id"]) == data_info.get("update_by", None):
                if dic_info["Authority_Name"] == u"审核人权限" and \
                   dic_info["Authority_Status"] ==u"是":
                    delta = (datetime.datetime.now() - data_info["update_date"] )
                    if  delta.seconds/ 3600.0 < 1:
                        return
            
        job_lock = copy.deepcopy(pre_lock)
        for j, cur_step_name in enumerate(step_list, 1):
            for i, cur_layer_name in enumerate(inner_layers + drill_layers, 1):
                if cur_step_name not in job_lock:
                    job_lock[cur_step_name] = [cur_layer_name]
                else:
                    if cur_layer_name not in job_lock[cur_step_name]:
                        job_lock[cur_step_name].append(cur_layer_name)

        self.write_file(job_lock, desfile=self.job_lock)
        # --将收集到的数据以json的格式写入数据库中-写锁记录
        self.getDATA.uploadLock_Layers(self.job_name.split("-")[0], lockJson=job_lock, userId="OPEN_HOOK")
        
        M = DiffDict(job_lock, pre_lock)
        lock_add = M.get_added()
        lock_change = M.get_changed()
        unlock = M.get_removed()

        o_lock_add, o_unlock = self.separate_lock_changes(lock_change)
        lock_add += o_lock_add
        unlock += o_unlock

        time_key = int(time.time())
        time_form = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time_key))
        # ====
        log_dict = {time_key: {'user': 'OPEN_HOOK', 'lock_add': lock_add, 'unlock': unlock, 'time': time_form}}

        # print 'log_dict='
        # print log_dict
        pre_log_dict = self.read_file(sour_file='job_lock_log.json')
        log_dict.update(pre_log_dict)
        self.write_file(log_dict, desfile='job_lock_log.json')
        self.getDATA.uploadLock_Layers(self.job_name.split("-")[0], logJson=log_dict, userId="OPEN_HOOK") 
        
    def lock_outer_layers(self):
        step_list, inner_layers, outer_layers, drill_layers,board_layers = self.get_job_matrix()
        # === 读取锁定文件，并写锁定Log 用户使用不使用获取，使用Auto===
        # --从数据库中获取lock记录 获取不到在从文件内获取 20230904 by lyh
        pre_lock,data_info = self.getJOB_LockInfo(dataType='locked_info')
        if not pre_lock:
            pre_lock = self.read_file(sour_file=self.job_lock)
             
        #12小时内 审核人解锁的型号 暂时不自动上锁 20231121 by lyh
        for dic_info in self.director_user_info:
            if str(dic_info["user_id"]) == data_info.get("update_by", None):
                if dic_info["Authority_Name"] == u"审核人权限" and \
                   dic_info["Authority_Status"] ==u"是":
                    delta = (datetime.datetime.now() - data_info["update_date"] )
                    if  delta.seconds/ 3600.0 < 1:
                        return                    
            
        job_lock = copy.deepcopy(pre_lock)
        for j, cur_step_name in enumerate(step_list, 1):
            for i, cur_layer_name in enumerate(outer_layers+inner_layers + drill_layers+board_layers, 1):
                if cur_step_name not in job_lock:
                    job_lock[cur_step_name] = [cur_layer_name]
                else:
                    if cur_layer_name not in job_lock[cur_step_name]:
                        job_lock[cur_step_name].append(cur_layer_name)

        self.write_file(job_lock, desfile=self.job_lock)
        # --将收集到的数据以json的格式写入数据库中-写锁记录
        self.getDATA.uploadLock_Layers(self.job_name.split("-")[0], lockJson=job_lock, userId="OPEN_HOOK")
        
        M = DiffDict(job_lock, pre_lock)
        lock_add = M.get_added()
        lock_change = M.get_changed()
        unlock = M.get_removed()

        o_lock_add, o_unlock = self.separate_lock_changes(lock_change)
        lock_add += o_lock_add
        unlock += o_unlock

        time_key = int(time.time())
        time_form = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time_key))
        # ====
        log_dict = {time_key: {'user': 'OPEN_HOOK', 'lock_add': lock_add, 'unlock': unlock, 'time': time_form}}

        # print 'log_dict='
        # print log_dict
        pre_log_dict = self.read_file(sour_file='job_lock_log.json')
        log_dict.update(pre_log_dict)
        self.write_file(log_dict, desfile='job_lock_log.json')
        self.getDATA.uploadLock_Layers(self.job_name.split("-")[0], logJson=log_dict, userId="OPEN_HOOK") 

    def lock_org_steps(self):
        step_list, inner_layers, outer_layers, drill_layers, board_layers = self.get_job_matrix()
        # === 读取锁定文件，并写锁定Log 用户使用不使用获取，使用Auto===
        # --从数据库中获取lock记录 获取不到在从文件内获取 20230904 by lyh
        pre_lock,data_info = self.getJOB_LockInfo(dataType='locked_info')
        if not pre_lock:
            pre_lock = self.read_file(sour_file=self.job_lock)            
            
        #12小时内 审核人解锁的型号 暂时不自动上锁 20231121 by lyh
        for dic_info in self.director_user_info:
            if str(dic_info["user_id"]) == data_info.get("update_by", None):
                if dic_info["Authority_Name"] == u"审核人权限" and \
                   dic_info["Authority_Status"] ==u"是":
                    delta = (datetime.datetime.now() - data_info["update_date"] )
                    if  delta.seconds/ 3600.0 < 1:
                        return             
            
        job_lock = copy.deepcopy(pre_lock)
        # print 'pre_lock_net',pre_lock['net']
        org_Reg = re.compile('orig|org|net')
        if 'edit' not in step_list:
            return
        for j, cur_step_name in enumerate(step_list, 1):
            if not org_Reg.match(cur_step_name):
                continue
            for i, cur_layer_name in enumerate(board_layers, 1):
                if cur_step_name not in job_lock:
                    job_lock[cur_step_name] = [cur_layer_name]
                else:
                    if cur_layer_name not in job_lock[cur_step_name]:
                        job_lock[cur_step_name].append(cur_layer_name)

        self.write_file(job_lock, desfile=self.job_lock)
        # --将收集到的数据以json的格式写入数据库中-写锁记录
        self.getDATA.uploadLock_Layers(self.job_name.split("-")[0], lockJson=job_lock, userId="OPEN_HOOK_LOCK_ORG")
        
        # print 'job_lock',job_lock
        # print 'pre_lock',pre_lock
        M = DiffDict(job_lock, pre_lock)
        lock_add = M.get_added()
        lock_change = M.get_changed()
        unlock = M.get_removed()
        # print 'lock_add',lock_add
        # print 'lock_change',lock_change
        # print 'unlock',unlock

        o_lock_add, o_unlock = self.separate_lock_changes(lock_change)
        # print 'o_lock_add',o_lock_add
        # print 'o_unlock',o_unlock

        lock_add += o_lock_add
        unlock += o_unlock

        time_key = int(time.time())+1
        time_form = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time_key))
        # ====
        log_dict = {time_key: {'user': 'OPEN_HOOK_LOCK_ORG', 'lock_add': lock_add, 'unlock': unlock, 'time': time_form}}
        # print 'before',log_dict
        # print 'log_dict='
        # print log_dict
        pre_log_dict = self.read_file(sour_file='job_lock_log.json')
        log_dict.update(pre_log_dict)
        # print 'after',log_dict

        self.write_file(log_dict, desfile='job_lock_log.json')
        self.getDATA.uploadLock_Layers(self.job_name.split("-")[0], logJson=log_dict, userId="OPEN_HOOK_LOCK_ORG") 

    def separate_lock_changes(self, ip_lock_change):
        """
        锁定变更，细化为锁定与解锁
        :param ip_lock_change: [{step:'',layers:"['','']->['',]"(字符串类型)}]
        :return:
        """
        lock_add = []
        unlock = []
        for cur_lock_change in ip_lock_change:
            current_step = cur_lock_change['step']
            before_layers = ast.literal_eval(cur_lock_change['layers'].split(' -> ')[0])
            after_layers = ast.literal_eval(cur_lock_change['layers'].split(' -> ')[1])
            print before_layers
            print after_layers
            # === 对比，新增与减少 （锁定与解锁）
            lmode = DiffArray(after_layers, before_layers)
            add_lock_layers = lmode.get_list_added()
            unlock_layers = lmode.get_list_remove()
            if len(add_lock_layers) > 0:
                lock_add.append({'layers': add_lock_layers, 'step': current_step})
            if len(unlock_layers) > 0:
                unlock.append({'layers': unlock_layers, 'step': current_step})
        return lock_add, unlock

    def write_file(self, job_lock, desfile='job_lock.json'):
        """
        用json把参数字典直接写入user文件夹中的job_lock.json
        json_str = json.dumps(self.parm)将字典dump成string的格式
        :return:
        :rtype:
        """
        # 将收集到的数据以json的格式写入user/param
        stat_file = os.path.join(self.userDir, desfile)
        fd = open(stat_file, 'w')
        json.dump(job_lock, fd, ensure_ascii=False, indent=4, separators=(', ', ': '), sort_keys=True)
        fd.close()

    def read_file(self, sour_file='job_lock.json'):
        """
        用json从user文件夹中的job_lock.json中读取字典
        :return:
        :rtype:
        """
        json_dict = {}
        # print 'x' * 40
        # print self.userDir
        # print sour_file

        stat_file = os.path.join(self.userDir, sour_file)
        if os.path.exists(stat_file):
            fd = open(stat_file, 'r')
            json_dict = json.load(fd, encoding='utf8')
            fd.close()

        conver_dict = unicode_convert(json_dict)
        return conver_dict


class DiffDict(object):
    """获取两个dict的差异"""

    def __init__(self, current, last):
        self.current = current
        self.last = last
        self.set_current = set(current)
        self.set_last = set(last)
        self.intersect_keys = self.set_current & self.set_last
        # print 'xxxxxxxxxxxxx', self.intersect_keys

    def get_added(self):
        """current - 交集 = 新增的key"""
        added_keys = self.set_current - self.intersect_keys
        return [{'step': key, 'layers': self.current.get(key)} for key in added_keys]

    def get_removed(self):
        """last - 交集 = 减去的key"""
        removed_keys = self.set_last - self.intersect_keys
        return [{'step': key, 'layers': self.last.get(key)} for key in removed_keys
                if key not in ["lock_panelization_status", "unlock_panelization_status"]]

    def get_changed(self):
        """用交集中的key去两个dict中找出值不相等的"""
        changed_keys = set(o for o in self.intersect_keys if self.current.get(o) != self.last.get(o))
        return [{
            'step': key,
            'layers': '%s -> %s' % (self.last.get(key), self.current.get(key))
        } for key in changed_keys]


class DiffArray(object):
    """两个列表，求增加减少"""

    def __init__(self, current, last):
        self.current_list = current
        self.last_list = last
        # === 以下，在转换为set模式时，保持排序
        self.set_current_list = set(self.current_list)
        self.set_last_list = set(self.last_list)
        self.intersect_items = self.set_current_list.intersection(self.set_last_list)

    def get_list_added(self):
        return sorted(list(self.set_current_list - self.intersect_items), key=lambda x: self.current_list.index(x))

    def get_list_remove(self):
        return sorted(list(self.set_last_list - self.intersect_items), key=lambda x: self.last_list.index(x))


# # # # --程序入口
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = CheckUserOpenJob()
