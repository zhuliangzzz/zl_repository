#!/usr/bin/perl
#/************************************
#
# 程序名称: output_pnlrout_data.pl
# 功能描述: 输出裁磨数据
# 开发小组: Vgt.pcb 系统开发部-程序课
#     作者: Chao.Song
# 开发日期: 2019.09.10
#   版本号: 3.5
# --更新备注见代码最后
#***********************************/
=head 程序使用条款
    -> 本程序主要服务于胜宏科技(惠州)，任何其他团体或个人如需使用，必须经胜宏科技(惠州)相关负责人及
       作者的批准，并遵守以下约定；
    1> 本着尊重创作者的劳动成果，任何团体或个人在使用此程序的时候，均需要知会此程序的原始创作者；
    2> 在任何场合宣导、宣传，在任何文件、报告、邮件中提及本程序的全部或部分功能，均需要声明此程序的
       原始创作者；
    3> 在任何时候对本程序做部分修改或者是升级时，必须要保留文件的原始信息，包括原始文件名、创作者及
       联系方式、创作日期等信息，且不得删除程序中的源代码，只能进行注释处理；
=cut
# --加载系统pm

use DBI;
use POSIX qw(strftime);

# --加载自定义公用pm
use lib "$ENV{GENESIS_DIR}/sys/scripts/Package";
use Genesis;
use mainVgt;
use VGT_Oracle;
use List::Util qw/max min/;
use Encode;
use utf8;
use Data::Dumper;
use Tk;
binmode (STDIN,':encoding(utf8)');
binmode (STDOUT,':encoding(utf8)');
binmode (STDERR,':encoding(utf8)');

# --开始启动项
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
    
    our $dbc_m = $o->CONNECT_MYSQL('host'=>'192.168.2.19', 'dbname'=>'engineering', 'port'=>'3306', 'user_name'=>'root', 'passwd'=>'k06931!');
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

# --程序版本
my $appVersion = '版本：Ver 3.6';

# --初始化料号及变量
my $job_name = $ENV{JOB};
my $step = $ENV{STEP};
$f->COM('get_user_name');
our $softuser = $f->{COMANS};

# --根据系统定义不同的参数
if ( $^O ne 'linux' ) {
    our $scriptPath = "$ENV{SCRIPTS_DIR}/sys/scripts";
    our $jobsPath = "$ENV{GENESIS_DIR}/fw/jobs";
    our $userDir = "$ENV{GENESIS_DIR}/fw/jobs/$job_name/user";
    our $tmpPath = "C:/tmp";
    our $perlVer = "Z:/incam/Path/Perl/bin/perl.exe";
    our $pythonVer = "Z:/incam/Path/Python26/python.exe";
    our $outputPath = "D:/disk/film/$job_name/Pnl_Rout/$job_name";
} else {
    our $scriptPath = "$ENV{SCRIPTS_DIR}/sys/scripts";
    our $jobsPath = "/incam/incam_db1/jobs";
    our $userDir = "$ENV{JOB_USER_DIR}";
    our $tmpPath = "/tmp";
    our $perlVer = "/opt/ActivePerl-5.14/bin/perl";
    our $outputPath = "/id/workfile/hdi_film/$job_name/Pnl_Rout/$job_name";
}

# --判断型号是否打开
unless($job_name){
    $f->PAUSE("The script must be run in a Job!!");
    exit(0);
}

# HDI一厂Inplan 
my $drc_job;

if ( $job_name =~ /(.*)-[a-z].*/ ) {
    $drc_job = uc($1);
} else {
    $drc_job = uc($job_name);
}

# 从Inplan数据库中获取压合叠构
#our %lamin_data = $o->getLaminData($dbc_h, $drc_job);
our %lamin_data = $o->getLaminData_new($dbc_h, $drc_job,$dbc_m);
print Dumper(\%lamin_data);
# 判断是否从InPlan无法获取数据，如果无数据，程序退出。
if (! %lamin_data ) {
    $c->Messages("info","无法从HDI InPlan数据库获取料号:$drc_job 信息，无法输出裁磨数据，程序退出");
    exit 0;
}

our @pnlRoutInfo = &getInplanPnlRout($dbc_h, $drc_job);
our %bar_note_info = &get_bar_note($dbc_h, $drc_job);
print Dumper(\%bar_note_info);

#print @pnlRoutInfo;
#print "\n";

#翟鸣通知 跟现在的规范已经不适应了 取消此项检测 20230629 by lyh
#my $check_led = &judge_led_board($dbc_h, $drc_job);

# === 2021.08.11 === V3.1增加判断，是否为 板边尺寸Y小于24.5 且4靶在长边 ===
# my $op_yn = &check_no_output();
# if ($op_yn eq False && $check_led == 0) {
	##$c->Messages("info","非LED且拼版Y小于24.5inch，T靶在长边，无法输出裁磨数据，程序退出");
	# my $warn_word = "非LED且拼版Y小于24.5inch,T靶在长边,无法输出裁磨数据,请CAM主管审核";
    #3exit 0;
	# my $a = system("python $scriptPath/sh_script/auto_output_pnlrout/auto_pnl_rout_submit.py  $job_name $warn_word ");
	# if ($a != 0) {
		# exit 0;
	# }
# }

# 定义初始变量
&pre_define_data;
&get_pnl_rout_data;
sub pre_define_data
{
	our $panel = 'panel';
    # 获取panel尺寸
    $f->INFO(units => 'mm', entity_type => 'step', entity_path => "$job_name/panel", data_type => 'PROF_LIMITS');
    our $xmin = $f->{doinfo}{gPROF_LIMITSxmin};
    our $xmax = $f->{doinfo}{gPROF_LIMITSxmax};
    our $ymin = $f->{doinfo}{gPROF_LIMITSymin};
    our $ymax = $f->{doinfo}{gPROF_LIMITSymax};
    our $xcenter = sprintf "%0.8f", ($xmax - $xmin) * 0.5;
    our $ycenter = sprintf "%0.8f", ($ymax - $ymin) * 0.5;

	our @drill_array = ();
	our @blind_burry_list = ();
	our @jx_drill_list = ();
	our	@all_signal_array = ();
	$f->DO_INFO("-t MATRIX -d ROW -e $job_name/matrix");

	for(my $i=0 ; $i < @{$f->{doinfo}{gROWname}} ; $i++){
		$info_ref = { name       => @{$f->{doinfo}{gROWname}}[$i],
					  layer_type => @{$f->{doinfo}{gROWlayer_type}}[$i],
					  context    => @{$f->{doinfo}{gROWcontext}}[$i],
					  polarity   => @{$f->{doinfo}{gROWpolarity}}[$i],
					  side       => @{$f->{doinfo}{gROWside}}[$i],
					};
		# --获取信号层
		if ( $info_ref->{context} eq "board" && $info_ref->{layer_type} eq "signal" ){
			push(@all_signal_array,$info_ref->{name});
		}
		# --获取钻孔层
		if ( $info_ref->{context} eq "board" && $info_ref->{layer_type} eq "drill" ){
			push(@drill_array,$info_ref->{name});
			# --匹配镭射钻孔层
			if ($info_ref->{name} =~ /^[bs][0-9][0-9]?-?[0-9][0-9]?/ ) {
				push(@blind_burry_list,$info_ref->{name});
			}
			# --匹配机械钻孔层
			if ($info_ref->{name} =~ /^m[0-9][0-9]?-?[0-9][0-9]?$/ ) {
				push(@jx_drill_list,$info_ref->{name});
			}
		}
	}
	our $job_signal_nubers = scalar(@all_signal_array);
	my $job_name_sigmal_num = int(substr($job_name, 4, 2));
	if ($job_signal_nubers != $job_name_sigmal_num) {
		# === 2020.08.24 去掉退出防呆，增加输出提示 ===
		$c->Messages('info',"料号名的层数与线路层的层数不符！使用层数$job_signal_nubers" );
		#exit 0 ;
	}
	
	our $halfjob_numb = $job_signal_nubers / 2;
	# TODO 盲埋孔层别归类，归到某一压合级别中
	# TODO 检测确认盲埋孔层别命名是否正确
	our $hdi_num = scalar(@blind_burry_list);
	our @blind_list;
    our @burry_list;

    foreach my $tmp (@blind_burry_list) {
        if ($tmp =~ /^s([0-9][0-9]?)-([0-9][0-9]?)$/) {
            push (@blind_list, $tmp);
			if (($1 < $2 and $1 <= $halfjob_numb) || ($1 > $2 and $2 >= $halfjob_numb)) {
				if ($1 < $2 and $1 <= $halfjob_numb) {

				} elsif ( $1 > $2 and $2 >= $halfjob_numb ) {
					if ($1 > $job_signal_nubers) {
						$c->Messages("info","$rlayers[$i] 镭射层钻带的起始层超出层别数量,\n请检查，程序退出！");
						exit 0;
					}
				} 
			} else {
				$c->Messages("info","$rlayers[$i] 镭射层钻带的起始层定义不正确,\n程序退出！");
				exit 0;
			}
        } elsif  ($tmp =~ /^b([0-9][0-9]?)-([0-9][0-9]?)$/) {
            push (@burry_list, $tmp);
        } else {
			$c->Messages("info","$tmp 层别非最新命名，\n应为s/b开始层-结束层，中间有横杠,\n程序退出！");
			exit 0;
		}
    }
	our $job_rj = 'no';
	$c->OPEN_STEP($job_name,$panel);
	$c->CLEAR_LAYER;
	$c->FILTER_RESET;
	$f->COM('affected_filter,filter=(type=signal|power_ground|mixed&context=board)');
	$c->FILTER_SET_FEAT_TYPES('pad');
	$c->FILTER_SET_INCLUDE_SYMS('chris-rjpad');
	$c->FILTER_SELECT;
	if ($c->GET_SELECT_COUNT > 0) {
		$job_rj = 'yes';
	}
	$c->CLEAR_LAYER;
}

sub get_pnl_rout_data
{
	# print Dumper(\%lamin_data);
    # CAM资料中的数据
    our %yh_data;
    # MI数据中的压合次数
    my $yh_num = $lamin_data{'yh_num'};
    $c->OPEN_STEP($job_name,$panel);
	# 图形均设计7靶位，
	# HDI通盲并存板序打7靶，钻孔使用3靶定位，图形使用4靶定位；
	# 通孔板/HDI板仅有埋孔板序，裁磨打4靶，图形使用板角四孔对位。
	# 判断条件确定规则，
	# 纯通孔板，inn层设计3孔的，按旧有规则输出； --> op_mode = 3bar --> 不支持此种输出
	# 纯通孔板，inn层设计4孔的，新。			 --> op_mode = 4bar
	# HDI板，每次压合判断当前板序是否有盲孔层及埋孔层同时存在； --> op_mode = 7bar   检测 inn层应该3孔设计
	# HDI板，除以上情况											--> op_mode = 4bar
    # 循环压合次数，获取起始层别，对应相应inn
	# === 2021.01.25
	# === 八靶规则，非溶胶板，非五代靶烧靶料号'V5laser'，8 bar，其他沿用以上
	# === 熔胶区判断以板内是否有熔胶块为准；
	# === 五代靶取inplan数据 ===
	# === 2021.07.31
	# === 常规使用备用靶输出裁磨数据 ===
	# === 2022.07.21 当前次压合板厚<0.2mm 或者 >2.8mm 打七靶用于中锣
	
    for(my $i=1 ;$i <= $yh_num; $i++) {
        # 增加输出模式定义
        # my $op_mode = "4bar";
		#my $short_8 = 'no';
		my $op_mode;
        my $from_lyr = substr($lamin_data{$i}{'fromLay'},1);
        my $to_lyr = substr($lamin_data{$i}{'toLay'},1);
		my $inn_layer =  ($i == $yh_num )? 'inn':'inn'.$from_lyr.$to_lyr;
		
		# === 2020.07.08 增加判断，是否有盲埋孔在当前的压合级别中
		if (grep /^b${from_lyr}-${to_lyr}$/, @burry_list) {
			if (grep /^b${from_lyr}-${to_lyr}$/, @burry_list) {
				$lamin_data{$i}{'burryLayer'} = "b${from_lyr}-${to_lyr}";
			} 
		}
		# === 2020.06.22 一压增加判断top面及Bot面镭射是否存在
		if (grep /^s${from_lyr}|${to_lyr}-/, @blind_list) {
			$lamin_data{$i}{'blindLayer'} = grep /^s${from_lyr}|${to_lyr}-/,@blind_list;
		} 
				
		# === 多次压合的外层, 取消这个判断，按MI为准 20231227 ynh
		# if ($job_rj eq 'no' && $lamin_data{$i}{'V5laser'} == 0 && ((defined $lamin_data{$i}{'burryLayer'} && defined $lamin_data{$i}{'blindLayer'}) || ($yh_num >= 1 && $i == $yh_num && defined $lamin_data{$i}{'blindLayer'} ) )) {
			# $op_mode = "8bar";
		# }
		
		
		# === 增加最后一次压合短短边8靶的设定 ===取消这个判断，按MI为准 20231227 ynh
		# if ($i == $yh_num && defined $lamin_data{$i}{'sig4y1'}  && $lamin_data{$i}{'sig4y1'} > 0   ) {
			# # === V3.4 2022.03.02 分割内层靶一般是11以及22标识，如果是是最外层是T靶，则不会输出数据，暂时不增加其他判断
			# $op_mode = '8bar';
			# #$short_8 = 'yes';
		# }			
		
		#exit 0;
		# === 定义获取靶孔的参考层，使用中间层，获取靶孔位置		
		my $get_bar_lyr_num = $from_lyr + 1;
		if ($get_bar_lyr_num >= $to_lyr) {
			$c->Messages("info","压合级别 ${i} 无法获取${from_lyr} ${to_lyr} 中间层,不支持此类型裁磨输出，程序退出");
			exit 0;
		}
		my $get_bar_lyr = 'l' . $get_bar_lyr_num;
		
		# 匹配INPLAN备注中的打靶信息 ,未匹配到则定义为no ynh -20231227
		if(exists $bar_note_info{$get_bar_lyr}){
			$op_mode = $bar_note_info{$get_bar_lyr};			
			}else{
				# &get_select_mode($get_bar_lyr);
				my $ans = $c->Messages_Sel('question', ${i}.'次压合无法从INPLAN中获取'.${from_lyr}.'-'.${to_lyr}.'打几孔,继续运行将按资料实际设计靶孔数量输出，否则请退出和MI确认');
				if ($ans eq "Cancel"){
					exit;
				}
				else{
					$op_mode = "no";		
				}	
				# $c->Messages("info","${i}次压合无法从INPLAN中获取${from_lyr}-${to_lyr} 打几孔，程序将按资料实际设计靶孔数量输出！");
			}
			
		# === 2020.07.07更新，通孔板使用4靶做钻孔定位，增加输出模式 4bar
		if ($hdi_num < 1) {
			$op_mode = "4bar";
		}
		
		## === 2022.07.21
		my $change_mode = 'no';
		my $yh_thick = $lamin_data{$i}{'yhThick'};
		if ( $yh_thick <= 0.2 or $yh_thick >= 2.8) {
			#$op_mode = '7bar';
			$change_mode = 'yes';
		}
		
		# === 2022.08.22
		if (defined @pnlRoutInfo) {
			for(my $b=0;$b<=$#pnlRoutInfo;$b++) {
				if ($pnlRoutInfo[$b][1] eq $lamin_data{$i}{'mrpName'}) {
					$op_mode = '7bar';
					if ($change_mode ne 'yes') {
						$c->Messages("info","检测到 $lamin_data{$i}{'mrpName'} 板厚 $yh_thick 未超裁磨制程能力,\n但存在铣边框站,需使用7靶输出,仍继续输出 \n Tips:如果是化金前铣边框,站名应为HDI243");
					}
				}
			}
		}
		if ($change_mode eq 'yes' and $op_mode ne '7bar') {
			$c->Messages("info","检测到板厚:$yh_thick 超裁磨制程能力,但输出模式不是7靶,仍继续输出");
		}
			
		my $pnl_rout_lyr = 'pnl_rout';
		if ($hdi_num >= 1) {
			$pnl_rout_lyr = 'pnl_rout' . $i;
		}
		
        if ($c->LAYER_EXISTS($job_name, $panel, $pnl_rout_lyr) eq "no") {
           #增加判断$inn_layer是否存在 2019.10.08
            $c->Messages("info","料号:$job_name 中缺少$pnl_rout_lyr 层设计，无法输出裁磨数据，程序退出");
            exit 0;
       }       
		# 检测选中层别中的靶标数量是否正确=============================
		$c->CLEAR_LAYER();
		$c->AFFECTED_LAYER($get_bar_lyr,'yes');		
		$c->FILTER_RESET();
		$f->COM('filter_atr_reset');
		my $select_allbar = ($i == $yh_num )? "hdi1-bat\;hdi1-bajt\;hdi1-bst": "hdi1-ba"."$i" ."\;hdi1-baj" . "$i". "\;hdi1-bs" . "$i";
		$c->FILTER_SET_INCLUDE_SYMS($select_allbar);
		$c->SEL_REF_FEAT($pnl_rout_lyr,'disjoint','positive','pad');
		# $c->FILTER_SELECT;
		my $select_count = $c->GET_SELECT_COUNT();	
		# $f->PAUSE($op_mode);
		# if ($select_count != 8 && $select_count != 4){						
			# $c->Messages("info","检测到: $get_bar_lyr 层靶标数量为:$select_count，数量不对,程序退出");
			# exit 0;		
		# }		
		if ($op_mode eq '8bar' &&  $select_count != 8) {			
			$c->Messages("info","检测到：$get_bar_lyr 层inplan流程为打8孔,实际靶标数量为:$select_count，数量不对，程序退出");
			exit 0;			
		}elsif($op_mode eq '4bar' &&  $select_count != 4){			
			# $c->Messages("info","检测到：$get_bar_lyr 层inplan流程为打4孔,实际靶标数量为:$select_count，数量不对，程序退出");
			$c->Messages("info","检测到：$get_bar_lyr 层inplan流程为打4孔,实际靶标数量为:$select_count，程序将按4bar输出！");
			# exit 0;		
		}elsif($op_mode eq 'no'){
			if ($select_count == 4){
				$op_mode = '4bar';
			}elsif($select_count == 8){
				 # 此处弹出窗口选择 8靶还是4靶
				 $op_mode = &get_select_from_win($get_bar_lyr);				 
			}			
		}		
		
		#======================================
		$c->CLEAR_LAYER();
		$c->AFFECTED_LAYER($get_bar_lyr,'yes');
		$c->FILTER_RESET();
		$f->COM('filter_atr_reset');
		my $select_bar = ($i == $yh_num )? "hdi1-bat\;hdi1-bajt":"hdi1-ba" . "$i" ."\;hdi1-baj" . "$i";
		$c->FILTER_SET_INCLUDE_SYMS($select_bar);
		if ($op_mode eq '7bar' || $op_mode eq '8bar' ) {
			 $c->SEL_REF_FEAT($pnl_rout_lyr,'disjoint','positive','pad');
		} elsif ($op_mode eq '4bar') {
			 $c->SEL_REF_FEAT($inn_layer,'touch','positive','pad');		}
	   
	   # === 2021.01.08 增加不选择带有指定属性的pad ===
	   
		#$f->COM('filter_atr_logic,filter_name=popup,logic=or');
		$c->SELECT_TEXT_ATTR('.string','back_up');
		$c->SELECT_TEXT_ATTR('.string','sig_use');
		$f->COM('filter_atr_logic,filter_name=popup,logic=or');

		$c->FILTER_SELECT('unselect');
		if ($c->GET_SELECT_COUNT() == 0) {
		    $c->Messages("info","料号:$job_name $select_bar 层靶孔选择不正确，程序退出");
            exit 0;	
		}
		$f->COM('filter_atr_reset');

		# 取层的五孔或四孔的关系，左上，右上，右下, 左下。
		my $csh_file  = "$tmpPath/info_csh.$$";
		$f->COM("info, out_file=$csh_file, units=mm,args= -t layer -e $job_name/$panel/$get_bar_lyr -m display -d FEATURES -o select");
		my @getInnData = $c->dealwithFeatureFile($csh_file);
		unlink ($csh_file);

        my $org_inn_num = scalar(@getInnData);

        # 存储四靶靶孔数据
        my %inn_data;
        my $inn_num = scalar(@getInnData);
        # 取消5靶孔判断 2019.11.21 Song
        if ($inn_num == 4 ) {            
            # --- # 左上 1 # 右上 2 # 右下 3 # 左下 4 # --- #  左上开始 顺时针取坐标
            my $getInn = &getFourCor(@getInnData);
            if ($getInn eq 'notpad') {
                #code
                $c->Messages("info","${inn_layer}层添加的标靶为非pad\n，程序退出");
                exit 0;
            } elsif ($getInn eq 'splitError') {
                $c->Messages("info","${inn_layer}层添加的标靶坐标归类错误\n，程序退出");
                exit 0;
            } else {
                %inn_data = %$getInn;
            }
        } else {
			#支持inn层有3靶数据
			#$c->Messages("info","通孔板 inn层 靶孔数量为4，程序退出");
			$c->Messages("info","压合级别:${i} 靶孔数量应为4，目前为：$inn_num ,程序退出");

			#压合级别 ${i}
			exit 0;
        }
		
		# === 2020.01.25 选择线路标靶 ===
		my %sig_bar_data ;
		if ($op_mode eq '8bar') {
			$c->CLEAR_LAYER();

			$c->AFFECTED_LAYER($get_bar_lyr,'yes');
			$c->FILTER_RESET();
			$f->COM('filter_atr_reset');

			my $select_bar = ($i == $yh_num )? "hdi1-bst":"hdi1-bs" . "$i";

			$c->FILTER_SET_INCLUDE_SYMS($select_bar);
			$c->FILTER_SELECT;
			# === Song 2021.02.24 增加短边靶位设计的规则（旧有规则） ===
			if ($c->GET_SELECT_COUNT() == 0) {
				$op_mode = '4bar';
				if ($lamin_data{$i}{'bar4y1'} != $lamin_data{$i}{'bar3y'}) {
					$c->Messages("info","料号:$job_name $select_bar 层线路对位靶孔选择为0，长边靶位，理论应设计8靶，按4靶输出");
				} else {
					$c->Messages("info","料号:$job_name $select_bar 层线路对位靶孔选择为0，是否为2021-02-22前旧靶位设计规则，按4靶输出");
				}
			}
			elsif ($c->GET_SELECT_COUNT() != 4) {
				$c->Messages("info","料号:$job_name $select_bar 层线路对位靶孔选择不为4个，程序退出");
				exit 0;	
			}
			$f->COM('filter_atr_reset');
			if ($op_mode eq '8bar') {
				# 取层四孔的关系，左上，右上，右下, 左下。
				my $csh_file  = "$tmpPath/info_csh.$$";
				$f->COM("info, out_file=$csh_file, units=mm,args= -t layer -e $job_name/$panel/$get_bar_lyr -m display -d FEATURES -o select");
				my @getTmpData = $c->dealwithFeatureFile($csh_file);
				unlink ($csh_file);
		
				my $tmp_num = scalar(@getTmpData);
	
				# 存储四靶线路靶靶孔数据
				if ($tmp_num == 4 ) {            
					# --- # 左上 1 # 右上 2 # 右下 3 # 左下 4 # --- #  左上开始 顺时针取坐标
					my $getTmp = &getFourCor(@getTmpData);
					if ($getTmp eq 'notpad') {
						#code
						$c->Messages("info","${get_bar_lyr}层添加的标靶${select_bar} 为非pad\n，程序退出");
						exit 0;
					} elsif ($getTmp eq 'splitError') {
						$c->Messages("info","${get_bar_lyr}层添加的标靶${select_bar} 坐标归类错误\n，程序退出");
						exit 0;
					} else {
						%sig_bar_data = %$getTmp;
					}
				} else {
					$c->Messages("info","压合级别:${i} 线路靶孔数量应为4，目前为：$tmp_num ,程序退出");
					exit 0;
				}
			}
		}
		
		# === 再次判断，反选另外的靶标
		$select_bar = ($i == $yh_num )? "hdi1-bat\;hdi1-bajt":"hdi1-ba" . "$i" ."\;hdi1-baj" . "$i";
		$c->CLEAR_LAYER();
		$c->AFFECTED_LAYER($get_bar_lyr,'yes');
		$c->FILTER_RESET();
		$c->FILTER_SET_INCLUDE_SYMS($select_bar);
		if ($op_mode eq '7bar' || $op_mode eq '8bar' ) {
			 $c->SEL_REF_FEAT($pnl_rout_lyr,'touch','positive','pad');
		} elsif ($op_mode eq '4bar') {
			 $c->SEL_REF_FEAT($inn_layer,'disjoint','positive','pad');
		}
		$f->COM("info, out_file=$csh_file, units=mm,args= -t layer -e $job_name/$panel/$get_bar_lyr -m display -d FEATURES -o select");
		my @rout_pad = $c->dealwithFeatureFile($csh_file);
		unlink ($csh_file);
		
		my $rout_pad_num = scalar(@rout_pad);
		if ( $rout_pad_num != 3) {
			$c->Messages("info","箭靶防呆靶数量应为3，程序退出");
				exit 0;
		}
		
		$c->CLEAR_LAYER(); 
        # print Dumper(\%inn_data);
        # 增加判断，当压合次数为1，判断是pnl_rout存在还是pnl_rout1存在
        my $show_pnl = "pnl_rout" . $i;
        if ($yh_num == 1 && $i == 1) {
            if ($c->LAYER_EXISTS($job_name, "panel", $show_pnl) eq "no") {
                $show_pnl = "pnl_rout";
            }
        }
        
        $f->COM("info, out_file=$csh_file, units=mm,args= -t layer -e $job_name/panel/$show_pnl -m display -d FEATURES");
        my @rout_data =  $c->dealwithFeatureFile($csh_file);
        unlink ($csh_file);
        my @lrpx_array;
        my @lrpy_array;

        for( my $k=0; $k<=$#rout_data; $k++) {
            if ($rout_data[$k]{type} eq 'line') {
                push (@lrpx_array, $rout_data[$k]{'xs'},$rout_data[$k]{'xe'});
                push (@lrpy_array, $rout_data[$k]{'ys'},$rout_data[$k]{'ye'});
            }
        }
     
        # %routPadData存储箭靶防呆靶数据
        my %routPadData;
        # 对 pnl_rout层的靶孔进行坐标归类
		if ($op_mode eq "4bar" || $op_mode eq "7bar"  || $op_mode eq "8bar") {
			#重新计算顶部靶的位置 20231108
			my $center_target_x=$xcenter;
			for( my $k=0; $k<$rout_pad_num; $k++) {
				if ( $rout_pad[$k]{y} < $ycenter and abs($rout_pad[$k]{x} - $xcenter) < 41) {
					$center_target_x = $rout_pad[$k]{x};
				}
			}
			for( my $k=0; $k<$rout_pad_num; $k++) {
				# 左上
				#翟鸣通知 工艺文件调整可以中间40范围内移动 20230824 by lyh
				#if ( $rout_pad[$k]{x} < $xcenter-40 && $rout_pad[$k]{y} > $ycenter) {
				if ( $rout_pad[$k]{x} < $center_target_x && $rout_pad[$k]{y} > $ycenter) {
					@{$routPadData{1}} = ($rout_pad[$k]{x}, $rout_pad[$k]{y});
				}
				
				 # 中上或右上       
				if ( $rout_pad[$k]{x} == $center_target_x && $rout_pad[$k]{y} > $ycenter) {
					@{$routPadData{2}} = ($rout_pad[$k]{x}, $rout_pad[$k]{y});
				}
				 # 中下或右下                
				if ( $rout_pad[$k]{x} == $center_target_x && $rout_pad[$k]{y} < $ycenter) {
					@{$routPadData{3}} = ($rout_pad[$k]{x}, $rout_pad[$k]{y});
				}
			}
			#print Dumper(\%routPadData);
			# 判断归类后的数据数量是否与归类前相同，不抛弃，不放弃
			my $routPadNum = scalar(keys  %routPadData );
			if ($routPadNum == 1) {
				#$f->PAUSE("Get Cor Error should be $rout_pad_num not $routPadNum");
				$c->Messages("info","Error 第${i}次压合坐标归类错误,应为${rout_pad_num},目前为${routPadNum},\n程序退出!\nTips:箭靶距panel中心线需在40mm范围内，请检查是否超范围\n");
						exit 0;
			}			
			if ($routPadNum != $rout_pad_num) {
				#$f->PAUSE("Get Cor Error should be $rout_pad_num not $routPadNum");
				$c->Messages("info","Error 第${i}次压合坐标归类错误,应为${rout_pad_num},目前为${routPadNum},\n程序退出!\nTips:中间三靶中右侧两靶需在panel中心线右侧\n");
						exit 0;
			}
			
#                取消该项目检测，http://192.168.2.120:82/zentao/story-view-6115.html  ————ynh 20231024
#				if ($routPadData{1}[1] != $routPadData{2}[1]) {
#					$c->Messages("info","Error pnl_rout$i ，上侧两靶标Y坐标不相同\n，程序退出");
#					exit 0;
#				}
			
		}
        
        my $minlrpx = min @lrpx_array;
        my $maxlrpx = max @lrpx_array;
        my $minlrpy = min @lrpy_array;
        my $maxlrpy = max @lrpy_array;
        
        my $pnl_rout_x = $maxlrpx - $minlrpx;
        my $pnl_rout_y = $maxlrpy - $minlrpy;
        my $inplan_routx = $lamin_data{$i}{'pnlroutx'}*25.4;
        my $inplan_routy = $lamin_data{$i}{'pnlrouty'}*25.4;
        # 检查是否捞边尺寸为本次压合的尺寸 ，允许数据0.005的公差     
        if (abs($pnl_rout_x - $inplan_routx) > 0.05 || abs($pnl_rout_y - $inplan_routy) > 0.05)  {
            #判断InPlan中的数据与CAM的设计数据是否相同
            #$f->PAUSE("CAM design pnl_rout${i}X direction is $pnl_rout_x,But inplan is $inplan_routx");
			my $cha1=abs($pnl_rout_x - $inplan_routx);
			my $cha2=abs($pnl_rout_y - $inplan_routy);
            $c->Messages("info","Error 第${i}次压合pnl_rout${i} 超出公差0.005mm \n
                X方向差值 $cha1 为${pnl_rout_x},InPlan值为${inplan_routx}\n
                Y方向差值 $cha2 为${pnl_rout_y},InPlan值为${inplan_routy}\n
                ，程序退出");
                    exit 0;
        }
        
        # 检查4靶位数据是否为本次压合的数据
         #print Dumper(\%inn_data );
        # 左上1及左下4为Y2数据
        my $bar4y2 = $inn_data{1}[1] - $inn_data{4}[1];
        # 右上2与右下3数据为Y1数据
        my $bar4y1 = $inn_data{2}[1] - $inn_data{3}[1];
        # 右上2与左上1的距离为X1数据
        my $bar4x1 = $inn_data{2}[0] - $inn_data{1}[0]; 
        # 右下3与左下4数据为X2数据
        my $bar4x2 = $inn_data{3}[0] - $inn_data{4}[0]; 

        print "CAM" . ": " . $bar4y1 ." " . $bar4y2 ." " . $bar4x1 . " " . $bar4x2 . "\r\n" ;
        print "MI"  . ": " . $lamin_data{$i}{'bar4y1'} . " " . $lamin_data{$i}{'bar4y2'}. " " . $lamin_data{$i}{'bar4x1'}. " " .$lamin_data{$i}{'bar4x2'}."\r\n" ;
        print "=======================\n";
        #print abs($bar4y1 - $lamin_data{$i}{'bar4y1'}) . abs($bar4x1 - $lamin_data{$i}{'bar4x1'}) . abs($bar4y2 - $lamin_data{$i}{'bar4y2'}).  abs($bar4x2 - $lamin_data{$i}{'bar4x2'}) . "\r\n";
        # Song 2019.11.21 当以上判定为3靶设计时，则不进行四靶判定
        if ($op_mode ne '3bar') {
            #code
            if (abs($bar4y1 - $lamin_data{$i}{'bar4y1'}) > 0.002
            || abs($bar4x1 - $lamin_data{$i}{'bar4x1'}) > 0.002
            || abs($bar4y2 - $lamin_data{$i}{'bar4y2'}) > 0.002
            || abs($bar4x2 - $lamin_data{$i}{'bar4x2'}) > 0.002 ) {
            #$f->PAUSE("CAM design 4 bar is not the same with MI InPlan,Detail See Log");
            $c->Messages("info","Error 第${i}次压合 $inn_layer CAM设计值与MI数据超出公差0.002mm：\n
                        CAM Y1: $bar4y1 Y2: $bar4y2 X1: $bar4x1 X2:$bar4x2 \n
                        MI  Y1:$lamin_data{$i}{'bar4y1'} Y2: $lamin_data{$i}{'bar4y2'} X1: $lamin_data{$i}{'bar4x1'} X2:$lamin_data{$i}{'bar4x2'} ，程序退出");
                    exit 0;
            }
        } else {
            # 当HDI InPlan数据库中存在4靶数据时，进行L2层的数据获取，用过滤器选择 hdi1-bat hdi-bajt 进行数据分割
            if (defined $lamin_data{$i}{'bar4y1'} && $lamin_data{$i}{'bar4y1'} ne '0') {
                my %bar_data = &checkInnerLayerBarDesign;              
            }
        }
        
		# 计算出四靶右上靶点到上下的捞边后的距离
		my $dis4C  = $maxlrpx - $inn_data{2}[0];
		my $dis4A1 = $maxlrpy - $inn_data{2}[1];
		my $dis4C1 = $maxlrpx - $inn_data{3}[0];
		my $dis4A2 = $inn_data{3}[1] - $minlrpy;
		print '$dis4C:'.$dis4C . '$dis4C1' .$dis4C1 ."\n";
		if ( abs($dis4C - $dis4C1) > 0.0001 ) {
			# $f->PAUSE("Error: $inn_layer right two bar not in same X Cor");
            $c->Messages("info","Error 第${i}次压合${inn_layer}右侧两靶孔X坐标不相同，程序退出");
                    exit 0;
		}
		print '$sig_bar_data' . "\n";
		print 'op_mode' . "$op_mode" . "\n";
		print Dumper(\%sig_bar_data);
		# === 2021.01.25 8靶输出时的距离计算 ===
		#%sig_bar_data
		my ($dis84C,$dis84A1,$dis84C1,$dis84A2,$bar84x1,$bar84y1,$bar84x2,$bar84y2) = ('','','','','','','','');
		if ($op_mode eq '8bar') {
			 $dis84C  = $maxlrpx - $sig_bar_data{2}[0];
			 $dis84A1 = $maxlrpy - $sig_bar_data{2}[1];
			 $dis84C1 = $maxlrpx - $sig_bar_data{3}[0];
			 $dis84A2 = $sig_bar_data{3}[1] - $minlrpy;
			$bar84y2 = $sig_bar_data{1}[1] - $sig_bar_data{4}[1];
			# 右上2与右下3数据为Y1数据
			$bar84y1 = $sig_bar_data{2}[1] - $sig_bar_data{3}[1];
			# 右上2与左上1的距离为X1数据
			$bar84x1 = $sig_bar_data{2}[0] - $sig_bar_data{1}[0]; 
			# 右下3与左下4数据为X2数据
			$bar84x2 = $sig_bar_data{3}[0] - $sig_bar_data{4}[0]; 
			# === 检测八靶数据是否与MI一致 ===2023.03.23 增加裁磨输出8靶,对比inplan数据的防呆===
			print "CAM" . ": " . $bar84y1 ." " . $bar84y2 ." " . $bar84x1 . " " . $bar84x2 . "\r\n" ;
			print "MI"  . ": " . $lamin_data{$i}{'sig4y1'} . " " . $lamin_data{$i}{'sig4y2'}. " " . $lamin_data{$i}{'sig4x1'}. " " .$lamin_data{$i}{'sig4x2'}."\r\n" ;
			print "=======================sig4y1,sig4y2,sig4x1,sig4x2\n";
            #code
			#my $sig4y1 = $lamin_data{$i}{'sig4y1'};
			#my $sig4y2 = $lamin_data{$i}{'sig4y2'};
			my $sig4x1 = $lamin_data{$i}{'sig4x1'};
			my $sig4x2 = $lamin_data{$i}{'sig4x2'};			
			if ($sig4x1 == 0) {
				$sig4x1 = $lamin_data{$i}{'bar4x1'};
			}
			if ($sig4x2 == 0) {
				$sig4x2 = $lamin_data{$i}{'bar4x2'};
			}			
            if (abs($bar84x1 - $sig4x1) > 0.002
            || abs($bar84y1 - $lamin_data{$i}{'sig4y1'}) > 0.002
            || abs($bar84x2 - $sig4x2) > 0.002
            || abs($bar84y2 - $lamin_data{$i}{'sig4y2'}) > 0.002 ) {
            #$f->PAUSE("CAM design 4 bar is not the same with MI InPlan,Detail See Log");
            $c->Messages("info","Error 第${i}次压合 线路靶CAM设计值与MI数据超出公差0.002mm：\n
                        CAM Y1: $bar84y1 Y2: $bar84y2 X1: $bar84x1 X2:$bar84x2 \n
                        MI  Y1:$lamin_data{$i}{'sig4y1'} Y2: $lamin_data{$i}{'sig4y2'} X1: $lamin_data{$i}{'sig4x1'} X2:$lamin_data{$i}{'sig4x2'} ，程序退出");
                    exit 0;
            }
		}
		
		
        # 检查3靶位数据是否为本次压合的数据
        my $bar3x = $routPadData{2}[0] - $routPadData{1}[0];
        my $bar3y = $routPadData{2}[1] - $routPadData{3}[1];
        print "CAM" . $bar3x ." ". $bar3y . "\r\n" ;
        print "MI"  . $lamin_data{$i}{'bar3x'} . " " . $lamin_data{$i}{'bar3y'} . "\r\n";
        print "=======================\n";        
        #print abs($bar3x - $lamin_data{$i}{'bar3x'}) .  abs($bar3y - $lamin_data{$i}{'bar3y'}) ."\r\n";
		#if ($op_mode ne '4bar') {

			if ( abs($bar3x - $lamin_data{$i}{'bar3x'}) > 0.002 || abs($bar3y - $lamin_data{$i}{'bar3y'}) > 0.002) {
            #$f->PAUSE("CAM design pnl_rout$i 3 bar is not the same with MI InPlan,Detail See Log");
            $c->Messages("info","Error 第$i 次压合 pnl_rout$i CAM设计值与MI数据不相同,公差0.002mm：\n
                         CAM $bar3x $bar3y
                         MI  $lamin_data{$i}{'bar3x'} $lamin_data{$i}{'bar3y'}，程序退出");
                    exit 0;
			}
		#}
		

        # 计算出箭靶上靶点到右长边的距离C；到上短边的距离A1；箭靶下靶点到下短边的距离A2；
		my $dis3A1 = $maxlrpy - $routPadData{2}[1];
		my $dis3C  = $maxlrpx - $routPadData{2}[0];
		my $dis3A2 = $routPadData{3}[1] - $minlrpy;
		my $dis3C1 = $maxlrpx - $routPadData{3}[0];
		# 判断上箭靶及下箭靶是否到右侧距离相同，X是否相同
		if (abs($dis3C - $dis3C1)>0.001) {
			#$f->PAUSE("Error:pnl_rour$i Two bar not in same X");
            $c->Messages("info","第${i}次压合Error:pnl_rour$i 中间两靶孔X坐标不相同，程序退出");
                    exit 0;
		}
        # 检测各侧靶孔是否同线
        my $upYmax = max ($inn_data{1}[1],$inn_data{2}[1],$routPadData{1}[1],$routPadData{2}[1]);
        my $upYmin = min ($inn_data{1}[1],$inn_data{2}[1],$routPadData{1}[1],$routPadData{2}[1]);
        print "upYmax:" . $upYmax . " upYmin: " . $upYmin . " " . "\n";
        print "=======================\n";
		# === 当MI信息中的三靶靶标数据与四靶靶标数据Y相同时，检查是否水平同线 ===
		#周涌通知 取消L靶的水平直线检测 20240513 by lyh
		# if (abs($lamin_data{$i}{'bar4y1'} - $lamin_data{$i}{'bar3y'}) < 0.1 ) {

			# if (abs($upYmax - $upYmin) >= 0.001 && $op_mode ne "3bar" ) {
				##判断上方的靶孔Y数据是否相同
				# $c->Messages("info","第${i}次压合判断上方的靶孔Y数据不相同，程序退出");
						# exit 0;
			# }
        
			# if (abs($inn_data{3}[1] - $routPadData{3}[1]) >= 0.001 && $op_mode ne "3bar" ) {
				##判断上方的靶孔Y数据是否相同
				##$f->PAUSE("第$i 次压合判断下方的靶孔Y数据不相同");
				# $c->Messages("info","第${i}次压合判断下方的靶孔Y数据不相同，程序退出");
						# exit 0;
			# }
		# }
        # 箭靶防呆靶与板边四角靶距≥70mm；
        if (abs($inn_data{1}[0] - $routPadData{1}[0]) <= 70 ) {
            #code
            #$f->PAUSE("第$i 次压合箭靶防呆靶与板边四角靶距小于70mm");
            $c->Messages("info","第${i}次压合箭靶防呆靶与板边四角靶距小于70mm，需预警工序");
        }

        # 输出为非三靶设计时才检测靶距数据
        if ($op_mode ne "3bar") {
			# 检测四靶靶孔XY方向坐标范围；
			my $minX4bar = min ($bar4x1, $bar4x2);
			my $maxX4bar = max ($bar4x1, $bar4x2);
			if ($minX4bar <= 250 || $maxX4bar >= 625 ) {
				#检测四靶靶孔X方向中心距在250~625mm
				#$f->PAUSE("第$i 次压合检测四靶靶孔X方向中心距不在250~625mm范围内");
				$c->Messages("info","第${i}次压合检测四靶靶孔X方向中心距不在250~625mm范围内，需预警工序");
			}
			my $minY4bar = min ($bar4y1,$bar4y2);
			my $maxY4bar = min ($bar4y1,$bar4y2);
			# === V3.0 更改 700-> 708
			if ($minY4bar <= 400 || $maxY4bar >= 708 ) {
				#Y方向靶中心距限制在400~700mm；
				#$f->PAUSE("第$i 次压合检测四靶靶孔Y方向靶中心距不在400~700mm范围内");
				$c->Messages("info","第${i}次压合检测四靶靶孔Y方向靶中心距不在400~708mm范围内，需预警工序");
			}
			# 检测四靶靶孔是否居中
			if (abs(($pnl_rout_x - $bar4x1)*0.5 - $dis4C) > 0.001) {
				#code
				$c->Messages("info","第${i}次压合检测四靶靶孔X方向不居中，需预警工序");
				#伍青通知 不对称需退出 20241224 by lyh
				#exit 0;
			}
			if (abs(($pnl_rout_y - $bar4y1)*0.5 - $dis4A1) > 0.001) {
				#code
				$c->Messages("info","第${i}次压合检测四靶靶孔Y方向不居中，需预警工序");
				exit 0;
			}        
		} 
			
		# 增加靶模式判断，是4靶还是7靶
		# === 当盲埋孔同时存在，使用7靶定位 === http://192.168.2.120:82/zentao/story-view-2222.html
		# === 2021.11.17 全面废除7靶规则，不再兼容旧料号的七靶要求
		# === 2022.07.26 起用7靶规则
		my $barmode = $op_mode;
		# cancle by song 2021.11.17
		#if ((defined $lamin_data{$i}{'blindLayer'} && $i == $yh_num) || (defined $lamin_data{$i}{'blindLayer'} && defined $lamin_data{$i}{'burryLayer'})) {
		#	$barmode = '7bar';
		#}
		if ($op_mode eq '8bar') {
			$barmode = '8bar';
		}
		# cancle by song 2021.11.17
		## === 废除7靶规则 ===
		#if ($op_mode eq '4bar' && $barmode eq '7bar') {
		#	$barmode = '4bar';
		#}
	

        # 取出左上角的产线需求值
         $yh_data{$i} = {'PnlRoutX',$pnl_rout_x,
                        'PnlRoutY',$pnl_rout_y,
                        'bar4x1',$bar4x1,
                        'bar4x2',$bar4x2,
                        'bar4y1',$bar4y1,
                        'bar4y2',$bar4y2,
                        'bar3x',$bar3x,
                        'bar3y',$bar3y,
						'bar3disA1',$dis3A1,
						'bar3disC',$dis3C,
						'bar3disC1',$dis3C1,
						'bar3disA2',$dis3A2,
						'bar4disA1',$dis4A1,
						'bar4disC',$dis4C,
						'bar4disC1',$dis4C1,
						'bar4disA2',$dis4A2,
						'bar84disA1',$dis84A1,
						'bar84disC',$dis84C,
						'bar84disC1',$dis84C1,
						'bar84disA2',$dis84A2,
						'bar84x1',$bar84x1,
                        'bar84x2',$bar84x2,
                        'bar84y1',$bar84y1,
                        'bar84y2',$bar84y2,
						'barmode',$barmode
        };       
        unlink ($csh_file);
    }
	        print Dumper(\%yh_data);
	$c->CLEAR_LAYER();
	&save_parameter;
    &writeLog;
    $c->Messages("info","裁磨输出，程序版本$appVersion 输出完成，详见$outputPath");
}

# 通孔板 HDI InPlan有七靶设计时，使用线路层的靶位设计进行与inplan数据的对比
# 以下检测与输出无关
sub checkInnerLayerBarDesign
{
    # 默认层别为L2层，判断L2层是否存在，是否为外层；
    
    # 打开Step panel
    $c->OPEN_STEP($job_name,'panel');
    $c->CHANGE_UNITS('mm');
    $c->CLEAR_LAYER();    
    # 过滤器选择L2层的hdi1-bajt， hdi1-bat 靶位
    $c->FILTER_RESET();
    $c->AFFECTED_LAYER('l2','yes');
    $c->FILTER_RESET();
    $c->FILTER_SET_INCLUDE_SYMS("hdi1-bat\;hdi1-bajt");
    $c->FILTER_SELECT();
    if ($c->GET_SELECT_COUNT() != 7) {
        $c->Messages("info","靶位未按MI指示设计，请检查！\n");
    }
    $c->CLEAR_FEAT();
    $c->SEL_REF_FEAT('inn','disjoint','positive');
    # 初始变量
    my %bar_data;
    if ($c->GET_SELECT_COUNT() != 4) {
        $c->Messages("info","非4靶位\n");
    } else {
        # 获取选择的物件坐标
        # 取inn层的五孔或四孔的关系，左上，右上，右下, 左下。
        my $csh_file  = "$tmpPath/info_csh.$$";
        $f->COM("info, out_file=$csh_file, units=mm,args= -t layer -e $job_name/panel/l2 -d FEATURES -o select");
        my @getlayerBar = $c->dealwithFeatureFile($csh_file);
        unlink ($csh_file);
        my $get_bar_data = &getFourCor(@getlayerBar);

        if ($get_bar_data eq 'notpad') {
            #code
            $c->Messages("info","L2层 添加的标靶为非pad\n，程序退出");
            exit 0;
        } elsif ($get_bar_data eq 'splitError') {
            $c->Messages("info","L2层 添加的标靶坐标归类错误\n，程序退出");
            exit 0;
        } else {
            %bar_data = %$get_bar_data;
        }
        print Dumper(\%bar_data);

    }
    # 取消影响层
    $c->CLEAR_LAYER(); 
    # 判定靶位坐标是否同线
        # 上面两个坐标的Y是否相同
        if ($bar_data{1}[1] ne $bar_data{2}[1] ) {
            $c->Messages("info","L2层 上方两个标靶不同线\n，程序退出");
            exit 0;
        }
        # 右侧的两个坐标X是否相同
        if ($bar_data{2}[0] ne $bar_data{3}[0] ) {
            $c->Messages("info","L2层 右侧两个标靶不同线\n，程序退出");
            exit 0;
        }        
    # 数据与inplan对比
    # 不相同则报错
    $bar_data{'bar4y1'} = $bar_data{2}[1] - $bar_data{3}[1];
    $bar_data{'bar4x1'} = $bar_data{2}[0] - $bar_data{1}[0];
    $bar_data{'bar4y2'} = $bar_data{1}[1] - $bar_data{4}[1];
    $bar_data{'bar4x2'} = $bar_data{3}[0] - $bar_data{4}[0];
    if (abs($bar_data{'bar4y1'} - $lamin_data{1}{'bar4y1'}) > 0.002
        || abs($bar_data{'bar4x1'} - $lamin_data{1}{'bar4x1'}) > 0.002
        || abs($bar_data{'bar4y2'} - $lamin_data{1}{'bar4y2'}) > 0.002
        || abs($bar_data{'bar4x2'} - $lamin_data{1}{'bar4x2'}) > 0.002 ) {
        #$f->PAUSE("CAM design 4 bar is not the same with MI InPlan,Detail See Log");
        $c->Messages("info","Error 第L2层 CAM设计值与MI数据超出公差0.002mm：\n
        CAM Y1:$bar_data{'bar4y1'} Y2: $bar_data{'bar4y2'}  X1: $bar_data{'bar4x1'} X2: $bar_data{'bar4x2'} \n
        MI  Y1:$lamin_data{1}{'bar4y1'} Y2: $lamin_data{1}{'bar4y2'} X1: $lamin_data{1}{'bar4x1'} X2:$lamin_data{1}{'bar4x2'} ，程序退出");
                exit 0;
    }
    return %bar_data;
}



# 坐标进行分割
sub getFourCor
{
    my (@getbarData) = @_;
    # 存储四靶靶孔数据
    my %bar_data;
    my $bar_num = scalar(@getbarData);
    # 取消5靶孔判断 2019.11.21 Song   
    if ( $bar_num == 4 ) {            
        #判断四个靶孔的方向
        for(my $k=0; $k<$bar_num; $k++) {
            if ($getbarData[$k]{type} != 'pad') {
                return 'notpad';
            }
            # 左上
            if ($getbarData[$k]{x} < $xcenter && $getbarData[$k]{y} > $ycenter) {
                 @{$bar_data{1}} = ($getbarData[$k]{x},$getbarData[$k]{y});
            }
            # 右上
            if ($getbarData[$k]{x} > $xcenter && $getbarData[$k]{y} > $ycenter) {
                @{$bar_data{2}} = ($getbarData[$k]{x},$getbarData[$k]{y});
            }
            # 右下为2颗
            if ($getbarData[$k]{x} > $xcenter && $getbarData[$k]{y} < $ycenter) {
                @{$bar_data{3}} = ($getbarData[$k]{x},$getbarData[$k]{y});
            }
            # 左下		
            if ($getbarData[$k]{x}  < $xcenter && $getbarData[$k]{y} < $ycenter) {
                @{$bar_data{4}} = ($getbarData[$k]{x},$getbarData[$k]{y});
            }
        }
    }
    my $barInnNum = scalar(keys %bar_data);
    if ($barInnNum != $bar_num) {
        #归类前与归类后数量是否相同
        return 'splitError';
    } else {
        return \%bar_data;
    }
}


# 用来保存压合打靶信息#
sub save_parameter
{
	my $setup_file1 = $outputPath . "/" ."8097";
	my $setup_file2 = $outputPath . "/" ."9900_1";
	my $setup_file3 = $outputPath . "/" ."9900_2";
	my $yh_num = $lamin_data{'yh_num'};

	for (my $i=1; $i<=$yh_num; $i++) {
		my $tail_name = $lamin_data{$i}{'mrpName'};
		print $tail_name;
		my $dirPath1 = $outputPath . "/" . $tail_name . "/" . "8097";
		my $tPath = '' ;
		for ( split("/",$dirPath1) ){
			if ( $tPath ) {
				$tPath = $tPath . $_ . '/';
			}else{
				$tPath = $_ . '/'  ;
			}

			unless ( -e $tPath ){
				mkdir "$tPath",0777 or warn "Cannot make $tPath directory: $!";
			}
		}
        my $tmp_file =  $dirPath1 . "/" . $tail_name;
        if (-e $tmp_file) {
            #code
            unlink $tmp_file;
        }
        
		my $filePath1 = $dirPath1 . "/" . $tail_name  . '.csv';
		if ( open(SEASE, ">:encoding(gbk)","$filePath1") or die("$!")) {
			print SEASE "$tail_name,0,0,0,0,,0,1,1,0,1,2,0,0\r\n";
            printf SEASE "%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,0,0,0,0,0,0,0,0,0,0,%.3f,%.3f,%.3f,0,0,0\r\n",
			$yh_data{$i}{'PnlRoutY'},$yh_data{$i}{'PnlRoutX'},$yh_data{$i}{'bar3disC'},$yh_data{$i}{'bar3y'},$yh_data{$i}{'bar3disA1'},$yh_data{$i}{'bar3disA2'},$yh_data{$i}{'bar3disC1'},$lamin_data{$i}{'yhThick'},$lamin_data{$i}{'yhThick'} + $lamin_data{$i}{'yhThkPlus'},$lamin_data{$i}{'yhThick'} - $lamin_data{$i}{'yhThkDown'};

			printf SEASE "%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,%.4f,0,0,0,0,0,0,0,0,0,0,%.3f,%.3f,%.3f,0,0,0\r\n",
            $yh_data{$i}{'PnlRoutY'}/25.4, $yh_data{$i}{'PnlRoutX'}/25.4, $yh_data{$i}{'bar3disC'}/25.4, $yh_data{$i}{'bar3y'}/25.4, $yh_data{$i}{'bar3disA1'}/25.4, $yh_data{$i}{'bar3disA2'}/25.4,$yh_data{$i}{'bar3disC1'}/25.4,            $lamin_data{$i}{'yhThick'} / 25.4,($lamin_data{$i}{'yhThick'} + $lamin_data{$i}{'yhThkPlus'})/25.4,($lamin_data{$i}{'yhThick'} - $lamin_data{$i}{'yhThkDown'})/25.4 ;
            print SEASE "0,0,0,0,0,0,0,0,0,0,,,,,,,,,,,,,\r\n";
			print SEASE "0,0,0,0,0,0,0,0,0,0,0";
		}
		close (SEASE);
        # nc_num = 0  通孔三靶
		# nc_num = 1  通孔四靶
		# nc_num = 2  七靶设计 四靶Y方向防呆
		# nc_num = 3  七靶设计 四靶X方向防呆
		# 4bar模式下，9900_2 即文件三，使用见靶不钻模式，即左模式及右模式为数字1，即第四列和第九列
        my $nc_num = 2;
        if (abs($yh_data{$i}{'bar4y2'} - $yh_data{$i}{'bar4y1'}) > 0 && $yh_data{$i}{'bar4x1'} eq $yh_data{$i}{'bar4x2'}) {
            $nc_num = 2;
        } elsif ($yh_data{$i}{'bar4x1'} ne $yh_data{$i}{'bar4x2'}) {
            $nc_num = 3;            
        } elsif ($yh_data{$i}{'bar4x1'} eq '0' or  $yh_data{$i}{'bar4x2'} eq '0') {
            # 判断是否4靶数据不存在，当四靶数据不存在，则使用3靶数据再输出一次
            $nc_num = 0
        } 
        my $barmode = $yh_data{$i}{'barmode'};

		
		my $dirPath2 = $outputPath . "/" . $tail_name . "/" . "9900_1";
		$tPath = '';
		for ( split("/",$dirPath2) ){
			if ( $tPath ) {
				$tPath = $tPath . $_ . '/';
			}else{
				$tPath = $_ . '/'  ;
			}

			unless ( -e $tPath ){
				mkdir "$tPath",0777 or warn "Cannot make $tPath directory: $!";
			}
		}
        $tmp_file =  $dirPath2 . "/" . $tail_name;
        if (-e $tmp_file) {
            #code
            unlink $tmp_file;
        }
		my $filePath2 = $dirPath2 . "/" . $tail_name . '.csv';
		if ( open(SEASE, ">:encoding(gbk)", "$filePath2") or die("$!")) {
			if ($barmode eq '7bar') {
				#正常输出3靶数据
				print SEASE "料号名称,$tail_name\r\n";
				print SEASE "基板孔数,3\r\n";
				print SEASE "钻孔型态,H3_3M\r\n";
				print SEASE "钻孔行数,2\r\n";
				printf SEASE "基板长度,%.4f\r\n",$yh_data{$i}{'PnlRoutX'};
				printf SEASE "基板宽度,%.4f\r\n",$yh_data{$i}{'PnlRoutY'};
				printf SEASE "DX,%.4f\r\n",$yh_data{$i}{'bar3disA1'};
				printf SEASE "DY,%.4f\r\n",$yh_data{$i}{'bar3disC'};
				printf SEASE "基板厚度,%.3f\r\n",$lamin_data{$i}{'yhThick'};
				print SEASE "坐标输入\r\n";
				print SEASE "Y位,左点序,左X位,左模式,参考点,Y位,右点序,右X位,右模式,参考点,右Y偏移\r\n";
				printf SEASE "0,1,0,2,0-0-0-0,0,2,%.4f,2,0-0-0-0,0\r\n",$yh_data{$i}{'bar3y'};
				printf SEASE "%.4f,3,0,2,0-0-0-0,0,4,0,0,0-0-0-0,0",$yh_data{$i}{'bar3x'};
			
			} elsif ($barmode eq '4bar') {
				# 使用9900_2输写入9900_1文件
			    print SEASE "料号名称,$tail_name\r\n";
                print SEASE "基板孔数,4\r\n";
                print SEASE "钻孔型态,NC\r\n";
                print SEASE "钻孔行数,$nc_num\r\n";
                printf SEASE "基板长度,%.4f\r\n",$yh_data{$i}{'PnlRoutX'};
                printf SEASE "基板宽度,%.4f\r\n",$yh_data{$i}{'PnlRoutY'};
                printf SEASE "DX,%.4f\r\n",$yh_data{$i}{'bar4disA1'};
                printf SEASE "DY,%.4f\r\n",$yh_data{$i}{'bar4disC'};
                printf SEASE "基板厚度,%.3f\r\n",$lamin_data{$i}{'yhThick'};
                print SEASE "坐标输入\r\n";
                print SEASE "Y位,左点序,左X位,左模式,参考点,Y位,右点序,右X位,右模式,参考点,右Y偏移\r\n";
                if ($nc_num == 2) {
                    # Y轴防呆，此种情况X1=X2。
                    printf SEASE "0,1,0,2,0-0-0-0,0,2,%.4f,2,0-0-0-0,0\r\n",$yh_data{$i}{'bar4y1'};
                    printf SEASE "%.4f,3,0,2,0-0-0-0,0,4,%.4f,2,0-0-0-0,0",$yh_data{$i}{'bar4x1'},$yh_data{$i}{'bar4y2'};
                    
                } elsif ($nc_num == 3) {
                    if ($yh_data{$i}{'bar4x1'} - $yh_data{$i}{'bar4x2'} < 0.001) {
                        #以下代码区别为第四列，见靶钻为2，见靶不钻为0.
                        printf SEASE "0,1,0,2,0-0-0-0,0,2,%.4f,2,0-0-0-0,0\r\n",$yh_data{$i}{'bar4y1'};
                        printf SEASE "%.4f,3,0,2,0-0-0-0,0,4,%.4f,0,0-0-0-0,0\r\n",$yh_data{$i}{'bar4x1'},$yh_data{$i}{'bar4y2'};
                        printf SEASE "%.4f,5,0,0,0-0-0-0,0,6,%.4f,2,0-0-0-0,0",$yh_data{$i}{'bar4x2'},$yh_data{$i}{'bar4y2'};                    
                    } else {
                        printf SEASE "0,1,0,2,0-0-0-0,0,2,%.4f,2,0-0-0-0,0\r\n",$yh_data{$i}{'bar4y1'};
                        printf SEASE "%.4f,3,0,0,0-0-0-0,0,4,%.4f,2,0-0-0-0,0\r\n",$yh_data{$i}{'bar4x2'},$yh_data{$i}{'bar4y2'};
                        printf SEASE "%.4f,5,0,2,0-0-0-0,0,6,%.4f,0,0-0-0-0,0",$yh_data{$i}{'bar4x1'},$yh_data{$i}{'bar4y2'};
                    }
                }
			} elsif ($barmode eq '8bar' ) {
				my $nc_num = 2; # 默认8靶模式下Y防呆 # Song 2021.01.25 
				# === 2021.01.25 先打线路对位4靶，再打钻孔对位4靶 === 
				# 使用9900_2输写入9900_1文件
			    print SEASE "料号名称,$tail_name\r\n";
                print SEASE "基板孔数,4\r\n";
                print SEASE "钻孔型态,NC\r\n";
                print SEASE "钻孔行数,$nc_num\r\n";
                printf SEASE "基板长度,%.4f\r\n",$yh_data{$i}{'PnlRoutX'};
                printf SEASE "基板宽度,%.4f\r\n",$yh_data{$i}{'PnlRoutY'};
                printf SEASE "DX,%.4f\r\n",$yh_data{$i}{'bar84disA1'};
                printf SEASE "DY,%.4f\r\n",$yh_data{$i}{'bar84disC'};
                printf SEASE "基板厚度,%.3f\r\n",$lamin_data{$i}{'yhThick'};
                print SEASE "坐标输入\r\n";
                print SEASE "Y位,左点序,左X位,左模式,参考点,Y位,右点序,右X位,右模式,参考点,右Y偏移\r\n";
				# Y轴防呆，此种情况X1=X2。
				printf SEASE "0,1,0,2,0-0-0-0,0,2,%.4f,2,0-0-0-0,0\r\n",$yh_data{$i}{'bar84y1'};
				printf SEASE "%.4f,3,0,2,0-0-0-0,0,4,%.4f,2,0-0-0-0,0",$yh_data{$i}{'bar84x1'},$yh_data{$i}{'bar84y2'};
			} else {
				$c->Messages("info","裁磨输出，未判断出靶位逻辑，程序退出，请手动删除已输出文件");
			}
		}
		

		close (SEASE);
		
		my $dirPath3  = $outputPath . "/" . $tail_name . "/" . "9900_2";
		$tPath = '';
		for ( split("/",$dirPath3) ){
			if ( $tPath ) {
				$tPath = $tPath . $_ . '/';
			}else{
				$tPath = $_ . '/'  ;
			}

			unless ( -e $tPath ){
				mkdir "$tPath",0777 or warn "Cannot make $tPath directory: $!";
			}
		}
        $tmp_file =  $dirPath3 . "/" . $tail_name;
        if (-e $tmp_file) {
            #code
            unlink $tmp_file;
        }

		
		my $filePath3 = $dirPath3 . "/" . $tail_name  . '.csv';

		if ( open(SEASE,">:encoding(gbk)", "$filePath3") or die("$!")) {
            if ($nc_num == 0) {
                #写入等同9900_1的三靶数据，变更参数2为0，见靶不钻
                print SEASE "料号名称,$tail_name\r\n";
                print SEASE "基板孔数,3\r\n";
                print SEASE "钻孔型态,NC\r\n";
                print SEASE "钻孔行数,2\r\n";
                printf SEASE "基板长度,%.4f\r\n",$yh_data{$i}{'PnlRoutX'};
                printf SEASE "基板宽度,%.4f\r\n",$yh_data{$i}{'PnlRoutY'};
                printf SEASE "DX,%.4f\r\n",$yh_data{$i}{'bar3disA1'};
                printf SEASE "DY,%.4f\r\n",$yh_data{$i}{'bar3disC'};
                printf SEASE "基板厚度,%.3f\r\n",$lamin_data{$i}{'yhThick'};
                print SEASE "坐标输入\r\n";
                print SEASE "Y位,左点序,左X位,左模式,参考点,Y位,右点序,右X位,右模式,参考点,右Y偏移\r\n";
                printf SEASE "0,1,0,1,0-0-0-0,0,2,%.4f,1,0-0-0-0,0\r\n",$yh_data{$i}{'bar3y'};
                printf SEASE "%.4f,3,0,1,0-0-0-0,0,4,0,0,0-0-0-0,0",$yh_data{$i}{'bar3x'};                
                
            } else {
				# showmode 2 --> 见靶钻靶
				# showmode 1 --> 见靶不钻
				my $showmode = 2;
				if ($barmode eq '4bar') {
					$showmode = 1;
				}
				
                print SEASE "料号名称,$tail_name\r\n";
                print SEASE "基板孔数,4\r\n";
                print SEASE "钻孔型态,NC\r\n";
                print SEASE "钻孔行数,$nc_num\r\n";
                printf SEASE "基板长度,%.4f\r\n",$yh_data{$i}{'PnlRoutX'};
                printf SEASE "基板宽度,%.4f\r\n",$yh_data{$i}{'PnlRoutY'};
                printf SEASE "DX,%.4f\r\n",$yh_data{$i}{'bar4disA1'};
                printf SEASE "DY,%.4f\r\n",$yh_data{$i}{'bar4disC'};
                printf SEASE "基板厚度,%.3f\r\n",$lamin_data{$i}{'yhThick'};
                print SEASE "坐标输入\r\n";
                print SEASE "Y位,左点序,左X位,左模式,参考点,Y位,右点序,右X位,右模式,参考点,右Y偏移\r\n";
                if ($nc_num == 2) {
                    # Y轴防呆，此种情况X1=X2。
                    #printf SEASE "0,1,0,2,0-0-0-0,0,2,%.4f,2,0-0-0-0,0\r\n",$yh_data{$i}{'bar4y1'};
                    #printf SEASE "%.4f,3,0,2,0-0-0-0,0,4,%.4f,2,0-0-0-0,0",$yh_data{$i}{'bar4x1'},$yh_data{$i}{'bar4y2'};
					
					printf SEASE "0,1,0,%s,0-0-0-0,0,2,%.4f,%s,0-0-0-0,0\r\n",$showmode,$yh_data{$i}{'bar4y1'},$showmode;
                    printf SEASE "%.4f,3,0,%s,0-0-0-0,0,4,%.4f,%s,0-0-0-0,0",$yh_data{$i}{'bar4x1'},$showmode,$yh_data{$i}{'bar4y2'},$showmode;
                    
                } elsif ($nc_num == 3) {
                    if ($yh_data{$i}{'bar4x1'} - $yh_data{$i}{'bar4x2'} < 0.001) {
                        #以下代码区别为第四列，见靶钻为2，见靶不钻为0.
                        #printf SEASE "0,1,0,2,0-0-0-0,0,2,%.4f,2,0-0-0-0,0\r\n",$yh_data{$i}{'bar4y1'};
                        #printf SEASE "%.4f,3,0,2,0-0-0-0,0,4,%.4f,0,0-0-0-0,0\r\n",$yh_data{$i}{'bar4x1'},$yh_data{$i}{'bar4y2'};
                        #printf SEASE "%.4f,5,0,0,0-0-0-0,0,6,%.4f,2,0-0-0-0,0",$yh_data{$i}{'bar4x2'},$yh_data{$i}{'bar4y2'};
						printf SEASE "0,1,0,%s,0-0-0-0,0,2,%.4f,%s,0-0-0-0,0\r\n",$showmode,$yh_data{$i}{'bar4y1'},$showmode;
                        printf SEASE "%.4f,3,0,%s,0-0-0-0,0,4,%.4f,0,0-0-0-0,0\r\n",$yh_data{$i}{'bar4x1'},$showmode,$yh_data{$i}{'bar4y2'};
                        printf SEASE "%.4f,5,0,0,0-0-0-0,0,6,%.4f,%s,0-0-0-0,0",$yh_data{$i}{'bar4x2'},$yh_data{$i}{'bar4y2'},$showmode; 
                    } else {
                        #printf SEASE "0,1,0,2,0-0-0-0,0,2,%.4f,2,0-0-0-0,0\r\n",$yh_data{$i}{'bar4y1'};
                        #printf SEASE "%.4f,3,0,0,0-0-0-0,0,4,%.4f,2,0-0-0-0,0\r\n",$yh_data{$i}{'bar4x2'},$yh_data{$i}{'bar4y2'};
                        #printf SEASE "%.4f,5,0,2,0-0-0-0,0,6,%.4f,0,0-0-0-0,0",$yh_data{$i}{'bar4x1'},$yh_data{$i}{'bar4y2'};
						printf SEASE "0,1,0,%s,0-0-0-0,0,2,%.4f,%s,0-0-0-0,0\r\n",$showmode,$yh_data{$i}{'bar4y1'},$showmode;
                        printf SEASE "%.4f,3,0,0,0-0-0-0,0,4,%.4f,%s,0-0-0-0,0\r\n",$yh_data{$i}{'bar4x2'},$yh_data{$i}{'bar4y2'},$showmode;
                        printf SEASE "%.4f,5,0,%s,0-0-0-0,0,6,%.4f,0,0-0-0-0,0",$yh_data{$i}{'bar4x1'},$showmode,$yh_data{$i}{'bar4y2'};
                    }
                }
            }
		}
		close (SEASE);
	}
}

sub getInplanPnlRout{
    my ($dbc, $drc_job) = @_;
    my @pnlrout_info;
    my $sql = "
	SELECT
		a.JOB_NAME,
		b.MRP_NAME,
		a.WORK_CENTER_CODE,
		a.OPERATION_CODE,
		a.DESCRIPTION 
	FROM
		vgt_hdi.rpt_job_trav_sect_list a
		INNER JOIN vgt_hdi.Rpt_Job_Process_List b ON a.ROOT_ID = b.ROOT_ID 
		AND a.PROC_ITEM_ID = b.ITEM_ID 
		AND a.PROC_REVISION_ID = b.REVISION_ID 
	WHERE
		a.OPERATION_CODE IN ( 'HDI23501' ) 
		AND a.JOB_NAME = '$drc_job'
		";
    my $sth = $dbc->prepare($sql);#结果保存在$sth中
    $sth->execute() or die "无法执行SQL语句:$dbc->errstr";

    # --循环所有行数据
    while (my @recs=$sth->fetchrow_array) {
		push(@pnlrout_info,\@recs);
	}
    # --返回信息
    return @pnlrout_info;

}
	
	
sub writeLog
{
    unless ( -e $userDir ){
        $c->Messages("info","未获取到用户目录，不能写入记录");
        return;
    }
    my $miData;
    my $camData;
    my $DateTime = strftime "%Y.%m.%d %H:%M:%S", localtime(time);
    print $DateTime;
    
    
    my $cmd="hostname";
    my $ophost=`$cmd`;
    chomp($ophost);
    my $plat;
    if ( $^O eq 'linux' ) {
        $plat = 'Linux' . '_' . "$ENV{INCAM_SERVER}";
        
    } elsif ( $^O eq  MSWin32 ) {
        #code   
        $plat = 'Windows';
    }
    

    if ( open(SEASE,">>:encoding(utf8)", "$userDir/pnlRoutLog") or die("$!")) {
        
            $lamin_data{'Time'} = $DateTime;
            $yh_data{'Time'} = $DateTime;
            $lamin_data{'softuser'} = $softuser;
            $yh_data{'softuser'} = $softuser;
            $yh_data{'hostname'} = $ophost;
            my $mi_name = Data::Dumper->new([\%lamin_data],[qw(lamin_data)]);
            $miData = $mi_name->Dump;
			print SEASE $miData;
            my $cam_name = Data::Dumper->new([\%yh_data],[qw(yh_data)]);
            $camData = $cam_name->Dump;
			print SEASE $camData;           
		}
 
    close (SEASE);
    
    # 写入hash开始 
    $miData =~ s/'/''/g;
    $camData =~ s/'/''/g;
    
    my $sql = "insert into panel_rout_output_log
    (job,Hash_str_mi,Hash_str_cam,log_time,creator,localhost,software_platform,app_Version)
    values ('$job_name','$miData','$camData',now(),'$softuser','$ophost','$plat','$appVersion')";
    
    my $sth = $dbc_m->prepare($sql);#结果保存在$sth中
    $sth->execute() or die "无法执行SQL语句:$dbc_m->errstr";
}



sub check_no_output {
	
	# MI数据中的压合次数
    my $yh_num = $lamin_data{'yh_num'};
	my $panel_y_inch = $lamin_data{$yh_num}{'pnlYInch'};
	my $final_bar3y =  $lamin_data{$yh_num}{'bar3y'};
	my $final_bar4y1 = $lamin_data{$yh_num}{'bar4y1'};
	# 开料Y小于24.5inch，T靶在长边不给输出裁磨
	if (abs($final_bar3y - $final_bar4y1) > 4 and $panel_y_inch < 24.5) {
		return False;
	}
	return True;
}

sub get_select_from_win{	
	$mw = MainWindow->new();	
	$mw->geometry( "+700+250" );
	$mw->Label(-text=>"@_ 层设计有8靶,请手动选择输出模式",-font => 'courier 15 bold',-background => '#FDC74D')->pack(-fill=>x,-ipady=>5);
	my $set_frame = $mw->Frame(-borderwidth => 2,)->pack(-fill=>both,-expand=>1);
	my $rb1 = $set_frame->Radiobutton(-background => white,-text => '8靶模式',-variable=>\$mode_bar_win,-value=>'8bar',-font => "times 16",-state=>'normal')->pack(-side=>'left',-ipady => 5,-expand=>1,-fill=>x);
	$rb1->invoke;
	$set_frame->Radiobutton(-background => white,-text => '4靶模式',-variable=>\$mode_bar_win,-value=>'4bar',-font => "times 16",-state=>'normal')->pack(-side=>'left',-ipady => 5,-expand=>1,-fill=>x);
	$mw->Button(-background => '#FDC74D',-font => 'courier 20',-activeforeground=>"red",-text=>"Apply",-command=>sub{$mw->destroy})->pack(-side=>'right',-expand=>1);
	MainLoop;
	return $mode_bar_win;
}


sub get_bar_note{
	#从inplan备注中获得钻靶的信息
    my ($dbc, $drc_job) = @_;	
	my $sql = "
	SELECT 
    RJTSL.JOB_NAME, 
		proc.mrp_name, 
    RJTSL.DESCRIPTION, 
    nts.note_string 
    FROM VGT_HDI.RPT_JOB_TRAV_SECT_LIST RJTSL
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
    WHERE RJTSL.JOB_NAME = '$drc_job'
				AND RJTSL.DESCRIPTION LIKE '%X-RAY打靶%' 
				AND   nts.note_string LIKE '%见靶钻_孔%'" ;
	my $sth = $dbc->prepare($sql);#结果保存在$sth中
    $sth->execute() or die "无法执行SQL语句:$dbc->errstr";
	 
	  # --循环所有行数据
    while (my @recs=$sth->fetchrow_array) {
		my $fromlayer;	
		my $tolaylayer;			
        my @stackProcess = split(/-/,$recs[1]);	
		my $bar_mode;
		if ($recs[3] =~ /见靶钻4孔/){
			$bar_mode = "4bar";
		}elsif($recs[3] =~ /见靶钻8孔/){
			$bar_mode = "8bar";
		}		
		if(scalar(@stackProcess) == 1){
			$fromlayer = "l2";
			$tolaylayer = substr($drc_job,4,2) - 1;				
			$tolaylayer =~ s/^0+//;	
			$tolaylayer	= "l".$tolaylayer;	
			$process_data{$fromlayer} = $bar_mode;
			$process_data{$tolaylayer} = $bar_mode;
			
		}else{
			my $get_layer = $stackProcess[1];
			# $get_layer =~ s/^\s+|\s+$//g;	
			$fromlayer = substr($get_layer,1,2) + 1;
			$fromlayer =~ s/^0+//;			
			$fromlayer	= "l".$fromlayer;
			$tolaylayer = substr($get_layer,3,2) - 1;
			$tolaylayer =~ s/^0+//;				
			$tolaylayer	= "l".$tolaylayer;	
			$process_data{$fromlayer} = $bar_mode;
			$process_data{$tolaylayer} = $bar_mode;			
		}
    }
    return %process_data;	
}


sub judge_led_board{

	#判断是否为LED板 
    my ($dbc, $drc_job) = @_;

	my $sql = "
	SELECT
			i.ITEM_NAME AS JobName,
			job.es_led_board_
	FROM
			VGT_hdi.PUBLIC_ITEMS i,
			VGT_hdi.JOB_DA job
	WHERE
			i.ITEM_NAME = '$drc_job'
			AND i.item_id = job.item_id
			AND i.revision_id = job.revision_id" ;
	my $sth = $dbc->prepare($sql);#结果保存在$sth中
    $sth->execute() or die "无法执行SQL语句:$dbc->errstr";
	 my @recs=$sth->fetchrow_array;
	return $recs[1];
}
__END__
2019.9.20
作者：Chao.Song
版本：1.0
1.增加判断压合次数，压合次数为1，且非HDI板，则使用层别pnl_rout;

2019.9.27
作者：Chao.Song
版本：1.1
1.更改输出路径增加两级文件夹；

2019.9.28
作者：Chao.Song
版本：1.2
1.X防呆，Y防呆方案；
2.无4靶数据。
3.换行符变为\r\n.

2019.10.08
作者：Chao.Song
版本：1.3
1.计算xcenter，ycenter保留三位小数；
2.inn层四靶五靶提醒变为非3靶4靶提醒。(实际包括三靶四靶五靶支持输出)；
3.增加从inplan无法获取数据的判断；
4.增加判断，当压合次数为一次，且设计铣带层为pnl_rout,且pnl_rout层无靶标设计时，使用inn层的定义。 2019.10.08；
5.增加inn层是否存在的判断。

2019.10.15
作者：Chao.Song
版本：1.4
1.更改输出文件格式为gbk；
更改输出文件名加后缀csv；

2019.10.15
作者：Chao.Song
版本：1.5
增加数据防呆：
1.四靶靶孔X方向中心距在250~625mm；Y方向靶中心距限制在400~700mm；
2.靶孔是否同线；
3.靶标中心距离成型区距离≥6.35mm；
4.箭靶防呆靶与板边四角靶距≥70mm；
5.计算xcenter，ycenter保留4位小数；

2019.10.16
作者：Chao.Song
版本：1.6
1.创建带后缀的.csv文件前，删除不带后缀的文件。

2019.10.18
作者：Chao.Song
版本：1.7
1.应薛工电话需求，防呆提醒的公差在0.01，超出此范围禁止输出;
2.实际铣边框使用公差0.005mm，靶孔数据使用公差0.002mm。

2019.11.01
作者：Chao.Song
版本：1.8
1.增加日志写入料号；
2.增加日志写入数据库，mysql，engineer， panel_rout_output_log。

2019.11.21
作者：Chao.Song
版本：1.9
1.inn设计为3个靶孔时，认为3靶设计，不做裁磨数据输出防呆，
由于此时MI有四靶数据，原来的判定条件下均为0，而更改规则后MI存在数据，判定就会报错。

2019.11.26
作者：Chao.Song
版本：2.0
1.判断当MI有四靶数据时，使用l2层的靶位设计进行数据判定。

2020.05.06
作者：Chao.Song
版本：2.1
1.inplan同步过来的拼版数据，保留的小数位数有7位，使得中心值使用保留四位小数判定失效，修复此问题
计算xcenter，ycenter保留8位小数；

2020.07.06
作者：Chao.Song
版本：Ver 2.2
http://192.168.2.120:82/zentao/story-view-1542.html
1.通孔板时，裁磨输出限制4靶数据输出(原规则为仅有三靶)；
2.HDI板通盲并存板序inn层设计3靶(原设计为4靶)；

2020.08.24
作者：Chao.Song
版本：Ver 2.3
http://192.168.2.120:82/zentao/story-view-1874.html
1.放行裁磨输出料号名及层数防呆

2020.10.22
作者：Chao.Song
版本：Ver 2.4
http://192.168.2.120:82/zentao/story-view-2222.html
1.仅有镭射层且非最外层，使用四靶;

2020.12.14
作者：Chao.Song
版本：Ver 2.5
http://192.168.2.120:82/zentao/story-view-2447.html
1.仅有一层镭射设计时为hdi板，修复Bug hdi_num > 1 --> hdi_num >= 1 ;


2021.01.08
作者：Chao.Song
版本：Ver 2.6
http://192.168.2.120:82/zentao/story-view-2530.html
1.工艺内联单要求变成，由本身的短边设计标靶，改为长边设计标靶，
程序更改，当三靶及四靶的y值不相同时，不进行两套标靶长边不同线检测。


2021.01.25
作者：Chao.Song
版本：Ver 2.7
http://192.168.2.120:82/zentao/story-view-2530.html
1.八靶及四靶输出支持

2021.02.24
作者：Chao.Song
版本：Ver 2.8
http://192.168.2.120:82/zentao/story-view-2530.html
1.iplan自2021.02.23切入8靶设计，程序更新，兼容旧订单的短边设计，但由打7靶改为打4靶;
2.应该为8靶设计但设计为4靶的，程序放行，但会提醒。

2021.03.15
作者：Chao.Song
版本：Ver 2.9
http://192.168.2.120:82/zentao/story-view-2530.html
1.更正一次压合的HDI靶孔数量判断错误问题。(应为8靶，判断为7靶)

2021.07.07
作者：Chao.Song
版本：Ver 3.0
1.Y方向靶位防呆放大到708;按《HDI对准度设计准则》5.5条目
http://ekp.shpcb.com/km/institution/km_institution_knowledge/kmInstitutionKnowledge.do?method=view&fdId=17075e5587f43140424dfbc43dd8012e

2021.08.12
作者：Chao.Song
版本：Ver 3.1
1.周涌钉钉需求——开料Y小于24.5inch，T靶在长边不给输出裁磨(新旧规则切换,满足此条件的目前在输出备用靶数据)
08.13
2.周涌电话要求，第一点防呆不管控LED板。
3.2021-10-22 经常接收CAM对于第n次压合坐标归类错误，应为3，实际为1类的问询，增加Tips：三靶设计需中间二靶中线靠右。

2021.11.17
作者：Chao.Song
版本：Ver 3.2
1.更改裁磨输出，使X,Y均防呆料号生效,相关料号：H69806PI327A1
2.全面废除7靶规则，不再兼容旧料号的七靶要求

2021.11.24
作者：Chao.Song
版本：Ver 3.3
1.增加禁止输出的放行,使用工程管理系统中的审核审批。http://192.168.2.120:82/zentao/story-view-3729.html
2.2022.02.10 更改提示文字，中间三靶其中右侧的两个靶要在整个拼版的中心线右侧。


2022.03.02
作者：Chao.Song
版本：Ver 3.4
1.增加最后一次压合TT靶数据输出；料号：575-179F2 http://192.168.2.120:82/zentao/story-view-4041.html


2022.07.21
作者：Chao.Song
版本：Ver 3.5
1.中锣料号的7靶输出。http://192.168.2.120:82/zentao/story-view-4428.html
2022.08.22 增加sql语句获取料号的流程是否有成型锣边
2022.12.08 板厚不作为输出7靶的判断条件,增加和成型锣边站的双重检测,仅提醒

2023.03.23
作者：Chao.Song
版本：Ver 3.6
1.增加裁磨输出8靶,对比inplan数据的防呆；

2024.01.08
作者：Nianhu.Yang
版本：Ver 3.7
更改选择模式，由MI流程获取http://192.168.2.120:82/zentao/story-view-6345.html
1.识别MI打靶信息，打4靶有一种靶位名称，打8靶有两种靶位名称。备注不合逻辑报出；
2.备注符合逻辑时检测资料是否设计对应靶位，符合设计直接输出，不符合报出异常；
3.报出异常时检测资料设计靶位情况，弹出提示框人工确认选择需输出的靶位类型。
