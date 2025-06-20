#/usr/bin/env python
# -*- coding:utf8 -*-
import os,sys,re,platform
# --加载相对位置，以实现InCAM与Genesis共用
if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
import genCOM_26 as genCOM
from messageBox import msgBox
from PyQt4.QtGui import QMessageBox
from PyQt4 import QtCore, QtGui
from PyQt4.Qt import *


class current_step(object):
    """
    当前step定义为一个类，类里面需要执行的方法封装如下
    """
    def __init__(self,step_name,show_result = 'yes',parent=None):
        # 从环境变量中获取料号名
        self.jobName = os.environ.get('JOB', None)
        self.GEN = genCOM.GEN_COM()
        self.step_name = step_name
        self.fill_layer = 'sr_fill'
        self.flat_layer = 'sr_fill_flat'
        self.close_sr = 'close_sr'
        # === 定义全局变量，以下单位为mm
        self.check_dist = 1
        self.out_dist = 0.49999 * float(self.check_dist)
        # self.run()
        self.show_mess = show_result
        if self.show_mess != 'yes':
            # === 增加日志写入及获取 ===
            job_user_dir = os.environ.get('JOB_USER_DIR',None)
            all_check_dir = job_user_dir + '/all_check/'
            self.check_result_log = all_check_dir + "index_" + self.show_mess + ".log"

    def run(self):
        self.GEN.OPEN_STEP(self.step_name)
        self.GEN.VOF()
        self.GEN.DELETE_LAYER(self.flat_layer)
        self.GEN.DELETE_LAYER(self.fill_layer)
        self.GEN.CREATE_LAYER(self.fill_layer)
        self.GEN.VON()
        self.fill_sr(self.step_name)
        self.Cont_SR()
        self.Check_SR()

    def Get_SR(self,step_now):
        """
        通过DO_INFO获取子排版
        :return:
        """
        sr_list = []
        info = self.GEN.DO_INFO('-t step -e %s/%s -m script -d SR' % (self.jobName,step_now))
        for step in info['gSRstep']:
            if step not in sr_list:
                sr_list.append(step)
        return sr_list

    # def __del__(self):
    #     self.GEN.VOF()
    #     self.GEN.DELETE_LAYER(self.fill_layer)
    #     self.GEN.VON()

    def fill_sr(self,step_now):
        """
        填充子排版,如果子排版中还有子排版，会递归调用
        :return: None
        """
        fill_layer = self.fill_layer
        SR = self.Get_SR(step_now)
        for step in SR:
            self.GEN.OPEN_STEP(step)
            self.GEN.CHANGE_UNITS('mm')
            self.GEN.WORK_LAYER(fill_layer)
            # 每个step在fill的时候，都附加一个.string=step的属性
            self.GEN.COM('cur_atr_reset')
            self.GEN.COM('cur_atr_set,attribute=.string,text=%s' % step)
            sr_info = self.GEN.DO_INFO('-t step -e %s/%s -m script -d SR' % (self.jobName,step))
            self.GEN.COM('sr_fill,polarity=%s,step_margin_x=%s,step_margin_y=%s,step_max_dist_x=%s,step_max_dist_y=%s,'
                'sr_margin_x=%s,sr_margin_y=%s,sr_max_dist_x=%s,sr_max_dist_y=%s,nest_sr=no,stop_at_steps=,'
                'consider_feat=no,consider_drill=no,consider_rout=no,dest=affected_layers,attributes=yes'
                % ('positive', '-' + str(self.out_dist), '-' + str(self.out_dist), 2540, 2540, 0, 0, 0, 0))
            self.GEN.COM('cur_atr_reset')
            self.GEN.CLEAR_LAYER()
            self.GEN.CLOSE_STEP()
            if len(sr_info['gSRstep']) > 0:
                # --递归调用，子排版中存在子排版
                self.fill_sr(step)

    def Cont_SR(self):
        """
        填充子排版，通过将sr_margin_x设为-2540,sr_margin_y设为-2540,可以实现
        :param sr_list:
        :return:
        """
        SR_list = []
        fill_layer = self.fill_layer
        flat_layer = self.flat_layer
        SR = self.Get_SR(self.step_name)
        for step in SR:
            sr_info = self.GEN.DO_INFO('-t step -e %s/%s -m script -d SR' % (self.jobName,step))
            if len(sr_info['gSRstep']) > 0:
                SR_list.append(step)

        # --s96604pn047a2 set中拼了其它step,要flatten出来，防止误报
        for sr in SR_list:
            self.GEN.OPEN_STEP(sr)
            self.GEN.COM('flatten_layer,source_layer=%s,target_layer=%s' % (fill_layer, flat_layer))
            self.GEN.COPY_LAYER(self.jobName,sr,flat_layer,fill_layer)
            self.GEN.WORK_LAYER(fill_layer)
            self.GEN.SEL_CONTOURIZE()
            # --整体化后加大1mil,不然cover不住里面的edit
            self.GEN.COM('sel_resize,size=25.4,corner_ctl=no')
            self.GEN.COM('cur_atr_reset')
            self.GEN.COM('cur_atr_set,attribute=.string,text=%s' % sr)
            self.GEN.COM('sel_change_atr,mode=add')
            self.GEN.COM('cur_atr_reset')
            self.GEN.DELETE_LAYER(flat_layer)
            self.GEN.CLOSE_STEP()

        # --在panel中将子排版中包含的子排版删除，防止误报,990/013a2 panel中既有set又有edit
        self.GEN.OPEN_STEP(self.step_name)
        self.GEN.COM('flatten_layer,source_layer=%s,target_layer=%s' % (fill_layer,flat_layer))
        self.GEN.WORK_LAYER(flat_layer)
        for sr in SR_list:
            self.GEN.FILTER_RESET()
            self.GEN.FILTER_TEXT_ATTR('.string',sr)
            self.GEN.FILTER_SELECT()
            self.GEN.FILTER_RESET()
            # 工作层和ref层均为flat_layer，注意use=select
            self.GEN.COM( 'sel_ref_feat,layers=,use=select,mode=cover,pads_as=shape,f_types=surface,'
                          'polarity=positive,include_syms=,exclude_syms=')
            count = self.GEN.GET_SELECT_COUNT()
            # --删除set里面被set cover的step
            if count > 0:
                self.GEN.SEL_DELETE()
            # --整体化后加大1mil,现在还原防止误报，参考料号586/475a4
            self.GEN.FILTER_TEXT_ATTR('.string', sr)
            self.GEN.FILTER_SELECT()
            self.GEN.FILTER_RESET()
            count = self.GEN.GET_SELECT_COUNT()
            if count > 0:
                self.GEN.COM('sel_resize,size=-25.4,corner_ctl=no')
        self.GEN.VOF()
        self.GEN.DELETE_LAYER(fill_layer)
        self.GEN.VON()

    def Check_SR(self):
        """
        检测flat_layer中的surface,两两之间不能相互touch
        :param layers:
        :return:
        """
        flat_layer = self.flat_layer
        close_sr = self.close_sr
        self.GEN.VOF()
        self.GEN.DELETE_LAYER(close_sr)
        self.GEN.CREATE_LAYER(close_sr)
        self.GEN.VON()
        self.GEN.OPEN_STEP(self.step_name)
        # DO_INFO获取surface的index,因为可能有多块金手指对应的防焊开窗，所以要迭代处理
        info = self.GEN.INFO( '-t layer -e %s/%s/%s -m script -d FEATURES -o feat_index' % (self.jobName, self.step_name, flat_layer))
        # 只检测edit,set,zk等step,因为其它step经常间距不足1mm
        indexRegex = re.compile(r'^#\d+\s+#S P 0;.pattern_fill,.string=(set(?:.+)?|edit(?:.+)?|zk)')
        for line in info:
            if re.match(indexRegex, line):
                index = line.strip().split()[0].strip('#')
                # 通过index选出物件到close_sr层
                self.GEN.WORK_LAYER(flat_layer)
                self.GEN.VOF()
                self.GEN.COM('sel_layer_feat,operation=select,layer=%s,index=%s' % (flat_layer, index))
                self.GEN.VON()
                count = self.GEN.GET_SELECT_COUNT()
                if count > 0:
                    # 工作层和ref层均为flat_layer，注意use=select
                    self.GEN.COM( 'sel_ref_feat,layers=,use=select,mode=cover,pads_as=shape,f_types=surface,polarity=positive,include_syms=,exclude_syms=')
                    count = self.GEN.GET_SELECT_COUNT()
                    if count > 0:
                        self.GEN.SEL_DELETE()
                    # 再次通过index选出物件到close_sr层
                    self.GEN.VOF()
                    self.GEN.COM('sel_layer_feat,operation=select,layer=%s,index=%s' % (flat_layer, index))
                    self.GEN.VON()
                    self.GEN.COM( 'sel_ref_feat,layers=,use=select,mode=touch,pads_as=shape,f_types=surface,polarity=positive,include_syms=,exclude_syms=')
                    count = self.GEN.GET_SELECT_COUNT()
                    if count > 0:
                        # 与当前index开窗连在一起的，move到blue_cham层
                        self.GEN.SEL_MOVE(close_sr)
                        # 与挑选出去的物件相连接的物件copy到blue_cham层
                        self.GEN.SEL_REF_FEAT(close_sr, 'touch')
                        count = self.GEN.GET_SELECT_COUNT()
                        if count > 0:
                            self.GEN.SEL_MOVE(close_sr)
        self.GEN.DELETE_LAYER(flat_layer)
        infoDict = self.GEN.DO_INFO('-t layer -e %s/%s/close_sr -m script -d FEAT_HIST -p total' % (self.jobName,self.step_name))
        if int(infoDict['gFEAT_HISTtotal']) > 0:
            self.GEN.COM('save_job,job=%s,override=no' % self.jobName)
            if self.show_mess == 'yes':
                msg_box = msgBox()
                msg_box.critical(None, '检测子排版间距', '间距不足%s mm,请查看close_sr层！' %  self.check_dist , QMessageBox.Ok)
            else:
                self.check_result = 'Warning'
                # 写文件
                fo = open (self.check_result_log, "w")
                fo.write ("Warning\n间距不足%s mm,请查看close_sr层！\n" %  self.check_dist)
                # 关闭打开的文件
                fo.close ()
            # raise SystemExit
            sys.exit(-1)
        else:
            self.GEN.DELETE_LAYER(close_sr)
            # self.GEN.COM('save_job,job=%s,override=no' % self.jobName)

            if self.show_mess != 'yes':
                # 写文件
                fo = open (self.check_result_log, "w")
                fo.write ("OK\n 检测子排版间距完成 \n")
                # 关闭打开的文件
                fo.close ()

if __name__ == '__main__':
    # 必须实例化app,不则警告信息无法弹出
    app = QtGui.QApplication(sys.argv)
    try:
        show_mess = sys.argv[1]
    except IndexError:
        show_mess = 'yes'

    # 实例化panel
    panel_step = current_step('panel',show_result=show_mess)
    # 执行实例panel的run函数
    panel_step.run()
