#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:CheckCCD2Profile.py
   @author:zl
   @time:2024/8/13 15:12
   @software:PyCharm
   @desc:检查ccd层距离pnl边小于8mm
"""
import json
import os
import re
import sys

import genClasses as gen


class CheckCCD2Profile(object):
    def __init__(self):
        if 'pnl' not in job.steps:
            DoExit('OK', '没有要检查的pnl.')
        self.ccds = filter(lambda row: re.match('ccd\d+$', row), job.matrix.returnRows())
        # 检查的值 mm
        self.check_val = 8
        if not self.ccds:
            DoExit('OK', '没有要检查的ccd层.')

    def do_check(self):
        msg_list, err_text_list = [], []
        step = job.steps.get('pnl')
        step.initStep()
        # 板边向内铺8mm铜 如果ccd层有接触到说明有距板边小于8mm
        _tmp = f'pnl_8mm+++{step.pid}'
        step.createLayer(_tmp)
        step.affect(_tmp)
        step.srFill_2(step_max_dist_x=self.check_val, step_max_dist_y=self.check_val)
        step.unaffectAll()
        for ccd in self.ccds:
            step.affect(ccd)
            step.refSelectFilter(_tmp)
            if step.Selected_count():
                show_ccd = f'{ccd}_show+++{step.pid}'
                step.copySel(show_ccd)
                Dict = {
                    'job': jobname,
                    'step': step.name,
                    'lay': [ccd, show_ccd],
                    'xy': [],
                    'chelist': ''
                }
                if Dict not in msg_list:
                    msg_list.append(Dict)
                err_text_list.append('Step:%s Layer:%s' % (step.name, ccd))
            step.unaffectAll()
        step.removeLayer(_tmp)
        if msg_list:
            mark_text = f'检查到ccd层有物件距板边小于{self.check_val}mm:\n%s' % '\n'.join(err_text_list)
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
    # path = 'D:/tmp/fpcchecklist/'
    path = f'{save_file_path}tmp/fpcchecklist/'
    if not os.path.exists(path):
        os.makedirs(path)
    returnXML = path + toppid + '_return.xml'
    if os.environ['JOB'] == '':
        DoExit(mark='没有打开料号')
    jobname = os.environ['JOB']
    job = gen.Job(jobname)
    checkCCD2Profile = CheckCCD2Profile()
    checkCCD2Profile.do_check()
