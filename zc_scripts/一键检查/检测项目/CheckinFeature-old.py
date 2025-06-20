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
        self.check_steps = list(filter(lambda x: 'set' in x or 'pnl' == x,job.steps))
        if not self.check_steps:
            DoExit('OK', '没有要检查的pnl和set')

    def do_check(self):
        msg_list, err_text_list = [], []
        counts = 0
        use_layer = job.matrix.returnRows('board', 'signal|silk_screen|solder_mask|drill')
        if not use_layer:
            DoExit('OK', '没有要检查的层')
        for step in self.check_steps:
            mystep = job.steps.get(step)
            mystep.initStep()
            mystep.VOF()
            mystep.truncate("check02+++")
            mystep.createLayer("check02+++")
            mystep.createLayer("check02_015+++")
            mystep.VON()
            # 铺铜
            if not re.search('set|panel|pnl', step):
                mystep.srFill('check02+++', 'positive', 0.3, 0.3, nest_sr='no')
                mystep.srFill('check02_015+++', 'positive', -0.15, -0.15, nest_sr='no')
                continue

            mystep.Flatten('check02+++', 'check03+++')
            mystep.Flatten('check02_015+++', 'check03_015+++')
            # 选层 touch板内-0.15 选线路层
            for layer in job.matrix.returnRows('board', 'signal|power_ground'):
               mystep.affect(layer)
            mystep.resetFilter()
            mystep.setFilterTypes(polarity='positive')
            # mystep.setAdv_srfarea(0, 200)
            mystep.refSelectFilter('check03_015+++')
            mystep.resetFilter()
            # 再选层
            for layer in use_layer:
                mystep.affect(layer)
            mystep.resetFilter()
            # mystep.setAdv_srfarea(0, 200)
            # touch板外0.3
            mystep.refSelectFilter('check03+++')
            mystep.resetFilter()
            if re.search(r'(panel|pnl)', step):
                mystep.resetFilter()
                mystep.setFilterTypes('text')
                mystep.setAdv_strlen(2, 2)
                mystep.selectAll('unselect')
                mystep.resetFilter()
                # 去掉动态序号
                mystep.setSymbolFilter('text+*')
                mystep.selectAll('unselect')
                mystep.resetFilter()
            count = mystep.Selected_count()
            if count:
                counts += count
                for layer in use_layer:
                    num = 0
                    readlines = mystep.INFO('-t layer -e %s/%s/%s -m script -d FEATURES -o feat_index+select,units=mm' % (jobname, step, layer))
                    del readlines[0]
                    for line in readlines:
                        row = line.split(' ')[0]
                        id = row.split('#')[1] if len(row.split('#')) > 1 else ''
                        if id:
                            Dict = {
                                'job': jobname,
                                'step': step,
                                'lay': [layer],
                                'xy': [id],
                                'chelist': ''
                            }
                            if Dict not in msg_list:
                                msg_list.append(Dict)
                            num += 1
                    if readlines:
                        err_text_list.append('Step:%s Layer:%s,有%s处' % (step, layer, num))
            else:
                err_text_list.append('Step:%s,检查正常' % step)
            if step.startswith('set'):
                mystep.srFill('check02+++', 'positive', 1.1, 1.1)
            mystep.unaffectAll()
        if msg_list:
            mark_text = '检测到板内有异物:共%s处\n%s' % (counts,'\n'.join(err_text_list))
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
    checkMisssold = CheckinFeature()
    checkMisssold.do_check()
