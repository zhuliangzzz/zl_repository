#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
if sys.platform == "win32":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package")
else:
    scriptPath = "%s/scripts" % os.environ.get('SCRIPTS_DIR', '/incam/server/site_data')
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")


from genesisPackages import job
from create_ui_model import showMessageInfo


step_list = job.getSteps()
panel_list = [s for s in step_list if 'panel' in s]
if panel_list:
    showMessageInfo(u"此程序仅用于输出不含panel拼版的非正式TGZ(确认工作稿，或其它临时用途)")
    sys.exit()

# 输出前检测是否保存
ischange = job.DO_INFO('-t job -e %s -m script -d IS_CHANGED' % job.name)
if ischange['gIS_CHANGED'] == 'yes':
    showMessageInfo(u"请保存资料后再运行程序")
    sys.exit(0)

tgz_path = os.path.join(r'/id/workfile/hdi_film', job.name, 'informal')
if not os.path.isdir(tgz_path):
    os.makedirs(tgz_path)


# job.COM("export_job,job={0},path={1},mode=tar_gzip,submode=full,overwrite=yes".format(job.name, tgz_path))
os.system("python /incam/server/site_data/scripts/sh_script/zl/output/Export_Job.py %s %s" % (job.name,tgz_path))
showMessageInfo(u"tgz已输出，路径：{0}".format(tgz_path))

