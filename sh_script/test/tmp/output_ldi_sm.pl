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

use lib "$ENV{GENESIS_DIR}/sys/scripts/Package";
use Genesis;
use mainVgt;
use Data::Dumper;
#use getYHdata;
use VGT_Oracle;
use JSON;

my $f = new Genesis();
my $c = new mainVgt();
my $o = new VGT_Oracle();

#my $v = new getYHdata();

my @localIpS = &getCurrentIp;

# --初始化
my $JOB=$ENV{JOB};
my $STEP=$ENV{STEP};
my $VerSion = "版本：V1.4.8";
my $tmpLay = "__outputldi__";

# --程式执行前的检测
unless ($JOB)
{
    &Messages('warning','JOB未打开，程式无法执行！');
    exit(1);
}
# --根据系统定义不同的参数
if ( $^O ne 'linux' ) {
    our $tmp_file = "C:/tmp";    
    our $dirPath = "D:/disk/film";
	our $scriptPath = "$ENV{SCRIPTS_DIR}/sys/scripts";
    our $parm_file = "$ENV{GENESIS_DIR}/fw/jobs/$JOB/user/panel_parameter1";
}else{
    our $tmp_file = "/tmp";    
    our $dirPath = "/id/workfile/hdi_film";
	our $scriptPath = "$ENV{SCRIPTS_DIR}/sys/scripts";
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
    # --连接ERP oracle数据库
    our $dbc_e = $o->CONNECT_ORACLE('host'=>'172.20.218.247', 'sid'=>'topprod1', 'port'=>'1521', 'user_name'=>'zygc', 'passwd'=>'ZYGC@2019');

    if (! $dbc_e)
    {
        $c->Messages('warning', '"ERP数据库"连接失败-> 程序终止!');
        exit(0);
    }
	
}
# --结束启动项
END
{
    # --断开Oracle连接
    $dbc_h->disconnect if ($dbc_h);
	$dbc_m->disconnect if ($dbc_m);
	$dbc_e->disconnect if ($dbc_e);
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

# --配置文件 orbotech_plot_spool.config 中设置的输出路径为 D:\disk\film,如需更改以下目录下的资料，请同时更改配置文件

# --定义输出check button 对应的类型
my %Sel_Check_B=('Sel_1' => 'SMask','Sel_2' => 'GM',);
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



my (%sel_but,%opt_frm_c,%opt_frm_cc,%opt_frm_d,%opt_frm_dd,%opt_frm_e,%sel_mir,%opt_frm_f,%sel_pol,%sel_state);
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
my $led_board = &get_ERP_product3;
my $sel_step='panel';


###获取所有Board层列表 及层所属的类型##
#my ($layer_array,$Layer_Info, $Drill_list)=&GET_ATTR_LAYER; ###返回的为两个指针
my ($layer_array,$Layer_Info)=&GET_ATTR_LAYER; ###返回的为两个指针     return (\@LayerValue,\%Lay_Info,\%Drill_list);
my @layer_array=@$layer_array;
my %Layer_Info=%$Layer_Info;
#my %Drill_list= %$Drill_list;
#my @ref_array = @$ref_array;

my $drc_job = '';
if ( $JOB =~ /(.*)-[a-z].*/ ) {
	$drc_job = uc($1);
} else {
	$drc_job = uc($JOB);
}

my $layer_number = substr($JOB,4,2)*1;

our %lamin_data = $o->getLaminData($dbc_h, $drc_job);
# 压合次数
my $lamination_num = $lamin_data{'yh_num'};
my $rout_x = $lamin_data{$lamination_num}{'pnlroutx'} * 25.4;
my $rout_y = $lamin_data{$lamination_num}{'pnlrouty'} * 25.4;
my $inplan_panel_x = $lamin_data{$lamination_num}{'pnlXInch'} * 25.4;
my $inplan_panel_y = $lamin_data{$lamination_num}{'pnlYInch'} * 25.4;

my $final_cut_x = ($inplan_panel_x - $rout_x) * 0.5;
my $final_cut_y = ($inplan_panel_y - $rout_y) * 0.5;

if ($rout_x == 0 and $rout_y == 0) {
	$final_cut_x = 0;
	$final_cut_y = 0;
	$rout_x = $inplan_panel_x;
	$rout_y = $inplan_panel_y;
}
my $stack_tmp = &GET_InPlan_Stackup;
my %layer_stack = %$stack_tmp;

# --获取所有内层XY系数
my ($scale_x,$scale_y)=&Get_Scale;
my %scale_x=%$scale_x;
my %scale_y=%$scale_y;

# --获取所有层的面向（从跑Panel的文件中获取 $ENV{GENESIS_DIR}/fw/jobs/$job_name/user/panel_parameter1）
#my %lay_Mir = {};#&GET_LAYER_MIR();
my %lay_Mir = &GET_LAYER_MIR();


###界面代码
my $mw = MainWindow -> new(-title => "胜宏奥宝外层线路后LDI资料输出 $VerSion");
$mw -> geometry("520x720+300+100");
$mw -> update;  ###关闭会取消置顶##
# Win32::API -> new("user32","SetWindowPos",[qw(N N N N N N N)],'N')->Call(hex($mw->frame()),-1,0,0,0,0,3);

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
for ("阻焊","干膜") {
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
my $main_frm=$display_frame->Scrolled('Frame', -scrollbars => 'se', -height => '320', -width => '540', -borderwidth => 2, -relief => 'groove') ->pack(-side => 'top');

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

###定义坐标及Hash
###循环所有输出层
for $lay_n (@layer_array)
{
    ###初始值Check Button的值
    $sel_but{$lay_n}=0;
    ###获取层别对应的颜色
    my $layer_color=&SET_LAYER_COLOR($lay_n);
    ###选择Check Button
    ###当临时文件中存在添加条码的层时
    $sel_but{$lay_n}=(exists $Bar_Info{$lay_n}{Tool_Num}) ? 1 : 0;
    $sel_state{$lay_n} = (exists $Bar_Info{$lay_n}{Tool_Num}) ? 'normal' : 'disabled';
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
        $sel_mir{$lay_n}=($lay_Mir{$lay_n} eq 'no') ? 'no' : 'yes';
        $mir_fg{$lay_n}='blue';
    }else{
        # --再次判断是否为辅助菲林（带‘-’的层）
        my $tmpLayN = $lay_n;
		if ($lay_n =~ /(.+)\-(.+)/){
			my @split_words = split '-', $lay_n;  # 以空格分割
			$tmpLayN = $split_words[0];     
		}    

        # --如果分割后能查到结果
        if (exists $lay_Mir{$tmpLayN}) {        
            $sel_mir{$lay_n}=($lay_Mir{$tmpLayN} eq 'no') ? 'no' : (($lay_Mir{$tmpLayN} eq 'yes') ? 'yes': 'Null');
            $mir_fg{$lay_n}=($sel_mir{$lay_n} ne 'Null') ? 'blue' : 'red';
        }else{
            ###当Inplan中无对应信息时默认为空
			# === 2021.10.11 排除 ($Layer_Info{$lay_n}{type} =~ /^(GM)$/) 的情况，如进入此段，则GM应是未获取对应线路层的top bottom 使用值默认为空Null，适用于盖孔层l1-gk,l8-gk类型
            $sel_mir{$lay_n}=($Layer_Info{$lay_n}{type} =~ /^(Outer|Inner|Silk|SMask|GM)$/) ? (($Layer_Info{$lay_n}{layer_side} eq 'top') ? 'no' : (($Layer_Info{$lay_n}{layer_side} eq 'bottom') ? 'yes': 'Null'))  : (($Layer_Info{$lay_n}{type} =~ /^(Silk)$/) ? ($Layer_Info{$lay_n}{layer_side} eq 'top' ? 'no' : 'yes') : 'Null');
			$mir_fg{$lay_n}=($Layer_Info{$lay_n}{type} =~ /^(Outer|Inner|Silk|SMask|GM)$/) ? 'blue' :'red';
        }
    }
    
    $mir_frm=$frm_list->Labelframe()->grid(-row => $num_row+1, -column => 5, -sticky => 'w');
	$mir_frm->gridForget();
    $opt_frm_f{$lay_n}=$mir_frm-> Optionmenu(-options => [qw/no yes Null/],-variable => \$sel_mir{$lay_n},-font =>'微软雅黑 10',-fg=>$mir_fg{$lay_n},-activebackground => 'white', -state => $sel_state{$lay_n})->grid(-row => 0, -column => 0, -sticky => 'w');
      
    ###层别极性
    if (exists $Lay_Mir_Pol{$lay_n}{Lay_Pol}) {
        $sel_pol{$lay_n}=$Lay_Mir_Pol{$lay_n}{Lay_Pol};
        $pol_fg{$lay_n}=($sel_pol{$lay_n} eq 'positive') ? 'blue' : '#CD853F';
    }else{
        #$sel_pol{$lay_n}=($Layer_Info{$lay_n}{type} =~ /^(Outer|Inner)$/) ? 'positive' : (($Layer_Info{$lay_n}{type} =~ /^(Inner)$/) ? 'negative' :'Null'); #$Layer_Info{$lay_n}{layer_polar}
        $sel_pol{$lay_n}=($Layer_Info{$lay_n}{type} =~ /^(Outer|Inner|Sec)$/) ? 'positive' : (($Layer_Info{$lay_n}{type} =~ /^(SMask|GM)$/) ? 'negative' : 'Null');
		# V1.4.8 GM类型，更改为默认negative
        if ($lay_n =~ /l.*-gk-?\d?/) {
			# === V1.4.2 HDI用LDI制作盖孔，定义为负极性，保证输出的LDI正确 ===
			$sel_pol{$lay_n} = 'negative';
		}
		if ($lay_n =~ /etch/) {
			$sel_pol{$lay_n} = 'positive';
		}
		#$sel_pol{$lay_n}='negative';
        # --次外层显示橙色
        $pol_fg{$lay_n}=($Layer_Info{$lay_n}{type} =~ /^(Outer|Inner)$/) ? 'blue' : (($Layer_Info{$lay_n}{type} =~ /^Sec$/) ? '#FFA500' : (($Layer_Info{$lay_n}{type} =~ /^SMask$/) ? '#2E8B57' : 'red'));
    } 
    $pol_frm=$frm_list->Labelframe()->grid(-row => $num_row+1, -column => 6, -sticky => 'w');
	$pol_frm->gridForget();
    $opt_frm_e{$lay_n}=$pol_frm-> Optionmenu(-options => [qw/positive negative Null/],-variable => \$sel_pol{$lay_n},-font =>'微软雅黑 10',-fg=>$pol_fg{$lay_n},-activebackground => 'white', -state => $sel_state{$lay_n})->grid(-row => 0, -column => 0, -sticky => 'w');
    
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
    my @sm_array ;
	my @gm_array; # 外层干膜层
    $f->INFO(entity_type => 'matrix',entity_path => "$JOB/matrix");
    ###遍历所有Info信息
    while ( $i < scalar @{$f->{doinfo}{gROWrow}} ) {
        if ( ${$f->{doinfo}{gROWcontext}}[$i] eq 'board' and ${$f->{doinfo}{gROWlayer_type}}[$i] ne "drill") {
            $Lay_Info{${$f->{doinfo}{gROWname}}[$i]}{type} = 'None';       
            ###防焊的列表
			if  (${$f->{doinfo}{gROWlayer_type}}[$i] eq 'solder_mask' ) {
				$Lay_Info{${$f->{doinfo}{gROWname}}[$i]}{type} = 'SMask';
				push (@sm_array,  $f->{doinfo}{gROWname}[$i]);
			}
			# 选化干膜：gold-c(top)/gold-s(bot),sgt-c(top)/sgt-s(bot)
			# 盖孔层别：外层-gk
			# 蚀刻引线：etch-c（top）/etch-s（bot）
			# if  (${$f->{doinfo}{gROWlayer_type}}[$i] eq 'solder_paste' &&  $f->{doinfo}{gROWname}[$i] =~ /^(gold-(c|s)|sgt-(c|s)|etch-(c|s)|xlym-(c|s)-?\d?|l[0-9][0-9]?-gk-?\d?)$/ ) {
			if  (${$f->{doinfo}{gROWlayer_type}}[$i] eq 'solder_paste' &&  $f->{doinfo}{gROWname}[$i] =~ /^(gold-(c|s)|sgt-(c|s)|etch-(c|s)|xlym-(c|s)-?\d?|l[0-9][0-9]?-gk-?\d?)(-ls\d{6}\.\d{4})?$/ ) {
				$Lay_Info{${$f->{doinfo}{gROWname}}[$i]}{type} = 'GM';
				push (@gm_array,  $f->{doinfo}{gROWname}[$i]);
			}			
            if ($Lay_Info{${$f->{doinfo}{gROWname}}[$i]}{type} ne 'None') {
                ###记录所有层列表
                push @LayerValue,${$f->{doinfo}{gROWname}}[$i];
                ###记录所有层极性
                $Lay_Info{${$f->{doinfo}{gROWname}}[$i]}{layer_polar}=${$f->{doinfo}{gROWpolarity}}[$i];
                ###记录所有层极性基础类型
                $Lay_Info{${$f->{doinfo}{gROWname}}[$i]}{layer_type}=${$f->{doinfo}{gROWlayer_type}}[$i];
                ###记录所有层的方向
                $Lay_Info{${$f->{doinfo}{gROWname}}[$i]}{layer_side}=(${$f->{doinfo}{gROWside}}[$i] ne 'inner') ? ${$f->{doinfo}{gROWside}}[$i] : ${$f->{doinfo}{gROWfoil_side}}[$i];
            }           
        }
        $i++;
    }
    return (\@LayerValue,\%Lay_Info);
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
		   from vgt_hdi.items a
		  inner join vgt_hdi.job b
			 on a.item_id = b.item_id
			and a.last_checked_in_rev = b.revision_id
		  inner join vgt_hdi.items c
			 on a.root_id = c.root_id
		  inner join vgt_hdi.process d
			 on c.item_id = d.item_id
			and c.last_checked_in_rev = d.revision_id
		  inner join vgt_hdi.process_da e
			 on d.item_id = e.item_id
			and d.revision_id = e.revision_id
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
		# 去除数据前后空格
		$get_two_layer =~ s/^\s+|\s+$//g;
		my @twice_top_bot_lay = split(/\//,$get_two_layer);
		my @fz_lay = split(/,/,lc($recs[6]));
		my $current_yhnum = $recs[5] - 1;
		my $flow_content =  $recs[7];
        my $layerMode;
        my $materialType;
        #Final Assembly - 1/12
        #Sub Assembly - 2/11
        #Inner Layers Core - 6/7
        # 20190902添加，此种判断针对标准的hdi结构为OK，
        # 但对于Core+Core结构的未验证，先依据此种方式判断，后续遇到再进行修正
        if ( $stackProcess[0] eq "Final Assembly " ) {
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
									 'flow_content',$flow_content
								);
				if (scalar(@fz_lay) == 1 ) {
				%{$stack_data{$fz_lay[0]}} = ('layerSide','bot',
									'layerMode','FZ',
									 'materialType',$materialType,
									'yh_process',$current_yhnum,
									 'flow_content',$flow_content
								);					
				}
				
			} elsif  ($top_bot_lay[0] eq $get_bot_lay) {
				%{$stack_data{$top_bot_lay[0]}} = ('layerSide','bot',
									'layerMode',$layerMode,
									 'materialType',$materialType,
									'yh_process',$current_yhnum,
									 'flow_content',$flow_content
								);
				if (scalar(@fz_lay) == 1 ) {
				%{$stack_data{$fz_lay[0]}} = ('layerSide','top',
									'layerMode','FZ',
									 'materialType',$materialType,
									'yh_process',$current_yhnum,
									 'flow_content',$flow_content
								);
				}
			}
		} else {
			%{$stack_data{$top_bot_lay[0]}} = ('layerSide','top',
                                            'layerMode',$layerMode,
                                             'materialType',$materialType,
											'yh_process',$current_yhnum,
									 'flow_content',$flow_content
                                        );
			%{$stack_data{$top_bot_lay[1]}} = ('layerSide','bot',
                                            'layerMode',$layerMode,
                                             'materialType',$materialType,
											'yh_process',$current_yhnum,
									 'flow_content',$flow_content
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

sub get_ERP_product3 {
    # 从ERP数据库中查出3张pp相关层别
	my $drc_job = '';
	if ( $JOB =~ /(.*)-[a-z].*/ ) {
		$drc_job = uc($1);
	} else {
		$drc_job = uc($JOB);
	}
    my $job_name_sql = uc($drc_job);
	my $query_sql = "SELECT
		tc_abt03
	FROM
		ima_file a
		JOIN tc_abt_file b ON ta_ima61 = b.tc_abt02 
	WHERE
		ima01 = '$job_name_sql' and
	tc_abt03 like '%LED%' and tc_abt03 not in ('LED-连接板')";
		my $sth_query = $dbc_e->prepare($query_sql);
    $sth_query->execute() or die "无法执行SQL语句:$dbc_e->errstr";
    my @row = $sth_query->fetchrow_array();
	return scalar @row;
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
    #if (-e $parm_file) {
    #   open(STAT, $parm_file) or die "can't open file $parm_file: $!";
    #   my @thick_up = ();
    #   while(<STAT>) {
    #        push(@thick_up, $_);
    #   }
    #   close(STAT);
    #   
    #    foreach $tmp (@thick_up) {
    #        my @array = split(/:/, $tmp);
    #        if ($array[0] =~ /l[0-9][0-9]?/) {
    #            my $tmp_value;
    #            if ($array[2] == 1) {
    #                $tmp_value = "no";
    #            } else {
    #                $tmp_value = "yes";
    #            }
    #            $layMir{$array[0]}=$tmp_value;
    #        }
    #    }
    #    # --返回信息
    #    return %layMir;        
    #}else{
    #    &Messages('warning', "警告：\n\t无法自动获取面向信息，请注意手动选择！");
    #}
	foreach my $tmp (sort keys %layer_stack) {
		if ($tmp =~ /l[0-9][0-9]?/) {
			my $tmp_value;
			if ($layer_stack{$tmp}{'layerSide'} eq 'bot') {
				$tmp_value = 'yes';
			} elsif ($layer_stack{$tmp}{'layerSide'} eq 'top') {
				$tmp_value = 'no';
			} else {
				&Messages('warning', "警告：\n\t层别 $tmp ,请注意手动选择！");
			}
			$layMir{$tmp}=$tmp_value;
		}
	}
	# --返回信息
	return %layMir;    
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
        }elsif($name eq "干膜") {
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
			if ($led_board and $Sel_Check_B{'Sel_'.$n} eq 'SMask') {
				$c->Messages('warning', 'LED板,不输出LDI格式防焊资料,程序退出!');
				$out_type{"Sel_".$n}=0;
				return;
			}
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

		if ($sel_but{$lay_n} == 1 and $Layer_Info{$lay_n}{type} eq "SMask" and $led_board) {
			$sel_but{$lay_n}=0;
			$c->Messages('warning', 'LED板,不输出LDI格式防焊资料!');
			return;
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
sub Output_Set
{    	
    #添加输出前检查阻焊r0是否被移动与sh-dwsd2014对不上，如果是就提示不能允许输出。
    if(length(&check_Align_ro_shdwsd) > 1){
        exit(1);
    }
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
		my $res = &Check_Output_layer;	 #调用检测
		if ($res == 0){
			&getOutputParm;
			destroy $mw;
			&Output_LDI_Main;     
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
            ###X、Y系数的检测
            if ($x_scale_change == 1){
                $Error_Info .= "$lay_n 层X系数: $scale_x{$lay_n} ; " if ($scale_x{$lay_n} !~ /^(-)?\d+(\.\d+)?$/);
            }
            if ($y_scale_change == 1){
                $Error_Info .= "$lay_n 层Y系数: $scale_y{$lay_n} ; " if ($scale_y{$lay_n} !~ /^(-)?\d+(\.\d+)?$/);
            }
            ###镜像及极性的检测
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
            # === 增加盖孔层别的镜像判断及负极性锁定 ===
			if ($lay_n =~ /l(\d+?)-gk-?\d?/) {
				if ($sel_pol{$lay_n} ne 'negative') {
					 $Error_Info .= "层别：$lay_n 极性应为Negative ; ";
				}
				my $cur_lay_num = int($1);
				if ($cur_lay_num == 1 && $sel_mir{$lay_n} ne 'no') {
					$Error_Info .= "层别：$lay_n 镜像应为No ; ";
				}
				my $job_num = substr $JOB,4,2;
				my $bot_gkchk = 'yes';
				if ($job_num !~ /[0-9][0-9]/) {
					$bot_gkchk = 'no';
				}
				if ($cur_lay_num != 1 ){
					if ( $bot_gkchk eq 'no' ) {
						&Messages("warning","由于无法通过料号名判断料号层数:$job_num ,导致层别：$lay_n 无法检查镜像是否正确！");
					} else {
						if ( $cur_lay_num == int($job_num)) {
							if ($sel_mir{$lay_n} ne 'yes') {
								$Error_Info .= "层别：$lay_n 镜像应为Yes ; ";
							}
						} else {
							&Messages("warning","层别：$lay_n ,非外层盖孔设计，请自行检查镜像是否正确!");
						}
					}
				}
			}
			# === V1.4.5 增加镀金，蚀刻引线，选化层别的镜像判断及负极性锁定 ===
			if ($lay_n =~ /(etch)-(c|s)/) {
				my $res = &get_etch_description;
				if($res != 0){
					$Error_Info .= "层别：$lay_n 金手指去导线为碱性蚀刻，禁止输出资料; ";
				}
				
				if ($sel_pol{$lay_n} ne 'positive') {
					 $Error_Info .= "层别：$lay_n 极性应为Positive ; ";
				}
				if ($2 eq 'c' && $sel_mir{$lay_n} ne 'no') {
					$Error_Info .= "层别：$lay_n 镜像应为No ; ";
				}
				if ($2 eq 's' && $sel_mir{$lay_n} ne 'yes') {
					$Error_Info .= "层别：$lay_n 镜像应为Yes ; ";
				}
			}
			
			# === V1.4.8 增加镀金，蚀刻引线，选化层别的镜像判断及负极性锁定 ===
			if ($lay_n =~ /(gold|sgt|xlym)-(c|s)|^xlym-(c|s)-?\d?/) {
				if ($sel_pol{$lay_n} ne 'negative') {
					 $Error_Info .= "层别：$lay_n 极性应为Negative ; ";
				}
				if ($2 eq 'c' && $sel_mir{$lay_n} ne 'no') {
					$Error_Info .= "层别：$lay_n 镜像应为No ; ";
				}
				if ($2 eq 's' && $sel_mir{$lay_n} ne 'yes') {
					$Error_Info .= "层别：$lay_n 镜像应为Yes ; ";
				}
			}
			
			# === 2021.10.12 防焊增加负极性锁定 ===
			if ($Layer_Info{$lay_n}{type} =~ /^(SMask)$/)
			{
				if ($sel_pol{$lay_n} ne 'negative') {
					 $Error_Info .= "层别：$lay_n 极性应为Negative ; ";
				}
			}
			
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
# 函数名: get_etch_description
# 功  能: 函数说明：获取金手指去导线是否为碱性蚀刻
# 参  数: 无
# 返回值: 1或0
#********************************/
sub get_etch_description{
    my $uc_job_name = uc(substr($JOB, 0, 13));
	my $sql = "SELECT
					PROC.MRP_NAME ,
					RJTSL.WORK_CENTER_CODE,					
					RJTSL.DESCRIPTION
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
					AND RJTSL.WORK_CENTER_CODE like '%金手指去导线%'
					AND RJTSL.DESCRIPTION like '%碱性蚀刻%'";

    my $sth = $dbc_h->prepare($sql);
    # 执行SQL操作
    $sth->execute() or die "无法执行SQL语句:$dbc_inplan->errstr";
    my @recs = $sth->fetchrow_array();
	if (@recs){
		return 1;
	}else{
		return 0;	
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
    # system("rm -rf $dirPath/$JOB");
	my @check_date_layer;
	for my $lay (@outLayer){
		# === 仅阻焊检测 
		if ($lay =~ /^m[12]/) {
			push @check_date_layer,$lay;
		}
	}
	
	if (@check_date_layer) {
		my $get_result = system("python $scriptPath/lyh/auto_sh_hdi_check_rules.py check_aobao_danymic_text_info @check_date_layer");
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
    
    # --在返回数据前填充参考层 创建参考层，填充所有Panel中step区模拟安全区，添加Stamp图形时，以防盖到其它图形
    # &CreateAllStep_Surface;
    # --填充所有pnl_rout层及inn层用于添加LDI字样的检测。
    # &CreateAllBar_Surface;
	&add_new_sm_target_symbol(@check_date_layer);
	
	# for my $lay (@outLayer){
		# if ($lay =~ /^m[12]/) {
			# #http://192.168.2.120:82/zentao/story-view-6596.html 20240323 by lyh
			# ##旧防焊对位靶需添加一个s3800 的开窗，新板边已更新
			# &add_new_sm_target_symbol($lay);
		# }		
	# }
	
	
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
				&Messages('warning', "层 $lay 分割设计,图形中属性(.fiducial_name=317.reg)不应存在，请确认资料，程序退出");
				exit(1);
			}
			if ($fg_num % 4 != 0) {
				&Messages('warning', "层 $lay 分割图形中属性(.fiducial_name=300.measure)部件数量不是4的整数倍，请确认资料，程序退出");
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
				&Messages('warning', "层 $lay 分割图形中属性(.fiducial_name=300.trmv或.fiducial_name=300.trmh)不存在，请确认资料，程序退出");
				exit(1);
			}
			my $fg_times = $fg_num / 4;
			# === 二分割应该 分割线或者横线或者竖线
			if ($fg_times == 1) {
				&Messages('warning', "层 $lay 分割光点数量为4，不合理，请确认资料，程序退出");
				exit(1);
			} elsif  ($fg_times == 2) {
				if (($fg_vnum + $fg_hnum) != 1) {
					&Messages('warning', "层 $lay 光点数量为8应为2分割,分割线r0数量不正确,请确认资料，程序退出");
					exit(1);
				}
			} elsif ($fg_times == 3) {
				if ($fg_vnum == 2 || $fg_hnum == 2 ) {
				} else {
					&Messages('warning', "层 $lay 光点数量为12应为3分割,分割线r0数量应横向2或纵向2,\n目前数量不正确,请确认资料，程序退出");
					exit(1);
				}
			} elsif ($fg_times == 4) {
				if ($fg_vnum == 1 && $fg_hnum == 1 ) {
				} else {
					&Messages('warning', "层 $lay 光点数量为16应为4分割,分割线r0数量应横向1+纵向1,\n目前数量不正确,请确认资料，程序退出");
					exit(1);
				}
			} else {
				&Messages('warning', "层 $lay 目前仅支持2分割及4分割,光点数量 $fg_times\n数量不正确,请确认资料，程序退出");
				exit(1);
			}
		} else {
			# --循环四个坐标添加r0对位靶点
			# --判断图形中对位靶点个数,对应r0靶点属性是否存在,若数量不对，程序退出
			# $c->SELECT_TEXT_ATTR('.fiducial_name', '317.reg', 1);
			# $c->FILTER_SELECT();
			# $c->FILTER_RESET();
			# # --当前层无对就r0靶点时，进行添加
			# if ($c->GET_SELECT_COUNT() == 0) {
				# # --从输出层中随便取出一层，取出四个对位点的坐标（用于添加r0定位靶点）
				# my @fourCoor = &Get_BD_Symbol($lay);
				# # --还原工作层
				# $c->CLEAR_LAYER();
				# $c->WORK_LAYER($lay);
				# for (@fourCoor)
				# {
					# next if($_->[0] eq "" or $_->[1] eq "");
					# $c->CUR_ATR_SET('.fiducial_name', '317.reg', 1);
					# $c->ADD_PAD_SINGLE($_->[0], $_->[1], 'r0', 'positive', 'yes');
					# $c->FILTER_RESET();
				# }
			# }
			$c->CLEAR_FEAT();			
			# --添加完成后，继续判断图形中对位靶点个数,对应r0靶点属性是否存在,若数量不对，程序退出
			$c->SELECT_TEXT_ATTR('.fiducial_name', '317.reg', 1);
			$c->FILTER_SELECT();
			$c->FILTER_RESET();
			# === 2020.07.14 更改靶点数量限制为四个
			#if ($c->GET_SELECT_COUNT() !~ /^(3|4)$/) {
			if ($c->GET_SELECT_COUNT() != 4) {
				# &Messages('warning', "层 $lay 图形中r0(.fiducial_name=317.reg)对位靶点数量不对，请检查板边是否有以下Symbol:\n chris-3683symbol\; sh-pindount\; sh-dwtop2013-chris\; sh-dwbot2013-chris\; sh-dwtop2013\; dwbot2013");
				&Messages('warning', "层 $lay 图形中r0(.fiducial_name=317.reg)对位靶点数量不为4个，请修改后进行输出！");				
				exit();
			}
		}
        # --清除选择的物体，以名对后面操作造成影响
        $c->CLEAR_FEAT();	
		# --添加奥宝LDI专用Stamp标记信息（供生产记录：涨缩系数/机器编号/时间/日期/lot号）
		# === 2021.05.25 仅防焊层别添加LDI Stamp，其他层别不添加 
		if ($lay =~ /^m[12]/) {
			#system("python /incam/server/site_data/scripts/sh_script/update_orbldi_stamp/update_orbldi_stamp.py $JOB");
			# &addOrbLdiStamp($lay);
			# 改为检测
			#20250426 翟鸣通知取消检测 工艺发文通知省金取消此开窗
			#&CheckOrbLdiStamp($lay);
			#$c->CLEAR_FEAT();				
		}
    }	
        
    # --循环需要输出的层检测r0靶点添加数量是否正确	
    for my $lay (@outLayer)
    {
        # --清除选择的物体，以名对后面操作造成影响
        $c->CLEAR_FEAT();        
        # --内层芯板跳转
        my @clp_sz_mm = [$final_cut_x,$final_cut_y,$rout_x, $rout_y];
		if ($lay =~ /gk/) {
			@clp_sz_mm = [0,0,$panel_x, $panel_y];
		}
		
        # --判断所选层别面向
        if ($outParm{$lay}{'Mir'} eq 'no') {
            imageSet($lay, 0, 0, 'no_swap');     
        }else{
            imageSet($lay, $panel_cx, 0, 'no_swap'); 
        }
		$c->COM("save_job,job=$JOB,override=no");	
        # --输出opfx格式资料
        &outputOpfx($lay, @clp_sz_mm); 		
    }
    
	
    # --删除垃圾层
    # $c->DELETE_LAYER($_) for ($c->GET_MATCH_LIST($JOB, $tmpLay));
    
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
    #若外层线路存在hdi_orbldi_stamp 优先从线路上直接拷贝过来
	if ($addLay eq "m1"){
		$c->WORK_LAYER("l1");
		$c->FILTER_RESET();
		$c->FILTER_SET_INCLUDE_SYMS("*hdi_orbldi_stamp_1*;*hdi_orbldi_stamp*");
		$c->FILTER_SELECT();
		$c->FILTER_RESET();
		if ($c->GET_SELECT_COUNT() > 0) {
			$c->SEL_COPY("$addLay","yes","0");
			return
		}
	}
	if ($addLay eq "m2"){
		$c->WORK_LAYER("l".$layer_number);
		$c->FILTER_RESET();
		$c->FILTER_SET_INCLUDE_SYMS("*hdi_orbldi_stamp_1*;*hdi_orbldi_stamp*");
		$c->FILTER_SELECT();
		$c->FILTER_RESET();
		if ($c->GET_SELECT_COUNT() > 0) {
			$c->SEL_COPY("$addLay","yes","0");
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
    #my @yhCoor = split(',', &getYHsize()); 删除了getYHsize 函数 
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
    #my $addLdi_y = $Y_srMin - 5;
    my $addLdi_y = $Y_srMin - 5.5;
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
    #my $ckWorkLay = $jobLayInn{$workLay}; # --定义参考层 “GET_LAYER_INN”方法中有初始化
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
		$c->WORK_LAYER ($workLay);
		my $filterSymbol = &seprateBar($workLay);
		# $c->FILTER_SET_INCLUDE_SYMS("r3683\;r3150\;sh-dwsd2014"); # sh-dwsd2014 为HDI最新板边阻焊对位Pad
		# === 2020.07.14 增加镀金干膜类 sh-dwsig2014 ===
		$c->FILTER_SET_INCLUDE_SYMS($filterSymbol); # sh-dwsd2014 为HDI最新板边阻焊对位Pad
		#$c->SEL_REF_FEAT("m1\;m2","disjoint","positive\;negative","pad",,);
		$c->FILTER_SELECT();
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
        @fourCoor = &get4Coor($workLay);
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
    #  Test By Song
	#print "xxxxxxxxfourCoorxxxxxxxxxxxxx\n";
	#print Dumper(\@fourCoor);
	#print "xxxxxxxxfourCoorxxxxxxxxxxxxx\n";

	
    # --返回一个四坐标数组
    return @fourCoor;
}

#旧防焊对位靶需添加一个s3800 的开窗，新板边已更新  ,s3800修改为r2235.2 ,负性套铜s4179修改为s4470.4

sub add_new_sm_target_symbol{ 
	my @change_layers;
	foreach my $workLay (@_){		
		my $bkworkLay = $workLay.'_s2235';
		$c->CLEAR_LAYER();
		$c->WORK_LAYER($workLay);
		$c->FILTER_RESET();
		$c->FILTER_SET_INCLUDE_SYMS("sh-dwsd2014");
		$c->FILTER_SELECT();
		$c->FILTER_RESET();
		if ($c->GET_SELECT_COUNT() > 0) {
			$c->SEL_COPY("${workLay}_tmp_ref++","no","0");
			$c->FILTER_RESET();
			# 如果资料添加的是S4470.4则不做后续检测和修改
			$c->FILTER_SET_INCLUDE_SYMS("s4470.4");
			$c->SEL_REF_FEAT("${workLay}_tmp_ref++", 'touch', 'positive;negative', 'line;pad;arc;text',); 			
			if ($c->GET_SELECT_COUNT() == 0) {						
				$c->COM("copy_layer,source_job=$JOB,source_step=$sel_step,source_layer=$workLay,dest=layer_name,dest_step=,dest_layer=$bkworkLay,mode=replace");	
				$c->CLEAR_LAYER();
				$c->WORK_LAYER($bkworkLay);
				$c->FILTER_RESET();
				$c->FILTER_SET_INCLUDE_SYMS("s3800");
				$c->SEL_REF_FEAT("${workLay}_tmp_ref++", 'touch', 'positive;negative', 'line;pad;arc;text',); 
				$c->FILTER_RESET();
				if ($c->GET_SELECT_COUNT() == 0) {							
					$c->WORK_LAYER("${workLay}_tmp_ref++");			
					# $c->COM("sel_change_sym,symbol=s4179,reset_angle=no");
					$c->COM("sel_change_sym,symbol=s4470.4,reset_angle=no");
					$c->SEL_COPY($bkworkLay,"yes","0");
					# $c->COM("sel_change_sym,symbol=s3800,reset_angle=no");
					$c->COM("sel_change_sym,symbol=r2235.2,reset_angle=no");
					$c->SEL_COPY($bkworkLay,"no","0");					
				}else{
					# 如果已经添加S3800则直接修改
					$c->COM("sel_change_sym,symbol=r2235.2,reset_angle=no");
					$c->CLEAR_LAYER();
					$c->WORK_LAYER($bkworkLay);
					$c->FILTER_RESET();
					$c->FILTER_SET_INCLUDE_SYMS("s4179");
					$c->SEL_REF_FEAT("${workLay}_tmp_ref++", 'touch', 'positive;negative', 'line;pad;arc;text',); 
					$c->FILTER_RESET();
					if ($c->GET_SELECT_COUNT() > 0) {
					$c->COM("sel_change_sym,symbol=s4470.4,reset_angle=no");
					}
				}
				push @change_layers, $workLay;				
			}
			$c->FILTER_RESET();
			$c->DELETE_LAYER("${workLay}_tmp_ref++");			
		}
	}
	$c->COM("save_job,job=$JOB,override=no");	
	if (@change_layers){		
		$c->CLEAR_LAYER();
		$c->FILTER_RESET();
		my $mgs_show = join(';', @change_layers);
		&Messages('warning',"阻焊层: $mgs_show 'sh-dwsd2014'对位点开窗不符合现有规则设计，程序已自动更改至备份层（后缀名_S2235）\n请对比备份层自行检查并更新正式层后重新运行程序 ");
		exit();
	}
}

# --获取四个点的坐标
sub get4Coor
{
	my ($workLay, $get_mode)=@_;
    $get_mode = 'normal'if (not $get_mode);
	# 新增get_mode,用于区分四角取值或长短边
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
	# === 限制对位点为4个 ===
	if (scalar @allCoor == 4)
    #if (scalar @allCoor == 3 or scalar @allCoor == 4)
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
			
	if ($clp_sz_mm[0]->[2] eq '' or $clp_sz_mm[0]->[2] eq '0') {
		&Messages('warning',"抓取不到erp信息，需找mi录入!");
		exit(1);
    }
	
    # --资料输出
    #$f->VOF();
    # scale_mode=nocontrol判定为scale mode 选择为scale features
    # 2019.12.06 更改scale_mode=all为scale_mode=nocontrol，使out_scale的图形不拉伸
	# units_factor=0.1 --> units_factor=0.01
	$f->VOF();	
    #$f->COM("output,job=$JOB,step=$sel_step,format=DP100X,dir_path=$dirPath/$JOB,prefix=,\
    #        suffix=,break_sr=no,break_symbols=no,break_arc=no,scale_mode=nocontrol,surface_mode=contour,units=mm,\
    #        x_anchor=$panel_cx,y_anchor=$panel_cy,x_offset=0,y_offset=0,line_units=mm,override_online=yes,local_copy=yes,send_to_plotter=no,\
    #        dp100x_lamination=0,dp100x_clip=0,clip_size=$clp_sz_mm[0]->[0] $clp_sz_mm[0]->[1],clip_orig=0 0,clip_width=$clp_sz_mm[0]->[0],clip_height=$clp_sz_mm[0]->[1],\
    #        clip_orig_x=0,clip_orig_y=0,plotter_group=any,units_factor=0.01,auto_purge=no,entry_num=5,plot_copies=999,\
    #        dp100x_iserial=1,imgmgr_name=LDI,deliver_date=");
	$f->COM("output,job=$JOB,step=$sel_step,format=DP100X,dir_path=$dirPath/$JOB,prefix=,\
            suffix=_,break_sr=no,break_symbols=no,break_arc=no,scale_mode=nocontrol,surface_mode=contour,units=mm,\
            x_anchor=$panel_cx,y_anchor=$panel_cy,x_offset=0,y_offset=0,line_units=mm,override_online=yes,local_copy=yes,send_to_plotter=no,\
            dp100x_lamination=0,dp100x_clip=0,clip_size=$clp_sz_mm[0]->[2] $clp_sz_mm[0]->[3],clip_orig=$clp_sz_mm[0]->[0] $clp_sz_mm[0]->[1],clip_width=$clp_sz_mm[0]->[2],clip_height=$clp_sz_mm[0]->[3],\
            clip_orig_x=$clp_sz_mm[0]->[0],clip_orig_y=$clp_sz_mm[0]->[1],plotter_group=any,units_factor=0.01,auto_purge=no,entry_num=5,plot_copies=999,\
            dp100x_iserial=1,imgmgr_name=LDI,deliver_date=");	
    my $Status=$f->{STATUS};	
	$f->VON();
	
	
    #$f->VON();
    # --当未能正常输出时，输出报错信息
    if ($Status ne '0') {
		#print("--------------->,$Status");
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
            system("cp $dirPath/$JOB/$JOB\@${out_Lay}_-* $machinePath_vgt5{'Sel_'.$machine_type_radio}[0]/$JOB\@$out_Lay");
            system("cp $dirPath/$JOB/$JOB\@${out_Lay}_-* $machinePath_vgt5{'Sel_'.$machine_type_radio}[1]/$JOB\@$out_Lay");
        }else{
            # --当选择输出本地时，需要重命名
            if ($machine_type_radio != 1) {
                system("cp $dirPath/$JOB/$JOB\@${out_Lay}_-* $machinePath_vgt5{'Sel_'.$machine_type_radio}/$JOB\@$out_Lay");
            }
        }
    } elsif ($factory_type_radio == 2) {
        # HDI 一 厂
        # --当选择输出本地时，需要重命名
        if ($machine_type_radio != 1) {
           system("cp $dirPath/$JOB/$JOB\@${out_Lay}_-* $machinePath_hdi1{'Sel_'.$machine_type_radio}/$JOB\@$out_Lay");
        }
    } 
	
	
    # --重命名本地文件（默认输出的带输出次数）
    #system("mv $dirPath/$JOB/$JOB\@${out_Lay}-* $dirPath/$JOB/$JOB\@$out_Lay"); # 此命令会误认为移动的是目录，而报错
    # print "find $dirPath/$JOB/ -name $JOB\@${out_Lay}-* | xargs -i mv {} $dirPath/$JOB/$JOB\@$out_Lay\n";
    # system ("find $dirPath/$JOB/ -name $JOB\@${out_Lay}-* | xargs -i mv {} $dirPath/$JOB/$JOB\@$out_Lay");
	if ($out_Lay =~ /gk/){
		unlink "$dirPath/$JOB/LDI_2.0Micron/$JOB\@$out_Lay" if (-e "$dirPath/$JOB/LDI_2.0Micron/$JOB\@$out_Lay");
		unlink "$dirPath/$JOB/LDI_1.5Micron/$JOB\@$out_Lay" if (-e "$dirPath/$JOB/LDI_1.5Micron/$JOB\@$out_Lay");
		
		mkdir("$dirPath/$JOB") unless(-d "$dirPath/$JOB"); 
		mkdir("$dirPath/$JOB/LDI_2.0Micron") unless(-d "$dirPath/$JOB/LDI_2.0Micron"); 
		mkdir("$dirPath/$JOB/LDI_1.5Micron") unless(-d "$dirPath/$JOB/LDI_1.5Micron"); 
		
		# 2020.03.31 料号中如果层别带点(.)会影响下方的grep动作
		

		my $grepLay = ${out_Lay};
		$grepLay =~ s/\.//g;
		
		my $renameFile = `ls $dirPath/$JOB | grep ${JOB}\@${grepLay}`;
		print("--------->,$renameFile");
		chomp $renameFile;
		if (-e "$dirPath/$JOB/$renameFile")
		{
			my $File_20Mic = "$dirPath/$JOB/LDI_2.0Micron/$JOB\@$out_Lay";
			my $File_15Mic = "$dirPath/$JOB/LDI_1.5Micron/$JOB\@$out_Lay";
			
			system("cp -rf $dirPath/$JOB/$renameFile $File_20Mic");
			
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
			
			system("rm -rf $dirPath/$JOB/$renameFile");
		}
	}else{
		if (-e "$dirPath/$JOB/$JOB\@$out_Lay")
		{
			unlink "$dirPath/$JOB/$JOB\@$out_Lay";
		}
		
		
		my $grepLay = ${out_Lay};
		$grepLay =~ s/\.//g;		
		my $renameFile = `ls $dirPath/$JOB | grep ${JOB}\@${grepLay}_-`;		
		chomp $renameFile;
		if (-e "$dirPath/$JOB/$renameFile")
		{
			rename ("$dirPath/$JOB/$renameFile","$dirPath/$JOB/$JOB\@$out_Lay");
			#system("mv $dirPath/$JOB/$renameFile $dirPath/$JOB/$JOB\@$out_Lay");
		}
	}
	# === V1.4.8 Song 增加LDI机参数 仅防焊类型的才加参数
	if ($Layer_Info{$out_Lay}{type} eq 'SMask') {
		&add_ldi_sm_parameter("$dirPath/$JOB/$JOB\@$out_Lay");
	}
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

# === 根据层别类型确定选取靶点的symbol
sub seprateBar
{
	my $workLay = shift;
	my $filter_sym = "sh-dwtop2013\;sh-dwbot2013";
	if ($workLay =~ /^(gold|sgt|etch|xlym)-(c|s)$|^xlym-(c|s)-?\d?/) {
		$filter_sym = "sh-dwsig2014";
	}
	if ($Layer_Info{$workLay}{type} eq "SMask") {
		$filter_sym = "sh-dwsd2014";
	}
	return $filter_sym;
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
    $f->COM('get_user_name');
    my $softuser = $f->{COMANS};
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

#检测阻焊r0是否被移动与sh-dwsd2014未对齐
sub check_Align_ro_shdwsd{
    my @check_sm_layers;
    if($sel_step eq "panel"){
        for my $lay_n (@layer_array){
            if ($sel_but{$lay_n} == 1 and $Layer_Info{$lay_n}{type} eq "SMask") {
                push(@check_sm_layers,$lay_n)
            }
        }
    }
    my $error_str = "";
    for my $sm_layer(@check_sm_layers){
        my $feature_file = "$tmp_file/$sm_layer.feature1".int(rand(9999));
        my @feature_list;
        my @mask_r0_array;
        my @mask_dwsd_array;
		$f->COM("affected_layer,mode=all,affected=no");
		$f->COM("clear_layers");
		$f->COM("affected_layer,name=$sm_layer,mode=single,affected=yes");
		$f->COM("filter_reset,filter_name=popup");
		$f->COM("filter_set,filter_name=popup,update_popup=no,polarity=positive");
		$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=pad");
		$f->COM("filter_set,filter_name=popup,update_popup=no,include_syms=r0\;sh-dwsd2014*");
		$f->COM("filter_area_strt");
		$f->COM("filter_area_end,layer=,filter_name=popup,operation=select,area_type=none,inside_area=no,intersect_area=no");		
        $f->COM("info,args=-t layer -e $JOB/$sel_step/$sm_layer -m script -d FEATURES -o select,out_file=$feature_file,write_mode=replace,units=inch");
		$f->COM("filter_reset,filter_name=popup");
		$f->COM("affected_layer,name=$sm_layer,mode=single,affected=no");
        if(-e $feature_file){
            open(MYFL,$feature_file) or die "can't open file $feature_file: $!";
            while(<MYFL>){
                 my @data_array = split(" ",$_);
				 # === 排除分割线属性.fiducial_name=300.trmh .fiducial_name=300.trmv ===
                 if($data_array[0] eq "#P" and $data_array[3] eq "r0" and $data_array[7] !~ /300.trm/){
                    $mask_r0_array[scalar(@mask_r0_array)] = {'x'=>sprintf("%0.3f",$data_array[1]),'y'=>sprintf("%0.3f",$data_array[2])};
                 }elsif($data_array[0] eq "#P" and ($data_array[3] eq "sh-dwsd2014" or $data_array[3] eq "sh-dwsd2014+1")){
                    $mask_dwsd_array[scalar(@mask_dwsd_array)] = {'x'=>sprintf("%0.3f",$data_array[1]),'y'=>sprintf("%0.3f",$data_array[2])};
                 }
                 push(@feature_list,$_);
            }
            close(MYFL);
            unlink($feature_file);
        }
		
        #分析结果
        my $different_num = 0;
        for(my $i=0;$i < scalar(@mask_r0_array);$i++){
            my $find_same = 0;
            my $num = scalar(@mask_r0_array);
            #$f->PAUSE("11111111111111111111  $mask_r0_array[$i]{'x'} --- $mask_r0_array[$i]{'y'}   :$num");
            for(my $n=0;$n < scalar(@mask_dwsd_array);$n++){
                if($mask_r0_array[$i]{"x"} == $mask_dwsd_array[$n]{"x"} and $mask_r0_array[$i]{"y"} == $mask_dwsd_array[$n]{"y"}){
                    $find_same = 1;
                    #$f->PAUSE("eeeeeeeeee");
                }
            }
            if($find_same == 0){
                $different_num++;
            }
        }
        if($different_num){
            $error_str = $error_str."$sm_layer 中大小为r0的PAD和symbol名为sh-dwsd2014或sh-dwsd2014+1的标靶坐标不在同一位置，请检查symbol名称和数量！\n";
        }
    }
    if(length($error_str) > 1){
        &Messages("error",$error_str);
    }
    return $error_str;
}

sub add_ldi_sm_parameter{
	#my $src_file = 'D:\disk\film\s94008pb504e1-song\s94008pb504e1-song@m1';
	my $src_file = shift;
	my $des_file = $src_file . '_new';
	if (-e $des_file) {
		unlink($des_file);
	}
	
	#my $filename=$ARGV[0];
	open FILE1,"<$src_file" or die "Can't open '$src_file':$!";
	open FILE2,">$des_file" or die "Can't open '$des_file':$!";
	#my $lines = join '',<FILE1>;
	
	while (<FILE1>) {
		#print $_ ."\n";
		if ($_ =~ /^(LINES_NUM\s*=\s*)(\d+)/) {
			print $1 . "\n";
			print $2 . "\n";
			my $line_num = $2 + 1;
			print FILE2 $1 .  $line_num  . "\n";
		} elsif ($_ =~ /^(PRIORITY\s*=\s*)(\d+)/) {
			print FILE2 $_ ;
			print FILE2 'COMPENSATION_CODE = HDI'  . "\n";
		} else {
			print  FILE2 $_ ;
		}
	}
	close FILE1;
	close FILE2;
	
	open FILE1,"<$src_file" or die "Can't open '$src_file':$!";
	open FILE2,"<$des_file" or die "Can't open '$des_file':$!";
	my @lines = <FILE1>;
	my $line_num_src = scalar(@lines);
	my @lines1 = <FILE2>;
	my $line_num_des =  scalar(@lines1);
	close FILE1;
	close FILE2;
	if ($line_num_des == ($line_num_src + 1)) {
		unlink($src_file);
		system("mv $des_file $src_file");
	} else {
		print 'error' . "\n";
	}
}

__DATA__
五厂奥宝LDI资料输出程序更新位置:
\\172.20.47.216\d$  (如无法访问使用机器本地管理员帐号：172.20.47.216\orbldi 密码：orbldi)

__END__
2020.07.10
旧有版本从线路LDI输出复制
版本：1.2
1.增加以下层别输出
# 选化干膜：gold-c(top)/gold-s(bot),sgt-c(top)/sgt-s(bot)
# 盖孔层别：外层-gk
# 蚀刻引线：etch-c（top）/etch-s（bot）


2020.07.15
作者：宋超
版本：1.3
1.更改以下层别输出选取的靶位图形:增加函数seprateBar
# 选化干膜：gold-c(top)/gold-s(bot),sgt-c(top)/sgt-s(bot) 蚀刻引线：etch-c（top）/etch-s（bot）对位靶点为短边防焊对位pad sh-dwsig2014
2.限制靶点选取输出数量为4个


2021.05.19
作者：柳闯
版本：1.4
1、类似l1-gk l6-gk层面向默认错误（参考对应外层进行匹配）

2021.05.25
作者：宋超
版本：1.4.1
1.仅防焊层别添加LDI Stamp。其他层别不添加。(不需要添加)

2021.05.26
作者：宋超
版本：1.4.2
1.盖孔层别输出LDI默认负极性

2021.07.02
作者：唐成
版本：1.4.3
1.添加输出前检查阻焊r0是否被移动与sh-dwsd2014对不上，如果是就提示不能允许输出。
Note by Song --> http://192.168.2.120:82/zentao/story-view-3190.html

2021.10.12
作者：宋超
版本：1.4.4
1.盖孔层别优化，层别镜像及极性获取及锁定;http://192.168.2.120:82/zentao/story-view-3550.html;
2.自动判断是否分割;http://192.168.2.120:82/zentao/story-view-3552.html
(增加分割的料号输出支持，检测分割图形中r0(.fiducial_name=300.measure)存在即为分割，对位靶点数量不是4的整数倍的检测，.fiducial_name=300.trmv或.fiducial_name=300.trmh是否存在的检测，)
3.stamp交叉判断;http://192.168.2.120:82/zentao/story-view-3557.html
4.10-20 变更光点数量的提醒，避免误导用户。

2021.12.09
作者：宋超
版本：1.4.5
1.镀金(gold-c/gold-s)、选化(sgt-c/sgt-s)、蚀刻引线(etch-c\etch-s)层别镜像栏默认c面ON，S面yes，如修改成其它提示不能修改，极性栏默认positive，如修改成其它提示不能修改。
http://192.168.2.120:82/zentao/story-view-3707.html
http://192.168.2.120:82/zentao/story-view-3708.html
http://192.168.2.120:82/zentao/story-view-3715.html


2022.08.16
作者：宋超
版本：1.4.6
1.增加l6-gk1类层别的输出支持.
http://192.168.2.120:82/zentao/story-view-4530.html

2022.08.30
作者：宋超
版本：1.4.7
1.输出线路油墨层xlym-c,xlym-s层,和镀金干膜极性一致。
来源:http://192.168.2.120:82/zentao/story-view-4577.html

2022.09.21 上线日期：2022.10.12 
作者：宋超
版本：1.4.8
1.LED板不可输出防焊LDI|EDI；
2.防焊LDI输出增加参数行。
http://192.168.2.120:82/zentao/story-view-4657.html
3.干膜(GM)类型，输出极性为负极性
http://192.168.2.120:82/zentao/story-view-4653.html
4.输出LDI使用板尺寸，非开料尺寸
http://192.168.2.120:82/zentao/story-view-4664.html

2023.01.31 by lyh
增加识别xlym-c-2，xlym-c-1及xlym-c-n类似的命名方式。
http://192.168.2.120:82/zentao/story-view-5081.html


