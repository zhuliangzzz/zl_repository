#! /usr/bin/perl


my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime(time());
$year += 1900;
$mon = sprintf("%02d", $mon + 1);
$mday = sprintf("%02d", $mday);
$hour = sprintf("%02d", $hour);
$min = sprintf("%02d", $min);
$sec = sprintf("%02d", $sec);
$todax = "${year}/${mon}/${mday} ${hour}:${min}:${sec}";

rename "/opt/db_management/logs/BAK/clean_list.log","/opt/db_management/logs/BAK/clean_list.log.$year-$mon-$mday_$hour:$min:$sec";

