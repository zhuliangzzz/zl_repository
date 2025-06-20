#!/usr/bin/env python
# -*-coding: Utf-8 -*-
# @File : readback_compare
# @author: tiger
# @Time：2024/9/27
# @version: v1.0
# @note:


import os
import string
import sys
import re
if sys.platform == "win32":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package_HDI")
    sys.path.append(r"D:/pyproject/Package")
else:
    scriptPath = "%s/scripts" % os.environ.get('SCRIPTS_DIR', '/incam/server/site_data')
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")

import gClasses
import gFeatures
import shutil
import getpass

from create_ui_model import showMessageInfo, showQuestionMessageInfo
from mwClass_V2 import AboutDialog

try:
    new_job, drl_filename, drl_name, jobname, step_name, scale_x, scale_y, mirr, anchor_x, anchor_y, ccd_mode = sys.argv[1:]
    print ccd_mode

except Exception as e:
    # new_job, drl_filename, drl_name, jobname, step_name, scale_x, scale_y, mirr, anchor_x, anchor_y = ['p11-b68506ph374c2-ynh', 'p11-b68506ph374c2-ynh.drl', 'drl', 'b68506ph374c2-ynh', 'panel', '1.00035', '1.00047',
    #  'no', '310.134', '345.694']
    print e
    sys.exit(0)


def send_message_to_director(message_result, job_name, label_result):
    """发送审批结果界面 20221122 by lyh"""
    submitData = {
        'site': u'HDI板事业部',
        'job_name': job_name,
        'pass_tpye': 'CAM',
        'pass_level': 8,
        'assign_approve': '43982|44566|44024|84310|83288|68027|91259',
        'pass_title': message_result,
    }
    Dialog = AboutDialog(label_result, cancel=True, appCheck=True, appData=submitData, style=None)
    Dialog.exec_()

    # --根据审批的结果返回值
    if Dialog.selBut in ['x', 'cancel']:
        return False
    if Dialog.selBut == 'ok':
        return True

    return False


def check_text_file(file_path):
    with open(file_path, 'r') as f:
        read_lines = f.readlines()
    split_index = read_lines.index('%\n')
    head_t = {}
    # T01C0.46S...
    erros = []
    for i, line in enumerate(read_lines):
        if i < split_index:
            if re.search('^T\d+C.*', line):
                t_index,t_size = line.strip().split('C')
                if re.search(r'\d+.?\d+?S.*', t_size):
                    t_size = t_size.split('S')[0]
                head_t[t_index] = t_size
        else:
            # 0.460S110.F1.5U12.Z-0.15H1800

            if line.strip() in head_t.keys():
                text_t = line.strip()
            if re.search('^M97,.*|^M98,.*', line):
                if abs(float(head_t[text_t]) - 0.46) >= 0.01:
                    erros.append(u"型号孔批号孔大小错误，请确认批号孔是否排在最后一把刀")
    return erros

def del_8888_text_and_write_scale_text(file_path):
    with open(file_path, 'r') as f:
        all_lines = f.readlines()

    del_index = []
    for i, line in enumerate(all_lines):
        if re.search('M97,8{5,}|M98,8{5,}', line):
            del_index.append(i)
            del_index.append(i + 1)
    
    if del_index:
        write_lines = [line for i, line in enumerate(all_lines) if i not in del_index]
        with open(file_path, 'w') as f:
            f.write(''.join(write_lines))

    # 因机器不识别备注，取消掉添加的备注
    # if float(scale_x) != 1 or float(scale_y) != 1:
    #     write_scale_text = '/User:{0} Scale:X={1} Y={2}'.format(user_name, scale_x, scale_y) + '\n'
    #     write_lines.append(write_scale_text)


# M47,\P:M16,M2
# M47,\P:M01,D2.075,I0,T'CIRCLE'
def re_write_ccdfile(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    split_index = lines.index('%\n')
    head_t = []
    for i, line in enumerate(lines):
        if i < split_index:
            rgx = '^T(\d+)C.*'
            res = re.match(rgx, line)
            if res:
                get_size = int(res.groups()[0])
                if get_size < 100:
                    head_t.append(int(res.groups()[0]))
        if i == split_index + 2:
            max_t = max(head_t) + 1
            if re.search('^M47.*,D\d+.*', line):
                ccd_size = line.split(',')[2].replace('D','')
                ccd_t = 'T{0}'.format(str(max_t).rjust(2, '0'))
                ccd_head = '{0}C{1}'.format(ccd_t, ccd_size) + '\n'
                lines[split_index] = ccd_head + lines[split_index] + ccd_t + '\n'
                break
    with open(file_path, 'w') as f:
        f.write(''.join(lines))


if __name__ == "__main__":
    job = gClasses.Job(jobname)
    step = gClasses.Step(job, step_name)
    if sys.platform == "win32":
        user_name = getpass.getuser()
        filepath = 'D:/disk/film/{0}/{1}'.format(new_job, drl_filename)
        tmp_path = 'C:/tmp'
    else:
        filepath = '/id/workfile/hdi_film/{0}/{1}'.format(new_job, drl_filename)
        tmp_path = '/tmp'
        user_name = gClasses.Top().getUser()

    #  检测文件中批号孔字麦大小是否正确
    if not re.search('lp|dq|sk', drl_name):
        res = check_text_file(filepath)
        if res:
            showMessageInfo(u"{0}型号孔批号孔大小错误，请确认批号孔是否排在最后一把刀".format(drl_name))
            sys.exit(1)

    # 回读比对前如果文件中有8888字样先删除
    del_8888_text_and_write_scale_text(filepath)

    os.environ["JOB"] = jobname
    from genesisPackages import compareLayersForOutput, get_sr_limits, get_profile_center

    compare_output = compareLayersForOutput()
    step.PAUSE('test')
    if os.path.isfile(filepath):
        # 20250320 zl 判断参数是否正确
        if re.search('^drl$|^b((\d+)(-)(\d+))$|^m((\d+)(-)(\d+))$|^dbk(\S+)$|^dbk$|^(2|3)nd$|^lr((\d+)(-)(\d+))$', drl_name):
            # file_contents = None
            with open(filepath) as f:
                file_contents = f.read()
            if file_contents:
                parms = re.findall('T\d+C\d+\.?\d*([a-zA-Z].*)?\n', file_contents)
                if any([len(parm.strip()) == 0 for parm in parms]):
                    showMessageInfo(u"{0}层钻带参数异常,输出文件将被删除，具体请查看钻带文件参数".format(drl_name))
                    os.remove(filepath)
                    sys.exit(1)
        if ccd_mode and ccd_mode in ['ccd', 'mark']:
            if not os.path.isdir(tmp_path):
                os.mkdir(tmp_path)
            shutil.copy(filepath, tmp_path)
            filepath = os.path.join(tmp_path, drl_filename)
            # ccd钻和mark钻需要更改文本后再回读，创建临时文件
            re_write_ccdfile(filepath)

        compare_output.input_drill_file(job.name, step.name,filepath, drl_name)
        # 回读完后删除tmp下面的临时文件
        tmp_file = os.path.join(tmp_path, drl_filename)
        if os.path.isfile(tmp_file):
            os.unlink(tmp_file)
        # 删除批号孔
        step.clearAll()
        step.resetFilter()
        # 用角线来确定sr区域角线有两类 sh-con,sh-con2
        con_lines = []
        if step.isLayer('l1'):
            con_info = step.INFO("-t layer -e %s/%s/%s  -d FEATURES" % (jobname, step_name, 'l1'))
            con_lines = [gFeatures.Pad(line) for line in con_info if 'sh-con2' in line or 'sh-con' in line]
        if not con_lines:
            if step.isLayer('l2'):
                con_info = step.INFO("-t layer -e %s/%s/%s  -d FEATURES" % (jobname, step_name, 'l2'))
                con_lines = [gFeatures.Pad(line) for line in con_info if 'sh-con2' in line or 'sh-con' in line]
        if con_lines:
            con_feax = [fea.x * 25.4 for fea in con_lines]
            con_feay = [fea.y * 25.4 for fea in con_lines]
            sr_xmin, sr_ymin, sr_xmax, sr_ymax = min(con_feax) + 1, min(con_feay) + 1, max(con_feax) - 1, max(con_feay) - 1
        else:
            sr_xmin, sr_ymin, sr_xmax, sr_ymax = get_sr_limits(step)
        xcent, ycent = get_profile_center(step_name)

        # 获取钻字坐标
        info = step.INFO("-t layer -e %s/%s/%s -m script -d FEATURES, units=mm" % (jobname, step_name, drl_name))
        for line in info:
            if 'zuanzi' in line or "JOB" in line:
                ss = string.split(line)
                x = string.atof(ss[1])
                y = string.atof(ss[2])
                rotation = string.atof(ss[5])
                if rotation == 0:
                    if y < ycent:
                        x1, y1 = x-10,  y-10
                        x2, y2 = x+200, y + 5
                    else:
                        x1, y1 = x - 10,  y - 1
                        x2, y2 = x + 200, y + 20
                else:
                    if x < xcent:
                        x1, y1 = x - 10,  y - 10
                        x2, y2 = x + 1,  y + 200
                    else:
                        x1, y1 = x - 5,  y - 10
                        x2, y2 = x + 10, y + 200
                step.clearAll()
                step.affect(drl_name)
                step.filter_set(feat_types='text')
                step.COM("filter_area_strt")
                step.COM("filter_area_xy,x=%s,y=%s" % (x1, y1))
                step.COM("filter_area_xy,x=%s,y=%s" % (x2, y2))
                step.COM("filter_area_end,layer=,filter_name=popup,operation=select,area_type=rectangle,inside_area=yes,intersect_area=no")

                # step.COM("sel_single_feat,operation=select,x=%s,y=%s,tol=500,cyclic=no" % (x, y))

                # step.PAUSE(str([x1,y1]))
                if step.featureSelected():
                    limit = step.DO_INFO("-t layer -e %s/%s/%s -d LIMITS  -o select,units=mm" % (jobname, step_name, drl_name))

                    step.clearAll()
                    step.affect(drl_name + '_compare')
                    step.resetFilter()
                    step.filter_set(include_syms='r508\;r460')
                    step.COM("filter_area_strt")
                    step.COM("filter_area_xy,x=%s,y=%s" % (float(limit['gLIMITSxmin'])-0.5, float(limit['gLIMITSymin'])-0.5))
                    step.COM("filter_area_xy,x=%s,y=%s" % (float(limit['gLIMITSxmax'])+0.5, float(limit['gLIMITSymax'])+0.5))
                    step.COM("filter_area_end,layer=,filter_name=popup,operation=select,area_type=rectangle,inside_area=yes,intersect_area=no")
                    if step.featureSelected():
                        step.selectDelete()

        step.resetFilter()
        step.clearAll()
        if "inn" not in drl_name:
            if ccd_mode and ccd_mode in ['ccd', 'mark']:
                step.affect(drl_name + '_compare')
                ccd_layer = drl_name + '.' + ccd_mode
                flt_ccd = ccd_layer + '__flt+'
                step.flatten_layer(ccd_layer, flt_ccd)
                step.refSelectFilter(flt_ccd)
                if step.featureSelected():
                    step.selectDelete()
                step.removeLayer(flt_ccd)

        step.resetFilter()
        step.clearAll()
        if 'ynh' in jobname:
            step.PAUSE(drl_name)
        diff_cout, diff_info, compare_status = compare_output.compare_layer(job.name, step.name, drl_name,
                                                                            "no", float(scale_x), float(scale_y),
                                                                            filepath, "drill", float(anchor_x),
                                                                      float(anchor_y), "layer_compare")

        if diff_info or diff_cout:
            if diff_info == 'in_pcs':
                showMessageInfo(u"{0}层钻带回读比对异常,输出文件将被删除，具体请查看层：r0_tmp".format(drl_name))
                os.remove(filepath)
                sys.exit(1)
            resurt = showQuestionMessageInfo(u"{0}层钻带回读比对与原钻带不一致，具体请查看层: r0_tmp！请确实是否继续输出？".format(drl_name))
            if resurt:
                # 继续输出发起评审
                log = u"{0}层钻带回读比对与原钻带不一致".format(drl_name)
                res = send_message_to_director(log, jobname, log)
                if not res:
                    os.remove(filepath)
                    sys.exit(1)
                else:
                    sys.exit(0)
        else:
            sys.exit(0)
    else:
        sys.exit(0)

