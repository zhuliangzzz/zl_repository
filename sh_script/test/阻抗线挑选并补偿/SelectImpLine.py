#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:SelectImpLine.py
   @author:zl
   @time: 2025/3/24 8:40
   @software:PyCharm
   @desc:
"""
import math
import os
import platform
import re
import sys

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import SelectImpLineUI_pyqt4 as ui

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
import genClasses_zl as gen


class SelectImpLine(QMainWindow, ui.Ui_MainWindow):
    def __init__(self):
        super(SelectImpLine, self).__init__()
        self.setupUi(self)
        self.render()

    def render(self):
        self.step = None
        self.result_mode = 'tl_tmp_layer'
        self.split_up, self.split_down = 'imp--------', 'imp++++++++'
        self.result_mode_items = {u'挑选到辅助层': 'to_tmp_layers', u'挑选并改测': 'auto_comp', u'全部': 'all'}
        self.comboBox_result_mode.addItems(self.result_mode_items.keys())
        self.work_mode_items = {u'内层': 'inner', u'外层': 'outer', u'全部': 'all'}
        self.comboBox_work_mode.addItems(self.work_mode_items.keys())
        self.lineEdit_line_width_tol.setValidator(QDoubleValidator(self.lineEdit_line_width_tol))
        self.lineEdit_diff_spacing_tol.setValidator(QDoubleValidator(self.lineEdit_diff_spacing_tol))
        self.lineEdit_coplanar_spacing_tol.setValidator(QDoubleValidator(self.lineEdit_coplanar_spacing_tol))
        self.lineEdit_parallel_length_factor.setValidator(QDoubleValidator(self.lineEdit_parallel_length_factor))
        self.lineEdit_line_width_tol.setText('0.01')
        self.lineEdit_diff_spacing_tol.setText('0.01')
        self.lineEdit_coplanar_spacing_tol.setText('0.01')
        self.lineEdit_step.setText('edit')
        self.pushButton_exec.clicked.connect(self.run)
        self.pushButton_exit.clicked.connect(lambda: sys.exit())
        self.setStyleSheet('''
               QPushButton:hover{background:black;color:white;}
               QPushButton{font:11pt;background-color:#0081a6;color:white;}
               QMessageBox{font-size:10pt;}
               QListWidget::Item{height:24px;border-radius:1.5px;} QListWidget::Item:selected{background:#0081a6;color:white;}
               QStatusBar{color:red;}
               ''')
        self.move((app.desktop().width() - self.geometry().width()) / 2,
                  (app.desktop().height() - self.geometry().height()) / 2)

    def run(self):
        # 线宽公差
        line_width_tol = 0.1
        if self.lineEdit_line_width_tol.text():
            line_width_tol = float(self.lineEdit_line_width_tol.text())
        # 差分间距公差
        spacing_tol = 0.1
        if self.lineEdit_diff_spacing_tol.text():
            spacing_tol = float(self.lineEdit_diff_spacing_tol.text())
        # coplanar间距公差
        coplanar_spacing_tol = 0.1
        if self.lineEdit_coplanar_spacing_tol.text():
            coplanar_spacing_tol = float(self.lineEdit_coplanar_spacing_tol.text())
        # 差分阻抗线平行线长度所需比例
        parallel_length_factor = 0.3
        if self.lineEdit_parallel_length_factor.text():
            parallel_length_factor = float(self.lineEdit_parallel_length_factor.text()) / 100
        result_mode = self.comboBox_result_mode.currentText()
        work_layer = self.comboBox_work_mode.currentText()
        self.select_confirm = 'no' if self.radioButton_confirm_no.isChecked() else 'yes'
        self.delete_imp_tmp = 'no' if self.radioButton_delete_imp_no.isChecked() else 'yes'
        # stepfilter
        step_filter = str(self.lineEdit_step.text())
        print(len(job.stepsList))
        self.ref_lyr = []
        try:
            if not job.stepsList:
                QMessageBox.warning(self, 'error', '在料号中没有Step存在,将退出!')
                return
            elif len(job.stepsList) != 1:
                if step_filter:
                    self.steps = list(filter(lambda stepname: step_filter in stepname, job.stepsList))
                else:
                    self.steps = job.stepsList
                if len(self.steps) == 0:
                    QMessageBox.warning(self, 'error', '根据脚本参数过滤出的step为空，请确认资料或脚本参数!')
                    return
                elif len(self.steps) == 1:
                    self.step = self.steps[0]
                else:
                    print('aaaaaaaaaa')
                    StepDialog(self)
            else:
                self.step = job.stepsList[0]
            self.statusbar.showMessage(u'正在打开%s step' % self.step)
            step = gen.Step(job, self.step)
            step.initStep()
            units = 'inch'
            step.setUnits(units)
            matrix = job.matrix.getInfo()
            matrix_ = {}
            for i in range(len(matrix.get('gROWname'))):
                matrix_[matrix.get('gROWname')[i]] = {'side': matrix.get('gROWside')[i]}
            imp_info = self.getImpInfo()
            if not imp_info:
                QMessageBox.warning(self, 'error', '%s 中没有阻抗线信息，请确认！' % jobname)
                return
            if 'auto_comp' in self.result_mode_items.get(result_mode):
                impedance = self.get_db_impedance_info()
                for imp_item in impedance:
                    if not imp_item.get('line_width1'):
                        QMessageBox.warning(self, '标题',
                                            '脚本参数设置了阻抗自动补偿，但是阻抗模块中没有工作稿信息，请导入完整的阻抗信息。')
                        return
            not_found, must_move = [], []
            filter_imp = {}
            work_value = self.work_mode_items.get(work_layer)
            if work_value == 'selected':
                tmp_imp = []
                for value1 in imp_info.values():
                    for value2 in value1.values():
                        if not isinstance(value2, dict):
                            continue
                        for value3 in value2.values():
                            tmp_imp.append(value3)
                # 阻抗线排序
                tmp_imp.sort(key=lambda k: k.get('id'))
                # todo 请选择需要的阻抗线(单位：mil)
                ids = []
                for id in ids:
                    for imp in tmp_imp:
                        if id == imp.get('id'):
                            filter_imp[id] = imp.get('imp_lyr')
            elif work_value == 'inner':
                tmp_imp = []
                for value1 in imp_info.values():
                    for value2 in value1.values():
                        if not isinstance(value2, dict):
                            continue
                        for value3 in value2.values():
                            if matrix_[value3.get('imp_lyr')].get('side') == 'inner':
                                tmp_imp.append(value3)
                # 阻抗线排序
                tmp_imp.sort(key=lambda k: k.get('id'))
                # todo 请选择需要的阻抗线(单位：mil)
                ids = []
                for id in ids:
                    for imp in tmp_imp:
                        if id == imp.get('id'):
                            filter_imp[id] = imp.get('imp_lyr')
            elif work_value == 'outer':
                tmp_imp = []
                for value1 in imp_info.values():
                    for value2 in value1.values():
                        if not isinstance(value2, dict):
                            continue
                        for value3 in value2.values():
                            if matrix_[value3.get('imp_lyr')].get('side') in ('top', 'bottom'):
                                tmp_imp.append(value3)
                # 阻抗线排序
                tmp_imp.sort(key=lambda k: k.get('id'))
                # todo 请选择需要的阻抗线(单位：mil)
                ids = []
                for id in ids:
                    for imp in tmp_imp:
                        if id == imp.get('id'):
                            filter_imp[id] = imp.get('imp_lyr')
            else:
                for value1 in imp_info.values():
                    for value2 in value1.values():
                        if not isinstance(value2, dict):
                            continue
                        for value3 in value2.values():
                            filter_imp[value3.get('id')] = value3.get('imp_lyr')
            imp_layers = []
            if not (matrix_.get(self.split_up) and matrix_.get(self.split_down)):
                step.createLayer(self.split_up)
                step.createLayer(self.split_down)
            for layer in sorted(imp_info.keys(), key=lambda k: matrix_.get(k).get('tl_num')):
                for imp_line_width in imp_info.get(layer).keys():
                    if imp_line_width == 'max_diff_spacing':
                        continue
                    imp_id_this_line = imp_info.get(layer).get(imp_line_width).keys()
                    imp_ids = []
                    for id in filter_imp.keys():
                        if filter_imp.get(id) == layer:
                            if id in imp_id_this_line:
                                imp_ids.append(id)
                    if not imp_ids: continue
                    self.statusbar.showMessage(u'正在查找%s层的阻抗线' % layer)
                    pars = {
                        'job': jobname,
                        'step': self.step,
                        'imp_lyr': layer,
                        'imp_lines': imp_info.get(layer),
                        'max_check_spacing': imp_info.get(layer).get('max_diff_spacing'),
                        'line_width_tol': line_width_tol,
                        'diff_spacing_tol': spacing_tol,
                        'coplanar_spacing_tol': coplanar_spacing_tol,
                        'parallel_length_factor': parallel_length_factor,
                        'units': units,
                        'imp_id': imp_ids,
                        'imp_line_width': imp_line_width,
                        'imp_info': imp_info
                    }
                    result = self.recognize_imp(**pars)
                    if result == 'Cancel':
                        return
                    if result.get('not_found_imp'):
                        not_found.append(result.get('not_found_imp'))
                    if result.get('imp_layers'):
                        imp_layers.append(result.get('imp_layers'))
                    if result.get('must_move_imp'):
                        must_move.append(result.get('must_move_imp'))
            ##
            # 自动补偿
            if 'auto_comp' in self.result_mode_items.get(result_mode):
                for lyr_imp in imp_layers:
                    # todo self.compensate_imp
                    ans = self.compensate_imp(step, **lyr_imp)
                    if ans:
                        return ans
            if not_found or must_move:
                mode = 'replace'
                if not_found:
                    report = "".join(not_found)
                    report = report.replace('\n', '<br>')
                    report = re.sub('<br>$', '', report)

        except Exception as e:
            QMessageBox.critical(self, 'errir', e)
            return
        finally:
            step.unaffectAll()
            self._deleteLayer([self.split_up, self.split_down, self.ref_lyr])

    def getImpInfo(self):
        pass

    def get_db_impedance_info(self):
        pass


    def compensate_imp(self, step, **par):
        step.clearAll()
        for imp_lyr in par.keys():
            step.display(imp_lyr)
            step.selectAll()
            if not step.Selected_count():
                step.unaffectAll()
                continue
            tmp = imp_lyr.split('+')
            if self.select_confirm == 'yes':
                if 'z' in tmp[3]:
                    self.statusbar.showMessage('检查[%s]辅助层中线宽为%s,间距为%s,阻值为%s的阻抗线是否挑选正确，检查完成后点continue进行自动补偿...' % (par[imp_lyr], tmp[1], tmp[2], tmp[3]))
                elif 'z' in tmp[2]:
                    self.statusbar.showMessage('检查[%s]辅助层中线宽为%s,阻值为%s的阻抗线是否挑选正确，检查完成后点continue进行自动补偿...' % (par[imp_lyr], tmp[1], tmp[2]))
                else:
                    self.statusbar.showMessage('检查[%s]辅助层中线宽为%s的阻抗线是否挑选正确，检查完成后点continue进行自动补偿...' % (par[imp_lyr], tmp[1]))
                layer_tmp = imp_lyr.split('+')
                if step.isLayer('%s-%s-ref-layer-tl+++' % (par[imp_lyr]['imp_layer'], layer_tmp[1])):
                    step.clearAll()
                    step.affect('%s-%s-ref-layer-tl+++' % (par[imp_lyr]['imp_layer'], layer_tmp[1]))
                    step.refSelectFilter(imp_lyr)
                    if step.Selected_count():
                        step.selectDelete()
                    step.unaffectAll()
                    step.display(imp_lyr)
                    step.display_layer('%s-%s-ref-layer-tl+++' % (par[imp_lyr]['imp_layer'], layer_tmp[1]), 2)
                else:
                    step.display_layer(par[imp_lyr]['imp_layer'], 2)
                ans = step.PAUSE('Please check the IMP lines...')
                if ans != 'OK':
                    return
            features = step.INFO('-t layer -e %s/%s/%s -m script -d FEATURES -o select' % (jobname, step.name, imp_lyr))
            del features[0]
            features[0].split()






    def recognize_imp(self, **kwargs):
        job = kwargs.get('job')
        step = kwargs.get('step')
        imp_lyr = kwargs.get('imp_lyr')
        imp_lines = kwargs.get('imp_lines')  # 阻抗信息表
        max_check_spacing = kwargs.get('max_check_spacing')
        line_width_tol = kwargs.get('line_width_tol')
        diff_spacing_tol = kwargs.get('diff_spacing_tol')
        diff_spacing_tol = kwargs.get('diff_spacing_tol')
        parallel_length_factor = kwargs.get('parallel_length_factor')
        line_surface = 'tl_line_surface'
        tmp_layer = 'tl_tmp_layer'
        temp_layer = 'tl_temp_layer'
        tmp_line_layer = 'tl_tmp_line'
        units = kwargs.get('units')
        imp_line_width = kwargs.get('imp_line_width')
        imp_ids = kwargs.get('imp_id')
        imp_info = kwargs.get('imp_info')
        gen_step = gen.Step(job, step)
        if gen_step.isLayer(imp_lyr):
            work_layer = 'for_' + imp_lyr if gen_step.isLayer('for_' + imp_lyr) else imp_lyr
            gen_step.affect(work_layer)
        else:
            return
        ### 选出先放到临时层
        gen_step.setFilterTypes_pro('line|arc', 'positive')
        gen_step.COM('set_filter_profile,mode=1')
        gen_step.setSymbolFilter('r*')
        gen_step.selectAll()
        gen_step.resetFilter()
        if not gen_step.Selected_count():
            return
        gen_step.removeLayer(tmp_layer)
        gen_step.copySel(tmp_layer)
        gSYMS_HISTsymbol = gen_step.layers.get(tmp_layer).info.get('gSYMS_HISTsymbol')
        symhist = {}
        for symbol in gSYMS_HISTsymbol:
            if symbol not in symhist.keys():
                symhist[symbol] = float(symbol.replace('r', ''))
        true_line_width = imp_line_width
        if imp_line_width:
            ##先检查other中是否存在信息，存放真正的客户原稿信息（原稿信息可能被mi修改）
            imps = imp_lines.get(imp_line_width).values()
            if imps[0].get('other_org_info'):
                other_org_info = imps[0].get('other_org_info')
                if other_org_info[0].get('org_line_width'):
                    true_line_width = other_org_info[0].get('org_line_width')/25.4
            ## 辅助层上过滤掉和要挑选的阻抗线宽无关的线
            gen_step.unaffectAll()
            gen_step.affect(tmp_layer)
            for sym in symhist.keys():
                size = symhist[sym]
                upper = size + line_width_tol
                lower = size - line_width_tol
                if true_line_width < lower or true_line_width > upper:
                    gen_step.setFilterTypes_pro('line|arc', 'positive')
                    gen_step.COM('set_filter_profile,mode=1')
                    gen_step.setSymbolFilter(sym)
                    gen_step.selectAll()
                    if gen_step.Selected_count():
                        gen_step.selectDelete()
            gen_step.selectAll()
            if gen_step.Selected_count():
                gen_step.removeLayer(imp_lyr+'-'+imp_line_width+'-ref-layer-tl+++')
                gen_step.createLayer(imp_lyr+'-'+imp_line_width+'-ref-layer-tl+++')
                self.ref_lyr.append(imp_lyr+'-'+imp_line_width+'-ref-layer-tl+++')
            gen_step.unaffectAll()
        # my($diff_flag,$spacing_length);
        #
        # my @ not_found_imp_lines;
        # my $imp_resize;
        #
        # my @ spacing_must_move;  ##调整后需要移线
        diff_flag, spacing_length = None,None
        not_found_imp_lines = []
        imp_resize = {}
        spacing_must_move = []
        for line_width in sorted(imp_lines.keys()):
            if not re.match('[0-9]+\.?[0-9]*',line_width):
                continue
            if not abs(line_width - imp_line_width) < 0.01:
                continue
            for imp in imp_lines.get(line_width).values():
                if spacing_length:
                    break
                if re.match('diff', imp.get('type')):
                    self.statusbar.showMessage('正在执行线路分析checklist获得间距信息')
                    spacing_length = self.get_spacing_length()
            self.statusbar.showMessage('正在挑选%s层线宽为%s的阻抗线...' % (imp_lyr, line_width))
            upper = true_line_width + line_width_tol
            lower = true_line_width - line_width_tol
            gen_step.affect(tmp_layer)
            gen_step.removeLayer(tmp_line_layer)
            gen_step.createLayer(tmp_line_layer)
            for item in symhist.keys():
                if re.match('r[0-9]+\.?[0-9]*', item):
                    if symhist[item] >= lower and symhist[item] <= upper:
                        gen_step.selectSymbol(item)
                        gen_step.copySel(tmp_line_layer)
            gen_step.unaffectAll()
            gen_step.affect(tmp_line_layer)
            gen_step.COM('sel_all_feat')
            if not gen_step.Selected_count():
                for imp in imp_lines.get(line_width).values():
                    if re.match('diff', imp.get('type')):
                        not_found_imp_lines.append('  类型：difference,  层别: %s,  线宽: %s, 间距：%s\n' % (imp.get("imp_lyr"), imp.get("line_width"), imp.get("diff_spacing")))
                    elif re.search('single', imp.get('type')):
                        not_found_imp_lines.append('  类型：single,   层别: %s,  线宽: %s\n' % (imp_lyr, line_width))
                return
            gen_step.copySel(line_surface)
            gen_step.unaffectAll()
            gen_step.affect(line_surface)
            gen_step.Contourize(0.25, clean_hole_size=3)
            gen_step.unaffectAll()
            self.statusbar.showMessage('正在挑选差分阻抗线...')
            diff_imp_tmp_layer = []
            for imp in imp_lines.get(line_width).values():
                if not list(filter(lambda id: imp.get('id') == id, imp_ids)):
                    continue
                if re.match('diff', imp.get('type'), re.I):
                    target_lyr = '%s+%s+%s+z%s' % (imp_lyr, line_width, imp.get('diff_spacing'), imp.get('target_impedance'))
                    if gen_step.isLayer(target_lyr):
                        gen_step.affect(target_lyr)
                        gen_step.selectDelete()
                        gen_step.unaffectAll()
                        rownum = job.matrix.getRow(self.split_down)
                        job.matrix.modifyRow(target_lyr, rownum)
                    else:
                        gen_step.createLayer(target_lyr, ins_layer=self.split_down)
                    self.statusbar.showMessage('正在通过计算查找线宽:%s mil,间距:%s mil的差分阻抗' % (line_width, imp.get('diff_spacing')))
                    true_check_spacing = imp.get('diff_spacing')
                    if imp.get('other_org_info'):
                        other_org_info = imp.get('other_org_info')
                        if other_org_info[0].get('org_line_width'):
                            true_check_spacing = other_org_info[0].get('org_line_width') / 25.4
                    s_lower = true_check_spacing - diff_spacing_tol
                    s_upper = true_check_spacing + diff_spacing_tol
                    ## 双线过滤掉没有间距的线
                    line_surface_tmp, tmp_line_layer_tmp = line_surface + '_tmp_tl', tmp_line_layer + '_tmp_tl'
                    if spacing_length:
                        checklist = 'topcam_imp_line_rec'
                        # todo $GEN->chklistCreateLyrs(chklist=>$checklist,severity=>3,suffix=>'tl');
                        tmp = 'ms_1_tl_tmp_layer_tl'
                        gen_step.affect(tmp)
                        gSYMS_HISTsymbol = gen_step.layers.get(tmp).info.get('gSYMS_HISTsymbol')
                        symhist = {}
                        for symbol in gSYMS_HISTsymbol:
                            if symbol not in symhist.keys():
                                symhist[symbol] = float(symbol.replace('r', ''))
                        for item in symhist.keys():
                            if re.search('^r[0-9]+\.?[0-9]*',item):
                                if s_lower <= symhist[sym] <= s_upper:
                                    gen_step.setFilterTypes('line', 'positive')
                                    gen_step.setSymbolFilter(item)
                                    gen_step.setAttrFilter_pro('.string', text='spacing_length')
                                    gen_step.selectAll()
                        gen_step.resetFilter()
                        if gen_step.Selected_count():
                            gen_step.selectReverse()
                            if gen_step.Selected_count():
                                gen_step.selectDelete()
                        gen_step.selectResize(1)
                        gen_step.unaffectAll()
                        gen_step.affect(line_surface)
                        gen_step.copySel(line_surface_tmp)
                        gen_step.unaffectAll()
                        gen_step.affect(line_surface_tmp)
                        gen_step.refSelectFilter(tmp)
                        if gen_step.Selected_count():
                            gen_step.selectReverse()
                            if gen_step.Selected_count():
                                gen_step.selectDelete()
                        gen_step.unaffectAll()
                        gen_step.affect(tmp_line_layer)
                        gen_step.copySel(tmp_line_layer_tmp)
                        gen_step.unaffectAll()
                        gen_step.affect(tmp_line_layer_tmp)
                        gen_step.refSelectFilter(line_surface_tmp)
                        if gen_step.Selected_count():
                            gen_step.selectReverse()
                            if gen_step.Selected_count():
                                gen_step.selectDelete()
                        self._deleteLayer([tmp, 'mk_1_tl_tmp_layer_tl'])
                    gen_step.unaffectAll()
                    # layer_obj = gen.Layer(gen_step, tmp_line_layer_tmp)
                    polylines = self.get_poly_lines(gen_step, tmp_line_layer_tmp)
                    self.statusbar.showMessage('正在通过计算查找线宽:%s mil,间距:%s mil的差分阻抗' % (line_width, imp.get("diff_spacing")))
                    # my $record;
                    # my @tmp_record;
                    # my $index = 1;
                    record = {}
                    for spacing in spacing_length.keys():
                        if s_lower <= spacing <= s_upper:
                            for mea_line in spacing_length.get('spacing').values():
                                imp_width = mea_line.get('line1')
                                imp_width = imp_width.replace('r', '')
                                if lower <= imp_width <= upper:
                                    line_paires = []
                                    for polyline in polylines:
                                        for line in polylines.get(polyline).values():
                                            mea2line = true_line_width / 2 + mea_line.get('spacing') / 2
                                            centerx = mea_line.get('xs') + mea_line.get('xe') / 2
                                            centery = mea_line.get('ys') + mea_line.get('ye') / 2
                                            l_centerx = line.get('xs') + line.get('xe') / 2
                                            l_centery = line.get('ys') + line.get('ye') / 2
                                            if ((centerx < line.get('xs') and centerx < line.get('xe')) or (centerx > line.get('xs') and centerx > line.get('xe'))) \
                                                and ((centery < line.get('ys') and centery < line.get('ye')) or (centery > line.get('ys') and centery > line.get('ye'))):
                                                continue
                                            dis = self.point2line_dist(centerx, centery, line) * 1000
                                            if abs(dis - mea2line) < 1:
                                                line_paires.append(line)
                                                break
                                        if len(line_paires) == 1:
                                            break
                                    key = line_paires[0] + '_' + line_paires[1]
                                    if key in record.keys():
                                        key_num = len(record.get(key).keys())
                                    else:
                                        key_num = len(record.get(key).keys())
                                        record[key] = {}
                                    record[key][key_num + 1] = mea_line
                    if record:
                        flag = None
                        for id in imp_ids:
                            if id == imp.get('id'):
                                flag = 'yes'
                                break
                        if flag == 'yes':
                            not_found_imp_lines.append('  类型：difference, 层别: %s, 线宽: %s mil, 间距：%s mil,阻值：%s\n' % (imp.get('imp_lyr'), imp.get('line_width'), imp.get('diff_spacing'), imp.get('target_impedance')))
                        continue
                    gen_step.removeLayer(temp_layer)
                    gen_step.createLayer(temp_layer)
                    gen_step.affect(temp_layer)
                    num = len(record.keys())
                    for key in record.keys():
                        self.statusbar.showMessage('去除掉平行线部分长度没达到比例%s的差分阻抗线' % parallel_length_factor)
                        polyline1, polyline2 = key.split('_')
                        if polyline1 == '' or polyline2 == '':
                            continue
                        polyline_length = 0.001
                        for line in polylines.get(polyline1).values():
                            polyline_length = math.sqrt((line['xs'] - line['xe'])**2 + (line['ys'] - line['ye'])**2) + polyline_length
                        for line in polylines.get(polyline2).values():
                            polyline_length = math.sqrt((line['xs'] - line['xe'])**2 + (line['ys'] - line['ye'])**2) + polyline_length
                        parallel_length = 0
                        for line in record[key].values():
                            parallel_length = math.sqrt((line['xs'] - line['xe'])**2 + (line['ys'] - line['ye'])**2) + parallel_length
                        parallel_length *=2
                        if parallel_length/polyline_length < parallel_length_factor:
                            continue
                        centerx = record[key][1]['xs'] + record[key][1]['xe'] / 2
                        centery = record[key][1]['ys'] + record[key][1]['te'] / 2
                        gen_step.addPad(centerx, centery, 'r%s' % record[key][1]['spacing'] + 0.2)
                    gen_step.unaffectAll()
                    gen_step.affect(line_surface_tmp)
                    gen_step.setFilterTypes('surface', 'positive')
                    gen_step.refSelectFilter2(temp_layer, types='pad', polarity='positive')
                    if not gen_step.Selected_count():
                        self._deleteLayer([tmp_line_layer_tmp, line_surface_tmp])
                        not_found_imp_lines.append('  类型：difference, 层别: %s, 线宽: %s mil, 间距：%s mil,阻值：%s\n' % (imp.get('imp_lyr'), imp.get('line_width'), imp.get('diff_spacing'), imp.get('target_impedance')))
                        continue
                    gen_step.affect(tmp_line_layer)
                    gen_step.setFilterTypes('line|arc', 'positive')
                    gen_step.COM('sel_ref_feat,layers=%s,use=select,mode=touch,f_types=surface,polarity=positive,include_syms=,exclude_syms=' % line_surface_tmp)
                    gen_step.COM('sel_options,clear_mode=clear_none')
                    gen_step.resetFilter()
                    if gen_step.Selected_count():
                        if imp['type'].lower().endswith('coplanar'):
                            gen_step.addAttr_zl('.imp_line')
                            gen_step.addAttr_zl('.imp_type,option=differential coplanar')
                            gen_step.addAttr_zl('.string,text=space:%s' % imp.get('diff_spacing'))
                            gen_step.addAttr_zl('.imp_info,text=%s' % imp.get('id'))
                            gen_step.COM('sel_change_atr,mode=add')
                        else:
                            gen_step.addAttr_zl('.imp_line')
                            gen_step.addAttr_zl('.imp_type,option=differential')
                            gen_step.addAttr_zl('.string,text=space:%s' % imp.get('diff_spacing'))
                            gen_step.addAttr_zl('.imp_info,text=%s' % imp.get('id'))
                            gen_step.COM('sel_change_atr,mode=add')
                        diff_imp_tmp_layer.append(target_lyr)
                    else:
                        gen_step.display(target_lyr)
                        if diff_imp_tmp_layer:
                            for i, imp_tmp_layer in enumerate(diff_imp_tmp_layer):
                                gen_step.display_layer(imp_tmp_layer, i+2)
                                if i > 2:
                                    break
                        self.statusbar.showMessage('阻抗类型：difference, 层别: %s, 线宽: %s mil, 间距：%s mil,阻值：%s未挑出，请确认是否在其他层上！' % (imp.get('imp_lyr'), imp.get('line_width'), imp.get('diff_spacing'), imp.get('target_impedance')))
                        ans = gen_step.PAUSE('Please Check')
                        if ans != 'OK':
                            return
                        gen_step.clearAll()
                        gen_step.affect(target_lyr)
                        gen_step.selectAll()
                        if not gen_step.Selected_count():
                            not_found_imp_lines.append('  类型：difference, 层别: %s, 线宽: %s mil, 间距：%s mil,阻值：%s\n' % (imp.get('imp_lyr'), imp.get('line_width'), imp.get('diff_spacing'), imp.get('target_impedance')))
                        gen_step.clearAll()
                        continue
                    gen_step.COM('sel_options,clear_mode=clear_after')
                    if gen_step.Selected_count():
                        flag = None
                        for id in imp_ids:
                            if id == imp['id']:
                                flag = 'yes'
                                break
                        if flag == 'yes':
                            gen_step.moveSel(target_lyr)
                            imp_resize[target_lyr]['dest_width'] = imp['dest_width']
                            imp_resize[target_lyr]['imp_layer'] = imp_lyr
                        else:
                            gen_step.selectDelete()
                    gen_step.selectAll()
                    if not gen_step.Selected_count():
                        not_found_imp_lines.append(
                            '  类型：difference, 层别: %s, 线宽: %s mil, 间距：%s mil,阻值：%s\n' % (
                            imp.get('imp_lyr'), imp.get('line_width'), imp.get('diff_spacing'),
                            imp.get('target_impedance')))
                    gen_step.clearAll()
                    gen_step.affect(target_lyr)
                    gen_step.selectAll()
                    if not gen_step.Selected_count():
                        if abs(abs(line_width - imp['dest_width']) - abs(imp['diff_spacing'] - imp['dest_spacing']))> 0.001:
                            spacing_must_move.append('  类型：difference, 层别: %s, 线宽: %s, 间距：%s, 调整线宽：%s, 调整间距： %s\n' % (imp.get('imp_lyr'), imp.get('line_width'), imp.get('diff_spacing'),imp.get('dest_width'),imp.get('dest_spacing')))
                    gen_step.unaffectAll()
                    self._deleteLayer([temp_layer, tmp_line_layer_tmp, line_surface_tmp])
            # 挑选单端阻抗
            self.statusbar.showMessage('正在挑选单端阻抗线...')
            diff_imp_tmp_layer = []
            for imp in imp_lines[line_width].values():
                if not imp['type'].lower().startswith('single'):
                    continue
                if not list(filter(lambda id: id == imp['id'], imp_ids)):
                    continue
                target_lyr = '%s+%s+z%s' % (imp_lyr, line_width, imp['target_impedance'])
                if gen_step.isLayer(target_lyr):
                    gen_step.affect(target_lyr)
                    gen_step.selectDelete()
                    gen_step.unaffectAll()
                    rownum = job.matrix.getRow(self.split_down)
                    job.matrix.modifyRow(target_lyr, rownum)
                else:
                    gen_step.createLayer(target_lyr, ins_layer=self.split_down)
                ##
                gen_step.unaffectAll()
                gen_step.affect(tmp_line_layer)
                gen_step.selectAll()
                if gen_step.Selected_count():
                    diff_imp_tmp_layer.append(target_lyr)
                    if imp['type'].lower().endswith('coplanar'):
                        gen_step.addAttr_zl('.imp_line')
                        gen_step.addAttr_zl('.imp_type,option=single-ended coplanar')
                        gen_step.addAttr_zl('.string,text=type:single')
                        gen_step.addAttr_zl('.imp_info,text=%s' % imp.get('id'))
                        gen_step.COM('sel_change_atr,mode=add')
                    else:
                        gen_step.addAttr_zl('.imp_line')
                        gen_step.addAttr_zl('.imp_type,option=single-ended')
                        gen_step.addAttr_zl('.string,text=type:single')
                        gen_step.addAttr_zl('.imp_info,text=%s' % imp.get('id'))
                        gen_step.COM('sel_change_atr,mode=add')
                    gen_step.moveSel(target_lyr)
                    imp_resize[target_lyr]['dest_width'] = imp['dest_width']
                    imp_resize[target_lyr]['imp_layer'] = imp_lyr
                else:
                    gen_step.unaffectAll()
                    gen_step.display(target_lyr)
                    if diff_imp_tmp_layer:
                        for i, imp_tmp_layer in enumerate(diff_imp_tmp_layer):
                            gen_step.display_layer(imp_tmp_layer, i + 2)
                            if i > 2:
                                break
                    self.statusbar.showMessage('阻抗类型：single, 层别: %s, 线宽: %s mil,阻值：%s未挑出，请确认是否在其他层上！' % (imp_lyr, line_width, imp['target_impedance']))
                    ans = gen_step.PAUSE('Please Check')
                    if ans != 'OK':
                        return
                    gen_step.clearAll()
                    gen_step.affect(target_lyr)
                    gen_step.selectAll()
                    if not gen_step.Selected_count():
                        not_found_imp_lines.append('  类型：single, 层别: %s, 线宽: %s mil,阻值：%s\n' % (imp.get('imp_lyr'), imp.get('line_width'), imp.get('target_impedance')))
                    gen_step.unaffectAll()
                    continue
                line_surface = 'tl_line_surface'
                tmp_layer = 'tl_tmp_layer'
                temp_layer = 'tl_temp_layer'
                tmp_line_layer = 'tl_tmp_line'
                self._deleteLayer([temp_layer, line_surface, tmp_line_layer])
        self._deleteLayer([tmp_layer, temp_layer, line_surface, tmp_line_layer])
        return_ = {}
        return_['not_found_imp'] = [not_found_imp_lines]
        return_['must_move_imp'] = [spacing_must_move]
        return_['imp_layers'] = imp_resize
        return return_

    def _deleteLayer(self, *args):
        layers = []
        [layers.extend(arg) for arg in args]
        for layer in layers:
            job.matrix.deleteRow(layer)

    def get_poly_lines(self, gen_step, layer):
        features = gen_step.INFO('-t layer -e %s/%s/%s -m script -d FEATURES' % (jobname, gen_step.name,layer))
        self.statusbar.showMessage(u'正在获得poly lines')
        lines = []
        polyline = {}
        for feature in features:
            if feature.startswith('#L'):
                lines.append(feature)
        polylines_flag = 1
        line_flag = 1
        for i in range(len(lines)):
            line_info1 = lines[i].split()
            line_info2 = lines[i+1].split()
            polyline[polylines_flag][line_flag] = {
                'xs': line_info1[1],
                'ys': line_info1[2],
                'xe': line_info1[3],
                'ye': line_info1[4],
                'symbol': line_info1[5],
            }
            if line_info1[3] == line_info2[1] and line_info1[4] == line_info2[2]:
                line_flag += 1
                polyline[polylines_flag][line_flag] = {
                    'xs': line_info2[1],
                    'ys': line_info2[2],
                    'xe': line_info2[3],
                    'ye': line_info2[4],
                    'symbol': line_info1[5],
                }
            else:
                polylines_flag += 1
                line_flag = 1
        return polyline
    def point2line_dist(self, x, y, line):
        # 如果线段长度为0，则无法计算垂直距离
        xs, ys, xe, ye = line.get('xs'), line.get('ys'), line.get('xe'), line.get('ye')
        if xs == xe and ys == ye:
            return None

        # 使用点到直线距离公式：|Ax + By + C|/√(A² + B²)
        # 其中直线方程为：Ax + By + C = 0
        # A = y2-y1, B = x1-x2, C = x2*y1 - x1*y2

        A = ye - ys
        B = xs - xe
        C = xe * ys - xs * ye

        # 计算垂直距离
        distance = abs(A * x + B * y + C) / math.sqrt(A * A + B * B)
        return distance

class StepDialog(QDialog):
    def __init__(self, parent=None):
        super(StepDialog, self).__init__(parent)
        self.stepList = sil.steps
        self.setupUI()
        self.exec_()

    def setupUI(self):
        self.setWindowTitle(u'请选择工作step')
        self.search_input = QLineEdit()
        self.listWidget = QListWidget()
        self.listWidget.addItems(self.stepList)
        self.search_input.textChanged.connect(self.search)
        layout = QVBoxLayout(self)
        btn_box = QHBoxLayout()
        ok = QPushButton(self)
        ok.setText(u'√确定')
        ok.setStyleSheet('background-color:#0081a6;color:white;')
        ok.setObjectName('dialog_ok')
        ok.setCursor(QCursor(Qt.PointingHandCursor))
        ok.clicked.connect(self.generate_stepstr)
        close = QPushButton(self)
        close.setText(u'×取消')
        close.setStyleSheet('background-color:#464646;color:white;')
        close.setObjectName('dialog_close')
        close.setCursor(QCursor(Qt.PointingHandCursor))
        close.clicked.connect(lambda: self.close())
        spacerItem1 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        btn_box.addItem(spacerItem1)
        btn_box.addWidget(ok)
        btn_box.addWidget(close)
        layout.addWidget(self.search_input)
        layout.addWidget(self.listWidget)
        layout.addLayout(btn_box)
        self.setStyleSheet('QPushButton{font-family:黑体;font-size:10pt;}')

    def search(self):
        search_result = []
        key = str(self.search_input.text())
        if key:
            for step in self.stepList:
                if key in step:
                    search_result.append(step)
        else:
            search_result = self.stepList
        self.listWidget.clear()
        self.listWidget.addItems(search_result)

    def generate_stepstr(self):
        if not len(self.listWidget.SelectItems()):
            QMessageBox.warning(self, 'error', '请选择step!')
            return
        sil.step = self.listWidget.SelectItems()[0].text()
        self.close()


if __name__ == '__main__':
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    app = QApplication(sys.argv)
    app.setStyle('Cleanlooks')
    sil = SelectImpLine()
    sil.show()
    sys.exit(app.exec_())
