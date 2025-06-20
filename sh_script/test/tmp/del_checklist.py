#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --加载相对位置，以实现InCAM与Genesis共用

import os
import platform
import sys
if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package_HDI")
    sys.path.append(r"D:/pyproject/Package")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
import gClasses


if __name__ == '__main__':
    jobName = os.environ.get("JOB")
    job_cmd = gClasses.Job(jobName)
    for s in job_cmd.getSteps():
        step = gClasses.Step(job_cmd, s)
        info_checklist = job_cmd.DO_INFO("-t step -e %s/%s -d CHECKS_LIST" % (jobName, s))['gCHECKS_LIST']
        if info_checklist:
            step.open()
            for check in info_checklist:
                step.COM("chklist_delete,chklist={0}".format(check))
    job_cmd.COM('save_job,job=%s,override=no' % jobName)






