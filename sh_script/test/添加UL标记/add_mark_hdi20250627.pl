#! /usr/bin/perl -w
#### write by hyp, 9/18/2017
use strict;
use utf8;
use Tk;
use Encode;
use POSIX qw(strftime);

my $hostCur = shift;
my $JOB = $ENV{JOB};
my $STEP = $ENV{STEP};
my $jobCut = uc(substr($JOB,0,13));

my $jobNum = substr($JOB,1,3);

our $f;
our $c;
our $o;
our $dbc_i;
my $pdfPath;
if ( $ENV{INCAM_PRODUCT} ) {
    # use lib "$ENV{INCAM_PRODUCT}/app_data/perl";
    # require incam;
    # $f = new incam($hostCur);
    $pdfPath = "/windows/174.file/Drawing/${jobNum}系列/$JOB/";
    $pdfPath = '/windows/174.file/Drawing/' unless ( -d $pdfPath );
} else {
    # use lib "$ENV{GENESIS_EDIR}/all/perl";
    # require Genesis;
    # $f = new Genesis($hostCur);
    $pdfPath = encode("gbk", "//192.168.2.174/GCfiles/Drawing/${jobNum}系列/$JOB/");
    $pdfPath = encode("gbk", "//192.168.2.174/GCfiles/Drawing/") unless ( -d $pdfPath );
}
use lib "$ENV{SCRIPTS_DIR}/sys/scripts/Package";
use Genesis;
use mainVgt;
use VGT_Oracle;

# 2019.11.13李家兴添加
# --开始启动项
BEGIN
{
    # --实例化对象
    $f = new Genesis();
    $c = new mainVgt();
    $o = new VGT_Oracle();

    # --连接InPlan oracle数据库
    $dbc_i = $o->CONNECT_ORACLE('host' => '172.20.218.193', 'service_name' => 'inmind.fls', 'port' => '1521', 'user_name' => 'GETDATA', 'passwd' => 'InplanAdmin');
    if (!$dbc_i) {
        $c->Messages('warning', '"InPlan数据库"连接失败->程序终止!');
        exit(0);
    }
}
# --结束启动项
END
{
    # --断开Oracle连接
    $dbc_i->disconnect if ($dbc_i);
}

&main();

sub main
{
    exit 0 if ( ! &CamInit($JOB) );
    
    my $inplanJob = &SearchJobFromInPlan($JOB);
    if ( ! $inplanJob )
    {
        require Tk::Dialog;
        $inplanJob = '(无数据)' if ( ! $inplanJob );
        my $warn_win = MainWindow->new(-title =>"胜宏科技");
        $warn_win->geometry("+850+400");    
        $warn_win->Dialog(-title=>'Dialog', -text => "查不到InPlan数据, 请与管理员确认.\n\n当前JOB:      $JOB\nInPlan JOB:   $inplanJob", -default_button => 'Ok', -buttons => ['Ok'], -bitmap => 'error', -font => 'SimSun 11', -bg => '#9BDBDB', -fg => 'black', -command => sub{$warn_win -> destroy;exit 0} ) -> Show ();
        MainLoop;
    }
    #### Main Window ####
    require Tk::BrowseEntry;
    
    my $mw = MainWindow -> new(-title => "胜宏科技");
    $mw->bind('<Return>' => sub{ shift -> focusNext; });
    $mw->geometry("+300+50");   

    my $sh_logo;
    ( -f 'Z:/incam/server/site_data/scripts/script_sh/images/sh_log.xpm' and $sh_logo = 'Z:/incam/server/site_data/scripts/script_sh/images/sh_log.xpm' ) or $sh_logo = '/incam/server/site_data/scripts/sh1_script/images/sh_log.xpm';
    my $sh_log = $mw -> Photo('info', -file => $sh_logo);
        
    my $CAM_frm = $mw->Frame(-bg => '#9BDBDB',-borderwidth =>2,-relief => "raised",-height => 15)->pack(-side => 'top', -fill => 'x');  
    my $image_label = $CAM_frm->Label(-image => $sh_log, -border => 1, -relief => 'solid')->pack(-side => 'left',-padx => 5,-pady => 1);  
    $CAM_frm->Label(-text => '胜宏科技标记添加程序',-font => 'charter 20 bold',-bg => '#9BDBDB')->pack();
    
    my $job_info_frm=$mw->Frame(-bg => '#9BDBDB',-borderwidth =>2,-relief => "raised",-height => 5)->pack(-side=>'top',-fill=>'x');
    $job_info_frm->Label(-text =>"当前JOB: $JOB",-font => 'SimSun 11 bold',-bg => '#9BDBDB', -fg => 'blue',-height=>2)->pack(-padx => 5, -side => 'left');
    # my @work_step = grep /^(edit|set|step|imp)$/,@{&GetStepsList($JOB)};
    my @work_step = @{&GetStepsList($JOB)};
    my$stepList_sel = $job_info_frm->BrowseEntry(-label => "当前Step:", -font => 'SimSun 11 bold', -bg => '#9BDBDB', -fg => 'blue', -variable => \$STEP, -state => 'readonly', -width => 8) -> pack(-padx => 5, -side => 'left');
    map {$stepList_sel->insert("end", "$_");} @work_step;   
    #### Title
    my $title_frm=$mw->Frame(-bg => '#9BDBDB',-borderwidth => 2, -relief => "raised",-height => 5)->pack(-side => 'top', -fill => 'x');
    $title_frm->Label(-text => "  选项         添加层               symbol信息                                        其他设置                            运行", -font => 'SimSun 11 bold',-bg => '#9BDBDB', -fg => 'black',-height=>2)->pack(-padx => 5, -side => 'left');
    
    my @all_layers;
    map push(@all_layers,$_),&GetLayerListWithAttr('board','silk_screen');
    map push(@all_layers,$_),&GetLayerListWithAttr('board','solder_mask');
    map push(@all_layers,$_),&GetLayerListWithAttr('board','signal');
    
    #### ul
    # my $ul_mark_tmp = decode('utf8',&GetInfoFromInplan("SELECT ul_mark FROM `project_status_inplan` WHERE job = '$jobCut'"));
    # 2019.11.15李家兴修改SQL语句，直接从inmind.fls数据库取值，不再通过project_status_inplan中间表
    # 因为MySQ数据库升级迁移，Inplan不再抛转中间数据库
     my $ul_mark_tmp = &GetInfoFromInplanDirect(
        "SELECT
                CASE WHEN j.UL_FINAL_ IS NULL
                THEN a.VALUE              
                ELSE j.UL_FINAL_
                END UL_MARK
        FROM
                VGT_hdi.PUBLIC_ITEMS i,
                VGT_hdi.JOB_DA j,
                VGT_hdi.enum_values a,
                VGT_hdi.enum_values b,
                VGT_hdi.enum_values c,
                VGT_hdi.enum_values d
        WHERE
                i.ITEM_NAME = '$jobCut'
                AND i.item_id = j.item_id
                AND i.revision_id = j.revision_id
                AND j.UL_MARK_ = a.enum
                AND a.enum_type = '1019'
                AND j.UL_SIDE_ = b.enum
                AND b.enum_type = '1020'
                AND j.DC_TYPE_ = c.enum
                AND c.enum_type = '1001'
                AND j.DC_SIDE_ = d.enum
                AND d.enum_type = '1022'");
    # my $ul_side_tmp = decode('utf8',&GetInfoFromInplan("SELECT ul_side FROM `project_status_inplan` WHERE job = '$jobCut'"));
    # 2019.11.15李家兴修改SQL语句，直接从inmind.fls数据库取值，不再通过project_status_inplan中间表
    # 因为MySQ数据库升级迁移，Inplan不再抛转中间数据库
    my $ul_side_tmp = &GetInfoFromInplanDirect(
        "SELECT
                b.VALUE
        FROM
                VGT_hdi.PUBLIC_ITEMS i,
                VGT_hdi.JOB_DA j,
                VGT_hdi.enum_values a,
                VGT_hdi.enum_values b,
                VGT_hdi.enum_values c,
                VGT_hdi.enum_values d
        WHERE
                i.ITEM_NAME = '$jobCut'
                AND i.item_id = j.item_id
                AND i.revision_id = j.revision_id
                AND j.UL_MARK_ = a.enum
                AND a.enum_type = '1019'
                AND j.UL_SIDE_ = b.enum
                AND b.enum_type = '1020'
                AND j.DC_TYPE_ = c.enum
                AND c.enum_type = '1001'
                AND j.DC_SIDE_ = d.enum
                AND d.enum_type = '1022'");
    
    my $ul_layer_type;
    $ul_layer_type = 'silk_screen' if ( $ul_side_tmp =~ /文字/ );
    $ul_layer_type = 'solder_mask' if ( $ul_side_tmp =~ /防焊/ );
    $ul_layer_type = 'signal' if ( $ul_side_tmp =~ /蚀刻/ );

    my $ul_side;
    $ul_side = 'top' if ( $ul_side_tmp =~ /C/i );
    $ul_side = 'bottom' if ( $ul_side_tmp =~ /S/i );
    $ul_side = 'top' if ( $ul_side_tmp =~ /C.*S|S.*C/i );

    my @ul_side_layer;
    @ul_side_layer = &GetLayerListWithAttr('board',$ul_layer_type,$ul_side) if ( $ul_side and $ul_layer_type );
            
    my $ul_ck_var;
    $ul_ck_var = 1 if ( $ul_mark_tmp );
    
    my $ul_state = 'normal';
    my $ul_state2 = 'readonly';
    $ul_state2 = $ul_state = 'disable' unless ( $ul_ck_var );
    
    my ($ulOptionWidget,$ulLayerWidget,$ulSymbolWidget,$ulPolarityWidget,$ulRotateWidget,$ulMirrorWidget,$ULActionWidget,$ulXWdiget,$ulYWdiget);
    
    my $ul_frm=$mw->Frame(-bg => '#9BDBDB',-borderwidth =>2, -relief => "raised",-height => 5)->pack(-side=>'top',-fill=>'x');
    $ulOptionWidget = $ul_frm->Checkbutton(-text => 'UL标记     ', -indicatoron => 1, -activebackground => '#e6e6fa', -font => 'SimSun 12', -bg => '#9BDBDB', -fg => 'black', -variable => \$ul_ck_var,-relief => 'flat', -command => sub {&WidgetStateControl($ulOptionWidget,$ulPolarityWidget,$ulRotateWidget,$ulMirrorWidget,$ULActionWidget,$ulXWdiget,$ulYWdiget)})->pack(-side => 'left');
 
    $ulLayerWidget = $ul_frm->BrowseEntry(-label => "", -font => 'SimSun 11', -bg => '#9BDBDB', -fg => 'black', -variable => \$ul_side_layer[0], -width => 6, -state => 'readonly') -> pack(-padx => 5, -side => 'left');
    # -->取消选择工作层  AresHe 2020.11.17
    map {$ulLayerWidget->insert("end", "$_");} @all_layers;    

    my $ul_symbol = '匹配失败，手动选择'; 
    my ($sh_pattern) = $ul_mark_tmp =~ /SH(\d{0,2}) .*$/i;
    $ul_symbol = "wz-ul-sh$sh_pattern" if ($ul_mark_tmp =~ /SH/i);
    $ulSymbolWidget = $ul_frm->BrowseEntry(-label => "", -font => 'SimSun 11', -bg => '#9BDBDB', -fg => 'black', -variable => \$ul_symbol, -width => 28, -state => 'readonly') -> pack(-padx => 5, -side => 'left');
    #map {$ulSymbolWidget->insert("end", "$_");} qw(wz-ul-sh wz-ul-sh1 wz-ul-sh2 wz-ul-sh3 wz-ul-sh4 wz-ul-sh5 wz-ul-sh6 wz-ul-sh7 wz-ul-sh8 wz-ul-sh9 wz-ul-sh10 wz-ul-sh11 wz-ul-sh12 wz-ul-sh13 wz-ul-sh14 wz-ul-sh15
    #wz-ul-sh16 wz-ul-sh17 wz-ul-sh18 wz-ul-sh19 wz-ul-sh20 wz-ul-sh21 wz-ul-sh22 wz-ul-sh23 wz-ul-sh24 wz-ul-sh25 wz-ul-sh26 wz-ul-sh27 wz-ul-sh28 wz-ul-sh29 wz-ul-sh30);
    map {$ulSymbolWidget->insert("end", "$_");} qw(wz-ul-sh wz-ul-sh1 wz-ul-sh2 wz-ul-sh3 wz-ul-sh4 wz-ul-sh5 wz-ul-sh6 wz-ul-sh7 wz-ul-sh8 wz-ul-sh9 wz-ul-sh10 wz-ul-sh11 wz-ul-sh12 wz-ul-sh13 wz-ul-sh14);

    my $ul_rotate_val = 0;
    $ulRotateWidget = $ul_frm->BrowseEntry(-label => "旋转", -font => 'SimSun 11', -bg => '#9BDBDB', -fg => 'black', -variable => \$ul_rotate_val, -width => 4, -state => $ul_state2) -> pack(-padx => 5, -side => 'left');
    map {$ulRotateWidget->insert("end", "$_");} qw(0 90 180 270);
        
    my $ul_polarity_val;
    $ulPolarityWidget = $ul_frm->Checkbutton(-text => '负极性', -indicatoron => 1, -activebackground => '#e6e6fa', -font => 'SimSun 12', -bg => '#9BDBDB', -fg => 'black', -variable => \$ul_polarity_val,-relief => 'flat', -state => $ul_state, -command => sub {})->pack(-side => 'left');

    my $ul_mirror_val;
    $ul_mirror_val = 1 if ( $ul_side =~ /bottom/i );
    $ulMirrorWidget = $ul_frm->Checkbutton(-text => '镜像', -indicatoron => 1, -activebackground => '#e6e6fa', -font => 'SimSun 12', -bg => '#9BDBDB', -fg => 'black', -variable => \$ul_mirror_val,-relief => 'flat', -state => $ul_state, -command => sub {})->pack(-side => 'left');
    
    my $ul_x_size = 1;
    $ulXWdiget = $ul_frm->LabEntry(-label => 'x_scale', -labelPack => [qw/-side left -anchor w/], -labelFont => 'SimSun 12', -labelBackground => '#9BDBDB', -text => \$ul_x_size, -font => 'SimSun 11', -bg => '#9BDBDB', -fg => 'black', -width => 6, -state => $ul_state) -> pack(-padx => 5, -side => 'left');    

    my $ul_y_size = 1;
    $ulYWdiget = $ul_frm->LabEntry(-label => 'y_scale', -labelPack => [qw/-side left -anchor w/], -labelFont => 'SimSun 12', -labelBackground => '#9BDBDB', -text => \$ul_y_size, -font => 'SimSun 11', -bg => '#9BDBDB', -fg => 'black', -width => 6, -state => $ul_state) -> pack(-padx => 5, -side => 'left');
    
    $ULActionWidget = $ul_frm->Button(-text => '执行', -command => sub{&ULAction($mw,$ulOptionWidget,$ulLayerWidget,$ulSymbolWidget,$ulPolarityWidget,$ulRotateWidget,$ulMirrorWidget,$ulXWdiget,$ulYWdiget)}, -width => 10, -activebackground => '#e6e6fa', -font => 'SimSun 10', -bg => '#9BDBDB', -fg => 'black', -height => 2, -state => $ul_state )->pack(-side => 'right');  
      
    #### period
    # my $period_tmp = decode('utf8',&GetInfoFromInplan("SELECT dc_side FROM `project_status_inplan` WHERE job = '$jobCut'"));
    # 2019.11.15李家兴修改SQL语句，直接从inmind.fls数据库取值，不再通过project_status_inplan中间表
    # 因为MySQ数据库升级迁移，Inplan不再抛转中间数据库
    my $period_tmp = &GetInfoFromInplanDirect(
        "SELECT
                d.VALUE
        FROM
                VGT_hdi.PUBLIC_ITEMS i,
                VGT_hdi.JOB_DA j,
                VGT_hdi.enum_values a,
                VGT_hdi.enum_values b,
                VGT_hdi.enum_values c,
                VGT_hdi.enum_values d
        WHERE
                i.ITEM_NAME = '$jobCut'
                AND i.item_id = j.item_id
                AND i.revision_id = j.revision_id
                AND j.UL_MARK_ = a.enum
                AND a.enum_type = '1019'
                AND j.UL_SIDE_ = b.enum
                AND b.enum_type = '1020'
                AND j.DC_TYPE_ = c.enum
                AND c.enum_type = '1001'
                AND j.DC_SIDE_ = d.enum
                AND d.enum_type = '1022'");

    my $period_ck_var = 0;
    my $period_layer_type;
    my $period_side;
    my $period_context;
    if ( $period_tmp && $period_tmp ne '/' ) 
    {
        $period_ck_var = 1;
        
        $period_layer_type = 'silk_screen' if ( $period_tmp =~ /文字/ );
        $period_layer_type = 'solder_mask' if ( $period_tmp =~ /防焊/ );
        $period_layer_type = 'signal' if ( $period_tmp =~ /蚀刻/ );
        
        $period_side = 'top' if ( $period_tmp =~ /C/i );
        $period_side = 'bottom' if ( $period_tmp =~ /S/i );
        $period_side = 'top' if ( $period_tmp =~ /C.*S|S.*C/i );
        
        # $period_context = &GetInfoFromInplan("SELECT dc_format FROM `project_status_inplan` WHERE job = '$jobCut'");
        # 2019.11.15李家兴修改SQL语句，直接从inmind.fls数据库取值，不再通过project_status_inplan中间表
        # 因为MySQ数据库升级迁移，Inplan不再抛转中间数据库
        $period_context = &GetInfoFromInplanDirect(
            "SELECT
                    c.VALUE
            FROM
                    VGT_hdi.PUBLIC_ITEMS i,
                    VGT_hdi.JOB_DA j,
                    VGT_hdi.enum_values a,
                    VGT_hdi.enum_values b,
                    VGT_hdi.enum_values c,
                    VGT_hdi.enum_values d
            WHERE
                    i.ITEM_NAME = '$jobCut'
                    AND i.item_id = j.item_id
                    AND i.revision_id = j.revision_id
                    AND j.UL_MARK_ = a.enum
                    AND a.enum_type = '1019'
                    AND j.UL_SIDE_ = b.enum
                    AND b.enum_type = '1020'
                    AND j.DC_TYPE_ = c.enum
                    AND c.enum_type = '1001'
                    AND j.DC_SIDE_ = d.enum
                    AND d.enum_type = '1022'");
    }
    
    my $period_state = 'normal';
    my $period_state2 = 'readonly';
    $period_state2 = $period_state = 'disable' unless ( $period_ck_var );    

    my ($periodOptionWidget,$periodLayerWidget,$periodSymbolWidget,$periodPolarityWidget,$periodRotateWidget,$periodMirrorWidget,$PeriodActionWidget,$periodDateWidget,$periodAttrWidget,$periodXWdiget,$periodYWdiget);

    my $period_frm=$mw->Frame(-bg => '#9BDBDB',-borderwidth => 2, -relief => "raised",-height => 5)->pack(-side => 'top',-fill => 'x');
    $periodOptionWidget = $period_frm->Checkbutton(-text => '周期 (um)  ', -activebackground => '#e6e6fa', -font => 'SimSun 12', -bg => '#9BDBDB', -fg => 'black', -variable => \$period_ck_var,-relief => 'flat', -command => sub {&WidgetStateControl($periodOptionWidget,$periodPolarityWidget,$periodRotateWidget,$periodMirrorWidget,$PeriodActionWidget,$periodDateWidget,$periodAttrWidget,$periodXWdiget,$periodYWdiget)})->pack(-side => 'left');

    my @period_side_layer_name;
    @period_side_layer_name = &GetLayerListWithAttr('board',$period_layer_type,$period_side) if ( $period_side and $period_layer_type );
    $periodLayerWidget = $period_frm->BrowseEntry(-label => "", -font => 'SimSun 11', -bg => '#9BDBDB', -fg => 'black', -variable => \$period_side_layer_name[0], -width => 6, -state => 'readonly') -> pack(-padx => 5, -side => 'left');
    #map {$periodLayerWidget->insert("end", "$_");} @all_layers;

    my $period_symbol = '匹配失败，手动选择';
    my $period_remark;
    if ( $period_context =~ /^yyww$/i )
    {
        $period_symbol = 'yyww';
        $period_remark = strftime "%y%U", localtime(time);
    } elsif ( $period_context =~ /^wwyy$/i )
    {
        $period_symbol = 'wwyy';
        $period_remark = strftime "%U%y", localtime(time);            
    } elsif ( $period_context =~ /^yyddmm$/i )
    {
        $period_symbol = 'yyddmm';
        $period_remark = strftime "%y%d%m", localtime(time);       
    }
    
    my @periodSymbols = qw(zq-1888 yyww wwyy yyddmm);
    
    $periodSymbolWidget = $period_frm->BrowseEntry(-label => "", -font => 'SimSun 12', -bg => '#9BDBDB', -fg => 'black', -variable => \$period_symbol, -width => 8, -state => 'readonly', -browsecmd => sub{&ChangeDateFormat($periodSymbolWidget,$periodDateWidget)}) -> pack(-padx => 5, -side => 'left');
    map {$periodSymbolWidget->insert("end", "$_");} (@periodSymbols);
    
    $periodDateWidget = $period_frm->Entry(-text => \$period_remark, -font => 'SimSun 12', -bg => '#9BDBDB', -fg => 'black', -width => 6, -state => $period_state) -> pack(-padx => 5, -side => 'left');
	
	#20221031 周涌通知改为默认 动态 by lyh
    my $period_attr_val = '动态';
    $periodAttrWidget = $period_frm->BrowseEntry(-label => "属性", -font => 'SimSun 12', -bg => '#9BDBDB', -fg => 'black', -variable => \$period_attr_val, -width => 6, -state => $period_state2) -> pack(-padx => 5, -side => 'left');
    map {$periodAttrWidget->insert("end", "$_");} qw(None 动态 静态);
            
    my $period_rotate_val = 0;
    $periodRotateWidget = $period_frm->BrowseEntry(-label => "旋转", -font => 'SimSun 12', -bg => '#9BDBDB', -fg => 'black', -variable => \$period_rotate_val, -width => 4, -state => $period_state2) -> pack(-padx => 5, -side => 'left');
    map {$periodRotateWidget->insert("end", "$_");} qw(0 90 180 270);
        
    my $period_polarity_val;
    $periodPolarityWidget = $period_frm->Checkbutton(-text => '负极性', -indicatoron => 1, -activebackground => '#e6e6fa', -font => 'SimSun 12', -bg => '#9BDBDB', -fg => 'black', -variable => \$period_polarity_val, -relief => 'flat', -state => $period_state, -command => sub {})->pack(-side => 'left');
    
    my $period_mirror_val;
    $period_mirror_val = 1 if ( $period_side =~ /bottom/i );
    $periodMirrorWidget = $period_frm->Checkbutton(-text => '镜像', -indicatoron => 1, -activebackground => '#e6e6fa', -font => 'SimSun 12', -bg => '#9BDBDB', -fg => 'black', -variable => \$period_mirror_val,-relief => 'flat', -state => $period_state, -command => sub {})->pack(-side => 'left');

    my $period_x_size = 40;
    $periodXWdiget = $period_frm->LabEntry(-label => 'x_size ', -labelPack => [qw/-side left -anchor w/], -labelFont => 'SimSun 12', -labelBackground => '#9BDBDB', -text => \$period_x_size, -font => 'SimSun 11', -bg => '#9BDBDB', -fg => 'black', -width => 6, -state => $period_state) -> pack(-padx => 5, -side => 'left');    

    my $period_y_size = 60;
    $periodYWdiget = $period_frm->LabEntry(-label => 'y_size ', -labelPack => [qw/-side left -anchor w/], -labelFont => 'SimSun 12', -labelBackground => '#9BDBDB', -text => \$period_y_size, -font => 'SimSun 11', -bg => '#9BDBDB', -fg => 'black', -width => 6, -state => $period_state) -> pack(-padx => 5, -side => 'left');  
    
    $PeriodActionWidget = $period_frm->Button(-text => '执行', -command => sub{&PeriodAction($mw,$periodOptionWidget,$periodLayerWidget,$periodSymbolWidget,$periodPolarityWidget,$periodRotateWidget,$periodMirrorWidget,$periodDateWidget,$periodAttrWidget,$periodXWdiget,$periodYWdiget)}, -width => 10, -activebackground => '#e6e6fa', -font => 'SimSun 10', -bg => '#9BDBDB', -fg => 'black', -height=> 2, -state => $period_state)->pack(-side => 'right');        

    #### triangle
    my ($triangleOptionWidget,$triangleLayerWidget,$triangleSymbolWidget,$trianglePolarityWidget,$triangleRotateWidget,$triangleMirrorWidget,$triangleActionWidget,$triangleXWdiget,$triangleYWdiget);
    
    my $triangle_frm=$mw->Frame(-bg => '#9BDBDB',-borderwidth =>2, -relief => "raised",-height => 5)->pack(-side=>'top',-fill=>'x');
    
    my $triangle_ck_var = 0;
    $triangle_ck_var = 1 if ($ul_mark_tmp =~ /三角/);
    
    $triangleOptionWidget = $triangle_frm->Checkbutton(-text => '三角形     ', -indicatoron => 1, -activebackground => '#e6e6fa', -font => 'SimSun 12', -bg => '#9BDBDB', -fg => 'black', -variable => \$triangle_ck_var, -relief => 'flat', -command => sub {&WidgetStateControl($triangleOptionWidget,$trianglePolarityWidget,$triangleRotateWidget,$triangleMirrorWidget,$triangleActionWidget,,$triangleXWdiget,$triangleYWdiget)})->pack(-side => 'left');
 
    my $triangle_side_layer = $ul_side_layer[0];
    $triangleLayerWidget = $triangle_frm->BrowseEntry(-label => "", -font => 'SimSun 11', -bg => '#9BDBDB', -fg => 'black', -variable => \$triangle_side_layer, -width => 6, -state => 'readonly') -> pack(-padx => 5, -side => 'left');
    #map {$triangleLayerWidget->insert("end", "$_");} @all_layers;    

    my $triangle_symbol = '手动选择';
    $triangleSymbolWidget = $triangle_frm->BrowseEntry(-label => "", -font => 'SimSun 11', -bg => '#9BDBDB', -fg => 'black', -variable => \$triangle_symbol, -width => 28, -state => 'readonly') -> pack(-padx => 5, -side => 'left');
    map {$triangleSymbolWidget->insert("end", "$_");} qw(NULL);
    
    my $triangle_state = 'normal';
    my $triangle_state2 = 'readonly';    
    $triangle_state2 = $triangle_state = 'disable' unless ( $triangle_ck_var );

    my $triangle_rotate_val = 0;
    $triangleRotateWidget = $triangle_frm->BrowseEntry(-label => "旋转", -font => 'SimSun 11', -bg => '#9BDBDB', -fg => 'black', -variable => \$triangle_rotate_val, -width => 4, -state => $triangle_state2) -> pack(-padx => 5, -side => 'left');
    map {$triangleRotateWidget->insert("end", "$_");} qw(0 90 180 270);
        
    my $triangle_polarity_val;
    $trianglePolarityWidget = $triangle_frm->Checkbutton(-text => '负极性', -indicatoron => 1, -activebackground => '#e6e6fa', -font => 'SimSun 12', -bg => '#9BDBDB', -fg => 'black', -variable => \$triangle_polarity_val,-relief => 'flat', -state => $triangle_state, -command => sub {})->pack(-side => 'left');
    
    my $triangle_mirror_val;
    $triangleMirrorWidget = $triangle_frm->Checkbutton(-text => '镜像', -indicatoron => 1, -activebackground => '#e6e6fa', -font => 'SimSun 12', -bg => '#9BDBDB', -fg => 'black', -variable => \$triangle_mirror_val, -relief => 'flat', -state => $triangle_state, -command => sub {})->pack(-side => 'left');

    my $triangle_x_size = 1;
    $triangleXWdiget = $triangle_frm->LabEntry(-label => 'x_scale', -labelPack => [qw/-side left -anchor w/], -labelFont => 'SimSun 12', -labelBackground => '#9BDBDB', -text => \$triangle_x_size, -font => 'SimSun 11', -bg => '#9BDBDB', -fg => 'black', -width => 6, -state => $triangle_state) -> pack(-padx => 5, -side => 'left');    

    my $triangle_y_size = 1;
    $triangleYWdiget = $triangle_frm->LabEntry(-label => 'y_scale', -labelPack => [qw/-side left -anchor w/], -labelFont => 'SimSun 12', -labelBackground => '#9BDBDB', -text => \$triangle_y_size, -font => 'SimSun 11', -bg => '#9BDBDB', -fg => 'black', -width => 6, -state => $triangle_state) -> pack(-padx => 5, -side => 'left');
        
    $triangleActionWidget = $triangle_frm->Button(-text => '执行', -command => sub{&triangleAction($mw,$triangleOptionWidget,$triangleLayerWidget,$triangleSymbolWidget,$trianglePolarityWidget,$triangleRotateWidget,$triangleMirrorWidget)}, -width => 10, -activebackground => '#e6e6fa', -font => 'SimSun 10', -bg => '#9BDBDB', -fg => 'black', -height=> 2, -state => $triangle_state )->pack(-side => 'right');  
    #### RoHS
    my ($rohsOptionWidget,$rohsLayerWidget,$rohsSymbolWidget,$rohsPolarityWidget,$rohsRotateWidget,$rohsMirrorWidget,$rohsActionWidget,$rohsXWdiget,$rohsYWdiget);    
    my $rohs_frm=$mw->Frame(-bg => '#9BDBDB',-borderwidth =>2, -relief => "raised",-height => 5)->pack(-side=>'top',-fill=>'x');
    
    my $rohs_ck_var = 0; 
    
    $rohsOptionWidget = $rohs_frm->Checkbutton(-text => 'RoHS标记   ', -indicatoron => 1, -activebackground => '#e6e6fa', -font => 'SimSun 12', -bg => '#9BDBDB', -fg => 'black', -variable => \$rohs_ck_var, -relief => 'flat', -command => sub {&WidgetStateControl($rohsOptionWidget,$rohsPolarityWidget,$rohsRotateWidget,$rohsMirrorWidget,$rohsActionWidget,$rohsXWdiget,$rohsYWdiget)})->pack(-side => 'left');
 
    my $rohs_side_layer = $ul_side_layer[0];
    $rohsLayerWidget = $rohs_frm->BrowseEntry(-label => "", -font => 'SimSun 11', -bg => '#9BDBDB', -fg => 'black', -variable => \$rohs_side_layer, -width => 6, -state => 'readonly') -> pack(-padx => 5, -side => 'left');
    #map {$rohsLayerWidget->insert("end", "$_");} @all_layers;    

    my $rohs_symbol = '手动选择';
    $rohsSymbolWidget = $rohs_frm->BrowseEntry(-label => "", -font => 'SimSun 11', -bg => '#9BDBDB', -fg => 'black', -variable => \$rohs_symbol, -width => 28, -state => 'readonly') -> pack(-padx => 5, -side => 'left');
    map {$rohsSymbolWidget->insert("end", "$_");} qw(004rohs  727rohs  78rohs  h015-rohs  h173rohs  rohs1  rohs2  ul-rohs);
    
    my $rohs_state = 'normal';
    my $rohs_state2 = 'readonly';
    $rohs_state2 = $rohs_state = 'disable' unless ( $rohs_ck_var );

    my $rohs_rotate_val = 0;
    $rohsRotateWidget = $rohs_frm->BrowseEntry(-label => "旋转", -font => 'SimSun 11', -bg => '#9BDBDB', -fg => 'black', -variable => \$rohs_rotate_val, -width => 4, -state => $rohs_state2) -> pack(-padx => 5, -side => 'left');
    map {$rohsRotateWidget->insert("end", "$_");} qw(0 90 180 270);
        
    my $rohs_polarity_val;
    $rohsPolarityWidget = $rohs_frm->Checkbutton(-text => '负极性', -indicatoron => 1, -activebackground => '#e6e6fa', -font => 'SimSun 12', -bg => '#9BDBDB', -fg => 'black', -variable => \$rohs_polarity_val,-relief => 'flat', -state => $rohs_state, -command => sub {})->pack(-side => 'left');
    
    my $rohs_mirror_val;
    $rohsMirrorWidget = $rohs_frm->Checkbutton(-text => '镜像', -indicatoron => 1, -activebackground => '#e6e6fa', -font => 'SimSun 12', -bg => '#9BDBDB', -fg => 'black', -variable => \$rohs_mirror_val, -relief => 'flat', -state => $rohs_state, -command => sub {})->pack(-side => 'left');

    my $rohs_x_size = 1;
    $rohsXWdiget = $rohs_frm->LabEntry(-label => 'x_scale', -labelPack => [qw/-side left -anchor w/], -labelFont => 'SimSun 12', -labelBackground => '#9BDBDB', -text => \$rohs_x_size, -font => 'SimSun 11', -bg => '#9BDBDB', -fg => 'black', -width => 6, -state => $rohs_state) -> pack(-padx => 5, -side => 'left');    

    my $rohs_y_size = 1;
    $rohsYWdiget = $rohs_frm->LabEntry(-label => 'y_scale', -labelPack => [qw/-side left -anchor w/], -labelFont => 'SimSun 12', -labelBackground => '#9BDBDB', -text => \$rohs_y_size, -font => 'SimSun 11', -bg => '#9BDBDB', -fg => 'black', -width => 6, -state => $rohs_state) -> pack(-padx => 5, -side => 'left');
        
    $rohsActionWidget = $rohs_frm->Button(-text => '执行', -command => sub{&RohsAction($mw,$rohsOptionWidget,$rohsLayerWidget,$rohsSymbolWidget,$rohsPolarityWidget,$rohsRotateWidget,$rohsMirrorWidget,$rohsXWdiget,$rohsYWdiget)}, -width => 10, -activebackground => '#e6e6fa', -font => 'SimSun 10', -bg => '#9BDBDB', -fg => 'black', -height=> 2, -state => $triangle_state )->pack(-side => 'right');  
    #### Pb
    my ($pbOptionWidget,$pbLayerWidget,$pbSymbolWidget,$pbPolarityWidget,$pbRotateWidget,$pbMirrorWidget,$pbActionWidget,$pbXWdiget,$pbYWdiget);    
    my $pb_frm=$mw->Frame(-bg => '#9BDBDB',-borderwidth =>2, -relief => "raised",-height => 5)->pack(-side=>'top',-fill=>'x');
    
    my $pb_ck_var = 0; 
    
    $pbOptionWidget = $pb_frm->Checkbutton(-text => 'pb标记     ', -indicatoron => 1, -activebackground => '#e6e6fa', -font => 'SimSun 12', -bg => '#9BDBDB', -fg => 'black', -variable => \$pb_ck_var, -relief => 'flat', -command => sub {&WidgetStateControl($pbOptionWidget,$pbPolarityWidget,$pbRotateWidget,$pbMirrorWidget,$pbActionWidget,$pbXWdiget,$pbYWdiget)})->pack(-side => 'left');

    my $pb_side_layer = $ul_side_layer[0]; 
    $pbLayerWidget = $pb_frm->BrowseEntry(-label => "", -font => 'SimSun 11', -bg => '#9BDBDB', -fg => 'black', -variable => \$pb_side_layer, -width => 6, -state => 'readonly') -> pack(-padx => 5, -side => 'left');
    #map {$pbLayerWidget->insert("end", "$_");} @all_layers;    

    my $pb_symbol = '手动选择';
    $pbSymbolWidget = $pb_frm->BrowseEntry(-label => "", -font => 'SimSun 11', -bg => '#9BDBDB', -fg => 'black', -variable => \$pb_symbol, -width => 28, -state => 'readonly') -> pack(-padx => 5, -side => 'left');
    map {$pbSymbolWidget->insert("end", "$_");} qw(pb ul-pb);
    
    my $pb_state = 'normal';
    my $pb_state2 = 'readonly';
    $pb_state2 = $pb_state = 'disable' unless ( $pb_ck_var );

    my $pb_rotate_val = 0;
    $pbRotateWidget = $pb_frm->BrowseEntry(-label => "旋转", -font => 'SimSun 11', -bg => '#9BDBDB', -fg => 'black', -variable => \$pb_rotate_val, -width => 4, -state => $pb_state2) -> pack(-padx => 5, -side => 'left');
    map {$pbRotateWidget->insert("end", "$_");} qw(0 90 180 270);
        
    my $pb_polarity_val;
    $pbPolarityWidget = $pb_frm->Checkbutton(-text => '负极性', -indicatoron => 1, -activebackground => '#e6e6fa', -font => 'SimSun 12', -bg => '#9BDBDB', -fg => 'black', -variable => \$pb_polarity_val,-relief => 'flat', -state => $pb_state, -command => sub {})->pack(-side => 'left');
    
    my $pb_mirror_val;
    $pbMirrorWidget = $pb_frm->Checkbutton(-text => '镜像', -indicatoron => 1, -activebackground => '#e6e6fa', -font => 'SimSun 12', -bg => '#9BDBDB', -fg => 'black', -variable => \$pb_mirror_val, -relief => 'flat', -state => $pb_state, -command => sub {})->pack(-side => 'left');

    my $pb_x_size = 1;
    $pbXWdiget = $pb_frm->LabEntry(-label => 'x_scale', -labelPack => [qw/-side left -anchor w/], -labelFont => 'SimSun 12', -labelBackground => '#9BDBDB', -text => \$pb_x_size, -font => 'SimSun 11', -bg => '#9BDBDB', -fg => 'black', -width => 6, -state => $pb_state) -> pack(-padx => 5, -side => 'left');    

    my $pb_y_size = 1;
    $pbYWdiget = $pb_frm->LabEntry(-label => 'y_scale', -labelPack => [qw/-side left -anchor w/], -labelFont => 'SimSun 12', -labelBackground => '#9BDBDB', -text => \$pb_y_size, -font => 'SimSun 11', -bg => '#9BDBDB', -fg => 'black', -width => 6, -state => $pb_state) -> pack(-padx => 5, -side => 'left');    
    
    $pbActionWidget = $pb_frm->Button(-text => '执行', -command => sub{&PbAction($mw,$pbOptionWidget,$pbLayerWidget,$pbSymbolWidget,$pbPolarityWidget,$pbRotateWidget,$pbMirrorWidget,$pbXWdiget,$pbYWdiget)}, -width => 10, -activebackground => '#e6e6fa', -font => 'SimSun 10', -bg => '#9BDBDB', -fg => 'black', -height=> 2, -state => $pb_state )->pack(-side => 'right'); 
    #### jobName
    my $jobName_ck_var = 1;
    my $jobName_layer_type;
    my $jobName_side;
    my $jobName_context;
    
    my $jobName_state = 'normal';
    my $jobName_state2 = 'readonly';
    $jobName_state2 = $jobName_state = 'disable' unless ( $jobName_ck_var );    

    my ($jobNameOptionWidget,$jobNameLayerWidget,$jobNameSymbolWidget,$jobNamePolarityWidget,$jobNameRotateWidget,$jobNameMirrorWidget,$JobNameActionWidget,$jobNameDateWidget,$jobNameAttrWidget,$jobNameXWdiget,$jobNameYWdiget);

    my $jobName_frm=$mw->Frame(-bg => '#9BDBDB',-borderwidth => 2, -relief => "raised",-height => 5)->pack(-side => 'top',-fill => 'x');
    $jobNameOptionWidget = $jobName_frm->Checkbutton(-text => 'Job名称    ', -activebackground => '#e6e6fa', -font => 'SimSun 12', -bg => '#9BDBDB', -fg => 'black', -variable => \$jobName_ck_var,-relief => 'flat', -command => sub {&WidgetStateControl($jobNameOptionWidget,$jobNamePolarityWidget,$jobNameRotateWidget,$jobNameMirrorWidget,$JobNameActionWidget,$jobNameDateWidget,$jobNameAttrWidget,$jobNameXWdiget,$jobNameYWdiget)})->pack(-side => 'left');

    my $jobName_side_layer_name = 'c1';
    $jobNameLayerWidget = $jobName_frm->BrowseEntry(-label => "", -font => 'SimSun 11', -bg => '#9BDBDB', -fg => 'black', -variable => \$jobName_side_layer_name, -width => 6, -state => 'readonly') -> pack(-padx => 5, -side => 'left');
    #map {$jobNameLayerWidget->insert("end", "$_");} @all_layers;

    my $jobName_remark = $JOB;
    $jobNameDateWidget = $jobName_frm->BrowseEntry(-label => "", -font => 'SimSun 11', -bg => '#9BDBDB', -fg => 'black', -variable => \$jobName_remark, -width => 14, -state => 'readonly') -> pack(-padx => 5, -side => 'left');

    my $jobName_attr_val = '动态';
    $jobNameAttrWidget = $jobName_frm->BrowseEntry(-label => "属性", -font => 'SimSun 12', -bg => '#9BDBDB', -fg => 'black', -variable => \$jobName_attr_val, -width => 6, -state => $jobName_state2) -> pack(-padx => 5, -side => 'left');
    map {$jobNameAttrWidget->insert("end", "$_");} qw(动态 静态);
            
    my $jobName_rotate_val = 0;
    $jobNameRotateWidget = $jobName_frm->BrowseEntry(-label => "旋转", -font => 'SimSun 11', -bg => '#9BDBDB', -fg => 'black', -variable => \$jobName_rotate_val, -width => 4, -state => $jobName_state2) -> pack(-padx => 5, -side => 'left');
    map {$jobNameRotateWidget->insert("end", "$_");} qw(0 90 180 270);
        
    my $jobName_polarity_val;
    $jobNamePolarityWidget = $jobName_frm->Checkbutton(-text => '负极性', -indicatoron => 1, -activebackground => '#e6e6fa', -font => 'SimSun 12', -bg => '#9BDBDB', -fg => 'black', -variable => \$jobName_polarity_val, -relief => 'flat', -state => $jobName_state, -command => sub {})->pack(-side => 'left');
    
    my $jobName_mirror_val;
    $jobName_mirror_val = 1 if ( $jobName_side =~ /bottom/i );
    $jobNameMirrorWidget = $jobName_frm->Checkbutton(-text => '镜像', -indicatoron => 1, -activebackground => '#e6e6fa', -font => 'SimSun 12', -bg => '#9BDBDB', -fg => 'black', -variable => \$jobName_mirror_val,-relief => 'flat', -state => $jobName_state, -command => sub {})->pack(-side => 'left');

    my $jobName_x_size = 100;
    $jobNameXWdiget = $jobName_frm->LabEntry(-label => 'x_size ', -labelPack => [qw/-side left -anchor w/], -labelFont => 'SimSun 12', -labelBackground => '#9BDBDB', -text => \$jobName_x_size, -font => 'SimSun 11', -bg => '#9BDBDB', -fg => 'black', -width => 6, -state => $jobName_state) -> pack(-padx => 5, -side => 'left');    

    my $jobName_y_size = 100;
    $jobNameYWdiget = $jobName_frm->LabEntry(-label => 'y_size ', -labelPack => [qw/-side left -anchor w/], -labelFont => 'SimSun 12', -labelBackground => '#9BDBDB', -text => \$jobName_y_size, -font => 'SimSun 11', -bg => '#9BDBDB', -fg => 'black', -width => 6, -state => $jobName_state) -> pack(-padx => 5, -side => 'left');  
    
    $JobNameActionWidget = $jobName_frm->Button(-text => '执行', -command => sub{&JobNameAction($mw,$jobNameOptionWidget,$jobNameLayerWidget,$jobNameSymbolWidget,$jobNamePolarityWidget,$jobNameRotateWidget,$jobNameMirrorWidget,$jobNameDateWidget,$jobNameAttrWidget,$jobNameXWdiget,$jobNameYWdiget)}, -width => 10, -activebackground => '#e6e6fa', -font => 'SimSun 10', -bg => '#9BDBDB', -fg => 'black', -height=> 2, -state => $jobName_state)->pack(-side => 'right');        
    #### Remark
    my $remark_frm=$mw->Frame(-bg => '#9BDBDB', -borderwidth => 2, -relief => "raised", -height => 5)->pack(-side => 'top', -fill => 'x');
    $remark_frm->Label(-text => 'Tips:N/A',-font => 'SimSun 11', -bg => '#9BDBDB', -fg => 'black', -height => 3)->pack(-side => 'left', -pady => '2');
    $remark_frm->Button(-text => '打开PDF', -command => sub{&OpenPDF($mw,$pdfPath)}, -width => 10, -activebackground => '#e6e6fa', -font => 'SimSun 10', -bg => '#9BDBDB', -fg => 'black', -height=> 2, -state => 'normal' )->pack(-side => 'right');    
    
    #### Run or Exit 
    my $perform_frm=$mw->Frame(-bg => '#9BDBDB',-borderwidth => 2, -relief => "raised",-height => 5)->pack(-side => 'top',-fill => 'both',-expand => 0);
    $perform_frm->Button(-text => '退出', -command => sub {print "exit\n";$mw -> destroy; &ScriptRunRecord("add_mark.pl","/incam/server/site_data/scripts/hyp/script_run_record.log",$JOB,$STEP); exit(0)}, -width => 10, -activebackground => '#e6e6fa', -font => 'SimSun 9', -bg => '#9BDBDB', -fg => 'black', -height => 2 )->pack( -side => 'left', -padx => 5, -pady => 5, -fill => 'both', -expand => 1);
    
    MainLoop;
}

sub CamInit
{
    my $jobCur = shift;
    if ( ! $jobCur )
    {
        my $mw = MainWindow -> new(-title => '胜宏科技');
        $mw -> messageBox(-icon => 'info',-message => '请打开一个JOB，谢谢.', -title => '胜宏科技', -type => 'ok');
        $mw -> destroy;
        MainLoop;
        return 0;    
    }
    $f->COM("filter_reset,filter_name=popup"); 
    $f->COM("affected_layer, name = , mode = all, affected = no");
    $f->COM("clear_layers");
    $f->COM("units,type=mm");   
    return 1;
}

sub SearchJobFromInPlan
{
    my $jobName = shift;
    return $jobName;
}
sub GetStepsList
{
    $f->INFO(entity_type => 'matrix',
             entity_path => "$JOB/matrix",
             data_type => 'COL',
             parameters => "step_name");
    return $f->{doinfo}{gCOLstep_name};    
}

sub GetInfoFromInplanDirect
{
    my $sql = shift;
    my $sth = $dbc_i->prepare($sql);
    $sth->execute() or die "无法执行SQL语句:$dbc_i->errstr";
    my $RV = $sth->fetchrow_array;
    return $RV;
}

sub GetInfoFromInplan
{
    my $sql = shift;
    use DBI;
    my $dbname = "project_status";
    my $location = "192.168.2.19";
    my $port = "3306";
    my $database = "DBI:mysql:$dbname:$location:$port";
    my $db_user = "root";
    my $db_pass = "k06931!";
    my $dbh = DBI->connect($database,$db_user,$db_pass);
    $dbh->do("SET NAMES utf8");
    my $sth = $dbh->prepare($sql);
    $sth->execute() or die "无法执行SQL语句:$dbh->errstr";
    my $RV = $sth->fetchrow_array;
    $sth->finish;
    $dbh->disconnect;
    return $RV;
}
sub GetLayerListWithAttr
{
    my ($context,$type,$side) = @_;
    
    $f->COM("affected_layer,name=,mode=all,affected=no");
    $f->COM("affected_filter,filter=(type=$type&context=$context&side=$side)") if ( $side =~ /top|bottom/i );
    $f->COM("affected_filter,filter=(type=$type&context=$context") if ( $side !~ /top|bottom/i );

    $f->COM("get_affect_layer");
    
    my @affect_layer = split (/\s+/,$f->{COMANS});
    $f->COM("affected_layer,name=,mode=all,affected=no");
    return @affect_layer;    
}
sub ULAction
{
    my ($mw,$ulOptionWidget,$ulLayerWidget,$ulSymbolWidget,$ulPolarityWidget,$ulRotateWidget,$ulMirrorWidget,$ulXWdiget,$ulYWdiget) = @_;
    
    my $layer = ${$ulLayerWidget->cget(-variable)};
    my $symbol = ${$ulSymbolWidget->cget(-variable)};
    
    return 0 if ( ! &layerAndSymbolCheck($layer,$symbol) );

    my $polarity;
    $polarity = 'negative' if (${$ulPolarityWidget->cget(-variable)});
    $polarity = 'positive' unless (${$ulPolarityWidget->cget(-variable)});

    my $rotate = ${$ulRotateWidget->cget(-variable)};
    
    my $mirror;
    $mirror = 'yes' if (${$ulMirrorWidget->cget(-variable)});
    $mirror = 'no' unless (${$ulMirrorWidget->cget(-variable)});

    my $ul_x_size = ${$ulXWdiget->cget(-text)};
    my $ul_y_size = ${$ulYWdiget->cget(-text)};
    
    $mw->withdraw;
    $f->COM("import_lib_item_to_job,src_category=symbols,src_profile=system,src_customer=,dst_names=$symbol");
    $f->COM("display_layer,name=$layer,display=yes,number=1");
    $f->COM("work_layer,name=$layer");
    $f->COM("units,type=inch");
    $f->COM("filter_reset,filter_name=popup");    
    my @point;
    $f->MOUSE("p select point");
    @point = split(' ',$f->{MOUSEANS});
    $f->COM("cur_atr_set,attribute=.string,text=ul_$symbol");
    $f->COM("add_pad,attributes=yes,x=$point[0],y=$point[1],symbol=$symbol,polarity=$polarity,angle=$rotate,mirror=$mirror,nx=1,ny=1,dx=0,dy=0,xscale=$ul_x_size,yscale=$ul_y_size");
    $f->COM('cur_atr_reset');
    $mw->deiconify;
    $mw->raise;
    return 1;
}

sub PeriodAction
{
    my ($mw,$periodOptionWidget,$periodLayerWidget,$periodSymbolWidget,$periodPolarityWidget,$periodRotateWidget,$periodMirrorWidget,$periodDateWidget,$periodAttrWidget,$periodXWdiget,$periodYWdiget) = @_;

    my $layer = ${$periodLayerWidget->cget(-variable)};
    my $symbol = ${$periodSymbolWidget->cget(-variable)};
    
    return 0 if ( ! &layerAndSymbolCheck($layer,$symbol) );

    my $polarity;
    $polarity = 'negative' if (${$periodPolarityWidget->cget(-variable)});
    $polarity = 'positive' unless (${$periodPolarityWidget->cget(-variable)});

    my $rotate = ${$periodRotateWidget->cget(-variable)};
    
    my $mirror;
    $mirror = 'yes' if (${$periodMirrorWidget->cget(-variable)});
    $mirror = 'no' unless (${$periodMirrorWidget->cget(-variable)});

    my $period_attr_val = ${$periodAttrWidget->cget(-variable)};
    
    my $dateStr;
    if ( $period_attr_val =~ /动态/ )
    {
        $dateStr = '$$yy$$ww' if ($symbol =~ /yyww/);
        $dateStr = '$$ww$$yy' if ($symbol =~ /wwyy/);
        $dateStr = '$$yy$$dd$$mm' if ($symbol =~ /yyddmm/);
    } else {
        $dateStr = ${$periodDateWidget->cget(-text)};    
    }
    
    my $period_x_size = ${$periodXWdiget->cget(-text)} / 1000;
    my $period_y_size = ${$periodYWdiget->cget(-text)} / 1000;
    
    $mw->withdraw;    
        
    $f->COM("display_layer,name=$layer,display=yes,number=1");
    $f->COM("work_layer,name=$layer");
    $f->COM("units,type=inch");
    $f->COM("filter_reset,filter_name=popup");
    my @point;
    $f->MOUSE("p select point");
    @point = split(' ',$f->{MOUSEANS});
    my $vgt_date='vgt_date';
	$vgt_date='vgt_date_318' if ($JOB=~/^[a-z]318/);
	
    if ( $symbol =~ /zq-1888/i )
    {
        $f->COM("add_pad,attributes=no,x=$point[0],y=$point[1],symbol=$symbol,polarity=$polarity,angle=$rotate,mirror=$mirror,nx=1,ny=1,dx=0,dy=0,xscale=1,yscale=1");
    } else {
        $f->COM("add_text,attributes=no,type=string,x=$point[0],y=$point[1],text=$dateStr,x_size=$period_x_size,y_size=$period_y_size,w_factor=0.5,polarity=$polarity,angle=$rotate,mirror=$mirror,fontname=$vgt_date,ver=1");    
    }
    
    
    $mw->deiconify;    
    $mw->raise;
    return 1;
}

sub RohsAction
{
    my ($mw,$rohsOptionWidget,$rohsLayerWidget,$rohsSymbolWidget,$rohsPolarityWidget,$rohsRotateWidget,$rohsMirrorWidget,$rohsXWdiget,$rohsYWdiget) = @_;
    
    my $layer = ${$rohsLayerWidget->cget(-variable)};
    my $symbol = ${$rohsSymbolWidget->cget(-variable)};
    
    if ( ! &layerAndSymbolCheck($layer,$symbol) )
    {
        return 0;
    }

    my $polarity;
    $polarity = 'negative' if (${$rohsPolarityWidget->cget(-variable)});
    $polarity = 'positive' unless (${$rohsPolarityWidget->cget(-variable)});

    my $rotate = ${$rohsRotateWidget->cget(-variable)};
    
    my $mirror;
    $mirror = 'yes' if (${$rohsMirrorWidget->cget(-variable)});
    $mirror = 'no' unless (${$rohsMirrorWidget->cget(-variable)});

    my $rohs_x_size = ${$rohsXWdiget->cget(-text)};
    my $rohs_y_size = ${$rohsYWdiget->cget(-text)};
    
    $mw->withdraw;
    
    $f->COM("display_layer,name=$layer,display=yes,number=1");
    $f->COM("work_layer,name=$layer");
    $f->COM("units,type=inch");
    $f->COM("filter_reset,filter_name=popup");    
    my @point;
    $f->MOUSE("p select point");
    @point = split(' ',$f->{MOUSEANS});
    $f->COM("cur_atr_set,attribute=.string,text=rohs_$symbol");
    $f->COM("add_pad,attributes=yes,x=$point[0],y=$point[1],symbol=$symbol,polarity=$polarity,angle=$rotate,mirror=$mirror,nx=1,ny=1,dx=0,dy=0,xscale=$rohs_x_size,yscale=$rohs_y_size");
    $f->COM("cur_atr_reset");
    $mw->deiconify;
    $mw->raise;
    return 1;
}

sub PbAction
{
    my ($mw,$pbOptionWidget,$pbLayerWidget,$pbSymbolWidget,$pbPolarityWidget,$pbRotateWidget,$pbMirrorWidget,$pbXWdiget,$pbYWdiget) = @_;
    
    my $layer = ${$pbLayerWidget->cget(-variable)};
    my $symbol = ${$pbSymbolWidget->cget(-variable)};
    
    if ( ! &layerAndSymbolCheck($layer,$symbol) )
    {
        return 0;
    }

    my $polarity;
    $polarity = 'negative' if (${$pbPolarityWidget->cget(-variable)});
    $polarity = 'positive' unless (${$pbPolarityWidget->cget(-variable)});

    my $rotate = ${$pbRotateWidget->cget(-variable)};
    
    my $mirror;
    $mirror = 'yes' if (${$pbMirrorWidget->cget(-variable)});
    $mirror = 'no' unless (${$pbMirrorWidget->cget(-variable)});

    my $pb_x_size = ${$pbXWdiget->cget(-text)};
    my $pb_y_size = ${$pbYWdiget->cget(-text)};
    
    $mw->withdraw;

    $f->COM("display_layer,name=$layer,display=yes,number=1");
    $f->COM("work_layer,name=$layer");
    $f->COM("units,type=inch");
    $f->COM("filter_reset,filter_name=popup");    
    my @point;
    $f->MOUSE("p select point");
    @point = split(' ',$f->{MOUSEANS});
    $f->COM("cur_atr_set,attribute=.string,text=pb_$symbol");
    $f->COM("add_pad,attributes=yes,x=$point[0],y=$point[1],symbol=$symbol,polarity=$polarity,angle=$rotate,mirror=$mirror,nx=1,ny=1,dx=0,dy=0,xscale=$pb_x_size,yscale=$pb_y_size");
    $f->COM("cur_atr_reset");
    $mw->deiconify;
    $mw->raise;
    return 1;
}

sub JobNameAction
{
    my ($mw,$jobNameOptionWidget,$jobNameLayerWidget,$jobNameSymbolWidget,$jobNamePolarityWidget,$jobNameRotateWidget,$jobNameMirrorWidget,$jobNameDateWidget,$jobNameAttrWidget,$jobNameXWdiget,$jobNameYWdiget) = @_;

    my $layer = ${$jobNameLayerWidget->cget(-variable)};
    
    my $polarity;
    $polarity = 'negative' if (${$jobNamePolarityWidget->cget(-variable)});
    $polarity = 'positive' unless (${$jobNamePolarityWidget->cget(-variable)});

    my $rotate = ${$jobNameRotateWidget->cget(-variable)};
    
    my $mirror;
    $mirror = 'yes' if (${$jobNameMirrorWidget->cget(-variable)});
    $mirror = 'no' unless (${$jobNameMirrorWidget->cget(-variable)});

    my $jobName_attr_val = ${$jobNameAttrWidget->cget(-variable)};
    
    my $jobCurrentName;
    if ( $jobName_attr_val =~ /动态/ )
    {
        $jobCurrentName = '$$job'; 
    } else {
        $jobCurrentName = ${$jobNameDateWidget->cget(-text)};    
    }
    
    my $jobName_x_size = ${$jobNameXWdiget->cget(-text)} / 1000;
    my $jobName_y_size = ${$jobNameYWdiget->cget(-text)} / 1000;
    
    $mw->withdraw;    
        
    $f->COM("display_layer,name=$layer,display=yes,number=1");
    $f->COM("work_layer,name=$layer");
    $f->COM("units,type=inch");
    $f->COM("filter_reset,filter_name=popup");
    my @point;
    $f->MOUSE("p select point");
    @point = split(' ',$f->{MOUSEANS});
    
    $jobCurrentName = uc $jobCurrentName;
    $f->COM("add_text,attributes=no,type=string,x=$point[0],y=$point[1],text=$jobCurrentName,x_size=$jobName_x_size,y_size=$jobName_y_size,w_factor=0.5,polarity=$polarity,angle=$rotate,mirror=$mirror,fontname=simple,ver=1");
    $mw->deiconify;    
    $mw->raise;
    return 1;	
}

sub WidgetStateControl
{
    my $optionWidget = shift;
    map $_->configure(-state=>'disable'),@_ unless (${$optionWidget->cget(-variable)});
    map $_->configure(-state=>'normal'),@_ if (${$optionWidget->cget(-variable)});
    return 1;
}
sub OpenPDF
{
    my ($mw,$path) = @_;
    #print "path=$path\n";
    #my $file = $mw->getOpenFile(-title => "打开PDF", -initialdir => $path);
    
    my $file = `/incam/server/site_data/scripts/User/Neo/Tools/StandardDialogs.Neo -dir $path`;
    chomp $file ;
    if ( "$file" ne '' ) {
        if ($^O =~ /MSWin32/ && $file)
        {
            my $fileEncode = encode('gbk',$file); 
            system("start acrord32 $fileEncode");
        } elsif ($^O =~ /linux/ && $file) {
            system(qq{evince "$file" &});    
        } else {
            return 0;
        }
    }
    return 1;
}
sub ChangeDateFormat
{
    my ($periodSymbolWidget,$periodDateWidget) = @_;
    
    my $period_remark;
    $period_remark = strftime "1888", localtime(time) if ( ${$periodSymbolWidget->cget(-variable)} =~ /zq-1888/i );
    $period_remark = strftime "%y%U", localtime(time) if ( ${$periodSymbolWidget->cget(-variable)} =~ /yyww/i );
    $period_remark = strftime "%U%y", localtime(time) if ( ${$periodSymbolWidget->cget(-variable)} =~ /wwyy/i );
    $period_remark = strftime "%y%d%m", localtime(time) if ( ${$periodSymbolWidget->cget(-variable)} =~ /yyddmm/i );
    
    $periodDateWidget->configure(-text=>\$period_remark);
    return 1;
}

sub layerAndSymbolCheck
{
    my ($layer,$symbol) = @_;
    if ( ! $layer or ! $symbol or $symbol =~ /匹配失败/ )
    {
        $f->PAUSE("Warning: No layer or symbol found");
        return 0;
    }
    return 1;
}
    
sub ScriptRunRecord
{
    my ($scriptName,$recordFile,$job,$step) = @_;
    use POSIX qw(strftime);
    $f->COM('get_user_name');
    my $userName = $f->{COMANS};
    my $hostName = `hostname`;
    chomp $hostName;
    open(FILE, ">>$recordFile") or warn "Can't access file $recordFile: $!";
    # 2017-11-17 15:22:23 hyp incam12 outer_compensation.pl     
    my $timeNow = strftime "%F %H:%M:%S", localtime(time);
    print FILE "$timeNow $userName $hostName $scriptName $job $step\n";
    close FILE;
    return 1;
}




