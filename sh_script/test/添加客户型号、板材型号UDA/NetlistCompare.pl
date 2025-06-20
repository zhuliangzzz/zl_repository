#!/usr/bin/perl

#use strict;
#use warnings;
#-run layer -layertype Inner
#-run layer -layertype Outer
#-run step
#-run ipc
#-run ipc -input_group


BEGIN{
    #if ( defined $ENV{INCAM_PRODUCT} ) {
    #    $ENV{CAMLIB} = "$ENV{INCAM_PRODUCT}/app_data/perl";
    #} else {
    #    $ENV{CAMLIB} = "$ENV{GENESIS_DIR}/e$ENV{GENESIS_VER}/all/perl";
    #}
    #push (@INC,$ENV{CAMLIB});
    #
    #if ( defined $ENV{INCAM_SITE_DATA_DIR} ) {
    #    $ENV{NeoM} = "$ENV{INCAM_SITE_DATA_DIR}/scripts/User/Neo/Misc/Modules";
    #    push (@INC,$ENV{NeoM});
    #}
    push (@INC,"$ENV{SCRIPTS_DIR}/sys/scripts/Package");
    use File::Basename;
    $ENV{CURRSCRIPTPATH} = dirname($0);
    $ENV{CURRSCRIPTPATH} =~ s#\\#/#g;
    push (@INC,$ENV{CURRSCRIPTPATH});
}

unless ( defined $ENV{GENESIS_TMP} ){
    $ENV{"GENESIS_TMP"} = $ENV{INCAM_TMP};
}


use Genesis;
our $f = new Genesis();

our $JOB  = $ENV{JOB};
our $STEP = $ENV{STEP};

use NeoM;
use Tkx;
use utf8;
use File::Basename;
use POSIX qw(strftime);

our ($SelLayerType,$RunType,@OptSteps);
if ( defined $ARGV[0] ) {
    if ( scalar(@ARGV) == 1 ) {
        @ARGV = split(" ",$ARGV[0]);
    }

    use Getopt::Long;
    GetOptions(
        "layertype=s"    => \$SelLayerType,    #选择的层别类型
        "steps=s{,}"    => \@OptSteps,            #Step
        "run=s"            => \$RunType,            #运行的项目 step Layer
        "input_group"            => \$OutputPathMode,            #Input组输出模式
    );
}

unless ( defined $JOB ){
    &iTkxMsgBox("JOB不存在!","JOB不存在,脚本退出!","ok","warning",);
    return -1;
}

our $JobUserDir = &igJobUserDir;

{ #主程序

    unless ( defined $OutputPathMode ) {
        our $OutputNetlistPath = 'D:/';
        if ( $^O =~ /^linux/i ) {
            $DesktopDir = &iGetDesktopDir || $ENV{HOME};
            $OutputNetlistPath = $DesktopDir;
        }
    } else {
        $DesktopDir = &iGetDesktopDir || $ENV{HOME};
        $OutputNetlistPath = $DesktopDir . '/' . 'TempOutput' . '/' . uc($JOB) . '/' . "EQ";
    }
    $OutputNetlistFile = $OutputNetlistPath . '/' . uc($JOB) . '-IpcReport.log';

    #$f->INFO( entity_type => 'root',data_type => 'JOBS_LIST' );
    #my @JobsList = @{$f->{doinfo}{gJOBS_LIST}};

    $f->INFO( entity_type => 'job',entity_path => "$JOB",data_type => 'STEPS_LIST' );
    my @StepList = @{$f->{doinfo}{gSTEPS_LIST}};

    our %JobMatrix = &JobMatrixDispose( $JOB );
    #print "44=@{$JobMatrix{SumData}{Layers}}\n";

    #$f->PAUSE($JOB);
    #our $JobSelGui;
    #our $YearMonthDay = strftime( "%y%m%d",localtime( ) );

    our $BarMsg = '欢迎进入Neo的世界.';
    our ($NetStepSel,$EditStepSel);

    #my $ThemeUse = "vista";
    my $ThemeUse = "clam";
    my ( $StepInPadX,$SelJobGuiOffset,$LayerListGuiResize, ) = ( 1,0,0, );
    #XP Windows NT 5.1    #win7 Windows NT 6.1
    if ( `uname -r` =~ /^Windows\sNT\s5\.1\s\S*/ ) {
        $SelJobGuiOffset = $SelJobGuiOffset + 23;
        $LayerListGuiResize = 8;
    }

    our $MainColor = "#F0F0F0";
    if ( $ThemeUse eq "clam" ) {
        $StepInPadX = 4;
        $SelJobGuiOffset = 2;
        if ( `uname -r` =~ /^Windows\sNT\s5\.1\s\S*/ ) {
            $SelJobGuiOffset = $SelJobGuiOffset + 24;
        }

        $MainColor = "#DCDAD5";
        Tkx::ttk__style_theme_use( "clam" );#winnative clam alt default classic vista xpnative ###Tkx::ttk__style_theme_names( );##vista
    }

    our $mw = Tkx::widget->new( ".", );
    $mw->g_wm_geometry( "+" . int( ( Tkx::winfo( 'screenwidth', $mw ) / 2 ) - 130 ) . "+" . int( ( Tkx::winfo( 'screenheight', $mw ) / 2 ) - 300 ) );
    $mw->g_wm_title( "网络比对" );
    $mw->g_wm_attributes( '-topmost',1 );
    &iTkxGetImageFile('SetMwLogo',$mw);

    ( my $ManFrame1 = $mw->new_ttk__frame( -padding => "0 0 0 0", ) )->g_pack( -fill=>'both',-side=>'top',
    #-expand => '1',
    );
    ( $ManFrame1->new_ttk__label( -text => "网络比对",-font=>['微软雅黑','14','bold'] ) )->g_pack;
    ( $ManFrame1->new_ttk__label( -text => "JOB:$JOB",-font=>['微软雅黑','12','bold'] ) )->g_pack;
    #( $ManFrame1->new_ttk__label( -text => "STEP:$STEP",-font=>['微软雅黑','12','bold'] ) )->g_pack;

    (my $NoteBookPageFrame = $mw->new_ttk__frame())->g_pack(-expand => '1',-fill=>'both',-side=>'top',);

    (our $NotebookPage = $NoteBookPageFrame->new_ttk__notebook)->g_pack(-expand => '1',-fill=>'both',);
    (my $NotebookPageLayers = $NotebookPage->new_ttk__frame(-padding => "3 3 0 3",) )->g_pack(-side=>'top',-expand => '1',-fill=>'both',);
    (my $NotebookPageStep  = $NotebookPage->new_ttk__frame(-padding => "3 3 0 3",) )->g_pack(-side=>'top',-expand => '1',-fill=>'both',);
    (my $NotebookPageIpc  = $NotebookPage->new_ttk__frame(-padding => "3 3 0 3",) )->g_pack(-side=>'top',-expand => '1',-fill=>'both',);

    $NotebookPage->add($NotebookPageLayers, -text => "Layer");
    $NotebookPage->add($NotebookPageStep, -text => "Step");
    $NotebookPage->add($NotebookPageIpc, -text => "IPC356");

    ##################################### Layer ############################################

    ( my $EditStepFrame = $NotebookPageLayers->new_ttk__frame( -padding => "3 3 3 1", ) )->g_pack(
    # -expand => '1',
     -fill=>'x', );
    ( $EditStepFrame->new_ttk__label( -text => "STEP1:" , ) )->g_pack( -side=>'left',-ipadx=> $StepInPadX, );
    ( my $NetStep = $EditStepFrame->new_ttk__combobox( -textvariable => \$NetStepSel,-values => "@StepList",-width => 5, ) )->g_pack( -side=>'left',-expand => '1',-fill=>'x', );
    $NetStep->g_bind( '<Enter>',sub {$BarMsg = "选择需要比对的Net STEP。";} );

    ( $EditStepFrame->new_ttk__label( -text => "STEP2:" , ) )->g_pack( -side=>'left',-ipadx=> $StepInPadX, );
    ( my $EditStep = $EditStepFrame->new_ttk__combobox( -textvariable => \$EditStepSel,-values => "@StepList",-width => 5, ) )->g_pack( -side=>'left',-expand => '1',-fill=>'x', );
    ( $EditStepFrame->new_ttk__label( -text => "选择:", ) )->g_pack( -side=>'left' );
    $EditStep->g_bind( '<Enter>',sub {$BarMsg = "选择需要比对的Edit STEP。";} );
    #$EditStep->g_bind( '<<ComboboxSelected>>', sub{&ShowCopySuffixOpt; } );


    $f->INFO( entity_type => 'step',entity_path => "$JOB/net",data_type => 'EXISTS' );
    if ( $f->{doinfo}{gEXISTS} eq 'yes' ) {
        $NetStepSel = 'net';
    }

    $f->INFO( entity_type => 'step',entity_path => "$JOB/edit",data_type => 'EXISTS' );
    if ( $f->{doinfo}{gEXISTS} eq 'yes' ) {
        $EditStepSel= 'edit';
    } else {
        if ( defined $STEP ){
            $EditStepSel = $STEP;
        } 
    }

    ( my $ListFrame = $NotebookPageLayers->new_ttk__frame( -padding => "3 3 3 3", ) )->g_pack( -expand => '1',-fill=>'both',-side=>'top', );
    ( $ListFrame->new_ttk__label( -text => "层别:", ) )->g_pack( -side=>'left',-ipadx=> 6, );
    ( our $LayerList = $ListFrame->new_tk__listbox( -height => 10 + $LayerListGuiResize,-width => 20 + $LayerListGuiResize,-selectmode => "extended",-selectforeground =>'white',-exportselection => 0, ) )->g_pack( -side=>'left',-expand => '1',-fill=>'both', );
    ( $tScrollbar = $ListFrame->new_ttk__scrollbar( -command => [$LayerList, "yview"], -orient => "vertical", ) )->g_pack( -side=>'left',-fill=>'y' );
    $LayerList->configure( -yscrollcommand => [$tScrollbar, "set"] );
    $LayerList->g_bind( '<Enter>',sub {$BarMsg = "左键拖动,连续选择;Ctrl+左键,间断选择。";} );

    my @LayerTypeFilter = ( "清除","线路","内层","外层", );
    my @LayerTypeFilterEn = ( "Clear","Signal","Inner","Outer", );
    my %LayerTypeTranslation;
    for ( 0 .. scalar( @LayerTypeFilterEn ) - 1 ){
        $LayerTypeTranslation{$LayerTypeFilterEn[$_]} = $LayerTypeFilter[$_] ;

    }

    my @LayerTypeFilterColor = ( "#d4d1c9","#FDC74D","#FDC74D","#FDC74D", );
    my @LayerTypeFilterSelColor = ( "#83b5e4","#98B0A6","#98B0A6","#98B0A6",);

    ( our $FilterType = $ListFrame->new_tk__listbox( -height => 10 + $LayerListGuiResize,-width => 4 + $LayerListGuiResize,-selectmode => "browse",-selectforeground =>'white',-exportselection => 0,-activestyle => 'none',-background  => '#DCDAD5',-relief => 'flat' ,
    -highlightbackground=> $MainColor,
    -highlightcolor=> $MainColor,
    -disabledforeground=> $MainColor,
     ) )->g_pack( -side=>'left',
    #-expand => '1',
    -fill=>'y', );
    $FilterType->delete( '0', 'end' );
    $FilterType->insert( 'end',@LayerTypeFilter );
    for (0 .. $#LayerTypeFilter){
        $FilterType->itemconfigure( $_,-background,$LayerTypeFilterColor[$_],-selectbackground,$LayerTypeFilterSelColor[$_],);
    }
    $FilterType->g_bind( '<B1-ButtonRelease>', sub {&FilterTypeSelect('Gui');} );
    $FilterType->g_bind( '<Enter>',sub {$BarMsg = "自动选择对应类型的层别。";} );

    ( my $ButtonFrame = $NotebookPageLayers->new_ttk__frame( -padding => "10 5 10 2", ) )->g_pack( -side=>'bottom',-fill=>'x', );
    ( $ButtonFrame->new_ttk__button( -text => "确定",-width => 12,-command => sub {&NetlistCmpLayers; }, ) )->g_pack( -side=>'left',-fill=>'x',-expand => '1' );
    ( my $ExitButton = $ButtonFrame->new_ttk__button( -text => "退出",-width => 8,-command => sub {$mw->g_destroy;}, ) )->g_pack( -side=>'left',-fill=>'x',-expand => '1' );
    #$ExitButton->g_bind( "<Button-3>", \&MainHelp, );
    #$ExitButton->g_bind( '<Enter>',sub {$BarMsg = "退出按钮右键查看帮助。";} );
    ##################################### STEP ############################################
    my $StepComboboxWidth = 13;
    ( my $StepCompareHeadFrame = $NotebookPageStep->new_ttk__frame( -padding => "3 3 3 1", ) )->g_pack( -side=>'top',
    # -expand => '1',
    # -fill=>'x',
      );
    ( $StepCompareHeadFrame->new_ttk__label( -text => "Net Step" , -width => $StepComboboxWidth, ) )->g_pack( -side=>'left',-ipadx=> $StepInPadX, );
    ( $StepCompareHeadFrame->new_ttk__label( -text => "Edit Step" , -width => $StepComboboxWidth, ) )->g_pack( -side=>'left',-ipadx=> $StepInPadX, );

    ( my $StepCompareStepFrame = $NotebookPageStep->new_ttk__frame( -padding => "3 3 3 1", ) )->g_pack( -side=>'top',
    # -expand => '1',
    # -fill=>'x',
      );

    our %StepCmpStepData;
    push @{$StepCmpStepData{Num}},"1";
    ( $StepCmpStepData{"Ram"}{"1"}{"Net"} = $StepCompareStepFrame->new_ttk__combobox( -textvariable => \$StepCmpStepData{"Step"}{"1"}{"Net"},-values => "@StepList",-width => $StepComboboxWidth, ) )->g_pack( -side=>'left',-expand => '1',-fill=>'x', );
    $StepCmpStepData{"Ram"}{"1"}{"Net"}->g_bind( '<Enter>',sub {$BarMsg = "选择需要比对的Net STEP。";} );
    ( $StepCmpStepData{"Ram"}{"1"}{"Edit"} = $StepCompareStepFrame->new_ttk__combobox( -textvariable => \$StepCmpStepData{"Step"}{"1"}{"Edit"},-values => "@StepList",-width => $StepComboboxWidth, ) )->g_pack( -side=>'left',-expand => '1',-fill=>'x', );
    $StepCmpStepData{"Ram"}{"1"}{"Edit"}->g_bind( '<Enter>',sub {$BarMsg = "选择需要比对的Edit STEP。";} );

    $f->INFO( entity_type => 'step',entity_path => "$JOB/net",data_type => 'EXISTS' );
    if ( $f->{doinfo}{gEXISTS} eq 'yes' ) {
        $StepCmpStepData{"Step"}{"1"}{"Net"} = 'net';
    }


    $f->INFO( entity_type => 'step',entity_path => "$JOB/edit",data_type => 'EXISTS' );
    if ( $f->{doinfo}{gEXISTS} eq 'yes' ) {
        $StepCmpStepData{"Step"}{"1"}{"Edit"} = 'edit';
    } else {
        if ( defined $STEP ){
            $StepCmpStepData{"Step"}{"1"}{"Edit"} = $STEP;
        }
    }


    ( my $StepCmpButtonFrame = $NotebookPageStep->new_ttk__frame( -padding => "10 5 10 2", ) )->g_pack( -side=>'bottom',-fill=>'x', );
    ( $StepCmpButtonFrame->new_ttk__button( -text => "确定",-width => 12,-command => sub { &NetlistCmpSteps ;}, ) )->g_pack( -side=>'left',-fill=>'x',-expand => '1' );
    ( my $StepCmpExitButton = $StepCmpButtonFrame->new_ttk__button( -text => "退出",-width => 8,-command => sub {$mw->g_destroy;}, ) )->g_pack( -side=>'left',-fill=>'x',-expand => '1' );


    #############################        IPC    ###################################
    (my $StepListFrame = $NotebookPageIpc->new_ttk__frame(-padding => "3 3 3 3",))->g_pack(-expand => '1',-fill=>'both',-side=>'top',);
    ( $StepListFrame->new_ttk__label(-text => "Step:",) )->g_pack(-side=>'left');
    ( our $StepList = $StepListFrame->new_tk__listbox(-height => 13,-width => 29,-selectmode => "extended",-selectforeground =>'white',-exportselection => 0,) )->g_pack(-side=>'left',-expand => '1',-fill=>'both',);
    ( $tScrollbar = $StepListFrame->new_ttk__scrollbar(-command => [$StepList, "yview"], -orient => "vertical",) )->g_pack(-side=>'left',-fill=>'y');
    $StepList->configure(-yscrollcommand => [$tScrollbar, "set"]);
    $StepList->g_bind('<Enter>',sub {$BarMsg = "左键拖动,连续选择;Ctrl+左键,间断选择。";});
    $StepList->insert( 'end',@StepList );
    
    my $tSetIpcJud = 'no';
    if ( defined $RunType ){
        if ( $RunType eq 'ipc' ) {
            if ( defined $OptSteps[0] ){
                my %tStepHash = iArr2Hash(@OptSteps);
                for my $tNum ( 0 .. $#StepList ){
                    if ( defined $tStepHash{$StepList[$tNum]}  ) {
                        $StepList->selection('set',$tNum,$tNum);
                        $tSetIpcJud = 'yes';
                    }
                }
            }
        }
    }
    
    if ( $tSetIpcJud eq 'no' ){
        if ( defined $STEP ){
            for my $tNum ( 0 .. $#StepList ){
                if ( $StepList[$tNum] eq $STEP ) {
                    $StepList->selection('set',$tNum,$tNum);
                    last;
                }
            }
        } elsif ( scalar(@StepList) == 1 ) {
            $StepList->selection('set',0,0);
        }
    }

    ( my $PathFrame = $NotebookPageIpc->new_ttk__frame(-padding => "3 3 3 3",))->g_pack(-expand => '1',-fill=>'x',-side=>'top',);
#    our $OutputNetlistCheck = 1;
    our $OutputNetlistCheck = 0;
    if ( $OutputPathMode == 1 ) {
        $OutputNetlistCheck = 1;
    }
    ($PathFrame->new_ttk__checkbutton(-text => "输出结果", -variable => \$OutputNetlistCheck, -onvalue => 1,-offvalue => 0,-command=>sub{&OutputPathShow;},))->g_pack(-side=>'left',);
    
    
    
    (our $OutputNetlistFileFrame = $PathFrame->new_ttk__frame(-padding => "0 0 0 0",));#->g_pack(-expand => '1',-fill=>'x',-side=>'left',);
#    ( $PathFrame->new_ttk__label(-text => "路径:",) )->g_pack(-side=>'left',);
    ( $OutputNetlistFileFrame->new_ttk__entry(-textvariable => \$OutputNetlistFile ,-width => 18,) )->g_pack(-side=>'left',-expand => '1',-fill=>'x',);
    Tkx::ttk__style_configure("Min.TButton",-padding => 0, );
    ( my $PathFileButton = $OutputNetlistFileFrame->new_ttk__button(-text => '...',-style => 'Min.TButton',-width => 4,) )-> g_pack(-side=>'left',-ipadx=> 0,);

    $PathFileButton-> g_bind("<Button-1>", sub {
    my $tOutputNetlistFile = Tkx::tk___getSaveFile(-initialdir=>$OutputNetlistFile,-title=> "Please enter a save path.",);
        if ( $tOutputNetlistFile ne '' ) {
            $OutputNetlistFile = $tOutputNetlistFile;
        }
    } );

    ( my $StepButtonFrame = $NotebookPageIpc->new_ttk__frame(-padding => "10 5 10 2",) )->g_pack(-side=>'bottom',-fill=>'x',);
    ( $StepButtonFrame->new_ttk__button(-text => "确定",-width => 12,-command => sub { &NetlistCmpIpc; }, ) )-> g_pack(-side=>'left',-fill=>'x',-expand => '1');
    ( $StepButtonFrame->new_ttk__button(-text => "退出",-width => 8,-command => sub {$mw->g_destroy;},) )-> g_pack(-side=>'left',-fill=>'x',-expand => '1');


    #######################################################################################

    ( my $MsgBarFrame = $mw->new_ttk__frame( -padding => "0 0 0 0", ) )->g_pack( -side=>'bottom',-fill=>'x', );
    ( $MsgBarFrame->new_ttk__sizegrip )->g_pack( -side=>'right', );
    ( $MsgBarFrame->new_ttk__label( -textvariable => \$BarMsg,-foreground =>'blue', ) )->g_pack( -side=>'left',-fill=>'x', );
    &LayerShow;
    &OutputPathShow;
    #$NotebookPage->select('.f2.n.f');
    if ( $RunType eq 'step' ) {
        $NotebookPage->select('.f2.n.f2');
    } elsif ( $RunType eq 'ipc' ) {
        $NotebookPage->select('.f2.n.f3');
    }
    
    if ( $SelLayerType ne '' ){
        &FilterTypeSelect('Parameters');
    }
    Tkx::MainLoop( );
    exit;
}
################################################################################

sub OutputPathShow { #显示 隐藏路径选项
    if ( $OutputNetlistCheck == 0 ) {
        $OutputNetlistFileFrame->g_pack_forget;
    } else {
        $OutputNetlistFileFrame->g_pack( -side=>'left',-expand => '1',-fill=>'x', );
    }
}

sub NetlistCmpLayers { #层别 网络比对
    my @SelLayerIndex = split( " ",$LayerList->curselection( ) );
    my $ErrText = '';

    if ( "$NetStepSel" eq "" ) {
        $ErrText .= "Net Step 没选择，请选择 Net Step！\n";
    } else {
        $f->INFO( entity_type => 'step',entity_path => "$JOB/$NetStepSel",data_type => 'EXISTS' );
        if ( $f->{doinfo}{gEXISTS} eq 'no' ) {
            $ErrText .= "Net Step 不存在，请重新选择 Net Step！\n";
        }
    }

    if ( "$EditStepSel" eq "" ) {
        $ErrText .= "Edit Step 没选择，请选择 Edit Step！\n";
    } else {
        $f->INFO( entity_type => 'step',entity_path => "$JOB/$EditStepSel",data_type => 'EXISTS' );
        if ( $f->{doinfo}{gEXISTS} eq 'no' ) {
            $ErrText .= "Edit Step 不存在，请重新选择 Edit Step！\n";
        }
    }

    unless ( defined $SelLayerIndex[0] ) {
        $ErrText .= "层别没选择，请选择层别！\n";
    }

    if ( "$ErrText" ne "" ){
        Tkx::tk___messageBox( -type => "ok", -message => "$ErrText",-icon => "warning",-title => "警告", -parent => $mw,);
        $mw->g_wm_deiconify;
        return -1;
    }
    
    $mw->g_wm_withdraw;

#    $f->COM('open_entity', job => $JOB, type => 'step', name => $EditStepSel, iconic => 'no');
#    $f->AUX('set_group', group => $f->{COMANS});
#    $f->COM('units', type => 'inch');

    $f->VOF;
    for my $tLayer ( @{$JobMatrix{"SumData"}{Signal}} ) {
        $f->COM('matrix_layer_context' ,job => $JOB ,matrix => 'matrix' ,layer => $tLayer ,context => 'misc');
    }
    $f->VON;

    my @DifferenceLayer;
    my @ListBoxLists = split( " ",$LayerList->get( 0,'end' ) );
    for $tIndex ( @SelLayerIndex ) {
        my $tLayer = $ListBoxLists[$tIndex] ;
        $f->VOF;
        $f->COM('matrix_layer_context' ,job => $JOB ,matrix => 'matrix' ,layer => $tLayer ,context => 'board');
        $f->VON;

        if ( $_CAMSOFT eq 'Genesis' )  {
    #        $f->COM('netlist_page_open' ,set => 'yes' ,job1 => $JOB ,job2 => $JOB);
            $f->COM('netlist_recalc' ,job => $JOB ,step => $NetStepSel ,type => 'cur' ,display => 'top');
            $f->COM('netlist_recalc' ,job => $JOB ,step => $EditStepSel ,type => 'cur' ,display => 'bottom');
            $f->COM('netlist_compare' ,job1 => $JOB ,step1 => $NetStepSel ,type1 => 'cur' ,job2 => $JOB ,step2 => $EditStepSel ,type2 => 'cur' ,display => 'yes');
    #        $f->PAUSE("$f->{COMANS}");
            my @NetlistReport = split (' ' , $f->{COMANS});
            &NetlistLogAct("Layer",$JOB,"$NetStepSel -> $EditStepSel : $tLayer",@NetlistReport,);
            if ( $NetlistReport[0] != 0 || $NetlistReport[2] != 0 )  {
    #            $f->COM('netlist_page_open' ,set => 'check' ,job1 => $JOB ,step1 => $NetStepSel ,type1 => 'cur' ,job2 => $JOB ,step2 => $EditStepSel ,type2 => 'cur');
                $f->COM('netlist_page_open');
                push @DifferenceLayer,$tLayer;
                $f->PAUSE("Please check the $tLayer Netlist!");
            }

            $f->VOF;
            $f->COM('netlist_page_close');
            $f->VON;
        } elsif ( $_CAMSOFT eq 'InCAM' ) {
            $f->COM('set_step' ,name => $NetStepSel ,);
            $f->AUX('set_group' ,group => $f->{COMANS} ,);
            $f->VOF;
            $f->COM('delete_shapelist' ,layer => 'comp' ,);
            $f->COM('netlist_ref_update' ,job => $JOB ,step => $NetStepSel ,source => 'none' ,);
            $f->VON;
            $f->COM('netlist_recalc' ,job => $JOB ,step => $NetStepSel ,type => 'cur' ,display => 'top' ,use_cad_names => 'no' ,);
            $f->COM('netlist_ref_update' ,job => $JOB ,step => $NetStepSel ,);
            #
            $f->COM('set_step' ,name => $EditStepSel ,);
            $f->AUX('set_group' ,group => $f->{COMANS} ,);
            $f->COM('rv_tab_empty' ,report => 'netlist_compare' ,is_empty => 'yes' ,);
            $f->COM('netlist_compare' ,job2 => $JOB ,step2 => $NetStepSel ,type2 => 'ref' ,recalc_cur => 'yes' ,use_cad_names => 'no' ,report_extra => 'yes' ,report_miss_on_cu => 'yes' ,report_miss => 'yes' ,
            #max_highlight_shapes => 5000 ,
			);
            my @NetlistReport = split (' ' , $f->{COMANS});
            &NetlistLogAct("Layer",$JOB,"$NetStepSel -> $EditStepSel : $tLayer",@NetlistReport,);
            if ( $NetlistReport[0] != 0 || $NetlistReport[2] != 0 )  {
                $f->COM('rv_tab_view_results' ,report => 'netlist_compare' ,);
                $f->COM('zoom_mode' ,zoom => 'pan' ,);
                $f->COM('rv_tab_view_results_enabled' ,report => 'netlist_compare' ,is_enabled => 'yes' ,serial_num => -1 ,all_count => -1 ,);
                #$f->COM('netlist_compare_results_show' ,action => 'netlist_compare' ,is_end_results => 'yes' ,is_reference_type => 'no' ,);
                $f->COM('netlist_compare_results_show' ,action => 'netlist_compare' ,is_end_results => 'yes' ,is_reference_type => 'no' ,job2 => $JOB ,step2 => $NetStepSel ,mode => 0 ,layers_list1 => '' ,layers_list2 => '' ,);
                $f->COM('edt_tab_select' ,report => 'netlist_compare' ,);
                $f->COM('show_component' ,component => 'Result_Viewer' ,show => 'yes');
                push @DifferenceLayer,$tLayer;
                $f->PAUSE("请检查 $NetStepSel -> $EditStepSel : $tLayer 的网络!");
            }
        }
        $f->VOF;
        $f->COM('matrix_layer_context' ,job => $JOB ,matrix => 'matrix' ,layer => $tLayer ,context => 'misc');
        $f->VON;
    }
    $f->VOF;
    for my $tLayer ( @{$JobMatrix{"SumData"}{Signal}} ) {
        $f->COM('matrix_layer_context' ,job => $JOB ,matrix => 'matrix' ,layer => $tLayer ,context => 'board');
    }
    $f->VON;
    
    my $tIco = 'info';
    my $tTmpEndMsgText = "单层网络比对完成。\n\n";
    if ( defined $DifferenceLayer[0] ){
        $tIco = 'warning';
        $tTmpEndMsgText .= "以下层别网络存在差异,请查看对应层别:\n  @DifferenceLayer。\n";
    } else {
        $tTmpEndMsgText .= "所有层别网络比对一致。\n";
    }
    
    if ( defined $f->COM('get_select_count') ) {
        &iTkxMsg($mw,"网络比对完成","$tTmpEndMsgText","ok",$tIco,);
    }
    $mw->g_destroy;
}

sub NetlistCmpSteps { #Step 网络比对
    my $ErrText;
    for my $tNum ( @{$StepCmpStepData{Num}} ) {
        my $tNetStep =  $StepCmpStepData{Step}{$tNum}{Net} ;
        my $tEditStep =  $StepCmpStepData{Step}{$tNum}{Edit} ;

        if ( "$tNetStep" eq "" ) {
            $ErrText .= "($tNum) Net Step 没选择，请选择 Net Step！\n";
        } else {
            $f->INFO( entity_type => 'step',entity_path => "$JOB/$tNetStep",data_type => 'EXISTS' );
            if ( $f->{doinfo}{gEXISTS} eq 'no' ) {
                $ErrText .= "($tNum)Net Step 不存在，请重新选择 Net Step！\n";
            }
        }

        if ( "$tEditStep" eq "" ) {
            $ErrText .= "($tNum)Edit Step 没选择，请选择 Edit Step！\n";
        } else {
            $f->INFO( entity_type => 'step',entity_path => "$JOB/$tEditStep",data_type => 'EXISTS' );
            if ( $f->{doinfo}{gEXISTS} eq 'no' ) {
                $ErrText .= "($tNum)Edit Step 不存在，请重新选择 Edit Step！\n";
            }
        }
    }

    if ( "$ErrText" ne "" ){
        Tkx::tk___messageBox( -type => "ok", -message => "$ErrText",-icon => "warning",-title => "警告", -parent => $mw,);
        $mw->g_wm_deiconify;
        return -1;
    }
    $mw->g_wm_withdraw;

    my @DifferenceStep;
    for my $tNum ( @{$StepCmpStepData{Num}} ) {
        my $tNetStep =  $StepCmpStepData{Step}{$tNum}{Net} ;
        my $tEditStep =  $StepCmpStepData{Step}{$tNum}{Edit} ;
        if ( $_CAMSOFT eq 'Genesis' )  {
            $f->COM('netlist_page_open' ,set => 'yes' ,job1 => $JOB ,job2 => $JOB);
            $f->COM('netlist_recalc' ,job => $JOB ,step => $NetStepSel ,type => 'cur' ,display => 'top');
            $f->COM('netlist_recalc' ,job => $JOB ,step => $EditStepSel ,type => 'cur' ,display => 'bottom');
            $f->COM('netlist_compare' ,job1 => $JOB ,step1 => $NetStepSel ,type1 => 'cur' ,job2 => $JOB ,step2 => $EditStepSel ,type2 => 'cur' ,display => 'yes');
            my @NetlistReport = split (' ' , $f->{COMANS});
            &NetlistLogAct("Step",$JOB,"$tNetStep . '=>' . $tEditStep",@NetlistReport,);
            if ( $NetlistReport[0] != 0 || $NetlistReport[2] != 0 )  {
    #            $f->COM('netlist_page_open');
                push @DifferenceStep,$tNetStep . '=>' . $tEditStep;
                $f->PAUSE("Please check the $tNetStep and $tEditStep Netlist!");
            }
            $f->VOF;
            $f->COM('netlist_page_close');
            $f->VON;
        } elsif ( $_CAMSOFT eq 'InCAM' ) {
        
            $f->COM('set_step' ,name => $tNetStep ,);
            $f->AUX('set_group' ,group => $f->{COMANS} ,);
            $f->VOF;
            $f->COM('delete_shapelist' ,layer => 'comp' ,);
            $f->COM('netlist_ref_update' ,job => $JOB ,step => $tNetStep ,source => 'none' ,);
            $f->VON;
            $f->COM('netlist_recalc' ,job => $JOB ,step => $tNetStep ,type => 'cur' ,display => 'top' ,use_cad_names => 'no' ,);
            $f->COM('netlist_ref_update' ,job => $JOB ,step => $tNetStep ,);
            #
            $f->COM('set_step' ,name => $tEditStep ,);
            $f->AUX('set_group' ,group => $f->{COMANS} ,);
            $f->COM('rv_tab_empty' ,report => 'netlist_compare' ,is_empty => 'yes' ,);
            $f->COM('netlist_compare' ,job2 => $JOB ,step2 => $tNetStep ,type2 => 'ref' ,recalc_cur => 'yes' ,use_cad_names => 'no' ,report_extra => 'yes' ,report_miss_on_cu => 'yes' ,report_miss => 'yes' ,
            #max_highlight_shapes => 5000 ,
            );
            my @NetlistReport = split (' ' , $f->{COMANS});
            &NetlistLogAct("Step",$JOB,"$tNetStep . '=>' . $tEditStep",@NetlistReport,);
            $f->COM('rv_tab_view_results' ,report => 'netlist_compare' ,);
            $f->COM('zoom_mode' ,zoom => 'pan' ,);
            $f->COM('rv_tab_view_results_enabled' ,report => 'netlist_compare' ,is_enabled => 'yes' ,serial_num => -1 ,all_count => -1 ,);
            #$f->COM('netlist_compare_results_show' ,action => 'netlist_compare' ,is_end_results => 'yes' ,is_reference_type => 'no' ,);
            $f->COM('netlist_compare_results_show' ,action => 'netlist_compare' ,is_end_results => 'yes' ,is_reference_type => 'no' ,job2 => $JOB ,step2 => $tNetStep ,mode => 0 ,layers_list1 => '' ,layers_list2 => '' ,);
            $f->COM('edt_tab_select' ,report => 'netlist_compare' ,);
            $f->COM('show_component' ,component => 'Result_Viewer' ,show => 'yes');
            
            if ( $NetlistReport[0] != 0 || $NetlistReport[2] != 0 )  {
    #            $f->COM('netlist_page_open');
                push @DifferenceStep,$tNetStep . '=>' . $tEditStep;
                $f->PAUSE("请检查 $tNetStep 和 $tEditStep 网络!");
            }
        }
    }
    my $tIco = 'info';
    my $tTmpEndMsgText = "Step网络比对完成。\n\n";
    if ( defined $DifferenceStep[0] ){
        $tIco = 'warning';
        $tTmpEndMsgText .= "以下Step网络存在差异,请查看对应Step:\n  @DifferenceStep 。\n";
    } else {
        $tTmpEndMsgText .= "所有Step网络比对一致。\n";
    }
    if ( defined $f->COM('get_select_count') ) {
        &iTkxMsg($mw,"网络比对完成","$tTmpEndMsgText","ok",$tIco,);
    }
    $mw->g_destroy;
}

sub NetlistCmpIpc { #IPC 网络比对
    my @SelStepIndex = split( " ",$StepList->curselection( ) );
    my $ErrText = '';

    unless ( defined $SelStepIndex[0] ) {
        $ErrText .= "Step没选择，请选择Step！\n";
    }
    
    if ( ( "$OutputNetlistCheck" eq 1 ) and ( $OutputNetlistFile eq '' ) ) {
        $ErrText .= "网络输出路径为空\n";
    }

    if ( "$ErrText" ne "" ){
        Tkx::tk___messageBox( -type => "ok", -message => "$ErrText",-icon => "warning",-title => "警告", -parent => $mw,);
        $mw->g_wm_deiconify;
        return -1;
    }
    $mw->g_wm_withdraw;
    
	my $cus_name = substr("$JOB", 1, 3);
	
    my @DifferenceStep;
    my @StepStepListBoxLists = split( " ",$StepList->get( 0,'end' ) );
    for $tIndex ( @SelStepIndex ) {
        my $tStep = $StepStepListBoxLists[$tIndex] ;
        if ( $_CAMSOFT eq 'Genesis' )  {
            #$f->COM('netlist_page_open' ,set => 'yes' ,job1 => $JOB ,step1 => $tStep ,type1 => 'ref' ,job2 => $JOB ,step2 => $tStep ,type2 => 'cur' ,);
            $f->COM('netlist_recalc' ,job => $JOB ,step => $tStep ,type => 'cad' ,display => 'top' ,layer_list => '' ,);
            $f->COM('netlist_recalc' ,job => $JOB ,step => $tStep ,type => 'cur' ,display => 'bottom' ,layer_list => '' ,);
            $f->COM('netlist_auto_reg' ,job => $JOB ,step => $tStep ,);
            $f->COM('cadnet_reduce_points_to_center' ,job => $JOB ,step => $tStep ,radius => 2 ,);
            $f->COM('netlist_compare' ,job1 => $JOB ,step1 => $tStep ,type1 => 'cad' ,job2 => $JOB ,step2 => $tStep ,type2 => 'cur' ,display => 'yes' ,);
            my @NetlistReport = split (' ' , $f->{COMANS});
            &NetlistLogAct("IPC356",$JOB,"$tStep",@NetlistReport,);
            $f->COM('netlist_page_open');
            # --输出报告到指定目录
            if ( "$OutputNetlistCheck" eq 1 ) {
                &iMkDir( dirname($OutputNetlistFile) );
                $f->COM('netlist_save_compare_results' ,output => 'file' ,out_file =>  $OutputNetlistFile ,);
            }
            if ( $NetlistReport[0] != 0 || $NetlistReport[2] != 0 )  {
                push @DifferenceStep,$tStep;
                $f->PAUSE("Please check the $tStep IPC Netlist!");
            }

            

            $f->VOF;
            $f->COM('netlist_page_close');
            $f->VON;
        } elsif ( $_CAMSOFT eq 'InCAM' ) {
            $f->COM('set_step' ,name => $tStep ,);
            $f->AUX('set_group' ,group => $f->{COMANS} ,);
            $f->COM('cadnet_reduce_points_to_center' ,job => $JOB ,step => $tStep ,);
#           $f->COM('display_net' ,job => $JOB ,step => $tStep ,netlist => 'cad' ,color => 1 ,section => 'first' ,nets => 'all' ,disp_mode => 'net_points' ,top_tp => 'yes' ,bot_tp => 'yes' ,drl_tp => 'yes' ,);
            $f->COM('netlist_auto_reg' ,job => $JOB ,step => $tStep ,);
#            $f->COM('netlist_recalc' ,job => $JOB ,step => $tStep ,type => 'cur' ,display => 'top' ,use_cad_names => 'yes' ,);
#            $f->COM('rv_tab_empty' ,report => 'netlist_compare' ,is_empty => 'yes' ,);
#            $f->COM('set_step' ,name => $tStep ,);
            $f->COM('rv_tab_empty' ,report => 'netlist_compare' ,is_empty => 'yes' ,);
			if ($cus_name eq '183'){
				#http://192.168.2.120:82/zentao/story-view-5930.html 按需求针对183客户 修改Extra和Missing 为no 20230825 by lyh
				$f->COM('netlist_compare' ,job2 => $JOB ,step2 => $tStep ,type2 => 'cad' ,recalc_cur => 'yes' ,use_cad_names => 'no' ,report_extra => 'no' ,report_miss_on_cu => 'no' ,report_miss => 'no' ,);
			}else{
				$f->COM('netlist_compare' ,job2 => $JOB ,step2 => $tStep ,type2 => 'cad' ,recalc_cur => 'yes' ,use_cad_names => 'yes' ,report_extra => 'yes' ,report_miss_on_cu => 'no' ,report_miss => 'yes' ,
				#max_highlight_shapes => 5000 ,
				);
			}

		   my @NetlistReport = split (' ' , $f->{COMANS});
            &NetlistLogAct("IPC356",$JOB,"$tStep",@NetlistReport,);
            $f->COM('rv_tab_view_results' ,report => 'netlist_compare' ,);
            $f->COM('zoom_mode' ,zoom => 'pan' ,);
            $f->COM('rv_tab_view_results_enabled' ,report => 'netlist_compare' ,is_enabled => 'yes' ,serial_num => -1 ,all_count => -1 ,);
            #$f->COM('netlist_compare_results_show' ,action => 'netlist_compare' ,is_end_results => 'yes' ,is_reference_type => 'no' ,);
            $f->COM('netlist_compare_results_show' ,action => 'netlist_compare' ,is_end_results => 'yes' ,is_reference_type => 'no' ,job2 => $JOB ,step2 => $tStep ,mode => 0 ,layers_list1 => '' ,layers_list2 => '' ,);
            $f->COM('edt_tab_select' ,report => 'netlist_compare' ,);
            $f->COM('show_component' ,component => 'Result_Viewer' ,show => 'yes');
            if ( "$OutputNetlistCheck" eq 1 ) {
                &iMkDir( dirname($OutputNetlistFile) );
                $f->COM('netlist_save_compare_results' ,output => 'file' ,out_file =>  $OutputNetlistFile ,);
            }
            if ( $NetlistReport[0] != 0 || $NetlistReport[2] != 0 )  {                
                push @DifferenceStep,$tStep;
                $f->PAUSE("请检查 Step $tStep IPC网络!");
            }
        }
    }
    
    my $tIco = 'info';
    my $tTmpEndMsgText = "Step网络比对完成。\n\n";
    if ( defined $DifferenceStep[0] ){
        $tIco = 'warning';
        $tTmpEndMsgText .= "以下Step IPC网络存在差异:\n  @DifferenceStep \n请检查";
    } else {
        $tTmpEndMsgText .= "所有Step IPC网络比对一致。\n";
    }    
    if ( defined $f->COM('get_select_count') ) {
        &iTkxMsg($mw,"网络比对完成","$tTmpEndMsgText","ok",$tIco,);
    }
    $mw->g_destroy;
}

sub NetlistLogAct { #日志记录文件操作
    #&NetlistLogAct("Layer",$JOB,"$NetStepSel -> $EditStepSel : $tLayer",@NetlistReport,);
    #&NetlistLogAct("Step",$JOB,"$tNetStep . '=>' . $tEditStep",@NetlistReport,);
    #&NetlistLogAct("IPC356",$JOB,"$tStep",@NetlistReport,);
    my $tLogType = shift;
    my $tJob = shift;
    my $tNetlistTypeText = shift;
    my @tNetlistResults = @_;
    #1 Shorts 8 Brokens 149 Missings 6 Extras 0 Missings SMD/BGA 0 Extras SMD/BGA
    my $tResultsName = '';
    my $tResultsNum = '';
    my $tResultsText;
    for my $tResults ( reverse @tNetlistResults ) {
        if ( $tResults =~ /^\D+$/ ){
            if ( $tResultsName eq '' ){
                $tResultsName = $tResults ;
            } else {
                $tResultsName = $tResults . " " . $tResultsName ;
            }
        } else {
            $tResultsNum =  $tResults ;
        }
        
        if ( $tResultsNum ne '' ){
            $tResultsText = "$tResultsName = $tResultsNum\n" . $tResultsText ;
            $tResultsName = '';
            $tResultsNum = '';
        }
    }
    
    $f->COM('get_user_name' ,);
    my $tUser = COMANS;
    my $dateTime = strftime( "%Y-%m-%d %H:%M:%S",localtime( ) );
    my $NetlistLogFile = $JobUserDir . "/Netlist_" . ucfirst($tLogType) . ".log";
    my $tLogHead = join (" ",'########',$dateTime,ucfirst($tLogType),$tJob,"## $tNetlistTypeText ##",$tUser,'########',);
    # my $tLogHead = join (" ",'########',"need time",ucfirst($tLogType),$tJob,"## $tNetlistTypeText ##",$tUser,'########',);

    &iWriteFile(
    '>>',$NetlistLogFile,
    $tLogHead,
    $tResultsText,
    "",
    );
}

sub LayerShow {
    my ( $tMoveGtl,$tMoveGbl,$tMove ) = ( 0,0,0 );
    $LayerList->insert( 'end',@{$JobMatrix{"SumData"}{Signal}} );
    for my $tNum ( 0 .. @{$JobMatrix{"SumData"}{"Signal"}} - 1 ){
        my $tLayer = $JobMatrix{"SumData"}{Signal}[$tNum];
        $LayerList->itemconfigure( $tNum,-background,$JobMatrix{"LayersData"}{$tLayer}{'Color'},-selectbackground,$JobMatrix{"LayersData"}{$tLayer}{'SelColor'} );
        if( defined $JobMatrix{"LayersData"}{$tLayer}{'TopSignalLayer'} ){
            $tMoveGtl = $tNum;
        } elsif ( defined $JobMatrix{"LayersData"}{$tLayer}{'BottomSignalLayer'} ){
            $tMoveGbl = $tNum;
        }
    }

    if ( $tMoveGtl == 0 ) {
        $tMove = $tMoveGbl - 5 ;
    } else {
        $tMove = $tMoveGtl - 5 ;
    }
    if ( $tMove > 0 ){
        $LayerList->yview( 'moveto', $tMove / scalar ( @{$JobMatrix{"SumData"}{Signal}} ) );
    }


}

sub FilterTypeSelect {
    my $SelMode = shift;
    my $FilterTypeSel;
    if ( $SelMode eq 'Gui' ){
        my @ListBoxLists = split( " ",$FilterType->get(0,'end') );
        my @SelListsIndex = split( " ",$FilterType->curselection() );
        $FilterTypeSel = $ListBoxLists[$SelListsIndex[0]];
    } elsif ( $SelMode eq 'Parameters' ){
        $FilterTypeSel = $LayerTypeTranslation{$SelLayerType};
    }
    if ( "$FilterTypeSel" eq '清除' ) {
        $LayerList->selection( 'clear',0,'end');
    } else {
        my $tNum = 0;
        for my $tNum ( 0 .. @{$JobMatrix{"SumData"}{"Signal"}} - 1 ){
            my $tLayer = $JobMatrix{"SumData"}{Signal}[$tNum];
            if ( defined $JobMatrix{"LayersData"}{$tLayer}{"$FilterTypeSel"} ){
                $LayerList->selection( 'set',$tNum,$tNum );
            }
            $tNum++;
        }
    }
}

sub JobMatrixDispose {    #料号Matrix处理         #my %JobMatrix = &JobMatrixDispose($JOB);
    my $CurrJob = shift;
#    print "CurrJob=$CurrJob\n";
    #3399ff 68%  覆盖  #3399ff 50%  覆盖
    if ( "$CurrJob" ne '' ) {
        $f->INFO(entity_type => 'matrix',entity_path => "$CurrJob/matrix",data_type => 'ROW',parameters => "context+layer_type+name+row+side+type");
        my %tJobMatrix;
        for my $gROWrow (@{$f->{doinfo}{gROWrow}}){
            my $tNum = $gROWrow -1;
            my $tLayerName = $f->{doinfo}{gROWname}[$tNum];
            if ( $f->{doinfo}{gROWtype}[$tNum] eq 'layer' ){
                push @{$tJobMatrix{"SumData"}{"LayerRow"}},$gROWrow;
                push @{$tJobMatrix{"SumData"}{Layers}},$f->{doinfo}{gROWname}[$tNum];
                #
                $tJobMatrix{"RowData"}{$gROWrow}{Layer} = $f->{doinfo}{gROWname}[$tNum];
                $tJobMatrix{"RowData"}{$gROWrow}{'全部'} = 'Yes';
                #
                $tJobMatrix{"LayersData"}{$tLayerName}{'Row'} = $gROWrow;
                $tJobMatrix{"LayersData"}{$tLayerName}{'全部'} = 'Yes';
                if ( $f->{doinfo}{gROWcontext}[$tNum] eq 'board'){
                    $tJobMatrix{"RowData"}{$gROWrow}{'板层'} = 'Yes';
                    $tJobMatrix{"LayersData"}{$tLayerName}{'板层'} = 'Yes';
                    #
                    push @{$tJobMatrix{"SumData"}{Board}},$f->{doinfo}{gROWname}[$tNum];
                    if ( $f->{doinfo}{gROWlayer_type}[$tNum] eq 'signal' || $f->{doinfo}{gROWlayer_type}[$tNum] eq 'power_ground' || $f->{doinfo}{gROWlayer_type}[$tNum] eq 'mixed' ) {
                        push @{$tJobMatrix{"SumData"}{Signal}},$f->{doinfo}{gROWname}[$tNum];
                        #
                        $tJobMatrix{"RowData"}{$gROWrow}{'线路'} = 'Yes';
                        $tJobMatrix{"LayersData"}{$tLayerName}{'线路'} = 'Yes';
                        if ( $f->{doinfo}{gROWlayer_type}[$tNum] eq 'signal'){
                            $tJobMatrix{"RowData"}{$gROWrow}{'Color'} = '#FDC74D';
                            $tJobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#98B0A6';
                            #
                            $tJobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#FDC74D';
                            $tJobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#98B0A6';
                        } elsif ( $f->{doinfo}{gROWlayer_type}[$tNum] eq 'power_ground') {
                            $tJobMatrix{"RowData"}{$gROWrow}{'Color'} = '#E6C412';
                            $tJobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#8CAE89';
                            #
                            $tJobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#E6C412';
                            $tJobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#8CAE89';
                        } elsif ( $f->{doinfo}{gROWlayer_type}[$tNum] eq 'mixed' ) {
                            $tJobMatrix{"RowData"}{$gROWrow}{'Color'} = '#CCCCA5';
                            $tJobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#7FB2D2';
                            #
                            $tJobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#CCCCA5';
                            $tJobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#7FB2D2';
                        }
                        #
                        if ( $f->{doinfo}{gROWside}[$tNum] eq 'top' || $f->{doinfo}{gROWside}[$tNum] eq 'bottom' ){
                            push @{$tJobMatrix{"SumData"}{Outer}},$f->{doinfo}{gROWname}[$tNum];
                            #
                            $tJobMatrix{"RowData"}{$gROWrow}{'外层'} = 'Yes';
                            $tJobMatrix{"LayersData"}{$tLayerName}{'外层'} = 'Yes';
                            if ( $f->{doinfo}{gROWside}[$tNum] eq 'top' ){
                                $tJobMatrix{"RowData"}{$gROWrow}{'TopSignalLayer'} = 'Yes';
                                $tJobMatrix{"LayersData"}{$tLayerName}{'TopSignalLayer'} = 'Yes';
                            } elsif ( $f->{doinfo}{gROWside}[$tNum] eq 'bottom' ){
                                $tJobMatrix{"RowData"}{$gROWrow}{'BottomSignalLayer'} = 'Yes';
                                $tJobMatrix{"LayersData"}{$tLayerName}{'BottomSignalLayer'} = 'Yes';
                            }
                        } elsif ( $f->{doinfo}{gROWside}[$tNum] eq 'inner' ) {
                            push @{$tJobMatrix{"SumData"}{Inner}},$f->{doinfo}{gROWname}[$tNum];
                            #
                            $tJobMatrix{"RowData"}{$gROWrow}{'内层'} = 'Yes';
                            $tJobMatrix{"LayersData"}{$tLayerName}{'内层'} = 'Yes';
                        }
                    } elsif ( $f->{doinfo}{gROWlayer_type}[$tNum] eq 'solder_mask' ) {
                        push @{$tJobMatrix{"SumData"}{SolderMask}},$f->{doinfo}{gROWname}[$tNum];
                        if ( $f->{doinfo}{gROWside}[$tNum] eq 'top' ){
                            push @{$tJobMatrix{"SumData"}{TopSolderMask}},$f->{doinfo}{gROWname}[$tNum];
                            $tJobMatrix{"RowData"}{$gROWrow}{'TopSolderMaskLayer'} = 'Yes';
                            $tJobMatrix{"LayersData"}{$tLayerName}{'TopSolderMaskLayer'} = 'Yes';

                        } elsif ( $f->{doinfo}{gROWside}[$tNum] eq 'bottom' ){
                            push @{$tJobMatrix{"SumData"}{BottomSolderMask}},$f->{doinfo}{gROWname}[$tNum];
                            $tJobMatrix{"RowData"}{$gROWrow}{'BottomSolderMaskLayer'} = 'Yes';
                            $tJobMatrix{"LayersData"}{$tLayerName}{'BottomSolderMaskLayer'} = 'Yes';
                        }
                        #
                        $tJobMatrix{"RowData"}{$gROWrow}{'阻焊'} = 'Yes';
                        $tJobMatrix{"RowData"}{$gROWrow}{'Color'} = '#00A279';
                        $tJobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#1A9DBC';
                        #
                        $tJobMatrix{"LayersData"}{$tLayerName}{'阻焊'} = 'Yes';
                        $tJobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#00A279';
                        $tJobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#1A9DBC';
                    } elsif ( $f->{doinfo}{gROWlayer_type}[$tNum] eq 'silk_screen' ) {
                        push @{$tJobMatrix{"SumData"}{SilkScreen}},$f->{doinfo}{gROWname}[$tNum];
                        if ( $f->{doinfo}{gROWside}[$tNum] eq 'top' ){
                            push @{$tJobMatrix{"SumData"}{TopSilkScreen}},$f->{doinfo}{gROWname}[$tNum];
                            $tJobMatrix{"RowData"}{$gROWrow}{'TopSilkScreenLayer'} = 'Yes';
                            $tJobMatrix{"LayersData"}{$tLayerName}{'TopSilkScreenLayer'} = 'Yes';
                        } elsif ( $f->{doinfo}{gROWside}[$tNum] eq 'bottom' ){
                            push @{$tJobMatrix{"SumData"}{BottomSilkScreen}},$f->{doinfo}{gROWname}[$tNum];
                            $tJobMatrix{"RowData"}{$gROWrow}{'BottomSilkScreenLayer'} = 'Yes';
                            $tJobMatrix{"LayersData"}{$tLayerName}{'BottomSilkScreenLayer'} = 'Yes';
                        }
                        #
                        $tJobMatrix{"RowData"}{$gROWrow}{'字符'} = 'Yes';
                        $tJobMatrix{"RowData"}{$gROWrow}{'Color'} = '#FFFFFF';
                        $tJobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#99CCFF';
                        #
                        $tJobMatrix{"LayersData"}{$tLayerName}{'字符'} = 'Yes';
                        $tJobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#FFFFFF';
                        $tJobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#99CCFF';
                    } elsif ( $f->{doinfo}{gROWlayer_type}[$tNum] eq 'solder_paste' ) {
                        push @{$tJobMatrix{"SumData"}{SolderPaste}},$f->{doinfo}{gROWname}[$tNum];
                        #
                        $tJobMatrix{"RowData"}{$gROWrow}{'钢网'} = 'Yes';
                        $tJobMatrix{"RowData"}{$gROWrow}{'Color'} = '#FFFFCE';
                        $tJobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#99CCE7';
                        #
                        $tJobMatrix{"LayersData"}{$tLayerName}{'钢网'} = 'Yes';
                        $tJobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#FFFFCE';
                        $tJobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#99CCE7';
                    } elsif ( $f->{doinfo}{gROWlayer_type}[$tNum] eq 'drill' ) {
                        push @{$tJobMatrix{"SumData"}{Drill}},$f->{doinfo}{gROWname}[$tNum];
                        $tJobMatrix{"RowData"}{$gROWrow}{'钻孔'} = 'Yes';
                        $tJobMatrix{"RowData"}{$gROWrow}{'Color'} = '#AFAFAF';
                        $tJobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#71A4D7';
                        #
                        $tJobMatrix{"LayersData"}{$tLayerName}{'钻孔'} = 'Yes';
                        $tJobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#AFAFAF';
                        $tJobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#71A4D7';
                    } elsif ( $f->{doinfo}{gROWlayer_type}[$tNum] eq 'rout' ) {
                        push @{$tJobMatrix{"SumData"}{Rout}},$f->{doinfo}{gROWname}[$tNum];
                        $tJobMatrix{"RowData"}{$gROWrow}{'Color'} = '#D4D1C9';
                        $tJobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#83B5E4';
                        #
                        $tJobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#D4D1C9';
                        $tJobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#83B5E4';
                    } elsif ( $f->{doinfo}{gROWlayer_type}[$tNum] eq 'document' ) {
                        push @{$tJobMatrix{"SumData"}{Document}},$f->{doinfo}{gROWname}[$tNum];
                        $tJobMatrix{"RowData"}{$gROWrow}{'Color'} = '#9BDBDB';
                        $tJobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#67BAED';
                        #
                        $tJobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#9BDBDB';
                        $tJobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#67BAED';
                    } else {
                        push @{$tJobMatrix{"SumData"}{Other}},$f->{doinfo}{gROWname}[$tNum];
                        #
                        $tJobMatrix{"RowData"}{$gROWrow}{'Color'} = '#9BDBDB';
                        $tJobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#67BAED';
                        #
                        $tJobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#9BDBDB';
                        $tJobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#67BAED';
                    }
                } else {
                    push @{$tJobMatrix{"SumData"}{Misc}},$f->{doinfo}{gROWname}[$tNum];
                    $tJobMatrix{"RowData"}{$gROWrow}{'Color'} = '#9BDBDB';
                    $tJobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#67BAED';
                    #
                    $tJobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#9BDBDB';
                    $tJobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#67BAED';
                }
            } else {
                push @{$tJobMatrix{"SumData"}{Empty}},$gROWrow;
                #
                if ( $f->{doinfo}{gROWlayer_type}[$tNum] eq 'document' ) {
                    push @{$tJobMatrix{"SumData"}{Document}},$f->{doinfo}{gROWname}[$tNum];
                    $tJobMatrix{"RowData"}{$gROWrow}{'Color'} = '#9BDBDB';
                    $tJobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#67BAED';
                    #
                    $tJobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#9BDBDB';
                    $tJobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#67BAED';
                }
            }
        }
#        print "22=@{$tJobMatrix{SumData}{Layers}}\n";
        return (%tJobMatrix);
    } else {
#        print "33\n";

        return ();
    }
}

