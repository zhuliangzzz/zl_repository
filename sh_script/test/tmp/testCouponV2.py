# -*- coding: utf-8 -*-
# --加载相对位置，以实现InCAM与Genesis共用
import platform
import sys

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
    # sys.path.append(r"D:/genesis/sys/scripts/Package")

else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

import genCOM_26 as genCOM
from PyQt4 import QtCore, QtGui
import re
import os
import json
import csv
import testcouponV as Ui
from PyQt4 import QtCore, QtGui
from PyQt4.QtGui import *

# --导入同级目录下的添加“对准度防漏接Coupon设计标准”模块方法
import dzd_testCoupon as dzdCoupon

import flj_testcoupon as fljCoupon
from flj_testcoupon import check_car_type, check_battery_type

if check_car_type or check_battery_type:
    max_laser_ar = 10
else:
    # 周涌通知全部改为10为上限
    max_laser_ar = 10

import add_qie_hole_new as addQieHoleCoupon

from genesisPackages import  getSmallestHole_and_step
     
GEN = genCOM.GEN_COM()
from messageBoxPro import msgBox

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8


    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)


class MainWindowShow(QtGui.QWidget):
    """
    窗体主方法
    """

    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.ui = Ui.Ui_Form()
        # Form = QtGui.QWidget()
        # ui = Ui_Form()
        # ui.setupUi(Form)
        self.ui.setupUi(self)
        self.job_name = os.environ.get('JOB')
        self.panel_step = 'panel'
        self.set_exists = GEN.STEP_EXISTS(step='set')
        if self.set_exists == 'yes':
            self.set_step = 'set'
        else:
            self.set_step = 'edit'
        self.pcs_step = 'edit'
        self.appVer = '2.11'
        self.update_date = '2022.10.12'
        self.scrDir = os.path.split(os.path.abspath(sys.argv[0]))[0]
        # === 增加外层及次外层干膜解析度的csv文件解析 ===
        self.tool_size_rule = []
        with open(self.scrDir + '/tool_size.csv') as f:
            f_csv = csv.DictReader(f)
            for row in f_csv:
                self.tool_size_rule.append(row)
        # print json.dumps(self.tool_size_rule, indent=2)
        
        # self.set_min_laser_ar_layers = []
        self.label = {}
        self.lineEdit = {}
        self.horizontalLayout = {}
        self.dictCouponInfo = {}
        self.allCouponInfo = []
        self.allInfoSave = {}
        
        self.allInfoSave["run_test_type"] = {"flj_coupon": "new_20241009"}
        
        self.top_Laser = []
        self.bot_Laser = []
        self.etch_layer = []
        self.drl_info = self.getdrillLayers()
        self.layer_num = int(self.job_name[4:6])
        self.linenum = len(self.drl_info['drl_layer'])
        self.max_txt_len = 0
        self.rout2cu = 20 * 0.0254
        self.textdx = 152 * 0.0254
        self.cu2cu = 20 * 0.0254
        self.cubar = 20 * 0.0254

        # === 分析板内相关的定义 ===
        self.chklist_name = 'signal_drill_check'
        self.result_list = ['c_type', 'sig_layer', 'result', 'r_unit', 'hole_symbol', 'pad_symbol', 'r_show',
                            'r_line_xs',
                            'r_line_ys', 'r_line_xe', 'r_line_ye', 'r_disp_id', 'r_color', 'r_index']
        # lvia2c l2 253.92 micron r102 r0 SG 3.5069 0.7130775 3.578625 0.4695 2 Y
        # pth2c l9 53.5 micron r102 r0 SG 1.51002 0.7498 1.561965 0.737 2 R 33
        self.warn_list = []
        self.laser_ar_range = [{'ar_down': 2.0, 'ar_up': 2.2, 'dest_ar': 2.2},
                               {'ar_down': 2.2, 'ar_up': 2.4, 'dest_ar': 2.4},
                               {'ar_down': 2.4, 'ar_up': 2.6, 'dest_ar': 2.6},
                               {'ar_down': 2.6, 'ar_up': 2.8, 'dest_ar': 2.8},
                               {'ar_down': 2.8, 'ar_up': 3.0, 'dest_ar': 3.0}]
        self.drill_layers = GEN.GET_ATTR_LAYER('drill')

        # === 获取 镭射层别列表 ===
        self.blind_layers = [i for i in self.drill_layers if re.match('s[1-9][0-9]?-?[1-9][0-9]?', i)]
        # --初始化jobsuse 目录
        if os.environ.get('JOB_USER_DIR'):
            self.userPath = os.environ.get('JOB_USER_DIR')
        else:
            self.userPath = os.path.join(os.environ.get('GENESIS_DIR'), 'fw', 'jobs', self.job_name, 'user')
        # --初始化记录文件
        self.jsonFile = 'HDI_TestCoupon.json'
        self.addUiDetail()
        self.ui.label_tips.setText(u'版权所有：胜宏科技 版本：%s 更新日期：%s' % (self.appVer, self.update_date))
        QtCore.QObject.connect(self.ui.pushButton_upload, QtCore.SIGNAL("clicked()"), self.loadingPargrams)
        QtCore.QObject.connect(self.ui.pushButton_close, QtCore.SIGNAL("clicked()"), self.close)
        QtCore.QObject.connect(self.ui.pushButton_apply, QtCore.SIGNAL("clicked()"), self.chkCouponMode)
        QtCore.QObject.connect(self.ui.pushButton_2, QtCore.SIGNAL("clicked()"), self.analysis_and_fill)

        # QtCore.QMetaObject.connectSlotsByName(QtGui.QWidget)

    def addUiDetail(self):

        self.ui.tableWidget.setRowCount(self.linenum)
        for i in range(self.linenum):
            for j, col in enumerate(['drl_layer', 'min_pth', 'min_list', 'min_ar']):
                if col in self.drl_info:
                    item = QtGui.QTableWidgetItem(str(self.drl_info[col][i]))
                    item.setFlags(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsUserCheckable)
                else:
                    item = QtGui.QTableWidgetItem()
                self.ui.tableWidget.setItem(i, j, item)
        # === 设定列宽
        table_col_width_list = [55, 100, 100, 150]
        for i, c_width in enumerate(table_col_width_list):
            self.ui.tableWidget.setColumnWidth(i, c_width)

    def getdrillLayers(self):
        # 获取钻带名称列表
        drill_layers = GEN.GET_ATTR_LAYER('drill')
        print drill_layers
        drl_info = {}
        drl_info['drl_layer'] = []
        drl_info['min_pth'] = []
        drl_info['min_list'] = []
        hole_reg = re.compile(r'[b,s][0-9]{2,4}$|[b,s][0-9]{1,2}-[0-9]{1,2}$|drl$')

        for item in drill_layers:
            if hole_reg.match(item):
                getlist = GEN.DO_INFO("-t layer -e %s/%s/%s -d TOOL -p drill_size+type+shape -o break_sr" %
                                      (self.job_name, self.set_step, item))
                if len(getlist['gTOOLdrill_size']) != 0:
                    # 只选pth孔
                    pth_tool = []
                    for i in range(len(getlist['gTOOLdrill_size'])):
                        if getlist['gTOOLtype'][i] in ['via', 'plated'] and getlist['gTOOLshape'][i] == 'hole':
                            if "drl" in item:
                                if not (str(getlist['gTOOLdrill_size'][i]).endswith("2") or\
                                   str(getlist['gTOOLdrill_size'][i]).endswith("4")):
                                    pth_tool.append(getlist['gTOOLdrill_size'][i])
                            else:
                                pth_tool.append(getlist['gTOOLdrill_size'][i])
                    if len(pth_tool):
                        # 按孔径大小取最小值，而不是按str格式取最小值
                        mintool = min(pth_tool, key=lambda x: float(x))

                        #20230802加入是否有浮点数存在，防止数据类型转换错误
                        try:
                            int(mintool)
                        except:
                            msg = msgBox()
                            msg.warning(None, '提示', '%s层存在非整数类型的孔径，大小:%s,请检查后再运行程序!' % (item,mintool), QMessageBox.Ok)
                            sys.exit()

                        if float(mintool) > 500:
                            if not item.startswith('s'):
                                drl_info['min_pth'].append('497')
                                drl_info['min_list'].append(mintool)
                            else:
                                drl_info['min_pth'].append(mintool)
                                drl_info['min_list'].append(mintool)
                        else:
                            min_pth = ''
                            if not item.startswith('s'):
                                for t_line in self.tool_size_rule:
                                    if int(t_line['tool_low']) < int(mintool) < int(t_line['tool_up']):
                                        min_pth = t_line['test_size']
                            # coupon内的孔要先钻，以'0'结尾的减3um
                            #     min_pth = str(int(mintool) - 3)
                            # elif mintool.endswith('5'):
                            #     # coupon内的孔要先钻，以'5'结尾的减2um
                            #     min_pth = str(int(mintool) - 2)
                            else:
                                min_pth = mintool
                            drl_info['min_pth'].append(min_pth)
                            drl_info['min_list'].append(mintool)
                        drl_info['drl_layer'].append(item)
                    else:
                        mintool = ''
                else:
                    mintool = ''
                    if item.startswith("s"):
                        arraylist = getSmallestHole_and_step(self.job_name, "", item, return_all_step=True)
                        mintool,stepname = sorted(arraylist, key=lambda x: x[0])[0]
                        if mintool:                            
                            drl_info['min_pth'].append(mintool)
                            drl_info['min_list'].append(mintool)
                            drl_info['drl_layer'].append(item)
                            # self.set_min_laser_ar_layers = [(item, x[1]) for x in arraylist if x[0] == mintool]
        # print drl_info
        return drl_info

    def get_etch_layer(self):
        # 获取蚀刻层列表
        self.etch_layer = []
        for x, y in enumerate(xrange(self.layer_num), 1):
            self.etch_layer.append("l" + str(x))

    def chkCouponMode(self):
        # 关闭窗口界面
        self.close()

        # --检测层别
        self.check_layer_name()
        # 确认界面值填写正确
        check_result = self.checkParameter()
        if check_result != '':
            try:
                if self.Message(check_result) == _fromUtf8("是"):
                    self.show()
                else:
                    if self.Message(check_result) == _fromUtf8("否"):
                        self.close()
            except:
                self.close()
        else:
            self.get_etch_layer()
            self.process_table_info()

            self.check_laser_layers()
            # --存储输入的参数
            self.saveJsonInfo()
                
            if self.ui.checkBox_4.isChecked():
                # addQieHoleCoupon.run_qie_hole_step() --改用新切片模块 http://192.168.2.120:82/zentao/story-view-8207.html
                os.system("python /incam/server/site_data/scripts/hdi_scr/Panel/creat_a86_coupon/creat_qp_coupon_new.py")
                
            # --检测所需要添加项
            if self.ui.checkBox.isChecked():
                self.create_coupon()
                self.addkCouponMode()
            # --用于创建镭射防漏接Coupon设计 . 作者：柳闯
            if self.ui.checkBox_2.isChecked():
                fljCoupon.MAIN(self.allCouponInfo)
            # --用于创建对准度防漏接Coupon设计 . 作者：柳闯
            if self.ui.checkBox_3.isChecked():
                dzdCoupon.MAIN(self.allCouponInfo)
                
            msg_box = msgBox()
            msg_box.information(self, '添加Coupon测试模块', '脚本运行完成，请检查!', QMessageBox.Ok)
            sys.exit()

    def check_laser_layers(self):
        
        #此处做个是否镭射能导通到外层的检测 即是否有漏接镭射断层的情况 20241214 by lyh
        signalLayers = GEN.GET_ATTR_LAYER('signal')
        self.layCount = len(signalLayers)
        self.sortOutData()
        
        top_laser_index = []
        top_find_not_laser_index = []
        bot_laser_index = []
        bot_find_not_laser_index = []
        find_not_laser_layers = []
        for i, layer in enumerate(signalLayers):
            for die_kong in range(10)[::-1]:                
                if i <= len(signalLayers) *0.5:
                    drill_layer = "s{0}-{1}".format(i+1, i+2+die_kong)
                    if drill_layer in self.laserList:
                        top_laser_index.append(i)
                        # 对应的底层镭射
                        drill_layer = "s{0}-{1}".format(self.layCount-(i+1) + 1, self.layCount-(i+2+die_kong) + 1)
                        if drill_layer not in self.laserList:
                            top_find_not_laser_index.append(i)
                            find_not_laser_layers.append(drill_layer)
                        break
                else:
                    drill_layer = "s{0}-{1}".format(i+1+die_kong, i)
                    if drill_layer in self.laserList:
                        bot_laser_index.append(i)
                        # 对应的顶层镭射
                        drill_layer = "s{0}-{1}".format(self.layCount-(i+1+die_kong) + 1, self.layCount-(i) + 1)
                        if drill_layer not in self.laserList:
                            bot_find_not_laser_index.append(i)
                            find_not_laser_layers.append(drill_layer)
                        break
        
        errorMsg = ""
        # GEN.PAUSE(str([top_find_not_laser_index, top_laser_index, bot_find_not_laser_index, bot_laser_index]))
        if (top_find_not_laser_index and (max(top_find_not_laser_index) < max(top_laser_index))) or \
           (bot_find_not_laser_index and (min(bot_find_not_laser_index) > min(bot_laser_index))):
            errorMsg = u"发现{0}层镭射没有孔，请在edit单元内加最小孔，并重新分析最小孔径，以便防漏接能测试导通！".format(find_not_laser_layers)
            self.Message('%s' % errorMsg)
            sys.exit(0)
            
    def sortOutData(self):
        """
        重新整理前端传入的参数以便此模块的分析
        :return:None
        """
        errorMsg = ""
        self.laserList = []
        # --遍历所有孔信息
        GEN.LOG(u'遍历传入参数的所有孔信息...')
        print self.allCouponInfo
        for i, Dict in enumerate(self.allCouponInfo):
            # --重新按Layer名为Key,创建HASH
            hole_name = str(Dict['hole_name'])

            # --只过滤出laser层
            if not hole_name.startswith('s'):
                continue

            # --检测命名是否标准
            if hole_name.startswith('s') and '-' not in hole_name:
                if errorMsg == "":
                    errorMsg = u'添加对准度模块失败！\n'
                errorMsg += u"%s 层钻带名命名不标准，请按最新标准命名！\n" % hole_name
                continue

            # --多字符切割，取出所有laser层两头信息
            (laser_s, laser_e) = self.splitLaser(hole_name)

            if abs(laser_s - laser_e) > 1:
                GEN.LOG(u'%s 此层非镭射层，跳过...' % hole_name)
                # continue
                # --判断是否存在s1-3类似的镭射孔  --测试用（标准未定）
                if abs(laser_e - laser_s) >= 2:
                    self.laserList.append(hole_name)
                else:
                    continue
            else:
                self.laserList.append(hole_name)

        # --当有收集到错误信息时
        if errorMsg != '':
            self.Message('%s' % errorMsg)
            sys.exit(0)
    def splitLaser(self, laserlayName):
        """
        匹配两个字符进行分割镭射层信息
        :param laserlayName:镭射层（s8-7)
        :return: (无组)
        """
        laser_s = int(re.split(r'[s,-]', laserlayName)[1])
        laser_e = int(re.split(r'[s,-]', laserlayName)[2])
        # --返加一个元组
        return (laser_s, laser_e)    
    def create_coupon(self):
        # 创建试钻模块
        if GEN.STEP_EXISTS(job=self.job_name, step='drill_test_coupon') == 'yes':
            GEN.OPEN_STEP('drill_test_coupon', job=self.job_name)
            GEN.COM('affected_layer,mode=all,affected=yes')
            GEN.COM('sel_delete')
            GEN.COM('affected_layer,mode=all,affected=no')
            GEN.CHANGE_UNITS('mm')
        else:
            GEN.CREATE_ENTITY('', job=self.job_name, step='drill_test_coupon')
            GEN.OPEN_STEP('drill_test_coupon', job=self.job_name)
            GEN.CHANGE_UNITS('mm')

    def process_table_info(self):
        """
        检查table中的信息，存入字典列表当中
        :return:
        """
        for i in range(self.linenum):
            a = self.ui.tableWidget.item(i, 0).text()
            b = self.ui.tableWidget.item(i, 1).text()
            d = self.ui.tableWidget.item(i, 3).text()
            self.dictCouponInfo[str(a)] = {'minDrill': str(b),
                                           'minRing': str(d)}
            if self.max_txt_len < len(a):
                self.max_txt_len = len(a)
            hole_dict = {'hole_name': str(a),
                         'minDrill': str(b),
                         'minRing': str(d)
                         }
            self.allCouponInfo.append(hole_dict)
            # --记录用于存储加载用的字典
            self.allInfoSave[str(a)] = {'minDrill': str(b), 'minRing': str(d)}
        # 对字典列表进行排序，按孔径从大到小
        self.allCouponInfo = list(reversed(sorted(self.allCouponInfo, key=lambda x: float(x['minDrill']))))

    def addkCouponMode(self):
        # 初始化变量
        layer_num = int(self.job_name[4:6])
        outer_layer = ['l1', 'l' + str(layer_num)]
        laser_reg = re.compile(r's[0-9]{2,4}$|s[0-9]{1,2}-[0-9]{1,2}$')
        pad2pad = 20 * 25.4 / 1000
        clearence = 4 * 25.4 / 1000
        clear2edge = 20 * 25.4 / 1000
        clear2text = 10 * 25.4 / 1000
        txt_x_size = 45 * 25.4 / 1000
        txt_y_size = 45 * 25.4 / 1000
        start_x = 0
        start_y = 0.2
        prof_xmax = 0
        prof_ymax = 0
        if self.max_txt_len > 4:
            # 镭射新命名规则导致层别名过长，层别标示相应的往右移
            txt_offset = 7
        else:
            txt_offset = 5
        # 生成只包含层别名的列表，方便取index用
        iList = []
        # fill 铜皮 加负片pad 加正片pad 钻孔层加孔


        # print json.dumps(self.allCouponInfo,indent=2)

        for i, Dict in enumerate(self.allCouponInfo):
            hole_name = str(Dict['hole_name'])
            min_drill = float(Dict['minDrill'])
            min_ring = float(Dict['minRing']) * 25.4
            min_pad = min_drill + min_ring * 2
            iList.append(Dict['hole_name'])
            if (i == 0):
                m = 0  # 引入m变量，用于当镭射层成对排列在1，2序号时，均跑在模块右侧的问题
                # 针对最大孔径（有可能是drl，也有可能是别的孔),设置dx等关键参数
                dx = min_pad + pad2pad * 1000
                # dx1 = dx * 4
                # dx2 = dx * 2
                # dx3 = dx
                pad_x1_left = start_x + txt_offset + clear2edge + min_pad / 2000
                pad_x2_left = pad_x1_left + dx / 1000
                pad_x3_left = pad_x2_left + dx / 1000
                pad_x4_left = pad_x3_left + dx / 1000
                pad_x5_left = pad_x4_left + dx / 1000
            elif (i == 1):
                # 默认做成两列，第二大的孔径应该会排在右侧
                start_x = 0 + txt_offset + 4 * clear2edge + min_pad / 1000 + dx * 4 / 1000 + 2 * clearence + 1.2
                pad_x1_right = start_x + txt_offset + clear2edge + min_pad / 2000
                pad_x2_right = pad_x1_right + dx / 1000
                pad_x3_right = pad_x2_right + dx / 1000
                pad_x4_right = pad_x3_right + dx / 1000
                pad_x5_right = pad_x4_right + dx / 1000
            if (m % 2 == 0):
                pad_x1 = pad_x1_left
                pad_x2 = pad_x2_left
                pad_x3 = pad_x3_left
                pad_x4 = pad_x4_left
                pad_x5 = pad_x5_left
                pad_y = start_y + clear2edge + clearence + min_pad / 2000
                txt_x_name = 0 + clear2edge
                end_x = 0 + txt_offset + 2 * clear2edge + min_pad / 1000 + dx * 4 / 1000 + 2 * clearence
            else:
                pad_x1 = pad_x1_right
                pad_x2 = pad_x2_right
                pad_x3 = pad_x3_right
                pad_x4 = pad_x4_right
                pad_x5 = pad_x5_right
                txt_x_name = start_x + clear2edge
                end_x = start_x + txt_offset + 2 * clear2edge + min_pad / 1000 + dx * 4 / 1000 + 2 * clearence
            # 定义层别名添加的y坐标
            txt_y_name = pad_y - txt_y_size / 2
            # 定义ring环添加的坐标
            # txt_x_ring = pad_x3 - txt_x_size/2
            txt_x_ring = pad_x3
            txt_y_ring = pad_y + min_pad / 2000 + clearence + clear2text
            # 正反面镭射坐标重复
            if laser_reg.match(hole_name):
                if '-' in hole_name:
                    digt_s = re.split(r'[s,-]', hole_name)[1]
                    digt_e = re.split(r'[s,-]', hole_name)[2]
                    pair_s = layer_num + 1 - int(digt_s)
                    pair_e = layer_num + 1 - int(digt_e)
                    pair_laser = "s" + str(pair_s) + '-' + str(pair_e)
                else:
                    if len(hole_name) >= 4:
                        # s910，结束层别取两码
                        if hole_name == 's109':
                            digt_e = 9
                            digt_s = 10
                        else:
                            digt_e = int(hole_name[-2:])
                            digt_s = int(hole_name[:-2][1:])
                        pair_s = layer_num + 1 - digt_s
                        pair_e = layer_num + 1 - digt_e
                    else:
                        # s89,结束层别取1码
                        digt_e = int(hole_name[-1:])
                        digt_s = int(hole_name[:-1][1:])
                        pair_s = layer_num + 1 - digt_s
                        pair_e = layer_num + 1 - digt_e
                    pair_laser = "s" + str(pair_s) + str(pair_e)
                if pair_laser in iList:
                    index = iList.index(pair_laser)
                    pair_Dict = self.allCouponInfo[index]
                    pad_x1 = pair_Dict['pad_x1']
                    pad_x2 = pair_Dict['pad_x2']
                    pad_x3 = pair_Dict['pad_x3']
                    pad_x4 = pair_Dict['pad_x4']
                    pad_x5 = pair_Dict['pad_x5']
                    pad_y = pair_Dict['pad_y']
                    txt_x_name = pair_Dict['txt_x_name']
                    txt_y_name = pair_Dict['txt_y_name']
                    txt_x_ring = pair_Dict['txt_x_ring']
                    txt_y_ring = pair_Dict['txt_y_ring']
                else:
                    m += 1
            else:
                m += 1
            # 定义下次添加的起始y坐标
            start_y = txt_y_ring + txt_y_size + clear2text
            # 定义profile尺寸
            if end_x > prof_xmax:
                prof_xmax = end_x
            if start_y > prof_ymax:
                prof_ymax = start_y
            else:
                # 右边的pad可能比左边的小，导致start_y被重置为右边较小的，此处修正
                if (i % 2 == 1):
                    start_y = prof_ymax
            GEN.WORK_LAYER(hole_name)
            # 添加孔
            GEN.ADD_PAD(pad_x1, pad_y, 'r' + str(min_drill), nx=1, ny=1, dx=0, dy=0)
            GEN.ADD_PAD(pad_x2, pad_y, 'r' + str(min_drill), nx=1, ny=1, dx=0, dy=0)
            GEN.ADD_PAD(pad_x3, pad_y, 'r' + str(min_drill), nx=1, ny=1, dx=0, dy=0)
            GEN.ADD_PAD(pad_x4, pad_y, 'r' + str(min_drill), nx=1, ny=1, dx=0, dy=0)
            GEN.ADD_PAD(pad_x5, pad_y, 'r' + str(min_drill), nx=1, ny=1, dx=0, dy=0)
            if laser_reg.match(hole_name):
                GEN.COM('cur_atr_reset')
                GEN.COM('cur_atr_set,attribute=.drill,option=via')
                GEN.COM('cur_atr_set,attribute=.via_type,option=laser')
                GEN.COM('sel_change_atr,mode=add')
                GEN.COM('cur_atr_reset')
            else:
                GEN.COM('cur_atr_reset')
                GEN.COM('cur_atr_set,attribute=.drill,option=via')
                # GEN.COM('cur_atr_set,attribute=.via_type,option=laser')
                GEN.COM('sel_change_atr,mode=add')
                GEN.COM('cur_atr_reset')

            # 将孔以相应的大小copy到档点层制作档点
            if hole_name == 'drl':
                if min_drill <= 400:
                    enlarge = 10 * 25.4
                else:
                    enlarge = 8 * 25.4
                for md in ('md1', 'md2'):
                    GEN.COM('sel_copy_other,dest=layer_name,target_layer=%s,invert=no,dx=0,dy=0,size=%s,x_anchor=0,y_anchor=0' % (md,enlarge))
                GEN.CLEAR_LAYER()
            # 写入字典，以备后用
            Dict['min_pad'] = min_pad
            Dict['pad_x1'] = pad_x1
            Dict['pad_x2'] = pad_x2
            Dict['pad_x3'] = pad_x3
            Dict['pad_x4'] = pad_x4
            Dict['pad_x5'] = pad_x5
            Dict['pad_y'] = pad_y
            Dict['txt_x_name'] = txt_x_name
            Dict['txt_y_name'] = txt_y_name
            Dict['txt_x_ring'] = txt_x_ring
            Dict['txt_y_ring'] = txt_y_ring
        # 定义profile
        prof_ymax = prof_ymax + 0.3
        GEN.COM('profile_rect,x1=0,y1=0,x2=%s,y2=%s' % (prof_xmax, prof_ymax))
        GEN.CLEAR_LAYER()
        # 防焊填充profile
        GEN.COM(
            'affected_filter,filter=(type=solder_mask|components|mask&context=board&side=top|bottom|none&pol=positive)')
        GEN.SR_FILL('positive', 0, 0, 2540, 2540)
        # 内层填充profile
        GEN.COM(
            'affected_filter,filter=(type=signal|power_ground|components|mask&context=board&side=inner|none&pol=positive)')
        # === Song 2021.05.31 双面板也需试钻孔
        GEN.COM('get_affect_layer')
        get_af_list = list(GEN.COMANS.split())
        if len(get_af_list) > 0:
            GEN.SR_FILL('positive', 0, 0, 2540, 2540)
        # 用profile_to_rout命令生成prof_rout层
        width_rout = 16 * 25.4
        GEN.DELETE_LAYER('prof_rout')
        GEN.COM('profile_to_rout,layer=prof_rout,width=%f' % width_rout)
        # 套开所有信号层，做内刮
        GEN.COM('affected_filter,filter=(type=signal|power_ground|components|mask&context=board&pol=positive)')
        GEN.COM('get_affect_layer')
        # etch_layer = list(GEN.COMANS.split())
        etch_layer = self.etch_layer
        GEN.CLEAR_LAYER()
        GEN.WORK_LAYER('prof_rout')
        GEN.COM('affected_filter,filter=(type=signal|power_ground|components|mask&context=board&pol=positive)')
        GEN.COM('sel_copy_other,dest=affected_layers,target_layer=,invert=yes,dx=0,dy=0,size=0,x_anchor=0,y_anchor=0')
        GEN.CLEAR_LAYER()
        for i, Dict in enumerate(self.allCouponInfo):
            # 从字典中取值
            hole_name = str(Dict['hole_name'])
            min_drill = float(Dict['minDrill'])
            min_ring = float(Dict['minRing']) * 25.4
            min_pad5 = float(Dict['min_pad']) + 1.0 * 2 * 25.4
            min_pad4 = float(Dict['min_pad']) + 0.5 * 2 * 25.4
            min_pad3 = float(Dict['min_pad'])
            min_pad2 = float(Dict['min_pad']) - 0.5 * 2 * 25.4
            min_pad1 = float(Dict['min_pad']) - 1.0 * 2 * 25.4
            min_clear5 = min_pad5 + clearence * 2000
            min_clear4 = min_pad4 + clearence * 2000
            min_clear3 = min_pad3 + clearence * 2000
            min_clear2 = min_pad2 + clearence * 2000
            min_clear1 = min_pad1 + clearence * 2000
            min_fx_laser = min_drill + 254
            pad_x1 = Dict['pad_x1']
            pad_x2 = Dict['pad_x2']
            pad_x3 = Dict['pad_x3']
            pad_x4 = Dict['pad_x4']
            pad_x5 = Dict['pad_x5']
            pad_y = Dict['pad_y']
            txt_x_name = Dict['txt_x_name']
            txt_y_name = Dict['txt_y_name']
            txt_x_ring = Dict['txt_x_ring']
            txt_y_ring = Dict['txt_y_ring']
            # 所有内层做clearence
            GEN.CLEAR_LAYER()
            if hole_name == 'drl':
                start, end = (etch_layer[0], etch_layer[-1])
            else:
                start, end = GEN.GET_DRILL_THROUGH(hole_name)
                # 考虑从底层拉的钻带
                if int(start[1:]) > int(end[1:]):
                    tmp = start
                    start = end
                    end = tmp
            layer_list = []
            add_pad = []
            add_fx = []

            for layer in etch_layer:
                if int(end[1:]) >= int(layer[1:]) >= int(start[1:]):
                    layer_list.append(layer)
                # if 's' in hole_name or 'b' in hole_name:
                if re.match("s\d+-.*", hole_name) or re.match("b\d+-\d+", hole_name): 
                    if int(end[1:]) == int(layer[1:]) or  int(start[1:])==int(layer[1:]):
                        add_pad.append(layer)
                    else:
                        add_fx.append(layer)
                else:
                    add_pad.append(layer)

            for layer in layer_list:
                GEN.AFFECTED_LAYER(layer, 'yes')
                if layer in add_fx:
                    GEN.ADD_PAD(pad_x1, pad_y, 'r' + str(min_fx_laser), pol='negative', nx=1, ny=1, dx=0, dy=0)
                    GEN.ADD_PAD(pad_x2, pad_y, 'r' + str(min_fx_laser), pol='negative', nx=1, ny=1, dx=0, dy=0)
                    GEN.ADD_PAD(pad_x3, pad_y, 'r' + str(min_fx_laser), pol='negative', nx=1, ny=1, dx=0, dy=0)
                    GEN.ADD_PAD(pad_x4, pad_y, 'r' + str(min_fx_laser), pol='negative', nx=1, ny=1, dx=0, dy=0)
                    GEN.ADD_PAD(pad_x5, pad_y, 'r' + str(min_fx_laser), pol='negative', nx=1, ny=1, dx=0, dy=0)
                else:
                    GEN.ADD_PAD(pad_x1, pad_y, 'r' + str(min_clear1), pol='negative', nx=1, ny=1, dx=0, dy=0)
                    GEN.ADD_PAD(pad_x2, pad_y, 'r' + str(min_clear2), pol='negative', nx=1, ny=1, dx=0, dy=0)
                    GEN.ADD_PAD(pad_x3, pad_y, 'r' + str(min_clear3), pol='negative', nx=1, ny=1, dx=0, dy=0)
                    GEN.ADD_PAD(pad_x4, pad_y, 'r' + str(min_clear4), pol='negative', nx=1, ny=1, dx=0, dy=0)
                    GEN.ADD_PAD(pad_x5, pad_y, 'r' + str(min_clear5), pol='negative', nx=1, ny=1, dx=0, dy=0)
                GEN.CLEAR_LAYER()


            for layer in add_pad:
                # target层做pad
                GEN.AFFECTED_LAYER(layer, 'yes')
                GEN.ADD_PAD(pad_x1, pad_y, 'r' + str(min_pad1), pol='positive', nx=1, ny=1, dx=0, dy=0)
                GEN.ADD_PAD(pad_x2, pad_y, 'r' + str(min_pad2), pol='positive', nx=1, ny=1, dx=0, dy=0)
                GEN.ADD_PAD(pad_x3, pad_y, 'r' + str(min_pad3), pol='positive', nx=1, ny=1, dx=0, dy=0)
                GEN.ADD_PAD(pad_x4, pad_y, 'r' + str(min_pad4), pol='positive', nx=1, ny=1, dx=0, dy=0)
                GEN.ADD_PAD(pad_x5, pad_y, 'r' + str(min_pad5), pol='positive', nx=1, ny=1, dx=0, dy=0)
                GEN.CLEAR_LAYER()


            # 外层文字正极性、内层负极性
            if start in outer_layer:
                start_pol = 'positive'
            else:
                start_pol = 'negative'
            if end in outer_layer:
                end_pol = 'positive'
            else:
                end_pol = 'negative'
            # 定义字正和字反
            if laser_reg.match(hole_name):
                if "-" in hole_name:
                    # 适用于镭射新命名规则
                    digt_s = int(re.split(r'[s,-]', hole_name)[1])
                    digt_e = int(re.split(r'[s,-]', hole_name)[2])
                    if digt_e > layer_num / 2:
                        start_mir = 'yes'
                        end_mir = 'yes'
                    else:
                        start_mir = 'no'
                        end_mir = 'no'
                else:
                    # 适用于镭射旧命名规则
                    if len(hole_name) >= 4:
                        # s910，结束层别取两码
                        if hole_name == 's109':
                            digt_e = 9
                            digt_s = 10
                        else:
                            digt_e = int(hole_name[-2:])
                            digt_s = int(hole_name[:-2][1:])
                    else:
                        # s89,结束层别取1码
                        digt_e = int(hole_name[-1:])
                        digt_s = int(hole_name[:-1][1:])
                    if digt_s > layer_num / 2:
                        start_mir = 'yes'
                        end_mir = 'yes'
                    else:
                        start_mir = 'no'
                        end_mir = 'no'
                txt_name = hole_name.upper()
            else:
                start_mir = 'no'
                end_mir = 'yes'
                txt_name = hole_name
            # target s面文字坐标重定义
            if start_mir == 'yes':
                txt_x_name_c = txt_x_name + len(hole_name) * txt_x_size
                txt_x_ring_c = txt_x_ring + len(Dict['minRing']) * txt_x_size / 2
            else:
                txt_x_name_c = txt_x_name
                txt_x_ring_c = txt_x_ring - len(Dict['minRing']) * txt_x_size / 2
            # target s面文字坐标重定义
            if end_mir == 'yes':
                txt_x_name_s = txt_x_name + len(hole_name) * txt_x_size
                txt_x_ring_s = txt_x_ring + len(Dict['minRing']) * txt_x_size / 2
            else:
                txt_x_name_s = txt_x_name
                txt_x_ring_s = txt_x_ring - len(Dict['minRing']) * txt_x_size / 2
            # target c面添加标示
            GEN.WORK_LAYER(start)
            GEN.ADD_TEXT(txt_x_name_c, txt_y_name, txt_name, txt_x_size, txt_y_size, w_factor=0.666667,
                         polarity=start_pol, mirr=start_mir)
            GEN.ADD_TEXT(txt_x_ring_c, txt_y_ring, Dict['minRing'], txt_x_size, txt_y_size, w_factor=0.666667,
                         polarity=start_pol, mirr=start_mir)
            # target s面添加标示
            GEN.WORK_LAYER(end)
            GEN.ADD_TEXT(txt_x_name_s, txt_y_name, txt_name, txt_x_size, txt_y_size, w_factor=0.666667,
                         polarity=end_pol, mirr=end_mir)
            GEN.ADD_TEXT(txt_x_ring_s, txt_y_ring, Dict['minRing'], txt_x_size, txt_y_size, w_factor=0.666667,
                         polarity=end_pol, mirr=end_mir)

    def checkParameter(self):
        warm_info = ''
        ring_out_spec = []
        for i in range(self.linenum):
            a = self.ui.tableWidget.item(i, 0).text()
            # print a
            b = self.ui.tableWidget.item(i, 1).text()
            d = self.ui.tableWidget.item(i, 3).text()
            print i, a, b, d
            if b == '' or d == '':
                warm_info += u"行%s，钻带%s，有数值为空，请检查\n" % ((i + 1), a)
            else:
                ring = float(d)
                if ring < 2 or ring > max_laser_ar:
                    warm_info += u"行%s，钻带%s，ring环超出范围，请检查\n" % (i, a)
                    ring_out_spec.append(ring)
        # 最后一行显示ring环范围
        if len(ring_out_spec) > 0:
            warm_info += u"ring环范围:2.0mil-{0}.0mil".format(max_laser_ar)
        return warm_info

    def check_layer_name(self):
        # 检查镭射命名是否符合规则，起始层别要大于结束层别
        errorMsg = ""
        laser_reg = re.compile(r's[0-9]{2,4}$|s[0-9]{1,2}-[0-9]{1,2}$')
        for i in range(self.linenum):
            layer_name = self.ui.tableWidget.item(i, 0).text()
            if laser_reg.match(layer_name):
                # 仅针对镭射层别名
                if '-' in layer_name:
                    # 层别名中带"-"
                    digt_s = int(re.split(r'[s,-]', layer_name)[1])
                    digt_e = int(re.split(r'[s,-]', layer_name)[2])
                    if int(digt_s) > self.layer_num / 2:
                        self.bot_Laser.append(layer_name)
                    else:
                        self.top_Laser.append(layer_name)
                else:
                    # 适用于镭射旧命名规则,层别名不带"-"
                    if len(layer_name) >= 4:
                        # s910，结束层别取两码
                        if layer_name == 's109':
                            digt_e = 9
                            digt_s = 10
                        else:
                            # s1011，结束层别取后两码
                            digt_e = int(layer_name[-2:])
                            digt_s = int(layer_name[:-2][1:])
                        if digt_s > self.layer_num / 2:
                            self.bot_Laser.append(layer_name)
                        else:
                            self.top_Laser.append(layer_name)
                    else:
                        # s89,结束层别取1码
                        digt_e = int(layer_name[-1:])
                        digt_s = int(layer_name[:-1][1:])
                        if digt_s > self.layer_num / 2:
                            self.bot_Laser.append(layer_name)
                        else:
                            self.top_Laser.append(layer_name)
                if digt_s > self.layer_num / 2:
                    if digt_e > digt_s:
                        errorMsg += u"%s 层钻带名命名不标准(起始层错误)，请按最新标准命名！\n" % layer_name
        # --当有收集到错误信息时
        if errorMsg != '':
            self.Message('%s' % errorMsg, sel=0)
            sys.exit(0)

    def Message(self, text, sel=1):
        message = QtGui.QMessageBox()
        # message.setText(QtCore.QObject.tr(text))
        message.setText(_fromUtf8(text))
        if sel != 1:
            message.addButton(u"OK", QtGui.QMessageBox.AcceptRole)
        if sel == 1:
            message.addButton(_fromUtf8("是"), QtGui.QMessageBox.AcceptRole)
            message.addButton(_fromUtf8("否"), QtGui.QMessageBox.RejectRole)
        message.exec_()
        return message.clickedButton().text()

    def saveJsonInfo(self):
        """
        存储当前料号的用户目录下，用以直接加载参数用
        :return:None
        """
        # print (json.dumps(self.allInfoSave, sort_keys=True, indent=4, separators=(', ', ': '), ensure_ascii=False))

        with open(os.path.join(self.userPath, self.jsonFile), 'w') as f:
            f.write(json.dumps(self.allInfoSave, sort_keys=True, indent=4, separators=(', ', ': '), ensure_ascii=False))

    def loadingPargrams(self):
        """
        加载最后一次参数
        :return: None
        """
        if not os.path.exists(os.path.join(self.userPath, self.jsonFile)):
            self.Message(u'未找到最后一次的参数记录，无法加载，请手动keyIn！', sel=0)
        else:
            # --读取存储的记录信息
            with open(os.path.join(self.userPath, self.jsonFile), 'r') as f:
                self.jsonData = json.load(f)
            # print "xxxxxxx\n%s\n\n" % self.jsonData
            for i in range(self.linenum):
                # --获取当前行的钻带信息
                # drlName = str(self.lineEdit[i][1].text())
                # self.lineEdit[i][4].setText(self.jsonData[drlName]['minRing'])

                drlName = str(self.ui.tableWidget.item(i, 0).text())
                self.ui.tableWidget.item(i, 3).setText(self.jsonData[drlName]['minRing'])

    def analysis_and_fill(self):
        # if len(self.blind_layers) == 0:
        #     # === 无镭射层，不进行防漏接检测 ===
        #     return True
        GEN.OPEN_STEP(self.pcs_step, job=self.job_name)
        GEN.CLEAR_LAYER()
        GEN.CHANGE_UNITS('inch')
        # === 内层分析，仅分析钻孔 分析结果
        self.run_checklist()
        all_rdict = self.get_checklist_result()
        # print all_rdict
        drl_dict = self.get_disp_id(self.drl_info['drl_layer'], all_rdict)
        # print(11111111111111, drl_dict)
        new_drl_dict = {}
        # for layer,stepname in self.set_min_laser_ar_layers:
        for i in range(self.linenum):
            drlName = str(self.ui.tableWidget.item(i, 0).text())
            if drlName not in drl_dict:
                arraylist = getSmallestHole_and_step(self.job_name, "", drlName, return_all_step=True)
                mintool,stepname = sorted(arraylist, key=lambda x: x[0])[0]
                if mintool:                            
                    for stepname in [x[1] for x in arraylist if x[0] == mintool]: 
                        # 去掉厂内加的测试coupon
                        for exclude_name in ["hct-coupon", "hct_coupon", "hct_coupon_new","drill_test_coupon", 
                                             "dzd_cp","cu-coupon","vip_coupon","qie_hole_coupon",
                                             "coupon-qp", "floujie"]:
                            if exclude_name.lower() in stepname:
                                break
                        else:                         
                            GEN.OPEN_STEP(stepname, job=self.job_name)
                            GEN.CLEAR_LAYER()
                            GEN.CHANGE_UNITS('inch')
                            
                            GEN.AFFECTED_LAYER(drlName, "yes")
                            GEN.COM('cur_atr_reset')
                            GEN.COM('cur_atr_set,attribute=.drill,option=via')
                            GEN.COM('cur_atr_set,attribute=.via_type,option=laser')
                            GEN.COM('sel_change_atr,mode=add')
                            GEN.COM('cur_atr_reset')
                            
                            self.run_checklist(stepname=stepname)
                            new_all_rdict = self.get_checklist_result(stepname=stepname)
                            new_drl_dict = self.get_disp_id([drlName], new_all_rdict, stepname=stepname)
                            # GEN.PAUSE(str([stepname, new_drl_dict]))
                            for key, value in new_drl_dict.iteritems():
                                if key not in drl_dict:                    
                                    drl_dict[key] = value
                                else:
                                    if drl_dict[key].get("laser_ar") is None:
                                        drl_dict[key] = value
                                    else:
                                        if value["laser_ar"] is not None and value["laser_ar"] < drl_dict[key]["laser_ar"]:
                                            drl_dict[key] = value
        
        # print(self.set_min_laser_ar_layers)
        # print(drl_dict)
        # exit()
        GEN.VOF()
        GEN.COM('save_job,job={0},override=no'.format(self.job_name))
        GEN.VON()
        GEN.OPEN_STEP(self.pcs_step, job=self.job_name)
        GEN.CLEAR_LAYER()
        GEN.CHANGE_UNITS('inch')        
        #if new_drl_dict:
            #for key, value in new_drl_dict.iteritems():
                #if key not in drl_dict:                    
                    #drl_dict[key] = value
            
        #print 2222, drl_dict
        #exit()
        for i in range(self.linenum):
            # --获取当前行的钻带信息
            # drlName = str(self.lineEdit[i][1].text())
            # self.lineEdit[i][4].setText(self.jsonData[drlName]['minRing'])

            drlName = str(self.ui.tableWidget.item(i, 0).text())
            if drlName in drl_dict:
                # 最大值按6mil设计
                # 周涌通知 6mil的上限改为10mil 20240622 by lyh
                if drlName in self.blind_layers:
                    if drl_dict[drlName]['laser_ar'] is None:
                        self.ui.tableWidget.item(i, 3).setText(str(max_laser_ar))
                        brush = QtGui.QBrush(QtGui.QColor(255, 0, 0))
                        brush.setStyle(QtCore.Qt.NoBrush)
                        self.ui.tableWidget.item(i, 3).setForeground(brush)
                       

                    elif float(drl_dict[drlName]['laser_ar']) > max_laser_ar or drl_dict[drlName]['laser_ar'] == None:
                        self.ui.tableWidget.item(i, 3).setText(str(max_laser_ar))
                        brush = QtGui.QBrush(QtGui.QColor(255, 0, 0))
                        brush.setStyle(QtCore.Qt.NoBrush)
                        self.ui.tableWidget.item(i, 3).setForeground(brush)
                        self.ui.tableWidget.item(i, 3).setToolTip(
                            u"板内实际值为{0}".format(str('%.1f' % drl_dict[drlName]['laser_ar'])))

                    else:
                        self.ui.tableWidget.item(i, 3).setText(str('%.1f' % drl_dict[drlName]['laser_ar']))
                else:
                    drill_ar_list = [k for k in drl_dict[drlName]['drill_ar'] if k != 0]
                    # drill_ar_list.remove(0)
                    # print drill_ar_list
                    if min(drill_ar_list) > max_laser_ar:
                        self.ui.tableWidget.item(i, 3).setText(str(max_laser_ar))
                        brush = QtGui.QBrush(QtGui.QColor(255, 0, 0))
                        brush.setStyle(QtCore.Qt.NoBrush)
                        self.ui.tableWidget.item(i, 3).setForeground(brush)
                        self.ui.tableWidget.item(i, 3).setToolTip(u"板内实际值为{0}".format(str('%.1f' % min(drill_ar_list))))
                    else:
                        self.ui.tableWidget.item(i, 3).setText(str('%.1f' % min(drill_ar_list)))

    def run_checklist(self, stepname=None):
        # 分析前去除部分锣带属性
        all_routs = GEN.GET_ATTR_LAYER(lay_type='rout')
        for rout_layers in all_routs:
            if not re.search('^pnl_rout\d+', rout_layers):
                GEN.COM("matrix_layer_context,job=%s,matrix=matrix,layer=%s,context=misc" % (os.environ['JOB'], rout_layers))
        gc_exist = GEN.DO_INFO("-t check -e %s/%s/%s -d EXISTS" % (self.job_name, stepname if stepname else self.pcs_step, self.chklist_name))
        if gc_exist["gEXISTS"] == 'yes':
            GEN.COM('chklist_delete,chklist=%s' % self.chklist_name)

        GEN.COM('chklist_from_lib,chklist=%s,profile=none,customer=' % self.chklist_name)
        GEN.COM('chklist_run,chklist=%s,nact=1,area=global,async_run=no' % self.chklist_name)

    def get_checklist_result(self, result_type=['laser_via_ar', 'pth_ar', 'via_ar'], stepname=None):
        """
        取分析结果中的镭射ring
        :return:
        """
        all_rdict = {}

        all_result = GEN.INFO("-t check -e %s/%s/%s -d MEAS -o index+action=1" % (
            self.job_name, stepname if stepname else self.pcs_step, self.chklist_name), units='inch')
        for r_line in all_result:
            r_list = r_line.split()
            if r_list[0] in result_type:
                r_dict = dict(zip(self.result_list, r_list))
                # print r_dict
                sig_layer = r_dict['sig_layer']
                r_disp_id = r_dict['r_disp_id']
                r_value = float(r_dict['result'])
                if sig_layer not in all_rdict:
                    all_rdict[sig_layer] = {r_disp_id: [r_value]}
                else:
                    if r_disp_id in all_rdict[sig_layer]:
                        all_rdict[sig_layer][r_disp_id].append(r_value)
                    else:
                        all_rdict[sig_layer][r_disp_id] = [r_value]
        return all_rdict

    def get_disp_id(self, drill_layers, all_rdict, stepname=None):
        """
        通过分析结果，取钻孔的Ring大小，镭射取底层的ring大小，机械孔取所有内层Ring，镭射孔的是字符串，机械孔的是列表
        :param drill_layers: list 镭射层
        :param all_rdict: 分析结果
        :return:
        """
        drl_dict = {}
        dp = GEN.INFO("-t check -e %s/%s/%s -d MEAS_DISP_ID -o action=1,  angle_direction=ccw" % (
            self.job_name, stepname if stepname else self.pcs_step, self.chklist_name), units='inch')
        for d_line in dp:
            d_list = d_line.split()
            if len(d_list) == 4:
                c_drl_layer = d_list[3]
                if c_drl_layer in drill_layers:
                    if c_drl_layer in self.blind_layers:
                        laser_end_layer = 'l' + d_list[3].split('-')[1]
                        if laser_end_layer == d_list[0]:
                            get_laser_ar = None
                            if laser_end_layer in all_rdict:
                                # === 2023.03.23 Song 没有分析结果时，定义10为AR值
                                if d_list[1] in all_rdict[laser_end_layer]:
                                    get_laser_ar = min(all_rdict[laser_end_layer][d_list[1]])
                                else:
                                    get_laser_ar = 10
                            dest_laser_ar = None
                            for line in self.laser_ar_range:
                                if line['ar_down'] <= get_laser_ar < line['ar_up']:
                                    dest_laser_ar = line['dest_ar']
                            if not dest_laser_ar: dest_laser_ar = get_laser_ar                                
                            drl_dict[d_list[3]] = {'end_layer': laser_end_layer, 'disp_id': d_list[1],
                                                   'laser_ar': dest_laser_ar}
                    else:
                        c_layer = d_list[0]
                        c_num = d_list[1]  # 分析结果的编号
                        # === V2.11
                        if c_layer not in all_rdict:
                            # 层别不在分析结果中时，认为当前层ring为较大值
                            ar_list = [10]
                        elif c_num in all_rdict[c_layer]:
                            ar_list = list(filter(lambda x: x != 0, all_rdict[c_layer][c_num]))
                            # print ar_list
                            # if 0 in ar_list:
                            #     ar_list.remove(0)

                        else:
                            # === 分析结果无值，给个较大值10，钉钉与陈惠建沟通，依此为上限值 ===
                            ar_list = [10]
                        get_ar = min(ar_list) if ar_list else 10
                        if c_drl_layer not in drl_dict:
                            drl_dict[c_drl_layer] = {'inner_layer': [c_layer], 'disp_id': [c_num], 'drill_ar': [get_ar]}
                        else:
                            drl_dict[c_drl_layer]['inner_layer'].append(c_layer)
                            drl_dict[c_drl_layer]['disp_id'].append(c_num)
                            drl_dict[c_drl_layer]['drill_ar'].append(get_ar)

                            
        return drl_dict


if __name__ == "__main__":
    import sys

    app = QtGui.QApplication(sys.argv)
    # Form = QtGui.QWidget()
    # ui = Ui_Form()
    # ui.setupUi(Form)
    ui = MainWindowShow()
    ui.show()
    # # --置顶
    # Form.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
    # Form.show()
    # # --居中
    # desktop = QtGui.QApplication.desktop()
    # x = (desktop.width() - Form.frameSize().width()) // 2
    # y = (desktop.height() - Form.frameSize().height()) // 2
    #
    # # --从屏幕外移回
    # Form.move(x, y)
    sys.exit(app.exec_())

# -------以上变更未记录版本，以及无变更记录------------------------
# V2.0
# Chao.Song
# 2022.04.25
# 1.引入实际钻咀大小的实际规则（tool_size.csv）通过孔径定义的上下限进行测试孔径定义（孔径-3um）
# http://192.168.2.120:82/zentao/story-view-4138.html
# 2022.05.06 未升版本，由于0.15mm孔径小于csv中定义的0.2mm，程序报错。Bug料号：B63-045A1

# V2.1
# Chao.Song
# 2022.08.26
# 1.更改程序与界面分离，使用tablewidget代替原有的line edit模式;
# 2.更改dzd_cp 模块不删除旧模块，直接更新
# 3.更改程序testCoupon.py --> testCouponV2.py 并变更程序路径
# 2022.08.29 1.分析Ring的数据保留一位小数
# 2.无分析结果时，使用10补位
# 2022.09.30 修复：通孔的分析ring结果为0时，不能获取Ring的问题

# V2.11
# Chao.Song
# 2022.10.12
# 排除了单层信号层会无分析结果的情况HB8108GB041A1

# V2.1.2
# Chao.Song
# 2022.11.01
# 1. 修正当各层镭射孔径不相同时，试钻孔模块镭射孔跑在同一位置的情况 Bug：323-937A1；
# 2. 增加镭射层的镭射孔属性；


