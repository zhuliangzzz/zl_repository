#!/usr/bin/perl -w
use Tk;
use encoding 'euc_cn';
use File::Copy;
use File::Copy::Recursive qw(fcopy rcopy dircopy fmove rmove dirmove);
require Tk::LabFrame;
require Tk::LabEntry;

# --�����Զ��幫��pm
use lib "$ENV{SCRIPTS_DIR}/sys/scripts/Package";
use Genesis;
use mainVgt;  
use Data::Dumper;
     
# --ʵ��������
my $f = new Genesis();
my $GEN = new mainVgt();

my $job_name = $ENV{JOB};
my $username = $GEN->GET_USER_NAME();
# --����ϵͳ���岻ͬ�Ĳ���
if ( $^O ne 'linux' ) {
    our $scriptPath = "$ENV{SCRIPTS_DIR}/sys/scripts";
    our $do_tgz_path = "D:/disk/film/$job_name";
    
} else {
    our $scriptPath = "$ENV{SCRIPTS_DIR}/sys/scripts";
    our $do_tgz_path = "/id/workfile/film/$job_name";
}

my $images_path = "$scriptPath/sh_script/output/images";

#my $jobname_no = length($job_name);
#if ( $jobname_no != 13 ) {
#	&run_message_not_right;
#	# exit 0;
#}

# === 2022.08.23 
&check_job_save();

my $client_no = substr($job_name, 1,3);
my $version = substr($job_name,-2,2); 
#my $path_client = "/windows/33\.file/$client_no\ϵ��";
#if (! -d $path_client ) {
#	mkdir "$path_client";
#}
my $pn_7 = substr($job_name,6,1);
if ($pn_7 eq "h" or $pn_7 eq "l") {
	$GEN->Messages('info', "������ʾ:�������������Ƿ��з���������,���������20mil.");
}

#1�� ���TGZ����������Ŀ�����osp+������Ϻţ�ץȡ�����������TGZ���ѣ���ע�⡮���Ϳ顯�谴�ջ����������������ϡ�
#2����Զƽ��Ҳ�������ѣ����TGZ���ѣ���ע�⡮���Ϳ顯�谴�ջ����������������ϡ�20221110
system("python /incam/server/site_data/scripts/lyh/sh_hdi_check_rules.py check_silk_for_face_tech_condition");

#��������ڲ㻹��ȫ�� �˽������� �����ж���ֲ��sh_hdi_warning_director_process.py�� 20241024
# system("rm -rf /tmp/all_output_type_$job_name");
# system("rm -rf /tmp/inner_output_type_$job_name");
# system("python /incam/server/site_data/scripts/lyh/output_tgz_inner_outer_ui_test.py $job_name");
if ( -e "/tmp/all_output_type_$job_name"){	
	$ENV{OUTPUT_TGZ_TYPE}="ALL";
}
if ( -e "/tmp/inner_output_type_$job_name"){	
	$ENV{OUTPUT_TGZ_TYPE}="INNER";
}
system("rm -rf /tmp/all_output_type_$job_name");
system("rm -rf /tmp/inner_output_type_$job_name");
if (-e "/tmp/exit_script_run_$job_name"){
	system("rm -rf /tmp/exit_script_run_$job_name");
	exit 0;
}


#���TGZ���ӿ��أ�1�����NPTH���Ƿ�����ͭƤ����8mil��(�������TGZ����⣩��û����ͭƤ�����޸ġ�
# 2�����NPTH���Ƿ���ڷ������������㡣��������TGZ��⣩��δ���ڿ��������������޸ġ�
# 3�����NPTH�׶�Ӧ��sgt-c,sgt-s���Ƿ���ڿ�������������TGZ��⣩��δ���ڿ��������޸ġ� 
# 5�����TGZ���Ӽ���ά������������ݲ��ʶ�𣩡�
#system("python /incam/server/site_data/scripts/lyh/sh_hdi_check_rules.py check_barcode_condition");�ϲ���check_npth_hole_condition���м��
#http://192.168.2.120:82/zentao/story-view-4696.html 20221116 by lyh
#����ĵ�ȫ�Զ��������� 20230417 by lyh
# system("rm -rf /tmp/exit_script_run_$job_name");
# system("python /incam/server/site_data/scripts/lyh/sh_hdi_check_rules.py check_npth_hole_condition");
# if (-e "/tmp/exit_script_run_$job_name"){
	# system("rm -rf /tmp/exit_script_run_$job_name");
	# exit 0;
# }

#http://192.168.2.120:82/zentao/story-view-5006.html ����Ŀ�ĵ����tgzʱ��� 20221227 by lyh δ���� ��ʱ����20230105
# system("python /incam/server/site_data/scripts/lyh/sh_hdi_check_rules.py check_mai_hole_lp_hole_condition");
# if (-e "/tmp/exit_script_run_$job_name"){
	# system("rm -rf /tmp/exit_script_run_$job_name");
	# exit 0;
# }

#���˫�濪�����Ƿ��������� ��ʾ20221215 by lyh
# �Ѿ���ֲ��ȫ�Զ��������У��������ȡ��  ynh

# system("python /incam/server/site_data/scripts/lyh/sh_hdi_check_rules.py check_plug_hole_condition");

#http://192.168.2.120:82/zentao/story-view-5022.html
#3.���TGZʱ���LED���п�����ʱ����Ƿ�Ҫ�����ͭPad 20230105 by lyh
system("python /incam/server/site_data/scripts/lyh/sh_hdi_check_rules.py check_kz_hole_add_pad_for_outer_layer");

#http://192.168.2.120:82/zentao/story-view-5034.html
# ���tgzʱ��ʾcam������ �п���ϳ����Ҫ��ͭ 20230105 by lyh
system("python /incam/server/site_data/scripts/lyh/sh_hdi_check_rules.py check_ks_rout_condition");


###���940ϵ���Ƿ�����drill_map ������� by ������ 2022/03/24
$GEN->GET_ATTR_LAYER("$job_name","all");
if ($client_no=~/940/){
	if (!grep /^drill-map$/,@{$GEN->{getlayer}}){
		
		my $re;
		if($^O=~/Win/i){
			$re=`python Z:/incam/genesis/sys/scripts/sh_script/COMGG/password.py`;
		}else{
			$re=`python /incam/server/site_data/scripts/sh_script/COMGG/password.py`;
		}
		my $ss=(split /------/,$re)[1];
		
		if ($ss!~/ok/){
			exit;
		}	
	}
}

# === ����Ϻ��е�Ring�Ƿ�Ͳ���ģ���ֵһ�� , ��������TGZʱ���⣬ת�Ƶ������Ŀ����ȥ
if($^O=~/Linux/i){
	my $get_re = system("python /incam/server/site_data/scripts/hdi_scr/Signal/run_check/get_checklist_result.py");
	#print $get_re . "\n";
	#print 'xxxxxxxxxxxxxxxxx' . "\n";
	if ($get_re != 0) {
		$GEN->Messages('info', "����Ringһ���Լ��δͨ��,���tgz������ֹ��");
		exit 0;
	}
	$f->COM("save_job,job=$job_name,override=no");
}

#####end#######by ������ 2022/03/24#####
if (! -d $do_tgz_path ) {
	mkdir "$do_tgz_path";		
}

# --��Ϊ202�ͻ�����ַ���ʱ�����������������£�
if ($client_no eq '202')
{
    &cusNum202_check($client_no);
}


#my $do_tgz_path = "/windows/33\.file/$client_no\ϵ��/$job_name/$version";
#if (! -d $do_tgz_path ) {
#	mkdir "$do_tgz_path";
#}

#my $path_tmp_job = "/tmp";
#if (! -d $path_tmp_job ) {
#	mkdir "$path_tmp_job";
#}

# 20211116�������ӣ����tgzǰ������־����Ƿ���ȷ
if ($GEN->STEP_EXISTS($job_name, 'panel') eq 'yes') {
	my $source_script_genesis = 'Z:/incam/genesis/sys/scripts/sh_script/silk_mirror_chk/silk_mirror_chk.py';
	my $source_script_incam = '/incam/server/site_data/scripts/sh_script/silk_mirror_chk/silk_mirror_chk.py';
	my $chk_status;
	if ($^O ne 'linux') {
		$chk_status = system("python $source_script_genesis panel");
	}
	else {
		$chk_status = system("python $source_script_incam panel");
	}
	print "\$chk_status : $chk_status\n";
	# ���systemִ�н��Ϊ���㣬��ʾ���־����⵽�쳣��Ҫ�˳�
	exit 0 if ($chk_status != 0);
	
	# === 2022.09.05 �������tgz��ͼ��symbol�ļ��  ===
	if ($ENV{OUTPUT_TGZ_TYPE} eq "ALL"){
		$source_script_genesis = 'Z:/incam/genesis/sys/scripts/hdi_scr/Signal/run_check/check_tudian.py';
		$source_script_incam = '/incam/server/site_data/scripts/hdi_scr/Signal/run_check/check_tudian.py';
		if ($^O ne 'linux') {
			$chk_status = system("python $source_script_genesis");
		}
		else {
			$chk_status = system("python $source_script_incam");
		}
		print "\$chk_status : $chk_status\n";
		# ���systemִ�н��Ϊ���㣬��ʾ���־����⵽�쳣��Ҫ�˳�
		exit 0 if ($chk_status != 0);
	}
}

# ���TGZǰɾ�����е�checklist 2023-12-25 ynh
system("python /incam/server/site_data/scripts/sh_script/output/del_checklist.py");

# 2019.12.5������޸ģ�gen_line_skip_pre_hooks�Ѿ�����Ϊ2,�˴�ǿ�Ƶ���pre,�������$job_name
my $pre_status = system("perl /incam/server/site_data/hooks/line_hooks/export_job.pre $job_name");
print "\$pre_status : $pre_status\n";
# ���systemִ�н��Ϊ���㣬��ʾpre hooks��⵽�쳣��Ҫ�˳�
exit 0 if ($pre_status != 0);
#$f->COM("export_job,job=$job_name,path=$do_tgz_path,mode=tar_gzip,submode=full,overwrite=yes");
system("python /incam/server/site_data/scripts/zl/test/Export_Job.py $job_name $do_tgz_path");
# 20241113 zl ���tgz
system("python /incam/server/site_data/scripts/sh_script/zltest/output/export_idb.py $job_name $username");

# 2019.12.5������޸ģ��������hash������
my $ref_param_hash = {
	# export_job.postֻ�õ����¼���������������Ҫ������������
	job         => $job_name,
	path        => $do_tgz_path,
	mode        => 'tar_gzip',
	submode     => 'full',
	output_name => $job_name,
};
# ������ͬ�ű�֮�䲻��ֱ�Ӵ�hash���ã�ֻ��ͨ���ַ�����ʽ��ת
my $param_hash_string = Dumper($ref_param_hash);
# 2019.12.5������޸ģ�gen_line_skip_post_hooks�Ѿ�����Ϊ2,�˴�ǿ�Ƶ���pre,�������$param_hash_string
system 'perl', '/incam/server/site_data/hooks/line_hooks/export_job.post', "$param_hash_string";

#copy("$path_tmp_job/$job_name.tgz","$do_tgz_path");
#system("rm -rf /tmp/$job_name.tgz");

&run_message_over;

exit 0;





####################################################################################################################################
#################################################�����ķָ���#######################################################################
####################################################################################################################################
sub check_job_save {
	# check if saved
    $f->INFO(entity_type => 'job',
             entity_path => $job_name,
             data_type => 'IS_CHANGED');
    if ( $f->{doinfo}{gIS_CHANGED} eq "yes" ) 
    {
		$GEN->Messages('info', "�Ϻ� $job_name δ���棬���ȱ���!");
		exit 0;
    }
}

# --202�ͻ����ַ�����copyǰ�汾�����¿ͻ��汾��δ�ĵ���ͬһ�ͻ��ѷ����ڶ��Σ�������ַ�ʱ����edit
sub cusNum202_check
{
    my $cusNum = shift;
    my $returnVal = $GEN->Messages('info', "$cusNum �ͻ������������������汾�����ַ���汾δ�޸ĵ�λ,������ȷ�ϣ�����ȷ�Ϻ��Զ���edit�ַ��㣡");
    # --�ж�edit step�Ƿ����
    if ($GEN->STEP_EXISTS($job_name, 'edit') eq 'no')
    {
        $GEN->Messages('warning', "��⵽��edit step�����ֶ�Ѱ��edit�����ַ�����бȶԣ�");
        $GEN->PAUSE('Pause...');            
    }
    # --��edit step  �����򿪲�
    $GEN->OPEN_STEP($job_name, 'edit');
    $GEN->CLEAR_LAYER;
    if ($GEN->LAYER_EXISTS($job_name, 'edit', 'c1') eq 'yes') {
        $GEN->WORK_LAYER('c1');
    }
    if ($GEN->LAYER_EXISTS($job_name, 'edit', 'c1+1') eq 'yes') {
        $GEN->WORK_LAYER('c1+1', 2);
    }
    
    # --��ͣ
    $GEN->PAUSE('Pause...');
    $GEN->CLEAR_LAYER;
    
    # --��ԭ���step
    # $GEN->OPEN_STEP($job_name, $sel_step);
}
	
sub run_message_over {
	my $mw3_3 = MainWindow->new( -title =>"VGT");
	$mw3_3->protocol("WM_DELETE_WINDOW", \&OnQuit);
	$mw3_3->geometry("500x145-800+100");
	$mw3_3->raise( );
	$mw3_3->resizable(0,0);
	
	my $sh_log = $mw3_3->Photo('info',-file => "$images_path/sh_log.xpm");
	my $CAM_frm = $mw3_3->Frame(-bg => '#9BDBDB',-borderwidth =>2,-relief => "raised",-height => 20)->pack(-side=>'top',-fill=>'x');
	my $image_label = $CAM_frm->Label(-image => $sh_log, -border => 1, -relief => 'solid',
                                              )->pack(-side => 'left',
                                                      -padx => 2,
                                                      -pady => 2);  
	$CAM_frm->Label(-text => '���TGZ  ',-font => 'charter 18 bold',-bg => '#9BDBDB')->pack(-pady => 2);
	$CAM_frm->Label(-text => '�汾:ʤ��Ƽ�  Ver:5.0',-font => 'charter 10',-bg => '#9BDBDB')->pack(-side=>'right', -padx => 10, -pady => 2);
	my $lab_frm = $mw3_3->Frame(-bg => '#9BDBDB',-borderwidth =>2,-height => 40)->pack(-side=>'top',-fill=>'x');
	$lab_frm->Label(-text => '�������н���,��ȷ��!',-font => 'charter 14',-bg => '#9BDBDB',-fg=>'red')->pack(-side=>'top', -padx => 5, -pady => 5);
	my $Bot_frm = $mw3_3->Frame(-bg => '#9BDBDB',-borderwidth =>2,-height => 40)->pack(-side=>'bottom',-fill=>'x');
	my $array_button = $Bot_frm->Button(-text => '�˳�',
                                         -command => sub {exit 0;},
                                         -width => 10,
										  -activebackground=>'#9BDBDB',
										  -font=> 'charter 12',
										  -height=> 2
                                          )->pack(-side => 'right',
                                                  -padx => 20);	
	MainLoop;
}

sub run_message_not_right {
	my $mw3_3 = MainWindow->new( -title =>"VGT");
	$mw3_3->protocol("WM_DELETE_WINDOW", \&OnQuit);
	$mw3_3->geometry("500x145-800+100");
	$mw3_3->raise( );
	$mw3_3->resizable(0,0);
	
	my $sh_log = $mw3_3->Photo('info',-file => "$images_path/sh_log.xpm");
	my $CAM_frm = $mw3_3->Frame(-bg => '#9BDBDB',-borderwidth =>2,-relief => "raised",-height => 20)->pack(-side=>'top',-fill=>'x');
	my $image_label = $CAM_frm->Label(-image => $sh_log, -border => 1, -relief => 'solid',
                                              )->pack(-side => 'left',
                                                      -padx => 2,
                                                      -pady => 2);  
	$CAM_frm->Label(-text => '���TGZ  ',-font => 'charter 18 bold',-bg => '#9BDBDB')->pack(-pady => 2);
	$CAM_frm->Label(-text => '�汾:ʤ��Ƽ�  Ver:5.0',-font => 'charter 10',-bg => '#9BDBDB')->pack(-side=>'right', -padx => 10, -pady => 2);
	my $lab_frm = $mw3_3->Frame(-bg => '#9BDBDB',-borderwidth =>2,-height => 40)->pack(-side=>'top',-fill=>'x');
	$lab_frm->Label(-text => '���಻�ǰ��涨����!',-font => 'charter 14',-bg => '#9BDBDB',-fg=>'red')->pack(-side=>'top', -padx => 5, -pady => 5);
	my $Bot_frm = $mw3_3->Frame(-bg => '#9BDBDB',-borderwidth =>2,-height => 40)->pack(-side=>'bottom',-fill=>'x');
	my $array_button = $Bot_frm->Button(-text => '�˳�',
                                         -command => sub {exit 0},
                                         -width => 10,
										  -activebackground=>'#9BDBDB',
										  -font=> 'charter 12',
										  -height=> 2
                                          )->pack(-side => 'right',
                                                  -padx => 20);	
	MainLoop;
}

sub OnQuit {
    my $mw3_3 = MainWindow->new( -title =>"VGT");
	my $ans = $mw3_3->messageBox(-icon => 'question',-message => '��ȷ��Ҫ�˳���',-title => 'quit',-type => 'YesNo');
	return if $ans eq "No";
	exit;
}
################################################################################################################################################################################


__END__
2019.07.17�����������£�
���ߣ�����
�汾��5.0
1.202�ͻ����ַ�����copyǰ�汾�����¿ͻ��汾��δ�ĵ���ͬһ�ͻ��ѷ����ڶ��Σ�������ַ�ʱ����edit step ����ȷ��(����Ҫ��Ӧ���ͻ�����)

# 2019.12.5������޸ģ��ű����й����в�����hooks 
gen_line_skip_pre_hooks�Ѿ�����Ϊ2,�˴�ǿ�Ƶ���pre,�������$job_name

###���940ϵ���Ƿ�����drill_map ������� by ������ 2022/03/24
http://192.168.2.120:82/zentao/story-view-3951.html

����������������
http://192.168.2.120:82/zentao/story-view-4332.html

2022.08.22
Song
1.�������tgz������Ring��� http://192.168.2.120:82/zentao/story-view-4478.html

20221110 by lyh
#1�� ���TGZ����������Ŀ�����osp+������Ϻţ�ץȡ�����������TGZ���ѣ���ע�⡮���Ϳ顯�谴�ջ����������������ϡ�
#2����Զƽ��Ҳ�������ѣ����TGZ���ѣ���ע�⡮���Ϳ顯�谴�ջ����������������ϡ�20221110

20221116 by lyh
#���TGZ���ӿ��أ�1�����NPTH���Ƿ�����ͭƤ����8mil��(�������TGZ����⣩��û����ͭƤ�����޸ġ�
# 2�����NPTH���Ƿ���ڷ������������㡣��������TGZ��⣩��δ���ڿ��������������޸ġ�
# 3�����NPTH�׶�Ӧ��sgt-c,sgt-s���Ƿ���ڿ�������������TGZ��⣩��δ���ڿ��������޸ġ� 
# 5�����TGZ���Ӽ���ά������������ݲ��ʶ�𣩡�
#system("python /incam/server/site_data/scripts/lyh/sh_hdi_check_rules.py check_barcode_condition");�ϲ���check_npth_hole_condition���м��
#http://192.168.2.120:82/zentao/story-view-4696.html 20221116 by lyh

20221215 by lyh
#���˫�濪�����Ƿ��������� ��ʾ
http://192.168.2.120:82/zentao/story-view-4976.html

20221227 by lyh
1����������֬��Ƭ��������b2-7.lp;2-7Ϊ����)&��֬����(b2-7...dq��2-7Ϊ����)����߹��߿��Ƿ�����ײ�Ĺ��߿���ͬһλ��
a,��ͬһλ�÷��С�
b,����ͬһλ�������Ҳ��������
2����������֬��Ƭ&ͨ����֬��Ƭ����Ƿ�����ؿס�
a,���ؿ׷���
b,���ؿ������Ҳ������
3�����ͨ����֬��Ƭ��������sz.lp/szsk-c.lp/szsk-s.lp/szsk2-1.lp/szsk2-2.lp/sz-c.lp/sz-s.lp )&��֬����(������ǰ׺����Ƭһ�£���׺...dq)����߹��߿��Ƿ���ͨ�ײ�Ĺ��߿���ͬһλ��
a,��ͬһλ�÷��С�
b,����ͬһλ�������Ҳ��������
#http://192.168.2.120:82/zentao/story-view-5006.html ����Ŀ�ĵ����tgzʱ��� 

20230105 by lyh
#http://192.168.2.120:82/zentao/story-view-5022.html
#3.���TGZʱ���LED���п�����ʱ����Ƿ�Ҫ�����ͭPad 

20230105 by lyh
#http://192.168.2.120:82/zentao/story-view-5034.html
# ���tgzʱ��ʾcam������ �п���ϳ����Ҫ��ͭ

# 20241113 zl ���tgz