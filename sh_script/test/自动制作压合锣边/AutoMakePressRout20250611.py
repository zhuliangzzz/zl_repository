#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:AutoMakePressRout.py
   @author:zl
   @time: 2025/6/6 9:40
   @software:PyCharm
   @desc:
"""
import os
import platform
import re
import sys
from PyQt4 import QtCore, QtGui
if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
import genClasses_zl as gen
from genesisPackages_zl import get_layer_limits
from get_erp_job_info import get_inplan_mrp_info, get_inplan_all_flow


class AutoMakePressRout(object):
    def __init__(self):
        self.jobname = jobname[:13]
        mrp_info = get_inplan_mrp_info(self.jobname.upper())
        if not mrp_info:
            return "没有压合数据"
        self.job = gen.Job(jobname)
        self.stepname = 'panel'
        if self.stepname not in self.job.getSteps():
            return "没有panel"
        self.output_path = '/windows/174.file/CNC/压合后锣边框'
        self.pnlrout_dic = {}
        for data in mrp_info:
            if data['PROCESS_NUM'] > 1:
                pnlrout = 'pnl_rout%s' % (data['PROCESS_NUM'] - 1)
                self.pnlrout_dic[pnlrout] = [data['FROMLAY'], data['TOLAY']]

    def make_press_rout(self):
        print(self.pnlrout_dic)
        step = gen.Step(self.job, self.stepname)
        gSRstep = step.DO_INFO('-t step -e %s/%s  -d SR' % (jobname, self.stepname)).get('gSRstep')
        for i, srname in enumerate(gSRstep):
            if re.search('set|edit', srname):
                self.set_order = i + 1
                break
        step.initStep()
        keys = sorted(self.pnlrout_dic.keys(), key=lambda i: int(i.split('pnl_rout')[1]))
        lastkey = keys[-1]
        inplan_all_flow = get_inplan_all_flow(self.jobname, True)
        output_routs = []
        for data in inplan_all_flow:
            if data['WORK_CENTER_CODE'] == '打靶' and data['PROCESS_DESCRIPTION'] == 'X-RAY打靶':
                note_string = data['NOTE_STRING']
                # print(note_string)
                search = re.search('“(.*?)”', str(note_string))
                if not search:
                    continue
                pnl_rout_n = search.group(1)
                inn_layer = None
                if pnl_rout_n.upper() == 'T':
                    pnl_rout = lastkey
                    inn_layer = 'inn'
                else:
                    pnl_rout = 'pnl_rout%s' % pnl_rout_n
                if step.isLayer(pnl_rout):
                    # print(pnl_rout, self.pnlrout_dic.get(pnl_rout))
                    if not inn_layer:
                        inn_layer = 'inn%s%s' % (self.pnlrout_dic.get(pnl_rout)[0].replace('L', ''),
                                                 self.pnlrout_dic.get(pnl_rout)[1].replace('L', ''))
                        print(pnl_rout, inn_layer)
                    tmp_pnl_rout = '%s+++' % pnl_rout
                    step.removeLayer(tmp_pnl_rout)
                    step.COM('compensate_layer,source_layer=%s,dest_layer=%s,dest_layer_type=document' % (pnl_rout, tmp_pnl_rout))
                    # step.affect(pnl_rout)
                    # step.copySel(tmp_pnl_rout)
                    # step.unaffectAll()
                    step.affect(tmp_pnl_rout)
                    step.setFilterTypes('pad')
                    step.selectAll()
                    step.resetFilter()
                    if step.Selected_count():
                        step.selectDelete()
                    step.unaffectAll()
                    step.affect(inn_layer)
                    step.copySel(tmp_pnl_rout)
                    step.selectChange('r3100')
                    step.unaffectAll()
                    xmin, ymin, xmax, ymax = get_layer_limits(step, tmp_pnl_rout)
                    # xmin, ymin, xmax, ymax = xmin + 1.2, ymin + 1.2, xmax - 1.2, ymax - 1.2
                    step.display(tmp_pnl_rout)
                    step.addLine(xmax - 13.2, ymin + 1.2, xmax - 13.2, ymin + 4.2, 'r2400')
                    step.addLine(xmax - 13.2, ymin + 4.2, xmax - 9.6, ymin + 4.2, 'r2400')
                    step.addLine(xmax - 9.6, ymin + 4.2, xmax - 9.6, ymin + 1.2, 'r2400')
                    step.COM('delete_feat,mode=intersect,index=2,x=%s,y=%s,tol=76.645' % (xmax - 10.4, ymin + 1.2))
                    self.job.matrix.modifyRow(tmp_pnl_rout, type='rout')
                    step.COM('chain_add,layer=%s,chain=1,size=2.4,comp=right,flag=0,feed=0,speed=0' % tmp_pnl_rout)
                    # step.COM('chain_add,layer=%s,chain_type=regular_chain,chain=1,size=2.4,flag=0,feed=0,speed=0,infeed_speed=0,retract_speed=0,pressure_foot=none,comp=right,repeat=no,plunge=no' % tmp_pnl_rout)
                    step.clearAll()
                    output_routs.append(tmp_pnl_rout)
                    # self.output(tmp_pnl_rout)
        for output_rout in output_routs:
            self.output(output_rout)
            step.removeLayer('_nc_%s_out_' % output_rout)
            # step.removeLayer(output_rout)
        print('success')
        QtGui.QMessageBox.information(None, u'提示', u'压合锣边下发成功!!!')


    def output(self, layer):
        ncPre = 'nc_%s' % layer
        offset_x, offset_y, op_scalex, scale_y, op_scaley, scale_center_y, xmirror, ymirror = 0, 0, 1, 1, 1, 1, 'no', 'no'

        if os.environ.get('INCAM_PRODUCT'):
            self.job.VOF()
            self.job.COM('nc_delete,layer=%s,ncset=%s' % (layer, ncPre))
            self.job.VON()
            self.job.COM('nc_create,ncset=%s,device=excellon_hdi,lyrs=%s,thickness=0' % (ncPre, layer))
            self.job.COM(
                'nc_set_advanced_params,layer=%s,ncset=%s,parameters=(rout_arc_as_ij=no)(out_exc_old_sr_syntax=no)' % (
                layer, ncPre))
            self.job.COM('nc_set_current,job=%s,step=%s,layer=%s,ncset=%s' % (jobname, self.stepname, layer, ncPre))
            self.job.COM(
                'nc_set_file_params,output_path=%s,output_name=%s.%s,zeroes=trailing,units=mm,tool_units=mm,nf1=3,nf2=3,'
                'decimal=yes,modal_coords=no,single_sr=yes,sr_zero_set=no,repetitions=sr,incremental=no,ext_layer=ncr-drill,sr_zero_layer=,'
                'ccw=no,short_lines=none,allow_no_chain_f=no,no_chain_as_slot=no,keep_table_order=yes,max_arc_angle=180,comp_short_slot=no,'
                'gscale_file_name=,layer_datum=bottom_left,gscle_align_angle=0,gscl_offset_x=0,gscl_offset_y=0' % (
                self.output_path, jobname, layer.replace('+', '')))
            self.job.COM(
                'nc_register,angle=0,xoff=0,yoff=0,version=1,xorigin=%s,yorigin=%s,xscale=%s,yscale=%s,xscale_o=%s,yscale_o=%s,xmirror=%s,ymirror=%s' % (offset_x, offset_y, op_scalex, scale_y, op_scaley, scale_center_y, xmirror, ymirror))
            self.job.COM('nc_order,serial=1,sr_line=%s,sr_nx=1,sr_ny=1,mode=lrbt,snake=yes' % self.set_order)
            # self.job.COM('top_tab,tab=NC Parameters Page')
            # self.job.COM('open_sets_manager,test_current=no')
            # self.job.PAUSE("请确认是否需要调整rout板顺序")
            self.job.COM('nc_cre_output,layer=%s,ncset=%s' % (layer, ncPre))
            # self.job.VOF()
            # self.job.matrix.deleteRow('_nc_%s_out_' % layer)
            # self.job.VON()
        else:
            # unicode_path = u'\\\\192.168.2.174\\GCfiles\\CNC\\压合后锣边框'
            unicode_path = u'D:\\disk\\rout\\%s' % jobname.upper()
            self.output_path = unicode_path.encode(sys.getfilesystemencoding())
            # print('aaaa', self.output_path+ '\n')
            self.job.COM("ncrset_page_open")
            self.job.COM("ncrset_cur,job=%s,step=%s,layer=%s,ncset=" % (jobname, self.stepname, layer))
            self.job.VOF()
            self.job.COM('ncrset_delete,name=%s' % ncPre)
            self.job.VON()
            self.job.COM("ncrset_create,name=%s" % ncPre)
            self.job.COM('ncrset_cur,job=%s,step=%s,layer=%s,ncset=%s' % (jobname, self.stepname, layer, ncPre))
            self.job.COM("ncr_set_machine,machine=excellon_hdi,thickness=0")
            self.job.COM("ncr_set_params,format=excellon2,zeroes=trailing,units=mm,tool_units=mm,nf1=3,nf2=3,decimal=yes,modal_coords=no,single_sr=yes,sr_zero_set=no,repetitions=sr,drill_layer=ncr-drill,sr_zero_drill_layer=,break_sr=no,ccw=no,short_lines=none,press_down=no,last_z_up=16,max_arc_ang=180,sep_lyrs=no,allow_no_chain_f=no,keep_table_order=yes")
            self.job.COM("ncr_register,angle=0,mirror=%s,xoff=0,yoff=0,version=1,xorigin=%s,yorigin=%s,xscale=%s,yscale=%s,xscale_o=%s,yscale_o=%s" % (xmirror, offset_x, offset_y, op_scalex, op_scaley, scale_center_y, scale_center_y))
            self.job.COM("ncr_order,sr_line=%s,sr_nx=1,sr_ny=1,serial=1,optional=no,mode=lrbt,snake=yes,full=1,nx=0,ny=0" % self.set_order)
            # === 2023.03.11 转自多层，使用上次排刀序进行输出 ===
            # my $rout_table_list = "$logpath/$i"."_table_list"
            # my $now_table_list_path = "$logpath/$i"."_now_table_list"
            # &sort_table_by_last($i,$rout_table_list,$now_table_list_path)
            # $f->PAUSE("please check rout Order");
            self.job.COM("ncr_table_close")
            self.job.COM("ncr_cre_rout")
            self.job.COM("ncr_ncf_export,dir=%s,name=%s.%s" % (self.output_path, jobname, layer.replace('+', '')))
            # self.job.COM("ncr_ncf_export,dir=\\\\192.168.2.174\GCfiles\CNC\压合后锣边框,name=%s.%s" % (jobname, layer.replace('+', '')))

            # 2023.03.10 参考多层 输出指定锣带table 到user 路径唐成
            # self.job.COM("ncrset_units,units=mm")
            # self.job.COM("ncr_report,path=$rout_table_list")


        '''
        foreach my $i (@selectlayers) {
		# --检查锣带销钉是否对称
		my $ncPre = "nc_".$i;
		my $pre_name = '';
		if ( defined $ENV{INCAM_PRODUCT} ) {
			$f->PAUSE("incam");
			$f->VOF;
				$f->COM("nc_delete,layer=$i,ncset=$ncPre");
			$f->VON;
			$f->COM("nc_create,ncset=$ncPre,device=excellon_hdi,lyrs=$i,thickness=0");
			$f->COM("nc_set_advanced_params,layer=$i,ncset=$ncPre,parameters=(rout_arc_as_ij=no)(out_exc_old_sr_syntax=no)");
			$f->COM("nc_set_current,job=$JOB,step=$op_step,layer=$i,ncset=$ncPre");
			$f->COM("nc_set_file_params,output_path=$current_path,output_name=$JOB.$i,zeroes=trailing,units=mm,tool_units=mm,nf1=3,nf2=3,decimal=yes,modal_coords=no,single_sr=yes,sr_zero_set=no,repetitions=sr,incremental=no,ext_layer=ncr-drill,sr_zero_layer=,ccw=no,short_lines=none,allow_no_chain_f=no,no_chain_as_slot=no,keep_table_order=yes,max_arc_angle=180,comp_short_slot=no,gscale_file_name=,layer_datum=bottom_left,gscle_align_angle=0,gscl_offset_x=0,gscl_offset_y=0");
			$f->COM("nc_register,angle=0,xoff=0,yoff=0,version=1,xorigin=$offset_x,yorigin=$offset_y,xscale=$op_scalex,yscale=$scale_y,xscale_o=$op_scaley,yscale_o=$scale_center_y,xmirror=$xmirror,ymirror=$ymirror");			
			$f->COM("nc_order,serial=1,sr_line=$set_order,sr_nx=1,sr_ny=1,mode=lrbt,snake=yes");
			#$f->COM("top_tab,tab=NC Parameters Page");
			#$f->COM("open_sets_manager,test_current=no");
			$f->PAUSE("请确认是否需要调整rout板顺序");
			$f->COM("nc_cre_output,layer=$i,ncset=$ncPre");
			$f->VOF;
			$f->COM("delete_layer,layer=_nc_$i\_out_");
			$f->VON;
		} else {
			#$f->PAUSE("Genesis");
			# --输出时料号名切换大写，后缀不变  --20191118  AresHe
            our $JobName = uc($JOB);
			# 做一个记录，是否用HDI的脚本输出
			my $recode_output_job_path = "C:/tmp/recode_hdi_output_name";
			open(FILE, '>',"$recode_output_job_path") or die "无法打开文件 $recode_output_job_path";;
			print FILE $JOB;
			close FILE;
			
            if (($i eq 'jp-rout' || $i eq 'ccd-rout') && $op_ccd_rout == 1) {
				# === 出货单元光学CCD锣带输出 ===
				
				&output_ccd_rout($i);
				#my $output_file = "$current_path/$JobName".uc($i);
				#if ($i eq 'jp.rou' ) { $output_file = "$current_path/$JobName.$i";}
				#&add_config_data($output_file,%rout_kanife_paramete);
				
			} else {
				$f->COM("ncrset_page_open");
				$f->COM("ncrset_cur,job=$JOB,step=$op_step,layer=$i,ncset=");
				$f->VOF;
					$f->COM("ncrset_delete,name=$ncPre");
				$f->VON;
				$f->COM("ncrset_create,name=$ncPre");
				$f->COM("ncrset_cur,job=$JOB,step=$op_step,layer=$i,ncset=$ncPre");
				$f->COM("ncr_set_machine,machine=excellon_hdi,thickness=0");
				$f->COM("ncr_set_params,format=excellon2,zeroes=trailing,units=mm,tool_units=mm,nf1=3,nf2=3,decimal=yes,modal_coords=no,single_sr=yes,sr_zero_set=no,repetitions=sr,drill_layer=ncr-drill,sr_zero_drill_layer=,break_sr=no,ccw=no,short_lines=none,press_down=no,last_z_up=16,max_arc_ang=180,sep_lyrs=no,allow_no_chain_f=no,keep_table_order=yes");
	
				$f->COM("ncr_register,angle=0,mirror=$xmirror,xoff=0,yoff=0,version=1,xorigin=$offset_x,yorigin=$offset_y,xscale=$op_scalex,yscale=$op_scaley,xscale_o=$scale_center_x,yscale_o=$scale_center_y");
				$f->COM("ncr_order,sr_line=$set_order,sr_nx=1,sr_ny=1,serial=1,optional=no,mode=lrbt,snake=yes,full=1,nx=0,ny=0");
				# === 2023.03.11 转自多层，使用上次排刀序进行输出 ===
				my $rout_table_list = "$logpath/$i"."_table_list";				
				my $now_table_list_path = "$logpath/$i"."_now_table_list";				
				&sort_table_by_last($i,$rout_table_list,$now_table_list_path);				
				$f->PAUSE("please check rout Order");
				
				$f->COM("ncr_table_close");		
				$f->COM("ncr_cre_rout");
				$f->COM("ncr_ncf_export,dir=$current_path,name=$pre_name$JobName.$i");
	
				# 2023.03.10 参考多层 输出指定锣带table 到user 路径唐成
				$f->COM("ncrset_units,units=mm");
				$f->COM("ncr_report,path=$rout_table_list");
				# 检测粗锣精修顺序 http://192.168.2.120:82/zentao/story-view-6803.html
				my $res = system "$pythonVer", "$scriptPath/hdi-scr/Output/output_rout/check_rou_index.py","check_index","$JOB","$i"."_table_list";
				if($res != 0){					
					return;
				}
				
				# 20200106李家兴添加，输出report,用来计算锣程
				$f->COM("ncrset_units,units=mm");
				my $report_file_path = "$current_path/$JobName.$i.report";
				$f->COM("ncr_report,path=$report_file_path");
				$f->COM("ncrset_units,units=inch");
				if ($softuser !~ /89627/) {
					system "//192.168.2.33/incam-share/incam/Path/Python26/python.exe","//192.168.2.33/incam-share/incam/genesis/sys/scripts/sh_script/nc_path/nc_path.py",$i,$report_file_path;
					system("rm -rf $report_file_path");
					#code
				}
				my $strTemp = "";
				open(FILE,"<$current_path/$pre_name$JobName.$i");
				while(<FILE>) {
			
					#先删除指定行（用空替换）
					$_ =~ s/^\/G05\n$//g;
					#再删除空行（用空替换）
					$_ =~ s/^\/G40\n$//g;
					$strTemp = $strTemp.$_;
				 }
				
				open(FILE,">$current_path/$pre_name$JobName.$i");
				print FILE $strTemp;
				close FILE;

                #锣带参数自动匹配
				&add_config_data("$current_path/$pre_name$JobName.$i", %rout_kanife_paramete);
			}
		}
		#$f->COM("set_subsystem,name=1-Up-Edit");	
		unlink("$output_message");
		
		# CCD锣带增加光学点检测及转换 http://192.168.2.120:82/zentao/story-view-6457.html
	if ($i =~ /^ccd|rout-cdc|rout-cds/ ) {
			my $res = system "$pythonVer", "$scriptPath/hdi-scr/Output/output_rout/re_write_ccd.py","$current_path","$pre_name$JobName.$i";	
				if($res != 0){
					$c->Messages('info',"CCD精修锣带参数写入文件失败！！！");					
					unlink "$current_path/$pre_name$JobName.$i";
					return;
				}
		}
		# 盖板作业增加M47指令，涨缩锣带自动对比正式锣带添加M47和ET字样
			# http://192.168.2.120:82/zentao/story-view-6605.html			
		if ($op_step =~ /panel/ && $i eq 'rout'){			
			my $res = system "$pythonVer", "$scriptPath/hdi-scr/Output/output_rout/re_write_M47_et.py","$current_path","$pre_name$JobName.$i","$scale_num","$JobName";	
				if($res != 0){
					$c->Messages('info',"写入M47&&ET指令失败！！！");					
					unlink "$current_path/$pre_name$JobName.$i";
					return;
				}
		}		
		
		# set输出锣带部分参数更新 
		if ($op_step =~ /set|edit/) {
			my $strTemp = "";
				open(FILE,"<$current_path/$pre_name$JobName.$i");
				while(<FILE>) {
					if ($_ !~ /M25\n$|M01\n$|M02\n$|M08\n$/){
						$strTemp = $strTemp.$_;
					}					
				 }
				
				open(FILE,">$current_path/$pre_name$JobName.$i");
				print FILE $strTemp;
				close FILE;
		}
		
		
		# --盲锣板输出自动化 AresHe 2021.10.29
		# --来源需求:http://192.168.2.120:82/zentao/story-view-3343.html
		if ($i =~ /^rout-cd[c|s]$|^ccd-rout-cd[c|s]$}/) {
			
			if (-f "$current_path/$pre_name$JobName.$i") {
				open(DATAFILE, "<$current_path/$pre_name$JobName.$i");
				my @DATALIST = <DATAFILE>;
				close DATAFILE;
				
				# --删除原文件
				unlink "$current_path/$pre_name$JobName.$i";
				
				# --保存文件
				open(WRITEFILE, ">$current_path/$pre_name$JobName.$i");
				
				my $flag;
				my $tool_count = 0;
				my $cp_count = 0;
				my $blind_tool;
				my $blind_first = 1;
				foreach my $des(@DATALIST){
					chomp $des;
					if ($des eq "M48") {
						$flag = "head";
					}elsif($flag eq "head"){
						if ($des =~ /\%/) {
							$flag = "boby";
						}
					}
					
					if ($flag eq "head") {
						if ($des =~ /^T\d+/) {
							if ($des =~ /ZZ$/i && $blind_first == 1) {
								my @tool_head = split(";",$des);								
								$blind_tool = $tool_head[0];
								$blind_first = 0;
							}else{
								if ($des =~ /^T\d+C/) {
									my @tool_head = split("C",$des);
									$tool_count = $tool_count + 1;
									my $tool = $tool_count;
									if ($tool < 10) {
										$tool = "0".$tool;
									}
									print WRITEFILE "T".$tool."C".$tool_head[1]."\n";
								}elsif($des =~ /^T(\d+);C(\d+\.\d+)(.*)/){
									# my @tool_head = split(";",$des);
									# my @tool_head = $1;
									$tool_count = $tool_count + 1;
									my $tool = $tool_count;									
									if ($tool < 10) {
										$tool = "0".$tool;
									}
									my $tool_new = int($2 * 100) / 100;	
									$tool_new = sprintf("%.3f", $tool_new);  #第3位小数变为0
									# print WRITEFILE "T$tool;$tool_head[1]\n";
									print WRITEFILE "T$tool;C$tool_new$3\n";  
								}
							}
						}else{
							if ($des =~ /^CP(\d+)(.*)/) {
								$cp_count = $1 * 1 - 1;
								my $tool = $cp_count;
								if ($tool < 10) {
									$tool = "0".$tool;
								}
								print WRITEFILE "CP".$tool.$2."\n";
							}else{
								print WRITEFILE "$des\n";
							}
						}
					}elsif($flag eq "boby"){
						if ($des eq $blind_tool) {
							print WRITEFILE "M127\n";
							print WRITEFILE "T98\n";
							$blind_first = 1;
						}elsif($des ne "G05"){
							if ($des =~ /^T(\d+)/) {
								$blind_first = 0;
								if ($1 > 1) {
									if ($des =~ /^T(\d+)$/) {
										my $tool = $1 * 1;
										$tool = $tool - 1;
										
										my $new_tool = $tool;
										if ($tool < 10) {
											$new_tool = "0".$tool;
										}
										print WRITEFILE "T$new_tool\n";
									}elsif($des =~ /^T(\d+)(C.*)/){
										my $tool = $1 * 1;
										$tool = $tool - 1;
										
										my $new_tool = $tool;
										if ($tool < 10) {
											$new_tool = "0".$tool;
										}
										print WRITEFILE "T".$new_tool.$2."\n";
									}
								}
							}else{
								print WRITEFILE "$des\n";
							}
						}elsif($des eq "G05" && $blind_first == 0){
							print WRITEFILE "$des\n";
						}
					}
				}
				close WRITEFILE;
			}
		}
		
		############## 输出记录
	    my $dbc_m = $o->CONNECT_MYSQL('host'=>'192.168.2.19', 'dbname'=>'hdi_engineering', 'port'=>'3306', 'user_name'=>'root', 'passwd'=>'k06931!');
		if (! $dbc_m)
		{
			$c->Messages('warning', '"工程数据库"连接失败-> 写入日志程序终止!');
			#exit(0);
			return;
		}

		open(OUT, ">>$logfile");
		if (-s "$logfile")
		{
		print OUT "\n";
		}
	
		print OUT "------------->>> $local_time\t$JOB\t$step_name\t\t$incam_user\t  at\tpc : $ipname\n
		$JOB,$i,$mirror,$offset_x,$offset_y,$scale_center_x,$scale_center_y,$scale_x,$scale_y,$mod_eng,$board_process,now(),$softuser,$ophost,$plat,$Version,$scale_num";
		
		#foreach my $i (@selectlayers)
		#{	
			#printf OUT "%-15s, 镜像:%s,\t偏移:%s,%s,\t涨缩中心(%s,%s),\tx涨缩：%s,\ty涨缩：%s\n ,\t涨缩方式: %s", $i,$mirror,$offset_x,$offset_y,$scale_center_x,$scale_center_y,$scale_x,$scale_y,$op_mode;
			#printf OUT "%-15s, Mirror:%s,\tOffset:%s,%s,\tScale_center:%s,%s,\txScale：%s,\t yScale：%s ,\t Scale_mode: %s\n", $i,$mirror,$offset_x,$offset_y,$scale_center_x,$scale_center_y,$scale_x,$scale_y,$mod_eng;
		my $sql = "insert into rout_output_log
		(job_name,layer,mirror,offset_x,offset_y,scale_center_x,scale_center_y,scale_x,scale_y,scale_mode,scale_num,param,log_time,creator,localhost,app_version)
		values('$JOB','$i','$mirror','$offset_x','$offset_y','$scale_center_x','$scale_center_y','$scale_x','$scale_y','$mod_eng','$scale_num','$board_process',now(),'$softuser','$ophost','$Version')";        
		my $sth = $dbc_m->prepare($sql);#结果保存在$sth中
		$sth->execute() or die "无法执行SQL语句:$dbc_m->errstr";
		#}
		close(OUT);
		$dbc_m->disconnect if ($dbc_m);  
		# if ($op_ccd_rout != 1) {
		# 	# 20200106李家兴添加，用来输出锣程,移至输出后立即执行
		# 	system "//192.168.2.33/incam-share/incam/Path/Python26/python.exe","//192.168.2.33/incam-share/incam/genesis/sys/scripts/sh_script/nc_path/nc_path_hdi.py",$current_path;
		# }
		
		# --不增加换行会导致COM命令失效。增加换行 song add 2022.01.04
		#print "\n";
		if ($scale_num ne "None") {
			my $get_result = system "$pythonVer", "$cur_script_dir/compare_rout.py",$JOB,$i,$scale_num,"$current_path/$pre_name$JobName.$i";
			my $result_num = &get_result_num($get_result);
			# 1——对应无法读取文件 100——非镜像 101——X镜像 102——Y镜像
			print '$result_num' . $result_num. "\n";
			if ($result_num == 1) {
				&message_show('是否退出?')
			}
		}
 	}
        '''


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    # app.setStyle('Cleanlooks')
    jobname = os.environ.get('JOB')
    auto_make_press_rout = AutoMakePressRout()
    auto_make_press_rout.make_press_rout()
