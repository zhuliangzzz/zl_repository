#!/usr/bin/env python
# -*-coding: Utf-8 -*-
# @File : check_183_attr_smd
# @author: tiger
# @Time：2024/10/1 
# @version: v1.0
# @note: 

import platform,sys
import os
reload(sys)
sys.setdefaultencoding('utf8')
if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

import gClasses
try:
    jobname, stepname  = sys.argv[1:]
    get_do = 'set_attr'
    os.environ["JOB"] = jobname
    os.environ["STEP"] = stepname
except:
    jobname = os.environ.get("JOB")
    try:
        stepname = sys.argv[1]
    except:
        stepname = os.environ.get("STEP")
    get_do = 'check_attr'


job = gClasses.Job(jobname)
step = gClasses.Step(job, stepname)

from genesisPackages import outsignalLayers, tongkongDrillLayer, solderMaskLayers
from create_ui_model import showMessageInfo
class Main:

    def __init__(self):
        self.clip_opensm_layers()

    def clip_opensm_layers(self):
        """
        检查是否漏定SMD属性，阻焊和钢网层结合
        """
        step.open()
        step.clearAll()
        step.resetFilter()
        step.COM("units,type=inch")
        tmp_drill = 'drl_pad_attr'
        step.removeLayer(tmp_drill)
        step.createLayer(tmp_drill)
        for drl in tongkongDrillLayer:
            # tmp层只挑出槽孔和大孔0.4以上
            info = step.DO_INFO("-t layer -e %s/%s/%s -d TOOL -p drill_size" % (jobname, step.name, drl))['gTOOLdrill_size']
            drl_size = list(set(['r{0}'.format(s) for s in info if float(s) > 400/25.4 ]))
            step.clearAll()
            step.affect(drl)
            step.filter_set(feat_types='line')
            step.selectAll()
            if step.featureSelected():
                step.copyToLayer(tmp_drill)
            step.resetFilter()
            step.filter_set(include_syms='oval*')
            step.selectAll()
            if step.featureSelected():
                step.copyToLayer(tmp_drill)
            step.resetFilter()
            if drl_size:
                step.filter_set(include_syms='\\;'.join(drl_size))
                step.selectAll()
                if step.featureSelected():
                    step.copyToLayer(tmp_drill)
        step.resetFilter()
        step.clearAll()

        for layer in outsignalLayers:
            if layer == 'l1':
                smlayer = 'm1'
                if step.isLayer('p1'):
                    pstlayer = 'p1'
                else:continue
            else:
                smlayer = 'm2'
                if step.isLayer('p2'):
                    pstlayer = 'p2'
                else:continue
            tmp_smlayer = smlayer + '_openpad'
            tmp_smdlayer = layer + '_pad_attr'
            tmp_smopenlayer = 'opensm_pad_attr'
            more_attr = layer + '_pad_attr_more'
            less_attr = layer + '_pad_attr_less'
            step.removeLayer(more_attr)
            step.removeLayer(less_attr)
            step.removeLayer(tmp_smdlayer)
            step.createLayer(tmp_smdlayer)
            step.removeLayer(tmp_smlayer)
            step.createLayer(tmp_smlayer)
            step.removeLayer(tmp_smopenlayer)
            step.createLayer(tmp_smopenlayer)
            step.copyLayer(jobname, stepname, pstlayer, tmp_smopenlayer)
            step.clearAll()

            # 阻焊层开窗加入检查
            step.copyLayer(jobname, stepname, smlayer, tmp_smlayer)
            step.affect(tmp_smlayer)
            step.filter_set(feat_types='line;arc;text;surface')
            step.selectAll()
            if step.featureSelected():
                step.selectDelete()
            step.resetFilter()
            step.filter_set(polarity='negative')
            step.selectAll()
            if step.featureSelected():
                step.selectDelete()
            step.resetFilter()
            step.refSelectFilter(pstlayer)
            if step.featureSelected():
                step.selectDelete()
            step.resetFilter()
            step.refSelectFilter(layer, mode='disjoint')
            if step.featureSelected():
                step.selectDelete()
            # 去除大孔对应的PAD
            step.refSelectFilter(tmp_drill)
            if step.featureSelected():
                step.selectDelete()

            step.copyToLayer(tmp_smopenlayer)
            step.clearAll()


            step.affect(tmp_smopenlayer)
            # 去除大孔对应的PAD
            step.refSelectFilter(tmp_drill)
            if step.featureSelected():
                step.selectDelete()
           
            step.clearAll()


            step.resetFilter()
            step.affect(layer)
            for atr in ['.smd', '.bga']:
                step.resetFilter()
                step.filter_set(feat_types='pad')
                step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute={0}".format(atr))
                step.selectAll()
                if step.featureSelected():
                    step.copySel(tmp_smdlayer)

            # 找出漏定义的SMD
            step.clearAll()
            step.resetFilter()
            step.affect(tmp_smopenlayer)
            step.refSelectFilter(tmp_smdlayer, mode='cover')
            step.refSelectFilter(tmp_smdlayer, mode='include')
            # step.refSelectFilter(tmp_smdlayer, mode='disjoint')
            step.COM("sel_reverse")

            if step.featureSelected():
                step.copySel(less_attr)

            # step.clearAll()
            # step.resetFilter()
            # pad_out = 'tmp_include_pad'
            # step.removeLayer(pad_out)
            # # 线路层PAD包含锡膏层的再找出来
            # step.affect(layer)
            # step.filter_set(feat_types='pad', polarity='positive')
            # step.refSelectFilter(tmp_smopenlayer, mode='include')
            # if step.featureSelected():
            #     step.copyToLayer(pad_out)
            #     step.clearAll()
            #     step.resetFilter()
            #     step.affect(pad_out)
            #     for atr in ['.smd', '.bga']:
            #         step.resetFilter()
            #         step.filter_set(feat_types='pad')
            #         step.COM("filter_atr_set,filter_name=popup,condition=yes,attribute={0}".format(atr))
            #         step.selectAll()
            #         if step.featureSelected():
            #             step.selectDelete()
            #     step.resetFilter()
            #     step.selectAll()
            #     if step.featureSelected():
            #         step.copyToLayer(less_attr)
            # step.removeLayer(pad_out)


            if get_do == 'check_attr':
                if step.isLayer(less_attr):
                    self.check_layers_attr(layer,less_attr)
                else:
                    pass
            elif get_do == 'set_attr':
                # 和p1层比较,先把多定的SMD找出来
                step.clearAll()
                step.resetFilter()
                step.affect(tmp_smdlayer)
                step.refSelectFilter(tmp_smopenlayer, mode='cover')
                step.refSelectFilter(tmp_smopenlayer, mode='include')
                # step.refSelectFilter(tmp_smopenlayer, mode='disjoint')
                step.COM("sel_reverse")
                if step.featureSelected():
                    step.moveSel(more_attr)
                    # 再找出线路层中多定义的去除属性
                    step.clearAll()
                    step.affect(layer)
                    step.filter_set(feat_types='pad', polarity='positive')
                    step.refSelectFilter(more_attr, mode='cover')
                    # step.PAUSE("11")
                    if step.featureSelected():
                        step.COM("sel_delete_atr,attributes=.smd\;.bga")
                    # 对应线路层找到PAD直接定义
                    if step.isLayer(less_attr):
                        step.affect(layer)
                        step.filter_set(feat_types='pad', polarity='positive')
                        step.refSelectFilter(less_attr, mode='include')
                        if step.featureSelected():
                            step.COM("cur_atr_set,attribute=.smd")
                            step.COM("sel_change_atr,mode=add")

                step.clearAll()
                step.resetFilter()
                step.removeLayer(tmp_smdlayer)
                step.removeLayer(tmp_smopenlayer)
                step.removeLayer(more_attr)
                step.removeLayer(less_attr)
        step.removeLayer(tmp_drill)
        showMessageInfo(u"程序已运行完成！")

    def check_layers_attr(self, layer, less_attr):
        step.clearAll()
        step.display_layer(lay=layer, num=1)
        step.display_layer(lay=less_attr, num=2)
        step.PAUSE(u"{0}层部分PAD漏定义SMD属性，请确认".format(layer))


if __name__ == "__main__":
    print get_do
    Main()