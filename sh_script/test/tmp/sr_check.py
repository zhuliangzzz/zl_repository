#/usr/bin/env python
# -*- coding:utf8 -*-
import os,sys,platform
# --加载相对位置，以实现InCAM与Genesis共用
if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
from collections import defaultdict
import genCOM_26 as genCOM
from messageBox import msgBox
from PyQt4.QtGui import QMessageBox
from PyQt4 import QtCore, QtGui
from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import *
from PyQt4.QtCore import *

class current_step(object):
    """
    当前step定义为一个类，类里面需要执行的方法封装如下
    """
    def __init__(self,step_name,parent=None):
        # 从环境变量中获取料号名
        self.jobName = os.environ.get('JOB', None)
        self.GEN = genCOM.GEN_COM()
        self.step_name = step_name
        self.error_layer = []
        self.clear_layer = []
        self.SR = self.Get_SR()
        self.fill_layer = '%s_fill' % self.step_name
        self.limit_layer = '%s_limit' % self.step_name

    def Get_SR(self,step=None):
        """
        通过DO_INFO获取子排版
        :return:
        """
        sr_list = []
        if not step:
            info = self.GEN.DO_INFO('-t step -e %s/%s -m script -d SR' % (self.jobName,self.step_name))
        else:
            info = self.GEN.DO_INFO('-t step -e %s/%s -m script -d SR' % (self.jobName,step))
        for step in info['gSRstep']:
            if step not in sr_list:
                sr_list.append(step)
        return sr_list

    def Get_Panel_SR(self):
        """
        获取panel中所有step
        :return:
        :rtype:
        """

    def __del__(self):
        self.GEN.VOF()
        # self.GEN.DELETE_LAYER(self.fill_layer)
        # self.GEN.DELETE_LAYER(self.limit_layer)
        self.GEN.VON()

    def Fill_SR(self,layers):
        """
        填充子排版，通过将sr_margin_x设为-2540,sr_margin_y设为-2540,可以实现
        :param sr_list:
        :return:
        """
        fill_layer = self.fill_layer
        src_layer = 'sr_fill'
        self.GEN.OPEN_STEP(self.step_name)
        self.GEN.CHANGE_UNITS('mm')
        self.GEN.DELETE_LAYER(fill_layer)
        self.GEN.VOF()
        self.GEN.CREATE_LAYER(fill_layer)
        self.GEN.VON()
        step_margin_x = 0
        step_margin_y = 0
        self.GEN.DELETE_LAYER(src_layer)
        self.GEN.VOF()
        self.GEN.CREATE_LAYER(src_layer)
        self.GEN.VON()
        for step in self.SR:
            if step not in ['drl','lp','2nd','fafa','szlp','fa']:
                self.GEN.OPEN_STEP(step)
                # --新增重置筛选器 2021.1.18
                self.GEN.COM('filter_reset,filter_name=popup')
                self.GEN.CHANGE_UNITS('mm')
                max_dist_x = 0
                max_dist_y = 0
                margin_x = -2540
                margin_y = -2540
                self.GEN.WORK_LAYER(src_layer)
                # --将fill参数重置初始化，不重置可能造成sr_fill时不是整块铜皮。 AresHe 2021.3.5
                self.GEN.COM('fill_params,type=solid,origin_type=datum,solid_type=surface')
                self.GEN.COM('sr_fill,polarity=%s,step_margin_x=%s,step_margin_y=%s,step_max_dist_x=%s,step_max_dist_y=%s,'
                             'sr_margin_x=%s,sr_margin_y=%s,sr_max_dist_x=%s,sr_max_dist_y=%s,nest_sr=no,stop_at_steps=,'
                             'consider_feat=no,consider_drill=no,consider_rout=no,dest=affected_layers,attributes=no'
                    % ('positive', step_margin_x, step_margin_y, 2540, 2540, margin_x, margin_y, max_dist_x, max_dist_y))
                # --单边加大2mm并copy到limit_layer,确认所有feature不超出profile 2mm  20210113刘文东要求更改到1.5mm
                # --单边加大0.3mm 黄小春 2021.8.9
                limit_layer = '%s_limit' % step
                self.GEN.SEL_COPY(limit_layer, size=600)
                # --TODO 可能有分板线、vcut孔等加在set边,同时会进入edit,此是常规做法，故将fill_layer内缩20mil
                self.GEN.COM('sel_resize,size=-508,corner_ctl=no')

                # --TODO 每个子排版执行检测，查看内容物是否超出profile 2mm
                out_limit_lyrs = []
                for layer in layers:
                    # -- Check_Board_LIMITS会返回bool值,超出2mm为真
                    out_of_limit = self.Check_Board_LIMITS(step, layer)
                    if out_of_limit:
                        chk_limit = '%s_%s_out2mm' % (step, layer)
                        out_limit_lyrs.append(chk_limit)
                if len(out_limit_lyrs) > 0:
                    if step not in error_info['out_of_limits']:
                        error_info['out_of_limits'][step] = ','.join(out_limit_lyrs)
                        clear_layers.extend(out_limit_lyrs)
                        clear_layers.append(limit_layer)
                else:
                    # --TODO 清除%s_limit辅助层
                    self.GEN.DELETE_LAYER(limit_layer)

                self.GEN.CLEAR_LAYER()
                self.GEN.CLOSE_STEP()
        # --如果子排版中还有子排版，将src_layer flatten出来
        self.GEN.OPEN_STEP(self.step_name)
        self.GEN.COM('flatten_layer,source_layer=%s,target_layer=%s' % (src_layer,fill_layer))
        self.GEN.DELETE_LAYER(src_layer)

    def Get_Board_Layer(self):
        """
        获取当前料号的board层别，只在panel step中执行一次
        enumerate :产出由两个元素组成的元组，结构是(index, item)，其中 index 从start 开始计数，item 则从iterable 中获取
        :return:
        """
        board_layer = []
        m_info = self.GEN.DO_INFO('-t matrix -e %s/matrix' % self.jobName)
        for i,name in enumerate(m_info['gROWname']):
            layer_type = m_info['gROWlayer_type'][i]
            context = m_info['gROWcontext'][i]
            side = m_info['gROWside'][i]
            if context == 'board':
                if layer_type in ['signal','power_ground','solder_mask','silk_screen','drill']:
                    board_layer.append(name)
                elif layer_type == 'solder_paste' and name in ['md1','md2']:
                    board_layer.append(name)
        return board_layer

    def Check_Board_LIMITS(self,step,layer):
        """
        检测当前step的feature有没有超出profile 2mm
        :param layer:
        :type layer:
        :return: True or False
        :rtype: bool
        """
        limit_layer = '%s_limit' % step
        self.GEN.WORK_LAYER(layer)
        if self.GEN.LAYER_EXISTS(limit_layer,job=self.jobName,step=step) == 'yes':
            self.GEN.SEL_REF_FEAT(limit_layer, 'cover')
            self.GEN.SEL_REVERSE()

            # --跟刘文东确认不筛选num_250 symbol（这个指定num_250 symbol touch以及cover失效）  AresHe 2021.1.19
            self.GEN.COM('filter_reset,filter_name=popup')
            self.GEN.COM('filter_set,filter_name=popup,update_popup=no,include_syms=num_250')
            self.GEN.COM('filter_area_strt')
            self.GEN.COM('filter_area_end,layer=,filter_name=popup,operation=unselect,area_type=none,inside_area=no,intersect_area=no')
            self.GEN.COM('filter_reset,filter_name=popup')
            count = self.GEN.GET_SELECT_COUNT()
            if count > 0:
                chk_limit = '%s_%s_out2mm' % (step, layer)
                self.GEN.DELETE_LAYER(chk_limit)
                self.GEN.SEL_COPY(chk_limit)
                self.GEN.WORK_LAYER(chk_limit)
                return True
        return False

    def Check_Board_Layer(self,layers):
        """
        检测当前step中的所有board层,不能touch到fill_layer
        :param layers:
        :return:
        """
        fill_layer = self.fill_layer
        self.Fill_SR(layers)
        # --TODO 检测当前step中，有没有内容物接触到子排版
        self.GEN.OPEN_STEP(self.step_name)

        # --刘文东需求取消监控内容物件入单元内，详见需求:http://192.168.2.120:82/zentao/story-view-2558.html
        '''
        for layer in layers:
            self.GEN.WORK_LAYER(layer)
            self.GEN.FILTER_RESET()
            self.GEN.SEL_REF_FEAT(fill_layer,'touch')
            if self.GEN.GET_SELECT_COUNT() > 0:
                chk_layer = '%s_%s_in_sr' % (self.step_name,layer)
                self.GEN.DELETE_LAYER(chk_layer)
                self.GEN.SEL_COPY(chk_layer)
                self.GEN.WORK_LAYER(chk_layer)
                # --TODO 排除防焊vcut线,参考料号815/f18
                if layer in ['m1','m2']:
                    if self.GEN.LAYER_EXISTS('vcut', job=self.jobName, step=self.step_name) == 'yes':
                        self.GEN.SEL_REF_FEAT('vcut','cover')
                        if self.GEN.GET_SELECT_COUNT() > 0:
                            self.GEN.SEL_DELETE()
                # --TODO 排除邮票孔，参考料号715/264a1
                self.GEN.SEL_REF_FEAT('drl', 'include')
                if self.GEN.GET_SELECT_COUNT() > 0:
                    self.GEN.SEL_DELETE()
                # --TODO 排除pcs序号，参考料号715/264a1
                self.GEN.FILTER_SET_FEAT_TYPES('text')
                self.GEN.FILTER_SELECT()
                count = self.GEN.GET_SELECT_COUNT()
                if count > 0:
                    self.GEN.SEL_DELETE()
                # --检查是否有内容物
                self.GEN.FILTER_RESET()
                self.GEN.FILTER_SELECT()
                count = self.GEN.GET_SELECT_COUNT()
                if count > 0:
                    self.error_layer.append(chk_layer)
                else:
                    self.GEN.DELETE_LAYER(chk_layer)
        '''
        if len(self.error_layer) > 0:
            if self.step_name not in error_info:
                error_info['in_srs'][self.step_name] = ','.join(self.error_layer)
                self.GEN.COM('negative_data,mode=dim')
                clear_layers.extend(self.error_layer)
                clear_layers.append(self.fill_layer)
        else:
            self.GEN.DELETE_LAYER(self.fill_layer)
            self.GEN.CLEAR_LAYER()
            self.GEN.CLOSE_STEP()

    def Recursive(self,layers):
        """
        递归函数，若有子排版，则递归调用
        :param layers:
        :return:
        """
        if self.SR:
            print self.SR
            self.Check_Board_Layer(layers)
            for step in self.SR:
               sr_step = current_step(step)
               if sr_step.SR:
                   sr_step.Check_Board_Layer(layers)

    def save_job_in_out(self):
        """
        check_out后保存料号,并且check_in
        :return:
        :rtype:
        """
        self.GEN.VOF()
        self.GEN.COM('check_inout,mode=test,type=job,job=%s' % self.jobName)
        check_info = self.GEN.COMANS
        check_status = check_info.split()[0]
        # --保证料号上锁状态，不把上锁的料号解锁
        if check_status == 'yes':
            self.GEN.COM('save_job,job=%s,override=no' % self.jobName)
        else:
            self.GEN.COM('check_inout,mode=out,type=job,job=%s' % self.jobName)
            self.GEN.COM('save_job,job=%s,override=no' % self.jobName)
            self.GEN.COM('check_inout,mode=in,type=job,job=%s' % self.jobName)
        self.GEN.VON()

    def test_panel(self):
        """
        点击test时要求输入解锁密码,初始密码为1234
        :return:
        :rtype:
        """
        inputDialog = QInputDialog(None)
        inputDialog.setOkButtonText(u'解锁')
        inputDialog.setCancelButtonText(u'退出')
        inputDialog.setLabelText(u'请输入解锁密码:')
        inputDialog.setWindowTitle(u'输入密码解锁')
        inputDialog.setTextEchoMode(QLineEdit.Password)
        if inputDialog.exec_():
            # --如果点击了ok按钮
            text = inputDialog.textValue()
            if text != 'sh-incam':
                self.Message(u'输入密码不正确,请重新输入!')
                self.test_panel()
            else:
                # --密码输入正确，继续运行
                return 1
            # else:
            #     # --密码输入正确，与正式一样运行
            #     self.testButton_clicked = True
            #     self.clickApply()

    def Message(self, text):
        """
        Msg窗口
        :param text: 显示的内容
        :return:None
        """
        # 警告信息提示框
        message = QtGui.QMessageBox.warning(None, u'提示信息!', text, QtGui.QMessageBox.Ok)

    def pause_check(self):
        self.GEN.OPEN_STEP(self.step_name)
        self.GEN.PAUSE('Please check ...')

if __name__ == '__main__':
    # 必须实例化app,不则警告信息无法弹出
    app = QtGui.QApplication(sys.argv)
    # 初始化error_step和error_layer
    error_info = defaultdict(dict)
    clear_layers = []
    # 实例化panel
    panel_step = current_step('panel')
    # 通过实例panel的函数获取需要检测的board层别
    boards = panel_step.Get_Board_Layer()
    print boards
    # 执行实例panel的递归函数
    panel_step.Recursive(boards)
    # --如果父排版的feature进入到子排版，提示如下
    if error_info.has_key('in_srs'):
        msg_box = msgBox()
        ret = msg_box.question(None, '添加的feature进入子排版中' , '具体请参考以下xx_in_sr及xx_fill的层别!\n', QMessageBox.Yes)
        # if ret == 1:
        #     # --退出前先保存料号，防止人员再次运行输出gerber时报错料号未保存
        #     panel_step.GEN.OPEN_STEP(panel_step.step_name)
        #     panel_step.GEN.COM('display_sr,display=yes')
        #     panel_step.GEN.COM('save_job,job=%s,override=no' % panel_step.jobName)
        #     sys.exit(1)
        # else:
        #     # --验证密码是否放行
        #     check_info = panel_step.test_panel()
        #     if  check_info == 1:
        #         # --若继续，清除临时层别
        #         for layer in clear_layers:
        #             if layer.endswith('_in_sr') or layer.endswith('_fill'):
        #                 panel_step.GEN.DELETE_LAYER(layer)
        #     else:
        #         # --退出前先保存料号，防止人员再次运行输出gerber时报错料号未保存
        #         panel_step.GEN.OPEN_STEP(panel_step.step_name)
        #         panel_step.GEN.COM('display_sr,display=yes')
        #         panel_step.GEN.COM('save_job,job=%s,override=no' % panel_step.jobName)
        #         # -->验证失败，退出程序
        #         sys.exit(1)

    # --如果子排版的feature超出profile 2mm以上，提示如下
    if error_info.has_key('out_of_limits'):
        msg_box = msgBox()
        ret = msg_box.question(None, 'step中的内容物超出profile 2mm', '具体请参考以下xx_out1.5mm及xx_limit的层别!', QMessageBox.Yes)
        # if ret == 1:
        #     # --退出前先保存料号，防止人员再次运行输出gerber时报错料号未保存
        #     panel_step.GEN.OPEN_STEP(panel_step.step_name)
        #     panel_step.GEN.COM('display_sr,display=yes')
        #     # panel_step.GEN.COM('save_job,job=%s,override=no' % panel_step.jobName)
        #     panel_step.save_job_in_out()
        #     sys.exit(1)
        # else:
        #     # --新增pause暂停检查项
        #     panel_step.pause_check()
        #     # --验证密码是否放行
        #     check_info = panel_step.test_panel()
        #     if check_info == 1:
        #         # --若继续，清除临时层别
        #         for layer in clear_layers:
        #             if layer.endswith('_out2mm') or layer.endswith('_limit'):
        #                 panel_step.GEN.DELETE_LAYER(layer)
        #     else:
        #         # --退出前先保存料号，防止人员再次运行输出gerber时报错料号未保存
        #         panel_step.GEN.OPEN_STEP(panel_step.step_name)
        #         panel_step.GEN.COM('display_sr,display=yes')
        #         # panel_step.GEN.COM('save_job,job=%s,override=no' % panel_step.jobName)
        #         panel_step.save_job_in_out()
        #         # -->验证失败，退出程序
        #         sys.exit(1)
    # --检测无问题或者强行输出前保存料号
    # panel_step.GEN.COM('save_job,job=%s,override=no' % panel_step.jobName)
    # panel_step.save_job_in_out()
    panel_step.Message(u'检查完成!!!')
    sys.exit(0)