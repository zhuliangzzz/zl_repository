#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:CheckCoverLayerLine.py
   @author:zl
   @time:2024/7/11 17:25
   @software:PyCharm
   @desc:检查pcs/set中coverlay是否有线或者弧
"""
import json
import os
import sys

import genClasses as gen


class CheckCoverLayerLine(object):
    def __init__(self):
        self.layers = job.matrix.returnRows('board', 'coverlay')
        if not self.layers:
            DoExit('OK', '没有要检查的覆盖膜层.')

    def do_check(self):
        msg_list, err_text_list = [], []
        for stepname in job.steps:
            if stepname in ('pcs', 'set'):
                step = job.steps.get(stepname)
                step.initStep()
                for layer in self.layers:
                    step.affect(layer)
                    step.setFilterTypes('line|arc')
                    step.selectAll()
                    step.resetFilter()
                    if step.Selected_count():
                        show_layer = f'{layer}+++{step.pid}'
                        step.copySel(show_layer)
                        Dict = {
                            'job': jobname,
                            'step': stepname,
                            'lay': [layer, show_layer],
                            'xy': [],
                            'chelist': ''
                        }
                        if Dict not in msg_list:
                            msg_list.append(Dict)
                        err_text_list.append('Step:%s Layer:%s' % (stepname, layer))
                    step.unaffectAll()
        if msg_list:
            mark_text = '检查到覆盖膜有线或弧:\n%s' % '\n'.join(err_text_list)
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
    checkCoverLayerLine = CheckCoverLayerLine()
    checkCoverLayerLine.do_check()
