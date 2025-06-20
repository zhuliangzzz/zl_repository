#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:TemporaryLayerComparsion-lyh.py
   @author:zl
   @time: 2024/12/25 14:46
   @software:PyCharm
   @desc:
   阴阳拼版逻辑  由于board层必须是对称的，所以不能把所有临时层一次性去改board属性
   必须循环临时层内去改board属性 两个层必须依次变成board 和misc  然后在各自为misc的时候去panel里flatten 再去对比flatten后的层
   20241230 比对层排除周期区域和sh-op区域
"""
import os
import re
import sys, platform

reload(sys)
sys.setdefaultencoding('utf8')
from PyQt4.QtCore import *
from PyQt4.QtGui import *

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
from genesisPackages_zl import get_layer_selected_limits
import genClasses_zl as gen
from genesisPackages import get_sr_area_flatten
import TemporaryLayerComparsionUI_pyqt4 as ui




class TemporaryLayerComparsion(QWidget, ui.Ui_Form):
    def __init__(self):
        super(TemporaryLayerComparsion, self).__init__()
        self.setupUi(self)
        self.render()

    def closeEvent(self, event):
        event.ignore()

    def render(self):
        self.job = gen.Job(jobname)
        self.temp_map = {}
        for row in self.job.matrix.returnRows():
            res = re.match(".*(-ls\d+.*)", row)
            if res:
                key = res.group(1)
                if key not in self.temp_map:
                    self.temp_map[key] = []
                self.temp_map[key].append(row)
        self.temp_layers = [i for val in self.temp_map.values() for i in val]  # 所有临时层
        self.flipList = []  # flip的step
        self.listWidget.addItems(self.temp_layers)
        self.comboBox_temp.addItem('')
        if self.temp_map.keys():
            self.comboBox_temp.addItems(self.temp_map.keys())
        self.listWidget.setSelectionMode(QAbstractItemView.MultiSelection)
        self.comboBox_resolution.addItems(['1', '2'])
        #
        self.checkBox_all.clicked.connect(self.select_all)
        self.comboBox_temp.currentIndexChanged.connect(self.filter_temp)
        self.pushButton_exec.clicked.connect(self.run)
        self.pushButton_exit.clicked.connect(lambda: sys.exit(1))
        self.setStyleSheet('''
        QPushButton:hover{background:black;color:white;}
        QPushButton{font:11pt;background-color:#0081a6;color:white;}
        QMessageBox{font-size:10pt;}
        QListWidget::Item{height:24px;border-radius:1.5px;} QListWidget::Item:selected{background:#0081a6;color:white;}
        ''')
        self.move((app.desktop().width() - self.geometry().width()) / 2,
                  (app.desktop().height() - self.geometry().height()) / 2)

    def filter_temp(self):
        text = str(self.comboBox_temp.currentText())
        self.listWidget.clear()
        if self.temp_map.get(text):
            self.listWidget.addItems(self.temp_map.get(text))
        else:
            self.listWidget.addItems(self.temp_layers)

    def select_all(self):
        if self.checkBox_all.isChecked():
            self.listWidget.selectAll()
        else:
            self.listWidget.clearSelection()

    def run(self):
        if not self.listWidget.selectedItems():
            QMessageBox.warning(None, u'警告', u'请选择层！')
            return
        get_sr_area_flatten("surface_fill")
        resolution = self.comboBox_resolution.currentText()
        resolution = int(resolution)
        layers = [str(item.text()) for item in self.listWidget.selectedItems()]
        board_layers = self.job.matrix.returnRows('board')
        step = gen.Step(self.job, 'panel')
        flipstep = gen.Step(self.job, "edit")
        self.flipStepName(step.name)
        # # 如果阴阳拼版 把属性取消
        dic_drill_start_end = self.get_drill_start_end_layers()
        step.initStep()
        # step.setUnits('inch')
        diff_layers = []
        for layer in layers:
            formal_layer = layer.split('-ls')[0]
            tmp_layer = '%s+++%s' % (layer, step.pid)
            tmp_formal_layer = '%s+++%s' % (formal_layer, step.pid)
            if self.flipList:
                # 临时层是board
                if layer in board_layers:
                    step.Flatten(formal_layer, tmp_formal_layer)
                    flipstep.open()
                    flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=yes' % jobname)
                    self.job.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=misc".format(jobname, layer))
                    self.job.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=board".format(jobname, formal_layer))
                    new_dic_drill_start_end = self.get_drill_start_end_layers()
                    for key, value in new_dic_drill_start_end.iteritems():
                        if value["start"] and value["end"]:

                            for new_key in [key, key.split("-ls")[0]]:
                                if not dic_drill_start_end.has_key(new_key):
                                    continue

                                if dic_drill_start_end[new_key]["start"] == value["start"] and \
                                        dic_drill_start_end[new_key]["end"] == value["end"]:
                                    continue
                                # start end 可能是正式层也可能是临时层 也可能跟目前这两层没关系
                                start = formal_layer if dic_drill_start_end[new_key]["start"] == layer else dic_drill_start_end[new_key]["start"]
                                end = formal_layer if dic_drill_start_end[new_key]["end"] == layer else dic_drill_start_end[new_key]["end"]
                                self.job.COM("matrix_layer_drill,job={0},matrix=matrix,layer={1},start={2},end={3}".format(
                                    jobname, key, start,end
                                ))
                    flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=no' % jobname)
                    step.open()
                    step.Flatten(layer, tmp_layer)
                    # 还原
                    flipstep.open()
                    flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=yes' % jobname)
                    self.job.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=board".format(jobname, layer))
                    self.job.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=misc".format(jobname, formal_layer))
                    new_dic_drill_start_end = self.get_drill_start_end_layers()
                    for key, value in new_dic_drill_start_end.iteritems():
                        if value["start"] and value["end"]:
                            for new_key in [key, key.split("-ls")[0]]:
                                if not dic_drill_start_end.has_key(new_key):
                                    continue
                                if dic_drill_start_end[new_key]["start"] == value["start"] and \
                                        dic_drill_start_end[new_key]["end"] == value["end"]:
                                    continue
                                self.job.COM(
                                    "matrix_layer_drill,job={0},matrix=matrix,layer={1},start={2},end={3}".format(
                                        jobname, key, dic_drill_start_end[new_key]["start"],
                                        dic_drill_start_end[new_key]["end"]
                                    ))
                    flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=no' % jobname)
                    step.open()
                else:
                    step.Flatten(layer, tmp_layer)
                # 正式层是board
                if formal_layer in board_layers:
                    step.Flatten(layer, tmp_layer)
                    flipstep.open()
                    flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=yes' % jobname)
                    self.job.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=misc".format(jobname, formal_layer))
                    self.job.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=board".format(jobname, layer))
                    new_dic_drill_start_end = self.get_drill_start_end_layers()
                    for key, value in new_dic_drill_start_end.iteritems():
                        if value["start"] and value["end"]:

                            for new_key in [key, key.split("-ls")[0]]:
                                if not dic_drill_start_end.has_key(new_key):
                                    continue

                                if dic_drill_start_end[new_key]["start"] == value["start"] and \
                                        dic_drill_start_end[new_key]["end"] == value["end"]:
                                    continue
                                # start end 可能是正式层也可能是临时层 也可能跟目前这两层没关系
                                start = layer if dic_drill_start_end[new_key]["start"] == formal_layer else dic_drill_start_end[new_key]["start"]
                                end = layer if dic_drill_start_end[new_key]["end"] == formal_layer else dic_drill_start_end[new_key]["end"]
                                self.job.COM("matrix_layer_drill,job={0},matrix=matrix,layer={1},start={2},end={3}".format(jobname, key, start, end))
                    flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=no' % jobname)
                    step.open()
                    step.Flatten(formal_layer, tmp_formal_layer)
                    # 还原
                    flipstep.open()
                    flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=yes' % jobname)
                    self.job.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=board".format(jobname, formal_layer))
                    self.job.COM("matrix_layer_context,job={0},matrix=matrix,layer={1},context=misc".format(jobname, layer))
                    new_dic_drill_start_end = self.get_drill_start_end_layers()
                    for key, value in new_dic_drill_start_end.iteritems():
                        if value["start"] and value["end"]:

                            for new_key in [key, key.split("-ls")[0]]:
                                if not dic_drill_start_end.has_key(new_key):
                                    continue

                                if dic_drill_start_end[new_key]["start"] == value["start"] and \
                                        dic_drill_start_end[new_key]["end"] == value["end"]:
                                    continue

                                self.job.COM(
                                    "matrix_layer_drill,job={0},matrix=matrix,layer={1},start={2},end={3}".format(
                                        jobname, key, dic_drill_start_end[new_key]["start"],
                                        dic_drill_start_end[new_key]["end"]
                                    ))
                    flipstep.COM('matrix_suspend_symmetry_check,job=%s,matrix=matrix,suspend=no' % jobname)
                    step.open()
                else:
                    step.Flatten(formal_layer, tmp_formal_layer)
            else:
                step.Flatten(layer, tmp_layer)
                step.Flatten(formal_layer, tmp_formal_layer)
            map_layer = '%s_check_compare_diff+++' % formal_layer
            step.removeLayer(map_layer)
            step.compareLayers(tmp_layer, self.job.name, step.name, tmp_formal_layer, tol=resolution * 25.4, map_layer=map_layer, map_layer_res=300)
            # 获取区域
            areas = []
            layer_cmd = gen.Layer(step, tmp_formal_layer)
            step.affect(tmp_formal_layer)
            step.selectSymbol('sh-op*')
            step.resetFilter()
            if step.Selected_count():
                feat_out = layer_cmd.featout_dic_Index(units="mm", options="feat_index+select")["pads"]
                for obj in feat_out:
                    step.clearSel()
                    step.selectByIndex(tmp_formal_layer, obj.feat_index)
                    xmin, ymin, xmax, ymax = get_layer_selected_limits(step, tmp_formal_layer)
                    areas.append([xmin - 0.5, ymin - 0.5, xmax + 0.5, ymax + 0.5])
                    step.clearSel()
                    
            step.setFilterTypes('text')
            step.selectAll()
            step.resetFilter()
            if step.Selected_count():
                feat_out = step.Features_INFO(tmp_formal_layer, mode='feat_index+select')
                index_list = []
                for feat in feat_out:
                    index, text = feat[0].replace('#', ''), feat[11].replace("'", '').lower()
                    for week_text in ["$$yy", "$${yy}", "$$ww",
                                      "$${ww}","$$month", "$${month}",
                                      "$$day", "$${day}", "$$banci",
                                      "$${banci}", "$$xingqi", "$${xingqi}",
                                      "$$picihao", "$${picihao}", "$$mm",
                                      "$${mm}", "$$dd", "$${dd}","$$year",
                                      "$${year}"]:
                        if week_text in text:
                            index_list.append(index)
                            break
                if index_list:
                    for feat_index in index_list:
                        step.clearSel()
                        step.selectByIndex(tmp_formal_layer, feat_index)
                        xmin, ymin, xmax, ymax = get_layer_selected_limits(step, tmp_formal_layer)
                        areas.append([xmin - 0.5, ymin - 0.5, xmax + 0.5, ymax + 0.5])
                        step.clearSel()

            step.unaffectAll()
            if areas:
                area_layer = 'area_layer+++'
                step.removeLayer(area_layer)
                step.createLayer(area_layer)
                step.affect(area_layer)
                for area in areas:
                    step.addRectangle(area[0], area[1],area[2],area[3])
                step.unaffectAll()
            step.affect(map_layer)
            step.resetFilter()
            step.setFilterTypes('pad')
            step.setSymbolFilter('r0')
            if step.isLayer(area_layer):
                step.refSelectFilter(area_layer, mode='cover')
                if step.Selected_count():
                    step.selectDelete()
            if step.isLayer("surface_fill"):
                step.refSelectFilter("surface_fill", mode='cover')
            else:
                step.selectAll()
            step.resetFilter()
            if step.Selected_count():
                diff_layers.append([layer, formal_layer, map_layer])
            else:
                step.removeLayer(map_layer)
            step.unaffectAll()
            step.removeLayer(area_layer)
            step.removeLayer(tmp_layer)
            step.removeLayer(tmp_formal_layer)
        if diff_layers:
            msg_list = []
            for diff_layer in diff_layers:
                msg_list.append(u'%s和%s比对有差异！请检查%s' % (diff_layer[0], diff_layer[1], diff_layer[2]))
            msg = '<span>%s<br><font style="color:red;">检测到异常，即将异常退出</font></span>' % '\n'.join(msg_list)
            QMessageBox.warning(self, u'提示', msg)
            sys.exit(1)
        else:
            QMessageBox.information(self, u'提示', u'比对通过！')
            sys.exit()

    def flipStepName(self, step):
        """
        递归寻找出有镜像的step，并append到 flipList数组中
        :param step: step名
        :return: None
        """
        info = self.job.DO_INFO('-t step -e %s/%s -m script -d SR -p flip+step' % (jobname, step))
        step_flip_tuple = [(info['gSRstep'][i], info['gSRflip'][i]) for i in range(len(info['gSRstep']))]
        step_flip_tuple = list(set(step_flip_tuple))
        for (stepName, flip_yn) in step_flip_tuple:
            if flip_yn == 'yes':
                self.flipList.append(stepName)
            elif flip_yn == 'no':
                self.flipStepName(stepName)

    def get_drill_start_end_layers(self):
        matrixInfo = self.job.matrix.getInfo()
        dic_drill_start_end = {}
        for i, layer in enumerate(matrixInfo["gROWname"]):
            if matrixInfo["gROWlayer_type"][i] == "drill" and \
                    matrixInfo["gROWcontext"][i] == "board":
                row = matrixInfo["gROWname"].index(layer)
                gROWdrl_start = matrixInfo["gROWdrl_start"][row]
                gROWdrl_end = matrixInfo["gROWdrl_end"][row]
                dic_drill_start_end[layer] = {"start": gROWdrl_start, "end": gROWdrl_end, }

        return dic_drill_start_end


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Cleanlooks')
    jobname = os.environ.get('JOB')
    temporaryLayerComparsion = TemporaryLayerComparsion()
    temporaryLayerComparsion.show()
    sys.exit(app.exec_())
