#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__  = "luthersy"
__date__ = "20240408"
__version__ = "Revision: 1.0.0 "
__credits__ = u"""合并镭射层 """

import sys
import os
if sys.platform == "win32":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package_HDI")    
else:
    scriptPath = "%s/scripts" % os.environ.get('SCRIPTS_DIR', '/incam/server/site_data')
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")
    
dest_merge_layer = sys.argv[1]
merge_layers = set(sys.argv[2:])

from genesisPackages import job, get_panelset_sr_step

import gClasses

stepname = "panel"
step = gClasses.Step(job, stepname)
step.open()
step.COM("units,type=mm")

all_steps = get_panelset_sr_step(job.name, stepname)

step.removeLayer(dest_merge_layer)

dic_symbols = {}
dic_resizes = {}
for layer in merge_layers:
    step.flatten_layer(layer, layer+"_flt")
    step.clearAll()
    step.resetFilter()
    step.affect(layer+"_flt")
    step.refSelectFilter(layer)
    if step.featureSelected():
        step.selectDelete()
    
    layer_cmd = gClasses.Layer(step, layer+"_flt")
    feat_out = layer_cmd.featCurrent_LayerOut(units="mm")["pads"]
    feat_out += layer_cmd.featCurrent_LayerOut(units="mm")["lines"]
    
    symbols = list(set([obj.symbol for obj in feat_out]))
    dic_symbols[layer] = symbols
    
    dic_resizes[layer] = abs(int(layer.split("-")[1]) - int(layer.split("-")[0][1:])) - 1
    step.removeLayer(layer+"_flt")

for stepname in all_steps + ["panel"]:
    step = gClasses.Step(job, stepname)
    step.open()
    step.COM("units,type=mm")
    
    for i, layer in enumerate(sorted(merge_layers, key=lambda x: dic_resizes[x])):
        resize = 0
        resize_symbols = []
        for key, values in dic_symbols.iteritems():
            if key == layer:
                continue
            
            for symbol in dic_symbols[layer]:
                if symbol in values:
                    resize = dic_resizes[layer]
                    resize_symbols.append(symbol)
                    break
                
        step.clearAll()
        step.affect(layer)
        step.resetFilter()
        
        if stepname != "panel":
            if not resize_symbols:
                step.copyToLayer(dest_merge_layer, size=0)            
            else:
                # 有相同孔径合并时才加1um
                step.selectSymbol(";".join(resize_symbols), 1, 1)
                if step.featureSelected():
                    step.copyToLayer(dest_merge_layer, size=resize)
                
                step.resetFilter()
                step.filter_set(exclude_syms=";".join(resize_symbols))
                step.selectAll()
                if step.featureSelected():
                    step.copyToLayer(dest_merge_layer, size=0)    
        
        else:
            if i == 0:        
                step.clearAll()
                step.affect(layer)
                step.copySel(dest_merge_layer)
            else:
                step.resetFilter()
                step.filter_set(exclude_syms="r501\;r520\;r3175")
                step.selectAll()
                if step.featureSelected():
                    step.copySel(dest_merge_layer)
            
        step.clearAll()

stepname = "panel"
step = gClasses.Step(job, stepname)
step.open()

step.clearAll()
step.resetFilter()
for layer in merge_layers:
    step.affect(layer)

step.selectSymbol("r520", 1, 1)
if step.featureSelected():
    step.clearAll()
    step.affect(dest_merge_layer)
    step.selectSymbol("r520", 1, 1)
    if not step.featureSelected():
        
        for i, layer in enumerate(sorted(merge_layers, key=lambda x: dic_resizes[x])):
            step.clearAll()
            step.affect(layer)
            step.resetFilter()
            step.selectSymbol("r520", 1, 1)
            if step.featureSelected():
                step.copySel(dest_merge_layer)
                break
            
step.clearAll()
step.COM("matrix_layer_type,job={0},matrix=matrix,layer={1},type=drill".format(job.name, dest_merge_layer))
    
    
