#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys,os,re,time
import socket
import getpass
import subprocess as sub
from genCOM_26 import Genesis,GEN_COM

jobName = os.environ.get('JOB',None)
stepName = os.environ.get('STEP',None)
GENESIS_EDIR = os.environ.get('GENESIS_EDIR',None)
GENESIS_TMP  = os.environ.get('GENESIS_TMP',None)

class Gateway(Genesis,GEN_COM):
    def __init__(self):
        Genesis.__init__(self)
        GEN_COM.__init__(self)
        self.display = os.environ.get('DISPLAY','').split(':')[0]
        self.host = socket.gethostname().split('.')[0]
        self.user = getpass.getuser()
        self.gw_exe = os.path.join(GENESIS_EDIR,'misc','gateway')
        self.pipe = None
        self.pid_num = None
        self.pid_check_address = None
        self.COMANS = ''
        self.STATUS = 0
        tmp = 'gen_' + '.' + `time.time()`
        if os.environ.has_key('GENESIS_TMP'):
            self.tmpfile = os.path.join(os.environ['GENESIS_TMP'], tmp)
        else:
            self.tmpfile = os.path.join('/tmp', tmp)

    def genesis_connect(self):
        # 通过os.popen执行linux命令并获取genesis窗口信息
        self.getline = os.popen('ps -elf | grep "Engineering Toolkit').read().strip()
        # 通过re.split获取窗口pid
        self.pid = re.split(r'\t| |\n|\(|\)',self.getline)[-2].split(r'pid:')[-1]
        # 通过genesis gateway命令连结pid进行会话
        self.connect(self.pid_address(self.pid))
        # 获取与当前pid相关的log-genesis文件名
        tmp_files = os.listdir(r'c:/tmp')
        log_file = None
        for file in tmp_files:
            if file.endswith('.%s' % self.pid) and file.startswith('%s' % 'log-genesis'):
                log_file = os.path.join(r'c:/tmp',file)
        # 从log-genesis文件中查找料号名
        self.job_name = os.environ.get('JOB', None)
        grep_list = os.popen('grep "jobs" %s' % log_file).readlines()
        # 从文件尾开始查找，这样不容易get到错误的料号名
        grep_list.reverse()
        for line in grep_list:
            if 'jobs' in line:
                getline = line.split('/')
                idx = getline.index('jobs') + 1
                self.job_name = getline[idx]
                break

    #清除gateway连接
    def __del__(self):
        self.disconnect()

    #用subprocess向标准输入写进数据,然后再读取标准输出的数据
    def __in_out(self, command):
        self.pipe.stdin.write('%s\n' % command)
        return self.pipe.stdout.readline().strip()

    #用subprocess读取命令执行结果
    def __out(self, command):
        pipe = sub.Popen([self.gw_exe, command], stdout=sub.PIPE)
        stdout = pipe.stdout.read()
        pipe.wait()
        pipe.stdout.close()
        return stdout

    #清除进程
    def cleanup(self):
        pid_list = self.PID( self.user_address())
        for ps_pid, ps_exe, ps_address in self.ps():
            address_pid = ps_address.lstrip('%').split('@')[0]
            if address_pid.isdigit():
                if not address_pid in pid_list:
                    os.kill(int(ps_pid), 9)

    #获取与gateway相关的进程
    def ps(self):
        ps_list = []
        if sys.platform[:3] == 'win':
            for line in os.popen('wmic process where caption="gateway.exe" get pid ,commandline'):
                print line
            return ps_list
        else:
            for line in os.popen('ps -ef'):
                split_line = line.strip().split(None, 7)
                print split_line
                uid = split_line[0]
                pid = split_line[1]
                cmd = split_line[7].split(None, 1)
                if uid == self.user:
                    if 'gateway' in cmd[0] and len(cmd) == 2:
                        exe, address = cmd
                        ps_list.append((pid, exe, address))
            return ps_list

    #%5236@HDI-GCBXTZ02,5236为PID
    def pid_address(self, pid):
        return '%%%s@%s' % (pid, self.host)

    #HDI-GCBXTZ02@HDI-GCBXTZ02.*
    def user_address(self):
        return '%s@%s.%s*' % (self.user, self.host, self.display)

    #执行gateway %5236@HDI-GCBXTZ02命令
    def connect(self, address):
        if address[0] == '%' and '@' in address:
            self.pid_num, host = address.lstrip('%').split('@',1)
            self.pid_check_address = '*@%s*' % host
            self.disconnect()
            edir = os.path.realpath('/proc/%s/exe'%self.pid_num).rstrip('/get/get')
            gw_exe = os.path.join(edir, 'misc','gateway')
            if os.path.isfile(gw_exe):
                exe = gw_exe
            else:
                exe = self.gw_exe
            self.pipe = sub.Popen([exe, address], stdin=sub.PIPE, stdout=sub.PIPE)
            self.tmpfile = '%s/gateway%s.info' % (GENESIS_TMP, self.pid_num)
        else:
            raise 'Invalid address format, must use format "%pid@host*", "user@host.display" not allowed.'

    #关闭连接
    def disconnect(self):
        if self.pipe:
            try:
                self.pipe.stdin.write('.\n')
            except IOError:
                pass
            self.pipe.wait()
            self.pipe.stdin.close()
            self.pipe.stdout.close()
            self.pipe = None
        self.cleanup()

    #执行gateway 'WHO *'命令，return为genesis@HDI-GCBXTZ02.HDI-GCBXTZ02
    def WHO(self, address='*'):
        if self.pipe:
            try:
                return self.__in_out('WHO %s' % address).split()
            except IOError:
                return self.__out('WHO %s' % address).split()
        else:
            return self.__out('WHO %s' % address).split()

    #执持gateway 'PID genesis@HDI-GCBXTZ'命令，return为pids(5236)
    def PID(self, address='*'):
        if self.pipe:
            try:
                return self.__in_out('PID %s' % address).split()
            except IOError:
                return self.__out('PID %s' % address).split()
        else:
            return self.__out('PID %s' % address).split()

    #gateway建立连接之后，执行command命令,并可获得COMANS和STATUS的值
    def COM(self, command):
        self.COMANS = ''
        self.STATUS = 0
        if self.pipe:
            try:
                if self.pid_num in self.PID(self.pid_check_address):
                    self.STATUS = int(self.__in_out('COM %s' % command))
                    self.COMANS = self.__in_out('COMANS')
                else:
                    self.STATUS = -4
            except IOError:
                self.STATUS = -3
        else:
            self.STATUS = -2
        return self.STATUS

    #用gateway执行DO_INFO命令
    def DO_INFO(self, args, units="mm"):
        if os.path.isfile(self.tmpfile):
            os.remove(self.tmpfile)
        self.COM('info,out_file=%s,write_mode=replace,units=%s,args=%s' % (self.tmpfile, units, args))
        # if os.path.isfile(self.tmpfile):
        lineList = open(self.tmpfile, 'r').readlines()
        os.unlink(self.tmpfile)
        infoDict = self.parseInfo(lineList)
        return infoDict
        # else:
        #     return {}

    #向genesis进程发送消息
    def MSG(self, address, message):
        os.system('%s %s "MSG %s"' % (self.gw_exe, address, message))

    #错误信息,gateway Err目前不起作用,但此处的ERR会返回一些有用的信息
    def ERR(self, num):
        int_num = int(num)
        if int_num > 0:
            if self.pipe:
                try:
                    return self.__in_out('ERR %s' % num).strip()
                except IOError:
                    return self.__out('ERR %s' % num).strip()
            else:
                return self.__out('ERR %s' % num).strip()
        elif int_num == 0:
            return ''
        else:
            if int_num == -1:
                return 'Invalid command'
            elif int_num == -2:
                return 'No connection'
            elif int_num == -3:
                return 'Lost connection'
            elif int_num == -4:
                return 'PID %s does not exist' % self.pid_num
            else:
                return 'Undefined error'

if __name__ == '__main__':
    g = Gateway()

