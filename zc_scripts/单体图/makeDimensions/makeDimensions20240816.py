#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:makeDimensions.py
   @author:zl
   @time:2024/8/15 16:40
   @software:PyCharm
   @desc:
"""
import math
import os
import genClasses as gen


def make(lay):
    step.initStep()
    # 获取层中心 参考与中心的相对位置来设置标注点的位置
    infoDict = step.DO_INFO(' -t layer -e %s/%s/%s -d LIMITS,units=mm' % (jobname, step.name, lay))
    xmin = infoDict['gLIMITSxmin']
    ymin = infoDict['gLIMITSymin']
    xmax = infoDict['gLIMITSxmax']
    ymax = infoDict['gLIMITSymax']
    cx = (xmin + xmax) / 2
    cy = (ymin + ymax) / 2
    features = step.INFO(' -t layer -e %s/%s/%s -d FEATURES,units=mm' % (jobname, step.name, lay))
    del features[0]
    lines = {'h': [], 'v': []}
    cirs = []
    for feature in features:
        type_ = feature.split()[0]
        if type_ == '#L':
            (x1, y1, x2, y2) = [float(i) for i in feature.split()[1: 5]]
            if x1 == x2:
                leng = round(abs(y1 - y2), 2)
                if leng > 8:
                    lines['v'].append((x1, y1, x2, y2, leng))
            if y1 == y2:
                leng = round(abs(x1 - x2), 2)
                if leng >8:
                    lines['h'].append((x1, y1, x2, y2, leng))
        elif type_ == '#A':
            (x1, y1, x2, y2, xc, yc) = [float(i) for i in feature.split()[1: 7]]
            if x1 == x2 and y1 == y2:  # 起点终点相同，则为circle
                # 半径
                r = float('%.2f' % math.sqrt(abs(x1 - xc) ** 2 + abs(y1 - yc) ** 2))
                cirs.append((x1, y1, r))
    print(cx, cy)
    print(lines)
    print(cirs)
    step.display(lay)
    step.COM(f'dimens_delete_drawing,lyr_name={lay}')
    step.COM(f'dimens_set_params,lyr_name={lay},post_decimal_dist=-1,post_decimal_pos=-1,post_decimal_angle=-1,line_width=0.2,font=standard,text_width=2,text_height=2,top_margin=19.05,bottom_margin=12.7,left_margin=19.05,right_margin=12.7,ext_overlen=1016,center_marker_len=1270,baseline_spacing=304.8,feature_color=0,dimens_color=0,dimens_text_color=0,profile_color=0,template_color=0,paren_loc_text=yes')
    st = sl = 1.5
    if lines.get('h'):
        for line in lines['h']:
            x1, y1, x2, y2, value = line[0], line[1], line[2], line[3], line[4]
            line_y = y1 + st if y1 > cy else y1 - st
            step.COM(f'dimens_add,type=horiz,x1={x1},y1={y1},x2={x2},y2={y2},x3=0,y3=0,line_x={(x1 + x2) / 2},line_y={line_y},offset=0.01,prefix=,value={value},tol_up=,tol_down=,suffix=,note=,units=mm,view_units=yes,underline=no,merge_tol=no,to_arc_center=no,two_sided_diam=no,magnify=1,vert_dimens_text_orientation=right')
    if lines.get('v'):
        for line in lines['v']:
            x1, y1, x2, y2, value = line[0], line[1], line[2], line[3], line[4]
            line_x = x1 + sl if x1 > cx else x1 - sl
            step.COM(f'dimens_add,type=vert,x1={x1},y1={y1},x2={x2},y2={y2},x3=0,y3=0,line_x={line_x},line_y={(y1 + y2)/2},offset=0.02,prefix=,value={value},tol_up=,tol_down=,suffix=,note=,units=mm,view_units=yes,underline=no,merge_tol=no,to_arc_center=no,two_sided_diam=no,magnify=1,vert_dimens_text_orientation=right')


if __name__ == '__main__':
    jobname = os.environ.get('JOB')
    job = gen.Job(jobname)
    step = job.steps.get('pcs')
    l = 'gko'
    make(l)
