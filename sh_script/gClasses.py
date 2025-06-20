#!/bin/env python
# -*- coding: utf-8 -*-
"""Modules for joining Genesis 2000 scripting and the Python scripting language.

This module has several companion modules.  These companion modules provide added
functionality over and above the basic Genesis commands.  This module holds several
classes used to abstract the interface with Genesis 2000, making scripting in 
Python faster and easier."""

__author__ = "Mike J. Hopkins"
__date__ = "18 August 2004"
__version__ = "$Revision: 1.4.1 $"
__credits__ = """ Daniel R. Gowans, for contributions to content.
Frontline PCB, for an excellent scripting interface to Genesis 2000"""

# NEED: genCommands.py and genFeatures.py

# drgowans - 8/21/2003 - modified significantly in rev 1.2 to change the method
# of subClassing from instancing helper classes to directly subclassing them.
# Hopefully this will reduce the code size and make method calling more straightforward,
# as well as removing the need for the backward compatible wrapper modules.

# Import Standard Python Modules
import os
import sys
import string
import time
import re
import math

if os.environ.get("JOB") == "genesislib":
    sys.exit()

import errorException

# import package specific stuff
import gCommands
import gFeatures

# Identify
# print "Using genClasses.py Rev " + __version__

from gCommands import *
from gFeatures import *


class Genesis:
    """This class defines the low-level interface methods for use with Genesis.
       It serves as a base-class for the higher-level objects.  It defines
       methods to interface with Genesis itself with the methods Frontline has
       provided."""

    colors = {
        'rgb': {
            'signal': (252, 198, 55),
            'mixed': (242, 224, 134),
            'power_ground': (219, 173, 0),
            'silk_screen': (255, 255, 255),
            'solder_mask': (0, 165, 124),
            'solder_paste': (255, 255, 206),
            'drill': (155, 180, 191),
            'rout': (216, 216, 216),
            'document': (155, 219, 219),
        },
        'hex': {
            'signal': 'FCC64D',
            'mixed': 'F2E086',
            'power_ground': 'DBAD00',
            'silk_screen': 'FFFFFF',
            'solder_mask': '00A57C',
            'solder_paste': 'FFFFCE',
            'drill': '9BB4BF',
            'rout': 'D8D8D8',
            'document': '9BDBDB',
        }
    }

    def __init__(self):
        """ Initialize method, called when object is instantiated (created)"""

        self.prefix = '@%#%@'
        self.blank()
        self.normalize()

        # Set up tmp files; must be unique to this instance,
        #   to allow more than one tmpfile to exist concurrently
        self.pid = os.getpid()
        tmp = 'gen_' + `self.pid` + '.' + `time.time()`
        if os.environ.has_key('GENESIS_TMP'):
            self.tmpfile = os.path.join(os.environ['GENESIS_TMP'], tmp)
            self.tmpdir = os.environ['GENESIS_TMP']
        else:
            self.tmpfile = os.path.join('/tmp', tmp)
            self.tmpdir = '/tmp'

    def __del__(self):
        """ Called when class is cleaned up by python"""

        if getattr(self, "tmpfile", None) and os.path.isfile(self.tmpfile):
            res = os.unlink(self.tmpfile)
            if res: self.error('Error deleting tmpfile', res)

    def _deleteAttribute(self, attr):
        """Method for generically deleting an attribute - makes sure attribute exists first
            attr - string containing the attribute to be deleted"""

        if hasattr(self, attr):
            delattr(self, attr)

    def normalize(self):
        """Normalize the path to GENESIS_EDIR, and make sure the environment is set"""

        if sys.platform == "win32":
            if os.environ.get("INCAM_PRODUCT"):
                self.edir = os.path.join(os.environ.get("INCAM_PRODUCT"), "bin")
                return 0

            if not os.environ.has_key('GENESIS_DIR'):
                self.error('GENESIS_DIR not set', 1)
            self.gendir = os.environ['GENESIS_DIR']
            if not os.environ.has_key('GENESIS_EDIR'):
                self.error('GENESIS_EDIR not set', 1)
            self.edir = os.environ['GENESIS_EDIR']
            if not os.path.isdir(self.edir):
                self.edir = os.path.join(self.gendir, self.edir)
            if not os.path.isdir(self.edir):
                self.error('Cannot normalize GENESIS_EDIR', 1)
        else:
            # if os.environ.get("INCAM_TMP", None):
            if os.path.exists("/incam2"):
                self.edir = '/incam2/release/bin'
            else:
                self.edir = '/incam/release/bin'
            # else:
            # self.edir = "/genesis/e100"
            if os.environ.get("INCAM_PRODUCT") and \
                    "incampro" in os.environ.get("INCAM_PRODUCT"):
                if os.path.exists("/incam2"):
                    self.edir = '/incam2/release/bin'
                else:
                    self.edir = '/frontline/incampro/release/bin'
        return 0

    def blank(self):
        """ Cleans out the return values"""

        self.STATUS = 0
        self.READANS = ''
        self.COMANS = ''
        self.PAUSANS = ''
        self.MOUSEANS = ''

    def sendCmd(self, cmd, args=''):
        """ Send a command to STDOUT - This is where Genesis will
        see a command - used by CMD, DO_INFO, etc
            cmd - the command root in CSH script form
            args - any arguments to the initial command CMD xxx..."""

        self.blank()
        args = args.replace("\n", "").replace("\t", "")
        wsp = ' ' * (len(args) > 0)
        cmd = self.prefix + cmd + wsp + args + '\n'
        sys.stdout.write(cmd)
        sys.stdout.flush()
        return 0

    def error(self, msg, severity=0):
        """ Basic error handler
            msg - string containing error message
            severity - integer.  If greater than one script exits"""
        sys.stderr.write(msg + '\n')
        if severity:
            sys.exit(severity)

    def write(self, msg):
        """ Very basic output writer
            msg - string to write to STDOUT"""
        sys.stdout.write(msg + '\n')

    #  ---------------------------------------
    #  Genesis Commands
    #
    def SU_ON(self):
        """ The Genesis SU_ON command - eq. to running SU_ON in csh"""
        return self.sendCmd('SU_ON')

    def SU_OFF(self):
        """ Genesis SU_OFF command - eq to running SU_OFF in csh"""
        return self.sendCmd('SU_OFF')

    def VON(self):
        """ Genesis VON command - turns off script halting on errors- eq to running VON in csh"""
        return self.sendCmd('VON')

    def VOF(self):
        """ Genesis VOF command - turns on script halting on errors - eq to running VOF in csh"""
        return self.sendCmd('VOF')

    def PAUSE(self, msg):
        """ Genesis PAUSE command - pauses script with box, and allows user to interact with
        Genesis before continuing - returns STATUS (as integer), sets class variables
        READANS and PAUSANS
            msg - string containing message to put in pause dialog box"""
        try:
            msg = str(msg)
        except Exception, e:
            print e
        self.sendCmd('PAUSE', msg)
        num = 0
        while True:            
            try:            
                self.STATUS = raw_input()
                self.READANS = raw_input()
                self.PAUSANS = raw_input()
                break
            except IOError as e:
                print(e)
                time.sleep(0.01)
                num += 1
                if num > 10:
                    raise 
        return self.STATUS

    def MOUSE(self, msg, mode='p'):
        """ Genesis MOUSE command - pauses to allow user to select a location with the mouse -
        returns STATUS as integer.  Sets class variables READANS and MOUSEANS to mouse location
            msg - message to put in dialog box
            mode - set to character 'p' or 'r'  p means to return a point, and r a rectangle (two points)"""
        self.sendCmd('MOUSE ' + mode, msg)
        num = 0
        while True:            
            try:            
                self.STATUS = string.atoi(raw_input())
                self.READANS = raw_input()
                self.MOUSEANS = raw_input()
                break
            except IOError as e:
                print(e)
                time.sleep(0.01)
                num += 1
                if num > 10:
                    raise 
        return self.STATUS

    def COM(self, args):
        """ Genesis COM command - all important command to issue script commands - returns STATUS
        and sets READANS as the command response raw input.  COMANS is the parsed READANS.  These are
        class variables
            args - string containing arguments for COM command (everything after COM)"""
        if os.environ.get("COM_VON_VOF") == "yes":
            self.VOF()
            self.sendCmd('COM', args)
            self.VON()
        else:            
            self.sendCmd('COM', args)
            
        num = 0
        while True:            
            try:            
                self.STATUS = string.atoi(raw_input())
                self.READANS = raw_input()
                self.COMANS = self.READANS[:]
                break
            except IOError as e:
                print(e)
                time.sleep(0.01)
                num += 1
                if num > 10:
                    raise 
        return self.STATUS

    def AUX(self, args):
        """ Genesis AUX command - returns STATUS.  Sets class variables READANS
        and COMANS, returns STATUS
            args - string containing arguments"""
        self.sendCmd('AUX', args)
        num = 0
        while True:            
            try:            
                self.STATUS = string.atoi(raw_input())
                self.READANS = raw_input()
                self.COMANS = self.READANS[:]
                break
            except IOError as e:
                print(e)
                time.sleep(0.01)
                num += 1
                if num > 10:
                    raise 
        return self.STATUS

    # --- INFO methods ---

    # returns a list of results - process how you like
    def INFO(self, args):
        """ This is similar to the Genesis command COM(info,...) Returns list of strings which
        are lines from the output file
            args - string containing all the arguments to the info command
                (that would be after the info,_*_)"""
        self.COM('info,out_file=%s,write_mode=replace,args=%s' % (self.tmpfile, args))
        num = 0
        while True:         
            if not os.path.exists(self.tmpfile):
                print("reback get info ---->")
                time.sleep(0.01)
                num += 1
                if num > 10:
                    raise
            else:
                break      
        lineList = open(self.tmpfile, 'r').readlines()
        os.unlink(self.tmpfile)
        return lineList

    # returns a dictionary of results parsed out all fun
    def DO_INFO(self, args):
        """ This is the command COM info,...  returns a dictionary with all the information in the
        output file from the info command.  Each array of information is accessed by a key to the
        dictionary that is returned. LIMITATION: Any string resembling a number will be converted
        to a number.  This means that a layer with the name '1.' or '1' will be returned later as
        the float 1.0
            args - arguments to the info command as a string"""
        self.COM('info,out_file=%s,write_mode=replace,args=%s' % (self.tmpfile, args))
        num = 0
        while True:         
            if not os.path.exists(self.tmpfile):
                print("reback get info ---->")
                time.sleep(0.01)
                num += 1
                if num > 10:
                    raise
            else:
                break      
        # self.PAUSE('Hi')
        lineList = open(self.tmpfile, 'r').readlines()
        # print lineList
        os.unlink(self.tmpfile)
        infoDict = self.parseInfo(lineList)
        return infoDict

    def DISP_INFO(self, args):
        """ This is similar to the DO_INFO but is run in 'display' mode and is parsed differently
            - this method is not complete"""
        self.COM('info,out_file=%s,write_mode=replace,args=-m display %s' % (self.tmpfile, args))
        num = 0
        while True:         
            if not os.path.exists(self.tmpfile):
                print("reback get info ---->")
                time.sleep(0.01)
                num += 1
                if num > 10:
                    raise
            else:
                break        
        lineList = open(self.tmpfile, 'r').readlines()
        os.unlink(self.tmpfile)
        infoDict = self.parseDispInfo(lineList)
        return infoDict

    # --- Utility commands ---
    def dbutil(self, *args):
        """ Runs the dbutil command with the specified arguments - returns lines from the response as
        array of strings
            args - arguments for dbutil command"""
        binary = os.path.join(self.edir, 'misc', 'dbutil')
        if "incam" in self.edir.lower() or \
                "incampro" in self.edir.lower():
            binary = os.path.join(self.edir, 'dbutil')

        args = string.join(args)
        fd = os.popen(binary + ' ' + args)
        res = fd.readlines()
        return res

    # Convert string to int or float if possible.
    def convertToNumber(self, value):
        """Utility function - converts string to a number returns integer if
        possible - otherwise returns a float
            value - string to be converted"""
        # If there is a leading zero, and it isn't followed by a decimal (.) then don't
        # convert to a number
        # print "Value " + str(value)
        if value in ["2d2", "2d-2"]:
            return value

        try:
            if value[0] == '0':
                if value[1] != '.':
                    return value
        except:
            pass

        try:
            return string.atoi(value)
        except:
            try:
                return string.atof(value)
            except:
                return value

    # Clean string of given character(s) on the edges
    def clean(self, strip_me, badchars):
        """ Internal - strips a string (strip_me) of given (badchars) on either edge - used in parsing"""
        badchars = badchars + ' \n'
        l = len(strip_me)
        if l < 1:
            return ""
        while (len(strip_me) > 0):
            if strip_me[0] in badchars:
                strip_me = strip_me[1:]
            else:
                break
        x = len(strip_me) - 1
        for i in range(x):
            if strip_me[x - i] in badchars:
                strip_me = strip_me[:x - i]
            else:
                break
        return strip_me

    # Parse the output of an info command in "cshell" mode
    def parseInfo(self, infoList, split_var=" = "):
        """ Internal - parses the output from the info command into a dictionary - returns dictionary"""
        # Parses csh variable assignments and wordlists.
        # Example: set gTOOLnum = ('1' '2' '3' ) OR set gLIMITSxmin = '-10.708661'
        dict = {}
        for line in infoList:
            # print line
            ss = string.split(line, split_var, 1)
            # print "This is ss: "
            # print ss
            if len(ss) == 2:
                key = string.strip(ss[0])[4:]
                val = string.strip(ss[1])
                # print "This is key %s and this is val %s" % (key,val)
                if '(' in val:
                    valList = string.split(val, "'")
                    # Wordlist example: ['(', '1', '   ', '2', '   ', '3', '   ', '4', '    )']
                    dict[key] = []
                    for n in range(len(valList)):
                        if n % 2 == 1:
                            # Append odd items to the list.
                            # print 'THIS IS VALLIST FOR ' + key,
                            # print valList
                            newval = self.clean(valList[n], "'")
                            dict[key].append(self.convertToNumber(newval))

                    if not dict[key]:
                        # valList = string.split(val, " ")
                        for pattern in ["'(.*?)'", '"(.*?)"']:
                            reg = re.compile(pattern)
                            result = reg.findall(val)
                            if result:
                                break
                        valList = result
                        for n in range(len(valList)):
                            # if n in [0, len(valList)-1]:
                            # continue
                            # if not valList[n].strip():
                            # continue
                            newval = valList[n].replace('"', "").replace("'", "")
                            dict[key].append(self.convertToNumber(newval))
                else:
                    # Single value example: ['test']
                    dict[key] = self.convertToNumber(self.clean(val, "'"))

        return dict

    # Parse the output of an info command in "display" mode
    def parseDispInfo(self, infoList):
        """Parses output from info command that was run in display mode. Incomplete"""
        mainDict = {}
        # print infoList
        for line in infoList:
            # print line
            line = string.strip(line)
            # print line
            try:
                exec (line)
            except SyntaxError:
                key = string.splitfields(line, '[')[0]
                if not key in mainDict.keys():
                    exec ('mainDict[\'' + key + '\'] = []')

                vals = string.splitfields(string.splitfields(line, ':')[1], ',')
                dict = {}
                for val in vals:
                    ss = string.splitfields(val, '=')
                    try:
                        val = eval(ss[1])
                    except:
                        val = ss[1]
                    STR = 'dict[\'' + ss[0] + '\'] = val'
                    exec (STR)
                exec ('mainDict[\'' + key + '\'].append(dict)')
        return mainDict

    # Parses the output of a features list (-d FEATURES)
    # Parses only lines, arcs, and pads, text, barcodes all with attribs.  Surfaces you are on your own...
    # utilizes genFeatures.py
    def parseFeatureInfo(self, infoList, feat_index={}):
        """Internal - Parses output from the info command when it writes out features.  Uses the genFeatures.py
        module and parses the information from this command (-d FEATURES) into class objects."""
        mainDict = {}

        lineList = []
        arcList = []
        padList = []
        textList = []
        barList = []
        surfaceList = []

        # setup searches
        pat_line = re.compile("^#L")
        pat_arc = re.compile("^#A")
        pat_pad = re.compile("^#P")
        pat_text = re.compile("^#T")
        pat_bar = re.compile("^#B")
        pat_surface = re.compile("^#OB")
        # print feat_index
        for line in infoList:
            line = string.strip(line)
            s_res = pat_line.search(line)
            if (s_res):
                lineObj = Line(line)
                if feat_index:
                    lineObj.feat_index = feat_index.get(line, None)
                lineList.append(lineObj)
                continue

            s_res = pat_arc.search(line)
            if (s_res):
                arcObj = Arc(line)
                if feat_index:
                    arcObj.feat_index = feat_index.get(line, None)
                arcList.append(arcObj)
                continue

            s_res = pat_pad.search(line)
            if (s_res):
                padObj = Pad(line)
                if feat_index:
                    padObj.feat_index = feat_index.get(line, None)
                padList.append(padObj)
                continue

            s_res = pat_text.search(line)
            if (s_res):                    
                textObj = Text(line)
                if feat_index:
                    textObj.feat_index = feat_index.get(line, None)
                textList.append(textObj)
                continue

            s_res = pat_bar.search(line)
            if (s_res):                    
                barObj = Barcode(line)
                if feat_index:
                    barObj.feat_index = feat_index.get(line, None)
                barList.append(barObj)
                continue

            s_res = pat_surface.search(line)
            if (s_res):
                surfaceObj = Surface(line)
                if feat_index:
                    surfaceObj.feat_index = feat_index.get(line, None)
                surfaceList.append(surfaceObj)
                continue

        mainDict['lines'] = lineList
        mainDict['arcs'] = arcList
        mainDict['pads'] = padList
        mainDict['text'] = textList
        mainDict['barcodes'] = barList
        mainDict['surface'] = surfaceList

        return mainDict

    # print the feature dictionary as text (used often for debugging)
    def printFeatureDict(self, features_dict):
        """ Used for debugging purposes, this prints out a dictionary created with the parseFeatureInfo command
            features_dict - dictionary returned by method parseFeatureInfo"""
        for x in range(len(features_dict['lines'])):
            print "Line " + str(x) + ": Shape-" + features_dict['lines'][x].shape + "",
            print "Start: " + str(features_dict['lines'][x].xs) + "," + str(features_dict['lines'][x].ys) + " End: ",
            print str(features_dict['lines'][x].xe) + "," + str(features_dict['lines'][x].ye) + " Symb: ",
            print features_dict['lines'][x].symbol + " Length: " + str(features_dict['lines'][x].len) + " Pol: ",
            print features_dict['lines'][x].polarity + " Dcode: " + str(features_dict['lines'][x].dcode)
            print "Attr: ",
            print features_dict['lines'][x].attrs
        for x in range(len(features_dict['arcs'])):
            print "Arc " + str(x) + ": Shape-" + features_dict['arcs'][x].shape + "",
            print "Start: " + str(features_dict['arcs'][x].xs) + "," + str(features_dict['arcs'][x].ys) + " End: ",
            print str(features_dict['arcs'][x].xe) + "," + str(features_dict['arcs'][x].ye) + " Cent: ",
            print str(features_dict['arcs'][x].xc) + "," + str(features_dict['arcs'][x].yc) + " Symb: ",
            print features_dict['arcs'][x].symbol + " Pol: " + features_dict['arcs'][x].polarity + " Dcode: ",
            print str(features_dict['arcs'][x].dcode) + " Dir: " + features_dict['arcs'][x].direction
            print "Attr: ",
            print features_dict['arcs'][x].attrs
        for x in range(len(features_dict['pads'])):
            print "Pad " + str(x) + ": Shape-" + features_dict['pads'][x].shape + "",
            print "Loc: " + str(features_dict['pads'][x].x) + "," + str(features_dict['pads'][x].y) + " Symb: ",
            print features_dict['pads'][x].symbol + " Pol: " + features_dict['pads'][x].polarity + " Dcode: ",
            print str(features_dict['pads'][x].dcode) + " Rot: " + str(features_dict['pads'][x].rotation) + " Mir: ",
            print str(features_dict['pads'][x].mirror)
            print "Attr: ",
            print features_dict['pads'][x].attrs
        for x in range(len(features_dict['text'])):
            print "Text " + str(x) + ": Shape-" + features_dict['text'][x].shape + "",
            print "Loc: " + str(features_dict['text'][x].x) + "," + str(features_dict['text'][x].y) + " Font: ",
            print features_dict['text'][x].font + " Pol: " + features_dict['text'][x].polarity + " Text: ",
            print features_dict['text'][x].text + "\n Rot: " + str(features_dict['text'][x].rotation) + " Mir: ",
            print str(features_dict['text'][x].mirror) + " Xsiz: " + str(features_dict['text'][x].xsize) + " Ysiz: ",
            print str(features_dict['text'][x].ysize) + " Wfact: " + str(features_dict['text'][x].wfactor) + " Ver: ",
            print str(features_dict['text'][x].version)
            print "Attr: ",
            print features_dict['text'][x].attrs
        for x in range(len(features_dict['barcodes'])):
            print "Barcode " + str(x) + ": Shape-" + features_dict['barcodes'][x].shape + "",
            print "Loc: " + str(features_dict['barcodes'][x].x) + "," + str(features_dict['barcodes'][x].y) + " Font: ",
            print features_dict['barcodes'][x].font + " Pol: " + features_dict['barcodes'][x].polarity + " Barcode: ",
            print features_dict['barcodes'][x].barcode + "\n Rot: " + str(
                features_dict['barcodes'][x].rotation) + " Constant: ",
            print str(features_dict['barcodes'][x].constant) + " Width: " + str(
                features_dict['barcodes'][x].width) + " Height: ",
            print str(features_dict['barcodes'][x].height) + "\n FullAscii: " + str(
                features_dict['barcodes'][x].full_ascii) + " Cksum: ",
            print str(features_dict['barcodes'][x].cksum) + " Invert BG: " + str(
                features_dict['barcodes'][x].invert_bg) + "\n addTxt: ",
            print str(features_dict['barcodes'][x].add_text) + " TextLoc: " + features_dict['barcodes'][
                x].text_loc + " Text: ",
            print features_dict['barcodes'][x].text
            print "Attr: ",
            print features_dict['barcodes'][x].attrs


class Empty:
    """This class defines a generic class constructor.
       it is used to create "empty" objects, to which attributes may be assigned."""

    def __init__(self):
        pass


class ExtraStuff:
    """ Class definition designed to provide some additional functionality
       to Job, Step, and Layer objects.  And, just to make it confusing
       by implementing multiple-inheritence ;)
       method to retrieve Genesis attributes listed as the given name
       Returns None if the Genesis object does not have the attribute"""

    def getGenesisAttr(self, name):
        """ Retrieve string associated with a certain attribute"""
        for x in xrange(len(self.info['gATTRname'])):
            if self.info['gATTRname'][x] == name:
                return self.info['gATTRval'][x]
            if self.info['gATTRname'][x] == '.' + name:
                return self.info['gATTRval'][x]
        return None


class Top(Genesis):
    """ This class can be used to find out status about Genesis on the main DB level, and do top level functions
     What jobs are open, etc."""

    def __init__(self):
        Genesis.__init__(self)

    # not run hooks 20200327 by lyh
    # self.COM("config_edit,name=gen_line_skip_post_hooks,value=2,mode=user")

    def __str__(self):
        """Returns string describing class - also what is printed if print method called on class object"""
        return 'genClasses status class instance'

    def currentJob(self):
        """ If in a job, this method returns that job as a string"""
        if 'JOB' in os.environ.keys():
            return os.environ['JOB']
        else:
            return ''

    def createJob(self, name, db_name):
        """Create a Genesis job by the name given.  Return a job class instance by that name.
        Job must be opened after this call.  It will be closed and checked in initially.
            name - name of new Genesis job entity
            db_name - name of database in which to put it"""

        joblist = self.listJobs()
        for eachjob in joblist:
            # If the job already exists
            if name == eachjob:
                return None

        self.COM('create_entity,job=,is_fw=no,type=job,name=' + name + ',db=' + db_name + ',fw_type=form')

        if self.STATUS:
            print "Some error in creating job " + name + " in db " + db_name

        job = Job(name)
        job.close(1)

        return job

    def deleteJob(self, name):
        """Delete a Genesis job by the name given.  Return status of command.
        returns -1 if no such job.
            name - name of existing job"""

        joblist = self.listJobs()
        for eachjob in joblist:
            # If the job sxists, delete
            if name == eachjob:
                self.COM('delete_entity,job=,type=job,name=' + name)
                return self.STATUS

        # If it gets this far, the job didn't exist, and couldn't be deleted
        # self.PAUSE(" Job not found:" + name)
        return -1

    def importJob(self, name, import_dir, db_name):
        """ Import an ODB++/Valor format job - returns status.
            name - name to give new job
            import_dir - directory from which to import
            db_name - database it will reside in"""

        joblist = self.listJobs()
        for eachjob in joblist:
            # If the job already exists
            if name == eachjob:
                return None

        STR = 'import_job,db=%s,path=%s,name=%s' % (db_name, import_dir, name)
        self.COM(STR)

        return self.STATUS

    def currentStep(self):
        """ If in a step, return the step name as a string"""
        if 'STEP' in os.environ.keys():
            return os.environ['STEP']
        else:
            return ''

    def openJobs(self):
        """ Returns a list of open jobs, as a list of strings"""
        jobList = self.DO_INFO('-t root')['gJOBS_LIST']
        openJobList = []
        for job in jobList:
            self.COM('is_job_open,job=%s' % job)
            if self.COMANS == 'yes':
                openJobList.append(job)
        return openJobList

    def listJobs(self):
        """ Returns a list of jobs in the databases., as a list of strings"""
        return self.DO_INFO('-t root')['gJOBS_LIST']

    def getUser(self):
        """ Returns the name, as a string, of the current user"""
        self.COM('get_user_name')
        self.user = self.COMANS
        return self.user


# Defines the job-level class
#  Must  supply the job name.
class Job(Genesis, ExtraStuff, JobCmds):
    """ This class is ised to represent a job object in the Genesis database.  It is used to open, close, and manipulate
jobs.  Other classes representing steps, forms, matrices, etc, can be contained by this class."""

    def __init__(self, name):
        self.name = name
        Genesis.__init__(self)

        if os.environ.get("GENESIS_PID", None) is None:
            try:
                os.system("rm -rf %s/pid/genesis_pid_%s*" % (self.tmpdir, name))
                if not os.path.exists(self.tmpdir + "/pid"):
                    os.makedirs(self.tmpdir + "/pid")

                self.COM("save_log_file,dir=%s/pid,prefix=genesis_pid_%s,clear=no" %
                         (self.tmpdir, name))
                new_pid = [x.split(".")[-1] for x in os.listdir(self.tmpdir + "/pid")
                           if "genesis_pid_%s" % name in x]
                # print "PID ----->", new_pid
                os.system("rm -rf %s/pid/genesis_pid_%s*" % (self.tmpdir, name))
                if new_pid:
                    os.environ["GENESIS_PID"] = new_pid[0]
            except Exception, e:
                print e

    def __str__(self):
        """Returns string describing class - also what is printed if print method called on class object"""
        return 'genClasses Job class instance for job %s.' % self.name

    # Method to force a refresh of attributes which are likely to change
    def _forceRefresh(self):
        """ Method to force a refresh of attributes which are likely to change"""
        self._deleteAttribute('matrix')
        self._deleteAttribute('info')
        self._deleteAttribute('steps')
        self._deleteAttribute('forms')

    def __getattr__(self, name):
        """
        Hook to generate attributes as they're requested - it is run automatically upon
        initial request	of an attribute. e.g. <class instance>.attribute

        If the attribute is in this method, it is handled by methods defined here,
        otherwise the Genesis job object associated with this instance is inspected
        for a corresponding Genesis attribute; the value of which is stored in the
        instance attribute.

        Special Attributes Supported:  matrix, info, steps, forms, db, dbpath, lockStat, user, bucket, xmlbucket
        """

        # print 'Dynamically fetching Job attribute::',name
        if name == 'matrix':
            self.matrix = Matrix(self)
            return self.matrix
        elif name == 'info':
            self.info = self.getInfo()
            return self.info
        elif name == 'steps':
            self.steps = self.getSteps()
            return self.steps
        elif name == 'forms':
            self.forms = self.getForms()
            return self.forms
        elif name == 'db':
            self.db = self.dbName()
            return self.db
        elif name == 'dbpath':
            self.dbpath = self.dbPath()
            return self.dbpath
        elif name == 'lockStat':
            self.lockStat = self.dbStat()
            return self.lockStat
        elif name == 'user':
            self.user = self.getUser()
            return self.user
        elif name == 'bucket':
            self.bucket = self.getBucket()
            return self.bucket
        elif name in ('__members__', '__methods__'):
            return
        else:
            val = self.getGenesisAttr(name)
            return val

    # ----------------------------------------------------------------
    #  These methods are called dynamically from the __getattr__ method,
    #    when the attributes are first accessed.
    # ----------------------------------------------------------------
    def getInfo(self):
        """ Called by __get_attr__ or can be called by user.  Builds and returns <inst>.info dictionary"""
        # print "Running getinfo"
        self.info = self.DO_INFO('-t job -e ' + self.name)
        return self.info

    def getSteps(self):
        """ Populates the <inst>.steps dictionary with Step classes representing each step.  Use to update
        the job class's representation of its steps"""
        self.steps = {}
        # print "Running getsteps"
        for step in self.info['gSTEPS_LIST']:
            self.steps[step] = Step(self, step)
        return self.steps

    def getForms(self):
        """ Populates the self.forms list.  This contains a list of all form names in the job.  Forms aren't
        very fully implemented yet."""
        self.forms = {}
        for form in self.info['gFORMS_LIST']:
            self.forms[form] = Form(self, form)
        return self.forms

    def dbName(self):
        """ Returns the name of the job.  Populates <inst>.db"""
        res = self.dbutil('list', 'jobs', self.name)
        self.db = string.split(res[0])[3]
        return self.db

    def dbPath(self):
        """ Returns the file path to the job.  Populates <inst>.dbpath"""
        if os.environ.get("JOB_USER_DIR", None):
            self.dbpath = os.path.dirname(os.environ["JOB_USER_DIR"])
        else:            
            res = self.dbutil('path', 'jobs', str(self.name))
            try:
                self.dbpath = string.strip(res[0])
            except:
                if sys.platform == "win32":
                    self.dbpath = os.path.join(
                        os.environ["GENESIS_DIR"], "fw", "jobs", str(self.name))
                    if not os.path.exists(self.dbpath):
                        for dirname in ["c:/genesis", "d:/genesis", "e:/genesis", "f:/genesis", "w:/genesis"]:
                            self.dbpath = os.path.join(
                                dirname, "fw", "jobs", str(self.name))
                            if os.path.exists(self.dbpath):
                                break
                else:
                    if os.path.exists("/incam2/fw/jobs/" + str(self.name)):
                        self.dbpath = "/incam2/fw/jobs/" + str(self.name)
                    else:
                        self.dbpath = "/incam/fw/jobs/" + str(self.name)
        return self.dbpath

    def dbStat(self):
        """ Returns the lock status.  Populates <inst>.lockStat """
        res = self.dbutil('lock', 'test', self.name)
        ss = string.split(res[0])
        d = {'no': 0, 'yes': 1}
        self.lockStat = d[ss[0]]
        if len(ss) > 1: self.lockUser = ss[1]
        return self.lockStat

    def getBucket(self):
        ''' Returns the persistency bucket...inspects the genPersist module to
        check the value of ENGINE, which by default is set to XML if gnosis.xml is installed.'''
        import genPersist
        if genPersist.ENGINE == 'XML':
            bucket = genPersist.XmlBucket(self)
        else:
            bucket = genPersist.Bucket(self)

        return bucket


class Step(Genesis, ExtraStuff, StepCmds):
    """ This class defines a step instance.  It is automatically instantiated as a
    member of the job.steps dictionary when the job.steps attribute is accessed.
    StepCmds is a subclass that is set up in genCommands.py containing commands for Steps.
    The step class allows for operations at the step level and is a gateway to the graphic
    editor functions and checklists, as well as layer manipulation (not the matrix - that
    is at the job level)

    """

    def __init__(self, job, name):
        Genesis.__init__(self)
        self.job = job
        self.name = str(name)
        self.group = None

        # Check if I really exist as a step
        d = self.DO_INFO('-t step -e ' + self.job.name + '/' + self.name + ' -d exists')
        if d['gEXISTS'] == 'no':
            self.error('Non-existent step::' + self.name, 1)

    def COM(self, args):
        """ Overloading method, to set group automatically - in the graphic editor"""
        if self.group:
            self.setGroup()
        self.sendCmd('COM', args)
        num = 0
        while True:            
            try:            
                self.STATUS = string.atoi(raw_input())
                self.READANS = raw_input()
                self.COMANS = self.READANS[:]
                break
            except IOError as e:
                print(e)
                time.sleep(0.01)
                num += 1
                if num > 10:
                    raise 
        return self.STATUS

    def _forceRefresh(self):
        """ Forces refresh of attributes that are likely to change."""
        self.job._deleteAttribute('matrix')
        self._deleteAttribute('info')
        self._deleteAttribute('layers')
        self._deleteAttribute('sr')
        self._deleteAttribute('profile')

    def __getattr__(self, name):
        """
        Hook to generate attributes as they're requested - it is run automatically upon
        initial request	of an attribute. e.g. <class instance>.attribute

        If the attribute is in this method, it is handled by methods defined here,
        otherwise the Genesis job object associated with this instance is inspected
        for a corresponding Genesis attribute; the value of which is stored in the
        instance attribute.

        Special Attributes Supported:  info, profile, layers, sr, datum, checks
        """
        # print 'Dynamically fetching Step attribute::',name
        if name == 'info':
            self.info = self.getInfo()
            return self.info
        elif name == 'profile':
            self.profile = self.getProfile()
            return self.profile
        elif name == 'layers':
            self.layers = self.getLayers()
            return self.layers
        elif name == 'sr':
            self.sr = self.getSr()
            return self.sr
        elif name == 'datum':
            self.datum = self.getDatum()
            return self.datum
        elif name == 'checks':
            self.checks = self.getChecks()
            return self.checks
        elif name in ('__members__', '__methods__'):
            return
        else:
            val = self.getGenesisAttr(name)
            return val

    # ----------------------------------------------------------------
    #  These methods are called dynamically from the __getattr__ method,
    #    when the attributes are first accessed.
    # ----------------------------------------------------------------
    def getInfo(self):
        """ Build the self.info dictionary... Doesn't do a full command (excluding -d from info command)
        because it does LIMITS, which takes forever!  Returns <inst>.info"""
        self.info = {}
        self.tmp = self.DO_INFO('-t step -e ' + self.job.name + '/' + self.name + ' -d LAYERS_LIST')
        self.info.update(self.tmp)
        self.tmp = self.DO_INFO('-t step -e ' + self.job.name + '/' + self.name + ' -d CHECKS_LIST')
        self.info.update(self.tmp)
        self.tmp = self.DO_INFO('-t step -e ' + self.job.name + '/' + self.name + ' -d NETS_LIST')
        self.info.update(self.tmp)
        self.tmp = self.DO_INFO('-t step -e ' + self.job.name + '/' + self.name + ' -d CHECKS_LIST')
        self.info.update(self.tmp)
        self.tmp = self.DO_INFO('-t step -e ' + self.job.name + '/' + self.name + ' -d ACTIVE_AREA')
        self.info.update(self.tmp)
        self.tmp = self.DO_INFO('-t step -e ' + self.job.name + '/' + self.name + ' -d NUM_SR')
        self.info.update(self.tmp)
        self.tmp = self.DO_INFO('-t step -e ' + self.job.name + '/' + self.name + ' -d SR')
        self.info.update(self.tmp)
        self.tmp = self.DO_INFO('-t step -e ' + self.job.name + '/' + self.name + ' -d SR_LIMITS')
        self.info.update(self.tmp)
        self.tmp = self.DO_INFO('-t step -e ' + self.job.name + '/' + self.name + ' -d NUM_REPEATS')
        self.info.update(self.tmp)
        self.tmp = self.DO_INFO('-t step -e ' + self.job.name + '/' + self.name + ' -d PROF_LIMITS')
        self.info.update(self.tmp)
        self.tmp = self.DO_INFO('-t step -e ' + self.job.name + '/' + self.name + ' -d PROF')
        self.info.update(self.tmp)
        self.tmp = self.DO_INFO('-t step -e ' + self.job.name + '/' + self.name + ' -d DATUM')
        self.info.update(self.tmp)
        self.tmp = self.DO_INFO('-t step -e ' + self.job.name + '/' + self.name + ' -d REPEAT')
        self.info.update(self.tmp)
        self.tmp = self.DO_INFO('-t step -e ' + self.job.name + '/' + self.name + ' -d ATTR')
        self.info.update(self.tmp)

        return self.info

    # Build the profile object
    def getProfile(self):
        """ Retrieves profile limits and places in <inst>.profile class. Access
        values by <stepinst>.profile.xmin (xmax, ymin, ymax, xsize, ysize, xcenter, ycenter)"""
        # print 'Getting Profile...'
        self.profile = Empty()
        self.profile.xmin = self.info['gPROF_LIMITSxmin']
        self.profile.ymin = self.info['gPROF_LIMITSymin']
        self.profile.xmax = self.info['gPROF_LIMITSxmax']
        self.profile.ymax = self.info['gPROF_LIMITSymax']
        # print self.profile.xmin, self.profile.ymin, self.profile.xmax, self.profile.ymax
        self.profile.xsize = self.profile.xmax - self.profile.xmin
        self.profile.ysize = self.profile.ymax - self.profile.ymin
        self.profile.xcenter = self.profile.xmin + self.profile.xsize / 2
        self.profile.ycenter = self.profile.ymin + self.profile.ysize / 2
        return self.profile

    def getSr(self):
        """ Builds <inst>.sr object and returns it.  This is the step & repeat limits.
        The numbers it generates are accessed in dot notation as well (like profile)
        (srLimits:L xmin, xmax, ymin, ymax, eBorder, wBorder, nBorder, sBorder, table)
        (Table contains list entries, each with access to each instance using dot
        notation - step, xanchor, yanchor, xdist, ydist, xnum, ynum, angle, mirror,
        xmin, xmax, ymin, ymax.  Accessed as sr.table[x].xmax, etc."""
        self.sr = Empty()
        self.sr.xmin = self.info['gSR_LIMITSxmin']
        self.sr.ymin = self.info['gSR_LIMITSymin']
        self.sr.xmax = self.info['gSR_LIMITSxmax']
        self.sr.ymax = self.info['gSR_LIMITSymax']
        self.sr.eBorder = self.profile.xmax - self.sr.xmax
        self.sr.wBorder = self.sr.xmin - self.profile.xmin
        self.sr.nBorder = self.profile.ymax - self.sr.ymax
        self.sr.sBorder = self.sr.ymin - self.profile.ymin
        self.sr.table = []
        for x in xrange(len(self.info['gSRstep'])):
            d = Empty()
            d.step = str(self.info['gSRstep'][x])
            d.xanchor = self.info['gSRxa'][x]
            d.yanchor = self.info['gSRya'][x]
            d.xdist = self.info['gSRdx'][x]
            d.ydist = self.info['gSRdy'][x]
            d.xnum = self.info['gSRnx'][x]
            d.ynum = self.info['gSRny'][x]
            d.angle = self.info['gSRangle'][x]
            d.mirror = self.info['gSRmirror'][x]
            d.xmin = self.info['gSRxmin'][x]
            d.ymin = self.info['gSRymin'][x]
            d.xmax = self.info['gSRxmax'][x]
            d.ymax = self.info['gSRymax'][x]
            self.sr.table.append(d)

        return self.sr

    def getLayers(self):
        """ Builds a dictionary of all the layers in the step.  This dictionary
        points to Layer classes as defined in this module."""
        self.layers = {}
        # print "Running getLayers"
        for layName in self.info['gLAYERS_LIST']:
            self.layers[str(layName)] = Layer(self, str(layName))
        return self.layers

    def getChecks(self):
        """ Builds a dictionary of all the checklists in the step.  It points to checklist
        classes, as defined in this module"""
        self.checks = {}
        # print "Running getChecks to retrieve checklist names"
        for checkName in self.info['gCHECKS_LIST']:
            self.checks[checkName] = Checklist(self, checkName)
        return self.checks

    def getDatum(self):
        """ Creates datum dictionary.  <inst>.datum['x'] or ['y']"""
        self.datum = {'x': 0.0, 'y': 0.0}
        d = self.DO_INFO('-t step -e ' + self.job.name + '/' + self.name + ' -d DATUM')
        self.datum['x'] = d['gDATUMx']
        self.datum['y'] = d['gDATUMy']
        return self.datum

    def isLayer(self, layer_name='misc'):
        """ Method to check for a single layer.  Sometimes faster than doing a key search on the
        layers dictionary  Returns 1 if exists, 0 if not.
            layer_name = String representing the name of the layer"""
        # print "Checking for layer :|" + layer_name + "|"
        if not layer_name:
            return 0
        d = self.DO_INFO(args='-t layer -e ' + self.job.name + '/' + self.name + '/' + layer_name + ' -d exists')
       
        if d['gEXISTS'] == 'no':
            return 0
        else:
            return 1

    def setGroup(self):
        """ Sets AUX group to current editor"""
        self.AUX('set_group,group=' + self.group)


# This class defines a form instance. It is automatically
#   instantiated  		
class Form(Genesis):
    """ Defines a form instance.  It is automatically instantiated as a member
     of the job.forms dictionary when the job.forms attribute is accessed."""

    def __init__(self, job, name):
        Genesis.__init__(self)
        self.job = job
        self.name = name

    def open(self):
        """ Opens and shows the form"""
        STR = 'show_form,job=' + self.job.name + ',form=' + self.name + ',updonly=No'
        self.COM(STR)
        return self.STATUS

    def close(self):
        """ Closes the form"""
        STR = 'close_form,job=' + self.job.name + ',form=' + self.name
        self.COM(STR)
        return self.STATUS

    def delete(self):
        """ Deletes this form """
        STR = 'delete_form,job=' + self.job.name + ',form=' + self.name
        self.COM(STR)
        del self.job.forms[self.name]
        return self.STATUS

    def read(self, field):
        """ Reads a form element, with opt_name set to no (i.e. gives selected column for options, not option name)
            field - string containing name of form element to read"""
        STR = 'read_form,job=' + self.job.name + ',form=' + self.name + ',elem=' + field + ',opt_name=no'
        self.COM(STR)
        return self.COMANS

    def readOpt(self, field):
        """ Reads a form element with opt_name set to yes (i.e. gives option value, not which column)
            field - string containing name of form element to read"""
        STR = 'read_form,job=' + self.job.name + ',form=' + self.name + ',elem=' + field + ',opt_name=yes'
        self.COM(STR)
        return self.COMANS

    def write(self, field, value, color=''):
        """ write value into field
            field - string with name of form element
            value - value to put there (for radio,etc, put col # )
            color (optional) - six digit color code"""
        STR = 'edit_form,job=' + self.job.name + ',form=' + self.name + ',elem=' + field + ',value=' + value
        if (color != ''):
            STR = STR + ',color=' + color
        STR = STR + ',opt_name=no'
        self.COM(STR)
        return self.COMANS

    def writeFile(self, fileName, color=''):
        """ write sets of values into elements.  Read information from file.  Doesn't use option names
            file - file containing element/value pairs see Genesis Docs for edit_form_list
            color - optional - color for changed elements (I think)"""

        STR = 'edit_form_list,job=' + self.job.name + ',form=' + self.name + ',opt_name=no,in_file=' + fileName
        if (color != ''):
            STR = STR + ',color=' + color
        self.COM(STR)
        return self.COMANS

    def writeFileOpt(self, fileName, color=''):
        """ write sets of values into elements.  Read information from file.  Uses option names
            file - file containing element/value pairs see Genesis Docs for edit_form_list
            color - optional - color for changed elements (I think)"""

        STR = 'edit_form_list,job=' + self.job.name + ',form=' + self.name + ',opt_name=yes,in_file=' + fileName
        if (color != ''):
            STR = STR + ',color=' + color
        self.COM(STR)
        return self.COMANS

    def color(self, element, color):
        """ change an element to another color
            element: Element Name
            color: six digit color code (RRGGBB)"""
        STR = 'edit_form,job=' + self.job.name + ',form=' + self.name + ',elem=' + element + ',color=' + color + ',opt_name=no'
        self.COM(STR)
        return self.COMANS

    def writeOpt(self, field, value, color=''):
        """ write value into field , using option name
            field - string with name of form element
            value - value to put there (for radio,etc, put value, not col#)
            color (optional) - siz digit color code"""
        STR = 'edit_form,job=' + self.job.name + ',form=' + self.name + ',elem=' + field + ',value=' + value
        if (color != ''):
            STR = STR + ',color=' + color
        STR = STR + ',opt_name=yes'
        self.COM(STR)
        return self.COMANS

    def visibility(self, field, mode):
        """ Changes an elements visibility
            field - element name
            mode - mode (sensitve,unsensitive,hide,unhide)"""
        STR = 'form_elem_visibility,job=' + self.job.name + ',form=' + self.name + ',elem=' + field + ',mode=' + mode
        self.COM(STR)
        return self.COMANS


class Checklist(Genesis):
    """ This class defines a checklist instance. Each checklist is automatically
       instantiated as a member of the {step}.checks dictionary when
       the {step}.checks attribute is accessed. """

    def __init__(self, step, name):
        Genesis.__init__(self)
        self.job = step.job
        self.step = step
        self.name = name

    def show(self):
        """ Show the checklist """
        STR = 'chklist_show,chklist=' + self.name
        self.COM(STR)
        return self.STATUS

    def open(self):
        """ Opens checklist, but doesn't show it """
        STR = 'chklist_open,chklist=' + self.name
        self.COM(STR)
        return self.STATUS

    def close(self):
        """ Close the checklist """
        STR = 'close_checklist,chklist=' + self.name + ',mode=destroy'
        self.COM(STR)
        return self.STATUS

    def hide(self):
        """ hides checklist.  It stays open, but isn't visible"""
        STR = 'close_checklist,chklist=' + self.name + ',mode=hide'
        self.COM(STR)
        return self.STATUS

    def run(self, params='',nact_num = 'a'):
        """ Runs a checklist on all actions.
            params - optional string (defaults to empty) <NOT IMPLEMENTED YET>"""

        STR = 'chklist_run,chklist=%s,nact=%s,area=profile' % (self.name, nact_num)
        self.COM(STR)
        return self.STATUS

    # update checklist parameters - params is a dictionary of parameters
    def update(self, action=1, params={}):
        """ Update checklist parameters, and specify action to which updates apply
            params - a dictionary of parameters.  Key is parameter name and value is
                         parameter values assigned to parameter"""

        param_str = '('
        for key in params.keys():
            param_str = param_str + '(' + key + '=' + params[key] + ')'
        STR = 'chklist_cupd,chklist=' + self.name + ',nact=' + str(action) + ',params=' + param_str + ',mode=regular'
        self.COM(STR)
        return self.STATUS


# This class defines the job matrix.
class Matrix(Genesis, MatrixCmds):
    """ Defines the job matrix.  Allows manipulation of matrix and retrieval of information from matrix
        accessed as <jobname>.matrix"""

    def __init__(self, job):
        Genesis.__init__(self)
        self.job = job
        self.name = 'matrix'

    def _forceRefresh(self):
        """ Method to force a refresh of attributes likely to change"""
        self._deleteAttribute('info')

    def __getattr__(self, name):
        """ Method to dynamically get info about the matrix
        Attributes Supported: info"""
        # print 'Dynamically fetching Matrix attribute::',name
        if name == 'info':
            # if hasattr(self, 'info'): return self.info
            self.info = self.getInfo()
            return self.info
        elif name in ('__members__', '__methods__'):
            return

    # ----------------------------------------------------------------
    #  These methods are called dynamically from the __getattr__ method,
    #    when the attributes are first accessed.
    # ----------------------------------------------------------------

    # Get all info about self, store in self.info
    def getInfo(self):
        """ Called when the info dictionary is accessed if not already created.  Populates info
        dictionary."""
        self.info = self.DO_INFO(' -t matrix -e ' + self.job.name + '/matrix')
        # Force all gROWname elements to string values
        for x in xrange(len(self.info['gROWname'])):
            self.info['gROWname'][x] = str(self.info['gROWname'][x])

        # Force all gCOLstep_name elements to string values
        for x in xrange(len(self.info['gCOLstep_name'])):
            self.info['gCOLstep_name'][x] = str(self.info['gCOLstep_name'][x])

        return self.info

    def rowList(self):
        ''' Called when the info dictionary is accessed if not already created.  Populates info
        dictionary.'''
        self.info = self.DO_INFO(' -t matrix -e ' + self.job.name + '/matrix -d ROW')
        return self.info['gROWname']

    def getRow(self, name):
        """ method returns row number of given layer.  A row number of zero
        means the layer doesn't exist
            name - string containing name of layer"""

        self.getInfo()
        for rowNum in self.info['gROWrow']:
            if self.info['gROWname'][int(rowNum) - 1] == name:
                return int(rowNum)
        return '0'

    def getRowInfo(self, rowNum):
        """Method returns dictionary of information on given row. Dictionary contains
        following keys:  name, context, type, polarity, and side
            rowNum - The row number in the matrix"""

        index = int(rowNum) - 1

        rowInfo = {'name': self.info['gROWname'][index],
                   'context': self.info['gROWcontext'][index],
                   'type': self.info['gROWlayer_type'][index],
                   'polarity': self.info['gROWpolarity'][index],
                   'side': self.info['gROWside'][index]}

        return rowInfo

    def getRowColor(self, rowNum, format='rgb'):
        ''' Return the color used in the Genesis matrix for the given row (layer).
        If format is 'rgb', a tuple of rgb values is returned (e,g, (252,198,55) for signal layers).
        If format is 'hex', a string representing the hexadecimal color value is returned (e.g. 'FCC64D')
        The colors table is a dictionary defined in the Genesis class as self.colors
        '''
        index = int(rowNum) - 1
        layType = self.info['gROWlayer_type'][index]
        if self.info['gROWcontext'][index] == 'misc':
            layType = 'document'
        if not len(layType): layType = 'document'

        return self.job.colors[format][layType]


# END OF MATRIX CLASS

class Layer(ExtraStuff, LayerCmds):
    """this class defines a layer object inside editor.  It may contain info, but cannot
       issue COM commands on it's own.  This layer object is a child of a step,
       NOT the matrix.  e.g. this object does not represent a matrix row.
       Most of these are commands you can access by right-clicking a layer in the editor."""

    def __init__(self, step, name):
        self.step = step
        self.name = name
        self.job = self.step.job

    def _deleteAttribute(self, attr):
        """ Method for generically deleting an attribute, with some
           validation before blindly deleting.
               attr - string containing attribute name"""
        if hasattr(self, attr):
            delattr(self, attr)

    def _forceRefresh(self):
        """ Method to force a refresh of attributes likely to change """
        self._deleteAttribute('info')
        self._deleteAttribute('cell')

    def __del__(self):
        pass

    def __getattr__(self, name):
        """
        Hook to generate attributes as they're requested - it is run automatically upon
        initial request	of an attribute. e.g. <class instance>.attribute

        If the attribute is in this method, it is handled by methods defined here,
        otherwise the Genesis layer object associated with this instance is inspected
        for a corresponding Genesis attribute; the value of which is stored in the
        instance attribute.

        Special Attributes Supported:  info, cell, color, hexcolor
        """

        # print 'Dynamically fetching Layer attribute::',name
        if name == 'info':
            self.info = self.getInfo()
            return self.info
        elif name == 'cell':
            self.cell = MatrixCellInfo(self)
            return self.cell
        elif name == 'color':
            self.color = self.getColor()
            return self.color
        elif name == 'hexcolor':
            self.hexcolor = self.getColor(format='hex')
            return self.hexcolor
        elif name in ('__members__', '__methods__'):
            return
        else:
            val = self.getGenesisAttr(name)
            return val

    # ----------------------------------------------------------------
    #  These methods are called dynamically from the __getattr__ method,
    #    when the attributes are first accessed.
    # ----------------------------------------------------------------

    def getInfo(self):
        """Get all info about self, store in self.info
        This method is automagically called when one accesses the self.info attribute."""
        STR = ' -t layer -e %s/%s/%s' % (self.job.name, self.step.name, self.name)
        self.info = self.step.DO_INFO(STR)
        return self.info

    def getColor(self, format='rgb'):
        ''' Return the color used in the Genesis matrix for this layer.
        If format is 'rgb', a tuple of rgb values is returned (e,g, (252,198,55) for signal layers).
        If format is 'hex', a string representing the hexadecimal color value is returned (e.g. 'FCC64D')
        This method is called when the layer's self.color or self.hexcolor attribute are accessed
        The colors table is a dictionary defined in the Genesis class as self.colors
        '''
        layType = self.info['gTYPE']
        if self.info['gCONTEXT'] == 'misc':
            layType = 'document'
        if not len(layType): layType = 'document'

        return self.job.colors[format][layType]


class MatrixCellInfo:
    """ This class defines an object which describes a layer's
    matrix information.  This object may only be a child of a layer
    object.	 Object in layer class is self.cell"""

    def __init__(self, parent):
        self.parent = parent
        self.parse()

    def parse(self):
        """ Run by __init__ method - parses matrix info into the object"""
        matrix = self.parent.job.matrix
        self.row = None
        self.type = None
        self.name = None
        self.context = None
        self.layer_type = None
        self.polarity = None
        self.side = None
        self.drl_start = None
        self.drl_end = None
        self.foil_side = None
        self.sheet_side = None          
        for x in xrange(len(matrix.info['gROWname'])):
            if not len(matrix.info['gROWname'][x]): continue
            if matrix.info['gROWname'][x] == self.parent.name:
                self.row = matrix.info['gROWrow'][x]
                self.type = matrix.info['gROWtype'][x]
                self.name = matrix.info['gROWname'][x]
                self.context = matrix.info['gROWcontext'][x]
                self.layer_type = matrix.info['gROWlayer_type'][x]
                self.polarity = matrix.info['gROWpolarity'][x]
                self.side = matrix.info['gROWside'][x]
                self.drl_start = matrix.info['gROWdrl_start'][x]
                self.drl_end = matrix.info['gROWdrl_end'][x]
                self.foil_side = matrix.info['gROWfoil_side'][x]
                self.sheet_side = matrix.info['gROWsheet_side'][x]
                break


# Self-test code - unfortunately not very complete...
if __name__ == '__main__':
    j = Job('blank')
    j.open(1)
    print j.STATUS
    print type(j.STATUS)
    print j.READANS
    print type(j.READANS)
    print j.COMANS
    print type(j.COMANS)
    steps = j.steps
    print 'STEPS::', steps
    for key in steps.keys():
        step = steps[key]
        step.open()
    for key in steps.keys():
        step = steps[key]
        step.close()
        time.sleep(2)

    j.addStep('xyz')
    j.removeStep('xyz')
    print j.steps

    matrix = j.matrix
    print matrix.info
    j.matrix.removeLayer('sm8')
    j.matrix.COM('matrix_refresh,job=' + j.name + ',matrix=matrix')
    time.sleep(3)
    j.matrix.addLayer('sm8', 11, type='solder_mask')
