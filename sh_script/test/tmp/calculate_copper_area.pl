#!/perl/bin/perl -w
#################################################
#scripts:test by chris
#author: chris
#date:2016.03.24
#purpose:
#################################################
use lib "$ENV{SCRIPTS_DIR}/sys/scripts/Package";

use Tk;
use Tk::Tree;
use Genesis;
#use incam;
use VGT_Oracle;
use mainVgt;
use utf8;
use Encode;

# use encoding 'euc_cn';
use POSIX qw(strftime);
#use Win32::API;
$f = new Genesis();
our $o = new VGT_Oracle();
our $c = new mainVgt();
use JSON;

require Tk::LabFrame;
require Tk::LabEntry;
require Tk::NoteBook;
require Tk::Table;

use LWP::UserAgent;
use HTTP::Request::Common;  

#2019.11.18 唐成添加
#html访问对象
$ua = LWP::UserAgent->new;
$ua->agent("$0/0.1 " . $ua->agent);

#define genesis env:
my $app_Version = 'Ver:1.6';
my $job_name = $ENV{JOB};
my $step = $ENV{STEP};

#my $script_path = "$ENV{GENESIS_DIR}/sys/scripts/sh_script/calculate_copper_area";
#my $images_path = "$script_path/images";
use File::Basename;
my $images_path = (fileparse($0, qw/\.exe \.com \.pl \.Neo/))[1] . 'images';
unless ( -e $images_path ){
	$images_path = "$ENV{GENESIS_DIR}/sys/scripts/sh_script/calculate_copper_area/images";
}

unless (defined $ENV{GENESIS_TMP} ){
	$ENV{"GENESIS_TMP"} = $ENV{INCAM_TMP};
}

#judge the job and step if open:
unless($job_name){
	$f->PAUSE("The script must be run in a Job!!");
	exit(0);
}
$f->COM('get_user_name');
our $softuser = $f->{COMANS};

my $cmd="hostname";
our $ophost=`$cmd`;
print $ophost;
our $plat;
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



#open the job.
$f->COM("open_entity,job=$job_name,type=step,name=panel,iconic=no");
$f->AUX("set_group,group=$f->{COMANS}");

$f->COM("units,type=mm");

$f->DO_INFO("-t MATRIX -d ROW -e $job_name/matrix");
my $info_ref;
#our @all_layer = ();
our @fill_array;
our $signal_num = 0;
our @signal_list = ();
our @all_layers = @{$f->{doinfo}{gROWname}};
# === 获取信号层列表 ===
for(my $i=0 ; $i < @{$f->{doinfo}{gROWname}} ; $i++){
	$info_ref = { name       => @{$f->{doinfo}{gROWname}}[$i],
				  layer_type => @{$f->{doinfo}{gROWlayer_type}}[$i],
				  context    => @{$f->{doinfo}{gROWcontext}}[$i],
				  polarity   => @{$f->{doinfo}{gROWpolarity}}[$i],
				  side       => @{$f->{doinfo}{gROWside}}[$i],
				};

	if ($info_ref->{context} eq "board"){
		if ($info_ref->{layer_type} eq "signal" || $info_ref->{layer_type} eq "power_ground"){
			my $fill_hash = {"layer_check"       =>"1",
							 "layer_name" => "$info_ref->{name}",
							 };
			push(@fill_array, $fill_hash);
			$signal_num = $signal_num + 1;

			push(@signal_list, $info_ref->{name})
		}
	}
}

# === 2022.04.01 增加panel中的set数及set中pcs数获取 ===
# === 先判断panel是否存在，一般都存在===
# === 再判断set是否存在，没有set就用edit ===
# ===  set类和edit类都算 ===
my @array_in_panel = ();
my @edit_in_array = ();
my $set_in_panel = 'no';
$f->DO_INFO("-t step -e $job_name/panel -d EXISTS");
if ( $f->{doinfo}{gEXISTS} eq "yes" ) {
	$f->DO_INFO("-t step -e $job_name/panel -d REPEAT");
	my $gsteplist = $f->{doinfo}{gREPEATstep};
	foreach $i (@$gsteplist) {
		if ($i =~ /set|edit/) {
			push(@array_in_panel, $i);
			if ($i =~ /set/ ) {
				$set_in_panel = $i;
			}
			print $i . "\n";
		}
	}
}

if ($set_in_panel ne 'no') {
	$f->DO_INFO("-t step -e $job_name/$set_in_panel -d REPEAT");
	my $gsteplist = $f->{doinfo}{gREPEATstep};
	foreach $i (@$gsteplist) {
		if ($i =~ /edit/) {
			push(@edit_in_array, $i);
			print $i . "\n";
		}
	}	
}
# === 2023.03.06 Song 通孔和控深孔合并时，无drl层存在，判断是否有cdc或者cds存在
my $drl_layer = '';
my @drl_list = ('drl','cdc','cds');
foreach $cur_drl_layer (@drl_list) {
$f->DO_INFO("-t layer -e $job_name/panel/$cur_drl_layer -d EXISTS");
	if ( $f->{doinfo}{gEXISTS} eq "yes" ) {
		$drl_layer = $cur_drl_layer;
		last;
	}
}

our $count_copper = 1;
our $count_gold = 0;
our $copper_rate = 0;
my $board_thick;

# === 从inplan获取板厚 ===
$board_thick = &get_board_thickness;
# === 主界面 ===
#gui:
Start:
our $mw = MainWindow->new( -title =>" ");
$mw->bind('<Return>' => sub{ shift->focusNext; });
$mw->protocol("WM_DELETE_WINDOW", \&OnQuit);
#$f->PAUSE("$ophost"."1122");
if ($ophost =~ /hdilinux55/){
	
	$mw->geometry("500x680+320+200");
}else{
	if ($signal_num <= 4) {
		$mw->geometry("500x550+320+200");
	} else {
		$mw->geometry("500x580+320+200");
	}
}
#$mw->resizable(0,0);
$mw->update;
#Win32::API->new("user32","SetWindowPos",[qw(N N N N N N N)],'N')->Call(hex($mw->frame()),-1,0,0,0,0,3);
my $sh_log = $mw->Photo('info',-file => "$images_path/sh_log.xpm");
$mw->Photo('OpenJob',-file => "$images_path/OpenJob.xpm");
#script log:
my $CAM_frm = $mw->Frame(-bg => '#9BDBDB',-borderwidth =>2)->pack(-side=>'top',-fill=>'x');
my $image_label = $CAM_frm->Label(-image => $sh_log, -border => 1, -relief => 'solid',
                                              )->pack(-side => 'left',
                                                      -padx => 4,
                                                      -pady => 4);

$CAM_frm->Label(-text => '计算铜&化金面积',-font => 'charter 20 bold',-bg => '#9BDBDB')->pack();
$CAM_frm->Label(-text => "版权所有:胜宏科技",-font => 'charter 10',-bg => '#9BDBDB')->pack(-side=>'right', -padx => 10);

#add the menubutton:
##########################################################################################
my $menu_frm=$mw->Frame(-bg => '#9BDBDB',-borderwidth =>2,-relief => "raised")->pack(-side=>'top',-fill=>'both');
my $book = $menu_frm->NoteBook(-font=> 'charter 12 bold', -fg=>"blue")->pack( -fill=>'both', -expand=>'y');
my $tab1 = $book->add("Sheet 1", -label=>"计算铜&化金面积");
# my $tab2 = $book->add("Sheet 2", -label=>"显示结果",-state=>'disabled');
my $tab2 = $book->add("Sheet 2", -label=>"显示结果");
my $tab3 = $book->add("Sheet 3", -label=>"料号名:$job_name");
#show select gui.
our $select_frm = $tab1->LabFrame(-label =>'参数选择',
							     -borderwidth => 2,
							     -bg => '#9BDBDB',
							     -fg          => 'blue',
								 -height => '4000',
                                 -font => 'SimSun 10')->pack(-side=>'top',-fill=>'both');

my $show_check = $select_frm->Frame(-bg => '#9BDBDB',-borderwidth =>2)->pack(-side=>'top',-fill=>'both');
my $thick_board = $show_check->LabEntry(-label => '板厚(mm): ',
											 -labelBackground => '#9BDBDB',
											 -labelFont => 'SimSun 12',
											 -textvariable => \$board_thick,
											 -bg => 'white',
											 -width => 10,
											 -relief=>'ridge',
											 -state=>"normal",
											 -labelPack => [qw/-side left -anchor w/])->pack(-side => 'left', -padx => 5);

my $copper_rate1 = $show_check->Checkbutton(-text => "外层添加残铜率",-variable => \$copper_rate,-bg => '#9BDBDB',-font=> 'SimSun 15',-command=>sub{})->pack(-side => 'left', -padx => '40');

our $show_check1 = $select_frm->Frame(-bg => '#9BDBDB',-borderwidth =>2)->pack(-side=>'top',-fill=>'both');
our $show_check2 = $select_frm->Frame(-bg => '#9BDBDB',-borderwidth =>2)->pack(-side=>'top',-fill=>'both');
our $show_check3 = $select_frm->Frame(-bg => '#9BDBDB',-borderwidth =>2)->pack(-side=>'top',-fill=>'both');
# song edit tk show 201908014
my $add = $show_check2->Checkbutton(-text => "铜面积",-variable => \$count_copper,-bg => '#9BDBDB',-font=> 'SimSun 15',-command=>sub{&press_button})->pack(-side => 'left');
my $update = $show_check1->Checkbutton(-text => "化金面积",-variable => \$count_gold,-bg => '#9BDBDB',-font=> 'SimSun 15',-command=>sub{&add_label})->pack(-side => 'left');
my $update1 = $show_check3->Checkbutton(-text => "电镀金面积",-variable => \$count_elec,-bg => '#9BDBDB',-font=> 'SimSun 15',-command=>sub{&add_label2})->pack(-side => 'left');

our $show_list = $select_frm->Frame(-bg => '#9BDBDB',-borderwidth =>2)->pack(-side=>'top',-fill=>'both');
&table_fr;
#####
my $show_list_button = $show_list->Frame(-bg => '#9BDBDB',-borderwidth =>2)->pack(-side=>'right',-padx => 1);
my $select_button2 = $show_list_button->Button(-text => '反选',
									   -command => sub {&reverse_select},
									   -width => 10,
									   -activebackground=>'#387448',
									   -bg=>'#9BDBDB',
									   -font=> 'charter 10 bold',
									   -height=> 2
									   )->pack(-side =>'top', -padx => 10, -pady => 18);
my $select_button3 = $show_list_button->Button(-text => '选择All',
									   -command => sub {&select_all},
									   -width => 10,
									   -activebackground=>'#387448',
									   -bg=>'#9BDBDB',
									   -font=> 'charter 10 bold',
									   -height=> 2
									   )->pack(-side =>'top', -padx => 10, -pady => 18);
my $select_button4 = $show_list_button->Button(-text => '清除All',
									   -command => sub {&clear_all},
									   -width => 10,
									   -activebackground=>'#387448',
									   -bg=>'#9BDBDB',
									   -font=> 'charter 10 bold',
									   -height=> 2
									   )->pack(-side =>'top', -padx => 10, -pady => 18);

#$lb_layer->insert('end',@all_layer);
my $button_frm = $select_frm->Frame(-bg => '#9BDBDB',-borderwidth =>2)->pack(-fill=>'both', -side=>'top');
my $create_button = $button_frm->Button(-text => '执行',
									   -command => sub {&appy},
									   -width => 12,
									   -activebackground=>'#387448',
									   -bg=>'#9BDBDB',
									   -font=> 'charter 10 bold',
									   -height=> 3
									   )->pack(-side => 'left', -padx => 15, -pady => 6);

my $exit_button = $button_frm->Button(-text => '退出',
									  -command => sub {exit 0},
									  -width => 12,
									  -activebackground=>'#387448',
									  -bg=>'#9BDBDB',
									  -font=> 'charter 10 bold',
									  -height=> 3
									  )->pack(-side => 'right', -padx => 15, -pady => 6);
MainLoop;

sub OnQuit {
	my $ans = $mw->messageBox(-icon => 'question',-message => '你确定要退出吗？',-title => 'quit',-type => 'YesNo');
	return if $ans eq "No";
	exit;
}

sub clear_all {
	my @fill_array1 = ();
	foreach my $tmp (@fill_array) {
		my $fill_hash = {"layer_check"       =>"0",
						 "layer_name" => "$tmp->{layer_name}",
						};
		push(@fill_array1, $fill_hash);
	}
	our @fill_array = @fill_array1;
	$show_list_scroll->destroy();
	&table_fr;
}

sub select_all {
	my @fill_array1 = ();
	foreach my $tmp (@fill_array) {
		my $fill_hash = {"layer_check"       =>"1",
						 "layer_name" => "$tmp->{layer_name}",
						};
		push(@fill_array1, $fill_hash);
	}
	our @fill_array = @fill_array1;
	$show_list_scroll->destroy();
	&table_fr;
}

sub reverse_select {
	my @fill_array1 = ();
	foreach my $tmp (@fill_array) {
		if ($tmp->{layer_check} == 0) {
			our $fill_hash = {"layer_check"       =>"1",
							 "layer_name" => "$tmp->{layer_name}",
							};
		} else {
			our $fill_hash = {"layer_check"       =>"0",
							 "layer_name" => "$tmp->{layer_name}",
							};
		}
		push(@fill_array1, $fill_hash);
	}
	our @fill_array = @fill_array1;
	$show_list_scroll->destroy();
	&table_fr;
}

sub table_fr {
	our $show_list_scroll = $show_list->Frame(-bg => '#9BDBDB',-borderwidth =>2,)->pack(-side=>'left',-fill=>'both');
	my @col_headings = ("选择", "层名");
	my $colum = scalar(@col_headings);

	#my $table_frame = $mw->Frame()->pack();
	my $table_frame = $show_list_scroll->Frame(-relief => 'groove',
								               -bg => '#9BDBDB',
								               -bd => 2)->pack(-side => 'top',
																 -fill => 'both',
																 -expand => 'y',
																 -pady => 0);

	my $table = $table_frame->Table(-columns => $colum,
									-rows => 7,
									-bg => '#9BDBDB',
									-fixedrows => 1,
									-pady => 0,
									-scrollbars => 'oe',
									-relief => 'groove');


	my $n = 1;
	my $width;
	foreach my $col (@col_headings) {
		if ($n == 1) {
			$width = 8;
		} else {
			$width = 20;
		}
		my $title_button = $table->Button(-text => "$col",
										  -command => sub {},
										  -width => $width,
										  -activebackground=>'#9BDBDB',
										  -font=> 'charter 12',
										  -state=> "disabled",
										  -height=> 1
										  )->pack(-side => 'left',
												  -padx => 2);
		$table->put(0, $n, $title_button);
		$n++;
	}

	my $i = 1;
	foreach my $value (@fill_array) {
		#set the color.
		my $color;
		if ($i % 2 == 0) {
			$color = '#daac00';
		} else {
			$color = '#fcc64d';
		}
		#$f->PAUSE("$value->{layer_check}");
		our $first_col = $table->Checkbutton(-text => "",
											-variable => \$value->{layer_check},
											-background => "$color",
											-relief =>'groove',
											);
		$table->put($i, 1, $first_col);

		my $second_col = $table->Label(-text => "$value->{layer_name}", -width => 7, -height=>'2', -font => 'SimSun 12',-relief =>'groove',-background => "$color");

		$table->put($i, 2, $second_col);
		$i++;
	}
	$table->pack(-side=>"top", -fill=>'x');
}

sub appy {
	if ($board_thick >= 0.2 && $board_thick <= 4) {

	} else {
		$mw->Dialog(-title=>'Dialog',
					-text =>"输入板厚>=0.2且<=4,请检查",
					-default_button => 'Ok',
					-buttons => ['Ok'],
					-bitmap => 'error')->Show();
	goto Start
	}
	if ($board_thick eq "" || $count_gold == 0 && $count_copper == 0 && $count_elec == 0 ) {
		$mw->Dialog(-title=>'Dialog',
					-text =>"请选择参数....",
					-default_button => 'Ok',
					-buttons => ['Ok'],
					-bitmap => 'error')->Show();
		$mw->update;
	} else {
	      if ($count_gold == 1) {
               # 20241011 zl 判断是否有化金流程
               my $_exists = system('python /incam/server/site_data/scripts/sh_script/calculate_copper_area/check_flow.py 1');
               if ($_exists == 0){
                   $c->Messages('warning', '该料号没有化金流程');
                   return;
               }
		  }
		  if ($count_elec == 1) {
               # 20241011 zl 判断是否有镀金流程
               my $_exists = system('python /incam/server/site_data/scripts/sh_script/calculate_copper_area/check_flow.py 2');
               if ($_exists == 0){
                   $c->Messages('warning', '该料号没有电镀镍金流程');
                   return;
              }
		  }

		$board_thick1 = $board_thick * 1000;
		#删除临时层
		$f->DO_INFO("-t layer -e $job_name/panel/m1_calc_expose_tmp -d EXISTS");
		if($f->{doinfo}{gEXISTS} eq "yes"){
			$f->COM("delete_layer,layer=m1_calc_expose_tmp");
		}
		$f->DO_INFO("-t layer -e $job_name/panel/m2_calc_expose_tmp -d EXISTS");
		if($f->{doinfo}{gEXISTS} eq "yes"){
			$f->COM("delete_layer,layer=m2_calc_expose_tmp");
		}

		#先上传残铜率到数据库 hdi_engineering.incam_copper_usage 以供后续统计参考 20230307 by lyh
		#加入选化金面积计算去掉 osp区域 生成临时层 m1_calc_expose_tmp  m2_calc_expose_tmp 20230412 by lyh 暂时屏蔽掉 用户手动处理 20230420
		system("python /incam/server/site_data/scripts/sh_script/uploading_copper_usage/uploading_copper_usage.py");

		$f->DO_INFO("-t layer -e $job_name/panel/m1_calc_expose_tmp -d EXISTS");
		if($f->{doinfo}{gEXISTS} eq "yes"){
			$m1_value = "m1_calc_expose_tmp";
		}
		$f->DO_INFO("-t layer -e $job_name/panel/m2_calc_expose_tmp -d EXISTS");
		if($f->{doinfo}{gEXISTS} eq "yes"){
			$m2_value = "m2_calc_expose_tmp";
		}
		#calculate the gold area.
		our @gold_result1 = ();
		our @gold_result = ();
		our @pnl_gold_result1 = ();
		our @pnl_gold_result = ();
		our @gold_total_exposed = ();
		
		our @pnl_gold_total_exposed = ();
		
		our @elec_result1 = ();
		our @elec_result = ();
		our @elec_total_exposed = ();

		our @pnl_elec_result1 = ();
		our @pnl_elec_result = ();
		my $exposed_drill = "exposed_drill_tmp";		
		# === 化金 ===
		# === 以出货单元进行计算 ===
		if ($count_gold == 1) {
			$f->DO_INFO("-t step -e $job_name/set -d EXISTS");
			if ( $f->{doinfo}{gEXISTS} eq "yes" ) {
				$f->COM("open_entity,job=$job_name,type=step,name=set,iconic=no");
				$f->AUX("set_group,group=$f->{COMANS}");
				$f->COM("units,type=mm");
			} else {
				$f->COM("open_entity,job=$job_name,type=step,name=edit,iconic=no");
				$f->AUX("set_group,group=$f->{COMANS}");
				$f->COM("units,type=mm");
			}
			$f->VOF();
			$f->COM("delete_layer,layer=$exposed_drill");				
			$f->VON();
			$f->COM("flatten_layer,source_layer=$drl_layer,target_layer=$exposed_drill");
			# 将备份钻孔层变board属性
			$f->COM("matrix_layer_context,job=$job_name,matrix=matrix,layer=$exposed_drill,context=board");
			$f->COM("matrix_layer_type,job=$job_name,matrix=matrix,layer=$exposed_drill,type=drill");			
			# $f->COM("merge_layers,source_layer=$drl_layer,dest_layer=$exposed_drill,invert=no");	
			$f->COM("clear_layers");			
			$f->COM("display_layer,name=$exposed_drill,display=yes,number=1");	
			$f->COM('filter_reset,filter_name=popup');			
			foreach $lay (@all_layers) {
				if($lay eq "szsk-c.lp" || $lay eq "szsk-s.lp" || $lay eq "sz.lp"){	
					$f->VOF();
					$f->COM("delete_layer,layer=ref_sk_lp_tmp");
					$f->VON();
					$f->COM("flatten_layer,source_layer=$lay,target_layer=ref_sk_lp_tmp");	
					$f->COM("sel_ref_feat,layers=ref_sk_lp_tmp,use=filter,mode=touch,pads_as=shape,f_types=line\;pad\;surface\;arc\;text,polarity=positive\;negative,include_syms=,exclude_syms=");
					$f->COM("get_select_count");
					if ($f->{COMANS} != 0){
						$f->COM("sel_delete");
					}
					$f->VOF();
					$f->COM("delete_layer,layer=ref_sk_lp_tmp");
					$f->VON();
				}
			}	
			$f->COM("clear_layers");
			my %get_CN = getERPCopperhickness();
			
			# 加入表面积铜厚
			$f->COM("exposed_area,layer1=l1,mask1=$m1_value,layer2=l$signal_num,mask2=$m2_value,edges=no,copper_thickness=$get_CN{l1},drills=yes,consider_rout=no,drills_source=matrix,drills_list=$exposed_drill,thickness=$board_thick1,resolution_value=25.4,x_boxes=3,y_boxes=3,area=no,dist_map=yes,out_file=$ENV{GENESIS_TMP}/copper_result,out_layer=first");
			#get the parameter from job.
			my $layer_name;
			my $layer_result;
			my $layer_total_exposed;
			my $stat_file = "$ENV{GENESIS_TMP}/copper_result";
			my @thick_up = ();
			if (-e $stat_file) {
				open(STAT, $stat_file) or die "can't open file $stat_file: $!";
				while(<STAT>) {
					push(@thick_up, $_);
				}
				close(STAT);

				foreach $tmp (@thick_up) {
					if ($tmp ne "") {
						my @array1 = split(/:/, $tmp);
						my @array = ();
						foreach my $loop_tmp (@array1) {
							$loop_tmp=~s/ +$//;
							push(@array, $loop_tmp);
						}

						if ($array[0] eq "Layer") {
							$layer_name = "$array[1]";
						}
						if($array[0] eq "Total exposed"){
                            my @tempArray = split(" ",$array[1]);
                            $layer_total_exposed = $tempArray[0];
                        }
						if ($array[0] eq "Percentage") {
							$layer_result = "$array[1]";
							last;
						}
					}
				}
			}
			#$layer_name = sprintf ("%.f", $layer_name);
			$layer_result = sprintf ("%.1f", $layer_result);
			push(@gold_result1, "$layer_name");
			push(@gold_result, "$layer_result");
			push(@gold_total_exposed, "$layer_total_exposed");
			
			$f->COM("exposed_area,layer1=l1,mask1=$m1_value,layer2=l$signal_num,mask2=$m2_value,drills=yes,consider_rout=no,drills_source=matrix,drills_list=$exposed_drill,thickness=$board_thick1,resolution_value=25.4,x_boxes=3,y_boxes=3,area=no,dist_map=yes,out_file=$ENV{GENESIS_TMP}/copper_result,out_layer=second");
			#get the parameter from job.
			my $layer_name;
			my $layer_result;
			my $layer_total_exposed;
			my $stat_file = "$ENV{GENESIS_TMP}/copper_result";
			my @thick_up = ();
			if (-e $stat_file) {
				open(STAT, $stat_file) or die "can't open file $stat_file: $!";
				while(<STAT>) {
					push(@thick_up, $_);
				}
				close(STAT);

				foreach $tmp (@thick_up) {
					if ($tmp ne "") {
						my @array1 = split(/:/, $tmp);
						my @array = ();
						foreach my $loop_tmp (@array1) {
							$loop_tmp=~s/ +$//;
							push(@array, $loop_tmp);
						}

						if ($array[0] eq "Layer") {
							$layer_name = "$array[1]";
						}
						if($array[0] eq "Total exposed"){
                            my @tempArray = split(" ",$array[1]);
                            $layer_total_exposed = $tempArray[0];
                        }
						if ($array[0] eq "Percentage") {
							$layer_result = "$array[1]";
							last;
						}
					}
				}
			}
			#$layer_name = sprintf ("%.f", $layer_name);
			$layer_result = sprintf ("%.1f", $layer_result);
			push(@gold_result1, "$layer_name");
			push(@gold_result, "$layer_result");
			push(@gold_total_exposed, "$layer_total_exposed");

			$f->COM("editor_page_close");
			# 20190809 wangwu add panel gold area in hdi factory1
			
			$f->COM("open_entity,job=$job_name,type=step,name=panel,iconic=no");  
			$f->AUX("set_group,group=$f->{COMANS}");
			$f->COM("units,type=mm");
			
			$f->VOF();
			$f->COM("delete_layer,layer=$exposed_drill");				
			$f->VON();
			$f->COM("flatten_layer,source_layer=$drl_layer,target_layer=$exposed_drill");
			# 将备份钻孔层变board属性
			$f->COM("matrix_layer_context,job=$job_name,matrix=matrix,layer=$exposed_drill,context=board");
			$f->COM("matrix_layer_type,job=$job_name,matrix=matrix,layer=$exposed_drill,type=drill");			
			# $f->COM("merge_layers,source_layer=$drl_layer,dest_layer=$exposed_drill,invert=no");	
			$f->COM("clear_layers");			
			$f->COM("display_layer,name=$exposed_drill,display=yes,number=1");	
			$f->COM('filter_reset,filter_name=popup');			
			foreach $lay (@all_layers) {
				if($lay eq "szsk-c.lp" || $lay eq "szsk-s.lp" || $lay eq "sz.lp"){	
					$f->VOF();
					$f->COM("delete_layer,layer=ref_sk_lp_tmp");
					$f->VON();
					$f->COM("flatten_layer,source_layer=$lay,target_layer=ref_sk_lp_tmp");	
					$f->COM("sel_ref_feat,layers=ref_sk_lp_tmp,use=filter,mode=touch,pads_as=shape,f_types=line\;pad\;surface\;arc\;text,polarity=positive\;negative,include_syms=,exclude_syms=");
					$f->COM("get_select_count");
					if ($f->{COMANS} != 0){
						$f->COM("sel_delete");
					}
					$f->VOF();
					$f->COM("delete_layer,layer=ref_sk_lp_tmp");
					$f->VON();
				}
			}	
			$f->COM("clear_layers");
			
			&opt_pnl_outer_layer_copper("bak-to");			
		
			$f->COM("merge_layers,source_layer=$drl_layer,dest_layer=$exposed_drill,invert=no");			
			$f->COM("exposed_area,layer1=l1,mask1=$m1_value,layer2=l$signal_num,mask2=$m2_value,drills=yes,consider_rout=no,drills_source=matrix,drills_list=$exposed_drill,thickness=$board_thick1,resolution_value=25.4,x_boxes=3,y_boxes=3,area=no,dist_map=yes,out_file=$ENV{GENESIS_TMP}/copper_result,out_layer=first");
			#get the parameter from job.
			my $layer_name;
			my $layer_result;
			my $pnl_layer_total_exposed;
			my $stat_file = "$ENV{GENESIS_TMP}/copper_result";
			my @thick_up = ();
			if (-e $stat_file) {
				open(STAT, $stat_file) or die "can't open file $stat_file: $!";
				while(<STAT>) {
					push(@thick_up, $_);
				}
				close(STAT);

				foreach $tmp (@thick_up) {
					if ($tmp ne "") {
						my @array1 = split(/:/, $tmp);
						my @array = ();
						foreach my $loop_tmp (@array1) {
							$loop_tmp=~s/ +$//;
							push(@array, $loop_tmp);
						}

						if ($array[0] eq "Layer") {
							$layer_name = "$array[1]";
						}
						if ($array[0] eq "Total exposed"){
                            my @tempArray = split(" ",$array[1]);
                            $pnl_layer_total_exposed = sprintf ("%.1f", $tempArray[0]);
                        }
						if ($array[0] eq "Percentage") {
							$layer_result = "$array[1]";
							last;
						}
					}
				}
			}
			#$layer_name = sprintf ("%.f", $layer_name);
			$layer_result = sprintf ("%.1f", $layer_result);
			push(@pnl_gold_result1, "$layer_name");
			push(@pnl_gold_result, "$layer_result");
			push(@pnl_gold_total_exposed, "$pnl_layer_total_exposed");

			$f->COM("exposed_area,layer1=l1,mask1=$m1_value,layer2=l$signal_num,mask2=$m2_value,drills=yes,consider_rout=no,drills_source=matrix,drills_list=$exposed_drill,thickness=$board_thick1,resolution_value=25.4,x_boxes=3,y_boxes=3,area=no,dist_map=yes,out_file=$ENV{GENESIS_TMP}/copper_result,out_layer=second");
			#get the parameter from job.
			my $layer_name;
			my $layer_result;
			my $pnl_layer_total_exposed;
			my $stat_file = "$ENV{GENESIS_TMP}/copper_result";
			my @thick_up = ();
			if (-e $stat_file) {
				open(STAT, $stat_file) or die "can't open file $stat_file: $!";
				while(<STAT>) {
					push(@thick_up, $_);
				}
				close(STAT);

				foreach $tmp (@thick_up) {
					if ($tmp ne "") {
						my @array1 = split(/:/, $tmp);
						my @array = ();
						foreach my $loop_tmp (@array1) {
							$loop_tmp=~s/ +$//;
							push(@array, $loop_tmp);
						}

						if ($array[0] eq "Layer") {
							$layer_name = "$array[1]";
						}
						if ($array[0] eq "Total exposed"){
                            my @tempArray = split(" ",$array[1]);
                            $pnl_layer_total_exposed = sprintf ("%.1f", $tempArray[0]);
                        }
						if ($array[0] eq "Percentage") {
							$layer_result = "$array[1]";
							last;
						}
					}
				}
			}
			#$layer_name = sprintf ("%.f", $layer_name);
			$layer_result = sprintf ("%.1f", $layer_result);
			push(@pnl_gold_result1, "$layer_name");
			push(@pnl_gold_result, "$layer_result");
			push(@pnl_gold_total_exposed, "$pnl_layer_total_exposed");
			
			&opt_pnl_outer_layer_copper("bak-from");
			$f->VOF();
			$f->COM("delete_layer,layer=$exposed_drill");				
			$f->VON();			
			$f->COM("editor_page_close");
		}
		
		if ($count_elec == 1) {
            system ("python /incam/server/site_data/scripts/ynh/no_gui/PosGF.py");
		}
		
		# === 电金面积进行计算 ===
		# if ($count_elec == 1) {
			# #$f->DO_INFO("-t step -e $job_name/set -d EXISTS");
			# #if ( $f->{doinfo}{gEXISTS} eq "yes" ) {
			# #	$f->COM("open_entity,job=$job_name,type=step,name=set,iconic=no");
			# #	$f->AUX("set_group,group=$f->{COMANS}");
			# #	$f->COM("units,type=mm");
			# #} else {
				# # === 2020.09.15 镀金板计算pcs 
				# $f->COM("open_entity,job=$job_name,type=step,name=edit,iconic=no");
				# $f->AUX("set_group,group=$f->{COMANS}");
				# $f->COM("units,type=mm");
			# #}
			# #$f->COM("flatten_layer,source_layer=$gm1_value,target_layer=${gm1_value}-elec,suffix=,selective=no");
			# #$f->COM("flatten_layer,source_layer=$gm2_value,target_layer=${gm2_value}-elec,suffix=,selective=no");
			# $f->COM("flatten_layer,source_layer=$gm1_value,target_layer=${gm1_value}-elec");
			# $f->COM("flatten_layer,source_layer=$gm2_value,target_layer=${gm2_value}-elec");
			# $f->COM("display_layer,name=${gm1_value}-elec,display=yes");
			# $f->COM("display_layer,name=${gm2_value}-elec,display=yes");
			# $f->VOF();
			# $f->COM("display_sr,display=yes");
			# $f->VON();
			# $f->PAUSE("请删除无用的开窗，仅保留镀金位置");			
			
			# $f->COM("exposed_area,layer1=l1,mask1=${gm1_value}-elec,layer2=l$signal_num,mask2=${gm2_value}-elec,drills=yes,consider_rout=no,drills_source=matrix,drills_list=$drl_layer,thickness=$board_thick1,resolution_value=25.4,x_boxes=3,y_boxes=3,area=no,dist_map=yes,out_file=$ENV{GENESIS_TMP}/copper_result,out_layer=first");
			# #get the parameter from job.
			# my $layer_name;
			# my $layer_result;
			# my $layer_total_exposed;
			# my $stat_file = "$ENV{GENESIS_TMP}/copper_result";
			# my @thick_up = ();
			# if (-e $stat_file) {
				# open(STAT, $stat_file) or die "can't open file $stat_file: $!";
				# while(<STAT>) {
					# push(@thick_up, $_);
				# }
				# close(STAT);

				# foreach $tmp (@thick_up) {
					# if ($tmp ne "") {
						# my @array1 = split(/:/, $tmp);
						# my @array = ();
						# foreach my $loop_tmp (@array1) {
							# $loop_tmp=~s/ +$//;
							# push(@array, $loop_tmp);
						# }

						# if ($array[0] eq "Layer") {
							# $layer_name = "$array[1]";
						# }
						# if($array[0] eq "Total exposed"){
                            # my @tempArray = split(" ",$array[1]);
                            # $layer_total_exposed = $tempArray[0];
                        # }
						# if ($array[0] eq "Percentage") {
							# $layer_result = "$array[1]";
							# last;
						# }
					# }
				# }
			# }
			# #$layer_name = sprintf ("%.f", $layer_name);
			# $layer_result = sprintf ("%.1f", $layer_result);
			# push(@elec_result1, "$layer_name");
			# push(@elec_result, "$layer_result");
			# push(@elec_total_exposed,$layer_total_exposed);

			# $f->COM("exposed_area,layer1=l1,mask1=${gm1_value}-elec,layer2=l$signal_num,mask2=${gm2_value}-elec,drills=yes,consider_rout=no,drills_source=matrix,drills_list=$drl_layer,thickness=$board_thick1,resolution_value=25.4,x_boxes=3,y_boxes=3,area=no,dist_map=yes,out_file=$ENV{GENESIS_TMP}/copper_result,out_layer=second");
			# #get the parameter from job.
			# my $layer_name;
			# my $layer_result;
			# my $stat_file = "$ENV{GENESIS_TMP}/copper_result";
			# my @thick_up = ();
			# if (-e $stat_file) {
				# open(STAT, $stat_file) or die "can't open file $stat_file: $!";
				# while(<STAT>) {
					# push(@thick_up, $_);
				# }
				# close(STAT);

				# foreach $tmp (@thick_up) {
					# if ($tmp ne "") {
						# my @array1 = split(/:/, $tmp);
						# my @array = ();
						# foreach my $loop_tmp (@array1) {
							# $loop_tmp=~s/ +$//;
							# push(@array, $loop_tmp);
						# }
						# if ($array[0] eq "Layer") {
							# $layer_name = "$array[1]";
						# }
						# if($array[0] eq "Total exposed"){
                            # my @tempArray = split(" ",$array[1]);
                            # $layer_total_exposed = $tempArray[0];
                        # }
						# if ($array[0] eq "Percentage") {
							# $layer_result = "$array[1]";
							# last;
						# }
					# }
				# }
			# }
			# #$layer_name = sprintf ("%.f", $layer_name);
			# $layer_result = sprintf ("%.1f", $layer_result);
			# push(@elec_result1, "$layer_name");
			# push(@elec_total_exposed,$layer_total_exposed);
			# push(@elec_result, "$layer_result");
			
			# $f->COM("editor_page_close");
			# 20190809 wangwu add panel gold area in hdi factory1
			# 20200915 镀金面积取消panel的计算，仅计算pcs面积
			#$f->COM("open_entity,job=$job_name,type=step,name=panel,iconic=no");  
			#$f->AUX("set_group,group=$f->{COMANS}");
			#$f->COM("units,type=mm");
			#$f->COM("flatten_layer,source_layer=$gm1_value,target_layer=${gm1_value}-elec,suffix=,selective=no");
			#$f->COM("flatten_layer,source_layer=$gm2_value,target_layer=${gm2_value}-elec,suffix=,selective=no");
			#$f->COM("display_layer,name=${gm1_value}-elec,display=yes");
			#$f->COM("display_layer,name=${gm2_value}-elec,display=yes");
			#$f->PAUSE("请删除无用的开窗，仅保留镀金位置");
			#$f->COM("exposed_area,layer1=l1,mask1=${gm1_value}-elec,layer2=l$signal_num,mask2=${gm2_value}-elec,drills=yes,consider_rout=no,drills_source=matrix,drills_list=drl,thickness=$board_thick1,resolution_value=25.4,x_boxes=3,y_boxes=3,area=no,dist_map=yes,out_file=$ENV{GENESIS_TMP}/copper_result,out_layer=first");
			##get the parameter from job.
			#my $layer_name;
			#my $layer_result;
			#my $stat_file = "$ENV{GENESIS_TMP}/copper_result";
			#my @thick_up = ();
			#if (-e $stat_file) {
			#	open(STAT, $stat_file) or die "can't open file $stat_file: $!";
			#	while(<STAT>) {
			#		push(@thick_up, $_);
			#	}
			#	close(STAT);
			#
			#	foreach $tmp (@thick_up) {
			#		if ($tmp ne "") {
			#			my @array1 = split(/:/, $tmp);
			#			my @array = ();
			#			foreach my $loop_tmp (@array1) {
			#				$loop_tmp=~s/ +$//;
			#				push(@array, $loop_tmp);
			#			}
			#
			#			if ($array[0] eq "Layer") {
			#				$layer_name = "$array[1]";
			#			}
			#			if ($array[0] eq "Percentage") {
			#				$layer_result = "$array[1]";
			#				last;
			#			}
			#		}
			#	}
			#}
			##$layer_name = sprintf ("%.f", $layer_name);
			#$layer_result = sprintf ("%.1f", $layer_result);
			#push(@pnl_elec_result1, "$layer_name");
			#push(@pnl_elec_result, "$layer_result");
			#
			#$f->COM("exposed_area,layer1=l1,mask1=${gm1_value}-elec,layer2=l$signal_num,mask2=${gm2_value}-elec,drills=yes,consider_rout=no,drills_source=matrix,drills_list=drl,thickness=$board_thick1,resolution_value=25.4,x_boxes=3,y_boxes=3,area=no,dist_map=yes,out_file=$ENV{GENESIS_TMP}/copper_result,out_layer=second");
			##get the parameter from job.
			#my $layer_name;
			#my $layer_result;
			#my $stat_file = "$ENV{GENESIS_TMP}/copper_result";
			#my @thick_up = ();
			#if (-e $stat_file) {
			#	open(STAT, $stat_file) or die "can't open file $stat_file: $!";
			#	while(<STAT>) {
			#		push(@thick_up, $_);
			#	}
			#	close(STAT);
			#
			#	foreach $tmp (@thick_up) {
			#		if ($tmp ne "") {
			#			my @array1 = split(/:/, $tmp);
			#			my @array = ();
			#			foreach my $loop_tmp (@array1) {
			#				$loop_tmp=~s/ +$//;
			#				push(@array, $loop_tmp);
			#			}
			#
			#			if ($array[0] eq "Layer") {
			#				$layer_name = "$array[1]";
			#			}
			#			if ($array[0] eq "Percentage") {
			#				$layer_result = "$array[1]";
			#				last;
			#			}
			#		}
			#	}
			#}
			##$layer_name = sprintf ("%.f", $layer_name);
			#$layer_result = sprintf ("%.1f", $layer_result);
			#push(@pnl_elec_result1, "$layer_name");
			#push(@pnl_elec_result, "$layer_result");
			#$f->COM("editor_page_close");
		# }

		$f->COM("open_entity,job=$job_name,type=step,name=panel,iconic=no");  
		$f->AUX("set_group,group=$f->{COMANS}");
		$f->COM("units,type=mm");
		
		# === 计算铜面积，按panel计算 ===
		#calculate the copper area.
		our @copper_result1 = ();
		our @copper_result = ();
		our @total_copper_area = ();
		if ($count_copper == 1) {
			foreach my $value (@fill_array) {
				if ($value->{layer_check} == 1) {
					if ($value->{layer_name} eq "l1") {
						#create the outline.
						$f->DO_INFO("-t layer -e $job_name/panel/profile_outline -d EXISTS");
						if ( $f->{doinfo}{gEXISTS} eq "yes" ) {
							$f->COM("delete_layer,layer=profile_outline");
						}
						
						#create outline.
						$f->COM("create_layer,layer=profile_outline,context=misc,type=signal,polarity=positive,ins_layer=");	## by hyp, Jan 18, 2018
						$f->COM("profile_to_rout,layer=profile_outline,width=762");
						$f->COM("matrix_layer_type,job=$job_name,matrix=matrix,layer=profile_outline,type=document");

						#reset the  profile.
						our $set_profile = "no";
						my $tmp_lj_fd = substr($job_name, 4, 2);
						if ($tmp_lj_fd != 02) {
						$f->DO_INFO("-t layer -e $job_name/panel/pnl_rout -d EXISTS");
						if ( $f->{doinfo}{gEXISTS} eq "yes" ) {
							#filter the arc and set the profile.
							$f->COM("clear_layers");
							$f->COM("affected_layer,mode=all,affected=no");
							$f->COM("affected_layer,name=pnl_rout,mode=single,affected=yes");

							$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=pad\;surface\;arc\;text");
							$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=line\;pad\;surface\;arc\;text");
							$f->COM("filter_reset,filter_name=popup");
							$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=pad\;surface\;arc\;text");
							$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=surface\;arc\;text");
							$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=arc\;text");
							$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=arc");
							$f->COM("filter_set,filter_name=popup,update_popup=no,polarity=positive");
							$f->COM("filter_area_strt");
							$f->COM("filter_area_end,layer=,filter_name=popup,operation=select,area_type=none,inside_area=no,intersect_area=no,lines_only=no,ovals_only=no,min_len=0,max_len=0,min_angle=0,max_angle=0");
							if ($f->{COMANS} == 4) {
								$f->COM("sel_create_profile");
								$set_profile = "yes";
							}
							$f->COM("filter_reset,filter_name=popup");
						} else {
							my $tmp_rout_layer;
							$f->DO_INFO("-t layer -e $job_name/panel/pnl_rout4 -d EXISTS");
							if ( $f->{doinfo}{gEXISTS} eq "yes" ) {
								$tmp_rout_layer = "pnl_rout4";
							} else {
								$f->DO_INFO("-t layer -e $job_name/panel/pnl_rout3 -d EXISTS");
								if ( $f->{doinfo}{gEXISTS} eq "yes" ) {
									$tmp_rout_layer = "pnl_rout3";
								} else {
									$f->DO_INFO("-t layer -e $job_name/panel/pnl_rout2 -d EXISTS");
									if ( $f->{doinfo}{gEXISTS} eq "yes" ) {
										$tmp_rout_layer = "pnl_rout2";
									} else {
										$tmp_rout_layer = "pnl_rout1";
									}
								}
							}

							$f->COM("clear_layers");
							$f->COM("affected_layer,mode=all,affected=no");
							$f->COM("affected_layer,name=$tmp_rout_layer,mode=single,affected=yes");

							$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=pad\;surface\;arc\;text");
							$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=line\;pad\;surface\;arc\;text");
							$f->COM("filter_reset,filter_name=popup");
							$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=pad\;surface\;arc\;text");
							$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=surface\;arc\;text");
							$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=arc\;text");
							$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=arc");
							$f->COM("filter_set,filter_name=popup,update_popup=no,polarity=positive");
							$f->COM("filter_area_strt");
							$f->COM("filter_area_end,layer=,filter_name=popup,operation=select,area_type=none,inside_area=no,intersect_area=no,lines_only=no,ovals_only=no,min_len=0,max_len=0,min_angle=0,max_angle=0");
							if ($f->{COMANS} == 4) {
								$f->COM("sel_create_profile");
								$set_profile = "yes";
							}
							$f->COM("filter_reset,filter_name=popup");
						}
						}
						$f->COM("copper_area,layer1=l1,layer2=l$signal_num,drills=yes,consider_rout=no,ignore_pth_no_pad=yes,drills_source=matrix,drills_list=$drl_layer,thickness=$board_thick1,resolution_value=25.4,x_boxes=3,y_boxes=3,area=no,dist_map=yes,out_file=$ENV{GENESIS_TMP}/copper_result,out_layer=first");

						#get the parameter from job.
						my $layer_name;
						my $layer_result;
						my $layer_total_copper;
						my $stat_file = "$ENV{GENESIS_TMP}/copper_result";
						my @thick_up = ();
						if (-e $stat_file) {
						    open(STAT, $stat_file) or die "can't open file $stat_file: $!";
						    while(<STAT>) {
								push(@thick_up, $_);
						    }
						    close(STAT);

							foreach $tmp (@thick_up) {
								if ($tmp ne "") {
									my @array1 = split(/:/, $tmp);
									my @array = ();
									foreach my $loop_tmp (@array1) {
										$loop_tmp=~s/ +$//;
										push(@array, $loop_tmp);
									}

									if ($array[0] eq "Layer") {
										$layer_name = "$array[1]";
									}
									
									if ($array[0] eq  "Total copper"){
										my @tempArray = split(" ",$array[1]);
										$layer_total_copper =  sprintf ("%.3f", $tempArray[0]/92903.04);
									}
									
									if ($array[0] eq "Percentage") {
										$layer_result = "$array[1]";
										last;
									}
								}
							}
						}
						#$layer_name = sprintf ("%.f", $layer_name);
						$layer_result = sprintf ("%.f", $layer_result);
						push(@copper_result1, "$layer_name");
						push(@copper_result, "$layer_result");
						push(@total_copper_area, "$layer_total_copper");

						$f->COM("copper_area,layer1=l1,layer2=l$signal_num,drills=yes,consider_rout=no,ignore_pth_no_pad=yes,drills_source=matrix,drills_list=$drl_layer,thickness=$board_thick1,resolution_value=25.4,x_boxes=3,y_boxes=3,area=no,dist_map=yes,out_file=$ENV{GENESIS_TMP}/copper_result,out_layer=second");

						#get the parameter from job.
						my $layer_name;
						my $layer_result;
						my $stat_file = "$ENV{GENESIS_TMP}/copper_result";
						my @thick_up = ();
						if (-e $stat_file) {
							open(STAT, $stat_file) or die "can't open file $stat_file: $!";
							while(<STAT>) {
								push(@thick_up, $_);
							}
							close(STAT);

							foreach $tmp (@thick_up) {
								if ($tmp ne "") {
									my @array1 = split(/:/, $tmp);
									my @array = ();
									foreach my $loop_tmp (@array1) {
										$loop_tmp=~s/ +$//;
										push(@array, $loop_tmp);
									}

									if ($array[0] eq "Layer") {
										$layer_name = "$array[1]";
									}
									
									if ($array[0] eq  "Total copper"){
										my @tempArray = split(" ",$array[1]);
										$layer_total_copper = sprintf ("%.3f", $tempArray[0]/92903.04);
									}
									
									if ($array[0] eq "Percentage") {
										$layer_result = "$array[1]";
										last;
									}
								}
							}
						}
						#$layer_name = sprintf ("%.f", $layer_name);
						$layer_result = sprintf ("%.f", $layer_result);
						push(@copper_result1, "$layer_name");
						push(@copper_result, "$layer_result");
						push(@total_copper_area, "$layer_total_copper");

						#reset the profile.
						if ($set_profile eq "yes") {
							$f->COM("clear_layers");
							$f->COM("affected_layer,mode=all,affected=no");
							$f->COM("affected_layer,name=profile_outline,mode=single,affected=yes");

							$f->COM("filter_reset,filter_name=popup");
							$f->COM("filter_area_strt");
							$f->COM("filter_area_end,layer=,filter_name=popup,operation=select,area_type=none,inside_area=no,intersect_area=no,lines_only=no,ovals_only=no,min_len=0,max_len=0,min_angle=0,max_angle=0");
							if ($f->{COMANS} != 0) {
								$f->COM("sel_create_profile");
							}
							$f->COM("filter_reset,filter_name=popup");

							$f->COM("clear_layers");
							$f->COM("affected_layer,mode=all,affected=no");
						}
					} else {
						if ($value->{layer_name} ne "l$signal_num") {
							# === 2020.9.25 Song 除最外层的层别，不考虑钻孔 
							# $f->COM("copper_area,layer1=$value->{layer_name},layer2=,drills=yes,consider_rout=no,drills_source=matrix,thickness=$board_thick1,resolution_value=25.4,x_boxes=3,y_boxes=3,area=no,dist_map=yes,out_file=$ENV{GENESIS_TMP}/copper_result,out_layer=first");
							
							$f->COM("copper_area,layer1=$value->{layer_name},layer2=,drills=no,consider_rout=no,drills_source=matrix,resolution_value=25.4,x_boxes=3,y_boxes=3,area=no,dist_map=yes,out_file=$ENV{GENESIS_TMP}/copper_result,out_layer=first");

							#get the parameter from job.
							my $layer_name;
							my $layer_result;
							my $stat_file = "$ENV{GENESIS_TMP}/copper_result";
							my @thick_up = ();
							if (-e $stat_file) {
								open(STAT, $stat_file) or die "can't open file $stat_file: $!";
								while(<STAT>) {
									push(@thick_up, $_);
								}
								close(STAT);

								foreach $tmp (@thick_up) {
									if ($tmp ne "") {
										my @array1 = split(/:/, $tmp);
										my @array = ();
										foreach my $loop_tmp (@array1) {
											$loop_tmp=~s/ +$//;
											push(@array, $loop_tmp);
										}

										if ($array[0] eq "Layer") {
											$layer_name = "$array[1]";
										}
										if ($array[0] eq "Percentage") {
											$layer_result = "$array[1]";
											last;
										}
									}
								}
							}
							#$layer_name = sprintf ("%.f", $layer_name);
							$layer_result = sprintf ("%.f", $layer_result);
							push(@copper_result1, "$layer_name");
							push(@copper_result, "$layer_result");
						}
					}
				}

			}
		}
		
		#删除临时层
		$f->DO_INFO("-t layer -e $job_name/panel/m1_calc_expose_tmp -d EXISTS");
		if($f->{doinfo}{gEXISTS} eq "yes"){
			$f->COM("delete_layer,layer=m1_calc_expose_tmp");
		}
		$f->DO_INFO("-t layer -e $job_name/panel/m2_calc_expose_tmp -d EXISTS");
		if($f->{doinfo}{gEXISTS} eq "yes"){
			$f->COM("delete_layer,layer=m2_calc_expose_tmp");
		}
	
		$f->DO_INFO("-t layer -e $job_name/panel/sgt-c_calc_expose_tmp -d EXISTS");
		if($f->{doinfo}{gEXISTS} eq "yes"){
			$f->COM("delete_layer,layer=sgt-c_calc_expose_tmp");
		}
		$f->DO_INFO("-t layer -e $job_name/panel/sgt-s_calc_expose_tmp -d EXISTS");
		if($f->{doinfo}{gEXISTS} eq "yes"){
			$f->COM("delete_layer,layer=sgt-s_calc_expose_tmp");
		}
		
		$book->pageconfigure( "Sheet 2", -state=>'normal' );
		$book->raise("Sheet 2");
		#show the result.
		if ($table_frame1) {
			$table_frame1->destroy();
		}

		if ($table_frame2) {
			$table_frame2->destroy();
		}

		if ($exit_book) {
			$exit_book->destroy();
		}

		if ($count_gold == 1) {
			&show_gold_result;
		}

		if ($count_copper == 1) {
			&show_copper_result;
		}

        # if ( $count_elec == 1) {
            # &show_elec_result;
        # }

		#链接surface_and_gold_area 数据表，这里的操作步骤是将panel的沉金面积加入panel板边，然后再讲set后unit的沉金面积导入数据库  唐成 2019/11/11
		my @tc_joblist_list = ();
		
		
		my $dbname = "engineering";
		my $location = "192.168.2.19";
		my $port = "3306"; #这是mysql的缺省
		my $database = "DBI:mysql:$dbname:$location:$port";
		my $db_user = "root";
		my $db_pass = "k06931!";
		my $dbc_m_e = DBI->connect($database,$db_user,$db_pass);
		
		my $sql = "SELECT jobname FROM  surface_and_gold_area";
		my $sth = $dbc_m_e->prepare($sql);#结果保存在$sth中
		$sth->execute() or die "无法执行SQL语句:$dbc_m_e->errstr";

		while (my @recs=$sth->fetchrow_array) {
			push(@tc_joblist_list,"$recs[0]");
		}

		my $job_exists = 0;
		for my$jobname(@tc_joblist_list){
			if($jobname eq $job_name){
				$job_exists =1;
			}
		}		
	
		if ($count_gold == 1) {
			#增加金面积数据板边上 20230420 by lyh
			system("python /incam/server/site_data/scripts/sh_script/add_expose_area_in_pnl_edge/add_expose_area_in_pnl_edge.py $pnl_gold_total_exposed[0] $pnl_gold_total_exposed[1]");
			
			#output the parameter to txt file.
			my $user = $f->COM("get_user_name");
			my $current_date = strftime("%m/%d/%Y",localtime);
			my $current_time = strftime("%H:%M:%S",localtime);
			$job_name1 = uc($job_name);
			$job_name1 = "ARRAY_$job_name1";
			my $setup_file = "/windows/inplan/inplan/Gold/$job_name1.txt";
			
			# === 20230410 by lyh 增加数据库的写入，写入方式为直接insert
			# ====================================================== #
			#链接surface_and_gold_area 数据表，这里的操作步骤是将panel的沉金面积加入panel板边，然后再讲set后unit的沉金面积导入数据库  唐成 2019/11/11
			my $dbname = "engineering";
			my $location = "192.168.2.19";
			my $port = "3306"; #这是mysql的缺省
			my $database = "DBI:mysql:$dbname:$location:$port";
			my $db_user = "root";
			my $db_pass = "k06931!";
			my $dbh = DBI->connect($database,$db_user,$db_pass);

			#@elec_result1, "$layer_name"
			#@elec_total_exposed,$layer_total_exposed
			#@elec_result, "$layer_result"
			#如果有此档案号数据那么就更新，
			if($job_exists == 1){
				my $sql = "UPDATE surface_and_gold_area set au_cs_Mm2=?,au_cs_percent=?,au_ss_Mm2=?,au_ss_percent=? where jobname = ?";
				#$sql = "insert into surface_and_gold_area(jobname) values('$job_name')";
				#my$answer = $mw->messageBox(-title=>'信息',-message=>$sql,-type=>'YesNo',-icon=>'question',-default=>'yes');
				my $sth = $dbh->prepare($sql);#结果保存在$sth中
				$sth->execute($pnl_gold_total_exposed[0],$pnl_gold_result[0],$pnl_gold_total_exposed[1],$pnl_gold_result[1],$job_name) or die "无法执行SQL语句:$dbh->errstr";

			}elsif($job_exists == 0){
				my $sql = "insert into surface_and_gold_area(jobname,au_cs_Mm2,au_cs_percent,au_ss_Mm2,au_ss_percent,create_by) values(?,?,?,?,?,?)";
				my $sth = $dbh->prepare($sql);#结果保存在$sth中
				$sth->execute($job_name,$pnl_gold_total_exposed[0],$pnl_gold_result[0],$pnl_gold_total_exposed[1],$pnl_gold_result[1],"$softuser $ophost $plat") or die "无法执行SQL语句:$dbh->errstr";
				#$sth->execute() or die "无法执行SQL语句:$dbh->errstr";
			}
			$sth->finish;
			$dbh->disconnect; #断开数据库连接
			
			if (length($job_name) == 13){
				&send_to_erp_au_gold('tc_aac123',$pnl_gold_total_exposed[0],'tc_aac124',$pnl_gold_result[0]);
				&send_to_erp_au_gold('tc_aac125',$pnl_gold_total_exposed[1],'tc_aac126',$pnl_gold_result[1]);				
				
			}
			# ====================================================== #
			
			if ( -d "/windows/inplan/inplan/Gold" )
			{
				if ( -f "$setup_file" ) {
					unlink("$setup_file");
				}
				if ( open(SESAME,">$setup_file") or die("$!")) {
					print SESAME "Date: $current_date Time: $current_time User: $user\n";
					print SESAME "Panel Gold Area of $job_name\n";
					print SESAME "Layer Gold Unit(%)\n";
					my $m = 0;
					foreach my $tmp (@gold_result1) {
						chomp($gold_result[$m]);
						chomp($gold_result1[$m]);
						chomp($pnl_gold_result[$m]);
						chomp($pnl_gold_result1[$m]);
						# Add a column panel gold percent
						print SESAME "$gold_result1[$m] $gold_result[$m] $pnl_gold_result[$m]\n";
						$m = $m + 1;
					}
					
					close (SESAME);
				}				
			} else {
				$f->PAUSE("/windows/inplan/inplan/Gold 路径不存在，请通知系统管理员解决.");
			}
			
		}
		
		my $sql = "SELECT jobname FROM  surface_and_gold_area";
		my $sth = $dbc_m_e->prepare($sql);#结果保存在$sth中
		$sth->execute() or die "无法执行SQL语句:$dbc_m_e->errstr";

		while (my @recs=$sth->fetchrow_array) {
			push(@tc_joblist_list,"$recs[0]");
		}

		my $job_exists = 0;
		for my$jobname(@tc_joblist_list){
			if($jobname eq $job_name){
				$job_exists =1;
			}
		}
		
		$sth->finish;
		$dbc_m_e->disconnect; #断开数据库连接		
		
		our $exit_book = $tab2->Button(-text => '退出',
									  -command => sub {exit 0},
									  -width => 12,
									  -activebackground=>'#387448',
									  -bg=>'#9BDBDB',
									  -font=> 'charter 10 bold',
									  -height=> 3
									  )->pack(-side => 'bottom', -padx => 15, -pady => 6);
	}
}


#2019.11.18 唐成添加
#访问html 提交数据到erp
#提交数据的时候要分化金和镀金，化金要提供百分比，镀金不用以后百分比。
sub send_to_erp_au_gold{

    my $au_data_table = shift;
    my $au_data = shift;
    my $au_percent_table = shift;
    my $au_percent = shift;

     #测试字符拼接，
     #119 镀金C面,面积
     #120 镀金S面,面积
     #123 化金C面,面积， 124化金C面,百分比
     #125 化金S面,面积， 126化金S面,百分比

    #            GET => 'http://192.168.2.23:9091/erp/service/?logino=mi_to_erp&password=mi_to_erp123&service=cimi110_prod&json=
    #    {
    #      "head": {
    #        "debug": 1,
    #        "table": "tc_aac_file",
    #        "col": 7,
    #        "row": 1
    #      },
    #      "body": [{
    #        "tc_aac01": "H22802PN015A2",
    #        "tc_aac119": "2.3",  #
    #        "tc_aac120": "2.4",
    #        "tc_aac123": "2.5",
    #        "tc_aac124": "2.6",
    #        "tc_aac125": "2.7",
    #        "tc_aac126": "2.95"
    #      }]
    #    }');


    #http 请求说明
    #1：debug 1表示测试，0表示将数据放到正式的erp数据库
    #2：如果传送的数据不一样，需要对列col的数据进行更改，几列数据就将值改成几。
    # my $url = 'http://192.168.2.23:9091/erp/service/?logino=mi_to_erp&password=mi_to_erp123&service=cimi110_prod&json=
    # my $url = 'http://192.168.2.13:9090/api/erp/service/?logino=mi_to_erp&password=mi_to_erp123&service=cimi110_prod&json=
        # {
          # "head": {
            # "debug": 0,
            # "table": "tc_aac_file",
            # "col": 3,
            # "row": 1
          # },
          # "body": [{
            # "tc_aac01": "'.uc($job_name).'",
            # "'.$au_data_table.'": "'.$au_data.'",
            # "'.$au_percent_table.'": "'.$au_percent.'"
          # }]
        # }';
    # $req = HTTP::Request->new(GET => $url);
    # $req->header('Accept' => 'text/html');

     # # send request
     # $res = $ua->request($req);
     # my $send_result = $res->decoded_content;
	 
	 # 参考多层更新接口 20241029  ynh
	 ###2024 08 20 更改erp上传接口 ，接口由谢文宝提供 
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
        #print "请求成功！\n";  
        # 打印响应体  
        my $string = encode('UTF-8', $response->decoded_content);
        my $data= decode_json($string);
        if($data->{code} != 200){
            $mw->messageBox(-title=>'信息',-message=>"erp获取令牌失败！上传erp失败,",-type=>'YesNo',-icon=>'question',-default=>'yes');
            return 0;
        }
        $token= $data->{data};  
    } else {  
        $mw->messageBox(-title=>'信息',-message=>"erp获取令牌失败！上传erp失败,",-type=>'YesNo',-icon=>'question',-default=>'yes');
        return 0;
    }
    
    
    
    my $job=uc($job_name);
    my $postjson=qq(
    { 	
        "ApiType": "ERPInterFace", 	
        "Method": "ChangeMI", 	
        "From": "CAM", 	
        "TO": "ERP", 	
        "Data": [ 		
            { 			
                "tc_aac01": "$job", 			
                "$au_data_table": "$au_data" ,
                "$au_percent_table":"$au_percent"
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
            $mw->messageBox(-title=>'信息',-message=>"erp上传面积失败,",-type=>'YesNo',-icon=>'question',-default=>'yes');
            return 0;
        }
		else{
			$mw->messageBox(-title=>'信息',-message=>"沉金数据提交交到erp成功",-type=>'YesNo',-icon=>'question',-default=>'yes');
		}
    } else {  
        $mw->messageBox(-title=>'信息',-message=>"erp上传面积失败,",-type=>'YesNo',-icon=>'question',-default=>'yes');
        return 0;
        
    }
     # if($send_result =~ /success/){
        # #成功不提示，调试用
        # #$mw->messageBox(-title=>'信息',-message=>"沉金数据提交交到erp成功",-type=>'YesNo',-icon=>'question',-default=>'yes');
     # }else{
        # $mw->messageBox(-title=>'信息',-message=>"无法连接到erp数据库,沉金数据提交到erp失败,",-type=>'YesNo',-icon=>'question',-default=>'yes');
     # }

}


sub opt_pnl_outer_layer_copper {
	#http://192.168.2.120:82/zentao/story-view-5009.html
	#优化下化金 跟电金面积计算时 先将pnl外层的铜皮去掉 计算完后在还原回来 20221230 by lyh
	#周涌通知 只要识别铜皮即可 不用加pattern_fill属性
	my $run_type=shift;	
	my @outer_signal_layers = ("l1","l$signal_num");
	if ($run_type eq 'bak-to'){
		foreach my $work_lay (@outer_signal_layers) {
			$f->COM("copy_layer,source_job=$job_name,source_step=panel,source_layer=$work_lay,dest=layer_name,dest_step=,dest_layer=${work_lay}_calc_expose_area_bf,mode=replace,invert=no,copy_notes=no,copy_attrs=no,copy_lpd=new_layers_only,copy_sr_feat=no");
			$f->COM("display_layer,name=$work_lay,display=yes");
			$f->COM("work_layer,name=$work_lay");
			$f->COM("filter_reset,filter_name=popup");
			$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=surface");
			#$f->COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.pattern_fill,text=");
			$f->COM("filter_area_strt");
			$f->COM("filter_area_end,layer=,filter_name=popup,operation=select,area_type=none,inside_area=no,intersect_area=no");
			$f->COM("get_select_count");
			if ( $f->{COMANS} > 0 ){
				$f->COM('sel_delete');
			}
		}
	}elsif($run_type eq 'bak-from'){
		foreach my $work_lay (@outer_signal_layers) {
			$f->COM("copy_layer,source_job=$job_name,source_step=panel,source_layer=${work_lay}_calc_expose_area_bf,dest=layer_name,dest_step=,dest_layer=$work_lay,mode=replace,invert=no,copy_notes=no,copy_attrs=no,copy_lpd=new_layers_only,copy_sr_feat=no");
		}
	}	
}

sub show_gold_result {
	my @col_headings = ("层名", "百分比%/面积(mm2)", "层名", "百分比%/面积(mm2)");
	my $colum = scalar(@col_headings);

	our $table_frame1 = $tab2->Frame(-relief => 'groove',
								   -bg => '#9BDBDB',
								   -bd => 2)->pack(-side => 'top',
												   -fill => 'both',
												   -padx => 1,
												   -pady => 0);

	my $table = $table_frame1->Table(-columns => $colum,
									-rows => 3,
									-fixedrows => 1,
									-scrollbars => 'oe',
									-relief => 'groove');

	my $n = 1;
	my $width;
	foreach my $col (@col_headings) {
		if ($n == 1 || $n == 3) {
			$width = 6;
		} else {
			$width = 15;
		}
		my $title_button = $table->Button(-text => "$col",
										  -command => sub {},
										  -width => $width,
										  -activebackground=>'#9BDBDB',
										  -font=> 'charter 12',
										  -state=> "normal",
										  -height=> 1
										  )->pack(-side => 'left',
												  -padx => 2);
		$table->put(0, $n, $title_button);
		$n++;
	}

    my $i = 1;
    my $first_col = $table->Label(-text => "$gold_result1[$i-1]", -width => 7, -height=>'2', -font => 'SimSun 12',-relief =>'groove',-background => "#daac00");
    $table->put($i, 1, $first_col);
    my $second_col = $table->Label(-text => "$gold_result[$i-1]/$gold_total_exposed[$i-1]", -width => 7, -height=>'2', -font => 'SimSun 12',-relief =>'groove',-background => "#fcc64d");
    $table->put($i, 2, $second_col);
    my $three_col = $table->Label(-text => "$gold_result1[$i]", -width => 7, -height=>'2', -font => 'SimSun 12',-relief =>'groove',-background => "#daac00");
    $table->put($i, 3, $three_col);
    my $four_col = $table->Label(-text => "$gold_result[$i]/$gold_total_exposed[$i]", -width => 7, -height=>'2', -font => 'SimSun 12',-relief =>'groove',-background => "#fcc64d");
    $table->put($i, 4, $four_col);
	
    $i = 1;
    $m = 2;
    $first_col = $table->Label(-text => "pnl $pnl_gold_result1[$i-1]", -width => 7, -height=>'2', -font => 'SimSun 12',-relief =>'groove',-background => "#daac00");
    $table->put($m, 1, $first_col);
    $second_col = $table->Label(-text => "$pnl_gold_result[$i-1]/$pnl_gold_total_exposed[$i-1]", -width => 7, -height=>'2', -font => 'SimSun 12',-relief =>'groove',-background => "#fcc64d");
    $table->put($m, 2, $second_col);
    $three_col = $table->Label(-text => "pnl $pnl_gold_result1[$i]", -width => 7, -height=>'2', -font => 'SimSun 12',-relief =>'groove',-background => "#daac00");
    $table->put($m, 3, $three_col);
    $four_col = $table->Label(-text => "$pnl_gold_result[$i]/$pnl_gold_total_exposed[$i]", -width => 7, -height=>'2', -font => 'SimSun 12',-relief =>'groove',-background => "#fcc64d");
    $table->put($m, 4, $four_col);	
    $table->pack(-side=>"top", -fill=>'x');
}

sub show_elec_result {
	my @col_headings = ("层名", "镀金面积%", "层名", "镀金面积%");
	my $colum = scalar(@col_headings);

	our $table_frame1 = $tab2->Frame(-relief => 'groove',
								   -bg => '#9BDBDB',
								   -bd => 2)->pack(-side => 'top',
												   -fill => 'both',
												   -padx => 1,
												   -pady => 0);

	my $table = $table_frame1->Table(-columns => $colum,
									-rows => 3,
									-fixedrows => 1,
									-scrollbars => 'oe',
									-relief => 'groove');

	my $n = 1;
	my $width;
	foreach my $col (@col_headings) {
		if ($n == 1 || $n == 3) {
			$width = 6;
		} else {
			$width = 15;
		}
		my $title_button = $table->Button(-text => "$col",
										  -command => sub {},
										  -width => $width,
										  -activebackground=>'#9BDBDB',
										  -font=> 'charter 12',
										  -state=> "normal",
										  -height=> 1
										  )->pack(-side => 'left',
												  -padx => 2);
		$table->put(0, $n, $title_button);
		$n++;
	}

    my $i = 1;
    my $first_col = $table->Label(-text => "$elec_result1[$i-1]", -width => 7, -height=>'2', -font => 'SimSun 12',-relief =>'groove',-background => "#daac00");
    $table->put($i, 1, $first_col);
    my $second_col = $table->Label(-text => "$elec_result[$i-1]", -width => 7, -height=>'2', -font => 'SimSun 12',-relief =>'groove',-background => "#fcc64d");
    $table->put($i, 2, $second_col);
    my $three_col = $table->Label(-text => "$elec_result1[$i]", -width => 7, -height=>'2', -font => 'SimSun 12',-relief =>'groove',-background => "#daac00");
    $table->put($i, 3, $three_col);
    my $four_col = $table->Label(-text => "$elec_result[$i]", -width => 7, -height=>'2', -font => 'SimSun 12',-relief =>'groove',-background => "#fcc64d");
    $table->put($i, 4, $four_col);
	
    #$i = 1;
    #$m = 2;
    #$first_col = $table->Label(-text => "pnl $pnl_elec_result1[$i-1]", -width => 7, -height=>'2', -font => 'SimSun 12',-relief =>'groove',-background => "#daac00");
    #$table->put($m, 1, $first_col);
    #$second_col = $table->Label(-text => "$pnl_elec_result[$i-1]", -width => 7, -height=>'2', -font => 'SimSun 12',-relief =>'groove',-background => "#fcc64d");
    #$table->put($m, 2, $second_col);
    #$three_col = $table->Label(-text => "pnl $pnl_elec_result1[$i]", -width => 7, -height=>'2', -font => 'SimSun 12',-relief =>'groove',-background => "#daac00");
    #$table->put($m, 3, $three_col);
    #$four_col = $table->Label(-text => "$pnl_elec_result[$i]", -width => 7, -height=>'2', -font => 'SimSun 12',-relief =>'groove',-background => "#fcc64d");
    #$table->put($m, 4, $four_col);	
    $table->pack(-side=>"top", -fill=>'x');
}



sub show_copper_result {
	#if ($table_frame2) {
	#	$table_frame2->destroy();
	#}
	#if ($count_gold == 0) {
	#	if ($table_frame1) {
	#		$table_frame1->destroy();
	#	}
	#}

	#if ($table_frame1) {
	#	$table_frame1->destroy();
	#}
	#if ($exit_book) {
	#	$exit_book->destroy();
	#}
	my $tmp_row = scalar(@copper_result) * 0.5;
	$tmp_row = int($tmp_row) + 1;
	my @col_headings = ("层名", "铜面积%", "层名", "铜面积%");
	my $colum = scalar(@col_headings);

	our $table_frame2 = $tab2->Frame(-relief => 'groove',
								   -bg => '#9BDBDB',
								   -bd => 2)->pack(-side => 'top',
												   -fill => 'both',
												   -expand => 'y',
												   -padx => 1,
												   -pady => 2);

	my $table = $table_frame2->Table(-columns => $colum,
									-rows => $tmp_row,
									-fixedrows => 1,
									-scrollbars => 'oe',
									-relief => 'groove');


	my $n = 1;
	my $width;
	foreach my $col (@col_headings) {
		if ($n % 2 != 0) {
			$width = 6;
		} else {
			$width = 15;
		}
		my $title_button = $table->Button(-text => "$col",
										  -command => sub {},
										  -width => $width,
										  -activebackground=>'#9BDBDB',
										  -font=> 'charter 12',
										  -state=> "normal",
										  -height=> 1
										  )->pack(-side => 'left',
												  -padx => 2);
		$table->put(0, $n, $title_button);
		$n++;
	}

	my $i = 1;
	my $n = 1;
	foreach my $value (@copper_result) {
		if ($i % 2 != 0) {
			my $first_col = $table->Label(-text => "$copper_result1[$i-1]", -width => 7, -height=>'2', -font => 'SimSun 12',-relief =>'groove',-background => "#daac00");

			$table->put($n, 1, $first_col);

			my $second_col = $table->Label(-text => "$copper_result[$i-1]", -width => 7, -height=>'2', -font => 'SimSun 12',-relief =>'groove',-background => "#fcc64d");

			$table->put($n, 2, $second_col);

			my $three_col = $table->Label(-text => "$copper_result1[$i]", -width => 7, -height=>'2', -font => 'SimSun 12',-relief =>'groove',-background => "#daac00");

			$table->put($n, 3, $three_col);

			my $four_col = $table->Label(-text => "$copper_result[$i]", -width => 7, -height=>'2', -font => 'SimSun 12',-relief =>'groove',-background => "#fcc64d");

			$table->put($n, 4, $four_col);
			$n++;
		}
		$i++;
	}
	$table->pack(-side=>"top", -fill=>'x');
	#output the parameter to txt file.
	my $user = $f->COM("get_user_name");
	my $current_date = strftime("%m/%d/%Y",localtime);
	my $current_time = strftime("%H:%M:%S",localtime);
	$job_name1 = uc($job_name);
	
	my $setup_file = "/windows/inplan/inplan/Copper_Exposed_Area/$job_name1.txt";
	if ( ! -d "/windows/inplan/inplan/Copper_Exposed_Area" )
	{
		$f->PAUSE("/windows/inplan/inplan/Copper_Exposed_Area 路径不存在，请通知管理员解决.")
	} else {
		unlink("$setup_file") if ( -f "$setup_file" );
		my $array_num = @array_in_panel;
		my $edit_num = @edit_in_array;
		
		if ( open(SESAME,">$setup_file") or die("$!"))
		{
			print SESAME "Date: $current_date Time: $current_time User: $user\n";
			print SESAME "array_in_panel:$array_num\n";
			print SESAME "edit_in_array:$edit_num\n";
			print SESAME "Panel copper Exposed Area of $job_name\n";
			print SESAME "Layer Usage Unit(%)\n";
			my $m = 0;
			foreach my $tmp (@copper_result) {
				chomp($tmp);
				chomp($copper_result1[$m]);
				print SESAME "$copper_result1[$m] $tmp % \n";
				$m = $m + 1;
			}
			close (SESAME);
		}		
	}

	my $have_copper_rate = "no";
	
	#先删除旧symbol 及text 20230414 by lyh
	$f->COM("clear_layers");
	$f->COM("affected_layer,mode=all,affected=no");
	$f->COM("affected_layer,name=$copper_result1[0],mode=single,affected=yes");
	$f->COM("affected_layer,name=$copper_result1[1],mode=single,affected=yes");
	$f->COM("filter_reset,filter_name=popup");
	$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=pad");
	$f->COM("filter_set,filter_name=popup,update_popup=no,include_syms=chris-tudian");
	$f->COM("filter_area_strt");
	$f->COM("filter_area_end,layer=,filter_name=popup,operation=select,area_type=none,inside_area=no,intersect_area=no");
	if ($f->{COMANS} > 0) {
		$f->COM("filter_reset,filter_name=popup");
		$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=pad");
		$f->COM("filter_set,filter_name=popup,update_popup=no,include_syms=chris-tudian");
		$f->COM("filter_area_strt");
		$f->COM("filter_area_end,layer=,filter_name=popup,operation=select,area_type=none,inside_area=no,intersect_area=no");
		if ($f->{COMANS} > 0) {
			$f->COM('sel_delete');
		}
		$f->COM("filter_reset,filter_name=popup");
		$f->COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.area_name,text=copper_rate");
		$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=text");
		$f->COM("filter_set,filter_name=popup,update_popup=no,polarity=negative");
		$f->COM("filter_area_strt");
		$f->COM("filter_area_end,layer=,filter_name=popup,operation=select,area_type=none,inside_area=no,intersect_area=no");
		if ($f->{COMANS} > 0) {
			$f->COM('sel_delete');
		}
	}
	
	$f->COM("clear_layers");
	$f->COM("affected_layer,mode=all,affected=no");
	$f->COM("affected_layer,name=l1,mode=single,affected=yes");
	$f->COM("filter_reset,filter_name=popup");
	$f->COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.area_name,text=copper_rate");
	$f->COM("filter_area_strt");
	$f->COM("filter_area_end,layer=,filter_name=popup,operation=select,area_type=none,inside_area=no,intersect_area=no");
	if ($f->{COMANS} != 0) {
		$have_copper_rate = "yes";
	}
	$f->COM("filter_reset,filter_name=popup");
	
	$f->COM("clear_layers");
	$f->COM("affected_layer,mode=all,affected=no");
	if ($copper_rate == 1 && $have_copper_rate eq "no") {
		#用新的chris-tudian2 添加图电面积 及百分比 20230413 by lyh
		system("python /incam/server/site_data/scripts/sh_script/add_tu_dian_copper_area_pnl_edge/add_tu_dian_copper_area_pnl_edge.py $copper_result[0] $copper_result[1] $total_copper_area[0] $total_copper_area[1]");
	#if ($copper_rate == 1) {
		#将结果加到panel板边.
=head
		our $sr_xmin = 100000000;
		our $sr_xmax = 0;
		our $sr_ymin = 100000000;
		our $sr_ymax = 0;
		#get the panel SR size.
		$f->INFO(units => 'mm', entity_type => 'step',
			 entity_path => "$job_name/panel",
			 data_type => 'SR');

		for(my $i=0 ; $i < @{$f->{doinfo}{gSRstep}} ; $i++){
			if (@{$f->{doinfo}{gSRstep}}[$i] =~ /^set[0-9]$/ || @{$f->{doinfo}{gSRstep}}[$i] =~ /^edit[0-9]$/ || @{$f->{doinfo}{gSRstep}}[$i] =~ /^edit[-+]f*/ || @{$f->{doinfo}{gSRstep}}[$i] =~ /^set-f*/ || @{$f->{doinfo}{gSRstep}}[$i] eq "set" || @{$f->{doinfo}{gSRstep}}[$i] eq "edit" || @{$f->{doinfo}{gSRstep}}[$i] =~ /^zk[0-9]?/ || @{$f->{doinfo}{gSRstep}}[$i] eq "2nd" || @{$f->{doinfo}{gSRstep}}[$i] eq "drl" || @{$f->{doinfo}{gSRstep}}[$i] eq "lp") {
				if ($sr_xmin > @{$f->{doinfo}{gSRxmin}}[$i]) {
					$sr_xmin = @{$f->{doinfo}{gSRxmin}}[$i];
				}

				if ($sr_xmax < @{$f->{doinfo}{gSRxmax}}[$i]) {
					$sr_xmax = @{$f->{doinfo}{gSRxmax}}[$i];
				}

				if ($sr_ymin > @{$f->{doinfo}{gSRymin}}[$i]) {
					$sr_ymin = @{$f->{doinfo}{gSRymin}}[$i];
				}

				if ($sr_ymax < @{$f->{doinfo}{gSRymax}}[$i]) {
					$sr_ymax = @{$f->{doinfo}{gSRymax}}[$i];
				}
			}
		}
		
		#添加短边的残铜率.
		# modified by song 2021.01.18 change symbol copper_rate to chris-tudian
		#my $cu_rate_sym = 'copper_rate';
		my $cu_rate_sym = 'chris-tudian';
		my $add_symbol_x = $sr_xmax - 100;
		my $add_symbol_y = $sr_ymax + 5.65;
		$f->COM("clear_layers");
		$f->COM("affected_layer,mode=all,affected=no");
		$f->COM("affected_layer,name=$copper_result1[0],mode=single,affected=yes");
		
		$f->COM("add_pad,attributes=no,x=$add_symbol_x,y=$add_symbol_y,symbol=$cu_rate_sym,polarity=positive,angle=0,mirror=no,nx=1,ny=1,dx=0,dy=0,xscale=1,yscale=1");
		
		$add_symbol_x = $add_symbol_x + 2;
		$add_symbol_y = $add_symbol_y - 0.92;
		
		$f->COM("cur_atr_reset");
		$f->COM("cur_atr_set,attribute=.area_name,text=copper_rate");
		$f->COM("add_text,attributes=yes,type=string,x=$add_symbol_x,y=$add_symbol_y,text=$copper_result[0]%,x_size=2.413,y_size=3.048,w_factor=1.25,polarity=negative,angle=0,mirror=no,fontname=standard,bar_type=UPC39,bar_char_set=full_ascii,bar128_code=none,bar_checksum=no,bar_background=yes,bar_add_string=yes,bar_add_string_pos=top,bar_width=0.0003149606,bar_height=0.0078740157,ver=1");
		
		my $add_symbol_x = $sr_xmax - 100 + 2.2;
		my $add_symbol_y = $sr_ymax + 5.65;
		$f->COM("clear_layers");
		$f->COM("affected_layer,mode=all,affected=no");
		$f->COM("affected_layer,name=$copper_result1[1],mode=single,affected=yes");
		
		$f->COM("add_pad,attributes=no,x=$add_symbol_x,y=$add_symbol_y,symbol=$cu_rate_sym,polarity=positive,angle=0,mirror=yes,nx=1,ny=1,dx=0,dy=0,xscale=1,yscale=1");
		
		$add_symbol_x = $add_symbol_x + 2 - 4.3;
		$add_symbol_y = $add_symbol_y + 0.92 - 2.2;
	
		$f->COM("cur_atr_reset");
		$f->COM("cur_atr_set,attribute=.area_name,text=copper_rate");
		$f->COM("add_text,attributes=yes,type=string,x=$add_symbol_x,y=$add_symbol_y,text=$copper_result[1]%,x_size=2.413,y_size=3.048,w_factor=1.25,polarity=negative,angle=0,mirror=yes,fontname=standard,bar_type=UPC39,bar_char_set=full_ascii,bar128_code=none,bar_checksum=no,bar_background=yes,bar_add_string=yes,bar_add_string_pos=top,bar_width=0.0003149606,bar_height=0.0078740157,ver=1");
		
		#######################################################
		#长边再添加一个残铜率.
		my $add_symbol_x = $sr_xmax + 5.65;
		my $add_symbol_y = ($sr_ymax - $sr_ymin) * 0.5 + $sr_ymin + 100;
		$f->COM("clear_layers");
		$f->COM("affected_layer,mode=all,affected=no");
		$f->COM("affected_layer,name=$copper_result1[0],mode=single,affected=yes");
		
		$f->COM("add_pad,attributes=no,x=$add_symbol_x,y=$add_symbol_y,symbol=$cu_rate_sym,polarity=positive,angle=270,mirror=no,nx=1,ny=1,dx=0,dy=0,xscale=1,yscale=1");
		
		$add_symbol_x = $add_symbol_x + 5 - 3.22 - 1.4;
		$add_symbol_y = $add_symbol_y - 1.4 - 0.92 + 2 + 3.22;
		
		$f->COM("cur_atr_reset");
		$f->COM("cur_atr_set,attribute=.area_name,text=copper_rate");
		$f->COM("add_text,attributes=yes,type=string,x=$add_symbol_x,y=$add_symbol_y,text=$copper_result[0]%,x_size=2.413,y_size=3.048,w_factor=1.25,polarity=negative,angle=270,mirror=no,fontname=standard,bar_type=UPC39,bar_char_set=full_ascii,bar128_code=none,bar_checksum=no,bar_background=yes,bar_add_string=yes,bar_add_string_pos=top,bar_width=0.0003149606,bar_height=0.0078740157,ver=1");
		
		my $add_symbol_x = $sr_xmax + 5.65;
		my $add_symbol_y = ($sr_ymax - $sr_ymin) * 0.5 + $sr_ymin + 100 + 2.23;
		$f->COM("clear_layers");
		$f->COM("affected_layer,mode=all,affected=no");
		$f->COM("affected_layer,name=$copper_result1[1],mode=single,affected=yes");
		
		$f->COM("add_pad,attributes=no,x=$add_symbol_x,y=$add_symbol_y,symbol=$cu_rate_sym,polarity=positive,angle=90,mirror=yes,nx=1,ny=1,dx=0,dy=0,xscale=1,yscale=1");
		
		$add_symbol_x = $add_symbol_x - 5 + 3.22 + 1.4 + 0.75;
		$add_symbol_y = $add_symbol_y - 1.4 - 0.92 + 2 - 3.22;
		
		$f->COM("cur_atr_reset");
		$f->COM("cur_atr_set,attribute=.area_name,text=copper_rate");
		$f->COM("add_text,attributes=yes,type=string,x=$add_symbol_x,y=$add_symbol_y,text=$copper_result[1]%,x_size=2.413,y_size=3.048,w_factor=1.25,polarity=negative,angle=90,mirror=yes,fontname=standard,bar_type=UPC39,bar_char_set=full_ascii,bar128_code=none,bar_checksum=no,bar_background=yes,bar_add_string=yes,bar_add_string_pos=top,bar_width=0.0003149606,bar_height=0.0078740157,ver=1");
		
		#######################################################
		$f->COM("clear_layers");
		$f->COM("affected_layer,mode=all,affected=no");
=cut
		
	}
	
	#更新数据.
	if ($copper_rate == 1 && $have_copper_rate eq "yes") {

		my @attr_text=("copper_rate","copper_area");
		foreach my $tmp_text (@attr_text) {
			$f->COM("clear_layers");
			$f->COM("affected_layer,mode=all,affected=no");
			$f->COM("affected_layer,name=$copper_result1[0],mode=single,affected=yes");
			
			$f->COM("filter_reset,filter_name=popup");
			$f->COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.area_name,text=$tmp_text");
			$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=pad\;surface\;arc\;text");
			$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=surface\;arc\;text");
			$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=arc\;text");
			$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=text");
			$f->COM("filter_set,filter_name=popup,update_popup=no,polarity=negative");
			$f->COM("filter_area_strt");
			$f->COM("filter_area_end,layer=,filter_name=popup,operation=select,area_type=none,inside_area=no,intersect_area=no");
			if ($f->{COMANS} == 2) {
				if ($tmp_text eq 'copper_rate'){
					$f->COM("sel_change_txt,text=$copper_result[0]%,x_size=2.413,y_size=3.048,w_factor=1.25,polarity=negative,mirror=no,fontname=standard");
				}else{
					$f->COM("sel_change_txt,text=$total_copper_area[0],x_size=2.413,y_size=3.048,w_factor=1.25,polarity=negative,mirror=no,fontname=standard");
				}
			}
			$f->COM("filter_reset,filter_name=popup");
			
			$f->COM("clear_layers");
			$f->COM("affected_layer,mode=all,affected=no");
			$f->COM("affected_layer,name=$copper_result1[1],mode=single,affected=yes");
			
			$f->COM("filter_reset,filter_name=popup");
			$f->COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.area_name,text=$tmp_text");
			$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=pad\;surface\;arc\;text");
			$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=surface\;arc\;text");
			$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=arc\;text");
			$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=text");
			$f->COM("filter_set,filter_name=popup,update_popup=no,polarity=negative");
			$f->COM("filter_area_strt");
			$f->COM("filter_area_end,layer=,filter_name=popup,operation=select,area_type=none,inside_area=no,intersect_area=no");
			if ($f->{COMANS} == 2) {
				if ($tmp_text eq 'copper_rate'){
					$f->COM("sel_change_txt,text=$copper_result[1]%,x_size=2.413,y_size=3.048,w_factor=1.25,polarity=negative,mirror=yes,fontname=standard");
				}else{
					$f->COM("sel_change_txt,text=$total_copper_area[1],x_size=2.413,y_size=3.048,w_factor=1.25,polarity=negative,mirror=yes,fontname=standard");
				}
			}
			$f->COM("filter_reset,filter_name=popup");
		}
		$f->COM("clear_layers");
		$f->COM("affected_layer,mode=all,affected=no");
	}
}


sub press_button {
	if ($count_copper == 0) {
		&clear_all;
	} else {
		&select_all;
	}
}

sub add_label {
	#$f->PAUSE("$count_gold");
	#$show_check1->Label(-text => "L1->", -width => 7, -height=>'2', -font => 'SimSun 12',-relief =>'groove',-background => "#fcc64d");
	our $first_lable;
	our $second_lable;

	#if ($first_lable) {
	#	$first_lable->destroy();
	#}
	our $m1_value = "m1";
	our $m2_value = "m2";
	if ($count_gold == 1) {
		$first_lable = $show_check1->LabEntry(-label => 'L1 参考:',
											 -labelBackground => '#9BDBDB',
											 -labelFont => 'SimSun 12',
											 -textvariable => \$m1_value,
											 -bg => 'white',
											 -width => 6,
											 -relief=>'ridge',
											 -state=>"normal",
											 -labelPack => [qw/-side left -anchor w/])->pack(-side => 'left', -padx => 5);

		$second_lable = $show_check1->LabEntry(-label => "L$signal_num 参考:",
											  -labelBackground => '#9BDBDB',
											  -labelFont => 'SimSun 12',
											  -textvariable => \$m2_value,
											  -bg => 'white',
											  -width => 6,
											  -relief=>'ridge',
											  -state=>"normal",
											  -labelPack => [qw/-side left -anchor w/])->pack(-side => 'left', -padx => 5);
	} else {
		if ($first_lable) {
			$first_lable->destroy();
		}

		if ($second_lable) {
			$second_lable->destroy();
		}
	}
}
sub add_label2 {
	our $third_lable;
	our $four_lable;	
	our $gm1_value = "m1";
	our $gm2_value = "m2";
	if ($count_elec == 1) {
		$third_lable = $show_check3->LabEntry(-label => 'L1 参考:',
											 -labelBackground => '#9BDBDB',
											 -labelFont => 'SimSun 12',
											 -textvariable => \$gm1_value,
											 -bg => 'white',
											 -width => 6,
											 -relief=>'ridge',
											 -state=>"normal",
											 -labelPack => [qw/-side left -anchor w/])->pack(-side => 'left', -padx => 5);

		$four_lable = $show_check3->LabEntry(-label => "L$signal_num 参考:",
											  -labelBackground => '#9BDBDB',
											  -labelFont => 'SimSun 12',
											  -textvariable => \$gm2_value,
											  -bg => 'white',
											  -width => 6,
											  -relief=>'ridge',
											  -state=>"normal",
											  -labelPack => [qw/-side left -anchor w/])->pack(-side => 'left', -padx => 5);
	} else {
		if ($third_lable) {
			$third_lable->destroy();
		}

		if ($four_lable) {
			$four_lable->destroy();
		}
	}
}

sub getERPCopperhickness{
    my $job_name_uc = uc(substr($job_name,0,13));
    my $mun=substr($job_name,4,2);
	
	my $dbc_h = $o->CONNECT_ORACLE('host'=>'172.20.218.193', 'service_name'=>'inmind.fls', 'port'=>'1521', 'user_name'=>'GETDATA', 'passwd'=>'InplanAdmin');
	if (! $dbc_h)
	{
		$c->Messages('warning', '"HDI InPlan数据库"连接失败->程序终止!');
		exit(0);	}   
    
     my $sql="
        SELECT
        job_name,   
         Layer_name,
            finish_cu_thk_,
            ROUND(CAL_CU_THK_/1.0 * 25.4  , 2) as  REQUIRED_CU_WEIGHT
        FROM
            VGT_HDI.RPT_COPPER_LAYER_LIST 
        where 
        Job_NAME =UPPER('$job_name_uc')
        and Layer_name in('l1','l$mun','L1','L$mun')";
		
     my $sth = $dbc_h->prepare($sql);#结果保存在$sth中 
	 $sth->execute() or die "无法执行SQL语句:$dbc_h->errstr"; 
 
    my $flow_info = "no";
	my @recs =();
	while (my @rec=$sth->fetchrow_array) {
        push @recs,\@rec;
    } 
   my %daa;
   foreach my $da (@recs){
        
       $daa{lc $da->[1]}=$da->[3]
   }    
   # print Dumper(%daa);
   return %daa;
}

sub get_board_thickness {
	
	# --连接HDI InPlan oracle数据库
	my $dbc_h = $o->CONNECT_ORACLE('host'=>'172.20.218.193', 'service_name'=>'inmind.fls', 'port'=>'1521', 'user_name'=>'GETDATA', 'passwd'=>'InplanAdmin');
	if (! $dbc_h)
	{
		$c->Messages('warning', '"HDI InPlan数据库"连接失败->程序终止!');
		exit(0);
	}
	my %job_data = $o->getJobData($dbc_h, uc(substr($job_name,0,13)));
	$dbc_h->disconnect if ($dbc_h);

	$board_thick = $job_data{'out_thick'};
	if ($board_thick) {
		return $board_thick/1;
	} else {
		return 0;
	}
}


__END__
Ver:1.3
Author:Chao.Song
2020..06.15
1.Request from YanDi.Xue:change int result to %.1f

Ver:1.4
Author:Chao.Song
2020.09.14
1.应业务要求，更改镀金面积及化金面积算法：
http://192.168.2.120:82/zentao/story-view-2031.html

Ver:1.5
Author:Chao.Song
2020.09.25
1.内层计算铜厚，不考虑钻孔
http://192.168.2.120:82/zentao/story-view-2105.html


Ver:1.6
Author:Chao.Song
2021.01.18
1.out layers  add copper rate symbol changed from copper_rate to chris-tudian. 
 NO HTML ReQuesr. Zhou Yong ask from DingDing. Back groud is output tgz check the chris-tudian symbol.


Ver:1.7
Author:Chao.Song
2022.04.02
1.增加panel中的set数和set中pcs数输出到残铜率文件。
http://192.168.2.120:82/zentao/story-view-4021.html

ver:1.8
Author:lyh
2022.12.30
优化4.15，计算化金面积&镀金面积程序，与外层有铜皮的料号，自动识别将外层铜皮去掉，防止面积过大，运行完成后还原。
http://192.168.2.120:82/zentao/story-view-5009.html

# === 2023.03.06 Song 通孔和控深孔合并时，无drl层存在，判断是否有cdc或者cds存在
