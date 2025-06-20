#! /bin/csh

# -->����IncamPro���ݿ� -->���ݲ�����4��ǰ��JOB(���ݵ�/data3/incampro/db_management/abnormal_jobs #ɾ��Inmcapro�����Ϻ�)
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

#  -->�����ǻ�ȡʲô��dbutil-->�Ϻ�����
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
    
    # -->ʲô��˼�� ���Ȳ�����13λ?
    # -->����13λ���������Ϻ�
    if ( `expr length $tmp` != 13 ) then        ## abnormal jobs handling
        # -->/incampro/incam_db1/jobs/��ǰ�Ϻ�
        set tmpRootPath = "${dbRootPath}/${tmp}"

        # -->���·��������Ϊ��
        if ( -d $tmpRootPath ) then
            set lastOpenFile = "$tmpRootPath/user/last_opentime"
            #  --> last_opentime == 2019-11-20 20:49:00 31740
            #  --> `cat $aa | cut -d ' ' -f3` -->�Կո���ָ�$aa������ȡ�������ֶ�
            
                # -->����·��(�ϴ����ݿ�����¼) AresHe 2020.03.27
            set backupPath = "/data3/incampro/db_management/abnormal_jobs";
            
            # -->����ļ�������Ϊ��
            if ( -f $lastOpenFile ) then            
                
                set lastOpenUser = `cat $lastOpenFile | cut  -d ' ' -f3`
                # --> $lastOpenUser = 31740 (-f3 ��3��)
            
                set timeLastOpen = `cat $lastOpenFile | cut  -d ' ' -f1`
                # --> $lastOpenUser = 201-11-20 (-f1 ��1��)
                
                set timeLastOpenTime = `cat $lastOpenFile | cut  -d ' ' -f2`
                # --> $lastOpenUser = 20:49:00 (-f2 ��2��)
                
                # -->$tmp��˫����������Ϊ��shell�﷨�����$tmp�����д���"-"������if���ж��﷨����.
                if ( "$tmp" =~ *mi ) then
                    # 1����ȡ��������ڣ�date -d next-day +%Y%m%d��
                    # 2����ȡ��������ڣ�date -d last-day +%Y%m%d��
                    # 3����ȡ�ϸ��µ�����£�date -d last-month +%Y%m��
                    # 4����ȡ�¸��µ�����£�date -d next-month +%Y%m��
                    # 5����ȡ�������ݣ�date -d next-year +%Y��
                    # ��ȡ����ʱ�ڣ�`date +%Y%m%d` �� `date +%F` �� $(date +%y%m%d)
                    
                    set _DayAgoTime = `date -d "-30 day" "+%F"`
                    # -->��ȡ30��ǰʱ��
                else
                    # -->��ȡ4��ǰʱ��
                    set _DayAgoTime = `date -d "-4 day" "+%F"`
                endif
            
                set timeLastOpenSeconds = `date -d "$timeLastOpen" "+%s"`    ## seconds since 1970-01-01 00:00:00 UTC  
                set _DayAgoTimeSeconds = `date -d "$_DayAgoTime" "+%s"`    ## seconds since 1970-01-01 00:00:00 UTC  
                
                # -->����ʱ��<=��ǰ����ʱ��Ա�
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
            # === Song 2021.03.02 ���laser lot�Ļ�׼�Ϻţ�Ŀǰ���Խ׶Σ��˳���ɾ������ === 
                set doRemove = "no"
            endif
            
            if ( $doRemove == "yes" ) then
            
                # -->����ʲô��˼?ʲô����?
                set checkInOut = `dbutil lock test $tmp | cut -d ' ' -f1`
                if ( $checkInOut == 'no' ) then
                    
                    # -->�л�·�� /incampro/incam_db1/jobs/��ǰ�Ϻ�
                    cd $tmpRootPath 
                    # -->�л�·�� /incampro/incam_db1/jobs
                    cd .. 
                    # -->�����ǰ�Ϻ�
                    \tar -zcf $rootPath/${tmp}.tgz $tmp
                    
                    if ( $? != 0 ) then     ## false, tar failed
                        # -->��$?������0ʱ�����ʧ��?
                        \rm -f $rootPath/${tmp}.tgz
                    else     ## true, tar successfully
                        VOF
                            # -->ɾ��Incam�µĵ�ǰ�Ϻ�TGZ
                            COM delete_entity,job=$tmp,name=$tmp,type=job
                        VON
                        if ( $STATUS == 0 ) then
                            # -->$STATUS����0����ִ�гɹ�?
                            @ number++
                            # -->date %F �������ڸ�ʽ���ȼ��� %Y-%m-%d
                            set timeNow = `date "+%F|%H:%M:%S"`
                            echo "$tmp" "$timeNow" "$lastOpenUser" "$lastOpenTime" "$backupPath" "$remarkContext" >> $cleanList
                            # -->����Ϣд�뵽/data3/incampro/db_management/logs/clean_list.log
                        else
                            \rm -f $rootPath/${tmp}.tgz
                            # -->ɾ����ǰ�Ϻ�
                        endif
                    endif
                endif
            endif
        endif
        @ i++
    else        ## normal jobs handling(�����Ϻ�-->13λ)
        set tmpRootPath = "${dbRootPath}/${tmp}"
        # -->/incampro/incam_db1/jobs/��ǰ�Ϻ�
        if ( -d $tmpRootPath ) then
            set lastOpenFile = "$tmpRootPath/user/last_opentime"
            # -->/incampro/incam_db1/jobs/��ǰ�Ϻ�/user/last_opentime"
            
                # -->����·��(�ϴ����ݿ�����¼) AresHe 2020.03.27
            set backupPath = "/data3/incampro/db_management/normal_jobs";
            
            #  --> last_opentime == 2019-11-20 20:49:00 31740
            #  --> `cat $aa | cut -d ' ' -f3` -->�Կո���ָ�$aa������ȡ�������ֶ�
            if ( -f $lastOpenFile ) then
                set lastOpenUser = `cat $lastOpenFile | cut  -d ' ' -f3`
                # --> $lastOpenUser = 31740 (-f3 ��3��)
            
                set timeLastOpen = `cat $lastOpenFile | cut  -d ' ' -f1`
                # --> $lastOpenUser = 201-11-20 (-f1 ��1��)
                
                set timeLastOpenTime = `cat $lastOpenFile | cut  -d ' ' -f2`
                # --> $lastOpenUser = 20:49:00 (-f2 ��2��)
                
                set _DayAgoTime = `date -d "-30 day" "+%F"`
                # -->��ȡ30��ǰʱ��
            
                set timeLastOpenSeconds = `date -d "$timeLastOpen" "+%s"`    ## seconds since 1970-01-01 00:00:00 UTC  
                set _DayAgoTimeSeconds = `date -d "$_DayAgoTime" "+%s"`    ## seconds since 1970-01-01 00:00:00 UTC  
                
                # -->����ʱ��<=��ǰ����ʱ��Ա�
                # -->2019-11-20 <= 2019-10-20(�����Ϻ�)
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
                # -->����ʲô��˼?ʲô����?
                set checkInOut = `dbutil lock test $tmp | cut -d ' ' -f1`
                if ( $checkInOut == 'no' ) then
                
                    # -->�л�·�� /incampro/incam_db1/jobs/��ǰ�Ϻ�
                    cd $tmpRootPath
                    
                    # -->�л�·�� /incampro/incam_db1/jobs
                    cd ..
                    
                    # -->�����ǰ�Ϻ�
                    \tar -zcf $normalJobsRootPath/${tmp}.tgz $tmp
                    
                    if ( $? != 0 ) then     ## false, tar failed
                        # -->��$?������0ʱ�����ʧ��?
                        \rm -f $rootPath/${tmp}.tgz
                    else     ## true, tar successfully
                        VOF
                            # -->ɾ��Incam�µĵ�ǰ�Ϻ�TGZ
                            COM delete_entity,job=$tmp,name=$tmp,type=job
                        VON
                        if ( $STATUS == 0 ) then
                        
                            # -->$STATUS����0����ִ�гɹ�?
                            @ number++
                            # -->date %F �������ڸ�ʽ���ȼ��� %Y-%m-%d
                            set timeNow = `date "+%F|%H:%M:%S"`
                            
                            echo "$tmp" "$timeNow" "$lastOpenUser" "$lastOpenTime" "$backupPath" "$remarkContext" >> $cleanList
                            # -->����Ϣд�뵽/data3/incampro/db_management/logs/clean_list.log
                        else
                            \rm -f $rootPath/${tmp}.tgz
                            # -->ɾ����ǰ�Ϻ�
                        endif
                    endif
                endif
            endif
        endif
        @ i++
    endif
end


EndAndExit:  # -->��������ǽ����˳�?

# -->perl�ű������ݿ⣬���沿����ʲô? /data3/incampro/db_management/logs/clean_list.log -->������ļ�?
perl /incampro/server/site_data/scripts/db_management/incamp_connect_to_mysql.pl /data3/incampro/db_management/logs/clean_list.log

# -->����ʱ��
set timeEnd = `date "+%F %H:%M:%S"`
echo "$timeEnd incam database clean end $i"  # --> $iʲô��˼? ����1?  -->ֻecho���ն��������ʾ?

echo "end ${number} : $timeEnd" >> $timeRecordFile
echo "=====================" >> $timeRecordFile













