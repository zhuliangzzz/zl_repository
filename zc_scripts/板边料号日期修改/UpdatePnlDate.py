#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:UpdatePnlDate.py
   @author:zl
   @time:2024/8/10 10:18
   @software:PyCharm
   @desc:更新板边日期
"""
import datetime
import os
import sys

from PyQt5.QtWidgets import QApplication, QMessageBox
import genClasses as gen


class UpdatePnlDate:
    def __init__(self):
        self.user = job.getUser()

    def updateDate(self):
        pieces = self.get_pcs_num()
        xsize = step.profile2.xsize
        ysize = step.profile2.ysize
        string = f'{xsize}*{ysize}={pieces}PCS/PNL {datetime.date.today().year}.{"%02d" % datetime.date.today().month}.{datetime.date.today().day} {self.user.upper()}'
        step.initStep()
        step.affect(layer)
        step.setFilterTypes('text')
        step.setTextFilter('*pcs/pnl*')
        step.selectAll()
        step.resetFilter()
        if step.Selected_count():
            lines = step.INFO('-t layer -e %s/%s/%s -d features -o select,units=mm' % (jobname, step.name, layer))
            del lines[0]
            text = lines[0].split("'")[1]
            # result = re.search('(.*)\*(.*)=(\d+)PCS/PNL (.*)', text)
            # size_x, size_y, pcs_n, date_user = result.group(1), result.group(2), result.group(3), result.group(4)
            if text != string:
                res = QMessageBox.warning(None, '提醒', '检测板边文字需要更新为\n%s\n是否修改' % string, QMessageBox.Yes | QMessageBox.No)
                if res == QMessageBox.Yes:
                    step.changeText(string)
                    QMessageBox.information(None, '提醒', '已修改')
                else:
                    step.unaffectAll()
                    sys.exit()
        step.unaffectAll()

    def get_pcs_num(self):
        steps = step.info.get('gREPEATstep')  # 获取set列表
        pcs_num_map = {}
        pcs_name = set()
        for s in steps:
            if 'set' in s:
                pcs_list = list(
                    filter(lambda repeat_: str(repeat_).startswith('pcs'), job.steps.get(s).info.get('gREPEATstep')))
                pcs_name.update(pcs_list)  # 获取每个set中的pcs列表
                if s not in pcs_num_map:
                    pcs_num_map[s] = 0
                pcs_num_map[s] += len(pcs_list)
        if len(pcs_name) > 1:
            return min(pcs_num_map.values())
        else:
            return sum(pcs_num_map.values())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('fusion')
    jobname = os.environ.get('JOB')
    layer = sys.argv[1]
    job = gen.Job(jobname)
    step = job.steps.get('pnl')
    update_pnl_date = UpdatePnlDate()
    update_pnl_date.updateDate()
