#!/usr/bin/perl

BEGIN{
	# our $CamLib = "$ENV{GENESIS_EDIR}/all/perl";
	# if ( defined $ENV{INCAM_PRODUCT} ) {
		# $CamLib = "/incam/server/site_data/scripts/Package";
	# }
}

use File::Basename;
use MIME::Base64;
use utf8;

use lib "$ENV{INCAM_PRODUCT}/app_data/perl";
use Genesis;
my $f = new Genesis();

our $perlPath = "/opt/ActivePerl-5.14/bin/perl";
our $JOB = $ENV{JOB};
our $STEP = $ENV{STEP};

our $CurrScriptFile = $0;
$CurrScriptFile =~ s#\\#/#g;

unless (defined $ENV{GENESIS_TMP} ){
	$ENV{"GENESIS_TMP"} = $ENV{INCAM_TMP};
}

#ShowSub=Box; #Pre Text Box Post

#&MainGui;
print "@ARGV\n";
if ( ! defined $ARGV[0] ){
	&CallGui;
}else{
	if ( $ARGV[0] =~ /^Run:.*/i ) {
		my ($RunSubName) = ($ARGV[0] =~ /^Run:(.*)$/i);
		&$RunSubName(@ARGV);
	} elsif ( $ARGV[0] =~ /^Gui:.*/i ) { ##CreateCoverLayer ChangeSilkMinLineWidth TextAndTextBoxSeparated SilkBridgeOpt TextCoverTextBox SolderMaskCoverTextBox
		my ($SingleGuiMode) = ($ARGV[0] =~ /^Gui:(.*)$/i);
		&ShowSingleGui($SingleGuiMode);
	} elsif ( $ARGV[0] =~ /^ConfigFile=.*/i or $ARGV[0] eq 'NoJob' or $ARGV[0] =~ /^[^=]+=[^=]+/i )  {
		&CallGui;
#	} elsif ( $ARGV[0] eq 'SilkScreenCoverLayerCreate' ) {
#		&SilkScreenCoverLayerCreate(@ARGV);
#	} elsif ( $ARGV[0] eq 'SemiAutoWordBoxZoom' ) {
#		&SemiAutoWordBoxZoom(@ARGV);
	} elsif ( $ARGV[0] eq 'Show' or $ARGV[0] eq 'NoJobShow' ) {
		&MainGui;
	} else{
		&MainGui;
	}
}

sub CallGui {
	unless (defined $ENV{INCAM_PRODUCT}) {
#		&MsgBox("运行环境错误","warning","ok","请在InCAM软件中运行此程序,\n程序退出！",);
		my $tMw = Tkx::widget->new(".");
		$tMw->g_wm_attributes('-topmost',1);
		$tMw->g_wm_geometry("0x0");
		$tMw->g_wm_withdraw;
		my $MsgOut = Tkx::tk___messageBox(-type => "ok",-message => "请在InCAM软件中运行此程序,\n程序退出！",-icon => "warning",-title => "运行环境错误",-parent => $tMw,	);
		$tMw->g_destroy;
		Tkx::MainLoop();
		exit;
	}

	my $ShowSub;
	for my $tARGV (@ARGV) {
		for my $nARGV ( split ( ",",$tARGV ) ) {
			if ($nARGV =~ /^ShowSub=.*/i ) {
				($ShowSub) = ($nARGV =~ /^\w+=(.*)$/i);
			}
		}
	}

	my $OtherParam;
	if ( defined $ShowSub ) {
		$OtherParam .= ",ShowSub=$ShowSub";
	}

	my %JobMatrix = &JobMatrixDispose($JOB);

	my %InCamPidData;
	my @ProcessInfo = qx /ps -ef/;
	my $CurrPid = $$;
	my $CurrParentPid;
	my %ProcessInfodata;
	my $GetInCamPid;
	for my $tInfoLine (@ProcessInfo){
		my @tInfoLineList = split (/\s+/,$tInfoLine);
		if ( $tInfoLineList[0] eq '' ) {
			shift @tInfoLineList;
		}

		$ProcessInfodata{"ParentPid"}{$tInfoLineList[1]} = $tInfoLineList[2];
		if ( $tInfoLineList[7] =~ m#/bin/InCAM$# ){
			push @{$InCamPidData{"Sum"}},$tInfoLineList[1];
			$InCamPidData{"Pid"}{$tInfoLineList[1]} = yes;
		}
		if ( $tInfoLineList[1] eq $CurrPid ){
			$CurrParentPid = $tInfoLineList[2];
		}

	}

	our $JOB = $ENV{JOB};
	our $STEP = $ENV{STEP};
#		$f->PAUSE("JOB=$JOB,STEP=$STEP,");

	unless ( defined $InCamPidData{"Pid"}{$CurrParentPid} ) {
		for ( 1 .. 10 ){
			$CurrParentPid = $ProcessInfodata{"ParentPid"}{$CurrParentPid} ;
			if ( defined $InCamPidData{"Pid"}{$CurrParentPid} ) {
				$GetInCamPid = $CurrParentPid;
				last;
			}
		}
	} else {
		$GetInCamPid = $CurrParentPid;
	}
	
	$GetInCamPid = $ENV{CURRENTPIDNUM} if ( defined $ENV{CURRENTPIDNUM});
	
	my $CurrHost = `hostname`;
	chomp $CurrHost;

	my ($CurrVncDisplay) = ($ENV{DISPLAY} =~ /:(\d+)\./);
	#	$CurrVncDisplay =~

	my $DisplayName;

	if ( $CurrVncDisplay == 0 ){
		$DisplayName = $CurrHost . '.' . $CurrHost;
	} else {
		$DisplayName = $CurrHost . '.' . $CurrHost . ':' . $CurrVncDisplay;
	}

	my $CurrUser = $ENV{INCAM_USER};
	# = $CurrVncDisplay

	#system ("echo $GetInCamPid,$DisplayName,$CurrUser,$JOB,$STEP,");
	#$f->PAUSE($GetInCamPid,$DisplayName);


	my $CurFile = (fileparse($CurrScriptFile, qw/\.exe \.com \.pl/))[1];
#	my $DevNullFile = '/dev/null';
	my $DevNullFile = '/tmp/Neo';



	our $GatewayPath = $ENV{INCAM_PRODUCT} . "/bin/gateway";
	my $HotKey = 'Ctrl+Shift+F12';
#	$f->PAUSE("11=@{$JobMatrix{SumData}{SilkScreen}}");
	my $SilkScreenLayer = join ('@',@{$JobMatrix{"SumData"}{"SilkScreen"}},);
	my $TParameters = encode_base64("Show ID=$GetInCamPid,Display=$DisplayName,JOB=$JOB,STEP=$STEP,SilkScreenLayer=$SilkScreenLayer,User=$CurrUser,GatewayPath=$GatewayPath,HotKey=$HotKey,$OtherParam,");
#	my $TParameters = "Show ID=$GetInCamPid,Display=$DisplayName,JOB=$JOB,STEP=$STEP,SilkScreenLayer=$SilkScreenLayer,User=$CurrUser,GatewayPath=$GatewayPath,HotKey=$HotKey,$OtherParam,";
	$TParameters =~ s/\s//g;
	my @aParameters = split (//,$TParameters);

	my $bParameters;
	if ($aParameters[$#aParameters - 1 ] eq '=' ){
		$bParameters = join( '', ( reverse ( @aParameters[0 .. $#aParameters - 2 ] ) ) ) . ',';
	} elsif ($aParameters[$#aParameters ] eq '=' ){
		$bParameters = join( '', ( reverse ( @aParameters[0 .. $#aParameters - 1 ] ) ) ) . '.';
	} else {
		$bParameters = join( '', ( reverse ( @aParameters ) ) );
	}
#    if ($aParameters[$#aParameters - 1 ] eq '=' ){
#		$bParameters = join( '', ( @aParameters[0 .. $#aParameters - 2 ] ) )  . ',';
#	} elsif ($aParameters[$#aParameters ] eq '=' ){
#		$bParameters = join( '', ( @aParameters[0 .. $#aParameters - 1 ] ) ) . '.';
#	} else {
#		$bParameters = join( '', (@aParameters) );
#	}
    print "$TParameters\n";


	my $tCshFile = $ENV{GENESIS_TMP} . "/gedit.Incam." . sprintf("%04d",rand(9999999999));
	open  DH, ">$tCshFile" or die "$!";
	if ( $CurrScriptFile =~ /.*\.pl$/i ) {
		print DH "$perlPath $CurrScriptFile $bParameters" . ' >& ' . "$DevNullFile" . ' &' . "\n\n";
	}else{
		print DH "$CurrScriptFile $bParameters" . ' >& ' . "$DevNullFile" . ' &' . "\n\n";
	}
	close DH;

	if (-e "$tCshFile") {
		system("csh $tCshFile");
#		unlink "$tCshFile";
	 }else{
	  return -1;
	}

}

sub MainGui {

	my %ShowSubConv = (
		'Pre'  => 1,
		'Box'  => 2,
		'Text' => 3,
		'Post' => 4,
	);

	our $ImagePath = "$ENV{INCAM_SITE_DATA_DIR}/scripts/User/Neo/Images/GIF";

	use threads;
	use threads::shared;

#	my $TParameters = encode_base64("Show ID=$CamParentProcessId,Display=$DisplayName,JOB=$JOB,STEP=$STEP,User=$CurrUser,GatewayPath=$GatewayPath,HotKey=$HotKey,");
	#yum install libX11-devel libXt-devel libXtst-devel
	our $ShareJob:shared;
	our $ShareStep:shared;

	my ($filename, $directories) = (fileparse($CurrScriptFile, qw/\.exe \.com \.pl \.Neo/))[0,1];
	our $MyScriptFile =  "$directories"."$filename" . '.cshrc';
	unless ( -e $MyScriptFile ) {
		$MyScriptFile = $0 ;
	}
	
	
	our $TextSeparatedLayerSuffix = '-text+';#分离的文字层后缀


	my @aParameters = split (//,$ARGV[0]);
	my $bParameters;
	if ($aParameters[$#aParameters] eq ',' ){
		$bParameters = join( '', ( reverse ( @aParameters[0 .. $#aParameters - 1 ] ) ) ) . '==';
	}elsif ($aParameters[$#aParameters] eq '.' ){
		$bParameters = join( '', ( reverse ( @aParameters[0 .. $#aParameters - 1 ] ) ) ) . '=';
	} else {
		$bParameters = join( '', ( reverse ( @aParameters ) ) );
	}
	@ARGV = split (' ',decode_base64($bParameters));

#	system ("echo @ARGV");
	our %MainConfig;
#	my ($JOB,$STEP,$User,$Display,);
	for my $tARGV (@ARGV) {
		chomp $tARGV;
		for my $nARGV ( split ( ",",$tARGV ) ) {
			if ( $nARGV =~ /^JOB=.*/i ) {
				($ShareJob) = ($nARGV =~ /^\w+=(.*)$/i);
			}elsif ( $nARGV =~ /^STEP=.*/i ) {
				($ShareStep) = ($nARGV =~ /^\w+=(.*)$/i);
			}elsif ( $nARGV =~ /^User=.*/i ) {
				($MainConfig{"User"}) = ($nARGV =~ /^\w+=(.*)$/i);
			}elsif ( $nARGV =~ /^SilkScreenLayer=.*/i ) {
				($MainConfig{"SilkScreenLayer"}) = ($nARGV =~ /^\w+=(.*)$/i);
			}elsif ( $nARGV =~ /^Display=.*/i ) {
				($MainConfig{"Display"}) = ($nARGV =~ /^\w+=(.*)$/i);
			}elsif ( $nARGV =~ /^ID=.*/i ) {
				($MainConfig{"ID"}) = ($nARGV =~ /^\w+=(.*)$/i);
			}elsif ( $nARGV =~ /^GatewayPath=.*/i ) {
				($MainConfig{"GatewayPath"}) = ($nARGV =~ /^\w+=(.*)$/i);
			}elsif ( $nARGV =~ /^HotKey=.*/i ) {
				($MainConfig{"HotKey"}) = ($nARGV =~ /^\w+=(.*)$/i);
			}elsif ( $nARGV =~ /^(\w+)=(.*)/i ) {
				($MainConfig{$1}) = $2;
			}
		}
	}
#	our $GetDisplay =
	$MainConfig{"GetDisplay"} = '%'. $MainConfig{ID} . '@' . $MainConfig{Display};
	system("python /incam/server/site_data/scripts/lyh/messageBox.py $MainConfig{GetDisplay}");
	my @SilkScreenList = split ('@',$MainConfig{"SilkScreenLayer"});


	use Tkx;
#	use Tkx::LabEntry;

	use File::Basename;
	use utf8;

	#my $ThemeUse = "vista";
	my $ThemeUse = "clam";
	my ($StepInPadX,$SelJobGuiOffset,$LayerListGuiResize,) = (1,0,0,);
	our $MainColor = "#F0F0F0";
	if ( $ThemeUse eq "clam" ) {
		$StepInPadX = 4;
		$SelJobGuiOffset = 2;
	#	if ( `uname -r` =~ /^Windows\sNT\s5\.1\s\S*/ ) {
	#		$SelJobGuiOffset = $SelJobGuiOffset + 24;
	#	}
		$MainColor = "#DCDAD5";
		Tkx::ttk__style_theme_use("clam");#winnative clam alt default classic vista xpnative ###Tkx::ttk__style_theme_names();##vista
	}


	our %VarDataStorage;#变量存储
	#前处理 文字 字框 后处理
	#PreProce Text TextBox PostProce
	#前 字 框 后
	our %NameConv;
	$NameConv{"PreProce"}{"CN"} 	 = "前\n处\n理";
	$NameConv{"Text"}{"CN"}			 = "文\n字";
	$NameConv{"TextBox"}{"CN"}		 = "字\n框";
	$NameConv{"PostProce"}{"CN"}	 = "后\n处\n理";
	#
	$NameConv{"PreProce"}{"ShortCN"} 	 = "前";
	$NameConv{"Text"}{"ShortCN"}			 = "字";
	$NameConv{"TextBox"}{"ShortCN"}		 = "框";
	$NameConv{"PostProce"}{"ShortCN"}	 = "后";
	#
#	our ($ButtonWidth,$ButtonPadX,$ButtonPadY,) = (2,1,1,);
	our ($ButtonWidth,$ButtonPadX,$ButtonPadY,) = (2,1,0,);
	#our ($SubFramePad,$SubFrameIPad,$SubFramePadding,) = (3,3,"1 1 1 1",);
	our ($SubFramePad,$SubFrameIPad,$SubFramePadding,) = (3,3,"3 3 1 3",);

	our (%GuiFrameVarStorage,%GuiFrameStatusStorage,%ButtonVarStorage);
	our (%GuiSubFrameVarStorage,%GuiSubFrameStatusStorage,);

	for my $tNumOne ( 1 .. 4 ) {
		for my $tNumTwo ( 1 .. 4 ) {
			$GuiFrameStatusStorage{$tNumOne}{$tNumTwo} = 'no';
		}
		$GuiSubFrameStatusStorage{$tNumOne} = 'no';
	}

	our $mw = Tkx::widget->new(".");

	#$mw->g_wm_geometry( $MainGuiWidth . "x" . $MainGuiHeight . "+" . int((Tkx::winfo('screenwidth', $mw) / 2) - ( $MainGuiWidth / 2 ) ) . "+" . 	int((Tkx::winfo('screenheight', $mw) / 2) - ( $MainGuiHeight / 2 ) ) );
	#$mw->g_wm_geometry( "+" . int((Tkx::winfo('screenwidth', $mw) / 2) - ( $MainGuiWidth / 2 ) ) . "+" . 	int((Tkx::winfo('screenheight', $mw) / 2) - ( $MainGuiHeight / 2 ) ) );
#	$mw->g_wm_geometry( "+" . int((Tkx::winfo('screenwidth', $mw) / 3 * 2 ) - ( $MainGuiWidth / 2 ) ) . "+" . 	int((Tkx::winfo('screenheight', $mw) / 6 ) - ( $MainGuiHeight / 2 ) ) );
#	$mw->g_wm_geometry( "+" . int( Tkx::winfo('screenwidth', $mw) - 666 ) . "+" . 	int( 127 ) );
#	$mw->g_wm_geometry( "+" . int( Tkx::winfo('screenwidth', $mw) - 730 ) . "+" . 	int( 129 ) );
	$mw->g_wm_geometry( "+" . int( Tkx::winfo('screenwidth', $mw) - 730 ) . "+" . 	'0' );
	$mw->g_wm_title("字符 一条龙");

	&iTkxGetImageFile('SetMwLogo',$mw);
	$mw->g_wm_attributes('-topmost',1);
	#$mw->g_wm_minsize(400,200);
	#$mw->g_wm_minsize(400,10);
	$mw->g_wm_resizable(0,0);

	#raised, sunken, flat, ridge, solid, and groove
#	our $TestRelief = 'groove';
	our $TestRelief = 'flat';
	(our $MainFrame = $mw->new_ttk__frame(-relief => $TestRelief,))->g_pack(-side=>'top',-expand => '1',-fill=>'both',);
	#####################################	  前处理		#############################
	($GuiSubFrameVarStorage{"1"} = $MainFrame->new_ttk__frame(-padding => $SubFramePadding,-relief =>'groove',));#->g_pack(-side=>'top',-expand => '1',-fill=>'both',-padx => $SubFramePad,-pady => $SubFramePad,-ipadx => $SubFrameIPad,-ipady => $SubFrameIPad,);#前处理
	(our $PreProceLeftButtonFrame = $GuiSubFrameVarStorage{"1"}->new_ttk__frame(-relief => $TestRelief,))->g_pack(-side=>'left',-fill=>'y',);#左侧按钮区
	#前处理 按钮
	($GuiFrameVarStorage{"1"}{"1"} = $PreProceLeftButtonFrame->new_ttk__frame(-relief => $TestRelief,));#->g_pack(-side=>'top',-fill=>'y',-expand => '1',);
	our $PreProceLeftButtonText = $NameConv{"PreProce"}{"CN"};
	($ButtonVarStorage{"1"}{"1"} = $GuiFrameVarStorage{"1"}{"1"}->new_ttk__button(-textvariable => \$PreProceLeftButtonText,-width=> $ButtonWidth,-command => sub {&SwitchDisplay('Single',1,1,);},) )->g_pack(-side=>'top',-padx => $ButtonPadX,-pady => $ButtonPadY,-fill=>'y',-expand => '1',);
	$ButtonVarStorage{"1"}{"1"}->g_bind( "<Button-3>", sub {&SwitchDisplay('Multiple',1,1,);}, );
	#字框 按钮
	($GuiFrameVarStorage{"1"}{"2"} = $PreProceLeftButtonFrame->new_ttk__frame(-relief => $TestRelief,));#->g_pack(-side=>'top',-fill=>'y',);
	($ButtonVarStorage{"1"}{"2"} = $GuiFrameVarStorage{"1"}{"2"}->new_ttk__button(-text => $NameConv{"TextBox"}{"ShortCN"},-width=> $ButtonWidth,-command => sub {&SwitchDisplay('Single',1,2,);},) )->g_pack(-side=>'top',-padx => $ButtonPadX,-pady => $ButtonPadY,-fill=>'y',);
	$ButtonVarStorage{"1"}{"2"}->g_bind( "<Button-3>", sub {&SwitchDisplay('Multiple',1,2,);}, );
	#文字 按钮
	($GuiFrameVarStorage{"1"}{"3"} = $PreProceLeftButtonFrame->new_ttk__frame(-relief => $TestRelief,));#->g_pack(-side=>'top',-fill=>'y',);
	($ButtonVarStorage{"1"}{"3"} = $GuiFrameVarStorage{"1"}{"3"}->new_ttk__button(-text => $NameConv{"Text"}{"ShortCN"},-width=> $ButtonWidth,-command => sub {&SwitchDisplay('Single',1,3,);},) )->g_pack(-side=>'top',-padx => $ButtonPadX,-pady => $ButtonPadY,-fill=>'y',);
	$ButtonVarStorage{"1"}{"3"}->g_bind( "<Button-3>", sub {&SwitchDisplay('Multiple',1,3,);}, );
	#后处理 按钮
	($GuiFrameVarStorage{"1"}{"4"} = $PreProceLeftButtonFrame->new_ttk__frame(-relief => $TestRelief,));#->g_pack(-side=>'top',-fill=>'y',);
	($ButtonVarStorage{"1"}{"4"} = $GuiFrameVarStorage{"1"}{"4"}->new_ttk__button(-text => $NameConv{"PostProce"}{"ShortCN"},-width=> $ButtonWidth,-command => sub {&SwitchDisplay('Single',1,4,);},) )->g_pack(-side=>'top',-padx => $ButtonPadX,-pady => $ButtonPadY,-fill=>'y',);
	$ButtonVarStorage{"1"}{"4"}->g_bind( "<Button-3>", sub {&SwitchDisplay('Multiple',1,4,);}, );
	#
	(our $PreProceRightDataFrame = $GuiSubFrameVarStorage{"1"}->new_ttk__frame(-relief => $TestRelief,))->g_pack(-side=>'right',-fill=>'x',-expand => '1',);#右侧数据区
	##################################### 	字 框		################################
	($GuiSubFrameVarStorage{"2"} = $MainFrame->new_ttk__frame(-padding => $SubFramePadding,-relief =>'groove',));#->g_pack(-side=>'top',-expand => '1',-fill=>'both',-padx => $SubFramePad,-pady => $SubFramePad,-ipadx => $SubFrameIPad,-ipady => $SubFrameIPad,);#字框
	(our $TextBoxLeftButtonFrame = $GuiSubFrameVarStorage{"2"}->new_ttk__frame(-relief => $TestRelief,))->g_pack(-side=>'left',-fill=>'y',);#左侧按钮区
	#前处理 按钮
	($GuiFrameVarStorage{"2"}{"1"} = $TextBoxLeftButtonFrame->new_ttk__frame(-relief => $TestRelief,));#->g_pack(-side=>'top',-fill=>'y',);
	($ButtonVarStorage{"2"}{"1"} = $GuiFrameVarStorage{"2"}{"1"}->new_ttk__button(-text => $NameConv{"PreProce"}{"ShortCN"},-width=> $ButtonWidth,-command => sub {&SwitchDisplay('Single',2,1,);},) )->g_pack(-side=>'top',-padx => $ButtonPadX,-pady => $ButtonPadY,-fill=>'y',);
	$ButtonVarStorage{"2"}{"1"}->g_bind( "<Button-3>", sub {&SwitchDisplay('Multiple',2,1,);}, );
	#字框 按钮
	($GuiFrameVarStorage{"2"}{"2"} = $TextBoxLeftButtonFrame->new_ttk__frame(-relief => $TestRelief,));#->g_pack(-side=>'top',-fill=>'y',-expand => '1',);
	our $TextBoxLeftButtonText = $NameConv{"TextBox"}{"CN"};
	($ButtonVarStorage{"2"}{"2"} = $GuiFrameVarStorage{"2"}{"2"}->new_ttk__button(-textvariable => \$TextBoxLeftButtonText,-width=> $ButtonWidth,-command => sub {&SwitchDisplay('Single',2,2,);},) )->g_pack(-side=>'top',-padx => $ButtonPadX,-pady => $ButtonPadY,-fill=>'y',-expand => '1',);
	$ButtonVarStorage{"2"}{"2"}->g_bind( "<Button-3>", sub {&SwitchDisplay('Multiple',2,2,);}, );
	#文字 按钮
	($GuiFrameVarStorage{"2"}{"3"} = $TextBoxLeftButtonFrame->new_ttk__frame(-relief => $TestRelief,));#->g_pack(-side=>'top',-fill=>'y',);
	($ButtonVarStorage{"2"}{"3"} = $GuiFrameVarStorage{"2"}{"3"}->new_ttk__button(-text => $NameConv{"Text"}{"ShortCN"},-width=> $ButtonWidth,-command => sub {&SwitchDisplay('Single',2,3,);},) )->g_pack(-side=>'top',-padx => $ButtonPadX,-pady => $ButtonPadY,-fill=>'y',);
	$ButtonVarStorage{"2"}{"3"}->g_bind( "<Button-3>", sub {&SwitchDisplay('Multiple',2,3,);}, );
	#后处理 按钮
	($GuiFrameVarStorage{"2"}{"4"} = $TextBoxLeftButtonFrame->new_ttk__frame(-relief => $TestRelief,));#->g_pack(-side=>'top',-fill=>'y',);
	($ButtonVarStorage{"2"}{"4"} = $GuiFrameVarStorage{"2"}{"4"}->new_ttk__button(-text => $NameConv{"PostProce"}{"ShortCN"},-width=> $ButtonWidth,-command => sub {&SwitchDisplay('Single',2,4,);},) )->g_pack(-side=>'top',-padx => $ButtonPadX,-pady => $ButtonPadY,-fill=>'y',);
	$ButtonVarStorage{"2"}{"4"}->g_bind( "<Button-3>", sub {&SwitchDisplay('Multiple',2,4,);}, );
	#
	(our $TextBoxRightDataFrame = $GuiSubFrameVarStorage{"2"}->new_ttk__frame(-relief => $TestRelief,))->g_pack(-side=>'right',-fill=>'x',-expand => '1',);#右侧数据区

	#####################################	 文 字	################################
	($GuiSubFrameVarStorage{"3"} = $MainFrame->new_ttk__frame(-padding => $SubFramePadding,-relief =>'groove',));#->g_pack(-side=>'top',-expand => '1',-fill=>'both',-padx => $SubFramePad,-pady => $SubFramePad,-ipadx => $SubFrameIPad,-ipady => $SubFrameIPad,);#文字
	(our $TextLeftButtonFrame = $GuiSubFrameVarStorage{"3"}->new_ttk__frame(-relief => $TestRelief,))->g_pack(-side=>'left',-fill=>'y',);#左侧按钮区
	#前处理 按钮
	($GuiFrameVarStorage{"3"}{"1"} = $TextLeftButtonFrame->new_ttk__frame(-relief => $TestRelief,));#->g_pack(-side=>'top',-fill=>'y',);
	($ButtonVarStorage{"3"}{"1"} = $GuiFrameVarStorage{"3"}{"1"}->new_ttk__button(-text => $NameConv{"PreProce"}{"ShortCN"},-width=> $ButtonWidth,-command => sub {&SwitchDisplay('Single',3,1,);},) )->g_pack(-side=>'top',-padx => $ButtonPadX,-pady => $ButtonPadY,-fill=>'y',);
	$ButtonVarStorage{"3"}{"1"}->g_bind( "<Button-3>", sub {&SwitchDisplay('Multiple',3,1,);}, );
	#字框 按钮
	($GuiFrameVarStorage{"3"}{"2"} = $TextLeftButtonFrame->new_ttk__frame(-relief => $TestRelief,));#->g_pack(-side=>'top',-fill=>'y',);
	($ButtonVarStorage{"3"}{"2"} = $GuiFrameVarStorage{"3"}{"2"}->new_ttk__button(-text => $NameConv{"TextBox"}{"ShortCN"},-width=> $ButtonWidth,-command => sub {&SwitchDisplay('Single',3,2,);},) )->g_pack(-side=>'top',-padx => $ButtonPadX,-pady => $ButtonPadY,-fill=>'y',);
	$ButtonVarStorage{"3"}{"2"}->g_bind( "<Button-3>", sub {&SwitchDisplay('Multiple',3,2,);}, );
	#文字 按钮
	($GuiFrameVarStorage{"3"}{"3"} = $TextLeftButtonFrame->new_ttk__frame(-relief => $TestRelief,));#->g_pack(-side=>'top',-fill=>'y',-expand => '1',);
	our $TextLeftButtonText = $NameConv{"Text"}{"CN"};
	($ButtonVarStorage{"3"}{"3"} = $GuiFrameVarStorage{"3"}{"3"}->new_ttk__button(-textvariable => \$TextLeftButtonText,-width=> $ButtonWidth,-command => sub {&SwitchDisplay('Single',3,3,);},) )->g_pack(-side=>'top',-padx => $ButtonPadX,-pady => $ButtonPadY,-fill=>'y',-expand => '1',);
	$ButtonVarStorage{"3"}{"3"}->g_bind( "<Button-3>", sub {&SwitchDisplay('Multiple',3,3,);}, );
	#后处理 按钮
	($GuiFrameVarStorage{"3"}{"4"} = $TextLeftButtonFrame->new_ttk__frame(-relief => $TestRelief,));#->g_pack(-side=>'top',-fill=>'y',);
	($ButtonVarStorage{"3"}{"4"} = $GuiFrameVarStorage{"3"}{"4"}->new_ttk__button(-text => $NameConv{"PostProce"}{"ShortCN"},-width=> $ButtonWidth,-command => sub {&SwitchDisplay('Single',3,4,);},) )->g_pack(-side=>'top',-padx => $ButtonPadX,-pady => $ButtonPadY,-fill=>'y',);
	$ButtonVarStorage{"3"}{"4"}->g_bind( "<Button-3>", sub {&SwitchDisplay('Multiple',3,4,);}, );
	#
	(our $TextRightDataFrame = $GuiSubFrameVarStorage{"3"}->new_ttk__frame(-relief => $TestRelief,))->g_pack(-side=>'right',-fill=>'x',-expand => '1',);#右侧数据区
	#####################################	后处理	################################
	($GuiSubFrameVarStorage{"4"} = $MainFrame->new_ttk__frame(-padding => $SubFramePadding,-relief =>'groove',));#->g_pack(-side=>'top',-expand => '1',-fill=>'both',-padx => $SubFramePad,-pady => $SubFramePad,-ipadx => $SubFrameIPad,-ipady => $SubFrameIPad,);#后处理
	(our $PostProceLeftButtonFrame = $GuiSubFrameVarStorage{"4"}->new_ttk__frame(-relief => $TestRelief,))->g_pack(-side=>'left',-fill=>'y',);#左侧按钮区
	#前处理 按钮
	($GuiFrameVarStorage{"4"}{"1"} = $PostProceLeftButtonFrame->new_ttk__frame(-relief => $TestRelief,));#->g_pack(-side=>'top',-fill=>'y',);
	($ButtonVarStorage{"4"}{"1"} = $GuiFrameVarStorage{"4"}{"1"}->new_ttk__button(-text => $NameConv{"PreProce"}{"ShortCN"},-width=> $ButtonWidth,-command => sub {&SwitchDisplay('Single',4,1,);},) )->g_pack(-side=>'top',-padx => $ButtonPadX,-pady => $ButtonPadY,-fill=>'y',);
	$ButtonVarStorage{"4"}{"1"}->g_bind( "<Button-3>", sub {&SwitchDisplay('Multiple',4,1,);}, );
	#字框 按钮
	($GuiFrameVarStorage{"4"}{"2"} = $PostProceLeftButtonFrame->new_ttk__frame(-relief => $TestRelief,));#->g_pack(-side=>'top',-fill=>'y',);
	($ButtonVarStorage{"4"}{"2"} = $GuiFrameVarStorage{"4"}{"2"}->new_ttk__button(-text => $NameConv{"TextBox"}{"ShortCN"},-width=> $ButtonWidth,-command => sub {&SwitchDisplay('Single',4,2,);},) )->g_pack(-side=>'top',-padx => $ButtonPadX,-pady => $ButtonPadY,-fill=>'y',);
	$ButtonVarStorage{"4"}{"2"}->g_bind( "<Button-3>", sub {&SwitchDisplay('Multiple',4,2,);}, );
	#文字 按钮
	($GuiFrameVarStorage{"4"}{"3"} = $PostProceLeftButtonFrame->new_ttk__frame(-relief => $TestRelief,));#->g_pack(-side=>'top',-fill=>'y',);
	($ButtonVarStorage{"4"}{"3"} = $GuiFrameVarStorage{"4"}{"3"}->new_ttk__button(-text => $NameConv{"Text"}{"ShortCN"},-width=> $ButtonWidth,-command => sub {&SwitchDisplay('Single',4,3,);},) )->g_pack(-side=>'top',-padx => $ButtonPadX,-pady => $ButtonPadY,-fill=>'y',);
	$ButtonVarStorage{"4"}{"3"}->g_bind( "<Button-3>", sub {&SwitchDisplay('Multiple',4,3,);}, );
	#后处理 按钮
	($GuiFrameVarStorage{"4"}{"4"} = $PostProceLeftButtonFrame->new_ttk__frame(-relief => $TestRelief,));#->g_pack(-side=>'top',-fill=>'y',-expand => '1',);
	our $PostProceLeftButtonText = $NameConv{"PostProce"}{"CN"};
	($ButtonVarStorage{"4"}{"4"} = $GuiFrameVarStorage{"4"}{"4"}->new_ttk__button(-textvariable => \$PostProceLeftButtonText,-width=> $ButtonWidth,-command => sub {&SwitchDisplay('Single',4,4,);},) )->g_pack(-side=>'top',-padx => $ButtonPadX,-pady => $ButtonPadY,-fill=>'y',-expand => '1',);
	$ButtonVarStorage{"4"}{"4"}->g_bind( "<Button-3>", sub {&SwitchDisplay('Multiple',4,4,);}, );
	#
	(our $PostProceRightDataFrame = $GuiSubFrameVarStorage{"4"}->new_ttk__frame(-relief => $TestRelief,))->g_pack(-side=>'right',-fill=>'x',-expand => '1',);#右侧数据区
	################################################################################
	#
	#############################	前处理	###################################### $PreProceRightDataFrame
	( my $PreProceSubCoverLayerFrame = $PreProceRightDataFrame->new_ttk__frame( -padding => $SubFramePadding,-relief =>'groove',) )->g_pack(-fill=>'y',-side=>'left', );
	( my $PreProceSubListFrame = $PreProceSubCoverLayerFrame->new_ttk__frame( -padding => $SubFramePadding, ) )->g_pack(-fill=>'y',-side=>'left', );
	( $PreProceSubListFrame->new_ttk__label( -text => "字\n符\n层\n :", ) )->g_pack( -side=>'left' );
	( our $LayerList = $PreProceSubListFrame->new_tk__listbox( -height => 4,-width => 4,-selectmode => "extended",-selectforeground =>'white',-exportselection => 0, ) )->g_pack( -side=>'left',-expand => '1',-fill=>'both', );
	( $tScrollbar = $PreProceSubListFrame->new_ttk__scrollbar( -command => [$LayerList, "yview"], -orient => "vertical", ) )->g_pack( -side=>'left',-fill=>'y' );
	$LayerList->configure( -yscrollcommand => [$tScrollbar, "set"] );
	$LayerList->delete( '0', 'end' );
	$LayerList->insert( 'end',@SilkScreenList );
	$LayerList->select( 'set',0 ,'end' );


	our $ButtonPadX = 1;
	our $ButtonPadY = 1;
	our $TwoButtonwidth = 3;
	our $TwoButtonwidth2 = 4;
	our $TwoButtonwidthAuto = 10;
#	our $ConvButtonText = '<=>';
#	our $ConvButtonWidth = 3;
	our $ConvButtonText = '↔';
	our $ConvButtonWidth = 2;
	our $TextEntryWidth = 4;
#	our $SubFramePadding = '3 3 3 3';
#	our $SubFramePadding = '0 0 0 0';
	our $SubFramePadding = '1 1 1 1';

	#变量赋值
	for my $tNum (qw/One Two Three/){
		for my $tTextTwo (qw/TextSubHW TextSubXY/){
			$VarDataStorage{'Mirror'}{$tTextTwo . $tNum} = 0 ;
		}
		$VarDataStorage{'Width'}{'TextSubHW' . $tNum} = 20 ;
		$VarDataStorage{'Height'}{'TextSubHW' . $tNum} = 32 ;

		for my $tTextTwo (qw/ScaleX ScaleY/){
			for my $tTextThree (qw/TextSubXY TextBoxSubManual/){
				$VarDataStorage{$tTextTwo}{$tTextThree . $tNum} = 1.1 ;
			}
		}
	}

#	for (1 .. 3){
	for (qw /BoxRectangle BoxOpenRectangle BoxRings/ ){
		$VarDataStorage{"TextBoxSubAutoType"}{$_} = 1 ;#自动类型赋值
	}

	our $SilkScreenToSolderMask = "5.5";
	our $SilkScreenToSmdBga = "7";
	our $CoverLayerSuffix = '-cover+';

	( my $PreProceCoverLayerConfigFrame = $PreProceSubCoverLayerFrame->new_ttk__frame( -padding => $SubFramePadding, ) )->g_pack(-fill=>'y',-side=>'left', );
	( my $PreProceCoverLayerTextFrame1 = $PreProceCoverLayerConfigFrame->new_ttk__frame( -padding => $SubFramePadding, ) )->g_pack(-fill=>'y',-side=>'top', );
	( my $PreProceCoverLayerTextFrame2 = $PreProceCoverLayerConfigFrame->new_ttk__frame( -padding => $SubFramePadding, ) )->g_pack(-fill=>'y',-side=>'top', );
	( my $PreProceCoverLayerTextFrame3 = $PreProceCoverLayerConfigFrame->new_ttk__frame( -padding => $SubFramePadding, ) )->g_pack(-fill=>'y',-side=>'top', );

	($PreProceCoverLayerTextFrame1->new_ttk__label(-text => "字符距阻焊:",) )->g_pack(-side=>'left');
	($PreProceCoverLayerTextFrame1->new_ttk__entry(-textvariable => \$SilkScreenToSolderMask ,-width => 7,) )->g_pack(-side=>'left',-expand => '1',-fill=>'x',);

	($PreProceCoverLayerTextFrame2->new_ttk__label(-text => "字符距Smd、Bga:",) )->g_pack(-side=>'left');
	($PreProceCoverLayerTextFrame2->new_ttk__entry(-textvariable => \$SilkScreenToSmdBga ,-width => 3,) )->g_pack(-side=>'left',-expand => '1',-fill=>'x',);
	#
	($PreProceCoverLayerTextFrame3->new_ttk__label(-text => "套层后缀:",) )->g_pack(-side=>'left');
	($PreProceCoverLayerTextFrame3->new_ttk__entry(-textvariable => \$CoverLayerSuffix ,-width => 9,) )->g_pack(-side=>'left',-expand => '1',-fill=>'x',);


	( my $PreProceCoverLayerButtonFrame = $PreProceCoverLayerConfigFrame->new_ttk__frame( -padding => $SubFramePadding, ) )->g_pack(-fill=>'y',-side=>'top', );

	($PreProceCoverLayerButtonFrame->new_ttk__button(-text => "创建套层",-width=> 8,-command => sub {&CreateCoverLayerButtonAct;},) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);

	( my $PreProceSubSubChangeSilkMinLineWidthButtonFrame = $PreProceRightDataFrame->new_ttk__frame( -padding => $SubFramePadding,-relief =>'groove',) )->g_pack(-side=>'top',-padx => 1,-pady => 1,-ipadx => 1,-ipady => 1,);
	( my $PreProceSubChangeSilkMinLineWidthFrame = $PreProceSubSubChangeSilkMinLineWidthButtonFrame->new_ttk__frame( -padding => $SubFramePadding, ) )->g_pack(-side=>'top', );
	($PreProceSubChangeSilkMinLineWidthFrame->new_ttk__label(-text => "字符最小线宽:",) )->g_pack(-side=>'left', -pady => 1,);
#	( my $PreProceSubChangeSilkMinLineWidthTwoFrame = $PreProceSubSubChangeSilkMinLineWidthButtonFrame->new_ttk__frame( -padding => $SubFramePadding, ) )->g_pack(-fill=>'x',-side=>'top', );
	our @SilkMinLineWidthData = qw/4 4.5 5/;
#	our $SilkMinLineWidth = $SilkMinLineWidthData[2];
	our $SilkMinLineWidth = $SilkMinLineWidthData[1];
	($PreProceSubChangeSilkMinLineWidthFrame->new_ttk__combobox(-textvariable => \$SilkMinLineWidth,-values => "@SilkMinLineWidthData",-width => 3,) )->g_pack(-side=>'left',-fill=>'x',);
	($PreProceSubSubChangeSilkMinLineWidthButtonFrame->new_ttk__button(-text => "修改",-width=> 8,-command => sub { &ChangeSilkMinLineWidthButtonAct; },) )->g_pack(-side=>'top',-padx => 1,-pady => $ButtonPadY,);


	( my $PreProceSubButtonFrame = $PreProceRightDataFrame->new_ttk__frame( -padding => $SubFramePadding,-relief =>'groove',) )->g_pack(-side=>'top',-padx => 1,-pady => 1,-ipadx => 1,-ipady => 1,);
	
	( my $PreProceSubTextSeparatedConfigFrame = $PreProceSubButtonFrame->new_ttk__frame( -padding => $SubFramePadding, ) )->g_pack(-side=>'top', );
	($PreProceSubTextSeparatedConfigFrame->new_ttk__label(-text => "文字最大高度:",) )->g_pack(-side=>'left', -pady => 3,);
	our $TextSeparatedTextMaxHeight = 60;
	($PreProceSubTextSeparatedConfigFrame->new_ttk__entry(-textvariable => \$TextSeparatedTextMaxHeight ,-width => 5,) )->g_pack(-side=>'left',-fill=>'x',);

	($PreProceSubButtonFrame->new_ttk__button(-text => "字框分离",-width=> 8,-command => sub { &TextAndTextBoxSeparatedButtonAct; },) )->g_pack(-side=>'top',-padx => 5,-pady => $ButtonPadY,);

	#
	#############################		字框	###################################### $TextBoxRightDataFrame
	(my $TextBoxSubNoteBookPageFrame = $TextBoxRightDataFrame->new_ttk__frame())->g_pack(-expand => '1',-fill=>'both',-side=>'top',);

	(our $TextBoxSubNotebookPage = $TextBoxSubNoteBookPageFrame->new_ttk__notebook)->g_pack(-expand => '1',-fill=>'both',);
	(my $TextBoxSubNotebookPageManual = $TextBoxSubNotebookPage->new_ttk__frame(-padding => "3 3 0 3",) )->g_pack(-expand => '1',-fill=>'both',);
	(my $TextBoxSubNotebookPageAuto  = $TextBoxSubNotebookPage->new_ttk__frame(-padding => "3 3 0 3",) )->g_pack(-expand => '1',-fill=>'both',);

	$TextBoxSubNotebookPage->add($TextBoxSubNotebookPageAuto, -text => "自动");
	$TextBoxSubNotebookPage->add($TextBoxSubNotebookPageManual, -text => "手动");
	######################################
	( my $TextBoxSubAutoButtonOneFrame = $TextBoxSubNotebookPageAuto->new_ttk__frame( -padding => $SubFramePadding,
	) )->g_pack(-fill=>'x',-side=>'top', );

	( my $TextBoxSubAutoCheckButtonFrame = $TextBoxSubAutoButtonOneFrame->new_ttk__frame( -padding => $SubFramePadding,
	-relief =>'groove',
	) )->g_pack(-fill=>'x',-side=>'left', );
	( my $TextBoxSubAutoCheckButtonOneFrame = $TextBoxSubAutoCheckButtonFrame->new_ttk__frame( -padding => $SubFramePadding,	) )->g_pack(-fill=>'x',-side=>'top', );


	($TextBoxSubAutoCheckButtonOneFrame->new_ttk__label(-text => "自动: 类型:",) )->g_pack(-side=>'left');
#	our $ImagePath = '/mnt/hgfs/LinuxShare/Pl/Image';
#	Tkx::package_require("Img");
	Tkx::image_create_photo("BoxRectangle", -file => "$ImagePath/BoxRectangle.gif");
	Tkx::image_create_photo("BoxOpenRectangle", -file => "$ImagePath/BoxOpenRectangle.gif");
	Tkx::image_create_photo("BoxRings", -file => "$ImagePath/BoxRings.gif");


#	Tkx::image_create_photo("BoxRectangle", -file => "$ImagePath/BoxRectangle.xpm");
#	Tkx::image_create_photo("BoxOpenRectangle", -file => "$ImagePath/BoxOpenRectangle.xpm");
#	Tkx::image_create_photo("BoxRings", -file => "$ImagePath/BoxRings.xpm");
#	$l->configure(-image => "imgobj");


#Tkx::ttk__style_configure("Emergency.TCheckbutton", -font => "helvetica 24",-foreground => "red", -padding => 10);
#	$VarDataStorage{"TextBoxSubAutoType"}{"BoxRings"} = 1 ;
#	$VarDataStorage{"TextBoxSubAutoType"}{"BoxRectangle"} = 1 ;
#	$VarDataStorage{"TextBoxSubAutoType"}{"BoxRings"} = 1;
#	($TextBoxSubAutoCheckButtonOneFrame->new_ttk__checkbutton(-image =>"BoxRings",-text => "圆环", -variable => \$VarDataStorage{TextBoxSubAutoType}{BoxRings},-offvalue => 0, -onvalue => 1))->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	($TextBoxSubAutoCheckButtonOneFrame->new_ttk__checkbutton(-image =>"BoxRings",-text => "圆环", -variable => \$VarDataStorage{TextBoxSubAutoType}{BoxRings},-offvalue => 0, -onvalue => 1))->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	($TextBoxSubAutoCheckButtonOneFrame->new_ttk__checkbutton(-image =>"BoxRectangle",-text => "矩形", -variable => \$VarDataStorage{TextBoxSubAutoType}{BoxRectangle},-offvalue => 1, -onvalue => 1))->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	(our $BoxOpenRectangleBotton = $TextBoxSubAutoCheckButtonOneFrame->new_ttk__checkbutton(-image =>"BoxOpenRectangle",-text => "开口矩形", -variable => \$VarDataStorage{TextBoxSubAutoType}{BoxOpenRectangle},-offvalue => 0, -onvalue => 1,
	-command => sub{
		if ( $VarDataStorage{TextBoxSubAutoType}{BoxOpenRectangle} == 0 ){
			$SpokesGapEntry->g_pack_forget;
		} else {
			$SpokesGapEntry->g_pack(-side=>'left',);
		}
	},
	))->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
#	$BoxOpenRectangleBotton->invoke();


	($TextBoxSubAutoCheckButtonOneFrame->new_ttk__button(-text => "运行",-width=> 4,-command => sub {
	&RunScriptAct($MyScriptFile,'Run:AllAutoWordBoxZoom',$CoverLayerSuffix,$TextBoxLengthMin,$TextBoxLengthMax,$TextBoxWidthMax,$VarDataStorage{TextBoxSubAutoType}{BoxRings},$VarDataStorage{TextBoxSubAutoType}{BoxRectangle},$VarDataStorage{TextBoxSubAutoType}{BoxOpenRectangle},$SpokesGap,);
	},) )->g_pack(-side=>'right',-padx => $ButtonPadX,-pady => $ButtonPadY,);

	###
	( my $TextBoxSubAutoCheckButtonTwoFrame = $TextBoxSubAutoCheckButtonFrame->new_ttk__frame( -padding => $SubFramePadding,	) )->g_pack(-fill=>'x',-side=>'top', );

#	our $TextBoxLengthMin = 30;
	our $TextBoxLengthMin = 20;
	#our $TextBoxLengthMax = 200;
	our $TextBoxLengthMax = 160;
	our $TextBoxWidthMax = 8;
	our $SpokesGap = 25;
	($TextBoxSubAutoCheckButtonTwoFrame->new_ttk__label(-text => "最小长度:",) )->g_pack(-side=>'left');
	($TextBoxSubAutoCheckButtonTwoFrame->new_ttk__entry(-textvariable => \$TextBoxLengthMin ,-width => 2,) )->g_pack(-side=>'left', -padx => 0,);
	($TextBoxSubAutoCheckButtonTwoFrame->new_ttk__label(-text => "最大长度:",) )->g_pack(-side=>'left');
	($TextBoxSubAutoCheckButtonTwoFrame->new_ttk__entry(-textvariable => \$TextBoxLengthMax ,-width => 3,) )->g_pack(-side=>'left', -padx => 0,);
	($TextBoxSubAutoCheckButtonTwoFrame->new_ttk__label(-text => "最大线宽:",) )->g_pack(-side=>'left');
	($TextBoxSubAutoCheckButtonTwoFrame->new_ttk__entry(-textvariable => \$TextBoxWidthMax ,-width => 2,) )->g_pack(-side=>'left', -padx => 0,);
	(our $SpokesGapEntry = $TextBoxSubAutoCheckButtonTwoFrame->new_ttk__frame( -padding => $SubFramePadding,	) )->g_pack(-fill=>'x',-side=>'left', );
	($SpokesGapEntry->new_ttk__label(-text => "最大开口:",) )->g_pack(-side=>'left');
	($SpokesGapEntry->new_ttk__entry(-textvariable => \$SpokesGap ,-width => 2,) )->g_pack(-side=>'left',);


	( my $TextBoxSubManualButtonOneTopFrame = $TextBoxSubNotebookPageAuto->new_ttk__frame( -padding => $SubFramePadding,
	) )->g_pack(-fill=>'x',-side=>'top', );
	( my $TextBoxSubManualButtonOneFrame = $TextBoxSubManualButtonOneTopFrame->new_ttk__frame( -padding => $SubFramePadding,
	-relief =>'groove',
	) )->g_pack(-fill=>'x',-side=>'left', );

	#
	($TextBoxSubManualButtonOneFrame->new_ttk__label(-text => "半自动:",) )->g_pack(-side=>'left');
#	our $TextBoxButtonwidth = 7;
	our $TextBoxButtonwidth = 4;
#	($TextBoxSubManualButtonOneFrame->new_ttk__button(-text => "单个",-width=> $TextBoxButtonwidth,-command => sub { &RunScriptAct($MyScriptFile,'Run:SemiAutoWordBoxZoom','Single',$CoverLayerSuffix); },) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
#	($TextBoxSubManualButtonOneFrame->new_ttk__button(-text => "多个",-width=> $TextBoxButtonwidth,-command => sub { &RunScriptAct($MyScriptFile,'Run:SemiAutoWordBoxZoom','Multiple',$CoverLayerSuffix); },) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	($TextBoxSubManualButtonOneFrame->new_ttk__button(-text => "单个",-width=> $TextBoxButtonwidth,-command => sub { &RunScriptAct($MyScriptFile,'Run:SemiAutoWordBoxZoom','Single','Scale',$CoverLayerSuffix); },) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	($TextBoxSubManualButtonOneFrame->new_ttk__button(-text => "多个",-width=> $TextBoxButtonwidth,-command => sub { &RunScriptAct($MyScriptFile,'Run:SemiAutoWordBoxZoom','Multiple','Scale',$CoverLayerSuffix); },) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	our $TextBoxButtonwidth2 = 2;
	($TextBoxSubManualButtonOneFrame->new_ttk__frame( -padding => $SubFramePadding,-relief =>'groove',) )->g_pack(-fill=>'y',-side=>'left', -padx => $ButtonPadX,);

	($TextBoxSubManualButtonOneFrame->new_ttk__button(-text => "X",-width=> $TextBoxButtonwidth2,-command => sub { &RunScriptAct($MyScriptFile,'Run:SemiAutoWordBoxZoom','Single','ScaleX',$CoverLayerSuffix); },) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	($TextBoxSubManualButtonOneFrame->new_ttk__button(-text => "Y",-width=> $TextBoxButtonwidth2,-command => sub { &RunScriptAct($MyScriptFile,'Run:SemiAutoWordBoxZoom','Single','ScaleY',$CoverLayerSuffix); },) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);

	($TextBoxSubManualButtonOneFrame->new_ttk__frame( -padding => $SubFramePadding,-relief =>'groove',) )->g_pack(-fill=>'y',-side=>'left', -padx => $ButtonPadX,);

	($TextBoxSubManualButtonOneFrame->new_ttk__button(-text => "外扩",-width=> $TextBoxButtonwidth,-command => sub { &RunScriptAct($MyScriptFile,'Run:SemiAutoWordBoxZoom','Single','Expansion',$CoverLayerSuffix); },) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);

	( my $TextBoxSubReplaceSimilarTopFrame = $TextBoxSubNotebookPageAuto->new_ttk__frame( -padding => $SubFramePadding,
	) )->g_pack(-fill=>'x',-side=>'top', );
	( my $TextBoxSubReplaceSimilarFrame = $TextBoxSubReplaceSimilarTopFrame->new_ttk__frame( -padding => $SubFramePadding,
	-relief =>'groove',
	) )->g_pack(-fill=>'x',-side=>'left', );

	our $ReplaceSimilarTol = 1.0;
	($TextBoxSubReplaceSimilarFrame->new_ttk__label(-text => "精度:",) )->g_pack(-side=>'left');
	($TextBoxSubReplaceSimilarFrame->new_ttk__entry(-textvariable => \$ReplaceSimilarTol ,-width => 4,) )->g_pack(-side=>'left',
	-padx => 2,
#	-expand => '1',-fill=>'x',
	);
	($TextBoxSubReplaceSimilarFrame->new_ttk__button(-text => "同类替换",-width=> 8,-command => sub { &RunScriptAct($MyScriptFile,'Run:ReplaceSimilar',$ReplaceSimilarTol,); },) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);


	###############

	###################
	###############
	( my $TextBoxSubManualButtonOneFrame = $TextBoxSubNotebookPageManual->new_ttk__frame( -padding => $SubFramePadding, -relief =>'groove',) )->g_pack(-fill=>'x',-side=>'top', );
#	our $PageManualTextMirrorOne = 0;

	($TextBoxSubManualButtonOneFrame->new_ttk__label(-text => "X:",) )->g_pack(-side=>'left');
	($TextBoxSubManualButtonOneFrame->new_ttk__entry(-textvariable => \$VarDataStorage{ScaleX}{TextBoxSubManualOne} ,-width => $TextEntryWidth,) )->g_pack(-side=>'left',-expand => '1',-fill=>'x',);
#	($TextBoxSubManualButtonOneFrame->new_ttk__label(-text => "mil",) )->g_pack(-side=>'left');
	#
	($TextBoxSubManualButtonOneFrame->new_ttk__button(-text => "$ConvButtonText",-width=> $ConvButtonWidth,-command => sub { &SwapDataAct(\$VarDataStorage{ScaleX}{TextBoxSubManualOne},\$VarDataStorage{ScaleY}{TextBoxSubManualOne}); },) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	#
	($TextBoxSubManualButtonOneFrame->new_ttk__label(-text => "Y:",) )->g_pack(-side=>'left');
	($TextBoxSubManualButtonOneFrame->new_ttk__entry(-textvariable => \$VarDataStorage{ScaleY}{TextBoxSubManualOne} ,-width => $TextEntryWidth,) )->g_pack(-side=>'left',-expand => '1',-fill=>'x',);
#	($TextBoxSubManualButtonOneFrame->new_ttk__label(-text => "mil",) )->g_pack(-side=>'left');
	#
	($TextBoxSubManualButtonOneFrame->new_ttk__button(-text => "单个",-width=> $TwoButtonwidth,-command => sub {
		&RunScriptAct($MyScriptFile,'Run:ManualWordBoxZoom','Single',$CoverLayerSuffix,$VarDataStorage{ScaleX}{TextBoxSubManualOne},$VarDataStorage{ScaleY}{TextBoxSubManualOne});
	},) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	($TextBoxSubManualButtonOneFrame->new_ttk__button(-text => "多个",-width=> $TwoButtonwidth,-command => sub {
		&RunScriptAct($MyScriptFile,'Run:ManualWordBoxZoom','Multiple',$CoverLayerSuffix,$VarDataStorage{ScaleX}{TextBoxSubManualOne},$VarDataStorage{ScaleY}{TextBoxSubManualOne});
	},) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	###############
	( my $TextBoxSubManualButtonTwoFrame = $TextBoxSubNotebookPageManual->new_ttk__frame( -padding => $SubFramePadding,-relief =>'groove', ) )->g_pack(-fill=>'x',-side=>'top', );
#	our $PageManualTextMirrorTwo = 0;

	($TextBoxSubManualButtonTwoFrame->new_ttk__label(-text => "X:",) )->g_pack(-side=>'left');
	($TextBoxSubManualButtonTwoFrame->new_ttk__entry(-textvariable => \$VarDataStorage{ScaleX}{TextBoxSubManualTwo} ,-width => $TextEntryWidth,) )->g_pack(-side=>'left',-expand => '1',-fill=>'x',);
#	($TextBoxSubManualButtonTwoFrame->new_ttk__label(-text => "mil",) )->g_pack(-side=>'left');
	#
	($TextBoxSubManualButtonTwoFrame->new_ttk__button(-text => "$ConvButtonText",-width=> $ConvButtonWidth,-command => sub { &SwapDataAct(\$VarDataStorage{ScaleX}{TextBoxSubManualTwo},\$VarDataStorage{ScaleY}{TextBoxSubManualTwo}); },) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	#
	($TextBoxSubManualButtonTwoFrame->new_ttk__label(-text => "Y:",) )->g_pack(-side=>'left');
	($TextBoxSubManualButtonTwoFrame->new_ttk__entry(-textvariable => \$VarDataStorage{ScaleY}{TextBoxSubManualTwo} ,-width => $TextEntryWidth,) )->g_pack(-side=>'left',-expand => '1',-fill=>'x',);
#	($TextBoxSubManualButtonTwoFrame->new_ttk__label(-text => "mil",) )->g_pack(-side=>'left');
	#
	($TextBoxSubManualButtonTwoFrame->new_ttk__button(-text => "单个",-width=> $TwoButtonwidth,-command => sub {
		&RunScriptAct($MyScriptFile,'Run:ManualWordBoxZoom','Single',$CoverLayerSuffix,$VarDataStorage{ScaleX}{TextBoxSubManualTwo},$VarDataStorage{ScaleY}{TextBoxSubManualTwo});
	},) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	($TextBoxSubManualButtonTwoFrame->new_ttk__button(-text => "多个",-width=> $TwoButtonwidth,-command => sub {
		&RunScriptAct($MyScriptFile,'Run:ManualWordBoxZoom','Multiple',$CoverLayerSuffix,$VarDataStorage{ScaleX}{TextBoxSubManualTwo},$VarDataStorage{ScaleY}{TextBoxSubManualTwo});
	},) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	###################
#	( my $TextBoxSubManualButtonThreeFrame = $TextBoxSubNotebookPageManual->new_ttk__frame( -padding => $SubFramePadding, ) )->g_pack(-fill=>'x',-side=>'top', );
##	our $PageManualTextMirrorThree = 0;
#
#	($TextBoxSubManualButtonThreeFrame->new_ttk__label(-text => "X:",) )->g_pack(-side=>'left');
#	($TextBoxSubManualButtonThreeFrame->new_ttk__entry(-textvariable => \$VarDataStorage{ScaleX}{TextBoxSubManualThree} ,-width => $TextEntryWidth,) )->g_pack(-side=>'left',-expand => '1',-fill=>'x',);
##	($TextBoxSubManualButtonThreeFrame->new_ttk__label(-text => "mil",) )->g_pack(-side=>'left');
#	#
#	($TextBoxSubManualButtonThreeFrame->new_ttk__button(-text => "$ConvButtonText",-width=> $ConvButtonWidth,-command => sub { &SwapDataAct(\$VarDataStorage{ScaleX}{TextBoxSubManualThree},\$VarDataStorage{ScaleY}{TextBoxSubManualThree}); },) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
#	#
#	($TextBoxSubManualButtonThreeFrame->new_ttk__label(-text => "Y:",) )->g_pack(-side=>'left');
#	($TextBoxSubManualButtonThreeFrame->new_ttk__entry(-textvariable => \$VarDataStorage{ScaleY}{TextBoxSubManualThree} ,-width => $TextEntryWidth,) )->g_pack(-side=>'left',-expand => '1',-fill=>'x',);
##	($TextBoxSubManualButtonThreeFrame->new_ttk__label(-text => "mil",) )->g_pack(-side=>'left');
#	#
#	($TextBoxSubManualButtonThreeFrame->new_ttk__button(-text => "单个",-width=> $TwoButtonwidth,-command => sub {
#		&RunScriptAct($MyScriptFile,'Run:ManualWordBoxZoom','Single',$CoverLayerSuffix,$VarDataStorage{ScaleX}{TextBoxSubManualThree},$VarDataStorage{ScaleY}{TextBoxSubManualThree});
#	},) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
#	($TextBoxSubManualButtonThreeFrame->new_ttk__button(-text => "多个",-width=> $TwoButtonwidth,-command => sub {
#		&RunScriptAct($MyScriptFile,'Run:ManualWordBoxZoom','Multiple',$CoverLayerSuffix,$VarDataStorage{ScaleX}{TextBoxSubManualThree},$VarDataStorage{ScaleY}{TextBoxSubManualThree});
#	},) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	###################
	( my $TextBoxSubManualButtonFourFrame = $TextBoxSubNotebookPageManual->new_ttk__frame( -padding => $SubFramePadding, ) )->g_pack(-fill=>'x',-side=>'top', );
#	our $PageManualTextMirrorFour = 0;
	$VarDataStorage{Polyline}{TextBoxSubManualOne} = 8;
	$VarDataStorage{Polyline}{TextBoxSubManualTwo} = 10;
	( my $TextBoxSubManualButtonFourFrameOne = $TextBoxSubManualButtonFourFrame->new_ttk__frame( -padding => $SubFramePadding, -relief =>'groove',) )->g_pack(-side=>'left', );
	( my $TextBoxSubManualButtonFourFrameTwo = $TextBoxSubManualButtonFourFrame->new_ttk__frame( -padding => $SubFramePadding, -relief =>'groove',) )->g_pack(-side=>'left', );


	($TextBoxSubManualButtonFourFrameOne->new_ttk__label(-text => "外扩:",) )->g_pack(-side=>'left');
	($TextBoxSubManualButtonFourFrameOne->new_ttk__entry(-textvariable => \$VarDataStorage{Polyline}{TextBoxSubManualOne} ,-width => $TextEntryWidth,) )->g_pack(-side=>'left',-expand => '1',-fill=>'x',);
	($TextBoxSubManualButtonFourFrameOne->new_ttk__button(-text => "单个",-width=> $TwoButtonwidth,-command => sub {
		&RunScriptAct($MyScriptFile,'Run:ManualTextBoxExternalExpansion','Single',$VarDataStorage{Polyline}{TextBoxSubManualOne},);
	},) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	($TextBoxSubManualButtonFourFrameOne->new_ttk__button(-text => "多个",-width=> $TwoButtonwidth,-command => sub {
		&RunScriptAct($MyScriptFile,'Run:ManualTextBoxExternalExpansion','Multiple',$VarDataStorage{Polyline}{TextBoxSubManualOne},);
	},) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	#
	($TextBoxSubManualButtonFourFrameTwo->new_ttk__label(-text => "外扩:",) )->g_pack(-side=>'left');
	($TextBoxSubManualButtonFourFrameTwo->new_ttk__entry(-textvariable => \$VarDataStorage{Polyline}{TextBoxSubManualTwo} ,-width => $TextEntryWidth,) )->g_pack(-side=>'left',-expand => '1',-fill=>'x',);
	($TextBoxSubManualButtonFourFrameTwo->new_ttk__button(-text => "单个",-width=> $TwoButtonwidth,-command => sub {
		&RunScriptAct($MyScriptFile,'Run:ManualTextBoxExternalExpansion','Single',$VarDataStorage{Polyline}{TextBoxSubManualTwo},);
	},) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	($TextBoxSubManualButtonFourFrameTwo->new_ttk__button(-text => "多个",-width=> $TwoButtonwidth,-command => sub {
		&RunScriptAct($MyScriptFile,'Run:ManualTextBoxExternalExpansion','Multiple',$VarDataStorage{Polyline}{TextBoxSubManualTwo},);
	},) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);


	###################

	#
	#############################		文字	###################################### $TextRightDataFrame
	(my $TextSubNoteBookPageFrame = $TextRightDataFrame->new_ttk__frame())->g_pack(-expand => '1',-fill=>'both',-side=>'top',);

	(our $TextSubNotebookPage = $TextSubNoteBookPageFrame->new_ttk__notebook)->g_pack(-expand => '1',-fill=>'both',);
	(my $TextSubNotebookPageHW = $TextSubNotebookPage->new_ttk__frame(-padding => "3 3 3 3",) )->g_pack(-expand => '1',-fill=>'both',);
	(my $TextSubNotebookPageXY  = $TextSubNotebookPage->new_ttk__frame(-padding => "3 3 3 3",) )->g_pack(-expand => '1',-fill=>'both',);

	$TextSubNotebookPage->add($TextSubNotebookPageHW, -text => "宽&高");
	$TextSubNotebookPage->add($TextSubNotebookPageXY, -text => "比例");
	#############

	( my $TextSubHWButtonOneFrame = $TextSubNotebookPageHW->new_ttk__frame( -padding => $SubFramePadding,-relief =>'groove',) )->g_pack(-fill=>'x',-side=>'top', );
	( my $TextSubHWButtonOneleftFrame = $TextSubHWButtonOneFrame->new_ttk__frame( -padding => $SubFramePadding, ) )->g_pack(-fill=>'x',-side=>'left', );

	( my $TextSubHWButtonOneleftUpFrame = $TextSubHWButtonOneleftFrame->new_ttk__frame( -padding => $SubFramePadding, ) )->g_pack(-fill=>'x',-side=>'top', );

	( my $TextSubHWButtonOneleftDownFrame = $TextSubHWButtonOneleftFrame->new_ttk__frame( -padding => $SubFramePadding, ) )->g_pack(-fill=>'x',-side=>'top', );

	( my $TextSubHWButtonOneRightFrame = $TextSubHWButtonOneFrame->new_ttk__frame( -padding => $SubFramePadding, ) )->g_pack(-fill=>'x',-side=>'left', );
	( my $TextSubHWButtonOneRightUpFrame = $TextSubHWButtonOneRightFrame->new_ttk__frame(
#	 -padding => $SubFramePadding,
	  ) )->g_pack(-fill=>'x',-side=>'top', );


#	our $PageHWTextMirrorOne = 0;
	($TextSubHWButtonOneleftUpFrame->new_ttk__checkbutton(-text => "镜像", -variable => \$VarDataStorage{Mirror}{TextSubHWOne},-offvalue => 0, -onvalue => 1))->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	($TextSubHWButtonOneleftUpFrame->new_ttk__label(-text => "字宽:",) )->g_pack(-side=>'left');
	($TextSubHWButtonOneleftUpFrame->new_ttk__entry(-textvariable => \$VarDataStorage{Width}{TextSubHWOne} ,-width => $TextEntryWidth,) )->g_pack(-side=>'left',-expand => '1',-fill=>'x',);
#	($TextSubHWButtonOneleftUpFrame->new_ttk__label(-text => "mil",) )->g_pack(-side=>'left');
	#
#	($TextSubHWButtonOneleftUpFrame->new_ttk__button(-text => "$ConvButtonText",-width=> $ConvButtonWidth,-command => sub { &SwapDataAct(\$VarDataStorage{Width}{TextSubHWOne},\$VarDataStorage{Height}{TextSubHWOne}); },) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	#
	($TextSubHWButtonOneleftUpFrame->new_ttk__label(-text => "字高:",) )->g_pack(-side=>'left');
	($TextSubHWButtonOneleftUpFrame->new_ttk__entry(-textvariable => \$VarDataStorage{Height}{TextSubHWOne} ,-width => $TextEntryWidth,) )->g_pack(-side=>'left',-expand => '1',-fill=>'x',);
#	($TextSubHWButtonOneleftUpFrame->new_ttk__label(-text => "mil",) )->g_pack(-side=>'left');
	#
#	our $SerialTextSpace = 4.5 ;
	our $SerialTextSpace = 10 ;
	($TextSubHWButtonOneleftDownFrame->new_ttk__label(-text => "连续文字间距离:",) )->g_pack(-side=>'left');
	($TextSubHWButtonOneleftDownFrame->new_ttk__entry(-textvariable => \$SerialTextSpace ,-width => $TextEntryWidth,) )->g_pack(-side=>'left',-expand => '1',-fill=>'x',);
#	($TextSubHWButtonOneleftDownFrame->new_ttk__label(-text => "mil",) )->g_pack(-side=>'left');
	#
	($TextSubHWButtonOneleftDownFrame->new_ttk__label(-text => "类型",) )->g_pack(-side=>'left');
	our @TextCategoryData = qw/线 铜皮/;
	our %TextCategoryDataConv = (
		'线' => 'Line',
		'铜皮' => 'Surface',
	);
	our $TextCategoryOption = $TextCategoryData[0];
	(our $SignatureCombobox = $TextSubHWButtonOneleftDownFrame->new_ttk__combobox(-textvariable => \$TextCategoryOption,-values => "@TextCategoryData", -width => 4,-state =>"readonly",) )-> g_pack(-side=>'left',-fill=>'x',);
	($TextSubHWButtonOneRightUpFrame->new_ttk__button(-text => "单个", -width=> $TwoButtonwidth2, -command => sub {
		&RunScriptAct($MyScriptFile,'Run:TextWidthHeightZoom','AutoSingle',$TextCategoryDataConv{$TextCategoryOption},$VarDataStorage{Width}{TextSubHWOne},$VarDataStorage{Height}{TextSubHWOne},$VarDataStorage{Mirror}{TextSubHWOne});
	},) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	#
	($TextSubHWButtonOneRightUpFrame->new_ttk__button(-text => "多个", -width=> $TwoButtonwidth2, -command => sub {
		&RunScriptAct($MyScriptFile,'Run:TextWidthHeightZoom','AutoMultiple',$TextCategoryDataConv{$TextCategoryOption},$VarDataStorage{Width}{TextSubHWOne},$VarDataStorage{Height}{TextSubHWOne},$VarDataStorage{Mirror}{TextSubHWOne});
	},) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	#
	($TextSubHWButtonOneRightFrame->new_ttk__button(-text => "整层", -width=> $TwoButtonwidthAuto, -command => sub {
		 &RunScriptAct($MyScriptFile,'Run:AutoTextWidthHeightAutoZoom',$SerialTextSpace,$TextCategoryDataConv{$TextCategoryOption},$VarDataStorage{Width}{TextSubHWOne},$VarDataStorage{Height}{TextSubHWOne},$VarDataStorage{Mirror}{TextSubHWOne});
	},) )->g_pack(-side=>'bottom',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	###############
	( my $TextSubHWButtonTwoFrame = $TextSubNotebookPageHW->new_ttk__frame( -padding => $SubFramePadding,	-relief =>'groove', ) )->g_pack(-fill=>'x',-side=>'top', );
#	our $PageHWTextMirrorTwo = 0;
	($TextSubHWButtonTwoFrame->new_ttk__checkbutton(-text => "镜像", -variable => \$VarDataStorage{Mirror}{TextSubHWTwo},-offvalue => 0, -onvalue => 1))->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	($TextSubHWButtonTwoFrame->new_ttk__label(-text => "X宽:",) )->g_pack(-side=>'left');
	($TextSubHWButtonTwoFrame->new_ttk__entry(-textvariable => \$VarDataStorage{Width}{TextSubHWTwo} ,-width => $TextEntryWidth,) )->g_pack(-side=>'left',-expand => '1',-fill=>'x',);
#	($TextSubHWButtonTwoFrame->new_ttk__label(-text => "mil",) )->g_pack(-side=>'left');
	#
	($TextSubHWButtonTwoFrame->new_ttk__button(-text => "$ConvButtonText",-width=> $ConvButtonWidth,-command => sub { &SwapDataAct(\$VarDataStorage{Width}{TextSubHWTwo},\$VarDataStorage{Height}{TextSubHWTwo}); },) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	#
	($TextSubHWButtonTwoFrame->new_ttk__label(-text => "Y宽:",) )->g_pack(-side=>'left');
	($TextSubHWButtonTwoFrame->new_ttk__entry(-textvariable => \$VarDataStorage{Height}{TextSubHWTwo} ,-width => $TextEntryWidth,) )->g_pack(-side=>'left',-expand => '1',-fill=>'x',);
#	($TextSubHWButtonTwoFrame->new_ttk__label(-text => "mil",) )->g_pack(-side=>'left');
	#
	($TextSubHWButtonTwoFrame->new_ttk__button(-text => "单个",-width=> $TwoButtonwidth,-command => sub {
		&RunScriptAct($MyScriptFile,'Run:TextWidthHeightZoom','Single',$TextCategoryDataConv{$TextCategoryOption},$VarDataStorage{Width}{TextSubHWTwo},$VarDataStorage{Height}{TextSubHWTwo},$VarDataStorage{Mirror}{TextSubHWTwo});
	},) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	#
	($TextSubHWButtonTwoFrame->new_ttk__button(-text => "多个",-width=> $TwoButtonwidth,-command => sub {
		&RunScriptAct($MyScriptFile,'Run:TextWidthHeightZoom','Multiple',$TextCategoryDataConv{$TextCategoryOption},$VarDataStorage{Width}{TextSubHWTwo},$VarDataStorage{Height}{TextSubHWTwo},$VarDataStorage{Mirror}{TextSubHWTwo});
	},) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	###################
	( my $TextSubHWButtonThreeFrame = $TextSubNotebookPageHW->new_ttk__frame( -padding => $SubFramePadding,	-relief =>'groove', ) )->g_pack(-fill=>'x',-side=>'top', );
#	our $PageHWTextMirrorThree = 0;
	($TextSubHWButtonThreeFrame->new_ttk__checkbutton(-text => "镜像", -variable => \$VarDataStorage{Mirror}{TextSubHWThree},-offvalue => 0, -onvalue => 1))->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	($TextSubHWButtonThreeFrame->new_ttk__label(-text => "X宽:",) )->g_pack(-side=>'left');
	($TextSubHWButtonThreeFrame->new_ttk__entry(-textvariable => \$VarDataStorage{Width}{TextSubHWThree} ,-width => $TextEntryWidth,) )->g_pack(-side=>'left',-expand => '1',-fill=>'x',);
#	($TextSubHWButtonThreeFrame->new_ttk__label(-text => "mil",) )->g_pack(-side=>'left');
	#
	($TextSubHWButtonThreeFrame->new_ttk__button(-text => "$ConvButtonText",-width=> $ConvButtonWidth,-command => sub { &SwapDataAct(\$VarDataStorage{Width}{TextSubHWThree},\$VarDataStorage{Height}{TextSubHWThree}); },) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	#
	($TextSubHWButtonThreeFrame->new_ttk__label(-text => "Y宽:",) )->g_pack(-side=>'left');
	($TextSubHWButtonThreeFrame->new_ttk__entry(-textvariable => \$VarDataStorage{Height}{TextSubHWThree} ,-width => $TextEntryWidth,) )->g_pack(-side=>'left',-expand => '1',-fill=>'x',);
#	($TextSubHWButtonThreeFrame->new_ttk__label(-text => "mil",) )->g_pack(-side=>'left');
	#
	($TextSubHWButtonThreeFrame->new_ttk__button(-text => "单个",-width=> $TwoButtonwidth,-command => sub {
		&RunScriptAct($MyScriptFile,'Run:TextWidthHeightZoom','Single',$TextCategoryDataConv{$TextCategoryOption},$VarDataStorage{Width}{TextSubHWThree},$VarDataStorage{Height}{TextSubHWThree},$VarDataStorage{Mirror}{TextSubHWThree});
	},) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	#
	($TextSubHWButtonThreeFrame->new_ttk__button(-text => "多个",-width=> $TwoButtonwidth,-command => sub {
		&RunScriptAct($MyScriptFile,'Run:TextWidthHeightZoom','Multiple',$TextCategoryDataConv{$TextCategoryOption},$VarDataStorage{Width}{TextSubHWThree},$VarDataStorage{Height}{TextSubHWThree},$VarDataStorage{Mirror}{TextSubHWThree});
	},) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	###################

	( my $TextSubXYButtonOneFrame = $TextSubNotebookPageXY->new_ttk__frame( -padding => $SubFramePadding,-relief =>'groove',) )->g_pack(-fill=>'x',-side=>'top', );
	( my $TextSubXYButtonOneleftFrame = $TextSubXYButtonOneFrame->new_ttk__frame( -padding => $SubFramePadding, ) )->g_pack(-fill=>'x',-side=>'left', );

	( my $TextSubXYButtonOneleftUpFrame = $TextSubXYButtonOneleftFrame->new_ttk__frame( -padding => $SubFramePadding, ) )->g_pack(-fill=>'x',-side=>'top', );

	( my $TextSubXYButtonOneleftDownFrame = $TextSubXYButtonOneleftFrame->new_ttk__frame( -padding => $SubFramePadding, ) )->g_pack(-fill=>'x',-side=>'top', );

	( my $TextSubXYButtonOneRightFrame = $TextSubXYButtonOneFrame->new_ttk__frame(
#	 -padding => $SubFramePadding,
	 ) )->g_pack(-fill=>'x',-side=>'left', );
	( my $TextSubXYButtonOneRightUpFrame = $TextSubXYButtonOneRightFrame->new_ttk__frame( -padding => $SubFramePadding, ) )->g_pack(-fill=>'x',-side=>'top', );

#	our $PageXYTextMirrorOne = 0;
	($TextSubXYButtonOneleftUpFrame->new_ttk__checkbutton(-text => "镜像", -variable => \$VarDataStorage{Mirror}{TextSubXYOne},-offvalue => 0, -onvalue => 1))->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	($TextSubXYButtonOneleftUpFrame->new_ttk__label(-text => "X:",) )->g_pack(-side=>'left');
	($TextSubXYButtonOneleftUpFrame->new_ttk__entry(-textvariable => \$VarDataStorage{ScaleX}{TextSubXYOne} ,-width => $TextEntryWidth,) )->g_pack(-side=>'left',-expand => '1',-fill=>'x',);
#	($TextSubXYButtonOneleftUpFrame->new_ttk__label(-text => "mil",) )->g_pack(-side=>'left');
	#
	($TextSubXYButtonOneleftUpFrame->new_ttk__button(-text => "$ConvButtonText",-width=> $ConvButtonWidth,-command => sub { &SwapDataAct(\$VarDataStorage{ScaleX}{TextSubXYOne},\$VarDataStorage{ScaleY}{TextSubXYOne}); },) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	#
	($TextSubXYButtonOneleftUpFrame->new_ttk__label(-text => "Y:",) )->g_pack(-side=>'left');
	($TextSubXYButtonOneleftUpFrame->new_ttk__entry(-textvariable => \$VarDataStorage{ScaleY}{TextSubXYOne} ,-width => $TextEntryWidth,) )->g_pack(-side=>'left',-expand => '1',-fill=>'x',);
#	($TextSubXYButtonOneleftUpFrame->new_ttk__label(-text => "mil",) )->g_pack(-side=>'left');
	#
	($TextSubXYButtonOneleftDownFrame->new_ttk__label(-text => "连续文字间距离:",) )->g_pack(-side=>'left');
	($TextSubXYButtonOneleftDownFrame->new_ttk__entry(-textvariable => \$SerialTextSpace ,-width => $TextEntryWidth,) )->g_pack(-side=>'left',-expand => '1',-fill=>'x',);
#	($TextSubXYButtonOneleftDownFrame->new_ttk__label(-text => "mil",) )->g_pack(-side=>'left');
	#
#	($TextSubXYButtonOneleftDownFrame->new_ttk__label(-text => "类型",) )->g_pack(-side=>'left');
#	(our $SignatureCombobox = $TextSubXYButtonOneleftDownFrame->new_ttk__combobox(-textvariable => \$TextCategoryOption,-values => "@TextCategoryData", -width => 4,-state =>"readonly",) )-> g_pack(-side=>'left',-fill=>'x',);
	($TextSubXYButtonOneRightUpFrame->new_ttk__button(-text => "单个", -width=> $TwoButtonwidth2, -command => sub {
		&RunScriptAct($MyScriptFile,'Run:TextScaleZoom','Single',$VarDataStorage{ScaleX}{TextSubXYOne},$VarDataStorage{ScaleY}{TextSubXYOne},$VarDataStorage{Mirror}{TextSubXYOne});
	},) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	($TextSubXYButtonOneRightUpFrame->new_ttk__button(-text => "多个", -width=> $TwoButtonwidth2, -command => sub {
		&RunScriptAct($MyScriptFile,'Run:TextScaleZoom','Multiple',$VarDataStorage{ScaleX}{TextSubXYOne},$VarDataStorage{ScaleY}{TextSubXYOne},$VarDataStorage{Mirror}{TextSubXYOne});
	},) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);

	($TextSubXYButtonOneRightFrame->new_ttk__button(-text => "整层", -width=> $TwoButtonwidthAuto, -command => sub {
		&RunScriptAct($MyScriptFile,'Run:TextScaleAutoZoom',$SerialTextSpace,$VarDataStorage{ScaleX}{TextSubXYOne},$VarDataStorage{ScaleY}{TextSubXYOne},$VarDataStorage{Mirror}{TextSubXYOne});
	},) )->g_pack(-side=>'bottom',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	###############
	( my $TextSubXYButtonTwoFrame = $TextSubNotebookPageXY->new_ttk__frame( -padding => $SubFramePadding,	-relief =>'groove', ) )->g_pack(-fill=>'x',-side=>'top', );
	our $PageXYTextMirrorTwo = 0;
	($TextSubXYButtonTwoFrame->new_ttk__checkbutton(-text => "镜像", -variable => \$VarDataStorage{Mirror}{TextSubXYTwo},-offvalue => 0, -onvalue => 1))->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	($TextSubXYButtonTwoFrame->new_ttk__label(-text => "X:",) )->g_pack(-side=>'left');
	($TextSubXYButtonTwoFrame->new_ttk__entry(-textvariable => \$VarDataStorage{ScaleX}{TextSubXYTwo} ,-width => $TextEntryWidth,) )->g_pack(-side=>'left',-expand => '1',-fill=>'x',);
#	($TextSubXYButtonTwoFrame->new_ttk__label(-text => "mil",) )->g_pack(-side=>'left');
	#
	($TextSubXYButtonTwoFrame->new_ttk__button(-text => "$ConvButtonText",-width=> $ConvButtonWidth,-command => sub { &SwapDataAct(\$VarDataStorage{ScaleX}{TextSubXYTwo},\$VarDataStorage{ScaleY}{TextSubXYTwo}); },) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	#
	($TextSubXYButtonTwoFrame->new_ttk__label(-text => "Y:",) )->g_pack(-side=>'left');
	($TextSubXYButtonTwoFrame->new_ttk__entry(-textvariable => \$VarDataStorage{ScaleY}{TextSubXYTwo} ,-width => $TextEntryWidth,) )->g_pack(-side=>'left',-expand => '1',-fill=>'x',);
#	($TextSubXYButtonTwoFrame->new_ttk__label(-text => "mil",) )->g_pack(-side=>'left');
	#
	($TextSubXYButtonTwoFrame->new_ttk__button(-text => "单个",-width=> $TwoButtonwidth,-command => sub {
		&RunScriptAct($MyScriptFile,'Run:TextScaleZoom','Single',$VarDataStorage{ScaleX}{TextSubXYTwo},$VarDataStorage{ScaleY}{TextSubXYTwo},$VarDataStorage{Mirror}{TextSubXYTwo});
	},) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	($TextSubXYButtonTwoFrame->new_ttk__button(-text => "多个",-width=> $TwoButtonwidth,-command => sub {
		&RunScriptAct($MyScriptFile,'Run:TextScaleZoom','Multiple',$VarDataStorage{ScaleX}{TextSubXYTwo},$VarDataStorage{ScaleY}{TextSubXYTwo},$VarDataStorage{Mirror}{TextSubXYTwo});
	},) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	###################
	( my $TextSubXYButtonThreeFrame = $TextSubNotebookPageXY->new_ttk__frame( -padding => $SubFramePadding,	-relief =>'groove', ) )->g_pack(-fill=>'x',-side=>'top', );
	our $PageXYTextMirrorThree = 0;
	($TextSubXYButtonThreeFrame->new_ttk__checkbutton(-text => "镜像", -variable => \$VarDataStorage{Mirror}{TextSubXYThree},-offvalue => 0, -onvalue => 1))->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	($TextSubXYButtonThreeFrame->new_ttk__label(-text => "X:",) )->g_pack(-side=>'left');
	($TextSubXYButtonThreeFrame->new_ttk__entry(-textvariable => \$VarDataStorage{ScaleX}{TextSubXYThree} ,-width => $TextEntryWidth,) )->g_pack(-side=>'left',-expand => '1',-fill=>'x',);
#	($TextSubXYButtonThreeFrame->new_ttk__label(-text => "mil",) )->g_pack(-side=>'left');
	#
	($TextSubXYButtonThreeFrame->new_ttk__button(-text => "$ConvButtonText",-width=> $ConvButtonWidth,-command => sub { &SwapDataAct(\$VarDataStorage{ScaleX}{TextSubXYThree},\$VarDataStorage{ScaleY}{TextSubXYThree}); },) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	#
	($TextSubXYButtonThreeFrame->new_ttk__label(-text => "Y:",) )->g_pack(-side=>'left');
	($TextSubXYButtonThreeFrame->new_ttk__entry(-textvariable => \$VarDataStorage{ScaleY}{TextSubXYThree} ,-width => $TextEntryWidth,) )->g_pack(-side=>'left',-expand => '1',-fill=>'x',);
#	($TextSubXYButtonThreeFrame->new_ttk__label(-text => "mil",) )->g_pack(-side=>'left');
	#
	($TextSubXYButtonThreeFrame->new_ttk__button(-text => "单个",-width=> $TwoButtonwidth,-command => sub {
		&RunScriptAct($MyScriptFile,'Run:TextScaleZoom','Single',$VarDataStorage{ScaleX}{TextSubXYThree},$VarDataStorage{ScaleY}{TextSubXYThree},$VarDataStorage{Mirror}{TextSubXYThree});
	},) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	($TextSubXYButtonThreeFrame->new_ttk__button(-text => "多个",-width=> $TwoButtonwidth,-command => sub {
		&RunScriptAct($MyScriptFile,'Run:TextScaleZoom','Multiple',$VarDataStorage{ScaleX}{TextSubXYThree},$VarDataStorage{ScaleY}{TextSubXYThree},$VarDataStorage{Mirror}{TextSubXYThree});
	},) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	###################

	#
	#############################	后处理	###################################### $PostProceRightDataFrame
	( my $PostProceSubLeftButtonFrame = $PostProceRightDataFrame->new_ttk__frame( -padding => $SubFramePadding, ) )->g_pack(-fill=>'x',-side=>'left', -expand => '1',);
#	( my $PostProceSubLeftButtonFrame2 = $PostProceSubLeftButtonFrame->new_ttk__frame( -padding => $SubFramePadding, ) )->g_pack(-side=>'left', -expand => '1',);
#	($PostProceSubLeftButtonFrame2->new_ttk__button(-text => "文字套字框",-width=> 8,-command => sub { &TextCoverTextBoxButtonAct; },) )->g_pack(-side=>'left',-pady => 2,-padx => 2,);
#	($PostProceSubLeftButtonFrame2->new_ttk__button(-text => "阻焊套文字",-width=> 8,-command => sub { &SolderMaskCoverTextBoxButtonAct; },) )->g_pack(-side=>'left',-pady => 2,-padx => 2,);

	($PostProceSubLeftButtonFrame->new_ttk__button(-text => "添加标记",-width=> 8,-command => sub {&RunScriptAct($MyScriptFile,'Run:AddMark');},) )->g_pack(-side=>'top',-pady => 2,-ipadx => 2,-expand => '1',);
	($PostProceSubLeftButtonFrame->new_ttk__button(-text => "文字套字框",-width=> 8,-command => sub { &TextCoverTextBoxButtonAct; },) )->g_pack(-side=>'top',-pady => 2,-ipadx => 2,-expand => '1',);
	($PostProceSubLeftButtonFrame->new_ttk__button(-text => "阻焊套文字",-width=> 8,-command => sub { &SolderMaskCoverTextBoxButtonAct; },) )->g_pack(-side=>'top',-pady => 2,-ipadx => 2,-expand => '1',);
	( my $PostProceSubRightButtonFrame = $PostProceRightDataFrame->new_ttk__frame( -padding => $SubFramePadding, ) )->g_pack(-fill=>'x',-side=>'left',-expand => '1', );
#	($PostProceSubRightButtonFrame->new_ttk__button(-text => "添加序号",-width=> 8,-command => sub { },) )->g_pack(-side=>'top',-pady => 2,-ipadx => 2,-expand => '1',);

	( my $SilkBridgeOptFrame = $PostProceSubRightButtonFrame->new_ttk__frame( -padding => $SubFramePadding, -relief =>'groove', ) )->g_pack(-side=>'top',);
	( my $SilkBridgeOptSetFrame = $SilkBridgeOptFrame->new_ttk__frame( -padding => $SubFramePadding,) )->g_pack(-side=>'top',-fill=>'x',);
	($SilkBridgeOptSetFrame->new_ttk__label(-text => "外层补偿:",) )->g_pack(-side=>'left');
	our $OutPadCompensating = 1.2;
	($SilkBridgeOptSetFrame->new_ttk__entry(-textvariable => \$OutPadCompensating ,-width => 3,) )->g_pack(-side=>'left',);
	($SilkBridgeOptFrame->new_ttk__button(-text => "字符桥优化",-width=> 8,-command => sub {&SilkBridgeOptButtonAct; },) )->g_pack(-side=>'top',-fill=>'x',-expand => '1',);
	($PostProceSubRightButtonFrame->new_ttk__button(-text => "字符分析",-width=> 8,-command => sub {&RunScriptAct($MyScriptFile,'Run:OpenSilkCheckList'); },) )->g_pack(-side=>'top',-pady => 2,-ipadx => 2,-expand => '1',);



	our $BarMsg = '欢迎进入Neo的世界.';
	( $MainFrame->new_ttk__label(-textvariable => \$BarMsg,-foreground =>'blue',) )->g_pack(-side=>'bottom',-fill=>'x',);

	(our $MainButtonFrame = $MainFrame->new_ttk__frame(-relief => $TestRelief,-padding => "3 4 3 0",))->g_pack(-side=>'bottom',-fill=>'x',);
	$mw->g_bind('<Enter>',sub {$BarMsg = "默认单位为mil.";});

	#展开状态
	our $ExpandState;
	our @ExpandStateOpt = qw /展开 收缩/;
	our $ExpandStateText = $ExpandStateOpt[1];
	#our $ExpandStateText = $ExpandStateOpt[0];
	our $MainButtonPadX = 3 ;
	our $MainButtonPadY = 0 ;
	($MainButtonFrame->new_ttk__button(-textvariable => \$ExpandStateText,-width=> 10,-command => sub {&ExpandStateSwitch;},) )->g_pack(-side=>'left',-padx => 10,-padx => $MainButtonPadX,-pady => $MainButtonPadY,);
	(our $HelpButton = $MainButtonFrame->new_ttk__button(-text => '?',-width=> 1,) )->g_pack(-side=>'left',-padx => 10,-padx => $MainButtonPadX,-pady => $MainButtonPadY,-expand => '1',);
	($MainButtonFrame->new_ttk__button(-text => "退出",-width=> 10,-command => sub {$mw->g_destroy;},) )->g_pack(-side=>'right',-padx => 10,-padx => $MainButtonPadX,-pady => $MainButtonPadY,);
	&SwitchDisplay('AllExpand');
	if ( defined $MainConfig{'ShowSub'} ) {
		my $ShowSubNum = $ShowSubConv{$MainConfig{'ShowSub'}} ;
		&SwitchDisplay('Single',$ShowSubNum,$ShowSubNum,);
	}
	
	
	
	Tkx::MainLoop;
}

sub SwapDataAct {  #&SwapDataAct(\$,\$);
	my ($tVarRam1,$tVarRam2) = ($_[0],$_[1]);
	my ($tVar1,$tVar2) = ($$tVarRam1,$$tVarRam2);
	($$tVarRam1,$$tVarRam2) = ($tVar2,$tVar1);
}

sub ExpandStateSwitch {
	if ( $ExpandStateText eq $ExpandStateOpt[0] ) {
		$ExpandStateText = $ExpandStateOpt[1];
		&SwitchDisplay('AllExpand');
	} else {
		$ExpandStateText = $ExpandStateOpt[0];
		&SwitchDisplay('AllShrink');
	}
}

sub SwitchDisplay {
	my $SwitchMode = $_[0];
	my $ParameterOne = $_[1];
	my $ParameterTwo = $_[2];
	#print "SwitchMode=$SwitchMode,ParameterOne=$ParameterOne,ParameterTwo=$ParameterTwo\n";
	if ( $SwitchMode eq  'AllExpand' ){
		for my $tNumOne ( 1 .. 4 ) {
			for my $tNumTwo ( 1 .. 4 ) {
				if ( $GuiFrameStatusStorage{$tNumOne}{$tNumTwo} eq 'yes' ) {
					if ($tNumOne ne $tNumTwo ) {
						$GuiFrameVarStorage{$tNumOne}{$tNumTwo}->g_pack_forget;
						$GuiFrameStatusStorage{$tNumOne}{$tNumTwo} = 'no';
					}
				} else {
					if ($tNumOne eq $tNumTwo ) {
						$GuiFrameVarStorage{$tNumOne}{$tNumTwo}->g_pack(-side=>'top',-padx => $ButtonPadX,-pady => $ButtonPadY,-fill=>'y',-expand => '1',);
						$GuiFrameStatusStorage{$tNumOne}{$tNumTwo} = 'yes';
					}
				}
			}
			if ( $GuiSubFrameStatusStorage{$tNumOne} eq 'yes' ) {  #子界面
				$GuiSubFrameVarStorage{$tNumOne}->g_pack_forget;
			}
			$GuiSubFrameVarStorage{$tNumOne}->g_pack(-side=>'top',-expand => '1',-fill=>'both',-padx => $SubFramePad,-pady => $SubFramePad,-ipadx => $SubFrameIPad,-ipady => $SubFrameIPad,);
			$GuiSubFrameStatusStorage{$tNumOne} = 'yes';

		}
	} elsif ( $SwitchMode eq  'AllShrink' ){
		for my $tNumOne ( 1 .. 4 ) {
			for my $tNumTwo ( 1 .. 4 ) {
				if ( $tNumOne == 1 ) {
					if ( $GuiFrameStatusStorage{$tNumOne}{$tNumTwo} eq 'no' ) {
						if ($tNumOne eq $tNumTwo ) {
							$GuiFrameVarStorage{$tNumOne}{$tNumTwo}->g_pack(-side=>'top',-padx => $ButtonPadX,-pady => $ButtonPadY,-fill=>'y',-expand => '1',);
						}else{
							$GuiFrameVarStorage{$tNumOne}{$tNumTwo}->g_pack(-side=>'top',-padx => $ButtonPadX,-pady => $ButtonPadY,-fill=>'y',);
						}
						$GuiFrameStatusStorage{$tNumOne}{$tNumTwo} = 'yes';
					}
				} else {
					if ( $GuiFrameStatusStorage{$tNumOne}{$tNumTwo} eq 'yes' ) {
						$GuiFrameVarStorage{$tNumOne}{$tNumTwo}->g_pack_forget;
						$GuiFrameStatusStorage{$tNumOne}{$tNumTwo} = 'no';
					}
				}
			}

			if ( $tNumOne == 1 ) {
				if ( $GuiSubFrameStatusStorage{$tNumOne} eq 'no' ) {  #子界面
					$GuiSubFrameVarStorage{$tNumOne}->g_pack(-side=>'top',-expand => '1',-fill=>'both',-padx => $SubFramePad,-pady => $SubFramePad,-ipadx => $SubFrameIPad,-ipady => $SubFrameIPad,);
					$GuiSubFrameStatusStorage{$tNumOne} = 'yes';
				}
			} else {
				if ( $GuiSubFrameStatusStorage{$tNumOne} eq 'yes' ) {  #子界面
					$GuiSubFrameVarStorage{$tNumOne}->g_pack_forget;
					$GuiSubFrameStatusStorage{$tNumOne} = 'no';
				}
			}
		}
	} elsif ( $SwitchMode eq  'Single' ){
		for my $tNumOne ( 1 .. 4 ) {
			if ( $tNumOne == $ParameterTwo ) {
				for my $tNumTwo ( 1 .. 4 ) {
					if ( $tNumOne == $ParameterTwo ) {
						if ( $GuiFrameStatusStorage{$tNumOne}{$tNumTwo} eq 'yes' ) {
							$GuiFrameVarStorage{$tNumOne}{$tNumTwo}->g_pack_forget;
						}
						if ($tNumOne eq $tNumTwo ) {
							$GuiFrameVarStorage{$tNumOne}{$tNumTwo}->g_pack(-side=>'top',-padx => $ButtonPadX,-pady => $ButtonPadY,-fill=>'y',-expand => '1',);
						}else{
							$GuiFrameVarStorage{$tNumOne}{$tNumTwo}->g_pack(-side=>'top',-padx => $ButtonPadX,-pady => $ButtonPadY,-fill=>'y',);
						}

#						$GuiFrameVarStorage{$tNumOne}{$tNumTwo}->g_pack(-side=>'top',-padx => $ButtonPadX,-pady => $ButtonPadY,-fill=>'y',-expand => '1',);
						$GuiFrameStatusStorage{$tNumOne}{$tNumTwo} = 'yes';
					}
				}
				if ( $GuiSubFrameStatusStorage{$tNumOne} eq 'no' ) {  #子界面
					$GuiSubFrameVarStorage{$tNumOne}->g_pack(-side=>'top',-expand => '1',-fill=>'both',-padx => $SubFramePad,-pady => $SubFramePad,-ipadx => $SubFrameIPad,-ipady => $SubFrameIPad,);
					$GuiSubFrameStatusStorage{$tNumOne} = 'yes';
				}
			} else {
				if ( $GuiSubFrameStatusStorage{$tNumOne} eq 'yes' ) {  #子界面
					$GuiSubFrameVarStorage{$tNumOne}->g_pack_forget;
					$GuiSubFrameStatusStorage{$tNumOne} = 'no';
				}
			}
		}
		$ExpandStateText = $ExpandStateOpt[0];
	} elsif ( $SwitchMode eq  'Multiple' ){
		my @ShowSubLists;
		for my $tNumOne ( 1 .. 4 ) {
			if ( $GuiSubFrameStatusStorage{$tNumOne} eq 'yes' ) {  #子界面
				push @ShowSubLists,$tNumOne;
			}
		}
		if ( ( scalar (@ShowSubLists) > 1 and $GuiSubFrameStatusStorage{$ParameterTwo} eq 'no' ) or ( scalar (@ShowSubLists) <= 1 ) ) {  #子界面
			if ( $GuiFrameStatusStorage{$ParameterOne}{$ParameterTwo} eq 'yes' ) {
				$GuiFrameVarStorage{$ParameterOne}{$ParameterTwo}->g_pack_forget;
				$GuiFrameStatusStorage{$ParameterOne}{$ParameterTwo} = 'no';
			}

			for my $tNumOne ( 1 .. 4 ) {
				if ( $GuiSubFrameStatusStorage{$tNumOne} eq 'yes' ) {  #子界面
					$GuiSubFrameVarStorage{$tNumOne}->g_pack_forget;
					$GuiSubFrameVarStorage{$tNumOne}->g_pack(-side=>'top',-expand => '1',-fill=>'both',-padx => $SubFramePad,-pady => $SubFramePad,-ipadx => $SubFrameIPad,-ipady => $SubFrameIPad,);
					$GuiSubFrameStatusStorage{$tNumOne} = 'yes';
				}
				if ( $tNumOne == $ParameterTwo ) {
					for my $tNumTwo ( 1 .. 4 ) {
						if ( $tNumTwo == $ParameterTwo ) {
							if ( $GuiFrameStatusStorage{$tNumOne}{$tNumTwo} eq 'no' ) {
								if ($tNumOne eq $tNumTwo ) {
									$GuiFrameVarStorage{$tNumOne}{$tNumTwo}->g_pack(-side=>'top',-padx => $ButtonPadX,-pady => $ButtonPadY,-fill=>'y',-expand => '1',);
								}else{
									$GuiFrameVarStorage{$tNumOne}{$tNumTwo}->g_pack(-side=>'top',-padx => $ButtonPadX,-pady => $ButtonPadY,-fill=>'y',);
								}
#								$GuiFrameVarStorage{$tNumOne}{$tNumTwo}->g_pack(-side=>'top',-padx => $ButtonPadX,-pady => $ButtonPadY,-fill=>'y',-expand => '1',);
								$GuiFrameStatusStorage{$tNumOne}{$tNumTwo} = 'yes';
							}
						} else {
							if ( $GuiFrameStatusStorage{$tNumOne}{$tNumTwo} eq 'yes' ) {
								$GuiFrameVarStorage{$tNumOne}{$tNumTwo}->g_pack_forget;
								$GuiFrameStatusStorage{$tNumOne}{$tNumTwo} = 'no';
							}
						}
					}
					$GuiSubFrameVarStorage{$tNumOne}->g_pack(-side=>'top',-expand => '1',-fill=>'both',-padx => $SubFramePad,-pady => $SubFramePad,-ipadx => $SubFrameIPad,-ipady => $SubFrameIPad,);
					$GuiSubFrameStatusStorage{$tNumOne} = 'yes';
				}
			}
		} else {
			if  ( ( scalar (@ShowSubLists) > 1 ) and ( $GuiSubFrameStatusStorage{$ParameterTwo} eq 'yes' ) ) {  #子界面
				$GuiSubFrameVarStorage{$ParameterTwo}->g_pack_forget;
				$GuiSubFrameStatusStorage{$ParameterTwo} = 'no';
			}

		}

		######
		my @ShowSubList;
		for my $tNumOne ( 1 .. 4 ) {
			if ( $GuiSubFrameStatusStorage{$tNumOne} eq 'yes' ) {  #子界面
				push @ShowSubList,$tNumOne;
			}
		}

		#按钮重新排列
		my @TempStorage;
		my %TmpStorageButton;
		my $tSubFrame;
		for my $tNumOne ( 1 .. 4 ) {
			if ( $GuiSubFrameStatusStorage{$tNumOne} eq 'no' ) {  #子界面
				push @TempStorage,$tNumOne;
			} else {
				push @TempStorage,$tNumOne;
				$tSubFrame = $tNumOne;
				push @{$TmpStorageButton{$tSubFrame}},@TempStorage;
#				print "$tSubFrame =  @{$TmpStorageButton{$tSubFrame}}\n";
				undef @TempStorage;
			}
		}

		push @{$TmpStorageButton{$tSubFrame}},@TempStorage;
#		print "$tSubFrame =  @{$TmpStorageButton{$tSubFrame}}\n-----------\n";
		for my $tShowSub ( @ShowSubList ) {
			for my $tNumTwo ( 1 .. 4 ) {
				if ( $GuiFrameStatusStorage{$tShowSub}{$tNumTwo} eq 'yes' ) {
					$GuiFrameVarStorage{$tShowSub}{$tNumTwo}->g_pack_forget;
					$GuiFrameStatusStorage{$tShowSub}{$tNumTwo} = 'no';
				}
			}
			for $tT ( @{$TmpStorageButton{$tShowSub}} ) {
				if ($tShowSub eq $tT ) {
					$GuiFrameVarStorage{$tShowSub}{$tT}->g_pack(-side=>'top',-padx => $ButtonPadX,-pady => $ButtonPadY,-fill=>'y',-expand => '1',);
				}else{
					$GuiFrameVarStorage{$tShowSub}{$tT}->g_pack(-side=>'top',-padx => $ButtonPadX,-pady => $ButtonPadY,-fill=>'y',);
				}
#				$GuiFrameVarStorage{$tShowSub}{$tT}->g_pack(-side=>'top',-padx => $ButtonPadX,-pady => $ButtonPadY,-fill=>'y',-expand => '1',);
				$GuiFrameStatusStorage{$tShowSub}{$tT} = 'yes';
			}

		}

		if ( scalar (@ShowSubList) == 4 ){
			$ExpandStateText = $ExpandStateOpt[1];
		}else{
			$ExpandStateText = $ExpandStateOpt[0];
		}
	}
#	Tkx::update('idletasks');
}

sub ShowSingleGui {  #显示单独的界面 方便调用
	my $SingleGuiMode = shift; #CreateCoverLayer ChangeSilkMinLineWidth TextAndTextBoxSeparated SilkBridgeOpt TextCoverTextBox SolderMaskCoverTextBox

	our $ButtonPadX = 1;
	our $ButtonPadY = 1;
	our ($SubFramePad,$SubFrameIPad,$SubFramePadding,) = (3,3,"3 3 1 3",);

	my %JobMatrix = &JobMatrixDispose($JOB);
	#my $SilkScreenLayer = join ('@',@{$JobMatrix{"SumData"}{"SilkScreen"}},);
	my @SilkScreenList = @{$JobMatrix{"SumData"}{"SilkScreen"}};

	use Tkx;
#	use Tkx::LabEntry;

	use File::Basename;
#	use utf8;
	my ($filename, $directories) = (fileparse($0, qw/\.exe \.com \.pl \.Neo/))[0,1];
	our $MyScriptFile =  "$directories"."$filename" . '.cshrc';
	unless ( -e $MyScriptFile ) {
		$MyScriptFile = $0 ;
	}

	#my $ThemeUse = "vista";
	my $ThemeUse = "clam";
	my ($StepInPadX,$SelJobGuiOffset,$LayerListGuiResize,) = (1,0,0,);
	our $MainColor = "#F0F0F0";
	if ( $ThemeUse eq "clam" ) {
		$StepInPadX = 4;
		$SelJobGuiOffset = 2;
	#	if ( `uname -r` =~ /^Windows\sNT\s5\.1\s\S*/ ) {
	#		$SelJobGuiOffset = $SelJobGuiOffset + 24;
	#	}
		$MainColor = "#DCDAD5";
		Tkx::ttk__style_theme_use("clam");#winnative clam alt default classic vista xpnative ###Tkx::ttk__style_theme_names();##vista
	}

	our $mw = Tkx::widget->new(".");
#	$mw->g_wm_geometry( "+" . int( Tkx::winfo('screenwidth', $mw) - 730 ) . "+" . 	'0' );
	$mw->g_wm_geometry( "+" . int( ( Tkx::winfo( 'screenwidth', $mw ) / 2 ) - 150 ) . "+" . int( ( Tkx::winfo( 'screenheight', $mw ) / 2 ) - 150 ) );
	$mw->g_wm_title("字符");
#	&GetImageFile('SetMwLogo',$mw);
	&iTkxGetImageFile('SetMwLogo',$mw);
	$mw->g_wm_attributes('-topmost',1);

	################ 层别
	( my $LayerListFrame = $mw->new_ttk__frame( -padding => $SubFramePadding, ) )->g_pack(-fill=>'y',-side=>'left', );
	( our $LayerList = $LayerListFrame->new_tk__listbox( -height => 4,-width => 4,-selectmode => "extended",-selectforeground =>'white',-exportselection => 0, ) )->g_pack( -side=>'left',-expand => '1',-fill=>'both', );
	( $tScrollbar = $LayerListFrame->new_ttk__scrollbar( -command => [$LayerList, "yview"], -orient => "vertical", ) )->g_pack( -side=>'left',-fill=>'y' );
	$LayerList->configure( -yscrollcommand => [$tScrollbar, "set"] );
	$LayerList->delete( '0', 'end' );
	$LayerList->insert( 'end',@SilkScreenList );
	$LayerList->select( 'set',0 ,'end' );

	our $CoverLayerSuffix = '-cover+';

	if ( $SingleGuiMode eq 'CreateCoverLayer' ) { #####		 套层			##################################
		our $SilkScreenToSolderMask = "5.5";
		our $SilkScreenToSmdBga = "7";
		( my $CoverLayerConfigFrame = $mw->new_ttk__frame( -padding => $SubFramePadding, ) )->g_pack(-fill=>'y',-side=>'left', );
		( my $CoverLayerTextFrame1 = $CoverLayerConfigFrame->new_ttk__frame( -padding => $SubFramePadding, ) )->g_pack(-fill=>'y',-side=>'top', );
		( my $CoverLayerTextFrame2 = $CoverLayerConfigFrame->new_ttk__frame( -padding => $SubFramePadding, ) )->g_pack(-fill=>'y',-side=>'top', );
		( my $CoverLayerTextFrame3 = $CoverLayerConfigFrame->new_ttk__frame( -padding => $SubFramePadding, ) )->g_pack(-fill=>'y',-side=>'top', );

		($CoverLayerTextFrame1->new_ttk__label(-text => "字符距阻焊:",) )->g_pack(-side=>'left');
		($CoverLayerTextFrame1->new_ttk__entry(-textvariable => \$SilkScreenToSolderMask ,-width => 7,) )->g_pack(-side=>'left',-expand => '1',-fill=>'x',);

		($CoverLayerTextFrame2->new_ttk__label(-text => "字符距Smd、Bga:",) )->g_pack(-side=>'left');
		($CoverLayerTextFrame2->new_ttk__entry(-textvariable => \$SilkScreenToSmdBga ,-width => 3,) )->g_pack(-side=>'left',-expand => '1',-fill=>'x',);
		#
#		($CoverLayerTextFrame3->new_ttk__label(-text => "套层后缀:",) )->g_pack(-side=>'left');
#		($CoverLayerTextFrame3->new_ttk__entry(-textvariable => \$CoverLayerSuffix ,-width => 9,) )->g_pack(-side=>'left',-expand => '1',-fill=>'x',);

		( my $CoverLayerButtonFrame = $CoverLayerConfigFrame->new_ttk__frame( -padding => $SubFramePadding, ) )->g_pack(-fill=>'y',-side=>'top', );

		($CoverLayerButtonFrame->new_ttk__button(-text => "创建套层",-width=> 8,-command => sub {$mw->g_wm_withdraw;&CreateCoverLayerButtonAct('InnRun');$mw->g_destroy;},) )->g_pack(-side=>'left',-padx => $ButtonPadX,-pady => $ButtonPadY,);
	} elsif ( $SingleGuiMode eq 'ChangeSilkMinLineWidth' ) { #####		 最小线宽			##################################

		( my $ChangeSilkMinLineWidthButtonFrame = $mw->new_ttk__frame( -padding => $SubFramePadding,) )->g_pack(-side=>'top',-padx => 1,-pady => 1,-ipadx => 1,-ipady => 1,);
		( my $ChangeSilkMinLineWidthFrame = $ChangeSilkMinLineWidthButtonFrame->new_ttk__frame( -padding => $SubFramePadding, ) )->g_pack(-side=>'top', );
		($ChangeSilkMinLineWidthFrame->new_ttk__label(-text => "字符最小线宽:",) )->g_pack(-side=>'left', -pady => 1,);
		our @SilkMinLineWidthData = qw/4 4.5 5/;
		#our $SilkMinLineWidth = $SilkMinLineWidthData[2];
		our $SilkMinLineWidth = $SilkMinLineWidthData[1];
		($ChangeSilkMinLineWidthFrame->new_ttk__combobox(-textvariable => \$SilkMinLineWidth,-values => "@SilkMinLineWidthData",-width => 3,) )->g_pack(-side=>'left',-fill=>'x',);
		($ChangeSilkMinLineWidthButtonFrame->new_ttk__button(-text => "修改",-width=> 8,-command => sub { $mw->g_wm_withdraw;&ChangeSilkMinLineWidthButtonAct('InnRun');$mw->g_destroy; },) )->g_pack(-side=>'top',-padx => 1,-pady => $ButtonPadY,);
	} elsif ( $SingleGuiMode eq 'TextAndTextBoxSeparated' ) { #####		 字框分离			##################################
		our $TextSeparatedLayerSuffix = '-text+';#分离的文字层后缀
		( my $TextSeparatedConfigButtonFrame = $mw->new_ttk__frame( -padding => $SubFramePadding,) )->g_pack(-side=>'top',-padx => 1,-pady => 1,-ipadx => 1,-ipady => 1,);
		( my $TextSeparatedConfigFrame = $TextSeparatedConfigButtonFrame->new_ttk__frame( -padding => $SubFramePadding, ) )->g_pack(-side=>'top', );
		($TextSeparatedConfigFrame->new_ttk__label(-text => "文字最大高度:",) )->g_pack(-side=>'left', -pady => 3,);
		our $TextSeparatedTextMaxHeight = 60;
		($TextSeparatedConfigFrame->new_ttk__entry(-textvariable => \$TextSeparatedTextMaxHeight ,-width => 5,) )->g_pack(-side=>'left',-fill=>'x',);

		($TextSeparatedConfigButtonFrame->new_ttk__button(-text => "字框分离",-width=> 8,-command => sub { $mw->g_wm_withdraw;&TextAndTextBoxSeparatedButtonAct('InnRun');$mw->g_destroy; },) )->g_pack(-side=>'top',-padx => 5,-pady => $ButtonPadY,);
	} elsif ( $SingleGuiMode eq 'TextCoverTextBox' ) { #####		 文字套字框			##################################
		($mw->new_ttk__button(-text => "文字套字框",-width=> 8,-command => sub { $mw->g_wm_withdraw;&TextCoverTextBoxButtonAct('InnRun');$mw->g_destroy; },) )->g_pack(-side=>'left',-padx => 5,-pady => $ButtonPadY,);
	} elsif ( $SingleGuiMode eq 'SolderMaskCoverTextBox' ) { #####		 阻焊套文字			##################################
		($mw->new_ttk__button(-text => "阻焊套文字",-width=> 8,-command => sub { $mw->g_wm_withdraw;&SolderMaskCoverTextBoxButtonAct('InnRun');$mw->g_destroy; },) )->g_pack(-side=>'left',-padx => 5,-pady => $ButtonPadY,);
	} elsif ( $SingleGuiMode eq 'SilkBridgeOpt' ) { #####		 字符桥优化			##################################
		( my $SilkBridgeOptFrame = $mw->new_ttk__frame( -padding => $SubFramePadding,  ) )->g_pack(-side=>'top',);
		( my $SilkBridgeOptSetFrame = $SilkBridgeOptFrame->new_ttk__frame( -padding => $SubFramePadding,) )->g_pack(-side=>'top',-fill=>'x',);
		($SilkBridgeOptSetFrame->new_ttk__label(-text => "外层补偿:",) )->g_pack(-side=>'left');
		our $OutPadCompensating = 1.2;
		($SilkBridgeOptSetFrame->new_ttk__entry(-textvariable => \$OutPadCompensating ,-width => 3,) )->g_pack(-side=>'left',);
		($SilkBridgeOptFrame->new_ttk__button(-text => "字符桥优化",-width=> 8,-command => sub {$mw->g_wm_withdraw;&SilkBridgeOptButtonAct('InnRun');$mw->g_destroy; },) )->g_pack(-side=>'top',-fill=>'x',-expand => '1',);
	}
	Tkx::MainLoop;
}

sub RunScriptAct {
	my $ScripFile = shift;
	my @tParams = @_;
	our $tThread;
	system("python /incam/server/site_data/scripts/lyh/messageBox.py $MainConfig{GetDisplay}   "."%${CURRENTPIDNUM}\@hdilinux55.hdilinux55:30 $ScripFile @tParams");
	$tThread = threads->create( sub {
		#system($MainConfig{GatewayPath},$MainConfig{GetDisplay},"COM script_run,name=$CurrScriptFile,env1=JOB=$ShareJob,env2=STEP=$ShareStep,params=\"");
		system($MainConfig{GatewayPath},$MainConfig{GetDisplay},"COM script_run,name=$ScripFile,env1=JOB=$ShareJob,env2=STEP=$ShareStep,params=@tParams");
#		system("python /incam/server/site_data/scripts/lyh/messageBox.py $MainConfig{GetDisplay}   "."%${CURRENTPIDNUM}\@hdilinux55.hdilinux55:30 $ScripFile");
	} );

}

sub InnRunScriptAct {
	my $ScripFile = shift;
	my @tParams = @_;
	$f->COM('script_run' ,name => $ScripFile ,env1 => "JOB=$JOB" ,env2 => "STEP=$STEP" ,params => "@tParams" ,);
}

sub SilkScreenCoverLayerCreate {	#创建套层
	#&RunScriptAct($MyScriptFile,'SilkScreenCoverLayerCreate',$SilkScreenToSolderMask,$SilkScreenToSmdBga,$CoverLayerSuffix,$TmpSilkSelLayerLists);
	my $RunSubScr = shift;
	my $SilkScreenToSolderMask = shift;
	my $SilkScreenToSmdBga = shift;
	my $CoverLayerSuffix = shift;
	my @SilkSelLayerLists = split ('@',"@_");

	&GetJobStep;
	my %JobMatrix = &JobMatrixDispose($JOB);

	for my $tLayer (@SilkSelLayerLists){
		my $SSCoverLayer = $tLayer . $CoverLayerSuffix;
		my $SmLayer = $JobMatrix{SumData}{TopSolderMask}[ scalar(@{$JobMatrix{SumData}{TopSolderMask}}) - 1 ];
		my $OutLayer = $JobMatrix{SumData}{Outer}[0];
		if ( defined $JobMatrix{"LayersData"}{$tLayer}{'BottomSilkScreenLayer'} ) {
			$SmLayer = $JobMatrix{"SumData"}{"BottomSolderMask"}[0];
			$OutLayer = $JobMatrix{SumData}{Outer}[ scalar( @{$JobMatrix{SumData}{Outer}} ) - 1 ];
		}

		&DelLayers($SSCoverLayer);
		$f->VOF;
		$f->COM('create_layer', layer => $SSCoverLayer, context => 'board', type => 'document', polarity => 'positive');
		$f->COM('create_layer', layer => $SSCoverLayer,type => 'document', );
		$f->VON;
		$f->COM('units', type => 'inch');
		$f->COM('clear_layers');
		$f->COM('affected_layer', name => '', mode => 'all', affected => 'no');

		$f->COM('affected_layer', name => $SmLayer, mode => 'single', affected => 'yes');
#		$f->COM('adv_filter_reset');
		$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');

		$f->COM('set_filter_polarity', filter_name => '', positive => 'yes', negative => 'no');
		$f->COM('filter_area_strt');
		$f->COM('filter_area_end', filter_name => 'popup', operation => 'select');

		$f->COM('get_select_count');
		if ( $f->{COMANS} != 0 ) {
			$f->COM('sel_copy_other', dest => 'layer_name', target_layer => $SSCoverLayer, invert => 'no', dx => 0, dy => 0, size => $SilkScreenToSolderMask * 2, x_anchor => 0, y_anchor => 0);
		}
		$f->COM('affected_layer', name => $SmLayer, mode => 'single', affected => 'no');

		$f->COM('affected_layer', name => $OutLayer, mode => 'single', affected => 'yes');

		$f->COM('reset_filter_criteria', filter_name => 'popup', criteria => 'inc_attr');
		$f->COM('set_filter_attributes', filter_name => 'popup', exclude_attributes => 'no', condition => 'no', attribute => '.bga', min_int_val => 0, max_int_val => 0, min_float_val => 0, max_float_val => 0, option => '', text => '');
		$f->COM('set_filter_attributes', filter_name => 'popup', exclude_attributes => 'no', condition => 'no', attribute => '.smd', min_int_val => 0, max_int_val => 0, min_float_val => 0, max_float_val => 0, option => '', text => '');
		$f->COM('set_filter_and_or_logic', filter_name => 'popup', criteria => 'inc_attr', logic => 'or');
		$f->COM('filter_area_strt');
		$f->COM('filter_area_end', filter_name => 'popup', operation => 'select');

		$f->COM('get_select_count');
		if ( $f->{COMANS} != 0 ) {
			$f->COM('sel_copy_other', dest => 'layer_name', target_layer => $SSCoverLayer, invert => 'no', dx => 0, dy => 0, size => $SilkScreenToSmdBga * 2, x_anchor => 0, y_anchor => 0);
		}
		$f->COM('affected_layer', name => $OutLayer, mode => 'single', affected => 'no');

		$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$tLayer",data_type => 'ROW');
		my $SSRow = $f->{doinfo}{gROW};
		if ( defined $JobMatrix{"LayersData"}{$tLayer}{'BottomSilkScreenLayer'} ) {
			$SSRow = $f->{doinfo}{gROW} + 1;
		}
		$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$SSCoverLayer",data_type => 'ROW');
		my $SSCoverLayerRow = $f->{doinfo}{gROW};
		$f->COM('matrix_move_row', job => $JOB, matrix => 'matrix', row => $SSCoverLayerRow, ins_row => $SSRow);

	}
#	$f->COM('adv_filter_reset');
	$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
	
	#检测有smd属性 没有开窗的pad 20221111 by lyh
	system("python $ENV{INCAM_SITE_DATA_DIR}/scripts/lyh/sh_hdi_check_rules.py check_smd_clip_silk_layer $STEP");
	&MsgBox("脚本已运行Ok","info","ok","文字套层已创建,请检查!",);
	
	# my $OutLineLayer = 'out' ;
	# $f->INFO(entity_type => 'layer',entity_path => "$JOB/$STEP/$OutLineLayer",data_type => 'EXISTS');
	# if ( $f->{doinfo}{gEXISTS} eq 'yes' ) {
		# my $tmpOutLineLayer = $OutLineLayer . 'tmp++' ;
		# &DelLayers($tmpOutLineLayer);
		# $f->COM('affected_layer' ,name => $OutLineLayer ,mode => 'single' ,affected => 'yes' ,);
		# $f->COM('sel_copy_other' ,dest => 'layer_name' ,target_layer => $tmpOutLineLayer ,invert => 'no' ,dx => 0 ,dy => 0 ,size => 0 ,x_anchor => 0 ,y_anchor => 0 ,);
		# $f->COM('affected_layer' ,name => $OutLineLayer ,mode => 'single' ,affected => 'no' ,);
		# $f->COM('affected_layer' ,name => $tmpOutLineLayer ,mode => 'single' ,affected => 'yes' ,);
		# $f->COM('sel_multi_feat' ,operation => 'select' ,feat_types => 'arc' ,include_syms => '' ,is_extended => 'no' ,clear_prev => 'no' ,);
		# $f->COM('sel_multi_feat' ,operation => 'select' ,feat_types => 'line' ,include_syms => '' ,is_extended => 'no' ,clear_prev => 'no' ,);
		# $f->COM('get_select_count');
		# if ( $f->{COMANS} != 0 ) {
			# $f->COM('sel_change_sym' ,symbol => 'r16' ,reset_angle => 'no' ,);
		# }
		# for my $tLayer ( @SilkSelLayerLists ) {
			# my $SSCoverLayer = $tLayer . $CoverLayerSuffix;
			# $f->COM('sel_copy_other' ,dest => 'layer_name' ,target_layer => $SSCoverLayer ,invert => 'no' ,dx => 0 ,dy => 0 ,size => 0 ,x_anchor => 0 ,y_anchor => 0 ,);
		# }
		# &DelLayers($tmpOutLineLayer);
		# &MsgBox("脚本已运行Ok","info","ok","文字套层已创建,请检查!",);
	# } else {
		# &MsgBox($OutLineLayer . '层不存在','warning','ok',$OutLineLayer . '层不存在,请手动在套层中添加外形.',);
	# }

	exit;
}

sub ChangeSilkMinLineWidth {  #修改字符最小线宽
	my $RunSubScr = shift;
	my $SilkMinLineWidth = shift;
	my @SilkSelLayerLists = split ('@',"@_");

	my $SelLineText = 'r0:r' . $SilkMinLineWidth;
#	$f->COM('clear_layers');
#	$f->COM('affected_layer', mode => 'all', affected => 'no');

	$f->COM('units', type => 'inch');
	for my $tLayer ( @SilkSelLayerLists ){
		$f->COM('clear_layers');
		$f->COM('affected_layer', mode => 'all', affected => 'no');
		#
		$f->COM('display_layer', name => $tLayer, display => 'yes');
		#
		$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
		$f->COM('set_filter_type', filter_name => '', lines => 'yes', pads => 'no', surfaces => 'no', arcs => 'yes', text => 'no');
		$f->COM('set_filter_polarity', filter_name => '', positive => 'yes', negative => 'no');
		$f->COM('set_filter_symbols', filter_name => '', exclude_symbols => 'no', symbols => $SelLineText);
		$f->COM('filter_area_strt');
		$f->COM('filter_area_end', filter_name => 'popup', operation => 'select');
		$f->COM('get_select_count');
		if ($f->{COMANS} != 0 ) {
			$f->COM('zoom_home');
			$f->PAUSE("请确认选择的物件是否正确.");
			$f->COM('get_select_count');
			my $tSelNum = $f->{COMANS};
			while ( $tSelNum == 0 ) {
				$->PAUSE("没有选择物件,请选择后再点击此处.");
				$f->COM('get_select_count');
				$tSelNum = $f->{COMANS};
			}
			$f->COM('affected_layer', mode => 'all', affected => 'no');
			$f->COM('units', type => 'inch');
			$f->COM('sel_change_sym', symbol => 'r'.$SilkMinLineWidth, reset_angle => 'no');
		}
	}

	$f->COM('clear_layers');
	$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');

}

sub TextAndTextBoxSeparated {  #字框分离
	my $RunSubScr = shift;
	my $TextSeparatedTextMaxHeight = shift;
	my $TextSeparatedLayerSuffix = shift;
	my $CoverLayerSuffix = shift;
	my @SilkSelLayerLists = split ('@',"@_");

	$f->COM('clear_layers');
	$f->COM('affected_layer', name => '', mode => 'all', affected => 'no');
	&GetJobStep;
	my $RepairLineWidth = 10;
	for my $tLayer (@SilkSelLayerLists){
		my $SSCoverLayer = $tLayer . $CoverLayerSuffix;
		my $TmpSSCoverLayer = $SSCoverLayer . '++';
#		my $TextSeparatedLayer = $tLayer . '-text+';
		my $TextSeparatedLayer = $tLayer . $TextSeparatedLayerSuffix;
		my $tLineArcLayer = $tLayer . '-line_arc++';
		my $tLineLayer = $tLayer . '-line++';
		my $TmpLayer1 = $tLayer . '-tmp1+';
		my $TmpLayer2 = $tLayer . '-tmp2+';
		$f->INFO(entity_type => 'layer',entity_path => "$JOB/$STEP/$SSCoverLayer",data_type => 'EXISTS');
		if ( $f->{doinfo}{gEXISTS} eq 'no' ) {
			&MsgBox("$SSCoverLayer 不存在","warning","ok","文字套层 $SSCoverLayer 不存在,脚本退出！",);
			exit;
		} else {
			&DelLayers($TmpSSCoverLayer,$tLineArcLayer,$tLineLayer,$TmpLayer1,$TmpLayer2,);
			$f->COM('sel_options', clear_mode => 'clear_after', display_mode => 'displayed_layers', area_inout => 'inside', area_select => 'select', select_mode => 'standard', area_touching_mode => 'exclude');

			$f->COM('copy_layer', source_job => $JOB, source_step => $STEP, source_layer => $tLayer, dest => 'layer_name', dest_layer => $tLayer . '-bak++', mode => 'replace', invert => 'no');
			#创建层别
			$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$TextSeparatedLayer",data_type => 'EXISTS');
			if ( $f->{doinfo}{gEXISTS} eq 'no' ) {
				$f->VOF;
				$f->COM('create_layer', layer => $TextSeparatedLayer, context => 'board', type => 'document', polarity => 'positive');
				$f->COM('create_layer', layer => $TextSeparatedLayer,type => 'document',);
				$f->VON;
				$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$tLayer",data_type => 'ROW');
				my $tLayerRow = $f->{doinfo}{gROW};
				$f->INFO(entity_type => 'layer',entity_path => "$JOB/$STEP/$tLayer",data_type => 'SIDE');
				if ( $f->{doinfo}{gSIDE} eq 'bottom' ) {
					$tLayerRow = $f->{doinfo}{gROW} + 1;
				}
				$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$TextSeparatedLayer",data_type => 'ROW');
				my $TextSeparatedLayerRow = $f->{doinfo}{gROW};
				$f->COM('matrix_move_row', job => $JOB, matrix => 'matrix', row => $TextSeparatedLayerRow, ins_row => $tLayerRow);
			}

			$f->COM('units', type => 'inch');
			#
			$f->COM('affected_layer', name => $tLayer, mode => 'single', affected => 'yes');
			$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
			$f->COM('set_filter_type', filter_name => '', lines => 'yes', pads => 'no', surfaces => 'no', arcs => 'yes', text => 'no');
			$f->COM('set_filter_polarity', filter_name => '', positive => 'yes', negative => 'no');
			$f->COM('filter_area_strt');
			$f->COM('filter_area_end', filter_name => 'popup', operation => 'select');
			$f->COM('get_select_count');
			if ($f->{COMANS} != 0 ) {
				$f->COM('sel_copy_other', dest => 'layer_name', target_layer => $tLineArcLayer, invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0);
			} else {
				&MsgBox("不存在线","warning","ok","文字层不存在线,脚本退出!",);
				exit;
			}
			$f->COM('affected_layer', name => $tLayer, mode => 'single', affected => 'no');
			#
			$f->COM('affected_layer', name => $tLineArcLayer, mode => 'single', affected => 'yes');
			my $ChangeLineSize = 0.2;
#			my $ChangeLineSize = 2;
#			my $ChangeLineSize = 1;
			$f->COM('sel_change_sym', symbol => 'r' . $ChangeLineSize, reset_angle => 'no');

			$f->COM('set_filter_type', filter_name => '', lines => 'yes', pads => 'no', surfaces => 'no', arcs => 'no', text => 'no');
			$f->COM('filter_area_strt');
			$f->COM('filter_area_end', filter_name => 'popup', operation => 'select');
			$f->COM('get_select_count');
			if ($f->{COMANS} != 0 ) {
				$f->COM('sel_copy_other', dest => 'layer_name', target_layer => $tLineLayer, invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0);
			} else {
				&MsgBox("不存在线","warning","ok","文字层不存在线,脚本退出!",);
				exit;
			}
			$f->COM('affected_layer', name => $tLineArcLayer, mode => 'single', affected => 'no');

			#
			$f->COM('affected_layer', name => $tLineLayer, mode => 'single', affected => 'yes');
			#$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
			for my $tNum ( 0 .. 7 ){#循环0-360之间的 45°跨度 # 45°的也区分长短判断
				my $tAngle = 45 * $tNum;
#				$f->COM('set_filter_length');
				$f->COM('set_filter_angle', slot => 'lines', min_angle => $tAngle, max_angle => $tAngle, direction => 'ccw');
#				$f->COM('adv_filter_reset');
				$f->COM('adv_filter_set', filter_name => 'popup', active => 'yes', limit_box => 'no', bound_box => 'no', srf_values => 'no', srf_area => 'no', mirror => 'any', ccw_rotations => '');
				$f->COM('filter_area_strt');
				$f->COM('filter_area_end', filter_name => 'popup', operation => 'select');
			}

			$f->COM('get_select_count');
			if ($f->{COMANS} != 0 ) {
				$f->COM('sel_delete');
			}
			$f->COM('affected_layer', name => $tLineLayer, mode => 'single', affected => 'no');

			$f->COM('affected_layer', name => $SSCoverLayer, mode => 'single', affected => 'yes');

			$f->COM('filter_reset', filter_name => 'popup');
			$f->COM('filter_set', filter_name => 'popup', update_popup => 'no', include_syms => 'r*');
			$f->COM('filter_set', filter_name => 'popup', update_popup => 'no', exclude_syms => 'rect*');
			$f->COM('filter_area_strt');
			$f->COM('filter_area_end', layer => '', filter_name => 'popup', operation => 'select', area_type => 'none', inside_area => 'no', intersect_area => 'no');
			$f->COM('filter_reset', filter_name => 'popup');
			$f->COM('sel_reverse');
			$f->COM('get_select_count');
			if ($f->{COMANS} != 0 ) {
				#套层$SSCoverLayer加大10mil
				$f->COM('sel_copy_other', dest => 'layer_name', target_layer => $TmpSSCoverLayer, invert => 'no', dx => 0, dy => 0, size => $RepairLineWidth, x_anchor => 0, y_anchor => 0);
			}

			$f->COM('affected_layer', name => $SSCoverLayer, mode => 'single', affected => 'no');

			#$TmpLayer1 是字符的;   $TmpLayer2 为$tLineArcLayer (剩余不能判断的字)的备份层
			$f->COM('affected_layer', name => $tLineArcLayer, mode => 'single', affected => 'yes');
			$f->COM('sel_contourize', accuracy => 0, break_to_islands => 'yes', clean_hole_size => 0, clean_hole_mode => 'x_or_y');
			$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
			$f->COM('sel_ref_feat', layers => $tLineLayer, use => 'filter', mode => 'touch', pads_as => 'shape', f_types => 'line;pad;surface;arc;text', polarity => 'positive;negative', include_syms => '', exclude_syms => '');
			$f->COM('get_select_count');
			if ($f->{COMANS} != 0 ) {
				$f->COM('sel_move_other', target_layer => $TmpLayer1, invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0);
			}
			#TmpSSCoverLayer
			$f->COM('sel_ref_feat', layers => $TmpSSCoverLayer, use => 'filter', mode => 'touch', pads_as => 'shape', f_types => 'line;pad;surface;arc;text', polarity => 'positive;negative', include_syms => '', exclude_syms => '');
			$f->COM('get_select_count');
			if ($f->{COMANS} != 0 ) {
				$f->COM('sel_delete');
			}
			$f->COM('sel_copy_other', dest => 'layer_name', target_layer => $TmpLayer2, invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0);
			#
			$f->COM('sel_clean_surface', accuracy => 0, clean_size => $TextSeparatedTextMaxHeight, clean_mode => 'x_and_y', max_fold_len => 0);
			$f->COM('affected_layer', name => $tLineArcLayer, mode => 'single', affected => 'no');
			$f->COM('affected_layer', name => $TmpLayer2, mode => 'single', affected => 'yes');
			$f->COM('sel_ref_feat', layers => $tLineArcLayer, use => 'filter', mode => 'disjoint', pads_as => 'shape', f_types => 'line;pad;surface;arc;text', polarity => 'positive;negative', include_syms => '', exclude_syms => '');
			$f->COM('get_select_count');
			if ($f->{COMANS} != 0 ) {
				$f->COM('sel_move_other', target_layer => $TmpLayer1, invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0);
			}
			$f->COM('affected_layer', name => $TmpLayer2, mode => 'single', affected => 'no');
			$f->COM('affected_layer', name => $TmpLayer1, mode => 'single', affected => 'yes');
			$f->COM('sel_ref_feat', layers => $tLayer, use => 'filter', mode => 'touch', pads_as => 'shape', f_types => 'line;pad;surface;arc;text', polarity => 'negative', include_syms => '', exclude_syms => '');
			$f->COM('sel_ref_feat', layers => $tLayer, use => 'filter', mode => 'touch', pads_as => 'shape', f_types => 'pad;surface;text', polarity => 'positive', include_syms => '', exclude_syms => '');
			$f->COM('get_select_count');
			if ($f->{COMANS} != 0 ) {
				$f->COM('sel_delete');
			}
			$f->COM('affected_layer', name => $TmpLayer1, mode => 'single', affected => 'no');

			$f->COM('affected_layer', name => $tLayer, mode => 'single', affected => 'yes');
			$f->COM('sel_ref_feat', layers => $TmpLayer1, use => 'filter', mode => 'touch', pads_as => 'shape', f_types => 'line;pad;surface;arc;text', polarity => 'positive;negative', include_syms => '', exclude_syms => '');
			$f->COM('get_select_count');
			if ($f->{COMANS} != 0 ) {
				$f->COM('sel_move_other', target_layer => $TextSeparatedLayer, invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0);
			}
			$f->COM('affected_layer', name => $tLayer, mode => 'single', affected => 'no');
			$f->COM('sel_options', clear_mode => 'clear_after', display_mode => 'all_layers', area_inout => 'inside', area_select => 'select', select_mode => 'standard', area_touching_mode => 'exclude');

			&DelLayers($TmpSSCoverLayer,$tLineArcLayer,$tLineLayer,$TmpLayer1,$TmpLayer2,);
		}
	}
	&MsgBox("脚本已运行Ok","info","ok","字框分离 脚本已运行Ok,请检查!",);
	exit;
}

sub AllAutoWordBoxZoom {  #全自动缩放文字框
#	&RunScriptAct($MyScriptFile,'Run:AllAutoWordBoxZoom',$CoverLayerSuffix,$TextBoxLengthMin,$TextBoxLengthMax,$VarDataStorage{TextBoxSubAutoType}{BoxRectangle},$VarDataStorage{TextBoxSubAutoType}{BoxOpenRectangle},$SpokesGap,);
#	&RunScriptAct($MyScriptFile,'Run:AllAutoWordBoxZoom',$CoverLayerSuffix,$TextBoxLengthMin,$TextBoxLengthMax,$TextBoxWidthMax,$VarDataStorage{TextBoxSubAutoType}{BoxRings},$VarDataStorage{TextBoxSubAutoType}{BoxRectangle},$VarDataStorage{TextBoxSubAutoType}{BoxOpenRectangle},$SpokesGap,);

	my $RunSubScr = shift;
	my ($CoverLayerSuffix,$TextBoxLengthMin,$TextBoxLengthMax,$TextBoxWidthMax,$BoxRingsJud,$BoxRectangleJud,$BoxOpenRectangleJud,$SpokesGap,) = (@_);
#	$f->PAUSE("@_");
#	my $ExtendLineSize = $SpokesGap + 7;
#	my $TextBoxLengthMin = 20;
#	my $TextBoxLengthMax = 160;

	#还要删除外围线
	my $TmpWordBoxSy = 'neo_silk-tmp+';
	#工作层
	$f->COM('get_work_layer');
	my $WorkLayer = $f->{COMANS};
	if ( $WorkLayer eq '' ) {
		&MsgBox("没有工作层","warning","ok","没有工作层,脚本退出",);
		exit;
	}

	&GetJobStep;
	my $WorkCoverLayer = $WorkLayer . $CoverLayerSuffix;
	$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$WorkCoverLayer",data_type => 'EXISTS');
	if ( $f->{doinfo}{gEXISTS} eq 'no' ) {
		&MsgBox("套层不存在","warning","ok","套层 $WorkCoverLayer 不存在,脚本退出",);
		exit;
	}

	my $WorkOkSuffix = '-ok+';
	my $WorkOkLayer = $WorkLayer . $WorkOkSuffix;
	$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$WorkOkLayer",data_type => 'EXISTS');
	if ( $f->{doinfo}{gEXISTS} eq 'no' ) {
		$f->VOF;
		$f->COM('create_layer', layer => $WorkOkLayer, context => 'board', type => 'document', polarity => 'positive');
		$f->COM('create_layer', layer => $WorkOkLayer, type => 'document',);
		$f->VON;
		$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$WorkLayer",data_type => 'ROW');
		my $WorkLayerRow = $f->{doinfo}{gROW};
		$f->INFO(entity_type => 'layer',entity_path => "$JOB/$STEP/$WorkLayer",data_type => 'SIDE');
      if ( $f->{doinfo}{gSIDE} eq 'bottom' ) {
			$WorkLayerRow = $f->{doinfo}{gROW} + 1;
      }
		$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$WorkOkLayer",data_type => 'ROW');
		my $WorkOkLayerRow = $f->{doinfo}{gROW};
		$f->COM('matrix_move_row', job => $JOB, matrix => 'matrix', row => $WorkOkLayerRow, ins_row => $WorkLayerRow);
	}
	my $BoxSelTol = 0.001;#框选套层公差

	$f->COM('copy_layer', source_job => $JOB, source_step => $STEP, source_layer => $WorkLayer, dest => 'layer_name', dest_layer => $WorkLayer . '-bak+', mode => 'replace', invert => 'no');

#	my $WorkLayer = "c1";
#	my @TmpLayers = ($WorkLayer . '-t1+',$WorkLayer . '-t2+',$WorkLayer . '-s1+',$WorkLayer . '-s2+',$WorkLayer . '-index+',$WorkLayer . '-out+',);
	my ($TmpLayerT1,$TmpLayerT2,$TmpLayerS1,$TmpLayerS2,$TmpLayerIndex,$TmpLayerOut,$TmpLayerS3,$TmpLayerT3,$TmpLayerHole) =
	($WorkLayer . '-t1+',$WorkLayer . '-t2+',$WorkLayer . '-s1+',$WorkLayer . '-s2+',$WorkLayer . '-index+',$WorkLayer . '-out+',$WorkLayer . '-s3+',$WorkLayer . '-t3+',$WorkLayer . '-hole+',);
	#my $TmpLayerT1 = "t1";
	#my $TmpLayerT2 = "t2";
	#my $TmpLayerS1 = "s1";
	#my $TmpLayerS2 = "s2";
	my $ExtendLineSize = $SpokesGap + $TextBoxWidthMax + 0.5;
#	my $WorkCoverLayer = 'm1';
#	my $TextBoxLengthMin = 20;
	#my $TextBoxLengthMax = 200;
#	my $TextBoxLengthMax = 160;


	$f->COM('clear_layers');
	$f->COM('affected_layer', name => '', mode => 'all', affected => 'no');
	$f->COM('units', type => 'inch');
	&DelLayers($TmpLayerT1,$TmpLayerT1 . '+++',$TmpLayerT2,$TmpLayerS1,$TmpLayerS1 . '+++',$TmpLayerS2,$TmpLayerIndex,);

	$f->COM('sel_options', clear_mode => 'clear_after', display_mode => 'displayed_layers', area_inout => 'inside', area_select => 'select', select_mode => 'standard', area_touching_mode => 'exclude');

	$f->COM('affected_layer', name => $WorkLayer, mode => 'single', affected => 'yes');
	#选线
	$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
	$f->COM('set_filter_type', filter_name => '', lines => 'yes', pads => 'no', surfaces => 'no', arcs => 'yes', text => 'no');
	$f->COM('set_filter_polarity', filter_name => '', positive => 'yes', negative => 'no');
	$f->COM('filter_area_strt');
	$f->COM('filter_area_end', filter_name => 'popup', operation => 'select');
	$f->COM('get_select_count');
	if ($f->{COMANS} != 0 ) {
		#复制临时层
		$f->COM('sel_copy_other', dest => 'layer_name', target_layer => $TmpLayerT1, invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0);
	}
	$f->COM('affected_layer', name => $WorkLayer, mode => 'single', affected => 'no');
	#
	$f->COM('profile_to_rout', layer => $TmpLayerOut, width => 1);
	$f->COM('affected_layer', name => $TmpLayerT1, mode => 'single', affected => 'yes');
#	$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
#	$f->COM('sel_ref_feat', layers => $TmpLayerOut, use => 'filter', mode => 'include', pads_as => 'shape', f_types => 'line;pad;surface;arc;text', polarity => 'positive;negative', include_syms => '', exclude_syms => '');
	$f->COM('sel_ref_feat', layers => $TmpLayerOut, use => 'filter', mode => 'touch', pads_as => 'shape', f_types => 'line;pad;surface;arc;text', polarity => 'positive;negative', include_syms => '', exclude_syms => '');
	$f->COM('get_select_count');
	if ($f->{COMANS} != 0 ) {
		$f->COM('sel_delete');
	}
#	$f->PAUSE(dh);
	#转铜
#	$f->COM('rv_tab_empty', report => 'cut_data_rep', is_empty => 'yes');
#	$f->COM('sel_cut_data', det_tol => 1, con_tol => 1, rad_tol => '0.1', ignore_width => 'yes', filter_overlaps => 'no', delete_doubles => 'no', use_order => 'yes', ignore_holes => 'none', start_positive => 'yes', polarity_of_touching => 'same', contourize => 'yes', simplify => 'yes', resize_thick_lines => 'no');
#	$f->COM('rv_tab_view_results_enabled', report => 'cut_data_rep', is_enabled => 'yes', serial_num => -1, all_count => -1);
#	$f->COM('rv_tab_empty', report => 'cut_data_rep', is_empty => 'yes');
#	$f->COM('sel_cut_data', det_tol => 1, con_tol => 1, rad_tol => '0.1', ignore_width => 'yes', filter_overlaps => 'no', delete_doubles => 'no', use_order => 'yes', ignore_holes => 'none', start_positive => 'yes', polarity_of_touching => 'same', contourize => 'no', simplify => 'yes', resize_thick_lines => 'no');
#	$f->COM('sel_cut_data', det_tol => 1, con_tol => 1, rad_tol => '0.1', ignore_width => 'no', filter_overlaps => 'no', delete_doubles => 'no', use_order => 'yes', ignore_holes => 'none', start_positive => 'yes', polarity_of_touching => 'same', contourize => 'no', simplify => 'yes', resize_thick_lines => 'no');
#	$f->COM('rv_tab_view_results_enabled', report => 'cut_data_rep', is_enabled => 'yes', serial_num => -1, all_count => -1);

$f->COM('rv_tab_empty', report => 'cut_data_rep', is_empty => 'yes');
$f->COM('sel_cut_data', det_tol => 1, con_tol => 1, rad_tol => '0.1', ignore_width => 'yes', filter_overlaps => 'no', delete_doubles => 'no', use_order => 'yes', ignore_holes => 'none', start_positive => 'yes', polarity_of_touching => 'same', contourize => 'no', simplify => 'yes', resize_thick_lines => 'no');
#$f->COM('sel_cut_data', det_tol => 1, con_tol => 1, rad_tol => '0.1', ignore_width => 'no', filter_overlaps => 'no', delete_doubles => 'no', use_order => 'yes', ignore_holes => 'none', start_positive => 'yes', polarity_of_touching => 'same', contourize => 'no', simplify => 'yes', resize_thick_lines => 'no');
$f->COM('rv_tab_view_results_enabled', report => 'cut_data_rep', is_enabled => 'yes', serial_num => -1, all_count => -1);

$f->COM('rv_tab_empty', report => 'cut_data_rep', is_empty => 'yes');
$f->COM('sel_cut_data', det_tol => 1, con_tol => 1, rad_tol => '0.1', ignore_width => 'yes', filter_overlaps => 'no', delete_doubles => 'no', use_order => 'yes', ignore_holes => 'none', start_positive => 'yes', polarity_of_touching => 'same', contourize => 'no', simplify => 'yes', resize_thick_lines => 'no');
#$f->COM('sel_cut_data', det_tol => 1, con_tol => 1, rad_tol => '0.1', ignore_width => 'no', filter_overlaps => 'no', delete_doubles => 'no', use_order => 'yes', ignore_holes => 'none', start_positive => 'yes', polarity_of_touching => 'same', contourize => 'no', simplify => 'yes', resize_thick_lines => 'no');
$f->COM('rv_tab_view_results_enabled', report => 'cut_data_rep', is_enabled => 'yes', serial_num => -1, all_count => -1);

	#要删除+++层
#	$f->COM('set_filter_type', filter_name => '', lines => 'no', pads => 'no', surfaces => 'yes', arcs => 'no', text => 'no');
#	$f->COM('filter_area_strt');
#	$f->COM('filter_area_end', filter_name => 'popup', operation => 'select');
	$f->COM('sel_multi_feat', operation => 'select', feat_types => 'surface', include_syms => '', is_extended => 'no', clear_prev => 'yes');
#		$f->PAUSE(111);

	$f->COM('get_select_count');
	if ($f->{COMANS} != 0 ) {
		#将铜移到另一层
		$f->COM('sel_move_other', target_layer => $TmpLayerS1, invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0);
	}

	if ( $BoxOpenRectangleJud == 1 ) {
		my $TmpExistsS2 = 'no';
		#备份层别
		$f->COM('sel_copy_other', dest => 'layer_name', target_layer => $TmpLayerT2, invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0);
		#线拉长
		$f->COM('sel_extend_slots', mode => 'ext_by', size => $ExtendLineSize, from => 'center');
		#整线
		$f->COM('rv_tab_empty', report => 'design2rout_rep', is_empty => 'yes');
		$f->COM('sel_design2rout', det_tol => 1, con_tol => 1, rad_tol => '0.1');
		$f->COM('rv_tab_view_results_enabled', report => 'design2rout_rep', is_enabled => 'yes', serial_num => -1, all_count => -1);
		#线缩回原来
		$f->COM('sel_extend_slots', mode => 'ext_by', size => '-' . $ExtendLineSize, from => 'center');
		#转铜
		$f->VOF;
		$f->COM('rv_tab_empty', report => 'cut_data_rep', is_empty => 'yes');
		$f->COM('sel_cut_data', det_tol => 1, con_tol => 1, rad_tol => '0.1', ignore_width => 'yes', filter_overlaps => 'no', delete_doubles => 'no', use_order => 'yes', ignore_holes => 'none', start_positive => 'yes', polarity_of_touching => 'same', contourize => 'no', simplify => 'yes', resize_thick_lines => 'no');
#		$f->COM('sel_cut_data', det_tol => 1, con_tol => 1, rad_tol => '0.1', ignore_width => 'no', filter_overlaps => 'no', delete_doubles => 'no', use_order => 'yes', ignore_holes => 'none', start_positive => 'yes', polarity_of_touching => 'same', contourize => 'no', simplify => 'yes', resize_thick_lines => 'no');
		$f->COM('rv_tab_view_results_enabled', report => 'cut_data_rep', is_enabled => 'yes', serial_num => -1, all_count => -1);
		$f->VON;

#		$f->COM('rv_tab_empty', report => 'cut_data_rep', is_empty => 'yes');
#		$f->COM('sel_cut_data', det_tol => 1, con_tol => 1, rad_tol => '0.1', ignore_width => 'yes', filter_overlaps => 'no', delete_doubles => 'no', use_order => 'yes', ignore_holes => 'none', start_positive => 'yes', polarity_of_touching => 'same', contourize => 'no', simplify => 'yes', resize_thick_lines => 'no');
#		$f->COM('rv_tab_view_results_enabled', report => 'cut_data_rep', is_enabled => 'yes', serial_num => -1, all_count => -1);

#		$f->COM('rv_tab_empty', report => 'cut_data_rep', is_empty => 'yes');
#		$f->COM('sel_cut_data', det_tol => 1, con_tol => 1, rad_tol => '0.1', ignore_width => 'yes', filter_overlaps => 'no', delete_doubles => 'no', use_order => 'yes', ignore_holes => 'none', start_positive => 'yes', polarity_of_touching => 'same', contourize => 'no', simplify => 'yes', resize_thick_lines => 'no');
#		$f->COM('rv_tab_view_results_enabled', report => 'cut_data_rep', is_enabled => 'yes', serial_num => -1, all_count => -1);
		#移到另一层

		$f->COM('set_filter_type', filter_name => '', lines => 'no', pads => 'no', surfaces => 'yes', arcs => 'no', text => 'no');
		$f->COM('set_filter_polarity', filter_name => '', positive => 'yes', negative => 'no');
		$f->COM('filter_area_strt');
		$f->COM('filter_area_end', filter_name => 'popup', operation => 'select');

#		$f->COM('sel_multi_feat', operation => 'select', feat_types => 'surface', include_syms => '', is_extended => 'no', clear_prev => 'yes');
#				$f->PAUSE(122);

		$f->COM('get_select_count');
		if ($f->{COMANS} != 0 ) {
			$TmpExistsS2 = 'yes';
			$f->COM('sel_move_other', target_layer => $TmpLayerS2, invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0);

			$f->COM('sel_options', clear_mode => 'clear_none', display_mode => 'displayed_layers', area_inout => 'inside', area_select => 'select', select_mode => 'standard', area_touching_mode => 'exclude');
			#接触到的线和弧
			$f->COM('set_filter_type', filter_name => '', lines => 'yes', pads => 'no', surfaces => 'no', arcs => 'yes', text => 'no');
		#	$f->COM('filter_area_strt');
		#	$f->COM('filter_area_end', filter_name => 'popup', operation => 'select');
			$f->COM('sel_ref_feat', layers => $TmpLayerS2, use => 'filter', mode => 'touch', pads_as => 'shape', f_types => 'line;pad;surface;arc;text', polarity => 'positive;negative', include_syms => '', exclude_syms => '');
			$f->COM('get_select_count');
			if ($f->{COMANS} != 0 ) {
				#修改大小
				$f->COM('sel_change_sym', symbol => 'r0.2', reset_angle => 'no');
				#拉长一点
				$f->COM('sel_extend_slots', mode => 'ext_by', size => 2, from => 'center');
				#套过去
				$f->COM('sel_move_other', target_layer => $TmpLayerS2, invert => 'yes', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0);
			}
			$f->COM('affected_layer', name => $TmpLayerT1, mode => 'single', affected => 'no');
			#将备份层改大小
			$f->COM('affected_layer', name => $TmpLayerT2, mode => 'single', affected => 'yes');
	#		$f->COM('sel_change_sym', symbol => 'r0.5', reset_angle => 'no');
			$f->COM('sel_change_sym', symbol => 'r0.1', reset_angle => 'no');
			$f->COM('affected_layer', name => $TmpLayerT2, mode => 'single', affected => 'no');
			#将正负片合并
			$f->COM('affected_layer', name => $TmpLayerS2, mode => 'single', affected => 'yes');
			$f->COM('sel_contourize', accuracy => 0, break_to_islands => 'yes', clean_hole_size => 0, clean_hole_mode => 'x_or_y');
			$f->INFO(entity_type => 'layer',entity_path => " $JOB/$STEP/$TmpLayerS2",data_type => 'FEAT_HIST');
#			$f->PAUSE("01=$f->{doinfo}{gFEAT_HISTsurf},$f->{doinfo}{gFEAT_HISTtotal},");

			if ( $f->{doinfo}{gFEAT_HISTsurf} == 1 ) {
#						$f->PAUSE(02);

				$f->COM('sel_decompose', overlap => 'no');
				$f->COM('sel_contourize', accuracy => 0, break_to_islands => 'yes', clean_hole_size => 0, clean_hole_mode => 'x_or_y');
			}
#						$f->PAUSE(03);
			
			#没接触到的铜删除$TmpLayerS2
	#		$f->PAUSE(1);
			$f->COM('set_filter_type', filter_name => '', lines => 'no', pads => 'no', surfaces => 'yes', arcs => 'no', text => 'no');
			$f->COM('sel_ref_feat', layers => $TmpLayerT2, use => 'filter', mode => 'disjoint', pads_as => 'shape', f_types => 'line;pad;surface;arc;text', polarity => 'positive;negative', include_syms => '', exclude_syms => '');
			$f->COM('get_select_count');
			if ($f->{COMANS} != 0 ) {
				$f->COM('sel_delete');
			}

			$f->COM('rv_tab_empty', report => 'resize_rep', is_empty => 'yes');
			$f->COM('sel_resize', size => '0.21', corner_ctl => 'no');
			$f->COM('rv_tab_view_results_enabled', report => 'resize_rep', is_enabled => 'no', serial_num => -1, all_count => -1);

			$f->COM('sel_contourize', accuracy => '0', break_to_islands => 'yes', clean_hole_size => 0, clean_hole_mode => 'x_or_y');

			$f->COM('rv_tab_empty', report => 'resize_rep', is_empty => 'yes');
			$f->COM('sel_resize', size => '-0.01', corner_ctl => 'no');
			$f->COM('rv_tab_view_results_enabled', report => 'resize_rep', is_enabled => 'no', serial_num => -1, all_count => -1);

			$f->COM('sel_move_other', target_layer => $TmpLayerS1, invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0);
			$f->COM('affected_layer', name => $TmpLayerS2, mode => 'single', affected => 'no');
		} else {
			$f->COM('affected_layer', name => $TmpLayerT1, mode => 'single', affected => 'no');
		}
	} else {
		$f->COM('affected_layer', name => $TmpLayerT1, mode => 'single', affected => 'no');
	}

	#没接触到阻焊套层的删除
	$f->COM('affected_layer', name => $TmpLayerS1, mode => 'single', affected => 'yes');
	$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
	$f->COM('sel_ref_feat', layers => $WorkCoverLayer, use => 'filter', mode => 'disjoint', pads_as => 'shape', f_types => 'line;pad;surface', polarity => 'positive', include_syms => '', exclude_syms => '');
	$f->COM('get_select_count');
	if ($f->{COMANS} != 0 ) {
		$f->COM('sel_delete');
	}

#	$f->PAUSE(11);
	##最小字框长度 排除
#	$f->COM('sel_clean_surface', accuracy => '0', clean_size => $TextBoxLengthMin - 0.2, clean_mode => 'x_or_y', max_fold_len => 0);
	$f->COM('sel_clean_surface', accuracy => '0', clean_size => $TextBoxLengthMin - 0.2, clean_mode => 'x_and_y', max_fold_len => 0);
#	$f->PAUSE(2);

	#最大字框长度 排除
	$f->COM('sel_cont2pad', match_tol => 0.1, restriction => '', min_size => 1, max_size => $TextBoxLengthMax, suffix => '+++');
	#要删除+++层
#	$f->PAUSE(3);

	#删除排除的铜
	$f->COM('sel_multi_feat', operation => 'select', feat_types => 'surface', include_syms => '', is_extended => 'no', clear_prev => 'yes');
	$f->COM('get_select_count');
	if ($f->{COMANS} != 0 ) {
		$f->COM('sel_delete');
	}

	$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
	$f->COM('set_filter_polarity', filter_name => '', positive => 'no', negative => 'yes');
	$f->COM('filter_area_strt');
	$f->COM('filter_area_end', filter_name => 'popup', operation => 'select');
	$f->COM('get_select_count');
	if ($f->{COMANS} != 0 ) {

		$f->COM('set_filter_polarity', filter_name => '', positive => 'yes', negative => 'no');
		$f->COM('sel_ref_feat', layers => '', use => 'select', mode => 'touch', pads_as => 'shape', f_types => 'line;pad;surface;arc;text', polarity => 'positive;negative', include_syms => '', exclude_syms => '');
		$f->COM('get_select_count');
		if ($f->{COMANS} != 0 ) {
			$f->COM('sel_delete');
		}

#		$f->COM('filter_area_strt');
#		$f->COM('filter_area_end', filter_name => 'popup', operation => 'select');
#		$f->COM('sel_resize', size => 8 * 2, corner_ctl => 'no');

		$f->COM('sel_polarity', polarity => 'positive');
	}
	$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');


#	$f->PAUSE(4);
#	my $ClearLineMax = 10;
	my $ClearLineMax = $TextBoxLengthMin - 5;
#	$f->COM('sel_copy_other', dest => 'layer_name', target_layer => $TmpLayerS3, invert => 'no', dx => 0, dy => 0, size => '-' . $ClearLineMax, x_anchor => 0, y_anchor => 0);
	$f->COM('sel_copy_other', dest => 'layer_name', target_layer => $TmpLayerS3, invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0);
	$f->COM('affected_layer', name => $TmpLayerS1, mode => 'single', affected => 'no');

	$f->COM('affected_layer', name => $TmpLayerS3, mode => 'single', affected => 'yes');
	$f->COM('sel_contourize', accuracy => 0, break_to_islands => 'yes', clean_hole_size => 0, clean_hole_mode => 'x_or_y');
	$f->COM('sel_resize', size => '-' . $ClearLineMax, corner_ctl => 'no');
	$f->COM('sel_resize', size => $ClearLineMax, corner_ctl => 'no');
	$f->COM('affected_layer', name => $TmpLayerS3, mode => 'single', affected => 'no');

	$f->COM('affected_layer', name => $TmpLayerS1, mode => 'single', affected => 'yes');
	$f->COM('sel_clear_feat');
	$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
	$f->COM('sel_ref_feat', layers => $TmpLayerS3, use => 'filter', mode => 'disjoint', pads_as => 'shape', f_types => 'line;pad;surface;arc;text', polarity => 'positive;negative', include_syms => '', exclude_syms => '');
#	$f->PAUSE(5);

	$f->COM('get_select_count');
	if ($f->{COMANS} != 0 ) {
		$f->COM('sel_delete');
	}

#	$f->COM('sel_resize', size => 8.3, corner_ctl => 'no');
#	$f->PAUSE("TextBoxWidthMax=$TextBoxWidthMax");
	$f->COM('sel_resize', size => $TextBoxWidthMax + 0.3, corner_ctl => 'no');
	$f->COM('affected_layer', name => $TmpLayerS1, mode => 'single', affected => 'no');


#	&DelLayers($TmpLayerT1,$TmpLayerT1 . '+++',$TmpLayerT2,$TmpLayerS1 . '+++',$TmpLayerS2,$TmpLayerIndex,$TmpLayerS3);
#	$f->PAUSE(e0);

	&DelLayers($TmpLayerT1,$TmpLayerT1 . '+++',$TmpLayerT2,$TmpLayerS1 . '+++',$TmpLayerS2,$TmpLayerIndex,$TmpLayerS3,$TmpLayerOut,$TmpLayerT3);
#	$f->PAUSE(e);

	my @TmpLayers2 = ($WorkLayer . '-silk_tmp1++',$WorkLayer . '-silk_tmp2++',);
	&TruncateLayers(@TmpLayers2);
	#选择第一个 #然后进行循环扩
	my $TmpFeatIndex;
	my $tInfoFile = $ENV{GENESIS_TMP} . '/info.' . int(rand(9999));
	$f->COM ( 'info',out_file => $tInfoFile,args => " -t layer -e $JOB/$STEP/$TmpLayerS1 -d FEATURES -o feat_index" ) ;
	open ( FH,"<$tInfoFile" ) ;
	while ( <FH> ) {
		my $line = $_;
		if ( $line =~ /^\#\d+\s+/ ) {
			#1    #S P 0
			( $TmpFeatIndex ) = ($line =~ /^\#(\d+)\s+/i);
			last;
		}
	}
	close FH;
	unlink $tInfoFile;

	$f->COM('sel_options', clear_mode => 'clear_none', display_mode => 'displayed_layers', area_inout => 'inside', area_select => 'select', select_mode => 'standard', area_touching_mode => 'exclude');
	while ( defined $TmpFeatIndex ) {
		$f->COM('affected_layer', name =>$TmpLayerS1, mode => 'single', affected => 'yes');
		$f->COM('sel_layer_feat', operation => 'select', layer => $TmpLayerS1, index => $TmpFeatIndex);

#		$f->COM('sel_copy_other', dest => 'layer_name', target_layer => , invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0, rotation => 0, mirror => 'none');
		$f->COM('sel_move_other', target_layer => $TmpLayerIndex, invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0);

		$f->COM('affected_layer', name => $TmpLayerS1, mode => 'single', affected => 'no');
		$f->COM('affected_layer', name => $WorkLayer, mode => 'single', affected => 'yes');

		$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
#		$f->COM('filter_area_strt');
#		$f->COM('filter_area_end', filter_name => 'popup', operation => 'select');
#		$f->COM('sel_ref_feat', layers => $TmpLayerIndex, use => 'filter', mode => 'touch', pads_as => 'shape', f_types => 'line;pad;surface;arc;text', polarity => 'positive;negative', include_syms => '', exclude_syms => '');
		$f->COM('sel_ref_feat', layers => $TmpLayerIndex, use => 'filter', mode => 'cover', pads_as => 'shape', f_types => 'line;pad;surface;arc;text', polarity => 'positive;negative', include_syms => '', exclude_syms => '');
		$f->COM('get_select_count');
		if ( $f->{COMANS} != 0 ) {
	#		if ( $f->{COMANS} >= 4 ) {
			$f->INFO(entity_type => 'layer',entity_path => " $JOB/$STEP/$WorkLayer",data_type => 'FEAT_HIST',options => "select");
	#		if( $f->{doinfo}{gFEAT_HISTarc} != 0 || $f->{doinfo}{gFEAT_HISTline} >= 4 ){
			if( ( $BoxRingsJud == 1 && $f->{doinfo}{gFEAT_HISTarc} != 0 ) || ( $f->{doinfo}{gFEAT_HISTarc} + $f->{doinfo}{gFEAT_HISTline} ) >= 4 ){
				&ZoomTextBoxSub($WorkLayer,$WorkCoverLayer,$WorkOkLayer,$TmpWordBoxSy);
			}
		} else {
#			next;
		}

		$f->COM('affected_layer', name => $WorkLayer, mode => 'single', affected => 'no');

		$f->COM('truncate_layer', layer => $TmpLayerIndex);
		$f->COM('affected_layer', name => $TmpLayerS1, mode => 'single', affected => 'yes');
		$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
#		$f->COM('sel_ref_feat', layers => $WorkCoverLayer, use => 'filter', mode => 'disjoint', pads_as => 'shape', f_types => 'line;pad;surface;arc;text', polarity => 'positive;negative', include_syms => '', exclude_syms => '');
		$f->COM('sel_ref_feat', layers => $WorkLayer, use => 'filter', mode => 'disjoint', pads_as => 'shape', f_types => 'line;pad;surface;arc;text', polarity => 'positive;negative', include_syms => '', exclude_syms => '');
		$f->COM('get_select_count');
		if ($f->{COMANS} != 0 ) {
			$f->COM('sel_delete');
		}
		$f->COM('affected_layer', name =>$TmpLayerS1, mode => 'single', affected => 'no');

		undef $TmpFeatIndex;
		my $tInfoFile = $ENV{GENESIS_TMP} . '/info.' . int(rand(9999));
		$f->COM ( 'info',out_file => $tInfoFile,args => " -t layer -e $JOB/$STEP/$TmpLayerS1 -d FEATURES -o feat_index" ) ;
		open ( FH,"<$tInfoFile" ) ;
		while ( <FH> ) {
			my $line = $_;
			if ( $line =~ /^\#\d+\s+/ ) {
				#1    #S P 0
				( $TmpFeatIndex ) = ($line =~ /^\#(\d+)\s+/i);
				last;
			}
		}
		close FH;
		unlink $tInfoFile;

	}
	
	&DelLayers($TmpLayerS1,$TmpLayerIndex,@TmpLayers2);

	$f->COM('sel_options', clear_mode => 'clear_after', display_mode => 'all_layers', area_inout => 'inside', area_select => 'select', select_mode => 'standard', area_touching_mode => 'exclude');
	$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
	$f->VOF;
	$f->COM('display_layer', name => $WorkLayer, display => 'yes');
	$f->COM('display_layer', name => $WorkOkLayer, display => 'yes');
	$f->COM('display_layer', name => $WorkCoverLayer, display => 'yes');
	$f->VON;
	$f->COM('zoom_home');
	if ( defined $f->COM('get_select_count') ) {
		&MsgBox("脚本运行Ok","info","ok","全自动文字框外扩脚本运行Ok,  请检查资料是否正确!!!",);
	}

#	$f->COM('get_disp_layers');
#	my @DispLayers = split (" ",$f->{COMANS});
#	my $WorkOkLayerDispJud = 'no';
#	for ( @DispLayers ){
#		if( $_ eq  $WorkOkLayer ){
#			$WorkOkLayerDispJud = 'yes';
#			last;
#		}
#	}
#	if ( $WorkOkLayerDispJud eq 'no' ) {
#		$f->COM('display_layer', name => $WorkOkLayer, display => 'yes');
#	}
}

sub ZoomTextBoxSub {  #全自动缩放文字框  子程序
	my ($WorkLayer,$WorkCoverLayer,$WorkOkLayer,$TmpWordBoxSy) = (@_) ;
	use Math::Trig;
	#获取框选区域的 物件的 LIMITS 和 物件FEATURES #获取最大线
	my $MinLineSize = 3 ;
	my %AngleData;
	my %LineData;

	my ($RotationAngle,$RecoveryAngle);
	my $TypeMode = 'Arc';
	my $ReplaceMode = 'Normal';
	my $tMinLineSize = 100 ;
	my $tInfoFile = $ENV{GENESIS_TMP} . '/info.' . int(rand(9999));
	$f->COM ( 'info',out_file => $tInfoFile,args => " -t layer -e $JOB/$STEP/$WorkLayer -d FEATURES -o select" ) ;
	open ( FH,"<$tInfoFile" ) ;
	while ( <FH> ) {
		my $line = $_;
		my ( $Size,$Positive ) = (0,'N');
		my ( $Xs,$Ys,$Xe,$Ye );
		if ( $line =~ /\#L/ ) {
			#L 1.80117 8.85592 1.79867 8.85717 r4.5 P 19
			($Xs,$Ys,$Xe,$Ye,$Size,$Positive ) = ( split ( ' ',$line ) ) [1,2,3,4,5,6,];
			if ($Xs == $Xe ) {
				$AngleData{90}++;
				my $tLineLength = abs ($Ye - $Ys) ;
				$LineData{$tLineLength} = 90;
			} elsif ($Ys == $Ye ) {
				$AngleData{0}++;
				my $tLineLength = abs ($Xe - $Xs) ;
				$LineData{$tLineLength} = 0;
			} else {
#				$f->PAUSE("$Ye,$Ys,$Xe,$Xs");
				my $tLineAngle = atan2 ( $Ye - $Ys,$Xe - $Xs ) * 180 / pi;
				$AngleData{$tLineAngle}++;
				my $tLineLength = sqrt ( ( $Xs - $Xe ) ** 2 + ( $Ys - $Ye ) ** 2 ) ;
				$LineData{$tLineLength} = $tLineAngle;

				$ReplaceMode = 'Rotate';
			}
			$TypeMode = 'Line';
		}elsif ( $line =~ /\#A/ ) {
			#A 1.96316 9.02362 1.96316 9.02362 1.89566 9.02362 r12 P 12 Y
			( $Size,$Positive ) = ( split ( ' ',$line ) ) [7,8,];
		}
		if ( $Positive eq 'P' ) {
			$Size =~ s/r//;
#			if ( $Size > $MinLineSize ) {
			if ( $Size < $tMinLineSize ) {
				$tMinLineSize = $Size ;
			}
		}
	}
	close FH;
	unlink $tInfoFile;
	if ( $tMinLineSize != 100 and $tMinLineSize > $MinLineSize ) {
		$MinLineSize = $tMinLineSize;
	}

	my $MinLineSizeInch = $MinLineSize / 1000;

	if ( $ReplaceMode eq 'Rotate' ) {
		my @SortLength = sort { $a <=> $b }( keys %LineData );
		my $tLengthMax = $LineData{$SortLength[$#SortLength]};
		if ( $tLengthMax == 0 || $tLengthMax == 90 ){
			$ReplaceMode = 'Normal';
		} else {
			if ( $tLengthMax < 0 ) {
				$RotationAngle = $tLengthMax  + 360;
			}else{
				$RotationAngle = $tLengthMax ;
			}
			$RecoveryAngle = 360 - $RotationAngle ;
		}
#		my @SortAngle = sort { $AngleData{$a} <=> $AngleData{$b} }( keys %AngleData );
#		if ( $SortAngle[$#SortAngle] == 0 || $SortAngle[$#SortAngle] == 90 ){
#			$ReplaceMode = 'Normal';
#		} else {

#			if ( $SortAngle[$#SortAngle] < 0 ) {
#				$RotationAngle = $SortAngle[$#SortAngle]  + 360;
#			}else{
#				$RotationAngle = $SortAngle[$#SortAngle] ;
#			}
#			$RecoveryAngle = 360 - $RotationAngle ;
#		}
	}
#		$f->COM('sel_options', clear_mode => 'clear_none', display_mode => 'displayed_layers', area_inout => 'inside', area_select => 'select', select_mode => 'standard', area_touching_mode => 'exclude');
	##########################################################################

	if ( $ReplaceMode eq 'Rotate' ) {
		my $TmpAttrStart = 'neo_silk-tmp1.' . int(rand(99999999));
		my $TmpAttrEnd = 'neo_silk-tmp2.' . int(rand(99999999));
		#不为0°或者不为90°则执行这一步

		#删除临时层别 $TmpLayers2[0] $TmpLayers2[1]
#		&TruncateLayers(@TmpLayers2);
		my @TmpLayers2 = ($WorkLayer . '-silk_tmp1++',$WorkLayer . '-silk_tmp2++',);

		#添加属性
		$f->COM('cur_atr_reset');
		$f->COM('cur_atr_set', attribute => '.string', text => $TmpAttrStart);
		$f->COM('sel_change_atr', mode => 'add');
		#复制到临时层$TmpLayers2[0]
		$f->COM('get_select_count');
		if ( $f->{COMANS} != 0 ) {
			$f->COM('sel_copy_other', dest => 'layer_name', target_layer => $TmpLayers2[0], invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0);
#				$f->PAUSE(0);

			#修改属性为后属性
#				$f->COM('sel_change_atr', mode => 'edit', attributes => '.string', attr_vals => $TmpAttrEnd);
			$f->COM('cur_atr_reset');
			$f->COM('cur_atr_set', attribute => '.string', text => $TmpAttrEnd);
			$f->COM('sel_change_atr', mode => 'add');

			#套层选择
			$f->COM('affected_layer', name => $WorkCoverLayer, mode => 'single', affected => 'yes');
			$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
			$f->COM('sel_ref_feat', layers => '', use => 'select', mode => 'touch', pads_as => 'shape', f_types => 'line;pad;surface;arc;text', polarity => 'positive;negative', include_syms => '', exclude_syms => '');
		
			####
			$f->COM('get_select_count');
			if ( $f->{COMANS} != 0 ) {
#			if ( $f->{COMANS} >= 4 ) {
				#添加属性
				$f->COM('cur_atr_reset');
				$f->COM('cur_atr_set', attribute => '.string', text => $TmpAttrStart);
				$f->COM('sel_change_atr', mode => 'add');
				#复制到临时层别2 $TmpLayers2[1]

				$f->COM('sel_copy_other', dest => 'layer_name', target_layer => $TmpLayers2[1], invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0);
				#删除属性
				$f->COM('sel_delete_atr', mode => 'list', attributes => '.string', attr_vals => $TmpAttrStart);
				$f->COM('affected_layer', name => $WorkCoverLayer, mode => 'single', affected => 'no');
				#勾选临时层别
				$f->COM('affected_layer', name => $TmpLayers2[0], mode => 'single', affected => 'yes');
				$f->COM('affected_layer', name => $TmpLayers2[1], mode => 'single', affected => 'yes');
				#通过属性选择
				$f->COM('set_filter_attributes', filter_name => 'popup', exclude_attributes => 'no', condition => 'yes', attribute => '.string', min_int_val => 0, max_int_val => 0, min_float_val => 0, max_float_val => 0, option => '', text => $TmpAttrStart);
				$f->COM('filter_area_strt');
				$f->COM('filter_area_end', filter_name => 'popup', operation => 'select');
				$f->COM('get_select_count');
				if ( $f->{COMANS} != 0 ) {
					#获取 $TmpLayers2[0] 层别中心
					$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$TmpLayers2[0]",data_type => 'LIMITS'
			#		,options => "select"
					);
					my $RotateCenterX = ($f->{doinfo}{gLIMITSxmax} + $f->{doinfo}{gLIMITSxmin} ) / 2 ;
					my $RotateCenterY = ($f->{doinfo}{gLIMITSymax} + $f->{doinfo}{gLIMITSymin} ) / 2 ;

					#旋转角度
					$f->COM('sel_transform', oper => 'rotate', x_anchor => $RotateCenterX , y_anchor => $RotateCenterY, angle => $RotationAngle, x_scale => 1, y_scale => 1, x_offset => 0, y_offset => 0, mode => 'anchor', duplicate => 'no');
					#清除选择
					$f->COM('sel_clear_feat');

					#框选$TmpLayers2[0] +1mil 层区域
					$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$TmpLayers2[0]",data_type => 'LIMITS'
			#		,options => "select"
					);

					my $tWorkLimitsMinX =  $f->{doinfo}{gLIMITSxmin};
					my $tWorkLimitsMinY =  $f->{doinfo}{gLIMITSymin};
					my $tWorkLimitsMaxX =  $f->{doinfo}{gLIMITSxmax};
					my $tWorkLimitsMaxY =  $f->{doinfo}{gLIMITSymax};

					my $WorkLimitsMinX =  $f->{doinfo}{gLIMITSxmin} + $MinLineSizeInch;
					my $WorkLimitsMinY =  $f->{doinfo}{gLIMITSymin} + $MinLineSizeInch;
					my $WorkLimitsMaxX =  $f->{doinfo}{gLIMITSxmax} - $MinLineSizeInch;
					my $WorkLimitsMaxY =  $f->{doinfo}{gLIMITSymax} - $MinLineSizeInch;

	#					$f->PAUSE(2);
					$f->COM('affected_layer', name => $TmpLayers2[0], mode => 'single', affected => 'no');
					
	#				$f->COM('filter_area_strt');
	#				$f->COM('filter_area_xy', x => $f->{doinfo}{gLIMITSxmin} - $BoxSelTol, y => $f->{doinfo}{gLIMITSymin} - $BoxSelTol);
	#				$f->COM('filter_area_xy', x => $f->{doinfo}{gLIMITSxmax} + $BoxSelTol, y => $f->{doinfo}{gLIMITSymax} + $BoxSelTol);
	#				$f->COM('filter_area_end', layer => '', filter_name => 'popup', operation => 'select', area_type => 'rectangle', inside_area => 'yes', intersect_area => 'no');
	##					$f->PAUSE("3=$WorkLimitsMinX,$WorkLimitsMinY.$WorkLimitsMaxX.$WorkLimitsMaxY");
	#				$f->COM('sel_break');
	#				$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$TmpLayers2[1]",data_type => 'LIMITS',options => "select");
					
					$f->COM('filter_area_strt');
					$f->COM('filter_area_end', filter_name => 'popup', operation => 'select');
					
#					$f->COM('sel_options', clear_mode => 'clear_none', display_mode => 'displayed_layers', area_inout => 'inside', area_select => 'unselect', select_mode => 'standard', area_touching_mode => 'exclude');
					
					$f->COM('filter_area_strt');
					$f->COM('filter_area_xy', x => $f->{doinfo}{gLIMITSxmin} - $BoxSelTol, y => $f->{doinfo}{gLIMITSymin} - $BoxSelTol);
					$f->COM('filter_area_xy', x => $f->{doinfo}{gLIMITSxmax} + $BoxSelTol, y => $f->{doinfo}{gLIMITSymax} + $BoxSelTol);
					$f->COM('filter_area_end', layer => '', filter_name => 'popup', operation => 'unselect', area_type => 'rectangle', inside_area => 'yes', intersect_area => 'no');
					$f->COM('get_select_count');
					if ( $f->{COMANS} != 0 ) {
						$f->COM('sel_delete');
					}
#					$f->COM('sel_options', clear_mode => 'clear_none', display_mode => 'displayed_layers', area_inout => 'inside', area_select => 'select', select_mode => 'standard', area_touching_mode => 'exclude');
					
					$f->COM('sel_break');

					$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$TmpLayers2[1]",data_type => 'LIMITS');

					my $WorkCoverLimitsMinX =  $f->{doinfo}{gLIMITSxmin};
					my $WorkCoverLimitsMinY =  $f->{doinfo}{gLIMITSymin};
					my $WorkCoverLimitsMaxX =  $f->{doinfo}{gLIMITSxmax};
					my $WorkCoverLimitsMaxY =  $f->{doinfo}{gLIMITSymax};
	#					print "44=$TmpLayers2[1],$f->{doinfo}{gLIMITSxmin},$f->{doinfo}{gLIMITSymin},$f->{doinfo}{gLIMITSxmax},$f->{doinfo}{gLIMITSymax}\n";
	#				$f->PAUSE("44=$TmpLayers2[1],$f->{doinfo}{gLIMITSxmin},$f->{doinfo}{gLIMITSymin},$f->{doinfo}{gLIMITSxmax},$f->{doinfo}{gLIMITSymax}" );
					my $WorkCoverLimitsCenterX =  $WorkCoverLimitsMinX + ( $WorkCoverLimitsMaxX  - $WorkCoverLimitsMinX ) / 2 ;
					my $WorkCoverLimitsCenterY =  $WorkCoverLimitsMinY + ( $WorkCoverLimitsMaxY  - $WorkCoverLimitsMinY ) / 2 ;
					my ($tScaleX,$tScaleY,) = (1,1,);
					my $tTmpScaleX1 = abs($WorkCoverLimitsCenterX - $WorkCoverLimitsMinX) / abs($WorkCoverLimitsCenterX - $WorkLimitsMinX);
					my $tTmpScaleX2 = abs($WorkCoverLimitsCenterX - $WorkCoverLimitsMaxX) / abs($WorkCoverLimitsCenterX - $WorkLimitsMaxX);
					if ($tTmpScaleX1 > $tScaleX ){
						$tScaleX = $tTmpScaleX1;
					}
					if ($tTmpScaleX2 > $tScaleX ){
						$tScaleX = $tTmpScaleX2;
					}

					my $tTmpScaleY1 = abs($WorkCoverLimitsCenterY - $WorkCoverLimitsMinY) / abs($WorkCoverLimitsCenterY - $WorkLimitsMinY);
					my $tTmpScaleY2 = abs($WorkCoverLimitsCenterY - $WorkCoverLimitsMaxY) / abs($WorkCoverLimitsCenterY - $WorkLimitsMaxY);
					if ($tTmpScaleY1 > $tScaleY ){
						$tScaleY = $tTmpScaleY1;
					}
					if ($tTmpScaleY2 > $tScaleY ){
						$tScaleY = $tTmpScaleY2;
					}
	#										$f->PAUSE("5=x_scale => $tScaleX, y_scale => $tScaleY," );

	#					$f->PAUSE(3);
					$f->COM('undo', depth => 1);

					$f->COM('affected_layer', name => $TmpLayers2[1], mode => 'single', affected => 'no');
					$f->COM('affected_layer', name => $TmpLayers2[0], mode => 'single', affected => 'yes');

					$f->COM('filter_area_strt');
					$f->COM('filter_area_xy', x => $tWorkLimitsMinX - $BoxSelTol, y => $tWorkLimitsMinY - $BoxSelTol);
					$f->COM('filter_area_xy', x => $tWorkLimitsMaxX + $BoxSelTol, y => $tWorkLimitsMaxY + $BoxSelTol);
					$f->COM('filter_area_end', layer => '', filter_name => 'popup', operation => 'select', area_type => 'rectangle', inside_area => 'yes', intersect_area => 'no');

#					if ( $tScaleX != 1 and $tScaleY != 1 ) {
					if ( $tScaleX != 1 or $tScaleY != 1 ) {
						$f->COM('sel_transform', x_anchor => $WorkCoverLimitsCenterX, y_anchor => $WorkCoverLimitsCenterY, x_scale => $tScaleX, y_scale => $tScaleY, oper => 'scale', angle => 0, direction => 'ccw', x_offset => 0, y_offset => 0, mode => 'anchor', duplicate => 'no');
					}
					###
					#获取$TmpLayers2[1] 中心和边缘
					#获取$TmpLayers2[0] 边缘
					#计算拉伸值
					#拉伸
					$f->COM('affected_layer', name => $TmpLayers2[1], mode => 'single', affected => 'yes');
					#COM sel_clear_feat
					#框选
					$f->COM('filter_area_strt');
					$f->COM('filter_area_xy', x => $tWorkLimitsMinX - $BoxSelTol, y => $tWorkLimitsMinY - $BoxSelTol);
					$f->COM('filter_area_xy', x => $tWorkLimitsMaxX + $BoxSelTol, y => $tWorkLimitsMaxY + $BoxSelTol);
					$f->COM('filter_area_end', layer => '', filter_name => 'popup', operation => 'select', area_type => 'rectangle', inside_area => 'yes', intersect_area => 'no');
					#旋转回来
					$f->COM('sel_transform', oper => 'rotate', x_anchor => $RotateCenterX , y_anchor => $RotateCenterY, angle => $RecoveryAngle, x_scale => 1, y_scale => 1, x_offset => 0, y_offset => 0, mode => 'anchor', duplicate => 'no');
					#获取$TmpLayers2[1]中心位置
	#										$f->PAUSE(5);

					$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$TmpLayers2[1]",data_type => 'LIMITS',options => "select");
					my $WorkCoverLimitsCenterX2 = ($f->{doinfo}{gLIMITSxmax} + $f->{doinfo}{gLIMITSxmin} ) / 2 ;
					my $WorkCoverLimitsCenterY2 = ($f->{doinfo}{gLIMITSymax} + $f->{doinfo}{gLIMITSymin} ) / 2 ;

					$f->COM('affected_layer', name => $TmpLayers2[1], mode => 'single', affected => 'no');
					$f->COM('sel_create_sym', symbol => $TmpWordBoxSy, x_datum => $WorkCoverLimitsCenterX2, y_datum => $WorkCoverLimitsCenterY2 , delete => 'no', fill_dx => '0.1', fill_dy => '0.1', attach_atr => 'no', retain_atr => 'no');
					#$f->COM('affected_layer', name => $TmpLayers2[0], mode => 'single', affected => 'no');
					#删除 $TmpLayers2[0] $TmpLayers2[1]
	#					$f->PAUSE(6);
					$f->COM('affected_layer', name => $TmpLayers2[0], mode => 'single', affected => 'no');

					$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
					$f->COM('set_filter_attributes', filter_name => 'popup', exclude_attributes => 'no', condition => 'yes', attribute => '.string', min_int_val => 0, max_int_val => 0, min_float_val => 0, max_float_val => 0, option => '', text => $TmpAttrEnd);
					$f->COM('filter_area_strt');
					$f->COM('filter_area_end', filter_name => 'popup', operation => 'select');
					#删除属性
					$f->COM('sel_delete_atr', mode => 'list', attributes => '.string', attr_vals => $TmpAttrEnd);
					$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
					#相同操作
					#替换sy
					$f->COM('get_select_count');

					if ( $f->{COMANS} == 0 ) {
						$f->PAUSE(11);
					}

					$f->COM('sel_substitute', mode => 'substitute', dcode => 0, symbol => $TmpWordBoxSy, x_datum => $WorkCoverLimitsCenterX2, y_datum => $WorkCoverLimitsCenterY2 , tol => 1, rotation => 0);
					#移动 到ok层
					#打散

					&TruncateLayers(@TmpLayers2);
				}
			} else {
				&TruncateLayers($TmpLayers2[0]);
				$f->COM('affected_layer', name => $WorkCoverLayer, mode => 'single', affected => 'no');

				$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$WorkLayer",data_type => 'LIMITS',options => "select");
				my $WorkLimitsMinX =  $f->{doinfo}{gLIMITSxmin};
				my $WorkLimitsMinY =  $f->{doinfo}{gLIMITSymin};
				my $WorkLimitsMaxX =  $f->{doinfo}{gLIMITSxmax};
				my $WorkLimitsMaxY =  $f->{doinfo}{gLIMITSymax};

				my $WorkLimitsCenterX =  $WorkLimitsMinX + ( $WorkLimitsMaxX  - $WorkLimitsMinX ) / 2 ;
				my $WorkLimitsCenterY =  $WorkLimitsMinY + ( $WorkLimitsMaxY  - $WorkLimitsMinY ) / 2 ;

				$f->COM('sel_clear_feat');
				$f->COM('reset_filter_criteria' ,filter_name => '' ,criteria => 'all');
				$f->COM('set_filter_attributes' ,filter_name => 'popup' ,exclude_attributes => 'no' ,condition => 'yes' ,attribute => '.string' ,min_int_val => 0 ,max_int_val => 0 ,min_float_val => 0 ,max_float_val => 0 ,option => '' ,text => $TmpAttrEnd);
				$f->COM('filter_area_strt');
				$f->COM('filter_area_end' ,filter_name => 'popup' ,operation => 'select');
				$f->COM('get_select_count');
				if ( $f->{COMANS} != 0 ) {
					#删除属性
					$f->COM('sel_delete_atr', mode => 'list', attributes => '.string', attr_vals => $TmpAttrEnd);
					$f->COM('sel_clear_feat');

#					$f->COM('sel_create_sym', symbol => $TmpWordBoxSy, x_datum => $WorkLimitsCenterX, y_datum => $WorkLimitsCenterY, delete => 'no', fill_dx => '0.1', fill_dy => '0.1', attach_atr => 'no', retain_atr => 'no');
	#				if ( $f->COM('get_select_count') == 0 ) {
	#					$f->PAUSE(115);
	#				}

#					$f->COM('sel_substitute', mode => 'substitute', dcode => 0, symbol => $TmpWordBoxSy, x_datum => $WorkLimitsCenterX, y_datum => $WorkLimitsCenterY, tol => 1, rotation => 0);
				}
			}
		} else {
			$f->COM('get_select_count');
			if ( $f->{COMANS} != 0 ) {
				#删除属性
				$f->COM('sel_delete_atr', mode => 'list', attributes => '.string', attr_vals => $TmpAttrStart);
				$f->COM('sel_clear_feat');

			}
		}
	} elsif ( $ReplaceMode eq 'Normal' ) {
		$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$WorkLayer",data_type => 'LIMITS',options => "select");
		my $WorkLimitsMinX =  $f->{doinfo}{gLIMITSxmin} + $MinLineSizeInch;
		my $WorkLimitsMinY =  $f->{doinfo}{gLIMITSymin} + $MinLineSizeInch;
		my $WorkLimitsMaxX =  $f->{doinfo}{gLIMITSxmax} - $MinLineSizeInch;
		my $WorkLimitsMaxY =  $f->{doinfo}{gLIMITSymax} - $MinLineSizeInch;

		my $TmpAttr = 'neo_silk-tmp1.' . int(rand(99999999));
		$f->COM('cur_atr_reset');
		$f->COM('cur_atr_set', attribute => '.string', text => $TmpAttr);
		$f->COM('sel_change_atr', mode => 'add');

		#
		#框选区域 FEATURES+单边1mil 获取套层 选中的 LIMITS
		$f->COM('affected_layer', name => $WorkCoverLayer, mode => 'single', affected => 'yes');
		
#	#	$f->COM('sel_clear_feat');
#		$f->COM('filter_area_strt');
#		$f->COM('filter_area_xy', x => $f->{doinfo}{gLIMITSxmin} - $BoxSelTol, y => $f->{doinfo}{gLIMITSymin} - $BoxSelTol);
#		$f->COM('filter_area_xy', x => $f->{doinfo}{gLIMITSxmax} + $BoxSelTol, y => $f->{doinfo}{gLIMITSymax} + $BoxSelTol);
#		$f->COM('filter_area_end', layer => '', filter_name => 'popup', operation => 'select', area_type => 'rectangle', inside_area => 'yes', intersect_area => 'no');

		$f->COM('reset_filter_criteria' ,filter_name => '' ,criteria => 'all');
		$f->COM('set_filter_polarity' ,filter_name => '' ,positive => 'yes' ,negative => 'no');
		$f->COM('sel_ref_feat' ,layers => $WorkCoverLayer ,use => 'select' ,mode => 'touch' ,pads_as => 'shape' ,f_types => 'line;pad;surface;arc;text' ,polarity => 'positive;negative' ,include_syms => '' ,exclude_syms => '');
		$f->COM('get_select_count');
		if ( $f->{COMANS} != 0 ) {
		
#			$f->COM('sel_options' ,clear_mode => 'clear_none' ,display_mode => 'displayed_layers' ,area_inout => 'outside' ,area_select => 'unselect' ,select_mode => 'standard' ,area_touching_mode => 'exclude');

			$f->COM('filter_area_strt');
			$f->COM('filter_area_xy', x => $f->{doinfo}{gLIMITSxmin} - $BoxSelTol, y => $f->{doinfo}{gLIMITSymin} - $BoxSelTol);
			$f->COM('filter_area_xy', x => $f->{doinfo}{gLIMITSxmax} + $BoxSelTol, y => $f->{doinfo}{gLIMITSymax} + $BoxSelTol);
			$f->COM('filter_area_end' ,layer => '' ,filter_name => 'popup' ,operation => 'unselect' ,area_type => 'rectangle' ,inside_area => 'no' ,intersect_area => 'no');

#			$f->COM('sel_options' ,clear_mode => 'clear_none' ,display_mode => 'displayed_layers' ,area_inout => 'inside' ,area_select => 'select' ,select_mode => 'standard' ,area_touching_mode => 'exclude');
#			$f->PAUSE(1);
			$f->COM('get_select_count');
			if ( $f->{COMANS} != 0 ) {
				$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$WorkCoverLayer",data_type => 'LIMITS',options => "select");
				my $WorkCoverLimitsMinX =  $f->{doinfo}{gLIMITSxmin};
				my $WorkCoverLimitsMinY =  $f->{doinfo}{gLIMITSymin};
				my $WorkCoverLimitsMaxX =  $f->{doinfo}{gLIMITSxmax};
				my $WorkCoverLimitsMaxY =  $f->{doinfo}{gLIMITSymax};

				my $WorkCoverLimitsCenterX =  $WorkCoverLimitsMinX + ( $WorkCoverLimitsMaxX  - $WorkCoverLimitsMinX ) / 2 ;
				my $WorkCoverLimitsCenterY =  $WorkCoverLimitsMinY + ( $WorkCoverLimitsMaxY  - $WorkCoverLimitsMinY ) / 2 ;
				my ($tScaleX,$tScaleY,) = (1,1,);
				my $tTmpScaleX1 = abs($WorkCoverLimitsCenterX - $WorkCoverLimitsMinX) / abs($WorkCoverLimitsCenterX - $WorkLimitsMinX);
				my $tTmpScaleX2 = abs($WorkCoverLimitsCenterX - $WorkCoverLimitsMaxX) / abs($WorkCoverLimitsCenterX - $WorkLimitsMaxX);
				if ($tTmpScaleX1 > $tScaleX ){
					$tScaleX = $tTmpScaleX1;
				}
				if ($tTmpScaleX2 > $tScaleX ){
					$tScaleX = $tTmpScaleX2;
				}

				my $tTmpScaleY1 = abs($WorkCoverLimitsCenterY - $WorkCoverLimitsMinY) / abs($WorkCoverLimitsCenterY - $WorkLimitsMinY);
				my $tTmpScaleY2 = abs($WorkCoverLimitsCenterY - $WorkCoverLimitsMaxY) / abs($WorkCoverLimitsCenterY - $WorkLimitsMaxY);
				if ($tTmpScaleY1 > $tScaleY ){
					$tScaleY = $tTmpScaleY1;
				}
				if ($tTmpScaleY2 > $tScaleY ){
					$tScaleY = $tTmpScaleY2;
				}
#$f->PAUSE("2,$tScaleX=$tScaleY");
				$f->COM('affected_layer', name => $WorkCoverLayer, mode => 'single', affected => 'no');

		#		$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
		#		$f->COM('set_filter_attributes', filter_name => 'popup', exclude_attributes => 'yes', condition => 'yes', attribute => '.string', min_int_val => 0, max_int_val => 0, min_float_val => 0, max_float_val => 0, option => '', text => $TmpAttr);
		#		$f->COM('filter_area_strt');
		#		$f->COM('filter_area_end', filter_name => 'popup', operation => 'unselect');
		#		$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');

				$f->COM('sel_clear_feat');
				$f->COM('reset_filter_criteria' ,filter_name => '' ,criteria => 'all');
				$f->COM('set_filter_attributes' ,filter_name => 'popup' ,exclude_attributes => 'no' ,condition => 'yes' ,attribute => '.string' ,min_int_val => 0 ,max_int_val => 0 ,min_float_val => 0 ,max_float_val => 0 ,option => '' ,text => $TmpAttr);
				$f->COM('filter_area_strt');
				$f->COM('filter_area_end' ,filter_name => 'popup' ,operation => 'select');
				$f->COM('reset_filter_criteria' ,filter_name => '' ,criteria => 'all');

				$f->COM('get_select_count');
				if ( $f->{COMANS} != 0 ) {
					$f->COM('sel_delete_atr', mode => 'list', attributes => '.string', attr_vals => $TmpAttr);
					$f->COM('cur_atr_reset');
					#
					if ( $tScaleX != 1 or $tScaleY != 1 ) {
#					if ( $tScaleX ne 1 and $tScaleY ne 1 ) {
						$f->COM('sel_transform', x_anchor => $WorkCoverLimitsCenterX, y_anchor => $WorkCoverLimitsCenterY, x_scale => $tScaleX, y_scale => $tScaleY, oper => 'scale', angle => 0, direction => 'ccw', x_offset => 0, y_offset => 0, mode => 'anchor', duplicate => 'no');
					}
					#
#					$f->PAUSE("3,$tScaleX=$tScaleY");
					$f->COM('sel_create_sym', symbol => $TmpWordBoxSy, x_datum => $WorkCoverLimitsCenterX, y_datum => $WorkCoverLimitsCenterY, delete => 'no', fill_dx => '0.1', fill_dy => '0.1', attach_atr => 'no', retain_atr => 'no');
					$f->COM('undo', depth => 1);
#						$f->COM('get_select_count');
#						if ( $f->{COMANS} == 0 ) {
#							$f->PAUSE(112);
#						}

					$f->COM('sel_substitute', mode => 'substitute', dcode => 0, symbol => $TmpWordBoxSy, x_datum => $WorkCoverLimitsCenterX, y_datum => $WorkCoverLimitsCenterY, tol => 1, rotation => 0);
				}
			} else {
				$f->COM('affected_layer', name => $WorkCoverLayer, mode => 'single', affected => 'no');
				my $WorkLimitsCenterX =  $WorkLimitsMinX + ( $WorkLimitsMaxX  - $WorkLimitsMinX ) / 2 ;
				my $WorkLimitsCenterY =  $WorkLimitsMinY + ( $WorkLimitsMaxY  - $WorkLimitsMinY ) / 2 ;

				$f->COM('sel_clear_feat');
				$f->COM('reset_filter_criteria' ,filter_name => '' ,criteria => 'all');
				$f->COM('set_filter_attributes' ,filter_name => 'popup' ,exclude_attributes => 'no' ,condition => 'yes' ,attribute => '.string' ,min_int_val => 0 ,max_int_val => 0 ,min_float_val => 0 ,max_float_val => 0 ,option => '' ,text => $TmpAttr);
				$f->COM('filter_area_strt');
				$f->COM('filter_area_end' ,filter_name => 'popup' ,operation => 'select');
				$f->COM('get_select_count');
				if ( $f->{COMANS} != 0 ) {
#					$f->PAUSE(117);
					#删除属性
					$f->COM('sel_delete_atr', mode => 'list', attributes => '.string', attr_vals => $TmpAttr);
					$f->COM('sel_clear_feat');
#					$f->PAUSE(117);
#					$f->COM('sel_create_sym', symbol => $TmpWordBoxSy, x_datum => $WorkLimitsCenterX, y_datum => $WorkLimitsCenterY, delete => 'no', fill_dx => '0.1', fill_dy => '0.1', attach_atr => 'no', retain_atr => 'no');
#					if ( $f->COM('get_select_count') == 0 ) {
#						$f->PAUSE(114);
#					}
#					$f->COM('sel_substitute', mode => 'substitute', dcode => 0, symbol => $TmpWordBoxSy, x_datum => $WorkLimitsCenterX, y_datum => $WorkLimitsCenterY, tol => 1, rotation => 0);
				}
			}
		} else {
			$f->COM('affected_layer', name => $WorkCoverLayer, mode => 'single', affected => 'no');
			my $WorkLimitsCenterX =  $WorkLimitsMinX + ( $WorkLimitsMaxX  - $WorkLimitsMinX ) / 2 ;
			my $WorkLimitsCenterY =  $WorkLimitsMinY + ( $WorkLimitsMaxY  - $WorkLimitsMinY ) / 2 ;

			$f->COM('sel_clear_feat');
			$f->COM('reset_filter_criteria' ,filter_name => '' ,criteria => 'all');
			$f->COM('set_filter_attributes' ,filter_name => 'popup' ,exclude_attributes => 'no' ,condition => 'yes' ,attribute => '.string' ,min_int_val => 0 ,max_int_val => 0 ,min_float_val => 0 ,max_float_val => 0 ,option => '' ,text => $TmpAttr);
			$f->COM('filter_area_strt');
			$f->COM('filter_area_end' ,filter_name => 'popup' ,operation => 'select');
			$f->COM('get_select_count');
			if ( $f->{COMANS} != 0 ) {
				#删除属性
				$f->COM('sel_delete_atr', mode => 'list', attributes => '.string', attr_vals => $TmpAttr);
#				$f->COM('sel_clear_feat');

#				$f->COM('sel_create_sym', symbol => $TmpWordBoxSy, x_datum => $WorkLimitsCenterX, y_datum => $WorkLimitsCenterY, delete => 'no', fill_dx => '0.1', fill_dy => '0.1', attach_atr => 'no', retain_atr => 'no');

				
#				if ( $f->COM('get_select_count') == 0 ) {
#					$f->PAUSE(113);
#				}

#				$f->COM('sel_substitute', mode => 'substitute', dcode => 0, symbol => $TmpWordBoxSy, x_datum => $WorkLimitsCenterX, y_datum => $WorkLimitsCenterY, tol => 1, rotation => 0);
#				if ( $f->COM('get_select_count') == 0 ) {
#					$f->PAUSE(118);
#				}

			}
		}
	}
	
	$f->COM('reset_filter_criteria' ,filter_name => '' ,criteria => 'all');
	$f->COM('sel_multi_feat', operation => 'select', feat_types => 'pad', include_syms => $TmpWordBoxSy, is_extended => 'no', clear_prev => 'yes');
	$f->COM('get_select_count');
	if ( $f->{COMANS} != 0 ) {
		$f->COM('sel_move_other', target_layer => $WorkOkLayer, invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0);
		$f->COM('affected_layer', name => $WorkOkLayer, mode => 'single', affected => 'yes');
		$f->COM('sel_multi_feat', operation => 'select', feat_types => 'pad', include_syms => $TmpWordBoxSy, is_extended => 'no', clear_prev => 'yes');
		$f->COM('get_select_count');
		if ( $f->{COMANS} != 0 ) {
			$f->COM('sel_break');
		}
		$f->COM('affected_layer', name => $WorkOkLayer, mode => 'single', affected => 'no');
	}
}

sub TruncateLayers {  #清空层别内容物
	$f->VOF;
	for ( @_ ) {
#		$f->COM('delete_layer', layer => $_);
		$f->COM('truncate_layer', layer => $_);
	}
	$f->VON;
}

sub SemiAutoWordBoxZoom {  #半自动缩放文字框
	use Math::Trig;
	#&RunScriptAct($MyScriptFile,'SemiAutoWordBoxZoom','Single','Scale',$CoverLayerSuffix);
	#&RunScriptAct($MyScriptFile,'SemiAutoWordBoxZoom','Multiple','Scale',$CoverLayerSuffix);
	#&RunScriptAct($MyScriptFile,'SemiAutoWordBoxZoom','Single','ScaleX',$CoverLayerSuffix);
	#&RunScriptAct($MyScriptFile,'SemiAutoWordBoxZoom','Single','ScaleY',$CoverLayerSuffix);
	#&RunScriptAct($MyScriptFile,'SemiAutoWordBoxZoom','Single','Expansion',$CoverLayerSuffix);

	my $RunSubScr = shift;
	my $tMode = shift;#Single #Multiple
	my $tRunType = shift;#Scale ScaleX ScaleY Expansion
	
	my $CoverLayerSuffix = shift;

	my $TmpWordBoxSy = 'neo_silk-tmp+';
	#工作层
	$f->COM('get_work_layer');
	my $WorkLayer = $f->{COMANS};
	if ( $WorkLayer eq '' ) {
		&MsgBox("没有工作层","warning","ok","没有工作层,脚本退出",);
		exit;
	}

	&GetJobStep;
	my $WorkCoverLayer = $WorkLayer . $CoverLayerSuffix;
	$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$WorkCoverLayer",data_type => 'EXISTS');
	if ( $f->{doinfo}{gEXISTS} eq 'no' ) {
		&MsgBox("套层不存在","warning","ok","套层 $WorkCoverLayer 不存在,脚本退出",);
		exit;
	}

	my $WorkOkSuffix = '-ok+';
	my $WorkOkLayer = $WorkLayer . $WorkOkSuffix;
	$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$WorkOkLayer",data_type => 'EXISTS');
	if ( $f->{doinfo}{gEXISTS} eq 'no' ) {
		$f->VOF;
		$f->COM('create_layer', layer => $WorkOkLayer, context => 'board', type => 'document', polarity => 'positive');
		$f->COM('create_layer', layer => $WorkOkLayer, type => 'document',);
		$f->VON;
		$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$WorkLayer",data_type => 'ROW');
		my $WorkLayerRow = $f->{doinfo}{gROW};
		$f->INFO(entity_type => 'layer',entity_path => "$JOB/$STEP/$WorkLayer",data_type => 'SIDE');
      if ( $f->{doinfo}{gSIDE} eq 'bottom' ) {
			$WorkLayerRow = $f->{doinfo}{gROW} + 1;
      }
		$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$WorkOkLayer",data_type => 'ROW');
		my $WorkOkLayerRow = $f->{doinfo}{gROW};
		$f->COM('matrix_move_row', job => $JOB, matrix => 'matrix', row => $WorkOkLayerRow, ins_row => $WorkLayerRow);
	}
	my $BoxSelTol = 0.001;#框选套层公差
#	my $BoxSelTol = 0.0003;#框选套层公差

	if( $tMode eq 'Multiple' ) {
		$f->COM('copy_layer', source_job => $JOB, source_step => $STEP, source_layer => $WorkLayer, dest => 'layer_name', dest_layer => $WorkLayer . '-bak+', mode => 'replace', invert => 'no');
	}
	SemiAutoWordBoxZoomMultipleRun:;########################################
#	$f->PAUSE(111);

	{
#		$f->PAUSE(2);

		$f->COM('affected_layer', name => '', mode => 'all', affected => 'no');

		$f->COM('units', type => 'inch');
	#	my ($X1,$Y1,$X2,$Y2,);
		$f->COM('get_select_count');
		if ( $f->{COMANS} == 0 ) {
			if( $tMode eq 'Single' ) {
				exit;
			} elsif( $tMode eq 'Multiple' ) {
				$f->MOUSE("r Please select the text box you want to enlarge.");
				($X1,$Y1,$X2,$Y2,) = split(/ /,$f->{MOUSEANS});
				$f->COM('filter_area_strt');
				$f->COM('filter_area_xy', x => $X1, y => $Y1);
				$f->COM('filter_area_xy', x => $X2, y => $Y2);
				$f->COM('filter_area_end', layer => '', filter_name => 'popup', operation => 'select', area_type => 'rectangle', inside_area => 'yes', intersect_area => 'no');
				$f->COM('get_select_count');
				my $tSelNum = $f->{COMANS};

	#			while ( $f->{COMANS} == 0 ) {
				while ( $tSelNum == 0 ) {
					my $SelJud = &MsgBox("未选择物件","warning","yesno","没有选择任何物件,是否退出脚本?",);
					if( lc($SelJud) eq 'yes' ){
						exit(0);
						last;
					}
					#
					$f->MOUSE("r Please select the text box you want to enlarge.");
					my ($X1,$Y1,$X2,$Y2,) = split(/ /,$f->{MOUSEANS});
					$f->COM('filter_area_strt');
					$f->COM('filter_area_xy', x => $X1, y => $Y1);
					$f->COM('filter_area_xy', x => $X2, y => $Y2);
					$f->COM('filter_area_end', layer => '', filter_name => 'popup', operation => 'select', area_type => 'rectangle', inside_area => 'yes', intersect_area => 'no');
					$f->COM('get_select_count');
					$tSelNum = $f->{COMANS};
				}
			}
		}

		#获取框选区域的 物件的 LIMITS 和 物件FEATURES #获取最大线
		$f->COM('units', type => 'inch');

	#	my $MinLineSize = 0 ;
		my $MinLineSize = 3 ;
		my %AngleData;
		my %LineData;
		my $ArcMaxSize = 0 ;
		my ($RotationAngle,$RecoveryAngle);
		my $TypeMode = 'Arc';
		my ($LineExist,$ArcExist,$ZoomPlusMode,) = ('no','no','Normal',);
		my $ArcSelExcludeTol = 0.0002; #排除选择的弧 精度

		my $ReplaceMode = 'Normal';
		my $tMinLineSize = 100 ;
		
		my $CurrSelCount = $f->COM('get_select_count');

		my $tInfoFile = $ENV{GENESIS_TMP} . '/info.' . int(rand(9999));
		$f->COM ( 'info',out_file => $tInfoFile,args => " -t layer -e $JOB/$STEP/$WorkLayer -d FEATURES -o select" ) ;
		open ( FH,"<$tInfoFile" ) ;
		while ( <FH> ) {
			my $line = $_;
			my ( $Size,$Positive ) = (0,'N');
			my ( $Xs,$Ys,$Xe,$Ye );
			if ( $line =~ /\#L/ ) {
				#L 1.80117 8.85592 1.79867 8.85717 r4.5 P 19
				($Xs,$Ys,$Xe,$Ye,$Size,$Positive ) = ( split ( ' ',$line ) ) [1,2,3,4,5,6,];
				if ($Xs == $Xe ) {
					$AngleData{90}++;
					my $tLineLength = abs ($Ye - $Ys) ;
					$LineData{$tLineLength} = 90;
				} elsif ($Ys == $Ye ) {
					$AngleData{0}++;
					my $tLineLength = abs ($Xe - $Xs) ;
					$LineData{$tLineLength} = 0;
				} else {
					my $tLineAngle = atan2 ( $Ye - $Ys,$Xe - $Xs ) * 180 / pi;
					$AngleData{$tLineAngle}++;
					my $tLineLength = sqrt ( ( $Xs - $Xe ) ** 2 + ( $Ys - $Ye ) ** 2 ) ;
					$LineData{$tLineLength} = $tLineAngle;
					$ReplaceMode = 'Rotate';
				}
				$TypeMode = 'Line';
				$LineExist = 'yes';#判断有没有线
			}elsif ( $line =~ /\#A/ ) {
				#A 1.96316 9.02362 1.96316 9.02362 1.89566 9.02362 r12 P 12 Y
				( $Size,$Positive ) = ( split ( ' ',$line ) ) [7,8,];
				if ( $Positive eq 'P' ) {
					my $tSize = $Size;
						$tSize =~ s/r//;
					if ( $tSize > $ArcMaxSize ){
						$ArcMaxSize = $tSize ;
					}
					$ArcExist = 'yes';#判断有没有弧
				}
			}
			if ( $Positive eq 'P' ) {
				$Size =~ s/r//;
	#			if ( $Size > $MinLineSize ) {
				if ( $Size < $tMinLineSize ) {
					$tMinLineSize = $Size ;
				}
			}
		}
		close FH;
		unlink $tInfoFile;
		
		if ( ( $CurrSelCount >= 30 ) and ( $LineExist eq 'yes' ) ) {
			$ZoomPlusMode = 'Dense';
		}
		if ( ( $ArcExist eq 'yes' ) and ( $LineExist eq 'yes' ) ) {  #有弧有线才进行 特殊判断
			$ZoomPlusMode = 'None';
		}
		

		if ( $tMinLineSize != 100 and $tMinLineSize > $MinLineSize ) {
			$MinLineSize = $tMinLineSize;
		}

		my $MinLineSizeInch = $MinLineSize / 1000;

		if ( $tRunType eq 'ScaleX' or $tRunType eq 'ScaleY' ){
			$ReplaceMode = 'Rotate';
		}
		if ( $ReplaceMode eq 'Rotate' ) {
#			$f->PAUSE("sgdsgd=,");
			my @SortLength = sort { $a <=> $b }( keys %LineData );
			my $tLengthMax = $LineData{$SortLength[$#SortLength]};
			if ( $tLengthMax == 0 || $tLengthMax == 90 ){
				$ReplaceMode = 'Normal';
			} else {
				if ( $tLengthMax < 0 ) {
					$RotationAngle = $tLengthMax  + 360;
				}else{
					$RotationAngle = $tLengthMax ;
				}
				$RecoveryAngle = 360 - $RotationAngle ;
			}
#			my @SortAngle = sort { $AngleData{$a} <=> $AngleData{$b} }( keys %AngleData );
#			if ( $SortAngle[$#SortAngle] == 0 || $SortAngle[$#SortAngle] == 90 ){
#				$ReplaceMode = 'Normal';
#				my $tRotationAngle;
#				$f->PAUSE("@SortAngle,$AngleData{$SortAngle[$#SortAngle]} == $AngleData{$SortAngle[0]}");
				
#				if ( $AngleData{$SortAngle[$#SortAngle]} == $AngleData{$SortAngle[0]} ){
#					$f->PAUSE("01=,");
#					for my $tAngle ( @SortAngle ) {
#						if ( ( $tAngle % 90 ) != 0 ) {
#							$f->PAUSE("1=,");

#							$tRotationAngle = $tAngle;
#							$ReplaceMode = 'Rotate';
#							$f->PAUSE("2=,");
#							last;
#						}
#					}
#				}
#				if ( $ReplaceMode eq 'Rotate' ) {
#					if ( $tRotationAngle < 0 ) {
#						$RotationAngle = $tRotationAngle  + 360;
#					}else{
#						$RotationAngle = $tRotationAngle ;
#					}
#					$RecoveryAngle = 360 - $RotationAngle ;
#				}
#			} else {
#				if ( $SortAngle[$#SortAngle] < 0 ) {
#					$RotationAngle = $SortAngle[$#SortAngle]  + 360;
#				}else{
#					$RotationAngle = $SortAngle[$#SortAngle] ;
#				}
#				$RecoveryAngle = 360 - $RotationAngle ;
#			}
		}

		$f->COM('sel_options', clear_mode => 'clear_none', display_mode => 'displayed_layers', area_inout => 'inside', area_select => 'select', select_mode => 'standard', area_touching_mode => 'exclude');
		##########################################################################
#		$f->PAUSE("ReplaceMode=$ReplaceMode");
#$ReplaceMode = 'Normal';
		if ( $ReplaceMode eq 'Rotate' ) {
			my $ZoomJud = 'yes';
			my $TmpAttrStart = 'neo_silk-tmp1.' . int(rand(99999999));
			my $TmpAttrEnd = 'neo_silk-tmp2.' . int(rand(99999999));
			#不为0°或者不为90°则执行这一步

			#删除临时层别 $TmpLayers[0] $TmpLayers[1]
			my @TmpLayers = ($WorkLayer . '-silk_tmp1++',$WorkLayer . '-silk_tmp2++',);
			&DelLayers(@TmpLayers);

			#添加属性
			$f->COM('cur_atr_reset');
			$f->COM('cur_atr_set', attribute => '.string', text => $TmpAttrStart);
			$f->COM('sel_change_atr', mode => 'add');
			#复制到临时层$TmpLayers[0]
			$f->COM('get_select_count');
			if ( $f->{COMANS} != 0 ) {
				$f->COM('sel_copy_other', dest => 'layer_name', target_layer => $TmpLayers[0], invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0);
#				$f->PAUSE(0);

				#修改属性为后属性
#				$f->COM('sel_change_atr', mode => 'edit', attributes => '.string', attr_vals => $TmpAttrEnd);
				$f->COM('cur_atr_reset');
				$f->COM('cur_atr_set', attribute => '.string', text => $TmpAttrEnd);
				$f->COM('sel_change_atr', mode => 'add');

				#套层选择
				$f->COM('affected_layer', name => $WorkCoverLayer, mode => 'single', affected => 'yes');
				$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
				$f->COM('sel_ref_feat', layers => '', use => 'select', mode => 'touch', pads_as => 'shape', f_types => 'line;pad;surface;arc;text', polarity => 'positive;negative', include_syms => '', exclude_syms => '');


				$f->COM('get_select_count');
				if ( $f->{COMANS} != 0 ) {
					#添加属性
					$f->COM('cur_atr_reset');
					$f->COM('cur_atr_set', attribute => '.string', text => $TmpAttrStart);
					$f->COM('sel_change_atr', mode => 'add');
					#复制到临时层别2 $TmpLayers[1]

					$f->COM('sel_copy_other', dest => 'layer_name', target_layer => $TmpLayers[1], invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0);
					#删除属性
					$f->COM('sel_delete_atr', mode => 'list', attributes => '.string', attr_vals => $TmpAttrStart);
					$f->COM('affected_layer', name => $WorkCoverLayer, mode => 'single', affected => 'no');
					#勾选临时层别
					$f->COM('affected_layer', name => $TmpLayers[0], mode => 'single', affected => 'yes');
					$f->COM('affected_layer', name => $TmpLayers[1], mode => 'single', affected => 'yes');
					#通过属性选择
					$f->COM('set_filter_attributes', filter_name => 'popup', exclude_attributes => 'no', condition => 'yes', attribute => '.string', min_int_val => 0, max_int_val => 0, min_float_val => 0, max_float_val => 0, option => '', text => $TmpAttrStart);
					$f->COM('filter_area_strt');
					$f->COM('filter_area_end', filter_name => 'popup', operation => 'select');
					$f->COM('get_select_count');
					if ( $f->{COMANS} != 0 ) {
						#获取 $TmpLayers[0] 层别中心
						$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$TmpLayers[0]",data_type => 'LIMITS'
				#		,options => "select"
						);
						my $RotateCenterX = ($f->{doinfo}{gLIMITSxmax} + $f->{doinfo}{gLIMITSxmin} ) / 2 ;
						my $RotateCenterY = ($f->{doinfo}{gLIMITSymax} + $f->{doinfo}{gLIMITSymin} ) / 2 ;


						#旋转角度
						$f->COM('sel_transform', oper => 'rotate', x_anchor => $RotateCenterX , y_anchor => $RotateCenterY, angle => $RotationAngle, x_scale => 1, y_scale => 1, x_offset => 0, y_offset => 0, mode => 'anchor', duplicate => 'no');
						#清除选择
						$f->COM('sel_clear_feat');

						#框选$TmpLayers[0] +1mil 层区域
						$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$TmpLayers[0]",data_type => 'LIMITS'
				#		,options => "select"
						);

						my $tWorkLimitsMinX =  $f->{doinfo}{gLIMITSxmin};
						my $tWorkLimitsMinY =  $f->{doinfo}{gLIMITSymin};
						my $tWorkLimitsMaxX =  $f->{doinfo}{gLIMITSxmax};
						my $tWorkLimitsMaxY =  $f->{doinfo}{gLIMITSymax};


						my $WorkLimitsMinX =  $f->{doinfo}{gLIMITSxmin} + $MinLineSizeInch;
						my $WorkLimitsMinY =  $f->{doinfo}{gLIMITSymin} + $MinLineSizeInch;
						my $WorkLimitsMaxX =  $f->{doinfo}{gLIMITSxmax} - $MinLineSizeInch;
						my $WorkLimitsMaxY =  $f->{doinfo}{gLIMITSymax} - $MinLineSizeInch;

	#					$f->PAUSE(2);
						$f->COM('affected_layer', name => $TmpLayers[0], mode => 'single', affected => 'no');
	#					$f->COM('filter_area_strt');
	#				#	$f->COM('filter_area_xy', x => $WorkLimitsMinX - $BoxSelTol, y => $WorkLimitsMinY - $BoxSelTol);
	#				#	$f->COM('filter_area_xy', x => $WorkLimitsMaxX + $BoxSelTol, y => $WorkLimitsMaxY + $BoxSelTol);
	#					$f->COM('filter_area_xy', x => $f->{doinfo}{gLIMITSxmin} - $BoxSelTol, y => $f->{doinfo}{gLIMITSymin} - $BoxSelTol);
	#					$f->COM('filter_area_xy', x => $f->{doinfo}{gLIMITSxmax} + $BoxSelTol, y => $f->{doinfo}{gLIMITSymax} + $BoxSelTol);
	#					$f->COM('filter_area_end', layer => '', filter_name => 'popup', operation => 'select', area_type => 'rectangle', inside_area => 'yes', intersect_area => 'no');
	##					$f->PAUSE("3=$WorkLimitsMinX,$WorkLimitsMinY.$WorkLimitsMaxX.$WorkLimitsMaxY");
	#					$f->COM('sel_break');
						
	#					$f->PAUSE(3);



	#					$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$TmpLayers[1]",data_type => 'LIMITS',options => "select");
						$f->COM('filter_area_strt');
						$f->COM('filter_area_end', filter_name => 'popup', operation => 'select');
						
#						$f->COM('sel_options', clear_mode => 'clear_none', display_mode => 'displayed_layers', area_inout => 'inside', area_select => 'unselect', select_mode => 'standard', area_touching_mode => 'exclude');

						$f->COM('filter_area_strt');
						$f->COM('filter_area_xy', x => $f->{doinfo}{gLIMITSxmin} - $BoxSelTol, y => $f->{doinfo}{gLIMITSymin} - $BoxSelTol);
						$f->COM('filter_area_xy', x => $f->{doinfo}{gLIMITSxmax} + $BoxSelTol, y => $f->{doinfo}{gLIMITSymax} + $BoxSelTol);
						$f->COM('filter_area_end', layer => '', filter_name => 'popup', operation => 'unselect', area_type => 'rectangle', inside_area => 'yes', intersect_area => 'no');
						$f->COM('get_select_count');
						if ( $f->{COMANS} != 0 ) {
							$f->COM('sel_delete');
						}
#						$f->COM('sel_options', clear_mode => 'clear_none', display_mode => 'displayed_layers', area_inout => 'inside', area_select => 'select', select_mode => 'standard', area_touching_mode => 'exclude');

						$f->COM('filter_area_strt');
						$f->COM('filter_area_end', filter_name => 'popup', operation => 'select');
						$f->COM('get_select_count');
						if ( $f->{COMANS} != 0 ) {
							$f->COM('sel_break');
							$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$TmpLayers[1]",data_type => 'LIMITS');	
							$f->COM('undo', depth => 1);
						} else {
						
							$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$TmpLayers[1]",data_type => 'LIMITS');							
						}
						

						my $WorkCoverLimitsMinX =  $f->{doinfo}{gLIMITSxmin};
						my $WorkCoverLimitsMinY =  $f->{doinfo}{gLIMITSymin};
						my $WorkCoverLimitsMaxX =  $f->{doinfo}{gLIMITSxmax};
						my $WorkCoverLimitsMaxY =  $f->{doinfo}{gLIMITSymax};
	#					print "44=$TmpLayers[1],$f->{doinfo}{gLIMITSxmin},$f->{doinfo}{gLIMITSymin},$f->{doinfo}{gLIMITSxmax},$f->{doinfo}{gLIMITSymax}\n";
	#				$f->PAUSE("44=$TmpLayers[1],$f->{doinfo}{gLIMITSxmin},$f->{doinfo}{gLIMITSymin},$f->{doinfo}{gLIMITSxmax},$f->{doinfo}{gLIMITSymax}" );
						my $WorkCoverLimitsCenterX =  $WorkCoverLimitsMinX + ( $WorkCoverLimitsMaxX  - $WorkCoverLimitsMinX ) / 2 ;
						my $WorkCoverLimitsCenterY =  $WorkCoverLimitsMinY + ( $WorkCoverLimitsMaxY  - $WorkCoverLimitsMinY ) / 2 ;
						
						my ($tScaleX,$tScaleY,$tExpansionSize,) = (1,1,0,);

	##########################################################################################################################################################
			#			$f->PAUSE(01);
						if ( $tRunType =~ /^Scale/i ) {
#							$f->PAUSE("ZoomPlusMode=$ZoomPlusMode");
							if ( $ZoomPlusMode eq 'None' ) {
								$f->COM('affected_layer', name => $TmpLayers[1], mode => 'single', affected => 'no');
								
								$f->COM('affected_layer', name => $TmpLayers[0], mode => 'single', affected => 'yes');

								my ($WorkArcLimitsMinX,$WorkArcLimitsMinY,$WorkArcLimitsMaxX,$WorkArcLimitsMaxY,@WorkArcData);
								$f->COM('sel_clear_feat');
								$f->COM('reset_filter_criteria' ,filter_name => '' ,criteria => 'all');
								$f->COM('set_filter_type' ,filter_name => '' ,lines => 'yes' ,pads => 'no' ,surfaces => 'no' ,arcs => 'no' ,text => 'no');
								$f->COM('set_filter_attributes' ,filter_name => 'popup' ,exclude_attributes => 'no' ,condition => 'yes' ,attribute => '.string' ,min_int_val => 0 ,max_int_val => 0 ,min_float_val => 0 ,max_float_val => 0 ,option => '' ,text => $TmpAttrStart);
								$f->COM('filter_area_strt');
								$f->COM('filter_area_end' ,filter_name => 'popup' ,operation => 'select');
								$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$TmpLayers[0]",data_type => 'LIMITS',options => "select");
								my $WorkLineLimitsMinX =  $f->{doinfo}{gLIMITSxmin};
								my $WorkLineLimitsMinY =  $f->{doinfo}{gLIMITSymin};
								my $WorkLineLimitsMaxX =  $f->{doinfo}{gLIMITSxmax};
								my $WorkLineLimitsMaxY =  $f->{doinfo}{gLIMITSymax};
								
								$f->COM('sel_clear_feat');
								$f->COM('reset_filter_criteria' ,filter_name => '' ,criteria => 'all');
								$f->COM('set_filter_type' ,filter_name => '' ,lines => 'no' ,pads => 'no' ,surfaces => 'no' ,arcs => 'yes' ,text => 'no');
								$f->COM('set_filter_attributes' ,filter_name => 'popup' ,exclude_attributes => 'no' ,condition => 'yes' ,attribute => '.string' ,min_int_val => 0 ,max_int_val => 0 ,min_float_val => 0 ,max_float_val => 0 ,option => '' ,text => $TmpAttrStart);
								$f->COM('filter_area_strt');
								$f->COM('filter_area_end' ,filter_name => 'popup' ,operation => 'select');
#								$f->PAUSE("01,ZoomPlusMode=$ZoomPlusMode," . $f->COM('get_select_count'));

								$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$TmpLayers[0]",data_type => 'LIMITS',options => "select");
								my $WorkArcLimitsMinX =  $f->{doinfo}{gLIMITSxmin};
								my $WorkArcLimitsMinY =  $f->{doinfo}{gLIMITSymin};
								my $WorkArcLimitsMaxX =  $f->{doinfo}{gLIMITSxmax};
								my $WorkArcLimitsMaxY =  $f->{doinfo}{gLIMITSymax};
								
								my $tArcSelExcludeTol = ( $ArcMaxSize / 1000 ) / 2 + $ArcSelExcludeTol ;
								
								$f->COM('filter_area_strt');
								$f->COM('filter_area_xy' ,x => $WorkArcLimitsMinX + $tArcSelExcludeTol ,y => $WorkArcLimitsMinY + $tArcSelExcludeTol );
								$f->COM('filter_area_xy' ,x => $WorkArcLimitsMaxX - $tArcSelExcludeTol ,y => $WorkArcLimitsMaxY - $tArcSelExcludeTol );
								$f->COM('filter_area_end' ,layer => '' ,filter_name => 'popup' ,operation => 'unselect' ,area_type => 'rectangle' ,inside_area => 'yes' ,intersect_area => 'no');
#								$f->PAUSE("tArcSelExcludeTol=$tArcSelExcludeTol,02,ZoomPlusMode=$ZoomPlusMode," . $f->COM('get_select_count'));

								$f->COM('get_select_count');
								if ( $f->{COMANS} != 0 ) {
		#							$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$TmpLayers[0]",data_type => 'LIMITS',options => "select");
		#							$WorkArcLimitsMinX =  $f->{doinfo}{gLIMITSxmin};
		#							$WorkArcLimitsMinY =  $f->{doinfo}{gLIMITSymin};
		#							$WorkArcLimitsMaxX =  $f->{doinfo}{gLIMITSxmax};
		#							$WorkArcLimitsMaxY =  $f->{doinfo}{gLIMITSymax};
									my $tInfoFile = $ENV{GENESIS_TMP} . '/info.' . int(rand(9999));
									$f->COM ( 'info',out_file => $tInfoFile,args => " -t layer -e $JOB/$STEP/$TmpLayers[0] -d FEATURES -o select" ) ;
									open ( FH,"<$tInfoFile" ) ;
									@WorkArcData = <FH>;
#									$f->PAUSE("$#WorkArcData=@WorkArcData");
									close FH;
									unlink $tInfoFile;

									$f->COM('affected_layer', name => $TmpLayers[1], mode => 'single', affected => 'yes');

									$f->COM('reset_filter_criteria' ,filter_name => '' ,criteria => 'all');
									$f->COM('set_filter_polarity' ,filter_name => '' ,positive => 'yes' ,negative => 'no');
									$f->COM('sel_ref_feat' ,layers => $TmpLayers[1] ,use => 'select' ,mode => 'touch' ,pads_as => 'shape' ,f_types => 'line;pad;surface;arc;text' ,polarity => 'positive' ,include_syms => '' ,exclude_syms => '');
#									$f->PAUSE("03,ZoomPlusMode=$ZoomPlusMode," . $f->COM('get_select_count'));
									
									$f->COM('affected_layer', name => $TmpLayers[0], mode => 'single', affected => 'no');
									
									$f->COM('get_select_count');
									if ( $f->{COMANS} != 0 ) {
										my $tInfoFile = $ENV{GENESIS_TMP} . '/info.' . int(rand(9999));
										$f->COM ( 'info',out_file => $tInfoFile,args => " -t layer -e $JOB/$STEP/$TmpLayers[1] -d FEATURES -o select" ) ;

										open ( FH,"<$tInfoFile" ) ;
										while ( <FH> ) {
											my $line = $_;
											my ( $Size,$Positive ) = (0,'N');
											my ( $Xs,$Ys,$Xe,$Ye );
											if ( $line =~ /\#L/ ) {
												#L 1.80117 8.85592 1.79867 8.85717 r4.5 P 19
												( $Size,$Positive,) = ( split ( ' ',$line ) ) [5,6,];
												if ( $Positive eq 'P' ) {
													if ( $Size !~ /^r\d+/ ) {
														$ZoomPlusMode = 'Yes';
													}
												}
											}elsif ( $line =~ /\#P/ ) {
												#P 1.80155 0.28521 rect33.41x37.41 N 0 0 N
												#oval\d+ r\d+ el\d+
												( $Size,$Positive ) = ( split ( ' ',$line ) ) [3,4,];
												if ( $Positive eq 'P' ) {
													if ( $Size !~ /^r\d+/ and $Size !~ /^oval\d+/ and $Size !~ /^el\d+/ ) {
														$ZoomPlusMode = 'Yes';
													}
												}
											}elsif ( $line =~ /\#S/ ) {
												#S P 0
												#OB 0.17558996063 0.29443011811 I
												( $Positive ) = ( split ( ' ',$line ) ) [1,];
												if ( $Positive eq 'P' ) {
													$ZoomPlusMode = 'Yes';
												}
											}
										}
										close FH;
										unlink $tInfoFile;
										if ( $ZoomPlusMode ne 'Yes' ){
											$ZoomPlusMode = 'Normal';
		#								} else {
										
										}
									
									} else {
										$ZoomPlusMode = 'Normal';
									}
									$f->COM('sel_clear_feat');
								} else {
									$ZoomPlusMode = 'Normal';
								}
#								$f->PAUSE("2,ZoomPlusMode=$ZoomPlusMode");

								if ( $ZoomPlusMode eq 'Yes' ){	
									#分三种情况   Rotate
									#弧的Limits 在 线的Limits里面 正常缩放
									#弧的Limits 在 线的Limits外面 直接 以 长方向 线的Limits做缩放 + 弧的3/4 缩放 1/4
	#								my $OutsideFixFactor = 1 / 4;
	#								my $EqualFixFactor = 1 / 2;
									my $LimitsFixMin = 0.0025 ;
#									my $LimitsFixMin = 0.00001 ;
	#								my $OutsideFixFactor = 1 / 3;
	#								my $OutsideFixFactor = 1 / 3;
	#								my $OutsideFixFactor = 1 / 2;
#									#my $OutsideFixFactor = 3 / 5;
									my $OutsideFixFactor = 1 / 10;
	#								my $OutsideFixFactor = 1;
	#								my $OutsideFixFactor = 1 / 2;
	#								my $OutsideFixFactor = 1;
#									my $EqualFixFactor = 1 / 3;
#									my $EqualFixFactor = 1 / 12;
									my $EqualFixFactor = 1 / 6;
	#								my $OutsideFixFactor = 1 / 2;
	#								my $EqualFixFactor = 1 / 2;
									#弧的Limits =~ 线的Limits 直接 以 长方向 线的Limits做缩放 + 弧的1/2 缩放
									#弧的Limits =~ 线的Limits 直接 以 长方向 线的Limits做缩放 + 弧的1/2 缩放
									my $WorkToCoverMinX = $WorkCoverLimitsMinX - $WorkLimitsMinX ;
									my $WorkToCoverMinY = $WorkCoverLimitsMinY - $WorkLimitsMinY ;
									my $WorkToCoverMaxX = $WorkLimitsMaxX - $WorkCoverLimitsMaxX;
									my $WorkToCoverMaxY = $WorkLimitsMaxY - $WorkCoverLimitsMaxY;
									
									my $LimitsLineToArcMinX = $WorkArcLimitsMinX - $WorkLineLimitsMinX ;
									my $LimitsLineToArcMinY = $WorkArcLimitsMinY - $WorkLineLimitsMinY ;
									my $LimitsLineToArcMaxX = $WorkLineLimitsMaxX - $WorkArcLimitsMaxX ;
									my $LimitsLineToArcMaxY = $WorkLineLimitsMaxY - $WorkArcLimitsMaxY ;
									
									my $LimitsLineToCoverMinX = ( $WorkLineLimitsMinX + ( $MinLineSizeInch / 2 ) )  - $WorkCoverLimitsMinX ;
									my $LimitsLineToCoverMinY = ( $WorkLineLimitsMinY + ( $MinLineSizeInch / 2 ) )  - $WorkCoverLimitsMinY ;
									my $LimitsLineToCoverMaxX = $WorkCoverLimitsMaxX -  ( $WorkLineLimitsMaxX - ( $MinLineSizeInch / 2 ) ) ;
									my $LimitsLineToCoverMaxY = $WorkCoverLimitsMaxY -  ( $WorkLineLimitsMaxY - ( $MinLineSizeInch / 2 ) ) ;
	#								$f->PAUSE("WorkToCover:MinX,MinY,MaxX,MaxY=$WorkToCoverMinX,$WorkToCoverMinY,$WorkToCoverMaxX,$WorkToCoverMaxY\nLimitsLineToCover:MinX,MinY,MaxX,MaxY,=$LimitsLineToCoverMinX,$LimitsLineToCoverMinY,$LimitsLineToCoverMaxX,$LimitsLineToCoverMaxY,");
									
									my $CalcTol = 0.0005; #0.5mil
									my ($LineCmpArcMinX,$LineCmpArcMinY,$LineCmpArcMaxX,$LineCmpArcMaxY,) = ('Equal','Equal','Equal','Equal',);#弧Limits 在线Limits的范围.
									
									my ($LimitsOffsetOutLeft,$LimitsOffsetOutRight,$LimitsOffsetOutUp,$LimitsOffsetOutDown,) = (0,0,0,0,);#弧Limits 在线Limits的范围之外

									#'Equal', 'Outside' , 'Inside'
									if ( $LimitsLineToArcMinX < ( 0 - $CalcTol ) ) {
										$LineCmpArcMinX = 'Outside';
	#									$LimitsOffsetOutLeft =  abs ( $LimitsLineToArcMinX ) * $OutsideFixFactor ;
										$LimitsOffsetOutLeft =  abs ( $LimitsLineToCoverMinX ) * $OutsideFixFactor ;
										if ( $LimitsOffsetOutLeft < $LimitsFixMin ){
											$LimitsOffsetOutLeft = $LimitsFixMin;
										}
										if ( $WorkToCoverMinX > 0 ){
											$LimitsOffsetOutLeft += $WorkToCoverMinX;
										}
										
									} elsif ( $LimitsLineToArcMinX > $CalcTol ) {
										$LineCmpArcMinX = 'Inside';
									}
									
									if ( $LimitsLineToArcMinY < ( 0 - $CalcTol ) ) {
										$LineCmpArcMinY = 'Outside';
	#									$LimitsOffsetOutDown =  abs ( $LimitsLineToArcMinY ) * $OutsideFixFactor ;
										$LimitsOffsetOutDown =  abs ( $LimitsLineToCoverMinY ) * $OutsideFixFactor ;
										if ( $LimitsOffsetOutDown < $LimitsFixMin ){
											$LimitsOffsetOutDown = $LimitsFixMin;
										}
										if ( $WorkToCoverMinY > 0 ){
											$LimitsOffsetOutDown += $WorkToCoverMinY;
										}
									} elsif ( $LimitsLineToArcMinY > $CalcTol ) {
										$LineCmpArcMinY = 'Inside';
									}
									
									if ( $LimitsLineToArcMaxX < ( 0 - $CalcTol ) ) {
										$LineCmpArcMaxX = 'Outside';
	#									$LimitsOffsetOutRight =  abs ( $LimitsLineToArcMaxX ) * $OutsideFixFactor ;
										$LimitsOffsetOutRight =  abs ( $LimitsLineToCoverMaxX ) * $OutsideFixFactor ;
										if ( $LimitsOffsetOutRight < $LimitsFixMin ){
											$LimitsOffsetOutRight = $LimitsFixMin;
										}
										if ( $WorkToCoverMaxX > 0 ){
											$LimitsOffsetOutRight += $WorkToCoverMaxX;
										}
									} elsif ( $LimitsLineToArcMaxX > $CalcTol ) {
										$LineCmpArcMaxX = 'Inside';
									}
									
									if ( $LimitsLineToArcMaxY < ( 0 - $CalcTol ) ) {
										$LineCmpArcMaxY = 'Outside';
	#									$LimitsOffsetOutUp =  abs ( $LimitsLineToArcMaxY ) * $OutsideFixFactor ;
										$LimitsOffsetOutUp =  abs ( $LimitsLineToCoverMaxY ) * $OutsideFixFactor ;
										if ( $LimitsOffsetOutUp < $LimitsFixMin ){
											$LimitsOffsetOutUp = $LimitsFixMin;
										}
										if ( $WorkToCoverMaxY > 0 ){
											$LimitsOffsetOutUp += $WorkToCoverMaxY;
										}
									} elsif ( $LimitsLineToArcMaxY > $CalcTol ) {
										$LineCmpArcMaxY = 'Inside';
									}
									
									#############################
									my $LimitsLineCmpArcEqual = 'None';
									if ( ( $LineCmpArcMinX eq 'Equal' ) or ( $LineCmpArcMaxX eq 'Equal' ) ) {
										$LimitsLineCmpArcEqual = 'X';
									}
									
									if ( ( $LineCmpArcMinY eq 'Equal' ) or ( $LineCmpArcMaxY eq 'Equal' ) ) {
										if ( $LimitsLineCmpArcEqual eq 'None' ) {
											$LimitsLineCmpArcEqual = 'Y';
										} else {
											$LimitsLineCmpArcEqual = 'Both';
										}
									}
									#############################
									my $LimitsLineCmpArcOut = 'None';
									if ( ( $LineCmpArcMinX eq 'Outside' ) or ( $LineCmpArcMaxX eq 'Outside' ) ) {
										$LimitsLineCmpArcOut = 'X';
									}
									
									if ( ( $LineCmpArcMinY eq 'Outside' ) or ( $LineCmpArcMaxY eq 'Outside' ) ) {
										if ( $LimitsLineCmpArcOut eq 'None' ) {
											$LimitsLineCmpArcOut = 'Y';
										} else {
											$LimitsLineCmpArcOut = 'Both';
										}
									}
									
	#								$f->PAUSE("$LimitsOffsetOutLeft,$LimitsOffsetOutRight,$LimitsOffsetOutUp,$LimitsOffsetOutDown,");

#									$f->PAUSE("0,LimitsLineCmpArcEqual=$LimitsLineCmpArcEqual,LimitsLineCmpArcOut=$LimitsLineCmpArcOut");

									my $WorkLimitsCenterX =  $WorkLimitsMinX + ( $WorkLimitsMaxX  - $WorkLimitsMinX ) / 2 ;
									my $WorkLimitsCenterY =  $WorkLimitsMinY + ( $WorkLimitsMaxY  - $WorkLimitsMinY ) / 2 ;
									
									my ($LimitsOffsetEqualLeft,$LimitsOffsetEqualRight,$LimitsOffsetEqualUp,$LimitsOffsetEqualDown,) = (0,0,0,0,);#弧Limits =~ 线Limits
	#								$f->PAUSE("0,WorkArcData=@WorkArcData");

									for my $tLine ( @WorkArcData ){
										#A 6.084084 1.4956883 6.084084 1.4553318 6.084084 1.47551 r6 P 15 N
										#Arc,XS=6.084084,YS=1.4956883,XE=6.084084,YE=1.4553318,XC=6.084084,YC=1.47551,,D=0.0403565,r6,POS,CCW
	#									my $line = $_;
	#									$f->PAUSE("tLine=$tLine");
										my ( $Size,$Positive ) = (0,'N');
										my ( $Xs,$Ys,$Xe,$Ye,$Xc,$Yc,);
										if ( $tLine =~ /\#A/ ) {
											($Xs,$Ys,$Xe,$Ye,$Xc,$Yc,$Size,$Positive ) = ( split ( ' ',$tLine ) ) [1,2,3,4,5,6,7,8];
											if ( $Positive eq 'P' ){
	#											$f->PAUSE("2=$Xs,$Ys,$Xe,$Ye,$Xc,$Yc,$Size,$Positive");

												# 1 | 2
												# -----
												# 3 | 4
												## ($LineCmpArcMinX,$LineCmpArcMinY,$LineCmpArcMaxX,$LineCmpArcMaxY,) = ('Equal','Equal','Equal','Equal',);#弧Limits 在线Limits的范围.
												if ( $Yc > $WorkLimitsCenterY ) {  #1 2
													if ( $Xc > $WorkLimitsCenterX ) {  #2 #右 上
														if ( $LineCmpArcMaxX eq 'Equal' ) {  #右
															my $tFixFactor = abs ( $Xs - $Xe ) * $EqualFixFactor ;
															if ( $tFixFactor > $LimitsOffsetEqualRight){
																$LimitsOffsetEqualRight = $tFixFactor ;
															}
														}
													} else {  #1 #左 上
														if ( $LineCmpArcMinX eq 'Equal' ) {  #左
															my $tFixFactor = abs ( $Xs - $Xe ) * $EqualFixFactor ;
															if ( $tFixFactor > $LimitsOffsetEqualLeft){
																$LimitsOffsetEqualLeft = $tFixFactor ;
															}
														}
													}
													#
													if ( $LineCmpArcMaxY eq 'Equal' ) {  #上
														my $tFixFactor = abs ( $Ys - $Ye ) * $EqualFixFactor ;
														if ( $tFixFactor > $LimitsOffsetEqualUp){
															$LimitsOffsetEqualUp = $tFixFactor ;
														}
													}
												} else {  #3 4
													if ( $Xc > $WorkLimitsCenterX ) {  #4 #右 下
														if ( $LineCmpArcMaxX eq 'Equal' ) {  #右
															my $tFixFactor = abs ( $Xs - $Xe ) * $EqualFixFactor ;
															if ( $tFixFactor > $LimitsOffsetEqualRight){
																$LimitsOffsetEqualRight = $tFixFactor ;
															}
														}
													} else {  #3 #左 下
														if ( $LineCmpArcMinX eq 'Equal' ) {  #左
															my $tFixFactor = abs ( $Xs - $Xe ) * $EqualFixFactor ;
															if ( $tFixFactor > $LimitsOffsetEqualLeft){
																$LimitsOffsetEqualLeft = $tFixFactor ;
															}
														}
													}
													#
													if ( $LineCmpArcMinY eq 'Equal' ) {  #下
														my $tFixFactor = abs ( $Ys - $Ye ) * $EqualFixFactor ;
														if ( $tFixFactor > $LimitsOffsetEqualDown){
															$LimitsOffsetEqualDown = $tFixFactor ;
														}
													}
												}
											}
										}
									}
									
#									$f->PAUSE("0=$LimitsOffsetEqualLeft,$LimitsOffsetEqualDown,$LimitsOffsetEqualRight,$LimitsOffsetEqualUp,");

									if ( $LimitsLineCmpArcOut eq 'None' ) {
										if ( $LimitsLineCmpArcEqual eq 'X' ) {
											$WorkLimitsMinX +=  $LimitsOffsetEqualLeft	;
											$WorkLimitsMaxX -=  $LimitsOffsetEqualRight	;
										} elsif ( $LimitsLineCmpArcEqual eq 'Y' ) {
											$WorkLimitsMinY +=  $LimitsOffsetEqualDown	;
											$WorkLimitsMaxY -=  $LimitsOffsetEqualUp		;
										} elsif ( $LimitsLineCmpArcEqual eq 'Both' ) {
											if ( abs ( $WorkCoverLimitsMaxX - $WorkCoverLimitsMinX ) > abs ( $WorkCoverLimitsMaxY - $WorkCoverLimitsMinY ) ) {
												$WorkLimitsMinX +=  $LimitsOffsetEqualLeft	;
												$WorkLimitsMaxX -=  $LimitsOffsetEqualRight	;
											} else {
												$WorkLimitsMinY +=  $LimitsOffsetEqualDown	;
												$WorkLimitsMaxY -=  $LimitsOffsetEqualUp		;
											}
										}
									} else {
										if ( $LimitsLineCmpArcOut eq 'X' ) {
											my $tWorkToCover = ( abs ( $WorkLimitsMaxY - $WorkLimitsMinY )  - abs ( $WorkCoverLimitsMaxY - $WorkCoverLimitsMinY ) )  / 2;
											if ( $tWorkToCover > 0 ){
	#											$WorkLimitsMinX +=  $tWorkToCover;
	#											$WorkLimitsMaxX -=  $tWorkToCover;
												$WorkLimitsMinX -=  $tWorkToCover;
												$WorkLimitsMaxX +=  $tWorkToCover;
											}
										} elsif ( $LimitsLineCmpArcOut eq 'Y' ) {
											my $tWorkToCover = ( abs ( $WorkLimitsMaxX - $WorkLimitsMinX )  - abs ( $WorkCoverLimitsMaxX - $WorkCoverLimitsMinX ) )  / 2;
											if ( $tWorkToCover > 0 ){
	#											$WorkLimitsMinY +=  $tWorkToCover;
	#											$WorkLimitsMaxY -=  $tWorkToCover;
												$WorkLimitsMinY -=  $tWorkToCover;
												$WorkLimitsMaxY +=  $tWorkToCover;
											}
										}
										$WorkLimitsMinX +=  $LimitsOffsetOutLeft		;
										$WorkLimitsMinY +=  $LimitsOffsetOutDown		;
										$WorkLimitsMaxX -=  $LimitsOffsetOutRight		;
										$WorkLimitsMaxY -=  $LimitsOffsetOutUp			;
									}
									
									#$WorkLimitsMinX,$WorkLimitsMinY,$WorkLimitsMaxX,$WorkLimitsMaxY,
									#$WorkCoverLimitsMinX,$WorkCoverLimitsMinY,$WorkCoverLimitsMaxX,$WorkCoverLimitsMaxY,

									#分三种情况
									#弧的Limits 在 线的Limits里面 正常缩放
									#弧的Limits 在 线的Limits外面 直接 以 arc 在外的方向 Limits做缩放 + 弧的3/4 缩放
									#如果另一边本来就大 就加上大于多少就加多少.

									#弧的Limits =~ 线的Limits 直接 以 长方向 线的Limits做缩放 + 弧的1/2 缩放

									### Layer - c1-1 features data ###
									#S P 0
									#OB 0.17558996063 0.29443011811 I
									#OS 0.17558996063 0.29443011811
									#OE
									#L 1.8217282 0.2430339 1.8217282 0.2880063 r6 P 15 
									#A 1.8217282 0.2880063 1.7813718 0.2880063 1.80155 0.2880063 r6 P 15 N
									#P 1.80155 0.28521 rect33.41x37.41 N 0 0 N

								}
							} elsif ( $ZoomPlusMode eq 'Dense' ) {  #密集线组成的弧 #################################################################
								$f->COM('affected_layer', name => $TmpLayers[1], mode => 'single', affected => 'no');
								
								$f->COM('affected_layer', name => $TmpLayers[0], mode => 'single', affected => 'yes');

								my $DenseArcJudNum = 20; 
								my $DenseLengthTol = 0.002 ; #inch
								$f->COM('sel_clear_feat');
								$f->COM('reset_filter_criteria' ,filter_name => '' ,criteria => 'all');
								$f->COM('set_filter_type' ,filter_name => '' ,lines => 'yes' ,pads => 'no' ,surfaces => 'no' ,arcs => 'no' ,text => 'no');
								$f->COM('set_filter_polarity' ,filter_name => '' ,positive => 'yes' ,negative => 'no');
								$f->COM('set_filter_attributes' ,filter_name => 'popup' ,exclude_attributes => 'no' ,condition => 'yes' ,attribute => '.string' ,min_int_val => 0 ,max_int_val => 0 ,min_float_val => 0 ,max_float_val => 0 ,option => '' ,text => $TmpAttrStart);

								$f->COM('set_filter_length' ,slot => 'lines' ,min_length => 0 ,max_length => 0.002);
								$f->COM('filter_area_strt');
								$f->COM('filter_area_end' ,filter_name => 'popup' ,operation => 'select');
								$f->COM('set_filter_length');
								$f->COM('adv_filter_reset');
								$f->COM('get_select_count');
	#							if ( $f->{COMANS} != 0 ) {
								if ( $f->{COMANS} > $DenseArcJudNum ) {
									$f->COM('cur_atr_reset');
									$f->COM('cur_atr_set', attribute => '.bit', text => $TmpAttrStart);
									$f->COM('sel_change_atr', mode => 'add');
#									$f->COM('set_filter_length');
	#								$f->COM('set_filter_angle');
#									$f->COM('adv_filter_reset');
									my ($WorkDenseLimitsMinX,$WorkDenseLimitsMinY,$WorkDenseLimitsMaxX,$WorkDenseLimitsMaxY,@WorkDenseData);
									$f->COM('sel_clear_feat');
	#								$f->COM('reset_filter_criteria' ,filter_name => '' ,criteria => 'all');
	#								$f->COM('set_filter_type' ,filter_name => '' ,lines => 'yes' ,pads => 'no' ,surfaces => 'no' ,arcs => 'no' ,text => 'no');
	#								$f->COM('set_filter_attributes' ,filter_name => 'popup' ,exclude_attributes => 'no' ,condition => 'yes' ,attribute => '.string' ,min_int_val => 0 ,max_int_val => 0 ,min_float_val => 0 ,max_float_val => 0 ,option => '' ,text => $TmpAttrStart);
	#								$f->COM('filter_area_strt');
	#								$f->COM('filter_area_end' ,filter_name => 'popup' ,operation => 'select');
									
									$f->COM('reset_filter_criteria' ,filter_name => '' ,criteria => 'all');
									$f->COM('set_filter_type' ,filter_name => '' ,lines => 'yes' ,pads => 'no' ,surfaces => 'no' ,arcs => 'no' ,text => 'no');
									$f->COM('set_filter_polarity' ,filter_name => '' ,positive => 'yes' ,negative => 'no');
									$f->COM('set_filter_attributes' ,filter_name => 'popup' ,exclude_attributes => 'no' ,condition => 'yes' ,attribute => '.string' ,min_int_val => 0 ,max_int_val => 0 ,min_float_val => 0 ,max_float_val => 0 ,option => '' ,text => $TmpAttrStart);
									$f->COM('set_filter_attributes' ,filter_name => 'popup' ,exclude_attributes => 'yes' ,condition => 'yes' ,attribute => '.bit' ,min_int_val => 0 ,max_int_val => 0 ,min_float_val => 0 ,max_float_val => 0 ,option => '' ,text => $TmpAttrStart);
									$f->COM('filter_area_strt');
									$f->COM('filter_area_end' ,filter_name => 'popup' ,operation => 'select');
#									$f->PAUSE("1,line");

									$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$TmpLayers[0]",data_type => 'LIMITS',options => "select");
									my $WorkLineLimitsMinX =  $f->{doinfo}{gLIMITSxmin};
									my $WorkLineLimitsMinY =  $f->{doinfo}{gLIMITSymin};
									my $WorkLineLimitsMaxX =  $f->{doinfo}{gLIMITSxmax};
									my $WorkLineLimitsMaxY =  $f->{doinfo}{gLIMITSymax};
									
									$f->COM('sel_clear_feat');
	#								$f->COM('reset_filter_criteria' ,filter_name => '' ,criteria => 'all');
	#								$f->COM('set_filter_type' ,filter_name => '' ,lines => 'no' ,pads => 'no' ,surfaces => 'no' ,arcs => 'yes' ,text => 'no');
	#								$f->COM('set_filter_attributes' ,filter_name => 'popup' ,exclude_attributes => 'no' ,condition => 'yes' ,attribute => '.string' ,min_int_val => 0 ,max_int_val => 0 ,min_float_val => 0 ,max_float_val => 0 ,option => '' ,text => $TmpAttrStart);
	#								$f->COM('filter_area_strt');
	#								$f->COM('filter_area_end' ,filter_name => 'popup' ,operation => 'select');

									$f->COM('reset_filter_criteria' ,filter_name => '' ,criteria => 'all');
									$f->COM('set_filter_type' ,filter_name => '' ,lines => 'yes' ,pads => 'no' ,surfaces => 'no' ,arcs => 'no' ,text => 'no');
									$f->COM('set_filter_polarity' ,filter_name => '' ,positive => 'yes' ,negative => 'no');
									$f->COM('set_filter_attributes' ,filter_name => 'popup' ,exclude_attributes => 'no' ,condition => 'yes' ,attribute => '.bit' ,min_int_val => 0 ,max_int_val => 0 ,min_float_val => 0 ,max_float_val => 0 ,option => '' ,text => $TmpAttrStart);
									$f->COM('filter_area_strt');
									$f->COM('filter_area_end' ,filter_name => 'popup' ,operation => 'select');
#									$f->PAUSE("1,ddd");
		#							$f->PAUSE("01,ZoomPlusMode=$ZoomPlusMode," . $f->COM('get_select_count'));
									$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$TmpLayers[0]",data_type => 'LIMITS',options => "select");
									my $WorkDenseLimitsMinX =  $f->{doinfo}{gLIMITSxmin};
									my $WorkDenseLimitsMinY =  $f->{doinfo}{gLIMITSymin};
									my $WorkDenseLimitsMaxX =  $f->{doinfo}{gLIMITSxmax};
									my $WorkDenseLimitsMaxY =  $f->{doinfo}{gLIMITSymax};
									
	#								my $tDenseSelExcludeTol = ( $DenseMaxSize / 1000 ) / 2 + $DenseSelExcludeTol ;
	#								$f->COM('filter_area_strt');
	#								$f->COM('filter_area_xy' ,x => $WorkDenseLimitsMinX + $tDenseSelExcludeTol ,y => $WorkDenseLimitsMinY + $tDenseSelExcludeTol );
	#								$f->COM('filter_area_xy' ,x => $WorkDenseLimitsMaxX - $tDenseSelExcludeTol ,y => $WorkDenseLimitsMaxY - $tDenseSelExcludeTol );
	#								$f->COM('filter_area_end' ,layer => '' ,filter_name => 'popup' ,operation => 'unselect' ,area_type => 'rectangle' ,inside_area => 'yes' ,intersect_area => 'no');
	#								$f->PAUSE("tDenseSelExcludeTol=$tDenseSelExcludeTol,02,ZoomPlusMode=$ZoomPlusMode," . $f->COM('get_select_count'));

									$f->COM('get_select_count');
									if ( $f->{COMANS} != 0 ) {
			#							$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$TmpLayers[0]",data_type => 'LIMITS',options => "select");
			#							$WorkDenseLimitsMinX =  $f->{doinfo}{gLIMITSxmin};
			#							$WorkDenseLimitsMinY =  $f->{doinfo}{gLIMITSymin};
			#							$WorkDenseLimitsMaxX =  $f->{doinfo}{gLIMITSxmax};
			#							$WorkDenseLimitsMaxY =  $f->{doinfo}{gLIMITSymax};
#										my $tInfoFile = $ENV{GENESIS_TMP} . '/info.' . int(rand(9999));
#										$f->COM ( 'info',out_file => $tInfoFile,args => " -t layer -e $JOB/$STEP/$TmpLayers[0] -d FEATURES -o select" ) ;
#										open ( FH,"<$tInfoFile" ) ;
#										@WorkDenseData = <FH>;
#		#								$f->PAUSE("$#WorkDenseData=@WorkDenseData");
#										close FH;
#										unlink $tInfoFile;

										$f->COM('affected_layer', name => $TmpLayers[1], mode => 'single', affected => 'yes');

										$f->COM('reset_filter_criteria' ,filter_name => '' ,criteria => 'all');
										$f->COM('set_filter_polarity' ,filter_name => '' ,positive => 'yes' ,negative => 'no');
										$f->COM('sel_ref_feat' ,layers => $TmpLayers[1] ,use => 'select' ,mode => 'touch' ,pads_as => 'shape' ,f_types => 'line;pad;surface;arc;text' ,polarity => 'positive' ,include_syms => '' ,exclude_syms => '');
	#									$f->PAUSE("03,ZoomPlusMode=$ZoomPlusMode," . $f->COM('get_select_count'));

										$f->COM('affected_layer', name => $TmpLayers[0], mode => 'single', affected => 'no');

										$f->COM('get_select_count');
										if ( $f->{COMANS} != 0 ) {
											my $tInfoFile = $ENV{GENESIS_TMP} . '/info.' . int(rand(9999));
											$f->COM ( 'info',out_file => $tInfoFile,args => " -t layer -e $JOB/$STEP/$TmpLayers[1] -d FEATURES -o select" ) ;
											open ( FH,"<$tInfoFile" ) ;
											while ( <FH> ) {
												my $line = $_;
												my ( $Size,$Positive ) = (0,'N');
												my ( $Xs,$Ys,$Xe,$Ye );
												if ( $line =~ /\#L/ ) {
													#L 1.80117 8.85592 1.79867 8.85717 r4.5 P 19
													( $Size,$Positive,) = ( split ( ' ',$line ) ) [5,6,];
													if ( $Positive eq 'P' ) {
														if ( $Size !~ /^r\d+/ ) {
															$ZoomPlusMode = 'Yes';
														}
													}
												}elsif ( $line =~ /\#P/ ) {
													#P 1.80155 0.28521 rect33.41x37.41 N 0 0 N
													#oval\d+ r\d+ el\d+
													( $Size,$Positive ) = ( split ( ' ',$line ) ) [3,4,];
													if ( $Positive eq 'P' ) {
														if ( $Size !~ /^r\d+/ and $Size !~ /^oval\d+/ and $Size !~ /^el\d+/ ) {
															$ZoomPlusMode = 'Yes';
														}
													}
												}elsif ( $line =~ /\#S/ ) {
													#S P 0
													#OB 0.17558996063 0.29443011811 I
													( $Positive ) = ( split ( ' ',$line ) ) [1,];
													if ( $Positive eq 'P' ) {
														$ZoomPlusMode = 'Yes';
													}
												}
											}
											close FH;
											unlink $tInfoFile;
											if ( $ZoomPlusMode ne 'Yes' ){
												$ZoomPlusMode = 'Normal';
			#								} else {
											
											}
										
										} else {
											$ZoomPlusMode = 'Normal';
										}
										$f->COM('sel_clear_feat');
									} else {
										$ZoomPlusMode = 'Normal';
									}
#									$f->PAUSE("2,ZoomPlusMode=$ZoomPlusMode");
									if ( $ZoomPlusMode eq 'Yes' ){	
										#分三种情况
										#弧的Limits 在 线的Limits里面 正常缩放
										#弧的Limits 在 线的Limits外面 直接 以 长方向 线的Limits做缩放 + 弧的3/4 缩放 1/4
		#								my $OutsideFixFactor = 1 / 4;
		#								my $EqualFixFactor = 1 / 2;
										my $LimitsFixMin = 0.0025 ;
		#								my $OutsideFixFactor = 1 / 3;
		#								my $OutsideFixFactor = 1 / 3;
	#									my $OutsideFixFactor = 1 / 2;
	#									my $OutsideFixFactor = 3 / 5;
										my $OutsideFixFactor = 1 / 3;
	#									my $OutsideFixFactor = 13 / 36;
		#								my $OutsideFixFactor = 1;
		#								my $OutsideFixFactor = 1 / 2;
		#								my $OutsideFixFactor = 1;
#										my $EqualFixFactor = 1 / 3;
										my $EqualFixFactor = 1 / 6;
#										my $EqualFixFactor = 1 / 12;
		#								my $OutsideFixFactor = 1 / 2;
		#								my $EqualFixFactor = 1 / 2;
										#弧的Limits =~ 线的Limits 直接 以 长方向 线的Limits做缩放 + 弧的1/2 缩放
										#弧的Limits =~ 线的Limits 直接 以 长方向 线的Limits做缩放 + 弧的1/2 缩放
										
										my $WorkToCoverMinX = $WorkCoverLimitsMinX - $WorkLimitsMinX ;
										my $WorkToCoverMinY = $WorkCoverLimitsMinY - $WorkLimitsMinY ;
										my $WorkToCoverMaxX = $WorkLimitsMaxX - $WorkCoverLimitsMaxX;
										my $WorkToCoverMaxY = $WorkLimitsMaxY - $WorkCoverLimitsMaxY;
										
										my $LimitsLineToDenseMinX = $WorkDenseLimitsMinX - $WorkLineLimitsMinX ;
										my $LimitsLineToDenseMinY = $WorkDenseLimitsMinY - $WorkLineLimitsMinY ;
										my $LimitsLineToDenseMaxX = $WorkLineLimitsMaxX - $WorkDenseLimitsMaxX ;
										my $LimitsLineToDenseMaxY = $WorkLineLimitsMaxY - $WorkDenseLimitsMaxY ;
										
										my $LimitsLineToCoverMinX = ( $WorkLineLimitsMinX + ( $MinLineSizeInch / 2 ) )  - $WorkCoverLimitsMinX ;
										my $LimitsLineToCoverMinY = ( $WorkLineLimitsMinY + ( $MinLineSizeInch / 2 ) )  - $WorkCoverLimitsMinY ;
										my $LimitsLineToCoverMaxX = $WorkCoverLimitsMaxX -  ( $WorkLineLimitsMaxX - ( $MinLineSizeInch / 2 ) ) ;
										my $LimitsLineToCoverMaxY = $WorkCoverLimitsMaxY -  ( $WorkLineLimitsMaxY - ( $MinLineSizeInch / 2 ) ) ;
											
										my $CalcTol = 0.0005; #0.5mil
										my ($LineCmpDenseMinX,$LineCmpDenseMinY,$LineCmpDenseMaxX,$LineCmpDenseMaxY,) = ('Equal','Equal','Equal','Equal',);#弧Limits 在线Limits的范围.
										
										my ($LimitsOffsetOutLeft,$LimitsOffsetOutRight,$LimitsOffsetOutUp,$LimitsOffsetOutDown,) = (0,0,0,0,);#弧Limits 在线Limits的范围之外

										#'Equal', 'Outside' , 'Inside'
										if ( $LimitsLineToDenseMinX < ( 0 - $CalcTol ) ) {
											$LineCmpDenseMinX = 'Outside';
	#										$LimitsOffsetOutLeft =  abs ( $LimitsLineToDenseMinX ) * $OutsideFixFactor ;
											$LimitsOffsetOutLeft =  abs ( $LimitsLineToCoverMinX ) * $OutsideFixFactor ;
											if ( $LimitsOffsetOutLeft < $LimitsFixMin ){
												$LimitsOffsetOutLeft = $LimitsFixMin;
											}
											if ( $WorkToCoverMinX > 0 ){
												$LimitsOffsetOutLeft += $WorkToCoverMinX;
											}
											
										} elsif ( $LimitsLineToDenseMinX > $CalcTol ) {
											$LineCmpDenseMinX = 'Inside';
										}
										
										if ( $LimitsLineToDenseMinY < ( 0 - $CalcTol ) ) {
											$LineCmpDenseMinY = 'Outside';
	#										$LimitsOffsetOutDown =  abs ( $LimitsLineToDenseMinY ) * $OutsideFixFactor ;
											$LimitsOffsetOutDown =  abs ( $LimitsLineToCoverMinY ) * $OutsideFixFactor ;
											if ( $LimitsOffsetOutDown < $LimitsFixMin ){
												$LimitsOffsetOutDown = $LimitsFixMin;
											}
											if ( $WorkToCoverMinY > 0 ){
												$LimitsOffsetOutDown += $WorkToCoverMinY;
											}

										} elsif ( $LimitsLineToDenseMinY > $CalcTol ) {
											$LineCmpDenseMinY = 'Inside';
										}
										
										if ( $LimitsLineToDenseMaxX < ( 0 - $CalcTol ) ) {
											$LineCmpDenseMaxX = 'Outside';
	#										$LimitsOffsetOutRight =  abs ( $LimitsLineToDenseMaxX ) * $OutsideFixFactor ;
											$LimitsOffsetOutRight =  abs ( $LimitsLineToCoverMaxX ) * $OutsideFixFactor ;
											if ( $LimitsOffsetOutRight < $LimitsFixMin ){
												$LimitsOffsetOutRight = $LimitsFixMin;
											}
											if ( $WorkToCoverMaxX > 0 ){
												$LimitsOffsetOutRight += $WorkToCoverMaxX;
											}

										} elsif ( $LimitsLineToDenseMaxX > $CalcTol ) {
											$LineCmpDenseMaxX = 'Inside';
										}
										
										if ( $LimitsLineToDenseMaxY < ( 0 - $CalcTol ) ) {
											$LineCmpDenseMaxY = 'Outside';
	#										$LimitsOffsetOutUp =  abs ( $LimitsLineToDenseMaxY ) * $OutsideFixFactor ;
											$LimitsOffsetOutUp =  abs ( $LimitsLineToCoverMaxY ) * $OutsideFixFactor ;
											if ( $LimitsOffsetOutUp < $LimitsFixMin ){
												$LimitsOffsetOutUp = $LimitsFixMin;
											}
											if ( $WorkToCoverMaxY > 0 ){
												$LimitsOffsetOutUp += $WorkToCoverMaxY;
											}
											
										} elsif ( $LimitsLineToDenseMaxY > $CalcTol ) {
											$LineCmpDenseMaxY = 'Inside';
										}
										
										#############################
										my $LimitsLineCmpDenseEqual = 'None';
										if ( ( $LineCmpDenseMinX eq 'Equal' ) or ( $LineCmpDenseMaxX eq 'Equal' ) ) {
											$LimitsLineCmpDenseEqual = 'X';
										}
										
										if ( ( $LineCmpDenseMinY eq 'Equal' ) or ( $LineCmpDenseMaxY eq 'Equal' ) ) {
											if ( $LimitsLineCmpDenseEqual eq 'None' ) {
												$LimitsLineCmpDenseEqual = 'Y';
											} else {
												$LimitsLineCmpDenseEqual = 'Both';
											}
										}
										#############################
										my $LimitsLineCmpDenseOut = 'None';
										if ( ( $LineCmpDenseMinX eq 'Outside' ) or ( $LineCmpDenseMaxX eq 'Outside' ) ) {
											$LimitsLineCmpDenseOut = 'X';
										}
										
										if ( ( $LineCmpDenseMinY eq 'Outside' ) or ( $LineCmpDenseMaxY eq 'Outside' ) ) {
											if ( $LimitsLineCmpDenseOut eq 'None' ) {
												$LimitsLineCmpDenseOut = 'Y';
											} else {
												$LimitsLineCmpDenseOut = 'Both';
											}
										}
										
	#									$f->PAUSE("0,LimitsLineCmpDenseEqual=$LimitsLineCmpDenseEqual,LimitsLineCmpDenseOut=$LimitsLineCmpDenseOut");

										my $WorkLimitsCenterX =  $WorkLimitsMinX + ( $WorkLimitsMaxX  - $WorkLimitsMinX ) / 2 ;
										my $WorkLimitsCenterY =  $WorkLimitsMinY + ( $WorkLimitsMaxY  - $WorkLimitsMinY ) / 2 ;
										
										my ($LimitsOffsetEqualLeft,$LimitsOffsetEqualRight,$LimitsOffsetEqualUp,$LimitsOffsetEqualDown,) = (0,0,0,0,);#弧Limits =~ 线Limits
	#									$f->PAUSE("0,WorkDenseData=@WorkDenseData");

										if ( $LineCmpDenseMaxY eq 'Equal' ) {  #上
											$LimitsOffsetEqualUp = $LimitsFixMin ;
											if ( $WorkToCoverMaxY > 0 ){
												$LimitsOffsetEqualUp += $WorkToCoverMaxY ;
											}
										}
										if ( $LineCmpDenseMinY eq 'Equal' ) {  #下
											$LimitsOffsetEqualDown = $LimitsFixMin ;
											if ( $WorkToCoverMinY > 0 ){
												$LimitsOffsetEqualDown += $WorkToCoverMinY ;
											}
										}
										if ( $LineCmpDenseMinX eq 'Equal' ) {  #左
											$LimitsOffsetEqualLeft = $LimitsFixMin ;
											if ( $WorkToCoverMinX > 0 ){
												$LimitsOffsetEqualLeft += $WorkToCoverMinX ;
											}
										}
										if ( $LineCmpDenseMaxX eq 'Equal' ) {  #右
											$LimitsOffsetEqualRight = $LimitsFixMin ;
											if ( $WorkToCoverMaxX > 0 ){
												$LimitsOffsetEqualRight += $WorkToCoverMaxX ;
											}
										}

#										$f->PAUSE("0=$LimitsOffsetEqualLeft,$LimitsOffsetEqualDown,$LimitsOffsetEqualRight,$LimitsOffsetEqualUp,");
#										$f->PAUSE("LimitsLineCmpDenseEqual=$LimitsLineCmpDenseEqual,");
										
										if ( $LimitsLineCmpDenseOut eq 'None' ) {
											if ( $LimitsLineCmpDenseEqual eq 'X' ) {
												$WorkLimitsMinX +=  $LimitsOffsetEqualLeft	;
												$WorkLimitsMaxX -=  $LimitsOffsetEqualRight	;
											} elsif ( $LimitsLineCmpDenseEqual eq 'Y' ) {
												$WorkLimitsMinY +=  $LimitsOffsetEqualDown	;
												$WorkLimitsMaxY -=  $LimitsOffsetEqualUp		;
											} elsif ( $LimitsLineCmpDenseEqual eq 'Both' ) {
												if ( abs ( $WorkCoverLimitsMaxX - $WorkCoverLimitsMinX ) > abs ( $WorkCoverLimitsMaxY - $WorkCoverLimitsMinY ) ) {
													$WorkLimitsMinX +=  $LimitsOffsetEqualLeft	;
													$WorkLimitsMaxX -=  $LimitsOffsetEqualRight	;
												} else {
													$WorkLimitsMinY +=  $LimitsOffsetEqualDown	;
													$WorkLimitsMaxY -=  $LimitsOffsetEqualUp		;
												}
											}
										} else {
											if ( $LimitsLineCmpDenseOut eq 'X' ) {
												my $tWorkToCover = ( abs ( $WorkLimitsMaxY - $WorkLimitsMinY )  - abs ( $WorkCoverLimitsMaxY - $WorkCoverLimitsMinY ) )  / 2;
												if ( $tWorkToCover > 0 ){
													$WorkLimitsMinX +=  $tWorkToCover;
													$WorkLimitsMaxX -=  $tWorkToCover;
												}
											} elsif ( $LimitsLineCmpDenseOut eq 'Y' ) {
												my $tWorkToCover = ( abs ( $WorkLimitsMaxX - $WorkLimitsMinX )  - abs ( $WorkCoverLimitsMaxX - $WorkCoverLimitsMinX ) )  / 2;
												if ( $tWorkToCover > 0 ){
													$WorkLimitsMinY +=  $tWorkToCover;
													$WorkLimitsMaxY -=  $tWorkToCover;
												}
											}
											$WorkLimitsMinX +=  $LimitsOffsetOutLeft		;
											$WorkLimitsMinY +=  $LimitsOffsetOutDown		;
											$WorkLimitsMaxX -=  $LimitsOffsetOutRight		;
											$WorkLimitsMaxY -=  $LimitsOffsetOutUp			;
										}
									}
								} else {
									$ZoomPlusMode = 'Normal';
								}
							}
						}
#						$f->COM('reset_filter_criteria' ,filter_name => '' ,criteria => 'all');
						$f->COM('set_filter_length');
						$f->COM('adv_filter_reset');
						$f->COM('set_filter_attributes', filter_name => 'popup', exclude_attributes => 'no', condition => 'yes', attribute => '.string', min_int_val => 0, max_int_val => 0, min_float_val => 0, max_float_val => 0, option => '', text => $TmpAttrStart);
#						$f->PAUSE("gngh");
	##########################################################################################################################################################



						if ( $tRunType eq 'Scale' ){
							my $tTmpScaleX1 = abs($WorkCoverLimitsCenterX - $WorkCoverLimitsMinX) / abs($WorkCoverLimitsCenterX - $WorkLimitsMinX);
							my $tTmpScaleX2 = abs($WorkCoverLimitsCenterX - $WorkCoverLimitsMaxX) / abs($WorkCoverLimitsCenterX - $WorkLimitsMaxX);
							if ($tTmpScaleX1 > $tScaleX ){
								$tScaleX = $tTmpScaleX1;
							}
							if ($tTmpScaleX2 > $tScaleX ){
								$tScaleX = $tTmpScaleX2;
							}
							my $tTmpScaleY1 = abs($WorkCoverLimitsCenterY - $WorkCoverLimitsMinY) / abs($WorkCoverLimitsCenterY - $WorkLimitsMinY);
							my $tTmpScaleY2 = abs($WorkCoverLimitsCenterY - $WorkCoverLimitsMaxY) / abs($WorkCoverLimitsCenterY - $WorkLimitsMaxY);
							if ($tTmpScaleY1 > $tScaleY ){
								$tScaleY = $tTmpScaleY1;
							}
							if ($tTmpScaleY2 > $tScaleY ){
								$tScaleY = $tTmpScaleY2;
							}
						} elsif ( $tRunType eq 'Expansion' ){
							my $tTmpDistanceX1 = abs($WorkCoverLimitsCenterX - $WorkCoverLimitsMinX) - abs($WorkCoverLimitsCenterX - $WorkLimitsMinX);
							my $tTmpDistanceX2 = abs($WorkCoverLimitsCenterX - $WorkCoverLimitsMaxX) - abs($WorkCoverLimitsCenterX - $WorkLimitsMaxX);
							my $tTmpDistanceY1 = abs($WorkCoverLimitsCenterY - $WorkCoverLimitsMinY) - abs($WorkCoverLimitsCenterY - $WorkLimitsMinY);
							my $tTmpDistanceY2 = abs($WorkCoverLimitsCenterY - $WorkCoverLimitsMaxY) - abs($WorkCoverLimitsCenterY - $WorkLimitsMaxY);
							my @SortDistance = sort { $a <=> $b }($tTmpDistanceX1,$tTmpDistanceX2,$tTmpDistanceY1,$tTmpDistanceY2,);
							$tExpansionSize = $SortDistance[$#SortDistance] * 2 * 1000;
						}
#											$f->PAUSE("5=x_scale => $tScaleX, y_scale => $tScaleY," );
						if ( ( $tRunType =~ /^Scale/i and $tScaleX == 1 and $tScaleY == 1 ) or ( $tRunType eq 'Expansion' and $tExpansionSize == 0 ) ) {
							$ZoomJud = 'no';
						}
#						$f->PAUSE(3);
						
						if ( $ZoomJud eq 'yes' ) {
#							$f->COM('undo', depth => 1);

							$f->COM('affected_layer', name => $TmpLayers[1], mode => 'single', affected => 'no');
							$f->COM('affected_layer', name => $TmpLayers[0], mode => 'single', affected => 'yes');

							$f->COM('filter_area_strt');
							$f->COM('filter_area_xy', x => $tWorkLimitsMinX - $BoxSelTol, y => $tWorkLimitsMinY - $BoxSelTol);
							$f->COM('filter_area_xy', x => $tWorkLimitsMaxX + $BoxSelTol, y => $tWorkLimitsMaxY + $BoxSelTol);
		#					$f->COM('filter_area_xy', x => $f->{doinfo}{gLIMITSxmin} - $BoxSelTol, y => $f->{doinfo}{gLIMITSymin} - $BoxSelTol);
		#					$f->COM('filter_area_xy', x => $f->{doinfo}{gLIMITSxmax} + $BoxSelTol, y => $f->{doinfo}{gLIMITSymax} + $BoxSelTol);
							$f->COM('filter_area_end', layer => '', filter_name => 'popup', operation => 'select', area_type => 'rectangle', inside_area => 'yes', intersect_area => 'no');
#							$f->PAUSE("dgd");
							my $ExpansionFailure = 'no';
							if ( $tRunType eq 'Scale' ){
								$f->COM('sel_transform', x_anchor => $WorkCoverLimitsCenterX, y_anchor => $WorkCoverLimitsCenterY, x_scale => $tScaleX, y_scale => $tScaleY, oper => 'scale', angle => 0, direction => 'ccw', x_offset => 0, y_offset => 0, mode => 'anchor', duplicate => 'no');
							} elsif ( $tRunType eq 'Expansion' ){
								$f->VOF;
								if ( $tExpansionSize != 0 ) {
									$f->COM('sel_resize_poly' ,size => $tExpansionSize);
									my $STATUS = $f->{STATUS};
									if ( $STATUS != 0 ) {
										$f->COM('rv_tab_empty' ,report => 'design2rout_rep' ,is_empty => 'yes');
										$f->COM('sel_design2rout' ,det_tol => 1 ,con_tol => 1 ,rad_tol => 0.1);
										$f->COM('rv_tab_view_results_enabled' ,report => 'design2rout_rep' ,is_enabled => 'no' ,serial_num => -1 ,all_count => -1);
										
										$f->COM('sel_resize_poly' ,size => $tExpansionSize);
										my $STATUS = $f->{STATUS};
										if ( $STATUS != 0 ) {
											$ExpansionFailure = 'yes';
										}

									}
								}
								$f->VON;
							}
						
#							$f->PAUSE(4);
							if ( $ExpansionFailure eq 'no') {
								###
						#		$f->COM('filter_area_strt');
						#		$f->COM('filter_area_xy', x => '3.5146047244', y => '1.639084252');
						#		$f->COM('filter_area_xy', x => '3.5849086614', y => '1.6026655512');
						#		$f->COM('filter_area_end', layer => '', filter_name => 'popup', operation => 'select', area_type => 'rectangle', inside_area => 'yes', intersect_area => 'no');
								#获取$TmpLayers[1] 中心和边缘
								#获取$TmpLayers[0] 边缘
								#计算拉伸值
						#		$f->COM('affected_layer', name => $TmpLayers[1], mode => 'single', affected => 'no');
								#拉伸
						#		$f->COM('sel_transform', oper => 'scale', x_anchor => '3.549944', y_anchor => '1.6196', angle => 0, x_scale => '1.1', y_scale => '1.15', x_offset => 0, y_offset => 0, mode => 'anchor', duplicate => 'no');
								$f->COM('affected_layer', name => $TmpLayers[1], mode => 'single', affected => 'yes');
								#COM sel_clear_feat
								#框选
								$f->COM('filter_area_strt');
								$f->COM('filter_area_xy', x => $tWorkLimitsMinX - $BoxSelTol, y => $tWorkLimitsMinY - $BoxSelTol);
								$f->COM('filter_area_xy', x => $tWorkLimitsMaxX + $BoxSelTol, y => $tWorkLimitsMaxY + $BoxSelTol);
			#					$f->COM('filter_area_xy', x => $f->{doinfo}{gLIMITSxmin} - $BoxSelTol, y => $f->{doinfo}{gLIMITSymin} - $BoxSelTol);
			#					$f->COM('filter_area_xy', x => $f->{doinfo}{gLIMITSxmax} + $BoxSelTol, y => $f->{doinfo}{gLIMITSymax} + $BoxSelTol);
								$f->COM('filter_area_end', layer => '', filter_name => 'popup', operation => 'select', area_type => 'rectangle', inside_area => 'yes', intersect_area => 'no');
								#旋转回来
								$f->COM('sel_transform', oper => 'rotate', x_anchor => $RotateCenterX , y_anchor => $RotateCenterY, angle => $RecoveryAngle, x_scale => 1, y_scale => 1, x_offset => 0, y_offset => 0, mode => 'anchor', duplicate => 'no');
								#获取$TmpLayers[1]中心位置
#													$f->PAUSE(5);

								$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$TmpLayers[1]",data_type => 'LIMITS',options => "select");
								my $WorkCoverLimitsCenterX2 = ($f->{doinfo}{gLIMITSxmax} + $f->{doinfo}{gLIMITSxmin} ) / 2 ;
								my $WorkCoverLimitsCenterY2 = ($f->{doinfo}{gLIMITSymax} + $f->{doinfo}{gLIMITSymin} ) / 2 ;

								$f->COM('affected_layer', name => $TmpLayers[1], mode => 'single', affected => 'no');
								$f->COM('sel_create_sym', symbol => $TmpWordBoxSy, x_datum => $WorkCoverLimitsCenterX2, y_datum => $WorkCoverLimitsCenterY2 , delete => 'no', fill_dx => '0.1', fill_dy => '0.1', attach_atr => 'no', retain_atr => 'no');
								#$f->COM('affected_layer', name => $TmpLayers[0], mode => 'single', affected => 'no');
								#删除 $TmpLayers[0] $TmpLayers[1]
#								$f->PAUSE(6);
								$f->COM('affected_layer', name => $TmpLayers[0], mode => 'single', affected => 'no');


								$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
								$f->COM('set_filter_attributes', filter_name => 'popup', exclude_attributes => 'no', condition => 'yes', attribute => '.string', min_int_val => 0, max_int_val => 0, min_float_val => 0, max_float_val => 0, option => '', text => $TmpAttrEnd);
								$f->COM('filter_area_strt');
								$f->COM('filter_area_end', filter_name => 'popup', operation => 'select');
								#删除属性
								$f->COM('sel_delete_atr', mode => 'list', attributes => '.string', attr_vals => $TmpAttrEnd);
								$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
								#相同操作
								#替换sy
								$f->COM('sel_substitute', mode => 'substitute', dcode => 0, symbol => $TmpWordBoxSy, x_datum => $WorkCoverLimitsCenterX2, y_datum => $WorkCoverLimitsCenterY2 , tol => 1, rotation => 0);
								#移动 到ok层
								#打散
						#		$f->COM('sel_multi_feat', operation => 'select', feat_types => 'pad', include_syms => $TmpWordBoxSy, is_extended => 'no', clear_prev => 'yes');
						#		$f->COM('sel_break');
							}
						}
						&DelLayers(@TmpLayers);
					}
				} else {
					&DelLayers($TmpLayers[0]);
					$f->COM('affected_layer', name => $WorkCoverLayer, mode => 'single', affected => 'no');
					$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
					$f->COM('set_filter_attributes', filter_name => 'popup', exclude_attributes => 'no', condition => 'yes', attribute => '.string', min_int_val => 0, max_int_val => 0, min_float_val => 0, max_float_val => 0, option => '', text => $TmpAttrEnd);
					$f->COM('filter_area_strt');
					$f->COM('filter_area_end', filter_name => 'popup', operation => 'select');
					#删除属性
					$f->COM('sel_delete_atr', mode => 'list', attributes => '.string', attr_vals => $TmpAttrEnd);
					$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
					$f->COM('sel_options', clear_mode => 'clear_after', display_mode => 'all_layers', area_inout => 'inside', area_select => 'select', select_mode => 'standard', area_touching_mode => 'exclude');
					goto SemiAutoWordBoxZoomMultipleEnd;
				}
			}
		} elsif ( $ReplaceMode eq 'Normal' ) {  ###################################################################################################################
			$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$WorkLayer",data_type => 'LIMITS',options => "select");
			my $WorkLimitsMinX =  $f->{doinfo}{gLIMITSxmin} + $MinLineSizeInch;
			my $WorkLimitsMinY =  $f->{doinfo}{gLIMITSymin} + $MinLineSizeInch;
			my $WorkLimitsMaxX =  $f->{doinfo}{gLIMITSxmax} - $MinLineSizeInch;
			my $WorkLimitsMaxY =  $f->{doinfo}{gLIMITSymax} - $MinLineSizeInch;

#			my $WorkLimitsCenterX =  $WorkLimitsMinX + ( $WorkLimitsMaxX  - $WorkLimitsMinX ) / 2 ;
#			my $WorkLimitsCenterY =  $WorkLimitsMinY + ( $WorkLimitsMaxY  - $WorkLimitsMinY ) / 2 ;


			my $TmpAttr = 'neo_silk-tmp1.' . int(rand(99999999));
			$f->COM('cur_atr_reset');
			$f->COM('cur_atr_set', attribute => '.string', text => $TmpAttr);
			$f->COM('sel_change_atr', mode => 'add');

			#
			#框选区域 FEATURES+单边1mil 获取套层 选中的 LIMITS
			$f->COM('affected_layer', name => $WorkCoverLayer, mode => 'single', affected => 'yes');

#		#	$f->COM('sel_clear_feat');
#			$f->COM('filter_area_strt');
#		#	$f->COM('filter_area_xy', x => $WorkLimitsMinX - $BoxSelTol, y => $WorkLimitsMinY - $BoxSelTol);
#		#	$f->COM('filter_area_xy', x => $WorkLimitsMaxX + $BoxSelTol, y => $WorkLimitsMaxY + $BoxSelTol);
#			$f->COM('filter_area_xy', x => $f->{doinfo}{gLIMITSxmin} - $BoxSelTol, y => $f->{doinfo}{gLIMITSymin} - $BoxSelTol);
#			$f->COM('filter_area_xy', x => $f->{doinfo}{gLIMITSxmax} + $BoxSelTol, y => $f->{doinfo}{gLIMITSymax} + $BoxSelTol);
#			$f->COM('filter_area_end', layer => '', filter_name => 'popup', operation => 'select', area_type => 'rectangle', inside_area => 'yes', intersect_area => 'no');
#			$f->PAUSE("1=10");

			$f->COM('reset_filter_criteria' ,filter_name => '' ,criteria => 'all');
			$f->COM('set_filter_polarity' ,filter_name => '' ,positive => 'yes' ,negative => 'no');
			$f->COM('sel_ref_feat' ,layers => $WorkCoverLayer ,use => 'select' ,mode => 'touch' ,pads_as => 'shape' ,f_types => 'line;pad;surface;arc;text' ,polarity => 'positive;negative' ,include_syms => '' ,exclude_syms => '');
#			$f->PAUSE("1=11");

			$f->COM('get_select_count');
			if ( $f->{COMANS} != 0 ) {
#				$f->COM('sel_options' ,clear_mode => 'clear_none' ,display_mode => 'displayed_layers' ,area_inout => 'outside' ,area_select => 'unselect' ,select_mode => 'standard' ,area_touching_mode => 'exclude');

				$f->COM('filter_area_strt');
				$f->COM('filter_area_xy', x => $f->{doinfo}{gLIMITSxmin} - $BoxSelTol, y => $f->{doinfo}{gLIMITSymin} - $BoxSelTol);
				$f->COM('filter_area_xy', x => $f->{doinfo}{gLIMITSxmax} + $BoxSelTol, y => $f->{doinfo}{gLIMITSymax} + $BoxSelTol);
				$f->COM('filter_area_end' ,layer => '' ,filter_name => 'popup' ,operation => 'unselect' ,area_type => 'rectangle' ,inside_area => 'no' ,intersect_area => 'no');

#				$f->COM('sel_options' ,clear_mode => 'clear_none' ,display_mode => 'displayed_layers' ,area_inout => 'inside' ,area_select => 'select' ,select_mode => 'standard' ,area_touching_mode => 'exclude');
#				$f->PAUSE("1=12");

				$f->COM('get_select_count');
				if ( $f->{COMANS} != 0 ) {

					$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$WorkCoverLayer",data_type => 'LIMITS',options => "select");
					my $WorkCoverLimitsMinX =  $f->{doinfo}{gLIMITSxmin};
					my $WorkCoverLimitsMinY =  $f->{doinfo}{gLIMITSymin};
					my $WorkCoverLimitsMaxX =  $f->{doinfo}{gLIMITSxmax};
					my $WorkCoverLimitsMaxY =  $f->{doinfo}{gLIMITSymax};

					my $WorkCoverLimitsCenterX =  $WorkCoverLimitsMinX + ( $WorkCoverLimitsMaxX  - $WorkCoverLimitsMinX ) / 2 ;
					my $WorkCoverLimitsCenterY =  $WorkCoverLimitsMinY + ( $WorkCoverLimitsMaxY  - $WorkCoverLimitsMinY ) / 2 ;
					my ($tScaleX,$tScaleY,$tExpansionSize,) = (1,1,0,);
					
##########################################################################################################################################################
		#			$f->PAUSE(01);
					if ( $tRunType =~ /^Scale/i ) {
#						$f->PAUSE("ZoomPlusMode=$ZoomPlusMode");
						if ( $ZoomPlusMode eq 'None' ) {
							my ($WorkArcLimitsMinX,$WorkArcLimitsMinY,$WorkArcLimitsMaxX,$WorkArcLimitsMaxY,@WorkArcData);
							$f->COM('sel_clear_feat');
							$f->COM('reset_filter_criteria' ,filter_name => '' ,criteria => 'all');
							$f->COM('set_filter_type' ,filter_name => '' ,lines => 'yes' ,pads => 'no' ,surfaces => 'no' ,arcs => 'no' ,text => 'no');
							$f->COM('set_filter_attributes' ,filter_name => 'popup' ,exclude_attributes => 'no' ,condition => 'yes' ,attribute => '.string' ,min_int_val => 0 ,max_int_val => 0 ,min_float_val => 0 ,max_float_val => 0 ,option => '' ,text => $TmpAttr);
							$f->COM('filter_area_strt');
							$f->COM('filter_area_end' ,filter_name => 'popup' ,operation => 'select');
							$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$WorkLayer",data_type => 'LIMITS',options => "select");
							my $WorkLineLimitsMinX =  $f->{doinfo}{gLIMITSxmin};
							my $WorkLineLimitsMinY =  $f->{doinfo}{gLIMITSymin};
							my $WorkLineLimitsMaxX =  $f->{doinfo}{gLIMITSxmax};
							my $WorkLineLimitsMaxY =  $f->{doinfo}{gLIMITSymax};
							
							$f->COM('sel_clear_feat');
							$f->COM('reset_filter_criteria' ,filter_name => '' ,criteria => 'all');
							$f->COM('set_filter_type' ,filter_name => '' ,lines => 'no' ,pads => 'no' ,surfaces => 'no' ,arcs => 'yes' ,text => 'no');
							$f->COM('set_filter_attributes' ,filter_name => 'popup' ,exclude_attributes => 'no' ,condition => 'yes' ,attribute => '.string' ,min_int_val => 0 ,max_int_val => 0 ,min_float_val => 0 ,max_float_val => 0 ,option => '' ,text => $TmpAttr);
							$f->COM('filter_area_strt');
							$f->COM('filter_area_end' ,filter_name => 'popup' ,operation => 'select');
#							$f->PAUSE("01,ZoomPlusMode=$ZoomPlusMode," . $f->COM('get_select_count'));

							$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$WorkLayer",data_type => 'LIMITS',options => "select");
							my $WorkArcLimitsMinX =  $f->{doinfo}{gLIMITSxmin};
							my $WorkArcLimitsMinY =  $f->{doinfo}{gLIMITSymin};
							my $WorkArcLimitsMaxX =  $f->{doinfo}{gLIMITSxmax};
							my $WorkArcLimitsMaxY =  $f->{doinfo}{gLIMITSymax};
							
							my $tArcSelExcludeTol = ( $ArcMaxSize / 1000 ) / 2 + $ArcSelExcludeTol ;
							
							$f->COM('filter_area_strt');
							$f->COM('filter_area_xy' ,x => $WorkArcLimitsMinX + $tArcSelExcludeTol ,y => $WorkArcLimitsMinY + $tArcSelExcludeTol );
							$f->COM('filter_area_xy' ,x => $WorkArcLimitsMaxX - $tArcSelExcludeTol ,y => $WorkArcLimitsMaxY - $tArcSelExcludeTol );
							$f->COM('filter_area_end' ,layer => '' ,filter_name => 'popup' ,operation => 'unselect' ,area_type => 'rectangle' ,inside_area => 'yes' ,intersect_area => 'no');
#							$f->PAUSE("tArcSelExcludeTol=$tArcSelExcludeTol,02,ZoomPlusMode=$ZoomPlusMode," . $f->COM('get_select_count'));

							$f->COM('get_select_count');
							if ( $f->{COMANS} != 0 ) {
	#							$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$WorkLayer",data_type => 'LIMITS',options => "select");
	#							$WorkArcLimitsMinX =  $f->{doinfo}{gLIMITSxmin};
	#							$WorkArcLimitsMinY =  $f->{doinfo}{gLIMITSymin};
	#							$WorkArcLimitsMaxX =  $f->{doinfo}{gLIMITSxmax};
	#							$WorkArcLimitsMaxY =  $f->{doinfo}{gLIMITSymax};
								my $tInfoFile = $ENV{GENESIS_TMP} . '/info.' . int(rand(9999));
								$f->COM ( 'info',out_file => $tInfoFile,args => " -t layer -e $JOB/$STEP/$WorkLayer -d FEATURES -o select" ) ;
								open ( FH,"<$tInfoFile" ) ;
								@WorkArcData = <FH>;
#								$f->PAUSE("$#WorkArcData=@WorkArcData");
								close FH;
								unlink $tInfoFile;

								$f->COM('reset_filter_criteria' ,filter_name => '' ,criteria => 'all');
								$f->COM('set_filter_polarity' ,filter_name => '' ,positive => 'yes' ,negative => 'no');
								$f->COM('sel_ref_feat' ,layers => $WorkCoverLayer ,use => 'select' ,mode => 'touch' ,pads_as => 'shape' ,f_types => 'line;pad;surface;arc;text' ,polarity => 'positive' ,include_syms => '' ,exclude_syms => '');
#								$f->PAUSE("03,ZoomPlusMode=$ZoomPlusMode," . $f->COM('get_select_count'));

								$f->COM('get_select_count');
								if ( $f->{COMANS} != 0 ) {
									my $tInfoFile = $ENV{GENESIS_TMP} . '/info.' . int(rand(9999));
									$f->COM ( 'info',out_file => $tInfoFile,args => " -t layer -e $JOB/$STEP/$WorkCoverLayer -d FEATURES -o select" ) ;
									open ( FH,"<$tInfoFile" ) ;
									while ( <FH> ) {
										my $line = $_;
										my ( $Size,$Positive ) = (0,'N');
										my ( $Xs,$Ys,$Xe,$Ye );
										if ( $line =~ /\#L/ ) {
											#L 1.80117 8.85592 1.79867 8.85717 r4.5 P 19
											( $Size,$Positive,) = ( split ( ' ',$line ) ) [5,6,];
											if ( $Positive eq 'P' ) {
												if ( $Size !~ /^r\d+/ ) {
													$ZoomPlusMode = 'Yes';
												}
											}
										}elsif ( $line =~ /\#P/ ) {
											#P 1.80155 0.28521 rect33.41x37.41 N 0 0 N
											#oval\d+ r\d+ el\d+
											( $Size,$Positive ) = ( split ( ' ',$line ) ) [3,4,];
											if ( $Positive eq 'P' ) {
												if ( $Size !~ /^r\d+/ and $Size !~ /^oval\d+/ and $Size !~ /^el\d+/ ) {
													$ZoomPlusMode = 'Yes';
												}
											}
										}elsif ( $line =~ /\#S/ ) {
											#S P 0
											#OB 0.17558996063 0.29443011811 I
											( $Positive ) = ( split ( ' ',$line ) ) [1,];
											if ( $Positive eq 'P' ) {
												$ZoomPlusMode = 'Yes';
											}
										}
									}
									close FH;
									unlink $tInfoFile;
									if ( $ZoomPlusMode ne 'Yes' ){
										$ZoomPlusMode = 'Normal';
	#								} else {
									
									}
								
								} else {
									$ZoomPlusMode = 'Normal';
								}
							} else {
								$ZoomPlusMode = 'Normal';
							}
#							$f->PAUSE("2,ZoomPlusMode=$ZoomPlusMode");

							if ( $ZoomPlusMode eq 'Yes' ){	
								#分三种情况      Normal
								#弧的Limits 在 线的Limits里面 正常缩放
								#弧的Limits 在 线的Limits外面 直接 以 长方向 线的Limits做缩放 + 弧的3/4 缩放 1/4
#								my $OutsideFixFactor = 1 / 4;
#								my $EqualFixFactor = 1 / 2;
								my $LimitsFixMin = 0.0025 ;
#								my $LimitsFixMin = 0.0015 ;
#								my $LimitsFixMin = 0.001 ;
#								my $LimitsFixMin = 0.00001 ;
#								my $LimitsFixMins = 0.00125 ;
#								my $OutsideFixFactor = 1 / 3;
#								my $OutsideFixFactor = 1 / 3;
#								my $OutsideFixFactor = 1 / 2;
#								#my $OutsideFixFactor = 3 / 5;
#								my $OutsideFixFactor = 1 / 5;
								my $OutsideFixFactor = 1 / 10;
#								my $OutsideFixFactor = 1 / 15;
#								my $OutsideFixFactor = 1;
#								my $OutsideFixFactor = 1 / 2;
#								my $OutsideFixFactor = 1;
#								my $EqualFixFactor = 1 / 3;
								my $EqualFixFactor = 1 / 6;
#								my $EqualFixFactor = 1 / 9;
#								my $EqualFixFactor = 1 / 12;
#								my $OutsideFixFactor = 1 / 2;
#								my $EqualFixFactor = 1 / 2;
								#弧的Limits =~ 线的Limits 直接 以 长方向 线的Limits做缩放 + 弧的1/2 缩放
								#弧的Limits =~ 线的Limits 直接 以 长方向 线的Limits做缩放 + 弧的1/2 缩放
								my $WorkToCoverMinX = $WorkCoverLimitsMinX - $WorkLimitsMinX ;
								my $WorkToCoverMinY = $WorkCoverLimitsMinY - $WorkLimitsMinY ;
								my $WorkToCoverMaxX = $WorkLimitsMaxX - $WorkCoverLimitsMaxX;
								my $WorkToCoverMaxY = $WorkLimitsMaxY - $WorkCoverLimitsMaxY;
								
								my $LimitsLineToArcMinX = $WorkArcLimitsMinX - $WorkLineLimitsMinX ;
								my $LimitsLineToArcMinY = $WorkArcLimitsMinY - $WorkLineLimitsMinY ;
								my $LimitsLineToArcMaxX = $WorkLineLimitsMaxX - $WorkArcLimitsMaxX ;
								my $LimitsLineToArcMaxY = $WorkLineLimitsMaxY - $WorkArcLimitsMaxY ;
								
								my $LimitsLineToCoverMinX = ( $WorkLineLimitsMinX + ( $MinLineSizeInch / 2 ) )  - $WorkCoverLimitsMinX ;
								my $LimitsLineToCoverMinY = ( $WorkLineLimitsMinY + ( $MinLineSizeInch / 2 ) )  - $WorkCoverLimitsMinY ;
								my $LimitsLineToCoverMaxX = $WorkCoverLimitsMaxX -  ( $WorkLineLimitsMaxX - ( $MinLineSizeInch / 2 ) ) ;
								my $LimitsLineToCoverMaxY = $WorkCoverLimitsMaxY -  ( $WorkLineLimitsMaxY - ( $MinLineSizeInch / 2 ) ) ;
#								$f->PAUSE("WorkToCover:MinX,MinY,MaxX,MaxY=$WorkToCoverMinX,$WorkToCoverMinY,$WorkToCoverMaxX,$WorkToCoverMaxY\nLimitsLineToCover:MinX,MinY,MaxX,MaxY,=$LimitsLineToCoverMinX,$LimitsLineToCoverMinY,$LimitsLineToCoverMaxX,$LimitsLineToCoverMaxY,");
								
								my $CalcTol = 0.0005; #0.5mil
								my ($LineCmpArcMinX,$LineCmpArcMinY,$LineCmpArcMaxX,$LineCmpArcMaxY,) = ('Equal','Equal','Equal','Equal',);#弧Limits 在线Limits的范围.
								
								my ($LimitsOffsetOutLeft,$LimitsOffsetOutRight,$LimitsOffsetOutUp,$LimitsOffsetOutDown,) = (0,0,0,0,);#弧Limits 在线Limits的范围之外

								#'Equal', 'Outside' , 'Inside'
								if ( $LimitsLineToArcMinX < ( 0 - $CalcTol ) ) {
									$LineCmpArcMinX = 'Outside';
#									$LimitsOffsetOutLeft =  abs ( $LimitsLineToArcMinX ) * $OutsideFixFactor ;
									$LimitsOffsetOutLeft =  abs ( $LimitsLineToCoverMinX ) * $OutsideFixFactor ;
									if ( $LimitsOffsetOutLeft < $LimitsFixMin ){
										$LimitsOffsetOutLeft = $LimitsFixMin;
									}
									if ( $WorkToCoverMinX > 0 ){
										$LimitsOffsetOutLeft += $WorkToCoverMinX;
									}
									
								} elsif ( $LimitsLineToArcMinX > $CalcTol ) {
									$LineCmpArcMinX = 'Inside';
								}
								
								if ( $LimitsLineToArcMinY < ( 0 - $CalcTol ) ) {
									$LineCmpArcMinY = 'Outside';
#									$LimitsOffsetOutDown =  abs ( $LimitsLineToArcMinY ) * $OutsideFixFactor ;
									$LimitsOffsetOutDown =  abs ( $LimitsLineToCoverMinY ) * $OutsideFixFactor ;
									if ( $LimitsOffsetOutDown < $LimitsFixMin ){
										$LimitsOffsetOutDown = $LimitsFixMin;
									}
									if ( $WorkToCoverMinY > 0 ){
										$LimitsOffsetOutDown += $WorkToCoverMinY;
									}
								} elsif ( $LimitsLineToArcMinY > $CalcTol ) {
									$LineCmpArcMinY = 'Inside';
								}
								
								if ( $LimitsLineToArcMaxX < ( 0 - $CalcTol ) ) {
									$LineCmpArcMaxX = 'Outside';
#									$LimitsOffsetOutRight =  abs ( $LimitsLineToArcMaxX ) * $OutsideFixFactor ;
									$LimitsOffsetOutRight =  abs ( $LimitsLineToCoverMaxX ) * $OutsideFixFactor ;
									if ( $LimitsOffsetOutRight < $LimitsFixMin ){
										$LimitsOffsetOutRight = $LimitsFixMin;
									}
									if ( $WorkToCoverMaxX > 0 ){
										$LimitsOffsetOutRight += $WorkToCoverMaxX;
									}
								} elsif ( $LimitsLineToArcMaxX > $CalcTol ) {
									$LineCmpArcMaxX = 'Inside';
								}
								
								if ( $LimitsLineToArcMaxY < ( 0 - $CalcTol ) ) {
									$LineCmpArcMaxY = 'Outside';
#									$LimitsOffsetOutUp =  abs ( $LimitsLineToArcMaxY ) * $OutsideFixFactor ;
									$LimitsOffsetOutUp =  abs ( $LimitsLineToCoverMaxY ) * $OutsideFixFactor ;
									if ( $LimitsOffsetOutUp < $LimitsFixMin ){
										$LimitsOffsetOutUp = $LimitsFixMin;
									}
									if ( $WorkToCoverMaxY > 0 ){
										$LimitsOffsetOutUp += $WorkToCoverMaxY;
									}
								} elsif ( $LimitsLineToArcMaxY > $CalcTol ) {
									$LineCmpArcMaxY = 'Inside';
								}
								
								#############################
								my $LimitsLineCmpArcEqual = 'None';
								if ( ( $LineCmpArcMinX eq 'Equal' ) or ( $LineCmpArcMaxX eq 'Equal' ) ) {
									$LimitsLineCmpArcEqual = 'X';
								}
								
								if ( ( $LineCmpArcMinY eq 'Equal' ) or ( $LineCmpArcMaxY eq 'Equal' ) ) {
									if ( $LimitsLineCmpArcEqual eq 'None' ) {
										$LimitsLineCmpArcEqual = 'Y';
									} else {
										$LimitsLineCmpArcEqual = 'Both';
									}
								}
								#############################
								my $LimitsLineCmpArcOut = 'None';
								if ( ( $LineCmpArcMinX eq 'Outside' ) or ( $LineCmpArcMaxX eq 'Outside' ) ) {
									$LimitsLineCmpArcOut = 'X';
								}
								
								if ( ( $LineCmpArcMinY eq 'Outside' ) or ( $LineCmpArcMaxY eq 'Outside' ) ) {
									if ( $LimitsLineCmpArcOut eq 'None' ) {
										$LimitsLineCmpArcOut = 'Y';
									} else {
										$LimitsLineCmpArcOut = 'Both';
									}
								}
								
#								$f->PAUSE("$LimitsOffsetOutLeft,$LimitsOffsetOutRight,$LimitsOffsetOutUp,$LimitsOffsetOutDown,");

#								$f->PAUSE("0,LimitsLineCmpArcEqual=$LimitsLineCmpArcEqual,LimitsLineCmpArcOut=$LimitsLineCmpArcOut");

								my $WorkLimitsCenterX =  $WorkLimitsMinX + ( $WorkLimitsMaxX  - $WorkLimitsMinX ) / 2 ;
								my $WorkLimitsCenterY =  $WorkLimitsMinY + ( $WorkLimitsMaxY  - $WorkLimitsMinY ) / 2 ;
								
								my ($LimitsOffsetEqualLeft,$LimitsOffsetEqualRight,$LimitsOffsetEqualUp,$LimitsOffsetEqualDown,) = (0,0,0,0,);#弧Limits =~ 线Limits
#								$f->PAUSE("0,WorkArcData=@WorkArcData");

								for my $tLine ( @WorkArcData ){
									#A 6.084084 1.4956883 6.084084 1.4553318 6.084084 1.47551 r6 P 15 N
									#Arc,XS=6.084084,YS=1.4956883,XE=6.084084,YE=1.4553318,XC=6.084084,YC=1.47551,,D=0.0403565,r6,POS,CCW
#									my $line = $_;
#									$f->PAUSE("tLine=$tLine");
									my ( $Size,$Positive ) = (0,'N');
									my ( $Xs,$Ys,$Xe,$Ye,$Xc,$Yc,);
									if ( $tLine =~ /\#A/ ) {
										($Xs,$Ys,$Xe,$Ye,$Xc,$Yc,$Size,$Positive ) = ( split ( ' ',$tLine ) ) [1,2,3,4,5,6,7,8];
										if ( $Positive eq 'P' ){
#											$f->PAUSE("2=$Xs,$Ys,$Xe,$Ye,$Xc,$Yc,$Size,$Positive");

											# 1 | 2
											# -----
											# 3 | 4
											## ($LineCmpArcMinX,$LineCmpArcMinY,$LineCmpArcMaxX,$LineCmpArcMaxY,) = ('Equal','Equal','Equal','Equal',);#弧Limits 在线Limits的范围.
											if ( $Yc > $WorkLimitsCenterY ) {  #1 2
												if ( $Xc > $WorkLimitsCenterX ) {  #2 #右 上
													if ( $LineCmpArcMaxX eq 'Equal' ) {  #右
														my $tFixFactor = abs ( $Xs - $Xe ) * $EqualFixFactor ;
														if ( $tFixFactor > $LimitsOffsetEqualRight){
															$LimitsOffsetEqualRight = $tFixFactor ;
														}
													}
												} else {  #1 #左 上
													if ( $LineCmpArcMinX eq 'Equal' ) {  #左
														my $tFixFactor = abs ( $Xs - $Xe ) * $EqualFixFactor ;
														if ( $tFixFactor > $LimitsOffsetEqualLeft){
															$LimitsOffsetEqualLeft = $tFixFactor ;
														}
													}
												}
												#
												if ( $LineCmpArcMaxY eq 'Equal' ) {  #上
													my $tFixFactor = abs ( $Ys - $Ye ) * $EqualFixFactor ;
													if ( $tFixFactor > $LimitsOffsetEqualUp){
														$LimitsOffsetEqualUp = $tFixFactor ;
													}
												}
											} else {  #3 4
												if ( $Xc > $WorkLimitsCenterX ) {  #4 #右 下
													if ( $LineCmpArcMaxX eq 'Equal' ) {  #右
														my $tFixFactor = abs ( $Xs - $Xe ) * $EqualFixFactor ;
														if ( $tFixFactor > $LimitsOffsetEqualRight){
															$LimitsOffsetEqualRight = $tFixFactor ;
														}
													}
												} else {  #3 #左 下
													if ( $LineCmpArcMinX eq 'Equal' ) {  #左
														my $tFixFactor = abs ( $Xs - $Xe ) * $EqualFixFactor ;
														if ( $tFixFactor > $LimitsOffsetEqualLeft){
															$LimitsOffsetEqualLeft = $tFixFactor ;
														}
													}
												}
												#
												if ( $LineCmpArcMinY eq 'Equal' ) {  #下
													my $tFixFactor = abs ( $Ys - $Ye ) * $EqualFixFactor ;
													if ( $tFixFactor > $LimitsOffsetEqualDown){
														$LimitsOffsetEqualDown = $tFixFactor ;
													}
												}
											}
										}
									}
								}
								
#								$f->PAUSE("0=$LimitsOffsetEqualLeft,$LimitsOffsetEqualDown,$LimitsOffsetEqualRight,$LimitsOffsetEqualUp,");

								if ( $LimitsLineCmpArcOut eq 'None' ) {
									if ( $LimitsLineCmpArcEqual eq 'X' ) {
										$WorkLimitsMinX +=  $LimitsOffsetEqualLeft	;
										$WorkLimitsMaxX -=  $LimitsOffsetEqualRight	;
									} elsif ( $LimitsLineCmpArcEqual eq 'Y' ) {
										$WorkLimitsMinY +=  $LimitsOffsetEqualDown	;
										$WorkLimitsMaxY -=  $LimitsOffsetEqualUp		;
									} elsif ( $LimitsLineCmpArcEqual eq 'Both' ) {
										if ( abs ( $WorkCoverLimitsMaxX - $WorkCoverLimitsMinX ) > abs ( $WorkCoverLimitsMaxY - $WorkCoverLimitsMinY ) ) {
											$WorkLimitsMinX +=  $LimitsOffsetEqualLeft	;
											$WorkLimitsMaxX -=  $LimitsOffsetEqualRight	;
										} else {
											$WorkLimitsMinY +=  $LimitsOffsetEqualDown	;
											$WorkLimitsMaxY -=  $LimitsOffsetEqualUp		;
										}
									}
								} else {
									if ( $LimitsLineCmpArcOut eq 'X' ) {
										my $tWorkToCover = ( abs ( $WorkLimitsMaxY - $WorkLimitsMinY )  - abs ( $WorkCoverLimitsMaxY - $WorkCoverLimitsMinY ) )  / 2;
										if ( $tWorkToCover > 0 ){
#											$WorkLimitsMinX +=  $tWorkToCover;
#											$WorkLimitsMaxX -=  $tWorkToCover;
											$WorkLimitsMinX -=  $tWorkToCover;
											$WorkLimitsMaxX +=  $tWorkToCover;
										}
									} elsif ( $LimitsLineCmpArcOut eq 'Y' ) {
										my $tWorkToCover = ( abs ( $WorkLimitsMaxX - $WorkLimitsMinX )  - abs ( $WorkCoverLimitsMaxX - $WorkCoverLimitsMinX ) )  / 2;
										if ( $tWorkToCover > 0 ){
#											$WorkLimitsMinY +=  $tWorkToCover;
#											$WorkLimitsMaxY -=  $tWorkToCover;
											$WorkLimitsMinY -=  $tWorkToCover;
											$WorkLimitsMaxY +=  $tWorkToCover;
										}
									}
									$WorkLimitsMinX +=  $LimitsOffsetOutLeft		;
									$WorkLimitsMinY +=  $LimitsOffsetOutDown		;
									$WorkLimitsMaxX -=  $LimitsOffsetOutRight		;
									$WorkLimitsMaxY -=  $LimitsOffsetOutUp			;
								}
								
								#$WorkLimitsMinX,$WorkLimitsMinY,$WorkLimitsMaxX,$WorkLimitsMaxY,
								#$WorkCoverLimitsMinX,$WorkCoverLimitsMinY,$WorkCoverLimitsMaxX,$WorkCoverLimitsMaxY,

								#分三种情况
								#弧的Limits 在 线的Limits里面 正常缩放
								#弧的Limits 在 线的Limits外面 直接 以 arc 在外的方向 Limits做缩放 + 弧的3/4 缩放
								#如果另一边本来就大 就加上大于多少就加多少.

								#弧的Limits =~ 线的Limits 直接 以 长方向 线的Limits做缩放 + 弧的1/2 缩放

								### Layer - c1-1 features data ###
								#S P 0
								#OB 0.17558996063 0.29443011811 I
								#OS 0.17558996063 0.29443011811
								#OE
								#L 1.8217282 0.2430339 1.8217282 0.2880063 r6 P 15 
								#A 1.8217282 0.2880063 1.7813718 0.2880063 1.80155 0.2880063 r6 P 15 N
								#P 1.80155 0.28521 rect33.41x37.41 N 0 0 N

							}
						} elsif ( $ZoomPlusMode eq 'Dense' ) {  #密集线组成的弧 #################################################################
							my $DenseArcJudNum = 20; 
							my $DenseLengthTol = 0.002 ; #inch
							$f->COM('sel_clear_feat');
							$f->COM('reset_filter_criteria' ,filter_name => '' ,criteria => 'all');
							$f->COM('set_filter_type' ,filter_name => '' ,lines => 'yes' ,pads => 'no' ,surfaces => 'no' ,arcs => 'no' ,text => 'no');
							$f->COM('set_filter_polarity' ,filter_name => '' ,positive => 'yes' ,negative => 'no');
							$f->COM('set_filter_attributes' ,filter_name => 'popup' ,exclude_attributes => 'no' ,condition => 'yes' ,attribute => '.string' ,min_int_val => 0 ,max_int_val => 0 ,min_float_val => 0 ,max_float_val => 0 ,option => '' ,text => $TmpAttr);

							$f->COM('set_filter_length' ,slot => 'lines' ,min_length => 0 ,max_length => 0.002);
							$f->COM('filter_area_strt');
							$f->COM('filter_area_end' ,filter_name => 'popup' ,operation => 'select');
							$f->COM('set_filter_length');
							$f->COM('adv_filter_reset');
							$f->COM('get_select_count');
#							if ( $f->{COMANS} != 0 ) {
							if ( $f->{COMANS} > $DenseArcJudNum ) {
								$f->COM('cur_atr_reset');
								$f->COM('cur_atr_set', attribute => '.bit', text => $TmpAttr);
								$f->COM('sel_change_atr', mode => 'add');
#								$f->COM('set_filter_length');
#								$f->COM('set_filter_angle');
#								$f->COM('adv_filter_reset');
								my ($WorkDenseLimitsMinX,$WorkDenseLimitsMinY,$WorkDenseLimitsMaxX,$WorkDenseLimitsMaxY,@WorkDenseData);
								$f->COM('sel_clear_feat');
#								$f->COM('reset_filter_criteria' ,filter_name => '' ,criteria => 'all');
#								$f->COM('set_filter_type' ,filter_name => '' ,lines => 'yes' ,pads => 'no' ,surfaces => 'no' ,arcs => 'no' ,text => 'no');
#								$f->COM('set_filter_attributes' ,filter_name => 'popup' ,exclude_attributes => 'no' ,condition => 'yes' ,attribute => '.string' ,min_int_val => 0 ,max_int_val => 0 ,min_float_val => 0 ,max_float_val => 0 ,option => '' ,text => $TmpAttr);
#								$f->COM('filter_area_strt');
#								$f->COM('filter_area_end' ,filter_name => 'popup' ,operation => 'select');
								
								$f->COM('reset_filter_criteria' ,filter_name => '' ,criteria => 'all');
								$f->COM('set_filter_type' ,filter_name => '' ,lines => 'yes' ,pads => 'no' ,surfaces => 'no' ,arcs => 'no' ,text => 'no');
								$f->COM('set_filter_polarity' ,filter_name => '' ,positive => 'yes' ,negative => 'no');
								$f->COM('set_filter_attributes' ,filter_name => 'popup' ,exclude_attributes => 'no' ,condition => 'yes' ,attribute => '.string' ,min_int_val => 0 ,max_int_val => 0 ,min_float_val => 0 ,max_float_val => 0 ,option => '' ,text => $TmpAttr);
								$f->COM('set_filter_attributes' ,filter_name => 'popup' ,exclude_attributes => 'yes' ,condition => 'yes' ,attribute => '.bit' ,min_int_val => 0 ,max_int_val => 0 ,min_float_val => 0 ,max_float_val => 0 ,option => '' ,text => $TmpAttr);
								$f->COM('filter_area_strt');
								$f->COM('filter_area_end' ,filter_name => 'popup' ,operation => 'select');
#								$f->PAUSE("1,line");

								$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$WorkLayer",data_type => 'LIMITS',options => "select");
								my $WorkLineLimitsMinX =  $f->{doinfo}{gLIMITSxmin};
								my $WorkLineLimitsMinY =  $f->{doinfo}{gLIMITSymin};
								my $WorkLineLimitsMaxX =  $f->{doinfo}{gLIMITSxmax};
								my $WorkLineLimitsMaxY =  $f->{doinfo}{gLIMITSymax};
								
								$f->COM('sel_clear_feat');
#								$f->COM('reset_filter_criteria' ,filter_name => '' ,criteria => 'all');
#								$f->COM('set_filter_type' ,filter_name => '' ,lines => 'no' ,pads => 'no' ,surfaces => 'no' ,arcs => 'yes' ,text => 'no');
#								$f->COM('set_filter_attributes' ,filter_name => 'popup' ,exclude_attributes => 'no' ,condition => 'yes' ,attribute => '.string' ,min_int_val => 0 ,max_int_val => 0 ,min_float_val => 0 ,max_float_val => 0 ,option => '' ,text => $TmpAttr);
#								$f->COM('filter_area_strt');
#								$f->COM('filter_area_end' ,filter_name => 'popup' ,operation => 'select');

								$f->COM('reset_filter_criteria' ,filter_name => '' ,criteria => 'all');
								$f->COM('set_filter_type' ,filter_name => '' ,lines => 'yes' ,pads => 'no' ,surfaces => 'no' ,arcs => 'no' ,text => 'no');
								$f->COM('set_filter_polarity' ,filter_name => '' ,positive => 'yes' ,negative => 'no');
								$f->COM('set_filter_attributes' ,filter_name => 'popup' ,exclude_attributes => 'no' ,condition => 'yes' ,attribute => '.bit' ,min_int_val => 0 ,max_int_val => 0 ,min_float_val => 0 ,max_float_val => 0 ,option => '' ,text => $TmpAttr);
								$f->COM('filter_area_strt');
								$f->COM('filter_area_end' ,filter_name => 'popup' ,operation => 'select');
#								$f->PAUSE("1,ddd");
	#							$f->PAUSE("01,ZoomPlusMode=$ZoomPlusMode," . $f->COM('get_select_count'));
								$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$WorkLayer",data_type => 'LIMITS',options => "select");
								my $WorkDenseLimitsMinX =  $f->{doinfo}{gLIMITSxmin};
								my $WorkDenseLimitsMinY =  $f->{doinfo}{gLIMITSymin};
								my $WorkDenseLimitsMaxX =  $f->{doinfo}{gLIMITSxmax};
								my $WorkDenseLimitsMaxY =  $f->{doinfo}{gLIMITSymax};
								
#								my $tDenseSelExcludeTol = ( $DenseMaxSize / 1000 ) / 2 + $DenseSelExcludeTol ;
#								$f->COM('filter_area_strt');
#								$f->COM('filter_area_xy' ,x => $WorkDenseLimitsMinX + $tDenseSelExcludeTol ,y => $WorkDenseLimitsMinY + $tDenseSelExcludeTol );
#								$f->COM('filter_area_xy' ,x => $WorkDenseLimitsMaxX - $tDenseSelExcludeTol ,y => $WorkDenseLimitsMaxY - $tDenseSelExcludeTol );
#								$f->COM('filter_area_end' ,layer => '' ,filter_name => 'popup' ,operation => 'unselect' ,area_type => 'rectangle' ,inside_area => 'yes' ,intersect_area => 'no');
#								$f->PAUSE("tDenseSelExcludeTol=$tDenseSelExcludeTol,02,ZoomPlusMode=$ZoomPlusMode," . $f->COM('get_select_count'));

								$f->COM('get_select_count');
								if ( $f->{COMANS} != 0 ) {
		#							$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$WorkLayer",data_type => 'LIMITS',options => "select");
		#							$WorkDenseLimitsMinX =  $f->{doinfo}{gLIMITSxmin};
		#							$WorkDenseLimitsMinY =  $f->{doinfo}{gLIMITSymin};
		#							$WorkDenseLimitsMaxX =  $f->{doinfo}{gLIMITSxmax};
		#							$WorkDenseLimitsMaxY =  $f->{doinfo}{gLIMITSymax};
#									my $tInfoFile = $ENV{GENESIS_TMP} . '/info.' . int(rand(9999));
#									$f->COM ( 'info',out_file => $tInfoFile,args => " -t layer -e $JOB/$STEP/$WorkLayer -d FEATURES -o select" ) ;
#									open ( FH,"<$tInfoFile" ) ;
#									@WorkDenseData = <FH>;
#	#								$f->PAUSE("$#WorkDenseData=@WorkDenseData");
#									close FH;
#									unlink $tInfoFile;

									$f->COM('reset_filter_criteria' ,filter_name => '' ,criteria => 'all');
									$f->COM('set_filter_polarity' ,filter_name => '' ,positive => 'yes' ,negative => 'no');
									$f->COM('sel_ref_feat' ,layers => $WorkCoverLayer ,use => 'select' ,mode => 'touch' ,pads_as => 'shape' ,f_types => 'line;pad;surface;arc;text' ,polarity => 'positive' ,include_syms => '' ,exclude_syms => '');
#									$f->PAUSE("03,ZoomPlusMode=$ZoomPlusMode," . $f->COM('get_select_count'));

									$f->COM('get_select_count');
									if ( $f->{COMANS} != 0 ) {
										my $tInfoFile = $ENV{GENESIS_TMP} . '/info.' . int(rand(9999));
										$f->COM ( 'info',out_file => $tInfoFile,args => " -t layer -e $JOB/$STEP/$WorkCoverLayer -d FEATURES -o select" ) ;
										open ( FH,"<$tInfoFile" ) ;
										while ( <FH> ) {
											my $line = $_;
											my ( $Size,$Positive ) = (0,'N');
											my ( $Xs,$Ys,$Xe,$Ye );
											if ( $line =~ /\#L/ ) {
												#L 1.80117 8.85592 1.79867 8.85717 r4.5 P 19
												( $Size,$Positive,) = ( split ( ' ',$line ) ) [5,6,];
												if ( $Positive eq 'P' ) {
													if ( $Size !~ /^r\d+/ ) {
														$ZoomPlusMode = 'Yes';
													}
												}
											}elsif ( $line =~ /\#P/ ) {
												#P 1.80155 0.28521 rect33.41x37.41 N 0 0 N
												#oval\d+ r\d+ el\d+
												( $Size,$Positive ) = ( split ( ' ',$line ) ) [3,4,];
												if ( $Positive eq 'P' ) {
													if ( $Size !~ /^r\d+/ and $Size !~ /^oval\d+/ and $Size !~ /^el\d+/ ) {
														$ZoomPlusMode = 'Yes';
													}
												}
											}elsif ( $line =~ /\#S/ ) {
												#S P 0
												#OB 0.17558996063 0.29443011811 I
												( $Positive ) = ( split ( ' ',$line ) ) [1,];
												if ( $Positive eq 'P' ) {
													$ZoomPlusMode = 'Yes';
												}
											}
										}
										close FH;
										unlink $tInfoFile;
										if ( $ZoomPlusMode ne 'Yes' ){
											$ZoomPlusMode = 'Normal';
		#								} else {
										
										}
									
									} else {
										$ZoomPlusMode = 'Normal';
									}
								} else {
									$ZoomPlusMode = 'Normal';
								}
#								$f->PAUSE("2,ZoomPlusMode=$ZoomPlusMode");
								if ( $ZoomPlusMode eq 'Yes' ){	
									#分三种情况
									#弧的Limits 在 线的Limits里面 正常缩放
									#弧的Limits 在 线的Limits外面 直接 以 长方向 线的Limits做缩放 + 弧的3/4 缩放 1/4
	#								my $OutsideFixFactor = 1 / 4;
	#								my $EqualFixFactor = 1 / 2;
									my $LimitsFixMin = 0.0025 ;
	#								my $OutsideFixFactor = 1 / 3;
	#								my $OutsideFixFactor = 1 / 3;
#									my $OutsideFixFactor = 1 / 2;
#									my $OutsideFixFactor = 3 / 5;
									my $OutsideFixFactor = 1 / 3;
#									my $OutsideFixFactor = 13 / 36;
	#								my $OutsideFixFactor = 1;
	#								my $OutsideFixFactor = 1 / 2;
	#								my $OutsideFixFactor = 1;
#									my $EqualFixFactor = 1 / 3;
									my $EqualFixFactor = 1 / 6;
	#								my $OutsideFixFactor = 1 / 2;
	#								my $EqualFixFactor = 1 / 2;
									#弧的Limits =~ 线的Limits 直接 以 长方向 线的Limits做缩放 + 弧的1/2 缩放
									#弧的Limits =~ 线的Limits 直接 以 长方向 线的Limits做缩放 + 弧的1/2 缩放
									
									my $WorkToCoverMinX = $WorkCoverLimitsMinX - $WorkLimitsMinX ;
									my $WorkToCoverMinY = $WorkCoverLimitsMinY - $WorkLimitsMinY ;
									my $WorkToCoverMaxX = $WorkLimitsMaxX - $WorkCoverLimitsMaxX;
									my $WorkToCoverMaxY = $WorkLimitsMaxY - $WorkCoverLimitsMaxY;
									
									my $LimitsLineToDenseMinX = $WorkDenseLimitsMinX - $WorkLineLimitsMinX ;
									my $LimitsLineToDenseMinY = $WorkDenseLimitsMinY - $WorkLineLimitsMinY ;
									my $LimitsLineToDenseMaxX = $WorkLineLimitsMaxX - $WorkDenseLimitsMaxX ;
									my $LimitsLineToDenseMaxY = $WorkLineLimitsMaxY - $WorkDenseLimitsMaxY ;
									
									my $LimitsLineToCoverMinX = ( $WorkLineLimitsMinX + ( $MinLineSizeInch / 2 ) )  - $WorkCoverLimitsMinX ;
									my $LimitsLineToCoverMinY = ( $WorkLineLimitsMinY + ( $MinLineSizeInch / 2 ) )  - $WorkCoverLimitsMinY ;
									my $LimitsLineToCoverMaxX = $WorkCoverLimitsMaxX -  ( $WorkLineLimitsMaxX - ( $MinLineSizeInch / 2 ) ) ;
									my $LimitsLineToCoverMaxY = $WorkCoverLimitsMaxY -  ( $WorkLineLimitsMaxY - ( $MinLineSizeInch / 2 ) ) ;
										
									my $CalcTol = 0.0005; #0.5mil
									my ($LineCmpDenseMinX,$LineCmpDenseMinY,$LineCmpDenseMaxX,$LineCmpDenseMaxY,) = ('Equal','Equal','Equal','Equal',);#弧Limits 在线Limits的范围.
									
									my ($LimitsOffsetOutLeft,$LimitsOffsetOutRight,$LimitsOffsetOutUp,$LimitsOffsetOutDown,) = (0,0,0,0,);#弧Limits 在线Limits的范围之外

									#'Equal', 'Outside' , 'Inside'
									if ( $LimitsLineToDenseMinX < ( 0 - $CalcTol ) ) {
										$LineCmpDenseMinX = 'Outside';
#										$LimitsOffsetOutLeft =  abs ( $LimitsLineToDenseMinX ) * $OutsideFixFactor ;
										$LimitsOffsetOutLeft =  abs ( $LimitsLineToCoverMinX ) * $OutsideFixFactor ;
										if ( $LimitsOffsetOutLeft < $LimitsFixMin ){
											$LimitsOffsetOutLeft = $LimitsFixMin;
										}
										if ( $WorkToCoverMinX > 0 ){
											$LimitsOffsetOutLeft += $WorkToCoverMinX;
										}
										
									} elsif ( $LimitsLineToDenseMinX > $CalcTol ) {
										$LineCmpDenseMinX = 'Inside';
									}
									
									if ( $LimitsLineToDenseMinY < ( 0 - $CalcTol ) ) {
										$LineCmpDenseMinY = 'Outside';
#										$LimitsOffsetOutDown =  abs ( $LimitsLineToDenseMinY ) * $OutsideFixFactor ;
										$LimitsOffsetOutDown =  abs ( $LimitsLineToCoverMinY ) * $OutsideFixFactor ;
										if ( $LimitsOffsetOutDown < $LimitsFixMin ){
											$LimitsOffsetOutDown = $LimitsFixMin;
										}
										if ( $WorkToCoverMinY > 0 ){
											$LimitsOffsetOutDown += $WorkToCoverMinY;
										}

									} elsif ( $LimitsLineToDenseMinY > $CalcTol ) {
										$LineCmpDenseMinY = 'Inside';
									}
									
									if ( $LimitsLineToDenseMaxX < ( 0 - $CalcTol ) ) {
										$LineCmpDenseMaxX = 'Outside';
#										$LimitsOffsetOutRight =  abs ( $LimitsLineToDenseMaxX ) * $OutsideFixFactor ;
										$LimitsOffsetOutRight =  abs ( $LimitsLineToCoverMaxX ) * $OutsideFixFactor ;
										if ( $LimitsOffsetOutRight < $LimitsFixMin ){
											$LimitsOffsetOutRight = $LimitsFixMin;
										}
										if ( $WorkToCoverMaxX > 0 ){
											$LimitsOffsetOutRight += $WorkToCoverMaxX;
										}

									} elsif ( $LimitsLineToDenseMaxX > $CalcTol ) {
										$LineCmpDenseMaxX = 'Inside';
									}
									
									if ( $LimitsLineToDenseMaxY < ( 0 - $CalcTol ) ) {
										$LineCmpDenseMaxY = 'Outside';
#										$LimitsOffsetOutUp =  abs ( $LimitsLineToDenseMaxY ) * $OutsideFixFactor ;
										$LimitsOffsetOutUp =  abs ( $LimitsLineToCoverMaxY ) * $OutsideFixFactor ;
										if ( $LimitsOffsetOutUp < $LimitsFixMin ){
											$LimitsOffsetOutUp = $LimitsFixMin;
										}
										if ( $WorkToCoverMaxY > 0 ){
											$LimitsOffsetOutUp += $WorkToCoverMaxY;
										}
										
									} elsif ( $LimitsLineToDenseMaxY > $CalcTol ) {
										$LineCmpDenseMaxY = 'Inside';
									}
									
									#############################
									my $LimitsLineCmpDenseEqual = 'None';
									if ( ( $LineCmpDenseMinX eq 'Equal' ) or ( $LineCmpDenseMaxX eq 'Equal' ) ) {
										$LimitsLineCmpDenseEqual = 'X';
									}
									
									if ( ( $LineCmpDenseMinY eq 'Equal' ) or ( $LineCmpDenseMaxY eq 'Equal' ) ) {
										if ( $LimitsLineCmpDenseEqual eq 'None' ) {
											$LimitsLineCmpDenseEqual = 'Y';
										} else {
											$LimitsLineCmpDenseEqual = 'Both';
										}
									}
									#############################
									my $LimitsLineCmpDenseOut = 'None';
									if ( ( $LineCmpDenseMinX eq 'Outside' ) or ( $LineCmpDenseMaxX eq 'Outside' ) ) {
										$LimitsLineCmpDenseOut = 'X';
									}
									
									if ( ( $LineCmpDenseMinY eq 'Outside' ) or ( $LineCmpDenseMaxY eq 'Outside' ) ) {
										if ( $LimitsLineCmpDenseOut eq 'None' ) {
											$LimitsLineCmpDenseOut = 'Y';
										} else {
											$LimitsLineCmpDenseOut = 'Both';
										}
									}
									
#									$f->PAUSE("0,LimitsLineCmpDenseEqual=$LimitsLineCmpDenseEqual,LimitsLineCmpDenseOut=$LimitsLineCmpDenseOut");

									my $WorkLimitsCenterX =  $WorkLimitsMinX + ( $WorkLimitsMaxX  - $WorkLimitsMinX ) / 2 ;
									my $WorkLimitsCenterY =  $WorkLimitsMinY + ( $WorkLimitsMaxY  - $WorkLimitsMinY ) / 2 ;
									
									my ($LimitsOffsetEqualLeft,$LimitsOffsetEqualRight,$LimitsOffsetEqualUp,$LimitsOffsetEqualDown,) = (0,0,0,0,);#弧Limits =~ 线Limits
#									$f->PAUSE("0,WorkDenseData=@WorkDenseData");

									if ( $LineCmpDenseMaxY eq 'Equal' ) {  #上
										$LimitsOffsetEqualUp = $LimitsFixMin ;
										if ( $WorkToCoverMaxY > 0 ){
											$LimitsOffsetEqualUp += $WorkToCoverMaxY ;
										}
									}
									if ( $LineCmpDenseMinY eq 'Equal' ) {  #下
										$LimitsOffsetEqualDown = $LimitsFixMin ;
										if ( $WorkToCoverMinY > 0 ){
											$LimitsOffsetEqualDown += $WorkToCoverMinY ;
										}
									}
									if ( $LineCmpDenseMinX eq 'Equal' ) {  #左
										$LimitsOffsetEqualLeft = $LimitsFixMin ;
										if ( $WorkToCoverMinX > 0 ){
											$LimitsOffsetEqualLeft += $WorkToCoverMinX ;
										}
									}
									if ( $LineCmpDenseMaxX eq 'Equal' ) {  #右
										$LimitsOffsetEqualRight = $LimitsFixMin ;
										if ( $WorkToCoverMaxX > 0 ){
											$LimitsOffsetEqualRight += $WorkToCoverMaxX ;
										}
									}

#									$f->PAUSE("0=$LimitsOffsetEqualLeft,$LimitsOffsetEqualDown,$LimitsOffsetEqualRight,$LimitsOffsetEqualUp,");
									if ( $LimitsLineCmpDenseOut eq 'None' ) {
										if ( $LimitsLineCmpDenseEqual eq 'X' ) {
											$WorkLimitsMinX +=  $LimitsOffsetEqualLeft	;
											$WorkLimitsMaxX -=  $LimitsOffsetEqualRight	;
										} elsif ( $LimitsLineCmpDenseEqual eq 'Y' ) {
											$WorkLimitsMinY +=  $LimitsOffsetEqualDown	;
											$WorkLimitsMaxY -=  $LimitsOffsetEqualUp		;
										} elsif ( $LimitsLineCmpDenseEqual eq 'Both' ) {
											if ( abs ( $WorkCoverLimitsMaxX - $WorkCoverLimitsMinX ) > abs ( $WorkCoverLimitsMaxY - $WorkCoverLimitsMinY ) ) {
												$WorkLimitsMinX +=  $LimitsOffsetEqualLeft	;
												$WorkLimitsMaxX -=  $LimitsOffsetEqualRight	;
											} else {
												$WorkLimitsMinY +=  $LimitsOffsetEqualDown	;
												$WorkLimitsMaxY -=  $LimitsOffsetEqualUp		;
											}
										}
									} else {
										if ( $LimitsLineCmpDenseOut eq 'X' ) {
											my $tWorkToCover = ( abs ( $WorkLimitsMaxY - $WorkLimitsMinY )  - abs ( $WorkCoverLimitsMaxY - $WorkCoverLimitsMinY ) )  / 2;
											if ( $tWorkToCover > 0 ){
												$WorkLimitsMinX +=  $tWorkToCover;
												$WorkLimitsMaxX -=  $tWorkToCover;
											}
										} elsif ( $LimitsLineCmpDenseOut eq 'Y' ) {
											my $tWorkToCover = ( abs ( $WorkLimitsMaxX - $WorkLimitsMinX )  - abs ( $WorkCoverLimitsMaxX - $WorkCoverLimitsMinX ) )  / 2;
											if ( $tWorkToCover > 0 ){
												$WorkLimitsMinY +=  $tWorkToCover;
												$WorkLimitsMaxY -=  $tWorkToCover;
											}
										}
										$WorkLimitsMinX +=  $LimitsOffsetOutLeft		;
										$WorkLimitsMinY +=  $LimitsOffsetOutDown		;
										$WorkLimitsMaxX -=  $LimitsOffsetOutRight		;
										$WorkLimitsMaxY -=  $LimitsOffsetOutUp			;
									}
								}
							} else {
								$ZoomPlusMode = 'Normal';
							}
						}
					}


##########################################################################################################################################################

					
					
					
					if ( $tRunType =~ /^Scale/i ){
						if ( $tRunType eq 'Scale' or $tRunType eq 'ScaleX' ){
							my $tTmpScaleX1 = abs($WorkCoverLimitsCenterX - $WorkCoverLimitsMinX) / abs($WorkCoverLimitsCenterX - $WorkLimitsMinX);
							my $tTmpScaleX2 = abs($WorkCoverLimitsCenterX - $WorkCoverLimitsMaxX) / abs($WorkCoverLimitsCenterX - $WorkLimitsMaxX);
						
							if ($tTmpScaleX1 > $tScaleX ){
								$tScaleX = $tTmpScaleX1;
							}
							if ($tTmpScaleX2 > $tScaleX ){
								$tScaleX = $tTmpScaleX2;
							}
						}
						
						if ( $tRunType eq 'Scale' or $tRunType eq 'ScaleY' ){
							my $tTmpScaleY1 = abs($WorkCoverLimitsCenterY - $WorkCoverLimitsMinY) / abs($WorkCoverLimitsCenterY - $WorkLimitsMinY);
							my $tTmpScaleY2 = abs($WorkCoverLimitsCenterY - $WorkCoverLimitsMaxY) / abs($WorkCoverLimitsCenterY - $WorkLimitsMaxY);
							
							if ($tTmpScaleY1 > $tScaleY ){
								$tScaleY = $tTmpScaleY1;
							}
							if ($tTmpScaleY2 > $tScaleY ){
								$tScaleY = $tTmpScaleY2;
							}
						}
					} elsif ( $tRunType eq 'Expansion' ){
						my $tTmpDistanceX1 = abs($WorkCoverLimitsCenterX - $WorkCoverLimitsMinX) - abs($WorkCoverLimitsCenterX - $WorkLimitsMinX);
						my $tTmpDistanceX2 = abs($WorkCoverLimitsCenterX - $WorkCoverLimitsMaxX) - abs($WorkCoverLimitsCenterX - $WorkLimitsMaxX);
						my $tTmpDistanceY1 = abs($WorkCoverLimitsCenterY - $WorkCoverLimitsMinY) - abs($WorkCoverLimitsCenterY - $WorkLimitsMinY);
						my $tTmpDistanceY2 = abs($WorkCoverLimitsCenterY - $WorkCoverLimitsMaxY) - abs($WorkCoverLimitsCenterY - $WorkLimitsMaxY);
						my @SortDistance = sort { $a <=> $b }($tTmpDistanceX1,$tTmpDistanceX2,$tTmpDistanceY1,$tTmpDistanceY2,);
	#					$f->PAUSE("$tTmpDistanceX1,$tTmpDistanceX2,$tTmpDistanceY1,$tTmpDistanceY2,");

						$tExpansionSize = $SortDistance[$#SortDistance] * 2 * 1000;
						if ( $tExpansionSize < 0 ){
							$tExpansionSize = 0;
						}
					}



					$f->COM('affected_layer', name => $WorkCoverLayer, mode => 'single', affected => 'no');

		#			$f->COM('sel_clear_feat');
		#			$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
		#			$f->COM('set_filter_attributes', filter_name => 'popup', exclude_attributes => 'no', condition => 'yes', attribute => '.string', min_int_val => 0, max_int_val => 0, min_float_val => 0, max_float_val => 0, option => '', text => $TmpAttr);
		#			$f->COM('filter_area_strt');
		#			$f->COM('filter_area_end', filter_name => 'popup', operation => 'select');
		#			$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');

		#			$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
		#			$f->COM('set_filter_attributes', filter_name => 'popup', exclude_attributes => 'yes', condition => 'yes', attribute => '.string', min_int_val => 0, max_int_val => 0, min_float_val => 0, max_float_val => 0, option => '', text => $TmpAttr);
		#			$f->COM('filter_area_strt');
		#			$f->COM('filter_area_end', filter_name => 'popup', operation => 'unselect');
		#			$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');

					$f->COM('sel_clear_feat');
					if ( ( $tRunType =~ /^Scale/i and $tScaleX == 1 and $tScaleY == 1 ) or ( $tRunType eq 'Expansion' and $tExpansionSize == 0 ) ) {
	#					$f->PAUSE(011);
					} else {
#						$f->COM('sel_clear_feat');
						$f->COM('reset_filter_criteria' ,filter_name => '' ,criteria => 'all');
						$f->COM('set_filter_attributes' ,filter_name => 'popup' ,exclude_attributes => 'no' ,condition => 'yes' ,attribute => '.string' ,min_int_val => 0 ,max_int_val => 0 ,min_float_val => 0 ,max_float_val => 0 ,option => '' ,text => $TmpAttr);
						$f->COM('filter_area_strt');
						$f->COM('filter_area_end' ,filter_name => 'popup' ,operation => 'select');
					}
	#				$f->PAUSE("$tRunType=$tExpansionSize");
					
					$f->COM('get_select_count');
					if ( $f->{COMANS} != 0 ) {
						my $tNextUndo = 0;
						if ( $tRunType =~ /^Scale/i ){
							$f->COM('sel_delete_atr', mode => 'list', attributes => '.bit;.string', attr_vals => $TmpAttr. ';' . $TmpAttr );
							$f->COM('cur_atr_reset');
							$f->COM('sel_transform', x_anchor => $WorkCoverLimitsCenterX, y_anchor => $WorkCoverLimitsCenterY, x_scale => $tScaleX, y_scale => $tScaleY, oper => 'scale', angle => 0, direction => 'ccw', x_offset => 0, y_offset => 0, mode => 'anchor', duplicate => 'no');
							$tNextUndo = 1;
						} elsif ( $tRunType eq 'Expansion' ){
							$f->VOF;
							if ( $tExpansionSize != 0 ) {
								$f->COM('sel_resize_poly' ,size => $tExpansionSize);
								my $STATUS = $f->{STATUS};
								if ( $STATUS == 0 ) {
									$tNextUndo = 1;
								} else {
									$f->COM('rv_tab_empty' ,report => 'design2rout_rep' ,is_empty => 'yes');
									$f->COM('sel_design2rout' ,det_tol => 1 ,con_tol => 1 ,rad_tol => 0.1);
									$f->COM('rv_tab_view_results_enabled' ,report => 'design2rout_rep' ,is_enabled => 'no' ,serial_num => -1 ,all_count => -1);
									
		#							$f->COM('reset_filter_criteria' ,filter_name => '' ,criteria => 'all');
		#							$f->COM('set_filter_attributes' ,filter_name => 'popup' ,exclude_attributes => 'no' ,condition => 'yes' ,attribute => '.string' ,min_int_val => 0 ,max_int_val => 0 ,min_float_val => 0 ,max_float_val => 0 ,option => '' ,text => $TmpAttr);
									$f->COM('filter_area_strt');
									$f->COM('filter_area_end' ,filter_name => 'popup' ,operation => 'select');
		#							$f->COM('reset_filter_criteria' ,filter_name => '' ,criteria => 'all');
									$f->COM('get_select_count');
									if ( $f->{COMANS} != 0 ) {
										$f->COM('sel_resize_poly' ,size => $tExpansionSize);
										my $STATUS = $f->{STATUS};
										if ( $STATUS == 0 ) {
											$tNextUndo = 2;
										} else {
											$f->COM('sel_clear_feat');
										}
									} else {
		#								$f->COM('sel_clear_feat');
										$tNextUndo = 1;
									}
								}
							}
							$f->VON;
						}

						$f->COM('get_select_count');
						if ( $f->{COMANS} != 0 ) {
							$f->COM('sel_create_sym', symbol => $TmpWordBoxSy, x_datum => $WorkCoverLimitsCenterX, y_datum => $WorkCoverLimitsCenterY, delete => 'no', fill_dx => '0.1', fill_dy => '0.1', attach_atr => 'no', retain_atr => 'no');
						}
						if ( $tNextUndo > 0 ) {
							$f->COM('undo', depth => $tNextUndo);
							if ( ( $tRunType eq 'Expansion' ) and ( $tNextUndo == 2 ) ) {
								$f->COM('filter_area_strt');
								$f->COM('filter_area_end' ,filter_name => 'popup' ,operation => 'select');
								$f->COM('get_select_count');
								if ( $f->{COMANS} != 0 ) {
#									$f->COM('sel_delete_atr', mode => 'list', attributes => '.string', attr_vals => $TmpAttr);
									$f->COM('sel_delete_atr', mode => 'list', attributes => '.bit;.string', attr_vals => $TmpAttr. ';' . $TmpAttr );
									$f->COM('cur_atr_reset');
								}
							}
						}
						$f->COM('get_select_count');
						if ( $f->{COMANS} != 0 ) {
							$f->COM('sel_substitute', mode => 'substitute', dcode => 0, symbol => $TmpWordBoxSy, x_datum => $WorkCoverLimitsCenterX, y_datum => $WorkCoverLimitsCenterY, tol => 1, rotation => 0);
						}
					}
				} else {
					$f->COM('affected_layer', name => $WorkCoverLayer, mode => 'single', affected => 'no');
					$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
					$f->COM('set_filter_attributes', filter_name => 'popup', exclude_attributes => 'no', condition => 'yes', attribute => '.string', min_int_val => 0, max_int_val => 0, min_float_val => 0, max_float_val => 0, option => '', text => $TmpAttr);
					$f->COM('filter_area_strt');
					$f->COM('filter_area_end', filter_name => 'popup', operation => 'select');

					#删除属性
#					$f->COM('sel_delete_atr', mode => 'list', attributes => '.string', attr_vals => $TmpAttr);
					$f->COM('sel_delete_atr', mode => 'list', attributes => '.bit;.string', attr_vals => $TmpAttr. ';' . $TmpAttr );
					$f->COM('sel_clear_feat');

					$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
					$f->COM('sel_options', clear_mode => 'clear_after', display_mode => 'all_layers', area_inout => 'inside', area_select => 'select', select_mode => 'standard', area_touching_mode => 'exclude');
					goto SemiAutoWordBoxZoomMultipleEnd;
				}
			} else {
				$f->COM('affected_layer', name => $WorkCoverLayer, mode => 'single', affected => 'no');
				$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
				$f->COM('set_filter_attributes', filter_name => 'popup', exclude_attributes => 'no', condition => 'yes', attribute => '.string', min_int_val => 0, max_int_val => 0, min_float_val => 0, max_float_val => 0, option => '', text => $TmpAttr);
				$f->COM('filter_area_strt');
				$f->COM('filter_area_end', filter_name => 'popup', operation => 'select');

				#删除属性
				$f->COM('sel_delete_atr', mode => 'list', attributes => '.bit;.string', attr_vals => $TmpAttr. ';' . $TmpAttr );
				$f->COM('sel_clear_feat');

				$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
				$f->COM('sel_options', clear_mode => 'clear_after', display_mode => 'all_layers', area_inout => 'inside', area_select => 'select', select_mode => 'standard', area_touching_mode => 'exclude');
				goto SemiAutoWordBoxZoomMultipleEnd;
			}
			$f->COM('reset_filter_criteria' ,filter_name => '' ,criteria => 'all');
		}

		$f->COM('sel_multi_feat', operation => 'select', feat_types => 'pad', include_syms => $TmpWordBoxSy, is_extended => 'no', clear_prev => 'yes');
		$f->COM('get_select_count');
		if ( $f->{COMANS} != 0 ) {
			$f->COM('sel_move_other', target_layer => $WorkOkLayer, invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0);
			$f->COM('affected_layer', name => $WorkOkLayer, mode => 'single', affected => 'yes');
			$f->COM('sel_multi_feat', operation => 'select', feat_types => 'pad', include_syms => $TmpWordBoxSy, is_extended => 'no', clear_prev => 'yes');
			$f->COM('get_select_count');
			if ( $f->{COMANS} != 0 ) {
				$f->COM('sel_break');
			}
			$f->COM('affected_layer', name => $WorkOkLayer, mode => 'single', affected => 'no');
		}

		$f->COM('sel_options', clear_mode => 'clear_after', display_mode => 'all_layers', area_inout => 'inside', area_select => 'select', select_mode => 'standard', area_touching_mode => 'exclude');

		$f->COM('get_disp_layers');
		my @DispLayers = split (" ",$f->{COMANS});
		my $WorkOkLayerDispJud = 'no';
		for ( @DispLayers ){
			if( $_ eq  $WorkOkLayer ){
				$WorkOkLayerDispJud = 'yes';
				last;
			}
		}
		if ( $WorkOkLayerDispJud eq 'no' ) {
			$f->COM('display_layer', name => $WorkOkLayer, display => 'yes');
		}
		#
	}#########################
	SemiAutoWordBoxZoomMultipleEnd:;
	if( $tMode eq 'Multiple' ) {
		goto SemiAutoWordBoxZoomMultipleRun;
	}
}

sub ManualWordBoxZoom {  #手动缩放文字框
	#&RunScriptAct($MyScriptFile,'WordBoxZoom','Single',$CoverLayerSuffix);
	#&RunScriptAct($MyScriptFile,'WordBoxZoom','Multiple',$CoverLayerSuffix);
	my $RunSubScr = shift;
#	my $tMode = shift;#Single #Multiple
#	my $CoverLayerSuffix = shift;
	my ($tMode,$CoverLayerSuffix,$tScaleX,$tScaleY) = @_;

	my $TmpWordBoxSy = 'neo_silk-tmp+';
	#工作层
	$f->COM('get_work_layer');
	my $WorkLayer = $f->{COMANS};
	if ( $WorkLayer eq '' ) {
		&MsgBox("没有工作层","warning","ok","没有工作层,脚本退出",);
		exit;
	}

	&GetJobStep;
	my $WorkCoverLayer = $WorkLayer . $CoverLayerSuffix;
	$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$WorkCoverLayer",data_type => 'EXISTS');
	if ( $f->{doinfo}{gEXISTS} eq 'no' ) {
		&MsgBox("套层不存在","warning","ok","套层 $WorkCoverLayer 不存在,脚本退出",);
		exit;
	}

	my $WorkOkSuffix = '-ok+';
	my $WorkOkLayer = $WorkLayer . $WorkOkSuffix;
	$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$WorkOkLayer",data_type => 'EXISTS');
	if ( $f->{doinfo}{gEXISTS} eq 'no' ) {
		$f->VOF;
		$f->COM('create_layer', layer => $WorkOkLayer, context => 'board', type => 'document', polarity => 'positive');
		$f->COM('create_layer', layer => $WorkOkLayer, type => 'document',);
		$f->VON;
		$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$WorkLayer",data_type => 'ROW');
		my $WorkLayerRow = $f->{doinfo}{gROW};
		$f->INFO(entity_type => 'layer',entity_path => "$JOB/$STEP/$WorkLayer",data_type => 'SIDE');
      if ( $f->{doinfo}{gSIDE} eq 'bottom' ) {
			$WorkLayerRow = $f->{doinfo}{gROW} + 1;
      }
		$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$WorkOkLayer",data_type => 'ROW');
		my $WorkOkLayerRow = $f->{doinfo}{gROW};
		$f->COM('matrix_move_row', job => $JOB, matrix => 'matrix', row => $WorkOkLayerRow, ins_row => $WorkLayerRow);
	}
	my $BoxSelTol = 0.001;#框选套层公差
#	my $BoxSelTol = 0.003;#框选套层公差
	if( $tMode eq 'Multiple' ) {
		$f->COM('copy_layer', source_job => $JOB, source_step => $STEP, source_layer => $WorkLayer, dest => 'layer_name', dest_layer => $WorkLayer . '-bak+', mode => 'replace', invert => 'no');
	}
	WordBoxZoomMultipleRun:;
	$f->COM('affected_layer', name => '', mode => 'all', affected => 'no');

	$f->COM('units', type => 'inch');
#	my ($X1,$Y1,$X2,$Y2,);
	$f->COM('get_select_count');
	if ( $f->{COMANS} == 0 ) {
		if( $tMode eq 'Single' ) {
			exit;
		} elsif( $tMode eq 'Multiple' ) {
			$f->MOUSE("r Please select the text box you want to enlarge.");
			($X1,$Y1,$X2,$Y2,) = split(/ /,$f->{MOUSEANS});
			$f->COM('filter_area_strt');
			$f->COM('filter_area_xy', x => $X1, y => $Y1);
			$f->COM('filter_area_xy', x => $X2, y => $Y2);
			$f->COM('filter_area_end', layer => '', filter_name => 'popup', operation => 'select', area_type => 'rectangle', inside_area => 'yes', intersect_area => 'no');
			$f->COM('get_select_count');
			my $tSelNum = $f->{COMANS};

#			while ( $f->{COMANS} == 0 ) {
			while ( $tSelNum == 0 ) {
				my $SelJud = &MsgBox("未选择物件","warning","yesno","没有选择任何物件,是否退出脚本?",);
				if( lc($SelJud) eq 'yes' ){
					exit(0);
					last;
				}
				#
				$f->MOUSE("r Please select the text box you want to enlarge.");
				my ($X1,$Y1,$X2,$Y2,) = split(/ /,$f->{MOUSEANS});
				$f->COM('filter_area_strt');
				$f->COM('filter_area_xy', x => $X1, y => $Y1);
				$f->COM('filter_area_xy', x => $X2, y => $Y2);
				$f->COM('filter_area_end', layer => '', filter_name => 'popup', operation => 'select', area_type => 'rectangle', inside_area => 'yes', intersect_area => 'no');
				$f->COM('get_select_count');
				$tSelNum = $f->{COMANS};
			}
		}
	}


#	#获取框选区域的 物件的 LIMITS 和 物件FEATURES #获取最小线
##	my $MinLineSize = 0 ;
#	my $MinLineSize = 3 ;
#	my $tMinLineSize = 100 ;
#	my $tInfoFile = $ENV{GENESIS_TMP} . '/info.' . int(rand(9999));
#	$f->COM ( 'info',out_file => $tInfoFile,args => " -t layer -e $JOB/$STEP/$WorkLayer -d FEATURES -o select" ) ;
#	open ( FH,"<$tInfoFile" ) ;
#	while ( <FH> ) {
#		my $line = $_;
#		my ( $Size,$Positive ) = (0,'N');
#		if ( $line =~ /\#L/ ) {
#			#L 1.80117 8.85592 1.79867 8.85717 r4.5 P 19
#			( $Size,$Positive ) = ( split ( ' ',$line ) ) [5,6,];
#		}elsif ( $line =~ /\#A/ ) {
#			#A 1.96316 9.02362 1.96316 9.02362 1.89566 9.02362 r12 P 12 Y
#			( $Size,$Positive ) = ( split ( ' ',$line ) ) [7,8,];
#		}
#		if ( $Positive eq 'P' ) {
#			$Size =~ s/r//;
##			if ( $Size > $MinLineSize ) {
#			if ( $Size < $tMinLineSize ) {
#				$tMinLineSize = $Size ;
#			}
#		}
#	}
#	close FH;
#	unlink $tInfoFile;
#	if ( $tMinLineSize != 100 and $tMinLineSize > $MinLineSize ) {
#		$MinLineSize = $tMinLineSize;
#	}
#
#	my $MinLineSizeInch = $MinLineSize / 1000;
	$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$WorkLayer",data_type => 'LIMITS',options => "select");
	my $WorkLimitsMinX =  $f->{doinfo}{gLIMITSxmin} + $MinLineSizeInch;
	my $WorkLimitsMinY =  $f->{doinfo}{gLIMITSymin} + $MinLineSizeInch;
	my $WorkLimitsMaxX =  $f->{doinfo}{gLIMITSxmax} - $MinLineSizeInch;
	my $WorkLimitsMaxY =  $f->{doinfo}{gLIMITSymax} - $MinLineSizeInch;
	$f->COM('sel_options', clear_mode => 'clear_none', display_mode => 'displayed_layers', area_inout => 'inside', area_select => 'select', select_mode => 'standard', area_touching_mode => 'exclude');
	#
	my $TmpAttr = 'neo_silk-tmp1.' . int(rand(99999999));
	$f->COM('cur_atr_reset');
	$f->COM('cur_atr_set', attribute => '.string', text => $TmpAttr);
	$f->COM('sel_change_atr', mode => 'add');

	#框选区域 FEATURES+单边1mil 获取套层 选中的 LIMITS
	$f->COM('affected_layer', name => $WorkCoverLayer, mode => 'single', affected => 'yes');
#	$f->COM('sel_clear_feat');
	$f->COM('filter_area_strt');
#	$f->COM('filter_area_xy', x => $WorkLimitsMinX - $BoxSelTol, y => $WorkLimitsMinY - $BoxSelTol);
#	$f->COM('filter_area_xy', x => $WorkLimitsMaxX + $BoxSelTol, y => $WorkLimitsMaxY + $BoxSelTol);
	$f->COM('filter_area_xy', x => $f->{doinfo}{gLIMITSxmin} - $BoxSelTol, y => $f->{doinfo}{gLIMITSymin} - $BoxSelTol);
	$f->COM('filter_area_xy', x => $f->{doinfo}{gLIMITSxmax} + $BoxSelTol, y => $f->{doinfo}{gLIMITSymax} + $BoxSelTol);

	$f->COM('filter_area_end', layer => '', filter_name => 'popup', operation => 'select', area_type => 'rectangle', inside_area => 'yes', intersect_area => 'no');
	$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$WorkCoverLayer",data_type => 'LIMITS',options => "select");
	my $WorkCoverLimitsMinX =  $f->{doinfo}{gLIMITSxmin};
	my $WorkCoverLimitsMinY =  $f->{doinfo}{gLIMITSymin};
	my $WorkCoverLimitsMaxX =  $f->{doinfo}{gLIMITSxmax};
	my $WorkCoverLimitsMaxY =  $f->{doinfo}{gLIMITSymax};

	my $WorkCoverLimitsCenterX =  $WorkCoverLimitsMinX + ( $WorkCoverLimitsMaxX  - $WorkCoverLimitsMinX ) / 2 ;
	my $WorkCoverLimitsCenterY =  $WorkCoverLimitsMinY + ( $WorkCoverLimitsMaxY  - $WorkCoverLimitsMinY ) / 2 ;
#	my ($tScaleX,$tScaleY,) = (1,1,);
#	my $tTmpScaleX1 = abs($WorkCoverLimitsCenterX - $WorkCoverLimitsMinX) / abs($WorkCoverLimitsCenterX - $WorkLimitsMinX);
#	my $tTmpScaleX2 = abs($WorkCoverLimitsCenterX - $WorkCoverLimitsMaxX) / abs($WorkCoverLimitsCenterX - $WorkLimitsMaxX);
#	if ($tTmpScaleX1 > $tScaleX ){
#		$tScaleX = $tTmpScaleX1;
#	}
#	if ($tTmpScaleX2 > $tScaleX ){
#		$tScaleX = $tTmpScaleX2;
#	}

#	my $tTmpScaleY1 = abs($WorkCoverLimitsCenterY - $WorkCoverLimitsMinY) / abs($WorkCoverLimitsCenterY - $WorkLimitsMinY);
#	my $tTmpScaleY2 = abs($WorkCoverLimitsCenterY - $WorkCoverLimitsMaxY) / abs($WorkCoverLimitsCenterY - $WorkLimitsMaxY);
#	if ($tTmpScaleY1 > $tScaleY ){
#		$tScaleY = $tTmpScaleY1;
#	}
#	if ($tTmpScaleY2 > $tScaleY ){
#		$tScaleY = $tTmpScaleY2;
#	}

	$f->COM('affected_layer', name => $WorkCoverLayer, mode => 'single', affected => 'no');

#	$f->COM('sel_clear_feat');
#	$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
#	$f->COM('set_filter_attributes', filter_name => 'popup', exclude_attributes => 'no', condition => 'yes', attribute => '.string', min_int_val => 0, max_int_val => 0, min_float_val => 0, max_float_val => 0, option => '', text => $TmpAttr);
#	$f->COM('filter_area_strt');
#	$f->COM('filter_area_end', filter_name => 'popup', operation => 'select');
#	$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');

	$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
	$f->COM('set_filter_attributes', filter_name => 'popup', exclude_attributes => 'yes', condition => 'yes', attribute => '.string', min_int_val => 0, max_int_val => 0, min_float_val => 0, max_float_val => 0, option => '', text => $TmpAttr);
	$f->COM('filter_area_strt');
	$f->COM('filter_area_end', filter_name => 'popup', operation => 'unselect');
	$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
	$f->COM('get_select_count');
	if ( $f->{COMANS} != 0 ) {
		$f->COM('sel_delete_atr', mode => 'list', attributes => '.string', attr_vals => $TmpAttr);
		$f->COM('cur_atr_reset');
		#

		$f->COM('sel_transform', x_anchor => $WorkCoverLimitsCenterX, y_anchor => $WorkCoverLimitsCenterY, x_scale => $tScaleX, y_scale => $tScaleY, oper => 'scale', angle => 0, direction => 'ccw', x_offset => 0, y_offset => 0, mode => 'anchor', duplicate => 'no');
		#
		$f->COM('sel_create_sym', symbol => $TmpWordBoxSy, x_datum => $WorkCoverLimitsCenterX, y_datum => $WorkCoverLimitsCenterY, delete => 'no', fill_dx => '0.1', fill_dy => '0.1', attach_atr => 'no', retain_atr => 'no');
		$f->COM('undo', depth => 1);
		$f->COM('sel_substitute', mode => 'substitute', dcode => 0, symbol => $TmpWordBoxSy, x_datum => $WorkCoverLimitsCenterX, y_datum => $WorkCoverLimitsCenterY, tol => 1, rotation => 0);
	}
	$f->COM('sel_multi_feat', operation => 'select', feat_types => 'pad', include_syms => $TmpWordBoxSy, is_extended => 'no', clear_prev => 'yes');
	$f->COM('get_select_count');
	if ( $f->{COMANS} != 0 ) {
		$f->COM('sel_move_other', target_layer => $WorkOkLayer, invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0);
		$f->COM('affected_layer', name => $WorkOkLayer, mode => 'single', affected => 'yes');
		$f->COM('sel_multi_feat', operation => 'select', feat_types => 'pad', include_syms => $TmpWordBoxSy, is_extended => 'no', clear_prev => 'yes');
		$f->COM('get_select_count');
		if ( $f->{COMANS} != 0 ) {
			$f->COM('sel_break');
		}
		$f->COM('affected_layer', name => $WorkOkLayer, mode => 'single', affected => 'no');
	}

	$f->COM('get_disp_layers');
	my @DispLayers = split (" ",$f->{COMANS});
	my $WorkOkLayerDispJud = 'no';
	for ( @DispLayers ){
		if( $_ eq  $WorkOkLayer ){
			$WorkOkLayerDispJud = 'yes';
			last;
		}
	}
	if ( $WorkOkLayerDispJud eq 'no' ) {
		$f->COM('display_layer', name => $WorkOkLayer, display => 'yes');
	}
	#
	$f->COM('sel_options', clear_mode => 'clear_after', display_mode => 'all_layers', area_inout => 'inside', area_select => 'select', select_mode => 'standard', area_touching_mode => 'exclude');
	if( $tMode eq 'Multiple' ) {
		goto WordBoxZoomMultipleRun;
	}
}

sub ManualTextBoxExternalExpansion {#手动按外扩字符框
	my $RunSubScr = shift;
	my ($tMode,$tPolylineResize,) = @_;


	my $TmpWordBoxSy = 'neo_silk-tmp+';

	#工作层
	$f->COM('get_work_layer');
	my $WorkLayer = $f->{COMANS};
	if ( $WorkLayer eq '' ) {
		&MsgBox("没有工作层","warning","ok","没有工作层,脚本退出",);
		exit;
	}
	my $WorkOkSuffix = '-ok+';
	my $WorkOkLayer = $WorkLayer . $WorkOkSuffix;



	&GetJobStep;
	if( $tMode eq 'Multiple' ) {
		$f->COM('copy_layer', source_job => $JOB, source_step => $STEP, source_layer => $WorkLayer, dest => 'layer_name', dest_layer => $WorkLayer . '-bak+', mode => 'replace', invert => 'no');
	}

	ManualTextBoxExternalExpansionRun:;
	$f->COM('units', type => 'inch');
	$f->COM('get_select_count');
	if ( $f->{COMANS} == 0 ) {
		if( $tMode eq 'Single' ) {
			exit;
		} elsif( $tMode eq 'Multiple' ) {
			$f->MOUSE("r Please select the text box you want to enlarge.");
			($X1,$Y1,$X2,$Y2,) = split(/ /,$f->{MOUSEANS});
			$f->COM('filter_area_strt');
			$f->COM('filter_area_xy', x => $X1, y => $Y1);
			$f->COM('filter_area_xy', x => $X2, y => $Y2);
			$f->COM('filter_area_end', layer => '', filter_name => 'popup', operation => 'select', area_type => 'rectangle', inside_area => 'yes', intersect_area => 'no');
			$f->COM('get_select_count');
			my $tSelNum = $f->{COMANS};
			while ( $tSelNum == 0 ) {
				my $SelJud = &MsgBox("未选择物件","warning","yesno","没有选择任何物件,是否退出脚本?",);
				if( lc($SelJud) eq 'yes' ){
					exit(0);
					last;
				}
				#
				$f->MOUSE("r Please select the text box you want to enlarge.");
				my ($X1,$Y1,$X2,$Y2,) = split(/ /,$f->{MOUSEANS});
				$f->COM('filter_area_strt');
				$f->COM('filter_area_xy', x => $X1, y => $Y1);
				$f->COM('filter_area_xy', x => $X2, y => $Y2);
				$f->COM('filter_area_end', layer => '', filter_name => 'popup', operation => 'select', area_type => 'rectangle', inside_area => 'yes', intersect_area => 'no');
				$f->COM('get_select_count');
				$tSelNum = $f->{COMANS};
			}
		}
	}

	$f->COM('affected_layer', name => '', mode => 'all', affected => 'no');
	$f->COM('units', type => 'inch');
	$f->COM('sel_options', clear_mode => 'clear_none', display_mode => 'displayed_layers', area_inout => 'inside', area_select => 'select', select_mode => 'standard', area_touching_mode => 'exclude');
	$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$WorkLayer",data_type => 'LIMITS',options => "select");
	my $WorkLimitsCenterX = ($f->{doinfo}{gLIMITSxmax} + $f->{doinfo}{gLIMITSxmin} ) / 2 ;
	my $WorkLimitsCenterY = ($f->{doinfo}{gLIMITSymax} + $f->{doinfo}{gLIMITSymin} ) / 2 ;

	$f->COM('sel_resize_poly', size => $tPolylineResize);
	#
	$f->COM('sel_create_sym', symbol => $TmpWordBoxSy, x_datum => $WorkLimitsCenterX, y_datum => $WorkLimitsCenterY, delete => 'no', fill_dx => '0.1', fill_dy => '0.1', attach_atr => 'no', retain_atr => 'no');
	$f->COM('undo', depth => 1);
	$f->COM('sel_substitute', mode => 'substitute', dcode => 0, symbol => $TmpWordBoxSy, x_datum => $WorkLimitsCenterX, y_datum => $WorkLimitsCenterY, tol => 1, rotation => 0);

	$f->COM('sel_multi_feat', operation => 'select', feat_types => 'pad', include_syms => $TmpWordBoxSy, is_extended => 'no', clear_prev => 'yes');
	$f->COM('get_select_count');
	if ( $f->{COMANS} != 0 ) {
		$f->COM('sel_move_other', target_layer => $WorkOkLayer, invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0);
		$f->COM('affected_layer', name => $WorkOkLayer, mode => 'single', affected => 'yes');
		$f->COM('sel_multi_feat', operation => 'select', feat_types => 'pad', include_syms => $TmpWordBoxSy, is_extended => 'no', clear_prev => 'yes');
		$f->COM('get_select_count');
		if ( $f->{COMANS} != 0 ) {
			$f->COM('sel_break');
		}
		$f->COM('affected_layer', name => $WorkOkLayer, mode => 'single', affected => 'no');
	}

	$f->COM('get_disp_layers');
	my @DispLayers = split (" ",$f->{COMANS});
	my $WorkOkLayerDispJud = 'no';
	for ( @DispLayers ){
		if( $_ eq  $WorkOkLayer ){
			$WorkOkLayerDispJud = 'yes';
			last;
		}
	}
	if ( $WorkOkLayerDispJud eq 'no' ) {
		$f->COM('display_layer', name => $WorkOkLayer, display => 'yes');
	}

	$f->COM('sel_options', clear_mode => 'clear_after', display_mode => 'all_layers', area_inout => 'inside', area_select => 'select', select_mode => 'standard', area_touching_mode => 'exclude');

	if( $tMode eq 'Multiple' ) {
		goto ManualTextBoxExternalExpansionRun;
	}
}

sub ReplaceSimilar {  #手动同类替换物件
	my $RunSubScr = shift;
	my $ReplaceSimilarTol = shift;
	#
	my $ReplaceSimilarRand = int(rand(99999999));
	$f->COM('get_select_count');
	if ( $f->{COMANS} == 0 ) {
		exit;
	}

	$f->COM('get_work_layer');
	my $WorkLayer = $f->{COMANS};
	if ( $WorkLayer eq '' ) {
#		&MsgBox("没有工作层","warning","ok","没有工作层,脚本退出",);
		exit;
	}

	my $TmpWordBoxSy = 'neo_silk-tmp+';
	my $TmpAttr = 'neo_silk-tmp' . $ReplaceSimilarRand;
	my $TmpConvLayer = $WorkLayer . '-conv++';

	$f->COM('sel_options', clear_mode => 'clear_none', display_mode => 'all_layers', area_inout => 'inside', area_select => 'select', select_mode => 'standard', area_touching_mode => 'exclude');
	$f->COM('cur_atr_reset');
	$f->COM('cur_atr_set', attribute => '.string', text => $TmpAttr);
	$f->COM('sel_change_atr', mode => 'add');
	$f->VOF;
	$f->COM('truncate_layer', layer => $TmpConvLayer);
	$f->VON;
	$f->COM('sel_copy_other', dest => 'layer_name', target_layer => $TmpConvLayer, invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0);
	$f->COM('cur_atr_reset');
	$f->COM('sel_options', clear_mode => 'clear_after', display_mode => 'all_layers', area_inout => 'inside', area_select => 'select', select_mode => 'standard', area_touching_mode => 'exclude');

	&GetJobStep;
	$f->PAUSE("请修改完后并选中后再点击此处.");
	$f->COM('get_select_count');
	my $tSelNum = $f->{COMANS};
	while ( $tSelNum == 0 ) {
		$f->PAUSE("没有选择物件,请选择后再点击此处.");
		$f->COM('get_select_count');
		$tSelNum = $f->{COMANS};
	}
	$f->COM('get_units');
	my $CurrUnits = $f->{COMANS};
	$f->COM('units', type => 'inch');
	$f->INFO(entity_type => 'layer',entity_path => "$JOB/$STEP/$TmpConvLayer",data_type => 'LIMITS');
	my $WorkLimitsCenterX = ($f->{doinfo}{gLIMITSxmax} + $f->{doinfo}{gLIMITSxmin} ) / 2 ;
	my $WorkLimitsCenterY = ($f->{doinfo}{gLIMITSymax} + $f->{doinfo}{gLIMITSymin} ) / 2 ;

	$f->COM('sel_create_sym', symbol => $TmpWordBoxSy, x_datum => $WorkLimitsCenterX, y_datum => $WorkLimitsCenterY, delete => 'yes', fill_dx => '0.1', fill_dy => '0.1', attach_atr => 'no', retain_atr => 'no');
	$f->COM('copy_layer', source_job => $JOB, source_step => $STEP, source_layer => $TmpConvLayer, dest => 'layer_name', dest_step => '', dest_layer => $WorkLayer, mode => 'append', invert => 'no', );
	$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
	$f->COM('set_filter_attributes', filter_name => 'popup', exclude_attributes => 'no', condition => 'yes', attribute => '.string', min_int_val => 0, max_int_val => 0, min_float_val => 0, max_float_val => 0, option => '', text => $TmpAttr);
	$f->COM('filter_area_strt');
	$f->COM('filter_area_end', filter_name => 'popup', operation => 'select');
	$f->COM('get_select_count');
	if ( $f->{COMANS} != 0 ) {
		$f->COM('sel_substitute', mode => 'substitute', dcode => 0, symbol => $TmpWordBoxSy,  x_datum => $WorkLimitsCenterX, y_datum => $WorkLimitsCenterY, tol => $ReplaceSimilarTol, rotation => 0);
#		$f->COM('sel_multi_feat', operation => 'select', feat_types => 'pad', include_syms => $TmpWordBoxSy, is_extended => 'no', clear_prev => 'yes');
#		$f->COM('get_select_count');
#		if ( $f->{COMANS} != 0 ) {
			$f->COM('sel_delete_atr', mode => 'list', attributes => '.string');
#		}
		$f->COM('sel_multi_feat', operation => 'select', feat_types => 'pad', include_syms => $TmpWordBoxSy, is_extended => 'no', clear_prev => 'yes');
		$f->COM('get_select_count');
		if ( $f->{COMANS} != 0 ) {
			$f->COM('sel_break');
		}
	}
	$f->COM('truncate_layer', layer => $TmpConvLayer);
	$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
	if ( $CurrUnits ne 'inch' ) {
		$f->COM('units', type => $CurrUnits);
	}
}

sub TextWidthHeightZoom {#手动按指定宽和高拉伸字符 X Y 自动判断高和宽
	my $RunSubScr = shift;
	#Single Multiple AutoSingle AutoMultiple
	my ($tMode,$tTextCategoryOption,$tWidth,$tHeight,$tMirror) = @_;


#	use Time::HiRes  qw( usleep );

#	$f->COM('get_work_layer');
#	$WorkLayer = $f->{COMANS};
	#
	#工作层
	$f->COM('get_work_layer');
	my $WorkLayer = $f->{COMANS};
	if ( $WorkLayer eq '' ) {
		&MsgBox("没有工作层","warning","ok","没有工作层,脚本退出",);
		exit;
	}
	#
	&GetJobStep;
	if( ( $tMode eq 'Multiple' ) or ( $tMode eq 'AutoMultiple' ) ) {
		$f->COM('copy_layer', source_job => $JOB, source_step => $STEP, source_layer => $WorkLayer, dest => 'layer_name', dest_layer => $WorkLayer . '-bak+', mode => 'replace', invert => 'no');
	}

	my @TmpLayers = ($WorkLayer . "-tmp1+", $WorkLayer . "-tmp2+", $WorkLayer . "-tmp3+", $WorkLayer . "-tmp4+", $WorkLayer . "-tmp5+",);
	&DelLayers(@TmpLayers);
	#
	my @DispLayers;
	TextWidthHeightZoomMultipleRun:;

	$f->COM('units', type => 'inch');
	$f->COM('affected_layer', name => '', mode => 'all', affected => 'no');
#	my ($X1,$Y1,$X2,$Y2,);
	$f->COM('get_select_count');
	if ( $f->{COMANS} == 0 ) {
		if( ( $tMode eq 'Single' ) or ( $tMode eq 'AutoSingle' ) ) {
			exit;
		} elsif( ( $tMode eq 'Multiple' ) or ( $tMode eq 'AutoMultiple' ) ) {
			$f->MOUSE("r Please select the text you want to enlarge.");
			my ($X1,$Y1,$X2,$Y2,) = split(/ /,$f->{MOUSEANS});
			$f->COM('filter_area_strt');
			$f->COM('filter_area_xy', x => $X1, y => $Y1);
			$f->COM('filter_area_xy', x => $X2, y => $Y2);
			$f->COM('filter_area_end', layer => '', filter_name => 'popup', operation => 'select', area_type => 'rectangle', inside_area => 'yes', intersect_area => 'no');
			$f->COM('get_select_count');
			my $tSelNum = $f->{COMANS};
			while ( $tSelNum == 0 ) {
				my $SelJud = &MsgBox("未选择物件","warning","yesno","没有选择任何物件,是否退出脚本?",);
				if( lc($SelJud) eq 'yes' ){
					exit(0);
					last;
				}
				#
				$f->MOUSE("r Please select the text you want to enlarge.");
				my ($X1,$Y1,$X2,$Y2,) = split(/ /,$f->{MOUSEANS});
				$f->COM('filter_area_strt');
				$f->COM('filter_area_xy', x => $X1, y => $Y1);
				$f->COM('filter_area_xy', x => $X2, y => $Y2);
				$f->COM('filter_area_end', layer => '', filter_name => 'popup', operation => 'select', area_type => 'rectangle', inside_area => 'yes', intersect_area => 'no');
				$f->COM('get_select_count');
				$tSelNum = $f->{COMANS};
			}
		}
	}

	$f->COM('sel_options', clear_mode => 'clear_none', display_mode => 'displayed_layers', area_inout => 'inside', area_select => 'select', select_mode => 'standard', area_touching_mode => 'exclude');
#	$f->PAUSE("ddhd");
#	$f->COM('copy_layer', source_job => $JOB, source_step => $STEP, source_layer => $WorkLayer, dest => 'layer_name', dest_layer => $TmpLayers[1], mode => 'replace', invert => 'no');
	$f->COM('sel_copy_other', dest => 'layer_name', target_layer => $TmpLayers[1], invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0, rotation => 0, mirror => 'none');
#	$f->PAUSE("$TmpLayers[1]");

	$f->COM('sel_move_other', target_layer => $TmpLayers[0], invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0, rotation => 0, mirror => 'none');
#	$f->PAUSE("33");
	$f->INFO(entity_type => 'layer',entity_path => "$JOB/$STEP/$TmpLayers[1]",data_type => 'LIMITS');
	my $WorkLimitsCenterX = ($f->{doinfo}{gLIMITSxmax} + $f->{doinfo}{gLIMITSxmin} ) / 2 ;
	my $WorkLimitsCenterY = ($f->{doinfo}{gLIMITSymax} + $f->{doinfo}{gLIMITSymin} ) / 2 ;
	my $MirrorMode = 'None';
	if ( ( $f->{doinfo}{gLIMITSymax} - $f->{doinfo}{gLIMITSymin} ) > ($f->{doinfo}{gLIMITSxmax} - $f->{doinfo}{gLIMITSxmin} ) ) {
		$MirrorMode = 'Y';
	} else {
		$MirrorMode = 'X';
	}


	$f->COM('get_disp_layers');
	@DispLayers = split (" ",$f->{COMANS});

	$f->COM('clear_layers');
	$f->COM('affected_layer', name => $WorkLayer, mode => 'single', affected => 'no');

	$f->COM('units', type => 'inch');
	$f->COM('affected_layer', name => $TmpLayers[1], mode => 'single', affected => 'yes');
	$f->COM('sel_contourize', accuracy => '0', break_to_islands => 'yes', clean_hole_size => '0', clean_hole_mode => 'x_and_y');
	my @TmpFeatIndexData4;
	my $tInfoFile = $ENV{GENESIS_TMP} . '/info.' . int(rand(9999));
	$f->COM ( 'info',out_file => $tInfoFile,args => " -t layer -e $JOB/$STEP/$TmpLayers[1] -d FEATURES -o feat_index" ) ;
	open ( FH,"<$tInfoFile" ) ;
	while ( <FH> ) {
		my $line = $_;
		if ( $line =~ /^\#\d+\s+/ ) {
			my ( $tTmpFeatIndexData ) = ($line =~ /^\#(\d+)\s+/i);
			push  @TmpFeatIndexData4,$tTmpFeatIndexData;
		}
	}
	close FH;
	unlink $tInfoFile;
	my ($TextSumX,$TextSumY,) = (0,0);
	for my $tNum4 ( @TmpFeatIndexData4 ) {
		$f->COM('sel_layer_feat', operation => 'select', layer => $TmpLayers[1], index => $tNum4);
		$f->INFO(entity_type => 'layer',entity_path => "$JOB/$STEP/$TmpLayers[1]",data_type => 'LIMITS',options => "select");
		my $tTextX = ( $f->{doinfo}{gLIMITSxmax} - $f->{doinfo}{gLIMITSxmin} ) * 1000;
		$TextSumX += $tTextX;
		my $tTextY = ( $f->{doinfo}{gLIMITSymax} - $f->{doinfo}{gLIMITSymin} ) * 1000;
		$TextSumY += $tTextY;
		$f->COM('sel_clear_feat');
	}
#	$f->PAUSE("TextSumX=$TextSumX,TextSumY=$TextSumY,");

	$f->COM('sel_delete');
	my $TextAverageX = $TextSumX / scalar(@TmpFeatIndexData4);
	my $TextAverageY = $TextSumY / scalar(@TmpFeatIndexData4);
	$f->COM('affected_layer', name => $TmpLayers[1], mode => 'single', affected => 'no');
	#
	my $tMaxLineSize = 3.9 ;
	if ( $tTextCategoryOption eq 'Line' ) {
		#获取框选区域的物件FEATURES #获取最大线
		my $MaxLineSize = 12 ;
		my $tInfoFile = $ENV{GENESIS_TMP} . '/info.' . int(rand(9999));
		$f->COM ( 'info',out_file => $tInfoFile,args => " -t layer -e $JOB/$STEP/$TmpLayers[0] -d FEATURES" ) ;
		open ( FH,"<$tInfoFile" ) ;
		while ( <FH> ) {
			my $line = $_;
			my ( $Size,$Positive ) = (0,'N');
			if ( $line =~ /\#L/ ) {
				#L 1.80117 8.85592 1.79867 8.85717 r4.5 P 19
				( $Size,$Positive ) = ( split ( ' ',$line ) ) [5,6,];
			}elsif ( $line =~ /\#A/ ) {
				#A 1.96316 9.02362 1.96316 9.02362 1.89566 9.02362 r12 P 12 Y
				( $Size,$Positive ) = ( split ( ' ',$line ) ) [7,8,];
			}
			if ( $Positive eq 'P' ) {
				$Size =~ s/r//;
				if ( $Size > $tMaxLineSize ) {
					$tMaxLineSize = $Size ;
				}
			}
		}
		close FH;
		unlink $tInfoFile;
		if ( $tMaxLineSize > $MaxLineSize ) {
			$tMaxLineSize = $MaxLineSize;
		}
	}
	#
	if ( $tTextCategoryOption eq 'Surface' ) {
		if( ( $tMode eq 'Single' ) or ( $tMode eq 'Multiple' ) ) {
			$tScaleX = $tWidth / $TextAverageX;
			$tScaleY = $tHeight / $TextAverageY;
		} else {
			if ( $MirrorMode eq 'X' ) {
				$tScaleX = $tWidth / $TextAverageX;
				$tScaleY = $tHeight / $TextAverageY;
			} else {
				$tScaleX = $tWidth / $TextAverageY;
				$tScaleY = $tHeight / $TextAverageX;
			}
		}
	} else {
		if( ( $tMode eq 'Single' ) or ( $tMode eq 'Multiple' ) ) {
#		$f->PAUSE("$tWidth,$TextAverageX");
			$tScaleX = $tWidth / $TextAverageX;
			$tScaleY = $tHeight / $TextAverageY;

		} else {
			if ( $MirrorMode eq 'X' ) {
				$tScaleX = ( $tWidth - $tMaxLineSize ) / ( $TextAverageX - $tMaxLineSize );
				$tScaleY = ( $tHeight - $tMaxLineSize ) / ( $TextAverageY - $tMaxLineSize );
			} else {
				$tScaleX = ( $tWidth - $tMaxLineSize ) / ( $TextAverageY - $tMaxLineSize );
				$tScaleY = ( $tHeight - $tMaxLineSize ) / ( $TextAverageX - $tMaxLineSize );
			}
		}
	}
	#
	if ( $tScaleX < 1 ){
		$tScaleX = 1 ;
	}
	if ( $tScaleX > $tScaleY ){
		$tScaleY = $tScaleX;
	} else {
		$tScaleX = $tScaleY;
	}
	#
	$f->COM('affected_layer', name => $TmpLayers[0], mode => 'single', affected => 'yes');
	if ( $tMirror eq 1 ) {
		if ( $MirrorMode eq 'X' ){
			$f->COM('sel_transform', oper => 'mirror;scale', x_anchor => $WorkLimitsCenterX, y_anchor => $WorkLimitsCenterY, angle => 0, x_scale => $tScaleX, y_scale => $tScaleY, x_offset => 0, y_offset => 0, mode => 'anchor', duplicate => 'no');
		} elsif ( $MirrorMode eq 'Y' ){
			$f->COM('sel_transform', oper => 'rotate;mirror;scale', x_anchor => $WorkLimitsCenterX, y_anchor => $WorkLimitsCenterY, angle => 180, x_scale => $tScaleX, y_scale => $tScaleY, x_offset => 0, y_offset => 0, mode => 'anchor', duplicate => 'no');
		}
	} else {
		$f->COM('sel_transform', oper => 'scale', x_anchor => $WorkLimitsCenterX, y_anchor => $WorkLimitsCenterY, angle => 0, x_scale => $tScaleX, y_scale => $tScaleY, x_offset => 0, y_offset => 0, mode => 'anchor' , duplicate => 'no',);
	}
	$f->COM('sel_move_other', target_layer => $WorkLayer, invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0, rotation => 0, mirror => 'none');
	$f->COM('affected_layer', name => $TmpLayers[0], mode => 'single', affected => 'no');

	$f->COM('sel_options', clear_mode => 'clear_after', display_mode => 'all_layers', area_inout => 'inside', area_select => 'select', select_mode => 'standard', area_touching_mode => 'exclude');

	&DelLayers(@TmpLayers);

#	$f->COM('display_layer', name => $WorkLayer, display => 'yes', number => 1);
	$f->COM('display_layer', name => $WorkLayer, display => 'yes');
	$f->COM('work_layer', name => $WorkLayer);

#	{
#		for my $tDispLayers ( @DispLayers ){
#			if( $tDispLayers ne $WorkOkLayer ){
#				$f->COM('display_layer', name => $tDispLayers, display => 'yes');
#			}
#		}
#	}

	if( ( $tMode eq 'Multiple' ) or ( $tMode eq 'AutoMultiple' ) ) {
		goto TextWidthHeightZoomMultipleRun;
	}
}

sub AutoTextWidthHeightAutoZoom {#自动按指定宽和高拉伸字符
	my $RunSubScr = shift;
	my ($tSerialTextSpace,$tTextCategoryOption,$tWidth,$tHeight,$tMirror) = @_;
	$f->COM('get_work_layer');
	$WorkLayer = $f->{COMANS};

	#工作层
	$f->COM('get_work_layer');
	my $WorkLayer = $f->{COMANS};
	if ( $WorkLayer eq '' ) {
		&MsgBox("没有工作层","warning","ok","没有工作层,脚本退出",);
		exit;
	}

	&GetJobStep;
	$f->COM('sel_options', clear_mode => 'clear_none', display_mode => 'displayed_layers', area_inout => 'inside', area_select => 'select', select_mode => 'standard', area_touching_mode => 'exclude');

	my @TmpLayers = ($WorkLayer . "-tmp1+", $WorkLayer . "-tmp2+", $WorkLayer . "-tmp3+", $WorkLayer . "-tmp4+", $WorkLayer . "-tmp5+",);
	&DelLayers(@TmpLayers);

	$f->COM('units', type => 'inch');
	$f->COM('clear_layers');
	$f->COM('affected_layer', name => '', mode => 'all', affected => 'no');
	$f->COM('copy_layer', source_job => $JOB, source_step => $STEP, source_layer => $WorkLayer, dest => 'layer_name', dest_layer => $WorkLayer . '-bak+' , mode => 'replace', invert => 'no');
	$f->COM('copy_layer', source_job => $JOB, source_step => $STEP, source_layer => $WorkLayer, dest => 'layer_name', dest_layer => $TmpLayers[0], mode => 'replace', invert => 'no');

	$f->COM('affected_layer', name => $TmpLayers[0], mode => 'single', affected => 'yes');
	if ( $tWidth != 0 ) {
		$f->COM('sel_contourize', accuracy => '0', break_to_islands => 'yes', clean_hole_size => '0', clean_hole_mode => 'x_and_y');
		$f->COM('copy_layer', source_job => $JOB, source_step => $STEP, source_layer => $TmpLayers[0], dest => 'layer_name', dest_layer => $TmpLayers[3], mode => 'replace', invert => 'no');
	}
	$f->COM('sel_resize', size => $tSerialTextSpace, corner_ctl => 'no');
	$f->COM('sel_contourize', accuracy => '0', break_to_islands => 'yes', clean_hole_size => '0', clean_hole_mode => 'x_and_y');

	$f->COM('filter_reset', filter_name => 'popup');

	my @TmpFeatIndexData;
	my $tInfoFile = $ENV{GENESIS_TMP} . '/info.' . int(rand(9999));
	$f->COM ( 'info',out_file => $tInfoFile,args => " -t layer -e $JOB/$STEP/$TmpLayers[0] -d FEATURES -o feat_index" ) ;
	open ( FH,"<$tInfoFile" ) ;
	while ( <FH> ) {
		my $line = $_;
		if ( $line =~ /^\#\d+\s+/ ) {
			#1    #S P 0
			my ( $tTmpFeatIndexData ) = ($line =~ /^\#(\d+)\s+/i);
			push  @TmpFeatIndexData,$tTmpFeatIndexData;
		}
	}
	close FH;
	unlink $tInfoFile;

	for my $tNum ( @TmpFeatIndexData ) {
		$f->COM('sel_layer_feat', operation => 'select', layer => $TmpLayers[0], index => $tNum);
		$f->COM('sel_copy_other', dest => 'layer_name', target_layer => $TmpLayers[1], invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0, rotation => 0, mirror => 'none');
		$f->COM('affected_layer', name => $TmpLayers[0], mode => 'single', affected => 'no');

		$f->INFO(entity_type => 'layer',entity_path => "$JOB/$STEP/$TmpLayers[1]",data_type => 'LIMITS');
		my $WorkLimitsCenterX = ($f->{doinfo}{gLIMITSxmax} + $f->{doinfo}{gLIMITSxmin} ) / 2 ;
		my $WorkLimitsCenterY = ($f->{doinfo}{gLIMITSymax} + $f->{doinfo}{gLIMITSymin} ) / 2 ;
		my $MirrorMode = 'None';
		if ( ( $f->{doinfo}{gLIMITSymax} - $f->{doinfo}{gLIMITSymin} ) > ($f->{doinfo}{gLIMITSxmax} - $f->{doinfo}{gLIMITSxmin} ) ) {
			$MirrorMode = 'Y';
		} else {
			$MirrorMode = 'X';
		}

		########
		my ($tScaleX,$tScaleY);
		my ($TextAverageX,$TextAverageY);
		if ( $tWidth != 0 ) {
			$f->COM('affected_layer', name => $TmpLayers[3], mode => 'single', affected => 'yes');
			$f->COM('sel_ref_feat', layers => $TmpLayers[1], use => 'filter', mode => 'cover', pads_as => 'shape', f_types => 'line;pad;surface;arc;text', polarity => 'positive;negative', include_syms => '', exclude_syms => '');
			$f->COM('get_select_count');
			my $TextPieceTextNum = $f->{COMANS};
			$f->COM('sel_move_other', target_layer => $TmpLayers[4], invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0, rotation => 0, mirror => 'none');
			$f->COM('affected_layer', name => $TmpLayers[3], mode => 'single', affected => 'no');

			my @TmpFeatIndexData4;
			my $tInfoFile = $ENV{GENESIS_TMP} . '/info.' . int(rand(9999));
			$f->COM ( 'info',out_file => $tInfoFile,args => " -t layer -e $JOB/$STEP/$TmpLayers[4] -d FEATURES -o feat_index" ) ;
			open ( FH,"<$tInfoFile" ) ;
			while ( <FH> ) {
				my $line = $_;
				if ( $line =~ /^\#\d+\s+/ ) {
					my ( $tTmpFeatIndexData ) = ($line =~ /^\#(\d+)\s+/i);
					push  @TmpFeatIndexData4,$tTmpFeatIndexData;
				}
			}
			close FH;
			unlink $tInfoFile;
			my ($TextSumX,$TextSumY,) = (0,0);
			$f->COM('affected_layer', name => $TmpLayers[4], mode => 'single', affected => 'yes');
			for my $tNum4 ( @TmpFeatIndexData4 ) {
				$f->COM('sel_layer_feat', operation => 'select', layer => $TmpLayers[4], index => $tNum4);
				$f->INFO(entity_type => 'layer',entity_path => "$JOB/$STEP/$TmpLayers[4]",data_type => 'LIMITS',options => "select");
				my $tTextX = ( $f->{doinfo}{gLIMITSxmax} - $f->{doinfo}{gLIMITSxmin} ) * 1000;
				$TextSumX += $tTextX;
				my $tTextY = ( $f->{doinfo}{gLIMITSymax} - $f->{doinfo}{gLIMITSymin} ) * 1000;
				$TextSumY += $tTextY;
				$f->COM('sel_clear_feat');
			}
			$f->COM('sel_delete');
			$f->COM('affected_layer', name => $TmpLayers[4], mode => 'single', affected => 'no');
			$TextAverageX = $TextSumX / $TextPieceTextNum;
			$TextAverageY = $TextSumY / $TextPieceTextNum;
		}

		$f->COM('affected_layer', name => $WorkLayer, mode => 'single', affected => 'yes');
		$f->COM('sel_ref_feat', layers => $TmpLayers[1], use => 'filter', mode => 'cover', pads_as => 'shape', f_types => 'line;pad;surface;arc;text', polarity => 'positive;negative', include_syms => '', exclude_syms => '');
#		my $MaxLineSizeInch;
		my $tMaxLineSize = 3.9 ;
		if ( $tTextCategoryOption eq 'Line' ) {
			#获取框选区域的物件FEATURES #获取最大线
			my $MaxLineSize = 12 ;
			#my $tMaxLineSize = 3.9 ;
			my $tInfoFile = $ENV{GENESIS_TMP} . '/info.' . int(rand(9999));
			$f->COM ( 'info',out_file => $tInfoFile,args => " -t layer -e $JOB/$STEP/$WorkLayer -d FEATURES -o select" ) ;
			open ( FH,"<$tInfoFile" ) ;
			while ( <FH> ) {
				my $line = $_;
				my ( $Size,$Positive ) = (0,'N');
				if ( $line =~ /\#L/ ) {
					#L 1.80117 8.85592 1.79867 8.85717 r4.5 P 19
					( $Size,$Positive ) = ( split ( ' ',$line ) ) [5,6,];
				}elsif ( $line =~ /\#A/ ) {
					#A 1.96316 9.02362 1.96316 9.02362 1.89566 9.02362 r12 P 12 Y
					( $Size,$Positive ) = ( split ( ' ',$line ) ) [7,8,];
				}
				if ( $Positive eq 'P' ) {
					$Size =~ s/r//;
		#			if ( $Size > $MaxLineSize ) {
					if ( $Size > $tMaxLineSize ) {
						$tMaxLineSize = $Size ;
					}
				}
			}
			close FH;
			unlink $tInfoFile;
			if ( $tMaxLineSize > $MaxLineSize ) {
				$tMaxLineSize = $MaxLineSize;
			}
#			$MaxLineSizeInch = $tMaxLineSize / 1000;

		}

		if ( $tWidth != 0 ) {
			if ( $tTextCategoryOption eq 'Surface' ) {
				if ( $MirrorMode eq 'X' ) {
					$tScaleX = $tWidth / $TextAverageX;
					$tScaleY = $tHeight / $TextAverageY;
				} else {
					$tScaleX = $tWidth / $TextAverageY;
					$tScaleY = $tHeight / $TextAverageX;
				}
			} else {
				if ( $MirrorMode eq 'X' ) {
					$tScaleX = ( $tWidth - $tMaxLineSize ) / ( $TextAverageX - $tMaxLineSize );
					$tScaleY = ( $tHeight - $tMaxLineSize ) / ( $TextAverageY - $tMaxLineSize );
				} else {
					$tScaleX = ( $tWidth - $tMaxLineSize ) / ( $TextAverageY - $tMaxLineSize );
					$tScaleY = ( $tHeight - $tMaxLineSize ) / ( $TextAverageX - $tMaxLineSize );
				}
			}
			#
			if ( $tScaleX < 1 ){
				$tScaleX = 1 ;
			}
			if ( $tScaleX > $tScaleY ){
				$tScaleY = $tScaleX;
			} else {
				$tScaleX = $tScaleY;
			}
		} else {
			$f->INFO(entity_type => 'layer',entity_path => "$JOB/$STEP/$WorkLayer",data_type => 'LIMITS',options => "select");
			my $tTextHeight;
			if ( $MirrorMode eq 'X' ) {
				$tTextHeight = ( $f->{doinfo}{gLIMITSymax} - $f->{doinfo}{gLIMITSymin} ) * 1000;
			} else {
				$tTextHeight = ( $f->{doinfo}{gLIMITSxmax} - $f->{doinfo}{gLIMITSxmin} ) * 1000;
			}
			if ( $tHeight < $tTextHeight ){
				$tScaleY = 1;
			} else {
				if ( $tTextCategoryOption eq 'Surface' ) {
					$tScaleY = $tHeight / $tTextHeight;
				} else {
					$tScaleY = ( $tHeight - $tMaxLineSize ) / ( $tTextHeight - $tMaxLineSize );
				}
			}
			$tScaleX = $tScaleY ;
		}
		#
		if ( $tMirror eq 1 ) {
			if ( $MirrorMode eq 'X' ){
				$f->COM('sel_transform', oper => 'mirror;scale', x_anchor => $WorkLimitsCenterX, y_anchor => $WorkLimitsCenterY, angle => 0, x_scale => $tScaleX, y_scale => $tScaleY, x_offset => 0, y_offset => 0, mode => 'anchor', duplicate => 'no');
			} elsif ( $MirrorMode eq 'Y' ){
				$f->COM('sel_transform', oper => 'rotate;mirror;scale', x_anchor => $WorkLimitsCenterX, y_anchor => $WorkLimitsCenterY, angle => 180, x_scale => $tScaleX, y_scale => $tScaleY, x_offset => 0, y_offset => 0, mode => 'anchor', duplicate => 'no');
			}
		} else {
			$f->COM('sel_transform', oper => 'scale', x_anchor => $WorkLimitsCenterX, y_anchor => $WorkLimitsCenterY, angle => 0, x_scale => $tScaleX, y_scale => $tScaleY, x_offset => 0, y_offset => 0, mode => 'anchor' , duplicate => 'no',);
		}

		$f->COM('sel_move_other', target_layer => $TmpLayers[2], invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0, rotation => 0, mirror => 'none');
		$f->COM('affected_layer', name => $WorkLayer, mode => 'single', affected => 'no');

		$f->COM('truncate_layer', layer => $TmpLayers[1]);
		$f->COM('affected_layer', name => $TmpLayers[0], mode => 'single', affected => 'yes');
	}
	$f->COM('sel_options', clear_mode => 'clear_after', display_mode => 'all_layers', area_inout => 'inside', area_select => 'select', select_mode => 'standard', area_touching_mode => 'exclude');

	$f->COM('copy_layer', source_job => $JOB, source_step => $STEP, source_layer => $TmpLayers[2], dest => 'layer_name', dest_layer => $WorkLayer, mode => 'replace', invert => 'no');
	&DelLayers(@TmpLayers);
	$f->COM('display_layer', name => $WorkLayer, display => 'yes', number => 1);
	$f->COM('work_layer', name => $WorkLayer);
}

sub TextScaleAutoZoom {#自动按比例拉伸字符
	my $RunSubScr = shift;
	my ($tSerialTextSpace,$tScaleX,$tScaleY,$tMirror) = @_;

	$f->COM('get_work_layer');
	$WorkLayer = $f->{COMANS};

	#工作层
	$f->COM('get_work_layer');
	my $WorkLayer = $f->{COMANS};
	if ( $WorkLayer eq '' ) {
		&MsgBox("没有工作层","warning","ok","没有工作层,脚本退出",);
		exit;
	}

	&GetJobStep;
	$f->COM('sel_options', clear_mode => 'clear_none', display_mode => 'displayed_layers', area_inout => 'inside', area_select => 'select', select_mode => 'standard', area_touching_mode => 'exclude');

#	my @TmpLayers = ($WorkLayer . "-tmp1+", $WorkLayer . "-tmp2+", $WorkLayer . "-tmp3+", $WorkLayer . "-tmp4+", );
	my @TmpLayers = ($WorkLayer . "-tmp1+", $WorkLayer . "-tmp2+", $WorkLayer . "-tmp3+",);
	&DelLayers(@TmpLayers);

	$f->COM('units', type => 'inch');
	$f->COM('clear_layers');
	$f->COM('affected_layer', name => '', mode => 'all', affected => 'no');
	$f->COM('copy_layer', source_job => $JOB, source_step => $STEP, source_layer => $WorkLayer, dest => 'layer_name', dest_layer => $WorkLayer . '-bak+' , mode => 'replace', invert => 'no');
	$f->COM('copy_layer', source_job => $JOB, source_step => $STEP, source_layer => $WorkLayer, dest => 'layer_name', dest_layer => $TmpLayers[0], mode => 'replace', invert => 'no');

	$f->COM('affected_layer', name => $TmpLayers[0], mode => 'single', affected => 'yes');
#	$f->COM('sel_contourize', accuracy => '0', break_to_islands => 'yes', clean_hole_size => '0', clean_hole_mode => 'x_and_y');
	$f->COM('sel_resize', size => $tSerialTextSpace, corner_ctl => 'no');
	$f->COM('sel_contourize', accuracy => '0', break_to_islands => 'yes', clean_hole_size => '0', clean_hole_mode => 'x_and_y');

	$f->COM('filter_reset', filter_name => 'popup');
#	$f->INFO(entity_type => 'layer',entity_path => "$JOB/$STEP/$TmpLayers[0]",data_type => 'FEAT_HIST');
#	my $LayerFeatSumNum = $f->{doinfo}{gFEAT_HISTtotal};

	my @TmpFeatIndexData;
	my $tInfoFile = $ENV{GENESIS_TMP} . '/info.' . int(rand(9999));
	$f->COM ( 'info',out_file => $tInfoFile,args => " -t layer -e $JOB/$STEP/$TmpLayers[0] -d FEATURES -o feat_index" ) ;
	open ( FH,"<$tInfoFile" ) ;
	while ( <FH> ) {
		my $line = $_;
		if ( $line =~ /^\#\d+\s+/ ) {
			#1    #S P 0
			my ( $tTmpFeatIndexData ) = ($line =~ /^\#(\d+)\s+/i);
			push  @TmpFeatIndexData,$tTmpFeatIndexData;
		}
	}
	close FH;
	unlink $tInfoFile;
#		$f->PAUSE("$#TmpFeatIndexData");

#	for my $tNum ( 1 .. $LayerFeatSumNum ) {
	for my $tNum ( @TmpFeatIndexData ) {
#		$f->PAUSE("('sel_layer_feat', operation => 'select', layer => $TmpLayers[0], index => $tNum)");

		$f->COM('sel_layer_feat', operation => 'select', layer => $TmpLayers[0], index => $tNum);

		$f->COM('sel_copy_other', dest => 'layer_name', target_layer => $TmpLayers[1], invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0, rotation => 0, mirror => 'none');
		$f->INFO(entity_type => 'layer',entity_path => "$JOB/$STEP/$TmpLayers[1]",data_type => 'LIMITS');
		my $WorkLimitsCenterX = ($f->{doinfo}{gLIMITSxmax} + $f->{doinfo}{gLIMITSxmin} ) / 2 ;
		my $WorkLimitsCenterY = ($f->{doinfo}{gLIMITSymax} + $f->{doinfo}{gLIMITSymin} ) / 2 ;
		my $MirrorMode = 'None';
		if ( $tMirror eq 1 ) {
			if ( ( $f->{doinfo}{gLIMITSymax} - $f->{doinfo}{gLIMITSymin} ) > ($f->{doinfo}{gLIMITSxmax} - $f->{doinfo}{gLIMITSxmin} ) ) {
				$MirrorMode = 'Y';
			} else {
				$MirrorMode = 'X';
			}
		}
#			my $WorkLimitsMinX =  $f->{doinfo}{gLIMITSxmin};
#	my $WorkLimitsMinY =  $f->{doinfo}{gLIMITSymin};
#	my $WorkLimitsMaxX =  $f->{doinfo}{gLIMITSxmax};
#	my $WorkLimitsMaxY =  $f->{doinfo}{gLIMITSymax};

		$f->COM('affected_layer', name => $TmpLayers[0], mode => 'single', affected => 'no');



		$f->COM('affected_layer', name => $WorkLayer, mode => 'single', affected => 'yes');
		$f->COM('sel_ref_feat', layers => $TmpLayers[1], use => 'filter', mode => 'cover', pads_as => 'shape', f_types => 'line;pad;surface;arc;text', polarity => 'positive;negative', include_syms => '', exclude_syms => '');
		#解决了清除选项问题 此步将不需要

#		$f->COM('sel_move_other', target_layer => $TmpLayers[2], invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0, rotation => 0, mirror => 'none');
#		$f->COM('affected_layer', name => $WorkLayer, mode => 'single', affected => 'no');
#		$f->COM('affected_layer', name => $TmpLayers[2], mode => 'single', affected => 'yes');

#		$f->COM('get_select_count');
#		if ( $f->{COMANS} == 0 ) {
#			$f->PAUSE("1,= $tNum");
#		}

		if ( $MirrorMode eq 'None'){
			$f->COM('sel_transform', oper => 'scale', x_anchor => $WorkLimitsCenterX, y_anchor => $WorkLimitsCenterY, angle => 0, x_scale => $tScaleX, y_scale => $tScaleY, x_offset => 0, y_offset => 0, mode => 'anchor' , duplicate => 'no',);
		} elsif ( $MirrorMode eq 'X'){
			$f->COM('sel_transform', oper => 'mirror;scale', x_anchor => $WorkLimitsCenterX, y_anchor => $WorkLimitsCenterY, angle => 0, x_scale => $tScaleX, y_scale => $tScaleY, x_offset => 0, y_offset => 0, mode => 'anchor', duplicate => 'no');
		} elsif ( $MirrorMode eq 'Y'){
			$f->COM('sel_transform', oper => 'rotate;mirror;scale', x_anchor => $WorkLimitsCenterX, y_anchor => $WorkLimitsCenterY, angle => 180, x_scale => $tScaleX, y_scale => $tScaleY, x_offset => 0, y_offset => 0, mode => 'anchor', duplicate => 'no');
		}

#		$f->COM('get_select_count');
#		if ( $f->{COMANS} == 0 ) {
#			$f->PAUSE("2,$tNum");
#		}

		$f->COM('sel_move_other', target_layer => $TmpLayers[2], invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0, rotation => 0, mirror => 'none');
		$f->COM('affected_layer', name => $WorkLayer, mode => 'single', affected => 'no');
#		$f->COM('affected_layer', name => $TmpLayers[2], mode => 'single', affected => 'no');

		$f->COM('truncate_layer', layer => $TmpLayers[1]);
		$f->COM('affected_layer', name => $TmpLayers[0], mode => 'single', affected => 'yes');
	}
	$f->COM('sel_options', clear_mode => 'clear_after', display_mode => 'all_layers', area_inout => 'inside', area_select => 'select', select_mode => 'standard', area_touching_mode => 'exclude');

	$f->COM('copy_layer', source_job => $JOB, source_step => $STEP, source_layer => $TmpLayers[2] , dest => 'layer_name', dest_layer => $WorkLayer, mode => 'replace', invert => 'no');
	&DelLayers(@TmpLayers);
	$f->COM('display_layer', name => $WorkLayer, display => 'yes', number => 1);
	$f->COM('work_layer', name => $WorkLayer);
}

sub TextScaleZoom {#手动按比例拉伸字符
	my $RunSubScr = shift;
	my ($tMode,$tScaleX,$tScaleY,$tMirror) = @_;

	#工作层
	$f->COM('get_work_layer');
	my $WorkLayer = $f->{COMANS};
	if ( $WorkLayer eq '' ) {
		&MsgBox("没有工作层","warning","ok","没有工作层,脚本退出",);
		exit;
	}

	&GetJobStep;
	if( $tMode eq 'Multiple' ) {
		$f->COM('copy_layer', source_job => $JOB, source_step => $STEP, source_layer => $WorkLayer, dest => 'layer_name', dest_layer => $WorkLayer . '-bak+', mode => 'replace', invert => 'no');
	}

	TextScaleZoomMultipleRun:;
	$f->COM('units', type => 'inch');
#	my ($X1,$Y1,$X2,$Y2,);
	$f->COM('get_select_count');
	if ( $f->{COMANS} == 0 ) {
		if( $tMode eq 'Single' ) {
			exit;
		} elsif( $tMode eq 'Multiple' ) {
			$f->MOUSE("r Please select the text you want to enlarge.");
			($X1,$Y1,$X2,$Y2,) = split(/ /,$f->{MOUSEANS});
			$f->COM('filter_area_strt');
			$f->COM('filter_area_xy', x => $X1, y => $Y1);
			$f->COM('filter_area_xy', x => $X2, y => $Y2);
			$f->COM('filter_area_end', layer => '', filter_name => 'popup', operation => 'select', area_type => 'rectangle', inside_area => 'yes', intersect_area => 'no');
			$f->COM('get_select_count');
			my $tSelNum = $f->{COMANS};
			while ( $tSelNum == 0 ) {
				my $SelJud = &MsgBox("未选择物件","warning","yesno","没有选择任何物件,是否退出脚本?",);
				if( lc($SelJud) eq 'yes' ){
					exit(0);
					last;
				}
				#
				$f->MOUSE("r Please select the text you want to enlarge.");
				my ($X1,$Y1,$X2,$Y2,) = split(/ /,$f->{MOUSEANS});
				$f->COM('filter_area_strt');
				$f->COM('filter_area_xy', x => $X1, y => $Y1);
				$f->COM('filter_area_xy', x => $X2, y => $Y2);
				$f->COM('filter_area_end', layer => '', filter_name => 'popup', operation => 'select', area_type => 'rectangle', inside_area => 'yes', intersect_area => 'no');
				$f->COM('get_select_count');
				$tSelNum = $f->{COMANS};
			}
		}
	}

	$f->INFO( entity_type => 'layer',entity_path => "$JOB/$STEP/$WorkLayer",data_type => 'LIMITS',options => "select");
	my $WorkLimitsCenterX = ($f->{doinfo}{gLIMITSxmax} + $f->{doinfo}{gLIMITSxmin} ) / 2 ;
	my $WorkLimitsCenterY = ($f->{doinfo}{gLIMITSymax} + $f->{doinfo}{gLIMITSymin} ) / 2 ;
	my $MirrorMode = 'None';
	if ( $tMirror eq 1 ) {
		if ( ( $f->{doinfo}{gLIMITSymax} - $f->{doinfo}{gLIMITSymin} ) > ($f->{doinfo}{gLIMITSxmax} - $f->{doinfo}{gLIMITSxmin} ) ) {
			$MirrorMode = 'Y';
		} else {
			$MirrorMode = 'X';
		}
	}

	if ( $MirrorMode eq 'None'){
		$f->COM('sel_transform', oper => 'scale', x_anchor => $WorkLimitsCenterX, y_anchor => $WorkLimitsCenterY, angle => 0, x_scale => $tScaleX, y_scale => $tScaleY, x_offset => 0, y_offset => 0, mode => 'anchor' , duplicate => 'no',);
	} elsif ( $MirrorMode eq 'X'){
		$f->COM('sel_transform', oper => 'mirror;scale', x_anchor => $WorkLimitsCenterX, y_anchor => $WorkLimitsCenterY, angle => 0, x_scale => $tScaleX, y_scale => $tScaleY, x_offset => 0, y_offset => 0, mode => 'anchor', duplicate => 'no');
	} elsif ( $MirrorMode eq 'Y'){
		$f->COM('sel_transform', oper => 'rotate;mirror;scale', x_anchor => $WorkLimitsCenterX, y_anchor => $WorkLimitsCenterY, angle => 180, x_scale => $tScaleX, y_scale => $tScaleY, x_offset => 0, y_offset => 0, mode => 'anchor', duplicate => 'no');
	}

	if( $tMode eq 'Multiple' ) {
		goto TextScaleZoomMultipleRun;
	}
}

sub AddMark {  #添加标记
	&GetJobStep;
	my $ScriptFile = '/incam/server/site_data/scripts/sh1_script/make/add_mark.pl';
	$f->COM('script_run', name => $ScriptFile, env1 => "JOB=$JOB", env2 => "STEP=$STEP",
#	 params => '$tParams',
	 );
}

sub TextCoverTextBox {  #文字套字框
	my $RunSubScr = shift;
	my $TextSeparatedLayerSuffix = shift;
	my @SilkSelLayerLists = split ('@',"@_");
	my $TextToTextBoxSpace = 6;
	&GetJobStep;
	for my $tLayer (@SilkSelLayerLists){
#		my $TextSeparatedLayer = $tLayer . '-text+';
		my $TextSeparatedLayer = $tLayer . $TextSeparatedLayerSuffix;
		my $TmpLayer = $tLayer . '-tmp1+';
		$f->INFO(entity_type => 'layer',entity_path => "$JOB/$STEP/$TextSeparatedLayer",data_type => 'EXISTS');
		if ( $f->{doinfo}{gEXISTS} eq 'no' ) {
			&MsgBox("$TextSeparatedLayer 不存在","warning","ok","文字分离层 $TextSeparatedLayer 不存在,脚本退出！",);
			exit;
		} else {
			&DelLayers($TmpLayer);
			$f->COM('clear_layers');
			$f->COM('affected_layer', mode => 'all', affected => 'no');
			$f->COM('units', type => 'inch');
			$f->COM('affected_layer', name => $TextSeparatedLayer, mode => 'single', affected => 'yes');
			$f->COM('sel_copy_other', dest => 'layer_name', target_layer => $TmpLayer, invert => 'no', dx => 0, dy => 0, size => $TextToTextBoxSpace);
			$f->COM('affected_layer', name => $TextSeparatedLayer, mode => 'single', affected => 'no');

			$f->COM('affected_layer', name => $TmpLayer, mode => 'single', affected => 'yes');
			$f->COM('filter_reset', filter_name => 'popup');
			$f->COM('filter_set', filter_name => 'popup', update_popup => 'no', feat_types => 'line;arc');
			$f->COM('filter_set', filter_name => 'popup', update_popup => 'no', polarity => 'positive');
			$f->COM('sel_ref_feat', layers => $tLayer , use => 'filter', mode => 'disjoint', pads_as => 'shape', f_types => 'line;pad;surface;arc;text', polarity => 'positive;negative', include_syms => '', exclude_syms => '');
			$f->COM('get_select_count');
			if ($f->{COMANS} > 0 ) {
				$f->COM('sel_delete');
			}
			$f->COM('affected_layer', name => $TmpLayer, mode => 'single', affected => 'no');

			$f->COM('affected_layer', name => $TextSeparatedLayer, mode => 'single', affected => 'yes');
 			$f->COM('filter_reset', filter_name => 'popup');
			$f->COM('filter_set', filter_name => 'popup', update_popup => 'no', feat_types => 'line;arc');
			$f->COM('filter_set', filter_name => 'popup', update_popup => 'no', polarity => 'positive');
			$f->COM('sel_ref_feat', layers => $TmpLayer , use => 'filter', mode => 'touch', pads_as => 'shape', f_types => 'line;pad;surface;arc;text', polarity => 'positive;negative', include_syms => '', exclude_syms => '');
			&DelLayers($TmpLayer);
 			$f->COM('filter_reset', filter_name => 'popup');
			$f->COM('display_layer', name => $TextSeparatedLayer, display => 'yes', number => 1);
			$f->COM('work_layer', name => $TextSeparatedLayer);
			$f->COM('display_layer', name => $tLayer, display => 'yes', number => 2);
			$f->PAUSE("请请检查选择的是否正确");
			$f->COM('get_select_count');
			while ( $f->{COMANS} == 0 ) {
				$f->PAUSE("没有选择,请重新选择!");
				$f->COM('get_select_count');
			}
			$f->COM('units', type => 'inch');
			$f->COM('sel_copy_other', dest => 'layer_name', target_layer => $tLayer, invert => 'yes', dx => 0, dy => 0, size => $TextToTextBoxSpace);
			$f->COM('sel_clear_feat');
			$f->COM('sel_copy_other', dest => 'layer_name', target_layer => $tLayer, invert => 'no', dx => 0, dy => 0, size => 0);

			$f->COM('clear_layers');
			$f->COM('affected_layer', mode => 'all', affected => 'no');
		}
	}
	&MsgBox("脚本已运行Ok","info","ok","文字套字框 脚本已运行Ok,请检查!",);
	exit;
}

sub SolderMaskCoverTextBox {  #阻焊套文字
	my $RunSubScr = shift;
	my $CoverLayerSuffix = shift;
	my @SilkSelLayerLists = split ('@',"@_");
	&GetJobStep;
	$f->COM('clear_layers');
	$f->COM('affected_layer', name => '', mode => 'all', affected => 'no');

	for my $tLayer (@SilkSelLayerLists){
		my $SSCoverLayer = $tLayer . $CoverLayerSuffix;
		$f->INFO(entity_type => 'layer',entity_path => "$JOB/$STEP/$SSCoverLayer",data_type => 'EXISTS');
		if ( $f->{doinfo}{gEXISTS} eq 'yes' ) {
			$f->COM('affected_layer', name => $SSCoverLayer, mode => 'single', affected => 'yes');
			$f->COM('sel_copy_other', dest => 'layer_name', target_layer => $tLayer, invert => 'yes', dx => 0, dy => 0, size => 0);
			$f->COM('affected_layer', name => $SSCoverLayer, mode => 'single', affected => 'yes');
		}
	}
	&MsgBox("脚本已运行Ok","info","ok","阻焊套文字 脚本已运行Ok,请检查!",);
	exit;
}

sub SilkBridgeOpt {	#字符桥优化
	#&RunScriptAct($MyScriptFile,'Run:SilkBridgeOpt',$OutPadCompensating,$CoverLayerSuffix,$TmpSilkSelLayerLists);
	unless($JOB){
		$f->PAUSE("The script must be run in a Job!!");
		exit(0);
	}
	my $RunSubScr = shift;
	my $OutPadCompensating = shift;
	my $CoverLayerSuffix = shift;
	my @SilkSelLayerLists = split ('@',"@_");

	&GetJobStep;
	my %JobMatrix = &JobMatrixDispose($JOB);

	my $ChangeAngleMode = 'no';
	#$ChangeAngleMode = 'yes';
	$f->COM('clear_layers');
	$f->COM('affected_layer', name => '', mode => 'all', affected => 'no');
	$f->COM('units', type => 'inch');

	my $SilkBridgeWidth = 4;
	#my $OutPadCompensating = 1.2;
	my $OutPadResize = 10 - $OutPadCompensating;
	my $TmpLineStretch = 150;
	my $ClearMaxLength = 15 / 1000 ;
	$f->COM('sel_options', clear_mode => 'clear_after', display_mode => 'displayed_layers', area_inout => 'inside', area_select => 'select', select_mode => 'standard', area_touching_mode => 'exclude');
	for my $tSilkLayer (@SilkSelLayerLists){
		my $SSCoverLayer = $tSilkLayer . $CoverLayerSuffix;
		my $tSolderMaskLayer = $JobMatrix{SumData}{TopSolderMask}[ scalar(@{$JobMatrix{SumData}{TopSolderMask}}) - 1 ];
		my $tOutLayer = $JobMatrix{SumData}{Outer}[0];
		if ( defined $JobMatrix{"LayersData"}{$tSilkLayer}{'BottomSilkScreenLayer'} ) {
			$tSolderMaskLayer = $JobMatrix{"SumData"}{"BottomSolderMask"}[0];
			$tOutLayer = $JobMatrix{SumData}{Outer}[ scalar( @{$JobMatrix{SumData}{Outer}} ) - 1 ];
		}
		#my $tSilkLayer = "c1";
		#my $tSolderMaskLayer = "m1";
		#my $tOutLayer = 'l1';

		my $tSolderMaskTmpLayer = $tSilkLayer . '-sm+';
		my $tSilkNegativeLayer = $tSilkLayer . '-n+';
		my $tSilkPositiveLayer = $tSilkLayer . '-p+';
		my $tSilkSurfaceLayer = $tSilkLayer . '-su+';
		my $tOutPadLayer = $tOutLayer . '-pad+';
		my $ChklistCreateLayerSuffix = 'neo_ms+';
		#my $tAnalysisLayer = $tSilkNegativeLayer;
		my $tAnalysisLayer = $tSolderMaskTmpLayer;

		my @TmpReportLayer = ('ms_1_' . $tAnalysisLayer . '_' . $ChklistCreateLayerSuffix,'mk_1_' . $tAnalysisLayer . '_' . $ChklistCreateLayerSuffix,);
		my $TmpLineLayer = $tSilkLayer . "-rep+";
		my $TmpLineLayer2 = $tSilkLayer . "-rep2+";
		my $TmpLineLayer3 = $tSilkLayer . "-rep3+";
		my $TmpOkLineLayer = $tSilkLayer . "-rep-ok+";
		my $SilkBridgeLayer = $tSilkLayer . "-bridge+";

		&DelLayers(@TmpReportLayer,$tSolderMaskTmpLayer,$tSilkNegativeLayer,$tSilkPositiveLayer,$tSilkSurfaceLayer,$tOutPadLayer,$TmpLineLayer,$TmpLineLayer . '+++',$TmpLineLayer2,$TmpLineLayer3,$TmpOkLineLayer,);

		#从字符层将正片 负片分离开
		$f->COM('affected_layer', name => $tSilkLayer, mode => 'single', affected => 'yes');
		#将负片copy到c1-n+
		$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
		$f->COM('set_filter_polarity', filter_name => '', positive => 'no', negative => 'yes');
		$f->COM('filter_area_strt');
		$f->COM('filter_area_end', filter_name => 'popup', operation => 'select');
		$f->COM('get_select_count');
		if ( $f->{COMANS} != 0 ) {
			$f->COM('sel_copy_other', dest => 'layer_name', target_layer => $tSilkNegativeLayer, invert => 'yes', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0);
		} else {
			&MsgBox("负片不存在","warning","ok","$tSilkLayer不存在负片,请执行阻焊套字符后再执行此脚本 !",);
			exit;
		}
		#将正片copy到c1-p+
		$f->COM('sel_clear_feat');
		$f->COM('set_filter_polarity', filter_name => '', positive => 'yes', negative => 'no');
		$f->COM('filter_area_strt');
		$f->COM('filter_area_end', filter_name => 'popup', operation => 'select');
		$f->COM('get_select_count');
		if ( $f->{COMANS} != 0 ) {
			$f->COM('sel_copy_other', dest => 'layer_name', target_layer => $tSilkPositiveLayer, invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0);
		}
		$f->COM('affected_layer', name => $tSilkLayer, mode => 'single', affected => 'no');

		#将阻焊正片图形copy出来
		$f->COM('affected_layer', name => $tSolderMaskLayer, mode => 'single', affected => 'yes');
		$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
		$f->COM('set_filter_polarity', filter_name => '', positive => 'yes', negative => 'no');
		$f->COM('filter_area_strt');
		$f->COM('filter_area_end', filter_name => 'popup', operation => 'select');
		$f->COM('get_select_count');
		if ( $f->{COMANS} != 0 ) {
			$f->COM('sel_copy_other', dest => 'layer_name', target_layer => $tSolderMaskTmpLayer, invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0);
		}
		$f->COM('affected_layer', name => $tSolderMaskLayer, mode => 'single', affected => 'no');

		#将外层的smd bga 加大 10-1.2 到c1-outlayer+
		$f->COM('affected_layer', name => $tOutLayer, mode => 'single', affected => 'yes');
		$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
		$f->COM('set_filter_type', filter_name => '', lines => 'yes', pads => 'yes', surfaces => 'yes', arcs => 'no', text => 'no');
		$f->COM('set_filter_polarity', filter_name => '', positive => 'yes', negative => 'no');
		$f->COM('set_filter_attributes', filter_name => 'popup', exclude_attributes => 'no', condition => 'no', attribute => '.bga', min_int_val => 0, max_int_val => 0, min_float_val => 0, max_float_val => 0, option => '', text => '');
		$f->COM('set_filter_attributes', filter_name => 'popup', exclude_attributes => 'no', condition => 'no', attribute => '.smd', min_int_val => 0, max_int_val => 0, min_float_val => 0, max_float_val => 0, option => '', text => '');
		$f->COM('set_filter_and_or_logic', filter_name => 'popup', criteria => 'inc_attr', logic => 'or');
		$f->COM('filter_area_strt');
		$f->COM('filter_area_end', filter_name => 'popup', operation => 'select');
		$f->COM('get_select_count');
		if ( $f->{COMANS} != 0 ) {
			$f->COM('sel_copy_other', dest => 'layer_name', target_layer => $tOutPadLayer, invert => 'no', dx => 0, dy => 0, size => $OutPadResize , x_anchor => 0, y_anchor => 0);
		}

		$f->COM('affected_layer', name => $tOutLayer, mode => 'single', affected => 'no');

		#另外建一层整层铜皮 -cu+ #将正层以负片的形式copy 到 -cu+ #将 -cu+ 合并铜皮
		$f->COM('create_layer', layer => $tSilkSurfaceLayer,);
		$f->COM('affected_layer', name => $tSilkSurfaceLayer, mode => 'single', affected => 'yes');
		$f->COM('sr_fill', type => 'solid', solid_type => 'surface', min_brush => 1, use_arcs => 'yes', cut_prims => 'no', outline_draw => 'no', outline_width => 0, outline_invert => 'no', polarity => 'positive', step_margin_x => '-0.5', step_margin_y => '-0.5', step_max_dist_x => 100, step_max_dist_y => 100, sr_margin_x => 0, sr_margin_y => 0, sr_max_dist_x => 0, sr_max_dist_y => 0, nest_sr => 'yes', consider_feat => 'no', feat_margin => 0, consider_drill => 'no', drill_margin => 0, consider_rout => 'no', dest => 'affected_layers', layer => '.affected', stop_at_steps => '');
		$f->COM('copy_layer', source_job => $JOB, source_step => $STEP, source_layer => $tSilkPositiveLayer, dest => 'layer_name', dest_step => '', dest_layer => $tSilkSurfaceLayer, mode => 'append', invert => 'yes', );
		$f->COM('sel_contourize', accuracy => 0, break_to_islands => 'yes', clean_hole_size => 0, clean_hole_mode => 'x_or_y');
		my $ClearSurMax = 1.5;
		$f->COM('rv_tab_empty', report => 'resize_rep', is_empty => 'yes');
		$f->COM('sel_resize', size => '-' . $ClearSurMax, corner_ctl => 'no');
		$f->COM('rv_tab_view_results_enabled', report => 'resize_rep', is_enabled => 'yes', serial_num => -1, all_count => -1);
		$f->COM('rv_tab_empty', report => 'resize_rep', is_empty => 'yes');
		$f->COM('sel_resize', size => $ClearSurMax, corner_ctl => 'no');
		$f->COM('rv_tab_view_results_enabled', report => 'resize_rep', is_enabled => 'yes', serial_num => -1, all_count => -1);

		$f->COM('affected_layer', name => $tSilkSurfaceLayer, mode => 'single', affected => 'no');

		#$f->COM('display_layer', name => $tSilkSurfaceLayer, display => 'no');
		#$f->COM('display_layer', name => $tSilkPositiveLayer, display => 'yes');
		#$f->COM('work_layer', name => $tSilkPositiveLayer);
		#$f->COM('display_layer', name => $tSilkSurfaceLayer, display => 'yes');
		#$f->COM('sel_copy_other', dest => 'layer_name', target_layer => $tSilkSurfaceLayer, invert => 'yes', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0);
		#$f->COM('display_layer', name => $tSilkPositiveLayer, display => 'no');
		#$f->COM('work_layer', name => $tSilkSurfaceLayer);
		#$f->COM('sel_contourize', accuracy => 0, break_to_islands => 'yes', clean_hole_size => 0, clean_hole_mode => 'x_or_y');
		#$f->COM('display_layer', name => $tSilkSurfaceLayer, display => 'no');

		#将正片再copy到 c1-p2+
		#$f->COM('affected_layer', name => $tSilkPositiveLayer, mode => 'single', affected => 'yes');
		#$f->COM('sel_copy_other', dest => 'layer_name', target_layer => 'c1-p2+', invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0);
		#$f->COM('affected_layer', name => $tSilkPositiveLayer, mode => 'single', affected => 'no');
		# c1-p2+整体化
		#$f->COM('affected_layer', name => 'c1-p2+', mode => 'single', affected => 'yes');
		#$f->COM('sel_contourize', accuracy => 0, break_to_islands => 'yes', clean_hole_size => 0, clean_hole_mode => 'x_or_y');
		#$f->COM('affected_layer', name => 'c1-p2+', mode => 'single', affected => 'no');

		#将分析c1-n+层间距
		my $ChkRange;
		my $MaxChkSpace;
		if ( $tAnalysisLayer eq $tSilkNegativeLayer ){
			$MaxChkSpace = 4;
		#	$ChkRange = '1.000000;2.000000;3.990000';
			$ChkRange = '1.000000;2.000000;' . ($MaxChkSpace - 0.01);
		} elsif ( $tAnalysisLayer eq $tSolderMaskTmpLayer ){
		#	$MaxChkSpace =  5.5 * 2 + 4;
		#	$MaxChkSpace =  sqrt( (5.5 * 2 + 4) ** 2 +  (5.5 * 2 + 4) ** 2 );
			$MaxChkSpace =  20;
		#	$ChkRange = '1.000000' . ';' . ( 5.5 * 2 ) . ';' . ( 5.5 * 2 + 3.99 );
			$ChkRange = '1.000000' . ';' . ( 5.5 * 2 ) . ';' . ($MaxChkSpace - 0.01);
		#	$ChkRange = sprintf( "%.6f;%.6f;%.6f",1,( 5.5 * 2 ),( 5.5 * 2 + 3.99 ) );
			$ClearMaxLength = 7 / 1000
		}
		#$f->PAUSE("ChkRange=$ChkRange");

		#$f->COM('affected_layer', name => $tSilkNegativeLayer, mode => 'single', affected => 'yes');
		#$f->COM('affected_layer', name => $tSolderMaskTmpLayer, mode => 'single', affected => 'yes');
		$f->COM('affected_layer', name => $tAnalysisLayer, mode => 'single', affected => 'yes');
		$f->VOF;
		$f->COM('chklist_delete', chklist => 'checklist');
		$f->COM('chklist_create', chklist => 'checklist', allow_save => 'no');
		$f->VON;
		$f->COM('show_tab', tab => 'Checklists', show => 'no');
		#$f->COM('top_tab', tab => 'Checklists');
		$f->COM('chklist_single', show => 'no', action => 'valor_analysis_signal');
		$f->VOF;
		$f->COM('chklist_delete', chklist => 'checklist');
		$f->VON;
		$f->COM('chklist_cupd', chklist => 'valor_analysis_signal', nact => 1, params => "((pp_layer=.affected)(pp_spacing=$MaxChkSpace)(pp_r2c=10)(pp_d2c=10)(pp_sliver=4)(pp_min_pad_overlap=5)(pp_tests=Spacing)(pp_selected=All)(pp_check_missing_pads_for_drills=Yes)(pp_use_compensated_rout=No)(pp_sm_spacing=No))", mode => 'regular');
		for (qw/bga2bga bga2pad bga2c c2l c2c cov2cov cov2cov_sn c2c_con c2c_con_neg l2l p2c_con p2l_con p2p_con p2c p2line p2p p2surface smd2pad smd2smd smd2c smd2sur_spacing smd2trace_spacing general_sp/){
		#	$f->COM('chklist_erf_range', chklist => 'valor_analysis_signal', nact => 1, redisplay => 0, category => 'bga2bga', erf => 'singer', range => '1.000000;2.000000;3.990000');
			$f->COM('chklist_erf_range', chklist => 'valor_analysis_signal', nact => 1, redisplay => 0, category => $_, erf => 'singer', range => $ChkRange);
		}
		$f->COM('chklist_set_hdr', chklist => 'valor_analysis_signal', save_res => 'no', stop_on_err => 'no', run => 'activated', area => 'global', mask => 'None', mask_usage => 'include');
		$f->COM('chklist_run', chklist => 'valor_analysis_signal', nact => 1, area => 'global', async_run => 'no');
		#$f->COM('chklist_close', chklist => 'frontline_dfm_spacing_opt', mode => 'hide');
		#$f->COM('affected_layer', name => $tSilkNegativeLayer, mode => 'single', affected => 'no');
		#$f->COM('affected_layer', name => $tSolderMaskTmpLayer, mode => 'single', affected => 'no');
		$f->COM('affected_layer', name => $tAnalysisLayer, mode => 'single', affected => 'no');

		#创建分析结果层
		$f->COM('chklist_create_lyrs', chklist => 'valor_analysis_signal', severity => 3, suffix => 'neo_ms+');
		$f->COM('copy_layer', source_job => $JOB, source_step => $STEP, source_layer => $TmpReportLayer[0], dest => 'layer_name', dest_layer => $TmpLineLayer, mode => 'replace', invert => 'no');
		&DelLayers(@TmpReportLayer);

		$f->COM('affected_layer', name => $TmpLineLayer, mode => 'single', affected => 'yes');
		$f->COM('sel_delete_atr', mode => 'all');
		#去重
		$f->COM('sel_change_sym', symbol => 'r' . $SilkBridgeWidth, reset_angle => 'no');

		$f->COM('chklist_single', show => 'no', action => 'valor_dfm_nflr');
		#$f->COM('chklist_close', chklist => 'valor_analysis_signal', mode => 'hide');
		$f->COM('chklist_cupd', chklist => 'valor_dfm_nflr', nact => 1, params => '((pp_layer=.affected)(pp_min_line=0)(pp_max_line=20)(pp_margin=1)(pp_remove_item=Line;Arc)(pp_delete=Covered)(pp_work=Features)(pp_remove_mark=Remove))', mode => 'regular');
		$f->COM('chklist_erf_variable', chklist => 'valor_dfm_nflr', nact => 1, variable => 'v_tolerance', value => 1, options => 0);
		$f->COM('chklist_cnf_act', chklist => 'valor_dfm_nflr', nact => 1, cnf => 'no');
		$f->COM('chklist_set_hdr', chklist => 'valor_dfm_nflr', save_res => 'no', stop_on_err => 'no', run => 'activated', area => 'global', mask => 'None', mask_usage => 'include');
		$f->COM('chklist_run', chklist => 'valor_dfm_nflr', nact => 1, area => 'global', async_run => 'no');
		$f->COM('chklist_cupd', chklist => 'valor_dfm_nflr', nact => 1, params => '((pp_layer=.affected)(pp_min_line=0)(pp_max_line=20)(pp_margin=1)(pp_remove_item=Line;Arc)(pp_delete=Duplicate)(pp_work=Features)(pp_remove_mark=Remove))', mode => 'regular');
		$f->COM('chklist_cnf_act', chklist => 'valor_dfm_nflr', nact => 1, cnf => 'no');
		$f->COM('chklist_set_hdr', chklist => 'valor_dfm_nflr', save_res => 'no', stop_on_err => 'no', run => 'activated', area => 'global', mask => 'None', mask_usage => 'include');
		$f->COM('chklist_run', chklist => 'valor_dfm_nflr', nact => 1, area => 'global', async_run => 'no');
		#没有接触到c1-p+ 的删除

		$f->COM('sel_change_sym', symbol => 'r0.2', reset_angle => 'no');
		$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
		$f->COM('sel_ref_feat', layers => $tSilkPositiveLayer, use => 'filter', mode => 'disjoint', pads_as => 'shape', f_types => 'line;pad;surface;arc;text', polarity => 'positive;negative', include_syms => '', exclude_syms => '');
		$f->COM('get_select_count');
		if ( $f->{COMANS} != 0 ) {
			$f->COM('sel_delete');
		}

		#$f->COM('display_layer', name => $TmpLineLayer, display => 'no');
		# 以自身 旋转 90 度 大小改为 4mil 接触到 c1-outlayer+的删除
		#$f->COM('display_layer', name => $TmpLineLayer, display => 'yes');
		#$f->COM('work_layer', name => $TmpLineLayer);
		$f->COM('sel_transform', oper => 'rotate', x_anchor => 0, y_anchor => 0, angle => 90,x_scale => 1, y_scale => 1, x_offset => 0, y_offset => 0, mode => 'axis', duplicate => 'no');
		$f->COM('sel_change_sym', symbol => 'r' . $SilkBridgeWidth, reset_angle => 'no');
		$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
		$f->COM('sel_ref_feat', layers => $tOutPadLayer, use => 'filter', mode => 'touch', pads_as => 'shape', f_types => 'line;pad;surface;arc;text', polarity => 'positive;negative', include_syms => '', exclude_syms => '');
		$f->COM('get_select_count');
		if ( $f->{COMANS} != 0 ) {
			$f->COM('sel_delete');
		}

		#备份这一层 -l-bak+
#		$f->PAUSE(dfh);
#		$f->COM('sel_copy_other', dest => 'layer_name', target_layer => $TmpLineLayer2, invert => 'no', dx => 0, dy => 0, size => '8.8', x_anchor => 0, y_anchor => 0);
		$f->COM('sel_copy_other', dest => 'layer_name', target_layer => $TmpLineLayer2, invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0);

		if ( $ChangeAngleMode eq 'yes' ) {
			#将 0°45°90° 的挑出来,不是这些的修正角度
			$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
			$f->COM('set_filter_type', filter_name => '', lines => 'yes', pads => 'no', surfaces => 'no', arcs => 'yes', text => 'no');
			$f->COM('set_filter_polarity', filter_name => '', positive => 'yes', negative => 'no');
			for my $tNum ( 0 .. 7 ){#循环0-360之间的 45°跨度 # 45°的也区分长短判断
				my $tAngle = 45 * $tNum;
#				$f->COM('set_filter_length');
				$f->COM('set_filter_angle', slot => 'lines', min_angle => $tAngle, max_angle => $tAngle, direction => 'ccw');
#				$f->COM('adv_filter_reset');
				$f->COM('adv_filter_set', filter_name => 'popup', active => 'yes', limit_box => 'no', bound_box => 'no', srf_values => 'no', srf_area => 'no', mirror => 'any', ccw_rotations => '');
				$f->COM('filter_area_strt');
				$f->COM('filter_area_end', filter_name => 'popup', operation => 'select');
			}
			$f->COM('sel_reverse');
			$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');

			$f->COM('get_select_count');
			if ($f->{COMANS} != 0 ) {
				#$f->COM('sel_move_other', target_layer => $TmpOkLineLayer, invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0);

				#my $TmpLineLayer = "ms-1+++";
				#直接解析角度,存哈希,连续选择index 旋转角度.
				my $tInfoFile = $ENV{GENESIS_TMP} . '/info.' . int(rand(9999));
				#$f->COM ( 'info',out_file => $tInfoFile,args => " -t layer -e $JOB/$STEP/$TmpLineLayer -d FEATURES -o select" ) ;
			#	$f->COM ( 'info',out_file => $tInfoFile,args => " -t layer -e $JOB/$STEP/$TmpLineLayer -d FEATURES -o feat_index" );
				$f->COM ( 'info',out_file => $tInfoFile,args => " -t layer -e $JOB/$STEP/$TmpLineLayer -d FEATURES -o feat_index+select" );
				$f->COM('sel_clear_feat');
				my %AngleData;
				open ( FH,"<$tInfoFile" ) ;
				while ( <FH> ) {
					my $line = $_;
				#	if ( $line =~ /\#L/ ) {
					if ( $line =~ /^\#(\d+)\s+\#L/ ) {
						#3055 #L 0.7425242 2.4380701 0.7169921 2.43807 r4 P 0 ;.string=general_sp
				#		($Xs,$Ys,$Xe,$Ye,$Size,$Positive ) = ( split ( ' ',$line ) ) [1,2,3,4,5,6,];

						my ($tIndex,$Xs,$Ys,$Xe,$Ye,$Size) = ($line =~ /^\#(\d+)\s+\#L\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+/i);
			#			$f->PAUSE("($tIndex,$Xs,$Ys,$Xe,$Ye,$Size)=$line");

			#			my $tLineAngle = atan2 ( $Ye - $Ys,$Xe - $Xs ) * 180 / pi;
						my $tLineAngle = 180 + atan2 ( $Ye - $Ys,$Xe - $Xs ) * 180 / pi;
						if ( $tLineAngle < 0 ){
							$tLineAngle += 360;
						}
						push @{$AngleData{$tLineAngle}},$tIndex;
					}
				}
				close FH;
				unlink $tInfoFile;

				for my $tAngle ( keys %AngleData ) {
					for my $tIndex (@{$AngleData{$tAngle}} ){
						$f->COM('sel_layer_feat', operation => 'select', layer => $TmpLineLayer, index => $tIndex);
					}
			#		$f->PAUSE("tAngle=$tAngle");

					my $AngleMultiple = int ( $tAngle / 45 );
					my $AngleRemainder = $tAngle - $AngleMultiple;
					if ( $AngleRemainder > 22.5 ){
						$AngleMultiple += 1;
					}
					my $RotationAngle = $AngleMultiple * 45 - $tAngle ;
					if ( $RotationAngle < 0 ){
						$RotationAngle += 360;
					}
			#		my $RotationAngle = 360 - $RotationAngle ;
			#		$f->PAUSE("@{$AngleData{$tAngle}},tAngle=$tAngle,RotationAngle=$RotationAngle");
			#		$f->COM('sel_transform', oper => 'rotate', x_anchor => 0, y_anchor => 0, angle => $RotationAngle,x_scale => 1, y_scale => 1, x_offset => 0, y_offset => 0, mode => 'axis', duplicate => 'no');
					$f->COM('sel_transform', oper => 'rotate', angle => $RotationAngle, direction => 'ccw', x_anchor => 0, y_anchor => 0, x_scale => 1, y_scale => 1, x_offset => 0, y_offset => 0, mode => 'axis', duplicate => 'no');
			#		$f->COM('sel_transform', oper => 'rotate', angle => $RotationAngle, x_anchor => 0, y_anchor => 0, x_scale => 1, y_scale => 1, x_offset => 0, y_offset => 0, mode => 'axis', duplicate => 'no');
			#		$f->PAUSE("111=@{$AngleData{$tAngle}},tAngle=$tAngle,RotationAngle=$RotationAngle");

					$f->COM('sel_clear_feat');

				}

			}
		}

		#$f->COM('sel_pattern', tol => '0.1');
		#拉长  150mil
		$f->COM('sel_extend_slots', mode => 'ext_by', size => $TmpLineStretch, from => 'center');

		$f->COM('affected_layer', name => $TmpLineLayer, mode => 'single', affected => 'no');

		#改为s4
		$f->COM('affected_layer', name => $TmpLineLayer, mode => 'single', affected => 'yes');

		#$f->COM('display_layer', name => $TmpLineLayer, display => 'yes');
		#$f->COM('work_layer', name => $TmpLineLayer);
		$f->COM('sel_change_sym', symbol => 's' . $SilkBridgeWidth, reset_angle => 'no');

		#将线以 -cu+套除
		$f->COM('clip_area_strt');
		$f->COM('clip_area_end', layers_mode => 'layer_name', layer => $TmpLineLayer, ref_layer => $tSilkSurfaceLayer, area => 'reference', area_type => 'rectangle', inout => 'inside', contour_cut => 'no', margin => 0, feat_types => 'line;pad;surface;arc;text', pol_types => 'positive;negative');

		#优化线 0 0 0
		$f->COM('rv_tab_empty', report => 'design2rout_rep', is_empty => 'yes');
		$f->COM('sel_design2rout', det_tol => '0.1', con_tol => '0.1', rad_tol => '0.1');
		$f->COM('rv_tab_view_results_enabled', report => 'design2rout_rep', is_enabled => 'yes', serial_num => -1, all_count => -1);

		#没有接触到备份层的删除
		$f->COM('sel_change_sym', symbol => 'r' . $SilkBridgeWidth, reset_angle => 'no');
		$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
		$f->COM('sel_ref_feat', layers => $TmpLineLayer2, use => 'filter', mode => 'disjoint', pads_as => 'shape', f_types => 'line;pad;surface;arc;text', polarity => 'positive;negative', include_syms => '', exclude_syms => '');
		$f->COM('get_select_count');
		if ($f->{COMANS} != 0 ) {
			$f->COM('sel_delete');
		}

		#将线以 -pad+套除
		$f->COM('clip_area_strt');
		$f->COM('clip_area_end', layers_mode => 'layer_name', layer => $TmpLineLayer, ref_layer => $tOutPadLayer, margin => 2,area => 'reference', area_type => 'rectangle', inout => 'inside', contour_cut => 'no',  feat_types => 'line;pad;surface;arc;text', pol_types => 'positive;negative');

		#没有接触到负片的删除
		$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
		$f->COM('sel_ref_feat', layers => $tSilkNegativeLayer, use => 'filter', mode => 'disjoint', pads_as => 'shape', f_types => 'line;pad;surface;arc;text', polarity => 'positive;negative', include_syms => '', exclude_syms => '');
		$f->COM('get_select_count');
		if ($f->{COMANS} != 0 ) {
			$f->COM('sel_delete');
		}

		#小于ClearMaxLength 的线选出来删除
		$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
		$f->COM('set_filter_length', slot => 'lines', min_length => 0, max_length => $ClearMaxLength,);
		$f->COM('filter_area_strt');
		$f->COM('filter_area_end', filter_name => 'popup', operation => 'select');
		$f->COM('get_select_count');
		if ($f->{COMANS} != 0 ) {
			$f->COM('sel_delete');
		}

		#挑出不是 0°45°90° 的
		$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
		$f->COM('set_filter_type', filter_name => '', lines => 'yes', pads => 'no', surfaces => 'no', arcs => 'yes', text => 'no');
		$f->COM('set_filter_polarity', filter_name => '', positive => 'yes', negative => 'no');
		for my $tNum ( 0 .. 7 ){#循环0-360之间的 45°跨度 
			my $tAngle = 45 * $tNum;
#			$f->COM('set_filter_length');
			$f->COM('set_filter_angle', slot => 'lines', min_angle => $tAngle, max_angle => $tAngle, direction => 'ccw');
#			$f->COM('adv_filter_reset');
			$f->COM('adv_filter_set', filter_name => 'popup', active => 'yes', limit_box => 'no', bound_box => 'no', srf_values => 'no', srf_area => 'no', mirror => 'any', ccw_rotations => '');
			$f->COM('filter_area_strt');
			$f->COM('filter_area_end', filter_name => 'popup', operation => 'select');
		}
		$f->COM('sel_reverse');
		$f->COM('get_select_count');
		if ($f->{COMANS} != 0 ) {
			$f->COM('sel_move_other', target_layer => $TmpLineLayer3, invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0);
			$f->COM('affected_layer', name => $TmpLineLayer, mode => 'single', affected => 'no');
			$f->COM('affected_layer', name => $TmpLineLayer3, mode => 'single', affected => 'yes');
#			$f->COM('display_layer', name => 'c1-rep+', display => 'no');
#			$f->COM('display_layer', name => $TmpLineLayer3, display => 'yes');
			my $ObliqueClip = 0.9;
			$f->COM('clip_area_strt');
			$f->COM('clip_area_end', layers_mode => 'layer_name', layer => $TmpLineLayer3, area => 'reference', margin => $ObliqueClip, ref_layer => $tSilkSurfaceLayer, area_type => 'rectangle', inout => 'inside', contour_cut => 'no',feat_types => 'line;pad;surface;arc;text', pol_types => 'positive;negative');
			$f->COM('clip_area_strt');                                                                         
			$f->COM('clip_area_end', layers_mode => 'layer_name', layer => $TmpLineLayer3, area => 'reference', margin => $ObliqueClip, ref_layer => $tOutPadLayer, area_type => 'rectangle', inout => 'inside', contour_cut => 'no',feat_types => 'line;pad;surface;arc;text', pol_types => 'positive;negative');
			$f->COM('cur_atr_reset');
			$f->COM('cur_atr_set', attribute => '.string', text => '?');
			$f->COM('sel_change_atr', mode => 'add');
			$f->COM('cur_atr_reset');
			$f->COM('sel_copy_other', dest => 'layer_name', target_layer => $TmpLineLayer, invert => 'no', dx => 0, dy => 0, size => 0, x_anchor => 0, y_anchor => 0);
		}

		$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
#	$f->PAUSE(111);
		$f->COM('copy_layer', source_job => $JOB, source_step => $STEP, source_layer => $TmpLineLayer, dest => 'layer_name', dest_layer => $SilkBridgeLayer, mode => 'replace', invert => 'no');

		&DelLayers(@TmpReportLayer,$tSolderMaskTmpLayer,$tSilkNegativeLayer,$tSilkPositiveLayer,$tSilkSurfaceLayer,$tOutPadLayer,$TmpLineLayer,$TmpLineLayer . '+++',$TmpLineLayer2,$TmpLineLayer3,$TmpOkLineLayer,);
	}
	$f->COM('sel_options', clear_mode => 'clear_after', display_mode => 'all_layers', area_inout => 'inside', area_select => 'select', select_mode => 'standard', area_touching_mode => 'exclude');
	&MsgBox("脚本已运行Ok","info","ok","字符桥优化 脚本已运行Ok,请选择、修改及检查你所需要的字符桥!",);
	my $SilkBridgeLayer = $SilkSelLayerLists[0] . "-bridge+";
	$f->COM('reset_filter_criteria', filter_name => '', criteria => 'all');
	$f->COM('display_width', mode => 'on');
	$f->VOF;
	$f->COM('display_layer', name => $SilkSelLayerLists[0], display => 'yes');
	$f->COM('display_layer', name => $SilkBridgeLayer, display => 'yes');
	$f->VON;
	$f->COM('zoom_home');
	exit;
}

sub OpenSilkCheckList {  #文字分析
	$f->COM('show_component', component => 'Checklists', show => 'yes', width => 0, height => 0);
	$f->COM('top_tab', tab => 'Checklists');
	my $SilkCheckList = 'lc-check';
	$f->COM('chklist_open', chklist => $SilkCheckList);
	$f->COM('chklist_show', chklist => $SilkCheckList, nact => 1, pinned => 'no', pinned_enabled => 'yes');
}

sub DelLayers {
	$f->VOF;
	for ( @_ ) {
		$f->COM('delete_layer', layer => $_);
	}
	$f->VON;
}

sub GetJobStep {
	$JOB  = $ENV{"JOB"} ;
	$STEP = $ENV{"STEP"} ;
}

sub RunHotKey {
#	use Time::HiRes  qw( usleep );
#	use X11::GUITest qw( :ALL );
#	my @windows = FindWindowLike("PID:10662");
#	die "No InCAM windows found" unless( scalar(@windows) > 0 );

#RaiseWindow WINDOWID
#Raises the specified window to the top of the stack, so that no other windows cover it.

#zero is returned on failure, non-zero for success.

#LowerWindow WINDOWID
#Lowers the specified window to the bottom of the stack, so other existing windows will cover it.

#zero is returned on failure, non-zero for success.


}

sub MsgBox {
#	my ($tType,$tMsg,$tIco,$tTitle) = (@_);
	my ($tTitle,$tIco,$tType,$tMsg,) = (@_);

#	my $tMw = Tkx::widget->new(".");
#	if ("$tLogoFile" ne "" ) {
#		if ( -e "$tLogoFile" ) {
#			$tMw->g_wm_iconbitmap("$tLogoFile");
#		}
#	}
#	$tMw->g_wm_attributes('-topmost',1);
#	$tMw->g_wm_geometry("0x0");
#	$tMw->g_wm_withdraw;
#	my $MsgOut = Tkx::tk___messageBox(-type => "$tType",-message => "$tMsg",-icon => "$tIco",-title => "$tTitle",-parent => $tMw,	);
#	$tMw->g_destroy;
#	Tkx::MainLoop();
	my $tParameterText = join ('::',($tTitle,$tMsg,$tType,$tIco,));
	#'标题::示范内容::按钮[ok|okcancel|yesno|yesnocancel|abortretryignore|retrycancel]::图标[info|question|warning|error]'
#	my $MsgOut = `perl /mnt/hgfs/LinuxShare/MessBoxTkx.pl $tParameterText`;
	my $MsgOut = `$ENV{INCAM_SITE_DATA_DIR}/scripts/User/Neo/Tools/MessBoxs.Neo $tParameterText`;
	chomp $MsgOut;
	return ($MsgOut);
}

sub JobMatrixDispose {	#料号Matrix处理		 #my %JobMatrix = &JobMatrixDispose($JOB);
	my $CurrJob = shift;
	#3399ff 68%  覆盖  #3399ff 50%  覆盖
	if ( "$CurrJob" ne '' ) {
		$f->INFO(entity_type => 'matrix',entity_path => "$CurrJob/matrix",data_type => 'ROW',parameters => "context+layer_type+name+row+side+type");
		my %tJobMatrix;
		for my $gROWrow (@{$f->{doinfo}{gROWrow}}){
			my $tNum = $gROWrow -1;
			my $tLayerName = $f->{doinfo}{gROWname}[$tNum];
			if ( $f->{doinfo}{gROWtype}[$tNum] eq 'layer' ){
				push @{$tJobMatrix{"SumData"}{LayerRow}},$gROWrow;
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
							#$tJobMatrix{"RowData"}{$gROWrow}{'Color'} = '#FDC74D';
							#$tJobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#98B0A6';
							#
							#$tJobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#FDC74D';
							#$tJobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#98B0A6';
						} elsif ( $f->{doinfo}{gROWlayer_type}[$tNum] eq 'power_ground') {
							#$tJobMatrix{"RowData"}{$gROWrow}{'Color'} = '#E6C412';
							#$tJobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#8CAE89';
							#
							#$tJobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#E6C412';
							#$tJobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#8CAE89';
						} elsif ( $f->{doinfo}{gROWlayer_type}[$tNum] eq 'mixed' ) {
							#$tJobMatrix{"RowData"}{$gROWrow}{'Color'} = '#CCCCA5';
							#$tJobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#7FB2D2';
							#
							#$tJobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#CCCCA5';
							#$tJobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#7FB2D2';
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
						#$tJobMatrix{"RowData"}{$gROWrow}{'Color'} = '#00A279';
						#$tJobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#1A9DBC';
						#
						$tJobMatrix{"LayersData"}{$tLayerName}{'阻焊'} = 'Yes';
						#$tJobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#00A279';
						#$tJobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#1A9DBC';
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
						#$tJobMatrix{"RowData"}{$gROWrow}{'Color'} = '#FFFFFF';
						#$tJobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#99CCFF';
						#
						$tJobMatrix{"LayersData"}{$tLayerName}{'字符'} = 'Yes';
						#$tJobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#FFFFFF';
						#$tJobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#99CCFF';
					} elsif ( $f->{doinfo}{gROWlayer_type}[$tNum] eq 'solder_paste' ) {
						push @{$tJobMatrix{"SumData"}{SolderPaste}},$f->{doinfo}{gROWname}[$tNum];
						#
						$tJobMatrix{"RowData"}{$gROWrow}{'钢网'} = 'Yes';
						#$tJobMatrix{"RowData"}{$gROWrow}{'Color'} = '#FFFFCE';
						#$tJobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#99CCE7';
						#
						$tJobMatrix{"LayersData"}{$tLayerName}{'钢网'} = 'Yes';
						#$tJobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#FFFFCE';
						#$tJobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#99CCE7';
					} elsif ( $f->{doinfo}{gROWlayer_type}[$tNum] eq 'drill' ) {
						push @{$tJobMatrix{"SumData"}{Drill}},$f->{doinfo}{gROWname}[$tNum];
						$tJobMatrix{"RowData"}{$gROWrow}{'钻孔'} = 'Yes';
						#$tJobMatrix{"RowData"}{$gROWrow}{'Color'} = '#AFAFAF';
						#$tJobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#71A4D7';
						#
						$tJobMatrix{"LayersData"}{$tLayerName}{'钻孔'} = 'Yes';
						#$tJobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#AFAFAF';
						#$tJobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#71A4D7';
					} elsif ( $f->{doinfo}{gROWlayer_type}[$tNum] eq 'rout' ) {
						push @{$tJobMatrix{"SumData"}{Rout}},$f->{doinfo}{gROWname}[$tNum];
						#$tJobMatrix{"RowData"}{$gROWrow}{'Color'} = '#D4D1C9';
						#$tJobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#83B5E4';
						#
						#$tJobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#D4D1C9';
						#$tJobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#83B5E4';
					} elsif ( $f->{doinfo}{gROWlayer_type}[$tNum] eq 'document' ) {
						push @{$tJobMatrix{"SumData"}{Document}},$f->{doinfo}{gROWname}[$tNum];
						#$tJobMatrix{"RowData"}{$gROWrow}{'Color'} = '#9BDBDB';
						#$tJobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#67BAED';
						#
						#$tJobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#9BDBDB';
						#$tJobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#67BAED';
					} else {
						push @{$tJobMatrix{"SumData"}{Other}},$f->{doinfo}{gROWname}[$tNum];
						#
						#$tJobMatrix{"RowData"}{$gROWrow}{'Color'} = '#9BDBDB';
						#$tJobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#67BAED';
						#
						#$tJobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#9BDBDB';
						#$tJobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#67BAED';
					}
				} else {
					push @{$tJobMatrix{"SumData"}{Misc}},$f->{doinfo}{gROWname}[$tNum];
					#$tJobMatrix{"RowData"}{$gROWrow}{'Color'} = '#9BDBDB';
					#$tJobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#67BAED';
					#
					#$tJobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#9BDBDB';
					#$tJobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#67BAED';
				}
			} else {
				push @{$tJobMatrix{"SumData"}{Empty}},$gROWrow;
				#
				if ( $f->{doinfo}{gROWlayer_type}[$tNum] eq 'document' ) {
					push @{$tJobMatrix{"SumData"}{Document}},$f->{doinfo}{gROWname}[$tNum];
					#$tJobMatrix{"RowData"}{$gROWrow}{'Color'} = '#9BDBDB';
					#$tJobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#67BAED';
					#
					#$tJobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#9BDBDB';
					#$tJobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#67BAED';
				}
			}
		}
		return (%tJobMatrix);
	} else {
		return ();
	}
}

sub CreateCoverLayerButtonAct {  #创建套层 中间Sub
	my $RunMode = shift;
	my @ListBoxLists  = split( " ",$LayerList->get(0,'end') );
	my @SelListsIndex = split( " ",$LayerList->curselection() );

	my @SilkSelLayerLists;
	for my $Index (@SelListsIndex){
		push @SilkSelLayerLists,$ListBoxLists[$Index];
	}
	my $TmpSilkSelLayerLists = join('@', @SilkSelLayerLists);
	if ( $RunMode eq 'InnRun' ) {
		&InnRunScriptAct($MyScriptFile,'Run:SilkScreenCoverLayerCreate',$SilkScreenToSolderMask,$SilkScreenToSmdBga,$CoverLayerSuffix,$TmpSilkSelLayerLists);
	} else {
		&RunScriptAct($MyScriptFile,'Run:SilkScreenCoverLayerCreate',$SilkScreenToSolderMask,$SilkScreenToSmdBga,$CoverLayerSuffix,$TmpSilkSelLayerLists);
	}
}

sub ChangeSilkMinLineWidthButtonAct {  #修改字符最小线宽 中间Sub
	my $RunMode = shift;

	my @ListBoxLists  = split( " ",$LayerList->get(0,'end') );
	my @SelListsIndex = split( " ",$LayerList->curselection() );

	my @SilkSelLayerLists;
	for my $Index (@SelListsIndex){
		push @SilkSelLayerLists,$ListBoxLists[$Index];
	}
	my $TmpSilkSelLayerLists = join('@', @SilkSelLayerLists);
	if ( $RunMode eq 'InnRun' ) {
		&InnRunScriptAct($MyScriptFile,'Run:ChangeSilkMinLineWidth',$SilkMinLineWidth,$TmpSilkSelLayerLists);
	} else {
		&RunScriptAct($MyScriptFile,'Run:ChangeSilkMinLineWidth',$SilkMinLineWidth,$TmpSilkSelLayerLists);
	}
}

sub TextAndTextBoxSeparatedButtonAct {  #字框分离 中间Sub
	my $RunMode = shift;

	my @ListBoxLists  = split( " ",$LayerList->get(0,'end') );
	my @SelListsIndex = split( " ",$LayerList->curselection() );

	my @SilkSelLayerLists;
	for my $Index (@SelListsIndex){
		push @SilkSelLayerLists,$ListBoxLists[$Index];
	}
	my $TmpSilkSelLayerLists = join('@', @SilkSelLayerLists);
	if ( $RunMode eq 'InnRun' ) {
		&InnRunScriptAct($MyScriptFile,'Run:TextAndTextBoxSeparated',$TextSeparatedTextMaxHeight,$TextSeparatedLayerSuffix,$CoverLayerSuffix,$TmpSilkSelLayerLists);
	} else {
		&RunScriptAct($MyScriptFile,'Run:TextAndTextBoxSeparated',$TextSeparatedTextMaxHeight,$TextSeparatedLayerSuffix,$CoverLayerSuffix,$TmpSilkSelLayerLists);
	}
}

sub TextCoverTextBoxButtonAct {  #文字套字框 中间Sub
	my $RunMode = shift;

	my @ListBoxLists  = split( " ",$LayerList->get(0,'end') );
	my @SelListsIndex = split( " ",$LayerList->curselection() );

	my @SilkSelLayerLists;
	for my $Index (@SelListsIndex){
		push @SilkSelLayerLists,$ListBoxLists[$Index];
	}
	my $TmpSilkSelLayerLists = join('@', @SilkSelLayerLists);
	if ( $RunMode eq 'InnRun' ) {
		&InnRunScriptAct($MyScriptFile,'Run:TextCoverTextBox',$TextSeparatedLayerSuffix,$TmpSilkSelLayerLists);
	} else {
		&RunScriptAct($MyScriptFile,'Run:TextCoverTextBox',$TextSeparatedLayerSuffix,$TmpSilkSelLayerLists);
	}
}

sub SolderMaskCoverTextBoxButtonAct {  #阻焊套文字 中间Sub
	my $RunMode = shift;

	my @ListBoxLists  = split( " ",$LayerList->get(0,'end') );
	my @SelListsIndex = split( " ",$LayerList->curselection() );

	my @SilkSelLayerLists;
	for my $Index (@SelListsIndex){
		push @SilkSelLayerLists,$ListBoxLists[$Index];
	}
	my $TmpSilkSelLayerLists = join('@', @SilkSelLayerLists);
	if ( $RunMode eq 'InnRun' ) {
		&InnRunScriptAct($MyScriptFile,'Run:SolderMaskCoverTextBox',$CoverLayerSuffix,$TmpSilkSelLayerLists);
	} else {
		&RunScriptAct($MyScriptFile,'Run:SolderMaskCoverTextBox',$CoverLayerSuffix,$TmpSilkSelLayerLists);
	}
}

sub SilkBridgeOptButtonAct {  #字符桥优化 中间Sub
	my $RunMode = shift;

	my @ListBoxLists  = split( " ",$LayerList->get(0,'end') );
	my @SelListsIndex = split( " ",$LayerList->curselection() );

	my @SilkSelLayerLists;
	for my $Index (@SelListsIndex){
		push @SilkSelLayerLists,$ListBoxLists[$Index];
	}
	my $TmpSilkSelLayerLists = join('@', @SilkSelLayerLists);
	if ( $RunMode eq 'InnRun' ) {
		&InnRunScriptAct($MyScriptFile,'Run:SilkBridgeOpt',$OutPadCompensating,$CoverLayerSuffix,$TmpSilkSelLayerLists);
	} else {
		&RunScriptAct($MyScriptFile,'Run:SilkBridgeOpt',$OutPadCompensating,$CoverLayerSuffix,$TmpSilkSelLayerLists);
	}
}

sub iTkxGetImageFile {  #获取并设置图片 # iTkxGetImageFile('SetMwLogo',$mw);   # iTkxGetImageFile('GetLogo'); # iTkxGetImageFile('GetImg',$ImgFileName,@SearchImagePath);
	my $tMode = shift;
	my ($MwVar,$ImgFileName,@ImgFileType,@SearchImagePath,$LastImgFileType,);
	my $tImageFile = "";
	if ( $tMode eq 'SetMwLogo' or $tMode eq 'GetLogo' ) {
		if ( $tMode eq 'SetMwLogo' ) {
			$MwVar = shift;
		}
		$ImgFileName = shift || 'Logo' ;
		if ( defined $_[0] ){
			@ImgFileType = @_ ;
		}else{
			if ( $tMode eq 'SetMwLogo' ) {
				@ImgFileType = qw /ico png gif xpm/;
			} else {
				@ImgFileType = qw /gif xpm png ico/;
#				print '($MwVar,$ImgFileName,$ImgFileType,) =' . " ($MwVar,$ImgFileName,@ImgFileType,)\n";
			}
		}

		use File::Basename;
		my $CurrScriptPath = (fileparse($0, qw/\.exe \.com \.pl/))[1];
		$CurrScriptPath =~ s#(\\|/)$##;
		push @SearchImagePath,$CurrScriptPath;
		#
		my @TmpPath;
		if ( defined $ENV{HOME} ){
			push @TmpPath,
			"$ENV{HOME}/.genesis/scripts/Image/Ico",
			"$ENV{HOME}/.incam/scripts/Image/Ico",

			;
		}
		if ( defined $ENV{GENESIS_DIR} ){
			push @TmpPath,
			"$ENV{GENESIS_DIR}/sys/scripts/Image/Ico",

			;
		}
		if ( defined $ENV{INCAM_SITE_DATA_DIR} ){
			push @TmpPath,
			"$ENV{INCAM_SITE_DATA_DIR}/scripts/Images/Ico",

			;
		}
		for my $tPath ( @TmpPath ){
			if ( -e $tPath ){
				push @SearchImagePath,$tPath;
			}
		}
		#
		for my $tImgFileType ( @ImgFileType ) {
			for my $tSearchImagePath ( @SearchImagePath ) {
				my $tFile = $tSearchImagePath . '/' . $ImgFileName . '.' . $tImgFileType ;
				$tFile  =~ s#\\#/#g ;
				if ( -e $tFile ) {
#					($tImageFile = $tFile) =~ s#\\#/#g;
					$tImageFile = $tFile;
					$LastImgFileType = lc($tImgFileType);
					last;
				}
			}
		}
		#
		if ( $tMode eq 'SetMwLogo' ) {
			if ( $^O =~ /^MSWin/i ) {
				if ( "$tImageFile" =~ /\.ico$/ ) {
					$MwVar->g_wm_iconbitmap( "$tImageFile" );
				} else {
					if ( "$tImageFile" !~ /(\.ico)$/) {
						Tkx::package_require("img::$LastImgFileType");
						Tkx::wm_iconphoto($MwVar, "-default", Tkx::image_create_photo(-file => $tImageFile, -format => "$LastImgFileType"));
					}
				}
			#\} elsif ( $^O =~ /^linux/i ) {
			} else {
				if ( "$tImageFile" ne "" ) {
					Tkx::package_require("img::$LastImgFileType");
					Tkx::wm_iconphoto($MwVar, "-default", Tkx::image_create_photo(-file => $tImageFile, -format => "$LastImgFileType"));
				}
			}
		} else {
			if ( "$tImageFile" ne "" ) {
				Tkx::package_require("img::$LastImgFileType");
				my $ImgInnerName = "TmpImage" . int( rand(9999) );
				Tkx::image_create_photo("$ImgInnerName",-file => $tImageFile, -format => "$LastImgFileType");
				#Tkx::image_delete(@photos);
				return ($ImgInnerName);
			}
		}
	} elsif ( $tMode eq 'GetImg' ) {  # &GetImageFile('GetImg',$ImgFileName,@SearchImagePath)
		$ImgFileName = shift ;
		@ImgFileType = qw /png xpm gif bmp jpg jpeg ico xbm tiff raw ppm sun pcx ps tga pixmap dted sgi/;
		@SearchImagePath = @_ ;
		for my $tImgFileType ( @ImgFileType ) {
			for my $tSearchImagePath ( @SearchImagePath ) {
				my $tFile = $tSearchImagePath . '/' . $ImgFileName . '.' . $tImgFileType ;
				$tFile  =~ s#\\#/#g ;
				if ( -e $tFile ) {
					$tImageFile = $tFile;
					$LastImgFileType = lc($tImgFileType);
					if ( $LastImgFileType eq 'jpg' ) {
						$LastImgFileType = 'jpeg';
					}
					Tkx::package_require("img::$LastImgFileType");
					my $ImgInnerName = "TmpImage" . int( rand(9999) );
					Tkx::image_create_photo("$ImgInnerName",-file => $tImageFile, -format => "$LastImgFileType");
					#Tkx::image_delete(@photos);
					return ($ImgInnerName);
					last;
				}
			}
		}
	}
	return ();
}

