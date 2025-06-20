 #!/Perl/bin/perl -w
=header

镭射输出脚本
writed by song 20180929
# 20191011更改临时，输出T23为0.102 设计仍为 0.52
=cut

use lib "$ENV{GENESIS_DIR}/sys/scripts/Package";

use Tk;
use Tk::LabFrame;
use Tk::BrowseEntry;
use Tk::Table;

use utf8;
use Encode;
use POSIX;
use Tk::JPEG;
use Tk::PNG;
use Genesis;
use mainVgt;
use VGT_Oracle;

use XML::Simple;
use Data::Dumper;
use File::Copy qw(move mv);

#use Cwd;
#my $cur_script_dir = getcwd();
#print "CWD PATH = ",$cwd,"\n";
my $skipvia = $ARGV[0];

use File::Spec;
print "\n";
my $path_curf = File::Spec->rel2abs(__FILE__);
print "C PATH = ",$path_curf,"\n";
my ($vol, $dirs, $file) = File::Spec->splitpath($path_curf);
$cur_script_dir = $dirs;
# 使用这种方式就能任何场景下得到正确的当前程序的绝对路径“$dir”。

binmode(STDIN, ':encoding(utf8)');
binmode(STDOUT, ':encoding(utf8)');
binmode(STDERR, ':encoding(utf8)');

my $script_Ver = '3.2.9';
#$host = shift;
#$f = new incam($host);
our $f = new Genesis();
our $c = new mainVgt();
BEGIN
    {
        # --实例化对象
        our $o = new VGT_Oracle();
        our $dbc_m = $o->CONNECT_MYSQL('host' => '192.168.2.19', 'dbname' => 'engineering', 'port' => '3306', 'user_name' => 'root', 'passwd' => 'k06931!');
        if (!$dbc_m) {
            $c->Messages('warning', '"工程数据库"连接失败-> 程序终止!');
            exit(0);
        }
    }

# --结束启动项
END
    {
        # --断开连接
        $dbc_m->disconnect if ($dbc_m);
    }
my $JOB = $ENV{JOB};
my $STEP = $ENV{STEP};
my $ipname = `hostname`;
my $incam_user = $ENV{INCAM_USER}; ###输出涨缩信息给ncr out_file取
my $logpath = $ENV{JOB_USER_DIR};
my $logfile = "$logpath/laser_output_log";
our $scriptPath = "$ENV{SCRIPTS_DIR}/sys/scripts";
our $tmpPath = "/tmp";
our %r515cor = {};
our %r515CheckData; # 需要添加r515的层别，lot号是否镜像
my $FlipSetExist = 'no';
my $FlipLayer;
$f->COM("get_user_name");
my $UserName = $f->{COMANS};
my @recordList;
if ($^O ne 'linux') {
    # TODO 待写入windows用户 日志路径
    $scriptPath = "d:/genesis/sys/scripts";
    $tmpPath = "c:/tmp";
}
#my $output_message = "/tmp/$JOB-rout-message";

unless ($JOB && $STEP) {
    $c->Messages("info", "必须打开料号及Step");
    exit(0);
}

# --参数初始化

my $images_path = "$scriptPath/xpms/";


# 获取料号中的Step列表
$f->INFO(angle_direction => 'ccw', entity_type => 'job',
    entity_path          => "$JOB",
    data_type            => 'STEPS_LIST');

my @steps = @{$f->{doinfo}{gSTEPS_LIST}};

for (my $i = 0; $i <= $#steps; $i++) {
    if ($steps[$i] eq "panel") {
        $step_name = "$steps[$i]";
        $panel_step = "$steps[$i]";
        last;
    }
}

if (!defined $panel_step) {
    $c->Messages("info", "必须存在panel Step");
    exit(0);
}
$f->INFO(angle_direction => 'ccw', entity_type => 'matrix',
    entity_path          => "$JOB/matrix",
    data_type            => 'ROW');

my @rlayers = ();
my @all_signal_array = ();
my @gROWname = @{$f->{doinfo}{gROWname}};
my @gROWlayer_type = @{$f->{doinfo}{gROWlayer_type}};
my @gROWcontext = @{$f->{doinfo}{gROWcontext}};

#for (my $i = 0; $i <= $#gROWname; $i++) {
#    if (($gROWlayer_type[$i] eq 'drill') && ($gROWcontext[$i] eq 'board') && $gROWname[$i] =~ /^s[0-9][0-9]?-?[0-9][0-9]?/) {
#        push(@rlayers, $gROWname[$i]);
#    }
#
#    #get the signal layer.
#    if ($gROWcontext[$i] eq "board" && $gROWlayer_type[$i] =~ /(signal|power_ground)/) {
#        push(@all_signal_array, $gROWname[$i]);
#    }
#}

our $job_signal_nubers = substr($JOB,4,2) * 1;
# 获取ERP中的钻带排刀
our %erp_drill_data = &getErpDrillData;
# 获取inplan中的铜厚信息
our %layer_copper_thick = &getInplanThick;
if( not $job_signal_nubers){
	my $job_signals = $c->GET_ATTR_LAYER($JOB,'signal');
	#print @{$job_signals} . "\n";
	#print 'xxxxxxxxxxxxxxxxxxxx' . "\n";
	$job_signal_nubers = scalar @$job_signals;
	$c->Messages("info", "层数无法从料号名获取,使用层别数量获取为$job_signal_nubers,\n程序继续！");
}	
our $halfjob_numb = $job_signal_nubers / 2;
print  '$halfjob_numb' . "$halfjob_numb" . "\n";

my @Merged_layer_top = ();
my @Merged_layer_bot = ();
my %merge_status;

my %laser_resize_dict;
for (my $i = 0; $i <= $#gROWname; $i++) {
    if (($gROWlayer_type[$i] eq 'drill') && ($gROWcontext[$i] eq 'board') && $gROWname[$i] =~ /^s(\d+)-(\d+)$/) {
        my $fisrt = $1;
        my $end = $2;
		$laser_resize_dict{$gROWname[$i]} = abs($2 - $1) - 1;

		if ($merge_status{$gROWname[$i]} eq "yes"){
			next;
		}
        
        # if (abs($1 - $2) == 2) {
            # my $same_layer;
            # if ($1 < $2) {
                # my $end_ = $2 - 1;
                # $same_layer = 's'.$1.'-'.$end_;
            # }else{
                # my $end_ = $2 + 1;
                # $same_layer = 's'.$1.'-'.$end_;
            # }
            
            # $f->INFO(units => 'mm', entity_type => 'layer',
                # entity_path => "$JOB/$panel_step/$same_layer",
                # data_type => 'EXISTS');

            # if ($f->{doninfo}{gEXISTS} eq 'yes') {
                # next;
            # }
        # }elsif(abs($1 - $2) > 1){
            # push(@rlayers, $gROWname[$i]);
            # next;
        # }
        
        my $status = 'yes';
		my @merged_layer_t_index = ();
		my @merged_layer_b_index = ();
		my @top_merged_layer_list=();
		my @bot_merged_layer_list=();
        for(my $h=0; $h<=$#gROWname; $h++){
            if ($gROWcontext[$h] eq 'board' and $gROWname[$h] =~ /^s(\d+)-(\d+)$/ and $gROWname[$i] ne $gROWname[$h]) {
				$laser_resize_dict{$gROWname[$h]} = abs($2 - $1) - 1;
                if ($fisrt == $1 ) {
                    if ($fisrt < $halfjob_numb) {
						
                        if ($end < $2) {
                            #$merged_layer_t = ($merged_layer_t eq "") ? 's'.$fisrt.'-'.$end.'-'.$2: $merged_layer_t.'-'.$2;
							if (scalar(@merged_layer_t_index) > 0){
								push(@merged_layer_t_index,$2);								
							}else{
								push(@merged_layer_t_index,$fisrt);
								push(@merged_layer_t_index,$end);
								push(@merged_layer_t_index,$2);
							}
							
                            #print ("\$merged_layer $gROWname[$i] $gROWname[$h] top $merged_layer\n");
                            #push(@Merged_layer_top, $merged_layer_t);
                            #print("$gROWname[$i] $gROWname[$h]\n");
                            # --生成合并层
                            #&merge_layer($merged_layer,$gROWname[$i],$gROWname[$h]);
							push(@top_merged_layer_list, $gROWname[$h]);
							push(@top_merged_layer_list, $gROWname[$i]);
                        }
                        $status = 'no';
                    }else{
                        if ($end < $2) {
                            #$merged_layer_b = ($merged_layer_b eq "") ? 's'.$fisrt.'-'.$2.'-'.$end: $merged_layer_b.'-'.$end;
							if (scalar(@merged_layer_b_index) > 0){
								push(@merged_layer_b_index,$2);								
							}else{
								push(@merged_layer_b_index,$fisrt);
								push(@merged_layer_b_index,$end);
								push(@merged_layer_b_index,$2);
							}
                            #push(@Merged_layer_bot, $merged_layer_b);
                            #print("$gROWname[$i] $gROWname[$h]\n");
                            # --生成合并层
                            #&merge_layer($merged_layer,$gROWname[$h],$gROWname[$i]);
							push(@bot_merged_layer_list, $gROWname[$h]);
							push(@bot_merged_layer_list, $gROWname[$i]);
                        }
                         $status = 'no';
                    }
                    #last;
                }
            }
        }
		# print @merged_layer_t_index;
		# print @merged_layer_b_index;
		#print '%laser_resize_dict' . "\n";
		#print Dumper(\%laser_resize_dict);
		my $merged_layer_t="";
		if (scalar(@merged_layer_t_index) > 0){
			my @new_merged_layer_t_index = sort { $a <=> $b } @merged_layer_t_index;
			$merged_layer_t = "s".join("-",@new_merged_layer_t_index);
			#print "------------> $merged_layer_t";
			&delete_layer($merged_layer_t);
			push(@Merged_layer_top, $merged_layer_t);
		}
		my $merged_layer_b="";
		if (scalar(@merged_layer_b_index) > 0){
			my @new_merged_layer_b_index = sort { $b <=> $a } @merged_layer_b_index;
			$merged_layer_b = "s".join("-",@new_merged_layer_b_index);
			&delete_layer($merged_layer_b);
			push(@Merged_layer_bot, $merged_layer_b);
		}
		
		my $copy_pnl = "yes";
		
		my $top_max_size = 0;
		foreach my $m_layer(@top_merged_layer_list){			
			if ($top_max_size <= $laser_resize_dict{$m_layer}){
				$top_max_size = $laser_resize_dict{$m_layer};
			}
		}
		my $end_top_layer="";
		foreach my $m_layer(@top_merged_layer_list){			
			if ($top_max_size == $laser_resize_dict{$m_layer}){
				$end_top_layer = $m_layer;
			}
		}
		if ($merged_layer_t ne ""){
			my $join_merge_layer = join(" ",@top_merged_layer_list);
			system("python $cur_script_dir/merge_laser_layer.py $merged_layer_t $join_merge_layer");
			foreach my $m_layer(@top_merged_layer_list){	
				$merge_status{$m_layer}="yes";			
			}
		}
		
		# foreach my $m_layer(@top_merged_layer_list){			
			# if ( $merge_status{$m_layer} ne "yes"){
				# &merge_layer($merged_layer_t,$m_layer,$end_top_layer,$copy_pnl,$laser_resize_dict{$m_layer});
			# }
			# $merge_status{$m_layer}="yes";
			# $copy_pnl = "no";
		# }

		$copy_pnl = "yes";
		
		my $bot_max_size = 0;
		foreach my $m_layer(@bot_merged_layer_list){			
			if ($bot_max_size <= $laser_resize_dict{$m_layer}){
				$bot_max_size = $laser_resize_dict{$m_layer};
			}
		}
		
		my $end_bot_layer="";
		foreach my $m_layer(@bot_merged_layer_list){			
			if ($bot_max_size == $laser_resize_dict{$m_layer}){
				$end_bot_layer = $m_layer;
			}
		}
		if ($merged_layer_b ne ""){
			my $join_merge_layer = join(" ",@bot_merged_layer_list);
			system("python $cur_script_dir/merge_laser_layer.py $merged_layer_b $join_merge_layer");
			foreach my $m_layer(@bot_merged_layer_list){	
				$merge_status{$m_layer}="yes";			
			}
		}
		
		# foreach my $m_layer(@bot_merged_layer_list){
			# if ( $merge_status{$m_layer} ne "yes"){
				# &merge_layer($merged_layer_b,$m_layer,$end_bot_layer,$copy_pnl,$laser_resize_dict{$m_layer});
			# }
			# $merge_status{$m_layer}="yes";
			# $copy_pnl = "no";
		# }
		
        if ($status eq 'yes') {
			if ( $merge_status{$gROWname[$i]} ne "yes"){
				push(@rlayers, $gROWname[$i]);
			}
        }
    }elsif($gROWcontext[$i] eq "board" && $gROWlayer_type[$i] =~ /(signal|power_ground)/) {
        push(@all_signal_array, $gROWname[$i]);
    }
}

# print Dumper(\%merge_status);
# print "333333333333";
# exit 0;



@rlayers = (@rlayers,@Merged_layer_top,@Merged_layer_bot);
foreach my $l(@rlayers){
    print ("$l\n");
}

#our $job_signal_nubers = scalar(@all_signal_array);
#our $halfjob_numb = $job_signal_nubers / 2;
our %sym_num_hash;
our $special_laser_mode;
my @three_T;

#设置是否跳钻输出 20221208 by lyh
my %layer_cool_speed_info;
#设置镭射是否打5遍 20221208 by lyh
my %laser_drill_five_times_info;
#定义镭射不同刀的数量
my %laser_symbol_size_num;
#定义手动选镭射跳钻信息
my %layer_manual_cool_speed_info;

my %layer_laser_info;
#定义传入的打5次钻孔参数
my %five_times_send_drill;
# 检测8mil孔是否符合工艺规范
my %layer_8mil_info;

#hash  是否选择 层别 拉伸x 拉伸y 是否镜像 孔径+/-0.1mil取mil整数 pp类型 pp张数 介质厚度 参数
for (my $i = 0; $i <= $#rlayers; $i++) {
    $f->INFO(
        angle_direction => 'ccw',
        entity_type     => 'layer',
        entity_path     => "$JOB/$panel_step/$rlayers[$i]",
        data_type       => 'SYMS_HIST',
        options         => "break_sr"
    );

    # 取panel中的镭射孔，排除板边辅助孔，机台孔0.501，set lot号0.515，五代靶烧靶0.520 ，定位孔3.175#
    # 增加0.045mm在镭射层的防呆
    my @symbol_list = ();
    my @pnlspecial = ('r125', 'r19.724', 'r20.276', 'r20.472');
    my ($r3175num,$r515num);
    my $r45num = 0;
    my $m = 0;
	my $lot_design = 'no';
	my @cool_speed_size;
	my @has_80_90mil_size;
	my @has_95_105mil_size;
	my $has_8mil_size_num=0;
	my $has_9mil_size_num=0;
	my $has_10mil_size_num=0;
	my $five_times_8mil_size_diff=0;
	my $five_times_9mil_size_diff=0;
	my $five_times_10mil_size_diff=0;
	my @array_t5 = qw(T05 T06 T07 T08 T09);
	my @array_t15 = qw(T15 T16 T17 T18 T19);
	
	my $five_8mil = 'no';
	my $exist_8mil = 'no';
	
    foreach (@{$f->{doinfo}{gSYMS_HISTsymbol}}) {
        if ($_ eq $pnlspecial[0] || $_ eq $pnlspecial[1] || $_ eq $pnlspecial[2] || $_ eq $pnlspecial[3] || $_ eq $pnlspecial[4]) {
            # 获取r125的数量
            if ($_ eq $pnlspecial[0]) {
                $r3175num = ${$f->{doinfo}{gSYMS_HISTpad}}[$m];
            }
			if ($_ eq $pnlspecial[2]) {
                $r515num = ${$f->{doinfo}{gSYMS_HISTpad}}[$m];
            }
        }
        else {
            #r0.045 的数量
            if ($_ eq 'r1.772') {
                $r45num = ${$f->{doinfo}{gSYMS_HISTpad}}[$m];
            }
			my $symbol_size = $_;
			$symbol_size =~ s/r//g;
			my $drillSize = $symbol_size * 25.4;
            $drillSize = sprintf "%.f",$drillSize;
			# 如果有大于16mil的镭射孔直接报错退出程序
			if (457 <= $drillSize and $drillSize != 515 and $drillSize != 520){
				$c->Messages("info", "$rlayers[$i] 层中存在大于等于18mil的镭射孔，大小: $drillSize 请检查！");
				#exit();
			}			
			
			if ( ($drillSize - 203 <=5.01 and $drillSize - 202 > 0) || ($drillSize - 254 <=5.01 and $drillSize - 253 > 0) || ($drillSize - 233 <=5.01 and $drillSize - 228 > 0) || ($drillSize - 245 <=5.01 and $drillSize - 240 > 0) || ($drillSize - 220 <=5.01 and $drillSize - 215 > 0)){		
				# if ( substr($JOB,1,3) eq 'a86' || substr($JOB,1,3) eq 'd10' )
				# {		
					# $laser_drill_five_times_info{"$rlayers[$i]"} = "yes";	
					# push(@cool_speed_size,$drillSize);				
					#判断是否打5遍
					my @rlayer_split =  split /-/, substr($rlayers[$i],1);			
					while (my ($key, $inner_dict) = each %erp_drill_data) {
						next if ($key !~ /s\d.*/);							
						my @hole_t5;
						my @hole_t15;							
						my @key_split = split /-/, substr($key,1);
						my $lay_in;						
						foreach my $key_s (@key_split) {
							if (!grep { $_ eq $key_s } @rlayer_split){$lay_in = 'no'}
						}						
						if($lay_in ne 'no'){							
							while (my ($t_key, $value_dict) = each %$inner_dict) {								
								while (my ($l_key, $value) = each %$value_dict) {	
									if(grep { $_ eq $t_key } @array_t5){
										if ($l_key eq 'DrillSize' && $drillSize/1000 == $value)
										{
											push(@hole_t5,$value);
										}
									}
									if(grep { $_ eq $t_key } @array_t15){
										if ($l_key eq 'DrillSize' && $drillSize/1000 == $value)
										{
											push(@hole_t15,$value);
										}
									}									
								}								
							}
						}						
						my @see_t5 = grep_arrey(@hole_t5);	
						my @see_t15 = grep_arrey(@hole_t15);
						
						if ($drillSize <= 229 and $drillSize >= 203){
							$exist_8mil = "yes";
							if ((scalar(@hole_t5) == 5  && scalar(@see_t5) == 1)){
								$five_8mil = "yes";	
							}
						}
												
						if ((scalar(@hole_t5) == 5  && scalar(@see_t5) == 1) || (scalar(@hole_t15) == 5  && scalar(@see_t15) == 1) ){							
							$laser_drill_five_times_info{"$rlayers[$i]"} = "yes";					
							push(@cool_speed_size,$drillSize);							
						}
						
					}				
					
				# }
			}
			
			if ($drillSize <= 229 and $drillSize >= 203){
				push(@has_80_90mil_size,$drillSize);		
				
			}
			if ($drillSize <= 267 and $drillSize >= 241){
				push(@has_95_105mil_size,$drillSize);		 
				
			}
			
			if ($drillSize - 254 <=5.01 and $drillSize - 253 > 0){
				$has_10mil_size_num=$has_10mil_size_num+1;
				$five_times_10mil_size_diff=$drillSize-254;
			}
			
			if ($drillSize - 233 <=5.01 and $drillSize - 228 > 0){
				$has_9mil_size_num=$has_9mil_size_num+1;
				$five_times_9mil_size_diff=$drillSize-233;
			}

			if ($drillSize - 203 <=5.01 and $drillSize - 202 > 0){
				$has_8mil_size_num=$has_8mil_size_num+1;
				$five_times_8mil_size_diff=$drillSize-203;
			}
			
            push(@symbol_list, $_);
        }
        $m++;
    };
	
	if (scalar(@has_80_90mil_size) > 1){
		$c->Messages("info", "$rlayers[$i] 工艺准则要求层别8-9mil需要全部按8mil设计,现存在多种孔径，请检查后输出");
			exit;
	}
	if (scalar(@has_95_105mil_size) > 1){
		$c->Messages("info", "$rlayers[$i] 工艺准则要求层别9.5-10.5mil需要全部按10mil设计,现存在多种孔径，请检查后输出");
			exit;
	}
	
	$layer_8mil_info{$rlayers[$i]}{'mgs'} = "None";
	
	if ($exist_8mil eq 'yes') {
		# 获取承接层铜厚
		my @layer_split =  split /-/, $rlayers[$i];		
		my $layer_split_end = "l"."$layer_split[-1]";
		my $layer_split_end_cuthick = $layer_copper_thick{$layer_split_end};
		if ($layer_split_end_cuthick <1.18 && $five_8mil ne 'yes'){
			$layer_8mil_info{$rlayers[$i]}{'mgs'} = "mgs1";
			# $c->Messages("info", "$rlayers[$i] 8-9mil孔承接层铜厚小于1OZ，但是MI未按工艺规范打5遍，请和MI确认！");
			
		}elsif($layer_split_end_cuthick >= 1.18 && $five_8mil eq 'yes'){
			$layer_8mil_info{$rlayers[$i]}{'mgs'} = "mgs2";
			# $c->Messages("info", "$rlayers[$i] 8-9mil孔承接层铜厚大于1OZ，工艺规范需要绕烧，MI为打5遍,请和MI确认！");
		}
	}
	
	$layer_cool_speed_info{$rlayers[$i]} = \@cool_speed_size;
	$layer_manual_cool_speed_info{$rlayers[$i]} = \@symbol_list;
	$five_times_send_drill{$rlayers[$i]} = join '_', @cool_speed_size;
	
	if ($r515num) {
		$lot_design = 'yes';
		$r515CheckData{"$rlayers[$i]"}{'lot_design'} = 'yes';
	}
    if ($r3175num ne '4') {
        $c->Messages("info", "$rlayers[$i] 3.175mmm 钻孔数量不是4个，不能正确生成G82及G83指令");
    }
    if ($r45num ne '0') {
        $c->Messages("info", "$rlayers[$i] 层别存在dld层钻孔,\n请手动删除处理0.045mm钻孔");
        exit;
    }

	
	if ( $laser_drill_five_times_info{$rlayers[$i]} eq "yes" ){
		
		# V3.2.9 1.8mil或者10mil的孔在一条钻带中需设计单一T;http://192.168.2.120:82/zentao/story-view-5220.html
		if ($has_10mil_size_num > 1 ) {
			$c->Messages("info", "$rlayers[$i] 层别10mil 孔径存在数量为$has_10mil_size_num,\n应仅设计数量为1");
			exit;
		}
		if ($has_9mil_size_num > 1) {
			$c->Messages("info", "$rlayers[$i] 层别9mil 孔径存在数量为$has_9mil_size_num,\n应仅设计数量为1");
			exit;
		}
		if ($has_8mil_size_num > 1) {
			$c->Messages("info", "$rlayers[$i] 层别8mil 孔径存在数量为$has_8mil_size_num,\n应仅设计数量为1");
			exit;
		}
		
		if ($has_9mil_size_num > 0 and $has_8mil_size_num > 0) {
			$c->Messages("info", "$rlayers[$i] 层别同时存在8mil 9mil 孔径，打五遍刀序一致不能输出，请提评审！");
			exit;
		}
	
		if ($five_times_8mil_size_diff > 1 or $five_times_10mil_size_diff > 1 or $five_times_9mil_size_diff > 1) {
			$c->Messages("info", "a86/d10系列$rlayers[$i] 层别有8-10mil的钻孔，但是孔径不是0.203或0.254或0.229设计, 程序无法执行打五遍，请检查！");
			exit;
		}
	}
	
    my ($symb, $lsr_stlr);
    my $sym_num = scalar(@symbol_list);	
	
	$laser_symbol_size_num{"$rlayers[$i]"}= scalar(@symbol_list);
	if ($has_10mil_size_num > 0){
		$laser_symbol_size_num{"$rlayers[$i]"}= $laser_symbol_size_num{"$rlayers[$i]"}-$has_10mil_size_num+1;
	}
	if ($has_8mil_size_num > 0){
		$laser_symbol_size_num{"$rlayers[$i]"}= $laser_symbol_size_num{"$rlayers[$i]"}-$has_8mil_size_num+1;
	}
	
    print ("\t\$#rlayers $rlayers[$i]\t\$sym_num $sym_num\n");
    $sym_num_hash{"$rlayers[$i]"} = $sym_num;
    $layer_laser_info{$rlayers[$i]} = $sym_num;
    if ($sym_num == 0) {
        # --系统自动排查检测机台孔:0.501 lot号孔:0.515 五代靶孔:0.520 定位孔:3.175之外孔是否存在,不存在将提示用户镭射孔为空  AresHe 2021.11.1
        # --放到界面点击输出按钮后提示 AresHe 2021.11.8
        #$c->Messages("info", "系统自动检测到[$rlayers[$i]]镭射层除以下孔之外为空,检查不到镭射孔,请检查.\n机台孔:\t0.501\nlot号孔:\t0.515\n五代靶孔:\t0.520\n定位孔:\t3.175\n");
        #exit;
    }
    elsif ($sym_num == 1) {
        $symb1 = $symbol_list[0];
        $symb1 =~ s/r//g;
        @symb1 = ret_int($symb1);
        $symb = "$symb1[0]mil";
    }
    elsif ($sym_num == 2) {
        my $symb1 = $symbol_list[0];
        $symb1 =~ s/r//g;
        @symb1 = ret_int($symb1);
        my $symb2 = $symbol_list[1];
        $symb2 =~ s/r//g;
        @symb2 = ret_int($symb2);
        if ($symb1[0] < $symb2[0]) {
            $symb = "$symb1[0]mil" . "+" . "$symb2[0]mil";
        }
        else {
            $symb = "$symb2[0]mil" . "+" . "$symb1[0]mil";
        }
    }
    else {
        # 程序可支持，不影响只要不超过T20都可以，工艺仅定义了两把刀的做法及参数，此处防呆。
        # ----------备注 By Song 2019.12.28
        # $c->Messages("info","镭射层超出二把刀，现场暂不支持,\n程序退出！");
        # -- TODO 20200925周涌在story-view-2042中备注，超出两把刀的也要正反面输出
        # $c->Messages("info","$rlayers[$i] 镭射层超出二把刀，现场暂不支持,\n此程序放行！");
        push(@three_T, $rlayers[$i]);
        # exit(0);
    }
    #雷射层的开始层别大于1/2的层别，则镜像
    my $mir_choose;

    if ($rlayers[$i] =~ /s(\d+)-(\d+)-?(\d+)?.*$/) {
        if (($1 < $2 and $1 <= $halfjob_numb) || ($1 > $2 and $2 >= $halfjob_numb)) {
            if ($1 < $2 and $1 <= $halfjob_numb) {
                $mir_choose = "no";
                if ($1 == 1) {
                    $r515CheckData{"$rlayers[$i]"}{'mir'} = $mir_choose;
                }
            }
            elsif ($1 > $2 and $2 >= $halfjob_numb) {
                $mir_choose = "yes";
                if ($1 == $job_signal_nubers) {
                    $r515CheckData{"$rlayers[$i]"}{'mir'} = $mir_choose;
                }
                if ($1 > $job_signal_nubers) {
                    #code
                    $c->Messages("info", "$rlayers[$i] 镭射层钻带的起始层超出层别数量,\n请检查，程序退出！");
                    exit 0;
                }
            }
        }elsif($rlayers[$i] =~ /s(\d+)-(\d+)-(\d+)$/){
            # --新命名合并层
        }
        else {
            $c->Messages("info", "$rlayers[$i] 镭射层钻带的起始层定义不正确,\n程序退出！");
            exit 0;
        }
    }
    else {
        $c->Messages("info", "$rlayers[$i] 镭射层别非最新命名，\n应为s开始层-结束层，中间有横杠,\n程序退出！");
        exit 0;
    }
    #my @htitle =            ('选择','层名','X涨缩','Y涨缩','镜像','孔径','介质厚度','PP张数','PP类型','参数'); 对应关系如下
    if ($rlayers[$i] =~ /s(\d+)-(\d+)-(\d+)$/) {
        @{$hash{$rlayers[$i]}} = (1, $rlayers[$i], '1.0000', '1.0000', $mir_choose, $symb, 0, 0, 'None', 0, '0', 'disabled', $lot_design);
    }else{
        @{$hash{$rlayers[$i]}} = (1, $rlayers[$i], '1.0000', '1.0000', $mir_choose, $symb, 0, 0, 'Null', 0, '0', 'disabled', $lot_design);
    }
}

# print Dumper(\%laser_symbol_size_num);
# print Dumper(\%layer_manual_cool_speed_info);
# exit;
# -- TODO 20200925周涌在story-view-2042中备注，超出两把刀的芯板镭射不能报错能出，要放行，可输出
if (scalar(@three_T) > 0) {
    #$c->Messages("info", "@three_T 镭射层超出二把刀，现场暂不支持,\n此程序放行！");
    # --2021。12.16周涌要求,镭射层不允许超出两把刀,禁止输出!
	#周涌通知 取消提示 20221219 by lyh
    #$c->Messages("info", "@three_T 镭射层超出二把刀，现场暂不支持,\n禁止输出!");
    #exit;
}

# === 是否有set step 以及是否在其他step中有lot号设计  ===
# === 三种模式下，定义为special lot 1.lot加在pcs中；2.set中添加多个；3.有阴阳拼版存在；4，多个不同set拼入panel
#my $check_end = 'no';
our @lot_base_step = ();
our $job_lot_design = 'yes';
if (%r515CheckData) {
	&check_if_special_laser;
} else {
	$special_laser_mode = 'no';
}
# === V3.2.9 Song
# 判定是简单镭射设计还是特殊镭射设计，单独模块，方便返回值，
# 由于都是全局变量，为程序连贯性，暂时不后置===
sub check_if_special_laser{
	# === 1.有阴阳拼版存在 ===
	$f->INFO(units => 'mm', entity_type => 'step', entity_path => "$JOB/$panel_step", data_type => 'SR');
	for (my $i = 0; $i < @{$f->{doinfo}{gSRstep}}; $i++) {
		if (${$f->{doinfo}{'gSRflip'}}[$i] eq 'yes') {
			$FlipSetExist = 'yes';
			#$check_end = 'yes';
			$special_laser_mode = 'yes';
			return;
		}
	}

	# === step list	去重 ===
	my %ha;
	my @step_list=grep{++$ha{$_}<2} @{$f->{doinfo}{'gSRstep'}};
	foreach my $tmpLaser (keys %r515CheckData) {
		# === 先判断panel step中是否有lot，如果用按特殊设计输出 ===
		$f->INFO(
			angle_direction => 'ccw',
			entity_type     => 'layer',
			entity_path     => "$JOB/$panel_step/$tmpLaser",
			data_type       => 'SYMS_HIST'
		);
		my @pnl_symbol_list =  @{$f->{doinfo}{gSYMS_HISTsymbol}};
		my @pnl_pad_num =  @{$f->{doinfo}{gSYMS_HISTpad}};
		# === symbbol 及数量的键值对 ===
		my %pnl_symbol_hash;
		@pnl_symbol_hash{@pnl_symbol_list} = @pnl_pad_num;
		#exists $pnl_symbol_hash{'r20.276'}
		if (exists $pnl_symbol_hash{'r20.276'}) {
			$special_laser_mode = 'yes';
			return;
		}
		foreach my $current_step (@step_list) {
			$f->INFO(
			angle_direction => 'ccw',
			entity_type     => 'layer',
			entity_path     => "$JOB/$current_step/$tmpLaser",
			data_type       => 'SYMS_HIST',
			options         => "break_sr"
			);
			print $current_step . "\n";
			my @symbol_list =  @{$f->{doinfo}{gSYMS_HISTsymbol}};
			my @pad_num =  @{$f->{doinfo}{gSYMS_HISTpad}};
			# === symbbol 及数量的键值对 ===
			my %symbol_hash;
			@symbol_hash{@symbol_list} = @pad_num;
			print Dumper(\%symbol_hash);
			#'r20.276',
			if (exists $symbol_hash{'r20.276'}) {
				# === 先用空值占位 ===
				$r515CheckData{$tmpLaser}{'lotCode'} = '';
				
				push (@lot_base_step,$current_step);

				if ($current_step ne 'set') {
					$special_laser_mode = 'yes';
					$r515CheckData{$tmpLaser}{'laser_base_step'} = $current_step;
				} else {
					# === 打散后和打散前数量相同，则认为加在set工艺边，为常规设计 === 
					$f->INFO(
					angle_direction => 'ccw',
					entity_type     => 'layer',
					entity_path     => "$JOB/$current_step/$tmpLaser",
					data_type       => 'SYMS_HIST'
					);
					my @array_symbol_list =  @{$f->{doinfo}{gSYMS_HISTsymbol}};
					my @array_pad_num =  @{$f->{doinfo}{gSYMS_HISTpad}};
					my %array_symbol_hash;
					@array_symbol_hash{@array_symbol_list} = @array_pad_num;
					print Dumper(\%array_symbol_hash);
					if (exists $array_symbol_hash{'r20.276'}) {
						# set和打散后的set中的数量相同,且等于1
						if ( $array_symbol_hash{'r20.276'} == $symbol_hash{'r20.276'} && $array_symbol_hash{'r20.276'} == 1) {
							$r515CheckData{$tmpLaser}{'laser_base_step'} = $current_step;
							$special_laser_mode = 'no';
						} else {
							$special_laser_mode = 'yes';
						}
					} else {
						# set 不打散时无515的设计，则认为加在edit里，为特殊Lot设计
						$special_laser_mode = 'yes';
					}
				}
			}
		}
	}
	#if ($FlipSetExist eq 'yes') {
	#	#$check_end = 'yes';
	#	$special_laser_mode = 'yes';
	#}
	if (scalar (@lot_base_step) == 0) {
		$job_lot_design = 'no';
		$special_laser_mode = 'no';
	}
}

#### 测试 2019.12.25 by Song For Test
if ($special_laser_mode eq 'yes') {
	$c->Messages("info", "特殊镭射LOT设计料号,\n继续运行！");
	print Dumper(\%r515CheckData);
	if (defined %r515CheckData) {
		foreach my $tmpLaser (keys %r515CheckData) {
			my $op_side;
			if ($hash{$tmpLaser}[4] eq 'yes') {
				$op_side = 'bot';
			}
			elsif ($hash{$tmpLaser}[4] eq 'no') {
				$op_side = 'top';
				if ($FlipSetExist eq 'yes') {
					$FlipLayer = $tmpLaser;
				}
			}
			if ($hash{$tmpLaser}[12] eq 'yes') {
				my @getCor1;
				my $getLotinfo = &dealWithPanelLaserLayer($op_side,$tmpLaser);
				if ($getLotinfo eq 'Type_Error') {
					$c->Messages("info", "类型错误,\n继续运行！");
				}
				elsif ($getLotinfo eq 'laserNameError') {
					$c->Messages("info", "镭射命名错误,\n继续运行！");
				}
				else {
					@getCor1 = @$getLotinfo;
				}
				$r515CheckData{"$tmpLaser"}{'corlist'} = [ @getCor1 ];
				#$r515CheckData{"$tmpLaser"}{'toplaser'} = $tmpLaser;
			}
			#else {
			#	$c->Messages('info', "层别$tmpLaser 未设计LaserLot号,程序继续");
			#}
		}
	}
} else {
	if (%r515CheckData) {
		foreach my $tmpLaser (keys %r515CheckData) {
			my $r515exist = &checkr515exist($tmpLaser);
			my $LotDirec;
			if ($r515exist eq 'yes') {
				my $getLotDirect = &mainCheckLaserLot($tmpLaser);
				if ($getLotDirect eq 'mirrorExist') {
					$FlipSetExist = 'yes';
					$FlipLayer = $tmpLaser;
				}
				else {
					$r515CheckData{"$tmpLaser"}{'LotDirec'} = $getLotDirect;
				}
			}
			#else {
			#	$c->Messages('info', "层别$tmpLaser 未设计LaserLot号,程序继续");
			#}
		}
	}
	else {
		$c->Messages("info", "未检测到有外层镭射设计,\n继续运行！");
	}
}


print Dumper(\%r515CheckData);
my $inplan_add_lot_yn = &getInplan_Lot_Add();
my $job_add_lot_yn = 'no';
foreach my $tmpLaser (keys %r515CheckData) {
	if ( exists $r515CheckData{$tmpLaser}{'lot_design'}) {
		$job_add_lot_yn =  $r515CheckData{$tmpLaser}{'lot_design'};
		print  $job_add_lot_yn . "\n";
	}
}

if ($inplan_add_lot_yn ne $job_add_lot_yn) {
	if ($inplan_add_lot_yn ne "Unknown") {
		$c->Messages("warning", "是否设计Lot号比对不一致:\nInPlan中为:$inplan_add_lot_yn ,CAM资料设计为:$job_add_lot_yn,\n程序退出！");
		exit 0;
	} else {
		$c->Messages("info", "是否设计Lot号比对不一致:\nInPlan中为:$inplan_add_lot_yn ,CAM资料设计为:$job_add_lot_yn,\n程序暂不退出,请自行核实是否添加Lot！");
	}
}



### Test 2020.01.07 for flip d
if ($FlipSetExist eq 'yes') {
    #镜像拼板的
    my @getCor1;
    my $getMirrorinfo = &dealWithMirrorLaserLayer('top', $FlipLayer);
    if ($getMirrorinfo eq 'Type_Error') {
        $c->Messages("info", "类型错误,\n继续运行！");
    }
    elsif ($getMirrorinfo eq 'laserNameError') {
        $c->Messages("info", "镭射命名错误,\n继续运行！");
    }
    else {
        @getCor1 = @$getMirrorinfo;
    }
    $r515CheckData{"$FlipLayer"}{'corlist'} = [ @getCor1 ];
    $r515CheckData{"$FlipLayer"}{'toplaser'} = $FlipLayer;

    #&addTmpStep($FlipLayer,@getCor1);
    if ($FlipLayer =~ /s([1-9][0-9]?)-([0-9][0-9]?)$/) {
        my $botLaserLayer = "s" . ($job_signal_nubers - $1 + 1) . "-" . ($job_signal_nubers - $2 + 1);
        my @getCor2;
        my $getMirrorinfo = &dealWithMirrorLaserLayer('bot', $botLaserLayer);
        if ($getMirrorinfo eq 'Type_Error') {
            $c->Messages("info", "类型错误,\n继续运行！");
        }
        elsif ($getMirrorinfo eq 'laserNameError') {
            $c->Messages("info", "镭射命名错误,\n继续运行！");
        }
        else {
            @getCor2 = @$getMirrorinfo;
        }
        $r515CheckData{"$botLaserLayer"}{'corlist'} = [ @getCor2 ];
        $r515CheckData{"$botLaserLayer"}{'toplaser'} = $FlipLayer;
        #&addTmpStep($botLaserLayer,@getCor2);
    }
    #exit 0;
}


####

############   创建Tk用户交互界面，获取变量  #########
RESTART:
our $Vend_sel = "";
our $PP_sel = "";
my $tg_fill = "";
my $mw = MainWindow->new(
    -title      => "镭射输出",
    -background => '#9BDBDB');

my $icon = $mw->Photo(
    '-format' => 'xpm',
    -file     => "$images_path/sh_log.xpm"); #此处图片的路径可以是完整的路径
$mw->iconimage($icon);                       #设定窗口标题的ico图标
$mw->resizable(0, 0);
$top = $mw->Frame(-background => '#9BDBDB')->pack();
$fre1 = $mw->Frame(-background => '#9BDBDB')->pack();
$fre2 = $mw->LabFrame(
    -background => '#9BDBDB',
    -label      => "参数设置",
    -foreground => 'blue',
    -labelside  => 'acrosstop',
    -font       => [ -size => 11 ],
    -width      => 38)->pack();

#$fre3 = $mw -> LabFrame(-background => '#9BDBDB',
#					  -label => "材料参数",
#					  -foreground => 'blue',
#					  -labelside => 'acrosstop',
#					  -font => [-size =>11],
#					  -width => 38) ->pack();

$table_frame = $mw->Frame(-background => '#9BDBDB')->pack();
$bot = $mw->Frame(-background => '#9BDBDB')->pack();
my $image1 = $top->Photo(
    '-format' => 'xpm',
    -file     => "$images_path/sh_log.xpm");
my $pic1 = $top->Label(-image => $image1)->pack(-side => 'left');
my $lab1 = $top->Label(
    -background => '#9BDBDB',
    -text       => "镭射输出程序",
    -font       => [ -family => 'Times', -weight => 'bold', -size => 30 ],
    -width      => 56)
    ->pack(
    -side   => 'top',
    -fill   => 'both',
    -expand => 1);
my $lab2 = $top->Label(
    -background => '#9BDBDB',
    -font       => [ -size => 8 ],
    -width      => 15)
    ->pack(
    -side   => 'left',
    -fill   => 'both',
    -expand => 1);
my $lab3 = $top->Label(
    -background => '#9BDBDB', -text => "作者：Song  Ver:$script_Ver 	",
    -font       => [ -size => 10 ],
    -width      => 20)
    ->pack(-side => 'right');
my $lab4 = $fre1->Label(
    -background => '#9BDBDB', -text => ">>> 料号：$JOB <<<",
    -font       => [ -size => 23 ],
    -foreground => 'blue',
    -relief     => 'groove',
    -width      => 80)
    ->pack(
    -side   => 'top',
    -fill   => 'both',
    -expand => 1);
########参数设置框里面再划分框架
my $lfam1 = $fre2->Frame(-background => '#9BDBDB')->pack(-side => 'top', -anchor => 'w');
my $lfam11 = $fre2->Frame(-background => '#9BDBDB')->pack(-side => 'top', -anchor => 'w');
my $lfam2 = $fre2->Frame(-background => '#9BDBDB')->pack(-side => 'bottom', -anchor => 'w');
my $l1 = $lfam1->Label(
    -text       => "输出STEP:",
    -font       => [ -size => 11 ],
    -width      => 10,
    -background => '#9BDBDB')
    ->pack(-side => 'left', -fill => 'both');
my $l2 = $lfam1->Optionmenu(
    -font       => [ -size => 11 ],
    -width      => 17,
    -background => '#9BDBDB',
    -relief     => 'groove',
    -variable   => \$step_name,
    -options    => [ @steps ])
    ->pack(
    -side => 'left',
    -fill => 'both');
my $l3 = $lfam1->Label(
    -text       => "	 涨缩位置:",
    -font       => [ -size => 11 ],
    -background => '#9BDBDB')
    ->pack(
    -side => 'left',
    -fill => 'both');
my @scale = ('中心', '零点');
my $scale_position = $scale[0];
my $l4 = $lfam1->Optionmenu(
    -font       => [ -size => 11 ],
    -background => '#9BDBDB',
    -relief     => 'groove',
    -variable   => \$scale_position,
    -options    => [ @scale ])
    ->pack(
    -side   => 'left',
    -fill   => 'both',
    -expand => 1);

my $l6 = $lfam1->Label(
    -text       => "	输出路径:",
    -background => '#9BDBDB',
    -font       => [ -size => 11 ])
    ->pack(
    -side   => 'left',
    -fill   => 'both',
    -expand => 1);

my $output_path_des = "/id/workfile/film/$JOB/";
if (!-d "$output_path_des") {
    mkdir("$output_path_des");
}
else {
    # --TODO 直接删除非空文件会报错，此处先删除目录里面所有的文件
    # unlink glob "$output_path/* $output_path/.*";
    # --TODO 删除已经清空的目录,20200927李家兴添加
    # rmdir $output_path;
}
my $output_path =  "$tmpPath/"."laser_"."$JOB";
if (!-d "$output_path") {
    mkdir("$output_path");
} else {
	unlink glob "$output_path/* $output_path/.*";
}
#my $l7 = $lfam1->Entry(
#    -font         => [ -size => 11 ],
#    -background   => 'white',
#    -relief       => 'groove',
#    -width        => 37,
#    -textvariable => \$output_path)
#    ->pack(
#    -side   => 'left',
#    -fill   => 'both',
#    -expand => 1);
#my $image = $lfam1->Photo(
#    '-format' => 'png',
#    -file     => "$images_path/OpenJob.png");
#my $l8 = $lfam1->Button(
#    -activeforeground    => 'red',
#    -background          => '#9BDBDB',
#    -image               => $image,
#    -highlightbackground => 'black',
#    -command             => sub {dirDialog($lfam1)})
#    ->pack(
#    -side   => 'left',
#    -fill   => 'both',
#    -expand => 1);

my $l8 =$lfam1->Label(
    -text       => "$output_path_des",
    -background => '#9BDBDB',
    -font       => [ -size => 11 ])
    ->pack(
    -side   => 'left',
    -fill   => 'both',
    -expand => 1);
	
my $l9 = $lfam1->Label(
    -text       => "",
    -background => '#9BDBDB',
    -font       => [ -size => 11 ],
    -width      => 6)
    ->pack(
    -side   => 'left',
    -fill   => 'both',
    -expand => 1);
    
my $l20 = $lfam11->Label(
    -text       => "分割模式:",
    -width      => 10,
    -background => '#9BDBDB',
    -font       => [ -size => 11 ])
    ->pack(
    -side   => 'left',
    -fill   => 'both',
    -expand => 1);

my @mode_list = ("2分割","4分割","不分割");
my $clip_mode = "不分割";
my $l21 = $lfam11->Optionmenu(
    -font       => [ -size => 11 ],
    -width      => 17,
    -background => '#9BDBDB',
    -relief     => 'groove',
    -variable   => \$clip_mode,
    -options    => [ @mode_list ])
    ->pack(
    -side => 'left',
    -fill => 'both');
	
my $l22 = $lfam11->Label(
    -text       => "跳钻测试:",
    -width      => 10,
    -background => '#9BDBDB',
    -font       => [ -size => 11 ])
    ->pack(
    -side   => 'left',
    -fill   => 'both',
    -expand => 1);
my @select_yn_list = ("否","是");
my $skip_hole = "否";

my $l23 = $lfam11->Optionmenu(
    -font       => [ -size => 11 ],
    -width      => 17,
    -background => '#9BDBDB',
    -relief     => 'groove',
    -variable   => \$skip_hole,
    -options    => [ @select_yn_list ])
    ->pack(
    -side => 'left',
    -fill => 'both');
	
sub dirDialog {
    my $w = shift;
    #my $ent = shift;
    my $dir;
    my $dpath = $l7->get();
    $dir = $w->chooseDirectory(-initialdir => "$dpath");
    my $ddd = decode("utf8", $dir);
    if (defined $dir and $dir ne '') {
        $l7->delete(0, 'end');
        $l7->insert(0, $ddd);
        $l7->xview('end');
    }
}
###材料相关参数获取 开始####
my $config_file = "$scriptPath/hdi_scr/Output/Laser/laser_table.xml";
if (-e $config_file) {
    $simple = XML::Simple->new();
    our $config = $simple->XMLin($config_file);
}

my $i = 0;

my @Vend_list = ();
my @DS_list = ();
my @PP_list = ();
our @all_data = ();
while ($config->{'Laser_op'}->{'RECORD'}->[$i]) {
    my ($Materials_Vendor, $Materials_PPtype, $Drill_Size);
    $all_data[$i] = $config->{'Laser_op'}->{'RECORD'}->[$i];
=pod
    $Materials_Vendor = decode("utf8",encode("utf8",$config ->{'Laser_op'}->{'RECORD'}->[$i]->{'Vendor'}));
    if (grep /^$Materials_Vendor$/,@Vend_list) {
    } else {
    push(@Vend_list,$Materials_Vendor);
    }
    $all_data[$i]{'Vendor'}=$Materials_Vendor;
=cut
    $Materials_PPtype = encode('utf8', $config->{'Laser_op'}->{'RECORD'}->[$i]->{'PP_TYPE'});
    if (grep {$_ eq $Materials_PPtype} @PP_list) {
        #if (grep /^$Materials_PPtype$/,@PP_list) {
    }
    else {
        push(@PP_list, $Materials_PPtype);
    }
    #$Materials_TG_up = encode('utf8',$config ->{'Laser_op'}->{'RECORD'}->[$i]->{'TG_up'});
    $Drill_Size = encode('utf8', $config->{'Laser_op'}->{'RECORD'}->[$i]->{'Dril_Size'});
    if (grep {$_ eq $Drill_Size} @DS_list) {
        #if (grep /^$Drill_Size$/,@DS_list) {
    }
    else {
        push(@DS_list, $Drill_Size);
    }
    #$Seg_up = encode('utf8',$config ->{'Laser_op'}->{'RECORD'}->[$i]->{'Segments_Thick_up'});
    #$Program_Name = encode('utf8',$config ->{'Laser_op'}->{'RECORD'}->[$i]->{'Program_Name'});
    $i++;
}


########Table框架
#my @htitle = ('选择', '层名', 'X涨缩', 'Y涨缩', '镜像', '孔径', '介质厚度', 'PP张数', 'PP类型', '参数', '手动选参');
my @htitle = ('选择', '层名', 'X涨缩', 'Y涨缩', '镜像', '孔径', '参数');
my @mirror = ('no', 'yes');
my @cool_speed = ('no', 'yes');
my @spp_type = @PP_list;
push(@spp_type, '其他');
my @spp_num = ('1', '2', '其他');
my $rows = $#rlayers + 2;

my $table = $table_frame->Table(
    -columns    => 12,
    -rows       => $rows,
    -fixedrows  => 1,
    -scrollbars => 'oe')
    ->pack(
    -side   => 'left',
    -fill   => 'both',
    -expand => 1);

for (my $i = 0; $i <= $#htitle; $i++) {
    my $hname = $table->Label(
        -text        => "$htitle[$i]",
        -font        => [ -size => 12 ],
        -relief      => 'raised',
        -borderwidth => 4,
        -width       => 9)
        ->pack(
        -side   => 'left',
        -fill   => 'both',
        -expand => 1);
    $table->put(0, $i, $hname);
}

&show_table;
my $bud0 = $bot->Button(
    -text                => "读取HDI Inplan数据",
    -font                => [ -size => 10, ],
    -activeforeground    => 'red',
    -borderwidth         => 3,
    -height              => 1,
    -width               => 20,
    -relief              => 'raised',
    -highlightbackground => 'black',
    -command             => \&getInplanData)
    ->pack(
    -side => 'left',
    -fill => 'both',
    -pady => 5,
    -padx => 3);

my $bud1 = $bot->Button(
    -text                => "输出",
    -font                => [ -size => 10, ],
    -activeforeground    => 'red',
    -borderwidth         => 3,
    -height              => 1,
    -width               => 6,
    -relief              => 'raised',
    -highlightbackground => 'black',
    -command             => \&apply_)
    ->pack(-side => 'left', -fill => 'both', -pady => 5, -padx => 93);

my $bud2 = $bot->Button(-text => "退出",
    -font                     => [ -size => 10, ],
    -activeforeground         => 'red',
    -borderwidth              => 3,
    -height                   => 1,
    -width                    => 6,
    -relief                   => 'raised',
    -highlightbackground      => 'black',
    -command                  => sub {exit 0})
    ->pack(-side => 'left', -fill => 'both', -pady => 5, -padx => 93);
MainLoop;


#### 窗口居中
# win_mid未使用
sub win_mid {
    my $x_resolution = $mw->screenwidth;
    my $y_resolution = $mw->screenheight;
    $x = $mw->reqwidth; #取真实宽度和高度
    $y = $mw->reqheight;
    print "$x,$y\n";
    my $xp = $x_resolution / 2 - $x / 2;
    my $yp = $y_resolution / 2 - $y / 2;
    $mw->geometry("200x$y+$xp+$yp");
}

sub show_table {
    for (my $i = 0; $i <= $#rlayers; $i++) {
        my $crow = $i + 1;
        #$cb_value[$i] = 0;
        $cb[$i] = $table->Checkbutton(
            -variable    => \${$hash{$rlayers[$i]}}[0],
            -offvalue    => 0,
            -onvalue     => 1,
            -indicatoron => 1,
            -relief      => 'groove',)
            ->pack(-side => 'left', -fill => 'both', -expand => 1);
        $table->put($crow, 0, $cb[$i]);
        #####
        #${$hash{$rlayers[$i]}}[5] = "$rlayers[$i]";
        $nalyer[$i] = $table->Label(
            -text         => \${$hash{$rlayers[$i]}}[1],
            -textvariable => \${$hash{$rlayers[$i]}}[1],
            -font         => [ -size => 12 ],
            -relief       => 'groove',
            -width        => 0)
            ->pack(-side => 'left', -fill => 'both', -expand => 1);
        $table->put($crow, 1, $nalyer[$i]);
        #####
        $xscale[$i] = $table->Entry(
            -textvariable => \${$hash{$rlayers[$i]}}[2],
            -font         => [ -size => 12 ],
            -background   => 'white',
            -relief       => 'groove',
            -width        => 9)
            ->pack(-side => 'left', -fill => 'both', -expand => 1);
        $table->put($crow, 2, $xscale[$i]);
        #####
        $yscale[$i] = $table->Entry(
            -textvariable => \${$hash{$rlayers[$i]}}[3],
            -font         => [ -size => 12 ],
            -background   => 'white',
            -relief       => 'groove',
            -width        => 9)
            ->pack(-side => 'left', -fill => 'both', -expand => 1);
        $table->put($crow, 3, $yscale[$i]);
        #####
        #$opmin_value[$i] = $mirror[0];
        $opmin[$i] = $table->Optionmenu(
            -font     => [ -size => 12 ],
            -relief   => 'groove',
            -variable => \${$hash{$rlayers[$i]}}[4],
            -options  => [ @mirror ])
            ->pack(-side => 'left', -fill => 'both', -expand => 1);
        $table->put($crow, 4, $opmin[$i]);
        #####
        $dsmin[$i] = $table->Label(
            -text         => \${$hash{$rlayers[$i]}}[5],
            -textvariable => \${$hash{$rlayers[$i]}}[5],
            -font         => [ -size => 12 ],
            -relief       => 'groove',
            -width        => 15)
            ->pack(-side => 'left', -fill => 'both', -expand => 1);

        $table->put($crow, 5, $dsmin[$i]);
        #####
        # $ptype[$i] = $table->Optionmenu(
            # -font     => [ -size => 12 ],
            # -relief   => 'groove',
            # -variable => \${$hash{$rlayers[$i]}}[6],
            # -options  => [ @spp_type ],
            # -state    => ${$hash{$rlayers[$i]}}[11],
            # -command  => sub {&click_option_button})
            # ->pack(-side => 'left', -fill => 'both', -expand => 1);
        # $table->put($crow, 8, $ptype[$i]);
        #####
        # $pnum[$i] = $table->Optionmenu(
            # -font     => [ -size => 12 ],
            # -relief   => 'groove',
            # -variable => \${$hash{$rlayers[$i]}}[7],
            # -options  => [ @spp_num ],
            # -state    => ${$hash{$rlayers[$i]}}[11],
            # -command  => sub {&click_option_button})
            # ->pack(-side => 'left', -fill => 'both', -expand => 1);
        # $table->put($crow, 7, $pnum[$i]);
        #####
        # $seg_thick[$i] = $table->Entry(
            # -textvariable => \${$hash{$rlayers[$i]}}[9],
            # -font         => [ -size => 12 ],
            # -background   => 'white',
            # -relief       => 'groove',
            # -state        => ${$hash{$rlayers[$i]}}[11],
            # -width        => 9)
            # ->pack(-side => 'left', -fill => 'both', -expand => 1);
        # $table->put($crow, 6, $seg_thick[$i]);

        #####
        if (${$hash{$rlayers[$i]}}[8] =~ /^Null/) {
            our $bg_color = "red";
        }
        else {
            our $bg_color = "grey";
        }
        $conlyer[$i] = $table->Label(
            -text         => \${$hash{$rlayers[$i]}}[8],
            -textvariable => \${$hash{$rlayers[$i]}}[8],
            -background   => "$bg_color",
            -font         => [ -size => 12 ],
            -relief       => 'groove',
            -width        => 70)
            ->pack(-side => 'left', -fill => 'both', -expand => 1);
        $table->put($crow, 6, $conlyer[$i]);

        # $cbb[$i] = $table->Checkbutton(
            # -variable    => \${$hash{$rlayers[$i]}}[10],
            # -offvalue    => 0,
            # -onvalue     => 1,
            # -indicatoron => 1,
            # -relief      => 'groove',
            # -command     => sub {&click_chk_button})
            # ->pack(-side => 'left', -fill => 'both', -expand => 1);
        # $table->put($crow, 10, $cbb[$i]);
		#####
    }
}

sub grep_arrey{	
	my @result = (); 
	foreach my $item (@_) {
    push @result, $item unless grep { $_ == $item } @result;
	}
	return @result;
}

sub click_option_button {
    my @check_data = ();
    #循环列表#
    for (my $a = 0; $a <= $#rlayers; $a++) {
        if (${$hash{$rlayers[$a]}}[9] ne "" && ${$hash{$rlayers[$a]}}[9] ne "0" && ${$hash{$rlayers[$a]}}[9] =~ /[0-9].*/) {
            $check_data[$a] = "no";
            # ###all_data 循环XML数据 all_data#
            if (${$hash{$rlayers[$a]}}[7] eq '其他' || ${$hash{$rlayers[$a]}}[6] eq '其他') {
                #} elsif ( ${$hash{$rlayers[$a]}}[11] == 0 ) {
                #	$check_data[$a] = "yes";
            }
            else {
                my $k = 0;
                while ($all_data[$k]) {
                    # define 判断条件 pp类型 供 TG值范围 介质厚度范围 最小孔径 # 给参数赋值 # 20181030更改 介质厚度更新为 PP张数 #
                    if ($all_data[$k]{'PP_TYPE'} eq ${$hash{$rlayers[$a]}}[6] && ${$hash{$rlayers[$a]}}[9] <= $all_data[$k]{'Segck_up'} && ${$hash{$rlayers[$a]}}[9] >= $all_data[$k]{'Segck_down'} && ${$hash{$rlayers[$a]}}[7] <= $all_data[$k]{'PP_NUM_up'} && ${$hash{$rlayers[$a]}}[7] >= $all_data[$k]{'PP_NUM_down'} && ${$hash{$rlayers[$a]}}[5] eq $all_data[$k]{'Dril_Size'}) {
                        $check_data[$a] = "yes";
                        ${$hash{$rlayers[$a]}}[8] = $all_data[$k]{'Program_Name'};
                    }
                    $k++;
                }
            }
            if ($check_data[$a] eq "no") {${$hash{$rlayers[$a]}}[8] = "Null";}
        }
    }
    &show_table;
}

sub click_chk_button {
    #my @check_data = ();
    #循环列表# 勾选了手动选择则栏位状态可用，否则，不可选择
    for (my $a = 0; $a <= $#rlayers; $a++) {
        if (${$hash{$rlayers[$a]}}[8] !~ /Null/ && ${$hash{$rlayers[$a]}}[10] eq "1") {
            #code
            $c->Messages('info', "层别$rlayers[$a]已有参数，不允许更改");
            ${$hash{$rlayers[$a]}}[10] = 0;
        }
        if (${$hash{$rlayers[$a]}}[8] =~ /Null/ && ${$hash{$rlayers[$a]}}[10] eq "0") {
            #code
            $c->Messages('info', "层别$rlayers[$a]未选择到参数，不允许锁定");
            ${$hash{$rlayers[$a]}}[10] = 1;
        }
        if (${$hash{$rlayers[$a]}}[10] eq "1") {
            ${$hash{$rlayers[$a]}}[11] = "normal";
        }
        else {
            ${$hash{$rlayers[$a]}}[11] = "disable";
        }
    }
    &show_table;
}

sub apply_ {
    my @check_data = ();
    # --循环列表#
    # --检测是否有定义镭射参数 #
    
    # --分割模式,板内镭射孔不能为空  AresHe 2021.11.8
    if ($clip_mode ne "不分割") {
        foreach my $info(keys %layer_laser_info){
            #print ("$layer_laser_info{$info}\n");
            if ($layer_laser_info{$info} == 0) {
                $c->Messages("info", "系统自动检测到[$info]镭射层除以下孔之外为空,检查不到镭射孔,请检查.\n机台孔:\t0.501\nlot号孔:\t0.515\n五代靶孔:\t0.520\n定位孔:\t3.175\n");
                #exit;
            }
        }
    }
    
    for (my $a = 0; $a <= $#rlayers; $a++) {
        # --没有选择的层直接跳过  AresHe 2021.11.30
        next if ${$hash{$rlayers[$a]}}[0] == 0;
        ##check laser config ##
		# 改为只提醒 20240103  杨年虎
		
		if ($layer_8mil_info{$rlayers[$a]}{'mgs'} eq 'mgs1' ){
			$c->Messages("info", "$rlayers[$a] 8-9mil孔承接层铜厚小于1OZ，但是MI未按工艺规范打5遍，请和MI确认！");
#			return;
		}elsif($layer_8mil_info{$rlayers[$a]}{'mgs'} eq 'mgs2'){
			$c->Messages("info", "$rlayers[$a] 8-9mil孔承接层铜厚大于1OZ，工艺规范需要绕烧，MI打5遍,请和MI确认！");
#			return;
		}
		
        if (${$hash{$rlayers[$a]}}[8] =~ /^Null/) {
            $c->Messages('info', "$rlayers[$a]没有镭射参数");
			# $c->Messages('info', "$rlayers[$a]没有雷射参数\n确定输出的,请主管输出(44566|68027|44024|83288|74648|91259)!");			
            # if ($UserName !~ /^44566|68027|44024|84310|83288|44839|74648|91259$/) {
                # #goto RESTART # --2021.12.16周涌要求,参数为None也不允许输出
				# return;
            # }
        }
        if (${$hash{$rlayers[$a]}}[8] eq 'None') {
            $c->Messages('info', "$rlayers[$a],Inplan中参数定义为None，没有镭射参数");
			# $c->Messages('info', "$rlayers[$a],Inplan中参数定义为None,\n请联系MI确认参数。\n确定没有的,请主管输出(44566|68027|44024|83288|74648|91259)!");             
            # goto RESTART # --2021.09.25周六宋超要求取消
            # if ($UserName !~ /^44566|68027|44024|84310|83288|44839|74648|91259$/) {
                # #goto RESTART # --2021.12.16周涌要求,参数为None也不允许输出
				# return;
            # }
        }
        if (${$hash{$rlayers[$a]}}[9] ne '0' && ${$hash{$rlayers[$a]}}[9] ne '') {
            #当介厚不为空时进行判断
            $check_data[$a] = "Null";
            my $k = 0;
            #循环XML数据 all_data#
            while ($all_data[$k]) {
                #判断条件 pp类型 供应商 TG值范围 介质厚度范围 最小孔径 # 给参数赋值 #
                if ($all_data[$k]{'PP_TYPE'} eq ${$hash{$rlayers[$a]}}[6]
                    && ${$hash{$rlayers[$a]}}[9] <= $all_data[$k]{'Segck_up'}
                    && ${$hash{$rlayers[$a]}}[9] >= $all_data[$k]{'Segck_down'}
                    && ${$hash{$rlayers[$a]}}[7] <= $all_data[$k]{'PP_NUM_up'}
                    && ${$hash{$rlayers[$a]}}[7] >= $all_data[$k]{'PP_NUM_down'}
                    && ${$hash{$rlayers[$a]}}[5] eq $all_data[$k]{'Dril_Size'}
                ) {
                    $check_data[$a] = $all_data[$k]{'Program_Name'};
                }
                $k++;
            }
            if ($check_data[$a] eq ${$hash{$rlayers[$a]}}[8]) {
            }
            else {
                $c->Messages('info', "$rlayers[$a]雷射参数未更新,应为$check_data[$a]");
                #goto RESTART
				return;
            }
        }
    }
    
    destroy $mw;
    ##get set SR size ##
    $f->INFO(units  => 'mm', angle_direction => 'ccw', entity_type => 'step',
        entity_path => "$JOB/$step_name",
        data_type   => 'SR');

    my @gSRstep = @{$f->{doinfo}{gSRstep}}; ########拼板左下角最小值
    my @gSRxmin = @{$f->{doinfo}{gSRxmin}};
    my @gSRymin = @{$f->{doinfo}{gSRymin}};
    my @gSRxmax = @{$f->{doinfo}{gSRxmax}};
    my @gSRymax = @{$f->{doinfo}{gSRymax}};
    my %step_position_min = ();
    my %step_position_max = ();
    for (my $i = 0; $i <= $#gSRstep; $i++) {
        if ($gSRstep[$i] =~ /^set/ || $gSRstep[$i] =~ /^edit/) {
            my $length1 = sqrt(($gSRxmin[$i]) ** 2 + ($gSRymin[$i]) ** 2);
            @{$step_position_min{$length1}} = ($gSRxmin[$i], $gSRymin[$i]);
            my $length2 = sqrt(($gSRxmax[$i]) ** 2 + ($gSRymax[$i]) ** 2);
            @{$step_position_max{$length2}} = ($gSRxmax[$i], $gSRymax[$i]);
        }
    }

    my @min = sort {$a <=> $b} keys(%step_position_min);
    our $srx_min = ${$step_position_min{$min[0]}}[0] * 1000;
    our $sry_min = ${$step_position_min{$min[0]}}[1] * 1000;
    my @max = sort {$b <=> $a} keys(%step_position_max);
    our $srx_max = ${$step_position_max{$max[0]}}[0] * 1000;
    our $sry_max = ${$step_position_max{$max[0]}}[1] * 1000;
	
    ##get profile size##
    $f->INFO(units  => 'mm', angle_direction => 'ccw', entity_type => 'step',
        entity_path => "$JOB/$step_name",
        data_type   => 'PROF_LIMITS');
    $op_x_max = $f->{doinfo}{gPROF_LIMITSxmax}; ########profile中心值
    our $op_x_center = $op_x_max / 2;
    $op_y_max = $f->{doinfo}{gPROF_LIMITSymax} / 2;
    our $op_y_center = $op_y_max / 2;

    for (my $i = 0; $i <= $#rlayers; $i++) {
        # --没有选择的层直接跳过  AresHe 2021.11.30
        next if ${$hash{$rlayers[$i]}}[0] == 0;
        my %loghash;
        $loghash{'Layer'} = $rlayers[$i];
        $loghash{'WarnInfo'} = $clip_mode . ';打5次:'. $laser_drill_five_times_info{"$rlayers[$i]"};
        $loghash{'LotDirec'} = '';
        if ($scale_position eq "中心") {
            $scale_center_x = $op_x_center;
            $scale_center_y = $op_y_center;
        }
        else {
            $scale_center_x = 0;
            $scale_center_y = 0;
        }

        our $dld_lyr;
        my $dld_exist;
        my $lr_laser = "no";
        my $lr_layer = "lr" . substr($rlayers[$i], 1);
        my $mirror_laser = $rlayers[$i];
        my $sym_num = $sym_num_hash{"$rlayers[$i]"};
        $f->COM("set_subsystem,name=1-Up-Edit");
        $f->COM("top_tab,tab=Display");
		$f->COM("open_entity,job=$JOB,type=step,name=$step_name,iconic=no");
        #$f->AUX("set_step,name=$step_name");
        $f->AUX("set_group,group=$f->{COMANS}");
		
		system("rm -rf /tmp/cool_speed_${JOB}*");

        if ($rlayers[$i] =~ /^s(\d+)-(\d+)-?(\d+)?-?(\d+)?-?(\d+)?-?(\d+)?-?(\d+)?-?(\d+)?$/) {
            #if ($rlayers[$i] =~ /^s(\d+)-(\d+)-?(\d+)$/) {
				my $check_signal = "";
				if ($rlayers[$i] =~ /^s(\d+)-(\d+)$/){
					$dld_lyr = "dld$1-$2";
					$check_signal = "l$2";
					if (abs($1 - $2) > 1 and $skipvia ne "not_check_skipvia"){
						#先检测反面镭射 
						my $reverse_laser_layer;
						my $skipvia_change;
						if ($1 >= $halfjob_numb){
							$reverse_laser_layer = "s".($job_signal_nubers-$1+1)."-".($job_signal_nubers-$1+3);
							$skipvia_change = &check_reverse_laser_skipvia_touch_mid_layer($job_signal_nubers-$1+1,$job_signal_nubers-$1+3,$reverse_laser_layer);
						}else{
							$reverse_laser_layer = "s".($job_signal_nubers-$1+1)."-".($job_signal_nubers-$1-1);
							$skipvia_change = &check_reverse_laser_skipvia_touch_mid_layer($job_signal_nubers-$1+1,$job_signal_nubers-$1-1,$reverse_laser_layer);
						}
						#$f->PAUSE($skipvia_change."----".$reverse_laser_layer);
						if ($skipvia_change eq "change"){
							my $mid_dld_index= ($1 < $2) ? $2 - 1 : $2 + 1;
							$check_signal = "l".$mid_dld_index
						}else{
							$check_signal = &check_skipvia_touch_mid_layer($1,$2,$rlayers[$i]);
						}
						$f->COM("set_subsystem,name=1-Up-Edit");
						$f->COM("top_tab,tab=Display");
						$f->COM("open_entity,job=$JOB,type=step,name=$step_name,iconic=no");
						#$f->AUX("set_step,name=$step_name");
						$f->AUX("set_group,group=$f->{COMANS}");
						#$f->PAUSE($check_signal);
					}
				}
				if ($rlayers[$i] =~ /^s(\d+)-(\d+)-(\d+)$/){
					$dld_lyr = "dld$1-$2";
					$check_signal = "l$2";
				}
				if ($rlayers[$i] =~ /^s(\d+)-(\d+)-(\d+)$/){
					$dld_lyr = "dld$1-$2";
					$check_signal = "l$2";
				}
				if ($rlayers[$i] =~ /^s(\d+)-(\d+)-(\d+)-(\d+)$/){
					$dld_lyr = "dld$1-$2";
					$check_signal = "l$2";
				}
				if ($rlayers[$i] =~ /^s(\d+)-(\d+)-(\d+)-(\d+)-(\d+)$/){
					$dld_lyr = "dld$1-$2";
					$check_signal = "l$2";
				}
				if ($rlayers[$i] =~ /^s(\d+)-(\d+)-(\d+)-(\d+)-(\d+)-(\d+)$/){
					$dld_lyr = "dld$1-$2";
					$check_signal = "l$2";
				}
				if ($rlayers[$i] =~ /^s(\d+)-(\d+)-(\d+)-(\d+)-(\d+)-(\d+)-(\d+)$/){
					$dld_lyr = "dld$1-$2";
					$check_signal = "l$2";
				}
				if ($check_signal eq ""){
					$c->Messages("info", "合并层$rlayers[$i] 超dld判断设计，请反馈程序工程师处理！");
					exit 0;
				}
                $mirror_laser = "s$2-$1";
                
            #}
            #
            #if ($rlayers[$i] =~ /s([0-9][0-9]?)-([0-9][0-9]?)$/) {
            #    $dld_lyr = "dld$1-$2";
            #    $mirror_laser = "s$2-$1";
            #}

            # 判断是否为芯板镭射，s6-7若对应有lr6-7存在，表示为芯板镭射,李家兴依据story-view-2042添加
            $f->DO_INFO("-t layer -e $JOB/$step_name/$lr_layer -m script -d EXISTS");
            if ($f->{doinfo}{gEXISTS} eq "yes" and $rlayers[$i] !~ /^s(\d+)-(\d+)-(\d+).*$/) {
                $lr_laser = "yes";
            }
            if ($lr_laser eq "no"){
                &check_dld_layer($dld_lyr,"$check_signal");
            }

            #$f->PAUSE('xxx'.$dld_lyr);
            $f->DO_INFO("-t layer -e $JOB/$step_name/$dld_lyr -d EXISTS");
            if ($f->{doinfo}{gEXISTS} eq "yes") {
                # --周涌要求,不分割输出完镭射钻孔后,不再需要0.045的孔   AresHe 2021.9.7
                #if ($clip_mode eq "不分割") {
                    $dld_exist = "yes";
                    &deleteLaserTouchDLD($rlayers[$i], $dld_lyr);
                    $f->COM("clear_layers");
                    $f->COM("affected_layer,mode=all,affected=no");
                    $f->COM("units,type=mm");
                    $f->VOF();
                    $f->COM("delete_layer,layer=$dld_lyr-tmp");
                    $f->VON();
                    $f->COM("display_layer,name=$dld_lyr,display=yes");
                    $f->COM("work_layer,name=$dld_lyr");
                    $f->COM("sel_copy_other,dest=layer_name,target_layer=$dld_lyr-tmp,invert=no,dx=0,dy=0,size=0,x_anchor=0,y_anchor=0,subsystem=1-Up-Edit");
                    $f->COM("display_layer,name=$dld_lyr-tmp,display=yes");
                    $f->COM("work_layer,name=$dld_lyr-tmp");
                    $f->COM("sel_change_sym,symbol=r45,reset_angle=no");
                    $f->COM("sel_copy_other,dest=layer_name,target_layer=$rlayers[$i],invert=no,dx=0,dy=0,size=0,x_anchor=0,y_anchor=0,subsystem=1-Up-Edit");
                    $f->COM("delete_layer,layer=$dld_lyr-tmp");
                #}
            }
            else {
                $dld_exist = "no";
                # --新增core芯板的不再提示 AresHe 2022.1.24
                if ($lr_laser eq "no") {
                    $c->Messages("info", "未设计$dld_lyr,输出钻带$rlayers[$i]无T500刀序")
                }
            }
        }else{
			$c->Messages("info", "合并层$rlayers[$i] 超dld判断设计，请反馈程序工程师处理！");
			exit 0;
		}

        $f->COM("set_subsystem,name=Nc-Manager");
        $f->COM("nc_set_current,job=$JOB,step=$step_name,layer=,ncset=");
        #$f->PAUSE('xx');
        if (${$hash{$rlayers[$i]}}[0] == 1) {
            #$f->PAUSE($rlayers[$i]);
            if (${$hash{$rlayers[$i]}}[4] eq 'no') {
                $ver = 1;
            }
            elsif (${$hash{$rlayers[$i]}}[4] eq 'yes') {
                $ver = 7;
            }
            $loghash{'ver'} = $ver;
            my $scale_x = ${$hash{$rlayers[$i]}}[2];
            my $scale_y = ${$hash{$rlayers[$i]}}[3];
            $loghash{'scale_x'} = $scale_x;
            $loghash{'scale_y'} = $scale_y;
            $loghash{'scale_center_x'} = $scale_center_x;
            $loghash{'scale_center_y'} = $scale_center_y;
            $loghash{'Mirror'} = ${$hash{$rlayers[$i]}}[4];

            # --TODO 芯板镭射或者大于两把刀时，先用第1象限输出，再用第七象限输出
            my $first_output = 'yes';
            my $nLoop = 1;
            if ($lr_laser eq 'yes') {
                $nLoop = 2;
            }

            for (my $n = 1; $n <= $nLoop; $n++) {
                $f->VOF;
                $f->COM("nc_delete,layer=$rlayers[$i],ncset=ncset.$rlayers[$i]");
                $f->VON;
				
				if ( $laser_drill_five_times_info{"$rlayers[$i]"} eq 'yes'){
					#$f->COM("nc_set_optim,optimize=yes,iterations=5,reduction_percent=1,cool_spread=5000,break_sr=yes,xspeed=2540,yspeed=2540,diag_mode=45ort");	
					foreach my $cool_speed_size(@{$layer_cool_speed_info{$rlayers[$i]}}){
						 open(SETTABLE,">/tmp/cool_speed_${JOB}_$rlayers[$i]_${cool_speed_size}.info") or die "can't open file /tmp/cool_speed_${JOB}_$rlayers[$i]_${cool_speed_size}.info: $!";
						 print SETTABLE "196.85\n";
						 close (SETTABLE);
					}					
				}
				
                $f->COM("nc_create,ncset=ncset.$rlayers[$i],device=misumi,lyrs=$rlayers[$i],thickness=0");
                $f->COM("nc_set_advanced_params,layer=$rlayers[$i],ncset=ncset.$rlayers[$i],parameters=(rout_arc_as_ij=no)(out_exc_old_sr_syntax=no)");
                $f->COM("nc_set_current,job=$JOB,step=$step_name,layer=$rlayers[$i],ncset=ncset.$rlayers[$i]");
                
                # --TODO 解决报internal error的方法，李家兴添加20200927,subsystem切回1-Up-Eidt再切回NC-Manager
                $f->COM("set_subsystem,name=1-Up-Edit");
                $f->COM("top_tab,tab=Display");
                # $f->PAUSE("\$step_name : $step_name");
                $f->COM("set_step,name=$step_name");
                $f->AUX("set_group,group=$f->{COMANS}");
                $f->COM("set_subsystem,name=Nc-Manager");
                # ---------------------------------------------------
                $f->COM("nc_set_file_params,output_path=$output_path,output_name=$JOB.$rlayers[$i],zeroes=trailing,units=mm,tool_units=mm,nf1=3,nf2=3,decimal=no,modal_coords=no,single_sr=no,sr_zero_set=no,repetitions=sr,incremental=no,ext_layer=drl2rt,sr_zero_layer=,ccw=no,short_lines=none,allow_no_chain_f=no,no_chain_as_slot=no,keep_table_order=no,max_arc_angle=0,comp_short_slot=no,gscale_file_name=,layer_datum=bottom_left,gscle_align_angle=0,gscl_offset_x=0,gscl_offset_y=0");
                $f->COM("nc_register,angle=0,xoff=0,yoff=0,version=$ver,xorigin=0,yorigin=0,xscale=$scale_x,yscale=$scale_y,xscale_o=$scale_center_x,yscale_o=$scale_center_y,xmirror=no,ymirror=no");
				
				if ($skip_hole eq '是') {
					$f->PAUSE('需要镭射跳钻，请自行打开排刀表，在最后一列加跳钻距离5000然后点击继续!');
				}
				$f->COM("set_view,view=Tools Table,level=user");
                $f->COM("nc_cre_output,layer=$rlayers[$i],ncset=ncset.$rlayers[$i]");

                ####################################################导出分割资料####################################################
                # --输出备份分割层数据
                if ($clip_mode ne "不分割" and $rlayers[$i] =~ /^s(\d+)-(\d+)-?(\d+)?-?(\d+)?-?(\d+)?-?(\d+)?-?(\d+)?-?(\d+)?$/) {
                    my $clip_layer = $rlayers[$i] . "-fg";
                    
                    # --新增镭射层自动分割    AresHe 2021.9.16
                    my $dld_layer = $dld_lyr;#"dld".$1;
                    
                    our $clip_drill_counnt = &clip_laser_layer($rlayers[$i],$clip_layer,$dld_layer);
                    
                    #$f->PAUSE("$clip_layer");
                    $f->INFO(entity_type => 'layer',
                        entity_path => "$JOB/$step_name/$clip_layer",
                        data_type => 'EXISTS');
                    if ($f->{doinfo}{gEXISTS} eq "yes") {
                        $f->VOF;
                        $f->COM("nc_delete,layer=$clip_layer,ncset=ncset.$clip_layer");
                        $f->VON;
						
						if ( $laser_drill_five_times_info{"$rlayers[$i]"} eq 'yes'){
							#$f->COM("nc_set_optim,optimize=yes,iterations=5,reduction_percent=1,cool_spread=5000,break_sr=yes,xspeed=2540,yspeed=2540,diag_mode=45ort");	
							foreach my $cool_speed_size(@{$layer_cool_speed_info{$rlayers[$i]}}){
								 open(SETTABLE,">/tmp/cool_speed_${JOB}_$rlayers[$i]_${cool_speed_size}.info") or die "can't open file /tmp/cool_speed_${JOB}_$rlayers[$i]_${cool_speed_size}.info: $!";
								 print SETTABLE "196.85\n";
								 close (SETTABLE);
							}
						}
						
                        $f->COM("nc_create,ncset=ncset.$clip_layer,device=misumi,lyrs=$clip_layer,thickness=0");
                        $f->COM("nc_set_advanced_params,layer=$clip_layer,ncset=ncset.$clip_layer,parameters=(rout_arc_as_ij=no)(out_exc_old_sr_syntax=no)");
                        $f->COM("nc_set_current,job=$JOB,step=$step_name,layer=$clip_layer,ncset=ncset.$clip_layer");
        
                        # --TODO 解决报internal error的方法，李家兴添加20200927,subsystem切回1-Up-Eidt再切回NC-Manager
                        $f->COM("set_subsystem,name=1-Up-Edit");
                        $f->COM("top_tab,tab=Display");
                        # $f->PAUSE("\$step_name : $step_name");
                        $f->COM("set_step,name=$step_name");
                        $f->AUX("set_group,group=$f->{COMANS}");
                        $f->COM("set_subsystem,name=Nc-Manager");
                        # ---------------------------------------------------
                        $f->COM("nc_set_file_params,output_path=$output_path,output_name=$JOB.$clip_layer,zeroes=trailing,units=mm,tool_units=mm,nf1=3,nf2=3,decimal=no,modal_coords=no,single_sr=no,sr_zero_set=no,repetitions=sr,incremental=no,ext_layer=drl2rt,sr_zero_layer=,ccw=no,short_lines=none,allow_no_chain_f=no,no_chain_as_slot=no,keep_table_order=no,max_arc_angle=0,comp_short_slot=no,gscale_file_name=,layer_datum=bottom_left,gscle_align_angle=0,gscl_offset_x=0,gscl_offset_y=0");
                        $f->COM("nc_register,angle=0,xoff=0,yoff=0,version=$ver,xorigin=0,yorigin=0,xscale=$scale_x,yscale=$scale_y,xscale_o=$scale_center_x,yscale_o=$scale_center_y,xmirror=no,ymirror=no");

						if ($skip_hole eq '是') {
							$f->PAUSE('需要镭射跳钻，请自行打开排刀表，在最后一列加跳钻距离5000然后点击继续!');
						}
						$f->COM("set_view,view=Tools Table,level=user");
						$f->COM("nc_cre_output,layer=$clip_layer,ncset=ncset.$clip_layer");
                        #code   
                    }else{
                        $c->Messages('info', "匹配不到($clip_layer)分割备份层,程序将退出!");
                        exit 0;
                    }
                }
                ####################################################导出分割资料####################################################
                
                if ($dld_lyr ne "" && $dld_exist eq "yes") {
                    &deleteLaserTouchDLD($rlayers[$i], $dld_lyr);
                }

                my $yyear = strftime "%Y-%m-%d", localtime;
                my $dday = strftime "%H:%M:%S", localtime;
                my $local_time = "$yyear $dday";
                chomp($ipname);
                my $head_log = "/Date:$local_time User:$incam_user Host:$ipname Job:$JOB Step:$step_name Layer:$rlayers[$i] Scale:X=$scale_x Y=$scale_y Anchor=$scale_position X/2=$scale_center_x  Y/2=$scale_center_y	Mirror_ver:$ver";

                # 增加判断是否阴阳拼版存在的情况下有Lot号存在，（阴阳拼版的lot号应在板边添加）

                if ($special_laser_mode eq 'yes' && exists $r515CheckData{$rlayers[$i]}{'lotCode'}) {
                    $loghash{'lotCode'} = 'yes';
                    $loghash{'LotDirec'} = $r515CheckData{$rlayers[$i]}{'lotCode'};
                    print Dumper(\%r515CheckData);
                    $loghash{'lotCode'} = 'yes';
                
                    &addLotStep($rlayers[$i], 's1-2', ($r515CheckData{"$rlayers[$i]"}{'corlist'}));
                    my $opR515Result = &deal_Lot_laser($rlayers[$i]);
                    if ($opR515Result eq 'getDirectError') {
                        $c->Messages("info", "获取层别$rlayers[$i] 镭射Lot号方向失败，请检查输出钻带.");
                        $loghash{'WarnInfo'} = 'getDirectError' . ';' . $loghash{'WarnInfo'};
                        $loghash{'lotCode'} = 'no';
                        %r515cor = {}; #  提前此赋值语句 2019.12.28
                    }
                    &chg_hole($n, $rlayers[$i], $head_log, ${$hash{$rlayers[$i]}}[8], %r515cor);
                }
                elsif (exists $r515CheckData{$rlayers[$i]} && exists $r515CheckData{$rlayers[$i]}{'LotDirec'}) {
                    &deal_515_laser($rlayers[$i]);
                    &chg_hole($n, $rlayers[$i], $head_log, ${$hash{$rlayers[$i]}}[8], %r515cor);
                    $loghash{'lotCode'} = 'yes';
                    $loghash{'LotDirec'} = $r515CheckData{$rlayers[$i]}{'LotDirec'};

                }
                else {
                    $loghash{'lotCode'} = 'no';
                    %r515cor = {}; #  提前此赋值语句 2019.12.28
                    # print Data::Dumper->Dump([ \%r515cor ], [ qw(*r515cor) ]);
                    &chg_hole($n, $rlayers[$i], $head_log, ${$hash{$rlayers[$i]}}[8], %r515cor);
                }	
				
                $loghash{'Param'} = ${$hash{$rlayers[$i]}}[8];
                $input_file = $des_file;
                $tmp_file = "/tmp/incam.tmp_${JOB}.$rlayers[$i]";
                open INPUT, $input_file or die $!;
                open OUTPUT, ">$tmp_file" or die $!;
                while (<INPUT>) {
                    $line = $_;
                    $line =~ s/G82//g;
                    $line =~ s/G83//g;
                    $line =~ s/%\n/%\nT01\n/g;
                    # === add by song 2020.06.10 尝试更改回读的LOT号孔径，看是否满足回读检查需求====
                    $line =~ s/T22C0.515/T22C0.2/g;
                    print OUTPUT $line;
                }
                close INPUT;
                close OUTPUT;

                if ($clip_mode eq "不分割") {
                    $f->COM("input_manual_reset");
                    if ($first_output eq 'no') {
                        $f->COM("input_manual_set,path=$tmp_file,job=$JOB,step=panel,format=Excellon2,data_type=ascii,units=mm,coordinates=absolute,zeroes=trailing,nf1=3,nf2=3,decimal=no,separator=nl,tool_units=mm,layer=${JOB}.$mirror_laser,wheel=,wheel_template=,nf_comp=0,multiplier=1,text_line_width=0.0024,signed_coords=no,break_sr=yes,drill_only=no,merge_by_rule=no,threshold=200,resolution=3");
                    }
                    else {
                        $f->COM("input_manual_set,path=$tmp_file,job=$JOB,step=panel,format=Excellon2,data_type=ascii,units=mm,coordinates=absolute,zeroes=trailing,nf1=3,nf2=3,decimal=no,separator=nl,tool_units=mm,layer=${JOB}.$rlayers[$i],wheel=,wheel_template=,nf_comp=0,multiplier=1,text_line_width=0.0024,signed_coords=no,break_sr=yes,drill_only=no,merge_by_rule=no,threshold=200,resolution=3");
                    }
                    
                    $f->COM("input_manual,script_path=");
                    $f->COM("matrix_move_row,job=$JOB,matrix=matrix,row=1,ins_row=2");
                    $f->COM("matrix_refresh,job=$JOB,matrix=matrix");
                    
                    if (${$hash{$rlayers[$i]}}[4] eq 'yes') {
                        $f->COM("affected_layer,mode=all,affected=no");
                        $f->COM("affected_layer,name=${JOB}.$rlayers[$i],mode=single,affected=yes");
                        $f->COM("sel_transform,oper=rotate\;mirror,x_anchor=0,y_anchor=0,angle=180,direction=ccw,x_scale=1,y_scale=1,x_offset=0,y_offset=0,mode=anchor,duplicate=no");
                        $f->COM("affected_layer,mode=all,affected=no");
                    }
                }else{
                    # --分割资料回读
                    $f->COM("input_manual_reset");
                    if ($first_output eq 'no') {
                        $f->COM("input_manual_set,path=$reread_file,job=$JOB,step=panel,format=Excellon2,data_type=ascii,units=mm,coordinates=absolute,zeroes=trailing,nf1=3,nf2=3,decimal=no,separator=nl,tool_units=mm,layer=${JOB}.$mirror_laser.write.reread,wheel=,wheel_template=,nf_comp=0,multiplier=1,text_line_width=0.0024,signed_coords=no,break_sr=yes,drill_only=no,merge_by_rule=no,threshold=200,resolution=3");
                    }
                    else {
                        $f->COM("input_manual_set,path=$reread_file,job=$JOB,step=panel,format=Excellon2,data_type=ascii,units=mm,coordinates=absolute,zeroes=trailing,nf1=3,nf2=3,decimal=no,separator=nl,tool_units=mm,layer=${JOB}.$rlayers[$i].write.reread,wheel=,wheel_template=,nf_comp=0,multiplier=1,text_line_width=0.0024,signed_coords=no,break_sr=yes,drill_only=no,merge_by_rule=no,threshold=200,resolution=3");
                    }
                    
                    $f->COM("input_manual,script_path=");
                    $f->COM("matrix_move_row,job=$JOB,matrix=matrix,row=1,ins_row=2");
                    $f->COM("matrix_refresh,job=$JOB,matrix=matrix");
                    
                    if (${$hash{$rlayers[$i]}}[4] eq 'yes') {
                        $f->COM("affected_layer,mode=all,affected=no");
                        $f->COM("affected_layer,name=${JOB}.$rlayers[$i].write.reread,mode=single,affected=yes");
                        $f->COM("sel_transform,oper=rotate\;mirror,x_anchor=0,y_anchor=0,angle=180,direction=ccw,x_scale=1,y_scale=1,x_offset=0,y_offset=0,mode=anchor,duplicate=no");
                        $f->COM("affected_layer,mode=all,affected=no");
                    }
                    
                    # --删除生成的回读文件
                    if (-f $reread_file) {
                        unlink($reread_file);
                    }
                }
    
                unlink($tmp_file);
                push(@recordList, \%loghash);

                # --TODO 芯板镭射或超过两把刀，先用第1象限输出，再用第七象限输出
                # --20200924李家兴依据story-view-2042添加
                # --更改输出文件名，防止被覆盖
				my $erp_laser = $rlayers[$i];
                if ($nLoop == 2) {
                    if ($first_output eq 'yes') {
                        #my $org_file_old = "$output_path/$JOB.$rlayers[$i]";
                        #my $des_file_old = "$output_path/$JOB.$rlayers[$i].write";
                        #my $org_file_new = "$org_file_old.move_back";
                        #my $des_file_new = "$des_file_old.move_back";
                        #rename $org_file_old, $org_file_new;
                        #rename $des_file_old, $des_file_new;
                    }
                    else {
						$erp_laser = $mirror_laser;
						# === 用于ERP比对后，移动镭射输出资料
						$des_file = "$output_path/$JOB.$mirror_laser.write";
						
                        my $org_file_old = "$output_path/$JOB.$rlayers[$i]";
                        my $des_file_old = "$output_path/$JOB.$rlayers[$i].write";
                        my $org_file_new = "$output_path/$JOB.$mirror_laser";
                        my $des_file_new = "$output_path/$JOB.$mirror_laser.write";

                        my $org_file_move = "$org_file_old.move_back";
                        my $des_file_move = "$des_file_old.move_back";
                        rename $org_file_old, $org_file_new;
                        rename $des_file_old, $des_file_new;
                        #rename $org_file_move, $org_file_old;
                        #rename $des_file_move, $des_file_old;
                    }
                }

                if ($first_output eq 'yes') {
                    $first_output = 'no';
                    if ($ver == 1) {
                        $ver = 7;
                    }
                    else {
                        $ver = 1;
                    }
                }
				# 此处输出钻带文件加入参数				
				
				my $send_five_size = 'None';
				if (@{$layer_cool_speed_info{$rlayers[$i]}}){
					my $five_size = join("_",@{$layer_cool_speed_info{$rlayers[$i]}}); 
					$send_five_size = $five_size;
				}
				# $f->PAUSE($send_five_size);		
                system("python $cur_script_dir/reWriteLaserFiles.py $output_path $JOB.$rlayers[$i].write $send_five_size");
				# === 在此处增加钻带文件比对ERP
			    my $get_result = system("python $cur_script_dir/compare_drl_data.py $JOB $erp_laser $output_path $lr_laser $UserName $rlayers[$i]");
				if ($get_result != 0) {
					unless (-e "/tmp/${JOB}_laser_exit_result.log"){
						my $mw1 = MainWindow->new(
								-title      => "镭射输出",
								-background => '#9BDBDB');
						my $ans = $mw1->messageBox(-icon => 'question',-message => '钻带比对异常，是否保留已输出钻带，若选择Yes请务必手动回读到incam比对！',-title => 'quit',-type => 'YesNo');
						if ($ans eq "Yes"){
							mv("$des_file","$output_path_des");
							my $tmp_source = "$output_path/$JOB.$erp_laser";
							mv("$tmp_source","$output_path_des");
						}
					}
					system("rm -rf /tmp/${JOB}_laser_exit_result.log");
					
				} else {
					# === 移动已输出的镭射到正式路径，后者为文件夹
					mv("$des_file","$output_path_des");
					my $tmp_source = "$output_path/$JOB.$erp_laser";
					mv("$tmp_source","$output_path_des");
				}
				

				# -- 写日志文件  --add song 20190416 ##
                if (open(LOG, ">>$logfile") or die("$!")) {
                    print LOG "$head_log ${$hash{$rlayers[$i]}}[0] ${$hash{$rlayers[$i]}}[1] ${$hash{$rlayers[$i]}}[2] ${$hash{$rlayers[$i]}}[3] ${$hash{$rlayers[$i]}}[4] ${$hash{$rlayers[$i]}}[5] ${$hash{$rlayers[$i]}}[6] ${$hash{$rlayers[$i]}}[7] ${$hash{$rlayers[$i]}}[8]\n";
                    close(LOG);
                }
            }
        }
	}
	
	if ($^O eq MSWin32) {

		$f->COM("set_subsystem,name=1-Up-Edit");
		$f->COM("top_tab,tab=Display");
	}
	
	#system("rm -rf /tmp/cool_speed_${JOB}*");
	
    &writeLog;
    ###input##
    ###############
    #system("python /incam/server/site_data/scripts/sh_script/output_drill/get_erp_tool_info.py $JOB");
#    system("perl /incam/server/site_data/scripts/sh_script/output_drill/show_drl_data.pl");
    #my $get_result = system("perl /incam/server/site_data/scripts/hdi_scr/Output/Laser/show_drl_data.pl");
    #system("perl /incam/server/site_data/scripts/sh1_script/output/show_drl_data.pl");
	#print $get_result . "\n";
	#if ($get_result != 0) {
	#	 $c->Messages('info', "镭射钻带比对ERP未通过");
	#} else {       
		$c->Messages('info', '雷射输出完毕,点击退出');
	#}
    exit;
}

sub clip_laser_layer{
    my ($laser_layer,$clip_layer,$dld_layer) = @_;
    
    # --获取profile坐标值
    $f->INFO(units => 'mm', entity_type => 'step',
         entity_path => "$JOB/$STEP",
         data_type => 'PROF_LIMITS');
    
    my $xmin = $f->{doinfo}{gPROF_LIMITSxmin};
    my $ymin = $f->{doinfo}{gPROF_LIMITSymin};
    my $xmax = $f->{doinfo}{gPROF_LIMITSxmax};
    my $ymax = $f->{doinfo}{gPROF_LIMITSymax};
    
    # my $top_signal_layer = "l1";

	my @trm_layer = split '-', substr($laser_layer, 1,-1);
	my $top_signal_layer = 'l'.$trm_layer[0];
    my $clip_x = $xmin;
    my $clip_y = $ymin;
    $f->INFO(entity_type => 'layer',
        entity_path => "$JOB/$STEP/$top_signal_layer",
        data_type => 'EXISTS');
    if ($f->{doinfo}{gEXISTS} eq "yes") {
        $c->OPEN_STEP($JOB, "$STEP");
        $c->CLEAR_LAYER();
        #$c->DELETE_LAYER($clip_layer);
        $c->AFFECTED_LAYER($top_signal_layer, 'yes');
        $c->FILTER_RESET;
        $c->SELECT_TEXT_ATTR(".fiducial_name","300.trmv");
        $c->FILTER_SELECT;
        
        if ($c->GET_SELECT_COUNT == 1) {
            # --获取分割坐标点
            my $csh_file = "/tmp/info_csh.$$";
            $f->COM("info, out_file=$csh_file, units=mm,args= -t layer -e $JOB/$STEP/$top_signal_layer -d FEATURES -o select");
            open(FILEHANDLE, "$csh_file");
            my @features = <FILEHANDLE>;
            close (FILEHANDLE);
            unlink($csh_file);
            
            foreach my $line(@features){
                if ($line =~ /^#P/) {
                    my @feat = split(" ",$line);
                    $clip_x = $feat[1];
                }
            }
        }
		else{
            if ($clip_mode eq "4分割") {
                $c->Messages("info", "找不到竖方向(r0 .fiducial_name=300.trmv)分割点或其数量不止一个...!程序退出,请检查!");
                exit 0;
            }
        }
        
        if ($clip_mode eq "4分割" or ($clip_x == $xmin and $clip_mode eq "2分割")) {
            if($clip_mode eq "2分割"){
                $clip_x = $xmax;
            }
            $f->COM("sel_clear_feat");
            $c->FILTER_RESET;
            $c->SELECT_TEXT_ATTR(".fiducial_name","300.trmh");
            $c->FILTER_SELECT;
            if ($c->GET_SELECT_COUNT == 1) {
                # --获取分割坐标点
                my $csh_file = "/tmp/info_csh.$$";
                $f->COM("info, out_file=$csh_file, units=mm,args= -t layer -e $JOB/$STEP/$top_signal_layer -d FEATURES -o select");
                open(FILEHANDLE, "$csh_file");
                my @features = <FILEHANDLE>;
                close (FILEHANDLE);
                unlink($csh_file);
                
                foreach my $line(@features){
                    if ($line =~ /^#P/) {
                        my @feat = split(" ",$line);
                        $clip_y = $feat[2];
                    }
                }
            }else{
                $c->Messages("info", "找不到横方向(r0 .fiducial_name=300.trmh)分割点或其数量不止一个...!程序退出,请检查!");
                exit 0; 
            }
        }
    }else{
        $c->Messages("info", "找不到(l1)层线路...!程序退出,请检查!");
        exit 0; 
    }
    
    #############################################自动生成分割层#############################################
    
    # --创建分割层
    $c->CLEAR_LAYER();
    $c->FILTER_RESET;
    $f->INFO(units => 'mm', entity_type => 'layer',
         entity_path => "$JOB/$STEP/$clip_layer",
         data_type => 'EXISTS');

    if ($f->{doinfo}{gEXISTS} eq "yes") {
        $c->DELETE_LAYER($clip_layer);
    }
    
    $f->COM("create_layer,layer=$clip_layer,context=misc,type=drill,polarity=positive,ins_layer=");
    
    
    $f->COM("flatten_layer,source_layer=$laser_layer,target_layer=$clip_layer");
    $c->AFFECTED_LAYER($clip_layer, 'yes');
    
    # --获取symbol大小
    $f->INFO(units => 'mm', entity_type => 'layer',
         entity_path => "$JOB/$STEP/$clip_layer",
         data_type => 'SYMS_HIST');
    
    my @symbol_lsit = @{$f->{doinfo}{gSYMS_HISTsymbol}};
    foreach my $t(@symbol_lsit){
        $t =~ s/^r//;
        # --清理不需要孔(单元内0.076-0.203mm之间,超出不算入镭射钻咀  来源工艺规范周涌提供  2021.11.24)
        if ($t != 520 and ($t < 76 or $t > 385)) {
            my $include_symbol = "r".$t;
            $c->FILTER_RESET;
            $c->FILTER_SET_INCLUDE_SYMS($include_symbol);
            $c->FILTER_SELECT;
            if ($c->GET_SELECT_COUNT > 0) {
                $c->SEL_DELETE;
            }
            print ("\$t $t\n");
        }
    }
    
    $c->AFFECTED_LAYER($clip_layer, 'no');
    
    # --检查dld层
    $f->INFO(units => 'mm', entity_type => 'layer',
         entity_path => "$JOB/$STEP/$dld_layer",
         data_type => 'EXISTS');

    if ($f->{doinfo}{gEXISTS} eq "no") {
        $c->Messages("info", "找不到($dld_layer)层...!程序退出,请检查!");
        exit 0; 
    }else{
        $f->INFO(units => 'mm', entity_type => 'layer',
            entity_path => "$JOB/$STEP/$dld_layer",
            data_type => 'SYMS_HIST');
        my @dld_symbol_list = @{$f->{doinfo}{gSYMS_HISTsymbol}};
        my @dld_symbol_count = @{$f->{doinfo}{gSYMS_HISTpad}};
        
        if (length(@dld_symbol_list) != 1) {
            $c->Messages("info", "检测到($dld_layer)层symbol不止一种类型或层为空..!程序退出,请检查!");
            exit 0;
        }else{
            if ($clip_mode eq "2分割" and $dld_symbol_count[0] != 8) {
                $c->Messages("info", "检测到($dld_layer)层symbol数量不符(2分割=8个)..!程序退出,请检查!");
                exit 0;
            }elsif($clip_mode eq "4分割" and $dld_symbol_count[0] != 16){
                $c->Messages("info", "检测到($dld_layer)层symbol数量不符(4分割=16个)..!程序退出,请检查!");
                exit 0;
            }
        }
    }
    
    $c->AFFECTED_LAYER($dld_layer, 'yes');
    $c->SEL_COPY($clip_layer,"no", 0);
    
    if ($clip_mode eq "4分割") {
        if ($clip_x == $xmin) {
            $c->Messages("info", "4分割竖方向分割点坐标值与profile X方向最小坐标一致..!程序退出,请检查!");
            exit 0; 
        }elsif($clip_y == $ymin){
            $c->Messages("info", "4分割横方向分割点坐标值与profile Y方向最小坐标一致..!程序退出,请检查!");
            exit 0; 
        }
    }else{
        if ($clip_x == $xmin && $clip_y == $ymin) {
            $c->Messages("info", "2分割横、竖方向分割点坐标值与profile 对应(X|Y)方向最小坐标一致..!程序退出,请检查!");
            exit 0; 
        }
    }
    
    $c->CLEAR_LAYER();
    $c->AFFECTED_LAYER($clip_layer, 'yes');
    
    my $clip_count;
    if ($clip_mode eq "2分割") {
        $clip_count = 2;
    }elsif($clip_mode eq "4分割"){
        $clip_count = 4;
    }
    
    # --第一区域坐标
    my $xmin_point = $xmin;
    my $ymin_point = $ymax;
    my $xmax_point = $clip_x;
    my $ymax_point = $clip_y;
    
    my $tool_count = 0;
    for(my $i=1; $i<=$clip_count; $i++){
        if ($i == 2) {
            $xmin_point = $xmin;
            $ymin_point = $ymin;
            $xmax_point = $clip_x;
            $ymax_point = $clip_y;
			if ($clip_mode eq "2分割" and $clip_y == $ymin){
				$xmin_point = $clip_x;
				$ymin_point = $clip_y;
				$xmax_point = $xmax;
				$ymax_point = $ymax;
			}
        }elsif($i == 3) {
            $xmin_point = $clip_x;
            $ymin_point = $clip_y;
            $xmax_point = $xmax;
            $ymax_point = $ymin;
        }elsif($i == 4){
            $xmin_point = $clip_x;
            $ymin_point = $clip_y;
            $xmax_point = $xmax;
            $ymax_point = $ymax;
        }
        
        $c->FILTER_RESET;
        $f->COM("filter_area_strt");
        $f->COM("filter_area_xy,x=$xmin_point,y=$ymin_point");
        $f->COM("filter_area_xy,x=$xmax_point,y=$ymax_point");
        $f->COM("filter_area_end,layer=,filter_name=popup,operation=select,area_type=rectangle,inside_area=yes,intersect_area=no");
        if ($c->GET_SELECT_COUNT > 0) {
            #print("xxxxxxx..............xxxxxxxxxxxxxxxxxxxxx...........xxxxxxxxxxxx\n");
            my $file_path = "/tmp/laser_clip_feature";
            $f->COM("info,args=-t layer -e $JOB/$STEP/$clip_layer -m script -d FEATURES -o select,out_file=$file_path,write_mode=replace,units=mm");
            open(LASERTOOL, "<$file_path");
            my %tool_count;
            while (<LASERTOOL>) {
                next if $_ =~ /^### Layer/i;
                my @info = split(" ",$_);
                if (!exists $tool_count{$info[3]}) {
                    $tool_count{$info[3]} = 1;
                }
            }
            print Dumper (%tool_count);
            close LASERTOOL;
            
            
            foreach my $k(keys %tool_count){
                $tool_count = $tool_count + 1;
            }
            
            if ($tool_count != 3) {
                #$c->Messages("info", "($laser_layer)层分割输出区域($i)钻孔刀序数量应为3,实际为$tool_count,程序不支持没规则分割镭射,请保持每个分割区域刀序为3把刀,请检查并重新输出.");
                #exit 0;
            }
            $c->SEL_RESIZE($i*1000);
        }
    }
    
    $c->AFFECTED_LAYER($clip_layer, 'no');
    
    # --相同钻咀之间差值必须大于或等于4以上，否则分区域会出现刀具少异常问题
    $f->INFO(units => 'mm', entity_type => 'layer',
         entity_path => "$JOB/$STEP/$clip_layer",
         data_type => 'SYMS_HIST',
         options => "break_sr");
    
    my @symbol_list = @{$f->{doinfo}{gSYMS_HISTsymbol}};
    # --返回总刀数
    return scalar(@symbol_list);
    #############################################自动生成分割层#############################################
}

sub chg_hole {
    my ($n, $laser_layer, $head_log, $meter_data, %r515cor) = @_;
    #print $head_log;
    my @file_list = ();
    my $source_file = "$output_path/$JOB.$laser_layer";
    if (-e $source_file) {
        open(STAT, $source_file) or die "can't open file $source_file: $!";
        while (<STAT>) {
            push(@file_list, $_);
        }
        close(STAT);
    }
    
    my $t02exist = "no";
	my $t20exist = "no";
    my $t21exist = "no";
    my $t22exist = "no";
    my $t23exist = "no";
	my @hole_8mil_suffix; #定义8mil 10mil镭射打5遍的是否已分刀 即同时存在0.203 0.204 0.205 0.206 0.207 0.254 0.255 0.256 0.257 0.258
	my @hole_10mil_suffix;
    my %tool = ();
    my %position = ();
    my $body_start = "no";
    my $search_key = "";
    undef @head_file;
    undef @t_list;
    foreach $tmp (@file_list) {
        if ($tmp ne "") {
            if ($tmp eq "T02C0.045\n") {$t02exist = "yes";}
			if ($tmp =~ /(T[01][0-9])(C0.127)/) {$t20exist = "$1";}
			if ($tmp =~ /(T[01][0-9])(C0.14)/) {$t20exist = "$1";}
            if ($tmp =~ /(T[01][0-9])(C0.501)/) {$t21exist = "$1";}
            if ($tmp =~ /(T[01][0-9])(C0.52)/) {$t23exist = "$1";}
            if ($tmp =~ /(T[01][0-9])(C0.515)/) {$t22exist = "$1";}
            if ($tmp =~ /(T\d+)(C[0-9].*)/) {
                $tool{"$1"} = "$2";
                if ("$1" eq "$t23exist") {$tool{"$1"} = "C0.102";}
                push(@t_list, $1);
				
				if ($2 eq 'C0.203' || $2 eq 'C0.204' || $2 eq 'C0.205' || $2 eq 'C0.206' ||$2 eq 'C0.207' ) 
				{
					push(@hole_8mil_suffix,$2);
				}
				if ($2 eq 'C0.254' || $2 eq 'C0.255' || $2 eq 'C0.256' ||$2 eq 'C0.257' ||$2 eq 'C0.258' || $2 eq 'C0.259' ) 
				{
					push(@hole_10mil_suffix,$2);
				}

            }
            if ($tmp eq "%\n") {$body_start = "yes";}
            if ($body_start eq "yes") {
                if ($tmp =~ /^T[01][0-9]\n$/) {
                    $search_key = $tmp;
                    chomp $search_key;
                }
                elsif ($tmp eq "M30\n") {

                }
                else {
                    if (exists $tool{"$search_key"}) {push(@{$position{"$search_key"}}, $tmp);}
                }
            }
            else {
                push(@head_file, $tmp);
            }
        }
    }
	
	if ($t20exist ne "no"){
		$f->INFO(units  => 'mm', angle_direction => 'ccw', entity_type => 'step',
			entity_path => "$JOB/$STEP",
			data_type   => 'SR');
		my $dcoupon_exists_127 = "no";
		my @gSRstep = @{$f->{doinfo}{gSRstep}}; 
		for (my $i = 0; $i <= $#gSRstep; $i++) {
			if ($gSRstep[$i] =~ /d-coupon/ or $gSRstep[$i] =~ /edit-d-coupon/) {
				my $csh_file = "$tmpPath/info_csh.$$";
				$f->COM("info, out_file=$csh_file, units=mm,args=  -t layer -e  $JOB/$gSRstep[$i]/$laser_layer -d FEATURES -o break_sr");
				my @getlayerTar = $c->dealwithFeatureFile($csh_file);
				unlink($csh_file);
				for (my $i = 0; $i <= $#getlayerTar; $i++) {
					if ($getlayerTar[$i]{symbol} eq 'r127' or $getlayerTar[$i]{symbol} eq 'r140') {
						$dcoupon_exists_127 = "yes";
					}
				}
			}
		}
		#$f->PAUSE("$t20exist   $dcoupon_exists_127");
		if ($dcoupon_exists_127 eq "no"){
			$t20exist = "no";
		}
	}
    
    # 判断T02 0.045mm的钻孔数量是否为4 Add by Song 2019.12.25
    #  --分割输出时，不再检测
    if ($t02exist eq "yes" and $clip_mode eq "不分割") {
        if (scalar(@{$position{'T02'}}) != "4") {
            my $tmp_num = scalar(@{$position{'T02'}});
            $c->Messages("info", "$laser_layer 中0.045mm钻孔数量应为4,现在为$tmp_num,\n请检查是否重孔,并重新输出.");
            return "T02numberError";
        }
    }

    print Dumper (\%tool);
    my @T = sort keys(%tool);
    ##T02非0.045mm DLD标靶，则所有T向后移位，
    my %t_chg = ();

	#10mil的刀序重排 10mil孔与其它孔径存在时，刀序需要变成T15,T16,T17,T18,T19 20221214 by lyh
	# 按新工艺文件要求 10mil孔固定15-19 20240111 by lyh
	# for $k (keys(%tool)) {			
		# for (my $i=0; $i<=$#hole_10mil_suffix; $i++) {
			##if ( $laser_symbol_size_num{$laser_layer} >= 2 and $#hole_10mil_suffix > 1 and $tool{$k} eq $hole_10mil_suffix[$i]) {	
			# if ($laser_drill_five_times_info{$laser_layer} eq "yes" and $tool{$k} eq $hole_10mil_suffix[$i]) {	
				# $aa = 15+$i;
				# $t_chg{"$k"} = "T$aa";
			# }
		# }			
	# }
	
	#按新工艺文件要求 8mil的刀序重排 刀序需要变成T5,T6,T7,T8,T9 20240116 by lyh
	# for $k (keys(%tool)) {			
		# for (my $i=0; $i<=$#hole_8mil_suffix; $i++) {	
			# if ($laser_drill_five_times_info{$laser_layer} eq "yes"  and $tool{$k} eq $hole_8mil_suffix[$i]) {	
				# $aa = 5+$i;
				
				# $t_chg{"$k"} = "T0$aa";
			# }
		# }			
	# }
	
    for $k (keys(%tool)) {
        if ($k eq "$t20exist") {
            $t_chg{"$k"} = "T20"
        }	
        if ($k eq "$t21exist") {
            $t_chg{"$k"} = "T21"
        }
        elsif ($k eq "$t22exist") {
            $t_chg{"$k"} = "T22"
        }
        elsif ($k eq "$t23exist") {
            $t_chg{"$k"} = "T23"
        }
        else {
            #if ($t02exist eq "no") {
            # --当不是输出core层S面时,重新排刀序,即:C面为T03,S面为T02  AresHe 2021.11.9
            if ($t02exist eq "no") {
				if ($n == 1){
					##not include T01
					if ($k =~ /T(0)([2-9])$/) {
						$aa = $2 + 1;
						if ($aa >= 10) {
							$t_chg{"$k"} = "T$aa";
						}
						else {
							$t_chg{"$k"} = "T0$aa";
						}
					}
					elsif ($k =~ /T([1-9])([0-9])$/) {
						$aa = $1 . $2 + 1;
						$t_chg{"$k"} = "T$aa"
					}
				}
				
				#芯板反面的按T02 T05 20240131 BY lyh
				if ($n == 2){
					if ($k eq "T02") {	
						$t_chg{"$k"} = "T02";
					}
					if ($k eq "T03") {	
						$t_chg{"$k"} = "T05";
					}
				}
				
            }
            elsif ($t02exist eq "yes") {
                if ($k eq "T02") {$t_chg{"$k"} = "T500";}
            }
        }
    }
	
    my %t21_cor = ();
    if ($t21exist ne "no") {
        $search_key = $t21exist;
        chomp $search_key;
        foreach $tps (@{$position{$search_key}}) {
            ##change trail cor to none cor ###
            chomp($tps);
            if ($tps =~ /X-?(\d+)Y-?(\d+)/) {
                if (length($1) < 6) {
                    $v = 0 x (6 - length($1));
                    $plus_num = "1" . "$v";
                    $showx = $1 * $plus_num;
                }
                else {
                    $showx = $1
                }
                if (length($2) < 6) {
                    $v = 0 x (6 - length($2));
                    $plus_num = "1" . "$v";
                    $showy = $2 * $plus_num;
                }
                else {
                    $showy = $2
                }
                if ($showy > $sry_max - 20*1000) {
                    if (exists $t21_cor{1}) {
                        $t21_cor{2} = $tps . "\n";
                    }
                    else {
                        $t21_cor{1} = $tps . "\n";
                    }
                    #} elsif ( $srx_min < $showx && $showx < $srx_max && $showy < $sry_min )   {
                }
                elsif ($showx > $srx_max - 20*1000 && $sry_min < $showy && $showy < $sry_max) {
                    $t21_cor{4} = $tps . "\n";
                }
                elsif ($showy < $sry_min + 20*1000) {
                    $t21_cor{3} = $tps . "\n";
                }
                else {
                    $t21_cor{5} = $tps . "\n";
                }
            }
            else {
                print "Error!";
            }
        }
    }
    # 增加T21数量为4的检测，如果不为4，程序退出
    my $t21count = keys %t21_cor;
    if ($t21count != "4") {
        $c->Messages("info", "$laser_layer 中0.501mm钻孔数量归类后应为4,现在为$t21count,\n请检查拼入的单元名称是否为set或edit,并重新输出.");
        return "T21numberError";
    } elsif (exists $t21_cor{5}) {
		$c->Messages("info", "$laser_layer 中0.501mm钻孔坐标：$t21_cor{5} 无法判断在哪个留边,\n请检查拼入的单元名称是否为set或edit,并重新输出.");
        return "T21numberError";
	}
	if ($t21exist ne "no") {
		my $t21_count = scalar(@{$position{$search_key}});
		if ($t21_count !=4 ){
			$c->Messages("info", "$laser_layer 中0.501mm钻孔数量归类后应为4,现在为$t21_count,\n请检查r501数量是否异常,并重新输出.");
			return "T21numberError";
		}
	}

    #@data2 =%t21_cor;
    #print Dumper(%t21_cor);
    our $des_file = "$output_path/$JOB.$laser_layer.write";
    if (open(SESAME, ">$des_file") or die("$!")) {
        #print SESAME "$head_log\n";
        print SESAME "M100($meter_data)\n";
        foreach $tmp (@head_file) {
            chomp $tmp;
            if ($tmp =~ /(T[01][0-9])(C.*)/) {
                if (exists $t_chg{"$1"}) {
                    if ($t_chg{"$1"} ne 'T23') {
                        print SESAME "$t_chg{$1}$2\n";
                    }
                    else {
                        print SESAME "$t_chg{$1}C0.102\n";
                    }
                }
                else {
                    print SESAME "$tmp\n";
                } ###change tool size ###
            }
            elsif ($tmp =~ /M48/) {
                print SESAME "M48\n$head_log\n";
            }
            else {
                print SESAME "$tmp\n";
            }
        }
        
        print SESAME "%\n"; #写入百分号#
        foreach $tmp (@t_list) {
            #next if 1 > 0;
            if (exists $t_chg{"$tmp"}) {
                $real_t = $t_chg{$tmp};
                
                # --判断资料是否分割
                if ($clip_mode eq "不分割") {
                    print SESAME "$t_chg{$tmp}\n";
                #}elsif($real_t ne "T500" and $real_t ne "T03" and $real_t ne "T23") {
                }elsif($real_t !~ /T500|T03|T04|T05|T06|T23/){
                    # --排除t03-t06刀,支持同时四把刀
                    print SESAME "$t_chg{$tmp}\n";
                }elsif($real_t eq "T500"){
                    ##########################读取资料、分割资料并合并##########################
                    my $clip_layer_file = "$output_path/$JOB.$laser_layer"."-fg";
					
					#增加 按区域来分割 加打五遍排刀逻辑 20240105 by lyh
					my $five_times="no";		
				
					if ($laser_drill_five_times_info{$laser_layer} eq "yes"){
						# $five_times="yes";
						$five_times= $five_times_send_drill{$laser_layer};
					}	
					# system("python $cur_script_dir/calc_laser_fg_coordinate.py $des_file $clip_layer_file $five_times $laser_symbol_size_num{$laser_layer}");	
					system("python $cur_script_dir/calc_laser_fg_coordinate_new_test.py $des_file $clip_layer_file $five_times $laser_symbol_size_num{$laser_layer}");					
					close(SESAME);
					open(SESAME, ">>$des_file") or die("$!");

                    if (-f $clip_layer_file) {
						
						$c->Messages("info", "$laser_layer 分割坐标排刀异常，请反馈程序工程师处理.");
						return "fg_numberError";
						
                        open(CLIPFILE, "<$clip_layer_file");
                        my @clip_data = <CLIPFILE>;
                        close CLIPFILE;
                        unlink "$clip_layer_file";
                        
                        if (@clip_data) {
                            my $split_count = 2;
                            if ($clip_mode eq "4分割") {
                                $split_count = 4;
                            }
                            
                            # --获取每个区域刀具数据
                            my $area_count = $clip_drill_counnt / $split_count;
                            
                            # --每个区域每把刀数量
                            my $array_tool_count = $clip_drill_counnt / $area_count;
                            my @array1 = ();
                            my @array2 = ();
                            my @array3 = ();
                            my @array4 = ();
                            
                            my $t1_area = 3;
                            my $t2_area = 3;
                            my $t3_area = 3;
                            my $t4_area = 3;
                            
                            my $flag = "start";
                            my $split_tool;
                            
                            for (my $i=0; $i<=$#clip_data; $i++){
                                chomp $clip_data[$i];
                                if( $flag eq "start" ){
                                    if( $clip_data[$i] eq "M48" ){
                                        $flag = "overhead";
                                    }
                                }
                                elsif( $flag eq "overhead" ){
                                    if( $clip_data[$i] =~ /^T01C/i ){
                                        $flag = "head";
                                    }
                                }
                                elsif( $flag eq "head" ){
                                    if( $clip_data[$i] !~ /^T\d+/i ){
                                        $flag = "neck";
                                    }
                                }
                                elsif( $flag eq "neck" ){
                                    if( $clip_data[$i] =~ /^T01/i ){
                                        $flag = "body";
                                    }
                                }
                                elsif( $flag eq "body" ){
                                    if( $clip_data[$i] =~ /^M30$/i ){
                                        $flag = "end";
                                    }
                                }
                                
                                if ($flag eq "body") {
                                    if ($clip_data[$i] =~ /^T(\d+)/i) {
                                        $split_tool = $1 * 1;
                                    }
                                    
                                    if ($split_tool % $split_count == 0) {
                                        if ($split_tool > $clip_drill_counnt - $array_tool_count) {
                                            # --最后一把刀为T23
                                            if ($clip_data[$i] =~ /^T(\d+)$/) {
                                                push @array4,"T23";
                                            }else{
                                                push @array4,$clip_data[$i];
                                            }
                                        }elsif($split_tool > $clip_drill_counnt - $array_tool_count * 2 and $split_tool <= $clip_drill_counnt - $array_tool_count){
                                            # --倒数第二把刀为T500
                                            if ($clip_data[$i] =~ /^T(\d+)$/) {
                                                push @array4,"T500";
                                            }else{
                                                push @array4,$clip_data[$i];
                                            }
                                        }else{
                                            if ($clip_data[$i] =~ /^T(\d+)$/) {
                                                my $new_tool = "T$t4_area";
                                                if ($t1_area <= 9) {
                                                    $new_tool = "T0$t4_area";
                                                }
                                                push @array4,$new_tool;
                                                $t4_area ++;
                                            }else{
                                                push @array4,$clip_data[$i];
                                            }
                                        }
                                    }elsif($split_tool % $split_count == 1){
                                        if ($split_tool > $clip_drill_counnt - $array_tool_count) {
                                            # --最后一把刀为T23
                                            if ($clip_data[$i] =~ /^T(\d+)$/) {
                                                push @array1,"T23";
                                            }else{
                                                push @array1,$clip_data[$i];
                                            }
                                        }elsif($split_tool > $clip_drill_counnt - $array_tool_count * 2 and $split_tool <= $clip_drill_counnt - $array_tool_count){
                                            # --倒数第二把刀为T500
                                            if ($clip_data[$i] =~ /^T(\d+)$/) {
                                                push @array1,"T500";
                                            }else{
                                                push @array1,$clip_data[$i];
                                            }
                                        }else{
                                            if ($clip_data[$i] =~ /^T(\d+)$/) {
                                                
                                                my $new_tool = "T$t1_area";
                                                if ($t1_area <= 9) {
                                                    $new_tool = "T0$t1_area";
                                                }
                                                push @array1,$new_tool;
                                                $t1_area ++;
                                            }else{
                                                push @array1,$clip_data[$i];
                                            }
                                        }
                                    }elsif($split_tool % $split_count == 2){
                                        if ($split_tool > $clip_drill_counnt - $array_tool_count) {
                                            # --最后一把刀为T23
                                            if ($clip_data[$i] =~ /^T(\d+)$/) {
                                                push @array2,"T23";
                                            }else{
                                                push @array2,$clip_data[$i];
                                            }
                                        }elsif($split_tool > $clip_drill_counnt - $array_tool_count * 2 and $split_tool <= $clip_drill_counnt - $array_tool_count){
                                            # --倒数第二把刀为T500
                                            if ($clip_data[$i] =~ /^T(\d+)$/) {
                                                push @array2,"T500";
                                            }else{
                                                push @array2,$clip_data[$i];
                                            }
                                        }else{
                                            if ($clip_data[$i] =~ /^T(\d+)$/) {
                                                
                                                my $new_tool = "T$t2_area";
                                                if ($t1_area <= 9) {
                                                    $new_tool = "T0$t2_area";
                                                }
                                                push @array2,$new_tool;
                                                $t2_area ++;
                                            }else{
                                                push @array2,$clip_data[$i];
                                            }
                                        }
                                    }elsif($split_tool % $split_count == 3){
                                        if ($split_tool > $clip_drill_counnt - $array_tool_count) {
                                            # --最后一把刀为T23
                                            if ($clip_data[$i] =~ /^T(\d+)$/) {
                                                push @array3,"T23";
                                            }else{
                                                push @array3,$clip_data[$i];
                                            }
                                        }elsif($split_tool > $clip_drill_counnt - $array_tool_count * 2 and $split_tool <= $clip_drill_counnt - $array_tool_count){
                                            # --倒数第二把刀为T500
                                            if ($clip_data[$i] =~ /^T(\d+)$/) {
                                                push @array3,"T500";
                                            }else{
                                                push @array3,$clip_data[$i];
                                            }
                                        }else{
                                            if ($clip_data[$i] =~ /^T(\d+)$/) {
                                                my $new_tool = "T$t3_area";
                                                if ($t1_area <= 9) {
                                                    $new_tool = "T0$t3_area";
                                                }
                                                push @array3,$new_tool;
                                                $t3_area ++;
                                            }else{
                                                push @array3,$clip_data[$i];
                                            }
                                        }
                                    }
                                }
                            }
                            
                            # --钻孔刀序排序(T500、T03、T23)
                            if (@array1) {
                                @array1 = &auto_sort(@array1);
                            }
                            
                            if (@array2) {
                                @array2 = &auto_sort(@array2);
                            }
                            
                            if (@array3) {
                                @array3 = &auto_sort(@array3);
                            }
                            
                            if (@array4) {
                                @array4 = &auto_sort(@array4);
                            }
                            
                            my @array_list = (@array1,@array2,@array3,@array4);
                            
                            # --所有内靶坐标写入文件
                            my $tool_5_status;
                            for (my $i=0; $i<=$#array_list; $i++){
                                if (!$tool_5_status and $array_list[$i] eq "T500") {
                                    print SESAME "T10\n";
                                    print SESAME "$array_list[$i]\n";
                                    $tool_5_status = "start";
                                    for(my $h=1;$h<=4; $h++){
                                        print SESAME "$array_list[$i + $h]\n";
                                    }
                                }elsif($array_list[$i] eq "T500"){
                                    for(my $h=1;$h<=4; $h++){
                                        print SESAME "$array_list[$i + $h]\n";
                                    }
                                }
                            }
                            
                            # --所有数据写入文本
                            my $tool_5_count;
                            for (my $i=0; $i<=$#array_list; $i++){
                                if ($array_list[$i] eq "T500") {
                                    print SESAME "\n";
                                    # --t500 总共4个坐标
                                    $tool_5_count = $i + 4;
                                }elsif($i <= $tool_5_count){
                                    # --最后一个坐标使用G83,其余坐标使用G82
                                    if ($i == $tool_5_count) {
                                        print SESAME "G83$array_list[$i]\n";
                                    }else{
                                        print SESAME "G82$array_list[$i]\n";
                                    }
                                }else{
                                    print SESAME "$array_list[$i]\n";
                                }
                            }
                        }
                    }else{
                        
                    }
                    ##########################读取资料、分割资料并合并##########################
                }
            }
            else {
                $real_t = $tmp;
                #T01C3.175
                if ($tmp eq "T01" && $tool{"$tmp"} eq "C3.175" && scalar(@{$position{$tmp}}) == "4") {
                    #print SESAME "T3000\n";
                }
                else {
                    if ($clip_mode eq "不分割") {
                        print SESAME "$tmp\n";
                    }
                }
            }
            
            my $tp1 = 1;
            my $tp2 = 1;
            my $tp4 = 1;
            my $tp5 = 1;
            foreach $tps (@{$position{$tmp}}) {
                chomp $tps;
                ##T01C3.175 add 3 G82 1 G83 before cor #
                if ($tmp eq "T01" && $tool{"$tmp"} eq "C3.175" && scalar(@{$position{$tmp}}) == "4") {
                    if ($tp1 < 4) {
                        print SESAME "G82$tps\n";
                        $tp1++;
                    }
                    elsif ($tp1 == 4) {
                        print SESAME "G83$tps\n";
                        $tp1++;
                    }
                    else {
                        print SESAME "$tps\n";
                    }
                }
                elsif ($real_t eq "T500" && $tool{"$tmp"} eq "C0.045" && scalar(@{$position{$tmp}}) == "4") {
                    if ($clip_mode eq "不分割") {
                        if ($tp2 < 4) {
                            print SESAME "G82$tps\n";
                            $tp2++;
                        }
                        elsif ($tp2 == 4) {
                            print SESAME "G83$tps\n";
                            $tp2++;
                        }
                        else {
                            print SESAME "$tps\n";
                        }
                    }
                }
                elsif ($real_t eq "T21" && $tool{"$tmp"} eq "C0.501" && scalar(@{$position{$tmp}}) == "4") {
                    if ($tp4 == 1) {print SESAME 'M97,$MACHINE&,&$STAGE' . "\n";}
                    if ($tp4 == 2) {print SESAME 'M97,$DATE&,&$TIME' . "\n";}
                    if ($tp4 == 3) {print SESAME 'M97,$LOT&,&$NAME-PRG' . "\n";}
                    if ($tp4 == 4) {print SESAME 'M98,$SINSYUKU' . "\n";}
                    print SESAME "$t21_cor{$tp4}";
                    $tp4++;
                }
                elsif ($real_t eq "T22" && $tool{"$tmp"} eq "C0.515") {
                    if ($tp5 == 1) {
                        foreach $lot_cc (@{$r515cor{"C0.515"}}) {
                            print SESAME $lot_cc;
                        }
                    }
                    $tp5++;
                }
                else {
                    if ($clip_mode eq "不分割") {
                        print SESAME "$tps\n";
                    }
                }
            }
        }                     ###write all tool position ###
        print SESAME "M30\n"; #写入end号#
        close(SESAME);
    }	

	
	if ( $clip_mode eq "不分割"){
		my $five_times_str = 'no';
		if ($laser_drill_five_times_info{$laser_layer} eq "yes"){
			$five_times_str= $five_times_send_drill{$laser_layer};
		}	
	
		system("python $cur_script_dir/calc_laser_only_five_times_coordinate_new_test_20241214zltest.py $des_file $output_path/$JOB.$laser_layer $five_times_str");
	}
    
    if ($clip_mode ne "不分割") {
        # --设定分割资料回读文件  AresHe 2021.10.11
        our $reread_file = "$output_path/$JOB.$laser_layer.write.reread";
        
        if (open(REREAD, "<$des_file") or die("$!")) {
            my @REREAD_DATA = <REREAD>;
            close(REREAD);
            
            
            open(WRITEFILE, ">$reread_file");
            my $flag = 'neck';
            foreach my $line(@REREAD_DATA){
                if ($flag eq 'neck') {
                    if ($line =~ /[G82|G83](X(-?)(\d+)Y(-?)(\d+))/) {
                        $flag = 'first';
                    }
                }elsif($flag eq 'first'){
                    if ($line =~ /^T(\d+)/) {
                        $flag = 'delete';
                    }
                }elsif($flag eq 'delete'){
                    if ($line !~ /\w/) {
                        $flag = 'change';
                    }
                }elsif($flag eq 'change'){
                    if ($line =~ /T21/) {
                        $flag = 'orig';
                    }
                }
                
                if($flag eq 'neck') {
                    if ($line =~ /\%/) {
                        print WRITEFILE $line;
                        print WRITEFILE "T01\n";
                    }else{
                        print WRITEFILE $line;
                    }
                }elsif($flag eq 'first'){
                    if ($line =~ /[G82|G83](X(-?)(\d+)Y(-?)(\d+))/) {
                        print WRITEFILE "$1\n";
                    }
                }elsif($flag eq 'change'){
                    if ($line =~ /[G82|G83](X(-?)(\d+)Y(-?)(\d+))/) {
                        print WRITEFILE "$1\n";
                    }elsif($line !~ /\w/){
                        print WRITEFILE "T500\n";
                    }else{
                        print WRITEFILE $line;
                    }
                }elsif($flag eq 'orig'){
                    print WRITEFILE $line;
                }
            }
            close(WRITEFILE);
        }
    }
}

sub modify_laser_five_times{
	#修改8mil 10mil镭射打5遍
    my ($laser_layer, $head_log, $meter_data ,$source_file) = @_;
    my @file_list = ();
    if (-e $source_file) {
        open(STAT, $source_file) or die "can't open file $source_file: $!";
        while (<STAT>) {
            push(@file_list, $_);
        }
        close(STAT);
    }
    
	my $hole_8mil_t=""; 
	my $hole_10mil_t="";
    my %tool = ();
    my %position = ();
    my $body_start = "no";
    my $search_key = "";
	my @T01_body;
    undef @head_file;
    undef @t_list;
    foreach $tmp (@file_list) {
        if ($tmp ne "") {
            if ($tmp =~ /(T\d+)(C[0-9].*)/) {
                $tool{"$1"} = "$2";
                push(@t_list, $1);		
				#有时合并会多加1um				
				if ($2 eq 'C0.203' || $2 eq 'C0.204') {
					$hole_8mil_t = $1;
					if ($2 eq 'C0.203'){
						$tool{"$1"."_2"} = "C0.204";
						$tool{"$1"."_3"} = "C0.205";
						$tool{"$1"."_4"} = "C0.206";
						$tool{"$1"."_5"} = "C0.207";
					}else{
						$tool{"$1"."_2"} = "C0.205";
						$tool{"$1"."_3"} = "C0.206";
						$tool{"$1"."_4"} = "C0.207";
						$tool{"$1"."_5"} = "C0.208";
					}
					push(@t_list, "$1"."_2");
					push(@t_list, "$1"."_3");	
					push(@t_list, "$1"."_4");	
					push(@t_list, "$1"."_5");
				}
				#有时合并会多加1um
				if ($2 eq 'C0.254' || $2 eq 'C0.255' ) {
					$hole_10mil_t = $1;
					if ($2 eq 'C0.254'){
						$tool{"$1"."_2"} = "C0.255";
						$tool{"$1"."_3"} = "C0.256";
						$tool{"$1"."_4"} = "C0.257";
						$tool{"$1"."_5"} = "C0.258";
					}else{
						$tool{"$1"."_2"} = "C0.256";
						$tool{"$1"."_3"} = "C0.257";
						$tool{"$1"."_4"} = "C0.258";
						$tool{"$1"."_5"} = "C0.259";
					}
					push(@t_list, "$1"."_2");
					push(@t_list, "$1"."_3");	
					push(@t_list, "$1"."_4");	
					push(@t_list, "$1"."_5");
				}

            }
            if ($tmp eq "%\n") {$body_start = "yes";}
            if ($body_start eq "yes") {
                if ($tmp =~ /^T(\d+)\n$/) {
                    $search_key = $tmp;
                    chomp $search_key;
                }
                elsif ($tmp eq "M30\n") {

                }
                else {
					if ($search_key eq "") {push(@T01_body, $tmp);}
                    if (exists $tool{"$search_key"}) {push(@{$position{"$search_key"}}, $tmp);}
                }
            }
            else {
				# print "--->,$hole_8mil_t";
				# print Dumper (\%tool);
				push(@head_file, $tmp);
				if ( $hole_8mil_t ne "" and $tmp =~ /$hole_8mil_t/){					
					push(@head_file, $hole_8mil_t."_2".$tool{"$hole_8mil_t"."_2"});
					push(@head_file, $hole_8mil_t."_3".$tool{"$hole_8mil_t"."_3"});
					push(@head_file, $hole_8mil_t."_4".$tool{"$hole_8mil_t"."_4"});
					push(@head_file, $hole_8mil_t."_5".$tool{"$hole_8mil_t"."_5"});				
				} elsif ( $hole_10mil_t ne "" and  $tmp =~ /$hole_10mil_t/){
					push(@head_file, $hole_10mil_t."_2".$tool{"$hole_10mil_t"."_2"});
					push(@head_file, $hole_10mil_t."_3".$tool{"$hole_10mil_t"."_3"});
					push(@head_file, $hole_10mil_t."_4".$tool{"$hole_10mil_t"."_4"});
					push(@head_file, $hole_10mil_t."_5".$tool{"$hole_10mil_t"."_5"});
				}
            }
        }
    }  
	
    my @T = sort keys(%tool);
    my %t_chg = ();
	my %exists_change_keys = ();
	my $aa;
    for $k (keys(%tool)) {
		if ( $laser_symbol_size_num{$laser_layer} >= 2 and $hole_10mil_t ne "" and $k =~ /$hole_10mil_t/) {
			if ($k eq $hole_10mil_t) {
				$t_chg{"$k"} = "T15";
				$exists_change_keys{"T15"}="exists";
			}
			elsif ($k =~ /(T\d+\_)(\d)/){
				$aa = 15+$2-1;
				$t_chg{"$k"} = "T$aa";
				$exists_change_keys{"T$aa"}="exists";
			}
		 }else{
			if ($hole_8mil_t ne "" and $k =~ /$hole_8mil_t/) {
				if ($k =~ /T(\d+)\_(\d)/){				
					$aa = $1*1+$2-1;
					if ( $aa < 10){
						$t_chg{"$k"} = "T0$aa";
						$exists_change_keys{"T0$aa"}="exists";
					}else{
						$t_chg{"$k"} = "T$aa";
						$exists_change_keys{"T$aa"}="exists";
					}
				}
			}
			elsif ($hole_10mil_t ne "" and $k =~ /$hole_10mil_t/) {
				if ($k =~ /T(\d+)\_(\d)/){				
					$aa = $1*1+$2-1;
					if ( $aa < 10){
						$t_chg{"$k"} = "T0$aa";
						$exists_change_keys{"T0$aa"}="exists";
					}else{
						$t_chg{"$k"} = "T$aa";
						$exists_change_keys{"T$aa"}="exists";
					}
				}
			}
			else{		
				next;
				#此部分单独循环 避免字典是乱序 导致这部分刀序在前面运行 没有改变重复刀序
				# if ($k =~ /T(\d+)/ and exists $t_chg{$k}){
					# for (my $i = 1; $i <= 5; $i++) {
						# $aa = $1*1+$i;						
						# if ( !exists $t_chg{$aa}) {
							# if ( $aa < 10){
								# $t_chg{"$k"} = "T0$aa";
							# }else{
								# $t_chg{"$k"} = "T$aa";
							# }
							# last;
						# }
					# }
				# }
			}
		}
    }
	
	#此处再循环一遍 以免刀重复 20230318 by lyh
	for $k (keys(%tool)) {
		if ($k =~ /T(\d+)$/ and exists $exists_change_keys{$k}){
			for (my $i = 1; $i <= 5; $i++) {
				$aa = $1*1+$i;						
				if ( !exists $exists_change_keys{"T0$aa"} and !exists $exists_change_keys{"T$aa"}) {
					if ( $aa < 10){
						$t_chg{"$k"} = "T0$aa";
						$exists_change_keys{"T0$aa"}="exists";
					}else{
						$t_chg{"$k"} = "T$aa";
						$exists_change_keys{"T$aa"}="exists";
					}
					last;
				}
			}
		}		
	}
	
	my $real_t;
	#print Dumper (\%position);
	# print @t_list;
	# print "------------->$hole_8mil_t,,";
    if (open(SESAME, ">$source_file") or die("$!")) {
        foreach $tmp (@head_file) {
            chomp $tmp;
            if ($tmp =~ /(T\d+)(C.*)/) {
                if (exists $t_chg{"$1"}) {
                    print SESAME "$t_chg{$1}$2\n";
                }
                else {
                    print SESAME "$tmp\n";
                } ###change tool size ###
            }
            else {
				if ($tmp =~ /(T\d+\_\d)(C.*)/) {
					if (exists $t_chg{"$1"}) {
						print SESAME "$t_chg{$1}$2\n";
					}
					else {
						print SESAME "$tmp\n";
					} ###change tool size ###
				} else {
					print SESAME "$tmp\n";
				}
            }
        }

        #print SESAME "%\n"; #写入百分号#
        foreach $tmp (@t_list) {
            if (exists $t_chg{"$tmp"}) {
                $real_t = $t_chg{$tmp};                
            }
            else {
                $real_t = $tmp;
            }
			
			if ( $tmp eq 'T01' ){
				foreach $t01_info (@T01_body) {
					chomp $t01_info;
					print SESAME "$t01_info\n";
				}
				next;
			}
			
            print SESAME "$real_t\n";
			if ( $hole_8mil_t ne "" and $tmp =~ /$hole_8mil_t/ ){$tmp=$hole_8mil_t;}
			if ( $hole_10mil_t ne "" and  $tmp =~ /$hole_10mil_t/){$tmp=$hole_10mil_t;}
            foreach $tps (@{$position{$tmp}}) {
                chomp $tps;
                print SESAME "$tps\n";
            }
        }                     ###write all tool position ###
        print SESAME "M30\n"; #写入end号#
        close(SESAME);
    }
}



sub auto_sort{
    my @array = @_;
    
    my @array1;
    my @array2;
    my @array3;
    
    my $selete_status;
    foreach my $line(@array){
        if ($line =~ /T/) {
            print ("\$line $line\n");
        }
        
        if ($line =~ /T500/) {
            $selete_status = "T500";
        }elsif ($line =~ /T23/){
            $selete_status = "T23";
        }elsif ($line =~ /T(\d+)/){
            $selete_status = "normal";
        }
        
        # T500 T03 T23
        if ($selete_status eq "T500") {
            push @array1,$line;
        }elsif($selete_status eq "T23"){
            push @array3,$line;
        }elsif($selete_status eq "normal"){
            push @array2,$line;
        }
    }
    #$f->PAUSE("xxx");
    my @array_new = (@array1,@array2,@array3);
    return (@array_new);
}

sub ret_int {
    my @src_list = @_;
    my @relist;
    for (my $i = 0; $i <= $#src_list; $i++) {
        $kk = int(($src_list[$i] + 0.25) / 0.5) * 0.5;
        push(@relist, $kk);
    }
    return (@relist);
}

#sub end_mess {
#    $mw->Dialog(-title  => 'Dialog',
#        -text           => "雷射输出完毕，点击退出",
#        -default_button => 'Ok',
#        -buttons        => [ 'Ok' ],
#        -bitmap         => 'error')->Show();
#}

sub deal_515_laser {
    my ($dis_lay) = @_;
    my $r515exist = &checkr515exist($dis_lay);

    my $LotDirec;
    if (exists $r515CheckData{"$dis_lay"}) {
        #code
        $LotDirec = $r515CheckData{"$dis_lay"}{'LotDirec'};
    }
    else {
        $c->Messages("info", "无法获取lot号方向,\n程序退出");
        exit 0;
    }
    if ($scale_position eq "中心") {
        $scale_center_x = $op_x_center;
        $scale_center_y = $op_y_center;
    }
    else {
        $scale_center_x = 0;
        $scale_center_y = 0;
    }
    $f->COM("top_tab,tab=Matrix");
    $f->AUX("set_step,name=$step_name");
    $f->AUX("set_group,group=$f->{COMANS}");
    my $r515laser = 'r515' . $dis_lay;
    my $ncsetlot = 'lot' . $dis_lay;
    if ($r515exist eq "yes") {
        $f->COM("matrix_layer_type,job=$JOB,matrix=matrix,layer=$r515laser,type=drill");
        $f->COM("set_subsystem,name=Nc-Manager");
        $f->COM("nc_set_current,job=$JOB,step=$step_name,layer=,ncset=");
        $f->VOF;
        $f->COM("nc_delete,layer=$r515laser,ncset=$ncsetlot");
        $f->VON;
        $f->COM("nc_create,ncset=$ncsetlot,device=misumi,lyrs=$r515laser,thickness=0");
        $f->COM("nc_set_advanced_params,layer=$r515laser,ncset=$ncsetlot,parameters=(rout_arc_as_ij=no)(out_exc_old_sr_syntax=no)");
        $f->COM("nc_set_current,job=$JOB,step=$step_name,layer=$r515laser,ncset=$ncsetlot");
        #$f->COM("show_tab,tab=NC Parameters Page,show=yes");
        #$f->COM("top_tab,tab=NC Parameters Page");
        #$f->COM("open_sets_manager,test_current=no");
        $f->COM("nc_set_file_params,output_path=$output_path,output_name=$JOB.$r515laser,zeroes=trailing,units=mm,tool_units=mm,nf1=3,nf2=3,decimal=no,modal_coords=no,single_sr=yes,sr_zero_set=no,repetitions=sr,incremental=no,ext_layer=drl2rt,sr_zero_layer=,ccw=no,short_lines=none,allow_no_chain_f=no,no_chain_as_slot=no,keep_table_order=no,max_arc_angle=0,comp_short_slot=no,gscale_file_name=,layer_datum=bottom_left,gscle_align_angle=0,gscl_offset_x=0,gscl_offset_y=0");
        if (${$hash{$dis_lay}}[4] eq 'no') {
            $ver = 1;
        }
        elsif (${$hash{$dis_lay}}[4] eq 'yes') {
            $ver = 7;
        }
        my $scale_x = ${$hash{$dis_lay}}[2];
        my $scale_y = ${$hash{$dis_lay}}[3];
        $f->COM("nc_register,angle=0,xoff=0,yoff=0,version=$ver,xorigin=0,yorigin=0,xscale=$scale_x,yscale=$scale_y,xscale_o=$scale_center_x,yscale_o=$scale_center_y,xmirror=no,ymirror=no");
        $f->COM("nc_set_optim,optimize=yes,iterations=5,reduction_percent=1,cool_spread=0,break_sr=no,xspeed=2540,yspeed=2540,diag_mode=45ort");
        # === add by Song for test 2020.06.10 镭射Lot号输出过程中会后台报错，前台没有任何提示===
        # === 测试获取Status无效 ===

        $f->COM("nc_cre_output,layer=$r515laser,ncset=$ncsetlot");
        my $lot_op_status = $f->{STATUS};
        my $lot_op_comans = $f->{COMANS};


        # === 考虑更改为没有输出文件则认为输出异常
        my $laser515_file = "$output_path/$JOB.$r515laser";
        my @lot_list = ();
        if (-e $laser515_file) {
            open(STAT, $laser515_file) or die "can't open file $laser515_file: $!";
            while (<STAT>) {
                push(@lot_list, $_);
            }
            close(STAT);
            unlink($laser515_file);
        }
        else {
            # === add by Song  2020.06.10  如果无文件输出，认为输出过程中报错 ===
            $c->Messages("info", "LaserLot号输出异常,\n请更改左下角的Set排在S&R Table的最前面\n重新输出");
            if (-e "$output_path/$JOB.$dis_lay") {
                unlink "$output_path/$JOB.$dis_lay";
            }
            exit 0;
        }

        my $t01exist = "no";
        my $m2exist = "no";
        my $body_start = "no";
        my $m25num = 0;
        foreach $tmp (@lot_list) {
            if ($tmp ne "") {
                if ($tmp eq "T0[2-9]C[0-9].*\n") {$m2exist = "yes";}
                if ($tmp =~ /T01(C0.515)/) {$t01exist = "yes";}
                if ($tmp eq "%\n") {$body_start = "yes";}
                if ($body_start eq "yes") {
                    if ($tmp =~ /^T01\n$/) {
                        $search_key = $tmp;
                        chomp $search_key;
                    }
                    elsif ($tmp eq "M30\n" || $tmp eq "%\n") {
                    }
                    elsif ($tmp eq "M25\n") {
                        $m25num++;
                        # change $LOTto 汤龙洲的需求 2020.03.25
						# 2020.11.18 更改回$LOT 
                        my $add_line = "M25\n$LotDirec,\$LOT\n";

                        #my $add_line = "M25\n$LotDirec,\$DAY&\$MACHINE&\$STAGE&\$SERIAL#3\n";
                        push(@{$r515cor{"C0.515"}}, $add_line);
                    }
                    else {
                        push(@{$r515cor{"C0.515"}}, $tmp);
                    }
                }
            }
        }
        # 检查输出的文本中是否M25指令为两个及以上
        if ($m25num > 1) {
            $c->Messages("info", "镭射LOT号输出中翻版指令M25仅能存在一个,请检查");
        }
    }
		if ($^O eq MSWin32) {

    $f->COM("set_subsystem,name=1-Up-Edit");
    $f->COM("top_tab,tab=Display");
		}
}

sub getInplanData {
    our $o = new VGT_Oracle();
    our $dbc_h = $o->CONNECT_ORACLE('host' => '172.20.218.193', 'service_name' => 'inmind.fls', 'port' => '1521', 'user_name' => 'GETDATA', 'passwd' => 'InplanAdmin');
    if (!$dbc_h) {
        $c->Messages('warning', '"HDI InPlan数据库"连接失败');
        return;
    }

    my $drc_job;
    if ($JOB =~ /(.*)-[a-z].*/) {
        $drc_job = uc($1);
    }
    else {
        $drc_job = uc($JOB);
    }

    my %inplanLaserData;
    my $sql = "select a.item_name,
                e.item_name,
                d.laser_drl_parameter_,
                c.start_index,
                c.end_index
           from vgt_hdi.Items           A,
                VGT_HDI.JOB              b,
                VGT_HDI.DRILL_PROGRAM    c,
                vgt_hdi.drill_program_da d,
                vgt_hdi.public_items     e
          where a.item_id = b.item_id
            and a.last_checked_in_rev = b.revision_id
            and a.root_id = e.root_id
            and e.item_id = c.item_id
            and e.revision_id = c.revision_id
            and c.item_id = d.item_id
            and c.revision_id = d.revision_id
            and a.item_name = '$drc_job'
            and c.drill_technology = 2";

    my $sth = $dbc_h->prepare($sql); #结果保存在$sth中
    $sth->execute() or die "无法执行SQL语句:$dbc_h->errstr";

	my @couple_layers_two = ();
	my @couple_layers_one = ();
	my @couple_layers_one1 = ();
	my @couple_joint_name = ();
	my %tmp_hash;
    # --循环所有行数据
    while (my @recs = $sth->fetchrow_array) {
        my $tmp_name = "s" . "$recs[3]" . "-" . "$recs[4]";
        if (abs($recs[3] - $recs[4]) == 2) {
			push @couple_layers_two,$tmp_name;			
			if ($recs[3] > $recs[4]) {
				my $middle_num = $recs[4] + 1;
				push @couple_layers_one, "s" . "$recs[3]" . "-" . "$middle_num";
				push @couple_layers_one1, "s0-0";
				push @couple_joint_name, "s" . "$recs[3]" . "-" . "$middle_num" . "-" . "$recs[4]";
			} else {
				my $middle_num = $recs[4] - 1;
				push @couple_layers_one, "s" . "$recs[3]" . "-" . "$middle_num";
				push @couple_layers_one1, "s0-0";
				push @couple_joint_name, "s" . "$recs[3]" . "-" . "$middle_num" . "-" . "$recs[4]";
			}
		}

        if (abs($recs[3] - $recs[4]) == 3) {
			push @couple_layers_two,$tmp_name;			
			if ($recs[3] > $recs[4]) {
				my $middle_num = $recs[4] + 1;  
				my $middle_num1 = $recs[4] + 2;  
				my $layers_one = "s" . "$recs[3]" . "-" . "$middle_num1";     
				my $layers_one1 = "s" . "$recs[3]" . "-" . "$middle_num";     
				push @couple_layers_one, "s" . "$recs[3]" . "-" . "$middle_num1";
				push @couple_layers_one1, "s" . "$recs[3]" . "-" . "$middle_num";
				
				
				
				if (exists $tmp_hash{$layers_one} &&  exists $tmp_hash{$layers_one1}){
					push @couple_joint_name, "s" . "$recs[3]" . "-" . "$middle_num1" . "-" . "$middle_num". "-" . "$recs[4]";
				}elsif(exists $tmp_hash{$layers_one} &&  not exists $tmp_hash{$layers_one1}){
					push @couple_joint_name, "s" . "$recs[3]" . "-" . "$middle_num". "-" . "$recs[4]";
				}elsif(not exists $tmp_hash{$layers_one} &&  exists $tmp_hash{$layers_one1}){
					push @couple_joint_name, "s" . "$recs[3]" . "-" . "$middle_num1". "-" . "$recs[4]";
				}
				
			} else {
				my $middle_num = $recs[4] - 1;
				my $middle_num1 = $recs[4] - 2;
				push @couple_layers_one, "s" . "$recs[3]" . "-" . "$middle_num1";
				push @couple_layers_one1, "s" . "$recs[3]" . "-" . "$middle_num";
				
				my $layers_one = "s" . "$recs[3]" . "-" . "$middle_num1";
				my $layers_one1 = "s" . "$recs[3]" . "-" . "$middle_num";
				if (exists $tmp_hash{$layers_one} &&  exists $tmp_hash{$layers_one1}){
					push @couple_joint_name, "s" . "$recs[3]" . "-" . "$middle_num1" . "-" . "$middle_num"."-" . "$recs[4]";
				}elsif(exists $tmp_hash{$layers_one} &&  not exists $tmp_hash{$layers_one1}){
					push @couple_joint_name, "s" . "$recs[3]" . "-" . "$middle_num1". "-" . "$recs[4]";
				}elsif(not exists $tmp_hash{$layers_one} &&  exists $tmp_hash{$layers_one1}){
					push @couple_joint_name, "s" . "$recs[3]" . "-" . "$middle_num". "-" . "$recs[4]";
				}
								
			}
		}
		
        # --重新恢复原来的匹配模式,使用起始、结束index组合来定义层名  AresHe 2022.1.11
        # --为防止匹配不到合并层(类似:s1-2-3),按层名栏位直接匹配,不再使用起始index组合新层匹配  AresHe 2021.12.16
        #my $tmp_name = $recs[1];
        $inplanLaserData{$tmp_name} = $recs[2];
		my @tmp_array = ();

		if (!defined $recs[2] || $recs[2] eq '') {
			push @tmp_array,"None";
			push @tmp_array, "1";
			push @tmp_array, "disable";
		}
		elsif ($recs[2] eq "未导入") {
			push @tmp_array,'Null2';
			push @tmp_array, "1";
			push @tmp_array, "normal";
		}
		elsif ($recs[2] =~ /^未导入(.*(um|mil))$/) {
			push @tmp_array, $1;
			push @tmp_array, "0";
			push @tmp_array, "disable";
		}
		elsif ($recs[2] =~ /^\d+.*(um|mil)$/) {
			push @tmp_array, $recs[2];
			push @tmp_array, "0";
			push @tmp_array, "disable";
		}
		elsif ($recs[2] =~ /^Core.*(um|mil)$/) {
			# 2019.12.11增加，工艺反馈
			push @tmp_array, $recs[2];
			push @tmp_array, "0";
			push @tmp_array, "disable";
		}
		elsif ($recs[2] =~ /^\d+.*(um|mil)X[23]$/) {
			# === 2021.03.30 镭射参数表更新 增加X2，X3结尾
			push @tmp_array, $recs[2];
			push @tmp_array, "0";
			push @tmp_array, "disable";
		}
		elsif ($recs[2] =~ /^\d+.*mil-X-[0-9][0-9]um$/) {
			# === 2021.03.30 106-2mil-X-70um
			push @tmp_array, $recs[2];
			push @tmp_array, "0";
			push @tmp_array, "disable";
		}
		elsif ($recs[2] =~ /^\d+(\+\d+){0,3}-\d+(\+\d+){0,3}um$/) {
			# === 2021.12.17 1067+1086-152+178+203UM 增加1~4种PP及1-4种孔径 ===
			push @tmp_array, $recs[2];
			push @tmp_array, "0";
			push @tmp_array, "disable";
		}
		else {
			push @tmp_array, $recs[2];
			push @tmp_array, "0";
			push @tmp_array, "disable";
		}
		@{$tmp_hash{$tmp_name}} = @tmp_array;
        if ($hash{$tmp_name}) {
			$hash{$tmp_name}[8] = $tmp_array[0];
			$hash{$tmp_name}[10] = $tmp_array[1];
			$hash{$tmp_name}[11] = $tmp_array[2];
        }

        #print Dumper(\@recs);
        # print Data::Dumper->Dump([ \@recs ], [ qw(*recs) ]);
    }
#    print Dumper(\%inplanLaserData);
#	print Dumper(\%hash);
	print Dumper(\%tmp_hash);

	for (my $k = 0; $k <= $#couple_layers_two; $k++) {
		if (exists $tmp_hash{$couple_layers_one[$k]}) {
			if ( $tmp_hash{$couple_layers_two[$k]}[0] eq $tmp_hash{$couple_layers_one[$k]}[0]) {
				if (exists $tmp_hash{$couple_layers_one1[$k]}) {
					if ( $tmp_hash{$couple_layers_two[$k]}[0] eq $tmp_hash{$couple_layers_one1[$k]}[0]){
						$hash{$couple_joint_name[$k]}[8] = $tmp_hash{$couple_layers_two[$k]}[0] ;
						$hash{$couple_joint_name[$k]}[10] = $tmp_hash{$couple_layers_two[$k]}[1] ;
						$hash{$couple_joint_name[$k]}[11] =  $tmp_hash{$couple_layers_two[$k]}[2] ;
					}
				}else{
					$hash{$couple_joint_name[$k]}[8] = $tmp_hash{$couple_layers_two[$k]}[0] ;
					$hash{$couple_joint_name[$k]}[10] = $tmp_hash{$couple_layers_two[$k]}[1] ;
					$hash{$couple_joint_name[$k]}[11] =  $tmp_hash{$couple_layers_two[$k]}[2] ;
				}
			}
		}
	}
	print @couple_layers_two;
	print "\n";
	print @couple_layers_one;
	print "\n";
	print @couple_layers_one1;
	print "\n";
	print @couple_joint_name;
	print "\n";
	#print  Dumper(\%hash);

    $dbc_h->disconnect if ($dbc_h);
    if (!%inplanLaserData) {
        #code
        $c->Messages('info', "HDI InPlan中无此料号信息，请手动填写");
        for (my $a = 0; $a <= $#rlayers; $a++) {
            ${$hash{$rlayers[$a]}}[10] = "1";
            ${$hash{$rlayers[$a]}}[11] = "normal";
        }
    }
    &show_table;
}

# 获取erp中镭射钻带打5遍的刀具信息

sub getErpDrillData{
	our $o = new VGT_Oracle();
    our $dbc_e = $o->CONNECT_ORACLE('host' => '172.20.218.247', 'service_name' => 'topprod', 'port' => '1521', 'user_name' => 'zygc', 'passwd' => 'ZYGC@2019');
    if (!$dbc_e) {
        $c->Messages('warning', '"ERP数据库"连接失败');
        return;
    }
	my $drc_job;
    if ($JOB =~ /(.*)-[a-z].*/) {
        $drc_job = uc($1);
    }
    else {
        $drc_job = uc($JOB);
    }
	my %erp_data = $o->getDrlData($dbc_e,$drc_job);
	print Dumper(\%erp_data); 
	return %erp_data;
}

#####获取对应层铜厚
sub getInplanThick {
	# my ($layer_thick) = @_;
    our $o = new VGT_Oracle();
    our $dbc_h = $o->CONNECT_ORACLE('host' => '172.20.218.193', 'service_name' => 'inmind.fls', 'port' => '1521', 'user_name' => 'GETDATA', 'passwd' => 'InplanAdmin');
    if (!$dbc_h) {
        $c->Messages('warning', '"HDI InPlan数据库"连接失败');
        return;
    }

    my $drc_job;
    if ($JOB =~ /(.*)-[a-z].*/) {
        $drc_job = uc($1);
    }
    else {
        $drc_job = uc($JOB);
    }
    
    my $sql =  " SELECT
            a.item_name JOB_NAME,
            LOWER(c.item_name) LAYER_NAME,
            d.layer_position,
            round( d.required_cu_weight / 28.3495, 2 ) CU_WEIGHT,
             e.finish_cu_thk_  FINISH_THICKNESS,
             round(e.cal_cu_thk_/1.0,2)  CAL_CU_THK
           
        FROM
            vgt_hdi.items a,
            vgt_hdi.job b,
            vgt_hdi.items c,
            vgt_hdi.copper_layer d,
            vgt_hdi.copper_layer_da e 
        WHERE
            a.item_id = b.item_id 
            AND a.last_checked_in_rev = b.revision_id 
            AND a.root_id = c.root_id 
            AND c.item_id = d.item_id 
            AND c.last_checked_in_rev = d.revision_id 
            AND d.item_id = e.item_id 
            AND d.revision_id = e.revision_id 
            AND a.item_name = '$drc_job' 
        ORDER BY
            d.layer_index";
	my %inplanThick;
    my $sth = $dbc_h->prepare($sql); #结果保存在$sth中
    $sth->execute() or die "无法执行SQL语句:$dbc_h->errstr";
	while (my @recs = $sth->fetchrow_array) {
		# $get_result = $recs[0];
		# print Dumper(\@recs); 
		$inplanThick{$recs[1]} = $recs[5];
	}
	# print Dumper(\%inplanThick); 
	return %inplanThick;
}

sub getInplan_Lot_Add {
    our $o = new VGT_Oracle();
    our $dbc_h = $o->CONNECT_ORACLE('host' => '172.20.218.193', 'service_name' => 'inmind.fls', 'port' => '1521', 'user_name' => 'GETDATA', 'passwd' => 'InplanAdmin');
    if (!$dbc_h) {
        $c->Messages('warning', '"HDI InPlan数据库"连接失败');
        return;
    }
	my $add_lot_yn;
    my $drc_job;
    if ($JOB =~ /(.*)-[a-z].*/) {
        $drc_job = uc($1);
    }
    else {
        $drc_job = uc($JOB);
    }

    my %inplanLaserData;
    my $sql = "SELECT
		p.value 
	FROM
		VGT_HDI.rpt_job_list j,
		VGT_HDI.field_enum_translate p
	WHERE
		j.job_name = '$drc_job' 
		AND p.fldname = 'CI_ADD_LASER_LOT_' 
		AND p.intname = 'JOB' 
		AND p.enum = j.CI_ADD_LASER_LOT_";

    my $sth = $dbc_h->prepare($sql); #结果保存在$sth中
    $sth->execute() or die "无法执行SQL语句:$dbc_h->errstr";
	my  $get_result;
	#print $sth . "\n";
    # --循环所有行数据
    while (my @recs = $sth->fetchrow_array) {
		$get_result = $recs[0];
	}
    $dbc_h->disconnect if ($dbc_h);
	if ( not $get_result or $get_result eq  'Unknown') {
		$add_lot_yn = 'Unknown';
	} elsif ( $get_result eq '不添加') {
		$add_lot_yn = 'no';
	} else {
		$add_lot_yn = 'yes';
	}
	return $add_lot_yn;
}



sub mainCheckLaserLot {
    my ($chkLotLyr) = @_;
    my $getfirstSetInfo = &checkSRtableContinue;
    my $flipStepExist = 'no';
    if ($getfirstSetInfo eq 'noContinue') {
        $c->Messages("info", "set在panel的S&R Table中未设计连续,\n程序退出");
        exit 0;
    }
    elsif ($getfirstSetInfo eq 'mirrorExist') {
        $c->Messages("info", "set在panel的S&R Table中镜像拼板,程序特殊算法");
        #exit 0;
        ## TODO 临时屏蔽 202002.21 song
        # 20200224 更改为返回值
        if ($chkLotLyr !~ 's1-') {
            #lot号在set中必须加于Top面
            $c->Messages("info", "set中的r515必须加于Top面,程序退出");
            exit 0;
        }
        $flipStepExist = 'yes';
    }
    my $getCheckSameCenter = &checkLaserLotSameWithCopper($chkLotLyr);
    # --TODO 解决报internal error的方法，李家兴添加20200927,切到set后，再直接切回NC-Manager会打开new nc output set窗口
	# === V3.2.5 为了在windows下测试界面，更改以下
	if ($^O ne 'MSWin32') {
		$f->COM("set_subsystem,name=1-Up-Edit");
		$f->COM("top_tab,tab=Display");
		$f->COM("set_step,name=$step_name");
		$f->AUX("set_group,group=$f->{COMANS}");
	} else {
		$f->COM("open_entity,job=$JOB,type=step,name=$step_name,iconic=no");
		$f->AUX("set_group,group=$f->{COMANS}");
	}
	
    # ---------------------------------------------------
    if ($getCheckSameCenter eq 'noOutSymDesign') {
        $c->Messages("info", "外层未设计laser-array-lot-cu或symbol被打散,\n程序退出");
        exit 0;
    }
    elsif ($getCheckSameCenter eq 'noSameCenter') {
        $c->Messages("info", "外层设计laser-array-lot-cu与r515中心不一致,\n程序退出");
        exit 0;
    }
    elsif ($getCheckSameCenter eq 'laserNameError') {
        $c->Messages("info", "镭射层$chkLotLyr 命名不正确,\nCode:100 程序退出");
        exit 0;
    }
    elsif ($getCheckSameCenter eq 'numErrorDesign') {
        $c->Messages("info", "镭射层$chkLotLyr 对应外层laser-array-lot-cu数量超过1,\nCode:103 程序退出");
        exit 0;
    }
    if ($flipStepExist eq 'yes') {
        return 'mirrorExist';
    }

    my $getLotDirec = &judgeM97orM98Direct($chkLotLyr, $getfirstSetInfo, $getCheckSameCenter);
    if ($getLotDirec eq 'laserNameError') {
        $c->Messages("info", "镭射层$chkLotLyr 命名不正确,\nCode:101 程序退出");
        exit 0;
    }
    return $getLotDirec;
}


sub checkSRtableContinue {
    # 用于检测是否set在panel中拼版为连续的
    $f->INFO(units => 'mm', entity_type => 'step', entity_path => "$JOB/$panel_step", data_type => 'SR');
    my @setNumList;
    my $laseNum;
    my %firstSetInfo;
    my $add_lot_step = 'set';
    $f->DO_INFO("-t step -e $JOB/set -d EXISTS");
    if ($f->{doinfo}{gEXISTS} eq "yes") {
        $add_lot_step = "set";
    }
    else {
        $add_lot_step = "edit";
    }
    for (my $i = 0; $i < @{$f->{doinfo}{gSRstep}}; $i++) {
        my $curStep = ${$f->{doinfo}{gSRstep}}[$i];
        if ($curStep eq $add_lot_step) {
            if (${$f->{doinfo}{'gSRflip'}}[$i] eq 'yes') {
                return 'mirrorExist';
            }
            push(@setNumList, $i);
            if (scalar @setNumList == 1) {
                #code
                $laseNum = $i;
                %firstSetInfo = (
                    'stepName'  => ${$f->{doinfo}{gSRstep}}[$i],
                    'stepIndex' => $i,
                    'gSRxa'     => ${$f->{doinfo}{'gSRxa'}}[$i],
                    'gSRya'     => ${$f->{doinfo}{'gSRya'}}[$i],
                    'gSRdx'     => ${$f->{doinfo}{'gSRdx'}}[$i],
                    'gSRdy'     => ${$f->{doinfo}{'gSRdy'}}[$i],
                    'gSRnx'     => ${$f->{doinfo}{'gSRnx'}}[$i],
                    'gSRny'     => ${$f->{doinfo}{'gSRny'}}[$i],
                    'gSRangle'  => ${$f->{doinfo}{'gSRangle'}}[$i],
                    'gSRmirror' => ${$f->{doinfo}{'gSRmirror'}}[$i],
                    'gSRxmin'   => ${$f->{doinfo}{'gSRxmin'}}[$i],
                    'gSRymin'   => ${$f->{doinfo}{'gSRymin'}}[$i],
                    'gSRxmax'   => ${$f->{doinfo}{'gSRxmax'}}[$i],
                    'gSRymax'   => ${$f->{doinfo}{'gSRymax'}}[$i],
                    'gSRflip'   => ${$f->{doinfo}{'gSRflip'}}[$i],
                )

            }
            else {

                my $tmp_chk_num = $laseNum + 1;

                if ($i != $tmp_chk_num) {
                    return 'noContinue';
                }
                $laseNum = $i;
            }
        }
    }
    #print Dumper(\%firstSetInfo);
    print "checkSRtableContinueEnd\n";
    return (\%firstSetInfo);
}

sub checkLaserLotSameWithCopper {
    # 用于检测工艺边上的lot号是否与底铜一致
    my ($chkLaserLayer) = @_;
    my $lotAddlayer;
    if ($chkLaserLayer =~ /s([1-9][0-9]?)-([1-9][0-9]?)/) {
        $lotAddlayer = "l" . "$1";
    }
    else {
        return "laserNameError";
    }
    my $chkLay = 'tmp_laser_lot+++';
    my $set_step = 'set';
    $f->DO_INFO("-t step -e $JOB/set -d EXISTS");
    if ($f->{doinfo}{gEXISTS} eq "yes") {
        $set_step = "set";
    }
    else {
        $set_step = "edit";
    }
    my $r515laser = 'r515' . $chkLaserLayer;
    my @getlayerF;
    $c->OPEN_STEP($JOB, "$set_step");
    $c->CLEAR_LAYER();
    $c->DELETE_LAYER($chkLay);
    $c->AFFECTED_LAYER($lotAddlayer, 'yes');
    $c->FILTER_RESET;
    $c->FILTER_SET_INCLUDE_SYMS('laser-array-lot-cu');
    $c->FILTER_SELECT;
    if ($c->GET_SELECT_COUNT != 0) {
        # 取底铜的信息
        my $csh_file = "$tmpPath/info_csh.$$";
        $f->COM("info, out_file=$csh_file, units=mm,args= -t layer -e $JOB/$set_step/$lotAddlayer -d FEATURES -o select");
        @getlayerF = $c->dealwithFeatureFile($csh_file);
        unlink($csh_file);
        $c->SEL_COPY($chkLay, "no", 0,);

    }
    else {
        return 'noOutSymDesign';
    }
    if (scalar @getlayerF != 1) {
        return 'numErrorDesign';
    }

    $c->CLEAR_LAYER();
    $c->AFFECTED_LAYER($chkLay, 'yes');
    $f->COM("sel_invert");
    $c->SEL_BREAK;
    $c->FILTER_RESET;
    $c->SEL_REF_FEAT($r515laser, 'cover',);
    if ($c->GET_SELECT_COUNT != 0) {
        $c->DELETE_LAYER($chkLay);
        $c->CLEAR_LAYER();
        #print Dumper(\@getlayerF);
        print "checkLaserLotSameWithCopperend\n";
        return (\@getlayerF);
    }
    else {
        $c->CLEAR_LAYER();
        return 'noSameCenter';
    }
}


sub judgeM97orM98Direct {
    # 通过底铜判断M97，M98方向
    my ($chkLotLayer, $getfirstSetInfo, $getCheckSameCenter) = @_;
    my %firstSetInfo = %$getfirstSetInfo;
    my @laserLotInfo = @$getCheckSameCenter;
#	print '%firstSetInfo' . "\n";
#    print Dumper(\%firstSetInfo);
#	print '@laserLotInfo' . "\n";
#    print Dumper(\@laserLotInfo);
    my $lotCode;
    my $chkMirRef;
    # 暂不支持镜像添加，检测symbol的镜像情况。
    if ($firstSetInfo{'gSRmirror'} eq 'yes') {
        $c->Messages("info", "set在panel中为镜像Lot号特殊加法，请检查");
        # TODO 暂时取消此退出窗口
        #exit 0;

    }
    # Top面镭射不允许添加镜像；
    # Bot面镭射不允许添加非镜像；
    if ($chkLotLayer =~ /s([1-9][0-9]?)-([1-9][0-9]?)/) {
        # TODO 判定为top或者bot
        if (exists $r515CheckData{$chkLotLayer}{'mir'}) {
            $chkMirRef = $r515CheckData{$chkLotLayer}{'mir'};
        }
        else {
            return "laserNameError"
        }
    }
    else {
        return "laserNameError";
    }

    if ($laserLotInfo[0]{'mirror'} ne $chkMirRef) {
        $c->Messages("info", "set中镭射$chkLotLayer 对应层别添加的\nlaser-array-lot-cu镜像为$laserLotInfo[0]{'mirror'},\n 实际应该添加镜像为$chkMirRef ,程序退出");
        exit 0;
    }
    if ($laserLotInfo[0]{'mirror'} eq 'yes') {
        # 镜像是角度使用相减计算，由于相减角度会出现负值，使用360补位
        my $pnlLotAngle = $laserLotInfo[0]{'angle'} - $firstSetInfo{'gSRangle'} + 360;
        if ($pnlLotAngle >= 360) {
            $pnlLotAngle = $pnlLotAngle - 360;
        }
        if ($pnlLotAngle == 180) {
            $lotCode = 'M97';
        }
        elsif ($pnlLotAngle == 90) {
            $lotCode = 'M98';
        }
        else {
            $c->Messages("info", "层别$chkLotLayer 在pnl中的lot角度为$pnlLotAngle,\n仅支持180度90度，程序退出");
            exit 0;
        }
    }
    else {
        my $pnlLotAngle = $firstSetInfo{'gSRangle'} + $laserLotInfo[0]{'angle'};
        if ($pnlLotAngle >= 360) {
            $pnlLotAngle = $pnlLotAngle - 360;
        }
        if ($pnlLotAngle == 0) {
            $lotCode = 'M97';
        }
        elsif ($pnlLotAngle == 270) {
            $lotCode = 'M98';
        }
        else {
            $c->Messages("info", "层别$chkLotLayer pnl中的lot角度为$pnlLotAngle,\n仅支持0度270度，程序退出");
            exit 0;
        }
    }
    return $lotCode;
}

sub checkr515exist {
    my ($dis_lay) = @_;
    my $lot_step;
    my $r515exist = "no";
    my $r515laser = 'r515' . $dis_lay;
    our %r515cor = ();
    $f->DO_INFO("-t step -e $JOB/set -d EXISTS");
    if ($f->{doinfo}{gEXISTS} eq "yes") {
        $lot_step = "set";
    }
    else {
        $lot_step = "edit";
    }
    $c->OPEN_STEP("$JOB", "$lot_step");
    $c->CHANGE_UNITS("mm");
    $c->DELETE_LAYER($r515laser);
    $c->CLEAR_LAYER();
    $c->AFFECTED_LAYER("$dis_lay", "yes");
    $c->FILTER_RESET;
    $c->FILTER_SET_INCLUDE_SYMS("r515");
    $c->FILTER_SELECT;
    if ($c->GET_SELECT_COUNT != 0) {
        $r515exist = "yes";
        $c->SEL_COPY("$r515laser", "no", 0,);
    }
    if ($r515exist eq "yes") {
        $f->COM("matrix_layer_type,job=$JOB,matrix=matrix,layer=$r515laser,type=drill");
    }
    $c->CLEAR_LAYER();
    return $r515exist;
}

sub deleteLaserTouchDLD {
    my ($laser_layer, $dld_layer) = @_;
    $f->COM("set_subsystem,name=1-Up-Edit");
    $f->COM("top_tab,tab=Display");
    $c->CLEAR_LAYER();
    $c->AFFECTED_LAYER("$laser_layer", "yes");
    $c->FILTER_RESET();
    $c->SEL_REF_FEAT("$dld_layer", 'cover',);
    $f->COM("get_select_count");
    if ($f->{COMANS} == 4 || $f->{COMANS} == 8 || $f->{COMANS} == 16) {
        $f->COM("sel_delete");
    }
    $c->CLEAR_LAYER();
}

sub dealWithMirrorLaserLayer {
    #P 267.5342325 163.9540625 laser-array-lot-cu N 0 90 Y
    # 获取反面镭射层中添加的 laser-array-lot-cu信息
    my ($add_type, $oplaserlayer) = @_;
	
	#print 'xxxxxxxxxxxxxxxxxxxxxxxxx' . "\n";
	#print $oplaserlayer . "\n";
	#print 'xxxxxxxxxxxxxxxxxxxxxxxxx' . "\n";
    my $chkLyr;
    my $chkMirRef;
    my @pnlLaserLotData;
    # 增加选项，top面及bot面
    if ($add_type eq 'top') {
        $chkLyr = 'l1';
        $chkMirRef = 'no';
    }
    elsif ($add_type eq 'bot') {
        $chkLyr = 'l' . $job_signal_nubers;
        $chkMirRef = 'yes';
    }
    else {
        return 'Type_Error';
    }


    # end 检测
    # 检测板边laser-array-lot-cu 与r515是否中心相同
    my $tmpLay = 'tmp_laser_lot+++';
    my $r515laser = 'r515' . $oplaserlayer;
    $c->OPEN_STEP($JOB, "$step_name");
    $c->CLEAR_LAYER();
    $c->CHANGE_UNITS('mm');
    $c->DELETE_LAYER($r515laser);

    # 选择panel中的r515钻孔
    $c->AFFECTED_LAYER($oplaserlayer, 'yes');
    $c->FILTER_RESET;
    $c->FILTER_SET_INCLUDE_SYMS('r515');
    $c->FILTER_SELECT;
    if ($c->GET_SELECT_COUNT != 0) {
        if ($c->GET_SELECT_COUNT != 1) {
            $c->Messages("info", "层别$oplaserlayer 在pnl中 的r515数量不是1个,\n阴阳拼版必须在板边添加一个，程序退出");
            exit 0;
        }
        $c->SEL_COPY($r515laser, "no", 0,);
    }
    else {
        $c->Messages("info", "层别$oplaserlayer 在pnl中 的r515数量不是1个,\n阴阳拼版必须在板边添加一个，程序退出");
        exit 0;
    }

    $c->CLEAR_LAYER();
    $c->DELETE_LAYER($tmpLay);
    $c->AFFECTED_LAYER($chkLyr, 'yes');
    $c->FILTER_RESET;
    $c->FILTER_SET_INCLUDE_SYMS('laser-array-lot-cu');
    $c->FILTER_SELECT;
    if ($c->GET_SELECT_COUNT != 0) {
        # 取底铜的信息
        my $csh_file = "$tmpPath/info_csh.$$";
        $f->COM("info, out_file=$csh_file, units=mm,args= -t layer -e $JOB/$step_name/$chkLyr -d FEATURES -o select");
        @pnlLaserLotData = $c->dealwithFeatureFile($csh_file);
        unlink($csh_file);
        $c->SEL_COPY($tmpLay, "no", 0,);

    }
    else {
        #return 'noOutSymDesign';
        $c->Messages("info", "$chkLyr pnl中的laser-array-lot-cu,\n添加数量非1个，Code:201 程序退出");
        exit 0;
    }
    if (scalar @pnlLaserLotData != 1) {
        #return 'numErrorDesign';
        $c->Messages("info", "$chkLyr pnl中的laser-array-lot-cu,\n添加数量非1个，Code:202 程序退出");
        exit 0;

    }

    $c->CLEAR_LAYER();
    $c->AFFECTED_LAYER($tmpLay, 'yes');
    $f->COM("sel_invert");
    $c->SEL_BREAK;
    $c->FILTER_RESET;
    $c->SEL_REF_FEAT($r515laser, 'cover',);
    if ($c->GET_SELECT_COUNT != 0) {
        $c->DELETE_LAYER($tmpLay);
        $c->CLEAR_LAYER();
        #print Dumper(\@getlayerF);
        print "checkLaserLotSameWithCopperend\n";
        #return (\@pnlLaserLotData);
    }
    else {
        $c->CLEAR_LAYER();
        #return 'noSameCenter';
        $c->Messages("info", "pnl外层${chkLyr}设计laser-array-lot-cu与r515中心不一致,\n程序退出");
        exit 0;
    }
    $c->DELETE_LAYER($r515laser);

    # end检测
    # 检测添加的一个角度是否正确

    # 检测panel中添加symbol的镜像关系
    if ($pnlLaserLotData[0]{'mirror'} ne $chkMirRef) {
        $c->Messages("info", "pnl中镭射$chkLyr 对应层别添加的\nlaser-array-lot-cu镜像为$pnlLaserLotData[0]{'mirror'},\n 实际应该添加镜像为$chkMirRef ,程序退出");
        exit 0;
    }
    if ($pnlLaserLotData[0]{'mirror'} eq 'yes') {
        # 镜像是角度使用相减计算，由于相减角度会出现负值，使用360补位
        if ($pnlLaserLotData[0]{'angle'} == 180) {
            $lotCode = 'M97';
        }
        elsif ($pnlLaserLotData[0]{'angle'} == 90) {
            $lotCode = 'M98';
        }
        else {
            $c->Messages("info", "层别$chkLyr 在pnl中的lot角度为$pnlLaserLotData[0]{'angle'} ,\n仅支持180度90度，程序退出");
            exit 0;
        }
    }
    else {
        if ($pnlLaserLotData[0]{'angle'} == 0) {
            $lotCode = 'M97';
        }
        elsif ($pnlLaserLotData[0]{'angle'} == 270) {
            $lotCode = 'M98';
        }
        else {
            $c->Messages("info", "层别$chkLyr 在pnl中的lot角度为$pnlLaserLotData[0]{'angle'},\n仅支持0度270度，程序退出");
            exit 0;
        }
    }
    $r515CheckData{$oplaserlayer}{'lotCode'} = $lotCode;

    # end check
    my $csh_file = "$tmpPath/info_csh.$$";
    $f->COM("info, out_file=$csh_file, units=mm,args=  -t layer -e  $JOB/panel/$chkLyr -d FEATURES -o break_sr");
    my @getlayerTar = $c->dealwithFeatureFile($csh_file);
    unlink($csh_file);
    my @arrayLaserLotData;
    push @arrayLaserLotData, $pnlLaserLotData[0];
    for (my $i = 0; $i <= $#getlayerTar; $i++) {
        if ($getlayerTar[$i]{symbol} eq 'laser-array-lot-cu') {
            if ($getlayerTar[$i]{'x'} ne $pnlLaserLotData[0]{'x'} && $getlayerTar[$i]{'y'} ne $pnlLaserLotData[0]{'y'}) {
                #panel中添加的剔除
                push @arrayLaserLotData, $getlayerTar[$i];
            }
        }
    }
    #print Dumper(\@arrayLaserLotData);
    return (\@arrayLaserLotData);
}

sub addTmpStep {
    my ($op_layer, $toplaser, $getLaserLotData) = @_;

    my @arrayLaserLotData = @$getLaserLotData;
    $f->VOF();
    $f->COM("delete_entity,job=$JOB,name=laser-lot,type=step");
    $f->VON();

    $f->COM("copy_entity_from_lib,job=$JOB,name=laser-lot,type=step,profile=none");
    $f->COM("set_step,name=$step_name");
    $f->AUX("set_group,group=$f->{COMANS}");
    $f->COM("units,type=mm");
    for (my $i = 0; $i <= $#arrayLaserLotData; $i++) {
        $f->COM("sr_tab_add,step=laser-lot,line=0,x=$arrayLaserLotData[$i]{x},y=$arrayLaserLotData[$i]{y},nx=1,ny=1,dx=0,dy=0,angle=$arrayLaserLotData[$i]{angle},flip=$arrayLaserLotData[$i]{mirror},mirror=no");
    }
    my $r515laser = 'r515' . $op_layer;
    my $r515exist = "no";

    $c->OPEN_STEP("$JOB", "laser-lot");
    $c->CHANGE_UNITS("mm");
    $c->DELETE_LAYER($r515laser);
    $c->CLEAR_LAYER();
    $c->AFFECTED_LAYER("$toplaser", "yes");
    $c->FILTER_RESET;
    $c->FILTER_SET_INCLUDE_SYMS("r515");
    $c->FILTER_SELECT;
    if ($c->GET_SELECT_COUNT != 0) {
        $r515exist = "yes";
        $c->SEL_COPY("$r515laser", "no", 0,);
    }
    if ($r515exist eq "yes") {
        $f->COM("matrix_layer_type,job=$JOB,matrix=matrix,layer=$r515laser,type=drill");
    }
    $c->CLEAR_LAYER();
}

sub deal_mir515_laser {
    #输出r515层别，并收集信息到hash中
    my ($dis_lay) = @_;
    my $LotDirec;
    our %r515cor = ();
    if (defined $r515CheckData{$dis_lay}{'lotCode'}) {
        $LotDirec = $r515CheckData{$dis_lay}{'lotCode'};
    }
    else {
        $c->Messages("info", "获取set镭射Lot号方向失败,请检查");
        return 'getDirectError';
    }

    if ($scale_position eq "中心") {
        $scale_center_x = $op_x_center;
        $scale_center_y = $op_y_center;
    }
    else {
        $scale_center_x = 0;
        $scale_center_y = 0;
    }
    $f->COM("top_tab,tab=Matrix");
    $f->AUX("set_step,name=$step_name");
    $f->AUX("set_group,group=$f->{COMANS}");
    my $r515laser = 'r515' . $dis_lay;
    my $ncsetlot = 'lot' . $dis_lay;

    $f->COM("matrix_layer_type,job=$JOB,matrix=matrix,layer=$r515laser,type=drill");
    $f->COM("set_subsystem,name=Nc-Manager");
    $f->COM("nc_set_current,job=$JOB,step=$step_name,layer=,ncset=");
    $f->VOF;
    $f->COM("nc_delete,layer=$r515laser,ncset=$ncsetlot");
    $f->VON;
    $f->COM("nc_create,ncset=$ncsetlot,device=misumi,lyrs=$r515laser,thickness=0");
    $f->COM("nc_set_advanced_params,layer=$r515laser,ncset=$ncsetlot,parameters=(rout_arc_as_ij=no)(out_exc_old_sr_syntax=no)");
    $f->COM("nc_set_current,job=$JOB,step=$step_name,layer=$r515laser,ncset=$ncsetlot");
    $f->COM("nc_set_file_params,output_path=$output_path,output_name=$JOB.$r515laser,zeroes=trailing,units=mm,tool_units=mm,nf1=3,nf2=3,decimal=no,modal_coords=no,single_sr=yes,sr_zero_set=no,repetitions=sr,incremental=no,ext_layer=drl2rt,sr_zero_layer=,ccw=no,short_lines=none,allow_no_chain_f=no,no_chain_as_slot=no,keep_table_order=no,max_arc_angle=0,comp_short_slot=no,gscale_file_name=,layer_datum=bottom_left,gscle_align_angle=0,gscl_offset_x=0,gscl_offset_y=0");
    if (${$hash{$dis_lay}}[4] eq 'no') {
        $ver = 1;
    }
    elsif (${$hash{$dis_lay}}[4] eq 'yes') {
        $ver = 7;
    }
    my $scale_x = ${$hash{$dis_lay}}[2];
    my $scale_y = ${$hash{$dis_lay}}[3];
    $f->COM("nc_register,angle=0,xoff=0,yoff=0,version=$ver,xorigin=0,yorigin=0,xscale=$scale_x,yscale=$scale_y,xscale_o=$scale_center_x,yscale_o=$scale_center_y,xmirror=no,ymirror=no");
    $f->COM("nc_set_optim,optimize=yes,iterations=5,reduction_percent=1,cool_spread=0,break_sr=no,xspeed=2540,yspeed=2540,diag_mode=45ort");
    $f->COM("nc_cre_output,layer=$r515laser,ncset=$ncsetlot");
    my $laser515_file = "$output_path/$JOB.$r515laser";
    my @lot_list = ();
    if (-e $laser515_file) {
        open(STAT, $laser515_file) or die "can't open file $laser515_file: $!";
        while (<STAT>) {
            push(@lot_list, $_);
        }
        close(STAT);
        # TODO 测试阶段屏蔽此句 by Song 2020.02.25
        #unlink($laser515_file);
    }

    my $t01exist = "no";
    my $m2exist = "no";
    my $body_start = "no";
    my $m25num = 0;
    foreach $tmp (@lot_list) {
        if ($tmp ne "") {
            if ($tmp eq "T0[2-9]C[0-9].*\n") {$m2exist = "yes";}
            if ($tmp =~ /T01(C0.515)/) {$t01exist = "yes";}
            if ($tmp eq "%\n") {$body_start = "yes";}
            if ($body_start eq "yes") {
                if ($tmp =~ /^T01\n$/) {
                    $search_key = $tmp;
                    chomp $search_key;
                }
                elsif ($tmp eq "M30\n" || $tmp eq "%\n") {
                }
                elsif ($tmp eq "M25\n") {
                    $m25num++;
					# 汤龙洲需求，更改镭射Lot为\$DAY&\$MACHINE&\$STAGE&\$SERIAL#3\ 2020.03.25
					# 彭勋要求，改回$LOT 2020.11.18 
                    my $add_line = "M25\n$LotDirec,\$LOT\n";
                    #my $add_line = "M25\n$LotDirec,\$DAY&\$MACHINE&\$STAGE&\$SERIAL#3\n";

                    push(@{$r515cor{"C0.515"}}, $add_line);
                }
                else {
                    push(@{$r515cor{"C0.515"}}, $tmp);
                }
            }
        }
    }
    # 检查输出的文本中是否M25指令为两个及以上
    if ($m25num > 1) {
        $c->Messages("info", "镭射LOT号输出中翻版指令M25仅能存在一个,请检查");
    }
    $f->VOF();
    $f->COM("delete_entity,job=$JOB,name=laser-lot,type=step");
    $f->VON();
    $f->COM("set_subsystem,name=1-Up-Edit");
    $f->COM("top_tab,tab=Display");
}

sub writeLog {

    unless (-e $logpath) {
        $c->Messages("info", "未获取到用户目录，不能写入记录");
        return;
    }
    #my $opData;
    #my $camData;
    my %loginfohah;
    my $DateTime = strftime "%Y.%m.%d %H:%M:%S", localtime(time);
    print $DateTime;

    my $cmd = "hostname";
    my $ophost = `$cmd`;
    chomp($ophost);
    my $plat;
    if ($^O eq 'linux') {
        $plat = 'Linux' . '_' . "$ENV{INCAM_SERVER}";

    }
    elsif ($^O eq MSWin32) {
        $plat = 'Windows';
    }

    $loginfohah{'JobName'} = $JOB;
    $loginfohah{'Appver'} = $script_Ver;
    $loginfohah{'Plat'} = $plat;
    $loginfohah{'opHost'} = $ophost;
    $loginfohah{'FlipSetExist'} = $FlipSetExist;

    if (open(SEASE, ">>:encoding(utf8)", "$logpath/outputlaserlog") or die("$!")) {

        $loginfohah{'Time'} = $DateTime;
        $loginfohah{'softuser'} = $incam_user;
        $loginfohah{'hostname'} = $ophost;
        #my $mi_name = Data::Dumper->new([\@recordLog],[qw(lamin_data)]);
        #$miData = $mi_name->Dump;
        print SEASE @recordList . "\n";
        my $baseinfo = Data::Dumper->new([ \%loginfohah ], [ qw(loginfohah) ]);
        $baseinfo1 = $baseinfo->Dump;
        print SEASE $baseinfo1;
        my $baseinfo2 = Data::Dumper->new([ \@recordList ], [ qw(recordList) ]);
        $baseinfo3 = $baseinfo2->Dump;
        print SEASE $baseinfo3;
    }

    close(SEASE);

    ## 写入hash开始 
    #$miData =~ s/'/''/g;
    #$camData =~ s/'/''/g;
    #
    for (my $i = 0; $i <= $#recordList; $i++) {
        my $sql = "insert into laser_output_log
    (job,layer,log_time,flipsetexist,filever,
    dld_exist,creator,param,mirror,
    lotcode,lotdirect,scalex,scaley,
    scale_center_x,scale_center_y,warninfo,localhost,
    software_platform,app_Version)
    values ('$loginfohah{'JobName'}','$recordList[$i]{'Layer'}','$loginfohah{'Time'}','$loginfohah{'FlipSetExist'}','$recordList[$i]{'ver'}',
    '$recordList[$i]{'dld_exist'}','$loginfohah{'softuser'}','$recordList[$i]{'Param'}','$recordList[$i]{'Mirror'}',
    '$recordList[$i]{'lotCode'}','$recordList[$i]{'LotDirec'}','$recordList[$i]{'scale_x'}','$recordList[$i]{'scale_y'}',
    '$recordList[$i]{'scale_center_x'}','$recordList[$i]{'scale_center_y'}','$recordList[$i]{'WarnInfo'}','$loginfohah{'opHost'}',
    '$loginfohah{'Plat'}','$loginfohah{'Appver'}')";

        my $sth = $dbc_m->prepare($sql); #结果保存在$sth中
        $sth->execute() or die "无法执行SQL语句:$dbc_m->errstr";
    }
}
#print "123";
#exit;
sub dealWithPanelLaserLayer {
    #P 267.5342325 163.9540625 laser-array-lot-cu N 0 90 Y
    # 获取反面镭射层中添加的 laser-array-lot-cu信息
    my ($add_type, $oplaserlayer) = @_;
    my $chkLyr;
    my $chkMirRef;
    my @pnlLaserLotData;
    # 增加选项，top面及bot面
    if ($add_type eq 'top') {
        $chkLyr = 'l1';
        $chkMirRef = 'no';
    }
    elsif ($add_type eq 'bot') {
        $chkLyr = 'l' . $job_signal_nubers;
        $chkMirRef = 'yes';
    }
    else {
        return 'Type_Error';
    }

    # end 检测
    # 检测板边laser-array-lot-cu 与r515是否中心相同
    my $tmpLay = 'tmp_laser_lot+++';
    my $r515laser = 'r515' . $oplaserlayer;
    $c->OPEN_STEP($JOB, "$step_name");
    $c->CLEAR_LAYER();
    $c->CHANGE_UNITS('mm');
    $c->DELETE_LAYER($r515laser);

    # 选择panel中的r515钻孔
    $c->AFFECTED_LAYER($oplaserlayer, 'yes');
    $c->FILTER_RESET;
    $c->FILTER_SET_INCLUDE_SYMS('r515');
    $c->FILTER_SELECT;
    if ($c->GET_SELECT_COUNT == 1) {
		$c->SEL_COPY($r515laser, "no", 0,);
    }
    else {
		$c->Messages("info", "层别$oplaserlayer 在pnl中 的r515数量不是1个,\n必须在板边添加一个，程序退出");
		exit 0;
    }
	# === 检测panel中的底铜Symbol数量是否为1，与515的Lot中心是否一致 ===
    $c->CLEAR_LAYER();
    $c->DELETE_LAYER($tmpLay);
    $c->AFFECTED_LAYER($chkLyr, 'yes');
    $c->FILTER_RESET;
    $c->FILTER_SET_INCLUDE_SYMS('laser-array-lot-cu');
    $c->FILTER_SELECT;
    if ($c->GET_SELECT_COUNT != 0) {
        # 取底铜的信息
        my $csh_file = "$tmpPath/info_csh.$$";
        $f->COM("info, out_file=$csh_file, units=mm,args= -t layer -e $JOB/$step_name/$chkLyr -d FEATURES -o select");
        @pnlLaserLotData = $c->dealwithFeatureFile($csh_file);
        unlink($csh_file);
        $c->SEL_COPY($tmpLay, "no", 0,);
    }
    else {
        #return 'noOutSymDesign';
        $c->Messages("info", "$chkLyr pnl中的laser-array-lot-cu,\n添加数量非1个，Code:201 程序退出");
        exit 0;
    }
    if (scalar @pnlLaserLotData != 1) {
        #return 'numErrorDesign';
        $c->Messages("info", "$chkLyr pnl中的laser-array-lot-cu,\n添加数量非1个，Code:202 程序退出");
        exit 0;
    }

    $c->CLEAR_LAYER();
    $c->AFFECTED_LAYER($tmpLay, 'yes');
    $f->COM("sel_invert");
    $c->SEL_BREAK;
    $c->FILTER_RESET;
    $c->SEL_REF_FEAT($r515laser, 'cover',);
    if ($c->GET_SELECT_COUNT != 0) {
        $c->DELETE_LAYER($tmpLay);
        $c->CLEAR_LAYER();
        #print Dumper(\@getlayerF);
        print "checkLaserLotSameWithCopperend\n";
        #return (\@pnlLaserLotData);
    }
    else {
        $c->CLEAR_LAYER();
        #return 'noSameCenter';
        $c->Messages("info", "pnl外层${chkLyr}设计laser-array-lot-cu与r515中心不一致,\n程序退出");
        exit 0;
    }
    $c->DELETE_LAYER($r515laser);

    # end检测
    # 检测添加的一个角度是否正确

    # 检测panel中添加symbol的镜像关系
    if ($pnlLaserLotData[0]{'mirror'} ne $chkMirRef) {
        $c->Messages("info", "pnl中镭射$chkLyr 对应层别添加的\nlaser-array-lot-cu镜像为 $pnlLaserLotData[0]{'mirror'},\n 实际应该添加镜像为$chkMirRef ,程序退出");
        exit 0;
    }
    if ($pnlLaserLotData[0]{'mirror'} eq 'yes') {
        # 镜像是角度使用相减计算，由于相减角度会出现负值，使用360补位
        if ($pnlLaserLotData[0]{'angle'} == 180) {
            $lotCode = 'M97';
        }
        elsif ($pnlLaserLotData[0]{'angle'} == 90) {
            $lotCode = 'M98';
        }
        else {
            $c->Messages("info", "层别$chkLyr 在pnl中的lot角度为$pnlLaserLotData[0]{'angle'} ,\n仅支持180度90度，程序退出");
            exit 0;
        }
    }
    else {
        if ($pnlLaserLotData[0]{'angle'} == 0) {
            $lotCode = 'M97';
        }
        elsif ($pnlLaserLotData[0]{'angle'} == 270) {
            $lotCode = 'M98';
        }
        else {
            $c->Messages("info", "层别$chkLyr 在pnl中的lot角度为$pnlLaserLotData[0]{'angle'},\n仅支持0度270度，程序退出");
            exit 0;
        }
    }
    $r515CheckData{$oplaserlayer}{'lotCode'} = $lotCode;
	# === 2021.02.26 Song 增加Symbol 镜像检查 ===
    # end check
    my $csh_file = "$tmpPath/info_csh.$$";
    $f->COM("info, out_file=$csh_file, units=mm,args=  -t layer -e  $JOB/panel/$chkLyr -d FEATURES -o break_sr");
    my @getlayerTar = $c->dealwithFeatureFile($csh_file);
    unlink($csh_file);
    my @arrayLaserLotData;
    push @arrayLaserLotData, $pnlLaserLotData[0];
    for (my $i = 0; $i <= $#getlayerTar; $i++) {
        if (exists $getlayerTar[$i]{symbol} && $getlayerTar[$i]{symbol} eq 'laser-array-lot-cu') {
			if ($getlayerTar[$i]{'mirror'} ne $chkMirRef) {
				$c->Messages("info", "镭射$chkLyr 对应层别添加的\nlaser-array-lot-cu镜像为 $getlayerTar[$i]{'mirror'},\n 实际应该添加镜像为$chkMirRef ,\n 坐标X:$getlayerTar[$i]{'x'} Y:$getlayerTar[$i]{'y'} 程序退出");
				exit 0;
			}
            if ($getlayerTar[$i]{'x'} ne $pnlLaserLotData[0]{'x'} && $getlayerTar[$i]{'y'} ne $pnlLaserLotData[0]{'y'}) {
                #panel中添加的剔除
                push @arrayLaserLotData, $getlayerTar[$i];
            }
        }
    }
	undef @getlayerTar;
	# === 2021.02.25 Song增加 镭射层的Lot与底铜对比
	# end check
    $csh_file = "$tmpPath/info_csh.$$";
    $f->COM("info, out_file=$csh_file, units=mm,args=  -t layer -e  $JOB/panel/$oplaserlayer -d FEATURES -o break_sr");
    my @getlayerCor = $c->dealwithFeatureFile($csh_file);
    unlink($csh_file);
    my @LaserLotData;
    push @LaserLotData, $pnlLaserLotData[0];
    for (my $i = 0; $i <= $#getlayerCor; $i++) {
        if (exists $getlayerCor[$i]{symbol} && $getlayerCor[$i]{symbol} eq 'r515') {
            if ($getlayerCor[$i]{'x'} ne $pnlLaserLotData[0]{'x'} && $getlayerCor[$i]{'y'} ne $pnlLaserLotData[0]{'y'}) {
                #panel中添加的剔除
                push @LaserLotData, $getlayerCor[$i];
            }
        }
    }
	undef @getlayerCor;

	if (scalar(@LaserLotData) != scalar(@arrayLaserLotData)) {
		$c->Messages("info", "数量不匹配：\n层别$chkLyr 中的laser-array-lot-cu 数量：$#arrayLaserLotData \n与层别$oplaserlayer 中的r515 数量: $#LaserLotData  不匹配，\n程序退出");
		exit 0;
	}
	
	my @check_symbol = sort seniority @arrayLaserLotData;
	my @check_drill = sort seniority @LaserLotData;
	
	foreach my $i ( 0 .. $#check_symbol) {
		my $cy_x = sprintf "%.3f",$check_symbol[$i]{'x'};
		my $cy_y = sprintf "%.3f",$check_symbol[$i]{'y'};
		my $cd_x = sprintf "%.3f",$check_drill[$i]{'x'};
		my $cd_y = sprintf "%.3f",$check_drill[$i]{'y'};
		
		if (($cy_x eq $cd_x) && ($cy_y eq $cd_y)) {
			#坐标相同
		}	
		
		# if (($check_symbol[$i]{'x'} eq $check_drill[$i]{'x'}) && ($check_symbol[$i]{'y'} eq $check_drill[$i]{'y'})) {
			# #坐标相同
		# }
		else {
			# 坐标不同
			$c->Messages("info", "层别$chkLyr 中X:$check_symbol[$i]{'x'} Y:$check_symbol[$i]{'y'}中的laser-array-lot-cu\n
						 与层别$oplaserlayer 中X:$check_drill[$i]{'x'} Y:$check_drill[$i]{'y'} 中的r515 \n
						 坐标不匹配，程序退出");
			exit 0;
		}
	}
	
	#print Dumper(\@arrayLaserLotData);
	# === 2021.08.26 给Lot排序，避免超出sr的情况,删除第一个元素
	my @sort_before; 

	for (1..$#arrayLaserLotData) {
		push(@sort_before,$arrayLaserLotData[$_]);
	}
	my @sort_after = sort seniority2 @sort_before;
	@arrayLaserLotData = ($arrayLaserLotData[0]);

	foreach (@sort_after) {
		push(@arrayLaserLotData,$_);
	}
	#print $#arrayLaserLotData . "\n";
	#print 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' . "\n";
	#print Dumper(\@arrayLaserLotData);
	#$f->PAUSE('cccccccccccccccccccccccccccccccccccccc');
    return (\@arrayLaserLotData);
}

sub seniority {
	$b->{x} <=> $a->{x}
	or $b->{y} <=> $a->{y}
}

sub seniority2 {
	$b->{angle} <=> $a->{angle}
	or $b->{y} <=> $a->{y}
	or $b->{x} <=> $a->{x}
}
sub addLotStep {
    my ($op_layer, $toplaser, $getLaserLotData) = @_;

    my @arrayLaserLotData = @$getLaserLotData;
	my $op_laser_lot_job = 'output-laser-lot';
	$c->OPEN_JOB($op_laser_lot_job);
    $f->VOF();
    $f->COM("delete_entity,job=$op_laser_lot_job,name=laser-lot,type=step");
    $f->VON();

    $f->COM("copy_entity_from_lib,job=$op_laser_lot_job,name=laser-lot,type=step,profile=none");
	
	$c->GREATE_ENTITY('step','',$op_laser_lot_job,$step_name);
    $f->AUX("set_step,name=$step_name");
    $f->AUX("set_group,group=$f->{COMANS}");
    $f->COM("units,type=mm");
	
    for (my $i = 0; $i <= $#arrayLaserLotData; $i++) {
        $f->COM("sr_tab_add,step=laser-lot,line=0,x=$arrayLaserLotData[$i]{x},y=$arrayLaserLotData[$i]{y},nx=1,ny=1,dx=0,dy=0,angle=$arrayLaserLotData[$i]{angle},flip=$arrayLaserLotData[$i]{mirror},mirror=no");
    }
    my $r515laser = 'r515' . $op_layer;
    my $r515exist = "no";

    $c->OPEN_STEP("$op_laser_lot_job", "laser-lot");
    $c->CHANGE_UNITS("mm");
    $c->DELETE_LAYER($r515laser);
    $c->CLEAR_LAYER();
    $c->AFFECTED_LAYER("$toplaser", "yes");
    $c->FILTER_RESET;
    $c->FILTER_SET_INCLUDE_SYMS("r515");
    $c->FILTER_SELECT;
    if ($c->GET_SELECT_COUNT != 0) {
        $r515exist = "yes";
        $c->SEL_COPY("$r515laser", "no", 0,);
    }
    if ($r515exist eq "yes") {
        $f->COM("matrix_layer_type,job=$op_laser_lot_job,matrix=matrix,layer=$r515laser,type=drill");
    }
    $c->CLEAR_LAYER();
}


sub deal_Lot_laser {
    #输出r515层别，并收集信息到hash中
    my ($dis_lay) = @_;
    my $LotDirec;
    our %r515cor = ();
    if (defined $r515CheckData{$dis_lay}{'lotCode'}) {
        $LotDirec = $r515CheckData{$dis_lay}{'lotCode'};
    }
    else {
        $c->Messages("info", "获取set镭射Lot号方向失败,请检查");
        return 'getDirectError';
    }

    if ($scale_position eq "中心") {
        $scale_center_x = $op_x_center;
        $scale_center_y = $op_y_center;
    }
    else {
        $scale_center_x = 0;
        $scale_center_y = 0;
    }
	my $op_laser_lot_job = 'output-laser-lot';
    $f->COM("top_tab,tab=Matrix");
    $f->AUX("set_step,name=$step_name");
    $f->AUX("set_group,group=$f->{COMANS}");
    my $r515laser = 'r515' . $dis_lay;
    my $ncsetlot = 'lot' . $dis_lay;

    $f->COM("matrix_layer_type,job=$op_laser_lot_job,matrix=matrix,layer=$r515laser,type=drill");
    $f->COM("set_subsystem,name=Nc-Manager");
    $f->COM("nc_set_current,job=$JOB,step=$step_name,layer=,ncset=");
    $f->VOF;
    $f->COM("nc_delete,layer=$r515laser,ncset=$ncsetlot");
    $f->VON;
    $f->COM("nc_create,ncset=$ncsetlot,device=misumi,lyrs=$r515laser,thickness=0");
    $f->COM("nc_set_advanced_params,layer=$r515laser,ncset=$ncsetlot,parameters=(rout_arc_as_ij=no)(out_exc_old_sr_syntax=no)");
    $f->COM("nc_set_current,job=$op_laser_lot_job,step=$step_name,layer=$r515laser,ncset=$ncsetlot");
    $f->COM("nc_set_file_params,output_path=$output_path,output_name=$JOB.$r515laser,zeroes=trailing,units=mm,tool_units=mm,nf1=3,nf2=3,decimal=no,modal_coords=no,single_sr=yes,sr_zero_set=no,repetitions=sr,incremental=no,ext_layer=drl2rt,sr_zero_layer=,ccw=no,short_lines=none,allow_no_chain_f=no,no_chain_as_slot=no,keep_table_order=no,max_arc_angle=0,comp_short_slot=no,gscale_file_name=,layer_datum=bottom_left,gscle_align_angle=0,gscl_offset_x=0,gscl_offset_y=0");
    if (${$hash{$dis_lay}}[4] eq 'no') {
        $ver = 1;
    }
    elsif (${$hash{$dis_lay}}[4] eq 'yes') {
        $ver = 7;
    }
    my $scale_x = ${$hash{$dis_lay}}[2];
    my $scale_y = ${$hash{$dis_lay}}[3];
    $f->COM("nc_register,angle=0,xoff=0,yoff=0,version=$ver,xorigin=0,yorigin=0,xscale=$scale_x,yscale=$scale_y,xscale_o=$scale_center_x,yscale_o=$scale_center_y,xmirror=no,ymirror=no");
    $f->COM("nc_set_optim,optimize=yes,iterations=5,reduction_percent=1,cool_spread=0,break_sr=no,xspeed=2540,yspeed=2540,diag_mode=45ort");
    $f->COM("nc_cre_output,layer=$r515laser,ncset=$ncsetlot");
    my $laser515_file = "$output_path/$JOB.$r515laser";
    my @lot_list = ();
    if (-e $laser515_file) {
        open(STAT, $laser515_file) or die "can't open file $laser515_file: $!";
        while (<STAT>) {
            push(@lot_list, $_);
        }
        close(STAT);
        unlink($laser515_file);
    } else {
		$c->Messages("info", "镭射LOT号未能正确输出,请检查");
			$f->PAUSE('xxxxxxxxxxxxxxxxxxxxxxx');
	}
	#$f->PAUSE('xxxxxxxxxxxxxxxxxxxxxxx');
	$f->COM("close_job,job=$op_laser_lot_job");
	
    my $t01exist = "no";
    my $m2exist = "no";
    my $body_start = "no";
    my $m25num = 0;
    foreach $tmp (@lot_list) {
        if ($tmp ne "") {
            if ($tmp eq "T0[2-9]C[0-9].*\n") {$m2exist = "yes";}
            if ($tmp =~ /T01(C0.515)/) {$t01exist = "yes";}
            if ($tmp eq "%\n") {$body_start = "yes";}
            if ($body_start eq "yes") {
                if ($tmp =~ /^T01\n$/) {
                    $search_key = $tmp;
                    chomp $search_key;
                }
                elsif ($tmp eq "M30\n" || $tmp eq "%\n") {
                }
                elsif ($tmp eq "M25\n") {
                    $m25num++;
					# 汤龙洲需求，更改镭射Lot为\$DAY&\$MACHINE&\$STAGE&\$SERIAL#3\ 2020.03.25
					# 彭勋要求，改回$LOT 2020.11.18 
                    my $add_line = "M25\n$LotDirec,\$LOT\n";
                    #my $add_line = "M25\n$LotDirec,\$DAY&\$MACHINE&\$STAGE&\$SERIAL#3\n";

                    push(@{$r515cor{"C0.515"}}, $add_line);
                }
                else {
                    push(@{$r515cor{"C0.515"}}, $tmp);
                }
            }
        }
    }
    # 检查输出的文本中是否M25指令为两个及以上
    if ($m25num > 1) {
        $c->Messages("info", "镭射LOT号输出中翻版指令M25仅能存在一个,请检查");
    }
    #$f->VOF();
    #$f->COM("delete_entity,job=$JOB,name=laser-lot,type=step");
    #$f->VON();
    $f->COM("set_subsystem,name=1-Up-Edit");
    $f->COM("top_tab,tab=Display");
}

sub merge_layer{
    my ($merge_layer,$fisrt_layer,$end_layer,$copy_pnl,$size) = @_;
    
    #&delete_layer($merge_layer);
    if ( $copy_pnl eq 'yes' ) {
		$f->COM("create_layer,layer=$merge_layer,context=misc,type=drill,polarity=positive,ins_layer=");
    }
    $f->INFO(units => 'mm', entity_type => 'job',
         entity_path => "$JOB",
         data_type => 'STEPS_LIST');
    
    my @step_list = @{$f->{doinfo}{gSTEPS_LIST}};
    
    foreach my $st(@step_list){
        if ($st eq "panel") {
			#if ($copy_pnl eq 'yes'){
				$f->COM("open_entity,job=$JOB,type=step,name=$st,iconic=no");
				$f->AUX("set_group,group=$f->{COMANS}");
				$f->COM("units,type=mm");
				
				$f->COM("clear_layers");
				$f->COM("affected_layer,mode=all,affected=no");
				
				#若1-2 1-3同时存在五代靶 以1-3的为准 20240329 by lyh
				my $copy_end_layer_dld_lot_hole="no";
				$f->COM("affected_layer,name=$end_layer,mode=single,affected=yes");
				$f->COM("filter_reset,filter_name=popup");
				$f->COM("filter_set,filter_name=popup,update_popup=no,include_syms=r501\;r520\;r3175");
				$f->COM("filter_area_strt");
				$f->COM("filter_area_end,layer=,filter_name=popup,operation=select,area_type=none,inside_area=no,intersect_area=no");
				if ($c->GET_SELECT_COUNT > 0) {						
					$copy_end_layer_dld_lot_hole="yes";	
					if ($fisrt_layer eq $end_layer){
						$f->COM("sel_copy_other,dest=layer_name,target_layer=$merge_layer,size=0");
					}
				}
				
				$f->COM("clear_layers");
				$f->COM("affected_layer,mode=all,affected=no");
				# --panel将第一层copy即可
				$f->COM("affected_layer,name=$fisrt_layer,mode=single,affected=yes");
				$f->COM("filter_reset,filter_name=popup");
				if ($size > 0){
					#周涌通知 需要排除dld层，lot号，对位孔，不合并			
					$f->COM("filter_set,filter_name=popup,update_popup=no,exclude_syms=r501\;r520\;r3175");
				}else{
					if ($copy_end_layer_dld_lot_hole eq "yes"){
						$f->COM("filter_set,filter_name=popup,update_popup=no,exclude_syms=r501\;r520\;r3175");
					}
				}
				
				$f->COM("sel_ref_feat,layers=$merge_layer,use=filter,mode=disjoint,pads_as=shape,f_types=line\;pad\;surface\;arc\;text,polarity=positive\;negative,include_syms=,exclude_syms=");
				#增加跟copy过去的不接触 否则会重复拷贝板边孔 20230308 by lyh
				if ($c->GET_SELECT_COUNT > 0) {					
					$f->COM("sel_copy_other,dest=layer_name,target_layer=$merge_layer,size=$size");
				}
				$f->COM("affected_layer,name=$fisrt_layer,mode=single,affected=no");
			#}
        }else{
            $f->COM("open_entity,job=$JOB,type=step,name=$st,iconic=no");
            $f->AUX("set_group,group=$f->{COMANS}");
            
            $f->COM("clear_layers");
            $f->COM("affected_layer,mode=all,affected=no");
            $f->COM("units,type=mm");
            #my $size = 1;
            # --其他symbol有孔都要copy
            $f->COM("affected_layer,name=$fisrt_layer,mode=single,affected=yes");
            #$f->COM("sel_copy_other,dest=layer_name,target_layer=$merge_layer");
			$f->COM("sel_copy_other,dest=layer_name,target_layer=$merge_layer,size=$size");
            $f->COM("affected_layer,name=$fisrt_layer,mode=single,affected=no");
			$f->COM("affected_layer,name=$merge_layer,mode=single,affected=yes");
			$f->COM("filter_set,filter_name=popup,update_popup=no,include_syms=r516");
			$f->COM("filter_area_strt");
			$f->COM("filter_area_end,layer=,filter_name=popup,operation=select,area_type=none,inside_area=no,intersect_area=no");
			if ($c->GET_SELECT_COUNT > 0) {
				$f->COM("sel_change_sym,symbol=r515,reset_angle=no");
			} 
			$f->COM("affected_layer,name=$merge_layer,mode=single,affected=no");
			
=head
            # --拷贝第二层

            $f->INFO(units => 'mm', entity_type => 'layer',
                entity_path => "$JOB/$st/$fisrt_layer",
                data_type => 'SYMS_HIST');
            my @symbols_fisrt = @{$f->{doinfo}{gSYMS_HISTsymbol}};
            
            $f->COM("affected_layer,name=$end_layer,mode=single,affected=yes");
            $f->INFO(units => 'mm', entity_type => 'layer',
                entity_path => "$JOB/$st/$end_layer",
                data_type => 'SYMS_HIST');
            my @symbols_end = @{$f->{doinfo}{gSYMS_HISTsymbol}};
            
            foreach my $symbol(@symbols_end){
                my $size = 1;
                # --周涌要求所有类似s1-3层孔径都加大1  AresHe 2022.3.10
                #foreach my $fisrt_symbol(@symbols_fisrt){
                #    if ($fisrt_symbol eq $symbol) {
                #        $size = 1;
                #    }
                #}
                
                $f->COM("filter_reset,filter_name=popup");
                $f->COM("filter_set,filter_name=popup,update_popup=no,include_syms=$symbol");
                $f->COM("filter_area_strt");
                $f->COM("filter_area_end,layer=,filter_name=popup,operation=select,area_type=none,inside_area=no,intersect_area=no");
                if ($c->GET_SELECT_COUNT > 0) {
                    $f->COM("sel_copy_other,dest=layer_name,target_layer=$merge_layer,size=$size");
                }
            }
=cut
			
            $f->COM("clear_layers");
            $f->COM("affected_layer,mode=all,affected=no");
            $f->COM("filter_reset,filter_name=popup");
            $f->COM("editor_page_close");
        }
    }
}

sub delete_layer{
    my @layer = @_;
    foreach my $bak(@layer){
        $f->INFO(units => 'mm', entity_type => 'layer',
            entity_path => "$JOB/$panel_step/$bak",
            data_type => 'EXISTS');
        if ($f->{doinfo}{gEXISTS} eq "yes") {
            $f->COM("delete_layer,layer=$bak");
        }
    }
}

#检测skipvia孔是否跟中间层接触 20240712 
#http://192.168.2.120:82/zentao/story-view-6834.html
sub check_skipvia_touch_mid_layer {
	my ($start_index,$end_index,$laser_drill) = @_;
	my $stepname="edit";
    $c->OPEN_STEP("$JOB", "$stepname");
    $c->CHANGE_UNITS("mm");
	my $mid_dld_index= ($start_index < $end_index) ? $end_index - 1 : $end_index + 1 ;
	for (my $i = 1; $i < 10; $i++){
		my $mid_layer_index = ($start_index < $end_index) ? $start_index+$i: $start_index-$i;
		if ($mid_layer_index == $end_index){			
			last;
		}
		&delete_layer("l".$mid_layer_index."_tmp");
		$c->COM("copy_layer,source_job=$JOB,source_step=$stepname,source_layer=l${mid_layer_index},dest=layer_name,dest_layer=l${mid_layer_index}_tmp,mode=replace,invert=no");
		$c->COM("clear_layers");
		$c->COM("affected_layer,mode=all,affected=no");
		$c->COM("affected_layer,name=l${mid_layer_index}_tmp,mode=single,affected=yes");
		$c->COM("sel_contourize,accuracy=25.4,break_to_islands=yes,clean_hole_size=76.2,clean_hole_mode=x_and_y");
		$c->COM("sel_ref_feat,layers=$laser_drill,use=filter,mode=touch,pads_as=shape,f_types=line\;pad\;surface\;arc\;text,polarity=positive\;negative,include_syms=,exclude_syms=");
		if ($c->GET_SELECT_COUNT > 0) {		
			#$c->PAUSE("DD");
			&delete_layer("l".$mid_layer_index."_tmp");
			return "l".$mid_dld_index;
		}	
		&delete_layer("l".$mid_layer_index."_tmp");		
	}
	return 	"l".$end_index;
}
#反面镭射检测
sub check_reverse_laser_skipvia_touch_mid_layer {
	my ($start_index,$end_index,$laser_drill) = @_;
	my $stepname="edit";
    $c->OPEN_STEP("$JOB", "$stepname");
    $c->CHANGE_UNITS("mm");
	my $mid_dld_index= ($start_index < $end_index) ? $end_index - 1 : $end_index + 1 ;
	for (my $i = 1; $i < 10; $i++){
		my $mid_layer_index = ($start_index < $end_index) ? $start_index+$i: $start_index-$i;
		if ($mid_layer_index == $end_index){			
			last;
		}
		&delete_layer("l".$mid_layer_index."_tmp");
		$c->COM("copy_layer,source_job=$JOB,source_step=$stepname,source_layer=l${mid_layer_index},dest=layer_name,dest_layer=l${mid_layer_index}_tmp,mode=replace,invert=no");
		$c->COM("clear_layers");
		$c->COM("affected_layer,mode=all,affected=no");
		$c->COM("affected_layer,name=l${mid_layer_index}_tmp,mode=single,affected=yes");
		$c->COM("sel_contourize,accuracy=25.4,break_to_islands=yes,clean_hole_size=76.2,clean_hole_mode=x_and_y");
		$c->COM("sel_ref_feat,layers=$laser_drill,use=filter,mode=touch,pads_as=shape,f_types=line\;pad\;surface\;arc\;text,polarity=positive\;negative,include_syms=,exclude_syms=");
		if ($c->GET_SELECT_COUNT > 0) {		
			#$c->PAUSE("DD");
			&delete_layer("l".$mid_layer_index."_tmp");
			return "change";
		}	
		&delete_layer("l".$mid_layer_index."_tmp");		
	}
	return 	"no_change";
}


sub check_dld_layer{
    my ($dld_layer,$signal_layer) = @_;
    $f->INFO(units => 'mm', entity_type => 'layer',
            entity_path => "$JOB/$panel_step/$dld_layer",
            data_type => 'EXISTS');
    unless ($f->{doinfo}{gEXISTS} eq "yes") {
        $c->Messages("info", "检测到'$dld_layer'层不存在!,程序退出!");
        exit;
    }
    
    $f->INFO(units => 'mm', entity_type => 'layer',
            entity_path => "$JOB/$panel_step/$signal_layer",
            data_type => 'EXISTS');
    unless ($f->{doinfo}{gEXISTS} eq "yes") {
        $$c->Messages("info", "检测到'$signal_layer'层不存在!,程序退出!");
        exit;
    }
    
    $f->INFO(units => 'mm', entity_type => 'layer',
         entity_path => "$JOB/$panel_step/$dld_layer",
         data_type => 'SYMS_HIST',
         options => "break_sr");
    my @symbol_list = @{$f->{doinfo}{gSYMS_HISTpad}};
    
    $f->COM("clear_layers");
    $f->COM("affected_layer,mode=all,affected=no");
    
    
    my $dld_layer_tmp = $dld_layer . '__________tmp';
    my $dld_layer_tmp2 = $dld_layer . '__________tmp2';
    &delete_layer($dld_layer_tmp);
    &delete_layer($dld_layer_tmp2);
    
    $f->COM("affected_layer,name=$dld_layer,mode=single,affected=yes");
    $f->COM("sel_copy_other,dest=layer_name,target_layer=$dld_layer_tmp");
    $f->COM("affected_layer,mode=all,affected=no");
    foreach my $next(1..$symbol_list[0]){
        my ($dld_x1,$dld_y1,$sx1,$sy1);
        $f->COM("affected_layer,mode=all,affected=no");
        $f->COM("affected_layer,name=$dld_layer_tmp,mode=single,affected=yes");
        $f->COM("filter_reset,filter_name=popup");
        $f->COM("sel_layer_feat,operation=select,layer=$dld_layer_tmp,index=$next");
        if ($c->GET_SELECT_COUNT > 0) {
            $f->INFO(units => 'mm', entity_type => 'layer',
                entity_path => "$JOB/$panel_step/$dld_layer_tmp",
                data_type => 'FEATURES',
                options => "select");
            my $feat_path = '/tmp/dld_symbol_tmp___';
            $f->COM("info,args=-t layer -e $JOB/$panel_step/$dld_layer_tmp -m script -d FEATURES -o select,out_file=$feat_path,write_mode=replace,units=mm");
            open(DLDFILE, "<$feat_path")  or die "$!";
            my @content = <DLDFILE>;
            close DLDFILE;
            shift @content;
            foreach my $line(@content){
                if ($line =~ /^#P/) {
                    my @tmp = split(' ',$line);
                    $dld_x1 = sprintf("%.3f",$tmp[1]);
                    $dld_y1 = sprintf("%.3f",$tmp[2]);
                    print ("$dld_x1 $dld_y1\n");
                }
            }
            
            &delete_layer($dld_layer_tmp2);
            $f->COM("sel_move_other,target_layer=$dld_layer_tmp2");
            
            $f->COM("affected_layer,name=$dld_layer_tmp,mode=single,affected=no");
            $f->COM("affected_layer,name=$signal_layer,mode=single,affected=yes");
            
            $f->COM("filter_set,filter_name=popup,update_popup=no,include_syms=sh-ldi");
            $f->COM("sel_ref_feat,layers=$dld_layer_tmp2,use=filter,mode=touch,pads_as=shape,f_types=line\;pad\;surface\;arc\;text,polarity=positive\;negative,include_syms=,exclude_syms=");
            if ($c->GET_SELECT_COUNT > 0) {
                $f->INFO(units => 'mm', entity_type => 'layer',
                    entity_path => "$JOB/$panel_step/$signal_layer",
                    data_type => 'FEATURES',
                    options => "select");
                my $feat_path1 = '/tmp/signal_symbol_tmp___';
                $f->COM("info,args=-t layer -e $JOB/$panel_step/$signal_layer -m script -d FEATURES -o select,out_file=$feat_path1,write_mode=replace,units=mm");
                open(DLDSYMBOL, "<$feat_path1")  or die "$!";
                my @sym_content = <DLDSYMBOL>;
                close DLDSYMBOL;
                shift @sym_content;
                foreach my $line(@sym_content){
                    if ($line =~ /^#P/) {
                        my @tmp = split(' ',$line);
                        $sx1 = sprintf("%.3f",$tmp[1]);
                        $sy1 = sprintf("%.3f",$tmp[2]);
                        
                        print ("$sx1 $sy1\n");
                    }
                }
            }
            
            if ($dld_x1 and $dld_y1) {
                unless ($sx1 and $sy1) {
                    $c->Messages("info", "$dld_layer 检测到x:$dld_x1,y:$dld_y1 位置没有对应dld symbol设计,程序退出!");
                    exit;
                }
                
                if  ($dld_x1 != $sx1 || $dld_y1 != $sy1) {
                    $c->Messages("info", "$dld_layer 检测到x:$dld_x1,y:$dld_y1 位置dld symbol与孔位不符,程序退出!");
                    exit;
                }
            }
        }
    }
    &delete_layer($dld_layer_tmp);
    &delete_layer($dld_layer_tmp2);
    
    $f->COM("clear_layers");
    $f->COM("affected_layer,mode=all,affected=no");
    $f->COM("filter_reset,filter_name=popup");
}

__END__
2019.11.05
版本：V1.5
作者：Chao.Song:
1.从HDI Inplan获取雷射参数；
2.输出从X方向镜像，改为Y方向镜像（第四象限改为第七象限）;

2019.11.29
版本：V1.6
作者：Chao.Song:
1.从HDI Inplan获取雷射参数,无雷射参数时使用None。


2019.12.11
版本：V1.7
作者：Chao.Song:
1.从HDI Inplan获取雷射参数,增加内层芯板为Core的判断;
2.为None时带上MI参数

2019.12.12
版本：V1.8
作者：Chao.Song:
1.修改从HDI inplan获取雷射参数的判断； 由not defined 更改为 ！ defined；
2.更改不在列表中的情况为Null3，需验证结果。

2019.12.25
版本:V1.9
作者：宋超
1.检查panel S&R中set是否连续；
2.L1层底铜与孔坐标是否重合检测；
3.首个拼版的laserlot角度判断；
4.dld层别0.045 数量防呆。

2019.12.26
版本：V2.0
作者：Songchao
仅升级大版本

2019.12.28
版本：V2.1
作者：SongChao
1.修改支持正面镭射不存在时反面镭射输出;
2.增加镭射层超出两把刀防呆，目前工艺不支持,脚本支持输出；
3.防呆旧镭射层别名；

2019.12.30
版本：V2.2
作者：SongChao
1.防呆set上单层仅能设计一个Lot号。

2020.01.06
版本：V2.3
作者：SongChao
1.镜像拼板不增加Lot号。料号：407-339A1

2020.01.09
版本：V2.3.1
作者：SongChao
1.增加反面LOT号添加方向防呆。Bug料号：561-147A3


版本：V2.3.2
2020.02.19
1.更改，仅edit step时脚本报错的情况。 Bug料号：B20-001A3
2.查询是否连续中增加判断set step是否。

2020.02.23 #2020.01.23开始，未上线中间穿插了V2.3.2版本的更改
版本：V2.4
作者：SongChao
1.应对情况：set在panel中为阴阳拼版：
1.0 确认Set中是否有添加Lot号；
1.1 以四层板为例，如果客户设计s1-2，则对称生成s4-3层别；（自动生成）
1.2 在set中的Lot号应添加于L1层；增加检测，set中的添加是否为L1层，如果是则检测中心是否一致。
1.3 在panel中Lot号生成L4层（s4-3中r515有Lot号）
1.4 阴阳拼版，板边需预添加r515的镭射lot标识孔，可以跳过set内的添加检测步骤judgeM97orM98Direct，而非阴阳拼版的板边则不需要添加。
2.增加阴阳拼版LOT号添加及输出支持。（应用板边添加模块，使用模块输出的方式实现）
2.1 panel中应设计laser-array-lot-cu 板边中添加此symbol，且应方向正确，后续取此坐标用于添加模块coupon；
2.2 输出过程，panel中添加临时coupon用于输出，输出结束后删除，（可考虑panel边也添加此coupon）

2020.03.25
版本：V2.5
作者：宋超
1.汤龙洲需求，更改laser lot 由$LOT 改成 $DAY&$MACHINE&$STAGE&$SERIAL#3   http://192.168.2.120:82/zentao/file-read-2557.png
2.增加日志写入

2020.05.19
版本：V2.6
作者：李家兴
1.芯板镭射，复制板内镭射

2020.06.10
版本：V2.7
作者：宋超
1.镭射lot号输出过程中有异常未输出，软件未终止；
2.更改回读的钻带程序，lot号孔径更改为0.2mm，便于检查。

2020.09.09
版本：V2.8
作者：宋超
1.增加T21钻孔处理后的检查，应该根据坐标位置归类后未4个，如果因为获取拼版尺寸原因无法获取，则程序退出。

2020.09.24
版本：V2.9
作者：李家兴
1.芯板镭射由重复刀改为正反面各输出一次，story-view-2042

2020.11.18
版本：V3.0
作者：宋超
1.更改镭射LOT号 更改laser lot  $DAY&$MACHINE&$STAGE&$SERIAL#3 改回$LOT
http://192.168.2.120:82/zentao/story-view-2321.html

2020.03.30
版本：V3.0.1
作者：宋超
1.InPLan参数表更新，增加尾数为X2,X3的匹配;
http://192.168.2.120:82/zentao/story-view-2768.html

2021.08.23(上线日期)
版本未升
作者：何瑞鹏 Note by Song
1.反面镭射输出后回读自动拉正 

2021.9.1
版本：V3.0.2
作者：何瑞鹏
1.制作人需把分割对应层制作好(分割层：s1-2-fg)，必须按钻咀尾数大小分割对应区域。分割规则依工艺要求
2.输出界面选择分割模式:不分割，2分割，4分割
3.程序自动生成并输出资料。
http://192.168.2.120:82/zentao/story-view-3448.html

2021.9.16
版本：V3.0.3
作者：何瑞鹏
1.新增全自动分割功能,参考l1线路层r0(竖=.fiducial_name=300.trmv) (横=.fiducial_name=300.trmh)
2.fltatten分割备份层时,只保留r520、以及钻咀在3-5mil之间的孔(规则:周涌提供)

2021.09.23 (上线日期）
版本：V3.1.0
作者：宋超
1.更改镭射lot号的输出，判断为常规类型还是特殊类型(特殊类型需板边上添加一个模块)
2.镭射输出卡关，参数为None，不可输出 http://192.168.2.120:82/zentao/story-view-3422.html

2021.9.28
版本：V3.1.1
作者：何瑞鹏
1.镭射2分分割,新增纵、横方向自动判断分割
2.来源需求:http://192.168.2.120:82/zentao/story-view-3554.html

2021.10.11
版本：V3.1.2
作者：何瑞鹏
1.镭射分割资料,新增自动回读功能
2.来源需求:http://192.168.2.120:82/zentao/story-view-3575.html

2021.11.1
版本：V3.1.3
作者：何瑞鹏
1.检查分割区域刀具,不足3把刀时给出提醒
2.来源需求:http://192.168.2.120:82/zentao/story-view-3628.html
3.新增系统自动排查检测机台孔:0.501 lot号孔:0.515 五代靶孔:0.520 定位孔:3.175之外孔是否存在,不存在将提示用户镭射孔为空

2021.11.12
版本：V3.2.0
作者：宋超
1.兼容镭射设计准则中的um单位的镭射参数，此部分从inplan获取
http://192.168.2.120:82/zentao/story-view-3687.html

2021.11.26
版本：V3.2.1
作者：何瑞鹏
1.支持正常资料两把镭射刀
2.支持类似1通2,1通3或12通11,12通10合并层输出
3.支持合并层分割输出(2、4分割)
4.支持多把刀,合并层分割输出
5.注意事项1:当多把镭射刀时,必须保证不同T之间差值>=4,包括同层或合并层输出(如:s1-2 镭射孔是:r76 s1-3镭射钻孔是:r80),否则分割后异常。
6.注意事项2:合并层输出跨层制作资料时,单元内仅保留有效镭射孔即可,不需添加lot号,否则报错(如:s1-2工艺边添加lot, s1-3不需添加)
7.来源需求:http://192.168.2.120:82/zentao/story-view-3674.html

8.新增镭射输出增加dld层的孔与线路层的靶是否在同一中心检测
9.来源需求:http://192.168.2.120:82/zentao/story-view-3697.html

2021.11.26
版本：V3.2.2
作者：何瑞鹏
1.镭射输出两把T只提示,不禁止
2.参数为空不允许输出
3.2021.12.17 1067+1086-152+178+203UM 增加1~4种PP及1-4种孔径 ===


2022.05.18
版本：V3.2.5
作者：宋超
1. 对比料号中的Lot设计与Inplan中的Lot设计：http://192.168.2.120:82/zentao/story-view-4205.html
2. 界面增加跳钻选项，用于工艺可能的跳钻测试；(此时需所有需要跳钻的孔为同一种属性，避免S&R Table中分刀)
3. 阴阳拼版的Lot输出处理。A57-137B1


2022.08.04
更改程序路径    system("perl /incam/server/site_data/scripts/hdi_scr/Output/Laser/show_drl_data.pl");

2022.10.28
版本：V3.2.6
作者：宋超
1.对比ERP数据中镭射,如果不一致则提醒;http://192.168.2.120:82/zentao/story-view-4617.html
2.获取inplan中的镭射参数,如果是s-2-3镭射镭射,则带入参数;http://192.168.2.120:82/zentao/story-view-4804.html

2022.12.09
版本：V3.2.6
作者：陆元会
1.输出镭射增加一孔打5遍及自动跳钻;http://192.168.2.120:82/zentao/story-view-4857.html

2023.02.09
版本：V3.2.6
作者：陆元会
1.输出镭射增加识别‘起始层为同一层的镭射时，都合并成一个钻带’;http://192.168.2.120:82/zentao/story-view-5108.html

2023.02.22
版本：V3.2.8
作者：宋超
1.对比ERP数据中镭射,如果不一致则报红;http://192.168.2.120:82/zentao/story-view-4617.html
2.合并钻带时进行分刀，分刀大小为终止层-起始层 + 1,如孔径为102 层别s1-4分刀大小为102 + 4 - 1 + 1;

2023.03.15 上线日期 2023.03.23
版本：V3.2.9
作者：宋超
1.8mil或者10mil的孔在一条钻带中需设计单一T;http://192.168.2.120:82/zentao/story-view-5220.html
2.当panel边添加laser lot时,判定为特殊设计；料号：SA2806GB071A2;
3.允许板内无正式孔设计，输出镭射。
4.板边所有孔合并,#增加跟copy过去的不接触 否则会重复拷贝板边孔 20230308 by lyh

