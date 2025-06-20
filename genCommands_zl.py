#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Modules for joining Genesis 2000 scripting and the Python scripting language.

NEED: genClasses.py and genFeatures.py

THIS MODULE *REQUIRES* ITSELF TO BE EMBEDDED IN CLASSES FROM THE genClasses.py MODULE
IT WILL NOT WORK ON ITS OWN!!!

This module is a companion to the genClasses module.  It provides added command
functionality over and above the basic Genesis commands.  This module holds several
classes that subclass into classes in the genClasses module, containing most commands
that can be executed in each class."""

__author__ = "Mike J. Hopkins"
__date__ = "19 August 2004"
__version__ = "$Revision: 1.4.1a $"
__credits__ = """ Daniel R. Gowans, for contributions to content.
Frontline PCB, for an excellent scripting interface to Genesis 2000"""

# drgowans - 8/21/2003 - Modified module to be subclassed in genClasses.
# Before it was only called as a class instance.  However, this created a
# few problems, in that the programmer had to remember if a method was in
# the main class or the class instance, the class instance had to be referred
# to when calling it, and backwards compatibility required wrapper functions.
# By directly subclassing, wrapper functions could be removed, reducing clutter
# significantly, while preserving backwards compatibility.  This also should make
# it easier to refer to parent class components without explicitly passing the
# parent class.  While a little less explicit, it should work out for those with
# access to both classes.  Strangely, these should probably be subclassed in
# reverse, since the classes subclassing the others have all the lowest level
# functions contained, but the change is only in semantics - people import the
# genClasses module instead of the genCommands module into their program.

# drgowans - 8/22/2003 - Moved all non-basic methods from the genClasses module
# to this module.
'''
20210901 根据板边程式需要用到的genesis功能补充执行函数  zl
'''
# StepCmds.unaffectAll  清除所有影响层 --20210901
# StepCmds.setFilterTypes 过滤选择的物件类型  feat_types=xxx\;yyy\;zzz   传入参数为物件类型集合 和 polarity（正负性）--20210909
# StepCmds.setTextFilter 过滤指定文字 text --20211002 zl
# 属性过滤（不包含属性值） setAttrFilter2 --20211011 zl
# StepCmds.copySel_2 补充缺失的参数，包括偏移量，位置，镜像 --20210901
# StepCmds.srFill_2 针对影响层填充 --20210901
# selectPolarity   转换选择物件的正负性 --20210909
# selectResize 改变size -- 20210913
# truncate  清空层 -- 20210914
# 排版 --20210923 zl
# panelSize
# sr_tab_add
# sr_close
# Transform 转换 --20211028
# 钻孔层贯穿层设置 setDrillThrough -- 20211029
# compareLayers 层对比  -- 20211101 zl
###
# selectAll  选择物件时默认为select,可传入参数为unselect --20210924 zl
# setFilterSlot 过滤范围内的line oval --20210924 zl
# setAdv 过滤器高级属性(advanced)设置   -- 20210924 zl
# clip_area(根据影响层)  clip_area2(根据层名) --20210926 zl
# updateStep --更新step   changeStep--release和restore(step) -- 20210929 zl
# prof_to_rout -- 20211002 zl
# selectCutData -- 20211003 zl 填充铜皮
# stpnum_xxx pcb numbering  --20211011 zl
# break_isl_hole    -- 20211014 zl
# 画线（矩形）
# addPolyline2      -- 带圆角的 --20211015 zl
# addPolyline3      -- 带折线角的 --20211015 zl
# resetFill         -- 重置填充参数（实铜)   20211022 zl
# addAttr_zl        -- 添加属性 20211110 zl
# selectRepeat      -- 重复选择的物件 20211115 zl
# selectCreateProf  -- 将选择的物件生成profile 20211116 zl
# selectSingal方法中命令有问题，将sel_signal_feat 改为sel_single_feat  20211208 zl
# FeatureToDrillPattern      --20211213 zl
# selectByIndex     -- 选择指定index对应的物件 20211214 zl
# deleteShapeList     -- 清除shapelist 重新生成index 20211214 zl
# addPolyline2 加多边形 传入连续的n个点 args为多个迭代器对象，每个迭代器两个元素（x,y）  20211229 zl
# refSelectFilter2 对reference层进行属性过滤  20220314 zl
# selectFill    增加x_off y_off 参数    --20220601 zl
# createSymbol 创建symbol --20240530 zl
# setAttrFilter_pro -- 20250226 zl
# setAttrLogic_pro -- 20250226 zl

# Import standard Python modules
import os, re


# Identify yourself!
# print("Using genCommands.py Rev " + __version__)

class JobCmds:
    """This class defines commands which will be invoked by a job.  It is added
    to the job class."""

    ### General Job Manipulation Methods ###
    # ......................................#
    def open(self, lock):
        """Open the job, and checkout if so indicated
                  lock - integer: if > 1, job is checked out/locked"""

        self.COM('is_job_open,job=%s' % self.name)

        # open the job, checkout if indicated
        # if already open, checkout if indicated, check back in if indicated
        if self.COMANS == 'yes':
            print("Job already open, not opening")
            if (lock > 0):
                self.COM('check_inout,mode=out,type=job,job=' + self.name)
            else:
                self.COM('check_inout,mode=test,type=job,job=' + self.name)
                if not (self.COMANS == 'no'):
                    self.COM('check_inout,mode=in,type=job,job=' + self.name)
        else:
            STR = 'open_job,job=%s' % (self.name)
            self.COM(STR)
            self.group = self.COMANS
            if ((self.STATUS < 1) and (lock > 0)):
                self.COM('check_inout,mode=out,type=job,job=' + self.name)

        return self.STATUS

    def close(self, unlock):
        """ Close job represented by this class.
               unlock - if > 1, checks in/unlocks the job"""
        self.COM('close_job,job=' + self.name)
        if ((self.STATUS < 1) and (unlock > 0)):
            self.COM('check_inout,mode=test,type=job,job=' + self.name)
            if not (self.COMANS == 'no'):
                self.COM('check_inout,mode=in,type=job,job=' + self.name)
        return self.STATUS

    def addStep(self, name):
        """ Add a step to the job.
                 name - name of new step"""

        STR = 'create_entity,job=%s,is_fw=no,type=step,name=%s,fw_type=form' % (self.name, name)
        self.COM(STR)
        self.group = self.COMANS

        # Re-populate the steps list
        self.getInfo()
        self.getSteps()

        return self.STATUS

    # 20240109 zl 拷贝step 默认是当前料号，也可从其它料号拷贝
    def copyStep(self, source_job='', source_name='', dest_job='', name=''):
        """ Copy a step from current job or other job"""

        STR = 'copy_entity,type=step,source_job=%s,source_name=%s,dest_job=%s,dest_name=%s,dest_database=' % (source_job,source_name,dest_job, name)
        self.COM(STR)
        self.group = self.COMANS

        # Re-populate the steps list
        self.getInfo()
        self.getSteps()
        return self.STATUS

    def removeStep(self, name):
        """ Remove a step from the job.
                name - name of step to delete"""

        STR = 'delete_entity,job=%s,type=step,name=%s' % (self.name, name)
        self.COM(STR)
        self.group = self.COMANS

        # Re-populate the steps list
        self.getInfo()
        self.getSteps()

        return self.STATUS

    # Check out the job - not done
    def checkout(self):
        """ Not implemented yet. """
        return

        # Check in the job - not done

    def checkin(self):
        """ Not implemented yet. """
        return

    def save(self, override='no'):
        """ Save the job pointed to by the job class (job.name)
              override (optional) defaults to no.  If set to yes, then overrides online violations"""

        if not (override == 'no' or override == 'yes'):
            override = 'no'

        STR = 'save_job,job=%s,override=%s' % (self.name, override)
        self.COM(STR)

        return self.STATUS

    def setGenesisAttr(self, name, value):
        """ Set job attribute to a value, update Python attribute value.
                name - string containing name of attribute
                value - string/int/float containing value of attribute
                  NOTE:  Value may be cast to string upon retreival"""

        STR = 'set_attribute,type=job,job=%s,name1=,name2=,name3=,attribute=%s,value=%s,units=inch' % (
        self.name, name, str(value))
        self.COM(STR)

        setattr(self, name, value)

        return self.STATUS

    def importForm(self, formName, newFormName=''):
        """ Import a form into the job from genesislib.
                formName - string containing name of form to import"""
        if (newFormName == ''):
            STR = 'copy_form,src_job=genesislib,src_form=%s,dst_job=%s,dst_form=%s' % (formName, self.name, formName)
        else:
            STR = 'copy_form,src_job=genesislib,src_form=%s,dst_job=%s,dst_form=%s' % (formName, self.name, newFormName)
        self.COM(STR)
        self.getInfo()
        self.getForms()  # to update the forms list

        return self.STATUS


class StepCmds:
    """This class defines commands which will be invoked on/by a step.  methods are added
    to the step class."""

    ### General Step Manipulation Methods ###
    # .......................................#

    def open(self, iconic='No'):
        """Open the step in graphic editor.
               iconic - string "Yes" or "No" indicating whether to open step as an icon only"""

        STR = 'open_entity,job=%s,type=step,name=%s,iconic=%s' % (self.job.name, self.name, iconic)
        self.COM(STR)
        self.group = self.COMANS
        return self.STATUS

    def close(self):
        """Close the editor window"""

        self.COM('editor_page_close')

    def Undo(self):
        self.COM("undo")

    def setGenesisAttr(self, name, value):
        """ Set step attribute to a value, update Python attribute value.
                name - string containing name of attribute
                value - string/int/float containing value of attribute
                  NOTE:  Value may be cast to string upon retreival"""

        STR = 'set_attribute,type=step,job=%s,name1=%s,name2=,name3=,attribute=%s,value=%s,units=inch' % (
        self.job.name, self.name, name, str(value))
        self.COM(STR)

        setattr(self, name, value)

        return self.STATUS

    ### DISPLAY/LAYER SELECTION Methods ###
    # .....................................#

    def display(self, lay, work=1):
        """Displays the layer in color 1, makes it work layer by default
                lay - string containing layer name
                work - integer 0=don't make work layer  1=make work layer"""

        self.display_layer(lay, 1, work)

    def display_layer(self, lay, num, work=0, display='yes'):
        """Display layer in editor.
                lay - string containing layer name
                num - integer (1-4) indicating color to display
                work - defaults to 0, see display()
                display - 'yes' to display layer, 'no' to clear layer.  default: 'yes'"""

        self.COM('display_layer,name=' + lay + ',display=' + display + ',number=' + repr(num))
        if work:
            self.COM('work_layer,name=' + lay)

    def displayChain(self, display="yes"):

        self.COM("display_chain,display=%s" % display)

    def clearAll(self):
        """Clears all the layers from editor window (turns everything off)
           this means it clears and unaffects all layers, selections, and highlights"""

        self.COM('clear_layers')
        self.COM('clear_highlight')
        self.COM('affected_layer,mode=all,affected=no')
        return self.STATUS

    def affect(self, lay):
        """ affect a layer in the graphic editor
               lay - name of layer"""

        self.COM('affected_layer,name=' + lay + ',mode=single,affected=yes')

    def unaffect(self, lay):
        """ un-affect a layer in the graphic editor
               lay - name of layer"""

        self.COM('affected_layer,name=' + lay + ',mode=single,affected=no')
    # 20210902 zl 清除所有影响层
    def unaffectAll(self):
        """ un-affect all layer in the graphic editor"""
        self.COM('affected_layer,name=,mode=all,affected=no')
    # 20211116 zl 全部设为影响层
    def affectAll(self):
        """ affect all layer in the graphic editor"""
        self.COM('affected_layer,name=,mode=all,affected=yes')
    # Affected by filter
    def affectFilter(self, filter):
        """ Affect by filter in Graphic Editor
                filter - string containing filter configuration"""

        self.COM('affected_filter,filter=' + filter)
        self.COM('get_affect_layer')
        return self.COMANS.split()

    def zoomHome(self):
        """ Zoom out to profile view/home"""
        self.COM('zoom_home')

    #20220330 zl 设置显示区域
    def zoomArea(self, x1, y1, x2, y2):
        """ 显示区域 """
        STR = 'zoom_area,x1=%s,y1=%s,x2=%s,y2=%s' % (x1, y1, x2, y2)
        self.COM(STR)
        return self.STATUS

    ### Filter setup Methods ###
    # ...............................#
    def resetFilter(self):
        """Reset the selection filter"""

        self.COM('filter_reset,filter_name=popup')

    def resetFilter_pro(self):
        self.COM('adv_filter_reset')
        self.COM('reset_filter_criteria,filter_name=,criteria=all')

    # 属性过滤（含有值）
    def setAttrFilter(self, attr, option="option="):
        """Set an attribute in the attribute filter
                attr - name of attribute"""

        self.COM('filter_atr_set,filter_name=popup,condition=yes,attribute=%s,%s' % (attr, option))

    # 属性过滤（不包含属性值）
    def setAttrFilter2(self, attr):
        """Set an attribute in the attribute filter
                attr - name of attribute"""

        self.COM('filter_atr_set,filter_name=popup,condition=no,attribute=%s' % attr)

    # attr and/or   1:and 0: or
    def setAttrLogic(self, logic=1):
        """set attr logic  logic = and/or """
        logic = 'and' if logic else 'or'
        self.COM('filter_atr_logic,filter_name=popup,logic=%s' % logic)

    # 过滤属性
    def setAttrFilter_pro(self, attr_name='', option='', text='', exclude_attr='no', condition='yes'):
        self.COM('set_filter_attributes,filter_name=popup,exclude_attributes=%s,condition=%s,attribute=%s,min_int_val=0,max_int_val=0,min_float_val=0,max_float_val=0,option=%s,text=%s' % (exclude_attr, condition, attr_name, option, text))

    # 属性逻辑 包含 inc_attr/排除 exc_attr  logic and/or
    def setAttrLogic_pro(self, logic='or', criteria='inc_attr'):
        self.COM('set_filter_and_or_logic,filter_name=popup,criteria=%s,logic=%s' % (criteria, logic))

    def setSymbolFilter(self, syms='', syms2=''):
        """Set a symbol on which to filter
                syms - symbol name"""
        if syms:
            self.COM('filter_set,filter_name=popup,update_popup=no,include_syms=' + syms)
        if syms2:
            self.COM('filter_set,filter_name=popup,update_popup=no,exclude_syms=' + syms2)
    # 20210908 zl  过滤选择的物件类型  feat_types=xxx\;yyy\;zzz   传入参数为物件类型集合
    # 20210916 zl 修改：type为字符串（多个类型用|分隔）
    def setFilterTypes(self,types="",polarity='positive\;negative'):
        if types:
            typeList = types.split('|')
            types = '\;'.join(typeList)
            self.COM('filter_set,filter_name=popup,update_popup=no,feat_types=%s,polarity=%s' % (types,polarity))
        else:
            self.COM('filter_set,filter_name=popup,update_popup=no,polarity=%s' % polarity)

    def setFilterTypes_pro(self,types="",polarity='positive|negative'):
        series = ('lines','pads','surfaces','arcs','text')
        filter_list = []
        if types:
            typeList = types.split('|')
            for serie in series:
                if serie in typeList:
                    filter_list.append('%s=yes' % serie)
                else:
                    filter_list.append('%s=no' % serie)
        if filter_list:
            self.COM('set_filter_type,filter_name=,%s' % (",".join(filter_list)))
        series = ('positive', 'negative')
        filter_list = []
        if polarity:
            polarityList = polarity.split('|')
            for p in polarityList:
                if p in series:
                    filter_list.append('%s=yes' % p)
                else:
                    filter_list.append('%s=no' % p)
            self.COM('set_filter_polarity,filter_name=,%s' % (",".join(filter_list)))

    # 20211002 zl  过滤指定文字
    def setTextFilter(self,text):
        self.COM('filter_set,filter_name=popup,update_popup=no,text=' + text)
    # ATTRIBUTE METHODS

    # 20210924 zl 过滤范围内的line oval
    def setFilterSlot(self,slot='line',slot_by='length',min_len=0,max_len=0,min_angle=0,max_angle=0):
        """Filter line/oval by length/angle
            between minlen/minangle ~ maxlen/maxangle"""
        slot_types = slot.split('|')
        slot_by_types = slot_by.split('|')
        if len(slot_types) > 1:
            slot = '\;'.join(slot_types)
        if len(slot_by_types) > 1:
            slot_by = '\;'.join(slot_by_types)
        array = []
        if 'length' in slot_by:
            STR2 = 'min_len=%s,max_len=%s' % (min_len,max_len)
            array.append(STR2)
        if 'angle' in slot_by:
            STR2 = 'min_angle=%s,max_angle=%s' % (min_angle,max_angle)
            array.append(STR2)
        arrayStr = ','.join(array)
        STR = 'filter_set, filter_name = popup, update_popup = yes, slot = %s, slot_by = %s,%s'%(slot,slot_by,arrayStr)
        self.COM(STR)
        return self.STATUS

    # 20210924 zl 过滤器高级属性设置 advanced
    def resetAdv(self):
        self.COM('adv_filter_reset,filter_name=popup')

    def setAdv_limitbox(self,min_dx=0,max_dx=0,min_dy=0,max_dy=0):
        self.COM('adv_filter_set,filter_name=popup,update_popup=yes,limit_box=yes,min_dx=%s,max_dx=%s,'
                 'min_dy=%s,max_dy=%s' % (min_dx,max_dx,min_dy,max_dy))

    def setAdv_boundbox(self,min_width=0,max_width=0,min_length=0,max_length=0):
        self.COM('adv_filter_set,filter_name=popup,update_popup=yes,bound_box=yes,min_width=%s,max_width=%s,'
                 'min_length=%s,max_length=%s' % (min_width, max_width, min_length, max_length))

    def setAdv_selected(self,selected='any'):
        self.COM('adv_filter_set,filter_name=popup,update_popup=no,selected=' + str(selected))

    def setAdv_attributes(self,attributes='any'):
        self.COM('adv_filter_set,filter_name=popup,update_popup=no,attributes=' + str(attributes))

    def setAdv_arcvalues(self,min_sweep_angle=0,max_sweep_angle=0,min_diameter=0,max_diameter=0,min_arc_len=0,max_arc_len=0):
        self.COM('adv_filter_set,filter_name=popup,update_popup=yes,arc_values=yes,min_sweep_angle=%s,max_sweep_angle=%s,min_diameter=%s,max_diameter=%s,'
                 'min_arc_len=%s,max_arc_len=%s' % (min_sweep_angle, max_sweep_angle, min_diameter, max_diameter,min_arc_len,max_arc_len))

    def setAdv_arcdirection(self,arc_direction='any'):
        self.COM('adv_filter_set,filter_name=popup,update_popup=no,arc_direction='+ str(arc_direction))

    def setAdv_rotations(self,rotations=0,min_rotation=0,max_rotation=0):
        self.COM('adv_filter_set,filter_name=popup,update_popup=yes,rotations=%s,min_rotation=%s,max_rotation=%s'%(rotations,min_rotation,max_rotation))

    def setAdv_mirror(self,mirror='any'):
        self.COM('adv_filter_set,filter_name=popup,update_popup=no,mirror='+ str(mirror))

    def setAdv_srfvalues(self,min_islands=0,max_islands=0,min_holes=0,max_holes=0,min_edges=0,max_edges=0):
        self.COM('adv_filter_set,filter_name=popup,update_popup=yes,srf_values=yes,min_islands=%s,max_islands=%s,min_holes=%s,max_holes=%s,'
                 'min_edges=%s,max_edges=%s'%(min_islands,max_islands,min_holes,max_holes,min_edges,max_edges))

    def setAdv_srfarea(self,min_area=0,max_area=0):
        self.COM('adv_filter_set,filter_name=popup,update_popup=yes,srf_area=yes,min_area=%s,max_area=%s' % (min_area,max_area))

    def setAdv_strlen(self,min_str_len=0,max_str_len=0):
        self.COM('adv_filter_set,filter_name=popup,update_popup=yes,str_len=yes,min_str_len=%s,max_str_len=%s' % (min_str_len,max_str_len))

    def setAdv_fontname(self,fontstring=''):
        self.COM('adv_filter_set,filter_name=popup,update_popup=yes,fontname='+ str(fontstring))

    def setAdv_txt_types(self,types=''):
        self.COM('adv_filter_set,filter_name=popup,update_popup=no,txt_types='+ str(types))
    #########################################
    def resetAttr(self):
        """Reset the attribute List"""

        self.COM('cur_atr_reset')
    # 20220818 zl add/replace  mode=0/非0
    def addAttr(self, attr, mode=0, attrVal='option='):
        """Add attribute to attribute list
            valType determines what attrVal should be
            valType : default is 'int', also 'float', 'text', 'option'"""
        if mode == 0:
            mode = 'add'
        else:
            mode = 'replace'
        self.COM('cur_atr_set,attribute=%s,%s' % (attr, attrVal))
        self.COM("sel_change_atr,mode=%s" % mode)
        self.resetAttr()
    # 添加属性
    def addAttr_zl(self,attr):
        self.COM('cur_atr_set,attribute=%s' % attr)

    ### SELECTION RELATED METHODS ###
    # ...............................#
    def selectNone(self):
        """Unselect all features."""

        self.COM('sel_clear_feat')
    # 20210924 zl -- 添加参数operation区分select和unselect
    def selectAll(self,operation='select'):
        """Select all features on affected layers, (applying popup filter)
               returns number selected"""

        self.COM('filter_area_strt')
        self.COM('''filter_area_end,layer=,filter_name=popup,operation=%s,
        area_type=none,inside_area=no,intersect_area=no,lines_only=no,
        ovals_only=no,min_len=0,max_len=0,min_angle=0,max_angle=0
        ''' % operation)
        # return int(self.COMANS)
    # 20240520 zl
    def selectAll_pro(self, operation='select'):
        self.COM('filter_area_strt')
        self.COM('filter_area_end, filter_name=popup, operation=%s' % operation)

    #20211214 zl  选择指定index对应的物件
    def selectByIndex(self,layer,index):
        STR = 'sel_layer_feat,operation=select,layer=%s,index=%s' % (layer,index)
        self.COM(STR)
        return self.STATUS

    def selectSymbol(self, symbolName='', reset=0, clear=0):
        """Select the Symbol indicated in the string resets if told to,
        clears other features if told to.
               symbolName - Symbol to select
               reset - resets filter if you don't want this
                   action to be affected by pre-existing filter settings.
                defaults to NOT reset (integer 0 = no reset, 1 = reset)
               clear - Clear all selected features first ( 0 = don't clear, 1 = clear)"""

        if reset:
            self.job.COM('filter_reset,filter_name=popup')
        if clear:
            self.job.COM('sel_clear_feat')
        self.COM('filter_set,filter_name=popup,update_popup=no,include_syms=' + symbolName)
        self.COM('filter_area_strt')
        self.COM('''filter_area_end,layer=,filter_name=popup,operation=select,
        area_type=none,inside_area=no,intersect_area=no,lines_only=no,
        ovals_only=no,min_len=0,max_len=0,min_angle=0,max_angle=0
        ''')
        return int(self.COMANS)

    # 20240601 zl
    def selectSymbol_pro(self, include='', exclude=''):
        if include:
            self.COM('set_filter_symbols,filter_name=,exclude_symbols=no,symbols=%s' % include)
        if exclude:
            self.COM('set_filter_symbols,filter_name=,exclude_symbols=yes,symbols=%s' % exclude)
        self.COM('filter_area_strt')
        self.COM('filter_area_end,filter_name=popup,operation=select')
        return int(self.COMANS)

    def selectRectangle(self, xs, ys, xe, ye, intersect='no', reset=0):
        """Select all features in a rectangle
               xs, ys, xe, ye - start and end x,y coordinates
               intersect - if 'yes' selects symbols intersected by rectangle but not fully inside
                    defaults to 'no'
               reset - see selectSymbol()"""

        if reset:
            self.resetFilter()
        self.COM('filter_area_strt')
        self.COM('filter_area_xy,x=%s,y=%s' % (xs, ys))
        self.COM('filter_area_xy,x=%s,y=%s' % (xe, ye))
        self.COM(
            'filter_area_end,layer=,filter_name=popup,operation=select,area_type=rectangle,inside_area=yes,intersect_area=%s' % (
                intersect))

        return int(self.COMANS)

    def refSelectFilter(self, refLay, include_syms='', exclude_syms='', mode='touch', reset=0):
        """Select by reference, using filter (so you better reset the filter if you need to!)
               refLay - reference layer
               include_syms (optional) - symbols to include in selection
               exclude_syms (optional) - symbols to exclude from selection
               mode (optional) - defaults to 'touch'
               reset (optional) - defaults to 0 (0 = DON'T reset filter, 1 = reset filter)"""

        if reset:
            self.resetFilter()
        STR = '''sel_ref_feat,layers=%s,use=filter,mode=%s,\
        f_types=line\;pad\;surface\;arc\;text,polarity=positive\;negative,\
        include_syms=%s,exclude_syms=%s'''
        STR = STR % (refLay, mode, include_syms, exclude_syms)
        self.COM(STR)
        return int(self.COMANS)
    # 20220314
    # 对reference层进行属性过滤
    def refSelectFilter2(self, refLay, include_syms='', exclude_syms='', mode='touch', reset=0, types='line|pad|surface|arc|text', polarity='positive\;negative'):
        """Select by reference, using filter (so you better reset the filter if you need to!)
               refLay - reference layer
               include_syms (optional) - symbols to include in selection
               exclude_syms (optional) - symbols to exclude from selection
               mode (optional) - defaults to 'touch'
               reset (optional) - defaults to 0 (0 = DON'T reset filter, 1 = reset filter)"""
        if reset:
            self.resetFilter()
        typeList = types.split('|')
        types = '\;'.join(typeList)
        STR = '''sel_ref_feat,layers=%s,use=filter,mode=%s,\
        f_types=%s,polarity=%s,include_syms=%s,exclude_syms=%s'''
        STR = STR % (refLay, mode, types, polarity, include_syms, exclude_syms)
        self.COM(STR)
        return int(self.COMANS)

    def Selected_count(self):
        """return number of selected features.  Can be used as boolean as well
                returns zero if no features selected, # features if there are"""

        self.COM('get_select_count')
        selected = int(self.COMANS)
        return selected

    def clearAndReset(self):
        """ Clears any selections in the graphic editor and resets the filter"""

        self.COM('sel_clear_feat')
        self.COM('filter_reset,filter_name=popup')

    def clearSel(self):
        """ Clears selections from graphic editor"""
        self.COM('sel_clear_feat')

    def copySel(self, layerName, invert='no'):
        """ Copies selected features to a new layer
               layerName - name of layer to copy to
               invert - 'yes' or 'no' default to 'no' - invert polarity of features
                    being copied."""

        self.COM('sel_copy_other,dest=layer_name,target_layer=' + layerName + ',invert=' + invert + ',dx=0,dy=0,size=0')
        return self.STATUS

    # 20210901 zl  补充缺失的参数
    def copySel_2(self, layerName, invert='no',dx=0,dy=0,size=0,x_anchor=0,y_anchor=0,rotation=0,mirror='none'):

        self.COM('sel_copy_other,dest=layer_name,target_layer=%s,invert=%s,dx=%s,dy=%s,size=%s,x_anchor=%s,y_anchor=%s,rotation=%s,mirror=%s'
                 %(layerName,invert,dx,dy,size,x_anchor,y_anchor,rotation,mirror))
        return self.STATUS

    def moveSel(self, layerName, invert="no", dx=0, dy=0, size=0, x_anchor=0, y_anchor=0, rotation=0, mirror="none"):
        """ Copies selected features to a new layer
               layerName - name of layer to copy to
               invert - 'yes' or 'no' default to 'no' - invert polarity of features
                    being copied."""

        self.COM(
            "sel_move_other,target_layer=%s,invert=%s,dx=%s,dy=%s,size=%s,x_anchor=%s,y_anchor=%s,rotation=%s,mirror=%s" % (
            layerName, invert, dx, dy, size, x_anchor, y_anchor, rotation, mirror))
        return self.STATUS

    def selectDelete(self):
        """ Delete Selected features."""
        self.COM('sel_delete')

    ### CHECKLIST OPERATION METHODS ###
    # .................................#

    def createCheck(self, checkName):
        """Create a new checklist
               checkName - name of new checklist"""

        STR = 'chklist_create,chklist=' + checkName
        self.COM(STR)
        self.getInfo()
        self.getChecks()
        return self.STATUS

    def deleteCheck(self, checkName):
        """Delete a checklist
               checkName - name of checklist to delete"""

        STR = 'chklist_delete,chklist=' + checkName
        self.COM(STR)
        self.getInfo()
        self.getChecks()
        return self.STATUS

    # 清除shapelist 重新生成index
    def deleteShapeList(self,layer):
        STR = 'delete_shapelist,layer=%s' % layer
        self.COM(STR)
        return self.STATUS

    # paste到某个checklist中   先要取到行数row
    def pasteCheck(self,checkName):
        row = self.checks.get(checkName).getInfo().get('gNUM_ACT') if self.checks.get(checkName) else 0
        STR = 'chklist_ppaste,chklist=' + checkName + ',row= '+ str(row)
        self.COM(STR)
        return self.STATUS

    # 关闭Check窗口
    def closeCheck(self,checkName):
        STR = 'chklist_close,chklist=' + checkName + ',mode=hide'
        self.COM(STR)
        return self.STATUS

    def importCheck(self, checkName, replace=0):
        """get checklist from library - replace if indicated
               checkName - name of checklist to replace
               replace - defaults to 0, if > 0, existing checklist is replaced"""

        if replace:
            self.COM('chklist_create,chklist=' + checkName)
            self.COM('chklist_delete,chklist=' + checkName)
            self.COM('chklist_from_lib,chklist=' + checkName)
            self.getInfo()
            self.getChecks()
        else:
            self.VOF()
            self.COM('chklist_from_lib,chklist=' + checkName)
            self.VON()
            self.getInfo()
            self.getChecks()

        return self.STATUS

    ### Buffer Operations ###
    # .......................#
    def buffCopy(self):
        """Copy selected features to buffer"""

        self.COM('sel_buffer_copy,x_datum=0,ydatum=0')

    def buffPaste(self, x=0, y=0):
        """Paste from buffer to x and y location indicated (defaults to origin)"""

        self.COM('sel_buffer_paste,x_datum=' + repr(x) + ',y_datum=' + repr(y))

    ### Layer-manipulation Methods ###
    # ................................#
    def copyToAffected(self, invert='no', dx=0, dy=0, size=0):
        """ Copy selected features to affected layers.
               invert (default to 'no') - 'yes' or 'no' indicates if features' polarity inverted
               dx,dy - x and y shift for copied features
               size - resize features by this amount when copied"""

        STR = 'sel_copy_other,dest=affected_layers,invert=%s,dx=%f,dy=%f,size=%f'
        STR = STR % (invert, dx, dy, size)
        self.COM(STR)

    def copyToLayer(self, lay, invert='no', dx=0, dy=0, size=0):
        """ Copy selected features to a specific layer.  See copyToAffected() for options"""

        STR = 'sel_copy_other,dest=layer_name,target_layer=%s,invert=%s,dx=%f,dy=%f,size=%f'
        STR = STR % (lay, invert, dx, dy, size)
        self.COM(STR)

    # 20210912 zl 增加 ins_layer 参数
    def createLayer(self, name, context='misc', laytype='document', polarity='positive',ins_layer=''):
        """ Create a blank layer.
               name - new layer name
               context - (defaults to 'misc') context of layer (board,misc)
               laytype - (defaults to 'document) type of layer (document, signal, etc...)
               polarity - (defaults to positive) polarity of layer (positive, negative)"""

        STR = 'create_layer,layer=%s,context=%s,type=%s,polarity=%s,ins_layer=%s' % (name, context, laytype, polarity, ins_layer)
        self.COM(STR)
        self.getInfo()
        self.getLayers()
        return self.STATUS

    def removeLayer(self, lay):
        """ Remove a layer
              lay - name of layer"""
        if self.isLayer(lay):
            self.COM('delete_layer,layer=' + lay)

    def copyLayer(self, job, step, lay, dest_lay, mode='replace', invert='no'):
        """ Copy a layer from another location to current step
              job - name of source job
              step - name of source step
              lay - name of source layer
              dest_lay - name of destination layer (to be created)
              mode (defaults to 'replace') - 'replace' to replace, 'append' to add to end of layer list
              invert (defaults to 'no') - invert the layer"""

        STR = 'copy_layer,source_job=%s,source_step=%s,source_layer=%s,dest=layer_name,dest_layer=%s,mode=%s,invert=%s'
        STR = STR % (job, step, lay, dest_lay, mode, invert)
        self.COM(STR)
        return self.STATUS
    # 20211101 zl 层比对
    def compareLayers(self,layer1,job2,step2,layer2,layer2_ext='',tol=1,area='global',consider_sr='yes',ignore_attr='',map_layer='',map_layer_res=1270):
        STR = 'compare_layers,layer1=%s,job2=%s,step2=%s,layer2=%s,layer2_ext=%s,tol=%s,area=%s,consider_sr=%s,ignore_attr=%s,' \
              'map_layer=%s,map_layer_res=%s' % (layer1,job2,step2,layer2,layer2_ext,tol,area,consider_sr,ignore_attr,map_layer,map_layer_res)
        self.COM(STR)
        return self.STATUS

    def mergeLayers(self, sourceLayer, destLayer, invert='no'):
        """ Merge the selected layers"""

        STR = 'merge_layers,source_layer=%s,dest_layer=%s,invert=%s' % (sourceLayer, destLayer, invert)
        self.COM(STR)

        return self.STATUS

    def inputAuto(self, path, report_path='', report_filename='', copy_to_job='no'):
        """ Run the input screen on a specific path.  Save the report to another specific path.
            path - path to look for input data
            report_path - path in which to save report data
            report_filename (optional)  will use jobname_inp.txt if not specified
            copy_to_job (optional) "yes" or "no" to tell if you want to copy input files to job input directory"""

        if report_path == '':
            report_path = path

        if report_filename == '':
            report_filename = self.job.name + '_inp.txt'

        if not (report_path[len(report_path) - 1] == '/'):
            report_full = report_path + '/' + report_filename
        else:
            report_full = report_path + report_filename

        # STR = 'input_set_params,path=%s,job=%s,step=%s,wheels=yes,gbr_ext=yes,gbr_units=auto,drl_ext=yes,drl_units=auto' % (path,self.job.name,self.name)
        # self.COM(STR)

        STR = 'input_identify,path=%s,job=%s,script_path=%s,unify=yes,gbr_ext=yes,drl_ext=yes,gbr_units=auto,drl_units=auto,break_sr=no' % (
        path, self.job.name, report_full + '_id')
        self.COM(STR)
        STR = 'input_auto,path=%s,job=%s,step=%s,report_path=%s,copy_to_job=%s' % (
        path, self.job.name, self.name, report_full, copy_to_job)
        self.COM(STR)

        return self.STATUS

    # FEATURE MANIPULATION
    def addPad(self, x, y, symbol, polarity='positive', angle=0, mirror='no', nx=1, ny=1, dx=0, dy=0, xscale=1,
               yscale=1, attributes='no'):
        """Add a pad to the selected layers in this step.  The arguments are self explanatory.
        All are optional except x, y, and symbol. NOTE: This is precise only to sixth decimal
        Also remember that dx and dy are in mils(microns)"""

        nx = str(int(nx))
        ny = str(int(ny))
        angle = str(int(angle))
        # array = [x, y, symbol, polarity, angle, mirror, nx, ny, dx, dy, xscale, yscale]
        STR = "add_pad,attributes=%s,x=%.6f,y=%.6f,symbol=%s,polarity=%s,angle=%s,mirror=%s,nx=%s,ny=%s,dx=%.3f,dy=%.3f,xscale=%.4f,yscale=%.4f" % (
        attributes, x, y, symbol, polarity, angle, mirror, nx, ny, dx, dy, xscale, yscale)
        self.COM(STR)

        return self.STATUS

    def addLine(self, xs, ys, xe, ye, symbol, polarity='positive', attributes='no'):
        """Add a line to the selected layers in this step.  The arguments are self explanatory.
        All are mandatory except polarity, which defaults to pos, and attributes, defaulting to no.
        NOTE: This is precise only to sixth decimal"""

        STR = "add_line,attributes=%s,xs=%.6f,ys=%.6f,xe=%.6f,ye=%.6f,symbol=%s,polarity=%s" % (
        attributes, xs, ys, xe, ye, symbol, polarity)
        self.COM(STR)

        return self.STATUS

    def addArc(self, xs, ys, xe, ye, xc, yc, symbol, direction="ccw", polarity='positive', attributes='no'):
        """Add an arc to the selected layers in this step.  xs/ys - start, xe/ye - end, xc/yc, center
        direction is 'CW' or 'CCW'.  All are mandatory except polarity, which defaults to pos, and
        attributes, defaulting to no.  NOTE: This is precise only to sixth decimal"""

        STR = "add_arc,attributes=%s,xs=%.6f,ys=%.6f,xe=%.6f,ye=%.6f,xc=%.6f,yc=%.6f,symbol=%s,polarity=%s,direction=%s" % (
        attributes, xs, ys, xe, ye, xc, yc, symbol, polarity, direction)
        self.COM(STR)

        return self.STATUS

    def addText(self, x, y, text, xSize, ySize, width, mirror='no', angle=0, type='string', fontname='standard',
                polarity='positive', attributes='no'):
        """Add text to the selected layers in this step.  x/y - text bottomleft corner (bottomright if mirror,
        xSize, ySize is size in mil of text, width is line width in mil, mirror defaults to no, angle defaults to 0
        but can be 0,90,180,270 -polarity defaults to positive, attributes defaults to no.
        NOTE: This is precise only to sixth decimal"""

        STR = "add_text,attributes=%s,type=%s,x=%.6f,y=%.6f,text=%s,x_size=%.3f,y_size=%.3f,w_factor=%.5f,polarity=%s,angle=%s,mirror=%s,fontname=%s" % (
        attributes, type, x, y, text, xSize, ySize, width, polarity, angle, mirror, fontname)
        self.COM(STR)

        return self.STATUS
    # 将fontname作为参数 20211002 zl
    def changeText(self, text="", x_size=-25.4, y_size=-25.4, w_factor=-1, polarity="no_change", angle=-1,
                   mirror="no_change", fontname=''):
        STR = "sel_change_txt,text=%s,x_size=%s,y_size=%s,w_factor=%s,polarity=%s,angle=%s,mirror=%s,fontname=%s" % (
        text, x_size, y_size, w_factor, polarity, angle, mirror, fontname)
        self.COM(STR)

    def addRectangle(self, xs, ys, xe, ye, polarity='positive', attributes='no'):
        """Add a rectangle to the selected layers in this step.  Need opposing
        corners for this to work.  polarity defaults to positive, attributes to no.
        NOTE: This is precise only to sixth decimal"""

        self.COM('add_surf_strt')
        STR = "add_surf_poly_strt,x=%.6f,y=%.6f" % (xs, ys)
        self.job.COM(STR)
        STR = "add_surf_poly_seg,x=%.6f,y=%.6f" % (xs, ye)
        self.job.COM(STR)
        STR = "add_surf_poly_seg,x=%.6f,y=%.6f" % (xe, ye)
        self.job.COM(STR)
        STR = "add_surf_poly_seg,x=%.6f,y=%.6f" % (xe, ys)
        self.job.COM(STR)
        STR = "add_surf_poly_seg,x=%.6f,y=%.6f" % (xs, ys)
        self.job.COM(STR)
        self.job.COM('add_surf_poly_end')
        STR = "add_surf_end,attributes=%s,polarity=%s" % (attributes, polarity)
        self.job.COM(STR)

        return self.STATUS

    # 20221104 加多边形铜皮
    # def addRectangle2(self, *args, polarity='positive', attributes='no'):
    #     """Add a rectangle to the selected layers in this step.  Need opposing
    #     corners for this to work.  polarity defaults to positive, attributes to no.
    #     NOTE: This is precise only to sixth decimal"""
    #
    #     self.COM('add_surf_strt')
    #     self.COM("add_surf_poly_strt,x=%.6f,y=%.6f" % (args[0][0], args[0][1]))
    #     for i, arg in enumerate(args):
    #             if i:
    #                 STR = "add_surf_poly_seg,x=%.6f,y=%.6f" % (arg[0], arg[1])
    #                 self.job.COM(STR)
    #     self.job.COM("add_surf_poly_seg,x=%.6f,y=%.6f" % (args[0][0], args[0][1]))
    #     self.job.COM('add_surf_poly_end')
    #     STR = "add_surf_end,attributes=%s,polarity=%s" % (attributes, polarity)
    #     self.job.COM(STR)
    #     return self.STATUS

    def addPolyline(self, xs, ys, xe, ye, symbol, polarity='positive', attributes='no'):
        """Add a Polyline to the selected layers in this step.  Need opposing
        corners for this to work.  polarity defaults to positive, attributes to no.
        NOTE: This is precise only to sixth decimal"""

        self.COM('add_polyline_strt')
        STR = "add_polyline_xy,x=%.6f,y=%.6f" % (xs, ys)
        self.job.COM(STR)
        STR = "add_polyline_xy,x=%.6f,y=%.6f" % (xs, ye)
        self.job.COM(STR)
        STR = "add_polyline_xy,x=%.6f,y=%.6f" % (xe, ye)
        self.job.COM(STR)
        STR = "add_polyline_xy,x=%.6f,y=%.6f" % (xe, ys)
        self.job.COM(STR)
        STR = "add_polyline_xy,x=%.6f,y=%.6f" % (xs, ys)
        self.job.COM(STR)
        STR = "add_polyline_end,attributes=%s,symbol=%s,polarity=%s" % (attributes, symbol, polarity)
        self.job.COM(STR)

        return self.STATUS

    # 20211229 zl 加多边形  传入连续的n个点 args为多个迭代器对象，每个迭代器两个元素（x,y）
    # def addPolyline1(self,*args,symbol, polarity='positive', attributes='no'):
    #     self.COM('add_polyline_strt')
    #     for arg in args:
    #         STR = "add_polyline_xy,x=%.6f,y=%.6f" % (arg[0], arg[1])
    #         self.job.COM(STR)
    #     STR = "add_polyline_end,attributes=%s,symbol=%s,polarity=%s" % (attributes, symbol, polarity)
    #     self.job.COM(STR)
    #     return self.STATUS

    # 画带圆角的矩形 radius 单位：my
    def addPolyline2(self, xs, ys, xe, ye, symbol,radius,polarity='positive', attributes='no'):
        radius = float(radius/1000)
        self.COM('add_polyline_strt')
        STR = "add_polyline_xy,x=%.6f,y=%.6f" % (xs + radius, ys)
        self.job.COM(STR)
        STR = "add_polyline_xy,x=%.6f,y=%.6f" % (xe - radius, ys)
        self.job.COM(STR)
        STR = "add_polyline_crv,xc=%.6f,yc=%.6f,xe=%.6f,ye=%.6f,cw=no" % (xe - radius, ys + radius, xe, ys + radius)
        self.job.COM(STR)
        STR = "add_polyline_xy,x=%.6f,y=%.6f" % (xe, ye - radius)
        self.job.COM(STR)
        STR = "add_polyline_crv,xc=%.6f,yc=%.6f,xe=%.6f,ye=%.6f,cw=no" % (xe - radius, ye-radius, xe-radius, ye)
        self.job.COM(STR)
        STR = "add_polyline_xy,x=%.6f,y=%.6f" % (xs + radius, ye)
        self.job.COM(STR)
        STR = "add_polyline_crv,xc=%.6f,yc=%.6f,xe=%.6f,ye=%.6f,cw=no" % (xs + radius, ye - radius, xs, ye-radius)
        self.job.COM(STR)
        STR = "add_polyline_xy,x=%.6f,y=%.6f" % (xs, ys+radius)
        self.job.COM(STR)
        STR = "add_polyline_crv,xc=%.6f,yc=%.6f,xe=%.6f,ye=%.6f,cw=no" % (xs + radius, ys + radius, xs+radius , ys)
        self.job.COM(STR)
        STR = "add_polyline_end,attributes=%s,symbol=%s,polarity=%s" % (attributes, symbol, polarity)
        self.job.COM(STR)

        return self.STATUS

    # 画缺角的矩形
    def addPolyline3(self, xs, ys, xe, ye, symbol, radius, polarity='positive', attributes='no'):
        radius = float(radius/1000)
        self.COM('add_polyline_strt')
        STR = "add_polyline_xy,x=%.6f,y=%.6f" % (xs + radius, ys)
        self.job.COM(STR)
        STR = "add_polyline_xy,x=%.6f,y=%.6f" % (xe - radius, ys)
        self.job.COM(STR)
        STR = "add_polyline_xy,x=%.6f,y=%.6f" % (xe, ys + radius)
        self.job.COM(STR)
        STR = "add_polyline_xy,x=%.6f,y=%.6f" % (xe, ye - radius)
        self.job.COM(STR)
        STR = "add_polyline_xy,x=%.6f,y=%.6f" % (xe - radius, ye)
        self.job.COM(STR)
        STR = "add_polyline_xy,x=%.6f,y=%.6f" % (xs + radius, ye)
        self.job.COM(STR)
        STR = "add_polyline_xy,x=%.6f,y=%.6f" % (xs, ye - radius)
        self.job.COM(STR)
        STR = "add_polyline_xy,x=%.6f,y=%.6f" % (xs, ys + radius)
        self.job.COM(STR)
        STR = "add_polyline_xy,x=%.6f,y=%.6f" % (xs + radius, ys)
        self.job.COM(STR)
        STR = "add_polyline_end,attributes=%s,symbol=%s,polarity=%s" % (attributes, symbol, polarity)
        self.job.COM(STR)
        # ROUT EDITOR COMMANDS

    def addRoutChain(self, layer, size, compensation, feed=0, flag=0, speed=0, first=0, change_direction=-1):
        """ Add selected features to a new rout chain.  This try rout chain 1, and if it fails,
        to try adding the chain, incrementing the chain number, until success.  It only goes to 100.
        Chain Number is returned.  If -1 returned, there was an error
            layer - layer to add rout chain to
            size (float) - size in inches for rout bit can be specified to 10th of mils only.
            compensation (str) - right, left, none
            feed (int) - feed rate
            flag (int) - default 0 - flag number
            speed (int) - default 0 - speed number
            first (int) - default 0 : -1 is not specified.  >0 is the first feature in chain. 0 is first of
            selected features to be added to layer (by index number), on up)
            change_direction (int) - defaults to -1 - not sure what it is for."""

        self.VOF()

        self.STATUS = 1
        chainNum = 0
        while (self.STATUS) and (chainNum <= 100):
            chainNum = chainNum + 1
            STR = 'chain_add,layer=%s,chain=%s,size=%.4f,comp=%s,flag=%s,feed=%s,speed=%s,first=%s,chng_direction=%s' % (
            layer, chainNum, size, compensation, flag, feed, speed, first, change_direction)
            self.COM(STR)
            print("Status: " + str(self.STATUS))

        self.VON()

        if (not self.STATUS):
            return chainNum
        else:
            return -1

    def setChainPlunge(self, layer, chain, len1, len2, intType='corner', mode='wrap', inl_mode='straight',
                       start_of_chain='yes', apply_to='all', len3=0.0, len4=0.0, val1=0, val2=0, ang1=0, ang2=0,
                       ifeed=0, ofeed=0):
        """ Set up the plunge for a rout chain.  Lots and lots of options.  For now, you can look at
        the code yourself."""

        self.COM('chain_list_reset')
        self.COM('chain_list_add,chain=' + str(chain))

        STR = 'chain_set_plunge,layer=%s,type=%s,mode=%s,inl_mode=%s,start_of_chain=%s,' % (
        layer, intType, mode, inl_mode, start_of_chain)
        STR = STR + 'apply_to=%s,len1=%.6f,len2=%.6f,len3=%.6f,len4=%.6f,val1=%s,val2=%s,ang1=%s,ang2=%s,ifeed=%s,ofeed=%s' % (
        apply_to, len1, len2, len3, len4, val1, val2, ang1, ang2, ifeed, ofeed)
        self.COM(STR)

        return self.STATUS

    def routCopy(self, sourceLayer, destLayer, destType='document'):
        """ Copy a rout layer to another layer.  destType determines if copied as normal features or rout features
        Obliterates the layer you are copying to
            destType - 'document' or 'rout'   """

        STR = 'compensate_layer,source_layer=%s,dest_layer=%s,dest_layer_type=%s' % (sourceLayer, destLayer, destType)
        self.COM(STR)

        return self.STATUS

    def srFill(self, layer, polarity="positive", step_margin_x=0, step_margin_y=0, step_max_dist_x=2540,
               step_max_dist_y=2540, sr_margin_x=0, sr_margin_y=0, sr_max_dist_x=0, \
               sr_max_dist_y=0, nest_sr="yes", consider_feat="no", consider_drill="no", consider_rout="no",
               attributes="no"):
        """Sr_fill copper for layer"""

        STR = 'sr_fill,polarity=%s,step_margin_x=%s,step_margin_y=%s,step_max_dist_x=%s,step_max_dist_y=%s,sr_margin_x=%s,sr_margin_y=%s,sr_max_dist_x=%s,\
               sr_max_dist_y=%s,nest_sr=%s,consider_feat=%s,consider_drill=%s,consider_rout=%s,dest=layer_name,layer=%s,attributes=%s ' % \
              (polarity, step_margin_x, step_margin_y, step_max_dist_x, step_max_dist_y, sr_margin_x, sr_margin_y,
               sr_max_dist_x, \
               sr_max_dist_y, nest_sr, consider_feat, consider_drill, consider_rout, layer, attributes)
        self.COM(STR)
        STR = 'fill_params,type=solid,origin_type=datum,solid_type=surface,std_type=line,min_brush=254,use_arcs=yes,symbol=,dx=2.54,dy=2.54,std_angle=45,\
                        std_line_width=254,std_step_dist=1270,std_indent=odd,break_partial=yes,cut_prims=no,outline_draw=no,outline_width=0,outline_invert=no'
        self.COM(STR)

    # 20210901 zl  增加对影响层操作
    def srFill_2(self, polarity="positive", step_margin_x=0, step_margin_y=0, step_max_dist_x=2540,
                 step_max_dist_y=2540, sr_margin_x=0, sr_margin_y=0, sr_max_dist_x=0, \
                 sr_max_dist_y=0, nest_sr="yes", stop_at_steps="", consider_feat="no", consider_drill="no",
                 consider_rout="no", attributes="no"):
        """Sr_fill copper for layer"""

        STR = 'sr_fill,polarity=%s,step_margin_x=%s,step_margin_y=%s,step_max_dist_x=%s,step_max_dist_y=%s,sr_margin_x=%s,sr_margin_y=%s,sr_max_dist_x=%s,\
                 sr_max_dist_y=%s,nest_sr=%s,stop_at_steps=%s,consider_feat=%s,consider_drill=%s,consider_rout=%s,dest=affected_layers,attributes=%s ' % \
              (polarity, step_margin_x, step_margin_y, step_max_dist_x, step_max_dist_y, sr_margin_x, sr_margin_y,
               sr_max_dist_x, \
               sr_max_dist_y, nest_sr, stop_at_steps, consider_feat, consider_drill, consider_rout, attributes)
        self.COM(STR)
        STR = 'fill_params,type=solid,origin_type=datum,solid_type=surface,std_type=line,min_brush=254,use_arcs=yes,symbol=,dx=2.54,dy=2.54,std_angle=45,\
                std_line_width=254,std_step_dist=1270,std_indent=odd,break_partial=yes,cut_prims=no,outline_draw=no,outline_width=0,outline_invert=no'
        self.COM(STR)

    # 20211022 重置填充参数（实铜）
    def resetFill(self):
        STR = 'fill_params,type=solid,origin_type=datum,solid_type=surface,std_type=line,min_brush=254,use_arcs=yes,symbol=,dx=2.54,dy=2.54,std_angle=45,\
                        std_line_width=254,std_step_dist=1270,std_indent=odd,break_partial=yes,cut_prims=no,outline_draw=no,outline_width=0,outline_invert=no'
        self.COM(STR)

    # 20211003 zl 填充铜皮
    def selectCutData(self,det_tol=25.4,con_tol=25.4, rad_tol=2.54,filter_overlaps='no',ignore_width='yes',ignore_holes='none',start_positive='yes',polarity_of_touching='same'):
        STR='sel_cut_data,det_tol=%s,con_tol=%s,rad_tol=%s,filter_overlaps=%s,delete_doubles=no,use_order=yes,' \
            'ignore_width=%s,ignore_holes=%s,start_positive=%s,polarity_of_touching=%s'%(det_tol,con_tol,rad_tol,filter_overlaps,ignore_width,ignore_holes,start_positive,polarity_of_touching)
        self.COM(STR)
        return self.STATUS

    # clip area  20210926 zl
    # 影响层
    def clip_area(self,area='profile',inout='inside',contour_cut='no',margin=2540,feat_types='',ref_layer=''):
        if feat_types:
            feat_types = '\;'.join(feat_types.split('|'))
        else:
            feat_types='line\;pad\;surface\;arc\;text'
        if ref_layer:
            STR= 'clip_area_end,layers_mode=affected_layers,layer=,area=reference,area_type=rectangle,inout=%s,contour_cut=%s,margin=%s,ref_layer=%s,feat_types=%s'\
                 %(inout,contour_cut,margin,ref_layer,feat_types)
        else:
            STR = 'clip_area_end,layers_mode=affected_layers,layer=,area=%s,area_type=rectangle,inout=%s,contour_cut=%s,margin=%s,ref_layer=%s,feat_types=%s' \
                  % (area, inout, contour_cut, margin, ref_layer, feat_types)
        self.COM('clip_area_strt')
        self.COM(STR)
        return self.STATUS
    # 层名
    def clip_area2(self,layer='',area='profile',inout='inside',contour_cut='yes',margin=2540,feat_types='',ref_layer=''):
        if feat_types:
            feat_types = '\;'.join(feat_types.split('|'))
        else:
            feat_types = 'line\;pad\;surface\;arc\;text'
        if ref_layer:
            STR = 'clip_area_end,layers_mode=layer_name,layer=%s,area=reference,area_type=rectangle,inout=%s,contour_cut=%s,margin=%s,ref_layer=%s,feat_types=%s' \
                  % (layer,inout, contour_cut, margin, ref_layer, feat_types)
        else:
            STR = 'clip_area_end,layers_mode=layer_name,layer=%s,area=%s,area_type=rectangle,inout=%s,contour_cut=%s,margin=%s,feat_types=%s' \
                  % (layer, area, inout, contour_cut, margin, feat_types)
        self.COM('clip_area_strt')
        self.COM(STR)
        return self.STATUS

    # 20210923 zl 拼版(step方法) 默认width为500，需要传height
    # 拼版大小
    def panelSize(self,height,width=500):
        STR = 'panel_size,width=%s,height=%s'% (width,height)
        self.COM(STR)
        return self.STATUS
    # 拼版step
    def sr_tab_add(self,line,step,x=0,y=0,nx=1,ny=1):
        STR = 'sr_tab_add,line=%s,step=%s,x=%s,y=%s,nx=%s,ny=%s' % (line,step,x,y,nx,ny)
        self.COM(STR)
        return self.STATUS
    # 关闭排版sredit窗口
    def sr_close(self):
        STR = 'sredit_close'
        self.COM(STR)
        return self.STATUS
    #################################
    # pcb numbering  20211011 zl
    def stpnum_display(self,name='set',x=0,y=0):
        STR = 'stpnum_display_step,step_name=%s,x=%s,y=%s' % (name,x,y)
        self.COM(STR)
    def stpnum_select(self,name='set',x=0,y=0):
        STR = 'stpnum_select_step,step_name=%s,x=%s,y=%s' % (name,x,y)
        self.COM(STR)
    def stpnum_ins_point(self,mode='pcb_datum',name='set',corner='bot_left',x=0,y=0):
        STR = 'stpnum_insertion_point,stp_ref_mode=%s,corner=%s,step_name=%s,x=%s,y=%s' % (mode,corner,name, x, y)
        self.COM(STR)
    def stpnum_step_params(self,name,method,format):
        STR = 'stpnum_set_step_params,step_name=%s,method=%s,format=%s'%(name,method,format)
        self.COM(STR)
    def stpnum_numbering(self,number_type='flat',del_prev_num='yes',name='set',method='',orientation='fixed',mirror='no',rotate=0,polarity='positive',background='no',
                         background_margin=0,text_type='string',x_size=0,y_size=0,line_width=0.024,hole_size=0,start_number='01',format=''):
        if number_type == 'flat':
            STR = 'stpnum_flat_numbering,'
        else:
            STR = 'stpnum_nested_numbering,'
        STR += 'just_preview=no,del_prev_num=%s,step_name=%s,method=%s,text_orientation=%s,text_mirror=%s,text_rotation=%s,text_polarity=%s,text_background=%s,text_background_margin=%s,\
        text_type=%s,x_size=%s,y_size=%s,line_width=%s,hole_size=%s,start_number=%s,format=%s' \
               % (del_prev_num,name,method,orientation,mirror,rotate,polarity,background,background_margin,text_type,x_size,y_size,line_width,hole_size,start_number,format)
        self.COM(STR)
        return self.STATUS
    ###################################################################################
    def selectSingle(self, x, y, tol=10, operation="select", cyclic="yes"):
        """singal a feat"""

        STR = 'sel_single_feat,operation=%s,x=%s,y=%s,tol=%s,cyclic=%s' % (operation, x, y, tol, cyclic)
        self.COM(STR)

        return self.STATUS

    def selectReverse(self):
        """Reverse Selection"""

        STR = 'sel_reverse'
        self.COM(STR)

        return self.STATUS

    def selectBreak(self):
        STR = 'sel_break'
        self.COM(STR)

        return self.STATUS

    # 20211002 zl profile_to_rout
    def prof_to_rout(self,layer,width=1000):
        STR = 'profile_to_rout,layer=%s,width=%s' % (layer,width)
        self.COM(STR)
        return self.STATUS

    # 20211213 zl 把feature转成孔模式Feature to Drill pattern
    def FeatureToDrillPattern(self,layer,drillsize=0,pitch=0,mode='append',drillsize2=0,pitch2=0,min_rep_diff=0,drill_type='via',outline='no'):
        STR='sel_feat2drill,target_layer=%s,lyr_mode=%s,drill_type=%s,outline_only=%s,drill_size=%s,pitch=%s,drill_size2=%s,pitch2=%s,min_rep_diff=%s' % (layer,mode,drill_type,outline,drillsize,pitch,drillsize2,pitch2,min_rep_diff)
        self.COM(STR)
        return self.STATUS

    # 改变大小size
    def selectResize(self,size=0,corner_ctl='no'):
        STR = 'sel_resize,size=%s,corner_ctl=%s' % (size,corner_ctl)
        self.COM(STR)
        return self.STATUS

    # 转换正负性
    def selectPolarity(self, polarity='positive'):
        STR = 'sel_polarity,polarity=' + str(polarity)
        self.COM(STR)
        return self.STATUS

    # 重复选择的物件 20211115
    def selectRepeat(self,nx=1,ny=1,dx=0,dy=0):
        STR = 'sel_copy_repeat,nx=%s,ny=%s,dx=%s,dy=%s,ref_layer=' % (nx,ny,dx,dy)
        self.COM(STR)

    # 生成profile 20211116
    def selectCreateProf(self):
        self.COM('sel_create_profile')
        return self.STATUS

    # 创建symbol 20240530
    def createSymbol(self, symbol='', x_datum=0, y_datum=0, fill_dx=2.54, fill_dy=2.54):
        self.COM('sel_create_sym,symbol=%s,x_datum=%s,y_datum=%s,delete=no,fill_dx=%s,fill_dy=%s,attach_atr=no,retain_atr=no' % (symbol, x_datum, y_datum, fill_dx, fill_dy))
        return self.STATUS

    # BREAK TO ISL HOLE
    def break_isl_hole(self,islands_layer='',holes_layer=''):
        STR = 'sel_break_isl_hole,islands_layer=%s,holes_layer=%s' % (islands_layer,holes_layer)
        self.COM(STR)
        return self.STATUS

    # 清空层
    def truncate(self,layer):
        STR = 'truncate_layer,layer=' + str(layer)
        self.COM(STR)
        return self.STATUS

     # 更新step 20210929
    def updateStep(self):
        STR = 'update_dependent_step,job='+ self.job.name + ',step=' + self.name
        self.job.COM(STR)
        return self.STATUS

    # # step release/restore
    # def changeStep(self, operation=1):
    #     """changestep -- release 1 /restore 0 """
    #     if operation:
    #         STR = 'change_step_dependency,job=%s,step=%s,operation=release' % (self.job.name,self.name)
    #         self.COM(STR)
    #         return self.STATUS
    #     else:
    #         self.VOF()
    #         STR = 'change_step_dependency,job=%s,step=%s,operation=restore' % (self.job.name,self.name)
    #         self.COM(STR)
    #         self.updateStep()
    #         info = self.DO_INFO('-t step -e %s/%s -d ATTR'%(self.job.name,self.name))
    #         rotatestep = info.get('gATTRval')[16]
    #         angle = info.get('gATTRval')[-2]
    #         # 翻转后旋转可以，旋转后翻转 release直接报内部错误,故不考虑该情况下的release
    #         # 旋转
    #         if rotatestep:
    #             # 取旋转时的mode   0-datum 1-center
    #             modeval = info.get('gATTRval')[18].split()[1]
    #             mode = 'datum' if modeval == '0' else 'center'
    #             self.COM('rotate_step,job=%s,step=%s,rotated_step=%s,angle=%s,mode=%s,units=inch,anchor_x=0,anchor_y=0'
    #                      %(self.job.name,rotatestep,self.name,angle,mode))
    #             return self.STATUS
    #         # 翻转
    #         flipstep = info.get('gATTRval')[11]
    #         if flipstep:
    #                 self.COM('flip_step,job=%s,step=%s,flipped_step=%s,new_layer_suffix=+flip,mode=anchor,board_only=yes'%(self.job.name,flipstep,self.name))
    #                 return self.STATUS
    #         self.VON()

    # 20230728 zl unable obtain parameters after release require passing in
    # step release/restore  operation 1?release:restore      dependent 1 rotate 0flip 2 rotate+flip
    # dependent 1   param   step angle mode(0 datum/ 1 center)
    # dependent 0  param   step
    # dependent 2  param   step angle mode(0 datum/ 1 center)
    # def changeStep(self, operation=1, param=(), dependent = 1):
    #     """changestep -- release 1 /restore 0 """
    #     if operation:
    #         STR = 'change_step_dependency,job=%s,step=%s,operation=release' % (self.job.name,self.name)
    #         self.COM(STR)
    #         return self.STATUS
    #     else:
    #         if not param:
    #             print("please pass in parameters required during restore")
    #             return -1
    #         self.VOF()
    #         STR = 'change_step_dependency,job=%s,step=%s,operation=restore' % (self.job.name,self.name)
    #         self.COM(STR)
    #         self.updateStep()
    #         # 翻转后旋转可以，旋转后翻转 release直接报内部错误,故不考虑该情况下的release
    #         # 旋转
    #         if dependent == 1:
    #             rotatestep = param[0]
    #             angle = param[1]
    #             # 取旋转时的mode   0-datum 1-center
    #             modeval = param[2]
    #             mode = 'datum' if modeval == 0 else 'center'
    #             self.COM('rotate_step,job=%s,step=%s,rotated_step=%s,angle=%s,mode=%s,units=inch,anchor_x=0,anchor_y=0'
    #                      %(self.job.name,rotatestep,self.name,angle,mode))
    #             return self.STATUS
    #         elif dependent == 0:
    #             # 翻转
    #             flipstep = param[0]
    #             if flipstep:
    #                 self.COM(
    #                     'flip_step,job=%s,step=%s,flipped_step=%s,new_layer_suffix=+flip,mode=anchor,board_only=yes' % (
    #                     self.job.name, flipstep, self.name))
    #                 return self.STATUS
    #         else:
    #             rotatestep = param[0]
    #             angle = param[1]
    #             # 取旋转时的mode   0-datum 1-center
    #             modeval = param[2]
    #             mode = 'datum' if modeval == 0 else 'center'
    #             self.COM('rotate_step,job=%s,step=%s,rotated_step=%s,angle=%s,mode=%s,units=inch,anchor_x=0,anchor_y=0'
    #                      % (self.job.name, rotatestep, self.name, angle, mode))
    #             # 翻转
    #             flipstep = param[0]
    #             if flipstep:
    #                     self.COM('flip_step,job=%s,step=%s,flipped_step=%s,new_layer_suffix=+flip,mode=anchor,board_only=yes'%(self.job.name,flipstep,self.name))
    #                     return self.STATUS
    #         self.VON()

    # step release/restore  operation 1?release:restore      dependent 1 rotate 0flip 2 rotate+flip
    def changeStep(self, operation=1):
        """changestep -- release 1 /restore 0 """
        if operation:
            STR = 'change_step_dependency,job=%s,step=%s,operation=release' % (self.job.name,self.name)
            self.COM(STR)
            return self.STATUS
        else:
            STR = 'change_step_dependency,job=%s,step=%s,operation=restore' % (self.job.name,self.name)
            self.COM(STR)
            return self.STATUS


    def selectLineToPad(self):
        STR = 'sel_line2pad'
        self.COM(STR)

        return self.STATUS

    def Contourize(self, accuracy=6.35, break_to_islads="yes", clean_hole_size=76.2, clean_hole_mode="x_and_y"):
        """Contourize surface"""

        STR = 'sel_contourize,accuracy=%s,break_to_islands=%s,clean_hole_size=%s,clean_hole_mode=%s' % (
        accuracy, break_to_islads, clean_hole_size, clean_hole_mode)
        self.COM(STR)
        return self.STATUS

    def surf_outline(self, width=100):
        STR = 'sel_surf2outline,width=%s' % width
        self.COM(STR)
        return self.STATUS

    # 20250620 zl feat2outline
    def feat_outline(self, width=100, offset=0, location='on_edge', polarity='as_feature',keep_original='no',text2limit='no'):
        STR = ('sel_feat2outline,width=%s,location=%s,offset=%s,polarity=%s,keep_original=%s,text2limit=%s'
               % (width, location, offset,polarity, keep_original, text2limit))
        self.COM(STR)
        return self.STATUS

    # 20240313
    # ignore  Symmetric\;Island\;Standard\;Rotated
    def cont2pad(self, match_tol=1, min_size=1, max_size=2540, restriction='', suffix='+++'):
        STR = 'sel_cont2pad,match_tol=%s,restriction=%s,min_size=%s,max_size=%s,suffix=%s' % (match_tol, restriction, min_size, max_size, suffix)
        self.COM(STR)
        return self.STATUS

    #20211028   zl
    # mode: anchor axis
    # oper: rotate\;mirror\;scale\;y_mirror
    # duplicate
    def Transform(self,mode='anchor',oper='',duplicate='no',x_anchor=0,y_anchor=0,angle=0,x_scale=1,y_scale=1,x_offset=0,y_offset=0):
        STR = 'sel_transform,mode=%s,oper=%s,duplicate=%s,x_anchor=%s,y_anchor=%s,angle=%s,' \
              'x_scale=%s,y_scale=%s,x_offset=%s,y_offset=%s'%(mode,oper,duplicate,x_anchor,y_anchor,angle,x_scale,y_scale,x_offset,y_offset)
        self.COM(STR)
        return self.STATUS

    def selectFill(self, min_brush=25.4, type="solid", origin_type="datum", solid_type="fill", std_type="line",
                   use_arcs="yes", symbol="", dx=2.54, dy=2.54, x_off=0, y_off=0, std_angle=45, \
                   std_line_width=254, std_step_dist=1270, std_indent="odd", break_partial="yes", cut_prims="no",
                   outline_draw="no", outline_width=0, outline_invert="no"):
        """Fill Selection"""
        STR = 'fill_params,type=%s,origin_type=%s,solid_type=%s,std_type=%s,min_brush=%s,use_arcs=%s,symbol=%s,dx=%s,dy=%s,x_off=%s,y_off=%s,std_angle=%s,\
               std_line_width=%s,std_step_dist=%s,std_indent=%s,break_partial=%s,cut_prims=%s,outline_draw=%s,outline_width=%s,outline_invert=%s' % \
              (type, origin_type, solid_type, std_type, min_brush, use_arcs, symbol, dx, dy, x_off, y_off, std_angle, std_line_width,
               std_step_dist, std_indent, \
               break_partial, cut_prims, outline_draw, outline_width, outline_invert)
        self.COM(STR)
        STR = 'sel_fill'
        self.COM(STR)
        # STR = 'fill_params,type=solid,origin_type=datum,solid_type=surface,std_type=line,min_brush=254,use_arcs=yes,symbol=,dx=2.54,dy=2.54,std_angle=45,\
        # std_line_width=254,std_step_dist=1270,std_indent=odd,break_partial=yes,cut_prims=no,outline_draw=no,outline_width=0,outline_invert=no'
        # self.COM(STR)

        return self.STATUS

    def selectChange(self, symbol, reset_angle="no"):
        """Change symbol for selection"""
        STR = 'sel_change_sym,symbol = %s,reset_angle = %s' % (symbol, reset_angle)
        self.COM(STR)

        return self.STATUS

    def Flatten(self, source, target):
        """Flatten layer"""
        STR = 'flatten_layer,source_layer=%s,target_layer=%s' % (source, target)
        self.COM(STR)

        return self.STATUS

    def Gerber274xOut(self, layer, path, angle=0, mirror='no', x_scale=1, y_scale=1, positive='positive', line_units='inch', prefix='', suffix='.gbr',
                      break_sr='yes', break_symbols='no', \
                      break_arc='no', scale_mode='all', surface_mode='contour', min_brush=0.25, units='inch', coordinates='absolute', zeroes='none', nf1=3, nf2=5, x_anchor=0, y_anchor=0, wheel=''):
        STR = "output_layer_reset"
        self.COM(STR)
        STR = "output_layer_set,layer=%s,angle=%s,mirror=%s,x_scale=%s,y_scale=%s,comp=0,polarity=%s,setupfile=,setupfiletmp=,\
               line_units=%s,gscl_file=,step_scale=no" % (layer, angle, mirror, x_scale, y_scale, positive, line_units)
        self.COM(STR)
        STR = "output,job=%s,step=%s,format=Gerber274x,dir_path=%s,prefix=%s,suffix=%s,break_sr=%s,break_symbols=%s,\
        break_arc=%s,scale_mode=%s,surface_mode=%s,min_brush=%s,units=%s,coordinates=%s,zeroes=%s,nf1=%s,nf2=%s,\
        x_anchor=%s,y_anchor=%s,wheel=%s,x_offset=0,y_offset=0,line_units=%s,override_online=yes,film_size_cross_scan=0,film_size_along_scan=0,\
        ds_model=RG6500" % (
        self.job.name, self.name, path, prefix, suffix, break_sr, break_symbols, break_arc, scale_mode, surface_mode,
        min_brush, \
        units, coordinates, zeroes, nf1, nf2, x_anchor, y_anchor, wheel, line_units)
        self.COM(STR)
        return self.STATUS

    def Excellon2Out(self, layer, path, angle=0, mirror='no', x_scale=1, y_scale=1, positive='positive', line_units='mm', prefix='', suffix='.drl', break_sr='yes',
                     break_symbols='no', break_arc='no', scale_mode='all', surface_mode='fill', \
                     min_brush=25.4, units='mm', coordinates='absolute', decimal='no', zeroes='trailing', nf1=3, nf2=5, modal='yes', tool_units='mm', optimize='no', iterations=5,
                     reduction_percent=1, cool_spread=0, x_anchor=0, y_anchor=0, canned_text_mode='break'):
        STR = "output_layer_reset"
        self.COM(STR)
        STR = "output_layer_set,layer=%s,angle=%s,mirror=%s,x_scale=%s,y_scale=%s,comp=0,polarity=%s,setupfile=,setupfiletmp=,\
               line_units=%s,gscl_file=,step_scale=no" % (layer, angle, mirror, x_scale, y_scale, positive, line_units)
        self.COM(STR)
        STR = "output,job=%s,step=%s,format=Excellon2,dir_path=%s,prefix=%s,suffix=%s,break_sr=%s,break_symbols=%s,break_arc=%s,scale_mode=%s,\
        surface_mode=%s,min_brush=%s,units=%s,coordinates=%s,decimal=%s,zeroes=%s,nf1=%s,nf2=%s,modal=%s,tool_units=%s,optimize=%s,iterations=%s,\
        reduction_percent=%s,cool_spread=%s,x_anchor=%s,y_anchor=%s,wheel=,x_offset=0,y_offset=0,line_units=%s,override_online=yes,\
        canned_text_mode=%s" % (
        self.job.name, self.name, path, prefix, suffix, break_sr, break_symbols, break_arc, scale_mode, surface_mode,
        min_brush, units, coordinates, \
        decimal, zeroes, nf1, nf2, modal, tool_units, optimize, iterations, reduction_percent, cool_spread, x_anchor, y_anchor, line_units,
        canned_text_mode)
        self.COM(STR)

    def DxfOut(self, layer, path, angle=0, mirror='no', x_scale=1, y_scale=1, positive='positive', line_units='mm', prefix='', suffix='.dxf', break_sr='no',
               break_symbols='yes',break_arc='no', scale_mode='all', surface_mode='contour', min_brush=6.35, units='mm', x_anchor=0, y_anchor=0, x_offset=0, y_offset=0, pads_2circles='no', draft='all', contour_to_hatch='no',
               pad_outline='no', output_files='multiple', file_ver='old'):
        STR = "output_layer_reset"
        self.COM(STR)
        STR = "output_layer_set,layer=%s,angle=%s,mirror=%s,x_scale=%s,y_scale=%s,comp=0,polarity=%s,setupfile=,setupfiletmp=,\
               line_units=%s,gscl_file=,step_scale=no" % (layer, angle, mirror, x_scale, y_scale, positive, line_units)
        self.COM(STR)
        STR = "output,job=%s,step=%s,format=Dxf,dir_path=%s,prefix=%s,suffix=%s,break_sr=%s,break_symbols=%s,\
        break_arc=%s,scale_mode=%s,surface_mode=%s,min_brush=%s,units=%s,x_anchor=%s,y_anchor=%s,x_offset=%s,y_offset=%s,line_units=%s,override_online=yes,\
        pads_2circles=%s,draft=%s,contour_to_hatch=%s,pad_outline=%s,output_files=%s,file_ver=%s" % (
        self.job.name, self.name, path, prefix, suffix, break_sr, break_symbols, \
        break_arc, scale_mode, surface_mode, min_brush, units, x_anchor, y_anchor, x_offset, y_offset,line_units, pads_2circles, draft, contour_to_hatch,
        pad_outline, output_files, file_ver)
        self.COM(STR)

    def PdfOut(self, title, layer_name, mirrored_layers, draw_profile, drawing_per_layer, label_layers, dest_fname,
               paper_size, nx, ny, orient, paper_orient, paper_units, \
               top_margin, bottom_margin, left_margin, right_margin, spacing, auto_tray="no", num_copies="1",
               scale_to="0"):
        STR = "print,title=%s,layer_name=%s,mirrored_layers=%s,draw_profile=%s,drawing_per_layer=%s,label_layers=%s,dest=pdf_file,num_copies=%s,dest_fname=%s,paper_size=%s,\
               scale_to=%s,nx=%s,ny=%s,orient=%s,paper_orient=%s,paper_width=0,paper_height=0,paper_units=%s,auto_tray=%s,top_margin=%s,bottom_margin=%s,left_margin=%s,right_margin=%s,\
               x_spacing=%s,y_spacing=%s,color1=990000,color2=9900,color3=99,color4=990099,color5=999900,color6=9999,color7=0" % (
        title, layer_name, mirrored_layers, draw_profile, \
        drawing_per_layer, label_layers, num_copies, dest_fname, paper_size, scale_to, nx, ny, orient, paper_orient,
        paper_units, auto_tray, top_margin, bottom_margin, left_margin, right_margin, \
        spacing, spacing)
        self.COM(STR)

    def AutoDrillManager(self, layer, machine, path, name, angle, mirror, xscale, yscale):

        STR = "ncset_cur,job=%s,step=%s,layer=%s,ncset=1" % (self.job.name, self.name, layer)
        self.COM(STR)
        STR = "ncd_set_machine,machine=%s,thickness=0" % (machine)
        self.COM(STR)
        STR = "ncd_register,angle=%s,mirror=%s,xoff=1,yoff=1,version=1,xorigin=1,yorigin=1,xscale=%s,yscale=%s,xscale_o=0,yscale_o=0" % (
        angle, mirror, xscale, yscale)
        self.COM(STR)
        STR = "ncd_cre_drill"
        self.COM(STR)
        STR = "ncd_ncf_export,stage=1,split=1,dir=%s,name=%s" % (path, name)
        self.COM(STR)
        STR = "ncset_delete,name=1"
        self.COM(STR)

    def AutoRoutManager(self, layer, machine, path, name, angle, mirror, xscale, yscale):
        STR = "ncrset_cur,job=%s,step=%s,layer=%s,ncset=1" % (self.job.name, self.name, layer)
        self.COM(STR)
        STR = "ncr_set_machine,machine=%s,thickness=0" % (machine)
        self.COM(STR)
        STR = "ncr_register,angle=%s,mirror=%s,xoff=1,yoff=1,version=1,xorigin=1,yorigin=1,xscale=%s,yscale=%s,xscale_o=0,yscale_o=0" % (
        angle, mirror, xscale, yscale)
        self.COM(STR)
        STR = "ncr_cre_rout"
        self.COM(STR)
        STR = "ncr_ncf_export,stage=1,split=1,dir=%s,name=%s" % (path, name)
        self.COM(STR)
        STR = "ncrset_delete,name=1"
        self.COM(STR)
    # This class defines commands which will be invoked on a matrix


class MatrixCmds:
    """Commands that are performed on a matrix through the matrix class"""

    def addCol(self, name, ColNumber=1):
        """ Add a Col to the job.
                 name - name of new Col
                 ColNumber - Number of Col"""
        STR = 'matrix_insert_col,job=%s,matrix=matrix,col=%s' % (self.job.name, ColNumber)
        self.COM(STR)
        STR = 'matrix_add_step,job=%s,matrix=matrix,step=%s,col=%s' % (self.job.name, name, ColNumber)
        self.COM(STR)
        self.group = self.COMANS

        # Re-populate the steps list
        self.job.getInfo()
        self.job.getSteps()

        return self.STATUS

    def removeCol(self, ColNumber=1):
        """ Remove a Col from the job.
                ColNumber - Number of Col to delete"""

        STR = 'matrix_delete_col,job=%s,matrix=matrix,col=%s' % (self.job.name, ColNumber)
        self.COM(STR)
        self.group = self.COMANS

        # Re-populate the steps list
        self.job.getInfo()
        self.job.getSteps()

        return self.STATUS

    def addLayer(self, name, index, context='misc', type='signal', polarity='positive'):
        """Add a row /layer to the matrix
               name - name of layer
               index - row number to use
               context - context of layer (default to misc)
               type - type of layer (default to signal)
               polarity - polarity of layer (default to positive)"""

        STR = 'matrix_insert_row,job=' + self.job.name + ',matrix=matrix,row=' + str(index)
        self.COM(STR)
        STR = 'matrix_add_layer,job=%s,matrix=matrix,row=' % (self.job.name)
        STR = STR + str(index) + ',layer=' + name + ',context=' + context
        STR = STR + ',type=' + type + ',polarity=' + polarity
        self.COM(STR)
        self.group = self.COMANS

        # Re-populate the steps list
        self.job.getInfo()
        self.job.getSteps()

        return self.STATUS

    def removeLayer(self, lay):
        """ Remove a layer from the matrix
          lay - name of layer"""

        STR = 'matrix_delete_row,job=%s,type=step,name=%s' % (self.name, lay)
        self.COM(STR)
        self.group = self.COMANS

        # Re-populate the steps list
        self.getInfo()
        self.getSteps()

        return self.STATUS

    # 20211002 zl
    def refresh(self):
        STR = 'matrix_refresh,job=%s,matrix=matrix' % self.job.name
        self.COM(STR)
        return self.STATUS

    # New Row applies only for those layers in a board context - replace indicates overwrite
    def copyRow(self, name, newName, context='misc', newRow=3, overwrite=0, ):
        """Copy a row from one location to another in the matrix.  If newRow not indicated, copies
        to the end of the matrix.
            name - name of row
            newName - name of new row
            context - context of new row (default to misc)
            newRow - number of new row if you need it to be in a certain place
            overwrite - overwrite row by same name as newName with this copy (defaults to 0)"""

        # get dest row
        # print "Row: " + name + " newRow: " + newName + " Context: " + context
        self.getInfo()
        dest_row = int(self.info['gNUM_LAYERS']) + 1

        if (int(self.getRow(newName))) and (overwrite):
            self.job.COM(
                'matrix_delete_row,job=' + self.job.name + ',row=' + str(self.getRow(newName)) + ',matrix=matrix')
            dest_row = dest_row - 1

        row = self.getRow(name)
        self.job.COM(
            'matrix_copy_row,job=' + self.job.name + ',row=' + str(row) + ',matrix=matrix,ins_row=' + str(dest_row))
        self.job.COM(
            'matrix_rename_layer,job=' + self.job.name + ',matrix=matrix,layer=' + name + '+1,new_name=' + newName)
        self.job.COM(
            'matrix_layer_context,job=' + self.job.name + ',matrix=matrix,layer=' + newName + ',context=' + context)
        if context == 'board':
            self.getInfo()
            row = self.getRow(newName)
            self.job.COM(
                'matrix_move_row,job=' + self.job.name + ',row=' + str(row) + ',matrix=matrix,ins_row=' + str(newRow))
        self.getInfo()
        self.job.getInfo()
        self.job.getSteps()
        return self.job.STATUS

    def deleteRow(self, name):
        """ Delete a row from the matrix
               name - name of row"""

        row = self.getRow(name)
        print("This is row: " + name + " and the number " + str(row))
        if int(row) > 0:
            self.job.COM('matrix_delete_row,job=' + self.job.name + ',row=' + str(row) + ',matrix=matrix')
            self.getInfo()
            for step in list(self.job.steps.keys()):
                self.job.steps[step].getInfo()
            return self.job.STATUS
        else:
            return 10

    def modifyRow(self, currentName, row=0, name='', context='', type='', polarity=''):
        """ Change the attributes of a row.  You only need assign values for the things you want
        to change.  Be sure to use the key value pair in the parameters list.
               currentName - name of current row to modify.
               (optional below)
               row - new row (defaults to leaving it in same place (indicated by 0)
               name - new name
               context - new context
               type - new type
               polarity - new polarity"""

        status = 0
        # Get current row
        curRow = self.getRow(currentName)
        # Change row if desired
        if row > 0:
            self.job.COM(
                'matrix_move_row,job=' + self.job.name + ',matrix=matrix,row=' + str(curRow) + ',ins_row=' + str(row))
            status = status + int(self.job.STATUS)
            # Change context if desired
        if not (context == ''):
            self.job.COM(
                'matrix_layer_context,job=' + self.job.name + ',matrix=matrix,layer=' + currentName + ',context=' + context)
            status = status + int(self.job.STATUS)
        if not (type == ''):
            self.job.COM(
                'matrix_layer_type,job=' + self.job.name + ',matrix=matrix,layer=' + currentName + ',type=' + type)
            status = status + int(self.job.STATUS)
        if not (polarity == ''):
            self.job.COM(
                'matrix_layer_polar,job=' + self.job.name + ',matrix=matrix,layer=' + currentName + ',polarity=' + polarity)
            status = status + int(self.job.STATUS)
        # Lastly change the name!
        if not (name == ''):
            self.job.COM(
                'matrix_rename_layer,job=' + self.job.name + ',matrix=matrix' + ',layer=' + currentName + ',new_name=' + name)
            status = status + int(self.job.STATUS)
        for step in list(self.job.steps.keys()):
            self.job.steps[step].getInfo()
            # self.job.steps[step].getLayers()
        return status
    def returnRows(self, context='', type='', polarity='', side='', names=1, ):
        """ Return all the rows matching certain criteria. Defaults to returning names
            can use '|' to separate multiple specs for each type (or)
               context (optional) - return with certain context
               type (optional) - return with certain type
               polarity (optional) - return with certain polarity
               side (optional) - return with certain side (top or bottom)
               names (optional) - defaults to 1, meaning names are returned. 0
                          means row numbers are returned"""

        # Parse all the ors
        contextList = context.split('|')
        # print contextList
        typeList = type.split('|')
        # print typeList
        polarityList = polarity.split('|')
        # print polarityList
        sideList = side.split('|')
        # print sideList

        self.getInfo()
        rowList = []
        nameList = []
        for x in range(len(self.info['gROWname'])):
            if not len(self.info['gROWname'][x]): continue
            r_row = self.info['gROWrow'][x]
            r_name = self.info['gROWname'][x]
            r_context = self.info['gROWcontext'][x]
            r_type = self.info['gROWtype'][x]
            r_layer_type = self.info['gROWlayer_type'][x]
            r_polarity = self.info['gROWpolarity'][x]
            r_side = self.info['gROWside'][x]
            # r_drl_start  = self.info['gROWdrl_start'][x]
            # r_drl_end    = self.info['gROWdrl_end'][x]
            # r_foil_side  = self.info['gROWfoil_side'][x]
            # r_sheet_side = self.info['gROWsheet_side'][x]

            # print(str(r_row) + " " + r_name + " " + r_context + " " + r_type + " " + r_layer_type + " " + r_polarity + " " + r_side)

            if not (r_type == 'layer'):
                continue

            if (context != ''):
                # print "entercontext"
                contextFound = 0
                for l_context in contextList:
                    if (l_context == r_context):
                        contextFound = 1
                if not contextFound:
                    continue

            if (type != ''):
                # print "entertype"
                typeFound = 0
                for l_type in typeList:
                    if (l_type == r_layer_type):
                        typeFound = 1
                if not typeFound:
                    continue

            if (polarity != ''):
                # print "enterpol"
                polarityFound = 0
                for l_polarity in polarityList:
                    if (l_polarity == r_polarity):
                        polarityFound = 1
                if not polarityFound:
                    continue

            if (side != ''):
                # print "enterside"
                sideFound = 0
                for l_side in sideList:
                    if (l_side == r_side):
                        sideFound = 1
                if not sideFound:
                    continue

            # print "Reached  Append    "
            rowList.append(int(r_row))
            nameList.append(r_name)

        if names:
            return nameList
        else:
            return rowList
    # 钻孔层贯穿层设置
    def setDrillThrough(self,layer,start,end):
        STR = 'matrix_layer_drill,job=%s,matrix=matrix,layer=%s,start=%s,end=%s' % (self.job.name,layer,start,end)
        self.job.COM(STR)
        return self.job.STATUS

class LayerCmds:
    """Class containing layer commands - same as using right mouse button in Graphic editor.
    These methods are run on layer objects, so there is no need to indicate which layer you
    are working on"""

    def display(self, num=1):
        """Display layer in the editor
               num - color number (defaults to 1)"""
        STR = 'display_layer,name=' + self.name + ',display=yes,number=' + str(num)
        self.job.COM(STR)
        return self.job.STATUS

    def work(self):
        """Changes this to the work layer"""

        STR = 'work_layer,name=' + self.name
        self.job.COM(STR)

    def setGenesisAttr(self, name, value):
        """ Set layer attribute to a value, update Python attribute value.
                name - string containing name of attribute
                value - string/int/float containing value of attribute
                  NOTE:  Value may be cast to string upon retreival"""

        STR = 'set_attribute,type=layer,job=%s,name1=%s,name2=%s,name3=,attribute=%s,value=%s,units=inch' % (
        self.job.name, self.step.name, self.name, name, str(value))
        self.job.COM(STR)

        setattr(self, name, value)

        return self.STATUS

    def affect(self):
        """Sets this layer to be affected"""
        STR = 'affected_layer,name=' + self.name + ',mode=single,affected=yes'
        self.job.COM(STR)

    def unaffect(self):
        """Unaffects the layer"""
        STR = 'affected_layer,name=' + self.name + ',mode=single,affected=no'
        self.job.COM(STR)

    def copy(self, dest_lay, mode='replace'):
        """copies this layer to destination layer
               dest_lay - name of destination layer
               mode - replace or append defaults to replace"""

        STR = 'copy_layer,source_job=%s,source_step=%s,source_layer=%s,dest=layer_name,dest_layer=%s,mode=%s'
        STR = STR % (self.job.name, self.step.name, self.name, dest_lay, mode)
        self.job.COM(STR)
        self.step.getInfo()
        self.step.getLayers()

    def featOut(self, fileName='', units='inch'):
        """ Takes all the features on the layer, parses them, and returns them in a
        dictionary.  See Features.py module.
               fileName (optional) - name with path of filename if you don't want to use the
                         default temp files"""

        if (fileName == ''):
            fileName = self.job.tmpfile
        print(fileName)

        STR = 'info,out_file=' + fileName + ',write_mode=replace,args=-t layer -e ' + self.job.name + '/' + self.step.name + '/' + self.name + ' -d FEATURES -o break_sr,units=%s' % units
        self.job.COM(STR)
        lineList = open(fileName, 'r').readlines()
        os.unlink(fileName)
        dict = self.job.parseFeatureInfo(lineList)
        return dict

    def featSelOut(self, fileName='', units='inch'):
        """Takes all the Selected features, parses them, and returns them in a
        dictionary.  See Features.py module.
            filename - see featOut()"""

        if (fileName == ''):
            print("Empty filename")
            fileName = self.job.tmpfile
        print("Filename" + str(fileName))

        STR = 'info,out_file=' + fileName + ',write_mode=replace,args=-t layer -e ' + self.job.name + '/' + self.step.name + '/' + self.name + ' -d FEATURES -o select, units=' + units
        self.job.COM(STR)
        lineList = open(fileName, 'r').readlines()
        print(lineList)
        os.unlink(fileName)
        dict = self.job.parseFeatureInfo(lineList)
        return dict

    def featout_dic_Index(self, fileName='', units="inch", options="feat_index+break_sr"):
        """Takes all the Selected features, parses them, and returns them in a
        dictionary.  See Features.py module.
            filename - see featOut()"""

        if (fileName == ''):
            # print "Empty filename"
            fileName = self.job.tmpfile
        # print "Filename" + str(fileName)

        STR = 'info,out_file=' + fileName + ',write_mode=replace,units=%s,args=-t layer -e ' % units + self.job.name + \
              '/' + self.step.name + '/' + self.name + ' -d FEATURES -o ' + options
        self.job.COM(STR)
        lineList = open(fileName, 'r').readlines()
        os.unlink(fileName)
        dic_feat_index = {}
        new_lineList = [lineList[0]]
        for line in lineList:
            if not line.strip(): continue
            if "#OB" in line or \
                    "#OS" in line or \
                    "#OE" in line:
                continue
            # ss = string.split(line)
            # if ss[0][1:].strip():
            match = re.search("\d+", line)
            if match:
                print(line)
                key = "#" + line.split("#")[2].strip()
                # dic_feat_index[" ".join(ss[1:])] = ss[0][1:].strip()
                # new_lineList.append(" ".join(ss[1:]))
                dic_feat_index[key] = match.group(0)
                new_lineList.append(key)

        dict = self.job.parseFeatureInfo(new_lineList, dic_feat_index)
        return dict

    def histogram(self):
        """Returns a dictionary of histogram information on the layer.  Returns key value pairs of
        all the histogram information."""
        STR = ' -t layer -e %s/%s/%s -d SYMS_HIST' % (self.job.name, self.step.name, self.name)
        dict = self.step.DO_INFO(STR)
        return dict

    def polarity(self):
        """ Returns the polarity of the layer"""

        STR = ' -t layer -e %s/%s/%s -d POLARITY' % (self.job.name, self.step.name, self.name)
        pol = self.step.DO_INFO(STR)

        return pol['gPOLARITY']
