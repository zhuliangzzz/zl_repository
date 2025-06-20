#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:modifyFile.py
   @author:zl
   @time: 2025/1/21 14:05
   @software:PyCharm
   @desc:
   # 更改脚本内容 路径'/workfile/film' 改为 ‘/workfile/hdi_film/'
"""
import datetime
import json
import os.path
import platform
import sys
import threading
import codecs
from Queue import Queue
if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
from TOPCAM_IKM import IKM


class ModifyFile():
    def __init__(self):
        self.num_threads = 10
        self.file_list = []
        # 创建队列和线程
        self.queue = Queue()
        self.ikm_fun = IKM()
        self.logs, self.log = {}, []
        self.search_word = '/workfile/film'
        self.replace_word = '/workfile/hdi_film/'
        # log
        self.log_file = '/windows/174.db/modify_film_log.txt'
        self.run()

    def run(self):
        threads = []
        # 启动线程池
        for _ in range(self.num_threads):
            t = threading.Thread(target=self.worker, args=(self.queue,))
            t.start()
            threads.append(t)
        sql = 'select script_parameter from pdm_workprocess'
        data_info = self.ikm_fun.PG.SELECT_DIC(self.ikm_fun.dbc_p, sql)
        scripts = []
        if data_info:
            # i = 0
            for data in data_info:
                # print(data["script_parameter"], type(data["script_parameter"]))
                file_path = json.loads(data["script_parameter"]).get('source_script_incam')
                # print(file_path)
                if file_path and file_path.strip():
                    if file_path not in scripts:
                        scripts.append(file_path)
                    # i += 1
                    # if i > 1:
                    #     break
        self.log.append(u'开始替换路径... %s' % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        # 测试10个
        # i = 0
        for script in scripts:
            # if i > 20:
            #     break
            # print(script)
            self.queue.put(script)
            # i += 1
        # self.queue.put('/frontline/incam/server/site_data/scripts/sh_script/jin_xin/jinxin_tgz_zltest.py')


        # 等待所有任务完成
        self.queue.join()

        # 等待所有线程完成
        for i in range(self.num_threads):
            self.queue.put(None)
        for t in threads:
            t.join()

        # logfile = os.path.join(, '')
        # if not os.path.exists('/windows/174.file/HDI_INCMAPRO_JOB_DB'):
        #     os.makedirs('/windows/174.file/HDI_INCMAPRO_JOB_DB')
        for key in self.logs.keys():
            self.log.append(key)
            self.log.extend(self.logs.get(key))
        self.log.append(u"本次替换完成 %s" % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        with codecs.open(self.log_file, 'a', 'utf-8') as w:
            w.write("\n".join(self.log) + '\n')

    # 线程池中的工作函数
    def worker(self, q):
        while True:
            folder_path = q.get()
            if folder_path is None:
                break
            try:
                self.modify(folder_path)
            finally:
                q.task_done()

    def modify(self, file):
        if os.path.isfile(file):
            dir_path = file.rsplit('/', 1)[0]
            filename = os.path.basename(file)
            if '.' in filename:
                back_file = os.path.join(dir_path, filename.replace('.', '_modify_back.'))
                tmp_filename = os.path.join(dir_path, filename.replace('.', '_modify_tmp.'))
            else:
                back_file = os.path.join(dir_path, filename + '_modify_back.')
                tmp_filename = os.path.join(dir_path, filename + '_modify_tmp.')
            if os.path.exists(back_file):
                return
            with open(file) as f1:
                with open(back_file, 'w') as f2:
                    for num, line in enumerate(f1):
                        if self.search_word in line:
                            new_line = line.replace(self.search_word, self.replace_word)
                            f2.write(new_line)
                            if file not in self.logs.keys():
                                self.logs[file] = []
                            self.logs[file].append(u'%s: %s' % (num + 1, line.strip()))
                        else:
                            f2.write(line)
            if file in self.logs.keys():
                os.rename(file, tmp_filename)
                os.rename(back_file, file)
                os.rename(tmp_filename, back_file)
            else:
                os.unlink(back_file)
        else:
            self.log.append(u'文件%s不存在' % file)

if __name__ == '__main__':
    ModifyFile()
