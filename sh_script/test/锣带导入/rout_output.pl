#!/Perl/bin/perl -w
=header

锣带输出脚本
Ver 1.0 writed by Song chao 20180915
Ver 1.1 modify by Song 20190507 增加铣带影响其他step检测
Ver 1.2 modify by Song 20190508	尾数为1的为粗锣刀，补偿0.2mm进行检测。
Ver 2.0 modify by Song 20190509 增加平移输出，不拉伸单元外形
Ver 2.1 modify by Song 20190510 
	single_sr 设定为no 则单只拼版的无翻版指令M25 M01 ，但out_file文件中针对最后的钻孔添加M30指令，粗锣刀增加M02，M08，M47对类似阻抗条的铣刀失效；
	此项需求更改失败 
Ver 2.2 modify by Song 20190510 更改铣带input的背景颜色由黄色更改为蓝色	
Ver 2.3 modify by Song 20190522 单板资料复制到panel中时，使用坐标原点（datum）进行粘贴，更改为0 0
Ver 2.4 modify by Song	20190613 更改取坐标原点info信息中增加单位=mm信息，更改粘贴位置为相对坐标原点 
=cut

if (defined $ENV{INCAM_PRODUCT}) {
	use lib "/incam/release/app_data/perl";
} else  {
	use lib "$ENV{GENESIS_EDIR}/all/perl";
}
use lib "$ENV{GENESIS_EDIR}/all/perl";
use lib "//192.168.2.33/incam-share/incam/genesis/sys/scripts/Package";
use Tk;
use Tk::LabFrame;
use utf8;
use Encode;
use Tk::JPEG;
use Tk::PNG;
require Tk::BrowseEntry;
use HTTP::Request::Common;
use Data::Dumper;
use POSIX;
use Spreadsheet::ParseExcel;
use File::Copy;
use File::Spec;
print "\n";
my $path_curf = File::Spec->rel2abs(__FILE__);
print "C PATH = ",$path_curf,"\n";
my ($vol, $dirs, $file) = File::Spec->splitpath($path_curf);
my $cur_script_dir = $dirs;
if ($vol) {
	$cur_script_dir = $vol .$cur_script_dir;
}

binmode STDOUT, ":utf8";
#use incam;
use Genesis;
use mainVgt;
use VGT_Oracle;
$host = shift;
#$f = new incam($host);
$f = new Genesis($host);
$c = new mainVgt();
my $JOB = $ENV{JOB};
my $STEP = $ENV{STEP};

# ======================
if ( $^O ne 'linux' ) {
    our $scriptPath = "$ENV{SCRIPTS_DIR}/sys/scripts";
    our $jobsPath = "$ENV{GENESIS_DIR}/fw/jobs";
    our $userDir = "$ENV{GENESIS_DIR}/fw/jobs/$JOB/user";
    our $perlVer = "Z:/incam/Path/Perl/bin/perl.exe";
    our $pythonVer = "Z:/incam/Path/Python26/python.exe";
} else {
    our $scriptPath = "$ENV{SCRIPTS_DIR}/sys/scripts";
    our $jobsPath = "/incam/incam_db1/jobs";
    our $userDir = "$ENV{JOB_USER_DIR}";
    our $perlVer = "/opt/ActivePerl-5.14/bin/perl";
}

BEGIN
{
    # --连接HDI InPlan oracle数据库
    our  $o = new VGT_Oracle();
    our $dbc_inplan = $o->CONNECT_ORACLE('host'=>'172.20.218.193', 'service_name'=>'inmind.fls', 'port'=>'1521', 'user_name'=>'GETDATA', 'passwd'=>'InplanAdmin');
    if (! $dbc_inplan)
    {
        $c->Messages('warning', '链接数据库失败，无法取得工艺参数，请注意选择工艺参数');
    }
}

END
{
    # --断开Oracle连接
    $dbc_inplan->disconnect if ($dbc_inplan);
}

unless($JOB ){
	# song delete run in $STEP
	$f->PAUSE("The script must be run in a JOB !!");
	exit(0);
}

# 单个料号加入提醒  http://192.168.2.120:82/zentao/story-view-8267.html
if ($JOB =~ /ca1906obc78.*/){
	$c->Messages('warning',"型号：A19*C78，工艺要求1.0的反刃刀排刀需要放在粗锣之后，请仔细检查排刀顺序");
}

$f->INFO(angle_direction => 'ccw', entity_type => 'job',
         entity_path => "$JOB",
         data_type => 'STEPS_LIST');

my @steps = @{$f->{doinfo}{gSTEPS_LIST}};
my $showStep;
my @CheckStep;
my $board_process = '普通锣板参数';
$board_process = &get_process_by_job_name(); #自动取得对应的工艺信息
for(my $i = 0; $i<=$#steps; $i++)
{
	if ($steps[$i] eq "panel")
	{	
		$step_name = "$steps[$i]";
		#last;
	}
	if ($steps[$i] =~  /^set$/ || $steps[$i] =~ /^edit$/) {
		push @CheckStep,$steps[$i];
	}
}

for my $back (@CheckStep) {
	if ($back eq 'set') {
		$showStep = $back;
		last;
	}else{
		$showStep = $back;
	}
}

if ($step_name ne 'panel') {
	#code
	$f->PAUSE('must Run in Job With Panel Step');
	exit(0);
}

$f->INFO(angle_direction => 'ccw', entity_type => 'matrix',
         entity_path => "$JOB/matrix",
         data_type => 'ROW');

my @rlayers = ();
my @gROWname = @{$f->{doinfo}{gROWname}};
my @gROWlayer_type = @{$f->{doinfo}{gROWlayer_type}};
my @gROWcontext = @{$f->{doinfo}{gROWcontext}};

for (my $i=0; $i<=$#gROWname; $i++)
{
	if (($gROWlayer_type[$i] eq 'rout') && ($gROWcontext[$i] eq 'board'))
	{
		push(@rlayers,$gROWname[$i]);
	}
}


$f->INFO(units => 'mm', angle_direction => 'ccw', entity_type => 'step',
         entity_path => "$JOB/$step_name",
         data_type => 'SR');

my @gSRstep =  @{$f->{doinfo}{gSRstep}};			########拼板左下角最小值
my @gSRxmin =  @{$f->{doinfo}{gSRxmin}};
my @gSRymin =  @{$f->{doinfo}{gSRymin}};
my %step_position = ();

for (my $i=0; $i<=$#gSRstep; $i++)
{
	if ($gSRstep[$i] =~ /set/ || $gSRstep[$i] =~ /edit/)
	{
		my $length = sqrt(($gSRxmin[$i])**2 + ($gSRymin[$i])**2);
		@{$step_position{$length}} = ($gSRxmin[$i],$gSRymin[$i]);
	}
}

my @min = sort{$a<=>$b}keys(%step_position);
my $doffset_x = ${$step_position{$min[0]}}[0];
my $doffset_y = ${$step_position{$min[0]}}[1];

$f->INFO(units => 'mm',angle_direction => 'ccw', entity_type => 'step',	
         entity_path => "$JOB/$step_name",
         data_type => 'PROF_LIMITS');
$op_x_max = $f->{doinfo}{gPROF_LIMITSxmax};			########profile中心值
$op_x_center = $op_x_max / 2;
$op_y_max = $f->{doinfo}{gPROF_LIMITSymax}/2;
$op_y_center = $op_y_max / 2;

$f->INFO(units => 'mm', angle_direction => 'ccw', entity_type => 'step',
	 entity_path => "$JOB/$step_name",
	 data_type => 'SR',
	 parameters => "step");
my @step_order = @{$f->{doinfo}{gSRstep}};		#####取出step在S&R里面的排序用于set排刀
for(my $i=0; $i<=$#step_order; $i++)
{
	if ($step_order[$i] =~ /set/ || $step_order[$i] =~ /edit/)
	{
		our $set_order = $i + 1;
		last;
	}
}

# 获取用户名
$f->COM('get_user_name');
our $softuser = $f->{COMANS};
my $cmd="hostname";
my $ophost=`$cmd`;
print $ophost;
my $plat;
if ( $^O eq 'linux' ) {
	$plat = 'Linux' . '_' . "$ENV{INCAM_SERVER}";
	
} elsif ( $^O eq  'MSWin32' ) {
	#code   
	$plat = 'Windows';
	eval('use Win32::API;');
	my $username = Win32::LoginName();
	chomp($username);
	$softuser = $username . "_" . $softuser;
}


my $job_upper = uc($JOB);

#my $script_path = "/incam/server/site_data/scripts/hdi_scr/Output/NC";
my $script_path = "//192.168.2.33/incam-share/incam/genesis/sys/scripts/hdi-scr/Output";
my $defaults_path =  "d:/disk/rout/$job_upper";
my $images_path = "$script_path/img";

&iMkDir($defaults_path);

############   创建Tk用户交互界面，获取变量  #########
my $Version = '3.4.3';
my $mw = MainWindow->new(-title=>"锣带输出",-background=>'#9BDBDB');
my $icon = $mw->Photo('-format' => 'png',-file =>"$images_path/incam.png");#此处图片的路径可以是完整的路径
$mw->iconimage($icon);#设定窗口标题的ico图标
#$mw->resizable(0,0);
$mw->geometry("440x650+300+200");


$top  = $mw -> Frame(-background=>'#9BDBDB') ->pack();
$fre1 = $mw -> Frame(-background=>'#9BDBDB') ->pack();
$fre2 = $mw -> LabFrame(-background=>'#9BDBDB',
					  -label => "参数设置",
					  -foreground => 'blue',
					  -labelside => 'acrosstop',
					  -font => [-family=>'Times',-size =>10],
					  -width => 30) ->pack();

$fre3 = $mw -> LabFrame(-background=>'#9BDBDB',
					  -label => "涨缩值",
					  -foreground => 'blue',
					  -labelside => 'acrosstop',
					  -font => [-family=>'Times',-size =>10],
					  -width => 30) ->pack();

$fre4 = $mw -> LabFrame(-background=>'#9BDBDB',
					  -label => "零点偏移值mm",
					  -foreground => 'blue',
					  -labelside => 'acrosstop',
					  -font => [-family=>'Times',-size =>10],
					  -width => 30) ->pack();
					  
$listframe = $mw -> LabFrame(-background=>'#9BDBDB',
					  -label => "层别列表",
					  -foreground => 'blue',
					  -labelside => 'acrosstop',
					  -font => [-family=>'Times',-size =>10],
					  -width => 30) ->pack();				  

$bot = $mw -> Frame(-background=>'#9BDBDB') ->pack();

my $image1 = $top ->Photo('info',-file => "$images_path/sh_log.xpm");

my $pic1 = $top ->Label(-image => $image1)->pack(-side => 'left');
				
my $lab1 = $top ->Label(-background=>'#9BDBDB',-text => "锣带输出程序",
						-font => [-family=>'Times',-weight=>'bold',-size=>31],
						-width => 15)
						->pack(-side => 'top',-fill=>'both',-expand=>1);
						
my $lab2 = $top ->Label(-background=>'#9BDBDB',
						-font => [-size =>10],
						-width => 13)
						->pack(-side => 'left',-fill=>'both',-expand=>1);
						
my $lab3 = $top ->Label(-background=>'#9BDBDB',-text => "作者：Song  版本:$Version",
						-font => [-size =>10],
						-width => 5)
						->pack(-side => 'right',-fill=>'both',-expand=>1);
					
my $lab4 = $fre1 ->Label(-background=>'#9BDBDB',-text =>">>> 料号：$JOB <<<",
						-font => [-family=>'Times',-weight=>'bold',-size =>18],
						-foreground => 'blue',
						-relief => 'groove',
						-width => 31)
						->pack(-side => 'top',-fill=>'both',-expand=>1);

						
########参数设置框里面再划分框架
						
my $lfam1 = $fre2 -> Frame(-background=>'#9BDBDB') ->pack(-anchor=>'w');
my $lfam11 = $fre2 -> Frame(-background=>'#9BDBDB') ->pack(-anchor=>'w');
my $lfam2 = $fre2 -> Frame(-background=>'#9BDBDB') ->pack(-anchor=>'w');
my $lfam22 = $fre2 -> Frame(-background=>'#9BDBDB') ->pack(-anchor=>'w');
my $lfam23 = $fre2 -> Frame(-background=>'#9BDBDB') ->pack(-anchor=>'w');

my $process_frame = $fre2 -> Frame(-background=>'#9BDBDB') ->pack(-anchor=>'w');  #添加一个工艺选项的option  唐成 20210317 添加
$process_frame->Label(-text => "锣带参数工艺选项:",
                  -font => [-size =>11],
                  -background=>'#9BDBDB')
                ->pack(-side => 'left',-fill=>'both',-expand=>1);

#my @board_process_array = ('普通锣板参数','线圈板.LED板参数.无卤素','铜基板.铝基板.陶瓷板','半孔.PTH槽参数','LED高tg板电池板参数','金手指卡板参数');
my @board_process_array = ('普通锣板参数.LED板参数.通孔板','线圈板.无卤素.高TG.电池板','铜基板.铝基板.陶瓷板','半孔.PTH槽参数','金手指卡板参数','医疗板参数','Rogers（罗杰斯）板料（PTFE）','A86、D10');

$process_frame->Optionmenu(-font => [-size =>11],
                        -background=>'#9BDBDB',
                        -relief => 'groove',
                        -variable => \$board_process,
                        -options => [@board_process_array],-width=>25)
                    ->pack(-side => 'left',-fill=>'both',-expand=>1);
					
my $l1 = $lfam1->Label(-text => "输出STEP:",
					  -font => [-size =>11],
					  -background=>'#9BDBDB')
					->pack(-side => 'left',-fill=>'both',-expand=>1);


my $l2 = $lfam1->Optionmenu(-font => [-size =>11],
							-background=>'#9BDBDB',
							-relief => 'groove',
							-variable => \$step_name,
							-options => [@steps],
							-command => sub{&click_change_zero})
						->pack(-side => 'left',-fill=>'both',-expand=>1);

my $checkStep = $lfam1->Label(-text => "检测:",
					  -font => [-size =>11],
					  -background=>'#9BDBDB')
					->pack(-side => 'left',-fill=>'both',-expand=>1);


my $StepList = $lfam1->Optionmenu(-font => [-size =>11],
							-background=>'#9BDBDB',
							-relief => 'groove',
							-variable => \$showStep,
							-options => [@steps])
						->pack(-side => 'left',-fill=>'both',-expand=>1);
						
my $l3 = $lfam1->Label(-text => "涨缩位置:",
					  -font => [-size =>11],
					  -background=>'#9BDBDB')
					->pack(-side => 'left',-fill=>'both',-expand=>1);

my @scale = ('中心','零点'); 
my $scale_position = $scale[0];

my $l4 = $lfam1->Optionmenu(-font => [-size =>11],
							-background=>'#9BDBDB',
							-relief => 'groove',
							-width => 3,
							-variable => \$scale_position,
							-options => [@scale])
						->pack(-side => 'left',-fill=>'both',-expand=>1);

#my $l41 = $lfam1->Label( -font => [-size =>11],
#				 -background=>'#9BDBDB',
#				 -width => 8)
#				->pack(-side => 'left',-fill=>'both',-expand=>1);

							
my $l5 = $lfam11->Label(-text => "镜像输出:",
					  -font => [-size =>11],
					  -background=>'#9BDBDB')
					->pack(-side => 'left',-fill=>'both',-expand=>1);
					
#my @mirror_value = ('No','X方向','Y方向');
my @mirror_value = ('No','X方向');

my $mirror = 'No';
foreach my $tmp (@mirror_value) {
		$lfam11->Radiobutton(-text     => $tmp,
				         -variable => \$mirror,
					   -relief => 'groove',
					   -background => '#9BDBDB',
					   -font => [-size =>11],
					   -width => 7,
					   -value => $tmp)
					->pack(-side => 'left',-fill=>'both',-expand=>1);

}

my $l51 = $lfam11->Label(-text => "     输出方式:",
					  -font => [-size =>11],
					  -background=>'#9BDBDB')
					->pack(-side => 'left',-fill=>'both',-expand=>1);
					
#my @mirror_value = ('No','X方向','Y方向');
my @opmode_value = ('拉伸','平移');

my $l52 = $lfam11->Optionmenu(-font => [-size =>11],
							-background=>'#9BDBDB',
							-relief => 'groove',
							-width => 3,
							-variable => \$op_mode,
							-options => [@opmode_value])
						->pack(-side => 'left',-fill=>'both',-expand=>1);

#my $l51 = $lfam11->Label( -font => [-size =>11],
#				  -background=>'#9BDBDB',
#				  -width => 11)
#				->pack(-side => 'left',-fill=>'both',-expand=>1);

my $l6 = $lfam2 ->Label(-text => "输出路径:",
					-background=>'#9BDBDB',
					-font => [-size =>11])
					->pack(-side => 'left',-fill=>'both',-expand=>1);
										
					
my $l7 = $lfam2->Entry(-font => [-size =>11],
						-background => 'white',
						-relief => 'groove',
						-width => 37,
						-textvariable =>\$defaults_path)
					->pack(-side => 'left',-fill=>'both',-expand=>1);
					
my $image  = $lfam2 ->Photo('-format' => 'png',-file =>"$images_path/OpenJob.png");
my $l8 = $lfam2 ->Button(
						 -activeforeground=>'red',
						 -background=>'#9BDBDB',
						 -image => $image,
						 -highlightbackground=>'black',
						  -command => sub {dirDialog($lfam2)})
						->pack(-side => 'left',-fill=>'both',-expand=>1);
						
my $l9 = $lfam22->Label(-text => "数据上传:",
                  -font => [-size =>11],
                  -background=>'#9BDBDB',)
                ->pack(-side => 'left',-fill=>'both',-expand=>1);
my $upload_erp = 1;
my $sel_frm = $lfam22->Checkbutton(-text => " 上传(锣程|锣刀)至ERP",-variable => \$upload_erp,
                                               -font => [-size =>11],-bg => '#9BDBDB',-fg => 'red',
                                               -command => sub {})->pack(-side => 'left', -padx => 5,-pady => 2);
my $half_knife = &get_rout_kinfe;
my $half_sel_frm = $lfam22->Checkbutton(-text => "锣刀寿命减半",-variable => \$half_knife,
                                               -font => [-size =>11],-bg => '#9BDBDB',-fg => 'red',
                                               -command => sub {})->pack(-side => 'left', -padx => 5,-pady => 2);       

my $l91 = $lfam23->Label(-text => "LED板:",
                  -font => [-size =>11],
                  -background=>'#9BDBDB',)
                ->pack(-side => 'left',-fill=>'both',-expand=>1);
my $op_ccd_rout = 0;
my $ccd_rout = $lfam23->Checkbutton(-text => "出货单元CCD锣带",-variable => \$op_ccd_rout,
                                               -font => [-size =>11],-bg => '#9BDBDB',-fg => 'blue',
                                               -command => \&ccd_select)->pack(-side => 'left', -padx => 5,-pady => 2);

#  === 以下变量用于函数 ccd_select === # 
my $op_ccd_top = 0;
my $ccd_side; 
sub dirDialog {
    my $w = shift;
    #my $ent = shift;
    my $dir;
    my $dpath = $l7->get();
    $dir = $w->chooseDirectory(-initialdir => "$dpath");
    if (defined $dir and $dir ne '') {
	$l7->delete(0, 'end');
	$l7->insert(0, $dir);
	$l7->xview('end');
    }
}
######################
 

######################
my $dscale_x = "1.000";
my $dscale_y = "1.000";
my $scale_num = 'None';
my $get_zs_list = &get_mysql_scale;
my @zs_array = qw();
print Dumper(\$get_zs_list);
my @all_zs_list = @$get_zs_list;
for(my $i=0; $i<=$#all_zs_list; $i++)
{
	my %cur_list = %{$all_zs_list[$i]};
	#print '@cur_list',$cur_list{'Zscode'};
	push @zs_array,$cur_list{'Zscode'};
}
push @zs_array,'None';
push @zs_array,'LS';
my $scale_status = 'readonly';



my $sh_site_entry = $fre3->BrowseEntry(-variable => \$scale_num,
                                                    -choices => \@zs_array,
                                                    -label        => '选涨缩代码:',
                                                    # -labelFont       => 'SimSun 11 bold',
                                                    -labelBackground => '#9BDBDB',
                                                    -background => '#9BDBDB',
                                                    -font=> 'SimSun 11 bold',
                                                    -selectbackground=>'blue',
                                                    -relief=>"ridge",
                                                    -listwidth=>20,
                                                    -listheight=>10,
                                                    -browsecmd => sub{&click_select_button},
                                                    -width => 5,
                                                    -state=>"readonly",
                                                    )->pack(-side => 'left',-fill=>'both',-expand=>1);
#my $l101 = $fre3 ->Label(-text => "涨缩代码:",
#					  -font => [-size =>11],
#					  -background=>'#9BDBDB')
#					->pack(-side => 'left',-fill=>'both',-expand=>1);
#
#my $l111 = $fre3 ->Entry(-font => [-size =>11],
#						-background => 'white',
#						-relief => 'groove',
#						-width => 10,
#						-textvariable =>\$scale_num,
#						-command => \&get_scale_value)
#					->pack(-side => 'left',-fill=>'both',-expand=>1);

# 设定涨缩界面
my $l10;
my $l11;
my $l13;
my $l14;
&scale_frame_set($scale_status);
#my $l10 = $fre3 ->Label(-text => "X涨缩:",
#					  -font => [-size =>11],
#					  -background=>'#9BDBDB')
#					->pack(-side => 'left',-fill=>'both',-expand=>1);
#
#my $l11 = $fre3 ->Entry(-font => [-size =>11],
#						-background => 'white',
#						-relief => 'groove',
#						-width => 10,
#						-textvariable =>\$dscale_x,
#						-state=>$x_scale_status,
#						)
#					->pack(-side => 'left',-fill=>'both',-expand=>1);
#
##my $l12 = $fre3 ->Label(-background=>'#9BDBDB',
##						-font => [-size =>11],
##						-width => 12)
##						->pack(-side => 'left',-fill=>'both',-expand=>1);
#my $l13 = $fre3 ->Label(-text => "Y涨缩:",
#					  -font => [-size =>11],
#					  -background=>'#9BDBDB')
#					->pack(-side => 'left',-fill=>'both',-expand=>1);
#
#my $l14 = $fre3 ->Entry(-font => [-size =>11],
#						-background => 'white',
#						-relief => 'groove',
#						-width => 10,
#						-textvariable =>\$dscale_y,
#						-state=>$y_scale_status,
#						)
#					->pack(-side => 'left',-fill=>'both',-expand=>1);
#

my $l15 = $fre4 ->Label(-text => "X偏移:",
					  -font => [-size =>11],
					  -background=>'#9BDBDB')
					->pack(-side => 'left',-fill=>'both',-expand=>1);

my $l16 = $fre4 ->Entry(-font => [-size =>11],
						-background => 'white',
						-relief => 'groove',
						-width => 13,
						-textvariable =>\$doffset_x)
					->pack(-side => 'left',-fill=>'both',-expand=>1);

my $l17 = $fre4 ->Label(-background=>'#9BDBDB',
						-font => [-size =>11],
						-width => 12)
						->pack(-side => 'left',-fill=>'both',-expand=>1);
my $l18 = $fre4 ->Label(-text => "Y偏移:",
					  -font => [-size =>11],
					  -background=>'#9BDBDB')
					->pack(-side => 'left',-fill=>'both',-expand=>1);

my $l19 = $fre4 ->Entry(-font => [-size =>11],
						-background => 'white',
						-relief => 'groove',
						-width => 13,
						-textvariable =>\$doffset_y)
					->pack(-side => 'left',-fill=>'both',-expand=>1);


########list框架

my $list = $listframe ->Scrolled('Listbox', -scrollbars=>'e')->pack(-side => 'left');
$list->configure(-selectmode => "extended",
				   -background=>'white',
				   -selectbackground=>'blue',
				   -relief => "groove",
				   -width => 26,
				   -height => 7,
				   -font => [-size =>19],
				);
$list->insert('end',@rlayers);	

my $but1 = $listframe ->Button(-text  => "所有",
				 -font=>[-size=>12],
				 -activeforeground=>'red',
				 -background=>'#9BDBDB',
				 -height=>1,
				 -width=>5,
				 -relief => 'groove',	
				 -command=> \&select_all)
				 ->pack(-side => 'top',-padx=>7,-pady=>15);
			 
my $but2 = $listframe ->Button(-text  => "清除",
				 -font=>[-size=>12],
				 -activeforeground=>'red',
				 -background=>'#9BDBDB',
				 -height=>1,
				 -width=>5,
				 -relief => 'groove',
				 -command=> \&select_clear)
				 ->pack(-side => 'top',-padx=>7,-pady=>15);		 


my $but3 = $listframe ->Button(-text  => "回读",
				 -font=>[-size=>12],
				 -activeforeground=>'red',
				 -background=>'#9BDBDB',
				 -height=>1,
				 -width=>5,
				 -relief => 'groove',
				 -command=> \&reinput_)
				 ->pack(-side => 'top',-padx=>7,-pady=>15);	

my $bud1 = $bot ->Button(-text  => "输出",
			 -font=>[-size=>10,],
			 -activeforeground=>'red',
			 -borderwidth => 3,
			 -height=>1,
			 -width=>6,
			 -relief => 'raised',
			 -highlightbackground=>'black',
			 -command=> \&output_mode)
			 ->pack(-side => 'left',-fill=>'both',-pady=>5,-padx=>83);

my $bud2 = $bot ->Button(-text  => "退出",
			 -font=>[-size=>10,],
			 -activeforeground=>'red',
			 -borderwidth => 3,
			 -height=>1,
			 -width=>6,
			 -relief => 'raised',
			 -highlightbackground=>'black',
			 -command=> sub{exit})
			 ->pack(-side => 'left',-fill=>'both',-pady=>5,-padx=>83);	
MainLoop;


#### 窗口居中
sub win_mid{
my $x_resolution = $mw->screenwidth;
my $y_resolution = $mw->screenheight;
$x = $mw->reqwidth;		#取真实宽度和高度
$y = $mw->reqheight;
print "$x,$y\n";
my $xp = $x_resolution/2 - $x/2;
my $yp = $y_resolution/2 - $y/2;
#$mw->geometry("400x300+300+200");
}	


# 选择panel以外的数据时候更改零点 
sub click_change_zero{
	if ($step_name eq "panel"){
		$doffset_x = ${$step_position{$min[0]}}[0];
		$doffset_y = ${$step_position{$min[0]}}[1];
	} 
	else{
		$doffset_x = 0;
		$doffset_y = 0;
	}	
}

#######涨缩值部分
sub scale_frame_set {
	my ($scale_status) = @_;

	$l10 = $fre3 ->Label(-text => "X涨缩:",
						  -font => [-size =>11],
						  -background=>'#9BDBDB')
						->pack(-side => 'left',-fill=>'both',-expand=>1);
	
	$l11 = $fre3 ->Entry(-font => [-size =>11],
							-background => 'white',
							-relief => 'groove',
							-width => 10,
							-textvariable =>\$dscale_x,
							-state=>$scale_status,
							)
						->pack(-side => 'left',-fill=>'both',-expand=>1);
	
	$l13 = $fre3 ->Label(-text => "Y涨缩:",
						  -font => [-size =>11],
						  -background=>'#9BDBDB')
						->pack(-side => 'left',-fill=>'both',-expand=>1);
	
	$l14 = $fre3 ->Entry(-font => [-size =>11],
							-background => 'white',
							-relief => 'groove',
							-width => 10,
							-textvariable =>\$dscale_y,
							-state=>$scale_status,
							)
						->pack(-side => 'left',-fill=>'both',-expand=>1);
}

########选择所有层

sub select_all{
$list->selectionSet (0, 'end' );
}

########清除选择

sub select_clear{
$list->selectionClear (0, 'end' );
}

sub click_select_button {
	print '123' . "\n";
	if ($scale_num eq 'LS') {
		destroy $l10;
		destroy $l11;
		destroy $l13;
		destroy $l14;
		&scale_frame_set('normal');
		return;
	} else {
		destroy $l10;
		destroy $l11;
		destroy $l13;
		destroy $l14;
		&scale_frame_set('readonly');
	}

	if ($scale_num eq 'None') {
		$dscale_x = '1.000';
		$dscale_y = '1.000';
		$op_mode = '涨缩';
		return;
	}
	
	$op_mode = '平移';
	
	for(my $i=0; $i<=$#all_zs_list; $i++)
	{
		my %cur_list = %{$all_zs_list[$i]};
		if ($cur_list{'Zscode'} eq $scale_num) {
			$dscale_x = $cur_list{'ScaleX'};
			$dscale_y = $cur_list{'ScaleY'};
		}
	}
}

#####输出程序

sub check_rout_other_step{
	
	my @selectlayers = @_;

	# -->检测锣带是否存在多锣  --AresHe 20191101
	my $get_result = &CheckRout(@selectlayers);
	if ($get_result ne 0) {
		return 1;
	}
	
    if ($op_ccd_rout == 0) {
		#$f->COM("disp_off");
		&defined_genesis_par;
		&delete_create_layer('rout_profile','profile_surface','rout_chain','touch_chain');
		$f->COM("create_layer,layer=rout_chain,context=board,type=rout,polarity=positive,ins_layer=");
		&p2surface;
		# 没有拼版的取消检查
		if (@dsteps) {&check_touch;}		
	}
	#$f->COM("disp_on");
	return 0;
}

sub delete_create_layer{
	my @defaults_layers = @_;					####需要生成的layer
	$f->COM("open_entity,job=$JOB,type=step,name=$step_name,iconic=no");
	$f->AUX("set_group,group=$f->{COMANS}");
	$f->VOF;
	foreach my $lll (@defaults_layers)
	{
		$f->COM("delete_layer,layer=$lll");
	}
	$f->VON;
}

sub defined_genesis_par{	
	&change_unit_mm;

	our %resteps =();			####获取分散的steps
	$f->INFO(units => 'mm', entity_type => 'step', entity_path => "$JOB/$step_name", data_type => 'REPEAT');
	my @gREPEATstep = @{$f->{doinfo}{gREPEATstep}};
	my @gREPEATxmin = @{$f->{doinfo}{gREPEATxmin}};
	my @gREPEATymin = @{$f->{doinfo}{gREPEATymin}};
	my @gREPEATxmax = @{$f->{doinfo}{gREPEATxmax}};
	my @gREPEATymax = @{$f->{doinfo}{gREPEATymax}};
	
	my @gREPEATxa = @{$f->{doinfo}{gREPEATxa}};  
	my @gREPEATya = @{$f->{doinfo}{gREPEATya}};      
	my @gREPEATangle = @{$f->{doinfo}{gREPEATangle}}; 
	my @gREPEATmirror = @{$f->{doinfo}{gREPEATmirror}}; 

	for(my $i=0; $i<=$#gREPEATstep; $i++)
	{
		@{$resteps{$i}} = ($gREPEATstep[$i],$gREPEATxmin[$i],$gREPEATymin[$i],$gREPEATxmax[$i],$gREPEATymax[$i], $gREPEATxa[$i],$gREPEATya[$i] ,$gREPEATangle[$i] ,$gREPEATmirror[$i]);
	}
	
	my %count;
	our @dsteps = grep{ ++$count{$_} < 2; }@gREPEATstep;				#######去除重复的step
	#$f->PAUSE("@dsteps");
	#$f->PAUSE (%resteps");
}

sub p2surface {
	#my $select_rout = $list->get($list->curselection());
	my @aff_layer_index = $list->curselection();
	my @selectlayers = ();				######选择的层
	foreach my $k (@aff_layer_index) {
		push(@selectlayers,$list->get("$k"));
	}
	our %step_datum;
	# 有铣带设计的step #
	our %check_step;
	foreach my $i (@dsteps)
	{
		$f->COM("open_entity,job=$JOB,type=step,name=$i,iconic=no");
		$f->AUX("set_group,group=$f->{COMANS}");
		&change_unit_mm;
		$f->COM("clear_layers");
		$f->COM("profile_to_rout,layer=rout_profile,width=10");
		$f->COM("display_layer,name=rout_profile,display=yes,number=1");
		$f->COM("work_layer,name=rout_profile");
		$f->COM("sel_cut_data,det_tol=25.4,con_tol=25.4,rad_tol=2.54,filter_overlaps=no,delete_doubles=no,use_order=yes,ignore_width=yes,
				ignore_holes=none,start_positive=yes,polarity_of_touching=same");
		$f->COM("display_layer,name=rout_profile,display=no,number=1");
		# 取是否rou都设计在以及拼版中，如设计在二级拼版，则报错 
		# 循环多个铣带 都复制到rout_chain 

		foreach my $select_rout (@selectlayers) {
			$f->INFO(entity_type => 'layer', entity_path => "$JOB/$i/$select_rout", data_type => 'FEAT_HIST');

			if ($f->{doinfo}{gFEAT_HISTtotal} ne '0') {
				$check_step{$i} = '';
				#$f->COM("compensate_layer,source_layer=$select_rout,dest_layer=rout_chain,dest_layer_type=document");
				$f->COM("compensate_layer,source_layer=$select_rout,dest_layer=chain.$select_rout,dest_layer_type=document");
				# 尾数是1的为粗锣刀，输出后按0.2补偿，依照此项进行过滤，加多0.2
				$f->COM("display_layer,name=chain.$select_rout,display=yes,number=1");
				$f->COM("work_layer,name=chain.$select_rout");
				$f->COM("filter_reset,filter_name=popup");
				$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=line\;arc");
				$f->COM("filter_set,filter_name=popup,update_popup=no,polarity=positive");
				$f->COM("filter_set,filter_name=popup,update_popup=no,include_syms=*1");
				$f->COM("filter_area_strt");
				$f->COM("filter_area_end,layer=,filter_name=popup,operation=select,area_type=none,inside_area=no,intersect_area=no");
				$f->COM("get_select_count");
				if ($f->{COMANS} != '0') {
                                        # 2023.03.02 尾数为1的补偿值均更改为0.15
					#整体0.4，单边0.2 -->补偿0.15 整体0.3 单边0.15
					$f->COM("sel_resize,size=300,corner_ctl=no");
				}
				
				$f->COM("merge_layers,source_layer=chain.$select_rout,dest_layer=rout_chain,invert=no");
				&delete_create_layer("chain.$select_rout");
			} else {
				$f->INFO(entity_type => 'layer', entity_path => "$JOB/$i/$select_rout", data_type => 'FEAT_HIST', options => "break_sr"); 
				if ($f->{doinfo}{gFEAT_HISTtotal} ne '0') {
					&message_show('$select_rout二级拼版，存在铣带设计,是否退出？');
				}
			}
		}
		$f->COM("editor_page_close");
		$f->INFO(units => 'mm', entity_type => 'step', entity_path => "$JOB/$i", data_type => 'DATUM');
		@{$step_datum{$i}} = ($f->{doinfo}{gDATUMx},$f->{doinfo}{gDATUMy});

	}	
		$f->VOF();
		$f->COM("delete_layer,layer=rout_profile+++");
		$f->VON();
}

sub check_touch {
	my $check_yn = 'ok';
	
	# my $select_rout = $list->get($list->curselection());
	$f->COM("open_entity,job=$JOB,type=step,name=$step_name,iconic=no");
	$f->AUX("set_group,group=$f->{COMANS}");
	
	$f->COM("clear_layers");
	$f->COM("flatten_layer,source_layer=rout_profile,target_layer=profile_surface");
	my $last_step = '';
	foreach my $i ( sort{$a<=>$b} keys(%resteps)) {

		# 不存在铣带则跳过检查
		if ( not exists $check_step{${$resteps{$i}}[0]}) {
			next;
		}
		my $psc_step = ${$resteps{$i}}[0];
		&delete_create_layer("panel.$i", "profile_cu.$i");
		if ($last_step ne $psc_step) {
			$f->COM("open_entity,job=$JOB,type=step,name=$psc_step,iconic=no");
			$f->AUX("set_group,group=$f->{COMANS}");
			$f->COM("display_layer,name=rout_chain,display=yes,number=1");
			$f->COM("work_layer,name=rout_chain");
			&change_unit_mm;		
			$f->COM("snap_mode,mode=off");
			$f->COM("sel_buffer_copy,x_datum=${$step_datum{$psc_step}}[0],y_datum=${$step_datum{$psc_step}}[1]");
			print "xxxxxxxxxxx\n";
			print $psc_step;
			print "xxxxxxxxxxx\n";
			#$f->COM("sel_buffer_copy,x_datum=$step_datum{$psc_step}[0],y_datum=$step_datum{$psc_step}[1]");
			#$f->COM("sel_buffer_copy,x_datum=0,y_datum=0");
			$f->COM("editor_page_close");
			$f->COM("open_entity,job=$JOB,type=step,name=$step_name,iconic=no");
			$f->AUX("set_group,group=$f->{COMANS}");
		}
		$last_step = $psc_step;
		$f->COM("clear_layers");
		&change_unit_mm;
		
		my $xc = (${$resteps{$i}}[3] - ${$resteps{$i}}[1])/2+${$resteps{$i}}[1];						##选中step的中心
		my $yc = (${$resteps{$i}}[4] - ${$resteps{$i}}[2])/2+${$resteps{$i}}[2];
		$f->COM("display_layer,name=profile_surface,display=yes,number=1");
		$f->COM("work_layer,name=profile_surface");		
		$f->COM("sel_copy_other,dest=layer_name,target_layer=profile_cu.$i,invert=no,dx=0,dy=0,size=0,x_anchor=0,y_anchor=0,rotation=0,mirror=none");
		$f->COM("display_layer,name=profile_cu.$i,display=yes,number=1");
		$f->COM("work_layer,name=profile_cu.$i");			
		$f->COM("sel_single_feat,operation=select,x=$xc,y=$yc,tol=0,cyclic=no");
		#$f->COM("sel_net_feat,operation=select,x=$xc,y=$yc,tol=0,use_ffilter=no");
		$f->COM("get_select_count");
		if ($f->{COMANS} ne '0') {			
			$f->COM("sel_delete");
			$f->COM("sel_single_feat,operation=select,x=$xc,y=$yc,tol=0,cyclic=no");
			$f->COM("get_select_count");
			if ($f->{COMANS} ne '0') {			
				$f->COM("sel_delete");				
			}
		} else {
			&message_show('铺铜不正确,是否退出？');
		}
		$f->COM("create_layer,layer=panel.$i,context=misc,type=signal,polarity=positive,ins_layer=");
		$f->COM("display_layer,name=panel.$i,display=yes,number=1");
		$f->COM("work_layer,name=panel.$i");
		$f->COM("snap_mode,mode=off");
		# 是否旋转 		# 是否镜像
		$f->COM("sel_buffer_options,mode=merge_layers,rotation=${$resteps{$i}}[7],mirror=${$resteps{$i}}[8]");
		$f->COM("sel_buffer_paste,x=${$resteps{$i}}[5],y=${$resteps{$i}}[6]");
		$f->COM("filter_reset,filter_name=popup");
		$f->COM("sel_ref_feat,layers=profile_cu.$i,use=filter,mode=touch,pads_as=shape,f_types=line\;pad\;surface\;arc\;text,polarity=positive\;negative,include_syms=,exclude_syms=");
		$f->COM("get_select_count");
		if ($f->{COMANS} ne '0') {
			$f->COM("sel_copy_other,dest=layer_name,target_layer=touch_chain,invert=no,dx=0,dy=0,size=0,x_anchor=0,y_anchor=0,rotation=0,mirror=none");
			$check_yn = 'error';
		} 

		&delete_create_layer("panel.$i", "profile_cu.$i");

	}
	if ($check_yn eq 'ok') {
		&delete_create_layer('rout_profile','profile_surface','rout_chain');
		&ok_mesage;
	} elsif ($check_yn eq 'error') {
		&error_mesage;
	}
}

sub change_unit_mm{
	$f->COM("get_units");
	my $cunit = $f->{COMANS};
	$f->COM("units,type=mm") if ($cunit eq "inch");
}

#####回读程序

sub reinput_{
	my @rfiles=();
	my $reinput_path = $l7->get();
	my $reinput_file = "$reinput_path/reinput";
	system("rm -rf $reinput_file");
	opendir(DIR, $reinput_path) || die "Can't open directory $reinput_path"; 
	my @rrs = readdir(DIR);
	close(DIR);
	foreach my $aaa (@rrs)
	{
		if ($aaa !~ /^\./)
		{
			push(@rfiles,$aaa);
		}
	}

	$smw1 = $mw->Toplevel(-background=>'#9BDBDB');
	$smw1->title("锣带回读");
	$smw1->resizable(0,0);
	my $subtop  = $smw1 -> Frame(-background=>'#9BDBDB') ->pack();
	my $sfl0  = $smw1 -> Frame(-background=>'#9BDBDB') ->pack();
	my $sfl1  = $smw1 -> Frame(-background=>'#9BDBDB') ->pack();
	my $slab1 = $subtop ->Label(-background=>'#9BDBDB',-text => "锣带列表",
							-font => [-family=>'Times',-weight=>'bold',-size=>20],
							-width => 10)
							->pack(-side => 'top',-fill=>'both',-expand=>1);

	$slist = $sfl0 ->Scrolled('Listbox', -scrollbars=>'se')->pack(-side => 'left');
						 
	$slist->configure(-selectmode => "extended",
					   -background=>'white',
					   -selectbackground=>'blue',
					   -relief => "groove",
					   -width => 20,
					   -height => 7,
					   -font => [-size =>15],
					);

	$slist->insert('end',@rfiles);	


	my $sbu1 = $sfl1 ->Button(-text => "确定", -command=> \&routinput_)
								->pack(-side => 'left',-fill=>'both',-padx=>18);
									   
	my $sbu2 = $sfl1  ->Button(-text => "退出",-command => [$smw1 => 'destroy'])
								->pack(-side => 'right',-fill=>'both',-padx=>18);
	}

	######锣带回读子程序
	sub routinput_ {
	my $reinput_path = $l7->get();

	my $reinput_file = "$reinput_path/reinput";
	print "$reinput_file\n";
	if (-e $reinput_file ) {
		system("rm -rf $reinput_file");
		mkdir("$reinput_file");
	}
	else {
		mkdir("$reinput_file");
	}

	my @rlayer_index = $slist->curselection();
	my @relayers = ();				######选择的层
	foreach my $i (@rlayer_index)
	{
	push(@relayers,$slist->get("$i"));
	}


	foreach my $rrlayer (@relayers)
	{
	#system("cat $reinput_path/$rrlayer | sed 's/;//g' | sed 's/DRL//g' | sed 's/BC.*//g' > $reinput_path/reinput/$rrlayer");
		 my $source_file = "$reinput_path/$rrlayer";
		 open FILE,$source_file or die $!;
		 {
				local $/=undef;
				$content= <FILE>;
				close FILE;
		 }
			$content =~ s/;//g;
			$content =~ s/DRL//g;
			$content =~ s/BC.*//g;
			$content =~ s/M48,.*//g;
			$content =~ s/%\nM252(.*)C(.*)/T21C$2\n%\nT21\n$1/g;
			$content =~ s/M252(.*)C(.*)/$1/g;
		my $des_file = "$reinput_path/reinput/$rrlayer";
			 if ( open(SESAME,">$des_file") or die("$!")) {
			 print SESAME "$content\n";
			 }	
			close SESAME;
	
	
		$f->COM("clear_layers");
#incam	
=pod	
	$f->COM("input_create,path=$reinput_path/reinput/$rrlayer");
	$f->COM("input_identify,path=,job=$JOB,script_path=/tmp/input.$$,gbr_ext=no,drl_ext=no,gbr_units=auto,drl_units=auto,unify=yes,break_sr=no,\gbr_wtp_filter=*,drl_wtp_filter=*,gbr_wtp_units=auto,drl_wtp_units=auto,wtp_dir=,have_wheels=yes,wheel=,gbr_consider_headlines=yes,drl_consider_headlines=yes,board_size_x=0,board_size_y=0");
	$f->COM("input_manual_reset");
	$f->COM("input_manual_set,path=$reinput_path/reinput/$rrlayer,job=$JOB,step=$step_name,format=Excellon2,data_type=ascii,units=mm,coordinates=absolute,zeroes=trailing,nf1=3,nf2=0,decimal=yes,separator=nl,tool_units=mm,layer=$rrlayer,wheel=,wheel_template=,nf_comp=0,multiplier=1,text_line_width=0.0024,signed_coords=no,break_sr=no,drill_only=no,merge_by_rule=no,threshold=200,resolution=3,drill_type=unspecified,parent_path=,force_params=no");
	$f->COM("input_manual,script_path=/tmp/input.$$");
=cut	
#Genesis
		my $ip_step = $step_name;
		if($rrlayer =~ /jp-rout/ || $rrlayer =~ /ccd-rout/ ) {
			$ip_step = $showStep;
		} 
		$f->COM("input_copy,path=$reinput_path/reinput/$rrlayer,
				job=$JOB,delete_source=no");
		$f->COM("input_manual_reset");
		# --转换小写回读，否则会报错  --20191118 AresHe
		$rrlayer = lc $rrlayer;
		$f->COM("input_manual_set,path=$reinput_path/reinput/$rrlayer,
				job=$JOB,step=$ip_step,format=Excellon2,data_type=ascii,
				units=mm,coordinates=absolute,zeroes=trailing,nf1=3,nf2=3,decimal=yes,
				separator=nl,tool_units=mm,layer=$rrlayer,wheel=,wheel_template=,
				nf_comp=0,multiplier=1,text_line_width=0.0024,signed_coords=no,
				break_sr=yes,drill_only=no,merge_by_rule=no,threshold=200,resolution=3");
		#}
		$f->COM("input_manual,script_path=");
		#
		#
		#foreach my $rrlayer (@relayers)
		#{
			$f->COM("matrix_layer_type,job=$JOB,matrix=matrix,layer=$rrlayer,type=rout");
			$f->COM("matrix_layer_context,job=$JOB,matrix=matrix,layer=$rrlayer,context=board");
			# 回读比对comper	
			system "$pythonVer", "$scriptPath/hdi-scr/Output/output_rout/compare_input_rout.py","$JOB","$ip_step","$rrlayer";	
			
	}
	
	$smw1 -> destroy();
}


sub message_show {
	my ($show_text) = @_;
	my $err = $mw->messageBox(-icon => 'warning',-message => $show_text,-title => '提示',-type => 'YesNo');
	return if $err eq "No";
	$f->COM("disp_on");
	exit;
}

sub error_mesage {
	my $err = $mw->messageBox(-icon => 'warning',-message => '拼板step的Rout刀有锣到其他step，请检查touch_chain层！',-title => '提示',-type => 'ok');
	#return if $err eq "No";
	exit;
}

sub ok_mesage {
	my $ok = $mw->messageBox(-icon => 'info',-message => '检查完毕，OK！',-title => '提示',-type => 'YesNo');
	return if $ok eq "No";
	#exit;
}

sub confirm_box {
	my ($title_show, $confirm_text) = @_;
	my $mwcb = MainWindow->new;
	$mwcb->geometry("200x100");
	$mwcb->title($title_show);

	$mwcb->Label(-text => $confirm_text)->pack(-side => "left");
	$mwcb->Entry(-background => 'black', -foreground => 'white')->pack(-side => "right");
	$mwcb->Button(-text => "确定")->pack(-side => 'bottom',-fill=>'both',-padx=>18);
	MainLoop;

}

sub output_mode{
	
	
	my @aff_layer_index = $list->curselection();
	my @selectlayers = ();				######选择的层

	foreach my $i (@aff_layer_index) {
	push(@selectlayers,$list->get("$i"));
	}

	#$a = "";
	 #defined $ENV(INCAM_PRODUCT)
	if($selectlayers[0] eq ""){
		my $message = $mw ->Dialog(-title=>'Dialog Box',
							   -text =>'请选择输出层！',
							   -default_button => 'Ok',
							   -buttons => ['Ok'],
							   -bitmap => 'error')->Show();
		return $message;
	}
	
	#if ($op_mode eq "拉伸")  {
	#	&confirm_box("确认窗口", "请输入用户名");
	#}
    #if ($c->GET_USER_NAME() ne '47773' && $c->GET_USER_NAME() ne '44839')
    #{
		
		###取镜像值
	if ($mirror eq "No") {
		$xmirror = 'no';
		$ymirror = 'no';
	} elsif($mirror eq "X方向"){
		$xmirror = 'yes';
		$ymirror = 'no';
	} elsif($mirror eq "Y方向"){
		$xmirror = 'no';
		$ymirror = 'yes';
	}

	#my $result = grep /^rout$/, @selectlayers;

	my $scale_x = $l11->get();				###X涨缩
	my $scale_y = $l14->get();				###Y涨缩

	my $offset_x = $l16->get();				###X偏移
	my $offset_y = $l19->get(); 			###Y偏移

	if ($scale_x != 1 or $scale_y != 1) {
		foreach my $cur_rout (@selectlayers) {
			#system "//192.168.2.33/incam-share/incam/Path/Python26/python.exe","//192.168.2.33/incam-share/incam/genesis/sys/scripts/sh_script/hdi_scr/Output/output_rout/compare_mirror_info.py",$job_name;
			my $get_result = system "$pythonVer", "$scriptPath/hdi-scr/Output/output_rout/compare_mirror_info.py",$JOB,$cur_rout;
			#my $get_result = `//192.168.2.33/incam-share/incam/Path/Python26/python.exe D:\\genesis\\sys\\scripts\\hdi_scr\\Output\\output_rout\\compare_mirror_info.py $JOB`;
			my $result_num = &get_result_num($get_result);
			# 1——对应无法读取文件 100——非镜像 101——X镜像 102——Y镜像
			print '$result_num' . $result_num. "\n";
			
			if ($result_num == 1) {
				# === 提醒确认是否继续输出
				&message_show('是否退出?')
			} elsif ($result_num == 100){
				if( $xmirror eq 'yes' or $ymirror eq 'yes') {
					$c->Messages('warning',"对比网盘正常锣带，镜像的选择不正确，网盘为非镜像");
					return;
				}
			} elsif ($result_num == 101){
				if( $xmirror ne 'yes' or $ymirror eq 'yes') {
					$c->Messages('warning',"对比网盘正常锣带，镜像的选择不正确，网盘为X镜像");
					return;
				}
			} elsif ($result_num == 102){
				if( $xmirror eq 'yes' or $ymirror ne 'yes') {
					$c->Messages('warning',"对比网盘正常锣带，镜像的选择不正确，网盘为Y镜像");
					return;
				}
			} else {
				# === 退出值不已知
				$c->Messages('warning',"对比正常锣带，返回值不是已知数，请反馈程序组");
				return;
			}
		}
	}
	
	if ($softuser !~ /89627/ && $JOB !~ /b51908pbal4|sd580200t02/) {		
		my $get_result = &check_rout_other_step(@selectlayers);
		if ($get_result ne 0) {
			return 1;
		}
	}	
	

	$f->COM("units,type=mm");
    our $current_path = $l7->get();            ###输出的具体目录
	if ( -d $current_path ) {
	} else {
		mkdir($current_path);
	}
	my $scale_poseng;
	####取涨缩位置
	if ($scale_position eq "中心") {
		$scale_center_x = $op_x_center;
		$scale_center_y = $op_y_center;
		$scale_poseng = 'Center';
	} else {
		$scale_center_x = 0;
		$scale_center_y = 0;
		$scale_poseng = 'Orig';
	}



	
	#my $incam_user = $ENV{INCAM_USER};			###输出涨缩信息给ncr out_file取
	our $incam_user = "cc";			###输出涨缩信息给ncr out_file取
	
	if (defined $ENV{INCAM_USER}) {
		$incam_user = $ENV{INCAM_USER};
	} else {
		$f->COM('get_user_name');
		$incam_user = $f->{COMANS};
		chmod $incam_user;
	}

	my $ipname = `hostname`;
	my $tmp = "/tmp";
	my $logpath;
	if (defined $ENV{INCAM_PRODUCT}) {
		$logpath = $ENV{JOB_USER_DIR};
	} else 	{
		$logpath = "$ENV{GENESIS_DIR}/fw/jobs/$JOB/user";
		#$jobpath = `dbutil path jobs $JOB`;
		#my $logpath = "$jobpath/user";
		$tmp = "c:/tmp";
	}
	
	#print "$op_mode";
	#$f->PAUSE("$ENV{GENESIS_DIR}");


	### 不改变单元大小进行位置拉伸 # Start #
	my ($op_step, $op_scalex, $op_scaley, $mod_eng);
	
	if ($op_mode eq "拉伸")  {
		$op_step = $step_name;
		$op_scalex = $scale_x;
		$op_scaley = $scale_y;
		$mod_eng = "Scale";
	} elsif ($op_mode eq "平移") {
		my $zsword;
		if ( $JOB =~ /(zs*)-*/ ) {
			$zsword = $1;
		} else {
			$zsword = 'zs';
		}
		$f->COM("copy_entity,type=step,source_job=$JOB,source_name=$step_name,dest_job=$JOB,dest_name=$zsword.$step_name,dest_database=");
		$f->COM("open_entity,job=$JOB,type=step,name=$zsword.$step_name,iconic=no");
		$f->AUX("set_group,group=$f->{COMANS}");
		&change_unit_mm;
		$f->COM("sr_popup");
		$f->COM("sr_tab_scaling,x_anchor=$scale_center_x,y_anchor=$scale_center_y,x_scale=$scale_x,y_scale=$scale_y,scale_on=center");
		$op_step = "$zsword.$step_name";
		$op_scalex = 1;
		$op_scaley = 1;
		$mod_eng = "Move";
	}
	my $logfile	= "$logpath/rout_output_log";
	#$f->PAUSE($logfile);
	my $yyear = strftime "%Y-%m-%d", localtime;
	my $dday = strftime "%H:%M:%S", localtime;
	our $local_time = "$yyear $dday";
	our $output_message = "$tmp/$JOB-rout-message";
	
	open(OUT, ">$output_message");
	# print OUT "/User:$incam_user Date:$local_time Scale:X=$scale_x Y=$scale_y Anchor=$scale_position X/2=$scale_center_x  Y/2=$scale_center_y	Mirror:$mirror";
	print OUT "/User:$incam_user Date:$local_time Scale:X=$scale_x Y=$scale_y Anchor=$scale_poseng X/2=$scale_center_x  Y/2=$scale_center_y	Mirror:$mirror Mode:$mod_eng";	
	close(OUT);
	
	### 不改变单元大小进行位置拉伸 # End #

	#$f->COM("set_subsystem,name=Nc-Manager");
	our %rout_kanife_paramete = &get_excel_kanife_parameters($board_process); #取得rou参数表
	unless(%rout_kanife_paramete){
		$c->Messages('warning',"没有取到  $board_process  工艺的刀具补偿信息，请检查锣带文件刀具表");
	}

	foreach my $i (@selectlayers) {
		# --检查锣带销钉是否对称
		&check_pin_symmetry($i);
		my $ncPre = "nc_".$i;
		my $pre_name = '';
		if ($scale_num ne 'None') {
			$pre_name = $scale_num."-";
		}
		if ( defined $ENV{INCAM_PRODUCT} ) {
			$f->PAUSE("incam");
			$f->VOF;
				$f->COM("nc_delete,layer=$i,ncset=$ncPre");
			$f->VON;
			$f->COM("nc_create,ncset=$ncPre,device=excellon_hdi,lyrs=$i,thickness=0");
			$f->COM("nc_set_advanced_params,layer=$i,ncset=$ncPre,parameters=(rout_arc_as_ij=no)(out_exc_old_sr_syntax=no)");
			$f->COM("nc_set_current,job=$JOB,step=$op_step,layer=$i,ncset=$ncPre");
			$f->COM("nc_set_file_params,output_path=$current_path,output_name=$JOB.$i,zeroes=trailing,units=mm,tool_units=mm,nf1=3,nf2=3,decimal=yes,modal_coords=no,single_sr=yes,sr_zero_set=no,repetitions=sr,incremental=no,ext_layer=ncr-drill,sr_zero_layer=,ccw=no,short_lines=none,allow_no_chain_f=no,no_chain_as_slot=no,keep_table_order=yes,max_arc_angle=180,comp_short_slot=no,gscale_file_name=,layer_datum=bottom_left,gscle_align_angle=0,gscl_offset_x=0,gscl_offset_y=0");
			$f->COM("nc_register,angle=0,xoff=0,yoff=0,version=1,xorigin=$offset_x,yorigin=$offset_y,xscale=$op_scalex,yscale=$scale_y,xscale_o=$op_scaley,yscale_o=$scale_center_y,xmirror=$xmirror,ymirror=$ymirror");			
			$f->COM("nc_order,serial=1,sr_line=$set_order,sr_nx=1,sr_ny=1,mode=lrbt,snake=yes");
			#$f->COM("top_tab,tab=NC Parameters Page");
			#$f->COM("open_sets_manager,test_current=no");
			$f->PAUSE("请确认是否需要调整rout板顺序");
			$f->COM("nc_cre_output,layer=$i,ncset=$ncPre");
			$f->VOF;
			$f->COM("delete_layer,layer=_nc_$i\_out_");
			$f->VON;
		} else {
			#$f->PAUSE("Genesis");
			# --输出时料号名切换大写，后缀不变  --20191118  AresHe
            our $JobName = uc($JOB);
            if (($i eq 'jp-rout' || $i eq 'ccd-rout') && $op_ccd_rout == 1) {
				# === 出货单元光学CCD锣带输出 ===
				
				&output_ccd_rout($i);
				#my $output_file = "$current_path/$JobName".uc($i);
				#if ($i eq 'jp.rou' ) { $output_file = "$current_path/$JobName.$i";}
				#&add_config_data($output_file,%rout_kanife_paramete);
				
			} else {
				$f->COM("ncrset_page_open");
				$f->COM("ncrset_cur,job=$JOB,step=$op_step,layer=$i,ncset=");
				$f->VOF;
					$f->COM("ncrset_delete,name=$ncPre");
				$f->VON;
				$f->COM("ncrset_create,name=$ncPre");
				$f->COM("ncrset_cur,job=$JOB,step=$op_step,layer=$i,ncset=$ncPre");
				$f->COM("ncr_set_machine,machine=excellon_hdi,thickness=0");
				$f->COM("ncr_set_params,format=excellon2,zeroes=trailing,units=mm,tool_units=mm,nf1=3,nf2=3,decimal=yes,modal_coords=no,single_sr=yes,sr_zero_set=no,repetitions=sr,drill_layer=ncr-drill,sr_zero_drill_layer=,break_sr=no,ccw=no,short_lines=none,press_down=no,last_z_up=16,max_arc_ang=180,sep_lyrs=no,allow_no_chain_f=no,keep_table_order=yes");
	
				$f->COM("ncr_register,angle=0,mirror=$xmirror,xoff=0,yoff=0,version=1,xorigin=$offset_x,yorigin=$offset_y,xscale=$op_scalex,yscale=$op_scaley,xscale_o=$scale_center_x,yscale_o=$scale_center_y");
				$f->COM("ncr_order,sr_line=$set_order,sr_nx=1,sr_ny=1,serial=1,optional=no,mode=lrbt,snake=yes,full=1,nx=0,ny=0");
				# === 2023.03.11 转自多层，使用上次排刀序进行输出 ===
				my $rout_table_list = "$logpath/$i"."_table_list";				
				my $now_table_list_path = "$logpath/$i"."_now_table_list";				
				&sort_table_by_last($i,$rout_table_list,$now_table_list_path);				
				$f->PAUSE("please check rout Order");
				
				$f->COM("ncr_table_close");		
				$f->COM("ncr_cre_rout");
				$f->COM("ncr_ncf_export,dir=$current_path,name=$pre_name$JobName.$i");
	
				# 2023.03.10 参考多层 输出指定锣带table 到user 路径唐成
				$f->COM("ncrset_units,units=mm");
				$f->COM("ncr_report,path=$rout_table_list");
				# 检测粗锣精修顺序 http://192.168.2.120:82/zentao/story-view-6803.html
				my $res = system "$pythonVer", "$scriptPath/hdi-scr/Output/output_rout/check_rou_index.py","check_index","$JOB","$i"."_table_list";
				if($res != 0){					
					return;
				}
				
				# 20200106李家兴添加，输出report,用来计算锣程
				$f->COM("ncrset_units,units=mm");
				my $report_file_path = "$current_path/$JobName.$i.report";
				$f->COM("ncr_report,path=$report_file_path");
				$f->COM("ncrset_units,units=inch");
				if ($softuser !~ /89627/) {
					system "//192.168.2.33/incam-share/incam/Path/Python26/python.exe","//192.168.2.33/incam-share/incam/genesis/sys/scripts/sh_script/nc_path/nc_path.py",$i,$report_file_path;
					system("rm -rf $report_file_path");
					#code
				}
				my $strTemp = "";
				open(FILE,"<$current_path/$pre_name$JobName.$i");
				while(<FILE>) {
			
					#先删除指定行（用空替换）
					$_ =~ s/^\/G05\n$//g;
					#再删除空行（用空替换）
					$_ =~ s/^\/G40\n$//g;
					$strTemp = $strTemp.$_;
				 }
				
				open(FILE,">$current_path/$pre_name$JobName.$i");
				print FILE $strTemp;
				close FILE;

                #锣带参数自动匹配
				&add_config_data("$current_path/$pre_name$JobName.$i", %rout_kanife_paramete);
			}
		}
		#$f->COM("set_subsystem,name=1-Up-Edit");	
		unlink("$output_message");
		
		# CCD锣带增加光学点检测及转换 http://192.168.2.120:82/zentao/story-view-6457.html
	if ($i =~ /^ccd|rout-cdc|rout-cds/ ) {
			my $res = system "$pythonVer", "$scriptPath/hdi-scr/Output/output_rout/re_write_ccd.py","$current_path","$pre_name$JobName.$i";	
				if($res != 0){
					$c->Messages('info',"CCD精修锣带参数写入文件失败！！！");					
					unlink "$current_path/$pre_name$JobName.$i";
					return;
				}
		}
		# 盖板作业增加M47指令，涨缩锣带自动对比正式锣带添加M47和ET字样
			# http://192.168.2.120:82/zentao/story-view-6605.html			
		if ($op_step =~ /panel/ && $i eq 'rout'){			
			my $res = system "$pythonVer", "$scriptPath/hdi-scr/Output/output_rout/re_write_M47_et.py","$current_path","$pre_name$JobName.$i","$scale_num","$JobName";	
				if($res != 0){
					$c->Messages('info',"写入M47&&ET指令失败！！！");					
					unlink "$current_path/$pre_name$JobName.$i";
					return;
				}
		}		
		
		# set输出锣带部分参数更新 
		if ($op_step =~ /set|edit/) {
			my $strTemp = "";
				open(FILE,"<$current_path/$pre_name$JobName.$i");
				while(<FILE>) {
					if ($_ !~ /M25\n$|M01\n$|M02\n$|M08\n$/){
						$strTemp = $strTemp.$_;
					}					
				 }
				
				open(FILE,">$current_path/$pre_name$JobName.$i");
				print FILE $strTemp;
				close FILE;
		}
		
		
		# --盲锣板输出自动化 AresHe 2021.10.29
		# --来源需求:http://192.168.2.120:82/zentao/story-view-3343.html
		if ($i =~ /^rout-cd[c|s]$|^ccd-rout-cd[c|s]$}/) {
			if (-f "$current_path/$pre_name$JobName.$i") {
				open(DATAFILE, "<$current_path/$pre_name$JobName.$i");
				my @DATALIST = <DATAFILE>;
				close DATAFILE;
				
				# --删除原文件
				unlink "$current_path/$pre_name$JobName.$i";
				
				# --保存文件
				open(WRITEFILE, ">$current_path/$pre_name$JobName.$i");
				
				my $flag;
				my $tool_count = 0;
				my $cp_count = 0;
				my $blind_tool;
				foreach my $des(@DATALIST){
					chomp $des;
					if ($des eq "M48") {
						$flag = "head";
					}elsif($flag eq "head"){
						if ($des =~ /\%/) {
							$flag = "boby";
						}
					}
					
					if ($flag eq "head") {
						if ($des =~ /^T\d+/) {
							if ($des =~ /ZZ$/i) {
								my @tool_head = split(";",$des);
								$blind_tool = $tool_head[0];
							}else{
								if ($des =~ /^T\d+C/) {
									my @tool_head = split("C",$des);
									$tool_count = $tool_count + 1;
									my $tool = $tool_count;
									if ($tool < 10) {
										$tool = "0".$tool;
									}
									print WRITEFILE "T".$tool."C".$tool_head[1]."\n";
								}elsif($des =~ /^T\d+;/){
									my @tool_head = split(";",$des);
									$tool_count = $tool_count + 1;
									my $tool = $tool_count;
									if ($tool < 10) {
										$tool = "0".$tool;
									}
									print WRITEFILE "T$tool;$tool_head[1]\n";
								}
							}
						}else{
							if ($des =~ /^CP(\d+)(.*)/) {
								$cp_count = $1 * 1 - 1;
								my $tool = $cp_count;
								if ($tool < 10) {
									$tool = "0".$tool;
								}
								print WRITEFILE "CP".$tool.$2."\n";
							}else{
								print WRITEFILE "$des\n";
							}
						}
					}elsif($flag eq "boby"){
						if ($des eq $blind_tool) {
							print WRITEFILE "M127\n";
							print WRITEFILE "T98\n";
						}elsif($des ne "G05"){
							if ($des =~ /^T(\d+)/) {
								if ($1 > 1) {
									if ($des =~ /^T\d+$/) {
										my $tool = $1 * 1;
										$tool = $tool - 1;
										
										my $new_tool = $tool;
										if ($tool < 10) {
											$new_tool = "0".$tool;
										}
										print WRITEFILE "T$new_tool\n";
									}elsif($des =~ /^T(\d+)(C.*)/){
										my $tool = $1 * 1;
										$tool = $tool - 1;
										
										my $new_tool = $tool;
										if ($tool < 10) {
											$new_tool = "0".$tool;
										}
										print WRITEFILE "T".$new_tool.$2."\n";
									}
								}
							}else{
								print WRITEFILE "$des\n";
							}
						}
					}
				}
				close WRITEFILE;
			}
		}

		############## 输出记录
	    my $dbc_m = $o->CONNECT_MYSQL('host'=>'192.168.2.19', 'dbname'=>'hdi_engineering', 'port'=>'3306', 'user_name'=>'root', 'passwd'=>'k06931!');
		if (! $dbc_m)
		{
			$c->Messages('warning', '"工程数据库"连接失败-> 写入日志程序终止!');
			#exit(0);
			return;
		}

		open(OUT, ">>$logfile");
		if (-s "$logfile")
		{
		print OUT "\n";
		}
	
		print OUT "------------->>> $local_time\t$JOB\t$step_name\t\t$incam_user\t  at\tpc : $ipname\n
		$JOB,$i,$mirror,$offset_x,$offset_y,$scale_center_x,$scale_center_y,$scale_x,$scale_y,$mod_eng,$board_process,now(),$softuser,$ophost,$plat,$Version,$scale_num";
		
		#foreach my $i (@selectlayers)
		#{	
			#printf OUT "%-15s, 镜像:%s,\t偏移:%s,%s,\t涨缩中心(%s,%s),\tx涨缩：%s,\ty涨缩：%s\n ,\t涨缩方式: %s", $i,$mirror,$offset_x,$offset_y,$scale_center_x,$scale_center_y,$scale_x,$scale_y,$op_mode;
			#printf OUT "%-15s, Mirror:%s,\tOffset:%s,%s,\tScale_center:%s,%s,\txScale：%s,\t yScale：%s ,\t Scale_mode: %s\n", $i,$mirror,$offset_x,$offset_y,$scale_center_x,$scale_center_y,$scale_x,$scale_y,$mod_eng;
		my $sql = "insert into rout_output_log
		(job_name,layer,mirror,offset_x,offset_y,scale_center_x,scale_center_y,scale_x,scale_y,scale_mode,scale_num,param,log_time,creator,localhost,app_version)
		values('$JOB','$i','$mirror','$offset_x','$offset_y','$scale_center_x','$scale_center_y','$scale_x','$scale_y','$mod_eng','$scale_num','$board_process',now(),'$softuser','$ophost','$Version')";        
		my $sth = $dbc_m->prepare($sql);#结果保存在$sth中
		$sth->execute() or die "无法执行SQL语句:$dbc_m->errstr";
		#}
		close(OUT);
		$dbc_m->disconnect if ($dbc_m);  
		# if ($op_ccd_rout != 1) {
		# 	# 20200106李家兴添加，用来输出锣程,移至输出后立即执行
		# 	system "//192.168.2.33/incam-share/incam/Path/Python26/python.exe","//192.168.2.33/incam-share/incam/genesis/sys/scripts/sh_script/nc_path/nc_path_hdi.py",$current_path;
		# }
		
		# --不增加换行会导致COM命令失效。增加换行 song add 2022.01.04
		#print "\n";
		if ($scale_num ne "None") {
			my $get_result = system "$pythonVer", "$cur_script_dir/compare_rout.py",$JOB,$i,$scale_num,"$current_path/$pre_name$JobName.$i";
			my $result_num = &get_result_num($get_result);
			# 1——对应无法读取文件 100——非镜像 101——X镜像 102——Y镜像
			print '$result_num' . $result_num. "\n";
			if ($result_num == 1) {
				&message_show('是否退出?')
			}
		}
 	}
	
	if ($upload_erp == 1)
    {
        &uploadRoutData();
    }else{
        $c->Messages('info',"锣带输出完成！！！");
		# exit;
    }        
    return ;
	
	#my $message1 = $mw ->messageBox(-icon => 'info',-title => 'Message',-message => "锣带输出完成！！！");
	#return $message1;
}


sub sort_table_by_last{
	my ($i,$rout_table_list,$now_table_list_path) = @_;
	#20210201 添加识别以前的刀具排序 唐成
	my @nc_table_rou_list;
	# if($i =~ /^rout\d*$/){
	# --匹配所有rou命名
	if($i =~ /rou/){
		open(TABLE_LIST,"<$rout_table_list");
		my @file_lines = <TABLE_LIST>;
		if(scalar(@file_lines) > 0){

			close(TABLE_LIST);
			my $in_Second_part = 0;
			my $in_first_part = 0;
			my $first_part_underline_num = 0;  #如果显示了3次下滑线一个刀具表已经读完需要退出
			my $second_part_underline_num = 0;  #如果显示了3次下滑线一个刀具表已经读完需要退出

			#first 表保存
			for my $file_line(@file_lines){
				if($file_line =~ /^NC-Table \(First part\)/){
					$in_first_part = 1;
				}
				if( $in_first_part == 1){
					if($file_line =~ /^------------------------------------------------------------/){
						$first_part_underline_num++;
					}
				}
				if($first_part_underline_num == 3){
					last;
				}
				#$f->PAUSE("333333333333333->$first_part_underline_num  --- $file_line ");
				if($file_line =~  /^\d+/){
					my @split_table = split(" ",$file_line);
					my %nc_table_hash;
					$nc_table_hash{index} = $split_table[0];
					$nc_table_hash{Type} = $split_table[1];
					$nc_table_hash{Step} = $split_table[2];
					$nc_table_hash{Chain_Num} = $split_table[3];
					$nc_table_hash{Rout_Size} = $split_table[4];
					$nc_table_hash{Comp} = $split_table[5];
					$nc_table_hash{Flg} = $split_table[6];
					$nc_table_hash{CW} = $split_table[7];
					$nc_table_hash{Path_Count} = $split_table[8];
					my $lline = scalar(@split_table);
					#$f->PAUSE("pppppppppppp->$lline -- @split_table  -3:- $split_table[2] ");
					$nc_table_rou_list[scalar(@nc_table_rou_list)] = {%nc_table_hash};
				}
			}

			#second 表保存
			for my $file_line(@file_lines){
				if($file_line =~ /^NC-Table \(Second part\)/){
					$in_Second_part = 1;
				}
				if($in_Second_part == 1){
					if($file_line =~ /^------------------------------------------------------------/){
						$second_part_underline_num++;
					}
				}
				if($second_part_underline_num == 3){
					last;
				}
				#$f->PAUSE("444444:$file_line  --->   $in_Second_part");
				if($in_Second_part == 1){
					if($file_line =~  /^\d+/){
						my @secont_table_part = split(" ",$file_line);
						#比对下标相同的加入到hash
						for(my $i=0; $i < scalar(@nc_table_rou_list);$i++){
							my %table_part = %{$nc_table_rou_list[$i]};
							#$f->PAUSE("ssssssss->$secont_table_part[0] == $table_part{index}   -> $nc_table_rou_list[$i]  i:$i");
							if($secont_table_part[0] == $table_part{index}){
								$table_part{Group} = $secont_table_part[1];
								$table_part{Hole_Mode} = $secont_table_part[2];
								$table_part{Option} = $secont_table_part[3];
								$table_part{Dup} = $secont_table_part[4];
								$table_part{Tool_Size} = $secont_table_part[5];
								$table_part{Comp_Fact} = $secont_table_part[6];
								$table_part{Spin_Speed} = $secont_table_part[7];
								$table_part{Feed_Rate} = $secont_table_part[8];
								$nc_table_rou_list[$i] = {%table_part};
								#$f->PAUSE("$table_part{index} -> $table_part{Group}");
								last;
							}
						}
					}elsif($file_line =~ /^Registration parameters/){
						last;
					}
				}
			}

			#$f->PAUSE("$rout_table_list --> @nc_table_rou_list");
			#运行下创建rout 导出未排列的锣带刀具表
			$f->COM("ncrset_units,units=mm");
			$f->COM("ncr_cre_rout");
			#$f->PAUSE("99999999999999999:$now_table_list_path");
			$f->COM("ncr_report,path=$now_table_list_path");
			#打开没有排列顺序刀具表文件
			open(NOW_TABLE_LIST,"<$now_table_list_path") or die "没有锣带刀具文件";
			my @unsort_rout_fill_lines = <NOW_TABLE_LIST>;
			close(NOW_TABLE_LIST);
			#unlink($now_table_list_path);


			#first 表保存
			my $now_table_in_first_part = 0;
			my $now_table_first_part_underline_num=0;
			my @now_rout_unsort_list;
			#unsort rout table list first
			for my $file_line(@unsort_rout_fill_lines){
				if($file_line =~ /^NC-Table \(First part\)/){
					$now_table_in_first_part = 1;
				}
				if( $in_first_part == 1){
					if($file_line =~ /^------------------------------------------------------------/){
						$now_table_first_part_underline_num++;
					}
				}
				if($now_table_first_part_underline_num == 3){
					last;
				}
				if($file_line =~  /^\d+/){
						my @split_table = split(" ",$file_line);
						my %nc_table_hash;
						$nc_table_hash{index} = $split_table[0];
						$nc_table_hash{Type} = $split_table[1];
						$nc_table_hash{Step} = $split_table[2];
						$nc_table_hash{Chain_Num} = $split_table[3];
						$nc_table_hash{Rout_Size} = $split_table[4];
						$nc_table_hash{Comp} = $split_table[5];
						$nc_table_hash{Flg} = $split_table[6];
						$nc_table_hash{CW} = $split_table[7];
						$nc_table_hash{Path_Count} = $split_table[8];
						#$f->PAUSE("pppppppppppp->$lline -- @split_table  -3:- $split_table[2] ");
						$now_rout_unsort_list[scalar(@now_rout_unsort_list)] = {%nc_table_hash};
				}
			}

			#unsort rout table list secont
			my $now_table_in_secont_part = 0;
			my $now_table_secont_part_underline_num=0;
			for my $file_line(@unsort_rout_fill_lines){
					if($file_line =~ /^NC-Table \(Second part\)/){
						$now_table_in_secont_part = 1;
					}
					if($now_table_in_secont_part == 1){
						if($file_line =~ /^------------------------------------------------------------/){
							$now_table_secont_part_underline_num++;
						}
					}
					if($now_table_secont_part_underline_num == 3){
						last;
					}
					if($now_table_in_secont_part == 1){
						if($file_line =~  /^\d+/){
							my @secont_table_part = split(" ",$file_line);
							#比对下标相同的加入到hash
							for(my $i=0; $i < scalar(@now_rout_unsort_list);$i++){
								my %table_part = %{$now_rout_unsort_list[$i]};
								#$f->PAUSE("ssssssss->$secont_table_part[0] == $table_part{index}   -> $nc_table_rou_list[$i]  i:$i");
								if($secont_table_part[0] == $table_part{index}){
									$table_part{Group} = $secont_table_part[1];
									$table_part{Hole_Mode} = $secont_table_part[2];
									$table_part{Option} = $secont_table_part[3];
									$table_part{Dup} = $secont_table_part[4];
									$table_part{Tool_Size} = $secont_table_part[5];
									$table_part{Comp_Fact} = $secont_table_part[6];
									$table_part{Spin_Speed} = $secont_table_part[7];
									$table_part{Feed_Rate} = $secont_table_part[8];
									$now_rout_unsort_list[$i] = {%table_part};
									last;
								}
							}
						}elsif($file_line =~ /^Registration parameters/){
							last;
						}
					}
			}

			#以没有排列锣刀具的列表进行
			$f->COM("get_units");
			my $my_unit = $f->{COMANS};
			if($my_unit eq "mm"){
				$f->COM("units,type=inch");
			}

			$f->COM("ncrset_units,units=mm");
			$f->COM("ncr_table_open");
			$f->COM("ncr_table_reset");
			#记录没有匹配到上一次刀具表的数组，用于提示
			my @un_matching_rou_array;
			foreach my $unsort_table_row(@now_rout_unsort_list){
				my %unsort_table_row_hash = %{$unsort_table_row};
				#$f->PAUSE("size:$unsort_table_row_hash{Rout_Size}");
				#记录是否有匹配到并重新排刀
				my $reset_rout_tool = 0;

				#上一次排列好的刀具表
				foreach my $sort_table_row (@nc_table_rou_list){
					my %sort_table_row_hash = %{$sort_table_row};
					#$f->PAUSE("qqqqqqqqqqqqqqqkey->$sort_table_row_hash{index} -> >$sort_table_row_hash{Group}");
					#出料index 其他全部一致就使用上传记录的序号(Path_Count 一定要设置小数精度和去绝对值不然有些刀具无法匹配到)
					# 2023.03.11 step都是panel类时，沿用上次排序（panel，zs.panel）
					if($unsort_table_row_hash{Type} eq $sort_table_row_hash{Type} and ($unsort_table_row_hash{Step} eq $sort_table_row_hash{Step} or ($unsort_table_row_hash{Step} =~ /panel/ and $sort_table_row_hash{Step} =~ /panel/)) and
					   $unsort_table_row_hash{Chain_Num} eq $sort_table_row_hash{Chain_Num} and $unsort_table_row_hash{Rout_Size} eq $sort_table_row_hash{Rout_Size} and
					   $unsort_table_row_hash{Comp} eq $sort_table_row_hash{Comp} and $unsort_table_row_hash{Flg} eq $sort_table_row_hash{Flg} and
					   $unsort_table_row_hash{CW} eq $sort_table_row_hash{CW} and  abs(sprintf("%.3f",$unsort_table_row_hash{Path_Count})) eq abs(sprintf("%.3f",$sort_table_row_hash{Path_Count})) and
					   $unsort_table_row_hash{Group} eq $sort_table_row_hash{Group} and $unsort_table_row_hash{Hole_Mode} eq $sort_table_row_hash{Hole_Mode} and
					   $unsort_table_row_hash{Option} eq $sort_table_row_hash{Option} and $unsort_table_row_hash{Dup} eq $sort_table_row_hash{Dup} and
					   $unsort_table_row_hash{Tool_Size} eq $sort_table_row_hash{Tool_Size} and $unsort_table_row_hash{Comp_Fact} eq $sort_table_row_hash{Comp_Fact} and
					   $unsort_table_row_hash{Spin_Speed} eq $sort_table_row_hash{Spin_Speed} and $unsort_table_row_hash{Feed_Rate} eq $sort_table_row_hash{Feed_Rate}){
							#$f->PAUSE("type:$unsort_table_row_hash{Type} : $sort_table_row_hash{Type} step:$unsort_table_row_hash{Step} : $sort_table_row_hash{Step}  Chain_Num:$unsort_table_row_hash{Chain_Num} : $sort_table_row_hash{Chain_Num}   Rout_Size:$unsort_table_row_hash{Rout_Size} : $sort_table_row_hash{Rout_Size}   Comp:$unsort_table_row_hash{Comp} : $sort_table_row_hash{Comp}   Flg:$unsort_table_row_hash{Flg} : $sort_table_row_hash{Flg}");
							#$f->PAUSE("CW:$unsort_table_row_hash{CW} : $sort_table_row_hash{CW}  Path_Count:$unsort_table_row_hash{Path_Count} : $sort_table_row_hash{Path_Count}  Group:$unsort_table_row_hash{Group} : $sort_table_row_hash{Group}  Hole_Mode:$unsort_table_row_hash{Hole_Mode} : $sort_table_row_hash{Hole_Mode} Option:$unsort_table_row_hash{Option} : $sort_table_row_hash{Option}  Dup:$unsort_table_row_hash{Dup} : $sort_table_row_hash{Dup}");
							#$f->PAUSE("Tool_Size:$unsort_table_row_hash{Tool_Size} : $sort_table_row_hash{Tool_Size}   Comp_Fact:$unsort_table_row_hash{Comp_Fact} : $sort_table_row_hash{Comp_Fact}  Spin_Speed:$unsort_table_row_hash{Spin_Speed} : $sort_table_row_hash{Spin_Speed}   Feed_Rate:$unsort_table_row_hash{Feed_Rate} : $sort_table_row_hash{Feed_Rate}");
							#孔数量和锣带数量命令里面是分开写的，输出刀具表和genesis窗口里面是放在一个栏位，如果Type是Hole 就填 count孔数量，path填0，如果Type是chain就填写path锣刀路径，count填0
							my $path_count = 0;
							my $count = 0;
							if($unsort_table_row_hash{Type} eq "Hole"){
								$count = $unsort_table_row_hash{Path_Count};
							}elsif($unsort_table_row_hash{Type} eq "Chain"){
								$path_count = $unsort_table_row_hash{Path_Count};
							}
							#有的时候输出的刀具表路径长度信息是负数，直接将其转为正数（测试不会影响实际锣带，刀具尺寸不能乱改，会影响实际输出锣带的刀具尺寸）
							if($path_count < 0){
								$path_count = abs($path_count);
							}

							#flag
							my $my_flag = $unsort_table_row_hash{Flg};
							if($my_flag eq "-"){#是一个横杠表示空没有填写,要填0
								$my_flag = 0;
							}
							#cw 如果cw是空就填入no,(打印出的刀具表与刀具排版全部相反，刀具面板是yes输出时就是no，所以要与输出时相反)
							my $my_cw = $unsort_table_row_hash{CW};
							if($my_cw eq "No"){
								$my_cw = "yes";
							}elsif($my_cw eq "Yes"){
								$my_cw = "no";
							}elsif($my_cw eq "-"){
								$my_cw = "no";
							}
							#创建一盒hash用于将里面的参数全部转换成小写填入参数
							my %temp_table_dat;
							foreach my $get_kay(keys(%unsort_table_row_hash)){
								$temp_table_dat{$get_kay} = lc($unsort_table_row_hash{$get_kay});
							}
							#锣带列表如果是-就设置为0
							my $my_Chain_Num = $temp_table_dat{Chain_Num};
							if($my_Chain_Num eq "-"){
								$my_Chain_Num = 0;
							}

							#录制命令在输出刀具表没有找到的参数 chain2录制出来全是chain2=0 ，parent没有参数录制出来全是parent=-1，spiral录制出来全部是spiral=none
						#my $mmmc = "ncr_table_set,index=$temp_table_dat{index},type=$temp_table_dat{Type},step_name=$temp_table_dat{Step},chain=$my_Chain_Num,chain2=0,size=$temp_table_dat{Rout_Size},comp=$temp_table_dat{Comp},path=$path_count,count=$count,flag=$my_flag,cw=$my_cw,tool_size=$temp_table_dat{Tool_Size},duplicate=$temp_table_dat{Dup},parent=-1,comp_factor=$temp_table_dat{Comp_Fact},spindle_speed=$temp_table_dat{Spin_Speed},feed_rate=$temp_table_dat{Feed_Rate},spiral=none,mode=$temp_table_dat{Hole_Mode},group=$temp_table_dat{Group},order=$sort_table_row_hash{index},optional=$temp_table_dat{Option}";
							#$f->PAUSE("mmmmm:$mmmc");
							$f->COM("ncr_table_set,index=$temp_table_dat{index},type=$temp_table_dat{Type},step_name=$temp_table_dat{Step},chain=$my_Chain_Num,chain2=0,size=$temp_table_dat{Rout_Size},comp=$temp_table_dat{Comp},path=$path_count,count=$count,flag=$my_flag,cw=$my_cw,tool_size=$temp_table_dat{Tool_Size},duplicate=$temp_table_dat{Dup},parent=-1,comp_factor=$temp_table_dat{Comp_Fact},spindle_speed=$temp_table_dat{Spin_Speed},feed_rate=$temp_table_dat{Feed_Rate},spiral=none,mode=$temp_table_dat{Hole_Mode},group=$temp_table_dat{Group},order=$sort_table_row_hash{index},optional=$temp_table_dat{Option}");
							$reset_rout_tool = 1;
					}
				}
				#如果没有从新排刀那么将原始刀具写入到刀具刀具表中
				if($reset_rout_tool == 0){
					&set_rout_nc_table_row(%unsort_table_row_hash);
					$un_matching_rou_array[scalar(@un_matching_rou_array)] = $unsort_table_row_hash{Rout_Size};
				}
			}
			$f->COM("ncr_table_apply");
			#$f->COM("ncr_table_close");
			$f->COM("units,type=$my_unit");
			#如果有没有匹配到的刀具提示检查
			my $test = scalar(@un_matching_rou_array);
			if(scalar(@un_matching_rou_array) > 0){
				my $message_str = "";
				foreach my $mss_size(@un_matching_rou_array){
					$message_str = "$message_str"."  $mss_size";
				}
				$c->Messages('warning',"$message_str 的刀具没有匹配到上次的排序，请注意检查.重新排序");
			}else{
				$c->Messages('warning',"已按上次排序匹配完毕，请手动点击sort-->apply方可生效排序.");
			}
		}
	}
}

#写一个函数填写一行的刀具表 (仅用于将没有匹配到的刀具数据填入) 2023.03.11 转自多层
sub set_rout_nc_table_row{
    my %unsort_table_row_hash = @_;
    #$f->PAUSE("type:$unsort_table_row_hash{Type} : $sort_table_row_hash{Type} step:$unsort_table_row_hash{Step} : $sort_table_row_hash{Step}  Chain_Num:$unsort_table_row_hash{Chain_Num} : $sort_table_row_hash{Chain_Num}   Rout_Size:$unsort_table_row_hash{Rout_Size} : $sort_table_row_hash{Rout_Size}   Comp:$unsort_table_row_hash{Comp} : $sort_table_row_hash{Comp}   Flg:$unsort_table_row_hash{Flg} : $sort_table_row_hash{Flg}");
    #$f->PAUSE("CW:$unsort_table_row_hash{CW} : $sort_table_row_hash{CW}  Path_Count:$unsort_table_row_hash{Path_Count} : $sort_table_row_hash{Path_Count}  Group:$unsort_table_row_hash{Group} : $sort_table_row_hash{Group}  Hole_Mode:$unsort_table_row_hash{Hole_Mode} : $sort_table_row_hash{Hole_Mode} Option:$unsort_table_row_hash{Option} : $sort_table_row_hash{Option}  Dup:$unsort_table_row_hash{Dup} : $sort_table_row_hash{Dup}");
    #$f->PAUSE("Tool_Size:$unsort_table_row_hash{Tool_Size} : $sort_table_row_hash{Tool_Size}   Comp_Fact:$unsort_table_row_hash{Comp_Fact} : $sort_table_row_hash{Comp_Fact}  Spin_Speed:$unsort_table_row_hash{Spin_Speed} : $sort_table_row_hash{Spin_Speed}   Feed_Rate:$unsort_table_row_hash{Feed_Rate} : $sort_table_row_hash{Feed_Rate}");
    #孔数量和锣带数量命令里面是分开写的，输出刀具表和genesis窗口里面是放在一个栏位，如果Type是Hole 就填 count孔数量，path填0，如果Type是chain就填写path锣刀路径，count填0
    my $path_count = 0;
    my $count = 0;
    if($unsort_table_row_hash{Type} eq "Hole"){
        $count = $unsort_table_row_hash{Path_Count};
    }elsif($unsort_table_row_hash{Type} eq "Chain"){
        $path_count = $unsort_table_row_hash{Path_Count};
    }
    #有的时候输出的刀具表路径长度信息是负数，直接将其转为正数（测试不会影响实际锣带，刀具尺寸不能乱改，会影响实际输出锣带的刀具尺寸）
    if($path_count < 0){
        $path_count = abs($path_count);
    }

    #flag
    my $my_flag = $unsort_table_row_hash{Flg};
    if($my_flag eq "-"){#是一个横杠表示空没有填写,要填0
        $my_flag = 0;
    }
    #cw 如果cw是空就填入no,(打印出的刀具表与刀具排版全部相反，刀具面板是yes输出时就是no，所以要与输出时相反)
    my $my_cw = $unsort_table_row_hash{CW};
    if($my_cw eq "No"){
        $my_cw = "yes";
    }elsif($my_cw eq "Yes"){
        $my_cw = "no";
    }elsif($my_cw eq "-"){
        $my_cw = "no";
    }
    #创建一盒hash用于将里面的参数全部转换成小写填入参数
    my %temp_table_dat;
    foreach my $get_kay(keys(%unsort_table_row_hash)){
        $temp_table_dat{$get_kay} = lc($unsort_table_row_hash{$get_kay});
    }
    #锣带列表如果是-就设置为0
    my $my_Chain_Num = $temp_table_dat{Chain_Num};
    if($my_Chain_Num eq "-"){
        $my_Chain_Num = 0;
    }

    #录制命令在输出刀具表没有找到的参数 chain2录制出来全是chain2=0 ，parent没有参数录制出来全是parent=-1，spiral录制出来全部是spiral=none
    my $mmmc = "ncr_table_set,index=$temp_table_dat{index},type=$temp_table_dat{Type},step_name=$temp_table_dat{Step},chain=$my_Chain_Num,chain2=0,size=$temp_table_dat{Rout_Size},comp=$temp_table_dat{Comp},path=$path_count,count=$count,flag=$my_flag,cw=$my_cw,tool_size=$temp_table_dat{Tool_Size},duplicate=$temp_table_dat{Dup},parent=-1,comp_factor=$temp_table_dat{Comp_Fact},spindle_speed=$temp_table_dat{Spin_Speed},feed_rate=$temp_table_dat{Feed_Rate},spiral=none,mode=$temp_table_dat{Hole_Mode},group=$temp_table_dat{Group},order=$temp_table_dat{index},optional=$temp_table_dat{Option}";
    #$f->PAUSE("mmmmm:$mmmc");
    $f->COM("ncr_table_set,index=$temp_table_dat{index},type=$temp_table_dat{Type},step_name=$temp_table_dat{Step},chain=$my_Chain_Num,chain2=0,size=$temp_table_dat{Rout_Size},comp=$temp_table_dat{Comp},path=$path_count,count=$count,flag=$my_flag,cw=$my_cw,tool_size=$temp_table_dat{Tool_Size},duplicate=$temp_table_dat{Dup},parent=-1,comp_factor=$temp_table_dat{Comp_Fact},spindle_speed=$temp_table_dat{Spin_Speed},feed_rate=$temp_table_dat{Feed_Rate},spiral=none,mode=$temp_table_dat{Hole_Mode},group=$temp_table_dat{Group},order=$temp_table_dat{index},optional=$temp_table_dat{Option}");

}

sub get_mysql_scale{
	my $dbc_m = $o->CONNECT_MYSQL('host'=>'192.168.2.19', 'dbname'=>'drill_zsDb_Hdi', 'port'=>'3306', 'user_name'=>'root', 'passwd'=>'k06931!');
	if (! $dbc_m)
	{
	$c->Messages('warning', '"工程数据库"连接失败-> 无法获取涨缩代码!');
		#exit(0);
		return;
	}
	if ( $JOB =~ /(.*)-[a-z].*/ ) {
		$drc_job = uc($1);
	} else {
		$drc_job = uc($JOB);
	}
	my $job_name_sql = uc($drc_job);
	my $sql_query = "
	SELECT
		job,
		Zscode,
		ScoreX,
		ScoreY
		FROM
		drill_zsDb_Hdi.tabResizeDrillHdi b 
	WHERE
		b.Job = '$job_name_sql'
		AND b.DrillType = '通孔'
		and b.IsDelete = '0'
		and Status != 3
	ORDER BY
		b.Id DESC";
	my $sth_query = $dbc_m->prepare($sql_query);
    $sth_query->execute() or die "无法执行SQL语句:$dbc_m->errstr";
	my @recs = qw();
	my @Zscode_list = qw();
	my @Zscodes = qw();
	# 方松要求同一代码取最新系数 http://192.168.2.120:82/zentao/story-view-7347.html
	while (my @row = $sth_query->fetchrow_array()) {		
		@recs = @row;					
		if(! grep { $recs[1] eq $_ } @Zscodes){
			my %hash =('Zscode',$recs[1],
				'ScaleX',$recs[2],
				'ScaleY',$recs[3]);
			push @Zscode_list,{%hash};			
		}
		push @Zscodes,$recs[1];
    }
	$dbc_m->disconnect if ($dbc_m);
	print Dumper(\@Zscode_list);
	return \@Zscode_list;
}

sub get_result_num {
	# === perl调用python 使用system方法，不能直接获取exit的数值，通过以下转换转化为实际返回值 
	my $sec_result = shift;
	my $exit_code = ($sec_result & 0xff00) >> 8; 
	my $core_dump = ($sec_result & 0x0080); 
	my $signal_no = ($sec_result & 0x007f); 
	if ($signal_no) { 
		print "Process killed by signal $signal_no"; 
		print $core_dump ? " (core dumped)\n" : "\n"; 
	} else { 
		print "Process exited with status $exit_code\n"; 
	} 
	return $exit_code; 
}


sub check_pin_symmetry{
	my $rout_layer = shift;
	if ($rout_layer =~ /.*lpt$|^pnl_rout\d+$|^jp.*|^ccd.*/){
		return;
	}
	my $check_step = 'set';
	my @show_type;
	$f->INFO(entity_type => 'step',
         entity_path => "$JOB/$check_step",
         data_type => 'EXISTS');
	if ($f->{doinfo}{gEXISTS} eq "yes"){
		$f->COM("open_entity,job=$JOB,type=step,name=$check_step,iconic=no");
		$f->AUX("set_group,group=$f->{COMANS}");		
		$f->COM("units,type=mm");
		$f->COM("clear_layers");
		$f->COM("affected_layer,mode=all,affected=no");
		$f->COM("filter_reset,filter_name=popup");
		# 销钉孔只取不和锣带接触的孔
		my $compen_rout = $rout_layer.'_compen_pin';		
		$f->COM("compensate_layer,source_layer=$rout_layer,dest_layer=$compen_rout,dest_layer_type=document");
		$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=pad");
		$f->COM("affected_layer,name=$compen_rout,mode=single,affected=yes");
		$f->COM("filter_area_strt");
		$f->COM("filter_area_end,layer=,filter_name=popup,operation=select,area_type=none,inside_area=no,intersect_area=no");
		$f->COM("get_select_count");
		my $select_count = $f->{COMANS};
		if ($select_count != 0) {
			$f->COM('sel_delete');
		}	
		$f->COM("clear_layers");
		$f->COM("affected_layer,mode=all,affected=no");	
		$f->COM("affected_layer,name=$rout_layer,mode=single,affected=yes");		
		$f->COM("sel_ref_feat,layers=$compen_rout,use=filter,mode=disjoint,pads_as=shape,f_types=line\;pad\;surface\;arc\;text,polarity=positive\;negative,include_syms=,exclude_syms=");		
		$f->COM("get_select_count");
		my $select_count = $f->{COMANS};
		if ($select_count != 0) {
			my $pin_bak = $rout_layer.'_pin_bak';
			&delete_layer($pin_bak);
			$f->COM("sel_copy_other,dest=layer_name,target_layer=$pin_bak");
			$f->COM("affected_layer,name=$rout_layer,mode=single,affected=no");
			foreach my $i (('180','x','y')){
				my $new_bak = $pin_bak.'_'.$i;
				&delete_layer($new_bak);
				$f->COM("affected_layer,name=$pin_bak,mode=single,affected=yes");
				$f->COM("sel_copy_other,dest=layer_name,target_layer=$new_bak,size=2000");
				
				$f->COM("affected_layer,name=$pin_bak,mode=single,affected=no");
				$f->COM("affected_layer,name=$new_bak,mode=single,affected=yes");
				
				$f->INFO(units => 'mm', entity_type => 'step',
						entity_path => "$JOB/$check_step",
						data_type => 'PROF_LIMITS');
				my $xmin = $f->{doinfo}{gPROF_LIMITSxmin};
				my $ymin = $f->{doinfo}{gPROF_LIMITSymin};
				my $xmax = $f->{doinfo}{gPROF_LIMITSxmax};
				my $ymax = $f->{doinfo}{gPROF_LIMITSymax};
				my $x_anchor = $xmin + ($xmax - $xmin) / 2;
				my $y_anchor = $ymin + ($ymax - $ymin) / 2;
				my $status_ = '';
				if ($i eq '180') {
					$status_ = "180°旋转";
					$f->COM("sel_transform,mode=anchor,oper=rotate,duplicate=no,x_anchor=$x_anchor,y_anchor=$y_anchor,angle=$i,x_scale=1,y_scale=1,x_offset=0,y_offset=0");
				}elsif($i eq 'x'){
					$status_ = "x方向镜像";
					$f->COM("sel_transform,mode=anchor,oper=mirror,duplicate=no,x_anchor=$x_anchor,y_anchor=$y_anchor,angle=0,x_scale=1,y_scale=1,x_offset=0,y_offset=0");
				}elsif($i eq 'y'){
					$status_ = "y方向镜像";
					$f->COM("sel_transform,mode=anchor,oper=y_mirror,duplicate=no,x_anchor=$x_anchor,y_anchor=$y_anchor,angle=0,x_scale=1,y_scale=1,x_offset=0,y_offset=0");
				}				
				$f->COM("sel_ref_feat,layers=$pin_bak,use=filter,mode=touch,pads_as=shape,f_types=line\;pad\;surface\;arc\;text,polarity=positive\;negative,include_syms=,exclude_syms=");
				#$f->PAUSE("xxxxxx");
				$f->COM("get_select_count");
				if ($f->{COMANS} eq $select_count) {
					push @show_type,$status_; 
					# $c->Messages('warning',"$rout_layer 层$status_ 后pin未设计防呆,相邻间距至少需错开1mm以上,详见备份层:$new_bak 程序退出!");
					$f->COM("clear_layers");
					$f->COM("affected_layer,mode=all,affected=no");
					$f->COM("filter_reset,filter_name=popup");
					#exit;
				}else{
					&delete_layer($new_bak);
				}
			}
			&delete_layer($pin_bak);
			&delete_layer($compen_rout);
		}		
		$f->COM("clear_layers");
		$f->COM("affected_layer,mode=all,affected=no");
		$f->COM("filter_reset,filter_name=popup");
	}	
	
	my @show_type_pnl;	
	if ($step_name eq "panel") {		
		my $show_str_set = join(';', @show_type);
		# 如果SET不防呆，检测PNL中是否添加防呆孔并是否防呆
		my $pnl_name = "panel";
		my $back_pin_pnl = $rout_layer."_back_pin_pnl";
		my $back_pin_org = $rout_layer."_back_pin_org";
		my $ykj_hole_pnl = "ykj_back_pin_pnl";
		my $fill_surface = "fill_surface_pin";
		my $flatten_pnl = "flatten_pnl_rout";
		&delete_layer($ykj_hole_pnl);
		&delete_layer($back_pin_org);
		&delete_layer($fill_surface);
		&delete_layer($flatten_pnl);
				
		$c->OPEN_STEP($JOB,$pnl_name);
		$f->COM("units,type=mm");			
		$f->COM("create_layer,layer=$fill_surface,context=misc,type=signal,polarity=positive,ins_layer=");
		# 先将ykj里面的工具孔copy出来放到tk.ykj_back_pin_pnl
		
		$f->COM("affected_layer,mode=all,affected=no");	
		$f->COM("clear_layers");
		$f->COM("affected_layer,name=$fill_surface,mode=single,affected=yes");	
		$f->INFO(entity_type => 'job', entity_path => "$JOB", data_type => 'STEPS_LIST');
		my @gSTEPS_LISTS = @{$f->{doinfo}{gSTEPS_LIST}};
		my @stop_steplist;
		foreach my $content_step (@gSTEPS_LISTS) {
			if ($content_step !~ /^drl$|^cdc$|^cds$|^b\d+-\d+$/){
				push @stop_steplist, $content_step;
			}
		}
		my $stop_steps = join("\\;",@stop_steplist );
		# 填充铜皮
		$f->COM("fill_params,type=solid,origin_type=datum,solid_type=surface,std_type=line,min_brush=25.4,use_arcs=yes,symbol=,dx=2.54,dy=2.54,std_angle=45,std_line_width=254,std_step_dist=1270,std_indent=odd,break_partial=yes,cut_prims=no,outline_draw=no,outline_width=0,outline_invert=no");
		$f->COM("sr_fill,polarity=positive,step_margin_x=0,step_margin_y=0,step_max_dist_x=2540,step_max_dist_y=2540,sr_margin_x=0,sr_margin_y=0,sr_max_dist_x=0,sr_max_dist_y=0,nest_sr=yes,stop_at_steps=$stop_steps,consider_feat=no,consider_drill=no,consider_rout=no,dest=affected_layers,attributes=no");
		$f->COM("affected_layer,mode=all,affected=no");
		# 锣带复制一层出来
		$f->COM("merge_layers,source_layer=$rout_layer,dest_layer=$flatten_pnl,invert=no");
		$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=pad");	
		$f->COM("affected_layer,name=$flatten_pnl,mode=single,affected=yes");
		$f->COM("sel_delete_atr,attributes=.rout_chain");
		$c->FILTER_SELECT();			
		if ($c->GET_SELECT_COUNT()){
			$f->COM("sel_delete");
		}		
		$f->COM("affected_layer,mode=all,affected=no");	
		# 生成一层防呆PIN层$back_pin_org
		$f->COM("filter_reset,filter_name=popup");
		$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=pad");	
		$f->COM("affected_layer,name=$rout_layer,mode=single,affected=yes");
		$c->FILTER_SELECT();			
		if ($c->GET_SELECT_COUNT()){
			$f->COM("sel_copy_other,dest=layer_name,target_layer=$back_pin_org");
		}
		
		$f->COM("clear_layers");		
		$f->COM("affected_layer,mode=all,affected=no");	
		$f->COM("affected_layer,name=$back_pin_org,mode=single,affected=yes");
		$f->COM("sel_ref_feat,layers=$flatten_pnl,use=filter,mode=touch,pads_as=shape,f_types=line\;pad\;surface\;arc\;text,polarity=positive\;negative,include_syms=,exclude_syms=");
		
		if ($c->GET_SELECT_COUNT()){
				$f->COM("sel_delete");
			}
		
		$f->COM("sel_ref_feat,layers=$fill_surface,use=filter,mode=disjoint,pads_as=shape,f_types=line\;pad\;surface\;arc\;text,polarity=positive\;negative,include_syms=,exclude_syms=");
		
		if ($c->GET_SELECT_COUNT()){
				$f->COM("sel_delete");
			}
		$c->FILTER_SELECT();
		if ($c->GET_SELECT_COUNT() == 0){
			$c->Messages('warning',"$rout_layer 层中 没有添加防呆PIN孔,程序退出");		
			exit;
		}
		my $ykj_layer = "tk.ykj";
		# 将ykj中的钻孔copy到辅助层
		$f->INFO(entity_type => 'layer',
				entity_path => "$JOB/$pnl_name/$ykj_layer",
				data_type => 'EXISTS');
		if ($f->{doinfo}{gEXISTS} eq "yes"){
			$f->COM("affected_layer,mode=all,affected=no");			
			$f->COM("affected_layer,name=$ykj_layer,mode=single,affected=yes");
			$f->COM("filter_set,filter_name=popup,update_popup=no,include_syms=r3175\;r3176");
			$c->FILTER_SELECT();				
			if ($c->GET_SELECT_COUNT()){
				$f->COM("sel_copy_other,dest=layer_name,target_layer=$ykj_hole_pnl");
				$f->COM("affected_layer,mode=all,affected=no");
				$f->COM("affected_layer,name=$ykj_hole_pnl,mode=single,affected=yes");
				$f->COM("sel_ref_feat,layers=$fill_surface,use=filter,mode=disjoint,pads_as=shape,f_types=line\;pad\;surface\;arc\;text,polarity=positive\;negative,include_syms=,exclude_syms=");			
				if ($c->GET_SELECT_COUNT()){
					$f->COM("sel_delete");
				}
			}			
		}
			
		$f->COM("affected_layer,mode=all,affected=no");
		# PIN孔层也copy到辅助层
		$f->COM("affected_layer,name=$back_pin_org,mode=single,affected=yes");
		$f->COM("sel_change_sym,symbol=r3175,reset_angle=no");
		$c->FILTER_SELECT();				
		if ($c->GET_SELECT_COUNT()){
			$f->COM("sel_copy_other,dest=layer_name,target_layer=$ykj_hole_pnl");
		}
		$f->COM("filter_reset,filter_name=popup");
		$f->COM("clear_layers");
		$f->COM("affected_layer,mode=all,affected=no");	
		$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=pad");			
		
		
		
		$f->INFO(units => 'mm', entity_type => 'step',
				entity_path => "$JOB/$pnl_name",
				data_type => 'PROF_LIMITS');
		my $xmin = $f->{doinfo}{gPROF_LIMITSxmin};
		my $ymin = $f->{doinfo}{gPROF_LIMITSymin};
		my $xmax = $f->{doinfo}{gPROF_LIMITSxmax};
		my $ymax = $f->{doinfo}{gPROF_LIMITSymax};
		my $x_anchor = $xmin + ($xmax - $xmin) / 2;
		my $y_anchor = $ymin + ($ymax - $ymin) / 2;		
			
		foreach my $ang (('180','x','y')){
			&delete_layer($back_pin_pnl);
			$f->COM("clear_layers");
			$f->COM("affected_layer,mode=all,affected=no");				
			$f->COM("affected_layer,name=$back_pin_org,mode=single,affected=yes");			
			$c->FILTER_SELECT();				
			if ($c->GET_SELECT_COUNT()){
				$f->COM("sel_copy_other,dest=layer_name,target_layer=$back_pin_pnl");
				$f->COM("affected_layer,mode=all,affected=no");	
				$c->AFFECTED_LAYER($back_pin_pnl,'yes');
				my $status_ = '';
				if ($ang eq '180') {
					$status_ = "180°旋转";
					$f->COM("sel_transform,mode=anchor,oper=rotate,duplicate=no,x_anchor=$x_anchor,y_anchor=$y_anchor,angle=$ang,x_scale=1,y_scale=1,x_offset=0,y_offset=0");
				}elsif($ang eq 'x'){
					$status_ = "x方向镜像";
					$f->COM("sel_transform,mode=anchor,oper=mirror,duplicate=no,x_anchor=$x_anchor,y_anchor=$y_anchor,angle=0,x_scale=1,y_scale=1,x_offset=0,y_offset=0");
				}elsif($ang eq 'y'){
					$status_ = "y方向镜像";
					$f->COM("sel_transform,mode=anchor,oper=y_mirror,duplicate=no,x_anchor=$x_anchor,y_anchor=$y_anchor,angle=0,x_scale=1,y_scale=1,x_offset=0,y_offset=0");
				}
				$f->COM("sel_ref_feat,layers=$ykj_hole_pnl,use=filter,mode=disjoint,pads_as=shape,f_types=line\;pad\;surface\;arc\;text,polarity=positive\;negative,include_syms=,exclude_syms=");
										
				if ($c->GET_SELECT_COUNT() == 0){						
					push @show_type_pnl,$status_; 
				}
			}
		}			
		&delete_layer($back_pin_pnl);
		&delete_layer($ykj_hole_pnl);
		&delete_layer($fill_surface);
		&delete_layer($back_pin_org);
		&delete_layer($flatten_pnl);
		$f->COM("clear_layers");
		$f->COM("affected_layer,mode=all,affected=no");
		$f->COM("filter_reset,filter_name=popup");
		
		if (@show_type){
			$c->Messages('warning',"$rout_layer 层 在 set中： $show_str_set 后pin未设计防呆,相邻间距至少需错开1MM以上,此条仅提示，程序不退出!");			
		}
		
		if (@show_type_pnl){			
			my $show_str_pnl = join(';', @show_type_pnl);			
			$c->Messages('warning',"$rout_layer 层 在 PNL中： $show_str_pnl 后pin未设计防呆,相邻间距至少需错开一个丝印孔间距(3.175MM)以上,程序退出!");
			exit;
		}		
	}elsif (@show_type && $step_name eq "set"){
		my $show_str_set = join(';', @show_type);
		$c->Messages('warning',"$rout_layer 层 在 set中： $show_str_set 后pin未设计防呆,相邻间距至少需错开1mm以上!");
		exit;
	}
}

sub delete_layer{	
	my $bak = shift;
	$f->INFO(units => 'mm', entity_type => 'layer',
			entity_path => "$JOB/$STEP/$bak",
			data_type => 'EXISTS');
	if ($f->{doinfo}{gEXISTS} eq "yes"){
		$f->COM("delete_layer,layer=$bak");
	}
}

sub CheckRout{
	
	my @selectlayers = @_;
	
	$f->COM("open_entity,job=$JOB,type=step,name=$showStep,iconic=no");
	$f->AUX("set_group,group=$f->{COMANS}");
	$f->COM("units,type=mm");
	
	$f->COM("clear_layers");
	$f->COM("affected_layer,mode=all,affected=no");
	$f->COM("filter_reset,filter_name=popup");
	my @ref_rrr_layers = ();
	foreach my $i (@selectlayers){
		if ($i =~ /lpt/){
			next;
		}
		#if ($i =~ /^(rout)(\d)?|^ccd-rout$/) {
			#rout  rrr
			#rout2  rrr2
			#ccd-rout  rrr-ccd
			#pth-rout  rrr-pth
			#half-rout  rrr-half
			#rout-cdc  rrr-cdc
			#rout-cds  rrr-cds
			#mid-rout  rrr-mid
		if ($i =~ /^jp-rout$/) {
			push @ref_rrr_layers,'NULL';
		} elsif ($i =~ /^ccd-rout$/) {
			push @ref_rrr_layers,'rrr-ccd';
		} elsif ($i =~ /^ccd-half-rout$/) {
			push @ref_rrr_layers,'ccd-rrr-half';
		}elsif ($i =~ /^ccd-pth-rout$/) {
			push @ref_rrr_layers,'ccd-rrr-pth';
		}elsif ($i =~ /^ccd-mid-rout$/) {
			push @ref_rrr_layers,'ccd-rrr-mid';
		}elsif ($i =~ /^rout$/ || $i =~ /^rout-fb$/) {
			push @ref_rrr_layers,'rrr';	
		}elsif ($i =~ /^half-rout$/) {
			push @ref_rrr_layers,'rrr-half';	
		}elsif ($i =~ /^rout-cdc$/) {
			push @ref_rrr_layers,'rrr-cdc';	
		}elsif ($i =~ /^rout-cds$/) {
			push @ref_rrr_layers,'rrr-cds';	
		}elsif ($i =~ /^ccd-rout-cdc$/) {
			push @ref_rrr_layers,'ccd-rrr-cdc';	
		}elsif ($i =~ /^ccd-rout-cds$/) {
			push @ref_rrr_layers,'ccd-rrr-cds';	
		}elsif ($i =~ /^pth-rout$/) {
			push @ref_rrr_layers,'rrr-pth';	
		}elsif ($i =~ /^mid-rout$/) {
			push @ref_rrr_layers,'rrr-mid';	
		}elsif ($i =~ /^(rout)(\d)/) {
			push @ref_rrr_layers,'rrr' . $2;
		} elsif ($i =~ /^([a-z].*)-rout?/) {
			push @ref_rrr_layers,'rrr-' . $1;
		} elsif ($i =~ /^rout-([a-z].*)?/) {
			push @ref_rrr_layers,'rrr-' . $1;	
		}else{
			if ($step_name eq "set"){
				&CheckRoutMessageBox("$i 无法获取到匹配的rrr层别,返回主页面","no");
				return 1;
			}
		}
	}
	#print Dumper(@ref_rrr_layers);
	for(my $j = 0; $j<=$#ref_rrr_layers; $j++) {
		#foreach my $r(@ref_rrr_layers){
		$r = $ref_rrr_layers[$j];
		if ($r eq "NULL") {
			next;
		}
		
		$f->INFO(units => 'mm', entity_type => 'layer',
				entity_path => "$JOB/$showStep/$r",
				data_type => 'EXISTS');
		if ($f->{doinfo}{gEXISTS} eq "no"){
			if ($step_name eq "set"){
				&CheckRoutMessageBox("$r 无法获取到匹配的rrr层别,返回主页面","no");
				return 1;
			}
		}
		
		my $outFina = $r .'___outfina';
		my $outtmp = $r .'___outtmp';
		my $outBack = $r .'___outback';
		my $touchww = $r .'_touch_ww';
		
		foreach my $bak(($outFina,$outtmp,$outBack,$touchww)){
			$f->INFO(units => 'mm', entity_type => 'layer',
					entity_path => "$JOB/$showStep/$bak",
					data_type => 'EXISTS');
			if ($f->{doinfo}{gEXISTS} eq "yes"){
				$f->COM("delete_layer,layer=$bak");
			}
		}
		
		$f->COM("display_layer,name=$r,display=yes,number=1");
		$f->COM("work_layer,name=$r");
		$f->COM("sel_copy_other,dest=layer_name,target_layer=$outFina");
		$f->COM("display_layer,name=$outFina,display=yes,number=1");
		$f->COM("work_layer,name=$outFina");
		
		#-->rout层生成实体铜皮
		$f->COM("sel_cut_data,det_tol=1,con_tol=1,rad_tol=0.1,filter_overlaps=no,delete_doubles=no,use_order=yes,ignore_width=yes,ignore_holes=none,start_positive=yes,polarity_of_touching=same");
		
		#-->筛选只保留铜皮(软件原因，生成铜皮时，可能存在line)
		$f->COM("filter_reset,filter_name=popup");
		$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=line");
		$f->COM("filter_area_strt");
		$f->COM("filter_area_end,layer=,filter_name=popup,operation=select,area_type=none,inside_area=no,intersect_area=no");
		$f->COM("get_select_count");
		if ($f->{COMANS} != 0) {
			&CheckRoutMessageBox("$r 层有未处理好的外形线,输出中止返回主界面","no");
			return 1;
			#$f->COM("sel_delete");
		}
		
		
		#-->筛选只保留铜皮(软件原因，生成铜皮时，可能存在line)
		$f->COM("filter_reset,filter_name=popup");
		$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=line\;pad\;arc\;text");
		$f->COM("filter_area_strt");
		$f->COM("filter_area_end,layer=,filter_name=popup,operation=select,area_type=none,inside_area=no,intersect_area=no");
		$f->COM("get_select_count");
		if ($f->{COMANS} != 0) {
			$f->COM("sel_delete");
		}
		#-->公差按单边0.01mm控制 ===V3.2.0 pth为內闭合槽,加大0.01 
		# 2023.02.24 Song 增加half-rout的检测进板内类型与pth类相同。
		if ($r !~ /pth|cdc|cds|half/) {
			$f->COM("sel_resize,size=-20,corner_ctl=no");
		} else {
			$f->COM("sel_resize,size=20,corner_ctl=no");
		}
		my $cur_rout = $selectlayers[$j];
		
		#增加mic孔判断 把mic孔位置的地方套开铜皮20230731 by lyh
		#http://192.168.2.120:82/zentao/story-view-5833.html
		$f->INFO(units => 'mm', entity_type => 'layer',
				entity_path => "$JOB/$showStep/drl",
				data_type => 'EXISTS');
		if ($f->{doinfo}{gEXISTS} eq "yes"){
			$f->COM("flatten_layer,source_layer=drl,target_layer=drl_mic_tmp");
			$f->COM("display_layer,name=drl_mic_tmp,display=yes,number=1");
			$f->COM("work_layer,name=drl_mic_tmp");
			$f->COM("filter_reset,filter_name=popup");
			$f->COM("filter_set,filter_name=popup,update_popup=no,include_syms=r*7");
			$f->COM("filter_area_strt");
			$f->COM("filter_area_end,layer=,filter_name=popup,operation=select,area_type=none,inside_area=no,intersect_area=no");
			$f->COM("get_select_count");
			if ($f->{COMANS} != 0) {
				$f->COM("sel_copy_other,dest=layer_name,target_layer=$outFina,invert=yes,size=10");
				
				$f->COM("display_layer,name=$outFina,display=yes,number=1");
				$f->COM("work_layer,name=$outFina");		
				$f->COM("sel_contourize,accuracy=0,break_to_islands=yes,clean_hole_size=76.2,clean_hole_mode=x_and_y");
			}
			$f->COM("delete_layer,layer=drl_mic_tmp");
		}
		
		#-->生成实体锣带层
		$f->COM("compensate_layer,source_layer=$cur_rout,dest_layer=$outtmp,dest_layer_type=document");
		$f->COM("display_layer,name=$outtmp,display=yes,number=1");
		$f->COM("work_layer,name=$outtmp");
		
		#-->对比实体锣带铜皮层，是否有多锣现象
		$f->COM("filter_reset,filter_name=popup");
		# === V3.2.0 当为pth 铣槽时，需要更改判断方式为cover ===
		# 2023.02.24 Song 增加half-rout的检测进板内类型与pth类相同。
		if ($cur_rout !~ /pth|cdc|cds|half/) {
			# === 2023.02.07 V3.4 增加了尾数为非0的孔进非锣带区的检测 -->更改锣带检查增加pad检查 line\;arc\;text\;surface -->pad\;line\;arc\;text\;surfacepad检查，pad的尾数不为0
			$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=pad\;line\;arc\;text\;surface");
			$f->COM("sel_ref_feat,layers=$outFina,use=filter,mode=touch,pads_as=shape,f_types=line\;pad\;surface\;arc\;text,polarity=positive\;negative,include_syms=,exclude_syms=");
			# === 不选择尾数是0的pad
			$f->COM("filter_reset,filter_name=popup");
			$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=pad");
			$f->COM("filter_set,filter_name=popup,update_popup=no,polarity=positive");
			#增加一个mic孔r353 20230727 by lyh
			$f->COM("filter_set,filter_name=popup,update_popup=no,include_syms=r*0;r353;r*2");
			$f->COM("filter_area_strt");
			# === 注意这里是unselect
			$f->COM("filter_area_end,layer=,filter_name=popup,operation=unselect,area_type=none,inside_area=no,intersect_area=no");
		}
		elsif ($cur_rout =~ /cdc|cds|half|ccd/) {
			$f->COM("sel_ref_feat,layers=$outFina,use=filter,mode=cover,pads_as=shape,f_types=line\;pad\;surface\;arc\;text,polarity=positive\;negative,include_syms=,exclude_syms=");
			$f->COM("sel_reverse");	
			# === 不选择尾数是0，或者5的pad,或者2的pad
			$f->COM("filter_reset,filter_name=popup");
			$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=pad");
			$f->COM("filter_set,filter_name=popup,update_popup=no,polarity=positive");
			$f->COM("filter_set,filter_name=popup,update_popup=no,include_syms=r*0\;r*5\;r*2");
			$f->COM("filter_area_strt");
			# === 注意这里是unselect
			$f->COM("filter_area_end,layer=,filter_name=popup,operation=unselect,area_type=none,inside_area=no,intersect_area=no");
			
		} else {
			
			$f->COM("sel_ref_feat,layers=$outFina,use=filter,mode=cover,pads_as=shape,f_types=line\;pad\;surface\;arc\;text,polarity=positive\;negative,include_syms=,exclude_syms=");
			$f->COM("sel_reverse");
		}
		$f->COM("filter_reset,filter_name=popup");
		$f->COM("get_select_count");
		
		if ($f->{COMANS} != 0) {
			$f->COM("sel_copy_other,dest=layer_name,target_layer=$outBack");
			$f->COM("display_layer,name=$outBack,display=yes,number=1");
			$f->COM("work_layer,name=$outBack");
			if ($cur_rout =~ /mid/) {
				my $warn_word = "$cur_rout";
				# exit 0;
				my $a = system "$pythonVer", "$scriptPath/hdi-scr/Output/output_rout/output_rout_submit.py",  "$JOB", "$warn_word","0";
				if ($a != 0) {
					return 1;
				}
			} else {
				&CheckRoutMessageBox("$cur_rout 层有部分物件进入单元,输出中止返回主界面","no");
				return 1;
				#$f->PAUSE('xxxxxxxxxxxxxxxxxxxxxxxxxx');
			}
		} else {
			# === V3.3 增加锣带实体是否碰到ww层的检测 ===
			$f->COM("display_layer,name=$outtmp,display=yes,number=1");
			$f->COM("work_layer,name=$outtmp");
			# === 减小0.3mm
			$f->COM("sel_resize,size=-300,corner_ctl=no");
			$f->COM("sel_ref_feat,layers=ww,use=filter,mode=touch,pads_as=shape,f_types=line\;pad\;surface\;arc\;text,polarity=positive\;negative,include_syms=,exclude_syms=");
			if ($f->{COMANS} != 0) {
				$f->COM("sel_copy_other,dest=layer_name,target_layer=$touchww");
				&CheckRoutMessageBox("$cur_rout 层有锣带实体碰到ww层,详见层别:$touchww,输出中止返回主界面","no");
				# === 删除锣带实体层
				$f->INFO(units => 'mm', entity_type => 'layer',
						entity_path => "$JOB/$showStep/$outtmp",
						data_type => 'EXISTS');
				if ($f->{doinfo}{gEXISTS} eq "yes"){
					$f->COM("delete_layer,layer=$outtmp");
				}
				return 1;
			}
			
			foreach my $bak(($outFina,$outtmp,$outBack)){
				$f->INFO(units => 'mm', entity_type => 'layer',
						entity_path => "$JOB/$showStep/$bak",
						data_type => 'EXISTS');
				if ($f->{doinfo}{gEXISTS} eq "yes"){
					$f->COM("delete_layer,layer=$bak");
				}
			}
		}
		
		
	}
	return 0;
}

#/************************
# 函数名: get_rout_length
# 功  能: 根据rrr层获取出货单元锣程总长度
# 参  数: NONE
# 返回值: Length
#***********************/
sub get_rout_length
{
    my $oplayer = 'rrr';
    my $oop_step='';
    # --从所有step中获取，哪一个step中存在物体
    for my $k (@steps) {
        # 判断step指定层中是否存在物件    
        $f->INFO(entity_type => 'layer',
                 entity_path => "$JOB/$k/rrr",
                 data_type => 'FEAT_HIST',
                 parameters => "total");
        if ($f->{doinfo}{gFEAT_HISTtotal} > 0 ) {
            $oop_step = $k;
            last;
        }
    }
    # --无法获取对应的工作step时，认为rrr在所有step中都是空层
    if ($oop_step eq '') 
    {
        my $nullSel = $c->Messages_Sel('question','"rrr" 层为空层，无法执行出货片的锣程计算，确认是否继续？') ;
        if (uc($nullSel) eq 'NO')
        {
            exit(0);
        }else{
            # --重置上传的参数
            $upload_erp = 0;
            return
        }        
    }
    my $routPath = '';
    my $current_path = "C:/tmp";            ###输出的具体目录

    $f->COM("open_entity,job=$JOB,type=step,name=$oop_step,iconic=no");
    $f->AUX("set_group,group=$f->{COMANS}");
    $f->COM('units,type=mm');
    # 删除存在的tmp_tt层
    my $tmp_tt = "tmp_" . $oplayer;
    $f->VOF();
    $f->COM("delete_layer,layer=$tmp_tt");
    $f->COM("create_layer,layer=$tmp_tt,context=misc,type=rout,polarity=positive,ins_layer=");
    $f->VON();
    $f->COM('affected_layer,mode=all,affected=no');
    $f->COM('clear_layers');
    $f->COM("affected_layer,name=$oplayer,mode=single,affected=yes");
    
    $f->COM("sel_copy_other,dest=layer_name,target_layer=$tmp_tt,invert=no,dx=0,dy=0,size=0,x_anchor=0,y_anchor=0,rotation=0,mirror=none");
    $f->COM("chain_add,layer=$tmp_tt,chain=1,size=0.004,comp=none,flag=0,feed=0,speed=0");
    $f->COM('affected_layer,mode=all,affected=no');
    $f->COM("ncrset_cur,job=$JOB,step=$oop_step,layer=$tmp_tt,ncset=nc.$tmp_tt");
    $f->VOF();
    $f->COM("ncrset_delete,name=nc.$tmp_tt");
    $f->VON();

    $f->COM("ncrset_create,name=nc.$tmp_tt");
    $f->COM("ncrset_cur,job=$JOB,step=$oop_step,layer=$tmp_tt,ncset=nc.$tmp_tt");
    
    $f->COM("ncr_set_machine,machine=excellon_hdi,thickness=0");
    $f->COM("ncr_cre_rout");
    
    my $NCreport_file = "C:/tmp" . "/NCreport-" . ${JOB} . "-" . $tmp_tt;

    $f->COM("ncr_report,path= $NCreport_file");
    if (-e "$NCreport_file") {
        # 以T01等开头，第二域为Chain的行，是有用信息
        #            Tool     Tool     Rout   Spindle      Time    
        #Tool Type  Size      Change   Hits   Path         Up Path      (Min)  
        #T01  Chain 0.003937  1        146    172.6250698  122.1509532  0.0     

        open Report,$NCreport_file;        
        while( <Report> )
        {
            chomp($_);

            if ( $_ =~ /^T01.*/ ) 
            {
                my @tmpData = split(/\s+/,$_);
                
                if($tmpData[1] eq "Chain" )
                {
                    $routPath = $tmpData[5];
                    #$f->PAUSE("$routPath");
                }
            }
        }
        close Report;
        unlink $NCreport_file;
    }    
    $f->VOF();
    $f->COM("delete_layer,layer=$tmp_tt");
    $f->VON();
    
    # --关闭窗口
    $f->COM('ncrset_page_close');
    $f->COM("editor_page_close");
    #if ( $routPath ne '' ) {
    #    code
    #    $f->PAUSE("write");
    #    # my $lengthpath  = $current_path . "/" . $oplayer. ".routlength";
    #    # open(OUT, ">$lengthpath");
    #    print OUT "/User:$incam_user Date:$local_time Scale:X=$scale_x Y=$scale_y Anchor=$scale_position X/2=$scale_center_x  Y/2=$scale_center_y    Mirror:$mirror";
    #    # print OUT "User:$incam_user Date:$local_time $JOB $oop_step $oplayer $routPath";    
    #    # close(OUT);
    #    return $routPath;
    #}
    # --樊健华要求保留两位小数
    return sprintf("%.2f", $routPath);
}


#/************************
# 函数名: uploadRoutData
# 功  能: 执行ERP数据上传逻辑
# 参  数: None
# 返回值: None
#************************/
sub uploadRoutData
{
    # --获取锣程数据
    my $totalLength = &get_rout_length();
    my $uc_tJob = uc($JOB);
    if ($totalLength == 0)
    {
        $c->Messages('warning','获取出货单元锣程数据异常，无法上传...');
        return;
    }
    
    # --从本地.rou文件中获取最小锣刀数据
    my $minRoutKnife = &getKnife_Minimum();

    if ($minRoutKnife == 0)
    {
        $c->Messages('warning','获取最小锣刀大小数据异常，无法上传...');
        return;
    }
    
    # --调用接口上传数据
    my $LenInfo = &Utf8_Gbk("出货单元铣程长度：$totalLength\n");
    print $LenInfo;
    # --调用接口上传铣程长度，接口无法覆盖
    # my ($returnCode,$returnMsg) = &Sumbit_GetRequest("{\"tc_aac01\": \"$uc_tJob\",\"tc_aac188\": \"$totalLength\"}");	
	my ($returnCode,$returnMsg) = &Sumbit_PostRequest("tc_aac188", "$totalLength");	
    print &Utf8_Gbk("出货单元铣程长度上传结果：");
    my $returnStatus_L = ($returnCode == 1) ? &Utf8_Gbk("成功\n") : &Utf8_Gbk("失败(") . encode('gbk',$returnMsg) . ")\n";
	if ($returnMsg =~ /.*exists.*/){
		$returnStatus_L =  &Utf8_Gbk("成功 (") . encode('gbk',$returnMsg) . ")\n";
		# 因上面的接口不能修改 故信息部重新提供靶孔上传的接口内加入此字段 供更新锣程用20231115 by lyh
		my $a = system "$pythonVer", "$scriptPath/hdi-scr/Output/output_rout/send_html_request_to_tc_aac_file.py",  "$JOB", "$totalLength";
		if ($a != 0) {
			$returnStatus_L =  &Utf8_Gbk("失败 ERP已存在值，无法自动更新，请手动更新(") . encode('gbk',$returnMsg) . ")\n";
		}		
	}
    
    
    my $KnifeInfo = &Utf8_Gbk("最小刀径：$minRoutKnife\n");
    # --调用接口上传最小刀径，可以覆盖    
    # ($returnCode,$returnMsg) = &Sumbit_GetRequest("{\"tc_aac01\": \"$uc_tJob\",\"tc_aac224\": \"$minRoutKnife\"}");	
	($returnCode,$returnMsg) = &Sumbit_PostRequest("tc_aac224", "$minRoutKnife");
    print &Utf8_Gbk("最小刀径上传结果：");
    my $returnStatus_K = ($returnCode == 1) ? &Utf8_Gbk("成功\n") : &Utf8_Gbk("失败(") .  encode('gbk',$returnMsg).")\n";
    print "$returnStatus_K";
    
	#新增直接更新工程管理系统的最小刀径及锣程 20240110 by lyh
	&uploading_data_to_engineer_database($totalLength,$minRoutKnife);
	
    $c->Messages('info',"锣带输出成功！！！\n\n"."出货单元铣程长度：$totalLength ；\n上传结果：" . &Gbk_Utf8($returnStatus_L) . "\n最小刀径：$minRoutKnife ;\n上传结果：" . &Gbk_Utf8($returnStatus_K));
    
    return;
}

#/************************
# 函数名: uploading_data_to_engineer_database
# 功  能: 最小锣刀和行程ERP有数据，工程管理系统没有数据 再此处上传
# 参  数: http://192.168.2.120:82/zentao/story-view-6344.html
# 返回值: 上传是否成功
#************************/
sub uploading_data_to_engineer_database{
	my ($totalLength,$minRoutKnife) = @_;
	my $dbc_m = $o->CONNECT_MYSQL('host'=>'192.168.2.19', 'dbname'=>'project_status', 'port'=>'3306', 'user_name'=>'root', 'passwd'=>'k06931!');
	if (! $dbc_m)
	{
	$c->Messages('warning', '"工程数据库"连接失败-> 无法获取涨缩代码!');
		#exit(0);
		return;
	}

	my $sql_query = "update project_status.project_status_jobmanage set rout_min_cut=$minRoutKnife,rout_lines=$totalLength where job='$JOB' ";
	my $sth_query = $dbc_m->prepare($sql_query);
    $sth_query->execute() or die "无法执行SQL语句:$dbc_m->errstr";
	$dbc_m->disconnect if ($dbc_m);  
	
	return ;
}



#/************************
# 函数名: Sumbit_GetRequest
# 功  能: POST请求，调用接口上传数据
# 参  数: 对应body数据
# 返回值: 上传是否成功
#************************/
sub Sumbit_PostRequest {
	# my $bodyData=shift;
	my $code = shift;
	my $data = shift;
	
	# --html访问对象
    use LWP::UserAgent;
    #use Data::Dumper;
    my $json = new JSON;  
    my $ua = LWP::UserAgent->new;
	
	## 2024-08-21 更换接口
	my $url='http://192.168.2.89:8081/ERPInterface/Login';
    # 创建 POST 请求
    my $post_data = [
        Username => 'ZYGC',
        Password => 'zygc@2019'
    ];
	my $token='';
    my $response = $ua->post($url, $post_data);
	# 检查响应状态  
    if ($response->is_success) {
        # 打印响应体  
        my $string = encode('UTF-8', $response->decoded_content);
        my $data= decode_json($string);
        if($data->{code} != 200){
			$c->Messages('warning','erp获取令牌失败！上传erp失败!!');
            return 0;
        }
        $token= $data->{data};  
    } else {
		$c->Messages('warning','erp获取令牌失败！上传erp失败!!!');
        return 0;
    }
	# $JOB
    my $job = uc($JOB);
    my $postjson=qq(
    { 	
        "ApiType": "ERPInterFace", 	
        "Method": "ChangeMI", 	
        "From": "CAM", 	
        "TO": "ERP", 	
        "Data": [ 		
            { 			
                "tc_aac01": "$job", 			
                "$code": "$data",
            } 	
        ] 
       }
    );
	
	my $url2="http://192.168.2.89:8081/ERPInterface/RecData";
    my $post_data2  = [
        'json' => $postjson,
    ];
    my $req = POST($url2, $post_data2,  
        'token' => $token,  
    );
	
	my $response2 = $ua->request($req);
    if ($response2->is_success) {  
        my $string = encode('UTF-8', $response2->decoded_content);
        
        my $data= decode_json($string);
        if($data->{code} != 200){
            return (0, 'ERP接口调用失败，不影响工具输出; 请手动在ERP中更新锣程数据!');
        }else{
			print "post succeed !!\n";
			return (1, '上传erp成功!');
		}
    } else {
        return (0, 'ERP接口调用失败，不影响工具输出; 请手动在ERP中更新锣程数据!');
    }
}



#/************************
# 函数名: Sumbit_GetRequest
# 功  能: 提交get请示，调用接口上传数据
# 参  数: 对应body数据
# 返回值: 上传是否成功
#************************/
sub Sumbit_GetRequest {
	#return (0,'测试阶段，暂时不上传ERP!');
    my $bodyData=shift;
    
    # --html访问对象
    use LWP::UserAgent;
    use JSON;
    #use Data::Dumper;
    my $json = new JSON;  
    my $ua = LWP::UserAgent->new;
    
    # --接口说明详见：http://192.168.2.120:82/zentao/story-view-1942.html   
    #1：debug 1表示测试，0表示将数据放到正式的erp数据库
    #2：如果传送的数据不一样，需要对列col的数据进行更改，几列数据就将值改成几。
    # http://192.168.2.23:9091/erp/service/?logino=mi_to_erp&password=mi_to_200925_erp&service=cimi900_prod_1&json=
    # my $url = 'http://192.168.2.23:9091/erp/service/?logino=mi_to_erp&password=mi_to_200925_erp&service=cimi900_prod_1&json=
    my $url = 'http://192.168.2.13:9090/api/erp/service/?logino=mi_to_erp&password=mi_to_200925_erp&service=cimi900_prod_1&json=
        {
            "head": {
                "debug": 0,
                "table": "tc_aac_file",
                "col": 2,
                "row": 1
            },
            
            "body": [xxxxxxxxxxx]
        }';
    # --将请示的内容替换成上传所需的数据
    $url =~ s/xxxxxxxxxxx/$bodyData/g;
	#print($url);
    # --提交get请求
    $req = HTTP::Request->new(GET => $url);
    $req->header('Accept' => 'text/html');
    
    # --send request
    $res = $ua->request($req);
    my $send_result = $res->decoded_content;
    if ($send_result =~ /errcode/)
    {
        # --解析JSON格式返回信息
        my $obj = $json->decode($send_result) ;
        return ($obj->{'errcode'},$obj->{'errmsg'});
    }else{
        return (0,'ERP接口调用失败，不影响工具输出; 请手动在ERP中更新锣程数据!');
    }
    

    # --出现异常
    # if($@){
        # return (0,'ERP接口调用失败，不影响工具输出; 请手动在ERP中更新锣程数据!');
    # }
    #printf Dumper($obj)."\n";
    
    # $c->PAUSE("SSSSSSSSSSSSS");
    # --返回接口返回的信息
    
}


#/************************
# 函数名: getKnife_Minimum
# 功  能: 从本地.rou文件中获取最小锣刀数据
# 参  数: NONE
# 返回值: 
#***********************/
sub getKnife_Minimum
{
    my $minRoutKnife;
    opendir(DIR, $defaults_path) || return;
    my @f = readdir(DIR);
    
    close(DIR);
    for my $fName (@f) {
        # --排除不匹配的锣带文件
        if ($fName !~ /.+\.(out|www)/i and $fName !~ /report/ and $fName !~ /^[\u4e00-\u9fa5]/)
        {
            #跳过中文乱码文件
            my $file_path = "$defaults_path"."/$fName";
            unless(-e $file_path){ #判断如果是中文乱码文件就跳过此文件
                next;
            }
            my $rouFile = "$defaults_path/$fName";
			print '$rouFile' . $rouFile . "\n";
            # --获取最小数据
            my $tmpMin = &getMinKnife($rouFile);
			if (defined $tmpMin){
				if (not defined $minRoutKnife) {
					$minRoutKnife= $tmpMin;
				}else{
					$minRoutKnife= $tmpMin if ($tmpMin<$minRoutKnife);                
				}
			}
        }
    }
    print "END___:".$minRoutKnife."\n";
    # --保留一位小数，因为存在 0.98的刀
    return sprintf('%.1f',$minRoutKnife);
    
}

# --获取最小数据
sub getMinKnife
{
	my $rouFile = shift;
	my $minSize;
	open (RFILE, $rouFile) || return;
	# M48
	# METRIC,LZ
	# T01;C1.95 DRL
	# T04;C1.5  BC1.55
	# T05;C1.5  BC1.47
	# T06;C1.0  BC0.97 
	# T07;C1.6  BC1.85
	# T08;C1.6  BC1.57
	# %
	
	for my $rLine (<RFILE>)
	{
		chomp $rLine;
		last if ($rLine eq '%');
		# --增加参数后不适用
		# if ($rLine =~ /T\d+;C(.+)\s+BC.+/i) {
		if ($rLine =~ /T\d+C(.+)S.+/i) {
			if (not defined $minSize) {
				$minSize = $1
			}else{
				$minSize = $1 if ($1<$minSize);
			}
		}            
		#print $rLine."\n";
	}
	close(RFILE);
	#print "\nMin:".$minSize."\n\n";
	return $minSize;
}
#
sub Utf8_Gbk { 
    #将 utf8 转换成 gbk                 # my $tOutputStr = Utf8_Gbk("$InputStr");
    #return encode('CP936',decode('utf8',shift));
    my @NewCode;
    for ( @_ ) {
    # print $_ . "\n" ;
        # push( @NewCode,encode('CP936',decode('utf8',$_)) );
        push( @NewCode,encode('CP936', $_) );
    }
    if ( defined $NewCode[0] ){
        if ( scalar(@NewCode) > 1 ){
            return(@NewCode);
        } else {
            return($NewCode[0]);
        }
    } else {
        return();
    }
}

sub Gbk_Utf8 { #将 gbk 转换成 utf8                 # my $tOutputStr = Gbk_Utf8("$InputStr");
    #return encode('utf8',decode('CP936',shift));
    my @NewCode;
    for ( @_ ) {
        # push( @NewCode,encode('utf8',decode('CP936',$_)) );
        push( @NewCode,decode('CP936',$_));
    }
    if ( defined $NewCode[0] ){
        if ( scalar(@NewCode) > 1 ){
            return(@NewCode);
        } else {
            return($NewCode[0]);
        }
    } else {
        return();
    }
}

#/************************
# 函数名: Run_Check
# 功  能: 输出前的检测
# 参  数: NONE
# 返回值: Ok or Cancel
#***********************/
sub Run_Check
{
    my $rrrExist = $c->LAYER_EXISTS($JOB,$STEP,'rrr');
    if (uc($rrrExist) eq 'NO') {
        return $c->Messages_Sel('question','"rrr" 层不存在，将无法上传ERP数据及检测是否有锣入板内的铣刀,确认是否继续?');
    }else{
        return 'OK';
    }
}

sub CheckRoutMessageBox {
	my ($ChckMessge,$pause_show) = @_;
	if (not defined $pause_show) {
		$pause_show = 'yes';
	}
	
	my $err = $mw->messageBox(-icon => 'warning',-message => $ChckMessge,-title => '提示',-type => 'OK');
	if ($pause_show eq 'yes')  {
		$f->PAUSE("Please Check ...");		
	}
}

sub ccd_select {
	# === 光学锣带选择 === 关联界面 ===
	if ($op_ccd_rout == 1) {
		$ccd_side = $lfam23->Checkbutton(-text => " 灯珠C面(不勾选为S面)",-variable => \$op_ccd_top,
												   -font => [-size =>11],-bg => '#9BDBDB',-fg => 'red',
												   -command => sub {})->pack(-side => 'left', -padx => 5,-pady => 2);
		$upload_erp = 0;
	} else {
		$ccd_side -> destroy;
	}
}

sub output_ccd_rout {
	my ($op_layer) = @_;
	
	if ($op_ccd_rout == 1 ) {
		my $ccd_op_mirror = '';
		if ($op_ccd_top == 1 ) {
			$ccd_op_mirror = 'yes';
		} elsif  ($op_ccd_top == 0 ) {
			$ccd_op_mirror = 'no';
		}
		my $ncPre = "nc_" . "$op_layer";
		my $op_step = "$showStep";
		print "\n";
		
		open(OUT, ">$output_message");
		# print OUT "/User:$incam_user Date:$local_time Scale:X=$scale_x Y=$scale_y Anchor=$scale_position X/2=$scale_center_x  Y/2=$scale_center_y	Mirror:$mirror";
		print OUT "/User:$incam_user Date:$local_time Scale:X=1 Y=1 Anchor=Orig X/2=0  Y/2=0	Mirror:$ccd_op_mirror Mode:CCD";	
		close(OUT);
		# ===== ;
		$f->COM("ncrset_page_open");
		$f->COM("ncrset_cur,job=$JOB,step=$op_step,layer=$op_layer,ncset=");
		$f->VOF;
			$f->COM("ncrset_delete,name=$ncPre");
		$f->VON;
		$f->COM("ncrset_create,name=$ncPre");
		$f->COM("ncrset_cur,job=$JOB,step=$op_step,layer=$op_layer,ncset=$ncPre");
		$f->COM("ncr_set_machine,machine=excellon_hdi,thickness=0");
		$f->COM("ncr_set_params,format=excellon2,zeroes=trailing,units=mm,tool_units=mm,nf1=3,nf2=3,decimal=yes,modal_coords=no,single_sr=yes,sr_zero_set=no,repetitions=sr,drill_layer=ncr-drill,sr_zero_drill_layer=,break_sr=no,ccw=no,short_lines=none,press_down=no,last_z_up=16,max_arc_ang=180,sep_lyrs=no,allow_no_chain_f=no,keep_table_order=yes");

		$f->COM("ncr_register,angle=0,mirror=$ccd_op_mirror,xoff=0,yoff=0,version=1,xorigin=0,yorigin=0,xscale=1,yscale=1,xscale_o=0,yscale_o=0");


		#$f->PAUSE("$rout_table_list --> @nc_table_rou_list");
		#运行下创建rout 导出未排列的锣带刀具表
		$f->COM("ncrset_units,units=mm");
		$f->COM("ncr_cre_rout");

		$f->COM("ncrset_units,units=mm");
		#$f->COM("ncr_table_open");
		#$f->COM("ncr_table_reset");

		$f->COM("ncr_cre_rout");
		$f->COM("ncr_ncf_export,dir=$current_path,name=$JobName.$op_layer");
		
		$f->COM('ncrset_page_close');
		
		my $strTemp = "";
		open(FILE,"<$current_path/$JobName.$op_layer");
		while(<FILE>) {

			#先删除指定行（用空替换）
			$_ =~ s/^\/G05\n$//g;
			#再删除空行（用空替换）
			$_ =~ s/^\/G40\n$//g;
			$strTemp = $strTemp.$_;
		 }
		 open(FILE,">$current_path/$JobName.$op_layer");
		 print FILE $strTemp;
		 close FILE;
		 
		if ($op_layer =~ /ccd/) {
			our %tool = ();
			our %position = ();
			our @head_file;
			our @t_list;
			&get_rout_split("$current_path/$JobName.$op_layer");
			unlink("$current_path/$JobName.$op_layer");
			my $des_file = "$current_path/$JobName.$op_layer";
			&write_des_file("$des_file");
		}
		if ($op_layer =~ /jp/) {
			our %tool = ();
			our %position = ();
			our @head_file;
			our @t_list;
			&get_rout_split("$current_path/$JobName.$op_layer");
			unlink("$current_path/$JobName.$op_layer");
			my $des_file = "$current_path/$JobName.$op_layer";
			&write_jp_file("$des_file");
		}
	}
	return 1;
}

#use Data::Dumper;

# 拆分当前铣带
sub get_rout_split
{
	my ($source_file) = @_;
	my @file_list = ();
	if (-e $source_file) {
        open(STAT, $source_file) or die "can't open file $source_file: $!";
        while (<STAT>) {
            push(@file_list, $_);
        }
        close(STAT);
    }

	my $body_start = "no";
	my $search_key = "";

	my @mark_T_array = ();
    undef @head_file;
    undef @t_list;
	foreach $tmp (@file_list) {
		if ($tmp ne "") {
			chomp $tmp;
			if ($tmp =~ /^(T\d+);(C\d+\.\d+)\s/) {
				$tool{"$1"} = "$2";
				push(@t_list, $1);
			}
			if ($tmp eq "%") {$body_start = "yes";}
			if ($body_start eq "yes") {
                if ($tmp =~ /^T[01][0-9]$/) {
                    $search_key = $tmp;
                }
				elsif  ($tmp =~/^\/(T[01][0-9])$/) {
					$search_key = $1;
					push @mark_T_array,$search_key;
					push(@{$position{"mark_T_array"}}, $search_key);
				}
                elsif ($tmp eq "M30\n") {

                }
				elsif ($tmp eq "M25\n") {

                }
                else {
                    if (exists $tool{"$search_key"})
					{
						push(@{$position{"$search_key"}}, $tmp);
					}
					else {
						#print $tmp;
					}
                }
            }
            else {
                push(@head_file, $tmp);
            }
		}
	}
	#$position{"mark_T_array"} = @mark_T_array;
	print '@mark_T_array' . "\n";
	print @mark_T_array;
	print "\n";
	return 1;
}

sub write_des_file
{
	my ($des_file) = @_;
	my $mark_T_num = scalar @{$position{"mark_T_array"}};
	my @mark_T_Size = ();
    if (open(SESAME, ">$des_file") or die("$!")) {
        #print SESAME "$head_log\n";
		my %hash_chg_T;
		my $T01size;
        foreach $tmp (@head_file) {
            chomp $tmp;
            if ($tmp =~ /^T(\d+);(C\d+\.\d+)\s.*$/) {
				if (grep { 'T'.$1 eq $_ } @{$position{"mark_T_array"}}) {
					push @mark_T_Size,$2;
				
				#if ($tmp =~ /^T(01);(C\d+\.\d+)\s.*$/) {
				#	#print SESAME "$tmp\n";
				#	$T01size = $2;
				#} elsif ($tmp =~ /^T(02);(C\d+\.\d+)\s.*$/) {
				#	#print SESAME "$tmp\n";
				#	$T02size = $2;
				} else {
					# === 除T01 所有T前进一位(光点T数量，光点T为1进一位，光点T为2进2位)，并记录 ===
					my $change_T = $1 - $mark_T_num;
					my $show_T = $change_T;
					if ($change_T <= 9 ) {
						$show_T = '0' . "$change_T";
					}
					$hash_chg_T{'T'.$1} = 'T'.$show_T;
					print SESAME "T".$show_T.$2."\n";
				}
            }
            #elsif ($tmp =~ /M48/) {
            #    print SESAME "$tmp\n";
            #}
            else {
                print SESAME "$tmp\n";
            }
        }
        print SESAME "%\n"; #写入百分号#
		my $t01cor = '';
		my $t01words = '';
		
		my $chg_start_T = 'T01';
		my $change_num = $mark_T_num + 1;
		if ($change_num < 10) {
			$chg_start_T = 'T0' . $change_num;
		} else {
			$chg_start_T = 'T' . $change_num;
		}
		print '@mark_T_Size' . "\n";
		print @mark_T_Size;
		print "\n";
        foreach $tmp (@t_list) {
			#T01C3.175
			if (grep { $tmp eq $_ } @{$position{"mark_T_array"}}) {
			#if ($tmp eq "T01") {
			#	#print SESAME "M25\n";
			#}
			#elsif ($tmp eq "T02") {
			#	#print SESAME "M25\n";
			#}
			}
			elsif ($tmp eq $chg_start_T) {
				print SESAME "$t01cor\n";
				#print SESAME "M01\nM02\nM08\n";
				if (exists $hash_chg_T{$tmp} ) {
					print SESAME $hash_chg_T{$tmp} . "\n";
				}else{
					print SESAME "$tmp\n";
				}
			}
			else {
				if (exists $hash_chg_T{$tmp} ) {
					print SESAME $hash_chg_T{$tmp} . "\n";
				}else{
					print SESAME "$tmp\n";
				}
			}
        
			my $t01first = '';
			
            foreach $tps (@{$position{$tmp}}) {
				chomp $tps;
				# === 2023.02.09 原来ccd的对位光点都是一种孔径，徐志刚反馈说可能存在两种孔径，更改为以下方法
				# @{$position{"mark_T_array"}} 光点T列表  T01 T02
				# @mark_T_Size 光点孔径列表
				if (grep { $tmp eq $_ } @{$position{"mark_T_array"}}) {
					for (my $cur_T_num=0;$cur_T_num<=scalar@{$position{"mark_T_array"}}; $cur_T_num++){
						if ($tmp eq ${$position{"mark_T_array"}}[$cur_T_num] ) {
							if ($tps =~ /\/(X.*Y.*)/) {
								my $tcor = $1;
								$t01cor = $t01cor . 'M252' . $tcor . $mark_T_Size[$cur_T_num] . "\n" ;
							}
						}
					}
				}	
				else {
					if ($tps eq 'M25') {
						#print SESAME "$tps\n";
						print SESAME "M256\n";
					} elsif ($tps eq 'M01' || $tps eq 'M02'  || $tps eq 'M08' || $tps eq 'M47') {
					} else {
						print SESAME "$tps\n";
					}
                }
            }
        }                     ###write all tool position ###
        #print SESAME "M30\n"; #写入end号#
        close(SESAME);
    }
	if ($mark_T_num != 1) {
		&message_show("文件$des_file \n 的设计的光点T数量为：$mark_T_num, 与常规仅1把T有差异\n 文件已输出,是否退出？");
	}
	
	return 1;
}

sub write_jp_file
{
	my ($des_file) = @_;
    if (open(SESAME, ">$des_file") or die("$!")) {
        #print SESAME "$head_log\n";
		my %hash_chg_T;
		my $T01size;
        foreach $tmp (@head_file) {
            chomp $tmp;
            if ($tmp =~ /^T(\d+);(C\d+\.\d+)\s.*$/) {
				my $jp_depth;
				if ($1 eq '01') {
					 $jp_depth = 11.5;
				} elsif ($1 eq '02') {
					$jp_depth = 12.0;
				} elsif  ($1 eq '03') {
					$jp_depth = 14.2;
				}

				print SESAME "T".$1.$2." Z" .$jp_depth."\n";
            }
            elsif ($tmp =~ /M48/) {
                print SESAME "$tmp\n";
            }
            else {
                print SESAME "$tmp\n";
            }
        }
        print SESAME "%\n"; #写入百分号#
		my $t01cor = '';
		my $t01words = '';
        foreach $tmp (@t_list) {
			if  ($tmp eq 'T01') {
				print SESAME '/T01'."\n";
			} else {
				print SESAME "$tmp\n";
			}
            foreach $tps (@{$position{$tmp}}) {
				chomp $tps;

				if ($tps eq 'M25' || $tps eq 'M01' || $tps eq 'M02'  || $tps eq 'M08' || $tps eq 'M47') {
				} else {
					print SESAME "$tps\n";
				}
            }
        }                     
        #print SESAME "M30\n"; #写入end号#
        close(SESAME);
    }
	return 1;
}

sub iMkDir {  #创建文件夹 # iMkDir('\\\192.168.1.1\1\12\','/root/desk/123/abc',);
	my @OrgPath = @_;
	if ( scalar(@OrgPath) != 0 ) {
		if ( $OrgPath[0] eq "" ) {
			return();
		}
		for my $tOrgPath ( @OrgPath ) {
			$tOrgPath =~ s#[\\]#/#g;
			my ($tOrgPathStart) = ($tOrgPath =~ m#^(/+)[^/]+#i );
			unless (defined $tOrgPathStart ){
				$tOrgPathStart = '';
			}
			my $tPath;
			my @TmpPath;
			for ( split /\/+/,$tOrgPath ){
				if ( $_ eq '' ) {
					next;
				}
				if ( defined $tPath ) {
					$tPath = $tPath . $_ . '/';
				}else{
					$tPath = $tOrgPathStart . $_ . '/'  ;
				}
				push @TmpPath,$tPath;
			}

			my @tCreateDir;
			for my $tPath ( reverse @TmpPath ){
				unless ( -e $tPath ){
					push @tCreateDir,$tPath;
				} else {
					last;
				}
			}
			for my $tPath ( reverse @tCreateDir ){
				mkdir "$tPath",0777 or warn "Cannot make $tPath directory: $!";
			}
		}
	}
	return();
}


#根据指定工艺导入刀具参数表
sub get_excel_kanife_parameters{
   my $BoardProcess = shift;

    my %kanife_data;
    #创建一个ParseExcel 对象
    my $parser   = Spreadsheet::ParseExcel->new();
    #读入excel文件 (前面导入了utf8,这里无法将汉字转换成gbk，只能使用全英文路径)
    my $workbook = $parser->parse('//192.168.2.33/incam-share/incam/genesis/sys/scripts/hdi-scr\/Output/output_rout/knife_too_ parameter/hdi_kanife_parameter_list-2024.12.16.xls');

    #如果读入错误就打印出错误信息
    if ( !defined $workbook ) {
        $c->Messages('warning',"不能读取到excel刀具表数据 \n， $parser->error()！！！");
        die $parser->error(), ".\n";
    }

    #循环读取excel 中的数据表格
    for my $worksheet($workbook->worksheets()){
        #print Dumper($worksheet);
        #row_range()：得到worksheet的行标范围
        my ( $row_min, $row_max ) = $worksheet->row_range();
        #col_range()：得到worksheet的列标范围
        my ( $col_min, $col_max ) = $worksheet->col_range();

        #get_name()：得到worksheet的名字
        my $sheet_name = $worksheet->get_name();
        #要转换成gbk不然有乱码
        my $test_name = encode('gbk',$sheet_name);
        #$c->Messages('warning',"$test_name --> $sheet_name -> $BoardProcess");
        if($sheet_name eq $BoardProcess){
          # $f->PAUSE("ddddddddddddddddddddddddd-> $row_min, $row_max ");
            #循环row 取得没行的数据 (第一列是title不用读)
            for my $row ( ($row_min + 1) .. $row_max ) {
                #取得指定下标行和列的值
                my $cell_0_obj = $worksheet->get_cell( $row, 0 );
                my $cell_1_obj = $worksheet->get_cell( $row, 1 );
                my $cell_2_obj = $worksheet->get_cell( $row, 2 );
                unless(defined($cell_0_obj)){
                    last;
                }
                $cell_0_kanife_size = $cell_0_obj->value();
                $cell_1_kanife_paramete = $cell_1_obj->value();
                $cell_2_compensate = $cell_2_obj->value();
                $kanife_data{$cell_0_kanife_size} = {kanife_size=>$cell_0_kanife_size,kanife_paramete=>$cell_1_kanife_paramete,compensate=>$cell_2_compensate};
            }
        }
    }
    #for my $kanife_size(keys %kanife_data){
       # $c->Messages('warning',"$kanife_data{$kanife_size}{kanife_size} --> $kanife_data{$kanife_size}{kanife_paramete} -> $kanife_data{$kanife_size}{compensate}");
    #}
    return %kanife_data;
}

#取得该料号的工艺信息
sub get_process_by_job_name{
   my $uc_job_name = uc($JOB);
   my $sql = "select JOB_NAME,
		a.VALUE as 表面处理,
		ES_HALF_HOLE_BOARD_ as 半孔板,
		ES_LED_BOARD_ as LED,
		ES_BATTERY_BOARD_ AS 电池板,
		ES_WINDING_BOARD_ AS  线圈板,
		ES_FREE_HALOGEN_ AS 无卤素,
		ES_HIGH_TG_ AS 高TG,
		ES_CAR_BOARD_ AS 汽车板,
		ES_MEDICAL_BOARD_ AS 医疗板
   from vgt_hdi.rpt_job_list Rjob,
		vgt_hdi.enum_values a
   where JOB_NAME='$uc_job_name' AND Rjob.SURFACE_FINISH_ = a.enum AND a.enum_type = '1000'";


    # 预处理SQL语句,结果保存在$sth中
    my $sth = $dbc_inplan->prepare($sql);
    # 执行SQL操作
    $sth->execute() or die "无法执行SQL语句:$dbc_inplan->errstr";
    # --循环所有行数据
    my @recs = $sth->fetchrow_array();

    #查询是否有PTH 锣槽
    my $slect_pth_sql = "SELECT JOB_NAME,	PROCESS_NAME,	SEQUENTIAL_INDEX,	WORK_CENTER_CODE,	OPERATION_CODE,	S_DESCRIPTION
	FROM vgt_hdi.RPT_JOB_TRAV_SECT_LIST
	where OPERATION_CODE='HDI15201' and JOB_NAME='$uc_job_name' order by SEQUENTIAL_INDEX";

    # 预处理SQL语句,结果保存在$sth中
    my $sth2 = $dbc_inplan->prepare($slect_pth_sql);
    # 执行SQL操作
    $sth2->execute() or die "无法执行SQL语句:$dbc_inplan->errstr";
    # --循环所有行数据
    my @recs_pth = $sth2->fetchrow_array();
	
	#查询是否为罗杰斯板材
    my $board_rgs_sql = "SELECT JOB_NAME,
        LISTAGG(FAMILY_T, ', ') WITHIN GROUP (ORDER BY FAMILY_T) AS concatenated_values
        FROM (
        SELECT DISTINCT a.JOB_NAME, (VENDOR_T || FAMILY_T) FAMILY_T
        FROM vgt_hdi.rpt_job_stackup_cont_list a
        JOIN vgt_hdi.rpt_job_list j ON a.JOB_NAME=j.JOB_NAME 
        where TYPE in (0,3)
        and a.JOB_NAME= '$uc_job_name'
        ) sub_Query
        GROUP BY JOB_NAME";

    # 预处理SQL语句,结果保存在$sth中
    my $sth3 = $dbc_inplan->prepare($board_rgs_sql);
    # 执行SQL操作
    $sth3->execute() or die "无法执行SQL语句:$dbc_inplan->errstr";
    # --循环所有行数据
    my @recs_rgs = $sth3->fetchrow_array();
	
    #####分析参数填入
    my $rou_tool_parameter;
    # '普通锣板参数','线圈板.LCD板参数.无卤素','铜基板.铝基板.陶瓷板','半孔.PTH槽参数','LED高tg板电池板参数','金手指卡板参数'
	# 2023.02.17 1.铜基板.铝基板.陶瓷板（备注：HDI暂时没有此类）2.半孔.PTH槽参数 3.金手指卡板参数 4.线圈板.无卤素.高TG.电池板 5.普通锣板参数.LED板参数.通孔板
    if(@recs){#如果取到值就返回工艺结果 1 表面处理（字符）, 2 半孔板 0/1, 3 LED  0/1, 4 电池板  0/1, 5 线圈板  0/1, 6 无卤素 0/1
        #只返回第一个查到的表面处理
		# 罗杰斯板材优先级最高， 20241216-1120，和工艺李启国确认
		if($recs_rgs[1] =~ /ROGERS/){
			$rou_tool_parameter =  'Rogers（罗杰斯）板料（PTFE）';	
		}
		elsif($recs[2] == 1){ # 半孔板
            $rou_tool_parameter =  '半孔.PTH槽参数';
		}elsif(@recs_pth){#有记录就是 PTH锣槽
            $rou_tool_parameter =  '半孔.PTH槽参数';
		}elsif($recs[1] =~ /.+金手指/ || $recs[1] =~ /GF\+/ ){
            $rou_tool_parameter =  '金手指卡板参数';			
		}elsif($recs[9] == 1 ){
            $rou_tool_parameter =  '医疗板参数';
        }elsif( $recs[4] == 1 or $recs[5] == 1 or $recs[6] == 1 or $recs[7] == 1 ){
            $rou_tool_parameter =  '线圈板.无卤素.高TG.电池板';	
        }elsif($recs[3] == 1 ){
            $rou_tool_parameter =  '普通锣板参数.LED板参数.通孔板';
        }		
		else{
            $rou_tool_parameter =  '普通锣板参数.LED板参数.通孔板';
        }
    }else{ #如果没有取到就返回正常板
        $rou_tool_parameter = '普通锣板参数.LED板参数.通孔板';
    }
	
	# NV型号直接使用NV的参数 http://192.168.2.120:82/zentao/story-view-8350.html
	if(substr($JOB,1,4) =~ /d10|a86/){
		$rou_tool_parameter =  'A86、D10';
	}
	
   return $rou_tool_parameter;
}

#/************************
# 函数名: add_config_data
# 功  能: 增加锣带参数
# 参  数: NONE
# 返回值: None
#***********************/
sub add_config_data {
	my ($output_file,%rout_kanife_paramete) = @_;
	my $tool_num = &get_tool_num_by_file("$output_file");

	#用于记录找到刀具开头 m48   唐成 2021-03-19添加
	my $in_kanife_list = 0;
	my $out_kanife_list = 0;
	my $BC_rou_size;
	my %rout_body_kanife_paramete;
	my $strTemp = "";
	open(FILE,"<$output_file");
	while(<FILE>) {
		#$f->PAUSE("$_");
		if($_ =~ /^M48$/){
			$in_kanife_list = 1;
		}elsif($_ =~ /^%$/ and $in_kanife_list){
			$out_kanife_list = 1;
		}
		#判断是否在刀具列表里面，如果在里面就匹配刀具参数
		if($in_kanife_list == 1 and $out_kanife_list == 0 and defined(%rout_kanife_paramete)){
			#使用正则表达试匹配是否是刀具表格式 T03;C1.006
			#if($_ =~ /^T\d+;C\d+\.\d+/ and !($_ =~ /DRL$/)){
			# --圆孔不需带出参数 AresHe 2021.9.29
			if($_ =~ /^T\d+;C\d+\.\d+/ and $_ !~ /DRL$|ZZ$/){
			   #使用空格切割
			   my @rou_data_array = split(" ",$_);

			   #这里正则去不掉空格，先用split
				my @split_array = split("C",$rou_data_array[0]);
				my $rou_size = $split_array[1];
				$rou_size =~ s/\s+//;
				if(scalar(@split_array) == 2){
					if(defined($rout_kanife_paramete{$rou_size})){
						#将默认值重新赋值 T06;C1.501
						$_ = $rou_data_array[0];
						#$f->PAUSE("sss->$_   aaa->$rou_data_array[0]");
						#后面刀具拼接需要的数据(一定要写到去掉分号前面，这里是以;分号来分隔的)
						my @tool_split = split(";",$_);
						my @digital_tool = split("T",$tool_split[0]);
						#去掉换行和分号
						$_ =~ s/\s+$//; #去掉尾部换行
						$_ =~ s/;//; #去掉分号						
						my $change_patameter = $rout_kanife_paramete{$rou_size}{kanife_paramete};
						# $f->PAUSE("$change_patameter");
						# 如果界面选择锣刀寿命减半，则需要将参数减少一半						
						if ($half_knife == 1){
							if ($change_patameter =~ /^(.*H)(\d+)(\.)/){								
								my $half = $2/2;
								$change_patameter = $1.$half.$3;														
							}
						}						

						#如果是最后2把刀需要将R改成R050
						# V3.3 Song 尾数是5，6的增加反刃字样；锣带内容部分的T刀序中不需要FZ字样,后续使用替换删除
						my $tail_zimu = '';
						if ($rou_size =~ /\d+\.\d\d[56]/) {
							$tail_zimu = 'FZ';
						}				
						
						if($digital_tool[1] > ($tool_num - 2)){
							# my $change_patameter = $rout_kanife_paramete{$rou_size}{kanife_paramete};
							$change_patameter =~ s/R\d+/R050/;
							$_ = $_.$change_patameter.$tail_zimu."\n";
							$rout_body_kanife_paramete{$tool_split[0]}=$_;
						}else{
							# $_ = $_.$rout_kanife_paramete{$rou_size}{kanife_paramete}.$tail_zimu."\n";
							$_ = $_.$change_patameter.$tail_zimu."\n";
							$rout_body_kanife_paramete{$tool_split[0]}=$_;
						}
						#如果前面切割的数组等于3 需要在后面加入
						if(scalar(@rou_data_array) >= 3){
							#循环取出数组>=2里面的内容拼接
							my $rou_end_str;
							for(my $row_index=2;$row_index < scalar(@rou_data_array);$row_index++){
								$rou_end_str = $rou_end_str." $rou_data_array[$row_index]";
							}
							$_ =~ s/\s+$//; #去掉尾部换行
							$_ = $_.$rou_end_str."\n";
						}

						#后面刀具列表要加上刀号(后面刀具表部分)
						my $no_CP = $rout_kanife_paramete{$rou_size}{compensate};
						$no_CP =~ s/^CP//;
						$BC_rou_size = "$BC_rou_size"."CP$digital_tool[1],"."$no_CP\n";
					}
				}
			}
		}elsif($in_kanife_list and $out_kanife_list and defined($BC_rou_size)){ #如果已到刀具尾部那么就将补偿信息加入
			$_ = $BC_rou_size.$_;
			#$f->PAUSE("xxxxxxxxxx");
			#设置完补偿刀具后要将参数设置为0
			undef $BC_rou_size;
			$in_kanife_list = 0;
			$out_kanife_list = 0;
		}
		#如果是锣带内容里面的刀序那么加入锣刀参数
		if($_ =~ /^T\d+$/){
			my $rou_size_tmp = $_;
			$rou_size_tmp =~ s/\s+$//; #去掉尾部换行
			if(defined($rout_body_kanife_paramete{$rou_size_tmp})){
				$_ = $rout_body_kanife_paramete{$rou_size_tmp};
				# === 去掉反刃刀添加的FZ字样 ===
				$_ =~ s/FZ$//g;
			}
		}
		#先删除指定行（用空替换）
		$_ =~ s/^\/G05\n$//g;
		#再删除空行（用空替换）
		$_ =~ s/^\/G40\n$//g;
		$strTemp = $strTemp.$_;
	 }
	open(FILE,">$output_file");
	print FILE $strTemp;
	close FILE;
	return;
}

#取得刀具数量
sub get_tool_num_by_file{
    my $file_path = shift;
    open(FILE_OBJ,$file_path) or die "cant open file $file_path";

    my $in_kanife_list = 0;
    my $out_kanife_list = 0;
    my $num_tool = 0;
    while(<FILE_OBJ>){
        if($_ =~ /^M48$/){
            $in_kanife_list = 1;
        }elsif($_ =~ /^%$/ and $in_kanife_list){
            $out_kanife_list = 1;
            last;
        }
        if($in_kanife_list and $_ =~ /^T\d+;/){
            $num_tool++;
        }
    }
    close(FILE_OBJ);
    #$f->PAUSE("num:$num_tool");
    return $num_tool;
}

#获取锣刀寿命是否减半
sub get_rout_kinfe{
    my $uc_job_name = uc($JOB);
	my $sql = "SELECT
					PROC.MRP_NAME ,
					RJTSL.WORK_CENTER_CODE ,
					NTS.NOTE_STRING 
				FROM 
					VGT_HDI.RPT_JOB_TRAV_SECT_LIST RJTSL
					left JOIN VGT_HDI.process proc
					on RJTSL.proc_item_id = proc.item_id 
					and RJTSL.proc_revision_id = proc.revision_id 
					left JOIN VGT_HDI.note_trav_sect nts
					ON RJTSL.item_id = nts.item_id
					and RJTSL.revision_id = nts.revision_id
					and RJTSL.sequential_index = nts.section_sequential_index
					left JOIN VGT_HDI.attr_trav_sect ats
					ON RJTSL.item_id = ats.item_id
					and RJTSL.revision_id = ats.revision_id
					and RJTSL.sequential_index = ats.section_sequential_index
				WHERE 
					RJTSL.JOB_NAME = UPPER('$uc_job_name')
					--AND RJTSL.WORK_CENTER_CODE like '%成型%'
					AND NTS.NOTE_STRING like '%锣刀%寿命%'";

    my $sth = $dbc_inplan->prepare($sql);
    # 执行SQL操作
    $sth->execute() or die "无法执行SQL语句:$dbc_inplan->errstr";
    my @recs = $sth->fetchrow_array();	
	my $rout_half_note = 0;
	if (@recs){
		$rout_half_note = 1;
	}	
	return $rout_half_note;	
}

__END__
2019.11.01更新如下：
作者：AresHe
1.锣带输出前检测防呆，嵌入到本输出程序中
2.输出界面增加显示检测STEP。

2019.11.25更新如下
1.重新简化程序检测步骤。
2.多锣入成型Rout层备份保留制作者比对

版本：V2.6 测试版本
2021.04.12
1。更改限定一定打开step才运行脚本；
2。脚本一定在有panel的step中运行；
3。LED板光学锣带输出，HDI模式。

版本：V2.6.1 测试版本
2021.04.20
1。缺少表头信息M48；
2. 删除刀具后的分号；

版本：V2.7
2021.04.26
1.默认输出路径的建立；
2.光学锣带回读

版本：V2.8
2021.07.08
1.添加锣带参数自动匹配功能

2021.10.28更新如下：
作者：何瑞鹏
版本：V2.9
需求链接：http://192.168.2.120:82/zentao/story-view-3343.html
1.盲锣板输出自动化
2.删除刀头ZZ标记探针刀序
3.添加M127、T98标记
4.重新修改刀序

2021.12.20更新如下：
作者：何瑞鹏
版本：V3.0
需求链接：http://192.168.2.120:82/zentao/story-view-3713.html
1.新增锣带输出前检查成型(set)销钉是否对称(旋转180°,镜像x,镜像y)

2021.12.31更新如下：
作者：何瑞鹏
版本：V3.1
需求链接：临时加入防呆
1.优化现有CheckRout方法多锣防呆
2.rout(\d+),防呆检测参考rrr
3.ccd-rout,防呆检测参考rrr_ccd


2022.09.23更新如下：
作者：宋超
版本：V3.11
需求链接：http://192.168.2.120:82/zentao/story-view-4669.html
1.金手指板无法默认获取金手指参数，实际获取的为无卤素参数;

2022.10.31
作者：宋超
版本：V3.2.0
需求链接：http://192.168.2.120:82/zentao/story-view-4809.html
1.输出钻带匹配外形层名,并加大检测范围,检测不通过，不可继续;

2022.11.14 
作者：宋超
版本：V3.2.1
需求链接：http://192.168.2.120:82/zentao/story-view-4809.html
1.增加中锣输出检测不通过的评审; mid-rout


2023.01.07(暂未上线)
作者：宋超
版本：V3.3
1.需求链接：http://192.168.2.120:82/zentao/story-view-4870.html
锣带检测:针对锣掉连接位的情况,增加转为实体的chain - 0.3mm后去碰ww层，如有碰到，则认为多锣。
2.需求链接：http://192.168.2.120:82/zentao/story-view-4342.html
锣带输出,尾数为5或者6的为反刃刀，增加FZ字样，锣带内容部分的T刀序中不需要FZ字样
3.需求链接： http://192.168.2.120:82/zentao/story-view-4995.html
增加涨缩锣带输出时，对比1:1锣带输出的镜像情况。

2023.02.07
作者：宋超
版本：V3.4
1.需求链接：http://192.168.2.120:82/zentao/story-view-5101.html
锣带检测:增加了尾数为非0的孔进非锣带区的检测
2.2023.02.24 Song 增加half-rout的检测进板内类型与pth类相同。
3.2020.03.02 1.0的锣刀按0.15补偿进行进其他单元检测

2023.02.09  上线日期：2023.03.13
作者：宋超
版本：V3.4.1
1.2023.02.09 原来ccd的对位光点都是一种孔径，徐志刚反馈说可能存在两种孔径，更改CCD输出光学点输出逻辑
2.根据何林邮件,铣带输出参数更新,增加了高TG的判断条件,更改铣带输出备选项,参数选择的优先级按何林沟通选定,增加MySQL日志记录.
http://192.168.2.120:82/zentao/story-view-5157.html

2023.03.07 上线日期：2023.03.13
作者：宋超
版本：V3.4.2
1.获取涨缩钻带拉伸系数：http://192.168.2.120:82/zentao/story-view-5205.html
2.输出路径改为大写;
3.set锣程上传 http://192.168.2.120:82/zentao/story-view-5117.html
4.涨缩锣带输出，对比1：1锣带(compare_rout.py)，XY类坐标使用公差0.05进行比较，如不一致，则弹出bcompare软件比对
5.再次输出锣带时，按上次锣带输出的顺序进行排序。

2023.03.13
作者：宋超
版本：V3.4.3
1.增加scale_num,上传到MySQL数据库

