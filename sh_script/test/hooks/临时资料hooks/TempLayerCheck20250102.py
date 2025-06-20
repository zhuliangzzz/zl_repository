#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
   @file:TempLayerCheck.py
   @author:zl
   @time: 2024/11/14 14:16
   @software:PyCharm
   @desc:
   close_job.pre    检测是否有临时层，是否需要还原成正式层
   open_job.post    检测是否有临时层，强制还原成正式层
"""
import re
import sys
import os

from PyQt4 import QtGui, QtCore

if sys.platform == "win32":
    scriptPath = "%s/sys/scripts" % os.environ.get('SCRIPTS_DIR', 'Z:/incam/genesis')
    sys.path.insert(0, "Z:/incam/genesis/sys/scripts/Package_HDI")
else:
    scriptPath = "%s/scripts" % os.environ.get('SCRIPTS_DIR', '/incam/server/site_data')
    sys.path.insert(0, "/incam/server/site_data/scripts/Package")
import genClasses_zl as gen
import MySQL_DB


class TempLayerCheck(object):
    def __init__(self):
        # jobname = os.environ.get('JOB')
        self.job = gen.Job(jobname)

    # close_job 是否重置临时层为正式层
    def check_restore_normal(self):
        matrix = self.job.matrix.getInfo()
        temp_layers = []
        for i, layer in enumerate(matrix['gROWname']):
            if matrix['gROWcontext'][i] == "board" and re.match(".*-ls\d+.*", layer):
                temp_layers.append(layer)
        if temp_layers:
            confirm = QtGui.QMessageBox.information(None, u"提示", u'检测到有临时层，是否还原成正式层',
                                                    QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
            if confirm == QtGui.QMessageBox.Yes:
                dic_drill_start_end = self.get_drill_start_end_layers()
                for temp_layer in temp_layers:
                    normal_layer = temp_layer.split("-ls")[0]
                    self.job.COM(
                        "matrix_layer_context,job={0},matrix=matrix,layer={1},context=misc".format(self.job.name,
                                                                                                   temp_layer))
                    self.job.COM(
                        "matrix_layer_context,job={0},matrix=matrix,layer={1},context=board".format(self.job.name,
                                                                                                    normal_layer))
                    for key, value in dic_drill_start_end.iteritems():
                        if value["start"] == temp_layer:
                            value["start"] = normal_layer
                        if value["end"] == temp_layer:
                            value["end"] = normal_layer

                new_dic_drill_start_end = self.get_drill_start_end_layers()

                for key, value in dic_drill_start_end.iteritems():
                    if value["start"] and value["end"]:
                        for new_key in [key, key.split("-ls")[0]]:
                            if not new_dic_drill_start_end.has_key(new_key):
                                continue
                            if new_dic_drill_start_end[new_key]["start"] == value["start"] and \
                                    new_dic_drill_start_end[new_key]["end"] == value["end"]:
                                continue
                            self.job.COM("matrix_layer_drill,job={0},matrix=matrix,layer={1},start={2},end={3}".format(
                                self.job.name, new_key, value["start"], value["end"]))
                self.job.save()

    # open_job 重置临时层为正式层
    def restore_normal(self):
        # 判断权限
        DB_M = MySQL_DB.MySQL()
        dbc_m = DB_M.MYSQL_CONNECT(hostName='192.168.2.19', database='hdi_engineering', prod=3306,
                                   username='root', passwd='k06931!')
        sql = u"select * from hdi_engineering.incam_user_authority"
        director_user_info = DB_M.SELECT_DIC(dbc_m, sql)
        dbc_m.close()
        IncamUser = self.job.getUser()
        for dic_info in director_user_info:
            if str(dic_info["user_id"]) == IncamUser:
                if dic_info["Authority_Name"] == u"审核人权限" and \
                        dic_info["Authority_Status"] == u"是":
                    # self.job.COM('skip_current_command')
                    return
        matrix = self.job.matrix.getInfo()
        temp_layers = []
        for i, layer in enumerate(matrix['gROWname']):
            if matrix['gROWcontext'][i] == "board" and re.match(".*-ls\d+.*", layer):
                temp_layers.append(layer)
        if temp_layers:
            dic_drill_start_end = self.get_drill_start_end_layers()
            for temp_layer in temp_layers:
                normal_layer = temp_layer.split("-ls")[0]
                self.job.COM(
                    "matrix_layer_context,job={0},matrix=matrix,layer={1},context=misc".format(self.job.name,
                                                                                               temp_layer))
                self.job.COM(
                    "matrix_layer_context,job={0},matrix=matrix,layer={1},context=board".format(self.job.name,
                                                                                                normal_layer))
                for key, value in dic_drill_start_end.iteritems():
                    if value["start"] == temp_layer:
                        value["start"] = normal_layer
                    if value["end"] == temp_layer:
                        value["end"] = normal_layer

            new_dic_drill_start_end = self.get_drill_start_end_layers()

            for key, value in dic_drill_start_end.iteritems():
                if value["start"] and value["end"]:
                    for new_key in [key, key.split("-ls")[0]]:
                        if not new_dic_drill_start_end.has_key(new_key):
                            continue
                        if new_dic_drill_start_end[new_key]["start"] == value["start"] and \
                                new_dic_drill_start_end[new_key]["end"] == value["end"]:
                            continue
                        self.job.COM("matrix_layer_drill,job={0},matrix=matrix,layer={1},start={2},end={3}".format(
                            self.job.name, new_key, value["start"], value["end"]))
            self.job.VOF()
            self.job.COM('check_inout,mode=out,type=job,job=%s' % self.job.name)
            self.job.VON()
            self.job.save()

    def get_drill_start_end_layers(self):
        matrixInfo = self.job.matrix.getInfo()
        dic_drill_start_end = {}
        for i, layer in enumerate(matrixInfo["gROWname"]):
            if matrixInfo["gROWlayer_type"][i] == "drill" and matrixInfo["gROWcontext"][i] == "board":
                row = matrixInfo["gROWname"].index(layer)
                gROWdrl_start = matrixInfo["gROWdrl_start"][row]
                gROWdrl_end = matrixInfo["gROWdrl_end"][row]
                dic_drill_start_end[layer] = {"start": gROWdrl_start, "end": gROWdrl_end, }

        return dic_drill_start_end


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    app.setStyle('Cleanlooks')
    jobname = sys.argv[1]
    tempLayerCheck = TempLayerCheck()
    if 'check_restore_normal' in sys.argv[2:]:
        tempLayerCheck.check_restore_normal()
    elif 'restore_normal' in sys.argv[2:]:
        tempLayerCheck.restore_normal()
