#!/usr/bin/perl -w
use Tk;
use encoding 'euc_cn';
use File::Copy;
use File::Copy::Recursive qw(fcopy rcopy dircopy fmove rmove dirmove);
require Tk::LabFrame;
require Tk::LabEntry;

# --加载自定义公用pm
use lib "$ENV{SCRIPTS_DIR}/sys/scripts/Package";
use Genesis;
use mainVgt;  
use Data::Dumper;
     
# --实例化对象
my $f = new Genesis();
my $GEN = new mainVgt();

my $job_name = $ENV{JOB};
my $username = $GEN->GET_USER_NAME();
# --根据系统定义不同的参数
if ( $^O ne 'linux' ) {
    our $scriptPath = "$ENV{SCRIPTS_DIR}/sys/scripts";
    our $do_tgz_path = "D:/disk/film/$job_name";
    
} else {
    our $scriptPath = "$ENV{SCRIPTS_DIR}/sys/scripts";
    our $do_tgz_path = "/id/workfile/film/$job_name";
}

my $images_path = "$scriptPath/sh_script/output/images";

#my $jobname_no = length($job_name);
#if ( $jobname_no != 13 ) {
#	&run_message_not_right;
#	# exit 0;
#}

# === 2022.08.23 
&check_job_save();

my $client_no = substr($job_name, 1,3);
my $version = substr($job_name,-2,2); 
#my $path_client = "/windows/33\.file/$client_no\系列";
#if (! -d $path_client ) {
#	mkdir "$path_client";
#}
my $pn_7 = substr($job_name,6,1);
if ($pn_7 eq "h" or $pn_7 eq "l") {
	$GEN->Messages('info', "常规提示:喷锡板请留意是否有防焊开窗字,字体宽度需≥20mil.");
}

#1， 输出TGZ增加提醒项目，针对osp+化金的料号，抓取命名规则，输出TGZ提醒；请注意‘白油块’需按照化金制作，请检查资料。
#2，针对镀金板也加入提醒，输出TGZ提醒；请注意‘白油块’需按照化金制作，请检查资料。20221110
system("python /incam/server/site_data/scripts/lyh/sh_hdi_check_rules.py check_silk_for_face_tech_condition");

#设置输出内层还是全套 此界面屏蔽 程序判断移植到sh_hdi_warning_director_process.py中 20241024
# system("rm -rf /tmp/all_output_type_$job_name");
# system("rm -rf /tmp/inner_output_type_$job_name");
# system("python /incam/server/site_data/scripts/lyh/output_tgz_inner_outer_ui_test.py $job_name");
if ( -e "/tmp/all_output_type_$job_name"){	
	$ENV{OUTPUT_TGZ_TYPE}="ALL";
}
if ( -e "/tmp/inner_output_type_$job_name"){	
	$ENV{OUTPUT_TGZ_TYPE}="INNER";
}
system("rm -rf /tmp/all_output_type_$job_name");
system("rm -rf /tmp/inner_output_type_$job_name");
if (-e "/tmp/exit_script_run_$job_name"){
	system("rm -rf /tmp/exit_script_run_$job_name");
	exit 0;
}


#输出TGZ增加卡关，1，监测NPTH孔是否有套铜皮单边8mil。(输出内外TGZ都检测）如没有套铜皮提醒修改。
# 2，监测NPTH孔是否存在防焊开窗及档点。（输出外层TGZ检测）如未存在开窗及档点提醒修改。
# 3，监测NPTH孔对应的sgt-c,sgt-s层是否存在开窗。（输出外层TGZ检测）如未存在开窗提醒修改。 
# 5，输出TGZ增加检测二维码的正反（根据层别识别）。
#system("python /incam/server/site_data/scripts/lyh/sh_hdi_check_rules.py check_barcode_condition");合并到check_npth_hole_condition此中检测
#http://192.168.2.120:82/zentao/story-view-4696.html 20221116 by lyh
#此项改到全自动检测程序内 20230417 by lyh
# system("rm -rf /tmp/exit_script_run_$job_name");
# system("python /incam/server/site_data/scripts/lyh/sh_hdi_check_rules.py check_npth_hole_condition");
# if (-e "/tmp/exit_script_run_$job_name"){
	# system("rm -rf /tmp/exit_script_run_$job_name");
	# exit 0;
# }

#http://192.168.2.120:82/zentao/story-view-5006.html 此项目改到输出tgz时检测 20221227 by lyh 未测试 暂时屏蔽20230105
# system("python /incam/server/site_data/scripts/lyh/sh_hdi_check_rules.py check_mai_hole_lp_hole_condition");
# if (-e "/tmp/exit_script_run_$job_name"){
	# system("rm -rf /tmp/exit_script_run_$job_name");
	# exit 0;
# }

#检测双面开窗孔是否制作塞孔 提示20221215 by lyh
# 已经移植到全自动检测程序中，输出卡关取消  ynh

# system("python /incam/server/site_data/scripts/lyh/sh_hdi_check_rules.py check_plug_hole_condition");

#http://192.168.2.120:82/zentao/story-view-5022.html
#3.输出TGZ时检测LED板有控深钻时外层是否按要求添加铜Pad 20230105 by lyh
system("python /incam/server/site_data/scripts/lyh/sh_hdi_check_rules.py check_kz_hole_add_pad_for_outer_layer");

#http://192.168.2.120:82/zentao/story-view-5034.html
# 输出tgz时提示cam制作人 有控深铣的需要避铜 20230105 by lyh
system("python /incam/server/site_data/scripts/lyh/sh_hdi_check_rules.py check_ks_rout_condition");


###检测940系列是否有做drill_map 密码输出 by 吕康侠 2022/03/24
$GEN->GET_ATTR_LAYER("$job_name","all");
if ($client_no=~/940/){
	if (!grep /^drill-map$/,@{$GEN->{getlayer}}){
		
		my $re;
		if($^O=~/Win/i){
			$re=`python Z:/incam/genesis/sys/scripts/sh_script/COMGG/password.py`;
		}else{
			$re=`python /incam/server/site_data/scripts/sh_script/COMGG/password.py`;
		}
		my $ss=(split /------/,$re)[1];
		
		if ($ss!~/ok/){
			exit;
		}	
	}
}

# === 检测料号中的Ring是否和测试模块的值一致 , 此项不在输出TGZ时候检测，转移到检测项目里面去
if($^O=~/Linux/i){
	my $get_re = system("python /incam/server/site_data/scripts/hdi_scr/Signal/run_check/get_checklist_result.py");
	#print $get_re . "\n";
	#print 'xxxxxxxxxxxxxxxxx' . "\n";
	if ($get_re != 0) {
		$GEN->Messages('info', "镭射Ring一致性检测未通过,输出tgz动作终止。");
		exit 0;
	}
	$f->COM("save_job,job=$job_name,override=no");
}

#####end#######by 吕康侠 2022/03/24#####
if (! -d $do_tgz_path ) {
	mkdir "$do_tgz_path";		
}

# --当为202客户输出字符层时，防呆提醒内容如下：
if ($client_no eq '202')
{
    &cusNum202_check($client_no);
}


#my $do_tgz_path = "/windows/33\.file/$client_no\系列/$job_name/$version";
#if (! -d $do_tgz_path ) {
#	mkdir "$do_tgz_path";
#}

#my $path_tmp_job = "/tmp";
#if (! -d $path_tmp_job ) {
#	mkdir "$path_tmp_job";
#}

# 20211116李家兴添加，输出tgz前检测文字镜像是否正确
if ($GEN->STEP_EXISTS($job_name, 'panel') eq 'yes') {
	my $source_script_genesis = 'Z:/incam/genesis/sys/scripts/sh_script/silk_mirror_chk/silk_mirror_chk.py';
	my $source_script_incam = '/incam/server/site_data/scripts/sh_script/silk_mirror_chk/silk_mirror_chk.py';
	my $chk_status;
	if ($^O ne 'linux') {
		$chk_status = system("python $source_script_genesis panel");
	}
	else {
		$chk_status = system("python $source_script_incam panel");
	}
	print "\$chk_status : $chk_status\n";
	# 如果system执行结果为非零，表示文字镜像检测到异常，要退出
	exit 0 if ($chk_status != 0);
	
	# === 2022.09.05 增加输出tgz的图电symbol的检测  ===
	if ($ENV{OUTPUT_TGZ_TYPE} eq "ALL"){
		$source_script_genesis = 'Z:/incam/genesis/sys/scripts/hdi_scr/Signal/run_check/check_tudian.py';
		$source_script_incam = '/incam/server/site_data/scripts/hdi_scr/Signal/run_check/check_tudian.py';
		if ($^O ne 'linux') {
			$chk_status = system("python $source_script_genesis");
		}
		else {
			$chk_status = system("python $source_script_incam");
		}
		print "\$chk_status : $chk_status\n";
		# 如果system执行结果为非零，表示文字镜像检测到异常，要退出
		exit 0 if ($chk_status != 0);
	}
}

# 输出TGZ前删除所有的checklist 2023-12-25 ynh
system("python /incam/server/site_data/scripts/sh_script/output/del_checklist.py");

# 2019.12.5李家兴修改，gen_line_skip_pre_hooks已经设置为2,此处强制调用pre,传入参数$job_name
my $pre_status = system("perl /incam/server/site_data/hooks/line_hooks/export_job.pre $job_name");
print "\$pre_status : $pre_status\n";
# 如果system执行结果为非零，表示pre hooks检测到异常，要退出
exit 0 if ($pre_status != 0);
#$f->COM("export_job,job=$job_name,path=$do_tgz_path,mode=tar_gzip,submode=full,overwrite=yes");
system("python /incam/server/site_data/scripts/zl/test/Export_Job.py $job_name $do_tgz_path");
# 20241113 zl 打包tgz
system("python /incam/server/site_data/scripts/sh_script/zltest/output/export_idb.py $job_name $username");

# 2019.12.5李家兴修改，定义参数hash的引用
my $ref_param_hash = {
	# export_job.post只用到如下几个参数，如有需要可以自行增加
	job         => $job_name,
	path        => $do_tgz_path,
	mode        => 'tar_gzip',
	submode     => 'full',
	output_name => $job_name,
};
# 两个不同脚本之间不能直接传hash引用，只能通过字符的形式中转
my $param_hash_string = Dumper($ref_param_hash);
# 2019.12.5李家兴修改，gen_line_skip_post_hooks已经设置为2,此处强制调用pre,传入参数$param_hash_string
system 'perl', '/incam/server/site_data/hooks/line_hooks/export_job.post', "$param_hash_string";

#copy("$path_tmp_job/$job_name.tgz","$do_tgz_path");
#system("rm -rf /tmp/$job_name.tgz");

&run_message_over;

exit 0;





####################################################################################################################################
#################################################华丽的分隔线#######################################################################
####################################################################################################################################
sub check_job_save {
	# check if saved
    $f->INFO(entity_type => 'job',
             entity_path => $job_name,
             data_type => 'IS_CHANGED');
    if ( $f->{doinfo}{gIS_CHANGED} eq "yes" ) 
    {
		$GEN->Messages('info', "料号 $job_name 未保存，请先保存!");
		exit 0;
    }
}

# --202客户文字防呆（copy前版本，导致客户版本号未改到。同一客户已发生第二次），输出字符时，打开edit
sub cusNum202_check
{
    my $cusNum = shift;
    my $returnVal = $GEN->Messages('info', "$cusNum 客户曾发生过两次升级版本导致字符层版本未修改到位,请再三确认！！！确认后自动打开edit字符层！");
    # --判断edit step是否存在
    if ($GEN->STEP_EXISTS($job_name, 'edit') eq 'no')
    {
        $GEN->Messages('warning', "检测到无edit step，请手动寻找edit并打开字符层进行比对！");
        $GEN->PAUSE('Pause...');            
    }
    # --打开edit step  ，并打开层
    $GEN->OPEN_STEP($job_name, 'edit');
    $GEN->CLEAR_LAYER;
    if ($GEN->LAYER_EXISTS($job_name, 'edit', 'c1') eq 'yes') {
        $GEN->WORK_LAYER('c1');
    }
    if ($GEN->LAYER_EXISTS($job_name, 'edit', 'c1+1') eq 'yes') {
        $GEN->WORK_LAYER('c1+1', 2);
    }
    
    # --暂停
    $GEN->PAUSE('Pause...');
    $GEN->CLEAR_LAYER;
    
    # --还原输出step
    # $GEN->OPEN_STEP($job_name, $sel_step);
}
	
sub run_message_over {
	my $mw3_3 = MainWindow->new( -title =>"VGT");
	$mw3_3->protocol("WM_DELETE_WINDOW", \&OnQuit);
	$mw3_3->geometry("500x145-800+100");
	$mw3_3->raise( );
	$mw3_3->resizable(0,0);
	
	my $sh_log = $mw3_3->Photo('info',-file => "$images_path/sh_log.xpm");
	my $CAM_frm = $mw3_3->Frame(-bg => '#9BDBDB',-borderwidth =>2,-relief => "raised",-height => 20)->pack(-side=>'top',-fill=>'x');
	my $image_label = $CAM_frm->Label(-image => $sh_log, -border => 1, -relief => 'solid',
                                              )->pack(-side => 'left',
                                                      -padx => 2,
                                                      -pady => 2);  
	$CAM_frm->Label(-text => '输出TGZ  ',-font => 'charter 18 bold',-bg => '#9BDBDB')->pack(-pady => 2);
	$CAM_frm->Label(-text => '版本:胜宏科技  Ver:5.0',-font => 'charter 10',-bg => '#9BDBDB')->pack(-side=>'right', -padx => 10, -pady => 2);
	my $lab_frm = $mw3_3->Frame(-bg => '#9BDBDB',-borderwidth =>2,-height => 40)->pack(-side=>'top',-fill=>'x');
	$lab_frm->Label(-text => '程序运行结束,请确认!',-font => 'charter 14',-bg => '#9BDBDB',-fg=>'red')->pack(-side=>'top', -padx => 5, -pady => 5);
	my $Bot_frm = $mw3_3->Frame(-bg => '#9BDBDB',-borderwidth =>2,-height => 40)->pack(-side=>'bottom',-fill=>'x');
	my $array_button = $Bot_frm->Button(-text => '退出',
                                         -command => sub {exit 0;},
                                         -width => 10,
										  -activebackground=>'#9BDBDB',
										  -font=> 'charter 12',
										  -height=> 2
                                          )->pack(-side => 'right',
                                                  -padx => 20);	
	MainLoop;
}

sub run_message_not_right {
	my $mw3_3 = MainWindow->new( -title =>"VGT");
	$mw3_3->protocol("WM_DELETE_WINDOW", \&OnQuit);
	$mw3_3->geometry("500x145-800+100");
	$mw3_3->raise( );
	$mw3_3->resizable(0,0);
	
	my $sh_log = $mw3_3->Photo('info',-file => "$images_path/sh_log.xpm");
	my $CAM_frm = $mw3_3->Frame(-bg => '#9BDBDB',-borderwidth =>2,-relief => "raised",-height => 20)->pack(-side=>'top',-fill=>'x');
	my $image_label = $CAM_frm->Label(-image => $sh_log, -border => 1, -relief => 'solid',
                                              )->pack(-side => 'left',
                                                      -padx => 2,
                                                      -pady => 2);  
	$CAM_frm->Label(-text => '输出TGZ  ',-font => 'charter 18 bold',-bg => '#9BDBDB')->pack(-pady => 2);
	$CAM_frm->Label(-text => '版本:胜宏科技  Ver:5.0',-font => 'charter 10',-bg => '#9BDBDB')->pack(-side=>'right', -padx => 10, -pady => 2);
	my $lab_frm = $mw3_3->Frame(-bg => '#9BDBDB',-borderwidth =>2,-height => 40)->pack(-side=>'top',-fill=>'x');
	$lab_frm->Label(-text => '厂编不是按规定命名!',-font => 'charter 14',-bg => '#9BDBDB',-fg=>'red')->pack(-side=>'top', -padx => 5, -pady => 5);
	my $Bot_frm = $mw3_3->Frame(-bg => '#9BDBDB',-borderwidth =>2,-height => 40)->pack(-side=>'bottom',-fill=>'x');
	my $array_button = $Bot_frm->Button(-text => '退出',
                                         -command => sub {exit 0},
                                         -width => 10,
										  -activebackground=>'#9BDBDB',
										  -font=> 'charter 12',
										  -height=> 2
                                          )->pack(-side => 'right',
                                                  -padx => 20);	
	MainLoop;
}

sub OnQuit {
    my $mw3_3 = MainWindow->new( -title =>"VGT");
	my $ans = $mw3_3->messageBox(-icon => 'question',-message => '你确定要退出吗？',-title => 'quit',-type => 'YesNo');
	return if $ans eq "No";
	exit;
}
################################################################################################################################################################################


__END__
2019.07.17更新内容如下：
作者：柳闯
版本：5.0
1.202客户文字防呆（copy前版本，导致客户版本号未改到。同一客户已发生第二次），输出字符时，打开edit step 进行确认(梁涛要求，应付客户稽核)

# 2019.12.5李家兴修改，脚本运行过程中不进入hooks 
gen_line_skip_pre_hooks已经设置为2,此处强制调用pre,传入参数$job_name

###检测940系列是否有做drill_map 密码输出 by 吕康侠 2022/03/24
http://192.168.2.120:82/zentao/story-view-3951.html

喷锡工艺增加提醒
http://192.168.2.120:82/zentao/story-view-4332.html

2022.08.22
Song
1.增加输出tgz的镭射Ring检测 http://192.168.2.120:82/zentao/story-view-4478.html

20221110 by lyh
#1， 输出TGZ增加提醒项目，针对osp+化金的料号，抓取命名规则，输出TGZ提醒；请注意‘白油块’需按照化金制作，请检查资料。
#2，针对镀金板也加入提醒，输出TGZ提醒；请注意‘白油块’需按照化金制作，请检查资料。20221110

20221116 by lyh
#输出TGZ增加卡关，1，监测NPTH孔是否有套铜皮单边8mil。(输出内外TGZ都检测）如没有套铜皮提醒修改。
# 2，监测NPTH孔是否存在防焊开窗及档点。（输出外层TGZ检测）如未存在开窗及档点提醒修改。
# 3，监测NPTH孔对应的sgt-c,sgt-s层是否存在开窗。（输出外层TGZ检测）如未存在开窗提醒修改。 
# 5，输出TGZ增加检测二维码的正反（根据层别识别）。
#system("python /incam/server/site_data/scripts/lyh/sh_hdi_check_rules.py check_barcode_condition");合并到check_npth_hole_condition此中检测
#http://192.168.2.120:82/zentao/story-view-4696.html 20221116 by lyh

20221215 by lyh
#检测双面开窗孔是否制作塞孔 提示
http://192.168.2.120:82/zentao/story-view-4976.html

20221227 by lyh
1，输出埋孔树脂铝片（层名：b2-7.lp;2-7为变量)&树脂导气(b2-7...dq；2-7为变量)检测板边工具孔是否与埋孔层的工具孔在同一位置
a,在同一位置放行。
b,不在同一位置提醒且不让输出。
2，输出埋孔树脂铝片&通孔树脂铝片检测是否存在重孔。
a,无重孔放行
b,有重孔提醒且不让输出
3，输出通孔树脂铝片（层名：sz.lp/szsk-c.lp/szsk-s.lp/szsk2-1.lp/szsk2-2.lp/sz-c.lp/sz-s.lp )&树脂导气(层名：前缀与铝片一致，后缀...dq)检测板边工具孔是否与通孔层的工具孔在同一位置
a,在同一位置放行。
b,不在同一位置提醒且不让输出。
#http://192.168.2.120:82/zentao/story-view-5006.html 此项目改到输出tgz时检测 

20230105 by lyh
#http://192.168.2.120:82/zentao/story-view-5022.html
#3.输出TGZ时检测LED板有控深钻时外层是否按要求添加铜Pad 

20230105 by lyh
#http://192.168.2.120:82/zentao/story-view-5034.html
# 输出tgz时提示cam制作人 有控深铣的需要避铜

# 20241113 zl 打包tgz