#!c:/perl/bin/perl -w
#******************************************#
#Use for         :自动输出奥宝LDI资料                
#Written by     :Chuang(suntak)
#Written date    :2015.06.17
#Updae          :2019.04.16修改防呆孔选择，以及Stamp图形位置 (Chuang.liu)
#Note            :上线前需保证以下参数为最新配置
#1.orbotech_plot_spooler参数genesis需要配置为“3”,Incam下需要配置为“1”，否则More参数中无法显示“Image Managere”
#2.gen_line_skip_post_hooks=2
#3.gen_line_skip_pre_hooks=2
#4.../hooks/orbotech_plot_spool.config文件需要配置GROUP_DP100X=any，
#DP_100输出地址：D:\disk\film KEEP_LOCAL_COPY = 'YES' KEEP_LOCAL_COPY IMGMGR_NAMES = 'LDI'
#5.创建了orbldi_stamp symbol图形
#6.../hooks/userdef_stamp_formats文件需要更新
#******************************************#
use Tk;
use Tk::Labelframe;
use Tk::Frame;
use Tk::Pane;
use Encode;
use utf8;
# use Win32::API;
use POSIX qw(strftime);  ###调用指定格式的时间模块##
use Data::Dumper;

use lib "$ENV{SCRIPTS_DIR}/sys/scripts/Package";
use Genesis;
use mainVgt;
use JSON;
use VGT_Oracle;


my @localIpS = &getCurrentIp;

# --初始化
my $JOB=$ENV{JOB};
my $STEP=$ENV{STEP};
my $VerSion = "版本：V5.6";
my $tmpLay = "__outputldi__";

# --程式执行前的检测
unless ($JOB)
{
    &Messages('warning','JOB未打开，程式无法执行！');
    exit(1);
}

# --根据系统定义不同的参数
if ( $^O ne 'linux' ) {
	eval 'use Win32::API';
    our $tmp_file = "C:/tmp";
	#our $tmp_dir = "C:/tmp/$JOB";
    our $scriptPath = "$ENV{SCRIPTS_DIR}/sys/scripts";
    our $dirPath = "D:/disk/film";
    our $parm_file = "$ENV{GENESIS_DIR}/fw/jobs/$JOB/user/panel_parameter1";
}else{
    our $tmp_file = "/tmp";
	#our $tmp_dir = "/tmp/$JOB";
	our $scriptPath = "$ENV{SCRIPTS_DIR}/sys/scripts";
    our $dirPath = "/id/workfile/hdi_film";
    #our $parm_file = "/incam/incam_db1/jobs/$JOB/user/panel_parameter1";
    our $parm_file = "$ENV{JOB_USER_DIR}/panel_parameter1";
}

BEGIN
{
    # --实例化对象
    our $f = new Genesis();
    our $c = new mainVgt();
    our $o = new VGT_Oracle();
    # --连接HDI InPlan oracle数据库
    our $dbc_h = $o->CONNECT_ORACLE('host'=>'172.20.218.193', 'service_name'=>'inmind.fls', 'port'=>'1521', 'user_name'=>'GETDATA', 'passwd'=>'InplanAdmin');
    if (! $dbc_h)
    {
        $c->Messages('warning', '"HDI InPlan数据库"连接失败->程序终止!');
        exit(0);
    }
	# --连接MySQL数据库
    our $dbc_m = $o->CONNECT_MYSQL('host'=>'192.168.2.19', 'dbname'=>'project_status', 'port'=>'3306', 'user_name'=>'root', 'passwd'=>'k06931!');
    if (! $dbc_m)
    {
        $c->Messages('warning', '"工程数据库"连接失败-> 程序终止!');
        exit(0);
    }
}
# --结束启动项
END
{
    # --断开Oracle连接
    $dbc_h->disconnect if ($dbc_h);
	$dbc_m->disconnect if ($dbc_m);

}

##检测资料是否保存
$f->INFO(entity_type => 'job',
         entity_path => "$JOB",
         data_type => 'IS_CHANGED');

my $is_changed = $f->{doinfo}{gIS_CHANGED};
if ($is_changed ne 'no'){
	$c->Messages('warning', '检测到资料未保存！请保存后输出');
        exit(0);
}

$f->COM('get_user_name');
our $softuser = $f->{COMANS};
# --配置文件 orbotech_plot_spool.config 中设置的输出路径为 D:\disk\film,如需更改以下目录下的资料，请同时更改配置文件

# --定义输出check button 对应的类型
my %Sel_Check_B=('Sel_1' => 'Outer', 'Sel_2' => 'Sec', 'Sel_3' => 'Inner','Sel_4' => 'FZ',);
# --初始化指定机台的输出路径 （Kenny Chen:205是二号线的 Kenny Chen:245是三号线的）
#my %machinePath=('Sel_1' => "\\\\172.20.47.205\\dp\\cam", 'Sel_2' =>"\\\\172.20.47.245\\dp\\cam", 'Sel_3' => ["\\\\172.20.47.205\\dp\\cam", "\\\\172.20.47.245\\dp\\cam"]);
my %machinePath_vgt5=('Sel_1' => $dirPath,
                 'Sel_2' => "\\\\172.20.47.205\\dp\\cam\\dp100_jobs",
                 'Sel_3' =>"\\\\172.20.47.245\\dp\\cam\\dp100_jobs",
                 'Sel_4' => ["\\\\172.20.47.205\\dp\\cam\\dp100_jobs", "\\\\172.20.47.245\\dp\\cam\\dp100_jobs"]);
my %machinePath_hdi1=('Sel_1' => $dirPath,
                 'Sel_2' => "\\\\172.20.47.10\\dp\\cam\\dp100_jobs",
                 'Sel_3' => "\\\\172.20.47.20\\dp\\cam\\dp100_jobs",
                 'Sel_4' => "\\\\172.20.47.30\\dp\\cam\\dp100_jobs",
                 'Sel_5' => "\\\\172.20.47.40\\dp\\cam\\dp100_jobs");

#  === 初始化界面参数 ===
my (%sel_but,%opt_frm_c,%opt_frm_cc,%opt_frm_d,%opt_frm_dd,%opt_frm_e,%sel_mir,%opt_frm_f,%opt_frm_g,%sel_pol,%sel_state);
my (@outLayer, %outParm, @stampCoor);
my $num_row=1;
my $out_type_radio=1;
my $machine_type_radio = 1;

my $factory_type_radio = 1;

# 判断IP是多层五厂还是HDI一厂，进行默认选择
# 五厂为172.20.47.216，HDI一厂三楼IP为172.20.47.100
my $vgt5Ip  = "172.20.47.216";
my $hdi1Ip1 = "172.20.47.100";
my $result  = grep /^$vgt5Ip$/,  @localIpS;
my $result2 = grep /^$hdi1Ip1$/, @localIpS;

if ($result eq '0') {
    $factory_type_radio = 2;
}

my $same_scale_x="";
my $same_scale_y="";
my $cs_scale_x=""; ###初始系数值
my $cs_scale_y="";
my $x_scale_change=1;
my $y_scale_change=1;

###初始化目录路径##
my $date_now=strftime("%Y.%m.%d", localtime(time));
my $year_m=substr $date_now,0,7;   ###截取年月
my $day=substr $date_now,8,2;      ###截取日
my $for_ground1='#008B8B';         ###浅蓝色##
my $outInn = 'no';                 # --初始化外层是否需要使用inn靶孔

###获取Step列表
my @all_step=&GET_STEP_LIST;
my $sel_step='panel';

###获取所有Board层列表 及层所属的类型##
#my ($layer_array,$Layer_Info, $Drill_list)=&GET_ATTR_LAYER; ###返回的为两个指针
my ($layer_array,$Layer_Info, $Drill_list, $ref_array)=&GET_ATTR_LAYER; ###返回的为两个指针     return (\@LayerValue,\%Lay_Info,\%Drill_list);
my @layer_array=@$layer_array;
my %Layer_Info=%$Layer_Info;
my %Drill_list= %$Drill_list;
my @ref_array = @$ref_array;

my $drc_job = '';
if ( $JOB =~ /(.*)-[a-z].*/ ) {
	$drc_job = uc($1);
} else {
	$drc_job = uc($JOB);
}
our %lamin_data = $o->getLaminData($dbc_h, $drc_job);
# 压合次数
my $lamination_num = $lamin_data{'yh_num'};
my $rout_x = $lamin_data{$lamination_num}{'pnlroutx'} * 25.4;
my $rout_y = $lamin_data{$lamination_num}{'pnlrouty'} * 25.4;
my $inplan_panel_x = $lamin_data{$lamination_num}{'pnlXInch'} * 25.4;
my $inplan_panel_y = $lamin_data{$lamination_num}{'pnlYInch'} * 25.4;
my $stack_tmp = &GET_InPlan_Stackup;
my %layer_stack = %$stack_tmp;

#print Dumper(\%layer_stack);
#print Dumper(\%lamin_data);
# --整理所有的信号层，找到匹配的inn层
my $jobLayInn = &GET_LAYER_INN;
my %jobLayInn = %$jobLayInn;

# --获取所有内层XY系数
my ($scale_x,$scale_y)=&Get_Scale;
my %scale_x=%$scale_x;
my %scale_y=%$scale_y;

# --获取所有层的面向（从跑Panel的文件中获取 $ENV{GENESIS_DIR}/fw/jobs/$job_name/user/panel_parameter1）
#my %lay_Mir = {};#&GET_LAYER_MIR();
my %lay_Mir = &GET_LAYER_MIR();

###界面代码
my $mw = MainWindow -> new(-title => "胜宏奥宝LDI资料自动输出 $VerSion");
$mw -> geometry("620x720+300+100");
$mw -> update;  ###关闭会取消置顶##
if ( $^O ne 'linux' ) {
 Win32::API -> new("user32","SetWindowPos",[qw(N N N N N N N)],'N')->Call(hex($mw->frame()),-1,0,0,0,0,3);
}
###标题Logo
#$mw->Photo('image1', -file => "$ENV{GENESIS_DIR}/sys/scripts/suntak/picture/suntak_logo.bmp");
#$mw->Label(-image => 'image1',-background => 'white')->pack(-side => 'top',-fill => 'x');

my $head_frame = $mw ->Labelframe(-text=>'输出参数',-font =>'微软雅黑 10',-fg=>'grey')->pack(-side => 'top',-anchor => 'w',-fill => 'x');
###STEP选择
my $jobHead=$head_frame->Frame()-> pack(-side => 'top',-anchor => 'w',-pady => '.1c');
$jobHead-> Label(-text => "当前型号: $JOB", -font =>'微软雅黑 14 bold',-fg => 'blue')->pack(-side => 'left',-fill => 'x');

my $head_1=$head_frame->Frame()-> pack(-side => 'top',-anchor => 'w',-fill=>'x');

my $head_1_2=$head_1->Frame()-> pack(-side => 'left',-anchor => 'w',-pady => '.2c');
$head_1_2-> Label(-text => '输出STEP :', -font =>'微软雅黑 14',-fg => 'blue')->pack(-side => 'left',-fill => 'x');
$head_1_2-> Optionmenu(-options => [@all_step],-variable => \$sel_step,-font =>'微软雅黑 11',-activebackground => 'white')->pack(-side => 'left');

###选择输出层别类型
my $head_5=$head_1->Labelframe(-text=>'批量选择',-font =>'微软雅黑 10',-fg=>'grey')-> pack(-side => 'right',-anchor => 'w',-fill=>'x',-padx=>'.1c');
my $head_5_1=$head_5->Frame()-> pack(-side => 'left');

@p3 = qw/-side left -padx 2 -pady 2 -anchor w/;
my %out_type;
   $sel_n=1;
for ("外层","次外层","内层","辅助") {
    ###初始化Check Button按钮的值为0
    $out_type{"Sel_".$sel_n}=0;
    my $sel_add_color=&SET_LAYER_COLOR($_);    
    $head_5_1-> Checkbutton(
                            -text=>"$_",
                            -font =>'微软雅黑 10',
                            -variable=>\$out_type{"Sel_".$sel_n},
                            -relief=>'flat',
                            -bg=>"$sel_add_color",
                            -activebackground=>'yellow',
                            -command=> \&BATCH_SELECT_LAYER)
                        -> pack(@p3);
    $sel_n++;
}


# add by song 20190820 add factory choose
my $factory_frame = $mw ->Labelframe(-text=>'选择厂区',-font =>'微软雅黑 10',-fg=>'grey')->pack(-side => 'top',-anchor => 'w',-fill => 'x');
my $head_5_2=$factory_frame->Frame()-> pack(-side => 'left');
@p3 = qw/-side left -padx 2 -pady 2 -anchor w/;
   $sel_n=1;
for ("五厂","HDI一厂") {    
    $head_5_2-> Radiobutton(
                            -font =>'微软雅黑 12',
                            -text     => "$_",
                            -variable => \$factory_type_radio,
                            -relief   => 'flat',
                            -value    => $sel_n,
                            -command=> \&changeLineShow
                        )-> pack(@p3);
    $sel_n++;
}
###选择输出的曝光机  --暂时先屏蔽，待生产员工熟悉后再添加
#my $head_6=$machine_frame->Labelframe(-text=>'选择机器',-font =>'微软雅黑 10',-fg=>'grey')-> pack(-side => 'left',-anchor => 'w',-fill=>'x',-padx=>'.1c');

my $machine_frame = $mw ->Labelframe(-text=>'选择机器',-font =>'微软雅黑 10',-fg=>'grey')->pack(-side => 'top',-anchor => 'w',-fill => 'x');
###选择输出的曝光机  --暂时先屏蔽，待生产员工熟悉后再添加
#my $head_6=$machine_frame->Labelframe(-text=>'选择机器',-font =>'微软雅黑 10',-fg=>'grey')-> pack(-side => 'left',-anchor => 'w',-fill=>'x',-padx=>'.1c');
     my $head_6_1=$machine_frame->Frame()-> pack(-side => 'left');

@p3 = qw/-side left -padx 2 -pady 2 -anchor w/;
&changeLineShow;
#   $sel_n=1;
#for ("本地","2号线","3号线",'2&3号线') {    
#    $head_6_1-> Radiobutton(
#                            -font =>'微软雅黑 12',
#                            -text     => "$_",
#                            -variable => \$machine_type_radio,
#                            -relief   => 'flat',
#                            -value    => $sel_n,
#                            -command=> \&changePath
#                        )-> pack(@p3);
#    $sel_n++;
#}

###显示标题栏##
my $display_frame = $mw ->Labelframe(-text=>'输出列表',-font =>'微软雅黑 10',-fg=>'grey')->pack(-side => 'top',-anchor => 'w');

###Scrolled主窗体
my $main_frm=$display_frame->Scrolled('Frame', -scrollbars => 'se', -height => '320', -width => '600', -borderwidth => 2, -relief => 'groove') ->pack(-side => 'top');

###Frame主窗体
my $frm_list=$main_frm->Frame()-> pack(-side => 'top',-anchor => 'w');
###用于填充的Frame
my $None_list=$main_frm->Frame()-> pack(-side => 'bottom',-anchor => 'w');
###层别
my $d_frm1=$frm_list->Frame()->grid(-row => 0, -column => 0, -sticky => 'w');
$d_frm1-> Label(-text =>"层别  ",-font =>'微软雅黑 11',-fg => 'black',-width=>'6') -> grid(-row => 0, -column => 0, -sticky => 'w');
###X系数
my $d_frm5=$frm_list->Frame()->grid(-row => 0, -column => 3, -sticky => 'w');
$d_frm5-> Checkbutton(-text=>"X系数",-font =>'微软雅黑 11',-variable=>\$x_scale_change,-relief=>'flat',-command=> \&Loop_List) -> grid(-row => 0, -column => 0, -sticky => 'w');
###Y系数
my $d_frm6=$frm_list->Frame()->grid(-row => 0, -column => 4, -sticky => 'w');
$d_frm6-> Checkbutton(-text=>"Y系数",-font =>'微软雅黑 11',-variable=>\$y_scale_change,-relief=>'flat',-command=> \&Loop_List) -> grid(-row => 0, -column => 0, -sticky => 'w');
###镜像
my $d_frm7=$frm_list->Frame()->grid(-row => 0, -column => 5, -sticky => 'w');
$d_frm7-> Label(-text => "镜像", -font =>'微软雅黑 11',-fg => 'black',-width=>'6') -> grid(-row => 0, -column => 0, -sticky => 'w');
###极性
my $d_frm8=$frm_list->Frame()->grid(-row => 0, -column => 6, -sticky => 'w');
$d_frm8-> Label(-text => "极性", -font =>'微软雅黑 11',-fg => 'black',-width=>'6') -> grid(-row => 0, -column => 0, -sticky => 'w');
###===2020.07.09 增加层别类型
my $d_frm9=$frm_list->Frame()->grid(-row => 0, -column => 7, -sticky => 'w');
$d_frm9-> Label(-text => "层别类型", -font =>'微软雅黑 11',-fg => 'black',-width=>'8') -> grid(-row => 0, -column => 0, -sticky => 'w');
###定义坐标及Hash
###循环所有输出层
for $lay_n (@layer_array)
{
	$Layer_Info{$lay_n}{type} = $layer_stack{$lay_n}{layerMode};
	$Layer_Info{$lay_n}{yh_process} = $layer_stack{$lay_n}{yh_process};
	
	if ($lay_n =~ /(l\d+)(-ls\d{6}\.\d{4}.*)?$/ ){
		my $tmpLayN = $1;
		$Layer_Info{$lay_n}{type} = $layer_stack{$tmpLayN}{layerMode};
		$Layer_Info{$lay_n}{yh_process} = $layer_stack{$tmpLayN}{yh_process};
		if (exists $lay_Mir{$tmpLayN}){
			$lay_Mir{$lay_n} = $lay_Mir{$tmpLayN};
		}		
	}
	
	if ($Layer_Info{$lay_n}{yh_process} ne '0') {
		$scale_x{$lay_n} = 0;
		$scale_y{$lay_n} = 0;
	}

	if ( $Layer_Info{$lay_n}{type}  eq 'FZ' ) {
		$Layer_Info{$lay_n}{layer_side} = $layer_stack{$lay_n}{layerSide};
	}	

	
	if ($lay_n =~ /ls-kc-(.+)/){
		my $tmpLayN = $lay_n;
        $tmpLayN = $1 if ($lay_n =~ /ls-kc-(.+)/);
		$Layer_Info{$lay_n}{type} = "FZ";
		#print "----------->,$lay_n,$tmpLayN,$Layer_Info{$tmpLayN}{layer_side},$lay_Mir{$tmpLayN}";
		if (exists $lay_Mir{$tmpLayN}){
			$lay_Mir{$lay_n} = $lay_Mir{$tmpLayN};
		}
	}

	if ($lay_n =~ /(l\d+)(-dk|-cm|-2)(-ls\d{6}\.\d{4}.*)?$/){
		my $tmpLayN = $1;
		# my $tmpLayN = $lay_n;
        # $tmpLayN = $1 if ($lay_n =~ /(.+)-dk$/);
		$Layer_Info{$lay_n}{type} = "FZ";
		#print "----------->,$lay_n,$tmpLayN,$Layer_Info{$tmpLayN}{layer_side},$lay_Mir{$tmpLayN}";
		if (exists $lay_Mir{$tmpLayN}){
			$lay_Mir{$lay_n} = $lay_Mir{$tmpLayN};
		}		
	}	
    ###初始值Check Button的值
    $sel_but{$lay_n}=0;
    ###获取层别对应的颜色
    my $layer_color=&SET_LAYER_COLOR($lay_n);
    ###选择Check Button
    ###当临时文件中存在添加条码的层时
    #$sel_but{$lay_n}=(exists $Bar_Info{$lay_n}{Tool_Num}) ? 1 : 0;
    #$sel_state{$lay_n} = (exists $Bar_Info{$lay_n}{Tool_Num}) ? 'normal' : 'disabled';
	$sel_state{$lay_n} =  'disabled';
    $but_frm=$frm_list->Frame()->grid(-row => $num_row+1, -column => 0, -sticky => 'w');
    $but_frm-> Checkbutton(-text=>"$lay_n",-font =>'微软雅黑 10',-variable=>\$sel_but{$lay_n},-bg=>"$layer_color",
                           -activebackground=>'yellow',-relief=>'flat',-command=>\&Loop_List) ->grid(-row => 0, -column => 0, -sticky => 'w' );

    ###工具X轴系数
    $x_frm=$frm_list->Labelframe()->grid(-row => $num_row+1, -column => 3, -sticky => 'w');
    $opt_frm_c{$lay_n}=$x_frm->Entry(-textvariable =>\$scale_x{$lay_n}, -font => '微软雅黑 11',-fg=>'blue', -width => '5', -state => $sel_state{$lay_n})
                            ->grid(-row => 0, -column => 0, -sticky => 'w');
    $opt_frm_cc{$lay_n}=$x_frm->Label(-text=>'/10000', -font =>'微软雅黑 10' , -fg=>'blue', -state => 'disabled')->grid(-row => 0, -column => 1, -sticky => 'w');
   
    ###工具Y轴系数
    $y_frm=$frm_list->Labelframe()->grid(-row => $num_row+1, -column => 4, -sticky => 'w');
    $opt_frm_d{$lay_n}=$y_frm->Entry(-textvariable =>\$scale_y{$lay_n}, -font => '微软雅黑 11',-fg=>'blue', -width => '5', -state => $sel_state{$lay_n})
                             ->grid(-row => 0, -column => 0, -sticky => 'w');
    $opt_frm_dd{$lay_n}=$y_frm->Label(-text=>'/10000', -font =>'微软雅黑 10' , -fg=>'blue', -state => 'disabled')->grid(-row => 0, -column => 1, -sticky => 'w');
   
    ###是否镜像
    if (exists $lay_Mir{$lay_n}) {		
        ###根据Inplan中的信息判断选择是否镜像（仅外层及内层）
        #$sel_mir{$lay_n}=($lay_Mir{$lay_n} eq 'top') ? 'no' : 'yes';
        # 从料号中的存储获取上下菲林面次
		if ($lay_Mir{$lay_n} =~ /no|yes/){
			$sel_mir{$lay_n}=($lay_Mir{$lay_n} eq 'no') ? 'no' : 'yes';
			$mir_fg{$lay_n}='blue';
		}else{
			$sel_mir{$lay_n}= 'Null';	
			$mir_fg{$lay_n}='red';
		}
    }else{
        ###当Inplan中无对应信息时默认为空
		$sel_mir{$lay_n} = 'Null';	
		$mir_fg{$lay_n}='red';
        # $sel_mir{$lay_n}=($Layer_Info{$lay_n}{type} =~ /^(Outer|Inner|Silk|FZ)$/) ? (($Layer_Info{$lay_n}{layer_side} eq 'top') ? 'no' : (($Layer_Info{$lay_n}{layer_side} eq 'bottom') ? 'yes': 'Null')) : (($Layer_Info{$lay_n}{type} =~ /^(Silk)$/) ? ($Layer_Info{$lay_n}{layer_side} eq 'top' ? 'no' : 'yes') : 'Null');
        # $mir_fg{$lay_n}=($Layer_Info{$lay_n}{type} =~ /^(Outer|Inner|Silk|FZ)$/) ? 'blue' : 'red';
    }
	
    $mir_frm=$frm_list->Labelframe()->grid(-row => $num_row+1, -column => 5, -sticky => 'w');
	if ($softuser ne '89627'){
		$mir_frm->gridForget();
	}	
	
    $opt_frm_f{$lay_n}=$mir_frm-> Optionmenu(-options => [qw/no yes Null/],-variable => \$sel_mir{$lay_n},-font =>'微软雅黑 10',-fg=>$mir_fg{$lay_n},-activebackground => 'white', -state => $sel_state{$lay_n})->grid(-row => 0, -column => 0, -sticky => 'w');
      
    ###层别极性
	my $tmp_pol_layer = $lay_n;
	if ($lay_n =~ /(l\d+)(-dk)?(-ls\d{6}\.\d{4}.*)?$/ or $lay_n =~ /(l\d+)(-cm.*)?(-ls\d{6}\.\d{4}.*)?$/){
		$tmp_pol_layer = $1;
	}
	
	if ($tmp_pol_layer =~ /-ls/){
		$c->Messages('warning', " $tmp_pol_layer 层含有LS字样，但是未匹配到正式层名，请联系程序员处理，程序终止!");
        exit(0);
	}
	
    if (exists $Lay_Mir_Pol{$lay_n}{Lay_Pol}) {
        $sel_pol{$lay_n}=$Lay_Mir_Pol{$tmp_pol_layer}{Lay_Pol};
        $pol_fg{$lay_n}=($sel_pol{$lay_n} eq 'positive') ? 'blue' : '#CD853F';
    }else{
        #$sel_pol{$lay_n}=($Layer_Info{$lay_n}{type} =~ /^(Outer|Inner)$/) ? 'positive' : (($Layer_Info{$lay_n}{type} =~ /^(Inner)$/) ? 'negative' :'Null'); #$Layer_Info{$lay_n}{layer_polar}
        $sel_pol{$lay_n}=($Layer_Info{$lay_n}{type} =~ /^(Outer|Inner|Sec|FZ)$/) ? 'Null' : 'positive'; #$Layer_Info{$lay_n}{layer_polar}
        #$sel_pol{$lay_n}='negative';
		#周涌通知镀孔菲林用负片 20240321 by lyh
		if ($lay_n =~ /(l\d+)-dk(-ls\d{6}\.\d{4}.*)?$/){
			$sel_pol{$lay_n}='negative';
		}
        # --次外层显示橙色
        $pol_fg{$lay_n}=($Layer_Info{$lay_n}{type} =~ /^(Outer|Inner)$/) ? 'blue' : (($Layer_Info{$lay_n}{type} =~ /^(Sec|FZ)$/) ? '#FFA500' : 'red');
    } 
    $pol_frm=$frm_list->Labelframe()->grid(-row => $num_row+1, -column => 6, -sticky => 'w');
	if ($softuser ne '89627'){
		$pol_frm->gridForget();
	}
	
    # $opt_frm_e{$lay_n}=$pol_frm-> Optionmenu(-options => [qw/positive negative Null/],-variable => \$sel_pol{$lay_n},-font =>'微软雅黑 10',-fg=>$pol_fg{$lay_n},-activebackground => 'white', -state => $sel_state{$lay_n})->grid(-row => 0, -column => 0, -sticky => 'w');
	# === 锁定线路层极性均为正极性 === http://192.168.2.120:82/zentao/story-view-1872.html
	# if ($softuser eq '40249' || $softuser eq '44926' || $softuser eq '44566' || $softuser eq '74648' || $softuser eq '84310') {
		##周涌通知 走正片流程的直接默认 negative 20221220 by lyh
		# if ($layer_stack{$lay_n}{flow_content} == 2) {
			## 2023.01.04 Song 增加个提醒语句，二次铜的层别设定极性为Negative
			# &Messages('warning', "从Inplan获取到 $lay_n 为二次铜，设定极性为Negative？");
			# $sel_pol{$lay_n}="negative";
		# }
		# $opt_frm_e{$lay_n}=$pol_frm-> Optionmenu(-options => [qw/positive negative Null/],-variable => \$sel_pol{$lay_n},-font =>'微软雅黑 10',-fg=>$pol_fg{$lay_n},-activebackground => 'white', -state => $sel_state{$lay_n})->grid(-row => 0, -column => 0, -sticky => 'w');
	# } else {
		if ($lay_n =~ /(l\d+)-dk/){
			$opt_frm_e{$lay_n}=$pol_frm-> Optionmenu(-options => [qw/positive negative Null/],-variable => \$sel_pol{$lay_n},-font =>'微软雅黑 10',-fg=>$pol_fg{$lay_n},-activebackground => 'white', -state => $sel_state{$lay_n})->grid(-row => 0, -column => 0, -sticky => 'w');
		}else {
			if (exists $layer_stack{$tmp_pol_layer}{flow_content}){				
				#周涌通知 正片全部按negative来设置 所有人都可以输出 20241016 by lyh
				# if ($layer_stack{$lay_n}{flow_content} == 2) {
				if ($layer_stack{$tmp_pol_layer}{flow_content} == 2) {
					$opt_frm_e{$lay_n}=$pol_frm-> Optionmenu(-options => [qw/negative/],-variable => \$sel_pol{$lay_n},-font =>'微软雅黑 10',-fg=>$pol_fg{$lay_n},-activebackground => 'white', -state => $sel_state{$lay_n})->grid(-row => 0, -column => 0, -sticky => 'w');
				}else{
					$opt_frm_e{$lay_n}=$pol_frm-> Optionmenu(-options => [qw/positive/],-variable => \$sel_pol{$lay_n},-font =>'微软雅黑 10',-fg=>$pol_fg{$lay_n},-activebackground => 'white', -state => $sel_state{$lay_n})->grid(-row => 0, -column => 0, -sticky => 'w');
				}
			}else{			
				$sel_pol{$lay_n} = 'Null';
				$opt_frm_e{$lay_n}=$pol_frm-> Optionmenu(-options => [qw/positive negative Null/],-variable => \$sel_pol{$lay_n},-font =>'微软雅黑 10',-fg=>$pol_fg{$lay_n},-activebackground => 'white', -state => $sel_state{$lay_n})->grid(-row => 0, -column => 0, -sticky => 'w');
				
			}		
			
		}
	#}
	$layer_type=$frm_list->Labelframe()->grid(-row => $num_row+1, -column => 7, -sticky => 'w');
    $opt_frm_g{$lay_n}=$layer_type->Entry(-textvariable =>\$Layer_Info{$lay_n}{type}, -font => '微软雅黑 11',-fg=>'blue', -width => '6', -state => 'disabled', -relief => 'flat' )
                             ->grid(-row => 0, -column => 0, -sticky => 'w');
							 
    $num_row++;
}

# --排满为12行加标题
if ($num_row < 12) {
    ###用于填满整个画布（Scrolled窗体中暂时未找到好方法让内嵌的部件位置按top位置放置）
    my $point_frm1=$None_list->Frame()->grid(-row => 0, -column => 0, -sticky => 'w');
    for (my $rN=0; $rN < (12-$num_row); $rN++)
    {
        $point_frm1-> Label(-text =>"",-font =>'微软雅黑 11',-fg => 'black',-width=>'6') -> grid(-row => $rN, -column => 0, -sticky => 'w');    
    }
}

###默认输出路径显示
my $path_info = $mw->Frame()->pack(-side => 'top');
my $lablePath = $path_info->Label(-font=>'微软雅黑 10',-text=>'选择1号机->输出路径为：\\\\172.20.47.245\dp\cam ',-fg=>'red')->pack(-fill=>'both',-pady=>'.1c');
#my $lablePath = $path_info->Label(-font=>'微软雅黑 10',-text=> "默认输出路径为：D:\\disk\\film\\$JOB ",-fg=>'red')->pack(-fill=>'both',-pady=>'.5c');
&changePath();

###底栏说明
my $frame_info = $mw->Frame()->pack(-side => 'bottom');
$frame_info->Label(-font=>'微软雅黑 8',-text=>'作者：Chuang.liu   公司：胜宏',-fg=>'gray')->pack(-fill=>'both',-pady=>'.1c');

###确定输出及退出按钮
my $frame_exit = $mw->Frame()->pack(-side => 'bottom');
my $focus=$frame_exit-> Button(-text => "资料输出",-font =>'微软雅黑 11', -width => "11", -height => '1', -activeforeground => "$for_ground1",-command => \&Output_Set) ->pack(-side => 'left',-padx=>'1c');
          $frame_exit-> Button(-text => "程序退出",-font =>'微软雅黑 11', -width => "11", -height => '1', -activeforeground => 'red',-command => sub{exit 0}) ->pack(-side => 'left',-padx=>'1c');
$focus ->focusFollowsMouse;


MainLoop;



############################################################
#####                    函数部分                      #####
############################################################
#********************************##
#函数名:获取所有Step 列表
#功  能: 无
#返回值:无
#********************************##
sub GET_STEP_LIST
{
    $f->INFO(entity_type => 'job',
         entity_path => "$JOB",
         data_type => 'STEPS_LIST');
    my @StepValue=@{$f->{doinfo}{gSTEPS_LIST}};
    return @StepValue;
}

#/********************************
# 函数名: GET_ATTR_LAYER
# 功  能: 拫据属性获取层别(board层)
# 参  数: 无
# 返回值: 1,层别数组；3.层别信息Hash
#********************************/
sub GET_ATTR_LAYER
{
    my $i=0; my @LayerValue=();
    my %Lay_Info;
    my %Drill_list;
    my @out_array ;
    my @inn_array ;
    my @sec_array ;
    my @ref_array ;
    my @fz_array ;
    $f->INFO(entity_type => 'matrix',entity_path => "$JOB/matrix");
    ###遍历所有Info信息
    while ( $i < scalar @{$f->{doinfo}{gROWrow}} ) {
        if ( ${$f->{doinfo}{gROWcontext}}[$i] eq 'board' and ${$f->{doinfo}{gROWlayer_type}}[$i] ne "drill") {
            $Lay_Info{${$f->{doinfo}{gROWname}}[$i]}{type} = 'None';       
            ###外层的列表
            if (${$f->{doinfo}{gROWlayer_type}}[$i] eq 'signal' and ${$f->{doinfo}{gROWside}}[$i] ne 'inner' ) {
                $Lay_Info{${$f->{doinfo}{gROWname}}[$i]}{type}='Outer';
                push ( @out_array, $f->{doinfo}{gROWname}[$i]);
            }            
            ###内层的列表
            elsif (${$f->{doinfo}{gROWlayer_type}}[$i] =~ /^(signal|power_ground|mixed)$/ and ${$f->{doinfo}{gROWside}}[$i] eq 'inner' ) {
                $Lay_Info{${$f->{doinfo}{gROWname}}[$i]}{type}='Inner';
                push ( @inn_array, $f->{doinfo}{gROWname}[$i]);
                
            }
			### 增加辅助菲林
			elsif (${$f->{doinfo}{gROWlayer_type}}[$i] eq 'solder_paste' and (${$f->{doinfo}{gROWname}}[$i] =~ /^l[0-9][0-9]?-[0-9][0-9]?\.fz$/ or ${$f->{doinfo}{gROWname}}[$i] =~ /^ls-kc-l[0-9][0-9]?$/  or ${$f->{doinfo}{gROWname}}[$i] =~ /^l[0-9][0-9]?-dk(-ls\d{6}\.\d{4}.*)?$/ or ${$f->{doinfo}{gROWname}}[$i] =~ /^l[0-9][0-9]?-cm(-ls\d{6}\.\d{4}.*)?$/)) {
                $Lay_Info{${$f->{doinfo}{gROWname}}[$i]}{type}='FZ';
			    push ( @fz_array, $f->{doinfo}{gROWname}[$i]);
			}
            if ($Lay_Info{${$f->{doinfo}{gROWname}}[$i]}{type} ne 'None') {
                ###记录所有层列表
                push @LayerValue,${$f->{doinfo}{gROWname}}[$i];
                ###记录所有层极性
                $Lay_Info{${$f->{doinfo}{gROWname}}[$i]}{layer_polar}=${$f->{doinfo}{gROWpolarity}}[$i];
                ###记录所有层极性基础类型
                $Lay_Info{${$f->{doinfo}{gROWname}}[$i]}{layer_type}=${$f->{doinfo}{gROWlayer_type}}[$i];
                ###记录所有层的方向
                #$Lay_Info{${$f->{doinfo}{gROWname}}[$i]}{layer_side}=(${$f->{doinfo}{gROWside}}[$i] ne 'inner') ? ${$f->{doinfo}{gROWside}}[$i] : ${$f->{doinfo}{gROWfoil_side}}[$i];
				# 2021.09.03 HDI的foil_side 不准确 
				$Lay_Info{${$f->{doinfo}{gROWname}}[$i]}{layer_side}=(${$f->{doinfo}{gROWside}}[$i] ne 'inner') ? ${$f->{doinfo}{gROWside}}[$i] : '';
            }           
        }
        # 遍历层别名为pnl_rout及inn的层别添加到参考层列表中
            if ( $f->{doinfo}{gROWname}[$i] =~ /pnl_rout.*/ ||  $f->{doinfo}{gROWname}[$i] =~ /inn[1-9].*/ ) {
                push @ref_array,${$f->{doinfo}{gROWname}}[$i];
            }
        $i++;
    }
    
    # 循环钻孔层，根据钻孔判断外层及次外层 #因加入ls-kc-l\d+ 层次这里直接从型号内获取层数 20231227 by lyh
    #my $lay_num = ($JOB =~ /inn$/) ? substr($JOB, 4, 2)*1 : @LayerValue;
	my $lay_num = substr($JOB, 4, 2)*1 ;
    my $half_num = $lay_num * 0.5;
    my $lastNum2 = $lay_num-1;
    #$f->PAUSE("layer num $lay_num");
    $i=0;
    while ( $i < scalar @{$f->{doinfo}{gROWrow}} ) {
        if ( ${$f->{doinfo}{gROWcontext}}[$i] eq 'board' and ${$f->{doinfo}{gROWlayer_type}}[$i] eq "drill" ) {
            if ( $f->{doinfo}{gROWname}[$i] =~ /s[1-9].*/ ) {
                push(@{$Drill_list{'laser'}}, $f->{doinfo}{gROWname}[$i]);
                if ( $f->{doinfo}{gROWname}[$i] =~ /s([1-9])([0-9])$/ or $f->{doinfo}{gROWname}[$i] =~ /s([1-9])([0-9][0-9])$/ or $f->{doinfo}{gROWname}[$i] =~ /s([1-9][0-9])([0-9][0-9])$/ ) {
                    #镭射层别>8/2 认为反面镭射。例s56
                    if ($1 < $2) {
                        if ($1 <= $half_num && $1 ne '1') {
                            $Lay_Info{'l'.$1}{type}='Sec';
                            push (@sec_array, 'l'.$1);
                        } elsif ($1 > $half_num && $2 ne $lay_num) {
                            $Lay_Info{'l'.$2}{type}='Sec';
                            push (@sec_array, 'l'.$2);
                        }
                    } else {
                        $f->PAUSE("$f->{doinfo}{gROWname}[$i] laser name is not right");
                    }
                } elsif ( $f->{doinfo}{gROWname}[$i] =~ /s([1-9][0-9]?)-([1-9][0-9]?)$/ ) {
                    if ($1 ne '1' && $1 ne $lay_num ) {
                        $Lay_Info{'l'.$1}{type}='Sec';
                        push (@sec_array, 'l'.$1);
                    }
                    if (($1 < $2 and $1 <= $half_num) || ($1 > $2 and $2 > $half_num)) {
                    
                    } else {
                        $f->PAUSE("$f->{doinfo}{gROWname}[$i] laser name is not right");
                    }                
                }
                # --判断最外层是否有对应的激光孔，如果有，定义参数                
                if ($f->{doinfo}{gROWname}[$i] =~ /^s(1(?:-)?2|${lay_num}(?:-)?${lastNum2}|${lastNum2}(?:-)?${lay_num})/)
                {
                    #$f->PAUSE("Layer:$f->{doinfo}{gROWname}[$i]");
                    $outInn = 'yes';
                }
                
            } elsif ( $f->{doinfo}{gROWname}[$i] =~ /m[1-9].*/ ) {
                push(@{$Drill_list{'blind'}}, $f->{doinfo}{gROWname}[$i]);
                # 暂不考虑机械盲孔 #
            } elsif ( $f->{doinfo}{gROWname}[$i] =~ /b[1-9].*/ ) {
                push(@{$Drill_list{'buried'}}, $f->{doinfo}{gROWname}[$i]);
                if ( $f->{doinfo}{gROWname}[$i] =~ /^b([1-9])(?:-)?([0-9])$/ or $f->{doinfo}{gROWname}[$i] =~ /^b([1-9])(?:-)?([1-9][0-9])$/ or $f->{doinfo}{gROWname}[$i] =~ /^b([1-9][0-9])(?:-)?([1-9][0-9])$/ ) {
                    $Lay_Info{'l'.$1}{type}='Sec';
                    $Lay_Info{'l'.$2}{type}='Sec';
                    push (@sec_array, 'l'.$1);
                    push (@sec_array, 'l'.$2);
                }
            } elsif ($f->{doinfo}{gROWname}[$i] =~ /drl(?:-)?(?:[1-9])?/) {
                push(@{$Drill_list{'through'}}, $f->{doinfo}{gROWname}[$i]);
            } elsif ($f->{doinfo}{gROWname}[$i] =~ /^inn(\d+)?$/) {
                push(@{$Drill_list{'inn'}}, $f->{doinfo}{gROWname}[$i]);
            }
        }
         $i++;
    }
    # Test for song20190821 
    #if (defined $Drill_list{'laser'} || defined $Drill_list{'blind'} || defined $Drill_list{'buried'} ) {
    #    $f->PAUSE('HDI change layer type');
    #}
    # 检查次外层的对称关系，如果一层存在，则对称添加另外一层
    # 对sec_array进行去重操作
    my %saw; 
    @sec_array = grep(!$saw{$_}++, @sec_array); 
    $i = 0;
    while ( $i < scalar @sec_array) {
        my $curentLayNum = substr($sec_array[$i], 1);
        my $reversLayNum = $lay_num - $curentLayNum + 1;
        my $reversLay = 'l' . $reversLayNum;
        my $getNum = grep /^$reversLay$/,  @sec_array;
        if ( $getNum eq '0' ) {
            &Messages('warning', "程序未添加到 $reversLay 为次外层，现在添加？");
            $Lay_Info{$reversLay}{type}='Sec';
        }
          $i++;       
    }	
    return (\@LayerValue,\%Lay_Info,\%Drill_list,\@ref_array);
}
#********************************##
#函数名: 获取所有InPLan的叠构信息，包含辅助层
# Song 2020.07.09
#功  能: 无
#返回值: 无
#********************************##
sub GET_InPlan_Stackup
{
	my $drc_job = '';
	if ( $JOB =~ /(.*)-[a-z].*/ ) {
		$drc_job = uc($1);
	} else {
		$drc_job = uc($JOB);
	}

    my %stack_data;
    
    my $sql = "select a.item_name,
				c.item_name,
				e.film_bg_,
				d.MRP_NAME,
				e.PRESS_PROGRAM_,
				e.process_num_ ,
				e.FILM_PF_,
				e.Plating_Type_
		  -- 1代表一次铜，2代表二次铜
		   from
		   VGT_HDI.ITEMS A
			INNER JOIN VGT_HDI.JOB B ON A.ITEM_ID = B.ITEM_ID 
			AND A.LAST_CHECKED_IN_REV = B.REVISION_ID
			INNER JOIN VGT_HDI.PUBLIC_ITEMS C ON A.ROOT_ID = C.ROOT_ID
			INNER JOIN VGT_HDI.PROCESS D ON C.ITEM_ID = D.ITEM_ID 
			AND C.REVISION_ID = D.REVISION_ID
			INNER JOIN VGT_HDI.PROCESS_DA E ON D.ITEM_ID = E.ITEM_ID 
			AND D.REVISION_ID = E.REVISION_ID 
		 where d.proc_type=1 and a.item_name = '$drc_job'
			   order by e.process_num_ desc";
	
		# ===  SQL结果数据格式如下 ===
		#SA1006GH011A1	Final Assembly - 1/6	SA1006GH011A1	一压板	2	L1,L6		1
		#SA1006GH011A1	Inner Layers Core - 1/2	SA1006GH011A1-10102		1	L2	L1-2.fz	0
		#SA1006GH011A1	Inner Layers Core - 3/4	SA1006GH011A1-10304		1	L3,L4		0
		#SA1006GH011A1	Inner Layers Core - 5/6	SA1006GH011A1-10506		1	L5	L6-5.fz	0
    my $sth = $dbc_h->prepare($sql); #结果保存在$sth中
    $sth->execute() or die "无法执行SQL语句:$dbc_h->errstr";
    
    # --循环所有行数据
    while (my @recs=$sth->fetchrow_array) {
        my @top_bot_lay = split(/,/,lc($recs[2]));
        my @stackProcess = split(/-/,$recs[1]);
		my $get_two_layer = $stackProcess[1];
		my $mrp_name = $recs[3];
		# 去除数据前后空格
		$get_two_layer =~ s/^\s+|\s+$//g;
		my @twice_top_bot_lay = split(/\//,$get_two_layer);
		my @fz_lay = split(/,/,lc($recs[6]));
		my $current_yhnum = $recs[5] - 1;
		my $flow_content =  $recs[7];
        my $layerMode;
        my $materialType;
		my $board_x;
		my $board_y;
		my $cut_x;
		my $cut_y;
		
		my %cur_lamin_data = %{$lamin_data{$current_yhnum}};
		#print Dumper(\%cur_lamin_data) . "\n";
        #Final Assembly - 1/12
        #Sub Assembly - 2/11
        #Inner Layers Core - 6/7
        # 20190902添加，此种判断针对标准的hdi结构为OK，
        # 但对于Core+Core结构的未验证，先依据此种方式判断，后续遇到再进行修正
        if ( $stackProcess[0] eq "Final Assembly" ) {
            $layerMode = 'Outer';
            $materialType = 'cu';
        } elsif ( $stackProcess[0] eq "Final Assembly " ) {
            $layerMode = 'Outer';
            $materialType = 'cu';
        } elsif ( $stackProcess[0] eq "Sub Assembly " ) {
            $layerMode = 'Sec';
            $materialType = 'cu';
        } elsif ( $stackProcess[0] eq "Inner Layers Core " ) {
            $layerMode = 'Inner';
            $materialType = 'core';
        } elsif  ( $stackProcess[0] eq "Buried Via " ) {
            $layerMode = 'Sec';
            $materialType = 'core';
        } elsif ( $stackProcess[0] eq "Blind Via " ) {
            $layerMode = 'Sec';
            $materialType = 'core';
		}
		if ($materialType eq 'core') {
			$board_x = $inplan_panel_x;
			$board_y = $inplan_panel_y;
			$cut_x = 0;
			$cut_y = 0;
		} elsif ($materialType eq 'cu') {
			$board_x = $cur_lamin_data{'pnlroutx'} * 25.4;
			$board_y = $cur_lamin_data{'pnlrouty'} * 25.4;
			$cut_x = ($cur_lamin_data{'pnlXInch'} - $cur_lamin_data{'pnlroutx'}) * 0.5 * 25.4;
			$cut_y = ($cur_lamin_data{'pnlYInch'} - $cur_lamin_data{'pnlrouty'}) * 0.5 * 25.4;
			if ($cur_lamin_data{'pnlroutx'} == 0  and $cur_lamin_data{'pnlrouty'} == 0) {
				#  === 双面板 
				$board_x = $inplan_panel_x;
				$board_y = $inplan_panel_y;
				$cut_x = 0;
				$cut_y = 0;
			}
		}
		
		
        # 2020.05.11 如果有core+core结构，则@top_bot_lay就不会有两个值
		# S55806GI139A3	Final Assembly - 1/6	L1,L6
		# S55806GI139A3	Inner Layers Core - 3/4	L3,L4
		# S55806GI139A3	Inner Layers Core - 5/6	L5
		# S55806GI139A3	Inner Layers Core - 1/2	L2
		# 增加判断条件，@top_bot_lay的内的个数不为2
			
		if (scalar(@top_bot_lay) != 2) {
			my $get_top_lay = 'l' . $twice_top_bot_lay[0];
			my $get_bot_lay = 'l' . $twice_top_bot_lay[1];
			if ($top_bot_lay[0] eq $get_top_lay) {
				%{$stack_data{$top_bot_lay[0]}} = ('layerSide','top',
									'layerMode',$layerMode,
									 'materialType',$materialType,
									 'yh_process',$current_yhnum,
									 'flow_content',$flow_content,
									 'board_x',$board_x,
									 'board_y',$board_y,
									 'cut_x',$cut_x,
									 'cut_y',$cut_y
								);
				if (scalar(@fz_lay) == 1 ) {
				%{$stack_data{$fz_lay[0]}} = ('layerSide','bot',
									'layerMode','FZ',
									 'materialType',$materialType,
									'yh_process',$current_yhnum,
									 'flow_content',$flow_content,
									 'board_x',$board_x,
									 'board_y',$board_y,
									 'cut_x',$cut_x,
									 'cut_y',$cut_y									 
								);					
				}
				
			} elsif  ($top_bot_lay[0] eq $get_bot_lay) {
				%{$stack_data{$top_bot_lay[0]}} = ('layerSide','bot',
									'layerMode',$layerMode,
									 'materialType',$materialType,
									'yh_process',$current_yhnum,
									 'flow_content',$flow_content,
									 'board_x',$board_x,
									 'board_y',$board_y,
									 'cut_x',$cut_x,
									 'cut_y',$cut_y
								);
				if (scalar(@fz_lay) == 1 ) {
				%{$stack_data{$fz_lay[0]}} = ('layerSide','top',
									'layerMode','FZ',
									 'materialType',$materialType,
									'yh_process',$current_yhnum,
									 'flow_content',$flow_content,
									 'board_x',$board_x,
									 'board_y',$board_y,
									 'cut_x',$cut_x,
									 'cut_y',$cut_y									 
								);
				}
			}
		} else {
			%{$stack_data{$top_bot_lay[0]}} = ('layerSide','top',
                                            'layerMode',$layerMode,
                                             'materialType',$materialType,
											'yh_process',$current_yhnum,
									 'flow_content',$flow_content,
									 'board_x',$board_x,
									 'board_y',$board_y,
									 'cut_x',$cut_x,
									 'cut_y',$cut_y									 
                                        );
			%{$stack_data{$top_bot_lay[1]}} = ('layerSide','bot',
                                            'layerMode',$layerMode,
                                             'materialType',$materialType,
											'yh_process',$current_yhnum,
									 'flow_content',$flow_content,
									 'board_x',$board_x,
									 'board_y',$board_y,
									 'cut_x',$cut_x,
									 'cut_y',$cut_y									 
                                        );
		}
    }

    #print Dumper(\%stack_data);
	

    # 从inpaln获取料号铜厚信息，并追加到哈希%stack_data中；
    $sql = "select a.item_name,
           c.item_name,
           d.layer_position,
           round(d.required_cu_weight / 28.3495,2),
           e.finish_cu_thk_,
           e.cal_cu_thk_,
			d.LAYER_ORIENTATION
      from vgt_hdi.items           a,
           vgt_hdi.job             b,
           vgt_hdi.items           c,
           vgt_hdi.copper_layer    d,
           vgt_hdi.copper_layer_da e
     where a.item_id = b.item_id
       and a.last_checked_in_rev = b.revision_id
       and a.root_id = c.root_id
       and c.item_id = d.item_id
       and c.last_checked_in_rev = d.revision_id
       and d.item_id = e.item_id
       and d.revision_id = e.revision_id
       and a.item_name = '$drc_job'
       order by d.layer_index";
       
    $sth = $dbc_h->prepare($sql); #结果保存在$sth中
    $sth->execute() or die "无法执行SQL语句: $dbc_h->errstr";
    
    while (my @recs=$sth->fetchrow_array) {
        #print Dumper(\@recs);
		my $lay = lc($recs[1]);
        $stack_data{$lay}{'layer_position'}     = $recs[2];
        $stack_data{$lay}{'required_cu_weight'} = $recs[3];
        $stack_data{$lay}{'finish_cu_thk'}      = $recs[4];
        $stack_data{$lay}{'cal_cu_thk'}         = $recs[5];
		$stack_data{$lay}{'mir'}                = $recs[6];
    }
    #print Dumper(\%stack_data);
    return \%stack_data;
}

#********************************##
#函数名: 获取所有board层对应的靶位孔
#功  能: 无
#返回值: 无
#********************************##
sub GET_LAYER_INN
{
    my %jobLayInn_tmp;
    my %jobLayInn;
    my %innNum;
    #print "SSSSS\n";
    #print Dumper(\%Drill_list);
    my $lay_num = ($JOB =~ /inn$/) ? substr($JOB, 4, 2)*1 : @layer_array; #GET_ATTR_LAYER 返回的参数
    
    for (keys %Drill_list)
    {
        # --判断inn层
        if ($_ =~ /inn/i)
        {
            for my $innL (@{$Drill_list{$_}})
            {
                my $inn_start;
                my $inn_end;
                # --拆分Inn起始和终止层inn34
                if($innL =~ /^inn(\d)(\d)$/)
                {
                    $inn_start = $1;
                    $inn_end = $2;
                }elsif($innL =~ /^inn(\d)(?:-)?(\d\d)$/){  
                    $inn_start = $1;
                    $inn_end =  $2;
                }elsif($innL =~ /^inn(\d\d)(?:-)?(\d\d)$/){  
                    $inn_start = $1;
                    $inn_end =  $2 ;
                }else{
                    $inn_start = 1;
                    $inn_end = $lay_num;
                }
                
                # --记录inn的起始及终止信息
                $innNum{$innL}{'start'} = $inn_start;
                $innNum{$innL}{'end'} = $inn_end;
                
                print "innL:$innL inn_start:$inn_start inn_end:$inn_end\n";
                
                # --循环所有board层
                for my $b_num (1..$lay_num)
                {
                    if ($b_num >= $inn_start and $b_num <= $inn_end)
                    {
                        push (@{$jobLayInn_tmp{'l'.$b_num}}, $innL)
                    }                    
                }
            }
        }        
    }
    
    # --取出最近的inn
    print Dumper(\%jobLayInn_tmp);
    for my $layName (keys %jobLayInn_tmp)
    {
        print $layName."\n";
        if (scalar @{$jobLayInn_tmp{$layName}} > 1)
        {
            for my $innL (@{$jobLayInn_tmp{$layName}})
            {
                my $layNum = substr($layName,1)*1;
                print "layNum:$layNum innL:$innL start:$innNum{$innL}{'start'} end:$innNum{$innL}{'end'}\n";
                # --只要层序号有在对应的inn 的起始层或终止层，即匹配如：l3 匹配 inn23 3=end
                if ($layNum == $innNum{$innL}{'start'} or $layNum == $innNum{$innL}{'end'})
                {
                    $jobLayInn{$layName} = $innL;
                }
            }
        }else{        
            $jobLayInn{$layName} = ${$jobLayInn_tmp{$layName}}[0]
        }
        
        # --对外层的信息重新定义
        # --对应的是最外层时，且判断是否有激光孔,有激光孔优先使用冲靶对位，没有则使用机钻板角孔对位
		# === 2023.01.11 以下判断增加$结尾，超过10层板，会把L10层定义为外层 a77/333e2
        if ($layName =~ /^l(1|$lay_num)$/)
        {
            if ($outInn eq 'no') # --GET_ATTR_LAYER方法中定义的是否存在激光孔，是否需要用Inn,冲的靶做定位
            {
				$jobLayInn{$layName} = $layName;
                # --参考阻焊层先出方向孔
                #if ($c->LAYER_EXISTS($JOB, $STEP, 'm1') =~ /yes/i) {
                #    $jobLayInn{$layName} = 'm1';
                #} elsif ($c->LAYER_EXISTS($JOB, $STEP, 'm2') =~ /yes/i) {
                #    $jobLayInn{$layName} = 'm2';
                #} else {
                #    $jobLayInn{$layName} = $layName;
                #}
            }
        }else{
            if ($outInn eq 'no') # --GET_ATTR_LAYER方法中定义的是否存在激光孔，是否需要用Inn,冲的靶做定位
            {
                $jobLayInn{$layName}=undef;
            }
        }
    }
    
    print Dumper(\%jobLayInn);
    
    # --判断板内是否有埋孔机械层
    for (keys %Drill_list)
    {
        # --判断埋孔层
        if ($_ =~ /buried/i)
        {
            for my $burL (@{$Drill_list{$_}})
            {
                if ( $burL =~ /^b([1-9])(?:-)?([0-9])$/ or $burL =~ /^b([1-9])(?:-)?([1-9][0-9])$/ or $burL =~ /^b([1-9][0-9])(?:-)?([1-9][0-9])$/ ) 
                {
                    $jobLayInn{'l'.$1} = $burL;
                    $jobLayInn{'l'.$2} = $burL;
                }
            }
        }
    }
    
    
    print Dumper(\%jobLayInn);
    
    return (\%jobLayInn);
}


#/********************************
# 函数名: GET_LAYER_MIR
# 功  能: 获取层别镜像信息
# 参  数: 无
# 返回值: 1,层别数组；3.层别信息Hash
#********************************/
sub GET_LAYER_MIR
{
    # --get the panel_parameter1
    my %layMir;
#    if (-e $parm_file) {
#       open(STAT, $parm_file) or die "can't open file $parm_file: $!";
#       my @thick_up = ();
#       while(<STAT>) {
#            push(@thick_up, $_);
#       }
#       close(STAT);
#       
#        foreach $tmp (@thick_up) {
#            my @array = split(/:/, $tmp);
#            if ($array[0] =~ /l[0-9][0-9]?/) {
#                my $tmp_value;
#                if ($array[2] == 1) {
#                    $tmp_value = "no";
#                } else {
#                    $tmp_value = "yes";
#                }
#                $layMir{$array[0]}=$tmp_value;
#            }
#        }
#        # --返回信息
#        return %layMir;        
#    }else{
        #&Messages('warning', "警告：\n\t无法自动获取面向信息，请注意手动选择！");		
		foreach my $tmp (sort keys %layer_stack) {
			if ($tmp =~ /l[0-9][0-9]?/) {
				my $tmp_value = 'Null';
				# if ($layer_stack{$tmp}{'layerSide'} eq 'bot') {
				if ($layer_stack{$tmp}{'mir'} eq '0') {
					$tmp_value = 'yes';
				# } elsif ($layer_stack{$tmp}{'layerSide'} eq 'top') {
				} elsif ($layer_stack{$tmp}{'mir'} eq '1') {
					$tmp_value = 'no';
				}
                # 20250523 zl 没有的话匹配线路层mir
                if ($tmp_value eq 'Null'){
                    if($tmp =~ /(l\d+).*/){
                        if(exists $layer_stack{$1}{'mir'}){
                            if ($layer_stack{$1}{'mir'} eq '0') {
                                $tmp_value = 'yes';
                            # } elsif ($layer_stack{$tmp}{'layerSide'} eq 'top') {
                            } elsif ($layer_stack{$1}{'mir'} eq '1') {
                                $tmp_value = 'no';
                            }
                        }else{
                            &Messages('warning', "警告：\n\t层别 $tmp ,请注意手动选择！");
                        }
                    }
                }
				$layMir{$tmp}=$tmp_value;
			}
		}
        # --返回信息
        return %layMir;     
    #}
}

#********************************##
#函数名:定义各行列表层的颜色
#功  能: 层名
#返回值:颜色变量
#********************************##
sub SET_LAYER_COLOR
{
    my $name=shift;
    my $layer_color;
    ###当传入的参数为层别时
    if (exists $Layer_Info{$name}{layer_type}) {
        if ($Layer_Info{$name}{type} ne "Other") {        
            if($Layer_Info{$name}{layer_type} eq "signal"){
                $layer_color = "#FFA500";  
            }
            elsif ($Layer_Info{$name}{layer_type} eq "power_ground"){
                $layer_color = "#CD853F";
            }
            elsif($Layer_Info{$name}{layer_type} eq "solder_mask"){
                $layer_color="#2E8B57"; 
            }
            elsif($Layer_Info{$name}{layer_type} eq "silk_screen"){
                $layer_color="#F5F5F5"; 
            }
            elsif($Layer_Info{$name}{layer_type} eq "drill"){
                $layer_color="#808080"; 
            }
            elsif($Layer_Info{$name}{layer_type} eq "solder_paste"){
                $layer_color="#FAFAD2";
            }
            elsif($Layer_Info{$name}{layer_type} eq "rout"){
                $layer_color="#BC8F8F";
            }
            elsif($Layer_Info{$name}{layer_type} eq "mixed"){
                $layer_color="#F0E68C";
            }
            elsif($Layer_Info{$name}{layer_type} eq "document"){
                $layer_color="#DCDCDC";
            }else{
                $layer_color="gray";
            }
        }else{
            $layer_color="gray";
        }
    }else{
        if ($name eq "字符") {
            $layer_color="#F5F5F5"; 
        }elsif($name eq "阻焊"){
            $layer_color="#2E8B57"; 
        }elsif($name eq "外层"){
            $layer_color = "#FFA500";  
        }elsif($name eq "次外层"){
            $layer_color = "#CD853F";
        }elsif($name eq "内层"){
            $layer_color = "#CD853F";
        }elsif($name eq "辅助"){
			$layer_color="#FAFAD2";
		}
    }
    return $layer_color;
}

#/********************************
# 函数名: BATCH_SELECT_LAYER
# 功  能: 批量选择所有层列表
# 参  数: 无
# 返回值: 无
#********************************/
sub BATCH_SELECT_LAYER
{
    for(my $n=1;$n<=4;$n++){
        if ($out_type{'Sel_'.$n} eq "1") {
            ###
            print "Sel_Type: $Sel_Check_B{'Sel_'.$n} \n";
            &Loop_List("$Sel_Check_B{'Sel_'.$n}","yes");            
        }else{
            ###
            &Loop_List("$Sel_Check_B{'Sel_'.$n}","no");       
        }
    }
}

# --选择不同机台，Show出不同地址
sub changePath()
{
    if ($factory_type_radio == 1) {
        if ($machine_type_radio == 4){
            if (-d $machinePath_vgt5{'Sel_'.$machine_type_radio}[0] and -d $machinePath_vgt5{'Sel_'.$machine_type_radio}[1]) {
                $lablePath -> configure(-text => "选择同时输出至两条线->输出路径为：\n$machinePath_vgt5{'Sel_'.$machine_type_radio}[0] \n$machinePath_vgt5{'Sel_'.$machine_type_radio}[1]");
            }else{
                &Messages('warning',"所选线地址不通，请检查，程序默认输出至： \n$dirPath/$JOB");
                # --强制更新至“本地”选项
                $machine_type_radio = 1;
                $lablePath -> configure(-text => "所选线地址不通，请检查，程序默认输出至： \n$dirPath/$JOB");
            }
        }else{        
            if (-d $machinePath_vgt5{'Sel_'.$machine_type_radio}) {
                if ($machine_type_radio == 1) {
                    $lablePath -> configure(-text => "选择输出至本地->输出路径为：$machinePath_vgt5{'Sel_'.$machine_type_radio} ");
                }else{
                    $lablePath -> configure(-text => "选择输出至${machine_type_radio}号线->输出路径为：$machinePath_vgt5{'Sel_'.$machine_type_radio} ");
                }
            }else{
                ##$lablePath -> configure(-text => "所选线地址不通，请检查，程序默认输出至： \n$dirPath/$JOB");
                &Messages('warning',"所选线地址不通，请检查，程序默认输出至本地： \n$dirPath/$JOB");
                # --强制更新至“本地”选项
                $machine_type_radio = 1;
                $lablePath -> configure(-text => "所选线地址不通，请检查，程序默认输出至本地： \n$dirPath/$JOB");
            }
        }
    } elsif ($factory_type_radio == 2) {
        # 当选择厂别为HDI一厂时，使用此判断 #
            if (-d $machinePath_hdi1{'Sel_'.$machine_type_radio}) {
                if ($machine_type_radio == 1) {
                    $lablePath -> configure(-text => "选择输出至本地->输出路径为：$machinePath_hdi1{'Sel_'.$machine_type_radio} ");
                }else{
                    $lablePath -> configure(-text => "选择输出至${machine_type_radio}号线->输出路径为：$machinePath_hdi1{'Sel_'.$machine_type_radio} ");
                }
            }else{
                ##$lablePath -> configure(-text => "所选线地址不通，请检查，程序默认输出至： \n$dirPath/$JOB");
                &Messages('warning',"所选线地址$machinePath_hdi1{'Sel_'.$machine_type_radio} 不通，请检查，程序默认输出至本地： \n$dirPath/$JOB");
                # --强制更新至“本地”选项
                $machine_type_radio = 1;
                $lablePath -> configure(-text => "所选线地址不通，请检查，程序默认输出至本地： \n$dirPath/$JOB");
            }        
    }
}

sub changeLineShow
{
    destroy $head_6_1;
    $head_6_1=$machine_frame->Frame()-> pack(-side => 'left');
    # 
    if ($factory_type_radio == 1) {
        my $sel_f=1;
        for ("本地","2号线","3号线",'2&3号线') {
            
            $head_6_1-> Radiobutton(
                                    -font =>'微软雅黑 12',
                                    -text     => "$_",
                                    -variable => \$machine_type_radio,
                                    -relief   => 'flat',
                                    -value    => $sel_f,
                                    -command=> \&changePath
                                )-> pack(@p3);
            $sel_f++;
        }
    } elsif ($factory_type_radio == 2) {
        my $sel_f=1;
        for ("本地","三楼1号线","三楼2号线",'四楼1号线', '四楼2号线') {    
            $head_6_1-> Radiobutton(
                                    -font =>'微软雅黑 12',
                                    -text     => "$_",
                                    -variable => \$machine_type_radio,
                                    -relief   => 'flat',
                                    -value    => $sel_f,
                                    -command=> \&changePath
                                )-> pack(@p3);
            $sel_f++;
        }        
    }
}


###循环所有层并更新对应的可写状态
sub Loop_List
{
    my ($sel_type_val,$v_exist)=@_;
    ###当非批量选择量
    for my $lay_n (@layer_array){
        unless (not $sel_type_val and not $v_exist) {
            ###循环所有层，重置对应的层别
            if ($Layer_Info{$lay_n}{type} eq "$sel_type_val") {
                $sel_but{$lay_n}= ($v_exist eq 'yes') ? 1 : 0;                
            }
        }
        ###更新是否可写状态
        &Update_State($lay_n,$sel_but{$lay_n});
        ###更新X系数列参数
        if ($x_scale_change eq "0") {
            $same_scale_x="";
            $opt_frm_c{$lay_n} -> configure(-textvariable =>\$same_scale_x) if($sel_but{$lay_n} eq "1");
            $opt_frm_c{$lay_n} -> configure(-textvariable =>\$cs_scale_x) if($sel_but{$lay_n} eq "0");
        }else{
            #$scale_x{$lay_n}=$same_scale_x  if($sel_but{$lay_n} eq "1");
            $opt_frm_c{$lay_n} -> configure(-textvariable =>\$scale_x{$lay_n});
        }
        ###更新Y系数列参数
        if ($y_scale_change eq "0") {
            $same_scale_y="";
            $opt_frm_d{$lay_n}-> configure(-textvariable =>\$same_scale_y) if($sel_but{$lay_n} eq "1");
            $opt_frm_d{$lay_n}-> configure(-textvariable =>\$cs_scale_y) if($sel_but{$lay_n} eq "0");
        }else{
            #$scale_y{$lay_n}=$same_scale_y  if($sel_but{$lay_n} eq "1");
            $opt_frm_d{$lay_n}-> configure(-textvariable =>\$scale_y{$lay_n});
        }
    }
}

###更新可写/不可写状态
sub Update_State
{
    my($lay_n,$sel_but_val)=@_;
    $state=($sel_but_val eq "1") ? 'normal' : 'disabled';
    $opt_frm_f{$lay_n}-> configure(-state =>"$state");
    $opt_frm_e{$lay_n}-> configure(-state =>"$state");
}

#/********************************
# 函数名: Output_Set
# 功  能: 程序输出检测，并记录数据
# 参  数: 无
# 返回值: 无
#********************************/
sub Output_Set{	
	#检测盖孔镀孔层是否添加铜面积及是否正确
	&Check_gk_cu_areas;
    ###检测界面输入错误
    my $Check_Result=&Check_Input_Val;
	if ($Check_Result eq 'No_Error') {
		my $timestamp = time;		
		our $recode_file = '/tmp/'.$JOB.'_'.$softuser.'_'.$timestamp.'json';	
		if (-e $recode_file){
			unlink $recode_file;
		}	
		my $res = &Check_Output_layer;				
		if ($res == 0){			
			&getOutputParm;			
			destroy $mw;
			&Output_LDI_Main;
			#print "$tmp_file"
		} 
		
	} 
}

sub relode_layers_json{	
	# 打开 JSON 文件
	open(my $fh, '<', $recode_file) or die "无法打开文件: $recode_file, 错误信息: $!";
	local $/;
	my $json_text = <$fh>;
	close($fh);
	my $json = JSON->new;
	my $data = $json->decode($json_text);	
	print Dumper($data);
	if (-e $recode_file){
		unlink $recode_file;
	}	
	return $data;
}



#/********************************
# 函数名: Check_Output_layer
# 功  能: 检测输出层镜像以及极性是否正确
# 参  数: 无
# 返回值: 无
#********************************/

sub Check_Output_layer{
	# 调用程序检测以及选择象限	
	my @send_str; 
	for my $lay (@layer_array){
        if ($sel_but{$lay} == 1) {          
			push @send_str, $lay.','.$sel_mir{$lay}.','.$sel_pol{$lay};  			
        }        
    }	
	my $res = system("python /incam/server/site_data/scripts/sh_script/ldi_orbotech/check_layer_output_info.py $JOB $recode_file @send_str");
	return $res;
}

#/********************************
# 函数名: Check_gk_cu_areas
# 功  能: 检测镀孔盖孔层铜面积是否正确
# 参  数: 无
# 返回值: 无
#********************************/

sub Check_gk_cu_areas
{	
	my @selGkLayer;	
	foreach my $lay_n (@layer_array){
		if ($lay_n =~ /dk|gk/ && $sel_but{$lay_n} == 1){
			push @selGkLayer, $lay_n;			
		}
	}
	if (scalar(@selGkLayer) > 0){
		my $string = join(":", @selGkLayer);	
		my $res = system("python /incam/server/site_data/scripts/sh_script/ldi_orbotech/check_gk_cu_areas.py $JOB $string");
		if($res != 0){
			exit(0);
		}
	}	
}

#/********************************
# 函数名: Check_Input_Val
# 功  能: 界面输入值检测
# 参  数: 无
# 返回值: 错误信息
#********************************/
sub Check_Input_Val
{
    my $Error_Info="";
    ###当X轴系数一样时
    if ($x_scale_change == 0) {
        $Error_Info .= "所有层 X系数: $same_scale_x ; " if($same_scale_x !~ /^(-)?\d+(\.\d+)?$/);
    }
    ###当Y轴系数一样时
    if ($y_scale_change == 0) {
        $Error_Info .= "所有层 Y系数: $same_scale_y" if($same_scale_y !~ /^(-)?\d+(\.\d+)?$/);
    }
    
    ###循环所有行列表，只针对选择的部分
    my $selCount = 0;
    for my $lay_n (@layer_array){
        ###当行被选中时
        if($sel_but{$lay_n} == 1) {
			# 20250401 by ynh 当非正常匹配到盖孔层时候限制输出
			if ($lay_n =~ /-gk/){
				$Error_Info .= "$lay_n 层命名中含有gk，此程序不支持盖孔资料输出 ; ";
			}
            ###X、Y系数的检测
            if ($x_scale_change == 1){
                $Error_Info .= "$lay_n 层X系数: $scale_x{$lay_n} ; " if ($scale_x{$lay_n} !~ /^(-)?\d+(\.\d+)?$/);
            }
            if ($y_scale_change == 1){
                $Error_Info .= "$lay_n 层Y系数: $scale_y{$lay_n} ; " if ($scale_y{$lay_n} !~ /^(-)?\d+(\.\d+)?$/);
            }
            ###镜像及极性的检测  此处不检测  by ynh 20250512
            # if ($sel_mir{$lay_n} eq 'Null') {
                # $Error_Info .= "$lay_n 层镜像: $sel_mir{$lay_n} ; ";
            # }
            # if ($sel_pol{$lay_n} eq 'Null') {
                # $Error_Info .= "$lay_n 层极性: $sel_pol{$lay_n} ; ";
            # }
            # --当选择五厂时 暂不支持内层的输出
            if ($factory_type_radio == 1) {                
                if ($Layer_Info{$lay_n}{type} !~ /^(Outer)$/)
                {
                    $Error_Info .= "内层$lay_n 层，暂不支持输出 ; ";
                }
            }
            # Test by song 20190820             
            # === 20200.09.02 如果选择的层别是二次铜，则不允许输出LDI，正片
			#20241016 周涌通知所有用户都可以输出
			# if ($softuser ne '40249' && $softuser ne '44926' && $softuser ne '44566' && $softuser ne '44839' && $softuser ne '74648' ) {
				# if ($layer_stack{$lay_n}{flow_content} == 2) {
					# $Error_Info .= "层别$lay_n 二次铜流程，暂不支持输出; ";
				# }
			# }
			
            $selCount ++;
        }
    }
    
    ###当错误信息存在时提醒，并返回参数
    if ($Error_Info ne "") {
        &Messages("warning","$Error_Info\n\n以上参数有误，请重新输入！");
        return "Error";
    }elsif($selCount == 0){
        &Messages("warning","请选择需要输出的层！");
        return "Error";   
    }else{
        return "No_Error";
    }    
}

#/********************************
# 函数名: Get_Scale
# 功  能: 函数说明：获取所有层的系数内层取层上的数值
# 参  数: 无
# 返回值: 系数Hask
#********************************/
sub Get_Scale
{
    my (%scale_x,%scale_y);
    for my $lay_n (@layer_array){
        $scale_x{$lay_n} = 0;
        $scale_y{$lay_n} = 0;
    }
    ###返回两个Hash的指针
    return (\%scale_x,\%scale_y)
}

#/********************************
# 函数名: getOutputParm
# 功  能: 获取界面输出值
# 参  数: 无
# 返回值: 
#********************************/
sub getOutputParm
{	
	my $info_json = &relode_layers_json;
    for my $lay_n (@layer_array){
        if ($sel_but{$lay_n} == 1) {
            ###打印层别信息
            push @outLayer, $lay_n;
            # $outParm{$lay_n}{'Mir'} = $sel_mir{$lay_n};
            # $outParm{$lay_n}{'Pol'} = $sel_pol{$lay_n};
			
			# 镜像以及极性调用py生成的json文件获取				
			$outParm{$lay_n}{'Mir'} = $info_json->{$lay_n}{'mc'};
            $outParm{$lay_n}{'Pol'} = $info_json->{$lay_n}{'pol'};
		
            $outParm{$lay_n}{'Xscal'} = ($x_scale_change == 1) ? "$scale_x{$lay_n}, " : "$same_scale_x, ";
            $outParm{$lay_n}{'Yscal'} = ($y_scale_change == 1) ? "$scale_y{$lay_n}, " : "$same_scale_y, ";  
        }        
    }    
}

#********************************#
#函数名:Messages 窗体
#功  能: 无
#返回值:无
#********************************##
sub Messages
{
    my ($icon,$message)=@_;
    my $w=MainWindow->new();
    $w-> withdraw();
    $w-> messageBox(-title => '提醒', 
                    -message => "$message",
                    -type => 'OK', -icon => "$icon");                                       
    destroy $w;
}


##################################################################################
############################# 资料输出部分 #######################################
##################################################################################
#/********************************
# 函数名: Output_LDI_Main
# 功  能: 输出LDI资料
# 参  数: 无
# 返回值: 错误信息
#********************************/
sub Output_LDI_Main
{
    # --清除输出目录下的旧资料
    system("rm -rf $tmp_file/$JOB");
    
	# === V5.6.1 增加周期是否存在在于输出层别的检测
	my @check_date_layer;
	for my $lay (@outLayer){
		# === 仅外层检测 
		if ($Layer_Info{$lay}{type} eq 'Outer') {
			push @check_date_layer,$lay;
		}
	}
	if (@check_date_layer) {
		my $get_result = system("python $scriptPath/sh_script/ldi_orbotech/exist_date_code.py $sel_step @check_date_layer");
		if ($get_result != 0) {
			exit 0;
		}
	}
	my @check_sig_layer;
	for my $lay (@outLayer){
		# === 仅外层检测 
		if ($Layer_Info{$lay}{type} eq 'Outer' or $Layer_Info{$lay}{type} eq 'Inner' or $Layer_Info{$lay}{type} eq 'Sec') {
			push @check_sig_layer,$lay;
		}
	}
	if (@check_sig_layer) {
		my $get_result = system("python $scriptPath/lyh/auto_sh_hdi_check_rules.py check_aobao_danymic_text_info @check_sig_layer");
		if ($get_result != 0) {
			exit 0;
		}
	}
	
	my $get_result = system("python $scriptPath/lyh/auto_sh_hdi_check_rules.py check_output_layer_is_locked @outLayer");
	if ($get_result != 0) {
		exit 0;
	}
	
    # --重新打开需要输出的step
    $c->OPEN_STEP($JOB, $sel_step);
    $c->CHANGE_UNITS('mm');
    $c->CLEAR_LAYER();

    # $f->COM('disp_off');
    
    # --获取Panel尺寸
    $f->INFO(units => 'mm', entity_type => 'step',
         entity_path => "$JOB/$sel_step",
         data_type => 'PROF_LIMITS');    
    our $panel_x = $f->{doinfo}{gPROF_LIMITSxmax} - $f->{doinfo}{gPROF_LIMITSxmin};
    our $panel_y = $f->{doinfo}{gPROF_LIMITSymax} - $f->{doinfo}{gPROF_LIMITSymin};
    
    # --获取SR的信息
    $f->INFO(units => 'mm', entity_type => 'step',
         entity_path => "$JOB/$sel_step",
         data_type => 'SR_LIMITS');
    our $sr_min_x = $f->{doinfo}{gSR_LIMITSxmin};
    our $sr_min_y = $f->{doinfo}{gSR_LIMITSymin};
    our $sr_max_x = $f->{doinfo}{gSR_LIMITSxmax};
    our $sr_max_y = $f->{doinfo}{gSR_LIMITSymax};
    our $panel_cx = $panel_x/2;
    our $panel_cy = $panel_y/2;
	
	# --循环需要输出的层
    for my $lay (@outLayer)
    {
        $c->CLEAR_LAYER();
        $c->WORK_LAYER($lay);   
		# === 判断是否分割
		$c->FILTER_RESET();
        $c->SELECT_TEXT_ATTR('.fiducial_name', '300.measure', 1);
        $c->FILTER_SELECT();
		$c->FILTER_RESET();
		my $fg_num = int($c->GET_SELECT_COUNT());
		$c->CLEAR_FEAT();
		if ($fg_num != 0) {
			# 有分割标靶存在时不应该有317.reg存在，增加判断
			$c->SELECT_TEXT_ATTR('.fiducial_name', '317.reg', 1);
			$c->FILTER_SELECT();
			$c->FILTER_RESET();
			# --当前层无对就r0靶点时，进行添加
			if ($c->GET_SELECT_COUNT() != 0) {
				&Messages('warning', "层: $lay 分割设计,图形中r0(.fiducial_name=317.reg)对位靶点不应存在，请确认资料，程序退出");
				exit(1);
			}
			if ($fg_num % 4 != 0) {
				&Messages('warning', "层: $lay 分割图形中r0(.fiducial_name=300.measure)对位靶点数量不是4的整数倍，请确认资料，程序退出");
				exit(1);
			}
			$c->CLEAR_FEAT();
			$c->SELECT_TEXT_ATTR('.fiducial_name', '300.trmv', 1);
			$c->FILTER_SELECT();
			$c->FILTER_RESET();
			my $fg_vnum = int($c->GET_SELECT_COUNT());
			$c->CLEAR_FEAT();
			$c->SELECT_TEXT_ATTR('.fiducial_name', '300.trmh', 1);
			$c->FILTER_SELECT();
			$c->FILTER_RESET();
			my $fg_hnum = int($c->GET_SELECT_COUNT());
			$c->CLEAR_FEAT();
			if (($fg_vnum + $fg_hnum) == 0) {
				&Messages('warning', "层: $lay 分割图形中r0(.fiducial_name=300.trmv或.fiducial_name=300.trmh)不存在，请确认资料，程序退出");
				exit(1);
			}
			my $fg_times = $fg_num / 4;
			# === 二分割应该 分割线或者横线或者竖线
			if ($fg_times == 1) {
				&Messages('warning', "层: $lay 分割光点数量为4，不合理，请确认资料，程序退出");
				exit(1);
			} elsif  ($fg_times == 2) {
				if (($fg_vnum + $fg_hnum) != 1) {
					&Messages('warning', "层: $lay 光点数量为8应为2分割,分割线r0数量不正确,请确认资料，程序退出");
					exit(1);
				}
			} elsif ($fg_times == 3) {
				if ($fg_vnum == 2 || $fg_hnum == 2 ) {
				} else {
					&Messages('warning', "层: $lay 光点数量为12应为3分割,分割线r0数量应横向2或纵向2,\n目前数量不正确,请确认资料，程序退出");
					exit(1);
				}
			} elsif ($fg_times == 4) {
				if ($fg_vnum == 1 && $fg_hnum == 1 ) {
				} else {
					&Messages('warning', "层: $lay 光点数量为16应为4分割,分割线r0数量应横向1+纵向1,\n目前数量不正确,请确认资料，程序退出");
					exit(1);
				}
			} elsif ($fg_times == 6) {
				# 975-148A3  六分割 2022.02.23 
				if (($fg_vnum == 2 && $fg_hnum == 1) || ($fg_vnum == 1 && $fg_hnum == 2) ) {
				} else {
					&Messages('warning', "层: $lay 光点数量为24应为6分割,分割线r0数量应横向1+纵向2或者横向2+纵向1,\n 目前数量不正确,请确认资料，程序退出");
					exit(1);
				}			
			} else {
				&Messages('warning', "目前仅支持2分割及4分割, 层: $lay 光点数量 $fg_times\n数量不正确,请确认资料，程序退出");
				exit(1);
			}
		} else {
			# --判断图形中对位靶点个数,对应r0靶点属性是否存在,若数量不对，程序退出
			        # --判断输出层对应的inn(靶点参考层)是否存在，当不存在时，默认为芯板，且给出提示确认
			if (not exists $jobLayInn{$lay} or not defined $jobLayInn{$lay})
			{
				if (not defined $jobLayInn{$lay})
				{
					next;
				}else{
					my $reVal = $c->Messages_Sel('question', "未匹配到 $lay 层对应的LDI对位靶点参考层，确认是否为内层纯芯板？\n\n参考信息：\n\t有盲孔的层次都是 冲靶 给线路曝光 ， 没有盲孔的层次  就是 机钻靶孔给 线路曝光!纯内层芯板可不用提供对位靶点！\n\n(确定：程序继续运行   取消：程序退出，请手动添加r0)");
					if ($reVal =~ /Ok/i)
					{
						next;
					}else{
						exit 1;
					}
				}
				
			}
			if ($Layer_Info{$lay}{type} eq 'Inner') {
				my $reVal = $c->Messages_Sel('question', "$lay 是否为内层纯芯板？\n\n 按正常规则未匹配到定位孔信息。");
				if ($reVal =~ /Ok/i)
				{
					next;
				}else{
					exit 1;
				}
			}
		
			$c->SELECT_TEXT_ATTR('.fiducial_name', '317.reg', 1);
			$c->FILTER_SELECT();
			$c->FILTER_RESET();	
			if ($c->GET_SELECT_COUNT()  != 4) {
				&Messages('warning', "层: $lay 图形中r0(.fiducial_name=317.reg)对位靶点数量不等于4个，请修改资料后再运行程序");				
				exit();
			}
		}
		# === 靶点检测及添加结束 ===
        # --清除选择的物体，以免对后面操作造成影响
        $c->CLEAR_FEAT();		
		&CheckOrbLdiStamp($lay);		
		$c->CLEAR_FEAT();
		
    } 
	# --在返回数据前填充参考层 创建参考层，填充所有Panel中step区模拟安全区，添加Stamp图形时，以防盖到其它图形
    # &CreateAllStep_Surface;
    # --填充所有pnl_rout层及inn层用于添加LDI字样的检测。	
    # &CreateAllBar_Surface;	
	
    # --循环需要输出的层
    for my $lay (@outLayer)
    {
        $c->CLEAR_LAYER();
        $c->WORK_LAYER($lay);
        
        # --判断输出层对应的inn(靶点参考层)是否存在，当不存在时，默认为芯板，且给出提示确认
        if (not exists $jobLayInn{$lay} or not defined $jobLayInn{$lay})
        {
            if (not defined $jobLayInn{$lay})
            {
                goto CORE_INNER;
            }else{
                my $reVal = $c->Messages_Sel('question', "未匹配到 $lay 层对应的LDI对位靶点参考层，确认是否为内层纯芯板？\n\n参考信息：\n\t有盲孔的层次都是 冲靶 给线路曝光 ， 没有盲孔的层次  就是 机钻靶孔给 线路曝光!纯内层芯板可不用提供对位靶点！\n\n(确定：程序继续运行   取消：程序退出，请手动添加r0)");
                if ($reVal =~ /Ok/i)
                {
                    goto CORE_INNER;
                }else{
                    exit 1;
                }
            }
            
        }
		if ($Layer_Info{$lay}{type} eq 'Inner') {
			my $reVal = $c->Messages_Sel('question', "$lay 是否为内层纯芯板？\n\n 按正常规则未匹配到定位孔信息。");
			if ($reVal =~ /Ok/i)
			{
				goto CORE_INNER;
			}else{
				exit 1;
			}
		}	
      # --内层芯板跳转
   CORE_INNER:
		#  todo 变更以下为压合信息中cut_x,cut_y,baord_x,board_y
		my @clp_sz_mm = [$layer_stack{$lay}{'cut_x'}, $layer_stack{$lay}{'cut_y'}, $layer_stack{$lay}{'board_x'}, $layer_stack{$lay}{'board_y'}];
		if ($lay =~ /ls-kc-(.+)/ or $lay =~ /(l\d+)(-dk|-cm|-2)?(-ls\d{6}\.\d{4}.*)?$/){		
			my $tmpLayN = $1;
			# $c->PAUSE("$tmpLayN");
			@clp_sz_mm = [$layer_stack{$tmpLayN}{'cut_x'}, $layer_stack{$tmpLayN}{'cut_y'}, $layer_stack{$tmpLayN}{'board_x'}, $layer_stack{$tmpLayN}{'board_y'}];
			#print "-------------------->,$layer_stack{$tmpLayN}{'cut_x'}, $layer_stack{$tmpLayN}{'cut_y'}, $layer_stack{$tmpLayN}{'board_x'}, $layer_stack{$tmpLayN}{'board_y'},$tmpLayN ,$lay,\n";
		}      

		#exit 0;
        # --判断所选层别面向
		
        if ($outParm{$lay}{'Mir'} eq 'no') {
            imageSet($lay, 0, 0, 'no_swap');     
        }else{
            imageSet($lay, $panel_cx, 0, 'no_swap'); 
        }
        	
        # --添加奥宝LDI专用Stamp标记信息（供生产记录：涨缩系数/机器编号/时间/日期/lot号）
		#system("python /incam/server/site_data/scripts/sh_script/update_orbldi_stamp/update_orbldi_stamp.py $JOB");
        # --输出opfx格式资料
		# print Dumper(\@clp_sz_mm);		
        &outputOpfx($lay, @clp_sz_mm);
    } 	
	$c->COM("save_job,job=$JOB,override=no");	
	
	# 输出完成后直接不保存直接退出,然后重新打开JOB
	# &close_job_and_open;
		
    # --删除垃圾层
    # $c->DELETE_LAYER($_) for ($c->GET_MATCH_LIST($JOB, $tmpLay));
    # 删除临时料号文件夹,TODO 判断目录不为空的情况,不为空，删除动作执行失败返回0，成功返回1
	my $rmstatus = rmdir("$tmp_file/$JOB");

	if ($rmstatus == 0) {
		&Messages('info', "层: $lay 奥宝LDI资料输出过程中遭遇不可知问题，请回读检查或重新输出");	}
	
    &writeLog;
    
    # --输出完成提示（此处无需再次判断地址是否存在，因前面已判断，当地址不通时，无法选择对应项）
    #  待增加工厂的选择
    if ($factory_type_radio == 1) {
        if ($machine_type_radio == 4) {
            &Messages('info', "奥宝LDI资料输出完成！见目录: \n$machinePath_vgt5{'Sel_'.$machine_type_radio}[0] \n$machinePath_vgt5{'Sel_'.$machine_type_radio}[1]");
        }else{
            &Messages('info', "奥宝LDI资料输出完成！见目录: $machinePath_vgt5{'Sel_'.$machine_type_radio}");
        }
    } elsif ($factory_type_radio == 2) {
        &Messages('info', "奥宝LDI资料输出完成！见目录: $machinePath_hdi1{'Sel_'.$machine_type_radio}");
    }

}


# 检测是否添加添加奥宝stamp图形
sub CheckOrbLdiStamp{
	my ($addLay) = @_;
    $c->WORK_LAYER($addLay);
    $c->CLEAR_FEAT();
	# 判断旧的ldi图形是否存在，存在则删除orbldi_stamp，重新添加
    $c->FILTER_SET_INCLUDE_SYMS("orbldi_stamp");
    $c->FILTER_SELECT();
    $c->FILTER_RESET();
    if ($c->GET_SELECT_COUNT() > 0) {
        # print ("Stamp 图形为旧的，现在重新添加新的Stamp！\n");
        &Messages('warning', "层别：$addLay 中Stamp图形为旧的，请删除后重新添加！\n");
		exit();
    }
    $c->FILTER_SET_INCLUDE_SYMS("sh-sh");
    $c->FILTER_SELECT();
    $c->FILTER_RESET();
    if ($c->GET_SELECT_COUNT() > 0) {
        # print ("删除sh-sh Symbol，现在重新添加新的Stamp！\n");
        &Messages('warning', "层别：$addLay 中Stamp图形为旧的，请删除后重新添加！\n");
		exit();
    } 
	    # --判断Stamp图形是否存在
    $c->FILTER_SET_INCLUDE_SYMS("*hdi_orbldi_stamp_1*;*hdi_orbldi_stamp*");
    $c->FILTER_SELECT();
    $c->FILTER_RESET();
	if ($c->GET_SELECT_COUNT() == 0) {
		&Messages('warning', "层别：$addLay 未添加Stamp 图形，请添加后再输出！\n");
		exit();
	}else{
		$c->FILTER_SET_FEAT_TYPES('pad',1);
		$f->COM('sel_ref_feat,layers=,use=select,mode=touch,pads_as=shape,f_types=line\;pad\;surface\;arc\;text,polarity=positive\;negative,include_syms=,exclude_syms=');
		if ($c->GET_SELECT_COUNT() > 0) {
			print ("Stamp 图形与层别：$addLay 中其他pad有相交,请检查！\n");
			&Messages('warning', "Stamp 图形与层别：$addLay 中其他pad有相交,请检查！\n");			
			exit();			
		}
	}
}


# --添加奥宝stamp图形
sub addOrbLdiStamp
{
    my ($addLay) = @_;
    $c->WORK_LAYER($addLay);
    $c->CLEAR_FEAT();
    if ( defined $ENV{INCAM_PRODUCT} ) {
        #当在incam中时，替换hdi_orbldi_stamp_1 2019.11.21
        $f->COM("import_lib_item_to_job,src_category=symbols,src_profile=system,src_customer=,dst_names=hdi_orbldi_stamp_1");
		$f->COM("import_lib_item_to_job,src_category=symbols,src_profile=system,src_customer=,dst_names=hdi_orbldi_stamp");
    }
    
    # 判断旧的ldi图形是否存在，存在则删除orbldi_stamp，重新添加
    $c->FILTER_SET_INCLUDE_SYMS("orbldi_stamp");
    $c->FILTER_SELECT();
    $c->FILTER_RESET();
    if ($c->GET_SELECT_COUNT() > 0) {
        print ("Stamp 图形为旧的，现在重新添加新的Stamp！\n");
        $c->SEL_DELETE();
    }
    $c->FILTER_SET_INCLUDE_SYMS("sh-sh");
    $c->FILTER_SELECT();
    $c->FILTER_RESET();
    if ($c->GET_SELECT_COUNT() > 0) {
        print ("删除sh-sh Symbol，现在重新添加新的Stamp！\n");
        $c->SEL_DELETE();
    }    
    
    # --判断Stamp图形是否存在，若存在刚可不添加
    $c->FILTER_SET_INCLUDE_SYMS("*hdi_orbldi_stamp_1*;*hdi_orbldi_stamp*");
    $c->FILTER_SELECT();
    $c->FILTER_RESET();
    if ($c->GET_SELECT_COUNT() > 0) {
		# === 2021.10.11 增加是否与本层pad touch的检测
		$c->FILTER_SET_FEAT_TYPES('pad',1);
		$f->COM('sel_ref_feat,layers=,use=select,mode=touch,pads_as=shape,f_types=line\;pad\;surface\;arc\;text,polarity=positive\;negative,include_syms=,exclude_syms=');
		if ($c->GET_SELECT_COUNT() > 0) {
			print ("Stamp 图形与层别：$addLay 中其他pad有相交,请检查！\n");
			&Messages('warning', "Stamp 图形与层别：$addLay 中其他pad有相交,请检查！\n");
			exit(1);
		} else {
			print ("Stamp 图形已添加无须再次添加，跳过！\n");
			$c->CLEAR_FEAT();
			return
		}
    }
    
    # --判断drl层是否存在
    my $drlExists =  $c->LAYER_EXISTS($JOB, $STEP,'drl');
    
    # --创建辅助层
    my $tmpLayer = "${addLay}_tmp++";
    $c->DELETE_LAYER($tmpLayer);
    $c->CREATE_LAYER($tmpLayer);
    $c->WORK_LAYER($tmpLayer);
    
    # --获取最后一 次压合后的锣边尺寸
    #my @yhCoor = split(',', &getYHsize());
    # --获取右边预留边的坐标    
    # --取出两头的预留边，取最大的一个值，因为有时存在有Coupon添加于短边
    my $sr_u = $panel_y - $sr_max_y;
    #my $srMax = $sr_u > $sr_min_y ? $sr_u : $sr_min_y;
    my %srInfo = &getSrMinMax;
    my $Y_srMin = $srInfo{'srYmin'};
    my $X_srMin = $srInfo{'srXmin'};
    my $Y_srMax = $srInfo{'srYmax'};
    
    print "Y_srMin:$Y_srMin X_srMin:$X_srMin Y_srMax:$Y_srMax\n";
    
    # --取出短边锣掉的尺寸
    #my $panel_yl_y = ($panel_y - $yhCoor[1]) / 2;
    # 2019.11.16更改位置同板边添加的sh-sh位置
    my $addLdi_x = $X_srMin  + 60.96 + 53.34;
    #my $addLdi_y = $Y_srMax + 4.5; # --由下短边改到上短边
    # --由上短边改到下短边 song 2019.11.16 由于要使用sh-shsymbol的位置，即 88888 SH 888888的位置。与工艺卢仁义的沟通结果，需求
    # http://192.168.2.120:82/zentao/story-view-566.html
    my $addLdi_y = $Y_srMin - 5;  
    #my $addLdi_y = ($Y_srMin > $panel_yl_y  + 7) ? ($panel_yl_y  + 5) : 2 ; # --判断Stamp图形是否会加到板内去
    
    #$f->PAUSE(" $yhCoor[1] , $sr_min_y, $panel_yl_y, $addLdi_y");
    # --添加的角度（加短边时，需要旋转）
    #my $addAngle = (lc($outParm{$addLay}{'Mir'}) eq 'no') ? '0' : '180';
    # 更改加在短边时加为0度，反面镜像。song 2019.11.16
    my $addAngle = 0;
    #my $addMir = (lc($outParm{$addLay}{'Mir'}) eq 'no') ? 'no' : 'yes';

    
    # --循环添加40次，每次移动一定距离，尝试避开
    for (1..40)
    {
        #my $length = @stampCoor;
        # 暂时先修改为不套用，每层添加 Song 2019.11.18 内外层避开symbol不同，经常重叠。
        my $length = 1;
        
        # --当记录的stamp坐标为2时，直接按记录的stamp坐标进行添加
        if ($length == 2 ) {
            # --添加单个Pad
            $c->ADD_PAD_SINGLE($stampCoor[0], $stampCoor[1], 'hdi_orbldi_stamp_1', 'positive', 'no', $addAngle, lc($outParm{$addLay}{'Mir'}));
            # --移动到对应层，并删除辅助层
            $c->SEL_MOVE($addLay, 'no', 0);
            $c->DELETE_LAYER($tmpLayer);
            return
        }
        
        # --添加单个Pad
        $c->ADD_PAD_SINGLE($addLdi_x, $addLdi_y, 'hdi_orbldi_stamp_1', 'positive', 'no', $addAngle, lc($outParm{$addLay}{'Mir'}));
        # --与参考层进行touch (需改为drl的Flaten层,此方案效率低，需要优化，如填充step 去touch填充的surface)
        $c->SEL_REF_FEAT("$addLay", 'touch', 'positive;negative', 'line;pad;arc;text', '', 'panel_symbol_*'); #\;__tmp__++drl
        # --发现有些料号没有通孔drl层，比如 525*R29A2
        if ($drlExists eq 'yes')
        {
            $c->SEL_REF_FEAT("drl\;${tmpLay}flatten++\;${tmpLay}ref++", 'touch', 'positive;negative', 'line;pad;arc;text;surface'); #\;__tmp__++drl
        }else{
            $c->SEL_REF_FEAT("${tmpLay}flatten++\;${tmpLay}ref++", 'touch', 'positive;negative', 'line;pad;arc;text;surface'); #\;__tmp__++drl
        }
        
        
        # --当有物体被选中时，删除重新添加
        if ($c->GET_SELECT_COUNT() > 0)
        {
            $c->SEL_DELETE();
            $addLdi_x  += 4;
        }else{
            # --移动前先获取最终的位置，以供下一层直接套用,先判断stamp图形是否还存在
            &rememberStampCoor($tmpLayer);
            
            # --移动到对应层，并删除辅助层            
            $c->SEL_MOVE($addLay, 'no', 0);
            $c->DELETE_LAYER($tmpLayer);
            last;
        }
        # --当移动20次仍然无法避开时，提示用户（暂未考虑是否会超出Panel尺寸）
        if ($_ == 40) {
            $c->ADD_PAD_SINGLE($addLdi_x, $addLdi_y, 'hdi_orbldi_stamp_1', 'positive', 'no', $addAngle, lc($outParm{$addLay}{'Mir'}));
            AGAIN:
            &Messages('warning', "提醒：\n\t程序需要添加LDI stamp图形，但无法自动避开，请参考 $addLay 层避开。然后继续");
            $c->WORK_LAYER($addLay, 2);
            $c->PAUSE("Pause ...");
            
            # --防止当事人仍然没移动
            # --与参考层进行touch (需改为drl的Flaten层,此方案效率低，需要优化，如填充step 去touch填充的surface)
            $c->WORK_LAYER($tmpLayer);
            $c->SEL_REF_FEAT("$addLay", 'touch', 'positive;negative', 'line;pad;arc;text', '', 'panel_symbol_*'); #\;__tmp__++drl
            if ($drlExists eq 'yes')
            {
                $c->SEL_REF_FEAT("drl\;${tmpLay}flatten++", 'touch', 'positive;negative', 'line;pad;arc;text;surface'); #\;__tmp__++drl
            }else{
                $c->SEL_REF_FEAT("${tmpLay}flatten++", 'touch', 'positive;negative', 'line;pad;arc;text;surface'); #\;__tmp__++drl
            }
                
            # --当有物体被选中时，删除重新添加
            if ($c->GET_SELECT_COUNT() > 0)
            {
                goto AGAIN;
            }
            
            # --移动前先获取最终的位置，以供下一层直接套用,先判断stamp图形是否还存在
            &rememberStampCoor($tmpLayer);
            
            # --移动到对应层，并删除辅助层
            $c->SEL_MOVE($addLay, 'no', 0);
            $c->DELETE_LAYER($tmpLayer);            
            last;
        }
    }    
}

# --记住Stamp
sub rememberStampCoor
{
    my $tmpLayer = shift;
    # --移动前先获取最终的位置，以供下一层直接套用,先判断stamp图形是否还存在
    $c->FILTER_SET_INCLUDE_SYMS("hdi_orbldi_stamp_1");
    $c->FILTER_SELECT();
    $c->FILTER_RESET();
    if ($c->GET_SELECT_COUNT() == 1) {
        
        my $infoLogFile = "$tmp_file/genesisinfo".int(rand(9999)).".log";
        $c->INFO_TO_FILE("info,out_file=$infoLogFile,units=mm,args= -t layer -e $JOB/$sel_step/$tmpLayer -d FEATURES -o select");        
        open INFO,$infoLogFile;        
        while( <INFO> )
        {
            chomp($_);
            if ( $_ =~ /^\#P.*/ ) 
            {
                my @tmpData = split(" ",$_);
                if($tmpData[1] ne "" and $tmpData[2] ne "")
                {
                    push @stampCoor,$tmpData[1];
                    push @stampCoor,$tmpData[2];
                }
            }
        }
        close INFO;
        unlink $infoLogFile;
    }
}

# --图形信息的参数设定
sub imageSet
{
    my ($lay, $xmirror, $ymirror, $SWAP) = @_;
    #$f->COM("image_open_elpd,job=$JOB,step=$sel_step,layer=$lay,units=mm,device_type=DP100");
    $f->COM("image_set_elpd2,job=$JOB,step=$sel_step,layer=$lay,device_type=DP100,polarity= $outParm{$lay}{'Pol'},\
            speed=0,xstretch=100,ystretch=100,xshift=0,yshift=0,xmirror=$xmirror,ymirror=$ymirror,xcenter=$panel_cx,\
            ycenter=$panel_cy,minvec=0,advec=0,minflash=0,adflash=0,conductors1=0,conductors2=0,conductors3=0,conductors4=0,\
            conductors5=0,media=first,smoothing=smooth,swap_axes=$SWAP,define_ext_lpd=yes,resolution_value=2,\
            resolution_units=micron,quality=auto,enlarge_polarity=both,enlarge_other=leave_as_is,enlarge_panel=no,\
            enlarge_contours_by=0,overlap=no,enlarge_image_symbols=no,enlarge_0_vecs=no,enlarge_symbols=none,\
            enlarge_symbols_by=0,symbol_name1=,enlarge_by1=0,symbol_name2=,enlarge_by2=0,symbol_name3=,enlarge_by3=0,\
            symbol_name4=,enlarge_by4=0,symbol_name5=,enlarge_by5=0,symbol_name6=,enlarge_by6=0,symbol_name7=,\
            enlarge_by7=0,symbol_name8=,enlarge_by8=0,symbol_name9=,enlarge_by9=0,symbol_name10=,enlarge_by10=0");
}

# --从当前层中取出板角图形（用于添加r0定位靶点）
sub Get_BD_Symbol
{    
    my $workLay = shift;
    my $ckWorkLay = $jobLayInn{$workLay}; # --定义参考层 “GET_LAYER_INN”方法中有初始化
    my @fourCoor=[];
	
	
    # --判断对应r0靶点属性是否存在(正片的r0)
    $c->WORK_LAYER ($workLay);
    # --判断对应r0靶点属性是否存在(正片的r0)
    $c->FILTER_SET_POL('positive', 1);
    $c->SELECT_TEXT_ATTR('.fiducial_name', '317.reg');
    $c->FILTER_SELECT();
    $c->FILTER_RESET();
    # --当选择的靶点数量不对时，删除后面重新添加
    if ($c->GET_SELECT_COUNT() != 0 and $c->GET_SELECT_COUNT() != 4) {
        ##&Messages('warning', "当前层选择的靶点数量不对时，返回错误信息")
        # --删除重新添加
        $c->SEL_DELETE(); 
    }
    
    # --当数量匹配时，无需再添加，但需要记录其坐标
    if ( $c->GET_SELECT_COUNT() == 4) {
        # --TODO判断四个孔是否正确
        
    
        # --取出四个点的坐标，一个角只需要一个即可
        @fourCoor = &get4Coor($workLay);
        return @fourCoor;
    }
    
    # --选择图形

	# --当存在激光孔时，即存在次外层，即以次外层对应的inn层为准
	if ($outInn eq 'no')
	{
		$c->WORK_LAYER ($ckWorkLay);		
		# $c->FILTER_SET_INCLUDE_SYMS("r3683\;r3150\;sh-dwsd2014"); # sh-dwsd2014 为HDI最新板边阻焊对位Pad
		$c->FILTER_SET_INCLUDE_SYMS("r3683\;r3150\;sh-dwtop2013\;sh-dwbot2013"); # sh-dwsd2014 为HDI最新板边阻焊对位Pad
		$c->SEL_REF_FEAT("m1\;m2","disjoint","positive\;negative","pad",,);
		#$c->FILTER_SELECT();
		$c->FILTER_RESET();

	}else{
		
		$c->WORK_LAYER ($ckWorkLay);
		$c->FILTER_SET_TYP('pad',1);
		$c->FILTER_SET_POL('positive');
		$c->FILTER_SELECT();
		$c->FILTER_RESET();
		
	}
        
    # --判断是否有选择到图形
    if ($c->GET_SELECT_COUNT() > 0)
    {
        # --取出四个点的坐标，一个角只需要一个即可
        @fourCoor = &get4Coor($ckWorkLay);
    }else{
        $c->WORK_LAYER ($workLay);
        # 适用于多层，当上面都取不到时，则在当前层（外层）取方向孔的图形
        $c->FILTER_SET_INCLUDE_SYMS("sh-fxpad315\;sh-pindonut");
        # $c->FILTER_SET_INCLUDE_SYMS("sh-dwsd2014");
        $c->FILTER_SELECT();
        $c->FILTER_RESET();
        
        if ($c->GET_SELECT_COUNT() > 0)
        {
            @fourCoor = &get4Coor($ckWorkLay);
        }
    }
       
    # --返回一个四坐标数组
    return @fourCoor;
}

# --获取四个点的坐标
sub get4Coor
{
    my $workLay = shift;
    my @allCoor=[];
    my @fourCoor=[];
    my $infoLogFile = "$tmp_file/genesisinfo".int(rand(9999)).".log";
    $c->INFO_TO_FILE("info,out_file=$infoLogFile,units=mm,args= -t layer -e $JOB/$sel_step/$workLay -d FEATURES -o select");        
    open INFO,$infoLogFile;        
    while( <INFO> )
    {
        chomp($_);
        if ( $_ =~ /^\#P.*/ ) 
        {
            my @tmpData = split(" ",$_);
            #$f->PAUSE("$tmpData[1],$tmpData[2]");
            push @allCoor,[$tmpData[1],$tmpData[2]] if($tmpData[1] ne "" and $tmpData[2] ne "");
        }
    }
    close INFO;
    unlink $infoLogFile;
    
    # --当传入的坐标就是三个或四个时，无须继续查找
	# ==20200507 更改判断条件，屏蔽三点定位
    #if (scalar @allCoor == 3 or scalar @allCoor == 4)
	if (scalar @allCoor == 4)

    {
        return @allCoor
    }
    
    # --循环所有坐标，取出符合条件的坐标:左下(左下有两个需要找另一个防呆孔)
    my @ldHole;
    for (@allCoor)
    {
        next if($_->[0] eq "" or $_->[1] eq "");
        # --左下取一个
        if ($_->[0] < $panel_x/2 and $_->[1] < $panel_y/2) {
            push @ldHole, [$_->[0],$_->[1]];
        }
    }
    # --取出X轴坐标最大的一个
    my $max_X = $ldHole[0]->[0];
    my @fdCoor = [$ldHole[0]->[0], $ldHole[0]->[1]];
    for (@ldHole)
    {
        if ($_->[0] > $max_X) {            
            @fdCoor = [$_->[0],$_->[1]];
        }
    }
    # --添加防呆孔坐标至@fourCoor坐标中
    push @fourCoor, [$fdCoor[0]->[0], $fdCoor[0]->[1]];
    
    # --循环所有坐标，取出符合条件的坐标:右下
    for (@allCoor)
    {
        next if($_->[0] eq "" or $_->[1] eq "");
        # --右下取一个
        if ($_->[0] > $panel_x/2 and $_->[1] < $panel_y/2) {
            push @fourCoor, [$_->[0],$_->[1]];
            last;
        }
    }
    # --循环所有坐标，取出符合条件的坐标:右上
    for (@allCoor)
    {
        next if($_->[0] eq "" or $_->[1] eq "");
        # --右上取一个
        if ($_->[0] > $panel_x/2 and $_->[1] > $panel_y/2) {
            push @fourCoor, [$_->[0],$_->[1]];
            last;
        }
    }
    # --循环所有坐标，取出符合条件的坐标:左上
    for (@allCoor)
    {
        next if($_->[0] eq "" or $_->[1] eq "");
        # --左上取一个
        if ($_->[0] < $panel_x/2 and $_->[1] > $panel_y/2) {
            push @fourCoor, [$_->[0],$_->[1]];
            last;
        }
    }
    
    # --返回四个坐标
    return @fourCoor
}

# --输出OPFX格式资料
sub outputOpfx
{	
    my ($out_Lay, @clp_sz_mm)=@_;
    # --初始化
    $f->COM("output_layer_reset");
    $f->COM("output_layer_set,layer=$out_Lay,angle=0,mirror=no,x_scale=1,y_scale=1,comp=0,polarity=positive,setupfile=,\
            setupfiletmp=,line_units=mm,gscl_file=,step_scale=no");
			
	if ($clp_sz_mm[0]->[2] eq '') {
		&Messages('warning',"抓取不到erp信息，需找mi录入!");	
		exit(0);
    }
    # --资料输出
    #$f->VOF();
    # scale_mode=nocontrol判定为scale mode 选择为scale features
    # 2019.12.06 更改scale_mode=all为scale_mode=nocontrol，使out_scale的图形不拉伸
    #$f->COM("output,job=$JOB,step=$sel_step,format=DP100X,dir_path=$dirPath/$JOB,prefix=,\
    #        suffix=,break_sr=no,break_symbols=no,break_arc=no,scale_mode=nocontrol,surface_mode=contour,units=mm,\
    #        x_anchor=$panel_cx,y_anchor=$panel_cy,x_offset=0,y_offset=0,line_units=mm,override_online=yes,local_copy=yes,send_to_plotter=no,\
    #        dp100x_lamination=0,dp100x_clip=0,clip_size=$clp_sz_mm[0]->[0] $clp_sz_mm[0]->[1],clip_orig=0 0,clip_width=$clp_sz_mm[0]->[0],clip_height=$clp_sz_mm[0]->[1],\
    #        clip_orig_x=0,clip_orig_y=0,plotter_group=any,units_factor=0.1,auto_purge=no,entry_num=5,plot_copies=999,\
    #        dp100x_iserial=1,imgmgr_name=LDI,deliver_date=");
	# 2020.03.30,更改输出路径为临时目录
	# 2022.04.22 LDI输出由开料板尺寸输出更改为由实际板尺寸输出
    $f->COM("output,job=$JOB,step=$sel_step,format=DP100X,dir_path=$tmp_file/$JOB,prefix=,\
            suffix=,break_sr=no,break_symbols=no,break_arc=no,scale_mode=nocontrol,surface_mode=contour,units=mm,\
            x_anchor=$panel_cx,y_anchor=$panel_cy,x_offset=0,y_offset=0,line_units=mm,override_online=yes,local_copy=yes,send_to_plotter=no,\
            dp100x_lamination=0,dp100x_clip=0,clip_size=$clp_sz_mm[0]->[2] $clp_sz_mm[0]->[3],clip_orig=$clp_sz_mm[0]->[0] $clp_sz_mm[0]->[1],clip_width=$clp_sz_mm[0]->[2],clip_height=$clp_sz_mm[0]->[3],\
            clip_orig_x=$clp_sz_mm[0]->[0],clip_orig_y=$clp_sz_mm[0]->[1],plotter_group=any,units_factor=0.01,auto_purge=no,entry_num=5,plot_copies=999,\
            dp100x_iserial=1,imgmgr_name=LDI,deliver_date=");	
	
    my $Status=$f->{STATUS};
    #$f->VON();
    # --当未能正常输出时，输出报错信息
    if ($Status ne '0') {
		if ($Status == 649001) {
			&Messages('warning',"Error:$Status $out_Lay 资料输出异常,发生内部错误，请查看后台信息！");
		}	
		elsif ($Status == 649012){
			&Messages('warning',"Error:$Status $out_Lay 资料输出异常,存在非法text添加了奥宝stamp属性，请查看后台Illegal Stamp 位置对应的text信息！");
		}
		else {
			&Messages('warning',"Error:$Status $out_Lay 资料输出异常,发生SIP错误，请定位至问题点修复此问题！");
		}		
        exit(1);
    }
    # --增加选择工厂，及输出路径
    if ($factory_type_radio == 1) {
        # vgt 五 厂
        # --当选择四时。默认输出至两台机
        if ($machine_type_radio == 4) {
            # --重命名此层名（默认输出的带输出次数）,复制至网络地址，本地留作备份
            system("cp $tmp_file/$JOB/$JOB\@${out_Lay}-* $machinePath_vgt5{'Sel_'.$machine_type_radio}[0]/$JOB\@$out_Lay");
            system("cp $tmp_file/$JOB/$JOB\@${out_Lay}-* $machinePath_vgt5{'Sel_'.$machine_type_radio}[1]/$JOB\@$out_Lay");
        }else{
            # --当选择输出本地时，需要重命名
            if ($machine_type_radio != 1) {
                system("cp $tmp_file/$JOB/$JOB\@${out_Lay}-* $machinePath_vgt5{'Sel_'.$machine_type_radio}/$JOB\@$out_Lay");
            }
        }
    } elsif ($factory_type_radio == 2) {
        # HDI 一 厂
        # --当选择输出本地时，需要重命名
        if ($machine_type_radio != 1) {
           system("cp $tmp_file/$JOB/$JOB\@${out_Lay}-* $machinePath_hdi1{'Sel_'.$machine_type_radio}/$JOB\@$out_Lay");
        }
    } 

    # --重命名本地文件（默认输出的带输出次数）
    #system("mv $dirPath/$JOB/$JOB\@${out_Lay}-* $dirPath/$JOB/$JOB\@$out_Lay"); # 此命令会误认为移动的是目录，而报错
    # print "find $dirPath/$JOB/ -name $JOB\@${out_Lay}-* | xargs -i mv {} $dirPath/$JOB/$JOB\@$out_Lay\n";
    # system ("find $dirPath/$JOB/ -name $JOB\@${out_Lay}-* | xargs -i mv {} $dirPath/$JOB/$JOB\@$out_Lay");
    unlink "$dirPath/$JOB/LDI_2.0Micron/$JOB\@$out_Lay" if (-e "$dirPath/$JOB/LDI_2.0Micron/$JOB\@$out_Lay");
    unlink "$dirPath/$JOB/LDI_1.5Micron/$JOB\@$out_Lay" if (-e "$dirPath/$JOB/LDI_1.5Micron/$JOB\@$out_Lay");
	
	mkdir("$dirPath/$JOB") unless(-d "$dirPath/$JOB"); 
    mkdir("$dirPath/$JOB/LDI_2.0Micron") unless(-d "$dirPath/$JOB/LDI_2.0Micron"); 
    mkdir("$dirPath/$JOB/LDI_1.5Micron") unless(-d "$dirPath/$JOB/LDI_1.5Micron"); 
    
	# 2020.03.31 料号中如果层别带点(.)会影响下方的grep动作
    

	my $grepLay = ${out_Lay};
	$grepLay =~ s/\.//g;
	
    my $renameFile = `ls $tmp_file/$JOB | grep ${JOB}\@${grepLay}-`;
    chomp $renameFile;
	# print("--------> $tmp_file/$JOB/$renameFile");
	# print($renameFile);
    if (-e "$tmp_file/$JOB/$renameFile")
    {
        my $File_20Mic = "$dirPath/$JOB/LDI_2.0Micron/$JOB\@$out_Lay";
        my $File_15Mic = "$dirPath/$JOB/LDI_1.5Micron/$JOB\@$out_Lay";
        
        system("mv $tmp_file/$JOB/$renameFile $File_20Mic");
        
        # --备份出一份1.5um解析度以适用于HDI 二处高精度设备
        
        my @highResData = ();
        open(rf, "< $File_20Mic") or die "源文件打开失败! $!";
        while(<rf>){
            chomp;
            $_ =~ s/RESOLUTION = 2.000000, micron/RESOLUTION = 1.500000, micron/;
            push @highResData, "$_\n";
        }
        close(rf);
        if(@highResData != 0) {
            open(wf, "+>$File_15Mic") or die "$!";
            print wf @highResData;
            close(wf);
        }
    }
}

sub close_job_and_open{
	$f->COM("check_inout,mode=in,type=job,job=$JOB");
	$f->COM("close_job,job=$JOB");
	$f->COM("check_inout,mode=out,type=job,job=$JOB");
	$f->COM("open_job,job=$JOB");
	$f->COM("open_entity,job=$JOB,type=step,name=$sel_step");
}

# --取出最大的SR信息
sub getSrMinMax
{
    $f->INFO(units => 'mm', entity_type => 'step', entity_path => "$JOB/panel", data_type => 'SR');
    my $srXmin = 99999999999999;
    my $srXmax = -9999999999999;
    my $srYmin = 99999999999999;
    my $srYmax = -9999999999999;

    #$f->PAUSE("$srXmin, $srXmax, $srYmin, $srYmax");
    for (my $i = 0; $i < @{$f->{doinfo}{gSRstep}} ; $i++)
    {
        $curStep = ${$f->{doinfo}{gSRstep}}[$i];
        if ($curStep =~ /^(set(_?)(?:\d+)?|edit(?:\d+)?|edit-f*|set-f*)$/) { # |coupon(?:-)?(?:\d+)?)
            $srXmin =($srXmin > ${$f->{doinfo}{gSRxmin}}[$i]) ? ${$f->{doinfo}{gSRxmin}}[$i] : $srXmin;
            $srXmax =($srXmax < ${$f->{doinfo}{gSRxmax}}[$i]) ? ${$f->{doinfo}{gSRxmax}}[$i] : $srXmax;
            $srYmin =($srYmin > ${$f->{doinfo}{gSRymin}}[$i]) ? ${$f->{doinfo}{gSRymin}}[$i] : $srYmin;
            $srYmax =($srYmax < ${$f->{doinfo}{gSRymax}}[$i]) ? ${$f->{doinfo}{gSRymax}}[$i] : $srYmax;
        }
    }
    #$f->PAUSE("$srXmin, $srXmax, $srYmin, $srYmax");
    my %SR_INFO = (
        'srXmin' => $srXmin,
        'srXmax' => $srXmax,
        'srYmin' => $srYmin,
        'srYmax' => $srYmax        
    );
    #$c->Messages('info', "$SR_INFO{'srYmin'}");
    # --返回Hash信息
    return %SR_INFO;
}

# --创建参考层，填充所有Panel中step区域，添加Stamp图形时，以防盖到其它图形
sub CreateAllStep_Surface
{	
    $c->DELETE_LAYER("${tmpLay}flatten++");	
    $c->DELETE_LAYER("${tmpLay}fn++");	
    $c->CREATE_LAYER("${tmpLay}fn++");	
    $c->WORK_LAYER("${tmpLay}fn++");	
    $c->FILL_PARAMS;
    # $c->SR_FILL('positive', 0, 0, 2540, 2540, 0, 0, 0, 0); # --因涉及nest_sr参数设置为'no'，pm无法支持
    $f->COM("sr_fill,polarity=positive,step_margin_x=0,step_margin_y=0,step_max_dist_x=2540,step_max_dist_y=2540,sr_margin_x=0,\n
            sr_margin_y=0,sr_max_dist_x=0,sr_max_dist_y=0,nest_sr=no,consider_feat=no,consider_drill=no,consider_rout=no,dest=affected_layers,attributes=no");
    
    # --打散出安全区域
    $f->COM("sel_break_isl_hole,islands_layer=isl_lyr+++,holes_layer=${tmpLay}flatten++");
    # --清除垃圾层
    
    $c->DELETE_LAYER("isl_lyr+++");
    $c->DELETE_LAYER("${tmpLay}fn++");
    
    return ;
}

# --创建参考层，inn层 pnl_rout层
sub CreateAllBar_Surface
{
    $c->DELETE_LAYER("${tmpLay}ref++");
    $c->CREATE_LAYER("${tmpLay}ref++");
    
    foreach $line (@ref_array) 
    {
        $c->AFFECTED_LAYER($line,"yes");
        $c->SEL_COPY("${tmpLay}ref++","no","0");
        
        # TODO循环所有参考层，copy到每个step生成的surface层别
    }
    
    $c->CLEAR_LAYER();
    
    return ;
}

# 获取当前系统IP地址
sub getCurrentIp
{
    # 如果是Linux系统需要更改以下ipconfig为ifconfig
    my $cmd="hostname";
    my $output=`$cmd`;
    print $output;
     
    my $cmd_1 = "ipconfig";
    if ( $^O eq 'linux' ) {
        $cmd_1 = "ifconfig";
    }
    my $output_1 = `$cmd_1`;
    my $line;
    my @ip ;
    my @array = split(/\n/,$output_1);
    foreach $line (@array) 
    {
        if ($line =~ m/IPv4 .*(\.\s)+: (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})/)
        #\d{a,b}： 匹配数字，最少为a位，最多为b位
        {                    
            push (@ip , $2);
            #last;
        }
    }
    return @ip;
}

# 增加日志写入
sub writeLog
{   
    my $dbc_m = $o->CONNECT_MYSQL('host'=>'192.168.2.19', 'dbname'=>'engineering', 'port'=>'3306', 'user_name'=>'root', 'passwd'=>'k06931!');
    if (! $dbc_m)
    {
        $c->Messages('warning', '"工程数据库"连接失败-> 写入日志程序终止!');
        #exit(0);
        return;
    }
    # 获取用户名

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
    # --循环需要输出的层
    for my $lay (@outLayer)
    {
        my $layer_info = Data::Dumper->new([\$Layer_Info{$lay}],[qw(layer_info)]);
        my $layData = $layer_info->Dump;
        $layData =~ s/'/''/g;

        my $layScaleX = $scale_x{$lay};
        my $layScaleY = $scale_y{$lay};
        my $layMir = $lay_Mir{$lay};
        #写入hash开始 
    
        my $sql = "insert into ldi_output_log
        (job,layer,ScaleX,ScaleY,Mirror,Hash_LayerInfo,log_time,creator,localhost,software_platform,app_Version)
        values ('$JOB','$lay','$layScaleX','$layScaleY','$layMir','$layData',now(),'$softuser','$ophost','$plat','$VerSion')";
        
        my $sth = $dbc_m->prepare($sql);#结果保存在$sth中
        $sth->execute() or die "无法执行SQL语句:$dbc_m->errstr";
    }
    $dbc_m->disconnect if ($dbc_m);   
}

__DATA__
五厂奥宝LDI资料输出程序更新位置:
\\172.20.47.216\d$  (如无法访问使用机器本地管理员帐号：172.20.47.216\orbldi 密码：orbldi)

__END__
2019.04.28更新如下：
升级版本：2.3
1.增加sh-dwtop2013\;dwbot2013两种类型的板角Symbol

2019.05.16更新如下:
升级版本：3.1
背景-因*336*438*e3版本生产曝反(不是上下面反，而是被旋转了180度)导致4片板报废；
1.更新板角孔选择逻辑，不再使用外层的图形进行选择，直接匹配对应的阻焊层，当无阻焊层是提示错误并退出

2019.05.21更新如下：
升级版本：3.2
背景：226-039C1无法打印出系数信息，原因是Panel预留边有添加WK Step，导致取出的最小的SR信息不准
1.更新判断SR的最小值的算法，并从成型边往外算

2019.05.22更新如下：
升级版本：3.3
1.创建参考层，填充所有Panel中step区域，添加Stamp图形时，以防盖到其它图形 （新增CreateAllStep_Surface函数）
2.修改Stamp图形添加位置，由下短边改到上短边，因为下短边有钻带的涨缩系统及机台信息
升级版本：3.4
3.修改打开各STEP时，默认为MM单位
4.修改客户机，config文件，默认为MM单位

2019.05.28更新如下：
升级版本：3.5
1.修复当存在flip时，无法完成填充STEP的操作，导致无法计算出最小的SR值报错问题 Bug型号：104-068D2

2019.05.31更新如下：
升级版本：3.6
1.应滕正前要求取消SWAP参数，生产员工统一横向放板
    5-31日邮件要求：
        主题：回复: 回复: 奥宝曝光机工程资料！

2019.06.03更新如下：
作者：Chuang.Liu
版本：3.7
1.修改连接ERP地址 172.20.218.253 改为 172.20.218.247 
版本：3.8
1.为解决生产问题，取消获取ERP的数据的(实则程式算法已与锣边后无关，程式里面已改为由成型边往外添加)。

2019.06.03更新如下：
作者：Chuang.Liu
版本：3.9
1.修改各step中填铜当step中还套有其它step时，直接全部填满，改SR_FILL的修改
2.修改touch填充的bug，以保证能够正确的检测到
3.保证用户不作移动时，一直提醒

2019.08.20更新如下：
作者：Chao.Song
版本：4.1
1.增加厂区选择 HDI一厂选项 五厂
2.增加根据厂区选择机台，增加厂区IP的哈希
3.增加LDI Stamp symbol时增加的位置过滤增加不touch panel_symbol_ 的过滤
4.默认窗口大小更改
5.增加从料号中选择，层别的正反面
6.修改函数GET_ATTR_LAYER,增加mbs开始层别的钻带读取，判断层次关系，生成次外层Sec
7.LDI Stamp标记增加时，增加不包含板边铺铜symbol pad panel_symbol_*
8.非内层层别，无需匹配阻焊层
9.修改symbol名书写错误：sh-pindonut

2019.08.20更新如下：
作者：Chuang.Liu
版本：4.2
1.修复当型号中无通孔drl层时，touch失败报错的Bug。Bug型号：525*R29A2 Bug代码段：$c->SEL_REF_FEAT("drl\;${tmpLay}flatten++",

2019.09.06更新如下：
作者：Chuang.Liu
版本：4.3
1.功能适配到Incam下

2019.09.11更新如下：
作者：Chuang.Liu
版本：4.4
1.获取层别镜像参数，适配InCAM

2019.09.11更新如下：
作者：Chuang.Liu
版本：4.5 
测试型号：*486*209*  h52506gic93a2  705*447  898*010
1.修改当外层存在激光孔时，需要采用 inn层的孔；
2.当内层存在机载埋孔时，优先取对应机钻的板角孔；
3.当纯芯板的资料时，系统给出提示，并输出无靶点的资料

2019.09.23更新如下：
作者：Chuang.Liu
版本：4.6 
1.更新HDI输出通孔板外层的对位点（取阻焊层 sh-dwsd2014）
2.修改默认参数由 yes -> no  my $outInn = 'no'; # --初始化外层是否需要使用inn靶孔

2019.09.27更新如下：
作者：Chuang.Liu & Chao.Song
版本：4.7 
1.更新HDI输出通孔板外层的对位点（取输出层别sh-dwtop2013;sh-dwbot2013）；
2.更新HDI输出通孔板内层不添加对位点；

2019.09.28更新如下：
作者：Chao.Song
版本：4.8 
1.更改输出后的层别后的序号，重命名前的匹配语句，增加料号名；放置如l1-fz类层别命名的影响。

2019.10.28更新如下：
作者：Chao.Song
版本：4.9 
1.更改增加symbol由orbldi_stamp更改为hdi_orbldi_stamp_1,增加时间日期;
2.更改添加位置在panel左上方开始，更改为左下方，使用sh-sh symbol位置图形为88888 sh888888;
3.防呆与内层Xray标靶重叠,$c->SEL_REF_FEAT("drl\;${tmpLay}flatten++\;${tmpLay}ref++\",;
4.添加的hdi_orbldi_stamp_1,反面镜像,取消了角度的判断。
5.TODO是否修改参数增加了out_scale属性的图形不拉伸;
6.修改了每层添加均需判断位置;TODO更改位置判断的记录文件为哈希，保存方式为，外层的坐标，次外层的坐标，内层的坐标;
    避免重复touch及外层的添加未考虑内层symbol的影响。
7.TODO对于现场，有两个疑问，一是这个out_scale Symbol是否可用，另一个，现场的内层预涨缩怎么实现？
8.在Linux下直接使用use Win32::API语句报错，使用eval(use Win32::API;);不会报错;
9.写入linux下的IP判断语句ifconfig。

2019.11.21更新如下：
作者：Chao.Song
版本：4.10
1.incam输出前从库内调用最新的symbol hdi_orbldi_stamp_1;

2019.12.04更新如下：
作者：Chao.Song
版本：5.1
1.更改linux下用户目录为环境变量。

作者：Chao.Song
版本：5.2
1.更改内层带拉伸值，未上线，跳过此版本。

2020.03.30
作者：Chao.Song
版本：5.3
1.更改输出路径为临时路径，更名后移至输出目录,避免输出后的文件名的正则匹配失效或可能错乱的情况
Bug料号：ha2308oi042c1 存在L1及L1-gk,导致外层无法重命名。

2020.03.31
作者：Chao.Song
版本：5.4
1.程序无法删除临时文件夹目录时，会报错提示，今日生效Bug料号：515-071A1 L1-2.fz L6-5.fz
	程序预警，结果为复制了tmp目录下的整个文件夹至输出目录。
	修复程序，对带点(.)的层别命名进行去点处理，再进行后续操作。
	
2020.06.04
作者：Chao.Song
版本：5.5
1.更改靶点限制为3个；

2020.08.26
作者：Chao.Song
版本：5.5.1
1.锁定线路层极性均为正极性 === http://192.168.2.120:82/zentao/story-view-1872.html
2.units_factor=0.1 --> 0.01

2020.09.02
作者：Chao.Song
版本：5.5.2
1.增加外层一次铜二次铜的防呆；
2.界面增加辅助菲林选项；

2020.10.09
作者：Chao.Song
版本：5.5.3
1.薛岩弟账号不防呆二次铜流程;


2020.12.15
作者：Chao.Song
版本：5.5.4
1.增加任德强44926账号,周涌44566的输出正片权限;

2021.08.02
作者：Chuang.Liu
版本：5.5.5
1.同一个料号外层，次外层ldi资料输出两种解析资料.一种解析度1.5um，一种解析度2.0um；增加高精度资料输出（http://192.168.2.120:82/zentao/story-view-3313.html）

2021.08.11
作者：Chao.Song
版本：5.5.6
1.修正芯板镭射报镭射命名错误问题

2021.09.03
作者：Chao.Song
版本：5.5.7
1.新板边上线后parm文件更改为json格式,输出时报无法识别面次，更改程序，使用inplan数据解析层别正反。
2021.09.07
2.更改直接使用inplan的结果，不使用文件，避免升级版本造成的料号数据有误。

2021.10.12(上线日期)
作者：Chao.Song
版本：5.5.8
1.增加分割的料号输出支持，检测分割图形中r0(.fiducial_name=300.measure)存在即为分割，对位靶点数量不是4的整数倍的检测，.fiducial_name=300.trmv或.fiducial_name=300.trmh是否存在的检测，
http://192.168.2.120:82/zentao/story-view-3552.html
2.检测stamp是否与其他图形相交;
http://192.168.2.120:82/zentao/story-view-3557.html
3.2022.02.23  975-148A3  六分割

2022.04.22 (开发日期)
作者：Chao.Song
版本：V5.6
1.LDI输出，使用实际板尺寸进行切割。http://192.168.2.120:82/zentao/story-view-4191.html
2.=== V5.6.1 2022.06.01  增加周期是否存在在于输出层别的检测 http://192.168.2.120:82/zentao/story-view-4300.html
3.2022.12.20 		#周涌通知 走正片流程的直接默认 negative 20221220 by lyh
4.2022.12.22 Song 一压特殊叠构料号，内层未能按内层输出。183-741
5.2023.01.03 Song 更新GET_InPlan_Stackup使之仅获取inplan最后一次check in的数据。C1832400737A1;HD3706GI034A1
6.2023.01.04 Song 增加个提醒语句，二次铜的层别设定极性为Negative C1832000741A1
7.2023.01.11 Somg 修正：通过inn来判定层别类型时，超过10层板，会把L10层定义为外层 a77/333e2
