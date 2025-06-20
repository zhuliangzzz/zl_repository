#!/usr/bin/perl -w
use lib '/incam/release/app_data/perl';
use Tk;
use Tk::Tree;
use incam;
use encoding 'euc_cn';
use POSIX;
use Encode;
use Encode::TW;
use File::Copy;
use File::Copy::Recursive qw(fcopy rcopy dircopy fmove rmove dirmove);
$host = shift;
$f = new incam($host);
require Tk::LabFrame;
require Tk::LabEntry;
                  
my $images_path = "/incam/server/site_data/scripts/sh1_script/images";
my $job_name = $ENV{JOB};
my $step = $ENV{STEP};

my $client_no = substr($job_name, 1,3);
my $version = substr($job_name,-2,2); 

my $do_rout_path = "/id/workfile/hdi_film/$job_name";
if (! -d $do_rout_path ) {
	mkdir $do_rout_path;
}	

my @all_signal_array = ();
my @rout_array = ();
my @drill_array = ();
my @inn_lay_array = ();
my @inn_lay_polarity = ();
$f->DO_INFO("-t MATRIX -d ROW -e $job_name/matrix");
for(my $i=0 ; $i < @{$f->{doinfo}{gROWname}} ; $i++){
	my $info_ref = { name       => @{$f->{doinfo}{gROWname}}[$i],
					 layer_type => @{$f->{doinfo}{gROWlayer_type}}[$i],
					 context    => @{$f->{doinfo}{gROWcontext}}[$i],
					 polarity   => @{$f->{doinfo}{gROWpolarity}}[$i],
					 side       => @{$f->{doinfo}{gROWside}}[$i],
					};
			
	if ( $info_ref->{context} eq "board" && $info_ref->{layer_type} =~ /(signal|power_ground)/ ){		
		push(@all_signal_array,$info_ref->{name});
	}
	if ( $info_ref->{context} eq "board" && $info_ref->{layer_type} eq "drill" ){
		push(@drill_array,$info_ref->{name});
	}
	if ( $info_ref->{context} eq "board" && $info_ref->{layer_type} eq "rout" && ( $info_ref->{name} eq "pnl_rout" or $info_ref->{name} eq "pnl_rout1" or $info_ref->{name} eq "pnl_rout2" or $info_ref->{name} eq "pnl_rout3" )){
		push(@rout_array,$info_ref->{name});
	}
	if ( $info_ref->{context} eq "board" && $info_ref->{side} eq "inner" ){		
		push(@inn_lay_array,$info_ref->{name});
		push(@inn_lay_polarity,$info_ref->{polarity});
	}
}
my $bot_signal_layer = scalar(@all_signal_array);
my $rout_layer_no = scalar(@rout_array);
###################################################################################################################################################################################################
if ( $bot_signal_layer <= 2 ) {
	&run_message_rout;
	exit 0;
}
if ( $rout_layer_no eq 0 ) {
	&run_message_rout_no;
	exit 0;
}
if ( $rout_layer_no > 3 ) {
	&run_message_rout4_no;
	exit 0;
}

my @step_xmin_list = ();
my @step_ymin_list = ();
my @step_xmax_list = ();
my @step_ymax_list = ();
my @panel_step_list = ();
$f->INFO(entity_type => 'step',entity_path => "$job_name/panel",data_type => 'SR');
for(my $i=0 ; $i < @{$f->{doinfo}{gSRstep}} ; $i++){
	my $info_sr = { name		=> @{$f->{doinfo}{gSRstep}}[$i],
					xmin		=> @{$f->{doinfo}{gSRxmin}}[$i],
					ymin		=> @{$f->{doinfo}{gSRymin}}[$i],
					xmax		=> @{$f->{doinfo}{gSRxmax}}[$i],
					ymax		=> @{$f->{doinfo}{gSRymax}}[$i],
				};	
	
	#if ( $info_sr->{name} =~ /edit/ or $info_sr->{name} =~ /set/ or $info_sr->{name} =~ /zk/ ){
	if ( $info_sr->{name} =~ /(edit|set|zk|kk)/ ){
		push(@step_xmin_list,$info_sr->{xmin});
		push(@step_ymin_list,$info_sr->{ymin});
		push(@step_xmax_list,$info_sr->{xmax});
		push(@step_ymax_list,$info_sr->{ymax});
	}
	push(@panel_step_list,$info_sr->{name});
}

my @sort_step_xmin_list = map{$_->[-1]}	sort {$a->[0] <=> $b->[0] } map {[(split)[1],$_]} @step_xmin_list;	
my @sort_step_ymin_list = map{$_->[-1]}	sort {$a->[0] <=> $b->[0] } map {[(split)[1],$_]} @step_ymin_list;	
my @sort_step_xmax_list = map{$_->[-1]}	sort {$b->[0] <=> $a->[0] } map {[(split)[1],$_]} @step_xmax_list;	
my @sort_step_ymax_list = map{$_->[-1]}	sort {$b->[0] <=> $a->[0] } map {[(split)[1],$_]} @step_ymax_list;	

my $sr_profile_x_min = @sort_step_xmin_list[0];
my $sr_profile_y_min = @sort_step_ymin_list[0];
my $sr_profile_x_max = @sort_step_xmax_list[0];
my $sr_profile_y_max = @sort_step_ymax_list[0];

$f->INFO(entity_type => 'step',entity_path => "$job_name/panel",data_type => 'PROF_LIMITS');
my $profile_x = $f->{doinfo}{gPROF_LIMITSxmax};
my $profile_y = $f->{doinfo}{gPROF_LIMITSymax};
################################################################################################################################################################################################
################################################################################################################################################################################################

my $rout_lb_data = $profile_y - $sr_profile_y_max;
my $rout_fd_tmp = sprintf('%.0f',($profile_y - $rout_lb_data * 2) * 25.4 - 40);
my $rout_fd_data = sprintf("%d", rand($rout_fd_tmp));
if ( $rout_layer_no > 0 ) {
	foreach my $tmp (@panel_step_list) {
		#if ( $tmp !~ /set/ && $tmp !~ /edit/ && $tmp !~ /zk/ && $tmp ne "org" && $tmp ne "orig" && $tmp ne "net" && $tmp ne "drl" && $tmp ne "lp" && $tmp ne "2nd" && $tmp ne "3nd" ) {  ## by hyp, Dec 24, 2017
		if ( $tmp !~ /set/ && $tmp !~ /edit/ && $tmp !~ /zk/ && $tmp ne "org" && $tmp ne "orig" && $tmp ne "net" && $tmp ne "drl" && $tmp ne "lp" && $tmp ne "2nd" && $tmp ne "3nd" &&  $tmp ne 'kk' ) {  ## by hyp, Dec 24, 2017
			
			foreach my $tmp_drl (@drill_array) {
				if ( $tmp eq $tmp_drl ) {
					goto BBBBB;
				}	
			}
			$f->COM("open_entity,job=$job_name,type=step,name=$tmp,iconic=no");
			$f->AUX("set_group,group=$f->{COMANS}");
			$f->COM("units,type=inch");
			$f->COM("profile_to_rout,layer=ww,width=20");
			$f->COM("editor_page_close");
		}
		BBBBB:
	}
	$f->COM("open_entity,job=$job_name,type=step,name=panel,iconic=no");
	$f->AUX("set_group,group=$f->{COMANS}");
	$f->COM("units,type=inch");
	$f->COM("flatten_layer,source_layer=ww,target_layer=ww_tmp_test");
	$f->COM("clear_layers");
	$f->COM("affected_layer,mode=all,affected=no");	
	$f->COM("filter_reset,filter_name=popup");
	$f->COM("affected_layer,name=ww_tmp_test,mode=single,affected=yes");
	$f->COM("sel_copy_other,dest=layer_name,target_layer=ww_tmp_test_fd,invert=no,dx=0,dy=0,size=0,x_anchor=0,y_anchor=0,rotation=0,mirror=none");
	$f->COM("clear_layers");
	$f->COM("affected_layer,mode=all,affected=no");	
	$f->COM("affected_layer,name=ww_tmp_test_fd,mode=single,affected=yes");
	$f->COM("sel_delete");
	
	AAAAA:
	my $i = 0;
	foreach my $tmp (@rout_array) {	
		my $test_x = $sr_profile_x_max + 0.2;
		my $test_xe = $profile_x;
		my $test_y = $profile_y - $sr_profile_y_max + $rout_fd_data * 0.03937 + ($i * 0.3937);
		$f->COM("clear_layers");
		$f->COM("affected_layer,mode=all,affected=no");	
		$f->COM("affected_layer,name=ww_tmp_test_fd,mode=single,affected=yes");
		$f->COM("add_line,attributes=no,xs=$test_x,ys=$test_y,xe=$test_xe,ye=$test_y,symbol=r95,polarity=positive,bus_num_lines=0,bus_dist_by=pitch,bus_distance=0,bus_reference=left");
		$i++;
	}
	
	$f->COM("clear_layers");
	$f->COM("affected_layer,mode=all,affected=no");	
	$f->COM("affected_layer,name=ww_tmp_test_fd,mode=single,affected=yes");
	$f->COM("sel_ref_feat,layers=ww_tmp_test,use=filter,mode=touch,pads_as=shape,f_types=line\;pad\;surface\;arc\;text,polarity=positive\;negative,include_syms=,exclude_syms=");
	if ($f->{COMANS} > 0) {
		#$f->PAUSE("测试中，请点击Resume");	## hyp
		$f->COM("clear_layers");
		$f->COM("affected_layer,mode=all,affected=no");	
		$f->COM("affected_layer,name=ww_tmp_test_fd,mode=single,affected=yes");
		$f->COM("sel_delete");		
		$rout_fd_data = sprintf("%d", rand($rout_fd_tmp));

		goto AAAAA;
	} else {
		$f->COM("clear_layers");
		$f->COM("affected_layer,mode=all,affected=no");
		$f->COM("delete_layer,layer=ww_tmp_test");
		$f->COM("delete_layer,layer=ww_tmp_test_fd");
	}	
}

my $rout_layrer_nubers = scalar(@rout_array);
if ( $rout_layrer_nubers == 1 ) {
	if ( @rout_array[0] ne "pnl_rout" && @rout_array[0] ne "pnl_rout1" ) {
		&rout_layer_name_error;
		exit 0;
	}
} elsif ( $rout_layrer_nubers == 2 ) {
	if ( @rout_array[0] ne "pnl_rout1" or @rout_array[1] ne "pnl_rout2" ) {
		&rout_layer_name_error;
		exit 0;
	}
} elsif ( $rout_layrer_nubers == 3 ) {
	if ( @rout_array[0] ne "pnl_rout1" or @rout_array[1] ne "pnl_rout2" or @rout_array[2] ne "pnl_rout3" ) {
		&rout_layer_name_error;
		exit 0;
	}
}	

my $mw3_5 = MainWindow->new( -title =>"VGT");
$mw3_5->bind('<Return>' => sub{ shift->focusNext; });
$mw3_5->protocol("WM_DELETE_WINDOW", \&OnQuit);
if ( $rout_layrer_nubers == 1 ) {
	$mw3_5->geometry("400x370-800+80");
} elsif ( $rout_layrer_nubers == 2 ) {
	$mw3_5->geometry("400x400-800+80");	
} elsif ( $rout_layrer_nubers == 3 ) {
	$mw3_5->geometry("400x430-800+80");	
}	
$mw3_5->raise( );
$mw3_5->resizable(0,0);

my $CAM_frm = $mw3_5->Frame(-bg => '#9BDBDB',-borderwidth =>2,-relief => "raised",-height => 2)->pack(-side=>'top',-fill=>'x');
my $sh_log = $mw3_5->Photo('info',-file => "$images_path/sh_log.xpm");

my $image_label = $CAM_frm->Label(-image => $sh_log, -border => 1, -relief => 'solid',
                                              )->pack(-side => 'left',
                                                      -padx => 5,
                                                      -pady => 5);  
													  
$CAM_frm->Label(-text => '锣带输出    ',-font => 'charter 18 bold',-bg => '#9BDBDB')->pack();
$CAM_frm->Label(-text => '作者:dgz  Ver:2.0',-font => 'charter 10',-bg => '#9BDBDB')->pack(-side=>'right', -padx => 10);  

my $path_frm = $mw3_5->LabFrame(-label => '参数选择',-font => 'SimSun 10',-bg => '#9BDBDB',-fg => 'blue',)->pack(-side=>'top',-fill=>'both');
my $path_sel_tmp = $path_frm->Frame(-bg => '#9BDBDB')->pack(-side=>'top',-fill=>'both');
my $open_path = $path_sel_tmp->Photo('path',-file => "$images_path/OpenJob.xpm");
my $show_rout_path = "$do_rout_path";
$path_sel_tmp->LabEntry(-label => '输出目录:',
										-labelBackground => '#9BDBDB',
										-labelFont => 'SimSun 14',
										-textvariable => \$show_rout_path,
										-bg => 'white',
										-width => 40,
										-relief=>'ridge',
										-labelPack => [qw/-side left -anchor w/])->pack(-side => 'left',-padx => 3,-pady => 5);
										
#$path_sel_tmp->Button(-image => $open_path,
#                                          -command => sub {&path_sel_run;},
#                                          -width => 19,
#										  -activebackground=>'#fcc64d',
#										  -bg => '#9BDBDB',
#										  -height=> 19,
#                                         )->pack(-side => 'left',-padx => 5);	

my $output_rout_film = $mw3_5->LabFrame(-label => '锣板防呆(单位:MM)',-font => 'SimSun 10',-bg => '#9BDBDB',-fg => 'blue',)->pack(-side=>'top',-fill=>'x');
my $output_rout = $output_rout_film->Frame(-bg => '#9BDBDB')->pack(-side=>'top',-fill=>'x');
my $rout_yes = "是";
my @rout_list = ('是','否');						 
foreach my $tmp (@rout_list) {
	if ( $tmp eq "是") {
		my $rout_select1 = $output_rout->Radiobutton(-text => $tmp,
														  -variable => \$rout_yes,
														  -background => '#9BDBDB',
														  -font => 'SimSun 12',
														  -value => $tmp)->pack(-side   => "left",
																				-padx   => 0,																					
																				-pady   => 5,
																				-fill   => 'x');

	} elsif ( $tmp eq "否") {
		my $rout_select2 = $output_rout->Radiobutton(-text => $tmp,
														  -variable => \$rout_yes,
														  -background => '#9BDBDB',
														  -font => 'SimSun 12',
														  -value => $tmp)->pack(-side   => "left",
																				-padx   => 0,
																				-pady   => 5,																					
																				-fill   => 'x');																	
	}		
}
my $output_data_film = $output_rout_film->Frame(-bg => '#9BDBDB')->pack(-side=>'top',-fill=>'x');
$output_data_film->LabEntry(-label => '锣板防呆数据:',
									-labelBackground => '#9BDBDB',
									-labelFont => 'SimSun 12',
									-textvariable => \$rout_fd_data,
									-bg => 'white',
									-width => 10,
									-relief=>'ridge',
									-labelPack => [qw/-side left -anchor w/])->pack(-side => 'left',-fill=>'x',-padx=> 0,-pady   => 5); 


my $change_rout_film = $mw3_5->LabFrame(-label => '(单位:MM)',-font => 'SimSun 10',-bg => '#9BDBDB',-fg => 'blue',)->pack(-side=>'top',-fill=>'x');
my $change_rout_film1 = $change_rout_film->Frame(-bg => '#9BDBDB')->pack(-side=>'top',-fill=>'x');
$change_rout_film1->Label(-text => '重新制作锣带:',-font => 'SimSun 12',-bg => '#9BDBDB')->pack(-side => "left",-padx => 2);
my $change_yes = "否";
my @change_list = ('否','是');
foreach my $tmp (@change_list) {
	if ( $tmp eq "是") {
		our $change_select1 = $change_rout_film1->Radiobutton(-text => $tmp,
														  -variable => \$change_yes,
														  -background => '#9BDBDB',
														  -font => 'SimSun 12',
														  -value => $tmp)->pack(-side   => "left",
																				-padx   => 0,																					
																				-pady   => 3,
																				-fill   => 'x');

	} elsif ( $tmp eq "否") {
		our $change_select2 = $change_rout_film1->Radiobutton(-text => $tmp,
														  -variable => \$change_yes,
														  -background => '#9BDBDB',
														  -font => 'SimSun 12',
														  -value => $tmp)->pack(-side   => "left",
																				-padx   => 0,
																				-pady   => 3,																					
																				-fill   => 'x');																	
	}		
}

$change_select1->bind('<Button>',\&update_fun_frm);
$change_select2->bind('<Button>',\&update_fun_frm);
my $rout_1x = "";
my $rout_1y = "";
my $rout_2x = "";
my $rout_2y = "";
my $rout_3x = "";
my $rout_3y = "";
if ( $rout_layrer_nubers eq 1 ) {
	my $rout_1 = @rout_array[0];
	my $change_rout_film2 = $change_rout_film->Frame(-bg => '#9BDBDB')->pack(-side=>'top',-fill=>'x');	
	my $change_label_frm1 = $change_rout_film2->Frame(-bg => '#9BDBDB')->pack(-side=>'left',-fill=>'both');	
	my $layer_name1 = $change_label_frm1->Label(-text => "$rout_1", -width => 10, -font => 'charter 14', -height=>'1',-background => "#9BDBDB",-fg=>"blue")->pack(-side => 'left',-padx => 1);	
	my $change_data_frm1 = $change_rout_film2->Frame(-bg => '#9BDBDB')->pack(-side=>'left',-fill=>'both');
	our $rout_lab1x = $change_data_frm1->LabEntry(-label => '锣边后X:',
												  -labelBackground => '#9BDBDB',
												  -labelFont => 'SimSun 12',
												  -textvariable => \$rout_1x,
												  -bg => 'white',
												  -width => 8,
												  -relief=>'ridge',
												  -state=>"disabled",
												  -labelPack => [qw/-side left -anchor w/])->pack(-side => 'left', -padx => 5,-pady => 5);   

	our $rout_lab1y = $change_data_frm1->LabEntry(-label => '锣边后Y:',											 
										 -labelBackground => '#9BDBDB',
										 -labelFont => 'SimSun 12',
										 -textvariable => \$rout_1y,
										 -bg => 'white',
										 -width => 8,
										 -relief=>'ridge',
										 -state=>"disabled",
										 -labelPack => [qw/-side left -anchor w/])->pack(-side => 'left', -padx => 5,-pady => 5);  
} elsif ( $rout_layrer_nubers eq 2 ) {
	my $rout_1 = @rout_array[0];
	my $rout_2 = @rout_array[1];
	my $change_rout_film2 = $change_rout_film->Frame(-bg => '#9BDBDB')->pack(-side=>'top',-fill=>'x');
	my $rout_data_frm1 = $change_rout_film2->Frame(-bg => '#9BDBDB')->pack(-side=>'top',-fill=>'x');
	my $change_label_frm1 = $rout_data_frm1->Frame(-bg => '#9BDBDB')->pack(-side=>'left',-fill=>'both');	
	my $layer_name1 = $change_label_frm1->Label(-text => "$rout_1", -width => 10, -font => 'charter 14', -height=>'1',-background => "#9BDBDB",-fg=>"blue")->pack(-side => 'left',-padx => 1);	
	my $change_data_frm1 = $rout_data_frm1->Frame(-bg => '#9BDBDB')->pack(-side=>'left',-fill=>'both');
	our $rout_lab1x = $change_data_frm1->LabEntry(-label => '锣边后X:',
												  -labelBackground => '#9BDBDB',
												  -labelFont => 'SimSun 12',
												  -textvariable => \$rout_1x,
												  -bg => 'white',
												  -width => 8,
												  -relief=>'ridge',
												  -state=>"disabled",
												  -labelPack => [qw/-side left -anchor w/])->pack(-side => 'left', -padx => 5,-pady => 5);   

	our $rout_lab1y = $change_data_frm1->LabEntry(-label => '锣边后Y:',											 
										 -labelBackground => '#9BDBDB',
										 -labelFont => 'SimSun 12',
										 -textvariable => \$rout_1y,
										 -bg => 'white',
										 -width => 8,
										 -relief=>'ridge',
										 -state=>"disabled",
										 -labelPack => [qw/-side left -anchor w/])->pack(-side => 'left', -padx => 5,-pady => 5);
	my $rout_data_frm2 = $change_rout_film2->Frame(-bg => '#9BDBDB')->pack(-side=>'top',-fill=>'x');
	my $change_label_frm2 = $rout_data_frm2->Frame(-bg => '#9BDBDB')->pack(-side=>'left',-fill=>'both');	
	my $layer_name2 = $change_label_frm2->Label(-text => "$rout_2", -width => 10, -font => 'charter 14', -height=>'1',-background => "#9BDBDB",-fg=>"blue")->pack(-side => 'left',-padx => 1);	
	my $change_data_frm2 = $rout_data_frm2->Frame(-bg => '#9BDBDB')->pack(-side=>'left',-fill=>'both');
	our $rout_lab2x = $change_data_frm2->LabEntry(-label => '锣边后X:',
												  -labelBackground => '#9BDBDB',
												  -labelFont => 'SimSun 12',
												  -textvariable => \$rout_2x,
												  -bg => 'white',
												  -width => 8,
												  -relief=>'ridge',
												  -state=>"disabled",
												  -labelPack => [qw/-side left -anchor w/])->pack(-side => 'left', -padx => 5,-pady => 5);   

	our $rout_lab2y = $change_data_frm2->LabEntry(-label => '锣边后Y:',											 
										 -labelBackground => '#9BDBDB',
										 -labelFont => 'SimSun 12',
										 -textvariable => \$rout_2y,
										 -bg => 'white',
										 -width => 8,
										 -relief=>'ridge',
										 -state=>"disabled",
										 -labelPack => [qw/-side left -anchor w/])->pack(-side => 'left', -padx => 5,-pady => 5);

} elsif ( $rout_layrer_nubers eq 3 ) {
	my $rout_1 = @rout_array[0];
	my $rout_2 = @rout_array[1];
	my $rout_3 = @rout_array[2];
	my $change_rout_film2 = $change_rout_film->Frame(-bg => '#9BDBDB')->pack(-side=>'top',-fill=>'x');
	my $rout_data_frm1 = $change_rout_film2->Frame(-bg => '#9BDBDB')->pack(-side=>'top',-fill=>'x');
	my $change_label_frm1 = $rout_data_frm1->Frame(-bg => '#9BDBDB')->pack(-side=>'left',-fill=>'both');	
	my $layer_name1 = $change_label_frm1->Label(-text => "$rout_1", -width => 10, -font => 'charter 14', -height=>'1',-background => "#9BDBDB",-fg=>"blue")->pack(-side => 'left',-padx => 1);	
	my $change_data_frm1 = $rout_data_frm1->Frame(-bg => '#9BDBDB')->pack(-side=>'left',-fill=>'both');
	our $rout_lab1x = $change_data_frm1->LabEntry(-label => '锣边后X:',
												  -labelBackground => '#9BDBDB',
												  -labelFont => 'SimSun 12',
												  -textvariable => \$rout_1x,
												  -bg => 'white',
												  -width => 8,
												  -relief=>'ridge',
												  -state=>"disabled",
												  -labelPack => [qw/-side left -anchor w/])->pack(-side => 'left', -padx => 5,-pady => 5);   

	our $rout_lab1y = $change_data_frm1->LabEntry(-label => '锣边后Y:',											 
										 -labelBackground => '#9BDBDB',
										 -labelFont => 'SimSun 12',
										 -textvariable => \$rout_1y,
										 -bg => 'white',
										 -width => 8,
										 -relief=>'ridge',
										 -state=>"disabled",
										 -labelPack => [qw/-side left -anchor w/])->pack(-side => 'left', -padx => 5,-pady => 5);
	my $rout_data_frm2 = $change_rout_film2->Frame(-bg => '#9BDBDB')->pack(-side=>'top',-fill=>'x');
	my $change_label_frm2 = $rout_data_frm2->Frame(-bg => '#9BDBDB')->pack(-side=>'left',-fill=>'both');	
	my $layer_name2 = $change_label_frm2->Label(-text => "$rout_2", -width => 10, -font => 'charter 14', -height=>'1',-background => "#9BDBDB",-fg=>"blue")->pack(-side => 'left',-padx => 1);	
	my $change_data_frm2 = $rout_data_frm2->Frame(-bg => '#9BDBDB')->pack(-side=>'left',-fill=>'both');
	our $rout_lab2x = $change_data_frm2->LabEntry(-label => '锣边后X:',
												  -labelBackground => '#9BDBDB',
												  -labelFont => 'SimSun 12',
												  -textvariable => \$rout_2x,
												  -bg => 'white',
												  -width => 8,
												  -relief=>'ridge',
												  -state=>"disabled",
												  -labelPack => [qw/-side left -anchor w/])->pack(-side => 'left', -padx => 5,-pady => 5);   

	our $rout_lab2y = $change_data_frm2->LabEntry(-label => '锣边后Y:',											 
										 -labelBackground => '#9BDBDB',
										 -labelFont => 'SimSun 12',
										 -textvariable => \$rout_2y,
										 -bg => 'white',
										 -width => 8,
										 -relief=>'ridge',
										 -state=>"disabled",
										 -labelPack => [qw/-side left -anchor w/])->pack(-side => 'left', -padx => 5,-pady => 5);
	
	my $rout_data_frm3 = $change_rout_film2->Frame(-bg => '#9BDBDB')->pack(-side=>'top',-fill=>'x');
	my $change_label_frm3 = $rout_data_frm3->Frame(-bg => '#9BDBDB')->pack(-side=>'left',-fill=>'both');	
	my $layer_name3 = $change_label_frm3->Label(-text => "$rout_3", -width => 10, -font => 'charter 14', -height=>'1',-background => "#9BDBDB",-fg=>"blue")->pack(-side => 'left',-padx => 1);	
	my $change_data_frm3 = $rout_data_frm3->Frame(-bg => '#9BDBDB')->pack(-side=>'left',-fill=>'both');
	our $rout_lab3x = $change_data_frm3->LabEntry(-label => '锣边后X:',
												  -labelBackground => '#9BDBDB',
												  -labelFont => 'SimSun 12',
												  -textvariable => \$rout_3x,
												  -bg => 'white',
												  -width => 8,
												  -relief=>'ridge',
												  -state=>"disabled",
												  -labelPack => [qw/-side left -anchor w/])->pack(-side => 'left', -padx => 5,-pady => 5);   

	our $rout_lab3y = $change_data_frm3->LabEntry(-label => '锣边后Y:',											 
										 -labelBackground => '#9BDBDB',
										 -labelFont => 'SimSun 12',
										 -textvariable => \$rout_3y,
										 -bg => 'white',
										 -width => 8,
										 -relief=>'ridge',
										 -state=>"disabled",
										 -labelPack => [qw/-side left -anchor w/])->pack(-side => 'left', -padx => 5,-pady => 5);
										 
}	
	
my $button_frm12 = $mw3_5->Frame(-bg => '#9BDBDB')->pack(-side=>'bottom',-fill=>'x'); 
my $b_ok = $button_frm12->Button(-text=>'确认',
										-activebackground=>'green',
										-height => 2, -bg => '#9BDBDB',
										-font=> 'charter 14',-width=>'8',
										-command=>sub{&run_output_rout;exit;})						
										->pack(-side=>'left',-padx=>2,-pady=>2);									  
my $b_close = $button_frm12->Button(-text=>'退出',
											-activebackground=>'red',
											-height => 2, -bg => '#9BDBDB',
											-font=> 'charter 14',-width=>'8',
											-command=>sub{exit 0;})
											->pack(-side=>'right',-padx=>2,-pady=>2);
MainLoop;										

###################################################################################################################################################################################################
sub OnQuit {
	my $ans = $mw3_5->messageBox(-icon => 'question',-message => '你确定要退出吗？',-title => 'quit',-type => 'YesNo');
	return if $ans eq "No";
	exit;
}

#sub path_sel_run {
#	my $path_dir = $path_sel_tmp->chooseDirectory(-initialdir => $target_dir);
#	if ( $path_dir eq "" ) {
#		$path_tmp = $path_tmp;
#	} else {
#		$path_tmp = $path_dir;
#	}
#	$path_sel_tmp->configure();
#}

sub update_fun_frm {
	if ( $change_yes eq "是" ) {
		if ( $rout_layrer_nubers eq 1 ) {
			#if ( $bot_signal_layer eq 4 ) {
			#	$rout_lab1x->configure(-state=>"disabled",);
			#	$rout_lab1y->configure(-state=>"disabled",);
			#} else {			
			$rout_lab1x->configure(-state=>"normal");
			$rout_lab1y->configure(-state=>"normal");
			#}
		} elsif ( $rout_layrer_nubers eq 2 ) {
			$rout_lab1x->configure(-state=>"normal",);
			$rout_lab1y->configure(-state=>"normal",);
			$rout_lab2x->configure(-state=>"normal",);
			$rout_lab2y->configure(-state=>"normal",);
		} elsif ( $rout_layrer_nubers eq 3 ) {
			$rout_lab1x->configure(-state=>"normal",);
			$rout_lab1y->configure(-state=>"normal",);
			$rout_lab2x->configure(-state=>"normal",);
			$rout_lab2y->configure(-state=>"normal",);
			$rout_lab3x->configure(-state=>"normal",);
			$rout_lab3y->configure(-state=>"normal",);
		}
	} elsif ( $change_yes eq "否" ) {
		if ( $rout_layrer_nubers eq 1 ) {					
			$rout_lab1x->configure(-state=>"disabled",);
			$rout_lab1y->configure(-state=>"disabled",);
		} elsif ( $rout_layrer_nubers eq 2 ) {
			$rout_lab1x->configure(-state=>"disabled",);
			$rout_lab1y->configure(-state=>"disabled",);
			$rout_lab2x->configure(-state=>"disabled",);
			$rout_lab2y->configure(-state=>"disabled",);
		} elsif ( $rout_layrer_nubers eq 3 ) {
			$rout_lab1x->configure(-state=>"disabled",);
			$rout_lab1y->configure(-state=>"disabled",);
			$rout_lab2x->configure(-state=>"disabled",);
			$rout_lab2y->configure(-state=>"disabled",);
			$rout_lab3x->configure(-state=>"disabled",);
			$rout_lab3y->configure(-state=>"disabled",);
		}		
	}
}
###################################################################################################################################################################################################

sub run_output_rout {
	my $rout_lb_x_inn = "";
	my $rout_lb_y_inn = "";
	if ( $change_yes eq "是" ) {
		if ( $rout_layrer_nubers eq 1 ) {
			if ( $rout_1x eq "" or $rout_1y eq "" ) {
				if ( $bot_signal_layer ne 4 ) {
					&run_message_rout_bk_data;
					$button_frm12->withdraw;
				} else {
					if ( $rout_1x eq "" && $rout_1y ne "" ) {
						&run_message_rout_bk_data;
						$button_frm12->withdraw;
					} elsif ( $rout_1x ne "" && $rout_1y eq "" ) {
						&run_message_rout_bk_data;
						$button_frm12->withdraw;
					}
				}
			} 
		} elsif ( $rout_layrer_nubers eq 2 ) {
			if ( $rout_1x eq "" or $rout_1y eq "" or $rout_2x eq "" or $rout_2y eq "") {
				&run_message_rout_bk_data;
				$button_frm12->withdraw;
			}
		} elsif ( $rout_layrer_nubers eq 3 ) {
			if ( $rout_1x eq "" or $rout_1y eq "" or $rout_2x eq "" or $rout_2y eq "" or $rout_3x eq "" or $rout_3y eq "" ) {
				&run_message_rout_bk_data;
				$button_frm12->withdraw;
			}
		}
		if ( $rout_layer_no eq 1 ) {
			$rout_lb_x_inn = $rout_1x;
			$rout_lb_y_inn = $rout_1y;			
		} elsif ( $rout_layer_no eq 2 ) {
			if ( $rout_1x > $rout_2x && $rout_1y > $rout_2y ) {
				$rout_lb_x_inn = $rout_2x;
				$rout_lb_y_inn = $rout_2y;						
			} else {
				&run_message_data_error;
				$button_frm12->withdraw;
			}
		} elsif ( $rout_layer_no eq 3 ) {
			if ( $rout_1x > $rout_2x && $rout_1y > $rout_2y ) {
				if ( $rout_2x > $rout_3x && $rout_2y > $rout_3y ) {
					$rout_lb_x_inn = $rout_3x;
					$rout_lb_y_inn = $rout_3y;	
				} else {
					&run_message_data_error;
					$button_frm12->withdraw;
				}				
			} else {
				&run_message_data_error;
				$button_frm12->withdraw;
			}
		}
	}

	$mw3_5->iconify();
	#unlink glob("$ENV{INCAM_TMP}/*.txt");
	
	my @bk_drll_layer = ();
	foreach my $tmp_drll (@drill_array) {
		if ( $tmp_drll =~ "^inn" ) {
			if ( $tmp_drll ne "inn" ) {
				my $tmp_name_l = length($tmp_drll);
				if ( $tmp_name_l == 5 ) {
					$drl_layer_top = substr($tmp_drll, -2,1);
					$drl_layer_bot = substr($tmp_drll, -1,1);				
				} elsif ( $tmp_name_l == 6 ) {
					$drl_layer_top = substr($tmp_drll, -3,1);
					$drl_layer_bot = substr($tmp_drll, -2,2);				
				} elsif ( $tmp_name_l == 7 ) {
					$drl_layer_top = substr($tmp_drll, -4,2);
					$drl_layer_bot = substr($tmp_drll, -2,2);			
				}
				my $drl_layer_space = $drl_layer_bot - $drl_layer_top;
				if ( $drl_layer_space > 1 ) {				
					push(@bk_drll_layer,$tmp_drll);
				}
			}
		}
	}

	my $bk_layer_no = scalar(@bk_drll_layer);
	my $bk_all_no = $bk_layer_no + 1;
	if ( $rout_layer_no ne $bk_all_no ) {
		&run_message_rout_bk_no;
		exit 0;
	}
	
	my 	$inn_bk_1 = "";
	my 	$inn_bk_2 = "";
	if ( $bk_layer_no == 1 ) {
		$inn_bk_1 = @bk_drll_layer[0];
	} elsif ( $bk_layer_no == 2 ) {
		my $layer_bk1_data = substr(@bk_drll_layer[0], -2,2);
		my $layer_bk2_data = substr(@bk_drll_layer[1], -2,2);
		if ( $layer_bk1_data > $layer_bk2_data ) {
			$inn_bk_1 = @bk_drll_layer[0];
			$inn_bk_2 = @bk_drll_layer[1];
		} else {
			$inn_bk_1 = @bk_drll_layer[1];
			$inn_bk_2 = @bk_drll_layer[0];
		}
	} elsif ( $bk_layer_no > 2 ) {
		&run_message_rout_bk_no;
		exit 0;
	}
	$f->COM("open_entity,job=$job_name,type=step,name=panel,iconic=no");
	$f->COM("set_step,name=panel");
	$f->AUX("set_group,group=$f->{COMANS}");
	$f->COM("units,type=inch");
	
	if ( $change_yes eq "是" ) {
		my $m = 0;
		my $polarity = "";
		foreach my $tmp (@inn_lay_array) {
			my $polarity_tmp = @inn_lay_polarity[$m];
			if ( $bot_signal_layer eq 4 ) {
				if ( $polarity_tmp eq "negative" ) {
					$polarity = "negative";
				} else {
					$polarity = "positive";
				}
			} else {
				$polarity = $polarity_tmp;
			}
			$f->COM("clear_layers");
			$f->COM("affected_layer,mode=all,affected=no");	
			$f->COM("filter_reset,filter_name=popup");			
			$f->COM("affected_layer,name=$tmp,mode=single,affected=yes");
			$f->COM("filter_set,filter_name=popup,update_popup=no,include_syms=sh-rout-con");
			$f->COM("filter_area_strt");	
			$f->COM("filter_area_end,layer=,filter_name=popup,operation=select,area_type=none,inside_area=no,intersect_area=no,lines_only=no,ovals_only=no,min_len=0,max_len=0,min_angle=0,max_angle=0");
			if ( $f->{COMANS} > 0 ) {
				$f->COM("sel_delete");	
			}
			my $add_pad_x1 = "";
			my $add_pad_x2 = "";
			my $add_pad_x3 = "";
			my $add_pad_x4 = "";
			my $add_pad_y1 = "";
			my $add_pad_y2 = "";
			my $add_pad_y3 = "";
			my $add_pad_y4 = "";
			if ( $bot_signal_layer eq 4 ) {
				if ( $rout_1x eq "" && $rout_1y eq "" ) {
					$add_pad_x1 = 0;
					$add_pad_x2 = 0;
					$add_pad_x3 = $profile_x;
					$add_pad_x4 = $profile_x;
					$add_pad_y1 = 0;
					$add_pad_y2 = $profile_y;
					$add_pad_y3 = $profile_y;
					$add_pad_y4 = 0;
				} elsif ( $rout_1x ne "" && $rout_1y ne "" ) {
					$add_pad_x1 = $sr_profile_x_min - $rout_lb_x_inn * 0.5 * 0.03937;
					$add_pad_x2 = $sr_profile_x_min - $rout_lb_x_inn * 0.5 * 0.03937;
					$add_pad_x3 = $sr_profile_x_max + $rout_lb_x_inn * 0.5 * 0.03937;
					$add_pad_x4 = $sr_profile_x_max + $rout_lb_x_inn * 0.5 * 0.03937;
					$add_pad_y1 = $sr_profile_y_min - $rout_lb_y_inn * 0.5 * 0.03937;
					$add_pad_y2 = $sr_profile_y_max + $rout_lb_y_inn * 0.5 * 0.03937;
					$add_pad_y3 = $sr_profile_y_max + $rout_lb_y_inn * 0.5 * 0.03937;
					$add_pad_y4 = $sr_profile_y_min - $rout_lb_y_inn * 0.5 * 0.03937;
				}
			} else {
				$add_pad_x1 = $sr_profile_x_min - $rout_lb_x_inn * 0.5 * 0.03937;
				$add_pad_x2 = $sr_profile_x_min - $rout_lb_x_inn * 0.5 * 0.03937;
				$add_pad_x3 = $sr_profile_x_max + $rout_lb_x_inn * 0.5 * 0.03937;
				$add_pad_x4 = $sr_profile_x_max + $rout_lb_x_inn * 0.5 * 0.03937;
				$add_pad_y1 = $sr_profile_y_min - $rout_lb_y_inn * 0.5 * 0.03937;
				$add_pad_y2 = $sr_profile_y_max + $rout_lb_y_inn * 0.5 * 0.03937;
				$add_pad_y3 = $sr_profile_y_max + $rout_lb_y_inn * 0.5 * 0.03937;
				$add_pad_y4 = $sr_profile_y_min - $rout_lb_y_inn * 0.5 * 0.03937;
			}			
			$f->COM("add_pad,attributes=no,x=$add_pad_x1,y=$add_pad_y1,symbol=sh-rout-con,polarity=$polarity,angle=0,mirror=no,nx=1,ny=1,dx=0,dy=0,xscale=1,yscale=1");			
			$f->COM("add_pad,attributes=no,x=$add_pad_x2,y=$add_pad_y2,symbol=sh-rout-con,polarity=$polarity,angle=90,mirror=no,nx=1,ny=1,dx=0,dy=0,xscale=1,yscale=1");
			$f->COM("add_pad,attributes=no,x=$add_pad_x3,y=$add_pad_y3,symbol=sh-rout-con,polarity=$polarity,angle=180,mirror=no,nx=1,ny=1,dx=0,dy=0,xscale=1,yscale=1");
			$f->COM("add_pad,attributes=no,x=$add_pad_x4,y=$add_pad_y4,symbol=sh-rout-con,polarity=$polarity,angle=270,mirror=no,nx=1,ny=1,dx=0,dy=0,xscale=1,yscale=1");
			$m++;
		}
	}
	
	my $i = 0;
	foreach my $tmp (@rout_array) {	
		$f->COM("units,type=inch");

		if ( $change_yes eq "是" ) {
			my $rout_lb_x = "";
			my $rout_lb_y = "";
			if ( $rout_layer_no == 1 ) {
				$rout_lb_x = $rout_1x;
				$rout_lb_y = $rout_1y;			
			} elsif ( $rout_layer_no == 2 ) {
				if ( $i == 0 ) {
					$rout_lb_x = $rout_1x;
					$rout_lb_y = $rout_1y;				
				} elsif ( $i == 1 ) {
					$rout_lb_x = $rout_2x;
					$rout_lb_y = $rout_2y;				
				}
			} elsif ( $rout_layer_no == 3 ) {
				if ( $i == 0 ) {
					$rout_lb_x = $rout_1x;
					$rout_lb_y = $rout_1y;				
				} elsif ( $i == 1 ) {
					$rout_lb_x = $rout_2x;
					$rout_lb_y = $rout_2y;				
				} elsif ( $i == 2 ) {
					$rout_lb_x = $rout_3x;
					$rout_lb_y = $rout_3y;				
				}
			}
			
			$f->COM("clear_layers");
			$f->COM("affected_layer,mode=all,affected=no");	
			$f->COM("filter_reset,filter_name=popup");			
			$f->COM("affected_layer,name=$tmp,mode=single,affected=yes");
			
			$f->COM("filter_set,filter_name=popup,update_popup=no,exclude_syms=r123.031");
			$f->COM("filter_area_strt");
			$f->COM("filter_area_end,layer=,filter_name=popup,operation=select,area_type=none,inside_area=no,intersect_area=no,lines_only=no,ovals_only=no,min_len=0,max_len=0,min_angle=0,max_angle=0");
			if ( $f->{COMANS} > 0 ) {
				$f->COM("sel_delete");	
			}
			
			my $lb_x_1 = "";
			my $lb_x_2 = "";
			my $lb_x_3 = "";
			my $lb_x_4 = "";
			my $lb_x_5 = "";
			my $lb_y_1 = "";
			my $lb_y_2 = "";
			my $lb_y_3 = "";
			my $lb_y_4 = "";
			my $lb_y_5 = "";
			if ( $bot_signal_layer eq 4 ) {
				if ( $rout_1x eq "" && $rout_1y eq "" ) {
					$lb_x_1 = 0;
					$lb_x_2 = 0 + 0.19685;
					$lb_x_3 = $profile_x - 0.19685;
					$lb_x_4 = $profile_x;
					$lb_x_5 = $profile_x - 0.07874;
					$lb_y_1 = 0;
					$lb_y_2 = 0 + 0.19685;
					$lb_y_3 = $profile_y - 0.19685;
					$lb_y_4 = $profile_y;
					$lb_y_5 = $profile_y - $sr_profile_y_max + $rout_fd_data * 0.03937 + ($i * 0.3937);
				} elsif ( $rout_1x ne "" && $rout_1y ne "" ) {
					$lb_x_1 = $sr_profile_x_min - $rout_lb_x * 0.03937 * 0.5;
					$lb_x_2 = $sr_profile_x_min - $rout_lb_x * 0.03937 * 0.5 + 0.19685;
					$lb_x_3 = $sr_profile_x_max + $rout_lb_x * 0.03937 * 0.5 - 0.19685;
					$lb_x_4 = $sr_profile_x_max + $rout_lb_x * 0.03937 * 0.5;
					$lb_x_5 = $sr_profile_x_max + $rout_lb_x * 0.03937 * 0.5 - 0.047244;
					$lb_y_1 = $sr_profile_y_min - $rout_lb_y * 0.03937 * 0.5;
					$lb_y_2 = $sr_profile_y_min - $rout_lb_y * 0.03937 * 0.5 + 0.19685;
					$lb_y_3 = $profile_y - ($profile_y - $sr_profile_y_max) + $rout_lb_y * 0.03937 * 0.5 - 0.19685;
					$lb_y_4 = $profile_y - ($profile_y - $sr_profile_y_max) + $rout_lb_y * 0.03937 * 0.5;
					$lb_y_5 = $profile_y - $sr_profile_y_max + $rout_fd_data * 0.03937 + ($i * 0.3937);				
				}
			} else {
				$lb_x_1 = $sr_profile_x_min - $rout_lb_x * 0.03937 * 0.5;
				$lb_x_2 = $sr_profile_x_min - $rout_lb_x * 0.03937 * 0.5 + 0.19685;
				$lb_x_3 = $sr_profile_x_max + $rout_lb_x * 0.03937 * 0.5 - 0.19685;
				$lb_x_4 = $sr_profile_x_max + $rout_lb_x * 0.03937 * 0.5;
				$lb_x_5 = $sr_profile_x_max + $rout_lb_x * 0.03937 * 0.5 - 0.047244;
				$lb_y_1 = $sr_profile_y_min - $rout_lb_y * 0.03937 * 0.5;
				$lb_y_2 = $sr_profile_y_min - $rout_lb_y * 0.03937 * 0.5 + 0.19685;
				$lb_y_3 = $profile_y - ($profile_y - $sr_profile_y_max) + $rout_lb_y * 0.03937 * 0.5 - 0.19685;
				$lb_y_4 = $profile_y - ($profile_y - $sr_profile_y_max) + $rout_lb_y * 0.03937 * 0.5;
				$lb_y_5 = $profile_y - $sr_profile_y_max + $rout_fd_data * 0.03937 + ($i * 0.3937);
			}
			$f->COM("add_polyline_strt");
			$f->COM("add_polyline_xy,x=$lb_x_1,y=$lb_y_4");
			$f->COM("add_polyline_xy,x=$lb_x_1,y=$lb_y_2");			
			$f->COM("add_polyline_crv,xc=$lb_x_2,yc=$lb_y_2,xe=$lb_x_2,ye=$lb_y_1,cw=no");
			$f->COM("add_polyline_xy,x=$lb_x_3,y=$lb_y_1");
			$f->COM("add_polyline_crv,xc=$lb_x_3,yc=$lb_y_2,xe=$lb_x_4,ye=$lb_y_2,cw=no");

			$f->COM("add_polyline_xy,x=$lb_x_4,y=$lb_y_3");
			$f->COM("add_polyline_crv,xc=$lb_x_3,yc=$lb_y_3,xe=$lb_x_3,ye=$lb_y_4,cw=no");
			$f->COM("add_polyline_xy,x=$lb_x_2,y=$lb_y_4");
			$f->COM("add_polyline_crv,xc=$lb_x_2,yc=$lb_y_3,xe=$lb_x_1,ye=$lb_y_3,cw=no");
			$f->COM("add_polyline_end,attributes=no,symbol=r94.495,polarity=positive");
			
			$f->COM("add_polyline_strt");
			$f->COM("add_polyline_xy,x=$lb_x_4,y=$lb_y_5");
			$f->COM("add_polyline_xy,x=$lb_x_5,y=$lb_y_5");
			$f->COM("add_polyline_end,attributes=no,symbol=r94.495,polarity=positive");
			$f->COM("sel_net_feat,operation=select,x=$lb_x_1,y=$lb_y_2,tol=120");
			$f->COM("chain_add,layer=$tmp,chain=1,size=0.094488,comp=right,feed=25,chng_direction=0");
		} 
		my $inn_layer = "";
		if ( $rout_layrer_nubers == 1 ) {
			$inn_layer = "inn";
		} elsif ( $rout_layrer_nubers == 2 ) {
			if ( $i == 0 ) {
				$inn_layer = "$inn_bk_1";
			} elsif ( $i == 1 ) {
				$inn_layer = "inn";
			}
		} elsif ( $rout_layrer_nubers == 3 ) { 			
			if ( $tmp eq "pnl_rout1" ) {
				$inn_layer = "$inn_bk_1";
			} elsif ( $tmp eq "pnl_rout2" ) {
				$inn_layer = "$inn_bk_2";
			} elsif ( $tmp eq "pnl_rout3" ) { 
				$inn_layer = "inn";
			}
		}
		
		$f->COM("clear_layers");
		$f->COM("affected_layer,mode=all,affected=no");			
		$f->COM("filter_reset,filter_name=popup");
		$f->COM("affected_layer,name=$tmp,mode=single,affected=yes");
		$f->COM("units,type=inch");
		$f->COM("filter_set,filter_name=popup,update_popup=no,include_syms=r123.031");		
		$f->COM("filter_area_strt");
		$f->COM("filter_area_end,layer=,filter_name=popup,operation=select,area_type=none,inside_area=no,intersect_area=no,lines_only=no,ovals_only=no,min_len=0,max_len=0,min_angle=0,max_angle=0");
		if ( $f->{COMANS} eq 0 ) {	
			$f->INFO(entity_type => 'layer',
					 entity_path => "$job_name/panel/$inn_layer",
					   data_type => 'EXISTS');
			if ( $f->{doinfo}{gEXISTS} eq "yes" ) {
				$f->COM("clear_layers");
				$f->COM("affected_layer,mode=all,affected=no");	
				$f->COM("filter_reset,filter_name=popup");			
				$f->COM("affected_layer,name=$inn_layer,mode=single,affected=yes");
				$f->COM("units,type=inch");
				$f->COM("filter_set,filter_name=popup,update_popup=no,include_syms=r123.031");
				$f->COM("filter_area_strt");
				$f->COM("filter_area_end,layer=,filter_name=popup,operation=select,area_type=none,inside_area=no,intersect_area=no,lines_only=no,ovals_only=no,min_len=0,max_len=0,min_angle=0,max_angle=0");
				if ( $f->{COMANS} > 0 ) {
					$f->COM("sel_copy_other,dest=layer_name,target_layer=$tmp,invert=no,dx=0,dy=0,size=0,x_anchor=0,y_anchor=0,rotation=0,mirror=none");
					$f->COM("filter_reset,filter_name=popup");	
				} else {
					&run_message_rout_bk;
					exit 0;
				}
			}
		}

		$f->COM("clear_layers");
		$f->COM("affected_layer,mode=all,affected=no");	
		$f->COM("filter_reset,filter_name=popup");			
		$f->COM("affected_layer,name=$tmp,mode=single,affected=yes");
		
		$f->COM("info, out_file=/tmp/$job_name.$i.txt,args= -t layer -e $job_name/panel/$tmp -m script -d FEATURES");	
		my @rout_tmp_list1 = ();
		my @bk_tmp_list1 = ();
		open(file1,"</tmp/$job_name.$i.txt");
		chomp;
		while($tmp1_txt = <file1> ) {
			if ($tmp1_txt =~ /#L/i) {
				print $tmp1_txt;
				push(@rout_tmp_list1, $tmp1_txt);
			} elsif ( $tmp1_txt =~ /#P/i ) {
				print $tmp1_txt;
				push(@bk_tmp_list1, $tmp1_txt);
			}
		}				
		close(file1);

		my @tmp1_routx_tmp =();
		
		my @bk_tmp_list2 = map{$_->[-1]} sort {$b->[0] <=> $a->[0]} map {[(split)[1],$_]} @bk_tmp_list1;
		foreach my $tmp_bk (@bk_tmp_list2) {
			my @tmp_list = split(/ /,$tmp_bk);
			my $tmp_1x = $tmp_list[1];
			push (@tmp1_routx_tmp, $tmp_1x);				
		}
		
		$f->INFO(entity_type => 'layer',
				 entity_path => "$job_name/panel/$tmp",
				   data_type => 'LIMITS');
		my $rout_x_max = $f->{doinfo}{gLIMITSxmax};
		my $bk_rout_x = @tmp1_routx_tmp[0];
		my $bk_x = sprintf('%.3f',($rout_x_max - $bk_rout_x - 0.047244) * 25.4);
	
		if ( $rout_yes eq "是" ) {	
			my @rout_tmp_list2 = ();			
			foreach my $tmp_rout (@rout_tmp_list1) {
				my @tmp_list = split(/ /,$tmp_rout);
				if ( $tmp_list[2] eq $tmp_list[4]) {
					my $rout_tmp_list_file = "$tmp_list[1] $tmp_list[2] $tmp_list[3] $tmp_list[4]";
					push (@rout_tmp_list2, $rout_tmp_list_file);	
				}
			}
			my @rout_tmp_list3 = map{$_->[-1]} sort {$b->[0] <=> $a->[0]} map {[(split)[1],$_]} @rout_tmp_list2;
			my @tmp1_rout1x_list = ();
			my @tmp1_rout1y_list = ();
			my @tmp1_rout2x_list = ();
			my @tmp1_rout2y_list = ();
			foreach my $tmp_rout (@rout_tmp_list3) {
				my @tmp_list = split(/ /,$tmp_rout);
				my $tmp_1x = $tmp_list[0];
				push (@tmp1_rout1x_list, $tmp_1x);				 
				my $tmp_1y = $tmp_list[1];
				push (@tmp1_rout1y_list, $tmp_1y);			 
				my $tmp_2x = $tmp_list[2];
				push (@tmp1_rout2x_list, $tmp_2x);
				my $tmp_2y = $tmp_list[3];
				push (@tmp1_rout2y_list, $tmp_2y);
			}				 
			my $sel_rout_1x = @tmp1_rout1x_list[1] - 0.1;			 
			my $sel_rout_1y = @tmp1_rout1y_list[1] - 0.1;				 
			my $sel_rout_2x = @tmp1_rout2x_list[1] + 0.1;			 
			my $sel_rout_2y = @tmp1_rout2y_list[1] + 0.1;
			my $move_rout_tmp = $rout_lb_data + $rout_fd_data * 0.03937 - @tmp1_rout1y_list[1] + ($i * 0.3937); 
			
			$f->COM("filter_reset,filter_name=popup");	
			$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=line");
			$f->COM("filter_area_strt");
			$f->COM("filter_area_xy,x=$sel_rout_1x,y=$sel_rout_1y");
			$f->COM("filter_area_xy,x=$sel_rout_2x,y=$sel_rout_2y");
			$f->COM("filter_area_end,layer=,filter_name=popup,operation=select,area_type=rectangle,inside_area=yes,intersect_area=no,lines_only=no,ovals_only=no,min_len=0,max_len=0,min_angle=0,max_angle=0");
			if ( $f->{COMANS} eq 1 ) {
				$f->COM("sel_move,dx=0,dy=$move_rout_tmp");
			} else {
				&run_message_rout_fd;
				exit 0;
			}	
		}
	
		$f->COM("clear_layers");
		$f->COM("affected_layer,mode=all,affected=no");	
		$f->COM("filter_reset,filter_name=popup");	
		$f->INFO(entity_type => 'layer',
				 entity_path => "$job_name/panel/$tmp\_s",
				   data_type => 'EXISTS');
		if ( $f->{doinfo}{gEXISTS} eq "yes" ) {
			$f->COM("clear_layers");
			$f->COM("affected_layer,mode=all,affected=no");	
			$f->COM("affected_layer,name=$tmp\_s,mode=single,affected=yes");
			$f->COM("sel_delete");
		} else {
			$f->COM("matrix_add_layer,job=$job_name,matrix=matrix,layer=$tmp\_s,context=board,type=rout,polarity=positive");
		}
#####################################################################################################################################################################################
		
		$f->COM("clear_layers");
		$f->COM("affected_layer,mode=all,affected=no");	
		$f->COM("affected_layer,name=$tmp,mode=single,affected=yes");
		
		$f->COM("sel_copy_other,dest=layer_name,target_layer=$tmp\_s,invert=no,dx=0,dy=0,size=0,x_anchor=0,y_anchor=0,rotation=0,mirror=none");
		$f->COM("clear_layers");
		$f->COM("affected_layer,mode=all,affected=no");				
		$f->COM("affected_layer,name=$tmp\_s,mode=single,affected=yes");		
		$f->COM("filter_reset,filter_name=popup");
		$f->COM("filter_set,filter_name=popup,update_popup=no,exclude_syms=r123.031");
		$f->COM("filter_area_strt");
		$f->COM("filter_area_end,layer=,filter_name=popup,operation=select,area_type=none,inside_area=no,intersect_area=no,lines_only=no,ovals_only=no,min_len=0,max_len=0,min_angle=0,max_angle=0");
		if ( $f->{COMANS} > 0 ) {
			$f->COM("sel_delete");	
		}
		my $rout_lb_x = "";
		my $rout_lb_y = "";
		my $lb_x_1 = "";
		my $lb_x_2 = "";
		my $lb_x_3 = "";
		my $lb_x_4 = "";
		my $lb_x_5 = "";
		my $lb_y_1 = "";
		my $lb_y_2 = "";
		my $lb_y_3 = "";
		my $lb_y_4 = "";
		my $lb_y_5 = "";
		if ( $change_yes eq "是" ) {
			
			if ( $rout_layer_no == 1 ) {
				$rout_lb_x = $rout_1x;
				$rout_lb_y = $rout_1y;			
			} elsif ( $rout_layer_no == 2 ) {
				if ( $i == 0 ) {
					$rout_lb_x = $rout_1x;
					$rout_lb_y = $rout_1y;				
				} elsif ( $i == 1 ) {
					$rout_lb_x = $rout_2x;
					$rout_lb_y = $rout_2y;				
				}
			} elsif ( $rout_layer_no == 3 ) {
				if ( $i == 0 ) {
					$rout_lb_x = $rout_1x;
					$rout_lb_y = $rout_1y;				
				} elsif ( $i == 1 ) {
					$rout_lb_x = $rout_2x;
					$rout_lb_y = $rout_2y;				
				} elsif ( $i == 2 ) {
					$rout_lb_x = $rout_3x;
					$rout_lb_y = $rout_3y;				
				}
			}
			
			if ( $bot_signal_layer eq 4 ) {
				if ( $rout_1x eq "" && $rout_1y eq "" ) {
					$lb_x_1 = 0;
					$lb_x_2 = 0 + 0.19685;
					$lb_x_3 = $profile_x - 0.19685;
					$lb_x_4 = $profile_x;
					$lb_x_5 = $profile_x - 0.07874;
					$lb_y_1 = 0;
					$lb_y_2 = 0 + 0.19685;
					$lb_y_3 = $profile_y - 0.19685;
					$lb_y_4 = $profile_y;
					$lb_y_5 = $profile_y - $sr_profile_y_max + $rout_fd_data * 0.03937 + ($i * 0.3937);
				} elsif ( $rout_1x ne "" && $rout_1y ne "" ) {
					$lb_x_1 = $sr_profile_x_min - $rout_lb_x * 0.03937 * 0.5;
					$lb_x_2 = $sr_profile_x_min - $rout_lb_x * 0.03937 * 0.5 + 0.19685;
					$lb_x_3 = $sr_profile_x_max + $rout_lb_x * 0.03937 * 0.5 - 0.19685;
					$lb_x_4 = $sr_profile_x_max + $rout_lb_x * 0.03937 * 0.5;
					$lb_x_5 = $sr_profile_x_max + $rout_lb_x * 0.03937 * 0.5 - 0.07874;
					$lb_y_1 = $sr_profile_y_min - $rout_lb_y * 0.03937 * 0.5;
					$lb_y_2 = $sr_profile_y_min - $rout_lb_y * 0.03937 * 0.5 + 0.19685;
					$lb_y_3 = $profile_y - ($profile_y - $sr_profile_y_max) + $rout_lb_y * 0.03937 * 0.5 - 0.19685;
					$lb_y_4 = $profile_y - ($profile_y - $sr_profile_y_max) + $rout_lb_y * 0.03937 * 0.5;
					$lb_y_5 = $profile_y - $sr_profile_y_max + $rout_fd_data * 0.03937 + ($i * 0.3937);				
				}
			} else {
				$lb_x_1 = $sr_profile_x_min - $rout_lb_x * 0.03937 * 0.5;
				$lb_x_2 = $sr_profile_x_min - $rout_lb_x * 0.03937 * 0.5 + 0.19685;
				$lb_x_3 = $sr_profile_x_max + $rout_lb_x * 0.03937 * 0.5 - 0.19685;
				$lb_x_4 = $sr_profile_x_max + $rout_lb_x * 0.03937 * 0.5;
				$lb_x_5 = $sr_profile_x_max + $rout_lb_x * 0.03937 * 0.5 - 0.047244;
				$lb_y_1 = $sr_profile_y_min - $rout_lb_y * 0.03937 * 0.5;
				$lb_y_2 = $sr_profile_y_min - $rout_lb_y * 0.03937 * 0.5 + 0.19685;
				$lb_y_3 = $profile_y - ($profile_y - $sr_profile_y_max) + $rout_lb_y * 0.03937 * 0.5 - 0.19685;
				$lb_y_4 = $profile_y - ($profile_y - $sr_profile_y_max) + $rout_lb_y * 0.03937 * 0.5;
				$lb_y_5 = $profile_y - $sr_profile_y_max + $rout_fd_data * 0.03937 + ($i * 0.3937);
			}
			
		} else {
			$f->INFO(entity_type => 'layer',entity_path => "$job_name/panel/$tmp",data_type => 'LIMITS');
			my $rout_xmin = $f->{doinfo}{gLIMITSxmin} + 0.0472441;
			my $rout_ymin = $f->{doinfo}{gLIMITSymin} + 0.0472441;
			my $rout_xmax = $f->{doinfo}{gLIMITSxmax} - 0.0472441;
			my $rout_ymax = $f->{doinfo}{gLIMITSymax} - 0.0472441;
			
			$lb_x_1 = $rout_xmin;
			$lb_x_2 = $rout_xmin + 0.19685;
			$lb_x_3 = $rout_xmax - 0.19685;
			$lb_x_4 = $rout_xmax;
			$lb_x_5 = $rout_xmax - 0.07874;
			$lb_y_1 = $rout_ymin;
			$lb_y_2 = $rout_ymin + 0.19685;
			$lb_y_3 = $rout_ymax - 0.19685;
			$lb_y_4 = $rout_ymax;
			$lb_y_5 = $rout_ymin + $rout_fd_data * 0.03937 + ($i * 0.3937);

		}
		$f->COM("add_polyline_strt");
		$f->COM("add_polyline_xy,x=$lb_x_1,y=$lb_y_4");
		$f->COM("add_polyline_xy,x=$lb_x_1,y=$lb_y_2");
		$f->COM("add_polyline_xy,x=$lb_x_2,y=$lb_y_1");	
		
		#$f->COM("add_polyline_crv,xc=$lb_x_2,yc=$lb_y_2,xe=$lb_x_2,ye=$lb_y_1,cw=no");		
		$f->COM("add_polyline_xy,x=$lb_x_3,y=$lb_y_1");
		$f->COM("add_polyline_crv,xc=$lb_x_3,yc=$lb_y_2,xe=$lb_x_4,ye=$lb_y_2,cw=no");

		$f->COM("add_polyline_xy,x=$lb_x_4,y=$lb_y_3");
		$f->COM("add_polyline_xy,x=$lb_x_3,y=$lb_y_4");
		#$f->COM("add_polyline_crv,xc=$lb_x_3,yc=$lb_y_3,xe=$lb_x_3,ye=$lb_y_4,cw=no");
		$f->COM("add_polyline_xy,x=$lb_x_2,y=$lb_y_4");
		$f->COM("add_polyline_crv,xc=$lb_x_2,yc=$lb_y_3,xe=$lb_x_1,ye=$lb_y_3,cw=no");
		$f->COM("add_polyline_end,attributes=no,symbol=r94.495,polarity=positive");
		
		$f->COM("add_polyline_strt");
		$f->COM("add_polyline_xy,x=$lb_x_4,y=$lb_y_5");
		$f->COM("add_polyline_xy,x=$lb_x_5,y=$lb_y_5");
		$f->COM("add_polyline_end,attributes=no,symbol=r94.495,polarity=positive");
		$f->COM("sel_net_feat,operation=select,x=$lb_x_1,y=$lb_y_2,tol=120");
		$f->COM("chain_add,layer=$tmp\_s,chain=1,size=0.094488,comp=right,feed=25,chng_direction=0");
	
		if ( $tmp eq "pnl_rout" ) {
			$rout_file_name = "rout";
			$input_rout_name = "sh-rout_s";
		} elsif ( $tmp eq "pnl_rout1" ) {
			$rout_file_name = "rout1";
			$input_rout_name = "sh-rout1_s";
		} elsif ( $tmp eq "pnl_rout2" ) {
			$rout_file_name = "rout2";
			$input_rout_name = "sh-rout2_s";
		} elsif ( $tmp eq "pnl_rout3" ) {
			$rout_file_name = "rout3";
			$input_rout_name = "sh-rout3_s";
		}
		
		my $ncset_name = "rout_set"; 
		#$f->COM("ncrset_cur,job=$job_name,step=panel,layer=$tmp\_s,ncset=");

		$f->VOF;
		$f->COM("ncrset_delete,name=$ncset_name");
		$f->VON;

		$f->COM("ncrset_cur,job=$job_name,step=panel,layer=$tmp\_s,ncset=$ncset_name");
		$f->COM("ncr_set_machine,machine=excellon_new,thickness=0");
		$f->COM("ncr_auto_all,create_rout=no");
		$f->COM("disp_on");
		$f->COM("origin_on");
		$f->COM("ncr_cre_rout");
		$f->COM("ncr_ncf_export,dir=$do_rout_path,name=$job_name.$rout_file_name\_s");	
		@ARGV = "$do_rout_path/$job_name.$rout_file_name\_s";
		local $^I= ".bak";
		my $marker = 0;
		while(<>) {
			if ( $marker eq 0 ) {
				my $text = encode("gb2312","//裁膜标准距: $bk_x MM");
				print "$text\n";
			}
			s/\/G05\n//;
			s/\/G40\n//;
			s/M16/M17/;
			print;
			$marker++;
		}
		
		my $ncset_name1 = "rout_set1"; 
		#$f->COM("ncrset_cur,job=$job_name,step=panel,layer=$tmp,ncset=");
		$f->VOF;
		$f->COM("ncrset_delete,name=$ncset_name1");
		$f->VON;
		
		$f->COM("ncrset_cur,job=$job_name,step=panel,layer=$tmp,ncset=$ncset_name1");
		$f->COM("ncr_set_machine,machine=excellon_new,thickness=0");		
		$f->COM("ncr_auto_all,create_rout=no");		
		$f->COM("ncr_cre_rout");
		$f->COM("disp_on");
		$f->COM("origin_on");
		$f->COM("ncr_ncf_export,dir=$do_rout_path,name=$job_name.$rout_file_name");
		@ARGV = "$do_rout_path/$job_name.$rout_file_name";
		local $^I=".bak1";
		my $marker1 = 0;
		while(<>) {
			if ( $marker1 eq 0 ) {
				my $text = encode("gb2312","//裁膜标准距: $bk_x MM");
				print "$text\n";
			}
			s/\/G05\n//;
			s/\/G40\n//;
			s/M16/M17/;
			print;
			$marker1++;
		}
		system("rm -rf $do_rout_path/$job_name.$rout_file_name.bak1");
		system("rm -rf $do_rout_path/$job_name.$rout_file_name\_s.bak");
		
		$f->COM("delete_layer,layer=$tmp\_s");
		$f->COM("units,type=mm");
		#$f->PAUSE("测试a=$i");
		$f->COM("input_manual_reset");
		$f->COM("input_manual_set,path=$do_rout_path/$job_name.$rout_file_name\_s,job=$job_name,step=panel,format=Excellon2,data_type=ascii,units=mm,coordinates=absolute,zeroes=leading,nf1=3,nf2=0,decimal=yes,separator=nl,tool_units=mm,layer=$input_rout_name,wheel=,wheel_template=,nf_comp=0,multiplier=1,text_line_width=0.0024,signed_coords=no,break_sr=yes,drill_only=no,merge_by_rule=no,threshold=200,resolution=3,drill_type=unspecified");
		$f->COM("input_manual,script_path=");
		#$f->PAUSE("测试b=$i");
		
		$i++;	
	}
	
	$f->COM("clear_layers");
	$f->COM("affected_layer,mode=all,affected=no");	
	$f->COM("filter_reset,filter_name=popup");
	#dircopy("$path_tmp_job","$do_rout_path");
	#system("rm -rf /tmp/$job_name");

	#unlink glob("$ENV{INCAM_TMP}/*.txt");
	&run_message_ok_exit;
	exit 0;
}	
	
sub run_message_rout {
	my $mw3_5 = MainWindow->new( -title =>"VGT");
	$mw3_5->protocol("WM_DELETE_WINDOW", \&OnQuit);
	$mw3_5->geometry("400x145-800+100");
	$mw3_5->raise( );
	$mw3_5->resizable(0,0);
	
	my $sh_log = $mw3_5->Photo('info',-file => "$images_path/sh_log.xpm");
	my $CAM_frm = $mw3_5->Frame(-bg => '#9BDBDB',-borderwidth =>2,-relief => "raised",-height => 20)->pack(-side=>'top',-fill=>'x');
	my $image_label = $CAM_frm->Label(-image => $sh_log, -border => 1, -relief => 'solid',
                                              )->pack(-side => 'left',
                                                      -padx => 2,
                                                      -pady => 2);  
	$CAM_frm->Label(-text => '锣带输出提示  ',-font => 'charter 18 bold',-bg => '#9BDBDB')->pack(-pady => 2);
	$CAM_frm->Label(-text => '作者:dgz  Ver:1.0',-font => 'charter 10',-bg => '#9BDBDB')->pack(-side=>'right', -padx => 10, -pady => 2);
	my $lab_frm = $mw3_5->Frame(-bg => '#9BDBDB',-borderwidth =>2,-height => 40)->pack(-side=>'top',-fill=>'x');
	$lab_frm->Label(-text => '小于4层的板没有锣板框锣带,请退出!',-font => 'charter 14',-bg => '#9BDBDB',-fg=>'red')->pack(-side=>'top', -padx => 5, -pady => 5);
	my $Bot_frm = $mw3_5->Frame(-bg => '#9BDBDB',-borderwidth =>2,-height => 40)->pack(-side=>'bottom',-fill=>'x');
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
sub run_message_rout_no {
	my $mw3_5 = MainWindow->new( -title =>"VGT");
	$mw3_5->protocol("WM_DELETE_WINDOW", \&OnQuit);
	$mw3_5->geometry("400x145-800+100");
	$mw3_5->raise( );
	$mw3_5->resizable(0,0);
	
	my $sh_log = $mw3_5->Photo('info',-file => "$images_path/sh_log.xpm");
	my $CAM_frm = $mw3_5->Frame(-bg => '#9BDBDB',-borderwidth =>2,-relief => "raised",-height => 20)->pack(-side=>'top',-fill=>'x');
	my $image_label = $CAM_frm->Label(-image => $sh_log, -border => 1, -relief => 'solid',
                                              )->pack(-side => 'left',
                                                      -padx => 2,
                                                      -pady => 2);  
	$CAM_frm->Label(-text => '锣带输出提示  ',-font => 'charter 18 bold',-bg => '#9BDBDB')->pack(-pady => 2);
	$CAM_frm->Label(-text => '作者:dgz  Ver:1.0',-font => 'charter 10',-bg => '#9BDBDB')->pack(-side=>'right', -padx => 10, -pady => 2);
	my $lab_frm = $mw3_5->Frame(-bg => '#9BDBDB',-borderwidth =>2,-height => 40)->pack(-side=>'top',-fill=>'x');
	$lab_frm->Label(-text => '板内没有Board属性的rout层,请退出!',-font => 'charter 14',-bg => '#9BDBDB',-fg=>'red')->pack(-side=>'top', -padx => 5, -pady => 5);
	my $Bot_frm = $mw3_5->Frame(-bg => '#9BDBDB',-borderwidth =>2,-height => 40)->pack(-side=>'bottom',-fill=>'x');
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
sub run_message_rout4_no {
	my $mw3_5 = MainWindow->new( -title =>"VGT");
	$mw3_5->protocol("WM_DELETE_WINDOW", \&OnQuit);
	$mw3_5->geometry("400x145-800+100");
	$mw3_5->raise( );
	$mw3_5->resizable(0,0);
	
	my $sh_log = $mw3_5->Photo('info',-file => "$images_path/sh_log.xpm");
	my $CAM_frm = $mw3_5->Frame(-bg => '#9BDBDB',-borderwidth =>2,-relief => "raised",-height => 20)->pack(-side=>'top',-fill=>'x');
	my $image_label = $CAM_frm->Label(-image => $sh_log, -border => 1, -relief => 'solid',
                                              )->pack(-side => 'left',
                                                      -padx => 2,
                                                      -pady => 2);  
	$CAM_frm->Label(-text => '锣带输出提示  ',-font => 'charter 18 bold',-bg => '#9BDBDB')->pack(-pady => 2);
	$CAM_frm->Label(-text => '作者:dgz  Ver:1.0',-font => 'charter 10',-bg => '#9BDBDB')->pack(-side=>'right', -padx => 10, -pady => 2);
	my $lab_frm = $mw3_5->Frame(-bg => '#9BDBDB',-borderwidth =>2,-height => 40)->pack(-side=>'top',-fill=>'x');
	$lab_frm->Label(-text => '程序暂时只支持三次压合锣板框锣带,请退出!',-font => 'charter 14',-bg => '#9BDBDB',-fg=>'red')->pack(-side=>'top', -padx => 5, -pady => 5);
	my $Bot_frm = $mw3_5->Frame(-bg => '#9BDBDB',-borderwidth =>2,-height => 40)->pack(-side=>'bottom',-fill=>'x');
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
sub run_message_rout_please {
	my $ans0 = $mw3_5->messageBox(-icon => 'question',-message => '没有选择到两条做C角的边线，请确认!',-title => 'Waiting',-type => 'Ok');
	return if $ans0 eq "No";
	exit 0;
}
sub run_message_rout_fd {
	my $ans0 = $mw3_5->messageBox(-icon => 'question',-message => '没有选择到防呆线，请确认!',-title => 'Waiting',-type => 'Ok');
	exit 0;
}	

sub run_message_rout_bk {
	my $ans0 = $mw3_5->messageBox(-icon => 'question',-message => '输出的锣带层没有靶孔，对应的INN层也没有，请确认!',-title => 'Waiting',-type => 'Ok');
	return if $ans0 eq "No";
	exit 0;
}

sub run_message_rout_bk_data {
	my $ans0 = $mw3_5->messageBox(-icon => 'question',-message => '请输入锣边尺寸!',-title => 'quit',-type => 'YesNo');
	return if $ans0 eq "Yes";
	exit 0;
}
sub run_message_rout_bk_no {
	my $ans0 = $mw3_5->messageBox(-icon => 'question',-message => 'inn与rout对应的数量不对!',-title => 'Waiting',-type => 'Ok');
	exit 0;
}

sub run_message_data_error {
	my $ans0 = $mw3_5->messageBox(-icon => 'question',-message => '输入的留边尺寸不对,请重新输入!',-title => 'quit',-type => 'YesNo');
	return if $ans0 eq "Yes";
	exit 0;
}
sub run_message_ok_exit {
	my $ans0 = $mw3_5->messageBox(-icon => 'question',-message => '输出巳完成，请检查!',-title => 'Waiting',-type => 'Ok');
	exit 0;
}
sub run_message_open_job {
	my $ans0 = $mw3_5->messageBox(-icon => 'question',-message => '请先打开一个JOB!',-title => 'Waiting',-type => 'Ok');
	exit 0;
}

sub rout_layer_name_error {
	my $mw3_5 = MainWindow->new( -title =>"VGT");
	$mw3_5->protocol("WM_DELETE_WINDOW", \&OnQuit);
	$mw3_5->geometry("550x145-800+100");
	$mw3_5->raise( );
	$mw3_5->resizable(0,0);
	
	my $sh_log = $mw3_5->Photo('info',-file => "$images_path/sh_log.xpm");
	my $CAM_frm = $mw3_5->Frame(-bg => '#9BDBDB',-borderwidth =>2,-relief => "raised",-height => 20)->pack(-side=>'top',-fill=>'x');
	my $image_label = $CAM_frm->Label(-image => $sh_log, -border => 1, -relief => 'solid',
                                              )->pack(-side => 'left',
                                                      -padx => 2,
                                                      -pady => 2);  
	$CAM_frm->Label(-text => '锣带输出提示  ',-font => 'charter 18 bold',-bg => '#9BDBDB')->pack(-pady => 2);
	$CAM_frm->Label(-text => '作者:dgz  Ver:1.0',-font => 'charter 10',-bg => '#9BDBDB')->pack(-side=>'right', -padx => 10, -pady => 2);
	my $lab_frm = $mw3_5->Frame(-bg => '#9BDBDB',-borderwidth =>2,-height => 40)->pack(-side=>'top',-fill=>'x');
	$lab_frm->Label(-text => '锣带的命名或者排列顺序不对,请定义好后再执行程序!',-font => 'charter 14',-bg => '#9BDBDB',-fg=>'red')->pack(-side=>'top', -padx => 5, -pady => 5);
	my $Bot_frm = $mw3_5->Frame(-bg => '#9BDBDB',-borderwidth =>2,-height => 40)->pack(-side=>'bottom',-fill=>'x');
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
###################################################################################################################################################################################################




