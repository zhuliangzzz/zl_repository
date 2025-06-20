#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:CheckExposedWires.py
   @author:zl
   @time:2024/9/4 13:32
   @software:PyCharm
   @desc:阻焊层、覆盖膜层检查露线
"""
import json
import os
import sys
import genClasses as gen


class CheckExposedWires(object):
    def __init__(self):
        self.covs = job.matrix.returnRows('board', 'coverlay')
        self.sms = job.matrix.returnRows('board', 'solder_mask')
        if not self.covs and not self.sms:
            DoExit('OK', '没有覆盖膜和阻焊层.')
        self.layers = {}
        if 'gts' in self.sms and 'c1' in self.covs:
            self.layers['gts'] = 'c1'
        if 'gbs' in self.sms and f'c{job.SignalNum}' in self.covs:
            self.layers['gbs'] = f'c{job.SignalNum}'
        if not self.layers:
            DoExit('OK', '没有对应的覆盖膜和阻焊层.')

    def do_check(self):
        msg_list, err_text_list = [], []
        step = job.steps.get('pcs')
        if not step:
            DoExit('OK', '没有pcs.')
        step.initStep()
        for sm, cov in self.layers.items():
            sm_tmp = f'{sm}+++{step.pid}'
            cov_tmp = f'{cov}+++{step.pid}'
            step.affect(sm)
            step.copyToLayer(sm_tmp)
            step.unaffectAll()
            step.affect(sm_tmp)
            step.Contourize()
            step.clip_area(inout='outside', margin=-150)
            step.selectResize(150)
            step.unaffectAll()
            step.affect(cov)
            step.copyToLayer(cov_tmp, size=400)
            step.unaffectAll()
            step.affect(sm_tmp)
            step.refSelectFilter(cov_tmp)
            if step.Selected_count():
                Dict = {
                    'job': jobname,
                    'step': step.name,
                    'lay': [sm, cov],
                    'xy': [],
                    'chelist': ''
                }
                if Dict not in msg_list:
                    msg_list.append(Dict)
                err_text_list.append('Step:%s Layer:%s %s' % (step.name, sm, cov))
                step.unaffectAll()
        if msg_list:
            mark_text = '检测到阻焊层、覆盖膜层露线:\n%s' % '\n'.join(err_text_list)
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
    checkExposedWires = CheckExposedWires()
    checkExposedWires.do_check()