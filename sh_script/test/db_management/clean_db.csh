#! /bin/csh
#### InCAM database clean
#### backup 4 days ago abnormal jobs to $rootPath and delete online job in InCAM
#### write by hyp, Sep 20.2017
#### modify by song 20190731 for change bakup path in hdi incam server from opt to /data3

#set timeRecordFile = '/opt/db_management/logs/time_record.log'
set timeRecordFile = '/data3/db_management/logs/time_record.log'
#set cleanList = '/opt/db_management/logs/clean_list.log'
set cleanList = '/data3/db_management/logs/clean_list.log'
set timeStart = `date "+%F %H:%M:%S"`
echo "$timeStart incam database clean start"
echo "start: $timeStart" >> $timeRecordFile

set recover = 0;
if ( $recover == 1 ) then
    COM recover_lost_jobs
endif

#set backupPath = "/data3/db_management/abnormal_jobs";

set outFile = "/tmp/incam_tmp.$$"
alias DO_INFO_MM "COM info, out_file=$outFile, units=mm, angle_direction=ccw,args= \!:*; source $outFile; rm -f $outFile"
alias dbutil /incam/release/bin/dbutil

set dbRootPath = '/incam/incam_db1/jobs';
set deleteJobLogFile = '';

# set rootPath = "/opt/db_management/abnormal_jobs"
set rootPath = "/data3/db_management/abnormal_jobs"
# set normalJobsRootPath = "/opt/db_management/normal_jobs"
set normalJobsRootPath = "/data3/db_management/normal_jobs"

set jobList = (`dbutil list jobs | awk -F ' ' '{print $1}'`)
#set jobList = ( `ls $dbRootPath` )
#\rm -f /tmp/hyp

set i = 1
set number = 1
foreach tmp ( $jobList )
    #if ( $i == 3000 ) then
        #goto EndAndExit
    #endif
    set doRemove = "no"
    if ( `expr length "$tmp"` != 13 ) then        ## abnormal jobs handling
        set tmpRootPath = "${dbRootPath}/${tmp}"
        if ( -d $tmpRootPath ) then
            set lastOpenFile = "$tmpRootPath/user/last_opentime"
            
                # -->备份路径(上传数据库做记录) AresHe 2020.03.27
            set backupPath = "/data3/db_management/abnormal_jobs";
            
            if ( -f $lastOpenFile ) then
                set lastOpenUser = `cat $lastOpenFile | cut  -d ' ' -f3`
            
                set timeLastOpen = `cat $lastOpenFile | cut  -d ' ' -f1`
                
                set timeLastOpenTime = `cat $lastOpenFile | cut  -d ' ' -f2`
                
                if ( "$tmp" =~ *mi ) then
#                    set _DayAgoTime = `date -d "-30 day" "+%F"` # edit by song 20200409
                    set _DayAgoTime = `date -d "-1 day" "+%F"`
                else
#                    set _DayAgoTime = `date -d "-4 day" "+%F"` # edit by song 20200409
                    set _DayAgoTime = `date -d "-1 day" "+%F"`
                endif
            
                set timeLastOpenSeconds = `date -d "$timeLastOpen" "+%s"`    ## seconds since 1970-01-01 00:00:00 UTC  
                set _DayAgoTimeSeconds = `date -d "$_DayAgoTime" "+%s"`    ## seconds since 1970-01-01 00:00:00 UTC  
            
                if ( $timeLastOpenSeconds <= $_DayAgoTimeSeconds ) then
                    set doRemove = "yes"
                endif
                
                set lastOpenTime = "${timeLastOpen}|$timeLastOpenTime"
                set remarkContext = "null"
            else
                set doRemove = "yes"
                set lastOpenUser = 'null'
                set timeLastOpen = 'null'
                set timeLastOpenTime = 'null'
                set lastOpenTime = "null"
                set remarkContext = "No|last|open|file."                
            endif
            
            if ( $doRemove == "yes" ) then
				VOF
					COM check_inout,mode=in,type=job,job=$tmp
					COM close_job,job=$tmp
					COM close_form,job=$tmp
					COM close_flow,job=$tmp
				VON
                set checkInOut = `dbutil lock test $tmp | cut -d ' ' -f1`
                if ( $checkInOut == 'no' ) then
                    cd $tmpRootPath
                    cd ..
                    \tar -zcf $rootPath/${tmp}.tgz $tmp
                    if ( $? != 0 ) then     ## false, tar failed
                        \rm -f $rootPath/${tmp}.tgz
                    else     ## true, tar successfully
                        VOF
                            COM delete_entity,job=$tmp,name=$tmp,type=job
                        VON
                        if ( $STATUS == 0 ) then
                            @ number++
                            set timeNow = `date "+%F|%H:%M:%S"`
                            
                            echo "$tmp" "$timeNow" "$lastOpenUser" "$lastOpenTime" "$backupPath" "$remarkContext" >> $cleanList
                        else
                            \rm -f $rootPath/${tmp}.tgz    
                        endif
                    endif
                endif
            endif
        endif
        @ i++
    else        ## normal jobs handling
        set tmpRootPath = "${dbRootPath}/${tmp}"
        if ( -d $tmpRootPath ) then
            set lastOpenFile = "$tmpRootPath/user/last_opentime"
            
                # -->备份路径(上传数据库做记录) AresHe 2020.03.27
            set backupPath = "/data3/db_management/normal_jobs";
            
            if ( -f $lastOpenFile ) then
                set lastOpenUser = `cat $lastOpenFile | cut  -d ' ' -f3`
            
                set timeLastOpen = `cat $lastOpenFile | cut  -d ' ' -f1`
                
                set timeLastOpenTime = `cat $lastOpenFile | cut  -d ' ' -f2`
                
#                set _DayAgoTime = `date -d "-30 day" "+%F"`
                set _DayAgoTime = `date -d "-1 day" "+%F"`
                set timeLastOpenSeconds = `date -d "$timeLastOpen" "+%s"`    ## seconds since 1970-01-01 00:00:00 UTC  
                set _DayAgoTimeSeconds = `date -d "$_DayAgoTime" "+%s"`    ## seconds since 1970-01-01 00:00:00 UTC  
            
                if ( $timeLastOpenSeconds <= $_DayAgoTimeSeconds ) set doRemove = "yes"
                    
                set lastOpenTime = "${timeLastOpen}|$timeLastOpenTime"
                set remarkContext = "null"
            else
                set doRemove = "yes"
                set lastOpenUser = 'null'
                set timeLastOpen = 'null'
                set timeLastOpenTime = 'null'
                set lastOpenTime = "null"
                set remarkContext = "No|last|open|file."                
            endif
            
            if ( $doRemove == "yes" ) then
                set checkInOut = `dbutil lock test $tmp | cut -d ' ' -f1`
                if ( $checkInOut == 'no' ) then
                    cd $tmpRootPath
                    cd ..
                    \tar -zcf $normalJobsRootPath/${tmp}.tgz $tmp
                    if ( $? != 0 ) then     ## false, tar failed
                        \rm -f $rootPath/${tmp}.tgz
                    else     ## true, tar successfully
                        VOF
                            COM delete_entity,job=$tmp,name=$tmp,type=job
                        VON
                        if ( $STATUS == 0 ) then
                            @ number++
                            set timeNow = `date "+%F|%H:%M:%S"`
                            
                            echo "$tmp" "$timeNow" "$lastOpenUser" "$lastOpenTime" "$backupPath" "$remarkContext" >> $cleanList
                        else
                            \rm -f $rootPath/${tmp}.tgz    
                        endif
                    endif
                endif
            endif
        endif
        @ i++
    endif
end

EndAndExit:

perl /incam/server/site_data/scripts/db_management/connect_to_mysql.pl /data3/db_management/logs/clean_list.log

set timeEnd = `date "+%F %H:%M:%S"`
echo "$timeEnd incam database clean end $i"

echo "end ${number} : $timeEnd" >> $timeRecordFile
echo "=====================" >> $timeRecordFile













