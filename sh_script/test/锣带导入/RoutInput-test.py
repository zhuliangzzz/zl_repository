#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:RoutInput.py
   @author:zl
   @time: 2024/12/19 9:16
   @software:PyCharm
   @desc:
   读取tgz导入
"""
import copy
import json
import os
import re
import shutil
import sys, platform

reload(sys)
sys.setdefaultencoding('utf8')
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import RoutInputUI_pyqt4 as ui
if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
import GetData
import MySQL_DB
import genClasses_zl as gen
from genesisPackages_zl import get_profile_limits, get_sr_area_for_step_include, get_layer_selected_limits, signalLayers

class RoutInput(QWidget, ui.Ui_Form):
    def __init__(self):
        super(RoutInput, self).__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        self.jobname = os.environ.get("JOB")
        self.job = gen.Job(self.jobname)
        steps = self.job.stepsList
        self.flipList = []  # flip的step
        self.comboBox.addItems(steps)
        if 'panel' in steps:
            stepname = 'panel'
        elif 'set' in steps:
            stepname = 'set'
        else:
            stepname = steps[0]
        self.flipstep = gen.Step(self.job, "edit")
        # 复制方式
        self.copy_mode = 'replace'
        self.flipStepName(stepname)
        if stepname:
            idex = list(filter(lambda i: steps[i] == stepname, range(len(steps))))[0] if list(filter(lambda i: steps[i] == stepname, range(len(steps)))) else -1
            self.comboBox.setCurrentIndex(idex)
        self.label_title.setText('Job:%s' % self.jobname)
        self.setStyleSheet(
            '''#pushButton_exec,#pushButton_exit{font:11pt;background-color:#0081a6;color:white;} #pushButton_exec:hover,#pushButton_exit:hover{background:black;color:white;}''')
        self.set_path()
        self.load_list()
        self.label.setVisible(False)
        self.comboBox.setVisible(False)
        # self.listWidget.setSelectionMode(QAbstractItemView.MultiSelection)
        self.lineEdit_path.returnPressed.connect(self.load_list)
        self.pushButton_path.clicked.connect(self.select_path)
        self.pushButton_exec.clicked.connect(self.run)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())
        self.checkBox_select_all.clicked.connect(self.check_all)
        self.panel_surface_layer = 'inner_panel_surface'  # 去细丝保留的铜皮层
        self.getDATA = GetData.Data()
        # PRODUCT = os.environ.get('INCAM_PRODUCT', None)
        if platform.system() == "Windows":
            self.userDir = "%s/fw/jobs/%s/user" % (os.environ.get('GENESIS_DIR', 'D:/genesis'), self.jobname)
        else:
            self.userDir = os.environ.get('JOB_USER_DIR', None)
            if not self.userDir:
                self.userDir = "%s/user" % self.job.dbpath
        print(self.userDir)
        self.job_make_info = self.getJOB_LockInfo(dataType='job_make_status')
        self.job_lock = os.path.join(self.userDir, '%s_job_lock.json' % self.jobname)
        # self.ignore_keys = ['lock_panelization_status', 'unlock_panelization_status']  # job_lock字典中不需要找的key

    def set_path(self):
        if sys.platform == "win32":
            self.get_para_path = ur"\\192.168.2.172\GCfiles\锣带备份\锣带备份".format(self.jobname[1:4].upper(),
                                                                                      self.jobname.split('-')[
                                                                                          0].upper(),
                                                                                      self.jobname.split('-')[0][
                                                                                      -2:].upper())
        else:
            self.get_para_path = u"/windows/172.file/锣带备份/锣带备份/{0}系列/{1}/".format(self.jobname[1:4].upper(),
                                                                                            self.jobname.split('-')[
                                                                                                0].upper())
            # self.get_para_path = u"/id/workfile/hdi_film/{0}".format(self.jobname.split('-')[0])
        self.lineEdit_path.setText(self.get_para_path)

    def select_path(self):
        directory = QFileDialog.getExistingDirectory(self, u"选择文件夹", self.get_para_path, QFileDialog.ShowDirsOnly)
        if directory:
            self.lineEdit_path.setText(directory)
            self.load_list()

    def check_all(self):
        if self.checkBox_select_all.isChecked():
            self.listWidget.selectAll()
        else:
            self.listWidget.clearSelection()

    def load_list(self):
        self.listWidget.clear()
        self.checkBox_select_all.setChecked(False)
        file_path = str(self.lineEdit_path.text())
        if not os.path.exists(file_path):
            QMessageBox.warning(None, u'提示', u'路径%s不存在' % str(self.lineEdit_path.text()))
            return
        files = filter(lambda x: os.path.isfile(os.path.join(file_path, x)), os.listdir(file_path))
        tgzs = []
        for file in files:
            if file.endswith('.tgz'):
                tgzs.append(file)
        self.listWidget.addItems(tgzs)

    def run(self):
        self.rout_layers = []
        if not self.listWidget.selectedItems():
            QMessageBox.warning(None, u'警告', u'请选择要导入的tgz！')
            return
        tgz = str(self.listWidget.selectedItems()[0].text())
        self.import_name = tgz.rsplit('.tgz', 1)[0]
        self.import_jobname = tgz.rsplit('.tgz', 1)[0] + '-rout'
        # stepname = self.comboBox.currentText()
        gen_top = gen.Top()
        if self.import_jobname in gen_top.listJobs():
            gen_top.deleteJob(self.import_jobname)
        gen_top.COM(
            'import_job,db=db1,path=%s,name=%s' % (os.path.join(str(self.lineEdit_path.text()), tgz), self.import_jobname))
        self.import_job = gen.Job(self.import_jobname)
        #
        layer_selector = alert_layer_window(self)
        print(self.rout_layers)
        steplist = self.job.stepsList
        layerlist = self.job.matrix.returnRows()
        DB_M = MySQL_DB.MySQL()
        dbc_m = DB_M.MYSQL_CONNECT(hostName='192.168.2.19', database='hdi_engineering', prod=3306,
                                   username='root', passwd='k06931!')
        sql = u"select * from hdi_engineering.incam_user_authority"
        director_user_info = DB_M.SELECT_DIC(dbc_m, sql)
        dbc_m.close()
        IncamUser = self.job.getUser()
        is_rout_user = False
        for dic_info in director_user_info:
            if str(dic_info["user_id"]) == IncamUser:
                if dic_info["Authority_Name"] == u"锣带制作用户" and \
                        dic_info["Authority_Status"] == u"是":
                    is_rout_user = True
                    break
        if self.flipList: # 先把层加进去
            self.flipstep.initStep()
            self.flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=yes' % self.jobname)
            if self.flipstep.name in self.import_job.stepsList:
                for layer in self.rout_layers:
                    # 备份
                    bk_layer = '%s_bak' % layer
                    # self.step.removeLayer(bk_layer)
                    if self.flipstep.isLayer(layer):
                        # 当前料号对导入的层备份
                        if layer_selector.bak:
                            self.flipstep.removeLayer(bk_layer)
                            self.flipstep.affect(layer)
                            self.flipstep.copySel(bk_layer)
                            self.flipstep.unaffectAll()
                        self.job.matrix.modifyRow(bk_layer, type='rout')
                    self.flipstep.copyLayer(self.import_jobname, self.flipstep.name, layer, layer, self.copy_mode)
                    self.job.matrix.modifyRow(layer, type='rout')
            else:
                for layer in self.rout_layers:
                    # 备份
                    bk_layer = '%s_bak' % layer
                    # self.step.removeLayer(bk_layer)
                    if self.flipstep.isLayer(layer):
                        # 当前料号对导入的层备份
                        if layer_selector.bak:
                            self.flipstep.removeLayer(bk_layer)
                            self.flipstep.affect(layer)
                            self.flipstep.copySel(bk_layer)
                            self.flipstep.unaffectAll()
                            self.flipstep.matrix.modifyRow(bk_layer, type='rout')
                        self.job.matrix.modifyRow(layer, type='rout')
            self.flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=no' % self.jobname)
            for stepname in steplist:
                if stepname not in self.import_job.stepsList:
                    continue
                if self.flipList:
                    if stepname == self.flipstep.name:
                        continue
                self.step = gen.Step(self.job, stepname)
                self.step.initStep()
                for layer in self.rout_layers:
                    # 备份
                    bk_layer = '%s_bak' % layer
                    # self.step.removeLayer(bk_layer)
                    if layer_selector.bak:
                        if layer in layerlist:
                            # self.step.removeLayer(bk_layer)
                            self.step.affect(layer)
                            self.step.copySel(bk_layer)
                            self.step.unaffectAll()
                        # self.job.matrix.modifyRow(bk_layer, type='rout')
                    self.step.copyLayer(self.import_jobname, stepname, layer, layer, self.copy_mode)
                    # self.job.matrix.modifyRow(layer, type='rout')
        else:
            for stepname in steplist:
                if stepname not in self.import_job.stepsList:
                    continue
                self.step = gen.Step(self.job, stepname)
                self.step.initStep()
                for layer in self.rout_layers:
                    # 备份
                    bk_layer = '%s_bak' % layer
                    # self.step.removeLayer(bk_layer)
                    if layer_selector.bak:
                        if layer in layerlist:
                            if bk_layer in layerlist:
                                self.step.truncate(bk_layer)
                            self.step.affect(layer)
                            self.step.copySel(bk_layer)
                            self.step.unaffectAll()
                            self.job.matrix.modifyRow(bk_layer, type='rout')
                    self.step.copyLayer(self.import_jobname, stepname, layer, layer, self.copy_mode)
                    self.job.matrix.modifyRow(layer, type='rout')
        self.import_job.close(1)
        gen_top.deleteJob(self.import_jobname)
        if is_rout_user:
            self.update_lock_info()
        if self.rout_layers:
            QMessageBox.information(None, u'提示', u'导入完成！\n导入的层：%s' % '、'.join(self.rout_layers))
        else:
            QMessageBox.information(None, u'提示', u'没有选择要导入的锣带层！')
        sys.exit()

    # 更新锁状态
    def update_lock_info(self):
        self.pre_lock = None
        if len(self.jobname) == 13:
            self.pre_lock = self.getJOB_LockInfo(dataType='locked_info')
        if not self.pre_lock:
            self.pre_lock = self.read_file()
        rout_layers = self.job.matrix.returnRows('board', 'rout')
        lyrs = self.job.matrix.returnRows()
        lock_lyrs = list(filter(lambda lyr: lyr not in rout_layers, lyrs))
        # print(lock_lyrs)
        for lock_step in self.job.stepsList:
            self.pre_lock.update({lock_step: lock_lyrs})
        self.pre_lock.update({"unlock_panelization_status": 'yes'})
        # print(self.pre_lock)
        # 记录状态
        status_file = os.path.join(self.userDir, 'cam_finish_status_{0}.log'.format(self.jobname))
        with open(status_file, 'w') as file_obj:
            json.dump(self.job_make_info, file_obj)
        self.write_file()

    def write_file(self):
        """
        用json把参数字典直接写入user文件夹中的job_lock.json
        json_str = json.dumps(self.parm)将字典dump成string的格式
        :return:
        :rtype:
        """
        # 将收集到的数据以json的格式写入user/param
        # stat_file = os.path.join(self.userDir, desfile)
        fd = open(self.job_lock, 'w')
        json.dump(self.pre_lock, fd, ensure_ascii=False, indent=4, separators=(', ', ': '), sort_keys=True)
        fd.close()

    def read_file(self):
        """
        用json从user文件夹中的job_lock.json中读取字典
        :return:
        :rtype:
        """
        json_dict = {}
        if os.path.exists(self.job_lock):
            fd = open(self.job_lock, 'r')
            json_dict = json.load(fd)
            fd.close()
        return json_dict

    def getJOB_LockInfo(self, dataType='locked_info'):
        """
        从数据库中获取料号的锁记录
        :param dataType: 获取的数据类型（status:locked_info log:locked_log）
        :return:dict
        """
        lockData = self.getDATA.getLock_Info(self.job.name.split("-")[0])
        try:
            return json.loads(lockData[dataType].replace("\r", ""), encoding='utf8')
        except:
            # print u'传入的数据参数异常'
            return {}

    def flipStepName(self, step):
        """
        递归寻找出有镜像的step，并append到 flipList数组中
        :param step: step名
        :return: None
        """
        info = self.job.DO_INFO('-t step -e %s/%s -m script -d SR -p flip+step' % (self.jobname, step))
        step_flip_tuple = [(info['gSRstep'][i], info['gSRflip'][i]) for i in range(len(info['gSRstep']))]
        step_flip_tuple = list(set(step_flip_tuple))
        for (stepName, flip_yn) in step_flip_tuple:
            if flip_yn == 'yes':
                self.flipList.append(stepName)
            elif flip_yn == 'no':
                self.flipStepName(stepName)
class alert_layer_window(QDialog):
    def __init__(self, parent):
        super(alert_layer_window, self).__init__(parent)
        self.render()
        self.exec_()

    def render(self):
        self.setWindowTitle(u'选择要导入的层')
        self.resize(300, 340)
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
        # all_lays = routInput.import_job.matrix.returnRows()
        rout_lays = routInput.import_job.matrix.returnRows('board', 'rout')
        rout_lays = list(filter(lambda rout: 'rout' in rout and not re.search('pnl_rout|%s' % routInput.import_name, rout), rout_lays))
        if rout_lays:
            signal_Node = QTreeWidgetItem(self.root)
            signal_Node.setText(0, u'锣带层')
            signal_Node.setCheckState(0, Qt.Unchecked)
            for layer in rout_lays:
                item = QTreeWidgetItem()
                item.setText(0, str(layer))
                # item.setIcon(0, QIcon('images/signal.png'))
                item.setCheckState(0, Qt.Unchecked)
                signal_Node.addChild(item)

        # 加载根节点的所有属性与子控件
        self.root.setCheckState(0, Qt.Unchecked)
        self.tree.addTopLevelItem(self.root)

        # TODO 优化3 给节点添加响应事件
        self.tree.clicked.connect(self.onClicked)

        # 节点全部展开
        self.tree.expandAll()
        layout.addWidget(self.tree)
        # 复制方式
        copy_mode = QHBoxLayout()
        label = QLabel(u'复制方式：')
        self.radio = QRadioButton(u'replace(替换)')
        self.radio2 = QRadioButton(u'append(追加)')
        self.radio.setChecked(True)
        copy_mode.addWidget(label)
        copy_mode.addWidget(self.radio)
        copy_mode.addWidget(self.radio2)
        btn_box = QHBoxLayout()
        ok = QPushButton(self)
        ok.setText('OK')
        ok.setStyleSheet('background-color:#0081a6;color:white;')
        ok.setObjectName('dialog_ok')
        ok.setCursor(QCursor(Qt.PointingHandCursor))
        ok.clicked.connect(self.generate_layerstr)
        # close = QPushButton(self)
        # close.setText('Close')
        # close.setStyleSheet('background-color:#464646;color:white;')
        # close.setObjectName('dialog_close')
        # close.setCursor(QCursor(Qt.PointingHandCursor))
        # close.clicked.connect(lambda: self.close())
        spacerItem1 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        # 是否备份
        self.bak_check = QCheckBox(u'导入层已存在时是否备份(_bak)')
        btn_box.addWidget(self.bak_check)
        btn_box.addItem(spacerItem1)
        btn_box.addWidget(ok)
        # btn_box.addWidget(close)
        layout.addLayout(copy_mode)
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
        if not select_lay:
            QMessageBox.information(None, u'提示', u'请选择要导入的锣带层！')
            return
        routInput.rout_layers.extend(select_lay)
        self.bak = self.bak_check.isChecked()
        routInput.copy_mode = 'replace' if self.radio.isChecked() else 'append'
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Cleanlooks')
    app.setStyleSheet('QPushButton:hover{background:black;color:white;}')
    routInput = RoutInput()
    routInput.show()
    sys.exit(app.exec_())
