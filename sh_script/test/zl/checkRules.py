#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = "luthersy"
__date__    = "20190225"
__version__ = "Revision: 1.1.0 "
__credits__ = u"""检测程序 """

import os,sys,string,time,re,math,socket
from scriptsRunRecordLog import uploadinglog
from oracleConnect import oracleConn
from scriptsRunRecordLog import senderData as writeLog

from genesisPackages import job, jobname, \
    stepname, top, matrixInfo, signalLayers, \
    get_layer_polarity, lay_num, get_profile_limits, \
    get_sr_limits, get_parseInplan_info, silkscreenLayers, \
    get_inplan_job

import gClasses

try:
    from getFactory import __factory__
    SITE_ID = __factory__
except Exception, e:
    print e
    SITE_ID = ""

class rule(object):
    def __init__(self, parent = None):
	super(rule,self).__init__()
	self.addnote = False
	
    def get_panelset_sr_step(self, jobname, panelset):
	"""获取panel内或set内的step名"""
	job = gClasses.Job(jobname)
	step = gClasses.Step(job, panelset)
	step.open()
	
	SrInfo = step.getSr()
	Sr_table = SrInfo.table
	stepnames = []
	for tableInfo in Sr_table:
	    stepnames.append(tableInfo.step)
	    
	    if "set" in tableInfo.step:
		
		setstep = gClasses.Step(job, tableInfo.step)
		setstep.open()
		
		set_sr_info = setstep.getSr()
		set_sr_table = set_sr_info.table
		
		for set_sr_table_info in set_sr_table:
		    stepnames.append(set_sr_table_info.step)
		    
	return stepnames		    
    
    def addAttr(self,jobname):#加排除属性eliminate_feature	
	info = self.getSymbolPosition(jobname)
	for data in info:
	    stepname = data[0]
	    dic_symbol_info = eval(data[1])
	    job = gClasses.Job(jobname)
	    step = gClasses.Step(job, stepname)
	    d = job.matrix.getInfo()
	    step.open()	  
	    for key in dic_symbol_info.keys():
		if step.isLayer(key):
		    step.clearAll()
		    step.resetFilter()
		    step.affect(key)
		    for x,y,symbol in dic_symbol_info[key]:
			step.COM("sel_single_feat,operation=select,x=%s,y=%s,tol=2.3427165354,cyclic=no"%(x,y))
			if step.featureSelected():
			    #step.PAUSE("21")
			    STR=r'-t layer -e %s/%s/%s -d FEATURES -o select,units= mm' %(jobname,stepname,key)
			    infoList = step.INFO(STR)			    
			    selectSymbol = self.parseInfoList(step, infoList)[0][2]
			    
			    if symbol !=selectSymbol and symbol !="surface" :
				step.selectSymbol(symbol,1,1)
				if step.featureSelected():
				    step.copySel("selectsymbol")
				    step.clearAll()
				    step.resetFilter()
				    step.affect("selectsymbol")
				    step.COM("sel_single_feat,operation=select,x=%s,y=%s,tol=2.3427165354,cyclic=no"%(x,y))
				    if step.featureSelected():
					step.COM("sel_reverse")
					if step.featureSelected():
					    step.selectDelete()
					step.clearAll()
					step.resetFilter()
					step.affect(key)
					step.refSelectFilter("selectsymbol",mode="cover")
					if step.featureSelected():
					    step.resetAttr()
					    step.COM("cur_atr_set,attribute=.eliminate_feature")
					    step.COM("sel_change_atr,mode=add")	
				    step.removeLayer("selectsymbol")
				    
			    step.resetAttr()
			    step.COM("cur_atr_set,attribute=.eliminate_feature")
			    step.COM("sel_change_atr,mode=add")
			#step.PAUSE("dsf")
		#step.addAttr(".eliminate_feature","")
	    step.COM("editor_page_close")     

	    
    def checkxhsymbol(self,jobname,checkMode,getReturn = "no"):     #检测是否有选化文字symbol
	job = gClasses.Job(jobname)	
	mat=gClasses.Matrix(job)
	d=mat.getInfo()
	sname="panel"
	step = gClasses.Step(job, sname)
	step.open()	
	
	xhlayer = [lay for i,lay in enumerate(d["gROWname"]) if lay in ["gtj","gbj"]]   
	
	
	if (("gtj" in d["gROWname"]) and ("gbj" in d["gROWname"])):
	    sb="dbxh"
	else:
	    sb="sbxh"
	
	for layer in xhlayer:
	    s=r' -t layer -e %s/%s/%s -d SYMS_HIST -m script -p symbol -o break_sr,units= mm' %(jobname,"panel",layer) 
	
	    infoList = step.INFO(s)	
	
	    o=step.parseInfo(infoList)
	
	    symbol=o["gSYMS_HISTsymbol"] 	 
	    
	    if  sb not in symbol:
		STR=u"Step:%s,%s 层中没有 %s Symbol，请检查~"%(sname,layer,sb)
		
		self.senderData(jobname, sname,layer, u"检测", u"检测选化symbol", u"未通过", STR,"")	
		
		return 0
	
	self.senderData(jobname, sname, "", u"检测", u"检测选化symbol", u"检测OK", "", "")	
	
	return 0   	

    def checktklines(self,jobname,checkMode,getReturn = "no"): #检测通孔lines能否被100整除
	
	job = gClasses.Job(jobname)	
	mat=gClasses.Matrix(job)
	d=mat.getInfo()
	
	tongkongDrillLayer = [lay for i,lay in enumerate(d["gROWname"]) if d["gROWcontext"][i] == "board" and d["gROWlayer_type"][i] == "drill" and re.match("^dr01\d\d$",lay)]
	
	for sname in ["set","edit"]:
	
	    step = gClasses.Step(job, sname)
	    step.open()
	    
	    for layer in tongkongDrillLayer:
	    
		STR=r'-t layer -e %s/%s/%s -d FEATURES  ,units= mm' %(jobname,sname,layer)
		
		infoList = step.INFO(STR)
		
		dic_Obj = step.parseFeatureInfo(infoList)
		Pad_symbol = []
		
		for key1 in dic_Obj:
		    for Obj in dic_Obj[key1]:
			if Obj.shape == "Line":
			    Pad_symbol.append(Obj.symbol)
			    								
		objlist1=[o[1:] for o in Pad_symbol]
		
		
		flist=[o for o in objlist1 if float(o)%50==0]    
		
		if len(flist)>0:
		    STR=u"Step:%s,%s 层中有被50整除的线，请检查~"%(sname,layer)
		    
		    self.senderData(jobname, sname,layer, u"检测", u"检测通孔层整除50的线", u"未通过", STR,"")
		    		   		    
		    return STR
		
	    self.senderData(jobname, sname, "", u"检测", u"检测通孔层整除50的线", u"检测OK", "", "")
	    
	return 0
    
    def convert_period(self, key):
	dic_period = {
	    0  : 'WWYY',                          #'周年',        
	    1  : 'YYWW',                          #'年周',        
	    2  : 'YYMMDD',                        #'年月日',      
	    3  : 'BOSCH',                         #'BOSCH周期',   
	    4  : 'SUNTAK',                        #'公司要求',    
	    5  : 'YYMM',                          #'年月',        
	    6  : 'YYWWMM',                        #'年周月',      
	    7  : 'WWYY+NUMBER',                   #'周年+批次号', 
	    8  : 'MMYYWW',                        #'月年周',      
	    9  : 'PDF',                           #'详见PDF档',   
	    10 : 'MMYY',                          #'月年',        
	    11 : 'YYWW+NUMBER',                   #'年周+批次号', 
	    12 : 'YYMMWW',                        #'年月周',      
	    13 : 'YYWWDD',                        #'年周日',      
	    14 : 'NONE',                          #'None',        
	    15 : 'YY.W.WW',                       #'年W周',       
	    16 : 'WW.W.YY',                       #'周W年'
	    17 : 'NOTE' ,                         #'备注'
	    18 : 'CUSTOMER',                      # 客供周期
	    19 : 'YY.WW.W',                       # 年周星期
	    20 : 'DDMMYY',                        # 日月年
	}
	
	return dic_period.get(key)
    
    def convert_period_on_layer(self, key):
	
	dic_layers = {
	    
	    0 : 'signal',                          #蚀刻字
	    1 : 'solder_mask',                     #阻焊字
	    2 : 'silk_screen',                     #字符
	    3 : 'NONE',                            #NONE
	    4 : 'solder_mask+silk_screen',         #阻焊和字符
	    5 : 'signal+solder_mask',              #阻焊和蚀刻
	    6 : 'signal+silk_screen',              #蚀刻和字符
	    7 : 'signal+solder_mask+silk_screen'   #蚀刻,阻焊及字符	    
	    
	}
	
	return dic_layers.get(key)
    
    def get_inplan_full_jobname(self, jobname):
	"""获取inplan全名称"""
	conn = oracleConn('inmind')
    
	if jobname.startswith("100"):
    
	    job_index = jobname[:9]
    
	else:
	    pattern = re.compile("(^\d+)\w\d\d.*")
	    find_indexes = pattern.findall(jobname)
	    if find_indexes:                
		job_index = find_indexes[0]
    
	    else:
		job_index = jobname[:6]
		
	sqlString = """SELECT 
	    JOB_NAME
	    FROM SUNTAK.RPT_JOB_LIST RJL
	    WHERE RJL.JOB_NAME like '%%%s%%' """% job_index
    
	data_info = conn.executeSql(sqlString)
    
	newjobnames = [name[0] for name in data_info
	               if len(name[0]) in [17, 19]]
	
	for inplan_jobname in newjobnames:
	    
	    inplan_job = inplan_jobname.upper().replace("-A", "").replace("-B", "")
	
	    if jobname.upper().strip() == inplan_job:
	
		return inplan_jobname
	    try:
		new_inplan_job = inplan_job[:-5] + \
                    inplan_job[-3] + str(int(inplan_job[-2:]))
	    except:
		# 非正式型号 此处会报错 继续下一个
		continue
	
	    if jobname.upper().strip() in new_inplan_job:
	
		return inplan_jobname
	    
	return None
    
    def get_inplan_period(self, jobname):
	
	inplan_jobname = self.get_inplan_full_jobname(jobname)
	
	if inplan_jobname is not None:
	    conn = oracleConn('inmind')
	    sqlString = """select RJL.NEED_DATE_CODE_SJ_,
	    RJL.NEED_DATE_CODE_,
	    RJL.MARK_ADDITION_MODE2_
	    from SUNTAK.RPT_JOB_LIST RJL
	    WHERE RJL.job_name like '%s'"""%inplan_jobname

	    data_info = conn.executeSql(sqlString)
	    
	    if data_info:
		
		return data_info[0]
	
	return None, None, None
    
    def checkPeriod(self,jobname, checkLayers, ERPPeriod, boardtype, getReturn = "no"):#检测周期
	
	from genesisPackages import genesisFlip
	
	flip = genesisFlip()	
	
	job = gClasses.Job(jobname)
	
	matrixInfo = job.matrix.getInfo()
	    
	count = 0
	
	exists_period_layer = []
	
	for panel in ["panel", "panela", "panelb"]:
	    
	    if panel not in matrixInfo["gCOLstep_name"]:
		continue
	    
	    sr_steps = [name for name in self.get_panelset_sr_step(jobname, panel)]
	    
	    for stepname in set(sr_steps):
		
		info = flip.get_flip_step(stepname, [".flipped_of", ".rotated_of"])
		
		if info is not None:
		    continue

		step = gClasses.Step(job, stepname)
		step.open()		
		
		for layer in checkLayers:
		    
		    if not step.isLayer(layer):continue
		    
		    if step.isLayer("period_layer"):
			step.COM("truncate_layer,layer=period_layer")
		    else:
			step.createLayer("period_layer")
		    
		    step.clearAll()
		    step.resetFilter()
		    step.affect(layer.strip())
		    step.selectSymbol("std-3;std-3n")
		    if step.featureSelected():
			step.copySel("period_layer")
		    
		    step.resetFilter()
		    step.COM("filter_set,filter_name=popup,update_popup=no,feat_types=text")		    
		    step.selectAll()
		    if step.featureSelected():
			step.copySel("period_layer")
			
		    step.clearAll()
		    step.affect("period_layer")
		    step.resetFilter()
		    step.selectSymbol("std-3;std-3n")
		    if step.featureSelected():
			step.COM('sel_break_level,attr_mode=merge')
			
		    step.selectNone()
		    step.resetFilter()
		    step.COM("filter_set,filter_name=popup,update_popup=no,feat_types=text")		    
		    step.selectAll()
		    
		    Text_Obj = []
		    
		    if step.featureSelected():																									
			STR = '-t layer -e %s/%s/%s -d FEATURES -o select,units= mm' %(jobname,stepname, "period_layer")
			infoList = step.INFO(STR)
			dic_Obj = step.parseFeatureInfo(infoList)
			Pad_symbol = []
			Text_symbol = []
			other_symbol = []
		
			for key1 in dic_Obj:
			    
			    for Obj in dic_Obj[key1]:
				
				if Obj.shape in ["Text"]:
				    
				    if Obj.text and ("ww" in Obj.text.lower() or
				                     "yy" in Obj.text.lower() or
				                     "mm" in Obj.text.lower()):#Obj.text in ["wwyy","yyww"]:
					
					layerPeriodText = Obj.text.lower().\
					    replace("'","").\
					    replace("$","").\
					    replace("s", "").\
					    replace("d", "").\
					    replace("c", "")
					
					count += 1
					
					exists_period_layer.append(layer)
					
					if len(layerPeriodText) == 4:
					    
					    if ERPPeriod.lower().strip() not in layerPeriodText.lower():
						
						if getReturn == "yes":
						    
						    return u"%s inplan上 %s 层定义了 %s 周期形式(%s)，\
						    但资料内 %s %s 层内存在周期（%s）与inplan上不一致，\
						    请检查~"%(jobname,exists_period_layer,boardtype, ERPPeriod,
						                 stepname,layer,layerPeriodText)
						
						else:							    
						    STR = u"%s inplan上 %s 层定义了 %s 周期形式(%s)，\
						    但资料内 %s %s 层内存在周期（%s）与inplan上不一致，\
						    请检查~"%(jobname,exists_period_layer,boardtype, ERPPeriod,
						                 stepname,layer,layerPeriodText)
						    
						    self.senderData(jobname, stepname,layer,
						                    u"全板检测", u"检测文字周期", u"未通过", STR,"")	
						    return ""
						
					    #检测bot面 是否镜像 未镜像报警退出
					    if "b" in layer and Obj.mirror == "no":
						if getReturn == "yes":
						    return u"%s面 发现周期 未镜像，请检查~" % layer
						else:								    
						    STR = u"%s面 发现周期 未镜像，请检查~" % layer
						    
						    self.senderData(jobname, stepname,layer,
						                    u"全板检测", u"检测文字周期", u"未通过", STR,"")
						    return ""
						
					    if "t" in layer  and Obj.mirror == "yes":
						if getReturn == "yes":
						    return u"%s面 发现周期 周期被镜像，请检查~" % layer
						else:							
						    STR = u"%s面 发现周期 周期被镜像，请检查~" % layer
						    self.senderData(jobname, stepname,layer,
						                    u"全板检测", u"检测文字周期", u"未通过", STR,"")	
						    return ""							
					else:
					    Text_Obj.append(Obj)
			    
		    if Text_Obj:#检测文字类型周期
			
			tt = self.checkPeriodType(Text_Obj, layer,ERPPeriod)
			
			if tt:
			    if getReturn == "yes":
				return u"%s %s %s 内发现 %s"%(jobname,stepname,layer,tt)
			    else:				    
				STR = u"%s %s %s 内发现 %s"%(jobname,stepname,layer,tt)
				self.senderData(jobname, stepname,layer,
				                u"全板检测", u"检测文字周期", u"未通过", STR,"")	
				return ""
		step.clearAll()
		if step.isLayer("period_layer"):
		    step.removeLayer("period_layer")
		step.COM("editor_page_close")
		
	if ERPPeriod:            
	    if not count:
		if getReturn == "yes":
		    STR = u"%s inplan上定义了 %s 周期形式(%s)，\
		    但资料内edit和set %s 层内未发现 动态属性周期，\
		    请检查~"%(jobname,boardtype, ERPPeriod,checkLayers)
		    return STR
		else:		    
		    STR = u"%s inplan上定义了 %s 周期形式(%s)，\
		    但资料内edit和set %s 层内未发现 动态属性周期，\
		    请检查~"%(jobname,boardtype, ERPPeriod,checkLayers)
		    
		    self.senderData(jobname, "edit","", u"全板检测",
		                    u"检测文字周期", u"未通过", STR,"")
		    return ""
	else:	    
	    if count:
		exists_period_layer = list(set(exists_period_layer))
		if getReturn == "yes":
		    return u"%s inplan上未定义 周期形式，\
		    但资料内 %s层 发现 动态属性周期，\
		    请检查周期是否正确"%(jobname,exists_period_layer)
		else:		    
		    STR = u"%s inplan上未定义 周期形式，\
		    但资料内 %s层 发现 动态属性周期，\
		    请检查周期是否正确"%(jobname,exists_period_layer)
		    self.senderData(jobname, "edit","", u"全板检测",
		                    u"检测文字周期", u"未通过", STR,"")
		    return ""
	    else:
		if boardtype in ["solder_mask", "signal"]:
		    return u"\n未检测到inplan周期数据，资料 %s 层\
		    内未发现动态属性周期，请手动检查：注意是否有周期" % checkLayers
		    

	#self.senderData(jobname, "edit", "", u"全板检测", u"检测文字周期", u"检测OK", "", "")
	return "" #u"周期比对Ok 板内周期[%s] ,erp周期[%s]" % (layerPeriodText, ERPPeriod)

    def checkPeriodType(self,Text_Obj,layer,ERPPeriod):#检测Text周期格式 比如YY或WW
	textInfo = [(Obj.x,
	             Obj.y,
	             Obj.text.lower().\
	             replace("'","").\
	             replace("$","").\
	             replace("s", "").\
	             replace("d", "").\
	             replace("c", ""),
	             Obj.rotation,
	             Obj.mirror,
	             Obj.xsize,
	             Obj.ysize)
	            for Obj in Text_Obj ]
	dic_zu = {}
	exists = []
	j = 0
	
	for i,info in enumerate(textInfo):
	    if info not in exists:
		j +=1
		dic_zu[j] =[]
		dic_zu[j].append(info)
		exists.append(info)
	    else:
		continue
	    for otherInfo in textInfo[i+1:]:
		if info[3] == 0 or info[3] == 180:
		    if info[3] == otherInfo[3] and \
		       abs(info[0] - otherInfo[0])  < 6 and  \
		       abs(info[1] - otherInfo[1]) < info[6] / 2:
			
			dic_zu[j].append(otherInfo)
			exists.append(otherInfo)
		else:
		    if info[3] == otherInfo[3] and \
		       abs(info[1] - otherInfo[1])  < 6 and \
		       abs(info[0] - otherInfo[0]) < info[5] / 2:
			
			dic_zu[j].append(otherInfo)
			exists.append(otherInfo)
			
	for key in dic_zu.keys():
	    if len(dic_zu[key]) != 2:
		return u"周期格式错误，系统无法检测对比周期，请检查~"
	    text1 = dic_zu[key][0]
	    text2 = dic_zu[key][1]
	    angle = text1[3]
	    mirror = text1[4]
	    #检测bot面 是否镜像 未镜像报警退出
	    if 'b' in layer and mirror == "no":
		return u"%s面 发现周期 未镜像，请检查~" % layer

	    if angle == 0:
		if text1[0] < text2[0]:
		    layerPeriodText = "%s%s"%(text1[2],text2[2])
		    if mirror == "yes":
			layerPeriodText = "%s%s"%(text2[2],text1[2])
		else:
		    layerPeriodText = "%s%s"%(text2[2],text1[2])
		    if mirror == "yes":
			layerPeriodText = "%s%s"%(text1[2],text2[2])
	    elif angle == 90:
		if text1[1] > text2[1]:
		    layerPeriodText = "%s%s"%(text1[2],text2[2])
		else:
		    layerPeriodText = "%s%s"%(text2[2],text1[2])    
	    elif angle == 180:
		if text1[0] > text2[0]:
		    layerPeriodText = "%s%s"%(text1[2],text2[2])
		    if mirror == "yes":
			layerPeriodText = "%s%s"%(text2[2],text1[2])
		else:
		    layerPeriodText = "%s%s"%(text2[2],text1[2])
		    if mirror == "yes":
			layerPeriodText = "%s%s"%(text1[2],text2[2])
	    elif angle == 270:
		if text1[1] < text2[1]:
		    layerPeriodText = "%s%s"%(text1[2],text2[2])
		else:
		    layerPeriodText = "%s%s"%(text2[2],text1[2])
	    else:
		return u"有斜度的 周期格式，系统无法检测对比周期，请手动检查~"

	    if layerPeriodText.lower().strip() != ERPPeriod.lower().strip():
		return u" 周期形式(%s)，与erp的周期形式（%s）不一致，\
		请检查~"%(layerPeriodText.lower().strip(),ERPPeriod.lower().strip())
	    
	return ""
    
    def check_period_picihao(self, step, jobname, stepname, worklayer):
	"""检测深圳江门二厂料号内周期批次号是否一致 20190809"""
	#job = gClasses.Job(jobname)
	#step = gClasses.Step(job, stepname)
	step.open()
	
	step.clearAll()	
	step.resetFilter()
	step.COM("filter_set,filter_name=popup,update_popup=no,feat_types=text")
	step.setAttrFilter(".bit,text=auto_date")
	step.flatten_layer(worklayer, worklayer + "_period")
	step.affect(worklayer + "_period")
	step.selectAll()
	layerPeriodText = []	
	if step.featureSelected():
	    STR = '-t layer -e %s/%s/%s -d FEATURES -o select,units= mm' %(jobname,stepname, worklayer + "_period")
	    infoList = step.INFO(STR)
	    dic_Obj = step.parseFeatureInfo(infoList)
	    for key1 in dic_Obj:		
		for Obj in dic_Obj[key1]:		    
		    if Obj.shape in ["Text"]:			    
			layerPeriodText.append(Obj.text.lower())
			
	step.removeLayer(worklayer + "_period")
	
	return layerPeriodText
    
    def check_et_process(self):
	"""输出字符时 检测有ET盖章流程 存在et symbol时 弹出提示
	20210125 by lyh"""
	dic_inplan_info = get_parseInplan_info()
	inplan_job = dic_inplan_info['inplan_job'].replace(
                "'", "").replace('"', "").replace(
                        '-A', "").replace('-B', "")
	exists_process = check_is_exists_process(inplan_job, "ET18")
	if exists_process:
	    if "panel" in matrixInfo["gCOLstep_name"]:		
		step = gClasses.Step(job, "panel")
		step.open()

		for worklayer in silkscreenLayers:
		    step.removeLayer(worklayer + "_tmp")
		    step.flatten_layer(worklayer, worklayer + "_tmp")
		    step.clearAll()
		    step.affect(worklayer + "_tmp")

		    step.resetFilter()
		    step.selectSymbol("et", 1, 1)

		    if step.featureSelected():
			msg = u"检测到此型号有ET盖章流程，字符层[%s]发现et symbol，请检查是否有异常~"
			if sys.platform == "win32":			    
			    os.system("python %s/sys/scripts/suntak/lyh/messageBox.py %s" %
				      (os.environ["GENESIS_DIR"], msg.encode("cp936") % worklayer))
			else:
			    QtGui.QMessageBox.information(
                                QtGui.QWidget(), u'警告', msg, 1)

			step.PAUSE("please check~")
			step.removeLayer(worklayer + "_tmp")
			step.clearAll()
			return

		    step.removeLayer(worklayer + "_tmp")

		step.clearAll()

	job_index = jobname[:6]
	cus_code = get_erp_customer_number(job_index)
	if "00185" in str(cus_code) and exists_process:
	    msg = u"检测到此型号为 00185 客户且有ET盖章流程，185客户不允许添加丝印ET章，请检查字符层是否存在ET盖章~"
	    if sys.platform == "win32":	
		os.system("python %s/sys/scripts/suntak/lyh/messageBox.py %s" %
		          (os.environ["GENESIS_DIR"], msg.encode("cp936")))
	    else:
		QtGui.QMessageBox.information(
                    QtGui.QWidget(), u'警告', msg, 1)		

	    job.PAUSE("please check~")
    
    def check_ope_or_multi_layer(self, jobname, stepname):
	"""大连外层转负片 板外铺铜往板内增加到4mm
	双面板有两张core也处理 20190704 by lyh
	返回值为1 或 0
	0 为不处理 按原来的2mm
	1 改为4mm"""
	job = gClasses.Job(jobname)
	step = gClasses.Step(job, stepname)
	step.open()
	
	if lay_num is not None:
	    if lay_num <= 2:
		#step.clearAll()
		for worklayer in ["gtl", 'gbl']:
		    if step.isLayer(worklayer):
			step.affect(worklayer)
		
		step.resetFilter()
		step.selectSymbol("*ope*", 1, 1)
		if step.featureSelected():
		    #step.clearAll()
		    for worklayer in ["gtl", 'gbl']:
			if step.isLayer(worklayer):
			    step.unaffect(worklayer)		    
		    return 1
		
		for worklayer in ["gtl", 'gbl']:
		    if step.isLayer(worklayer):
			step.unaffect(worklayer)		
	    else:
		return 1
	    
	return 0

    def modify_mask_layer_for_negative_process(self, jobname, stepname):
	"""阻焊菲林板边无开窗，喷涂后板边包油墨，过程转运易撞碎掉渣，
	返沾板面，字符加工时易出现字
	符残缺或字符模糊，对标集团阻焊菲林板边均为开窗设计； 
	b. 负片阻焊板边开窗后会增加沉金包胶比例，为不影响产品加工比例，
	同步对标负片外层菲林进行优
	化。20200327 by lyh"""
	from get_erp_job_info import get_tech_params
	# jobname, stepname = args
	job = gClasses.Job(jobname)
	step = gClasses.Step(job, stepname)
	step.open()
	techface = jobname[10]
	if jobname[12:14] in ["26", "27", "98"] or \
	   techface in ["f"]:  # 电金板
	    return 0
	
	if not step.isLayer("gts") and \
	   not step.isLayer("gbs"):
	    #张世斌通知 帮优化下脚本，没有阻焊工序的板子，负片时板边不留铜 20210327 by lyh 
	    return 1

	dic_zu = get_tech_params(jobname, 84)
	mask_color = dic_zu.get(
		"SOLDER_MASK_COLOR_TOP_") or dic_zu.get("SOLDER_MASK_COLOR_")
	n_polarity = dic_zu.get(u"全板电镀(负片)电流指示编号")
	mask_thk = dic_zu.get("SM_THK_ON_LINE_SURFACE_MAX_")
	surface_thk = dic_zu.get("SURFACE_CU_THK_")
	mask_oil_type = [dic_zu.get("SOLDER_MASK_OIL_TYPE_"),
	                 dic_zu.get("SOLDER_MASK_OIL_TYPE_TOP_"),
	                 dic_zu.get("SOLDER_MASK_OIL_TYPE_BOT_")]
	customer_thickness = dic_zu.get("CUSTOMER_THICKNESS")
	# print [surface_thk, mask_thk, n_polarity, mask_color]
	# step.PAUSE("ddd")
	try:
	    mask_thk = float(mask_thk)
	except:
	    mask_thk = 100000
	try:	    
	    surface_thk = float(surface_thk)
	except:
	    return 0
	
	# if n_polarity is None or mask_color is None:
	# 测试时不判断负片流程 20210625 by lyh
	if mask_color is None:
	    return 0

	mask_color = mask_color.strip()

	if u'哑绿色' not in mask_color and \
	   u"绿色" not in mask_color:
	    "油墨颜色即不是“绿色”也不是“哑绿色”时，板边不铺铜！"
	    return 1
	
	if u"哑绿色" == mask_color:
	    ""
	    return 1
	    #if surface_thk >= 87.5:
		#return 0
	    #else:
		#"哑绿色油墨负片板，当客户要求完成铜厚\
		#（含树脂塞孔加镀及开料加镀）＜2.5oz 时：PNL 板边不设计铜皮"
		#return 1

	# print [surface_thk, mask_thk, n_polarity, mask_color]
	f_xmin, f_ymin, _, _ = get_profile_limits(step)
	sr_xmin, sr_ymin, _, _ = get_sr_limits(step)
	
	if u"绿色" == mask_color:
	    """MI中使用指定阻焊油墨：炎墨SR-500 HG25、太阳PSR-2000 CE826HF、
	    广信KSM-S6189 KG26、广信KSM-S6189 GLF14、炎墨SR-500 HG36，
	    太阳 PSR 4000 G23K板边留铜更改为板边不设计铜皮（电金板除外）20210623 by lyh"""
	    """广信KSM-S6189 KG26、广信KSM-S6189 GLF14、炎墨SR-500 HG36
	    工艺要求仅这三种限制20220811 by lyh"""
	    arraylist = ["SR-500_HG36",
	                 # "PSR4000G_23K",
	                 # "PSR-2000_CE826HF3",
	                 # "SR-500_HG25",
	                 "KSM-S6189-GLF14",
	                 "KSM-S6189-KG26"]
	    for name in arraylist:
		if name in mask_oil_type:
		    return 1
		
	    try:
		"绿色光亮油墨负片板，0.4mm＜板厚＜0.8mm，板边留铜更改为板边不设计铜皮（电金板除外） 20210623 by lyh"
		if 0.4 < float(customer_thickness) < 0.8:
		    return 1
	    except:
		pass
	    # 20220811 工艺要求 取消此条限制
	    #if surface_thk < 87.5 and \
	       #mask_thk <= 35:
		#"绿色油墨负片板，当客户要求完成铜厚（含树脂塞孔加镀及开料加镀）＜2.5oz，\
		#且阻焊 MI“线面最大阻焊厚度” ≤35um 时，负片板边不设计铜皮"
		#return 1
	    #else:
	    if sr_xmin - f_xmin >= 12:
		step_max_dist_x = 10
	    elif 10 <= sr_xmin - f_xmin < 12:
		step_max_dist_x = 8
	    else:
		return 0
	    
	    if sr_ymin - f_ymin >= 12:
		step_max_dist_y = 10
	    elif 10 <= sr_ymin - f_ymin < 12:
		step_max_dist_y = 8
	    else:
		return 0

	    return step_max_dist_x, step_max_dist_y

    def checkRingPad(self,jobname):        
	job = gClasses.Job(jobname)
	d = job.matrix.getInfo()
	step = gClasses.Step(job, "edit")
	dic_layer = self.getout_ciwaiLayers(jobname,d)
	ciwaiLayer = dic_layer["ciwaiLayer"]  
	drillLayers = [lay for i,lay in enumerate(d["gROWname"]) if d["gROWlayer_type"][i] == "drill" and d["gROWcontext"][i] == "board" and re.match("^ld\d\d\d\d$|^md\d\d\d\d$",lay)]
	signalLayer = [lay for i,lay in enumerate(d["gROWname"]) if d["gROWcontext"][i] == "board" and( d["gROWlayer_type"][i] == "signal" or d["gROWlayer_type"][i] == "power_ground") ]
	self.deleteNote(jobname, "edit", signalLayer)
	for layer in ciwaiLayer:
	    for drillLayer in drillLayers:
		if "dr01" in drillLayer:
		    ss = self.checkciwaiPadIsRing(step, jobname, layer,drillLayer)
		    if ss:
			return ss
		else:
		    if layer in ["l%s"%drillLayer[2:4],"l%s"%drillLayer[-2:]]:
			ss = self.checkciwaiPadIsRing(step, jobname, layer,drillLayer)        
			if ss:			
			    return ss
	return 0
    
    def checkciwaiPadIsRing(self,step,jobname,layer,drillLayer):#检测次外层Pad是否有孔环       
	step.clearAll()
	step.resetFilter()	
	step.COM("units,type=inch")
	if step.isLayer("%s_padref"%layer):
	    step.removeLayer("%s_padref"%layer)
	    
	step.affect(layer)
	step.copyToLayer("%s_padref"%layer)
	step.COM("filter_set,filter_name=popup,update_popup=no,feat_types=pad;line;surface,polarity=positive")
	step.selectAll()

	dic_zu_layer = {}
	if step.featureSelected():
	    #if step.isLayer("%s_padref"%layer):
		#step.COM("truncate_layer,layer=%s_padref"%layer)
	    #step.copySel("%s_padref"%layer)
	    step.clearAll()
	    step.affect("%s_padref"%layer)
	    step.COM("sel_contourize,accuracy=1,break_to_islands=yes,clean_hole_size=3,clean_hole_mode=x_and_y")

	    step.clearAll()
	    step.affect(drillLayer)
	    step.resetFilter()
	    step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.drill,option=non_plated")
	    step.selectAll()   

	    if step.featureSelected():
		if step.isLayer("npth"):
		    step.COM("truncate_layer,layer=npth")
		step.copyToLayer("npth",size=2)
	    step.resetFilter()
	    step.selectNone()
	    step.refSelectFilter("%s_padref"%layer,mode="cover")

	    if step.featureSelected():
		if "dr01" in drillLayer:
		    step.refSelectFilter("npth",mode="cover")
		step.COM("sel_reverse")
		if step.featureSelected():
		    STR=r'-t layer -e %s/%s/%s -d FEATURES -o select,units= inch' %(jobname,'edit',drillLayer)
		    infoList = step.INFO(STR)
		    #step.removeLayer("%s_padref"%layer)
		    #self.addNote(step, layer, infoList, "find %s has no pad in %s layer please check"%(drillLayer,layer))
		    #step.display_layer(drillLayer, num=2)
		    dic_zu_layer[layer] = self.parseInfoList(step, infoList)

	    step.removeLayer("%s_padref"%layer)
	step.clearAll()	
	if dic_zu_layer:
	    layers = dic_zu_layer.keys()
	    CoordinateInfo = dic_zu_layer	    
	    STR = u'%s 资料 检测到 %s 为次外层 在钻孔层:%s 对应的位置没有孔环 或孔环不足，系统不予输出资料，请检查~'%(jobname,layer,drillLayer)
	    self.senderData(jobname, "edit"," ".join(layers), u"全板检测", u"检测次外层孔环", u"未通过", STR,CoordinateInfo)
	    	    
	    return STR
	else:
	    self.senderData(jobname, "edit","", u"全板检测", u"检测次外层孔环", u"检测OK", "","")

	return 0
	
    def checkOutline(self,jobname,checkMode):#检测ko是否掏外型线	
	#ss = self.getERPProductType1(jobname)#检测是否半孔板
	#if ss:
	    #return 0
	
	job = gClasses.Job(jobname)
	#step = gClasses.Step(job, "edit")
	d = job.matrix.getInfo()
	for name in d["gCOLstep_name"]:
	    if "edit" in name and "flip" not in name:
		stepname = name
	step = gClasses.Step(job, stepname)
	step.open()
	step.COM("units,type=inch")
	step.clearAll()
	if not step.isLayer("patternfill"):
	    step.createLayer("patternfill")
	else:
	    step.COM("truncate_layer,layer=patternfill")
	step.affect("patternfill")
	step.COM("sr_fill,polarity=positive,step_margin_x=0,step_margin_y=0,step_max_dist_x=100,step_max_dist_y=100,sr_margin_x=0,sr_margin_y=0,sr_max_dist_x=100,sr_max_dist_y=100,nest_sr=yes,stop_at_steps=,consider_feat=no,consider_drill=no,consider_rout=no,dest=affected_layers,attributes=no")
	
	if not step.isLayer("patternfill-outline"):
	    step.createLayer("patternfill-outline")
	    step.copySel("patternfill-outline")
	else:
	    step.COM("truncate_layer,layer=patternfill-outline")
	    step.copySel("patternfill-outline")
	    
	step.unaffect("patternfill")
	step.affect("patternfill-outline")
	step.COM("sel_surf2outline,width=15.8")
	#step.COM("sel_change_sym,symbol=r0.1,reset_angle=no")
	if checkMode == "all":
	    outputType = u"全板检测"
	    signalLayer = [lay for i,lay in enumerate(d["gROWname"]) if d["gROWcontext"][i] == "board" and( d["gROWlayer_type"][i] == "signal" or d["gROWlayer_type"][i] == "power_ground")]
	else:
	    outputType = u"内层检测"
	    signalLayer = [lay for i,lay in enumerate(d["gROWname"]) if d["gROWcontext"][i] == "board" and( d["gROWlayer_type"][i] == "signal" or d["gROWlayer_type"][i] == "power_ground") and d["gROWside"][i] == "inner" ]
	self.deleteNote(jobname, "edit", signalLayer)
	dic_zu_layer = {}
	for layer in signalLayer:
	    if step.isLayer(layer):
		step.clearAll()
		step.COM("units,type=inch")
		step.affect(layer)
		if step.isLayer("%s_ref"%layer):
		    step.removeLayer("%s_ref"%layer)
		step.copySel("%s_ref"%layer)
		step.unaffect(layer)
		step.affect("%s_ref"%layer)
		step.resetFilter()
		step.setAttrFilter(".eliminate_feature")
		step.COM("filter_area_end,layer=,filter_name=popup,operation=select,area_type=none,inside_area=no,intersect_area=no")
		count = step.featureSelected()
		if count:
		    step.selectDelete()
		step.resetFilter()
		step.COM("filter_set,filter_name=popup,update_popup=no,feat_types=surface,polarity=positive")
		step.selectAll()
		if step.featureSelected():
		    step.COM("sel_surf2outline,width=10")
		step.resetFilter()
		step.refSelectFilter("patternfill-outline",mode="touch")	
		if step.featureSelected():
		    step.COM("sel_reverse")
		    step.selectDelete()
		step.COM("sel_contourize,accuracy=1,break_to_islands=yes,clean_hole_size=3,clean_hole_mode=x_and_y")
		#step.refSelectFilter("patternfill",mode="disjoint")
		#if step.featureSelected():
		    #step.copySel("selectfeature")		    
		step.resetFilter()
		step.COM("filter_set,filter_name=popup,update_popup=no,polarity=positive")
		step.refSelectFilter("patternfill-outline",mode="touch")
		count = step.featureSelected()
		if count:
		    STR=r'-t layer -e %s/%s/%s -d FEATURES -o select,units= inch' %(jobname,'edit',"%s_ref"%layer)
		    infoList = step.INFO(STR)
		    #step.removeLayer("%s_ref"%layer)
		    #self.addNote(step, layer, infoList, "find features touch outline please check!",showSymbol= "no")
		    #return u'%s 资料 %s层 检测到外形线跟板内元素接触，请检查是否漏掏铜，若此料号客户接受成型露铜，请把此元素添加（.eliminate_feature）排除属性，请检查~'%(jobname,layer)
		    dic_zu_layer[layer] = self.parseInfoList(step, infoList)
		step.removeLayer("%s_ref"%layer)
	step.COM("note_page_close")
	
	if dic_zu_layer:
	    layers = dic_zu_layer.keys()
	    CoordinateInfo = dic_zu_layer
	    STR = u'%s 资料 %s层 检测到外形线跟板内元素接触，请检查是否漏掏铜，若此料号客户接受成型露铜，请把此元素添加（.eliminate_feature）排除属性，请检查~'%(jobname," ".join(layers))
	    self.senderData(jobname, stepname, " ".join(layers), outputType, u"检测ko是否掏外型线", 
                           u"未通过", STR, CoordinateInfo)
	else:
	    self.senderData(jobname, stepname, "", outputType, u"检测ko是否掏外型线", 
                           u"检测OK", "", "")
	step.clearAll()	
	return 0 
    
    def render(self,args):#接收数据
	
	self.addnote = args
    
    def senderData(self,jobname,stepname,layers,outputType,checkProject,checkStatus,instruction,CoordinateInfo):	
	localip = socket.gethostbyname_ex(socket.gethostname())   
	top = gClasses.Top()
	user = top.getUser()
	
	SITE_ID = ""
	JOB_NAME = jobname
	STEP_NAME = "edit"
	RUN_TYPE = checkProject
	RUN_RECORD = instruction
	GEN_USER = user
	COMPUTER_IP = localip[2][0]
	SCRIPT_NAME = os.path.basename(sys.argv[0])
	    
	writeLog(SITE_ID, JOB_NAME, STEP_NAME, RUN_TYPE, RUN_RECORD, GEN_USER, 
	         COMPUTER_IP, SCRIPT_NAME)	    

    def checkFeaturesInOutside(self, jobname, stepname, check_type="all"):  # 检测板外物件
        job = gClasses.Job(jobname)
	top = gClasses.Top()
	matrixinfo = job.matrix.getInfo()
	boardlayers = [lay for i, lay in enumerate(matrixinfo["gROWname"])
	               if matrixinfo["gROWcontext"][i] == "board"
	               and matrixinfo["gROWlayer_type"][i] != "rout"]
	solderMaskLayers = [lay for i, lay in enumerate(matrixinfo["gROWname"])

		            if matrixinfo["gROWcontext"][i] == "board"

		            and matrixinfo["gROWlayer_type"][i] == "solder_mask"]
	
	silkscreenLayers = [lay for i, lay in enumerate(matrixinfo["gROWname"])

		            if matrixinfo["gROWcontext"][i] == "board"

		            and matrixinfo["gROWlayer_type"][i] == "silk_screen"]
	
	innersignalLayers = [lay for i, lay in enumerate(matrixInfo["gROWname"])
    
	                     if matrixInfo["gROWcontext"][i] == "board"
    
	                     and (matrixInfo["gROWlayer_type"][i] == "signal"
    
	                          or matrixInfo["gROWlayer_type"][i] == "power_ground")
    
	                     and matrixInfo["gROWside"][i] == "inner"]
    
	outsignalLayers = [lay for i, lay in enumerate(matrixInfo["gROWname"])
    
	                   if matrixInfo["gROWcontext"][i] == "board"
    
	                   and matrixInfo["gROWlayer_type"][i] == "signal"
    
	                   and matrixInfo["gROWside"][i] != "inner"]
	other_layers = [lay for i, lay in enumerate(matrixinfo["gROWname"])

	                if matrixinfo["gROWcontext"][i] == "board"

	                and matrixinfo["gROWlayer_type"][i] == "solder_paste"]

	
	drill_layers = [lay for i, lay in enumerate(matrixinfo["gROWname"])
	                if matrixinfo["gROWcontext"][i] == "board"
	                and matrixinfo["gROWlayer_type"][i] == "drill"]

	if check_type == "all":
	    check_layers = boardlayers + solderMaskLayers + silkscreenLayers + other_layers
	else:
	    check_layers = innersignalLayers + drill_layers	
	
	dic_zu_layer = {}
	
	step = gClasses.Step(job, stepname)
	step.open()
	self.deleteNote(jobname, stepname, check_layers)
	step.clearAll()
	step.resetFilter()
	step.COM("units,type=mm")
	if not step.isLayer("patternfill"):
	    step.createLayer("patternfill")
	else:
	    step.COM("truncate_layer,layer=patternfill")

	if "set" in stepname:
	    """检测set板外物 是否进入另一个单元"""
	    step.removeLayer("set_fill_outside_1.8")
	    step.createLayer("set_fill_outside_1.8")
	    step.affect("set_fill_outside_1.8")
	    step.reset_fill_params()
	    #由1.8 改为1.5 20230412 by lyh
	    step.COM("sr_fill,polarity=positive,step_margin_x=-1.5,step_margin_y=-1.5,"
		     "step_max_dist_x=2540,step_max_dist_y=2540,sr_margin_x=0,"
		     "sr_margin_y=0,sr_max_dist_x=2540,sr_max_dist_y=2540,nest_sr=yes,"
		     "stop_at_steps=,consider_feat=no,consider_drill=no,"
		     "consider_rout=no,dest=affected_layers,attributes=no")
	    step.COM("sel_surf2outline,width=2.54")
	    step.COM("filter_set,filter_name=popup,update_popup=no,profile=out")
	    step.selectAll()
	    step.COM("sel_reverse")
	    if step.featureSelected():
		step.selectDelete()

	step.clearAll()
	step.affect("patternfill")
	step.reset_fill_params()
	step.COM("sr_fill,polarity=positive,step_margin_x=-0.254,step_margin_y=-0.254,"
	         "step_max_dist_x=2540,step_max_dist_y=2540,sr_margin_x=-0.254,"
	         "sr_margin_y=-0.254,sr_max_dist_x=2540,sr_max_dist_y=2540,nest_sr=yes,"
	         "stop_at_steps=,consider_feat=no,consider_drill=no,"
	         "consider_rout=no,dest=affected_layers,attributes=no")
	
	#ss = self.getERPProductType1(jobname)#检测是否半孔板
	#if ss:
	    # step.COM("sel_resize,size=30,corner_ctl=no")
	    
	# icg 测试条外物检测 会有异常 单边加大0.5mm 20220329
	if "icg" in stepname:
	    step.COM("sel_resize,size=500,corner_ctl=no")
	    
	if not step.isLayer("patternfill-outline"):
	    step.createLayer("patternfill-outline")
	    step.copySel("patternfill-outline")
	else:
	    step.COM("truncate_layer,layer=patternfill-outline")
	    step.copySel("patternfill-outline")
	    
	step.unaffect("patternfill")
	step.affect("patternfill-outline")
	step.COM("sel_surf2outline,width=508")
	step.COM("sel_change_sym,symbol=r2.54,reset_angle=no")
	# step.PAUSE("dsdf")

	for layer in check_layers:
	    if not step.isLayer(layer):continue
	    step.clearAll()
	    step.COM("units,type=mm")
	    step.affect(layer)		    
	    step.resetFilter()
	    
	    step.setAttrFilter(".string,text=set_outside_feature")
	    step.selectAll()
	    if step.featureSelected():
		step.COM("sel_delete_atr,attributes=.string")
	    step.selectNone()
	    step.resetFilter()
	    
	    if step.isLayer("set_fill_outside_1.8"):
		step.flatten_layer(layer, layer+"_set_outside")
		step.resetFilter()
		step.affect(layer+"_set_outside")
		step.refSelectFilter("set_fill_outside_1.8")
		if step.featureSelected():		    
		    step.addAttr(".string", "set_outside_feature", "text")
		    step.COM("sel_change_atr,mode=add")
		    step.refSelectFilter("set_fill_outside_1.8")
		    if step.featureSelected():			
			step.copySel("selectfeature")		    
		else:
		    step.removeLayer(layer+"_set_outside")
	    
	    step.clearAll()
	    step.affect(layer)		    
	    step.resetFilter()	    
	    step.VOF()
	    step.COM("filter_set,filter_name=popup,update_popup=no,profile=out")
	    step.selectAll()
	    if step.STATUS > 0:
		continue	    
	    step.VON()

	    # step.PAUSE("dddd")
	    step.selectAll()
	    count = step.featureSelected()
	    if not count and not step.isLayer("selectfeature"):
		if "set" in stepname:
		    step.VOF()
		    step.COM("filter_set,filter_name=popup,update_popup=no,profile=in")
		    step.selectAll()
		    if step.STATUS > 0:
			continue	    
		    step.VON()
		    step.selectAll()
		    step.COM("sel_reverse")
		    count = step.featureSelected()
		    
		if not count:
		    step.resetFilter()
		    step.refSelectFilter("patternfill-outline",mode="touch")
		    if not step.featureSelected():
			continue
	    
	    step.copySel("%s_ref"%layer)
	    step.refSelectFilter("patternfill",mode="disjoint")
	    if step.featureSelected():
		step.copySel("selectfeature")
	    step.unaffect(layer)
	    step.affect("%s_ref" % layer)
	    step.refSelectFilter("patternfill-outline", mode="touch")
	    if step.featureSelected():
		step.copySel("selectfeature")

	    # step.PAUSE("sdf")
	    if step.isLayer("selectfeature"):
		step.clearAll()
		step.affect("patternfill")
		# 负片层因图形要做出板外 严文刚通知 板外0.8mm的区域 不检查 20220316 by lyh
		if layer.endswith("n") and (layer.startswith("l") or layer.startswith("gp")):
		    step.COM("sel_resize,size=1590,corner_ctl=no")
		else:
		    # 严文刚通知 整体加大900 因外形掏负性很多都是单边400 20220318
		    step.COM("sel_resize,size=900,corner_ctl=no")
		    
		step.unaffect("patternfill")
		step.affect("selectfeature")
		step.resetFilter()
		if layer.endswith("n") and (layer.startswith("l") or layer.startswith("gp")):
		    pass
		else:
		    # 去掉负性外形线
		    step.COM("filter_set,filter_name=popup,update_popup=no,polarity=negative")
		    
		step.refSelectFilter("patternfill", mode="cover")
		if step.featureSelected():
		    step.selectDelete()
		step.clearAll()
		step.affect("patternfill")
		if layer.endswith("n") and (layer.startswith("l") or layer.startswith("gp")):
		    step.COM("sel_resize,size=-1590,corner_ctl=no")
		else:
		    step.COM("sel_resize,size=-900,corner_ctl=no")
		step.clearAll()
		step.affect("selectfeature")
		step.resetFilter()

		# surface 不好取坐标 把surface挑出来 转成外形线 再打标记 20201112 by lyh
		step.selectNone()
		step.filter_set(feat_types='surface')
		step.selectAll()
		infoList1 = []
		if step.featureSelected():
		    step.removeLayer(layer + "_surface")
		    step.moveSel(layer + "_surface")
		    step.clearAll()
		    step.affect(layer + "_surface")
		    # step.COM("sel_resize,size=-500") 屏蔽此处 防止surface被减没了 导致漏标记 20210621 by lyh
		    step.COM("sel_surf2outline,width=1")
		    
		    # surface存在板内的坐标要去掉 否则很多误报 20220312 by lyh
		    step.resetFilter()
		    step.refSelectFilter("patternfill", mode="cover")
		    if step.featureSelected():
			step.selectDelete()
    
		    #step.resetFilter()
		    #step.refSelectFilter("patternfill-outline", mode="disjoint")
		    #if step.featureSelected():
			#step.selectDelete()
		    # step.PAUSE("dd")
		    step.resetFilter()
		    step.selectAll()
		    if step.featureSelected():
			STR = r'-t layer -e %s/%s/%s -d FEATURES,units= mm' % (
			    jobname, stepname, layer + "_surface")
			infoList1 = step.INFO(STR)
		    step.removeLayer(layer + "_surface")		

		step.clearAll()
		step.affect("selectfeature")

		# 为防止误报 这里再把板内的坐标清除掉
		step.resetFilter()
		step.refSelectFilter("patternfill", mode="cover")
		if step.featureSelected():
		    step.selectDelete()
		    
		step.resetFilter()
		step.selectAll()
		count = step.featureSelected()
		if count or infoList1:
		    STR = r'-t layer -e %s/%s/%s -d FEATURES -o select,units= mm' % (
                        jobname, stepname, "selectfeature")
		    infoList = step.INFO(STR)			
		    dic_zu_layer[layer] = self.parseInfoList(step, infoList + infoList1)
		    
		    if step.isLayer("set_fill_outside_1.8"):
			"""检测板外物会进去拼版单元其他单元内 20200514"""
			step.clearAll()
			step.resetFilter()
			step.affect(layer)
			step.refSelectFilter("set_fill_outside_1.8")
			if step.featureSelected():
			    # step.PAUSE("ddd")
			    step.addAttr(".string", "set_outside_feature", "text")
			    step.COM("sel_change_atr,mode=add")

	    step.VOF()
	    step.removeLayer("selectfeature")
	    step.removeLayer("%s_ref"%layer)
	    step.VON()
	    step.clearAll()
	    
	step.COM("editor_page_close")
	step.clearAll()
	step.removeLayer("set_fill_outside_1.8")
	
	return dic_zu_layer
    
    def checkFeaturesInOutsideForpanelset(self, jobname, stepname, check_type="all"):
	job = gClasses.Job(jobname)
	editsteps = [name for name in self.get_panelset_sr_step(jobname, stepname)
	             if name not in ["wk"]]
	
	setsteps = []	
	if "panel" in stepname:
	    
	    setsteps = [name for name in self.get_panelset_sr_step(jobname, stepname)
	                if name not in ["wk"]]
	
	for editname in set(editsteps + setsteps):
	    
	    editstep = gClasses.Step(job, editname)
	    matrixinfo = job.matrix.getInfo()	
	    editstep.open()
	    editstep.COM("units,type=mm")
	    editstep.clearAll()
	    if not editstep.isLayer("patternfill"):
		editstep.createLayer("patternfill")
	    else:
		editstep.COM("truncate_layer,layer=patternfill")
		
	    editstep.affect("patternfill")
	    editstep.reset_fill_params()
	    editstep.COM("sr_fill,polarity=positive,step_margin_x=0,step_margin_y=0,"
	    "step_max_dist_x=2540,step_max_dist_y=2540,sr_margin_x=0,sr_margin_y=0,"
	    "sr_max_dist_x=2540,sr_max_dist_y=2540,nest_sr=yes,stop_at_steps=,"
	    "consider_feat=no,consider_drill=no,consider_rout=no,"
	    "dest=affected_layers,attributes=no")	       

	    #if "panel" in stepname:
		#editstep.COM("sel_resize,size=-254,corner_ctl=no")
	    #else:
		#pass
		#if SITE_ID in [u"江门二厂", u"深圳沙井"]:
		    ##20190520 严文刚 要求距板边2mm 即可
		    #editstep.COM("sel_resize,size=-4000,corner_ctl=no")
		    # editstep.clearAll()

	step = gClasses.Step(job, stepname)
	step.open()
	
	if not step.isLayer("patternfill"):
	    return {}
	
	step.COM("flatten_layer,source_layer=%s,target_layer=%s_flatten" %
	         ("patternfill", "patternfill"))
	
	matrixinfo = job.matrix.getInfo()

	checklayers = [lay for i, lay in enumerate(matrixinfo["gROWname"])
	               if matrixinfo["gROWcontext"][i] == "board"
	               and matrixinfo["gROWlayer_type"][i] != "rout"]

	innersignalLayers = [lay for i, lay in enumerate(matrixInfo["gROWname"])
    
	                     if matrixInfo["gROWcontext"][i] == "board"
    
	                     and (matrixInfo["gROWlayer_type"][i] == "signal"
    
	                          or matrixInfo["gROWlayer_type"][i] == "power_ground")
    
	                     and matrixInfo["gROWside"][i] == "inner"]
	
	drill_layers = [lay for i, lay in enumerate(matrixinfo["gROWname"])
	                if matrixinfo["gROWcontext"][i] == "board"
	                and matrixinfo["gROWlayer_type"][i] == "drill"]
	
	
	inplan_job = get_inplan_job()
	face_tech = inplan_job[12:14]
	
	if check_type == "all":
	    check_layers = checklayers
	else:
	    check_layers = innersignalLayers + drill_layers	
	
	dic_zu_layer = {}
	self.deleteNote(jobname, stepname, check_layers)
	step.clearAll()
	step.resetFilter()
	step.COM("units,type=mm")	
	step.COM("flatten_layer,source_layer=patternfill,target_layer=patternfill_flatten")	

	for layer in check_layers:
	    if not step.isLayer(layer):continue
	    step.clearAll()
	    step.affect(layer)
	    
	    step.resetFilter()
	    step.filter_set(feat_types='pad;line;arc;text')
	    step.refSelectFilter("patternfill_flatten", mode="touch")
	    #step.setAttrFilter(".eliminate_feature")
	    # step.COM("filter_area_end,layer=,filter_name=popup,operation=unselect,area_type=none,inside_area=no,intersect_area=no")
	    if layer == "drl" and stepname == "set" and face_tech in ["98", "26", "27"]:
		"""通孔层再检测是否 有掏断edit板外引线 例如：一厂100310266c0698a01 20191119 by lyh"""
		for checksiglayer in signalLayers:
		    if step.isLayer(checksiglayer):
			if checksiglayer.endswith("n"):
			    pol = "negative"
			else:
			    pol = "positive"
			    
			step.flatten_layer(checksiglayer, checksiglayer + "_tmp_check")
			# step.refSelectFilter(checksiglayer + "_tmp_check", mode="touch")
			step.COM("sel_ref_feat,layers=%s_tmp_check,use=filter,mode=touch,"
			"pads_as=shape,f_types=line\;pad\;arc,polarity=%s,"
			"include_syms=,exclude_syms=" % (checksiglayer, pol))
			step.removeLayer(checksiglayer + "_tmp_check")
			
	    infoList = []
	    if step.featureSelected():
		#if stepname == "panel":
		    #step.PAUSE("check")
		STR=r'-t layer -e %s/%s/%s -d FEATURES -o select,units= mm' %(jobname,stepname,layer)
		infoList = step.INFO(STR)		    
			
	    # surface 不好取坐标 把surface挑出来 转成外形线 再打标记 20201112 by lyh
	    if infoList:
		infoList1 = []
		step.resetFilter()
		step.selectNone()
		step.filter_set(feat_types='surface')
		step.refSelectFilter("patternfill_flatten", mode="touch")
		if step.featureSelected():
		    # step.PAUSE("ddd")
		    step.removeLayer(layer + "_surface")
		    step.copySel(layer + "_surface")
		    step.clearAll()
		    step.affect(layer + "_surface")
		    step.COM("sel_resize,size=-500")
		    step.COM("sel_surf2outline,width=1")
    
		    step.resetFilter()
		    step.refSelectFilter("patternfill_flatten", mode="disjoint")
		    if step.featureSelected():
			step.selectDelete()
    
		    step.resetFilter()
		    step.selectAll()
		    if step.featureSelected():
			#if stepname == "panel":
			    #step.PAUSE("check")		    
			STR = r'-t layer -e %s/%s/%s -d FEATURES,units= mm' % (
			    jobname, stepname, layer + "_surface")
			infoList1 = step.INFO(STR)
			
		    step.removeLayer(layer + "_surface")		
    
		if infoList + infoList1:
		    dic_zu_layer[layer] = self.parseInfoList(step, infoList + infoList1)
		
	step.removeLayer("patternfill_flatten")
	step.removeLayer("patternfill")	
	step.clearAll()	    
	return dic_zu_layer
    
    def checkOrign(self,jobname):#检测原点位置
        job = gClasses.Job(jobname)
	d = job.matrix.getInfo()	
	for stepname in ["edit","set","panel"]:
	    if stepname in d["gCOLstep_name"]:	    
		step = gClasses.Step(job, stepname)  
		step.open()
		step.COM("units,type=inch")
		step.COM("get_origin")
		orignx,origny = step.COMANS.split()
		orignx = "%.2f"%float(orignx)
		origny = "%.2f"%float(origny)
		datumx = "%.2f"%step.getDatum()["x"]
		datumy = "%.2f"%step.getDatum()["y"]
		if orignx == datumx and origny == datumy:
		    pass
		else:
		    STR = u"%s 料号 %s 中原点(%s,%s)与基准点(%s,%s) 不在同一位置，请调整~"%(jobname,stepname,orignx,origny,datumx,datumy)	
		    self.senderData(jobname, stepname, "", u"全板检测", u"检测原点位置", u"未通过", STR, "")		
	return 0       
    
    def checkRoutInsidePCS(self,jobname):#检测锣刀是否锣到板内 界定为板内2mil
	job = gClasses.Job(jobname)
	step = gClasses.Step(job, "edit")
	d = job.matrix.getInfo()	
	step.open()
	step.COM("units,type=mm")
	step.clearAll()
	if not step.isLayer("patternfill"):
	    step.createLayer("patternfill")
	else:
	    step.removeLayer("patternfill")
	    step.createLayer("patternfill")
	if step.isLayer("out"):
	    step.copyLayer(jobname, "edit", "out", "patternfill")
	    step.affect("patternfill")
	    step.COM("sel_cut_data,det_tol=1,con_tol=1,rad_tol=0.1,filter_overlaps=no,delete_doubles=no,use_order=yes,ignore_width=yes,ignore_holes=none,start_positive=yes,polarity_of_touching=same")
	else:
	    step.affect("patternfill")
	    step.COM("sr_fill,polarity=positive,step_margin_x=0,step_margin_y=0,step_max_dist_x=100,step_max_dist_y=100,sr_margin_x=0,sr_margin_y=0,sr_max_dist_x=100,sr_max_dist_y=100,nest_sr=yes,stop_at_steps=,consider_feat=no,consider_drill=no,consider_rout=no,dest=affected_layers,attributes=no")
	
	step.COM("sel_resize,size=-4.2,corner_ctl=no")# 4mil
	
	step = gClasses.Step(job, "panel")
	step.open()
	step.COM("flatten_layer,source_layer=%s,target_layer=%s_flatten"%("patternfill","patternfill"))
	step.clearAll()
	step.COM('units,type=mm')
	step.resetFilter()
	dic_zu_layer = {}
	for layer in ["rou","pthrou"]:
	    if step.isLayer(layer):
		step.affect(layer)
		#step.COM("flatten_layer,source_layer=%s,target_layer=%s_flatten"%(layer,layer))
		step.COM("compensate_layer,source_layer=%s,dest_layer=%s_flatten,dest_layer_type=document"%(layer,layer))
		step.unaffect(layer)
		step.affect("%s_flatten"%layer)
		#step.COM("chain_cancel,layer=%s_flatten,renumber_sequentially=no"%layer)
		#step.COM("sel_change_sym,symbol=r4,reset_angle=no")
		step.refSelectFilter("patternfill_flatten",mode="touch")
		if step.featureSelected():
		    STR=r'-t layer -e %s/%s/%s -d FEATURES -o select,units= mm' %(jobname,"panel","%s_flatten"%layer)
		    infoList = step.INFO(STR)
		    dic_zu_layer[layer] = self.parseInfoList(step, infoList)
		    #self.addNote(step, layer, infoList, "%s find features touch out please check!"%layer)
		    step.removeLayer("%s_flatten"%layer)
		    #step.removeLayer("patternfill_flatten")
		    #step.removeLayer("patternfill")
		    #return u'%s 资料 %s %s层 检测到锣刀 有锣进板内超过 2mil，请检查~'%(jobname,"panel",layer)
	step.removeLayer("patternfill_flatten")
	step.removeLayer("patternfill")
	#step.PAUSE(str(dic_zu_layer))
	if dic_zu_layer:
	    layers = dic_zu_layer.keys()
	    CoordinateInfo = dic_zu_layer
	    STR = u'%s 资料 %s %s层 检测到锣刀 有锣进板内超过 2mil，请检查~'%(jobname,"panel"," ".join(layers))
	    self.senderData(jobname, "panel", " ".join(layers), u"全板检测", u"检测锣刀是否锣到板内", 
	                   u"未通过", STR, CoordinateInfo)
	else:
	    self.senderData(jobname, "panel", "", u"全板检测", u"检测锣刀是否锣到板内", 
	                   u"检测OK", "", "")	
	return 0    
    def checkNpthHoleInsetStep(self,jobname,stepname="set"):#检测set中的Npth孔是否接触到板内物件
        job = gClasses.Job(jobname)
	d = job.matrix.getInfo()
	if stepname not in d["gCOLstep_name"]:#没有set 不检测
	    return 0	
        step = gClasses.Step(job, stepname)        
        layer_number = jobname[:2] 
        if re.match("^[a-z].*", jobname):
            layer_number = jobname[1:3]
        bottomoutLayer = "l%s"%layer_number        
        step.open()
        step.COM("units,type=mm")
        step.clearAll()
        step.resetFilter()
        tongkongLayer = "dr01%s"%layer_number
        if not step.isLayer(tongkongLayer):
            return u"%s通孔层不存在，请检查~"%tongkongLayer
        signalLayer = [lay for i,lay in enumerate(d["gROWname"]) if d["gROWcontext"][i] == "board" and( d["gROWlayer_type"][i] == "signal" or d["gROWlayer_type"][i] == "power_ground") ]
        self.deleteNote(jobname, stepname, signalLayer)
        #step.affect(tongkongLayer)
	dic_zu_layer = {}
        for layer in ["l01",bottomoutLayer]:
            flatten_layer = "%s_flatten"%layer
            step.COM("flatten_layer,source_layer=%s,target_layer=%s"%(layer,flatten_layer))
            step.affect(flatten_layer)
            step.COM("sel_contourize,accuracy=25.4,break_to_islands=yes,clean_hole_size=76.2,clean_hole_mode=x_and_y")
            step.unaffect(flatten_layer)
            step.affect(tongkongLayer)
            step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.drill,option=non_plated")
            step.COM("filter_set,filter_name=popup,update_popup=no,polarity=positive,feat_types=pad")
            step.refSelectFilter(flatten_layer,mode="touch")            
            if step.featureSelected():
                STR=r'-t layer -e %s/%s/%s -d FEATURES -o select,units= mm' %(jobname,stepname,tongkongLayer)
                infoList = step.INFO(STR)
		
		dic_zu_layer[layer] = self.parseInfoList(step, infoList)
		
                #self.addNote(step, layer, infoList, "find %s has npth hole touch copper please check"%tongkongLayer)
                step.display_layer(tongkongLayer, num=2)
                step.removeLayer(flatten_layer)
                #return u'%s 资料 检测到 %s 通孔层中 有NPTH 孔接触到板边物件，系统不予输出资料，请检查~'%(jobname,stepname)
            step.removeLayer(flatten_layer)
            step.clearAll()
            step.COM("editor_page_close")
	    
	    if dic_zu_layer:
		layers = dic_zu_layer.keys()
		CoordinateInfo = dic_zu_layer
                STR = u'%s 资料 检测到 %s 通孔层中 有NPTH 孔接触到板边物件，系统不予输出资料，请检查~'%(jobname,stepname)
		self.senderData(jobname, "set", " ".join(layers), u"全板检测", u"检测set中的Npth孔是否接触到板内物件", 
		               u"未通过", STR, CoordinateInfo)	
	    else:
		self.senderData(jobname, "set", "", u"全板检测", u"检测set中的Npth孔是否接触到板内物件", 
	                       u"检测OK", "", "")
        return 0
    
    def addNote(self,step,layer,infoList,noteText,showNote="yes",user="",showSymbol = "yes"): 
        #step.COM("note_delete_all,layer=%s,note_from=0,note_to=2147483647,user="%layer)
	step.COM("get_origin")
	orignx, origny = step.COMANS.split()
	orignx = float(orignx)
	origny = float(origny)

	# step.PAUSE(str([orignx,origny]))
        for x,y,symbol in infoList:
	    if showSymbol == "yes":
		# step.PAUSE(str([x, y, x - orignx,y - origny]))
		if "spacing:" in noteText:
		    step.COM("note_add,layer=%s,x=%s,y=%s,user=%s,text=%s %s" %
		             (layer, x - orignx, y - origny, user, noteText, symbol))
		else:
		    step.COM("note_add,layer=%s,x=%s,y=%s,user=%s,text=%s symbol:%s"%(layer,x - orignx,y - origny,user,noteText,symbol))
	    else:
		step.COM("note_add,layer=%s,x=%s,y=%s,user=%s,text=%s "%(layer,x - orignx,y - origny,user,noteText))
		
        if showNote == "yes":            
            step.COM("zoom_home")
	    step.COM("note_page_close")
            step.clearAll()
            step.display(layer,work=1)
	    if sys.platform == "win32":
		step.COM("note_page_show,layer=%s"%layer)
	    else:
		step.COM("set_note_layer,layer=%s"%layer)
		step.COM("show_component,component=Notes,show=yes,width=0,height=0")
	    
    def parseInfoList(self,step,infoList, calc_legth=None):
        dic_Obj = step.parseFeatureInfo(infoList)
        allsymbol_xy = []
	exists_coordinate = []
        for key in dic_Obj:
            for Obj in dic_Obj[key]:
                if Obj.shape in ["Pad","Text", "Barcode"]:# and Obj.polarity == "positive":
		    if (Obj.x,Obj.y) in exists_coordinate:
			continue
		    
		    if Obj.shape == "Pad":
			allsymbol_xy.append((Obj.x,Obj.y,Obj.symbol))
			exists_coordinate.append((Obj.x,Obj.y))
		    else:
			allsymbol_xy.append((Obj.x,Obj.y,Obj.text))
			exists_coordinate.append((Obj.x,Obj.y))
			
                if Obj.shape in ["Arc"]:  # and Obj.polarity == "positive":
		    if (Obj.xs,Obj.ys) in exists_coordinate:
			continue
		    
		    allsymbol_xy.append((Obj.xs, Obj.ys, Obj.symbol))
		    exists_coordinate.append((Obj.xs,Obj.ys))
		    
		if Obj.shape in ["Line"]:
		    if ((Obj.xs + Obj.xe) / 2.0, (Obj.ys + Obj.ye) / 2.0) in exists_coordinate:
			continue
		    if calc_legth is None:			
			allsymbol_xy.append(((Obj.xs + Obj.xe) / 2.0, (Obj.ys + Obj.ye) / 2.0, Obj.symbol))
		    else:
			if calc_legth == "inch":
			    flag = 39.37
			    units = "mil"
			else:
			    flag = 1
			    units = "mm"
			allsymbol_xy.append(((Obj.xs + Obj.xe) / 2.0, (Obj.ys + Obj.ye) / 2.0,
			                     Obj.symbol+" value:{0} {1}".format(round(Obj.len*flag, 1), units)))
			
		    exists_coordinate.append(((Obj.xs + Obj.xe) / 2.0, (Obj.ys + Obj.ye) / 2.0))
		    
		if Obj.shape in ["Surface"]:
		    if (Obj.x,Obj.y) in exists_coordinate:
			continue		    
		    allsymbol_xy.append((Obj.x,Obj.y,"surface"))		    
		    exists_coordinate.append((Obj.x,Obj.y))
		    
	return allsymbol_xy
    
    def check_npth_holes(self):
	"""检测NPTH孔是否漏套铜"""
	step = gClasses.Step(job, stepname)
	step.open()
	if step.isLayer("drl"):
	    drillLayer = "drl"
	else:
	    items = [layer for i, layer in enumerate(matrixInfo["gROWname"])
	            if matrixInfo["gROWcontext"][i] == "board"
	            and matrixInfo["gROWlayer_type"][i] == "drill"]
	
	    item, okPressed = QtGui.QInputDialog.getItem(QtGui.QWidget(), u"提示", u"请选择通孔层:", items, 0, False, Qt.Qt.WindowStaysOnTopHint)
	
	    drillLayer = str(item)
	    
	step.clearAll()
	step.affect(drillLayer)
	step.resetFilter()
	step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute=.drill,option=non_plated")
	step.selectAll()
	npth_holes = drillLayer + "_npth"
	if step.isLayer(npth_holes):
	    step.removeLayer(npth_holes)
	    
	if step.featureSelected():
	    step.copySel(npth_holes)
	    
	    for worklayer in signalLayers:
		polarity = get_layer_polarity(worklayer)
		if not step.isLayer(worklayer + "_opt"):
		    step.createLayer(worklayer + "_opt")
		else:
		    step.COM("truncate_layer,layer=%s_opt" % worklayer)
		    
		if polarity == "negative":
		    invert = "yes"
		    step.clearAll()
		    step.affect(worklayer + "_opt")
		    step.COM("fill_params,type=solid,origin_type=datum,solid_type=surface,min_brush=0.254,\
			use_arcs=yes,symbol=,dx=2.54,dy=2.54,break_partial=yes,cut_prims=no,outline_draw=no,\
			outline_width=0,outline_invert=no")
		    step.COM("sr_fill,polarity=positive,step_margin_x=0,step_margin_y=0,step_max_dist_x=2540,\
		    step_max_dist_y=2540,sr_margin_x=0,sr_margin_y=0,sr_max_dist_x=400,sr_max_dist_y=500,\
		    nest_sr=yes,stop_at_steps=,consider_feat=no,consider_drill=no,consider_rout=no,\
		    dest=affected_layers,attributes=no") 
		else:
		    invert = "no"
		
		step.clearAll()
		step.affect(worklayer)
		step.copyToLayer(worklayer + "_opt", invert= invert)
		step.clearAll()
		step.affect(worklayer + "_opt")
		step.contourize()
		
		step.clearAll()
		step.affect(npth_holes)
		step.refSelectFilter(worklayer + "_opt")
		if step.featureSelected():
		    STR=r'-t layer -e %s/%s/%s -d FEATURES -o select,units= mm' %(jobname,stepname,npth_holes)
		    infoList = step.INFO(STR)
		    
		    infoList = self.parseInfoList(step, infoList)
		    
		    self.addNote(step, drillLayer, infoList, "find %s has npth hole touch copper please check"%drillLayer)
		    step.display(drillLayer)
		    step.display_layer(worklayer, num=2)
		    
		    try:
			uploadinglog(__credits__, __version__ + str(infoList + [worklayer]) + " " + func, stepname, GEN_USER= top.getUser())
		    except Exception, e:
			print e		    
		    step.PAUSE("please check npth holes")
		    step.removeLayer(npth_holes)
		    step.removeLayer(worklayer + "_opt")
		    #return str(infoList + [worklayer])
		    return ""
		else:		    
		    step.removeLayer(worklayer + "_opt")
		    
	step.removeLayer(npth_holes)
	return "sucess"		    
    
    def get_big_pth_holes(self, jobname, stepname, drillLayer):
	"""获取大于2.0的PTH孔"""
	job = gClasses.Job(jobname)
	step = gClasses.Step(job, stepname)
	step.open()
	STR=r'-t layer -e %s/%s/%s -d FEATURES,units= mm' %(jobname,stepname,drillLayer)
	infoList = step.INFO(STR)
	padObj = step.parseFeatureInfo(infoList)['pads']
	lineObj = step.parseFeatureInfo(infoList)['lines']
	
	holes = [obj for obj in padObj + lineObj
	         if getattr(obj, "drill", None) != "non_plated"
	         and obj.symbol.startswith("r")
	         and float(obj.symbol[1:]) >= 2000]
	
	#print [(obj.symbol, obj.drill) for obj in holes]
	
	return holes    

    def deleteNote(self, jobname, stepname, layers):
        job = gClasses.Job(jobname)
        step = gClasses.Step(job, stepname)
        step.open()

	if isinstance(layers, list):
	    for layer in layers:
		if step.isLayer(layer):
		    step.COM(
		        "note_delete_all,layer=%s,note_from=0,note_to=2147483647,user=" % layer)

	elif isinstance(layers, str):
	    if step.isLayer(layers):
		step.COM("note_delete_all,layer=%s,note_from=0,note_to=2147483647,user=" % layers)


if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)

    main = rule()
    func = None
    try:
	func = sys.argv[1]
    except Exception, e:
	print e

    args = []
    try:
	args = sys.argv[2:]
    except Exception, e:
	print 'args:', e

    ###测试
    #func = ""
    #args = [""]
    ####

    if func is None:
	pass
    else:

	if hasattr(main, func):
	    if args:
		result = getattr(main, func)(args)
	    else:
		result = getattr(main, func)()

	    if result:
		try:
		    uploadinglog(__credits__, __version__ + result + " " + func, stepname, GEN_USER= top.getUser())
		except Exception, e:
		    print e
    
    sys.exit()