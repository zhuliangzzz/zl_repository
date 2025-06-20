#!/usr/bin/perl -w
#### modifiy by hyp, Jan 17, 2018
use lib "/incam/$ENV{INCAM_RELEASE_VER_VGT}/app_data/perl";
use Tk;
use Tk::Tree;
use incam;
use Encode;
use POSIX;
use File::Copy;
use File::Copy::Recursive qw(fcopy rcopy dircopy fmove rmove dirmove);
use Data::Dumper;
$host = shift;
$f = new incam($host);

require Tk::LabFrame;
require Tk::LabEntry;

my $job_name = $ENV{JOB};

my $isFlipJob;
$isFlipJob = 1 unless ( &checkIfFilpJob($job_name) );

my $images_path = "/incam/server/site_data/scripts/sh1_script/images";
my $do_inn_tgz_path = "/id/workfile/hdi_film/$job_name";

mkdir "$do_inn_tgz_path" if (! -d $do_inn_tgz_path );

my $target_dir = "$do_inn_tgz_path";

$f->INFO(entity_type => 'job', entity_path => "$job_name", data_type => 'STEPS_LIST');
my @step_list = @{$f->{doinfo}{gSTEPS_LIST}};

my @update_step_list = ();
foreach my $tmp (@step_list)
{
	push(@update_step_list, $tmp) if ($tmp =~ /^edit[0-9]?.[flip][flip].*/);
}

if (scalar(@update_step_list) != 0)
{
	&run_message_flip;
	exit 0;
}

$f->INFO(angle_direction => 'ccw', entity_type => 'matrix',
		 entity_path => "$job_name/matrix",
		 data_type => 'ROW',
		 parameters => "name");
my @layersAll = @{$f->{doinfo}{gROWname}};

my @signal_lay_array = ();
my @signal_other_array = ();

$f->DO_INFO("-t MATRIX -d ROW -e $job_name/matrix");
for(my $i=0 ; $i < @{$f->{doinfo}{gROWname}} ; $i++)
{
	$info_ref = { name       => @{$f->{doinfo}{gROWname}}[$i],
				  layer_type => @{$f->{doinfo}{gROWlayer_type}}[$i],
				  context    => @{$f->{doinfo}{gROWcontext}}[$i],
				  polarity   => @{$f->{doinfo}{gROWpolarity}}[$i],
				  side       => @{$f->{doinfo}{gROWside}}[$i],
				};
	push(@signal_lay_array,$info_ref->{name}) if ( $info_ref->{context} eq "board" && $info_ref->{side} eq "inner" );
	#push(@signal_other_array,$info_ref->{name}) if ( ($info_ref->{context} eq "board" && $info_ref->{layer_type} eq "drill") or $info_ref->{name} eq "w" or $info_ref->{name} eq "w27" or $info_ref->{name} eq "w25" or $info_ref->{name} eq "ww" or $info_ref->{name} eq "ww1" or $info_ref->{name} eq "np" or $info_ref->{name} eq "npt" or $info_ref->{name} eq "npth" or $info_ref->{name} eq "drl+1" or $info_ref->{name} eq "dd+1" or $info_ref->{name} =~ /pnl_rout[0-9]?/ or $info_ref->{name} eq "dd" or $info_ref->{name} eq "sz.lp" or $info_ref->{name} =~ "sz[0-9][0-9].lp" or $info_ref->{name} eq "lp");
	push(@signal_other_array,$info_ref->{name})
	if ( ($info_ref->{context} eq "board" && $info_ref->{layer_type} eq "drill")
		or $info_ref->{name} eq "w"
		or $info_ref->{name} eq "w27"
		or $info_ref->{name} eq "w25"
		or $info_ref->{name} eq "ww"
		or $info_ref->{name} eq "ww1"
		or $info_ref->{name} eq "np"
		or $info_ref->{name} eq "npt"
		or $info_ref->{name} eq "npth"
		or $info_ref->{name} eq "drl+1"
		or $info_ref->{name} eq "dd+1"
		or $info_ref->{name} =~ /pnl_rout[0-9]?/
		or $info_ref->{name} eq "dd"
		or $info_ref->{name} eq "sz.lp"
		or $info_ref->{name} =~ "sz[0-9][0-9].lp"
		or $info_ref->{name} eq "lp"
		or ($info_ref->{name} =~ /^sz/ && $info_ref->{name} =~ /\./));

}

my $board_inn_layer = scalar(@signal_lay_array);
if ( $board_inn_layer eq 0 )
{
	&run_message_no_aoi;
	exit 0;
} 
my @all_lay_list = (@signal_lay_array,@signal_other_array);

my $mw3_2 = MainWindow->new( -title =>"VGT");
$mw3_2->bind('<Return>' => sub{ shift->focusNext;});
$mw3_2->geometry("+600+80");
$mw3_2->raise();

my $sh_log_frm = $mw3_2->Frame(-bg => '#9BDBDB',-borderwidth =>2,-relief => "raised",-height => 5)->pack(-side=>'top',-fill=>'both');

my $sh_log = $sh_log_frm->Photo('info',-file => "$images_path/sh_log.xpm");
my $image_label = $sh_log_frm->Label(-image => $sh_log, -border => 1, -relief => 'solid')->pack(-side => 'left', -padx => 5, -pady => 5);  
													  
$sh_log_frm->Label(-text => hanzi("内层AOI输出"),-font => 'charter 24 bold',-bg => '#9BDBDB')->pack();
$sh_log_frm->Label(-text => hanzi("作者:dgz  Ver:1.0"),-font => 'charter 10',-bg => '#9BDBDB')->pack(-side=>'right', -padx => 10); 

my $tab_frm = $mw3_2->LabFrame(-label => hanzi("参数选择"),-font => 'SimSun 10',-bg => '#9BDBDB',-fg => 'blue',)->pack(-side=>'top',-fill=>'both');
my $path_sel_tmp = $tab_frm->Frame(-bg => '#9BDBDB')->pack(-side=>'top',-fill=>'both');
my $open_path = $path_sel_tmp->Photo('path',-file => "$images_path/OpenJob.xpm");

$path_sel_tmp->LabEntry(-label => hanzi("输出目录:"),
										-labelBackground => '#9BDBDB',
										-labelFont => 'SimSun 12',
										-textvariable => \$do_inn_tgz_path,
										-bg => 'white',
										-width => 32,
										-state=> 'disabled',
										-relief=>'ridge',
										-labelPack => [qw/-side left -anchor w/])->pack(-side => 'left',-padx => 3,-pady => 5);
										
my $select_frm_lay = $mw3_2-> Frame(-bg => '#9BDBDB')->pack(-side=>'top',-fill=>'both',-expand=>1);
my $select_all_lay = $select_frm_lay-> Frame(-bg => '#9BDBDB')->pack(-side=>'top',-fill=>'both',-expand=>1);

my $qqq = $select_all_lay-> Frame(-bg => '#9BDBDB')->pack(-padx => 3,-fill=>'both');

my $rb_value = '只列内层';
for ( qw(列出所有层 只列内层) )
{
	$qqq->Radiobutton(-text => hanzi("$_"),
					  -value => $_,
					  -variable => \$rb_value,
					  -background => "#9BDBDB",
					  -foreground => 'blue',
					  -command => sub{&ChangeLayersList($rb_value)})->pack(-side => 'left');
}

my $select_lay_list = $select_all_lay-> Frame(-bg => '#9BDBDB')->pack(-side=>'left',-padx => 3,-fill=>'both');
my $sel_layer_lb = $select_lay_list->Scrolled('Listbox',-scrollbars=>'se',-selectbackground=>'blue',-selectforeground=>'white',-selectmode=>'multiple',-height => 16, -background=>'white',-foreground=>'black',-font=> 'charter 12 bold')->pack(-side=>'top',-fill=>'x');									 
foreach my $tmp (@all_lay_list)
{
	$sel_layer_lb -> insert('end', "$tmp");	
}												  
		
my $select_frm_tmp = $select_all_lay-> Frame(-bg => '#9BDBDB')->pack(-side=>'right',-padx => 20);

my $button_frm1 = $select_frm_tmp->Button(-text => hanzi("选择all"),
                                          -command => sub {&sel_lay_all;},
                                          -width => 10,
										  -activebackground=>'green',
										  -bg => '#9BDBDB',
										  -font=> 'charter 10 bold',
										  -height=> 1,
                                         )->pack(-side => 'top',
												 -fill=>'y',
                                                 -pady => 25 );
												 
my $button_frm2 = $select_frm_tmp->Button(-text => hanzi("清除all"),
                                          -command => sub {&clear_lay_all;},
                                          -width => 10,
										  -activebackground=>'green',
										  -bg => '#9BDBDB',
										  -font=> 'charter 10 bold',
										  -height=> 1,
                                         )->pack(-side => 'top',
												 -fill=>'y',
                                                 -pady => 25 );	

my $button_frm3 = $select_frm_tmp->Button(-text => hanzi("输出"),
                                          -command => sub {&run_output_gerber;exit 0;},
                                          -width => 10,
										  -activebackground=>'green',
										  -bg => '#9BDBDB',
										  -font=> 'charter 10 bold',
										  -height=> 1,
                                         )->pack(-side => 'top',
												 -fill=>'y',
                                                 -pady => 25 );	

my $button_frm4 = $select_frm_tmp->Button(-text => hanzi("退出"),
                                          -command => sub {exit 0;},
                                          -width => 10,
										  -activebackground=>'red',
										  -bg => '#9BDBDB',
										  -font=> 'charter 10 bold',
										  -height=> 1,
                                         )->pack(-side => 'top',
												 -fill=>'y',
                                                 -pady => 25 );

MainLoop;

sub run_output_gerber
{
	my @selectlayers = ();	
	foreach($sel_layer_lb->curselection())
	{	
		$tmp_layers = $sel_layer_lb->get($_);
		push(@selectlayers,$tmp_layers);		
	}	
	my $layer_no = scalar(@selectlayers);
	if ( $layer_no eq 0 )
	{
		&run_message_no_sel;
		$select_frm_tmp->withdraw;
	}
	$mw3_2->iconify();
	
	$f->INFO(entity_type => 'job',
			 entity_path => "$job_name-inn",
			   data_type => 'EXISTS');
	$f->COM("delete_entity,job=,type=job,name=$job_name-inn") if ( $f->{doinfo}{gEXISTS} eq "yes" );

	$f->COM("copy_entity,type=job,source_job=$job_name,source_name=$job_name,dest_job=$job_name-inn,dest_name=$job_name-inn,dest_database=,remove_from_sr=yes");
	$f->COM("clipb_open_job,job=$job_name-inn,update_clipboard=view_job");
	$f->COM("open_job,job=$job_name-inn");
	
	$f->COM("open_job,job=$job_name-inn,open_win=yes");
	$f->AUX("set_group,group=$f->{COMANS}");
	$f->COM("set_subsystem,name=1-Up-Edit");
	$f->COM("set_step,name=panel");
	$f->COM("open_group,job=$job_name-inn,step=panel,is_sym=no");
	$f->AUX("set_group,group=$f->{COMANS}");
	$f->COM("open_entity,job=$job_name-inn,type=step,name=panel,iconic=no");
	$f->AUX("set_group,group=$f->{COMANS}");			
	$f->COM("units,type=inch");

	$f->INFO(entity_type => 'step',
			 entity_path => "$job_name-inn/panel",
             data_type => 'LAYERS_LIST');
	my @all_layers_list = @{$f->{doinfo}{gLAYERS_LIST}};

	if ( $isFlipJob )
	{
		$f->COM("set_step,name=edit");
		$f->COM("matrix_suspend_symmetry_check,job=$job_name-inn,matrix=matrix,suspend=yes");		
	}
	
	foreach my $tmp1 (@all_layers_list)
	{
		foreach my $tmp2 (@selectlayers)
		{
			goto BBBBB if ( $tmp1 eq $tmp2 );
		}
		$f->COM("delete_layer,layer=$tmp1");
		BBBBB:
	}
	
	if ( $isFlipJob )
	{
		$f->COM("matrix_suspend_symmetry_check,job=$job_name-inn,matrix=matrix,suspend=no");
		$f->COM("set_step,name=panel");			
	}
	
	$f->COM("save_job,job=$job_name-inn,override=no");


    # 2019.12.6李家兴修改，gen_line_skip_pre_hooks已经设置为2,此处强制调用pre,传入参数$job_name
    my $pre_status = system("perl /incam/server/site_data/hooks/line_hooks/export_job.pre $job_name-inn");
    print "\$pre_status : $pre_status\n";
    # 如果system执行结果为非零，表示pre hooks检测到异常，要退出
    exit 0 if ($pre_status != 0);
	$f->COM("export_job,job=$job_name-inn,path=$do_inn_tgz_path,mode=tar_gzip,submode=full,overwrite=yes");	
    # 2019.12.5李家兴修改，定义参数hash的引用
    my $ref_param_hash = {
    	# export_job.post只用到如下几个参数，如有需要可以自行增加
	    job         => "${job_name}-inn",
	    path        => $do_inn_tgz_path,
	    mode        => 'tar_gzip',
    	submode     => 'full',
    	output_name => "${job_name}-inn",
    };
    # 两个不同脚本之间不能直接传hash引用，只能通过字符的形式中转
    my $param_hash_string = Dumper($ref_param_hash);
    # 2019.12.6李家兴修改，gen_line_skip_post_hooks已经设置为2,此处强制调用pre,传入参数$param_hash_string
    system 'perl', '/incam/server/site_data/hooks/line_hooks/export_job.post', "$param_hash_string";

	$f->COM("check_inout,mode=in,type=job,job=$job_name-inn");
	$f->COM("close_job,job=$job_name-inn");
	$f->COM("close_form,job=$job_name-inn");
	$f->COM("close_flow,job=$job_name-inn");
	
	&run_message_over;
}

sub sel_lay_all
{
	$sel_layer_lb->selectionSet(0,'end');
}
sub clear_lay_all
{
	$sel_layer_lb->selectionClear(0,'end')
}

sub run_message_no_aoi
{
	my $mw3_2 = MainWindow->new( -title =>"VGT");
	$mw3_2->protocol("WM_DELETE_WINDOW", \&OnQuit);
	$mw3_2->geometry("500x145-800+100");
	$mw3_2->raise( );
	$mw3_2->resizable(0,0);
	
	my $sh_log = $mw3_2->Photo('info',-file => "$images_path/sh_log.xpm");
	my $CAM_frm = $mw3_2->Frame(-bg => '#9BDBDB',-borderwidth =>2,-relief => "raised",-height => 20)->pack(-side=>'top',-fill=>'x');
	my $image_label = $CAM_frm->Label(-image => $sh_log, -border => 1, -relief => 'solid',
                                              )->pack(-side => 'left',
                                                      -padx => 2,
                                                      -pady => 2);  
	$CAM_frm->Label(-text => hanzi("输出内层AOI  "),-font => 'charter 18 bold',-bg => '#9BDBDB')->pack(-pady => 2);
	$CAM_frm->Label(-text => hanzi("作者:dgz  Ver:1.0"),-font => 'charter 10',-bg => '#9BDBDB')->pack(-side=>'right', -padx => 10, -pady => 2);
	my $lab_frm = $mw3_2->Frame(-bg => '#9BDBDB',-borderwidth =>2,-height => 40)->pack(-side=>'top',-fill=>'x');
	$lab_frm->Label(-text => hanzi("没有内层,不用输出内层AOI!"),-font => 'charter 14',-bg => '#9BDBDB',-fg=>'red')->pack(-side=>'top', -padx => 5, -pady => 5);
	my $Bot_frm = $mw3_2->Frame(-bg => '#9BDBDB',-borderwidth =>2,-height => 40)->pack(-side=>'bottom',-fill=>'x');
	my $array_button = $Bot_frm->Button(-text => hanzi("退出"),
                                         -command => sub {exit 0;},
                                         -width => 10,
										  -activebackground=>'#9BDBDB',
										  -font=> 'charter 12',
										  -height=> 2
                                          )->pack(-side => 'right',
                                                  -padx => 20);	
	MainLoop;
}

sub run_message_over
{
	my $ans0 = $mw3_2->messageBox(-icon => 'question',-message => hanzi("程序运行结束，请确认!"),-title => 'Waiting',-type => 'Ok');
	exit 0;
}

sub run_message_flip
{
	my $mw3_2 = MainWindow->new( -title =>"VGT");
	$mw3_2->protocol("WM_DELETE_WINDOW", \&OnQuit);
	$mw3_2->geometry("500x145-800+100");
	$mw3_2->raise( );
	$mw3_2->resizable(0,0);
	
	my $sh_log = $mw3_2->Photo('info',-file => "$images_path/sh_log.xpm");
	my $CAM_frm = $mw3_2->Frame(-bg => '#9BDBDB',-borderwidth =>2,-relief => "raised",-height => 20)->pack(-side=>'top',-fill=>'x');
	my $image_label = $CAM_frm->Label(-image => $sh_log, -border => 1, -relief => 'solid',
                                              )->pack(-side => 'left',
                                                      -padx => 2,
                                                      -pady => 2);  
	$CAM_frm->Label(-text => hanzi("输出内层AOI  "),-font => 'charter 18 bold',-bg => '#9BDBDB')->pack(-pady => 2);
	$CAM_frm->Label(-text => hanzi("作者:dgz  Ver:1.0"),-font => 'charter 10',-bg => '#9BDBDB')->pack(-side=>'right', -padx => 10, -pady => 2);
	my $lab_frm = $mw3_2->Frame(-bg => '#9BDBDB',-borderwidth =>2,-height => 40)->pack(-side=>'top',-fill=>'x');
	$lab_frm->Label(-text => hanzi("INCAM对于此板的阴阳方式不认同!"),-font => 'charter 14',-bg => '#9BDBDB',-fg=>'red')->pack(-side=>'top', -padx => 5, -pady => 5);
	my $Bot_frm = $mw3_2->Frame(-bg => '#9BDBDB',-borderwidth =>2,-height => 40)->pack(-side=>'bottom',-fill=>'x');
	my $array_button = $Bot_frm->Button(-text => hanzi("退出"),
                                         -command => sub {exit 0;},
                                         -width => 10,
										  -activebackground=>'#9BDBDB',
										  -font=> 'charter 12',
										  -height=> 2
                                          )->pack(-side => 'right',
                                                  -padx => 20);	
	MainLoop;
}

sub OnQuit
{
	my $ans = $mw3_2->messageBox(-icon => 'question',-message => hanzi("你确定要退出吗？"),-title => 'quit',-type => 'YesNo');
	return if $ans eq "No";
	exit;
}
sub hanzi
{
	return decode('utf8',shift);
}


sub checkIfFilpJob
{
	my $curJob = shift;
	
	my @steps_list = ();
	$f->INFO(entity_type => 'job',
			 entity_path => "$curJob",
			 data_type => 'STEPS_LIST');
	@steps_list = @{$f->{doinfo}{gSTEPS_LIST}};
	
	for my $curStep ( @steps_list )
	{
		$f->INFO(angle_direction => 'ccw',
				 entity_type => 'step',
				 entity_path => "$curJob/$curStep",
				 data_type => 'REPEAT',
				 parameters => "flip");
		my @stepRepeatList = @{$f->{doinfo}{gREPEATflip}};
		for my $repeatStatus ( @stepRepeatList )
		{
			if ( $repeatStatus eq 'yes' )
			{
				return 0;
			}
		}
	}
	return 1;
}

sub flipJobWarning
{
	use Tk;
	my $warning = MainWindow -> new( -title =>"VGT");
	${warning}->geometry("+200+300");
	my $text = $warning -> Text(
			-background       => 'white',
			-foreground       => "blue",
			-font             => 'charter 10',
			-width            => 110,
			-selectforeground => 'yellow',
			-relief           => 'sunken',
			-spacing1         => 15,
			-height           => 4
		)->pack( -expand => 1, -fill => 'both' );
		$text->insert( 'end', hanzi("该板为阴阳板，目前InCAM不支持部分层AOI资料的输出，请将该资料转移到Genesis输出.\n该问题将在InCAM 4.0版本修复，谢谢.") );
		$text->configure( -state => 'disable' );
		
		my $frame1 = $warning -> Frame->pack( -side => 'bottom' , -expand => 1 );		
		my $continueButton = $frame1->Button(
			-text             => 'OK',
			-font             => [ -size => 8 ],
			-width            => '8',
			-height           => '3',
			-activebackground => 'green',
			-command => sub { $warning->destroy; exit 0; }
		)->pack( -side => "right", -padx => "100", -pady => "5" );		
	MainLoop;
	
	exit 0;
}

sub ChangeLayersList
{
	my $select = shift;
	$sel_layer_lb->selectionClear(0,'end');
	$sel_layer_lb->delete(0,'end');			
	if ( $select eq '列出所有层' )
	{
		foreach my $tmp (@layersAll)
		{
			$sel_layer_lb -> insert('end', "$tmp");	
		}			
	} else {
		$sel_layer_lb->selectionClear(0,'end');
		$sel_layer_lb->delete(0,'end');			
		foreach my $tmp (@all_lay_list)
		{
			$sel_layer_lb -> insert('end', "$tmp");	
		}			
	}
}








