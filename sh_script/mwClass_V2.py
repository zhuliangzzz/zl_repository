#!/usr/bin/env python
# -*- coding: utf-8 -*-
# --------------------------------------------------------- #
#                VTG.SH SOFTWARE GROUP                      #
# --------------------------------------------------------- #
# @Author       :    LiuChuang
# @Mail         :    Chuang_cs@163.com
# @Date         :    2019/06/12
# @Revision     :    3.1.0
# @File         :    msgBox.py
# @Software     :    PyCharm
# @Usefor       :    用于其它界面及防呆的提醒
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
_readme = {
    '功能': '''
    1.可用于其它窗体的模态提醒；
    2.可单独用于防呆及预警信息的提醒;
    ''',
    '用法': '''
    1.用于窗体模态提醒时：
        `
        from mwClass_V2 import *
        AboutDialog(u'这是一个提示').exec_()
        
        # --如需要接收参数，如下：
        # showMsg(u"资料优化失败，请参考后台提示信息...");
        M=AboutDialog(u'这是一个提示',cancel=True)
        M.exec_()
        # --打印选择的“按钮”
        print(M.selBut)
        `
    2.用于独立提醒时：       
        `
        from mwClass_V2 import *
        showMsg(u'这是一个提示，可直接接收参数')
        `
    3.showMsg()方法是支持返回信息的（默认的三个参数为'x'|'ok'|'cancel' 全为小写）
    4.2020.05.20增加了定时器功能（窗体延时自动关闭，timerOn=True 即可开启），同时支持默认触发的按钮
    5.带密码验证的示例
        `showMsg(mesg1, Msg2=mesg2, cancel=True, passwdCheck=True,passwd=1)`
    '''
}
"""
版本  ：V2.1.0
更新人：柳闯
更新时间：2021-08-31
更新内容：
    更新窗体置顶参数`self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog | Qt.WindowStaysOnTopHint)`
    
版本  ：V2.2.0
更新人：柳闯
更新时间：2021-09-08
更新内容：
    1、增加密码验证功能(密码自定义)
    2、去掉了小黄人的插图
    
版本  ：V3.0.0
更新人：柳闯
更新时间：2021-11-09
更新内容：
    1、增加APP审批提交机制（默认等待时长五分钟）
    2、增加提交的数据字典（key与表字段保持一致）
    3、修复升级后密码验证的bug

版本  ：V3.2.0
更新人：柳闯
更新时间：2022-01-06
更新内容：
    1、增加其它语言支持审核提交的方法（暂测试Perl），需传入3个参数：标题、是否开启审核、审核提交的数据，即len(sys.argv) == 4；
    2、具体用法参考：http://192.168.2.120:82/zentao/story-view-3671.html 备注 6 ；

版本  ：V3.2.1
更新人：柳闯
更新时间：2022-05-10
更新内容：
    1、修复Perl调用接口传入中文decode转码问题
"""

import getpass
import json
import os
import platform
import socket
import sys

from PyQt4 import QtGui
from PyQt4.Qt import *

# --加载相对位置，以实现InCAM与Genesis共用
if platform.system() == "Windows":
    sys.path.append(r"Z:/incam/genesis/sys/scripts/Package")
else:
    sys.path.append(r"/incam/server/site_data/scripts/Package")

import MySQL_DB

reload(sys)
sys.setdefaultencoding("utf-8")


class PushButton(QPushButton):
    def __init__(self, parent=None):
        super(PushButton, self).__init__(parent)

        # 枚举值
        self.status = 0  # self.NORMAL

    def loadPixmap(self, pic_name):
        self.pixmap = QPixmap(pic_name)
        self.btn_width = self.pixmap.width() / 4
        self.btn_height = self.pixmap.height()
        self.setFixedSize(self.btn_width, self.btn_height)

    def enterEvent(self, event):
        self.status = 1  # self.ENTER
        self.update()

    def mousePressEvent(self, event):
        # 若点击鼠标左键
        if event.button() == Qt.LeftButton:
            self.mouse_press = True
            self.status = 2  # self.PRESS
            self.update()

    def mouseReleaseEvent(self, event):
        # 若点击鼠标左键
        if self.mouse_press:
            self.mouse_press = False
            self.status = 3  # self.ENTER
            self.update()
            self.clicked.emit(True)

    def leaveEvent(self, event):
        self.status = 0  # self.NORMAL
        self.update()

    def paintEvent(self, event):
        self.painter = QPainter()
        self.painter.begin(self)
        self.painter.drawPixmap(self.rect(),
            self.pixmap.copy(self.btn_width * self.status, 0, self.btn_width, self.btn_height))
        self.painter.end()


class AppRelease:
    def __init__(self):
        # --当非从当前文件执行时为系统任务计划，定义为'gbk'
        self.zhCode = 'gbk'
        self.MS = MySQL_DB.MySQL(logCode=self.zhCode, printLog=False)
        self.dbc_m = self.MS.MYSQL_CONNECT(database='engineering')


    def submitApp(self, appData, passDetail):
        """
        提交审核数据（校验过的,每提交一次插入一笔记录-超时失效、取消失效）
        :param appData: 审批提交的data数据(以字段名为Key，传入的字典数据）
        :param passDetail: 放行的具体明细，即界面上备注的放行原因
        :return: data_id
        """
        # --判断是否存在指定审核人
        zhidingApprove = ""
        is_assign = 'N'
        if 'assign_approve' in appData.keys():
            is_assign = 'Y'
            zhidingApprove = appData['assign_approve']
        # @formatter:off
        insertSql = """insert into engineering.approval_pass_record 
                            (site,
                            job_name,
                            pass_tpye,
                            pass_level,
                            pass_title,
                            pass_detail,
                            submit_by,
                            submit_date,
                            submit_hosts,
                            is_assign,
                            assign_approve)
                        values 
                            ('%s','%s','%s','%d','%s','%s','%s',%s,'%s','%s','%s')""" % (appData['site'],
                                                                                    appData['job_name'],
                                                                                    appData['pass_tpye'],
                                                                                    appData['pass_level'],
                                                                                    appData['pass_title'],
                                                                                    passDetail,
                                                                                    getpass.getuser(),
                                                                                    'NOW()',
                                                                                    '%s|%s' % (socket.gethostname(), socket.gethostbyname(socket.gethostname())),
                                                                                    is_assign,
                                                                                    zhidingApprove
                                                                                    )
        # @formatter:on

        # print insertSql
        self.MS.SQL_EXECUTE(self.dbc_m, insertSql)
        # --获取当前插入的ID（因插入叔不频繁，故使用此方法）
        getSql = """select max(id) as data_id from  engineering.approval_pass_record"""
        getId = self.MS.SELECT_DIC(self.dbc_m, getSql)
        # print ("ID:%s" % getId[0]['data_id'])

        return getId[0]['data_id']

    def checkAppResult(self, dataId):
        """
        检测审核结果
        :param dataId:数据ID
        :return: True or False
        """

        selSql = """select is_pass,approve_note from engineering.approval_pass_record where id = %s""" % dataId
        getPass = self.MS.SELECT_DIC(self.dbc_m, selSql)
        # --释放连接池
        self.MS.DB_CLOSE(self.dbc_m)
        # --TODO 需要实时监控数据变化，释放连接池也取出最新数据（待优化，此处频繁连接不妥）
        self.dbc_m = self.MS.MYSQL_CONNECT(database='engineering')
        # print ("getPass:%s" % getPass)
        return getPass[0]

    def waitTimeout(self, dataId, passStatus):
        """
        审批等待超时更新审批记录
        :param dataId: 数据ID
        :return: True or False
        """
        updateSql = """UPDATE engineering.approval_pass_record SET is_pass ='%s'  where id = %s""" % (
            passStatus, dataId)
        self.MS.SQL_EXECUTE(self.dbc_m, updateSql)

        return True


class AboutDialog(QDialog, AppRelease):
    def __init__(self, Msg1, okButton='Ok', Msg2='', cancel=False, cancelButton='Cancel', style="Default",
                 passwdCheck=False, passwd='qwerty123', appCheck=False, appData={}, parent=None):
        """
        :param Msg1: 默认显示的消息
        :param Msg2: 第二条显示信息
        :param okButton: OK按钮的内容
        :param cancel: 是否显示取消按钮
        :param cancelButton: 取消按钮的内容
        :param style: 显示内容的风格（Default：默认 Custom：自定义（支持html格式的内容）
        :param passwdCheck: 是否启动密码验证
        :param passwd: 默认的密码验证
        """
        super(AboutDialog, self).__init__(parent)
        AppRelease.__init__(self)
        # --初始化移动事件相关参数
        self.dragPosition = None

        # --定义选择的按钮是哪一个
        self.selBut = None
        self.pake_path = os.path.dirname(os.path.abspath(__file__))
        self.okButton = okButton
        self.cancel = cancel
        self.cancelButton = cancelButton
        self.passwdCheck = passwdCheck
        self.appCheck = appCheck
        self.appData = appData
        # --密码转字符串,以免传入的数据为非字符型
        self.passwd = str(passwd)
        self.step = 0

        # --初始化插入的数据表的ID
        self.getInsert_id = None
        # --初始化审批等待时间(毫秒)
        self.waitTime = 100 * 10

        # --Qt.FramelessWindowHint:去除dialog标题栏 Qt.Dialog：Dialog窗体 Qt.WindowStaysOnTopHint:窗体置顶
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog | Qt.WindowStaysOnTopHint)

        # --添加任务栏图标
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(self.pake_path + "/img/9.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)

        # --重新定义提示信息的样式 并不是所有样式都支持 如后面的都不支持;padding:5px 20px;border-radius:10px;line-height:16px
        if style == 'Default':
            self.Msg1 = """
                    <p>
                        <span style="background-color:#E53333;color:#fff;font-size:16px"><strong>%s<strong></span>                    
                    </p>""" % Msg1
            self.Msg2 = """
                    <p>
                        <span style="background-color:transparent;color:#f90;font-size:16px"><strong>%s<strong></span>                    
                    </p>""" % Msg2
        else:
            self.Msg1 = Msg1
            self.Msg2 = Msg2

        self.title_label = QLabel(self)
        self.title_label.setFixedHeight(30)
        self.title_label.setStyleSheet("color:white")
        self.title_label.setFont(QFont(u"微软雅黑", 10, False))

        self.title_icon_label = QLabel(self)
        self.title_icon_label.setPixmap(QPixmap(self.pake_path + "/img/9.png"))
        self.title_icon_label.setFixedSize(16, 16)
        self.title_icon_label.setScaledContents(True)

        self.close_button = PushButton()
        self.close_button.loadPixmap(self.pake_path + "/img/close.png")

        self.title_info_label = QLabel(self)
        self.title_info_label.setStyleSheet("color:blue")  # ("color:rgb(30,170,60)")
        self.title_info_label.setFont(QFont(u"微软雅黑", 16, QFont.Bold, False))

        self.info_label = QLabel(self)
        self.info_label.setContentsMargins(0, 0, 0, 40)
        self.info_label.setStyleSheet("color:blue")  # ("color:rgb(30,170,60)")
        self.info_label.setFont(QFont(u"微软雅黑", 10, QFont.Bold, False))
        self.info_label.setContentsMargins(0, 0, 0, 40)

        self.version_label = QLabel(self)
        # self.version_label.setStyleSheet("color:red")
        self.version_label.setFont(QFont(u"微软雅黑", 12, False))

        self.mummy_label = QLabel(self)
        # self.mummy_label.setStyleSheet("color:red")
        self.mummy_label.setFont(QFont(u"微软雅黑", 12, False))

        self.copyright_label = QLabel(self)
        self.copyright_label.setStyleSheet("color:gray")

        self.icon_label = QLabel(self)
        # self.pixmap = QPixmap(self.pake_path + "/img/dancing.png")
        # self.icon_label.setPixmap(self.pixmap)
        # self.icon_label.setFixedSize(self.pixmap.size())

        # --分割线
        self.splitLine = QLabel(self)
        # self.splitLine.setStyleSheet("border-top:1px solid #fff;")

        # --密码区
        if self.passwdCheck:
            self.passwd_label = QLabel(self)
            self.passwd_label.setText(u'放行密码：')
            self.passwd_label.setStyleSheet("color:white;border:2px solid green;font:bold")

            self.passwd_edit = QLineEdit(self)
            # --密码隐藏显示
            self.passwd_edit.setEchoMode(QLineEdit.Password)
            # self.passwd_edit.setMaximumSize(200,100)
            # --密码验证结果显示区域
            self.passwd_check_label = QLabel(self)
            self.passwd_check_label.setText(u'等待密码验证或直接提交审核等待放行...')
            self.passwd_check_label.setStyleSheet("color:white;border:0px solid #fff")

        # --提交审核区
        if self.appCheck:
            # --放行文本及输入区
            self.app_label = QLabel(self)
            self.app_label.setText(u'放行原因：')
            self.app_label.setStyleSheet("color:white;border:2px solid green;font:bold")
            self.releaseReason = QTextEdit(self)
            # --提交审核按钮
            self.appButton = QPushButton(self)
            self.appButton.setText(u'提交审核')
            self.pbar = QProgressBar(self)
            self.pbar.setTextVisible(False)
            # self.pbar.setStyleSheet("""
            #                QProgressBar {
            #                    background-color: #C0C6CA;
            #                    border: 0px;
            #                    padding-top: 1px;
            #                    padding-bottom: 1px;
            #                }""")
            # self.pbar.setOrientation(Qt::Horizontal); // 水平方向

            # --计时器
            self.timer = QBasicTimer()

        # --按钮区
        self.ok_button = QPushButton(self)
        self.ok_button.setFixedSize(75, 25)
        self.ok_button.setStyleSheet("QPushButton{border:1px solid #fff;border-radius:11px;background:rgb(230,230,230)}"
                                     "QPushButton:hover{border-color:#fff;border-radius:11px;background:transparent;color:#fff}"
                                     "QPushButton:pressed{background:lightblue;border-style:hidden;color:#000}")
        if self.cancel:
            self.other_button = QPushButton(self)
            self.other_button.setFixedSize(75, 25)
            self.other_button.setStyleSheet(
                "QPushButton{border:1px solid lightgray;border-radius:11px;background:rgb(230,230,230)}"
                "QPushButton:hover{border:1px solid #E53333;border-radius:11px;background:transparent;color:#fff}"
                "QPushButton:pressed{background:lightblue;border-style:hidden;color:#000}")

        # 布局标题
        self.title_layout = QHBoxLayout()
        self.title_layout.addWidget(self.title_icon_label, 0, Qt.AlignVCenter)
        self.title_layout.addWidget(self.title_icon_label, 0, Qt.AlignVCenter)
        self.title_layout.addWidget(self.title_label, 0, Qt.AlignVCenter)
        self.title_layout.addStretch()  # 平均
        self.title_layout.addWidget(self.close_button, 0, Qt.AlignTop)

        # 布局信息列表
        self.v1_layout = QVBoxLayout()
        self.v1_layout.addWidget(self.title_info_label)
        self.v1_layout.addWidget(self.info_label)
        self.v1_layout.setSpacing(15)

        # --两行message的布局
        self.v2_layout = QVBoxLayout()
        self.v2_layout.addWidget(self.version_label)
        self.v2_layout.addWidget(self.mummy_label)
        self.v2_layout.setSpacing(15)

        self.v3_layout = QVBoxLayout()
        self.v3_layout.addWidget(self.splitLine)
        self.v3_layout.setSpacing(15)

        # --一行密码验证的布局
        if self.passwdCheck:
            self.v4_layout = QHBoxLayout()
            self.v4_layout.addWidget(self.passwd_label)
            self.v4_layout.addWidget(self.passwd_edit)
            self.v4_layout.addWidget(self.passwd_check_label)
            # self.v4_layout.setSpacing(15)
        else:
            self.v4_layout = False

        if self.appCheck:
            self.v5_layout = QHBoxLayout()
            self.v6_layout = QHBoxLayout()

            self.v5_layout.addWidget(self.app_label)
            self.v5_layout.addWidget(self.releaseReason)

            self.v6_layout.addWidget(self.appButton)
            self.v6_layout.addWidget(self.pbar)
            # self.v6_layout.setSpacing(15)
        else:
            self.v5_layout = False

        # --版权信息的布局
        self.copright = QVBoxLayout()
        self.copright.addWidget(self.copyright_label)
        self.copright.setSpacing(15)

        # --整体的布局
        self.v_layout = QVBoxLayout()
        self.v_layout.addLayout(self.v1_layout)
        self.v_layout.addLayout(self.v2_layout)
        self.v_layout.addLayout(self.v3_layout)
        if self.v4_layout:
            self.v_layout.addLayout(self.v4_layout)
        if self.v5_layout:
            self.v_layout.addLayout(self.v5_layout)
            self.v_layout.addLayout(self.v6_layout)
        self.v_layout.addLayout(self.copright)
        self.v_layout.addStretch()  # 平均分配
        self.v_layout.setSpacing(20)
        self.v_layout.setContentsMargins(0, 5, 0, 0)  # 设置距离边界的值

        # 布局配置
        self.bottom_layout = QHBoxLayout()
        # --是否显示取消按钮
        if self.cancel:
            self.bottom_layout.addStretch()
            self.bottom_layout.addWidget(self.other_button)
            self.bottom_layout.setSpacing(0)
            self.bottom_layout.setContentsMargins(0, 0, 0, 20)

        self.bottom_layout.addStretch()
        self.bottom_layout.addWidget(self.ok_button)
        self.bottom_layout.setSpacing(0)
        self.bottom_layout.setContentsMargins(0, 0, 60, 20)

        self.h_layout = QHBoxLayout()
        # self.h_layout = QVBoxLayout()
        self.h_layout.addLayout(self.v_layout)
        self.h_layout.addWidget(self.icon_label)
        self.h_layout.setSpacing(0)
        self.h_layout.setContentsMargins(40, 0, 20, 10)

        self.main_layout = QVBoxLayout()
        self.main_layout.addLayout(self.title_layout)
        self.main_layout.addStretch()
        self.main_layout.addLayout(self.h_layout)
        self.main_layout.addLayout(self.bottom_layout)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.setLayout(self.main_layout)

        self.title_layout.setSpacing(0)
        self.title_layout.setContentsMargins(10, 0, 5, 0)

        self.translateLanguage()
        self.resize(520, 290)

        # --绑定右上角‘X’事件及 按钮事件
        self.connect(self.ok_button, SIGNAL("clicked()"), self.ONclick_ok)
        self.connect(self.close_button, SIGNAL("clicked()"), self.ONclick_x)

        # --当取消按钮被选择时的事件绑定
        if self.cancel:
            self.connect(self.other_button, SIGNAL("clicked()"), self.ONclick_cancel)

        # --当存在密码验证时的事件
        if self.appCheck:
            self.connect(self.appButton, SIGNAL('clicked()'), self.appSubmit)

        # --当需要审核时，OK按钮为禁用状态
        if self.appCheck:
            self.ok_button.setDisabled(True)

    def ONclick_ok(self):
        # --验证密码是否有效
        if self.passwdCheck:
            get_Passwd = self.passwd_edit.text()
            if get_Passwd != self.passwd:
                self.passwd_check_label.setText(u'密码错误,请重新输入...')
                self.passwd_check_label.setStyleSheet("color:red;border:0px solid #fff")
                self.passwd_edit.setText('')
                return
            else:
                self.passwd_check_label.setText(u'密码验证通过!')
                self.passwd_check_label.setStyleSheet("color:green;border:0px solid #fff")
                QMessageBox.about(self, u'温馨提醒', u'密码验证通过，OK后即将放行。。。！')

        # --关闭
        self.close()
        self.selBut = "ok"

    def timerEvent(self, e):
        # self.pbar.setMinimum(0)
        # self.pbar.setMaximum(0)
        if self.step >= self.waitTime:
            # --进度100%
            self.step = 100
            self.pbar.setValue(self.step)
            self.timer.stop()
            self.appButton.setText(u'提交审核')
            # @formatter:off
            quesSel = QMessageBox.question(self, u"是否重新提交", u'等待超时，是否重新提交审核请求继续等待审批？', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if quesSel == QMessageBox.Yes:
                # --重置进度长
                self.step = 0
                self.pbar.setValue(self.step)
                # --调用提交功能继续在本向记录下等待审批
                self.appSubmit()
                print "Yes"
            else:
                print "No"
                self.waitTimeout(self.getInsert_id,'Timeout')
                # --关闭窗体
                self.close()
                # --用于返回数据
                self.selBut = "x"
                return
            # @formatter:on

            return
        # region # --此处可以添加检测跳出事件(为防止频繁访问DB，此处事件设置为每5查一次数据库审核状态
        # print u"此处可以添加检测跳出事件....\n"
        # if not self.step % 50:
        # print (u'等待时长：%s' % self.step)
        getPass_Result = self.checkAppResult(self.getInsert_id)
        if getPass_Result['is_pass'].lower() == 'pass':
            self.timer.stop()
            self.appButton.setText(u'审核通过')
            self.ok_button.setDisabled(False)
            QMessageBox.about(self, u'温馨提醒', u'审核通过，OK后即将放行。。。！')
            self.ONclick_ok()
            return
        elif getPass_Result['is_pass'].lower() == 'nopass':
            self.timer.stop()
            self.appButton.setText(u'审核不通过')
            # --关闭窗体
            self.close()
            QMessageBox.about(self, u'温馨提醒', u'审核不通过，原因如下：\n\t%s' % getPass_Result['approve_note'])

            # --用于返回数据
            self.selBut = "x"
            return
        # endregion

        self.step = self.step + 1
        # self.pbar.setValue(self.step)
        self.pbar.setValue(int((self.step * 100) / self.waitTime))

    def appSubmit(self):
        """
        审核提交等待放行
        :return: None
        """
        # --提交前判断是否有写入放行原因
        # print ('A:%s' % self.releaseReason.toPlainText())
        if self.releaseReason.toPlainText() == "":
            QMessageBox.about(self, u'温馨提醒', u'提交审核放行前请输入放行原因！')
            return

        # region # --提交审核，并insert数据
        # print self.appData
        self.getInsert_id = self.submitApp(self.appData, self.releaseReason.toPlainText())
        # endregion

        self.doAction()

        # print "appSubmit...."

    def doAction(self):
        # print("do action")
        if self.timer.isActive():
            self.timer.stop()
            self.appButton.setText(u'继续等待')
        else:
            self.timer.start(self.waitTime, self)
            self.appButton.setText(u'等待审批中')


    def ONclick_x(self):
        # --失效审批记录
        if self.getInsert_id:
            self.waitTimeout(self.getInsert_id, 'Cancel')

        # --关闭窗体
        self.close()
        self.selBut = "x"

    def ONclick_cancel(self):
        # --失效审批记录
        if self.getInsert_id:
            self.waitTimeout(self.getInsert_id, 'Cancel')

        # --关闭窗体
        self.close()
        self.selBut = "cancel"

    def paintEvent(self, event):
        self.painter = QPainter()
        self.painter.begin(self)
        self.painter.drawPixmap(self.rect(), QPixmap(self.pake_path + "/img/17_big.png"))
        self.painter.end()

        self.painter2 = QPainter()
        self.painter2.begin(self)
        # 设定画笔颜色，到时侯就是边框颜色
        self.painter2.setPen(Qt.white)
        self.painter2.drawRect(QRect(0, 30, self.width(), self.height() - 30))
        self.painter2.end()

        self.painter3 = QPainter()
        self.painter3.begin(self)
        self.painter3.setPen(Qt.gray)
        self.painter3.drawPolyline(QPointF(0, 30), QPointF(0, self.height() - 1),
            QPointF(self.width() - 1, self.height() - 1), QPointF(self.width() - 1, 30))
        self.painter3.end()

    def translateLanguage(self):
        self.ram_txt = self.setRandomTxt()
        self.title_label.setText(u"消息提醒")
        self.title_info_label.setText(u"胜宏科技（惠州）股份有限公司")
        self.info_label.setText(self.ram_txt)
        self.version_label.setText(self.Msg1)
        self.mummy_label.setText(self.Msg2)

        self.copyright_label.setText(u"Copyright(c) Vgt(Chuang.Liu) Inc.All Rights Reserved.")
        self.ok_button.setText(self.okButton)
        if self.cancel:
            self.other_button.setText(self.cancelButton)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragPosition = event.globalPos() - self.frameGeometry().topLeft()
            QApplication.postEvent(self, QEvent(174))
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            if self.dragPosition:
                self.move(event.globalPos() - self.dragPosition)
            event.accept()

    def setRandomTxt(self):
        import os
        import random
        import codecs
        self.txt_path = self.pake_path + "/RandomTxt.txt"
        self.line = None
        if os.path.isfile(self.txt_path):
            f = codecs.open(self.txt_path, 'r', 'utf-8')
            # --读取所有行信息，并存入数组
            self.line = f.readlines()
        if self.line:
            # --随机选择一个元素
            return random.choice(self.line)
        else:
            return u'冰冻三尺，非一日之寒！'


def showMsg(Msg1, Msg2='', okButton=u'OK', cancel=False, cancelButton='Cancel', timerOn=False, timing=2,
            autoClick='ok', passwdCheck=False, passwd='qwerty123', appCheck=False, appData={}):
    """
    :param Msg1: 默认显示的消息
    :param Msg2: 第二条显示信息
    :param okButton: OK按钮的内容
    :param cancel: 是否显示取消按钮
    :param cancelButton: 取消按钮的内容
    :param timerOn: 定时器开关(True | False)
    :param timing: 定时时长（以秒为单位）
    :param autoClick: 自动触发的按钮（仅接收ok|cancel）
    :param passwdCheck: 是否密码放行
    :param passwd: 验证的密码
    :param appCheck: 是否提交Web审核
    :param appData: 提交Web审核的数据字典（Key需要与表字段保持一致）
    :return:返回选择的按钮名称 'x'|'ok'|'cancel' 全为小写
    """

    app = QApplication(sys.argv)

    Dialog = AboutDialog(Msg1, okButton=okButton, Msg2=Msg2, cancel=cancel, cancelButton=cancelButton,
        passwdCheck=passwdCheck, passwd=passwd, appCheck=appCheck, appData=appData)

    Dialog.show()
    # --当定时器开启时的功能
    if timerOn:
        if autoClick == 'ok':
            Dialog.ok_button.animateClick(timing * 1000)  # 3秒自动关闭
        elif autoClick == 'cancel':
            Dialog.other_button.animateClick(timing * 1000)  # 3秒自动关闭
        else:
            pass

    app.exec_()

    # 返回按钮的选择名称
    return Dialog.selBut


if __name__ == '__main__':
    # 测试传进来的参数尽量使用utf-8，因为以下只对utf-8和编码进行解码，未考虑gbk
    # TODO 如果是perl脚本调用传过来的mesg1、mesg2中有中文时，需要前后加上个英文以防decode异常 或 使用英文标点符号结尾
    if len(sys.argv) == 2:
        mesg1 = sys.argv[1].decode('utf-8','ignore')
        mesg2 = ''
        print(showMsg(mesg1, Msg2=mesg2))
    elif len(sys.argv) == 3:
        mesg1 = sys.argv[1].decode('utf-8','ignore')
        mesg2 = sys.argv[2].decode('utf-8','ignore')
        print(showMsg(mesg1, Msg2=mesg2))
    elif len(sys.argv) == 4:
        cancel = True
        appCheck = sys.argv[1]
        # print type(sys.argv[2].decode('utf-8'))
        # print type(sys.argv[2].encode('utf8').decode('unicode_escape'))
        mesg1 = sys.argv[2].decode('utf-8','ignore')
        # mesg1 =str(sys.argv[2]).decoce('utf-8', 'ignore')
        tmpData = json.loads(str(sys.argv[3]).replace('\'', '"'))
        tmpData['pass_title'] = mesg1
        print(showMsg(mesg1, cancel=cancel, appCheck=appCheck, appData=tmpData))
    else:
        mesg1 = u'这是第一条...'
        mesg2 = u'这是第二条'
        print (sys.argv)
        print(showMsg(mesg1, Msg2=mesg2))

    # --此处注意有其它脚本呼叫，参数格式不能作更改（print 用作csh 、 perl脚本接收返回值用）


    # region # --独立的提醒窗体demo
    # showMsg(mesg1)
    # endregion

    # region # --带密码的demo
    # showMsg(mesg1, Msg2=mesg2, cancel=True, passwdCheck=True, passwd=1, appCheck=False)
    # endregion

    # region # --带审核的demo,可参考 ..\sh_script\InnerAutoOpt\InnerOpt_Win.py
    # tmpData = {
    #     'site': u'多层板事业部',
    #     'job_name': 'test_liuc1222',
    #     'pass_tpye': 'CAM',
    #     'pass_level': 4,
    #     'pass_title': u'111-间距小于2禁止输',
    # }
    # --暂不考虑密码验证与审批验证同时存在-没必要
    # showMsg(tmpData['pass_title'], cancel=True, passwdCheck=True, passwd=1, appCheck=True, appData=tmpData)
    # showMsg(tmpData['pass_title'], cancel=True, appCheck=True, appData=tmpData)
    # endregion


