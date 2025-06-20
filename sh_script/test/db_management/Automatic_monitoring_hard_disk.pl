#!/usr/bin/perl
use DBI;

####自动监控计算机储存信息程序-->当储存达到80%将自动报警通知各负责人。
#### AresHe 20191210
#use Mail::Sender;
#$ip_addr=`/sbin/ifconfig eth0 | perl -lne 'print \$1 if/inet addr:(.*)Bcast/'`;
#$ip_addr=~ s/^\s+|\s+$//g;

my @diskinfo=`df -h`;
my $hostName = `hostname`;
chomp $hostName;
shift @diskinfo;
my @diskspace=();
my @diskpath=();
foreach my $i(@diskinfo){
    if ($i =~ /%/) {
        my @tmp =  split(' ', $i);
        for (my $n=0;$n<=$#tmp;$n++){
            if ($tmp[$n] =~ /%/) {
                $tmp[$n] =~ s/%//g;;
                $tmp[$n] =~ s/ +$//;
                if ($tmp[$n] > 0 && $tmp[$n] > 80) {
                    chomp $tmp[$n];
                    my $m =  $n + 1;
                    chomp $tmp[$m];
                    if ($hostName =~ /^ibm6/ || $hostName =~ /^hdi-incam/) {
                        if ($hostName =~ /^ibm6/) {
                            if ($tmp[$m] =~ /^\/mnt/) {
                                next;
                            }else{
                                push @diskspace,$tmp[$n];
                                push @diskpath,$tmp[$m];
                            }
                        }else{
                            push @diskspace,$tmp[$n];
                            push @diskpath,$tmp[$m];
                        }
                    }else{
                        if ($tmp[$m] =~ /^\/$/) {
                            push @diskspace,$tmp[$n];
                            push @diskpath,$tmp[$m];
                        }else{
                            next;
                        }
                    }
                }
            }
        }
    }
}
if (! @diskspace) {
    exit;
}else{
    &sqlemail;
    exit;
}

sub sqlemail{
    my $msg = "<h1>计算机&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;已使用空间&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;路径</h1>";
    my $add_msg;
    for (my $i=0; $i<=$#diskspace; $i++) {
        my $addmsg = "<p>$hostName&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;$diskspace[$i]% &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; $diskpath[$i]</p>";
        $add_msg = $add_msg . $addmsg;
    }
    my $body = qq{
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <title>检测硬盘容量提示</title>
    </head>
    <body>
        $msg
        $add_msg
    </body>
    </html>};
    
    my $dbname = "project_status";
    my $location = "192.168.2.19";
    my $port = "3306"; 
    my $database = "DBI:mysql:$dbname:$location:$port";
    my $db_user = "root";
    my $db_pass = "k06931!";
    my $dbh = DBI->connect($database,$db_user,$db_pass);
    $dbh->do("SET NAMES utf8");
    my $sth;
    
    my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime(time());
    $year += 1900;
    $mon = sprintf("%02d", $mon + 1);
    $mday = sprintf("%02d", $mday);
    $hour = sprintf("%02d", $hour);
    $min = sprintf("%02d", $min);
    $sec = sprintf("%02d", $sec);
        
    my $MailName = '自动监控计算机硬盘储存信息提醒';
    my $mailto;
    if ($hostName =~ /^ibm6/ || $hostName =~ /^hdi-incam/) {
        $mailto = 'chuang.liu@shpcb.com;rpeng.he@shpcb.com;jxing.li@shpcb.com;chao.song@shpcb.com;cheng.tang@shpcb.com';
        #$mailto = 'rpeng.he@shpcb.com';
    }elsif($hostName =~ /^incam/){
        $mailto = 'qqian.zhuang@shpcb.com;wjun.yang@shpcb.com;tao.liang@shpcb.com;eping.wei@shpcb.com';
    }elsif($hostName =~ /^hdilinux/){
        $mailto = 'li.xiong@shpcb.com;ydi.xue@shpcb.com';
    }
    
    my $mailCC = '';
    my $mailBCC = '';
    my $subject = '监控到下列存盘容量使用超过80%,请清理磁盘空间，避免异常';
    my $mailStatus = 'N';
    my $getTime = "${year}-${mon}-${mday} ${hour}:${min}:${sec}";
    
    $sth = $dbh->prepare("INSERT INTO `mailsent_table` (`MailName`, `mailto`, `mailCC`, `mailBCC`, `subject`, `body`, `mailStatus`, `getTime`)
                         VALUES ('$MailName', '$mailto', '$mailCC', '$mailBCC', '$subject', '$body', '$mailStatus', '$getTime')");
    $sth->execute() or die "无法执行SQL语句:$dbh->errstr";
    $sth->finish;
    $dbh->disconnect;
}


#sub sedmail{
#    my $sender=Mail::Sender->new({
#    ctype=>'text/plain;charset=utf-8',
#    encoding=>'utf-8',
#    smtp =>'smtp.exmail.qq.com',
#    from =>'rpeng.he@shpcb.com',
#    auth =>'LOGIN',
#    authid =>'rpeng.he@shpcb.com',
#    authpwd =>'HRP502614708hrp'}
#    ) or die "Can't send mail.\n";
#    
#    my $msg="Hi All:\n     检测到$hostName-->下列盘符储存空间不足80%,请及时清理垃圾文件!\n     =======================================\n     计算机          盘符            储存空间比例\n";
#    my $add_msg;
#    
#    for (my $i=0; $i<=$#diskspace; $i++) {
#    	$add_msg= "     $hostName       空间: $diskspace[$i]%       路径: $diskpath[$i]\n";
#        $msg = $msg . $add_msg;
#    }
#    if ($hostName =~ /^Incam/ || $hostName =~ /^incam/) {
#            $sender->MailMsg({
#            #to=> 'qqian.zhuang@shpcb.com,tao.liang@shpcb.com,wjun.yang@shpcb.com,eping.wei@shpcb.com',
#            to=> 'rpeng.he@shpcb.com',
#            subject=>'自动监控计算机储存信息程序',
#            msg=>$msg}
#        );
#        $sender->Close();
#    }elsif($hostName =~ /^ibm6/ || $hostName =~ /^hdi-incam/){
#            $sender->MailMsg({
#            #to=> 'chuang.liu@shpcb.com,rpeng.he@shpcb.com,jxing.li@shpcb.com,chao.song@shpcb.com,cheng.tang@shpcb.com',
#            to=> 'rpeng.he@shpcb.com',
#            subject=>'自动监控计算机储存信息程序',
#            msg=>$msg}
#        );
#        $sender->Close();
#    }elsif($hostName =~ /^hdilinux/){
#            $sender->MailMsg({
#            #to=> 'li.xiong@shpcb.com,yfeng.tu@shpcb.com,ydi.xue@shpcb.com,zgang.xu@shpcb.com',
#            to=> 'rpeng.he@shpcb.com',
#            subject=>'自动监控计算机储存信息程序',
#            msg=>$msg}
#        );
#        $sender->Close(); 
#    }
#    print "$hostName 硬盘空间检测完成!\n";
#}
