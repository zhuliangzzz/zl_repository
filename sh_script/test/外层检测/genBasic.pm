#!/usr/bin/perl
#/************************************
#
# 程序名称: genBasic.pm
# 功能描述: Genesis命令全集
# 开发小组: Vgt.pcb 系统开发部-程序课
#	  作者: Jeff(wzh)&Chuang.liu
# 开发日期: 2015.01.28
#   版本号: 3.1
#
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
package genBasic;

$VERSION = 3.1;

# --导入模块
use strict;
use warnings;
use lib "$ENV{GENESIS_EDIR}/all/perl";
use Genesis;
use Exporter;
our @ISA = qw(Exporter);
my @flip_steps;
my %flip_hash;

# --初始化模块
my $f = Genesis::->new();

# --程序名称
my $appName = "genBasic";

#/************************
# 函数名: AFFECTED_LAYER
# 功  能: 打开和关闭影响层
# 参  数: NONE
# 返回值: NONE
#************************/
sub AFFECTED_LAYER
{
    shift;
    my ($name,$affected)=@_;
    $f->COM('affected_layer', name => "$name", mode => 'single', affected => "$affected");
}

#/************************
# 函数名: ADD_PAD
# 功  能: 添加Pad
# 参  数: NONE
# 返回值: NONE
#************************/
sub ADD_PAD
{
    shift;
    my ($add_x,$add_y,$symbol,$pol,$attr,$angle,$mir,$nx,$ny,$dx,$dy,$xscale,$yscale)=@_;
    $pol="positive" if(not defined $pol);
    $attr="no"      if (not defined $attr);
    $angle="0"      if (not defined $angle);
    $mir="no"       if (not defined $mir);
    $nx="1"         if (not defined $nx);
    $ny="1"         if (not defined $ny);
    $dx="0"         if (not defined $dx);
    $dy="0"         if (not defined $dy);
    $xscale="1"     if (not defined $xscale);
    $yscale="1"     if (not defined $yscale); 
    $f->COM('add_pad', attributes => "$attr",
                     x            => "$add_x",
                     y            => "$add_y",
                     symbol       => "$symbol",
                     polarity     => "$pol",
                     angle        => "$angle",
                     mirror       => "$mir",
                     nx           => $nx,
                     ny           => $ny,
                     dx           => $dx,
                     dy           => $dy,
                     xscale       => $xscale,
                     yscale       => $yscale);
}

#/************************
# 函数名: ADD_PAD_SINGLE
# 功  能: 添加单个Pad
# 参  数: NONE
# 返回值: NONE
#************************/
sub ADD_PAD_SINGLE
{
    shift;
    my ($add_x,$add_y,$symbol,$pol,$attr,$angle,$mir)=@_;
    $pol="positive" if(not defined $pol);
    $attr="no"      if (not defined $attr);
    $angle="0"      if (not defined $angle);
    $mir="no"       if (not defined $mir);
    $f->COM('add_pad', attributes => "$attr",
                     x            => "$add_x",
                     y            => "$add_y",
                     symbol       => "$symbol",
                     polarity     => "$pol",
                     angle        => "$angle",
                     mirror       => "$mir",
                     nx           => 1,
                     ny           => 1,
                     dx           => 0,
                     dy           => 0,
                     xscale       => 1,
                     yscale       => 1);
}

#/************************
# 函数名: ADD_SURFACE
# 功  能: 添加Surface
# 参  数: NONE
# 返回值: NONE
#************************/
sub ADD_SURFACE
{
    shift;
    my ($add_sx,$add_sy,$add_ex,$add_ey,$pol,$attr)=@_;
    $pol="positive" if(not defined $pol);
    $attr="no"      if (not defined $attr);
    $f->COM('add_surf_strt', surf_type => "feature");
    $f->COM('add_surf_poly_strt', x => "$add_sx", y => "$add_sy");
    $f->COM('add_surf_poly_seg', x => "$add_sx", y => "$add_ey");
    $f->COM('add_surf_poly_seg', x => "$add_ex", y => "$add_ey");
    $f->COM('add_surf_poly_seg', x => "$add_ex", y => "$add_sy");
    $f->COM('add_surf_poly_seg', x => "$add_sx", y => "$add_sy");
    $f->COM('add_surf_poly_end');
    $f->COM('add_surf_end', attributes => "$attr", polarity => "$pol");
}

#/****************************
# 函数名: COM
# 功  能: COMMOND命令
# 参  数: 执行命名
# 返回值: 执行结果
#****************************/
sub COM
{
    shift;
    my $commond=shift;
    $f->VOF();
    $f->COM("$commond");
    my $Status=$f->{STATUS};
    $f->VON();
    # --返回
    return $Status;
}

#/****************************
# 函数名: CLOSE_JOB
# 功  能: 关闭料号
# 参  数: 1,料号名
# 返回值: NONE
#****************************/
sub CLOSE_JOB
{
    shift;
    my $job = shift;
    $f->VOF();
    $f->COM('close_job',job=>$job);
    $f->VON();
    $f->VOF();
    $f->COM("check_inout,mode=in,type=job,job=$job");
    $f->VON();
}

#/****************************
# 函数名: CLEAR_LAYER
# 功  能: 清除显示层和影响层命令
# 参  数: NONE
# 返回值: NONE
#****************************/
sub CLEAR_LAYER
{
    shift;
    $f->COM('clear_layers');
    $f->COM('affected_layer', mode => 'all', affected => 'no');
}

#/************************
# 函数名: CLEAR_FEAT
# 功  能: 清除选中实体和高亮
# 参  数: NONE
# 返回值: NONE
#************************/
sub CLEAR_FEAT
{
    shift;
    $f->COM('clear_highlight');
    $f->COM('sel_clear_feat');
}

#/************************
# 函数名: CLOSE_STEP
# 功  能: 关闭Step
# 参  数: NONE
# 返回值: NONE
#************************/
sub CLOSE_STEP
{
    shift;
    $f->VOF();
    $f->COM('editor_page_close');
    $f->VON();
}


#/************************
# 函数名: CHANGE_UNITS
# 功  能: 改变当前单位
# 参  数: NONE
# 返回值: NONE
#************************/
sub CHANGE_UNITS 
{
    shift;
    my $types = shift;
    $f->COM('units',type=> $types);
}

#/************************
# 函数名: CREATE_LAYER
# 功  能: 创建层别
# 参  数: NONE
# 返回值: NONE
#***********************/
sub CREATE_LAYER
{
    shift;
    my ($creat_name,$ins_layer,$context,$type,$polarity,$location) = @_;
    $ins_layer=""              if (not $ins_layer);
    $context = "misc"         if (not $context);
    $type = "signal"         if (not $type);
    $polarity="positive"    if (not $polarity);
    $location="after"        if (not $location);
    my $JOB =  $ENV{JOB};
    my $STEP = $ENV{STEP};
    if ($^O eq 'linux' && $context ne 'misc') {
        # $STEP不存在也没关系，因为循环处理了当前料号中所有step
        # incam和incampro环境下，阴阳拼在创建board层别时，会报错，
        # 需要先释放依赖关系,创建完层别后再重建依赖关系
        &GET_FLIP_STEP($JOB);
        # 释放依赖关系
        &STEP_SUSPEND($JOB,'yes',@flip_steps);
    $f->COM('create_layer', layer => $creat_name, context => $context, type => $type,
            polarity => $polarity, ins_layer => "$ins_layer",location=>$location);
        # 重建依赖关系
        &STEP_SUSPEND($JOB,'no',@flip_steps);
        # 将工作step复原
        &OPEN_STEP('no',$JOB,$STEP);
    } else {
        $f->COM('create_layer', layer => $creat_name, context => $context, type => $type,
                 polarity => $polarity, ins_layer => "$ins_layer", location => $location);
    }
}

#/************************
# 函数名: GET_FLIP_STEP
# 功  能: 找出有镜像的step
# 参  数: NONE
# 返回值: NONE
#***********************/
sub GET_FLIP_STEP
{
    my ($JOB) = @_;
    # 循环处理所有step,这样就不必使用递归，而且在edit中加borad层也不会报错
    $f->INFO(entity_type => 'job', entity_path => "$JOB", data_type => 'STEPS_LIST');
    my @gSTEPS_LIST = @{$f->{doinfo}{gSTEPS_LIST}};
    foreach my $content_step (@gSTEPS_LIST) {
        $f->INFO(entity_type => 'step', entity_path => "$JOB/$content_step", data_type => 'SR', parameters => "flip+step");
        my @gSRstep = @{$f->{doinfo}{gSRstep}};
        my @gSRflip = @{$f->{doinfo}{gSRflip}};
        # 寻找出有镜像的step，并push到filp_steps数组中
        for (my $num = 0; $num < @gSRstep; $num++) {
            if (exists($flip_hash{$gSRstep[$num]})) {
                # 如果hash键中已经存在当前step
                if ($gSRflip[$num] eq 'yes') {
                    # 如果当前键的值为'yes'
                    $flip_hash{$gSRstep[$num]} = $gSRflip[$num];
                    # Incam释放关系只能在edit释放，如果panel阴阳拼版，释放set会报错! AresHe 2019-12-11
                    if ($gSRstep[$num] eq 'set'){
                        $gSRstep[$num] = 'edit';
                        push(@flip_steps, $gSRstep[$num]);
                    }else{
                        push(@flip_steps, $gSRstep[$num]);
                    }
                }
            }
            else {
                # 如果hash键中不存在当前step
                $flip_hash{$gSRstep[$num]} = $gSRflip[$num];
            }
        }
    }
}

#/************************
# 函数名: STEP_SUSPEND
# 功  能: 释放/添加关系
# 参  数: NONE
# 返回值: NONE
#***********************/
sub STEP_SUSPEND
{
    my ($JOB,$suspend,@steps) = @_;
    foreach my $step (@steps) {
        &OPEN_STEP('no',$JOB,$step);
        $f->COM("matrix_suspend_symmetry_check,job=$JOB,matrix=matrix,suspend=$suspend");
        &CLOSE_STEP();
    }
}

#/************************
# 函数名: CLIP_AREA
# 功  能: 削除指定区域内容
# 参  数: NONE
# 返回值: NONE
#***********************/
sub CLIP_AREA
{
    shift;
    my($area,$inout,$margin,$feat_types)=@_;
    $feat_types="line;pad;surface;arc;text" if(not $feat_types);
    
    $f->COM('clip_area_strt');
    $f->COM('clip_area_end', layers_mode => "affected_layers",
                           layer       => "",
                           area        => "$area",
                           area_type   => "rectangle",
                           inout       => "$inout",
                           contour_cut => "yes",
                           margin      => "$margin",
                           feat_types  => "line;pad;surface;arc;text");
}

#/************************
# 函数名: CUR_ATR_SET
# 功  能: 物件属性定义
# 参  数: reset传入0或1
# 返回值: NONE
#***********************/
sub CUR_ATR_SET
{
    shift;
    my($attr,$text,$reset)=@_;
    ###reset传入0或1
    if ($reset) {
        $f->COM('cur_atr_reset');
    }    
    if (not $text) {
        $f->COM('cur_atr_set', attribute => "$attr");
    }else{
        $f->COM('cur_atr_set', attribute => "$attr", text => "$text");
    }    
}

#/************************
# 函数名: CUR_ATR_RESET
# 功  能: 物件属性重置
# 参  数: NONE
# 返回值: NONE
#***********************/
sub CUR_ATR_RESET
{
    shift;
    $f->COM('cur_atr_reset');
}

#/************************
# 函数名: COMPARE_LAYERS
# 功  能: 两层物体比对
# 参  数: NONE
# 返回值: NONE
#***********************/
sub COMPARE_LAYERS
{
    shift;
    my ($layer_1,$job2,$step2,$layer_2)=@_;
    my $map_layer="compare_layer++";
    $f->COM('compare_layers', layer1        => "$layer_1",
                            job2          => "$job2",
                            step2         => "$step2",
                            layer2        => "$layer_2",
                            layer2_ext    => "",
                            tol           => "25.4",
                            area          => "global",
                            consider_sr   => "yes",
                            ignore_attr   => "",
                            map_layer     => $map_layer,
                            map_layer_res => 5080);
    my $result=$f->{COMANS};
    ###删除结果层
    $f->COM('delete_layer', layer => $map_layer);# if ($result == 0);
    return $result;
}


#/************************
# 函数名: COPY_ENTITY
# 功  能: COPY Step or Symbol
# 参  数: NONE
# 返回值: NONE
#***********************/
sub COPY_ENTITY
{
    shift;
    my ($type,$source_job,$source_name,$dest_job,$dest_name,$dest_db)=@_;    
    $dest_db="" if(not $dest_db);
    $f->COM('copy_entity',     type             => "$type",
                            source_job         => "$source_job",
                            source_name     => "$source_name",
                            dest_job         => "$dest_job",
                            dest_name         => "$dest_name",
                            dest_database     => "$dest_db");
}

#/************************
# 函数名:  COPY_LAYER
# 功  能:  COPY LAYER
# 参  数:  NONE
# 返回值:  NONE
#***********************/
sub COPY_LAYER
{
    shift;
    my ($source_job,$source_step,$source_layer,$dist_layer)=@_;
    $source_job="" if(not $source_job);
    $f->COM('copy_layer',   source_job      =>  "$source_job",
                            source_step     =>  "$source_step",
                            source_layer    =>  "$source_layer",
                            dest            =>  "layer_name",
                            dest_layer      =>  "$dist_layer",
                            mode            =>  "replace",
                            invert          =>  "no",
                            copy_notes      =>  "no",
                            copy_attrs      =>  "new_layers_only");
}

#/************************
# 函数名: CHECK_LAYER_FEATURES
# 功  能: 检测该层是否存在物体
# 参  数: NONE
# 返回值: yes or no
#***********************/
sub CHECK_LAYER_FEATURES
{
    shift;
    my ($job,$step,$layer)=@_;
    my $tmp_file=(-d "C:/tmp") ? "C:/tmp/fea.$$" : "/tmp/fea.$$";
    $f->COM('info', args => "-t layer -e $job/$step/$layer -m display -d FEATURES",
            out_file => "$tmp_file", write_mode => "replace", units => "mm");
    my @info=`cat $tmp_file`;
    unlink $tmp_file;
    
    ###返回当前层是否存在物体
    if (@info > 1) {
        return 'yes';
    }else{
        return 'no';
    }
}

#/************************
# 函数名: DELETE_LAYER
# 功  能: 删除层
# 参  数: NONE
# 返回值: NONE
#***********************/
sub DELETE_LAYER
{
    shift;
    my($layer)=@_;
    $f->VOF;
    $f->COM('delete_layer', layer => $layer);
    $f->VON;
}

#/************************
# 函数名: Del_WK_Step
# 功  能: 删除尾孔 Step
# 参  数: NONE
# 返回值: NONE
#***********************/
sub DELETE_STEP
{
    shift;    
    my ($JOB,$STEP,$del_step)=@_;
    my %WK_STEP;
RESTART:
    $f->INFO(units => 'mm', entity_type => 'step',entity_path => "$JOB/$STEP",data_type => 'SR');
    my @gSRstep=@{$f->{doinfo}{gSRstep}};
    my @gSRxa=@{$f->{doinfo}{gSRxa}};
    my @gSRya=@{$f->{doinfo}{gSRya}};
    my @gSRangle=@{$f->{doinfo}{gSRangle}};
    ###循环取出WK 的坐标及WK 的角度
    for(my $num=0;$num<@gSRstep;$num++){
        my $sr_line=$num+1;
        if ($gSRstep[$num] =~ /^($del_step\d?)$/) {
            $WK_STEP{"name_$gSRstep[$num]"}  = $gSRstep[$num];            
            $WK_STEP{"xa_$gSRstep[$num]"}    = $gSRxa[$num];
            $WK_STEP{"ya_$gSRstep[$num]"}    = $gSRya[$num];
            $WK_STEP{"angle_$gSRstep[$num]"} = $gSRangle[$num];
            $WK_STEP{"exist_$gSRstep[$num]"} = "yes";
            
            ###删除
            $f->COM('sr_tab_del', line => $sr_line);
            
            ###当存在类似"wk1 wk2 wk3“的step时，删除一个后。需要重新计算对应的行
            goto RESTART;
        }        
    }
    ###返回Hash的指针
    return \%WK_STEP;
}

#/************************
# 函数名: DELETE_ENTITY
# 功  能: 删除JOB或Step
# 参  数: NONE
# 返回值: NONE
#***********************/
sub DELETE_ENTITY
{
    shift;    
    my ($type,$name)=@_;
    $f->COM("delete_entity,job=,type=$type,name=$name");
}

#/************************
# 函数名: Add_WK_Step
# 功  能: 原位置添加尾孔 Step
# 参  数: NONE
# 返回值: NONE
#***********************/
sub ADD_STEP
{
    shift;
    my ($WK_STEP,$del_step)=@_;
    my %WK_STEP=%$WK_STEP;    
    my $Add_step="no";
    ###获取当前单位：
    $f->COM('get_units');
    my $Units=$f->{COMANS};
    ###切换当前单位为英寸(因为删除时记录的数据为MM单位)
    $f->COM('units',type=> 'mm');
    ###wk 或2nd后不带数字的Step，还原位置
    $Add_step="yes" if ($WK_STEP{"exist_".$del_step} eq 'yes');    
    ###当Step后带数字时
    for(1..4)
    {
        $Add_step="yes",$del_step = $del_step.$_ if ($WK_STEP{"exist_".$del_step.$_} eq 'yes');
    }
    if($Add_step eq "yes")
    {
        $f->COM('sr_tab_add', line => 1,
                               step => $WK_STEP{"name_".$del_step},
                               x    => $WK_STEP{"xa_".$del_step},
                               y    => $WK_STEP{"ya_".$del_step},
                               nx   => 1,
                               ny   => 1,
                               angle => $WK_STEP{"angle_".$del_step},
                              mirror => 'no');
    }
    ###还原单位
    $f->COM('units',type=> $Units);
}

#/******************************
# 函数名: 过滤物体命令集
# 功  能: 过滤选择物体
# 参  数: 应用项
# 返回值: NONE
#*****************************/
sub FILTER_RESET 
{
    shift;
    $f->COM('filter_reset', filter_name => 'popup');    
}

sub FILTER_SET_POL 
{
    shift;
    my ($polarity,$reset_filter) = @_;
    $reset_filter = (not defined $reset_filter) ? 0 : $reset_filter;
    if ($reset_filter eq '1') {
        $f->COM('filter_reset', filter_name => 'popup');
    }
    $f->COM('filter_set', filter_name  => 'popup',update_popup => 'no',polarity => "$polarity"); 
}

sub FILTER_SET_TYP 
{
    shift;
    my ($feat_types,$reset_filter) = @_;
    $reset_filter = (not defined $reset_filter) ? 0 : $reset_filter;
    if ($reset_filter eq '1') {
        $f->COM('filter_reset', filter_name => 'popup');
    }
    $f->COM('filter_set', filter_name => "popup", update_popup => "no", feat_types => $feat_types);
}


sub FILTER_SET_PRO 
{
    shift;
    my ($profile,$reset_filter) = @_;
    $reset_filter = (not defined $reset_filter) ? 0 : $reset_filter;
    if ($reset_filter eq '1') {
        $f->COM('filter_reset', filter_name => 'popup');
    }
    $f->COM('filter_set', filter_name => 'popup',update_popup => 'no',profile => "$profile"); 
}

sub FILTER_SET_DCODE
{
    shift;
    my ($dcode,$reset_filter) = @_;
    $reset_filter = (not defined $reset_filter) ? 0 : $reset_filter;
    if ($reset_filter eq '1') {
          $f->COM('filter_reset', filter_name => 'popup');
    };    
    $f->COM('filter_set', filter_name => "popup", update_popup => "no", dcode => "$dcode");
}

sub FILTER_SET_INCLUDE_SYMS
{
    shift;
    my ($include_syms,$reset_filter) = @_;
    $reset_filter = (not defined $reset_filter) ? 0 : $reset_filter;
    if ($reset_filter eq '1') {
        $f->COM('filter_reset', filter_name => 'popup');
    };    
    $f->COM('filter_set', filter_name  => 'popup',update_popup => 'no',include_syms => "$include_syms");
}

sub FILTER_SET_EXCLUDE_SYMS
{
    shift;
    my ($exclude_syms,$reset_filter) = @_;
    $reset_filter = (not defined $reset_filter) ? 0 : $reset_filter;
    if ($reset_filter eq '1') {
        $f->COM('filter_reset', filter_name => 'popup');
    };    
    $f->COM('filter_set', filter_name  => 'popup',update_popup => 'no',exclude_syms => "$exclude_syms");
}

sub FILTER_SET_ATR_SYMS
{
    shift;
    my ($atr_set,$reset_filter) = @_;
    $reset_filter = (not defined $reset_filter) ? 0 : $reset_filter;
    if ($reset_filter eq '1') {
          $f->COM('filter_reset', filter_name => 'popup');
    };    
    $f->COM('filter_atr_set', filter_name => 'popup',condition   => 'yes',attribute   => "$atr_set");
}


sub SELECT_OPTION_ATTR
{ 
   shift; 
   my ($attr,$option_attr)=@_;
   $f->COM('filter_reset',filter_name=>"popup");
   $f->COM('filter_atr_set',filter_name=>"popup",condition=>"yes",attribute=>$attr,option=>$option_attr);        
}

sub SELECT_TEXT_ATTR
{
    shift;
    my ($attr,$text_attr,$reset_filter)=@_;
    $reset_filter = (not defined $reset_filter) ? 0 : $reset_filter;
    if ($reset_filter eq '1') {
          $f->COM('filter_reset', filter_name => 'popup');
    };    
    $f->COM('filter_atr_set', filter_name => "popup", condition => "yes", attribute => $attr, text => $text_attr);
}

sub FILTER_SET_FEAT_TYPES
{
    shift;
    my ($feat_types,$reset_filter) = @_;
    $reset_filter = (not defined $reset_filter) ? 0 : $reset_filter;
    if ($reset_filter eq '1') {
          $f->COM('filter_reset', filter_name => 'popup');
    }        
    $f->COM('filter_set', filter_name  => 'popup',update_popup => 'no',feat_types => $feat_types);    
}

sub FILTER_SELECT 
{
    shift;
    my ($operation) = @_;
    if (! defined $operation) {$operation = 'select';};
    $f->COM('filter_area_strt');
    $f->COM('filter_area_end', layer => '',filter_name => 'popup',operation => "$operation",area_type => 'none',inside_area => 'no',intersect_area => 'no',lines_only => 'no',ovals_only => 'no',min_len => 0,max_len => 0,min_angle => 0,max_angle => 0);
}

#/******************************
# 函数名: INPUT_MANUAL_SET
# 功  能: 导入资料
# 参  数: 1,文件路径名 2,料号名 3,STEP名 
#        4,文件格式 5,层别名
# 返回值: NONE
sub INPUT_MANUAL_SET
{
    shift;
    my ($filePath,$jobname,$stepname,$fileformat,$layername) = @_;
    $f->COM('input_manual_reset');
    $f->COM('input_manual_set', path            => "$filePath",
                          job             => "$jobname",
                          step            => "$stepname",
                          format          => "$fileformat",
                          data_type       => 'ascii',
                          units           => 'inch',
                          coordinates     => 'absolute',
                          zeroes          => 'leading',
                          nf1             => 2,
                          nf2             => 6,
                          decimal         => 'no',
                          separator       => '*',
                          tool_units      => 'inch',
                          layer           => "$layername",
                          wheel           => '',
                          wheel_template  => '',
                          nf_comp         => 0,
                          multiplier      => 1,
                          text_line_width => '0.0024',
                          signed_coords   => 'no',
                          break_sr        => 'yes',
                          drill_only      => 'no',
                          merge_by_rule   => 'no',
                          threshold       => 200,
                          resolution      => 3);
    $f->COM('input_manual', script_path => '');
}

#/******************************
# 函数名: INFO_TO_FILE
# 功  能: 将INFO信息转为文件
# 参  数: 1,INFO命令
# 返回值: NONE
#*****************************/
sub INFO_TO_FILE
{
    shift;
    my $com = shift;
    $f->COM($com);
}

#/***************************
# 函数名: IMPORT_JOB
# 功  能: 导入TGZ资料
# 参  数: 1,TGZ路径 2,料号名 3,数据库名
# 返回值: NONE
#***************************/
sub IMPORT_JOB
{
    shift;
    my $tgzPath = shift;
    my $jobname = shift;
    my $db = shift;
    $db = 'genesis' if ( not $db );
    $f->VOF;
    $f->COM('import_job', db => "$db", path => "$tgzPath", name => "$jobname", analyze_surfaces => "no");
    my $Status=$f->{STATUS};
    $f->VON;
    
    ###
    return $Status;
}

#/***************************
# 函数名: GET_SELECT_COUNT
# 功  能: 获得选中的数量
# 参  数: NONE
# 返回值: 1,整形
#**************************/
sub GET_SELECT_COUNT
{
    shift;
    $f->COM('get_select_count');
    my $select_count = $f->{COMANS};
    return $select_count;
}

#/*****************************
# 函数名: GET_VERSION
# 功  能: 获取G的版本信息
# 参  数: NONE
# 返回值: 1,版本信息
#*****************************/
sub GET_VERSION
{
    shift;
    $f->COM('get_version');
    return $f->{COMANS};
}

#/********************************
# 函数名: GET_ATTR_LAYER
# 功  能: 拫据属性获取层别(board层)
# 参  数: 1,料号名 2,类型
# 返回值: 1,层别数组
#********************************/
sub GET_ATTR_LAYER
{
    my $self = shift;
    my $job = shift; my $type = shift;
    my $i=0; my %hashValue; my @LayerValue=();
    $f->INFO(entity_type => 'matrix',entity_path => "$job/matrix");

    while ( $i < scalar @{$f->{doinfo}{gROWrow}} ) {
        if ($type eq 'drill') {
            if ( ${$f->{doinfo}{gROWcontext}}[$i] eq 'board' and ${$f->{doinfo}{gROWlayer_type}}[$i] eq 'drill' ) {
                push @LayerValue,${$f->{doinfo}{gROWname}}[$i];
            }
        }
        if ($type eq 'signal') {
            if ( ${$f->{doinfo}{gROWcontext}}[$i] eq 'board' and (${$f->{doinfo}{gROWlayer_type}}[$i] eq 'signal' or ${$f->{doinfo}{gROWlayer_type}}[$i] eq 'power_ground') ) {
                push @LayerValue,${$f->{doinfo}{gROWname}}[$i];
            }
        }
        if ($type eq 'power_ground') {
            if ( ${$f->{doinfo}{gROWcontext}}[$i] eq 'board' and ${$f->{doinfo}{gROWlayer_type}}[$i] eq 'power_ground' ) {
                push @LayerValue,${$f->{doinfo}{gROWname}}[$i];
            }
        }
        if ($type eq 'silk_screen') {
            if ( ${$f->{doinfo}{gROWcontext}}[$i] eq 'board' and ${$f->{doinfo}{gROWlayer_type}}[$i] eq 'silk_screen' ) {
                push @LayerValue,${$f->{doinfo}{gROWname}}[$i];
            }
        }
        if ($type eq 'solder_mask') {
            if ( ${$f->{doinfo}{gROWcontext}}[$i] eq 'board' and ${$f->{doinfo}{gROWlayer_type}}[$i] eq 'solder_mask' ) {
                push @LayerValue,${$f->{doinfo}{gROWname}}[$i];
            }
        }
        if ($type eq 'inner') {
            if ( ${$f->{doinfo}{gROWcontext}}[$i] eq 'board' and ${$f->{doinfo}{gROWside}}[$i] eq 'inner' ) {
                push @LayerValue,${$f->{doinfo}{gROWname}}[$i];
            }
        }
        if ($type eq 'outer') {
            if ( ${$f->{doinfo}{gROWcontext}}[$i] eq 'board' and ${$f->{doinfo}{gROWlayer_type}}[$i] eq 'signal' and (${$f->{doinfo}{gROWside}}[$i] eq 'top' or ${$f->{doinfo}{gROWside}}[$i] eq 'bottom') ) {
                push @LayerValue,${$f->{doinfo}{gROWname}}[$i];
            }
        }

        if ($type eq 'coverlay') {
            if ( ${$f->{doinfo}{gROWcontext}}[$i] eq 'board' and ${$f->{doinfo}{gROWlayer_type}}[$i] eq 'coverlay' and (${$f->{doinfo}{gROWside}}[$i] eq 'top' or ${$f->{doinfo}{gROWside}}[$i] eq 'bottom') ) {
                push @LayerValue,${$f->{doinfo}{gROWname}}[$i];
            }
        }

        if ($type eq 'all') {
            push @LayerValue,${$f->{doinfo}{gROWname}}[$i] if (${$f->{doinfo}{gROWname}}[$i] ne "");
        }
        $i++;
    }
    $self->{getlayer}    = [@LayerValue];
}

#/***************************
# 函数名: GET_DRILL_THROUGH
# 功  能: 返回钻孔层的起始层
# 参  数: 1,料号名 2,STEP 3,钻孔层别 
# 返回值: NONE
#***************************/
sub GET_DRILL_THROUGH
{
    shift;
    my ($job,$step,$drillLayer) = @_;
    
    $f->INFO(entity_type => 'layer',entity_path => "$job/$step/$drillLayer",data_type => 'DRL_END');
    my $end = $f->{doinfo}{gDRL_END};
    
    $f->INFO(entity_type => 'layer',entity_path => "$job/$step/$drillLayer",data_type => 'DRL_START');
    my $start = $f->{doinfo}{gDRL_START};
    
    return ($start,$end);
}

#/***************************
# 函数名: GET_STEP_NAME
# 功  能: 获取料号的STEP名字
# 参  数: 1,料号名
# 返回值: NONE
#***************************/
sub GET_STEP_NAME
{
    my $self = shift;
    my $job = shift;
    $f->INFO(entity_type => 'matrix',entity_path => "$job/matrix");
    my @StepValue = @{$f->{doinfo}{gCOLstep_name}};
    $self->{getstep}    = [@StepValue];
    return @StepValue;
}

#/***************************
# 函数名: GET_COPPER_LIST
# 功  能: 获取料号的COPYERLAYER信息
# 参  数: Inplan中的面向Hash
# 返回值: CopperHash
# 备  注: 需要传入一个面向Hash
#***************************/
sub GET_COPPER_LIST
{
    shift;
    my($job,%Lay_Mir)=@_;
    my %Copper_Info;
    $f->INFO(entity_type => 'matrix',entity_path => "$job/matrix");

    my @gROWname=@{$f->{doinfo}{gROWname}};
    my @gROWcontext=@{$f->{doinfo}{gROWcontext}};
    my @gROWlayer_type=@{$f->{doinfo}{gROWlayer_type}};
    my @gROWpolarity=@{$f->{doinfo}{gROWpolarity}};
    my @gROWside=@{$f->{doinfo}{gROWside}};
    my @gROWfoil_side=@{$f->{doinfo}{gROWfoil_side}};
    my $n=0;
    my $layer_num=1;
    for (@gROWname){ 
        if ($gROWcontext[$n] eq "board" and $gROWlayer_type[$n] =~ /^(signal|power_ground)$/) {
            my $Foil_side=(exists $Lay_Mir{$_}) ? $Lay_Mir{$_} : $gROWfoil_side[$n];
            $Copper_Info{$_}={'ROWcontext'      => "$gROWcontext[$n]",
                              'ROWlayer_type'   => "$gROWlayer_type[$n]",
                              'ROWpolarity'     => "$gROWpolarity[$n]",
                              'ROWside'         => "$gROWside[$n]",
                              'gROWfoil_side'   => "$Foil_side",
                              'Layer_Num'       => "$layer_num"
                              };
            $layer_num++;
        };
        $n++;
    }
    return %Copper_Info;
}

#/***************************
# 函数名: GET_MATCH_LIST
# 功  能: 获取相匹配的层列表（通过层名）
# 参  数: 型号名+层名正则表达式
# 返回值: 数组列表
# 备  注: 
#***************************/
sub GET_MATCH_LIST
{
    shift;
    my($job,$matchRule)=@_;
    $matchRule =~ s/\+/\\+/;  
    my @matchList;
    $f->INFO(entity_type => 'matrix',entity_path => "$job/matrix");

    my @gROWname=@{$f->{doinfo}{gROWname}};
    my @gROWcontext=@{$f->{doinfo}{gROWcontext}};
    my @gROWlayer_type=@{$f->{doinfo}{gROWlayer_type}};
    my @gROWpolarity=@{$f->{doinfo}{gROWpolarity}};
    my @gROWside=@{$f->{doinfo}{gROWside}};
    my @gROWfoil_side=@{$f->{doinfo}{gROWfoil_side}};
    my $n=0;
    my $layer_num=1;
    for (@gROWname){ 
        if ($_ =~ /$matchRule/) {
            push @matchList, $_;
        }
    }
    return @matchList;
}


#/************************
# 函数名: GREATE_ENTITY
# 功  能: 创建实体
# 参  数: 1,类型 2,数据库 3,料号名 4,STEP名 
# 返回值: NONE
#*************************/
sub GREATE_ENTITY
{
    shift;
    my ($type,$dbname,$jobname,$stepname) = @_;
    
    if ( "job" eq $type ) 
    {
        $f->COM('create_entity', job => '',is_fw => 'no',type => 'job',name => "$jobname",db => "$dbname",fw_type => 'form');    
    }

    if ( "step" eq $type )
    {
        $f->COM('create_entity', job => "$jobname",is_fw => 'no',type => 'step',name => "$stepname",db => "$dbname",fw_type => 'form');
    }
}

#/************************
# 函数名: GET_UNITS
# 功  能: 获取当前单位
# 参  数: NONE
# 返回值: units
#***********************/
sub GET_UNITS
{
    shift;
    $f->COM('get_units');
    return $f->{COMANS};    
}

sub GET_USER_NAME
{
    shift;
    $f->COM('get_user_name');
    return $f->{COMANS};    
}

sub GET_USER_GROUP
{
    shift;
    $f->COM('get_user_group');
    return $f->{COMANS};    
}
#/************************
# 函数名: GET_WORK_LAYER
# 功  能: 获取工作层
# 参  数: NONE
# 返回值: work_layer
#***********************/
sub GET_WORK_LAYER
{
    shift;
    $f->COM("get_work_layer");
    return $f->{COMANS};
}


#/************************
# 函数名: GET_PROFILE_SIZE
# 功  能: 获取Profile的尺寸
# 参  数: NONE
# 返回值: 
#***********************/
sub GET_PROFILE_SIZE
{
    shift;
    my ($JOB,$STEP)=@_;
    $f->INFO(units => 'mm', entity_type => 'step',
         entity_path => "$JOB/$STEP",
         data_type => 'PROF_LIMITS');
    my $gPROF_LIMITSxmin = $f->{doinfo}{gPROF_LIMITSxmin};
    my $gPROF_LIMITSymin = $f->{doinfo}{gPROF_LIMITSymin};
    my $gPROF_LIMITSxmax = $f->{doinfo}{gPROF_LIMITSxmax};
    my $gPROF_LIMITSymax = $f->{doinfo}{gPROF_LIMITSymax};
    
    my $Size_X=($gPROF_LIMITSxmax - $gPROF_LIMITSxmin) + $gPROF_LIMITSxmin*2;
    my $Size_Y=($gPROF_LIMITSymax - $gPROF_LIMITSymin) + $gPROF_LIMITSymin*2;
    
    return ($Size_X,$Size_Y);
}

#/************************
# 函数名: getSrMinMax
# 功  能: 取出最大的SR信息
# 参  数: Hash
# 返回值: 
#***********************/
sub getSrMinMax
{
    shift;
    my ($JOB,$STEP)=@_;
    $f->INFO(units => 'mm', entity_type => 'step', entity_path => "$JOB/$STEP", data_type => 'SR');
    my $srXmin = 99999999999999;
    my $srXmax = -9999999999999;
    my $srYmin = 99999999999999;
    my $srYmax = -9999999999999;

    #$f->PAUSE("$srXmin, $srXmax, $srYmin, $srYmax");
    for (my $i = 0; $i < @{$f->{doinfo}{gSRstep}} ; $i++)
    {
        my $curStep = ${$f->{doinfo}{gSRstep}}[$i];
        if ($curStep =~ /^(set(?:.+)?|edit(?:.+)?|.+flip)$/) { # |coupon(?:-)?(?:\d+)?)
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


#/************************
# 函数名: JOB_EXISTS
# 功  能: 判断JOB是否存在
# 参  数: NONE
# 返回值: 
#***********************/
sub JOB_EXISTS
{
    shift;
    my ($JOB)=@_;
    $f->INFO(entity_type => 'job',entity_path => $JOB,data_type => 'EXISTS');
    my $job_exists=$f->{doinfo}{gEXISTS};
    return $job_exists;
}

#/************************
# 函数名: LAYER_EXISTS
# 功  能: 判断层别是否存在
# 参  数: 1,料号名 2,STEP名 3,层别名
# 返回值: yes/no
#************************/
sub LAYER_EXISTS
{
    shift;
    my ($job,$step,$layer) = @_;
    $f->INFO(entity_type => 'layer',entity_path => "$job/$step/$layer",data_type => 'EXISTS');
    return $f->{doinfo}{gEXISTS};
}


#/************************
# 函数名: MULTI_LAYER_DISP
# 功  能: 多层显示
# 参  数: 1,显示方式
# 返回值: NONE
#************************/
sub MULTI_LAYER_DISP
{
    shift;
    my $mode = shift;
    $f->COM('multi_layer_disp', mode => $mode, show_board => 'no');
}

#/************************
# 函数名: MOUSE
# 功  能: 鼠标坐标捕获
# 参  数: 单位，类型（P:点选）
# 返回值: NONE
#************************/
sub MOUSE
{
    shift;
    my ($m_type) = @_;
    $m_type = 'p' if (not defined $m_type);
    $f -> MOUSE("$m_type Please select ");
    my @point = split(" ",$f ->{MOUSEANS});
    
    # --返回坐标信息
    return @point;
}

#/************************
# 函数名: OPEN_JOB
# 功  能: 打开料号名
# 参  数: 1,料号名
# 返回值: NONE
#************************/
sub OPEN_JOB
{
    shift;
    my $jobname    = shift;
    $f->VOF;
    $f->COM('open_job',job=> $jobname);    
    my $Status=$f->{STATUS};
    $f->VON;
    
    ###
    return $Status;
}

#/************************
# 函数名: OPEN_JOB
# 功  能: 打开STEP名字
# 参  数: 1,料号名 2,STEP名字
# 返回值: NONE
#************************/
sub OPEN_STEP
{
    shift;
    my $jobname    = shift;
    my $setname    = shift;
    $f->COM('open_entity', job => $jobname ,type => 'step',name => $setname,iconic => 'no');
    $f->AUX('set_group', group => $f->{COMANS});
}

#/************************
# 函数名: OPTIMIZE_LEVELS
# 功  能: 优化指定层
# 参  数: 1,指定层名 2,优化后的层名
# 返回值: NONE
#************************/
sub OPTIMIZE_LEVELS
{
    my $self    = shift;
    my ($layer,$opt_layer,$levels) = @_;
    $levels = 1 if (! defined $levels);    
    $f->COM('optimize_levels', layer => "$layer", opt_layer => "$opt_layer", levels => $levels);
}

#/************************
# 函数名: OUTPUT_LAYER_RESET
# 功  能: 输出信息还原
# 参  数: 层名...
# 返回值: NONE
#************************/
sub OUTPUT_LAYER_RESET
{
    shift;
    $f->COM('output_layer_reset');
}

#/************************
# 函数名: OUTPUT_LAYER_SET
# 功  能: 层输出设置
# 参  数: 层名...
# 返回值: NONE
#************************/
sub OUTPUT_LAYER_SET
{
    shift;
    my ($layer,$reset,$angle,$mir,$x_scale,$y_scale,$pol,$line_units)=@_;
    if (defined $reset){
        $f->COM('output_layer_reset') if ($reset == 1);
    }  
    
    $angle=0          if(not defined $angle);
    $mir="no"          if(not defined $mir);
    $x_scale=1          if(not defined $x_scale);
    $y_scale=1          if(not defined $y_scale);
    $pol='positive'  if(not defined $pol);
    $line_units='mm' if(not defined $line_units);
    $f->COM('output_layer_set', layer  => "$layer",
                          angle        => "$angle",
                          mirror       => "$mir",
                          x_scale      => "$x_scale",
                          y_scale      => "$y_scale",
                          comp         => "0",
                          polarity     => "$pol",
                          setupfile    => "",
                          setupfiletmp => "",
                          line_units   => "$line_units",
                          gscl_file    => "",
                          step_scale   => "no");
}

#/***************************
# 函数名: PAUSE
# 功  能: G暂停
# 参  数: 1,txt
# 返回值: NONE
#***************************/
sub PAUSE
{
    shift;
    my $txt = shift;
    $f->PAUSE("$txt");
}

#/******************************
# 函数名: REGISTER_LAYERS
# 功  能: 拉正层别
# 参  数: 1
# 返回值: NONE
#******************************/
sub REGISTER_LAYERS
{
    shift;
    my $reflayer = shift;
    $f->COM('register_layers', reference_layer  => "$reflayer",
            tolerance        => '0.1',
            mirror_allowed   => 'no',
            rotation_allowed => 'no',
            zero_lines       => 'no',
            reg_mode         => 'affected_layers',
            register_layer   => '');

}

#/******************************
# 函数名: SCRIPT_RUN
# 功  能: 调运其它执行程序
# 参  数: 1,程序文件路径 2,参数
# 返回值: NONE
#******************************/
sub SCRIPT_RUN
{
    shift;
    my $scriptPath = shift;
    my $env = \@_;
    my $comTxt = "script_run,name=$scriptPath";
    for ( my $i=0 ; $i < scalar @$env ; $i++) 
    {
        $comTxt .= ",env";
        $comTxt .= $i+1 ;
        $comTxt .= "=";
        $comTxt .= $env->[$i];
    }
    $f->COM("$comTxt");
}

#/***************************
# 函数名: SAVE_JOB
# 功  能: 保存料号
# 参  数: 1,料号名
# 返回值: NONE
#***************************/
sub SAVE_JOB
{
    shift;
    my $jobName = shift;
    $f->COM('save_job','job'=>"$jobName",'override'=>'no');
}

#/*******************************
# 函数名: SEL_REF_FEAT
# 功  能: 参数选择
# 参  数: 1,层名 2,方式 3,极性
# 返回值: NONE
#******************************/
sub SEL_REF_FEAT
{
    ###mode:,"touch",disjoint,cover,include
    shift;
    my ($layer_name,$mode,$polarity,$f_types,$include,$exclude) = @_;
    $polarity = 'positive;negative' if (! defined $polarity);
    $f_types='line;pad;surface;arc;text' if(not $f_types);
    $include='' if(not $include);
    $exclude='' if(not $exclude);
    
    $f->COM('sel_ref_feat', layers       => "$layer_name",
                      use          => 'filter',
                      mode         => "$mode",
                      pads_as      => 'shape',
                      f_types      => "$f_types",
                      polarity     => "$polarity",
                      include_syms => $include,
                      exclude_syms => $exclude);
}

#/************************
# 函数名: SEPCMP_PAGE_OPEN
# 功  能: 打开STEP对比的界面
# 参  数: 1,job1 2,step1
# 返回值: NONE
#************************/
sub SEPCMP_PAGE_OPEN
{
    shift;
    my ($job1,$step1,$job2,$step2) = @_;
    $f->COM('stpcmp_page_open', job1       => "$job1",
                          step1      => "$step1",
                            job2       => "$job2",
                          step2      => "$step2",
                          force_init => 'yes');
}

#/************************
# 函数名: SEL_COPY
# 功  能: COPY选择的物体
# 参  数: NONE
# 返回值: NONE
#***********************/
sub SEL_COPY
{
    shift;
    my ($target_layer,$invert,$size,$dx,$dy,$x_anchor,$y_anchor,$rotation,$mirror) = @_;
    if (not $dx and not $dy and not $x_anchor and not $y_anchor and not $rotation and not $mirror) {
        $dx=0,$dy=0,$x_anchor=0;$y_anchor=0,$rotation=0,$mirror='none';
    }
    
    $f->COM('sel_copy_other', dest => "layer_name", target_layer => $target_layer, invert => $invert,
        size => $size, dx => $dx, dy => $dy,  x_anchor => $x_anchor, y_anchor => $y_anchor,
        rotation => $rotation, mirror => $mirror);
}

#/************************
# 函数名: SEL_CHANGE_SYM
# 功  能: 改变选择物体Symbol
# 参  数: NONE
# 返回值: NONE
#***********************/
sub SEL_CHANGE_SYM
{
    shift;
    my($symbol,$angle)=@_;
    $angle = 'no' if (not $angle);
    $f->COM('sel_change_sym',symbol=> "$symbol",reset_angle=>"$angle");
}

#/************************
# 函数名: SEL_DECOMPOSE
# 功  能: 打散Surface
# 参  数: NONE
# 返回值: NONE
#***********************/
sub SEL_DECOMPOSE
{
    shift;
    $f->COM('sel_decompose', overlap => "yes");
}

#/************************
# 函数名: SEL_TRANSFORM
# 功  能: 偏移或旋转
# 参  数: NONE
# 返回值: NONE
#***********************/
sub SEL_TRANSFORM
{
    shift;
    my ($mode,$duplicate,$x_anchor,$y_anchor,$angle,$x_scale,$y_scale,$x_offset,$y_offset)=@_;
    $f->COM('sel_transform', mode => $mode, oper => "", duplicate => $duplicate, x_anchor => $x_anchor, 
        y_anchor => $y_anchor, angle => $angle, x_scale => $x_scale, y_scale => $y_scale, x_offset => $x_offset, 
        y_offset => $y_offset);
    #$f->COM('sel_transform', mode => "anchor", oper => "", duplicate => "no", x_anchor => 0, 
    #    y_anchor => 0, angle => 0, x_scale => 1, y_scale => 1, x_offset => "0", 
    #    y_offset => "0");
}

#/************************
# 函数名: SEL_BREAK
# 功  能: 打散物体
# 参  数: NONE
# 返回值: NONE
#***********************/
sub SEL_BREAK
{
    shift;
    $f->COM('sel_break_level', attr_mode => "merge");
}

#/************************
# 函数名: SEL_DELETE
# 功  能: 删除选中物体
# 参  数: NONE
# 返回值: NONE
#***********************/
sub SEL_DELETE
{
    shift;
    $f->COM('sel_delete');
}

#/************************
# 函数名: SEL_DELETE_ATR
# 功  能: 删除选中物体指定属性
# 参  数: NONE
# 返回值: NONE
#***********************/
sub SEL_DELETE_ATR
{
    shift;
    my ($atr)=@_;
    $f->COM('sel_delete_atr', attributes => "$atr");
}



#/************************
# 函数名: SEL_POLYLINE_FEAT
# 功  能: 网选物体
# 参  数: NONE
# 返回值: NONE
#***********************/
sub SEL_POLYLINE_FEAT
{
    shift;
    my ($sel_x,$sel_y)=@_;
    $f->COM('sel_polyline_feat', operation => "select", x => $sel_x, y => $sel_y, tol => "0");
}

#/************************
# 函数名: SEL_CUT_DATA
# 功  能: 以范围填充Surface
# 参  数: NONE
# 返回值: NONE
#***********************/
sub SEL_CUT_DATA
{
    shift;
    my($ignore_width,$ignore_holes,$start_positive)=@_;
    if (not $ignore_width and not $ignore_holes and not $start_positive) {
        $ignore_width='no',$ignore_holes='none',$start_positive='yes';
    }
    $f->COM('sel_cut_data', det_tol            => "25.4",
                          con_tol              => "25.4",
                          rad_tol              => "2.54",
                          filter_overlaps      => "no",
                          delete_doubles       => "no",
                          use_order            => "yes",
                          ignore_width         => $ignore_width,
                          ignore_holes         => $ignore_holes,
                          start_positive       => $start_positive,
                          polarity_of_touching => "same");
}

#/************************
# 函数名: SEL_RESIZE
# 功  能: 预大选中物体
# 参  数: 预大值
# 返回值: NONE
#***********************/
sub SEL_RESIZE
{
    shift;
    my $size=shift;
    $f->COM('sel_resize', size => $size, corner_ctl => "no");
}

#/************************
# 函数名: SEL_REVERSE
# 功  能: 反选命令
# 参  数: NONE
# 返回值: NONE
#***********************/
sub SEL_REVERSE 
{
    shift;
    $f->COM('sel_reverse');
}

#/************************
# 函数名: SR_FILL
# 功  能: 填充物体时参数设置
# 参  数: NONE
# 返回值: NONE
#***********************/
sub SR_FILL
{
    shift;
    my ($polarity,$step_margin_x,$step_margin_y,$step_max_dist_x,$step_max_dist_y,$sr_margin_x,$sr_margin_y,$sr_max_dist_x,$sr_max_dist_y,$nest_sr)=@_;
    ###$polarity (positive or negative) $step_margin_x $step_margin_y $step_max_dist_x $step_max_dist_y为number型
    if ($sr_margin_x eq "" and $sr_margin_y eq "" and $sr_max_dist_x eq "" and $sr_max_dist_y eq "") {
        $sr_margin_x=$sr_margin_y=$sr_max_dist_x=$sr_max_dist_y=0;
    }
    if ($nest_sr eq "") {
        #code
        $nest_sr = "yes";
    }
    
    $f->AUX("get_version");
    our $version  = (split(/ /,$f->{COMANS}))[-2];
    if ($version =~ /V9.7b?/ || $version =~ /V10.0?/) {
        $f->COM('sr_fill', polarity      => $polarity,
                         step_margin_x   => $step_margin_x,
                         step_margin_y   => $step_margin_y,
                         step_max_dist_x => $step_max_dist_x,
                         step_max_dist_y => $step_max_dist_y,
                         sr_margin_x     => $sr_margin_x,
                         sr_margin_y     => $sr_margin_y,
                         sr_max_dist_x   => $sr_max_dist_x,
                         sr_max_dist_y   => $sr_max_dist_y,
                         nest_sr         => $nest_sr,
                         stop_at_steps   => "",
                         consider_feat   => "no",
                         consider_drill  => "no",
                         consider_rout   => "no",
                         dest            => "affected_layers",
                         attributes      => "no");
    } else {
        $f->COM('sr_fill', polarity      => $polarity,
                         step_margin_x   => $step_margin_x,
                         step_margin_y   => $step_margin_y,
                         step_max_dist_x => $step_max_dist_x,
                         step_max_dist_y => $step_max_dist_y,
                         sr_margin_x     => $sr_margin_x,
                         sr_margin_y     => $sr_margin_y,
                         sr_max_dist_x   => $sr_max_dist_x,
                         sr_max_dist_y   => $sr_max_dist_y,
                         nest_sr         => $nest_sr,
                         stop_at_steps   => "",
                         consider_feat   => "no",
                         consider_drill  => "no",
                         consider_rout   => "no",
                         dest            => "affected_layers",
                         attributes      => "no",
                         use_profile     => "use_profile");        
    }
}

#/************************
# 函数名: FILL_PARAMS
# 功  能: 填充物体时参数设置
# 参  数: NONE
# 返回值: NONE
#***********************/
sub FILL_PARAMS
{
    shift;
    # Song Change 20191022
    #$f->COM('fill_params', type         => "solid",
    #                     origin_type    => "datum",
    #                     solid_type     => "surface",
    #                     std_type       => "line",
    #                     min_brush      => "25.4",
    #                     use_arcs       => "yes",
    #                     symbol         => "",
    #                     dx             => "2.54",
    #                     dy             => "2.54",
    #                     std_angle      => 45,
    #                     std_line_width => 254,
    #                     std_step_dist  => 1270,
    #                     std_indent     => "odd",
    #                     break_partial  => "yes",
    #                     cut_prims      => "no",
    #                     outline_draw   => "no",
    #                     outline_width  => 0,
    #                     outline_invert => "no");
            my ($type,$origin_type,$solid_type,$std_type,$min_brush,$use_arcs,$symbol,$dx,$dy, $std_angle,$std_line_width,$std_step_dist,$std_indent,$break_partial,$cut_prims,$outline_draw,$outline_width,$outline_invert) = @_;
            if ($type           eq "" ) { $type = "solid";}
            if ($origin_type    eq "" ) { $origin_type = "datum";}
            if ($solid_type     eq "" ) { $solid_type = "surface";}
            if ($std_type       eq "" ) { $std_type = "line";}
            if ($min_brush      eq "" ) { $min_brush = "25.4";}
            if ($use_arcs       eq "" ) { $use_arcs = "yes";}
            if ($symbol         eq "" ) { $symbol = "";}
            if ($dx             eq "" ) { $dx = "2.54";}
            if ($dy             eq "" ) { $dy = "2.54";}
            if ($std_angle      eq "" ) { $std_angle = 45;}
            if ($std_line_width eq "" ) { $std_line_width = 254;}
            if ($std_step_dist  eq "" ) { $std_step_dist = 1270;}
            if ($std_indent     eq "" ) { $std_indent  = "odd";}
            if ($break_partial  eq "" ) { $break_partial = "yes";}
            if ($cut_prims      eq "" ) { $cut_prims = "no";}
            if ($outline_draw   eq "" ) { $outline_draw = "no";}
            if ($outline_width  eq "" ) { $outline_width =  0;}
            if ($outline_invert eq "" ) { $outline_invert = "no";}     
         

           $f->COM('fill_params', type  => $type,
                         origin_type    => $origin_type,
                         solid_type     => $solid_type,
                         std_type       => $std_type,
                         min_brush      => $min_brush,
                         use_arcs       => $use_arcs,
                         symbol         => $symbol,
                         dx             => $dx,
                         dy             => $dy,
                         std_angle      => $std_angle,
                         std_line_width => $std_line_width,
                         std_step_dist  => $std_step_dist,
                         std_indent     => $std_indent,
                         break_partial  => $break_partial,
                         cut_prims      => $cut_prims,
                         outline_draw   => $outline_draw,
                         outline_width  => $outline_width,
                         outline_invert => $outline_invert);
    
}
    
#/************************
# 函数名: SEL_CONTOURIZE
# 功  能: 平面化Surface
# 参  数: NONE
# 返回值: NONE
#***********************/
sub SEL_CONTOURIZE
{
    shift;
    my ($accuracy,$clean_hole_size,$clean_hole_mode)=@_;
    if ($accuracy eq "" and $clean_hole_size eq "" and $clean_hole_mode eq "") {
        $accuracy=6.35,$clean_hole_size=76.2,$clean_hole_mode="x_and_y";
    }    
    $f->COM('sel_contourize', accuracy => $accuracy, break_to_islands => "yes",
            clean_hole_size => $clean_hole_size, clean_hole_mode => $clean_hole_mode);
}

#/************************
# 函数名: SEL_MOVE
# 功  能: 平面化Surface
# 参  数: NONE
# 返回值: NONE
#***********************/
sub SEL_MOVE
{
    shift;
    my ($target_layer,$invert,$size,$dx,$dy,$x_anchor,$y_anchor,$rotation,$mirror)=@_;
    if ($dx eq "" or $dy eq "" or $x_anchor eq "" or $y_anchor eq "" or $rotation eq "" or $mirror eq "") {
        $dx=$dy=$x_anchor=$y_anchor=$rotation=0,$mirror="none";
    }
    ###可只传入三个参数（层别，极性，加大尺寸）
    $f->COM('sel_move_other', target_layer => $target_layer, invert => $invert, size => $size, 
            dx => $dx, dy => $dy, x_anchor => $x_anchor, y_anchor => $y_anchor,
            rotation => $rotation, mirror => $mirror);
}

#/************************
# 函数名: SEL_MOVE_SAME
# 功  能: 平面化Surface
# 参  数: NONE
# 返回值: NONE
#***********************/
sub SEL_MOVE_SAME
{
    shift;
    my ($dx,$dy)=@_;
    $f->COM('sel_move',dx=>$dx,dy=>$dy);
}

#/************************
# 函数名: SEL_POLARITY
# 功  能: 转换极性
# 参  数: NONE
# 返回值: NONE
#***********************/
sub SEL_POLARITY
{
    shift;
    my ($polarity)=@_;
    $f->COM('sel_polarity',polarity=>"$polarity");
}

#/************************
# 函数名: SEL_POLARITY
# 功  能: 转换极性
# 参  数: NONE
# 返回值: NONE
#***********************/
sub STEP_EXISTS
{
    shift;
    my ($JOB,$STEP)=@_;
    $f->INFO(units => 'mm', entity_type => 'step',
         entity_path => "$JOB/$STEP",
         data_type => 'EXISTS');
    return $f->{doinfo}{gEXISTS};
}


#/************************
# 函数名: WORK_LAYER
# 功  能: 显示工作层
# 参  数: NONE
# 返回值: NONE
#***********************/
sub WORK_LAYER
{
    shift;
    my ($worklayer,$number) = @_;
    $number = 1 if (not $number);
    
    $f->VOF;
    $f->COM('display_layer', name => "$worklayer", display => 'yes', number => $number);
    my $Status=$f->{STATUS};
    $f->VON;
    
    ###正常打开后，继续执行命令
    if ($Status eq '0') {
        $f->COM('work_layer', name => "$worklayer") if ( 1 == $number );        
    }
    
    ###
    return $Status;    
}


#/************************
# 函数名: Messages
# 功  能: Message窗口
# 参  数: NONE
# 返回值: NONE
#***********************/
sub Messages
{
    shift;
    my ($icon,$message)=@_;
    use Tk;
    my $w=MainWindow->new();
    $w-> withdraw();
    $w-> messageBox(-title =>'Info',
                    -message => "$message",
                    -type => 'OK', -icon => "$icon");                                       
    destroy $w;
}

#/************************
# 函数名: Messages_Sel
# 功  能: Message窗口
# 参  数: NONE
# 返回值: Ok or Cancel
#***********************/
sub Messages_Sel
{
    shift;
    my ($icon,$message)=@_;
    use Tk;
    my $w=MainWindow->new();
    $w-> withdraw();
    
    my $reply = $w->messageBox(-title => 'Info',
                                    -type => 'OkCancel',
                                    -icon => "$icon",
                                    -default => 'Ok',
                                    -message => "$message");    
    destroy $w;
    return $reply;
}
#/************************
# 函数名: getFeatures
# 功  能: 取层别内的元素信息
# 参  数: NONE
# 返回值: 数组，哈希
#***********************/

sub getFeatures{
    shift;
	my %par = @_;
	$par{units} = 'inch' if (! defined $par{units});
	my $cshfile;
	if ($par{options}){
		$cshfile = $f->INFO(
			'units'=>$par{units},
			'entity_type'=>'layer',
			'entity_path'=>$par{job}.'/'.$par{step}.'/'.$par{layer},
			'data_type'=>'FEATURES',
			'options'=>$par{options},
			'parse'=>'no'	
		);
	}
	else{
		$cshfile = $f->INFO(
			'units'=>$par{units},
			'entity_type'=>'layer',
			'entity_path'=>$par{job}.'/'.$par{step}.'/'.$par{layer},
			'data_type'=>'FEATURES',
			'parse'=>'no'	
		);		
	}
    my @return = &dealwithFeatureFile($cshfile);
    return @return;
}

sub dealwithFeatureFile
{
    shift;
	my ($cshfile) = @_;
    open(CSHFILE,$cshfile);
	my @return;
	my $surface;
	my $surf_num = 1;
	while(<CSHFILE>){
		my $item = $_;
		next if $item =~ /^###/;
		next if $item =~ /^\s+$/;
		chomp $item;
		if ($item =~ /^#[PLATBS]/){
	
			my ($info,$attr) = split(';',$item);
			my @attributes;
			if (defined $attr and $attr ne ''){
				@attributes = split(',',$attr);
			}
			
			my @infos = split(' ',$info);
			if ($infos[0] eq '#P'){
				push @return,{
					type=>'pad',
					x=>$infos[1],
					y=>$infos[2],
					symbol=>$infos[3],
					polarity=>($infos[4] eq 'P')?'positive':'negative',
					dcode => $infos[5],
					angle=>$infos[6],
					mirror=>($infos[7] eq 'Y')?'yes':'no',
					attributes=>[@attributes],
				}
			}
			elsif($infos[0] eq '#L'){
				push @return,{
					type=>'line',
					xs=>$infos[1],
					ys=>$infos[2],
					xe=>$infos[3],
					ye=>$infos[4],
					symbol=>$infos[5],
					polarity=>($infos[6] eq 'P')?'positive':'negative',
					dcode => $infos[7],  
					attributes=>[@attributes],
				}
			}
			elsif($infos[0] eq '#A'){
				push @return,{
					type=>'arc',
					xs=>$infos[1],
					ys=>$infos[2],
					xe=>$infos[3],
					ye=>$infos[4],
					xc=>$infos[5],
					yc=>$infos[6],
					symbol=>$infos[7],
					polarity=>($infos[8] eq 'P')?'positive':'negative',
					dcode => $infos[9],  
					direction=>($infos[10] eq 'Y')?'cw':'ccw',
					attributes=>[@attributes],
				}
			}
			elsif($infos[0] eq '#T'){
				my $text = join(' ',@infos[10..$#infos-1]);
				$text =~ s/^'|'$//g;
				push @return,{
					type=>'text',
					x=>$infos[1],
					y=>$infos[2],
					fontname=>$infos[3],
					polarity=>($infos[4] eq 'P')?'positive':'negative',
					angle=>$infos[5],
					mirror=>($infos[6] eq 'Y')?'yes':'no',
					x_size=>$infos[7],
					y_size=>$infos[8],
					w_factor=>$infos[9],
					text=>$text,
					attributes=>[@attributes],
					}
			}
			elsif($infos[0] eq '#B'){
				# === 2022.07.21 Song 增加barcode类型，主要是奥宝类型的解析，其他待完善
				#B 4.214057 3.802248 ECC-200 standard P 0 N E 0.044 0.044 Minimal M N N T 'B2123123SSS';.deferred,.nomenclature,.orbotech_plot_stamp
				my $text = join(' ',@infos[16..$#infos]);
				$text =~ s/^'|'$//g;
				push @return,{
					type=>'barcode',
					x=>$infos[1],
					y=>$infos[2],
					fontname=>$infos[4],
					polarity=>($infos[5] eq 'P')?'positive':'negative',
					angle=>$infos[6],
					mirror=>($infos[7] eq 'Y')?'yes':'no',
					x_size=>$infos[9],
					y_size=>$infos[10],
					matrix=>$infos[11],
					bar_marks=>($infos[12] eq 'M')?'yes':'no',
					bar_background=>$infos[13],
					bar_add_string=>$infos[14],
					bar_add_string_pos=>$infos[15],
					text=>$text,
					attributes=>[@attributes],
					}
			} else {
        		push @return,{
        			type=>'surface',
        			feats=>@infos},  
            }
            # 没获取到下面代码的精髓，暂不使用
			#elsif($infos[0] eq '#S'){
			#	$surf_num ++;
			#	#if ($par{surface}){
			#		push @{$surface->{$surf_num}},$item;
			#		push @return,{
			#			type=>'surface',
			#			feats=>$surface->{$surf_num},
			#		}
			#	#}
			#	#else{
			#	#	push @return,{
			#	#		type=>'surface',
			#	#	}
			#	#}
			#	#currently ignore surface
			#}
		}
		#elsif($par{surface}){
		#	if ($item =~ /^#O[BSEC]/){
		#		push @{$surface->{$surf_num}},$item;
		#	}
		#}
	}
	close(CSHFILE);
	
	return @return;
}


1;

__END__
2019.05.17更新如下：
更新版本：V2.1
新增通过传入正则表达式，并传回符合的层别列表：GET_MATCH_LIST

# 版本3.02
 modify by song 20190910
# 增加函数 getFeature
modify by song 20190917
# 改写了SR_FILL加了软件版本9.710.0及其他的判断

2019.10.23
作者：Chao.Song
版本：3.03
1.更新了FILL_PARAMS;

2020.06.17
作者：Chao.Song
版本：3.1
1.增加家兴更改的CREATE_LAYER方法；

2022.07.21
作者：Chao.Song
版本：3.2
1. 更新Package中的genBasic.pm dealwithFeatureFile 增加二维码类型Featurs文件识别。


