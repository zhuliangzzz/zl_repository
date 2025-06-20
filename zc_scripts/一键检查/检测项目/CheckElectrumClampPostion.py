#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:CheckElectrumClampPostion.py
   @author:zl
   @time:2024/8/26 17:24
   @software:PyCharm
   @desc:
    检查到电金/电银/电锡板覆盖膜/阻焊电金夹位开窗
"""
import json
import os
import re
import sys

import genClasses as gen


class CheckElectrumClampPostion(object):
    def __init__(self):
        __treatment = jobname[4:6]
        if __treatment not in ('dy', 'dr', 'dx', 'hy', 'hr'):
            DoExit('OK', '不是电金/电银/电锡板.')
        if 'pnl' not in job.steps:
            DoExit('OK', '没有要检查的pnl.')
        self.covs = job.matrix.returnRows('board', 'coverlay')
        self.sms = job.matrix.returnRows('board', 'solder_mask')
        if not self.covs and not self.sms:
            DoExit('OK', '没有要检查的覆盖膜和阻焊层.')

    def do_check(self):
        msg_list, err_text_list = [], []
        step = job.steps.get('pnl')
        step.initStep()
        mask_layer = f'mask+++{step.pid}'
        step.createLayer(mask_layer)
        step.affect(mask_layer)
        step.addRectangle(0, 0, 10, 10)
        step.addRectangle(0, step.profile2.ymax, 10, step.profile2.ymax - 10)
        step.addRectangle(step.profile2.xmax, step.profile2.ymax, step.profile2.xmax - 10, step.profile2.ymax - 10)
        step.addRectangle(step.profile2.xmax, 0, step.profile2.xmax - 10, 10)
        step.unaffectAll()
        step.COM(
                f'copper_area,layer1={mask_layer},layer2=,drills=yes,consider_rout=no,ignore_pth_no_pad=no,drills_source=matrix,thickness=0,resolution_value=25.4,x_boxes=3,y_boxes=3,area=no,dist_map=yes')
        total_area = float(step.COMANS.split()[0])
        # 覆盖膜层
        if self.covs:
            for cov in self.covs:
                tmp_cov = f'{cov}+++{step.pid}'
                step.affect(cov)
                step.selectRectangle(0, 0, 10, 10)
                step.selectRectangle(0, step.profile2.ymax, 10, step.profile2.ymax - 10)
                step.selectRectangle(step.profile2.xmax, step.profile2.ymax, step.profile2.xmax - 10, step.profile2.ymax-10)
                step.selectRectangle(step.profile2.xmax, 0, step.profile2.xmax - 10, 10)
                if step.Selected_count():
                    step.copySel(tmp_cov)
                else:
                    Dict = {
                        'job': jobname,
                        'step': step.name,
                        'lay': [cov],
                        'xy': [],
                        'chelist': ''
                    }
                    if Dict not in msg_list:
                        msg_list.append(Dict)
                    err_text_list.append('Step:%s Layer:%s' % (step.name, cov))
                    step.unaffectAll()
                    continue
                step.unaffectAll()
                step.COM(f'copper_area,layer1={tmp_cov},layer2=,drills=yes,consider_rout=no,ignore_pth_no_pad=no,drills_source=matrix,thickness=0,resolution_value=25.4,x_boxes=3,y_boxes=3,area=no,dist_map=yes')
                area = float(step.COMANS.split()[0])
                percent = area / total_area
                if percent < 0.6:
                    Dict = {
                        'job': jobname,
                        'step': step.name,
                        'lay': [cov],
                        'xy': [],
                        'chelist': ''
                    }
                    if Dict not in msg_list:
                        msg_list.append(Dict)
                    err_text_list.append('Step:%s Layer:%s' % (step.name, cov))
                step.removeLayer(tmp_cov)
        # 阻焊层
        if self.sms:
            for sm in self.sms:
                tmp_sm = f'{sm}+++{step.pid}'
                step.affect(mask_layer)
                step.refSelectFilter(sm, mode='cover')
                if step.Selected_count() == 4:
                    step.unaffectAll()
                    continue
                step.unaffectAll()
                step.affect(sm)
                step.selectRectangle(0, 0, 10, 10)
                step.selectRectangle(0, step.profile2.ymax, 10, step.profile2.ymax - 10)
                step.selectRectangle(step.profile2.xmax, step.profile2.ymax, step.profile2.xmax - 10,
                                         step.profile2.ymax - 10)
                step.selectRectangle(step.profile2.xmax, 0, step.profile2.xmax - 10, 10)
                if step.Selected_count():
                    step.copySel(tmp_sm)
                else:
                    Dict = {
                        'job': jobname,
                        'step': step.name,
                        'lay': [sm],
                        'xy': [],
                        'chelist': ''
                    }
                    if Dict not in msg_list:
                        msg_list.append(Dict)
                    err_text_list.append('Step:%s Layer:%s' % (step.name, sm))
                    step.unaffectAll()
                    continue
                step.unaffectAll()
                step.COM(
                    f'copper_area,layer1={tmp_sm},layer2=,drills=yes,consider_rout=no,ignore_pth_no_pad=no,drills_source=matrix,thickness=0,resolution_value=25.4,x_boxes=3,y_boxes=3,area=no,dist_map=yes')
                area = float(step.COMANS.split()[0])
                percent = area / total_area
                if percent < 0.6:
                    Dict = {
                        'job': jobname,
                        'step': step.name,
                        'lay': [sm],
                        'xy': [],
                        'chelist': ''
                    }
                    if Dict not in msg_list:
                            msg_list.append(Dict)
                    err_text_list.append('Step:%s Layer:%s' % (step.name, sm))
                step.removeLayer(tmp_sm)
        step.removeLayer(mask_layer)
        if msg_list:
            if err_text_list:
                mark_text = '未检查到电金夹位开窗:\n%s' % '\n'.join(err_text_list)
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
    check_ecp = CheckElectrumClampPostion()
    check_ecp.do_check()
