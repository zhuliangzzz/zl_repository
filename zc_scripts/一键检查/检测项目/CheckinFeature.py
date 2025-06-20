#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author:zl
# 临时层加上+++ 在退出时能清除掉临时层

import sys,json

from genClasses import *
import genClasses as gen
"""
检测板内异物
"""


class CheckinFeature:
    def __init__(self):
        self.check_steps = list(filter(lambda x: 'set' in x or 'pnl' == x, job.steps))
        if not self.check_steps:
            DoExit('OK', '没有要检查的pnl和set')
        do_usestep('pnl')

    def do_check(self):
        use_layer = job.matrix.returnRows('board', 'signal|silk_screen|solder_mask|drill')
        if not use_layer:
            DoExit('OK', '没有要检查的层')
        msg_list, err_text_list, err2_text_list = [], [], []
        # 检测pnl内pcs的板内异物
        pnl_step = job.steps.get('pnl')
        pnl_step.initStep()
        pnl_tmp = f'check_pnl+++{pnl_step.pid}'
        pnl_tmp_ = f'check_pnl_+++{pnl_step.pid}'
        pnl_step.createLayer(pnl_tmp)
        pnl_step.createLayer(pnl_tmp_)
        pnl_step.srFill(pnl_tmp, sr_margin_x=-0.01, sr_margin_y=-0.01)
        pnl_step.srFill(pnl_tmp_, sr_margin_x=-2540, sr_margin_y=-2540)
        pnl_step.affect(pnl_tmp)
        pnl_step.copySel(pnl_tmp_, 'yes')
        pnl_step.unaffectAll()
        pnl_step.affect(pnl_tmp_)
        pnl_step.Contourize()
        pnl_step.unaffectAll()
        for layer in use_layer:
            show_layer = f'pnl_pcs_{layer}+++{pnl_step.pid}'
            pnl_step.affect(layer)
            pnl_step.refSelectFilter(pnl_tmp_)
            if pnl_step.Selected_count():
                pnl_step.copySel(show_layer)
                Dict = {
                    'job': jobname,
                    'step': pnl_step.name,
                    'lay': [layer, show_layer],
                    'xy': [],
                    'chelist': ''
                }
                if Dict not in msg_list:
                    msg_list.append(Dict)
                err_text_list.append('Step:%s Layer:%s' % (pnl_step.name, layer))
            pnl_step.unaffectAll()
        # 检测pnl内set的板内异物
        pnl_step.truncate(pnl_tmp)
        pnl_step.srFill(pnl_tmp, sr_margin_x=-2540, sr_margin_y=-2540)
        # 填pnl板边的
        _pnl_tmp = f'check__pnl+++{pnl_step.pid}'
        pnl_step.createLayer(_pnl_tmp)
        pnl_step.srFill(_pnl_tmp, sr_margin_x=-0.01, sr_margin_y=-0.01, nest_sr='no')
        # 掏掉板边和set内的，剩下set区域
        pnl_step.affect(pnl_tmp_)
        pnl_step.affect(_pnl_tmp)
        pnl_step.copySel(pnl_tmp, 'yes')
        pnl_step.unaffectAll()
        pnl_step.affect(pnl_tmp)
        pnl_step.Contourize()
        pnl_step.unaffectAll()
        for layer in use_layer:
            show_layer = f'pnl_set_{layer}+++{pnl_step.pid}'
            pnl_step.affect(layer)
            pnl_step.refSelectFilter(pnl_tmp)
            if pnl_step.Selected_count():
                pnl_step.copySel(show_layer)
                Dict = {
                    'job': jobname,
                    'step': pnl_step.name,
                    'lay': [layer, show_layer],
                    'xy': [],
                    'chelist': ''
                }
                if Dict not in msg_list:
                    msg_list.append(Dict)
                err2_text_list.append('Step:%s Layer:%s' % (pnl_step.name, layer))
            pnl_step.unaffectAll()
        pnl_step.removeLayer(pnl_tmp)
        pnl_step.removeLayer(pnl_tmp_)
        pnl_step.removeLayer(_pnl_tmp)
        usestep = do_usestep('pnl')
        set_steps = list(filter(lambda x: 'set' in x, usestep))
        # pnl拼板内包含set命名的认为是set 对该step检测板内异物
        for set_ in set_steps:
            set_step = job.steps.get(set_)
            set_step.initStep()
            set_tmp = f'check_{set_}+++{set_step.pid}'
            set_tmp_ = f'check_{set_}_+++{set_step.pid}'
            set_step.createLayer(set_tmp)
            set_step.createLayer(set_tmp_)
            set_step.srFill(set_tmp, sr_margin_x=-0.01, sr_margin_y=-0.01)
            set_step.srFill(set_tmp_, sr_margin_x=-2540, sr_margin_y=-2540)
            set_step.affect(set_tmp)
            set_step.copySel(set_tmp_, 'yes')
            set_step.unaffectAll()
            set_step.affect(set_tmp_)
            set_step.Contourize()
            set_step.unaffectAll()
            for layer in use_layer:
                show_layer = f'{set_}_{layer}+++{set_step.pid}'
                set_step.affect(layer)
                set_step.refSelectFilter(set_tmp_)
                if set_step.Selected_count():
                    set_step.copySel(show_layer)
                    Dict = {
                        'job': jobname,
                        'step': set_,
                        'lay': [layer, show_layer],
                        'xy': [],
                        'chelist': ''
                    }
                    if Dict not in msg_list:
                        msg_list.append(Dict)
                    err_text_list.append('Step:%s Layer:%s' % (set_, layer))
                set_step.unaffectAll()
            set_step.removeLayer(set_tmp)
            set_step.removeLayer(set_tmp_)
        if msg_list:
            mark_text = '检测到板内有异物:'
            if err_text_list:
                mark_text += '\npcs区域：' + '\n'.join(err_text_list)
            if err2_text_list:
                mark_text += '\nset区域：' + '\n'.join(err2_text_list)
            DoExit('NG', msg=msg_list, mark=mark_text)
        else:
            DoExit('OK', '恭喜，该项检查通过.')


def do_usestep(name):
    everysteps = []
    def do_every_step(job, stepname):
        infoDict = job.DO_INFO(' -t step -e %s/%s -d REPEAT,units=mm' % (jobname, stepname))
        if infoDict['gREPEATstep']:
            stepArr = set(infoDict['gREPEATstep'])
            for s in stepArr:
                everysteps.append(str(s))
                do_every_step(job, str(s))

    do_every_step(job, name)
    return set(everysteps)


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
    checkMisssold = CheckinFeature()
    checkMisssold.do_check()
