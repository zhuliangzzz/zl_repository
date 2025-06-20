#! /usr/bin/perl -w
use strict;
use DBI;
use File::Copy;
my $cleanList = $ARGV[0];

if ( -f $cleanList )
{
    my $dbname = "incam_management";
    my $location = "192.168.2.19";
    my $port = "3306"; 
    my $database = "DBI:mysql:$dbname:$location:$port";
    my $db_user = "root";
    my $db_pass = "k06931!";
    my $dbh = DBI->connect($database,$db_user,$db_pass);
    my $sth;
    while ( <> )
    {
        my @allLog = split(" ",$_);
        
        my $p = 0;
        foreach my $tmp ( @allLog )
        {
            $allLog[$p] =~ s/\|/\ /g;
            $allLog[$p] =~ s/null/\ /g;
            $p++;
        }
        
        my ($curJob,$removeTime,$lastOpenUser,$lastOpenTime,$backupPath,$remarkContext) = ( @allLog );
        
		# add Backup Path for HDI path and MLB path not the same But job name may be the same 
        $sth = $dbh->prepare("SELECT Job FROM abnormal_jobs where Job = \'$curJob\' AND `Backup Path` = \'$backupPath\'");
        $sth->execute() or die "无法执行SQL语句:$dbh->errstr"; 
        
        my @existStat;
        while ( my @recs=$sth->fetchrow_array)
        {
            push (@existStat,$recs[0]);
        }
        
        my $scalarVal = @existStat;
        
        if ( $scalarVal == 0 )
        {
            $sth = $dbh->prepare("INSERT INTO `abnormal_jobs` (`Job`, `Remove Time`, `Last Open User`, `Last Open Time`, `Backup Path`, `Remark`, `Site`, `DB_Source`) VALUES ('$curJob', '$removeTime', '$lastOpenUser', '$lastOpenTime', '$backupPath', '$remarkContext', 'HDI', 'incam')");
        
        } else {
		# Add Site 
            $sth = $dbh->prepare("UPDATE abnormal_jobs set `Remove Time` = '$removeTime', `Last Open User` = '$lastOpenUser', `Last Open Time` = '$lastOpenTime', `Backup Path` = '$backupPath', Remark = '$remarkContext', Site = 'HDI', DB_Source = 'incam' WHERE Job = '$curJob' AND `Backup Path` = \'$backupPath\'");
        }
        $sth->execute() or die "无法执行SQL语句:$dbh->errstr";
    }
    my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime(time());
    $year += 1900;
    $mon = sprintf("%02d", $mon + 1);
    $mday = sprintf("%02d", $mday);
    $hour = sprintf("%02d", $hour);
    $min = sprintf("%02d", $min);
    $sec = sprintf("%02d", $sec);
    
    rename "$cleanList","${cleanList}.${year}-${mon}-${mday}_${hour}:${min}:${sec}";
    move ("${cleanList}.${year}-${mon}-${mday}_${hour}:${min}:${sec}","/data3/db_management/logs/BAK/clean_list.log.${year}-${mon}-${mday}_${hour}:${min}:${sec}");
    

    $sth->finish;
    $dbh->disconnect;
}

exit 0;














