#! /bin/csh

# -->清理IncamPro数据库 -->备份并清理4天前的JOB(备份到/data3/incampro/db_management/abnormal_jobs #删除Inmcapro在线料号)
#### InCAMPRO database clean
#### backup 4 days ago abnormal jobs to $rootPath and delete online job in InCAMPRO
#### write by hyp, Sep 20.2017
set timeRecordFile = '/data3/incampro/db_management/logs/time_record.log'
set cleanList = '/data3/incampro/db_management/logs/clean_list.log'

set timeStart = `date "+%F %H:%M:%S"`
echo "$timeStart incampro database clean start"
echo "start: $timeStart" >> $timeRecordFile

set recover = 0;
if ( $recover == 1 ) then
    COM recover_lost_jobs
endif

#set backupPath = "/data3/incampro/db_management/abnormal_jobs";

set outFile = "/tmp/incampro/incam_tmp.$$"
alias DO_INFO_MM "COM info, out_file=$outFile, units=mm, angle_direction=ccw,args= \!:*; source $outFile; rm -f $outFile"
alias dbutil /incampro/release/bin/dbutil

set dbRootPath = '/incampro/incamp_db1/jobs';
set deleteJobLogFile = '';

set rootPath = "/data3/incampro/db_management/abnormal_jobs"
set normalJobsRootPath = "/data3/incampro/db_management/normal_jobs"

#  -->这里是获取什么？dbutil-->料号名？
set jobList = (`dbutil list jobs | awk -F ' ' '{print $1}'`)

#set jobList = ( `ls $dbRootPath` )
#\rm -f /tmp/hyp

set i = 1
set number = 1
foreach tmp ( $jobList )

    #if ( $i > 100 ) then
        #goto EndAndExit
    #endif
    set doRemove = "no"
    
    # -->什么意思？ 长度不等于13位?
    # -->等于13位则是正常料号
    if ( `expr length $tmp` != 13 ) then        ## abnormal jobs handling
        # -->/incampro/incam_db1/jobs/当前料号
        set tmpRootPath = "${dbRootPath}/${tmp}"

        # -->如果路径存在则为真
        if ( -d $tmpRootPath ) then
            set lastOpenFile = "$tmpRootPath/user/last_opentime"
            #  --> last_opentime == 2019-11-20 20:49:00 31740
            #  --> `cat $aa | cut -d ' ' -f3` -->以空格键分割$aa变量，取第三个字段
            
                # -->备份路径(上传数据库做记录) AresHe 2020.03.27
            set backupPath = "/data3/incampro/db_management/abnormal_jobs";
            
            # -->如果文件存在则为真
            if ( -f $lastOpenFile ) then            
                
                set lastOpenUser = `cat $lastOpenFile | cut  -d ' ' -f3`
                # --> $lastOpenUser = 31740 (-f3 第3段)
            
                set timeLastOpen = `cat $lastOpenFile | cut  -d ' ' -f1`
                # --> $lastOpenUser = 201-11-20 (-f1 第1段)
                
                set timeLastOpenTime = `cat $lastOpenFile | cut  -d ' ' -f2`
                # --> $lastOpenUser = 20:49:00 (-f2 第2段)
                
                # -->$tmp用双引号引起，因为在shell语法中如果$tmp变量中带有"-"会引起if等判断语法错误.
                if ( "$tmp" =~ *mi ) then
                    # 1、获取明天的日期：date -d next-day +%Y%m%d。
                    # 2、获取昨天的日期：date -d last-day +%Y%m%d。
                    # 3、获取上个月的年和月：date -d last-month +%Y%m。
                    # 4、获取下个月的年和月：date -d next-month +%Y%m。
                    # 5、获取明年的年份：date -d next-year +%Y。
                    # 获取今天时期：`date +%Y%m%d` 或 `date +%F` 或 $(date +%y%m%d)
                    
                    set _DayAgoTime = `date -d "-30 day" "+%F"`
                    # -->获取30天前时间
                else
                    # -->获取4天前时间
                    set _DayAgoTime = `date -d "-4 day" "+%F"`
                endif
            
                set timeLastOpenSeconds = `date -d "$timeLastOpen" "+%s"`    ## seconds since 1970-01-01 00:00:00 UTC  
                set _DayAgoTimeSeconds = `date -d "$_DayAgoTime" "+%s"`    ## seconds since 1970-01-01 00:00:00 UTC  
                
                # -->最后打开时间<=以前现在时间对比
                # -->   2019-11-20 <= 2019-11-16 || 2019-11-20 <= 2019-10-20(*mi)
                if ( $timeLastOpenSeconds <= $_DayAgoTimeSeconds ) then
                    set doRemove = "yes"
                endif
                
                # --> 2019-11-20 20:49:00
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
            
            if ( "$tmp" == 'output-laser-lot' ) then
            # === Song 2021.03.02 输出laser lot的基准料号，目前测试阶段，此程序不删除处理 === 
                set doRemove = "no"
            endif
            
            if ( $doRemove == "yes" ) then
            
                # -->这是什么意思?什么命令?
                set checkInOut = `dbutil lock test $tmp | cut -d ' ' -f1`
                if ( $checkInOut == 'no' ) then
                    
                    # -->切换路径 /incampro/incam_db1/jobs/当前料号
                    cd $tmpRootPath 
                    # -->切换路径 /incampro/incam_db1/jobs
                    cd .. 
                    # -->打包当前料号
                    \tar -zcf $rootPath/${tmp}.tgz $tmp
                    
                    if ( $? != 0 ) then     ## false, tar failed
                        # -->当$?不返还0时，打包失败?
                        \rm -f $rootPath/${tmp}.tgz
                    else     ## true, tar successfully
                        VOF
                            # -->删除Incam下的当前料号TGZ
                            COM delete_entity,job=$tmp,name=$tmp,type=job
                        VON
                        if ( $STATUS == 0 ) then
                            # -->$STATUS返回0程序执行成功?
                            @ number++
                            # -->date %F 完整日期格式，等价于 %Y-%m-%d
                            set timeNow = `date "+%F|%H:%M:%S"`
                            echo "$tmp" "$timeNow" "$lastOpenUser" "$lastOpenTime" "$backupPath" "$remarkContext" >> $cleanList
                            # -->将信息写入到/data3/incampro/db_management/logs/clean_list.log
                        else
                            \rm -f $rootPath/${tmp}.tgz
                            # -->删除当前料号
                        endif
                    endif
                endif
            endif
        endif
        @ i++
    else        ## normal jobs handling(正常料号-->13位)
        set tmpRootPath = "${dbRootPath}/${tmp}"
        # -->/incampro/incam_db1/jobs/当前料号
        if ( -d $tmpRootPath ) then
            set lastOpenFile = "$tmpRootPath/user/last_opentime"
            # -->/incampro/incam_db1/jobs/当前料号/user/last_opentime"
            
                # -->备份路径(上传数据库做记录) AresHe 2020.03.27
            set backupPath = "/data3/incampro/db_management/normal_jobs";
            
            #  --> last_opentime == 2019-11-20 20:49:00 31740
            #  --> `cat $aa | cut -d ' ' -f3` -->以空格键分割$aa变量，取第三个字段
            if ( -f $lastOpenFile ) then
                set lastOpenUser = `cat $lastOpenFile | cut  -d ' ' -f3`
                # --> $lastOpenUser = 31740 (-f3 第3段)
            
                set timeLastOpen = `cat $lastOpenFile | cut  -d ' ' -f1`
                # --> $lastOpenUser = 201-11-20 (-f1 第1段)
                
                set timeLastOpenTime = `cat $lastOpenFile | cut  -d ' ' -f2`
                # --> $lastOpenUser = 20:49:00 (-f2 第2段)
                
                set _DayAgoTime = `date -d "-30 day" "+%F"`
                # -->获取30天前时间
            
                set timeLastOpenSeconds = `date -d "$timeLastOpen" "+%s"`    ## seconds since 1970-01-01 00:00:00 UTC  
                set _DayAgoTimeSeconds = `date -d "$_DayAgoTime" "+%s"`    ## seconds since 1970-01-01 00:00:00 UTC  
                
                # -->最后打开时间<=以前现在时间对比
                # -->2019-11-20 <= 2019-10-20(正常料号)
                if ( $timeLastOpenSeconds <= $_DayAgoTimeSeconds ) set doRemove = "yes"
                
                # --> 2019-11-20 20:49:00
                set lastOpenTime = "${timeLastOpen}|$timeLastOpenTime"
                set remarkContext = "null"
            else
                #set doRemove = "no"	#-->AresHe 20191126
                set doRemove = "yes"  
                set lastOpenUser = 'null'
                set timeLastOpen = 'null'
                set timeLastOpenTime = 'null'
                set lastOpenTime = "null"
                set remarkContext = "No|last|open|file."                
            endif
            
            if ( $doRemove == "yes" ) then
                # -->这是什么意思?什么命令?
                set checkInOut = `dbutil lock test $tmp | cut -d ' ' -f1`
                if ( $checkInOut == 'no' ) then
                
                    # -->切换路径 /incampro/incam_db1/jobs/当前料号
                    cd $tmpRootPath
                    
                    # -->切换路径 /incampro/incam_db1/jobs
                    cd ..
                    
                    # -->打包当前料号
                    \tar -zcf $normalJobsRootPath/${tmp}.tgz $tmp
                    
                    if ( $? != 0 ) then     ## false, tar failed
                        # -->当$?不返还0时，打包失败?
                        \rm -f $rootPath/${tmp}.tgz
                    else     ## true, tar successfully
                        VOF
                            # -->删除Incam下的当前料号TGZ
                            COM delete_entity,job=$tmp,name=$tmp,type=job
                        VON
                        if ( $STATUS == 0 ) then
                        
                            # -->$STATUS返回0程序执行成功?
                            @ number++
                            # -->date %F 完整日期格式，等价于 %Y-%m-%d
                            set timeNow = `date "+%F|%H:%M:%S"`
                            
                            echo "$tmp" "$timeNow" "$lastOpenUser" "$lastOpenTime" "$backupPath" "$remarkContext" >> $cleanList
                            # -->将信息写入到/data3/incampro/db_management/logs/clean_list.log
                        else
                            \rm -f $rootPath/${tmp}.tgz
                            # -->删除当前料号
                        endif
                    endif
                endif
            endif
        endif
        @ i++
    endif
end


EndAndExit:  # -->这个命令是结束退出?

# -->perl脚本链数据库，后面部分是什么? /data3/incampro/db_management/logs/clean_list.log -->打开这个文件?
perl /incampro/server/site_data/scripts/db_management/incamp_connect_to_mysql.pl /data3/incampro/db_management/logs/clean_list.log

# -->结束时间
set timeEnd = `date "+%F %H:%M:%S"`
echo "$timeEnd incam database clean end $i"  # --> $i什么意思? 不是1?  -->只echo到终端面板上显示?

echo "end ${number} : $timeEnd" >> $timeRecordFile
echo "=====================" >> $timeRecordFile













