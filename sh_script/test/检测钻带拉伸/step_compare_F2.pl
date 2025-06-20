#!c:/perl/bin/perl -w
#### by hyp, Nov 24, 2017
use strict;
use utf8;
use lib "/incam/$ENV{INCAM_RELEASE_VER_VGT}/app_data/perl/";
use incam;
use POSIX qw(strftime);

my $f = new incam();

my $job_name = $ENV{JOB};
my $step = $ENV{STEP};

$f->COM("info, out_file=/tmp/change_data_file,args= -t job -e $job_name -m script -d CHANGES");
my @change_data = readpipe("cat /tmp/change_data_file");
system("rm -rf /tmp/change_data_file");
if (scalar(@change_data) > 0 ){
	system("python /incam/server/site_data/scripts/sh_script/show_user_authority_warning/show_user_authority_warning.py check_cam_director $job_name");
	if (-e "/tmp/check_cam_director_${job_name}.log"){
		system("rm -rf /tmp/check_cam_director_${job_name}.log");
	}else{
		$f->PAUSE("检测到资料有改动，请先保存资料后再比对网络！");
		exit 0;
	}
}

&Main();

sub Main {
    unless ($job_name) {
        $f->PAUSE("The script must be run in a Job!!");
        exit(0);
    }

    for my $tmp (qw(edit net)) {
        $f->DO_INFO("-t step -e $job_name/$tmp -d EXISTS");
        if ($f->{doinfo}{gEXISTS} eq "no") {
            $f->PAUSE("$_ 不存在，程序退出.");
            exit 0;
        }
    }
    my $status = system('python /incam/server/site_data/scripts/sh_script/zl/check/CheckDrillThrough.py');
    if ($status != 0) {
        exit 0;
    }
	&check_line_touch_outline();
    &net_resize();
    &NetlistCompare('net+0.5mil');
    &NetlistCompare('net');
    &del_tmp_net();
	# &del_tmp_out();
    exit 0;
}

sub check_outline_layer {
	# === 目的：检测出铣带对资料网络的影响 ===
	# === 检测net的out中是否有内容
	$f->DO_INFO("-t layer -e $job_name/net/out -d EXISTS");
	if ($f->{doinfo}{gEXISTS} eq "no") {
		$f->PAUSE("out 层别不存在，必须存在，且其中为标准外形线，程序退出.");
		exit 0;
	}
	#$f->DO_INFO("-t layer -e $job_name/net/out -d FEAT_HIST");
	#if ($f->{doinfo}{gFEAT_HISTtotal} != 0) {
	#	$f->PAUSE("net Step中out 层别需设计为空，程序退出.");
	#	exit 0;
	#}

	# === 检查edit的out中有内容
	$f->DO_INFO("-t layer -e $job_name/edit/out -d FEAT_HIST");
	if ($f->{doinfo}{gFEAT_HISTtotal} == 0) {
		$f->PAUSE("edit Step中out 层别不能为空，程序退出.");
		exit 0;
	}

	$f->COM("set_step,name=edit");
	$f->VOF();
	my $tmp_out_layer = '__tmp_out__';
	$f->COM("delete_layer,layer=$tmp_out_layer");
	$f->VON();

	$f->COM("create_layer,layer=$tmp_out_layer, context=board, type=rout,polarity=positive, ins_layer=,location=after");
	$f->COM('clear_layers');
    $f->COM("affected_layer, mode=all, affected=no");
	#$f->COM("affected_layer, name=out, mode=single, affected =yes");
    $f->COM("copy_layer,source_job=$job_name,source_step=edit,source_layer=out,dest=layer_name,dest_layer=$tmp_out_layer,mode=replace,invert=no");

}

sub check_line_touch_outline {
	# === 目的：检测出铣带对资料网络的影响 ===
	# === 检测net的out中是否有内容
	$f->DO_INFO("-t layer -e $job_name/net/out -d EXISTS");
	if ($f->{doinfo}{gEXISTS} eq "no") {
		$f->PAUSE("out 层别不存在，必须存在，且其中为标准外形线，程序退出.");
		exit 0;
	}


	$f->DO_INFO("-t layer -e $job_name/net/out -d FEAT_HIST");
	if ($f->{doinfo}{gFEAT_HISTtotal} == 0) {
		$f->PAUSE("net Step中out 层别不能为空，程序退出.");
		exit 0;
	}

	$f->COM("set_step,name=net");
	$f->COM('clear_layers');
    $f->COM("affected_layer, mode=all, affected=no");
	
	$f->COM("affected_filter,filter=(type=signal|power_ground&context=board)");
	$f->COM("filter_reset,filter_name=popup");
	$f->COM("filter_set,filter_name=popup,update_popup=no,feat_types=line");
	$f->COM("filter_set,filter_name=popup,update_popup=no,polarity=positive");
	$f->COM("sel_ref_feat,layers=out,use=filter,mode=touch,pads_as=shape,f_types=line\;pad\;surface\;arc\;text,polarity=positive\;negative,include_syms=,exclude_syms=");
	$f->COM("get_select_count");
    my $g_num = $f->{COMANS};
	if ($g_num > 0) {
		$f->PAUSE("net Step中out层别有与信号层line相交,请确认是否影响网络");
	}
    $f->COM("affected_layer, mode=all, affected=no");
	$f->COM("filter_reset,filter_name=popup");
}


sub net_resize {
    $f->COM("copy_entity,type=step,source_job=$job_name,source_name=net,dest_job=$job_name,dest_name=net+0.5mil,dest_database=");
    $f->COM("set_step,name=net+0.5mil");
    $f->COM("clear_layers");
    $f->COM("affected_layer,mode=all,affected=no");
    $f->COM("units,type=mm");
    $f->COM("affected_filter,filter=(type=signal&context=board)");
    $f->COM("sel_resize,size=12.7,corner_ctl=no");
    $f->COM("affected_layer,mode=all,affected=no");
}

sub del_tmp_net {
    $f->DO_INFO("-t step -e $job_name/net+0.5mil -m script -d EXISTS");
    if ($f->{doinfo}{gEXISTS} eq "yes") {
        $f->COM("delete_entity,job=$job_name,type=step,name=net+0.5mil");
    }
}

sub del_tmp_out {
    $f->DO_INFO("-t layer -e $job_name/edit/__tmp_out__ -m script -d EXISTS");
    if ($f->{doinfo}{gEXISTS} eq "yes") {
        $f->COM("delete_layer,layer=__tmp_out__");
    }
}

sub NetlistCompare {
    my $compare_net = shift;
    $f->COM("set_step,name=edit");
    $f->COM("netlist_page_open,set=yes,job1=$job_name,job2=$job_name");
    $f->COM("netlist_recalc,job=$job_name,step=$compare_net,type=cur,display=top");
    $f->COM("netlist_recalc,job=$job_name,step=edit,type=cur,display=bottom");

    #2019.12.9李家兴修改，gen_line_skip_pre_hooks修改为2
    #此处强制调用pre hooks
    $f->COM('script_run', name => "/incam/server/site_data/hooks/line_hooks/netlist_compare.pre", params => "$job_name");
    $f->COM("netlist_compare,job1=$job_name,step1=$compare_net,type1=cur,job2=$job_name,step2=edit,type2=cur,display=yes");

    my $result = $f->{COMANS};
    my @result_list = split(/ /, $result);
    my $result_short = $result_list[0];
    my $result_open = $result_list[2];

    #2019.12.9李家兴修改，gen_line_skip_post_hooks修改为2
    #此处强制调用post hooks
    $f->COM('script_run', name => "/incam/server/site_data/hooks/line_hooks/netlist_compare.post", params => "$job_name");

    $f->COM("get_job_path,job=$job_name");
    my $netlistCompareResultFile = $f->{COMANS} . '/user/last_netlist_compare_log';
    unlink $netlistCompareResultFile;
    $f->COM("netlist_save_compare_results,output=file,out_file=$netlistCompareResultFile");
    # 0 Shorts 3 Brokens 2 Missings 0 Extras 0 Missings SMD/BGA 0 Extras SMD/BGA

    require Tk::Dialog;
    my $mw = MainWindow->new(-title => "");
    if ($result_short != 0 || $result_open != 0) {
        $mw->Dialog(-title => 'Dialog',
            -fg            => 'red',
            -text          => "网络比对异常：Step=$compare_net Short=$result_short Open=$result_open", -default_button => 'Ok',
            -buttons       => [ 'Ok' ],
            -bitmap        => 'error')->Show();
        if ($compare_net eq 'net+0.5mil') {
            # --不删除net+0.5mil的step,要查看报告
            # &del_tmp_net();
            exit(0);
        }
    }
    else {
        if ($compare_net eq 'net') {
            $mw->Dialog(-title  => 'Dialog',
                -text           => "网络比对OK",
                -default_button => 'Ok',
                -buttons        => [ 'Ok' ],
                -bitmap         => 'error')->Show();
            $f->COM("netlist_page_close");
            $f->COM("set_step,name=$step");
        }
    }
    return 1;
}


__END__
2022.09.06
Song
V1.1
1.增加外形层out的网络比对：使用edit的out层生成临时rout board层,进行与net的网络比对;
http://192.168.2.120:82/zentao/story-view-4606.html






