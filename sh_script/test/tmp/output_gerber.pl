#!/usr/bin/perl -w
#### modify by hyp, Jan 11, 2018, �Ż���ͭƤ�ϸ���ʱ�޷����Gerber���⣬����: ��׽���surface=copper����ͭƤ���ֽ�֮���ٵ�Gerber.


use Tk;
use Tk::Tree;
require Tk::Dialog;
require Tk::LabFrame;
require Tk::LabEntry;
use Encode;
use encoding 'euc_cn';
use File::Copy;
use File::Copy::Recursive qw(fcopy rcopy dircopy fmove rmove dirmove);
use POSIX;

# --�����Զ��幫��pm
use lib "$ENV{GENESIS_DIR}/sys/scripts/Package";
use Genesis;
use mainVgt;
#use VGT_Oracle;
use Data::Dumper;
BEGIN
{
	# --ʵ��������
	our $f = new Genesis();
	our $c = new mainVgt();
	#our $o = new VGT_Oracle();
	#
	## --����HDI InPlan oracle���ݿ�
	#our $dbc_h = $o->CONNECT_ORACLE('host' => '172.20.218.193', 'service_name' => 'inmind.fls', 'port' => '1521', 'user_name' => 'GETDATA', 'passwd' => 'InplanAdmin');
	#if (!$dbc_h) {
	#	$c->Messages('warning', '"HDI InPlan���ݿ�"����ʧ��->������ֹ!');
	#	exit(0);
	#}
}

END
{
	# --�Ͽ�Oracle����
	#$dbc_h->disconnect if ($dbc_h);
}

our $job_name = $ENV{JOB};
my $drc_job;
if ( $job_name =~ /(.*)-[a-z].*/ ) {
    $drc_job = uc($1);
} else {
    $drc_job = uc($job_name);
}
# --����ϵͳ���岻ͬ�Ĳ���
if ( $^O ne 'linux' ) {
	our $images_path = "$ENV{SCRIPTS_DIR}/sys/scripts/sh_script/output_gerber/images";
	our $do_gerber_path = "D:/disk/film/$job_name";
	our $tmpPath = "C:/tmp";
    our $scriptPath = "$ENV{SCRIPTS_DIR}/sys/scripts";
} else {
    our $images_path = "/incam/server/site_data/scripts/sh1_script/images";
    our $do_gerber_path = "/id/workfile/film/$job_name";
	our $tmpPath = "/tmp";
    our $scriptPath = "$ENV{SCRIPTS_DIR}/sys/scripts";
}

if (! -d $do_gerber_path ) {
	mkdir $do_gerber_path;
}

$f->INFO(entity_type => 'job',
		 entity_path => $job_name,
		 data_type => 'IS_CHANGED');
if ( $f->{doinfo}{gIS_CHANGED} eq "yes" )
{
	$c->Messages('warning', '��⵽δ����!���ȱ���!');
	exit 0;
}
our $scale_x = 0.9999;
our $scale_y = 0.9997;
our $transform_x = 1.0003;
our $transform_y = 1.0003;
#my $images_path = "$scriptPath/xpms";

#my $do_gerber_path = "/id/workfile/film/$job_name";
if (! -d $do_gerber_path ) {
	mkdir $do_gerber_path;
}

my @inn_lay_array = ();
my @all_outlayer_array = ();
my @all_board_array = ();
my @all_lay_list = ();
my @step_list_all = ();
my @all_silk_array = ();
$f->DO_INFO("-t MATRIX -d ROW -e $job_name/matrix");
for(my $i=0 ; $i < @{$f->{doinfo}{gROWname}} ; $i++){
	$info_ref = { name       => @{$f->{doinfo}{gROWname}}[$i],
				  layer_type => @{$f->{doinfo}{gROWlayer_type}}[$i],
				  context    => @{$f->{doinfo}{gROWcontext}}[$i],
				  polarity   => @{$f->{doinfo}{gROWpolarity}}[$i],
				  side       => @{$f->{doinfo}{gROWside}}[$i],
				};
	if ( $info_ref->{context} eq "board" && $info_ref->{side} eq "inner" ){
		push(@inn_lay_array,$info_ref->{name});
	}
	if ( $info_ref->{context} eq "board" && $info_ref->{side} =~ /(top|bottom)/ && $info_ref->{layer_type} eq "signal" ){
		push(@all_outlayer_array,$info_ref->{name});
	}
	if ( $info_ref->{context} eq "board" && $info_ref->{side} =~ /(top|bottom)/ && $info_ref->{layer_type} eq "silk_screen" ){
		push(@all_silk_array,$info_ref->{name});
	}
	if ( $info_ref->{context} eq "board" ){
		push(@all_board_array,$info_ref->{name});
	}
}

$f->COM("disp_off");

$f->INFO(entity_type => 'step',
		 entity_path => "$job_name/panel",
		   data_type => 'LAYERS_LIST');
@all_lay_list = @{$f->{doinfo}{gLAYERS_LIST}};
$f->INFO(entity_type => 'job',
		 entity_path => "$job_name",
		   data_type => 'STEPS_LIST');

my @step_list_tmp = @{$f->{doinfo}{gSTEPS_LIST}};
foreach my $tmp (@step_list_tmp) {
	if ( $tmp ne "drl" && $tmp ne "lp" && $tmp ne "2nd" && $tmp ne "3nd" ) {
		push(@step_list_all,"$tmp");
	}
}

my $mw3_1 = MainWindow->new( -title =>"VGT");
$mw3_1->bind('<Return>' => sub{ shift->focusNext; });
$mw3_1->protocol("WM_DELETE_WINDOW", \&OnQuit);
#$mw3_1->geometry("400x575-800+80");
$mw3_1->geometry("+800+80");
$mw3_1->raise( );

my $sh_log_frm = $mw3_1->Frame(-bg => '#9BDBDB',-borderwidth =>2,-relief => "raised",-height => 5)->pack(-side=>'top',-fill=>'both');

my $sh_log = $sh_log_frm->Photo('info',-file => "$images_path/sh_log.xpm");
my $image_label = $sh_log_frm->Label(-image => $sh_log, -border => 1, -relief => 'solid',
                                              )->pack(-side => 'left',
                                                      -padx => 5,
                                                      -pady => 5);

$sh_log_frm->Label(-text => 'Gerber���',-font => 'charter 24 bold',-bg => '#9BDBDB')->pack();
$sh_log_frm->Label(-text => '��Ȩ���У�ʤ��Ƽ�  Ver:2.4',-font => 'charter 10',-bg => '#9BDBDB')->pack(-side=>'right', -padx => 10);

my $tab_frm = $mw3_1->LabFrame(-label => '����ѡ��',-font => 'SimSun 10',-bg => '#9BDBDB',-fg => 'blue',)->pack(-side=>'top',-fill=>'both');

my $menub_sel_tmp = $tab_frm->Frame(-bg => '#9BDBDB')->pack(-side=>'top',-fill=>'both');
my $menub_sel_tmp1 = $menub_sel_tmp->Frame(-bg => '#9BDBDB')->pack(-side=>'left',-fill=>'both');
$menub_sel_tmp1->Label(-text => 'stepѡ��:',-font => 'charter 14 ',-bg => '#9BDBDB')->pack(-side => 'left',-padx => 3,-pady => 2);
our $sel_step = "panel";
$menub_sel_tmp1->Optionmenu(-variable => \$sel_step, -options => [@step_list_all],-bg => '#9BDBDB')->pack(-side=>'left');

my $path_sel_tmp = $tab_frm->Frame(-bg => '#9BDBDB')->pack(-side=>'top',-fill=>'both');
my $open_path = $path_sel_tmp->Photo('path',-file => "$images_path/OpenJob.xpm");
$path_sel_tmp->LabEntry(-label => '���Ŀ¼:',
										-labelBackground => '#9BDBDB',
										-labelFont => 'SimSun 14',
										-textvariable => \$do_gerber_path,
										-bg => 'white',
										-width => 40,
										-relief=>'ridge',
										-labelPack => [qw/-side left -anchor w/])->pack(-padx => 3, -side => 'left', -pady => 5);

my $reminder_frm = $tab_frm->Frame(-bg => '#9BDBDB')->pack(-side=>'top',-fill=>'both');
$reminder_frm->Label(-text => '��ܰ����: ����;���򱨴����˳���ǰ���ϲ��ؽ���',-font => 'Simsun 10 bold',-bg => 'blue', -fg => 'white')->pack( -side => 'left', -padx => 10);

our $GerberReread = 1;
#$mw3_1->Checkbutton(-font => ['Arial', '11'],-text=>'�ض�����',-variable=>\$GerberReread,-onvalue => 1,-offvalue => 0,-bg => '#9BDBDB',)->pack(-side=>'top',-fill=>'x',);
$mw3_1->Label(-text => '���Gerber����ض���',-font => 'Simsun 10 bold',-bg => 'red', -fg => 'white')->pack( -side=>'top',-fill=>'x',-padx => 10);

my $select_frm_lay = $mw3_1-> Frame(-bg => '#9BDBDB')->pack(-side=>'top',-fill=>'both',-expand=>1);
my $select_all_lay = $select_frm_lay-> Frame(-bg => '#9BDBDB')->pack(-side=>'top',-fill=>'both',-expand=>1);
my $select_lay_list = $select_all_lay-> Frame(-bg => '#9BDBDB')->pack(-side=>'left',-padx => 15,-fill=>'both');
$sel_layer_lb = $select_lay_list->Scrolled('Listbox',-scrollbars=>'osoe',-selectbackground=>'blue',-selectforeground=>'white',-selectmode=>'multiple',-height => 16,
									 -background=>'white',-foreground=>'black',-font=> 'charter 12 bold')
									 ->pack(-side=>'top',-fill=>'x');
foreach my $tmp (@all_lay_list) {
	$sel_layer_lb -> insert('end', "$tmp");
}

my $select_frm_tmp = $select_all_lay-> Frame(-bg => '#9BDBDB')->pack(-side=>'right',-padx => 24);
my $button_frm1 = $select_frm_tmp->Button(-text => 'ֻѡ�ڲ�',
                                          -command => sub {&inn_sel_lay;},
                                          -width => 8,
										  -activebackground=>'green',
										  -bg => '#9BDBDB',
										  -font=> 'charter 10 bold',
										  -height=> 2,
                                         )->pack(-side => 'top',
												 -fill=>'y',
                                                 -pady => 5 );
my $button_frm2 = $select_frm_tmp->Button(-text => 'ֻѡ���',
                                          -command => sub {&out_sel_lay;},
                                          -width => 8,
										  -activebackground=>'green',
										  -bg => '#9BDBDB',
										  -font=> 'charter 10 bold',
										  -height=> 2,
                                         )->pack(-side => 'top',
												 -fill=>'y',
                                                 -pady => 5 );
my $button_frm3 = $select_frm_tmp->Button(-text => 'Board',
                                          -command => sub {&board_sel_lay;},
                                          -width => 8,
										  -activebackground=>'green',
										  -bg => '#9BDBDB',
										  -font=> 'charter 10 bold',
										  -height=> 2,
                                         )->pack(-side => 'top',
												 -fill=>'y',
                                                 -pady => 5 );
my $button_frm4 = $select_frm_tmp->Button(-text => '��ѡ',
                                          -command => sub {&reverse_sel_lay;},
                                          -width => 8,
										  -activebackground=>'green',
										  -bg => '#9BDBDB',
										  -font=> 'charter 10 bold',
										  -height=> 2,
                                         )->pack(-side => 'top',
												 -fill=>'y',
                                                 -pady => 5 );
my $button_frm5 = $select_frm_tmp->Button(-text => 'ѡ��all',
                                          -command => sub {&sel_lay_all;},
                                          -width => 8,
										  -activebackground=>'green',
										  -bg => '#9BDBDB',
										  -font=> 'charter 10 bold',
										  -height=> 2,
                                         )->pack(-side => 'top',
												 -fill=>'y',
                                                 -pady => 5 );
my $button_frm6 = $select_frm_tmp->Button(-text => '���all',
                                          -command => sub {&clear_lay_all;},
                                          -width => 8,
										  -activebackground=>'green',
										  -bg => '#9BDBDB',
										  -font=> 'charter 10 bold',
										  -height=> 2,
                                         )->pack(-side => 'top',
												 -fill=>'y',
                                                 -pady => 5 );

my $button_frm = $select_frm_lay->Frame(-bg => '#9BDBDB',)->pack(-side=>'bottom',-fill=>'x');
my $run_button = $button_frm->Button(-text => '���',
                                          -command => sub {&run_output_gerber;},
                                          -width => 10,
										  -activebackground=>'green',
										  -bg => '#9BDBDB',
										  -font=> 'charter 10 bold',
										  -height=> 2,
                                          )->pack(-side => 'left',
                                                  -padx => 15,
												  -pady => 5);

my $exit_button = $button_frm->Button(-text => '�˳�',
                                          -command => sub {exit 0},
                                          -width => 10,
										  -activebackground=>'red',
										  -bg => '#9BDBDB',
										  -font=> 'charter 10 bold',
										  -height=> 2,
                                          )->pack(-side => 'right',
                                                  -padx => 15,
												  -pady => 5);

MainLoop;

##################################################################################################################################

sub OnQuit {
	my $ans = $mw3_1->messageBox(-icon => 'question',-message => '��ȷ��Ҫ�˳���',-title => 'quit',-type => 'YesNo');
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
		$tmp_layers = $sel_layer_lb->get($_);
		push(@selectlayers_tmp,$tmp_layers);
	}
	$sel_lay_no = scalar(@selectlayers_tmp);
	if ( $sel_lay_no == 0 ) {
		$sel_layer_lb->selectionSet(0,'end');
	} else {
		my @sel_lay_list = ();
		@tmp_layer = $sel_layer_lb->get(0,'end');
		#$tmp_layer_no = scalar(@tmp_layer);
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

sub scale_silk {
	#my @select_layers = @_;
    my @scale_silk_array = @_;
	my @empty = qw();
#    # if ($sh_site eq 'HDI����') {
#		foreach my $layer (@select_layers) {
#			if (grep {$_ eq $layer} @all_silk_array) {
#                # --��������ֲ㣬�����֮��
#				push(@scale_silk_array,$layer);
#			}
#		}
#	# }
	if (@scale_silk_array > 0) {
		my $dialog = $mw3_1->DialogBox(
			-title          => "�������ֲ���������@scale_silk_array",
			-buttons        => [ "����", "�˳�" ],
			-default_button => "����",
		);
		$dialog->Label(-text => '���������ֲ���������(�޶�0.9990-1.0015֮��):', -font => 'SimSun 12',)->pack(-pady => 3, -side => 'top'),
		$dialog->LabEntry(-label => '����X:',
			-labelFont           => 'SimSun 13',
			-textvariable        => \$scale_x,
			-bg                  => 'white',
			-width               => 12,
			-relief              => 'ridge',
			-labelPack           => [ qw/-side left -anchor w/ ])->pack(-padx => 20, -side => 'left', -pady => 5);
		$dialog->LabEntry(-label => '����Y:',
			-labelFont           => 'SimSun 13',
			-textvariable        => \$scale_y,
			-bg                  => 'white',
			-width               => 12,
			-relief              => 'ridge',
			-labelPack           => [ qw/-side left -anchor w/ ])->pack(-padx => 5, -side => 'left', -pady => 5);
		my $button = $dialog->Show();
		if ($button eq "����") {
			if ($scale_x > 1.0015 || $scale_x < 0.999) {
				$mw3_1->messageBox(
					-icon    => 'warning',
					-message => "���������Xֵ($scale_x)�������Ʒ�Χ0.9990-1.0015!",
					-title   => '�����������Ʒ�Χ!',
					-type    => 'Ok');
                exit 0;
			}
			if ($scale_y > 1.0015 || $scale_y < 0.999) {
				$mw3_1->messageBox(
					-icon    => 'warning',
					-message => "���������Yֵ($scale_y)�������Ʒ�Χ0.9990-1.0015!",
					-title   => '�����������Ʒ�Χ!',
					-type    => 'Ok');
				exit 0;
			}
		}
		else {
            exit 0;
		}
	}
	return @scale_silk_array;
}

sub add_scale_content {
	# --���ֲ��������ϵ��
	my $layer = shift;
	my $xCoord = 0;
	my $yCoord = 0;
	my $job_n_x = 0;
	my $job_n_y = 0;
    my $text_content = "x=$scale_x y=$scale_y";
	$f->COM("open_entity,job=$job_name,type=step,name=$sel_step,iconic=no");
	$f->AUX("set_group,group=$f->{COMANS}");
	$f->COM("units,type=inch");
	$f->COM("clear_layers");
	$f->COM("affected_layer,mode=all,affected=no");
	$f->COM("affected_layer,name=$layer,mode=single,affected=yes");
	$f->COM("filter_reset,filter_name=popup");
	$f->COM("filter_set,filter_name=popup,update_popup=no,include_syms=sh-opnew*");
	$f->COM("filter_area_strt");
	$f->COM("filter_area_end,layer=,filter_name=popup,operation=select,area_type=none,inside_area=no,intersect_area=no,lines_only=no,ovals_only=no,min_len=0,max_len=0,min_angle=0,max_angle=0");
	$f->COM("filter_reset,filter_name=popup");
	$f->COM("get_select_count");
	if ($f->{COMANS} == 1) {
		#get the feature.
		my @file_list = ();
		my $stat_file = "$tmpPath/tmp.feature";
		$f->COM("info,out_file=$stat_file,units=inch,args=-t layer -e $job_name/panel/$layer -d FEATURES -o select");
		if (-e $stat_file) {
			open(STAT, $stat_file) or die "can't open file $stat_file: $!";
			while (<STAT>) {
				push(@file_list, $_);
			}
			close(STAT);

			foreach $line (@file_list) {
				if ($line ne "") {
					my @column = split(' ', $line);
					if (@column[0] eq "#P") {
						$job_n_x = @column[1];
						$job_n_y = @column[2];
					}
				}
			}
		}
		$f->COM("sel_clear_feat");
	}
    $f->COM("cur_atr_reset");
    $f->COM("cur_atr_set,attribute=.ignore_action");	
	$f->DO_INFO("-t layer -e $job_name/panel/$layer -m script -d SIDE");
	#�������ݲ������жϼӵ�ϵ��λ���Ƿ���ȷ
	$f->VOF();
	$f->COM("delete_layer,layer=cm_scalctext");
	$f->COM("delete_layer,layer=cm_scalctext_tmp");
	$f->COM("create_layer,layer=cm_scalctext,context=misc,type=signal,polarity=positive,ins_layer=");
	$f->COM("create_layer,layer=cm_scalctext_tmp,context=misc,type=signal,polarity=positive,ins_layer=");
	$f->VON();
	$f->COM("sel_copy_other,dest=layer_name,target_layer=cm_scalctext_tmp,invert=no,dx=0,dy=0,size=0,x_anchor=0,y_anchor=0,rotation=0,mirror=none");
	$f->COM("affected_layer,name=cm_scalctext,mode=single,affected=yes");	
	
    if ( $f->{doinfo}{gSIDE} eq "top" ) {
		# --top�����ֲ���Ҫ����
        $xCoord = $job_n_x + 0.2;
		$yCoord = $job_n_y - 1.27;
		$f->COM("add_text,attributes=no,type=string,x=$xCoord,y=$yCoord,text=$text_content,x_size=0.1,y_size=0.1,w_factor=1,polarity=positive,angle=270,mirror=no,fontname=standard,ver=1");
		
	} else {
		# --bot�����־���
		$xCoord = $job_n_x + 0.2;
		$yCoord = $job_n_y + 1.27;
        $f->COM("add_text,attributes=no,type=string,x=$xCoord,y=$yCoord,text=$text_content,x_size=0.1,y_size=0.1,w_factor=1,polarity=positive,angle=90,mirror=yes,fontname=standard,ver=1");
	}
	$f->COM("cur_atr_reset");
	$f->COM("affected_layer,name=$layer,mode=single,affected=no");
	#�ж�ϵ��λ��
	$f->COM("sel_ref_feat,layers=cm_scalctext_tmp,use=filter,mode=touch,pads_as=shape,f_types=line\;pad\;surface\;arc\;text,polarity=positive\;negative,include_syms=,exclude_syms=");
	$f->COM('get_select_count');
	if ( $f->{COMANS} > 0 ){		
		$f->COM("affected_layer,name=cm_scalctext,mode=single,affected=no");
		$f->COM("affected_layer,name=$layer,mode=single,affected=yes");
		$c->Messages('warning', '��⵽ϵ�������������ص�,���ֶ��ƿ�');
		$f->COM("display_layer,name=$layer,display=yes,number=1");		
		$f->PAUSE("please remove scale_text!");
		$f->COM("display_layer,name=$layer,display=no,number=1");	
		$f->COM("affected_layer,name=$layer,mode=single,affected=no");		
	}else{
		$f->COM("affected_layer,name=cm_scalctext,mode=single,affected=no");
	}	
	$f->VOF();
	$f->COM("delete_layer,layer=cm_scalctext");	
	$f->COM("delete_layer,layer=cm_scalctext_tmp");	
	$f->VON();	
	system("python /incam/server/site_data/scripts/hdi_scr/Output/output_gerber_hdi/check_scale_text.py $job_name $layer $text_content");
}

################################################################################################################################################################################
sub run_output_gerber {
	my @selectlayers = ();
	foreach($sel_layer_lb->curselection()){
		$tmp_layers = $sel_layer_lb->get($_);
		push(@selectlayers,$tmp_layers);
	}
	my $layer_no = scalar(@selectlayers);
	if ( $layer_no == 0 ) {
		&run_message_no_sel;
		$button_frm->withdraw;
	}



	$mw3_1->iconify();
	if ( $sel_step ne "panel") {
		$do_gerber_path = $do_gerber_path . '/' . $sel_step;
		if (! -d $do_gerber_path ) {
			mkdir $do_gerber_path;
		}
	}
	# === 2022.05.31 ����������Ϊ���ֲ㣬��Ϊ318ϵ�У������panel��gerberʱ�����ڼ�� ===

	my %hash_job_silk = map{$_=>1} @all_silk_array; 
	#my %hash_select = map{$_=>1} @selectlayers; 
	my @common = grep {$hash_job_silk{$_}} @selectlayers; 
	print Dumper(\@common);
	my $cus_name = substr("$job_name", 1, 3);
	if ($cus_name eq "318" and $sel_step eq "panel" and @common) {
		my $get_return = system("python $scriptPath/hdi_scr/Panel/chk_date_code/chk_date_code.py");
		if ($get_return != 0) {
			exit 0;
		}
	}
	my @scale_silk_array;
	#����֪ͨȡ�����ڼ�� ѡ�е����ֲ㶼Ҫ���� 20230724 by lyh
	# if ($sel_step eq "panel" and @common) {
		# foreach my $tmp_silk(@common) {
			# my $get_return = system("python $scriptPath/hdi_scr/Panel/chk_date_code/check_date_code_exist.py $tmp_silk");
			# if ($get_return != 0) {
				# push @scale_silk_array,$tmp_silk;
			# }
		# }
	# }
	if ($sel_step eq "panel" and @common) {		
		foreach my $tmp_silk(@common) {
			push @scale_silk_array,$tmp_silk;
		}
	}
	print '@scale_silk_array';
	print Dumper(\@scale_silk_array);
	#exit 0;
	
	# === TODO �����жϣ�ѡ������ֲ��Ƿ�������
	#@scale_silk_array
	@scale_silk_array = &scale_silk(@scale_silk_array);
	
	if ( $sel_step eq "set" or $sel_step eq "edit") {
		$f->COM("open_entity,job=$job_name,type=step,name=edit,iconic=no");
		$f->AUX("set_group,group=$f->{COMANS}");
		$f->COM("units,type=inch");
		
		#ȡ���г������İ����� �����ͺ�h32310oba36b1 ������ж�λpad 20231127 by lyh
		#http://192.168.2.120:82/zentao/story-view-6254.html
		foreach my $tmp (@selectlayers) {
			if ( $tmp eq "p1" or $tmp eq "p2" or $tmp eq "pp" ) {
				$f->COM("clear_layers");
				$f->COM("affected_layer,mode=all,affected=no");
				$f->COM("affected_layer,name=$tmp,mode=single,affected=yes");
				# $f->COM("clip_area_strt");
				# $f->COM("clip_area_end,layers_mode=affected_layers,layer=,area=profile,area_type=rectangle,inout=outside,contour_cut=no,margin=-2");
				$f->COM("filter_reset,filter_name=popup");
				$f->COM("filter_set,filter_name=popup,update_popup=no,profile=out");
				$f->COM("filter_area_strt");
				$f->COM("filter_area_end,layer=,filter_name=popup,operation=select,area_type=rectangle,inside_area=no,intersect_area=no");
				$f->COM('get_select_count');
				my $count = $f->{COMANS};
				if ($count > 0){
					$c->Messages('warning', "��⵽����${tmp} ��profile���������������ͣ���,��ȷ���Ƿ��쳣?");
					$f->PAUSE("PLEASE CHECK!");				
				}
				$f->COM("clear_layers");
				$f->COM("affected_layer,mode=all,affected=no");
			}
		}

		if ( $sel_step eq "set" ) {
			$f->COM("open_entity,job=$job_name,type=step,name=$sel_step,iconic=no");
			$f->AUX("set_group,group=$f->{COMANS}");
#			$f->COM("sredit_reduce_nesting,mode=one_highest");
		}
#		foreach my $tmp (@selectlayers) {
#			$f->COM("clear_layers");
#			$f->COM("affected_layer,mode=all,affected=no");
#			$f->COM("affected_layer,name=$tmp,mode=single,affected=yes");
#			$f->COM("sel_contourize,accuracy=0.25,break_to_islands=yes,clean_hole_size=3,clean_hole_mode=x_and_y");
#			$f->COM("clear_layers");
#			$f->COM("affected_layer,mode=all,affected=no");
#		}
	}

	$f->COM("units,type=inch");
	$f->INFO( entity_type => 'step',entity_path => "$job_name/$sel_step",data_type => 'SR_LIMITS');
	our $LimitMinX = $f->{doinfo}{gSR_LIMITSxmax} - $f->{doinfo}{gSR_LIMITSxmin} ;
	our $LimitMinY = $f->{doinfo}{gSR_LIMITSymax} - $f->{doinfo}{gSR_LIMITSymin} ;

	$f->INFO( entity_type => 'step',entity_path => "$job_name/$sel_step",data_type => 'PROF_LIMITS');
	our $LimitMaxX = ($f->{doinfo}{gPROF_LIMITSxmax} - $f->{doinfo}{gPROF_LIMITSxmin} ) + 1;
	our $LimitMaxY = ($f->{doinfo}{gPROF_LIMITSymax} - $f->{doinfo}{gPROF_LIMITSymin} ) + 1;
	our $prof_center_x = $f->{doinfo}{gPROF_LIMITSxmax}/2 + $f->{doinfo}{gPROF_LIMITSxmin}/2;
	our $prof_center_y = $f->{doinfo}{gPROF_LIMITSymax}/2 + $f->{doinfo}{gPROF_LIMITSymin}/2;

	my $OutputSuffix = '_output_tmp++';
	my $break_symbol;
	foreach my $tmp (@selectlayers) {
		$f->COM("clear_layers");
		$f->COM("affected_layer,mode=all,affected=no");
		# --������޸�20200701����Ϊ�������ʱ��pad,���Բ���ɢ�����ͭƤ
		# --20200715����ʴ�����߲�each-c/s,etch-c/s
		# --2725�������Ҫȡ�����ʱ��ɢ��ȡ��decomposeָ��  AresHe 2021.3.10
		#&decomposeSurface($sel_step,$tmp,'surface=copper') if ( $sel_step eq 'panel' && $tmp !~ /^md[1,2]-?(\w+)?-?(\w+)?$/ && $tmp !~ /^e[a,t]ch-[c,s]-?(\w+)?-?(\w+)?$/);
		#http://192.168.2.120:82/zentao/story-view-4718.html ���ֿͻ�Ҫ�����������ʵ��������� �ʲ��ܴ�ɢ��� 20221114 by Lyh
		$break_symbol="yes";
		if ($tmp eq "p1" or $tmp eq "p2"){				
			$break_symbol="no";
		}
		$f->COM("clear_layers");
		$f->COM("output_layer_reset");
		if ( $sel_step eq "set" ){
			$f->VOF;
			$f->COM('delete_layer', layer => $tmp . $OutputSuffix);
			$f->VON;
			$f->COM('optimize_levels' ,layer => $tmp,opt_layer => $tmp . $OutputSuffix ,levels => 1 ,);
			my $OrgFile = $do_gerber_path . '/' . $tmp;
			my $tmpOutputFile = $do_gerber_path . '/' . $tmp . $OutputSuffix;
			$OrgFile =~ s#\\#/#g;
			$tmpOutputFile =~ s#\\#/#g;

			if ( -e $OrgFile ){
				unlink($OrgFile) or warn "Could not unlink $OrgFile: $!";
			}
			$f->COM('output_layer_set' ,layer => $tmp . $OutputSuffix ,angle => 0 ,mirror => 'no' ,x_scale => 1 ,y_scale => 1 ,comp => 0 ,polarity => 'positive' ,setupfile => '' ,setupfiletmp => '' ,line_units => 'inch' ,gscl_file => '' ,);
			$f->COM('output' ,job => $job_name ,step => $sel_step ,format => 'Gerber274x' ,dir_path => $do_gerber_path ,prefix => '' ,suffix => '' ,break_sr => 'yes' ,break_symbols => 'yes' ,break_arc => 'no' ,scale_mode => 'all' ,surface_mode => 'contour' ,min_brush => 1 ,units => 'inch' ,coordinates => 'absolute' ,zeroes => 'none' ,nf1 => 2 ,nf2 => 6 ,x_anchor => 0 ,y_anchor => 0 ,wheel => '' ,x_offset => 0 ,y_offset => 0 ,line_units => 'inch' ,override_online => 'yes' ,film_size_cross_scan => 0 ,film_size_along_scan => 0 ,ds_model => 'RG6500' ,);
			$f->VOF;
			$f->COM('delete_layer', layer => $tmp . $OutputSuffix);
			$f->VON;
			rename($tmpOutputFile,$OrgFile) or warn "Unable to rename file $tmpOutputFile: $!";
			#move($tmpOutputFile,$OrgFile) or warn "Unable to rename file $tmpOutputFile: $!";
		} else {
			if (grep {$_ eq $tmp} @scale_silk_array) {
				# --���������Ϣ
				&add_scale_content($tmp);
                # --��������ֲ㣬�����֮��
				$f->COM("output_layer_set,layer=$tmp,angle=0,mirror=no,x_scale=$scale_x,y_scale=$scale_y,comp=0,polarity=positive,setupfile=,setupfiletmp=,line_units=inch,gscl_file=");
			} else {
				$f->COM("output_layer_set,layer=$tmp,angle=0,mirror=no,x_scale=1,y_scale=1,comp=0,polarity=positive,setupfile=,setupfiletmp=,line_units=inch,gscl_file=");
			}

            #2019.12.9������޸�gen_line_post_skip_hooks config����Ϊ2
            #�˴�ǿ��ִ��output_layer_set.post hooks
            #=======================================================================================
			if ( $^O eq 'linux' ) {
				my $output_set_file = "/tmp/output_set_parameter.$$";
				open(PARAM_SET,">$output_set_file") or die("$!");
				print PARAM_SET "set lnPARAM = ('layer'        'angle'        'mirror'       'x_scale'      'y_scale'      'comp'     'polarity'    'setupfile'    'setupfiletmp' 'line_units'   'gscl_file' )\n";
				print PARAM_SET "set lnVAL   = ('$tmp'         '0'            'no'           '1'            '1'            '0'        'positive'    ''             ''             'inch'         ''          )\n";
				close (PARAM_SET);
				
				$f->COM('script_run',name=>"/incam/server/site_data/hooks/line_hooks/output_layer_set.post",params=>"$output_set_file");
				
				unlink($output_set_file);
	
				my $param_file = "/tmp/output_parameter.$$";
				open(PARAM,">$param_file") or die("$!");
				print PARAM "set lnPARAM = ('job'           'step'           'dir_path'        'prefix'      'suffix'            'x_anchor'          'y_anchor'   'x_offset'      'y_offset'  'line_units'    'format' 'break_sr'      'break_symbols'  'break_arc'       'scale_mode'  'surface_mode'      'min_brush'         'units'      'coordinates'   'zeroes'    'nf1'           'nf2' 'decimal'        'modal'         'tool_units'      'optimize'    'iterations'        'reduction_percent' 'canned_text' )\n";
				print PARAM "set lnVAL   = ('$job_name'     '$sel_step'      '$do_gerber_path' ''            ''                  '0'                 '0'         '0'             '0'         'inch'           'Gerber274x' 'yes'           '$break_symbol'            'no'              'all'         'contour'           '1'                 'inch'      'absolute'      'none'      '2'              '6' 'no'            'no'             'inch'            'no'          '5'                 '1'                 'break'     )\n";
				close (PARAM);
				
				$f->COM('script_run',name=>"/incam/server/site_data/hooks/line_hooks/output.pre",params=>"$param_file");
				
				unlink($param_file);
			}
            #=======================================================================================

			if (grep {$_ eq $tmp} @scale_silk_array) {
				# --��������ֲ㣬��profile��������
				$f->COM("output,job=$job_name,step=$sel_step,format=Gerber274x,dir_path=$do_gerber_path,prefix=,suffix=,break_sr=yes,break_symbols=$break_symbol,break_arc=no,scale_mode=all,surface_mode=contour,min_brush=1,units=inch,coordinates=absolute,zeroes=none,nf1=2,nf2=6,x_anchor=$prof_center_x,y_anchor=$prof_center_y,wheel=,x_offset=0,y_offset=0,line_units=inch,override_online=yes,film_size_cross_scan=0,film_size_along_scan=0,ds_model=RG6500");
			} else {
				$f->COM("output,job=$job_name,step=$sel_step,format=Gerber274x,dir_path=$do_gerber_path,prefix=,suffix=,break_sr=yes,break_symbols=$break_symbol,break_arc=no,scale_mode=all,surface_mode=contour,min_brush=1,units=inch,coordinates=absolute,zeroes=none,nf1=2,nf2=6,x_anchor=0,y_anchor=0,wheel=,x_offset=0,y_offset=0,line_units=inch,override_online=yes,film_size_cross_scan=0,film_size_along_scan=0,ds_model=RG6500");
			}
		}
		$f->COM("disp_on");
		$f->COM("origin_on");
	}

	if ( $sel_step eq 'panel'  ) {
		#$f->COM("check_inout,mode=in,type=job,job=$job_name");
		$f->COM("close_job,job=$job_name");
		#$f->COM("close_form,job=$job_name");
		#$f->COM("close_flow,job=$job_name");
		#$f->COM("check_inout,mode=out,type=job,job=$job_name");
		$f->COM("clipb_open_job,job=$job_name,update_clipboard=view_job");
		$f->COM("open_job,job=$job_name");
	}
	my @warn_message_list;
	my @ok_message_list;
	if ( $GerberReread eq 1 ) {
#		if ( $sel_step eq "panel" ) {
			$f->COM("open_entity,job=$job_name,type=step,name=$sel_step,iconic=no");
			$f->COM("units,type=inch");
			$f->COM("clear_layers");
			$f->COM("affected_layer,mode=all,affected=no");
			foreach my $tmp (@selectlayers) {
				my $do_path_input = "$do_gerber_path/$tmp";
				my $new_lp_name = "$tmp.gerber";
				$f->COM("input_manual_reset");
				$f->COM("input_manual_set,path=$do_path_input,job=$job_name,step=$sel_step,format=Gerber274x,data_type=ascii,units=inch,coordinates=absolute,zeroes=leading,nf1=2,nf2=6,decimal=no,separator=*,tool_units=inch,layer=$new_lp_name,wheel=,wheel_template=,nf_comp=0,multiplier=1,text_line_width=0.0024,signed_coords=no,break_sr=yes,drill_only=no,merge_by_rule=no,threshold=200,resolution=3");
				$f->COM("input_manual,script_path=");
				$f->COM("matrix_layer_context,job=$job_name,matrix=matrix,layer=$new_lp_name,context=misc");
				# === TODO �ж�input�����Ĳ���Ƿ������ݣ����û�п����϶�input���� ===
				$f->DO_INFO("-t layer -e $job_name/$sel_step/$new_lp_name -d FEAT_HIST");
				my $feat_num = $f->{doinfo}{gFEAT_HISTtotal};
				if ($feat_num == 0) {
					$c->Messages('warning', "${tmp} δ����ȷ�ض� ${new_lp_name} \n\n��ɾ��������ļ�!\n ���ں�̨�ն˲鿴������Ϣ���������Ϻ��ٴ����!\n Ps:SIP���������:Self");
					unlink $do_path_input;
				} else {
					if (grep {$_ eq $tmp} @scale_silk_array) {
                        # --HDI�������ֲ�ض��������֮��������ȶԲ�һ��
						$transform_x = 1/$scale_x;
						$transform_y = 1/$scale_y;
						$f->COM("affected_layer,name=$new_lp_name,mode=single,affected=yes");
						$f->COM("sel_transform,mode=anchor,oper=scale,duplicate=no,x_anchor=$prof_center_x,y_anchor=$prof_center_y,angle=0,x_scale=$transform_x,y_scale=$transform_y,x_offset=0,y_offset=0");
						$f->COM("affected_layer,name=$new_lp_name,mode=single,affected=no");
					}
					# --���ȶԣ���������20200701����Ϊ�������ʱ��pad
					# --20200715����ʴ�����߲�each-c/s,etch-c/s
					# --------------------------------------------------------------------------------------------------------
					#if ($tmp =~ /^md[1,2]-?(\w+)?-?(\w+)?$/ || $tmp =~ /^e[a,t]ch-[c,s]-?(\w+)?-?(\w+)?$/) {
					my $result = &compare_layer($sel_step,$tmp,$new_lp_name);
					if ($result > 0) {
						if (grep {$_ eq $tmp} @scale_silk_array) {
							push @warn_message_list, "${tmp} �� ${new_lp_name}��Ϊ���������ϵ��, �ȶԲ�һ��,\n��ȷ���Ƿ���������һ��!\n";
						} else {
							push @warn_message_list, "${tmp}��${new_lp_name}�ȶԲ�һ��,\n\n��ɾ��������ļ�!�Ժ����������!\n";
							unlink $do_path_input;
						}

					} else {

						push @ok_message_list,"${tmp} �� ${new_lp_name} ���ȶ�һ��!";

					}
				}
				#}
				# --------------------------------------------------------------------------------------------------------
			}
#		}
		my $word = 'Gerber�����';
		if (scalar @warn_message_list > 0) {
			$word  .= "�ȶԲ�һ�²������:\n" . join "\n", @warn_message_list;
		}
		if (@ok_message_list) {
			$word  .= "�ȶ�һ�µĲ������:\n" . join "\n", @ok_message_list;
		}
		
		&run_message_over('question',$word,'waiting');
		#exit 0;
	}
}

sub run_message_no_sel {
	my $ans0 = $mw3_1->messageBox(-icon => 'question',-message => 'û��ѡ��Ҫ����Ĳ�,������ѡ��!',-title => 'quit',-type => 'YesNo');
	return if $ans0 eq "Yes";
	exit 0;
}

sub run_message_over {
    my ($icon_type,$show_text,$title) = @_;
	my $mw = MainWindow->new( -title =>"VGT");
	$mw->title("�ȶԽ��");  
	$mw->geometry("400x600+800+80");
	$mw->raise( );
	# �����ɹ����ı���  
	my $text = $mw->Scrolled('Text', -scrollbars => 'oe')->pack(-side => 'top', -fill => 'both', -expand => 1);  
	$text->insert('end', $show_text);
	$text->configure(-font => 'Arial 14');
	
	#my $ans0 = $mw->messageBox(-icon => 'question',-bitmapname  => $text, -title => 'quit',-type => 'YesNo');
	# ����ȷ����ť  
	my $ok_button = $mw->Button(  
		-text => 'OK',  
		-command => sub {exit 0}, 
	)->pack(-side => 'bottom');  
	  
	#exit 0;
}


sub decomposeSurface		## by hyp, Jan 11, 2018
{
	my ($step,$layer,$attr) = @_;

	my ($attribute,$text) = $attr =~ /^([^=]*)=([^=]*)$/;

	$f->COM("set_step,name=$step");
	$f->COM("clear_layers");
	$f->COM("affected_layer,mode=all,affected=no");
	$f->COM('filter_reset,filter_name =popup');    

	
	my $bakLayer = $layer.'-bak-output';
	$f->VOF;
		$f->COM("delete_layer,layer=$bakLayer");
	$f->VON;
	$f->COM("create_layer,layer=$bakLayer,context=misc,type=signal,polarity=positive,ins_layer=");
	$f->COM("copy_layer,source_job=$job_name,source_step=$step,source_layer=$layer,dest=layer_name,dest_step=,dest_layer=$bakLayer,mode=replace,invert=no,copy_notes=no,copy_attrs=no,copy_lpd=new_layers_only,copy_sr_feat=no");

	my $tmpLayer = 'tmplayer___';
	$f->VOF;
		$f->COM("delete_layer,layer=$tmpLayer");
	$f->VON;
	$f->COM("create_layer,layer=$tmpLayer,context=misc,type=signal,polarity=positive,ins_layer=");
	$f->COM("display_layer,name=$layer,display=yes");
	$f->COM("work_layer,name=$layer");

	$f->COM("reset_filter_criteria,filter_name=,criteria=all");
	$f->COM("set_filter_type,filter_name=,lines=no,pads=yes,surfaces=yes,arcs=no,text=no");
	$f->COM("set_filter_attributes,filter_name=popup,exclude_attributes=no,condition=yes,attribute=$attribute,min_int_val=0,max_int_val=0,min_float_val=0,max_float_val=0,option=,text=$text");
	$f->COM("get_select_count");
	if ( $f->{COMANS} == 0 ){
		$f->VOF;
		$f->COM("reset_filter_criteria,filter_name=,criteria=all");
		$f->COM("set_filter_type,filter_name=,lines=no,pads=no,surfaces=yes,arcs=no,text=no");
		$f->COM("units,type=inch");
		$f->COM('adv_filter_set' ,filter_name => 'popup' ,active => 'yes' ,limit_box => 'yes' ,
		min_dx => $LimitMinX , min_dy => $LimitMinY ,
		max_dx => $LimitMaxX , max_dy => $LimitMaxY ,
		bound_box => 'no' ,srf_values => 'no' ,srf_area => 'no' ,mirror => 'any' ,ccw_rotations => '' ,);

		$f->COM("filter_area_strt");
		$f->COM("filter_area_end,filter_name=popup,operation=select");
		$f->VON;
	}

	$f->COM("get_select_count");
	if ( $f->{COMANS} > 0 )
	{
		$f->COM("sel_reverse");
		$f->COM("sel_move_other,target_layer=$tmpLayer,invert=no,dx=0,dy=0,size=0,x_anchor=0,y_anchor=0");
		$f->COM('sel_break');
		$f->VOF;
		$f->COM("sel_decompose,overlap=no");
		$f->VON;
		$f->COM("copy_layer,source_job=$job_name,source_step=$step,source_layer=$tmpLayer,dest=layer_name,dest_step=,dest_layer=$layer,mode=append,invert=no,copy_notes=no,copy_attrs=no,copy_lpd=new_layers_only,copy_sr_feat=no");
	}
	$f->COM("adv_filter_reset");
	$f->COM("reset_filter_criteria,filter_name=,criteria=all");
	$f->COM("sel_clear_feat");
	$f->COM("delete_layer,layer=$tmpLayer");
	$f->COM("delete_layer,layer=$bakLayer");
	$f->COM("clear_layers");
	return 1;
}

sub compare_layer {
	# --���ȶԣ���������20200701����Ϊ�������ʱ��pad
	my ($step,$layer,$inp_layer) = @_;
    my $result = 0;
	if ( $^O ne 'linux' ) {
		$f->COM("compare_layers,layer1=$layer,job2=$job_name,step2=$step,layer2=$inp_layer,layer2_ext=,tol=1,area=global,consider_sr=yes,ignore_attr=.ignore_action,map_layer=${layer}_cmp,map_layer_res=200");
		$result = $f->{COMANS};
		$f->COM("delete_layer,layer=${layer}_cmp");
	} else {
		$f->COM("rv_tab_empty,report=graphic_compare,is_empty=yes");
		$f->COM("graphic_compare_res,layer1=$layer,job2=$job_name,step2=$step,layer2=$inp_layer,layer2_ext=,tol=1,resolution=200,area=global,ignore_attr=.ignore_action,map_layer_prefix=,consider_sr=yes");
		$result = $f->{COMANS};
		$f->COM("rv_tab_view_results_enabled,report=graphic_compare,is_enabled=yes,serial_num=-1,all_count=-1");
	}
	return $result
}

sub DialogWindow
{
    my ($content,$bg,$fg) = @_;
    $bg = '#d9d9d9' unless ($bg);
    $fg = 'black' unless ($fg);
    require Tk::Dialog;
    my $warn_win = MainWindow->new(-title =>"ʤ��Ƽ�");
    $warn_win-> withdraw();
    $warn_win->Dialog(-title=>'Dialog', -text => $content, -default_button => 'Ok', -buttons => ['Ok'], -bitmap => 'error', -font => 'monospace 12', -bg => $bg, -fg => $fg, -command => sub{$warn_win -> destroy;} ) -> Show ();
    MainLoop;
    return 1;
}


__END__

Version 2.0
2021.01.10
���ߣ�Chao.Song
1.���Gerber��ǿ�ƻض��ȶ�;
http://192.168.2.120:82/zentao/story-view-2539.html
2.���Ӵ�step������Ӱ���;

Version 2.1
2021.01.20
���ߣ�Chao.Song
1.�жϻض�����Ƿ������ݣ��ޣ�����Ϊ�ض�ʧ�ܣ�����ΪSIP���⣻SIP���������룺677002

Version 2.2
2021.3.10
���ߣ�������
1.����2725�������ʱȡ��decomposeָ���ɢsurface


Version 2.3
2021.5.31
����:�γ�
1.���ּ���windows������;
2.����Gerber�������ʾΪ���ͳһ��ʾ;
3.�������ֲ㡢318ϵ�С����������Ƿ�Ϊvgt_date_318�ļ�⡣http://192.168.2.120:82/zentao/story-view-4258.html
# 2022.11.14 by Lyh ���ֿͻ�Ҫ�����������ʵ��������� �ʲ��ܴ�ɢ��� http://192.168.2.120:82/zentao/story-view-4718.html


Version 2.4
2022.12.29
����:�γ�
1.������ֲ�Gerber������ʱ����0.9997���������http://192.168.2.120:82/zentao/story-view-4988.html


Version 2.5
2023.06.12
����:½Ԫ��
1.������ֲ�Gerber������ʱ����0.99999 0.9998���������http://192.168.2.120:82/zentao/story-view-5650.html
2.������ֲ�Gerber������ʱ����X��1.00000  Y��0.99990���������http://192.168.2.120:82/zentao/story-view-5677.html