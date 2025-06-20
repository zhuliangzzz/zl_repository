#! /bin/csh


#set rv = `perl /incam/server/site_data/scripts/db_management/tipsToCheckJoblist.pl`
set rv = `java -jar /incam/server/site_data/scripts/db_management/JoblistCheckTips.jar`

if ( $rv =~ 'continue' ) /incam/$INCAM_RELEASE_VER_VGT/bin/dbutil check y



