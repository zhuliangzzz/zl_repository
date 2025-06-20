#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:CheckPnlSizeAndPcsNum.py
   @author:zl
   @time:2024/06/29 11:28
   @software:PyCharm
   @desc:
   检查pnl中的尺寸和pcs数量的文字是否正确
"""
import json
import os
import re
import sys

import genClasses as gen


class CheckPnlSizeAndPcsNum(object):
    def __init__(self):
        if 'pnl' not in job.steps:
            DoExit('OK', '没有要检查的pnl')
        self.step = job.steps.get('pnl')
        # 要检查的外层阻焊外层覆盖膜层
        self.layers = job.matrix.returnRows('board', 'signal|silk_screen')
        for row in job.matrix.returnRows('board', 'solder_mask'):
            if re.match('dk(t|b)$', row):
                self.layers.append(row)
        job.matrix.returnRows()
        if not self.layers:
            DoExit('OK', '没有要检查的线路和文字层')

    def do_check(self):
        msg_list, err_text_list = [], []
        size_err_lays, pcs_err_lays = [], []
        # 尺寸
        xsize, ysize = self.step.profile2.xsize, self.step.profile2.ysize
        # pcs数量
        pcs_num = get_pcs_num(self.step)
        self.step.initStep()
        for layer in self.layers:
            self.step.affect(layer)
            self.step.setFilterTypes('text')
            self.step.setTextFilter('*pcs/pnl*')
            self.step.selectAll()
            self.step.resetFilter()
            if self.step.Selected_count():
                lines = self.step.INFO(
                    '-t layer -e %s/%s/%s -d features -o select,units=mm' % (jobname, self.step.name, layer))
                del lines[0]
                text = lines[0].split("'")[1]
                result = re.search('(.*)\*(.*)=(\d+)PCS/PNL', text)
                size_x, size_y, pcs_n = result.group(1), result.group(2), result.group(3)
                if size_x != str(xsize) or size_y != str(ysize):
                    Dict = {
                        'job': jobname,
                        'step': self.step.name,
                        'lay': [layer],
                        'xy': [],
                        'chelist': ''
                    }
                    if Dict not in msg_list:
                        msg_list.append(Dict)
                    size_err_lays.append('Step:%s Layer:%s' % (self.step.name, layer))
                if pcs_n != str(pcs_num):
                    Dict = {
                        'job': jobname,
                        'step': self.step.name,
                        'lay': [layer],
                        'xy': [],
                        'chelist': ''
                    }
                    if Dict not in msg_list:
                        msg_list.append(Dict)
                    pcs_err_lays.append('Step:%s Layer:%s' % (self.step.name, layer))
            self.step.unaffectAll()
        mark_text = ''
        if msg_list:
            mark_text += '实际尺寸：%sx%s pcs数量：%s\n' % (xsize, ysize, pcs_num)
            if size_err_lays:
                mark_text += '检测到尺寸有误:\n%s\n' % '\n'.join(size_err_lays)
            if pcs_err_lays:
                mark_text += '检测到pcs数量有误:\n%s\n' % '\n'.join(pcs_err_lays)
        if mark_text:
            DoExit('NG', msg=msg_list, mark=mark_text)
        else:
            DoExit('OK', '恭喜，该项检查通过.')



def get_pcs_num(step):
    steps = step.info.get('gREPEATstep')  # 获取set列表
    pcs_num_map = {}
    pcs_name = set()
    for s in steps:
        if 'set' in s:
            pcs_list = list(filter(lambda repeat_: str(repeat_).startswith('pcs'), job.steps.get(s).info.get('gREPEATstep')))
            pcs_name.update(pcs_list)  # 获取每个set中的pcs列表
            if s not in pcs_num_map:
                pcs_num_map[s] = 0
            pcs_num_map[s] += len(pcs_list)
    if len(pcs_name) > 1:
        return min(pcs_num_map.values())
    else:
        return sum(pcs_num_map.values())


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
    checkPnlSizeAndPcsNum = CheckPnlSizeAndPcsNum()
    checkPnlSizeAndPcsNum.do_check()
