#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:CopyLayer.py
   @author:zl
   @time: 2025/5/29 10:14
   @software:PyCharm
   @desc:
"""
import json
import os
import re
import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import CopyLayerUI_pyqt4 as ui
import platform, random, time

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
    sys.path.append(r"\\192.168.2.33\incam-share\incam\Path\OracleClient_x86\instantclient_11_1")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
import genClasses_zl as gen
from messageBox import msgBox
from mwClass_V4 import AboutDialog


def get_step_layers(name, axis):
    """
    :param name: 料号名
    :param axis: step/layer
    :return: steps/layers
    """
    db1 = '/id/incamp_db1/jobs'
    matrix = os.path.join(db1, name, 'lyr_list', 'matrix')
    print(matrix, axis)
    if os.path.isfile(matrix):
        with open(matrix) as r:
            content = r.read()
        if axis == 'step':
            return re.findall('STEP \{.*?\s+NAME=(\S*)\n.*?\}', content, re.M | re.S)
        else:
            return re.findall('LAYER \{.*?\s+NAME=(\S*)\n.*?\}', content, re.M | re.S)
    else:
        return []


def send_message_to_director(message_result, job_name, label_result, password_approve=False):
    """发送审批结果界面 20221122 by lyh"""
    passwd = str(random.random() * 10000)[:4]
    while "." in passwd:
        passwd = str(random.random() * 10000)[:4]
        time.sleep(0.0001)

    # 验证码接收机器人url
    url = "https://oapi.dingtalk.com/robot/send?access_token=412a2d8e3d567c1be81fcd0912e3b27cfa46a10150863734ae7eefb304a3a4cb"
    if u"重要项目" in message_result:
        url = "https://oapi.dingtalk.com/robot/send?access_token=2049ceb982d2a0abd97528190190a1c171193455965e5f961f837ad6db398571"

    submitData = {
        'site': u'HDI板事业部',
        'job_name': job_name,
        'pass_tpye': 'CAM',
        'pass_level': 8, ""
                         'assign_approve': '83288|51059|84310',
        'pass_title': message_result,
        'oa_approval_result': {"passwd": passwd, "machine_url": url, },
    }

    if password_approve:
        # 验证码主管审批
        Dialog = AboutDialog(label_result, cancel=False, passwdCheck=True, passwd=passwd, appData=submitData,
                             style=None)
    else:
        Dialog = AboutDialog(label_result, cancel=True, appCheck=True, appData=submitData, style=None)
    Dialog.exec_()

    # --根据审批的结果返回值
    if Dialog.selBut in ['x', 'cancel']:
        return False
    if Dialog.selBut == 'ok':
        return True

    return False

def unicode_convert(input):
    """
    用于解决json.load json中带u开头的问题
    :param input:
    :return:
    """
    if isinstance(input, dict):
        new_dict = {}
        for key, value in input.iteritems():
            new_dict[unicode_convert(key)] = unicode_convert(value)
        return new_dict
        # return {unicode_convert (key): unicode_convert (value) for key, value in input.iteritems ()}
    elif isinstance(input, list):
        return [unicode_convert(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input

class CopyLayer(QWidget, ui.Ui_Form):
    def __init__(self):
        super(CopyLayer, self).__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        self.job_name = jobname
        self.user = gen.Top().getUser()
        self.ignore_users = ('106883')   # 忽略限制的用户
        self.step_name = os.environ.get('STEP', None)
        self.job_lock = '%s_job_lock.json' % self.job_name
        # print self.job_name
        PRODUCT = os.environ.get('INCAM_PRODUCT', None)
        if platform.system() == "Windows":
            self.userDir = "%s/fw/jobs/%s/user" % (os.environ.get('GENESIS_DIR', 'D:/genesis'), self.job_name)
        else:
            self.userDir = os.environ.get('JOB_USER_DIR', None)
            if not PRODUCT and not self.userDir:
                # --Linux环境下网络版genesis没有定义INCAM_PRODUCT环境变量
                self.userDir = "%s/fw/jobs/%s/user" % (os.environ.get('GENESIS_DIR', '/genesis'), self.job_name)
        self.pre_lock = self.read_file()
        self.target_jobname = jobname
        self.joblist = [str(job_) for job_ in gen.Top().listJobs()]
        options = ['No', 'Yes', 'New Layers']
        self.comboBox.addItems(options)
        self.comboBox_2.addItems(options)
        self.comboBox_2.setCurrentIndex(2)
        self.lineEdit_job.setText(jobname)
        self.steps = job.matrix.getInfo().get('gCOLstep_name')
        self.target_steps = self.steps
        self.lineEdit_step.setText(self.step_name)
        header = ['Source', 'Destination', 'Invert']
        self.tableWidget.setColumnCount(len(header))
        self.tableWidget.verticalHeader().hide()
        self.tableWidget.setHorizontalHeaderLabels(header)
        self.tableWidget.horizontalHeader().setResizeMode(0, QHeaderView.Stretch)
        self.tableWidget.horizontalHeader().setResizeMode(1, QHeaderView.Stretch)
        self.tableWidget.setItemDelegateForColumn(0, EmptyDelegate(self))
        self.pushButton_select_job.clicked.connect(lambda: self.selectItem('job'))
        self.pushButton_select_step.clicked.connect(lambda: self.selectItem('step'))
        self.pushButton_add_layer.clicked.connect(self.addLayer)
        self.pushButton_remove_layer.clicked.connect(self.clearLayer)
        self.pushButton_ok.clicked.connect(self.run)
        self.pushButton_close.clicked.connect(lambda: sys.exit())
        self.move((app.desktop().width() - self.geometry().width()) / 2,
                  (app.desktop().height() - self.geometry().height()) / 2)
        self.setStyleSheet(
            """#pushButton_select_step,#pushButton_select_job,#pushButton_add_layer,#pushButton_remove_layer{background-color:#464646;color:white;}
            #pushButton_ok{background-color:#0081a6;color:white;}#pushButton_close{background-color:#464646;color:white;}
            QRadioButton{color:black;}
            QToolTip{background-color:#cecece;}#pushButton_ok:hover,#pushButton_close:hover{background:#882F09;}QMessageBox{font:10pt;}""")

    def addLayer(self):
        self.window = alert_layer_window(self)
        self.window.signal_to_parent.connect(self.handle_signal)
        self.window.exec_()

    def clearLayer(self):
        self.tableWidget.clearContents()
        self.tableWidget.setRowCount(0)

    def selectItem(self, t):
        select_item_window(self, t)

    # 处理选择的层
    def handle_signal(self, data):
        layerstr, suffix = data
        print(layerstr, suffix)
        layers = layerstr.split(';')
        self.tableWidget.setRowCount(0)
        self.tableWidget.clearContents()
        self.tableWidget.setRowCount(len(layers))
        for row, layer in enumerate(layers):
            self.tableWidget.setItem(row, 0, QTableWidgetItem(layer))
            self.tableWidget.setItem(row, 1, QTableWidgetItem(layer + suffix))
            check = QCheckBox()
            check.setStyleSheet('margin-left:5px;')
            self.tableWidget.setCellWidget(row, 2, check)

    def run(self):
        source_job = str(self.lineEdit_job.text()).strip()
        if not source_job:
            QMessageBox.warning(self, 'tips', u'请选择目标料号!')
            return
        if source_job not in self.joblist:
            QMessageBox.warning(self, 'tips', u'目标料号不存在，请重新选择料号!')
            return
        source_step = str(self.lineEdit_step.text()).strip()
        if not source_step:
            QMessageBox.warning(self, 'tips', u'请选择目标step!')
            return
        if source_step not in get_step_layers(source_job, 'step'):
            QMessageBox.warning(self, 'tips', u'目标料号不存在目标step,\n请重新选择step!')
            return
        if not self.tableWidget.rowCount():
            QMessageBox.warning(self, 'tips', u'请添加拷贝的层!')
            return
        copy_layers = []
        for row in range(self.tableWidget.rowCount()):
            layer = str(self.tableWidget.item(row, 0).text())
            dest_layer = str(self.tableWidget.item(row, 1).text())
            invert = 'yes' if self.tableWidget.cellWidget(row, 2).isChecked() else 'no'
            copy_layers.append([layer, dest_layer, invert])
        # todo 验证码审批校验 20250529
        source_layers = list(map(lambda copy_layer: copy_layer[0], copy_layers))
        if self.user not in self.ignore_users:
            if source_job[1:12] != self.job_name[1:12]:
                log = u"检测到拷贝型号{0} 非当前型号{1}的小版本，禁止从其他型号copy资料到当前型号！<br>拷贝的step跟层别：{2} {3}".format(
                    source_job, self.job_name, source_step, u'、'.join(source_layers)
                )
                if self.job_name != 'da8614g5ta5a1':
                    if "c1" in source_layers or "c2" in source_layers:
                        # GEN.COM('skip_current_command')
                        log = u"检测到拷贝型号{0} 非当前型号{1}的小版本，禁止从其他型号copy资料到当前型号！<br>文字层禁止拷贝，拷贝的step跟层别：{2} {3}".format(
                            source_job, self.job_name, source_step, u'、'.join(source_layers)
                        )
                        msg_box = msgBox()
                        msg_box.critical(self, '警告', log.format(source_job, self.job_name),  QMessageBox.Ok)
                        # exit(0)
                        return

                result = send_message_to_director(u"重要项目:" + log, self.job_name,
                                                  log,
                                                  password_approve=True)
                if not result:
                    # GEN.COM('skip_current_command')
                    # exit(0)
                    return

            res = self.check_soure_job_is_right(source_job)
            # print('res', res)
            if res:
                # GEN.COM('skip_current_command')
                log = u"检测到拷贝型号{0} 命名非法，资料内容跟型号不一致，请检查命名是否异常，禁止从其中拷贝资料！！"
                msg_box = msgBox()
                msg_box.critical(self, '警告', log.format(source_job, self.job_name), QMessageBox.Ok)
                # exit(0)
                return
            warn_mess = []
            layers_name = list(map(lambda copy_layer: copy_layer[1], copy_layers))
            # print(layers_name)
            if len(layers_name) == 0:
                # exit(0)
                return
            # set中不允许从edit中拷贝资料过来覆盖
            if "set" in self.step_name:
                # source_layer = self.hook_dict['source_layer']
                # dest_layer = self.hook_dict['dest_layer']
                for source_layer, dest_layer, _ in copy_layers:
                    if source_layer == dest_layer:
                        log = u"检测到有从{0} 中拷贝层资料到{1}，此为非常规操作，请谨慎确认是否执行！"
                        msg_box = msgBox()
                        msg_box.critical(self, '警告', log.format(source_step, self.step_name), QMessageBox.Ok)
                        # exit(0)
                        return
            # 检查层别是否在lock范围内
            # print(self.step_name, self.pre_lock)
            if self.step_name in self.pre_lock:
                intersection_layers = [i for i in layers_name if i in self.pre_lock[self.step_name]]
                if len(intersection_layers) > 0:
                    warn_mess.append(u'锁定的Step：%s中_锁定的层别：%s,不可编辑' % (self.step_name, intersection_layers))
                # else:
                #     # exit(0)
                #     return
            # else:
            #     exit(0)
            if len(warn_mess) != 0:
                # GEN.COM('skip_current_command')
                msg_box = msgBox()
                msg_box.critical(self, '警告', u"%s" % "\n".join(warn_mess), QMessageBox.Ok)
                # exit(0)
                return
        #
        transMap = {
            'No': 'no',
            'Yes': 'yes',
            'New Layers': 'new_layers_only',
        }
        copy_attrs = transMap.get(str(self.comboBox.currentText()))
        copy_lpd = transMap.get(str(self.comboBox_2.currentText()))
        for layer, dest_layer, invert in copy_layers:
            '''copy_layer,source_job=sf3012pc002d1-zltest,source_step=edit,source_layer=kh.dxf,dest=layer_name,dest_step=,
            dest_layer=kh.dxf_bak,mode=replace,invert=no,copy_notes=no,copy_attrs=no,copy_lpd=new_layers_only,copy_sr_feat=no'''
            job.COM(
                'copy_layer,source_job=%s,source_step=%s,source_layer=%s,dest=layer_name,dest_step=,dest_layer=%s,mode=replace,invert=%s,'
                'copy_notes=no,copy_attrs=%s,copy_lpd=%s,copy_sr_feat=no' % (
                    source_job, source_step, layer, dest_layer, invert, copy_attrs, copy_lpd))
        QMessageBox.information(self, 'tips', u'复制完成')
        sys.exit()

    def check_soure_job_is_right(self, source_job):
        """"""
        log_path1 = "/id/incamp_db1/jobs/{0}/user/last_netlist_compare_log".format(source_job)
        log_path2 = "/id/incamp_db1/jobs/{0}/user/save_log".format(source_job)
        if os.path.exists(log_path1) or os.path.exists(log_path2):
            if (os.path.exists(log_path1) and source_job[:13] in "".join(file(log_path1).readlines())) or \
                    (os.path.exists(log_path2) and source_job[:13] in "".join(file(log_path2).readlines())):
                return 0

            return 2

        return 0

    def read_file(self):
        """
        用json从user文件夹中的job_lock.json中读取字典
        :return:
        :rtype:
        """
        json_dict = {}
        stat_file = os.path.join(self.userDir, self.job_lock)
        if os.path.exists(stat_file):
            fd = open(stat_file, 'r')
            json_dict = json.load(fd)
            fd.close()
        conver_dict = unicode_convert(json_dict)
        return conver_dict

# 选择料号或step
class select_item_window(QDialog):
    def __init__(self, parent, type):
        super(select_item_window, self).__init__(parent)
        self.type = type
        self.render()
        self.exec_()

    def render(self):
        self.setWindowTitle('Select Values')
        self.resize(240, 300)
        layout = QVBoxLayout(self)
        # combo = QComboBox(self)
        self.label = QLabel('Selected Item(s):')
        self.line_input = QLineEdit('*')
        self.line_input.textChanged.connect(self.filter_item)
        self.listWidget = QListWidget()
        self.listWidget.itemDoubleClicked.connect(self.set_select_value)
        self.listWidget.setStyleSheet('QListWidget::Item{height:20px;}')
        layout.addWidget(self.label)
        layout.addWidget(self.line_input)
        layout.addWidget(self.listWidget)
        btn_box = QHBoxLayout()
        ok = QPushButton()
        ok.setText('OK')
        ok.setStyleSheet('background-color:#0081a6;color:white;')
        ok.setObjectName('dialog_ok')
        ok.setMaximumSize(QSize(50, 16777215))
        ok.setCursor(QCursor(Qt.PointingHandCursor))
        ok.clicked.connect(self.set_select_value)
        close = QPushButton()
        close.setText('Close')
        close.setStyleSheet('background-color:#464646;color:white;')
        close.setObjectName('dialog_close')
        close.setMaximumSize(QSize(50, 16777215))
        close.setCursor(QCursor(Qt.PointingHandCursor))
        close.clicked.connect(lambda: self.close())
        spacerItem1 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        btn_box.addItem(spacerItem1)
        btn_box.addWidget(ok)
        btn_box.addWidget(close)
        layout.addLayout(btn_box)
        self.setStyleSheet('font-family:Arial;font-size:10pt;')
        self.loadList()

    def loadList(self):
        if self.type == 'job':
            self.listWidget.addItems(form.joblist)
        else:
            form.target_steps = get_step_layers(form.target_jobname, 'step')
            print(form.target_steps)
            self.listWidget.addItems(form.target_steps)

    def filter_item(self):
        input_text = str(self.line_input.text()).lower()
        self.listWidget.clear()
        if input_text.startswith('*') or input_text == '':
            if input_text == '*' or input_text == '':
                items = form.joblist if self.type == 'job' else form.target_steps
            else:
                parts = input_text.split('*')[1:]
                items = self.filter(parts)
        else:
            items = list(filter(lambda item: item == input_text, form.joblist)) if self.type == 'job' else list(
                filter(lambda item: item == input_text, form.target_steps))
        self.listWidget.addItems(items)

    def filter(self, args):
        items = []
        if self.type == 'job':
            for item in form.joblist:
                if all([arg in item for arg in args]):
                    items.append(item)
        else:
            for item in form.target_steps:
                if all([arg in item for arg in args]):
                    items.append(item)
        return items

    def set_select_value(self):
        if self.type == 'job':
            form.lineEdit_job.clear()
            form.tableWidget.clearContents()
            if self.listWidget.selectedItems():
                form.target_jobname = str(self.listWidget.selectedItems()[0].text())
                form.lineEdit_job.setText(form.target_jobname)
        else:
            form.lineEdit_step.clear()
            if self.listWidget.selectedItems():
                form.target_step = str(self.listWidget.selectedItems()[0].text())
                form.lineEdit_step.setText(form.target_step)
        self.close()


class alert_layer_window(QDialog):
    # 定义自定义信号，带一个str类型参数
    signal_to_parent = pyqtSignal(list)

    def __init__(self, parent=None):
        super(alert_layer_window, self).__init__(parent)
        self.render()
        # self.exec_()

    def render(self):
        self.setWindowTitle('Source Layers')
        self.resize(240, 300)
        layout = QVBoxLayout(self)
        self.label = QLabel('Selected Source Layer(s):')
        self.line_input = QLineEdit('*')
        self.line_input.textChanged.connect(self.filter_item)
        #
        suffix_box = QHBoxLayout()
        label = QLabel('Suffix:')
        # label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.preference = ['_bak', '_orig', '_copy']
        self.suffixCombo = QComboBox()
        self.suffixCombo.setEditable(True)
        self.suffixCombo.addItems(self.preference)
        suffix_box.addWidget(label)
        suffix_box.addWidget(self.suffixCombo, 1)
        suffix_box.addItem(spacerItem)
        # suffix_box.setStretch(1, 0)
        self.tree = QTreeWidget()
        self.tree.setSelectionMode(QHeaderView.NoSelection)
        self.tree.setStyleSheet(':item{height:20px;}')
        # 设置列数
        self.tree.setColumnCount(1)
        # 设置树形控件头部的标题
        self.tree.setHeaderHidden(True)

        # 设置根节点
        self.root = QTreeWidgetItem(self.tree)
        self.root.setText(0, 'All')
        # root.setIcon(0, QIcon('./images/root.png'))

        # todo 优化2 设置根节点的背景颜色
        # 设置树形控件的列的宽度
        self.tree.setColumnWidth(0, 120)
        # 设置子节点
        # self.items = job.matrix.returnRows()
        self.items = get_step_layers(form.target_jobname, 'layer')
        print(self.items)
        for layer in self.items:
            item = QTreeWidgetItem()
            item.setText(0, str(layer))
            item.setIcon(0, QIcon('images/other.png'))
            item.setCheckState(0, Qt.Unchecked)
            self.root.addChild(item)

        # 加载根节点的所有属性与子控件
        self.root.setCheckState(0, Qt.Unchecked)
        self.tree.addTopLevelItem(self.root)

        # TODO 优化3 给节点添加响应事件
        self.tree.clicked.connect(self.onClicked)

        # 节点全部展开
        self.tree.expandAll()
        layout.addWidget(self.label)
        layout.addWidget(self.line_input)
        layout.addWidget(self.tree)
        layout.addLayout(suffix_box)
        btn_box = QHBoxLayout()
        ok = QPushButton()
        ok.setText('OK')
        ok.setStyleSheet('background-color:#0081a6;color:white;')
        ok.setObjectName('dialog_ok')
        ok.setCursor(QCursor(Qt.PointingHandCursor))
        ok.clicked.connect(self.select_layers)
        close = QPushButton()
        close.setText('Close')
        close.setStyleSheet('background-color:#464646;color:white;')
        close.setObjectName('dialog_close')
        close.setCursor(QCursor(Qt.PointingHandCursor))
        close.clicked.connect(lambda: self.close())
        spacerItem1 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        btn_box.addItem(spacerItem1)
        btn_box.addWidget(ok)
        btn_box.addWidget(close)
        layout.addLayout(btn_box)
        self.setStyleSheet('font-family:Arial;font-size:10pt;')

    def onClicked(self, qmodeLindex):
        # print(qmodeLindex.data())
        count = self.tree.topLevelItemCount()
        for index in range(count):
            item = self.tree.topLevelItem(index)
            # 判断根节点
            if item.text(0) == qmodeLindex.data():
                if item.checkState(0) == 0:
                    for i in range(item.childCount()):
                        child = item.child(i)
                        # if child.checkState(0) == 0:
                        #     child.setCheckState(0, Qt.Checked)
                        # else:
                        child.setCheckState(0, Qt.Unchecked)

                        for j in range(child.childCount()):
                            sub_child = child.child(j)
                            # if sub_child.checkState(0) == 0:
                            #     sub_child.setCheckState(0, Qt.Checked)
                            # else:
                            sub_child.setCheckState(0, Qt.Unchecked)
                    break
                else:
                    for i in range(item.childCount()):
                        child = item.child(i)
                        # if child.checkState(0) == 0:
                        child.setCheckState(0, Qt.Checked)
                        # else:
                        #     child.setCheckState(0, Qt.Unchecked)

                        for j in range(child.childCount()):
                            sub_child = child.child(j)
                            # if sub_child.checkState(0) == 0:
                            sub_child.setCheckState(0, Qt.Checked)
                            # else:
                            #     sub_child.setCheckState(0, Qt.Unchecked)
                    break
            for i in range(item.childCount()):
                child = item.child(i)
                if qmodeLindex.data() == child.text(0):
                    if child.checkState(0) == 0:
                        for i in range(child.childCount()):
                            chi = child.child(i)
                            chi.setCheckState(0, Qt.Unchecked)
                    else:
                        for i in range(child.childCount()):
                            chi = child.child(i)
                            chi.setCheckState(0, Qt.Checked)
            break

    def filter_item(self):
        input_text = str(self.line_input.text()).lower()
        self.root.takeChildren()
        if input_text.startswith('*'):
            if input_text == '*':
                items = self.items
            else:
                parts = input_text.split('*')[1:]
                items = self.filter(parts)
        else:
            items = list(filter(lambda item: item == input_text, self.items))
        for layer in items:
            item = QTreeWidgetItem()
            item.setText(0, str(layer))
            item.setIcon(0, QIcon('images/other.png'))
            item.setCheckState(0, Qt.Unchecked)
            self.root.addChild(item)

    def filter(self, args):
        items = []
        for item in self.items:
            if all([arg in item for arg in args]):
                items.append(item)
        return items

    def select_layers(self):
        # 取到选择的layers
        count = self.tree.topLevelItemCount()
        select_lay = []
        for index in range(count):
            item = self.tree.topLevelItem(index)
            for i in range(item.childCount()):
                child = item.child(i)
                if child.checkState(0) == 2:
                    select_lay.append(str(child.text(0)))
        if not select_lay:
            QMessageBox.warning(self, 'tips', u'请选择要拷贝的层')
            return
        layer_str = ';'.join(select_lay)
        suffix = str(self.suffixCombo.currentText()).strip()
        if suffix == '':
            QMessageBox.warning(self, 'tips', u'后缀不能为空')
            return
        self.signal_to_parent.emit([layer_str, suffix])
        self.close()


# 代理类
class EmptyDelegate(QItemDelegate):
    def __init__(self, parent):
        super(EmptyDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        return None


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Cleanlooks')
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    form = CopyLayer()
    form.show()
    sys.exit(app.exec_())
