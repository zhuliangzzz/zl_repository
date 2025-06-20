#!/bin/csh
# CAM Guide, net, ipc net compare

COM get_job_path,job=$JOB
set jobPath = `echo "$COMANS"`
set curStep = $STEP
COM check_inout,job=$JOB,mode=in,ent_type=job
DO_INFO -t netlist -e $JOB/net/cadnet -m script -d EXISTS
if ( $gEXISTS == no ) then
	PAUSE NET没有IPC文件。	
else
	
	COM display_net,job=$JOB,step=net,netlist=cad,color=4,section=first,nets=all,disp_mode=net_points,top_tp=yes,bot_tp=yes,drl_tp=yes,npth_tp=yes,inner_tp=yes
	COM netlist_auto_reg,job=$JOB,step=net
	

	#COM netlist_compare,job2=$job,step2=orig,type2=cad,recalc_cur=no,use_cad_names=no,report_extra=yes,report_miss_on_cu=no,report_miss=yes,max_highlight_shapes=50000
	#COM top_tab,tab=1-Up Parameters Page
	COM rv_tab_empty,report=netlist_compare,is_empty=yes

        #2019.12.9 gen_line_hooks_pre_skip改为2
        #此处要强制执行pre hooks
        source /incam/server/site_data/hooks/line_hooks/netlist_compare.pre $JOB

	COM netlist_compare,job2=$JOB,step2=$STEP,type2=cad,recalc_cur=yes,use_cad_names=yes,report_extra=yes,report_miss_on_cu=no,report_miss=yes,max_highlight_shapes=50000

        #2019.12.9 gen_line_hooks_post_skip改为2
        #此处要强制执行post hooks
        source /incam/server/site_data/hooks/line_hooks/netlist_compare.post $JOB

	COM rv_tab_view_results_enabled,report=netlist_compare,is_enabled=yes,serial_num=-1,all_count=-1
	COM get_job_path,job=$JOB

	#COM top_tab,tab=1-Up Parameters Page
	COM rv_tab_empty,report=netlist_compare,is_empty=no
	COM netlist_compare_results_show,action=netlist_compare,is_end_results=yes,is_reference_type=no,job2=$JOB,step2=$STEP
	COM netlist_save_compare_results,output=file,out_file=$INCAM_TMP/netlist.$$
	COM edt_tab_select,report=netlist_compare
	COM top_tab,tab=NetlistCompareResults
	COM show_component,component=Result_Viewer,show=yes,width=703,height=282

	set shorted = `echo "$COMANS[1]"`
	set broken = `echo "$COMANS[3]"`
	if ( $shorted == 0 && $broken == 0 ) then

		PAUSE 网络比对OK！
	else

		PAUSE 与客户IPC网络不一致，请检查网络！
	endif
endif


exit


#COM netlist_compare_results_show,action=netlist_compare,is_end_results=yes,is_reference_type=no,job2=336126,step2=net,mode=0,layers_list1=,layers_list2=

