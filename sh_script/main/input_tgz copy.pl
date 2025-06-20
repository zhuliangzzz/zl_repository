#!/usr/bin/perl
use lib '/incam/release/app_data/perl';
use Tk;
use incam;
use Encode;
use File::Find;
use File::Copy;
use File::Copy::Recursive qw(fcopy rcopy dircopy fmove rmove dirmove);
use XML::Simple;
my $Version = "V1.6";

$host = shift;
my $f = new incam($host);
require Tk::LabFrame;
require Tk::LabEntry;

use POSIX qw(strftime);

my $sel_job = "";
my $change_job_name = "";
my $tgz_path = "";
my $images_path = "/incam/server/site_data/scripts/sh1_script/images";
my @joblist_new = ();
my @pp_data = ();
my @joblist_new_sel = ();
my @joblist_input_path = ();
###################################################################################################################################################################################################

my $mw9 = MainWindow->new( -title =>"VGT");
$mw9->bind('<Return>' => sub{ shift->focusNext; });
$mw9->protocol("WM_DELETE_WINDOW", \&OnQuit);
$mw9->geometry("305x535+30+100");
$mw9->raise( );
#$mw9->resizable(0,0);
my $sh_log = $mw9->Photo('info',-file => "$images_path/sh_log.xpm");

my $CAM_frm = $mw9->Frame(-bg => '#9BDBDB',-borderwidth =>2,-relief => "raised",-height => 15)->pack(-side=>'top',-fill=>'x');
my $image_label = $CAM_frm->Label(-image => $sh_log, -border => 1, -relief => 'solid',
                                              )->pack(-side => 'left',
                                                      -padx => 5,
                                                      -pady => 5);

$CAM_frm->Label(-text => 'Input TGZ',-font => 'charter 18 bold',-bg => '#9BDBDB')->pack();
$CAM_frm->Label(-text => hanzi("作者:dgz $Version"),-font => 'charter 8',-bg => '#9BDBDB')->pack(-side=>'right', -padx => 10);

my $sel_frm = $mw9->LabFrame(-label => hanzi("参数选择"),-font => 'SimSun 10',-bg => '#9BDBDB',-fg => 'blue',)->pack(-side=>'top',-fill=>'both');
my $sel_site_frm = $sel_frm->Frame(-bg => '#9BDBDB')->pack(-side=>'left',-fill=>'both');

my $sel_site = "临时";
$sel_site = decode('utf8',$sel_site);
my @function_list = ('胜宏全套','临时','HDI全套');
foreach my $tmp (@function_list) {
	my $show_sel_site = $sel_site_frm->Radiobutton( -text => hanzi("$tmp"),
													-variable => \$sel_site,
													-background => '#9BDBDB',
													-font => 'SimSun 12',
													-value => hanzi("$tmp"))->pack(-side   => "left",
																		  -padx   => 2,
																		  -pady   => 5,
																		  -fill   => "both");

}

my $job_name = "此处输入料号回车搜索";
$job_name = decode('utf8',$job_name);
my $input_frm = $mw9->Frame(-bg => '#9BDBDB',-borderwidth =>2,-relief => "raised")->pack(-side=>'top',-fill=>'x');
my $input_name = $input_frm->LabEntry(-label => hanzi("关键字:"),
										-labelBackground => '#9BDBDB',
										-labelFont => 'SimSun 16',
										-textvariable => \$job_name,
										-bg => 'white',
										-fg => 'grey',
										-width => 24,
										-relief=>'ridge',
										-labelPack => [qw/-side left -anchor w/])->pack(-side => 'left',-padx => 1,-pady => 5);
$input_name->bind('<Button-1>',\&update_input_frm);
$input_name->bind('<Button-2>',\&update_input_frm);
$input_name->bind('<Button-3>',\&update_input_frm);
foreach my $key (qw/Return KP_Enter/){
	$input_name->bind("<$key>",\&jobfilter);
}
my $search_button = $input_frm->Button(	-text => hanzi("查找"),
										-command => sub {&jobfilter;},
										-width => 3,
										-bg => '#9BDBDB',
										#-activebackground=>'#9BDBDB',
										-font=> 'SimSun 12',
										-height=> 1)
										->pack(	-side => 'right',
												-padx => 5,
												-pady => 5);
my @joblist = ();
my $listbox_app_frm = $mw9->Frame(-bg => '#9BDBDB')->pack(-side=>'top',-fill=>'x');
my $listbox_frm = $listbox_app_frm->Frame(-bg => '#9BDBDB')->pack(-side => 'left',-fill=>'both');
my $lb_joblist = $listbox_frm->Scrolled('Listbox',-scrollbars=>'e',-background=>'white',-foreground=>'black',-selectmode=>'single',-selectbackground=>'black',-selectforeground=>'white',-height=>'16',-width => '35',-font=> 'charter 12 bold')
						->pack(-fill=>'both',-expand=>1);

$lb_joblist->insert('end',@joblist);

$lb_joblist->bind('<Double-Button-1>',\&run_input_tgz);

my $button_frm = $mw9->Frame(-bg => '#9BDBDB',-borderwidth =>2,-height => 20)->pack(-side=>'bottom',-fill=>'x');
my $run_button = $button_frm->Button(-text => hanzi("导入"),
										  -command => sub {&run_input_tgz;},
										  -width => 6,
										  -activebackground=>'green',
										  -bg => '#9BDBDB',
										  -font=> 'SimSun 12',
										  -height=> 1,
										  )->pack(-side => 'left',
												  -padx => 2);
my $b_close = $button_frm->Button(-text=>hanzi("退出"),
											-activebackground=>'red',
											-height => 1, -bg => '#9BDBDB',
											-font=> 'SimSun 12',-width=>'6',
											-command=>sub{exit 0;})
											->pack(-side=>'right',-padx=>2);

MainLoop;

###############################################################################################################################################################################################################
sub OnQuit {
	my $ans = $mw9->messageBox(-icon => 'question',-message => hanzi("你确定要退出吗？"),-title => 'quit',-type => 'YesNo');
	return if $ans eq "No";
	exit 0;
}

sub update_input_frm {
	$job_name = "";
	$input_name->configure(-fg => 'black');
}

sub jobfilter {

	@joblist_new = ();
	@pp_data = ();
	@joblist_new_sel = ();
	@joblist_input_path = ();
	my $tmp_jobname = $job_name;
	$tmp_jobname =~ s/\*\*\*\*/\*/g;
	$tmp_jobname =~ s/\*\*\*/\*/g;
	$tmp_jobname =~ s/\*\*/\*/g;

	my @tmp_data = split(/\*/,$tmp_jobname);
	foreach my $tmp (@tmp_data) {
		chomp($tmp);
		push(@pp_data,$tmp);
	}
	my $client_no = uc($pp_data[0]);

	if ( $sel_site eq hanzi("胜宏全套"))  {
		$tgz_path = "/windows/33\.tgz/$client_no\系列";
		chdir "$do_path";
	} elsif ( $sel_site eq hanzi("临时")) {
		$tgz_path = "/windows/33\.file/$client_no\系列";
		chdir "$do_path";
	} elsif ( $sel_site eq hanzi("HDI全套")) {
		$tgz_path = "/windows/174\.tgz/$client_no\系列";
		chdir "$do_path";		
	}
	$tgz_path = decode('utf8',$tgz_path);
	&find_fileindir("$tgz_path");
}

sub run_input_tgz {
	my @sel_job_name = ();
	foreach($lb_joblist->curselection()){
		my $tmp_job = $lb_joblist->get($_);
		push(@sel_job_name,$tmp_job);
	}
	$sel_job_no = scalar(@sel_job_name);
	if ( $sel_job_no eq 0 ) {
		&run_message_notsel_job;
		$run_button->withdraw;
	}
	$sel_job = @sel_job_name[0];
	my $i = 0;
	foreach my $job (@joblist_new_sel) {
		if ( $sel_job eq $job ) {
			last;
		}
		$i++;
	}
	my $input_path = @joblist_input_path[$i];
	my @tmp_data = split(/\./,$sel_job);
	my $input_tgz_name = @tmp_data[0];
    #检测是否最新版本的tgz  
	
	my $res = system("python /incam/server/site_data/scripts/hdi_scr/Input/input_tgz/check_tgz_ver.py $input_tgz_name");	
	if($res != 0){return;}
    #&checkTwoSoftExistsSameJob($input_tgz_name);
	$f->INFO(entity_type => 'job',entity_path => "$input_tgz_name",data_type => 'EXISTS');
	if ( $f->{doinfo}{gEXISTS} eq "yes" ) {
		&run_message_job_yes;
		my $tmpJob = lc($sel_job);
			$tmpJob =~ s/\.tgz$//i;
		$f->COM('get_user_name');
		my $IncamUser = lc($f->{COMANS});
		my $DateTime = strftime "%Y.%m.%d", localtime(time);
		my $tmpJobName = $tmpJob . '-old' . '_' . $IncamUser . '_' . $DateTime;
		$f->INFO(entity_type => 'job',entity_path => "$tmpJobName",data_type => 'EXISTS');
		if ( $f->{doinfo}{gEXISTS} eq "no" ) {
			$change_job_name = $tmpJobName;
			#$f->COM("rename_entity,job=,is_fw=no,type=job,fw_type=form,name=$input_tgz_name,new_name=$tmp_name");	## mark by hyp, Nov 22, 2017
			$f->COM("rename_entity,job=$input_tgz_name,name=$input_tgz_name,new_name=$tmpJobName,is_fw=no,type=job,fw_type=form");	## add by hyp, Nov 22, 2017
		} else {
				my $n = 1;
				while ( $n < 100 ) {
					#my $tmp_name = "$sel_job\+$n";
					my $tmp_name = $tmpJobName . sprintf("%02d",$n);
					$f->INFO(entity_type => 'job',entity_path => "$tmp_name",data_type => 'EXISTS');
					if ( $f->{doinfo}{gEXISTS} eq "no" ) {
						$change_job_name = $tmp_name;
						#$f->COM("rename_entity,job=,is_fw=no,type=job,fw_type=form,name=$input_tgz_name,new_name=$tmp_name");	## mark by hyp, Nov 22, 2017
						$f->COM("rename_entity,job=$input_tgz_name,name=$input_tgz_name,new_name=$tmp_name,is_fw=no,type=job,fw_type=form");	## add by hyp, Nov 22, 2017
						last;
					}
					$n++;
				}
		}
	}

	$f->VOF;
	my $ip_db = 'db1';
	
	my $cmd ="hostname";
	my $host_name =`$cmd`;
	# print $output;

	if ($host_name =~ /ntincam/) {
		$ip_db = 'db3';
	}
	
	$f->COM("import_job,db=$ip_db,path=$input_path,name=$input_tgz_name");
	$f->COM("checkin_closed_job,job=$input_tgz_name");
	$f->VON;

	if ( $change_job_name eq "" ) {
		&run_message_input_job_no_ok($input_tgz_name);
	} else {
		&run_message_input_job_yes_ok($input_tgz_name);
	}

}
###################################################################################################################################################################################################
sub hanzi {
	return decode('utf8',shift);
}

sub run_message_input_job_yes_ok {
	my $input_tgz_name = shift ;
#	my $ans1 = $mw9->messageBox(-icon => 'question',-message => hanzi("料号\:$sel_job\已导入;\n  旧资料改名为\:  $change_job_name  \!"),-title => 'Waiting',-type => 'Ok');
	my $ans1 = $mw9->messageBox(-icon => 'question',-message => hanzi(
		join("\n",
			'料号:' . $sel_job . '已导入;',
			'旧资料改名为:' . $change_job_name,
			'是否打开？？？',
		)
	),-title => hanzi('已导入'),-type => 'YesNo');

	if ( uc($ans1) eq 'YES' ) {
		&OpenJob($input_tgz_name);
	}



	exit 0;
	#my $mw9 = MainWindow->new( -title =>"VGT");
	#$mw9->protocol("WM_DELETE_WINDOW", \&OnQuit);
	#$mw9->geometry("500x200-800+100");
	#$mw9->raise( );
	#$mw9->resizable(0,0);
	#my $sh_log = $mw9->Photo('info',-file => "$images_path/sh_log.xpm");
	#my $CAM_frm = $mw9->Frame(-bg => '#9BDBDB',-borderwidth =>2,-relief => "raised",-height => 20)->pack(-side=>'top',-fill=>'x');
	#my $image_label = $CAM_frm->Label(-image => $sh_log, -border => 1, -relief => 'solid',
    #                                          )->pack(-side => 'left',
    #                                                  -padx => 2,
    #                                                  -pady => 2);
	#$CAM_frm->Label(-text => hanzi("脚本提示"),-font => 'charter 18 bold',-bg => '#9BDBDB')->pack(-pady => 2);
	#$CAM_frm->Label(-text => hanzi("作者:dgz  Ver:1.0"),-font => 'charter 10',-bg => '#9BDBDB')->pack(-side=>'right', -padx => 10, -pady => 2);
	#my $lab_frm = $mw9->Frame(-bg => '#9BDBDB',-borderwidth =>2,-height => 40)->pack(-side=>'top',-fill=>'x');
	#$lab_frm->Label(-text => hanzi("料号\:$sel_job\已导入;"),-font => 'charter 14',-bg => '#9BDBDB',-fg=>'blue')->pack(-side=>'top', -padx => 5, -pady => 5);
	#$lab_frm->Label(-text => hanzi("旧资料改名为\:$change_job_name\!"),-font => 'charter 14',-bg => '#9BDBDB',-fg=>'blue')->pack(-side=>'top', -padx => 5, -pady => 5);
	#my $Bot_frm = $mw9->Frame(-bg => '#9BDBDB',-borderwidth =>2,-height => 40)->pack(-side=>'bottom',-fill=>'x');
	#my $array_button = $Bot_frm->Button(-text => hanzi("退出"),
    #                                     -command => sub {exit 0;},
    #                                     -width => 10,
	#									  -activebackground=>'#9BDBDB',
	#									  -font=> 'charter 12',
	#									  -height=> 2
    #                                      )->pack(-side => 'right',
    #                                              -padx => 20);
	#MainLoop;
}

sub run_message_input_job_no_ok {
	my $input_tgz_name = shift ;

#	my $ans1 = $mw9->messageBox(-icon => 'question',-message => hanzi("料号已导入!"),-title => 'Waiting',-type => 'Ok');
#	my $ans1 = $mw9->messageBox(-icon => 'question',-message => hanzi("料号已导入!"),-title => 'Waiting',-type => 'Ok');
	my $ans1 = $mw9->messageBox(-icon => 'question',-message => hanzi(
		join("\n",
			'料号:' . $sel_job . '已导入;',
			'是否打开？？？',
		)
	),-title => hanzi('已导入'),-type => 'YesNo');

	if ( uc($ans1) eq 'YES' ) {
		&OpenJob($input_tgz_name);
	}
	exit 0;
}

sub OpenJob {
	my $tJob = shift ;
	if ( not defined $tJob ) {
		return;
	}

	$f->VOF;
	$f->COM('open_job' ,job => $tJob ,open_win => 'yes' ,);
	$f->AUX('set_group' ,group => $f->{COMANS} ,);
	$f->COM('check_inout' ,job => $tJob ,mode => 'out' ,ent_type => 'job' ,);
	$f->VON;
	# === TOOD 调用外部程序，写入打开时间以及关联锁定的hooks ===
	$f->COM('get_user_name');
	my $IncamUser = lc($f->{COMANS});
	#if (($IncamUser eq '44566' || $IncamUser eq '69599' || $IncamUser eq '74509' || $IncamUser eq '74591' || $IncamUser eq '74508' || $IncamUser eq '74512') and $sel_site eq hanzi("临时")) {
	if ($sel_site eq hanzi("临时")) {
		system("python /incam/server/site_data/scripts/hdi_scr/Tools/job_lock/open_job_lock.py $tJob");
	}
	# === 2022.10.14 增加是否更新hct的检测 
	system("python /incam/server/site_data/scripts/sh_script/hct_coupon/check_job_hct_step_time.py $tJob");

	##针对A79系列 ，打开料号提醒更改二维码，并跳转到二维码界面 by 吕康侠 需求来源：http://192.168.2.120:82/zentao/story-view-3980.html
	if ($tJob=~/^[a-z]a79/)
	{
		if ($^O=~/Win/i){
			system ("python Z:\\incam\\genesis\\sys\\scripts\\sh_script\\GETZQMC\\CheckEWM.py $tJob");
		}else{
			system ("python /incam/server/site_data/scripts/sh_script/GETZQMC/CheckEWM.py $tJob");
		}
	}
	# === 183 系列打开时提示值班人员不可修改 ===
	if ($tJob=~/^[a-z0-9]183/) {
		my $ans1 = $mw9->messageBox(-icon => 'question',-message => hanzi("值班人员请注意，183系列不允许修改资料."),-title => 'Waiting',-type => 'Ok');
	}

	#显示客户系列和单个料号特殊做法的记录 20230310 by lyh
	system("python /incam/server/site_data/scripts/sh_script/record_job_customer_spec/show_job_customer_spec.py $tJob");
	
	#更新周期配置格式 20240102 by lyh
	system("python /incam/server/site_data/scripts/sh_script/update_users_week_format_config/update_users_week_format_config.py");
	
	system("python /incam/server/site_data/scripts/hdi_scr/Tools/get_job_attr/get_job_attr.py $tJob");
}


sub run_message_job_yes {
	my $ans1 = $mw9->messageBox(-icon => 'question',-message => hanzi("料号已存在!  点击YES旧资料改名并导入,  点击NO退出."),-title => 'quit',-type => 'YesNo');
	return if $ans1 eq "Yes";
	exit 0;
}

sub run_message_notsel_job {
	my $ans1 = $mw9->messageBox(-icon => 'question',-message => hanzi("没有选择要导入的JOB，是否退出？"),-title => 'quit',-type => 'YesNo');
	return if $ans1 eq "No";
	exit 0;
}

sub find_fileindir() {
	local($dir) = @_;
	opendir(DIR,"$dir"|| die "can't open this $dir");
	local @files =readdir(DIR);
	closedir(DIR);

	foreach my $file (@files) {
#		next if ( $file =~ m/\.$/ or $file =~ m/\.\.$/ or $file =~ m/000/ );
		next if ( $file =~ m/\.$/ or $file =~ m/\.\.$/ );

		my $pp_name1 = "";
		my $pp_name2 = "";
		my $pp_name3 = "";
		my $pp_name4 = "";
		my $pp_name5 = "";

		my $name_no = scalar(@pp_data);

		if ( $name_no eq "0" ) {
			$lb_joblist->selectionClear(0,'end');
		} elsif ( $name_no eq "1" ) {
			$pp_name1 = @pp_data[0];
			if ( $file =~ /$pp_name1/ && $file =~ /.tgz$/ ) {

				my $name_legth = length($file);
				if ( $name_legth eq "17" ) {
					push(@joblist_input_path,"$dir/$file");
					push(@joblist_new_sel,$file);
				}

			} elsif ( -d "$dir/$file" ) {
				find_fileindir("$dir/$file");
			}
		} elsif ( $name_no eq "2" ) {
			$pp_name1 = @pp_data[0];
			$pp_name2 = @pp_data[1];
			if ( $file =~ /$pp_name1/ && $file =~ /$pp_name2/ && $file =~ /.tgz$/ ) {

				my $name_legth = length($file);
				#if ( $name_legth eq "17" ) {
					push(@joblist_input_path,"$dir/$file");
					push(@joblist_new_sel,$file);
				#}

			} elsif ( -d "$dir/$file" ) {
				find_fileindir("$dir/$file");
			}
		} elsif ( $name_no eq "3" ) {
			$pp_name1 = @pp_data[0];
			$pp_name2 = @pp_data[1];
			$pp_name3 = @pp_data[2];
			if ( $file =~ /$pp_name1/ && $file =~ /$pp_name2/ && $file =~ /$pp_name3/ && $file =~ /.tgz$/ ) {
				my $name_legth = length($file);
				if ( $name_legth eq "17" ) {
					push(@joblist_input_path,"$dir/$file");
					push(@joblist_new_sel,$file);
				}

			} elsif ( -d "$dir/$file" ) {
				find_fileindir("$dir/$file");
			}
		} elsif ( $name_no eq "4" ) {
			$pp_name1 = @pp_data[0];
			$pp_name2 = @pp_data[1];
			$pp_name3 = @pp_data[2];
			$pp_name4 = @pp_data[3];
			if ( $file =~ /$pp_name1/ && $file =~ /$pp_name2/ && $file =~ /$pp_name3/ && $file =~ /$pp_name4/ && $file =~ /.tgz$/ ) {
				my $name_legth = length($file);
				if ( $name_legth eq "17" ) {
					push(@joblist_input_path,"$dir/$file");
					push(@joblist_new_sel,$file);
				}

			} elsif ( -d "$dir/$file" ) {
				find_fileindir("$dir/$file");
			}
		} elsif ( $name_no eq "5" ) {
			$pp_name1 = @pp_data[0];
			$pp_name2 = @pp_data[1];
			$pp_name3 = @pp_data[2];
			$pp_name4 = @pp_data[3];
			$pp_name5 = @pp_data[4];
			if ( $file =~ /$pp_name1/ && $file =~ /$pp_name2/ && $file =~ /$pp_name3/ && $file =~ /$pp_name4/ && $file =~ /$pp_name5/ && $file =~ /.tgz$/ ) {
				my $name_legth = length($file);
				if ( $name_legth eq "17" ) {
					push(@joblist_input_path,"$dir/$file");
					push(@joblist_new_sel,$file);
				}

			} elsif ( -d "$dir/$file" ) {
				find_fileindir("$dir/$file");
			}
		}
	}
	$lb_joblist -> delete("0","end");
	$lb_joblist->insert('end',@joblist_new_sel);
}

sub checkTwoSoftExistsSameJob {
    my ($curJob) = @_;
    
    my $soft_use;
    my $another_joblist;
    my $another_soft;
    my $anotherDbutilPath;
    my $error;

    # add judge which soft use 

		if ("$ENV{INCAM_PRODUCT}" =~ /\/incampro\//){
			$soft_use = "incampro";
			$another_soft = "incam";
			$another_joblist = "/incam/server/config/joblist.xml";
			$anotherDbutilPath = "/incam/release/bin/dbutil";
		} elsif ("$ENV{INCAM_PRODUCT}" =~ /\/incam\//) {
			$soft_use = "incam";
			$another_soft = "incampro";
			$another_joblist = "/incampro/server/config/joblist.xml";
			$anotherDbutilPath = "/incampro/release/bin/dbutil";

		} else {
			$soft_use = "error";
		}
	
	
		# 判断料号名是否存在另一个数据库中
		# incam /frontline/incam/server/config/joblist.xml
		# incampro /frontline/incampro/server/config/joblist.xml
		if ( -e $another_joblist ) {
	
			my $simple = XML::Simple->new();
			our $check = $simple->XMLin($another_joblist);
				#print Dumper($check);
			if (exists $check->{'job'}->{$curJob}) {
					my $tmpCmdLine = "$anotherDbutilPath lock test $curJob" ;
					my $tmpExecLine = `$tmpCmdLine`;
					chomp $tmpExecLine;
					my @lock_status = split(/ /,$tmpExecLine);

					my $atime;
					my $mess;
					$atime =  strftime "%Y-%m-%d %H:%M:%S", localtime($check->{'job'}->{$curJob}->{'updated'});
					if ($lock_status[0] eq "no") {
						#code
						$mess = "此料号未被锁定\n";
					} elsif ($lock_status[0] eq "yes")  {
						$mess = "此料号由$lock_status[1] 锁定\n";
					} else {
						$mess = "未能获取锁定状态\n";
					}
					#my $anotherExist = iTkxMsgBox("同名料号存在" ,"$curJob" . "存在于软件" . "$another_soft" . "中,\n$mess 最后用户为 $check->{'job'}->{$curJob}->{'lastUser'},最后更新时间为 $atime \n,打开料号动作终止","ok","warning",'ok',);
						my $ans1 = $mw9->messageBox(-icon => 'info',-message => hanzi("同名料号存在" . "$curJob" . "存在于软件" . "$another_soft" . "中,\n$mess 最后用户为 $check->{'job'}->{$curJob}->{'lastUser'},最后更新时间为 $atime \n,导入料号动作终止"),-title => 'quit',-type => 'ok');

	exit 0;
					$error = 'yes';
			} else {
				#my $anotherExist = iTkxMsgBox("放行","$curJob" . "不存在于软件" . "$another_soft" . "列表中","ok","warning",'ok',);
				$error = 'no';
			}
		} else {
						my $ans1 = $mw9->messageBox(-icon => 'info',-message => hanzi("单一程序存在". "找不到" . $another_soft ."对应的数据库" . "$another_joblist" . "导入料号动作终止"),-title => 'quit',-type => 'ok');

	exit 0;
			#my $noOtherSoft = iTkxMsgBox("单一程序存在", "找不到" . $another_soft ."对应的数据库" . "$another_joblist" . "打开料号动作终止","ok","warning",'ok',);
			
			$error = 'yes';
		}
		if ($error eq 'yes') {
			$f->VOF();
			#$f->COM("checkin_closed_job,job=$curJob");
			#$f->COM("check_inout,job=$curJob,mode=in,ent_type=job");
			$f->VON();

        exit 0;
		}
}






__END__
# 版本v1.2
# Author:Chao.Song
# Modifies:
# 1. 增加HDI全套tgz路径；
# 2. 更改“全套” 为“胜宏全套”
# 3. 需挂载174.tgz 参考/etc/auto.win/
版本:v1.3
2020.01.08
Author:Chao.Song
1.判断料号名是否存在另一个数据库中

版本:v1.4
2021.04.12
Author:Chao.Song
1.南通机台，导入默认db3

版本：V1.5
2022.03.15
Author:Chao.Song
1.吕康侠加了二维码检测
2.周涌的账号添加了仅从临时导入时，才检查料号锁定。
3.取消料号是否在两个软件中的检测。

版本：V1.6
2022.08.16
Author:Chao.Song
1.183系列打开时。提醒值班人员不可修改。http://192.168.2.120:82/zentao/story-view-4528.html
