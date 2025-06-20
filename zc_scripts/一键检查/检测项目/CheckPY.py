#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:CheckLDI.py
   @author:zl
   @time:2024/8/23 14:22
   @software:PyCharm
   @desc:检查pnl中的py孔是否防呆且与线路层py是否一致
"""
import json
import os
import re
import sys

import genClasses as gen


class CheckLDI(object):
    def __init__(self):
        self.silk_screen_layers = job.matrix.returnRows('board', 'silk_screen')
        if 'pnl' not in job.steps:
            DoExit('OK', '没有要检查的pnl.')
        if not self.silk_screen_layers:
            DoExit('OK', '没有要检查的文字层.')

    def do_check(self):
        # err2 py线路不一致  err 不防错
        msg_list, err_text_list, err2_text_list = [], [], []
        step = job.steps.get('pnl')
        step.initStep()
        for silk_screen in self.silk_screen_layers:
            if job.SignalNum > 2:
                signal = f'l{job.SignalNum}' if 'b' in silk_screen else 'l1'
            else:
                signal = f'gbl' if 'b' in silk_screen else 'gtl'
            # 判断线路层的py是否和文字层一致
            tmp_ss = f'{silk_screen}+++{step.pid}'
            step.affect(signal)
            step.selectSymbol('py')
            tmp_signal = f'{signal}+++{step.pid}'
            step.resetFilter()
            if step.Selected_count():
                py_num = step.Selected_count()
                step.copySel(tmp_signal)
                step.unaffectAll()
                # 打散py
                step.affect(tmp_signal)
                step.selectBreak()
                step.unaffectAll()
                step.affect(silk_screen)
                step.refSelectFilter(tmp_signal)
                if step.Selected_count() == py_num:
                    step.copySel(tmp_ss)
                else:
                    Dict = {
                        'job': jobname,
                        'step': step.name,
                        'lay': [silk_screen],
                        'xy': [],
                        'chelist': ''
                    }
                    if Dict not in msg_list:
                        msg_list.append(Dict)
                    err2_text_list.append('Step:%s Layer:%s' % (step.name, silk_screen))
                    step.unaffectAll()
                    step.removeLayer(tmp_signal)
                    continue
                step.unaffectAll()
                step.removeLayer(tmp_signal)
                # 判断py孔是否防错 x镜像 y镜像 180旋转
                # 1.找出中心点
                infoDict = step.DO_INFO(' -t layer -e %s/%s/%s -d LIMITS,units=mm' % (jobname, step.name, tmp_ss))
                xmin = infoDict['gLIMITSxmin']
                ymin = infoDict['gLIMITSymin']
                xmax = infoDict['gLIMITSxmax']
                ymax = infoDict['gLIMITSymax']
                xc = (xmin + xmax) / 2
                yc = (ymin + ymax) / 2
                # 参考层
                tmp_ss_ = f'{tmp_ss}+++'
                step.affect(tmp_ss)
                step.copySel_2(tmp_ss_, x_anchor=xc, y_anchor=yc, mirror='horizontal')
                step.refSelectFilter(tmp_ss_)
                if step.Selected_count() == py_num:
                    Dict = {
                        'job': jobname,
                        'step': step.name,
                        'lay': [silk_screen],
                        'xy': [],
                        'chelist': ''
                    }
                    if Dict not in msg_list:
                        msg_list.append(Dict)
                    err_text_list.append('Step:%s Layer:%s 水平镜像不防错' % (step.name, silk_screen))
                step.truncate(tmp_ss_)
                step.copySel_2(tmp_ss_, x_anchor=xc, y_anchor=yc, mirror='vertical')
                step.refSelectFilter(tmp_ss_)
                if step.Selected_count() == py_num:
                    Dict = {
                        'job': jobname,
                        'step': step.name,
                        'lay': [silk_screen],
                        'xy': [],
                        'chelist': ''
                    }
                    if Dict not in msg_list:
                        msg_list.append(Dict)
                    err_text_list.append('Step:%s Layer:%s 竖直镜像不防错' % (step.name, silk_screen))
                step.truncate(tmp_ss_)
                step.copySel_2(tmp_ss_, x_anchor=xc, y_anchor=yc, rotation=180)
                step.refSelectFilter(tmp_ss_)
                if step.Selected_count() == py_num:
                    Dict = {
                        'job': jobname,
                        'step': step.name,
                        'lay': [silk_screen],
                        'xy': [],
                        'chelist': ''
                    }
                    if Dict not in msg_list:
                        msg_list.append(Dict)
                    err_text_list.append('Step:%s Layer:%s 旋转180°不防错' % (step.name, silk_screen))
                step.unaffectAll()
                step.removeLayer(tmp_ss)
                step.removeLayer(tmp_ss_)
            step.unaffectAll()
        if msg_list:
            mark_text = ''
            if err2_text_list:
                err2_text_list = list(dict.fromkeys(err2_text_list))
                mark_text += '检查到py孔与线路层不一致:\n%s' % '\n'.join(err2_text_list)
            if err_text_list:
                err_text_list = list(dict.fromkeys(err_text_list))
                mark_text += '检查到py孔不防错:\n%s' % '\n'.join(err_text_list)
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
