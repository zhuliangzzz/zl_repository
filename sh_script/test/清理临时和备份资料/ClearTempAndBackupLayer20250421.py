#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:ClearTempAndBackupLayer.py
   @author:zl
   @time: 2025/1/24 15:36
   @software:PyCharm
   @desc:
   清除临时层-ls和备份层-bf   10天前
   20250207 把不存在的层的锁信息去除
   20250211 优化旋转拼版的料号和跳过ODB格式的料号
"""
import copy
import json
import os
import re
import sys
import tarfile
import platform
import time

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

import MySQL_DB
import GetData
import genClasses_zl as gen


class ClearTempAndBackupLayer(object):
    def __init__(self):
        self.db1 = '/data2/incamp_db1/jobs'
        self.back_path = '/data3/backup_linshi_jobs'
        self.term = 10  # 期限：天
        self.suffix = time.strftime('_%Y%m%d%H%M%S')
        self.logfile = os.path.join(self.back_path, '%s.txt' % jobname)
        if jobname not in gen.Top().listJobs():
            with open(self.logfile, 'a') as writer:
                writer.write('[%s]Job does not exist: %s\n' % (
                time.strftime('%Y-%m-%d %H:%M:%S'), jobname))
            sys.exit(-1)
        self.job = gen.Job(jobname)
        self.panel_surface_layer = 'inner_panel_surface'  # 去细丝保留的铜皮层
        self.getDATA = GetData.Data()
        # PRODUCT = os.environ.get('INCAM_PRODUCT', None)
        if platform.system() == "Windows":
            self.userDir = "%s/fw/jobs/%s/user" % (os.environ.get('GENESIS_DIR', 'D:/genesis'), jobname)
        else:
            self.userDir = os.environ.get('JOB_USER_DIR', None)
            if not self.userDir:
                self.userDir = "%s/user" % self.job.dbpath
        print(self.userDir)
        self.job_lock = os.path.join(self.userDir, '%s_job_lock.json' % jobname)
        # self.lock_info = self.getJOB_LockInfo(dataType='locked_info')
        self.job_make_info = self.getJOB_LockInfo(dataType='job_make_status')
        self.ignore_keys = ['lock_panelization_status', 'unlock_panelization_status']   # job_lock字典中不需要找的key
        self.flipList = []
        self.run()

    def run(self):
        self.job.COM('check_inout,mode=test,type=job,job=' + self.job.name)
        if 'yes' in self.job.COMANS:  # check out了 无法操作
            # print("Job already open, not opening")
            check_user = self.job.COMANS.split()[1]
            with open(self.logfile, 'a') as writer:
                writer.write('[%s]Job already open&check out by %s: %s\n' % (
                time.strftime('%Y-%m-%d %H:%M:%S'), check_user, jobname))
            sys.exit(-1)
        os.chdir(self.db1)
        self.tar_tgz(jobname)
        self.job.open(1)
        if 'panel' in self.job.stepsList:
            self.flipStepName('panel')
        self.rows = self.job.matrix.returnRows()  # 当前料号中的所有层
        if 'edit' in self.job.stepsList:
            stepname = 'edit'
        elif 'orig' in self.job.stepsList:
            stepname = 'orig'
        else:
            stepname = self.job.stepsList[0]
        step = gen.Step(self.job, stepname)
        step.open()
        if self.flipList:
            self.job.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=yes' % jobname)
        # 20250218 zl 先还原正式层
        os.system("python /incam/server/site_data/scripts/sh_script/zl/check/TempLayerCheck.py %s restore_normal" % jobname)
        for lyr in lyrs:
            self.job.VOF()
            self.job.matrix.deleteRow(lyr)
            self.job.VON()
        if self.flipList:
            self.job.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=no' % jobname)
        self.job.save()
        # self.job.VOF()
        self.job.close(1)  # 有人open了，可以成功清理和保存 忽略被open提示  open的人重新open
        # self.job.VON()
        with open(self.logfile, 'a') as writer:
            writer.write('[%s]Removed layer: %s\n' % (jobname + self.suffix + '.tgz', ' '.join(lyrs)))
        # 更新料号锁信息
        self.update_lock_info()
        sys.exit(0)

    def tar_tgz(self, jobname):
        if not os.path.exists(os.path.join(self.db1, jobname)):
            sys.exit(-1)
        if not os.path.exists(self.back_path):
            os.makedirs(self.back_path)
        output_file = os.path.join(self.back_path, jobname + self.suffix + '.tgz')
        try:
            tar = tarfile.open(output_file, "w:gz")
            for root, dirs, files in os.walk(jobname):
                for file in files:
                    file_path = os.path.join(root, file)
                    tar.add(file_path)
            tar.close()
        except IOError as e:
            os.chmod(e.filename, 0o664)
            self.tar_tgz(jobname)

    # 更新锁状态
    def update_lock_info(self):
        conn = MySQL_DB.MySQL()
        dbc_m = conn.MYSQL_CONNECT()
        self.pre_lock = None
        if len(jobname) == 13:
            self.pre_lock = self.getJOB_LockInfo(dataType='locked_info')
        if not self.pre_lock:
            self.pre_lock = self.read_file()
        update_not_exists_layers = []  # 不存在的层需要去掉锁信息
        for lock_step, lock_layers in self.pre_lock.items():
            if lock_step in self.ignore_keys:
                continue
            copy_lock_layers = copy.deepcopy(lock_layers)
            for lock_layer in copy_lock_layers:
                if lock_layer == self.panel_surface_layer:  # 20241204 zl 排除去细丝所保存的铜皮层
                    continue
                if lock_layer in lyrs:  # 20250207 去除临时层的锁信息和不存在的层的锁信息
                    lock_layers.remove(lock_layer)
                if lock_layer not in self.rows:
                    update_not_exists_layers.append(lock_layer)
                    lock_layers.remove(lock_layer)
        if update_not_exists_layers:  # 锁住的层信息中删除掉不存在的层
            with open(self.logfile, 'a') as writer:
                writer.write('[%s]Lock delete layer: %s\n' % (jobname + self.suffix + '.tgz', ' '.join(update_not_exists_layers)))
        # 记录状态
        status_file = os.path.join(self.userDir, 'cam_finish_status_{0}.log'.format(jobname))
        with open(status_file, 'w') as file_obj:
            json.dump(self.job_make_info, file_obj)
        try:
            sql = u"update hdi_engineering.job_lock_data  set job_make_status=%s,locked_info=%s where job_name = '{0}'".format(jobname.split("-")[0])
            conn.SQL_EXECUTE(dbc_m, sql, (json.dumps(self.job_make_info, ensure_ascii=False), json.dumps(self.pre_lock)))
        except Exception as e:
            with open(self.logfile, 'a') as writer:
                writer.write('[%s] Exception: %s (%s)\n' % (jobname + self.suffix + '.tgz', e, ' '.join(lyrs)))
        finally:
            conn.DB_CLOSE(dbc_m)
        # lock_info = self.getJOB_LockInfo()
        self.write_file()

    def write_file(self):
        """
        用json把参数字典直接写入user文件夹中的job_lock.json
        json_str = json.dumps(self.parm)将字典dump成string的格式
        :return:
        :rtype:
        """
        # 将收集到的数据以json的格式写入user/param
        # stat_file = os.path.join(self.userDir, desfile)
        fd = open(self.job_lock, 'w')
        json.dump(self.pre_lock, fd, ensure_ascii=False, indent=4, separators=(', ', ': '), sort_keys=True)
        fd.close()

    def read_file(self):
        """
        用json从user文件夹中的job_lock.json中读取字典
        :return:
        :rtype:
        """
        json_dict = {}
        if os.path.exists(self.job_lock):
            fd = open(self.job_lock, 'r')
            json_dict = json.load(fd)
            fd.close()
        return json_dict

    def getJOB_LockInfo(self, dataType='locked_info'):
        """
        从数据库中获取料号的锁记录
        :param dataType: 获取的数据类型（status:locked_info log:locked_log）
        :return:dict
        """

        lockData = self.getDATA.getLock_Info(self.job.name.split("-")[0])

        try:
            return json.loads(lockData[dataType].replace("\r", ""), encoding='utf8')
        except:
            # print u'传入的数据参数异常'
            return {}

    def flipStepName(self, step):
        """
        递归寻找出有镜像的step，并append到 flipList数组中
        :param step: step名
        :return: None
        """
        info = self.job.DO_INFO('-t step -e %s/%s -m script -d SR -p flip+step' % (jobname, step))
        step_flip_tuple = [(info['gSRstep'][i], info['gSRflip'][i]) for i in range(len(info['gSRstep']))]
        step_flip_tuple = list(set(step_flip_tuple))
        for (stepName, flip_yn) in step_flip_tuple:
            if flip_yn == 'yes':
                self.flipList.append(stepName)
            elif flip_yn == 'no':
                self.flipStepName(stepName)


if __name__ == '__main__':
    jobname = sys.argv[1]
    lyrs = sys.argv[2:]
    ClearTempAndBackupLayer()
