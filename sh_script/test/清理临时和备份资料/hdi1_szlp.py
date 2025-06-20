#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ---------------------------------------------------------#
#               VTG.SH SOFTWARE GROUP                     #
# ---------------------------------------------------------#
# @Author       :    Song
# @Mail         :
# @Date         :    2020/11、030
# @Revision     :    1.0
# @File         :    hdi1_szlp.py
# @Software     :    PyCharm
# @Usefor       :    HDI一厂树脂铝片制作程序
# @Revision     :
# ---------------------------------------------------------#

# --导入Package
import sys
import re
import os
import makelpUI as Mui
import json
import csv
from PyQt4 import QtCore, QtGui
import platform

import string

if platform.system() == "Windows":
    # sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
    sys.path.append(r"D:/genesis/sys/scripts/Package")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
import genCOM_26
import Oracle_DB

# from package import msgBox

reload(sys)
sys.setdefaultencoding("utf-8")

# --实例化genesis com对象
GEN = genCOM_26.GEN_COM()
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


class MyApp(object):
    def __init__(self):
        self.job_name = os.environ.get('JOB')
        self.step_name = os.environ.get('STEP')
        self.boardthick = 0
        self.tmplp = '__tmpszlp__'
        self.lpdict = {}
        self.smlist = GEN.GET_ATTR_LAYER('solder_mask')
        # === 以下语句仅适用于incam
        job_user_dir = os.environ.get('JOB_USER_DIR')
        self.logFile = '%s/resin_plug.log' % job_user_dir

    def stringtonum(self, instr):
        """
        转换字符串为数字优先转换为整数，不成功则转换为浮点数
        :param instr:
        :return:
        """
        try:
            num = string.atoi(instr)
            return num
        except (ValueError, TypeError):
            try:
                num = string.atof(instr)
                return num
            except ValueError:
                return False


class M_Box(QtGui.QMessageBox):
    """
    MesageBox提示界面
    """

    def __init__(self, parent=None):
        QtGui.QMessageBox.__init__(self, parent)

    def msgBox_option(self, body, title=u'提示信息', msgType='information'):
        """
        可供提示选择的MessagesBox
        :param body:显示内容（支持html样式）
        :param title:标题
        :param msgType:显示类型（包括information, question, warning）QtGui.QMessageBox.ButtonMask 可查看所有
        :return:
        """
        msg = QtGui.QMessageBox.information(self, u"信息", body, QtGui.QMessageBox.Ok,
                                            QtGui.QMessageBox.Cancel)  # , )
        # --返回相应信息
        if msg == QtGui.QMessageBox.Ok:
            return 'Ok'
        else:
            return 'Cancel'

    def msgBox(self, body, title=u'提示信息', msgType='information', ):
        """
        可供提示选择的MessagesBox
        :param body:显示内容（支持html样式）
        :param title:标题
        :param msgType:显示类型（包括information, question, warning）
        :return:
        """
        if msgType == 'information':
            QtGui.QMessageBox.information(self, title, body, u'确定')
        elif msgType == 'warning':
            QtGui.QMessageBox.warning(self, title, body, u'确定')
        elif msgType == 'question':
            QtGui.QMessageBox.question(self, title, body, u'确定')

    def msgText(self, body1, body2, body3=None, showcolor='#E53333'):
        """
        转换HTML格式
        :param body1:文本1
        :param body2:文本2
        :param body3:文本3
        :return:转换后的文本
        """
        # --转换为Html文本
        textInfo = u"""
                <p>
                    <span style="background-color:%s;color:'#FFFFFF';font-size:18px;"><strong>%s：</strong></span>
                </p>
                <p>
                    <span style="font-size:18px;">&nbsp;&nbsp;</span>
                    <span style="color:#E53333;font-size:18px;">&nbsp;&nbsp;</span>
                    <span style="color:#E53333;font-size:18px;">&nbsp; &nbsp; </span>
                    <span style="color:#E53333;font-size:16px;">%s</span>
                </p>""" % (showcolor, body1, body2)

        # --返回HTML样式文本
        return textInfo


class MainWindowShow(QtGui.QDialog, MyApp):
    """
    窗体主方法
    """

    def __init__(self):
        super(MainWindowShow, self).__init__()
        # 初始数据
        MyApp.__init__(self)
        if not self.job_name or not self.step_name:
            M = M_Box()
            showText = M.msgText(u'提示', u"必须打开料号及需添加的Step,程序退出!", showcolor='red')
            M.msgBox(showText)
            exit(0)
        if self.step_name == 'panel':
            M = M_Box()
            showText = M.msgText(u'提示', u"不能在panel中运行此程序,程序退出!", showcolor='red')
            M.msgBox(showText)
            exit(0)
        self.appVer = "V1.4"
        # === 获取钻孔层 ====
        all_drill = GEN.GET_ATTR_LAYER('drill')
        self.szpre_drill = {}
        for idrl in all_drill:
            if re.match(r'b[1-9][0-9]?-[1-9][0-9]?|drl', idrl):
                self.szpre_drill[idrl] = {'cur_yh_num': '',
                                          'thickness': '',
                                          'layer_mode': '',
                                          'sz_name': ''}
        self.yh_num = ''
        # === 获取压合板厚数据 ===
        self.DB_O = Oracle_DB.ORACLE_INIT()
        # 连接Inplan
        self.dbc_o = self.DB_O.DB_CONNECT(host='172.20.218.193', servername='inmind.fls', port='1521',
                                          username='GETDATA', passwd='InplanAdmin')
        self.lamin_data = self.get_lamin_thickness(self.dbc_o)
        # === 获取料号信息，包含是否树脂塞，是否防焊塞，中文为key
        job_data = self.DB_O.getJobData(self.dbc_o, self.job_name.upper()[:13])
        # print json.dumps(job_data,indent=2)
        self.dbc_o.close()
        self.job_info = job_data[0]
        # print json.dumps(self.lamin_data,indent=2)

        if not self.match_drill_and_thickness():
            exit(0)

        # === 2020.11.16 检测外层是否有树脂塞孔，如没有，层别从列表中删除 ===
        if self.job_info['是否树脂塞'] == '否':
            out_drill = [i for i in self.szpre_drill if self.szpre_drill[i]['layer_mode'] == 'outer']
            for c in out_drill:
                del self.szpre_drill[c]
        # print json.dumps(self.szpre_drill, indent=2)
        if len(self.szpre_drill) == 0:
            M = M_Box()
            showText = M.msgText(u'提示', u"没有需要树脂塞孔的层别,程序退出!", showcolor='red')
            M.msgBox(showText)
            exit(0)
        # print json.dumps(self.szpre_drill,indent=2)
        # === 选择输出铝片的层别 ===
        self.sz_lp = []
        self.job_step_list = GEN.GET_STEP_LIST(job=self.job_name)
        # 铝片塞孔模型 0 -- 无塞孔；1 -- 一种孔径；2 -- 多种孔径超范围0.2mm； 3 -- 多种孔径未超范围
        self.lpmode = ''
        self.scrDir = os.path.split(os.path.abspath(sys.argv[0]))[0]
        # 钻孔分类，考虑分T
        self.drill_classify = []
        self.sz_more_t_mode = []
        # self.lp_mode3_array = []

        with open(self.scrDir + '/sz_classify.csv') as f:
            f_csv = csv.DictReader(f)
            for row in f_csv:
                self.drill_classify.append(row)

        with open(self.scrDir + '/sz_morethanone.csv') as f:
            f_csv = csv.DictReader(f)
            for row in f_csv:
                self.sz_more_t_mode.append(row)

        self.ui = Mui.Ui_Dialog()
        self.ui.setupUi(self)
        self.addUiDetail()

    def addUiDetail(self):
        """
        在原框架基础上继续加载窗体
        :return:None
        """
        # 增加板厚输入限制，个位数加小数点后三位
        self.setWindowTitle(_translate("Dialog", "树脂塞孔", None))

        self.ui.label.setText(_translate("Dialog", "HDI一厂树脂塞孔铝片制作\n"
                                                   " 版本：%s" % self.appVer, None))
        my_regex = QtCore.QRegExp("^[0-3]\.[0-9][0-9]?[0-9]?$")
        my_validator = QtGui.QRegExpValidator(my_regex, self.ui.lineEdit)
        self.ui.lineEdit.setValidator(my_validator)
        # HDI一厂不需要输入板厚
        self.ui.lineEdit.hide()
        self.ui.label_2.hide()
        # === 2020.09.17 取消透光点要求
        self.ui.checkBox.setChecked(False)
        self.ui.checkBox.hide()
        # === table中显示层别列表
        self.ui.tableWidget.setColumnCount(2)
        item = self.ui.tableWidget.horizontalHeaderItem(1)
        item.setText(_translate("Dialog", "压合板厚", None))
        item = self.ui.tableWidget.horizontalHeaderItem(0)
        item.setText(_translate("Dialog", "选择层别", None))
        self.ui.tableWidget.setRowCount(len(self.szpre_drill))
        # QAbstractItemView.SelectColumns
        # self.ui.tableWidget.setSelectionMode(0)
        for i, layer in enumerate(self.szpre_drill):
            item = QtGui.QTableWidgetItem(str(layer))
            item.setFlags(
                QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            self.ui.tableWidget.setItem(i, 0, item)
            item = QtGui.QTableWidgetItem(str(self.szpre_drill[layer]['thickness']))
            item.setFlags(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsSelectable)
            self.ui.tableWidget.setItem(i, 1, item)
        # self.ui.label_3.hide()
        self.ui.checkBox_dot2cu.hide()
        self.ui.label_3.setText(u"Tips:选择层别前序号，使层别处于选中状态")
        QtCore.QObject.connect(self.ui.pushButton_apply, QtCore.SIGNAL("clicked()"), self.main_run)

    def closeEvent(self, event):
        GEN.FILTER_RESET()
        GEN.CLEAR_LAYER()
        if self.lpdict:
            # print json.dumps (self.lpdict, sort_keys=True, indent=2, separators=(',', ': '))
            for i in self.lpdict:
                if self.lpdict[i]:
                    GEN.DELETE_LAYER(self.lpdict[i]['drltmp'])
                    GEN.DELETE_LAYER(self.lpdict[i]['smtmp'])
        event.accept()

    def get_lamin_thickness(self, dbc):
        """
        在inplan中获取板厚
        :param dbc:
        :return:
        """
        sql = """select a.item_name as jobname,
               d.mrp_name,
               e.process_num_ ,
               b.pnl_size_x/1000,
               b.pnl_size_Y/1000,
               e.pressed_pnl_x_/1000,
               e.pressed_pnl_y_/1000,
               e.film_bg_,
           ROUND(e.PRESSED_THICKNESS_/39.37,2) as THICKNESS,
           ROUND(e.PRESSED_THICKNESS_TOL_PLUS_/39.37,2) as THICKNESS_PLUS,
           ROUND(e.PRESSED_THICKNESS_TOL_MINUS_/39.37,2) as THICKNESS_MINUS,
           e.LASER_BURN_TARGET_ 
          from vgt_hdi.items a
         inner join vgt_hdi.job b
            on a.item_id = b.item_id
           and a.last_checked_in_rev = b.revision_id
         inner join vgt_hdi.public_items c
            on a.root_id = c.root_id
         inner join vgt_hdi.process d
            on c.item_id = d.item_id
           and c.revision_id = d.revision_id
         inner join vgt_hdi.process_da e
            on d.item_id = e.item_id
           and d.revision_id = e.revision_id
         where a.item_name = '%s'
           and d.proc_type = 1
           order by e.press_program_ desc
        """ % self.job_name.upper()[:13]

        dataVal = self.DB_O.SELECT_DIC(dbc, sql)
        # === 分割下压合数据 ===     "MRP_NAME": "S94010PC202E1-20308",
        for i in dataVal:
            if i['MRP_NAME'] == i['JOBNAME']:
                self.yh_num = int(i['PROCESS_NUM_']) - 1
            check_mode1 = re.search('%s-([0-9]{5})' % self.job_name.upper()[:13], i['MRP_NAME'])
            if check_mode1:
                i['start_num'] = int(check_mode1.group(1)[1:3])
                i['end_num'] = int(check_mode1.group(1)[3:5])
        return dataVal

    def match_drill_and_thickness(self):
        """
        通过钻带名称匹配压合级别及板厚
        :return:
        """
        for drill in self.szpre_drill:
            if re.match(r'drl', drill):
                # === 通孔匹配最后一次压合板厚 ===
                self.szpre_drill[drill]['cur_yh_num'] = self.yh_num
                self.szpre_drill[drill]['thickness'] = [i['THICKNESS'] for i in self.lamin_data
                                                        if self.yh_num == (int(i['PROCESS_NUM_']) - 1)][0]
                self.szpre_drill[drill]['layer_mode'] = 'outer'
                self.szpre_drill[drill]['sz_name'] = 'sz.lp'
                # === 2020.11.16 如外层无树脂塞孔，则删除外层key===
            elif re.match(r'b[0-9][0-9]?-[0-9][0-9]?', drill):
                # === 埋孔根据埋孔层命名匹配第几次压合 ===
                bstart_layer = int(re.search(r'b([0-9][0-9]?)-([0-9][0-9]?)', drill).group(1))
                bend_layer = int(re.search(r'b([0-9][0-9]?)-([0-9][0-9]?)', drill).group(2))
                get_thickness = [(i['PROCESS_NUM_'], i['THICKNESS']) for i in self.lamin_data
                                 if
                                 ('start_num' in i and bstart_layer == i['start_num'] and bend_layer == i['end_num'])]
                self.szpre_drill[drill]['thickness'] = get_thickness[0][1]
                self.szpre_drill[drill]['cur_yh_num'] = int(get_thickness[0][0]) - 1
                self.szpre_drill[drill]['layer_mode'] = 'inner'
                self.szpre_drill[drill]['sz_name'] = 'sz%s-%s.lp' % (bstart_layer, bend_layer)
            else:
                M = M_Box()
                showText = M.msgText(u'提示', u"选中的层别%s不符合外层及埋孔命名!" % drill, showcolor='red')
                M.msgBox(showText)
                return False
        return True

    def makeCopylayer(self, source_layer, suffix):
        """

        :param source_layer:
        :param suffix:
        :return:
        """
        dislayer = '%s-%s' % (source_layer, suffix)
        GEN.DELETE_LAYER(dislayer)
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(source_layer, 'yes')
        GEN.SEL_COPY(dislayer)
        GEN.CLEAR_LAYER()
        return dislayer

    def seperateLayer(self, layer1, layer2):
        """
        两面均存在的钻孔分一层,单面存在的钻孔分一层
        """
        tmp_layer1 = '__tmponce__'
        tmp_layer2 = '__tmptwice__'
        feedback1 = None
        feedback2 = None
        GEN.DELETE_LAYER(tmp_layer1)
        GEN.DELETE_LAYER(tmp_layer2)
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(layer1, 'yes')
        GEN.FILTER_RESET()
        GEN.SEL_REF_FEAT(layer2, 'cover')
        if int(GEN.GET_SELECT_COUNT()) > 0:
            GEN.SEL_REVERSE()
            if int(GEN.GET_SELECT_COUNT()) > 0:
                GEN.SEL_COPY(tmp_layer1)
        else:
            GEN.SEL_REVERSE()
            if int(GEN.GET_SELECT_COUNT()) > 0:
                GEN.SEL_COPY(tmp_layer1)
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(layer2, 'yes')
        GEN.FILTER_RESET()
        GEN.SEL_REF_FEAT(layer1, 'cover')
        if int(GEN.GET_SELECT_COUNT()) > 0:
            GEN.SEL_REVERSE()
            if int(GEN.GET_SELECT_COUNT()) > 0:
                GEN.SEL_MOVE(tmp_layer1)
                GEN.SEL_COPY(tmp_layer2)
            else:
                GEN.SEL_COPY(tmp_layer2)
        else:
            GEN.SEL_REVERSE()
            if int(GEN.GET_SELECT_COUNT()) > 0:
                GEN.SEL_COPY(tmp_layer1)
        if GEN.LAYER_EXISTS(tmp_layer1, job=self.job_name, step=self.step_name) == 'yes':
            feedback1 = tmp_layer1
        if GEN.LAYER_EXISTS(tmp_layer2, job=self.job_name, step=self.step_name) == 'yes':
            feedback2 = tmp_layer2
        return feedback1, feedback2

    def mvhole(self, sourcelayer, orgSymSize, desSymSize, destlayer):
        # 通过中间辅助层，进行大小变更，移动到目标层
        mytmplayer = '__tmpchangehole__'
        GEN.DELETE_LAYER(mytmplayer)
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(sourcelayer, 'yes')
        GEN.FILTER_RESET()
        GEN.FILTER_SET_INCLUDE_SYMS('r%s' % orgSymSize)
        GEN.FILTER_SELECT()
        if int(GEN.GET_SELECT_COUNT()) == 0:
            M = M_Box()
            showText = M.msgText(u'提示', u"Error 2002 有没有搞错，怎么会%s选不到%s呢!" % (sourcelayer, orgSymSize), showcolor='red')
            M.msgBox(showText)
            return False
        GEN.SEL_MOVE(mytmplayer)
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(mytmplayer, 'yes')
        GEN.SEL_CHANEG_SYM('r%s' % desSymSize)
        GEN.SEL_COPY(destlayer)
        GEN.DELETE_LAYER(mytmplayer)
        GEN.CLEAR_LAYER()
        return

    def makelp(self, inputlayer, outputlayer, drill_layer):
        """
        制作铝片主流程
        :param inputlayer: 待分类需塞孔钻咀层
        :param outputlayer:  需生成lp层
        :param drill_layer: 相关钻孔层
        :return:
        """
        run_step_list = [self.step_name]
        # if GEN.STEP_EXISTS(job=self.job_name, step='dzd_cp') == 'yes':
        if 'dzd_cp' in self.job_step_list:
            run_step_list.append('dzd_cp')

        before_step = '%s' % self.step_name
        for current_step in run_step_list:
            self.step_name = current_step
            GEN.OPEN_STEP(self.step_name, job=self.job_name)
            GEN.CLEAR_LAYER()
            if current_step != before_step:
                GEN.AFFECTED_LAYER(inputlayer, 'yes')
                GEN.SEL_DELETE()
                GEN.AFFECTED_LAYER(inputlayer, 'no')
                GEN.AFFECTED_LAYER(drill_layer, 'yes')
                GEN.SEL_COPY(inputlayer)

                GEN.CLEAR_LAYER()
                GEN.VOF()
                GEN.AFFECTED_LAYER(outputlayer, 'yes')
                GEN.SEL_DELETE()
                GEN.VON()

                GEN.CLEAR_LAYER()
                GEN.CHANGE_UNITS('mm')
            dogetSym = GEN.DO_INFO('-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, self.step_name, inputlayer))
            gsymlist = [self.stringtonum(i.strip('r')) for i in dogetSym["gSYMS_HISTsymbol"]]
            # 对需做lp的symbol进行归类，考虑区间上下限
            needlplist = []
            outrangelist = []
            for tooldrill in gsymlist:
                tmpdict = {}
                for line in self.drill_classify:
                    if float(line['drill_down']) <= float(tooldrill) <= float(line['drill_up']):
                        tmpdict['mode'] = line['mode']
                        tmpdict['trudrill'] = tooldrill
                        tmpdict['pre_size'] = line['tool_mm']
                        tmpdict['tool_lower'] = line['tool_lower']
                        tmpdict['sz_mode1'] = line['sz_mode1']
                        tmpdict['sz_mode2'] = line['sz_mode2']
                        needlplist.append(tmpdict)

                # 不在区间内的判断
                if not tmpdict:
                    outrangelist.append(tooldrill)

            if len(outrangelist) != 0:
                s = ' '.join([str(a) for a in outrangelist])
                M = M_Box()
                showText = M.msgText(u'提示', u"孔径:%s超出可塞孔区间范围!" % s, showcolor='red')
                M.msgBox(showText)
                return False

            # 判断需要塞孔的孔径数量
            judge_lp_list = [int(i['tool_lower']) for i in needlplist]
            judgeMode = list(set(judge_lp_list))

            if len(judgeMode) == 1:
                self.lpmode = 1
            else:
                # === 判断极差大小，极差超过0.2mm需区分为2次塞孔
                max_lp_size = max(judge_lp_list)
                min_lp_size = min(judge_lp_list)
                if max_lp_size - min_lp_size >= 200:
                    self.lpmode = 2
                    # TODO 需塞孔的孔径进行分孔 小孔径分至szsk2-1，大孔径分到szsk2-2
                    # M = M_Box ()
                    # showText = M.msgText (u'提示', u"需分段塞孔，程序暂未支持!"  , showcolor='red')
                    # M.msgBox (showText)
                    get_run_status = self.deal_with_split_sz(inputlayer, drill_layer, needlplist)
                    return get_run_status
                else:
                    self.lpmode = 3
            # === 把孔径变为标准钻孔大小 ===
            chg_tmp_layer = self.change_to_normal_drill_size(inputlayer, needlplist, tmp_layer='__tmpoutdrill__')
            # === 塞孔的孔与非塞孔的孔的距离检查 ===
            getlayerless800 = self.check_dis_fill_with_no_fill(drill_layer, chg_tmp_layer)
            all_above_800 = 'no'
            if getlayerless800 is False:
                # === 过程中有错误抛出 ===
                return False
            elif getlayerless800 is True:
                all_above_800 = 'yes'

            # === 没有不需要塞孔的孔，均按大于800um处理
            if self.lpmode == 1:
                if all_above_800 == 'yes':
                    self.mvhole(chg_tmp_layer, needlplist[0]['pre_size'], needlplist[0]['sz_mode1'], outputlayer)
                else:
                    # === V1.3 单一孔径 选塞距离没有影响，但程序先不动，避免后续仍需更改
                    GEN.CLEAR_LAYER()
                    GEN.AFFECTED_LAYER(chg_tmp_layer, 'yes')
                    GEN.FILTER_RESET()
                    GEN.SEL_REF_FEAT(getlayerless800, 'touch')
                    if int(GEN.GET_SELECT_COUNT()) > 0:
                        tmp_resize = int(needlplist[0]['sz_mode2']) - int(needlplist[0]['pre_size'])
                        GEN.SEL_MOVE(outputlayer, size=tmp_resize)
                    else:
                        M = M_Box()
                        showText = M.msgText(u'提示', u"ERROR:001,区间%s分类错误!" % self.lpmode, showcolor='red')
                        M.msgBox(showText)
                        return False
                    # === 如果有剩余孔径，均按大于800处理
                    self.mvhole(chg_tmp_layer, needlplist[0]['pre_size'], needlplist[0]['sz_mode1'], outputlayer)
                # # === 运行完回收垃圾层 ===
                # GEN.DELETE_LAYER(chg_tmp_layer)
            elif self.lpmode == 3:
                GEN.CLEAR_LAYER()
                GEN.AFFECTED_LAYER(chg_tmp_layer, 'yes')
                if all_above_800 == 'no':
                    # === V1.3 如果存在此种情况，均按0.5-0.8的选塞距离处理
                    GEN.FILTER_RESET()
                    # GEN.SEL_REF_FEAT(getlayerless800, 'touch')
                    GEN.FILTER_SELECT()
                    if int(GEN.GET_SELECT_COUNT()) > 0:
                        # === D + 4
                        tmp_use_layer = '__tmpmoreone_drill__'
                        # GEN.CLEAR_LAYER()
                        GEN.DELETE_LAYER(tmp_use_layer)
                        # GEN.AFFECTED_LAYER(drill_layer, 'yes')
                        GEN.SEL_MOVE(tmp_use_layer)
                        dogetSym = GEN.DO_INFO(
                            '-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, self.step_name, tmp_use_layer))
                        gsymlist = [self.stringtonum(i.strip('r')) for i in dogetSym["gSYMS_HISTsymbol"]]
                        # 对需做lp的symbol进行归类，考虑区间上下限
                        needlplist = []
                        # outrangelist = []
                        for tooldrill in gsymlist:
                            tmpdict = {}
                            for line in self.drill_classify:
                                if float(line['drill_down']) <= float(tooldrill) <= float(line['drill_up']):
                                    tmpdict['mode'] = line['mode']
                                    tmpdict['trudrill'] = tooldrill
                                    tmpdict['pre_size'] = line['tool_mm']
                                    tmpdict['tool_lower'] = line['tool_lower']
                                    tmpdict['sz_mode1'] = line['sz_mode1']
                                    tmpdict['sz_mode2'] = line['sz_mode2']
                                    needlplist.append(tmpdict)
                        GEN.CLEAR_LAYER()
                        for drill_line in needlplist:
                            self.mvhole(tmp_use_layer, drill_line['trudrill'], drill_line['sz_mode1'], outputlayer)
                        GEN.CLEAR_LAYER()
                        tmpgetSym = GEN.DO_INFO(
                            '-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, self.step_name, tmp_use_layer))
                        tmpsymlist = [self.stringtonum(i.strip('r')) for i in tmpgetSym["gSYMS_HISTsymbol"]]
                        if len(tmpsymlist) != 0:
                            M = M_Box()
                            showText = M.msgText(u'提示', u"ERROR:1141，层别中%s仍存在物件!" % tmp_use_layer, showcolor='red')
                            M.msgBox(showText)
                            return False
                        # GEN.SEL_MOVE(outputlayer, size='100')
                    else:
                        M = M_Box()
                        showText = M.msgText(u'提示', u"ERROR:002,区间%s分类错误!" % self.lpmode, showcolor='red')
                        M.msgBox(showText)
                        return False
                # === 按区间分类
                # === 需判断需塞孔的孔径的最小值，再判断属于哪个区间
                dogetSym = GEN.DO_INFO(
                    '-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, self.step_name, chg_tmp_layer))
                if len(dogetSym["gSYMS_HISTsymbol"]) > 0:
                    gsymlist = [self.stringtonum(i.strip('r')) for i in dogetSym["gSYMS_HISTsymbol"]]
                    gsymlist = list(set(gsymlist))
                    min_drill = min(gsymlist)
                    print json.dumps(self.sz_more_t_mode, indent=2)
                    check_exist = 'no'
                    for all_item in self.sz_more_t_mode:
                        if str(min_drill) == all_item['min_drill']:
                            check_exist = 'yes'
                            GEN.CLEAR_LAYER()
                            GEN.AFFECTED_LAYER(chg_tmp_layer, 'yes')
                            for itool in gsymlist:
                                if all_item[str(itool)]:
                                    self.mvhole(chg_tmp_layer, itool, all_item[str(itool)], outputlayer)
                                else:
                                    M = M_Box()
                                    showText = M.msgText(u'提示', u"ERROR:006,最小孔径%s对应孔径%s不在规范内!" % (min_drill, itool),
                                                         showcolor='red')
                                    M.msgBox(showText)
                                    return False
                            GEN.CLEAR_LAYER()
                    if check_exist == 'no':
                        M = M_Box()
                        showText = M.msgText(u'提示', u"ERROR:005,最小孔径%s不在规范内!" % min_drill, showcolor='red')
                        M.msgBox(showText)
                        return False

            # === 增加塞孔层的距离检查 ===
            # TODO 待处理塞孔间距不足0.05mm的缩孔处理，加备注以及更改程序 V1.1.0 近孔距离 0.05mm --> 0.075mm
            get_lp_dist = self.check_touch_drill(outputlayer, close_hole_dis=500, op_chk_layer='yes')

            if float(get_lp_dist) <= 50:

                # M = M_Box()
                # get_decrease_size = self.decrease_hole_size(outputlayer, 'ms_1_%s_%s' % (outputlayer, outputlayer))
                # if get_decrease_size is False:
                #     showText = M.msgText(u'提示',
                #                          u"层别：%s 钻孔距离为%s 微米,不满足75微米的铝片间距，\n运行中未能缩小孔径，请处理!"
                #                          % (outputlayer, get_lp_dist),
                #                          showcolor='red')
                # else:
                #     showText = M.msgText(u'提示',
                #                          u"层别：%s 钻孔距离为%s 微米,不满足75微米的铝片间距，\n运行中能缩小孔径%s处，请处理!"
                #                          % (outputlayer, get_lp_dist, get_decrease_size),
                #                          showcolor='red')
                # M.msgBox(showText)
                M = M_Box()
                get_reshape_size = self.decrease_hole_size2drlsize(outputlayer, 'ms_1_%s_%s' % (outputlayer, outputlayer),drill_layer,dis_value=50)
                if get_reshape_size is False:
                    showText = M.msgText(u'提示',
                                         u"Step:%s 层别：%s 钻孔距离为%s 微米,不满足50微米的铝片间距，\n运行中未能缩小孔径，请处理!"
                                         % (self.step_name,outputlayer, get_lp_dist),
                                         showcolor='red')
                else:
                    showText = M.msgText(u'提示',
                                         u"Step:%s 层别：%s 钻孔距离为%s 微米,不满足50微米的铝片间距，\n运行中能缩小孔径%s处，请处理!"
                                         % (self.step_name,outputlayer, get_lp_dist, get_reshape_size),
                                         showcolor='red')
                M.msgBox(showText)
            endgetSym = GEN.DO_INFO('-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, self.step_name, outputlayer))
            if len(endgetSym['gSYMS_HISTsymbol']) > 2:
                M = M_Box()
                showText = M.msgText(u'提示', u"Step:%s 层别:%s，孔径超出2种，当前为：%s!" % (self.step_name, outputlayer,','.join(endgetSym['gSYMS_HISTsymbol'])),
                                     showcolor='red')
                M.msgBox(showText)

            # 再次判断待处理层别是否有物件
            # GEN.PAUSE('ccccccccccccccccccccccccccc')
            endgetSym = GEN.DO_INFO('-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, self.step_name, chg_tmp_layer))
            if len(endgetSym['gSYMS_HISTsymbol']) != 0:
                M = M_Box()
                showText = M.msgText(u'提示', u"Oh my God，Error015你看到这条消息了么，mode %s 快点告诉我，程序中断!" % self.lpmode,
                                     showcolor='red')
                M.msgBox(showText)
                return False
            else:
                # === 运行完成后回收垃圾层 ===
                GEN.DELETE_LAYER(chg_tmp_layer)
                GEN.DELETE_LAYER(getlayerless800)
                # return True

            GEN.COM('editor_page_close')
        self.step_name = before_step
        GEN.OPEN_STEP(self.step_name, job=self.job_name)
        checklp = "checklist_prelp"

        GEN.COM('chklist_open,chklist=%s' % checklp)
        GEN.COM('chklist_show,chklist=%s,nact=1,pinned=yes,pinned_enabled=yes' % checklp)
        return True

    def check_dis_fill_with_no_fill(self, drill_layer, inputlayer):
        """
        塞孔的孔与非塞孔的孔的距离检查
        :param drill_layer: 钻孔层
        :param inputlayer: 需塞孔层
        :return:False（不符合规范） True（没有满足条件的钻孔）或者返回小于0.8mm的层别
        """
        nofilldrl = '__nofilldrl__'
        tmpfill1 = '__tmpfilllessthan500__'
        tmpfill2 = '__tmpfill500to800__'
        GEN.DELETE_LAYER(nofilldrl)
        GEN.DELETE_LAYER(tmpfill1)
        GEN.DELETE_LAYER(tmpfill2)

        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(drill_layer, 'yes')
        GEN.FILTER_RESET()
        GEN.COM('adv_filter_reset,filter_name=popup')
        GEN.SEL_REF_FEAT(inputlayer, 'disjoint')
        if int(GEN.GET_SELECT_COUNT()) > 0:
            GEN.SEL_COPY(nofilldrl)
        else:
            return True
        # === 目前仅有两个维度，不使用计算的方式，直接加大进行判断
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(nofilldrl, 'yes')
        GEN.SEL_COPY(tmpfill1)
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(tmpfill1, 'yes')
        GEN.CHANGE_UNITS('mm')
        # === 增加删除板外孔的动作，孔径缩小5微米，过滤选择板外孔，删除处理
        GEN.SEL_RESIZE(-5)
        GEN.FILTER_RESET()
        GEN.FILTER_SET_PRO('out')
        GEN.FILTER_SELECT()
        if int(GEN.GET_SELECT_COUNT()) > 0:
            GEN.SEL_DELETE()
        GEN.FILTER_RESET()
        GEN.SEL_RESIZE(5)
        # === 略小于1000
        GEN.SEL_RESIZE(999)
        GEN.SEL_REF_FEAT(inputlayer, 'touch')
        if int(GEN.GET_SELECT_COUNT()) > 0:
            GEN.SEL_REVERSE()
            if int(GEN.GET_SELECT_COUNT()) > 0:
                GEN.SEL_MOVE(tmpfill2)
        else:
            GEN.SEL_MOVE(tmpfill2)

        if GEN.LAYER_EXISTS(tmpfill2, job=self.job_name, step=self.step_name) == 'yes':
            GEN.AFFECTED_LAYER(tmpfill2, 'yes')
            # 0.5mm - 0.8mm  1600-999
            GEN.SEL_RESIZE(601)
            GEN.SEL_REF_FEAT(inputlayer, 'touch')
            if int(GEN.GET_SELECT_COUNT()) > 0:
                GEN.SEL_REVERSE()
                if int(GEN.GET_SELECT_COUNT()) > 0:
                    GEN.SEL_DELETE()
            else:
                # === 无选塞距离0.5-0.8范围的孔 ===
                GEN.DELETE_LAYER(nofilldrl)
                GEN.DELETE_LAYER(tmpfill2)
                GEN.DELETE_LAYER(tmpfill1)
                return True
        else:
            GEN.DELETE_LAYER(nofilldrl)
            return True

        # === tmpfill1层别中是否有物件，如果有则退出
        dogetSym = GEN.DO_INFO('-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, self.step_name, tmpfill1))
        if len(dogetSym["gSYMS_HISTsymbol"]) != 0:
            M = M_Box()
            showText = M.msgText(u'提示', u"选塞距离小于0.5mm，请检查%s 层别!" % tmpfill1, showcolor='red')
            M.msgBox(showText)
            # return False
        else:
            GEN.DELETE_LAYER(tmpfill1)
        GEN.DELETE_LAYER(nofilldrl)

        return tmpfill2

    def prechecklp(self, drill_layer, lp_layer):
        GEN.CHANGE_UNITS('mm')
        GEN.CLEAR_LAYER()
        # === 判断树脂铝片层是否存在，不存在则创建，存在则清空 ===
        #  TODO === 另外一种方案是lp层改名成sz.lp
        if GEN.LAYER_EXISTS('remove_' + lp_layer, job=self.job_name, step=self.step_name) == 'yes':
            M = M_Box()
            showText = M.msgText(u'提示', u"层别%s存在，请确认如需继续需还原%s为正式层别,程序退出!" %
                                 ('remove_' + lp_layer, 'remove_' + lp_layer), showcolor='red')
            M.msgBox(showText)
            return False
        elif GEN.LAYER_EXISTS(lp_layer, job=self.job_name, step=self.step_name) == 'yes':
            GEN.AFFECTED_LAYER(lp_layer, 'yes')
            GEN.SEL_DELETE()
            GEN.CLEAR_LAYER()
        else:
            GEN.CREATE_LAYER(lp_layer, ins_lay=drill_layer, context='board', add_type='drill')
        for sm in self.smlist:
            self.lpdict[sm] = {}
            # 检测是top面soldermask还是bot面soldermask
            glyrside = GEN.DO_INFO("-t layer -e %s/%s/%s -d SIDE" % (self.job_name, self.step_name, sm))
            if glyrside['gSIDE'] == 'top' or glyrside['gSIDE'] == 'bottom':
                self.lpdict[sm]['SIDE'] = glyrside['gSIDE']
            else:
                M = M_Box()
                showText = M.msgText(u'提示', u"获取防焊层%s面次失败,程序退出!" % sm, showcolor='red')
                M.msgBox(showText)
                return False
            # 生成辅助层别
            self.lpdict[sm]['smtmp'] = self.makeCopylayer(sm, lp_layer)
            self.lpdict[sm]['drltmp'] = self.makeCopylayer(drill_layer, sm)
            GEN.CLEAR_LAYER()
            GEN.AFFECTED_LAYER(self.lpdict[sm]['smtmp'], 'yes')
            # 整体化临时防焊层，用于去除负片
            GEN.COM(
                'sel_contourize, accuracy = 0.1, break_to_islands = yes, clean_hole_size = 3, clean_hole_mode = x_or_y')
            GEN.AFFECTED_LAYER(self.lpdict[sm]['smtmp'], 'no')
            # 选出此防焊面次未开窗的钻孔
            GEN.AFFECTED_LAYER(self.lpdict[sm]['drltmp'], 'yes')
            GEN.FILTER_RESET()
            GEN.SEL_REF_FEAT(self.lpdict[sm]['smtmp'], 'cover')
            if int(GEN.GET_SELECT_COUNT()) > 0:
                GEN.SEL_DELETE()
            GEN.SEL_REVERSE()
            noopennum = int(GEN.GET_SELECT_COUNT())
            if noopennum > 0:
                self.lpdict[sm]['filloilnum'] = noopennum
            GEN.CLEAR_LAYER()

        # 定义变量，防焊面次数量
        smside = 1
        fillnum = 0
        onelayer = "__signaloil__"
        twolayer = "__twiceoil__"
        GEN.DELETE_LAYER(onelayer)
        GEN.DELETE_LAYER(twolayer)
        # 判断防焊层数量，获取半塞孔层 __signaloil__
        if len(self.lpdict) == 1:
            # 单面防焊存在
            smside = 1
            if (self.lpdict[self.smlist[0]]['filloilnum'] - self.lpdict[self.smlist[0]]['halftouchnum'] == 0) or \
                    self.lpdict[self.smlist[0]][
                        'filloilnum'] == 0:
                M = M_Box()
                showText = M.msgText(u'提示', u"Info002：单面防焊层，且无需塞孔，程序退出!", showcolor='green')
                M.msgBox(showText)
                return
            else:
                fillnum = self.lpdict[self.smlist[0]]['filloilnum'] + self.lpdict[self.smlist[0]]['halftouchnum']
                GEN.AFFECTED_LAYER(self.lpdict[self.smlist[0]]['drltmp'], 'yes')
                GEN.COPY_LAYER(onelayer)
                GEN.CLEAR_LAYER()
        elif len(self.lpdict) == 2:
            # 初步判断双面防焊存在，继续判断是否两面防焊
            smsidelist = [self.lpdict[self.smlist[0]]['SIDE'], self.lpdict[self.smlist[1]]['SIDE']]
            smsidelist = list(set(smsidelist))
            smside = len(smsidelist)
            oneSideLayer, twoSideLayer = self.seperateLayer(self.lpdict[self.smlist[0]]['drltmp'],
                                                            self.lpdict[self.smlist[1]]['drltmp'])
            print 'oneSideLayer %s, twoSideLayer %s' % (oneSideLayer, twoSideLayer)
            # GEN.PAUSE('xxxx')
            if oneSideLayer is None and twoSideLayer is None:
                M = M_Box()
                showText = M.msgText(u'提示', u"Info005:没有需要塞孔的钻孔，程序退出？!", showcolor='red')
                M.msgBox(showText)
                return False
            # 当两层防焊同时存在且为同面次时，合并两层到onelayer
            if smside == 1:
                GEN.CLEAR_LAYER()
                # 无需塞孔判断
                if oneSideLayer:
                    GEN.AFFECTED_LAYER(oneSideLayer, 'yes')
                if twoSideLayer:
                    GEN.AFFECTED_LAYER(twoSideLayer, 'yes')
                GEN.SEL_COPY(onelayer)
                GEN.CLEAR_LAYER()
                if oneSideLayer: GEN.DELETE_LAYER(oneSideLayer)
                if twoSideLayer: GEN.DELETE_LAYER(twoSideLayer)
            elif smside == 2:
                # 当两层防焊同时存在且为两面次时，分离层别到onelayer及twolayer
                GEN.CLEAR_LAYER()
                if oneSideLayer:
                    GEN.AFFECTED_LAYER(oneSideLayer, 'yes')
                    GEN.SEL_COPY(onelayer)
                    GEN.CLEAR_LAYER()
                if oneSideLayer: GEN.DELETE_LAYER(oneSideLayer)
                GEN.CLEAR_LAYER()
                if twoSideLayer:
                    GEN.AFFECTED_LAYER(twoSideLayer, 'yes')
                    GEN.SEL_COPY(twolayer)
                    GEN.CLEAR_LAYER()
                if twoSideLayer: GEN.DELETE_LAYER(twoSideLayer)
        elif len(self.lpdict) == 3:
            # 程序获取了三层防焊，提醒用户
            smsidelist = [self.lpdict[self.smlist[0]]['SIDE'], self.lpdict[self.smlist[1]]['SIDE'],
                          self.lpdict[self.smlist[2]]['SIDE']]
            smsidelist = list(set(smsidelist))
            smside = len(smsidelist)
            M = M_Box()
            showText = M.msgText(u'提示', u"Error003：程序获取了三层防焊，程序退出!", showcolor='red')
            M.msgBox(showText)
            exit(0)
        else:
            M = M_Box()
            showText = M.msgText(u'提示', u"Error002：程序获取防焊层超过3层，程序退出!", showcolor='red')
            M.msgBox(showText)
            exit(0)

        # 判断半塞孔层是否存在
        if GEN.LAYER_EXISTS(onelayer, job=self.job_name, step=self.step_name) == 'yes':
            # === 增加半塞孔需要做防焊透光点的方式 ===
            if self.ui.checkBox.isChecked():
                self.make_tgpoint(onelayer)

        GEN.DELETE_LAYER(self.tmplp)
        GEN.CLEAR_LAYER()
        filloilexist = 'no'
        if GEN.LAYER_EXISTS(onelayer, job=self.job_name, step=self.step_name) == 'yes':
            GEN.AFFECTED_LAYER(onelayer, 'yes')
            filloilexist = 'yes'
        if GEN.LAYER_EXISTS(twolayer, job=self.job_name, step=self.step_name) == 'yes':
            GEN.AFFECTED_LAYER(twolayer, 'yes')
            filloilexist = 'yes'
        if filloilexist == 'yes':
            GEN.SEL_COPY(self.tmplp)
        else:
            M = M_Box()
            showText = M.msgText(u'提示', u"Info004:没有需要塞孔的钻孔？!", showcolor='red')
            M.msgBox(showText)
            return False
        GEN.CLEAR_LAYER()

        GEN.DELETE_LAYER(onelayer)
        GEN.DELETE_LAYER(twolayer)
        return True

    def mvhole_withattr(self, sourcelayer, orgSymSize, desSymSize, destlayer, invertyorn='no', attr='tg_point'):
        """
        通过中间辅助层，进行大小变更，移动到目标层
        :param sourcelayer:
        :param orgSymSize:
        :param desSymSize:
        :param destlayer:
        :param invertyorn:
        :param attr:
        :return:
        """
        mytmplayer = '__tmpchangehole__'
        GEN.DELETE_LAYER(mytmplayer)
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(sourcelayer, 'yes')
        GEN.FILTER_RESET()
        GEN.FILTER_SET_INCLUDE_SYMS('r%s' % orgSymSize)
        GEN.FILTER_SELECT()
        if int(GEN.GET_SELECT_COUNT()) == 0:
            M = M_Box()
            showText = M.msgText(u'提示', u"Error：2001 有没有搞错，怎么会选不到呢!", showcolor='red')
            M.msgBox(showText)
            return False
        GEN.SEL_MOVE(mytmplayer)
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(mytmplayer, 'yes')
        GEN.SEL_CHANEG_SYM('r%s' % desSymSize)
        GEN.COM('cur_atr_set, attribute =.bit, text = %s' % attr)
        GEN.COM('sel_change_atr, mode = add')

        GEN.SEL_COPY(destlayer, invert=invertyorn)
        GEN.DELETE_LAYER(mytmplayer)
        GEN.CLEAR_LAYER()
        return

    def check_touch_drill(self, check_layer, rout_dis=200, close_hole_dis=500, op_chk_layer='no'):
        """
        分析钻孔间距，需要时导出分析结果层别
        :param check_layer:
        :param rout_dis:
        :param close_hole_dis:
        :param op_chk_layer:
        :return:
        """
        GEN.CHANGE_UNITS('mm')
        checklp = "checklist_prelp"
        GEN.CLEAR_LAYER()
        GEN.COM('matrix_layer_type, job=%s, matrix=matrix, layer=%s, type=drill' % (self.job_name, check_layer))
        GEN.AFFECTED_LAYER(check_layer, 'yes')
        GEN.VOF()
        GEN.COM("chklist_delete, chklist = %s" % checklp)
        GEN.VON()
        GEN.COM("chklist_create,chklist=%s" % checklp)
        GEN.COM("chklist_show,chklist=%s" % checklp)
        GEN.COM("chklist_single,action=valor_analysis_drill,show=yes")
        GEN.COM("chklist_pclear")
        GEN.COM("chklist_cupd,chklist=valor_analysis_drill,nact=1,params="
                "((pp_drill_layer=.affected)(pp_rout_distance=200)(pp_tests=Hole Separation)(pp_extra_hole_type=Pth\;Via)"
                "(pp_use_compensated_rout=Skeleton)),mode=regular")
        GEN.COM("chklist_pcopy,chklist=valor_analysis_drill,nact=1")
        GEN.COM("chklist_ppaste,chklist=%s,row=0" % checklp)
        GEN.COM("chklist_cupd,chklist=%s,nact=1,params=((pp_drill_layer=.affected)"
                "(pp_rout_distance=%s)(pp_tests=Hole Separation)(pp_extra_hole_type=Pth\;Via)"
                "(pp_use_compensated_rout=Skeleton)),mode=regular" % (checklp, rout_dis))
        # === 近孔分析距离应用为变量，由于树脂塞孔的分析距离为2000，其他近孔不做此距离分析，避免影响效率
        GEN.COM("chklist_erf_variable, chklist=checklist_prelp, nact=1, variable=close_hole_dist,value=%s, options=0"
                % close_hole_dis)
        # === 自由放大最大分析区间 ===
        GEN.COM("chklist_erf_range,chklist=checklist_prelp,nact=1,redisplay=0,category=closeh,"
                "erf=drlcheck,range=304.8\;381\;%s" % close_hole_dis)
        # === 以下语句应该在Genesis下不可用,Genesis中由ERF控制，近孔不做区分
        GEN.COM("chklist_erf_variable, chklist=checklist_prelp, nact=1, "
                "variable=v_report_detailed_close_holes, value=0, options=0")
        GEN.COM("chklist_run,chklist=%s,nact=1,area=global" % checklp)
        GEN.COM("chklist_show,chklist=%s" % checklp)

        get_info_status = GEN.DO_INFO(
            "-t check -e %s/%s/%s  -d STATUS  -o action=1" % (self.job_name, self.step_name, checklp))
        if get_info_status['gSTATUS'] != 'DONE':
            M = M_Box()
            showText = M.msgText(u'提示', u"%s分析错误，请反馈程序课" % check_layer, showcolor='red')
            M.msgBox(showText)

        min_close_hole = ''
        # checkiftouchh = 'no'
        # checkifoverlap = 'no'
        # === 取分析结果 ===
        # === 增加是否有结果的判断 2020.10.23===
        get_info_result = GEN.DO_INFO(
            "-t check -e %s/%s/%s -d CHK_ATTR -o action=1, units=mm" % (self.job_name, self.step_name, checklp))
        # === 循环取值
        for index, name in enumerate(get_info_result['gCHK_ATTRname']):
            if name == 'min_closeh':
                min_close_hole = get_info_result['gCHK_ATTRval'][index]
                if get_info_result['gCHK_ATTRval'][index] == 'N/A':
                    # 当无结果时，赋较大值
                    min_close_hole = '9999'
                    # M = M_Box ()
                    # showText = M.msgText (u'提示', u"%s间距分析未分析到近孔数据，按无近孔处理!\n如分析错误，请反馈程序课" % check_layer , showcolor='green')
                    # M.msgBox (showText)
                    # TODO 如果为分析报错，后续添加此种判断
            if name == 'num_touchh' and get_info_result['gCHK_ATTRval'][index] != '0':
                min_close_hole = '0'
                break
                # checkiftouchh = 'yes'
            # ==== 增加重孔的判断，此处可能为程序运行异常
            if name == 'num_duph' and get_info_result['gCHK_ATTRval'][index] != '0':
                min_close_hole = '0'
                break
            if name == 'min_overlap_width' and get_info_result['gCHK_ATTRval'][index] != 'N/A':
                min_close_hole = '0'
                break
                # checkifoverlap = 'yes'
        if op_chk_layer == "yes" and float(min_close_hole) < close_hole_dis:
            GEN.COM("chklist_create_lyrs,chklist=checklist_prelp,severity=3,suffix=%s" % check_layer)
            if GEN.LAYER_EXISTS('mk_1_%s_%s' % (check_layer, check_layer), job=self.job_name,
                                step=self.step_name) == 'yes':
                # === 有用的是ms_1_*层别，此处删除无用层别
                GEN.DELETE_LAYER('mk_1_%s_%s' % (check_layer, check_layer))
            else:
                M = M_Box()
                showText = M.msgText(u'提示', u"%s分析结果导出失败，请反馈程序课" % check_layer, showcolor='red')
                M.msgBox(showText)

        return min_close_hole
        # get_info_result['gCHK_ATTRname'] = 'min_closeh'
        # get_info_result['gCHK_ATTRname'] = 'num_touchh'
        # get_info_result['gCHK_ATTRname'] = 'min_overlap_width'

    def deal_with_split_sz(self, inputlayer, drill_layer, iplplist):
        # === 先做层别回归处理，处理分T的情形
        pre_splitlayer = '__tmpsplitlayer__'
        tmp_szsk1 = '__tmp_szsk1__'
        tmp_szsk2 = '__tmp_szsk2__'
        GEN.DELETE_LAYER(pre_splitlayer)
        chg_tmp_layer = self.change_to_normal_drill_size(inputlayer, iplplist, tmp_layer=pre_splitlayer)
        # === 判断选塞距离，根据不同距离进行归类判断
        # === 塞孔的孔与非塞孔的孔的距离检查 ===
        getlayerless800 = self.check_dis_fill_with_no_fill(drill_layer, chg_tmp_layer)
        all_above_800 = 'no'
        if getlayerless800 is False:
            # === 过程中有错误抛出 ===
            return False
        elif getlayerless800 is True:
            all_above_800 = 'yes'
        # else:

        # === 对已经处理好的层别取最小值，孔径与最小值差值小于0.2的部分移到分孔1、其余移到分孔2，
        dogetSym = GEN.DO_INFO(
            '-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, self.step_name, chg_tmp_layer))
        gsymlist = [self.stringtonum(i.strip('r')) for i in dogetSym["gSYMS_HISTsymbol"]]
        gsymlist = list(set(gsymlist))
        min_drill = min(gsymlist)
        GEN.CLEAR_LAYER()
        GEN.FILTER_RESET()
        GEN.COM('adv_filter_reset,filter_name=popup')
        GEN.AFFECTED_LAYER(chg_tmp_layer, 'yes')
        for tool in gsymlist:
            if tool - min_drill < 200:
                GEN.FILTER_RESET()
                GEN.FILTER_SET_INCLUDE_SYMS('r%s' % tool)
                GEN.FILTER_SELECT()
                if int(GEN.GET_SELECT_COUNT()) > 0:
                    GEN.SEL_MOVE(tmp_szsk1)
                else:
                    M = M_Box()
                    showText = M.msgText(u'提示', u"ERROR:1001 孔径:%s未被选择到!" % tool, showcolor='red')
                    M.msgBox(showText)
                    return False
            elif 200 <= tool - min_drill < 400:
                GEN.FILTER_RESET()
                GEN.FILTER_SET_INCLUDE_SYMS('r%s' % tool)
                GEN.FILTER_SELECT()
                if int(GEN.GET_SELECT_COUNT()) > 0:
                    GEN.SEL_MOVE(tmp_szsk2)
                else:
                    M = M_Box()
                    showText = M.msgText(u'提示', u"ERROR:1002 孔径:%s未被选择到!" % tool, showcolor='red')
                    M.msgBox(showText)
                    return False
            else:
                M = M_Box()
                showText = M.msgText(u'提示', u"%s - %s 极差超过400，规范未定义!" % (tool, min_drill), showcolor='red')
                M.msgBox(showText)
                return False
        # === 分孔结束后，删除临时层别,增加判断是否还有物件 ===
        ttgetSym = GEN.DO_INFO('-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, self.step_name, chg_tmp_layer))
        if len(ttgetSym['gSYMS_HISTsymbol']) != 0:
            M = M_Box()
            showText = M.msgText(u'提示', u"Oh my God，Error015你看到这条消息了么，层别%s未分孔完毕!" % chg_tmp_layer, showcolor='red')
            M.msgBox(showText)
            return False
        else:
            # === 运行完成后回收垃圾层 ===
            GEN.DELETE_LAYER(chg_tmp_layer)

        # === 分别处理分孔1、分孔2
        for i, deal_layer in enumerate([tmp_szsk1, tmp_szsk2]):
            szsk = ''
            if i == 0:
                szsk = 'szsk2-1'
            elif i == 1:
                szsk = 'szsk2-2'
            # === 运行前，清空分孔树脂塞孔层别 ===
            GEN.CLEAR_LAYER()
            if GEN.LAYER_EXISTS(szsk, job=self.job_name, step=self.step_name) == 'yes':
                GEN.AFFECTED_LAYER(szsk, 'yes')
                GEN.SEL_DELETE()
                GEN.CLEAR_LAYER()

            # === 获取孔径信息，是单一孔径还是多孔径
            dogetSym = GEN.DO_INFO('-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, self.step_name, deal_layer))
            gsymlist = [self.stringtonum(i.strip('r')) for i in dogetSym["gSYMS_HISTsymbol"]]
            # 对需做lp的symbol进行归类，考虑区间上下限
            needlplist2 = []
            outrangelist = []
            for tooldrill in gsymlist:
                tmpdict = {}
                for line in self.drill_classify:
                    if float(line['drill_down']) <= float(tooldrill) <= float(line['drill_up']):
                        tmpdict['mode'] = line['mode']
                        tmpdict['trudrill'] = tooldrill
                        tmpdict['pre_size'] = line['tool_mm']
                        tmpdict['tool_lower'] = line['tool_lower']
                        tmpdict['sz_mode1'] = line['sz_mode1']
                        tmpdict['sz_mode2'] = line['sz_mode2']
                        needlplist2.append(tmpdict)
                # 不在区间内的判断
                if not tmpdict:
                    outrangelist.append(tooldrill)
            # 判断需要塞孔的孔径数量
            judge_lp_list = [int(i['tool_lower']) for i in needlplist2]
            judgeMode = list(set(judge_lp_list))
            if len(judgeMode) == 1:
                sz_mode = 1
            else:
                # === 判断极差大小，极差超过0.2mm需区分为2次塞孔
                max_lp_size = max(judge_lp_list)
                min_lp_size = min(judge_lp_list)
                if max_lp_size - min_lp_size >= 200:
                    sz_mode = 2
                    # === 已经进行过一次分孔，不可再分第二次
                    M = M_Box()
                    showText = M.msgText(u'提示', u"需分段塞孔，程序暂未支持!", showcolor='red')
                    M.msgBox(showText)
                    return False
                else:
                    sz_mode = 3
            if sz_mode == 1:
                if all_above_800 == 'yes':
                    self.mvhole(deal_layer, needlplist2[0]['trudrill'], needlplist2[0]['sz_mode1'], szsk)
                else:
                    GEN.CLEAR_LAYER()
                    GEN.AFFECTED_LAYER(deal_layer, 'yes')
                    GEN.FILTER_RESET()
                    GEN.SEL_REF_FEAT(getlayerless800, 'touch')
                    if int(GEN.GET_SELECT_COUNT()) > 0:
                        tmp_resize = int(needlplist2[0]['sz_mode2']) - int(needlplist2[0]['trudrill'])
                        GEN.SEL_MOVE(szsk, size=tmp_resize)
                    # else:
                    #     M = M_Box ()
                    #     showText = M.msgText (u'提示', u"ERROR:1031,区间%s分类错误!" % self.lpmode, showcolor='red')
                    #     M.msgBox (showText)
                    #     return False
                    # === 如果有剩余孔径，均按大于800处理
                    # === 可能存在选塞距离小于800的钻孔均在另一层的情况 ===
                    self.mvhole(deal_layer, needlplist2[0]['trudrill'], needlplist2[0]['sz_mode1'], szsk)
            elif sz_mode == 3:

                GEN.CLEAR_LAYER()
                GEN.AFFECTED_LAYER(deal_layer, 'yes')
                if all_above_800 == 'no':
                    GEN.FILTER_RESET()
                    GEN.SEL_REF_FEAT(getlayerless800, 'touch')
                    if int(GEN.GET_SELECT_COUNT()) > 0:
                        # === D + 4
                        GEN.SEL_MOVE(szsk, size='100')
                    else:
                        M = M_Box()
                        showText = M.msgText(u'提示', u"ERROR:1032,区间%s分类错误!" % self.lpmode, showcolor='red')
                        M.msgBox(showText)
                        return False

                # === 需判断需塞孔的孔径的最小值，再判断属于哪个区间
                dogetSym = GEN.DO_INFO(
                    '-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, self.step_name, deal_layer))
                gsymlist = [self.stringtonum(i.strip('r')) for i in dogetSym["gSYMS_HISTsymbol"]]
                gsymlist = list(set(gsymlist))
                min_drill = min(gsymlist)
                check_exist = 'no'
                for all_item in self.sz_more_t_mode:
                    if str(min_drill) == all_item['min_drill']:
                        check_exist = 'yes'
                        GEN.CLEAR_LAYER()
                        GEN.AFFECTED_LAYER(deal_layer, 'yes')
                        for itool in gsymlist:
                            if all_item[str(itool)]:
                                self.mvhole(deal_layer, itool, all_item[str(itool)], szsk)
                            else:
                                M = M_Box()
                                showText = M.msgText(u'提示', u"ERROR:1006,最小孔径%s对应孔径%s不在规范内!" % (min_drill, itool),
                                                     showcolor='red')
                                M.msgBox(showText)
                                return False
                        GEN.CLEAR_LAYER()
                if check_exist == 'no':
                    M = M_Box()
                    showText = M.msgText(u'提示', u"ERROR:1005,最小孔径%s不在规范内!" % min_drill, showcolor='red')
                    M.msgBox(showText)
                    return False
            tmpgetSym = GEN.DO_INFO('-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, self.step_name, deal_layer))
            tmpsymlist = [self.stringtonum(i.strip('r')) for i in tmpgetSym["gSYMS_HISTsymbol"]]
            if len(tmpsymlist) != 0:
                M = M_Box()
                showText = M.msgText(u'提示', u"ERROR:1041，层别中%s仍存在物件!" % deal_layer, showcolor='red')
                M.msgBox(showText)
                return False
            else:
                # === 删除临时层别 ===
                GEN.DELETE_LAYER(deal_layer)
            # === 检测塞孔层距离 ===
            # === 增加塞孔层的距离检查 ===
            get_lp_dist = self.check_touch_drill(szsk, close_hole_dis=500, op_chk_layer='yes')
            if float(get_lp_dist) <= 50:
                M = M_Box()
                get_decrease_size = self.decrease_hole_size(szsk, 'ms_1_%s_%s' % (szsk, szsk))
                if get_decrease_size is False:
                    showText = M.msgText(u'提示',
                                         u"层别：%s 钻孔距离为%s 微米,不满足50微米的铝片间距，\n运行中未能缩小孔径，请处理!"
                                         % (szsk, get_lp_dist),
                                         showcolor='red')
                else:
                    showText = M.msgText(u'提示',
                                         u"层别：%s 钻孔距离为%s 微米,不满足50微米的铝片间距，\n运行中能缩小孔径%s处，请处理!"
                                         % (szsk, get_lp_dist, get_decrease_size),
                                         showcolor='red')
                M.msgBox(showText)
                # M = M_Box()
                # get_reshape_size = self.decrease_hole_size2drlsize(szsk,'ms_1_%s_%s' % (szsk, szsk), drill_layer,dis_value=50)
                # if get_reshape_size is False:
                #     showText = M.msgText(u'提示',
                #                          u"层别：%s 钻孔距离为%s 微米,不满足50微米的铝片间距，\n运行中未能缩小孔径，请处理!"
                #                          % (szsk, get_lp_dist),
                #                          showcolor='red')
                # else:
                #     showText = M.msgText(u'提示',
                #                          u"层别：%s 钻孔距离为%s 微米,不满足50微米的铝片间距，\n运行中能缩小孔径%s处，请处理!"
                #                          % (szsk, get_lp_dist, get_reshape_size),
                #                          showcolor='red')
                # M.msgBox(showText)
            else:
                GEN.DELETE_LAYER('ms_1_%s_%s' % (szsk, szsk))
            # === 判断树脂塞孔层板边是否有物件，如无，从sz.lp copy ；如果有跳过 ===
            pnlSym = GEN.DO_INFO('-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, 'panel', szsk))
            if len(pnlSym["gSYMS_HISTsymbol"]) != 0:
                # === 已有symbol 不进行处理 ===
                pass
            else:
                if GEN.LAYER_EXISTS('sz.lp', job=self.job_name, step='panel') == 'yes':
                    GEN.COM('open_entity, job=%s, type=step, name=%s ,iconic=%s' % (self.job_name, 'panel', 'no'))
                    GEN.AUX('set_group, group=%s' % GEN.COMANS)
                    GEN.COPY_LAYER(self.job_name, 'panel', 'sz.lp', szsk, mode='replace', invert='no')
                    GEN.COM('editor_page_close')
                    GEN.COM(
                        'open_entity, job=%s, type=step, name=%s ,iconic=%s' % (self.job_name, self.step_name, 'no'))
                    GEN.AUX('set_group, group=%s' % GEN.COMANS)
                else:
                    M = M_Box()
                    showText = M.msgText(u'提示', u"无sz.lp层，\n请自行制作板边，程序继续!", showcolor='red')
                    M.msgBox(showText)
        if all_above_800 == 'no':
            # === 回收垃圾层 ===
            GEN.DELETE_LAYER(getlayerless800)
        if GEN.LAYER_EXISTS('sz.lp', job=self.job_name, step='panel') == 'yes':
            GEN.COM("rename_layer,name=sz.lp,new_name=remove_sz.lp")
        return True

    def deal_with_inner_sz(self, drill_layer):
        # === 循环层别的symbol。判定有多少种孔径，如果超出一种，则程序退出 ===
        # === 板厚判断 >0.6还是<=0.6 ===
        run_step_list = [self.step_name]
        if GEN.STEP_EXISTS(job=self.job_name, step='dzd_cp') == 'yes':
            run_step_list.append('dzd_cp')

        if 'panel' in self.job_step_list:
            # === 获取panel拼版中step ===
            getData = GEN.DO_INFO('-t step -e %s/%s -d SR' % (self.job_name, 'panel'))
            panel_sr_steps = list(set(getData['gSRstep']))
            for ps in panel_sr_steps:
                if ps not in run_step_list and not re.match('drl|b[0-9]|qie_hole_coupon_new_.*', ps):
                    dogetSym = GEN.DO_INFO(
                        '-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, ps, drill_layer))
                    if len(dogetSym["gSYMS_HISTsymbol"]) > 0:
                        run_step_list.append(ps)
        else:
            get_step_list = [i for i in self.job_step_list if
                             not re.match('^orig|net|b[0-9]|panel', i) and i not in run_step_list]
            for ps in get_step_list:
                dogetSym = GEN.DO_INFO(
                    '-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, ps, drill_layer))
                if len(dogetSym["gSYMS_HISTsymbol"]) > 0:
                    run_step_list.append(ps)

        before_step = '%s' % self.step_name
        for current_step in run_step_list:
            self.step_name = current_step
            GEN.OPEN_STEP(step=self.step_name, job=self.job_name)
            cur_thick = self.szpre_drill[drill_layer]['thickness']
            sz_layer = self.szpre_drill[drill_layer]['sz_name']
            GEN.CLEAR_LAYER()
            GEN.CHANGE_UNITS('mm')
            GEN.VOF()
            GEN.AFFECTED_LAYER(sz_layer, 'yes')
            GEN.SEL_DELETE()
            GEN.VON()
            GEN.CLEAR_LAYER()
            dogetSym = GEN.DO_INFO('-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, self.step_name, drill_layer))
            gsymlist = [self.stringtonum(i.strip('r')) for i in dogetSym["gSYMS_HISTsymbol"]]
            # 对需做lp的symbol进行归类，考虑区间上下限
            needlplist = []
            outrangelist = []
            for tooldrill in gsymlist:
                tmpdict = {}
                for line in self.drill_classify:
                    if float(line['drill_down']) <= float(tooldrill) <= float(line['drill_up']):
                        tmpdict['mode'] = line['mode']
                        tmpdict['trudrill'] = tooldrill
                        tmpdict['pre_size'] = line['tool_mm']
                        tmpdict['tool_lower'] = line['tool_lower']
                        tmpdict['sz_mode1'] = line['sz_mode1']
                        tmpdict['sz_mode2'] = line['sz_mode2']
                        needlplist.append(tmpdict)
                # 不在区间内的判断
                if not tmpdict:
                    outrangelist.append(tooldrill)

            if len(outrangelist) != 0:
                s = ' '.join([str(a) for a in outrangelist])
                M = M_Box()
                showText = M.msgText(u'提示', u"孔径:%s超出可塞孔区间范围!" % s, showcolor='red')
                M.msgBox(showText)
                return False

            if len(list(set([i['pre_size'] for i in needlplist]))) > 2:
                M = M_Box()
                showText = M.msgText(u'提示', u"内埋孔%s铝片暂不支持三种孔径，请确认!" % drill_layer, showcolor='red')
                M.msgBox(showText)
                return False

            # ===  板厚在0.3~0.6mm范围内才考虑孔距
            if 0.25 <= float(cur_thick) <= 0.6:
                # === TODO 测试简化制作步骤 开始===
                chg_tmp_layer = self.change_to_normal_drill_size(drill_layer, needlplist, des_key='tool_lower')
                GEN.CLEAR_LAYER()
                GEN.AFFECTED_LAYER(chg_tmp_layer, 'yes')
                # GEN.SEL_MOVE(sz_layer, size='150')
                GEN.SEL_MOVE(sz_layer, size='100')
                GEN.CLEAR_LAYER()
                # === TODO 测试简化制作步骤 结束===

                # get_min_dist = self.check_touch_drill(drill_layer, rout_dis=10, close_hole_dis=2000, op_chk_layer='yes')
                # # === 建立临时层别，第一步用于把分T的孔径处理成标准孔径大小，避免铝片层别分T。
                # chg_tmp_layer = self.change_to_normal_drill_size(drill_layer, needlplist, des_key='tool_lower')
                # print get_min_dist
                # if float(get_min_dist) > 2000:
                #     # === 选择不考虑距离的处理方式，规则使用D + 100
                #     GEN.CLEAR_LAYER()
                #     GEN.AFFECTED_LAYER(chg_tmp_layer, 'yes')
                #     # GEN.SEL_MOVE(sz_layer, size='150')
                #     GEN.SEL_MOVE(sz_layer, size='100')
                #     GEN.CLEAR_LAYER()
                # elif GEN.LAYER_EXISTS('ms_1_%s_%s' % (drill_layer, drill_layer), job=self.job_name,
                #                       step=self.step_name) == 'yes':
                #     # === 区分2.0mm范围内的孔及范围外的孔，应用不同规则
                #     chk_result_lyr = 'ms_1_%s_%s' % (drill_layer, drill_layer)
                #     GEN.CLEAR_LAYER()
                #     GEN.AFFECTED_LAYER(chk_result_lyr, 'yes')
                #     # GEN.FILTER_RESET()
                #     GEN.SEL_CHANEG_SYM('r0.1')
                #     GEN.FILTER_RESET()
                #     GEN.COM('adv_filter_reset,filter_name=popup')
                #     # === V1.3 仅保留线长为75微米的分析值 ===
                #     # === 以下语句需要加上线宽，不知道76.2微米的线宽是否为固定值，更改为过滤线长 ===
                #     GEN.FILTER_SET_TYP('line')
                #     GEN.FILTER_TEXT_ATTR('.string', 'closeh')
                #     GEN.COM('adv_filter_set,filter_name=popup,update_popup=yes,bound_box=yes,min_width=0,max_width=0,'
                #             'min_length=0,max_length=%s' % '0.076')
                #     GEN.FILTER_SELECT()
                #
                #     GEN.SEL_REVERSE()
                #     if int(GEN.GET_SELECT_COUNT()) > 0:
                #         GEN.SEL_DELETE()
                #     GEN.VOF()
                #     GEN.COM('sel_extend_slots, mode=ext_to, size=75,from=center')
                #     GEN.VON()
                #
                #     GEN.CLEAR_LAYER()
                #     GEN.AFFECTED_LAYER(chg_tmp_layer, 'yes')
                #     GEN.FILTER_RESET()
                #     GEN.PAUSE('xxxxxxxxxxxxxx')
                #     # === 钻孔层碰到此层的，为近孔，
                #     GEN.SEL_REF_FEAT(chk_result_lyr, 'touch')
                #     if int(GEN.GET_SELECT_COUNT()) > 0:
                #         GEN.SEL_MOVE(sz_layer, size='50')
                #     GEN.SEL_REVERSE()
                #     if int(GEN.GET_SELECT_COUNT()) > 0:
                #         GEN.SEL_COPY(sz_layer, size='100')
                #     # === 清除垃圾层
                #     GEN.DELETE_LAYER(chk_result_lyr)
                #     GEN.CLEAR_LAYER()
                # else:
                #     M = M_Box()
                #     showText = M.msgText(u'提示', u"未在checklist中成功导出层别%s分析结果!" % drill_layer, showcolor='red')
                #     M.msgBox(showText)
                # === 回收临时层别
                GEN.DELETE_LAYER(chg_tmp_layer)

            elif 0.6 < float(cur_thick) <= 3.0:
                # === 板厚大于0.6mm小于3.0mm的情形,内埋钻不需要考虑选塞距离问题
                tmp_use_layer = '__tmpinner_drill__'
                GEN.CLEAR_LAYER()
                GEN.AFFECTED_LAYER(drill_layer, 'yes')
                GEN.SEL_COPY(tmp_use_layer)
                GEN.CLEAR_LAYER()
                for drill_line in needlplist:
                    self.mvhole(tmp_use_layer, drill_line['trudrill'], drill_line['sz_mode1'], sz_layer)
                GEN.CLEAR_LAYER()
                tmpgetSym = GEN.DO_INFO(
                    '-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, self.step_name, tmp_use_layer))
                tmpsymlist = [self.stringtonum(i.strip('r')) for i in tmpgetSym["gSYMS_HISTsymbol"]]
                if len(tmpsymlist) != 0:
                    M = M_Box()
                    showText = M.msgText(u'提示', u"ERROR:1141，层别中%s仍存在物件!" % tmp_use_layer, showcolor='red')
                    M.msgBox(showText)
                    return False
                else:
                    # === 回收临时层别 ===
                    GEN.DELETE_LAYER(tmp_use_layer)
            else:
                M = M_Box()
                showText = M.msgText(u'提示', u"目前板厚%s,不在规范中定义0.3mm-3.0mm区间!" % cur_thick, showcolor='red')
                M.msgBox(showText)
                return False

            # === 增加塞孔层别距离分析 ===
            get_lp_dist = self.check_touch_drill(sz_layer, close_hole_dis=500, op_chk_layer='yes')
            if float(get_lp_dist) <= 50:
                M = M_Box()
                get_decrease_size = self.decrease_hole_size(sz_layer, 'ms_1_%s_%s' % (sz_layer, sz_layer))
                if get_decrease_size is False:
                    showText = M.msgText(u'提示',
                                         u"层别：%s 钻孔距离为%s 微米,不满足50微米的铝片间距，\n运行中未能缩小孔径，请处理!"
                                         % (sz_layer, get_lp_dist),
                                         showcolor='red')
                else:
                    showText = M.msgText(u'提示',
                                         u"层别：%s 钻孔距离为%s 微米,不满足50微米的铝片间距，\n运行中能缩小孔径%s处，请处理!"
                                         % (sz_layer, get_lp_dist, get_decrease_size),
                                         showcolor='red')
                M.msgBox(showText)
                # M = M_Box()
                # get_reshape_size = self.decrease_hole_size2drlsize(sz_layer,'ms_1_%s_%s' % (sz_layer, sz_layer),drill_layer,dis_value=50,des_key='tool_lower')
                # if get_reshape_size is False:
                #     showText = M.msgText(u'提示',
                #                          u"层别：%s 钻孔距离为%s 微米,不满足50微米的铝片间距，\n运行中未能缩小孔径，请处理!"
                #                          % (sz_layer, get_lp_dist),
                #                          showcolor='red')
                # else:
                #     showText = M.msgText(u'提示',
                #                          u"层别：%s 钻孔距离为%s 微米,不满足50微米的铝片间距，\n运行中能缩小孔径%s处，请处理!"
                #                          % (sz_layer, get_lp_dist, get_reshape_size),
                #                          showcolor='red')
                # M.msgBox(showText)
            endgetSym = GEN.DO_INFO('-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, self.step_name, sz_layer))
            if len(endgetSym['gSYMS_HISTsymbol']) > 2:
                M = M_Box()
                showText = M.msgText(u'提示', u"Step:%s 层别:%s，孔径超出2种，当前为：%s!" % (self.step_name, sz_layer,','.join(endgetSym['gSYMS_HISTsymbol'])),
                                     showcolor='red')
                M.msgBox(showText)
            GEN.COM('editor_page_close')
        self.step_name = before_step
        GEN.OPEN_STEP(step=self.step_name, job=self.job_name)
        checklp = "checklist_prelp"

        GEN.COM('chklist_open,chklist=%s' % checklp)
        GEN.COM('chklist_show,chklist=%s,nact=1,pinned=yes,pinned_enabled=yes' % checklp)

        return True

    def change_to_normal_drill_size(self, drill_layer, needlplist, tmp_layer='__tmpinnnerdrill__',des_key='pre_size'):
        """
        分T以及非标钻咀转换为标准钻咀
        :param drill_layer: 钻孔层
        :param needlplist: 需塞孔的孔径列表
        :param tmp_layer: 临时层
        :param des_key: pre_size 是包含225的钻咀， tool_lower 是 50的倍数钻咀
        :return:
        """
        GEN.CLEAR_LAYER()
        # tmp_layer = '__tmpinnnerdrill__'
        GEN.DELETE_LAYER(tmp_layer)
        GEN.AFFECTED_LAYER(drill_layer, 'yes')
        GEN.SEL_COPY(tmp_layer)
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(tmp_layer, 'yes')
        for tool in needlplist:
            GEN.FILTER_RESET()
            GEN.COM('adv_filter_reset,filter_name=popup')
            GEN.FILTER_SET_INCLUDE_SYMS('r%s' % tool['trudrill'])
            GEN.FILTER_SELECT()
            if int(GEN.GET_SELECT_COUNT()) > 0:
                GEN.SEL_CHANEG_SYM('r' + tool[des_key])
        GEN.FILTER_RESET()
        GEN.CLEAR_LAYER()
        return tmp_layer

    def decrease_hole_size(self, change_layer, mk_layer, decrease_value=50):
        """
        根据分析结果的mark层更改输入孔径的大小，目前缩小孔径，缩小50微米
        :param change_layer:
        :param mk_layer:
        :return:
        """
        select_value = float(decrease_value) / 1000 + 0.001

        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(mk_layer, 'yes')
        # === 更改所有测点为0.1微米
        GEN.SEL_CHANEG_SYM('r0.1')
        GEN.FILTER_RESET()
        GEN.COM('adv_filter_reset,filter_name=popup')
        # === 以下语句需要加上线宽，不知道76.2微米的线宽是否为固定值，更改为过滤线长 ===
        GEN.COM('adv_filter_set,filter_name=popup,update_popup=yes,bound_box=yes,min_width=0,max_width=0,'
                'min_length=0,max_length=%s' % select_value)
        GEN.FILTER_SET_TYP('line')
        GEN.FILTER_TEXT_ATTR('.string', 'closeh')
        GEN.FILTER_SELECT()
        GEN.FILTER_RESET()
        GEN.COM('adv_filter_reset,filter_name=popup')
        GEN.FILTER_TEXT_ATTR('.string', 'overlap_width')
        GEN.FILTER_SELECT()
        if int(GEN.GET_SELECT_COUNT()) > 0:
            GEN.SEL_REVERSE()
            if int(GEN.GET_SELECT_COUNT()) > 0:
                GEN.SEL_DELETE()
        else:
            return False

        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(change_layer, 'yes')
        GEN.FILTER_RESET()
        GEN.COM('adv_filter_reset,filter_name=popup')
        GEN.SEL_REF_FEAT(mk_layer, 'touch')
        change_num = int(GEN.GET_SELECT_COUNT())
        if change_num > 0:
            GEN.SEL_RESIZE('-%s' % decrease_value)
        else:
            return False
        GEN.CLEAR_LAYER()

        return change_num

    def decrease_hole_size2drlsize(self, change_layer, mk_layer, drl_layer, dis_value=75,des_key='pre_size'):
        """
        V1.1根据分析结果的mark层更改输入孔径的大小，更改为和钻孔等大
        :param change_layer:
        :param mk_layer:分析生成的图层
        :param drl_layer:钻孔层
        :return:
        """
        tmp_layer = '__change_sz2drlsize__'
        tmp2_layer = '__tmp_hole_size__'
        GEN.DELETE_LAYER(tmp_layer)
        GEN.DELETE_LAYER(tmp2_layer)
        select_value = float(dis_value) / 1000 + 0.001
        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(mk_layer, 'yes')
        # === 更改所有测点为0.1微米
        GEN.SEL_CHANEG_SYM('r0.1')
        GEN.FILTER_RESET()
        GEN.COM('adv_filter_reset,filter_name=popup')
        # === 以下语句需要加上线宽，不知道76.2微米的线宽是否为固定值，更改为过滤线长 ===
        GEN.COM('adv_filter_set,filter_name=popup,update_popup=yes,bound_box=yes,min_width=0,max_width=0,'
                'min_length=0,max_length=%s' % select_value)
        GEN.FILTER_SET_TYP('line')
        GEN.FILTER_TEXT_ATTR('.string', 'closeh')
        GEN.FILTER_SELECT()
        GEN.FILTER_RESET()
        GEN.COM('adv_filter_reset,filter_name=popup')
        GEN.FILTER_TEXT_ATTR('.string', 'overlap_width')
        GEN.FILTER_SELECT()
        if int(GEN.GET_SELECT_COUNT()) > 0:
            GEN.SEL_REVERSE()
            if int(GEN.GET_SELECT_COUNT()) > 0:
                GEN.SEL_DELETE()
        else:
            return False

        GEN.CLEAR_LAYER()
        GEN.AFFECTED_LAYER(change_layer, 'yes')
        GEN.FILTER_RESET()
        GEN.COM('adv_filter_reset,filter_name=popup')
        GEN.SEL_REF_FEAT(mk_layer, 'touch')
        change_num = int(GEN.GET_SELECT_COUNT())
        if change_num > 0:
            # GEN.SEL_RESIZE('-%s' % decrease_value)
            GEN.SEL_MOVE(tmp_layer)
        else:
            return False
        GEN.CLEAR_LAYER()
        GEN.FILTER_RESET()
        GEN.AFFECTED_LAYER(drl_layer, 'yes')
        GEN.SEL_REF_FEAT(tmp_layer, 'touch')
        get_num = int(GEN.GET_SELECT_COUNT())
        if get_num == change_num:
            GEN.SEL_COPY(tmp2_layer)
            GEN.DELETE_LAYER(tmp_layer)
            dogetSym = GEN.DO_INFO('-t layer -e %s/%s/%s -d SYMS_HIST' % (self.job_name, self.step_name, tmp2_layer))
            gsymlist = [self.stringtonum(i.strip('r')) for i in dogetSym["gSYMS_HISTsymbol"]]
            # 对需做lp的symbol进行归类，考虑区间上下限
            needlplist = []
            for tooldrill in gsymlist:
                tmpdict = {}
                for line in self.drill_classify:
                    if float(line['drill_down']) <= float(tooldrill) <= float(line['drill_up']):
                        tmpdict['mode'] = line['mode']
                        tmpdict['trudrill'] = tooldrill
                        tmpdict['pre_size'] = line['tool_mm']
                        tmpdict['tool_lower'] = line['tool_lower']
                        tmpdict['sz_mode1'] = line['sz_mode1']
                        tmpdict['sz_mode2'] = line['sz_mode2']
                        needlplist.append(tmpdict)

            # === 更改tmp2_layer层别中的为标准孔径 ===
            tmp3_layer = self.change_to_normal_drill_size(tmp2_layer,needlplist,des_key=des_key)
            GEN.CLEAR_LAYER()
            GEN.AFFECTED_LAYER(tmp3_layer,'yes')
            GEN.SEL_COPY(change_layer)
            GEN.DELETE_LAYER(tmp2_layer)
            GEN.DELETE_LAYER(tmp3_layer)
        else:
            M = M_Box()
            showText = M.msgText(u'警告',
                                 u"层别：%s 钻孔不满足%s微米的铝片间距，\n更改为钻孔孔径时，选择到的数量不相同%s-->%s，需要手动处理层别的：%s的铝片，请处理!"
                                 % (change_layer,change_num,get_num,dis_value,tmp_layer),
                                 showcolor='red')
            M.msgBox(showText)
        GEN.CLEAR_LAYER()

        return change_num

    def main_run(self):

        # === 获取选择到的层别 ===
        # self.ui.tableWidget.selectedItems()
        if len([i.text() for i in self.ui.tableWidget.selectedItems()]) == 0:
            M = M_Box()
            showText = M.msgText(u'提示', u"未选择到层别，重新选择!", showcolor='red')
            M.msgBox(showText)
            return
        for i in self.ui.tableWidget.selectedItems():
            print i.text()
            self.sz_lp.append(str(i.text()))
            if str(i.text()) not in self.szpre_drill:
                M = M_Box()
                showText = M.msgText(u'提示', u"%s仅能选择钻孔层别位置，重新选择!" % i.text(), showcolor='red')
                M.msgBox(showText)
                return

        status_list = []

        for drill_layer in self.sz_lp:
            if self.szpre_drill[drill_layer]['layer_mode'] == 'inner':
                getStatus = self.deal_with_inner_sz(drill_layer)
                self.Write_Log('%s %s' % (getStatus, self.szpre_drill[drill_layer]))
            elif self.szpre_drill[drill_layer]['layer_mode'] == 'outer':
                # 塞孔制作预处理程序，包含单双面塞孔判断，防呆检测
                preStatus = self.prechecklp(drill_layer, self.szpre_drill[drill_layer]['sz_name'])
                # 塞孔更改主程序
                if preStatus:
                    getStatus = self.makelp(self.tmplp, self.szpre_drill[drill_layer]['sz_name'], drill_layer)
                    # === 回收临时层别 ====
                    GEN.DELETE_LAYER(self.tmplp)
                    self.Write_Log('%s %s' % (getStatus, self.szpre_drill[drill_layer]))
                else:
                    getStatus = False
            status_list.append(getStatus)

        if False in status_list:
            M = M_Box()
            showText = M.msgText(u'提示', u"程序运行过程中有异常抛出，程序退出!", showcolor='red')
            M.msgBox(showText)
        else:
            GEN.DELETE_LAYER(self.tmplp)
            M = M_Box()
            showText = M.msgText(u'提示', u"程序运行完成，请检查!", showcolor='green')
            M.msgBox(showText)

        self.close()
        exit(0)

    # --记录日志
    def Write_Log(self, log_msg):
        """
        记录日志文件至tmp盘
        :param log_msg: 传入的日志信息
        :return: None
        """
        import time
        now_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))

        # --开始执行转换
        try:
            log_msg = (str(now_time) + u'：' + log_msg)
        except:
            log_msg = log_msg
        # --打印Log
        print(log_msg)

        # --是否打印至文本
        if self.logFile is not None:
            f = open(self.logFile, 'a')
            f.write(log_msg + '\n')
            f.close()


# # # # --程序入口
if __name__ == "__main__":
    # 名词解释：半塞孔即为单面塞孔
    app = QtGui.QApplication(sys.argv)
    myapp = MainWindowShow()
    myapp.show()
    app.exec_()
    sys.exit(0)

"""
版本：V1.0.0
作者：宋超
日期：2020.11.11
说明：
新增程序，为HDI埋孔及通孔树脂塞孔；

版本：V1.0.1
作者：宋超
日期：2020.11.16
说明：
1.增加从inplan获取外层树脂塞孔为否时，界面不显示外层钻孔；
2.增加程序运行日志；
3.铝片距离管控为50微米μm；
4.距离分析中增加重孔的判断；

版本：V1.0.2
作者：宋超
日期：2020.11.19
说明：
1.选塞距离分析时，增加剔除板外孔的动作（一般为成型辅助孔）；

版本：V1.0.3
作者：宋超
日期：2020.11.30
说明：
1.分段树脂塞孔，增加panel中的物件，如果有sz.lp存在则重命名操作；

版本：V1.1
作者：宋超
开发日期：2022.07.06
说明：
1.树脂塞孔间隙管控值0.05mm改为0.075mm http://192.168.2.120:82/zentao/story-view-4397.html；
2.多种树脂塞孔孔径。 http://192.168.2.120:82/zentao/story-view-4398.html

版本：V1.3
作者：宋超
开发日期：2022.09.16
上线如期：2022.10.11
说明：
1.埋孔钻咀的非标钻咀选择 http://192.168.2.120:82/zentao/story-view-4535.html
2.树脂塞孔准则变更。 http://192.168.2.120:82/zentao/story-view-4576.html


版本：V1.4
作者：宋超
开发日期：2022.12.15
上线如期：None
说明：
1.增加step埋孔层塞孔 http://192.168.2.120:82/zentao/story-view-4984.html
"""
