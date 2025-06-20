#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --加载相对位置，以实现InCAM与Genesis共用

import platform,sys,pprint
if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

from PyQt4 import QtCore, QtGui
import re,math,os,math
import genCOM_26 as genCOM

#设置编码函数
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

#设置解码函数
try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class MAIN:
    def __init__(self):
        self.job_name = os.environ.get('JOB', None)
        #接口定义
        self.GEN = genCOM.GEN_COM()
        #正则表达式定义
        self.laser_reg = re.compile(r's[0-9]{2,4}$|s[0-9]{1,2}-[0-9]{1,2}$')
        self.burid_reg = re.compile(r'b[1-9]{2,4}$|b[0-9]{1,2}-[0-9]{1,2}$')
        #层数定义
        self.layer_num = int(self.job_name[4:6])
        #判断边片是否存在
        self.set_exists = self.GEN.STEP_EXISTS('set')
        if self.set_exists:
            self.set_step = 'set'
        else:
            self.set_step = 'edit'
        #定义板内step名
        self.pcs_step = 'edit'
        self.net_step = 'net'
        #获取相关信息
        #self.outer_layers = self.GEN.GET_ATTR_LAYER('outer')
        #self.inner_layers = self.GEN.GET_ATTR_LAYER('inner')
        self.mask_layers  = self.GEN.GET_ATTR_LAYER('solder_mask')
        self.etch_layers  = self.get_etch_layer()
        self.laser_layers = self.get_laser_layers()
        self.top_lasers,self.bot_lasers = self.get_top_bot_laser()
        # --调用程序
        self.runMain()

    def runMain(self):
        self.check_layer_name(self.laser_layers)
        self.create_coupon()

    def get_laser_layers(self):
        #获取钻带名称列表
        laser_layers = []
        drill_layers = self.GEN.GET_ATTR_LAYER('drill')
        for layer in drill_layers:
            if self.laser_reg.match(layer):
                min_laser = self.get_min_laser(layer)
                if len(min_laser) > 0:
                    laser_layers.append(layer)
        return laser_layers

    def get_top_bot_laser(self):
        #将镭射层区分顶部和底部
        top_laser = []
        bot_laser = []
        drill_layers = self.GEN.GET_ATTR_LAYER('drill')
        for layer in self.laser_layers:
            start,end = self.get_drill_through(layer)
            digt_s = start[1:]
            digt_e = end[1:]
            max_digt = max([int(digt_s),int(digt_e)])
            if max_digt > self.layer_num/2:
                bot_laser.append(layer)
            else:
                top_laser.append(layer)
        return top_laser,bot_laser

    def check_layer_name(self,layers):
        #检查镭射命名
        errorMsg = u""
        for layer in layers:
            start,end = self.get_drill_through(layer)
            start_digt = start[1:]
            end_digt = end[1:]
            if '-' in layer:
                #层名中间带"-"的情况
                digt_s = re.split(r'[s,b,bd,-]',layer)[-2]
                digt_e = re.split(r'[s,b,bd,-]',layer)[-1]
            else:
                #层名中间不带"-"的情况
                digts = re.split(r'[s,b,bd,-]',layer)[-1]
                if len(digts) == 2:
                    digt_s = digts[0]
                    digt_e = digts[1]
                elif len(digts) == 3:
                    #s109默认按正确的层别名，先取两码再取一码
                    digt_s = digts[:2]
                    digt_e = digts[2:]
                    if math.fabs(int(digt_s)-int(digt_e)) > 2 and self.laser_reg.match(layer):
                        #若相差过大，可能是旧的命名方式，先取一码再取两码，如s910,埋孔则不必
                        digt_s = digts[:1]
                        digt_s = digts[1:]
                else:
                    digt_s = digts[:2]
                    digt_e = digts[2:]
            max_digt = max([int(digt_s),int(digt_e)])
            if max_digt > self.layer_num/2:
                if int(digt_s) < int(digt_e):
                    errorMsg += u"%s 层钻带名命名不标准(起始层错误)，请按最新标准命名！\n" % layer
            if digt_s != start_digt or digt_e != end_digt:
                errorMsg += u"%s 层，请检查钻带方向！\n" % layer
        #当有收集到错误信息时
        if errorMsg != '':
            self.Message('%s' % errorMsg,sel=0)
            sys.exit(0)

    def get_drill_through(self, layer, job=os.environ.get('JOB', None), step=os.environ.get('STEP', None)):
        """返回起始层信息与终止层信息"""
        start = self.GEN.DO_INFO('-t layer -e %s/%s/%s -d DRL_START' % (job, step, layer))
        end = self.GEN.DO_INFO('-t layer -e %s/%s/%s -d DRL_END' % (job, step, layer))
        """防止C面镭射或S面镭射拉错孔带，拉到防焊或者其它非蚀刻层"""
        start_info = self.GEN.DO_INFO('-t layer -e %s/%s/%s -d SIDE' % (job, step, start['gDRL_START']))
        end_info = self.GEN.DO_INFO('-t layer -e %s/%s/%s -d SIDE' % (job, step, end['gDRL_END']))
        start_side = start_info['gSIDE']
        end_side = end_info['gSIDE']
        """顶层钻带校正"""
        if start_side == 'top':
            start_layer = 'l1'
        elif start_side == 'bottom':
            start_layer = 'l' + str(self.layer_num)
        else:
            start_layer = start['gDRL_START']
        """底层钻带校正"""
        if end_side == 'top':
            end_layer = 'l1'
        elif end_side == 'bottom':
            end_layer = 'l' + str(self.layer_num)
        else:
            end_layer = end['gDRL_END']
        # --返回两个值
        return start_layer,end_layer

    def get_plus(self):
        #根据正反面镭射定义HDI阶数
        plus = 0
        if len(self.top_lasers) >= len(self.bot_lasers):
            plus = len(self.top_lasers)
        else:
            plus = len(self.bot_lasers)
        return plus

    def get_etch_layer(self):
        #获取蚀刻层列表
        etch_layer = []
        for x,y in enumerate(xrange(self.layer_num),1):
            etch_layer.append("l"+str(x))
        return etch_layer

    def get_dest_lasers(self,nPlus):
        #获取镭射源层别和目标层别列表
        top_src_lasers = []
        bot_src_lasers = []
        top_dst_lasers = []
        bot_dst_lasers = []
        layer_num = self.layer_num

        for plus,idx in enumerate(xrange(nPlus),1):
            top_laser_old = 's%s%s' % (plus,plus+1)
            top_laser_new = 's%s-%s' % (plus,plus+1)
            top_src_lasers.append(top_laser_new)
            if top_laser_new in self.top_lasers:
                top_dst_lasers.append(top_laser_new)
            else:
                if top_laser_old in self.top_lasers:
                    top_dst_lasers.append(top_laser_old)
            #起始层别必须比结束层别大(层别命名新规则，旧规则在前面界面处已经设置防呆了)
            bot_laser_old = 's%s%s' % (layer_num+1-plus,layer_num-plus)
            bot_laser_new = 's%s-%s' % (layer_num+1-plus,layer_num-plus)
            bot_src_lasers.append(top_laser_new)
            if bot_laser_new in self.bot_lasers:
                bot_dst_lasers.append(bot_laser_new)
            else:
                if bot_laser_old in self.bot_lasers:
                    bot_dst_lasers.append(bot_laser_old)
        return top_src_lasers,bot_src_lasers,top_dst_lasers,bot_dst_lasers

    def get_min_laser(self,layer):
        info = self.GEN.DO_INFO("-t layer -e %s/%s/%s -d TOOL -p drill_size+type -o break_sr" %
                            (self.job_name, self.pcs_step, layer))
        if len(info['gTOOLdrill_size']) != 0:
            #只选pth孔
            pth_tool = []
            for i in range(len(info['gTOOLdrill_size'])):
                if info['gTOOLtype'][i] in ['via','plated']:
                    pth_tool.append(info['gTOOLdrill_size'][i])
            if len(pth_tool):
                #按孔径大小取最小值，而不是按str格式取最小值
                mintool = min(pth_tool,key=lambda x : float(x))
            else:
                mintool = ''
        else:
            mintool = ''
        return mintool

    def copy_lasers(self,src_coupon,src_lasers,dst_lasers):
        #从genesislib中copy镭射层并change sym
        for src_laser,dst_laser in zip(src_lasers,dst_lasers):
            self.GEN.COM('copy_layer_from_lib,source_layer=%s,source_step=%s,profile=none,dest=layer_name,dest_layer=%s,mode=replace,invert=no' % (src_laser,src_coupon,dst_laser))
            self.GEN.AFFECTED_LAYER(dst_laser,'yes')
            min_laser = self.get_min_laser(dst_laser)
            self.GEN.SEL_CHANEG_SYM("r"+str(min_laser))
            self.GEN.AFFECTED_LAYER(dst_laser,'no')

    def copy_layers(self,src_coupon,src_layers,dst_layers):
        #从genesislib中copy信号层并变更ring环
        for src_layer,dst_layer in zip(src_layers,dst_layers):
            self.GEN.COM('copy_layer_from_lib,source_layer=%s,source_step=%s,profile=none,dest=layer_name,dest_layer=%s,mode=replace,invert=no' % (src_layer,src_coupon,dst_layer))

    def copy_fill_layers(self,src_coupon,dst_layers,src_layer):
        #空层从plus-hct l4层copy
        for layer in self.etch_layers + self.mask_layers:
            if layer not in dst_layers:
                self.GEN.COM('copy_layer_from_lib,source_layer=%s,source_step=%s,profile=none,dest=layer_name,dest_layer=%s,mode=replace,invert=no' % (src_layer,src_coupon,layer))

    def create_coupon(self):
        #定义镭射hct模块名称
        nPlus = self.get_plus()
        print nPlus
        coupon_list = []
        if len(self.etch_layers) == 4 and nPlus == 1:
            coupon_top = "plus%s-hct-top" % nPlus
            coupon_bot = "plus%s-hct-bot" % nPlus
            coupon_list.append(coupon_top)
            coupon_list.append(coupon_bot)
        elif len(self.etch_layers) == 6 and nPlus == 2:
            coupon_top = "plus%s-hct-top" % nPlus
            coupon_bot = "plus%s-hct-bot" % nPlus
            coupon_list.append(coupon_top)
            coupon_list.append(coupon_bot)
        elif len(self.etch_layers) == 8 and nPlus == 3:
            coupon_top = "plus%s-hct-top" % nPlus
            coupon_bot = "plus%s-hct-bot" % nPlus
            coupon_list.append(coupon_top)
            coupon_list.append(coupon_bot)
        elif len(self.etch_layers) == 10 and nPlus == 4:
            coupon_top = "plus%s-hct-top" % nPlus
            coupon_bot = "plus%s-hct-bot" % nPlus
            coupon_list.append(coupon_top)
            coupon_list.append(coupon_bot)
        else:
            coupon = "plus%s-hct" % nPlus
            coupon_list.append(coupon)
        #定义profile大小
        if nPlus == 0:
            errorMsg = u'没有镭射孔，不需要hct模块!'
            self.Message('%s' % errorMsg,sel=0)
            sys.exit(0)
        elif nPlus == 1:
            prof_xmax = 21.256407
            prof_ymax = 1.906405
        elif nPlus == 2:
            prof_xmax = 24.376405
            prof_ymax = 2.836460
        elif nPlus == 3:
            prof_xmax = 34.776412
            prof_ymax = 2.836460
        elif nPlus == 4:
            prof_xmax = 28.394625
            prof_ymax = 4.506435
        else:
            errorMsg = u'五阶hct模块正在开发中，请联系管理员!'
            self.Message('%s' % errorMsg,sel=0)
            sys.exit(0)
        for coupon in coupon_list:
            #创建step
            self.GEN.VOF()
            self.GEN.DELETE_ENTITY('step',coupon)
            self.GEN.CREATE_ENTITY('', job=self.job_name, step=coupon)
            self.GEN.OPEN_STEP(coupon, job=self.job_name)
            self.GEN.CHANGE_UNITS ('mm')
            self.GEN.VON()
            self.GEN.COM('profile_rect,x1=0,y1=0,x2=%s,y2=%s' % (prof_xmax,prof_ymax))
            self.copy_coupon_from_lib(nPlus,coupon)

    def copy_coupon_from_lib(self,plus,coupon):
        #从genesislib中copy
        top_src_coupon = "plus%s-hct" % plus
        bot_src_coupon = "plus%s-hct" % plus
        top_src_layers = ['m1']
        top_dst_layers = ['m1']
        top_dst_lasers = []
        bot_dst_lasers = []
        if plus == 1:
            #一阶时定义源层别和目标层
            if len(self.top_lasers) >= 1:
                top_src_layers.extend(self.etch_layers[:3])
                top_dst_layers.extend(self.etch_layers[:3])
            if len(self.bot_lasers) >= 1:
                bot_src_layers = list(reversed(self.etch_layers[:3])) + ['m2']
                bot_dst_layers = self.etch_layers[-3:] + ['m2']
            else:
                bot_src_layers = ['m2']
                bot_dst_layers = ['m2']
            fill_layer = 'l4'
        elif plus == 2:
            #二阶时定义源层别和目标层
            if len(self.top_lasers) >= 2:
                top_src_layers.extend(self.etch_layers[:4])
                top_dst_layers.extend(self.etch_layers[:4])
            elif len(self.top_lasers) >= 1:
                top_src_layers.extend(self.etch_layers[:3])
                top_dst_layers.extend(self.etch_layers[:3])
            if len(self.bot_lasers) >= 2:
                bot_src_layers = list(reversed(self.etch_layers[:4])) + ['m2']
                bot_dst_layers = self.etch_layers[-4:] + ['m2']
            elif len(self.bot_lasers) >= 1:
                bot_src_layers = list(reversed(self.etch_layers[:3])) + ['m2']
                bot_dst_layers = self.etch_layers[-3:] + ['m2']
            fill_layer = 'l5'
        elif plus == 3:
            #三阶时定义源层别和目标层
            if len(self.top_lasers) >= 3:
                top_src_layers.extend(self.etch_layers[:5])
                top_dst_layers.extend(self.etch_layers[:5])
            elif len(self.top_lasers) >= 2:
                top_src_layers.extend(self.etch_layers[:4])
                top_dst_layers.extend(self.etch_layers[:4])
            elif len(self.top_lasers) >= 1:
                top_src_layers.extend(self.etch_layers[:3])
                top_dst_layers.extend(self.etch_layers[:3])
            if len(self.bot_lasers) >= 3:
                bot_src_layers = list(reversed(self.etch_layers[:5])) + ['m2']
                bot_dst_layers = self.etch_layers[-5:] + ['m2']
            elif len(self.bot_lasers) >= 2:
                bot_src_layers = list(reversed(self.etch_layers[:4])) + ['m2']
                bot_dst_layers = self.etch_layers[-4:] + ['m2']
            elif len(self.bot_lasers) >= 1:
                bot_src_layers = list(reversed(self.etch_layers[:3])) + ['m2']
                bot_dst_layers = self.etch_layers[-3:] + ['m2']
            fill_layer = 'l6'
        elif plus == 4:
            #三阶时定义源层别和目标层
            if len(self.top_lasers) >= 4:
                top_src_layers.extend(self.etch_layers[:6])
                top_dst_layers.extend(self.etch_layers[:6])
            elif len(self.top_lasers) >= 3:
                top_src_layers.extend(self.etch_layers[:5])
                top_dst_layers.extend(self.etch_layers[:5])
            elif len(self.top_lasers) >= 2:
                top_src_layers.extend(self.etch_layers[:4])
                top_dst_layers.extend(self.etch_layers[:4])
            elif len(self.top_lasers) >= 1:
                top_src_layers.extend(self.etch_layers[:3])
                top_dst_layers.extend(self.etch_layers[:3])
            if len(self.bot_lasers) >= 4:
                bot_src_layers = list(reversed(self.etch_layers[:6])) + ['m2']
                bot_dst_layers = self.etch_layers[-6:] + ['m2']
            elif len(self.bot_lasers) >= 3:
                bot_src_layers = list(reversed(self.etch_layers[:5])) + ['m2']
                bot_dst_layers = self.etch_layers[-5:] + ['m2']
            elif len(self.bot_lasers) >= 2:
                bot_src_layers = list(reversed(self.etch_layers[:4])) + ['m2']
                bot_dst_layers = self.etch_layers[-4:] + ['m2']
            elif len(self.bot_lasers) >= 1:
                bot_src_layers = list(reversed(self.etch_layers[:3])) + ['m2']
                bot_dst_layers = self.etch_layers[-3:] + ['m2']
            fill_layer = 'l7'
        #通过get_dest_lasers方法获取源层和目标层
        top_src_lasers,bot_src_lasers,top_dst_lasers,bot_dst_lasers = self.get_dest_lasers(plus)
        self.GEN.CLEAR_LAYER()
        if coupon.endswith('-top') or coupon.endswith('-hct') :
            self.copy_layers(top_src_coupon,top_src_layers,top_dst_layers)
            if not coupon.endswith('-hct'):
                #一个模块时，copy顶部时，底部不能用fill_layer填充
                self.copy_fill_layers(top_src_coupon,top_dst_layers,fill_layer)
            self.copy_lasers(top_src_coupon,top_src_lasers,top_dst_lasers)
        if coupon.endswith('-bot') or coupon.endswith('-hct') :
            self.copy_layers(bot_src_coupon,bot_src_layers,bot_dst_layers)
            if not coupon.endswith('-hct'):
                #一个模块时，copy底部时，顶部不能用fill_layer填充
                self.copy_fill_layers(bot_src_coupon,bot_dst_layers,fill_layer)
            self.copy_lasers(bot_src_coupon,bot_src_lasers,bot_dst_lasers)
        if coupon.endswith('-hct'):
            #一个模块时，中间层别用fill_layer填充
            self.copy_fill_layers(bot_src_coupon,top_dst_layers+bot_dst_layers,fill_layer)

    def Message(self, text,sel=1):
        message = QtGui.QMessageBox()
        message.setText(text)
        if sel != 1:
            message.addButton(u"OK", QtGui.QMessageBox.AcceptRole)
        if sel == 1:
            message.addButton(u"是", QtGui.QMessageBox.AcceptRole)
            message.addButton(u"否", QtGui.QMessageBox.RejectRole)
        message.exec_()
        return message.clickedButton().text()

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    #Form = QtGui.QWidget()
    main = MAIN()
    #sys.exit(app.exec_())
