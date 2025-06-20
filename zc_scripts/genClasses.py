#!/usr/bin python

"""Modules for joining Genesis 2000 scripting and the Python scripting language.

This module has several companion modules.  These companion modules provide added
functionality over and above the basic Genesis commands.  This module holds several
classes used to abstract the interface with Genesis 2000, making scripting in 
Python faster and easier."""

__author__  = "Mike J. Hopkins"
__date__    = "18 August 2004"
__version__ = "$Revision: 1.4.1 $"
__credits__ = """ Daniel R. Gowans, for contributions to content.
Frontline PCB, for an excellent scripting interface to Genesis 2000"""

# NEED: genCommands.py and genFeatures.py

# drgowans - 8/21/2003 - modified significantly in rev 1.2 to change the method
# of subClassing from instancing helper classes to directly subclassing them.
# Hopefully this will reduce the code size and make method calling more straightforward,
# as well as removing the need for the backward compatible wrapper modules.

#Checklist.action()   20210910 zl   开启checkanalyzer
# Job   更新依赖步 updateDependentStep 20210913 zl
# 加info2获取单位为mm的info、profile2、sr2  20211018 zl
# 网络分析方法  20211028 zl
# rotateStep  旋转step 20211110 zl
# initStep 初始化step 20211206 zl

 # Import Standard Python Modules
import os, sys, time, re, math, platform

# import package specific stuff
import genCommands, genFeatures

#Identify
print("Using genClasses.py Rev " + __version__)

from genCommands import *
from genFeatures import *

class Genesis:
    """This class defines the low-level interface methods for use with Genesis.
       It serves as a base-class for the higher-level objects.  It defines 
       methods to interface with Genesis itself with the methods Frontline has
       provided."""

    colors = {
        'rgb': {
            'signal'    : (252,198,55),
            'mixed'        : (242,224,134),
            'power_ground'    : (219,173,0),
            'silk_screen'    : (255,255,255),
            'solder_mask'    : (0,165,124),
            'solder_paste'    : (255,255,206),
            'drill'        : (155,180,191),
            'rout'        : (216,216,216),
            'document'    : (155,219,219),
            },
        'hex': {
            'signal'    : 'FCC64D',
            'mixed'        : 'F2E086',
            'power_ground'    : 'DBAD00',
            'silk_screen'    : 'FFFFFF',
            'solder_mask'    : '00A57C',
            'solder_paste'    : 'FFFFCE',
            'drill'        : '9BB4BF',
            'rout'        : 'D8D8D8',
            'document'    : '9BDBDB',
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
        tmp = 'gen_'+repr(self.pid)+'.'+repr(time.time())
        if 'GENESIS_TMP' in os.environ:
            self.tmpfile = os.path.join(os.environ['GENESIS_TMP'], tmp)
            self.tmpdir = os.environ['GENESIS_TMP']
        else:
            if platform.system() == "Linux":
                self.tmpfile = os.path.join('/genesis/tmp', tmp)
                self.tmpdir = '/genesis/tmp'
            elif platform.system() == "Windows":
                self.tmpfile = os.path.join('c:/genesis/tmp', tmp)
                self.tmpdir = 'c:/genesis/tmp'

    def __del__(self):
        """ Called when class is cleaned up by python"""
        try:
            if os.path.isfile(self.tmpfile):
                res = os.unlink(self.tmpfile)
                if res: self.error('Error deleting tmpfile', res)
        except:
            None

    def _deleteAttribute(self, attr):
        """Method for generically deleting an attribute - makes sure attribute exists first
            attr - string containing the attribute to be deleted"""

        if hasattr(self, attr):
            delattr(self, attr)

    def normalize(self):
        """Normalize the path to GENESIS_EDIR, and make sure the environment is set"""

        if 'GENESIS_DIR' not in os.environ:
            self.error('GENESIS_DIR not set', 1)
        self.gendir = os.environ['GENESIS_DIR']
        if 'GENESIS_EDIR' not in os.environ:
            self.error('GENESIS_EDIR not set', 1)
        self.edir = os.environ['GENESIS_EDIR']
        if not os.path.isdir(self.edir):
            self.edir = os.path.join(self.gendir, self.edir)
        if not os.path.isdir(self.edir):
            self.error('Cannot normalize GENESIS_EDIR', 1)
        return 0

    def blank(self):
        """ Cleans out the return values"""

        self.STATUS   = 0
        self.READANS  = ''
        self.COMANS   = ''
        self.PAUSANS  = ''
        self.MOUSEANS = ''

    def sendCmd(self, cmd, args=''):
        """ Send a command to STDOUT - This is where Genesis will 
        see a command - used by CMD, DO_INFO, etc
            cmd - the command root in CSH script form
            args - any arguments to the initial command CMD xxx..."""

        self.blank()
        wsp = ' '*(len(args)>0)
        cmd = self.prefix + cmd + wsp + args
        print (cmd)
        sys.stdout.flush()
        return 0

    def error(self, msg, severity=0):
        """ Basic error handler
            msg - string containing error message
            severity - integer.  If greater than one script exits"""
        sys.stderr.write(msg+'\n')
        if severity:
            sys.exit(severity)

    def write(self, msg):
        """ Very basic output writer
            msg - string to write to STDOUT"""
        print (msg)


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
        self.sendCmd('PAUSE', msg)
        self.STATUS = int(input())
        self.READANS = input()
        self.PAUSANS = input()
        return self.STATUS

    def MOUSE(self, msg, mode='p'):
        """ Genesis MOUSE command - pauses to allow user to select a location with the mouse - 
        returns STATUS as integer.  Sets class variables READANS and MOUSEANS to mouse location
            msg - message to put in dialog box
            mode - set to character 'p' or 'r'  p means to return a point, and r a rectangle (two points)"""
        self.sendCmd('MOUSE ' + mode, msg)
        self.STATUS = int(input())
        self.READANS = input()
        self.MOUSEANS = input()
        return self.STATUS

    def COM(self, args):
        """ Genesis COM command - all important command to issue script commands - returns STATUS
        and sets READANS as the command response raw input.  COMANS is the parsed READANS.  These are
        class variables
            args - string containing arguments for COM command (everything after COM)"""
        self.sendCmd('COM', args)
        self.STATUS = int(input())
        self.READANS = input()
        self.COMANS = self.READANS[:]
        return self.STATUS

    def AUX(self, args):
        """ Genesis AUX command - returns STATUS.  Sets class variables READANS 
        and COMANS, returns STATUS
            args - string containing arguments"""
        self.sendCmd('AUX', args)
        self.STATUS = int(input())
        self.READANS = input()
        self.COMANS = self.READANS[:]
        return self.STATUS

    # --- INFO methods ---

    #returns a list of results - process how you like
    def INFO(self, args):
        """ This is similar to the Genesis command COM(info,...) Returns list of strings which
        are lines from the output file
            args - string containing all the arguments to the info command 
                (that would be after the info,_*_)"""
        self.COM('info,out_file=%s,write_mode=replace,args=%s' % (self.tmpfile, args))
        lineList = []
        lineList_tmp = open(self.tmpfile, 'rb').readlines()
        for line_tmp in lineList_tmp:
            lineList.append(line_tmp.decode('utf-8',errors='ignore'))
        os.unlink(self.tmpfile)
        return lineList

    #returns a dictionary of results parsed out all fun
    def DO_INFO(self, args):
        """ This is the command COM info,...  returns a dictionary with all the information in the 
        output file from the info command.  Each array of information is accessed by a key to the
        dictionary that is returned. LIMITATION: Any string resembling a number will be converted
        to a number.  This means that a layer with the name '1.' or '1' will be returned later as
        the float 1.0
            args - arguments to the info command as a string"""
        self.COM('info,out_file=%s,write_mode=replace,args=%s' % (self.tmpfile, args))
        #self.PAUSE('Hi')
        lineList = []
        lineList_tmp = open(self.tmpfile, 'rb').readlines()
        print (lineList_tmp)
        for line_tmp in lineList_tmp:
            lineList.append(line_tmp.decode('utf-8',errors='ignore'))
        os.unlink(self.tmpfile)
        infoDict = self.parseInfo(lineList)
        return infoDict

    def DISP_INFO(self, args):
        """ This is similar to the DO_INFO but is run in 'display' mode and is parsed differently 
            - this method is not complete"""
        self.COM('info,out_file=%s,write_mode=replace,args=-m display %s' % (self.tmpfile, args))
        lineList = []
        lineList_tmp = open(self.tmpfile, 'rb').readlines()
        for line_tmp in lineList_tmp:
            lineList.append(line_tmp.decode('utf-8',errors='ignore'))
        os.unlink(self.tmpfile)
        infoDict = self.parseDispInfo(lineList)
        return infoDict

    # --- Utility commands ---
    def dbutil(self, *args):
        """ Runs the dbutil command with the specified arguments - returns lines from the response as
        array of strings args - arguments for dbutil command"""
        binary = os.path.join(self.edir, 'misc', 'dbutil')
        args = "".join(args)
        fd = os.popen(binary + ' '+args)
        res = fd.readlines()
        return res

    # Convert string to int or float if possible.
    def convertToNumber(self, value):
        """Utility function - converts string to a number returns integer if 
        possible - otherwise returns a float value - string to be converted"""
        #If there is a leading zero, and it isn't followed by a decimal (.) then don't
        #convert to a number
        #print "Value " + str(value)
        try:
            if value[0] == '0':
                if value[1] != '.':
                    return value
        except:
            pass

        #20240116 zl 数字间用_也会转成数字，导致返回的值有误
        if '_' in value:
            return value

        try:
            return int(value)
        except:
            try:
                return float(value)
            except:
                return value

    # Clean string of given character(s) on the edges
    def clean(self,strip_me,badchars):
        """ Internal - strips a string (strip_me) of given (badchars) on either edge - used in parsing"""
        badchars = badchars + ' \n'
        l = len(strip_me)
        if l < 1:
            return ""
        while(len(strip_me) > 0):
            if strip_me[0] in badchars:
                strip_me = strip_me[1:]
            else:
                break
        x = len(strip_me)-1
        for i in range(x):
            if strip_me[x-i] in badchars:
                strip_me = strip_me[:x-i]
            else:
                break
        return strip_me

    # Parse the output of an info command in "cshell" mode
    def parseInfo(self, infoList):
        """ Internal - parses the output from the info command into a dictionary - returns dictionary"""
        # Parses csh variable assignments and wordlists.
        # Example: set gTOOLnum = ('1' '2' '3' ) OR set gLIMITSxmin = '-10.708661'
        dict = {}
        for line in infoList:
            ss = line.split( ' = ', 1)
            #print "This is ss: "
            #print ss
            if len(ss) == 2:
                key = ss[0].strip()[4:]
                val = ss[1].strip()
                #print "This is key %s and this is val %s" % (key,val)
                if '(' in val:
                    valList = val.split("'")
                    # Wordlist example: ['(', '1', '   ', '2', '   ', '3', '   ', '4', '    )']
                    dict[key] = []
                    for n in range(len(valList)):
                        if n % 2 == 1:
                            # Append odd items to the list.
                            #print 'THIS IS VALLIST FOR ' + key,
                            #print valList
                            newval = self.clean(valList[n],"'")
                            dict[key].append(self.convertToNumber(newval))
                else:
                    # Single value example: ['test']
                    dict[key] = self.convertToNumber(self.clean(val,"'"))

        return dict

    # Parse the output of an info command in "display" mode
    def parseDispInfo(self, infoList):
        """Parses output from info command that was run in display mode. Incomplete"""
        mainDict = {}
        #print infoList
        for line in infoList:
                #print line
            line = line.strip()
            #print line
            try:
                exec(line)
            except SyntaxError:
                key = line.split('[')[0]
                if not key in list(mainDict.keys()):
                    exec('mainDict[\''+key+'\'] = []')

                vals = line.split(':')[1].split(',')
                dict = {}
                for val in vals:
                    ss = val.split('=')
                    try:
                        val = eval(ss[1])
                    except:
                        val = ss[1]
                    STR = 'dict[\''+ss[0]+'\'] = val'
                    exec(STR)
                exec('mainDict[\''+key+'\'].append(dict)')
        return mainDict

    # Parses the output of a features list (-d FEATURES)
    # Parses only lines, arcs, and pads, text, barcodes all with attribs.  Surfaces you are on your own...    
    # utilizes genFeatures.py
    def parseFeatureInfo(self, infoList):
        """Internal - Parses output from the info command when it writes out features.  Uses the genFeatures.py
        module and parses the information from this command (-d FEATURES) into class objects."""
        mainDict = {}

        lineList = []
        arcList = []
        padList = []
        textList = []
        barList = []

        # setup searches
        pat_line = re.compile("^#L")
        pat_arc = re.compile("^#A")
        pat_pad = re.compile("^#P")
        pat_text = re.compile("^#T")
        pat_bar = re.compile("^B")
        for line in infoList:
            line = line.strip()
            s_res = pat_line.search(line)
            if (s_res):
                lineObj = Line(line)
                lineList.append(lineObj)
                continue

            s_res = pat_arc.search(line)
            if (s_res):
                arcObj = Arc(line)
                arcList.append(arcObj)
                continue

            s_res = pat_pad.search(line)
            if (s_res):
                padObj = Pad(line)
                padList.append(padObj)
                continue

            s_res = pat_text.search(line)
            if (s_res):
                textObj = Text(line)
                textList.append(textObj)
                continue

            s_res = pat_bar.search(line)
            if (s_res):
                barObj = Barcode(line)
                barList.append(barObj)
                continue

        mainDict['lines'] = lineList
        mainDict['arcs'] = arcList
        mainDict['pads'] = padList
        mainDict['text'] = textList
        mainDict['barcodes'] = barList

        return mainDict

    #print the feature dictionary as text (used often for debugging)
    def printFeatureDict(self, features_dict):
        """ Used for debugging purposes, this prints out a dictionary created with the parseFeatureInfo command
            features_dict - dictionary returned by method parseFeatureInfo"""
        for x in range(len(features_dict['lines'])):
            print("Line " + str(x) + ": Shape-" + features_dict['lines'][x].shape + "", end=' ')
            print("Start: " + str(features_dict['lines'][x].xs) + "," + str(features_dict['lines'][x].ys) + " End: ", end=' ')
            print(str(features_dict['lines'][x].xe) + "," + str(features_dict['lines'][x].ye) + " Symb: ", end=' ')
            print(features_dict['lines'][x].symbol + " Length: " + str(features_dict['lines'][x].len) + " Pol: ", end=' ')
            print(features_dict['lines'][x].polarity + " Dcode: " + str(features_dict['lines'][x].dcode))
            print("Attr: ", end=' ')
            print(features_dict['lines'][x].attrs)
        for x in range(len(features_dict['arcs'])):
            print("Arc " + str(x) + ": Shape-" + features_dict['arcs'][x].shape + "", end=' ')
            print("Start: " + str(features_dict['arcs'][x].xs) + "," + str(features_dict['arcs'][x].ys) + " End: ", end=' ')
            print(str(features_dict['arcs'][x].xe) + "," + str(features_dict['arcs'][x].ye) + " Cent: ", end=' ')
            print(str(features_dict['arcs'][x].xc) + "," + str(features_dict['arcs'][x].yc) + " Symb: ", end=' ')
            print(features_dict['arcs'][x].symbol + " Pol: " + features_dict['arcs'][x].polarity + " Dcode: ", end=' ')
            print(str(features_dict['arcs'][x].dcode) + " Dir: " + features_dict['arcs'][x].direction)
            print("Attr: ", end=' ')
            print(features_dict['arcs'][x].attrs)
        for x in range(len(features_dict['pads'])):
            print("Pad " + str(x) + ": Shape-" + features_dict['pads'][x].shape + "", end=' ')
            print("Loc: " + str(features_dict['pads'][x].x) + "," + str(features_dict['pads'][x].y) + " Symb: ", end=' ')
            print(features_dict['pads'][x].symbol + " Pol: " + features_dict['pads'][x].polarity + " Dcode: ", end=' ')
            print(str(features_dict['pads'][x].dcode) + " Rot: " + str(features_dict['pads'][x].rotation) + " Mir: ", end=' ')
            print(str(features_dict['pads'][x].mirror))
            print("Attr: ", end=' ')
            print(features_dict['pads'][x].attrs)
        for x in range(len(features_dict['text'])):
            print("Text " + str(x) + ": Shape-" + features_dict['text'][x].shape + "", end=' ')
            print("Loc: " + str(features_dict['text'][x].x) + "," + str(features_dict['text'][x].y) + " Font: ", end=' ')
            print(features_dict['text'][x].font + " Pol: " + features_dict['text'][x].polarity + " Text: ", end=' ')
            print(features_dict['text'][x].text + "\n Rot: " + str(features_dict['text'][x].rotation) + " Mir: ", end=' ')
            print(str(features_dict['text'][x].mirror) + " Xsiz: " + str(features_dict['text'][x].xsize) + " Ysiz: ", end=' ')
            print(str(features_dict['text'][x].ysize) + " Wfact: " + str(features_dict['text'][x].wfactor) + " Ver: ", end=' ')
            print(str(features_dict['text'][x].version))
            print("Attr: ", end=' ')
            print(features_dict['text'][x].attrs)
        for x in range(len(features_dict['barcodes'])):
            print("Barcode " + str(x) + ": Shape-" + features_dict['barcodes'][x].shape + "", end=' ')
            print("Loc: " + str(features_dict['barcodes'][x].x) + "," + str(features_dict['barcodes'][x].y) + " Font: ", end=' ')
            print(features_dict['barcodes'][x].font + " Pol: " + features_dict['barcodes'][x].polarity + " Barcode: ", end=' ')
            print(features_dict['barcodes'][x].barcode + "\n Rot: " + str(features_dict['barcodes'][x].rotation) + " Constant: ", end=' ')
            print(str(features_dict['barcodes'][x].constant) + " Width: " + str(features_dict['barcodes'][x].width) + " Height: ", end=' ')
            print(str(features_dict['barcodes'][x].height) + "\n FullAscii: " + str(features_dict['barcodes'][x].full_ascii) + " Cksum: ", end=' ')
            print(str(features_dict['barcodes'][x].cksum) + " Invert BG: " + str(features_dict['barcodes'][x].invert_bg) + "\n addTxt: ", end=' ')
            print(str(features_dict['barcodes'][x].add_text) + " TextLoc: " + features_dict['barcodes'][x].text_loc + " Text: ", end=' ')
            print(features_dict['barcodes'][x].text)
            print("Attr: ", end=' ')
            print(features_dict['barcodes'][x].attrs)

    def piontList(self, piontListTemp = [],tolerance = 0.5):                   #解析从INFO中读取的线条信息 解析成一条直线
        piontList = []
        for line in piontListTemp:
            line[0],line[1] = float(line[0]),float(line[1])
            if line[0] > line[1]:
                line[0],line[1] = line[1],line[0]
            piontList.append(line)

        piontListTemp = []
        while piontList:                                                      #用列表做循环变量 列表数据被取完之后 就停止循环
            if len(piontList) == 1:                                           #如果只有最后一个数 无法循环 直接添加进列表
                piontListTemp.append(piontList[0])
                break
            line = piontList[0]                                               #取出第一个值
            del piontList[0]                                                  #删掉第一个值
            count = -1                                                        #计数
            while piontList:                                                  #二次循环
                count += 1
                term_1 = piontList[count][0] <= line[0] <= piontList[count][1] #下面4行找任何一个坐标在另一线段中被包含或相等
                term_2 = piontList[count][0] <= line[1] <= piontList[count][1]
                term_3 = line[0] <= piontList[count][0] <= line[1]
                term_4 = line[0] <= piontList[count][1] <= line[1]
                if term_1 or term_2 or term_3 or term_4:                       #如果找到任何一个坐标 把这两个坐标取出最大值 并从头开始循环
                    line = (min(piontList[count][0],line[0],line[1],piontList[count][1]),max(piontList[count][0],line[0],line[1],piontList[count][1])) #取最小和小大值给line 用于和其他值再比较
                    del piontList[count]                                       #找到任何一个坐标时将坐标从列表中删除
                    if len(piontList) == 0:                                    #当只有最后一个坐标时无法循环 直接在这里判断并返回到列表中
                        piontListTemp.append(line)
                    count = -1                                                 #找到任何一个坐标后 要从头开始循环 重置计数器
                    continue                                                   #开始下一次循环
                else:                                                          #如果一个坐标都没有找到
                    if count < len(piontList)-1:                               #计数器必须比当前列表小 否则会越界
                        continue                                               #如果没有找到坐标 且计数器比列表小 开始下一次循环 计数器开始累加
                piontListTemp.append(line)                                     #到这里一轮循环跑完都没有找到任何一个坐标的话 就将这个最小和最大坐标加入临时列表 就找到一组坐标了
                break                                                          #退出当前循环 开始上一级循环

        piontList = []
        for coor in piontListTemp:
            piontList.append(round(coor[0]*25.4,3))
            piontList.append(round(coor[1]*25.4,3))
        piontList.sort()

        piontListTemp = []
        for coor in range(len(piontList)//2):
            piontListTemp.append(piontList[coor * 2:coor * 2+2])

                                                                                                           #设置公差 小于设置公差间距的合并为一条线
        piontList = []
        while piontListTemp:                                                      #用列表做循环变量 列表数据被取完之后 就停止循环
            if len(piontListTemp) == 1:                                           #如果只有最后一个数 无法循环 直接添加进列表
                piontList.append(piontListTemp[0])
                break
            line = piontListTemp[0]                                               #取出第一个值
            del piontListTemp[0]                                                  #删掉第一个值
            count = -1                                                        #计数
            while piontListTemp:                                                  #二次循环
                count += 1
                if piontListTemp[count][0] - line[1] <= tolerance:
                    line = (min(piontListTemp[count][0],line[0],line[1],piontListTemp[count][1]),max(piontListTemp[count][0],line[0],line[1],piontListTemp[count][1])) #取最小和小大值给line 用于和其他值再比较
                    del piontListTemp[count]                                  #找到任何一个坐标时将坐标从列表中删除
                    if len(piontListTemp) == 0:                               #当只有最后一个坐标时无法循环 直接在这里判断并返回到列表中
                        piontList.append(line)
                    count = -1                                                 #找到任何一个坐标后 要从头开始循环 重置计数器
                    continue                                                   #开始下一次循环
                else:                                                          #如果一个坐标都没有找到
                    if count < len(piontListTemp)-1:                               #计数器必须比当前列表小 否则会越界
                        continue                                               #如果没有找到坐标 且计数器比列表小 开始下一次循环 计数器开始累加
                piontList.append(line)                                      #到这里一轮循环跑完都没有找到任何一个坐标的话 就将这个最小和最大坐标加入临时列表 就找到一组坐标了
                break

        return piontList

    def singlePiont(self,piontList_Temp,tolerance = 0.2):                      #提供一个单数的列表 返回公差范围内的中值 提供inch 返回mm
        piontListTemp = []
        for i in piontList_Temp:
            i = round(float(i)*25.4,3)
            piontListTemp.append(i)
        piontListTemp.sort()
        piontList = []
        piontList_arry = []
        piontList_arry.append(piontListTemp[0])
        for x in range(len(piontListTemp)-1):
            if (piontListTemp[x+1] - piontListTemp[x]) <= tolerance:
                piontList_arry.append(piontListTemp[x+1])
                if x+1 == len(piontListTemp)-1:
                    piontList.append(piontList_arry)
                continue
            else:
                piontList.append(piontList_arry)
                piontList_arry = []
                piontList_arry.append(piontListTemp[x+1])
        piontList_Temp = []
        for n in piontList:
            n = round(((max(n) + min(n)) / 2),3)
            piontList_Temp.append(n)
        return piontList_Temp

    def getUser(self):
        """ Returns the name, as a string, of the current user"""
        self.COM('get_user_name')
        self.user = self.COMANS
        return self.user

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
        for x in range(len(self.info['gATTRname'])):
            if self.info['gATTRname'][x] == name:
                return self.info['gATTRval'][x]
            if self.info['gATTRname'][x] == '.'+name:
                return self.info['gATTRval'][x]
        return None

class Top(Genesis):
    """ This class can be used to find out status about Genesis on the main DB level, and do top level functions
     What jobs are open, etc."""
    def __init__(self):
        Genesis.__init__(self)

    def __str__(self):
        """Returns string describing class - also what is printed if print method called on class object"""
        return 'genClasses status class instance'

    def __getattr__(self, item):
        if item == 'user':
            self.user = self.getUser()
            return self.user

    def currentJob(self):
        """ If in a job, this method returns that job as a string"""
        if 'JOB' in list(os.environ.keys()):
            return os.environ['JOB']
        else:
            return ''

    def createJob(self,name,db_name):
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
            print("Some error in creating job " + name + " in db " + db_name)

        job = Job(name)
        job.close(1)

        return job

    # 20231207 zl 复制料号
    def copyJob(self, name, dbname, dbase='db253'):
        joblist = self.listJobs()
        if name in joblist and dbname not in joblist:
            self.COM('copy_entity,type=job,source_job=' + name + ',source_name=' + name + ',dest_job=' + dbname + ',dest_name=' + dbname + ',dest_database=' + dbase)
            return self.STATUS
        return -1

    def deleteJob(self,name):
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
        #self.PAUSE(" Job not found:" + name)
        return -1

    def importJob(self,name,import_dir,db_name,analyze,verify):
        """ Import an ODB++/Valor format job - returns status.
            name - name to give new job
            import_dir - directory from which to import
            db_name - database it will reside in"""

        STR = 'import_job,db=%s,path=%s,name=%s,analyze_surfaces=%s,verify_tgz=%s' % (db_name,import_dir,name,analyze,verify)
        self.COM(STR)

        return self.STATUS

    def exportJob(self,job,export_dir):
        """ Export Tgz - returns status.
            name - name to give exist job
            Export_dir - directory from which to Export
            s"""

        STR = 'export_job,job=%s,path=%s,mode=tar_gzip,submode=full,overwrite=yes' % (job,export_dir)
        self.COM(STR)

        return self.STATUS

    def currentStep(self):
        """ If in a step, return the step name as a string"""
        if 'STEP' in list(os.environ.keys()):
            return os.environ['STEP']
        else:
                return ''

    def openJobs(self):
        """ Returns a list of open jobs, as a list of strings"""
        jobList = self.DO_INFO('-t root')['gJOBS_LIST']
        openJobList=[]
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
        user = self.COMANS
        return user

# Defines the job-level class
#  Must  supply the job name.
class Job(Genesis,ExtraStuff,JobCmds):
    """ This class is ised to represent a job object in the Genesis database.  It is used to open, close, and manipulate
    jobs.  Other classes representing steps, forms, matrices, etc, can be contained by this class."""
    def __init__(self, name):
        self.name = name
        Genesis.__init__(self)

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
        initial request    of an attribute. e.g. <class instance>.attribute 
        
        If the attribute is in this method, it is handled by methods defined here, 
        otherwise the Genesis job object associated with this instance is inspected 
        for a corresponding Genesis attribute; the value of which is stored in the 
        instance attribute.
        
        Special Attributes Supported:  matrix, info, steps, forms, db, dbpath, lockStat, user, bucket, xmlbucket
        """

        print('Dynamically fetching Job attribute::',name)
        if name == 'matrix':
            self.matrix = Matrix(self)
            return self.matrix
        elif name == 'SignalDict':
            self.SignalDict = self.getSignalLayers()
            return self.SignalDict
        elif name == 'SignalNum':
            self.SignalNum = self.SignalDict.get('num')
            return self.SignalNum
        elif name == 'SignalLayers':
            self.SignalLayers = self.SignalDict.get('layers')
            return self.SignalLayers
        elif name == 'dependentsteps':
            self.dependentsteps = self.getDependentSteps()
            return self.dependentsteps
        elif name == 'flipsteps':
            self.flipsteps = self.dependentsteps.get('flip')
            return self.flipsteps
        elif name == 'rotatesteps':
            self.rotatesteps = self.dependentsteps.get('rotate')
            return self.rotatesteps
        elif name == 'info':
            self.info = self.getInfo()
            return self.info
        elif name == 'steps':
            self.steps = self.getSteps()
            return self.steps
        elif name == 'stepsList':
            self.stepsList_temp = self.getInfo()["gSTEPS_LIST"]
            self.stepsList = []
            for step in self.stepsList_temp:
                self.stepsList.append(str(step))
            return  self.stepsList
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
        elif name == 'throughdrill':
            self.throughdrill = self.getThroughDrill()
            return self.throughdrill
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
        print("Running getinfo")
        self.info = self.DO_INFO('-t job -e '+self.name)
        return self.info

    def getSteps(self):
        """ Populates the <inst>.steps dictionary with Step classes representing each step.  Use to update
        the job class's representation of its steps"""
        self.steps = {}
        print("Running getsteps")
        for step in self.info["gSTEPS_LIST"]:
            self.steps[str(step)] = Step(self, str(step))
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
        self.db = res[0].split()[3]
        return self.db

    def dbPath(self):
        """ Returns the file path to the job.  Populates <inst>.dbpath"""
        res = self.dbutil('path', 'jobs', str(self.name))
        self.dbpath = res[0].split()
        return self.dbpath

    def dbStat(self):
        """ Returns the lock status.  Populates <inst>.lockStat """
        res = self.dbutil('lock', 'test', self.name)
        ss = res[0].split()
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

    # 20210913 zl  更新依赖步update_dependent_step
    def updateDependentStep(self, step):
        STR = 'update_dependent_step,job=' + self.name +',step=' + str(step)
        self.COM(STR)
        return self.STATUS
    # 网络分析  compare
    def net_recalc(self,job='',step='',type='cur',display='top'):
        if not job:
            job = self.name
        STR = 'netlist_recalc,job=%s,step=%s,type=%s,display=%s,layer_list=' % (job, step, type,display)
        self.VOF()
        self.COM(STR)
        return self.STATUS
        self.VON()

    def net_control(self,filter1='',filter2=''):
        if filter1:
            self.COM("netlist_control,filter1=%s" % filter1)
        else:
            self.COM("netlist_control,filter2=%s" % filter2)
    def net_compare(self,job2='',step1='',type1='cur',step2='',type2='cur'):
        if not job2:
            job2 = self.name
        STR = 'netlist_compare,job1=%s,step1=%s,type1=%s,job2=%s,step2=%s,type2=%s,display=yes,' \
              'filter_ignore_net_names=no,filter_cad_problem=no,filter_nfp=no,filter_attr_diff=no,' \
              'filter_extra_on_pad=no,filter_backdrill=no' % (self.name,step1, type1, job2, step2, type2)
        self.COM(STR)
        return self.STATUS
    # report
    def net_result(self,output='screen',out_file=''):
        if output == 'screen':
            STR = 'netlist_save_compare_results,output=screen'
        if output == 'file' and out_file:
            STR = 'netlist_save_compare_results,out_file=%s,output=file' % (out_file)
        else:
            return
        self.COM(STR)
        return self.STATUS
    # 网络分析  Per Layers
    def net_partial_compare(self,job2='',step1='',type1='cur',layer_list1='',step2='',type2='cur',layer_list2=''):
        if not job2:
            job2 = self.name
        if not layer_list2:
            layer_list2 = layer_list1
        STR = 'netlist_partial_compare,job1=%s,step1=%s,type1=%s,layer_list1=%s\;,job2=%s,step2=%s,type2=%s,layer_list2=%s\;,batch_mode=yes,display=yes' % (self.name, step1, type1, layer_list1, job2, step2, type2,layer_list2)
        self.VOF()
        self.COM(STR)
        return self.STATUS
        self.VON()
    # report
    def net_partial_result(self, output='screen', out_file=''):
        if output == 'screen':
            STR = 'netlist_save_partial_compare_results,output=screen'
        if output == 'file' and out_file:
            STR = 'netlist_save_partial_compare_results,out_file=%s,output=file' % (out_file)
        else:
            return
        self.COM(STR)
        return self.STATUS
    # 取正式层
    def getSignalLayers(self):
        signal_dict = {}
        signal_layers = []
        rows = self.matrix.returnRows('board', 'signal|power_ground')
        signal_num = 0
        for row in rows:
            if re.match('^cs$|^ss$|^in\d+$|^pg\d+$',row):
                signal_num +=1
                signal_layers.append(row)
        signal_dict['num'] = signal_num
        signal_dict['layers'] = signal_layers
        return signal_dict
    # 取旋转和翻转的step
    def getDependentSteps(self):
        dependentSteps = {}
        flipSteps,rotateSteps,flipVals,rotateVals = [],[],[],[]
        for step in self.steps.values():
            for index, rname in enumerate(step.info['gATTRname']):
                attrval = step.info['gATTRval'][index]
                if rname == '.flipped_of' and attrval != '':
                    flipSteps.append(step.name)
                    flipVals.append(attrval)
                if rname == '.rotated_of' and attrval != '':
                    rotateSteps.append(step.name)
                    rotateVals.append(attrval)
        dependentSteps['flip'] = flipSteps
        dependentSteps['rotate'] = rotateSteps
        dependentSteps['flipval'] = flipVals
        dependentSteps['rotateval'] = rotateVals
        return dependentSteps

    ########### Services ##########
    # 20220209 zl  业务方法
    # 取该料号的内层线路
    def getInnerLayer(self):
        lays = []
        if self.SignalNum > 2:
            for i in range(2,self.SignalNum):
                lays.append('in' + str(i))
        return lays
    ##内层芯板层
    def getCoreLay(self):
        lays = []
        if self.SignalNum > 3:
            lays.append('in' + str(int(self.SignalNum/2)))
            lays.append('in' + str(int(self.SignalNum/2 + 1)))
        return lays
    # ###内层芯板对应的cov层
    def getInCov(self):
        lays = []
        if self.SignalNum > 3:
            lays.append('cov-' + str(int(self.SignalNum / 2)))
            lays.append('cov-' + str(int(self.SignalNum / 2 + 1)))
        return lays
    #获取内层top和内层bot
    def getInLay_top_bot(self):
        resdic = {}
        # 找最里面钻孔层
        drill_lays = self.matrix.returnRows('board', 'drill')
        if self.SignalNum < 3 or self.SignalNum % 2:
            return resdic
        resdic = { 'inLay_top': [], 'inLay_bot': [] }
        median = int(self.SignalNum/2)
        # 最里面钻孔层对应的序号
        drill_top = 1
        drill_bot = self.SignalNum
        for i in range(median,1,-1):
            lay = 'drill%s-%s' % (i, self.SignalNum + 1 - i)
            if lay in drill_lays:
                drill_top = i
                drill_bot = self.SignalNum + 1 - i
                break
        # 开始找内层top和bot
        if drill_top != 1:
            resdic['inLay_top'].append('in'+ str(drill_top))
            resdic['inLay_bot'].append('in'+ str(drill_bot))
        # 次外层
        # top层往上为top bot层往下为bot
        if drill_top > 2:
            for i in range(2,drill_top):
                resdic['inLay_top'].append('in%s' % i)
            for i in range(self.SignalNum - 1,drill_bot,-1):
                resdic['inLay_bot'].append('in%s' % i)
        # 内层
        # top层到bot层，交替为内层top/内层bot
        pos = 1
        for i in range(drill_top + 1 ,drill_bot):
            if pos%2:
                resdic['inLay_top'].append('in%s' % i)
            else:
                resdic['inLay_bot'].append('in%s' % i)
            pos += 1
        return resdic

    # 取埋孔
    def getBuriedLay(self):
        buried_lays = []
        drill_lays = self.matrix.returnRows('board', 'drill')
        if self.SignalNum < 5 or self.SignalNum % 2:
            return buried_lays
        # 通孔层
        # through_drill = 'drill1-'+ str(self.SignalNum)
        # for i in range(1,self.SignalNum):
        #     for j in range(i + 2, self.SignalNum + 1):
        #         if 'drill%s-%s' % (i, j) in drill_lays:
        #             buried_lays.append('drill%s-%s' % (i, j))
        # # 去掉通孔层
        # if through_drill in buried_lays:
        #     buried_lays.remove(through_drill)
        # 20221115 埋孔指埋在里面的孔  如六层板为2-5   八层板为2-7 3-6
        for i in range(2,int(self.SignalNum/2)):
            j = self.SignalNum + 1 - i
            if 'drill%s-%s' % (i, j) in drill_lays:
                buried_lays.append('drill%s-%s' % (i, j))
        return buried_lays

    # 取盲孔
    def getBlindLay(self):
        blind_lays = []
        drill_lays = self.matrix.returnRows('board', 'drill')
        if self.SignalNum < 3 or self.SignalNum % 2:
            return blind_lays
        for i in range(1, self.SignalNum):
            if 'drill%s-%s' % (i, i + 1) in drill_lays:
                blind_lays.append('drill%s-%s' % (i, i + 1))
        return blind_lays

    # 获取有改动的层
    def getChangeLays(self, boardlay=1):
        """
        获取料号有改动的层
        [[step,lay]..]
        """
        info = self.INFO('-t job -e %s -d CHANGES' % self.name)
        List = []
        for line in info:
            line = line.strip()
            if line:
                m = re.search(r'^step\s+=\s(\S+)\s+,\slayer\s+=\s(\S+)[\s ,]', line)
                if m and [m.group(1), m.group(2)] not in List:
                    List.append([m.group(1), m.group(2)])
        if boardlay == 1:  # 只取board层
            new_list = []
            board_lay_list = self.matrix.returnRows('board')
            for line in List:
                if line[1] in board_lay_list:
                    new_list.append(line)
            return new_list
        else:  # 所有层
            return List

    # 通孔层
    def getThroughDrill(self):
        throughdrill = 'drill1-%s' % self.SignalNum
        if throughdrill in self.matrix.returnRows('board', 'drill'):
            return throughdrill
        else:
            return None

class Step(Genesis,ExtraStuff,StepCmds):
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
        self.name = name
        self.group = None

        # Check if I really exist as a step
#        d = self.DO_INFO('-t step -e '+self.job.name+'/'+self.name+' -d exists')
#        if d['gEXISTS'] == 'no':
#            self.error('Non-existent step::'+self.name, 1)

    def COM(self, args):
        """ Overloading method, to set group automatically - in the graphic editor"""
        if self.group:
            self.setGroup()
        self.sendCmd('COM', args)
        self.STATUS = int(input())
        self.READANS = input()
        self.COMANS = self.READANS[:]
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
        initial request    of an attribute. e.g. <class instance>.attribute 
        
        If the attribute is in this method, it is handled by methods defined here, 
        otherwise the Genesis job object associated with this instance is inspected 
        for a corresponding Genesis attribute; the value of which is stored in the 
        instance attribute.
        
        Special Attributes Supported:  info, profile, layers, sr, datum, checks    
        """
        print('Dynamically fetching Step attribute::',name)
        if name == 'info':
            self.info = self.getInfo()
            return self.info
        elif name == 'info2':
            self.info2 = self.getInfo2()
            return self.info2
        elif name == 'profile':
            self.profile = self.getProfile()
            return self.profile
        elif name == 'profile2':
            self.profile2 = self.getProfile2()
            return self.profile2
        elif name == 'layers':
            self.layers = self.getLayers()
            return self.layers
        elif name == 'layersList':
            self.layersList = []
            for layer in self.getInfo()["gLAYERS_LIST"]:
                self.layersList.append(str(layer))
            return self.layersList
        elif name == 'sr':
            self.sr = self.getSr()
            return self.sr
        elif name == 'sr2':
            self.sr2 = self.getSr2()
            return self.sr2
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

    def setUnits(self,units):
        self.COM("units,type=%s" % (units))

    def getUnits(self):
        self.COM("get_units")
        return self.COMANS

    def getInfo(self):
        """ Build the self.info dictionary... Doesn't do a full command (excluding -d from info command) 
        because it does LIMITS, which takes forever!  Returns <inst>.info"""
        self.info = {}
        self.tmp = self.DO_INFO('-t step -e '+self.job.name+'/'+str(self.name) + ' -d LAYERS_LIST')
        self.info.update(self.tmp)
        self.tmp = self.DO_INFO('-t step -e '+self.job.name+'/'+str(self.name) + ' -d CHECKS_LIST')
        self.info.update(self.tmp)
        self.tmp = self.DO_INFO('-t step -e '+self.job.name+'/'+str(self.name) + ' -d NETS_LIST')
        self.info.update(self.tmp)
        self.tmp = self.DO_INFO('-t step -e '+self.job.name+'/'+str(self.name) + ' -d CHECKS_LIST')
        self.info.update(self.tmp)
        self.tmp = self.DO_INFO('-t step -e '+self.job.name+'/'+str(self.name) + ' -d ACTIVE_AREA')
        self.info.update(self.tmp)
        self.tmp = self.DO_INFO('-t step -e '+self.job.name+'/'+str(self.name) + ' -d NUM_SR')
        self.info.update(self.tmp)
        self.tmp = self.DO_INFO('-t step -e '+self.job.name+'/'+str(self.name) + ' -d SR')
        self.info.update(self.tmp)
        self.tmp = self.DO_INFO('-t step -e '+self.job.name+'/'+str(self.name) + ' -d SR_LIMITS')
        self.info.update(self.tmp)
        self.tmp = self.DO_INFO('-t step -e '+self.job.name+'/'+str(self.name) + ' -d NUM_REPEATS')
        self.info.update(self.tmp)
        self.tmp = self.DO_INFO('-t step -e '+self.job.name+'/'+str(self.name) + ' -d PROF_LIMITS')
        self.info.update(self.tmp)
        self.tmp = self.DO_INFO('-t step -e '+self.job.name+'/'+str(self.name) + ' -d PROF')
        self.info.update(self.tmp)
        self.tmp = self.DO_INFO('-t step -e '+self.job.name+'/'+str(self.name) + ' -d DATUM')
        self.info.update(self.tmp)
        self.tmp = self.DO_INFO('-t step -e '+self.job.name+'/'+str(self.name) + ' -d REPEAT')
        self.info.update(self.tmp)
        self.tmp = self.DO_INFO('-t step -e '+self.job.name+'/'+str(self.name) + ' -d ATTR')
        self.info.update(self.tmp)
        return self.info
    # 单位为mm的info 20211018 zl
    def getInfo2(self):
            self.info2 = {}
            self.tmp = self.DO_INFO('-t step -e ' + self.job.name + '/' + str(self.name) + ' -d LAYERS_LIST,units=mm')
            self.info2.update(self.tmp)
            self.tmp = self.DO_INFO('-t step -e ' + self.job.name + '/' + str(self.name) + ' -d CHECKS_LIST,units=mm')
            self.info2.update(self.tmp)
            self.tmp = self.DO_INFO('-t step -e ' + self.job.name + '/' + str(self.name) + ' -d NETS_LIST,units=mm')
            self.info2.update(self.tmp)
            self.tmp = self.DO_INFO('-t step -e ' + self.job.name + '/' + str(self.name) + ' -d CHECKS_LIST,units=mm')
            self.info2.update(self.tmp)
            self.tmp = self.DO_INFO('-t step -e ' + self.job.name + '/' + str(self.name) + ' -d ACTIVE_AREA,units=mm')
            self.info2.update(self.tmp)
            self.tmp = self.DO_INFO('-t step -e ' + self.job.name + '/' + str(self.name) + ' -d NUM_SR,units=mm')
            self.info2.update(self.tmp)
            self.tmp = self.DO_INFO('-t step -e ' + self.job.name + '/' + str(self.name) + ' -d SR,units=mm')
            self.info2.update(self.tmp)
            self.tmp = self.DO_INFO('-t step -e ' + self.job.name + '/' + str(self.name) + ' -d SR_LIMITS,units=mm')
            self.info2.update(self.tmp)
            self.tmp = self.DO_INFO('-t step -e ' + self.job.name + '/' + str(self.name) + ' -d NUM_REPEATS,units=mm')
            self.info2.update(self.tmp)
            self.tmp = self.DO_INFO('-t step -e ' + self.job.name + '/' + str(self.name) + ' -d PROF_LIMITS,units=mm')
            self.info2.update(self.tmp)
            self.tmp = self.DO_INFO('-t step -e ' + self.job.name + '/' + str(self.name) + ' -d PROF,units=mm')
            self.info2.update(self.tmp)
            self.tmp = self.DO_INFO('-t step -e ' + self.job.name + '/' + str(self.name) + ' -d DATUM,units=mm')
            self.info2.update(self.tmp)
            self.tmp = self.DO_INFO('-t step -e ' + self.job.name + '/' + str(self.name) + ' -d REPEAT,units=mm')
            self.info2.update(self.tmp)
            self.tmp = self.DO_INFO('-t step -e ' + self.job.name + '/' + str(self.name) + ' -d ATTR,units=mm')
            self.info2.update(self.tmp)
            return self.info2

    # Build the profile object
    def getProfile(self):
        """ Retrieves profile limits and places in <inst>.profile class. Access
        values by <stepinst>.profile.xmin (xmax, ymin, ymax, xsize, ysize, xcenter, ycenter)"""
        print('Getting Profile...')
        self.profile = Empty()
        self.profile.xmin = self.info['gPROF_LIMITSxmin']
        self.profile.ymin = self.info['gPROF_LIMITSymin']
        self.profile.xmax = self.info['gPROF_LIMITSxmax']
        self.profile.ymax = self.info['gPROF_LIMITSymax']
        self.profile.xsize = self.profile.xmax - self.profile.xmin
        self.profile.ysize = self.profile.ymax - self.profile.ymin
        self.profile.xcenter = self.profile.xmin + self.profile.xsize / 2
        self.profile.ycenter = self.profile.ymin + self.profile.ysize / 2
        return self.profile
    # 自定义单位返回profile 20211018 zl
    def getProfile2(self):
        """ Retrieves profile limits and places in <inst>.profile class. Access
                values by <stepinst>.profile.xmin (xmax, ymin, ymax, xsize, ysize, xcenter, ycenter)"""
        print('Getting Profile...')
        self.profile2 = Empty()
        self.profile2.xmin = self.info2['gPROF_LIMITSxmin']
        self.profile2.ymin = self.info2['gPROF_LIMITSymin']
        self.profile2.xmax = self.info2['gPROF_LIMITSxmax']
        self.profile2.ymax = self.info2['gPROF_LIMITSymax']
        self.profile2.xsize = self.profile2.xmax - self.profile2.xmin
        self.profile2.ysize = self.profile2.ymax - self.profile2.ymin
        self.profile2.xcenter = self.profile2.xmin + self.profile2.xsize / 2
        self.profile2.ycenter = self.profile2.ymin + self.profile2.ysize / 2
        return self.profile2

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
        self.sr.num_sr = self.info['gNUM_SR']
        self.sr.RBorder = self.profile.xmax - self.sr.xmax
        self.sr.LBorder = self.sr.xmin - self.profile.xmin
        self.sr.TBorder = self.profile.ymax - self.sr.ymax
        self.sr.BBorder = self.sr.ymin - self.profile.ymin
        self.sr.table = []
        for x in range(len(self.info['gSRstep'])):
            d     = Empty()
            d.step    = self.info['gSRstep'][x]
            d.xanchor = self.info['gSRxa'][x]
            d.yanchor = self.info['gSRya'][x]
            d.xdist   = self.info['gSRdx'][x]
            d.ydist   = self.info['gSRdy'][x]
            d.xnum    = self.info['gSRnx'][x]
            d.ynum    = self.info['gSRny'][x]
            d.angle   = self.info['gSRangle'][x]
            d.mirror  = self.info['gSRmirror'][x]
            d.xmin    = self.info['gSRxmin'][x]
            d.ymin    = self.info['gSRymin'][x]
            d.xmax    = self.info['gSRxmax'][x]
            d.ymax    = self.info['gSRymax'][x]
            self.sr.table.append(d)

        return self.sr

    def getSr2(self):
        """ Builds <inst>.sr object and returns it.  This is the step & repeat limits.
        The numbers it generates are accessed in dot notation as well (like profile)
        (srLimits:L xmin, xmax, ymin, ymax, eBorder, wBorder, nBorder, sBorder, table)
        (Table contains list entries, each with access to each instance using dot
        notation - step, xanchor, yanchor, xdist, ydist, xnum, ynum, angle, mirror,
        xmin, xmax, ymin, ymax.  Accessed as sr.table[x].xmax, etc."""
        self.sr2 = Empty()
        self.sr2.xmin = self.info2['gSR_LIMITSxmin']
        self.sr2.ymin = self.info2['gSR_LIMITSymin']
        self.sr2.xmax = self.info2['gSR_LIMITSxmax']
        self.sr2.ymax = self.info2['gSR_LIMITSymax']
        self.sr2.num_sr = self.info2['gNUM_SR']
        self.sr2.RBorder = self.profile2.xmax - self.sr2.xmax
        self.sr2.LBorder = self.sr2.xmin - self.profile2.xmin
        self.sr2.TBorder = self.profile2.ymax - self.sr2.ymax
        self.sr2.BBorder = self.sr2.ymin - self.profile2.ymin
        self.sr2.table = []
        for x in range(len(self.info2['gSRstep'])):
            d = Empty()
            d.step = self.info2['gSRstep'][x]
            d.xanchor = self.info2['gSRxa'][x]
            d.yanchor = self.info2['gSRya'][x]
            d.xdist = self.info2['gSRdx'][x]
            d.ydist = self.info2['gSRdy'][x]
            d.xnum = self.info2['gSRnx'][x]
            d.ynum = self.info2['gSRny'][x]
            d.angle = self.info2['gSRangle'][x]
            d.mirror = self.info2['gSRmirror'][x]
            d.xmin = self.info2['gSRxmin'][x]
            d.ymin = self.info2['gSRymin'][x]
            d.xmax = self.info2['gSRxmax'][x]
            d.ymax = self.info2['gSRymax'][x]
            self.sr2.table.append(d)

        return self.sr2
    def getLayers(self):
        """ Builds a dictionary of all the layers in the step.  This dictionary 
        points to Layer classes as defined in this module."""
        self.layers = {}
        print("Running getLayers")
        for layName in self.info["gLAYERS_LIST"]:
            self.layers[str(layName)] = Layer(self, str(layName))
        return self.layers

    def getChecks(self):
        """ Builds a dictionary of all the checklists in the step.  It points to checklist
        classes, as defined in this module"""
        self.checks = {}
        print("Running getChecks to retrieve checklist names")
        for checkName in self.info['gCHECKS_LIST']:
            self.checks[checkName] = Checklist(self, checkName)
        return self.checks

    def getDatum(self):
        """ Creates datum dictionary.  <inst>.datum['x'] or ['y']"""
        self.datum = {'x' : 0.0, 'y' : 0.0}
        d = self.DO_INFO('-t step -e '+self.job.name+'/'+str(self.name)+' -d DATUM')
        self.datum['x'] = d['gDATUMx']
        self.datum['y'] = d['gDATUMy']
        return self.datum

    def isLayer(self,layer_name='misc'):
        """ Method to check for a single layer.  Sometimes faster than doing a key search on the
        layers dictionary  Returns 1 if exists, 0 if not.
            layer_name = String representing the name of the layer"""
        #print "Checking for layer :|" + layer_name + "|"
        d = self.DO_INFO(args='-t layer -e '+self.job.name + '/' + str(self.name) + '/' + str(layer_name) + ' -d exists')
        #print "This is existence: |" + d['gEXISTS'] + "|"
        if d['gEXISTS'] == 'no':
            return 0
        else:
            return 1

    def setGroup(self):
        """ Sets AUX group to current editor"""
        self.AUX('set_group,group='+self.group)

    def Features_INFO(self,Layer = "",mode = "select"):
        piont = self.INFO(' -t layer -e '+self.job.name+'/'+str(self.name)+'/%s -d FEATURES -o %s' % (Layer,mode))
        del piont[0]
        coor = []
        for line in piont:
            coor.append(line.split())
        return coor
    # 旋转step     angle旋转角度  rotated_step旋转后的step名 mode旋转中心 outputname
    def rotateStep(self,angle,rotated_step='',mode='datum',outputname=''):
        anchor_x = 0
        anchor_y = 0
        units = self.getUnits()
        if mode == 'center':
            anchor_x = self.profile2.xcenter
            anchor_y = self.profile2.ycenter
        STR = 'rotate_step,job=%s,step=%s,rotated_step=%s,angle=%s,mode=%s,units=%s,anchor_x=%s,anchor_y=%s' % (self.job.name,self.name,rotated_step,angle,mode,units,anchor_x,anchor_y)
        self.COM(STR)
        if outputname:
            self.COM('set_out_name_attr,job=%s,step=%s,value=%s' % (self.job.name,rotated_step,outputname))

    # 初始化当前step
    def initStep(self):
        self.open()
        self.setGroup()
        self.clearAll()
        self.clearAndReset()
        self.zoomHome()
        self.COM(" display_width,mode=on ")
        self.COM(" negative_data,mode=clear ")
        self.COM(" display_sr,display=no ")
        self.COM(" sel_options,clear_mode=clear_after,display_mode=all_layers,area_inout=inside,area_select=select ")
        self.COM(" cur_atr_reset ")
        self.COM(" display_grid,mode=off ")
        self.COM(" display_grid,mode=off,xgrid=0.1,ygrid=0.1 ")
        self.COM(" snap_mode,mode=off ")
        self.COM(" units,type=mm")


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
        STR = 'show_form,job=' + self.job.name + ',form=' + str(self.name) + ',updonly=No'
        self.COM(STR)
        return self.STATUS

    def close(self):
        """ Closes the form"""
        STR = 'close_form,job=' + self.job.name + ',form=' + str(self.name)
        self.COM(STR)
        return self.STATUS

    def delete(self):
        """ Deletes this form """
        STR = 'delete_form,job=' + self.job.name + ',form=' + str(self.name)
        self.COM(STR)
        del self.job.forms[self.name]
        return self.STATUS

    def read(self, field):
        """ Reads a form element, with opt_name set to no (i.e. gives selected column for options, not option name)
            field - string containing name of form element to read"""
        STR = 'read_form,job=' + self.job.name + ',form=' + str(self.name) + ',elem=' + field + ',opt_name=no'
        self.COM(STR)
        return self.COMANS

    def readOpt(self, field):
        """ Reads a form element with opt_name set to yes (i.e. gives option value, not which column)
            field - string containing name of form element to read"""
        STR = 'read_form,job=' + self.job.name + ',form=' + str(self.name) + ',elem=' + field + ',opt_name=yes'
        self.COM(STR)
        return self.COMANS

    def write(self, field, value, color = ''):
        """ write value into field 
            field - string with name of form element
            value - value to put there (for radio,etc, put col # )
            color (optional) - six digit color code"""
        STR = 'edit_form,job=' + self.job.name + ',form=' + str(self.name) + ',elem=' + field + ',value=' + value
        if (color != ''):
            STR = STR + ',color=' + color
        STR = STR + ',opt_name=no'
        self.COM(STR)
        return self.COMANS

    def writeFile(self, fileName, color = ''):
        """ write sets of values into elements.  Read information from file.  Doesn't use option names
            file - file containing element/value pairs see Genesis Docs for edit_form_list
            color - optional - color for changed elements (I think)"""

        STR = 'edit_form_list,job=' + self.job.name + ',form=' + str(self.name) + ',opt_name=no,in_file=' + fileName
        if (color != ''):
            STR = STR + ',color=' + color
        self.COM(STR)
        return self.COMANS

    def writeFileOpt(self, fileName, color = ''):
        """ write sets of values into elements.  Read information from file.  Uses option names
            file - file containing element/value pairs see Genesis Docs for edit_form_list
            color - optional - color for changed elements (I think)"""

        STR = 'edit_form_list,job=' + self.job.name + ',form=' + str(self.name) + ',opt_name=yes,in_file=' + fileName
        if (color != ''):
            STR = STR + ',color=' + color
        self.COM(STR)
        return self.COMANS

    def color(self,element,color):
        """ change an element to another color
            element: Element Name
            color: six digit color code (RRGGBB)"""
        STR = 'edit_form,job=' + self.job.name + ',form=' + str(self.name) + ',elem=' + element + ',color=' + color + ',opt_name=no'
        self.COM(STR)
        return self.COMANS

    def writeOpt(self, field, value, color = ''):
        """ write value into field , using option name
            field - string with name of form element
            value - value to put there (for radio,etc, put value, not col#)
            color (optional) - siz digit color code"""
        STR = 'edit_form,job=' + self.job.name + ',form=' + str(self.name) + ',elem=' + field + ',value=' + value
        if (color != ''):
            STR = STR + ',color=' + color
        STR = STR + ',opt_name=yes'
        self.COM(STR)
        return self.COMANS

    def visibility(self, field, mode):
        """ Changes an elements visibility
            field - element name
            mode - mode (sensitve,unsensitive,hide,unhide)"""
        STR = 'form_elem_visibility,job=' + self.job.name + ',form=' + str(self.name) + ',elem=' + field + ',mode=' + mode
        self.COM(STR)
        return self.COMANS


     # analysis的过程，先action-erf-update-run-clear-update-copy
class Checklist(Genesis):
    """ This class defines a checklist instance. Each checklist is automatically
       instantiated as a member of the {step}.checks dictionary when
       the {step}.checks attribute is accessed. """
    '''
        type 分析的类型 包含valor_analysis_signal  钻孔分析 文字分析等
        name checklist的名称 默认为checklist
    '''
    def __init__(self, step, name='checklist', type=''):
        Genesis.__init__(self)
        self.job = step.job
        self.step = step
        self.name = name
        self.type = type


    # 参数action为当前checklist中的第几项 默认为1 至少有一个，否则info不了
    def getInfo(self, action = 1):
        # 先判断是否有该checklist
        self.info = {}
        if self.name in self.step.checks:
            self.VOF()
            self.tmp = self.DO_INFO('-t check -e %s/%s/%s -d CHK_ATTR -o action=%s ' % (self.job.name,self.step.name,self.name, action))
            self.info.update(self.tmp)
            self.tmp = self.DO_INFO('-t check -e %s/%s/%s -d DURATION -o action=%s ' % (self.job.name, self.step.name, self.name, action))
            self.info.update(self.tmp)
            self.tmp = self.DO_INFO('-t check -e %s/%s/%s -d ERF -o action=%s ' % (self.job.name, self.step.name, self.name, action))
            self.info.update(self.tmp)
            self.tmp = self.DO_INFO('-t check -e %s/%s/%s -d EXISTS' % (self.job.name, self.step.name, self.name))
            self.info.update(self.tmp)
            self.tmp = self.DO_INFO('-t check -e %s/%s/%s -d LAST_TIME -o action=%s ' % (self.job.name, self.step.name, self.name, action))
            self.info.update(self.tmp)
            self.tmp = self.DO_INFO('-t check -e %s/%s/%s -d MEAS -o action=%s ' % (self.job.name, self.step.name, self.name, action))
            self.info.update(self.tmp)
            self.tmp = self.DO_INFO('-t check -e %s/%s/%s -d MEAS_DISP_ID -o action=%s ' % (self.job.name, self.step.name, self.name, action))
            self.info.update(self.tmp)
            self.tmp = self.DO_INFO('-t check -e %s/%s/%s -d NUM_ACT -o action=%s ' % (self.job.name, self.step.name, self.name, action))
            self.info.update(self.tmp)
            self.tmp = self.DO_INFO('-t check -e %s/%s/%s -d REPOST -o action=%s ' % (self.job.name, self.step.name, self.name, action))
            self.info.update(self.tmp)
            self.tmp = self.DO_INFO('-t check -e %s/%s/%s -d STATUS -o action=%s ' % (self.job.name, self.step.name, self.name, action))
            self.info.update(self.tmp)
            self.tmp = self.DO_INFO('-t check -e %s/%s/%s -d TITLE -o action=%s ' % (self.job.name, self.step.name, self.name, action))
            self.info.update(self.tmp)
            self.VON()
        return self.info

    def show(self):
        """ Show the checklist """
        STR = 'chklist_show,chklist=' + str(self.name)
        self.COM(STR)
        return self.STATUS

    def open(self):
        """ Opens checklist, but doesn't show it """
        STR = 'chklist_open,chklist=' + str(self.name)
        self.COM(STR)
        return self.STATUS

    # #20210910 zl
    def action(self,show='no'):
        STR = 'chklist_single,action='+self.type + ',show=' + show
        self.COM(STR)
        return self.STATUS

    # 20210913 zl
    def erf(self,erf):
        STR = 'chklist_erf,chklist='+ self.type +',nact=1,erf='+ erf
        self.COM(STR)
        return  self.STATUS

    def close(self):
        """ Close the checklist """
        # STR = 'close_checklist,chklist=' + self.name + ',mode=destroy'
        STR = 'chklist_close,chklist=' + str(self.name) + ',mode=destroy'      #20210912 zl  之前的com不对，修改
        self.COM(STR)
        return self.STATUS

    def hide(self):
        """ hides checklist.  It stays open, but isn't visible"""
        # STR = 'close_checklist,chklist=' + self.name + ',mode=hide'
        STR = 'chklist_close,chklist=' + str(self.name) + ',mode=hide'         #20210912 zl  之前的com不对，修改
        self.COM(STR)
        return self.STATUS

    def run(self, area = 'profile'):
        """ Runs a checklist on all actions.
            params - optional string (defaults to empty) <NOT IMPLEMENTED YET>"""
        # STR = 'chklist_run,chklist=' + self.name + ',nact=a,area=profile'
        STR = 'chklist_run,chklist=' + self.type + ',nact=1,area=' + area            #20210912 zl
        self.COM(STR)
        return self.STATUS

    # 20210913 zl
    def clear(self):
        self.COM('chklist_pclear')
        return self.STATUS

    # 20210913 zl  拷贝checklist到actions中的checklists中
    def copy(self):
        """
        copy checklist to actions-checklists
        :return:
        """
        STR = 'chklist_pcopy,chklist=' + self.type + ',nact=1'  # 20210913 zl
        self.COM(STR)
        return self.STATUS

    # 20220408 zl 显示checklist结果
    def res_show(self, x = 500, y = 400):
        STR = 'chklist_res_show,chklist=%s,nact=1,x=%s,y=%s,w=0,h=0' % (self.type,x,y)
        self.COM(STR)
        return self.STATUS

    #update checklist parameters - params is a dictionary of parameters
    def update(self, action = 1, params = {}):
        """ Update checklist parameters, and specify action to which updates apply
            params - a dictionary of parameters.  Key is parameter name and value is
                 parameter values assigned to parameter"""

        param_str = '('
        for key in list(params.keys()):
            param_str = param_str + '(' + key + '=' + params[key] + ')'
        STR = 'chklist_cupd,chklist=' + self.type + ',nact=' + str(action) + ',params=' + param_str + '),mode=regular'
        self.COM(STR)
        return self.STATUS

    # 20210913 zl  关闭分析窗口
    def closeCheck(self):
        self.step.closeCheck(self.type)

# This class defines the job matrix.
class Matrix(Genesis,MatrixCmds):
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
        print('Dynamically fetching Matrix attribute::',name)
        if name == 'info':
            #if hasattr(self, 'info'): return self.info
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
        self.info = self.DO_INFO(' -t matrix -e '+self.job.name+'/matrix')
        # Force all gROWname elements to string values
        for x in range(len(self.info['gROWname'])):

            self.info['gROWname'][x] = str(self.info['gROWname'][x])
        return self.info

    def getRow(self, name):
        """ method returns row number of given layer.  A row number of zero 
        means the layer doesn't exist
            name - string containing name of layer"""

        self.getInfo()
        for rowNum in self.info['gROWrow']:
            if self.info['gROWname'][int(rowNum)-1] == name:
                return int(rowNum)
        return '0'

    def getRowInfo(self, rowNum):
        """Method returns dictionary of information on given row. Dictionary contains 
        following keys:  name, context, type, polarity, and side
            rowNum - The row number in the matrix"""

        index = int(rowNum)-1

        rowInfo = {'name'     : self.info['gROWname'][index],
               'context'  : self.info['gROWcontext'][index],
               'type'     : self.info['gROWlayer_type'][index],
               'polarity' : self.info['gROWpolarity'][index],
               'side'     : self.info['gROWside'][index]}

        return rowInfo

    def getRowColor(self, rowNum, format='rgb'):
        ''' Return the color used in the Genesis matrix for the given row (layer).
        If format is 'rgb', a tuple of rgb values is returned (e,g, (252,198,55) for signal layers).
        If format is 'hex', a string representing the hexadecimal color value is returned (e.g. 'FCC64D')
        The colors table is a dictionary defined in the Genesis class as self.colors
        '''
        index = int(rowNum)-1
        layType = self.info['gROWlayer_type'][index]
        if self.info['gROWcontext'][index] == 'misc':
            layType = 'document'
        if not len(layType): layType = 'document'

        return self.job.colors[format][layType]


# END OF MATRIX CLASS

class Layer(ExtraStuff,LayerCmds):
    """this class defines a layer object inside editor.  It may contain info, but cannot
       issue COM commands on it's own.  This layer object is a child of a step,
       NOT the matrix.  e.g. this object does not represent a matrix row.
       Most of these are commands you can access by right-clicking a layer in the editor."""
    def __init__(self, step, name):
        self.step = step
        self.name = name
        self.job  = self.step.job

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
        initial request    of an attribute. e.g. <class instance>.attribute 
        
        If the attribute is in this method, it is handled by methods defined here, 
        otherwise the Genesis layer object associated with this instance is inspected 
        for a corresponding Genesis attribute; the value of which is stored in the 
        instance attribute.
        
        Special Attributes Supported:  info, cell, color, hexcolor
        """

        print('Dynamically fetching Layer attribute::',name)
        if name == 'info':
            self.info = self.getInfo()
            return self.info
        elif name == 'info2':
            self.info2 = self.getInfo2()
            return self.info2
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

    def getInfo2(self):
        """Get all info about self, store in self.info
        This method is automagically called when one accesses the self.info attribute."""
        STR = ' -t layer -e %s/%s/%s,units=mm' % (self.job.name, self.step.name, self.name)
        self.info2 = self.step.DO_INFO(STR)
        return self.info2

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
    object.     Object in layer class is self.cell"""

    def __init__(self, parent):
        self.parent = parent
        self.parse()

    def parse(self):
        """ Run by __init__ method - parses matrix info into the object"""
        matrix = self.parent.job.matrix
        for x in range(len(matrix.info['gROWname'])):
            if not len(matrix.info['gROWname'][x]): continue
            if matrix.info['gROWname'][x] == self.parent.name: break
        self.row    = matrix.info['gROWrow'][x]
        self.type       = matrix.info['gROWtype'][x]
        self.name       = matrix.info['gROWname'][x]
        self.context    = matrix.info['gROWcontext'][x]
        self.layer_type = matrix.info['gROWlayer_type'][x]
        self.polarity   = matrix.info['gROWpolarity'][x]
        self.side       = matrix.info['gROWside'][x]
        self.drl_start  = matrix.info['gROWdrl_start'][x]
        self.drl_end    = matrix.info['gROWdrl_end'][x]
        self.foil_side  = matrix.info['gROWfoil_side'][x]
        self.sheet_side = matrix.info['gROWsheet_side'][x]


# Self-test code - unfortunately not very complete...
if __name__ == '__main__':
    j = Job('blank')
    j.open(1)
    print(j.STATUS)
    print(type(j.STATUS))
    print(j.READANS)
    print(type(j.READANS))
    print(j.COMANS)
    print(type(j.COMANS))
    steps = j.steps
    print('STEPS::',steps)
    for key in list(steps.keys()):
        step = steps[key]
        step.open()
    for key in list(steps.keys()):
        step = steps[key]
        step.close()
        time.sleep(2)

    j.addStep('xyz')
    j.removeStep('xyz')
    print(j.steps)

    matrix = j.matrix
    print(matrix.info)
    j.matrix.removeLayer('sm8')
    j.matrix.COM('matrix_refresh,job='+j.name+',matrix=matrix')
    time.sleep(3)
    j.matrix.addLayer('sm8', 11, type='solder_mask')


