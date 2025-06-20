#!/bin/csh -f

#set echo
set NeoScr = "$INCAM_SITE_DATA_DIR/scripts/sh_script"
set INCAM_SCRIPT = "$INCAM_SITE_DATA_DIR/scripts"

set RunParameters = `echo $* \
| sed 's#$NeoScr#'"$NeoScr#g" \
| sed 's#$INCAM_SCRIPT#'"$INCAM_SCRIPT#g" \
| sed 's#$INCAM_SITE_DATA_DIR#'"$INCAM_SITE_DATA_DIR#g"  \
| sed 's#$INCAM_SERVER#'"$INCAM_SERVER#g" \
| sed 's#$INCAM_LOCAL_DIR#'"$INCAM_LOCAL_DIR#g" \
| sed 's#$INCAM_USER_DIR#'"$INCAM_USER_DIR#g" \
 `
if ( ! -e /tmp/pid ) then
	mkdir /tmp/pid
endif
echo $JOB
rm -rf /tmp/pid/genesis_pid_$JOB*
COM save_log_file,dir=/tmp/pid,prefix=genesis_pid_$JOB,clear=no
cd /tmp/pid
set pid=`ls | grep $JOB | cut -d "." -f 4`
if ( $pid != '' ) then
#此处设置当前pid 后续程序锁定此pid
	setenv CURRENTPIDNUM $pid
endif
rm -rf /tmp/pid/genesis_pid_$JOB*
setenv STEP edit
$NeoScr/SilkScreen/./SilkScreenOnePackageService_zltest.cshrc ShowSub=Pre

echo "RunScript=$RunParameters"




