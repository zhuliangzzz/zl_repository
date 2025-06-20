#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os, sys
import re
import json
import platform
if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package_HDI")
    sys.path.append(r"D:/pyproject/Package")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

from create_ui_model import showMessageInfo,app, showQuestionMessageInfo
from PyQt4.QtGui import QVBoxLayout,QLabel,QTableWidgetItem,QComboBox,QMessageBox,QHBoxLayout
from PyQt4 import QtGui,QtCore,Qt
from mwClass_V4 import  AboutDialog
import random
import time
import requests
from genesisPackages import top


def send_erros_mgs_to_director(mgs):
    print mgs
    # 验证码接收机器人url

    url = "https://oapi.dingtalk.com/robot/send?access_token=a670a1140dfe55400090bc2796e88f42181b6d9c60f878303ce1580393ea6215"
    message = {
        "msgtype": "text",  # text，文本格式
        "text": {
            "content": mgs,  # 我们将需要发送的消息，写在这里
        }
    }
    # 3、发送HTTP POST请求
    try:
        response = requests.post(url, headers={'Content-Type': 'application/json'}, data=json.dumps(message))
        # 检查响应状态码
        if response.status_code == 200:
            print(response.text)
        else:
            print(u"消息发送失败，状态码：{response.status_code}，响应内容：{response.text}")
    except Exception as e:
        print e


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


class CustomQCB(QComboBox):
    def wheelEvent(self, e):
        # 重写该方法，不响应滚轮事件
        if e.type() == QtCore.QEvent.Wheel:
            e.ignore()

class MyWindow(QtGui.QDialog):
    def __init__(self):
        super(MyWindow,self).__init__()
        self.setupUi()

    def setupUi(self):
        self.setFixedSize(800,600)
        self.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        font = QtGui.QFont()
        self.setWindowTitle(u"设定输出层")
        self.vh = QVBoxLayout()
        lb=QLabel(u"请选择相关参数:")
        font.setPointSize(15)
        lb.setFont(font)
        self.vh.addWidget(lb)
        self.table = QtGui.QTableWidget()
        self.set_table()

        self.vh.addWidget(self.table)
        self.setLayout(self.vh)
        self.buttonBox = QtGui.QDialogButtonBox()
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Ok)
        self.vh.addWidget(self.buttonBox)
        self.buttonBox.accepted.connect(self.apply)  # 确定
        self.buttonBox.rejected.connect(self.exit_win)  # 取消
        # self.cbox.currentIndexChanged.connect(self.tabel_show)

    def exit_win(self):
        sys.exit(1)

    def set_table(self):
        button_StyleSheet = """
                QRadioButton::indicator {
                    width: 16px;
                    height: 16px;
                    border-radius: 0px; /* 设置为0px使其成为方形 */
                    background-color: white;
                    border: 2px solid gray;
                }
                QRadioButton::indicator:checked {
                    background-color: red; /* 选中时的颜色 */
                }
            """
        table = self.table
        # 禁止表格编辑
        table.setEditTriggers(QtGui.QTableWidget.NoEditTriggers)
        table.horizontalHeader().setStretchLastSection(True)
        header_name = [u'输出层名', u'镜像选择', u'镜像选择',u'正负极性', u'正负极性', u'NOTE']
        column_witths = [80, 80, 80, 90, 90]
        table.setColumnCount(len(header_name))
        for i, name in enumerate(header_name):
            item = QTableWidgetItem(name)
            item.setTextAlignment(QtCore.Qt.AlignCenter)  # 字符居中
            table.setHorizontalHeaderItem(i, item)
        for i, cloumd in enumerate(column_witths):
            table.setColumnWidth(i, cloumd)
        font = QtGui.QFont()
        font.setPointSize(15)
        font.setBold(True)
        table.verticalHeader().setVisible(False)
        table.setRowCount(len(output_lays))



        for i, layer in enumerate(output_lays):
            table.setRowHeight(i, 40)
            item = QTableWidgetItem(layer)
            item.setFont(font)
            item.setForeground(QtGui.QColor(0, 0, 255))
            item.setTextAlignment(QtCore.Qt.AlignCenter)  # 字符居中
            table.setItem(i, 0, item)

        for i, layer in enumerate(output_lays):
            group = QtGui.QButtonGroup(self)
            rbut1 = QtGui.QRadioButton('no')
            rbut1.setFont(font)
            rbut1.setStyleSheet(button_StyleSheet)
            rbut2 = QtGui.QRadioButton('yes')
            rbut2.setFont(font)
            rbut2.setStyleSheet(button_StyleSheet)
            group.addButton(rbut1)
            group.addButton(rbut2)
            table.setCellWidget(i, 1, rbut1)
            table.setCellWidget(i, 2, rbut2)

        for i, layer in enumerate(output_lays):
            group = QtGui.QButtonGroup(self)
            rbut1 = QtGui.QRadioButton(u'正片')
            rbut1.setFont(font)
            rbut1.setStyleSheet(button_StyleSheet)
            rbut2 = QtGui.QRadioButton(u'负片')
            rbut2.setFont(font)
            rbut2.setStyleSheet(button_StyleSheet)
            group.addButton(rbut1)
            group.addButton(rbut2)
            table.setCellWidget(i, 3, rbut1)
            table.setCellWidget(i, 4, rbut2)

    def closeEvent(self, event):
        # 忽略关闭事件
        event.ignore()

    def apply(self):
        color_red = QtGui.QColor(255, 0, 0)
        font = QtGui.QFont()
        font.setPointSize(11)
        dict_output_info = {}
        choose_erros = []
        for row in range(self.table.rowCount()):
            layer_name = self.table.item(row, 0).text()
            if not self.table.cellWidget(row, 1).isChecked() and not self.table.cellWidget(row, 2).isChecked():
                choose_erros.append(u"{0}层输出面次未选择".format(layer_name))
            if not self.table.cellWidget(row, 3).isChecked() and not self.table.cellWidget(row, 4).isChecked():
                choose_erros.append(u"{0}层正负极性未选择".format(layer_name))
        if choose_erros:
            showMessageInfo(*(choose_erros))
        else:
            show_erros = []
            for row in range(self.table.rowCount()):
                show_log = []
                layer_name = str(self.table.item(row, 0).text())

                if self.table.cellWidget(row, 1).isChecked():
                    mc = 'no'
                else:
                    mc = 'yes'
                if output_layers[layer_name]['mc'] <> mc:
                    mgs = u"{0}层系统判断镜像为{1}，手动选择为{2}".format(layer_name, output_layers[layer_name]['mc'], mc)
                    show_log.append(mgs)
                    show_erros.append(mgs)
                if self.table.cellWidget(row, 3).isChecked():
                    pol = 'positive'
                else:
                    pol = 'negative'
                if output_layers[layer_name]['pol'] <> pol:
                    mgs = u"{0}层系统判断极性为{1}，手动选择为{2}".format(layer_name, output_layers[layer_name]['pol'], pol)
                    show_log.append(mgs)
                    show_erros.append(mgs)
                if show_log:
                    item = QTableWidgetItem('\n'.join(show_log))
                    item.setFont(font)
                    item.setForeground(color_red)
                    item.setToolTip('\n'.join(show_log))
                    self.table.setItem(row, 5, item)
                else:
                    item = QTableWidgetItem('')
                    item.setFont(font)
                    self.table.setItem(row, 5, item)
                dict_output_info[layer_name] = {'mc': mc, 'pol': pol}

            go_next = False
            if show_erros:
                # 获取用户名
                user = top.getUser()
                # send_log = u"检测到用户{0}输出LDI资料有下列异常:\n  ".format(user) + '\n   '.join(show_erros).decode('utf-8', 'ignore')
                send_log = u"重要项目:型号{0}检测到用户{1}输出LDI资料存在下列异常:\n   ".format(job_name, user) + '\n   '.join(show_erros)
                send_erros_mgs_to_director(send_log)
                resurt = showQuestionMessageInfo(u"系统判断和人工选择判断存在不一致，继续输出将发起评审，退出重新选择")
                if resurt:
                    # 继续输出发起评审
                    res = send_message_to_director(send_log, job_name, send_log, password_approve=True)
                    if res:
                        go_next = True
            else:
                go_next = True

            if go_next:
                # 记录输出选择
                with open(recode_file, 'w') as file:
                    json.dump(dict_output_info, file, indent=4)
                sys.exit(0)

if __name__ == "__main__":
    job_name = sys.argv[1]
    recode_file = sys.argv[2]
    get_lines = sys.argv[3:]
    output_layers = {}
    output_lays = []
    for line in get_lines:
        layerName, layer_mir, layer_pol = line.split(',')
        output_lays.append(layerName)
        output_layers[layerName] = {'mc': layer_mir, 'pol': layer_pol}
    dlog = MyWindow()
    screen = QtGui.QDesktopWidget().screenGeometry()
    size = dlog.geometry()
    dlog.move((screen.width() - size.width()) / 2 + 200, 100)
    dlog.show()
    dlog.exec_()