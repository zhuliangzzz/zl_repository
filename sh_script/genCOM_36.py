#!/usr/bin/env python
# -*- coding: utf-8 -*-
#---------------------------------------------------------#
#               SUNTAK SOFTWARE GROUP                     #
#---------------------------------------------------------#
#@Author       :    LiuChuang
#@Mail         :    Chuang_cs@163.com
#@Date         :    2018/09/15
#@Revision     :    2.0.0
#@File         :    genCOM.py
#@Software     :    PyCharm
#@Usefor       :    支持Python3.x的genesis COM 命令接口
#---------------------------------------------------------#

_header = {
    'description': '''
    -> 本程序主要服务于胜宏科技(惠州)，任何其他团体或个人如需使用，必须经胜宏科技(惠州)相关负责人及
       作者的批准，并遵守以下约定；
    1> 本着尊重创作者的劳动成果，任何团体或个人在使用此程序的时候，均需要知会此程序的原始创作者；
    2> 在任何场合宣导、宣传，在任何文件、报告、邮件中提及本程序的全部或部分功能，均需要声明此程序的
       原始创作者；
    3> 在任何时候对本程序做部分修改或者是升级时，必须要保留文件的原始信息，包括原始文件名、创作者及
       联系方式、创作日期等信息，且不得删除程序中的源代码，只能进行注释处理；   
'''
}
"""
                   _ooOoo_
                  o8888888o
                  88" . "88
                  (| -_- |)
                  O\  =  /O
               ____/`---'\____
             .'  \\|     |//  `.
            /  \\|||  :  |||//  \
           /  _||||| -:- |||||-  \
           |   | \\\  -  /// |   |
           | \_|  ''\---/''  |   |
           \  .-\__  `-`  ___/-. /
         ___`. .'  /--.--\  `. . __
      ."" '<  `.___\_<|>_/___.'  >'"".
     | | :  `- \`.;`\ _ /`;.`/ - ` : | |
     \  \ `-.   \_ __\ /__ _/   .-` /  /
======`-.____`-.___\_____/___.-`____.-'======
                   `=---='
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
         佛祖保佑       永无BUG
"""



# Import Standard Python Modules
import os, sys, string, time


# This object defines the low-level interface methods
#   for use with Genesis.  It serves as a base-class
#   for the higher-level objects.
class Genesis:
    # Initialize method, called when object is instantiated.
    def __init__(self):
        self.prefix = '@%#%@'
        self.blank()
        self.normalize()
        
        # Set up tmp files; must be unique to this instance,
        #   to allow more than one tmpfile to exist concurrently
        self.pid = os.getpid()
        tmp = 'gen_'+str(self.pid)+'.'+str(time.time())
        if 'GENESIS_TMP' in os.environ.keys():
            self.tmpfile = os.path.join(os.environ['GENESIS_TMP'], tmp)
        else:
            self.tmpfile = os.path.join('/tmp', tmp)
    
    # Method called when the instance is deleted, or
    #   garbage collected.  Cleans up after self.    
    def __del__(self):
        if os.path.isfile(self.tmpfile):
            os.unlink(self.tmpfile)
    
    # Normalize the path to GENESIS_EDIR, and make sure 
    #   the environment is set.
    def normalize(self):
        self.incamProduct = os.environ.get('INCAM_PRODUCT', None)
        if self.incamProduct:
            self.gendir = r'/incam'
            self.edir = self.incamProduct
        else:
            if 'GENESIS_DIR' not in os.environ.keys():
                self.error('GENESIS_DIR not set', 1)
            else:
                self.gendir = os.environ['GENESIS_DIR']
            if 'GENESIS_EDIR' not in os.environ.keys():
                self.error('GENESIS_EDIR not set', 1)
            else:
                self.edir = os.environ['GENESIS_EDIR']
                self.edir = os.path.join(self.gendir, self.edir)  
        return 0
        
    # Empties out the return values
    def blank(self):
        self.STATUS   = None
        self.READANS  = None
        self.COMANS   = None
        self.PAUSANS  = None
        self.MOUSEANS = None    
    
    # Send a command to STDOUT    
    def sendCmd(self, cmd, args=''):
        self.blank()
        wsp = ' '*(len(args)>0)
        cmd = self.prefix + cmd + wsp + args + '\n'
        sys.stdout.write(cmd)
        sys.stdout.flush()
        return 0
    
    # Basic error handler
    def error(self, msg, severity=0):
        sys.stderr.write(msg+'\n')
        if severity:
            sys.exit(severity)
            
    # Basic output writer
    def write(self, msg):
        sys.stdout.write(msg+'\n')
    
    
    #  ---------------------------------------
    #  Genesis Commands
    #  ---------------------------------------
    def SU_ON(self):
        self.sendCmd('SU_ON')
        
    def SU_OFF(self):
        self.sendCmd('SU_OFF')
        
    def VON(self):
        self.sendCmd('VON')
        
    def VOF(self):
        self.sendCmd('VOF')
        
    def PAUSE(self, msg):
        self.sendCmd('PAUSE', msg)
        self.STATUS = int(input())
        self.READANS = input()
        self.PAUSANS = input()
        return self.STATUS
        
    def MOUSE(self, msg, mode='p'):
        self.sendCmd('MOUSE ' + mode, msg)
        self.STATUS = int(input())
        self.READANS = input()
        self.MOUSEANS = input()
        return self.STATUS
        
    def COM(self, args):
        self.sendCmd('COM', args)
        self.STATUS = int(input())
        self.READANS = input()
        self.COMANS = self.READANS[:]
        return self.STATUS
        
    def AUX(self, args):
        self.sendCmd('AUX', args)
        self.STATUS = int(input())
        self.READANS = input()
        self.COMANS = self.READANS[:]
        return self.STATUS
    
    # --- INFO methods ---

    def INFOMM(self,args):
        self.COM('info,out_file=%s,write_mode=replace,units=mm,args=%s' % (self.tmpfile,args))
        lineList = open(self.tmpfile,'r').readlines()
        os.unlink(self.tmpfile)
        return lineList
        
    def INFO(self,args, units="mm"):
        self.COM('info,out_file=%s,write_mode=replace,units=%s,args=%s' % (self.tmpfile,units,args))
        lineList = open(self.tmpfile,'r').readlines()
        os.unlink(self.tmpfile)
        return lineList

    def DO_INFO(self,args,units="mm"):
        # type: (object, object) -> object
        self.COM('info,out_file=%s,write_mode=replace,units=%s,args=%s' % (self.tmpfile,units,args))
        lineList = open(self.tmpfile,'r').readlines()
        os.unlink(self.tmpfile)
        infoDict = self.parseInfo(lineList)
        return infoDict

    def DISP_INFO(self,args):
        self.COM('info,out_file=%s,write_mode=replace,args=-m display %s' % (self.tmpfile,args))
        lineList = open(self.tmpfile,'r').readlines()
        os.unlink(self.tmpfile)
        infoDict = self.parseDispInfo(lineList)
        return infoDict
        
    def DISP_NOTES(self,args):
        self.COM('info,out_file=%s,write_mode=replace,args=-m display %s' % (self.tmpfile,args))
        lineList = open(self.tmpfile,'r').readlines()
        os.unlink(self.tmpfile)
        bigLine = ''
        for item in lineList:
            bigLine = bigLine + ' ' + str.strip(item)
        infoDict = self.parseDispNotes(bigLine)
        return infoDict
        
    # --- Utility commands ---
    def dbutil(self, *args):
        if self.incamProduct:
            binary = os.path.join('/incam/release/bin','dbutil')
        else:
            binary = os.path.join(self.edir,'misc','dbutil')
        args = str.join(args)
        fd = os.popen(binary + ' '+args)
        res = fd.readlines()
        return res
        
    # Convert string to int or float if possible.
    def convertToNumber(self, value):
        try:
            return int(value)
        except:
            try:
                return float(value)
            except:
                return value

    # Parse the output of an info command in "cshell" mode
    def parseInfo(self, infoList):
        # Parses csh variable assignments and wordlists.
        # Example: set gTOOLnum = ('1' '2' '3' ) OR set gLIMITSxmin = '-10.708661'
        dict = {}
        for line in infoList:
            ss = str.split(line, ' = ', 1)
            if len(ss) == 2:
                key = str.strip(ss[0])[4:]
                val = str.strip(ss[1])
                valList = str.split(val, "'")
                if '(' in val:
                    # Wordlist example: ['(', '1', '   ', '2', '   ', '3', '   ', '4', '    )']
                    dict[key] = []
                    for n in range(len(valList)):
                        if n % 2 == 1:
                            # Append odd items to the list.
                            dict[key].append(valList[n])
                elif len(valList) == 3:
                    # Single value example: ['', 'test', '']
                    dict[key] = str.split(val, "'")[1]
                elif len(valList) == 1:
                    dict[key] = str.split(val, "'")[0]
        return dict
    
    # Parse the output of an info command in "display" mode
    def parseDispInfo(self, infoList):
        mainDict = {}
        for line in infoList:
            line = str.strip(line)
            try:
                exec(line)
            except SyntaxError:
                key = string.splitfields(line, '[')[0]
                if not key in mainDict.keys():
                    exec('mainDict[\''+key+'\'] = []')
                vals = string.splitfields(string.splitfields(line, ':')[1], ',')
                for val in vals:
                    ss = string.splitfields(val, '=')
                    try:
                        val = eval(ss[1])
                    except:
                        val = ss[1]
                    STR = 'dict[\''+ss[0]+'\'] = val'
                    exec(STR)
                exec('mainDict[\''+key+'\'].append(dict)')
        return mainDict

class GEN_COM (Genesis):
    """genesis操作的常用COMMANDS"""
    def __init__(self, job=None, step=None):
        Genesis.__init__(self)
        self.job = job
        self.step = step
        self.group = None

    #--Get the current username
    def getUser(self):
        self.COM('get_user_name')
        self.user = self.COMANS
        return self.user

    #--打开或关闭影响层
    def AFFECTED_LAYER(self, name, affected):
        self.COM('affected_layer, name = %s, mode = single, affected =%s' % (name, affected))

    # --添加文件
    def ADD_TEXT(self,add_x, add_y, txt, x_size, y_size, attr='no',polarity='positive',angle='0',mirr='no',font='simple'):
        self.COM('add_text,attributes=%s,type=string,x=%s,y=%s,text=%s,x_size=%s,y_size=%s,'
                 'w_factor=0.984251976,polarity=%s,angle=%s,mirror=%s,fontname=%s,ver=1'
                % (attr, add_x, add_y, txt, x_size, y_size, polarity, angle, mirr, font))
    #--添加Pad
    def ADD_PAD(self, add_x, add_y, symbol, pol='positive', attr='no', angle=0, mir='no', nx=1, ny=1, dx=0, dy=0,
                xscale=1, yscale=1):
        self.COM('add_pad, attributes = %s, x = %f, y = %f, symbol = %s,polarity = %s,'
                    'angle = %f, mirror = %s, nx = %d, ny = %d,dx = %f, dy = %f, xscale = %f, yscale = %f'
                 % (attr, add_x, add_y, symbol, pol, angle, mir, nx, ny, dx, dy, xscale, yscale))

    #--原位置添加尾孔 Step
    def ADD_STEP(self, WK_STEP, add_step):
        """传入删除Step时记录的Dict信息，还原对应Step删除前的位置"""
        self.is_add='no'
        self.units=self.GET_UNITS()
        if self.units != 'mm' : self.CHANGE_UNITS('mm')
        if WK_STEP['exist_'+add_step] == 'yes':
            self.COM('sr_tab_add,line=1,step=%s,x=%s,y=%s,nx=1,ny=1,angle=%s,mirror=%s'
                     % (WK_STEP['name_'+add_step], WK_STEP['xa_'+add_step], WK_STEP['ya_'+add_step], WK_STEP['angle_'+add_step], WK_STEP['mir_'+add_step]))

    #--关闭型号
    def CLOSE_JOB(self, job):
        self.job=job
        self.COM('close_job,job=%s' % self.job)
        # self.lockStat = self.dbStat()
        self.CHECK_IN(self.job)

    #--Check in型号
    def CHECK_IN(self, job):
        self.job=job
        self.VOF()
        self.COM('check_inout,mode=in,type=job,job=%s' % self.job)
        self.status=self.STATUS
        self.VON()
        return self.status
    
    #--Check in型号
    def CHECK_OUT(self, job):
        self.job=job
        self.VOF()
        self.COM('check_inout,mode=out,type=job,job=%s' % self.job)
        self.status=self.STATUS
        self.VON()
        return self.status
    
    #--清除层
    def CLEAR_LAYER(self):
        self.COM('clear_layers')
        self.COM('affected_layer,name=,mode=all,affected=no')
        return self.STATUS

    #--清除选中物体及高亮
    def CLEAR_FEAT(self):
        self.COM('clear_highlight')
        self.COM('sel_clear_feat')

    #--关闭Step
    def CLOSE_STEP(self):
        self.COM('editor_page_close')
        return self.STATUS

    #--改变单位
    def CHANGE_UNITS(self, units):
        self.units=units
        self.COM('units, type=%s' % self.units)
        return self.STATUS

    #--创建层别
    def CREATE_LAYER(self, layer, ins_lay='', context='misc', add_type='signal', pol='positive', location='after'):
        self.COM('create_layer,layer=%s,context=%s,type=%s,polarity=%s,ins_layer=%s,location=%s'
                 % (layer,context,add_type,pol,ins_lay,location))
        return self.STATUS

    #--创建JOB、创建STEP
    def CREATE_ENTITY(self, db, job, step=None):
        self.db=db
        self.job=job
        self.step=step
        #--当Step不存在时，创建 JOB
        if not self.step and self.job:
            self.COM('create_entity, job=, is_fw=no, type=job, name=%s, db=%s, fw_type=form' % (self.job, self.db))
            return self.STATUS
        # --当Step存在时，创建STEP
        if self.step and self.job:
            self.COM('create_entity, job=%s, is_fw=no, type=step, name=%s, db=%s, fw_type=form' % (self.job, self.step, self.db))
            return self.STATUS

    #--削除指定区域内容
    def CLIP_AREA(self, area='profile', area_type='rectangle', inout='outside', contour_cut='yes', margin=0, feat_types='line;pad;surface;arc;text'):
        self.COM('clip_area_strt')
        self.COM('''clip_area_end,layers_mode=affected_layers,layer=,area=%s,area_type=%s,
                 inout=%s,contour_cut=%s,margin=%s,feat_types=%s'''
                 % (area,area_type,inout,contour_cut,margin,feat_types))
        return self.STATUS

    #--物件属性定义(reset传入0或1)
    def CUR_ATR_SET(self, attr, text=None, reset=0, add=False):
        """reset传入0或1"""
        if reset:
            self.CUR_ART_RESET()
        if text:
            self.COM('cur_atr_set,attribute=%s,text=%s' % (attr, text))
        else:
            self.COM('cur_atr_set,attribute=%s' % attr)
        #--是否进行Change
        if add:
            self.COM('sel_change_atr,mode=add')

    #--物件属性重置
    def CUR_ART_RESET(self):
        self.COM('cur_atr_reset')

    #--两层物体比对
    def COMPARE_LAYERS(self, layer1, job2, step2, layer2, layer2_ext='', tol=25.4, area='global', consider_sr='yes', ignore_attr='', map_layeer='compare_layer++', res=5080):
        self.COM('compare_layers,layer1        = %s,'
                                'job2          = %s,'
                                'step2         = %s,'
                                'layer2        = %s,'
                                'layer2_ext    = %s,'
                                'tol           = %s,'
                                'area          = %s,'
                                'consider_sr   = %s,'
                                'ignore_attr   = %s,'
                                'map_layer     = %s,'
                                'map_layer_res = %s'
                 % (layer1, job2, step2, layer2, layer2_ext, tol, area, consider_sr, ignore_attr, map_layeer, res))
        self.com_result=self.COMANS
        self.DELETE_LAYER(map_layeer)
        return self.com_result

    #--COPY Step or Symbol
    def COPY_ENTITY(self, cp_type, source_job, source_name, dest_job, dest_name, dest_db=''):
        self.COM('copy_entity,type       = %s,'
                        'source_job      = %s,'
                        'source_name     = %s,'
                        'dest_job        = %s,'
                        'dest_name       = %s,'
                        'dest_database   = %s'
                 % (cp_type, source_job, source_name, dest_job, dest_name, dest_db))
        return self.STATUS

    # --Copy layer from other step
    def COPY_LAYER(self,s_job,s_step,s_layer,d_layer,mode='replace',invert='no'):
        """
        从同一JOB或其它JOB拷贝Layer（单层COPY）
        :param s_job:　  源JOB　
        :param s_step: 　源STEP
        :param s_layer:　源Layer
        :param d_layer:  目标层
        :param mode:     覆盖模式
        :param invert:   COPY极性
        :return:         返回处理结果
        """
        self.VOF()
        self.COM('copy_layer,source_job=%s,source_step=%s,source_layer=%s,dest=layer_name,dest_layer=%s,mode=%s,invert=%s'
                 % (s_job,s_step,s_layer,d_layer,mode,invert))
        copy_s = self.STATUS
        self.VON()
        # --当正常COPY OK后返回信息
        if copy_s == 0:
            return True
        else:
            return False

    #--检测该层是否存在物体
    def CHECK_LAYER_FEATURES(self, layer, job=os.environ.get('JOB', None), step = os.environ.get('STEP', None)):
        """返回yes or no 来说明层中的物体是否存在"""
        self.val=self.INFO('-t layer -e %s/%s/%s -m display -d FEATURES' % (job, step, layer))
        #--当层中无物体时,info文件中仅有一行信息，即：### Layer - gts features data ###
        if len(self.val) > 1:
            return 'yes'
        else:
            return 'no'

    # --计算铜面积
    def COPPER_AREA(self, lay_1, copper_th, drl_list, thick_h):
        """
        获取实物面积
        :return: 当无异常报错时，返回两个数据，一个面积，一个百分比
        """
        self.VOF()
        self.COM('copper_area,layer1=%s,layer2=,edges=yes,copper_thickness=%s,drills=yes,consider_rout=no,'
                 'ignore_pth_no_pad=no,drills_source=matrix,drills_list=%s,thickness=%s,resolution_value=25.4,'
                 'x_boxes=3,y_boxes=3,area=no,dist_map=yes' % (lay_1, copper_th, drl_list, thick_h))
        self.Arec_V = self.COMANS
        self.area = self.STATUS
        self.VON()
        # --返回
        if self.area == 0:
            # --以空格分隔出数组
            self.Area = '%.1f' % float(self.Arec_V.split(' ')[0])
            self.PerCent = '%.2f' % float(self.Arec_V.split(' ')[1])
            return float(self.Area), float(self.PerCent)
        else:
            return False, False

    #--删除层
    def DELETE_LAYER(self, layer):
        self.VOF()
        self.COM('delete_layer,layer=%s' % layer)
        self.VON()

    #--删除Step
    def DELETE_STEP(self, del_step, job = os.environ.get('JOB', None), step = os.environ.get('STEP', None)):
        """返回所有Step相关信息的Dict"""
        self.step_sr=self.DO_INFO('-t step -e %s/%s -m script -d SR' % (job,step))
        print (self.step_sr)
        num=0
        WK_STEP={}
        for loop_step in self.step_sr['gSRstep'] :
            sr_line = num + 1
            if loop_step == del_step:
                WK_STEP['name_'+loop_step]=loop_step
                WK_STEP['xa_' + loop_step] = self.step_sr['gSRxa'][num]
                WK_STEP['ya_' + loop_step] = self.step_sr['gSRya'][num]
                WK_STEP['angle_' + loop_step] = self.step_sr['gSRangle'][num]
                WK_STEP['mir_' + loop_step] = self.step_sr['gSRmirror'][num]
                WK_STEP['exist_' + loop_step] = 'yes'
                #--删除tab中的Step
                self.COM('sr_tab_del,line=%d' % sr_line)
            num += 1
        #--返回字典信息
        return WK_STEP

    #--删除JOB或Step
    def DELETE_ENTITY (self, del_type, del_name):
        """
        删除指定类型的ENTITY
        :param del_type: job, step, symbol, stackup, wheel, matrix
        :param del_name: existing entity name
        :return: delete result
        """
        self.VOF()
        self.COM('delete_entity,job=,type=%s,name=%s' % (del_type, del_name))
        delStatus = self.STATUS
        self.VON()
        return delStatus

    # --导出Tgz
    def EXPORT_JOB(self, jobName, outPath, mode='tar_gzip', submode='full', fmat='genesis', outName = None):
        """
        导出JOB至指定位置
        :param jobName:型号名
        :param outPath: 输出路径
        :param mode: 输出格式（tar_gzip，tar，directory）
        :param submode:输出哪些文件（full, partial）
        :param fmat: 支持类型
        :param outName:输出名称
        :return:返回输出结果
        """
        if not outName:
            outName = jobName
        self.VOF()
        self.COM('export_job,job=%s,path=%s,mode=%s,submode=%s,format=%s,'
                 'overwrite=yes,output_name=%s' % (jobName, outPath, mode, submode, fmat, outName))
        self.expv = self.COMANS
        self.expv = self.STATUS
        self.VON()
        
        # --返回导出结果(0:表示成功，非0：表示失败) 
        return self.expv
        
    # --计算铜或表面处理面积
    def EXPOSED_AREA(self, lay_1, mask_1, lay_2, mask_2, copper_th, drl_list, thick_h):
        """
        获取表面处理面积（沉金、OSP...）
        :return: 当无异常报错时，返回两个数据，一个面积，一个百分比
        """
        self.VOF()
        self.COM('exposed_area,layer1=%s,mask1=%s,layer2=%s,mask2=%s,mask_mode=or,edges=yes,'
                 'copper_thickness=%s,drills=yes,consider_rout=no,ignore_pth_no_pad=no,'
                 'drills_source=matrix,drills_list=%s,thickness=%s,resolution_value=25.4,'
                 'x_boxes=3,y_boxes=3,area=no,dist_map=yes' % (lay_1, mask_1, lay_2, mask_2, copper_th, drl_list, thick_h))
        self.Arec_V = self.COMANS
        self.area=self.STATUS
        self.VON()

        # --返回(当COMANS未获取到值时，self.COMANS 的值为None)
        if self.area == 0:
            # --以空格分隔出数组
            # print '\nXXXXXXXXXXXXXX:\n', self.Arec_V, self.area, '\nXXXXXXXXXXXXXXXX\n'
            try:
                self.Area    = '%.1f' % float(self.Arec_V.split(' ')[0])
                self.PerCent = '%.2f' % float(self.Arec_V.split(' ')[1])
                return float(self.Area), float(self.PerCent)
            except:
                return False, False
        else:
            return False, False


    #--过滤物体命令集
    def FILTER_RESET(self):
        self.COM('filter_reset,filter_name=popup')

    def FILTER_SET_POL(self, pol, reset=0):
        self.pol=pol
        if reset == 1 : self.FILTER_RESET()
        self.COM('filter_set,filter_name=popup,update_popup=no,polarity=%s' % self.pol)

    def FILTER_SET_TYP(self, feat_t, reset=0):
        self.feat_t=feat_t
        if reset == 1 : self.FILTER_RESET()
        self.COM('filter_set,filter_name=popup,update_popup=no,feat_types=%s' % self.feat_t)

    def FILTER_SET_PRO(self, pro, reset=0):
        self.pro=pro
        if reset == 1 : self.FILTER_RESET()
        self.COM('filter_set,filter_name=popup,update_popup=no,profile=%s' % self.pro)

    def FILTER_SET_DCODE(self, dcode, reset=0):
        self.dcode=dcode
        if reset == 1 : self.FILTER_RESET()
        self.COM('filter_set,filter_name=popup,update_popup=no,dcode=%s' % self.dcode)

    def FILTER_SET_INCLUDE_SYMS(self, in_syms, reset=0):
        self.in_syms=in_syms
        if reset == 1 : self.FILTER_RESET()
        self.COM('filter_set,filter_name=popup,update_popup=no,include_syms=%s' % self.in_syms)

    def FILTER_SET_FEAT_TYPES(self,feat_types, reset=0):
        self.feat_types = feat_types
        if reset == 1: self.FILTER_RESET()
        self.COM('filter_set,filter_name=popup,update_popup=no,feat_types=%s' % self.feat_types)

    def FILTER_SET_ATR_SYMS(self, atr_set, reset=0):
        self.atr_set=atr_set
        if reset == 1: self.FILTER_RESET()
        self.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=%s' % self.atr_set)

    def FILTER_OPTION_ATTR(self,attr, option, reset=0):
        self.attr=attr
        self.option=option
        if reset == 1: self.FILTER_RESET()
        self.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=%s,option=%s' % (self.attr, self.option))

    def FILTER_TEXT_ATTR(self, attr, text, reset=0):
        self.attr=attr
        self.text=text
        if reset == 1: self.FILTER_RESET()
        self.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=%s,text=%s' % (self.attr, self.text))

    #--执行选择命令
    def FILTER_SELECT(self,op='select'):
        self.op=op
        self.COM('filter_area_strt')
        self.COM('filter_area_end,layer=,filter_name=popup,operation=%s,area_type=none,inside_area=no,intersect_area=no' % self.op)

    #--导入资料
    def INPUT_MANUAL_SET(self):
        pass

    #--导入Tgz资料
    def IMPORT_JOB(self, tgzpath, job, db):
        self.VOF()
        self.COM('import_job, db=%s, path=%s, name=%s, analyze_surfaces=no' % (db, tgzpath, job))
        status=self.STATUS
        self.VON()
        return status

    #--获得选中物体数量
    def GET_SELECT_COUNT(self):
        self.COM('get_select_count')
        return eval(self.COMANS)

    #--获取Genesis版本信息
    def GET_VERSION(self):
        self.COM('get_version')
        return self.COMANS

    #--获取当前层单位
    def GET_UNITS(self):
        self.COM('get_units')
        return self.COMANS

    # --获取工作层
    def GET_WORK_LAYER(self):
        self.COM('get_work_layer')
        return self.COMANS

    #--根据属性获取Board层
    def GET_ATTR_LAYER(self, lay_type, job=os.environ.get('JOB', None)):
        """返回满足条件的数组"""
        self.job=job
        m_info=self.DO_INFO('-t matrix -e %s/matrix' % self.job)
        self.LayValues=[]
        for row in m_info['gROWrow']:
            num=m_info['gROWrow'].index(row)
            if lay_type == 'drill':
                if m_info['gROWcontext'][num] == 'board' and  m_info['gROWlayer_type'][num] == 'drill':
                    self.LayValues.append(m_info['gROWname'][num])
            if lay_type == 'signal':
                if m_info['gROWcontext'][num] == 'board' and (m_info['gROWlayer_type'][num] == 'signal' or m_info['gROWlayer_type'][num] == 'power_ground'):
                    self.LayValues.append(m_info['gROWname'][num])
            if lay_type == 'power_ground':
                if m_info['gROWcontext'][num] == 'board' and m_info['gROWlayer_type'][num] == 'power_ground':
                    self.LayValues.append(m_info['gROWname'][num])
            if lay_type == 'silk_screen':
                if m_info['gROWcontext'][num] == 'board' and m_info['gROWlayer_type'][num] == 'silk_screen':
                    self.LayValues.append(m_info['gROWname'][num])
            if lay_type == 'solder_mask':
                if m_info['gROWcontext'][num] == 'board' and m_info['gROWlayer_type'][num] == 'solder_mask':
                    self.LayValues.append(m_info['gROWname'][num])
            if lay_type == 'inner':
                if m_info['gROWcontext'][num] == 'board' and m_info['gROWside'][num] == 'inner':
                    self.LayValues.append(m_info['gROWname'][num])
            if lay_type == 'outer':
                if m_info['gROWcontext'][num] == 'board' and m_info['gROWlayer_type'][num] == 'signal' and (m_info['gROWside'][num] == 'top' or m_info['gROWside'][num] == 'bottom'):
                    self.LayValues.append(m_info['gROWname'][num])
            if lay_type == 'coverlay':
                if m_info['gROWcontext'][num] == 'board' and m_info['gROWlayer_type'][num] == 'coverlay' and (
                        m_info['gROWside'][num] == 'top' or m_info['gROWside'][num] == 'bottom'):
                    self.LayValues.append(m_info['gROWname'][num])
            if lay_type == 'all':
                #--不为空时
                if not m_info['gROWname'][num]:
                    self.LayValues.append(m_info['gROWname'][num])
        #--返回对应数组信息
        return self.LayValues

    #--返回钻孔层的起始层
    def GET_DRILL_THROUGH(self, layer, job=os.environ.get('JOB', None), step = os.environ.get('STEP', None)):
        """返回起始层信息与终止层信息"""
        self.start=self.DO_INFO('-t layer -e %s/%s/%s -d DRL_START' % (job, step, layer))
        self.end=self.DO_INFO('-t layer -e %s/%s/%s -d DRL_END' % (job, step, layer))
        #--返回两个值
        return self.start['gDRL_START'], self.end['gDRL_END']

    #--获取JOB中所有STEP列表
    def GET_STEP_LIST(self, job=os.environ.get('JOB', None)):
        """获取JOB中所有STEP列表，并返回列表信息"""
        self.job=job
        self.m_info=self.DO_INFO('-t matrix -e %s/matrix -d COL' % self.job)
        #--返回step列表信息
        return self.m_info['gCOLstep_name']

    #--获取料号的COPPER LAYER信息
    def GET_COPPER_LIST(self, Lay_Mir, job=os.environ.get('JOB', None)):
        """传入层别镜像的Dict"""
        self.job = job
        self.m_info = self.DO_INFO('-t matrix -e %s/matrix -d ROW' % self.job)
        self.num=0
        self.Copper_Info={}
        for row_n in self.m_info['gROWrow']:
            num=row_n-1
            if self.m_info['gROWcontext'] == 'board' and (self.m_info['gROWlayer_type'] == 'signal' or self.m_info['gROWlayer_type'] == 'power_ground'):
                self.r_name=self.m_info['gROWname'][num]
                if self.r_name in Lay_Mir.keys():
                    self.Foil_side=Lay_Mir[self.r_name]
                else:
                    self.Foil_side =self.m_info['gROWfoil_side'][num]
            self.Copper_Info[self.r_name]={
                'ROWcontext'    :    self.m_info['gROWcontext'][num],
                'ROWlayer_type' :    self.m_info['gROWlayer_type'][num],
                'ROWside'        :    self.m_info['gROWside'][num],
                'gROWfoil_side'    :    self.Foil_side,
                'Layer_Num'        :    row_n
            }
        #--返回Copper Dict
        return self.Copper_Info

    #--获取Profile的尺寸
    def GET_PROFILE_SIZE(self, job=os.environ.get('JOB', None), step = os.environ.get('STEP', None)):
        """获取Profile的尺寸，仅限Profile的尺寸，返回两个参数"""
        self.job=job
        self.step=step
        self.p_info=self.DO_INFO('-t step -e %s/%s -m script -d PROF_LIMITS' % (self.job, self.step))
        self.Pro_X = self.p_info['gPROF_LIMITSxmax'] - self.p_info['gPROF_LIMITSxmin'] + self.p_info['gPROF_LIMITSxmin'] * 2
        self.Pro_Y = self.p_info['gPROF_LIMITSymax'] - self.p_info['gPROF_LIMITSymin'] + self.p_info['gPROF_LIMITSymin'] * 2
        #--返回参数
        return self.Pro_X, self.Pro_Y

    #--GET当前JOB创建时间
    def GET_JOB_INFO(self, job, fw_path, parameter):
        """
        :param job: 型号
        :param fw_path: fw路径
        :param parameter: 参数（JOB_NAME ODB_VERSION_MAJOR ODB_VERSION_MINOR CREATION_DATE SAVE_DATE SAVE_APP SAVE_USER）
        :return:参数对应的值
        """
        info_p = os.path.join(fw_path, 'jobs', job, 'misc', 'info')
        #--判断文件是否存在
        if not os.path.isfile(info_p):
            print (u'info文件不存在'.encode('gb2312'))
            return None
        f = open(info_p, 'r')
        for info in f.readlines():
            info=info.strip('\n')
            info = info.strip(' ')
            par, val = info.split('=')
            if par == parameter:
                return val

    #--判断JOB是否存在
    def JOB_EXISTS(self, job):
        """判断JOB是否存在，并返回yes or no"""
        self.job=job
        self.j_info=self.DO_INFO('-t job -e %s -d EXISTS' % self.job)
        #--返回yes or no
        return self.j_info['gEXISTS']

    #--判断层别是否存在
    def LAYER_EXISTS(self, layer, job=os.environ.get('JOB', None), step = os.environ.get('STEP', None)):
        """判断Layer是否存在，并返回yes or no"""
        self.layer=layer
        self.job=job
        self.step=step
        self.l_info=self.DO_INFO('-t layer -e %s/%s/%s -d EXISTS' % (self.job, self.step, self.layer))
        #--返回yes or no
        return self.l_info['gEXISTS']

    #--打开 JOB
    def OPEN_JOB(self, job):        
        self.job=job
        self.status=self.CHECK_OUT(self.job)
        #--当正常Check out时，打开JOB
        if not self.status:
            self.VOF()
            self.COM('open_job, job=%s' % self.job)
            self.status=self.STATUS
            self.VON()
            return self.status
        return self.status

    #--打开 STEP
    def OPEN_STEP(self, step, job=os.environ.get('JOB', None), iconic='no'):
        self.job=job
        self.step=step
        self.iconic=iconic
        self.VOF()
        self.COM('open_entity, job=%s, type=step, name=%s ,iconic=%s' % (self.job, self.step, self.iconic))
        self.AUX('set_group, group=%s' % self.COMANS)
        self.status=self.STATUS
        self.VON()
        return self.status

    #--优化指定层
    def OPTIMIZE_LEVELS(self, layer, opt_lay, levels=1):
        """优化指定层别到另一指定层中"""
        self.layer=layer
        self.opt_lay=opt_lay
        self.levels=levels
        ##--判断opt_lay层是否存在
        #self.l_ex=self.LAYER_EXISTS(self.opt_lay)
        #if self.l_ex == 'yes':
        #    self.DELETE_LAYER(self.opt_lay)
        #--优化至指定层
        self.VOF()
        self.COM('optimize_levels, layer=%s, opt_layer=%s, levels=%s' % (self.layer, self.opt_lay, self.levels))
        self.status=self.STATUS
        self.VON()
        return self.status

    #--输出信息还原
    def OUTPUT_LAYER_RESET(self):
        self.COM('output_layer_reset')

    #--层输出设置
    def OUTPUT_LAYER_SET(self, layer, reset=0, angle=0, mir='no', x_scale=1, y_scale=1, pol='positive', line_units='mm'):
        if reset:
            self.OUTPUT_LAYER_RESET()
        self.VOF()
        self.COM('output_layer_set, layer=%s, angle=%s, mirror=%s, x_scale=%s, y_scale=%s, comp=0, polarity=%s,'
                 'setupfile=, setupfiletmp=, line_units=%s, gscl_file=, step_scale=no'
                 % (layer, angle, mir, x_scale, y_scale, pol, line_units))
        self.status=self.STATUS
        self.VON()
        return self.status

    #--输出GERBER274X
    def OUTPUT_GERBER(self, dir_path, nf1=3, nf2=5, job=os.environ.get('JOB', None), step=os.environ.get('STEP', None)):
        self.VOF()
        self.COM('output,job=%s,step=%s,format=Gerber274x,dir_path=%s,prefix=,suffix=,'
                 'break_sr=yes,break_symbols=yes,break_arc=no,scale_mode=all,surface_mode=contour,min_brush=1,'
                 'units=mm,coordinates=absolute,zeroes=none,nf1=%d,nf2=%d,x_anchor=0,y_anchor=0,wheel=,x_offset=0,'
                 'y_offset=0,line_units=inch,override_online=yes,film_size_cross_scan=0,film_size_along_scan=0,'
                 'ds_model=RG6500' % (job, step, dir_path, nf1, nf2))
        self.status=self.STATUS
        self.VON()
        return self.status
    
    #--保存JOB
    def SAVE_JOB(self, job=os.environ.get('JOB', None)):
        self.job=job
        self.COM('save_job, job=%s' % self.job)
        return self.STATUS

    #--参考选择
    def SEL_REF_FEAT(self, ref_lay, mode, pol='positive;negative', f_type='line;pad;surface;arc;text', include='', exclude=''):
        """mode 包含touch,disjoint,cover,include"""
        self.COM('sel_ref_feat, layers=%s, use=filter, mode=%s, pads_as=shape, f_types=%s, polarity=%s, include_syms=%s, exclude_syms=%s'
                 % (ref_lay, mode, f_type, pol, include, exclude))
        return self.STATUS

    #--COPY选择的物体
    def SEL_COPY(self, target_layer, invert='no', size=0, dx=0, dy=0, x_anchor=0, y_anchor=0, rotation=0, mir='none'):
        self.COM('sel_copy_other, dest=layer_name, target_layer=%s, invert=%s, size=%s, dx=%s, dy=%s, x_anchor=%s, y_anchor=%s'
                 'rotation=%s, mirror=%s'
                 % (target_layer, invert, size, dx, dy, x_anchor, y_anchor, rotation, mir))
        return self.STATUS

    #--移动选择的物体
    def SEL_MOVE(self, target_layer, invert='no', size=0, dx=0, dy=0, x_anchor=0, y_anchor=0, rotation=0, mir='none'):
        self.COM('sel_move_other, target_layer=%s, invert=%s, size=%s, dx=%s, dy=%s, x_anchor=%s, y_anchor=%s'
                 'rotation=%s, mirror=%s'
                 % (target_layer, invert, size, dx, dy, x_anchor, y_anchor, rotation, mir))
        return self.STATUS

    #--当前层移动
    def SEL_MOVE_SAME(self, dx, dy):
        self.dx=dx
        self.dy=dy
        self.COM('sel_move, dx=%s, dy=%s' % (self.dx, self.dy))

    #--改变选择物体Symbol
    def SEL_CHANEG_SYM(self, sym, angle='no'):
        self.sym=sym
        self.angle=angle
        self.COM('sel_change_sym, symbol=%s, reset_angle=%s' % (self.sym, self.angle))
        return  self.STATUS

    #--打散Surface
    def SEL_DECOMPOSE(self):
        self.VOF()
        self.COM('sel_decompose, overlap=yes')
        self.status=self.STATUS
        self.VON()
        return self.status

    #--打散物体（非Surface物体）
    def SEL_BREAK(self):
        self.VOF()
        self.COM('sel_break_level, attr_mode=merge')
        self.status=self.STATUS
        self.VON()
        return self.status

    #--删除选中物体
    def SEL_DELETE(self):
        self.COM('sel_delete')

    #--删除选中物体指定属性
    def SEL_DELETE_ATR(self, art):
        self.art=art
        self.COM('sel_delete_atr, attributes=%s' % self.art)

    #--框选物体
    def SEL_POLYLINE_FEAT(self, sel_x, sel_y, tol=0):
        """返回一个数据：框选物体的数量"""
        self.sel_x=sel_x
        self.sel_y=sel_y
        self.tol=tol
        self.COM('sel_polyline_feat, operation=select, x=%s, y=%s, tol=%s' % (self.sel_x, self.sel_y, self.tol))
        #--返回框选的结果（框选失物体的数量）
        return self.GET_SELECT_COUNT()

    #--以范围填充Surface
    def SEL_CUT_DATA(self, ignore_width='no', ignore_holes='none', start_positive='yes'):
        self.VOF()
        self.COM('sel_cut_data, det_tol=25.4, con_tol=25.4, filter_overlaps=no, delete_doubles=no, use_order=yes'
                 'ignore_width=%s, ignore_holes=%s, start_positive=%s, polarity_of_touching=same'
                 % (ignore_width, ignore_holes, start_positive))
        self.status=self.STATUS
        self.VON()
        return self.status

    #--预大选中物体
    def SEL_RESIZE(self, size):
        self.size=size
        self.COM('sel_resize, size=%s' % self.size)
        return self.STATUS

    #--反选命令
    def SEL_REVERSE(self):
        self.COM('sel_reverse')

    #--转换极性
    def SEL_POLARITY(self, pol):
        self.pol=pol
        self.COM('sel_polarity, polarity=%s' % self.pol)

    #--填充物体时参数设置
    def FILL_SUR_PARAMS(self):
        self.COM('fill_params, type=solid, origin_type=datum, solid_type=surface, std_type=line, min_brush=25.4'
                 'use_arcs=yes, symbol=, dx=2.54, dy=2.54, std_angle=45, std_line_width=254, std_step_dist=1270,'
                 'std_indent=odd, break_partial=yes, cut_prims=no, outline_draw=no, outline_width=0, outline_invert=no')

    #--执行填充
    def SR_FILL(self, polarity, step_margin_x, step_margin_y, step_max_dist_x, step_max_dist_y, mode='surface', sr_margin_x=0 ,sr_margin_y=0, sr_max_dist_x=0, sr_max_dist_y=0):
        """默认传入的参数会直接以Surface的形式填充指定区域"""
        if mode == 'surface':
            self.FILL_SUR_PARAMS()
        self.COM('sr_fill, polarity=%s, step_margin_x=%s, step_margin_y=%s, step_max_dist_x=%s, step_max_dist_y=%s'
                 'sr_margin_x=%s, sr_margin_y=%s, sr_max_dist_x=%s, sr_max_dist_y=%s, nest_sr=yes, stop_at_steps='
                 'consider_feat=no, consider_drill=no, consider_rout=no, dest=affected_layers, attributes=no'
                 % (polarity, step_margin_x, step_margin_y, step_max_dist_x, step_max_dist_y, sr_margin_x, sr_margin_y, sr_max_dist_x, sr_max_dist_y))

    #--平面化Surface
    def SEL_CONTOURIZE(self, accuracy=6.35, clean_hole_size=76.2):
        """
        clean_hole_mod 无法加入此参数，加入后会报‘The command sel_contourize does not have the field clean_hole_mod'的错
        """
        self.VOF()
        self.COM('sel_contourize, accuracy=%s, break_to_islands=yes, clean_hole_size=%s' % (accuracy, clean_hole_size))
        self.con_status=self.STATUS
        self.VON()
        return self.con_status

    #--判断STEP是否存在
    def STEP_EXISTS(self, job=os.environ.get('JOB', None), step=os.environ.get('STEP', None)):
        """判断STEP是否存在，并返回yes or no"""
        self.job=job
        self.step=step
        self.s_info=self.DO_INFO('-t step -e %s/%s -d EXISTS' % (self.job, self.step))
        #--返回STEP是否存在（yes or no)
        return self.s_info['gEXISTS']

    #--选择工作层
    def WORK_LAYER(self, name, number=1):
        if number == 1:
            self.CLEAR_LAYER()
        self.VOF()
        self.COM('display_layer,name=%s,display=yes,number=%d' % (name, number))
        if number == 1:
            self.COM('work_layer,name=%s' % name)
        self.status=self.STATUS
        self.VON()
        return self.status
    
    # --重命名层别 	
    def RENAME_LAYER(self, oldname, newname):
        self.VOF()
        self.COM('rename_layer,name=%s,new_name=%s' % (oldname,newname))
        self.status=self.STATUS    
        self.VON()
        return self.status
        
    # --转换中文
    def ZH_CODE(self, zh, code='gb2312'):
        """
        转换中文编码
        :param zh   : uncode格式式的中文字符
        :param code : 转换中文的格式
        :return     : 返回转换后的中文
        """
        self.zh = zh
        self.code = code
        return zh.encode(self.code)

    # --输出LOG记录
    def LOG(self, log_msg, code='gb2312', write='Y'):
        """
        记录日志文件至tmp盘
        :param log_msg: 传入的日志信息
        :param code: 传入的字符编码，默认gb2312中文
        :return: None
        """
        import time
        now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        log_date = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        if os.path.exists('C:/tmp'):
            tmp_f='C:/tmp/tMp_LoG'+str(log_date)+'.log'
        else:
            # --incam下需要转码为utf-8格式
            code='utf-8'
            tmp_f='/tmp/tMp_LoG'+str(log_date)+'.log'
        try:
            # log_msg=self.ZH_CODE(str(now_time)+u'：'+log_msg, code=code)
            log_msg=str(now_time)+log_msg
        except:
            log_msg = str(now_time)+self.ZH_CODE(u'：', code=code)+str(log_msg)
        print (log_msg)
        if write == 'Y':
            f=open(tmp_f,'a')
            f.write(log_msg+'\n')
            f.close()