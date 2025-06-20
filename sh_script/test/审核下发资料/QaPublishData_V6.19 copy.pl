#!c:/perl/bin/perl -w
#QaPublishData
#检查组下发资料
use POSIX qw(strftime);
use Win32::API;
use Encode;
use Encode qw/from_to/;

use Tk;
require Tk::LabFrame;
require Tk::Table;

use File::Find;
use File::Basename;
use File::Copy;
use File::Copy::Recursive qw(fcopy rcopy dircopy fmove rmove dirmove);
use File::Path qw(make_path remove_tree);

use Digest::file qw(digest_file_hex);
use Digest::MD5 ;
use DBI;
##################################
# !!!!!! 文件夹复制需要先创建文件夹 CAM QA 检查组没有权限重命名文件夹 !!!!!!!

# --加载自定义公用pm
use lib "//192.168.2.33/incam-share/incam/genesis/sys/scripts/Package_HDI";
use VGT_Oracle;

# --接收到外部传入的参数（inner、outer、all），用于匹配显示对应的下发按钮功能（主要针对审核guide用）
my $showType = $ARGV[0] || undef;

# --开始启动项
BEGIN
{
    # --实例化对象
    our $o = new VGT_Oracle();
    
    # --连接ERP oracle数据库
    our $dbc_e = $o->CONNECT_ORACLE('host'=>'172.20.218.247', 'sid'=>'topprod1', 'port'=>'1521', 'user_name'=>'zygc', 'passwd'=>'ZYGC@2019');
    
    if (! $dbc_e)
    {
        &Messages('warning', '"ERP数据库"连接失败-> 程序终止!');
        exit(0);
    }
    
    # --连接INPLAN oracle数据库
    our $dbc_p = $o->CONNECT_ORACLE('host'=>'172.20.218.193', 'service_name'=>'inmind.fls', 'port'=>'1521', 'user_name'=>'GETDATA', 'passwd'=>'InplanAdmin');
    
    if (! $dbc_p)
    {
        &Messages('warning', '"INPLAN数据库"连接失败-> 程序终止!');
        exit(0);
    }

}

# --结束启动项
END
{
    # --断开Oracle连接
    $dbc_e->disconnect if ($dbc_e);
    
    $dbc_p->disconnect if ($dbc_p);
}

my $Sys_name = $^O;
if ($Sys_name =~ /MSWin32/){
    print $ENV{'USERNAME'},"\n";
    our $RunMode = ($ENV{'USERNAME'} =~ /(84310)|(44839)|(52400)/) ? 'test' : 'formal';
}else {
    if($Sys_name =~ /linux/){
        print $ENV{'USER'},"\n";
        our $RunMode = 'test' ;
    }else{
        print "Unknow\n";
    }
}

##################################
my $SiteCode = 'hz_hdi'; # --惠州HDI工程
our ($MySqlProcess,$MySqlExecute);
our ($org_code, $SourceDataRootPath,$DestDataRootPath);

if ( $RunMode eq 'formal' ) {
    # --南通HDI下发的地址
    if ($SiteCode =~ /^nt_hdi$/i){
        $SourceDataRootPath = '//172.28.30.9/ntsh$/工程';
    # --惠州HDI下发的地址
    }elsif($SiteCode =~ /^hz_hdi$/i){
        $SourceDataRootPath = '//192.168.2.57';
    }
    $DestDataRootPath = '//192.168.2.174'; # --HDI事业部文件服务器
    $BackupDataPath = '//192.168.2.172';
} elsif ( $RunMode eq 'test' ) {
    if ($ENV{'USERNAME'} =~ /(84310)|(44839)|(52400)/) {
        $SourceDataRootPath = 'D:/Test/Source';
        $DestDataRootPath = 'D:/Test/Dest';
        $BackupDataPath = 'D:/Test/Backup';
        #my $text_mea = decode('utf8',"H70506GI296B2 料号存在蚀刻周期,禁止下发LDI资料!");
        #&Messages('warning', $text_mea);
    }else{
        #$SourceDataRootPath = '//192.168.2.57';
        $SourceDataRootPath = '//172.28.30.9/ntsh$/工程';
        $DestDataRootPath = '//192.168.2.174'; # --HDI事业部文件服务器
        $BackupDataPath = '//192.168.2.172';
    }
}

my $appVersion = '版本：V6.19'.$RunMode;
if ($SiteCode =~ /^nt_hdi$/i){
    $org_code = '南通 to HDI';
}elsif($SiteCode =~ /^hz_hdi$/i){
    $org_code = 'HDI';
}
# --打印相关信息
print &Utf8_Gbk("工具自动下发程式启动...\n");
print &Utf8_Gbk("事业部        ：$org_code \n当前运行环境  ：$RunMode \n$appVersion\n\n");

our %StatusConv = (
    'Yes'=>'已下发',
    'Err' =>'复制出现异常',
    'Not' =>'没有资料',
    'NotSel' =>'未勾选',
    'BanInkJet' =>'不允许喷墨',
);

our %StatusColor = (
    'Yes'=>'yellowgreen',
    'Err' =>'red',
    'Not' =>'red',
);

# --下发结果窗体的宽度
our $HeadNoteWidth = 23; 
our $HeadFileWidth = 28;
our $HeadStatWidth = 12;
our $HeadPathWidth = 70;

#$DataInfoLog{List} #发放列表
#$DataInfoLog{'Log'} #发放记录
#my $tFeatures = "yk";
#my $tFeaturesFile = "$tmp.$tFeatures";
#push (@{$DataInfoLog{List}},$tFeatures);
#$DataInfoLog{'Log'}{$tFeatures}{'Name'} = "工程辅助资料($tFeatures)";
#$DataInfoLog{'Log'}{$tFeatures}{'File'} = "$tFeaturesFile";
#$DataInfoLog{'Log'}{$tFeatures}{'Status'} = $StatusConv{Yes};
#$DataInfoLog{'Log'}{$tFeatures}{'Color'} = $StatusColor{Yes};

# --初始化型号名
my $JOB=$ENV{JOB} || undef; 

{ #主程序
    # our $images_path = "z:/incam/server/site_data/scripts/script_sh/images";
    our $images_path = dirname($0)."/images";
    our $username = Win32::LoginName();
    chomp($username);

    our $mw = MainWindow->new( -title =>_Utf8('下发资料'));
    $mw->protocol("WM_DELETE_WINDOW", \&aOnQuit);
    #$mw->geometry("285x486+20+100");
    $mw->geometry("285x486+600+200");
    $mw->resizable(0,0);
    $mw->update;
    Win32::API->new("user32","SetWindowPos",[qw(N N N N N N N)],'N')->Call(hex($mw->frame()),-1,0,0,0,0,3);
    $mw->update;
    Win32::API->new("user32","SetWindowPos",[qw(N N N N N N N)],'N')->Call(hex($mw->frame()),-2,0,0,0,0,3);
    my $sh_log_frm = $mw->Frame(-bg => '#9BDBDB',-borderwidth =>2,-relief => "raised",-height => 5)->pack(-side=>'top',-fill=>'both');

    my $sh_log = $sh_log_frm->Photo('info',-file => "$images_path/sh_log.xpm");
    my $image_label = $sh_log_frm->Label(-image => $sh_log, -border => 0, -relief => 'solid',)->pack(-side => 'left',-padx => 5,-pady => 5);

    $sh_log_frm->Label(-text => _Utf8("HDI审核资料下发"),-font => 'charter 18 bold',-bg => '#9BDBDB')->pack();
    $sh_log_frm->Label(-text => _Utf8("版权:胜宏科技  $appVersion"),-font => 'charter 10',-bg => '#9BDBDB')->pack(-side=>'right', -padx => 10);
    my $tab_frm = $mw->LabFrame(-label => _Utf8("参数选择"),-font => 'SimSun 10',-bg => '#9BDBDB',-fg => 'blue',)->pack(-side=>'top',-fill=>'both');
    my $all_sel_frm = $tab_frm->Frame(-bg => '#9BDBDB')->pack(-side=>'top',-fill=>'both');
    our $set_pm_tmp = "0";
    my $pm_sel_frm = $all_sel_frm->Checkbutton(-text => _Utf8(" 喷墨资料"),-variable    => \$set_pm_tmp,-font => 'SimSun 12',-bg => '#9BDBDB',)->pack(-side => 'left', -padx => 5,-pady => 2);

    my $sel_frm = $mw->Frame(-bg => '#9BDBDB')->pack(-side=>'top',-fill=>'both');
    my $sel_name_frm = $sel_frm->Frame(-bg => '#9BDBDB')->pack(-side=>'left',-fill=>'both');
    our $add_name_frm = $sel_name_frm->Scrolled('Text',-insertborderwidth=>1,-scrollbars=>'e',-font => 'charter 12',-highlightthickness=>2,-insertwidth=>10,-exportselection=>0,-background=>'white',-spacing1=> 3,-spacing2=> 3,-width=> 17,-height=> 18,-selectbackground=>'grey',-selectforeground=>'blue')->pack(-side=>'top',-pady => 2 );
    
    if (defined $JOB)
    {
        $add_name_frm->insert('end',$JOB);
    }else{        
        $add_name_frm->insert('end',_Utf8("在此输入一个料号名."));
    }
    #if ($RunMode eq 'test') {
    #    $add_name_frm->delete('1.0',"end");
    #    #$add_name_frm->insert('end',"h60708gb191a1");
    #}
    $add_name_frm->bind('<Button-1>',\&update_sel_frm);
    $add_name_frm->bind('<Button-2>',\&update_sel_frm);
    $add_name_frm->bind('<Button-3>',\&update_sel_frm);
    our $sel_but_frm     = $sel_frm->Frame(-bg => '#9BDBDB')->pack(-side=>'left',-fill=>'both');
    
    if (not defined $showType or lc($showType) eq 'inner')
    {        
        my $sel_inn_frm     = $sel_but_frm->Button(-text => _Utf8("内层资料"),        -command => sub {&HandOut_InnData("inner");},    -width => 12,-activebackground=>'green',-bg => '#9BDBDB',-font=> 'charter 10 bold',-height=> 2,)->pack(-side => 'top',-fill=>'y',-padx => 15,-pady => 8 );
    }
    if (not defined $showType or lc($showType) eq 'outer')
    { 
        my $sel_out_frm     = $sel_but_frm->Button(-text => _Utf8("外层资料"),        -command => sub {&HandOut_OutData;},    -width => 12,-activebackground=>'green',-bg => '#9BDBDB',-font=> 'charter 10 bold',-height=> 2,)->pack(-side => 'top',-fill=>'y',-padx => 15,-pady => 8 );
    }
    if (not defined $showType or lc($showType) eq 'all'){       
        my $sel_all_frm     = $sel_but_frm->Button(-text => _Utf8("全套资料"),        -command => sub {&HandOut_AllData;},    -width => 12,-activebackground=>'green',-bg => '#9BDBDB',-font=> 'charter 10 bold',-height=> 2,)->pack(-side => 'top',-fill=>'y',-padx => 15,-pady => 8 );
    }
    my $del_all_frm     = $sel_but_frm->Button(-text => _Utf8("清空输入"),        -command => sub {&ClearListText;},    -width => 12,-activebackground=>'green',-bg => '#9BDBDB',-font=> 'charter 10 bold',-height=> 2,)->pack(-side => 'top',-fill=>'y',-padx => 15,-pady => 8 );
    #my $del_old_frm     = $sel_but_frm->Button(-text => _Utf8("删除旧资料"),      -command => sub {&DelHandOutOldData;},    -width => 12,-activebackground=>'red',-bg => '#9BDBDB',-font=> 'charter 10 bold',-height=> 2,)->pack(-side => 'top',-fill=>'y',-padx => 15,-pady => 8 );
    my $save_file_frm = $sel_but_frm->Button(-text => _Utf8("只归档资料"),        -command => sub {&BackupCAMData;},    -width => 12,-activebackground=>'green',-bg => '#9BDBDB',-font=> 'charter 10 bold',-height=> 2,)->pack(-side => 'top',-fill=>'y',-padx => 15,-pady => 8 );

    my $b_close = $sel_but_frm->Button(-text=> _Utf8("退出"),-activebackground=>'red',-height => 2, -bg => '#9BDBDB',-font=> 'charter 10 bold',-width=>'12',-command=>sub{exit 0;})->pack(-side=>'bottom',-padx=>15,-pady=>8);

    MainLoop;
}



###########################################################################################################################################################
###############################################################  华丽的分隔线  ############################################################################
###########################################################################################################################################################
#/****************************
# 函数名: HandOut_InnData
# 功  能: 下发内层资料数据逻辑方法
# 参  数: None
# 返回值: 执行结果界面
#****************************/
sub HandOut_InnData
{
	$showType=shift;
	
    &RunNewVerScript;
    my %DataInfoLog;
    my %RecordHandOut;
    
    my $name_list = $add_name_frm->get("1.0","end");
    my @output_name_list = split(/\n/,$name_list);
    if ( &JobNameCheck($sel_but_frm,@output_name_list) eq 'no' ) {
        return;
    }

    if ( $set_pm_tmp eq 1 ) {
        &iTkMwMsg($mw,_Utf8("警告","warning","ok","内层下发资料不要勾选喷墨,请重新选择!"),);
        return ('no');
    }
    foreach my $tJob (@output_name_list) {
        $tJob =lc($tJob);
        $tmp =lc($tJob);
        my $layer_no = substr($tmp, 4,2);
        if ( $layer_no < 4 ) {
            &iTkMwMsg($mw,_Utf8("警告","warning","ok","层数小于4层的板不用下发内层资料!"),);
            return ('no');
        }
        my %tPath = &getHandOutPath("$tJob"); #获取通用路径及变量
        
        # --内层AOI tgz      ---OK  
        { 
            my $tKeyName = '-inn.tgz';
            &HandOutActSub('Copy', # Copy Move Copys Moves
            \%DataInfoLog,\%RecordHandOut,
            $tKeyName,
            "内层AOI扫描tgz",
            $tJob,
            $tJob . '-inn.tgz' ,
            &Utf8_Gbk( $tPath{TempJobVer} ),
            &Utf8_Gbk( $tPath{InnTgzFormalCustomer} ),
            );
        }
        
        # --内层LDI资料输出   ---OK
        {
            # --定义内层超始层
            my $innStart = 2;
            my $innEnd = $layer_no - 1;
            # --定义匹配内层的正则
            my $matchStr = "";
            for ($innStart .. $innEnd)
            {
                if ($_ != $innEnd)
                {
                    $matchStr .= 'l'.$_.'|'
                }else{
                    $matchStr .= 'l'.$_
                }               
            }
            # --兼容旧的2.0Mic精度工具存储方式
            if (-d &Utf8_Gbk("$tPath{TempJobVer}/LDI_2.0Micron"))
            {
                # --下发
                my $tKeyName = "LDI_2_0Mic";
                &HandOutActSub('Copys', # Copy Move Copys Moves
                \%DataInfoLog,\%RecordHandOut,
                'LDI' . $tKeyName,
                "内层LDI资料($tKeyName)",
                $tJob,
                '^' . $tJob . '(\.|\@)(' . $matchStr. ')$' ,
                &Utf8_Gbk( $tPath{TempJobVer}."/LDI_2.0Micron" ),
                &Utf8_Gbk( $tPath{OrbLdiJob} ),
                ); 
            }else{
                # --下发
                my $tKeyName = "LDI_2_0Mic";
                &HandOutActSub('Copys', # Copy Move Copys Moves
                \%DataInfoLog,\%RecordHandOut,
                'LDI' . $tKeyName,
                "内层LDI资料($tKeyName)",
                $tJob,
                '^' . $tJob . '(\.|\@)(' . $matchStr. ')$' ,
                &Utf8_Gbk( $tPath{TempJobVer} ),
                &Utf8_Gbk( $tPath{OrbLdiJob} ),
                ); 
            }
            
            # --下发1.5Micron精度资料
            my $tKeyName = "LDI_1_5Mic";
            &HandOutActSub('Copys', # Copy Move Copys Moves
            \%DataInfoLog,\%RecordHandOut,
            'LDI' . $tKeyName,
            "内层LDI资料($tKeyName)",
            $tJob,
            '^' . $tJob . '(\.|\@)(' . $matchStr. ')$' ,
            &Utf8_Gbk( $tPath{TempJobVer}."/LDI_1.5Micron" ),
            &Utf8_Gbk( $tPath{OrbLdi_80FJob} ),
            );             
        }         
        # === 辅助层别的下发 料号名@L数字-数字.fz
		        # --内层LDI资料输出   ---OK
        {
            # --定义内层超始层
            my $innStart = 1;
            my $innEnd = $layer_no;
            # --定义匹配内层的正则
            my $matchStr = "";
            for ($innStart .. $innEnd)
            {
                if ($_ != $innEnd)
                {
                    $matchStr .= 'l'.$_.'|'
                }else{
                    $matchStr .= 'l'.$_
                }               
            }
            # --兼容旧的2.0Mic精度工具存储方式

			# --下发
			my $ldi_source_path=&Utf8_Gbk( $tPath{TempJobVer} );
			if (-d &Utf8_Gbk("$tPath{TempJobVer}/LDI_2.0Micron")){
				$ldi_source_path=&Utf8_Gbk("$tPath{TempJobVer}/LDI_2.0Micron");
			}
			my $tKeyName = "FZ_2_0Mic";
			&HandOutActSub('Copys', # Copy Move Copys Moves
			\%DataInfoLog,\%RecordHandOut,
			'LDI' . $tKeyName,
			"内层辅助层LDI资料($tKeyName)",
			$tJob,
			'^' . $tJob . '(\.|\@)(' . $matchStr. ')-.+\.fz$' ,
			$ldi_source_path,
			&Utf8_Gbk( $tPath{OrbLdiJob} ),
			); 

            # --下发1.5Micron精度资料
            $tKeyName = "FZ_1_5Mic";
            &HandOutActSub('Copys', # Copy Move Copys Moves
            \%DataInfoLog,\%RecordHandOut,
            'LDI' . $tKeyName,
            "内层辅助层LDI资料($tKeyName)",
            $tJob,
            '^' . $tJob . '(\.|\@)(' . $matchStr. ')-.+\.fz$' ,
            &Utf8_Gbk( $tPath{TempJobVer}."/LDI_1.5Micron" ),
            &Utf8_Gbk( $tPath{OrbLdi_80FJob} ),
            );             
        }    
		
        # --盖孔减铜LDI资料 增加镀孔菲林
        {
            # --定义内层超始层
            my $innStart = 2;
            my $innEnd = $layer_no - 1;
            # --定义匹配内层的正则
            my $matchStr = "";
            for ($innStart .. $innEnd)
            {
                if ($_ != $innEnd)
                {
                    $matchStr .= 'l'.$_.'|'
                }else{
                    $matchStr .= 'l'.$_
                }               
            }
            # --兼容旧的2.0Mic精度工具存储方式
			
            # --下发
			my $ldi_source_path=&Utf8_Gbk( $tPath{TempJobVer} );
			if (-d &Utf8_Gbk("$tPath{TempJobVer}/LDI_2.0Micron")){
				$ldi_source_path=&Utf8_Gbk("$tPath{TempJobVer}/LDI_2.0Micron");
			}
            my $tKeyName = "LDI_GK/DK2.0Micron";
            &HandOutActSub('Copys', # Copy Move Copys Moves
            \%DataInfoLog,\%RecordHandOut,
            'LDI' . $tKeyName,
            "盖孔减铜(镀孔)LDI资料($tKeyName)",
            $tJob,
            '^' . $tJob . '(\.|\@)(' . $matchStr. ')-(.+)?(g|d)k$' ,
            $ldi_source_path ,
            &Utf8_Gbk( $tPath{OrbLdiJob} ),
            ); 
			
			my $tKeyName = "LDI_GK/DK1.5Micron";
            &HandOutActSub('Copys', # Copy Move Copys Moves
            \%DataInfoLog,\%RecordHandOut,
            'LDI' . $tKeyName,
            "盖孔减铜(镀孔)LDI资料($tKeyName)",
            $tJob,
            '^' . $tJob . '(\.|\@)(' . $matchStr. ')-(.+)?(g|d)k$' ,
            &Utf8_Gbk( $tPath{TempJobVer}."/LDI_1.5Micron" ),
            &Utf8_Gbk( $tPath{OrbLdi_80FJob} ),
            ); 
        }
		
        # --裁磨线资料下发
        {
            my $tKeyName = 'cmtools';
            &HandOutActSub('Copys', # Copy Move Copys Moves
            \%DataInfoLog,\%RecordHandOut,
            $tKeyName,
            "裁磨线资料($tKeyName)",
            $tJob,
            $tJob,
            &Utf8_Gbk( $tPath{TempJobVer}."/Pnl_Rout". "/$tJob"),
            &Utf8_Gbk( $tPath{CmJob} ),
            );
        }  
        # --长7短5涨缩测量数据
        {
            my $tKeyName = 'csv';
            &HandOutActSub('Copys', # Copy Move Copys Moves
            \%DataInfoLog,\%RecordHandOut,
            $tKeyName,
            "长7短5涨缩测量数据($tKeyName)",
            $tJob,
            'YH_PY_Cor',
            &Utf8_Gbk( $tPath{TempJobVer}),
            &Utf8_Gbk( $tPath{ScaleJob} ),
            );
        }  

        # --X-ray测量数据
        {
            my $tKeyName = 'Xray';
            &HandOutActSub('Copys', # Copy Move Copys Moves
            \%DataInfoLog,\%RecordHandOut,
            $tKeyName,
            "X-RAY测量数据($tKeyName)",
            $tJob,
            '^' . $tJob . '-?(.+)?ix$',
            &Utf8_Gbk( $tPath{TempJobVer}),
            &Utf8_Gbk( $tPath{XrayJob} ),
            );
        }  
        
        # --盲孔钻带    ---OK 
        # {
        #     my $tKeyName = "write";
        #     &HandOutActSub('Copys', # Copy Move Copys Moves
        #     \%DataInfoLog,\%RecordHandOut,
        #     'MkDrl' . $tKeyName,
        #     "盲孔转档程式($tKeyName)",
        #     $tJob,
        #     '^' . $tJob . '.+\.write$' ,
        #     &Utf8_Gbk( $tPath{TempJobVer} ),
        #     &Utf8_Gbk( $tPath{MkJob} ),
        #     );
        #     # --有镭射的料号，不需要放inn和out，只放镭射层，通孔才放inn和out
        #     # print "AAAA:" . &Utf8_Gbk($DataInfoLog{'Log'}{"MkDrl".$tKeyName}{'Status'}) . "\n";
        #     # print "BBBB:" . &Utf8_Gbk($StatusConv{'Not'}). "\n";
        #     our $outDrl = ($DataInfoLog{'Log'}{"MkDrl".$tKeyName}{'Status'} eq $StatusConv{'Not'}) ? 'yes' : 'no';
        # }
        
        # --通孔钻带       ---OK 
        {                         
            my $tKeyName = "drl";
            &HandOutActSub('Copys', # Copy Move Copys Moves
            \%DataInfoLog,\%RecordHandOut,
            'Drl' . $tKeyName,
            "辅助通孔钻带程式($tKeyName)",
            $tJob,
            '^' . $tJob . '\.(inn|out|drl)$' ,
            &Utf8_Gbk( $tPath{TempJobVer} ),
            &Utf8_Gbk( $tPath{AidSimpleJob} ),
            );
        }        
        
        # --其它所有辅助工具 # ^(?:h60708gb191a1.(?:b.+|d.+|inn\d+|lp.+|rout.+|s.+|ww|sz.+)|w(?:.+)?)$  ---OK
        {
            my $tKeyName = "otherDrl";
            &HandOutActSub('Copys', # Copy Move Copys Moves
            \%DataInfoLog,\%RecordHandOut,
            'oDrl' . $tKeyName,
            "其它辅助程式($tKeyName)",
            $tJob,
            # '^((?:'.$tJob.'\.(?:b.+|d.+|inn\d+|lp(?:.+)?|rout(?:.+)?|s.+|ww|sz(?:.+)?|cd(-)?(c|s)(.+)?|tk\.ykj|lr\d+-\d+|2nd(.+)?))|(w(?:.+)?|sz.+xm|KS.+dq))$',
            '^(('.$tJob.'\.(b.+|d.+|inn(-)?(\d+)?(-pp)?|lp(.+)|rout(.+)?|s.+|ww|sz(.+)?|cd(-)?(c|s)(.+)?|tk\.ykj|lr\d+-\d+|2nd(.+)?))|(sz.+xm|KS.+dq))$',
            #'^(' . $tJob . '(b.+|d.+|inn\d+|lp.+|rout.+|s.+|ww|sz.+)'.'|w.+)$' ,
            &Utf8_Gbk( $tPath{TempJobVer} ),
            &Utf8_Gbk( $tPath{AidSimpleJob} ),
            );
        }
		if (-d &Utf8_Gbk("$tPath{TempJobVer}/uv-laser"))
		{
            my $tKeyName = 'uv_laser';
            &HandOutActSub('Copys', # Copy Move Copys Moves
            \%DataInfoLog,\%RecordHandOut,
            $tKeyName,
            "其它辅助程式($tKeyName)",
            $tJob,
            "uv-laser",
            &Utf8_Gbk( $tPath{TempJobVer}),
            &Utf8_Gbk( $tPath{AidSimpleJob} ),
            );
        }
        # --上传LOG信息至数据库
        &UploadLogToMySql("inner",$tPath{vuJob},$RecordHandOut{SimpleLog},$RecordHandOut{FullLog},); # inner outer all backup delete
        
        # --上传工具下发记录
        &uploadToolsIssue($tPath{vuJob});
        
        # --上传工程订单内层审核完成时间
        &uploadTime($tPath{vuJob}, 'icheckfinish_time')
    }
	
	if ($showType eq "inner"){
		# --归档（移走临时目录下所有资料到2.33）
		&BackupCAMData('Hide');
	}
	
    # --显示最终下发结果信息
    &showXFresult(\%DataInfoLog);
	
	#内层下发后 清楚状态 20240311 by lyh
	$showType = undef;
}

#/****************************
# 函数名: HandOut_OutData
# 功  能: 下发外层资料数据逻辑方法
# 参  数: None
# 返回值: 执行结果界面
#****************************/
sub HandOut_OutData 
{
    &RunNewVerScript;
    my %DataInfoLog;
    my %RecordHandOut;
    my $name_list = $add_name_frm->get(   "1.0","end");
    my @output_name_list = split(/\n/,$name_list);
    # --检测是否有输入正确的型号名
    if ( &JobNameCheck($sel_but_frm,@output_name_list) eq 'no' ) {
        return;
    }
	
	my $find_dir;
	
    foreach my $tJob (@output_name_list) {
        $tJob =lc($tJob);
        my $tmp =lc($tJob);
        my $layer_no = substr($tmp, 4,2)*1;
        my %tPath = &getHandOutPath("$tJob"); #获取通用路径及变量
		
		#检测是否漏输出lp md1 md2资料 20231128 by lyh
		#http://192.168.2.120:82/zentao/story-view-6261.html
		{			
			if (not -e Utf8_Gbk("$tPath{TempJobVer}". '/'.'md1'))
            {
                &iTkMwMsg($mw,_Utf8("提示","info","ok",$tPath{TempJobVer}. '/'.'md1'."文件不存在，请反馈CAM是否漏输出!",));
            }
			if (not -e Utf8_Gbk("$tPath{TempJobVer}". '/'.'md2'))
            {
                &iTkMwMsg($mw,_Utf8("提示","info","ok",$tPath{TempJobVer}. '/'.'md2'."文件不存在，请反馈CAM是否漏输出!",));
            }
			if (not -e Utf8_Gbk("$tPath{TempJobVer}". '/'.$tJob.'.lp'))
            {
                &iTkMwMsg($mw,_Utf8("提示","info","ok",$tPath{TempJobVer}. '/'.$tJob.'.lp'."文件不存在，请反馈CAM是否漏输出!",));
            }
		}

        # --外层全套tgz    ---OK
        {
            # --先判断目标地址下的内层AOI tgz资料是否存在（-inn.tgz结尾）
            if (-e Utf8_Gbk("$tPath{TgzFormalCustomer}". '/'. $tJob.'-inn.tgz'))
            {
                unlink Utf8_Gbk("$tPath{TgzFormalCustomer}". '/'. $tJob.'-inn.tgz');
            }
            # --执行全套tgz的拷贝
            my $tKeyName = 'tgz';
            &HandOutActSub('Copy', # Copy Move Copys Moves
            \%DataInfoLog,\%RecordHandOut,
            $tKeyName,
            "HDI全套Tgz",
            $tJob,
            "$tJob.$tKeyName",
            &Utf8_Gbk( $tPath{TempJobVer} ),
            &Utf8_Gbk( $tPath{TgzFormalCustomer} ),
            );
        }
        
        # --通孔钻带       ---OK 
        {
            my $tKeyName = "inn";
            &HandOutActSub('Copys', # Copy Move Copys Moves
                \%DataInfoLog,\%RecordHandOut,
                'Drl' . $tKeyName,
                "通孔钻孔程式($tKeyName)",
                $tJob,
                '^' . $tJob . '\.(inn|out|drl)$' ,
                &Utf8_Gbk( $tPath{TempJobVer} ),
                &Utf8_Gbk( $tPath{AidSimpleJob} ),
                );
            ## --双面板多放一个位置见需求：http://192.168.2.120:82/zentao/story-view-3385.html
            #if ($layer_no <=2){
            #    my $tKeyName = "inn_2";
            #    &HandOutActSub('Copys', # Copy Move Copys Moves
            #        \%DataInfoLog,\%RecordHandOut,
            #        'Drl' . $tKeyName,
            #        "通孔钻孔程式($tKeyName)",
            #        $tJob,
            #        '^' . $tJob . '\.(inn|out|drl)$' ,
            #        &Utf8_Gbk( $tPath{TempJobVer} ),
            #        &Utf8_Gbk( $tPath{MecJob} ),
            #        );
            #}
        }

        # --其它所有辅助工具 # 薛岩弟要求：外层备份 料号名.lp 也要放到辅助里，统一再放一下   料号名.* 到辅助 CDS CDC 控深钻 SZ23.DQ是埋孔树脂导气板
        # --SZ23.XM是埋孔树脂网板 WW1是一次成型
        {
            my $tKeyName = "otherDrl";
            &HandOutActSub('Copys', # Copy Move Copys Moves
                \%DataInfoLog,\%RecordHandOut,
                'oDrl' . $tKeyName,
                "其它辅助程式($tKeyName)",
                $tJob,
                # '^((?:'.$tJob.'\.(?:b.+|d.+|inn\d+|lp(?:.+)?|rout(?:.+)?|s.+|ww(.+)?|sz(?:.+)?|w(?:.+)?|cd(-)?(c|s)(.+)?|))|(sz.+xm|KS.+dq))$',
                '^((?:'.$tJob.'\.(?:b.+|d.+|inn\d+|lp(?:.+)?|rout(?:.+)?|s.+|ww(.+)?|sz(?:.+)?|w(?:.+)?|cd(-)?(c|s)(.+)?|))|(sz.+xm|KS.+dq))$',
                #'^(' . $tJob . '(b.+|d.+|inn\d+|lp.+|rout.+|s.+|ww|sz.+)'.'|w.+)$' ,
                &Utf8_Gbk( $tPath{TempJobVer} ),
                &Utf8_Gbk( $tPath{AidSimpleJob} ),
                );
            ## --双面板多放一个位置见需求：http://192.168.2.120:82/zentao/story-view-3385.html
            #if ($layer_no <=2){
            #    my $tKeyName = "otherDrl_2";
            #    &HandOutActSub('Copys', # Copy Move Copys Moves
            #        \%DataInfoLog,\%RecordHandOut,
            #        'oDrl' . $tKeyName,
            #        "其它辅助程式($tKeyName)",
            #        $tJob,
            #        # '^((?:'.$tJob.'\.(?:b.+|d.+|inn\d+|lp(?:.+)?|rout(?:.+)?|s.+|ww(.+)?|sz(?:.+)?|w(?:.+)?|cd(-)?(c|s)(.+)?|))|(sz.+xm|KS.+dq))$',
            #        '^((?:'.$tJob.'\.(?:b.+|d.+|inn\d+|lp(?:.+)?|rout(?:.+)?|s.+|ww(.+)?|sz(?:.+)?|w(?:.+)?|cd(-)?(c|s)(.+)?|))|(sz.+xm|KS.+dq))$',
            #        #'^(' . $tJob . '(b.+|d.+|inn\d+|lp.+|rout.+|s.+|ww|sz.+)'.'|w.+)$' ,
            #        &Utf8_Gbk( $tPath{TempJobVer} ),
            #        &Utf8_Gbk( $tPath{MecJob} ),
            #        );
            #}
        }
        
        # --外层LDI资料输出   ---No
        {
            # --WB6908OB072F1 防焊周期
            # --N60104SI060B1 蚀刻周期
            # --当外层是蚀刻周期时,禁止下发  AresHe 2022.3.1
            # --来源需求:http://192.168.2.120:82/zentao/story-view-3981.html
            my $week_format = &getWeekFromat($dbc_p, uc($tJob));
            print ("\$week_format $week_format\n");
            my $shike = &Utf8_Gbk("蚀刻");
            if ($week_format !~ /$shike/) {
                # --兼容旧的2.0Mic精度工具存储方式
                if (-d &Utf8_Gbk("$tPath{TempJobVer}/LDI_2.0Micron"))
                {
                    my $tKeyName = "LDI_2_0Mic";
                    &HandOutActSub('Copys', # Copy Move Copys Moves
                    \%DataInfoLog,\%RecordHandOut,
                    'LDI' . $tKeyName,
                    "外层LDI资料($tKeyName)",
                    $tJob,
                    '^' . $tJob . '(\.|\@)l(1|'. $layer_no .')$' ,
                    &Utf8_Gbk( $tPath{TempJobVer}."/LDI_2.0Micron" ),
                    &Utf8_Gbk( $tPath{OrbLdiJob} ),
                    );
                }else{
                    my $tKeyName = "LDI_2_0Mic";
                    &HandOutActSub('Copys', # Copy Move Copys Moves
                    \%DataInfoLog,\%RecordHandOut,
                    'LDI' . $tKeyName,
                    "外层LDI资料($tKeyName)",
                    $tJob,
                    '^' . $tJob . '(\.|\@)l(1|'. $layer_no .')$' ,
                    &Utf8_Gbk( $tPath{TempJobVer} ),
                    &Utf8_Gbk( $tPath{OrbLdiJob} ),
                    );
                }
                
                # --下发1.5Micron精度资料
                my $tKeyName = "LDI_1_5Mic";
                &HandOutActSub('Copys', # Copy Move Copys Moves
                \%DataInfoLog,\%RecordHandOut,
                'LDI' . $tKeyName,
                "外层LDI资料($tKeyName)",
                $tJob,
                '^' . $tJob . '(\.|\@)l(1|'. $layer_no .')$' ,
                &Utf8_Gbk( $tPath{TempJobVer}."/LDI_1.5Micron" ),
                &Utf8_Gbk( $tPath{OrbLdi_80FJob} ),
                );
            }else{
                my $text_mea = decode('utf8',"$tJob 料号存在蚀刻周期,禁止下发LDI资料!");
                &Messages('warning', $text_mea);
            }
        }
        # --盖孔减铜LDI资料
        {
            # --下发
			my $ldi_source_path=&Utf8_Gbk( $tPath{TempJobVer} );
			if (-d &Utf8_Gbk("$tPath{TempJobVer}/LDI_2.0Micron")){
				$ldi_source_path=&Utf8_Gbk("$tPath{TempJobVer}/LDI_2.0Micron");
			}
            my $tKeyName = "LDI_GK_2.0Micron";
            &HandOutActSub('Copys', # Copy Move Copys Moves
            \%DataInfoLog,\%RecordHandOut,
            'LDI' . $tKeyName,
            "盖孔减铜(镀孔)LDI资料($tKeyName)",
            $tJob,
            '^' . $tJob . '(\.|\@)l(1|'. $layer_no .')-(g|d)k$' ,
            $ldi_source_path ,
            &Utf8_Gbk( $tPath{OrbLdiJob} ),
            ); 

            my $tKeyName = "LDI_GK_1.5Micron";
            &HandOutActSub('Copys', # Copy Move Copys Moves
            \%DataInfoLog,\%RecordHandOut,
            'LDI' . $tKeyName,
            "盖孔减铜(镀孔)LDI资料($tKeyName)",
            $tJob,
            '^' . $tJob . '(\.|\@)l(1|'. $layer_no .')-(g|d)k$' ,
            &Utf8_Gbk( $tPath{TempJobVer}."/LDI_1.5Micron" ),
            &Utf8_Gbk( $tPath{OrbLdi_80FJob} ),
            ); 
        }
		# --蚀刻引线
        {
			#print "------------>\n";
			my $find_dir = "";
			find(	sub {		
						return unless -f; # 只处理文件	
						my $basefilename = lc(basename($File::Find::name));	
						if ($basefilename =~ /^$tJob(\.|\@)etch-(c|s)$/i) {
							my $full_path = $File::Find::name; # 获取文件的完整路径
							$full_path =~ s{/[^/]*$}{} ; # 获取文件所在的目录路径
							#print "找到文件：$full_path 在目录：$dir_path\n";
							$find_dir = $full_path;
							from_to($find_dir,"gbk","utf8");
						}		
					}, 
					&Utf8_Gbk( $tPath{TempJobVer} ));
			
			my $ldi_source_path=&Utf8_Gbk($find_dir);
			
			#print "------------->,$ldi_source_path,\n";
            my $tKeyName = "LDI_ETCH_2.0Micron";
            &HandOutActSub('Copys', # Copy Move Copys Moves
            \%DataInfoLog,\%RecordHandOut,
            'LDI' . $tKeyName,
            "蚀刻引线LDI资料($tKeyName)",
            $tJob,
            '^' . $tJob . '(\.|\@)etch-(c|s)$' ,
            $ldi_source_path ,
            &Utf8_Gbk( $tPath{OrbLdiJob} ),
            ); 

            my $tKeyName = "LDI_ETCH_1.5Micron";
            &HandOutActSub('Copys', # Copy Move Copys Moves
            \%DataInfoLog,\%RecordHandOut,
            'LDI' . $tKeyName,
            "蚀刻引线LDI资料($tKeyName)",
            $tJob,
            '^' . $tJob . '(\.|\@)etch-(c|s)$' ,
            &Utf8_Gbk( $tPath{TempJobVer}."/LDI_1.5Micron" ),
            &Utf8_Gbk( $tPath{OrbLdi_80FJob} ),
            ); 
        }
        # --执行劲鑫字符打印机资料拷贝
        {
            my $tKeyName = 'JinXin';
            &HandOutActSub('Copy', # Copy Move Copys Moves
            \%DataInfoLog,\%RecordHandOut,
            $tKeyName,
            "劲鑫字符喷墨资料($tKeyName)",
            $tJob,
            "$tJob"."_jinxin.tgz",
            &Utf8_Gbk( $tPath{TempJobVer} ),
            &Utf8_Gbk( $tPath{SilkJinXinCus} ),
            );
        }
		# === 蓝胶下发到辅助
        {
            my $tKeyName = 'Blue';
            &HandOutActSub('Copy', # Copy Move Copys Moves
            \%DataInfoLog,\%RecordHandOut,
            $tKeyName,
            "割蓝胶资料($tKeyName)",
            $tJob,
            "$tJob".".dxf",
			&Utf8_Gbk( $tPath{TempJobVer}."/blue_dxf" ),
			&Utf8_Gbk("//192.168.2.33/vgt\$/设计课/外部资料/工程部外部取读资料/五处镀金割胶机图形/HDI蓝胶代工资料"),
			#&Utf8_Gbk( $tPath{AidSimpleJob}."/blue_dxf" ),
            );
        }
        # --执行外检AVI
        {
            my $tKeyName = 'OuterAVI';
            &HandOutActSub('Copy', # Copy Move Copys Moves
            \%DataInfoLog,\%RecordHandOut,
            $tKeyName,
            "外检AVI资料($tKeyName)",
            $tJob,
            "$tJob"."_outavi.tgz",
            &Utf8_Gbk( $tPath{TempJobVer} ),
            &Utf8_Gbk( $tPath{OuterAVICus} ),
            );
        }
        
        # --喷墨资料  ---No
        {
            my $tKeyName = "InkJet";
            my $tNoteName = "工程辅助资料(喷墨)";

            if ( $set_pm_tmp == 1 ) {
                my @InkJetFindKey = ($tPath{vCustomerCode} . '系列','喷墨','(不|禁止)',);
                my @InkJetCustomerFolderList = &iReadDir ( &Utf8_Gbk( $tPath{InkJet} ) ) ;
                my @InkJetBanFind = @InkJetCustomerFolderList;
                for my $tKey ( &Utf8_Gbk( @InkJetFindKey ) ){
                    @InkJetBanFind = grep( /$tKey/i,@InkJetBanFind );
                }
                if ( scalar(@InkJetBanFind) == 0 ) {
                    my @TempInkJetFindPath;
                    my @FolderList = &ilistFolders('2',&Utf8_Gbk( $tPath{TempJobVer} ));
                    ## @FolderList
                    #查找符合喷墨文件夹命名规则的
                    for my $tFolderList ( @FolderList ) {
                        ## $tFolderList
                        if ( $tFolderList =~ m#/$tJob[^/]*/$tJob[^/]+(top|bot)$#i ) {
                             push (@TempInkJetFindPath,dirname($tFolderList));
                        }

                    }
                    if ( scalar(@TempInkJetFindPath) > 0 ) {
                        @TempInkJetFindPath = &iClearDup(@TempInkJetFindPath);
                        ## @TempInkJetFindPath

                        my $tFindFolder = basename($TempInkJetFindPath[0]);
                        ## $tFindFolder

                        &HandOutActSub('Copy', # Copy Move Copys Moves
                        \%DataInfoLog,\%RecordHandOut,
                        $tKeyName,
                        $tNoteName,
                        $tJob,
                        $tFindFolder ,
                        &Utf8_Gbk( $tPath{TempJobVer} ),
                        &Utf8_Gbk( $tPath{InkJetCustomer} ),
                        );
                    } else {
                        push (@{$DataInfoLog{List}},$tKeyName);
                        $DataInfoLog{'Log'}{$tKeyName}{'Name'} = $tNoteName;
                        $DataInfoLog{'Log'}{$tKeyName}{'File'} = '';
                        $DataInfoLog{'Log'}{$tKeyName}{'Status'} = $StatusConv{Not};
                        $DataInfoLog{'Log'}{$tKeyName}{'Color'} = $StatusColor{Err};
                    }
                } else {
                    push (@{$DataInfoLog{List}},$tKeyName);
                    $DataInfoLog{'Log'}{$tKeyName}{'Name'} = $tNoteName;
                    $DataInfoLog{'Log'}{$tKeyName}{'File'} = '';
                    $DataInfoLog{'Log'}{$tKeyName}{'Status'} = $StatusConv{BanInkJet};
                    $DataInfoLog{'Log'}{$tKeyName}{'Color'} = $StatusColor{Err};
                }
            } else {
                push (@{$DataInfoLog{List}},$tKeyName);
                $DataInfoLog{'Log'}{$tKeyName}{'Name'} = $tNoteName;
                $DataInfoLog{'Log'}{$tKeyName}{'File'} = '';
                $DataInfoLog{'Log'}{$tKeyName}{'Status'} = $StatusConv{NotSel};
                $DataInfoLog{'Log'}{$tKeyName}{'Color'} = $StatusColor{Err};
            }
        }
        
        # --下发镭雕资料
        {
            my $tKeyName = "leidiao";
            &HandOutActSub('Copys', # Copy Move Copys Moves
            \%DataInfoLog,\%RecordHandOut,
            $tKeyName,
            "镭雕资料($tKeyName)",
            $tJob,
            '^' . $tJob . '_(top|bottom)\.txt$' ,
            &Utf8_Gbk( $tPath{TempJobVer} ),
            &Utf8_Gbk( $tPath{LeiDiaoJob} ),
            );
        }
        
        
        # --上传LOG信息至数据库数据库
        &UploadLogToMySql("outer",$tPath{vuJob},$RecordHandOut{SimpleLog},$RecordHandOut{FullLog},); # inner outer all backup delete
        
        # --上传工具下发记录
        &uploadToolsIssue($tPath{vuJob});
        
        # --上传工程订单内层审核完成时间
        &uploadTime($tPath{vuJob}, 'ocheckfinish_time')
    }

    # --归档（移走临时目录下所有资料到2.33）
    &BackupCAMData('Hide');

    # --显示最终下发结果信息
    &showXFresult(\%DataInfoLog);
}
#/****************************
# 函数名: HandOut_AllData
# 功  能: 下发内外层所有资料数据逻辑方法
# 参  数: None
# 返回值: 执行结果界面
#****************************/
sub HandOut_AllData {  #全部
    &RunNewVerScript;
    
    # --下发内层资料
    &HandOut_InnData("all");
    
    # --下发外层资料
    &HandOut_OutData;    
}

#############################################################################################################
sub DelHandOutOldData { #删除旧资料
    &RunNewVerScript;
	
    my %DataInfoLog;
    my %RecordHandOut;
    my $name_list = $add_name_frm->get("1.0","end");
    my @output_name_list = split(/\n/,$name_list);
    if ( &JobNameCheck($sel_but_frm,@output_name_list) eq 'no' ) {
        return;
    }

    if ( &iTkMwMsg($mw,_Utf8("提示","info","yesno","你确定要删除旧资料吗?"),) eq 'no' ) {
        return;
    }

    my $name1 = $output_name_list[0];
    my %tPath = &getHandOutPath( lc($name1) ); #获取通用路径及变量

    my $current_time_yy_tmp = (localtime)[5];
    my $current_time_yy = $current_time_yy_tmp + 1900;
    my $current_time_mm_tmp = (localtime)[4];
    my $current_time_mm = $current_time_mm_tmp + 1;
    my $current_time_dd = (localtime)[3];

    my $del_client_no = substr($name1, 1,3);
    my $del_sh_no = substr($name1, 8,3);

    my $del_inn_path = "$DestDataRootPath/vgt\$/设计课/外部资料/工程部外部取读资料/胜宏资料/内层AOI扫描资料";
    from_to($del_inn_path,"utf8","gbk");
    my @del_yy_dir = &iReadDir($del_inn_path);
    my $del_inn_file_no = 0;
    my @del_inn_file_name = ();
    my @del_inn_file_name_result = ();
    my @del_inn_file_name_path = ();
    foreach my $dir_yy (@del_yy_dir) {
        my $dir_tmp = "年";
        $dir_tmp = decode('utf8',$dir_tmp);
        $dir_tmp = encode('gbk',$dir_tmp);
        if ( $dir_yy =~ /$dir_tmp$/ ) {
            my $del_mm_dir_path = "$del_inn_path/$dir_yy";
            my @del_mm_dir = &iReadDir($del_mm_dir_path);
            foreach my $dir_mm (@del_mm_dir) {
                my $del_dd_dir_path = "$del_inn_path/$dir_yy/$dir_mm";
                my @del_dd_dir = &iReadDir($del_dd_dir_path);
                foreach my $dir_dd (@del_dd_dir) {
                    my $del_job_dir_path = "$del_inn_path/$dir_yy/$dir_mm/$dir_dd";
                    my @del_job_dir = &iReadDir($del_job_dir_path);
                    foreach my $dir_job (@del_job_dir) {
                        if ( $dir_job =~ /$del_client_no/ && $dir_job =~ /$del_sh_no/ && $dir_job =~ /tgz$/i ) {
                            push(@del_inn_file_name,"$dir_job");
                            my $path = "$dir_yy/$dir_mm/$dir_dd";
                            from_to($path,"gbk","utf8");
                            push(@del_inn_file_name_path,$path);
                            my $result = unlink glob("$del_inn_path/$dir_yy/$dir_mm/$dir_dd/$dir_job");
                            if ( $result == 1 ) {
                                push(@del_inn_file_name_result,"已删除");
                            } else {
                                push(@del_inn_file_name_result,"删除出现异常");
                            }
                        }
                    }
                }
            }
        }
    }
    $del_inn_file_no =  scalar(@del_inn_file_name);
    if ( $del_inn_file_no == 0 ) {
        push(@del_inn_file_name,"内层AOI TGZ");
        push(@del_inn_file_name_path,"内层AOI扫描资料");
        push(@del_inn_file_name_result,"没找到旧资料");
    }
#################################################################################################################################################

    my $del_all_path = "$DestDataRootPath/vgt\$/设计课/外部资料/工程部外部取读资料/胜宏全套tgz/$del_client_no\系列";
    from_to($del_all_path,"utf8","gbk");
    my @del_all_dir = &iReadDir($del_all_path);
    my $del_all_file_no = "";
    my @del_all_file_name = ();
    my @del_all_file_name_path = ();
    my @del_all_file_name_result = ();
    foreach my $dir_job (@del_all_dir) {
        if ( $dir_job =~ /$del_client_no/ && $dir_job =~ /$del_sh_no/ && $dir_job =~ /tgz$/i ) {
            my $move_all_path = "$DestDataRootPath/vgt\$/设计课/内部资料/因升级版本前版需作废的tgz/$del_client_no\系列";
            from_to($move_all_path,"utf8","gbk");
            &iMkDir($move_all_path,);
            push(@del_all_file_name,"$dir_job");
            push(@del_all_file_name_path,"胜宏全套tgz/$del_client_no\系列");
            my $result = move("$del_all_path/$dir_job","$move_all_path");
            if ( $result == 1 ) {
                push(@del_all_file_name_result,"移到作废文件夹");
            } else {
                push(@del_all_file_name_result,"移动时出现异常");
            }
        }
    }
    $del_all_file_no =  scalar(@del_all_file_name);
    if ( $del_all_file_no == 0 ) {
        push(@del_all_file_name,"胜宏全套TGZ");
        push(@del_all_file_name_path,"胜宏全套tgz/$del_client_no\系列");
        push(@del_all_file_name_result,"没找到旧资料");
    }

#################################################################################################################################################
    my $del_fz_path = "$DestDataRootPath/vgt\$/设计课/外部资料/工程部外部取读资料/工程辅助资料/胜宏/$del_client_no\系列";
    from_to($del_fz_path,"utf8","gbk");
    my @del_fz_dir = &iReadDir($del_fz_path);
    my $del_fz_file_no = scalar(@del_fz_dir);
    my @del_fz_file_name = ();
    my @del_fz_file_name_path = ();
    my @del_fz_file_name_result = ();
    if ( $del_fz_file_no > 0 ) {
        foreach my $dir_job (@del_fz_dir) {
            if ( $dir_job =~ /$del_sh_no/ ) {
                push(@del_fz_file_name,"$dir_job");
                push(@del_fz_file_name_path,"工程辅助资料/胜宏/$del_client_no\系列");
                #my $del_fz_sh_path = "$del_fz_path/$dir_job";
                my $result = remove_tree("$del_fz_path/$dir_job");
                if ( $result eq 1 ) {
                    push(@del_fz_file_name_result,"已删除");
                } else {
                    push(@del_fz_file_name_result,"删除出现异常");
                }
                goto FFFFF;
            }
        }
    }
    push(@del_fz_file_name,"工程辅助资料");
    push(@del_fz_file_name_path,"工程辅助资料/胜宏/$del_client_no\系列");
    push(@del_fz_file_name_result,"没找到旧资料");
    FFFFF:
#################################################################################################################################################

#    my $del_drl_path = "$DestDataRootPath/vgt\$/设计课/外部资料/工程部外部取读资料/外部资料/工程部外部取读资料/工程钻孔程式/工程钻孔程式/$del_client_no\系列";
    my $del_drl_path = "$DestDataRootPath/vgt\$/设计课/外部资料/工程部外部取读资料/工程钻孔程式/工程钻孔程式/$del_client_no\系列";
    from_to($del_drl_path,"utf8","gbk");
    my @del_drl_dir = &iReadDir($del_drl_path);
    my $del_drl_file_no = scalar(@del_drl_dir);
    my @del_drl_file_name = ();
    my @del_drl_file_name_path = ();
    my @del_drl_file_name_result = ();
    if ( $del_drl_file_no > 0 ) {
        foreach my $dir_drl (@del_drl_dir) {
            if ( $dir_drl =~ /$del_sh_no/ ) {
                push(@del_drl_file_name,"$dir_drl");
                push(@del_drl_file_name_path,"工程钻孔程式/$del_client_no\系列");
                #my $del_drl_sh_path = "$del_drl_path/$dir_drl";
                my $result = remove_tree("$del_fz_path/$dir_drl");
                if ( $result eq 1 ) {
                    push(@del_drl_file_name_result,"已删除");
                } else {
                    push(@del_drl_file_name_result,"删除出现异常");
                }
                goto GGGGG;
            }
        }
    }
    push(@del_drl_file_name,"工程钻孔程式");
    push(@del_drl_file_name_path,"工程钻孔程式/$del_client_no\系列");
    push(@del_drl_file_name_result,"没找到旧资料");
    GGGGG:
#################################################################################################################################################
#    my $del_xl_path = "$DestDataRootPath/vgt\$/设计课/外部资料/工程部外部取读资料/外部资料/工程部外部取读资料/工程辅助资料/文字喷漆资料\-\-\-选化板不可喷墨/一厂汉印喷墨机\-表面化\，不用减3MIL";
    my $del_xl_path = "$DestDataRootPath/vgt\$/设计课/外部资料/工程部外部取读资料/工程辅助资料/文字喷漆资料\-\-\-选化板不可喷墨/一厂汉印喷墨机\-表面化\，不用减3MIL";
    from_to($del_xl_path,"utf8","gbk");
    my @del_pm_xl = &iReadDir($del_xl_path);
    my @del_pm_file_name = ();
    my @del_pm_file_name_path = ();
    my @del_pm_file_name_result = ();

    foreach my $dir_xl (@del_pm_xl) {
        my $china_xl = "$del_client_no\系列";
        $china_xl = decode('utf8',$china_xl);
        $china_xl = encode('gbk',$china_xl);
        if ( $dir_xl =~ $china_xl ) {
            my $del_pm_path = "$del_xl_path/$dir_xl";
            my @del_pm_dir = &iReadDir($del_pm_path);
            my $del_pm_file_no = scalar(@del_pm_dir);
            if ( $del_pm_file_no > 0 ) {
                foreach my $dir_pm (@del_pm_dir) {
                    if ( $dir_pm =~ /$del_client_no/ && $dir_pm =~ /$del_sh_no/ ) {
                        push(@del_pm_file_name,"$dir_pm");
                        push(@del_pm_file_name_path,"工程辅助资料(喷墨)");
                        my $result = remove_tree("$del_pm_path/$dir_pm");
                        if ( $result eq 1 ) {
                            push(@del_pm_file_name_result,"已删除");
                        } else {
                            push(@del_pm_file_name_result,"删除出现异常");
                        }
                        goto HHHHH;
                    }
                }
            }
        }
    }
    push(@del_pm_file_name,"喷墨资料");
    push(@del_pm_file_name_path,"工程辅助资料(喷墨)");
    push(@del_pm_file_name_result,"没找到旧资料");
    HHHHH:

#################################################################################################################################################

    my $del_ls_drl_path = "$DestDataRootPath/vgt\$/设计课/外部资料/工程部外部取读资料/工程钻孔程式/试验或临时资料";
    from_to($del_ls_drl_path,"utf8","gbk");
    my @del_ls_drl_dir = ();
    my $china_drl = "试验钻带";
    $china_drl = decode('utf8',$china_drl);
    $china_drl = encode('gbk',$china_drl);
    my @del_ls_drl_dir_tmp = &iReadDir($del_ls_drl_path);
    foreach my $dir (@del_ls_drl_dir_tmp) {
#        if ( $dir ne "." && $dir ne ".." && $dir ne "" && $dir ne "Thumbs.db" && $dir ne "$china_drl" ) {
        if ( $dir ne "" && $dir ne "Thumbs.db" && $dir ne "$china_drl" ) {
            push(@del_ls_drl_dir,$dir);
        }
    }
    my $del_ls_drl_name = "临时钻带";
    my $del_ls_drl_name_path = "试验或临时资料";
    my $del_normal_no = 0;
    my $del_anomalous_no = 0;
    foreach my $dir_ls (@del_ls_drl_dir) {
        my $del_ls_no1_son_path = "$del_ls_drl_path/$dir_ls";
        my @del_ls_no1_son = &iReadDir($del_ls_no1_son_path);
        foreach my $dir1 (@del_ls_no1_son) {
            if ( -f "$del_ls_drl_path/$dir_ls/$dir1" ) {
                if ( $dir1 =~ /$del_client_no/ && $dir1 =~ /$del_sh_no/ ) {
                    my $result = unlink glob("$del_ls_drl_path/$dir_ls/$dir1");
                    if ($result == 1) {
                        $del_normal_no++;
                    } else {
                        $del_anomalous_no++;
                    }
                }
            } else {
                if ( -d "$del_ls_drl_path/$dir_ls/$dir1" ) {
                    my $del_ls_2_son_path = "$del_ls_drl_path/$dir_ls/$dir1";
                    my @del_ls_2_son = &iReadDir($del_ls_2_son_path);
                    foreach my $dir2 (@del_ls_2_son) {
                        if ( -f "$del_ls_drl_path/$dir_ls/$dir1/$dir2" ) {
                            if ( $dir2 =~ /$del_client_no/ && $dir2 =~ /$del_sh_no/ ) {
                                my $result = unlink glob("$del_ls_drl_path/$dir_ls/$dir1/$dir2");
                                if ($result == 1) {
                                    $del_normal_no++;
                                } else {
                                    $del_anomalous_no++;
                                }
                            }
                        } else {
                            if ( -d "$del_ls_drl_path/$dir_ls/$dir1/$dir2" ) {
                                my $del_ls_3_son_path = "$del_ls_drl_path/$dir_ls/$dir1/$dir2";
                                my @del_ls_3_son = &iReadDir($del_ls_3_son_path);
                                foreach my $dir3 (@del_ls_3_son) {
                                    if ( -f "$del_ls_drl_path/$dir_ls/$dir1/$dir2/$dir3" ) {
                                        if ( $dir3 =~ /$del_client_no/ && $dir3 =~ /$del_sh_no/ ) {
                                            my $result = unlink glob("$del_ls_drl_path/$dir_ls/$dir1/$dir2/$dir3");
                                            if ($result == 1) {
                                                $del_normal_no++;
                                            } else {
                                                $del_anomalous_no++;
                                            }
                                        }
                                    } else {
                                        if ( -d "$del_ls_drl_path/$dir_ls/$dir1/$dir2/$dir3" ) {
                                            my $del_ls_4_son_path = "$del_ls_drl_path/$dir_ls/$dir1/$dir2/$dir3";
                                            my @del_ls_4_son = &iReadDir($del_ls_4_son_path);
                                            foreach my $dir4 (@del_ls_4_son) {
                                                if ( -f "$del_ls_drl_path/$dir_ls/$dir1/$dir2/$dir3/$dir4" ) {
                                                    if ( $dir4 =~ /$del_client_no/ && $dir4 =~ /$del_sh_no/ ) {
                                                        my $result = unlink glob("$del_ls_drl_path/$dir_ls/$dir1/$dir2/$dir3/$dir4");
                                                        if ($result == 1) {
                                                            $del_normal_no++;
                                                        } else {
                                                            $del_anomalous_no++;
                                                        }
                                                    }
                                                } else {
                                                    if ( -d "$del_ls_drl_path/$dir_ls/$dir1/$dir2/$dir3/$dir4" ) {
                                                        my $del_ls_5_son_path = "$del_ls_drl_path/$dir_ls/$dir1/$dir2/$dir3/$dir4";
                                                        my @del_ls_5_son = &iReadDir($del_ls_5_son_path);
                                                        foreach my $dir5 (@del_ls_5_son) {
                                                            if ( -f "$del_ls_drl_path/$dir_ls/$dir1/$dir2/$dir3/$dir4/$dir5" ) {
                                                                if ( $dir5 =~ /$del_client_no/ && $dir5 =~ /$del_sh_no/ ) {
                                                                    my $result = unlink glob("$del_ls_drl_path/$dir_ls/$dir1/$dir2/$dir3/$dir4/$dir5");
                                                                    if ($result == 1) {
                                                                        $del_normal_no++;
                                                                    } else {
                                                                        $del_anomalous_no++;
                                                                    }
                                                                }
                                                            } else {
                                                                if ( -d "$del_ls_drl_path/$dir_ls/$dir1/$dir2/$dir3/$dir4/$dir5" ) {
                                                                    my $del_ls_6_son_path = "$del_ls_drl_path/$dir_ls/$dir1/$dir2/$dir3/$dir4/$dir5";
                                                                    my @del_ls_6_son = &iReadDir($del_ls_6_son_path);
                                                                    foreach my $dir6 (@del_ls_6_son) {
                                                                        if ( -f "$del_ls_drl_path/$dir_ls/$dir1/$dir2/$dir3/$dir4/$dir5/$dir6" ) {
                                                                            if ( $dir6 =~ /$del_client_no/ && $dir6 =~ /$del_sh_no/ ) {
                                                                                my $result = unlink glob("$del_ls_drl_path/$dir_ls/$dir1/$dir2/$dir3/$dir4/$dir5/$dir6");
                                                                                if ($result == 1) {
                                                                                    $del_normal_no++;
                                                                                } else {
                                                                                    $del_anomalous_no++;
                                                                                }
                                                                            }
                                                                        } else {
                                                                            if ( -d "$del_ls_drl_path/$dir_ls/$dir1/$dir2/$dir3/$dir4/$dir5/$dir6" ) {
                                                                                my $del_ls_7_son_path = "$del_ls_drl_path/$dir_ls/$dir1/$dir2/$dir3/$dir4/$dir5/$dir6";
                                                                                my @del_ls_7_son = &iReadDir($del_ls_7_son_path);
                                                                                foreach my $dir7 (@del_ls_7_son) {
                                                                                    if ( -f "$del_ls_drl_path/$dir_ls/$dir1/$dir2/$dir3/$dir4/$dir5/$dir6/$dir7" ) {
                                                                                        if ( $dir7 =~ /$del_client_no/ && $dir7 =~ /$del_sh_no/ ) {
                                                                                            my $result = unlink glob("$del_ls_drl_path/$dir_ls/$dir1/$dir2/$dir3/$dir4/$dir5/$dir6/$dir7");
                                                                                            if ($result == 1) {
                                                                                                $del_normal_no++;
                                                                                            } else {
                                                                                                $del_anomalous_no++;
                                                                                            }
                                                                                        }
                                                                                    } else {
                                                                                        if ( -d "$del_ls_drl_path/$dir_ls/$dir1/$dir2/$dir3/$dir4/$dir5/$dir6/$dir7" ) {
                                                                                            my $del_ls_8_son_path = "$del_ls_drl_path/$dir_ls/$dir1/$dir2/$dir3/$dir4/$dir5/$dir6/$dir7";
                                                                                            my @del_ls_8_son = &iReadDir($del_ls_8_son_path);
                                                                                            foreach my $dir8 (@del_ls_8_son) {
                                                                                                if ( -f "$del_ls_drl_path/$dir_ls/$dir1/$dir2/$dir3/$dir4/$dir5/$dir6/$dir7/$dir8" ) {
                                                                                                    if ( $dir8 =~ /$del_client_no/ && $dir8 =~ /$del_sh_no/ ) {
                                                                                                        my $result = unlink glob("$del_ls_drl_path/$dir_ls/$dir1/$dir2/$dir3/$dir4/$dir5/$dir6/$dir7/$dir8");
                                                                                                        if ($result == 1) {
                                                                                                            $del_normal_no++;
                                                                                                        } else {
                                                                                                            $del_anomalous_no++;
                                                                                                        }
                                                                                                    }
                                                                                                }
                                                                                            }
                                                                                            if ( $dir7 =~ /$del_client_no/ && $dir7 =~ /$del_sh_no/ ) {
                                                                                                rmdir("$del_ls_drl_path/$dir_ls/$dir1/$dir2/$dir3/$dir4/$dir5/$dir6/$dir7");
                                                                                            }
                                                                                        }
                                                                                    }
                                                                                }
                                                                                if ( $dir6 =~ /$del_client_no/ && $dir6 =~ /$del_sh_no/ ) {
                                                                                    rmdir("$del_ls_drl_path/$dir_ls/$dir1/$dir2/$dir3/$dir4/$dir5/$dir6");
                                                                                }
                                                                            }
                                                                        }
                                                                    }
                                                                    if ( $dir5 =~ /$del_client_no/ && $dir5 =~ /$del_sh_no/ ) {
                                                                        rmdir("$del_ls_drl_path/$dir_ls/$dir1/$dir2/$dir3/$dir4/$dir5");
                                                                    }
                                                                }
                                                            }
                                                        }
                                                        if ( $dir4 =~ /$del_client_no/ && $dir4 =~ /$del_sh_no/ ) {
                                                            rmdir("$del_ls_drl_path/$dir_ls/$dir1/$dir2/$dir3/$dir4");
                                                        }
                                                    }
                                                }
                                            }
                                            if ( $dir3 =~ /$del_client_no/ && $dir3 =~ /$del_sh_no/ ) {
                                                rmdir("$del_ls_drl_path/$dir_ls/$dir1/$dir2/$dir3");
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    # 上传数据库 ##########################################################
#    &UploadLogToMySql("delete",$tPath{vuJob},$RecordHandOut{SimpleLog},$RecordHandOut{FullLog},); # inner outer all backup delete
    &UploadLogToMySql("delete",$tPath{vuJob},'','',); # inner outer all backup delete

#################################################################################################################################################
    my @all_del_file_name = ();
    @all_del_file_name = (@del_inn_file_name,@del_all_file_name,@del_fz_file_name,@del_drl_file_name,@del_pm_file_name,"$del_ls_drl_name");
    my @all_del_file_path = ();
    @all_del_file_path = (@del_inn_file_name_path,@del_all_file_name_path,@del_fz_file_name_path,@del_drl_file_name_path,@del_pm_file_name_path,"$del_ls_drl_name_path");
    my @all_del_file_result = ();
    @all_del_file_result = (@del_inn_file_name_result,@del_all_file_name_result,@del_fz_file_name_result,@del_drl_file_name_result,@del_pm_file_name_result,"已删除$del_normal_no\个;异常$del_anomalous_no\个");
    my $file_no = scalar(@all_del_file_name);
    my $tab_row = "";
    my $mw4 = MainWindow->new( -title =>_Utf8("胜宏科技"));
    $mw4->bind('<Return>' => sub{ shift->focusNext; });
#    $mw4->protocol("WM_DELETE_WINDOW", \&OnQuit);
    if ( $file_no <= 5 ) {
        $mw4->geometry("616x330-800+80");
        $tab_row = 6;
    } else {
        $mw4->geometry("616x500-800+80");
        $tab_row = 11;
    }
    $mw4->resizable(0,0);
    $mw4->raise();
    Win32::API->new("user32","SetWindowPos",[qw(N N N N N N N)],'N')->Call(hex($mw4->frame()),-1,0,0,0,0,3);
    my $sh_log = $mw4->Photo('info',-file => "$images_path/sh_log.xpm");
    my $CAM_frm = $mw4->Frame(-bg => '#9BDBDB',-borderwidth =>2,-relief => "raised",-height => 15)->pack(-side=>'top',-fill=>'x');
    my $image_label = $CAM_frm->Label(-image => $sh_log, -border => 1, -relief => 'solid',)->pack(-side => 'left',-padx => 2,-pady => 2);
    $CAM_frm->Label(-text => _Utf8('删除旧资料列表'),-font => 'charter 18 bold',-bg => '#9BDBDB')->pack();
    $CAM_frm->Label(-text => _Utf8("版权所有：胜宏科技  $appVersion"),-font => 'charter 10',-bg => '#9BDBDB')->pack(-side=>'right', -padx => 10);
    my $CAM_frm_all = $mw4->Frame(-bg => '#9BDBDB')->pack(-side=>'top',-fill=>'both',-expand=>1);
    my $CAM_frm_old = $CAM_frm_all->Frame(-bg => '#9BDBDB')->pack(-side=>'top',-fill=>'both');
    my $tab_frm = $CAM_frm_old->Table(-columns => 3,-rows => "$tab_row",fixedrows => 1,-scrollbars =>'oe',-bg => 'white',-relief => 'groove');
    my @tab_name_headings = ();
    my $tab_width = "";
    @tab_name_headings = ("删除资料位置","删除文件名称","状态");
    my $m = 1;
    foreach my $tmp (@tab_name_headings) {
        if ( $tmp eq "删除资料位置" ) {
            $tab_width = 25;
        } elsif ( $tmp eq "状态" ) {
            $tab_width = 18;
        } else {
            $tab_width = 25;
        }
        my $title_but = $tab_frm->Button(-text =>_Utf8("$tmp"),-width => $tab_width,-font=> 'charter 12',-activebackground=>'#9BDBDB',-state=> "disabled",)->pack(-side => 'left',-fill=>'x');
        $tab_frm->put(0, $m, $title_but);
        $m++;
    }

    if ( $file_no > 0 ) {
        my $i = 1;
        my $n = 0;
        foreach my $tmp (@all_del_file_name) {
#            my $result = @all_del_file_result[$n];
            my $result = $all_del_file_result[$n];
            my $color_fg = "";
            if ( $result eq "已删除" or  $result eq "移到作废文件夹" or $del_normal_no ne "0" ) {
                $color_fg = "yellowgreen";
            } else {
                $color_fg = "red";
            }
#            my $site = @all_del_file_path[$n];
            my $site = $all_del_file_path[$n];
            my $show_out_name = $tab_frm->Label(-text => _Utf8("$site"), -width => 25, -height=>'2', -font => 'SimSun 11 bold',-relief =>'groove',-background => "white",-fg=> "$color_fg")->pack(-side => 'top');
            $tab_frm->put($i, 1, $show_out_name);
            my $show_lay_name = $tab_frm->Label(-text => _Utf8("$tmp"), -width => 25, -height=>'2', -font => 'SimSun 11',-relief =>'groove',-background => "white",-fg=> "$color_fg")->pack(-side => 'top');
            $tab_frm->put($i, 2, $show_lay_name);
            my $show_lay_result = $tab_frm->Label(-text => _Utf8("$result"), -width => 18, -height=>'2', -font => 'SimSun 11',-relief =>'groove',-background => "white",-fg=> "$color_fg")->pack(-side => 'top');
            $tab_frm->put($i, 3, $show_lay_result);
            $i++;
            $n++;
        }
    }
    $tab_frm->pack(-side=>"top", -fill=>'x');

    my $Bot_frm = $mw4->Frame(-bg => '#9BDBDB',-borderwidth =>2,-height => 40)->pack(-side=>'bottom',-fill=>'x');
    my $array_button = $Bot_frm->Button(-text => _Utf8('退出'),-command => sub {$mw4->withdraw;},-width => 10,-bg => '#9BDBDB',-activebackground=>'white',-font=> 'charter 12',-height=> 2)->pack(-side => 'right',-padx => 10);
    MainLoop;
}

sub BackupCAMData { #归档资料 &BackupCAMData('Hide');
    my $tActMode = shift || 'None' ;

    my $name_list = $add_name_frm->get("1.0","end");
    my @output_name_list = split(/\n/,$name_list);

#    my %DataInfoLog;
#    my %RecordHandOut;
    if ( $tActMode eq 'None' ) {
        &RunNewVerScript;
        if ( &JobNameCheck($sel_but_frm,@output_name_list) eq 'no' ) {
            return;
        }
    }

    foreach my $tJob (@output_name_list) {
        $tJob =lc($tJob);
        my %tPath = &getHandOutPath("$tJob"); #获取通用路径及变量

        &iMkDir(&Utf8_Gbk( $tPath{BakJob} ),);
        my @TempJobFolderList = &iReadDir( &Utf8_Gbk( $tPath{TempJob} ) );
        print (@TempJobFolderList);
        print "\n";
        
        my $MiFileExists = 'no';
        &iMkDir( &Utf8_Gbk( $tPath{BakJob} ),);
        foreach my $tFile (@TempJobFolderList) {
            if ( -d &Utf8_Gbk( $tPath{TempJob} ) . '/' . $tFile ) {
                &iMkDir(&Utf8_Gbk( $tPath{BakJob} ) . '/' . $tFile,);
				my $tCopyStat;
                $tCopyStat = rcopy(  &Utf8_Gbk( $tPath{TempJob} ) . '/' . $tFile,&Utf8_Gbk( $tPath{BakJob} ) . '/' . $tFile );
                if ( $tFile =~ /mi$/i ) {
                    $MiFileExists = 'yes';
                } else {
                    if ( $RunMode ne 'test' ) {
						if (not defined $showType or $showType ne "inner"){
							
							remove_tree( &Utf8_Gbk( $tPath{TempJob} ) . '/' . $tFile);
							print "delete ----> $tFile,\n";
							
						}else{
							#伍青通知 内层下发时删除所有临时文件 tgz资料保留 20240204 by lyh
							if ( lc($tFile) eq lc($tPath{'vJobVer'}) ){
								my @vJobVer_TempJobFolderList = &iReadDir( &Utf8_Gbk( $tPath{TempJob} ) . '/' . $tFile );
								print (@vJobVer_TempJobFolderList);
								print "\n";
								
								foreach my $vJobVer_tFile (@vJobVer_TempJobFolderList) {
									if ( -d &Utf8_Gbk( $tPath{TempJob} ) . '/' . $tFile . '/' . $vJobVer_tFile ) {
										remove_tree( &Utf8_Gbk( $tPath{TempJob} ) . '/' . $tFile . '/' . $vJobVer_tFile);
									}else{
										if ($vJobVer_tFile !~ /.*tgz$/i){
											unlink &Utf8_Gbk( $tPath{TempJob} ) . '/' . $tFile . '/' . $vJobVer_tFile;
										}
									}
								}
								
							}else{
								#print "delete22222 ----> $tFile,\n";
								my $gongzuogao = &Utf8_Gbk("工作稿");
								if ($tFile !~ /$gongzuogao/){
									remove_tree( &Utf8_Gbk( $tPath{TempJob} ) . '/' . $tFile);
								}
							}
						}
                    }
                }
				if (not defined $tCopyStat){
					&iTkMwMsg($mw,_Utf8("提示","info","ok",&Utf8_Gbk( $tPath{TempJob} ) . '/' . $tFile."拷贝归档资料失败，请手动覆盖!"),);
				}
            } else {
				my $tCopyStat;
                $tCopyStat = rcopy( &Utf8_Gbk( $tPath{TempJob} ) . '/' . $tFile,&Utf8_Gbk( $tPath{BakJob} ) . '/' . $tFile );
                if ( $RunMode ne 'test') {
                    unlink &Utf8_Gbk( $tPath{TempJob} ) . '/' . $tFile;
                }
				if (not defined $tCopyStat){
					&iTkMwMsg($mw,_Utf8("提示","info","ok",&Utf8_Gbk( $tPath{TempJob} ) . '/' . $tFile."拷贝归档资料失败，请手动覆盖!"),);
				}
            }
        }
        if ( $MiFileExists eq 'no' ) {
            if ( $RunMode ne 'test' ) {
				if (not defined $showType or $showType ne "inner"){
					remove_tree( &Utf8_Gbk( $tPath{TempJob} ) );
					print "delete ---->";
					print &Utf8_Gbk( $tPath{TempJob} );
					print "\n";
				}
            }
        }
        if ( $tActMode eq 'None' ) {
            &UploadLogToMySql("backup",$tPath{vuJob},'','',); # inner outer all backup delete
        }
    }

    if ( $tActMode eq 'None' ) {
        &iTkMwMsg($mw,_Utf8("提示","info","ok","归档结束,请确认!"),);
    }
}

#/****************************
# 函数名: showXFresult
# 功  能: 显示最终下发结果信息
# 参  数: None
# 返回值: 执行结果界面
#****************************/
sub showXFresult
{
    my $DataInfoLog=shift;
    my %DataInfoLog = %$DataInfoLog;
    my $mw1 = MainWindow->new( -title =>_Utf8("胜宏科技"));
    $mw1->bind('<Return>' => sub{ shift->focusNext; });
    $mw1->geometry("+400+80");
    $mw1->resizable(0,0);
    $mw1->raise();
    # Win32::API->new("user32","SetWindowPos",[qw(N N N N N N N)],'N')->Call(hex($mw1->frame()),-1,0,0,0,0,3);
    my $sh_log = $mw1->Photo('info',-file => "$images_path/sh_log.xpm");
    my $CAM_frm = $mw1->Frame(-bg => '#9BDBDB',-borderwidth =>2,-relief => "raised",-height => 15)->pack(-side=>'top',-fill=>'x');
    my $image_label = $CAM_frm->Label(-image => $sh_log, -border => 1, -relief => 'solid',)->pack(-side => 'left',-padx => 2,-pady => 2);
    $CAM_frm->Label(-text => _Utf8('下发资料列表'),-font => 'charter 18 bold',-bg => '#9BDBDB')->pack();
    $CAM_frm->Label(-text => _Utf8("版权所有：胜宏科技  $appVersion"),-font => 'charter 10',-bg => '#9BDBDB')->pack(-side=>'right', -padx => 10);
    my $CAM_frm_all = $mw1->Frame(-bg => '#9BDBDB')->pack(-side=>'top',-fill=>'both',-expand=>1);
    my $CAM_frm_inn = $CAM_frm_all->Frame(-bg => '#9BDBDB')->pack(-side=>'top',-fill=>'both');

    my $tab_frm = $CAM_frm_inn->Table(-columns => 4,-rows => scalar(@{$DataInfoLog{List}}) + 1,fixedrows => 1,-scrollbars =>'oe',-bg => 'white',-relief => 'groove');
    my @tab_name_headings = ();
    my $tab_width = "";
    @tab_name_headings = ("下发资料类型","下发文件名称","状态","下发位置");
    my $m = 1;
    foreach my $tmp (@tab_name_headings) {
        if ( $tmp eq "下发资料类型" ) {
            $tab_width = $HeadNoteWidth;
        } elsif ( $tmp eq "状态" ) {
            $tab_width = $HeadStatWidth;
        } elsif ( $tmp eq "下发位置" ) {
            $tab_width = $HeadPathWidth;
        } else {
            $tab_width = $HeadFileWidth;
        }
        my $title_but = $tab_frm->Button(-text =>_Utf8("$tmp"),-width => $tab_width,-font=> 'charter 12',-activebackground=>'#9BDBDB',-state=> "disabled",)->pack(-side => 'left',-fill=>'x');
        $tab_frm->put(0, $m, $title_but);
        $m++;
    }
    my $file_no = 0;
    if ( scalar(@{$DataInfoLog{List}}) > 0 ) {
        my @dhd = @{$DataInfoLog{List}};
        ## @dhd
        for my $tNum ( 0 .. scalar(@{$DataInfoLog{List}}) - 1 ){
            ## $tNum
            my $tName = $DataInfoLog{List}[$tNum];
            my $tTableLine = $tNum + 1 + $file_no;
            # --下发资料类型
            my $show_out_name = $tab_frm->Entry(-textvariable =>  _Utf8( $DataInfoLog{'Log'}{$tName}{'Name'} ), -width => $HeadNoteWidth, -font => 'SimSun 11 bold',-relief =>'groove',-background => "white",-fg=> $DataInfoLog{'Log'}{$tName}{'Color'} ,)->pack(-side => 'top');
             $tab_frm->put($tTableLine, 1, $show_out_name);
            
            # --下发文件名称
            my $show_lay_name = $tab_frm->Label(-text => _Utf8( $DataInfoLog{'Log'}{$tName}{'File'} || '' ), -width => $HeadFileWidth, -font => 'SimSun 11',-relief =>'groove',-background => "white",-fg=>$DataInfoLog{'Log'}{$tName}{'Color'} ,)->pack(-side => 'top');
             $tab_frm->put($tTableLine, 2, $show_lay_name);
             
            # --下发状态
            my $show_lay_result = $tab_frm->Entry(-text => _Utf8( $DataInfoLog{'Log'}{$tName}{'Status'} ), -width => $HeadStatWidth, -font => 'SimSun 11',-relief =>'groove',-background => "white",-fg=>$DataInfoLog{'Log'}{$tName}{'Color'} ,)->pack(-side => 'top');
            $tab_frm->put($tTableLine, 3, $show_lay_result);
            
            # --下发位置
            # --存在
            my $show_xf_path = $tab_frm->Entry(-text => _Gbk( $DataInfoLog{'Log'}{$tName}{'DesPath'} || ""), -width => $HeadPathWidth, -font => 'SimSun 11',-relief =>'groove',-background => "white",-fg=>$DataInfoLog{'Log'}{$tName}{'Color'} ,)->pack(-side => 'top');
            $tab_frm->put($tTableLine, 4, $show_xf_path);
        }
    }
    $tab_frm->pack(-side=>"top", -fill=>'x');

    my $Bot_frm = $mw1->Frame(-bg => '#9BDBDB',-borderwidth =>2,-height => 40)->pack(-side=>'bottom',-fill=>'x');
    my $array_button = $Bot_frm->Button(-text => _Utf8('退出'),-command => sub {$mw1->withdraw},-width => 10,-bg => '#9BDBDB',-activebackground=>'white',-font=> 'charter 12',-height=> 2)->pack(-side => 'right',-padx => 10);
    MainLoop;
}

#############################################################################################################

sub aOnQuit {
    my ($ans) = $mw->messageBox(-icon => 'question',-message => _Utf8('你确定要退出吗？'),-title => 'quit',-type => 'OkCancel');
    return if $ans eq "Cancel";
    exit;
}

sub update_sel_frm { #更新输入框状态
    my @output_name_list = ();
    my $name_list = ();
    $name_list = $add_name_frm->get("1.0","end");
    @output_name_list = split(/\n/,$name_list);
    my $name_list_no = scalar(@output_name_list);
    if ( $name_list_no > 0 ) {
        foreach my $tmp (@output_name_list) {
            my $tmp_name = _Utf8("在此输入一个料号名.");
            if ( $tmp eq $tmp_name ) {
                $add_name_frm->delete('1.0',"end");
                $add_name_frm->configure();
            }
        }
    }   
}

sub ClearListText {  #清空列表
    $add_name_frm->delete('1.0',"end");
    $add_name_frm->configure();
}

sub JobNameCheck { #&JobNameCheck($sel_but_frm,@output_name_list);
    my $sel_but_frm = shift ;
    my @output_name_list = @_ ;
    my $name_list_no = scalar(@output_name_list);
    if ( $name_list_no == 0 ) {
        &iTkMwMsg($mw,_Utf8("警告","warning","ok","料号名为空,请重新输入!"),);
        return ('no');
    } else {
        my $name1 = $output_name_list[0];
        my $tmp_name = _Utf8("在此输入一个料号名.");
        if ( $name1 eq $tmp_name ) {
#            &run_message_no_sel;
            &iTkMwMsg($mw,_Utf8("警告","warning","ok","料号名为空,请重新输入!"),);
#            $sel_but_frm->withdraw;
            return ('no');
        } else {
            my $name_l = length($name1);
            if ( $name_l eq 15 ){
                if ( $name1 !~ /-C$/i ){
                    &iTkMwMsg($mw,_Utf8("警告","warning","ok","料号名有误,请重新输入!"),);
                    return ('no');
                }
            } elsif ( $name_l ne 13 ) {
                &iTkMwMsg($mw,_Utf8("警告","warning","ok","料号名有误,请重新输入!"),);
                return ('no');
            }
        }
                        
        # --从ERP中获取是否存在此型号
        if (&checkERPjob($dbc_e, $name1) == 0)
        {
            my $reV = &Messages_Sel('warning', _Utf8("警告：\n\tERP中查无此料号，请确认是否继续下发？"));
            return ('no') if ($reV !~ /OK/i);
        }
		# if ($ENV{'USERNAME'} =~ /(44813)/ ) {
		    my $cust_name = substr($name1, 1,3); # TODO 为了183的单独防呆
		if ($cust_name eq '183') {
			# 183系列希耀匹配ECN系统单号
			my $scriptPath = "//192.168.2.33/incam-share/incam/genesis/sys/scripts";
			my $pythonVer = "//192.168.2.33/incam-share/incam/Path/Python26/python.exe";
			my $a=system ("$pythonVer $scriptPath/sh_script/qa_publish/qa_need_update_hdi.py $name1");
			print $a;
			if ($a != 0) {
				return ('no');
			}
		}
		#}
    }
    return ('ok');
}

sub RunNewVerScript { #&RunNewVerScript; 运行新版本
    # --获取当前程序所在的目录地址
    my $CURRSCRIPTPATH = dirname($0);
    #from_to($CURRSCRIPTPATH,"gbk","utf8",);
    $CURRSCRIPTPATH =~ s#\\#/#g;
    my $LoadScriptVerFile = $CURRSCRIPTPATH . '/' . "Version.ini";

    my $ScriptVer;
    for my $tLine ( &iReadFile($LoadScriptVerFile) ) {
        chomp $tLine;
        $tLine =~ s/^\s*|\s*$//g;
        $tLine =~ s#\\#/#g;
        if ( ( $tLine =~ /^\s*$/ ) or ( $tLine =~ /^\#.*/ ) or ( $tLine =~  /^\;.*/ ) ) {
            next;
        } else {
            $ScriptVer = $tLine;
            last;
        }
    }
    
    if ( defined $ScriptVer ){
        my ($CurrScriptVer) = (fileparse($0, qw/\.exe \.com \.pl/))[0];
        print &Utf8_Gbk("当前运行程序版本：")."$CurrScriptVer\n";
        print &Utf8_Gbk("服务器最新程序版本：")."$ScriptVer\n";
        if ( $ScriptVer ne $CurrScriptVer ){
            #print "|$ScriptVer|\n|$CurrScriptVer|\n";
            my $RunScriptPath = $CURRSCRIPTPATH . '/' . $ScriptVer . '.exe' ;
            my $RunPerlScriptPath = $CURRSCRIPTPATH . '/' . $ScriptVer . '.pl' ;
            print "$RunScriptPath\n$RunPerlScriptPath\n";
            if ( -e $RunScriptPath ){
                &iTkMwMsg($mw,_Utf8("版本更新","info","ok","当前程序存在新版本,点击 [ 确定 ] 运行新版本。"),);
                exec($RunScriptPath);

            }elsif ( -e $RunPerlScriptPath ){
                &iTkMwMsg($mw,_Utf8("版本更新","info","ok","当前程序存在新版本,点击 [ 确定 ] 运行新版本。"),);
        #        my $PerlPath = `where perl`;
                my $PerlPath = 'perl';
                exec($PerlPath,$RunPerlScriptPath);
            }
        }
    }
    return();
}

#############################################################################################################
sub _Gbk { #将 中文 解码成 字节流                 # my $tString = _Gbk("$InputStr");
    #return decode('CP936',shift);
    my @NewCode;
    for ( @_ ) {
        push( @NewCode,decode('CP936',$_) );
    }
    if ( defined $NewCode[0] ){
        if ( scalar(@NewCode) > 1 ){
            return(@NewCode);
        } else {
            return($NewCode[0]);
        }
    } else {
        return();
    }
}

sub _Utf8 { #将 utf8 解码成 字节流 (Tk;Tkx)     # my $tString = _Utf8("$InputStr");
    #return decode('utf8',shift);
    my @NewCode;
    for ( @_ ) {
        push( @NewCode,decode('utf8',$_) );
    }
    if ( defined $NewCode[0] ){
        if ( scalar(@NewCode) > 1 ){
            return(@NewCode);
        } else {
            return($NewCode[0]);
        }
    } else {
        return();
    }
}

sub Utf8_ { #将 utf8 解码再编码                     # my $tString = Utf8_("$ConvStr");
    #return encode('utf8',decode('utf8',shift));
    my @NewCode;
    for ( @_ ) {
        push( @NewCode,encode('utf8',decode('utf8',$_)) );
    }
    if ( defined $NewCode[0] ){
        if ( scalar(@NewCode) > 1 ){
            return(@NewCode);
        } else {
            return($NewCode[0]);
        }
    } else {
        return();
    }
}

sub Gbk_ { #将 gbk 解码再编码                     # my $tString = Gbk_("$ConvStr");
    #return encode('CP936',decode('CP936',shift));
    my @NewCode;
    for ( @_ ) {
        push( @NewCode,encode('CP936',decode('CP936',$_)) );
    }
    if ( defined $NewCode[0] ){
        if ( scalar(@NewCode) > 1 ){
            return(@NewCode);
        } else {
            return($NewCode[0]);
        }
    } else {
        return();
    }

}

sub Gbk_Utf8 { #将 gbk 转换成 utf8                 # my $tOutputStr = Gbk_Utf8("$InputStr");
    #return encode('utf8',decode('CP936',shift));
    my @NewCode;
    for ( @_ ) {
        push( @NewCode,encode('utf8',decode('CP936',$_)) );
    }
    if ( defined $NewCode[0] ){
        if ( scalar(@NewCode) > 1 ){
            return(@NewCode);
        } else {
            return($NewCode[0]);
        }
    } else {
        return();
    }
}

sub Utf8_Gbk { #将 utf8 转换成 gbk                 # my $tOutputStr = Utf8_Gbk("$InputStr");
    #return encode('CP936',decode('utf8',shift));
    my @NewCode;
    for ( @_ ) {
#        print $_ . "\n" ;
        push( @NewCode,encode('CP936',decode('utf8',$_)) );
    }
    if ( defined $NewCode[0] ){
        if ( scalar(@NewCode) > 1 ){
            return(@NewCode);
        } else {
            return($NewCode[0]);
        }
    } else {
        return();
    }
}

sub iReadDir {  #读取文件夹 # my @tDirLists = &iReadDir('D:\Input');
    my $tPath = shift;
    # --"\"替换成“/"
    $tPath =~ s#[\\]#/#g;
    if ( defined $tPath ) {
        if ( -e $tPath ){
            my %DirHandle;
            my $DirHandleRand = 'DirHandle' . int(rand(99999));
#            opendir($DirHandle,"$tPath" || die "Cannot open path this $tPath");
            opendir($DirHandle{$DirHandleRand},"$tPath" || die "Cannot open path this $tPath: $!\n");
            my @DirLists;
            for my $tDir ( readdir($DirHandle{$DirHandleRand}) ) {
                if ( $tDir ne '.' and $tDir ne '..' ){
                    push @DirLists,$tDir;
                }
            }
            closedir($DirHandle{$DirHandleRand});
            return(@DirLists);
        } else {
            warn "Dir does not exist - $tPath: $!\n";
        }
    } else {
        die "No definition Dir!\n";
    }
    return();
}

sub iMkDir {  #创建文件夹 # &iMkDir('\\\192.168.1.1\1\12\','/root/desk/123/abc',);
    my @OrgPath = @_;
    if ( scalar(@OrgPath) != 0 ) {
        if ( $OrgPath[0] eq "" ) {
            return();
        }
        for my $tOrgPath ( @OrgPath ) {
            $tOrgPath =~ s#[\\]#/#g;
            my ($tOrgPathStart) = ($tOrgPath =~ m#^(/+)[^/]+#i );
            my $tPath;
            my @TmpPath;
            for ( split /\/+/,$tOrgPath ){
                if ( $_ eq '' ) {
                    next;
                }
                if ( defined $tPath ) {
                    $tPath = $tPath . $_ . '/';
                }else{
                    if ( defined $tOrgPathStart ){
                        $tPath = $tOrgPathStart . $_ . '/'  ;
                    } else {
                        $tPath = $_ . '/'  ;
                    }

                }
                push @TmpPath,$tPath;
            }

            my @tCreateDir;
            for my $tPath ( reverse @TmpPath ){
                unless ( -e $tPath ){
                    push @tCreateDir,$tPath;
                } else {
                    last;
                }
            }
            for my $tPath ( reverse @tCreateDir ){
                mkdir "$tPath",0777 or warn "Cannot make $tPath directory: $!\n";
            }
        }
    }
    return();
}

sub iReadFile {  #读取文件 # my @tFieContent = iReadFile('D:\1.txt');
    my $tFile = shift;
    $tFile =~ s#[\\]#/#g;
    #print $tFile;
    if ( defined $tFile ) {
        if ( -e ($tFile) ){
            my %Handle;
            my $FileHandleRand = 'FileHandle' . int(rand(99999));
            open ($Handle{$FileHandleRand},  "<$tFile") or warn "Cannot open file - $tFile: $!\n";
            my $FileHandle = $Handle{$FileHandleRand};
            my @FileContent = <$FileHandle>;
            close ($Handle{$FileHandleRand});
            return(@FileContent);
        } else {
            warn "File does not exist - $tFile: $!\n";
        }
    } else {
        warn "No definition file!\n";
    }
    return();
}

sub iWriteFile {  #写文件 # iWriteFile('>','D:\1.txt','1','2',); # iWriteFile('>>','D:\1.txt','1','2',);
    my $WriteMode;
    if ( $_[0] eq '>' or $_[0] eq '>>' ){
        $WriteMode = shift;
    } else {
        $WriteMode = '>';
    }
    my $tFile = shift;
    if ( $tFile =~ /^>/ ){
        $WriteMode = '';
    }
    $tFile =~ s#[\\]#/#g;
    my @WriteContent = @_;
    if ( defined $tFile ) {
            my %Handle;
            my $FileHandleRand = 'FileHandle' . int(rand(99999));
            open ($Handle{$FileHandleRand},  $WriteMode . $tFile) or warn "Cannot open file - $tFile: $!\n";
            my $FileHandle = $Handle{$FileHandleRand};
            for my $tLine ( @WriteContent) {
                chomp $tLine;
                print $FileHandle $tLine . "\n";
            }
            close ($Handle{$FileHandleRand});
    } else {
        die "No definition file!\n";
    }
    return();
}

sub iTkMwMsg {  #当前$mw提示框 # iTkMwMsg($mw,"JOB不存在!","warning","ok","JOB不存在,脚本退出!",);
    my ($mw,$tTitle,$tIco,$tType,$tMsg,) = (@_);
    my $MsgOut = $mw->messageBox(-type => "$tType",-message => "$tMsg",-icon => "$tIco",-title => "$tTitle",);
    $MsgOut = lc($MsgOut);
    chomp $MsgOut;
    return ($MsgOut);
}

sub ilistFolders { #列出指定目录的所有文件夹 my @FolderList = &ilistFolders('2',$listRootPath); my @FolderList = &ilistFolders(';;',$listRootPath);
    my $RecursionDeep = shift || ';;';
    my @listRootPath = @_;
#    my @FolderList = ($listRootPath,);
    my @FolderList;
    my @tFolderList = &ilistPath('folder',@listRootPath);
    if ( $RecursionDeep eq ';;' ) {
        for ( ;; ){
            if ( scalar(@tFolderList) != 0 ) {
                push (@FolderList,@tFolderList);
                @tFolderList = &ilistPath('folder',@tFolderList);
            } else {
                last;
            }
        }
    } else {
        for ( 1 .. $RecursionDeep ){
            if ( scalar(@tFolderList) != 0 ) {
                push (@FolderList,@tFolderList);
                @tFolderList = &ilistPath('folder',@tFolderList);
            } else {
                last;
            }
        }
    }
    return (@FolderList);
}

sub ilistPath { #列出指定目录的一级的文件或文件夹
    my @FolderList;
    my $listMode = shift; #file folder all
    my @listRootPath = @_;
    for my $tlistRootPath (@listRootPath) {
        if ( -e $tlistRootPath ){
            opendir(DIR,"$tlistRootPath"|| die "can't open this $tlistRootPath");
            my @Files = readdir(DIR);
            closedir(DIR);

            for my $tFile ( @Files ){
                next if( $tFile =~ /^\.$/ || $tFile =~ /^\.\.$/ );
                if ( $listMode eq "file" ){
                    if ( -f $tlistRootPath. '/' . $tFile ){
                        push (@FolderList,$tlistRootPath. '/' . $tFile);
                    }
                } elsif ( $listMode eq "folder" ){
                    if ( -d $tlistRootPath. '/' . $tFile ){
                        push (@FolderList,$tlistRootPath. '/' . $tFile);
                    }
                } elsif ( $listMode eq "all" ){
                    push (@FolderList,$tlistRootPath. '/' . $tFile);
                }
            }
        } else {
            warn "Dir does not exist - $tlistRootPath: $!\n";
        }
    }
    return(@FolderList);
}

sub iClearDup {  #数组去重 # my @newArray = iClearDup(@Array);
    my %hash;
    for (@_) {
        $hash{$_} = 1;
    }
    return (keys %hash);
}

sub HandOutActSub {  #下发动作
#    &HandOutActSub('Copy',\%DataInfoLog,\%RecordHandOut,$tKeyName,$tNoteName,$tJob,$tFeatures,$tSourcePath,$DestPath1,$DestPath2,);
#    &HandOutActSub('Copys',\%DataInfoLog,\%RecordHandOut,$tKeyName,$tNoteName,$tJob,$tFeatures,$tSourcePath,$DestPath1);

#    &HandOutActSub('Move',\%DataInfoLog,\%RecordHandOut,$tKeyName,$tNoteName,$tJob,$tFeatures,$tSourcePath,@DestPath);
#    &HandOutActSub('Moves',\%DataInfoLog,\%RecordHandOut,$tKeyName,$tNoteName,$tJob,$tFeatures,$tSourcePath,@DestPath);
    #
    my $ActMode = shift ; # misc_ Copy Move Copys Moves
    ## $ActMode
    my $tActMode;
    my $DataRecord = 'yes';
    if ( $ActMode =~ /^misc_/i ){
        $DataRecord = 'no';
        ($tActMode) = ($ActMode =~ /^misc_(\w+)/i) ; # misc_ Copy Move Copys Moves
    } else {
        $tActMode = $ActMode ; # misc_ Copy Move Copys Moves
    }

    my $tDataInfoLogRAM = shift ; #动作执行完后 显示数据记录
    my $tRecordHandOut = shift ;    #上传SQL需要的记录
    my $tKeyName = shift ;            #创建 哈希键的名称
    my $tNoteName = shift ;            #显示记录的中文说明
    my $tJob = shift ;                #料号名 用于SQL记录简化
    my $tFeatures = shift ;            #文件名 或者匹配关键字
    my $tSourcePath = shift ;        #原始路径
    my @DestPath = @_;                #目的路径 可以为 路径 或 路径|文件名
    ## $tFeatures
    ## $tSourcePath
    ## @DestPath

    ####################################
    my %DataInfoLog = %$tDataInfoLogRAM;
    my %RecordHandOut = %$tRecordHandOut;
    ####################################
    my ($tSimpleLog,$tFullLog,) = ('','',);
    if ( $tActMode eq 'Copy' || $tActMode eq 'Move' ){ #单一文件
        #my $CopyNum = 1 ;
        my $tSourceFile = "$tSourcePath/$tFeatures";
        print "tSourceFile:$tSourceFile\n";
        ## $tSourceFile
        if ( -e $tSourceFile ) {
            ## Exists
            if ( $DataRecord eq 'yes' ) {
                $tFullLog .= $tNoteName . ':' ;
            }
            for my $tmpDestPath ( @DestPath ){
                my ($tDestPath,$tDestFolder,$tDestFile,);
                if ( $tmpDestPath =~ /\|\|/ ){
                    my $ReplaceText;
                    ($tDestFolder,$ReplaceText,) = split ('\|\|',$tmpDestPath);
                    my ($ReplaceSourceText,$ReplaceDestText,) = split ('->',$ReplaceText);
                    $tDestFile = $tFeatures;
                    $tDestFile =~ s/$ReplaceSourceText/$ReplaceDestText/i;
                    $tDestPath = $tDestFolder . '/' . $tDestFile;
                }    elsif ( $tmpDestPath =~ /\|/ ){
                    ($tDestFolder,$tDestFile,) = split ('\|',$tmpDestPath);
                    $tDestPath = $tDestFolder . '/' . $tDestFile;
                }    else {
                    $tDestFolder = $tmpDestPath;
                    $tDestFile = $tFeatures;
                    #$tDestPath = $tDestFolder;
                    $tDestPath = $tDestFolder . '/' . $tDestFile;
                }
                &iMkDir($tDestFolder,);
                if ( -d $tSourceFile ) {
                    &iMkDir($tDestPath);
                }

                if ( $DataRecord eq 'yes' ) {
                    unless ( $DataInfoLog{'Log'}{$tKeyName}{'Name'} ) {
                        push (@{$DataInfoLog{List}},$tKeyName);
                        $DataInfoLog{'Log'}{$tKeyName}{'Name'} = $tNoteName;
#                        $DataInfoLog{'Log'}{$tKeyName}{'File'} = $tFeatures;
                        $DataInfoLog{'Log'}{$tKeyName}{'File'} = Gbk_Utf8($tFeatures);
                    }
                }
#                if ( copy( $tSourceFile,"$tDestPath" ) == 1 ) {
                my $tCopyStat;
                if ( $tActMode eq 'Copy' ){
                    $tCopyStat = rcopy( $tSourceFile,$tDestPath );
                } elsif ( $tActMode eq 'Move' ){
                    $tCopyStat = rmove( $tSourceFile,$tDestPath );
                }

                if ( $DataRecord eq 'yes' ) {
                    if ( defined $tCopyStat ) {
                        #unless ( defined $tSimpleLog) {
                            my $tSimFile = $tFeatures;
                            ## aaaaaaaaaaaaaaaa
                            ## $tSimFile
#                                $tSimFile =~  s/^$tJob\.?//gi;
                                $tSimFile =~  s/$tJob\.?//gi;
                            $tSimpleLog = $tSimFile;
                            ## $tSimpleLog
#                        }
                        $tFullLog .= $tDestFile . ',' ;

                        unless ( defined $DataInfoLog{'Log'}{$tKeyName}{'Status'} ) {
                            $DataInfoLog{'Log'}{$tKeyName}{'Status'} = $StatusConv{Yes};
                            $DataInfoLog{'Log'}{$tKeyName}{'Color'} = $StatusColor{Yes};
                        }
                    } else {
                        $DataInfoLog{'Log'}{$tKeyName}{'Status'} = $StatusConv{Err};
                        $DataInfoLog{'Log'}{$tKeyName}{'Color'} = $StatusColor{Err};
                    }
                }
            }
            if ( $DataRecord eq 'yes' ) {
                $tFullLog .= "\n" ;
            }
        } else {
            ## NotExists
            if ( $DataRecord eq 'yes' ) {
                push (@{$DataInfoLog{List}},$tKeyName);
                $DataInfoLog{'Log'}{$tKeyName}{'Name'} = $tNoteName;
#                $DataInfoLog{'Log'}{$tKeyName}{'File'} = $tFeatures;
                $DataInfoLog{'Log'}{$tKeyName}{'File'} = Gbk_Utf8($tFeatures);
                $DataInfoLog{'Log'}{$tKeyName}{'Status'} = $StatusConv{Not};
                $DataInfoLog{'Log'}{$tKeyName}{'Color'} = $StatusColor{Not};
            }
        }

    } elsif ( $tActMode eq 'Copys' || $tActMode eq 'Moves' ){ #匹配文件
        if ( $DataRecord eq 'yes' ) {
            push (@{$DataInfoLog{List}},$tKeyName);
            $DataInfoLog{'Log'}{$tKeyName}{'Name'} = $tNoteName;
        }
        ## $tFeatures
#        my @SourceFileList = grep(/^$tFeatures/i,&iReadDir($tSourcePath,));
        my @SourceFileList = grep(/$tFeatures/i,&iReadDir($tSourcePath,));
        ## @SourceFileList
        #
        if ( scalar(@SourceFileList) == 0 ) {
            if ( $DataRecord eq 'yes' ) {
                $DataInfoLog{'Log'}{$tKeyName}{'Status'} = $StatusConv{Not};
                $DataInfoLog{'Log'}{$tKeyName}{'Color'} = $StatusColor{Not};
                $DataInfoLog{'Log'}{$tKeyName}{'File'} = '';
            }
        } else {
            for my $tFile ( @SourceFileList ) {
                for my $tmpDestPath ( @DestPath ) {
                    my ($tDestPath,$tDestFolder,$tDestFile,);
                    if ( $tmpDestPath =~ /\|\|/ ){
                        my $ReplaceText;
                        ($tDestFolder,$ReplaceText,) = split ('\|\|',$tmpDestPath);
                        my ($ReplaceSourceText,$ReplaceDestText,) = split ('->',$ReplaceText);
                        ## $ReplaceSourceText
                        ## $ReplaceDestText
                        $tDestFile = $tFile;
                        ## $tDestFile
                        $tDestFile =~ s/$ReplaceSourceText/$ReplaceDestText/i;
                        $tDestPath = $tDestFolder . '/' . $tDestFile;
                        ## $tDestFolder
                        ## $tDestFile
                    }    elsif ( $tmpDestPath =~ /\|/ ){
                        ($tDestFolder,$tDestFile,) = split ('\|',$tmpDestPath);
                        $tDestPath = $tDestFolder . '/' . $tDestFile;
                    }    else {
                        $tDestFolder = $tmpDestPath;
                        $tDestFile = $tFeatures;
#                        $tDestPath = $tDestFolder;
                        $tDestPath = $tDestFolder . '/' . $tFile;
                    }
                    &iMkDir($tDestFolder,);
                    ## $tFile
                    my $tSourceFile = "$tSourcePath/$tFile";
                    if ( -d $tSourceFile ) {
                        &iMkDir($tDestPath);
                    }
    #                if ( copy( $tSourceFile,"$tDestPath" ) == 1 ) {
                    my $tCopyStat;
                    ## sgdgdf
                    ## $tSourceFile
                    ## $tDestPath
                    #print '$tSourceFile,$tDestPath =' . "$tSourceFile,$tDestPath\n";

                    if ( $tActMode eq 'Copys' ){
                        $tCopyStat = rcopy( $tSourceFile,$tDestPath );
                    } elsif ( $tActMode eq 'Moves' ){
                        $tCopyStat = rmove( $tSourceFile,$tDestPath );
                    }
                    if ( $DataRecord eq 'yes' ) {
                        if ( defined $tCopyStat ) {
                            unless ( defined $DataInfoLog{'Log'}{$tKeyName}{'Status'} ) {
                                $DataInfoLog{'Log'}{$tKeyName}{'Status'} = $StatusConv{Yes};
                                $DataInfoLog{'Log'}{$tKeyName}{'Color'} = $StatusColor{Yes};
                            }
                            $DataInfoLog{'Log'}{$tKeyName}{'File'} .= "$tFile\n";
                        } else {
                            if ( $DataInfoLog{'Log'}{$tKeyName}{'Status'} ne $StatusConv{Not} ) {
                                $DataInfoLog{'Log'}{$tKeyName}{'Status'} = $StatusConv{Err};
                                $DataInfoLog{'Log'}{$tKeyName}{'Color'} = $StatusColor{Err};
                            }
                        }
                    }

                }
            }
            if ( $DataRecord eq 'yes' ) {
                chomp $DataInfoLog{'Log'}{$tKeyName}{'File'};
                $DataInfoLog{'Log'}{$tKeyName}{'File'} = Gbk_Utf8($DataInfoLog{'Log'}{$tKeyName}{'File'});
            }
            if ( $DataRecord eq 'yes' ) {
                my $tSimFile = $DataInfoLog{'Log'}{$tKeyName}{'File'} ;
                    $tSimFile =~  s/$tJob\.?//gi;
                    $tSimFile =~  s/\n/,/gi;
                $tSimpleLog = $tSimFile;

                $tFullLog = $DataInfoLog{'Log'}{$tKeyName}{'File'} ;
                $tFullLog =~  s/\n/,/gi;
                #$tFullLog .= $tFullLog ;
                $tFullLog = $tNoteName . ':' . $tFullLog . "\n" ;
                #
                #$tFullLog .= "\n" ;
            }
        }
    }

#    $tSimpleLog = Gbk_Utf8($tSimpleLog);
#    $tFullLog = Gbk_Utf8($tFullLog);
#    $RecordHandOut{'SimpleLog'} .= $tSimpleLog . "\n";
#    $RecordHandOut{'FullLog'}     .= $tFullLog . "\n";
    ## end
    ## $tKeyName
    ## $tSimpleLog
    ## $tFullLog
    # --记录目标地址
    $DataInfoLog{'Log'}{$tKeyName}{'DesPath'} = join('\n', @DestPath);
    
    print &Utf8_Gbk("$tNoteName $tKeyName 下发地址") . ":$DataInfoLog{'Log'}{$tKeyName}{'DesPath'}\n";
    
    
    if ( $DataRecord eq 'yes' ) {
        $RecordHandOut{'SimpleLog'} .= $tSimpleLog . ";";
        $RecordHandOut{'FullLog'}     .= $tFullLog . ";\n";
        #####################################
        %$tDataInfoLogRAM = %DataInfoLog ;
        %$tRecordHandOut = %RecordHandOut;
        #####################################
    }
    return();
}

sub getHandOutPath { #获取通用路径及变量 # my %tPath = &getHandOutPath("$tJob"); 
    my $tJob = shift;
    if ( defined $tJob ){
        my %tPath;
        #
        $tPath{'vlJob'}         = lc($tJob);
        $tPath{'vuJob'}         = uc($tJob);
        $tPath{'vCustomerCode'}     = substr($tPath{'vuJob'}, 1,3);
        $tPath{'vJobVer'}           = substr($tPath{'vuJob'},11);
        $tPath{'vSimpleJob'}        = substr($tPath{'vuJob'},4);
        $tPath{'vCurrYear'}         = strftime('%Y', localtime(time));
        $tPath{'vCurrMonth'}        = strftime('%m', localtime(time)) - 0 ;
        $tPath{'vCurrDay'}          = strftime('%d', localtime(time)) - 0 ;
        ############################################用于HDI临时中转工具的地址##################################################
        #临时文件夹 2.57 #文件夹
        if ($SiteCode =~ /^nt_hdi$/i){
            $tPath{'Temp'}                         = $SourceDataRootPath               . '/' . '临时文件夹';
        }elsif($SiteCode =~ /^hz_hdi$/i){
            $tPath{'Temp'}                         = $SourceDataRootPath               . '/' . '临时文件夹' . '/' . '系列资料临时存放区';
        }
        #
        $tPath{'TempCustomer'}                 = $tPath{'Temp'}                    . '/' . $tPath{'vCustomerCode'} . '系列';
        # job 文件夹
        $tPath{'TempJob'}                      = $tPath{'TempCustomer'}            . '/' . $tPath{'vuJob'};
        # job 版本 文件夹
        $tPath{'TempJobVer'}                   = $tPath{'TempJob'}                 . '/' . $tPath{'vJobVer'};
        ############################################用于HDI临时中转工具的地址##################################################
        
        ############################################用于HDI备份的地址##########################################################        
        #设计课
        $tPath{'Design'}                       = $BackupDataPath                   . '/' . 'GCfiles';
        #内部资料
        #$tPath{'Inside'}                       = $tPath{'Design'}                  . '/' . '工程内部资料';
        
        #
        #胜宏CAM资料备份 #文件夹
        #$tPath{'BakCam_SH'}                    = $tPath{'Inside'}                  . '/' . '工程cam资料'           . '/' . '胜宏';
		$tPath{'BakCam_SH'}                       = $tPath{'Design'}                  . '/' . '工程cam资料';
        $tPath{'BakCustomer'}                  = $tPath{'BakCam_SH'}               . '/' . $tPath{'vCustomerCode'} . '系列';
        $tPath{'BakJob'}                       = $tPath{'BakCustomer'}             . '/' . $tPath{'vuJob'};
        ############################################用于HDI备份的地址###########################################################
        
        ############################################用于HDI内层完成上传资料地址#################################################
        # --HDI新服务器地址
        $tPath{'HDI'}                          = $DestDataRootPath                 . '/' . 'GCfiles';
        # --内层Tgz（*-inn）
        $tPath{'InnTgzFormal'}                 = $tPath{'HDI'}                     . '/' . 'HDI全套tgz';
        $tPath{'InnTgzFormalCustomer'}         = $tPath{'InnTgzFormal'}            . '/' . $tPath{'vCustomerCode'} . '系列';
        
        # --工程辅助资料
        #辅助资料 文件夹 #短料号名，包含通孔（见http://192.168.2.120:82/zentao/story-view-1315.html）
        $tPath{'Program'}                      = $tPath{'HDI'}                     . '/' . 'Program';
        $tPath{'AidSH'}                        = $tPath{'Program'}                 . '/' . '工程辅助资料';
        $tPath{'AidCustomer'}                  = $tPath{'AidSH'}                   . '/' . $tPath{'vCustomerCode'}     . '系列';
        $tPath{'AidSimpleJob'}                 = $tPath{'AidCustomer'}             . '/' . $tPath{'vuJob'};
        
        # --工程盲孔资料
        $tPath{'Mechanical'}                   = $tPath{'Program'}                 . '/' . 'Mechanical';   
        $tPath{'Mechanical_Drl'}               = $tPath{'Mechanical'}              . '/' . '工程钻孔程式';           
        $tPath{'MecCustomer'}                  = $tPath{'Mechanical_Drl'}          . '/' . $tPath{'vCustomerCode'}     . '系列';
        $tPath{'MecJob'}                       = $tPath{'MecCustomer'}             . '/' . $tPath{'vuJob'};
        # --埋孔对应资料目录    
        $tPath{'MkJob'}                        = $tPath{'MecJob'}                  . '/' . '盲孔';
        
        # --工程裁磨资料地址
        $tPath{'PnlRout'}                      = $tPath{'HDI'}                     . '/' . 'PnlRout';
        $tPath{'CMCustomer'}                   = $tPath{'PnlRout'}                 . '/' . $tPath{'vCustomerCode'}     . '系列';
        $tPath{'CmJob'}                        = $tPath{'CMCustomer'}              . '/' . $tPath{'vuJob'};
        
        # --测量涨缩资料地址
        $tPath{'ScaleCustomer'}                = $tPath{'PnlRout'}                 . '/' . '长7短5涨缩测量数据' . '/'  . $tPath{'vCustomerCode'}  . '系列';
        $tPath{'ScaleJob'}                     = $tPath{'ScaleCustomer'}           . '/' . $tPath{'vuJob'};
		
        # --测量X-RAY资料地址
        $tPath{'PnlRout'}                      = $tPath{'HDI'}                     . '/' . 'PnlRout';
		$tPath{'PnlRout_xray'}                 = $tPath{'PnlRout'}                 . '/' . 'X-RAY测量数据';
        $tPath{'XrayCustomer'}                 = $tPath{'PnlRout_xray'}            . '/' . $tPath{'vCustomerCode'}     . '系列';
        $tPath{'XrayJob'}                      = $tPath{'XrayCustomer'}            . '/' . $tPath{'vuJob'};
        ############################################用于HDI内层完成上传资料地址#################################################
        
        ############################################用于HDI外层完成上传资料地址#################################################
        # --全套Tgz
        $tPath{'AllTgzFormal'}                 = $tPath{'HDI'}                     . '/' . 'HDI全套Tgz';
        $tPath{'TgzFormalCustomer'}            = $tPath{'AllTgzFormal'}            . '/' . $tPath{'vCustomerCode'} . '系列';
        
        # --文字喷漆资料---选化板不可喷墨
        #喷墨  ## 文件夹+周期+备注
        $tPath{'Silk'}                         = $tPath{'HDI'}                     . '/' . 'Silk';
        $tPath{'InkJet'}                       = $tPath{'Silk'}                    . '/' . '文字喷墨';
        $tPath{'InkJetCustomer'}               = $tPath{'InkJet'}                  . '/' . $tPath{'vCustomerCode'}     . '系列';
        
        # --劲鑫字符喷墨资料
        $tPath{'SilkJinXin'}                   = $tPath{'Silk'}                    . '/' . '劲鑫文字喷墨';
        $tPath{'SilkJinXinCus'}                = $tPath{'SilkJinXin'}              . '/' . $tPath{'vCustomerCode'}     . '系列';
        
        # --镭雕资料
        $tPath{'LeiDiao'}                       = $tPath{'Silk'}                    . '/' . '镭雕资料';
        $tPath{'LeiDiaoCustomer'}               = $tPath{'LeiDiao'}                 . '/' . $tPath{'vCustomerCode'}     . '系列';
        $tPath{'LeiDiaoJob'}                    = $tPath{'LeiDiaoCustomer'}         . '/' . $tPath{'vuJob'};
        
        # --外检AVI资料
        $tPath{'outerAvi'}                   = $tPath{'AllTgzFormal'}                    . '/' . 'avi 资料';
        $tPath{'OuterAVICus'}                = $tPath{'outerAvi'}              . '/' . $tPath{'vCustomerCode'}     . '系列';
        
        # --LDI资料-精度2.0Micron
        $tPath{'Ldi'}                          = $tPath{'HDI'}                      . '/' . 'LDI';
        $tPath{'OrbLdi'}                       = $tPath{'Ldi'}                      . '/' . '奥宝LDI';
        $tPath{'OrbLdiCustomer'}               = $tPath{'OrbLdi'}                   . '/' . $tPath{'vCustomerCode'}     . '系列';
        $tPath{'OrbLdiJob'}                    = $tPath{'OrbLdiCustomer'}           . '/' . $tPath{'vuJob'};
        
        # --LDI资料-精度1.5Micron
        $tPath{'OrbLdi_80F'}                    = $tPath{'Ldi'}                      . '/' . '80F奥宝LDI';
        $tPath{'OrbLdi_80FCustomer'}            = $tPath{'OrbLdi_80F'}               . '/' . $tPath{'vCustomerCode'}     . '系列';
        $tPath{'OrbLdi_80FJob'}                 = $tPath{'OrbLdi_80FCustomer'}       . '/' . $tPath{'vuJob'};
        ############################################用于HDI外层完成上传资料地址#################################################
        
        $tPath{'DrlLpinnOutLogFile'}           = '//192.168.2.57/Home/Log/DEL_DrlLpinnOut.log' ;
        $tPath{'DrlLpinnOutBakLogFile'}        = '//192.168.2.57/Home/Log/DEL_DrlLpinnOut_Bak.log' ;
        $tPath{'DrlLpinnOutGeneralLogFile'}    = '//192.168.2.57/Home/Log/General_DrlLpinnOut.log' ;
        $tPath{'DrlLpinnOutGeneralBakLogFile'} = '//192.168.2.57/Home/Log/General_DrlLpinnOut_Bak.log' ;
        if ( $RunMode eq 'test' ) {
            $tPath{'DrlLpinnOutLogFile'}       = $SourceDataRootPath . '/DEL_DrlLpinnOut.log' ;
            $tPath{'DrlLpinnOutBakLogFile'}    = $SourceDataRootPath . '/DEL_DrlLpinnOut_Bak.log' ;
            $tPath{'DrlLpinnOutGeneralLogFile'}     = $SourceDataRootPath . '/General_DrlLpinnOut.log' ;
            $tPath{'DrlLpinnOutGeneralBakLogFile'}  = $SourceDataRootPath . '/General_DrlLpinnOut_Bak.log' ;
        }
        return(%tPath);
    } else {
        warn "Not's defined variable JOB" ;
        return();
    }
}

sub UploadLogToMySql {  #上传数据库 # &UploadLogToMySql("inner",$tPath{vuJob},$RecordHandOut{SimpleLog},$RecordHandOut{FullLog},); # inner outer all backup delete

    my $HandOutType = shift; #内层(inner) 外层(outer) 全套(all)',
    my $tJob = shift; #$tPath{vuJob}
    my $RecordSimpleLog = shift; #$RecordHandOut{SimpleLog}
    my $RecordFullLog = shift; #$RecordHandOut{FullLog}

    my $CurrDate = strftime "%Y-%m-%d", localtime(time);
    my $CurrTime = strftime "%H:%M:%S", localtime(time);
    my $CurrDateTime = $CurrDate . ' ' . $CurrTime;
#    our $CurrHost = `hostname`;
#    chomp $CurrHost;
    my $CurrHost  = $ENV{COMPUTERNAME};
    my $LoginUser = $ENV{USERNAME};
    ## %RecordHandOut
    $RecordSimpleLog =~ s/\;+/;/gi;
    $RecordSimpleLog =~ s/^\;+//gi;
    #
    $RecordFullLog =~ s/(\r|\n)+//gi;
    $RecordFullLog =~ s/^;+//gi;
    $RecordFullLog =~ s/;+/;/gi;
    $RecordFullLog =~ s/,;/;/gi;
    $RecordFullLog =~ s/;/;\n/gi;
    ## %RecordHandOut

    &AliasMySqlRun('Link',"engineering");
    my $SqlCmd = qq{INSERT logs_cam_qa_hand_out
    (job_name,hand_out_type,hand_out_simple_log,hand_out_full_log,hand_out_date,hand_out_time,hand_out_datetime,hostname,win_user,logs_type,org_code)
    VALUES
    ('$tJob','$HandOutType','$RecordSimpleLog','$RecordFullLog','$CurrDate','$CurrTime','$CurrDateTime','$CurrHost','$LoginUser','$RunMode','$org_code') ;
    };

    my $tResult = &AliasMySqlRun('Set',"$SqlCmd");
    &AliasMySqlRun('Finish');
    &AliasMySqlRun('Unlink');
}

sub AliasMySqlRun {  #数据库连接操作
    my $tActMode = shift;
    if ( $tActMode =~ /^Link$/i ){
        my ($MySqlServer,$MySqlPort) = ("192.168.2.19","3306");
        my $MySqlAccessingDatabase = shift || "project_status";
        my ($MySqlUserId,$MySqlPassword) = ("root","k06931!");
        $MySqlProcess = DBI->connect("DBI:mysql:$MySqlAccessingDatabase:$MySqlServer:$MySqlPort",$MySqlUserId,$MySqlPassword) ;#or die "$MySqlProcess->errstr";
        $MySqlProcess->do("SET NAMES utf8");
    } elsif ( $tActMode =~ /^Get$/i ){
        my $ActExecute = shift;
        $MySqlExecute = $MySqlProcess->prepare("$ActExecute");
        $MySqlExecute->execute() or die "无法执行SQL语句:$MySqlProcess->errstr";
        my @tArray;
        while (my @tRow = $MySqlExecute->fetchrow_array){
#            print scalar(@tRow) . " =" . "@tRow\n";
            if ( scalar(@tRow) > 1 ){
                push (@tArray,\@tRow);
            }else{
                push (@tArray,$tRow[0]);
            }

        }
        #my @tArray = $MySqlExecute->fetchrow_array();
#        print "tArray=@tArray\n";
        if ( scalar(@tArray) > 1 ) {
            return (\@tArray);
        } else {
            return ($tArray[0]);
        }
        return ($MySqlExecute);        
    # --调用MySQL存储过程
    } elsif ( $tActMode =~ /^Call$/i) {
        my $ActExecute = shift;
        my ($callSql,$selSql) = split(';', $ActExecute);
        # --呼叫接口
        $MySqlProcess->do($callSql);
        # --接收返回值
        my $p_Receive = $MySqlProcess->selectrow_array($selSql);
        return ($p_Receive);        
    } elsif ( $tActMode =~ /^Set$/i ){
        my $ActExecute = shift;
        $MySqlExecute = $MySqlProcess->prepare("$ActExecute");
        $MySqlExecute->execute() or die "无法执行SQL语句:$MySqlProcess->errstr";
        return ($MySqlExecute);
    } elsif ( $tActMode =~ /^Finish$/i){
        $MySqlExecute->finish;
    } elsif ( $tActMode =~ /^Unlink$/i){
        $MySqlProcess->disconnect; #断开数据库连接
    }
}

sub getCurrDateTime {  #获取当前时间
    my $CurrDateTime = strftime "%Y-%m-%d %H:%M:%S", localtime(time);
    return($CurrDateTime);
}

sub iGetFileMD5 {  #获取文件MD5值 #my $tFileMd5 = &iGetFileMD5($file1,); #my @FileMd5 = &iGetFileMD5($file1,$file2,);
#    use Digest::file qw(digest_file_hex);
#    &iLoadModules("Digest::file");
    my @NewFileMd5;
    for ( @_ ) {
        push( @NewFileMd5,digest_file_hex( $_ ,'MD5') );
    }
    ### @NewFileMd5
    if ( defined $NewFileMd5[0] ){
        if ( scalar(@NewFileMd5) > 1 ){
            return(@NewFileMd5);
        } else {
            return($NewFileMd5[0]);
        }
    } else {
        return();
    }    
}

sub iTraverseFindTgz {  #遍历查找 my %FindFileList = &iTraverseFindTgz($SearchFilterKey,@FindPath);
    my $SearchFilterKey = shift ;
    my @FindPath = @_;
    my @SearchFilterKeyArray = split(/\*+/,$SearchFilterKey);
    if ($SearchFilterKeyArray[0] eq "") {
        shift @SearchFilterKeyArray;
    }

    my $SearchKey = '.*' . join('.*',@SearchFilterKeyArray) .  '.*'  . '\.tgz$';
    print "@FindPath\n $SearchKey\n";
    

    undef %ListHash;
    
    # --当目录为空时
    if (scalar(@FindPath) == 0)
    {
        return (%ListHash);
    }
    
    my $tListNum = 0;
    find( sub {
                if ( -f $File::Find::name ) {
                    if ( $File::Find::name =~ /$SearchKey/i ) {
                        ### FILE: $_
                        ### Dir: $File::Find::dir
                        ### Path: $File::Find::name
                        my $tTmpItem = $_;
                            $tTmpItem =~ s/\.tgz//ig;
                        push (@{$ListHash{"List"}},$tTmpItem);
                        $ListHash{'Num'}{$tListNum} = $File::Find::name;
#                        $ListHash{"ListItem"}{$tTmpItem} = $File::Find::name;
                        {
                            
                            my $tMonthDayDir = basename($File::Find::dir);
                            my $tYearDir  = basename( dirname( dirname( $File::Find::dir ) ) );
                            my ($tYear) = ( $tYearDir =~ /^(\d{4})/ );
                            $ListHash{'Date'}{$tListNum} = $tYear . '.' . $tMonthDayDir ;
                        }
                        $tListNum++;
                    }
                }
            }
        , @FindPath );

    ### %ListHash
    #    %ListHash: {
    #        Date => {
    #            0 => '2018.10.11',
    #            1 => '2018.10.12'
    #        },
    #        List => [
    #            'q00810gn089a1-inn',
    #            'q00810gn089a1-inn'
    #        ],
    #        Num => {
    #            0 => 'E:/Test/Dest/vgt$/设计课/外部资料/工程部外部取读资料/胜宏资料/内层AOI扫描资料/2018年/10月/10.11/q00810gn089a1-inn.tgz',
    #            1 => 'E:/Test/Dest/vgt$/设计课/外部资料/工程部外部取读资料/胜宏资料/内层AOI扫描资料/2018年/10月/10.12/q00810gn089a1-inn.tgz'
    #        }
    #    }
    return(%ListHash);
}

#/****************************
# 函数名: uploadTime
# 功  能: 调用接口更新工程订单制作时间
# 参  数: 型号名、字段名
# 返回值: None
#****************************/
sub uploadTime
{
    my $tJob = shift; #$tPath{vuJob}
    my $SubmitVal = shift; # (调用时直接传入需要更新的字段名 eg: icheckfinish_time ： 内层审核完成时间, ocheckfinish_time：外层审核完成时间 )
    
    # --连接数据库
    &AliasMySqlRun('Link',"project_status");
    
    # --更新对应时间
    my $SqlCmd = qq{CALL EngOrderStatusSubmit ('$tJob','$SubmitVal', '', '', '', '$ENV{'USERNAME'}', \@result);SELECT \@result};
    my $SubmitResult = (&AliasMySqlRun('Call',"$SqlCmd") || "");
    
    print &Utf8_Gbk("更新($SubmitVal)栏位时间返回结果：" . $SubmitResult);
    
    # --断开连接
    &AliasMySqlRun('Unlink');
}

#/****************************
# 函数名: uploadTime
# 功  能: 上传工具下发记录
# 参  数: 型号名
# 返回值: None
#****************************/
sub uploadToolsIssue
{
    my $tJob = shift;
    my $joinType = "";
    my $IssUeResult = undef;
    my $layerCount = substr($tJob, 4,2);
    &AliasMySqlRun('Link',"project_status");
    
    # --判断job在数据库是否存在
    my $SqlCmd = qq{SELECT 
                        elog.hand_out_type                        
                    FROM
                        project_status_jobmanage psj
                        INNER JOIN engineering.logs_cam_qa_hand_out elog ON psj.job = elog.job_name 
                    WHERE
                        elog.hand_out_full_log <> "" 
                        AND psj.job = '$tJob'};
                        
    # --获取select数组数据
    my $jobLog = (&AliasMySqlRun('Get',"$SqlCmd") || "");
    if (scalar (@$jobLog) == 0)
    {
        if ($jobLog ne ""){
            $joinType = $jobLog;
        }
    }else{
        for my $list (@$jobLog){
            $joinType .= $list . '+';     
        }
    }
    
    # 根据拼接的log信息，判断下发的资料阶段
    if (($joinType =~ /outer/i  and ($joinType =~ /inner/i or $layerCount <= 2)) or $joinType =~ /all/i)
    {
        $IssUeResult = '全套已下发';
    }elsif($joinType !~ /outer/i  and $joinType =~ /inner/i){
        $IssUeResult = '仅下发了内层';
    }elsif($joinType =~ /outer/i  and $joinType !~ /inner/i){
        $IssUeResult = '仅下发了外层';
    }else{
        $IssUeResult = '其它';
    }
    
    print &Utf8_Gbk("此型号工具下发情况：" . $IssUeResult ."！");
    # --更新对应栏位数据（上面的查询用的 inner join 不需要再次判断更新的表中料号是否存在）
    if (defined $IssUeResult){
        # $SqlCmd = qq{UPDATE project_status_jobmanage SET tools_issue = '$IssUeResult' WHERE job = '$tJob';};
        # --调用接口更新对应字段信息 (jobName udaName 型号名及UDA名为必须参数 udaContent  dataType isUpdate userName为可选参数)
        my $SqlCmd = qq{CALL EngOrderStatusSubmit ('$tJob', 'tools_issue', '$IssUeResult', 'VARCHAR', 'Y', '$ENV{'USERNAME'}', \@result);SELECT \@result};
        my $SubmitResult = (&AliasMySqlRun('Call',"$SqlCmd") || "");
        
        print &Utf8_Gbk("更新(tools_issue)栏位数据返回结果：" . $SubmitResult);
    }
    
    # --断开连接
    &AliasMySqlRun('Finish');
    &AliasMySqlRun('Unlink');
}

#/****************************
# 函数名: GetEcnData 
# 功  能: 根据料号获取ECN变更系统中的更改记录 2022.08.02新增，暂时未调试
# 参  数: 型号名、字段名
# 返回值: None
#****************************/
sub GetEcnData
{
    my $tJob = shift; #$tPath{vuJob}
    my $SubmitVal = shift; # (调用时直接传入需要更新的字段名 eg: icheckfinish_time ： 内层审核完成时间, ocheckfinish_time：外层审核完成时间 )
    
    # --连接数据库
    &AliasMySqlRun('Link',"vgt_ecn_hdi");
    
	# --判断job在数据库是否存在
    my $SqlCmd = qq{SELECT SerialCode, ChangeDate, ShortJob, JobVer, AfterJob, BeforeJob 
        FROM  vgt_ecn_hdi.change_notice 
        WHERE IsDelete = '0' and  AfterJob = '$tJob'};		          
    # --获取select数组数据
    my $ecnLog = (&AliasMySqlRun('Get',"$SqlCmd") || "");
	print $ecnLog;
    # --更新对应时间
    print &Utf8_Gbk("获取ECN系统信息");
    # --断开连接
    &AliasMySqlRun('Finish');
    &AliasMySqlRun('Unlink');
}


#/************************
# 函数名: Messages
# 功  能: Message窗口
# 参  数: NONE
# 返回值: NONE
#***********************/
sub Messages
{
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
# 函数名: checkERPjob
# 功  能: 同步ERP信息，检测料号是否存在 
# 参  数: $dbc, $jobName
# 返回值: 1 0r 0
#***********************/
sub checkERPjob
{
    my ($dbc, $jobName) = @_;
    my $Sel_Info = "SELECT COUNT(a.TC_AAC01) FROM TC_AAC_FILE a WHERE a.TC_AAC01=upper('$jobName')";
    my $Sel_Sth = $dbc ->prepare($Sel_Info);
    $Sel_Sth ->execute or die "\nExecute error: $DBI::err .... $DBI::errstr\n";
    # --获取SQL数据
    my $jobCount=$Sel_Sth ->fetchrow_array();
    
    # --返回数据列表 (0:料号不存在 非0：料号存在)
    return $jobCount;    
}

#/************************
# 函数名: getWeekFromat
# 功  能: 获取周期格式 
# 参  数: $dbc, $jobName
# 返回值: 1 0r 0
#***********************/
sub getWeekFromat
{
    my ($dbc, $jobName) = @_;
    my $sql = "select a.item_name 料号名,
                        d.customer_name 客户名,
                        c.customer_job_name_ 客户品名,
                        h.value 工厂,
                        i.value 订单类型,
                        j.value 出货方式,
                        round(c.delivery_width_ / 39.37, 3) 出货尺寸宽,
                        round(c.delivery_length_ / 39.37, 3) 出货尺寸长,
                        round(f.customer_thickness / 39.37,3) 成品板厚,
                        k.value  表面处理,
                        l.value 阻焊次数,
                        m.value 阻焊面别,
                        (select enu.value
                         from vgt_hdi.items sm   
                        inner join vgt_hdi.mask_layer sm2
                           on sm.item_id = sm2.item_id
                          and sm.last_checked_in_rev = sm2.revision_id
                        inner join vgt_hdi.mask_layer_da sm3
                           on sm2.item_id = sm3.item_id
                          and sm2.revision_id = sm3.revision_id
                        inner join vgt_hdi.enum_values enu
                           on sm3.sm_color_ = enu.enum
                        where sm.root_id = a.root_id
                          and sm2.mask_type = 0
                          and enu.enum_type = 214
                          and enu.value is not null
                          and rownum = 1) 阻焊颜色,
                        n.value 字符次数,
                        o.value 字符面别,
                        (select enu.value
                           from vgt_hdi.items ss   
                          inner join vgt_hdi.mask_layer ss2
                             on ss.item_id = ss2.item_id
                            and ss.last_checked_in_rev = ss2.revision_id
                          inner join vgt_hdi.mask_layer_da ss3
                             on ss2.item_id = ss3.item_id
                            and ss2.revision_id = ss3.revision_id
                          inner join vgt_hdi.enum_values enu
                             on ss3.ss_color_ = enu.enum
                          where ss.root_id = a.root_id
                            and ss2.mask_type = 2
                            and enu.enum_type = 1025
                            and enu.value is not null
                            and rownum = 1) 字符颜色,
                           decode(c.has_qr_code_,0,'无',1,'有') 是否有雷雕,
                           round(g.pcb_size_x/39.37,3) PCS_X,
                           round(g.pcb_size_y/39.37,3) PSC_Y,
                           round(c.set_size_x_/39.37,3) SET_X,
                           round(c.set_size_y_/39.37,3) SET_Y,
                           b.num_arrays PNL中的Set数,
                           c.pcs_per_set_ SET中的Pcs数,
                           p.value 周期面别,
                           q.value 周期格式,
                           r.value 大板Vcut,
                           s.value UL面别,
                           t.value UL标记,
                           c.es_elic_,
                decode(c.sm_plug_type_,0,'否',1,'否',2,'是',3,'是')  是否阻焊塞,
                (select decode(proda.resin_plug_type_,0,'否',1,'否',2,'是')
                    from vgt_hdi.public_items pb
                    inner join vgt_hdi.process pro
                       on pb.item_id = pro.item_id
                      and pb.revision_id = pro.revision_id
                    inner join vgt_hdi.process_da proda
                       on pro.item_id = proda.item_id
                      and pro.revision_id = proda.revision_id
                    where pb.root_id = a.root_id
                      and pro.proc_subtype = 29)  是否树脂塞
                   from vgt_hdi.items a
                  inner join vgt_hdi.job b
                     on a.item_id = b.item_id
                    and a.last_checked_in_rev = b.revision_id
                  inner join vgt_hdi.job_da c
                     on b.item_id = c.item_id
                    and b.revision_id = c.revision_id
                  inner join vgt_hdi.customer d
                     on b.customer_id = d.cust_id
                  inner join vgt_hdi.items e
                     on a.root_id = e.root_id
                  inner join vgt_hdi.stackup f
                     on e.item_id = f.item_id
                    and e.last_checked_in_rev = f.revision_id
                  inner join vgt_hdi.part g
                     on b.item_id = g.item_id
                    and b.revision_id = g.revision_id
                  inner join vgt_hdi.enum_values h
                     on c.site_ = h.enum
                  inner join vgt_hdi.enum_values i
                     on c.order_type_ = i.enum
                  inner join vgt_hdi.enum_values j
                     on c.delivery_unit_ = j.enum
                  inner join vgt_hdi.enum_values k
                     on c.surface_finish_ = k.enum
                  inner join vgt_hdi.enum_values l
                     on c.sm_print_times_ = l.enum
                  inner join vgt_hdi.enum_values m
                     on c.sm_side_ = m.enum 
                  inner join vgt_hdi.enum_values n
                     on c.ss_print_times_ = n.enum
                  inner join vgt_hdi.enum_values o
                     on c.ss_side_ = o.enum 
                  inner join vgt_hdi.enum_values p
                     on c.dc_side_ = p.enum
                  inner join vgt_hdi.enum_values q
                     on c.dc_type_ = q.enum
                  inner join vgt_hdi.enum_values r
                     on c.rout_process_ = r.enum 
                  inner join vgt_hdi.enum_values s
                     on c.ul_side_ = s.enum
                  inner join vgt_hdi.enum_values t
                     on c.ul_mark_ = t.enum                     
                  where a.item_name = '$jobName'
                     and h.enum_type = 1057
                    and i.enum_type = 1007
                    and j.enum_type = 1029
                    and k.enum_type = 1000
                    and l.enum_type = 1114
                    and m.enum_type = 1015
                    and n.enum_type = 1113
                    and o.enum_type = 1038
                    and p.enum_type = 1022
                    and q.enum_type = 1001
                    and r.enum_type = 1045
                    and s.enum_type = 1020
                    and t.enum_type = 1019";
    my $sth = $dbc->prepare($sql);
    $sth->execute() or die "无法执行SQL语句:$dbc->errstr";
    # --循环所有行数据
    my @recs = $sth->fetchrow_array();
    print ("XXXX:".encode('gbk',$recs[23])."\n\n");
    return encode('gbk',$recs[23]);
}

__END__
2019.08.17更新如下：
作者：柳闯
版本：3.1
内层审核完成下发动作包括：
1.自动上传$JOB-inn.tgz至“HDI全套Tgz"目录对应的系列下；
2.自动上传所有$JOB开头的文本文件至“Program/工程辅助”目录下，包括w、w开头的文本；
3.自动上传根通孔'.out','.inn','.shizuan'文件至“ Mechanical"目录下，如有转完档的.write 激光孔文档。自动创建”盲孔“目录上传转完档的文本至对应”盲孔“系列目录下；
4.上传内层审核完成时间；


外层审核完成下发动作包括：
1.自动上传全套的tgz至“HDI全套Tgz"目录下，当"$JOB-inn.tgz"存在时，先删除再上传；
2.通孔钻带重新上传一遍；
3.自动上传文字喷墨资料（为文件夹）至”Silk/文字喷墨"对应系列里；
4.自动上传内外层LDI资料（目录下不区分内外层）至“LDI”对应系列里；
5.所有临时资料全部归档至2.33文件服务器；并删除临时目录下的资料("\\192.168.2.57\临时文件夹"对应系列文件)
6.上传外层审核完成时间；

以上需求链接地址：http://192.168.2.120:82/zentao/story-view-282-3.html

2019.08.17更新如下：
作者：柳闯
版本：3.2
1.增加上传内外层审核时间

2019.08.17更新如下：
作者：柳闯
版本：3.3
1.修改使用网络Perl环境直接呼出主程式（不需要编译exe执行）

2019.08.17更新如下：
作者：柳闯
版本：3.4
1.修改钻带输出位置；
2.修改内外层审核时间无法上传的bug；

2019.09.17更新如下：
作者：柳闯
版本：3.5
1.有镭射的料号，不需要放inn和out，只放镭射层，通孔才放inn和out，否则放到辅助里面
2.注释了以下代码 ：
#if ( defined $ENV{RUNMODE} ){
#    $RunMode = $ENV{RUNMODE} ;
#}

2019.09.18更新如下：
作者：柳闯
版本：3.6
1.自己都不知道改进了什么，可能只是调整了格式

2019.09.23更新如下：
作者：柳闯
版本：3.7
1.外层下发后存档 
2.修复外层下发时无法下发外层LDI的情况 
3.修复下发外层后无法更新对应的外层审核时间
4.外层备份 料号名.lp 也要放到辅助里，统一再放一下   料号名.* 到辅助
匹配规则：^(?:'.$tJob.'\.(?:b.+|d.+|inn\d+|lp(?:.+)?|rout(?:.+)?|s.+|ww|sz(?:.+)?)|w(?:.+)?)$

2019.09.28更新如下：
作者：柳闯
版本：3.8
1.新增WW1是一次成型 SZ23.DQ是埋孔树脂导气板 SZ23.XM是埋孔树脂网板 CDS CSC CD-S CS-C 控深钻
匹配规则：'^(?:'.$tJob.'\.(?:b.+|d.+|inn\d+|lp(?:.+)?|rout(?:.+)?|s.+|ww(.+)?|sz(?:.+)?|w(?:.+)?|cd(-)?(c|s)(.+)?|))|(sz.+xm|KS.+dq)$'

作者：柳闯
版本：3.9
1.新增劲鑫字符打印机资料下发逻辑

作者：柳闯
版本：4.0
1.新增裁磨资料下发逻辑

2019.08.17更新如下：
作者：柳闯
版本：4.1
1、所有工具下发加入了ERP料号ERP中是否可查的检测，如ERP中不存在刚给出提醒
2、修复外层工具下发时 其它辅助程式(otherDrl) 包含了全套tgz资料 （实则不需要）

2019.08.17更新如下：
作者：柳闯
版本：4.3
变更链接:http://192.168.2.120:82/zentao/story-view-1315.html
1、HDI通孔下发至工程辅助资料夹；
2、外层下发时，移除文件

2020.07.06更新如下：
作者：柳闯
版本：4.4
变更链接:http://192.168.2.120:82/zentao/story-view-1553.html
1、在内层下发时，下发 *.tk.ykj此类工具。

2020.8.11更新如下：
作者：柳闯
版本：4.5
1、通孔钻带.out变更为.drl

2020.08.28更新如下：
作者：柳闯
版本：4.6
1、l888test343a1.lr6-7 这种后缀的下发资料识别不了，内层时下发到辅助资料文件夹（周燕要求）

2020.10.30更新如下：
作者：柳闯
版本：4.7
变更链接：http://192.168.2.120:82/zentao/story-view-2261.html
1、下发2nd及2nd.inn资料，内层时下发到辅助资料文件夹（周燕要求） 

2020.12.07更新如下：
作者：柳闯
版本：5.0
变更链接：http://192.168.2.120:82/zentao/story-view-2414.html
1、HDI文件备份用目录变更（2.33->2.174）

2020.12.09更新如下：
作者：柳闯
版本：5.1&5.2
变更链接：http://192.168.2.120:82/zentao/story-view-2417.html
1、审核avi 资料自动下发

2021.05.05更新如下：
作者：宋超
版本：5.3
1.南通的资料下发，从南通的临时文件夹，下发到HDI

2021.06.10更新如下：
作者：柳闯
版本：5.3
变更链接：http://192.168.2.120:82/zentao/story-view-3148.html
1、增加自动默认当前型号（方便审核guide中自动下发）


2021.06.10更新如下：
作者：柳闯
版本：5.4
变更链接：http://192.168.2.120:82/zentao/story-view-3161.html
1、增加汇总下发的log并整理出当前状态，更新主表tools_issue字段（全套已下发、仅下发了内层、仅下发了外层）

2021.06.22更新如下：
作者：柳闯
版本：5.5
1、整合南通与HDI的下发逻辑

2021.06.25更新如下：
作者：柳闯
版本：5.6
1、CAM审核自动下发 涨缩测量的数据 YH_PY_Cor资料 

2021.07.13更新如下：
作者：柳闯
版本：5.7
1、修复因 limit 2 导致的下发状态更新异常；
2、增加单面板的下发逻辑

2021.08.05更新如下：
作者：柳闯
版本：5.8
1、新增双精度奥宝LDI资料自动下发（2.0Micron & 1.5Micron）
2、同时兼容过渡期间的旧标准存储工具

2021.08.06更新如下：
作者：柳闯
版本：5.9
1、双面板下发外层时，同时下发对应的钻孔程式；

2021.08.19更新如下：
作者：柳闯
版本：6.0
1、修复W开开头的型号会在内层下发资料时一并下发所有资料至辅助层；

2021.09.02更新如下：
作者：柳闯
版本：6.1
1、取消了 \\192.168.2.174\GCfiles\Program\Mechanical\工程钻孔程式 目录下的所有下发逻辑（此目录已禁止访问）
http://192.168.2.120:82/zentao/story-view-3463.html

2021.11.16更新如下：
作者：柳闯
版本：6.2
1、增加盖孔减铜LDI资料内层自动下发时下发

2021.12.30更新如下：
作者：柳闯
版本：6.3
1、外层工具下发，自动下发镭雕资料 http://192.168.2.120:82/zentao/story-view-3833.html

2022.3.1更新如下：
何瑞鹏
版本：6.4
1、线路周期LDI下发资料防呆http://192.168.2.120:82/zentao/story-view-3981.html


2022.04.06更新如下：
柳闯
版本：6.5
1.2.57目录下存储目录结构发生变化；

2022.08.02 更新如下：
宋超
版本：6.6
1.183系列下发时的ECN系统对接；http://192.168.2.120:82/zentao/story-view-4412.html
目前针对所有料号

2023.01.03
宋超
版本：6.7
1.增加外层盖孔下发；
2.增加内层辅助下发；
3.增加蓝胶带文件夹下发；
http://192.168.2.120:82/zentao/story-view-4956.html

