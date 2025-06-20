#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:CheckLDI.py
   @author:zl
   @time:2024/8/23 10:22
   @software:PyCharm
   @desc:检查pnl中的LDI孔是否防呆且与线路层LDI是否一致
"""
import json
import os
import re
import sys

import genClasses as gen


class CheckLDI(object):
    def __init__(self):
        layers = job.matrix.returnRows('board', 'drill')
        self.drill_layers = filter(lambda x: re.match('f\d+$|l\d+-l\d+$', x), layers)
        if 'pnl' not in job.steps:
            DoExit('OK', '没有要检查的pnl.')
        if not self.drill_layers:
            DoExit('OK', '没有要检查的通层.')

    def do_check(self):
        # err2 ldi线路不一致  err 不防错
        msg_list, err_text_list, err2_text_list = [], [], []
        step = job.steps.get('pnl')
        step.initStep()
        for drill in self.drill_layers:
            signal_list = []
            if '-' in drill:
               signal_list.extend(drill.split('-'))
            else:
                if job.SignalNum > 2:
                    signal_list.append('l1')
                    signal_list.append(f'l{job.SignalNum}')
                else:
                    signal_list.extend(job.SignalLayers)
            # 判断线路层的ldi是否和钻孔一致
            tmp_drl = f'{drill}+++{step.pid}'
            for signal in signal_list:
                step.affect(signal)
                step.selectSymbol('ldi-mark-t;ldi-mark-b;nc-ldi-t')
                tmp_signal = f'{signal}+++{step.pid}'
                step.resetFilter()
                if step.Selected_count():
                    ldi_num = step.Selected_count()
                    step.copySel(tmp_signal)
                    step.unaffectAll()
                    step.affect(drill)
                    step.refSelectFilter(tmp_signal)
                    if step.Selected_count() == ldi_num:
                        step.copySel(tmp_drl)
                    else:
                        Dict = {
                            'job': jobname,
                            'step': step.name,
                            'lay': [drill],
                            'xy': [],
                            'chelist': ''
                        }
                        if Dict not in msg_list:
                            msg_list.append(Dict)
                        err2_text_list.append('Step:%s Layer:%s' % (step.name, drill))
                        step.unaffectAll()
                        step.removeLayer(tmp_signal)
                        continue
                    step.unaffectAll()
                    step.removeLayer(tmp_signal)
                    # 判断ldi孔是否防错 x镜像 y镜像 180旋转
                    # 1.找出中心点
                    infoDict = step.DO_INFO(' -t layer -e %s/%s/%s -d LIMITS,units=mm' % (jobname, step.name, tmp_drl))
                    xmin = infoDict['gLIMITSxmin']
                    ymin = infoDict['gLIMITSymin']
                    xmax = infoDict['gLIMITSxmax']
                    ymax = infoDict['gLIMITSymax']
                    xc = (xmin + xmax) / 2
                    yc = (ymin + ymax) / 2
                    # 参考层
                    tmp_drl_ = f'{tmp_drl}+++'
                    step.affect(tmp_drl)
                    step.copySel_2(tmp_drl_, x_anchor=xc, y_anchor=yc, mirror='horizontal')
                    step.refSelectFilter(tmp_drl_)
                    if step.Selected_count() == ldi_num:
                        Dict = {
                            'job': jobname,
                            'step': step.name,
                            'lay': [drill],
                            'xy': [],
                            'chelist': ''
                        }
                        if Dict not in msg_list:
                            msg_list.append(Dict)
                        err_text_list.append('Step:%s Layer:%s 水平镜像不防错' % (step.name, drill))
                    step.truncate(tmp_drl_)
                    step.copySel_2(tmp_drl_, x_anchor=xc, y_anchor=yc, mirror='vertical')
                    step.refSelectFilter(tmp_drl_)
                    if step.Selected_count() == ldi_num:
                        Dict = {
                            'job': jobname,
                            'step': step.name,
                            'lay': [drill],
                            'xy': [],
                            'chelist': ''
                        }
                        if Dict not in msg_list:
                            msg_list.append(Dict)
                        err_text_list.append('Step:%s Layer:%s 竖直镜像不防错' % (step.name, drill))
                    step.truncate(tmp_drl_)
                    step.copySel_2(tmp_drl_, x_anchor=xc, y_anchor=yc, rotation=180)
                    step.refSelectFilter(tmp_drl_)
                    if step.Selected_count() == ldi_num:
                        Dict = {
                            'job': jobname,
                            'step': step.name,
                            'lay': [drill],
                            'xy': [],
                            'chelist': ''
                        }
                        if Dict not in msg_list:
                            msg_list.append(Dict)
                        err_text_list.append('Step:%s Layer:%s 旋转180°不防错' % (step.name, drill))
                    step.unaffectAll()
                    step.removeLayer(tmp_drl)
                    step.removeLayer(tmp_drl_)
                step.unaffectAll()
        if msg_list:
            mark_text = ''
            if err2_text_list:
                err2_text_list = list(dict.fromkeys(err2_text_list))
                mark_text += '检查到ldi孔与线路层不一致:\n%s' % '\n'.join(err2_text_list)
            if err_text_list:
                err_text_list = list(dict.fromkeys(err_text_list))
                mark_text += '检查到ldi孔不防错:\n%s' % '\n'.join(err_text_list)
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
    checkLdi = CheckLDI()
    checkLdi.do_check()
