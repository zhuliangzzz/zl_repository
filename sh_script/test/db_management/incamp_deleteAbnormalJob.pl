#! /usr/bin/perl -w
use strict;
use utf8;
use POSIX qw(strftime);

&main();
sub main
{
    my $dbName = 'incam_management';
    my $table = 'abnormal_jobs';
    
    my $deletelog = "/data3/incampro/db_management/logs/delete.log";
    open(FILEPATH, ">>$deletelog") or die $!;
    
    my @deleteJobs = &GetInfoFromMysql($dbName,"SELECT Job FROM `$table` WHERE UNIX_TIMESTAMP(`Remove Time`) <= UNIX_TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 7 DAY)) AND Job REGEXP '[^0*]' AND DB_Source='incamp'" );
    # -->这句话什么意思 WHERE UNIX_TIMESTAMP(`Remove Time`) <= UNIX_TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 3 DAY)) AND Job REGEXP '[^0*]
    for my $delJob ( @deleteJobs )
    {
        # -->如果料号长度为13位，将跳到下一个继续开始，直至结束为止
        next if ( length($delJob) == 13 );
        
        # -->删除备份型号
        if (unlink "/data3/incampro/db_management/abnormal_jobs/${delJob}.tgz")
        {
            my $timeNow = strftime "%Y-%m-%d %H:%M:%S", localtime(time);
            print FILEPATH "$timeNow Deleted ${delJob}.tgz...\n";
            # -->删除不是正常料号数据库信息
            &DeleteMysqlLog($dbName,"DELETE FROM $table WHERE Job = \'$delJob\' AND DB_Source='incamp'");
        } else {
            # -->料号长度等于13位不删除。
            my $timeNow = strftime "%Y-%m-%d %H:%M:%S", localtime(time);
            print FILEPATH "$timeNow Delete /data3/incampro/db_management/abnormal_jobs/${delJob}.tgz failed.\n";            
        }
    }
    print FILEPATH "end\n";
    close (FILEPATH);
}

sub GetInfoFromMysql
{
    my ($dbName,$sql) = @_;
    my @array;
    require DBI;
    my $location = "192.168.2.19";
    my $port = "3306";
    my $database = "DBI:mysql:$dbName:$location:$port";
    my $db_user = "root";
    my $db_pass = "k06931!";
    my $dbh = DBI->connect($database,$db_user,$db_pass);
    my $sth = $dbh->prepare($sql); 
    $sth->execute() or die "Can't execute:$dbh->errstr";
    
    while (my $RV = $sth->fetchrow_array)
    {
        push (@array,$RV);
    }
    $sth->finish;
    $dbh->disconnect;
    return @array; 
}
sub DeleteMysqlLog
{
    my ($dbName,$sql) = @_;
    
    my $location = "192.168.2.19";
    my $port = "3306"; 
    my $database = "DBI:mysql:$dbName:$location:$port";
    my $db_user = "root";
    my $db_pass = "k06931!";
    my $dbh = DBI->connect($database,$db_user,$db_pass);
    my $sth;
    
    $sth = $dbh->prepare($sql);
    $sth->execute() or die "无法执行SQL语句:$dbh->errstr"; 
    
    $sth->finish;
    $dbh->disconnect;
    
    return 1;
}

