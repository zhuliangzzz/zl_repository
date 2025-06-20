#!/bin/csh
# 20250212 zl 判断文件执行oepnvnc30任务
setenv SHELL /bin/csh

set pid = ` ps -ef | grep Xvnc | grep :30 | grep -v grep | awk '{ print $2 }'`
if (-e "/tmp/openvnc30.log") then
    if ("$pid" == "") then
        /usr/bin/vncserver :30 -geometry 1920x1080 -depth 24 -AlwaysShared
        rm -rf "/tmp/openvnc30.log"
    endif
endif

if (-e "/tmp/bak_job.log") then
	setenv DISPLAY :30.0
	python /incam/server/site_data/scripts/sh_script/autoScheduleTask/autoScheduleTaskForVGT.py auto_bak_incampro_jobs
	rm -rf "/tmp/bak_job.log"
endif

if (-e "/tmp/delete_linshi_layer_bak_job.log") then
	setenv DISPLAY :30.0
	python /incam/server/site_data/scripts/sh_script/autoScheduleTask/autoScheduleTaskForVGT.py auto_bak_linshi_incampro_jobs
	rm -rf "/tmp/delete_linshi_layer_bak_job.log"
endif

exit 
