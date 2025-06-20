#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:CheckStepsName.py
   @author:zl
   @time:2024/7/1 17:42
   @software:PyCharm
   @desc:检查step名称是否不符
"""
import json
import os
import re
import sys

import genClasses as gen


class CheckStepsName(object):
    def do_check(self):
        missing_steps = []
        for step in ('orig', 'pcs', 'set', 'pnl'):
            if step not in job.steps:
                missing_steps.append(step)
        if missing_steps:
            mark_text = '检查到step缺失:%s' % '、'.join(missing_steps)
            DoExit('NG', msg=[], mark=mark_text)
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
    checkStepsName = CheckStepsName()
    checkStepsName.do_check()
