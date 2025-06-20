#

our $_CAMSOFT = 'Genesis'; # Genesis InCAM #if ( $_CAMSOFT eq "InCAM" ) {} #if ( $_CAMSOFT eq "Genesis" ) {}
if ( defined $ENV{'INCAM_PRODUCT'} ) {
	$_CAMSOFT = 'InCAM';
}


##############								编码转换						#####################################################################

=h #decode (解码字节流) #encode (编码字节流) 字节流(Perl字符串)

Perl从5.6开始已经开始在内部使用utf8编码来表示字符，也就是说对中文以及其他语言字符的处理应该是完全没有问题的。我们只需要利用好Encode这个模块便能充分发挥Perl的utf8字符的优势了。

下面就以中文文本的处理为例进行说明，比如有一个字符串"测试文本"，我们想要把这个中文字符串拆成单个字符，可以这样写：

use Encode;
$dat="测试文本";
$str=decode("gb2312",$dat);
@chars=split //,$str;
foreach $char (@chars) {
print encode("gb2312",$char),"/n";
}

结果大家试一试就知道了，应该是令人满意的。

这里主要用到了Encode模块的decode、encode函数。要了解这两个函数的作用我们需要清楚几个概念：

1、Perl字符串是使用utf8编码的，它由Unicode字符组成而不是单个字节，每个utf8编码的Unicode字符占1~4个字节（变长）。

2、进入或离开Perl处理环境（比如输出到屏幕、读入和保存文件等等）时不是直接使用Perl字符串，而需要把Perl字符串转换成字节流，转换过程中使用何种编码方式完全取决于你（或者由Perl代劳）。一旦Perl字符串向字节流的编码完成，字符的概念就不存在了，变成了纯粹的字节组合，如何解释这些组合则是你自己的工作。

我们可以看出如果想要Perl按照我们的字符概念来对待文本，文本数据就需要一直用Perl字符串的形式存放。但是我们平时写出的每个字符一般都被作为纯ASCII字符保存（包括在程序中明文写出的字符串），也就是字节流的形式，这里就需要encode和decode函数的帮助了。

encode函数顾名思义是用来编码Perl字符串的。它将Perl字符串中的字符用指定的编码格式编码，最终转化为字节流的形式，因此和Perl处理环境之外的事物打交道经常需要它。其格式很简单：
$octets = encode(ENCODING, $string [, CHECK])

$string：　　Perl字符串
encoding：　是给定的编码方式
$octets:　　是编码之后的字节流
check:　　　表示转换时如何处理畸变字符（也就是Perl认不出来的字符）。一般不需使用

编码方式视语言环境的不同有很大变化，默认可以识别utf8、ascii、ascii-ctrl、
iso-8859-1等。

decode函数则是用来解码字节流的。它按照你给出的编码格式解释给定的字节流，将其转化为使用utf8编码的Perl字符串，一般来说从终端或者文件取得的文本数据都应该用decode转换为Perl字符串的形式。它的格式为：

$string = decode(ENCODING, $octets [, CHECK])
$string、ENCODING、$octets和CHECK的含义同上。

现在就很容易理解上面写的那段程序了。因为字符串是用明文写出的，存放的时候已经是字节流形式，丧失了本来的意义，所以首先就要用 decode函数将其转换为Perl字符串，由于汉字一般都用gb2312格式编码，这里decode也要使用gb2312编码格式。转换完成后Perl 对待字符的行为就和我们一样了，平时对字符串进行操作的函数基本上都能正确对字符进行处理，除了那些本来就把字符串当成一堆字节的函数（如vec、 pack、unpack等）。于是split就能把字符串切成单个字符了。最后由于在输出的时候不能直接使用utf8编码的字符串，还需要将切割后的字符用encode函数编码为gb2312格式的字节流，再用print输出。


=cut

#use Encode;
#use Encode::CN;

sub _Utf8 { #将 utf8 解码成 字节流 (Tk;Tkx) 	# my $tString = _Utf8("$InputStr");
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

sub Utf8_ { #将 字符串 进行 utf8 编码 					# my $tString = Utf8_("$ConvStr");
	#return encode('utf8',decode('utf8',shift));
	my @NewCode;
	for ( @_ ) {
		push( @NewCode,encode('utf8',$_) );
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


sub _Utf8_ { #将 utf8 解码再编码 					# my $tString = _Utf8_("$ConvStr");
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

sub _Gbk { #将 中文 解码成 字节流 				# my $tString = _Gbk("$InputStr");
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


sub Gbk_ { ##将 字符串 进行 gbk 编码 					# my $tString = Gbk_("$ConvStr");
	#return encode('CP936',decode('CP936',shift));
	my @NewCode;
	for ( @_ ) {
		push( @NewCode,encode('CP936',$_) );
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

sub _Gbk_ { #将 gbk 解码再编码 					# my $tString = _Gbk_("$ConvStr");
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

sub Gbk_Utf8 { #将 gbk 转换成 utf8 				# my $tOutputStr = Gbk_Utf8("$InputStr");
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

sub Utf8_Gbk { #将 utf8 转换成 gbk 				# my $tOutputStr = Utf8_Gbk("$InputStr");
	#return encode('CP936',decode('utf8',shift));
	my @NewCode;
	for ( @_ ) {
#		print $_ . "\n" ;
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

sub CH { #将 中文 解码成 字节流 					# my $tString = CH("$InputStr");
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

##############								通用						#####################################################################

sub iAliasMySql {
	my $tActMode = shift;
	if ( $tActMode =~ /^(Get|Set)$/i ){
		my $tSqlCmd = shift;
		my $tSqlTable = shift;
		if ( defined $tSqlCmd ){
			&iMySqlAct('Link',$tSqlTable);
			my $tResult = &iMySqlAct($tActMode,$tSqlCmd);
			&iMySqlAct('Finish');
			&iMySqlAct('Unlink');
			if ( $tActMode =~ /Get/i ) {
				if ( ref($tResult) eq "HASH" ) {
					return(%$tResult);
				} elsif ( ref($tResult) eq "ARRAY" ) {
					return(@$tResult);
				} else {
					return ($tResult);
				}
			}
			return($tResult);
		}
	} elsif ( $tActMode =~ /^(Gets|Sets)$/i ){
		my $tSqlDefTable = shift;
		my @SqlCmd = @_;
		if ( defined $SqlCmd[0] ){
			&iMySqlAct('Link',$tSqlDefTable);
			my %SqlResult;
			my $RunNum = 0;
			for my $tSqlCmd ( @SqlCmd ){
				my $tResult = &iMySqlAct($tActMode,$tSqlCmd);
				if ( $tActMode =~ /Gets/i ) {
					if ( ref($tResult) eq "HASH" ) {
						%{$SqlResult{$RunNum}} = %$tResult;
					} elsif ( ref($tResult) eq "ARRAY" ) {
						@{$SqlResult{$RunNum}} = @$tResult;
					} else {
						$SqlResult{$RunNum} = $tResult;
					}
				}
				&iMySqlAct('Finish');
				$RunNum++;
			}
			&iMySqlAct('Unlink');
			return(%SqlResult);
		} else {
			return();
		}
	}
}

sub iMySqlAct {  #数据库连接操作
	my $tActMode = shift;
	if ( $tActMode =~ /Link/i ){
		my ($MySqlServer,$MySqlPort) = ("192.168.2.19","3306");
		my $MySqlAccessingDatabase = shift || "project_status";
		my ($MySqlUserId,$MySqlPassword) = ("root","k06931!");
		$MySqlProcess = DBI->connect("DBI:mysql:$MySqlAccessingDatabase:$MySqlServer:$MySqlPort",$MySqlUserId,$MySqlPassword) or die "$MySqlProcess->errstr";

		$MySqlProcess->do("SET NAMES utf8");
	} elsif ( $tActMode =~ /(Get|Set)/i ){
		my $ActExecute = shift;
		$MySqlExecute = $MySqlProcess->prepare("$ActExecute");
		$MySqlExecute->execute() or die "无法执行SQL语句:$MySqlProcess->errstr";
		if ( $tActMode =~ /Get/i ) {
			my @tArray;
			while (my @tRow = $MySqlExecute->fetchrow_array){
				if ( scalar(@tRow) > 1 ){
					push (@tArray,\@tRow);
				}else{
					push (@tArray,$tRow[0]);
				}
			}
			if ( scalar(@tArray) > 1 ) {
				return (\@tArray);
			} else {
				return ($tArray[0]);
			}
		}
		return ($MySqlExecute);
	} elsif ( $tActMode =~ /Finish/i ){
		$MySqlExecute->finish;
	} elsif ( $tActMode =~ /Unlink/i ){
		$MySqlProcess->disconnect; #断开数据库连接
	}
}

sub ilistFolders { #列出指定目录的所有文件夹 my @FolderList = &ilistFolders('2',@listRootPath); my @FolderList = &ilistFolders(';;',@listRootPath);
	my $RecursionDeep = shift || ';;';
	my @listRootPath = @_;
	my @FolderList = ($listRootPath,);
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

sub iOutMsgBoxs {  #外部exe提示框 # iOutMsgBoxs("JOB不存在!","warning","ok","JOB不存在,脚本退出!",);
	my ($tTitle,$tIco,$tType,$tMsg,) = (@_);
	my $tParameterText = join ('::',($tTitle,$tMsg,$tType,$tIco,));
	my $MessBoxsPath;
	if ( $^O =~ /^linux/i ) {
		$MessBoxsPath = "$ENV{INCAM_SITE_DATA_DIR}/scripts/User/Neo/Tools/MessBoxs.Neo";
	} elsif ( $^O =~ /^MSWin/i ) {
		for (
		"D:/genesis/sys/scripts/Tools/MessBoxs.exe",
		"//192.168.2.33/incam-share/incam/server/site_data/scripts/User/Neo/MessBoxs.exe",
		){
			if ( -e $_ ) {
				$MessBoxsPath = $_;
				last;
			}
		}
	}
	# my $MsgOut = `perl /mnt/hgfs/LinuxShare/MessBoxTkx.pl $tParameterText`;
	my $MsgOut = `$MessBoxsPath $tParameterText`;
	#'标题::示范内容::按钮[ok|okcancel|yesno|yesnocancel|abortretryignore|retrycancel]::图标[info|question|warning|error]'
	$MsgOut = lc($MsgOut);
	chomp $MsgOut;
	return ($MsgOut);
}

sub iGetDesktopDir {  #Linux获取桌面路径 # my $DesktopDir = iGetDesktopDir;
	if ( $^O =~ /^linux/i ) {
		my $UserDirsConfigFile = $ENV{HOME} . '/.config/user-dirs.dirs';
		if ( -e $UserDirsConfigFile ){
			my @tFieContent = &iReadFile($UserDirsConfigFile);
			for my $tLine ( @tFieContent ){
				chomp $tLine;
				if ( $tLine =~ /XDG_DESKTOP_DIR/i){
					my ($tDesktopDir) = ($tLine =~ /^\s*[^=]+\s*=\s*"?(\S+.*[^\s"]+)"?\s*$/);
					$tDesktopDir = &iTextProcessing('Path',$tDesktopDir);
					return ($tDesktopDir);
					last;
				}
			}
		}
	}

	#~/.config/user-dirs.dirs
	#XDG_DESKTOP_DIR="$HOME/桌面"
	#XDG_DOWNLOAD_DIR="$HOME/下载"
	#XDG_TEMPLATES_DIR="$HOME/"
	#XDG_PUBLICSHARE_DIR="$HOME/"
	#XDG_DOCUMENTS_DIR="$HOME/"
	#XDG_MUSIC_DIR="$HOME/"
	#XDG_PICTURES_DIR="$HOME/"
	#XDG_VIDEOS_DIR="$HOME/"
	return ();
}

sub iTextWrap {  #文本换行 iTextWrap($tDefText,$tText,$tLimitedLength,$tStartTextLength,$tTextRows,);
		my ($tDefText,$tText,$tLimitedLength,$tStartTextLength,$tTextRows,) = @_;
		$tTextLen = length($tText);
		if ( ( $tTextLen + $tStartTextLength ) <= $tLimitedLength ){
			if ( defined $tDefText ){
				$tDefText .= " $tText" ;		
			} else {
				$tDefText .= "$tText" ;
			}
			$tStartTextLength += $tTextLen;
		} else {
			$tDefText .= "\n$tText";
			$tTextRows ++;
			$tStartTextLength = $tTextLen;
		}
		return ($tDefText,$tStartTextLength,$tTextRows);
}

sub iTextProcessing {  #清除前后空格|转换变量|转换路径斜杠 # TextProcessing('Trim',,);  # TextProcessing('Text',,);  # TextProcessing('Path',,);  # TextProcessing('Param',,);# TextProcessing('uParam','::',);
	# &TextProcessing('Trim',,);  # &TextProcessing('Text',,);  # &TextProcessing('Path',,);  # &TextProcessing('Param',,);# &TextProcessing('uParam','::',);
	my $tProcessingMode = shift;
	my $tSepa ;
	if ( $tProcessingMode =~ /^uParam$/i ) {
		$tSepa = shift;
	}
	my @TextData = @_;
	my @NewTextData;

	for my $tTextData ( @TextData ) {
		my $tText = $tTextData;
		chomp $tText;
		$tText =~ s/^\s*|\s*$//g;
		if ( $tProcessingMode !~ /^Trim$/i ) {
			if ( $tProcessingMode =~ /^Param$/i ) {
				$tText =~ s/\s+\|/|/g;
				$tText =~ s/\|\s+/|/g;
			} elsif ( $tProcessingMode =~ /^uParam$/i ) {
				$tText =~ s/\s+$tSepa/$tSepa/g;
				$tText =~ s/\$tSepa\s+/$tSepa/g;
			} else {
				$tText =~ s/\$\{(\w+)\}/$ENV{$1}/g;
				$tText =~ s/\$(\w+)/$ENV{$1}/g;
			}
		}
		if ( $tProcessingMode =~ /^Path$/i ) {
			$tText =~ s#\\#/#g;
		}
		push ( @NewTextData,$tText ) ;
	}
	if ( scalar( @NewTextData) == 1 ) {
		return ( $NewTextData[0] ) ;
	} elsif ( scalar( @NewTextData) > 1 ) {
		return ( @NewTextData ) ;
	} else {
		return ();
	}
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

sub iReadFile {  #读取文件 # my @tFieContent = iReadFile('D:\1.txt');
	my $tFile = shift;
	$tFile =~ s#[\\]#/#g;
	if ( defined $tFile ) {
		if ( -e $tFile ){
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

sub iReadDir {  #读取文件夹 # my @tDirLists = iReadDir('D:\Input');
	my $tPath = shift;
	$tPath =~ s#[\\]#/#g;
	if ( defined $tPath ) {
		if ( -e $tPath ){
			my %DirHandle;
			my $DirHandleRand = 'DirHandle' . int(rand(99999));
#			opendir($DirHandle,"$tPath" || die "Cannot open path this $tPath");
			opendir($DirHandle{$DirHandleRand},"$tPath" || die "Cannot open path this $tPath");
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
		warn "No definition Dir!\n";
	}
	return();
}

sub iMkDir {  #创建文件夹 # iMkDir('\\\192.168.1.1\1\12\','/root/desk/123/abc',);
	my @OrgPath = @_;
	if ( scalar(@OrgPath) != 0 ) {
		if ( $OrgPath[0] eq "" ) {
			return();
		}
		for my $tOrgPath ( @OrgPath ) {
			$tOrgPath =~ s#[\\]#/#g;
			my ($tOrgPathStart) = ($tOrgPath =~ m#^(/+)[^/]+#i );
			unless (defined $tOrgPathStart ){
				$tOrgPathStart = '';
			}
			my $tPath;
			my @TmpPath;
			for ( split /\/+/,$tOrgPath ){
				if ( $_ eq '' ) {
					next;
				}
				if ( defined $tPath ) {
					$tPath = $tPath . $_ . '/';
				}else{
					$tPath = $tOrgPathStart . $_ . '/'  ;
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
				mkdir "$tPath",0777 or warn "Cannot make $tPath directory: $!";
			}
		}
	}
	return();
}

sub iClearDup {  #数组去重 # my @newArray = iClearDup(@Array);
	my %hash;
	for (@_) {
		$hash{$_} = 1;
	}
	return (keys %hash);
}

sub iGetDateTime {  #获取时间 # iGetDateTime; iGetDateTime("Date"); iGetDateTime("Time"); iGetDateTime("DateTime"); iGetDateTime("DateTimes"); iGetDateTime("Custom","YY-MM-DD hh:mm:ss");
	my $DateTimeType = shift;
#	use Time::localtime;
	&iLoadModules("Time::localtime");
	my $tDateTime;
	unless ( defined $DateTimeType ) {
		$tDateTime = sprintf("%4d/%d/%d %d:%02d:%02d",(1900 + localtime->year),(localtime->mon + 1),localtime->mday,localtime->hour,localtime->min,localtime->sec);
	} else {
		if ( $DateTimeType eq 'Date' ) {
			$tDateTime = sprintf("%4d%02d%02d",(1900 + localtime->year),(localtime->mon + 1),localtime->mday,);
		} elsif ( $DateTimeType eq 'Time' ) {
			$tDateTime = sprintf("%d:%02d:%02d",localtime->hour,localtime->min,localtime->sec);
		} elsif ( $DateTimeType eq 'DateTime' ) {
			$tDateTime = sprintf("%4d%02d%02d %d:%02d:%02d",(1900 + localtime->year),(localtime->mon + 1),localtime->mday,localtime->hour,localtime->min,localtime->sec);
		} elsif ( $DateTimeType eq 'DateTimes' ) {
			$tDateTime = sprintf("%4d/%02d/%02d %d:%02d:%02d",(1900 + localtime->year),(localtime->mon + 1),localtime->mday,localtime->hour,localtime->min,localtime->sec);
		} elsif ( $DateTimeType eq 'Custom' ) {
			#yy,MM,dd,hh,mm,ss,cc
			my $Args = shift ;

			my %TimeConv;
			$TimeConv{YY} = sprintf("%4d",(1900 + localtime->year),);
			$TimeConv{MM} = sprintf("%02d",(localtime->mon + 1),);
			$TimeConv{DD} = sprintf("%02d",localtime->mday,);
			#
			$TimeConv{hh} = sprintf("%02d",localtime->hour,);
			$TimeConv{mm} = sprintf("%02d",localtime->min,);
			$TimeConv{ss} = sprintf("%02d",localtime->sec,);
			#########
			$TimeConv{y} = sprintf("%02d",( substr (1900 + localtime->year,2,2) ),);
			$TimeConv{M} = sprintf("%d",(localtime->mon + 1),);
			$TimeConv{d} = sprintf("%d",localtime->mday,);
			#
			$TimeConv{h} = sprintf("%d",localtime->hour,);
			$TimeConv{m} = sprintf("%d",localtime->min,);
			$TimeConv{s} = sprintf("%d",localtime->sec,);

			$Args =~ s/(YY|MM|DD|hh|mm|ss)/$TimeConv{$1}/g;
			$Args =~ s/(Y|M|D|h|m|s)/$TimeConv{$1}/g;
			#
			$tDateTime = $Args;
		}
	}
#	my $date = sprintf("%4d%02d%02d-%02d:%02d:%02d",(1900 + localtime->year),(localtime->mon + 1),localtime->mday,localtime->hour,localtime->min,localtime->sec);
#	my $date = sprintf("%2d%02d%02d %02d:%02d:%02d",( substr (1900 + localtime->year,2,2) ),(localtime->mon + 1),localtime->mday,localtime->hour,localtime->min,localtime->sec);
	chomp $tDateTime;
	return ($tDateTime);
}

sub Say {  #打印 自动加换行符 # Say(@Text);
	&iSay(@_);
}

sub iSay {  #打印 自动加换行符 # iSay(@Text);
	for ( @_ ) {
		my $tLine = $_ ;
		chomp $tLine;
		print $tLine . "\n";
	}
}

=h
sub iSayV {  #打印变量 #iSayV($var,\@array,\@hash,); iSayV($var,); iSayV(\@array); iSayV(\%hash);
#	use Data::Dumper ();
#	use Scalar::Util 'refaddr';
#	use PadWalker 'peek_my';
	&iLoadModules("Data::Dumper");
	&iLoadModules("Scalar::Util 'refaddr'");
	&iLoadModules("PadWalker 'peek_my'");
	my $UpLevel = 1;

	my $pad = peek_my($UpLevel);
	my %pad_vars;
	while ( my ( $var, $ref ) = each %$pad ) {
		# we no longer remove the '$' sigil because we don't want
		# "$foo = \@array" reported as "@foo".
		$var =~ s/^[\@\%]/*/;
		$pad_vars{ refaddr $ref } = $var;
	}

	my @names;
	my $varcount = 1;
	foreach ( @_ ) {
		my $name;
		INNER: foreach ( \$_, $_ ) {
			no warnings 'uninitialized';
			$name = $pad_vars{ refaddr $_} and last INNER;
		}
		push @names, $name;
	}
#	return Data::Dumper->Dump( \@_, \@names );
	print Data::Dumper->Dump( \@_, \@names );
}
=cut
sub fSay {  #输出到文件 自动加换行符 # fSay($FileHandle,@Text);
	my $FileHandle = shift;
	for my $tLine ( @_ ) {
		chomp $tLine;
		print $FileHandle $tLine . "\n";
	}
}

sub iSort {  #默认大小排序 # iSort(@Array);
	return ( sort { $a <=> $b }(@_) );
}

sub uSort {  #自定义排序 # iSort("1",@Array); # iSort("2",@Array); # iSort("a",@Array); # iSort("b",@Array);
	my $tSortMode = shift;
	if ( $tSortMode eq "1" ){
		return ( sort { $a <=> $b }(@_) );
	} elsif ( $tSortMode eq "2" ){
		return ( sort { $b <=> $a }(@_) );
	} elsif ( $tSortMode eq "a" ){
		return ( sort { $a cmp $b }(@_) );
	} elsif ( $tSortMode eq "b" ){
		return ( sort { $b cmp $a }(@_) );
	}
}

sub iArr2Hash {  #数组转换为哈希 #my %tHash = iArr2Hash(@tArray);
	my @tArray = @_;
	my %tHash;
	for ( 0 .. $#tArray ) {
		$tHash{$tArray[$_]} = $_;
	}
	return (%tHash);
}

sub iHooksParamConv { #Hooks传入参数转换  #our %HooksParam = &iHooksParamConv;
	my $readFile = shift || $ARGV[0] ;
	#set lnPARAM = ('type'                'source_job'          'source_name'         'dest_job'            'dest_name'           'dest_database'       'remove_from_sr'      )
	#set lnVAL   = ('job'                 'h50204gn497a1-neo'   'h50204gn497a1-neo'   'h50204gn497a1-neo-t' 'h50204gn497a1-neo-t' 'linux1'              'yes'                 )
	my (@lnParam,@lnVal);
	open (PARAM_FILE,  "$readFile") or warn "Cannot open info file -$readFile: $!\n";
	while ( <PARAM_FILE> ) {
		chomp($_);
		if ( $_ =~ /set\s+(\S+)/ ){
			my ($var,$value) = /set\s+(\S+)\s*=\s*(.*)\s*/;
			my @words;
			$value =~ s/^\s*|\s*$//g;
			if ($value =~ /^\(/ ) {
				$value =~ s/^\(|\)$//g;
				@words = &iShellWords($value);
			} else {
				$value =~ s/^'|'$//g;
				@words = ($value);
			}
			if ( $var eq 'lnPARAM' ) {
				@lnParam = @words;
			} elsif ( $var eq 'lnVAL' ) {
				@lnVal = @words;
			}
		}
	}
	close (PARAM_FILE);
	
	if ( defined $lnParam[0] and defined $lnVal[0] ){
		my %tHash;
		for ( 0 .. $#lnParam ) {
			$tHash{$lnParam[$_]} = $lnVal[$_];
		}
		return (%tHash);
	
	}
	return();
}

sub iShellWords {  #Shell 变量转换 #my @words = iShellWords($line); #my @words = iShellWords(@lines);
#	local ($_) = join('', @_) if @_;
#	local (@words,$snippet,$field);
	my ($_) = join('', @_) if @_;
	my (@words,$snippet,$field);

	s/^\s+//;
	while ($_ ne '') {
		$field = '';
		for (;;) {
			if (s/^"(([^"\\]|\\[\\"])*)"//) {
				($snippet = $1) =~ s#\\(.)#$1#g;
			} elsif (/^"/) {
				die "Unmatched double quote: $_\n";
			} elsif (s/^'(([^'\\]|\\[\\'])*)'//) {
				($snippet = $1) =~ s#\\(.)#$1#g;
			} elsif (/^'/) {
				die "Unmatched single quote: $_\n";
			} elsif (s/^\\(.)//) {
				$snippet = $1;
			} elsif (s/^([^\s\\'"]+)//) {
				$snippet = $1;
			} else {
				s/^\s+//;
				last;
			}
			$field .= $snippet;
		}
		push(@words, $field);
	}
	return(@words);
}

sub iShellVarConv {  #Shell 变量转换 单行 #my %tHash = iShellVarConv($tFileLine);
	local ($_) = join('', @_) if @_;
	my ($var,$value) = /set\s+(\S+)\s*=\s*(.*)\s*/;
	my %tHash;
	my @tArray;
	$value =~ s/^\s*|\s*$//g;
	if ($value =~ /^\(/ ) {
		$value =~ s/^\(|\)$//g;
		my @words = &iShellWords($value);
		$tHash{$var} = [@words];
		@tArray = ($var,@words);
	} else {
		$value =~ s/^'|'$//g;
#		$tHash{$var} = [$value];
		$tHash{$var} = $value;
		@tArray = ($var,$value);
	}
	return(%tHash);
#	return(@tArray);
}

sub iShellVarConvs {  #Shell 变量转换 多行 #my %tHash = iShellVarConvs(@FileLine); #my %tHash = iShellVarConvs(<>);
	my %tMergeHash;
	for ( @_ ) {
		my %tHash = &iShellVarConv($_);
		%tMergeHash = (%tMergeHash,%tHash);
	}
	return(%tMergeHash);
}

sub iArrMergeHash {  #数组合并为哈希 #my %tHash = iArrMergeHash(\@KeyArray,\@ValueArray,);
	my $tKeyText = shift;
	my $tValueText = shift;
	my @KeyArray = @$tKeyText;
	my @ValueArray = @$tValueText;
#	print "tKeyText=$tKeyText,tValueText=$tValueText\n";
#	print "KeyArray=@KeyArray,ValueArray=@ValueArray\n";
	my %tHash;
	for ( 0 .. $#KeyArray ) {
		$tHash{$KeyArray[$_]} = $ValueArray[$_];
	}
	return (%tHash);
}

sub iHashArrConvHash {  #哈希内嵌数转换为哈希 # my %tHash = iHashArrConvHash('gTOOLnum',\%{$f->{doinfo}},); # my %tHash = iHashArrConvHash($keyname,\%hash,);
	#指定的 Key 数组的元素为 主键名 , 其他的数组名为 子键名 
	my $tKeyName = shift;
	my $tHashText = shift;
	my %HashData = %$tHashText;
	my @SubKeys;
	for my $tKey ( keys  %HashData ){
		if ( $tKey ne $tKeyName ){
			push (@SubKeys,$tKey);
		}
	}

	my @RootKeys = @{$HashData{$tKeyName}} ;
	my %NewHash;
	for (my $n = 0;$n<=$#RootKeys;$n++ ) {
		for my $tSubKey ( @SubKeys ) {
			#my $tSubValue = $HashData{$tSubKey}[$n];
			$NewHash{$RootKeys[$n]}{$tSubKey} = $HashData{$tSubKey}[$n];
		}
	}
	return (%NewHash);
}

sub iHashArrConvHash2 {  #哈希内嵌数转换为哈希 # my %tHash = iHashArrConvHash2('gTOOLnum',\%{$f->{doinfo}},); # my %tHash = iHashArrConvHash2($keyname,\%hash,);
	# 其他的数组名为 主键名 , 指定的 Key 数组的元素为 子键名
	my $tKeyName = shift;
	my $tHashText = shift;
	my %HashData = %$tHashText;
	my @SubKeys;
	for my $tKey ( keys  %HashData ){
		if ( $tKey ne $tKeyName ){
			push (@SubKeys,$tKey);
		}
	}

	my @RootKeys = @{$HashData{$tKeyName}} ;
	my %NewHash;
	for (my $n = 0;$n<=$#RootKeys;$n++ ) {
		for my $tSubKey ( @SubKeys ) {
			#my $tSubValue = $HashData{$tSubKey}[$n];
			$NewHash{$tSubKey}{$RootKeys[$n]} = $HashData{$tSubKey}[$n];
		}
	}
	return (%NewHash);
}


sub igFileModifyTime {  #获取文件修改时间 my $tFileModifyTime = igFileModifyTime($tFile);
	my $tFile = shift;
	if ( -f $tFile ) {
#		use POSIX qw(strftime);
#		use File::stat;
		&iLoadModules("POSIX");
		&iLoadModules("File::stat");
		my $tFileModifyTime = strftime("%Y-%m-%d %H:%M:%S", localtime( stat($tFile)->mtime ) ) ;
		return($tFileModifyTime);
	}
}

sub igFileSize {  ##获取文件大小 my $tFiletFileSize = igFileSize($tFile);
	my $tFile = shift;
	if ( -f $tFile ) {
#		use File::stat;
		&iLoadModules("File::stat");
		my $tFiletFileSize = stat($tFile)->size ;
		return( $tFiletFileSize);
	}
}


##############								Tkx						#####################################################################

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

#		use File::Basename;
		&iLoadModules("File::Basename");
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

sub iTkxMsgBox {  #一次性当前提示框 # iTkxMsgBox("JOB不存在!","JOB不存在,脚本退出!","ok","warning",);
#	my ($tTitle,$tIco,$tButtonType,$tMsg,$DefButton,) = (@_);
	my ($tTitle,$tMsg,$tButtonType,$tIco,$DefButton,) = (@_);
	&iLoadModules("Tkx");
	my $tMw = Tkx::widget->new(".");
	&iTkxGetImageFile('SetMwLogo',$tMw);
	$tMw->g_wm_attributes('-topmost',1);
	$tMw->g_wm_geometry("0x0");
	$tMw->g_wm_withdraw;
	my $MsgOut;
	if ( defined $DefButton ) {
		$MsgOut = Tkx::tk___messageBox(-title => $tTitle,-message => $tMsg,-type => $tButtonType || 'ok',-icon => $tIco || 'warning',-parent => $tMw,-default => $DefButton,	);
	} else {
		$MsgOut = Tkx::tk___messageBox(-title => $tTitle,-message => $tMsg,-type => $tButtonType || 'ok',-icon => $tIco || 'warning',-parent => $tMw,	);
	}	
		
	$tMw->g_destroy;
	Tkx::MainLoop();
	
	$MsgOut = lc($MsgOut);
	chomp $MsgOut;
	return ($MsgOut);
}

sub iTkxMwMsg {  #当前$mw提示框 # iTkxMwMsg($mw,"JOB不存在!","JOB不存在,脚本退出!","ok","warning",);
#	my ($mw,$tTitle,$tIco,$tButtonType,$tMsg,$DefButton,) = (@_);
	my ($mw,$tTitle,$tMsg,$tButtonType,$tIco,$DefButton,) = (@_);
	&iLoadModules("Tkx");
	my $MsgOut;
	if ( defined $DefButton ) {
		$MsgOut = Tkx::tk___messageBox(-title => $tTitle,-message => $tMsg,-type => $tButtonType || 'ok',-icon => $tIco || 'warning',-parent => $mw,-default => $DefButton, );
	} else {
		$MsgOut = Tkx::tk___messageBox(-title => $tTitle,-message => $tMsg,-type => $tButtonType || 'ok',-icon => $tIco || 'warning',-parent => $mw,);
	}
	
	chomp $MsgOut;
	$MsgOut = lc($MsgOut);
	return ($MsgOut);
}


##############						Genesis InCAM					#####################################################################
#######################				清除			###################################

sub igClearSel {  #清除选择 # igClearSel;
	$f->COM('sel_clear_feat' ,);
}

sub igClearSels {  #清除选择及高亮 # igClearSels;
	$f->COM('clear_highlight' ,);
	$f->COM('sel_clear_feat' ,);
}

sub igClearLayers {  #清除勾选和显示层别 # igClearLayers;
	$f->COM('clear_layers');
	$f->COM('affected_layer', mode => 'all', affected => 'no');
}

sub igClearAffe {  #清除勾选层别 # igClearAffe;
	$f->COM('affected_layer', mode => 'all', affected => 'no');
}

sub igClearLayer {  #清除勾选层别 # igClearLayer;
	$f->COM('affected_layer', mode => 'all', affected => 'no');
}

#######################				获取			###################################
sub igGetSymInfo {  # 获取Gen内置Pad参数信息 #my $SymWidth  = igGetSymInfo('MinWidth',$tSym);
	my $GetType = shift ;
	my $tSym    = shift ;
	my @iSymInfo = &igSymIdentify($tSym);
	if ( defined $iSymInfo[0] ) {
		my $tSymType = shift @iSymInfo;
		my @SymArg = @iSymInfo ;
		if ( $GetType eq 'MinWidth' ) {
			if ( $tSymType =~ /^(r|s)$/i ){
				return($SymArg[0]);
			} elsif ( $tSymType =~ /^(bfr|bfs)$/i ){
				return( $SymArg[0] / 2 );
#			} elsif ( $tSymType =~ /^(el|tri|di|rect|oval|oval_h|hex_l|oct|hex_s|dshape|radhplate|fhplate|rhplate|hplate)$/i ){
			} elsif ( $tSymType =~ /^(el|rect|oval|oval_h|oct|dshape|radhplate|fhplate|rhplate)$/i ){
				return(  ($SymArg[0] < $SymArg[1]) ? $SymArg[0] : $SymArg[1]  );
			} elsif ( $tSymType =~ /^(cross|dogbone)$/i ){
#				return(  ($SymArg[2] < $SymArg[3]) ? $SymArg[2] : $SymArg[3]  );
				my $hMin = ( $SymArg[0] < $SymArg[2] ) ? $SymArg[0] : $SymArg[2];
				my $vMin = ( $SymArg[1] < $SymArg[3] ) ? $SymArg[1] : $SymArg[3];
				my $tSymWidth = ( $hMin > $vMin ) ? $hMin : $vMin;
				return( $tSymWidth );
			} elsif ( $tSymType =~ /^(thr|ths|s_tho|s_thr|s_ths|donut_r|donut_s)$/i ){
				return(  ( $SymArg[0] - $SymArg[1] ) / 2  );
			} elsif ( $tSymType =~ /^(donut_rc|donut_o)$/i ){
				return( $SymArg[2] );
			} elsif ( $tSymType =~ /^(rc_ths|rc_tho|oblong_ths)$/i ){
				return( $SymArg[5] );
			} elsif ( $tSymType =~ /^(dpack)$/i ){
				#宽度x高度x{x间距}x{y间距}x{x数量}x{y数量}x圆角大小
				my $xW = ($SymArg[0] - ($SymArg[2] * ($SymArg[4] - 1) ) ) / $SymArg[4];
				my $yH = ($SymArg[1] - ($SymArg[3] * ($SymArg[5] - 1) ) ) / $SymArg[5];
				return( ($xW < $yH) ? $xW : $yH );
			} elsif ( $tSymType =~ /^(donut_sr|sr_ths)$/i ){
				return();
			} elsif ( $tSymType =~ /^(moire)$/i ){
				return();
			}
			return();
		}
		return();
	} else {
		return();
	}
}

sub igSymIdentify {  # 判断及获取Gen内置Pad参数信息(空值结果表示不是内置的) #my @iSymInfo = igSymIdentify($tSym);
	my $tSym = shift ;
	my $Figure = '\d{1}\.?\d*';
	if ( $tSym =~
		m/^
		(
			r|           #1、圆  #直径  #r10
			s|           #2、方  #宽度  #s10
			rect|        #3、长方形  #宽度x高度  #rect10x20
							 #4、圆角长方形  #宽度x高度x圆角大小  #宽度x高度x圆角大小x哪个象限圆角  #  2  1  #  3  4#rect10x20xr1#rect10x20xr1x134
							 #5、斜角长方形  #宽度x高度x斜角大小  #宽度x高度x斜角大小x哪个象限斜角  #  2  1  #  3  4#rect10x20xc1#rect10x20xc1x134
			oval|        #6、椭圆  #宽度x高度#oval10x20
			oval_h|      #7、半椭圆  #宽度x高度#oval_h10x20
			donut_r|     #8、环形(甜甜圈)  #外径x内径 #donut_r20x10
			donut_s|     #9、方形环形  #外径x内径#donut_s20x10
			donut_rc|    #10、长方形环形    (Genesis没有)  #长x宽x线宽(导体宽度) #donut_rc10x20x1
							 #11、长方形环形 圆角     (Genesis没有)  #长x宽x线宽(导体宽度)x倒角大小x哪个象限倒角  #  2  1  #  3  4 #donut_rc10x20x1xr4 #donut_rc10x20x1xr4x134
							 #12、方形环形 圆角    (Genesis没有)  #外径x内径x圆角大小x哪个象限倒角  #  2  1  #  3  4#donut_s20x15xr5x123
			donut_o|     #13、椭圆环形    (Genesis没有)  #宽x高x线宽(导体宽度) #donut_o10x20x1
			donut_sr|    #14、外方内圆    (Genesis没有)  #外方形宽度x内圆直径(空)#donut_sr20x10

			thr|         #15、																				  thr 圆形边缘 #thr50x40x1x4x5
			ths|         #15、圆形 花pad(散热pad)   #外径x内径x起始角度x开口数量x开口宽度   ths 方形边缘#ths50x40x1x4x5

			s_tho|       #16、																				 #s_tho 直角边缘 #s_tho50x40x45x4x10
			s_thr|       #16、																				 #s_thr 圆形边缘 #s_thr50x40x45x4x10
			s_ths|       #16、方形 花pad(散热pad)   #外径x内径x起始角度x开口数量x开口宽度  #s_ths 直线边缘 #s_ths50x40x0x4x10

			rc_tho|      #17、																										#rc_tho 直角边缘 #rc_tho40x50x0x4x5x3
			rc_ths|      #17、长方形 花pad(散热pad)   #宽度x高度x起始角度x开口数量x开口宽度x线宽(导体宽度)  #rc_ths 直线边缘 #rc_ths40x50x0x4x5x3
							 #18、圆角 长方形 花pad(散热pad)     (Genesis没有)  #宽度x高度x起始角度x开口数量x开口宽度x线宽(导体宽度)x圆角大小x哪个象限倒角  #  2  1  #  3  4 #rc_ths40x50x0x4x10x2xr3 #rc_ths40x50x0x4x10x2xr3x123
							 #19、圆角 方形 花pad(散热pad)    (Genesis没有)  #外径x内径x起始角度x开口数量x开口宽度x圆角大小x哪个象限倒角  #  2  1  #  3  4 #s_ths50x40x0x4x10xr3 #s_ths50x40x0x4x10xr3x123

			oblong_ths|  #20、椭圆 花pad(散热pad)    (Genesis没有)  #宽度x高度x起始角度x开口数量x开口宽度x线宽(导体宽度)x边缘形状(s方形,r圆形)#oblong_ths100x50x0x4x5x10xr #oblong_ths100x50x0x4x5x10xs
			sr_ths|      #21、外方内圆 花pad(散热pad)  #外方形宽度x内圆直径(空)x起始角度x开口数量x开口宽度#sr_ths50x40x0x4x10
			di|          #22、菱形  #宽度x高度#di20x30
			oct|         #23、长方形倒角  #宽度x高度x倒角长度#oct10x20x3
			hex_l|       #24、六边形 x方向斜角  #宽度x高度x{斜角X长度}#hex_l10x20x3
			hex_s|       #25、六边形 Y方向斜角  #宽度x高度x{斜角Y长度}#hex_s10x20x3
			tri|         #26、三角形  #宽度x高度#tri10x20
			el|          #27、真 椭圆   #宽x高#el20x30
			bfr|         #28、蝴蝶pad 圆形  #直径 bfr10
			bfs|         #29、蝴蝶pad 方形  #宽度 bfs10
			moire|       #30、靶形  #环形宽度x中心pad到第一个环形距离x环形数量x十字线宽x十字线长度x起始角度  #环形间距固定 1.5#moire1x2x3x1.5x20x0
			hplate|      #31、一边方形一边三角    (Genesis没有)  #宽度x高度x{右边斜角X长度}x左边方形圆角大小x右边三角圆角大小(三角)#hplate10x20x5 #hplate10x20x5xra2xro3
			rhplate|     #32、一边方形一边内向三角    (Genesis没有)  #宽度x高度x{右边内向斜角X长度}x左边方形圆角大小x右边内三角尖角圆角大小(一角) #rhplate10x20x5 #rhplate10x20x5xra2xro3
			fhplate|     #33、一边方形一边梯形    (Genesis没有)#fhplate20x30x3x2 #fhplate20x30x3x2xra4xro1  #宽度x高度x{右边斜角X长度}x{右边斜角Y长度}x左边方形圆角大小x右边梯形圆角大小(四角)
			radhplate|   #34、一边方形一边双半圆    (Genesis没有)  #宽度x高度x两个半圆之间的距离x左边方形圆角大小#radhplate20x30x5 #radhplate20x30x5xra3
			dshape|      #35、一边方形一边弧    (Genesis没有)  #宽度x高度x右边弧高x左边方形圆角大小#dshape10x20x3 #dshape10x20x3xra3
			cross|       #36、横竖交叉十字 (Genesis没有) #横向线长x纵向线长x横向线宽x纵向线宽x纵向在横向所在位置%x横向在纵向所在位置%x边缘形状(s方形,r圆形) #cross30x20x5x6x50x50xs  cross10x20x5x6x40x50xr  #交叉处圆角(圆形边缘)  cross10x20x5x6x40x50xrxra1  #边缘处圆角(方形边缘)  cross30x20x5x6x40x50xcxra1  #边缘处圆角+交叉处圆角(方形边缘)  cross30x20x5x6x50x50xsxra1
			dogbone|     #37、工形    (Genesis没有)  #横向线长x纵向线长x横向线宽x纵向线宽x纵向在横向所在位置%x边缘形状(s方形,r圆形) #dogbone30x40x5x6x50xr #dogbone30x40x5x6x50xs  #交叉处圆角(圆形边缘)#dogbone30x40x5x6x50xrxra1  #边缘处圆角+交叉处圆角(方形边缘) #dogbone30x40x5x6x50xsxra1
			dpack|       #38、矩阵长方形pad    (Genesis没有)  #宽度x高度x{x间距}x{y间距}x{x数量}x{y数量}x圆角大小#dpack100x200x3x4x5x6 #dpack100x200x3x4x5x6xra1
			null			 #39、空               null10
		)
		((
			$Figure|
			x$Figure|
			xc|
			xc$Figure|
			xr|
			xr$Figure|
			xra$Figure|
			xro$Figure|
			xs|
			xs$Figure|
			_$Figure     # Genesis 特殊角度pad 将角度加在了后面(_角度) InCAM不用
		){1,})
		$/x
	){
		my ($SymType,$SymArgText,) = ($1,$2,);
		my @SymArg = split('x',$SymArgText);
		my $LastSymArg = $SymArg[$#SymArg];
		if ( $LastSymArg =~ /_/ ){ # Genesis 特殊角度pad 将角度加在了后面(_角度)
			my @tLastSymArg = split('_',$LastSymArg);
			return($SymType,@SymArg[0.. $#SymArg - 1],$tLastSymArg[0],'_' . $tLastSymArg[1]);
		}
		return($SymType,@SymArg);
	} else {
		return();
	}
}


sub iGetInCAMUserData {  #获取InCAM用户属性数据 #my %InCAMUserData = iGetInCAMUserData; #my $GenUserFullName = iGetInCAMUserData($GenUser,'fullName');
	if ( $_CAMSOFT eq "InCAM" ) {
		my $tGenUser = shift;
		my $tGetData = shift;

#		use XML::Simple;
		&iLoadModules("XML::Simple");
		my $InCAMUsersFile = '/incam/server/config/users.xml';
		if ( defined $ENV{INCAM_SERVER} ){
			$InCAMUsersFile = $ENV{INCAM_SERVER} .'/config/users.xml';
		}

		my %InCAMUsers = %{XMLin($InCAMUsersFile)};
		if ( defined $tGenUser ) {
			if ( defined $tGetData ) {
				if ( $tGetData !~ /^Get$/ ){
					return ($InCAMUsers{'user'}{$tGenUser}{'properties'}{$tGetData});
				}
			}
		}
		################
		my %ReturnHash;
		for my $tKey ( keys %{$InCAMUsers{'user'}} ){
			%{$ReturnHash{$tKey}} = %{$InCAMUsers{'user'}{$tKey}{'properties'}};
		}
		return (%ReturnHash);
	}
}

sub iGetInCAMLibSym {  #获取InCAM库里面的Symbol列表 # my %InCAMLibSym = iGetInCAMLibSym;
#	use XML::Simple;
	&iLoadModules("XML::Simple");
	my $InCAMLibSymFile = '/incam/server/site_data/library/symbols/index.idx';
	if ( defined $ENV{INCAM_SITE_DATA_DIR} ){
		$InCAMLibSymFile = $ENV{INCAM_SITE_DATA_DIR} . '/library/symbols/index.idx';
	}
	print"InCAMLibSymFile=$InCAMLibSymFile\n";
	my %InCAMLibSymData = %{XMLin($InCAMLibSymFile)};
	my %InCAMLibSym_NameToLatinName;
	for my $tName ( keys %{$InCAMLibSymData{item}} ){
		$InCAMLibSym_NameToLatinName{$tName} = $InCAMLibSymData{item}{$tName}{latin_name};
	}
	return(%InCAMLibSym_NameToLatinName);
}

sub igJobDir {  #获取料号User路径 # my $tJobDir = igJobDir; # my $tJobDir = igJobUserDir($tJob);
	my $tJob = shift;
	unless ( defined $tJob ){
		if ( defined $ENV{INCAM_USER} ) {
			if ( defined $ENV{JOB_USER_DIR} ) {
				my $tJobPath = $ENV{JOB_USER_DIR} ;
					#$tJobPath =~ s#/user\z## ;
					$tJobPath =~ s#/user$## ;
				return ($tJobPath);
			}
		}
		$tJob = $ENV{JOB};
	}
	if ( defined $tJob ){
		my $DbutilPath;
		if ( defined $ENV{INCAM_USER} ) {
				$f->COM('get_version' ,);
				my $tInCAMVer = $f->{COMANS}; #V3.3SP2 (04Sep17)
				my $tVerNum = ( $tInCAMVer =~ /^V(\d.?\d*)\D*/i ) ;
				if ( $tVerNum >= 2.2 ) {
					$f->COM('get_job_path' ,job => $ENV{JOB} ,);
					my $tJobPath = $f->{COMANS};
					chomp $tJobPath;
					return ("$tJobPath");
				} else {
					$DbutilPath = $ENV{INCAM_PRODUCT} . "/bin/dbutil";
				}
		} else {
			$DbutilPath = $ENV{GENESIS_EDIR} . "/misc/dbutil";
		}
		my $tJobPath = `$DbutilPath path jobs $ENV{JOB}`;
		chomp $tJobPath;
		return ("$tJobPath");
	}
}

sub igJobUserDir {  #获取料号User路径 # my $tJobUserDir = igJobUserDir; # my $tJobUserDir = igJobUserDir($tJob);
	my $tJob = shift;
	unless ( defined $tJob ){
		if ( defined $ENV{INCAM_USER} ) {
			if ( defined $ENV{JOB_USER_DIR} ) {
				return ($ENV{JOB_USER_DIR});
			}
		}
		$tJob = $ENV{JOB};
	}
	if ( defined $tJob ){
		my $DbutilPath;
		if ( defined $ENV{INCAM_USER} ) {
				$f->COM('get_version' ,);
				my $tInCAMVer = $f->{COMANS}; #V3.3SP2 (04Sep17)
				my $tVerNum = ( $tInCAMVer =~ /^V(\d.?\d*)\D*/i ) ;
				if ( $tVerNum >= 2.2 ) {
					$f->COM('get_job_path' ,job => $ENV{JOB} ,);
					my $tJobPath = $f->{COMANS};
					chomp $tJobPath;
					return ("$tJobPath/user");
				} else {
					$DbutilPath = $ENV{INCAM_PRODUCT} . "/bin/dbutil";
				}
		} else {
			$DbutilPath = $ENV{GENESIS_EDIR} . "/misc/dbutil";
		}
		my $tJobPath = `$DbutilPath path jobs $ENV{JOB}`;
		chomp $tJobPath;
		return ("$tJobPath/user");
	}
}

sub igGetSel {  #获取选中数量 # my $tSelCount = igGetSel;
	return ( $f->COM ('get_select_count') );
}

sub igWork {  #获取工作层 # my $tWorkLayer = igWork;
	$f->COM('get_work_layer');
	return ( $f->{COMANS} );
}

sub igAffe {  #获取勾选层别 # my @tAffeLayer = igAffe;
	$f->COM('get_affect_layer');
	# my @AffectLayer = split ( " ",$f->{COMANS} );
	return ( split (" ",$f->{COMANS}) );
}

sub igDisp {  #获取勾选层别 # my @tDispLayer = igDisp;
	$f->COM('get_disp_layers');
	# my @DispLayer = split ( " ",$f->{COMANS} );
	return ( split (" ",$f->{COMANS}) );
}

sub igMsgBar {  #信息栏数据 # my $tMsgBarText = igMsgBar;
	$f->COM('get_message_bar');
	return ( $f->{COMANS} );
}

sub igVer {  #获取Gen版本 # my $GenVer = igVer;
	$f->COM('get_version' ,);
	my ($tVerText) = ($f->{COMANS} =~ /^V(\d+\.*\d*)/i);
	my $tVer = $tVerText * 10 ;
	return($tVer);
}

############## Genesis InCAM 命令简写###########################################
sub COMANS  {  #获取返回数据 # my $tCOMANS = COMANS;
	return ( $f->{COMANS} );
}

sub igCOM  {  #获取返回数据 # my $tCOMANS = igCOM;
	return ( $f->{COMANS} );
}

sub _P {  #Genesis、InCAM暂停    # _P(@Text);
	my $tText = join(",",@_);
	$f->PAUSE($tText);
	$f->COM('get_select_count');
	unless ( defined $f->{COMANS} ) {
		return('exit');
	}
	return('next');
}

sub iP {  #Genesis、InCAM暂停   # iP(@Text);
	my $tText = join(",",@_);
	$f->PAUSE($tText);
	$f->COM('get_select_count');
	unless ( defined $f->{COMANS} ) {
		return('exit');
	}
	return('next');
}

sub igInfo {  #获取Info文件内容 # my @FileContent = igInfo("mm"," -t layer -e $JOB/$STEP/$LAYER -d FEATURES -o feat_index");
				# my @FileContent = &igInfo(" -t layer -e $JOB/$STEP/$LAYER -d FEATURES -o feat_index");
	my $tUnits;
	if ( $_[0] eq "mm" or $_[0] eq "inch" ){
		$tUnits = shift;
	}
	my $tArgs = "@_";
	unless ( defined $ENV{GENESIS_TMP} ){
		$ENV{"GENESIS_TMP"} = $ENV{INCAM_TMP};
	}
	my $tInfoFile = $ENV{GENESIS_TMP} . '/info.' . int(rand(9999));

	if ( defined $tUnits ){
		$f->COM ( 'info' ,out_file => $tInfoFile ,units => $tUnits ,args => $tArgs ,) ;
	} else {
		$f->COM ( 'info' ,out_file => $tInfoFile ,args => $tArgs ,) ;
	}
	my %Handle;
	my $FileHandleRand = 'FileHandle' . int(rand(99999));
	open ( $Handle{$FileHandleRand},"<$tInfoFile" ) or warn "Cannot open file - $tInfoFile: $!\n";
	my $FileHandle = $Handle{$FileHandleRand};
	my @tFileContent = <$FileHandle>;
	close ($Handle{$FileHandleRand});
	unlink ($tInfoFile);
	return (@tFileContent);
}

sub igFeatIndex { #my @tFeatIndex = igFeatIndex($JOB,$STEP,$LAYER,); #获取层别物件的索引
	my $tJob = shift;
	my $tStep = shift;
	my $tLayer = shift;
	my @tFeatIndex;
	unless ( defined $ENV{GENESIS_TMP} ){
		$ENV{"GENESIS_TMP"} = $ENV{INCAM_TMP};
	}
	my $tInfoFile = $ENV{GENESIS_TMP} . '/info.' . int(rand(9999));
	my $tArgs = " -t layer -e " . $tJob . '/' . $tStep . '/' . $tLayer . " -d FEATURES -o feat_index" ;
	$f->COM ( 'info' ,out_file => $tInfoFile ,args => $tArgs ,) ;
	
	my %Handle;
	my $FileHandleRand = 'FileHandle' . int(rand(99999));
	open ( $Handle{$FileHandleRand},"<$tInfoFile" ) or warn "Cannot open file - $tInfoFile: $!\n";
	my $FileHandle = $Handle{$FileHandleRand};
	while (<$FileHandle>){
		my $tLine = $_ ;
		#  #283
		if ( $tLine =~ /^#(\d+)/ ) {
			push (@tFeatIndex,$1);
		}
	}

	close ($Handle{$FileHandleRand});
	unlink ($tInfoFile);
	return (@tFeatIndex);
	
}

sub _COM {
	$f->COM(@_);
}

sub _AUX {
	$f->AUX(@_);
}

sub _INFO {
	$f->INFO(@_);
}

sub _PAUSE {
	my $tText = join(",",@_);
	$f->PAUSE($tText);
	$f->COM('get_select_count');
	unless ( defined $f->{COMANS} ) {
		return('exit');
	}
	return('next');
}


sub _MOUSE { 
	$f->MOUSE(@_);
}

sub _VOF {
	$f->VOF;
}

sub _VON {
	$f->VON;
}

sub _SU_OFF {
	$f->SU_OFF;
}

sub _SU_ON {
	$f->SU_ON;
}

#######################				创建			###################################
sub igmAddLayer {  #matrix(row插入)创建层别 # igmAddLayer($tLayer,$tInsRow,$tContext,$tType,$tPolarity,); # igmAddLayer($tLayer,$tInsRow,'misc','signal','positive',$tJob);
	my $tLayer = shift;
	my $tInsRow = shift;
	my $tContext = shift || 'misc'; #misc board
	my $tType = shift || 'signal'; #signal
	my $tPolarity = shift || 'positive'; #positive negative
	my $tJob = shift || $ENV{JOB};

	$f->VOF;
	unless ( defined $ENV{INCAM_USER} ) {
		$f->COM('matrix_insert_row' ,job => $tJob ,matrix => 'matrix' ,row => $tInsRow ,);
	}
	$f->COM('matrix_add_layer' ,job => $tJob ,matrix => 'matrix' ,layer => $tLayer ,row => $tInsRow ,context => $tContext ,type => $tType ,polarity => $tPolarity ,);
	$f->VON;
}

sub igCreateLayer {  #创建层别 # igCreateLayer($tLayer); # igCreateLayer($tLayer,$tContext,$tType,$tPolarity,$tInsLayer,); # igCreateLayer($tLayer,'misc','signal','positive',$tInsLayer,);

	my $tLayer = shift;
	my $tContext = shift || 'misc'; #misc board
	my $tType = shift || 'signal'; #signal
	my $tPolarity = shift || 'positive'; #positive negative
	my $tInsLayer = shift;
	$f->VOF;
	if ( defined $tInsLayer ){
		$f->COM('create_layer',layer => $tLayer,context => $tContext,type => $tType,polarity  => $tPolarity,ins_layer => $tInsLayer,);
	} else {
		$f->COM('create_layer',layer => $tLayer,context => $tContext,type => $tType,polarity  => $tPolarity,);
	}
	$f->VON;
}

sub igCreateLayers {  #创建多层 # igCreateLayer(@tLayers);
	for ( @_ ) {
		&igCreateLayer($_);
	}
}

#######################				设置			###################################

sub igAffeLayer {  #勾选层别 # igAffeLayer('no',@tLayer,); # igAffeLayer(@tLayer,);
	my $tAffeAct;
	if ( $_[0] eq 'yes' or $_[0] eq 'no' ){
		$tAffeAct = shift;
	} else {
		$tAffeAct = 'yes';
	}

	my @tLayer = @_;        ##layername
	for ( @tLayer ){
	$f->COM ('affected_layer',name=>$_,mode=>'single',affected=>$affected);
	}
}

#######################				其他			###################################

sub iGetPS { # 获取ps命令返回值 # my @PsPidData = iGetPS;
	my @PsPidData;
	if ( defined $_[0] ){
		my $tParameter = "@_";
		@PsPidData = `\\ps $tParameter`;
	} else {
		@PsPidData = `\\ps -ef`;
	}
	
	return (@PsPidData);
}

sub iGetAllPid {  #获取所有进程 Pid # my %AllPid = iGetAllPid; # my %AllPid = iGetAllPid(@PsPidData);
	my @PsPidData;
	if ( defined $_[0] ){
		@PsPidData = @_;
	} else {
		@PsPidData = `\\ps -ef`;
	}
	
	my %AllPid;
	for my $tLine ( @PsPidData ){
		chomp $tLine;
		## $tLine
		my ($tPid,$tPPid) = ( $tLine =~ /^\s*\w+\s+(\d+)\s+(\d+)\s+/i );
		if ( defined $tPid ){
			$AllPid{$tPid} = $tPPid || '';
		}
		if ( defined $tPPid ){
			$AllPid{$tPPid} = $tPPid || '';
		}
	}
	return (%AllPid);
}

sub iGetGenPidList {  #获取当前进程 所有运行 的Genesis|Genflex|InCAM Pid # my %GenPidList = iGetGenPidList; # my %GenPidList = iGetGenPidList(@PsPidData);
	my @PsPidData;
	if ( defined $_[0] ){
		@PsPidData = @_;
	} else {
		@PsPidData = `\\ps -ef`;
	}

	my %InCAMPidHash;
	for my $tLine ( @PsPidData ){
		chomp $tLine;
		## $tLine
		my ($tPid,$tPPid) = ( $tLine =~ /^\s*\w+\s+(\d+)\s+(\d+)\s+/i );
		if ( not defined $tPid ) {
			next;
		}
		if ( $tLine =~ m#(/bin/InCAM|/get/get|/get/gfx)# ) {
			$InCAMPidHash{$tPid} = $tPid;
		}
	}
	return (%InCAMPidHash);
}

sub iGetGenPid {  #获取当前进程对应运行的Genesis|Genflex|InCAM Pid # my $GenPID = iGetGenPid(); # my $GenPID = iGetGenPid($$,50,); # my $GenPID = iGetGenPid($$,50,@PsPidData);
	my $UserPid = shift || $$;
	my $MaxGet  = shift || 50;
	unless ( defined $UserPid ){
		return ();
	}
	my @PsPidData;
	if ( scalar(@_) > 20 ){
		@PsPidData = @_;
	} else {
		@PsPidData = `\\ps -ef`;
	}
	
	my %InCAMPidHash;
	my %PidToPPidHash;
	my $InCAMPidFlag = 'no';
	for my $tLine ( @PsPidData ){
		chomp $tLine;
		## $tLine
		my ($tPid,$tPPid) = ( $tLine =~ /^\s*\w+\s+(\d+)\s+(\d+)\s+/i );
		if ( (not defined $tPid) or (not defined $tPPid) ){
			next;
		}
		$PidToPPidHash{$tPid} = $tPPid;
		if ( $tLine =~ m#(/bin/InCAM|/get/get|/get/gfx)# ) {
			$InCAMPidHash{$tPid} = $tPid;
			$InCAMPidFlag = 'yes';
		}
	}
	#
	if ( $InCAMPidFlag eq 'no' ){
		return ();
	}
	#
	my $InCAMPid;
	for ( 0 .. $MaxGet ){
		my $tPPid = $PidToPPidHash{$UserPid};
		if ( defined $InCAMPidHash{$tPPid} ){
			$InCAMPid = $tPPid;
			return ($InCAMPid);
			last;
		} else {
			$UserPid = $tPPid;
		}
	}
	return ($InCAMPid);
}

sub iGetInCAMPid {  #获取当前进程所运行的InCAMPid # iGetInCAMPid($$,50,);
	my $UserPid = shift || $$;
	my $MaxGet  = shift || 50;
	unless ( defined $UserPid ){
		return ();
	}
	my @PsPidData = `ps -ef`;
	my %IncAMPidHash;
	my %PidToPPidHash;
	my $IncAMPidFlag = 'no';
	for my $tLine ( @PsPidData ){
		chomp $tLine;
		my ($tPid,$tPPid) = ( $tLine =~ /^\s*\w+\s+(\d+)\s+(\d+)\s+/i );
		$PidToPPidHash{$tPid} = $tPPid;
		if ( $tLine =~ m#/bin/InCAM# ) {
			$IncAMPidHash{$tPid} = $tPid;
			$IncAMPidFlag = 'yes';
		}
	}
	#
	if ( $IncAMPidFlag eq 'no' ){
		return ();
	}
	#
	my $InCAMPid;
	for ( 0 .. $MaxGet ){
		my $tPPid = $PidToPPidHash{$UserPid};
		if ( defined $IncAMPidHash{$tPPid} ){
			$InCAMPid = $tPPid;
			return ($InCAMPid);
			last;
		} else {
			$UserPid = $tPPid;
		}
	}
	return ($InCAMPid);
}

sub igGetWorkStep {  #获取料号有效的step # igGetWorkStep($JOB,$PnlStep);
	my $JOB  = shift;
	my $PnlStep = shift || 'panel';
	my @GetStep;
	my $GetStepMode = 'def';
	my $LoopDepth = 6;
	$f->INFO(entity_type => 'step',entity_path => "$JOB/$PnlStep",data_type => 'EXISTS');
	if ( $f->{doinfo}{gEXISTS} eq 'yes' ) {
		$GetStepMode = 'pnl';
		my @tRootStep = ($PnlStep,);
		for my $tNum ( 1 .. $LoopDepth ){
			my @tSrStep = &igGetSrStep(@tRootStep);
			if ( scalar (@tSrStep) != 0 ){
				@tRootStep = @tSrStep;
				push @GetStep,@tSrStep;
			} else {
				if ( $tNum == 1 ){
					$GetStepMode = 'def';
				}
				last;
			}
		}
	}

	if ( $GetStepMode eq 'def' ) {
		$f->INFO(entity_type => 'job',entity_path => "$JOB", data_type => 'STEPS_LIST');
		@GetStep = grep {$_ !~/err|old|bak/i} @{$f->{doinfo}{gSTEPS_LIST}};
	}

	if ( scalar(@GetStep) == 0 ) {
#		exit;
		return();
	}
#	print "@GetStep\n";
	return(@GetStep);
}

sub igEntityAttrVarConvert {  #实体属性变量转换 # my %AttrData = igEntityAttrVarConvert($JOB,$STEP,);
	my ($tJOB,$tSTEP,) = @_;
	$f->INFO(entity_type => 'step',entity_path => "$tJOB/$tSTEP",data_type => 'ATTR');
#	set gATTRname = ('.out_drill_full' '.out_drill_optional' '.out_rout_optional' '.array_with_rotation' '.flipped_out_of_date' '.sr_pcb' '.comment' '.out_name' '.assembly_proc_top' '.assembly_proc_bottom' '.all_eda_layers' '.flipped_of' '.pnl_scheme' '.pnl_pcb' '.pnl_class' '.pnl_place' '.source_name' '.rotated_of' '.transform_data' '.released_from' '.merge_processes' '.neutralization_info' '.design_center' '.neutralization_ss_layers' '.fs_direction_top' '.fs_direction_bottom' '.smt_direction_top' '.smt_direction_bottom' '.viacap_layer' '.etm_tester' '.etm_pin_style' '.etm_repear_fmt' '.se_coupon' '.se_coupon_mode' '.se_coupon_split_num' '.out_drill_order' '.out_rout_order' '.se_coupon_order' '.etm_adapter_h' '.rotation_angle')
#	set gATTRval  = ('no'              'no'                  'no'                 'no'                   'no'                   'no'      ''         ''          ''                   ''                      ''                'edit'        ''            ''         ''           ''           ''             ''            '0 +flip 1'       ''               ''                 ''                     ''               ''                          'right2left'        'right2left'           'right2left'         'right2left'            'none'          'mania'       'regular'        'none'            'none'       'start_end'       '1'                    '0'                '0'               '1'                '3750.000000'    '0.000000'       )
	my %tAttrData;
	for ( 0 .. scalar( @{$f->{doinfo}{gATTRname}} ) - 1 ) {
		$tAttrData{$f->{doinfo}{gATTRname}[$_]} = $f->{doinfo}{gATTRval}[$_] ;
	}
	return (%tAttrData);
}

sub igGetSrStep {  #获取SR STEP 列表 # my @SrStep = igGetSrStep(@Step);
	my @tRootStep = @_;
	my @tSubStep;
	for my $tStep ( @tRootStep ) {
		$f->INFO(entity_type => 'step',entity_path => "$JOB/$tStep",data_type => 'SR',parameters => "step");
		#set gSRstep = ('edit' 'edit' 'edit' 'zk' 'edit' 'edit' 'edit' 'drl' 'lp')
		 push @tSubStep,@{$f->{doinfo}{gSRstep}};
	}
	return ( &iClearDup( @tSubStep ) );
}

sub igDelLayers {  #删除层别 # igDelLayers(@DelLayers);
	$f->VOF;
	for ( @_ ) {
		$f->COM('delete_layer', layer => $_);
	}
	$f->VON;
}

sub igJobMatrixConv {  # Job Matrix 数据转换 # my %JobMatrixData = igJobMatrixConv($JOB);
	my $CurrJob = shift;
	my %JobMatrixData;
	if ( defined $CurrJob ) {
		$f->INFO(entity_type => 'matrix',entity_path => "$CurrJob/matrix",data_type => 'ROW',);
		%JobMatrixData = iHashArrConvHash('gROWrow',\%{$f->{doinfo}},);
		%{$JobMatrixData{'LayerToRow'}} = iArrMergeHash(\@{$f->{doinfo}{gROWname}},\@{$f->{doinfo}{gROWrow}},);
		
	}
	return(%JobMatrixData);
}

sub igJobMatrixDispose {  #料号Matrix处理 # our %JobMatrix = igJobMatrixDispose($JOB);
	my $CurrJob = shift;
	#3399ff 68%  覆盖  #3399ff 50%  覆盖
	if ( "$CurrJob" ne '' ) {
#		$f->INFO(entity_type => 'matrix',entity_path => "$CurrJob/matrix",data_type => 'ROW',parameters => "context+layer_type+name+row+side+type");
		$f->INFO(entity_type => 'matrix',entity_path => "$CurrJob/matrix",data_type => 'ROW',parameters => "context+drl_end+drl_start+layer_type+name+polarity+row+side+type");
		my %JobMatrix;

#		my @LayerTypeFilter	 = ( "清除","全部","板层","线路","内层","外层","钻孔","阻焊","字符","钢网","Misc钻孔", );
#		my @LayerTypeFilterEn = ( "Clear","All","Borad","Signal","Inner","Outer","Dril","SolderMask","SilkScreen","SolderPaste","MiscDril", );
#		for ( 0 .. scalar( @LayerTypeFilterEn ) - 1 ){
#			$JobMatrix{'ConvEnToCn'}{$LayerTypeFilterEn[$_]} = $LayerTypeFilter[$_] ;
#			$JobMatrix{'ConvCnToEn'}{$LayerTypeFilter[$_]} = $LayerTypeFilterEn[$_] ;
#		}

		for my $gROWrow (@{$f->{doinfo}{gROWrow}}){
			my $tNum = $gROWrow -1;
			my $tLayerName = $f->{doinfo}{gROWname}[$tNum];
			if ( $f->{doinfo}{gROWtype}[$tNum] eq 'layer' ){
				push @{$JobMatrix{"SumData"}{LayerRow}},$gROWrow;
				push @{$JobMatrix{"SumData"}{Layers}},$f->{doinfo}{gROWname}[$tNum];
				#
				$JobMatrix{"RowData"}{$gROWrow}{Layer} = $f->{doinfo}{gROWname}[$tNum];
				$JobMatrix{"RowData"}{$gROWrow}{'全部'} = 'Yes';
				$JobMatrix{"RowData"}{$gROWrow}{'All'} = 'Yes';
				#
				$JobMatrix{"LayersData"}{$tLayerName}{'Row'} = $gROWrow;
				$JobMatrix{"LayersData"}{$tLayerName}{'全部'} = 'Yes';
				$JobMatrix{"LayersData"}{$tLayerName}{'All'} = 'Yes';
				if ( $f->{doinfo}{gROWcontext}[$tNum] eq 'board'){
					$JobMatrix{"RowData"}{$gROWrow}{'板层'} = 'Yes';
					$JobMatrix{"LayersData"}{$tLayerName}{'板层'} = 'Yes';

					$JobMatrix{"RowData"}{$gROWrow}{'Borad'} = 'Yes';
					$JobMatrix{"LayersData"}{$tLayerName}{'Borad'} = 'Yes';
					#
					push @{$JobMatrix{"SumData"}{Board}},$f->{doinfo}{gROWname}[$tNum];
					if ( $f->{doinfo}{gROWlayer_type}[$tNum] eq 'signal' || $f->{doinfo}{gROWlayer_type}[$tNum] eq 'power_ground' || $f->{doinfo}{gROWlayer_type}[$tNum] eq 'mixed' ) {
						push @{$JobMatrix{"SumData"}{Signal}},$f->{doinfo}{gROWname}[$tNum];
						#
						$JobMatrix{"RowData"}{$gROWrow}{'线路'} = 'Yes';
						$JobMatrix{"LayersData"}{$tLayerName}{'线路'} = 'Yes';

						$JobMatrix{"RowData"}{$gROWrow}{'Signal'} = 'Yes';
						$JobMatrix{"LayersData"}{$tLayerName}{'Signal'} = 'Yes';

						if ( $f->{doinfo}{gROWlayer_type}[$tNum] eq 'signal'){
							$JobMatrix{"RowData"}{$gROWrow}{'Color'} = '#FDC74D';
							$JobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#98B0A6';
							#
							$JobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#FDC74D';
							$JobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#98B0A6';
						} elsif ( $f->{doinfo}{gROWlayer_type}[$tNum] eq 'power_ground') {
							$JobMatrix{"RowData"}{$gROWrow}{'Color'} = '#E6C412';
							$JobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#8CAE89';
							#
							$JobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#E6C412';
							$JobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#8CAE89';
						} elsif ( $f->{doinfo}{gROWlayer_type}[$tNum] eq 'mixed' ) {
							$JobMatrix{"RowData"}{$gROWrow}{'Color'} = '#CCCCA5';
							$JobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#7FB2D2';
							#
							$JobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#CCCCA5';
							$JobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#7FB2D2';
						}
						#
						if ( $f->{doinfo}{gROWside}[$tNum] eq 'top' || $f->{doinfo}{gROWside}[$tNum] eq 'bottom' ){
							push @{$JobMatrix{"SumData"}{Outer}},$f->{doinfo}{gROWname}[$tNum];
							#
							$JobMatrix{"RowData"}{$gROWrow}{'外层'} = 'Yes';
							$JobMatrix{"LayersData"}{$tLayerName}{'外层'} = 'Yes';

							$JobMatrix{"RowData"}{$gROWrow}{'Outer'} = 'Yes';
							$JobMatrix{"LayersData"}{$tLayerName}{'Outer'} = 'Yes';

							if ( $f->{doinfo}{gROWside}[$tNum] eq 'top' ){
								push @{$JobMatrix{"SumData"}{TopSignal}},$f->{doinfo}{gROWname}[$tNum];
								$JobMatrix{"RowData"}{$gROWrow}{'TopSignalLayer'} = 'Yes';
								$JobMatrix{"LayersData"}{$tLayerName}{'TopSignalLayer'} = 'Yes';
							} elsif ( $f->{doinfo}{gROWside}[$tNum] eq 'bottom' ){
								push @{$JobMatrix{"SumData"}{BottomSignal}},$f->{doinfo}{gROWname}[$tNum];
								$JobMatrix{"RowData"}{$gROWrow}{'BottomSignalLayer'} = 'Yes';
								$JobMatrix{"LayersData"}{$tLayerName}{'BottomSignalLayer'} = 'Yes';
							}
						} elsif ( $f->{doinfo}{gROWside}[$tNum] eq 'inner' ) {
							push @{$JobMatrix{"SumData"}{Inner}},$f->{doinfo}{gROWname}[$tNum];
							#
							$JobMatrix{"RowData"}{$gROWrow}{'内层'} = 'Yes';
							$JobMatrix{"LayersData"}{$tLayerName}{'内层'} = 'Yes';

							$JobMatrix{"RowData"}{$gROWrow}{'Inner'} = 'Yes';
							$JobMatrix{"LayersData"}{$tLayerName}{'Inner'} = 'Yes';
						}
					} elsif ( $f->{doinfo}{gROWlayer_type}[$tNum] eq 'solder_mask' ) {
						push @{$JobMatrix{"SumData"}{SolderMask}},$f->{doinfo}{gROWname}[$tNum];
						if ( $f->{doinfo}{gROWside}[$tNum] eq 'top' ){
							push @{$JobMatrix{"SumData"}{TopSolderMask}},$f->{doinfo}{gROWname}[$tNum];
							$JobMatrix{"RowData"}{$gROWrow}{'TopSolderMaskLayer'} = 'Yes';
							$JobMatrix{"LayersData"}{$tLayerName}{'TopSolderMaskLayer'} = 'Yes';

						} elsif ( $f->{doinfo}{gROWside}[$tNum] eq 'bottom' ){
							push @{$JobMatrix{"SumData"}{BottomSolderMask}},$f->{doinfo}{gROWname}[$tNum];
							$JobMatrix{"RowData"}{$gROWrow}{'BottomSolderMaskLayer'} = 'Yes';
							$JobMatrix{"LayersData"}{$tLayerName}{'BottomSolderMaskLayer'} = 'Yes';
						}
						#
						$JobMatrix{"RowData"}{$gROWrow}{'阻焊'} = 'Yes';

						$JobMatrix{"RowData"}{$gROWrow}{'SolderMask'} = 'Yes';

						$JobMatrix{"RowData"}{$gROWrow}{'Color'} = '#00A279';
						$JobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#1A9DBC';
						#
						$JobMatrix{"LayersData"}{$tLayerName}{'阻焊'} = 'Yes';

						$JobMatrix{"LayersData"}{$tLayerName}{'SolderMask'} = 'Yes';

						$JobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#00A279';
						$JobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#1A9DBC';
					} elsif ( $f->{doinfo}{gROWlayer_type}[$tNum] eq 'silk_screen' ) {
						push @{$JobMatrix{"SumData"}{SilkScreen}},$f->{doinfo}{gROWname}[$tNum];
						if ( $f->{doinfo}{gROWside}[$tNum] eq 'top' ){
							push @{$JobMatrix{"SumData"}{TopSilkScreen}},$f->{doinfo}{gROWname}[$tNum];
							$JobMatrix{"RowData"}{$gROWrow}{'TopSilkScreenLayer'} = 'Yes';
							$JobMatrix{"LayersData"}{$tLayerName}{'TopSilkScreenLayer'} = 'Yes';
						} elsif ( $f->{doinfo}{gROWside}[$tNum] eq 'bottom' ){
							push @{$JobMatrix{"SumData"}{BottomSilkScreen}},$f->{doinfo}{gROWname}[$tNum];
							$JobMatrix{"RowData"}{$gROWrow}{'BottomSilkScreenLayer'} = 'Yes';
							$JobMatrix{"LayersData"}{$tLayerName}{'BottomSilkScreenLayer'} = 'Yes';
						}
						#
						$JobMatrix{"RowData"}{$gROWrow}{'字符'} = 'Yes';

						$JobMatrix{"RowData"}{$gROWrow}{'SilkScreen'} = 'Yes';

						$JobMatrix{"RowData"}{$gROWrow}{'Color'} = '#FFFFFF';
						$JobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#99CCFF';
						#
						$JobMatrix{"LayersData"}{$tLayerName}{'字符'} = 'Yes';

						$JobMatrix{"LayersData"}{$tLayerName}{'SilkScreen'} = 'Yes';

						$JobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#FFFFFF';
						$JobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#99CCFF';
					} elsif ( $f->{doinfo}{gROWlayer_type}[$tNum] eq 'solder_paste' ) {
						push @{$JobMatrix{"SumData"}{SolderPaste}},$f->{doinfo}{gROWname}[$tNum];
						#
						$JobMatrix{"RowData"}{$gROWrow}{'钢网'} = 'Yes';

						$JobMatrix{"RowData"}{$gROWrow}{'SolderPaste'} = 'Yes';

						$JobMatrix{"RowData"}{$gROWrow}{'Color'} = '#FFFFCE';
						$JobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#99CCE7';
						#
						$JobMatrix{"LayersData"}{$tLayerName}{'钢网'} = 'Yes';

						$JobMatrix{"LayersData"}{$tLayerName}{'SolderPaste'} = 'Yes';

						$JobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#FFFFCE';
						$JobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#99CCE7';
					} elsif ( $f->{doinfo}{gROWlayer_type}[$tNum] eq 'drill' ) {
						push @{$JobMatrix{"SumData"}{Drill}},$f->{doinfo}{gROWname}[$tNum];
						$JobMatrix{"RowData"}{$gROWrow}{'钻孔'} = 'Yes';

						$JobMatrix{"RowData"}{$gROWrow}{'Dril'} = 'Yes';

						$JobMatrix{"RowData"}{$gROWrow}{'Color'} = '#AFAFAF';
						$JobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#71A4D7';
						#
						$JobMatrix{"LayersData"}{$tLayerName}{'钻孔'} = 'Yes';

						$JobMatrix{"LayersData"}{$tLayerName}{'Dril'} = 'Yes';

						$JobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#AFAFAF';
						$JobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#71A4D7';
						$JobMatrix{"RowData"}{$gROWrow}{'DrlStart'} = $f->{doinfo}{gROWdrl_start}[$tNum];
						$JobMatrix{"LayersData"}{$tLayerName}{'DrlStart'} = $f->{doinfo}{gROWdrl_start}[$tNum];

						$JobMatrix{"RowData"}{$gROWrow}{'DrlEnd'} = $f->{doinfo}{gROWdrl_end}[$tNum];
						$JobMatrix{"LayersData"}{$tLayerName}{'DrlEnd'} = $f->{doinfo}{gROWdrl_end}[$tNum];
					} elsif ( $f->{doinfo}{gROWlayer_type}[$tNum] eq 'rout' ) {
						push @{$JobMatrix{"SumData"}{Rout}},$f->{doinfo}{gROWname}[$tNum];
						$JobMatrix{"RowData"}{$gROWrow}{'Color'} = '#D4D1C9';
						$JobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#83B5E4';
						#
						$JobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#D4D1C9';
						$JobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#83B5E4';
						$JobMatrix{"RowData"}{$gROWrow}{'DrlStart'} = $f->{doinfo}{gROWdrl_start}[$tNum];
						$JobMatrix{"LayersData"}{$tLayerName}{'DrlStart'} = $f->{doinfo}{gROWdrl_start}[$tNum];

						$JobMatrix{"RowData"}{$gROWrow}{'DrlEnd'} = $f->{doinfo}{gROWdrl_end}[$tNum];
						$JobMatrix{"LayersData"}{$tLayerName}{'DrlEnd'} = $f->{doinfo}{gROWdrl_end}[$tNum];
					} elsif ( $f->{doinfo}{gROWlayer_type}[$tNum] eq 'document' ) {
						push @{$JobMatrix{"SumData"}{Document}},$f->{doinfo}{gROWname}[$tNum];
						$JobMatrix{"RowData"}{$gROWrow}{'Color'} = '#9BDBDB';
						$JobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#67BAED';
						#
						$JobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#9BDBDB';
						$JobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#67BAED';
					} else {
						push @{$JobMatrix{"SumData"}{Other}},$f->{doinfo}{gROWname}[$tNum];
						#
						$JobMatrix{"RowData"}{$gROWrow}{'Color'} = '#9BDBDB';
						$JobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#67BAED';
						#
						$JobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#9BDBDB';
						$JobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#67BAED';
					}
				} else {
					push @{$JobMatrix{"SumData"}{Misc}},$f->{doinfo}{gROWname}[$tNum];
					$JobMatrix{"RowData"}{$gROWrow}{'Color'} = '#9BDBDB';
					$JobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#67BAED';
					#
					$JobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#9BDBDB';
					$JobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#67BAED';

					if ( $f->{doinfo}{gROWlayer_type}[$tNum] eq 'drill' ) {
						push @{$JobMatrix{"SumData"}{MiscDrill}},$f->{doinfo}{gROWname}[$tNum];
						$JobMatrix{"RowData"}{$gROWrow}{'Misc钻孔'} = 'Yes';

						$JobMatrix{"RowData"}{$gROWrow}{'MiscDril'} = 'Yes';

						$JobMatrix{"RowData"}{$gROWrow}{'Color'} = '#AFAFAF';
						$JobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#71A4D7';
						#
						$JobMatrix{"LayersData"}{$tLayerName}{'Misc钻孔'} = 'Yes';

						$JobMatrix{"LayersData"}{$tLayerName}{'MiscDril'} = 'Yes';

						$JobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#AFAFAF';
						$JobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#71A4D7';
						$JobMatrix{"RowData"}{$gROWrow}{'DrlStart'} = $f->{doinfo}{gROWdrl_start}[$tNum];
						$JobMatrix{"LayersData"}{$tLayerName}{'DrlStart'} = $f->{doinfo}{gROWdrl_start}[$tNum];

						$JobMatrix{"RowData"}{$gROWrow}{'DrlEnd'} = $f->{doinfo}{gROWdrl_end}[$tNum];
						$JobMatrix{"LayersData"}{$tLayerName}{'DrlEnd'} = $f->{doinfo}{gROWdrl_end}[$tNum];
					} elsif ( $f->{doinfo}{gROWlayer_type}[$tNum] eq 'rout' ) {
						push @{$JobMatrix{"SumData"}{MiscRout}},$f->{doinfo}{gROWname}[$tNum];
						$JobMatrix{"RowData"}{$gROWrow}{'Color'} = '#D4D1C9';
						$JobMatrix{"RowData"}{$gROWrow}{'SelColor'} = '#83B5E4';
						#
						$JobMatrix{"LayersData"}{$tLayerName}{'Color'} = '#D4D1C9';
						$JobMatrix{"LayersData"}{$tLayerName}{'SelColor'} = '#83B5E4';
						$JobMatrix{"RowData"}{$gROWrow}{'DrlStart'} = $f->{doinfo}{gROWdrl_start}[$tNum];
						$JobMatrix{"LayersData"}{$tLayerName}{'DrlStart'} = $f->{doinfo}{gROWdrl_start}[$tNum];

						$JobMatrix{"RowData"}{$gROWrow}{'DrlEnd'} = $f->{doinfo}{gROWdrl_end}[$tNum];
						$JobMatrix{"LayersData"}{$tLayerName}{'DrlEnd'} = $f->{doinfo}{gROWdrl_end}[$tNum];
					}

				}
			} else {
				push @{$JobMatrix{"SumData"}{Empty}},$gROWrow;
			}
		}
		return (%JobMatrix);
	} else {
		return ();
	}
}


##############								Tk							#####################################################################

#(标题,示范内容,按钮[ok|okcancel|yesno|yesnocancel|abortretryignore|retrycancel],图标[info|question|warning|error],)

sub iTkMsgBox {  #一次性当前提示框 # iTkMsgBox("JOB不存在!","JOB不存在,脚本退出!","ok","warning",);
#	use Tk;
	&iLoadModules("Tk");
#	my ($tTitle,$tIco,$tButtonType,$tMsg,$DefButton,) = (@_);
	my ($tTitle,$tMsg,$tButtonType,$tIco,$DefButton,) = (@_);
	my $tMw = MainWindow->new(-title =>".");
	$tMw->geometry("0x0");
	$tMw->update;
	$tMw->withdraw;
	$tMw->attributes('-topmost',1);
#	my $MsgOut = $tMw->messageBox(-type => "$tButtonType",-message => "$tMsg",-icon => "$tIco",-title => "$tTitle",);
	my $MsgOut;
	if ( defined $DefButton ) {
		$MsgOut = $tMw->messageBox(-title => $tTitle,-message => $tMsg,-type => $tButtonType || 'ok',-icon => $tIco || 'warning',-default => $DefButton,);
	} else {
		$MsgOut = $tMw->messageBox(-title => $tTitle,-message => $tMsg,-type => $tButtonType || 'ok',-icon => $tIco || 'warning',);
	}
	
	$tMw->destroy;
	MainLoop();
	$MsgOut = lc($MsgOut);
	chomp $MsgOut;
	return ($MsgOut);
}

sub iTkMwMsg {  #当前$mw提示框 # iTkMwMsg($mw,"JOB不存在!","JOB不存在,脚本退出!","ok","warning",);
#	my ($mw,$tTitle,$tIco,$tButtonType,$tMsg,$DefButton,) = (@_);
	my ($mw,$tTitle,$tMsg,$tButtonType,$tIco,$DefButton,) = (@_);
#	my $MsgOut = $mw->messageBox(-type => "$tButtonType",-message => "$tMsg",-icon => "$tIco",-title => "$tTitle",);
	my $MsgOut;
	if ( defined $DefButton ) {
		$MsgOut = $mw->messageBox(-title => $tTitle,-message => $tMsg,-type => $tButtonType || 'ok',-icon => $tIco || 'warning',-default => $DefButton,);
	} else {
		$MsgOut = $mw->messageBox(-title => $tTitle,-message => $tMsg,-type => $tButtonType || 'ok',-icon => $tIco || 'warning',);
	}
	$MsgOut = lc($MsgOut);
	chomp $MsgOut;
	return ($MsgOut);
}


##############						兼容旧脚本						#####################################################################

sub ClearDup {  #数组去重 #iClearDup
	return ( &iClearDup(@_) );
}

######
sub GetImageFile {  #获取并设置图片 #iTkxGetImageFile
	return ( &iTkxGetImageFile(@_) );
}

sub MsgBox {  #一次性当前提示框 #iTkxMsgBox
	return ( &iTkxMsgBox(@_) );
}

sub iTkxMsg {  #当前$mw提示框 #iTkxMwMsg
	return ( &iTkxMwMsg(@_) );
}

######
sub EntityAttrVarConvert {  #实体属性变量转换 #igEntityAttrVarConvert
	return ( &igEntityAttrVarConvert(@_) );
}

sub GetSrStep {  #获取SR STEP 列表 #igGetSrStep
	return ( &igGetSrStep(@_) );
}

sub DelLayers {  #删除层别 #igDelLayers
	return ( &igDelLayers(@_) );
}

sub JobMatrixDispose {	#料号Matrix处理 #igJobMatrixDispose
	return ( &igJobMatrixDispose(@_) );
}

################################################################################
sub iLoadModules { # 加载模块(欺骗PDK) # &iLoadModules("Tk");
	for my $tModules (@_){
		eval("use $tModules");
	}
}

1;