#!/usr/bin/python
# -*- coding: UTF-8 -*-
# --------------------------------------------------------- #
#                VTG.SH SOFTWARE GROUP                      #
# --------------------------------------------------------- #
# @Author       :    AresHe
# @Mail         :    502614708@qq.com
# @Date         :    2020/12/16
# @Revision     :    1.0.0
# @File         :    laser_reread_file.py
# @Software     :    PyCharm
# @Usefor       :
# --------------------------------------------------------- #

_header = {
    'description': '''
    -> 本程序主要服务于胜宏科技（惠州），任何其他团体或个人如需使用，必须经胜宏科技（惠州）相关负责
       人及作者的批准，并遵守以下约定；
    1> 本着尊重创作者的劳动成果，任何团体或个人在使用此程序的时候，均需要知会此程序的原始创作者；
    2> 在任何场合宣导、宣传，在任何文件、报告、邮件中提及本程序的全部或部分功能，均需要声明此程序的
       原始创作者；
    3> 在任何时候对本程序做部分修改或者是升级时，必须要保留文件的原始信息，包括原始文件名、创作者及
       联系方式、创作日期等信息，且不得删除程序中的源代码，只能进行注释处理；
'''
}
'''
                   _ooOoo_
                  o8888888o
                  88" . "88
                  (| -_- |)
                  O\  =  /O
               ____/`---'\____
             .'  \\|     |//  `.
            /  \\|||  :  |||//  \
           /  _||||| -:- |||||-  \
           |   | \\\  -  /// |   |
           | \_|  ''\---/''  |   |
           \  .-\__  `-`  ___/-. /
         ___`. .'  /--.--\  `. . __
      ."" '<  `.___\_<|>_/___.'  >'"".
     | | :  `- \`.;`\ _ /`;.`/ - ` : | |
     \  \ `-.   \_ __\ /__ _/   .-` /  /
======`-.____`-.___\_____/___.-`____.-'======
                   `=---='
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
           佛祖保佑       永无BUG
'''

import platform, socket, getpass, time, sys, os, re, pprint

if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")
import genCOM_26 as genCOM
from PyQt4 import QtCore, QtGui
from packge.win import *
from packge.img import *
from messageBoxPro import msgBox
import shutil

# --这三行解决python2.7编码问题,解决方案来源于网络。。。
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

class WINDOWS():
    def __init__(self):
        self.GEN = genCOM.GEN_COM()
        self.JOB = os.environ.get("JOB")
        self.STEP = os.environ.get("STEP")
        self.set_window_para()

        # --设定参数文件路径
        self.filePath = '/tmp/get_reread_drill_file_scripts_para'
        if platform.system() == "Windows":
            self.filePath = 'C:/tmp/get_reread_drill_file_scripts_para'

        # --设定回读文件路径
        self.get_parameter()

    def set_window_para(self):
        self.Form = QtGui.QWidget()
        self.ui = Ui_Form()
        self.ui.setupUi(self.Form)
        self.Form.setWindowTitle(u"机械钻带回读比对")
        self.ui.label.setText(u"机械钻带资料自动回读、比对")
        self.Form.show()
        self.ui.pushButton.clicked.connect(self.selete_file)
        self.ui.pushButton_4.clicked.connect(self.set_filePath)
        self.ui.pushButton_3.clicked.connect(sys.exit)

    def set_filePath(self):
        inputDialog = QtGui.QInputDialog(None)
        inputDialog.setOkButtonText(u'保存')
        inputDialog.setCancelButtonText(u'退出')
        inputDialog.setLabelText(u'输入修改路径:')
        inputDialog.setWindowTitle(u'设定帮助')
        if inputDialog.exec_():
            # --如果点击了ok按钮
            text = inputDialog.textValue()
            if text != None:
                self.write_para(text)

    def write_para(self,text):
        fo = open(self.filePath, 'w')
        fo.write(text)
        fo.close()

    def get_parameter(self):
        #self.get_para_path = ''
        #if os.path.exists(self.filePath):
            #with open(self.filePath, 'r') as f:
                #self.get_para_path = f.read().strip()
        if sys.platform == "win32":
            self.get_para_path = ur"\\192.168.2.174\GCfiles\Program\工程辅助资料\{0}系列\{1}".format(self.JOB[1:4], self.JOB.split('-')[0])
        else:
            self.get_para_path = u"/windows/174.file/Program/工程辅助资料/{0}系列/{1}".format(self.JOB[1:4], self.JOB.split('-')[0])        
        self.ui.lineEdit.setText(self.get_para_path)

    def selete_file(self):
        self.find_file = QtGui.QFileDialog.getOpenFileNames(self.Form, QtCore.QString(u"选择机械钻带文件"),QtCore.QString(self.ui.lineEdit.text()),QtCore.QString(u"All(*.*);;分割镭射文件(*.write);;Images(*.png *.jpg);;txt文件(*.txt)"))
        # --系统自行过滤机械资料
        file = re.compile('b\d+-\d+|drl|cdc|cds|bd\d+-?\d+')
        if len(self.find_file) > 1:            
            for f in self.find_file:
                if file.search(f):
                    # print type(unicode(f).encode('utf-8'))
                    # --QtCore.QString 转换到string
                    self.check_file(unicode(f).encode('utf-8'))
                    self.input_file()
        else:
            self.check_file(unicode(self.find_file[0]).encode('utf-8'))
            self.input_file()            

        if self.find_file:
            msg_box = msgBox()
            msg_box.information(self, '提示', '完成退出!', QtGui.QMessageBox.Ok)
            sys.exit(0)

    def check_file(self,file_path):
        if sys.platform == "win32":            
            filearray = file_path.split('\\')
        else:
            filearray = file_path.split('/')
        if len(filearray) > 0:
            self.file_bak = 'filebak_' + filearray[len(filearray) - 1]
        else:
            self.file_bak = 'filebak_' + filearray[len(filearray)]

        self.file_bak_path = '/tmp/' + self.file_bak
        if platform.system() == "Windows":
            self.file_bak_path = 'D:\\tmp\\' + self.file_bak
            
        if not os.path.exists(file_path):
            file_path = file_path.decode("utf8")
        
        if os.path.exists(file_path):
            g82_g83 = re.compile('(G82|G83)(X(-?)(\d+)Y(-?)(\d+))')
            delete_tool = re.compile('^T(\d+)')
            change_tool = re.compile('\w')
            orig_tool = re.compile('T21')
            per_symbol = re.compile('%')

            with open(file_path,'r') as f:
                dile_data = f.readlines()
                write_file_bak = open(self.file_bak_path, 'w+')
                flag = 'neck'

                clip_drill = 'no'
                for ck in dile_data:
                    # --当检查到资料内存在T10则视为分割资料
                    if ck == 'T10':
                        clip_drill = 'yes'
                   
                if clip_drill == 'yes':
                    for line in dile_data:                     
                        if flag == 'neck':
                            if g82_g83.search(line):
                                flag = 'first'
                        elif flag == 'first':
                            if delete_tool.search(line):
                                flag = 'delete'
                        elif flag == 'delete':
                            if not change_tool.search(line):
                                flag = 'change'
                        elif flag == 'change':
                            if orig_tool.search(line):
                                flag = 'orig'

                        if flag == 'neck':
                            if per_symbol.search(line):
                                write_file_bak.write(line)
                                write_file_bak.write('T01\n')
                            else:
                                write_file_bak.write(line)
                        elif flag == 'first':
                            # [G82|G83](X(-?)(\d+)Y(-?)(\d+))
                            match_obj = g82_g83.match(line)
                            if match_obj:
                                write_file_bak.write(match_obj.group(2) + "\n")
                        elif flag == 'change':
                            match_obj = g82_g83.match(line)
                            if match_obj:
                                write_file_bak.write(match_obj.group(2) + "\n")
                            elif change_tool.search(line) is None:
                                write_file_bak.write("T500\n")
                            else:
                                if not re.search('^T50[1-9]', line):
                                    write_file_bak.write(line)
                        elif flag == 'orig':
                            write_file_bak.write(line)
                else:
                    for line in dile_data:
                        if per_symbol.search(line):
                            write_file_bak.write(line)
                            write_file_bak.write('T01\n')
                        elif g82_g83.search(line):
                            match_obj = g82_g83.match(line)
                            if match_obj:
                                write_file_bak.write(match_obj.group(2) + "\n")
                            else:
                                write_file_bak.write(line)
                        else:
                            if not re.search('^T50[1-9]',line):
                                write_file_bak.write(line)
                write_file_bak.close()
                # sys.exit(0)

    def input_file(self):
        self.GEN.OPEN_STEP(self.STEP)

        # --导入文件
        self.GEN.COM('input_manual_reset')
        self.GEN.COM('input_manual_set,path=%s,job=%s,step=panel,format=Excellon2,data_type=ascii,\
                     units=mm,coordinates=absolute,zeroes=trailing,nf1=3,nf2=3,decimal=no,separator=nl,tool_units=mm,layer=%s,wheel=,\
                     wheel_template=,nf_comp=0,multiplier=1,text_line_width=0.0024,signed_coords=no,break_sr=yes,drill_only=no,merge_by_rule=no,threshold=200,resolution=3'%(self.file_bak_path,self.JOB,self.file_bak))
        self.GEN.COM('input_manual,script_path=')
        
        lines = file(self.file_bak_path).readlines()
        if "Mirror_ver:7" in "".join(lines):
            self.GEN.CLEAR_LAYER()
            self.GEN.AFFECTED_LAYER(self.file_bak, "yes")
            self.GEN.COM("sel_transform,mode=anchor,oper=y_mirror,duplicate=no,"
                         "x_anchor=0,y_anchor=0,angle=0,x_scale=1,y_scale=1,"
                         "x_offset=0,y_offset=0")            

        os.unlink(self.file_bak_path)
        if self.ui.checkBox.isChecked():
            result = self.auto_compare()
            if result:                
                status,souce_layer,layer_map = result
                if status:
                    msg_box = msgBox()
                    msg_box.critical(self, '警告', '重读资料比对:\n%s和%s\n发现异常:%s处\n详细请检查:%s!'%(self.file_bak,souce_layer,status,layer_map), QtGui.QMessageBox.Ok)

    def auto_compare(self):
        #compare_layer = re.compile('s\d+-\d+')
        #layer_name = compare_layer.findall(self.file_bak_path)
        layer_name = [os.path.basename(self.file_bak_path).split(".")[1]]
        if layer_name[0]:
            if self.GEN.LAYER_EXISTS(layer_name[0]) == 'yes' and self.GEN.LAYER_EXISTS(self.file_bak) == 'yes':
                layer_bak = 'new_bak_' + layer_name[0]
                map_layer = layer_name[0] + '_reread_compare'
                self.GEN.COM("units,type=inch")
                self.GEN.COM('flatten_layer,source_layer=%s,target_layer=%s'%(layer_name[0],layer_bak))
                self.GEN.COM('compare_layers,layer1=%s,job2=%s,step2=%s,layer2=%s,layer2_ext=,tol=0.3,area=global,consider_sr=yes,ignore_attr=,map_layer=%s,map_layer_res=200'%(layer_bak,self.JOB,self.STEP,self.file_bak,map_layer))
                self.GEN.DELETE_LAYER(layer_bak)

                info = self.GEN.DO_INFO('-t layer -e %s/%s/%s -m script -d SYMS_HIST'%(self.JOB,self.STEP,map_layer))
                sym_list = info['gSYMS_HISTsymbol']
                sym_size = info['gSYMS_HISTpad']
                for n in range(len(sym_list)):
                    if sym_list[n] == 'r0':
                        return sym_size[n],layer_name[0],map_layer
            else:
                if self.GEN.LAYER_EXISTS(layer_name[0]) == 'no':                    
                    log = "{0}层不存在，请检查".format(layer_name[0])
                else:
                    log = "钻带回读异常，请手动回读比对"
                msg_box = msgBox()
                msg_box.critical(self, '警告', log, QtGui.QMessageBox.Ok)                

    def copy_file(self, source, target):
        '''
        copy文件
        :param source: 原文件
        :param target: 目标文件
        :return:None
        '''
        if os.path.exists(target) == False:
            os.makedirs(target)
        try:
            shutil.copy(source, target)
        except IOError as reson:
            print("Unable to copy file %s" % (reson))
        except:
            print("Unexpected Error:%s", sys.exc_info())


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    win = WINDOWS()
    sys.exit(app.exec_())
