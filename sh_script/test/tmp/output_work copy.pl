#!c:/perl/bin/perl -w
=head
v1.1 modified by song 20190513 add pdf format output

=cut

use lib '/incam/release/app_data/perl';
use strict;
use warnings;
use Encode;
use encoding 'euc_cn';
use Tk;
use Tk::Tree;
use incam;
use File::Copy;
use File::Path;
use File::Copy::Recursive qw(fcopy rcopy dircopy fmove rmove dirmove);
use File::Path qw(make_path remove_tree);
#use POSIX;

my $host = shift;
my $f = new incam($host);

require Tk::LabFrame;
require Tk::LabEntry;

my $genesis_dir_work = $ENV{GENESIS_DIR}; 
my $images_path = "/incam/server/site_data/scripts/sh1_script/images";
my $job_name = $ENV{JOB};

my $client_no = substr($job_name, 1,3);
my $type_client = substr($job_name, 0,4);
my $version = substr($job_name, 8,5);

my $do_workfile_path = "/id/workfile/hdi_film/$job_name";
if (! -d $do_workfile_path ) {
	mkdir "$do_workfile_path";		
}
#my $send_mi_path = "//192.168.2.33/vgt\$/设计课/外部资料/工程部外部取读资料/设计课确认工程问题/发给客户GERBER";

my @inn_lay_array = ();
my @all_outlayer_array = ();
my @all_board_array = ();
my @step_list_all = ();
my @drill_lay_array = ();
$f->DO_INFO("-t MATRIX -d ROW -e $job_name/matrix");
for(my $i=0 ; $i < @{$f->{doinfo}{gROWname}} ; $i++){
	my $info_ref = { name    => @{$f->{doinfo}{gROWname}}[$i],
				  layer_type => @{$f->{doinfo}{gROWlayer_type}}[$i],
				  context    => @{$f->{doinfo}{gROWcontext}}[$i],
				  polarity   => @{$f->{doinfo}{gROWpolarity}}[$i],
				  side       => @{$f->{doinfo}{gROWside}}[$i],
				};
	if ( $info_ref->{context} eq "board" && $info_ref->{side} eq "inner" ){		
		push(@inn_lay_array,$info_ref->{name});
	}
	if ( $info_ref->{context} eq "board" && $info_ref->{layer_type} eq "drill" ){		
		push(@drill_lay_array,$info_ref->{name});
	}
	if ( $info_ref->{context} eq "board" && $info_ref->{side} =~ /(top|bottom)/ && $info_ref->{layer_type} eq "signal" ){		
		push(@all_outlayer_array,$info_ref->{name});
	}	
	if ( $info_ref->{context} eq "board" ){
		if ( $info_ref->{name} ne "md1" && $info_ref->{name} ne "md2" && $info_ref->{name} ne "pnl_rout" && $info_ref->{name} ne "inn" && $info_ref->{name} ne "inn-pp" && $info_ref->{name} ne "drl-sz" && $info_ref->{name} ne "lp" && $info_ref->{name} ne "pnl_rout1" && $info_ref->{name} ne "pnl_rout2" && $info_ref->{name} ne "pnl_rout3" && $info_ref->{name} ne "pnl_rout4" ) {
			push(@all_board_array,$info_ref->{name});
		}
	}
}

$f->INFO(entity_type => 'step',
		 entity_path => "$job_name/panel",
		   data_type => 'LAYERS_LIST');		   
my @all_lay_list = @{$f->{doinfo}{gLAYERS_LIST}};
$f->INFO(entity_type => 'job',
		 entity_path => "$job_name",
		   data_type => 'STEPS_LIST');
my $sel_step = "edit";		   
my @step_list_tmp = @{$f->{doinfo}{gSTEPS_LIST}};
foreach my $tmp (@step_list_tmp) {
	if ( $tmp ne "drl" && $tmp ne "lp" && $tmp ne "2nd" && $tmp ne "3nd" && $tmp ne "fa" && $tmp ne "zk" && $tmp ne "panel" && $tmp ne "orig" && $tmp ne "org" && $tmp ne "net" ) {
		push(@step_list_all,"$tmp"); 
	}
	if ( $tmp eq "set" ) {
		$sel_step = "set";
	}
}

my $mw3_7 = MainWindow->new(-title =>"VGT");
$mw3_7->bind('<Return>' => sub{ shift->focusNext; });
$mw3_7->protocol("WM_DELETE_WINDOW", \&OnQuit);
$mw3_7->geometry("290x680+20+80");
$mw3_7->resizable(0,0);
$mw3_7->raise( );

my $sh_log_frm = $mw3_7->Frame(-bg => '#9BDBDB',-borderwidth =>2,-relief => "raised",-height => 5)->pack(-side=>'top',-fill=>'both');
my $sh_log = $sh_log_frm->Photo('info',-file => "$images_path/sh_log.xpm");
my $image_label = $sh_log_frm->Label(-image => $sh_log, -border => 1, -relief => 'solid',
                                              )->pack(-side => 'left',
                                                      -padx => 5,
                                                      -pady => 5);  
													  
$sh_log_frm->Label(-text => "输出客户工作稿",-font => 'charter 20 bold',-bg => '#9BDBDB')->pack();
$sh_log_frm->Label(-text => "作者:dgz  Ver:1.1",-font => 'charter 10',-bg => '#9BDBDB')->pack(-side=>'right', -padx => 10); 

my $tab_frm = $mw3_7->LabFrame(-label => "参数选择",-font => 'SimSun 10',-bg => '#9BDBDB',-fg => 'blue',)->pack(-side=>'top',-fill=>'both');
my $menub_sel_frm = $tab_frm->Frame(-bg => '#9BDBDB')->pack(-side=>'top',-fill=>'both');
my $menub_sel_job_frm = $menub_sel_frm->Frame(-bg => '#9BDBDB')->pack(-side=>'left',-fill=>'both');
my $menub_sel_job = $menub_sel_job_frm->LabEntry(-label => "料号:",
									-labelBackground => '#9BDBDB',
									-labelFont => 'SimSun 11',
									-textvariable => \$job_name,
									-bg => 'white',
									-fg => 'blue',
									-width => 15,
									-relief=>'ridge',
									-state=>"disabled",
									-labelPack => [qw/-side left -anchor w/])->pack(-side => 'left',-fill=>'x',-padx=> 2,-pady=> 5); 

my $menub_sel_step_frm = $menub_sel_frm->Frame(-bg => '#9BDBDB')->pack(-side=>'left',-fill=>'both');

$menub_sel_step_frm->Label(-text => "step:",-font => 'SimSun 11',-bg => '#9BDBDB')->pack(-side => 'left',-padx => 5,-pady => 5);
$menub_sel_step_frm->Optionmenu(-variable => \$sel_step, -options => [@step_list_all],-bg => 'white',)->pack(-side=>'left');

my $output_format_frm = $tab_frm->Frame(-bg => '#9BDBDB')->pack(-side=>'top',-fill=>'both');	
my $sel_format = "Gerber274x";
my @all_format = ("Gerber274x","TGZ","PDF");
$output_format_frm->Label(-text => "格式:",-font => 'SimSun 11',-bg => '#9BDBDB')->pack(-side => 'left',-padx => 2,-pady => 5);
$output_format_frm->Optionmenu(-variable => \$sel_format, -options => [@all_format],-bg => 'white')->pack(-side=>'left');

my $path_sel_all_frm = $tab_frm->Frame(-bg => '#9BDBDB')->pack(-side=>'top',-fill=>'both');
my $path_sel = $path_sel_all_frm->LabEntry(-label => "路径:",
										-labelBackground => '#9BDBDB',
										-labelFont => 'SimSun 8',
										-textvariable =>\$do_workfile_path,
										-bg => 'white',
										-width => 36,
										-relief=>'ridge',
										-labelPack => [qw/-side left -anchor w/])->pack(-side => 'left',-padx => 2,-pady => 5);
										
my $select_frm_lay = $mw3_7-> Frame(-bg => '#9BDBDB')->pack(-side=>'top',-fill=>'both',-expand=>1);
my $select_all_lay = $select_frm_lay-> Frame(-bg => '#9BDBDB')->pack(-side=>'top',-fill=>'both',-expand=>1);
my $select_lay_list = $select_all_lay-> Frame(-bg => '#9BDBDB')->pack(-side=>'left',-padx => 2,-fill=>'both');
my $sel_layer_lb = $select_lay_list->Scrolled('Listbox',-scrollbars=>'e',-selectbackground=>'#6DA5EB',-selectforeground=>'white',-selectmode=>'multiple',-height => 30,-width=> 18,
									 -background=>'white',-foreground=>'black',-font=> 'SimSun 12 bold')
									 ->pack(-side=>'top');									 
foreach my $tmp (@all_lay_list) {
	$sel_layer_lb -> insert('end', "$tmp");	
}	
		
my $select_frm_tmp = $select_all_lay-> Frame(-bg => '#9BDBDB')->pack(-side=>'right',-fill=>'both',-padx => 10);
my $button_frm1 = $select_frm_tmp->Button(-text => "只选内层",
                                          -command => sub {&inn_sel_lay;},
                                          -width => 10,
										  -activebackground=>'green',
										  -bg => '#9BDBDB',
										  -font=> 'SimSun 10 bold',
										  -height=> 2,
                                         )->pack(-side => 'top',
												 -fill=>'y',
                                                 -pady => 10 );	
my $button_frm2 = $select_frm_tmp->Button(-text => "只选外层",
                                          -command => sub {&out_sel_lay;},
                                          -width => 10,
										  -activebackground=>'green',
										  -bg => '#9BDBDB',
										  -font=> 'SimSun 10 bold',
										  -height=> 2,
                                         )->pack(-side => 'top',
												 -fill=>'y',
                                                 -pady => 10 );													 
my $button_frm3 = $select_frm_tmp->Button(-text => 'Board',
                                          -command => sub {&board_sel_lay;},
                                          -width => 10,
										  -activebackground=>'green',
										  -bg => '#9BDBDB',
										  -font=> 'SimSun 10 bold',
										  -height=> 2,
                                         )->pack(-side => 'top',
												 -fill=>'y',
                                                 -pady => 10 );									 
my $button_frm4 = $select_frm_tmp->Button(-text => "反选",
                                          -command => sub {&reverse_sel_lay;},
                                          -width => 10,
										  -activebackground=>'green',
										  -bg => '#9BDBDB',
										  -font=> 'SimSun 10 bold',
										  -height=> 2,
                                         )->pack(-side => 'top',
												 -fill=>'y',
                                                 -pady => 10 );
my $button_frm5 = $select_frm_tmp->Button(-text => "选择all",
                                          -command => sub {&sel_lay_all;},
                                          -width => 10,
										  -activebackground=>'green',
										  -bg => '#9BDBDB',
										  -font=> 'SimSun 10 bold',
										  -height=> 2,
                                         )->pack(-side => 'top',
												 -fill=>'y',
                                                 -pady => 10 );
my $button_frm6 = $select_frm_tmp->Button(-text => "清除all",
                                          -command => sub {&clear_lay_all;},
                                          -width => 10,
										  -activebackground=>'green',
										  -bg => '#9BDBDB',
										  -font=> 'SimSun 10 bold',
										  -height=> 2,
                                         )->pack(-side => 'top',
												 -fill=>'y',
                                                 -pady => 10 );	

my $run_button = $select_frm_tmp->Button(-text => "输出",
                                          -command => sub {&run_output_gerber;exit 0;},
                                          -width => 10,
										  -activebackground=>'green',
										  -bg => '#9BDBDB',
										  -font=> 'SimSun 10 bold',
										  -height=> 2,
                                          )->pack(-side => 'top',
												  -fill=>'y',
                                                  -pady => 10 );
												  
my $exit_button = $select_frm_tmp->Button(-text => "退出",
                                          -command => sub {exit 0},
                                          -width => 10,
										  -activebackground=>'red',
										  -bg => '#9BDBDB',
										  -font=> 'SimSun 10 bold',
										  -height=> 2,
                                          )->pack(-side => 'top',
												  -fill=>'y',
                                                  -pady => 10 );											  

MainLoop;

################################################################################################################################################################################

sub OnQuit {
	my $ans = $mw3_7->messageBox(-icon => 'question',-message => "确定要退出吗?",-title => 'quit',-type => 'YesNo');
	return if $ans eq "No";
	exit;
}

sub inn_sel_lay {
	my @tmp_layer = ();
	@tmp_layer = $sel_layer_lb->get(0,'end');
	$sel_layer_lb->selectionClear(0,'end');
	foreach my $tmp (@inn_lay_array) {
		AAAAA:
		foreach (0..$#tmp_layer) {
			if ($tmp_layer[$_] eq $tmp) {
				$sel_layer_lb->selectionSet($_);
				last AAAAA;
			}
		} 
	}
}
sub out_sel_lay {
	my @tmp_layer = ();
	@tmp_layer = $sel_layer_lb->get(0,'end');
	$sel_layer_lb->selectionClear(0,'end');
	foreach my $tmp (@all_outlayer_array) {
		AAAAA:
		foreach (0..$#tmp_layer) {
			if ($tmp_layer[$_] eq $tmp) {
				$sel_layer_lb->selectionSet($_);
				last AAAAA;
			}
		} 
	}
}
sub board_sel_lay {
	my @tmp_layer = ();
	@tmp_layer = $sel_layer_lb->get(0,'end');
	$sel_layer_lb->selectionClear(0,'end');
	foreach my $tmp (@all_board_array) {
		AAAAA:
		foreach (0..$#tmp_layer) {
			if ($tmp_layer[$_] eq $tmp) {
				$sel_layer_lb->selectionSet($_);
				last AAAAA;
			}
		} 
	}
}

sub reverse_sel_lay {
	
	my @tmp_layer = ();
	my @selectlayers_tmp = ();	
	foreach($sel_layer_lb->curselection()){	
		my $tmp_layers = $sel_layer_lb->get($_);
		push(@selectlayers_tmp,$tmp_layers);		
	}
	my $sel_lay_no = scalar(@selectlayers_tmp);
	if ( $sel_lay_no == 0 ) {
		$sel_layer_lb->selectionSet(0,'end');	
	} else {
		our @sel_lay_list = ();
		@tmp_layer = $sel_layer_lb->get(0,'end');
		my $tmp_layer_no = scalar(@tmp_layer);
		$sel_layer_lb->selectionClear(0,'end');		
		foreach (0..$#tmp_layer) {			
			foreach my $tmp (@selectlayers_tmp) {				
				if ($tmp_layer[$_] eq $tmp ) {
					goto CCCCC;
				}
			}
			push(@sel_lay_list,"$tmp_layer[$_]");
			CCCCC:		
		}
		foreach (0..$#tmp_layer) {			
			foreach my $tmp (@sel_lay_list) {				
				if ($tmp_layer[$_] eq $tmp ) {
					$sel_layer_lb->selectionSet($_);
				}
			}	
		}
	}
}
sub sel_lay_all {
	$sel_layer_lb->selectionSet(0,'end');
}
sub clear_lay_all {
	$sel_layer_lb->selectionClear(0,'end')
}
################################################################################################################################################################################
sub run_output_gerber {	
	my @selectlayers = ();	
	foreach($sel_layer_lb->curselection()){	
		my $tmp_layers = $sel_layer_lb->get($_);		
		push(@selectlayers,$tmp_layers);		
	}	
	my $layer_no = scalar(@selectlayers);
	if ( $layer_no eq 0 ) {
		&run_message_no_sel;
		$select_frm_tmp->withdraw;
	}
	$mw3_7->iconify();

	my $job_path_name = "$type_client\-$version";
	my $do_path = "/tmp/$job_path_name";
	if (! -d $do_path ) {
		mkdir "$do_path";	
	} else {
		system("rm -rf $do_path/*");
	}
	if ( $sel_format eq "Gerber274x" ) {
		if ( $sel_step eq "set" or $sel_step eq "edit") {
			$f->COM("open_entity,job=$job_name,type=step,name=edit,iconic=no");
			$f->AUX("set_group,group=$f->{COMANS}");
			$f->COM("units,type=inch");
			
			#取消切除钢网的板外物 例如型号h32310oba36b1 板外就有对位pad 20231127 by lyh
			#http://192.168.2.120:82/zentao/story-view-6254.html
			foreach my $tmp (@selectlayers) {
				if ( $tmp eq "p1" or $tmp eq "p2" or $tmp eq "pp" ) {				  
					$f->COM("clear_layers");
					$f->COM("affected_layer,mode=all,affected=no");
					$f->COM("affected_layer,name=$tmp,mode=single,affected=yes");
					#$f->COM("clip_area_strt");
					#$f->COM("clip_area_end,layers_mode=affected_layers,layer=,area=profile,area_type=rectangle,inout=outside,contour_cut=no,margin=-2");
					$f->COM("filter_reset,filter_name=popup");
					$f->COM("filter_set,filter_name=popup,update_popup=no,profile=out");
					$f->COM("filter_area_strt");
					$f->COM("filter_area_end,layer=,filter_name=popup,operation=select,area_type=rectangle,inside_area=no,intersect_area=no");
					$f->COM('get_select_count');
					my $count = $f->{COMANS};
					if ($count > 0){
						my $ans = $mw3_7->messageBox(-icon => 'question',-message => "检测到钢网${tmp} 层profile外有物件，程序将暂停检查,请确认是否异常?",-title => 'quit',-type => 'Ok');
						$f->PAUSE("PLEASE CHECK!");				
					}
					$f->COM("clear_layers");
					$f->COM("affected_layer,mode=all,affected=no");
				}		
			}
		
			if ( $sel_step eq "set" ) {
				$f->COM("open_entity,job=$job_name,type=step,name=$sel_step,iconic=no");
				$f->AUX("set_group,group=$f->{COMANS}");
				$f->COM("units,type=inch");
				$f->COM("sredit_reduce_nesting");
			}
			
			my @surface_lay_array = ();
			foreach my $tmp (@selectlayers) {
				foreach my $tmp_drl (@drill_lay_array) {
					if ( $tmp eq $tmp_drl )	{
						goto NOT_DRILL;
					}
				}
				push(@surface_lay_array,$tmp);
				NOT_DRILL:
			}
			
			foreach my $tmp (@surface_lay_array) {
				if ( $tmp ne "p1" && $tmp ne "p2" && $tmp ne "w" && $tmp ne "ww" ) {
					$f->COM("clear_layers");
					$f->COM("affected_layer,mode=all,affected=no");
					$f->COM("affected_layer,name=$tmp,mode=single,affected=yes");
					$f->COM("sel_contourize,accuracy=0,break_to_islands=yes,clean_hole_size=3,clean_hole_mode=x_and_y");
					$f->COM("clear_layers");
					$f->COM("affected_layer,mode=all,affected=no");
				}
			}			
		}
		
		my @files = ();
		my $break_symbol;
		foreach my $tmp (@selectlayers) {
			#http://192.168.2.120:82/zentao/story-view-4718.html 部分客户要求工作稿钢网按实际资料输出 故不能打散输出 20221114 by Lyh
			$break_symbol="yes";
			if ($tmp eq "p1" or $tmp eq "p2"){				
				$break_symbol="no";
			}
			$f->COM("output_layer_reset");
			$f->COM("output_layer_set,layer=$tmp,angle=0,mirror=no,x_scale=1,y_scale=1,comp=0,polarity=positive,setupfile=,setupfiletmp=,line_units=inch,gscl_file=");
			$f->COM("output,job=$job_name,step=$sel_step,format=Gerber274x,dir_path=$do_path,prefix=,suffix=,break_sr=yes,break_symbols=$break_symbol,break_arc=no,scale_mode=all,surface_mode=contour,min_brush=1,units=inch,coordinates=absolute,zeroes=none,nf1=2,nf2=6,x_anchor=0,y_anchor=0,wheel=,x_offset=0,y_offset=0,line_units=inch,override_online=yes,film_size_cross_scan=0,film_size_along_scan=0,ds_model=RG6500");
			$f->COM("disp_on");
			$f->COM("origin_on");
			push(@files,"$tmp");
		}
		
		chdir "$do_path";	
		#song change tar to rar in 20190315 ##	
		#system("tar -czvf $job_path_name.tar.gz *");
		#system("rar a $job_path_name *");
		#周涌通知 全部用zip压缩 20230920 by lyh
		system("zip -r $job_path_name ./*");
		
		$f->COM("check_inout,mode=in,type=job,job=$job_name");
		$f->COM("close_job,job=$job_name");
		$f->COM("close_form,job=$job_name");
		$f->COM("close_flow,job=$job_name");
		#song change tar to rar in 20190315 ##	
		#copy("$do_path/$job_path_name.tar.gz","$do_workfile_path");
		#copy("$do_path/$job_path_name.rar","$do_workfile_path");
		copy("$do_path/$job_path_name.zip","$do_workfile_path");

		system("rm -rf $do_path");
		
	} elsif ($sel_format eq "TGZ" ) {
		
		my $copy_tgz_name = "$job_name\-work";
		$f->INFO(entity_type => 'job',
			 entity_path => "$copy_tgz_name",
			   data_type => 'EXISTS');
		if ( $f->{doinfo}{gEXISTS} eq "yes" ) {	
			$f->COM("delete_entity,job=,type=job,name=$copy_tgz_name");
		}
		$f->COM("check_inout,mode=in,type=job,job=$job_name");
		$f->COM("close_job,job=$job_name");
		$f->COM("close_form,job=$job_name");
		$f->COM("close_flow,job=$job_name");
		$f->COM("copy_entity,type=job,source_job=$job_name,source_name=$job_name,dest_job=$copy_tgz_name,dest_name=$copy_tgz_name,dest_database=linux1");
		
		$f->COM("check_inout,mode=out,type=job,job=$copy_tgz_name");
		$f->COM("clipb_open_job,job=$copy_tgz_name,update_clipboard=view_job");
		$f->COM("open_job,job=$copy_tgz_name");
		$f->INFO(entity_type => 'job',
				 entity_path => "$copy_tgz_name",
				 data_type => 'STEPS_LIST');
		my @step_list = @{$f->{doinfo}{gSTEPS_LIST}};
		
		if ( $sel_step eq "set" ) {
			$f->INFO(entity_type => 'step',
					 entity_path => "$copy_tgz_name/set",
					   data_type => 'SR',
					  parameters => "step");
			my @sr_step_tmp = @{$f->{doinfo}{gSRstep}};
			my %count;
			my @sr_step = grep {++$count{$_}<2}@sr_step_tmp;
			foreach my $tmp1 (@step_list) {
				foreach my $tmp2 (@sr_step_tmp) {
					if ( $tmp1 eq $tmp2 ) {
						goto DEL_step_mark;
					}				
				}
				if ( $tmp1 ne "$sel_step" ) {
					$f->COM("delete_entity,job=$copy_tgz_name,type=step,name=$tmp1");
				}
				DEL_step_mark:
			}
			$f->PAUSE("@step_list");
			$f->PAUSE("@sr_step_tmp");
		}
		
		my @update_step_list = ();
		foreach my $tmp (@step_list) {
			if ($tmp =~ /^edit[0-9]?.[flip][flip].*/) {
				push(@update_step_list, $tmp);
			}
		}

		if (scalar(@update_step_list) != 0) {
			foreach my $tmp (@update_step_list) {
				my $update_step = $tmp;
				my $tmp_word = substr($tmp, 4, 1);
				
				my $tmp_step;
				if ($tmp_word =~ /^\d+$/) {
					$tmp_step = substr($tmp, 0, 5);
				} else {
					$tmp_step = substr($tmp, 0, 4);
				}
				
				my $have_step = "no";
				my $orig_step = "";
				foreach my $step (@step_list) {
					if ($step eq "$tmp_step") {
						$have_step = "yes";
						$orig_step = "$tmp_step";
					}
				}

				if ($have_step eq "yes") {
					$f->COM("change_step_dependency,job=$copy_tgz_name,step=$update_step,operation=release");	
					$f->COM("change_step_dependency,job=$job_name,step=$update_step,operation=restore");
					$f->COM("update_dependent_step,job=$job_name,step=$update_step");
					$f->COM("flip_step,job=$job_name,step=$orig_step,flipped_step=$update_step,new_layer_suffix=_flp,mode=center,board_only=yes");
					$f->COM("change_step_dependency,job=$job_name,step=$update_step,operation=release");
				}
			}
		}
		
		$f->INFO(entity_type => 'step',
				 entity_path => "$copy_tgz_name/$sel_step",
				   data_type => 'LAYERS_LIST');
		$f->COM("open_entity,job=$copy_tgz_name,type=step,name=$sel_step,iconic=no");
		$f->AUX("set_group,group=$f->{COMANS}");	
		$f->COM("units,type=inch");		   
		my @all_layers_list = @{$f->{doinfo}{gLAYERS_LIST}};
		foreach my $tmp1 (@all_layers_list) {
			foreach my $tmp2 (@selectlayers) {
				if ( $tmp1 eq $tmp2 ) {
					goto DEL_layer_mark;
				}			
			}
			$f->COM("delete_layer,layer=$tmp1");
			DEL_layer_mark:
		}
		
		if ( -e "$genesis_dir_work/sys/hooks/line_hooks/export_job.pre" ) {
			move("$genesis_dir_work/sys/hooks/line_hooks/export_job.pre","$genesis_dir_work/sys/hooks/line_hooks/export_job.pre-tmpbackup");
		}
		$f->COM("save_job,job=$copy_tgz_name,override=no");
		$f->COM("export_job,job=$copy_tgz_name,path=$do_path,mode=tar_gzip,submode=full,overwrite=yes");	
		$f->COM("check_inout,mode=in,type=job,job=$copy_tgz_name");
		$f->COM("close_job,job=$copy_tgz_name");
		$f->COM("close_form,job=$copy_tgz_name");
		$f->COM("close_flow,job=$copy_tgz_name");
		if ( -e "$genesis_dir_work/sys/hooks/line_hooks/export_job.pre-tmpbackup" ) {
			move("$genesis_dir_work/sys/hooks/line_hooks/export_job.pre-tmpbackup","$genesis_dir_work/sys/hooks/line_hooks/export_job.pre");
		}
		
		copy("$do_path/$copy_tgz_name.tgz","$do_workfile_path");	
		system("rm -rf $do_path");
	} elsif ($sel_format eq "PDF") {
        $f->COM("open_entity,job=$job_name,type=step,name=$sel_step,iconic=no");
        $f->AUX("set_group,group=$f->{COMANS}");
        my $print_layers = join('\;',@selectlayers);
        $f->COM("print,title=$job_name,layer_name=$print_layers,mirrored_layers=,draw_profile=no,drawing_per_layer=yes,label_layers=bottom,dest=pdf_file,num_copies=1,dest_fname=$do_workfile_path/$job_name.pdf,paper_size=A4, scale_to=0,orient=none,paper_orient=portrait,paper_width=210,paper_units=mm,auto_tray=no,page_numbering=no,top_margin=0.5,bottom_margin=0.5,left_margin=0.5,right_margin=0.5,x_spacing=0,y_spacing=0");
    }
		
	&run_message_over;

}

sub run_message_no_sel {
	my $ans0 = $mw3_7->messageBox(-icon => 'question',-message => "没有选择要输出的层,请重新选择!",-title => 'quit',-type => 'YesNo');
	return if $ans0 eq "Yes";
	exit 0;
}

sub run_message_data_yes {
	my $ans1 = $mw3_7->messageBox(-icon => 'question',-message => "发给客户GERBER目录下巳有资料,是否更新!",-title => 'quit',-type => 'YesNo');
	return if $ans1 eq "Yes";
	exit 0;
}

sub run_message_over {
	my $ans1 = $mw3_7->messageBox(-icon => 'question',-message => "程序运行结束,请检查!",-title => 'Waiting',-type => 'Ok');
	exit 0;
}




