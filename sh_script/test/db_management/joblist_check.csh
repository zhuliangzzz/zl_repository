#! /bin/csh


#set rv = `perl /incam/server/site_data/scripts/db_management/tipsToCheckJoblist.pl`
set rv = `java -jar /incam/server/site_data/scripts/db_management/JoblistCheckTips.jar`

if ( $rv =~ 'continue' ) then
	#/incam/$INCAM_RELEASE_VER_VGT/bin/dbutil check y

	set DbutilPath = "/incam/$INCAM_RELEASE_VER_VGT/bin/dbutil"
	set DateTime = `date "+%Y-%m-%d %H:%M:%S"`
	set HostName = `hostname`
	set FixLogsPath = "/incam/server/site_data/scripts/Logs/Fix"
	set FixLogsFile = "$FixLogsPath/external_joblist_fix.log"

	echo "$DateTime $HostName" >> $FixLogsFile
	#
	set tFile = "/tmp/tFile$$.log"
	$DbutilPath check y >& $tFile
	cat $tFile
	cat $tFile | grep -v 'Checking' | grep -v 'lock' | grep -v 'Lock' >> $FixLogsFile
	\rm -rf $tFile
	#
	echo "" >> $FixLogsFile

endif





