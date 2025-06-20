#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:CopyLayer.py
   @author:zl
   @time: 2025/5/29 10:14
   @software:PyCharm
   @desc:
"""
import os
import sys

from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import CopyLayerUI as ui


class CopyLayer(QWidget, ui.Ui_Form):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        options = ['No', 'Yes', 'New Layers']
        self.comboBox.addItems(options)
        self.comboBox_2.addItems(options)
        self.comboBox_2.setCurrentIndex(2)
        self.pushButton_select_job.clicked.connect(lambda: self.selectItem('job'))
        self.pushButton_select_step.clicked.connect(lambda: self.selectItem('step'))
        self.pushButton_add_layer.clicked.connect(self.addLayer)
        self.pushButton_remove_layer.clicked.connect(self.clearLayer)
        self.pushButton_ok.clicked.connect(self.run)
        self.pushButton_close.clicked.connect(lambda: sys.exit())
        self.setStyleSheet(
            """#pushButton_select_step,#pushButton_select_job,#pushButton_add_layer,#pushButton_remove_layer{background-color:#464646;color:white;}
            #pushButton_ok{background-color:#0081a6;color:white;}#pushButton_close{background-color:#464646;color:white;}
            QRadioButton{color:black;}
            QToolTip{background-color:#cecece;}#pushButton_ok:hover,#pushButton_close:hover{background:#882F09;}QMessageBox{font:12pt;}""")

    def addLayer(self):
        window = alert_layer_window(self)

    def clearLayer(self):
        self.tableWidget.clearContents()
        self.tableWidget.setRowCount(0)

    def selectItem(self, t):
        print(t)
        window = select_item_window(self, t)

    def run(self):
        pass


# 选择料号或step
class select_item_window(QDialog):
    def __init__(self, parent, type):
        super(select_item_window, self).__init__(parent)
        self.type = type
        self.render()
        self.exec_()

    def render(self):
        self.setWindowTitle('Select Values')
        self.resize(220, 260)
        layout = QVBoxLayout(self)
        # combo = QComboBox(self)
        self.label = QLabel('Selected Item(s):')
        self.line_input = QLineEdit('*')
        self.line_input.textChanged.connect(self.filter_item)
        # steps = job.stepsList
        # if steps:
        #     for step in steps:
        #         item = QTreeWidgetItem(self.root)
        #         item.setText(0, step)
        #         item.setCheckState(0, Qt.Unchecked)
        #         # item.setIcon(0, QIcon('images/other.png'))
        self.listWidget = QListWidget()
        self.listWidget.itemDoubleClicked.connect(self.set_select_value)
        layout.addWidget(self.label)
        layout.addWidget(self.line_input)
        layout.addWidget(self.listWidget)
        btn_box = QHBoxLayout()
        ok = QPushButton(self)
        ok.setText('OK')
        ok.setStyleSheet('background-color:#0081a6;color:white;')
        ok.setObjectName('dialog_ok')
        ok.setMaximumSize(QSize(50, 16777215))
        ok.setCursor(QCursor(Qt.PointingHandCursor))
        ok.clicked.connect(self.set_select_value)
        close = QPushButton(self)
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
        self.setStyleSheet('font-family:微软雅黑;font-size:10pt;')
        self.loadList()

    def loadList(self):
        self.items = [chr(i) for i in range(97, 107)]
        self.listWidget.addItems(self.items)

    def filter_item(self):
        input_text = self.line_input.text().lower()
        self.listWidget.clear()
        if input_text.startswith('*'):
            if input_text == '*':
                items = self.items
            else:
                parts = input_text.split('*')[1:]
                items = self.filter(parts)
        else:
            items = list(filter(lambda item: item == input_text, self.items))
        self.listWidget.addItems(items)

    def filter(self, args):
        items = []
        print(args)
        for item in self.items:
            if all([arg in item for arg in args]):
                items.append(item)
        return items

    def set_select_value(self):
        if self.type == 'job':
            form.lineEdit_job.clear()
            if self.listWidget.selectedItems():
                form.lineEdit_job.setText(self.listWidget.selectedItems()[0].text())
        else:
            form.lineEdit_step.clear()
            if self.listWidget.selectedItems():
                form.lineEdit_step.setText(self.listWidget.selectedItems()[0].text())
        self.close()


class alert_layer_window(QDialog):
    def __init__(self, parent):
        super(alert_layer_window, self).__init__(parent)
        self.render()
        self.exec_()

    def render(self):
        self.setWindowTitle('Layer Filter')
        self.resize(200, 240)
        layout = QVBoxLayout(self)
        # combo = QComboBox(self)
        self.tree = QTreeWidget()
        # 设置列数
        self.tree.setColumnCount(1)
        # 设置树形控件头部的标题
        self.tree.setHeaderLabels(['Layers'])
        # 设置根节点
        self.root = QTreeWidgetItem(self.tree)
        self.root.setText(0, 'All')
        # root.setIcon(0, QIcon('./images/root.png'))

        # todo 优化2 设置根节点的背景颜色
        # 设置树形控件的列的宽度
        self.tree.setColumnWidth(0, 120)
        # 设置子节点
        all_lays = job.matrix.returnRows()
        signal_lays = job.matrix.returnRows('board')
        if signal_lays:
            signal_Node = QTreeWidgetItem(self.root)
            signal_Node.setText(0, 'Board')
            signal_Node.setCheckState(0, Qt.Unchecked)
            for layer in signal_lays:
                item = QTreeWidgetItem()
                item.setText(0, str(layer))
                # item.setIcon(0, QIcon('images/signal.png'))
                item.setCheckState(0, Qt.Unchecked)
                signal_Node.addChild(item)
        copy_lays = copy.copy(all_lays)
        for lay in copy_lays:
            if lay in signal_lays:
                all_lays.remove(lay)
        if all_lays:
            other_Node = QTreeWidgetItem(self.root)
            other_Node.setText(0, 'Other')
            other_Node.setCheckState(0, Qt.Unchecked)
            for layer in all_lays:
                item = QTreeWidgetItem()
                item.setText(0, str(layer))
                item.setIcon(0, QIcon('images/other.png'))
                item.setCheckState(0, Qt.Unchecked)
                other_Node.addChild(item)

        # 加载根节点的所有属性与子控件
        self.root.setCheckState(0, Qt.Unchecked)
        self.tree.addTopLevelItem(self.root)

        # TODO 优化3 给节点添加响应事件
        self.tree.clicked.connect(self.onClicked)

        # 节点全部展开
        self.tree.expandAll()
        layout.addWidget(self.tree)
        btn_box = QHBoxLayout()
        ok = QPushButton(self)
        ok.setText('OK')
        ok.setStyleSheet('background-color:#0081a6;color:white;')
        ok.setObjectName('dialog_ok')
        ok.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        ok.clicked.connect(self.generate_layerstr)
        close = QPushButton(self)
        close.setText('Close')
        close.setStyleSheet('background-color:#464646;color:white;')
        close.setObjectName('dialog_close')
        close.setCursor(QCursor(QtCore.Qt.PointingHandCursor))
        close.clicked.connect(lambda: self.close())
        spacerItem1 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        btn_box.addItem(spacerItem1)
        btn_box.addWidget(ok)
        btn_box.addWidget(close)
        layout.addLayout(btn_box)
        self.setStyleSheet('QPushButton{font-family:黑体;font-size:10pt;}')

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

    def generate_layerstr(self):
        # 取到选择的layers
        # print('generate layerstr')
        count = self.tree.topLevelItemCount()
        select_lay = []
        for index in range(count):
            item = self.tree.topLevelItem(index)
            for i in range(item.childCount()):
                child = item.child(i)
                for j in range(child.childCount()):
                    chi = child.child(j)
                    if chi.checkState(0) == 2:
                        select_lay.append(str(chi.text(0)))
        # print(select_lay)
        # print(len(select_lay))
        layer_str = ';'.join(select_lay)
        ex.lineEdit_layers.setText(layer_str)
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    jobname = os.environ.get('JOB')
    form = CopyLayer()
    form.show()
    sys.exit(app.exec_())
