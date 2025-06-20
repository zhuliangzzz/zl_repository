#! /usr/bin/perl -w
use strict;
use utf8;
use POSIX qw(strftime);

&main();

#    
sub main
{
    my $dbName = 'incam_management';
    my $table = 'abnormal_jobs';
    
    my @deleteJobs = &GetInfoFromMysql($dbName,"SELECT Job FROM `$table` WHERE UNIX_TIMESTAMP(`Remove Time`) <= UNIX_TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 3 DAY)) AND Job REGEXP '[^0*]'" );

    for my $delJob ( @deleteJobs )
    {
        next if ( length($delJob) == 13 );
        if (unlink "/opt/db_management/abnormal_jobs/${delJob}.tgz")
        {
            my $timeNow = strftime "%Y-%m-%d %H:%M:%S", localtime(time);
            print "$timeNow Deleted ${delJob}.tgz...\n";
            &DeleteMysqlLog($dbName,"DELETE FROM $table WHERE Job = \'$delJob\'");
        } else {
            my $timeNow = strftime "%Y-%m-%d %H:%M:%S", localtime(time);
            print "$timeNow Delete /opt/db_management/abnormal_jobs/${delJob}.tgz failed.\n";            
        }
    }
    print "end\n";
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

