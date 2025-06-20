#!/bin/env python

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


# Import standard Python modules
import string, os, re


# Identify yourself!
# print "Using genCommands.py Rev " + __version__

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
            print
            "Job already open, not opening"
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

        self.COM('display_layer,name=' + lay + ',display=' + display + ',number=' + `num`)
        if work:
            self.COM('work_layer,name=' + lay)

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

    # Affected by filter
    def affectFilter(self, filter):
        """ Affect by filter in Graphic Editor
                filter - string containing filter configuration"""

        self.COM('affected_filter,filter=' + filter)
        self.COM('get_affect_layer')
        return string.split(self.COMANS)

    def zoomHome(self):
        """ Zoom out to profile view/home"""
        self.COM('zoom_home')

    ### Filter setup Methods ###
    # ...............................#
    def resetFilter(self):
        """Reset the selection filter"""

        self.COM('filter_reset,filter_name=popup')

    def setAttrFilter(self, attr, condition="yes"):
        """Set an attribute in the attribute filter
                attr - name of attribute"""

        self.COM('filter_atr_set,filter_name=popup,condition=%s,attribute=%s' % (condition, attr))

    def setSymbolFilter(self, syms):
        """Set a symbol on which to filter
                syms - symbol name"""

        self.COM('filter_set,filter_name=popup,update_popup=no,include_syms=' + syms)

    def filter_set(self, feat_types='pad;line;arc;text;surface',
                   polarity='positive;negative', exclude_syms='',
                   include_syms='', reset="no"):
        """set filter"""
        if reset == "yes":
            self.resetFilter()

        self.COM('filter_set,filter_name=popup,\
		update_popup=no,feat_types=%s,\
		polarity=%s,exclude_syms=%s,include_syms=%s'
                 % (feat_types, polarity, exclude_syms, include_syms))

    # ATTRIBUTE METHODS

    def resetAttr(self):
        """Reset the attribute List"""

        self.COM('cur_atr_reset')

    def addAttr(self, attr, attrVal='', valType='int', change_attr=""):
        """Add attribute to attribute list
            valType determines what attrVal should be
            valType : default is 'int', also 'float', 'text', 'option'"""

        if (valType == ''):
            self.COM('cur_atr_set,attribute=' + attr)
        else:
            self.COM('cur_atr_set,attribute=' + attr + ',' + valType + '=' + str(attrVal))

        if change_attr:
            self.COM("sel_change_atr,mode=add")

    ### SELECTION RELATED METHODS ###
    # ...............................#
    def selectNone(self):
        """Unselect all features."""

        self.COM('sel_clear_feat')

    def selectAll(self):
        """Select all features on affected layers, (applying popup filter)
               returns number selected"""

        self.COM('filter_area_strt')
        self.COM('''filter_area_end,layer=,filter_name=popup,operation=select,
		area_type=none,inside_area=no,intersect_area=no,lines_only=no,
		ovals_only=no,min_len=0,max_len=0,min_angle=0,max_angle=0
		''')
        self.COM("get_select_count")
        try:
            return string.atoi(self.COMANS)
        except:
            return 0

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
        self.COM("get_select_count")
        return string.atoi(self.COMANS)

    def selectRectangle(self, xs, ys, xe, ye, intersect='no', reset=0):
        """Select all features in a rectangle
               xs, ys, xe, ye - start and end x,y coordinates
               intersect - if 'yes' selects symbols intersected by rectangle but not fully inside
                            defaults to 'no'
               reset - see selectSymbol()"""

        if reset:
            self.resetFilter()
        self.COM('filter_area_strt')
        self.COM('filter_area_xy,x=' + `xs` + ',y=' + `ys`)
        self.COM('filter_area_xy,x=' + `xe` + ',y=' + `ye`)
        self.COM(
            'filter_area_end,layer=,filter_name=popup,operation=select,area_type=rectangle,inside_area=yes,intersect_area=' + intersect)
        self.COM("get_select_count")
        return string.atoi(self.COMANS)

    def refSelectFilter(self, refLay, include_syms='', exclude_syms='', mode='touch', reset=0,
                        f_types="line\;pad\;surface\;arc\;text", polarity="positive\;negative"):
        """Select by reference, using filter (so you better reset the filter if you need to!)
               refLay - reference layer
               include_syms (optional) - symbols to include in selection
               exclude_syms (optional) - symbols to exclude from selection
               mode (optional) - defaults to 'touch'
               reset (optional) - defaults to 0 (0 = DON'T reset filter, 1 = reset filter)"""

        if reset:
            self.resetFilter()
        STR = '''sel_ref_feat,layers=%s,use=filter,mode=%s,f_types=%s,polarity=%s,include_syms=%s,exclude_syms=%s'''
        STR = STR % (refLay, mode, f_types, polarity, include_syms, exclude_syms)
        self.COM(STR)
        self.COM("get_select_count")
        return string.atoi(self.COMANS)

    def featureSelected(self):
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

    def selectDelete(self):
        """ Delete Selected features."""
        self.COM('sel_delete')

    def changeSymbol(self, symbolname):
        self.COM('sel_change_sym,symbol=%s,reset_angle=no' % symbolname)
        return self.STATUS

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

        self.COM('sel_buffer_paste,x_datum=' + `x` + ',y_datum=' + `y`)

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

    def createLayer(self, name, context='misc', laytype='document', polarity='positive', ins_layer="", location=""):
        """ Create a blank layer.
               name - new layer name
               context - (defaults to 'misc') context of layer (board,misc)
               laytype - (defaults to 'document) type of layer (document, signal, etc...)
               polarity - (defaults to positive) polarity of layer (positive, negative)"""

        STR = 'create_layer,layer=%s,context=%s,type=%s,polarity=%s,ins_layer=%s' % (
            name, context, laytype, polarity, ins_layer)
        if location:
            STR = 'create_layer,layer=%s,context=%s,type=%s,polarity=%s,ins_layer=%s,location=%s' % (
                name, context, laytype, polarity, ins_layer, location)
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
               yscale=1, attributes='no', direction=""):
        """Add a pad to the selected layers in this step.  The arguments are self explanatory.
        All are optional except x, y, and symbol. NOTE: This is precise only to sixth decimal
        Also remember that dx and dy are in mils(microns)"""

        nx = str(int(nx))
        ny = str(int(ny))
        angle = str(int(angle))
        # array = [x, y, symbol, polarity, angle, mirror, nx, ny, dx, dy, xscale, yscale]
        if direction:
            STR = "add_pad,attributes=%s,x=%.6f,y=%.6f,symbol=%s,polarity=%s,angle=%s,direction=%s,mirror=%s,nx=%s,ny=%s,dx=%.3f,dy=%.3f,xscale=%.4f,yscale=%.4f" % (
                attributes, x, y, symbol, polarity, angle, direction, mirror, nx, ny, dx, dy, xscale, yscale)
        else:
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

    def addArc(self, xs, ys, xe, ye, xc, yc, symbol, direction, polarity='positive', attributes='no'):
        """Add an arc to the selected layers in this step.  xs/ys - start, xe/ye - end, xc/yc, center
        direction is 'CW' or 'CCW'.  All are mandatory except polarity, which defaults to pos, and
        attributes, defaulting to no.  NOTE: This is precise only to sixth decimal"""

        STR = "add_arc,attributes=%s,xs=%.6f,ys=%.6f,xe=%.6f,ye=%.6f,xc=%.6f,yc=%.6f,symbol=%s,polarity=%s,direction=%s" % (
        attributes, xs, ys, xe, ye, xc, yc, symbol, polarity, direction)
        self.COM(STR)

        return self.STATUS

    def addText(self, x, y, text, xSize, ySize, width, mirror='no', angle=0, polarity='positive', attributes='no',
                fontname='standard', direction=None):
        """Add text to the selected layers in this step.  x/y - text bottomleft corner (bottomright if mirror,
        xSize, ySize is size in mil of text, width is line width in mil, mirror defaults to no, angle defaults to 0
        but can be 0,90,180,270 -polarity defaults to positive, attributes defaults to no.
        NOTE: This is precise only to sixth decimal"""

        if "canned" in fontname:
            STR = "add_text,attributes=%s,type=canned_text,x=%.6f,y=%.6f,text=%s,x_size=%.3f,y_size=%.3f,w_factor=%.2f,polarity=%s,angle=%s,mirror=%s,fontname=%s,ver=1" % (
                attributes, x, y, text, xSize, ySize, width, polarity, angle, mirror, fontname)
        else:
            STR = "add_text,attributes=%s,type=string,x=%.6f,y=%.6f,text=%s,x_size=%.3f,y_size=%.3f,w_factor=%.2f,polarity=%s,angle=%s,mirror=%s,fontname=%s,ver=1" % (
                attributes, x, y, text, xSize, ySize, width, polarity, angle, mirror, fontname)
        if direction is not None:
            STR += ",direction={0}".format(direction)

        self.COM(STR)

        return self.STATUS

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

    def clip_rectangle(self, xs, ys, xe, ye,
                       inout="inside", feat_types="line\;pad\;surface\;arc\;text",
                       area="manual", ):
        self.COM("clip_area_strt")
        self.COM("clip_area_xy,x=%s,y=%s" % (xs, ys))
        self.COM("clip_area_xy,x=%s,y=%s" % (xe, ye))
        self.COM("clip_area_end,layers_mode=affected_layers,"
                 "layer=,area=%s,area_type=rectangle,inout=%s,"
                 "contour_cut=no,margin=0,feat_types=%s" % (area, inout, feat_types))

    # ROUT EDITOR COMMANDS
    def addRoutChain(self, layer, size, compensation, feed, flag=0, speed=0, first=0, change_direction=-1):
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
            print
            "Status: " + str(self.STATUS)

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

    def contourize(self, units="mm", accuracy=None):
        if units == "mm":
            STR = "sel_contourize,accuracy=%s,break_to_islands=yes,clean_hole_size=76.2,clean_hole_mode=x_and_y"
            STR = STR % accuracy if accuracy is not None else STR % 6.35
        else:
            STR = "sel_contourize,accuracy=%s,break_to_islands=yes,clean_hole_size=3,clean_hole_mode=x_and_y"
            STR = STR % accuracy if accuracy is not None else STR % 0.1

        self.COM(STR)

        return self.STATUS

    def moveSel(self, layer, invert="no", dx=0, dy=0, size=0, x_anchor=0, y_anchor=0, rotation=0, mirror="none"):
        STR = "sel_move_other,target_layer=%s,invert=%s,\
		dx=%s,dy=%s,size=%s,x_anchor=%s,y_anchor=%s,\
		rotation=%s,mirror=%s" % (layer, invert, dx, dy, size, x_anchor, y_anchor, rotation, mirror)

        self.COM(STR)

        return self.STATUS

    def flatten_layer(self, layer, destlayer):
        STR = "flatten_layer,source_layer=%s,target_layer=%s" % (layer, destlayer)
        self.COM(STR)

        return self.STATUS

    def reset_fill_params(self, fill_type="surface"):
        self.COM("fill_params,type=solid,origin_type=datum,solid_type=%s,min_brush=0.254,\
		    use_arcs=yes,symbol=,dx=2.54,dy=2.54,break_partial=yes,cut_prims=no,outline_draw=no,\
		    outline_width=0,outline_invert=no" % fill_type)
        return self.STATUS

    def selectFeatureIndex(self, layer, index):
        self.COM("sel_layer_feat,operation=select,layer={0},index={1}".format(layer, index))
        return self.STATUS


# This class defines commands which will be invoked on a matrix
class MatrixCmds:
    """Commands that are performed on a matrix through the matrix class"""

    def addLayer(self, name, index, context='board', type='signal', polarity='positive'):
        """Add a row /layer to the matrix
               name - name of layer
               index - row number to use
               context - context of layer (default to board)
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
        print
        "This is row: " + name + " and the number " + str(row)
        if int(row) > 0:
            self.job.COM('matrix_delete_row,job=' + self.job.name + ',row=' + str(row) + ',matrix=matrix')
            self.getInfo()
            for step in self.job.steps.keys():
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
        for step in self.job.steps.keys():
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

        # self.getInfo()
        rowList = []
        nameList = []
        for x in xrange(len(self.info['gROWname'])):
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

            # print str(r_row) + " " + r_name + " " + r_context + " " + r_type + " " + r_layer_type + " " + r_polarity + " " + r_side

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

            # print "Reached  Append	"
            rowList.append(int(r_row))
            nameList.append(r_name)

        if names:
            return nameList
        else:
            return rowList


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

    def featOut(self, fileName='', units="inch"):
        """ Takes all the features on the layer, parses them, and returns them in a
        dictionary.  See Features.py module.
               fileName (optional) - name with path of filename if you don't want to use the
                                     default temp files"""

        if (fileName == ''):
            fileName = self.job.tmpfile
        # print fileName

        STR = 'info,out_file=' + fileName + ',write_mode=replace,units=%s,args=-t layer -e ' % units + self.job.name + '/' + self.step.name + '/' + self.name + ' -d FEATURES -o break_sr'
        self.job.COM(STR)
        lineList = open(fileName, 'r').readlines()
        os.unlink(fileName)
        dict = self.job.parseFeatureInfo(lineList)
        return dict

    def featSelOut(self, fileName='', units="inch"):
        """Takes all the Selected features, parses them, and returns them in a
        dictionary.  See Features.py module.
            filename - see featOut()"""

        if (fileName == ''):
            print
            "Empty filename"
            fileName = self.job.tmpfile
        # print "Filename" + str(fileName)

        STR = 'info,out_file=' + fileName + ',write_mode=replace,units=%s,args=-t layer -e ' % units + self.job.name + '/' + self.step.name + '/' + self.name + ' -d FEATURES -o select'
        self.job.COM(STR)
        lineList = open(fileName, 'r').readlines()
        os.unlink(fileName)
        dict = self.job.parseFeatureInfo(lineList)
        return dict

    def featCurrent_LayerOut(self, fileName='', units="inch"):
        """Takes all the Selected features, parses them, and returns them in a
        dictionary.  See Features.py module.
            filename - see featOut()"""

        if (fileName == ''):
            print
            "Empty filename"
            fileName = self.job.tmpfile
        # print "Filename" + str(fileName)

        STR = 'info,out_file=' + fileName + ',write_mode=replace,units=%s,args=-t layer -e ' % units + \
              self.job.name + '/' + self.step.name + '/' + self.name + ' -d FEATURES'
        self.job.COM(STR)
        lineList = open(fileName, 'r').readlines()
        os.unlink(fileName)
        dict = self.job.parseFeatureInfo(lineList)
        return dict

    def featSelIndex(self, fileName=''):
        """Takes all the Selected features, parses them, and returns them in a
        dictionary.  See Features.py module.
            filename - see featOut()"""

        if (fileName == ''):
            print
            "Empty filename"
            fileName = self.job.tmpfile
        # print "Filename" + str(fileName)

        STR = 'info,out_file=' + fileName + ',write_mode=replace,args=-t layer -e ' + self.job.name + '/' + self.step.name + '/' + self.name + ' -d FEATURES -o feat_index+select'
        self.job.COM(STR)
        lineList = open(fileName, 'r').readlines()
        os.unlink(fileName)
        del lineList[0]
        listIndex = []
        for line in lineList:
            if not line.strip(): continue
            if "#OB" in line or \
                    "#OS" in line or \
                    "#OE" in line or \
                    "#OC" in line:
                continue
            # ss = string.split(line)
            # if ss[0][1:].strip():
            match = re.search("\d+", line)
            if match:
                # listIndex.append(ss[0][1:])
                listIndex.append(match.group(0))
        return listIndex

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
