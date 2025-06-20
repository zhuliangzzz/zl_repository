#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:CheckCloseHoleSpacing.py
   @author:zl
   @time:2024/7/16 15:01
   @software:PyCharm
   @desc:检查ccd孔间距是否小于1.8mm
"""
import json
import os
import re
import sys

import genClasses as gen


class CheckCloseHoleSpacing(object):
    def __init__(self):
        if 'pnl' not in job.steps:
            DoExit('OK', '没有要检查的pnl.')
        self.ccds = filter(lambda row: re.match('ccd\d+$', row), job.matrix.returnRows())
        # 检查的值 mm
        self.check_val = 1.8
        if not self.ccds:
            DoExit('OK', '没有要检查的ccd层.')

    def do_check(self):
        msg_list, err_text_list = [], []
        step = job.steps.get('pnl')
        step.initStep()
        # 钻孔分析
        checklist = gen.Checklist(step, 'checkcloseholespacing_check', 'valor_analysis_drill')
        checklist.action()
        # ((pp_drill_layer=ccd1)(pp_rout_distance=5080)(pp_tests=Hole
        #  Size\;Hole Separation\;Missing Holes\;Extra Holes\;Power / Ground Shorts\;NPTH to Rout)(
        #     pp_extra_hole_type=Pth\;Via)(pp_use_compensated_rout=Skeleton)
        params = {'pp_drill_layer': ';'.join(self.ccds),
                  'pp_rout_distance': '5080',
                  'pp_tests': 'Hole Size\;Hole Separation\;Missing Holes\;Extra Holes\;Power/Ground Shorts\;NPTH to Rout',
                  'pp_extra_hole_type': 'Pth\;Via',
                  'pp_use_compensated_rout': 'Skeleton'
                  }
        checklist.update(params=params)
        checklist.run()
        # 分析保存checklist
        checklist.clear()
        checklist.update(params=params)
        checklist.copy()
        if checklist.name in step.checks:
            step.deleteCheck(checklist.name)
        step.createCheck(checklist.name)
        step.pasteCheck(checklist.name)
        info = step.INFO('-t check -e %s/%s/%s -d MEAS -o action=1+category=closeh,units=mm' % (jobname, step.name, checklist.name))
        for line in info:
            layer, min_close = line.split()[1], line.split()[2]
            if float(min_close) < self.check_val * 1000:
                Dict = {
                    'job': jobname,
                    'step': step.name,
                    'lay': [layer],
                    'xy': [],
                    'chelist': checklist.name
                }
                if Dict not in msg_list:
                    msg_list.append(Dict)
                    err_text_list.append('Step:%s Layer:%s 最小间距：%s mm' % (step.name, layer, float(min_close)/1000))
        if msg_list:
            mark_text = f'检查到ccd层孔间距小于{self.check_val}mm:\n%s' % '\n'.join(err_text_list)
            DoExit('NG', msg=msg_list, mark=mark_text)
        else:
            DoExit('OK', '恭喜，该项检查通过.')


def DoExit(state='error', mark='', msg=[]):
    """
    ***所有退出状态都需要用此函数***
        state = [error|ok|ng]   :为异常退出
        mark = ''   :为返回的备注信息
        msg = {}    :为返回的字典,存脚本结果
    """
    Dict = {
        'state': state,
        'mark': mark,
        'msg': msg
    }
    str_json = json.dumps(Dict, ensure_ascii=False)
    with open(returnXML, 'w', encoding='utf-8') as file:
        file.write(str_json)
    print(str_json)
    sys.exit(0)


if __name__ == '__main__':
    toppid = sys.argv[1]
    # 返回结果路径
    save_file_path = '//172.16.0.106/scripts/'
    path = f'{save_file_path}tmp/fpcchecklist/'
    if not os.path.exists(path):
        os.makedirs(path)
    returnXML = path + toppid + '_return.xml'
    if os.environ['JOB'] == '':
        DoExit(mark='没有打开料号')
    jobname = os.environ['JOB']
    job = gen.Job(jobname)
    checkCloseHoleSpacing = CheckCloseHoleSpacing()
    checkCloseHoleSpacing.do_check()
